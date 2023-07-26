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
        self.btn_text = ['❤️', '👎', '➡️', 'избранные', 'выход']

    def start(self):
        for event in self.long_poll.listen():
            if event.type == VkEventType.MESSAGE_NEW:
                if event.to_me:
                    self.request_handler(event)

    def request_handler(self, event):

        if 'payload' in event.raw[6]:
            self.payload_handler(event)
        self.text_handler(event)

    def check_user_info(self, event, current_user, vk_session):
        if not current_user.get('bdate'):
            if 'setting' in event.text:
                setting = re.findall(r'-\s*(\d{2}.\d{2}.\d{4})\s*-\s*(\S+)', event.text)[0]
                current_user['bdate'] = setting[0]
                current_user['city'] = vk_session.get_city(setting[1])
                msg = f'Получены настройки:\n Дата рождения - {setting[0]},\n Город поиска - {setting[1]}'
                payload = '{\"command\":\"setting\"}'
                self.send_msg(send_id=event.user_id, message=msg, payload=payload)
            else:
                msg = 'Не удается получить данные пользователя😔\n' \
                      'Введи команду setting с указанием даты рождения и города.\n' \
                      'Пример, setting - 01.01.1990 - Москва'
                self.send_msg(send_id=event.user_id, message=msg)

        return current_user

    def text_handler(self, event):
        request = event.text
        if request.lower() == 'привет' or 'setting' in request:  # or command == 'setting':
            vk_session = VK(access_token=settings.VK_USER_TOKEN)
            current_user = vk_session.get_users_info(user_ids=event.user_id)[0]
            current_user = self.check_user_info(event, current_user, vk_session)
            if current_user.get('bdate'):
                is_new = self.add_new_user(current_user)
                options = {
                    'age_from': 14,
                    'age_to': 80
                }
                user_age = current_user.get('bdate')

                if user_age:
                    options['age_from'] = calculate_age(user_age) - 5 if current_user['sex'] == 1 else calculate_age(
                        user_age)
                    options['age_to'] = calculate_age(user_age) if current_user['sex'] == 1 else calculate_age(
                        user_age) + 5

                founded_profiles = vk_session.search_users(
                    sex=current_user['sex'],
                    city_id=current_user['city']['id'],
                    age_from=options['age_from'],
                    age_to=options['age_to']
                )

                self.response_handler(vk_session, founded_profiles, current_user)

        elif request.lower() in self.btn_text:
            # Заглушка от получаемого текста кнопок
            pass
        else:
            self.send_msg(event.user_id, "Не поняла вашего ответа...")

    def payload_handler(self, event):
        command_obj = json.loads(event.payload)
        command = command_obj.get('command')
        current_user_vk_id = command_obj.get("current_user")
        founded_profile_vk_id = command_obj.get("founded_profile")
        if command == 'like':
            print(f'Пользователь {current_user_vk_id} ❤️ {founded_profile_vk_id}')
            self.add_to_favorites(current_user_vk_id, founded_profile_vk_id)
        elif command == 'dislike':
            print(f'Пользователь {current_user_vk_id} 👎 {founded_profile_vk_id}')
            self.add_to_blacklist(current_user_vk_id, founded_profile_vk_id)
        elif command == 'next':
            pass
        elif command == 'favorites':
            fav = self.get_favorites(current_user_vk_id)
            self.send_msg(send_id=event.user_id, message=fav)
        elif command == 'exit':
            self.send_msg(send_id=event.user_id, message='👋Возвращайся еще')
        else:
            command = None

    def response_handler(self, vk_session, event, founded_profiles, current_user):

        message_pack = settings.bot_massages_for_male if current_user[
                                                             'sex'] == 2 else settings.bot_massages_for_female

        for profile in founded_profiles:
            if self.already_viewed(current_user['id'], profile['id']):
                continue
            message = f"{choice(message_pack)} \n " \
                      f"{profile.get('first_name')} {profile.get('last_name')}. " \
                      f"\n Ссылка: http://www.vk.com/{profile.get('domain')}"

            photo_attachments = vk_session.get_photos(owner_id=profile['id'])

            vk_keyboard = keyboard_gen(event, profile)

            self.send_msg(send_id=event.user_id, message=message, attachments=photo_attachments,
                          keyboard=vk_keyboard)
            break

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
