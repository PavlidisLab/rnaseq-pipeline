import argparse
import logging
import os
import os.path
import pickle
import sys
from os.path import dirname, expanduser, join

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import luigi
import pandas as pd
import xdg.BaseDirectory

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

logger = logging.getLogger('luigi-interface')

def _authenticate():
    # authentication
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    token_path = join(xdg.BaseDirectory.save_data_path('pavlab-rnaseq-pipeline'), 'token.pickle')
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_console()
        # Save the credentials for the next run
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
            logger.info(f'Created Google Sheets API token under {token_path}.')
    return creds

def retrieve_spreadsheet(spreadsheet_id, sheet_name):
    service = build('sheets', 'v4', credentials=_authenticate(), cache_discovery=None)

    # Retrieve the documents contents from the Docs service.
    rnaseq_pipeline_queue = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=sheet_name).execute()

    # this will fail if people add new columns
    df = pd.DataFrame(rnaseq_pipeline_queue['values'][1:], columns=rnaseq_pipeline_queue['values'][0]+list(range(2)))

    # type adjustment
    df['priority'] = df.priority.fillna(0).replace('', '0').astype('int')

    return df
