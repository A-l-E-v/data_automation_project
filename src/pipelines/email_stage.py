from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Any

from src.reporting.email import send_email
from src.utils.logging import getLogger

logger = getLogger(__name__)


def send_email_with_artifacts(cfg: Dict[str, Any], artifacts: Dict[str, Any]) -> None:
    """
    Отправляет письмо со всеми артефактами (pdf, excel, изображения).
    Совместимо с вызовом из runner.py.
    """
    if not cfg:
        logger.info("email: конфиг отсутствует — пропускаем отправку")
        return

    if str(cfg.get("enabled", "true")).lower() in {"false", "0", "no"}:
        logger.info("email: отключён через config — пропускаем отправку")
        return

    # Соберём список вложений
    attachments: List[Path] = []
    if artifacts:
        for key in ("pdf", "excel"):
            p = artifacts.get(key)
            if p:
                attachments.append(Path(p))
        for p in artifacts.get("images", []) or []:
            attachments.append(Path(p))

    try:
        send_email(
            smtp_host=cfg.get("smtp", {}).get("host") or cfg.get("smtp_host"),
            smtp_port=int(cfg.get("smtp", {}).get("port", cfg.get("smtp_port", 25))),
            username=cfg.get("username", ""),
            password=cfg.get("password", ""),
            to=cfg.get("to", []),
            subject=cfg.get("subject", "Pipeline report"),
            body=cfg.get("body", ""),
            attachments=attachments,
            use_ssl=bool(cfg.get("smtp", {}).get("use_ssl", cfg.get("use_ssl", False))),
            from_addr=cfg.get("from", cfg.get("from_addr", "noreply@example.com")),
        )
        logger.info("email: письмо отправлено (вложений: %d)", len(attachments))
    except Exception as e:
        logger.error("email: ошибка при отправке (ignored): %s", e)
