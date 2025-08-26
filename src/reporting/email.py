from __future__ import annotations
from typing import Iterable, List
import smtplib
from email.message import EmailMessage
from pathlib import Path

from src.utils.logging import getLogger

log = getLogger(__name__)


def send_email(
    smtp_host: str,
    smtp_port: int,
    username: str,
    password: str,
    to: List[str],
    subject: str,
    body: str,
    attachments: Iterable[Path],
    use_ssl: bool = False,
    from_addr: str = "noreply@example.com",
) -> None:
    """
    Отправка email с опциональными вложениями.
    Поддерживает SMTP и SMTP_SSL.
    """
    if not smtp_host:
        log.info("Email: smtp_host пустой → отправка пропущена")
        return

    msg = EmailMessage()
    msg["From"] = from_addr or username or "noreply@example.com"
    msg["To"] = ", ".join(to if isinstance(to, (list, tuple)) else [to])
    msg["Subject"] = subject
    msg.set_content(body or "")

    for p in attachments or []:
        try:
            p = Path(p)
            if not p.exists():
                continue
            with open(p, "rb") as fh:
                data = fh.read()
            maintype = "application"
            subtype = "octet-stream"
            msg.add_attachment(
                data, maintype=maintype, subtype=subtype, filename=p.name
            )
        except Exception:
            log.exception("Прикрепление файла %s не удалось (ignored)", p)

    try:
        if use_ssl:
            with smtplib.SMTP_SSL(smtp_host, int(smtp_port), timeout=10) as smtp:
                if username and password:
                    smtp.login(username, password)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(smtp_host, int(smtp_port), timeout=10) as smtp:
                if username and password:
                    smtp.login(username, password)
                smtp.send_message(msg)
        log.info("Email успешно отправлен.")
    except Exception:
        log.exception("Email отправить не удалось (ignored).")
