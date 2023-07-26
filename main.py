from db.session import DBHandler
from vk.bot import VkBot
from core.config import settings
from db.crud import user

if __name__ == '__main__':
    vk_bot = VkBot(access_token=settings.VK_BOT_TOKEN)
    vk_bot.start()

