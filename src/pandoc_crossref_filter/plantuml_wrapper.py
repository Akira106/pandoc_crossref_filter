from typing import Tuple, List, Dict
import json
import sys
import re

import requests
import panflute as pf
import plantuml

from . import utils
from .config import PLANTUML_SERVER_URL

logger = utils.get_logger()


class PlantUMLWrapper():
    def __init__(self):
        """コンストラクタ
        """
        # PlantUMLで出力するべきコードブロック
        self.list_puml: List[Dict] = []

    @staticmethod
    def extract_filename_caption_identifier(text: str) -> Tuple[str | None,
                                                                str,
                                                                str | None,
                                                                str | None]:
        """PlantUMLのCodeBlockの中からファイル名、キャプション、IDを取得する

        PlantUMLのテキスト中に
        - 'filename=XX
        - 'caption=YY
        - '#fig:ZZ'
        - 'width=AA
        が記載されているとき、XX, YY, fig:ZZ, AAを返します。

        Args:
            text (str):
                PlantUMLのテキスト

        Returns:
            str | None: PlantUMLで出力後のファイル名 = XX
            str: キャプション = YY
            str | None: ID = fig:ZZ
            str | None: 幅 = AA
        """
        filename = None
        caption = ""
        fig = None
        width = None

        match_filename = re.search(r"^'filename=(\S+)", text, re.MULTILINE)
        match_caption = re.search(r"^'caption=(.+)", text, re.MULTILINE)
        match_fig = re.search(r"^'#(fig:\S+)", text, re.MULTILINE)
        match_width = re.search(r"^'width=(\S+)", text, re.MULTILINE)

        if match_filename:
            filename = match_filename.group(1).strip("'" + '"')
        if match_caption:
            caption = match_caption.group(1).strip("'" + '"')
        if match_fig:
            fig = match_fig.group(1)
        if match_width:
            width = match_width.group(1).strip('"' + "'")

        return filename, caption, fig, width

    @classmethod
    def is_image(cls, elem: pf.Element) -> bool:
        """コードブロックがPlantUMLかどうかを判定する

        通常のpandoc、または
        Markdown Preview Enhancedでexportするときの判定

        Args:
            elem (pf.Element): Pandocの要素

        Returns:
            判定結果
        """
        if cls._is_image_when_export(elem.classes):
            return True
        if cls.is_image_when_MPE_preview(elem.attributes):
            return True

        return False

    @staticmethod
    def _is_image_when_export(classes: List[str]) -> bool:
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
    def is_image_when_MPE_preview(attributes: Dict) -> bool:
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

    def add(self, filename: str, elem: pf.Element) -> None:
        """PlantUMLに変換する対象を追加する

        Args:
            filename (str):
                出力ファイル名
            elem (pf.Element):
                panflute要素
        """
        self.list_puml.append({
            "filename": filename,
            "elem": elem
        })

    def get_filenames(self) -> List[str]:
        """出力画像のファイル名を取得する

        Returns:
            list(str): 出力画像のファイル名の一覧
        """
        return [puml["filename"] for puml in self.list_puml]

    def export_images(self) -> None:
        """PlantUML画像の出力"""
        # 画像に変換する
        for puml in self.list_puml:
            self._export_image(puml["filename"], puml["elem"].text)

    def _export_image(self, filename: str, text: str) -> None:
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
            logger.error(f"Failed to export {filename}.")
            sys.exit(1)

        with open(filename, "wb") as f:
            f.write(ret.content)
