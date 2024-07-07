import os
import argparse
import requests
from dotenv import load_dotenv
from telegram import Bot


def get_response(url, headers, params):
    response = requests.get(url, headers=headers, params=params, timeout=60)
    response.raise_for_status()
    return response.json()


def send_message(chat_id, message):
    bot = Bot(token=os.getenv('TOKEN_TG'))
    bot.send_message(chat_id=chat_id, text=message)
    

if __name__ == '__main__':
    load_dotenv()
    token_devman = os.getenv('TOKEN_DEVMAN')

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
        'Authorization': f'Token {token_devman}'
    }
    url = 'https://dvmn.org/api/long_polling/'

    timestamp = None

    while True:
        try:
            params = {'timestamp': timestamp} if timestamp else {}
            result = get_response(url, headers, params)
            timestamp = result.get('timestamp_to_request', None)

            if result.get('status') == 'found':
                for attempt in result.get('new_attempts', []):
                    lesson_title = attempt.get('lesson_title')
                    is_negative = attempt.get('is_negative')
                    lesson_url = attempt.get('lesson_url')
                    message = f'У вас проверили работу "{lesson_title}"!\n'
                    message += 'К сожалению, в работе нашлись ошибки.' if is_negative else 'Ваша работа принята без ошибок!'
                    message += f'\n\n{lesson_url}'
                    send_message(args.chat_id, message)

        except requests.exceptions.ReadTimeout:
            print('Ошибка чтения')
        except requests.exceptions.ConnectionError:
            print('Нет соединения с сайтом')
