"""Prepare renamed, outline-converted Noto SC subsets for ReportLab.

The generated subsets are redistributed under the SIL Open Font License.
Only the conversion helper needs fontTools and the system Noto collections.
"""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
FONT_DIR = HERE / "fonts"
SOURCES = (
    ("CourseSerif-Regular", "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc", "Regular"),
    ("CourseSerif-Semibold", "/usr/share/fonts/opentype/noto/NotoSerifCJK-SemiBold.ttc", "Semibold"),
    ("CourseHei-Bold", "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", "Bold"),
)


def prepare():
    text = (HERE / "main_zh.html").read_text()
    characters = set(text) | set("0123456789（）〔〕，。；：、？！“”‘’—…±×−∑ΣΦφ∈𝒫")
    signature = hashlib.sha256("".join(sorted(characters)).encode()).hexdigest()
    marker = FONT_DIR / "SUBSETS.json"
    if marker.is_file():
        old = json.loads(marker.read_text())
        if old.get("character_signature") == signature and all(
            (FONT_DIR / (name + ".ttf")).is_file() for name, _, _ in SOURCES
        ):
            return
    from fontTools import subset
    from fontTools.ttLib import TTFont, newTable
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.pens.cu2quPen import Cu2QuPen

    FONT_DIR.mkdir(exist_ok=True)
    records = []
    for name, path, weight in SOURCES:
        font = TTFont(path, fontNumber=2)  # Simplified Chinese member.
        options = subset.Options()
        options.layout_features = []
        options.hinting = False
        worker = subset.Subsetter(options=options)
        worker.populate(unicodes={ord(c) for c in characters})
        worker.subset(font)
        glyph_set = font.getGlyphSet()
        glyphs = {}
        for glyph_name in font.getGlyphOrder():
            pen = TTGlyphPen(glyph_set)
            glyph_set[glyph_name].draw(Cu2QuPen(pen, max_err=0.5, reverse_direction=True))
            glyphs[glyph_name] = pen.glyph()
        del font["CFF "]
        for tag in ("VORG", "DSIG"):
            if tag in font:
                del font[tag]
        font.sfntVersion = "\x00\x01\x00\x00"
        font["glyf"] = newTable("glyf")
        font["glyf"].glyphs = glyphs
        font["loca"] = newTable("loca")
        font["maxp"] = newTable("maxp")
        font["maxp"].tableVersion = 0x00010000
        for key in ("maxTwilightPoints", "maxStorage", "maxFunctionDefs", "maxInstructionDefs", "maxStackElements", "maxSizeOfInstructions"):
            setattr(font["maxp"], key, 0)
        font["maxp"].maxZones = 2
        font["post"].formatType = 3.0
        family = name.rsplit("-", 1)[0]
        for record in list(font["name"].names):
            if record.nameID in (1, 2, 3, 4, 6, 16, 17):
                font["name"].names.remove(record)
        for name_id, value in ((1, family), (2, weight), (3, name), (4, name), (6, name), (16, family), (17, weight)):
            font["name"].setName(value, name_id, 3, 1, 0x409)
        target = FONT_DIR / (name + ".ttf")
        font.save(target)
        records.append({"file": target.name, "source": path.rsplit("/", 1)[-1], "collection_member": "SC", "glyphs": len(glyphs), "sha256": hashlib.sha256(target.read_bytes()).hexdigest()})
    marker.write_text(json.dumps({"character_signature": signature, "fonts": records}, indent=2) + "\n")


if __name__ == "__main__":
    prepare()
