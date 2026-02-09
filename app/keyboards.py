from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def menu_kb(
    *,
    next_day: int | None,
    completed_day: int,
    max_day: int,
    entry_test_completed: bool,
    can_continue: bool = True,
    locked_until: str | None = None,
) -> InlineKeyboardMarkup:
    rows = []
    if not entry_test_completed:
        rows.append([InlineKeyboardButton(text="Входное тестирование", callback_data="entry_test:open")])
    else:
        if next_day and next_day <= max_day and can_continue:
            rows.append([InlineKeyboardButton(text=f"Продолжить: день {next_day}", callback_data="training:next")])
        elif next_day and next_day <= max_day and locked_until:
            rows.append([InlineKeyboardButton(text=f"Следующий день откроется {locked_until}", callback_data="noop")])
        rows.append([InlineKeyboardButton(text="Выбрать день", callback_data="training:choose_page:1")])

    rows.append([InlineKeyboardButton(text="Изучить теорию", callback_data="theory:menu")])

    status = f"Пройдено дней: {completed_day}/{max_day}" if max_day else "Уроки пока не загружены"
    rows.append([InlineKeyboardButton(text=status, callback_data="noop")])

    return InlineKeyboardMarkup(inline_keyboard=rows)

def entry_test_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Первое тестирование", url="https://forms.gle/95pxWHj4rvwJzN318")],
            [InlineKeyboardButton(text="Второе тестирование", url="https://forms.gle/khJb1FowpBWKMujw9")],
            [InlineKeyboardButton(text="Третье тестирование", url="https://forms.gle/HoepHvnXxNqAMHhX6")],
            [InlineKeyboardButton(text="Четвертое тестирование", url="https://forms.gle/MW6TF3bZEeEB4ywa6")],
            [InlineKeyboardButton(text="Выполнено", callback_data="entry_test:done")],
            [InlineKeyboardButton(text="В меню", callback_data="menu:open")],
        ]
    )

def lesson_kb(day_num: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Выполнено", callback_data=f"training:complete:{day_num}")],
            [InlineKeyboardButton(text="В меню", callback_data="menu:open")],
        ]
    )

def days_page_kb(days: list[int], page: int, page_size: int, max_day: int) -> InlineKeyboardMarkup:
    # Buttons by 2 in a row
    rows = []
    row = []
    for d in days:
        row.append(InlineKeyboardButton(text=f"День {d}", callback_data=f"training:show:{d}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)

    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"training:choose_page:{page-1}"))
    # next page exists if page*page_size < max_day (rough)
    if page * page_size < max_day:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"training:choose_page:{page+1}"))
    if nav:
        rows.append(nav)

    rows.append([InlineKeyboardButton(text="В меню", callback_data="menu:open")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def theory_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Иллюзии", callback_data="theory:topic:illusions")],
            [InlineKeyboardButton(text="Startle Effect", callback_data="theory:topic:startleffect")],
            [InlineKeyboardButton(text="Исследования", callback_data="theory:topic:research")],
            [InlineKeyboardButton(text="В меню", callback_data="menu:open")],
        ]
    )

def theory_file_kb(topic_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Открыть файл", callback_data=f"theory:file:{topic_key}")],
            [InlineKeyboardButton(text="В меню", callback_data="menu:open")],
        ]
    )
