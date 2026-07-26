from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .models import Problem, TestCase
from .question_bank import SOURCE_PREFIX, QuestionBankProblem, build_question_bank


SOURCE_PATTERN = re.compile(rf"<!-- {re.escape(SOURCE_PREFIX)}([^;]+);version:\d+ -->")


@dataclass(frozen=True)
class ImportSummary:
    created: int = 0
    updated: int = 0
    unchanged: int = 0
    removed: int = 0
    test_cases: int = 0


def _source_key(description: str) -> str | None:
    match = SOURCE_PATTERN.search(description)
    return match.group(1) if match else None


def _problem_values(spec: QuestionBankProblem) -> dict:
    return {
        "title": spec.title,
        "description": spec.description,
        "input_format": "",
        "output_format": "",
        "constraints": "",
        "samples": [],
        "tags": list(spec.tags),
        "time_limit_ms": spec.time_limit_ms,
        "memory_limit_mb": spec.memory_limit_mb,
    }


def _case_values(spec: QuestionBankProblem) -> list[tuple[str, int, str, str]]:
    return [
        (item.name, ordinal, item.input_data, item.output_data)
        for ordinal, item in enumerate(spec.cases, start=1)
    ]


def _stored_case_values(problem: Problem) -> list[tuple[str, int, str, str]]:
    return [
        (item.name, item.ordinal, item.input_data, item.output_data)
        for item in sorted(problem.test_cases, key=lambda case: (case.ordinal, case.id))
    ]


def _metadata_matches(problem: Problem, values: dict) -> bool:
    return all(getattr(problem, field) == value for field, value in values.items())


def _replace_cases(problem: Problem, spec: QuestionBankProblem) -> None:
    problem.test_cases.clear()
    for ordinal, item in enumerate(spec.cases, start=1):
        problem.test_cases.append(
            TestCase(
                name=item.name,
                ordinal=ordinal,
                input_data=item.input_data,
                output_data=item.output_data,
            )
        )


def import_question_bank(db: Session, *, prune_stale: bool = False) -> ImportSummary:
    existing = db.scalars(
        select(Problem)
        .where(Problem.description.contains(f"<!-- {SOURCE_PREFIX}"))
        .options(selectinload(Problem.test_cases))
    ).all()
    by_key: dict[str, Problem] = {}
    for problem in existing:
        key = _source_key(problem.description)
        if key is None:
            continue
        if key in by_key:
            raise ValueError(f"数据库中存在重复的 408 题库来源标识：{key}")
        by_key[key] = problem

    specs = build_question_bank()
    active_keys = {spec.key for spec in specs}
    stale = [problem for key, problem in by_key.items() if key not in active_keys]

    removed = 0
    if prune_stale:
        for problem in stale:
            db.delete(problem)
            removed += 1

    created = updated = unchanged = 0
    total_cases = 0
    for spec in specs:
        values = _problem_values(spec)
        expected_cases = _case_values(spec)
        total_cases += len(expected_cases)
        problem = by_key.get(spec.key)
        if problem is None:
            problem = Problem(**values)
            _replace_cases(problem, spec)
            db.add(problem)
            created += 1
            continue

        metadata_changed = not _metadata_matches(problem, values)
        cases_changed = _stored_case_values(problem) != expected_cases
        if not metadata_changed and not cases_changed:
            unchanged += 1
            continue
        for field, value in values.items():
            setattr(problem, field, value)
        if cases_changed:
            _replace_cases(problem, spec)
        updated += 1

    db.commit()
    return ImportSummary(
        created=created,
        updated=updated,
        unchanged=unchanged,
        removed=removed,
        test_cases=total_cases,
    )
