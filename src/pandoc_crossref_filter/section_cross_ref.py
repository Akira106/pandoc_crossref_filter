import sys
from typing import List, Dict

import panflute as pf

from . import utils
from .output_format import (
    DOCX,
    HTML,
    GFM,
)


logger = utils.get_logger()


class SectionCrossRef():
    def __init__(self, config: Dict, output_format: int) -> None:
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
            output_format (int):
                出力形式
        """
        self.auto_section: bool = bool(
            config.get("auto_section", False))
        self.start_header_level: int = max(1, int(
            config.get("start_header_level", "1")))
        self.section_title_template: List[str] = \
            config.get("section_title_template", ["%s."])
        self.delimiter: str = \
            config.get("delimiter", ".")
        self.section_ref_template: List[str] = \
            config.get("section_ref_template", ["第%s章", "%s節", "%s項", "%s目"])
        self.output_format: int = output_format
        self.enable_link = self.output_format in [DOCX, HTML, GFM]

        # 現在のセクション番号
        self.list_present_section_numbers: List[int] = []
        # 参照用のセクション番号を格納する辞書
        self.references: Dict = {}
        # 書き換えるべき項目を記憶する(最後に書き換える)
        self.list_replace_target: List[Dict] = []
        # GFMフォーマットで使用する、ヘッダーに挿入するHTML要素の辞書
        # キー：identifier、値：pf.RawHtml要素
        self.gfm_anchor_elements: Dict = {}

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
        # GFMフォーマットの場合、アンカータグをヘッダーの前に挿入
        if self.output_format == GFM:
            self._create_gfm_anchor(elem.identifier)

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

    def _create_gfm_anchor(self, identifier: str) -> None:
        """GFMフォーマット用のアンカータグを生成

        Args:
            identifier (str):
                ヘッダーのID
        """
        if not identifier.startswith("sec:"):
            return

        # アンカータグのHTML要素を生成
        anchor_html = f'<a id="{identifier}"></a>'
        anchor_element = pf.RawBlock(anchor_html, format='html')
        self.gfm_anchor_elements[identifier] = anchor_element

    def get_gfm_anchor(self, elem: pf.Header) -> pf.RawBlock | None:
        """GFMフォーマット用のアンカータグを取得

        Args:
            elem (pf.Header):
                ヘッダー要素

        Returns:
            pf.RawBlock | None:
                アンカータグ
        """
        if self.output_format != GFM:
            return None

        if elem.identifier in self.gfm_anchor_elements:
            anchor = self.gfm_anchor_elements[elem.identifier]
            return anchor

        return None

    def add_reference(self,
                      key: str,
                      is_header: bool) -> pf.Str | pf.Link:
        """参照を上書きするべき対象を一時的に記憶しておく

        Args:
            key (str): 参照の目印となるキー
            is_header (bool): 上書き対象がヘッダーかどうか

        Returns:
            pf.Str | pf.Link:
                参照追加後の要素
        """
        target = pf.Str("")
        self.list_replace_target.append({
            "key": key,
            "target": target,
            "is_header": is_header
        })

        # ヘッダー内の参照なら終了
        if is_header:
            return target

        if self.enable_link:
            # 参照先へのリンクを張る
            return pf.Link(target, url=f"#{key}")
        else:
            return target

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
        return section_template[level] % section_number_str

    def get_present_section_numbers(self) -> List[int]:
        """現在のセクション番号を返す

        Returns:
            list(int): 現在のセクション番号
        """
        return self.list_present_section_numbers.copy()
