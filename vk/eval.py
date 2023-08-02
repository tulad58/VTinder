import string
import re
from core.config import settings


def extract_keywords(text: str) -> set:
    """
    Функция принимает текст убирая лишние данные
    :param text: Интересы пользователя в виде строки
    :return: Множество уникальных ключевых слов (до 5 ключей)
    """
    if text:
        str_cleaned = text.translate(str.maketrans('', '', string.punctuation))
        # Поиск всех слов в строке, содержащих более 2х символов
        words = re.findall(r'\b\w{3,}\b', str_cleaned.lower())
        result = list(set(words))[0:settings.eval_limit]
        return set(result)
    else:
        return set()


def get_cost_eval(user_interests: set, profile_interests: set, point: int) -> float:
    """
    Функция рассчитывает оценку
    :param user_interests: Множество ключевых интересов пользователя
    :param profile_interests: Множество ключевых интересов найденного профиля
    :param point: Вес оценки
    :return: Оценка совпадений между ключевыми интересами пользователя и интересами найденного профиля
    """
    return point * round(len(profile_interests & user_interests) / settings.eval_limit, 2) \
        if user_interests and profile_interests else 0


def evaluation_profiles(current_user, founded_profiles):
    user_interest_key = extract_keywords(current_user.get('interests'))
    user_music_key = extract_keywords(current_user.get('music'))
    user_books_key = extract_keywords(current_user.get('books'))

    for i, profile in enumerate(founded_profiles):

        profile_interest_key = extract_keywords(profile.get('interests'))
        profile_music_key = extract_keywords(profile.get('music'))
        profile_books_key = extract_keywords(profile.get('books'))

        # cost_interest - вес равен 7 * на процент совпадений
        cost_interest = get_cost_eval(user_interest_key, profile_interest_key, 7)
        # cost_music - вес равен 3 * на процент совпадений
        cost_music = get_cost_eval(user_music_key, profile_music_key, 5)
        # cost_books - вес равен 2 * на процент совпадений
        cost_books = get_cost_eval(user_books_key, profile_books_key, 2)
        # cost_age_one - вес 5 идет сравнение с разницей в возрасте, чем больше разница, тем меньше балл
        if profile.get('bdate') and len(profile.get('bdate')) >= 8 and len(current_user['bdate']) >= 8:
            cost_age = 5 - abs(int(current_user['bdate'][-4:]) - int(profile['bdate'][-4:]))
        # если не указан год рождения
        else:
            cost_age = 3

        founded_profiles[i]['eval'] = cost_age + cost_interest + cost_music + cost_books

    result = sorted(founded_profiles, key=lambda x: float(x['eval']), reverse=True)
    return result
