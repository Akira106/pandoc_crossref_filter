"""
pandocの出力形式の管理。
ここで列挙する形式は、クリックジャンプに対応します。
"""

DOCX = 1  # Word
HTML = 2  # Markdown Preview Enhanced のプレビュー画面
GFM = 3  # GitHub Flavored Markdown
OTHER = 4  # その他、クリックジャンプ未対応


def get_output_format(format_str: str) -> int:
    """
    出力形式の文字列から、対応する定数を返す。
    """
    if format_str == "docx":
        return DOCX
    elif format_str == "html":
        return HTML
    elif format_str == "gfm":
        return GFM
    else:
        return OTHER