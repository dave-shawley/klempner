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
   host      : service-name

.. _consul-discovery-method:

consul
~~~~~~
The *consul* discovery method combines the service name and the consul data
center to build the DNS CNAME that consul advertises:

.. productionlist::
   host      : service-name ".service." data-center ".consul"

The data center name is configured by the :envvar:`CONSUL_DATACENTER`
environment variable.

.. _consul-agent-discovery-method:

consul+agent
~~~~~~~~~~~~
The *consul-agent* discovery method is similar to the
:ref:`consul-discovery-method` method except that the data-center is discovered
from a consul agent instead of an environment variable.

.. productionlist::
   host      : service-name ".service." data-center ".consul"

The consul agent endpoint is configured by the :envvar:`CONSUL_HTTP_ADDR`
environment variable.

.. _kubernetes-discovery-method:

kubernetes
~~~~~~~~~~
The *kubernetes* discovery method is similar to the
:ref:`consul-discovery-method` discovery method except that it generates DNS
CNAMEs that `Kubernetes advertises`_.

.. productionlist::
   host      : service-name "." namespace ".svc.cluster.local"

The namespace is configured by the :envvar:`KUBERNETES_NAMESPACE` environemnt
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

      - :ref:`simple-discovery-method`
      - :ref:`consul-discovery-method`
      - :ref:`consul-agent-discovery-method`
      - :ref:`kubernetes-discovery-method`

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
