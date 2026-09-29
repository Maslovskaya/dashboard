# Дашборд для анализа таблиц Excel

Веб-приложение на FastAPI: загрузка Excel-таблицы, столбчатая и круговая диаграммы,
автоматический анализ (максимум, минимум, самая выгодная модель).
Расчёты и графики делают pandas и matplotlib на сервере, интерфейс на HTML/CSS/JS
подстраивается под экран ноутбука и телефона.

Тема данных: процессоры (пример лежит в `data/cpu.xlsx`).

## Что нужно заранее

- **Python 3.10 или новее** (проверить: `python --version`)
- **Git**

## Запуск из репозитория

### 1. Клонировать репозиторий

```bash
git clone [<URL-репозитория>](https://github.com/Maslovskaya/dashboard)
cd <папка-репозитория>
```
папка репозитория - dashboard, в ней открывайте терминал и выполняйте действия написанные далее.
### 2. Создать виртуальное окружение и установить зависимости

**Windows (PowerShell или cmd):**
```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Если в PowerShell команда `activate` выдаёт ошибку про политику выполнения, выполните
`Set-ExecutionPolicy -Scope Process RemoteSigned` и повторите.

### 3. Запустить сервер

```bash
uvicorn api.main:app --reload
```

### 4. Открыть в браузере

http://127.0.0.1:8000

Нажмите «Загрузить Excel» и выберите свой `.xlsx`-файл или кнопку
«Попробовать на примере», чтобы открыть `data/cpu.xlsx`.
Остановить сервер: `Ctrl+C` в терминале.

## Если что-то не работает

| Проблема | Что делать |
|---|---|
| `python` не найден | Установить Python с python.org, при установке поставить галочку «Add to PATH». На macOS/Linux пробовать `python3` |
| `uvicorn` не найден | Не активировано виртуальное окружение (шаг 2) или не выполнен `pip install -r requirements.txt` |
| `Address already in use` | Порт 8000 занят: запустить с другим портом, `uvicorn api.main:app --port 8001` |
| «Нужен файл в формате .xlsx» | Старый формат `.xls` не поддерживается: пересохранить файл в Excel как `.xlsx` |

## Структура проекта

```
core/data_loader.py   чтение Excel, определение числовых и текстовых колонок
core/charts.py        bar_chart() с выделением максимума, pie_chart() на value_counts()
core/analysis.py      максимум, минимум, показатель «выгодность»
api/main.py           FastAPI: /api/upload, /api/sample, /api/chart/bar, /api/chart/pie, /api/analysis
web/                  index.html, style.css (адаптивная вёрстка), app.js
data/cpu.xlsx         пример данных, data/make_sample.py пересоздаёт его
```

Интерактивная документация API, которую FastAPI строит сам: http://127.0.0.1:8000/docs

## Распределение работы

1. Данные: сбор и проверка Excel, обоснование формулы выгодности.
2. `core/data_loader.py` и `core/analysis.py`.
3. `core/charts.py`.
4. `api/main.py`.
5. `web/` (адаптивная вёрстка) и отчёт.
