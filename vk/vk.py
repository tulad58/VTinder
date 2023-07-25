import json
import re
from datetime import datetime
from random import randrange, choice

import vk_api
from vk_api import VkTools
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkLongPoll, VkEventType

from core.config import settings


def get_max_size(sizes):
    return 'wzyrqpoxms'.index(sizes['type'])


def calculate_age(birth_date):
    birth_date = datetime.strptime(birth_date, '%d.%m.%Y')
    current_date = datetime.now()
    age = current_date.year - birth_date.year
    if (current_date.month, current_date.day) < (birth_date.month, birth_date.day):
        age -= 1
    return age


class VK:
    def __init__(self, access_token, version=settings.VK_API_VERSION):
        self.vk = vk_api.VkApi(token=access_token, api_version=version)
        self.fields = 'about, activities, bdate, books, can_send_friend_request, can_write_private_message, city,' \
                      'domain, interests, lists, music, photo_max_orig, quotes, relation, screen_name, sex'

    def get_users_info(self, user_ids):
        return self.vk.method('users.get', {
            'user_ids': user_ids,
            'fields': self.fields
        })

    def search_users(self, sex=0, city_id=None, age_from=None, age_to=None):
        if sex == 1:
            search_sex = 2
        elif sex == 2:
            search_sex = 1
        else:
            search_sex = 0

        params = {
            'fields': self.fields,
            'sex': search_sex,
            'has_photo': True,
            'is_closed': False,
        }
        if city_id:
            params['city_id'] = int(city_id)
        if age_from:
            params['age_from'] = int(age_from)
        if age_to:
            params['age_to'] = int(age_to)

        users = VkTools(self.vk).get_all(
            method='users.search',
            max_count=1000,
            values=params,
        ).get('items')

        if users:
            return users
        return []

    def get_photos(self, owner_id, album_id='profile'):
        params = {
            'owner_id': owner_id,
            'album_id': album_id,
            'rev': 1,
            'extended': 1
        }
        photos = self.vk.method('photos.get', params).get('items')
        if photos:
            photos_top_likes = sorted(photos, key=lambda x: x['likes']['count'], reverse=True)[:3]
            return ','.join([f'photo{photo["owner_id"]}_{photo["id"]}' for photo in photos_top_likes])
        return None


class VkBot:
    def __init__(self, access_token):
        self.vk = vk_api.VkApi(token=access_token)
        self.long_poll = VkLongPoll(self.vk)

    def start(self):
        for event in self.long_poll.listen():
            if event.type == VkEventType.MESSAGE_NEW:
                if event.to_me:
                    # События, которые идут от кнопки
                    if 'payload' in event.raw[6]:
                        btn = json.loads(event.payload).get('button')
                        if re.match(r'^like_', btn):
                            user_id = btn.split('like_')[1]
                            ...
                        elif re.match(r'^dislike_', btn):
                            user_id = btn.split('dislike_')[1]
                            ...
                        elif re.match(r'^favorites_', btn):
                            user_id = btn.split('favorites_')[1]
                            ...
                        elif btn == 'exit':
                            print('Возвращайся еще')
                    else:
                        self.request_handler(event)

    def request_handler(self, event):

        request = event.text
        if request.upper() == "ПРИВЕТ":
            vk_session = VK(access_token=settings.VK_USER_TOKEN)
            current_user = vk_session.get_users_info(user_ids=event.user_id)[0]
            is_new = self.add_new_user(current_user)
            options = {
                'age_from': 14,
                'age_to': 80
            }
            user_age = current_user.get('bdate')

            if user_age:
                options['age_from'] = calculate_age(user_age) - 5 if current_user['sex'] == 1 else calculate_age(
                    user_age)
                options['age_to'] = calculate_age(user_age) if current_user['sex'] == 1 else calculate_age(user_age) + 5

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
                self.send_msg(send_id=event.user_id, message=message, attachments=photo_attachments,
                              user_id=user['id'])
                break
        else:
            self.send_msg(event.user_id, "Не поняла вашего ответа...")

    def send_msg(self, send_id, message, attachments=None, user_id=None):
        """
        Отправка сообщения через метод messages.send
        :param send_id: vk id пользователя, который получит сообщение
        :param message: содержимое отправляемого сообщения
        :param attachments: строка с фото контентом отправляемого сообщения
        :return: None
        """

        keyboard = VkKeyboard(one_time=False, inline=True)
        keyboard.add_button('❤️', VkKeyboardColor.SECONDARY, payload={'button': f'like_{user_id}'})
        keyboard.add_button('👎', VkKeyboardColor.SECONDARY, payload={'button': 'dislike'})
        keyboard.add_button('➡️', VkKeyboardColor.SECONDARY, payload={'button': 'next'})
        keyboard.add_line()  # Новая строка для кнопок
        keyboard.add_button('Избранные', VkKeyboardColor.PRIMARY, payload={'button': 'favorites'})
        keyboard.add_button('Выход', VkKeyboardColor.PRIMARY, payload={'button': 'exit'})

        self.vk.method('messages.send', {'user_id': send_id,
                                         'message': message,
                                         'random_id': randrange(10 ** 7),
                                         'attachment': attachments,
                                         'keyboard': keyboard.get_keyboard()})

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
        Эта функция проверяет есть ли ппользователь в каких либо списках у текущего пользователя
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
