from datetime import datetime


def get_max_size(sizes):
    return 'wzyrqpoxms'.index(sizes['type'])


def calculate_age(birth_date):
    birth_date = datetime.strptime(birth_date, '%d.%m.%Y')
    current_date = datetime.now()
    age = current_date.year - birth_date.year
    if (current_date.month, current_date.day) < (birth_date.month, birth_date.day):
        age -= 1
    return age