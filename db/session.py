import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from core.config import settings
from .models import Base


class DBHandler:

    def __init__(self):
        self.Session = None

    @staticmethod
    def create_db():
        connection = psycopg2.connect(user=settings.DB_USER, password=settings.DB_PASSWORD)
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

        cursor = connection.cursor()
        try:
            cursor.execute(f"SELECT 1 FROM pg_database WHERE datname='{settings.DB_NAME}'")
            exists = cursor.fetchone()
            if not exists:
                cursor.execute(f"CREATE DATABASE {settings.DB_NAME}")
                print(f"База данных '{settings.DB_NAME}' успешно создана.")
        except psycopg2.Error as e:
            print("Ошибка при проверке наличия базы данных:", e)
        finally:
            cursor.close()
            connection.close()

    def connect(self):
        self.create_db()
        try:
            engine = create_engine(settings.DATABASE_URL)
            Base.metadata.create_all(engine)
            self.Session = sessionmaker(bind=engine)
            session = self.Session()
            return session
        except SQLAlchemyError as error:
            print("Ошибка подключения к базе данных:")
            raise error


db = DBHandler()
session = db.connect()
