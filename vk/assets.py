from datetime import datetime

from vk_api.keyboard import VkKeyboard, VkKeyboardColor


def calculate_age(birth_date):
    birth_date = datetime.strptime(birth_date, '%d.%m.%Y')
    current_date = datetime.now()
    age = current_date.year - birth_date.year
    if (current_date.month, current_date.day) < (birth_date.month, birth_date.day):
        age -= 1
    return age


def keyboard_gen(event, profile):
    keyboard = VkKeyboard(one_time=False, inline=True)
    keyboard.add_button('❤️',
                        color=VkKeyboardColor.SECONDARY,
                        payload={'command': 'like',
                                 'current_user': event.user_id,
                                 'founded_profile': profile['id'],
                                 'profile_firstname': profile['first_name'],
                                 'profile_lastname': profile['last_name'],
                                 'profile_domain': profile['domain'],
                                 })
    keyboard.add_button('👎',
                        color=VkKeyboardColor.SECONDARY,
                        payload={'command': 'dislike',
                                 'current_user': event.user_id,
                                 'founded_profile': profile['id'],
                                 'profile_firstname': profile['first_name'],
                                 'profile_lastname': profile['last_name'],
                                 'profile_domain': profile['domain'],
                                 })
    keyboard.add_button('➡️', color=VkKeyboardColor.SECONDARY, payload={'command': 'next'})
    keyboard.add_line()  # Новая строка для кнопок
    keyboard.add_button('Избранные',
                        color=VkKeyboardColor.PRIMARY,
                        payload={
                            'command': 'favorites',
                            'current_user': event.user_id,
                        })
    keyboard.add_button('Выход',
                        color=VkKeyboardColor.PRIMARY,
                        payload={'command': 'exit',})
    return keyboard.get_keyboard()
