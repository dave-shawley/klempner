from __future__ import unicode_literals

import unittest

from tests import helpers
import klempner.config
import klempner.url


class SimpleEnvironmentTests(helpers.EnvironmentMixin, unittest.TestCase):
    def setUp(self):
        super(SimpleEnvironmentTests, self).setUp()
        klempner.url.reset_cache()
        self.setenv('KLEMPNER_DISCOVERY',
                    klempner.config.DiscoveryMethod.ENV_VARS)

    def test_that_scheme_envvar_is_honored(self):
        self.setenv('ACCOUNT_SCHEME', 'https')
        url = klempner.url.build_url('account')
        self.assertEqual('https://account/', url)

    def test_that_host_envvar_is_honored(self):
        self.setenv('ACCOUNT_HOST', '10.2.12.23')
        url = klempner.url.build_url('account')
        self.assertEqual('http://10.2.12.23/', url)

    def test_that_port_envvar_is_honored(self):
        self.setenv('ACCOUNT_PORT', '11223')
        url = klempner.url.build_url('account')
        self.assertEqual('http://account:11223/', url)

    def test_that_docker_linked_port_is_accepted(self):
        self.setenv('ACCOUNT_PORT', 'tcp://10.2.12.23:11223')
        url = klempner.url.build_url('account')
        self.assertEqual('http://10.2.12.23:11223/', url)

    def test_that_host_is_taken_from_docker_linked_port(self):
        self.setenv('ACCOUNT_HOST', '10.2.12.23')
        self.setenv('ACCOUNT_PORT', 'tcp://10.2.12.24:11223')
        url = klempner.url.build_url('account')
        self.assertEqual('http://10.2.12.23:11223/', url)

    def test_that_scheme_is_set_from_port(self):
        self.setenv('ACCOUNT_HOST', '10.2.12.23')
        self.setenv('ACCOUNT_PORT', '443')
        url = klempner.url.build_url('account')
        self.assertEqual('https://10.2.12.23:443/', url)

    def test_that_scheme_is_taken_from_docker_linked_port(self):
        self.setenv('ACCOUNT_PORT', 'tcp://10.2.12.23:443')
        url = klempner.url.build_url('account')
        self.assertEqual('https://10.2.12.23:443/', url)
