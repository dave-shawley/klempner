import unittest

from klempner import errors, url

import tests.helpers


class ConfigTests(tests.helpers.EnvironmentMixin, unittest.TestCase):
    def tearDown(self):
        super(ConfigTests, self).tearDown()
        url.config.reset()

    def test_that_unknown_discovery_method_raises_configuration_error(self):
        with self.assertRaises(errors.ConfigurationError) as context:
            url.config.discovery_style = 'unknown-option'
        self.assertEqual('discovery_style',
                         context.exception.configuration_name)
        self.assertEqual('unknown-option',
                         context.exception.configuration_value)

    def test_that_discovery_style_is_cached(self):
        # NB - assumes that setting a style changes url.config.parameters
        url.config.discovery_style = url.DiscoveryMethod.SIMPLE
        url.config.parameters['fake'] = 'parameter'

        url.config.discovery_style = url.DiscoveryMethod.SIMPLE
        self.assertEqual({'fake': 'parameter'}, url.config.parameters)

    def test_that_simple_discovery_is_parameterless(self):
        url.config.discovery_style = url.DiscoveryMethod.SIMPLE
        self.assertEqual({}, url.config.parameters)

    def test_that_consul_discovery_without_datacenter_fails(self):
        self.unsetenv('CONSUL_DATACENTER')
        with self.assertRaises(errors.ConfigurationError) as context:
            url.config.discovery_style = url.DiscoveryMethod.CONSUL
        self.assertEqual('CONSUL_DATACENTER',
                         context.exception.configuration_name)
        self.assertIs(None, context.exception.configuration_value)

    def test_that_consul_agent_discovery_with_addr_fails(self):
        self.unsetenv('CONSUL_HTTP_ADDR')
        with self.assertRaises(errors.ConfigurationError) as context:
            url.config.discovery_style = url.DiscoveryMethod.CONSUL_AGENT
        self.assertEqual('CONSUL_HTTP_ADDR',
                         context.exception.configuration_name)
        self.assertIs(None, context.exception.configuration_value)
