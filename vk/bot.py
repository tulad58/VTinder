import json
import re
from random import randrange, choice

import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType

from core.config import settings
from db.crud import user as session
from vk.api import VK
from vk.assets import calculate_age, keyboard_gen


class VkBot:
    def __init__(self, access_token):
        self.vk = vk_api.VkApi(token=access_token)
        self.long_poll = VkLongPoll(self.vk)
        self.text_commands = ['привет', '❤️', '👎', '➡️', 'избранные', 'выход', 'setting']
        self.stack_founded_profiles = dict()

    def start(self):
        for event in self.long_poll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                self.request_handler(event)

    def request_handler(self, event):
        vk_session = VK(access_token=settings.VK_USER_TOKEN)
        event_text = event.text.lower()
        if event_text in self.text_commands or 'setting' in event_text:
            if 'payload' in event.raw[6]:
                self.payload_handler(vk_session, event)
            else:
                self.text_handler(vk_session, event)
        else:
            # Тут напрашивается "или нажмите кнопку 🔎" и сама кнопка
            self.send_msg(event.user_id, 'Напишите: "Привет" и я попробую найти для вас пару')

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

    def text_handler(self, vk_session, event):
        current_user = vk_session.get_users_info(user_ids=event.user_id)[0]
        # TEST EXAMPLE
        # current_user = {'id': 1, 'sex': 2}
        current_user = self.check_user_info(event, current_user, vk_session)
        current_user_bdate = current_user.get('bdate')
        if current_user_bdate:
            is_new = self.add_new_user(current_user)
            age_from = calculate_age(current_user_bdate) - 5 if current_user['sex'] == 1 else calculate_age(
                current_user_bdate)
            age_to = calculate_age(current_user_bdate) if current_user['sex'] == 1 else calculate_age(
                current_user_bdate) + 5

            # Что-то тут делаю не правильно self.stack_founded_profiles не меняется при next команде, то не работает
            if not self.stack_founded_profiles.get(f'current_user["id"]'):
                founded_profiles = vk_session.search_users(
                    sex=current_user['sex'],
                    city_id=current_user['city']['id'],
                    age_from=age_from,
                    age_to=age_to
                )
                # добавляем полученных пользователей в stack
                self.stack_founded_profiles[current_user['id']] = founded_profiles
            profile = self.stack_founded_profiles[current_user['id']].pop(0)
            self.response_handler(vk_session, event, profile, current_user)

    def payload_handler(self, vk_session, event):
        command_obj = json.loads(event.payload)
        command = command_obj.get('command')
        current_user_id = command_obj.get("current_user")
        founded_profile_id = command_obj.get("founded_profile")
        if command == 'like':
            self.add_to_favorites(current_user_id, founded_profile_id)
            self.send_msg(send_id=event.user_id,
                          message=f'Пользователь id{founded_profile_id} добавлен в ⭐ Избранное')
        elif command == 'dislike':
            self.add_to_blacklist(current_user_id, founded_profile_id)
            self.send_msg(send_id=event.user_id,
                          message=f'Пользователь id{founded_profile_id} добавлен в 👎 Чёрный список')
        elif command == 'next':
            self.text_handler(vk_session, event)
        elif command == 'favorites':
            fav = self.get_favorites(current_user_id)
            self.send_msg(send_id=event.user_id, message=fav)
        elif command == 'exit':
            self.send_msg(send_id=event.user_id, message='👋Возвращайся еще')
        # Возможно убрать else, так как левых command, которые мы не создали в payload не будет
        else:
            command = None

    def response_handler(self, vk_session, event, profile, current_user):

        message_pack = settings.bot_massages_for_male if current_user[
                                                             'sex'] == 2 else settings.bot_massages_for_female

        if self.already_viewed(current_user['id'], profile['id']):
            # функция запроса нового пользователя из self.stack_founded_profiles[current_user['id']]
            pass
        message = f'{choice(message_pack)} \n' \
                  f'{profile.get("first_name")} {profile.get("last_name")}.\n' \
                  f'Ссылка: https://vk.com/{profile.get("domain")}'
        photo_attachments = vk_session.get_photos(owner_id=profile['id'])
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

        self.vk.method('messages.send', {'user_id': send_id,
                                         'message': message,
                                         'random_id': randrange(10 ** 7),
                                         'attachment': attachments,
                                         'keyboard': keyboard,
                                         'payload': payload
                                         })

    def add_to_favorites(self, user_vk_id: int = None, profile_vk_id: int = None):
        # нужно добавить:
        # сохранение ссылок на профиль, чтобы возвращать в get_favorites
        # параметр favor - boolean если like то True, Черный список - False
        if user_vk_id and profile_vk_id:
            return session.add_favorite(user_vk_id, profile_vk_id)
        raise ValueError('Problem with vk_id')

    def add_to_blacklist(self, user_vk_id: int = None, profile_vk_id: int = None):
        if user_vk_id and profile_vk_id:
            return session.add_to_blacklist(user_vk_id, profile_vk_id)
        raise ValueError('Problem with vk_id')

    def get_favorites(self, user_id):
        '''
        Функция возвращает список строк favorites текущего пользователя:
        Структура: ФИО -- Возраст -- Город -- Ссылка
        :return:
        '''
        favorites = session.get_favorites(user_id)
        if not favorites:
            return 'Избранных пока нету'
        verbose_favorites = 'Твои избранные: \n'
        for i, profile in enumerate(favorites, start=1):
            verbose_favorites += f'{i}. {str(profile.profile_id)}\n'
        return verbose_favorites

    def already_viewed(self, user_id, profile_id) -> bool:
        '''
        Эта функция проверяет есть ли пользователь в каких либо списках у текущего пользователя
        :param user:
        :return:
        '''
        return session.exist_in_user_lists(user_id, profile_id)

    def add_new_user(self, user) -> bool:
        '''
        Функция принимает пользователя, проверяет есть ли он в БД,
        Добавляет если его нет и возвращает True, иначе False
        '''

        user_vk_id = user.get('id')
        return session.get_or_create_user(user_vk_id)
