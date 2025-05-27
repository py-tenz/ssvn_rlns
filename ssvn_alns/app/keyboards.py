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
        [InlineKeyboardButton(text="Иллюзии", url="https://docs.google.com/document/d/1E8ibRMK-u-WXHECDxp583TZk1g5DgzAs/edit?tab=t.0#heading=h.rihmfqm9vg6")],
        [InlineKeyboardButton(text="Startle Effect", url="https://docs.google.com/document/d/1m4bhAjZB0QBkVtHP2bfHzATYU4nThbAF/edit?tab=t.0")],
        [InlineKeyboardButton(text="Исследования, подтвеждающие валидность чат-бота", url="https://docs.google.com/document/d/1d-bfSeZU7U-IfZa4BmNBaHAXpSSb_U1J/edit?tab=t.0")],
        [InlineKeyboardButton(text="Вернуться в основное меню", callback_data="return_main_menu")]

    ]
)

startle_effect = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Тeория", callback_data="open_word_file:startle_effect")],
        [InlineKeyboardButton(text="Вернуться в основное меню", callback_data="back_to_main_menu")]
    ])
illusions = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Тeория", callback_data="open_word_file:illusions")],
        [InlineKeyboardButton(text="Вернуться в основное меню", callback_data="back_to_main_menu")]
    ])
research = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Тeория", callback_data="open_word_file:research")],
        [InlineKeyboardButton(text="Вернуться в основное меню", callback_data="back_to_main_menu")]
    ])

#Клавиатура завершения действия
complete = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Выполнено", callback_data="test_complete_call")]
    ]
)