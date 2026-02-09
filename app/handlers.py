from __future__ import annotations

from pathlib import Path
from typing import Optional
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
PAGE_SIZE = 10  # for day picker

MOSCOW_TZ = ZoneInfo("Europe/Moscow")

# ---------- FSM for registration ----------
class Registration(StatesGroup):
    name = State()
    birth_year = State()

# ---------- Helpers ----------
def _format_dt_berlin(dt_utc: datetime) -> str:
    """Human-friendly datetime in Europe/Berlin, e.g. 10.02.2026 08:00."""
    dt_local = dt_utc.astimezone(BERLIN_TZ)
    return dt_local.strftime("%d.%m.%Y %H:%M")


def _compute_next_unlock_at(now_utc: datetime) -> datetime:
    """Next day at 08:00 Europe/Berlin, returned as UTC datetime."""
    now_local = now_utc.astimezone(BERLIN_TZ)
    next_date = now_local.date() + timedelta(days=1)
    unlock_local = datetime.combine(next_date, time(hour=8, minute=0), tzinfo=BERLIN_TZ)
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


async def render_menu(message: Message, mongo: Mongo, tg_id: int) -> None:
    """Render main menu into the given chat message.

    IMPORTANT: In callback queries, cb.message.from_user is the bot (message author),
    so tg_id must be provided explicitly (cb.from_user.id).
    """
    user = await mongo.get_user(tg_id)
    max_day = await mongo.get_max_day()

    if not user:
        # Should not happen often - fallback
        await message.answer("Давайте знакомиться. Как тебя зовут?")
        return

    completed_day = int(user.get("completed_day", 0))
    entry_done = bool(user.get("entry_test_completed", False))
    next_day = (completed_day + 1) if entry_done else None

    now_utc = datetime.now(timezone.utc)
    next_unlock_at = _normalize_dt(user.get("next_unlock_at"))
    unlocked = _is_unlocked(now_utc, next_unlock_at)

    # You can continue only when next day exists and unlock time has come.
    can_continue = bool(entry_done and next_day and (next_day <= max_day) and unlocked)
    locked_until = _format_dt_berlin(next_unlock_at) if (next_unlock_at and not unlocked) else None

    await message.answer(
        "Главное меню:",
        reply_markup=kb.menu_kb(
            next_day=next_day,
            completed_day=completed_day,
            max_day=max_day,
            entry_test_completed=entry_done,
            can_continue=can_continue,
            locked_until=locked_until,
        ),
    )

async def send_lesson(message: Message, mongo: Mongo, day_num: int, *, allow_complete: bool = True) -> None:
    lesson = await mongo.get_lesson(day_num)
    if not lesson:
        await message.answer(
            f"Урок на день {day_num} не найден в базе. Сообщи администратору."
        )
        return

    text = str(lesson.get("text", "")).strip()
    images = lesson.get("images") or []
    if not isinstance(images, list):
        images = []

    # Telegram allows max 10 media in one album
    if images:
        chunks = [images[i:i+10] for i in range(0, len(images), 10)]
        for chunk in chunks:
            media = []
            for img in chunk:
                img_path = MEDIA_PATH / str(img)
                if img_path.exists():
                    media.append(InputMediaPhoto(media=FSInputFile(img_path)))
            if media:
                await message.answer_media_group(media=media)

    caption = f"День {day_num}\n\n{text}" if text else f"День {day_num}"
    await message.answer(
        caption,
        reply_markup=kb.lesson_kb(day_num) if allow_complete else kb.menu_kb(next_day=None, completed_day=0, max_day=0, entry_test_completed=True, can_continue=False, locked_until=None),
    )

# ---------- /start ----------
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, mongo: Mongo):
    tg_id = message.from_user.id
    user = await mongo.get_user(tg_id)

    if user:
        await state.clear()
        if not user.get("entry_test_completed", False):
            await message.answer(
                "Перед началом обучения пройди входное тестирование и нажми «Выполнено».",
                reply_markup=kb.entry_test_kb(),
            )
        else:
            await render_menu(message, mongo, tg_id=tg_id)
        return

    await message.answer("Давайте знакомиться. Как тебя зовут?")
    await state.set_state(Registration.name)

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
            f"Следующий день будет доступен { _format_dt_berlin(next_unlock_at) } (по московскому времени)."
        )
        await cb.answer()
        return

    max_day = await mongo.get_max_day()
    if max_day and day_num > max_day:
        await cb.message.answer("Поздравляю! Ты прошёл(ла) все доступные дни обучения.")
        await render_menu(cb.message, mongo, tg_id=tg_id)
        await cb.answer()
        return

    await send_lesson(cb.message, mongo, day_num)
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
            f"Следующий день будет доступен { _format_dt_berlin(next_unlock_at) } (по времени Берлина)."
        )
        await cb.answer()
        return

    # Mark completion and schedule next unlock
    unlock_utc = _compute_next_unlock_at(now_utc)
    await mongo.mark_day_completed(tg_id=tg_id, completed_day=day_num, next_unlock_at=unlock_utc, last_completed_at=now_utc)

    await cb.message.answer(
        f"День {day_num} отмечен как выполненный ✅\n"
        f"Следующий день откроется { _format_dt_berlin(unlock_utc) } (по времени Берлина)."
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
        await send_lesson(cb.message, mongo, day_num, allow_complete=False)
        await cb.answer()
        return

    if day_num == current_day and unlocked:
        await send_lesson(cb.message, mongo, day_num, allow_complete=True)
        await cb.answer()
        return

    if day_num == current_day and not unlocked:
        await cb.message.answer(
            f"Этот день ещё закрыт. Он будет доступен { _format_dt_berlin(next_unlock_at) } (по времени Берлина)."
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
