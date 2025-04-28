from aiogram import types as T


## 3. Входное тестирование
entry_test = T.InlineKeyboardMarkup(
    inline_keyboard=[
        [T.InlineKeyboardButton(text="Первое тестирование", url="https://forms.gle/95pxWHj4rvwJzN318", callback_data="")], 
        [T.InlineKeyboardButton(text="Второе тестирование", url="https://forms.gle/khJb1FowpBWKMujw9", callback_data="")],
        [T.InlineKeyboardButton(text="Третье тестирование", url="https://forms.gle/HoepHvnXxNqAMHhX6", callback_data="")],
        [T.InlineKeyboardButton(text="Четвертое тестирование", url="https://forms.gle/MW6TF3bZEeEB4ywa6", callback_data="")],
    ]
)


# ##4. Задание первого дня
# first_day = T.InlineKeyboardButton(
#     inline_keyboard=[
#         [T.InlineKeyboardButton(text="Перейти к тестированию", callback_data="first_day_test_call")],
#         [T.InlineKeyboardButton(text="Изучить теорию", callback_data="first_day_theory_call")]
#     ]
# )

# #Клавиатура завершения действия
# complete = T.InlineKeyboardMarkup(
#     inline_keyboard=[
#         [T.InlineKeyboardButton(text="Выполнено", callback_data="test_complete_call")]
#     ]
# )