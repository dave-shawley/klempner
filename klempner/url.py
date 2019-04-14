from __future__ import unicode_literals

import logging
import os

try:
    from io import StringIO
    from urllib.parse import quote, urlparse, urlunparse
except ImportError:  # pragma: no cover
    from StringIO import StringIO
    from urllib import quote
    from urlparse import urlparse, urlunparse

try:
    from typing import Iterable, Mapping
    TEXT_TYPES = (str, )

except ImportError:  # pragma: no cover
    from collections import Iterable, Mapping
    TEXT_TYPES = (str, unicode)  # noqa: F821

import requests.adapters

from klempner import errors

#    pchar         = unreserved / pct-encoded / sub-delims / ":" / "@"
#    sub-delims    = "!" / "$" / "&" / "'" / "(" / ")"
#                  / "*" / "+" / "," / ";" / "="
#    unreserved    = ALPHA / DIGIT / "-" / "." / "_" / "~"
PATH_SAFE_CHARS = ":@!$&'()*+,;=-._~"
"""Safe characters for path elements."""


class DiscoveryMethod(object):
    """Available discovery methods."""

    SIMPLE = 'simple'
    """Build URLs using service name as host name."""

    CONSUL = 'consul'
    """Build consul-based service URLs."""

    CONSUL_AGENT = 'consul+agent'
    """Build consul-based service URLs using a consul agent."""

    K8S = 'kubernetes'
    """Build Kubernetes cluster-based service URLs."""

    DEFAULT = SIMPLE

    AVAILABLE = (CONSUL, CONSUL_AGENT, K8S, SIMPLE)


class ConsulAgentAdapter(requests.adapters.HTTPAdapter):
    """Adapter that sends `consul://` requests to a consul agent."""

    def send(self, request, stream=False, timeout=None, verify=True, cert=None,
             proxies=None):
        _, _, path, params, query, fragment = urlparse(request.url)
        request.url = urlunparse(('http', os.environ['CONSUL_HTTP_ADDR'], path,
                                  params, query, fragment))
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
        self.discovery_style = None
        self.discovery_parameters = tuple()
        self.logger = logging.getLogger(__package__)
        self.session = requests.Session()
        self.session.mount('consul://', ConsulAgentAdapter())

    def clear(self):
        self.session.close()
        self.discovery_style = None

    def determine_discovery_method(self):
        if self.discovery_style is not None:
            return

        self.discovery_style = DiscoveryMethod.DEFAULT
        discovery_style = os.environ.get('KLEMPNER_DISCOVERY',
                                         DiscoveryMethod.SIMPLE)
        if discovery_style == DiscoveryMethod.CONSUL:
            try:
                datacenter = os.environ['CONSUL_DATACENTER']
                self.discovery_style = discovery_style
                self.discovery_parameters = (datacenter, )
            except KeyError:
                self.logger.warning(
                    'discovery style set to %s but CONSUL_DATACENTER is not '
                    'set: falling back to simple URL construction',
                    discovery_style)
        elif discovery_style == DiscoveryMethod.CONSUL_AGENT:
            response = self.session.get('consul://agent/v1/agent/self')
            response.raise_for_status()
            body = response.json()
            self.discovery_style = discovery_style
            self.discovery_parameters = (body['Config']['Datacenter'], )
        elif discovery_style == DiscoveryMethod.K8S:
            namespace = os.environ.get('KUBERNETES_NAMESPACE', 'default')
            self.discovery_style = discovery_style
            self.discovery_parameters = (namespace, )


_state = State()


def reset_cache():
    """Reset internal caches.

    Applications MUST call this function if they have changed discovery
    configuration details or suspect that they may have changed.  This
    should not happen often since the discovery configuration is based
    primarily on environment variables which are not modifiable from
    outside of the process.

    """
    _state.clear()


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
    buf.write('/'.join(quote(str(p), safe=PATH_SAFE_CHARS) for p in path))

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
    _state.determine_discovery_method()
    env_service = service.upper()
    details = (_state.discovery_style, _state.discovery_parameters[0])
    if details[0] == DiscoveryMethod.CONSUL:
        buf.write('http://')
        buf.write(service)
        buf.write('.service.')
        buf.write(details[1])
        buf.write('.consul')
    elif details[0] == DiscoveryMethod.CONSUL_AGENT:
        response = _state.session.get(
            'consul://agent/v1/catalog/service/{0}'.format(service))
        response.raise_for_status()
        body = response.json()
        if not body:  # service does not exist in consul
            raise errors.ServiceNotFoundError(service)
        else:
            buf.write('http://')
            buf.write(body[0]['ServiceName'])
            buf.write('.service.')
            buf.write(body[0]['Datacenter'])
            buf.write('.consul:')
            buf.write(str(body[0]['ServicePort']))
    elif details[0] == DiscoveryMethod.K8S:
        buf.write('http://')
        buf.write(service + '.')
        buf.write(details[1])
        buf.write('.svc.cluster.local')
    else:
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
    return quote(v.encode('utf-8'))
