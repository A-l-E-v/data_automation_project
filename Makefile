# Установить виртуальное окружение и зависимости
install:
	python -m venv .venv
	. .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt

# Запустить пайплайн с config/config.yaml
run:
	rm -rf /home/al/data_automation_project/reports && rm -f /home/al/data_automation_project/logs/app.log && clear && . .venv/bin/activate && python -m src.main --config config/config.yaml

# Прогнать тесты
test:
	. .venv/bin/activate && pytest

# Подробный тестовый прогон
test-verbose:
	. .venv/bin/activate && pytest -vv -rA --maxfail=1 --durations=20 --durations-min=0.001 --showlocals --full-trace -s

# Список тестов без запуска для навигации
test-collect:
	. .venv/bin/activate && pytest --collect-only -q

# Запуск части тестов по фильтру: make test-one SPEC="validator and outliers"
test-one:
	. .venv/bin/activate && pytest -vv -k "$(SPEC)" --maxfail=1 -x -s

# Показать доступные фикстуры
test-fixtures:
	. .venv/bin/activate && pytest --fixtures -q

# Готовим HTML/JUnit отчёт для CI
test-report:
	mkdir -p reports/tests
	. .venv/bin/activate && pytest -vv -rA --junitxml=reports/tests/junit.xml

email:
	clear && clear && lsof -ti:1025 | xargs -r kill -9 && . .venv/bin/activate && python /home/al/data_automation_project/tools/run_debug_smtp.py

api:
	clear &&  lsof -ti:5000 | xargs -r kill -9 && . .venv/bin/activate && python -m tools.mock_api

full:
	clear && lsof -ti:5000 | xargs -r kill -9 && . .venv/bin/activate && \
python -m tools.mock_api & \
sleep 2 && \
. .venv/bin/activate && \
lsof -ti:1025 | xargs -r kill -9 && \
python /home/al/data_automation_project/tools/run_debug_smtp.py

# Очистить временные и сгенерированные файлы
clean:
	rm -rf __pycache__ */__pycache__ */*/__pycache__ .pytest_cache
	rm -rf data/processed/* reports/pdf/* reports/excel/* reports/images/*
	rm -f logs/*.log

# Форматирование кода
format:
	. .venv/bin/activate && black src tests

tree:
	clear && tree --prune -I '__pycache__|*static|*share|.pytest_cache|*.venv|*.git*' -a -L 10

db-test-connection:
	. .venv/bin/activate && pytest -q tests/sql_test_connection.py

db-init:
	psql -U ecom_superadmin -d ml_db -h localhost -f tools/init_schema.sql

db-load:
	. .venv/bin/activate && python -m tools.load_csv_to_db

db-metrics:
	. .venv/bin/activate && python -m tools.export_metrics

.PHONY: install run test test-verbose test-collect test-one test-fixtures test-report email api full clean format tree db-test-connection db-init db-load db-metrics
