import asyncio
from datetime import datetime

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
# КНОПКА ПОКУПКИ
# ==========================

def buy_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🖤 Купить доступ на 30 дней",
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
            "🖤 У вас уже есть активная подписка.\n\n"
            f"📅 Действует до:\n"
            f"{expire.strftime('%d.%m.%Y')}\n\n"
            "Можно продлить доступ:",
            reply_markup=buy_keyboard()
        )

        return


    await message.answer(
        "🖤 Добро пожаловать!\n\n"
        "После оплаты вы получите доступ "
        "к закрытому каналу на 30 дней.",
        reply_markup=buy_keyboard()
    )


# ==========================
# СОЗДАНИЕ ОПЛАТЫ
# ==========================

@dp.callback_query(F.data == "buy")
async def buy(callback: CallbackQuery):

    await callback.answer()


    try:

        await bot.send_invoice(

            chat_id=callback.from_user.id,

            title="Подписка на канал",

            description=(
                "Доступ к закрытому Telegram-каналу "
                "на 30 дней"
            ),

            payload=(
                f"channel_subscription_"
                f"{callback.from_user.id}"
            ),

            provider_token=PROVIDER_TOKEN,

            currency="RUB",

            prices=[
                LabeledPrice(
                    label="Доступ на 30 дней",
                    amount=PRICE
                )
            ],

            start_parameter="channel_access"

        )


    except Exception as e:

        print(
            "ОШИБКА СОЗДАНИЯ ПЛАТЕЖА:",
            e
        )

        await callback.message.answer(
            "❌ Не удалось открыть оплату.\n\n"
            f"{e}"
        )


# ==========================
# ПРОВЕРКА ПЕРЕД ОПЛАТОЙ
# ==========================

@dp.pre_checkout_query()
async def checkout(
    query: PreCheckoutQuery
):

    await bot.answer_pre_checkout_query(
        query.id,
        ok=True
    )


# ==========================
# УСПЕШНАЯ ОПЛАТА
# ==========================

@dp.message(F.successful_payment)
async def payment_success(
    message: Message
):

    payment = message.successful_payment


    if payment.currency != "RUB":

        return


    if payment.total_amount != PRICE:

        return


    user_id = message.from_user.id


    expire = await add_subscription(
        user_id
    )


    try:

        invite = await bot.create_chat_invite_link(

            chat_id=CHANNEL_ID,

            member_limit=1

        )


    except Exception as e:


        await bot.send_message(

            ADMIN_ID,

            f"❌ Не могу создать ссылку:\n{e}"

        )


        await message.answer(

            "Оплата прошла, но произошла ошибка "
            "при выдаче доступа.\n"
            "Напишите администратору."

        )

        return



    await message.answer(

        "🖤 Оплата прошла успешно!\n\n"

        "Ваш доступ к каналу:\n"

        f"{invite.invite_link}\n\n"

        "📅 Доступ до:\n"

        f"{expire.strftime('%d.%m.%Y')}"

    )


    await bot.send_message(

        ADMIN_ID,

        "🤑 Новый платеж!\n\n"

        f"👤 {message.from_user.full_name}\n"

        f"ID: {user_id}\n"

        f"До: {expire.strftime('%d.%m.%Y')}"

    )


# ==========================
# СТАТИСТИКА
# ==========================

@dp.message(Command("stats"))
async def stats(message: Message):

    if message.from_user.id != ADMIN_ID:

        return


    users = await get_all_users()


    await message.answer(

        "📊 Статистика\n\n"

        f"Подписчиков: {len(users)}"

    )



# ==========================
# УДАЛЕНИЕ ПРОСРОЧЕННЫХ
# ==========================

async def check_expired():


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



                await delete_user(
                    user_id
                )



        await asyncio.sleep(3600)



# ==========================
# ЗАПУСК
# ==========================

async def main():

    await init_db()


    asyncio.create_task(
        check_expired()
    )


    print(
        "BOT STARTED"
    )


    await dp.start_polling(
        bot
    )



if __name__ == "__main__":

    asyncio.run(main())