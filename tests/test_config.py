import logging
import unittest

from klempner import errors, url

import tests.helpers


class DirectConfigTests(unittest.TestCase):
    def tearDown(self):
        super(DirectConfigTests, self).tearDown()
        url.config.reset()

    def test_that_unknown_discovery_method_raises_configuration_error(self):
        with self.assertRaises(errors.ConfigurationError) as context:
            url.config.configure('unknown-option')
        self.assertEqual('discovery_style',
                         context.exception.configuration_name)
        self.assertEqual('unknown-option',
                         context.exception.configuration_value)

    def test_that_simple_discovery_is_parameterless(self):
        url.config.configure(url.DiscoveryMethod.SIMPLE)
        self.assertEqual({}, url.config._parameters)

    def test_that_consul_discovery_without_datacenter_fails(self):
        with self.assertRaises(errors.ConfigurationError) as context:
            url.config.configure(url.DiscoveryMethod.CONSUL)
        self.assertEqual('datacenter', context.exception.configuration_name)
        self.assertIs(None, context.exception.configuration_value)

    def test_that_consul_agent_discovery_without_datacenter_fails(self):
        with self.assertRaises(errors.ConfigurationError) as context:
            url.config.configure(url.DiscoveryMethod.CONSUL_AGENT)
        self.assertEqual('datacenter', context.exception.configuration_name)
        self.assertIs(None, context.exception.configuration_value)


class ConfigByEnvironTests(tests.helpers.EnvironmentMixin, unittest.TestCase):
    def tearDown(self):
        super(ConfigByEnvironTests, self).tearDown()
        url.config.reset()

    def test_that_unknown_discovery_method_raises_configuration_error(self):
        self.setenv('KLEMPNER_DISCOVERY', 'unknown-option')
        with self.assertRaises(errors.ConfigurationError) as context:
            url.config.configure_from_environment()
        self.assertEqual('discovery_style',
                         context.exception.configuration_name)
        self.assertEqual('unknown-option',
                         context.exception.configuration_value)

    def test_that_consul_discovery_without_datacenter_fails(self):
        self.setenv('KLEMPNER_DISCOVERY', url.DiscoveryMethod.CONSUL)
        self.unsetenv('CONSUL_DATACENTER')
        with self.assertRaises(errors.ConfigurationError) as context:
            url.config.configure_from_environment()
        self.assertEqual('CONSUL_DATACENTER',
                         context.exception.configuration_name)
        self.assertIs(None, context.exception.configuration_value)

    def test_that_consul_agent_discovery_without_http_addr_fails(self):
        self.setenv('KLEMPNER_DISCOVERY', url.DiscoveryMethod.CONSUL_AGENT)
        self.unsetenv('CONSUL_HTTP_ADDR')
        with self.assertRaises(errors.ConfigurationError) as context:
            url.config.configure_from_environment()
        self.assertEqual('CONSUL_HTTP_ADDR',
                         context.exception.configuration_name)
        self.assertIs(None, context.exception.configuration_value)


class ErrorHandlingTests(unittest.TestCase):
    def test_that_warning_is_logged_for_unused_parameters(self):
        log_messages = []

        class Recorder(logging.Handler):
            def emit(self, record):
                log_messages.append(record.getMessage())

        handler = Recorder()
        url.config.logger.addHandler(handler)
        self.addCleanup(url.config.logger.removeHandler, handler)

        url.config.configure(url.DiscoveryMethod.SIMPLE, unusued='parameter')
        for message in log_messages:
            if 'simple does not accept additional parameters' in message:
                break
        else:
            self.fail('expected to find warning message in ' +
                      repr(log_messages))
