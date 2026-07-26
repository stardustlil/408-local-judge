from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import Problem, TestCase


DEMO_PROBLEMS = [
    {
        "title": "反转顺序表",
        "description": "给定一个长度为 n 的顺序表，请将其中的元素原地逆序，并输出逆序后的序列。",
        "input_format": "第一行输入整数 n。\n第二行输入 n 个整数，整数之间以空格分隔。",
        "output_format": "输出逆序后的 n 个整数，整数之间以一个空格分隔。",
        "constraints": "1 <= n <= 100000\n-10^9 <= a_i <= 10^9",
        "samples": [{"input": "5\n1 2 3 4 5\n", "output": "5 4 3 2 1\n"}],
        "tags": ["顺序表", "数组"],
        "time_limit_ms": 1000,
        "memory_limit_mb": 128,
        "tests": [
            ("最小规模", "1\n42\n", "42\n"),
            ("普通序列", "5\n1 2 3 4 5\n", "5 4 3 2 1\n"),
            ("含负数", "6\n-1 0 8 -3 8 2\n", "2 8 -3 8 0 -1\n"),
        ],
    },
    {
        "title": "有效括号序列",
        "description": "给定一个只包含圆括号、方括号和花括号的字符串，判断括号是否正确匹配。空栈遇到右括号、类型不匹配或遍历结束后栈非空，均为无效序列。",
        "input_format": "输入一行非空字符串，仅包含 ()[]{}。",
        "output_format": "若括号序列有效，输出 YES；否则输出 NO。",
        "constraints": "1 <= 字符串长度 <= 100000",
        "samples": [
            {"input": "([]{})\n", "output": "YES\n"},
            {"input": "([)]\n", "output": "NO\n"},
        ],
        "tags": ["栈", "字符串"],
        "time_limit_ms": 1000,
        "memory_limit_mb": 128,
        "tests": [
            ("完全匹配", "([]{})\n", "YES\n"),
            ("交叉括号", "([)]\n", "NO\n"),
            ("缺少右括号", "(((()\n", "NO\n"),
            ("连续结构", "{}[]()\n", "YES\n"),
        ],
    },
    {
        "title": "二叉搜索树层序遍历",
        "description": "按给定顺序将互不相同的整数插入一棵二叉搜索树，并输出该树的层序遍历结果。左子树结点值小于根结点，右子树结点值大于根结点。",
        "input_format": "第一行输入整数 n。\n第二行输入 n 个互不相同的整数，表示插入顺序。",
        "output_format": "输出二叉搜索树的层序遍历序列，整数之间以一个空格分隔。",
        "constraints": "1 <= n <= 10000\n-10^9 <= key <= 10^9",
        "samples": [{"input": "7\n4 2 6 1 3 5 7\n", "output": "4 2 6 1 3 5 7\n"}],
        "tags": ["树", "二叉搜索树", "队列"],
        "time_limit_ms": 1500,
        "memory_limit_mb": 128,
        "tests": [
            ("平衡结构", "7\n4 2 6 1 3 5 7\n", "4 2 6 1 3 5 7\n"),
            ("左斜树", "5\n5 4 3 2 1\n", "5 4 3 2 1\n"),
            ("一般结构", "8\n8 3 10 1 6 14 4 7\n", "8 3 10 1 6 14 4 7\n"),
        ],
    },
]


def seed_demo_data(db: Session) -> None:
    if db.scalar(select(func.count(Problem.id))):
        return

    for item in DEMO_PROBLEMS:
        tests = item["tests"]
        problem_data = {key: value for key, value in item.items() if key != "tests"}
        problem = Problem(**problem_data)
        db.add(problem)
        db.flush()
        for index, (name, input_data, output_data) in enumerate(tests, start=1):
            db.add(
                TestCase(
                    problem_id=problem.id,
                    name=name,
                    ordinal=index,
                    input_data=input_data,
                    output_data=output_data,
                )
            )
    db.commit()

