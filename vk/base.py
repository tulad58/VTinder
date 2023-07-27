from vk_api import vk_api

from core.config import settings


class VKBase:
    def __init__(self, access_token, version):
        self.vk = vk_api.VkApi(token=access_token, api_version=version)
        self.fields = settings.request_fields

    def get_users_info(self, user_ids):
        return self.vk.method('users.get', {
            'user_ids': user_ids,
            'fields': self.fields
        })
