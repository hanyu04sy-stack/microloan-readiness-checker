from __future__ import annotations

import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "TRADE_OFF_REPORT.md"
TARGET = ROOT / "output" / "pdf" / "SUN_HANYU_PE6201_Trade_Off_Report.pdf"


def inline_markup(text: str) -> str:
    parts = re.split(r"(`[^`]+`)", text)
    rendered: list[str] = []
    for part in parts:
        if part.startswith("`") and part.endswith("`"):
            rendered.append(
                f'<font name="Courier" color="#174A5B">{html.escape(part[1:-1])}</font>'
            )
            continue
        escaped = html.escape(part)
        escaped = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", escaped)
        escaped = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", escaped)
        rendered.append(escaped)
    return "".join(rendered)


def parse_table(lines: list[str], start: int, body_style: ParagraphStyle) -> tuple[Table, int]:
    rows: list[list[str]] = []
    index = start
    while index < len(lines) and lines[index].strip().startswith("|"):
        raw = [cell.strip() for cell in lines[index].strip().strip("|").split("|")]
        if not all(re.fullmatch(r":?-+:?", cell) for cell in raw):
            rows.append(raw)
        index += 1
    data = [
        [Paragraph(f"<b>{inline_markup(cell)}</b>" if row_index == 0 else inline_markup(cell), body_style)
         for cell in row]
        for row_index, row in enumerate(rows)
    ]
    widths = [44 * mm, 18 * mm, 18 * mm, 15 * mm, 11 * mm, 11 * mm, 11 * mm, 11 * mm, 23 * mm]
    table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#123B4A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F2F7F8")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#9DB5BE")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return table, index


def footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#BCD1D8"))
    canvas.line(20 * mm, 14 * mm, 190 * mm, 14 * mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#536A73"))
    canvas.drawString(20 * mm, 9 * mm, "PE6201 Trade-off Report")
    canvas.drawRightString(190 * mm, 9 * mm, str(doc.page))
    canvas.restoreState()


def build() -> None:
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleCustom", parent=styles["Title"], fontName="Helvetica-Bold",
        fontSize=20, leading=24, textColor=colors.HexColor("#123B4A"),
        alignment=TA_CENTER, spaceAfter=5 * mm,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle", parent=styles["Heading2"], fontName="Helvetica-Bold",
        fontSize=13, leading=16, textColor=colors.HexColor("#2C6570"),
        alignment=TA_CENTER, spaceAfter=5 * mm,
    )
    heading_style = ParagraphStyle(
        "Heading", parent=styles["Heading2"], fontName="Helvetica-Bold",
        fontSize=13, leading=16, textColor=colors.HexColor("#123B4A"),
        spaceBefore=4 * mm, spaceAfter=2 * mm, keepWithNext=True,
    )
    body_style = ParagraphStyle(
        "Body", parent=styles["BodyText"], fontName="Helvetica",
        fontSize=9.3, leading=13.1, textColor=colors.HexColor("#17242A"),
        spaceAfter=2.4 * mm,
    )
    meta_style = ParagraphStyle(
        "Meta", parent=body_style, alignment=TA_CENTER, leading=14,
        textColor=colors.HexColor("#435C65"), spaceAfter=1 * mm,
    )
    bullet_style = ParagraphStyle(
        "Bullet", parent=body_style, leftIndent=5 * mm, firstLineIndent=-3 * mm,
        bulletIndent=1 * mm, spaceAfter=1.5 * mm,
    )
    code_style = ParagraphStyle(
        "Code", parent=body_style, fontName="Courier", fontSize=8.2,
        leading=11, leftIndent=5 * mm, rightIndent=5 * mm,
        backColor=colors.HexColor("#EDF5F6"), borderColor=colors.HexColor("#BCD1D8"),
        borderWidth=0.5, borderPadding=6, spaceBefore=1 * mm, spaceAfter=3 * mm,
    )

    doc = BaseDocTemplate(
        str(TARGET), pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=18 * mm, bottomMargin=20 * mm,
        title="AI-Assisted Microloan Application Readiness Checker - Trade-off Report",
        author="Sun Hanyu",
        subject="PE6201 Emerging AI Technologies Individual End-of-Course Project",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")
    doc.addPageTemplates(PageTemplate(id="report", frames=[frame], onPage=footer))

    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    story = []
    index = 0
    paragraph_buffer: list[str] = []

    def flush_paragraph() -> None:
        if paragraph_buffer:
            story.append(Paragraph(inline_markup(" ".join(paragraph_buffer)), body_style))
            paragraph_buffer.clear()

    while index < len(lines):
        line = lines[index].rstrip()
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            index += 1
            continue
        if stripped.startswith("|:") or stripped.startswith("|-"):
            index += 1
            continue
        if stripped.startswith("|"):
            flush_paragraph()
            table, index = parse_table(lines, index, body_style)
            story.extend([table, Spacer(1, 2 * mm)])
            continue
        if stripped.startswith("# "):
            flush_paragraph()
            story.append(Spacer(1, 7 * mm))
            story.append(Paragraph(inline_markup(stripped[2:]), title_style))
        elif stripped.startswith("## Trade-off Report"):
            flush_paragraph()
            story.append(Paragraph("Trade-off Report", subtitle_style))
        elif stripped.startswith("## "):
            flush_paragraph()
            story.append(Paragraph(inline_markup(stripped[3:]), heading_style))
        elif stripped.startswith("**Name:") or stripped.startswith("**Course:") or stripped.startswith("**Programme:"):
            flush_paragraph()
            story.append(Paragraph(inline_markup(stripped.rstrip("  ")), meta_style))
        elif stripped.startswith("- "):
            flush_paragraph()
            story.append(Paragraph(inline_markup(stripped[2:]), bullet_style, bulletText="•"))
        elif stripped.startswith("`") and stripped.endswith("`."):
            flush_paragraph()
            story.append(Paragraph(inline_markup(stripped[:-1]), code_style))
        else:
            paragraph_buffer.append(stripped)
        index += 1
    flush_paragraph()
    doc.build(story)
    print(TARGET)


if __name__ == "__main__":
    build()
