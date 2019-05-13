Library configuration
=====================
This library can be configured by environment variables or programmatically
via the :func:`~klempner.config.configure` function.  If the
:func:`~klempner.config.configure` is not called explicitly, then
:func:`~klempner.config.configure_from_environment` will be called implicitly
the first time that :func:`~klempner.url.build_url` is called.

The following grammar snippet for a URL comes from :rfc:`3986`.  The goal of
:func:`klempner.url.build_url` is creating properly formed URLs so it is very
important to understand precisely how the different discovery methods work.
The following sub-sections describe how each discovery method populates the
:token:`authority` portion of the URLs.

.. productionlist::
   URI       : scheme ":" hier-part [ "?" query ] [ "#" fragment ]
   hier-part : "//" authority path-empty
             : path-absolute
             : path-rootless
             : path-empty
   authority : [ userinfo "@" ] host [ ":" port ]

Discovery methods
-----------------

.. _simple-discovery-method:

simple
~~~~~~
The *simple* discovery method simply inserts the service name into the
:token:`host` portion of the URL directly.  The scheme is hard-coded and
the port is left as the protocol default (unspecified).

.. productionlist::
   scheme    : "http"
   host      : service-name

.. _consul-discovery-method:

consul
~~~~~~
The *consul* discovery method combines the service name and the consul data
center to build the DNS CNAME that consul advertises:

.. productionlist::
   scheme    : "http"
   host      : service-name ".service." data-center ".consul"

The data center name is configured by the :envvar:`CONSUL_DATACENTER`
environment variable.

.. _consul-agent-discovery-method:

consul+agent
~~~~~~~~~~~~
The *consul-agent* discovery method retrieves the service information from
a consul agent by `listing the available nodes`_ from the agent.  The
service record includes the host name, port number, and configured metadata.

Instead of selecting a host name from the available nodes, the advertised
DNS name is used (see `consul-discovery-method`_ section) as the *host portion*.

The *port number* from the first advertised node is used.

If the protocol is included in the service metadata, then it is used as the
*scheme* for the URL.  Otherwise, the port number is mapped through the
:data:`~klempner.config.URL_SCHEME_MAP` to determine the scheme to apply.

The consul agent endpoint is configured by the :envvar:`CONSUL_HTTP_ADDR`
environment variable.

.. _listing the available nodes: https://www.consul.io/api/catalog.html
   #list-nodes-for-service

.. _environment-discovery-method:

environment
~~~~~~~~~~~
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

.. _kubernetes service discovery: https://kubernetes.io/docs/concepts
   /services-networking/service/#environment-variables

.. _kubernetes-discovery-method:

kubernetes
~~~~~~~~~~
The *kubernetes* discovery method is similar to the
:ref:`consul-discovery-method` discovery method except that it generates DNS
CNAMEs that `Kubernetes advertises`_.

.. productionlist::
   host      : service-name "." namespace ".svc.cluster.local"

The namespace is configured by the :envvar:`KUBERNETES_NAMESPACE` environment
variable.

.. _Kubernetes advertises: https://kubernetes.io/docs/concepts
   /services-networking/dns-pod-service/#services

Environment variables
---------------------
The library can be configured based on the environment by calling the
:func:`~klempner.config.configure_from_environment` function explicitly.

.. envvar:: KLEMPNER_DISCOVERY

   Controls the discovery method that the library will used.  The following
   values are understood:

      - :ref:`consul-discovery-method`
      - :ref:`consul-agent-discovery-method`
      - :ref:`environment-discovery-method`
      - :ref:`kubernetes-discovery-method`
      - :ref:`simple-discovery-method`

.. envvar:: CONSUL_DATACENTER

   Configures the datacenter used for Consul-based discovery methods.  This
   variable is required if :envvar:`KLEMPNER_DISCOVERY` is set to
   :ref:`consul-discovery-method`.

.. envvar:: CONSUL_HTTP_ADDR

   Configures the Consul agent address and port used by the
   :ref:`consul-agent-discovery-method` method.

.. envvar:: KUBERNETES_NAMESPACE

   Configures the name of the Kubernetes namespace used by
   :ref:`kubernetes-discovery-method` to generate URLs.  If this variable is
   not set, the value of ``default`` is used.

URL schemes
-----------
The default scheme for all URLs is ``http``.  If a port number is available
for the configured discovery scheme, then the port number is looked up in
:data:`klempner.config.URL_SCHEME_MAP` and the result is used as the URL
scheme.  The initial content of the mapping contains many of the `IANA
registered schemes`_ as well as a number of other commonly used ones (e.g.,
``postgresql``, ``amqp``).

You can adjust the *port to scheme* mapping to match your needs.  If you
want to disable scheme mapping altogether, simply clear the mapping when
your application initializes:

.. code-block:: python

   klempner.config.URL_SCHEME_MAP.clear()

Use the ``update`` operation if you need to augment the mapping or override
specific entries:

.. code-block:: python

   klempner.config.URL_SCHEME_MAP.update({
      5672: 'rabbitmq',
      15672: 'rabbitmq-admin',
   })

The mapping is a simple :class:`dict` so you can manipulate it using the
standard methods.  It is not cached anywhere in the library implementation
so all modifications are immediately reflected in API calls.

.. _IANA registered schemes: https://www.iana.org/assignments/uri-schemes
   /uri-schemes.xhtml
