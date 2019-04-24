import unittest

from klempner import errors, url

import tests.helpers


class ConfigTests(tests.helpers.EnvironmentMixin, unittest.TestCase):
    def tearDown(self):
        super(ConfigTests, self).tearDown()
        url.config.reset()

    def test_that_discovery_style_is_cached(self):
        sentinel = object()
        url.config.discovery_style = sentinel
        url.config.determine_discovery_method()
        self.assertIs(sentinel, url.config.discovery_style)

    def test_that_unknown_discovery_method_raises_configuration_error(self):
        self.setenv('KLEMPNER_DISCOVERY', 'unknown-option')
        with self.assertRaises(errors.ConfigurationError):
            url.config.determine_discovery_method()
