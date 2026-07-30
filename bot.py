import asyncio
import json

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    LabeledPrice,
    PreCheckoutQuery
)
from aiogram.filters import Command

from config import (
    BOT_TOKEN,
    PROVIDER_TOKEN,
    ADMIN_ID,
    CHANNEL_ID,
    PRICE
)

from database import (
    init_db,
    get_user,
    add_subscription,
    get_all_users,
    delete_user
)


bot = Bot(token=BOT_TOKEN)

dp = Dispatcher()


# ==========================
# КНОПКИ
# ==========================

def buy_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🖤 Купить доступ на месяц",
                    callback_data="buy"
                )
            ]
        ]
    )


# ==========================
# START
# ==========================

@dp.message(Command("start"))
async def start(message: Message):

    user_id = message.from_user.id

    expire = await get_user(user_id)


    if expire:

        await message.answer(
            f"✅ У вас уже есть подписка\n\n"
            f"📅 Действует до:\n"
            f"{expire.strftime('%d.%m.%Y')}\n\n"
            f"Можно продлить:",
            reply_markup=buy_keyboard()
        )

        return


    await message.answer(
        "🖤 Добро пожаловать!\n\n"
        "Нажмите кнопку ниже,что бы получить доступ к каналу на 30 дней.\n",
        reply_markup=buy_keyboard()
    )



# ==========================
# ОПЛАТА
# ==========================

@dp.callback_query(F.data == "buy")
async def buy(callback: CallbackQuery):

    await callback.answer()


    receipt = {

        "receipt": {

            "items": [

                {

                    "description": " ",

                    "quantity": "1.00",

                    "amount": {

                        "value": "1300.00",

                        "currency": "RUB"

                    },

                    "vat_code": 1

                }

            ]

        }

    }


    await bot.send_invoice(
    chat_id=callback.from_user.id,
    title="Подписка на канал",
    description="Доступ к закрытому контенту",
    payload=f"subscription_{callback.from_user.id}",
    provider_token=PROVIDER_TOKEN,
    currency="RUB",
    prices=[
        LabeledPrice(
            label="Подписка",
            amount=130000
        )
    ],
    start_parameter="subscription",
    need_phone_number=True,
    need_email=True,
    send_phone_number_to_provider=True,
    send_email_to_provider=True,
    provider_data='{"receipt": {"items": [{"description": "Подписка на канал", "quantity": "1.00", "amount": {"value": "1300.00", "currency": "RUB"}, "vat_code": 4}], "tax_system_code": 0}}'
)
# ==========================
# ПРОВЕРКА ПЛАТЕЖА
# ==========================

@dp.pre_checkout_query()
async def checkout(query: PreCheckoutQuery):

    await bot.answer_pre_checkout_query(
        query.id,
        ok=True
    )



# ==========================
# УСПЕШНАЯ ОПЛАТА
# ==========================

@dp.message(F.successful_payment)
async def payment_success(message: Message):

    user_id = message.from_user.id


    expire = await add_subscription(user_id)


    try:

        invite = await bot.create_chat_invite_link(

            chat_id=CHANNEL_ID,

            member_limit=1

        )

    except Exception as e:


        await bot.send_message(

            ADMIN_ID,

            f"❌ Ошибка создания ссылки:\n{e}"

        )


        await message.answer(
            "Произошла ошибка."
        )

        return



    await message.answer(

        "🖤 Оплата прошла успешно!\n\n"

        f"🔗 Ваша ссылка:\n"
        f"{invite.invite_link}\n\n"

        f"📅 Доступ до:\n"
        f"{expire.strftime('%d.%m.%Y')}"

    )


    await bot.send_message(

        ADMIN_ID,

        f"🤑 Новый платеж!\n\n"

        f"👤 {message.from_user.full_name}\n"

        f"ID: {user_id}\n"

        f"До: {expire.strftime('%d.%m.%Y')}"

    )



# ==========================
# АДМИН СТАТИСТИКА
# ==========================

@dp.message(Command("stats"))
async def stats(message: Message):

    if message.from_user.id != ADMIN_ID:

        return


    users = await get_all_users()


    await message.answer(

        f"📊 Статистика\n\n"

        f"Всего подписчиков: {len(users)}"

    )



# ==========================
# УДАЛЕНИЕ ПРОСРОЧЕННЫХ
# ==========================

async def check_expired():

    from datetime import datetime


    while True:

        users = await get_all_users()

        now = datetime.now()


        for user_id, date in users:

            expire = datetime.fromisoformat(date)


            if expire <= now:


                try:

                    await bot.ban_chat_member(

                        CHANNEL_ID,

                        user_id

                    )

                    await bot.unban_chat_member(

                        CHANNEL_ID,

                        user_id

                    )


                except Exception:

                    pass


                await delete_user(user_id)



        await asyncio.sleep(3600)



# ==========================
# ЗАПУСК
# ==========================

async def main():

    await init_db()

    asyncio.create_task(
        check_expired()
    )


    print("BOT STARTED")


    await dp.start_polling(bot)



if __name__ == "__main__":

    asyncio.run(main())