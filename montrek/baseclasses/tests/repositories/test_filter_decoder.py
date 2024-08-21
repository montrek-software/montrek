from django.db.models import Q
from django.test import TestCase
from baseclasses.repositories.filter_decoder import FilterDecoder


class TestFilterDecoder(TestCase):
    def test_decode_dict_to_filter(self):
        filter_dict = {
            "field1__exact": {
                "filter_negate": False,
                "filter_value": "value1",
            }
        }
        test_query_list = FilterDecoder.decode_dict_to_query_list(filter_dict)
        self.assertTrue(isinstance(test_query_list, list))
        self.assertEqual(len(test_query_list), 1)
        self.assertTrue(isinstance(test_query_list[0], Q))
        self.assertEqual(
            test_query_list[0].__dict__, Q(field1__exact="value1").__dict__
        )

    def test_decode_dict_to_filter__multiple_statements(self):
        filter_dict = {
            "field1__exact": {
                "filter_negate": False,
                "filter_value": "value1",
            },
            "field2__exact": {
                "filter_negate": False,
                "filter_value": "value2",
            },
        }
        test_query_list = FilterDecoder.decode_dict_to_query_list(filter_dict)
        self.assertTrue(isinstance(test_query_list, list))
        self.assertEqual(len(test_query_list), 2)
        self.assertTrue(isinstance(test_query_list[0], Q))
        self.assertEqual(
            test_query_list[0].__dict__, Q(field1__exact="value1").__dict__
        )
        self.assertTrue(isinstance(test_query_list[1], Q))
        self.assertEqual(
            test_query_list[1].__dict__, Q(field2__exact="value2").__dict__
        )

    def test_decode_dict_to_filter__negate(self):
        filter_dict = {
            "field1__exact": {
                "filter_negate": True,
                "filter_value": "value1",
            }
        }
        test_query_list = FilterDecoder.decode_dict_to_query_list(filter_dict)
        self.assertTrue(isinstance(test_query_list, list))
        self.assertEqual(len(test_query_list), 1)
        self.assertTrue(isinstance(test_query_list[0], Q))
        self.assertEqual(
            test_query_list[0].__dict__, (~Q(field1__exact="value1")).__dict__
        )

    def test_decode_dict_to_filter__multiple_statements_negate(self):
        filter_dict = {
            "field1__exact": {
                "filter_negate": True,
                "filter_value": "value1",
            },
            "field2__exact": {
                "filter_negate": True,
                "filter_value": "value2",
            },
        }
        test_query_list = FilterDecoder.decode_dict_to_query_list(filter_dict)
        self.assertTrue(isinstance(test_query_list, list))
        self.assertEqual(len(test_query_list), 2)
        self.assertTrue(isinstance(test_query_list[0], Q))
        self.assertEqual(
            test_query_list[0].__dict__, (~Q(field1__exact="value1")).__dict__
        )
        self.assertTrue(isinstance(test_query_list[1], Q))
        self.assertEqual(
            test_query_list[1].__dict__, (~Q(field2__exact="value2")).__dict__
        )

    def test_decode_dict_to_filter__mixed_negate(self):
        filter_dict = {
            "field1__exact": {
                "filter_negate": True,
                "filter_value": "value1",
            },
            "field2__exact": {
                "filter_negate": False,
                "filter_value": "value2",
            },
        }
        test_query_list = FilterDecoder.decode_dict_to_query_list(filter_dict)
        self.assertTrue(isinstance(test_query_list, list))
        self.assertEqual(len(test_query_list), 2)
        self.assertTrue(isinstance(test_query_list[0], Q))
        self.assertEqual(
            test_query_list[0].__dict__, (~Q(field1__exact="value1")).__dict__
        )
        self.assertTrue(isinstance(test_query_list[1], Q))
        self.assertEqual(
            test_query_list[1].__dict__, Q(field2__exact="value2").__dict__
        )

    def test_decode_dict_to_filter__empty(self):
        filter_dict = {}
        test_query_list = FilterDecoder.decode_dict_to_query_list(filter_dict)
        self.assertTrue(isinstance(test_query_list, list))
        self.assertEqual(len(test_query_list), 0)

    def test_decode_dict_to_filter__or_statement(self):
        filter_dict = {
            "or": {
                "field1__exact": {
                    "filter_negate": False,
                    "filter_value": "value1",
                },
                "field2__exact": {
                    "filter_negate": False,
                    "filter_value": "value2",
                },
            }
        }
        test_query_list = FilterDecoder.decode_dict_to_query_list(filter_dict)
        self.assertTrue(isinstance(test_query_list, list))
        self.assertEqual(len(test_query_list), 1)
        self.assertTrue(isinstance(test_query_list[0], Q))
        self.assertEqual(
            test_query_list[0].__dict__,
            (Q(field1__exact="value1") | Q(field2__exact="value2")).__dict__,
        )
