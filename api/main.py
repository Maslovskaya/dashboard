"""FastAPI-версия: те же функции из core/, но с HTML/CSS-интерфейсом.

Запуск:  uvicorn api.main:app --reload
Потом открыть http://127.0.0.1:8000
"""
import io
import uuid
from collections import OrderedDict
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core.analysis import ALL_OPTIONS, build_analysis
from core.charts import bar_chart, fig_to_base64, pie_chart
from core.data_loader import (
    category_columns, guess_name_column, guess_perf_columns,
    guess_price_column, load_excel, numeric_columns,
)

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = ROOT / "data" / "cpu.xlsx"
MAX_FILE_MB = 10
MAX_STORED = 20  # сколько таблиц держим в памяти одновременно

app = FastAPI(title="Дашборд: сравнение данных")

# Сервер не помнит пользователя между запросами, поэтому после загрузки
# выдаём file_id, а таблицу храним в памяти. Старые выбрасываем.
STORE: "OrderedDict[str, pd.DataFrame]" = OrderedDict()


def _save(df: pd.DataFrame) -> str:
    file_id = uuid.uuid4().hex[:12]
    STORE[file_id] = df
    while len(STORE) > MAX_STORED:
        STORE.popitem(last=False)
    return file_id


def _get(file_id: str) -> pd.DataFrame:
    if file_id not in STORE:
        raise HTTPException(404, "Таблица не найдена. Загрузите файл заново.")
    return STORE[file_id]


def _check_columns(df: pd.DataFrame, *cols: str) -> None:
    for c in cols:
        if c not in df.columns:
            raise HTTPException(400, f"В таблице нет столбца «{c}».")


def _describe(file_id: str, df: pd.DataFrame) -> dict:
    """Всё, что нужно интерфейсу сразу после загрузки."""
    price = guess_price_column(df)
    preview = df.head(8).astype(object).where(df.head(8).notna(), "")
    return {
        "file_id": file_id,
        "rows": len(df),
        "columns": df.columns.tolist(),
        "numeric": numeric_columns(df),
        "categorical": category_columns(df),
        "defaults": {
            "name": guess_name_column(df),
            "price": price,
            "perf": guess_perf_columns(df, price),
        },
        "preview": preview.values.tolist(),
    }


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    if not (file.filename or "").lower().endswith(".xlsx"):
        raise HTTPException(400, "Нужен файл в формате .xlsx")
    content = await file.read()
    if len(content) > MAX_FILE_MB * 1024 * 1024:
        raise HTTPException(413, f"Файл больше {MAX_FILE_MB} МБ.")
    try:
        df = load_excel(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(400, f"Не удалось прочитать файл: {e}")
    return _describe(_save(df), df)


@app.post("/api/sample")
def sample():
    """Загружает пример data/cpu.xlsx, чтобы можно было попробовать без файла."""
    if not SAMPLE.exists():
        raise HTTPException(404, "Файл примера не найден.")
    df = load_excel(SAMPLE)
    return _describe(_save(df), df)


@app.get("/api/chart/bar")
def chart_bar(file_id: str, x: str, y: str):
    df = _get(file_id)
    _check_columns(df, x, y)
    if y not in numeric_columns(df):
        raise HTTPException(400, f"Столбец «{y}» не числовой.")
    fig, top = bar_chart(df, x, y)
    return {"image": fig_to_base64(fig), "max_label": top["label"], "max_value": top["value"]}


@app.get("/api/chart/pie")
def chart_pie(file_id: str, column: str):
    df = _get(file_id)
    _check_columns(df, column)
    return {"image": fig_to_base64(pie_chart(df, column))}


class AnalysisRequest(BaseModel):
    file_id: str
    options: list[str]
    name_col: str
    metric_col: str
    price_col: str | None = None
    perf_cols: list[str] = []


@app.post("/api/analysis")
def analysis(req: AnalysisRequest):
    df = _get(req.file_id)
    _check_columns(df, req.name_col, req.metric_col, *req.perf_cols, *([req.price_col] if req.price_col else []))
    options = [o for o in req.options if o in ALL_OPTIONS]
    if not options:
        raise HTTPException(400, "Выберите хотя бы один показатель.")
    try:
        table = build_analysis(df, options, req.name_col, req.metric_col, req.perf_cols, req.price_col)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"columns": table.columns.tolist(), "rows": table.values.tolist()}


# ---- Фронтенд (HTML/CSS/JS) отдаём с того же сервера ----
@app.get("/")
def index():
    return FileResponse(ROOT / "web" / "index.html")


app.mount("/", StaticFiles(directory=ROOT / "web"), name="web")
