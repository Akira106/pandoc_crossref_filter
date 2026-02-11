from typing import Tuple, List, Dict
import json
import sys
import re

import panflute as pf
import asyncio

from . import utils

try:
    from mermaid_cli import render_mermaid
    ENABLE_MERMAID = True
except ImportError:
    ENABLE_MERMAID = False

logger = utils.get_logger()


class MermaidWrapper():
    def __init__(self):
        """コンストラクタ
        """
        # Mermaidで出力するべきコードブロック
        self.list_mmd: List[Dict] = []
        # MermaidWrapperがインストールされていないときの警告を1回だけだす
        self.reported_warning = False

    @staticmethod
    def extract_filename_caption_identifier(text: str) -> Tuple[str | None,
                                                                str,
                                                                str | None,
                                                                str | None]:
        """MermaidのCodeBlockの中からファイル名、キャプション、IDを取得する

        Mermaidのテキスト中に
        - %%filename=XX
        - %%caption=YY
        - %%#fig:ZZ'
        - %%width=AA
        が記載されているとき、XX, YY, fig:ZZを返します。

        Args:
            text (str):
                Mermaidのテキスト

        Returns:
            str | None: Mermaidで出力後のファイル名 = XX
            str: キャプション = YY
            str | None: ID = fig:ZZ
            str | None: 幅 = AA
        """
        filename = None
        caption = ""
        fig = None
        width = None

        match_filename = re.search(r"^%%filename=(\S+)", text, re.MULTILINE)
        match_caption = re.search(r"^%%caption=(.+)", text, re.MULTILINE)
        match_fig = re.search(r"^%%#(fig:\S+)", text, re.MULTILINE)
        match_width = re.search(r"^%%width=(\S+)", text, re.MULTILINE)

        if match_filename:
            filename = match_filename.group(1).strip("'" + '"')
        if match_caption:
            caption = match_caption.group(1).strip("'" + '"')
        if match_fig:
            fig = match_fig.group(1)
        if match_width:
            width = match_width.group(1).strip('"' + "'")

        return filename, caption, fig, width

    def is_image(self, elem: pf.Element) -> bool:
        """コードブロックがMermaidかどうかを判定する

        通常のpandoc、または
        Markdown Preview Enhancedでexportするときの判定

        Args:
            elem (pf.Element): Pandocの要素

        Returns:
            判定結果
        """
        if self._is_image_when_export(elem.classes) or \
           self.is_image_when_MPE_preview(elem.attributes):
            if ENABLE_MERMAID is False and self.reported_warning is False:
                logger.warning(
                    "mermaid is not installed in pandoc_crossref_filter")
                self.reported_warning = True
            return True

        return False

    @staticmethod
    def _is_image_when_export(classes: List[str]) -> bool:
        """コードブロックがMermaidかどうかを判定する

        通常のpandoc、または
        Markdown Preview Enhancedでexportするときの判定

        Args:
            classes (list(str)): 要素のクラス一覧

        Returns:
            判定結果
        """
        return "mermaid" in classes

    @staticmethod
    def is_image_when_MPE_preview(attributes: Dict) -> bool:
        """コードブロックがMermaidかどうかを判定する

        Markdown Preview Enhancedでプレビューしている場合は判定方法が変わる

        Args:
            attributes (Dict): 要素の属性一覧

        Returns:
            判定結果
        """
        data_parsed_info = json.loads(attributes.get("data-parsed-info", "{}"))
        language = data_parsed_info.get("language")
        return language == "mermaid"

    def add(self, filename: str, elem: pf.Element) -> None:
        """Mermaidに変換する対象を追加する

        Args:
            filename (str):
                出力ファイル名
            elem (pf.Element):
                panflute要素
        """
        self.list_mmd.append({
            "filename": filename,
            "elem": elem
        })

    def get_filenames(self) -> List[str]:
        """出力画像のファイル名を取得する

        Returns:
            list(str): 出力画像のファイル名の一覧
        """
        return [mmd["filename"] for mmd in self.list_mmd]

    def export_images(self) -> None:
        """Mermaid画像の出力"""
        # mermaid-cliがインストールされていなければ終了
        if ENABLE_MERMAID is False:
            return

        # 画像に変換する
        for mmd in self.list_mmd:
            asyncio.run(self._export_image(mmd["filename"], mmd["elem"].text))

    async def _export_image(self, filename: str, text: str) -> None:
        """Mermaidのテキストを画像に出力する

        Args:
            filename (str): 出力先の画像ファイル名
            text (str): Mermaidのテキスト
        """
        # エラーすることがあるのでリトライする
        for _ in range(2):
            try:
                _, _, svg_data = await render_mermaid(
                    text,
                    output_format=("svg" if filename.endswith(".svg") else "png"),
                    background_color="white",
                    mermaid_config={"theme": "forest"}
                )
                with open(filename, "wb") as f:
                    f.write(svg_data)
                return

            except Exception:
                pass

        logger.error(f"Failed to export {filename}.")
        sys.exit(1)
