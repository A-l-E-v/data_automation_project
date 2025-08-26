from __future__ import annotations
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, precision_recall_curve
from .utils import savefig


def confusion(cm: np.ndarray, out: Path) -> str:
    plt.figure()
    plt.imshow(cm, interpolation="nearest", cmap="Blues")
    plt.title("Матрица ошибок")
    plt.xlabel("Предсказанный класс")
    plt.ylabel("Истинный класс")
    thresh = cm.max() / 2.0 if cm.size else 0
    for (i, j), v in np.ndenumerate(cm):
        color = "white" if v > thresh else "black"
        plt.text(j, i, int(v), ha="center", va="center", color=color, fontsize=9)
    return savefig(out)


def roc(y_true, y_proba, out: Path) -> str:
    fpr, tpr, _ = roc_curve(y_true, y_proba)
    plt.figure()
    plt.plot(fpr, tpr)
    plt.plot([0, 1], [0, 1], linestyle="--")
    plt.xlabel("FPR")
    plt.ylabel("TPR")
    plt.title("ROC")
    return savefig(out)


def pr(y_true, y_proba, out: Path) -> str:
    prec, rec, _ = precision_recall_curve(y_true, y_proba)
    plt.figure()
    plt.plot(rec, prec)
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title("PR")
    return savefig(out)


def reg_scatter(y_true, y_pred, out: Path) -> str:
    plt.figure()
    plt.scatter(y_true, y_pred, s=10)
    plt.xlabel("Факт")
    plt.ylabel("Прогноз")
    plt.title("Регрессия: факт vs прогноз")
    return savefig(out)


def residuals(y_true, y_pred, out: Path) -> str:
    res = y_true - y_pred
    plt.figure()
    plt.hist(res, bins=30)
    plt.xlabel("Остаток")
    plt.ylabel("Частота")
    plt.title("Остатки")
    return savefig(out)


def bar(names, vals, title, out: Path) -> str:
    """Простой bar-chart для топ-фич/важностей и т.п."""
    plt.figure()
    idx = np.arange(len(names))
    plt.bar(idx, vals)
    plt.xticks(idx, names, rotation=90)
    plt.title(str(title)[:60])
    plt.tight_layout()
    return savefig(out)
