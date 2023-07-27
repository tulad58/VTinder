import vk_api
from vk_api import VkTools

from core.config import settings
from vk.base import VKBase


class VkUserSession(VKBase):
    sessions_count = 0

    def __init__(self, user_access_token, version=settings.VK_API_VERSION, user=None, db_user=None):
        super().__init__(user_access_token, version)
        self.user__ = user
        self.pop_marker__ = 0
        self.db_user__ = db_user
        VkUserSession.sessions_count += 1

    def set_db_user(self, db_user):
        self.db_user__ = db_user

    @property
    def db_user(self):
        return self.db_user__

    def set_user(self, user):
        self.user__ = user

    @property
    def user(self):
        return self.user__

    def increase_pop(self):
        self.pop_marker__ += 1

    @property
    def pop(self):
        return self.pop_marker__

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
        try:
            photos = self.vk.method('photos.get', params).get('items')
            if photos:
                photos_top_likes = sorted(photos, key=lambda x: x['likes']['count'], reverse=True)[:3]
                return ','.join([f'photo{photo["owner_id"]}_{photo["id"]}' for photo in photos_top_likes])
            return None
        except vk_api.exceptions.ApiError as e:
            if e.code == 30:
                print("Ошибка: Профиль пользователя является приватным")
            else:
                # Обработка других ошибок API VK, если необходимо
                print("Ошибка API VK:", e)
            return None

    def get_city(self, city_name):
        city = self.vk.method('database.getCities', {'q': city_name.capitalize(), 'count': 5}).get('items')
        if city:
            return city[0]
        else:
            return None
