import argparse

from .database import Base, SessionLocal, engine
from .question_importer import import_question_bank


def main() -> None:
    parser = argparse.ArgumentParser(description="导入本地 408 算法题库")
    parser.add_argument(
        "--prune-stale",
        action="store_true",
        help="删除已不在当前目录中的受管题目；不会删除自定义题目",
    )
    args = parser.parse_args()
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        summary = import_question_bank(db, prune_stale=args.prune_stale)
    print(
        "408 题库导入完成："
        f"新增 {summary.created}，更新 {summary.updated}，"
        f"未变化 {summary.unchanged}，清理 {summary.removed}，"
        f"测试点 {summary.test_cases}。"
    )


if __name__ == "__main__":
    main()
