import logging
import sys

import const

import panflute as pf


def set_logger(log_level):
    # フォーマット
    log_format = logging.Formatter("%(levelname)s: %(message)s")
    # 標準エラー出力(標準出力はpandocが使う)
    stderr_handler = logging.StreamHandler(stream=sys.stderr)
    stderr_handler.setLevel(log_level)
    stderr_handler.setFormatter(log_format)
    # 設定の適用
    logger = logging.getLogger(const.LOGGER_NAME)
    logger.setLevel(log_level)
    logger.addHandler(stderr_handler)


def get_logger():
    return logging.getLogger(const.LOGGER_NAME)


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
