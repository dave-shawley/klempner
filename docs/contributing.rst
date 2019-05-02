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
.. code-block:: sh

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
   ..........................
   ----------------------------------------------------------------------
   Ran 26 tests in 0.069s

   OK
   (env) $ coverage report
   Name                   Stmts   Miss Branch BrPart  Cover   Missing
   ------------------------------------------------------------------
   klempner/__init__.py       2      0      2      0   100%
   klempner/compat.py         8      0      0      0   100%
   klempner/config.py        71      0     22      0   100%
   klempner/errors.py        11      0      0      0   100%
   klempner/url.py           88      0     32      0   100%
   ------------------------------------------------------------------
   TOTAL                    180      0     56      0   100%

.. code-block:: sh

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

Checking code style
-------------------
.. code-block:: sh

   (env) $ yapf -dpr klempner setup.py tests
   (env) $ flake8

Building documents
------------------
.. code-block:: sh

   (env) $ ./setup.py build_sphinx

