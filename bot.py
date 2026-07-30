import asyncio
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.types import LabeledPrice
import datetime

# ===================================================
# ТОЛЬКО ЭТИ ДАННЫЕ ЗАПОЛНИТЕ
# ===================================================
BOT_TOKEN = "8439119682:AAHV00Uk9LK90eoysUe7uKq3J56AcS3uPgQ"
PROVIDER_TOKEN = "390540012:LIVE:100092"  # БОЕВОЙ ТОКЕН
YOUR_TELEGRAM_ID = 6217476601
# ===================================================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# ПРОСТАЯ КНОПКА
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    keyboard = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("💳 ТЕСТ ОПЛАТЫ 100 ₽", callback_data="pay")
    keyboard.add(btn)
    
    await message.answer(
        "🧪 ТЕСТОВЫЙ ПЛАТЕЖ\n\n"
        "Нажмите кнопку для теста оплаты\n"
        "Сумма: 100 ₽",
        reply_markup=keyboard
    )

# ОБРАБОТКА КНОПКИ
@dp.callback_query_handler(lambda c: c.data == 'pay')
async def process_pay(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    
    try:
        await bot.send_invoice(
            chat_id=callback_query.from_user.id,
            title="ТЕСТОВЫЙ ПЛАТЕЖ",
            description="Тестовая оплата 100 ₽",
            payload="test_" + str(callback_query.from_user.id),
            provider_token=PROVIDER_TOKEN,
            currency="RUB",
            prices=[LabeledPrice(label="Тест", amount=10000)],  # 100 ₽
            start_parameter="test",
            need_phone_number=False,
            need_email=False
        )
        print(f"✅ Инвойс отправлен {callback_query.from_user.id}")
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        await callback_query.message.answer(f"❌ Ошибка: {e}")

# ПРОВЕРКА ПЛАТЕЖА
@dp.pre_checkout_query_handler(lambda query: True)
async def pre_checkout(pre_checkout_query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

# УСПЕШНАЯ ОПЛАТА
@dp.message_handler(content_types=['successful_payment'])
async def successful_payment(message: types.Message):
    amount = message.successful_payment.total_amount // 100
    
    await message.answer(
        f"✅ ОПЛАТА ПРОШЛА УСПЕШНО!\n"
        f"💰 Сумма: {amount} руб.\n"
        f"🆔 ID: {message.from_user.id}\n\n"
        f"🎉 Тест пройден! Оплата работает!"
    )
    
    await bot.send_message(
        YOUR_TELEGRAM_ID,
        f"✅ ТЕСТОВАЯ ОПЛАТА\n"
        f"Сумма: {amount} руб.\n"
        f"ID: {message.from_user.id}"
    )

# ЗАПУСК
if __name__ == '__main__':
    print("🚀 ЗАПУСК ТЕСТОВОГО БОТА")
    print(f"🔑 PROVIDER_TOKEN: {PROVIDER_TOKEN[:20]}...")
    executor.start_polling(dp, skip_updates=True)