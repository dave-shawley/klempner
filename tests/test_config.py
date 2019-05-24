import logging
import os
import unittest
try:
    import unittest.mock as mock
except ImportError:
    import mock

from klempner import config, errors, url, version

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

    def test_that_consul_agent_discovery_uses_consul_token(self):
        self.setenv('KLEMPNER_DISCOVERY', config.DiscoveryMethod.CONSUL_AGENT)
        self.setenv('CONSUL_HTTP_ADDR', '127.0.0.1:1')
        self.setenv('CONSUL_HTTP_TOKEN', 'some-token')
        with mock.patch('klempner.config.requests.get') as requests_get:
            response = mock.Mock()
            response.json.return_value = {'Config': {'Datacenter': 'dc1'}}
            requests_get.return_value = response
            config.configure_from_environment()

        self.assertEqual(1, requests_get.call_count)
        positional, kwargs = requests_get.call_args_list[0]
        self.assertIn('headers', kwargs)
        self.assertIn('Authorization', kwargs['headers'])
        self.assertEqual('bearer some-token',
                         kwargs['headers']['Authorization'].lower())

    @unittest.skipUnless('CONSUL_HTTP_ADDR' in os.environ,
                         'Consul agent is not present')
    def test_that_consul_agent_discovery_includes_user_agent(self):
        self.setenv('KLEMPNER_DISCOVERY', config.DiscoveryMethod.CONSUL_AGENT)
        with mock.patch('klempner.config.requests.get') as requests_get:
            response = mock.Mock()
            response.json.return_value = {'Config': {'Datacenter': 'dc1'}}
            requests_get.return_value = response
            config.configure_from_environment()

        self.assertEqual(1, requests_get.call_count)
        positional, kwargs = requests_get.call_args_list[0]
        self.assertIn('headers', kwargs)
        self.assertIn('User-Agent', kwargs['headers'])
        self.assertEqual('klempner/{}'.format(version),
                         kwargs['headers']['User-Agent'])


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


class SchemeMappingTests(tests.helpers.EnvironmentMixin, unittest.TestCase):
    def setUp(self):
        self._saved_scheme_map = config.URL_SCHEME_MAP.copy()
        super(SchemeMappingTests, self).setUp()

    def tearDown(self):
        super(SchemeMappingTests, self).tearDown()
        config.URL_SCHEME_MAP.clear()
        config.URL_SCHEME_MAP.update(self._saved_scheme_map)

    def test_that_mapping_can_be_disabled(self):
        config.URL_SCHEME_MAP.clear()
        config.configure(config.DiscoveryMethod.ENV_VARS)
        self.setenv('ACCOUNT_HOST', 'account.example.com')
        self.setenv('ACCOUNT_PORT', '443')
        self.assertEqual('http://account.example.com:443/',
                         url.build_url('account'))

    def test_that_mapping_can_be_overridden(self):
        config.URL_SCHEME_MAP[5672] = 'rabbitmq'
        config.configure(config.DiscoveryMethod.ENV_VARS)
        self.setenv('ACCOUNT_HOST', 'account.example.com')
        self.setenv('ACCOUNT_PORT', '5672')
        self.assertEqual('rabbitmq://account.example.com:5672/',
                         url.build_url('account'))
