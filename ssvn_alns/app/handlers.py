from aiogram import Router, F, html
from aiogram.filters import CommandStart

from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from . import keyboards as kb
from aiogram.types import Message, CallbackQuery
from app.common import user, User
router = Router()

 

# Классы для FSM
class Registration(StatesGroup):
    waiting_for_name = State()
    waiting_for_birth_year = State()

class SecondTest(StatesGroup):
    fast_count_tester = State()
    remembered_words = State()
    stroop_test_time = State()



# Обработчик команды start
@router.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        await message.answer(f"Давайте знакомиться, как вас зовут?")    
        await state.set_state(Registration.waiting_for_name)
    else:
        await message.answer("Вы уже в процессе регистрации.")


@router.message(Registration.waiting_for_name)
async def get_name(message: Message, state: FSMContext) -> None:
    await state.update_data(waiting_for_name=message.text)
    await message.answer("Введите год своего рождения")
    await state.set_state(Registration.waiting_for_birth_year)


@router.message(Registration.waiting_for_birth_year)
async def get_birth_year(message: Message, state: FSMContext) -> None:
    global user
    try:
        birth_year = int(message.text)
        await state.update_data(waiting_for_birth_year=birth_year)
        user_data = await state.get_data()
        name = user_data.get('waiting_for_name')
        birth_year = user_data.get('waiting_for_birth_year')
        user_id = message.from_user.id
        user = User(name, birth_year, completed_tests_state=0)
        await message.answer(
            text=f"Отлично! Вы успешно зарегистрировались. Ваши данные: \n" \
            f"Имя: {user.name} \n" \
            f"Год рождения: {user.birth_date} \n" \
            f"Тестов выполнено: {user.completed_tests_state} \n" \
            "Теперь Вам доступно входное тестирование.\n" \
            "Перейдите по ссылкам ниже и пройдите тесты\n" \
            "После завершения нажмите кнопку 'Выполнено'",
            reply_markup=kb.entry_test  ## Здесь добавляем клавиатуру с тестами
        )
        await state.clear()

        # какая-то логика добавления в БД

    except ValueError:
        await message.answer("Введите год рождения в верном формате, например 1990.")
        return
    
@router.callback_query(F.data == "entry_test_complete_call")
async def entry_test_complete(query:CallbackQuery):
    await query.message.answer(
        text="Отлично! Вы завершили тестирование. Теперь вы можете перейти к следующему этапу.\n"
                "Выберите, что хотите сделать дальше:",
        reply_markup=kb.universal_kb  ## Здесь добавляем клавиатуру с выбором первого дня
    )

@router.callback_query(F.data == "test_complete_call")
async def test_complete (query:CallbackQuery):
    global user
    user.completed_tests_state += 1
    await query.message.answer(
<<<<<<< HEAD
        text=f"Вы завершили тест номер {user.completed_tests_state}! Выберите действие дальше: ",
        reply_markup=kb.universal_kb
        )
=======
        text=f"Вы завершили тест номер {user.completed_tests_state}! Выберите действие дальше: ") 
>>>>>>> 14beb867bc535194148f445ad9d18f07dd08bbe6


@router.callback_query(F.data == "first_day_test_call")
async def first_day_test(query: CallbackQuery):
    # Первое сообщение
    await query.message.answer(
        text="Сегодня 1 день твоей тренировки, тебе предстоит выполнить 3 упражнения.\n"
             "После выполнения задания, нажимай кнопку «Выполнено» и переходи к следующему."    
    )
    
    # Второе сообщение с упражнением, сюда осталось добавить 2 картинки, сделаем позже
    await query.message.answer(
        text="1. На одной руке покажи детский жест примирения (сожми пальцы в кулак, а мизинец выпрями и слегка отклони).\n"
             "2. На другой руке покажи одобряющий жест — «класс» (сожми кулак, а затем подними большой палец вверх).\n"
             "Выполняй это упражнение поочередно правой и левой рукой.",
        reply_markup=kb.complete  ## Пока добавляю везде комплиты, не хочу создавать много клавиатур, попробую подумать, как реализовать
    )

@router.callback_query(F.data == "theory_call")
async def theory_call(query: CallbackQuery):
    await query.message.answer(
        reply_markup=kb.theory
    ) 

## Обработка второго дня, сделал через FSM просто ради красивого вывода
@router.callback_query(F.data == "second_day_test_call")
async def second_day_test(query: CallbackQuery, state: FSMContext):
    second_day_state = await state.get_state()
    if second_day_state is None:
        await query.message.answer(
            text="Сегодня 2 день твоей тренировки, тебе предстоит выполнить 3 новых упражнения.\n"
        )
        await query.message.answer(
            text="1. Тест на счет. Засеки время и максимально быстро посчитай вслух от 1 до 120."
                 " Запиши свой результат (в секундах), например: 63"
        )
        await state.set_state(SecondTest.fast_count_tester)
    else:
        await query.message.answer(
            text="Вы уже в процессе прохождения испытания."
        )

@router.message(SecondTest.fast_count_tester)
async def get_fast_count_tester(message: Message, state: FSMContext):
    await state.update_data(fast_count_tester=message.text)
    await state.set_state(SecondTest.remembered_words)
    await message.answer(
        text="2. Тест на запоминание слов. В течение 2 минут постарайся запомнить как можно больше записанных ниже слов."
             " Напиши здесь, в чат, слова, которые запомнил. Сколько слов ты смог вспомнить за 2 минуты?",
    )

@router.message(SecondTest.remembered_words)
async def get_remembered_words(message: Message, state: FSMContext) -> None:
    try: 
        remembered_words_count = int(message.text)
        await state.update_data(remembered_words=remembered_words_count)
        await state.set_state(SecondTest.stroop_test_time)

        await message.answer(
            text="3. Тест Струпа. Называй вслух цвет слов, делая это как можно быстрее. Будь внимателен: ты должен не читать слова, а называть их цвет."
                 " Если ошибешься, назови цвет еще раз. Отметь время (в секундах), которое тебе понадобилось. Например, 34"
        )
    except ValueError:
        await message.answer(
            text="Введите значение цифрой, например: 24"  
        )
        return

@router.message(SecondTest.stroop_test_time)
async def get_stroop_test_time(message: Message, state: FSMContext) -> None:
    try:
        stroop_time = int(message.text)
        await state.update_data(stroop_test_time=stroop_time)

        contained_data = await state.get_data()
        await message.answer(
            text=f"Ваши результаты:\n"
                 f"1-й тест: {contained_data['fast_count_tester']} сек.\n"
                 f"2-й тест: {contained_data['remembered_words']} слов\n"
                 f"3-й тест: {contained_data['stroop_test_time']} сек."
        )
    except ValueError:
        await message.answer("Введенное сообщение должно быть числом!")
        return
