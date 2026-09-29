"""Расчёты: максимум, минимум и собственный показатель «выгодность»."""
import pandas as pd

MAX, MIN, VALUE = "max", "min", "value"
ALL_OPTIONS = [MAX, MIN, VALUE]

OPTION_LABELS = {
    MAX: "Максимум",
    MIN: "Минимум",
    VALUE: "Самая выгодная модель",
}

VALUE_SCORE_NAME = "Выгодность"


def value_score(df: pd.DataFrame, perf_cols: list[str], price_col: str) -> pd.Series:
    """Показатель «выгодность» = (произведение характеристик) / цена × 1000.

    Для процессоров: (частота × ядра) / цена × 1000 — сколько «вычислительной
    мощности» получаем за каждую 1000 рублей. Чем больше, тем выгоднее.
    """
    if not perf_cols:
        raise ValueError("Выберите хотя бы одну характеристику для расчёта выгодности.")
    power = pd.Series(1.0, index=df.index)
    for col in perf_cols:
        power = power * df[col]
    price = df[price_col].where(df[price_col] > 0)  # цена 0 или меньше → пропуск
    return power / price * 1000


def _fmt(x) -> str:
    """Число → строка: целые с пробелом-разделителем, дробные без лишних нулей."""
    if isinstance(x, (int,)) or hasattr(x, "dtype") and "int" in str(x.dtype):
        return f"{int(x):,}".replace(",", " ")
    text = f"{float(x):,.2f}".rstrip("0")
    if text.endswith("."):
        text += "0"
    return text.replace(",", " ")


def _names_at(df: pd.DataFrame, mask: pd.Series, name_col: str, limit: int = 3) -> str:
    """Названия всех моделей, где выполнено условие (при равенстве их несколько)."""
    names = df.loc[mask, name_col].astype(str).tolist()
    if len(names) <= limit:
        return ", ".join(names)
    return ", ".join(names[:limit]) + f" и ещё {len(names) - limit}"


def build_analysis(
    df: pd.DataFrame,
    options: list[str],
    name_col: str,
    metric_col: str,
    perf_cols: list[str] | None = None,
    price_col: str | None = None,
) -> pd.DataFrame:
    """Собирает выбранные показатели в одну таблицу.

    Колонки результата: «Показатель», «Модель», «Значение».
    """
    rows = []
    if MAX in options:
        top = df[metric_col].max()
        rows.append((f"Максимум: {metric_col}", _names_at(df, df[metric_col] == top, name_col), _fmt(top)))
    if MIN in options:
        low = df[metric_col].min()
        rows.append((f"Минимум: {metric_col}", _names_at(df, df[metric_col] == low, name_col), _fmt(low)))
    if VALUE in options:
        if not price_col:
            raise ValueError("Для расчёта выгодности нужен столбец с ценой.")
        score = value_score(df, perf_cols or [], price_col).round(2)
        best = score.max()
        rows.append((f"Самая выгодная ({VALUE_SCORE_NAME})", _names_at(df, score == best, name_col), _fmt(best)))
    return pd.DataFrame(rows, columns=["Показатель", "Модель", "Значение"])
