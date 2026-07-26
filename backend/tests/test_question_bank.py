import itertools
import random
from collections import Counter

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.database import Base
from app.judge import MAX_OUTPUT_BYTES
from app.models import Problem
from app.question_bank import (
    BANK_VERSION,
    SOURCE_PREFIX,
    _partition_difference,
    _suffix_products,
    _triple_distance,
    _unique_topological,
    build_question_bank,
    source_marker,
)
from app.question_importer import import_question_bank


def test_question_bank_is_complete_and_deterministic():
    first = build_question_bank()
    second = build_question_bank()

    assert first == second
    assert len(first) == 17
    assert {problem.year for problem in first} == set(range(2009, 2026))
    assert Counter(problem.year for problem in first) == {
        year: 1 for year in range(2009, 2026)
    }
    assert all(problem.year != 2026 for problem in first)
    assert len({problem.key for problem in first}) == len(first)
    assert sum(len(problem.cases) for problem in first) == 188

    for problem in first:
        assert f"【真题（{problem.year}）】" in problem.description
        assert source_marker(problem.key) in problem.description
        assert f"version:{BANK_VERSION}" in problem.description
        assert "## 题目描述" in problem.description
        assert "## 输入格式" in problem.description
        assert "## 输出格式" in problem.description
        assert "## 输入输出样例 #1" in problem.description
        assert "\t" not in problem.description
        assert len(problem.cases) >= 8
        assert len({case.name for case in problem.cases}) == len(problem.cases)
        assert all(case.input_data.endswith("\n") for case in problem.cases)
        assert all(case.output_data.endswith("\n") for case in problem.cases)
        assert all(len(case.input_data.encode("utf-8")) <= 2 * 1024 * 1024 for case in problem.cases)
        assert all(len(case.output_data.encode("utf-8")) <= MAX_OUTPUT_BYTES for case in problem.cases)


def test_import_is_idempotent_and_preserves_custom_problems():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        custom = Problem(
            title="我的自定义题目",
            description="# 我的自定义题目\n\n不会被批量导入覆盖。",
            tags=["自定义"],
        )
        db.add(custom)
        db.commit()

        first = import_question_bank(db)
        assert first.created == 17
        assert first.updated == 0
        assert first.unchanged == 0
        assert first.test_cases == 188

        second = import_question_bank(db)
        assert second.created == 0
        assert second.updated == 0
        assert second.unchanged == 17

        stale = Problem(
            title="已经退出目录的受管题目",
            description=f"# 旧题\n\n<!-- {SOURCE_PREFIX}legacy-question;version:0 -->",
            tags=["408真题"],
        )
        db.add(stale)
        db.commit()
        stale_id = stale.id

        without_prune = import_question_bank(db)
        assert without_prune.removed == 0
        assert db.get(Problem, stale_id) is not None

        pruned = import_question_bank(db, prune_stale=True)
        assert pruned.removed == 1
        assert db.get(Problem, stale_id) is None

        stored_custom = db.scalar(select(Problem).where(Problem.title == "我的自定义题目"))
        assert stored_custom is not None
        assert stored_custom.description.endswith("不会被批量导入覆盖。")

        imported = db.scalar(select(Problem).where(Problem.title.startswith("408-2009")))
        assert imported is not None
        imported.title = "被意外改动"
        imported.test_cases[0].output_data = "corrupt\n"
        db.commit()

        repaired = import_question_bank(db)
        assert repaired.created == 0
        assert repaired.updated == 1
        assert repaired.unchanged == 16
        assert imported.title.startswith("408-2009")
        assert imported.test_cases[0].output_data != "corrupt\n"


def test_reference_algorithms_match_independent_brute_force():
    rng = random.Random(408)
    for size in range(2, 9):
        for _ in range(12):
            values = [rng.randint(1, 30) for _ in range(size)]
            subset_size = size // 2
            total = sum(values)
            expected_partition = max(
                abs(total - 2 * sum(values[index] for index in subset))
                for subset in itertools.combinations(range(size), subset_size)
            )
            assert _partition_difference(values) == (size % 2, expected_partition)

            expected_suffix = [
                max(values[index] * value for value in values[index:])
                for index in range(size)
            ]
            assert _suffix_products(values) == expected_suffix

    for _ in range(80):
        arrays = [sorted(rng.randint(-20, 20) for _ in range(rng.randint(1, 5))) for _ in range(3)]
        expected_distance = min(
            abs(a - b) + abs(b - c) + abs(c - a)
            for a in arrays[0]
            for b in arrays[1]
            for c in arrays[2]
        )
        assert _triple_distance(*arrays) == expected_distance

    for size in range(1, 7):
        candidates = [(left, right) for left in range(1, size + 1) for right in range(left + 1, size + 1)]
        for _ in range(20):
            edges = [edge for edge in candidates if rng.random() < 0.35]
            valid_orders = sum(
                all(order.index(left) < order.index(right) for left, right in edges)
                for order in itertools.permutations(range(1, size + 1))
            )
            assert _unique_topological(size, edges) == int(valid_orders == 1)
