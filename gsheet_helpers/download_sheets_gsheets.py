import os

SCOPES = 'https://www.googleapis.com/auth/drive.readonly'

from secure.local_path import secure_path

from gsheets import Sheets


def download_sheets(spreadsheet_id, csv_dir, sheet_names_ids):
    secrets_file = os.path.join(secure_path, 'client_secrets.json')
    credentials_file = os.path.join(secure_path, 'credentials.json')
    sheets_conn = Sheets.from_files(secrets_file, credentials_file)

    spreadsheet = sheets_conn[spreadsheet_id]
    print(spreadsheet)
    print(spreadsheet.sheets)

    print(sheet_names_ids)
    my_sheets = {
        sheet_name: spreadsheet[sheet_id] for sheet_name, sheet_id in sheet_names_ids.items()
    }
    print(my_sheets)

    csv_pathes = {
        sheet_name: os.path.join(csv_dir, sheet_name + '.csv')
        for sheet_name, sheet_obj in my_sheets.items()
    }

    # dump to csv
    for sheet_name, sheet_obj in my_sheets.items():
        sheet_obj.to_csv(csv_pathes[sheet_name],
                         encoding='utf-8', dialect='excel')

    return csv_pathes
