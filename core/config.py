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


settings = Settings()
