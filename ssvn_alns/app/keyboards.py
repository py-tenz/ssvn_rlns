from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo


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
theory = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Иллюзии", callback_data="theory:illusions")],
        [InlineKeyboardButton(text="Startle Effect", callback_data="theory:startleffect")],
        [InlineKeyboardButton(text="Исследования подтвеждающие валидность чат-бота", callback_data="theory:research")],
        [InlineKeyboardButton(text="Вернуться в основное меню", callback_data="test_complete_call")]

    ]
)

startle_effect = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Тeория", web_app=WebAppInfo(url="https://docs.google.com/document/d/1rqipDyv4OkAYrjmXJmFMlCcoqf3xLZ2l_pc2q2OLAkE/edit?tab=t.0"))],
        [InlineKeyboardButton(text="Вернуться в основное меню", callback_data="test_complete_call")]
    ])
illusions = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Тeория", web_app=WebAppInfo(url="https://docs.google.com/document/d/1rqipDyv4OkAYrjmXJmFMlCcoqf3xLZ2l_pc2q2OLAkE/edit?tab=t.0"))],
        [InlineKeyboardButton(text="Вернуться в основное меню", callback_data="test_complete_call")]
    ])
research = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Тeория", web_app=WebAppInfo(url="https://docs.google.com/document/d/1rqipDyv4OkAYrjmXJmFMlCcoqf3xLZ2l_pc2q2OLAkE/edit?tab=t.0"))],
        [InlineKeyboardButton(text="Вернуться в основное меню", callback_data="test_complete_call")]
    ])

#Клавиатура завершения действия
complete = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Выполнено", callback_data="test_complete_call")]
    ]
)