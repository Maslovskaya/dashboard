"""Загрузка Excel и определение типов колонок.

Этот модуль ничего не знает ни про Streamlit, ни про FastAPI:
его функции можно вызвать откуда угодно.
"""
import pandas as pd


def load_excel(source) -> pd.DataFrame:
    """Читает .xlsx (путь или файловый объект) в таблицу.

    Пустые строки и полностью пустые столбцы выбрасываются,
    названия колонок очищаются от лишних пробелов.
    """
    df = pd.read_excel(source, engine="openpyxl")
    df = df.dropna(how="all").dropna(axis=1, how="all")
    df.columns = [str(c).strip() for c in df.columns]
    if df.empty:
        raise ValueError("В файле нет данных.")
    return df.reset_index(drop=True)


def numeric_columns(df: pd.DataFrame) -> list[str]:
    """Колонки с числами: их можно откладывать по оси Y и считать макс/мин."""
    return df.select_dtypes(include="number").columns.tolist()


def category_columns(df: pd.DataFrame) -> list[str]:
    """Нечисловые колонки: подходят для подписей и круговой диаграммы."""
    nums = set(numeric_columns(df))
    return [c for c in df.columns if c not in nums]


def guess_name_column(df: pd.DataFrame) -> str:
    """Колонка с названиями моделей: первая нечисловая, иначе первая вообще."""
    cats = category_columns(df)
    return cats[0] if cats else df.columns[0]


def guess_price_column(df: pd.DataFrame) -> str | None:
    """Ищет числовую колонку с ценой по названию."""
    for col in numeric_columns(df):
        if any(w in col.lower() for w in ("цен", "price", "стоим", "руб")):
            return col
    return None


def guess_perf_columns(df: pd.DataFrame, price_col: str | None) -> list[str]:
    """Колонки-характеристики для показателя «выгодность» (частота, ядра)."""
    words = ("частот", "ггц", "ядр", "freq", "core")
    return [c for c in numeric_columns(df)
            if c != price_col and any(w in c.lower() for w in words)]
