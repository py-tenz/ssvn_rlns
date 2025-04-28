from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

entry_test = InlineKeyboardMarkup[
  inline_keyboard=[
     [InlineKeyboardButton(text="Первое тестирование", url="https://forms.gle/95pxWHj4rvwJzN318")]
     [InlineKeyboardButton(text="Второе тестирование", url="https://forms.gle/khJb1FowpBWKMujw9")]
     [InlineKeyboardButton(text="Третье тестирование", url="https://forms.gle/HoepHvnXxNqAMHhX6")]
     [InlineKeyboardButton(text="Четвертое тестирование", url="https://forms.gle/MW6TF3bZEeEB4ywa6")]
  ]
]

first_day_test = InlineKeyboardMarkup[
  inline_keyboard=[
     [InlineKeyboardButton(text="Перейти к тренировке")]
     [InlineKeyboardButton(text="Изучить теорию")]
  ]
]

