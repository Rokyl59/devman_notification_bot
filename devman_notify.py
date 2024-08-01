import os
import time
import requests
from dotenv import load_dotenv
from telegram import Bot
import logging


class TelegramLogsHandler(logging.Handler):
    def __init__(self, bot, chat_id):
        super().__init__()
        self.bot = bot
        self.chat_id = chat_id

    def emit(self, record):
        log_entry = self.format(record)
        self.bot.send_message(chat_id=self.chat_id, text=log_entry)


def main():
    load_dotenv()
    devman_token = os.getenv('DEVMAN_TOKEN')
    bot = Bot(token=os.getenv('TOKEN_TG'))
    chat_id = os.getenv('CHAT_ID')

    logger = logging.getLogger('TelegramLogger')
    logger.setLevel(logging.ERROR)
    handler = TelegramLogsHandler(bot, chat_id)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    headers = {
        'Authorization': f'Token {devman_token}'
    }
    url = 'https://dvmn.org/api/long_polling/'

    timestamp = None

    while True:
        try:
            params = {'timestamp': timestamp} if timestamp else {}
            response = requests.get(url, headers=headers, params=params, timeout=90)
            response.raise_for_status()
            notification = response.json()

            if notification.get('status') == 'found':
                for attempt in notification.get('new_attempts', []):
                    lesson_title = attempt.get('lesson_title')
                    is_negative = attempt.get('is_negative')
                    lesson_url = attempt.get('lesson_url')
                    message = f'У вас проверили работу "{lesson_title}"!\n'
                    message += 'К сожалению, в работе нашлись ошибки.' if is_negative else 'Ваша работа принята без ошибок!'
                    message += f'\n\n{lesson_url}'
                    bot.send_message(chat_id=chat_id, text=message)

            timestamp = notification.get('timestamp_to_request', notification.get('last_attempt_timestamp', timestamp))

        except requests.exceptions.ReadTimeout:
            continue
        except requests.exceptions.ConnectionError:
            time.sleep(5)
        except Exception as e:
            logger.error("Ошибка в основном цикле", exc_info=e)


if __name__ == '__main__':
    main()
