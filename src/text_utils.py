"""文字列ユーティリティ実装。"""


def normalize_whitespace(text: str) -> str:
    """連続する空白を1つに正規化し、前後空白を削除する。"""
    parts = text.split()
    return " ".join(parts)
