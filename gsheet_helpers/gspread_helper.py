import json
import os
from oauth2client.service_account import ServiceAccountCredentials
import datetime

from bd_const.month_names import MONTHES_DICT

SCOPES = 'https://www.googleapis.com/auth/drive.readonly'
# SCOPES = 'https://www.googleapis.com/auth/drive'
# SCOPES = ['https://spreadsheets.google.com/feeds',
#          'https://www.googleapis.com/auth/drive']

import gspread
from bd_const import env_variables as BD
import calendar
import pandas as pd
import numpy as np

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding = 'utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding = 'utf-8')

def download_sheets():
    credentials_json = os.environ.get(BD.BD_BOT_SERVICE_ACCOUNT_CREDENTIALS)
    # print(credentials_json)
    credentials = json.loads(credentials_json)
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials, scopes=SCOPES)

    gc = gspread.authorize(credentials)
    spreadsheet = os.environ.get(BD.BD_BOT_STIL_SPREADSHEET_ID)
    wks = gc.open_by_key(spreadsheet).sheet1

    cell_list = wks.get_all_values()
    print(type(cell_list))

    print(type(cell_list[0]))

    return cell_list


def check_spreadsheet_errors(cell_list, header_rows):
    well_formed_cell_list = []
    cell_list = cell_list[1:]
    error_message = ''
    for i in range(len(cell_list)):
        row = cell_list[i]
        row = row[:3]
        c = len(error_message)
        if len(row) < 3:
            error_message += os.linesep + 'Строка ' + str(i + 1 + header_rows) + '. Не заполнена целиком.'
        if row[0] == '' and row[1] == '' and row[2] == '':
            continue
        if row[0].lower() not in MONTHES_DICT:
            error_message += os.linesep + 'Строка ' + str(i + 1 + header_rows) + '. Месяц не корректен.'
            if row[2] is not None and len(row[2]) > 0:
                error_message += ' Поэтому мы не знаем, когда поздравлять: ' + row[2] + '.'
            error_message += ' Дозаполните, пожалуйста, данные!'
        if not row[1].isdigit():
            error_message += os.linesep + 'Строка ' + str(i + 1 + header_rows) + '. День месяца не корректен.'
            if row[2] is not None and len(row[2]) > 0:
                error_message += ' Поэтому мы не знаем, когда поздравлять: ' + row[2] + '.'
            error_message += ' Дозаполните, пожалуйста, данные!'
        if len(row[2]) == 0:
            error_message += os.linesep + 'Строка ' + str(i + 1 + header_rows) + '. Именинник не заполнен.'
            error_message += ' Дозаполните, пожалуйста, данные!'

        if len(error_message) == c:
            well_formed_cell_list += [row]

    return well_formed_cell_list, error_message


def pandas_conversion(cell_list):
    # don't use pandas from start because I need per-row error checking
    df = pd.DataFrame(cell_list, columns=['month', 'day', 'person'])
    df['month'] = df['month'].str.lower()
    df['month_int'] = df['month'].map(MONTHES_DICT).astype(np.int)
    df['day'] = df['day'].astype(np.int)
    current_year = int(datetime.datetime.now().year)
    df['bd_date'] = pd.to_datetime(
        current_year * 10000 +
        df['month_int'] * 100 +
        df['day'],
        format='%Y%m%d')
    return df


def get_dates_persons_df():
    cell_list = download_sheets()
    print(str(cell_list)[:50])
    # use pandas only after per-row error checking
    well_formed_cell_list, error_message = check_spreadsheet_errors(cell_list, header_rows=1)

    df = pandas_conversion(well_formed_cell_list)
    return df, error_message
