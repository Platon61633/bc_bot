import logging
from datetime import datetime

from aiogram import Dispatcher, Bot   # добавили Bot
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)

from db import db
from anons import repost_announcements_to_aiogram   # убрали импорт bot

# CHANEL = -1001922284221    #id БК

CHANEL = -1003865073475

def setup_registration_handlers(dp: Dispatcher, bot: Bot):   # добавили параметр bot
    logging.basicConfig(level=logging.INFO)

    class Registration(StatesGroup):
        name = State()
        b_day = State()
        faculty = State()

    def get_register_kb() -> ReplyKeyboardMarkup:
        kb = [[KeyboardButton(text="Зарегистрироваться")]]
        return ReplyKeyboardMarkup(
            keyboard=kb,
            resize_keyboard=True,
            one_time_keyboard=True,
        )

    def get_main_menu_kb() -> ReplyKeyboardMarkup:
        kb = [
            [
                KeyboardButton(text="Зарегистрироваться на мероприятие"),
                KeyboardButton(text="Смотреть котят"),
            ]
        ]
        return ReplyKeyboardMarkup( 
            keyboard=kb,
            resize_keyboard=True,
            one_time_keyboard=False,
        )

    @dp.message(lambda message: message.text == "Зарегистрироваться на мероприятие")
    async def register_button(message: Message, state: FSMContext):
        await message.answer("Ищу анонсы и публикую...")
        try:
            # используем переданный bot
            await repost_announcements_to_aiogram(
                bot=bot,
                chat_id=message.chat.id,
                channel_id=CHANEL,
                hashtag='#анонс',
                limit=3,
                max_scan=200
            )
            await message.answer("Это все актуальные мероприятия.")
        except Exception as e:
            await message.answer(f"Ошибка: {e}")

    @dp.message(CommandStart())
    async def cmd_start(message: Message, state: FSMContext):
        user_id = message.from_user.id
        user = await db.get_user(user_id) 
        if user:
            await message.answer(
                f"С возвращением, {user['name']}! Вы уже зарегистрированы.",
                reply_markup=get_main_menu_kb(),
            )
            return
        await message.answer(
            "Добро пожаловать! Для регистрации нажмите кнопку ниже.",
            reply_markup=get_register_kb(),
        )

    @dp.message(lambda message: message.text == "Зарегистрироваться")
    async def register_button_start(message: Message, state: FSMContext):
        # ... без изменений
        user_id = message.from_user.id
        user = await db.get_user(user_id)
        if user:
            await message.answer(
                "Вы уже зарегистрированы.",
                reply_markup=get_main_menu_kb(),
            )
            return
        await state.set_state(Registration.name)
        await message.answer(
            "Введите ваше имя:",
            reply_markup=ReplyKeyboardRemove(),
        )

    @dp.message(Command("cancel"))
    async def cmd_cancel(message: Message, state: FSMContext):
        # ... без изменений
        current_state = await state.get_state()
        if current_state is None:
            await message.answer(
                "Нет активной регистрации.",
                reply_markup=ReplyKeyboardRemove(),
            )
            return
        await state.clear()
        await message.answer(
            "Регистрация отменена.",
            reply_markup=ReplyKeyboardRemove(),
        )

    @dp.message(Registration.name)
    async def process_name(message: Message, state: FSMContext):
        # ... без изменений
        await state.update_data(name=message.text)
        await state.set_state(Registration.b_day)
        await message.answer(
            "Теперь введите вашу дату рождения в формате ДД.ММ.ГГГГ (например, 02.03.2004):"
        )

    @dp.message(Registration.b_day)
    async def process_b_day(message: Message, state: FSMContext):
        # ... без изменений
        try:
            b_day_obj = datetime.strptime(message.text, "%d.%m.%Y").date()
        except ValueError:
            await message.answer(
                "Неверный формат даты. Пожалуйста, используйте ДД.ММ.ГГГГ (например, 02.03.2004)."
            )
            return
        await state.update_data(b_day=b_day_obj)
        await state.set_state(Registration.faculty)
        await message.answer("Введите ваш факультет:")

    @dp.message(Registration.faculty)
    async def process_faculty(message: Message, state: FSMContext):
        # ... без изменений
        data = await state.get_data()
        name = data["name"]
        b_day = data["b_day"]
        faculty = message.text

        user_id = message.from_user.id
        tg_username = message.from_user.username or ""

        try:
            await db.add_user(user_id, tg_username, name, b_day, faculty)
            await message.answer(
                "Регистрация завершена!\n"
                f"Имя: {name}\n"
                f"День рождения: {b_day.strftime('%d.%m.%Y')}\n"
                f"Факультет: {faculty}\n"
                "Статус: активен (блокировка 0)",
                reply_markup=get_main_menu_kb(),
            )
        except Exception as e:
            logging.error(f"Ошибка при сохранении в БД: {e}")
            await message.answer(
                "Произошла ошибка при регистрации. Попробуйте позже."
            )
        finally:
            await state.clear()