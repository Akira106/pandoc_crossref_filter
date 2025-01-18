import sys
from typing import List, Dict

import panflute as pf

import crossref_utils


logger = crossref_utils.get_logger()


class ImageCrossRef():
    def __init__(self, config: Dict) -> None:
        """コンストラクタ

        Args:
            config (dict):
                設定
                - fig_number_count_level (int): 図番号の連番のカウントをするレベル
        """
        # 図番号の連番のカウントをするレベル
        # 例えば1なら章番号ごとにカウントする
        self.fig_number_count_level = int(
            config.get("fig_number_count_level", "1"))
        assert self.fig_number_count_level >= 0

        # 参照用のセクション番号を格納する辞書
        self.references: Dict = {}
        # 書き換えるべき項目を記憶する(最後に書き換える)
        self.list_replace_target: List[Dict] = []
        # 図番号のプレフィックス
        self.prefix = "[図"
        # 図番号の区切り
        self.delimiter: str = "-"
        # 図番号の末尾の区切り文字
        self.suffix: str = "]"
        # 図番号の連番をカウントする辞書
        self.dict_fig_number_increment: Dict = {}

    def register_image(self,
                       elem: pf.Image | pf.Figure,
                       list_present_section_numbers: List
                       ) -> pf.Element | List[pf.Element]:
        """図番号の登録

        Args:
            elem: pf.Image | pf.Figure:
                図要素
            list_present_section_numbers: List:
                セクション番号

        Returns:
            pf.Element | List[pf.Element]:
                Noneではない場合、キャプションを追加して要素を差し替えます。
        """
        # 参照が定義されていなければ何もしない
        if not elem.identifier.startswith("fig:"):
            return elem

        # DefinitionListがすでに定義されている場合は、記載が重複するのでエラーにする
        root_elem = crossref_utils.get_root_elem(elem)
        if isinstance(root_elem, pf.DefinitionList):
            logger.error(f"Duplicate definition: '{elem.identifier}'")
            sys.exit(1)

        # 親要素にFigureが存在する場合は、子のImageでは何もしない
        # (キャプションに何も設定しないと、FigureではなくImageになる)
        if isinstance(elem, pf.Image) and \
           isinstance(root_elem, pf.Figure):
            return elem

        # 図番号の取得
        fig_number = self._get_fig_number(list_present_section_numbers)

        # identifierの登録
        self._add_image_ref(elem.identifier, fig_number)
        # 不要になったidentifierの削除
        elem.identifier = ""

        # キャプションを追加する
        caption = self.prefix + fig_number + self.suffix
        if isinstance(elem, pf.Figure):
            caption += " " + elem.caption.content[0].content[0].text
            caption = pf.Definition(pf.Para(pf.Str(caption)))
            image = elem.content[0].content[0]
            return [pf.DefinitionList(pf.DefinitionItem([image], [caption]))]
        else:
            if len(elem.content) > 0:
                caption += " " + elem.content[0].text
            caption = pf.Str(caption)
            image = elem
            return [image, pf.Str("\n\n: "), caption]

    def _add_image_ref(self,
                       identifier: str,
                       fig_number: str) -> None:
        """図参照の追加

        Args:
            identifier (str):
                図のID
            fig_number (str):
                図番号
        """
        # 重複登録はエラーで落とす
        if identifier in self.references:
            logger.error(f"Duplicate identifier: '{identifier}'")
            sys.exit(1)

        # 登録
        self.references[identifier] = fig_number

    def _get_fig_number(self,
                        list_present_section_numbers: List[int]) -> str:
        """図番号の取得

        Args:
            list_present_section_numbers (list):
                セクション番号の配列

        Returns:
            str: 図番号を返します。
        """
        # カウントを開始するレベルの調整
        if len(list_present_section_numbers) > self.fig_number_count_level:
            list_present_section_numbers = \
                list_present_section_numbers[:self.fig_number_count_level]
        # 番号のカウント
        start_number = \
            self.delimiter.join(map(str, list_present_section_numbers))
        if start_number not in self.dict_fig_number_increment:
            self.dict_fig_number_increment[start_number] = 0
        self.dict_fig_number_increment[start_number] += 1

        if start_number != "":
            fig_number = \
                start_number + \
                self.delimiter + \
                str(self.dict_fig_number_increment[start_number])
        else:
            fig_number = str(self.dict_fig_number_increment[start_number])
        return fig_number

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
        """参照キーから、図番号の文字列を返す

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
        fig_number = self.prefix + self.references[key] + self.suffix
        return fig_number
