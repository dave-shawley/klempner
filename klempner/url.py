import urllib.parse
try:
    from typing import Iterable, Mapping
    TEXT_TYPES = (str, )
except ImportError:  # pragma: no cover
    from collections import Iterable, Mapping
    TEXT_TYPES = (str, unicode)

PATH_SAFE_CHARS = ':@~._-'


def build_url(service, *path, **query):
    """Build a URL that targets `service`.

    :param str service: service to target
    :param path: request path elements
    :param query: request query parameters
    :returns: a fully-formed, absolute URL
    :rtype: str

    """
    url = ['http://', service]
    if path:
        url.extend('/' + urllib.parse.quote(str(p), safe=PATH_SAFE_CHARS)
                   for p in path)
    else:
        url.append('/')

    qtuples = []
    for name, value in query.items():
        if isinstance(value, Mapping):
            raise ValueError('Mapping query parameters are unsupported')
        if isinstance(value, Iterable) and not isinstance(value, TEXT_TYPES):
            qtuples.extend((name, elm) for elm in sorted(value))
        else:
            qtuples.append((name, value))
    if qtuples:
        url.extend([
            '?',
            urllib.parse.urlencode(qtuples, quote_via=urllib.parse.quote),
        ])

    return ''.join(url)
