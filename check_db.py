import datetime
import json
import os
import yaml
import logging

from telegram import ext as T
import peewee as P
from playhouse.db_url import connect

from goes import db_init, BaseModel, User, Notification

# BD_DATABASE = connect(os.environ['DATABASE_URL'])

# db_init()


def main():
    print('====================')
    users = User.select().count()
    users = User.select()
    print(users)

    for u in users:
        notification_for_user_today = Notification.select().join(User).where(
            (User.username == u.username) &
            (Notification.created_date >= datetime.date.today()) &
            (Notification.is_auto_notification == True)
        ).count()
        print(u .username, notification_for_user_today)

if __name__ == '__main__':
    main()
