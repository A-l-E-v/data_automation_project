from __future__ import annotations
from pathlib import Path
from typing import Dict
import pandas as pd

from src.utils.logging import getLogger
from src.reporting.pdf import to_pdf

log = getLogger(__name__)


def build_pdf(
    images_with_captions: list[tuple[str, str]],
    agg_df: pd.DataFrame,
    pdf_cfg: Dict,
    extra_tables: list[tuple[str, list[list[str]]]],
) -> str | None:
    """
    Формирует тело отчёта через to_pdf(...) и подшивает первым листом внешний PDF
    (по умолчанию assets/preface.pdf) как титульную страницу.
    """
    final_out = Path(pdf_cfg.get("output", "reports/pdf/report.pdf"))
    pdf_dir = final_out.parent
    pdf_dir.mkdir(parents=True, exist_ok=True)

    tmp_body = pdf_dir / "__body_tmp.pdf"

    # --- 1) Генерируем тело отчёта во временный файл
    meta = {
        # ничего «лишнего» не добавляем, всё берём из конфигурации
        "title": pdf_cfg.get("title", "Сводный отчёт по продажам"),
        "author": pdf_cfg.get(
            "author", ""
        ),  # пусто — чтобы не печатать строку "Автор:" его перенёс на титул
        "intro_paragraphs": pdf_cfg.get("intro_extra", []) or [],
    }
    try:
        comp_rows = agg_df.to_dict(orient="records") if not agg_df.empty else []
        to_pdf(
            images_with_captions,
            pdf_dir,
            filename=tmp_body.name,
            meta=meta,
            comparison_aggregates=comp_rows,
            extra_tables=extra_tables,
            compact=True,
        )
    except Exception as e:
        log.exception("Ошибка при формировании PDF (тело): %s", e)
        return None

    # --- 2) Подшиваем титульную страницу из внешнего файла
    preface_path = Path(pdf_cfg.get("preface_path", "assets/preface.pdf"))

    try:
        from pypdf import PdfReader, PdfWriter

        writer = PdfWriter()

        # Добавляем первую страницу из preface.pdf (если он есть)
        if preface_path.exists():
            try:
                pref_reader = PdfReader(str(preface_path))
                if len(pref_reader.pages) > 0:
                    writer.add_page(pref_reader.pages[0])
                else:
                    log.warning(
                        "preface.pdf найден, но страниц нет — пропускаю титульный лист."
                    )
            except Exception as e:
                log.warning(
                    "Не удалось прочитать preface.pdf (%s) — пропускаю титульный лист.",
                    e,
                )

        # Затем — всё тело отчёта
        body_reader = PdfReader(str(tmp_body))
        for page in body_reader.pages:
            writer.add_page(page)

        with open(final_out, "wb") as f:
            writer.write(f)

    except Exception as e:
        log.exception("Не удалось объединить титульный лист с отчётом: %s", e)
        # Фоллбэк — просто оставляем тело отчёта как финальный PDF
        tmp_body.replace(final_out)
    finally:
        # Чистим временный файл
        try:
            if tmp_body.exists():
                tmp_body.unlink()
        except Exception:
            pass

    return str(final_out)
