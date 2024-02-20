from django.test import TestCase
import datetime
from baseclasses.dataclasses.history_data_tags import HistoryDataTag, HistoryDataTagSet
from user.tests.factories.montrek_user_factories import MontrekUserFactory


class HistoryDataTagTestCase(TestCase):
    def test_history_data_tag(self):
        history_data_tag = HistoryDataTag(
            change_date=datetime.datetime(2020, 1, 1), user_ids=[1, 2, 3]
        )
        self.assertEqual(history_data_tag.change_date, datetime.datetime(2020, 1, 1))
        self.assertEqual(history_data_tag.user_ids, [1, 2, 3])

    def test_history_data_tag_get_user_string(self):
        user1 = MontrekUserFactory.create()
        user2 = MontrekUserFactory.create()
        user3 = MontrekUserFactory.create()

        history_data_tag = HistoryDataTag(
            change_date=datetime.datetime(2020, 1, 1),
            user_ids=[user1.id, user2.id, user3.id],
        )
        self.assertEqual(
            history_data_tag.get_user_string(), f"{user1.id},{user2.id},{user3.id}"
        )


class HistoryDataTagSetTestCase(TestCase):
    def test_history_data_tag_set(self):
        history_data_tag_set = HistoryDataTagSet()
        history_data_tag_set.append(datetime.datetime(2020, 1, 1), 1)
        history_data_tag_set.append(datetime.datetime(2020, 1, 2), 2)
        self.assertEqual(len(history_data_tag_set), 2)
        self.assertEqual(
            history_data_tag_set[0].change_date, datetime.datetime(2020, 1, 1)
        )
        self.assertEqual(history_data_tag_set[0].user_ids, [1])
        self.assertEqual(
            history_data_tag_set[1].change_date, datetime.datetime(2020, 1, 2)
        )
        self.assertEqual(history_data_tag_set[1].user_ids, [2])

    def test_history_data_tag_update(self):
        history_data_tag_set = HistoryDataTagSet()
        history_data_tag_set.append(datetime.datetime(2020, 1, 1), 1)
        history_data_tag_set.append(datetime.datetime(2020, 1, 1), 1)
        history_data_tag_set.append(datetime.datetime(2020, 1, 2), 2)
        history_data_tag_set.append(datetime.datetime(2020, 1, 1), 3)
        self.assertEqual(len(history_data_tag_set), 2)
        self.assertEqual(
            history_data_tag_set[0].change_date, datetime.datetime(2020, 1, 1)
        )
        self.assertEqual(history_data_tag_set[0].user_ids, [1, 3])
        self.assertEqual(
            history_data_tag_set[1].change_date, datetime.datetime(2020, 1, 2)
        )
        self.assertEqual(history_data_tag_set[1].user_ids, [2])
