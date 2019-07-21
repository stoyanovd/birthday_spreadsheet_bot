ENGLISH_LIST_LOWERCASE = ['january', 'february', 'march', 'april', 'may', 'june', 'july',
                          'august', 'september', 'october', 'november', 'december']

RUSSIAN_LIST_LOWERCASE = ['январь', 'февраль', 'март', 'апрель', 'май', 'июнь', 'июль',
                          'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь']

MONTHES_DICT = {ENGLISH_LIST_LOWERCASE[i]: i + 1 for i in range(len(ENGLISH_LIST_LOWERCASE))}
MONTHES_DICT.update(
    {RUSSIAN_LIST_LOWERCASE[i]: i + 1 for i in range(len(RUSSIAN_LIST_LOWERCASE))}
)
