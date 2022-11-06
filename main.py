import messages
import payment
import stablediffusion
import os
import logging
from dalle2 import Dalle2
# you need the python-telegram-bot prerelease (v20.0)
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv
import qrcode
import time
from rclone.rclone import Rclone

rc = Rclone()


load_dotenv()

# logging configuration
logging.basicConfig(
    filename="mylog.txt",
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# initialize dalle with api token
dalle = Dalle2(os.environ['openai_token'])

# telegram functions

user_state = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=messages.start)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=messages.group)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=messages.todo)
    except:
        print("Sending /start message failed")
        logging.error("Sending start message failed")


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=messages.help)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=messages.todo)


async def problem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=messages.problem)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=messages.todo)


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if str(chat_id) == str(os.environ['tg_group_id']):
        pass
    else:
        user_state[chat_id] = [update.message.text, payment.getinvoice(), False]
        img = qrcode.make("lightning:" + user_state[chat_id][1]['payment_request'])
        img.save(str(chat_id) + ".png")
        try:
            await context.bot.send_photo(chat_id=chat_id,
                                         photo=open(str(chat_id) + ".png", 'rb'))
            os.remove(str(chat_id) + ".png")
            await context.bot.send_message(chat_id=chat_id,
                                           text="`lightning:" + user_state[chat_id][1][
                                               'payment_request'] + "`",
                                           parse_mode='MarkdownV2')
            await context.bot.send_message(chat_id=chat_id, text="Press \n/generate_dalle2 \nor \n "
                                                                 "/generate_stablediffusion \nonce you "
                                                                 "paid the invoice")
        except:
            logging.error("Answer to command failed")
            print("Answer to command failed")

async def group_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_state[chat_id] = [update.message.text[8:], payment.getinvoice(), False]
    img = qrcode.make("lightning:" + user_state[chat_id][1]['payment_request'])
    img.save(str(chat_id) + ".png")
    try:
        await context.bot.send_photo(chat_id=chat_id,
                                     photo=open(str(chat_id) + ".png", 'rb'))
        os.remove(str(chat_id) + ".png")
        await context.bot.send_message(chat_id=chat_id,
                                       text="`lightning:" + user_state[chat_id][1][
                                           'payment_request'] + "`",
                                       parse_mode='MarkdownV2')
        await context.bot.send_message(chat_id=chat_id, text="Press \n/generate_dalle2 \nor \n "
                                                             "/generate_stablediffusion \nonce you "
                                                             "paid the invoice")
    except:
        logging.error("Answer to command failed")
        print("Answer to command failed")


async def paid_dalle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in user_state:
        if payment.checkinvoice(user_state[chat_id][1]['payment_hash']):
            await context.bot.send_message(chat_id=chat_id,
                                           text="Generating pictures, this will take around 1 minute..")
            for generating in range(2):
                try:
                    file_paths = dalle.generate_and_download(user_state[chat_id][0])
                    if isinstance(file_paths, list):
                        for n in file_paths:
                            await context.bot.send_photo(chat_id=chat_id, photo=open(n, 'rb'))
                            os.remove(n)
                        user_state.pop(chat_id)
                    elif file_paths == "violation":
                        logging.info("dalle violation: " + user_state[chat_id][0])
                        await context.bot.send_message(chat_id=chat_id,
                                                       text=messages.violation)
                        user_state.pop(chat_id)
                    elif file_paths == "failure":
                        logging.error(user_state[chat_id][0])
                        await context.bot.send_message(chat_id=chat_id,
                                                       text="This request failed due to some problems with the DALLE2 "
                                                            "API.")
                        await context.bot.send_message(chat_id=chat_id,
                                                       text="You can use /refund lnbc...(invoice) with a 1000 "
                                                            "Satoshi invoice to get a refund.")
                        user_state[chat_id][2] = True
                    break
                except:
                    logging.error(user_state[chat_id][0])
                    await context.bot.send_message(chat_id=chat_id,
                                                   text="Failed, trying again. If it doesn't give you pictures in a "
                                                        "minute click /problem")
                    time.sleep(15)
        else:
            await context.bot.send_message(chat_id=chat_id,
                                           text="You haven't paid, press \n/generate_dalle2 again once you paid the "
                                                "invoice")
    else:
        pass


async def paid_stablediffusion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in user_state:
        if payment.checkinvoice(user_state[chat_id][1]['payment_hash']):
            await context.bot.send_message(chat_id=chat_id,
                                           text="Generating pictures, this will take around 1 minute..")
            for generating in range(2):
                if stablediffusion.find_seed(user_state[chat_id][0]) == "seed_too_long":
                    await context.bot.send_message(chat_id=chat_id,
                                                   text="Seed too long, use max. 9 digits, generating without seed "
                                                        "now.")
                elif stablediffusion.find_seed(user_state[chat_id][0]) == "seed_no_int":
                    await context.bot.send_message(chat_id=chat_id,
                                                   text="Seed no integer (number), generating without seed now.")
                try:
                    stablediffusion.generate_sd_normal(user_state[chat_id][0], str(chat_id))
                    for guidance in range(7, 11):
                        await context.bot.send_photo(chat_id=chat_id, photo=open(
                            'sd_picture_gd_' + str(guidance) + "_" + str(chat_id) + '.png', 'rb'))
                        os.remove('sd_picture_gd_' + str(guidance) + "_" + str(chat_id) + '.png')
                        time.sleep(1)
                    logging.info('sd: ' + user_state[chat_id][0])
                    user_state.pop(chat_id)
                    break
                except:
                    if generating == 0:
                        logging.error("sd error: " + user_state[chat_id][0])
                        await context.bot.send_message(chat_id=chat_id,
                                                       text="Failed, trying again. If it doesn't give you pictures in a "
                                                            "minute click /problem")
                        time.sleep(15)
                    elif generating == 1:
                        logging.error(user_state[chat_id][0])
                        await context.bot.send_message(chat_id=chat_id,
                                                       text="This request failed due to some problems with the SD "
                                                            "API.")
                        await context.bot.send_message(chat_id=chat_id,
                                                       text="You can use /refund lnbc...(invoice) with a 1000 "
                                                            "Satoshi invoice to get a refund.")
                        user_state[chat_id][2] = True
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text="You haven't paid, press \n/generate_stablediffusion again once you "
                                                "paid the invoice")
    else:
        pass


async def terms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=messages.terms)


async def source(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=messages.source)


async def refund(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    try:
        if user_state[chat_id][2] != True:
            await context.bot.send_message(chat_id=chat_id, text="You are not supposed to get a refund, if you are and "
                                                                 "this is an error contact @f321x")
            logging.info("!!! Somebody tried to refund without True")
        elif user_state[chat_id][2] == True:
            await context.bot.send_message(chat_id=chat_id, text="Trying to refund...")
            refund = payment.refund(update.message.text[8:])
            if refund == "success":
                user_state.pop(chat_id)
                await context.bot.send_message(chat_id=chat_id, text="Refund successful!")
            elif refund == "wrong":
                await context.bot.send_message(chat_id=chat_id, text="Your invoice is invalid, please try again with a "
                                                                     "1000 Satoshi invoice. Use the format /refund "
                                                                     "bolt11Invoice")
            elif refund == "error":
                await context.bot.send_message(chat_id=chat_id, text="Refunding failed, please try again with an "
                                                                     "invoice from another Wallet")
    except:
        await context.bot.send_message(chat_id=chat_id, text="You are not supposed to get a refund, if you are and "
                                                             "this is an error contact @f321x")
        logging.info("!!! Somebody tried to refund without True")


async def logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    logging.info("!!! Somebody used /logs !!!")
    if update.message.text[6:] == os.environ['log_pw']:
        log_file = open('mylog.txt', 'rb')
        await context.bot.send_document(chat_id, log_file)
        log_file.close()
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Sorry, I didn't understand that command. Please try /start or /help")
        time.sleep(3)


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) == str(os.environ['tg_group_id']):
        pass
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Sorry, I didn't understand that command. Please try /start or /help")


if __name__ == '__main__':
    # initialize telegram bot with botfather api token
    application = ApplicationBuilder().token(os.environ['telegram_token']).build()

    # handlers
    start_handler = CommandHandler('start', start)
    help_handler = CommandHandler('help', help)
    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
    group_handler = CommandHandler('prompt', group_prompt)
    payment_handler_dalle = CommandHandler('generate_dalle2', paid_dalle)
    payment_handler_sd = CommandHandler('generate_stablediffusion', paid_stablediffusion)
    term_handler = CommandHandler('terms', terms)
    problem_handler = CommandHandler('problem', problem)
    source_handler = CommandHandler('source', source)
    refund_handler = CommandHandler('refund', refund)
    log_handler = CommandHandler('logs', logs)

    # enable handlers
    application.add_handler(start_handler)
    application.add_handler(help_handler)
    application.add_handler(echo_handler)
    application.add_handler(group_handler)
    application.add_handler(payment_handler_dalle)
    application.add_handler(payment_handler_sd)
    application.add_handler(term_handler)
    application.add_handler(problem_handler)
    application.add_handler(source_handler)
    application.add_handler(refund_handler)
    application.add_handler(log_handler)

    # unknown handler
    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    application.add_handler(unknown_handler)

    # run telegram bot
    application.run_polling()

