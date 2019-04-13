import os
import unittest


class EnvironmentMixin(unittest.TestCase):
    def setUp(self):
        super(EnvironmentMixin, self).setUp()
        self._environment = {}

    def tearDown(self):
        super(EnvironmentMixin, self).tearDown()
        for name, value in self._environment.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value

    def setenv(self, name, value):
        self._environment.setdefault(name, os.environ.get(name, None))
        os.environ[name] = value

    def unsetenv(self, name):
        self._environment.setdefault(name, os.environ.get(name, None))
        os.environ.pop(name, None)
