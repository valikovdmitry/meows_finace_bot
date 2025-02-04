from oauth2client.service_account import ServiceAccountCredentials
import httplib2
import apiclient.discovery
from config import CREDENTIALS_FILE
from utilities.memory_manager import get_memory_usage


def get_service():
    print('---------- На старте программы ----------')
    get_memory_usage()
    print(f'\n')

    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        CREDENTIALS_FILE,
        ['https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'])

    http_auth = credentials.authorize(httplib2.Http(disable_ssl_certificate_validation=True, cache=None))

    service = apiclient.discovery.build('sheets', 'v4', http=http_auth, cache_discovery=False)

    return service, http_auth