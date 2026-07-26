from __future__ import annotations

import json
import os
import time
from typing import Any
from urllib.request import Request, urlopen


API_URL = os.environ.get("OJ_API_URL", "http://127.0.0.1:8000/api").rstrip("/")
FRONTEND_URL = os.environ.get("OJ_FRONTEND_URL", "http://127.0.0.1:3000").rstrip("/")
PENDING_STATUSES = {"Queued", "Judging"}

CPP_SOLUTION = r"""#include <iostream>

int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);

    long long a, b;
    if (!(std::cin >> a >> b)) return 0;
    std::cout << a + b << '\n';
    return 0;
}
"""

C_SOLUTION = r"""#include <stdio.h>

int main(void) {
    long long a, b;
    if (scanf("%lld%lld", &a, &b) != 2) return 0;
    printf("%lld\n", a + b);
    return 0;
}
"""

SMOKE_CASES = [
    {"name": "positive", "input_data": "1 2\n", "output_data": "3\n"},
    {"name": "mixed signs", "input_data": "-7 5\n", "output_data": "-2\n"},
    {
        "name": "64-bit values",
        "input_data": "1000000000000 2000000000000\n",
        "output_data": "3000000000000\n",
    },
]


def request_json(path: str, payload: dict[str, Any] | None = None) -> Any:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(
        f"{API_URL}{path}",
        data=data,
        headers={"Content-Type": "application/json"} if data else {},
        method="POST" if data else "GET",
    )
    with urlopen(request, timeout=10) as response:
        return json.load(response)


def verify_frontend() -> None:
    with urlopen(FRONTEND_URL, timeout=10) as response:
        html = response.read().decode("utf-8")
    assert "408 Local Judge" in html, "frontend title is missing"


def wait_for_result(submission_id: int, timeout_seconds: float = 120) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    latest: dict[str, Any] | None = None
    while time.monotonic() < deadline:
        latest = request_json(f"/submissions/{submission_id}")
        if latest["status"] not in PENDING_STATUSES:
            return latest
        time.sleep(0.5)
    raise TimeoutError(f"submission {submission_id} did not finish: {latest}")


def verify_solution(problem_id: int, language: str, source_code: str) -> None:
    submission = request_json(
        f"/problems/{problem_id}/submissions",
        {"language": language, "source_code": source_code},
    )
    result = wait_for_result(submission["id"])
    assert result["status"] == "Accepted", json.dumps(result, ensure_ascii=False)
    assert len(result["case_results"]) == len(SMOKE_CASES), result
    assert all(case["status"] == "Accepted" for case in result["case_results"]), result
    print(f"{language} submission #{submission['id']}: Accepted")


def main() -> None:
    health = request_json("/health")
    assert health == {"status": "ok"}, health
    verify_frontend()

    stats = request_json("/stats")
    assert stats["problem_count"] == 17, stats
    assert stats["tag_counts"].get("408真题") == 17, stats

    problems = request_json("/problems")
    assert len(problems) == 17, problems
    assert sum(problem["test_case_count"] for problem in problems) == 188, problems

    smoke_problem = request_json(
        "/problems",
        {
            "title": "CI smoke: sum two integers",
            "description": "# CI smoke\n\nRead two integers and output their sum.",
            "tags": ["CI"],
            "time_limit_ms": 1000,
            "memory_limit_mb": 64,
        },
    )
    for test_case in SMOKE_CASES:
        request_json(f"/problems/{smoke_problem['id']}/test-cases", test_case)

    verify_solution(smoke_problem["id"], "cpp", CPP_SOLUTION)
    verify_solution(smoke_problem["id"], "c", C_SOLUTION)
    print("Docker smoke test passed: 17 problems, 188 cases, C/C++ judge accepted")


if __name__ == "__main__":
    main()
