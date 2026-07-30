import asyncio
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.types import LabeledPrice

BOT_TOKEN = "8439119682:AAFeCLMNd5g8dsxEattUB7tiYb-2mK7w0ck"
PROVIDER_TOKEN = "390540012:LIVE:100092"  # Или 381764678:TEST:185557

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def pay(message: types.Message):
    await bot.send_invoice(
        message.chat.id,
        title="Тест оплаты",
        description="Покупка теста",
        payload="test_payload",
        provider_token=PROVIDER_TOKEN,
        currency="RUB",
        prices=[LabeledPrice(label="Тест", amount=100)],
        start_parameter="test"
    )

@dp.pre_checkout_query_handler()
async def process_pre_checkout_query(query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(query.id, ok=True)

@dp.message_handler(content_types=types.ContentTypes.SUCCESSFUL_PAYMENT)
async def process_successful_payment(message: types.Message):
    await message.answer("Оплата прошла!")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
