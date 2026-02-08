import sys
from typing import List, Dict, Tuple
import re

import panflute as pf

from . import utils


logger = utils.get_logger()


class TableCrossRef():
    def __init__(self, config: Dict, enable_link: bool) -> None:
        """コンストラクタ

        Args:
            config (dict):
                設定
                - table_number_count_level (int):
                    表番号の連番のカウントをするレベル
                    例えば0なら、ドキュメント全体で連番をカウントする
                    例えば1なら、第一階層である章ごとにカウントする
                    負の値なら、常に一番深い階層ごとにカウントする
                - table_title_template (str):
                    表番号のタイトルのテンプレート
                - delimiter (str):
                    表番号の区切り
            enable_link (bool):
                参照にリンクを張るかどうか
        """
        self.table_number_count_level = int(
            config.get("table_number_count_level", "0"))
        self.table_title_template: str = \
            config.get("table_title_template", "[表%s]")
        self.delimiter: str = \
            config.get("delimiter", "-")
        self.enable_link: bool = enable_link

        # 参照用の表番号を格納する辞書
        self.references: Dict = {}
        # 参照用の表のタイトルを格納する辞書
        self.references_title: Dict = {}
        # 書き換えるべき項目を記憶する(最後に書き換える)
        self.list_replace_target: List[Dict] = []
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
        root_elem = utils.get_root_elem(elem)
        if not isinstance(root_elem, pf.Table):
            return

        # キャプションのテキスト情報と表定義の取得
        caption_text = pf.stringify(elem.content)
        if not caption_text:  # キャプションが無ければ何もしない
            return
        identifier, width, new_caption_text = self._get_table_identifier(caption_text)
        # 参照と width が定義されていなければ何もしない
        if identifier is None and not width:
            return

        if self.enable_link and identifier:
            # 親のTable要素に参照元(identifier)を設定する
            root_elem.identifier = identifier

        # width指定があればクラスに追加
        if width:
            if not hasattr(root_elem, 'classes'):
                root_elem.classes = []
            elif isinstance(root_elem.classes, str):
                root_elem.classes = [root_elem.classes]
            root_elem.classes.append(f'width="{width}"')
            # キャプション文字列を更新（width部分を削除）
            self._set_caption_text(elem, new_caption_text)

        # identifier がない場合は表番号処理をスキップ
        if identifier is None:
            return

        # 表番号の取得
        table_number = self._get_table_number(list_present_section_numbers)

        # identifierの登録
        self._add_table_ref(identifier, table_number, new_caption_text)

        # キャプションに表番号を追加する
        new_caption_text = \
            self.table_title_template % table_number + " " + new_caption_text
        self._set_caption_text(elem, new_caption_text)

    def _get_table_identifier(self,
                              caption_text: str) -> Tuple[None | str, str, str]:
        """表定義を取得する関数

        Args:
            caption_text (str):
                キャプションのテキスト情報

        Returns:
            None or str:
                表定義
            str:
                width情報（指定されていなければ空文字列）
            str:
                表定義を削除したあとのテキスト情報
        """
        # 正規表現でパターンを抽出
        # {#tbl:XXX}, {#tbl:XXX .width="20,80"}, {.width="20,80"} に対応
        pattern = r"\{(?:#(tbl:[^\s\}]+))?(?:\s*\.width=\"([^\"]+)\")?\}"
        matches = re.findall(pattern, caption_text)

        if matches:
            # 複数見つかった場合は最後の1だけにする
            identifier, width = matches[-1]
            # 少なくともidentifierまたはwidthのどちらかがあるかを確認
            if not identifier and not width:
                return None, "", caption_text
            # 表定義の削除
            new_caption_text = re.sub(pattern, "", caption_text).strip()
            return identifier if identifier else None, width, new_caption_text
        else:
            return None, "", caption_text

    def _add_table_ref(self,
                       identifier: str,
                       table_number: str,
                       table_title: str) -> None:
        """表参照の追加

        Args:
            identifier (str):
                表ID
            ftable_number (str):
                表番号
            table_title (str):
                表のタイトル
        """
        # 重複登録はエラーで落とす
        if identifier in self.references:
            logger.error(f"Duplicate identifier: '{identifier}'")
            sys.exit(1)

        # 登録
        self.references[identifier] = table_number

        # タイトルも登録
        self.references_title[identifier] = table_title

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
        if self.table_number_count_level >= 0 and \
           len(list_present_section_numbers) > self.table_number_count_level:
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
                      key: str) -> pf.Str | pf.Link:
        """参照を上書きするべき対象を一時的に記憶しておく

        Args:
            key (str): 参照の目印となるキー

        Returns:
            pf.Str | pf.Link:
                参照追加後の要素
        """
        key, is_add_title = utils.split_key_title(key)
        target = pf.Str("")
        self.list_replace_target.append({
            "key": key,
            "target": target,
            "add_title": is_add_title
        })

        if self.enable_link:
            # 参照先へのリンクを張る
            return pf.Link(target, url=f"#{key}")
        else:
            return target

    def replace_reference(self) -> None:
        """参照の上書き"""
        for replace_target in self.list_replace_target:
            replace_target["target"].text = self.get_reference_string(
                replace_target["key"], replace_target["add_title"])

    def get_reference_string(self, key: str, add_title: bool) -> str:
        """参照キーから、表番号の文字列を返す

        Args:
            key (str):
                参照キー
            add_title (bool):
                タイトルを追加するかどうか

        Returns:
            str:
                セクション番号の文字列
        """
        # 参照キーが見つからない
        if key not in self.references:
            logger.error(f"No such reference: '{key}'.")
            sys.exit(1)
        table_number = self.table_title_template % self.references[key]

        if add_title is True:
            table_title = self.references_title[key]
            if table_title != "":
                table_number += " " + table_title

        return table_number
