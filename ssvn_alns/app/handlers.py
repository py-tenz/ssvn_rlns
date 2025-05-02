from aiogram import Router, F, html
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from . import keyboards as kb  # Предположим, что клавиатуры уже определены где-то в keyboards.py

router = Router()

# Словарь тестов по дням
tests = {
    1: "first_day",
    2: "second_day",
    3: "third_day"
}

# Генерация универсальной клавиатуры
def get_universal_kb(completed_tests):
    next_test_index = completed_tests
    if next_test_index >= len(tests):
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Вы прошли все тесты!", callback_data="done")]
        ])

    next_test_key = tests[next_test_index]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Перейти к тестированию", callback_data=f"{next_test_key}_test_call")],
        [InlineKeyboardButton(text="Изучить теорию", callback_data="theory_call")]
    ])

# --- FSM для регистрации ---
class Registration(StatesGroup):
    name = State()
    birth_year = State()

# --- FSM для второго дня тестирования ---
class SecondTest(StatesGroup):
    fast_count = State()
    remembered_words = State()
    stroop_time = State()

# --- Начало работы ---
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    data = await state.get_data()
    if 'name' in data:
        await message.answer("Вы уже зарегистрированы.")
        completed = data.get('completed_tests', 0)
        await message.answer(
            text="Вы можете продолжить обучение или пройти новые тесты.",
            reply_markup=get_universal_kb(completed)
        )
        return

    await message.answer("Давайте знакомиться. Как вас зовут?")
    await state.set_state(Registration.name)

# --- Регистрация имени ---
@router.message(Registration.name)
async def reg_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите год рождения")
    await state.set_state(Registration.birth_year)

# --- Регистрация года рождения ---
@router.message(Registration.birth_year)
async def reg_birth_year(message: Message, state: FSMContext):
    try:
        year = int(message.text)
        await state.update_data(birth_year=year, completed_tests=0)
        data = await state.get_data()

        await message.answer(
            f"Отлично! Вы успешно зарегистрировались.\n"
            f"Имя: {data['name']}\n"
            f"Год рождения: {data['birth_year']}\n"
            f"Тестов выполнено: 0\n"
            f"Теперь вам доступны задания первого дня тренировок.",
            reply_markup=kb.entry_test  
        )
        await state.set_state(None)  # Сброс состояния

    except ValueError:
        await message.answer("Введите год рождения числом, например: 1990")

# --- Обработчик кнопки завершения входного теста ---
@router.callback_query(F.data == "entry_test_complete_call")
async def entry_test_done(query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.update_data(completed_tests=1)
    await query.message.answer(
        "Теперь вы можете начать первый день тренировки.",
        reply_markup=get_universal_kb(1)
    )

# --- Обработчик кнопки завершения любого теста ---
@router.callback_query(F.data == "test_complete_call")
async def test_done(query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    completed = data.get('completed_tests', 0) + 1
    await state.update_data(completed_tests=completed)

    if completed >= len(tests):
        await query.message.answer("🎉 Поздравляем! Вы успешно завершили все тесты!")
    else:
        await query.message.answer(
            f"Вы завершили тест номер {completed-1}!",
            reply_markup=get_universal_kb(completed)
        )

# --- Тест первого дня ---
@router.callback_query(F.data == "first_day_test_call")
async def first_day_test(query: CallbackQuery):
    await query.message.answer(
        "Сегодня первый день тренировки. Выполните следующие упражнения:\n"
        "1. На одной руке покажите детский жест примирения (сожмите пальцы в кулак, а мизинец выпрямите).\n"
        "2. На другой руке покажите одобряющий жест — «класс».\n"
        "Выполняйте упражнение поочередно правой и левой рукой."
    )
    await query.message.answer("Нажмите 'Выполнено', чтобы продолжить.", reply_markup=kb.complete)

# --- Тест второго дня через FSM ---
@router.callback_query(F.data == "second_day_test_call")
async def second_day_test(query: CallbackQuery, state: FSMContext):
    current = await state.get_state()
    if current is None:
        await query.message.answer("Сегодня второй день тренировки. Начинаем тестирование.")
        await query.message.answer(
            "1. Засеките время и посчитайте вслух от 1 до 120 как можно быстрее. "
            "Введите результат в секундах, например: 63"
        )
        await state.set_state(SecondTest.fast_count)
    else:
        await query.message.answer("Вы уже в процессе теста.")

@router.message(SecondTest.fast_count)
async def count_test(message: Message, state: FSMContext):
    try:
        time = int(message.text)
        await state.update_data(fast_count=time)
        await message.answer(
            "2. За 2 минуты запомните как можно больше слов из списка. "
            "Запишите слова, которые запомнили."
        )
        await state.set_state(SecondTest.remembered_words)
    except ValueError:
        await message.answer("Введите число, например: 65")

@router.message(SecondTest.remembered_words)
async def words_test(message: Message, state: FSMContext):
    words = message.text.split()
    await state.update_data(remembered_words=len(words))
    await message.answer(
        "3. Тест Струпа: называйте цвет слов, не читая их. Засеките время в секундах."
    )
    await state.set_state(SecondTest.stroop_time)

@router.message(SecondTest.stroop_time)
async def stroop_test(message: Message, state: FSMContext):
    try:
        time = int(message.text)
        await state.update_data(stroop_time=time)
        data = await state.get_data()

        await message.answer(
            f"Ваши результаты за второй день:\n"
            f"1. Счет: {data['fast_count']} сек.\n"
            f"2. Запомнил слов: {data['remembered_words']}\n"
            f"3. Тест Струпа: {data['stroop_time']} сек."
        )
        await state.set_state(None)
        await message.answer("Нажмите 'Выполнено', чтобы продолжить.", reply_markup=kb.complete)
    except ValueError:
        await message.answer("Введите число, например: 34")

# --- Теория ---
@router.callback_query(F.data == "theory_call")
async def theory_handler(query: CallbackQuery):
    await query.message.answer("Выберите интересующую тему:", reply_markup=kb.theory)