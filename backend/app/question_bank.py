from __future__ import annotations

import heapq
import random
from dataclasses import dataclass
from typing import Callable


BANK_VERSION = 2
SOURCE_PREFIX = "408-oj-source:"

# Only questions whose original prompt explicitly asks for an algorithm are imported.
ALGORITHM_KEYS = (
    "408-2009-q42-kth-from-end",
    "408-2010-q42-left-rotate",
    "408-2011-q42-lower-median",
    "408-2012-q42-shared-suffix-node",
    "408-2013-q41-majority-element",
    "408-2014-q41-binary-tree-wpl",
    "408-2015-q41-abs-deduplicate-list",
    "408-2016-q43-balanced-partition",
    "408-2017-q41-expression-tree-infix",
    "408-2018-q41-smallest-missing-positive",
    "408-2019-q41-reorder-linked-list",
    "408-2020-q41-min-triple-distance",
    "408-2021-q41-euler-trail-exists",
    "408-2022-q41-array-bst-validation",
    "408-2023-q41-k-vertices",
    "408-2024-q41-unique-topological-order",
    "408-2025-q41-suffix-max-product",
)


@dataclass(frozen=True)
class GeneratedCase:
    name: str
    input_data: str
    output_data: str


@dataclass(frozen=True)
class ProblemDefinition:
    key: str
    year: int
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


@dataclass(frozen=True)
class QuestionBankProblem:
    key: str
    year: int
    title: str
    description: str
    tags: tuple[str, ...]
    time_limit_ms: int
    memory_limit_mb: int
    cases: tuple[GeneratedCase, ...]


def _case(name: str, input_data: str, output_data: str) -> GeneratedCase:
    return GeneratedCase(
        name=name,
        input_data=input_data.rstrip() + "\n",
        output_data=output_data.rstrip() + "\n",
    )


def _line(values: list[int]) -> str:
    return " ".join(map(str, values))


def _seq_input(header: str, values: list[int]) -> str:
    return f"{header}\n{_line(values)}"


def _kth_cases(rng: random.Random) -> list[GeneratedCase]:
    data = [
        ("普通链表", [10, 20, 30, 40, 50], 2),
        ("仅一个结点", [7], 1),
        ("查找首结点", [-3, 8, 8, 21], 4),
        ("k 超出长度", [1, 2, 3], 4),
        ("空链表", [], 1),
    ]
    for index in range(5):
        n = rng.randint(2, 80)
        values = [rng.randint(-1000, 1000) for _ in range(n)]
        data.append((f"随机链表 {index + 1}", values, rng.randint(1, n + 2)))
    stress = [rng.randint(-(10**9), 10**9) for _ in range(50_000)]
    data.append(("五万结点压力测试", stress, 37_421))
    cases = []
    for name, values, k in data:
        answer = f"1 {values[-k]}" if k <= len(values) else "0"
        cases.append(_case(name, _seq_input(f"{len(values)} {k}", values), answer))
    return cases


def _rotate_cases(rng: random.Random) -> list[GeneratedCase]:
    data = [
        ("普通序列", [1, 2, 3, 4, 5, 6, 7], 3),
        ("两个元素", [8, 9], 1),
        ("左移 n-1 位", [4, -2, 7, 7, 0], 4),
        ("全部相等", [5] * 12, 7),
    ]
    for index in range(6):
        n = rng.randint(3, 120)
        data.append(
            (f"随机序列 {index + 1}", [rng.randint(-5000, 5000) for _ in range(n)], rng.randint(1, n - 1))
        )
    stress = [rng.randint(-(10**9), 10**9) for _ in range(50_000)]
    data.append(("五万元素压力测试", stress, 23_457))
    return [
        _case(name, _seq_input(f"{len(values)} {p}", values), _line(values[p:] + values[:p]))
        for name, values, p in data
    ]


def _median_cases(rng: random.Random) -> list[GeneratedCase]:
    data = [
        ("原题示例", [11, 13, 15, 17, 19], [2, 4, 6, 8, 20]),
        ("单元素", [-5], [10]),
        ("完全分离", [1, 2, 3, 4], [100, 101, 102, 103]),
        ("大量重复", [1, 1, 2, 2, 2], [2, 2, 2, 3, 3]),
    ]
    for index in range(6):
        n = rng.randint(2, 100)
        a = sorted(rng.randint(-1000, 1000) for _ in range(n))
        b = sorted(rng.randint(-1000, 1000) for _ in range(n))
        data.append((f"随机升序列 {index + 1}", a, b))
    data.append(
        (
            "五万元素升序列",
            list(range(-100_000, 0, 2)),
            list(range(-99_999, 1, 2)),
        )
    )
    cases = []
    for name, a, b in data:
        merged = sorted(a + b)
        cases.append(_case(name, f"{len(a)}\n{_line(a)}\n{_line(b)}", str(merged[len(a) - 1])))
    return cases


def _optimal_merge_cost(lengths: list[int]) -> int:
    queue = lengths[:]
    heapq.heapify(queue)
    total = 0
    while len(queue) > 1:
        left = heapq.heappop(queue)
        right = heapq.heappop(queue)
        total += left + right - 1
        heapq.heappush(queue, left + right)
    return total


def _optimal_merge_cases(rng: random.Random) -> list[GeneratedCase]:
    data = [
        ("原题表长", [10, 35, 40, 50, 60, 200]),
        ("仅两个表", [1, 1]),
        ("长度相同", [8] * 8),
        ("长度悬殊", [1, 2, 3, 4, 1_000_000]),
        ("六个大表", [10**9, 10**9 - 1, 10**9 - 2, 17, 23, 42]),
    ]
    for index in range(5):
        n = rng.randint(3, 30)
        data.append((f"随机表长 {index + 1}", [rng.randint(1, 100_000) for _ in range(n)]))
    return [
        _case(name, _seq_input(str(len(lengths)), lengths), str(_optimal_merge_cost(lengths)))
        for name, lengths in data
    ]


def _shared_list_case(
    rng: random.Random,
    name: str,
    prefix_a: list[int],
    prefix_b: list[int],
    shared: list[int],
) -> GeneratedCase:
    total = len(prefix_a) + len(prefix_b) + len(shared)
    if total == 0:
        return _case(name, "0 0 0", "-1")

    a_nodes = list(range(len(prefix_a)))
    b_start = len(prefix_a)
    b_nodes = list(range(b_start, b_start + len(prefix_b)))
    shared_start = b_start + len(prefix_b)
    shared_nodes = list(range(shared_start, total))
    values = prefix_a + prefix_b + shared
    logical_next = [-1] * total
    chain_a = a_nodes + shared_nodes
    chain_b = b_nodes + shared_nodes
    for chain in (chain_a, chain_b):
        for left, right in zip(chain, chain[1:]):
            logical_next[left] = right

    ids = list(range(1, total + 1))
    rng.shuffle(ids)
    rows: list[tuple[int, int]] = [(0, 0)] * total
    for logical in range(total):
        node_id = ids[logical]
        next_id = ids[logical_next[logical]] if logical_next[logical] >= 0 else 0
        rows[node_id - 1] = (values[logical], next_id)
    head_a = ids[chain_a[0]] if chain_a else 0
    head_b = ids[chain_b[0]] if chain_b else 0
    answer = str(ids[shared_nodes[0]]) if shared_nodes else "-1"
    body = "\n".join(f"{value} {next_id}" for value, next_id in rows)
    return _case(name, f"{total} {head_a} {head_b}\n{body}", answer)


def _shared_suffix_cases(rng: random.Random) -> list[GeneratedCase]:
    cases = [
        _shared_list_case(rng, "共享 ing 后缀", [108, 111, 97, 100], [98, 101], [105, 110, 103]),
        _shared_list_case(rng, "两个头指针相同", [], [], [3, 5, 8]),
        _shared_list_case(rng, "仅共享尾结点", [1, 2, 3], [4, 5], [9]),
        _shared_list_case(rng, "没有公共结点", [1, 2, 3], [2, 3], []),
        _shared_list_case(rng, "两个空链表", [], [], []),
    ]
    for index in range(5):
        a_len = rng.randint(0, 20)
        b_len = rng.randint(0, 20)
        shared_len = rng.randint(0, 15)
        if a_len + shared_len == 0 and b_len + shared_len == 0:
            a_len = 1
        cases.append(
            _shared_list_case(
                rng,
                f"随机结点编号 {index + 1}",
                [rng.randint(-99, 99) for _ in range(a_len)],
                [rng.randint(-99, 99) for _ in range(b_len)],
                [rng.randint(-99, 99) for _ in range(shared_len)],
            )
        )
    cases.append(
        _shared_list_case(
            rng,
            "三万结点压力测试",
            list(range(10_000)),
            list(range(10_000, 20_000)),
            list(range(20_000, 30_000)),
        )
    )
    return cases


def _majority_answer(values: list[int]) -> int:
    candidate = -1
    count = 0
    for value in values:
        if count == 0:
            candidate = value
            count = 1
        elif value == candidate:
            count += 1
        else:
            count -= 1
    return candidate if values.count(candidate) > len(values) // 2 else -1


def _majority_cases(rng: random.Random) -> list[GeneratedCase]:
    data = [
        ("存在主元素", [0, 5, 5, 3, 5, 7, 5, 5]),
        ("没有主元素", [0, 5, 5, 3, 5, 1, 5, 7]),
        ("单元素", [0]),
        ("恰好一半", [1, 1, 2, 2]),
    ]
    for index in range(6):
        n = rng.randint(3, 101)
        if index % 2 == 0:
            candidate = rng.randrange(n)
            count = n // 2 + 1
            values = [candidate] * count + [rng.randrange(n) for _ in range(n - count)]
            rng.shuffle(values)
        else:
            values = [rng.randrange(n) for _ in range(n)]
        data.append((f"随机序列 {index + 1}", values))
    stress = [17] * 50_001 + [value % 100_000 for value in range(49_999)]
    rng.shuffle(stress)
    data.append(("十万元素主元素", stress))
    return [
        _case(name, _seq_input(str(len(values)), values), str(_majority_answer(values)))
        for name, values in data
    ]


def _wpl(nodes: list[tuple[int, int, int]], root: int) -> int:
    def visit(node_id: int, depth: int) -> int:
        if node_id == 0:
            return 0
        weight, left, right = nodes[node_id - 1]
        if left == 0 and right == 0:
            return weight * depth
        return visit(left, depth + 1) + visit(right, depth + 1)

    return visit(root, 0)


def _tree_nodes(rng: random.Random, n: int) -> list[tuple[int, int, int]]:
    children = [[0, 0] for _ in range(n)]
    open_slots = [(0, 0), (0, 1)]
    for child in range(1, n):
        slot_index = rng.randrange(len(open_slots))
        parent, side = open_slots.pop(slot_index)
        children[parent][side] = child + 1
        open_slots.extend([(child, 0), (child, 1)])
    nodes = []
    for left, right in children:
        weight = rng.randint(0, 10_000) if left == 0 and right == 0 else 0
        nodes.append((weight, left, right))
    return nodes


def _renumber_tree(
    rng: random.Random, nodes: list[tuple[int, int, int]], root: int
) -> tuple[list[tuple[int, int, int]], int]:
    if len(nodes) <= 1:
        return nodes, root
    new_ids = list(range(1, len(nodes) + 1))
    rng.shuffle(new_ids)
    if new_ids[root - 1] == 1:
        swap_index = new_ids.index(2)
        new_ids[root - 1], new_ids[swap_index] = new_ids[swap_index], new_ids[root - 1]
    renumbered = [(0, 0, 0)] * len(nodes)
    for old_id, (weight, left, right) in enumerate(nodes, start=1):
        new_id = new_ids[old_id - 1]
        renumbered[new_id - 1] = (
            weight,
            new_ids[left - 1] if left else 0,
            new_ids[right - 1] if right else 0,
        )
    return renumbered, new_ids[root - 1]


def _wpl_case(name: str, nodes: list[tuple[int, int, int]], root: int = 1) -> GeneratedCase:
    rows = "\n".join(f"{weight} {left} {right}" for weight, left, right in nodes)
    return _case(name, f"{len(nodes)} {root}\n{rows}", str(_wpl(nodes, root)))


def _wpl_cases(rng: random.Random) -> list[GeneratedCase]:
    cases = [
        _wpl_case("普通二叉树", [(0, 2, 3), (3, 0, 0), (0, 4, 5), (4, 0, 0), (5, 0, 0)]),
        _wpl_case("单结点", [(999, 0, 0)]),
        _wpl_case("零权叶结点", [(0, 2, 3), (0, 0, 0), (7, 0, 0)]),
        _wpl_case("右斜树", [(0, 0, 2), (0, 0, 3), (0, 0, 4), (10**9, 0, 0)]),
    ]
    for index, n in enumerate((8, 15, 40, 80, 160, 320)):
        nodes, root = _renumber_tree(rng, _tree_nodes(rng, n), 1)
        cases.append(_wpl_case(f"随机重编号二叉树 {index + 1}", nodes, root))
    complete_size = 32_767
    complete = []
    for node_id in range(1, complete_size + 1):
        left = node_id * 2 if node_id * 2 <= complete_size else 0
        right = node_id * 2 + 1 if node_id * 2 + 1 <= complete_size else 0
        complete.append((10**9 if left == 0 else 0, left, right))
    complete, root = _renumber_tree(rng, complete, 1)
    cases.append(_wpl_case("完整树压力测试与随机根编号", complete, root))
    return cases


def _deduplicate_cases(rng: random.Random) -> list[GeneratedCase]:
    data = [
        ("正负值绝对值重复", [21, -15, -15, -7, 15, 0, 7, 0]),
        ("全部唯一", [0, 1, -2, 3, -4]),
        ("全部同绝对值", [9, -9, 9, -9]),
        ("零重复", [0, 0, 1, 0, -1]),
    ]
    for index in range(6):
        count = rng.randint(10, 120)
        data.append((f"随机链表 {index + 1}", [rng.randint(-40, 40) for _ in range(count)]))
    data.append(
        (
            "十万结点压力测试",
            [(-1 if index % 3 == 0 else 1) * (index % 50_000) for index in range(100_000)],
        )
    )
    cases = []
    for name, values in data:
        seen: set[int] = set()
        kept = []
        for value in values:
            if abs(value) not in seen:
                seen.add(abs(value))
                kept.append(value)
        bound = max((abs(value) for value in values), default=1)
        cases.append(_case(name, _seq_input(f"{len(values)} {bound}", values), _line(kept)))
    return cases


def _partition_difference(values: list[int]) -> tuple[int, int]:
    ordered = sorted(values)
    small_size = len(values) // 2
    low_difference = abs(sum(ordered[:small_size]) - sum(ordered[small_size:]))
    high_difference = abs(sum(ordered[-small_size:]) - sum(ordered[:-small_size]))
    return len(values) % 2, max(low_difference, high_difference)


def _partition_cases(rng: random.Random) -> list[GeneratedCase]:
    data = [
        ("偶数个元素", [1, 2, 3, 4, 5, 6]),
        ("奇数个元素", [1, 2, 10, 11, 20]),
        ("两个元素", [7, 100]),
        ("全部相等", [9] * 9),
        ("大整数", [10**9, 1, 10**9 - 1, 2, 10**9 - 2]),
    ]
    for index in range(5):
        n = rng.randint(3, 151)
        data.append((f"随机序列 {index + 1}", [rng.randint(1, 1_000_000) for _ in range(n)]))
    data.append(("五万元素压力测试", [rng.randint(1, 10**9) for _ in range(50_000)]))
    cases = []
    for name, values in data:
        count_difference, sum_difference = _partition_difference(values)
        cases.append(
            _case(name, _seq_input(str(len(values)), values), f"{count_difference} {sum_difference}")
        )
    return cases


def _linear_probe_result(
    table_size: int, hash_modulus: int, multiplier: int, keys: list[int]
) -> tuple[list[int | None], tuple[int, int], tuple[int, int]]:
    table: list[int | None] = [None] * table_size
    successful_total = 0
    for key in keys:
        start = (key * multiplier) % hash_modulus
        for step in range(table_size):
            address = (start + step) % table_size
            if table[address] is None:
                table[address] = key
                successful_total += step + 1
                break
        else:
            raise ValueError("hash table is full")

    unsuccessful_total = 0
    for start in range(hash_modulus):
        for step in range(table_size):
            address = (start + step) % table_size
            unsuccessful_total += 1
            if table[address] is None:
                break
    return table, (successful_total, len(keys)), (unsuccessful_total, hash_modulus)


def _reduced_fraction(numerator: int, denominator: int) -> str:
    from math import gcd

    divisor = gcd(numerator, denominator)
    return f"{numerator // divisor}/{denominator // divisor}"


def _linear_probe_cases(rng: random.Random) -> list[GeneratedCase]:
    data = [
        ("原题关键字", 10, 7, 3, [7, 8, 30, 11, 18, 9, 14]),
        ("无冲突", 11, 11, 1, [0, 2, 4, 6]),
        ("集中冲突", 13, 7, 3, [0, 7, 14, 21, 28, 35]),
        ("跨表尾探测", 9, 7, 5, [4, 11, 18, 25, 32]),
    ]
    for index in range(5):
        table_size = rng.choice([17, 19, 23, 29])
        hash_modulus = rng.randint(max(2, table_size // 2), table_size)
        count = rng.randint(3, table_size - 2)
        keys = rng.sample(range(0, 10_000), count)
        data.append(
            (f"随机散列表 {index + 1}", table_size, hash_modulus, rng.randint(1, 9), keys)
        )
    cases = []
    for name, table_size, hash_modulus, multiplier, keys in data:
        table, success, failure = _linear_probe_result(table_size, hash_modulus, multiplier, keys)
        rendered = " ".join("_" if value is None else str(value) for value in table)
        answer = f"{rendered}\n{_reduced_fraction(*success)} {_reduced_fraction(*failure)}"
        cases.append(
            _case(
                name,
                _seq_input(f"{table_size} {hash_modulus} {multiplier} {len(keys)}", keys),
                answer,
            )
        )
    return cases


def _critical_path_answer(n: int, edges: list[tuple[int, int, int]]) -> tuple[int, list[int]]:
    outgoing: list[list[tuple[int, int]]] = [[] for _ in range(n + 1)]
    for start, end, weight in edges:
        outgoing[start].append((end, weight))
    distance = [-(10**30)] * (n + 1)
    distance[n] = 0
    for vertex in range(n - 1, 0, -1):
        if outgoing[vertex]:
            distance[vertex] = max(weight + distance[end] for end, weight in outgoing[vertex])
    path = [1]
    current = 1
    while current != n:
        candidates = [
            end
            for end, weight in outgoing[current]
            if distance[current] == weight + distance[end]
        ]
        current = min(candidates)
        path.append(current)
    return distance[1], path


def _dag_edges(rng: random.Random, n: int, extra: int, max_weight: int = 30) -> list[tuple[int, int, int]]:
    edges = [(vertex, vertex + 1, rng.randint(1, max_weight)) for vertex in range(1, n)]
    existing = {(start, end) for start, end, _ in edges}
    candidates = [
        (start, end)
        for start in range(1, n)
        for end in range(start + 2, n + 1)
        if (start, end) not in existing
    ]
    rng.shuffle(candidates)
    for start, end in candidates[:extra]:
        edges.append((start, end, rng.randint(1, max_weight)))
    rng.shuffle(edges)
    return edges


def _critical_path_case(name: str, n: int, edges: list[tuple[int, int, int]]) -> GeneratedCase:
    duration, path = _critical_path_answer(n, edges)
    rows = "\n".join(f"{start} {end} {weight}" for start, end, weight in edges)
    return _case(name, f"{n} {len(edges)}\n{rows}", f"{duration}\n{len(path)} {_line(path)}")


def _critical_path_cases(rng: random.Random) -> list[GeneratedCase]:
    cases = [
        _critical_path_case(
            "普通 AOE 网",
            6,
            [(1, 2, 3), (1, 3, 2), (2, 4, 4), (3, 4, 1), (3, 5, 6), (4, 6, 3), (5, 6, 2)],
        ),
        _critical_path_case("单一路径", 4, [(1, 2, 8), (2, 3, 5), (3, 4, 2)]),
        _critical_path_case("并列关键路径", 4, [(1, 2, 3), (1, 3, 3), (2, 4, 4), (3, 4, 4)]),
    ]
    for index, n in enumerate((6, 8, 10, 14, 20, 30)):
        cases.append(
            _critical_path_case(
                f"随机 AOE 网 {index + 1}", n, _dag_edges(rng, n, n * 2)
            )
        )
    return cases


def _matrix_multiply(left: list[list[int]], right: list[list[int]]) -> list[list[int]]:
    size = len(left)
    result = [[0] * size for _ in range(size)]
    for row in range(size):
        for middle in range(size):
            if left[row][middle] == 0:
                continue
            for column in range(size):
                result[row][column] += left[row][middle] * right[middle][column]
    return result


def _matrix_power(matrix: list[list[int]], exponent: int) -> list[list[int]]:
    size = len(matrix)
    result = [[int(row == column) for column in range(size)] for row in range(size)]
    base = matrix
    while exponent:
        if exponent & 1:
            result = _matrix_multiply(result, base)
        base = _matrix_multiply(base, base)
        exponent >>= 1
    return result


def _walk_case(name: str, matrix: list[list[int]], exponent: int) -> GeneratedCase:
    answer = _matrix_power(matrix, exponent)
    rows = "\n".join(_line(row) for row in matrix)
    output = "\n".join(_line(row) for row in answer)
    return _case(name, f"{len(matrix)} {exponent}\n{rows}", output)


def _walk_cases(rng: random.Random) -> list[GeneratedCase]:
    cases = [
        _walk_case("三角形中的二步通路", [[0, 1, 1], [1, 0, 1], [1, 1, 0]], 2),
        _walk_case("单条有向链", [[0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1], [0, 0, 0, 0]], 3),
        _walk_case("自环", [[1, 1], [0, 1]], 5),
    ]
    for index in range(6):
        n = rng.randint(2, 7)
        matrix = [
            [int(rng.random() < 0.32) for _ in range(n)]
            for _ in range(n)
        ]
        cases.append(_walk_case(f"随机邻接矩阵 {index + 1}", matrix, rng.randint(2, 8)))
    return cases


Expression = tuple[str, "Expression | None", "Expression | None"]


def _render_expression(node: Expression, root: bool = True) -> str:
    token, left, right = node
    if left is None and right is None:
        return token
    if left is None:
        content = token + _render_expression(right, False)  # type: ignore[arg-type]
    elif right is None:
        content = _render_expression(left, False) + token
    else:
        content = _render_expression(left, False) + token + _render_expression(right, False)
    return content if root else f"({content})"


def _serialize_expression(node: Expression) -> tuple[int, list[tuple[str, int, int]]]:
    rows: list[list[str | int]] = []

    def visit(current: Expression) -> int:
        node_id = len(rows) + 1
        rows.append([current[0], 0, 0])
        if current[1] is not None:
            rows[node_id - 1][1] = visit(current[1])
        if current[2] is not None:
            rows[node_id - 1][2] = visit(current[2])
        return node_id

    root = visit(node)
    return root, [(str(token), int(left), int(right)) for token, left, right in rows]


def _renumber_expression(
    rng: random.Random, rows: list[tuple[str, int, int]], root: int
) -> tuple[list[tuple[str, int, int]], int]:
    if len(rows) <= 1:
        return rows, root
    new_ids = list(range(1, len(rows) + 1))
    rng.shuffle(new_ids)
    if new_ids[root - 1] == 1:
        swap_index = new_ids.index(2)
        new_ids[root - 1], new_ids[swap_index] = new_ids[swap_index], new_ids[root - 1]
    renumbered = [("", 0, 0)] * len(rows)
    for old_id, (token, left, right) in enumerate(rows, start=1):
        new_id = new_ids[old_id - 1]
        renumbered[new_id - 1] = (
            token,
            new_ids[left - 1] if left else 0,
            new_ids[right - 1] if right else 0,
        )
    return renumbered, new_ids[root - 1]


def _expression_case(
    name: str, expression: Expression, renumber_rng: random.Random | None = None
) -> GeneratedCase:
    root, rows = _serialize_expression(expression)
    if renumber_rng is not None:
        rows, root = _renumber_expression(renumber_rng, rows, root)
    body = "\n".join(f"{token} {left} {right}" for token, left, right in rows)
    return _case(name, f"{len(rows)} {root}\n{body}", _render_expression(expression))


def _random_expression(rng: random.Random, depth: int) -> Expression:
    if depth <= 0 or rng.random() < 0.28:
        return (str(rng.randint(0, 99)), None, None)
    if rng.random() < 0.18:
        return ("-", None, _random_expression(rng, depth - 1))
    return (
        rng.choice(["+", "-", "*", "/"]),
        _random_expression(rng, depth - 1),
        _random_expression(rng, depth - 1),
    )


def _expression_cases(rng: random.Random) -> list[GeneratedCase]:
    leaf = lambda value: (value, None, None)
    sample: Expression = (
        "*",
        ("+", leaf("a"), leaf("b")),
        ("*", leaf("c"), ("-", None, leaf("d"))),
    )
    cases = [
        _expression_case("原题示例", sample),
        _expression_case("单个操作数", leaf("answer")),
        _expression_case("根为一元负号", ("-", None, leaf("42"))),
        _expression_case("嵌套一元运算", ("-", None, ("-", None, leaf("x")))),
    ]
    for index in range(6):
        cases.append(
            _expression_case(
                f"随机重编号表达式树 {index + 1}",
                _random_expression(rng, 4),
                rng,
            )
        )

    def balanced(depth: int) -> Expression:
        if depth == 0:
            return leaf("1")
        return ("+", balanced(depth - 1), balanced(depth - 1))

    cases.append(_expression_case("三万结点压力测试", balanced(14), rng))
    return cases


class _Dsu:
    def __init__(self, size: int):
        self.parent = list(range(size + 1))
        self.rank = [0] * (size + 1)

    def find(self, value: int) -> int:
        while self.parent[value] != value:
            self.parent[value] = self.parent[self.parent[value]]
            value = self.parent[value]
        return value

    def union(self, left: int, right: int) -> bool:
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root == right_root:
            return False
        if self.rank[left_root] < self.rank[right_root]:
            left_root, right_root = right_root, left_root
        self.parent[right_root] = left_root
        if self.rank[left_root] == self.rank[right_root]:
            self.rank[left_root] += 1
        return True


def _mst_result(n: int, edges: list[tuple[int, int, int]]) -> tuple[int, bool]:
    ordered = sorted(edges, key=lambda edge: edge[2])
    global_dsu = _Dsu(n)
    weight = 0
    used = 0
    unique = True
    index = 0
    while index < len(ordered):
        end = index
        while end < len(ordered) and ordered[end][2] == ordered[index][2]:
            end += 1
        candidates: list[tuple[int, int]] = []
        roots: set[int] = set()
        for left, right, _ in ordered[index:end]:
            left_root = global_dsu.find(left)
            right_root = global_dsu.find(right)
            if left_root != right_root:
                candidates.append((left_root, right_root))
                roots.update((left_root, right_root))
        root_ids = {root: item + 1 for item, root in enumerate(sorted(roots))}
        group_dsu = _Dsu(len(root_ids))
        for left_root, right_root in candidates:
            if not group_dsu.union(root_ids[left_root], root_ids[right_root]):
                unique = False
        for left, right, edge_weight in ordered[index:end]:
            if global_dsu.union(left, right):
                weight += edge_weight
                used += 1
        index = end
    if used != n - 1:
        raise ValueError("MST cases must be connected")
    return weight, unique


def _mst_case(name: str, n: int, edges: list[tuple[int, int, int]]) -> GeneratedCase:
    weight, unique = _mst_result(n, edges)
    rows = "\n".join(f"{left} {right} {edge_weight}" for left, right, edge_weight in edges)
    return _case(name, f"{n} {len(edges)}\n{rows}", f"{weight} {'UNIQUE' if unique else 'MULTIPLE'}")


def _random_connected_graph(rng: random.Random, n: int, extra: int, distinct: bool) -> list[tuple[int, int, int]]:
    edges: list[tuple[int, int, int]] = []
    existing: set[tuple[int, int]] = set()
    weights = list(range(1, n + extra + 20))
    rng.shuffle(weights)
    for vertex in range(2, n + 1):
        parent = rng.randint(1, vertex - 1)
        edge = (parent, vertex)
        existing.add(edge)
        edges.append((parent, vertex, weights.pop() if distinct else rng.randint(1, 8)))
    candidates = [(left, right) for left in range(1, n) for right in range(left + 1, n + 1) if (left, right) not in existing]
    rng.shuffle(candidates)
    for left, right in candidates[:extra]:
        edges.append((left, right, weights.pop() if distinct else rng.randint(1, 8)))
    rng.shuffle(edges)
    return edges


def _mst_cases(rng: random.Random) -> list[GeneratedCase]:
    cases = [
        _mst_case("唯一最小生成树", 4, [(1, 2, 1), (2, 3, 2), (3, 4, 3), (1, 4, 9), (1, 3, 7)]),
        _mst_case("三角形多解", 3, [(1, 2, 5), (2, 3, 5), (1, 3, 5)]),
        _mst_case("图本身是一棵树", 5, [(1, 2, 8), (2, 3, 2), (2, 4, 2), (4, 5, 1)]),
        _mst_case("同权边但仍唯一", 4, [(1, 2, 1), (3, 4, 1), (2, 3, 2), (1, 4, 8)]),
    ]
    for index in range(6):
        n = rng.randint(5, 24)
        cases.append(
            _mst_case(
                f"随机连通图 {index + 1}",
                n,
                _random_connected_graph(rng, n, n * 2, distinct=index % 2 == 0),
            )
        )
    return cases


def _missing_positive(values: list[int]) -> int:
    positives = set(values)
    answer = 1
    while answer in positives:
        answer += 1
    return answer


def _missing_positive_cases(rng: random.Random) -> list[GeneratedCase]:
    data = [
        ("缺少 1", [-5, 3, 2, 3]),
        ("连续正整数", [1, 2, 3]),
        ("全非正数", [0, -1, -7, -100]),
        ("缺少中间值", [1, 2, 4, 5, 2, 7]),
        ("含大整数", [1, 2, 2_147_483_647, -2_147_483_648]),
    ]
    for index in range(5):
        n = rng.randint(5, 200)
        data.append((f"随机数组 {index + 1}", [rng.randint(-n, n * 2) for _ in range(n)]))
    stress = list(range(1, 100_001))
    stress[73_456] = -1
    rng.shuffle(stress)
    data.append(("十万元素压力测试", stress))
    return [
        _case(name, _seq_input(str(len(values)), values), str(_missing_positive(values)))
        for name, values in data
    ]


def _reorder(values: list[int]) -> list[int]:
    result = []
    left, right = 0, len(values) - 1
    while left <= right:
        result.append(values[left])
        if left != right:
            result.append(values[right])
        left += 1
        right -= 1
    return result


def _reorder_cases(rng: random.Random) -> list[GeneratedCase]:
    data = [
        ("偶数长度", [1, 2, 3, 4, 5, 6]),
        ("奇数长度", [10, 20, 30, 40, 50]),
        ("空链表", []),
        ("单结点", [42]),
        ("两个结点", [-1, 9]),
    ]
    for index in range(5):
        n = rng.randint(3, 160)
        data.append((f"随机链表 {index + 1}", [rng.randint(-1000, 1000) for _ in range(n)]))
    data.append(("十万结点压力测试", list(range(-50_000, 50_000))))
    return [
        _case(name, _seq_input(str(len(values)), values), _line(_reorder(values)))
        for name, values in data
    ]


def _triple_distance(a: list[int], b: list[int], c: list[int]) -> int:
    i = j = k = 0
    answer = 10**30
    while i < len(a) and j < len(b) and k < len(c):
        low = min(a[i], b[j], c[k])
        high = max(a[i], b[j], c[k])
        answer = min(answer, 2 * (high - low))
        if a[i] == low:
            i += 1
        elif b[j] == low:
            j += 1
        else:
            k += 1
    return answer


def _triple_case(name: str, a: list[int], b: list[int], c: list[int]) -> GeneratedCase:
    body = f"{len(a)} {len(b)} {len(c)}\n{_line(a)}\n{_line(b)}\n{_line(c)}"
    return _case(name, body, str(_triple_distance(a, b, c)))


def _triple_cases(rng: random.Random) -> list[GeneratedCase]:
    cases = [
        _triple_case("原题示例", [-1, 0, 9], [-25, -10, 10, 11], [2, 9, 17, 30, 41]),
        _triple_case("三个集合有共同元素", [1, 5, 9], [-4, 5, 8], [5, 6]),
        _triple_case("每个集合一个元素", [-10], [0], [20]),
        _triple_case("区间完全分离", [-100, -90], [1, 2, 3], [100, 200]),
        _triple_case("32 位整数边界", [-(2**31)], [0], [2**31 - 1]),
    ]
    for index in range(6):
        arrays = []
        for _ in range(3):
            length = rng.randint(2, 150)
            arrays.append(sorted(rng.randint(-10**8, 10**8) for _ in range(length)))
        cases.append(_triple_case(f"随机升序集合 {index + 1}", *arrays))
    cases.append(
        _triple_case(
            "十五万元素压力测试",
            list(range(-150_000, -100_000)),
            list(range(-50_000, 0)),
            list(range(100_000, 150_000)),
        )
    )
    return cases


def _decode_prefix_code(codes: list[tuple[str, str]], bits: str) -> str:
    root: dict = {}
    for symbol, code in codes:
        node = root
        if not code:
            return "INVALID"
        for bit in code:
            if bit not in "01" or "symbol" in node:
                return "INVALID"
            node = node.setdefault(bit, {})
        if "symbol" in node or "0" in node or "1" in node:
            return "INVALID"
        node["symbol"] = symbol
    result: list[str] = []
    node = root
    for bit in bits:
        if bit not in node:
            return "INVALID"
        node = node[bit]
        if "symbol" in node:
            result.append(node["symbol"])
            node = root
    return "".join(result) if node is root else "INVALID"


def _prefix_case(name: str, codes: list[tuple[str, str]], bits: str) -> GeneratedCase:
    rows = "\n".join(f"{symbol} {code}" for symbol, code in codes)
    return _case(name, f"{len(codes)}\n{rows}\n{bits}", _decode_prefix_code(codes, bits))


def _prefix_cases(rng: random.Random) -> list[GeneratedCase]:
    cases = [
        _prefix_case("合法前缀码译码", [("A", "0"), ("B", "10"), ("C", "110"), ("D", "111")], "0101101110"),
        _prefix_case("编码互为前缀", [("A", "0"), ("B", "01")], "01"),
        _prefix_case("重复编码", [("A", "10"), ("B", "10")], "10"),
        _prefix_case("比特串不完整", [("A", "0"), ("B", "10"), ("C", "11")], "0101"),
        _prefix_case("比特串无匹配分支", [("A", "00"), ("B", "01")], "11"),
    ]
    code_sets = [
        [("A", "00"), ("B", "01"), ("C", "10"), ("D", "110"), ("E", "111")],
        [("X", "0"), ("Y", "100"), ("Z", "101"), ("P", "110"), ("Q", "111")],
    ]
    for index in range(5):
        codes = code_sets[index % len(code_sets)]
        message = [rng.choice(codes)[0] for _ in range(rng.randint(5, 40))]
        mapping = dict(codes)
        bits = "".join(mapping[symbol] for symbol in message)
        cases.append(_prefix_case(f"随机译码 {index + 1}", codes, bits))
    return cases


def _euler_exists(n: int, edges: list[tuple[int, int]]) -> int:
    adjacency = [[] for _ in range(n + 1)]
    degree = [0] * (n + 1)
    for left, right in edges:
        adjacency[left].append(right)
        adjacency[right].append(left)
        degree[left] += 1
        degree[right] += 1
    start = next((vertex for vertex in range(1, n + 1) if degree[vertex]), None)
    if start is None:
        return 0
    seen = {start}
    stack = [start]
    while stack:
        current = stack.pop()
        for neighbor in adjacency[current]:
            if neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    connected = all(degree[vertex] == 0 or vertex in seen for vertex in range(1, n + 1))
    odd = sum(value % 2 for value in degree)
    return int(connected and odd in (0, 2))


def _euler_case(name: str, n: int, edges: list[tuple[int, int]]) -> GeneratedCase:
    rows = "\n".join(f"{left} {right}" for left, right in edges)
    return _case(name, f"{n} {len(edges)}\n{rows}", str(_euler_exists(n, edges)))


def _euler_cases(rng: random.Random) -> list[GeneratedCase]:
    cases = [
        _euler_case("一条链", 5, [(1, 2), (2, 3), (3, 4), (4, 5)]),
        _euler_case("一个环", 4, [(1, 2), (2, 3), (3, 4), (4, 1)]),
        _euler_case("四个奇度顶点", 5, [(1, 2), (1, 3), (1, 4), (1, 5)]),
        _euler_case("非零度顶点不连通", 6, [(1, 2), (2, 3), (4, 5), (5, 6)]),
    ]
    for index in range(6):
        n = rng.randint(4, 30)
        edge_set = {(vertex, vertex + 1) for vertex in range(1, n)}
        candidates = [(left, right) for left in range(1, n) for right in range(left + 1, n + 1) if (left, right) not in edge_set]
        rng.shuffle(candidates)
        edge_set.update(candidates[: rng.randint(0, min(len(candidates), n * 2))])
        cases.append(_euler_case(f"随机连通图 {index + 1}", n, sorted(edge_set)))
    cases.append(_euler_case("两千顶点链", 2_000, [(i, i + 1) for i in range(1, 2_000)]))
    return cases


def _stable_sort_case(name: str, records: list[tuple[int, int]]) -> GeneratedCase:
    ordered = sorted(records, key=lambda record: record[0])
    rows = "\n".join(f"{key} {identifier}" for key, identifier in records)
    answer = "\n".join(f"{key} {identifier}" for key, identifier in ordered)
    return _case(name, f"{len(records)}\n{rows}", answer)


def _stable_sort_cases(rng: random.Random) -> list[GeneratedCase]:
    cases = [
        _stable_sort_case("原题关键字", [(25, 1), (-10, 2), (25, 3), (10, 4), (11, 5), (19, 6)]),
        _stable_sort_case("全部相等", [(7, item) for item in range(1, 8)]),
        _stable_sort_case("已经有序", [(-3, 1), (0, 2), (4, 3), (9, 4)]),
        _stable_sort_case("逆序且有重复", [(5, 1), (4, 2), (4, 3), (2, 4), (1, 5)]),
    ]
    for index in range(6):
        n = rng.randint(5, 100)
        records = [(rng.randint(-20, 20), item + 1) for item in range(n)]
        cases.append(_stable_sort_case(f"随机记录 {index + 1}", records))
    cases.append(
        _stable_sort_case(
            "五千条稳定性压力测试",
            [(rng.randint(-25, 25), item + 1) for item in range(5_000)],
        )
    )
    return cases


def _array_is_bst(values: list[int]) -> int:
    def check(index: int, low: int, high: int) -> bool:
        if index >= len(values) or values[index] == -1:
            return True
        value = values[index]
        return low < value < high and check(index * 2 + 1, low, value) and check(index * 2 + 2, value, high)

    return int(check(0, -(10**30), 10**30))


def _bst_array_case(name: str, values: list[int]) -> GeneratedCase:
    return _case(name, _seq_input(str(len(values)), values), str(_array_is_bst(values)))


def _insert_bst(tree: dict, value: int) -> None:
    if "value" not in tree:
        tree.update(value=value, left={}, right={})
        return
    _insert_bst(tree["left"] if value < tree["value"] else tree["right"], value)


def _bst_to_array(tree: dict) -> list[int]:
    indexed: dict[int, int] = {}

    def visit(node: dict, index: int) -> None:
        if not node:
            return
        indexed[index] = node["value"]
        visit(node["left"], index * 2 + 1)
        visit(node["right"], index * 2 + 2)

    visit(tree, 0)
    result = [-1] * (max(indexed) + 1)
    for index, value in indexed.items():
        result[index] = value
    return result


def _bst_array_cases(rng: random.Random) -> list[GeneratedCase]:
    cases = [
        _bst_array_case("原题中的合法树", [40, 25, 60, -1, 30, -1, 80, -1, -1, 27]),
        _bst_array_case("原题中的非法树", [40, 50, 60, -1, 30, -1, -1, -1, -1, -1, 35]),
        _bst_array_case("单结点", [1]),
        _bst_array_case("祖先范围违规", [20, 10, 30, 5, 25, 21, 40]),
        _bst_array_case("重复关键字", [10, 5, 10]),
    ]
    for index in range(5):
        count = rng.randint(5, 35)
        ordered = rng.sample(range(1, 10_000), count)
        tree: dict = {}
        # A shuffled median-first order avoids pathological heap indices.
        ordered.sort()
        insertion: list[int] = []

        def medians(items: list[int]) -> None:
            if not items:
                return
            middle = len(items) // 2
            insertion.append(items[middle])
            medians(items[:middle])
            medians(items[middle + 1 :])

        medians(ordered)
        for value in insertion:
            _insert_bst(tree, value)
        values = _bst_to_array(tree)
        if index % 2:
            occupied = [item for item, value in enumerate(values) if value != -1]
            target = rng.choice(occupied[1:])
            values[target] = values[0] + (1 if target % 2 else -1)
        cases.append(_bst_array_case(f"随机{'非法' if index % 2 else '合法'}树 {index + 1}", values))
    complete_size = 65_535
    complete = [0] * complete_size
    next_value = 1

    def assign_inorder(index: int) -> None:
        nonlocal next_value
        if index >= complete_size:
            return
        assign_inorder(index * 2 + 1)
        complete[index] = next_value
        next_value += 1
        assign_inorder(index * 2 + 2)

    assign_inorder(0)
    cases.append(_bst_array_case("六万结点合法 BST", complete))
    return cases


def _smallest_ten_cases(rng: random.Random) -> list[GeneratedCase]:
    data = [
        ("恰好十个数", [9, 1, 8, 2, 7, 3, 6, 4, 5, 0]),
        ("包含重复值", [5] * 8 + [1] * 7 + [9, -2, -2, 20]),
        ("严格递增", list(range(-5, 25))),
        ("严格递减", list(range(100, 50, -1))),
    ]
    for index, n in enumerate((100, 500, 2_000, 5_000, 20_000, 100_001)):
        data.append((f"随机大数组 {index + 1}", [rng.randint(-10**9, 10**9) for _ in range(n)]))
    return [
        _case(name, _seq_input(str(len(values)), values), _line(sorted(values)[:10]))
        for name, values in data
    ]


def _k_vertices_case(name: str, n: int, edges: list[tuple[int, int]]) -> GeneratedCase:
    incoming = [0] * (n + 1)
    outgoing = [0] * (n + 1)
    for start, end in edges:
        outgoing[start] += 1
        incoming[end] += 1
    vertices = [vertex for vertex in range(1, n + 1) if outgoing[vertex] > incoming[vertex]]
    matrix = [[0] * n for _ in range(n)]
    for start, end in edges:
        matrix[start - 1][end - 1] = 1
    rows = "\n".join(_line(row) for row in matrix)
    answer = str(len(vertices)) + (f"\n{_line(vertices)}" if vertices else "")
    return _case(name, f"{n}\n{rows}", answer)


def _k_vertices_cases(rng: random.Random) -> list[GeneratedCase]:
    cases = [
        _k_vertices_case("多个 K 顶点", 5, [(1, 3), (1, 4), (2, 4), (2, 5), (3, 5)]),
        _k_vertices_case("有向环", 4, [(1, 2), (2, 3), (3, 4), (4, 1)]),
        _k_vertices_case("空边集", 5, []),
        _k_vertices_case("含自环", 4, [(1, 1), (1, 2), (3, 2), (3, 4)]),
    ]
    for index in range(6):
        n = rng.randint(4, 40)
        candidates = [(start, end) for start in range(1, n + 1) for end in range(1, n + 1)]
        rng.shuffle(candidates)
        edges = candidates[: rng.randint(1, min(len(candidates), n * 4))]
        cases.append(_k_vertices_case(f"随机有向图 {index + 1}", n, edges))
    stress_n = 600
    stress_edges = [(vertex, vertex + 1) for vertex in range(1, stress_n)]
    stress_edges.extend((1, vertex) for vertex in range(3, stress_n + 1))
    cases.append(_k_vertices_case("六百阶邻接矩阵", stress_n, stress_edges))
    return cases


def _replacement_runs(values: list[int], capacity: int) -> list[list[int]]:
    current = values[:capacity]
    heapq.heapify(current)
    frozen: list[int] = []
    source = capacity
    runs: list[list[int]] = []
    run: list[int] = []
    while current:
        value = heapq.heappop(current)
        run.append(value)
        if source < len(values):
            incoming = values[source]
            source += 1
            if incoming >= value:
                heapq.heappush(current, incoming)
            else:
                frozen.append(incoming)
        if not current:
            runs.append(run)
            run = []
            current = frozen
            heapq.heapify(current)
            frozen = []
    return runs


def _replacement_case(name: str, values: list[int], capacity: int) -> GeneratedCase:
    runs = _replacement_runs(values, capacity)
    output = [str(len(runs))]
    output.extend(f"{len(run)} {_line(run)}" for run in runs)
    return _case(name, _seq_input(f"{len(values)} {capacity}", values), "\n".join(output))


def _replacement_cases(rng: random.Random) -> list[GeneratedCase]:
    official = [51, 94, 37, 92, 14, 63, 15, 99, 48, 56, 23, 60, 31, 17, 43, 8, 90, 166, 100]
    cases = [
        _replacement_case("原题记录序列", official, 4),
        _replacement_case("工作区容量为一", [5, 1, 4, 2, 3], 1),
        _replacement_case("输入已经升序", list(range(1, 16)), 4),
        _replacement_case("输入严格降序", list(range(20, 0, -1)), 5),
        _replacement_case("记录少于工作区", [8, 3, 3, 7], 10),
    ]
    for index in range(5):
        n = rng.randint(20, 150)
        cases.append(
            _replacement_case(
                f"随机文件 {index + 1}",
                [rng.randint(-1000, 1000) for _ in range(n)],
                rng.randint(2, min(20, n)),
            )
        )
    return cases


def _unique_topological(n: int, edges: list[tuple[int, int]]) -> int:
    adjacency = [[] for _ in range(n + 1)]
    indegree = [0] * (n + 1)
    for start, end in edges:
        adjacency[start].append(end)
        indegree[end] += 1
    available = [vertex for vertex in range(1, n + 1) if indegree[vertex] == 0]
    heapq.heapify(available)
    visited = 0
    unique = True
    while available:
        if len(available) != 1:
            unique = False
        current = heapq.heappop(available)
        visited += 1
        for neighbor in adjacency[current]:
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                heapq.heappush(available, neighbor)
    return int(unique and visited == n)


def _topological_case(name: str, n: int, edges: list[tuple[int, int]]) -> GeneratedCase:
    rows = "\n".join(f"{start} {end}" for start, end in edges)
    return _case(name, f"{n} {len(edges)}\n{rows}", str(_unique_topological(n, edges)))


def _topological_cases(rng: random.Random) -> list[GeneratedCase]:
    cases = [
        _topological_case("唯一拓扑序列", 5, [(1, 2), (2, 3), (3, 4), (4, 5)]),
        _topological_case("存在分叉", 4, [(1, 2), (1, 3), (2, 4), (3, 4)]),
        _topological_case("有向环", 3, [(1, 2), (2, 3), (3, 1)]),
        _topological_case("单个顶点", 1, []),
        _topological_case("多点空图", 6, []),
    ]
    for index in range(5):
        n = rng.randint(5, 50)
        if index % 2 == 0:
            edges = [(vertex, vertex + 1) for vertex in range(1, n)]
            for start, end, _ in _dag_edges(rng, n, n):
                if (start, end) not in edges:
                    edges.append((start, end))
        else:
            edges = [(1, vertex) for vertex in range(2, n + 1)]
        cases.append(_topological_case(f"随机有向图 {index + 1}", n, edges))
    cases.append(
        _topological_case(
            "十万顶点唯一拓扑序列",
            100_000,
            [(vertex, vertex + 1) for vertex in range(1, 100_000)],
        )
    )
    return cases


def _quadratic_probe(
    table_size: int, multiplier: int, keys: list[int], queries: list[int]
) -> tuple[list[int | None], list[tuple[list[int], int]]]:
    table: list[int | None] = [None] * table_size
    for key in keys:
        start = (key * multiplier) % table_size
        for step in range(table_size):
            address = (start + step * step) % table_size
            if table[address] is None or table[address] == key:
                table[address] = key
                break
    results = []
    for key in queries:
        start = (key * multiplier) % table_size
        addresses = []
        found = 0
        for step in range(table_size):
            address = (start + step * step) % table_size
            addresses.append(address)
            if table[address] == key:
                found = 1
                break
            if table[address] is None:
                break
        results.append((addresses, found))
    return table, results


def _quadratic_case(
    name: str, table_size: int, multiplier: int, keys: list[int], queries: list[int]
) -> GeneratedCase:
    table, results = _quadratic_probe(table_size, multiplier, keys, queries)
    rendered = " ".join("_" if value is None else str(value) for value in table)
    lines = [rendered]
    lines.extend(f"{len(addresses)} {_line(addresses)} {found}" for addresses, found in results)
    input_data = f"{table_size} {multiplier} {len(keys)} {len(queries)}\n{_line(keys)}\n{_line(queries)}"
    return _case(name, input_data, "\n".join(lines))


def _quadratic_cases(rng: random.Random) -> list[GeneratedCase]:
    cases = [
        _quadratic_case("原题关键字", 11, 3, [20, 3, 11, 18, 9, 14, 7], [14, 8]),
        _quadratic_case("无冲突", 13, 1, [1, 2, 3, 4], [1, 9]),
        _quadratic_case("反复访问同一地址", 8, 1, [0, 8, 16, 24, 32, 40], [40, 48]),
        _quadratic_case("表未满但插入失败", 12, 1, [0, 12, 24, 36, 48, 60, 72], [72, 84]),
    ]
    for index in range(6):
        table_size = rng.choice([11, 13, 17, 19, 23])
        count = rng.randint(3, table_size - 2)
        keys = rng.sample(range(0, 5000), count)
        queries = rng.sample(keys, min(2, len(keys))) + rng.sample(range(6000, 7000), 2)
        cases.append(_quadratic_case(f"随机散列表 {index + 1}", table_size, rng.randint(1, 9), keys, queries))
    return cases


def _suffix_products(values: list[int]) -> list[int]:
    result = [0] * len(values)
    suffix_min = suffix_max = values[-1]
    for index in range(len(values) - 1, -1, -1):
        suffix_min = min(suffix_min, values[index])
        suffix_max = max(suffix_max, values[index])
        result[index] = max(values[index] * suffix_min, values[index] * suffix_max)
    return result


def _suffix_product_cases(rng: random.Random) -> list[GeneratedCase]:
    data = [
        ("原题示例", [1, 4, -9, 6]),
        ("单元素", [-7]),
        ("全部正数", [8, 1, 5, 2, 9]),
        ("全部负数", [-2, -8, -1, -10]),
        ("含零和正负数", [0, -3, 5, -8, 2, 0]),
        ("大整数", [10**9, -(10**9), 999_999_999]),
    ]
    for index in range(4):
        n = rng.randint(5, 300)
        data.append((f"随机数组 {index + 1}", [rng.randint(-10**9, 10**9) for _ in range(n)]))
    data.append(("五万元素压力测试", [rng.randint(-10**9, 10**9) for _ in range(50_000)]))
    return [
        _case(name, _seq_input(str(len(values)), values), _line(_suffix_products(values)))
        for name, values in data
    ]


def _aoe_result(n: int, edges: list[tuple[int, int, int]]) -> tuple[int, list[int], list[int]]:
    outgoing: list[list[tuple[int, int, int]]] = [[] for _ in range(n + 1)]
    incoming: list[list[tuple[int, int, int]]] = [[] for _ in range(n + 1)]
    indegree = [0] * (n + 1)
    for activity, (start, end, duration) in enumerate(edges, 1):
        outgoing[start].append((end, duration, activity))
        incoming[end].append((start, duration, activity))
        indegree[end] += 1
    queue = [vertex for vertex in range(1, n + 1) if indegree[vertex] == 0]
    heapq.heapify(queue)
    order = []
    earliest = [0] * (n + 1)
    while queue:
        current = heapq.heappop(queue)
        order.append(current)
        for end, duration, _ in outgoing[current]:
            earliest[end] = max(earliest[end], earliest[current] + duration)
            indegree[end] -= 1
            if indegree[end] == 0:
                heapq.heappush(queue, end)
    project_duration = max(earliest)
    latest = [project_duration] * (n + 1)
    for current in reversed(order):
        if outgoing[current]:
            latest[current] = min(latest[end] - duration for end, duration, _ in outgoing[current])
    slacks = []
    critical = []
    for activity, (start, end, duration) in enumerate(edges, 1):
        slack = latest[end] - duration - earliest[start]
        slacks.append(slack)
        if slack == 0:
            critical.append(activity)
    return project_duration, critical, slacks


def _aoe_case(name: str, n: int, edges: list[tuple[int, int, int]]) -> GeneratedCase:
    duration, critical, slacks = _aoe_result(n, edges)
    rows = "\n".join(f"{start} {end} {weight}" for start, end, weight in edges)
    critical_line = f"{len(critical)}" + (f" {_line(critical)}" if critical else "")
    return _case(name, f"{n} {len(edges)}\n{rows}", f"{duration}\n{critical_line}\n{_line(slacks)}")


def _aoe_cases(rng: random.Random) -> list[GeneratedCase]:
    cases = [
        _aoe_case("单条关键路径", 4, [(1, 2, 3), (2, 3, 5), (3, 4, 2)]),
        _aoe_case("两条并行路径", 4, [(1, 2, 3), (2, 4, 4), (1, 3, 2), (3, 4, 7)]),
        _aoe_case("多条关键路径", 4, [(1, 2, 3), (2, 4, 5), (1, 3, 4), (3, 4, 4)]),
    ]
    for index, n in enumerate((6, 8, 10, 15, 20, 30, 50)):
        cases.append(_aoe_case(f"随机 AOE 网 {index + 1}", n, _dag_edges(rng, n, n * 2, 20)))
    return cases


def source_marker(key: str) -> str:
    return f"<!-- {SOURCE_PREFIX}{key};version:{BANK_VERSION} -->"


def _statement(definition: ProblemDefinition, sample: GeneratedCase) -> str:
    title = f"408-{definition.year} {definition.title}"
    return f"""# {title}

**【真题（{definition.year}）】**

> 来源：{definition.year} 年全国硕士研究生招生考试 408 数据结构综合应用题第 {definition.question} 题。{definition.adaptation}

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

原卷考查算法设计思想、正确性与复杂度分析，没有规定完整的标准输入输出。本题保留原考点，并补充了适合本地 OJ 自动判定的输入输出约定；题面不是对原卷文字的逐字转载。

{source_marker(definition.key)}
"""


def _definitions() -> list[ProblemDefinition]:
    candidates = [
        ProblemDefinition(
            key="408-2009-q42-kth-from-end",
            year=2009,
            question="42",
            title="单链表倒数第 k 个结点",
            body=r"""给定一个带头结点的单链表和正整数 $k$。在不改变链表的前提下，查找倒数第 $k$ 个位置上的结点。

若查找成功，输出成功标志及该结点的数据；否则输出失败标志。""",
            input_format=r"""第一行包含两个整数 $n,k$，分别表示链表的数据结点数和待查位置。

第二行包含 $n$ 个整数，按链表从前到后的顺序给出；当 $n=0$ 时该行可以省略。""",
            output_format=r"""若倒数第 $k$ 个结点存在，输出 `1 value`；否则输出 `0`。""",
            constraints=r"""- $0 \le n \le 200000$
- $1 \le k \le 200001$
- 结点数据在 32 位有符号整数范围内""",
            tags=("408真题", "链表", "双指针"),
            build_cases=_kth_cases,
        ),
        ProblemDefinition(
            key="408-2010-q41-linear-probing-asl",
            year=2010,
            question="41",
            title="线性探测散列表与平均查找长度",
            body=r"""将一组互不相同的非负关键字依次插入散列表。表长为 $m$，散列函数为

$$H(key)=(key\times c)\bmod h$$

发生冲突时采用线性探测，地址按 $(H(key)+i)\bmod m$ 产生。构造散列表，并计算等概率情况下查找成功与查找失败的平均查找长度。""",
            input_format=r"""第一行包含 $m,h,c,n$。第二行包含 $n$ 个互不相同的非负关键字。""",
            output_format=r"""第一行输出散列表的 $m$ 个槽位，空槽输出 `_`。

第二行输出两个最简分数，依次为查找成功和查找失败的平均查找长度。失败查找对初始地址 $0$ 到 $h-1$ 等概率统计，并计入最终检查空槽的一次比较。""",
            constraints=r"""- $2 \le h \le m \le 2000$
- $1 \le n < m$
- 所有关键字均能插入表中""",
            tags=("408真题", "查找", "哈希表"),
            build_cases=_linear_probe_cases,
            adaptation="原题使用固定关键字和散列函数；这里将参数一般化，以便生成独立测试数据。",
        ),
        ProblemDefinition(
            key="408-2010-q42-left-rotate",
            year=2010,
            question="42",
            title="数组循环左移",
            body=r"""将数组 $R=(x_0,x_1,\ldots,x_{n-1})$ 循环左移 $p$ 个位置，得到

$$R'=(x_p,x_{p+1},\ldots,x_{n-1},x_0,\ldots,x_{p-1})$$""",
            input_format=r"""第一行包含 $n,p$。第二行包含 $n$ 个整数。""",
            output_format=r"""输出循环左移后的 $n$ 个整数，以单个空格分隔。""",
            constraints=r"""- $2 \le n \le 200000$
- $0 < p < n$
- 数组元素在 32 位有符号整数范围内""",
            tags=("408真题", "顺序表", "数组"),
            build_cases=_rotate_cases,
        ),
        ProblemDefinition(
            key="408-2011-q41-critical-path",
            year=2011,
            question="41",
            title="AOE 网的关键路径",
            body=r"""给定一个以顶点 $1$ 为源点、顶点 $n$ 为汇点的有向无环 AOE 网。边权表示活动持续时间。

求工程最短完工时间，并输出一条关键路径。若存在多条关键路径，输出顶点序列字典序最小的一条。""",
            input_format=r"""第一行包含 $n,m$。接下来 $m$ 行每行包含 $u,v,w$，表示从 $u$ 到 $v$、持续时间为 $w$ 的活动。

输入保证 $u<v$，每个顶点都位于从 $1$ 到 $n$ 的某条路径上。""",
            output_format=r"""第一行输出最短完工时间。第二行先输出路径顶点数，再输出关键路径上的顶点编号。""",
            constraints=r"""- $2 \le n \le 2000$
- $1 \le m \le 20000$
- $1 \le w \le 10^9$""",
            tags=("408真题", "图", "关键路径", "动态规划"),
            build_cases=_critical_path_cases,
            adaptation="原题给出固定上三角邻接矩阵；这里改为可批量生成的边表，并约定多解时的唯一输出。",
        ),
        ProblemDefinition(
            key="408-2011-q42-lower-median",
            year=2011,
            question="42",
            title="两个等长升序序列的中位数",
            body=r"""给定两个长度均为 $n$ 的非降序整数序列 $A$ 和 $B$。将二者合并后共有 $2n$ 个元素，求其中第 $n$ 小的元素，即下中位数。""",
            input_format=r"""第一行包含 $n$。第二、三行分别包含序列 $A$ 和 $B$ 的 $n$ 个整数。""",
            output_format=r"""输出两个序列的下中位数。""",
            constraints=r"""- $1 \le n \le 200000$
- 两个序列均按非降序排列
- 序列元素在 32 位有符号整数范围内""",
            tags=("408真题", "顺序表", "二分查找"),
            build_cases=_median_cases,
        ),
        ProblemDefinition(
            key="408-2012-q41-optimal-merge",
            year=2012,
            question="41",
            title="不等长有序表的最优合并",
            body=r"""有 $n$ 个长度不等的升序表。每次选择两个表合并为一个新升序表，合并长度分别为 $x,y$ 的两个表在最坏情况下需要 $x+y-1$ 次关键字比较。

求将所有表合并为一个表所需的最小最坏比较总次数。""",
            input_format=r"""第一行包含表的数量 $n$。第二行包含各表长度 $L_1,L_2,\ldots,L_n$。""",
            output_format=r"""输出最小的最坏比较总次数。""",
            constraints=r"""- $2 \le n \le 200000$
- $1 \le L_i \le 10^9$
- 答案不超过 64 位有符号整数范围""",
            tags=("408真题", "贪心", "堆", "归并"),
            build_cases=_optimal_merge_cases,
            adaptation="原题先计算六个固定表的最优合并，再要求推广策略；这里直接判定一般情形。",
        ),
        ProblemDefinition(
            key="408-2012-q42-shared-suffix-node",
            year=2012,
            question="42",
            title="两个单链表的共同后缀起点",
            body=r"""两个带头结点的单链表可以共享同一段结点存储空间。给定所有数据结点及两个链表的首个数据结点编号，找出共同后缀的起始结点。

注意：结点数据相等不代表结点相同，只有编号相同才表示共享同一个结点。""",
            input_format=r"""第一行包含 $n,h_1,h_2$，其中 $n$ 为数据结点数，$h_1,h_2$ 为两个链表的首结点编号；`0` 表示空指针。

随后 $n$ 行中的第 $i$ 行包含 `data next`，表示编号 $i$ 的结点数据和后继编号。输入保证两个链表无环。""",
            output_format=r"""输出共同后缀起始结点的编号；若不存在共同结点，输出 `-1`。""",
            constraints=r"""- $0 \le n \le 200000$
- $0 \le h_1,h_2,next \le n$
- 结点数据在 32 位有符号整数范围内""",
            tags=("408真题", "链表", "双指针"),
            build_cases=_shared_suffix_cases,
            adaptation="原题返回指针位置；这里使用结点编号精确保留“共享结点身份”这一考点。",
        ),
        ProblemDefinition(
            key="408-2013-q41-majority-element",
            year=2013,
            question="41",
            title="数组的主元素",
            body=r"""整数序列 $A$ 长度为 $n$，且 $0\le A_i<n$。若某个值出现次数严格大于 $n/2$，则称其为主元素。

找出主元素；若不存在，输出 `-1`。""",
            input_format=r"""第一行包含 $n$。第二行包含 $n$ 个整数。""",
            output_format=r"""输出主元素，或在不存在时输出 `-1`。""",
            constraints=r"""- $1 \le n \le 200000$
- $0 \le A_i < n$""",
            tags=("408真题", "顺序表", "Boyer-Moore"),
            build_cases=_majority_cases,
        ),
        ProblemDefinition(
            key="408-2014-q41-binary-tree-wpl",
            year=2014,
            question="41",
            title="二叉树的带权路径长度",
            body=r"""二叉树的带权路径长度 WPL 是所有叶结点的“权值乘以从根到该叶结点的边数”之和。根结点深度为 $0$。

给定一棵非空二叉树，求其 WPL。内部结点的权值输入为 `0`，不参与计算。""",
            input_format=r"""第一行包含 $n,root$。随后 $n$ 行中的第 $i$ 行包含 `weight left right`，描述编号 $i$ 的结点；`0` 表示空孩子。""",
            output_format=r"""输出二叉树的 WPL。""",
            constraints=r"""- $1 \le n \le 200000$
- 叶结点权值为 $0$ 到 $10^9$
- 答案不超过 64 位有符号整数范围""",
            tags=("408真题", "树", "深度优先搜索"),
            build_cases=_wpl_cases,
        ),
        ProblemDefinition(
            key="408-2015-q41-abs-deduplicate-list",
            year=2015,
            question="41",
            title="删除绝对值重复的链表结点",
            body=r"""单链表中有 $m$ 个整数，且每个数据的绝对值不超过给定上界 $n$。从前向后扫描链表，对于绝对值相同的结点只保留第一次出现者。

输出删除重复结点后的数据序列。""",
            input_format=r"""第一行包含 $m,n$。第二行包含链表中的 $m$ 个整数。""",
            output_format=r"""输出保留下来的整数，保持原相对顺序，以单个空格分隔。""",
            constraints=r"""- $1 \le m \le 200000$
- $1 \le n \le 10^6$
- $|data_i|\le n$""",
            tags=("408真题", "链表", "哈希表"),
            build_cases=_deduplicate_cases,
        ),
        ProblemDefinition(
            key="408-2015-q42-adjacency-matrix-walks",
            year=2015,
            question="42",
            title="邻接矩阵幂与定长通路数",
            body=r"""有向图的邻接矩阵为 $A$。矩阵 $A^k$ 的第 $i$ 行第 $j$ 列表示从顶点 $i$ 到顶点 $j$、长度恰为 $k$ 的通路条数。

给定 $A$ 和 $k$，计算 $A^k$。通路允许重复经过顶点或边。""",
            input_format=r"""第一行包含 $n,k$。随后 $n$ 行给出 $n\times n$ 的 0/1 邻接矩阵。""",
            output_format=r"""输出 $A^k$，共 $n$ 行，每行 $n$ 个整数。""",
            constraints=r"""- $1 \le n \le 30$
- $1 \le k \le 50$
- 所有结果均在 64 位有符号整数范围内""",
            tags=("408真题", "图", "邻接矩阵", "矩阵快速幂"),
            build_cases=_walk_cases,
            adaptation="原题在固定图上解释邻接矩阵平方的含义；这里将该含义改编为可执行的矩阵幂任务。",
        ),
        ProblemDefinition(
            key="408-2016-q43-balanced-partition",
            year=2016,
            question="43",
            title="等规模划分并最大化和差",
            body=r"""将由 $n$ 个正整数组成的序列按元素位置划分为两个不相交的子序列。数值相同但位置不同的元素分别计数。首先要求两个子序列的元素个数之差最小，在此条件下再使两组元素和的绝对差最大。

输出最小元素个数差和对应的最大元素和差。""",
            input_format=r"""第一行包含 $n$。第二行包含 $n$ 个正整数。""",
            output_format=r"""输出 `count_difference sum_difference`。""",
            constraints=r"""- $2 \le n \le 200000$
- $1 \le A_i \le 10^9$
- 元素和使用 64 位整数""",
            tags=("408真题", "顺序表", "快速选择", "排序"),
            build_cases=_partition_cases,
        ),
        ProblemDefinition(
            key="408-2017-q41-expression-tree-infix",
            year=2017,
            question="41",
            title="表达式树转中缀表达式",
            body=r"""给定一棵表达式树。叶结点保存操作数，非叶结点保存二元运算符或一元负号 `-`。

按中序次序输出等价表达式。根运算子树不加最外层括号，其他每个运算子树都加一对括号，以明确反映原树的计算次序。一元负号结点的左孩子为 `0`。""",
            input_format=r"""第一行包含 $n,root$。随后 $n$ 行中的第 $i$ 行包含 `token left right`，描述编号 $i$ 的结点；孩子编号 `0` 表示空。

`token` 是不含空白、长度不超过 10 的操作数，或 `+ - * /`。""",
            output_format=r"""输出唯一的中缀表达式，不包含空格。""",
            constraints=r"""- $1 \le n \le 200000$
- 输入保证是一棵合法表达式树""",
            tags=("408真题", "树", "中序遍历", "递归"),
            build_cases=_expression_cases,
        ),
        ProblemDefinition(
            key="408-2017-q42-mst-uniqueness",
            year=2017,
            question="42",
            title="最小生成树的权值与唯一性",
            body=r"""给定一个带权无向连通图，求最小生成树的总权值，并判断最小生成树是否唯一。

若存在两棵或更多权值同为最小的生成树，则判为不唯一。""",
            input_format=r"""第一行包含 $n,m$。随后 $m$ 行每行包含 $u,v,w$，表示一条连接 $u,v$、权值为 $w$ 的无向边。""",
            output_format=r"""输出 `weight UNIQUE` 或 `weight MULTIPLE`。""",
            constraints=r"""- $2 \le n \le 2000$
- $n-1 \le m \le 20000$
- $1 \le w \le 10^9$
- 图连通且没有自环""",
            tags=("408真题", "图", "最小生成树", "并查集"),
            build_cases=_mst_cases,
            adaptation="原题使用固定图执行 Prim 算法并讨论唯一性；这里推广为任意连通图，并只输出无歧义的权值和唯一性。",
        ),
        ProblemDefinition(
            key="408-2018-q41-smallest-missing-positive",
            year=2018,
            question="41",
            title="最小未出现正整数",
            body=r"""给定一个包含 $n$ 个整数的数组，找出数组中没有出现过的最小正整数。""",
            input_format=r"""第一行包含 $n$。第二行包含 $n$ 个整数。""",
            output_format=r"""输出最小未出现正整数。""",
            constraints=r"""- $1 \le n \le 200000$
- 数组元素在 32 位有符号整数范围内""",
            tags=("408真题", "顺序表", "数组", "哈希表"),
            build_cases=_missing_positive_cases,
        ),
        ProblemDefinition(
            key="408-2019-q41-reorder-linked-list",
            year=2019,
            question="41",
            title="首尾交替重排链表",
            body=r"""线性表 $L=(a_1,a_2,\ldots,a_n)$ 使用带头结点的单链表存储。重新排列各结点，得到

$$L'=(a_1,a_n,a_2,a_{n-1},a_3,a_{n-2},\ldots)$$

输出重排后的数据序列。""",
            input_format=r"""第一行包含 $n$。第二行包含 $n$ 个整数；当 $n=0$ 时该行可以省略。""",
            output_format=r"""输出首尾交替重排后的序列。空链表输出为空。""",
            constraints=r"""- $0 \le n \le 200000$
- 数据在 32 位有符号整数范围内""",
            tags=("408真题", "链表", "双指针", "链表反转"),
            build_cases=_reorder_cases,
        ),
        ProblemDefinition(
            key="408-2020-q41-min-triple-distance",
            year=2020,
            question="41",
            title="三个升序集合的最小三元组距离",
            body=r"""定义三元组 $(a,b,c)$ 的距离为

$$D=|a-b|+|b-c|+|c-a|$$

给定三个非空整数集合，分别按非降序存储在数组 $S_1,S_2,S_3$ 中。每个集合各取一个数，求所有三元组中的最小距离。""",
            input_format=r"""第一行包含 $n_1,n_2,n_3$。接下来三行分别包含三个升序数组。""",
            output_format=r"""输出最小距离。""",
            constraints=r"""- $1 \le n_1,n_2,n_3 \le 200000$
- 元素在 32 位有符号整数范围内
- 答案使用 64 位整数""",
            tags=("408真题", "顺序表", "双指针", "贪心"),
            build_cases=_triple_cases,
        ),
        ProblemDefinition(
            key="408-2020-q42-prefix-code",
            year=2020,
            question="42",
            title="前缀编码判定与译码",
            body=r"""若任一字符的编码都不是其他字符编码的前缀，则该编码表具有前缀特性。

给定字符到 01 串的编码表以及一个待译码比特串：若编码表不具有前缀特性，或比特串无法被完整译码，输出 `INVALID`；否则输出唯一译文。""",
            input_format=r"""第一行包含字符数 $n$。随后 $n$ 行每行包含一个非空白字符和它的非空 01 编码。最后一行包含待译码的非空 01 串。""",
            output_format=r"""输出译码结果，或 `INVALID`。""",
            constraints=r"""- $2 \le n \le 256$
- 单个编码长度不超过 200
- 待译码串长度不超过 1000000""",
            tags=("408真题", "树", "字典树", "哈夫曼编码"),
            build_cases=_prefix_cases,
            adaptation="原题要求说明适用的数据结构、译码过程和前缀性判定；这里合并为可执行的判定与译码任务。",
        ),
        ProblemDefinition(
            key="408-2021-q41-euler-trail-exists",
            year=2021,
            question="41",
            title="EL 路径存在性",
            body=r"""无向图中的 EL 路径是恰好经过每条边一次的路径，也称欧拉通路。

给定一个至少含一条边的无向简单图，判断是否存在 EL 路径。与原题的连通图条件相比，本题输入还可能含孤立点或多个非零度连通分量，因此需要完整检查非零度顶点的连通性。""",
            input_format=r"""第一行包含 $n,m$。随后 $m$ 行每行包含一条无向边的两个端点 $u,v$。""",
            output_format=r"""存在 EL 路径时输出 `1`，否则输出 `0`。""",
            constraints=r"""- $2 \le n \le 2000$
- $1 \le m \le 20000$
- 图没有自环和重边""",
            tags=("408真题", "图", "欧拉路径", "深度优先搜索"),
            build_cases=_euler_cases,
            adaptation="原题使用邻接矩阵存储固定规模的无向图；这里改用边表输入以支持独立大规模测试，并补充非零度连通性判定。",
        ),
        ProblemDefinition(
            key="408-2021-q42-stable-comparison-count-sort",
            year=2021,
            question="42",
            title="稳定的比较计数排序",
            body=r"""每条记录由排序关键字 `key` 和唯一标识 `id` 组成。请按 `key` 非降序排序；关键字相等的记录必须保持输入时的相对顺序。

原题给出比较计数排序代码并要求判断、修正其稳定性。本题使用记录标识直接检验稳定输出。""",
            input_format=r"""第一行包含记录数 $n$。随后 $n$ 行每行包含 `key id`，所有 `id` 互不相同。""",
            output_format=r"""输出排序后的 $n$ 条记录，每行仍为 `key id`。""",
            constraints=r"""- $1 \le n \le 5000$
- `key` 和 `id` 均在 32 位有符号整数范围内""",
            tags=("408真题", "排序", "稳定性"),
            build_cases=_stable_sort_cases,
            adaptation="原题侧重分析给定程序；这里用带标识记录将“稳定”转化为可自动检查的行为。",
        ),
        ProblemDefinition(
            key="408-2022-q41-array-bst-validation",
            year=2022,
            question="41",
            title="顺序存储二叉树判定 BST",
            body=r"""一棵非空二叉树按完全二叉树位置顺序存入数组：下标从 $0$ 开始时，结点 $i$ 的左右孩子位置分别为 $2i+1$ 和 $2i+2$，不存在的结点用 `-1` 表示；实际结点值均为正整数。

判断这棵树是否为关键字互不相同的二叉搜索树。""",
            input_format=r"""第一行包含数组长度 `ElemNum`。第二行包含 `ElemNum` 个整数，依次为顺序存储数组。输入保证不存在“父位置为空但后代位置非空”的情况。""",
            output_format=r"""是二叉搜索树时输出 `1`，否则输出 `0`。""",
            constraints=r"""- $1 \le ElemNum \le 200000$
- 非空结点值为 $1$ 到 $10^9$""",
            tags=("408真题", "树", "二叉搜索树", "中序遍历"),
            build_cases=_bst_array_cases,
        ),
        ProblemDefinition(
            key="408-2022-q42-smallest-ten",
            year=2022,
            question="42",
            title="查找数组中最小的十个数",
            body=r"""给定一个很大的整数数组，找出其中最小的十个数。重复值分别计数。

为了使答案唯一，将这十个数按非降序输出。""",
            input_format=r"""第一行包含 $n$。第二行包含 $n$ 个整数。""",
            output_format=r"""输出最小的十个数，按非降序排列。""",
            constraints=r"""- $10 \le n \le 1000000$
- 数组元素在 32 位有符号整数范围内""",
            tags=("408真题", "顺序表", "堆", "快速选择"),
            build_cases=_smallest_ten_cases,
            time_limit_ms=2000,
            adaptation="原题要求为 $n>100000$ 的数组设计平均比较次数尽可能少的算法；这里补充唯一的排序输出约定。",
        ),
        ProblemDefinition(
            key="408-2023-q41-k-vertices",
            year=2023,
            question="41",
            title="有向图中的 K 顶点",
            body=r"""将有向图中出度严格大于入度的顶点称为 K 顶点。图以邻接矩阵存储。输出图中全部 K 顶点，并返回其个数。

本题用从 $1$ 开始的整数编号代替原题顶点字符。""",
            input_format=r"""第一行包含顶点数 $n$。随后 $n$ 行每行包含 $n$ 个 `0` 或 `1`，给出有向图的邻接矩阵；主对角线允许为 `1`。""",
            output_format=r"""第一行输出 K 顶点个数 $k$。若 $k>0$，第二行按编号升序输出所有 K 顶点；若 $k=0$，不输出第二行。""",
            constraints=r"""- $1 \le n \le 2000$
- 矩阵元素只能是 `0` 或 `1`""",
            tags=("408真题", "图", "邻接矩阵", "度"),
            build_cases=_k_vertices_cases,
        ),
        ProblemDefinition(
            key="408-2023-q42-replacement-selection-runs",
            year=2023,
            question="42",
            title="置换选择生成初始归并段",
            body=r"""对记录文件进行外部排序，使用容量为 $m$ 的工作区执行置换选择算法生成初始归并段。

先读入至多 $m$ 个记录。每次输出当前未冻结记录中的最小值，并读入一个新记录：若新值不小于刚输出的值，则加入当前归并段候选；否则冻结到下一归并段。当前候选为空时结束本段，解冻所有记录并继续。""",
            input_format=r"""第一行包含记录数 $n$ 和工作区容量 $m$。第二行按文件顺序给出 $n$ 个整数关键字。""",
            output_format=r"""第一行输出归并段数 $r$。随后 $r$ 行，每行先输出该段长度，再输出该段中的关键字序列。""",
            constraints=r"""- $1 \le n \le 200000$
- $1 \le m \le 10000$
- 关键字在 32 位有符号整数范围内""",
            tags=("408真题", "排序", "外部排序", "堆"),
            build_cases=_replacement_cases,
            adaptation="原题在固定 19 个记录上手工生成归并段；这里严格定义算法过程并推广到任意记录序列。",
        ),
        ProblemDefinition(
            key="408-2024-q41-unique-topological-order",
            year=2024,
            question="41",
            title="唯一拓扑序列判定",
            body=r"""给定一个非空有向图，判断它是否存在唯一的拓扑序列。

若图中有环，则不存在拓扑序列，也应输出 `0`。""",
            input_format=r"""第一行包含 $n,m$。随后 $m$ 行每行包含一条有向边 $u,v$。输入不含重边。""",
            output_format=r"""拓扑序列存在且唯一时输出 `1`，否则输出 `0`。""",
            constraints=r"""- $1 \le n \le 200000$
- $0 \le m \le 500000$""",
            tags=("408真题", "图", "拓扑排序", "队列"),
            build_cases=_topological_cases,
            time_limit_ms=2000,
            adaptation="原题使用邻接矩阵讨论拓扑序列唯一性；这里改用边表输入，以便构造大规模有向图测试。",
        ),
        ProblemDefinition(
            key="408-2024-q42-quadratic-probing",
            year=2024,
            question="42",
            title="平方探测散列表模拟",
            body=r"""将互不相同的非负关键字依次插入长度为 $m$ 的散列表，散列函数为

$$H_0=(key\times c)\bmod m,$$

冲突时第 $k$ 次探测地址为 $H_k=(H_0+k^2)\bmod m$。插入和查询都最多探测 $m$ 次；即使表中仍有空槽，探测序列未到达空槽时也可能失败。

构造散列表，并给出每个查询实际访问的地址序列。""",
            input_format=r"""第一行包含 $m,c,n,q$。第二行包含 $n$ 个待插入关键字，第三行包含 $q$ 个查询关键字。""",
            output_format=r"""第一行输出最终散列表，空槽输出 `_`。

随后每个查询输出一行：先输出实际探测次数 $r$，再输出 $r$ 个地址，最后输出 `1` 表示找到或 `0` 表示未找到。遇到目标、空槽或完成 $m$ 次探测时停止。""",
            constraints=r"""- $2 \le m \le 2000$
- $1 \le n < m$
- $1 \le q \le 2000$
- 关键字非负且插入关键字互不相同""",
            tags=("408真题", "查找", "哈希表"),
            build_cases=_quadratic_cases,
            adaptation="原题使用固定表长、关键字和查询；这里将参数一般化，并明确有限探测规则以得到唯一结果。",
        ),
        ProblemDefinition(
            key="408-2025-q41-suffix-max-product",
            year=2025,
            question="41",
            title="后缀范围最大乘积",
            body=r"""给定长度为 $n$ 的整数数组 $A$。对每个下标 $i$，计算

$$res_i=\max_{i\le j<n}(A_i\times A_j)$$

输出数组 $res$。""",
            input_format=r"""第一行包含 $n$。第二行包含 $n$ 个整数。""",
            output_format=r"""输出 $n$ 个 64 位整数 $res_0,res_1,\ldots,res_{n-1}$。""",
            constraints=r"""- $1 \le n \le 200000$
- $-10^9 \le A_i \le 10^9$""",
            tags=("408真题", "顺序表", "后缀最值", "动态规划"),
            build_cases=_suffix_product_cases,
        ),
        ProblemDefinition(
            key="408-2025-q42-aoe-critical-activities",
            year=2025,
            question="42",
            title="AOE 网工期与关键活动",
            body=r"""给定一个单源单汇 AOE 网，每条有向边代表一项活动，边权为持续时间，活动编号按输入顺序从 $1$ 开始。

求工程最短完工时间、全部关键活动，以及每项活动的总时差。活动 $(u,v,w)$ 的总时差定义为其最迟开始时间与最早开始时间之差。""",
            input_format=r"""第一行包含事件顶点数 $n$ 和活动数 $m$。随后 $m$ 行按活动编号顺序给出 $u,v,w$。

输入保证 $u<v$，顶点 $1$ 是唯一源点，顶点 $n$ 是唯一汇点，每个顶点均位于从源到汇的路径上。""",
            output_format=r"""第一行输出最短完工时间。

第二行先输出关键活动数量，再按编号升序输出全部关键活动编号。

第三行按活动编号输出 $m$ 个总时差。""",
            constraints=r"""- $2 \le n \le 2000$
- $1 \le m \le 20000$
- $1 \le w \le 10^9$
- 所有结果在 64 位有符号整数范围内""",
            tags=("408真题", "图", "关键路径", "拓扑排序"),
            build_cases=_aoe_cases,
            adaptation="原题围绕固定 AOE 图询问关键活动、并行活动和延期补救；这里保留可唯一判定的工期、关键活动和总时差核心。",
        ),
    ]
    by_key = {definition.key: definition for definition in candidates}
    if len(by_key) != len(candidates):
        raise ValueError("duplicate question-bank candidate key")
    missing = set(ALGORITHM_KEYS) - set(by_key)
    if missing:
        raise ValueError(f"algorithm question definitions are missing: {sorted(missing)}")
    return [by_key[key] for key in ALGORITHM_KEYS]


def build_question_bank() -> tuple[QuestionBankProblem, ...]:
    problems: list[QuestionBankProblem] = []
    seen: set[str] = set()
    for definition in _definitions():
        if definition.key in seen:
            raise ValueError(f"duplicate question-bank key: {definition.key}")
        seen.add(definition.key)
        rng = random.Random(f"local-408-oj:{definition.key}:v{BANK_VERSION}")
        cases = tuple(definition.build_cases(rng))
        if not cases:
            raise ValueError(f"question has no generated cases: {definition.key}")
        if len({item.name for item in cases}) != len(cases):
            raise ValueError(f"question has duplicate case names: {definition.key}")
        title = f"408-{definition.year} {definition.title}"
        problems.append(
            QuestionBankProblem(
                key=definition.key,
                year=definition.year,
                title=title,
                description=_statement(definition, cases[0]),
                tags=definition.tags,
                time_limit_ms=definition.time_limit_ms,
                memory_limit_mb=definition.memory_limit_mb,
                cases=cases,
            )
        )
    return tuple(problems)
