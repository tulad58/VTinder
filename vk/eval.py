import string
import re


def extract_keywords(text: str) -> list:
    """
    Функция принимает текст убирая лишние данные
    :param text: Интересы пользователя в виде строки
    :return: Список уникальных ключевых слов
    """
    str_cleaned = text.translate(str.maketrans('', '', string.punctuation))
    # Поиск всех слов в строке, содержащих более 2х символов
    words = re.findall(r'\b\w{3,}\b', str_cleaned.lower())
    return list(set(words))


def get_cost_eval(user_interests: list, profile_interests: str, point: int) -> float:
    """
    Функция рассчитывает оценку
    :param user_interests: Список ключевых интересов пользователя
    :param profile_interests: Интересы найденного профиля в виде строки
    :param point: Вес оценки
    :return: Количество совпадений между ключевыми интересами и интересами клиента
    """
    return point * round(get_matches(profile_interests, user_interests) / len(user_interests), 2) \
        if user_interests and profile_interests else 0


def get_matches(profile_interests: str, user_interests: list) -> int:
    """
    Функция подсчитывает количество совпадений между ключевыми интересами и интересами клиента.
    :param user_interests: Список ключевых интересов пользователя
    :param profile_interests: Интересы найденного профиля в виде строки
    :return: Количество совпадений между ключевыми интересами и интересами клиента
    """
    profile_interests_lower = profile_interests.lower()
    matching_count = sum(interest.lower() in profile_interests_lower for interest in user_interests)
    return matching_count


def evaluation_profiles(current_user, founded_profiles):
    user_interest_key = extract_keywords(current_user['interests'])
    user_music_key = extract_keywords(current_user['music'])
    user_books_key = extract_keywords(current_user['books'])

    for i, profile in enumerate(founded_profiles):
        # cost_age_one - вес 5 идет сравнение с разницей в возрасте, чем больше разница, тем меньше балл
        if profile.get('bdate') and len(profile.get('bdate')) >= 8 and len(current_user['bdate']) >= 8:
            cost_age = 5 - abs(int(current_user['bdate'][-4:]) - int(profile['bdate'][-4:]))
        # если не указан год рождения
        else:
            cost_age = 3
        # cost_interest - вес равен 7 * на процент совпадений
        cost_interest = get_cost_eval(user_interest_key, profile.get('interests'), 7)
        # cost_music - вес равен 3 * на процент совпадений
        cost_music = get_cost_eval(user_music_key, profile.get('music'), 5)
        # cost_books - вес равен 2 * на процент совпадений
        cost_books = get_cost_eval(user_books_key, profile.get('books'), 2)

        founded_profiles[i]['eval'] = cost_age + cost_interest + cost_music + cost_books

    result = sorted(founded_profiles, key=lambda x: float(x['eval']), reverse=True)
    return result
