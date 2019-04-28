import logging
import unittest

from klempner import config, errors

import tests.helpers


class DirectConfigTests(unittest.TestCase):
    def tearDown(self):
        super(DirectConfigTests, self).tearDown()
        config.reset()

    def test_that_unknown_discovery_method_raises_configuration_error(self):
        with self.assertRaises(errors.ConfigurationError) as context:
            config.configure('unknown-option')
        self.assertEqual('discovery_style',
                         context.exception.configuration_name)
        self.assertEqual('unknown-option',
                         context.exception.configuration_value)

    def test_that_simple_discovery_is_parameterless(self):
        config.configure(config.DiscoveryMethod.SIMPLE)
        _, parameters = config.get_discovery_details()
        self.assertEqual({}, parameters)

    def test_that_consul_discovery_without_datacenter_fails(self):
        with self.assertRaises(errors.ConfigurationError) as context:
            config.configure(config.DiscoveryMethod.CONSUL)
        self.assertEqual('datacenter', context.exception.configuration_name)
        self.assertIs(None, context.exception.configuration_value)

    def test_that_consul_agent_discovery_without_datacenter_fails(self):
        with self.assertRaises(errors.ConfigurationError) as context:
            config.configure(config.DiscoveryMethod.CONSUL_AGENT)
        self.assertEqual('datacenter', context.exception.configuration_name)
        self.assertIs(None, context.exception.configuration_value)


class ConfigByEnvironTests(tests.helpers.EnvironmentMixin, unittest.TestCase):
    def tearDown(self):
        super(ConfigByEnvironTests, self).tearDown()
        config.reset()

    def test_that_unknown_discovery_method_raises_configuration_error(self):
        self.setenv('KLEMPNER_DISCOVERY', 'unknown-option')
        with self.assertRaises(errors.ConfigurationError) as context:
            config.configure_from_environment()
        self.assertEqual('discovery_style',
                         context.exception.configuration_name)
        self.assertEqual('unknown-option',
                         context.exception.configuration_value)

    def test_that_consul_discovery_without_datacenter_fails(self):
        self.setenv('KLEMPNER_DISCOVERY', config.DiscoveryMethod.CONSUL)
        self.unsetenv('CONSUL_DATACENTER')
        with self.assertRaises(errors.ConfigurationError) as context:
            config.configure_from_environment()
        self.assertEqual('CONSUL_DATACENTER',
                         context.exception.configuration_name)
        self.assertIs(None, context.exception.configuration_value)

    def test_that_consul_agent_discovery_without_http_addr_fails(self):
        self.setenv('KLEMPNER_DISCOVERY', config.DiscoveryMethod.CONSUL_AGENT)
        self.unsetenv('CONSUL_HTTP_ADDR')
        with self.assertRaises(errors.ConfigurationError) as context:
            config.configure_from_environment()
        self.assertEqual('CONSUL_HTTP_ADDR',
                         context.exception.configuration_name)
        self.assertIs(None, context.exception.configuration_value)


class ErrorHandlingTests(unittest.TestCase):
    def test_that_warning_is_logged_for_unused_parameters(self):
        log_messages = []

        class Recorder(logging.Handler):
            def emit(self, record):
                log_messages.append(record.getMessage())

        logger = logging.getLogger('klempner.configure')
        handler = Recorder()
        logger.addHandler(handler)
        self.addCleanup(logger.removeHandler, handler)

        config.configure(config.DiscoveryMethod.SIMPLE, unusued='parameter')
        for message in log_messages:
            if 'simple does not accept additional parameters' in message:
                break
        else:
            self.fail('expected to find warning message in ' +
                      repr(log_messages))
