import psutil
import os
import sys


def get_memory_usage():
    process = psutil.Process()
    print(f"🔍 Использование памяти: {process.memory_info().rss / 1024 / 1024:.2f} MB")
    return f"🔍 Использование памяти: {process.memory_info().rss / 1024 / 1024:.2f} MB"


def check_memory_limit(service, http_auth):
    process = psutil.Process(os.getpid())
    mem_usage = process.memory_info().rss / 1024 / 1024  # MB
    print(f"🔍 Использование памяти: {mem_usage:.2f} MB")

    if mem_usage > 300:
        print("⚠️ Память превышает 300 MB, перезапуск...")
        os.execv(sys.executable, ['python'] + sys.argv)
          # Перезапускаем процесс