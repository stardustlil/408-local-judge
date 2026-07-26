from __future__ import annotations

import os
import math
import subprocess
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from .config import settings
from .models import Problem, Submission, TestCase


MAX_DIAGNOSTIC_BYTES = 16 * 1024
MAX_OUTPUT_BYTES = 8 * 1024 * 1024
MAX_BINARY_BYTES = 8 * 1024 * 1024
COMPILE_MEMORY_MB = 512
COMPILE_TIMEOUT_SECONDS = 15


class JudgeInfrastructureError(RuntimeError):
    pass


@dataclass
class JudgeOutcome:
    status: str
    message: str = ""
    compile_output: str = ""
    case_results: list[dict] = field(default_factory=list)
    runtime_ms: int | None = None
    memory_kb: int | None = None


def normalize_output(value: str) -> str:
    lines = value.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    normalized = [line.rstrip() for line in lines]
    while normalized and normalized[-1] == "":
        normalized.pop()
    return "\n".join(normalized)


def _decode(value: bytes | None, limit: int = MAX_DIAGNOSTIC_BYTES) -> str:
    if not value:
        return ""
    clipped = value[:limit]
    result = clipped.decode("utf-8", errors="replace")
    if len(value) > limit:
        result += "\n... 输出已截断"
    return result


def _docker(
    args: list[str],
    *,
    input_data: bytes | None = None,
    timeout: float = 30,
    check: bool = True,
) -> subprocess.CompletedProcess[bytes]:
    try:
        result = subprocess.run(
            ["docker", *args],
            input=input_data,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise JudgeInfrastructureError(f"Docker 命令执行失败：{exc}") from exc
    if check and result.returncode != 0:
        detail = _decode(result.stderr) or _decode(result.stdout)
        raise JudgeInfrastructureError(f"Docker 命令失败：{detail.strip()}")
    return result


def _container_name(kind: str, submission_id: int) -> str:
    suffix = uuid.uuid4().hex[:10]
    return f"local-oj-{kind}-{submission_id}-{suffix}"


def _create_container(
    *,
    name: str,
    memory_mb: int,
    workspace_mb: int,
    temp_mb: int,
    pids_limit: int,
) -> str:
    result = _docker(
        [
            "create",
            "--name",
            name,
            "--label",
            "local-oj.sandbox=true",
            "--network",
            "none",
            "--read-only",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges:true",
            "--pids-limit",
            str(pids_limit),
            "--cpus",
            "1.0",
            "--memory",
            f"{memory_mb}m",
            "--memory-swap",
            f"{memory_mb}m",
            "--ulimit",
            "nofile=64:64",
            "--tmpfs",
            f"/workspace:rw,exec,nosuid,nodev,size={workspace_mb}m,uid=10001,gid=10001",
            "--tmpfs",
            f"/tmp:rw,noexec,nosuid,nodev,size={temp_mb}m,uid=10001,gid=10001",
            "--user",
            "10001:10001",
            "--init",
            settings.judge_image,
        ],
        timeout=30,
    )
    container_id = _decode(result.stdout).strip()
    _docker(["start", container_id], timeout=15)
    return container_id


def _remove_container(container_id: str | None) -> None:
    if not container_id:
        return
    _docker(["rm", "-f", container_id], timeout=15, check=False)


def _write_container_file(container_id: str, path: str, content: bytes, executable: bool = False) -> None:
    _docker(
        ["exec", "-i", container_id, "sh", "-c", f"cat > {path}"],
        input_data=content,
        timeout=15,
    )
    if executable:
        _docker(["exec", container_id, "chmod", "700", path], timeout=5)


def cleanup_orphaned_sandboxes() -> None:
    result = _docker(
        ["ps", "-aq", "--filter", "label=local-oj.sandbox=true"],
        timeout=15,
        check=False,
    )
    ids = _decode(result.stdout).split()
    if ids:
        _docker(["rm", "-f", *ids], timeout=30, check=False)


def _compile(submission: Submission, output_path: Path) -> tuple[bool, str]:
    filename = "main.c" if submission.language == "c" else "main.cpp"
    compiler = "gcc" if submission.language == "c" else "g++"
    standard = "-std=c17" if submission.language == "c" else "-std=c++17"
    container_id: str | None = None

    try:
        container_id = _create_container(
            name=_container_name("compile", submission.id),
            memory_mb=COMPILE_MEMORY_MB,
            workspace_mb=128,
            temp_mb=32,
            pids_limit=128,
        )
        source_path = output_path.parent / filename
        source_path.write_text(submission.source_code, encoding="utf-8", newline="\n")
        _write_container_file(
            container_id,
            f"/workspace/{filename}",
            source_path.read_bytes(),
        )
        result = _docker(
            [
                "exec",
                container_id,
                "/usr/bin/timeout",
                "-k",
                "1s",
                f"{COMPILE_TIMEOUT_SECONDS}s",
                compiler,
                standard,
                "-O2",
                "-pipe",
                "-DONLINE_JUDGE",
                f"/workspace/{filename}",
                "-o",
                "/workspace/main",
            ],
            timeout=COMPILE_TIMEOUT_SECONDS + 5,
            check=False,
        )
        diagnostics = _decode((result.stdout or b"") + (result.stderr or b""))
        if result.returncode != 0:
            if result.returncode in (124, 137):
                diagnostics = "编译超时（最多 15 秒）\n" + diagnostics
            return False, diagnostics.strip()
        size_result = _docker(
            ["exec", container_id, "stat", "-c", "%s", "/workspace/main"],
            timeout=5,
        )
        try:
            binary_size = int(_decode(size_result.stdout).strip())
        except ValueError as exc:
            raise JudgeInfrastructureError("无法读取编译产物大小") from exc
        if binary_size <= 0 or binary_size > MAX_BINARY_BYTES:
            return False, f"编译产物大小异常（上限 {MAX_BINARY_BYTES // 1024 // 1024} MB）"
        binary_result = _docker(
            ["exec", container_id, "cat", "/workspace/main"],
            timeout=15,
        )
        if len(binary_result.stdout) != binary_size:
            raise JudgeInfrastructureError("编译产物读取不完整")
        output_path.write_bytes(binary_result.stdout)
        os.chmod(output_path, 0o700)
        return True, diagnostics.strip()
    finally:
        _remove_container(container_id)


def _oom_killed(container_id: str) -> bool:
    state = _docker(
        ["inspect", "--format", "{{.State.OOMKilled}}", container_id],
        check=False,
        timeout=5,
    )
    if _decode(state.stdout).strip().lower() == "true":
        return True
    events = _docker(
        ["exec", container_id, "cat", "/sys/fs/cgroup/memory.events"],
        check=False,
        timeout=5,
    )
    for line in _decode(events.stdout).splitlines():
        key, _, value = line.partition(" ")
        if key == "oom_kill" and value.isdigit() and int(value) > 0:
            return True
    return False


def _read_container_file(container_id: str, path: str) -> str:
    result = _docker(
        ["exec", container_id, "head", "-c", str(MAX_OUTPUT_BYTES + 1), path],
        timeout=10,
        check=False,
    )
    return _decode(result.stdout, MAX_OUTPUT_BYTES + 1)


def _short_difference(expected: str, actual: str) -> str:
    expected_normalized = normalize_output(expected)
    actual_normalized = normalize_output(actual)
    return (
        "输出与标准答案不一致\n"
        f"期望：{expected_normalized[:300] or '<空>'}\n"
        f"实际：{actual_normalized[:300] or '<空>'}"
    )


def _run_case(
    submission_id: int,
    problem: Problem,
    test_case: TestCase,
    binary_path: Path,
) -> dict:
    container_id: str | None = None
    started = 0.0
    elapsed_ms = 0
    try:
        container_id = _create_container(
            name=_container_name("run", submission_id),
            memory_mb=max(16, problem.memory_limit_mb),
            workspace_mb=32,
            temp_mb=4,
            pids_limit=64,
        )
        _write_container_file(
            container_id,
            "/workspace/main",
            binary_path.read_bytes(),
            executable=True,
        )
        _docker(
            ["exec", "-i", container_id, "sh", "-c", "cat > /workspace/input.txt"],
            input_data=test_case.input_data.encode("utf-8"),
            timeout=10,
        )

        seconds = problem.time_limit_ms / 1000
        cpu_seconds = max(1, math.ceil(seconds))
        command = (
            f"ulimit -f {MAX_OUTPUT_BYTES // 512}; ulimit -t {cpu_seconds}; "
            f"/usr/bin/timeout -k 0.2s {seconds:.3f}s /workspace/main "
            "< /workspace/input.txt > /workspace/actual.txt 2> /workspace/stderr.txt"
        )
        started = time.perf_counter()
        result = _docker(
            ["exec", container_id, "sh", "-c", command],
            timeout=seconds + 3,
            check=False,
        )
        elapsed_ms = max(1, round((time.perf_counter() - started) * 1000))
        oom = _oom_killed(container_id)

        if oom:
            return {
                "status": "Memory Limit Exceeded",
                "time_ms": elapsed_ms,
                "message": f"内存使用超过 {problem.memory_limit_mb} MB",
            }
        if result.returncode == 124 or (
            result.returncode == 137 and elapsed_ms >= problem.time_limit_ms * 0.8
        ):
            return {
                "status": "Time Limit Exceeded",
                "time_ms": elapsed_ms,
                "message": f"运行时间超过 {problem.time_limit_ms} ms",
            }
        if result.returncode != 0:
            stderr = _read_container_file(container_id, "/workspace/stderr.txt")
            detail = stderr.strip() or f"程序异常退出，退出码 {result.returncode}"
            return {
                "status": "Runtime Error",
                "time_ms": elapsed_ms,
                "message": detail[:1000],
            }

        actual = _read_container_file(container_id, "/workspace/actual.txt")
        if len(actual.encode("utf-8")) > MAX_OUTPUT_BYTES:
            return {
                "status": "Runtime Error",
                "time_ms": elapsed_ms,
                "message": f"程序输出超过 {MAX_OUTPUT_BYTES // 1024 // 1024} MB 限制",
            }
        if normalize_output(actual) != normalize_output(test_case.output_data):
            return {
                "status": "Wrong Answer",
                "time_ms": elapsed_ms,
                "message": _short_difference(test_case.output_data, actual),
            }
        return {"status": "Accepted", "time_ms": elapsed_ms, "message": "通过"}
    except JudgeInfrastructureError:
        raise
    except Exception as exc:
        if started:
            elapsed_ms = max(1, round((time.perf_counter() - started) * 1000))
        raise JudgeInfrastructureError(f"测试点运行失败：{exc}") from exc
    finally:
        _remove_container(container_id)


def judge_submission(
    submission: Submission, problem: Problem, test_cases: list[TestCase]
) -> JudgeOutcome:
    if not test_cases:
        return JudgeOutcome(status="System Error", message="题目没有测试点")

    with tempfile.TemporaryDirectory(prefix=f"oj-{submission.id}-") as temp_dir:
        binary_path = Path(temp_dir) / "main"
        compiled, diagnostics = _compile(submission, binary_path)
        if not compiled:
            return JudgeOutcome(
                status="Compile Error",
                message="编译失败",
                compile_output=diagnostics,
            )

        results: list[dict] = []
        final_status = "Accepted"
        max_runtime = 0
        first_failure = "全部测试点通过"
        for index, test_case in enumerate(test_cases, start=1):
            result = _run_case(submission.id, problem, test_case, binary_path)
            result.update({"case": index, "name": test_case.name})
            results.append(result)
            max_runtime = max(max_runtime, result["time_ms"])
            if final_status == "Accepted" and result["status"] != "Accepted":
                final_status = result["status"]
                first_failure = f"测试点 {index}：{result['message']}"

        return JudgeOutcome(
            status=final_status,
            message=first_failure,
            compile_output=diagnostics,
            case_results=results,
            runtime_ms=max_runtime,
        )
