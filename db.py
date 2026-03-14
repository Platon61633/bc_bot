import asyncpg
from config import DB_CONFIG

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
                    block INTEGER NOT NULL DEFAULT 0
                )
            ''')

    async def add_user(self, user_id: int, tg_username: str, name: str, b_day, faculty: str):
        """b_day должен быть объектом datetime.date"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO users (user_id, tg_username, name, b_day, faculty, block)
                VALUES ($1, $2, $3, $4, $5, 0)
            ''', user_id, tg_username, name, b_day, faculty)

    async def get_user(self, user_id: int):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow('SELECT * FROM users WHERE user_id = $1', user_id)

db = Database()