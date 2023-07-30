import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

nltk.download('punkt')
nltk.download('stopwords')


def extract_keywords(text):
    """
    Функция принимает текст убирая лишние данные.
    Args:
        text (str): Интересы пользователя в виде строки.
    Returns:
        list: Список ключевых слов
    """

    stop_words = set(stopwords.words('russian'))
    keywords = word_tokenize(text.lower(), language='russian')
    return [token for token in keywords if token.isalpha() and token not in stop_words and len(token) > 2]


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
        # cost_interest - вес равен 4 * на процент совпадений
        cost_interest = 0
        if profile.get('interests'):
            cost_interest = 7 * round(get_matches(profile['interests'], user_interest_key) / len(user_interest_key), 2)
        # cost_music - вес равен 3 * на процент совпадений
        cost_music = 0
        if profile.get('music'):
            cost_music = 5 * round(get_matches(profile['music'], user_music_key) / len(user_music_key), 2)
        # cost_books - вес равен 2 * на процент совпадений
        cost_books = 0
        if profile.get('books'):
            cost_books = 2 * round(get_matches(profile['books'], user_books_key) / len(user_books_key), 2)

        founded_profiles[i]['eval'] = cost_age + cost_interest + cost_music + cost_books

    result = sorted(founded_profiles, key=lambda x: float(x['eval']), reverse=True)

    return result
