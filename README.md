# Telegram бот обучения пилотов (MongoDB)

## Что изменилось по сравнению со старым проектом
- Уроки (текст + изображения) берутся из MongoDB коллекции `lessons` с полями:
  - `dayNum` (int) — номер дня
  - `text` (string) — текст урока
  - `images` (array[string]) — список файлов из папки `media/`
- Прогресс пользователя хранится в MongoDB коллекции `users` (персистентно).

## Переменные окружения
Скопируй `.env.example` → `.env` и заполни:
- `BOT_TOKEN`
- `MONGO_URI`
- `MONGO_DB`

## Запуск локально
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

MongoDB должна быть доступна по `MONGO_URI`.

## Структура коллекций

### lessons
Пример документа:
```json
{
  "dayNum": 1,
  "text": "Текст для первого дня",
  "images": ["day1_1.jpg", "day1_2.jpg"]
}
```

### users
Пользователь сохраняется автоматически при регистрации:
```json
{
  "_id": 123456789,
  "name": "Иван",
  "birth_year": 1990,
  "entry_test_completed": false,
  "completed_day": 0
}
```

## Сидинг уроков
В `scripts/seed_lessons.py` есть пример загрузки уроков из JSON файла.

