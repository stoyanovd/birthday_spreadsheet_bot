import datetime
import json
import os

import yaml

from telegram import ext as T
import logging

from bd_const import env_variables as BD
from gsheet_helpers import gspread_helper

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

import peewee as P
from playhouse.db_url import connect


########################################################################
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
    DATABASE_URL = os.environ['DATABASE_URL']

    print(BD_DF)
    print(BOT_USERS)

    return BD_DF, BOT_USERS, DATABASE_URL


BD_DF, BOT_USERS, DATABASE_URL = init()
# BD_DATABASE = P.PostgresqlDatabase(DATABASE_URL)
BD_DATABASE = connect(DATABASE_URL)


########################################################################
########################################################################


class BaseModel(P.Model):
    class Meta:
        database = BD_DATABASE


class User(BaseModel):
    username = P.CharField(unique=True)
    chat_id = P.CharField(unique=True)


class Notification(BaseModel):
    user = P.ForeignKeyField(User, backref='notifications')
    message = P.TextField()
    created_date = P.DateTimeField(default=datetime.datetime.utcnow)
    # hb_person = P.TextField()
    is_auto_notification = P.BooleanField()


def db_init():
    db = BD_DATABASE
    db.connect()
    ##    # db.drop_tables([User, Notification])
    db.create_tables([User, Notification])


db_init()


def create_user_if_needed(username, chat_id):
    if User.select(User.username == username).count() == 0:
        new_user = User(username=username, chat_id=chat_id)
        new_user.save()


def command_start(bot, update):
    update.message.reply_text('Hello World!')


def command_hello(bot, update):
    # update.message.reply_text(
    #     'Hello {}'.format(update.message.from_user.first_name))
    t = 'Hello'
    user = update.message.from_user.username
    update.message.reply_text(t)


def get_text_of_today(is_income_question):
    current_date = datetime.datetime.utcnow().date()
    today = BD_DF[BD_DF['bd_date'].dt.date == current_date]
    if len(today) > 0:
        t = 'Сегодня Дни рождения:' + os.linesep + os.linesep.join(today['person'])
    elif is_income_question:
        t = 'Сегодня нет дней рождения.'
    else:
        t = ''

    return t


def send_today(bot, username, chat_id, is_income_question):
    create_user_if_needed(username, chat_id)

    if username not in BOT_USERS:
        t = 'У вас нет разрешения на доступ. Обратитесь к @stoyanovd'
    else:
        t = get_text_of_today(is_income_question)

    n = Notification(user=User.get(username == username),
                     message=t,
                     is_auto_notification=is_income_question)
    n.save()
    bot.send_message(chat_id=chat_id, text=t)


def command_today(bot, update):
    username = update.message.chat_id.username
    chat_id = update.message.chat_id
    send_today(bot, username, chat_id, False)


def callback_minute_per_user(bot, job, user):
    # current_date = datetime.datetime.now().date()
    current_msk_time = (datetime.datetime.utcnow() + datetime.timedelta(hours=3)).time()
    time_is_early = 'early' if current_msk_time < datetime.time(hour=7) else 'good'
    print(current_msk_time, time_is_early)
    if time_is_early == 'early':
        return

    username = user.username
    chat_id = user.chat_id
    create_user_if_needed(username, chat_id)

    notification_for_user_today = Notification.select().join(User).where(
        (User.username == username) &
        (Notification.created_date >= datetime.date.today()) &
        (Notification.is_auto_notification == True)
    ).count()

    print('user:', username,
          'chat_id: ', chat_id,
          'notification_for_user_today: ', notification_for_user_today)

    if notification_for_user_today == 0:
        send_today(bot, username, chat_id, True)
        # bot.send_message(chat_id=update.message.chat_id, text="let's work with it")


def callback_minute(bot, job):
    if User.select().count() == 0:
        print('no rows in User. return')
        return
    users = list(User.select())
    print('users: ', users)
    for u in users:
        callback_minute_per_user(bot, job, u)


def command_echo(bot, update):
    # global d
    bot.send_message(chat_id=update.message.chat_id, text="let's work with it")

    msg = update.message.text
    print(msg)

    bot.send_message(chat_id=update.message.chat_id, text='rr')


def main():
    # return
    #################################################
    TELEGRAM_BOT_TOKEN = os.environ.get(BD.BD_BOT_TELEGRAM_BOT_TOKEN)
    PORT = int(os.environ.get(BD.PORT, '5000'))
    BOT_WEBHOOK_URL = os.environ.get(BD.BD_BOT_WEBHOOK_URL)

    updater = T.Updater(TELEGRAM_BOT_TOKEN)

    dispatcher = updater.dispatcher
    dispatcher.add_handler(T.CommandHandler('start', command_start))
    dispatcher.add_handler(T.CommandHandler('hello', command_hello))
    dispatcher.add_handler(T.CommandHandler('today', command_today))

    dispatcher.add_handler(T.MessageHandler(T.Filters.text, command_echo))

    j = updater.job_queue
    job_minute = j.run_repeating(callback_minute, interval=60, first=0)

    print("finish set up bot.")

    use_polling = True
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
