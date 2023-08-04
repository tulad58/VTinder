import vk_api
from vk_api import VkTools

from core.config import settings
from vk.base import VKBase


class VkUserSession(VKBase):
    sessions_count = 0

    def __init__(self, user_access_token, version=settings.VK_API_VERSION, user=None, db_user=None):
        super().__init__(user_access_token, version)
        self.__vk_user = user
        self.__pop_marker = 0
        self.__db_user = db_user
        self.founded_profiles = None
        VkUserSession.sessions_count += 1

    @property
    def db_user(self):
        return self.__db_user

    @db_user.setter
    def db_user(self, db_user):
        self.__db_user = db_user

    @property
    def vk_user(self):
        return self.__vk_user

    @vk_user.setter
    def vk_user(self, user):
        self.__vk_user = user

    @property
    def pop_marker(self):
        return self.__pop_marker

    @pop_marker.setter
    def pop_marker(self):
        self.__pop_marker += 1


    def search_users(self, city_id, age_from, age_to, sex=0, status=6):
        search_sex = 2 if sex == 1 else 1 if sex == 2 else 0
        params = {
            'fields': self.fields,
            'sex': search_sex,
            'city_id': int(city_id),
            'status': status,
            'has_photo': 1,
        }

        users = []
        for age in range(int(age_from), int(age_to)):
            if age_from:
                params['age_from'] = int(age)
            if age_to:
                params['age_to'] = int(age)
            users += VkTools(self.vk).get_all(
                method='users.search',
                max_count=1000,
                values=params,
            ).get('items')
        return users if users else []

    def get_photos(self, owner_id, album_id='profile'):
        params = {
            'owner_id': owner_id,
            'album_id': album_id,
            'rev': 1,
            'extended': 1
        }

        photos = []
        try:
            photos_from_avatars = self.vk.method('photos.get', params).get('items')
        except vk_api.exceptions.ApiError:
            photos_from_avatars = None
            print(f"Не удалось получить фото профиля пользователем {owner_id}")
        if photos_from_avatars:
            photos += photos_from_avatars
        try:
            photos_marked_user = self.vk.method('photos.getUserPhotos', {'user_id': owner_id, 'extended': 1}).get('items')
        except vk_api.exceptions.ApiError:
            photos_marked_user = None
            print(f"Не удалось получить фото с пользователем {owner_id}")
        if photos_marked_user:
            photos += photos_marked_user
        if photos:
            photos_top_likes = sorted(photos, key=lambda x: x['likes']['count'], reverse=True)[:3]
            return ','.join([f'photo{photo["owner_id"]}_{photo["id"]}' for photo in photos_top_likes])
        return None

    def get_city(self, city_name):
        city = self.vk.method('database.getCities', {'q': city_name.capitalize(), 'count': 5}).get('items')
        return city[0] if city else None
