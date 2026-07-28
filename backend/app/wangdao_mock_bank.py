from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable

from .question_bank import GeneratedCase, QuestionBankProblem, SOURCE_PREFIX


MOCK_BANK_VERSION = 1
MOCK_ALGORITHM_KEYS = (
    "wangdao-2026-v1-q42-balanced-binary-tree",
    "wangdao-2026-v2-q42-position-parity",
    "wangdao-2026-v3-q42-rotated-array-minimum",
    "wangdao-2026-v4-q42-mirror-similar-trees",
    "wangdao-2026-v5-q42-stable-index-parity",
    "wangdao-2026-v6-q42-vertex-indegree",
    "wangdao-2026-v7-q42-child-sibling-tree-degree",
    "wangdao-2026-v8-q42-linked-list-palindrome",
)

VOLUME_NAMES = {
    1: "卷一",
    2: "卷二",
    3: "卷三",
    4: "卷四",
    5: "卷五",
    6: "卷六",
    7: "卷七",
    8: "卷八",
}


@dataclass(frozen=True)
class MockProblemDefinition:
    key: str
    volume: int
    question: str
    title: str
    body: str
    input_format: str
    output_format: str
    constraints: str
    tags: tuple[str, ...]
    build_cases: Callable[[random.Random], list[GeneratedCase]]
    time_limit_ms: int = 1000
    memory_limit_mb: int = 128
    adaptation: str = "本题将原卷中的函数式算法设计要求改编为标准输入输出形式。"


def _case(name: str, input_data: str, output_data: str) -> GeneratedCase:
    return GeneratedCase(
        name=name,
        input_data=input_data.rstrip() + "\n",
        output_data=output_data.rstrip() + "\n",
    )


def _line(values: list[int] | list[str]) -> str:
    return " ".join(map(str, values))


def mock_source_marker(key: str) -> str:
    return f"<!-- {SOURCE_PREFIX}{key};version:{MOCK_BANK_VERSION} -->"


def _statement(definition: MockProblemDefinition, sample: GeneratedCase) -> str:
    volume = VOLUME_NAMES[definition.volume]
    title = f"王道模拟-{volume} {definition.title}"
    return f"""# {title}

**【王道模拟题（2026·{volume}）】**

> 来源：2026 王道计算机 408 八套卷·{volume}数据结构综合应用题第 {definition.question} 题。{definition.adaptation}

## 题目描述

{definition.body.strip()}

## 输入格式

{definition.input_format.strip()}

## 输出格式

{definition.output_format.strip()}

## 输入输出样例 #1

### 输入 #1

```
{sample.input_data.rstrip()}
```

### 输出 #1

```
{sample.output_data.rstrip()}
```

## 说明/提示

**【数据范围】**

{definition.constraints.strip()}

**【改编说明】**

原卷考查算法设计思想、数据结构操作与复杂度分析，没有规定完整的标准输入输出。本题保留原考点，并补充了适合本地 OJ 自动判定的输入输出约定；题面不是对原卷文字的逐字转载。

{mock_source_marker(definition.key)}
"""


def _binary_tree_input(children: list[tuple[int, int]], root: int) -> str:
    n = len(children) - 1
    rows = "\n".join(f"{left} {right}" for left, right in children[1:])
    return f"{n} {root}" + (f"\n{rows}" if rows else "")


def _binary_tree_height_balance(
    children: list[tuple[int, int]], root: int
) -> tuple[int, int]:
    if root == 0:
        return 0, 1
    heights = [0] * len(children)
    balanced = True
    stack = [(root, False)]
    while stack:
        node, visited = stack.pop()
        if visited:
            left, right = children[node]
            if abs(heights[left] - heights[right]) > 1:
                balanced = False
            heights[node] = max(heights[left], heights[right]) + 1
            continue
        stack.append((node, True))
        left, right = children[node]
        if right:
            stack.append((right, False))
        if left:
            stack.append((left, False))
    return heights[root], int(balanced)


def _balanced_tree_case(
    name: str, children: list[tuple[int, int]], root: int
) -> GeneratedCase:
    height, balanced = _binary_tree_height_balance(children, root)
    return _case(name, _binary_tree_input(children, root), f"{height} {balanced}")


def _random_binary_tree(rng: random.Random, n: int) -> tuple[list[tuple[int, int]], int]:
    mutable = [[0, 0] for _ in range(n + 1)]
    available = [1]
    for node in range(2, n + 1):
        parent = rng.choice(available)
        empty_sides = [side for side in (0, 1) if mutable[parent][side] == 0]
        side = rng.choice(empty_sides)
        mutable[parent][side] = node
        if mutable[parent][0] and mutable[parent][1]:
            available.remove(parent)
        available.append(node)
    return [(left, right) for left, right in mutable], 1


def _remap_binary_tree(
    rng: random.Random, children: list[tuple[int, int]], root: int
) -> tuple[list[tuple[int, int]], int]:
    n = len(children) - 1
    shuffled = list(range(1, n + 1))
    rng.shuffle(shuffled)
    mapping = [0] + shuffled
    remapped = [(0, 0) for _ in range(n + 1)]
    for old in range(1, n + 1):
        left, right = children[old]
        remapped[mapping[old]] = (
            mapping[left] if left else 0,
            mapping[right] if right else 0,
        )
    return remapped, mapping[root] if root else 0


def _balanced_tree_cases(rng: random.Random) -> list[GeneratedCase]:
    cases = [
        _balanced_tree_case(
            "满二叉树",
            [(0, 0), (2, 3), (4, 5), (6, 7), (0, 0), (0, 0), (0, 0), (0, 0)],
            1,
        ),
        _balanced_tree_case("空树", [(0, 0)], 0),
        _balanced_tree_case("单结点", [(0, 0), (0, 0)], 1),
        _balanced_tree_case("两层左子树", [(0, 0), (2, 0), (0, 0)], 1),
        _balanced_tree_case(
            "左斜三层",
            [(0, 0), (2, 0), (3, 0), (0, 0)],
            1,
        ),
        _balanced_tree_case(
            "根结点平衡但内部失衡",
            [(0, 0), (2, 3), (4, 0), (0, 6), (5, 0), (0, 0), (0, 0)],
            1,
        ),
        _balanced_tree_case(
            "之字形失衡",
            [(0, 0), (0, 2), (3, 0), (0, 4), (0, 0)],
            1,
        ),
    ]
    for index, n in enumerate((17, 31, 80, 160, 320), start=1):
        children, root = _random_binary_tree(rng, n)
        children, root = _remap_binary_tree(rng, children, root)
        cases.append(_balanced_tree_case(f"随机编号二叉树 {index}", children, root))

    complete_n = 16_383
    complete = [(0, 0)] + [
        (2 * node if 2 * node <= complete_n else 0, 2 * node + 1 if 2 * node + 1 <= complete_n else 0)
        for node in range(1, complete_n + 1)
    ]
    cases.append(_balanced_tree_case("完全树压力测试", complete, 1))

    chain_n = 15_000
    chain = [(0, 0)] + [
        (0, node + 1 if node < chain_n else 0) for node in range(1, chain_n + 1)
    ]
    cases.append(_balanced_tree_case("深链压力测试", chain, 1))
    return cases


def _rearrange_position_parity(values: list[int]) -> list[int]:
    result = values[:]
    odd_position = 0
    even_position = 1
    while True:
        while odd_position < len(result) and result[odd_position] % 2 != 0:
            odd_position += 2
        while even_position < len(result) and result[even_position] % 2 == 0:
            even_position += 2
        if odd_position >= len(result) or even_position >= len(result):
            return result
        result[odd_position], result[even_position] = result[even_position], result[odd_position]


def _position_parity_case(name: str, values: list[int]) -> GeneratedCase:
    output = _rearrange_position_parity(values)
    return _case(name, f"{len(values)}\n{_line(values)}", _line(output))


def _position_parity_cases(rng: random.Random) -> list[GeneratedCase]:
    cases = [
        _position_parity_case("原地交换一对", [2, 1, 3, 4, 5, 6]),
        _position_parity_case("两个元素已就位", [1, 2]),
        _position_parity_case("两个元素错位", [8, -3]),
        _position_parity_case("全部位置错位", [2, 1, 4, 3, 6, 5, 8, 7]),
        _position_parity_case("含负数和零", [0, -3, -5, 8, 12, -7, 9, 2]),
        _position_parity_case("含重复值", [2, 2, 1, 1, 3, 4, 5, 6]),
    ]
    for index in range(6):
        n = rng.randrange(4, 202, 2)
        odds = [2 * rng.randint(-5000, 5000) + 1 for _ in range(n // 2)]
        evens = [2 * rng.randint(-5000, 5000) for _ in range(n // 2)]
        values = odds + evens
        rng.shuffle(values)
        cases.append(_position_parity_case(f"随机奇偶序列 {index + 1}", values))

    n = 100_000
    values = [2 * index + 2 for index in range(n // 2)] + [
        2 * index + 1 for index in range(n // 2)
    ]
    cases.append(_position_parity_case("十万元素压力测试", values))
    return cases


def _rotated_minimum_case(name: str, values: list[int]) -> GeneratedCase:
    return _case(name, f"{len(values)}\n{_line(values)}", str(min(values)))


def _rotated_minimum_cases(rng: random.Random) -> list[GeneratedCase]:
    cases = [
        _rotated_minimum_case("原题示例", [3, 4, 5, 1, 2]),
        _rotated_minimum_case("单元素", [-7]),
        _rotated_minimum_case("没有旋转", [-5, -1, 0, 9, 20]),
        _rotated_minimum_case("旋转一位", [2, 3, 4, 5, 1]),
        _rotated_minimum_case("全部相等", [8] * 12),
        _rotated_minimum_case("最小值附近有重复", [2, 2, 2, 0, 0, 1, 2]),
        _rotated_minimum_case("负数与重复值", [-1, 0, 4, -8, -8, -3]),
    ]
    for index in range(6):
        n = rng.randint(5, 300)
        current = rng.randint(-10_000, 10_000)
        ordered = []
        for _ in range(n):
            current += rng.randint(0, 9)
            ordered.append(current)
        pivot = rng.randrange(n)
        values = ordered[pivot:] + ordered[:pivot]
        cases.append(_rotated_minimum_case(f"随机旋转数组 {index + 1}", values))

    n = 200_000
    ordered = list(range(-100_000, 100_000))
    pivot = 137_531
    cases.append(_rotated_minimum_case("严格递增压力测试", ordered[pivot:] + ordered[:pivot]))
    repeated = [0] + [7] * (n - 1)
    pivot = n // 2
    cases.append(_rotated_minimum_case("重复值压力测试", repeated[pivot:] + repeated[:pivot]))
    return cases


def _mirror_similar(
    first: list[tuple[int, int]], first_root: int,
    second: list[tuple[int, int]], second_root: int,
) -> bool:
    stack = [(first_root, second_root)]
    while stack:
        left_tree, right_tree = stack.pop()
        if left_tree == 0 or right_tree == 0:
            if left_tree != right_tree:
                return False
            continue
        first_left, first_right = first[left_tree]
        second_left, second_right = second[right_tree]
        stack.append((first_left, second_right))
        stack.append((first_right, second_left))
    return True


def _mirror_tree(children: list[tuple[int, int]]) -> list[tuple[int, int]]:
    return [(right, left) for left, right in children]


def _two_tree_input(
    first: list[tuple[int, int]], first_root: int,
    second: list[tuple[int, int]], second_root: int,
) -> str:
    return f"{_binary_tree_input(first, first_root)}\n{_binary_tree_input(second, second_root)}"


def _mirror_case(
    name: str,
    first: list[tuple[int, int]], first_root: int,
    second: list[tuple[int, int]], second_root: int,
) -> GeneratedCase:
    answer = int(_mirror_similar(first, first_root, second, second_root))
    return _case(name, _two_tree_input(first, first_root, second, second_root), str(answer))


def _mirror_cases(rng: random.Random) -> list[GeneratedCase]:
    asymmetric = [(0, 0), (2, 3), (4, 0), (5, 6), (0, 0), (0, 7), (0, 0), (0, 0)]
    mirrored = _mirror_tree(asymmetric)
    mirrored, mirrored_root = _remap_binary_tree(rng, mirrored, 1)
    cases = [
        _mirror_case("非对称树的镜像", asymmetric, 1, mirrored, mirrored_root),
        _mirror_case("两棵空树", [(0, 0)], 0, [(0, 0)], 0),
        _mirror_case("单结点", [(0, 0), (0, 0)], 1, [(0, 0), (0, 0)], 1),
        _mirror_case("一空一非空", [(0, 0)], 0, [(0, 0), (0, 0)], 1),
        _mirror_case("同向单链不构成镜像", [(0, 0), (2, 0), (0, 0)], 1, [(0, 0), (2, 0), (0, 0)], 1),
        _mirror_case("结点数不同", [(0, 0), (2, 0), (0, 0)], 1, [(0, 0), (0, 0)], 1),
        _mirror_case("满二叉树自镜像", [(0, 0), (2, 3), (0, 0), (0, 0)], 1, [(0, 0), (2, 3), (0, 0), (0, 0)], 1),
    ]
    for index, n in enumerate((12, 25, 60, 120, 250, 500), start=1):
        first, first_root = _random_binary_tree(rng, n)
        if index % 2:
            second = _mirror_tree(first)
            second, second_root = _remap_binary_tree(rng, second, first_root)
        else:
            while True:
                second, second_root = _random_binary_tree(rng, n)
                second, second_root = _remap_binary_tree(rng, second, second_root)
                if not _mirror_similar(first, first_root, second, second_root):
                    break
        cases.append(_mirror_case(f"随机树对 {index}", first, first_root, second, second_root))

    complete_n = 8_191
    complete = [(0, 0)] + [
        (2 * node if 2 * node <= complete_n else 0, 2 * node + 1 if 2 * node + 1 <= complete_n else 0)
        for node in range(1, complete_n + 1)
    ]
    cases.append(_mirror_case("完全树压力测试", complete, 1, _mirror_tree(complete), 1))

    chain_n = 10_000
    left_chain = [(0, 0)] + [
        (node + 1 if node < chain_n else 0, 0) for node in range(1, chain_n + 1)
    ]
    right_chain = _mirror_tree(left_chain)
    cases.append(_mirror_case("深链压力测试", left_chain, 1, right_chain, 1))
    return cases


def _stable_index_case(name: str, values: list[int]) -> GeneratedCase:
    output = values[::2] + values[1::2]
    return _case(name, f"{len(values)}\n{_line(values)}", _line(output))


def _stable_index_cases(rng: random.Random) -> list[GeneratedCase]:
    cases = [
        _stable_index_case("普通偶数长度", [10, 20, 30, 40, 50, 60]),
        _stable_index_case("单元素", [42]),
        _stable_index_case("两个元素", [-1, 9]),
        _stable_index_case("普通奇数长度", [1, 2, 3, 4, 5, 6, 7]),
        _stable_index_case("含重复值", [5, 5, 5, 2, 2, 8, 5]),
        _stable_index_case("含极值", [-(10**9), 10**9, 0, -1, 1]),
    ]
    for index in range(6):
        n = rng.randint(3, 300)
        values = [rng.randint(-(10**6), 10**6) for _ in range(n)]
        cases.append(_stable_index_case(f"随机顺序表 {index + 1}", values))
    values = [((index * 1_000_003) % 2_000_001) - 1_000_000 for index in range(200_000)]
    cases.append(_stable_index_case("二十万元素压力测试", values))
    return cases


def _indegree_case(
    name: str, n: int, target: int, edges: list[tuple[int, int]]
) -> GeneratedCase:
    rows = "\n".join(f"{start} {end}" for start, end in edges)
    input_data = f"{n} {len(edges)} {target}" + (f"\n{rows}" if rows else "")
    answer = sum(end == target for _, end in edges)
    return _case(name, input_data, str(answer))


def _random_edges(
    rng: random.Random, n: int, count: int, *, allow_loops: bool = True
) -> list[tuple[int, int]]:
    edges: set[tuple[int, int]] = set()
    while len(edges) < count:
        edge = (rng.randint(1, n), rng.randint(1, n))
        if allow_loops or edge[0] != edge[1]:
            edges.add(edge)
    return sorted(edges)


def _indegree_cases(rng: random.Random) -> list[GeneratedCase]:
    cases = [
        _indegree_case("多条边进入目标", 5, 3, [(1, 3), (2, 3), (3, 4), (5, 3)]),
        _indegree_case("单顶点无边", 1, 1, []),
        _indegree_case("目标是孤立点", 6, 6, [(1, 2), (2, 3), (3, 1)]),
        _indegree_case("仅有自环", 3, 2, [(2, 2)]),
        _indegree_case("只有出边", 5, 1, [(1, 2), (1, 3), (1, 4), (1, 5)]),
        _indegree_case("有向环", 4, 1, [(1, 2), (2, 3), (3, 4), (4, 1)]),
        _indegree_case("完全有向图", 5, 4, [(i, j) for i in range(1, 6) for j in range(1, 6)]),
    ]
    for index, n in enumerate((20, 40, 80, 120, 200, 300), start=1):
        edges = _random_edges(rng, n, n * 4)
        cases.append(_indegree_case(f"随机有向图 {index}", n, rng.randint(1, n), edges))

    n = 20_000
    edges = _random_edges(rng, n, 100_000)
    cases.append(_indegree_case("十万条边压力测试", n, 13_579, edges))
    return cases


def _child_sibling_arrays(children: list[list[int]]) -> tuple[list[int], list[int]]:
    first_child = [0] * len(children)
    next_sibling = [0] * len(children)
    for parent in range(1, len(children)):
        if children[parent]:
            first_child[parent] = children[parent][0]
        for left, right in zip(children[parent], children[parent][1:]):
            next_sibling[left] = right
    return first_child, next_sibling


def _tree_degree_from_child_sibling(first_child: list[int], next_sibling: list[int]) -> int:
    degree = 0
    for node in range(1, len(first_child)):
        count = 0
        child = first_child[node]
        while child:
            count += 1
            child = next_sibling[child]
        degree = max(degree, count)
    return degree


def _tree_degree_case(name: str, children: list[list[int]], root: int = 1) -> GeneratedCase:
    first_child, next_sibling = _child_sibling_arrays(children)
    rows = "\n".join(
        f"{first_child[node]} {next_sibling[node]}" for node in range(1, len(children))
    )
    answer = _tree_degree_from_child_sibling(first_child, next_sibling)
    return _case(name, f"{len(children) - 1} {root}\n{rows}", str(answer))


def _remap_rooted_children(
    rng: random.Random, children: list[list[int]], root: int = 1
) -> tuple[list[list[int]], int]:
    n = len(children) - 1
    shuffled = list(range(1, n + 1))
    rng.shuffle(shuffled)
    mapping = [0] + shuffled
    remapped = [[] for _ in range(n + 1)]
    for parent in range(1, n + 1):
        remapped[mapping[parent]] = [mapping[child] for child in children[parent]]
    return remapped, mapping[root]


def _tree_degree_cases(rng: random.Random) -> list[GeneratedCase]:
    cases = [
        _tree_degree_case("根结点有三个孩子", [[], [2, 3, 4], [], [], []]),
        _tree_degree_case("单结点树", [[], []]),
        _tree_degree_case("单链树", [[], [2], [3], [4], []]),
        _tree_degree_case("最大度在内部结点", [[], [2, 3], [4, 5, 6, 7], [], [], [], [], []]),
        _tree_degree_case("多层兄弟链", [[], [2, 3, 4], [5, 6], [7], [], [], [], []]),
        _tree_degree_case("二叉树对应结构", [[], [2, 3], [4, 5], [6, 7], [], [], [], []]),
    ]
    for index, n in enumerate((15, 30, 60, 120, 240, 500), start=1):
        children = [[] for _ in range(n + 1)]
        for node in range(2, n + 1):
            children[rng.randint(1, node - 1)].append(node)
        children, root = _remap_rooted_children(rng, children)
        cases.append(_tree_degree_case(f"随机编号树 {index}", children, root))

    star_n = 30_000
    star = [[] for _ in range(star_n + 1)]
    star[1] = list(range(2, star_n + 1))
    cases.append(_tree_degree_case("三万结点星形树", star))

    chain_n = 30_000
    chain = [[] for _ in range(chain_n + 1)]
    for node in range(1, chain_n):
        chain[node].append(node + 1)
    cases.append(_tree_degree_case("三万结点单链树", chain))
    return cases


def _linked_list_input(
    rng: random.Random, values: list[str], *, shuffle_ids: bool = True
) -> str:
    n = len(values)
    logical_ids = list(range(1, n + 1))
    if shuffle_ids:
        rng.shuffle(logical_ids)
    rows: list[tuple[str, int]] = [("", 0) for _ in range(n + 1)]
    for index, value in enumerate(values):
        node = logical_ids[index]
        next_node = logical_ids[index + 1] if index + 1 < n else 0
        rows[node] = (value, next_node)
    body = "\n".join(f"{value} {next_node}" for value, next_node in rows[1:])
    return f"{n} {logical_ids[0]}\n{body}"


def _linked_palindrome_case(
    rng: random.Random, name: str, values: list[str], *, shuffle_ids: bool = True
) -> GeneratedCase:
    answer = int(values == list(reversed(values)))
    return _case(name, _linked_list_input(rng, values, shuffle_ids=shuffle_ids), str(answer))


def _linked_palindrome_cases(rng: random.Random) -> list[GeneratedCase]:
    cases = [
        _linked_palindrome_case(rng, "奇数长度回文", list("xyx")),
        _linked_palindrome_case(rng, "两个相同字符", list("aa")),
        _linked_palindrome_case(rng, "两个不同字符", list("ab")),
        _linked_palindrome_case(rng, "偶数长度回文", list("xxyyxx")),
        _linked_palindrome_case(rng, "首尾相同但不是回文", list("abca")),
        _linked_palindrome_case(rng, "全部相同", list("zzzzzzzzzz")),
        _linked_palindrome_case(rng, "数字字符回文", list("1234554321")),
        _linked_palindrome_case(rng, "仅中间不匹配", list("abcxefcba")),
    ]
    alphabet = "abcdef012345"
    for index in range(6):
        half_size = rng.randint(3, 100)
        half = [rng.choice(alphabet) for _ in range(half_size)]
        if index % 2 == 0:
            middle = [rng.choice(alphabet)] if index % 4 == 0 else []
            values = half + middle + list(reversed(half))
        else:
            values = half + list(reversed(half))
            replacement = rng.choice([char for char in alphabet if char != values[-1]])
            values[-1] = replacement
        cases.append(_linked_palindrome_case(rng, f"随机链表 {index + 1}", values))

    half = [chr(ord("a") + index % 5) for index in range(40_000)]
    cases.append(
        _linked_palindrome_case(
            rng,
            "八万结点回文压力测试",
            half + list(reversed(half)),
            shuffle_ids=False,
        )
    )
    values = half + ["q"] + list(reversed(half))
    values[-2] = "z" if values[-2] != "z" else "y"
    cases.append(
        _linked_palindrome_case(
            rng,
            "八万结点非回文压力测试",
            values,
            shuffle_ids=False,
        )
    )
    return cases


def _definitions() -> list[MockProblemDefinition]:
    return [
        MockProblemDefinition(
            key=MOCK_ALGORITHM_KEYS[0],
            volume=1,
            question="42",
            title="二叉树高度与平衡判定",
            body=r"""给定一棵采用二叉链式结构表示的二叉树，求树的高度，并判断它是否平衡。

若任意结点的左、右子树高度差的绝对值都不超过 $1$，则该树平衡。空树的高度为 $0$，非空树的高度按结点层数计算。""",
            input_format=r"""第一行包含 $n,root$，分别表示结点数和根结点编号。结点编号为 $1$ 到 $n$，编号 $0$ 表示空指针。

随后 $n$ 行中的第 $i$ 行包含 `left right`，表示结点 $i$ 的左右孩子。空树输入为 `0 0`，且没有后续结点行。""",
            output_format="输出 `height balanced`。`balanced` 为 `1` 表示平衡，为 `0` 表示不平衡。",
            constraints=r"""- $0 \le n \le 20000$
- 输入保证所有非零编号恰好构成一棵合法二叉树""",
            tags=("王道模拟题", "2026王道八套卷", "数据结构", "树", "平衡二叉树", "后序遍历"),
            build_cases=_balanced_tree_cases,
        ),
        MockProblemDefinition(
            key=MOCK_ALGORITHM_KEYS[1],
            volume=2,
            question="42",
            title="按位置奇偶性重排整数",
            body=r"""给定一个含有相同数量奇数和偶数的整数顺序表。重新排列元素，使奇数位于奇数位置，偶数位于偶数位置。位置从 $1$ 开始编号。

为使输出唯一，按以下原地过程重排：分别从左到右扫描奇数位置和偶数位置，每次交换最靠左的“奇数位置上的偶数”和最靠左的“偶数位置上的奇数”，直到全部就位。""",
            input_format="第一行包含偶数 $n$。第二行包含 $n$ 个整数，其中恰有 $n/2$ 个奇数和 $n/2$ 个偶数。",
            output_format="输出按规定过程重排后的 $n$ 个整数。",
            constraints=r"""- $2 \le n \le 100000$，且 $n$ 为偶数
- 元素在 32 位有符号整数范围内""",
            tags=("王道模拟题", "2026王道八套卷", "数据结构", "顺序表", "双指针", "原地交换"),
            build_cases=_position_parity_cases,
            adaptation="原题允许任意满足奇偶位置要求的排列；为支持自动判定，这里规定从左到右成对交换最早错位元素。",
        ),
        MockProblemDefinition(
            key=MOCK_ALGORITHM_KEYS[2],
            volume=3,
            question="42",
            title="旋转有序数组的最小值",
            body=r"""将一个非降序数组开头的若干元素搬到末尾，称为数组的一次旋转。给定一个非降序数组的旋转，求其中的最小元素。

数组中允许有重复值，也允许没有发生旋转。""",
            input_format="第一行包含 $n$。第二行包含旋转后的 $n$ 个整数。",
            output_format="输出数组中的最小元素。",
            constraints=r"""- $1 \le n \le 200000$
- 元素在 32 位有符号整数范围内
- 输入保证可以由某个非降序数组旋转得到""",
            tags=("王道模拟题", "2026王道八套卷", "数据结构", "顺序表", "二分查找"),
            build_cases=_rotated_minimum_cases,
        ),
        MockProblemDefinition(
            key=MOCK_ALGORITHM_KEYS[3],
            volume=4,
            question="42",
            title="二叉树镜像相似判定",
            body=r"""若两棵二叉树在树形上左右对称同构，即一棵树的结构等于另一棵树左右翻转后的结构，则称它们镜像相似。结点的数据值不参与判断。

给定两棵二叉树，判断它们是否镜像相似。""",
            input_format=r"""依次输入两棵树。每棵树的第一行包含 $n,root$；随后 $n$ 行中的第 $i$ 行包含结点 $i$ 的 `left right`。结点编号为 $1$ 到 $n$，编号 $0$ 表示空指针。空树只输入 `0 0`。""",
            output_format="镜像相似时输出 `1`，否则输出 `0`。",
            constraints=r"""- 两棵树的结点总数不超过 $20000$
- 输入保证每组非零编号恰好构成一棵合法二叉树""",
            tags=("王道模拟题", "2026王道八套卷", "数据结构", "树", "递归", "结构匹配"),
            build_cases=_mirror_cases,
        ),
        MockProblemDefinition(
            key=MOCK_ALGORITHM_KEYS[4],
            volume=5,
            question="42",
            title="奇数号元素稳定前移",
            body=r"""线性表 $(a_1,a_2,\ldots,a_n)$ 存放在一维数组中。将所有奇数号元素移到所有偶数号元素前面，同时保持奇数号元素之间、偶数号元素之间原有的相对顺序。

也就是说，输出顺序为 $a_1,a_3,a_5,\ldots,a_2,a_4,a_6,\ldots$。""",
            input_format="第一行包含 $n$。第二行包含 $n$ 个整数。",
            output_format="输出稳定重排后的 $n$ 个整数。",
            constraints=r"""- $1 \le n \le 200000$
- 元素在 32 位有符号整数范围内""",
            tags=("王道模拟题", "2026王道八套卷", "数据结构", "顺序表", "稳定重排", "分治"),
            build_cases=_stable_index_cases,
        ),
        MockProblemDefinition(
            key=MOCK_ALGORITHM_KEYS[5],
            volume=6,
            question="42",
            title="邻接表中顶点的入度",
            body="给定一个无权有向图和顶点 $v$，求 $v$ 的入度。自环对该顶点的入度贡献为 $1$。",
            input_format="第一行包含 $n,m,v$。随后 $m$ 行每行包含一条有向边 `from to`。",
            output_format="输出顶点 $v$ 的入度。",
            constraints=r"""- $1 \le n \le 20000$
- $0 \le m \le 150000$
- 顶点编号为 $1$ 到 $n$
- 输入不含重边，但允许自环""",
            tags=("王道模拟题", "2026王道八套卷", "数据结构", "图", "邻接表", "度"),
            build_cases=_indegree_cases,
            time_limit_ms=1500,
            adaptation="原题要求先定义邻接表再编写求入度函数；这里使用边表作为标准输入，由程序自行建立所需结构。",
        ),
        MockProblemDefinition(
            key=MOCK_ALGORITHM_KEYS[6],
            volume=7,
            question="42",
            title="孩子兄弟树的度",
            body=r"""树采用孩子兄弟链表表示。每个结点包含第一个孩子指针和下一个兄弟指针。

树的度是所有结点的孩子数量的最大值。给定一棵孩子兄弟树，求它的度。""",
            input_format=r"""第一行包含 $n,root$。随后 $n$ 行中的第 $i$ 行包含 `first_child next_sibling`，表示结点 $i$ 的第一个孩子和下一个兄弟；编号 $0$ 表示空指针。""",
            output_format="输出树的度。",
            constraints=r"""- $1 \le n \le 30000$
- 结点编号为 $1$ 到 $n$
- 输入保证全部结点恰好构成一棵合法的孩子兄弟树""",
            tags=("王道模拟题", "2026王道八套卷", "数据结构", "树", "孩子兄弟表示法", "遍历"),
            build_cases=_tree_degree_cases,
        ),
        MockProblemDefinition(
            key=MOCK_ALGORITHM_KEYS[7],
            volume=8,
            question="42",
            title="单链表中心对称判定",
            body=r"""给定一个长度大于 $1$ 的单链表，每个结点的数据域保存一个非空白字符。判断从表头到表尾得到的字符序列是否中心对称，即是否为回文序列。

结点在输入中的编号顺序不一定等于链表中的逻辑顺序。""",
            input_format=r"""第一行包含 $n,head$。随后 $n$ 行中的第 $i$ 行包含 `data next`，表示编号为 $i$ 的结点；`data` 是一个 ASCII 字母或数字，`next=0` 表示链表结束。""",
            output_format="中心对称时输出 `1`，否则输出 `0`。",
            constraints=r"""- $2 \le n \le 100000$
- 输入保证从 `head` 出发恰好经过全部 $n$ 个结点一次""",
            tags=("王道模拟题", "2026王道八套卷", "数据结构", "链表", "快慢指针", "链表反转"),
            build_cases=_linked_palindrome_cases,
        ),
    ]


def build_wangdao_mock_bank() -> tuple[QuestionBankProblem, ...]:
    definitions = _definitions()
    by_key = {definition.key: definition for definition in definitions}
    if len(by_key) != len(definitions):
        raise ValueError("duplicate Wangdao mock question key")
    if set(by_key) != set(MOCK_ALGORITHM_KEYS):
        missing = sorted(set(MOCK_ALGORITHM_KEYS) - set(by_key))
        extra = sorted(set(by_key) - set(MOCK_ALGORITHM_KEYS))
        raise ValueError(f"Wangdao mock question catalog mismatch: missing={missing}, extra={extra}")

    problems: list[QuestionBankProblem] = []
    for key in MOCK_ALGORITHM_KEYS:
        definition = by_key[key]
        rng = random.Random(f"local-408-oj:{definition.key}:v{MOCK_BANK_VERSION}")
        cases = tuple(definition.build_cases(rng))
        if not cases:
            raise ValueError(f"Wangdao mock question has no cases: {definition.key}")
        if len({case.name for case in cases}) != len(cases):
            raise ValueError(f"Wangdao mock question has duplicate case names: {definition.key}")
        volume = VOLUME_NAMES[definition.volume]
        problems.append(
            QuestionBankProblem(
                key=definition.key,
                year=2026,
                title=f"王道模拟-{volume} {definition.title}",
                description=_statement(definition, cases[0]),
                tags=definition.tags,
                time_limit_ms=definition.time_limit_ms,
                memory_limit_mb=definition.memory_limit_mb,
                cases=cases,
            )
        )
    return tuple(problems)
