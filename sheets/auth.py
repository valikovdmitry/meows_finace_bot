from oauth2client.service_account import ServiceAccountCredentials
import httplib2
import apiclient.discovery
from config import CREDENTIALS_FILE


def get_service():
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        CREDENTIALS_FILE,
        ['https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'])

    http_auth = credentials.authorize(httplib2.Http())

    service = apiclient.discovery.build('sheets', 'v4', http=http_auth)

    return service, http_auth

get_service()