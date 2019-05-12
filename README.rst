klempner
========
Constructs URLs that targeting other services.

This library makes building URLs for inter-service communication safer
and easier to build.

URL building
------------

.. code-block:: python

   url = klempner.url.build_url('account', 'path', 'with spaces',
                                query='arg',  multi=['arg', 'support'])
   print(url)
   # http://account/path/with%20spaces?query=arg&multi=arg&multi=support

``build_url`` takes care of formatting the path and query parameters correctly
in addition to discovering the service name.  In this example, the service name
is used as-is (see *Unconfigured usage* below).  The real power in ``build_url``
is its ability to discover the scheme, host name, and port number based on the
operating environment.

``build_url`` uses the ``http`` scheme by default.  If the port is determined
by the discovery mechanism, then the scheme is set to the service name returned
from `socket.getservbyport`_.

.. _socket.getservbyport: https://docs.python.org/3/library/socket.html
   #socket.getservbyport

Discovery examples
------------------

Unconfigured usage
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   url = klempner.url.build_url('account')
   print(url)  # http://account/

This isn't very useful but if you do not configure the discovery mechanism,
then ``build_url`` assumes that the requested service is accessible directly
by name.

Consul service discovery
~~~~~~~~~~~~~~~~~~~~~~~~
The basic form of using consul is not *discovery* at all.  It is simply
URL construction that follows the naming convention that Consul's DNS
interface exposes.

.. code-block:: python

   os.environ['KLEMPNER_DISCOVERY'] = 'consul'
   os.environ['CONSUL_DATACENTER'] = 'production'
   url = klempner.url.build_url('account')
   print(url)  # http://account.service.production.consul/

If you append ``+agent`` to the discovery method, then ``build_url`` will
connect to a Consul agent and retrieve the port number for services.  If the
port has a registered service associated with it, then the service name will
be used as the scheme.

Assuming that the *account* service is registered in consul with a service port
of 8000::

.. code-block:: python

   os.environ['KLEMPNER_DISCOVERY'] = 'consul+agent'
   url = klempner.url.build_url('account')
   print(url)  # http://account.service.production.consul:8000/

Now let's look at what happens for a RabbitMQ connection::

.. code-block:: python

   url = klempner.url.build_url('rabbit')
   print(url)  # amqp://rabbit.service.production.consul:5432/

The scheme is derived by calling ``socket.getservbyport(5432)``

The library will connect to the agent specified by the ``CONSUL_HTTP_ADDR``
environment variable.  If the environment variable is not specified, then the
agent listening on the localhost will be used.

Kubernetes service discovery
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   os.environ['KLEMPNER_DISCOVERY'] = 'kubernetes'
   url = klempner.url.build_url('account')
   print(url)  # http://account.default.svc.cluster.local/

.. code-block:: python

   os.environ['KLEMPNER_DISCOVERY'] = 'kubernetes'
   os.environ['KUBERNETES_NAMESPACE'] = 'my-team'
   url = klempner.url.build_url('account')
   print(url)  # http://account.my-team.svc.cluster.local/

Docker-compose service discovery
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   os.environ['KLEMPNER_DISCOVERY'] = 'docker-compose'
   os.environ['COMPOSE_PROJECT_NAME'] = 'foo'
   url = klempner.url.build_url('account')
   print(url)  # http://127.0.0.1:32867/

This discovery mechanism discovers IP and port numbers for services using
the Docker API.  ``build_url`` retrieves the list of services from the docker
host, filters the list using the "com.docker.compose.project" label, and
selects the service using the "com.docker.compose.service" label.

Environment variable discovery
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This form of discovery uses environment variables with the service name encoded
into them:

.. code-block:: python

   os.environ['ACCOUNT_HOST'] = '10.2.12.23'
   os.environ['ACCOUNT_PORT'] = '11223'
   url = klempner.url.build_url('account')
   print(url)  # http://10.2.12.23:11223/

For a service named ``adder``, the following table lists the environment
variables that are applicable:

+------------------+-------------------------------+-------------+
| Name             | URL component                 | Default     |
+------------------+-------------------------------+-------------+
| ``ADDER_HOST``   | host portion of the authority | *none*      |
+------------------+-------------------------------+-------------+
| ``ADDER_PORT``   | port portion of the authority | *omitted*   |
+------------------+-------------------------------+-------------+
| ``ADDER_SCHEME`` | scheme                        | *see below* |
+------------------+-------------------------------+-------------+

The URL scheme defaults to looking up the port number in the
``klempner.config.URL_SCHEME_MAP`` dictionary.  If the port number is not
in the dictionary, then ``http`` is used as a default.

.. code-block:: python

   os.environ['ACCOUNT_HOST'] = '10.2.12.23'
   os.environ['ACCOUNT_PORT'] = '443'
   url = klempner.url.build_url('account')
   print(url)  # https://10.2.12.23:443/

