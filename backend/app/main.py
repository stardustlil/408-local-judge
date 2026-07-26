from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session, selectinload

from .config import settings
from .database import Base, SessionLocal, engine, get_db
from .models import Problem, Submission, TestCase
from .question_importer import import_question_bank
from .schemas import (
    ProblemCreate,
    ProblemRead,
    ProblemUpdate,
    StatsRead,
    SubmissionCreate,
    SubmissionRead,
    TestCaseCreate,
    TestCaseRead,
)
from .seed import seed_demo_data


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    if settings.seed_demo_data:
        with SessionLocal() as db:
            seed_demo_data(db)
    if settings.import_408_questions:
        with SessionLocal() as db:
            import_question_bank(db)
    yield


app = FastAPI(title="408 Local Judge API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:3000", "http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_problem_or_404(db: Session, problem_id: int) -> Problem:
    problem = db.get(Problem, problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail="题目不存在")
    return problem


def problem_reads(db: Session, problems: list[Problem]) -> list[ProblemRead]:
    if not problems:
        return []
    problem_ids = [problem.id for problem in problems]
    test_counts = dict(
        db.execute(
            select(TestCase.problem_id, func.count(TestCase.id))
            .where(TestCase.problem_id.in_(problem_ids))
            .group_by(TestCase.problem_id)
        ).all()
    )
    submission_rows = db.execute(
        select(
            Submission.problem_id,
            func.count(Submission.id),
            func.count(Submission.id).filter(Submission.status == "Accepted"),
        )
        .where(Submission.problem_id.in_(problem_ids))
        .group_by(Submission.problem_id)
    ).all()
    submission_stats = {
        problem_id: (submission_count, accepted_count)
        for problem_id, submission_count, accepted_count in submission_rows
    }

    result: list[ProblemRead] = []
    for problem in problems:
        data = ProblemRead.model_validate(problem).model_dump()
        submission_count, accepted_count = submission_stats.get(problem.id, (0, 0))
        data.update(
            test_case_count=test_counts.get(problem.id, 0),
            submission_count=submission_count,
            accepted=accepted_count > 0,
        )
        result.append(ProblemRead(**data))
    return result


def problem_read(db: Session, problem: Problem) -> ProblemRead:
    return problem_reads(db, [problem])[0]


def submission_read(submission: Submission) -> SubmissionRead:
    data = SubmissionRead.model_validate(
        {
            **submission.__dict__,
            "problem_title": submission.problem.title,
        }
    )
    return data


@app.get("/api/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok"}


@app.get("/api/stats", response_model=StatsRead)
def get_stats(db: Session = Depends(get_db)):
    problem_count = db.scalar(select(func.count(Problem.id))) or 0
    submission_count = db.scalar(select(func.count(Submission.id))) or 0
    accepted_count = db.scalar(
        select(func.count(Submission.id)).where(Submission.status == "Accepted")
    ) or 0
    solved_count = db.scalar(
        select(func.count(func.distinct(Submission.problem_id))).where(
            Submission.status == "Accepted"
        )
    ) or 0
    tag_counts: dict[str, int] = {}
    for tags in db.scalars(select(Problem.tags)).all():
        for tag in tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    return StatsRead(
        problem_count=problem_count,
        solved_count=solved_count,
        submission_count=submission_count,
        accepted_count=accepted_count,
        tag_counts=tag_counts,
    )


@app.get("/api/problems", response_model=list[ProblemRead])
def list_problems(
    search: str | None = Query(default=None, max_length=100),
    tag: str | None = Query(default=None, max_length=30),
    db: Session = Depends(get_db),
):
    stmt = select(Problem)
    if search:
        stmt = stmt.where(Problem.title.ilike(f"%{search}%"))
    stmt = stmt.order_by(Problem.id)
    problems = db.scalars(stmt).all()
    if tag:
        problems = [problem for problem in problems if tag in problem.tags]
    return problem_reads(db, list(problems))


@app.post("/api/problems", response_model=ProblemRead, status_code=status.HTTP_201_CREATED)
def create_problem(payload: ProblemCreate, db: Session = Depends(get_db)):
    problem = Problem(**payload.model_dump(mode="json"))
    db.add(problem)
    db.commit()
    return problem_read(db, get_problem_or_404(db, problem.id))


@app.get("/api/problems/{problem_id}", response_model=ProblemRead)
def get_problem(problem_id: int, db: Session = Depends(get_db)):
    return problem_read(db, get_problem_or_404(db, problem_id))


@app.put("/api/problems/{problem_id}", response_model=ProblemRead)
def update_problem(problem_id: int, payload: ProblemUpdate, db: Session = Depends(get_db)):
    problem = get_problem_or_404(db, problem_id)
    for field, value in payload.model_dump(mode="json").items():
        setattr(problem, field, value)
    db.commit()
    return problem_read(db, get_problem_or_404(db, problem_id))


@app.delete("/api/problems/{problem_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_problem(problem_id: int, db: Session = Depends(get_db)):
    problem = get_problem_or_404(db, problem_id)
    db.delete(problem)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/api/problems/{problem_id}/test-cases", response_model=list[TestCaseRead])
def list_test_cases(problem_id: int, db: Session = Depends(get_db)):
    get_problem_or_404(db, problem_id)
    return db.scalars(
        select(TestCase)
        .where(TestCase.problem_id == problem_id)
        .order_by(TestCase.ordinal, TestCase.id)
    ).all()


def next_test_ordinal(db: Session, problem_id: int) -> int:
    current = db.scalar(
        select(func.max(TestCase.ordinal)).where(TestCase.problem_id == problem_id)
    )
    return (current or 0) + 1


@app.post(
    "/api/problems/{problem_id}/test-cases",
    response_model=TestCaseRead,
    status_code=status.HTTP_201_CREATED,
)
def create_test_case(problem_id: int, payload: TestCaseCreate, db: Session = Depends(get_db)):
    get_problem_or_404(db, problem_id)
    test_case = TestCase(
        problem_id=problem_id,
        ordinal=next_test_ordinal(db, problem_id),
        **payload.model_dump(),
    )
    db.add(test_case)
    db.commit()
    db.refresh(test_case)
    return test_case


async def read_utf8_upload(file: UploadFile, label: str) -> str:
    content = await file.read(settings.max_test_file_bytes + 1)
    if len(content) > settings.max_test_file_bytes:
        raise HTTPException(status_code=413, detail=f"{label} 文件不能超过 2 MB")
    try:
        return content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"{label} 文件必须为 UTF-8 文本") from exc


@app.post(
    "/api/problems/{problem_id}/test-cases/upload",
    response_model=TestCaseRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_test_case(
    problem_id: int,
    name: str = Form(default="上传测试点"),
    input_file: UploadFile = File(...),
    output_file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    get_problem_or_404(db, problem_id)
    input_data = await read_utf8_upload(input_file, "input")
    output_data = await read_utf8_upload(output_file, "output")
    test_case = TestCase(
        problem_id=problem_id,
        name=name.strip()[:120] or "上传测试点",
        ordinal=next_test_ordinal(db, problem_id),
        input_data=input_data,
        output_data=output_data,
    )
    db.add(test_case)
    db.commit()
    db.refresh(test_case)
    return test_case


@app.delete(
    "/api/problems/{problem_id}/test-cases/{test_case_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_test_case(problem_id: int, test_case_id: int, db: Session = Depends(get_db)):
    test_case = db.scalar(
        select(TestCase).where(
            TestCase.id == test_case_id, TestCase.problem_id == problem_id
        )
    )
    if not test_case:
        raise HTTPException(status_code=404, detail="测试点不存在")
    db.delete(test_case)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post(
    "/api/problems/{problem_id}/submissions",
    response_model=SubmissionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_submission(
    problem_id: int, payload: SubmissionCreate, db: Session = Depends(get_db)
):
    problem = get_problem_or_404(db, problem_id)
    if not db.scalar(select(TestCase.id).where(TestCase.problem_id == problem_id).limit(1)):
        raise HTTPException(status_code=400, detail="该题尚未配置测试点")
    if len(payload.source_code.encode("utf-8")) > settings.max_source_bytes:
        raise HTTPException(status_code=413, detail="源代码不能超过 128 KB")
    submission = Submission(problem_id=problem_id, **payload.model_dump())
    db.add(submission)
    db.commit()
    db.refresh(submission)
    submission.problem = problem
    return submission_read(submission)


@app.get("/api/submissions", response_model=list[SubmissionRead])
def list_submissions(
    problem_id: int | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    stmt = select(Submission).options(selectinload(Submission.problem))
    if problem_id is not None:
        stmt = stmt.where(Submission.problem_id == problem_id)
    submissions = db.scalars(stmt.order_by(Submission.id.desc()).limit(limit)).all()
    return [submission_read(item) for item in submissions]


@app.get("/api/submissions/{submission_id}", response_model=SubmissionRead)
def get_submission(submission_id: int, db: Session = Depends(get_db)):
    submission = db.scalar(
        select(Submission)
        .where(Submission.id == submission_id)
        .options(selectinload(Submission.problem))
    )
    if not submission:
        raise HTTPException(status_code=404, detail="提交记录不存在")
    return submission_read(submission)
