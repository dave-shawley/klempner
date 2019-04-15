from __future__ import unicode_literals

import unittest

from tests import helpers
import klempner.url


class SimpleEnvironmentTests(helpers.EnvironmentMixin, unittest.TestCase):
    def setUp(self):
        super(SimpleEnvironmentTests, self).setUp()
        klempner.url.reset_cache()

    def test_that_scheme_envvar_is_honored(self):
        self.setenv('ACCOUNT_SCHEME', 'https')
        url = klempner.url.build_url('account')
        self.assertEqual('https://account/', url)

    def test_that_host_envvar_is_honored(self):
        self.setenv('ACCOUNT_HOST', '10.2.12.23')
        url = klempner.url.build_url('account')
        self.assertEqual('http://10.2.12.23/', url)

    def test_that_port_envvar_is_honored(self):
        self.setenv('ACCOUNT_HOST', '10.2.12.23')
        self.setenv('ACCOUNT_PORT', '11223')
        url = klempner.url.build_url('account')
        self.assertEqual('http://10.2.12.23:11223/', url)

    def test_that_port_envvar_is_ignored_unless_host_is_set(self):
        self.unsetenv('ACCOUNT_HOST')
        self.setenv('ACCOUNT_PORT', '11223')
        url = klempner.url.build_url('account')
        self.assertEqual('http://account/', url)

    def test_that_docker_formatted_port_is_accepted(self):
        self.setenv('ACCOUNT_HOST', '10.2.12.23')
        self.setenv('ACCOUNT_PORT', '10.2.12.23:11223')
        url = klempner.url.build_url('account')
        self.assertEqual('http://10.2.12.23:11223/', url)

    def test_that_host_is_taken_from_port_in_docker_formatted_port(self):
        self.setenv('ACCOUNT_HOST', '10.2.12.23')
        self.setenv('ACCOUNT_PORT', '10.2.12.24:11223')
        url = klempner.url.build_url('account')
        self.assertEqual('http://10.2.12.24:11223/', url)
