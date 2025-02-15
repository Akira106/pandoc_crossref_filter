import os
import subprocess
import sys
import re
import hashlib
from typing import List, Tuple, Dict
import json
import collections

import panflute as pf
import requests
import plantuml

from . import crossref_utils
from .section_cross_ref import SectionCrossRef
from .figure_cross_ref import FigureCrossRef
from .table_cross_ref import TableCrossRef
from .config import PLANTUML_SERVER_URL


logger = crossref_utils.get_logger()


class CodeBlockRef():

    def __init__(self, config: Dict):
        """コンストラクタ

        Args:
            config (dict): config設定
            - save_dir (str): PlantUMLの出力先
            - plantuml_jar_path (str): plantuml.jarのパス
        """
        # 画像の保存先
        self.save_dir: str = config.get("save_dir", "assets")

        # 書き換えるべき項目を記憶する(最後に書き換える)
        self.list_replace_target: List[Dict] = []
        # PlantUMLで出力するべきコードブロック
        self.list_puml: List[Dict] = []

    def register_code_block(self, elem: pf.CodeBlock) -> None | pf.Figure | List:
        """コードブロックの登録

        - コードブロックの参照を抽出して一時保存する
        - PlantUMLのコードブロックであった場合、pf.Figure要素に変換する

        Args:
            elem (pf.CodeBlock):
                コードブロック

        Returns:
            None | pf.Figure | List:
                PlantUMLをFigureに置き換えた要素
        """
        # 参照を抽出して一時記憶する
        replace_text, list_ref_key = self._extract_reference(elem.text)
        replace_target = {
            "elem": elem,
            "replace_text": replace_text,
            "list_ref_key": list_ref_key
        }
        self.list_replace_target.append(replace_target)

        # PlantUMLでなければ終了
        if self._is_puml(elem) is False:
            return

        # ファイル名、キャプション、IDを取得する
        filename, caption, identifier = \
            self._extract_filename_caption_identifier(elem.text)

        # Markdown Preview Enhancedでプレビューしている場合は、キャプションとIDを追加する
        if self._is_puml_when_MPE_preview(elem.attributes):
            # IDが定義されていなければ何もしない
            if identifier is None:
                return None

            fig_num = pf.Str("")  # figure_cross_refで書き換える
            caption = pf.Para(fig_num, pf.Space, pf.Str(caption))
            return [caption, identifier]

        # エキスポート時は画像で返す
        # (上位側でFigureCrossRefに登録する)
        else:
            # 出力先のディレクトリを追加
            filename = os.path.join(self.save_dir, filename)

            # 拡張子が無ければsvgにする
            if filename.endswith(".png") is False and \
               filename.endswith(".svg") is False:
                filename += ".svg"

            self.list_puml.append({
                "filename": filename,
                "elem": elem
            })

            caption = pf.Str(caption)
            image = pf.Image(caption, url=filename)
            figure = pf.Figure(
                pf.Plain(image),
                caption=pf.Caption(pf.Plain(caption)),
                identifier=identifier)
            return figure

    def _extract_reference(self, text: str) -> Tuple[str, List[str]]:
        """コードブロックから参照を抽出する関数

        Args:
            text (str):
                コードブロックのテキスト

        Returns:
            str:
                入力文字列について、参照する箇所を%sに置き換えた文字列
            list(str):
                参照のリスト
        """
        # 正規表現で[@XXX]の形式を抽出
        pattern = r"\[@(.*?)\]"
        matches = re.findall(pattern, text)  # "XXX"部分を抽出

        # "[@XXX]"を"%s"に置き換え
        replaced_text = re.sub(pattern, "%s", text)

        return replaced_text, matches

    @staticmethod
    def _extract_filename_caption_identifier(text: str) -> Tuple[str | None,
                                                                 str,
                                                                 str | None]:
        """PlantUMLのCodeBlockの中からファイル名、キャプション、IDを取得する

        PlantUMLのテキスト中に
        - 'filename=XX
        - 'caption=YY
        - '#fig:ZZ'
        が記載されているとき、XX, YY, fig:ZZを返します。

        Args:
            text (str):
                PlantUMLのテキスト

        Returns:
            str | None: PlantUMLで出力後のファイル名 = XX
            str: キャプション = YY
            str | None: ID = fig:ZZ
        """
        filename = None
        caption = ""
        fig = None

        match_filename = re.search(r"^'filename=(\S+)", text, re.MULTILINE)
        match_caption = re.search(r"^'caption=(.+)", text, re.MULTILINE)
        match_fig = re.search(r"^'#(fig:\S+)", text, re.MULTILINE)

        if match_filename:
            filename = match_filename.group(1).strip("'" + '"')
        if match_caption:
            caption = match_caption.group(1).strip("'" + '"')
        if match_fig:
            fig = match_fig.group(1)

        return filename, caption, fig

    def replace_reference(self,
                          section_cross_ref: SectionCrossRef,
                          figure_cross_ref: FigureCrossRef,
                          table_cross_ref: TableCrossRef) -> None:
        """参照を置き換える関数

        Args:
            section_cross_ref: SectionCrossRef
                セクション番号の参照
            figure_cross_ref: FigureCrossRef):
                図番号の参照
            table_cross_ref: TableCrossRef):
                表番号の参照
        """
        for replace_text in self.list_replace_target:
            # 参照キーから、置き換える文字列を取得する
            list_replace_value = []
            for key in replace_text["list_ref_key"]:
                if key.startswith("sec:"):
                    reference = section_cross_ref
                elif key.startswith("fig:"):
                    reference = figure_cross_ref
                elif key.startswith("tbl:"):
                    reference = table_cross_ref
                else:
                    logger.error(f"Unsupported reference: '{key}'.")
                    sys.exit(1)

                # 参照の取得
                value = reference.get_reference_string(key)
                list_replace_value.append(value)

            # コードブロック文字列の置き換え
            replace_text["elem"].text = \
                replace_text["replace_text"] % tuple(list_replace_value)

    @classmethod
    def _is_puml(cls, elem: pf.Element) -> bool:
        """コードブロックがPlantUMLかどうかを判定する

        通常のpandoc、または
        Markdown Preview Enhancedでexportするときの判定

        Args:
            elem (pf.Element): Pandocの要素

        Returns:
            判定結果
        """
        if cls._is_puml_when_export(elem.classes):
            return True
        if cls._is_puml_when_MPE_preview(elem.attributes):
            return True

        return False

    @staticmethod
    def _is_puml_when_export(classes: List[str]) -> bool:
        """コードブロックがPlantUMLかどうかを判定する

        通常のpandoc、または
        Markdown Preview Enhancedでexportするときの判定

        Args:
            classes (list(str)): 要素のクラス一覧

        Returns:
            判定結果
        """
        list_target = [
            "plantuml",
            "puml"
        ]
        return any([target in classes for target in list_target])

    @staticmethod
    def _is_puml_when_MPE_preview(attributes: Dict) -> bool:
        """コードブロックがPlantUMLかどうかを判定する

        Markdown Preview Enhancedでプレビューしている場合は判定方法が変わる

        Args:
            attributes (Dict): 要素の属性一覧

        Returns:
            判定結果
        """
        data_parsed_info = json.loads(attributes.get("data-parsed-info", "{}"))
        language = data_parsed_info.get("language")
        list_target = [
            "plantuml",
            "puml"
        ]
        return language in list_target

    @staticmethod
    def _has_ref(identifier: str) -> bool:
        """図の参照が設定されているかどうか判定する"""
        return identifier.startswith("fig:")

    @staticmethod
    def _md5(text: str) -> str:
        """文字列のMD5を取得する"""
        hash_object = hashlib.md5(text.encode())
        return hash_object.hexdigest()

    def export_puml_images(self) -> None:
        """PlantUML画像の出力"""
        # PlantUMLがなければ終了
        if len(self.list_puml) == 0:
            return

        # ディレクトリが無ければ作成
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir, exist_ok=True)

        # 出力ファイルの重複チェック
        self._assert_no_duplicate_filename(
            [puml["filename"] for puml in self.list_puml])

        # 画像に変換する
        for puml in self.list_puml:
            self._export_puml_image(puml["filename"], puml["elem"].text)

    @staticmethod
    def _assert_no_duplicate_filename(list_filename: List[str]) -> None:
        """出力ファイル名の重複チェック

        Args:
            list_filename (str):
                ファイル名の出力先
        """
        counter = collections.Counter(list_filename)
        duplicates = [item for item, count in counter.items() if count > 1]
        if len(duplicates) > 0:
            for dup in duplicates:
                logger.error(f"Duplicate filename: {dup}.")
            sys.exit(1)

    def _export_puml_image(self, filename: str, text: str) -> None:
        """PlantUMLのテキストを画像に出力する

        Args:
            filename (str): 出力先の画像ファイル名
            text (str): PlantUMLのテキスト
        """
        fmt = "svg" if filename.endswith(".svg") else "png"
        encode_text = plantuml.deflate_and_encode(text)
        url = PLANTUML_SERVER_URL + f"/{fmt}/{encode_text}"

        try:
            ret = requests.get(url)
        except Exception:
            logger.error(f"Failed to connect to {PLANTUML_SERVER_URL}.")
            sys.exit(1)
        if ret.status_code != 200:
            logger.error(f"Failed to export f{filename}.")
            sys.exit(1)

        with open(filename, "wb") as f:
            f.write(ret.content)
