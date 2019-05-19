Configuration
=============
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

.. envvar:: CONSUL_HTTP_TOKEN

   Configures the option authorization token for interacting with the
   Consul HTTP API.  If this environment variable is set, then it is
   sent as a HTTP ``Beaerer`` authorization header.

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

