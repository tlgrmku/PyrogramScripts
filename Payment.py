from pyrogram import Client, filters
from pyrogram.types import Message, Update
from pyrogram.raw.functions.messages import SendMedia, SetBotPrecheckoutResults
from pyrogram.raw.types import (
    DataJSON,
    InputMediaInvoice,
    Invoice,
    LabeledPrice,
    MessageActionPaymentSentMe,
    UpdateBotPrecheckoutQuery,
    UpdateNewMessage,
)

money_token = ''

app = Client('bot')


@app.on_message(filters.command('pay') & filters.private)
async def payment(app: Client, message: Message):
    peer = await app.resolve_peer(message.from_user.username)
    await app.invoke(SendMedia(
        peer=peer,
        media=InputMediaInvoice(
            title='Покупка подписки',
            description='Подписка на бота',
            invoice=Invoice(
                currency='RUB',
                prices=[LabeledPrice(label='Подписка', amount=10000)],
                test=True
                ),
            payload=b'payment',
            provider=money_token,
            provider_data=DataJSON(data=r'{}')
            ),
        message='',
        random_id=app.rnd_id()
        )
    )

@app.on_raw_update()
async def raw_update(_, update, users, chats):
    if isinstance(update, UpdateBotPrecheckoutQuery):
        await app.invoke(SetBotPrecheckoutResults(query_id=update.query_id, success=True))

    if (isinstance(update, UpdateNewMessage) and hasattr(update.message, 'action') and isinstance(update.message.action, MessageActionPaymentSentMe)):
        user = users[update.message.peer_id.user_id]
        await app.send_message(user.id, 'Подписка оформлена.')
        print(user.id, user.first_name, user.username, 'подписка оформлена.')


app.run()
