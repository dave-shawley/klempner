import logging
import os

import requests

from klempner import compat, errors

URL_SCHEME_MAP = {
    5672: 'amqp',  # https://www.rabbitmq.com/uri-spec.html
    21: 'ftp',  # https://tools.ietf.org/html/rfc1738
    70: 'gopher',  # https://tools.ietf.org/html/rfc4266
    80: 'http',  # https://tools.ietf.org/html/rfc7230#section-2.7.1
    443: 'https',  # https://tools.ietf.org/html/rfc7230#section-2.7.2
    1344: 'icap',  # https://tools.ietf.org/html/rfc3507#section-4.2
    631: 'ipp',  # https://tools.ietf.org/html/rfc3510
    389: 'ldap',  # https://tools.ietf.org/html/rfc4516
    636: 'ldaps',  # https://tools.ietf.org/html/rfc4516
    # https://docs.mongodb.com/manual/reference/connection-string/
    27017: 'mongodb',
    3306: 'mysql',
    119: 'nntp',  # https://tools.ietf.org/html/rfc5538
    110: 'pop',  # https://tools.ietf.org/html/rfc2384
    # https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING
    5432: 'postgresql',
    6379: 'redis',  # https://www.iana.org/assignments/uri-schemes/prov/redis
    873: 'rsync',  # https://tools.ietf.org/html/rfc5781
    554: 'rtsp',  # https://tools.ietf.org/html/rfc7826#section-4.2
    322: 'rtsps',  # https://tools.ietf.org/html/rfc7826#section-4.2
    25: 'smtp',  # https://tools.ietf.org/html/draft-melnikov-smime-msa-to-mda
    161: 'snmp',  # https://tools.ietf.org/html/rfc4088
    22: 'ssh',  # https://tools.ietf.org/html/draft-ietf-secsh-scp-sftp-ssh-uri
    23: 'telnet',  # https://tools.ietf.org/html/rfc4248
    69: 'tftp',  # https://tools.ietf.org/html/rfc3617
    3372: 'tip',  # https://tools.ietf.org/html/rfc2371
    5900: 'vnc',  # https://tools.ietf.org/html/rfc7869
    602: 'xmlrpc.beep',  # https://tools.ietf.org/html/rfc3529#section-5.1
}
"""Mapping of port number to URL scheme.

This dictionary is used to identify the URL scheme based on the port number
when a port number is available.  Users of the library MAY modify the content
of this dictionary **at any time**.

"""


class DiscoveryMethod(object):
    """Available discovery methods."""

    SIMPLE = 'simple'
    """Build URLs using service name as host name."""

    CONSUL = 'consul'
    """Build consul-based service URLs."""

    CONSUL_AGENT = 'consul+agent'
    """Build consul-based service URLs using a consul agent."""

    ENV_VARS = 'environment'
    """Build URLs based on _HOST, _PORT, and _SCHEME environment variables."""

    K8S = 'kubernetes'
    """Build Kubernetes cluster-based service URLs."""

    DEFAULT = SIMPLE

    UNSET = object()

    AVAILABLE = (CONSUL, CONSUL_AGENT, ENV_VARS, K8S, SIMPLE, UNSET)


_discovery_method = DiscoveryMethod.UNSET
_discovery_parameters = {}


def reset():
    """Reset URL construction parameters."""
    configure(DiscoveryMethod.UNSET)


def ensure_configured():
    """Configure from the environment if currently unconfigured."""
    if _discovery_method is DiscoveryMethod.UNSET:
        configure_from_environment()


def configure(discovery_method, **parameters):
    """Configure the discovery method directly.

    :param discovery_method: method to use
    :param parameters: parameters required for the selected
        method
    :raises: :exc:`klempner.errors.ConfigurationError` if a required
        parameter is not provided

    """
    logger = logging.getLogger(__package__).getChild('configure')

    def require_parameter(name):
        try:
            return parameters.pop(name)
        except KeyError:
            logger.error('parameter %s is required by discovery method %s',
                         name, discovery_method)
            raise errors.ConfigurationError(name, None)

    logger.debug('configuring for discovery_method %s with parameters=%r',
                 discovery_method, parameters)
    incoming_parameters = {}
    if discovery_method == DiscoveryMethod.CONSUL:
        incoming_parameters['datacenter'] = require_parameter('datacenter')
    elif discovery_method == DiscoveryMethod.CONSUL_AGENT:
        incoming_parameters['datacenter'] = require_parameter('datacenter')
    elif discovery_method == DiscoveryMethod.K8S:
        incoming_parameters['namespace'] = require_parameter('namespace')
    elif discovery_method not in DiscoveryMethod.AVAILABLE:
        raise errors.ConfigurationError('discovery_style', discovery_method)

    global _discovery_method, _discovery_parameters
    if _discovery_method is DiscoveryMethod.UNSET:
        logger.info('setting discovery method to %r with parameters=%r',
                    discovery_method, incoming_parameters)
    else:
        logger.info(
            'setting discovery method: current_method=%r new_method=%r '
            'parameters=%r', _discovery_method, discovery_method,
            incoming_parameters)
    _discovery_method = discovery_method
    _discovery_parameters.clear()
    _discovery_parameters.update(incoming_parameters)
    if parameters:
        logger.warning(
            'discovery style %s does not accept additional parameters, '
            '%d extra parameters were passed to configure', discovery_method,
            len(parameters))


def configure_from_environment():
    """Set the discovery method from ``$KLEMPNER_DISCOVERY``.

    This method configures the library based on the
    :envvar:`KLEMPNER_DISCOVERY` environment variable.  If the
    environment variable is not set, then the "simple" configuration
    is used.

    """
    logger = logging.getLogger(__package__).getChild(
        'configure_from_environment')
    new_method = os.environ.get('KLEMPNER_DISCOVERY', DiscoveryMethod.SIMPLE)
    logger.debug('configuring from environment: discovery_method=%s',
                 new_method)

    def require_envvar(name):
        try:
            return os.environ[name]
        except KeyError:
            logger.error(
                'discovery method %s requires the %s environment variable',
                new_method, name)
            raise errors.ConfigurationError(name, None)

    parameters = {}
    if new_method == DiscoveryMethod.CONSUL:
        parameters['datacenter'] = require_envvar('CONSUL_DATACENTER')
    elif new_method == DiscoveryMethod.CONSUL_AGENT:
        url = compat.urlunparse(('http', require_envvar('CONSUL_HTTP_ADDR'),
                                 '/v1/agent/self', None, None, None))
        response = requests.get(url)
        response.raise_for_status()
        body = response.json()
        parameters['datacenter'] = body['Config']['Datacenter']
    elif new_method == DiscoveryMethod.K8S:
        parameters['namespace'] = os.environ.get('KUBERNETES_NAMESPACE',
                                                 'default')
    elif new_method not in DiscoveryMethod.AVAILABLE:
        raise errors.ConfigurationError('discovery_style', new_method)

    configure(new_method, **parameters)


def get_discovery_details():
    """Retrieve the configured method and parameters.

    :rtype: tuple(str, dict)

    """
    return _discovery_method, _discovery_parameters.copy()
