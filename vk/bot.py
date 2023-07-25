import json
import re
from random import randrange, choice

import vk_api

from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkLongPoll, VkEventType

from core.config import settings
from vk.api import VK
from vk.assets import calculate_age


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
            command_obj = json.loads(event.payload)
            command = command_obj.get('command')
            if command == 'like':
                print(f'Пользователь {command_obj.get("current_user")} ❤️ {command_obj.get("founded_user")}')
                # Записываем в favorites
                self.add_to_favourites()
            elif command == 'dislike':
                print(f'Пользователь {command_obj.get("current_user")} 👎 {command_obj.get("founded_user")}')
                # Записываем в blacklist
                self.add_to_blacklist()
            elif command == 'next':
                pass
            elif command == 'favorites':
                self.get_favourites()
            elif command == 'exit':
                self.send_msg(send_id=event.user_id, message='👋Возвращайся еще')
        else:
            command = None

        request = event.text
        if request.lower() == 'привет' or 'setting' in request or command == 'setting':
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

                founded_users = vk_session.search_users(
                    sex=current_user['sex'],
                    city_id=current_user['city']['id'],
                    age_from=options['age_from'],
                    age_to=options['age_to']
                )
                message_pack = settings.bot_massages_for_male if current_user[
                                                                     'sex'] == 2 else settings.bot_massages_for_female

                for user in founded_users:
                    # ЗДЕСЬ ПРОВЕРЯЕМ ЕСТЬ ЛИ ПОЛЬЗОВАТЕЛЬ В СПИСКАХ (ИЗБРАННЫЕ ИЛИ БЛЭКЛИСТ) У ТЕКУЩЕГО ПОЛЬЗОВАТЕЛЯ
                    # ЕСЛИ ЕСТЬ ТО ПРОБУЕМ СЛЕДУЮЩЕГО ЕСЛИ НЕТ ТО РАБОТАЕМ ДАЛЬШЕ С НИМ
                    if self.already_viewed(user):
                        continue

                    message = f"{choice(message_pack)} \n " \
                              f"{user.get('first_name')} {user.get('last_name')}. " \
                              f"\n Ссылка: http://www.vk.com/{user.get('domain')}"

                    photo_attachments = vk_session.get_photos(owner_id=user['id'])

                    keyboard = VkKeyboard(one_time=False, inline=True)
                    keyboard.add_button('❤️', color=VkKeyboardColor.SECONDARY,
                                        payload={'command': 'like',
                                                 'current_user': event.user_id,
                                                 'founded_user': user['id']})
                    keyboard.add_button('👎', color=VkKeyboardColor.SECONDARY,
                                        payload={'command': 'dislike',
                                                 'current_user': event.user_id,
                                                 'founded_user': user['id']})
                    keyboard.add_button('➡️', color=VkKeyboardColor.SECONDARY, payload={'command': 'next'})
                    keyboard.add_line()  # Новая строка для кнопок
                    keyboard.add_button('Избранные', color=VkKeyboardColor.PRIMARY, payload={'command': 'favorites'})
                    keyboard.add_button('Выход', color=VkKeyboardColor.PRIMARY, payload={'command': 'exit'})
                    vk_keyboard = keyboard.get_keyboard()

                    self.send_msg(send_id=event.user_id, message=message, attachments=photo_attachments,
                                  keyboard=vk_keyboard)
                    break
        elif request.lower() in self.btn_text:
            # Заглушка от получаемого текста кнопок
            pass
        else:
            self.send_msg(event.user_id, "Не поняла вашего ответа...")

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

    def add_to_favourites(self):
        pass

    def add_to_blacklist(self):
        pass

    def get_favourites(self):
        '''
        Функция возвращает список строк favorites текущего пользователя:
        Структура: ФИО -- Возраст -- Город -- Ссылка
        :return:
        '''
        pass

    def already_viewed(self, user) -> bool:
        '''
        Эта функция проверяет есть ли пользователь в каких либо списках у текущего пользователя
        :param user:
        :return:
        '''
        return False

    def add_new_user(self, user) -> bool:
        '''
        Функция принимает пользователя, проверяет есть ли он в БД,
        Добавляет если его нет и возвращает True,
        Иначе False

        :param user:
        :return:  bool
        '''

        pass
