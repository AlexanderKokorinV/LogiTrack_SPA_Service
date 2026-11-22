# 1. Базовый образ Python
FROM python:3.14-slim

# 2. Настройки окружения
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    POETRY_VERSION=2.2.1 \
    POETRY_HOME="/opt/poetry" \
    PATH="/opt/poetry/bin:$PATH"

# 3. Рабочая директория
WORKDIR /app

# 4. Установка системных утилит и Poetry
RUN apt-get update && apt-get install --no-install-recommends -y \
    curl \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 5. Копирование файлов зависимостей
COPY pyproject.toml poetry.lock ./

# 6. Установка основных зависимостей
RUN poetry install --no-root --only main --no-ansi

# 7. Копирование исходного кода
COPY . .

# 8. Порт приложения
EXPOSE 8000

# 9. Миграции, сбор статики и запуск Gunicorn
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput && exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3"]
