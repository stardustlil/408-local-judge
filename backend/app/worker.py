import logging
import signal
import time

from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from .config import settings
from .database import Base, SessionLocal, engine
from .judge import JudgeInfrastructureError, cleanup_orphaned_sandboxes, judge_submission
from .models import Problem, Submission


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("judge-worker")
running = True


def stop_worker(signum, _frame):
    global running
    logger.info("收到信号 %s，判题 worker 将退出", signum)
    running = False


def claim_submission() -> int | None:
    with SessionLocal() as db, db.begin():
        submission = db.scalar(
            select(Submission)
            .where(Submission.status == "Queued")
            .order_by(Submission.id)
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        if not submission:
            return None
        submission.status = "Judging"
        submission.judge_message = "正在编译"
        db.flush()
        return submission.id


def process_submission(submission_id: int) -> None:
    with SessionLocal() as db:
        submission = db.scalar(
            select(Submission)
            .where(Submission.id == submission_id)
            .options(
                selectinload(Submission.problem).selectinload(Problem.test_cases)
            )
        )
        if not submission:
            return
        problem = submission.problem
        test_cases = list(problem.test_cases)

    logger.info("开始判题 submission=%s tests=%s", submission_id, len(test_cases))
    try:
        outcome = judge_submission(submission, problem, test_cases)
    except JudgeInfrastructureError as exc:
        logger.exception("判题基础设施错误 submission=%s", submission_id)
        with SessionLocal() as db:
            current = db.get(Submission, submission_id)
            if current:
                current.status = "System Error"
                current.judge_message = str(exc)[:2000]
                db.commit()
        return
    except Exception as exc:
        logger.exception("未处理的判题错误 submission=%s", submission_id)
        with SessionLocal() as db:
            current = db.get(Submission, submission_id)
            if current:
                current.status = "System Error"
                current.judge_message = f"判题器异常：{exc}"[:2000]
                db.commit()
        return

    with SessionLocal() as db:
        current = db.get(Submission, submission_id)
        if not current:
            return
        current.status = outcome.status
        current.judge_message = outcome.message
        current.compile_output = outcome.compile_output
        current.case_results = outcome.case_results
        current.runtime_ms = outcome.runtime_ms
        current.memory_kb = outcome.memory_kb
        db.commit()
    logger.info("判题完成 submission=%s status=%s", submission_id, outcome.status)


def main() -> None:
    global running
    signal.signal(signal.SIGTERM, stop_worker)
    signal.signal(signal.SIGINT, stop_worker)
    Base.metadata.create_all(bind=engine)
    cleanup_orphaned_sandboxes()
    with SessionLocal() as db:
        db.execute(
            update(Submission)
            .where(Submission.status == "Judging")
            .values(status="Queued", judge_message="等待重新判题")
        )
        db.commit()
    logger.info("判题 worker 已启动，沙箱镜像：%s", settings.judge_image)

    while running:
        submission_id = claim_submission()
        if submission_id is None:
            time.sleep(settings.judge_poll_interval)
            continue
        process_submission(submission_id)


if __name__ == "__main__":
    main()
