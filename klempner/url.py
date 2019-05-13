from __future__ import unicode_literals

import logging
import os
try:
    from urllib.parse import urlsplit
except ImportError:
    from urlparse import urlsplit

import requests.adapters

import cachetools
from klempner import compat, config, errors

#    pchar         = unreserved / pct-encoded / sub-delims / ":" / "@"
#    sub-delims    = "!" / "$" / "&" / "'" / "(" / ")"
#                  / "*" / "+" / "," / ";" / "="
#    unreserved    = ALPHA / DIGIT / "-" / "." / "_" / "~"

PATH_SAFE_CHARS = ":@!$&'()*+,;=-._~"
"""Safe characters for path elements."""


class ConsulAgentAdapter(requests.adapters.HTTPAdapter):
    """Adapter that sends `consul://` requests to a consul agent."""

    def send(self, request, stream=False, timeout=None, verify=True, cert=None,
             proxies=None):
        _, host, path, params, query, fragment = compat.urlparse(request.url)
        path = host + path
        request.url = compat.urlunparse(
            ('http', os.environ['CONSUL_HTTP_ADDR'], path, params, query,
             fragment))
        return super(ConsulAgentAdapter, self).send(
            request, stream=stream, timeout=timeout, verify=verify, cert=cert,
            proxies=proxies)  # yapf: disable


class State(object):
    """Module state.

    A single instance of this class exists as a module-level property.
    It caches information as it is discovered.  Applications SHOULD
    call :func:`.reset_cache` if they suspect that the discovery
    configuration has changed.

    """

    def __init__(self):
        self.discovery_cache = cachetools.TTLCache(50, 300)
        self.logger = logging.getLogger(__package__)
        self.session = requests.Session()
        self.session.mount('consul://', ConsulAgentAdapter())

    def clear(self):
        self.discovery_cache.clear()
        self.session.close()


_state = State()


def reset_cache():
    """Reset internal caches.

    Applications MUST call this function if they have changed discovery
    configuration details or suspect that they may have changed.  This
    should not happen often since the discovery configuration is based
    primarily on environment variables which are not modifiable from
    outside of the process.

    """
    config.reset()
    _state.clear()


def build_url(service, *path, **query):
    """Build a URL that targets `service`.

    :param str service: service to target
    :param path: request path elements
    :param query: request query parameters
    :returns: a fully-formed, absolute URL
    :rtype: str

    """
    config.ensure_configured()
    buf = compat.StringIO()
    _write_network_portion(buf, service)
    buf.write('/')
    buf.write('/'.join(
        compat.quote(str(p), safe=PATH_SAFE_CHARS) for p in path))

    query_tuples = []
    for name, value in query.items():
        if isinstance(value, compat.Mapping):
            raise ValueError('Mapping query parameters are unsupported')
        if (isinstance(value, compat.Iterable)
                and not isinstance(value, compat.TEXT_TYPES)):
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

    :param klempner.compat.StringIO buf: buffer to write the discovered
        network details to
    :param str service: name of the service that is being looked up

    """
    env_service = service.upper()
    discovery_style, parameters = config.get_discovery_details()
    if discovery_style == config.DiscoveryMethod.CONSUL:
        buf.write('http://')
        buf.write(service)
        buf.write('.service.')
        buf.write(parameters['datacenter'])
        buf.write('.consul')
    elif discovery_style == config.DiscoveryMethod.CONSUL_AGENT:
        sentinel = object()
        body = _state.discovery_cache.get(service, sentinel)
        if body is sentinel:
            response = _state.session.get(
                'consul://v1/catalog/service/{0}'.format(service))
            response.raise_for_status()
            body = response.json()
            _state.discovery_cache[service] = body

        if not body:  # service does not exist in consul
            raise errors.ServiceNotFoundError(service)
        else:
            calculated_scheme = config.URL_SCHEME_MAP.get(
                body[0]['ServicePort'], 'http')
            meta = body[0].get('ServiceMeta', {})
            buf.write(meta.get('protocol', calculated_scheme))
            buf.write('://')
            buf.write(
                '{ServiceName}.service.{Datacenter}.consul'.format(**body[0]))
            buf.write(':' + str(body[0]['ServicePort']))
    elif discovery_style == config.DiscoveryMethod.K8S:
        buf.write('http://')
        buf.write(service + '.')
        buf.write(parameters['namespace'])
        buf.write('.svc.cluster.local')
    elif discovery_style == config.DiscoveryMethod.ENV_VARS:
        scheme = os.environ.get('{0}_SCHEME'.format(env_service), None)
        host = os.environ.get('{0}_HOST'.format(env_service), None)
        port = os.environ.get('{0}_PORT'.format(env_service), None)

        if port is not None and port.startswith('tcp://'):
            # special case for docker's ip:port format
            parts = urlsplit(port)
            port = str(parts.port)
            if host is None:
                host = parts.hostname
        if scheme is None:
            if port is not None:
                scheme = config.URL_SCHEME_MAP.get(int(port), 'http')
            else:
                scheme = 'http'
        buf.write(scheme)
        buf.write('://')
        buf.write(host or service)
        if port is not None:
            buf.write(':')
            buf.write(port)
    else:
        buf.write('http://')
        buf.write(service)


def _quote_query_arg(v):
    if not isinstance(v, compat.TEXT_TYPES):
        v = str(v)
    return compat.quote(v.encode('utf-8'))
