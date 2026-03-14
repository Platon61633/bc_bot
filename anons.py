from telethon import TelegramClient

# ==== НАСТРОЙКИ ====
# Конфигурация (замените на свои данные)
API_ID = 36050023  # Ваш API ID (int)
API_HASH = '0d37f945af68c74bce27e39b10a07d9c'

SESSION_FILE = 'user_session'  # Имя файла сессии пользователя (не бота)
# ===================

def get_last_announcements(channel_id, hashtag, limit=3, max_scan=100):
    """
    Получает последние limit соо��щений из канала, содержащих hashtag,
    просматривая не более max_scan последних сообщений.
    
    :param channel_id: username канала (например '@bcmsu') или числовой ID
    :param hashtag: строка с хештегом (например '#анонс@bcmsu')
    :param limit: сколько сообщений с хештегом вернуть
    :param max_scan: сколько последних сообщений просмотреть
    :return: список объектов Message (из telethon)
    """
    client = TelegramClient(SESSION_FILE, API_ID, API_HASH)
    # Авторизация как пользователь (при первом запуске запросит номер и код)
    await client.start()

    # Если передан положительный числовой ID канала, преобразуем в формат MTProto (-100...)
    if isinstance(channel_id, int) and channel_id > 0:
        channel_id = int(f"-100{channel_id}")

    # Получаем сущность канала (проверка доступа)
    try:
        entity = await client.get_entity(channel_id)
    except Exception as e:
        await client.disconnect()
        raise ValueError(f"Не удалось найти канал {channel_id}. "
                         f"Убедитесь, что пользователь подписан на канал. Ошибка: {e}")

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

# Удобная обёртка, возвращающая только тексты сообщений
async def get_last_announcements_texts(channel_id, hashtag, limit=3, max_scan=100):
    msgs = await get_last_announcements(channel_id, hashtag, limit, max_scan)
    return [msg.text for msg in msgs if msg.text]

# Обёртка, возвращающая сообщения с ID и текстом
async def get_last_announcements_with_ids(channel_id, hashtag, limit=3, max_scan=100):
    """Возвращает список словарей с ID и текстом сообщений"""
    msgs = await get_last_announcements(channel_id, hashtag, limit, max_scan)
    return [{"id": msg.id, "text": msg.text} for msg in msgs if msg.text]