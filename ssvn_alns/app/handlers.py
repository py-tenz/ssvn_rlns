from aiogram import Router, F, html
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from . import keyboards as kb

router = Router()

# Класс для FSM
class Registration(StatesGroup):
    waiting_for_name = State()
    waiting_for_birth_year = State()


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
    name = message.text
    await state.update_data(name=name)
    await message.answer("Введите год своего рождения")
    await state.set_state(Registration.waiting_for_birth_year)


@router.message(Registration.waiting_for_birth_year)
async def get_birth_year(message: Message, state: FSMContext) -> None:
    try:
        birth_year = int(message.text)
        user_data = await state.get_data()
        name = user_data.get('name')
        user_id = message.from_user.id
        
        # какая-то логика добавления в БД

    except ValueError:
        await message.answer("Введите год рождения в верном формате, например 1990.")
        return

@router.callback_query(F.data == "first_day_test_call")
async def first_day_test(query: F.CallbackQuery):
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
        reply_markup=kb.complete
    )