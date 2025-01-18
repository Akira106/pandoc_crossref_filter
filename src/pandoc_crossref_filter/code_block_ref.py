import os
import subprocess
import sys
import re
import hashlib
from typing import List, Tuple, Dict

import panflute as pf

from . import crossref_utils
from .section_cross_ref import SectionCrossRef
from .image_cross_ref import ImageCrossRef
from .table_cross_ref import TableCrossRef


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

        # PlantUMLの設定
        self.puml_jar_path: str = config.get("plantuml_jar_path")

        # 書き換えるべき項目を記憶する(最後に書き換える)
        self.list_replace_target: List[Dict] = []
        # PlantUMLで出力するべきコードブロック
        self.list_puml: List[Dict] = []

    def register_code_block(self, elem: pf.CodeBlock) -> None | pf.Figure:
        """コードブロックの登録

        - コードブロックの参照を抽出して一時保存する
        - PlantUMLのコードブロックであった場合、pf.Figure要素に変換する

        Args:
            elem (pf.CodeBlock):
                コードブロック

        Returns:
            None | pf.Figure:
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
        if self._is_puml(elem.classes) is False:
            return

        # 後でPlantUMLに変換する要素を保存しておく
        url = os.path.join(
            self.save_dir,
            elem.attributes.get("filename", self._md5(elem.text) + ".png"))
        # 拡張子を強制的にpngにする
        if url.endswith(".png") is False:
            url += ".png"
        self.list_puml.append({
            "filename": url,
            "elem": elem
        })

        # PlantUMLの場合は画像を返す
        # (上位側でImageCrossRefに登録する)
        caption = pf.Str(elem.attributes.get("caption", ""))
        image = pf.Image(caption, url=url)
        figure = pf.Figure(
            pf.Plain(image),
            caption=pf.Caption(pf.Plain(caption)),
            identifier=elem.identifier)
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

    def replace_reference(self,
                          section_cross_ref: SectionCrossRef,
                          image_cross_ref: ImageCrossRef,
                          table_cross_ref: TableCrossRef) -> None:
        """参照を置き換える関数

        Args:
            section_cross_ref: SectionCrossRef
                セクション番号の参照
            image_cross_ref: ImageCrossRef):
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
                    reference = image_cross_ref
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

    @staticmethod
    def _is_puml(classes: List[str]) -> bool:
        """コードブロックがPlantUMLかどうかを判定する

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
    def _has_ref(identifier: str) -> bool:
        """図の参照が設定されているかどうか判定する"""
        return identifier.startswith("fig:")

    @staticmethod
    def _md5(text: str) -> str:
        """文字列のMD5を取得する"""
        hash_object = hashlib.md5(text.encode())
        return hash_object.hexdigest()

    def export_puml_image(self) -> None:
        """PlantUML画像の出力"""
        # PlantUMLがなければ終了
        if len(self.list_puml) == 0:
            return

        # ディレクトリが無ければ作成
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir, exist_ok=True)

        # .pumlの拡張子で一旦出力する
        list_puml_filename = []
        for puml in self.list_puml:
            puml_text = puml["elem"].text
            # @startumlと@endumlを自動で追加する
            if not puml_text.startswith("@startuml"):
                puml_text = "@startuml\n" + puml_text
            if not puml_text.endswith("@enduml"):
                puml_text += "\n@enduml"
            # 拡張子の変更
            # (self.register_code_block内で強制的に.pngにしているので、それを.pumlにする)
            puml_filename = \
                puml["filename"].rsplit(".", maxsplit=1)[0] + ".puml"
            with open(puml_filename, "w") as f:
                f.write(puml_text)
            list_puml_filename.append(puml_filename)

        # PlantUMLで変換する
        self._export_puml_image_local(list_puml_filename)

        # pumlファイルを削除する
        for puml_filename in list_puml_filename:
            if os.path.exists(puml_filename) is True:
                os.remove(puml_filename)

    def _export_puml_image_local(self,
                                 list_puml_filename: List[str],
                                 limit_size: int = 16384) -> None:
        """ローカルのplantuml.jarで出力する

        Args:
            list_puml_filename (list(str)): 出力するファイル名のリスト
        """
        target_puml = " ".join(list_puml_filename)
        # ToDo:
        # - PlantUMLのパスを環境変数などに分離する
        cmd = f'java -jar {self.puml_jar_path} -DPLANTUML_LIMIT_SIZE={limit_size} -charset UTF-8 {target_puml}'
        subprocess.check_output(cmd, shell=True)
