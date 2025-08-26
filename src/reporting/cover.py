# TODO оставил на будущее - сейчас просто пришиваю титульник из пдф.

from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

# Visual constants
UNI_FS = 18
PROJ_TYPE_FS = 20
COURSE_FS = 14
TITLE_FS = 26
INFO_FS = 14


def _register_fonts(font_dir: Path) -> None:
    regular = font_dir / "DejaVuSans.ttf"
    bold = font_dir / "DejaVuSans-Bold.ttf"
    if regular.exists():
        pdfmetrics.registerFont(TTFont("DejaVu", str(regular)))
    if bold.exists():
        pdfmetrics.registerFont(TTFont("DejaVu-Bold", str(bold)))


def _wrap_center(
    c: canvas.Canvas, text: str, font: str, size: int, max_w: float
) -> list[str]:
    # naive word wrap by measured width
    words = text.split()
    line = ""
    lines = []
    for w in words:
        probe = (line + " " + w).strip()
        if pdfmetrics.stringWidth(probe, font, size) <= max_w:
            line = probe
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines


def build_cover_pdf(cfg: Dict[str, Any], output_path: Path) -> str:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fonts_dir = Path(cfg.get("fonts_dir", "assets/fonts"))
    _register_fonts(fonts_dir)

    c = canvas.Canvas(str(output_path), pagesize=A4)
    width, height = A4

    left = 64
    right = 64
    top = 64
    bottom = 48

    y = height - top

    # 1) Logo (top-left), small and neat
    logo_path = cfg.get("logo_path")
    if logo_path:
        try:
            img = ImageReader(str(logo_path))
            target_w = 115
            iw, ih = img.getSize()
            ratio = target_w / float(iw)
            target_h = ih * ratio
            c.drawImage(
                img, left, y - target_h, width=target_w, height=target_h, mask="auto"
            )
        except Exception:
            pass

    # 2) University (centered)
    y -= 10
    c.setFont("DejaVu", UNI_FS)
    uni = cfg.get("university", "")
    if uni:
        c.drawCentredString(width / 2, y, uni)

    # spacing
    y -= 60

    # 3) Project type (centered, slightly larger)
    c.setFont("DejaVu", PROJ_TYPE_FS)
    proj_type = cfg.get("project_type", "")
    if proj_type:
        c.drawCentredString(width / 2, y, proj_type)

    # 4) Course line
    y -= 28
    c.setFont("DejaVu", COURSE_FS)
    course = cfg.get("course", "")
    if course:
        c.drawCentredString(width / 2, y, course)

    # 5) Title (bold, wrapped, larger, center)
    y -= 42
    title = cfg.get("project_title", "")
    if title:
        lines = _wrap_center(c, title, "DejaVu-Bold", TITLE_FS, width - (left + right))
        c.setFont("DejaVu-Bold", TITLE_FS)
        for ln in lines:
            c.drawCentredString(width / 2, y, ln)
            y -= TITLE_FS + 10

    # 6) Student & group block (left-aligned, lower on page)
    y -= 20
    c.setFont("DejaVu", INFO_FS)
    stud = cfg.get("student", "")
    grp = cfg.get("group", "")
    if stud:
        c.drawString(left, y, stud)
        y -= INFO_FS + 6
    if grp:
        c.drawString(left, y, grp)
        y -= INFO_FS + 6

    # 7) City/year (bottom centered)
    c.setFont("DejaVu", INFO_FS)
    city_year = cfg.get("city_year", "")
    if city_year:
        c.drawCentredString(width / 2, bottom, city_year)

    c.showPage()
    c.save()
    return str(output_path)
