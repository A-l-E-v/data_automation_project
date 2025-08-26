from __future__ import annotations
from pathlib import Path
from typing import List, Tuple, Dict, Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    Table,
    TableStyle,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader


# --- кириллица ---
def _register_fonts():
    tried = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/local/share/fonts/DejaVuSans.ttf",
        "DejaVuSans.ttf",
    ]
    for p in tried:
        try:
            pdfmetrics.registerFont(TTFont("DejaVuSans", p))
            return "DejaVuSans"
        except Exception:
            continue
    return "Helvetica"


_FONT = _register_fonts()


# --- стили (чуть больше интервалов) ---
def _h1(text: str) -> Paragraph:
    return Paragraph(
        text,
        ParagraphStyle(
            name="H1",
            fontName=_FONT,
            fontSize=16,
            leading=19,
            spaceAfter=8,
            textColor=colors.HexColor("#111"),
        ),
    )


def _h2(text: str) -> Paragraph:
    return Paragraph(
        text,
        ParagraphStyle(
            name="H2",
            fontName=_FONT,
            fontSize=12,
            leading=14,
            spaceBefore=8,
            spaceAfter=6,
            textColor=colors.HexColor("#222"),
        ),
    )


def _p(text: str) -> Paragraph:
    # «чуть-чуть больше свободного пространства»
    return Paragraph(
        text,
        ParagraphStyle(
            name="P",
            fontName=_FONT,
            fontSize=10,
            leading=12,
            spaceBefore=0,
            spaceAfter=8,
        ),
    )


def _table(data: List[List[Any]], compact: bool = False) -> Table:
    if not data:
        data = [["нет данных"]]
    tbl = Table(data)
    base_style = [
        ("FONTNAME", (0, 0), (-1, -1), _FONT),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f0f0")),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]
    if compact:
        base_style += [
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("LEADING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ]
    else:
        base_style += [
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("LEADING", (0, 0), (-1, -1), 12),
        ]
    tbl.setStyle(TableStyle(base_style))
    return tbl


# --- helper: вставка изображения с сохранением пропорций ---
def _image_fit(
    img_path: str, max_w: float = 480, max_h: float = 300, h_align: str = "CENTER"
) -> Image:
    ir = ImageReader(img_path)
    iw, ih = ir.getSize()
    # масштаб с сохранением пропорций в рамку max_w x max_h
    scale = min(max_w / iw, max_h / ih)
    w, h = iw * scale, ih * scale
    im = Image(img_path, width=w, height=h)
    im.hAlign = h_align
    return im


def to_pdf(
    images_with_captions: List[Tuple[str, str]],
    out_dir: Path,
    filename: str = "report.pdf",
    meta: Dict[str, Any] | None = None,
    comparison_aggregates: List[Dict[str, Any]] | None = None,
    extra_tables: List[Tuple[str, List[List[str]]]] | None = None,
    compact: bool = False,
) -> str:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / filename

    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    story: List[Any] = []

    meta = meta or {}
    title = meta.get("title", "Отчёт")
    author = meta.get("author", "Pipeline")
    intro = meta.get("intro_paragraphs", [])

    story.append(_h1(title))
    for t in intro:
        story.append(_p(t))

    # Таблицы: плотные, с H2-заголовками
    if extra_tables:
        for title_or_h2, rows in extra_tables:
            if title_or_h2.startswith("## "):
                story.append(_h2(title_or_h2[3:]))
            elif rows:
                story.append(_p(title_or_h2))
            if rows:
                story.append(_table(rows, compact=True if compact else False))

    # Картинки (сохранение пропорций; квадратные остаются квадратными)
    for i, (img_path, caption) in enumerate(images_with_captions, 1):
        story.append(Spacer(1, 6 if compact else 10))
        story.append(_p(f"Рисунок {i}. {Path(img_path).name}"))
        story.append(_image_fit(img_path, max_w=480, max_h=300, h_align="CENTER"))
        if caption:
            story.append(_p(caption))

    doc.build(story)
    return str(path)
