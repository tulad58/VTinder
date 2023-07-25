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
    VK_BOT_TOKEN = ENV('vk_bot_token')
    VK_API_VERSION = ENV('vk_api_version')

    bot_massages_for_male = (
        'Как тебе такой вариант?',
        'Может она?',
        'А как тебе эта?',
        'Вот эта точно должна подойти?',
        'Не, ну эта то ничего вроде?',
        'Лучше не будет, выбирай)'
    )

    bot_massages_for_female = (
        'Как тебе такой вариант?',
        'Может он?',
        'А как тебе этот?',
        'Вот этот точно должна подойти?',
        'Не, ну этот мужик то ничего вроде?',
        'Лучше не будет, выбирай)'
    )


settings = Settings()
