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
from vk.eval import evaluation_profiles


class VkBot(VKBase):
    def __init__(self, access_token, version=settings.VK_API_VERSION):
        super().__init__(access_token, version)
        self.long_poll = VkLongPoll(self.vk)
        self.text_commands = settings.bot_commands
        self.user_sessions = dict()

    def start(self):
        for event in self.long_poll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                vk_user_token = self.check_user_registration(event)
                if vk_user_token:
                    user_session, have_all_we_need = self.get_or_create_session(vk_user_token, event)
                    if have_all_we_need:
                        self.request_handler(user_session, event)

    def get_or_create_session(self, vk_user_token, event):
        have_all_we_need = True
        if event.user_id in self.user_sessions:
            return self.user_sessions.get(event.user_id), have_all_we_need
        new_session = VkUserSession(user_access_token=vk_user_token)
        current_user = new_session.get_users_info(user_ids=event.user_id)[0]
        have_all_we_need = self.check_update_user_params(event, current_user, new_session)
        if have_all_we_need:
            new_session.db_user = db.get_or_create_user(current_user['id'])
            new_session.vk_user = current_user
            self.user_sessions[current_user['id']] = new_session
        return new_session, have_all_we_need

    def request_handler(self, user_session: VkUserSession, event):
        event_text = event.text.lower()
        if event_text in self.text_commands or 'setting' in event_text:
            if 'payload' in event.raw[6]:
                self.payload_handler(user_session, event)
            else:
                self.text_handler(user_session, event)
        else:
            self.send_msg(event.user_id, f'❗❗❗Неизвестная команда: {event_text}❗❗❗\n'
                                         f'Напишите: "Привет" и я попробую найти для вас пару')

    def text_handler(self, user_session: VkUserSession, event, next=None):
        if next:
            user_session.pop_marker
        current_user = user_session.vk_user
        current_user_bdate = current_user.get('bdate')
        age_from = settings.default_age_from
        age_to = settings.default_age_to
        if current_user_bdate and len(current_user_bdate) >= 8:
            current_user['age'] = calculate_age(current_user_bdate)
            age_from = current_user['age'] - 5 if current_user['sex'] == 2 else current_user['age']
            age_to = current_user['age'] if current_user['sex'] == 2 else current_user['age'] + 5
        if not user_session.founded_profiles:
            self.send_msg(event.user_id, '️🧐Начинаю поиск...')

            founded_profiles = user_session.search_users(
                sex=current_user['sex'],
                city_id=current_user['city']['id'],
                age_from=age_from,
                age_to=age_to
            )
            founded_profiles = [profile for profile in founded_profiles if
                                not self.already_viewed(user_session.db_user, profile['id']) and not profile[
                                    'is_closed']]
            self.send_msg(event.user_id, '️🤔 Выбираю кто тебе больше подходит...')
            user_session.founded_profiles = evaluation_profiles(current_user, founded_profiles)
        self.response_handler(user_session, event, current_user)

    def payload_handler(self, user_session: VkUserSession, event):
        command_obj = json.loads(event.payload)
        command = command_obj.get('command')
        founded_profile_id = command_obj.get('founded_profile')
        profile_firstname = command_obj.get('profile_firstname')
        profile_lastname = command_obj.get('profile_lastname')
        profile_domain = command_obj.get('profile_domain')
        if command == 'like':
            is_added = self.add_to_list(user_session.db_user, founded_profile_id, profile_firstname,
                                        profile_lastname, profile_domain)
            if is_added:
                self.send_msg(send_id=event.user_id,
                              message=f'{profile_firstname} теперь в ваших ⭐ Избранных')
            self.text_handler(user_session, event)
        elif command == 'dislike':
            to_blacklist = True
            is_added = self.add_to_list(user_session.db_user, founded_profile_id, profile_firstname,
                                        profile_lastname, profile_domain, to_blacklist)
            if is_added:
                self.send_msg(send_id=event.user_id,
                              message=f'{profile_firstname} теперь в вашем 👎 Черном списке')
            self.text_handler(user_session, event)
        elif command == 'next':
            self.text_handler(user_session, event, next=True)
        elif command == 'favorites':
            fav = self.get_favorites(user_session.db_user)
            self.send_msg(send_id=event.user_id, message=fav)
        elif command == 'exit':
            self.user_sessions.pop(event.user_id)
            self.send_msg(send_id=event.user_id, message='👋Возвращайся еще')

    def response_handler(self, user_session, event, current_user):
        message_pack = settings.male_msgs if current_user['sex'] == 2 else settings.female_msgs
        while True:
            profile = user_session.founded_profiles.pop(user_session.pop_marker)
            photo_attachments = user_session.get_photos(owner_id=profile['id'])
            if photo_attachments is None:
                continue
            break

        message = f'{choice(message_pack)} \n' \
                  f'{profile.get("first_name")} {profile.get("last_name")}.\n' \
                  f'Ссылка: https://vk.com/{profile.get("domain")}'
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
        :param payload: параметр для получения обратной связи в виде json строки
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

    @staticmethod
    def add_to_list(db_user,
                    profile_vk_id: int,
                    profile_firstname: str,
                    profile_lastname: str,
                    profile_domain: str,
                    blacklist=False):
        if db_user and profile_vk_id:
            return db.add_to_lists(
                db_user,
                profile_vk_id,
                profile_firstname,
                profile_lastname,
                profile_domain,
                blacklist
            )
        raise ValueError('Problem with vk_id')

    @staticmethod
    def get_favorites(user_id):
        '''
        Функция возвращает список строк favorites текущего пользователя:
        Структура: ФИО -- Ссылка
        :return:
        '''
        favorites = db.get_favorites(user_id)
        if not favorites:
            return 'Избранных пока нету'
        verbose_favorites = 'Твои избранные: \n'
        for i, profile in enumerate(favorites, start=1):
            verbose_favorites += f'{i}. {profile.first_name} {profile.last_name} - https://vk.com/{profile.domain} \n'
        return verbose_favorites

    @staticmethod
    def already_viewed(db_user, profile_id) -> bool:
        '''
        Эта функция проверяет есть ли пользователь в каких либо списках у текущего пользователя
        :param user:
        :return:
        '''
        return db.exist_in_user_lists(db_user, profile_id)

    @staticmethod
    def add_new_user(user) -> bool:
        '''
        Функция принимает пользователя, проверяет есть ли он в БД.
        Добавляет если его нет и возвращает True, иначе False
        '''

        user_vk_id = user.get('id')
        return db.get_or_create_user(user_vk_id)

    def check_update_user_params(self, event, current_user, vk_session):
        birthday = current_user.get('bdate')
        if not birthday or len(birthday) <= 8 or not current_user.get('city').get('id'):
            if 'setting' in event.text:
                setting = re.findall(r'-\s*(\d{2}.\d{2}.\d{4})\s*-\s*(\S+)', event.text)[0]
                current_user['bdate'] = setting[0]
                current_user['city'] = vk_session.get_city(setting[1])
                msg = f'Получены настройки\n ' \
                      f'Дата рождения: {current_user["bdate"]},\n ' \
                      f'Город поиска:  {current_user["city"]["title"]}'
                payload = '{\"command\":\"setting\"}'
                self.send_msg(send_id=event.user_id, message=msg, payload=payload)
                return True
            else:
                msg = 'Не удается получить данные пользователя😔\n' \
                      'Введи команду setting с указанием даты рождения и города.\n\n' \
                      'Пример: setting - 01.01.1990 - Москва'
                self.send_msg(send_id=event.user_id, message=msg)
                return False
        return True

    def check_user_registration(self, event):
        if 'token' in event.text:
            access_token = re.findall(r'(vk1[^&]+)', event.text)
            if access_token:
                token = access_token[0]
                msg = 'Получен access_token 💾 '
                payload = '{\"command\":\"access_token\"}'
                self.send_msg(send_id=event.user_id, message=msg, payload=payload)
                return token
            else:
                msg = '❗❗❗Значение access_token неопределенно❗❗❗\n' \
                      'Отправьте новое сообщение с командой token\n' \
                      'Пример, token - vk1.a.************************************'
                payload = '{\"command\":\"access_token\"}'
                self.send_msg(send_id=event.user_id, message=msg, payload=payload)
                return None
        else:
            # access_token временный и его хранение в бд не безопасно,
            # поэтому добавили подставку токена пользователя из настроек приложения settings.VK_USER_TOKEN
            token = settings.VK_USER_TOKEN
            # token = False
            if not token:
                msg = 'Привет🤚\n' \
                      'Для работы поиска необходим access_token пользователя ⚙️\n' \
                      'Откройте ссылку в браузере 👇\n' \
                      f'https://oauth.vk.com/authorize?client_id={settings.VK_CLIENT_ID}&scope=327686' \
                      f'&response_type=token\n' \
                      'Появится окно с запросом доступа 👉 нажимаем "Разрешить"\n' \
                      'В результате Браузер перекинет на другую ссылку\n' \
                      'Из этой ссылки нужно скопировать access_token и отправить сообщение с командой token\n' \
                      'Пример, token - vk1.a.************************************'
                self.send_msg(send_id=event.user_id, message=msg)
            return token

