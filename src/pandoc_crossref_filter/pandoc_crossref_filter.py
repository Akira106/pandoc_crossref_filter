import panflute as pf

from . import utils
from .section_cross_ref import SectionCrossRef
from .figure_cross_ref import FigureCrossRef
from .table_cross_ref import TableCrossRef
from .code_block_ref import CodeBlockRef


logger = utils.get_logger()

# configのキー
CONFIG_ROOT = "pandoc_crossref_filter"
CONFIG_SECTION = f"{CONFIG_ROOT}.section"
CONFIG_IMAGE = f"{CONFIG_ROOT}.figure"
CONFIG_TABLE = f"{CONFIG_ROOT}.table"
CONFIG_CODE_BLOCK = f"{CONFIG_ROOT}.code_block"


def prepare(doc):
    # セクション番号管理
    doc.section_cross_ref = SectionCrossRef(
        doc.get_metadata(CONFIG_SECTION, {}))
    # コードブロック管理
    doc.code_block_ref = CodeBlockRef(
        doc.get_metadata(CONFIG_CODE_BLOCK, {}))
    # 図番号管理
    doc.figure_cross_ref = FigureCrossRef(
        doc.get_metadata(CONFIG_IMAGE, {}))
    # 表番号管理
    doc.table_cross_ref = TableCrossRef(
        doc.get_metadata(CONFIG_TABLE, {}))
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

        のような文章の場合、Markdownでは

        ああいい

        のように改行が無くなってしまう。
        そこで、元の見た目と同じになるように、改行を追加する。
        """
        return [pf.LineBreak()]

    elif (isinstance(elem, pf.RawInline)
          and elem.text == "<br>"
          and elem.format == "html"):
        """
        Tableの中で<br>を使うと、
        pandocでwordに変換したときも、表の中で改行できるようにする
        """
        return [pf.LineBreak()]

    # ヘッダー -> セクション番号
    elif isinstance(elem, pf.Header):
        # セクション番号の加算と参照の登録
        doc.section_cross_ref.register_section(elem)
        # セクション番号の更新
        doc.list_present_section_numbers = \
            doc.section_cross_ref.get_present_section_numbers()

    # コードブロック
    elif isinstance(elem, pf.CodeBlock):
        # コードブロック中の参照を探して一時記憶しておく
        ret = doc.code_block_ref.register_code_block(elem)

        if ret is None:
            return

        # コードブロックをイメージ要素に置き換える
        if isinstance(ret, (pf.Figure, pf.Image)):
            figure = doc.figure_cross_ref.register_figure(
                ret, doc.list_present_section_numbers)
            # Image要素の場合は、Para要素に変換しないとエラーになる
            if isinstance(ret, pf.Image):
                figure = pf.Para(figure)
            return figure

        # Markdown Preview Enhancedの場合は、図番号をfigure_cross_refに管理させる
        else:
            caption = ret[0]
            identifier = ret[1]
            doc.figure_cross_ref.register_external_caption(
                caption,
                identifier,
                doc.list_present_section_numbers
            )
            return [elem, caption]

    # 画像
    elif isinstance(elem, (pf.Figure, pf.Image)):
        image = doc.figure_cross_ref.register_figure(
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
                root_elem = utils.get_root_elem(elem)
                doc.section_cross_ref.add_reference(
                    citation.id,
                    replace_str,
                    isinstance(root_elem, pf.Header)
                )
                list_ret_elem.append(replace_str)
            # 図番号の参照
            elif citation.id.startswith("fig:"):
                doc.figure_cross_ref.add_reference(
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
    doc.figure_cross_ref.replace_reference()
    # 表番号の参照を上書きする
    doc.table_cross_ref.replace_reference()
    # コードブロックの参照を上書きする
    doc.code_block_ref.replace_reference(
        doc.section_cross_ref,
        doc.figure_cross_ref,
        doc.table_cross_ref
    )
    # PlantUML画像を出力する
    doc.code_block_ref.export_puml_images()
