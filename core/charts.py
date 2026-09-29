"""Графики Matplotlib. Функции возвращают Figure, а показывает их интерфейс."""
import base64
import io

import matplotlib
matplotlib.use("Agg")  # рисуем в память, без окон — нужно для сервера
import matplotlib.pyplot as plt
import pandas as pd

BLUE = "#2F5D8A"     # обычные столбцы
AMBER = "#E8A317"    # столбец с максимумом
INK = "#14212B"
GRID = "#D5DDE3"
PIE_COLORS = ["#2F5D8A", "#E8A317", "#5A9BB5", "#8AB17D", "#B5533C",
              "#7D6BA8", "#C9C1A8", "#3E7C6F", "#9AA5AE"]


def bar_chart(df: pd.DataFrame, x: str, y: str):
    """Столбчатая диаграмма. Столбец с максимальным значением — другого цвета.

    Возвращает (Figure, {"label": ..., "value": ...}) — вторым значением идёт
    информация о столбце-максимуме.
    """
    data = df[[x, y]].dropna()
    labels = data[x].astype(str).tolist()
    values = data[y].tolist()
    max_pos = values.index(max(values))
    colors = [AMBER if i == max_pos else BLUE for i in range(len(values))]

    width = min(max(7, len(values) * 0.3), 10.5)
    fig, ax = plt.subplots(figsize=(width, 5.6))
    ax.bar(range(len(values)), values, color=colors, width=0.72)
    ax.set_xticks(range(len(values)))
    ax.set_xticklabels(labels, rotation=60, ha="right", fontsize=10, color=INK)
    ax.set_ylabel(y, color=INK, fontsize=11)
    ax.set_xlabel(x, color=INK, fontsize=11)
    ax.set_title(f"{y} по «{x}»", loc="left", fontsize=14, color=INK, pad=12)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.tick_params(axis="y", colors=INK, length=0, labelsize=10)

    ax.annotate(
        f"максимум: {values[max_pos]:g}",
        (max_pos, values[max_pos]),
        textcoords="offset points", xytext=(0, 6), ha="center",
        fontsize=10, color=INK, fontweight="bold",
    )
    ax.set_ylim(0, max(values) * 1.12)
    fig.tight_layout()
    return fig, {"label": labels[max_pos], "value": values[max_pos]}


def pie_chart(df: pd.DataFrame, column: str, max_slices: int = 8):
    """Круговая диаграмма долей: считаем value_counts() и подписываем процентами.

    Если уникальных значений больше max_slices, мелкие объединяются в «Другое».
    """
    counts = df[column].value_counts()
    if len(counts) > max_slices:
        head = counts.iloc[: max_slices - 1]
        counts = pd.concat([head, pd.Series({"Другое": counts.iloc[max_slices - 1:].sum()})])

    fig, ax = plt.subplots(figsize=(7, 5.2))
    ax.pie(
        counts.values,
        labels=[str(i) for i in counts.index],
        autopct="%1.1f%%",
        startangle=90,
        counterclock=False,
        colors=PIE_COLORS[: len(counts)],
        wedgeprops={"edgecolor": "white", "linewidth": 2},
        textprops={"color": INK, "fontsize": 10},
        pctdistance=0.75,
    )
    ax.set_title(f"Доли по столбцу «{column}»", loc="left", fontsize=13, color=INK, pad=12)
    ax.axis("equal")
    fig.tight_layout()
    return fig


def fig_to_base64(fig) -> str:
    """PNG в base64 — так график удобно отдавать через API и вставлять в <img>."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=140, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("ascii")
