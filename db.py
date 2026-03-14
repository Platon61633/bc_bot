import asyncpg
from config import DB_CONFIG
from datetime import date

class Database:
    def __init__(self):
        self.pool = None

    async def create_pool(self):
        self.pool = await asyncpg.create_pool(**DB_CONFIG)

    async def init_db(self):
        async with self.pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    tg_username TEXT,
                    name TEXT NOT NULL,
                    b_day DATE,
                    faculty TEXT,
                    block INTEGER NOT NULL DEFAULT 0,
                    ivents TEXT
                )
            ''')
            # Таблица мероприятий (дата как ключ, список пользователей через пробел)
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    date DATE PRIMARY KEY,
                    users TEXT,
                    title TEXT
                )
            ''')

    async def add_user(self, user_id: int, tg_username: str, name: str, b_day, faculty: str):
        """b_day должен быть объектом datetime.date"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO users (user_id, tg_username, name, b_day, faculty, block, role)
                VALUES ($1, $2, $3, $4, $5, 0, 'user')
            ''', user_id, tg_username, name, b_day, faculty)

    async def get_user(self, user_id: int):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow('SELECT * FROM users WHERE user_id = $1', user_id)
        
        
    async def cleanup_old_events(self):
        """Удаляет записи о прошедших мероприятиях (date < сегодня)."""
        async with self.pool.acquire() as conn:
            await conn.execute('DELETE FROM events WHERE date < $1', date.today())

    async def add_user_to_event(self, date: date, user_id: int) -> str:
        """
        Добавляет пользователя в список участников мероприятия.
        Возвращает:
          - 'added'   – пользователь успешно добавлен
          - 'already' – пользователь уже был записан
          - 'error'   – ошибка (например, пользователь не найден)
        """
        # Сначала удаляем прошедшие мероприятия
        await self.cleanup_old_events()

        # Проверяем, существует ли пользователь в таблице users (опционально)
        user = await self.get_user(user_id)
        if not user:
            return 'error'

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('SELECT users FROM events WHERE date = $1', date)
            if row:
                users_str = row['users']
                user_list = users_str.split() if users_str else []
                if str(user_id) in user_list:
                    return 'already'
                user_list.append(str(user_id))
                new_users_str = ' '.join(user_list)
                await conn.execute('UPDATE events SET users = $1 WHERE date = $2', new_users_str, date)
                return 'added'
            else:
                # Создаём новую запись
                await conn.execute('INSERT INTO events (date, users) VALUES ($1, $2)', date, str(user_id))
                return 'added'

    async def get_event_users(self, date: date) -> list:
        """Возвращает список user_id для данного мероприятия."""
        await self.cleanup_old_events()
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('SELECT users FROM events WHERE date = $1', date)
            if not row:
                return []
            return [int(uid) for uid in row['users'].split() if uid]

    async def get_user_events(self, user_id: int) -> list:
        """Возвращает список дат мероприятий, на которые записан пользователь."""
        await self.cleanup_old_events()
        async with self.pool.acquire() as conn:
            # Получаем все события (их немного)
            rows = await conn.fetch('SELECT date, users FROM events')
            result = []
            for row in rows:
                if str(user_id) in row['users'].split():
                    result.append(row['date'])
            return result
            
db = Database()