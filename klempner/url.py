from __future__ import unicode_literals

import logging
import os

import requests.adapters

import cachetools
from klempner import compat, config, errors, version

#    pchar         = unreserved / pct-encoded / sub-delims / ":" / "@"
#    sub-delims    = "!" / "$" / "&" / "'" / "(" / ")"
#                  / "*" / "+" / "," / ";" / "="
#    unreserved    = ALPHA / DIGIT / "-" / "." / "_" / "~"

PATH_SAFE_CHARS = ":@!$&'()*+,;=-._~"
"""Safe characters for path elements."""


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
        self.session = self._create_session()

    def clear(self):
        self.discovery_cache.clear()
        self.session.close()
        self.session = self._create_session()

    def lookup_consul_service(self, service):
        sentinel = object()
        service_info = self.discovery_cache.get(service, sentinel)
        if service_info is sentinel:
            parsed = compat.urlparse(os.environ['CONSUL_AGENT_URL'])
            url = compat.urlunparse(
                (parsed[0], parsed[1],
                 '/v1/catalog/service/{0}'.format(service), '', '', ''))
            headers = {}
            if os.environ.get('CONSUL_HTTP_TOKEN'):
                headers['Authorization'] = 'Bearer {0}'.format(
                    os.environ['CONSUL_HTTP_TOKEN'])

            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            body = response.json()
            if body:
                service_info = body[0]
                self.discovery_cache[service] = service_info
            else:
                service_info = None

        return service_info

    @staticmethod
    def _create_session():
        session = requests.Session()
        session.headers['User-Agent'] = '/'.join([__package__, version])
        return session


_state = State()


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


def _reset_cache():
    """Reset internal caches.

    Applications MUST call this function if they have changed discovery
    configuration details or suspect that they may have changed.  This
    should not happen often since the discovery configuration is based
    primarily on environment variables which are not modifiable from
    outside of the process.

    """
    _state.clear()


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
        service_info = _state.lookup_consul_service(service)
        if not service_info:  # service does not exist in consul
            raise errors.ServiceNotFoundError(service)
        else:
            calculated_scheme = config.URL_SCHEME_MAP.get(
                service_info['ServicePort'], 'http')
            meta = service_info.get('ServiceMeta', {})
            buf.write(meta.get('protocol', calculated_scheme))
            buf.write('://')
            buf.write(service_info['ServiceName'])
            buf.write('.service.')
            buf.write(service_info['Datacenter'])
            buf.write('.consul:')
            buf.write(str(service_info['ServicePort']))
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
            parts = compat.urlparse(port)
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
