from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.common import tests, polzovatel






## 3. Входное тестирование
entry_test = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Первое тестирование", url="https://forms.gle/95pxWHj4rvwJzN318")], 
        [InlineKeyboardButton(text="Второе тестирование", url="https://forms.gle/khJb1FowpBWKMujw9")],
        [InlineKeyboardButton(text="Третье тестирование", url="https://forms.gle/HoepHvnXxNqAMHhX6")],
        [InlineKeyboardButton(text="Четвертое тестирование", url="https://forms.gle/MW6TF3bZEeEB4ywa6")],
        [InlineKeyboardButton(text="Выполнено", callback_data="entry_test_complete_call")],

    ] 
)


##4. Задание первого дня
universal_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Перейти к тестированию", callback_data={tests[polzovatel.completed_tests_state]} + "_test_call")],
        [InlineKeyboardButton(text="Изучить теорию", callback_data="theory_call")]
    ]
)

theory = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Иллюзии", callback_data="1")],
        [InlineKeyboardButton(text="Startle Effect", callback_data="2")],
        [InlineKeyboardButton(text="Исследования подтрвеждающие валидность чат-бота", callback_data="3")],
        [InlineKeyboardButton(text="Вернуться в основное меню", callback_data="entry_test_complete_call")]

    ]
)

#Клавиатура завершения действия
complete = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Выполнено", callback_data="test_complete_call")]
    ]
)