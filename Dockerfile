# Используем официальный образ Python (3.10-slim)
FROM python:3.10-slim

# Задаём рабочую директорию
WORKDIR /app

# Копируем файл с зависимостями (создайте его, если отсутствует)
COPY requirements.txt /app/requirements.txt

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код проекта в контейнер
COPY . /app

# Открываем порт 80 для доступа
EXPOSE 80

# Запускаем приложение через Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]

