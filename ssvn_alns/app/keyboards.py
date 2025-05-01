from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.common import tests, user





## 3. Входное тестирование
entry_test = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Первое тестирование", url="https://forms.gle/95pxWHj4rvwJzN318")], 
        [InlineKeyboardButton(text="Второе тестирование", url="https://forms.gle/khJb1FowpBWKMujw9")],
        [InlineKeyboardButton(text="Третье тестирование", url="https://forms.gle/HoepHvnXxNqAMHhX6")],
        [InlineKeyboardButton(text="Четвертое тестирование", url="https://forms.gle/MW6TF3bZEeEB4ywa6")],
        [InlineKeyboardButton(text="Выполнено", callback_data="entry_test_complete_call")]
)


##4. Задание первого дня
universal_kb = InlineKeyboardMarkup(
    inline_keyboard=[
<<<<<<< HEAD
        [InlineKeyboardButton(text="Перейти к тестированию", callback_data=f"{tests[user.completed_tests_state+2]}_test_call")],
        [InlineKeyboardButton(text="Изучить теорию", callback_data="first_day_theory_call")]
=======
        [InlineKeyboardButton(text="Перейти к тестированию", callback_data="first_day_test_call")],
        [InlineKeyboardButton(text="Изучить теорию", callback_data="theory_call")]
    ]
)

theory = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Иллюзии")],
        [InlineKeyboardButton(text="Startle Effect")],
        [InlineKeyboardButton(text="Исследования подтрвеждающие валидность чат-бота")],
        [InlineKeyboardButton(text="Вернуться в основное меню")]
>>>>>>> 14beb867bc535194148f445ad9d18f07dd08bbe6
    ]
)

#Клавиатура завершения действия
complete = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Выполнено", callback_data="test_complete_call")]
    ]
)