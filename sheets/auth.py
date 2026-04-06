from oauth2client.service_account import ServiceAccountCredentials
import httplib2
import apiclient.discovery
import threading
from config import CREDENTIALS_FILE


_thread_local = threading.local()


def _build_service():
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        CREDENTIALS_FILE,
        [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ],
    )

    # Keep one authorized HTTP transport per worker thread.
    http_auth = credentials.authorize(httplib2.Http(timeout=10))
    service = apiclient.discovery.build(
        "sheets",
        "v4",
        http=http_auth,
        cache_discovery=False,
    )
    return service, http_auth


def get_service():
    service = getattr(_thread_local, "service", None)
    if service is None:
        service, http_auth = _build_service()
        _thread_local.service = service
        _thread_local.http_auth = http_auth
    return _thread_local.service
