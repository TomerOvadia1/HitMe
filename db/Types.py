from collections import namedtuple

Type_filter = namedtuple('Type_filter',
                         ['tempo_lower',
                          'tempo_upper',
                          'loudness_upper',
                          'loudness_lower',
                          'tempo_weight',
                          'loudness_weight'
                          ])


def available_types():
    return _types.keys()


def _running_filter():
    return Type_filter(tempo_lower=190, tempo_upper=260, loudness_lower=-15, loudness_upper=-2, tempo_weight=0.7,
                       loudness_weight=0.3)


def _driving_filter():
    return Type_filter(tempo_lower=130, tempo_upper=200, loudness_lower=-20, loudness_upper=-8, tempo_weight=0.6,
                       loudness_weight=0.4)


def _studying_filter():
    return Type_filter(tempo_lower=120, tempo_upper=180, loudness_lower=-15, loudness_upper=-8, tempo_weight=0.4,
                       loudness_weight=0.6)


def _dancing_filter():
    return Type_filter(tempo_lower=60, tempo_upper=120, loudness_lower=-50, loudness_upper=-12, tempo_weight=0.5,
                       loudness_weight=0.5)


def type_from_string(str_type):
    if str_type.lower() not in available_types():
        raise KeyError("Type not available")
    return _types[str_type]()


_types = {
    'running': _running_filter,
    'driving': _driving_filter,
    'studying': _studying_filter,
    'dancing': _dancing_filter,
}
