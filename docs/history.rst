Release history
===============

Next Release
------------
- :compare:`0.0.3...master`
- Add support for using https with consul by replacing ``CONSUL_HTTP_ADDR``
  with :envvar:`CONSUL_AGENT_URL`

0.0.3 (25 May 2019)
-------------------
- :compare:`0.0.2...0.0.3`
- Add support for the :envvar:`CONSUL_HTTP_TOKEN` environment variable.
- Set ``User-Agent`` when sending requests to Consul.
- Rework documentation.

0.0.2 (19 May 2019)
-------------------
- :compare:`0.0.1...0.0.2`
- Add :data:`~klempner.config.URL_SCHEME_MAP` so that URL schemes can be
  easily configured.
- Separate the :ref:`environment-discovery-method` method out from the
  :ref:`simple-discovery-method` method.  Previously the simple method would
  fall back to using environment variables if they were set.

0.0.1 (5 May 2019)
------------------
- :compare:`0.0.0...0.0.1`
- Implement :ref:`simple-discovery-method`, :ref:`consul-discovery-method`,
  :ref:`consul-agent-discovery-method`, :ref:`kubernetes-discovery-method`
  discovery methods.
