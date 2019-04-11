import os
import unittest

import klempner


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


class SimpleEnvironmentTests(EnvironmentMixin, unittest.TestCase):
    def test_that_scheme_envvar_is_honored(self):
        self.setenv('ACCOUNT_SCHEME', 'https')
        url = klempner.build_url('account')
        self.assertEqual('https://account/', url)

    def test_that_host_envvar_is_honored(self):
        self.setenv('ACCOUNT_HOST', '10.2.12.23')
        url = klempner.build_url('account')
        self.assertEqual('http://10.2.12.23/', url)

    def test_that_port_envvar_is_honored(self):
        self.setenv('ACCOUNT_HOST', '10.2.12.23')
        self.setenv('ACCOUNT_PORT', '11223')
        url = klempner.build_url('account')
        self.assertEqual('http://10.2.12.23:11223/', url)

    def test_that_port_envvar_is_ignored_unless_host_is_set(self):
        self.unsetenv('ACCOUNT_HOST')
        self.setenv('ACCOUNT_PORT', '11223')
        url = klempner.build_url('account')
        self.assertEqual('http://account/', url)

    def test_that_docker_formatted_port_is_accepted(self):
        self.setenv('ACCOUNT_HOST', '10.2.12.23')
        self.setenv('ACCOUNT_PORT', '10.2.12.23:11223')
        url = klempner.build_url('account')
        self.assertEqual('http://10.2.12.23:11223/', url)

    def test_that_host_is_taken_from_port_in_docker_formatted_port(self):
        self.setenv('ACCOUNT_HOST', '10.2.12.23')
        self.setenv('ACCOUNT_PORT', '10.2.12.24:11223')
        url = klempner.build_url('account')
        self.assertEqual('http://10.2.12.24:11223/', url)
