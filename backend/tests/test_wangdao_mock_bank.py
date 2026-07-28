from collections import Counter

from app.judge import MAX_OUTPUT_BYTES
from app.wangdao_mock_bank import (
    MOCK_ALGORITHM_KEYS,
    MOCK_BANK_VERSION,
    build_wangdao_mock_bank,
    mock_source_marker,
)


def test_wangdao_mock_bank_is_complete_and_deterministic():
    first = build_wangdao_mock_bank()
    second = build_wangdao_mock_bank()

    assert first == second
    assert len(first) == 8
    assert tuple(problem.key for problem in first) == MOCK_ALGORITHM_KEYS
    assert sum(len(problem.cases) for problem in first) == 114
    assert all("q42" in problem.key for problem in first)

    for volume, problem in enumerate(first, start=1):
        assert problem.year == 2026
        assert "王道模拟题" in problem.tags
        assert "2026王道八套卷" in problem.tags
        assert f"version:{MOCK_BANK_VERSION}" in problem.description
        assert mock_source_marker(problem.key) in problem.description
        assert "## 题目描述" in problem.description
        assert "## 输入格式" in problem.description
        assert "## 输出格式" in problem.description
        assert "## 输入输出样例 #1" in problem.description
        assert f"第 42 题" in problem.description
        assert len(problem.cases) >= 12
        assert len({case.name for case in problem.cases}) == len(problem.cases)
        assert all(case.input_data.endswith("\n") for case in problem.cases)
        assert all(case.output_data.endswith("\n") for case in problem.cases)
        assert all(len(case.input_data.encode("utf-8")) <= 2 * 1024 * 1024 for case in problem.cases)
        assert all(len(case.output_data.encode("utf-8")) <= MAX_OUTPUT_BYTES for case in problem.cases)


def _read_binary_tree(tokens, offset):
    n = int(tokens[offset])
    root = int(tokens[offset + 1])
    offset += 2
    children = [(0, 0)]
    for _ in range(n):
        children.append((int(tokens[offset]), int(tokens[offset + 1])))
        offset += 2
    return children, root, offset


def _height_and_balance(children, root):
    if root == 0:
        return 0, 1
    heights = [0] * len(children)
    balanced = 1
    stack = [(root, 0)]
    while stack:
        node, state = stack.pop()
        if state:
            left, right = children[node]
            balanced &= int(abs(heights[left] - heights[right]) <= 1)
            heights[node] = max(heights[left], heights[right]) + 1
        else:
            stack.append((node, 1))
            left, right = children[node]
            if left:
                stack.append((left, 0))
            if right:
                stack.append((right, 0))
    return heights[root], balanced


def _position_parity_output(values):
    values = values[:]
    odd_position, even_position = 0, 1
    while True:
        while odd_position < len(values) and values[odd_position] % 2:
            odd_position += 2
        while even_position < len(values) and values[even_position] % 2 == 0:
            even_position += 2
        if odd_position >= len(values) or even_position >= len(values):
            return " ".join(map(str, values))
        values[odd_position], values[even_position] = values[even_position], values[odd_position]


def _mirror_answer(first, first_root, second, second_root):
    pairs = [(first_root, second_root)]
    while pairs:
        one, two = pairs.pop()
        if not one or not two:
            if one != two:
                return "0"
            continue
        one_left, one_right = first[one]
        two_left, two_right = second[two]
        pairs.extend(((one_left, two_right), (one_right, two_left)))
    return "1"


def _expected_output(problem_key, input_data):
    tokens = input_data.split()
    if problem_key == MOCK_ALGORITHM_KEYS[0]:
        children, root, _ = _read_binary_tree(tokens, 0)
        return " ".join(map(str, _height_and_balance(children, root)))

    if problem_key == MOCK_ALGORITHM_KEYS[1]:
        n = int(tokens[0])
        return _position_parity_output(list(map(int, tokens[1 : n + 1])))

    if problem_key == MOCK_ALGORITHM_KEYS[2]:
        n = int(tokens[0])
        return str(min(map(int, tokens[1 : n + 1])))

    if problem_key == MOCK_ALGORITHM_KEYS[3]:
        first, first_root, offset = _read_binary_tree(tokens, 0)
        second, second_root, _ = _read_binary_tree(tokens, offset)
        return _mirror_answer(first, first_root, second, second_root)

    if problem_key == MOCK_ALGORITHM_KEYS[4]:
        n = int(tokens[0])
        values = list(map(int, tokens[1 : n + 1]))
        return " ".join(map(str, values[::2] + values[1::2]))

    if problem_key == MOCK_ALGORITHM_KEYS[5]:
        m = int(tokens[1])
        target = int(tokens[2])
        ends = (int(tokens[index + 1]) for index in range(3, 3 + 2 * m, 2))
        return str(sum(end == target for end in ends))

    if problem_key == MOCK_ALGORITHM_KEYS[6]:
        n = int(tokens[0])
        rows = [(0, 0)]
        offset = 2
        for _ in range(n):
            rows.append((int(tokens[offset]), int(tokens[offset + 1])))
            offset += 2
        degree = 0
        for node in range(1, n + 1):
            count = 0
            child = rows[node][0]
            while child:
                count += 1
                child = rows[child][1]
            degree = max(degree, count)
        return str(degree)

    if problem_key == MOCK_ALGORITHM_KEYS[7]:
        n = int(tokens[0])
        head = int(tokens[1])
        rows = [("", 0)]
        offset = 2
        for _ in range(n):
            rows.append((tokens[offset], int(tokens[offset + 1])))
            offset += 2
        values = []
        node = head
        while node:
            values.append(rows[node][0])
            node = rows[node][1]
        assert len(values) == n
        return str(int(values == list(reversed(values))))

    raise AssertionError(f"unexpected problem key: {problem_key}")


def test_all_generated_outputs_match_independent_readers():
    bank = build_wangdao_mock_bank()
    checked = Counter()
    for problem in bank:
        for case in problem.cases:
            assert case.output_data.strip() == _expected_output(problem.key, case.input_data)
            checked[problem.key] += 1
    assert checked == Counter({problem.key: len(problem.cases) for problem in bank})
