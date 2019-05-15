Release history
===============

`Next Release`_
---------------
- Add :data:`~klempner.config.URL_SCHEME_MAP` so that URL schemes can be
  easily configured.
- Separate the :ref:`environment-discovery-method` method out from the
  :ref:`simple-discovery-method` method.  Previously the simple method would
  fall back to using environment variables if they were set.

`0.0.1`_ (5 May 2019)
---------------------
- Implement :ref:`simple-discovery-method`, :ref:`consul-discovery-method`,
  :ref:`consul-agent-discovery-method`, :ref:`kubernetes-discovery-method`
  discovery methods.


.. _Next Release: https://github.com/dave-shawley/klempner/compare/0.0.1...master
.. _0.0.1: https://github.com/dave-shawley/klempner/compare/0.0.0...0.0.1
