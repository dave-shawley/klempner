from __future__ import unicode_literals

import os
import random
import unittest
import uuid

import requests

import klempner.config
import klempner.errors
import klempner.url

from tests import helpers


class SimpleConsulTests(helpers.EnvironmentMixin, unittest.TestCase):
    def test_that_consul_datacenter_environment_sets_datacenter_name(self):
        klempner.url.reset_cache()
        self.setenv('KLEMPNER_DISCOVERY',
                    klempner.config.DiscoveryMethod.CONSUL)
        env = str(uuid.uuid4())
        self.setenv('CONSUL_DATACENTER', env)
        self.assertEqual('http://account.service.{0}.consul/'.format(env),
                         klempner.url.build_url('account'))


class AgentBasedTests(helpers.EnvironmentMixin, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super(AgentBasedTests, cls).setUpClass()
        cls.session = requests.Session()

        try:
            cls.agent_url = 'http://{0}/v1/agent'.format(
                os.environ['CONSUL_HTTP_ADDR'])
        except KeyError:
            raise unittest.SkipTest('Consul agent is not present')

        response = cls.session.get(cls.agent_url + '/self')
        response.raise_for_status()
        body = response.json()
        cls.datacenter = body['Config']['Datacenter']

    def setUp(self):
        super(AgentBasedTests, self).setUp()
        klempner.url.reset_cache()
        self.setenv('KLEMPNER_DISCOVERY',
                    klempner.config.DiscoveryMethod.CONSUL_AGENT)
        self.unsetenv('CONSUL_DATACENTER')
        self._service_ids = set()

    def tearDown(self):
        super(AgentBasedTests, self).tearDown()
        for service_id in list(self._service_ids):
            self.deregister_service(service_id, ignore_error=True)
        klempner.url.reset_cache()

    def register_service(self, meta=None, port=None):
        service_id = str(uuid.uuid4())
        service_details = {
            'ID': service_id,
            'Name': 's' + service_id.replace('-', '').lower(),
            'Address': '10.0.0.1',
            'Port': port or random.randint(10000, 20000),
            'Datacenter': self.datacenter,
        }
        if meta:
            service_details['Meta'] = meta
        response = self.session.put(self.agent_url + '/service/register',
                                    json=service_details)
        response.raise_for_status()
        self._service_ids.add(service_id)
        return service_details

    def deregister_service(self, service_id, ignore_error=False):
        response = self.session.put(
            self.agent_url + '/service/deregister/{0}'.format(service_id))
        if not ignore_error:
            response.raise_for_status()
        self._service_ids.discard(service_id)

    def test_that_details_are_fetched_from_consul_agent(self):
        service_info = self.register_service()
        self.assertEqual(
            'http://{Name}.service.{Datacenter}.consul:{Port}/'.format(
                **service_info),
            klempner.url.build_url(service_info['Name']),
        )

    def test_that_nonexistent_service_raises_exception(self):
        with self.assertRaises(klempner.errors.ServiceNotFoundError):
            klempner.url.build_url(str(uuid.uuid4()))

    def test_that_service_lookup_is_cached(self):
        service_info = self.register_service()
        expected = 'http://{Name}.service.{Datacenter}.consul:{Port}/'.format(
            **service_info)
        self.assertEqual(expected,
                         klempner.url.build_url(service_info['Name']))

        self.deregister_service(service_info['ID'])
        self.assertEqual(expected,
                         klempner.url.build_url(service_info['Name']))

    def test_that_scheme_set_by_metadata(self):
        service_info = self.register_service(meta={'protocol': 'https'})
        expected = 'https://{Name}.service.{Datacenter}.consul:{Port}/'.format(
            **service_info)
        self.assertEqual(expected,
                         klempner.url.build_url(service_info['Name']))

    def test_that_scheme_set_by_port(self):
        for port, scheme in klempner.config.URL_SCHEME_MAP.items():
            service_info = self.register_service(port=port)
            self.assertEqual(
                '{scheme}://{Name}.service.{Datacenter}.consul:{port}/'.format(
                    port=port, scheme=scheme, **service_info),
                klempner.url.build_url(service_info['Name']))

    def test_that_consul_token_is_sent_as_auth_header(self):
        interceptor = helpers.Interceptor(klempner.url._state.session,
                                          'prepare_request')
        self.setenv('CONSUL_HTTP_TOKEN', 'my-token')
        service_info = self.register_service()
        expected = 'http://{Name}.service.{Datacenter}.consul:{Port}/'.format(
            **service_info)
        self.assertEqual(expected,
                         klempner.url.build_url(service_info['Name']))

        self.assertEqual(1, interceptor.call_count)
        self.assertEqual('Bearer my-token',
                         interceptor.result.headers['Authorization'])

    def test_that_user_agent_is_set(self):
        interceptor = helpers.Interceptor(klempner.url._state.session,
                                          'prepare_request')
        service_info = self.register_service()
        klempner.url.build_url(service_info['Name'])

        self.assertEqual(1, interceptor.call_count)
        self.assertEqual('klempner/{}'.format(klempner.version),
                         interceptor.result.headers['User-Agent'])
