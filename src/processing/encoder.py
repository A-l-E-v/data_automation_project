"""
smart_encode(df, cfg)

Возвращает (df_encoded, encoded_columns_list).

Логика:
- Опирается на cfg (например cfg = config['processing']['cleaning']['encode_categorical'])
- По умолчанию max_onehot_unique = 10
- Приводит list/tuple/dict колонки к строкам (через coerce_list_columns_to_strings) перед кодированием
- Исключает из кодирования колонки, перечисленные в cfg['exclude_onehot']
- Выбирает кандидатов в code = object / category колонки с nunique <= max_onehot_unique
- Вызывает pd.get_dummies для выбранных колонок
- Возвращает новый df (без inplace)
"""

from __future__ import annotations
from typing import Dict, Any, Iterable, List, Tuple, Optional
import logging
import pandas as pd

log = logging.getLogger(__name__)

# импортируем функцию приведения list-колонок в строки из cleaner
try:
    from src.processing.cleaner import coerce_list_columns_to_strings
except Exception:
    # fallback - если модуль недоступен, реализуем простую локальную функцию
    import json

    def coerce_list_columns_to_strings(
        df: pd.DataFrame, sample_n: int = 100
    ) -> pd.DataFrame:
        df = df.copy()

        def _is_list_like(x):
            return isinstance(x, (list, tuple, set, dict))

        cols = []
        for col in df.columns:
            try:
                vals = df[col].dropna().head(sample_n).tolist()
            except Exception:
                continue
            for v in vals:
                if _is_list_like(v):
                    cols.append(col)
                    break
        for c in cols:

            def _conv(v):
                try:
                    if isinstance(v, set):
                        v = list(v)
                    if isinstance(v, (list, tuple, dict)):
                        return json.dumps(v, ensure_ascii=False, sort_keys=True)
                    return v
                except Exception:
                    try:
                        return str(v)
                    except Exception:
                        return None

            df[c] = df[c].apply(_conv)
        return df


def smart_encode(
    df: pd.DataFrame, cfg: Optional[Dict[str, Any]] = None
) -> Tuple[pd.DataFrame, List[str]]:
    """
    df -> df_encoded, encoded_columns

    Ключи cfg:
      - max_onehot_unique: int (по умолчанию 10)
      - exclude_onehot: список названий столбцов, которые никогда не кодировать one-hot
      - coerce_list_columns_to_strings: bool (по умолчанию True)
      - ignore_errors: bool (по умолчанию True)
    """
    if df is None:
        return df, []

    _cfg = cfg or {}
    max_onehot_unique = int(_cfg.get("max_onehot_unique", 10))
    exclude_onehot = (
        list(_cfg.get("exclude_onehot", [])) if _cfg.get("exclude_onehot") else []
    )
    coerce_lists = bool(_cfg.get("coerce_list_columns_to_strings", True))
    ignore_errors = bool(_cfg.get("ignore_errors", True))

    df = df.copy()

    # сначала приводим list-like столбцы к строкам (иначе: unhashable type: 'list')
    if coerce_lists:
        try:
            df = coerce_list_columns_to_strings(df)
        except Exception:
            log.exception(
                "smart_encode: coerce_list_columns_to_strings failed (ignored)"
            )
            if not ignore_errors:
                raise

    # Выберем кандидатов для OHE: object/categorical колонки, не в exclude, с небольшим числом уникальных значений.
    obj_cols = list(df.select_dtypes(include=["object", "category"]).columns)
    candidates = []
    for c in obj_cols:
        if c in exclude_onehot:
            log.debug("smart_encode: excluded by config: %s", c)
            continue
        try:
            nunique = df[c].nunique(dropna=True)
        except Exception:
            log.debug(
                "smart_encode: cannot compute nunique for %s, skipping",
                c,
                exc_info=False,
            )
            continue
        # пропускаем колонки, где все значения уникальны (например текст/описания)
        if nunique <= max_onehot_unique and nunique > 1:
            candidates.append(c)

    if not candidates:
        log.info(
            "smart_encode: no candidate columns for one-hot encoding (max_onehot_unique=%s)",
            max_onehot_unique,
        )
        return df, []

    log.info("smart_encode: one-hot encoding candidates: %s", candidates)

    # Выполним OHE
    try:
        df_encoded = pd.get_dummies(
            df, columns=candidates, dummy_na=False, drop_first=False
        )
        log.info("smart_encode: applied one-hot to %s columns", len(candidates))
        return df_encoded, candidates
    except Exception:
        log.exception("smart_encode: get_dummies failed", exc_info=False)
        if not ignore_errors:
            raise
        # в случае ошибки возвращаем оригинал
        return df, []


# Если требуется: простой wrapper, чтобы pipeline мог вызывать encode_categorical(df, mode_cfg)
def encode_categorical(
    df: pd.DataFrame, mode_cfg: Optional[Dict[str, Any]] = None
) -> pd.DataFrame:
    """
    Простая совместимость с существующим pipeline: возвращает DataFrame (без списка колонок).
    """
    out, _ = smart_encode(df, cfg=mode_cfg or {})
    return out
