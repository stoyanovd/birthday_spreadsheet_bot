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
    print(users)


if __name__ == '__main__':
    main()
