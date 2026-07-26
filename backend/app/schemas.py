from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Sample(BaseModel):
    input: str = ""
    output: str = ""


class ProblemBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    input_format: str = ""
    output_format: str = ""
    constraints: str = ""
    samples: list[Sample] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    time_limit_ms: int = Field(default=1000, ge=100, le=10_000)
    memory_limit_mb: int = Field(default=128, ge=16, le=1024)

    @field_validator("tags")
    @classmethod
    def clean_tags(cls, tags: list[str]) -> list[str]:
        cleaned: list[str] = []
        for tag in tags:
            value = tag.strip()
            if value and value not in cleaned:
                cleaned.append(value[:30])
        return cleaned[:20]


class ProblemCreate(ProblemBase):
    pass


class ProblemUpdate(ProblemBase):
    pass


class ProblemRead(ProblemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    test_case_count: int = 0
    submission_count: int = 0
    accepted: bool = False
    created_at: datetime
    updated_at: datetime


class TestCaseCreate(BaseModel):
    name: str = Field(default="测试点", max_length=120)
    input_data: str = ""
    output_data: str = ""


class TestCaseRead(TestCaseCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    problem_id: int
    ordinal: int
    created_at: datetime


class SubmissionCreate(BaseModel):
    language: str
    source_code: str = Field(min_length=1)

    @field_validator("language")
    @classmethod
    def validate_language(cls, language: str) -> str:
        normalized = language.lower().strip()
        aliases = {"cpp": "cpp", "c++": "cpp", "c": "c"}
        if normalized not in aliases:
            raise ValueError("仅支持 C 和 C++")
        return aliases[normalized]


class SubmissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    problem_id: int
    problem_title: str
    language: str
    source_code: str
    status: str
    compile_output: str
    judge_message: str
    case_results: list
    runtime_ms: int | None
    memory_kb: int | None
    created_at: datetime
    updated_at: datetime


class StatsRead(BaseModel):
    problem_count: int
    solved_count: int
    submission_count: int
    accepted_count: int
    tag_counts: dict[str, int]

