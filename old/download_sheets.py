import apiclient.discovery
import httplib2
import oauth2client

import requests
import shutil
import urllib.parse
import os
import re


def make_csv_file_template(template_name):
    return  template_name + '-%s.csv'


SCOPES = 'https://www.googleapis.com/auth/drive.readonly'

from secure.local_path import secure_path


def download_sheets(spreadsheet_id, data_dir, name_for_csv_template):
    secrets_file = os.path.join(secure_path, 'client_secrets.json')
    credentials_file = os.path.join(secure_path, 'credentials.json')

    csv_files_template_local = os.path.join(data_dir, make_csv_file_template(name_for_csv_template))

    store = oauth2client.file.Storage(credentials_file)
    creds = store.get()
    if not creds or creds.invalid:
        flow = oauth2client.client.flow_from_clientsecrets(secrets_file, SCOPES)
        creds = oauth2client.tools.run_flow(flow, store)

    service = apiclient.discovery.build('sheets', 'v4', http=creds.authorize(httplib2.Http()))

    result = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    spreadsheetUrl = result['spreadsheetUrl']
    exportUrl = re.sub("\/edit$", '/export', spreadsheetUrl)
    headers = {
        'Authorization': 'Bearer ' + creds.access_token,
    }

    result_csv_files = []
    for sheet in result['sheets']:
        from time import sleep
        sleep(0.05)

        params = {
            'format': 'csv',
            'gid': sheet['properties']['sheetId'],
        }
        queryParams = urllib.parse.urlencode(params)
        url = exportUrl + '?' + queryParams
        response = requests.get(url, headers=headers)

        # unary plus - is some 'sheet' operator
        filePath = csv_files_template_local % (+ params['gid'])
        with open(filePath, 'wb') as csvFile:
            csvFile.write(response.content)
        result_csv_files += [filePath]

    return csv_files_template_local, result_csv_files
