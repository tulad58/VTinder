import vk_api
from vk_api import VkTools

from core.config import settings


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
