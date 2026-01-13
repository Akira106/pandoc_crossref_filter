import logging
import sys

import panflute as pf

# ロガーの名前
LOGGER_NAME = "crossref"


def set_logger(log_level):
    # フォーマット
    log_format = logging.Formatter("%(levelname)s: %(message)s")
    # 標準エラー出力(標準出力はpandocが使う)
    stderr_handler = logging.StreamHandler(stream=sys.stderr)
    stderr_handler.setLevel(log_level)
    stderr_handler.setFormatter(log_format)
    # 設定の適用
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(log_level)
    logger.addHandler(stderr_handler)


def get_logger():
    return logging.getLogger(LOGGER_NAME)


def get_root_elem(elem: pf.Element) -> pf.Element:
    """一番上の親要素を取得する

    Args:
        elem (pf.Element):
            要素

    Returns:
        pf.Element:
            一番上の親要素
    """
    while True:
        parent = elem.parent
        if isinstance(parent, pf.Doc) or parent is None:
            return elem
        else:
            elem = parent


def joinpath(path1: str, path2: str) -> str:
    """パスを結合する

    Args:
        path1 (str): パス1
        path2 (str): パス2

    Returns:
        str: path1/path2を返す
    """
    # path.join()だとOSごとに文字が変わってしまうので、直接"/"でjoinする
    # filename = os.path.join(path1, path2)
    delimiter = "/"
    if not path1.endswith(delimiter):
        path1 += delimiter
    return path1 + path2
