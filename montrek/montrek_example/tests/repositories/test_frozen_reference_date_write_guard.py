"""The repository refuses to write while it reads a past state.

This lives with the ``montrek_example`` repositories rather than in
``mt_competo`` on purpose: the guard is in ``MontrekRepository`` and applies to
every repository in the project, so it is tested against the framework's own
example models, not against the risk procedure that happens to be its first
caller.
"""

import datetime

import pandas as pd
from django.test import TestCase
from django.utils import timezone

from baseclasses.errors.montrek_user_error import MontrekError
from baseclasses.repositories.montrek_repository import (
    FROZEN_REFERENCE_DATE_WRITE_MESSAGE,
)
from montrek_example.models import example_models as me_models
from montrek_example.repositories.hub_a_repository import HubARepository
from user.tests.factories.montrek_user_factories import MontrekUserFactory

AN_HOUR = datetime.timedelta(hours=1)


class FrozenReferenceDateWriteGuardTestCaseBase(TestCase):
    def setUp(self):
        self.user = MontrekUserFactory()

    def build_repository(self, **extra_session_data) -> HubARepository:
        return HubARepository(
            session_data={"user_id": self.user.id, **extra_session_data}
        )

    def creation_data(self, marker: str = "test") -> dict:
        return {"field_a1_int": 5, "field_a1_str": marker}

    def creation_data_frame(self) -> pd.DataFrame:
        return pd.DataFrame({"field_a1_int": [5], "field_a1_str": ["test"]})


class TestCreateByDictUnderAFrozenReferenceDate(
    FrozenReferenceDateWriteGuardTestCaseBase
):
    def test_a_past_reference_date_refuses_the_write(self):
        repository = self.build_repository(
            reference_date=timezone.now() - AN_HOUR,
        )
        with self.assertRaises(MontrekError) as raised:
            repository.create_by_dict(self.creation_data())
        self.assertEqual(raised.exception.args[0], FROZEN_REFERENCE_DATE_WRITE_MESSAGE)
        self.assertEqual(me_models.SatA1.objects.count(), 0)

    def test_a_reference_date_set_through_the_setter_refuses_too(self):
        """The guard must not be dodgeable by using the property instead."""
        repository = self.build_repository()
        repository.reference_date = timezone.now() - AN_HOUR
        with self.assertRaises(MontrekError):
            repository.create_by_dict(self.creation_data())
        self.assertEqual(me_models.SatA1.objects.count(), 0)

    def test_a_past_reference_date_as_a_string_refuses_the_write(self):
        """Session data coming from a query string arrives as text, not datetime."""
        reference_date = (timezone.now() - AN_HOUR).isoformat()
        repository = self.build_repository(reference_date=reference_date)
        with self.assertRaises(MontrekError):
            repository.create_by_dict(self.creation_data())

    def test_a_past_reference_date_as_a_query_parameter_list_refuses_the_write(self):
        """``request.GET`` is turned into ``{key: [value]}`` by the view mixin."""
        reference_date = [(timezone.now() - AN_HOUR).isoformat()]
        repository = self.build_repository(reference_date=reference_date)
        with self.assertRaises(MontrekError):
            repository.create_by_dict(self.creation_data())

    def test_without_a_reference_date_the_write_goes_through(self):
        self.build_repository().create_by_dict(self.creation_data())
        self.assertEqual(me_models.SatA1.objects.count(), 1)

    def test_a_reference_date_of_now_still_writes(self):
        """A pin at the present cannot hide anything, so it must not block."""
        repository = self.build_repository(reference_date=timezone.now() + AN_HOUR)
        repository.create_by_dict(self.creation_data())
        self.assertEqual(me_models.SatA1.objects.count(), 1)

    def test_an_empty_reference_date_list_is_treated_as_unset(self):
        """A stripped query parameter must not read as a pin at the epoch."""
        repository = self.build_repository(reference_date=[])
        repository.create_by_dict(self.creation_data())
        self.assertEqual(me_models.SatA1.objects.count(), 1)


class TestCreateByDataFrameUnderAFrozenReferenceDate(
    FrozenReferenceDateWriteGuardTestCaseBase
):
    def test_a_past_reference_date_refuses_the_write(self):
        repository = self.build_repository(reference_date=timezone.now() - AN_HOUR)
        with self.assertRaises(MontrekError):
            repository.create_by_data_frame(self.creation_data_frame())
        self.assertEqual(me_models.SatA1.objects.count(), 0)

    def test_without_a_reference_date_the_write_goes_through(self):
        self.build_repository().create_by_data_frame(self.creation_data_frame())
        self.assertEqual(me_models.SatA1.objects.count(), 1)


class TestExplicitReferenceDate(FrozenReferenceDateWriteGuardTestCaseBase):
    """``reference_date`` keeps answering ``now()``; only the pin is new."""

    def test_it_is_none_without_a_pin_while_reference_date_answers_now(self):
        repository = self.build_repository()
        self.assertIsNone(repository.explicit_reference_date)
        self.assertAlmostEqual(
            repository.reference_date,
            timezone.now(),
            delta=datetime.timedelta(seconds=10),
        )

    def test_the_setter_wins_over_session_data(self):
        session_reference_date = timezone.now() - AN_HOUR
        set_reference_date = timezone.now() - 2 * AN_HOUR
        repository = self.build_repository(reference_date=session_reference_date)
        repository.reference_date = set_reference_date
        self.assertEqual(repository.explicit_reference_date, set_reference_date)
        self.assertEqual(repository.reference_date, set_reference_date)
