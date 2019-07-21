import os

from telegram.ext import Updater, CommandHandler
import logging
from telegram.ext import MessageHandler, Filters
import pymorphy2

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


def start(bot, update):
    update.message.reply_text('Hello World!')


def hello(bot, update):
    # update.message.reply_text(
    #     'Hello {}'.format(update.message.from_user.first_name))
    t = 'Hello'
    update.message.reply_text(t)


orders_dict = {
    'VERB': 4,
    'INFN': 3,
    'PRED': 2
}


def sorting_rule(word_desc):
    for k in orders_dict.keys():
        if k in word_desc:
            return orders_dict[k]
    return 0


def echo(bot, update):
    # global d
    bot.send_message(chat_id=update.message.chat_id, text="let's work with it")

    msg = update.message.text
    print(msg)

    morph = pymorphy2.MorphAnalyzer()

    a = msg.split(' ')
    [print(morph.parse(a[i])[0].tag) for i in range(min(len(a), 20))]
    a = sorted(a, key=lambda s: sorting_rule(morph.parse(s)[0].tag))

    ans = ' '.join(a)
    bot.send_message(chat_id=update.message.chat_id, text=ans)


#################################################
from yaml import load, dump

env_file = '.env.yaml'

token_str = 'TELEGRAM_BOT_TOKEN'

if os.path.exists(env_file):
    print('find local env file')
    with open(env_file, 'r') as f:
        data = load(f)
        assert token_str in data.keys()
        os.environ[token_str] = data[token_str]

assert token_str in os.environ.keys()

TOKEN = os.environ.get(token_str)
PORT = int(os.environ.get('PORT', '5000'))

#################################################


updater = Updater(TOKEN)

dispatcher = updater.dispatcher
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('hello', hello))

dispatcher.add_handler(MessageHandler(Filters.text, echo))

print("finish set up bot.")

updater.start_webhook(listen="0.0.0.0",
                      port=PORT,
                      url_path="" + TOKEN)
updater.bot.set_webhook("https://yodabotrus.herokuapp.com/" + TOKEN)

# time to try webhooks
# updater.start_polling()

print("before idle")
updater.idle()
print("after idle")
