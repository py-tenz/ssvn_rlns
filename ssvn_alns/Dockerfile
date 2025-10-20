
FROM python:3.11-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /application

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект в контейнер
COPY . .

# Переменная окружения, чтобы Python выводил логи сразу
ENV PYTHONUNBUFFERED=1

# Команда запуска бота
CMD ["python", "run.py"]
