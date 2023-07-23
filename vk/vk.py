import json
from datetime import datetime
from random import randrange
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
    def __init__(self, access_token, version='5.131'):
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
            'has_photo': 1,
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
            # Если пришло новое сообщение
            if event.type == VkEventType.MESSAGE_NEW:
                if event.to_me:
                    # События, которые идут от кнопки
                    if 'payload' in event.raw[6]:
                        btn = json.loads(event.payload).get('button')
                        print(btn)
                    # Сообщение от пользователя
                    request = event.text
                    # Логика ответа - вынести в отдельный блок
                    if request.upper() == "ПРИВЕТ":
                        vk_session = VK(access_token=settings.VK_USER_TOKEN)
                        user_info = vk_session.get_users_info(user_ids=event.user_id)[0]
                        options = {
                            'age_from': 14,
                            'age_to': 80
                        }
                        user_age = user_info.get('bdate')  # Запрашивать у пользователя, если нет
                        if user_age:
                            options['age_from'] = calculate_age(user_age) - 5,
                            options['age_to'] = calculate_age(user_age)

                        example_found_user = vk_session.search_users(
                            sex=user_info['sex'],
                            city_id=user_info['city']['id'],
                            age_from=options['age_from'][0],
                            age_to=options['age_to']
                        )[1]
                        # Добавить проверку приватности, пропускать приватных
                        example_photo_attachments = vk_session.get_photos(owner_id=example_found_user['id'])
                        self.send_msg(send_id=event.user_id, message="Привет", attachments=example_photo_attachments)
                    elif request.upper() == 'ПОКА':
                        self.send_msg(event.user_id, "Пока((")
                    elif request.upper() == 'ВЫХОД':
                        self.send_msg(event.user_id, "Пока((")
                    else:
                        self.send_msg(event.user_id, "Не поняла вашего ответа...")

    def send_msg(self, send_id, message, attachments=None):
        """
        Отправка сообщения через метод messages.send
        :param send_id: vk id пользователя, который получит сообщение
        :param message: содержимое отправляемого сообщения
        :param attachments: строка с фото контентом отправляемого сообщения
        :return: None
        """

        keyboard = VkKeyboard(one_time=False, inline=True)
        keyboard.add_button('👎', VkKeyboardColor.SECONDARY, payload={'button': 'dislike'})
        keyboard.add_button('❤️', VkKeyboardColor.SECONDARY, payload={'button': 'like'})
        keyboard.add_button('➡️', VkKeyboardColor.SECONDARY, payload={'button': 'next'})
        keyboard.add_line()  # Новая строка для кнопок
        keyboard.add_button('Выход', VkKeyboardColor.PRIMARY, payload={'button': 'exit'})

        self.vk.method('messages.send', {'user_id': send_id,
                                         'message': message,
                                         'random_id': randrange(10 ** 7),
                                         'attachment': attachments,
                                         'keyboard': keyboard.get_keyboard()})


if __name__ == '__main__':
    vk_bot = VkBot(access_token=settings.VK_BOT_TOKEN)
    vk_bot.start()
