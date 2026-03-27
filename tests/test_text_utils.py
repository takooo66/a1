"""text_utils の単体テスト。"""

import unittest

from src.text_utils import normalize_whitespace


class TestNormalizeWhitespace(unittest.TestCase):
    def test_multiple_spaces_are_collapsed(self) -> None:
        self.assertEqual(normalize_whitespace("a   b    c"), "a b c")

    def test_leading_and_trailing_spaces_are_trimmed(self) -> None:
        self.assertEqual(normalize_whitespace("   hello world   "), "hello world")

    def test_tabs_and_newlines_are_normalized(self) -> None:
        self.assertEqual(normalize_whitespace("hello\t\nworld"), "hello world")

    def test_empty_or_whitespace_only_returns_empty(self) -> None:
        self.assertEqual(normalize_whitespace("   \t  \n"), "")


if __name__ == "__main__":
    unittest.main()
