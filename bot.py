import asyncio
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.types import LabeledPrice, PreCheckoutQuery, ContentType

# ==========================================
# ВАШИ ДАННЫЕ
# ==========================================
BOT_TOKEN = "8439119682:AAFeCLMNd5g8dsxEattUB7tiYb-2mK7w0ck"
PROVIDER_TOKEN = "live_mB44CKbSz6YjwlI9ArHdbAoJtW2qSWpRISmE83mvDCQ"  # БОЕВОЙ ТОКЕН
ADMIN_ID = 6217476601
CHANNEL_ID = -1001234567890  # ✅ ВАШ ID КАНАЛА (ВСТАВЛЕН!)
PRICE = 100  # 1 РУБЛЬ (ТЕСТ!)
# ==========================================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Команда /start
@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    # Создаем кнопку
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("💳 Оплатить 1 рубль", pay=True)
    markup.add(btn)
    
    # ОТПРАВЛЯЕМ СЧЕТ (INVOICE)!
    # Без этой функции кнопка не откроет оплату
    await bot.send_invoice(
        message.chat.id,
        title="Тестовый товар",
        description="Покупка доступа к боту",
        payload="test_payload",
        provider_token=PROVIDER_TOKEN,
        currency="RUB",
        prices=[LabeledPrice(label="Доступ к боту", amount=PRICE)],
        start_parameter="test",
        need_email=False,
        need_phone_number=False,
        need_shipping_address=False,
        is_flexible=False
    )

# Обработчик нажатия на кнопку оплаты (когда деньги списались)
@dp.message_handler(content_types=ContentType.SUCCESSFUL_PAYMENT)
async def process_successful_payment(message: types.Message):
    await message.answer("✅ Оплата прошла успешно! Спасибо за покупку!")

# Обработчик PreCheckout (Обязателен!)
@dp.pre_checkout_query_handler()
async def process_pre_checkout_query(query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(query.id, ok=True)

if __name__ == '__main__':
    print("🚀 БОТ ЗАПУЩЕН И ГОТОВ К ОПЛАТЕ!")
    executor.start_polling(dp, skip_updates=True)
