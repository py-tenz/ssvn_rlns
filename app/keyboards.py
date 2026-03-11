from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def menu_kb(
    *,
    next_day: int | None,
    completed_day: int,
    max_day: int,
    entry_test_completed: bool,
    final_test_completed: bool = False,
    can_continue: bool = True,
    locked_until: str | None = None,
) -> InlineKeyboardMarkup:
    rows = []
    if not entry_test_completed:
        rows.append([InlineKeyboardButton(text="Входное тестирование", callback_data="entry_test:open")])
    else:
        finished = bool(max_day) and completed_day >= max_day
        if finished and not final_test_completed:
            rows.append([InlineKeyboardButton(text="Итоговое тестирование", callback_data="final_test:open")])
        if (not finished) and next_day and next_day <= max_day and can_continue:
            rows.append([InlineKeyboardButton(text=f"Продолжить: день {next_day}", callback_data="training:next")])
        elif (not finished) and next_day and next_day <= max_day and locked_until:
            rows.append([InlineKeyboardButton(text=f"Следующий день откроется {locked_until}", callback_data="noop")])
        rows.append([InlineKeyboardButton(text="Выбрать день", callback_data="training:choose_page:1")])

    rows.append([InlineKeyboardButton(text="Изучить теорию", callback_data="theory:menu")])

    if not max_day:
        status = "Уроки пока не загружены"
    else:
        finished = completed_day >= max_day
        if finished and final_test_completed:
            status = f"Обучение завершено ✅ {completed_day}/{max_day}"
        elif finished and not final_test_completed:
            status = f"Пройдено дней: {completed_day}/{max_day} • осталось итоговое тестирование"
        else:
            status = f"Пройдено дней: {completed_day}/{max_day}"
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



def final_test_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Первое тестирование", url="https://forms.gle/95pxWHj4rvwJzN318")],
            [InlineKeyboardButton(text="Второе тестирование", url="https://forms.gle/khJb1FowpBWKMujw9")],
            [InlineKeyboardButton(text="Третье тестирование", url="https://forms.gle/HoepHvnXxNqAMHhX6")],
            [InlineKeyboardButton(text="Четвертое тестирование", url="https://forms.gle/MW6TF3bZEeEB4ywa6")],
            [InlineKeyboardButton(text="Выполнено", callback_data="final_test:done")],
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


def task_kb(*, day_num: int, task_idx: int, total_tasks: int, mode: str, allow_complete: bool) -> InlineKeyboardMarkup:
    """Keyboard for task-by-task flow.

    mode:
      - "active": user is completing the current (next) day; progress is persisted.
      - "view": user is just browsing a day; progress is NOT persisted and completion is disabled.
    """
    rows: list[list[InlineKeyboardButton]] = []

    is_last = task_idx >= (total_tasks - 1)
    if not is_last:
        if mode == "active":
            rows.append([InlineKeyboardButton(text="Перейти к следующему заданию ➡️", callback_data="training:task_next")])
        else:
            rows.append(
                [
                    InlineKeyboardButton(
                        text="Перейти к следующему заданию ➡️",
                        callback_data=f"training:task_show:{day_num}:{task_idx+1}",
                    )
                ]
            )
    else:
        # No "next" button on the last task.
        if allow_complete:
            rows.append([InlineKeyboardButton(text="День выполнен ✅", callback_data=f"training:complete:{day_num}")])

    rows.append([InlineKeyboardButton(text="В меню", callback_data="menu:open")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

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


def consent_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Ознакомился и согласен", callback_data="consent:agree")],
            [InlineKeyboardButton(text="🔁 Отправить файлы ещё раз", callback_data="consent:resend")],
        ]
    )
