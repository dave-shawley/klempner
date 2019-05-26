Discovery mechanisms
====================

.. _simple-discovery-method:

simple
------
The *simple* discovery method simply inserts the service name into the
:token:`host` portion of the URL directly.  The scheme is hard-coded and
the port is left as the protocol default (unspecified).

.. productionlist::
   scheme    : "http"
   host      : service-name

.. code-block::
   :caption: Simple discovery method

   url = klempner.url.build_url('account')
   print(url)  # http://account/

This is the default discovery mechanism which is little more than a wrapper
around :func:`~urllib.parse.urlunsplit`.  It might be useful in Kubernetes
for namespace-local services but I am not even convinced that it can be used
there.  Call :func:`klempner.config.configure` or set the
:envvar:`KLEMPNER_DISCOVERY` environment variable to set a more capable method.

.. _environment-discovery-method:

environment
-----------
The *environment* discovery method uses environment variables to configure
service endpoints.  When :func:`~klempner.url.build_url` is called for a
service, several environment variables will be used to build the URL if they
are defined.  The service name is upper-cased and each of the following
suffixes are appended to calculate the URL compoment.

+-------------+-------------------------------+---------------------+
| Suffix      | URL component                 | Default             |
+-------------+-------------------------------+---------------------+
| ``_HOST``   | host portion of the authority | name of the service |
+-------------+-------------------------------+---------------------+
| ``_PORT``   | port portion of the authority | *omitted*           |
+-------------+-------------------------------+---------------------+
| ``_SCHEME`` | scheme                        | *see below*         |
+-------------+-------------------------------+---------------------+

The URL scheme defaults to looking up the port number in the
``klempner.config.URL_SCHEME_MAP`` dictionary.  If the port number is not
in the dictionary, then ``http`` is used as a default.

.. code-block::
   :caption: Environment variable discovery

   os.environ['KLEMPNER_DISCOVERY'] = 'environment'
   os.environ['ACCOUNT_HOST'] = '10.2.12.23'
   os.environ['ACCOUNT_PORT'] = '11223'
   url = klempner.url.build_url('account')
   print(url)  # http://10.2.12.23:11223/


.. rubric:: Special case for docker/kubernetes linking

If you are still using version 1 docker-compose files or you are deploying
in a Kubernetes cluster, then the ``..._PORT`` environment variable is set
something very much not a port number.  For example, if there is a service
named ``foo`` is available on the host ``1.2.3.4`` and port ``5678``, then
``$FOO_PORT`` is set to ``tcp://1.2.3.4:5678``.  Needless to say that this
is not a simple port number and should not be treated as such.  See the
`kubernetes service discovery`_ documentation for more detail.  If the port
environment variable matches this pattern, then the host and port are parsed
from the URL.

.. code-block::
   :caption: Docker-linked environment variables

   # mimic linkage to a single service
   os.environ['ACCOUNT_PORT'] = 'tcp://172.17.0.2:8000'
   os.environ['ACCOUNT_PORT_8000_TCP'] = 'tcp://172.17.0.2:8000'
   os.environ['ACCOUNT_PORT_8000_TCP_ADDR'] = '172.17.0.2'
   os.environ['ACCOUNT_PORT_8000_TCP_PORT'] = '8000'
   os.environ['ACCOUNT_PORT_8000_TCP_PROTO'] = 'tcp'

   os.environ['KLEMPNER_DISCOVERY'] = 'environment'
   url = klempner.url.build_url('account')
   print(url)  # http://172.17.0.2:8000/

.. _kubernetes service discovery: https://kubernetes.io/docs/concepts
   /services-networking/service/#environment-variables

.. _consul-discovery-method:

consul
------
The *consul* discovery method combines the service name and the consul data
center to build the DNS CNAME that consul advertises:

.. productionlist::
   scheme    : "http"
   host      : service-name ".service." data-center ".consul"

The data center name is configured by the :envvar:`CONSUL_DATACENTER`
environment variable.

.. code-block:: python
   :caption: Consul URL templating

   os.environ['KLEMPNER_DISCOVERY'] = 'consul'
   os.environ['CONSUL_DATACENTER'] = 'production'
   url = klempner.url.build_url('account')
   print(url)  # http://account.service.production.consul/

.. _consul-agent-discovery-method:

consul+agent
------------
The *consul-agent* discovery method retrieves the service information from
a consul agent by `listing the available nodes`_ from the agent.  The
service record includes the host name, port number, and configured metadata.

Instead of selecting a host name from the available nodes, the advertised
DNS name is used (see `consul-discovery-method`_ section) as the *host portion*.

The *port number* from the first advertised node is used.

If the protocol is included in the service metadata, then it is used as the
*scheme* for the URL.  Otherwise, the port number is mapped through the
:data:`~klempner.config.URL_SCHEME_MAP` to determine the scheme to apply.

The consul agent endpoint is configured by the :envvar:`CONSUL_AGENT_URL`
environment variable.

.. code-block:: python
   :caption: Consul agent lookup

   os.environ['CONSUL_AGENT_URL'] = 'http://127.0.0.1:8500'

   os.environ['KLEMPNER_DISCOVERY'] = 'consul+agent'
   url = klempner.url.build_url('account')
   print(url)  # http://account.service.production.consul:8000/

.. _listing the available nodes: https://www.consul.io/api/catalog.html
   #list-nodes-for-service

.. _kubernetes-discovery-method:

kubernetes
----------
The *kubernetes* discovery method is similar to the
:ref:`consul-discovery-method` discovery method except that it generates DNS
CNAMEs that `Kubernetes advertises`_.

.. productionlist::
   host      : service-name "." namespace ".svc.cluster.local"

The namespace is configured by the :envvar:`KUBERNETES_NAMESPACE` environment
variable.

.. code-block:: python
   :caption: Kubernetes URL templating

   os.environ['KLEMPNER_DISCOVERY'] = 'kubernetes'
   url = klempner.url.build_url('account')
   print(url)  # http://account.default.svc.local/

   os.environ['KUBERNETES_NAMESPACE'] = 'my-team'
   url = klempner.url.build_url('account')
   print(url)  # http://account.my-team.svc.local/

.. _Kubernetes advertises: https://kubernetes.io/docs/concepts
   /services-networking/dns-pod-service/#services
