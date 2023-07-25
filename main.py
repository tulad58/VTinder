from db.session import DBHandler
from vk.bot import VkBot
from core.config import settings

if __name__ == '__main__':
    db = DBHandler()
    session = db.connect()
    vk_bot = VkBot(access_token=settings.VK_BOT_TOKEN)
    vk_bot.start()

