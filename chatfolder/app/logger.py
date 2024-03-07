# logger.py
import logging
from logging.handlers import RotatingFileHandler
import os

def setup_chatroom_logger(chatroom_id):
    # Перевіряємо чи існує директорія для логів, якщо немає - створюємо
    log_directory = os.path.join(os.getcwd(), 'chatroom_logs')
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    # Шлях до файлу лога для данного чатрума
    log_file = os.path.join(log_directory, f"chatroom_{chatroom_id}.log")

    # Створюємо логгер з ім'ям, що відповідає ідентифікатору чату
    logger = logging.getLogger(f"chatroom_{chatroom_id}")
    logger.setLevel(logging.INFO)

    # Якщо у логгера немає обробників, додаємо їх
    if not logger.handlers:
        # Створюємо обробник, який писатиме логи у файл із ротацією
        file_handler = RotatingFileHandler(log_file, maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        logger.addHandler(file_handler)

    return logger
