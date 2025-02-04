from tg_bot import main
from sheets.auth import get_service
from bot.handlers.update import update_self

from utilities.memory_manager import get_memory_usage
from sheets.sheets_manager import test_transaction_stream


if __name__ == "__main__":
    service, http_auth = get_service()

    update_self(service, http_auth)

    #test_transaction_stream(service, http_auth)

    main(service, http_auth)