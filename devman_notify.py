import os
import time
import argparse
import requests
from dotenv import load_dotenv
from telegram import Bot


if __name__ == '__main__':
    load_dotenv()
    devman_token = os.getenv('DEVMAN_TOKEN')
    bot = Bot(token=os.getenv('TOKEN_TG'))

    parser = argparse.ArgumentParser(
        description='Скрипт запрашивает данные у Devman о свежих проверенных работах ученика'
                    'И сообщает о результатах проверки ученику в созданный им телеграм бот')
    parser.add_argument(
        '--chat_id',
        type=int,
        required=True,
        help='Идентификатор пользователя в телеграм'
    )
    args = parser.parse_args()

    headers = {
        'Authorization': f'Token {devman_token}'
    }
    url = 'https://dvmn.org/api/long_polling/'

    timestamp = None

    while True:
        try:
            params = {'timestamp': timestamp} if timestamp else {}
            response = requests.get(url, headers=headers, params=params, timeout=60)
            response.raise_for_status()
            notify = response.json()
            timestamp = notify.get('timestamp_to_request', None)

            if notify.get('status') == 'found':
                for attempt in notify.get('new_attempts', []):
                    lesson_title = attempt.get('lesson_title')
                    is_negative = attempt.get('is_negative')
                    lesson_url = attempt.get('lesson_url')
                    message = f'У вас проверили работу "{lesson_title}"!\n'
                    message += 'К сожалению, в работе нашлись ошибки.' if is_negative else 'Ваша работа принята без ошибок!'
                    message += f'\n\n{lesson_url}'
                    bot.send_message(chat_id=args.chat_id, text=message)

        except requests.exceptions.ReadTimeout:
            continue
        except requests.exceptions.ConnectionError:
            time.sleep(5)
