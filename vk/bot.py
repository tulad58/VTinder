import json
import re
from random import randrange, choice

import vk_api.exceptions
from vk_api.longpoll import VkLongPoll, VkEventType

from core.config import settings
from db.crud import db
from vk.api import VkUserSession
from vk.assets import calculate_age, keyboard_gen
from vk.base import VKBase


class VkBot(VKBase):
    def __init__(self, access_token, version=settings.VK_API_VERSION):
        super().__init__(access_token, version)
        self.long_poll = VkLongPoll(self.vk)
        self.text_commands = settings.bot_commands
        self.stack_founded_profiles = dict()
        self.user_sessions = dict()

    def start(self):
        for event in self.long_poll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                user_session = self.get_or_create_session(event)
                self.request_handler(user_session, event)

    def get_or_create_session(self, event):
        current_user = self.get_users_info(user_ids=event.user_id)[0]
        if current_user['id'] in self.user_sessions:
            return self.user_sessions.get(current_user['id'])
        new_session = VkUserSession(user_access_token=settings.VK_USER_TOKEN)
        # Метод get.user с токеном группы не возращает полные данные по дате рождения поэтому берем еще раз от имени пользователя
        current_user = new_session.get_users_info(user_ids=event.user_id)[0]
        new_session.set_db_user(db.get_or_create_user(current_user['id']))
        new_session.set_user(current_user)
        self.user_sessions[current_user['id']] = new_session
        return new_session

    def request_handler(self, user_session: VkUserSession, event):
        event_text = event.text.lower()
        if event_text in self.text_commands or 'setting' in event_text:
            if 'payload' in event.raw[6]:
                self.payload_handler(user_session, event)
            else:
                self.text_handler(user_session, event)
        else:
            self.send_msg(event.user_id, f'Напишите: "Привет" и я попробую найти для вас пару {event_text}')

    def text_handler(self, user_session: VkUserSession, event, next=None):
        if next:
            user_session.increase_pop()
        current_user = user_session.user
        # TEST EXAMPLE
        # current_user = {'id': 1, 'sex': 2}
        current_user = self.check_user_info(event, current_user, user_session)
        current_user_bdate = current_user.get('bdate')
        if current_user_bdate:
            age_from = calculate_age(current_user_bdate) - 5 if current_user['sex'] == 2 else calculate_age(
                current_user_bdate)
            age_to = calculate_age(current_user_bdate) if current_user['sex'] == 2 else calculate_age(
                current_user_bdate) + 5

            if not self.stack_founded_profiles.get(current_user["id"]):
                founded_profiles = user_session.search_users(
                    sex=current_user['sex'],
                    city_id=current_user['city']['id'],
                    age_from=age_from,
                    age_to=age_to
                )
                self.stack_founded_profiles[current_user['id']] = founded_profiles
            self.response_handler(user_session, event, current_user)

    def payload_handler(self, user_session: VkUserSession, event):
        command_obj = json.loads(event.payload)
        command = command_obj.get('command')
        founded_profile_id = command_obj.get("founded_profile")
        if command == 'like':
            is_added = self.add_to_favorites(user_session.db_user, founded_profile_id)
            if is_added:
                self.send_msg(send_id=event.user_id,
                              message=f'Пользователь id{founded_profile_id} добавлен в ⭐ Избранное')
            self.text_handler(user_session, event)
        elif command == 'dislike':
            is_added = self.add_to_blacklist(user_session.db_user, founded_profile_id)
            if is_added:
                self.send_msg(send_id=event.user_id,
                              message=f'Пользователь id{founded_profile_id} добавлен в 👎 Чёрный список')
            self.text_handler(user_session, event)
        elif command == 'next':
            self.text_handler(user_session, event, next=True)
        elif command == 'favorites':
            fav = self.get_favorites(user_session.db_user)
            self.send_msg(send_id=event.user_id, message=fav)
        elif command == 'exit':
            self.send_msg(send_id=event.user_id, message='👋Возвращайся еще')

    def response_handler(self, user_session, event, current_user):

        message_pack = settings.male_msgs if current_user['sex'] == 2 else settings.female_msgs
        print(self.stack_founded_profiles[current_user['id']][0]['id'])
        while True:
            profile = self.stack_founded_profiles[current_user['id']].pop(user_session.pop)
            if self.already_viewed(user_session.db_user, profile['id']):
                continue
            break

        message = f'{choice(message_pack)} \n' \
                  f'{profile.get("first_name")} {profile.get("last_name")}.\n' \
                  f'Ссылка: https://vk.com/{profile.get("domain")}'
        photo_attachments = user_session.get_photos(owner_id=profile['id'])
        if photo_attachments is None:
            message += f'\nФото недоступно - приватный профиль пользователя'
        vk_keyboard = keyboard_gen(event, profile)
        self.send_msg(send_id=event.user_id, message=message, attachments=photo_attachments,
                      keyboard=vk_keyboard)

    def send_msg(self, send_id, message, attachments=None, keyboard=None, payload=None):
        """
        Отправка сообщения через метод messages.send
        :param send_id: vk id пользователя, который получит сообщение
        :param message: содержимое отправляемого сообщения
        :param attachments: строка с фото контентом отправляемого сообщения
        :param keyboard: объект кнопок VkKeyboard
        :return: None
        """
        try:
            self.vk.method('messages.send', {'user_id': send_id,
                                             'message': message,
                                             'random_id': randrange(10 ** 7),
                                             'attachment': attachments,
                                             'keyboard': keyboard,
                                             'payload': payload
                                             })
        except vk_api.exceptions.ApiError as error:
            print('Ошибка отправки сообщения: ', error)

    def add_to_favorites(self, db_user, profile_vk_id: int = None):
        # нужно добавить:
        # сохранение ссылок на профиль, чтобы возвращать в get_favorites
        # параметр favor - boolean если like то True, Черный список - False
        if db_user and profile_vk_id:
            return db.add_favorite(db_user, profile_vk_id)
        raise ValueError('Problem with vk_id')

    def add_to_blacklist(self, db_user, profile_vk_id: int = None):
        if db_user and profile_vk_id:
            return db.add_to_blacklist(db_user, profile_vk_id)
        raise ValueError('Problem with vk_id')

    def get_favorites(self, user_id):
        '''
        Функция возвращает список строк favorites текущего пользователя:
        Структура: ФИО -- Возраст -- Город -- Ссылка
        :return:
        '''
        favorites = db.get_favorites(user_id)
        if not favorites:
            return 'Избранных пока нету'
        verbose_favorites = 'Твои избранные: \n'
        for i, profile in enumerate(favorites, start=1):
            verbose_favorites += f'{i}. {str(profile.profile_id)}\n'
        return verbose_favorites

    def already_viewed(self, db_user, profile_id) -> bool:
        '''
        Эта функция проверяет есть ли пользователь в каких либо списках у текущего пользователя
        :param user:
        :return:
        '''
        return db.exist_in_user_lists(db_user, profile_id)

    def add_new_user(self, user) -> bool:
        '''
        Функция принимает пользователя, проверяет есть ли он в БД,
        Добавляет если его нет и возвращает True, иначе False
        '''

        user_vk_id = user.get('id')
        return db.get_or_create_user(user_vk_id)

    def check_user_info(self, event, current_user, vk_session):
        if not current_user.get('bdate'):
            if 'setting' in event.text:
                setting = re.findall(r'-\s*(\d{2}.\d{2}.\d{4})\s*-\s*(\S+)', event.text)[0]
                current_user['bdate'] = setting[0]
                current_user['city'] = vk_session.get_city(setting[1])
                msg = f'Получены настройки:\n ' \
                      f'Дата рождения - {current_user["bdate"]},\n ' \
                      f'Город поиска - {current_user["city"]["title"]}'
                payload = '{\"command\":\"setting\"}'
                self.send_msg(send_id=event.user_id, message=msg, payload=payload)
            else:
                msg = 'Не удается получить данные пользователя😔\n' \
                      'Введи команду setting с указанием даты рождения и города.\n' \
                      'Пример, setting - 01.01.1990 - Москва'
                self.send_msg(send_id=event.user_id, message=msg)

        return current_user
