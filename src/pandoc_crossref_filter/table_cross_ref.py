import sys
from typing import List, Dict, Tuple
import re

import panflute as pf

from . import utils


logger = utils.get_logger()


class TableCrossRef():
    def __init__(self, config: Dict) -> None:
        """コンストラクタ

        Args:
            config (dict):
                設定
                - table_number_count_level (int): 表番号の連番のカウントをするレベル
        """
        # 表番号の連番のカウントをするレベル
        # 例えば1なら章番号ごとにカウントする
        self.table_number_count_level = int(
            config.get("table_number_count_level", "1"))
        assert self.table_number_count_level >= 0

        # 参照用のセクション番号を格納する辞書
        self.references: Dict = {}
        # 書き換えるべき項目を記憶する(最後に書き換える)
        self.list_replace_target: List[Dict] = []
        # 表番号のプレフィックス
        self.prefix = "[表"
        # 表番号の区切り
        self.delimiter: str = "-"
        # 表番号の末尾の区切り文字
        self.suffix: str = "]"
        # 表番号の連番をカウントする辞書
        self.dict_table_number_increment: Dict = {}

    def register_table(self,
                       elem: pf.Caption,
                       list_present_section_numbers: List
                       ) -> None:
        """表番号の登録

        Args:
            elem: pf.Caption:
                表番号のキャプション
            list_present_section_numbers: List:
                セクション番号
        """
        # Table要素のキャプションでなければ終了
        if not isinstance(utils.get_root_elem(elem), pf.Table):
            return

        # キャプションのテキスト情報と表定義の取得
        caption_text = self._get_caption_text(elem)
        if caption_text is None:  # キャプションが無ければ何もしない
            return
        identifier, new_caption_text = self._get_table_identifier(caption_text)
        # 参照が定義されていなければ何もしない
        if identifier is None:
            return

        # 表番号の取得
        table_number = self._get_table_number(list_present_section_numbers)

        # identifierの登録
        self._add_table_ref(identifier, table_number)

        # キャプションに表番号を追加する
        new_caption_text = \
            self.prefix + table_number + self.suffix + " " + new_caption_text
        self._set_caption_text(elem, new_caption_text)

    def _get_caption_text(self, elem: pf.Caption) -> str | None:
        """キャプションのテキスト情報を取得する

        Args:
            elem (pf.Caption):
                キャプション要素

        Returns:
            str: テキスト情報
        """
        # キャプションが無ければ終了
        if len(elem.content) == 0:
            return None

        caption_text = ""
        for caption_elem in elem.content[0].content:
            if isinstance(caption_elem, pf.Space):
                caption_text += " "
            else:
                caption_text += caption_elem.text

        return caption_text

    def _get_table_identifier(self,
                              caption_text: str) -> Tuple[None | str, str]:
        """表定義を取得する関数

        Args:
            caption_text (str):
                キャプションのテキスト情報

        Returns:
            None or str:
                表定義
            str:
                表定義を削除したあとのテキスト情報
        """
        # 正規表現でパターンを抽出
        pattern = r"\{#(tbl:[^\}]+)\}"
        matches = re.findall(pattern, caption_text)

        if matches:
            # 表定義の削除
            new_caption_text = re.sub(pattern, "", caption_text).strip()
            # 複数見つかった場合は最後の1だけにする
            return matches[-1], new_caption_text
        else:
            return None, caption_text

    def _add_table_ref(self,
                       identifier: str,
                       table_number: str) -> None:
        """表参照の追加

        Args:
            identifier (str):
                表ID
            ftable_number (str):
                表番号
        """
        # 重複登録はエラーで落とす
        if identifier in self.references:
            logger.error(f"Duplicate identifier: '{identifier}'")
            sys.exit(1)

        # 登録
        self.references[identifier] = table_number

    def _get_table_number(self,
                          list_present_section_numbers: List[int]) -> str:
        """表番号の取得

        Args:
            list_present_section_numbers (list):
                セクション番号の配列

        Returns:
            str: 表番号を返します。
        """
        # カウントを開始するレベルの調整
        if len(list_present_section_numbers) > self.table_number_count_level:
            list_present_section_numbers = \
                list_present_section_numbers[:self.table_number_count_level]
        # 番号のカウント
        start_number = \
            self.delimiter.join(map(str, list_present_section_numbers))
        if start_number not in self.dict_table_number_increment:
            self.dict_table_number_increment[start_number] = 0
        self.dict_table_number_increment[start_number] += 1

        if start_number != "":
            table_number = \
                start_number + \
                self.delimiter + \
                str(self.dict_table_number_increment[start_number])
        else:
            table_number = str(self.dict_table_number_increment[start_number])
        return table_number

    def _set_caption_text(self, elem: pf.Caption, caption_text: str) -> None:
        """キャプションのテキスト情報を設定する

        Args:
            elem (pf.Caption):
                キャプション要素
            caption_text (str):
                設定するテキスト
        """
        elem.content[0].content = [pf.Str(caption_text)]

    def add_reference(self,
                      key: str,
                      target: pf.Str) -> None:
        """参照を上書きするべき対象を一時的に記憶しておく

        Args:
            key (str): 参照の目印となるキー
            target (pf.Str): 上書きするべき項目
        """
        self.list_replace_target.append({
            "key": key,
            "target": target,
        })

    def replace_reference(self) -> None:
        """参照の上書き"""
        for replace_target in self.list_replace_target:
            replace_target["target"].text = self.get_reference_string(
                replace_target["key"])

    def get_reference_string(self, key: str) -> str:
        """参照キーから、表番号の文字列を返す

        Args:
            key (str):
                参照キー

        Returns:
            str:
                セクション番号の文字列
        """
        # 参照キーが見つからない
        if key not in self.references:
            logger.error(f"No such reference: '{key}'.")
            sys.exit(1)
        table_number = self.prefix + self.references[key] + self.suffix
        return table_number
