from __future__ import unicode_literals

from io import StringIO
import logging
import os

try:
    from urllib import parse
except ImportError:  # pragma: no cover
    import urllib as parse

try:
    from typing import Iterable, Mapping
    TEXT_TYPES = (str, )
except ImportError:  # pragma: no cover
    from collections import Iterable, Mapping
    TEXT_TYPES = (str, unicode)  # noqa: F821

#    pchar         = unreserved / pct-encoded / sub-delims / ":" / "@"
#    sub-delims    = "!" / "$" / "&" / "'" / "(" / ")"
#                  / "*" / "+" / "," / ";" / "="
#    unreserved    = ALPHA / DIGIT / "-" / "." / "_" / "~"
PATH_SAFE_CHARS = ":@!$&'()*+,;=-._~"
"""Safe characters for path elements."""


def build_url(service, *path, **query):
    """Build a URL that targets `service`.

    :param str service: service to target
    :param path: request path elements
    :param query: request query parameters
    :returns: a fully-formed, absolute URL
    :rtype: str

    """
    buf = StringIO()
    _write_network_portion(buf, service)
    buf.write('/')
    buf.write('/'.join(
        parse.quote(str(p), safe=PATH_SAFE_CHARS) for p in path))

    query_tuples = []
    for name, value in query.items():
        if isinstance(value, Mapping):
            raise ValueError('Mapping query parameters are unsupported')
        if isinstance(value, Iterable) and not isinstance(value, TEXT_TYPES):
            query_tuples.extend((name, elm) for elm in sorted(value))
        else:
            query_tuples.append((name, value))
    if query_tuples:
        query_tuples.sort()
        buf.write('?')
        buf.write('&'.join(
            '{0}={1}'.format(_quote_query_arg(name), _quote_query_arg(value))
            for name, value in query_tuples))

    return buf.getvalue()


def _write_network_portion(buf, service):
    """Add the discovered network portion to `buf`.

    :param io.StringIO buf: buffer to write the discovered network
        details to
    :param str service: name of the service that is being looked up

    """
    logger = logging.getLogger(__package__)
    env_service = service.upper()
    discovery_style = os.environ.get('KLEMPNER_DISCOVERY', None)
    if discovery_style == 'consul':
        try:
            datacenter = os.environ['CONSUL_DATACENTER']
        except KeyError:
            logger.warning('discovery style set to consul but '
                           'CONSUL_DATACENTER is not set: falling back to '
                           'simple URL building')
        else:
            buf.write('http://')
            buf.write(service)
            buf.write('.service.')
            buf.write(datacenter)
            buf.write('.consul')
            return

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


def _quote_query_arg(v):
    if not isinstance(v, TEXT_TYPES):
        v = str(v)
    return parse.quote(v.encode('utf-8'))
