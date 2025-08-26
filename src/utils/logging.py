from __future__ import annotations
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys
import os
from typing import Union


def _resolve_log_file(log_path: Union[str, Path]) -> Path:
    """
    Дан путь, который может быть каталогом или именем файла. Вернуть объект Path к файлу.
    Правила:
    - Если переданный путь существует и это каталог → использовать <path>/app.log
    - Если переданный путь оканчивается разделителем пути → считать каталогом → использовать <path>/app.log
    - Если у переданного пути есть суффикс (например, .лог) → считать файлом
    - Если у переданного пути нет суффикса → считать каталогом и использовать <path>/app.log
    """
    p = Path(log_path)
    # явно передан каталог
    if p.exists() and p.is_dir():
        return p / "app.log"
    # заканчивается разделителем пути → считаем каталогом
    s = str(log_path)
    if s.endswith(os.sep) or s.endswith("/") or s.endswith("\\"):
        return p / "app.log"
    # если нет суффикса → считаем каталогом (частый случай, когда указывают "logs")
    if p.suffix == "":
        return p / "app.log"
    # иначе считаем, что это путь к файлу
    return p


def setup_logging(
    log_path: Union[str, Path] = "logs", level: Union[str, int] = "INFO"
) -> None:
    """
    Настраивает корневой логгер: консоль + файловый обработчик с ротацией.
    Принимает путь к файлу или каталогу; если передан каталог (или путь без суффикса),
    фактический файл логов будет <каталог>/app.log.
    """
    lp = _resolve_log_file(log_path)
    lp.parent.mkdir(parents=True, exist_ok=True)

    numeric_level = getattr(
        logging, level if isinstance(level, str) else str(level), logging.INFO
    )
    fmt = "%(asctime)s | %(levelname)-7s | %(name)s:%(lineno)d - %(message)s"
    root = logging.getLogger()
    root.setLevel(numeric_level)

    # убираем уже добавленные обработчики, чтобы не дублировать логи при повторной настройке
    for h in list(root.handlers):
        root.removeHandler(h)

    # консольный обработчик
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(numeric_level)
    ch.setFormatter(logging.Formatter(fmt))
    root.addHandler(ch)

    # файловый обработчик (с ротацией) — обёрнут в try/except, чтобы не падать, если файл нельзя открыть
    try:
        fh = RotatingFileHandler(
            str(lp), maxBytes=5_000_000, backupCount=5, encoding="utf-8"
        )
        fh.setLevel(numeric_level)
        fh.setFormatter(logging.Formatter(fmt))
        root.addHandler(fh)
        logging.getLogger(__name__).info(
            "Логирование настроено. Файл: %s, уровень: %s",
            str(lp),
            logging.getLevelName(numeric_level),
        )
    except Exception:
        # если файловый обработчик не удалось создать, оставляем только консольный лог и не завершаем программу
        logging.getLogger(__name__).exception(
            "Не удалось создать файловый обработчик логов (%s). Включён только консольный лог.",
            lp,
        )


def getLogger(name: str | None = None) -> logging.Logger:
    """
    Обёртка над logging.getLogger для единообразного импорта по всему проекту.
    """
    return logging.getLogger(name)
