from django.test import TestCase
from baseclasses.templatetags import data_table_filters as dtf

class TestDataTableFilters(TestCase):

    def test__get_dotted_attr_or_arg(self):
        """
        Test that the function returns the correct value when the
        attribute is a dotted path.
        """
        class TestClass():
            def __init__(self, attr):
                self.attr = attr

        test_obj = TestClass(attr='test_value')
        self.assertEqual(dtf._get_dotted_attr_or_arg(test_obj, 'attr'), 'test_value')
        class SecondTestClass():
            def __init__(self, attr):
                self.test_class = TestClass(attr=attr)
        second_test_obj = SecondTestClass(attr='test_value')
        self.assertEqual(dtf._get_dotted_attr_or_arg(second_test_obj, 'test_class.attr'), 'test_value')

        self.assertEqual(dtf._get_dotted_attr_or_arg(test_obj, 'no_attr'), 'no_attr')
