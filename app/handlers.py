from __future__ import annotations

from pathlib import Path
from typing import Optional

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

# ---------- FSM for registration ----------
class Registration(StatesGroup):
    name = State()
    birth_year = State()

# ---------- Helpers ----------
async def render_menu(message: Message, mongo: Mongo) -> None:
    tg_id = message.from_user.id
    user = await mongo.get_user(tg_id)
    max_day = await mongo.get_max_day()

    if not user:
        # Should not happen often - fallback
        await message.answer("Давайте знакомиться. Как тебя зовут?")
        return

    completed_day = int(user.get("completed_day", 0))
    entry_done = bool(user.get("entry_test_completed", False))
    next_day = (completed_day + 1) if entry_done else None

    await message.answer(
        "Главное меню:",
        reply_markup=kb.menu_kb(next_day=next_day, completed_day=completed_day, max_day=max_day, entry_test_completed=entry_done),
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
        reply_markup=kb.lesson_kb(day_num) if allow_complete else kb.menu_kb(next_day=None, completed_day=0, max_day=0, entry_test_completed=True),
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
            await render_menu(message, mongo)
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
    await render_menu(cb.message, mongo)
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
    await render_menu(cb.message, mongo)
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

    max_day = await mongo.get_max_day()
    if max_day and day_num > max_day:
        await cb.message.answer("Поздравляю! Ты прошёл(ла) все доступные дни обучения.")
        await render_menu(cb.message, mongo)
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
    # Prevent decreasing progress
    new_completed = max(current_completed, day_num)

    await mongo.set_completed_day(tg_id, new_completed)

    await cb.message.answer(f"День {day_num} отмечен как выполненный ✅")
    await render_menu(cb.message, mongo)
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

    skip = (page - 1) * PAGE_SIZE
    days = await mongo.get_days(skip=skip, limit=PAGE_SIZE)
    if not days and page > 1:
        # fallback to previous page
        page -= 1
        skip = (page - 1) * PAGE_SIZE
        days = await mongo.get_days(skip=skip, limit=PAGE_SIZE)

    await cb.message.answer(
        "Выбери день:",
        reply_markup=kb.days_page_kb(days=days, page=page, page_size=PAGE_SIZE, max_day=max_day),
    )
    await cb.answer()

@router.callback_query(F.data.startswith("training:show:"))
async def training_show_day(cb: CallbackQuery, mongo: Mongo):
    try:
        day_num = int(cb.data.split(":")[-1])
    except Exception:
        await cb.answer()
        return

    # Allow view any day, but completion only when user marks it.
    await send_lesson(cb.message, mongo, day_num)
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
    await render_menu(message, mongo)
