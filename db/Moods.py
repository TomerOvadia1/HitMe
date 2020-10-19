from collections import namedtuple

Mood_filter = namedtuple('Mood_filter',
                         ['lower_bound',
                          'upper_bound'])


def available_moods():
    return _moods.keys()


def _hype_filter():
    return Mood_filter(lower_bound='2/3', upper_bound='1')


def _chill_filter():
    return Mood_filter(lower_bound='0', upper_bound='1/3')


def _neutral_filter():
    return Mood_filter(lower_bound='1/3', upper_bound='2/3')


def mood_from_string(mood_str):
    """
    Create a mood object from string
    :param mood_str:
    :return:
    """
    if mood_str.lower() not in available_moods():
        raise KeyError('Mood not available')
    return _moods[mood_str]()


_moods = {
    'hype': _hype_filter,
    'neutral': _neutral_filter,
    'chill': _chill_filter
}
