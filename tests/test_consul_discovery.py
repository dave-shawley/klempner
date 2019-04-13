from __future__ import unicode_literals

import unittest
import uuid

from tests import helpers
import klempner


class SimpleConsulTests(helpers.EnvironmentMixin, unittest.TestCase):
    def setUp(self):
        super(SimpleConsulTests, self).setUp()
        self.setenv('KLEMPNER_DISCOVERY', 'consul')
        self.setenv('CONSUL_DATACENTER', 'development')

    def test_that_consul_datacenter_environment_sets_datacenter_name(self):
        env = str(uuid.uuid4())
        self.setenv('CONSUL_DATACENTER', env)
        self.assertEqual('http://account.service.{0}.consul/'.format(env),
                         klempner.build_url('account'))

    def test_that_consul_discovery_is_disabled_when_envvar_is_not_set(self):
        self.unsetenv('CONSUL_DATACENTER')
        self.assertEqual('http://account/', klempner.build_url('account'))
