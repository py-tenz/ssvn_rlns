from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

## 3. Входное тестирование
entry_test = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Первое тестирование", url="https://forms.gle/95pxWHj4rvwJzN318", callback_data="")], 
        [InlineKeyboardButton(text="Второе тестирование", url="https://forms.gle/khJb1FowpBWKMujw9", callback_data="")],
        [InlineKeyboardButton(text="Третье тестирование", url="https://forms.gle/HoepHvnXxNqAMHhX6", callback_data="")],
        [InlineKeyboardButton(text="Четвертое тестирование", url="https://forms.gle/MW6TF3bZEeEB4ywa6", callback_data="")],
    ]
)


##4. Задание первого дня
first_day = InlineKeyboardButton(
    inline_keyboard=[
        [InlineKeyboardButton(text="Перейти к тестированию", callback_data="first_day_test_call")],
        [InlineKeyboardButton(text="Изучить теорию", callback_data="first_day_theory_call")]
    ]
)

#Клавиатура завершения действия
complete = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Выполнено", callback_data="test_complete_call")]
    ]
)