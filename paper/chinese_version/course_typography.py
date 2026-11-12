"""Embedded Chinese/Latin typefaces and native-vector mathematical equations."""
import re
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Flowable

from prepare_course_fonts import prepare, FONT_DIR


LATIN_DIR = next(p for p in (
    Path("/usr/share/fonts/truetype/liberation2"),
    Path("/usr/share/fonts/truetype/liberation"),
) if (p / "LiberationSerif-Regular.ttf").is_file())
SYMBOLS = set("ΦφΣ∑∈𝒫𝒦")


def _unicode_cmap(fontname, subset):
    """Encode astral mathematical letters as UTF-16 surrogate pairs in PDFs."""
    lines = [
        "/CIDInit /ProcSet findresource begin", "12 dict begin", "begincmap",
        "/CIDSystemInfo", "<< /Registry (%s)" % fontname,
        "/Ordering (%s)" % fontname, "/Supplement 0", ">> def",
        "/CMapName /%s def" % fontname, "/CMapType 2 def",
        "1 begincodespacerange", "<00> <%02X>" % (len(subset) - 1),
        "endcodespacerange", "%d beginbfchar" % len(subset),
    ]
    lines.extend("<%02X> <%s>" % (i, chr(code).encode("utf-16-be").hex().upper()) for i, code in enumerate(subset))
    lines.extend(["endbfchar", "endcmap", "CMapName currentdict /CMap defineresource pop", "end", "end"])
    return "\n".join(lines)


def configure(reading):
    prepare()
    from matplotlib import get_data_path
    from reportlab.pdfbase import ttfonts
    ttfonts.makeToUnicodeCMap = _unicode_cmap
    import reportlab.platypus.paragraph as paragraph_engine
    paragraph_engine.ALL_CANNOT_START += "，；：！？％”’）〕】〉》…"
    for name, path in (
        ("CJK", FONT_DIR / "CourseSerif-Regular.ttf"),
        ("CJK-Bold", FONT_DIR / "CourseSerif-Semibold.ttf"),
        ("CJK-Heading", FONT_DIR / "CourseHei-Bold.ttf"),
        ("Latin", LATIN_DIR / "LiberationSerif-Regular.ttf"),
        ("Latin-Bold", LATIN_DIR / "LiberationSerif-Bold.ttf"),
        ("Latin-Italic", LATIN_DIR / "LiberationSerif-Italic.ttf"),
        ("Latin-BoldItalic", LATIN_DIR / "LiberationSerif-BoldItalic.ttf"),
        ("Mono", LATIN_DIR / "LiberationMono-Regular.ttf"),
        ("MathSymbols", Path(get_data_path()) / "fonts/ttf/STIXGeneral.ttf"),
    ):
        pdfmetrics.registerFont(TTFont(name, str(path)))
    pdfmetrics.registerFontFamily("CJK", normal="CJK", bold="CJK-Bold", italic="CJK", boldItalic="CJK-Bold")
    pdfmetrics.registerFontFamily("Latin", normal="Latin", bold="Latin-Bold", italic="Latin-Italic", boldItalic="Latin-BoldItalic")
    pdfmetrics.registerFontFamily("CJK-Heading", normal="CJK-Heading", bold="CJK-Heading", italic="CJK-Heading", boldItalic="CJK-Heading")
    reading.font_markup = text_markup
    reading.paragraph_markup = paragraph_markup


def _font(char, bold, italic, heading):
    code = ord(char)
    if char in SYMBOLS:
        return "MathSymbols"
    if code >= 0x2E80 or char in "“”‘’—…":
        return "CJK-Heading" if heading else ("CJK-Bold" if bold else "CJK")
    if bold and italic:
        return "Latin-BoldItalic"
    return "Latin-Bold" if bold else ("Latin-Italic" if italic else "Latin")


def _runs(value, bold=False, italic=False, heading=False):
    output, run, face = [], [], None
    for char in value:
        target = _font(char, bold, italic, heading)
        if target != face and run:
            output.append('<font name="%s">%s</font>' % (face, escape("".join(run))))
            run = []
        face = target
        run.append(char)
    if run:
        output.append('<font name="%s">%s</font>' % (face, escape("".join(run))))
    return "".join(output)


def text_markup(value, bold=False, italic=False, heading=False):
    output, last = [], 0
    # Keep AP and mAP upright; their IoU thresholds are real subscripts.
    for match in re.finditer(r"(?<![A-Za-z])(m?AP)(50(?::95)?)(?![0-9])", value):
        output.append(_runs(value[last:match.start()], bold, italic, heading))
        output.append(_runs(match[1], bold, False, heading))
        output.append('<sub rise="15%" size="70%">' + _runs(match[2], bold, False, heading) + "</sub>")
        last = match.end()
    output.append(_runs(value[last:], bold, italic, heading))
    return "".join(output)


def paragraph_markup(node, bold=False, italic=False, heading=False):
    heading = heading or node.tag in {"h1", "h2", "h3", "h4"}
    bold = bold or heading or node.tag in {"strong", "b"} or "english-title" in node.attrs.get("class", "").split()
    italic = italic or node.tag in {"i", "em"}
    result = []
    for child in node.children:
        if isinstance(child, str):
            result.append(text_markup(child, bold, italic, heading))
        elif child.tag == "br":
            result.append("<br/>")
        elif child.tag in {"sup", "sub"}:
            tag = "super" if child.tag == "sup" else "sub"
            rise = "35%" if child.tag == "sup" else "15%"
            result.append('<' + tag + ' rise="' + rise + '" size="70%">' + paragraph_markup(child, bold, italic, heading) + "</" + tag + ">")
        else:
            result.append(paragraph_markup(child, bold, italic, heading))
    return "".join(result).strip()


class Equation(Flowable):
    """Draw MathText's individual glyphs as embedded PDF text, without rasterization."""
    FORMULAS = {
        1: r"A=\mathrm{Concat}\left(U(F_5),M(P_4),D(P_3)\right)",
        2: r"\Phi(A)=A+\mathcal{P}\!\left(A+\sum_{k\in\mathcal{K}}\mathrm{DW}_k(A)\right)",
        3: r"Z_4^{(2)}=\Phi_2\!\left(\mathrm{Align}\left(Z_5^{(1)},Z_4^{(1)},Z_3^{(1)}\right)\right)",
    }

    def __init__(self, number, width):
        super().__init__()
        from matplotlib.mathtext import MathTextParser
        from matplotlib.font_manager import FontProperties
        self.number, self.width = number, width
        self.vector = MathTextParser("path").parse(
            "$" + self.FORMULAS[number] + "$", dpi=72,
            prop=FontProperties(size=9, math_fontfamily="stix"),
        )
        self.height = self.vector.height + 11
        self.spaceBefore, self.spaceAfter = 3, 5

    def draw(self):
        c = self.canv
        x = max(0, (self.width - 22 - self.vector.width) / 2)
        baseline = self.vector.depth + 5
        for font, size, code, gx, gy in self.vector.glyphs:
            name = "Equation-" + Path(font.fname).stem
            if name not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont(name, str(font.fname)))
            if code not in pdfmetrics.getFont(name).face.charToGlyph:
                raise ValueError("Missing mathematical glyph: %s U+%04X" % (name, code))
            c.setFont(name, size)
            c.drawString(x + gx, baseline + gy, chr(code))
        for rx, ry, rw, rh in self.vector.rects:
            c.rect(x + rx, baseline + ry, rw, rh, stroke=0, fill=1)
        c.setFont("Latin", 8.5)
        c.drawRightString(self.width, baseline, "(%d)" % self.number)
