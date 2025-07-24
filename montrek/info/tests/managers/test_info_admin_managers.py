from django.test import TestCase
from info.managers.info_admin_managers import InfoAdminManager


class TestInfoAdminManager(TestCase):
    def setUp(self):
        self.info_admin_manager = InfoAdminManager({})
        self.info_admin_manager.collect_report_elements()

    def test_admin_links(self):
        link_table_manager = self.info_admin_manager.report_elements[0]
        test_df = link_table_manager.get_df()
        self.assertEqual(test_df.columns.tolist(), ["System", "Description", "Link"])
        self.assertEqual(test_df.shape, (3, 3))
