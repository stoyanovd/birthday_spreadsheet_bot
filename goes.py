import datetime
import json
import os
import yaml
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


########################################################################
def env_init():
    env_file = '.env.yaml'
    if os.path.exists(env_file):
        print('find local env file')
        with open(env_file, 'r') as f:
            data = yaml.safe_load(f)
            for k, v in data.items():
                os.environ[k] = str(v)


########################################################################
env_init()
import sentry_sdk

sentry_sdk.init(os.environ['SENTRY_TOKEN_URL'])

########################################################################

from telegram import ext as T
import peewee as P
from playhouse.db_url import connect

from gsheet_helpers import gspread_helper
from bd_const import env_variables as BD

BD_DF = None
BOT_USERS = None


def refresh_gspread_and_bot_users():
    global BD_DF, BOT_USERS
    BD_DF, error_message = gspread_helper.get_dates_persons_df()
    BOT_USERS = json.loads(os.environ.get(BD.BD_BOT_STIL_USERS))
    return error_message


def init_second():
    assert BD.BD_BOT_TELEGRAM_BOT_TOKEN in os.environ.keys()

    refresh_gspread_and_bot_users()

    print(BD_DF)
    print(BOT_USERS)


init_second()
# BD_DATABASE = P.PostgresqlDatabase(DATABASE_URL)
BD_DATABASE = connect(os.environ['DATABASE_URL'])


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
    # db.create_tables([User, Notification])


db_init()


def create_user_if_needed(username, chat_id):
    if User.select(User.username == username).count() == 0:
        new_user = User(username=username, chat_id=chat_id)
        new_user.save()


def command_start(bot, update):
    username = update.message.from_user.username
    chat_id = update.message.chat_id
    create_user_if_needed(username, chat_id)

    update.message.reply_text('Привет! Я буду слать вам напоминания о днях рождения, '
                              'записанных в ваш google spreadsheet документ.')


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
    username = update.message.from_user.username
    chat_id = update.message.chat_id

    error_message = refresh_gspread_and_bot_users()
    if error_message:
        bot.send_message(chat_id=chat_id, text="У вас в Spreadsheet есть ошибки: " + error_message)

    send_today(bot, username, chat_id, False)


def send_notifications_per_user(bot, job, user, error_message):
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
        if error_message:
            bot.send_message(chat_id=chat_id, text="У вас в Spreadsheet есть ошибки: " + error_message)
        send_today(bot, username, chat_id, True)
        # bot.send_message(chat_id=update.message.chat_id, text="let's work with it")


def callback_send_notifications_morning(bot, job):
    if User.select().count() == 0:
        print('no rows in User. return')
        return

    error_message = refresh_gspread_and_bot_users()

    users = list(User.select())
    print('users: ', users)
    for u in users:
        send_notifications_per_user(bot, job, u, error_message)


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
    dispatcher.add_handler(T.CommandHandler('today', command_today))

    # dispatcher.add_handler(T.MessageHandler(T.Filters.text, command_echo))

    j = updater.job_queue
    job_interval = 60 * 10
    # job_interval = 60
    job_for_check = j.run_repeating(callback_send_notifications_morning, interval=job_interval, first=0)

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
