from environs import Env

ENV = Env()
ENV.read_env()


class Settings:
    PROJECT_NAME: str = "VKinter"
    PROJECT_VERSION: str = "0.1.1"

    DB_USER = ENV('db_user')
    DB_PASSWORD = ENV('db_password')
    DB_HOST = ENV('db_host')
    DB_PORT = ENV('db_port')
    DB_NAME = ENV('db_name')
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    VK_USER_TOKEN = ENV('vk_user_token')
    VK_CLIENT_ID = ENV('vk_client_id')
    VK_BOT_TOKEN = ENV('vk_bot_token')
    VK_API_VERSION = ENV('vk_api_version')

    male_msgs = (
        'Как тебе такой вариант?',
        'Может она?',
        'А как тебе эта?',
        'Вот эта точно должна подойти?',
        'Не, ну эта то ничего вроде?',
        'Лучше не будет, выбирай)'
    )

    female_msgs = (
        'Как тебе такой вариант?',
        'Может он?',
        'А как тебе этот?',
        'Вот этот точно должна подойти?',
        'Не, ну этот мужик то ничего вроде?',
        'Лучше не будет, выбирай)'
    )

    request_fields = 'about, activities, bdate, books, can_send_friend_request, can_write_private_message, city, ' \
                     'domain, interests, lists, music, photo_max_orig, quotes, relation, screen_name, sex'

    bot_commands = ['привет', '❤️', '👎', '➡️', 'избранные', 'выход', 'setting', 'token']


settings = Settings()
