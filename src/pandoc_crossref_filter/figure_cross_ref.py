import sys
from typing import List, Dict

import panflute as pf

from . import utils


logger = utils.get_logger()


class FigureCrossRef():
    def __init__(self, config: Dict) -> None:
        """コンストラクタ

        Args:
            config (dict):
                設定
                - figure_number_count_level (int):
                    図番号の連番のカウントをするレベル
                    例えば0なら、ドキュメント全体で連番をカウントする
                    例えば1なら、第一階層である章ごとにカウントする
                    負の値なら、常に一番深い階層ごとにカウントする

                - figure_title_template (str):
                    図番号のタイトルのテンプレート
                - delimiter (str):
                    図番号の区切り
        """
        self.figure_number_count_level: int = int(
            config.get("figure_number_count_level", "0"))
        self.figure_title_template: str = \
            config.get("figure_title_template", "[図%s]")
        self.delimiter: str = \
            config.get("delimiter", "-")

        # 参照用のセクション番号を格納する辞書
        self.references: Dict = {}
        # 書き換えるべき項目を記憶する(最後に書き換える)
        self.list_replace_target: List[Dict] = []
        # 図番号の連番をカウントする辞書
        self.dict_fig_number_increment: Dict = {}

    def register_figure(self,
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
        root_elem = utils.get_root_elem(elem)
        if isinstance(root_elem, pf.DefinitionList):
            logger.error(f"Duplicate definition: '{elem.identifier}'")
            sys.exit(1)

        # 親要素にFigureが存在する場合は、子のImageでは何もしない
        # (キャプションに何も設定しないと、FigureではなくImageになる)
        if isinstance(elem, pf.Image) and \
           isinstance(root_elem, pf.Figure):
            return elem

        # 図番号の取得
        fig_number = self._get_figure_number(list_present_section_numbers)

        # identifierの登録
        self._add_figure_identifier(elem.identifier, fig_number)

        # キャプションを追加する
        caption = self.figure_title_template % fig_number
        if isinstance(elem, pf.Figure):
            caption = caption + " " + self._get_caption(elem)
            caption = pf.Definition(pf.Para(pf.Str(caption)))
            image = elem.content[0].content[0]
            return [pf.DefinitionList(pf.DefinitionItem([image], [caption]))]
        else:
            if len(elem.content) > 0:
                caption += " " + elem.content[0].text
            caption = pf.Str(caption)
            image = elem
            return [image, pf.Str("\n\n: "), caption]

    def _get_caption(self, elem: pf.Figure) -> str:
        """キャプションの取得

        指定されたFigure要素からキャプションテキストを取得する。
        Args:
            elem (pf.Figure): キャプションを含むFigure要素。
        Returns:
            str: キャプションのテキスト。
        """
        list_text = []
        for c in elem.caption.content[0].content:
            if isinstance(c, pf.Space):
                list_text.append(" ")
            else:
                list_text.append(c.text)
        return "".join(list_text)

    def register_external_caption(self,
                                  caption: pf.Para,
                                  identifier: str,
                                  list_present_section_numbers: List) -> None:
        """外部のキャプションの登録

        Markdown Preview EnhancedでPlantUMLのプレビューを実行するときに使用する

        Args:
            caption: pf.Para
                キャプションを表す文章
            identifier: str:
                ID
            list_present_section_numbers: List:
                セクション番号
        """
        # 図番号の取得
        fig_number = self._get_figure_number(list_present_section_numbers)

        # identifierの登録
        self._add_figure_identifier(identifier, fig_number)

        # キャプションに図番号を追加する
        caption_text = self.figure_title_template % fig_number
        caption.content[0].text = caption_text

    def _add_figure_identifier(self,
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

    def _get_figure_number(self,
                           list_present_section_numbers: List[int]) -> str:
        """図番号の取得

        Args:
            list_present_section_numbers (list):
                セクション番号の配列

        Returns:
            str: 図番号を返します。
        """
        # カウントを開始するレベルの調整
        if self.figure_number_count_level >= 0 and \
           len(list_present_section_numbers) > self.figure_number_count_level:
            list_present_section_numbers = \
                list_present_section_numbers[:self.figure_number_count_level]
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
        fig_number = self.figure_title_template % self.references[key]
        return fig_number
