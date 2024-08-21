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
        test_query = FilterDecoder.decode_dict_to_query(filter_dict)
        self.assertTrue(isinstance(test_query, Q))
        self.assertEqual(test_query.__dict__, Q(Q(field1__exact="value1")).__dict__)

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
        test_query = FilterDecoder.decode_dict_to_query(filter_dict)
        self.assertTrue(isinstance(test_query, Q))
        self.assertEqual(
            test_query.__dict__,
            (Q(Q(field1__exact="value1"), Q(field2__exact="value2"))).__dict__,
        )

    def test_decode_dict_to_filter__negate(self):
        filter_dict = {
            "field1__exact": {
                "filter_negate": True,
                "filter_value": "value1",
            }
        }
        test_query = FilterDecoder.decode_dict_to_query(filter_dict)
        self.assertTrue(isinstance(test_query, Q))
        self.assertEqual(test_query.__dict__, (Q(~Q(field1__exact="value1"))).__dict__)

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
        test_query = FilterDecoder.decode_dict_to_query(filter_dict)
        self.assertTrue(isinstance(test_query, Q))
        expected_query = Q(~Q(field1__exact="value1"), ~Q(field2__exact="value2"))
        self.assertEqual(
            test_query.__dict__,
            expected_query.__dict__,
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
        test_query = FilterDecoder.decode_dict_to_query(filter_dict)
        self.assertTrue(isinstance(test_query, Q))
        expected_query = Q(~Q(field1__exact="value1"), Q(field2__exact="value2"))
        self.assertEqual(
            test_query.__dict__,
            expected_query.__dict__,
        )

    def test_decode_dict_to_filter__empty(self):
        filter_dict = {}
        test_query = FilterDecoder.decode_dict_to_query(filter_dict)
        self.assertTrue(isinstance(test_query, Q))
        expected_query = Q()
        self.assertEqual(
            test_query.__dict__,
            expected_query.__dict__,
        )

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
        test_query = FilterDecoder.decode_dict_to_query(filter_dict)
        self.assertTrue(isinstance(test_query, Q))
        expected_query = Q(Q(field1__exact="value1") | Q(field2__exact="value2"))
        self.assertEqual(
            test_query.__dict__,
            expected_query.__dict__,
        )

    def test_decode_dict_to_filter__or_statement_negate(self):
        filter_dict = {
            "or": {
                "field1__exact": {
                    "filter_negate": False,
                    "filter_value": "value1",
                },
                "field2__exact": {
                    "filter_negate": True,
                    "filter_value": "value2",
                },
            }
        }
        test_query = FilterDecoder.decode_dict_to_query(filter_dict)
        self.assertTrue(isinstance(test_query, Q))
        expected_query = Q(Q(field1__exact="value1") | ~Q(field2__exact="value2"))
        self.assertEqual(
            test_query.__dict__,
            expected_query.__dict__,
        )

    def test_decode_dict_to_filter__or_statement_compose(self):
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
            },
            "field3__exact": {
                "filter_negate": False,
                "filter_value": "value3",
            },
        }
        test_query = FilterDecoder.decode_dict_to_query(filter_dict)
        self.assertTrue(isinstance(test_query, Q))
        expected_query = Q(
            (Q(field1__exact="value1") | Q(field2__exact="value2")),
            Q(field3__exact="value3"),
        )
        self.assertEqual(
            test_query.__dict__,
            expected_query.__dict__,
        )
