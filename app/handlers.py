from __future__ import annotations

import os

from pathlib import Path
from typing import Optional, Any
from datetime import datetime, timezone, timedelta, time
from zoneinfo import ZoneInfo

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    CallbackQuery,
    FSInputFile,
    InputMediaPhoto,
)
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from .db import Mongo
from . import keyboards as kb

router = Router()

MEDIA_PATH = Path(__file__).parent.parent / "media"

CONSENT_DIR = MEDIA_PATH / "consents"
CONSENT_FILE_1 = os.getenv("CONSENT_FILE_1", "soglasie_1.docx")
CONSENT_FILE_2 = os.getenv("CONSENT_FILE_2", "soglasie_2.docx")

CONSENT_TEXT = (
    "Перед началом регистрации ознакомься с двумя файлами-согласиями на обработку персональных данных.\n"
    "Если ты согласен(на), нажми кнопку ниже — после этого я попрошу ввести данные."
)

PAGE_SIZE = 10  # for day picker

MOSCOW_TZ = ZoneInfo("Europe/Moscow")
LOCAL_TZ = MOSCOW_TZ

# ---------- FSM for registration ----------
class Registration(StatesGroup):
    name = State()
    birth_year = State()

# ---------- FSM for consent before registration ----------
class Consent(StatesGroup):
    pending = State()


# ---------- Helpers ----------
def _format_dt_local(dt_utc: datetime) -> str:
    """Human-friendly datetime in local timezone (MSK), e.g. 10.02.2026 08:00."""
    dt_local = dt_utc.astimezone(LOCAL_TZ)
    return dt_local.strftime("%d.%m.%Y %H:%M")


def _compute_next_unlock_at(now_utc: datetime) -> datetime:
    """Next day at 08:00 MSK, returned as UTC datetime."""
    now_local = now_utc.astimezone(LOCAL_TZ)
    next_date = now_local.date() + timedelta(days=1)
    unlock_local = datetime.combine(next_date, time(hour=8, minute=0), tzinfo=LOCAL_TZ)
    return unlock_local.astimezone(timezone.utc)


def _is_unlocked(now_utc: datetime, next_unlock_at: Optional[datetime]) -> bool:
    return (next_unlock_at is None) or (now_utc >= next_unlock_at)


def _normalize_dt(dt: object) -> Optional[datetime]:
    """Motor/PyMongo returns datetime; keep robust if missing/invalid."""
    if isinstance(dt, datetime):
        # If stored as naive UTC, treat it as UTC.
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt
    return None



async def send_consents(message: Message) -> None:
    """Send consent documents (docx) before registration."""
    await message.answer(CONSENT_TEXT, reply_markup=kb.consent_kb())
    for filename in (CONSENT_FILE_1, CONSENT_FILE_2):
        path = CONSENT_DIR / filename
        if path.exists():
            await message.answer_document(FSInputFile(path))
        else:
            await message.answer(
                f"⚠️ Не найден файл согласия: {filename}. Ожидаю его в {path}."
            )

async def render_menu(message: Message, mongo: Mongo, tg_id: int) -> None:
    """Render main menu into the given chat message.

    IMPORTANT: In callback queries, cb.message.from_user is the bot (message author),
    so tg_id must be provided explicitly (cb.from_user.id).
    """
    user = await mongo.get_user(tg_id)
    max_day = await mongo.get_max_day()

    if not user:
        await message.answer("Чтобы начать, отправь команду /start")
        return

    completed_day = int(user.get("completed_day", 0) or 0)
    entry_test_completed = bool(user.get("entry_test_completed", False))

    next_day = completed_day + 1
    if max_day and next_day > max_day:
        next_day = None

    now = datetime.now(timezone.utc)
    next_unlock_at = _normalize_dt(user.get("next_unlock_at"))
    can_continue = _is_unlocked(now, next_unlock_at)
    locked_until = None if can_continue else (_format_dt_local(next_unlock_at) if next_unlock_at else None)

    name = user.get("name") or "пилот"

    await message.answer(
        f"Привет, {name}!\nВыбери действие:",
        reply_markup=kb.menu_kb(
            next_day=next_day,
            completed_day=completed_day,
            max_day=max_day,
            entry_test_completed=entry_test_completed,
            can_continue=can_continue,
            locked_until=locked_until,
        ),
    )

def _lesson_to_tasks(lesson: dict) -> list[dict]:
    """
    Normalizes lesson schema to tasks[].
    Supports:
      - new schema: {"dayNum": 1, "tasks": [{"text": "...", "images": [...]}, ...]}
      - legacy schema: {"dayNum": 1, "text": "...", "images": [...]}
    """
    tasks = lesson.get("tasks")
    if isinstance(tasks, list) and tasks:
        norm: list[dict] = []
        for t in tasks:
            if not isinstance(t, dict):
                continue
            norm.append(
                {
                    "text": str(t.get("text") or "").strip(),
                    "images": list(t.get("images") or []),
                }
            )
        return norm or [{"text": str(lesson.get("text") or "").strip(), "images": list(lesson.get("images") or [])}]

    # legacy fallback
    return [{"text": str(lesson.get("text") or "").strip(), "images": list(lesson.get("images") or [])}]


async def _send_task_content(message: Message, task: dict) -> None:
    """Sends task images (as albums where possible) and then text."""
    images = list(task.get("images") or [])
    text = str(task.get("text") or "").strip()

    # send images
    if images:
        # collect existing image paths only
        existing_paths: list[Path] = []
        for img in images:
            p = MEDIA_PATH / str(img)
            if p.exists():
                existing_paths.append(p)

        # Telegram albums: 2..10 items per media_group
        for i in range(0, len(existing_paths), 10):
            chunk = existing_paths[i : i + 10]
            if len(chunk) >= 2:
                media = [InputMediaPhoto(media=FSInputFile(p)) for p in chunk]
                await message.answer_media_group(media=media)
            elif len(chunk) == 1:
                await message.answer_photo(photo=FSInputFile(chunk[0]))

    # send text
    if text:
        await message.answer(text)


async def send_view_day_task(message: Message, mongo: Mongo, day_num: int, task_idx: int) -> None:
    """Shows a specific task of a chosen day (view-only mode)."""
    lesson = await mongo.get_lesson(int(day_num))
    if not lesson:
        await message.answer(f"Урок на день {day_num} не найден в базе.")
        return

    tasks = _lesson_to_tasks(lesson)
    total = len(tasks)
    if total == 0:
        await message.answer(f"В дне {day_num} нет заданий.")
        return

    task_idx = max(0, min(int(task_idx), total - 1))
    await message.answer(f"День {day_num}. Задание {task_idx + 1}/{total}")
    await _send_task_content(message, tasks[task_idx])

    await message.answer(
        "Выбор задания:",
        reply_markup=kb.task_kb(
            day_num=day_num,
            task_idx=task_idx,
            total_tasks=total,
            mode="view",
            allow_complete=False,
        ),
    )


async def send_active_day_current_task(
    message: Message,
    mongo: Mongo,
    *,
    tg_id: int,
    user: dict,
    day_num: int,
) -> None:
    """Shows the current task for the active (next) day; uses persisted progress."""
    lesson = await mongo.get_lesson(int(day_num))
    if not lesson:
        await message.answer(f"Урок на день {day_num} не найден в базе.")
        return

    tasks = _lesson_to_tasks(lesson)
    total = len(tasks)
    if total == 0:
        await message.answer(f"В дне {day_num} нет заданий.")
        return

    in_progress_day = int(user.get("in_progress_day") or 0)
    current_task = int(user.get("current_task", 0) or 0)

    # initialize progress for this day if needed
    if in_progress_day != int(day_num):
        current_task = 0
        await mongo.set_task_progress(tg_id, int(day_num), current_task)

    current_task = max(0, min(current_task, total - 1))

    await message.answer(f"День {day_num}. Задание {current_task + 1}/{total}")
    await _send_task_content(message, tasks[current_task])

    await message.answer(
        "Навигация:",
        reply_markup=kb.task_kb(
            day_num=day_num,
            task_idx=current_task,
            total_tasks=total,
            mode="active",
	    allow_complete=True,
        ),
    )

@router.message(CommandStart())
async def start(message: Message, state: FSMContext, mongo: Mongo):
    """Entry point.

    Existing users -> menu.
    New users -> consent documents, then registration.
    """
    tg_id = message.from_user.id
    user = await mongo.get_user(tg_id)

    if user:
        await state.clear()
        await render_menu(message, mongo, tg_id=tg_id)
        return

    await state.set_state(Consent.pending)
    await send_consents(message)


@router.message(Consent.pending)
async def consent_wait(message: Message):
    await message.answer(
        "Чтобы продолжить, нажми кнопку «✅ Ознакомился и согласен».",
        reply_markup=kb.consent_kb(),
    )

@router.message(Registration.name)
async def reg_name(message: Message, state: FSMContext):
    name = (message.text or "").strip()
    if not name:
        await message.answer("Напиши имя текстом.")
        return
    await state.update_data(name=name)
    await message.answer("Введи год рождения (например, 1990)")
    await state.set_state(Registration.birth_year)

@router.message(Registration.birth_year)
async def reg_birth_year(message: Message, state: FSMContext, mongo: Mongo):
    try:
        year = int((message.text or "").strip())
    except ValueError:
        await message.answer("Введи год рождения числом, например: 1990")
        return

    data = await state.get_data()
    name = data.get("name", "Пользователь")
    tg_id = message.from_user.id

    await mongo.create_user(tg_id=tg_id, name=name, birth_year=year)
    await state.clear()

    await message.answer(
        "Перед началом обучения необходимо пройти входное тестирование.\n"
        "Перейди по ссылкам ниже и заполни формы, затем нажми «Выполнено».",
        reply_markup=kb.entry_test_kb(),
    )

# ---------- Menu ----------
@router.callback_query(F.data == "menu:open")
async def menu_open(cb: CallbackQuery, mongo: Mongo):
    await render_menu(cb.message, mongo, tg_id=cb.from_user.id)
    await cb.answer()

@router.callback_query(F.data == "noop")
async def noop(cb: CallbackQuery):
    await cb.answer()


# ---------- Consent (before registration) ----------
@router.callback_query(F.data == "consent:resend")
async def consent_resend(cb: CallbackQuery, state: FSMContext):
    await send_consents(cb.message)
    await state.set_state(Consent.pending)
    await cb.answer()

@router.callback_query(F.data == "consent:agree")
async def consent_agree(cb: CallbackQuery, state: FSMContext, mongo: Mongo):
    tg_id = cb.from_user.id
    user = await mongo.get_user(tg_id)
    if user:
        # User already exists -> go to menu
        await state.clear()
        await render_menu(cb.message, mongo, tg_id=tg_id)
        await cb.answer()
        return
    await cb.message.answer("Отлично. Как тебя зовут?")
    await state.set_state(Registration.name)
    await cb.answer()

# ---------- Entry test ----------
@router.callback_query(F.data == "entry_test:open")
async def entry_test_open(cb: CallbackQuery):
    await cb.message.answer(
        "Входное тестирование:",
        reply_markup=kb.entry_test_kb(),
    )
    await cb.answer()

@router.callback_query(F.data == "entry_test:done")
async def entry_test_done(cb: CallbackQuery, mongo: Mongo):
    tg_id = cb.from_user.id
    await mongo.set_entry_test_completed(tg_id, True)
    await cb.message.answer("Отлично! Теперь можно начинать обучение.")
    await render_menu(cb.message, mongo, tg_id=tg_id)
    await cb.answer()

# ---------- Training: next day ----------
@router.callback_query(F.data == "training:next")
async def training_next(cb: CallbackQuery, mongo: Mongo):
    tg_id = cb.from_user.id
    user = await mongo.get_user(tg_id)
    if not user:
        await cb.message.answer("Не нашёл твою регистрацию. Нажми /start")
        await cb.answer()
        return

    if not user.get("entry_test_completed", False):
        await cb.message.answer("Сначала заверши входное тестирование.", reply_markup=kb.entry_test_kb())
        await cb.answer()
        return

    completed_day = int(user.get("completed_day", 0))
    day_num = completed_day + 1

    now_utc = datetime.now(timezone.utc)
    next_unlock_at = _normalize_dt(user.get("next_unlock_at"))
    if not _is_unlocked(now_utc, next_unlock_at) and day_num > 1:
        # Day 1 is always available right after entry test.
        await cb.message.answer(
            f"Следующий день будет доступен { _format_dt_local(next_unlock_at) } (по московскому времени)."
        )
        await cb.answer()
        return

    max_day = await mongo.get_max_day()
    if max_day and day_num > max_day:
        await cb.message.answer("Поздравляю! Ты прошёл(ла) все доступные дни обучения.")
        await render_menu(cb.message, mongo, tg_id=tg_id)
        await cb.answer()
        return

    # Send ONLY the current task for that day (task-by-task progression).
    await send_active_day_current_task(cb.message, mongo, tg_id=tg_id, user=user, day_num=day_num)
    await cb.answer()


# ---------- Training: next task (active day) ----------
@router.callback_query(F.data == "training:task_next")
async def training_task_next(cb: CallbackQuery, mongo: Mongo):
    tg_id = cb.from_user.id
    user = await mongo.get_user(tg_id)
    if not user or not user.get("entry_test_completed", False):
        await cb.message.answer("Сначала пройди /start и заверши входное тестирование.")
        await cb.answer()
        return

    completed_day = int(user.get("completed_day", 0))
    day_num = completed_day + 1

    now_utc = datetime.now(timezone.utc)
    next_unlock_at = _normalize_dt(user.get("next_unlock_at"))
    if not _is_unlocked(now_utc, next_unlock_at) and day_num > 1:
        await cb.message.answer(
            f"Следующий день будет доступен { _format_dt_local(next_unlock_at) } (по московскому времени)."
        )
        await cb.answer()
        return

    lesson = await mongo.get_lesson(day_num)
    if not lesson:
        await cb.message.answer(f"Урок на день {day_num} не найден в базе. Сообщи администратору.")
        await cb.answer()
        return

    tasks = _lesson_to_tasks(lesson)
    total = len(tasks)

    in_progress_day = int(user.get("in_progress_day") or 0)
    current_task = int(user.get("current_task", 0) or 0)

    # If progress wasn't initialized yet, start from 0.
    if in_progress_day != day_num:
        current_task = 0
        await mongo.set_task_progress(tg_id, day_num, current_task)

    if current_task >= total - 1:
        # Already at last task.
        await cb.answer("Это последнее задание дня.")
        await send_active_day_current_task(cb.message, mongo, tg_id=tg_id, user=await mongo.get_user(tg_id), day_num=day_num)
        return

    new_task = current_task + 1
    await mongo.set_task_progress(tg_id, day_num, new_task)
    # Re-read to reflect persisted progress in further logic.
    user2 = await mongo.get_user(tg_id) or user
    await send_active_day_current_task(cb.message, mongo, tg_id=tg_id, user=user2, day_num=day_num)
    await cb.answer()

# ---------- Training: complete day ----------
@router.callback_query(F.data.startswith("training:complete:"))
async def training_complete(cb: CallbackQuery, mongo: Mongo):
    tg_id = cb.from_user.id
    try:
        day_num = int(cb.data.split(":")[-1])
    except Exception:
        await cb.answer()
        return

    user = await mongo.get_user(tg_id)
    if not user:
        await cb.message.answer("Не нашёл твою регистрацию. Нажми /start")
        await cb.answer()
        return

    current_completed = int(user.get("completed_day", 0))
    entry_done = bool(user.get("entry_test_completed", False))
    if not entry_done:
        await cb.message.answer("Сначала заверши входное тестирование.", reply_markup=kb.entry_test_kb())
        await cb.answer()
        return

    # Only allow completing the currently available day (sequential progression).
    expected_day = current_completed + 1
    if day_num < expected_day:
        await cb.message.answer("Этот день уже был отмечен как выполненный ✅")
        await render_menu(cb.message, mongo, tg_id=tg_id)
        await cb.answer()
        return

    if day_num > expected_day:
        await cb.message.answer("Нельзя отметить будущий день. Проходи обучение по порядку ⏳")
        await cb.answer()
        return

    now_utc = datetime.now(timezone.utc)
    next_unlock_at = _normalize_dt(user.get("next_unlock_at"))
    if not _is_unlocked(now_utc, next_unlock_at) and day_num > 1:
        await cb.message.answer(
            f"Следующий день будет доступен { _format_dt_local(next_unlock_at) } (по московскому времени)."
        )
        await cb.answer()
        return

    # Enforce task-by-task completion: day can be completed only on the LAST task.
    lesson = await mongo.get_lesson(day_num)
    if lesson:
        tasks = _lesson_to_tasks(lesson)
        total = len(tasks)

        in_progress_day = int(user.get("in_progress_day") or 0)
        current_task = int(user.get("current_task", 0) or 0)

        if in_progress_day != day_num:
            # Progress isn't initialized yet for this day.
            current_task = 0
            await mongo.set_task_progress(tg_id, day_num, current_task)

        if current_task < total - 1:
            await cb.message.answer(
                f"Чтобы отметить день выполненным, нужно пройти все задания дня.\n"
                f"Сейчас у тебя задание {current_task + 1}/{total}."
            )
            user2 = await mongo.get_user(tg_id) or user
            await send_active_day_current_task(cb.message, mongo, tg_id=tg_id, user=user2, day_num=day_num)
            await cb.answer()
            return

    # Mark completion and schedule next unlock
    unlock_utc = _compute_next_unlock_at(now_utc)
    await mongo.mark_day_completed(tg_id=tg_id, completed_day=day_num, next_unlock_at=unlock_utc, last_completed_at=now_utc)

    await cb.message.answer(
        f"День {day_num} отмечен как выполненный ✅\n"
        f"Следующий день откроется { _format_dt_local(unlock_utc) } (по московскому времени)."
    )
    await render_menu(cb.message, mongo, tg_id=tg_id)
    await cb.answer()

# ---------- Training: choose day ----------
@router.callback_query(F.data.startswith("training:choose_page:"))
async def training_choose_page(cb: CallbackQuery, mongo: Mongo):
    try:
        page = int(cb.data.split(":")[-1])
    except Exception:
        page = 1

    page = max(page, 1)
    max_day = await mongo.get_max_day()
    if not max_day:
        await cb.message.answer("Уроки пока не загружены.")
        await cb.answer()
        return

    # Restrict browsing: only completed days + (optionally) currently available day.
    user = await mongo.get_user(cb.from_user.id)
    if not user or not user.get("entry_test_completed", False):
        await cb.message.answer("Сначала пройди регистрацию через /start и заверши входное тестирование.")
        await cb.answer()
        return

    completed_day = int(user.get("completed_day", 0))
    now_utc = datetime.now(timezone.utc)
    next_unlock_at = _normalize_dt(user.get("next_unlock_at"))
    can_view_current = _is_unlocked(now_utc, next_unlock_at)
    max_visible_day = completed_day + 1 if (can_view_current and completed_day + 1 <= max_day) else completed_day

    if max_visible_day <= 0:
        await cb.message.answer("Пока нечего выбирать. Начни с «Продолжить: день 1» в меню.")
        await cb.answer()
        return

    skip = (page - 1) * PAGE_SIZE
    days = await mongo.get_days(skip=skip, limit=PAGE_SIZE, max_day_num=max_visible_day)
    if not days and page > 1:
        # fallback to previous page
        page -= 1
        skip = (page - 1) * PAGE_SIZE
        days = await mongo.get_days(skip=skip, limit=PAGE_SIZE, max_day_num=max_visible_day)

    await cb.message.answer(
        "Выбери день:",
        reply_markup=kb.days_page_kb(days=days, page=page, page_size=PAGE_SIZE, max_day=max_visible_day),
    )
    await cb.answer()

@router.callback_query(F.data.startswith("training:show:"))
async def training_show_day(cb: CallbackQuery, mongo: Mongo):
    try:
        day_num = int(cb.data.split(":")[-1])
    except Exception:
        await cb.answer()
        return

    user = await mongo.get_user(cb.from_user.id)
    if not user or not user.get("entry_test_completed", False):
        await cb.message.answer("Сначала пройди регистрацию через /start и заверши входное тестирование.")
        await cb.answer()
        return

    completed_day = int(user.get("completed_day", 0))
    now_utc = datetime.now(timezone.utc)
    next_unlock_at = _normalize_dt(user.get("next_unlock_at"))
    unlocked = _is_unlocked(now_utc, next_unlock_at)
    current_day = completed_day + 1

    # Past days are always viewable; current day only if unlocked; future days blocked.
    if day_num <= completed_day:
        # Browsing mode: start from the first task.
        await send_view_day_task(cb.message, mongo, day_num, task_idx=0)
        await cb.answer()
        return

    if day_num == current_day and unlocked:
        # Active mode: resume current task (progress is persisted).
        await send_active_day_current_task(cb.message, mongo, tg_id=cb.from_user.id, user=user, day_num=day_num)
        await cb.answer()
        return

    if day_num == current_day and not unlocked:
        await cb.message.answer(
            f"Этот день ещё закрыт. Он будет доступен { _format_dt_local(next_unlock_at) } (по московскому времени)."
        )
        await cb.answer()
        return

    await cb.message.answer("Будущие дни недоступны. Проходи обучение по порядку ⏳")
    await cb.answer()


# ---------- Training: browse tasks of a day ----------
@router.callback_query(F.data.startswith("training:task_show:"))
async def training_task_show(cb: CallbackQuery, mongo: Mongo):
    tg_id = cb.from_user.id
    parts = cb.data.split(":")
    if len(parts) != 4:
        await cb.answer()
        return

    try:
        day_num = int(parts[2])
        task_idx = int(parts[3])
    except Exception:
        await cb.answer()
        return

    user = await mongo.get_user(tg_id)
    if not user or not user.get("entry_test_completed", False):
        await cb.message.answer("Сначала пройди регистрацию через /start и заверши входное тестирование.")
        await cb.answer()
        return

    completed_day = int(user.get("completed_day", 0))
    now_utc = datetime.now(timezone.utc)
    next_unlock_at = _normalize_dt(user.get("next_unlock_at"))
    unlocked = _is_unlocked(now_utc, next_unlock_at)
    current_day = completed_day + 1

    if day_num <= completed_day:
        await send_view_day_task(cb.message, mongo, day_num, task_idx)
        await cb.answer()
        return

    if day_num == current_day and unlocked:
        # For the active day we always show the persisted current task.
        await send_active_day_current_task(cb.message, mongo, tg_id=tg_id, user=user, day_num=day_num)
        await cb.answer()
        return

    if day_num == current_day and not unlocked:
        await cb.message.answer(
            f"Этот день ещё закрыт. Он будет доступен { _format_dt_local(next_unlock_at) } (по московскому времени)."
        )
        await cb.answer()
        return

    await cb.message.answer("Будущие дни недоступны. Проходи обучение по порядку ⏳")
    await cb.answer()

# ---------- Theory ----------
@router.callback_query(F.data == "theory:menu")
async def theory_menu(cb: CallbackQuery):
    await cb.message.answer("Выбери интересующую тему:", reply_markup=kb.theory_menu_kb())
    await cb.answer()

@router.callback_query(F.data.startswith("theory:topic:"))
async def theory_topic(cb: CallbackQuery):
    topic = cb.data.split(":")[-1]
    if topic == "startleffect":
        await cb.message.answer("Startle Effect:", reply_markup=kb.theory_file_kb("startle_effect"))
    elif topic == "illusions":
        await cb.message.answer("Иллюзии:", reply_markup=kb.theory_file_kb("illusions"))
    elif topic == "research":
        await cb.message.answer("Исследования:", reply_markup=kb.theory_file_kb("research"))
    await cb.answer()

@router.callback_query(F.data.startswith("theory:file:"))
async def theory_send_file(cb: CallbackQuery):
    key = cb.data.split(":")[-1]
    file_path = MEDIA_PATH / f"{key}.txt"
    if not file_path.exists():
        await cb.message.answer("Файл не найден.")
        await cb.answer()
        return

    await cb.message.answer_document(FSInputFile(file_path), caption="Вот файл:")
    await cb.answer()

# ---------- Convenience commands ----------
@router.message(Command("menu"))
async def cmd_menu(message: Message, mongo: Mongo):
    await render_menu(message, mongo, tg_id=message.from_user.id)
