from __future__ import unicode_literals

import unittest
import uuid

import klempner.config
from tests import helpers
import klempner.url


class SimpleK8sTests(helpers.EnvironmentMixin, unittest.TestCase):
    def setUp(self):
        super(SimpleK8sTests, self).setUp()
        klempner.url.reset_cache()
        self.setenv('KLEMPNER_DISCOVERY', klempner.config.DiscoveryMethod.K8S)
        self.setenv('KUBERNETES_NAMESPACE', 'development')

    def test_that_k8s_namespace_environment_sets_datacenter_name(self):
        env = str(uuid.uuid4())
        self.setenv('KUBERNETES_NAMESPACE', env)
        self.assertEqual('http://account.{0}.svc.cluster.local/'.format(env),
                         klempner.url.build_url('account'))

    def test_that_k8s_namespace_defaults_when_envvar_is_not_set(self):
        self.unsetenv('KUBERNETES_NAMESPACE')
        self.assertEqual('http://account.default.svc.cluster.local/',
                         klempner.url.build_url('account'))
