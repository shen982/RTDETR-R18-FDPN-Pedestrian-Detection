#!/usr/bin/env python3
"""Build an A4, two-column course manuscript from the shared Chinese source."""
from functools import partial
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    BaseDocTemplate, Frame, FrameBreak, FrameSplitter, Image, NextPageTemplate, PageBreak,
    PageTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether,
)

import build_zh_pdf as reading
import course_typography

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "陈佳旭_多核上下文聚焦融合_课程论文.pdf"
PAGE_W, PAGE_H = A4
MARGIN = 18 * mm
BOTTOM = 17 * mm
TOP = PAGE_H - 17 * mm
WIDTH = PAGE_W - 2 * MARGIN
GUTTER = 7 * mm
COLUMN = (WIDTH - GUTTER) / 2
PROJECT_URL = "https://github.com/shen982/RTDETR-R18-FDPN-Pedestrian-Detection"


class FlexibleKeepTogether(KeepTogether):
    """Keep a heading with two lines, rather than moving its whole paragraph."""

    def split(self, available_width, available_height):
        if getattr(self, "_wrapInfo", None) != (available_width, available_height):
            self.wrap(available_width, available_height)
        last = self._content[-1]
        if isinstance(last, Paragraph):
            tail_height = last.height
            minimum_tail = min(tail_height, 2 * last.style.leading)
        elif isinstance(last, Table):
            tail_height = last._height
            header_count = last.repeatRows if isinstance(last.repeatRows, int) else len(last.repeatRows)
            minimum_tail = sum(last._rowHeights[:header_count + 1])
        else:
            return super().split(available_width, available_height)
        minimum = self._H - tail_height + minimum_tail + 2
        if available_height >= minimum:
            return self._content[:]
        return super().split(available_width, available_height)


class ContinuingTable(Table):
    """Repeat the column header and identify every continued table segment."""

    def split(self, available_width, available_height):
        parts = super().split(available_width, available_height)
        label = getattr(self, "continuation_label", None)
        if len(parts) == 2 and label:
            for part in parts:
                part.continuation_label = label
                part.continuation_style = self.continuation_style
            return [parts[0], Paragraph(label, self.continuation_style), parts[1]]
        return parts


class CourseDocTemplate(BaseDocTemplate):
    keepTogetherClass = FlexibleKeepTogether

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("keepTogetherClass", FlexibleKeepTogether)
        super().__init__(*args, **kwargs)
        self.column_usage = {}

    def afterFlowable(self, flowable):
        current = getattr(self, "frame", None)
        if current is None or not getattr(flowable, "height", getattr(flowable, "_height", 0)):
            return
        key = (self.page, current.id)
        entry = self.column_usage.setdefault(key, {
            "page": self.page, "column": current.id,
            "top": current._y2, "bottom": current._y1,
            "content_bottom": current._y,
        })
        entry["content_bottom"] = min(entry["content_bottom"], current._y)


def styles_for_course():
    styles = reading.make_styles()
    for name in ("body", "noindent", "list"):
        styles[name].fontSize = 9.4
        styles[name].leading = 14.8
        styles[name].spaceAfter = 2.5
    styles["body"].firstLineIndent = 18.8
    styles["title"].fontSize = 17
    styles["title"].leading = 23
    styles["title"].spaceAfter = 6
    styles["english_title"].fontSize = 12.3
    styles["english_title"].leading = 16
    styles["english_title"].spaceBefore = 5
    styles["english_title"].spaceAfter = 5
    styles["author"].fontSize = 9
    styles["author"].leading = 13
    styles["author"].spaceAfter = 6
    styles["abstract"].fontSize = 8.8
    styles["abstract"].leading = 12.5
    styles["abstract"].spaceAfter = 5
    for name, size, leading in (("h2", 11, 16), ("h3", 10, 14.5)):
        styles[name].fontName = "CJK-Heading"
        styles[name].fontSize = size
        styles[name].leading = leading
        styles[name].spaceBefore = 7
        styles[name].spaceAfter = 4
    styles["caption"].fontSize = 8
    styles["caption"].leading = 11.4
    styles["caption"].spaceAfter = 6
    styles["table_caption"].fontSize = 8.1
    styles["table_caption"].leading = 11.5
    styles["table_caption"].spaceBefore = 5
    styles["cell"].fontSize = 7.4
    styles["cell"].leading = 10.6
    styles["cell_head"].fontSize = 7.4
    styles["cell_head"].leading = 10.6
    styles["refs"].fontSize = 7.5
    styles["refs"].leading = 10.3
    styles["refs"].spaceAfter = 2.5
    styles["refs"].allowWidows = 0
    styles["refs"].allowOrphans = 0
    styles["equation"].fontSize = 8.3
    styles["equation"].leading = 13
    styles["equation"].leftIndent = 0
    styles["equation"].rightIndent = 0
    styles["equation"].borderWidth = 0
    styles["equation"].backColor = None
    styles["equation"].borderPadding = 0
    styles["equation"].spaceBefore = 4
    styles["equation"].spaceAfter = 5
    styles["title"].fontName = "CJK-Heading"
    styles["english_abstract"] = styles["abstract"].clone("CourseEnglishAbstract")
    styles["english_abstract"].fontName = "Latin"
    styles["english_abstract"].fontSize = 9.2
    styles["english_abstract"].leading = 12.3
    styles["english_abstract"].wordWrap = None
    return styles


def academic_table(node, styles):
    rows = list(reading.descendants(node, "tr"))
    data, headers = [], 0
    for row in rows:
        cells = [c for c in row.children if isinstance(c, reading.Node) and c.tag in {"th", "td"}]
        if not cells:
            continue
        headers += int(all(c.tag == "th" for c in cells))
        data.append([Paragraph(reading.paragraph_markup(c), styles["cell_head" if c.tag == "th" else "cell"]) for c in cells])
    count = len(data[0])
    widths = reading.table_widths(count, COLUMN, node)
    if "dataset-splits" in reading.classes(node):
        widths = [COLUMN * x for x in (.34, .24, .21, .21)]
    elif count == 4 and "robustness-stats" not in reading.classes(node) and "budget-sensitivity" not in reading.classes(node):
        widths = [COLUMN * x for x in (.34, .22, .20, .24)]
    grid = ContinuingTable(data, colWidths=widths, repeatRows=headers, hAlign="CENTER")
    grid.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Latin"),
        ("LINEABOVE", (0, 0), (-1, 0), .8, colors.black),
        ("LINEBELOW", (0, headers - 1), (-1, headers - 1), .45, colors.black),
        ("LINEBELOW", (0, -1), (-1, -1), .8, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2.5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2.5),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    caption = reading.first_descendant(node, "caption")
    import re
    number = re.match(r"表\s*([A-Z]?\d+)", reading.plain_text(caption)).group(1)
    grid.continuation_label = "续表 " + number
    grid.continuation_style = styles["table_caption"]
    if number == "3":
        # Keep baseline and FDPN rows from the same dataset together.
        grid.setStyle(TableStyle([("NOSPLIT", (0, row), (-1, row + 1))
                                  for row in (1, 3, 5)]))
    return [Paragraph(reading.paragraph_markup(caption), styles["table_caption"]), grid, Spacer(1, 5)]


def figure_block(node, styles, available=WIDTH):
    img = reading.first_descendant(node, "img")
    path = HERE / img.attrs["src"]
    if "robustness_summary" in path.name and available == COLUMN:
        path = HERE.parent / "figures/robustness_summary_column.png"
    with PILImage.open(path) as source:
        width, height = source.size
    # Keep the accepted figure intact; only its placement and scale are changed.
    draw_width = available * (.99 if available == COLUMN else .96)
    image = Image(str(path), width=draw_width, height=draw_width * height / width)
    caption = Paragraph(reading.paragraph_markup(reading.first_descendant(node, "figcaption")), styles["caption"])
    _, caption_height = caption.wrap(available, PAGE_H)
    total = image.drawHeight + 5 + caption_height + 12
    return image, caption, caption_height, total


def frame(name, x, top, width):
    return Frame(x, BOTTOM, width, top - BOTTOM, id=name,
                 leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Latin", 8)
    if doc.page == 1:
        canvas.drawRightString(PAGE_W - MARGIN, 9 * mm, str(doc.page))
        canvas.setFont("Latin", 7)
        canvas.drawString(MARGIN, 9 * mm, PROJECT_URL)
        width = canvas.stringWidth(PROJECT_URL, "Latin", 7)
        canvas.linkURL(PROJECT_URL, (MARGIN, 8 * mm, MARGIN + width, 12 * mm),
                       relative=0, thickness=0)
    else:
        canvas.drawCentredString(PAGE_W / 2, 9 * mm, str(doc.page))
    canvas.restoreState()


def main():
    course_typography.configure(reading)
    styles = styles_for_course()
    parser = reading.DOMParser()
    parser.feed(reading.HTML_PATH.read_text())
    body = reading.first_descendant(parser.root, "body")
    nodes = [n for n in body.children if isinstance(n, reading.Node)]
    figures = {reading.first_descendant(n, "img").attrs["src"]: n for n in nodes if n.tag == "figure"}
    blocks = {name: figure_block(figures[src], styles) for name, src in (
        ("architecture", "architecture_visio_revision.png"),
        ("results", "robustness_summary.png"))}
    doc = CourseDocTemplate(str(OUTPUT), pagesize=A4, initialFontName="Latin",
                          leftMargin=MARGIN, rightMargin=MARGIN,
                          topMargin=PAGE_H - TOP, bottomMargin=BOTTOM,
                          title="有限标注行人检测中聚焦—扩散特征融合的受控评估与组件分析",
                          author="陈佳旭 / Jiaxu Chen")
    templates = [PageTemplate(id="front", frames=[frame("full", MARGIN, TOP, WIDTH)], onPage=footer),
                 PageTemplate(id="body", frames=[frame("left", MARGIN, TOP, COLUMN), frame("right", MARGIN + COLUMN + GUTTER, TOP, COLUMN)], onPage=footer)]
    drawn_figures = []
    for name, (img, caption, caption_height, total) in blocks.items():
        def draw(canvas, document, img=img, caption=caption, caption_height=caption_height, name=name):
            footer(canvas, document)
            img.drawOn(canvas, MARGIN + (WIDTH - img.drawWidth) / 2, TOP - img.drawHeight)
            caption.drawOn(canvas, MARGIN, TOP - img.drawHeight - 5 - caption_height)
            drawn_figures.append((name, document.page))
        top = TOP - total
        templates.append(PageTemplate(id=name, frames=[frame("left", MARGIN, top, COLUMN), frame("right", MARGIN + COLUMN + GUTTER, top, COLUMN)], onPage=draw, autoNextPageTemplate="body"))
    doc.addPageTemplates(templates)
    story, in_body = [], False
    for node in nodes:
        text = reading.plain_text(node)
        if node.tag == "h2" and text.startswith("一、") and not in_body:
            story.append(FrameSplitter("body", ["left", "right"], gap=9, required=75))
            story.append(NextPageTemplate("architecture"))
            in_body = True
        if node.tag == "figure":
            if reading.first_descendant(node, "img").attrs["src"] == "initial_penn_curves_column.png":
                img, caption, _, _ = figure_block(node, styles, COLUMN)
                story.append(KeepTogether([Spacer(1, 5), img, Spacer(1, 3), caption]))
            continue
        if node.tag == "h2" and text.startswith("四、"):
            story.append(NextPageTemplate("results"))
        if node.tag == "h2" and text.startswith("附录 A"):
            story.extend([NextPageTemplate("body"), Spacer(1, 8)])
        if node.tag in {"h2", "h3", "h4"}:
            story.append(Paragraph(reading.paragraph_markup(node), styles["h2" if node.tag == "h2" else "h3"]))
        elif node.tag == "table":
            story.extend(academic_table(node, styles))
        elif node.tag == "div" and "keywords" in reading.classes(node):
            story.append(Paragraph(reading.paragraph_markup(node), styles["abstract"]))
        elif node.tag == "div" and "equation" in reading.classes(node):
            import re
            number = int(re.search(r"（(\d+)）", text).group(1))
            story.append(course_typography.Equation(number, COLUMN))
        elif node.tag == "div" and {"abstract", "english"}.issubset(reading.classes(node)):
            story.append(Paragraph("Abstract", styles["h3"]))
            for paragraph in reading.descendants(node, "p"):
                story.append(Paragraph(reading.paragraph_markup(paragraph), styles["english_abstract"]))
        else:
            wrapper = reading.Node("div")
            wrapper.children = [node]
            reading.render_children(wrapper, story, styles, COLUMN if in_body else WIDTH)
    doc.build(story, canvasmaker=partial(Canvas, initialFontName="Latin"))
    assert sorted(name for name, _ in drawn_figures) == ["architecture", "results"], drawn_figures
    print(OUTPUT)
    print("Full-width figure placement:", drawn_figures)
    return doc


if __name__ == "__main__":
    main()
