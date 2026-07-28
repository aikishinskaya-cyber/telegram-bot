import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import F
import json
import datetime
import os

# ===================================================
# ВАШИ ДАННЫЕ — ПРОВЕРЬТЕ ВСЁ!
# ===================================================
BOT_TOKEN = "8439119682:AAHV00Uk9LK90eoysUe7uKq3J56AcS3uPgQ"
PROVIDER_TOKEN = "390540012:LIVE:100092"
YOUR_TELEGRAM_ID = 6217476601
CHANNEL_ID = -6217476601
# ===================================================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
DB_FILE = "users_db.txt"

# ---------- РАБОТА С БАЗОЙ ----------
def load_users():
    if not os.path.exists(DB_FILE):
        return {}
    users = {}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                user_id, expire_date = line.strip().split("|")
                users[int(user_id)] = datetime.datetime.fromisoformat(expire_date)
    return users

def save_user(user_id, expire_date):
    users = load_users()
    users[user_id] = expire_date
    with open(DB_FILE, "w", encoding="utf-8") as f:
        for uid, exp_date in users.items():
            f.write(f"{uid}|{exp_date.isoformat()}\n")

def remove_user(user_id):
    users = load_users()
    if user_id in users:
        del users[user_id]
        with open(DB_FILE, "w", encoding="utf-8") as f:
            for uid, exp_date in users.items():
                f.write(f"{uid}|{exp_date.isoformat()}\n")
        return True
    return False

def get_expire_date():
    return datetime.datetime.now() + datetime.timedelta(days=30)

# ---------- КОМАНДА /start ----------
@dp.message(Command("start"))
async def start(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🖤 Купить доступ на месяц", callback_data="pay")]
    ])

    users = load_users()
    user_id = message.from_user.id

    if user_id in users and users[user_id] > datetime.datetime.now():
        days_left = (users[user_id] - datetime.datetime.now()).days
        await message.answer(
            f"✅ У вас уже есть доступ!\nОсталось дней: {days_left}",
            reply_markup=keyboard
        )
        return

    await message.answer(
        "🖤 Добро пожаловать!\nНажмите кнопку ниже, чтобы получить доступ к каналу на 30 дней.",
        reply_markup=keyboard
    )

# ---------- ОБРАБОТКА ОПЛАТЫ ----------
@dp.callback_query(F.data == "pay")
async def process_pay(callback_query: types.CallbackQuery):
    await callback_query.answer()

    provider_data = {
        "receipt": {
            "items": [{
                "description": "Доступ на 30 дней",
                "quantity": "1.00",
                "amount": {"value": "1300.00", "currency": "RUB"},
                "vat_code": 1
            }]
        }
    }

    await bot.send_invoice(
        chat_id=callback_query.from_user.id,
        title="Подписка на месяц",
        description="Доступ к закрытому каналу на 30 дней",
        payload="subscription_" + str(callback_query.from_user.id),
        provider_token=PROVIDER_TOKEN,
        currency="RUB",
        prices=[LabeledPrice(label="Подписка", amount=130000)],
        provider_data=json.dumps(provider_data),
        need_phone_number=False,
        send_phone_number_to_provider=False
    )

@dp.pre_checkout_query()
async def pre_checkout(pre_checkout_query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message(F.successful_payment)
async def successful_payment(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    amount = message.successful_payment.total_amount // 100

    try:
        invite_link = await bot.create_chat_invite_link(
            chat_id=CHANNEL_ID,
            member_limit=1,
            expire_date=None,
            creates_join_request=False
        )
        invite_url = invite_link.invite_link
    except Exception as e:
        await bot.send_message(YOUR_TELEGRAM_ID, f"Ошибка ссылки: {e}")
        await message.answer("❌ Ошибка. Напишите админу.")
        return

    expire_date = get_expire_date()
    save_user(user_id, expire_date)

    await message.answer(
        f"🖤 ОПЛАТА ПРОШЛА УСПЕШНО!\n"
        f"Сумма: {amount} руб.\n\n"
        f"🔗 ВАША ССЫЛКА:\n{invite_url}\n\n"
        f"📅 Доступ до: {expire_date.strftime('%d.%m.%Y')}"
    )

    await bot.send_message(
        YOUR_TELEGRAM_ID,
        f"🖤 ОПЛАТА ПОЛУЧЕНА!\n"
        f"От: {user_name}\n"
        f"ID: {user_id}\n"
        f"Сумма: {amount} руб."
    )

# ---------- ФОНОВАЯ ПРОВЕРКА ----------
async def check_expired_users():
    while True:
        try:
            users = load_users()
            now = datetime.datetime.now()
            for user_id, expire_date in users.items():
                if expire_date <= now:
                    try:
                        await bot.ban_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
                        await bot.unban_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
                        remove_user(user_id)
                        await bot.send_message(YOUR_TELEGRAM_ID, f"⏰ Исключен: {user_id}")
                    except Exception as e:
                        await bot.send_message(YOUR_TELEGRAM_ID, f"Ошибка исключения: {e}")
        except Exception as e:
            await bot.send_message(YOUR_TELEGRAM_ID, f"Ошибка фоновой задачи: {e}")
        await asyncio.sleep(3600)

# ---------- АДМИН-КОМАНДЫ ----------
@dp.message(Command("stats"))
async def stats_command(message: types.Message):
    if message.from_user.id != YOUR_TELEGRAM_ID:
        await message.answer("❌ Нет прав.")
        return
    users = load_users()
    await message.answer(f"📊 Всего подписчиков: {len(users)}")

# ---------- ЗАПУСК ----------
async def on_startup():
    asyncio.create_task(check_expired_users())

async def main():
    await on_startup()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
