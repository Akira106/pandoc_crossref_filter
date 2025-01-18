import sys
from typing import List, Dict

import panflute as pf

from . import crossref_utils


logger = crossref_utils.get_logger()


class SectionCrossRef():
    def __init__(self, config: Dict) -> None:
        """コンストラクタ

        Args:
            config (dict):
                設定
                - start_header_level: セクション番号のカウントを開始するヘッダーレベル
        """
        self.start_header_level: int = int(
            config.get("start_header_level", "1"))
        assert self.start_header_level >= 1

        # 現在のセクション番号
        self.list_present_section_numbers: List[int] = []
        # 参照用のセクション番号を格納する辞書
        self.references: Dict = {}
        # 書き換えるべき項目を記憶する(最後に書き換える)
        self.list_replace_target: List[Dict] = []
        # セクション番号の区切り文字
        self.delimiter: str = "."
        # セクション番号の末尾の区切り文字
        self.suffix: str = ". "

    def register_section(self, elem: pf.Header) -> None:
        """セクション番号の登録

        Args:
            elem: pf.Header:
                ヘッダー
        """
        # セクション番号カウントの除外
        if self._is_unnumbered(elem.classes):
            return

        # ヘッダーレベルが設定値未満なら何もしない
        if self.start_header_level > elem.level:
            return

        # セクション番号のインクリメント
        self._increment_section_numbers(elem.level)
        # セクション番号を文字列に変換
        str_section_number = self._get_section_number_str()
        # 元のヘッダー内容の前にセクション番号を追加
        self._insert_section_numbers(elem.content, str_section_number)
        # セクション参照の追加
        self._add_section_ref(elem.identifier, str_section_number)

    def _is_unnumbered(self, classes: List[str]) -> bool:
        """セクション番号を加算しないヘッダーであるか判定する

        Args:
            classes (list(str)):
                ヘッダーのクラス

        Returns:
            bool: trueの場合、このヘッダーは番号を加算しない
        """
        if "unnumbered" in classes:
            return True
        else:
            return False

    def _increment_section_numbers(self, header_level: int) -> None:
        """セクション番号のレベルをインクリメント

        Args:
            header_level (int):
                ヘッダーレベル
        """
        relative_header_level = header_level - (self.start_header_level - 1)
        # 必要に応じてセクション番号リストを拡張
        while len(self.list_present_section_numbers) < relative_header_level:
            self.list_present_section_numbers.append(0)

        # 現在のレベルをインクリメント
        self.list_present_section_numbers[relative_header_level - 1] += 1

        # 現在のレベルより下のセクション番号をリセット
        if len(self.list_present_section_numbers) > relative_header_level:
            self.list_present_section_numbers = \
                self.list_present_section_numbers[:relative_header_level]

    def _get_section_number_str(self) -> str:
        """現在のセクション番号を文字列で取得する

        Returns:
            str: 現在のセクション番号
        """
        # セクション番号を文字列として生成
        return self.delimiter.join(map(str, self.list_present_section_numbers))

    def _insert_section_numbers(self,
                                content: pf.containers.ListContainer,
                                str_section_number: str) -> None:
        """元のヘッダー内容の前にセクション番号を追加する
        """
        content.insert(0, pf.Str(str_section_number + self.suffix))

    def _add_section_ref(self,
                         identifier: str,
                         str_section_number: str) -> None:
        """セクション参照の追加

        Args:
            identifier (str):
                ヘッダーのID
            str_section_number (str):
                ヘッダーのセクション番号
        """
        # ヘッダーに"#sec:"が無ければ終了
        if identifier.startswith("sec:") is False:
            return

        # 重複登録はエラーで落とす
        if identifier in self.references:
            logger.error(f"Duplicate identifier: '{identifier}'")
            sys.exit(1)

        # 登録
        self.references[identifier] = str_section_number

    def add_reference(self,
                      key: str,
                      target: pf.Str,
                      is_header: bool) -> None:
        """参照を上書きするべき対象を一時的に記憶しておく

        Args:
            key (str): 参照の目印となるキー
            target (pf.Str): 上書きするべき項目
            is_header (bool): 上書き対象がヘッダーかどうか
        """
        self.list_replace_target.append({
            "key": key,
            "target": target,
            "is_header": is_header
        })

    def replace_reference(self) -> None:
        """参照の上書き"""
        for replace_target in self.list_replace_target:
            replace_target["target"].text = self.get_reference_string(
                replace_target["key"], replace_target["is_header"])

    def get_reference_string(self, key: str, is_header: bool = False) -> str:
        """参照キーから、セクション番号の文字列を返す

        Args:
            key (str):
                参照キー
            is_header (bool):
                ヘッダーかどうか

        Returns:
            str:
                セクション番号の文字列
        """
        # 参照キーが見つからない
        if key not in self.references:
            logger.error(f"No such reference: '{key}'.")
            sys.exit(1)

        str_section_number = self.references[key]
        suffix = self._get_section_suffix(str_section_number, is_header)
        return str_section_number + suffix

    def _get_section_suffix(self,
                            str_section_number: str,
                            is_header: bool) -> str:
        """セクション番号のサフィックス

        Args:
            str_section_number (str):
                セクション番号
            is_header (bool):
                参照要素がヘッダーの中にあるかどうか

        Returns:
            str:
                サフィックス
        """
        # ヘッダーならサフィックスはつけない
        if is_header is True:
            return ""

        level = str_section_number.count(self.delimiter) + 1
        if level == 1:
            suffix = "章"
        elif level == 2:
            suffix = "節"
        elif level == 3:
            suffix = "項"
        else:
            suffix = "目"
        return suffix

    def get_present_section_numbers(self) -> List[int]:
        """現在のセクション番号を返す

        Returns:
            list(int): 現在のセクション番号
        """
        return self.list_present_section_numbers.copy()
