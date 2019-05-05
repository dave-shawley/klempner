Developers guide
================

Setting up your environment
---------------------------
.. code-block:: sh

   $ python -mvenv env
   $ ./env/bin/pip install -qe '.[dev]'
   $ cp ci/git-pre-commit .git/hooks/pre-commit
   $ chmod u+x .git/hooks/pre-commit

Running tests
-------------

Local tests
~~~~~~~~~~~
.. note::

   Locally running tests without starting the integration depedencies
   does not cover all of the library source code as shown in the following
   snippets.  See `Integration testing`_ below for full test coverage.

.. code-block:: sh
   :caption: Testing with coverage reporting

   $ . ./env/bin/activate
   (env) $ coverage run setup.py test -q
   running test
   running egg_info
   writing klempner.egg-info/PKG-INFO
   writing dependency_links to klempner.egg-info/dependency_links.txt
   writing requirements to klempner.egg-info/requires.txt
   writing top-level names to klempner.egg-info/top_level.txt
   reading manifest file 'klempner.egg-info/SOURCES.txt'
   reading manifest template 'MANIFEST.in'
   writing manifest file 'klempner.egg-info/SOURCES.txt'
   running build_ext
   ........s...............
   ----------------------------------------------------------------------
   Ran 23 tests in 0.005s

   OK (skipped=1)
   (env) $ coverage report
   Name                   Stmts   Miss Branch BrPart  Cover   Missing
   ------------------------------------------------------------------
   klempner/__init__.py       2      0      2      0   100%
   klempner/compat.py         8      0      0      0   100%
   klempner/config.py        71      4     22      0    96%   127-130
   klempner/errors.py        11      2      0      0    82%   10-11
   klempner/url.py           88     18     32      1    81%   25-29, 125-142, 124->125
   ------------------------------------------------------------------
   TOTAL                    180     24     56      1    88%

.. code-block:: sh
   :caption: Using tox to ensure version compatibility

   (env) $ tox -p auto
   ✔ OK py37 in 1.885 seconds
   ✔ OK py27 in 1.934 seconds
   ✔ OK py35 in 2.081 seconds
   ✔ OK py36 in 2.11 seconds
   ___________________________________________________ summary ___________________________________________________
     py27: commands succeeded
     py35: commands succeeded
     py36: commands succeeded
     py37: commands succeeded
     congratulations :)

Integration testing
~~~~~~~~~~~~~~~~~~~
The integration tests require that you have some additional services running.
This project runs the dependencies using `docker`_ so you will need access to
a docker host.  You can install docker from `hub.docker.com`_ for the majority
of operating systems.  Once docker is installed, running the integrated tests
is simple.

.. _docker: https://www.docker.com/products/docker-desktop
.. _hub.docker.com: https://hub.docker.com/search?q=&type=edition
   &offering=community

.. code-block:: sh
   :caption: Full coverage testing in docker-compose

   $ docker-compose run --rm integration-test
   Creating network "klempner_default" with the default driver
   Creating klempner_consul_1 ... done
   Building package...
   Installing...
   Running tests..........................
   Name                   Stmts   Miss Branch BrPart  Cover   Missing
   ------------------------------------------------------------------
   klempner/__init__.py       2      0      2      0   100%
   klempner/compat.py         8      0      0      0   100%
   klempner/config.py        71      0     22      0   100%
   klempner/errors.py        11      0      0      0   100%
   klempner/url.py           88      0     32      0   100%
   ------------------------------------------------------------------
   TOTAL                    180      0     56      0   100%
   ----------------------------------------------------------------------
   Ran 26 tests in 0.648s

   OK

Checking code style
-------------------
.. code-block:: sh

   (env) $ yapf -dpr klempner setup.py tests
   (env) $ flake8

Building documents
------------------
.. code-block:: sh

   (env) $ ./setup.py build_sphinx

