import aiosqlite
from datetime import datetime, timedelta


DB_NAME = "users.db"


async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:

        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            expire_date TEXT
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER,
            payment_id TEXT UNIQUE,
            amount INTEGER,
            created_at TEXT
        )
        """)

        await db.commit()



async def get_user(user_id):

    async with aiosqlite.connect(DB_NAME) as db:

        cursor = await db.execute(
            "SELECT expire_date FROM users WHERE telegram_id=?",
            (user_id,)
        )

        result = await cursor.fetchone()

        if result:
            return datetime.fromisoformat(result[0])

        return None



async def add_subscription(user_id):

    now = datetime.now()

    old_date = await get_user(user_id)


    if old_date and old_date > now:
        new_date = old_date + timedelta(days=30)
    else:
        new_date = now + timedelta(days=30)



    async with aiosqlite.connect(DB_NAME) as db:

        await db.execute(
            """
            INSERT INTO users(telegram_id, expire_date)
            VALUES(?,?)

            ON CONFLICT(telegram_id)
            DO UPDATE SET expire_date=excluded.expire_date
            """,

            (
                user_id,
                new_date.isoformat()
            )
        )

        await db.commit()


    return new_date



async def delete_user(user_id):

    async with aiosqlite.connect(DB_NAME) as db:

        await db.execute(
            "DELETE FROM users WHERE telegram_id=?",
            (user_id,)
        )

        await db.commit()



async def get_all_users():

    async with aiosqlite.connect(DB_NAME) as db:

        cursor = await db.execute(
            "SELECT telegram_id, expire_date FROM users"
        )

        return await cursor.fetchall()