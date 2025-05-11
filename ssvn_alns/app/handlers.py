from aiogram import Router, F, html
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery, InputMediaPhoto, FSInputFile
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from pathlib import Path

from . import keyboards as kb  # Предположим, что клавиатуры уже определены где-то в keyboards.py

router = Router()

# Словарь тестов по дням
tests = {
    1: "first_day",
    2: "second_day",
    3: "third_day"
}

FIRST_DAY_TASKS = {
    1: {
        "text": "Задание 1/3: На одной руке покажи детский жест примирения (сожми пальцы в кулак, а мизинец выпрями и слегка отклони). "
                "На другой руке покажи одобряющий жест — «класс» (сожми кулак, а затем подними большой палец вверх). "
                "Выполняй это упражнение поочередно правой и левой рукой.",
        "photos": ["first_day_task1_1.jpg", "first_day_task1_2.jpg"]
    },
    2: {
        "text": "Задание 2/3: Пометка «П» означает, что нужно поднять правую руку, «Л» - левую, а «О» - обе. "
                "Проговори вслух последовательно буквы, одновременно выполняя действие, прописанное под каждой из них. "
                "Упражнение считается выполненным, если ты без ошибок пройдешь все буквы от «А» до «Я» и в обратном направлении. "
                "Засекай время: сделать это нужно как можно быстрее!",
        "photos": ["first_day_task2_1.jpg"]
    },
    3: {
        "text": "Задание 3/3: Сядь удобно. Скрести ноги в лодыжках. Держи колени свободно. "
                "Держи колени свободно.  Наклонись вперед, руки плавно опусти вниз и сделай выдох, а затем выпрямись. "
                "Подними руки и сделай вдох. Делай упражнение, наклоняясь вперед, влево и вправо. "
                "Потом повтори упражнение, изменив положение ног.",
        "photos": ["first_day_task3_1.jpg"]
    }
}

MEDIA_PATH = Path(__file__).parent.parent / "media"

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
            f"Перед началом тренировки необходимо пройти входное тестирование.\n"
            f"Пожалуйста, перейдите по каждой из ссылок ниже и заполните форму. В поле “Уникальный номер” укажите ваш код: [уникальный номер 4-значный].",
            reply_markup=kb.entry_test  
        )
        await state.set_state(None)  # Сброс состояния

    except ValueError:
        await message.answer("Введите год рождения числом, например: 1990")

# --- Обработчик кнопки завершения входного теста ---
@router.callback_query(F.data == "entry_test_complete_call")
async def entry_test_done(query: CallbackQuery, state: FSMContext):
    await state.update_data(completed_tests=1)
    await query.message.answer(
        "Теперь вы можете начать первый день тренировки.",
        reply_markup=get_universal_kb(1)
    )

# --- Обработчик кнопки завершения любого теста ---
@router.callback_query(F.data == "test_complete_call")
async def test_done(query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    day = data.get('current_day')
    current_task = data.get('current_task', 1)
    completed = data.get('completed_tests', 0)
    
    if day == 1:
        if current_task < 3:  # Если есть еще задания
            next_task = current_task + 1
            await state.update_data(current_task=next_task)
            await show_day_task(query.message, next_task, state)
        else:
            await state.update_data(
                completed_tests=completed + 1,
                current_day=None,
                current_task=None
            )
            await query.message.answer(
                "Вы успешно завершили первый день тренировок!",
                reply_markup=get_universal_kb(completed + 1)
            )
    
    await query.answer()

# --- Тест первого дня ---
@router.callback_query(F.data == "first_day_test_call")
async def first_day_test(query: CallbackQuery, state: FSMContext):
    await state.update_data(
        current_day=1,
        current_task=1,
    )
    
    # Показываем первое задание
    await show_day_task(query.message, 1, state)
    await query.answer()

# функция для отображения заданий первого дня
async def show_day_task(message: Message, task_num: int, state: FSMContext):
    data = await state.get_data()
    day = data.get('current_day')
    
    if day == 1:
        task = FIRST_DAY_TASKS[task_num]
        
        media = [
            InputMediaPhoto(media=FSInputFile(MEDIA_PATH / photo))
            for photo in task["photos"]
        ]
        
        await message.answer_media_group(media=media)
        await message.answer(
            f"День 1. {task['text']}\n\n"
            f"Нажмите 'Выполнено', чтобы продолжить.",
            reply_markup=kb.complete
        )
        

# --- Тест второго дня через FSM ---
@router.callback_query(F.data == "second_day_test_call")
async def second_day_test(query: CallbackQuery, state: FSMContext):
    current = await state.get_state()
    if current is None:
        await query.message.answer("Сегодня второй день тренировки. Начинаем тестирование.")
        await query.message.answer(
            "1. Тест на счет. Засеки время и максимально быстро посчитай вслух от 1 до 120.\n"
            "Введите результат в секундах, например: 63"
        )
        await state.set_state(SecondTest.fast_count)
    else:
        await query.message.answer("Вы уже в процессе теста.")

@router.message(SecondTest.fast_count)
async def count_test(message: Message, state: FSMContext):
    try:
        time = int(message.text)
        photo_path=MEDIA_PATH / "second_day_task2_1.jpg"
        await state.update_data(fast_count=time)
        await message.answer(
            "2. Тест на запоминание слов. "
            "В течение 2 минут постарайся запомнить как можно больше записанных ниже слов. "
            "Напиши здесь, в чат, слова, которые запомнил. Сколько слов ты смог вспомнить за 2 минуты?"
        )
        await message.answer_photo(photo=FSInputFile(photo_path))
        await state.set_state(SecondTest.remembered_words)
    except ValueError:
        await message.answer("Введите число, например: 65")

@router.message(SecondTest.remembered_words)
async def words_test(message: Message, state: FSMContext):
    words = message.text.split()
    photo_path=MEDIA_PATH / "second_day_task3_1.jpg"
    await state.update_data(remembered_words=len(words))
    await message.answer(
        "3. Тест Струпа. Называй вслух цвет слов, делая это как можно быстрее. "
        "Будь внимателен: ты должен не читать слова, а называть их цвет. "
        "Если ошибешься, назови цвет еще раз. Отметь время, которое тебе понадобилось."
    )
    await message.answer_photo(photo=FSInputFile(photo_path))
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
        completed = data.get('completed_tests', 0)
        new_completed = completed + 1

        await state.update_data(completed_tests=new_completed)
        await state.set_state(None)

        await message.answer("Вы успешно завершили тестирование.", reply_markup=get_universal_kb(new_completed))
    except ValueError:
        await message.answer("Введите число, например: 34")

# --- Теория ---
@router.callback_query(F.data == "theory_call")
async def theory_handler(query: CallbackQuery):
    await query.message.answer("Выберите интересующую тему:", reply_markup=kb.theory)