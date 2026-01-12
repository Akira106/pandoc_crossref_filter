import os
import sys
import re
import hashlib
from typing import List, Tuple, Dict
import collections
import itertools

import panflute as pf

from . import utils
from .section_cross_ref import SectionCrossRef
from .figure_cross_ref import FigureCrossRef
from .table_cross_ref import TableCrossRef
from .plantuml_wrapper import PlantUMLWrapper
from .mermaid_wrapper import MermaidWrapper


logger = utils.get_logger()


class CodeBlockRef():

    def __init__(self, config: Dict):
        """コンストラクタ

        Args:
            config (dict): config設定
            - save_dir (str):
                PlantUML or Mermaid画像の出力先
        """
        self.save_dir: str = config.get("save_dir", "assets")

        # 書き換えるべき項目を記憶する(最後に書き換える)
        self.list_replace_target: List[Dict] = []

        # ラッパー
        self.list_wrapper = [
            PlantUMLWrapper(),
            MermaidWrapper()
        ]

    def register_code_block(self, elem: pf.CodeBlock) -> None | pf.Image | pf.Figure | List:
        """コードブロックの登録

        - コードブロックの参照を抽出して一時保存する
        - PlantUMLのコードブロックであった場合、pf.Figure要素に変換する

        Args:
            elem (pf.CodeBlock):
                コードブロック

        Returns:
            None | pf.Image | pf.Figure | List:
                PlantUMLをFigureに置き換えた要素
        """
        # 参照を抽出して一時記憶する
        replace_text, list_ref_key = self._extract_reference(elem.text)
        if len(list_ref_key) > 0:
            # 参照あり
            # %のエスケープは戻さなくてよい(参照適用時にpythonが勝手に戻す)
            self.list_replace_target.append({
                "elem": elem,
                "replace_text": replace_text,
                "list_ref_key": list_ref_key
            })

        # コードブロックを画像に変換する
        for wrapper in self.list_wrapper:
            if wrapper.is_image(elem) is False:
                continue

            # ファイル名、キャプション、IDを取得する
            filename, caption, identifier = \
                wrapper.extract_filename_caption_identifier(elem.text)

            # Markdown Preview Enhancedでプレビューしている場合は、キャプションとIDを追加する
            if wrapper.is_image_when_MPE_preview(elem.attributes):
                # IDが定義されていなければ何もしない
                if identifier is None:
                    return None

                anchor = pf.RawBlock(
                    f'<a id="{utils.normalize_identifier(identifier)}"></a>',
                    format='html')
                fig_num = pf.Str("")  # figure_cross_refで書き換える
                caption = pf.Para(fig_num, pf.Space, pf.Str(caption))
                return [anchor, caption, identifier]

            # エキスポート時は画像で返す
            # (上位側でFigureCrossRefに登録する)
            else:
                # 出力先のディレクトリを追加
                filename = utils.joinpath(self.save_dir, filename)

                # 拡張子が無ければpngにする
                if filename.endswith(".png") is False and \
                   filename.endswith(".svg") is False:
                    filename += ".png"

                wrapper.add(filename, elem)

                caption = pf.Str(caption)
                image = pf.Image(caption, url=filename)
                if identifier is None:
                    return image

                figure = pf.Figure(
                    pf.Plain(image),
                    caption=pf.Caption(pf.Plain(caption)),
                    identifier=identifier)
                return figure

        return None

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

        if len(matches) == 0:
            # 抽出なし
            return text, []

        # "[@XXX]"を"%s"に置き換え
        # ただし、事前に%を%%にエスケープする
        # (参照適用時にpythonが勝手に%%を%に戻すので、明示的にエスケープは戻さなくてよい)
        replaced_text = re.sub(pattern, "%s", text.replace("%", "%%"))

        return replaced_text, matches

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
                list_replace_value.append(reference.get_reference_string(key))

            # コードブロック文字列の置き換え
            replace_text["elem"].text = \
                replace_text["replace_text"] % tuple(list_replace_value)

    @staticmethod
    def _has_ref(identifier: str) -> bool:
        """図の参照が設定されているかどうか判定する"""
        return identifier.startswith("fig:")

    @staticmethod
    def _md5(text: str) -> str:
        """文字列のMD5を取得する"""
        hash_object = hashlib.md5(text.encode())
        return hash_object.hexdigest()

    def export_images(self) -> None:
        """画像の出力"""
        # ディレクトリが無ければ作成
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir, exist_ok=True)

        # 出力ファイルの重複チェック
        self._assert_no_duplicate_filename(
            itertools.chain.from_iterable([
                wrapper.get_filenames() for wrapper in self.list_wrapper
            ])
        )

        # 画像の出力
        for wrapper in self.list_wrapper:
            wrapper.export_images()

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
