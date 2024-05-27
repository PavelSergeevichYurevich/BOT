import os
import aiohttp
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackContext, CallbackQueryHandler

os.system('cls||clear')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f'Добро пожаловать пользователь в сервис <b>OPEN MUSIC</b>', parse_mode='html')
    keyboard = [
        [
            InlineKeyboardButton("Register", callback_data="1")
        ],
        [
            InlineKeyboardButton("Download music", callback_data="2")
        ],
        [
            InlineKeyboardButton("View search history", callback_data="3")
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose:", reply_markup=reply_markup)

async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    text:str = 'Enter the /register <username> <password> for registration'
    await context.bot.send_message(query.message.chat.id, text=text)
    
async def search_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    text:str = 'Enter the /tracks for view search  history'
    await context.bot.send_message(query.message.chat.id, text=text)

async def register_user(update: Update, context: CallbackContext):
    if len(context.args) == 2:
            username, password = context.args
            telegram_id = update.message.chat.id
            async with aiohttp.ClientSession() as session:
                data = {"username": username, "password": password, "telegram_id": telegram_id}
                response = await session.post('http://127.0.0.1:8000/register', json=data)
                if response.status == 201:
                    await update.message.reply_text(text=f'Вы успешно зарегистрировались в системе <b>OPEN MUSIC</b>\n Ваш login: {username}\nPassword: {password}', parse_mode='html')
                elif response.status == 202:
                    await update.message.reply_text(text=f"Данные обновлены . . .")
                elif response.status == 401:
                    await update.message.reply_text(text=f"Вы уже зарегистрированы . . .")
                else:
                    await update.message.reply_text(text=f"Что то пошло не так . . .")
    else:   
        await update.message.reply_text('Не корректая форма для регистрации')

async def download_by_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    text:str = 'Enter the /download <track name or link> for download'
    await context.bot.send_message(query.message.chat.id, text=text)

async def youtube_download(update: Update, context: CallbackContext):
    search:str = ' '.join(context.args)
    telegram_id = update.message.chat.id
    async with aiohttp.ClientSession() as session:
        data = {"telegram_id": telegram_id, "search_string": search}
        response = await session.post('http://127.0.0.1:8000/download', json=data)
        if response.status == 200:
            from anyio import open_file
            async with await open_file('audio_file.mp3', 'wb') as file:
                content = await response.read()
                await file.write(content)
                await context.bot.send_audio(chat_id=telegram_id, audio='audio_file.mp3')

async def tracks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import aiohttp
    telegram_id = update.message.chat.id
    async with aiohttp.ClientSession() as session:
        data = {"telegram_id": telegram_id}
        async with session.post(f'http://127.0.0.1:8000/tracks/', json=data) as response:
            text = await response.text()
            await update.message.reply_text(text = text)
    


def main() -> None:
    TOKEN = '6909703788:AAH7gSDXAWb9b64VlZNTlp-527GDksG9uPI'
    application = Application.builder().token(token=TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('register', register_user))
    application.add_handler(CommandHandler('download', youtube_download))
    application.add_handler(CommandHandler('tracks', tracks))
    application.add_handler(CallbackQueryHandler(login, pattern='1'))
    application.add_handler(CallbackQueryHandler(download_by_name, pattern='2'))
    application.add_handler(CallbackQueryHandler(search_history, pattern='3'))
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    print('Start bot . . .')
    main()
    print('Stopped bot . . .')

