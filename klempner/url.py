from __future__ import unicode_literals

import logging
import os

import requests.adapters

import cachetools
from klempner import compat, errors

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


class Config:
    def __init__(self):
        self._discovery_style = None
        self.parameters = {}

    def reset(self):
        self.discovery_style = None

    @property
    def discovery_style(self):
        return self._discovery_style

    @discovery_style.setter
    def discovery_style(self, new_style):
        logger = logging.getLogger(__package__)
        if new_style is None:
            self._discovery_style = None
            self.parameters.clear()
        elif new_style == self._discovery_style:
            return
        elif new_style == DiscoveryMethod.SIMPLE:
            self._discovery_style = new_style
            self.parameters.clear()
        elif new_style == DiscoveryMethod.CONSUL:
            try:
                datacenter = os.environ['CONSUL_DATACENTER']
                self._discovery_style = new_style
                self.parameters['datacenter'] = datacenter
            except KeyError:
                logger.warning(
                    'discovery style set to %s but CONSUL_DATACENTER is not '
                    'set: falling back to simple URL construction', new_style)
                self.discovery_style = DiscoveryMethod.SIMPLE
        elif new_style == DiscoveryMethod.CONSUL_AGENT:
            try:
                url = compat.urlunparse(
                    ('http', os.environ['CONSUL_HTTP_ADDR'], '/v1/agent/self',
                     None, None, None))
            except KeyError as error:
                logger.error('discovery style %s requires %s to be set',
                             new_style, error.args[0].upper())
                raise errors.ConfigurationError(error.args[0].upper(), None)
            response = requests.get(url)
            response.raise_for_status()
            body = response.json()
            self._discovery_style = new_style
            self.parameters['datacenter'] = body['Config']['Datacenter']
        elif new_style == DiscoveryMethod.K8S:
            namespace = os.environ.get('KUBERNETES_NAMESPACE', 'default')
            self._discovery_style = new_style
            self.parameters['namespace'] = namespace
        else:
            raise errors.ConfigurationError('discovery_style', new_style)

    def determine_discovery_method(self):
        if self.discovery_style is not None:
            return
        self.discovery_style = os.environ.get('KLEMPNER_DISCOVERY',
                                              DiscoveryMethod.SIMPLE)


config = Config()


class ConsulAgentAdapter(requests.adapters.HTTPAdapter):
    """Adapter that sends `consul://` requests to a consul agent."""

    def send(self, request, stream=False, timeout=None, verify=True, cert=None,
             proxies=None):
        _, _, path, params, query, fragment = compat.urlparse(request.url)
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
    config.determine_discovery_method()
    env_service = service.upper()
    if config.discovery_style == DiscoveryMethod.CONSUL:
        buf.write('http://')
        buf.write(service)
        buf.write('.service.')
        buf.write(config.parameters['datacenter'])
        buf.write('.consul')
    elif config.discovery_style == DiscoveryMethod.CONSUL_AGENT:
        sentinel = object()
        body = _state.discovery_cache.get(service, sentinel)
        if body is sentinel:
            response = _state.session.get(
                'consul://agent/v1/catalog/service/{0}'.format(service))
            response.raise_for_status()
            body = response.json()
            _state.discovery_cache[service] = body

        if not body:  # service does not exist in consul
            raise errors.ServiceNotFoundError(service)
        else:
            buf.write('http://')
            buf.write(body[0]['ServiceName'])
            buf.write('.service.')
            buf.write(body[0]['Datacenter'])
            buf.write('.consul:')
            buf.write(str(body[0]['ServicePort']))
    elif config.discovery_style == DiscoveryMethod.K8S:
        buf.write('http://')
        buf.write(service + '.')
        buf.write(config.parameters['namespace'])
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
    if not isinstance(v, compat.TEXT_TYPES):
        v = str(v)
    return compat.quote(v.encode('utf-8'))
