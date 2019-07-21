import datetime
import json
import os
import yaml

from telegram.ext import Updater, CommandHandler
import logging
from telegram.ext import MessageHandler, Filters
from bd_const import env_variables as BD
from gsheet_helpers import gspread_helper

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


def init():
    env_file = '.env.yaml'
    if os.path.exists(env_file):
        print('find local env file')
        with open(env_file, 'r') as f:
            data = yaml.safe_load(f)
            for k, v in data.items():
                os.environ[k] = str(v)

    assert BD.BD_BOT_TELEGRAM_BOT_TOKEN in os.environ.keys()

    BOT_USERS = json.loads(os.environ.get(BD.BD_BOT_STIL_USERS))

    BD_DF = gspread_helper.get_dates_persons_df()
    print(BD_DF)
    print(BOT_USERS)
    return BD_DF, BOT_USERS


########################
BD_DF, BOT_USERS = init()


########################


def command_start(bot, update):
    update.message.reply_text('Hello World!')


def command_hello(bot, update):
    # update.message.reply_text(
    #     'Hello {}'.format(update.message.from_user.first_name))
    t = 'Hello'
    user = update.message.from_user.username
    update.message.reply_text(t)


def command_today(bot, update):
    # update.message.reply_text(
    #     'Hello {}'.format(update.message.from_user.first_name))
    user = update.message.from_user.username
    if user not in BOT_USERS:
        update.message.reply_text('У вас нет разрешения на доступ. Обратитесь к @stoyanovd')
        return
    current_date = datetime.datetime.now().date()

    today = BD_DF[BD_DF['bd_date'].dt.date == current_date]
    print(today)
    if len(today) == 0:
        t = 'Сегодня нет дней рождения.'
    else:
        t = 'Сегодня День рождения у ' + ','.join(today['person'])
    update.message.reply_text(t)


def command_cron():
    pass


def command_echo(bot, update):
    # global d
    bot.send_message(chat_id=update.message.chat_id, text="let's work with it")

    msg = update.message.text
    print(msg)

    bot.send_message(chat_id=update.message.chat_id, text='rr')


def main():
    #################################################
    TELEGRAM_BOT_TOKEN = os.environ.get(BD.BD_BOT_TELEGRAM_BOT_TOKEN)
    PORT = int(os.environ.get(BD.BD_BOT_PORT, '5000'))
    BOT_WEBHOOK_URL = os.environ.get(BD.BD_BOT_WEBHOOK_URL)

    updater = Updater(TELEGRAM_BOT_TOKEN)

    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('start', command_start))
    dispatcher.add_handler(CommandHandler('hello', command_hello))
    dispatcher.add_handler(CommandHandler('today', command_today))

    dispatcher.add_handler(MessageHandler(Filters.text, command_echo))

    print("finish set up bot.")

    use_polling = False
    if use_polling:
        updater.start_polling()
    else:
        updater.start_webhook(listen="0.0.0.0",
                              port=PORT,
                              url_path="" + TELEGRAM_BOT_TOKEN)
        updater.bot.set_webhook(BOT_WEBHOOK_URL + TELEGRAM_BOT_TOKEN)

    print("before idle")
    updater.idle()
    print("after idle")


#################################################
if __name__ == '__main__':
    main()
