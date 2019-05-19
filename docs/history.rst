Release history
===============

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
