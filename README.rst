klempner
========
Constructs URLs that targeting other services.

This library makes building URLs for inter-service communication safer
and easier to build.

URL building
------------

.. code-block:: python

   url = klempner.build_url('account', 'path', 'with spaces',
                            query='arg',  multi=['arg', 'support'])
   print(url)
   # http://account/path/with%20spaces?query=arg&multi=arg&multi=support

Discovery examples
------------------

Unconfigured usage
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   url = klempner.build_url('account')
   print(url)  # http://account/

This isn't very useful but if you do not configure the discovery mechanism,
then ``build_url`` assumes that the requested service is accessible directly
by name.

Consul service discovery
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   os.environ['CONSUL_DATACENTER'] = 'production'
   os.environ['KLEMPNER_DISCOVERY'] = 'consul'
   url = klempner.build_url('account')
   print(url)  # http://account.service.production.consul/

Kubernetes service discovery
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   os.environ['KLEMPNER_DISCOVERY'] = 'kubernetes'
   url = klempner.build_url('account')
   print(url)  # http://account.default.svc.cluster.local/

.. code-block:: python

   os.environ['KUBERNETES_NAMESPACE'] = 'my-team'
   os.environ['KLEMPNER_DISCOVERY'] = 'kubernetes'
   url = klempner.build_url('account')
   print(url)  # http://account.my-team.svc.cluster.local/

Docker-compose service discovery
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   os.environ['COMPOSE_PROJECT_NAME'] = 'foo'
   os.environ['KLEMPNER_DISCOVERY'] = 'docker-compose'
   url = klempner.build_url('account')
   print(url)  # http://127.0.0.1:32867/

This discovery mechanism discovers IP and port numbers for services using
the Docker API.  ``build_url`` retrieves the list of services from the docker
host, filters the list using the "com.docker.compose.project" label, and
selects the service using the "com.docker.compose.service" label.

Environment variable discovery
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   os.environ['ACCOUNT_HOST'] = '10.2.12.23'
   os.environ['ACCOUNT_PORT'] = '11223'
   url = klempner.build_url('account')
   print(url)  # http://10.2.12.23:11223/
