from __future__ import unicode_literals

import unittest

import klempner.url


class QueryParameterTests(unittest.TestCase):
    def setUp(self):
        super(QueryParameterTests, self).setUp()
        klempner.url.reset_cache()

    def test_that_query_parameters_are_encoded(self):
        url = klempner.url.build_url('some-service', arg1='value',
                                     arg2='with space',
                                     arg3='r\u00E9sum\u00E9')
        self.assertEqual(
            'http://some-service/'
            '?arg1=value&arg2=with%20space&arg3=r%C3%A9sum%C3%A9',
            url,
        )

    def test_that_sequences_are_expanded(self):
        url = klempner.url.build_url(
            'some-service',
            list_arg=['one', 'two'],
            set_arg=set(['one', 'two']),
            tuple_arg=('one', 'two'),
        )
        self.assertEqual(
            'http://some-service/'
            '?list_arg=one&list_arg=two'
            '&set_arg=one&set_arg=two'
            '&tuple_arg=one&tuple_arg=two',
            url,
        )

    def test_that_mapping_query_params_fail(self):
        with self.assertRaises(ValueError):
            klempner.url.build_url('some-service', val={'one': 1, 'two': '2'})


class PathTests(unittest.TestCase):
    def setUp(self):
        super(PathTests, self).setUp()
        klempner.url.reset_cache()

    def test_that_path_elements_are_quoted(self):
        url = klempner.url.build_url(
            'some-service', 'with spaces', 'other:interesting@chars',
            '(sub!&*+,;=!delims)', 'unreserved-._~chars', 'quoted<>{}/chars')
        self.assertEqual(
            'http://some-service'
            '/with%20spaces'
            '/other:interesting@chars'
            '/(sub!&*+,;=!delims)'
            '/unreserved-._~chars'
            '/quoted%3C%3E%7B%7D%2Fchars',
            url,
        )

    def test_that_non_string_path_elements_are_stringified(self):
        url = klempner.url.build_url('some-service', 1234, True, None)
        self.assertEqual('http://some-service/1234/True/None', url)

    def test_that_no_path_always_ends_with_slash(self):
        self.assertEqual('http://some-service/',
                         klempner.url.build_url('some-service'))
        self.assertEqual('http://some-service/?q=1',
                         klempner.url.build_url('some-service', q=1))
