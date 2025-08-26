from __future__ import annotations
from pathlib import Path
from typing import Optional, Union, Dict, Any
import pandas as pd
import requests
import logging
import json
import math
from urllib.parse import urljoin

log = logging.getLogger(__name__)


def load_csv(path: Union[str, Path], **kwargs) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"CSV not found: {p}")
    df = pd.read_csv(p, **kwargs)
    log.info("CSV loaded: %s shape=%s", p, getattr(df, "shape", None))
    return df


def load_excel(
    path: Union[str, Path], sheet_name: Optional[str] = None, **kwargs
) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Excel not found: {p}")
    df = pd.read_excel(p, sheet_name=sheet_name, **kwargs)
    # если указан sheet_name — вернётся DataFrame; иначе pandas возвращает dict — обработаем это
    if isinstance(df, dict):
        # берём первый лист
        first = list(df.keys())[0]
        df = df[first]
    log.info(
        "Excel loaded: %s sheet=%s shape=%s", p, sheet_name, getattr(df, "shape", None)
    )
    return df


def load_sql(conn_str: str, query: str):
    # заглушка — пользователь может реализовать специфику БД сам
    raise NotImplementedError("load_sql not implemented in this environment")


def _extract_json_root(resp_json: dict, json_root: Optional[str]):
    if not json_root:
        return resp_json
    # поддержка вложенных корней вида "data.items"
    parts = json_root.split(".")
    v = resp_json
    for p in parts:
        if isinstance(v, dict) and p in v:
            v = v[p]
        else:
            return resp_json
    return v


def call_api(
    url: Union[str, dict],
    method: str = "GET",
    params: Optional[dict] = None,
    headers: Optional[dict] = None,
    json_root: Optional[str] = None,
    paginate: Optional[dict] = None,
    save_as: Optional[str] = None,
    timeout: int = 10,
    verify: bool = True,
) -> pd.DataFrame:
    """
    Надёжный вызов API:
    - принимает либо строковый url, либо словарь описания эндпоинта (ключи: url, method, params, json_root, paginate, save_as)
    - поддерживает простую пагинацию через параметры skip/limit или page, если передан словарь paginate
    - возвращает pandas.DataFrame (по возможности «сплющивая» вложенные объекты)
    """
    # поддержка формата словаря описания эндпоинта
    if isinstance(url, dict):
        ep = url
        url = ep.get("url")
        method = ep.get("method", method)
        params = ep.get("params", params)
        headers = ep.get("headers", headers)
        json_root = ep.get("json_root", json_root)
        paginate = ep.get("paginate", paginate)
        save_as = ep.get("save_as", save_as)

    if not url or not isinstance(url, str):
        raise ValueError("Invalid URL for call_api")

    sess = requests.Session()
    sess.headers.update(headers or {})
    all_items = []
    try:
        if paginate and paginate.get("enabled"):
            # базовая поддержка пагинации: ожидаются limit/skip или соглашение с page в словаре paginate
            limit_param = paginate.get("limit_param", "limit")
            skip_param = paginate.get("skip_param", "skip")
            page_limit = int(paginate.get("page_limit", 100))
            max_pages = int(paginate.get("max_pages", 100))
            response_total_key = paginate.get("response_total_key")
            offset = params.get(skip_param, 0) if params else 0
            limit = params.get(limit_param, page_limit) if params else page_limit
            for page in range(max_pages):
                p = dict(params or {})
                p[limit_param] = limit
                p[skip_param] = offset + page * limit
                resp = sess.request(
                    method, url, params=p, timeout=timeout, verify=verify
                )
                resp.raise_for_status()
                js = resp.json()
                data = _extract_json_root(js, json_root)
                if isinstance(data, list):
                    all_items.extend(data)
                elif isinstance(data, dict):
                    # пытаемся извлечь список из значений словаря
                    for v in data.values():
                        if isinstance(v, list):
                            all_items.extend(v)
                            break
                # останавливаемся, если ответ меньше размера страницы
                if (isinstance(data, list) and len(data) < limit) or (
                    response_total_key
                    and js.get(response_total_key)
                    and len(all_items) >= js.get(response_total_key)
                ):
                    break
        else:
            resp = sess.request(
                method, url, params=params or {}, timeout=timeout, verify=verify
            )
            resp.raise_for_status()
            js = resp.json()
            data = _extract_json_root(js, json_root)
            if isinstance(data, list):
                all_items = data
            elif isinstance(data, dict):
                # пытаемся извлечь первый вложенный список
                for v in data.values():
                    if isinstance(v, list):
                        all_items = v
                        break
                if not all_items:
                    # одиночный объект в ответе
                    all_items = [data]
    except Exception as exc:
        log.exception("call_api error for url=%s: %s", url, exc)
        raise

    # преобразуем в DataFrame и по возможности «сплющиваем» вложенные словари
    try:
        df = pd.json_normalize(all_items)
    except Exception:
        df = pd.DataFrame(all_items)

    log.info(
        "API returned %s rows, %s cols",
        getattr(df, "shape", (None, None))[0],
        getattr(df, "shape", (None, None))[1],
    )

    if save_as:
        try:
            p = Path(save_as)
            p.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(p, index=False)
            log.info("API saved to %s", p)
        except Exception:
            log.exception("Failed to save api result to %s", save_as)

    return df
