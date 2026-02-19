from tg_bot import main
from bot.handlers.update import update_self

if __name__ == "__main__":
    try:
        update_self()
    except Exception as exc:
        print(f"Не удалось обновить категории при старте: {exc}")
    main()
