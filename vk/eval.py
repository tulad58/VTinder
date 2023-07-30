import string
import re

def extract_keywords(text):
    """
    Функция принимает текст убирая лишние данные.
    Args:
        text (str): Интересы пользователя в виде строки.
    Returns:
        list: Список ключевых слов
    """
    # Удаление символов пунктуации из строки
    str_cleaned = text.translate(str.maketrans('', '', string.punctuation))
    # Поиск всех слов в строке, содержащих более 2х символов
    words = re.findall(r'\b\w{3,}\b', str_cleaned.lower())
    # Возвращаем список уникальных слов
    return list(set(words))


def get_cost_eval(user_key, profile_interests, point):
    cost_eval = 0
    if user_key and profile_interests:
        cost_eval = point * round(get_matches(profile_interests, user_key) / len(user_key), 2)
    return cost_eval


def get_matches(profile_interests, key_interests):
    """
    Функция подсчитывает количество совпадений между ключевыми интересами и интересами клиента.
    Args:
        profile_interests (str): Интересы клиента в виде строки.
        key_interests (list): Список ключевых интересов.
    Returns:
        int: Количество совпадений между ключевыми интересами и интересами клиента.
    """
    profile_interests_lower = profile_interests.lower()
    matching_count = sum(interest.lower() in profile_interests_lower for interest in key_interests)
    return matching_count


def evaluation_profiles(current_user, founded_profiles):
    user_interest_key = extract_keywords(current_user['interests'])
    user_music_key = extract_keywords(current_user['music'])
    user_books_key = extract_keywords(current_user['books'])

    for i, profile in enumerate(founded_profiles):
        # cost_age_one - вес 5 идет сравнение с разницей в возрасте, чем больше разница, тем меньше балл
        if profile.get('bdate') and len(profile.get('bdate')) >= 8:
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
