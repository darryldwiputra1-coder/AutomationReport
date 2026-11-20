"""Create downloadable Galaxy research briefs in memory."""
from io import BytesIO
import json
from xml.sax.saxutils import escape, quoteattr

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer


def evidence_text(row):
    if row["kind"] != "price":
        return row["title"]
    text = f'{row["title"]} · {row["value"]}'
    if row["change_pct"] is not None:
        text += f' · {row["change_pct"]:+.2f}% from {row["points"][0][0]}'
    return text


def section_items(section):
    for row in section["rows"]:
        label = "Market data" if row["kind"] == "price" else "Headline lead"
        yield label, f'{evidence_text(row)} [{row["id"]}]', row
    for finding in section["ai"]:
        yield "AI interpretation", f'{finding["text"]} [{", ".join(finding["evidence_ids"])}]', None
    for item in section["watch"]:
        yield "Watch", item, None
    for item in section["gaps"]:
        yield "Source gap", item, None


def _stamp(report):
    return f'{report["method"]} | {report["window_start"]} to {report["generated_at"][:10]} | Jakarta time'


def _pdf(report):
    buffer = BytesIO()
    styles = getSampleStyleSheet()
    styles["Heading1"].textColor = colors.HexColor("#101a33")
    styles["Heading2"].textColor = colors.HexColor("#101a33")
    styles["BodyText"].leading = 14
    story = [
        Paragraph("Galaxy IMMA Horizon", styles["Heading1"]),
        Paragraph("Market research brief", styles["Title"]),
        Paragraph(escape(_stamp(report)), styles["BodyText"]),
        Paragraph("Daily price snapshots may include an open session. Headlines are research leads.",
                  styles["BodyText"]),
    ]
    for section in report["sections"]:
        heading = Paragraph(escape(section["name"]), styles["Heading2"])
        entries = []
        for label, text, source in section_items(section):
            detail = f"<b>{escape(label)}</b> · {escape(text)}"
            if source:
                link_text = escape(f'{source["source"]} · {source["date"]}')
                detail += f'<br/><link color="#095687" href={quoteattr(source["url"])}>{link_text}</link>'
            entries.append(Paragraph(detail, styles["BodyText"]))
        story.extend([Spacer(1, 10), KeepTogether([heading, entries[0]]), *entries[1:]])
    SimpleDocTemplate(buffer, title="Galaxy IMMA Horizon | Market research brief",
                      author="Galaxy IMMA Horizon").build(story)
    return buffer.getvalue()


def _rgb(hex_color):
    return RGBColor.from_string(hex_color)


def _box(slide, x, y, width, height, value, size, color, *, bold=False, url=None):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(width), Inches(height))
    frame = box.text_frame
    frame.word_wrap = True
    frame.margin_left = frame.margin_right = Pt(0)
    frame.margin_top = frame.margin_bottom = Pt(0)
    run = frame.paragraphs[0].add_run()
    run.text = value
    if url:
        run.hyperlink.address = url
    run.font.name = "Aptos"
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = _rgb(color)


def _powerpoint(report):
    deck = Presentation()
    deck.slide_width, deck.slide_height = Inches(13.333), Inches(7.5)
    for section in report["sections"]:
        entries = list(section_items(section))
        for offset in range(0, len(entries), 4):
            slide = deck.slides.add_slide(deck.slide_layouts[6])
            slide.background.fill.solid()
            slide.background.fill.fore_color.rgb = _rgb("0A1229")
            _box(slide, .65, .36, 12, .26, "GALAXY IMMA HORIZON", 12, "57DBFF", bold=True)
            _box(slide, .65, .77, 12, .9, section["name"], 24, "F2F6FF", bold=True)
            _box(slide, .65, 1.72, 12, .33, _stamp(report), 12, "ADC0E1")
            for line, (label, text, source) in enumerate(entries[offset:offset + 4]):
                y = 2.15 + 1.18 * line
                _box(slide, .65, y, 12, .24, label.upper(), 10, "57DBFF", bold=True)
                _box(slide, .65, y + .25, 12, .65, text, 15, "F2F6FF")
                if source:
                    source_text = f'{source["source"]} · {source["date"]} · open source'
                    _box(slide, .65, y + .91, 12, .22, source_text, 10, "ADC0E1", url=source["url"])
    buffer = BytesIO()
    deck.save(buffer)
    return buffer.getvalue()


def build_exports(report):
    return (
        _pdf(report),
        _powerpoint(report),
        json.dumps(report, indent=2, ensure_ascii=False).encode("utf-8"),
    )
