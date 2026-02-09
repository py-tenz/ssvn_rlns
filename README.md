# Telegram-бот обучения пилотов (Aiogram 3 + MongoDB)

Этот проект — Telegram-бот для длительного обучения (например, 30 дней и больше).

Ключевые особенности:
- **Уроки** берутся из MongoDB (`lessons`: `dayNum`, `text`, `images`).
- **Прогресс пользователя** и регистрация тоже хранятся в MongoDB (`users`).
- Количество дней обучения не «зашито»: бот определяет его по максимальному `dayNum` в базе.

---

## Стек

- Python **3.11**
- Aiogram **3.19.0**
- MongoDB
  - `motor` (async драйвер)
  - `pymongo` (для сидинга и bulk-операций)
- Docker / docker-compose (опционально)

---

## Структура проекта

```
.
├─ app/
│  ├─ handlers.py        # роутеры/хендлеры aiogram
│  ├─ keyboards.py       # inline-кнопки
│  ├─ db.py              # слой доступа к MongoDB + индексы
│  └─ middlewares.py     # middleware для прокидывания Mongo в хендлеры
├─ media/                # картинки и .txt для теории (отправляются из файлов)
├─ scripts/
│  └─ seed_lessons.py    # «сидинг» уроков в MongoDB из JSON
├─ config.py             # чтение env + валидация
├─ run.py                # точка входа
├─ requirements.txt
├─ Dockerfile
└─ docker-compose.yml
```

---

## Быстрый старт (Docker Compose)

1) Создайте `.env` на основе `.env.example`:

```bash
cp .env.example .env
```

2) Заполните `BOT_TOKEN` и (при необходимости) Mongo-настройки.

3) Запуск:

```bash
docker compose up -d --build
```

По умолчанию:
- MongoDB поднимается как сервис `mongo` (порт `27017` наружу тоже открыт).
- Бот запускается как сервис `bot`.
- Папка `./media` монтируется внутрь контейнера **только для чтения**.

Логи:

```bash
docker compose logs -f bot
```

Остановка:

```bash
docker compose down
```

---

## Запуск локально (без Docker)

> Нужна поднятая MongoDB (локальная, в Docker или удалённая).

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# отредактируйте .env

python run.py
```

---

## Переменные окружения

Файл `.env` (см. `.env.example`):

- `BOT_TOKEN` — токен Telegram-бота (обязателен)
- `ADMIN_ID` — опционально, сейчас в коде не используется для прав, но оставлен «на вырост»
- `MONGO_URI` — строка подключения к MongoDB (по умолчанию `mongodb://localhost:27017`)
- `MONGO_DB` — имя БД (по умолчанию `pilot_training`)

---

## MongoDB: коллекции и индексы

### Коллекция `lessons`

Документ урока:

```json
{
  "dayNum": 1,
  "text": "Текст урока...",
  "images": ["day1_1.jpg", "day1_2.jpg"]
}
```

- `dayNum` — уникальный номер дня (создаётся unique-index при старте бота).
- `images` — имена файлов из папки `media/`.

⚠️ Важно про картинки:
- Бот отправляет картинки **файлами с диска** (`media/<имя_файла>`).
- Если файл не найден — он **тихо пропускается** (альбом отправится из того, что найдено).
- Telegram ограничивает альбом: **до 10 фото** за одну отправку. Если больше — бот делит на части.

### Коллекция `users`

Документ пользователя:

```json
{
  "_id": 123456789,
  "name": "Иван",
  "birth_year": 1990,
  "entry_test_completed": false,
  "completed_day": 0,
  "next_unlock_at": null,
  "last_completed_at": null,
  "created_at": "...",
  "updated_at": "..."
}
```

- `_id` — Telegram user id (целое число)
- `completed_day` — последний **полностью выполненный** день
- `entry_test_completed` — флаг прохождения входного тестирования

Дополнительные поля для "обучения по дням":

- `next_unlock_at` — момент (UTC), когда откроется следующий день.
  - `null`/отсутствует ⇒ следующий день открыт.
  - При завершении дня N бот выставляет **следующий день** на **08:00 следующего календарного дня по времени Europe/Berlin**.
- `last_completed_at` — когда пользователь последний раз отмечал день как выполненный (UTC).

### Ограничение "один день в сутки"

После выполнения дня **следующий день становится доступен только на следующий календарный день в 08:00 по времени Берлина**.

Для этого используются поля:

- `next_unlock_at` — момент (UTC), когда можно открыть следующий день
- `last_completed_at` — момент (UTC) фактического завершения текущего дня

Если `next_unlock_at` отсутствует/`null`, следующий день считается доступным сразу (например, для Дня 1 сразу после входного тестирования).

Индексы создаются автоматически при запуске (см. `app/db.py → ensure_indexes`).

---

## Сидинг уроков (seed)

**Сидинг** — это начальная загрузка (или обновление) контента в базу.

Скрипт: `scripts/seed_lessons.py`

### Формат JSON

Файл `lessons.json` должен быть массивом:

```json
[
  {"dayNum": 1, "text": "...", "images": ["day1_1.jpg"]},
  {"dayNum": 2, "text": "...", "images": []}
]
```

### Запуск

```bash
python scripts/seed_lessons.py lessons.json mongodb://localhost:27017 pilot_training
```

Что делает скрипт:
- Для каждого `dayNum` делает **upsert** (создаст, если нет; обновит, если есть).
- Поля, которые обновляются: `dayNum`, `text`, `images`.

---

## Где что менять в коде

- Тексты/сценарии общения: `app/handlers.py`
- Кнопки и callback_data: `app/keyboards.py`
- MongoDB и схема данных: `app/db.py`

### Ссылки на входное тестирование

Сейчас ссылки на Google Forms зашиты в `app/keyboards.py → entry_test_kb()`.
Если нужно вынести в конфиг/БД — это лучше сделать следующим шагом.

### Теория (файлы .txt)

Меню теории: `app/keyboards.py → theory_menu_kb()`
Логика отправки: `app/handlers.py → theory_send_file()`

Файлы должны лежать в `media/` с именами:
- `illusions.txt`
- `startle_effect.txt`
- `research.txt`

---

## Типовые операции в Mongo (для разработчика)

Сбросить прогресс пользователя:

```js
db.users.updateOne({ _id: 123456789 }, { $set: { completed_day: 0, entry_test_completed: false } })
```

Посмотреть, какие дни загружены:

```js
db.lessons.find({}, { dayNum: 1, _id: 0 }).sort({ dayNum: 1 })
```

---

## Частые проблемы

- **ValueError: BOT_TOKEN not found**
  - Проверьте `.env` и что он подхватывается (в Docker — через `env_file: .env`).

- **MongoDB connection refused**
  - Проверьте `MONGO_URI` и что Mongo реально запущена.
  - В Docker Compose для бота чаще всего удобнее `MONGO_URI=mongodb://mongo:27017`.

- **Картинки не отправляются**
  - Проверьте, что файлы реально лежат в `media/` и названия в `images[]` совпадают.
  - В Docker Compose папка `./media` монтируется в контейнер как `/application/media`.

---

## Деплой (минимальный вариант)

Самый простой продовый вариант — запуск через Docker Compose на сервере:

1) Скопируйте проект на сервер.
2) Создайте `.env`.
3) Запустите:

```bash
docker compose up -d --build
```

Бэкапы Mongo:
- используйте `mongodump/mongorestore` или снапшоты volume (в зависимости от инфраструктуры).

---

## Лицензия

Внутренняя разработка / учебный проект.
