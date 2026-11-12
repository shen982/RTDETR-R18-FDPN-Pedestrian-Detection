#!/usr/bin/env python3
"""Build the standalone Chinese reading edition from main_zh.html."""

from __future__ import annotations

from functools import partial
from html.parser import HTMLParser
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    HRFlowable,
    Image,
    ListFlowable,
    ListItem,
    KeepTogether,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


HERE = Path(__file__).resolve().parent
HTML_PATH = HERE / "main_zh.html"
PDF_PATH = HERE / "RTDETR_R18_FDPN_中文阅读版.pdf"
FONT_PATH = Path("/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf")
MONO_PATH = Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf")
LATIN_PATH = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
LATIN_BOLD_PATH = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
CJK_CHARACTERS = set()


def font_markup(value: str) -> str:
    """Droid CJK lacks Latin glyphs; explicitly select an embedded Latin font."""
    output, run, current = [], [], None
    for char in value:
        face = "CJK" if ord(char) in CJK_CHARACTERS else "Latin"
        if face != current and run:
            output.append(f'<font name="{current}">{escape("".join(run))}</font>')
            run = []
        current = face
        run.append(char)
    if run:
        output.append(f'<font name="{current}">{escape("".join(run))}</font>')
    return "".join(output)


class Node:
    def __init__(self, tag: str, attrs=None, parent=None):
        self.tag = tag
        self.attrs = dict(attrs or [])
        self.parent = parent
        self.children: list[Node | str] = []


class DOMParser(HTMLParser):
    VOID = {"meta", "img", "br", "hr", "link", "input", "wbr"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("document")
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag.lower(), attrs, self.stack[-1])
        self.stack[-1].children.append(node)
        if tag.lower() not in self.VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        node = Node(tag.lower(), attrs, self.stack[-1])
        self.stack[-1].children.append(node)

    def handle_endtag(self, tag):
        tag = tag.lower()
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_data(self, data):
        if data:
            self.stack[-1].children.append(data)


def descendants(node: Node, tag: str):
    for child in node.children:
        if isinstance(child, Node):
            if child.tag == tag:
                yield child
            yield from descendants(child, tag)


def first_descendant(node: Node, tag: str) -> Node | None:
    return next(descendants(node, tag), None)


def classes(node: Node) -> set[str]:
    return set(node.attrs.get("class", "").split())


def plain_text(node: Node) -> str:
    pieces: list[str] = []
    for child in node.children:
        if isinstance(child, str):
            pieces.append(child)
        elif child.tag == "br":
            pieces.append("\n")
        else:
            pieces.append(plain_text(child))
    return "".join(pieces).strip()


def paragraph_markup(node: Node) -> str:
    pieces: list[str] = []
    supported = {
        "strong": ("<b>", "</b>"),
        "b": ("<b>", "</b>"),
        "i": ("<i>", "</i>"),
        "em": ("<i>", "</i>"),
        "sup": ("<super>", "</super>"),
        "sub": ("<sub>", "</sub>"),
    }
    for child in node.children:
        if isinstance(child, str):
            pieces.append(font_markup(child))
        elif child.tag == "br":
            pieces.append("<br/>")
        elif child.tag in supported:
            opening, closing = supported[child.tag]
            pieces.append(opening + paragraph_markup(child) + closing)
        else:
            pieces.append(paragraph_markup(child))
    return "".join(pieces).strip()


def register_fonts() -> None:
    global CJK_CHARACTERS
    pdfmetrics.registerFont(TTFont("CJK", str(FONT_PATH)))
    pdfmetrics.registerFont(TTFont("CJK-Bold", str(FONT_PATH)))
    pdfmetrics.registerFont(TTFont("CJK-Italic", str(FONT_PATH)))
    pdfmetrics.registerFont(TTFont("Mono", str(MONO_PATH)))
    pdfmetrics.registerFont(TTFont("Latin", str(LATIN_PATH)))
    pdfmetrics.registerFont(TTFont("Latin-Bold", str(LATIN_BOLD_PATH)))
    pdfmetrics.registerFontFamily("Latin", normal="Latin", bold="Latin-Bold", italic="Latin", boldItalic="Latin-Bold")
    pdfmetrics.registerFontFamily("CJK", normal="CJK", bold="CJK-Bold", italic="CJK-Italic", boldItalic="CJK-Bold")
    CJK_CHARACTERS = set(pdfmetrics.getFont("CJK").face.charToGlyph)


def make_styles():
    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle(
            "ZHTitle", parent=base["Title"], fontName="CJK-Bold", fontSize=21,
            leading=29, alignment=TA_CENTER, textColor=colors.HexColor("#171717"),
            spaceAfter=7 * mm,
        ),
        "subtitle": ParagraphStyle(
            "ZHSubtitle", fontName="CJK", fontSize=10.5, leading=16,
            alignment=TA_CENTER, textColor=colors.HexColor("#555555"), spaceAfter=3 * mm,
        ),
        "english_title": ParagraphStyle(
            "EnglishTitle", fontName="Latin-Bold", fontSize=14,
            leading=19, alignment=TA_CENTER, spaceBefore=3 * mm, spaceAfter=3 * mm,
        ),
        "abstract": ParagraphStyle(
            "AcademicAbstract", fontName="CJK", fontSize=9.6, leading=15.5,
            alignment=TA_JUSTIFY, spaceAfter=3 * mm,
        ),
        "author": ParagraphStyle(
            "ZHAuthor", fontName="CJK", fontSize=10.5, leading=16,
            alignment=TA_CENTER, spaceAfter=6 * mm,
        ),
        "h2": ParagraphStyle(
            "ZHH2", fontName="CJK-Bold", fontSize=15, leading=22,
            spaceBefore=6 * mm, spaceAfter=2.5 * mm, keepWithNext=True,
        ),
        "h3": ParagraphStyle(
            "ZHH3", fontName="CJK-Bold", fontSize=12.2, leading=18,
            spaceBefore=4 * mm, spaceAfter=1.5 * mm, keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "ZHBody", fontName="CJK", fontSize=10.2, leading=17.2,
            firstLineIndent=20.4, alignment=TA_JUSTIFY, spaceAfter=2.2 * mm,
            allowWidows=0, allowOrphans=0,
        ),
        "noindent": ParagraphStyle(
            "ZHNoIndent", fontName="CJK", fontSize=10.2, leading=17.2,
            alignment=TA_JUSTIFY, spaceAfter=2.2 * mm,
        ),
        "callout": ParagraphStyle(
            "ZHCallout", fontName="CJK", fontSize=9.8, leading=16.2,
            alignment=TA_JUSTIFY, leftIndent=4 * mm, rightIndent=3 * mm,
            borderColor=colors.HexColor("#3B6F8F"), borderWidth=1.2,
            borderPadding=7, backColor=colors.HexColor("#F3F7FA"), spaceAfter=3 * mm,
        ),
        "equation": ParagraphStyle(
            "ZHEquation", fontName="CJK", fontSize=10.2, leading=16,
            alignment=TA_CENTER, leftIndent=8 * mm, rightIndent=8 * mm,
            borderColor=colors.HexColor("#DDDDDD"), borderWidth=0.6,
            borderPadding=7, backColor=colors.HexColor("#FAFAFA"),
            spaceBefore=2 * mm, spaceAfter=3 * mm,
        ),
        "caption": ParagraphStyle(
            "ZHCaption", fontName="CJK", fontSize=8.4, leading=13,
            alignment=TA_JUSTIFY, textColor=colors.HexColor("#333333"),
            spaceBefore=1.5 * mm, spaceAfter=4 * mm,
        ),
        "table_caption": ParagraphStyle(
            "ZHTableCaption", fontName="CJK-Bold", fontSize=9.2, leading=14,
            alignment=TA_CENTER, spaceBefore=2 * mm, spaceAfter=1.5 * mm, keepWithNext=True,
        ),
        "cell": ParagraphStyle(
            "ZHCell", fontName="CJK", fontSize=7.7, leading=11, alignment=TA_LEFT,
        ),
        "cell_head": ParagraphStyle(
            "ZHCellHead", fontName="CJK-Bold", fontSize=7.7, leading=11, alignment=TA_CENTER,
        ),
        "list": ParagraphStyle(
            "ZHList", fontName="CJK", fontSize=10, leading=16.5, alignment=TA_JUSTIFY,
        ),
        "refs": ParagraphStyle(
            "ZHRefs", fontName="CJK", fontSize=8.2, leading=12.8,
            leftIndent=8 * mm, firstLineIndent=-8 * mm, spaceAfter=1.5 * mm,
        ),
        "footer_note": ParagraphStyle(
            "ZHFooterNote", fontName="CJK", fontSize=8.2, leading=13,
            alignment=TA_CENTER, textColor=colors.HexColor("#666666"), spaceBefore=5 * mm,
        ),
        "code": ParagraphStyle(
            "ZHCode", fontName="Mono", fontSize=7.6, leading=10.8,
            leftIndent=3 * mm, rightIndent=3 * mm, borderColor=colors.HexColor("#DDDDDD"),
            borderWidth=0.6, borderPadding=6, backColor=colors.HexColor("#F6F6F6"),
            spaceBefore=2 * mm, spaceAfter=4 * mm,
        ),
    }
    for style in styles.values():
        if style.fontName.startswith("CJK"):
            style.wordWrap = "CJK"
    return styles


def table_widths(column_count: int, available: float, node: Node):
    if "dataset-splits" in classes(node):
        return [available * x for x in (.31, .23, .23, .23)]
    if "ablation" in classes(node):
        if column_count == 5:
            return [available * x for x in (.32,.15,.17,.18,.18)]
        return [available * x for x in (.23,.14,.14,.12,.12,.13,.12)]
    if "robustness-stats" in classes(node) or "budget-sensitivity" in classes(node):
        return [available * x for x in (.34,.16,.25,.25)]
    if "robustness-seeds" in classes(node):
        return [available * x for x in (.13,.30,.17,.18,.22)]
    if "hashes" in classes(node):
        return [available * 0.24, available * 0.76]
    if column_count == 2:
        return [available * 0.30, available * 0.70]
    if column_count == 4:
        return [available * 0.14, available * 0.21, available * 0.26, available * 0.39]
    if column_count == 5:
        return [available * 0.28] + [available * 0.18] * 4
    if column_count == 7:
        return [available * 0.09, available * 0.21, available * 0.08] + [available * 0.155] * 4
    return [available / column_count] * column_count


def make_table(node: Node, styles, available: float):
    output = []
    caption = first_descendant(node, "caption")
    if caption is not None:
        output.append(Paragraph(paragraph_markup(caption), styles["table_caption"]))

    rows = list(descendants(node, "tr"))
    data = []
    header_rows = 0
    for row_index, row in enumerate(rows):
        cells = [child for child in row.children if isinstance(child, Node) and child.tag in {"th", "td"}]
        if not cells:
            continue
        if all(cell.tag == "th" for cell in cells):
            header_rows += 1
        rendered = []
        for cell in cells:
            style = styles["cell_head"] if cell.tag == "th" else styles["cell"]
            rendered.append(Paragraph(paragraph_markup(cell), style))
        data.append(rendered)
    if not data:
        return output

    col_count = max(len(row) for row in data)
    for row in data:
        row.extend([Paragraph("", styles["cell"])] * (col_count - len(row)))
    grid = Table(data, colWidths=table_widths(col_count, available, node), repeatRows=header_rows)
    grid.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Latin"),
        ("LINEABOVE", (0, 0), (-1, 0), 0.8, colors.black),
        ("LINEBELOW", (0, header_rows - 1), (-1, header_rows - 1), 0.45, colors.black),
        ("LINEBELOW", (0, -1), (-1, -1), 0.8, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    output.extend([grid, Spacer(1, 3 * mm)])
    return output


def render_children(node: Node, story, styles, available: float):
    for child in node.children:
        if not isinstance(child, Node):
            continue
        tag = child.tag
        cls = classes(child)

        if tag in {"style", "head", "script"}:
            continue
        if tag == "h1":
            story.append(Paragraph(paragraph_markup(child).replace("<br/>", "<br/>"), styles["title"]))
        elif tag == "h2":
            if plain_text(child).startswith("附录 A"):
                # Keep supplementary analysis compact without shrinking the main text.
                styles = {name: value.clone(value.name + "Appendix") for name, value in styles.items()}
                for name in ("body", "noindent"):
                    styles[name].fontSize = 9.5
                    styles[name].leading = 15
                    styles[name].spaceAfter = 3
                styles["h2"].spaceBefore = 8
                styles["h3"].spaceBefore = 7
                styles["h3"].spaceAfter = 3
            if "page-break" in cls:
                story.append(PageBreak())
            story.append(Paragraph(paragraph_markup(child), styles["h2"]))
            rule = HRFlowable(width="100%", thickness=0.7, color=colors.HexColor("#444444"), spaceAfter=2 * mm)
            rule.keepWithNext = True
            story.append(rule)
        elif tag in {"h3", "h4"}:
            story.append(Paragraph(paragraph_markup(child), styles["h3"]))
        elif tag == "p":
            style = styles["noindent"] if "noindent" in cls else styles["body"]
            story.append(Paragraph(paragraph_markup(child), style))
        elif tag == "div" and "subtitle" in cls:
            story.append(Paragraph(paragraph_markup(child), styles["subtitle"]))
        elif tag == "div" and "english-title" in cls:
            story.append(Paragraph(paragraph_markup(child), styles["english_title"]))
        elif tag == "div" and "author" in cls:
            story.append(Paragraph(paragraph_markup(child), styles["author"]))
        elif tag == "div" and "keywords" in cls:
            story.append(Paragraph(paragraph_markup(child), styles["noindent"]))
        elif tag == "div" and ("abstract" in cls or "note" in cls):
            title = first_descendant(child, "h2") or first_descendant(child, "h3")
            paragraphs = list(descendants(child, "p"))
            if title is not None:
                story.append(Paragraph(paragraph_markup(title), styles["h3"]))
            for paragraph in paragraphs:
                story.append(Paragraph(paragraph_markup(paragraph), styles["abstract" if "abstract" in cls else "callout"]))
        elif tag == "div" and "equation" in cls:
            story.append(Paragraph(paragraph_markup(child), styles["equation"]))
        elif tag == "div" and "code" in cls:
            story.append(Preformatted(plain_text(child), styles["code"], maxLineLength=110))
        elif tag == "div" and "footer-note" in cls:
            story.append(Paragraph(paragraph_markup(child), styles["footer_note"]))
        elif tag in {"ul", "ol"}:
            items = [n for n in child.children if isinstance(n, Node) and n.tag == "li"]
            if "refs" in cls:
                for index, item in enumerate(items, 1):
                    story.append(Paragraph(font_markup(f"[{index}]　") + paragraph_markup(item), styles["refs"]))
            else:
                bullets = [ListItem(Paragraph(paragraph_markup(item), styles["list"]), leftIndent=4 * mm) for item in items]
                story.append(ListFlowable(
                    bullets, bulletType="bullet" if tag == "ul" else "1",
                    start="circle" if tag == "ul" else "1", leftIndent=8 * mm,
                    bulletFontName="Latin", bulletFontSize=8, spaceAfter=3 * mm,
                ))
        elif tag == "figure":
            figure_story = []
            image_node = first_descendant(child, "img")
            caption = first_descendant(child, "figcaption")
            if image_node is not None:
                image_path = HERE / image_node.attrs["src"]
                with PILImage.open(image_path) as source:
                    px_w, px_h = source.size
                scale = 0.78 if "robustness_summary" in image_path.name else (0.74 if "compact" in cls else 1.0)
                width = available * scale
                height = width * px_h / px_w
                max_height = 185 * mm
                if height > max_height:
                    height = max_height
                    width = height * px_w / px_h
                figure_story.append(Spacer(1, 2 * mm))
                figure_story.append(Image(str(image_path), width=width, height=height, hAlign="CENTER"))
            if caption is not None:
                figure_story.append(Paragraph(paragraph_markup(caption), styles["caption"]))
            story.append(KeepTogether(figure_story))
        elif tag == "table":
            story.extend(make_table(child, styles, available))
        else:
            render_children(child, story, styles, available)


def draw_footer(canvas, doc):
    canvas.saveState()
    style = ParagraphStyle("PageFooter", fontName="CJK", fontSize=8, leading=10, alignment=TA_CENTER, textColor=colors.HexColor("#666666"))
    footer = Paragraph(font_markup(f"RT-DETR-R18 + FDPN 中文阅读版　·　第 {doc.page} 页"), style)
    footer.wrap(A4[0]-36*mm, 15*mm)
    footer.drawOn(canvas, 18*mm, 9*mm)
    canvas.restoreState()


def main() -> None:
    register_fonts()
    parser = DOMParser()
    parser.feed(HTML_PATH.read_text(encoding="utf-8"))
    body = first_descendant(parser.root, "body")
    if body is None:
        raise RuntimeError("main_zh.html has no body element")

    doc = SimpleDocTemplate(
        str(PDF_PATH), pagesize=A4,
        initialFontName="Latin",
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=17 * mm,
        title="有限标注行人检测中聚焦—扩散融合的性能与组件分析",
        author="陈佳旭 / Jiaxu Chen",
        subject="FDPN adaptation of RT-DETR-R18; bilingual abstracts and Chinese full text",
    )
    styles = make_styles()
    story = []
    render_children(body, story, styles, doc.width)
    doc.build(story, onFirstPage=draw_footer, onLaterPages=draw_footer,
              canvasmaker=partial(Canvas, initialFontName="Latin"))
    print(PDF_PATH)


if __name__ == "__main__":
    main()
