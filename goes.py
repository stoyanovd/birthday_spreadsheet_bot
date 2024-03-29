import datetime
import json
import os
import yaml
import logging
from functools import wraps
import time

import sys
import io

# sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')
# sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8')

import os, sys
os.chdir(sys.path[0])

if not os.path.exists('logs'):
    os.makedirs('logs')
date_time_str = datetime.datetime.now().strftime("%Y-%m-%d__%H-%M-%S")
logfile_path = 'logs/run_' + date_time_str + '.log'

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)  # or whatever
handler = logging.FileHandler(logfile_path, 'w', 'utf-8')  # or whatever
formatter = logging.Formatter(
    '[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s', '%m-%d %H:%M:%S')
handler.setFormatter(formatter)
root_logger.addHandler(handler)
# logger = logging.getLogger(__name__)
logger = root_logger

def logger_print_info(*args):
    logger.info(' '.join(map(str, list(args))))
    
##################################

def timed(func):
    """This decorator prints the execution time for the decorated function."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        logger_print_info("Start of {}.".format(func.__name__))

        result = func(*args, **kwargs)
        end = time.time()

        logger_print_info("{} ran in {}s".format(func.__name__, round(end - start, 2)))
        return result

    return wrapper


########################################################################
def env_init():
    env_file = '.env.yaml'
    if os.path.exists(env_file):
        logger_print_info('find local env file')
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
    logger_print_info('BD_BOT_STIL_USERS=', os.environ.get(BD.BD_BOT_STIL_USERS))
    BOT_USERS = json.loads(os.environ.get(BD.BD_BOT_STIL_USERS), encoding='utf-8')
    return error_message


def init_second():
    assert BD.BD_BOT_TELEGRAM_BOT_TOKEN in os.environ.keys()

    refresh_gspread_and_bot_users()

    logger_print_info(BD_DF)
    logger_print_info(BOT_USERS)


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


# def db_init():
#     db = BD_DATABASE
#     db.connect()
#     # db.drop_tables([User, Notification])
#     db.create_tables([User, Notification])
#
#
# db_init()
# exit()

@timed
def create_user_if_needed(username, chat_id):
    logger_print_info('check user exists,', username, ',count==', User.select().where(User.username == username).count())
    if User.select().where(User.username == username).count() == 0:
        logger_print_info('New user addition : ', username, chat_id)
        new_user = User(username=username, chat_id=chat_id)
        new_user.save()


@timed
def command_start(bot, update):
    username = update.message.from_user.username
    chat_id = update.message.chat_id
    create_user_if_needed(username, chat_id)

    update.message.reply_text('Привет! Я буду слать вам напоминания о днях рождения, '
                              'записанных в ваш google spreadsheet документ.')


M_ANSWERS_today_no_birthdays = 'Сегодня нет дней рождения.'


@timed
def get_text_of_today():
    current_date = (datetime.datetime.utcnow() + datetime.timedelta(hours=3)).date()
    today = BD_DF[BD_DF['bd_date'].dt.date == current_date]
    if len(today) > 0:
        t = 'Сегодня Дни рождения:' + os.linesep + os.linesep.join(today['person'])
    else:
        t = M_ANSWERS_today_no_birthdays

    return t


@timed
def send_today(bot, username, chat_id, is_auto_notification):
    create_user_if_needed(username, chat_id)

    if username not in BOT_USERS:
        t = 'У вас нет разрешения на доступ. Обратитесь к @stoyanovd'
    else:
        t = get_text_of_today()

    is_empty = 1 if t == M_ANSWERS_today_no_birthdays else 0
    logger_print_info('is_empty=', is_empty, ' . (In case of is_empty=1 message will not be sent)')

    # we want to add is_empty to model, when we will make migrations
    n = Notification(user=User.get(User.username == username).id,
                     message=t,
                     is_auto_notification=is_auto_notification)
    n.save()
    if is_empty == 0:
        bot.send_message(chat_id=chat_id, text=t)


@timed
def command_today(bot, update):
    username = update.message.from_user.username
    chat_id = update.message.chat_id
    if username not in BOT_USERS:
        t = 'У вас нет разрешения на доступ. Обратитесь к @stoyanovd'
        bot.send_message(chat_id=chat_id, text=t)
        return

    error_message = refresh_gspread_and_bot_users()
    if error_message:
        bot.send_message(chat_id=chat_id, text="У вас в Spreadsheet есть ошибки: " + error_message)

    send_today(bot, username, chat_id, False)


@timed
def command_debug(bot, update):
    username = update.message.from_user.username
    chat_id = update.message.chat_id
    if username not in BOT_USERS:
        t = 'У вас нет разрешения на доступ. Обратитесь к @stoyanovd'
        bot.send_message(chat_id=chat_id, text=t)
        return

    t = str([(u, u.username, u.chat_id) for u in User.select()])
    bot.send_message(chat_id=chat_id, text=t)


@timed
def send_notifications_per_user(bot, user, error_message):
    # current_date = datetime.datetime.now().date()
    current_msk_time = (datetime.datetime.utcnow() + datetime.timedelta(hours=3)).time()
    time_is_early = 'early' if current_msk_time < datetime.time(hour=8, minute=20) else 'good'
    logger_print_info(current_msk_time, time_is_early)
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

    logger_print_info('user:', username,
          'chat_id: ', chat_id,
          'notification_for_user_today: ', notification_for_user_today)

    if notification_for_user_today == 0:
        if error_message:
            bot.send_message(chat_id=chat_id, text="У вас в Spreadsheet есть ошибки: " + error_message)
        send_today(bot, username, chat_id, True)
        # bot.send_message(chat_id=update.message.chat_id, text="let's work with it")


@timed
def callback_send_notifications_morning(bot, job):
    if User.select().count() == 0:
        logger_print_info('no rows in User. return')
        return

    error_message = refresh_gspread_and_bot_users()
    if error_message:
        logger_print_info(error_message)

    users = list(User.select())
    logger_print_info('users: ', users)
    for u in users:
        logger_print_info(u, u.username, u.chat_id)
        send_notifications_per_user(bot, u, error_message)


@timed
def command_manual_check(bot, update):
    if User.select().count() == 0:
        logger_print_info('no rows in User. return')
        return

    error_message = refresh_gspread_and_bot_users()
    if error_message:
        logger_print_info(error_message)

    users_me = list(User.select().where(User.username == 'stoyanovd'))
    logger_print_info('users_me: ', users_me)
    for u in users_me:
        logger_print_info(u, u.username, u.chat_id)
        send_notifications_per_user(bot, u, error_message)


@timed
def command_echo(bot, update):
    # global d
    bot.send_message(chat_id=update.message.chat_id, text="let's work with it")

    msg = update.message.text
    logger_print_info(msg)

    bot.send_message(chat_id=update.message.chat_id, text='rr')


@timed
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
    dispatcher.add_handler(T.CommandHandler('debug', command_debug))
    dispatcher.add_handler(T.CommandHandler('manual_check', command_manual_check))

    # dispatcher.add_handler(T.MessageHandler(T.Filters.text, command_echo))

    j = updater.job_queue
    job_interval = 60 * 10
    # job_interval = 60
    job_for_check = j.run_repeating(callback_send_notifications_morning, interval=job_interval, first=20)

    logger_print_info("finish set up bot.")

    ########################
    # False for webhooks - i.e. work on Heroku,
    # True for polling, i.e. work from local computer

    # use_polling = False
    use_polling = True
    if use_polling:
        updater.start_polling()
    else:
        updater.start_webhook(listen="0.0.0.0",
                              port=PORT,
                              url_path="" + TELEGRAM_BOT_TOKEN)
        updater.bot.set_webhook(BOT_WEBHOOK_URL + TELEGRAM_BOT_TOKEN)

    logger_print_info("before idle")
    updater.idle()
    logger_print_info("after idle")


#################################################
if __name__ == '__main__':
    main()
