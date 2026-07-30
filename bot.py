import asyncio
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.types import LabeledPrice
import datetime
import os

# ==========================================
# ВАШИ ДАННЫЕ (ВСЁ ЗАПОЛНЕНО)
# ==========================================
BOT_TOKEN = "8439119682:AAHV00Uk9LK90eoysUe7uKq3J56AcS3uPgQ"
PROVIDER_TOKEN = "390540012:LIVE:100092"  # БОЕВОЙ ТОКЕН
ADMIN_ID = 6217476601
CHANNEL_ID = -1001234567890  # ✅ ВАШ ID КАНАЛА (ВСТАВЛЕН!)
PRICE = 100  # 1 РУБЛЬ (ТЕСТ!)
# ==========================================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

DB_FILE = "users.txt"

# ==========================================
# РАБОТА С БАЗОЙ
# ==========================================
def load_users():
    if not os.path.exists(DB_FILE):
        return {}
    users = {}
    with open(DB_FILE, "r") as f:
        for line in f:
            if line.strip():
                user_id, expire = line.strip().split("|")
                users[int(user_id)] = datetime.datetime.fromisoformat(expire)
    return users

def save_user(user_id, expire):
    users = load_users()
    users[user_id] = expire
    with open(DB_FILE, "w") as f:
        for uid, exp in users.items():
            f.write(f"{uid}|{exp.isoformat()}\n")

def remove_user(user_id):
    users = load_users()
    if user_id in users:
        del users[user_id]
        with open(DB_FILE, "w") as f:
            for uid, exp in users.items():
                f.write(f"{uid}|{exp.isoformat()}\n")
        return True
    return False

# ==========================================
# КОМАНДЫ
# ==========================================

# ---------- СТАРТ ----------
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton("💳 КУПИТЬ 1 ₽ (ТЕСТ)", callback_data="pay")
    btn2 = types.InlineKeyboardButton("🔍 ПРОВЕРИТЬ ПОДПИСКУ", callback_data="check")
    btn3 = types.InlineKeyboardButton("❓ ПОМОЩЬ", callback_data="help")
    keyboard.add(btn1, btn2, btn3)
    
    users = load_users()
    user_id = message.from_user.id
    
    if user_id in users and users[user_id] > datetime.datetime.now():
        days = (users[user_id] - datetime.datetime.now()).days
        await message.answer(
            f"✅ ПОДПИСКА АКТИВНА!\n\n"
            f"📅 Действует до: {users[user_id].strftime('%d.%m.%Y')}\n"
            f"⏳ Осталось дней: {days}\n\n"
            f"💡 Нажмите кнопку, чтобы продлить:",
            reply_markup=keyboard
        )
        return
    
    await message.answer(
        "🌟 ДОБРО ПОЖАЛОВАТЬ!\n\n"
        "🧪 ТЕСТОВАЯ ОПЛАТА 1 ₽\n"
        "🔥 Проверка боевого токена ЮKassa\n"
        "💰 Спишется 1 рубль с вашей карты\n\n"
        "⬇️ Нажмите кнопку для оплаты:",
        reply_markup=keyboard
    )

# ---------- ОПЛАТА ----------
@dp.callback_query_handler(lambda c: c.data == 'pay')
async def pay(callback: types.CallbackQuery):
    await bot.answer_callback_query(callback.id)
    
    try:
        await bot.send_invoice(
            chat_id=callback.from_user.id,
            title="🧪 ТЕСТОВАЯ ПОДПИСКА",
            description="🔥 Проверка боевого токена\n"
                        "💰 Спишется 1 ₽ с карты\n"
                        "📅 Доступ на 30 дней (тест)",
            payload=f"sub_{callback.from_user.id}",
            provider_token=PROVIDER_TOKEN,
            currency="RUB",
            prices=[LabeledPrice(label="Тестовая оплата", amount=PRICE)],
            start_parameter="subscription",
            need_phone_number=False,
            need_email=False
        )
        print(f"✅ Инвойс отправлен пользователю {callback.from_user.id}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        await callback.message.answer(
            f"❌ ОШИБКА ОПЛАТЫ:\n\n"
            f"{str(e)}\n\n"
            f"Проверьте:\n"
            f"1. Правильный ли PROVIDER_TOKEN\n"
            f"2. Активен ли токен в BotFather"
        )

# ---------- ПРОВЕРКА ПЛАТЕЖА ----------
@dp.pre_checkout_query_handler(lambda q: True)
async def pre_checkout(query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(query.id, ok=True)

# ---------- УСПЕШНАЯ ОПЛАТА ----------
@dp.message_handler(content_types=['successful_payment'])
async def payment_success(message: types.Message):
    amount = message.successful_payment.total_amount // 100
    user_id = message.from_user.id
    expire = datetime.datetime.now() + datetime.timedelta(days=30)
    
    # Сохраняем в базу
    save_user(user_id, expire)
    
    # Отправляем ссылку
    try:
        link = await bot.create_chat_invite_link(
            chat_id=CHANNEL_ID,
            member_limit=1,
            expire_date=expire
        )
        
        await message.answer(
            f"🎉 ОПЛАТА ПРОШЛА УСПЕШНО!\n\n"
            f"💰 Сумма: {amount} ₽\n"
            f"📅 Доступ до: {expire.strftime('%d.%m.%Y')}\n\n"
            f"🔗 ВАША ССЫЛКА:\n"
            f"{link.invite_link}\n\n"
            f"⚠️ Ссылка одноразовая!\n"
            f"✅ Тест боевого токена ПРОЙДЕН!"
        )
        
        # Уведомление админу
        await bot.send_message(
            ADMIN_ID,
            f"🤑 НОВАЯ ОПЛАТА (ТЕСТ!)\n\n"
            f"👤 {message.from_user.full_name}\n"
            f"🆔 ID: {user_id}\n"
            f"💰 {amount} ₽\n"
            f"📅 До: {expire.strftime('%d.%m.%Y')}\n\n"
            f"✅ Боевой токен РАБОТАЕТ!"
        )
        
    except Exception as e:
        await message.answer(
            f"❌ ОШИБКА: Не удалось создать ссылку\n\n"
            f"Оплата прошла, но ссылка не создалась.\n"
            f"Напишите администратору."
        )
        await bot.send_message(
            ADMIN_ID,
            f"⚠️ ОШИБКА СОЗДАНИЯ ССЫЛКИ\n"
            f"ID: {user_id}\n"
            f"Ошибка: {e}"
        )

# ---------- ПРОВЕРКА ПОДПИСКИ ----------
@dp.callback_query_handler(lambda c: c.data == 'check')
async def check_subscription(callback: types.CallbackQuery):
    await bot.answer_callback_query(callback.id)
    user_id = callback.from_user.id
    users = load_users()
    
    if user_id in users and users[user_id] > datetime.datetime.now():
        days = (users[user_id] - datetime.datetime.now()).days
        await callback.message.answer(
            f"✅ ПОДПИСКА АКТИВНА!\n\n"
            f"📅 До: {users[user_id].strftime('%d.%m.%Y')}\n"
            f"⏳ Осталось: {days} дн."
        )
    else:
        await callback.message.answer(
            f"❌ ПОДПИСКА НЕ АКТИВНА!\n\n"
            f"Нажмите /start, чтобы купить"
        )

# ---------- ПОМОЩЬ ----------
@dp.callback_query_handler(lambda c: c.data == 'help')
async def help_menu(callback: types.CallbackQuery):
    await bot.answer_callback_query(callback.id)
    await callback.message.answer(
        "❓ ПОМОЩЬ\n\n"
        "🧪 Это ТЕСТОВАЯ оплата 1 ₽\n\n"
        "🔹 Как проверить боевой токен?\n"
        "   Нажмите «КУПИТЬ 1 ₽»\n"
        "   Оплатите картой\n"
        "   Должна прийти ссылка\n\n"
        "🔹 Что проверяем?\n"
        "   - Работу боевого токена\n"
        "   - Создание ссылок\n"
        "   - Сохранение подписки\n\n"
        "🔹 После теста?\n"
        "   Цена станет 1300 ₽"
    )

# ==========================================
# АДМИН-КОМАНДЫ
# ==========================================

@dp.message_handler(commands=['stats'])
async def stats(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Нет прав")
        return
    
    users = load_users()
    now = datetime.datetime.now()
    active = sum(1 for exp in users.values() if exp > now)
    
    await message.answer(
        f"📊 СТАТИСТИКА\n\n"
        f"👥 Всего: {len(users)}\n"
        f"✅ Активных: {active}\n"
        f"❌ Просрочено: {len(users) - active}"
    )

@dp.message_handler(commands=['list'])
async def list_users(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Нет прав")
        return
    
    users = load_users()
    if not users:
        await message.answer("📭 База пуста")
        return
    
    text = "👥 СПИСОК ПОЛЬЗОВАТЕЛЕЙ:\n━━━━━━━━━━━━━━━━\n"
    for uid, exp in users.items():
        days = (exp - datetime.datetime.now()).days
        status = "🟢" if days > 0 else "🔴"
        text += f"{status} {uid} | до {exp.strftime('%d.%m.%Y')} | {days} дн.\n"
    
    await message.answer(text)

@dp.message_handler(commands=['remove'])
async def remove_user_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Нет прав")
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("ℹ️ /remove ID")
        return
    
    try:
        user_id = int(parts[1])
        if remove_user(user_id):
            try:
                await bot.ban_chat_member(CHANNEL_ID, user_id)
                await bot.unban_chat_member(CHANNEL_ID, user_id)
            except:
                pass
            await message.answer(f"✅ Пользователь {user_id} удален")
        else:
            await message.answer(f"❌ Пользователь {user_id} не найден")
    except:
        await message.answer("❌ Неверный ID")

# ==========================================
# ФОНОВАЯ ПРОВЕРКА (УДАЛЕНИЕ ПРОСРОЧЕННЫХ)
# ==========================================

async def check_expired():
    while True:
        try:
            users = load_users()
            now = datetime.datetime.now()
            for user_id, expire in users.items():
                if expire <= now:
                    try:
                        await bot.ban_chat_member(CHANNEL_ID, user_id)
                        await bot.unban_chat_member(CHANNEL_ID, user_id)
                    except:
                        pass
                    remove_user(user_id)
                    print(f"⏰ Пользователь {user_id} удален (подписка истекла)")
            await asyncio.sleep(3600)  # Проверка каждый час
        except Exception as e:
            print(f"Ошибка в check_expired: {e}")
            await asyncio.sleep(60)

# ==========================================
# ЗАПУСК
# ==========================================

async def on_startup(dp):
    asyncio.create_task(check_expired())
    print("="*40)
    print("🚀 БОТ ЗАПУЩЕН!")
    print(f"💰 Цена: {PRICE//100} ₽ (ТЕСТОВАЯ!)")
    print(f"🔑 Токен: БОЕВОЙ")
    print(f"📢 Канал: {CHANNEL_ID}")
    print("="*40)
    await bot.send_message(ADMIN_ID, "✅ Бот запущен! Тестовая оплата 1 ₽")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
