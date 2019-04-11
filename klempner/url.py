from io import StringIO
import os
import urllib.parse
try:
    from typing import Iterable, Mapping
    TEXT_TYPES = (str, )
except ImportError:  # pragma: no cover
    from collections import Iterable, Mapping
    TEXT_TYPES = (str, unicode)  # noqa: F821

PATH_SAFE_CHARS = ':@~._-'


def build_url(service, *path, **query):
    """Build a URL that targets `service`.

    :param str service: service to target
    :param path: request path elements
    :param query: request query parameters
    :returns: a fully-formed, absolute URL
    :rtype: str

    """
    buf = StringIO()

    env_service = service.upper()
    buf.write(os.environ.get('{0}_SCHEME'.format(env_service), 'http'))
    buf.write('://')

    netloc = os.environ.get('{0}_HOST'.format(env_service), None)
    if netloc is None:
        buf.write(service)
    else:
        port = os.environ.get('{0}_PORT'.format(env_service), '')
        if ':' in port:  # special case for docker's service:port format
            buf.write(port)
        else:
            buf.write(netloc)
            if port:
                buf.write(':' + port)

    buf.write('/')
    buf.write('/'.join(
        urllib.parse.quote(str(p), safe=PATH_SAFE_CHARS) for p in path))

    qtuples = []
    for name, value in query.items():
        if isinstance(value, Mapping):
            raise ValueError('Mapping query parameters are unsupported')
        if isinstance(value, Iterable) and not isinstance(value, TEXT_TYPES):
            qtuples.extend((name, elm) for elm in sorted(value))
        else:
            qtuples.append((name, value))
    if qtuples:
        buf.write('?' + urllib.parse.urlencode(qtuples,
                                               quote_via=urllib.parse.quote))

    return buf.getvalue()
