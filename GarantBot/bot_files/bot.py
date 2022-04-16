from aiogram.bot import Bot
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from bot_files.config import *
from handlers import handlers
import sqlite3
import datetime


# bot settings
bot = Bot(token=token)
dispatcher = Dispatcher(bot=bot)

# database settings
con = sqlite3.connect(
    'database.db'
)
cur = con.cursor()


# create tables
try:
    cur.execute(
        f'CREATE TABLE users ('
        f'user_id UNIQUE,'
        f'state INT,'
        f'balance INT,'
        f'free_tasks_count INT,'
        f'deal_id INT'
        f');'
    )
    cur.execute(
        f'CREATE TABLE tasks ('
        f'id INTEGER PRIMARY KEY AUTOINCREMENT,'
        f'is_confirmed INT,'
        f'task_text TEXT,'
        f'customer_id INT,'
        f'executor_id INT,'
        f'sum INT,'
        f'date_of_creation TEXT,'
        f'date_of_ending TEXT,'
        f'balance INT'
        f');'
    )
    cur.execute(
        f'CREATE TABLE payments ('
        f'id INTEGER PRIMARY KEY AUTOINCREMENT,'
        f'user_id INT,'
        f'sum INT,'
        f'payment_code TEXT,'
        f'status INT,'
        f'date TEXT,'
        f'type TEXT'
        f');'
    )
    con.commit()
except sqlite3.OperationalError:
    print('# RUN')

# register handlers and run bot
if __name__ == '__main__':
    # register handlers
    dispatcher.register_message_handler(
        handlers.get_user_id_handler,
        commands=['myid']
    )

    dispatcher.register_message_handler(
        handlers.start_message_handler,
        commands=['start']
    )
    dispatcher.register_message_handler(
        handlers.other_messages_handler
    )

    dispatcher.register_callback_query_handler(
        handlers.callback_handler
    )

    # run bot
    executor.start_polling(dispatcher=dispatcher)
