import messages
import payment
import os
import logging
from dalle2 import Dalle2
# you need the python-telegram-bot prerelease (v20.0)
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv
import qrcode

load_dotenv()

# logging configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# initialize dalle with api token
dalle = Dalle2(os.environ['openai_token'])

# telegram functions

user_state = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=messages.start)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=messages.todo)


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=messages.help)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=messages.todo)


async def problem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=messages.problem)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=messages.todo)


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_state[update.effective_chat.id] = [update.message.text, payment.getinvoice()]
    img = qrcode.make("lightning:" + user_state[update.effective_chat.id][1]['payment_request'])
    img.save(str(update.effective_chat.id) + ".png")
    await context.bot.send_photo(chat_id=update.effective_chat.id,
                                 photo=open(str(update.effective_chat.id) + ".png", 'rb'))
    os.remove(str(update.effective_chat.id) + ".png")
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="lightning:" + user_state[update.effective_chat.id][1]['payment_request'])
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Press /generate once you paid the invoice")


async def paid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if payment.checkinvoice(user_state[update.effective_chat.id][1]['payment_hash']):
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Generating pictures, this will take some time...")
        file_paths = dalle.generate_and_download(user_state[update.effective_chat.id][0])
        user_state.pop(update.effective_chat.id)
        if isinstance(file_paths, list):
            for n in file_paths:
                await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(n, 'rb'))
                os.remove(n)
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text=messages.violation)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="You haven't paid, press /generate again once you paid the invoice")


async def terms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=messages.terms)


async def source(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=messages.source)


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="Sorry, I didn't understand that command. Please try /start or /help")


if __name__ == '__main__':
    # initialize telegram bot with botfather api token
    application = ApplicationBuilder().token(os.environ['telegram_token']).build()

    # handlers
    start_handler = CommandHandler('start', start)
    help_handler = CommandHandler('help', help)
    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
    payment_handler = CommandHandler('generate', paid)
    term_handler = CommandHandler('terms', terms)
    problem_handler = CommandHandler('problem', problem)
    source_handler = CommandHandler('source', source)

    # enable handlers
    application.add_handler(start_handler)
    application.add_handler(help_handler)
    application.add_handler(echo_handler)
    application.add_handler(payment_handler)
    application.add_handler(term_handler)
    application.add_handler(problem_handler)
    application.add_handler(source_handler)

    # unknown handler
    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    application.add_handler(unknown_handler)

    # run telegram bot
    application.run_polling()
