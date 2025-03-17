# Этап сборки и тестирования
FROM python:3.10-slim AS builder

WORKDIR /app

# Копируем зависимости и устанавливаем их
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь исходный код в контейнер
COPY . /app

# Запускаем тесты. Если тесты не пройдут, сборка завершится с ошибкой.
RUN pytest test_app.py

# Финальный этап: создаём минимальный образ для запуска приложения
FROM python:3.10-slim

WORKDIR /app

# Копируем установленные зависимости и исходный код из этапа builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /app /app

EXPOSE 80

# Запускаем приложение через uvicorn, используя python -m uvicorn
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]

