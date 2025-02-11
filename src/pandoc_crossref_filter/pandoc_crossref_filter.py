import panflute as pf

from . import const
from . import crossref_utils
from .section_cross_ref import SectionCrossRef
from .image_cross_ref import ImageCrossRef
from .table_cross_ref import TableCrossRef
from .code_block_ref import CodeBlockRef


logger = crossref_utils.get_logger()


def prepare(doc):
    # セクション番号管理
    doc.section_cross_ref = SectionCrossRef(
        doc.get_metadata(const.CONFIG_SECTION, {}))
    # コードブロック管理
    doc.code_block_ref = CodeBlockRef(
        doc.get_metadata(const.CONFIG_CODE_BLOCK, {}))
    # 図番号管理
    doc.image_cross_ref = ImageCrossRef(
        doc.get_metadata(const.CONFIG_IMAGE, {}))
    # 表番号管理
    doc.table_cross_ref = TableCrossRef(
        doc.get_metadata(const.CONFIG_TABLE, {}))
    # 現在のセクション番号
    doc.list_present_section_numbers = []


def action(elem, doc):
    """
    各ヘッダーにセクション番号を付与する。
    """
    logger.debug("Elem:%s", elem)

    if isinstance(elem, pf.SoftBreak):
        """
        例えば

        ああ
        いい

        のような文章の場合、Markdownでは結合されているので

        ああいい

        になってしまうので、入力に従って改行を追加する
        """
        return [pf.LineBreak()]

    elif (isinstance(elem, pf.RawInline)
          and elem.text == "<br>"
          and elem.format == "html"):
        """
        Tableの中で<br>を使うと、
        workd変換時も改行できるようにする
        """
        return [pf.LineBreak()]

    # ヘッダー -> セクション番号
    elif isinstance(elem, pf.Header):
        # セクション番号の加算と参照の登録
        doc.section_cross_ref.register_section(elem)
        # セクション番号の更新
        doc.list_present_section_numbers = \
            doc.section_cross_ref.get_present_section_numbers()
        # メタデータの削除(いろんなものが余計に付与されているので消す)
        elem.classes.clear()
        elem.identifier = ""

    # コードブロック
    elif isinstance(elem, pf.CodeBlock):
        # コードブロック中の参照を探して一時記憶しておく
        ret = doc.code_block_ref.register_code_block(elem)

        if ret is None:
            return

        # コードブロックをイメージ要素に置き換える
        if isinstance(ret, pf.Figure):
            return doc.image_cross_ref.register_image(
                ret, doc.list_present_section_numbers)

        # Markdown Preview Enhancedの場合は、図番号をimage_cross_refに管理させる
        else:
            caption = ret[0]
            identifier = ret[1]
            doc.image_cross_ref.register_external_caption(
                caption,
                identifier,
                doc.list_present_section_numbers
            )
            return [elem, caption]

    # 画像
    elif isinstance(elem, (pf.Figure, pf.Image)):
        image = doc.image_cross_ref.register_image(
            elem, doc.list_present_section_numbers)
        return image

    # 表(のキャプション)
    elif isinstance(elem, pf.Caption):
        doc.table_cross_ref.register_table(
            elem, doc.list_present_section_numbers)

    # 参照を上書きするべき対象を一時的に記憶しておく
    # (参照が後続で定義されているかもしれないので、ここでは上書きできない)
    elif isinstance(elem, pf.Cite):
        list_ret_elem = []
        for citation in elem.citations:
            replace_str = pf.Str("")
            # セクション番号の参照
            if citation.id.startswith("sec:"):
                root_elem = crossref_utils.get_root_elem(elem)
                doc.section_cross_ref.add_reference(
                    citation.id,
                    replace_str,
                    isinstance(root_elem, pf.Header)
                )
                list_ret_elem.append(replace_str)
            # 図番号の参照
            elif citation.id.startswith("fig:"):
                doc.image_cross_ref.add_reference(
                    citation.id,
                    replace_str
                )
                list_ret_elem.append(replace_str)

            # 表番号の参照
            elif citation.id.startswith("tbl:"):
                doc.table_cross_ref.add_reference(
                    citation.id,
                    replace_str
                )
                list_ret_elem.append(replace_str)

        if len(list_ret_elem) > 0:
            # pf.Citeをpf.Strで置き換える
            # (文字列の中身はfinalize()で書き換える)
            return list_ret_elem


def finalize(doc):
    # セクション番号の参照を上書きする
    doc.section_cross_ref.replace_reference()
    # 図番号の参照を上書きする
    doc.image_cross_ref.replace_reference()
    # 表番号の参照を上書きする
    doc.table_cross_ref.replace_reference()
    # コードブロックの参照を上書きする
    doc.code_block_ref.replace_reference(
        doc.section_cross_ref,
        doc.image_cross_ref,
        doc.table_cross_ref
    )
    # PlantUML画像を出力する
    doc.code_block_ref.export_puml_image()
