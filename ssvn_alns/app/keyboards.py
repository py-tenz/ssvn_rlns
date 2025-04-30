from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton




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
first_day = InlineKeyboardMarkup(
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