#!/usr/bin/env python3
"""Build the BlueShare README3 first-person blog as a polished A4 PDF."""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "README3.md"
DEFAULT_OUTPUT = ROOT / "output" / "pdf" / "blueshare-sharing-moments-matters.pdf"

NAVY = colors.HexColor("#071522")
DEEP_BLUE = colors.HexColor("#0D2238")
BLUE = colors.HexColor("#37B8FF")
GREEN = colors.HexColor("#39C982")
AMBER = colors.HexColor("#E7A82F")
INK = colors.HexColor("#172536")
MUTED = colors.HexColor("#52677C")
PALE = colors.HexColor("#EAF6FD")
LINE = colors.HexColor("#BCD7E8")
WHITE = colors.white


def register_fonts() -> tuple[str, str, str]:
    font_dir = Path(r"C:\Windows\Fonts")
    candidates = {
        "regular": font_dir / "segoeui.ttf",
        "bold": font_dir / "segoeuib.ttf",
        "italic": font_dir / "segoeuii.ttf",
    }
    if all(path.is_file() for path in candidates.values()):
        pdfmetrics.registerFont(TTFont("BlueShareSans", str(candidates["regular"])))
        pdfmetrics.registerFont(TTFont("BlueShareSans-Bold", str(candidates["bold"])))
        pdfmetrics.registerFont(TTFont("BlueShareSans-Italic", str(candidates["italic"])))
        return "BlueShareSans", "BlueShareSans-Bold", "BlueShareSans-Italic"
    return "Helvetica", "Helvetica-Bold", "Helvetica-Oblique"


REGULAR, BOLD, ITALIC = register_fonts()


def styles() -> dict[str, ParagraphStyle]:
    sample = getSampleStyleSheet()
    return {
        "cover_title": ParagraphStyle(
            "CoverTitle",
            parent=sample["Title"],
            fontName=BOLD,
            fontSize=34,
            leading=38,
            textColor=BLUE,
            alignment=TA_LEFT,
            spaceAfter=8,
        ),
        "cover_subtitle": ParagraphStyle(
            "CoverSubtitle",
            parent=sample["Normal"],
            fontName=BOLD,
            fontSize=17,
            leading=22,
            textColor=WHITE,
            spaceAfter=20,
        ),
        "cover_body": ParagraphStyle(
            "CoverBody",
            parent=sample["Normal"],
            fontName=REGULAR,
            fontSize=11.5,
            leading=17,
            textColor=colors.HexColor("#B7CFE2"),
            spaceAfter=8,
        ),
        "h1": ParagraphStyle(
            "H1",
            parent=sample["Heading1"],
            fontName=BOLD,
            fontSize=24,
            leading=29,
            textColor=NAVY,
            spaceBefore=6,
            spaceAfter=10,
            keepWithNext=True,
        ),
        "h2": ParagraphStyle(
            "H2",
            parent=sample["Heading2"],
            fontName=BOLD,
            fontSize=16,
            leading=20,
            textColor=DEEP_BLUE,
            spaceBefore=13,
            spaceAfter=7,
            keepWithNext=True,
        ),
        "h3": ParagraphStyle(
            "H3",
            parent=sample["Heading3"],
            fontName=BOLD,
            fontSize=12.2,
            leading=15,
            textColor=colors.HexColor("#0D739E"),
            spaceBefore=9,
            spaceAfter=4,
            keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=sample["BodyText"],
            fontName=REGULAR,
            fontSize=10.1,
            leading=14.4,
            textColor=INK,
            spaceAfter=7,
        ),
        "caption": ParagraphStyle(
            "Caption",
            parent=sample["BodyText"],
            fontName=ITALIC,
            fontSize=8.2,
            leading=11,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceBefore=4,
            spaceAfter=10,
        ),
        "quote": ParagraphStyle(
            "Quote",
            parent=sample["BodyText"],
            fontName=ITALIC,
            fontSize=12.5,
            leading=18,
            textColor=DEEP_BLUE,
            leftIndent=14,
            rightIndent=14,
            borderColor=BLUE,
            borderWidth=0,
            borderPadding=10,
            backColor=PALE,
            spaceBefore=8,
            spaceAfter=12,
        ),
        "list": ParagraphStyle(
            "List",
            parent=sample["BodyText"],
            fontName=REGULAR,
            fontSize=9.8,
            leading=13.8,
            textColor=INK,
            leftIndent=0,
            spaceAfter=2,
        ),
        "code": ParagraphStyle(
            "Code",
            parent=sample["Code"],
            fontName="Courier",
            fontSize=8.2,
            leading=11.2,
            textColor=colors.HexColor("#DDF3FF"),
            leftIndent=0,
            rightIndent=0,
            spaceBefore=0,
            spaceAfter=0,
        ),
        "small": ParagraphStyle(
            "Small",
            parent=sample["BodyText"],
            fontName=REGULAR,
            fontSize=8.4,
            leading=11.5,
            textColor=MUTED,
        ),
    }


STYLES = styles()


def inline_markdown(text: str) -> str:
    value = html.escape(text, quote=True)
    value = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda match: (
            f'<link href="{match.group(2)}" color="#0878A8"><u>{match.group(1)}</u></link>'
        ),
        value,
    )
    value = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", value)
    value = re.sub(r"`([^`]+)`", r'<font name="Courier">\1</font>', value)
    value = re.sub(r"(?<!\*)\*([^*]+)\*", r"<i>\1</i>", value)
    return value


def draw_cover(canvas, doc) -> None:
    width, height = A4
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, width, height, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#0C314E"))
    canvas.circle(width - 18 * mm, height - 16 * mm, 44 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#0A263D"))
    canvas.circle(width - 3 * mm, 10 * mm, 55 * mm, fill=1, stroke=0)
    canvas.setFillColor(BLUE)
    canvas.rect(18 * mm, 18 * mm, 48 * mm, 2.2 * mm, fill=1, stroke=0)
    canvas.setTitle("BlueShare - Sharing Moments Matters")
    canvas.setAuthor("Nnamdi Michael Okpala")
    canvas.setSubject("BlueShare first-person user blog and Windows media-room guide")
    canvas.restoreState()


def draw_content_page(canvas, doc) -> None:
    width, height = A4
    canvas.saveState()
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.6)
    canvas.line(18 * mm, height - 15 * mm, width - 18 * mm, height - 15 * mm)
    canvas.setFont(BOLD, 8)
    canvas.setFillColor(colors.HexColor("#0D739E"))
    canvas.drawString(18 * mm, height - 11.5 * mm, "BLUESHARE - SHARING MOMENTS MATTERS")
    canvas.setFont(REGULAR, 7.8)
    canvas.setFillColor(MUTED)
    canvas.drawRightString(width - 18 * mm, 11 * mm, f"Page {doc.page}")
    canvas.drawString(18 * mm, 11 * mm, "Nnamdi Michael Okpala - okpalan@protonmail.com")
    canvas.restoreState()


def make_document(output: Path) -> BaseDocTemplate:
    output.parent.mkdir(parents=True, exist_ok=True)
    doc = BaseDocTemplate(
        str(output),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=22 * mm,
        bottomMargin=18 * mm,
        title="BlueShare - Sharing Moments Matters",
        author="Nnamdi Michael Okpala",
    )
    cover_frame = Frame(
        22 * mm,
        24 * mm,
        A4[0] - 44 * mm,
        A4[1] - 48 * mm,
        id="cover",
        showBoundary=0,
    )
    content_frame = Frame(
        18 * mm,
        24 * mm,
        A4[0] - 36 * mm,
        A4[1] - 46 * mm,
        id="content",
        showBoundary=0,
    )
    doc.addPageTemplates(
        [
            PageTemplate(id="cover", frames=[cover_frame], onPage=draw_cover, autoNextPageTemplate="content"),
            PageTemplate(id="content", frames=[content_frame], onPage=draw_content_page),
        ]
    )
    return doc


def cover_story() -> list:
    return [
        Spacer(1, 34 * mm),
        Paragraph("BlueShare", STYLES["cover_title"]),
        Paragraph("Sharing Moments Matters", STYLES["cover_subtitle"]),
        Spacer(1, 5 * mm),
        Paragraph("A first-person user story and Windows guide", STYLES["cover_body"]),
        Spacer(1, 11 * mm),
        Paragraph("By <b>Nnamdi Michael Okpala</b>", STYLES["cover_body"]),
        Paragraph("OBINexus Computing", STYLES["cover_body"]),
        Paragraph(
            '<link href="mailto:okpalan@protonmail.com" color="#37B8FF">okpalan@protonmail.com</link>',
            STYLES["cover_body"],
        ),
        Paragraph("BlueShare 0.2.0", STYLES["cover_body"]),
        Spacer(1, 28 * mm),
        Paragraph(
            "I created BlueShare because listening together should feel like a shared moment, "
            "even when every person uses a different laptop, speaker, or headset.",
            ParagraphStyle(
                "CoverQuote",
                parent=STYLES["cover_body"],
                fontName=ITALIC,
                fontSize=14,
                leading=21,
                textColor=WHITE,
            ),
        ),
        PageBreak(),
    ]


def markdown_image(path_text: str, alt_text: str) -> list:
    image_path = (ROOT / path_text).resolve()
    if not image_path.is_file():
        return [Paragraph(f"[Missing image: {html.escape(path_text)}]", STYLES["body"])]
    with PILImage.open(image_path) as source:
        width_px, height_px = source.size
    max_width = A4[0] - 40 * mm
    max_height = 175 * mm if height_px / width_px > 1.2 else 214 * mm
    scale = min(max_width / width_px, max_height / height_px)
    rendered = Image(str(image_path), width=width_px * scale, height=height_px * scale)
    rendered.hAlign = "CENTER"
    rendered._restrictSize(max_width, max_height)
    spacer = Paragraph(f"<i>{html.escape(alt_text)}</i>", STYLES["small"])
    return [KeepTogether([rendered, Spacer(1, 2 * mm), spacer])]


def code_block(code_lines: list[str]) -> list:
    content_width = A4[0] - 40 * mm
    code = Preformatted("\n".join(code_lines), STYLES["code"], maxLineLength=92)
    container = Table([[code]], colWidths=[content_width], hAlign="LEFT")
    container.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), NAVY),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#17405E")),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ]
        )
    )
    return [container, Spacer(1, 4 * mm)]


def is_special(line: str) -> bool:
    stripped = line.strip()
    return bool(
        not stripped
        or stripped.startswith("#")
        or stripped.startswith("```")
        or stripped.startswith("![")
        or stripped.startswith(">")
        or stripped.startswith("|")
        or re.match(r"^[-*] ", stripped)
        or re.match(r"^\d+\. ", stripped)
    )


def parse_markdown(source: Path) -> list:
    lines = source.read_text(encoding="utf-8").splitlines()
    start = next(index for index, line in enumerate(lines) if line.strip() == "## Why I built BlueShare")
    story: list = []
    index = start
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped:
            index += 1
            continue

        heading = re.match(r"^(#{1,3})\s+(.+)$", stripped)
        if heading:
            level = len(heading.group(1))
            story.append(Paragraph(inline_markdown(heading.group(2)), STYLES[f"h{level}"]))
            index += 1
            continue

        if stripped.startswith("```"):
            code_lines: list[str] = []
            index += 1
            while index < len(lines) and not lines[index].strip().startswith("```"):
                code_lines.append(lines[index])
                index += 1
            index += 1
            story.extend(code_block(code_lines))
            continue

        image_match = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", stripped)
        if image_match:
            story.extend(markdown_image(image_match.group(2), image_match.group(1)))
            index += 1
            continue

        if stripped.startswith(">"):
            quote_lines: list[str] = []
            while index < len(lines) and lines[index].strip().startswith(">"):
                quote_lines.append(lines[index].strip()[1:].strip())
                index += 1
            story.append(Paragraph(inline_markdown(" ".join(quote_lines)), STYLES["quote"]))
            continue

        if re.match(r"^[-*] ", stripped) or re.match(r"^\d+\. ", stripped):
            ordered = bool(re.match(r"^\d+\. ", stripped))
            items: list[ListItem] = []
            pattern = r"^\d+\.\s+" if ordered else r"^[-*]\s+"
            while index < len(lines) and re.match(pattern, lines[index].strip()):
                item_text = re.sub(pattern, "", lines[index].strip())
                index += 1
                while index < len(lines) and lines[index].startswith("   ") and lines[index].strip():
                    item_text += " " + lines[index].strip()
                    index += 1
                items.append(ListItem(Paragraph(inline_markdown(item_text), STYLES["list"])))
            list_options = {
                "bulletType": "1" if ordered else "bullet",
                "start": "1" if ordered else "-",
                "leftIndent": 18,
                "bulletFontName": BOLD,
                "bulletFontSize": 8.5,
                "bulletColor": colors.HexColor("#0D739E"),
                "spaceAfter": 8,
            }
            story.append(ListFlowable(items, **list_options))
            continue

        if stripped.startswith("|"):
            rows: list[list[str]] = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                cells = [cell.strip() for cell in lines[index].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
                    rows.append(cells)
                index += 1
            table_data = [
                [Paragraph(inline_markdown(cell), STYLES["small"]) for cell in row]
                for row in rows
            ]
            table = Table(table_data, colWidths=[50 * mm, 120 * mm], repeatRows=1, hAlign="LEFT")
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), DEEP_BLUE),
                        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                        ("FONTNAME", (0, 0), (-1, 0), BOLD),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F4FAFD")),
                        ("GRID", (0, 0), (-1, -1), 0.4, LINE),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ]
                )
            )
            story.extend([table, Spacer(1, 4 * mm)])
            continue

        paragraph_lines = [stripped]
        index += 1
        while index < len(lines) and not is_special(lines[index]):
            paragraph_lines.append(lines[index].strip())
            index += 1
        paragraph_text = " ".join(paragraph_lines)
        style = STYLES["caption"] if paragraph_text.startswith("*Figure ") else STYLES["body"]
        story.append(Paragraph(inline_markdown(paragraph_text), style))

    return story


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output = args.output.resolve()
    document = make_document(output)
    story = cover_story() + parse_markdown(SOURCE)
    document.build(story)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
