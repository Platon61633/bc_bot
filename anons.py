import os
import tempfile
import asyncio
import re
from functools import partial
from datetime import date

from telethon import TelegramClient

from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.filters import Command
from aiogram.enums import ParseMode

from db import db


# ==== НАСТРОЙКИ ====
# Telethon (как пользователь)
API_ID = 36050023  # Ваш API ID (int)
API_HASH = '0d37f945af68c74bce27e39b10a07d9c'
SESSION_FILE = 'user_session'  # Имя файла сессии пользователя (Telethon)


month_map = {
    'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4, 'мая': 5, 'июня': 6,
    'июля': 7, 'августа': 8, 'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
}

def parse_event_date(text: str):
    
    """Извлекает дату из строки вида '📅 Дата: 19 марта (четверг), 18:00'"""
    match = re.search(r'📅 Дата:\s*(\d{1,2})\s+([а-я]+)', text, re.IGNORECASE)
    if not match:
        match = re.search(r'📅 \s*(\d{1,2})\s+([а-я]+)', text, re.IGNORECASE)
    day = int(match.group(1))
    month_name = match.group(2).lower()
    month = month_map.get(month_name)
    if not month:
        return None

    today = date.today()
    year = today.year
    try:
        event_date = date(year, month, day)
    except ValueError:
        return None

    # Если дата уже прошла в этом году, проверяем следующий год
    if event_date < today:
        try:
            event_date = date(year, month, day)
        except ValueError:
            return None
    return event_date

def truncate_text(text: str, max_length: int = 1024) -> str:
    # Ищем маркер "📅 Дата"
    marker = "📅"
    idx = text.find(marker)
    if idx != -1:
        # Берём текст, начиная с маркера (включая его)
        text = text[idx:]
    # Если текст всё ещё длиннее лимита — обрезаем
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

async def get_last_announcements(channel_id, hashtag, limit=3, max_scan=100):
    client = TelegramClient(SESSION_FILE, API_ID, API_HASH)
    await client.start()

    if isinstance(channel_id, int) and channel_id > 0:
        channel_id = int(f"-100{channel_id}")

    try:
        entity = await client.get_entity(channel_id)
    except Exception as e:
        await client.disconnect()
        raise ValueError(f"Не удалось найти канал {channel_id}. Ошибка: {e}")

    messages = []
    try:
        async for msg in client.iter_messages(entity, limit=max_scan):
            if msg.text and hashtag in msg.text:
                messages.append(msg)
                if len(messages) >= limit:
                    break
    finally:
        await client.disconnect()

    return messages

async def repost_announcements_to_aiogram(bot: Bot, chat_id: int, channel_id, hashtag: str, limit=3, max_scan=100):
    client = TelegramClient(SESSION_FILE, API_ID, API_HASH)
    await client.start()

    if isinstance(channel_id, int) and channel_id > 0:
        channel_id = int(f"-100{channel_id}")

    try:
        entity = await client.get_entity(channel_id)
    except Exception as e:
        await client.disconnect()
        raise ValueError(f"Не удалось найти канал {channel_id}. Ошибка: {e}")

    found = 0
    try:
        async for msg in client.iter_messages(entity, limit=max_scan):
            if not (msg.text and hashtag in msg.text):
                continue
            
            # закомментированно для тестирования
            event_date = parse_event_date(msg.text)
            if event_date and event_date < date.today():
                print(f"Пропускаем прошедшее мероприятие от {event_date}")
                break   # если встречаем мероприятие, которое уже прошло, то больше не ищем!!!!!!!
            
            # Формируем ссылку на оригинальный пост
            if isinstance(channel_id, str) and channel_id.startswith('@'):
                link = f"https://t.me/{channel_id[1:]}/{msg.id}"
            else:
                chat_id_for_link = str(msg.chat_id)
                if chat_id_for_link.startswith('-100'):
                    chat_id_for_link = chat_id_for_link[4:]
                link = f"https://t.me/c/{chat_id_for_link}/{msg.id}"
            
            event_date_str = event_date.isoformat() if event_date else 'unknown'
            callback_data = f"click:{event_date_str}"
            # Создаём клавиатуру с двумя кнопками
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="Зарегистрироваться", callback_data=callback_data),
                    InlineKeyboardButton(text="🔗 Оригинал", url=link)
                ]
            ])

            if msg.media:
                tmp = tempfile.NamedTemporaryFile(delete=False)
                tmp_path = tmp.name
                tmp.close()
                try:
                    await client.download_media(msg, file=tmp_path)
                    
                    try:
                        caption = truncate_text(msg.text or "", 1024)
                        await bot.send_photo(chat_id, FSInputFile(tmp_path), caption=caption, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
                    except Exception:
                        caption = truncate_text(msg.text or "", 4096)
                        await bot.send_document(chat_id, FSInputFile(tmp_path), caption=caption or "", reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
                finally:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
            else:
                await bot.send_message(chat_id, msg.text or " ", reply_markup=kb, parse_mode=ParseMode.MARKDOWN)

            found += 1
            if found >= limit:
                break
    finally:
        await client.disconnect()

# Обработчики aiogram
async def cmd_anons(message: types.Message, bot: Bot):   # добавляем bot в параметры
    await message.answer("Ищу анонсы и публикую...")
    try:
        await repost_announcements_to_aiogram(
            bot=bot,   # передаём локальный bot
            chat_id=message.chat.id,
            channel_id='@bcmsu',
            hashtag='#анонс',
            limit=3,
            max_scan=200
        )
        await message.answer("Готово.")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

async def process_click(callback_query: types.CallbackQuery, bot: Bot):
    # callback_data = "click:YYYY-MM-DD" или "click:unknown"
    parts = callback_query.data.split(':')
    if len(parts) != 2:
        await bot.answer_callback_query(callback_query.id, text="Ошибка данных")
        return

    _, event_date_str = parts
    
    if event_date_str == 'unknown':
        await bot.answer_callback_query(callback_query.id, text="Дата мероприятия не определена")
        return

    try:
        event_date = date.fromisoformat(event_date_str)
    except ValueError:
        await bot.answer_callback_query(callback_query.id, text="Некорректная дата")
        return

    user_id = callback_query.from_user.id

    # Добавляем пользователя на мероприятие (только если оно есть в БД)
    result = await db.add_user_to_event(event_date, user_id)

    if result == 'added':
        await bot.answer_callback_query(callback_query.id, text="✅ Вы записаны на мероприятие!")
    elif result == 'already':
        await bot.answer_callback_query(callback_query.id, text="⚠️ Вы уже были записаны")
    elif result == 'not_found':
        await bot.answer_callback_query(callback_query.id, text="❌ Мероприятие не найдено в базе (возможно, ещё не добавлено админом)")
    else:
        await bot.answer_callback_query(callback_query.id, text="❌ Сначала зарегистрируйтесь в боте через /start")

    # Здесь можно добавить дополнительную логику, например, логирование

    
def setup_anons_handlers(dp, bot):
    dp.message.register(partial(cmd_anons, bot=bot), Command(commands=['anons']))
    dp.callback_query.register(partial(process_click, bot=bot), lambda c: c.data and c.data.startswith('click:'))