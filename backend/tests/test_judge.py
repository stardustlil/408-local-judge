from app.judge import normalize_output


def test_normalize_output_ignores_line_endings_and_trailing_spaces():
    assert normalize_output("1 2 3  \r\n\r\n") == normalize_output("1 2 3\n")


def test_normalize_output_preserves_internal_whitespace():
    assert normalize_output("1  2\n") != normalize_output("1 2\n")

