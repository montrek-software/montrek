import copy
import io
import logging
import logging.config
import re

from django.conf import settings
from django.test import SimpleTestCase


class TestLoggingSettings(SimpleTestCase):
    def setUp(self):
        super().setUp()
        self.stream = io.StringIO()
        config = copy.deepcopy(settings.LOGGING)
        config["handlers"]["console"]["stream"] = self.stream
        config["handlers"]["console"]["level"] = "DEBUG"
        logging.config.dictConfig(config)
        self.addCleanup(logging.config.dictConfig, settings.LOGGING)

    def test_line_shows_time_logger_and_level(self):
        logging.getLogger("montrek_example.some_module").error("broken")

        self.assertRegex(
            self.stream.getvalue(),
            r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} - "
            r"montrek_example\.some_module - ERROR - broken\n$",
        )

    def test_db_backends_warning_printed_once(self):
        logging.getLogger("django.db.backends").warning("slow query")

        self.assertEqual(len(re.findall("slow query", self.stream.getvalue())), 1)

    def test_db_backends_below_warning_not_printed(self):
        logging.getLogger("django.db.backends").info("query")

        self.assertEqual(self.stream.getvalue(), "")
