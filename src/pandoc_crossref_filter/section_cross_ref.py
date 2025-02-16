import sys
from typing import List, Dict

import panflute as pf

from . import utils


logger = utils.get_logger()


class SectionCrossRef():
    def __init__(self, config: Dict) -> None:
        """コンストラクタ

        Args:
            config (dict):
                設定
                - auto_section (bool):
                    セクション番号を自動付与するかどうか
                - start_header_level (int):
                    セクション番号のカウントを開始するヘッダーレベル
                - section_title_template (list(str)):
                    セクション番号のタイトルのテンプレート。レベルに応じて配列で設定できる
                - delimiter (str):
                    セクション番号の区切り
                - section_ref_template (list(str)):
                    セクション番号の参照のテンプレート。レベルに応じて配列で設定できる
        """
        self.auto_section: bool = bool(
            config.get("auto_section", False))
        self.start_header_level: int = min(1, int(
            config.get("start_header_level", "1")))
        self.section_title_template: List[str] = \
            config.get("section_title_template", ["%s."])
        self.delimiter: str = \
            config.get("delimiter", ".")
        self.section_ref_template: List[str] = \
            config.get("section_ref_template", ["第%s章", "%s節", "%s項", "%s目"])
        logger.error("%sです", self.section_title_template)

        # 現在のセクション番号
        self.list_present_section_numbers: List[int] = []
        # 参照用のセクション番号を格納する辞書
        self.references: Dict = {}
        # 書き換えるべき項目を記憶する(最後に書き換える)
        self.list_replace_target: List[Dict] = []

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
        section_number_str = self._get_section_number_str()
        # 元のヘッダー内容の前にセクション番号を追加
        if self.auto_section:
            self._insert_section_numbers(elem.content, section_number_str)
        # セクション参照の追加
        self._add_section_identifier(elem.identifier, section_number_str)

    def _is_unnumbered(self, classes: List[str]) -> bool:
        """セクション番号を加算しないヘッダーであるか判定する

        Args:
            classes (list(str)):
                ヘッダーのクラス

        Returns:
            bool: trueの場合、このヘッダーは番号を加算しない
        """
        if "un" in classes or "unnumbered" in classes:
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
                                section_number_str: str) -> None:
        """元のヘッダー内容の前にセクション番号を追加する
        """
        section_str = self._get_section_str(
            section_number_str, self.section_title_template) + " "
        content.insert(0, pf.Str(section_str))

    def _add_section_identifier(self,
                                identifier: str,
                                section_number_str: str) -> None:
        """セクション参照の追加

        Args:
            identifier (str):
                ヘッダーのID
            section_number_str (str):
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
        self.references[identifier] = section_number_str

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

        section_number_str = self.references[key]
        # ヘッダー内の引用なら、セクション番号をそのまま返す
        if is_header is True:
            return section_number_str

        return self._get_section_str(
            section_number_str, self.section_ref_template)

    def _get_section_str(self,
                         section_number_str: str,
                         section_template: List[str]) -> str:
        """セクション番号の文字列を返す

        Args:
            section_number_str (str):
                セクション番号
            section_template (list(str)):
                セクション文字列のテンプレート

        Returns:
            str: セクション文字列
        """
        level = min(
            len(section_template) - 1,
            section_number_str.count(self.delimiter)
        )
        logger.error("%sです", section_template[level])
        return section_template[level] % section_number_str

    def get_present_section_numbers(self) -> List[int]:
        """現在のセクション番号を返す

        Returns:
            list(int): 現在のセクション番号
        """
        return self.list_present_section_numbers.copy()
