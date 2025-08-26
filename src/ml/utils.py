from __future__ import annotations
from pathlib import Path
import matplotlib.pyplot as plt

ID_COLUMNS = {"order_id", "customer_id"}


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def savefig(path: Path, title: str | None = None) -> str:
    ensure_dir(path.parent)
    if title:
        plt.title(title)
    plt.tight_layout()
    plt.savefig(path, dpi=130)
    plt.close()
    return str(path)
