from aiogram import Router, F, html
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery, InputMediaPhoto, FSInputFile
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from pathlib import Path

from . import keyboards as kb 

router = Router()

# Словарь тестов по дням
tests = {
    1: "first_day",
    2: "second_day",
    3: "third_day"
}


# Структура для подстановки различных задания для первого дня
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

# Универсальная клавиатура для перехода к другим тестировочным дням.
def get_universal_kb(completed_tests):
    """
    На вход подается счетчик выполненных тестов
    """
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

# FSM для регистрации
class Registration(StatesGroup):
    name = State()
    birth_year = State()

# FSM для второго дня тестирования
class SecondTest(StatesGroup):
    fast_count = State()
    remembered_words = State()
    stroop_time = State()

# Обработчик команды start, запускает процесс регистрации нового пользователя или проверяет уже зарегистрированного
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    data = await state.get_data()
    if 'name' in data:
        await message.answer("Ты уже зарегистрирован.")
        completed = data.get('completed_tests', 0)
        await message.answer(
            text="Можешь продолжить обучение или пройти новые тесты.",
            reply_markup=get_universal_kb(completed)
        )
        return

    await message.answer("Давайте знакомиться. Как тебя зовут?")
    await state.set_state(Registration.name)

# Регистрация имени 
@router.message(Registration.name)
async def reg_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введи год рождения")
    await state.set_state(Registration.birth_year)

# Регистрация года рождения, вывод клавиатуры с 
@router.message(Registration.birth_year)
async def reg_birth_year(message: Message, state: FSMContext):
    try:
        year = int(message.text)
        await state.update_data(birth_year=year, completed_tests=0)

        await message.answer(
            f"Перед началом тренировки необходимо пройти входное тестирование.\n"
            f"Пожалуйста, перейди по каждой из ссылок ниже и заполните форму. В поле “Уникальный номер” укажи свой код: [уникальный номер 4-значный].",
            reply_markup=kb.entry_test  
        )
        await state.clear() # Сброс состояния после регистрации

    except ValueError:
        await message.answer("Введи год рождения числом, например: 1990")

# Обработчик кнопки завершения входного теста
@router.callback_query(F.data == "entry_test_complete_call")
async def entry_test_done(query: CallbackQuery, state: FSMContext):
    await state.update_data(completed_tests=1)
    await query.message.answer(
        "Теперь ты можешь начать тренировки.",
        reply_markup=get_universal_kb(1)
    )

# Обработчик кнопки завершения любого теста 
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
                "Ты успешно завершил первый день тренировок!",
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
            f"Нажми 'Выполнено', чтобы продолжить.",
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
            "Введи результат в секундах, например: 63"
        )
        await state.set_state(SecondTest.fast_count)
    else:
        await query.message.answer("Ты уже в процессе теста.")

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
        await message.answer("Введи число, например: 65")

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
            f"Твои результаты за второй день:\n"
            f"1. Счет: {data['fast_count']} сек.\n"
            f"2. Запомнил слов: {data['remembered_words']}\n"
            f"3. Тест Струпа: {data['stroop_time']} сек."
        )
        completed = data.get('completed_tests', 0)
        new_completed = completed + 1

        await state.update_data(completed_tests=new_completed)
        await state.set_state(None)

        await message.answer("Ты успешно завершили тестирование.", reply_markup=get_universal_kb(new_completed))
    except ValueError:
        await message.answer("Введи число, например: 34")

# --- Теория ---
@router.callback_query(F.data == "theory_call")
async def theory_handler(query: CallbackQuery):
    await query.message.answer("Выбери интересующую тему:", reply_markup=kb.theory)

@router.callback_query(F.data.startswith("theory:"))
async def theory_call_handler(callback: CallbackQuery):
    topic = callback.data.removeprefix("theory:")

    if topic == "startleffect":
        await callback.message.answer(
            text="Перейдите к теории по кнопке ниже:",
            reply_markup=kb.startle_effect
        )
    elif topic == "illusions":
        await callback.message.answer(
            text="Перейдите к теории по кнопке ниже:",
            reply_markup=kb.illusions
        )
    elif topic == "research":
        await callback.message.answer(
            text="Перейдите к теории по кнопке ниже:",
            reply_markup=kb.research
        )


@router.callback_query(F.data.startswith("open_word_file:"))
async def send_word_file(callback: CallbackQuery):
    file = FSInputFile(f"media/{callback.data.removeprefix("open_word_file:")}.txt")
    await callback.message.answer_document(file, caption="Вот ваш файл:")
    await callback.answer()

