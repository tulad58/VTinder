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
            print(event)
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                vk_user_setting = self.check_user_registration(event)  # получив токен впервые тут создал первую сессию
                if vk_user_setting:
                    # check_update_user_params решил заменить на check_update_user_settings но сверяя с базой
                    # have_all_we_need = self.check_update_user_settings(event, vk_user_setting, new_session)  # сессию потерял тут создав новую
                    user_session, have_all_we_need = self.get_or_create_session(vk_user_setting, event)
                    if have_all_we_need:
                        self.request_handler(user_session, event)

    def get_or_create_session(self, vk_user_setting, event):
        have_all_we_need = True
        if event.user_id in self.user_sessions:
            return self.user_sessions.get(event.user_id), have_all_we_need
        new_session = VkUserSession(user_access_token=vk_user_setting.token)
        # current_user = new_session.get_users_info(user_ids=event.user_id)[0]
        have_all_we_need = self.check_update_user_settings(event, vk_user_setting, new_session)
        # have_all_we_need = self.check_update_user_params(event, current_user, new_session)
        if have_all_we_need:
            new_session.set_db_user(db.get_or_create_user(vk_user_setting.user_id))
            new_session.set_user(vk_user_setting)
            self.user_sessions[f'{vk_user_setting.user_id}'] = new_session
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
            user_session.increase_pop()
        current_user = user_session.user
        current_user_age = calculate_age(current_user.date_of_birth.strftime('%d.%m.%Y'))
        age_from = current_user_age - 5 if current_user.gender_id == 2 else current_user_age
        age_to = current_user_age if current_user.gender_id == 2 else current_user_age + 5

        if not user_session.founded_profiles:
            self.send_msg(event.user_id, '️🧐Начинаю поиск...')

            founded_profiles = user_session.search_users(
                sex=current_user.gender_id,
                city_id=current_user.city_id,
                age_from=age_from,
                age_to=age_to
            )
            founded_profiles = [profile for profile in founded_profiles if
                                not self.already_viewed(user_session.db_user, profile['id']) and not profile[
                                    'is_closed']]
            self.send_msg(event.user_id, '️🤔 Выбираю кто тебе больше подходит...')
            # Нет хранения интересов в бд
            # user_session.founded_profiles = evaluation_profiles(current_user, founded_profiles)
            user_session.founded_profiles = founded_profiles
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
            self.send_msg(send_id=event.user_id, message='👋Возвращайся еще')

    def response_handler(self, user_session, event, current_user):
        photo_attachments = None
        message_pack = settings.male_msgs if current_user['sex'] == 2 else settings.female_msgs
        while True:
            profile = user_session.founded_profiles.pop(user_session.pop)
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

    def add_to_list(self,
                    db_user,
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
            verbose_favorites += f'{i}. {profile.first_name} {profile.last_name} - https://vk.com/{profile.domain} \n'
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
        Функция принимает пользователя, проверяет есть ли он в БД.
        Добавляет если его нет и возвращает True, иначе False
        '''

        user_vk_id = user.get('id')
        return db.get_or_create_user(user_vk_id)

    def check_update_user_params(self, event, current_user, vk_session):
        if not current_user.get('sex') or not current_user.get('city'):
            # Обработать исключения когда у пользователя нет города или пола
            pass
        if not current_user.get('bdate'):
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
                new_session = VkUserSession(user_access_token=access_token[0])
                user_ = new_session.get_users_info(user_ids=event.user_id)[0]
                user_setting = db.create_user_setting(user_id=user_.get('id'),
                                                      token=access_token[0],
                                                      gender_id=user_.get('sex'),
                                                      date_of_birth=user_.get('bdate'),
                                                      city_id=user_.get('city').get('id'))
                msg = 'Получен access_token 💾 '
                payload = '{\"command\":\"access_token\"}'
                self.send_msg(send_id=event.user_id, message=msg, payload=payload)
                return user_setting
            else:
                msg = '❗❗❗Значение access_token неопределенно❗❗❗\n' \
                      'Отправьте новое сообщение с командой token\n' \
                      'Пример, token - vk1.a.************************************'
                payload = '{\"command\":\"access_token\"}'
                self.send_msg(send_id=event.user_id, message=msg, payload=payload)
                return None
        else:
            # Делаем запрос в БД по event.user_id для уточнения регистрации и наличия токена
            user_setting = db.get_user_setting(event.user_id)
            # Временно добавил подставку settings.VK_USER_TOKEN, когда БД доделаем, то уберем
            # user_setting.token = settings.VK_USER_TOKEN
            if user_setting is None:
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

            return user_setting

    def check_update_user_settings(self, event, user_setting, new_session):
        if user_setting.city_id is None or user_setting.date_of_birth is None:
            if 'setting' in event.text:
                setting = re.findall(r'-\s*(\d{2}.\d{2}.\d{4})\s*-\s*(\S+)', event.text)[0]
                user_setting.date_of_birth = setting[0]
                city = new_session.get_city(setting[1])
                user_setting.city_id = city.get('id')
                user_setting = db.create_user_setting(user_id=user_setting.user_id,
                                                      token=user_setting.token,
                                                      gender_id=user_setting.gender_id,
                                                      date_of_birth=user_setting.date_of_birth,
                                                      city_id=user_setting.city_id)

                msg = f'Получены настройки\n ' \
                      f'Дата рождения: {user_setting.date_of_birth},\n ' \
                      f'Город поиска:  {city["title"]}'
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
