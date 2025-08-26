# 📘 Data Automation Project

## 📌 Описание проекта
Проект реализует автоматизацию обработки данных для задания итогового проекта.

Цель — собрать конвейер, который:
- 📥 загружает данные из разных источников (**CSV / Excel / SQL (PostgreSQL) / API**);
- 🧹 выполняет **очистку, валидацию, обработку пропусков/дубликатов/выбросов**;
- 📊 делает **анализ** и обучает **ML‑модели**;
- 📝 генерирует **отчёты (PDF, Excel, HTML)** с графиками и комментариями;
- 📧 отправляет результаты по **email**;
- 🗄️ сохраняет артефакты (логи, данные, отчёты, модели) по папкам и/или в БД;
- ✅ покрыт **автотестами (pytest)** и может запускаться вручную, по **cron** или через **systemd**.

---

## 🎯 Решение
Полный конвейер обработки данных включает:
1. **Источники**: CSV, Excel, SQL (PostgreSQL с JOIN), Mock API.  
2. **Загрузку и объединение** витрин (`sales`, `customers`) → Parquet.  
3. **Очистку**: удаление мусора, заполнение NaN, кодирование категорий, парсинг дат, отлов выбросов.  
4. **Аналитику**: базовые статистики, корреляции, временные ряды, базовый ML.  
5. **Визуализацию**: Matplotlib, Seaborn, Plotly (HTML‑интерактив).  
6. **Отчёты**: PDF (графики+текст), Excel (несколько листов), PNG‑графики, HTML‑дашборды.  
7. **Интеграции**: Email (SMTP), PostgreSQL (инициализация схемы, загрузка CSV, экспорт метрик).  

---

## 📐 Архитектура проекта

Ниже три диаграммы: **общая архитектура, последовательность выполнения, модульные связи**.

### 🔹 Общая архитектура
```mermaid
flowchart LR
  subgraph SRC["Источники"]
    CSV["CSV<br/>data/raw/*.csv"]
    XLSX["Excel<br/>data/raw/*.xlsx"]
    SQL["PostgreSQL<br/>JOIN + SELECT"]
    API["HTTP API<br/>(mock_api.py)"]
  end

  CFG["config.yaml"]
  MAIN["CLI: python -m src.main"]
  RUNNER["Runner"]

  subgraph IO["IO Stage"]
    LOADER["loader.py<br/>CSV/Excel/API"]
    SQLIO["sql.py<br/>DSN+Query"]
    MERGE["Объединение витрин"]
  end

  RAW["processed/_combined_raw.parquet"]

  subgraph CLEAN["Clean Stage"]
    VALID["validator.py"]
    IMPUTE["impute_missing"]
    ENCODE["encode_categorical"]
    SCALE["scale_numeric"]
    PARSE["parse_dates"]
  end

  CLEANED["processed/cleaned.parquet"]

  subgraph REPORT["Reporting"]
    PLOTS["plots.py<br/>Matplotlib"]
    SEABORN["seaborn_plots.py"]
    PLOTLY["plotly_charts.py"]
    PDF["pdf.py"]
    XLS["excel.py"]
  end

  EMAIL["email.py"]
  LOGS["logs/app.log"]

  subgraph DB["PostgreSQL"]
    INITSQL["init_schema.sql"]
    METRICS["export_metrics.py"]
    LOADCSV["load_csv_to_db.py"]
  end

  CRON["Cron/systemd"]
  TESTS["pytest"]

  %% Связи
  CFG --> MAIN --> RUNNER
  RUNNER --> IO
  IO --> RAW
  RAW --> CLEAN --> CLEANED
  CLEANED --> REPORT
  REPORT --> PDF
  REPORT --> XLS
  REPORT --> EMAIL
  REPORT --> DB
  RUNNER --> LOGS
  CRON --> MAIN
  TESTS --> MAIN
```

### 🔹 Последовательность выполнения
```mermaid
sequenceDiagram
  autonumber
  participant User as Пользователь/CRON
  participant Main as src.main
  participant Config as utils.config
  participant Runner as pipelines.runner
  participant IO as pipelines.io_stage
  participant Clean as pipelines.clean_stage
  participant Report as pipelines.report_stage
  participant Email as reporting.email
  participant DB as PostgreSQL

  User->>Main: python -m src.main --config config.yaml
  Main->>Config: load_config
  Config-->>Main: Config dict
  Main->>Runner: run(cfg)
  Runner->>IO: load_sources(cfg)
  par Источники
    IO->>DB: SQL SELECT+JOIN
    IO->>IO: load CSV/Excel/API
  end
  IO-->>Runner: DataFrames
  Runner->>Clean: run_cleaning
  Clean-->>Runner: cleaned DF + stats
  Runner->>Report: run_reporting
  Report-->>Runner: PDF + Excel + PNG + HTML
  Runner->>Email: send_email_with_artifacts
  Runner-->>User: JSON summary
```

### 🔹 Модульная структура
```mermaid
flowchart TD
  MAINFILE["main.py"]

  subgraph Pipelines
    RUNNER["runner.py"]
    IOST["io_stage.py"]
    CLN["clean_stage.py"]
    RPT["report_stage.py"]
    EMAILST["email_stage.py"]
  end

  subgraph IO
    LDR["loader.py"]
    SQLIO2["sql.py"]
  end

  subgraph Processing
    CLEAN["cleaner.py"]
    VAL["validator.py"]
    ENC["encoder.py"]
    SEL["selector.py"]
  end

  subgraph Reporting
    RPLOTS["plots.py"]
    RPDF["pdf.py"]
    RXLS["excel.py"]
    RMAIL["email.py"]
    RPTPKG["report_stage<br/>(оркестратор PDF/Excel/HTML)"]
  end

  subgraph ML
    MLSTAGE["ml/stage.py"]
    MLC["ml/classification.py"]
    MLR["ml/regression.py"]
    MLF["ml/features.py"]
    MLP["ml/plots.py"]
  end

  subgraph Utils
    UCFG["config.py"]
    ULOG["logging.py"]
    UPERS["persist.py"]
  end

  MAINFILE --> RUNNER
  RUNNER --> IOST & CLN & RPT & EMAILST
  IOST --> LDR & SQLIO2 & UCFG & ULOG
  CLN --> CLEAN & VAL & ENC & SEL
  RPT --> RPLOTS & RPDF & RXLS & RMAIL & RPTPKG
  RUNNER --> MLSTAGE
```

---

## 📂 Структура проекта

```text
data_automation_project/
├── config/          # конфиги (YAML/тестовые принты)
├── data/            # raw/processed данные
├── logs/            # логи
├── reports/         # PDF/Excel/HTML/PNG
├── src/             # код пайплайна (pipelines, reporting, ml, processing, io, utils)
├── tests/           # pytest тесты
├── tools/           # вспомогательные скрипты (mock API, email, экспорт метрик и т.п.)
├── requirements.txt # зависимости
├── Makefile         # удобные команды
└── README.md
```

---

## 🚀 Установка и запуск

### Требования
- Python **3.12**
- (Опционально) PostgreSQL для SQL‑источников
- Шрифты для PDF: `assets/fonts/DejaVuSans.ttf`, `DejaVuSans-Bold.ttf` (есть в проекте).

### Установка
```bash
make install
```

### Быстрый запуск
```bash
make run         # полный пайплайн: CSV/Excel/SQL/API -> очистка -> отчёты -> email
# или
python -m src.main --config config/config.yaml
```

### Работа с БД
```bash
make db-init
make db-load
make db-metrics
make db-test-connection
```

### Mock API + SMTP
```bash
make api
make email
make full
```

### Тесты
```bash
make test
# или подробнее:
pytest -vv -rA --showlocals --full-trace
```

---

## ⚙️ Конфигурация (`config/config.yaml`)

Пример источников:
```yaml
sources:
  sql:
    - name: sales
      dsn: postgresql+psycopg2://user:pass@host:5432/dbname
      query: SELECT order_id, customer_id, order_date, amount FROM sales
      target: sales
  csv:
    - name: sales
      path: data/raw/sales.csv
      target: sales
  api:
    - name: sales_api
      url: http://127.0.0.1:5000/sales
      method: GET
      json_root: data
      target: sales
```

### PDF‑отчёт и титульный лист
Ключи для настройки:
```yaml
reporting:
  pdf:
    output: reports/pdf/report.pdf
    preface_path: assets/preface.pdf   # обложка, подшивается первой страницей
    title: "Сводный отчёт по продажам" # заголовок тела отчёта
    intro_extra: []                    # при необходимости можно добавить абзацы
```

---

## 🧪 Тестирование
Категории тестов:
- `test_loader.py` — загрузка CSV/Excel/SQL/API;  
- `test_cleaner.py` — пропуски, кодирование, даты;  
- `test_validator.py` — дубликаты, пропуски, выбросы;  
- `test_pipeline.py` — сквозной прогон;  
- `sql_test_connection.py` — проверка Postgres;  
- `ssl_test.py` — SSL‑проверки;  
- `api_test.py` — тест API.  

Полезные команды:
```bash
pytest --durations=10    # топ-10 самых медленных тестов
pytest -k "validator"    # запустить часть тестов по имени
```

---

## 📊 Отчёты
- 📑 **PDF** — графики + комментарии.  
- 📊 **Excel** — листы: raw, cleaned, aggregates, metrics (+ произвольные таблицы).  
- 🌐 **HTML** — интерактивные Plotly‑графики.  
- 🖼️ **PNG** — статичные графики по источникам и ML.  

Файлы находятся в `reports/{pdf,excel,html,images}`.

---

## 📧 Email
Отправка через локальный SMTP:  
```bash
make email
```
Письмо содержит PDF, Excel и изображения как вложения.

---

## 🤖 Автоматизация
**cron (ежедневно в 08:00):**
```bash
0 8 * * * cd /home/USER/data_automation_project && . .venv/bin/activate && python -m src.main --config config/config.yaml >> logs/cron.log 2>&1
```
**systemd:**
```ini
[Unit]
Description=Data Automation Pipeline
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/USER/data_automation_project
ExecStart=/home/USER/data_automation_project/.venv/bin/python -m src.main --config config/config.yaml
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

---

## 🧭 Принципы разработки
- **KISS** — каждая функция решает одну задачу.  
- **DRY** — общие блоки вынесены в `utils`.  
- **Логирование** — INFO в консоль и `logs/app.log`.  
- **Документация** — docstrings + комментарии.  
- **Расширяемость** — легко добавить новые источники/отчёты/модели.

---

## ✅ Итоги
- [x] Загрузка CSV/Excel/SQL/API  
- [x] Очистка, валидация, обработка  
- [x] Базовый анализ  
- [x] ML: классификация и регрессия (метрики/графики/модели)  
- [x] Отчёты: PDF, Excel, HTML, PNG  
- [x] Email‑рассылка  
- [x] PostgreSQL (init, load, metrics)  
- [x] Полное тестирование (pytest)  
- [x] Автоматизация (cron/systemd)