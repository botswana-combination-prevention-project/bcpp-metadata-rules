from django.test import TestCase, tag
from bcpp_metadata_rules.predicates import Predicates


from arrow.arrow import Arrow
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta

from edc_constants.constants import NEG, POS, UNK, YES, IND, NAIVE, NO
from edc_reference.tests import ReferenceTestHelper
from edc_reference import LongitudinalRefset
from pprint import pprint

MICROTUBE = 'Microtube'


class TestPredicates(TestCase):

    reference_helper_cls = ReferenceTestHelper
    visit_model = 'bcpp_subject.subjectvisit'
    reference_model = 'edc_reference.reference'

    def setUp(self):
        self.subject_identifier = '111111111'
        self.reference_helper = self.reference_helper_cls(
            visit_model='bcpp_subject.subjectvisit',
            subject_identifier=self.subject_identifier)

        report_datetime = Arrow.fromdatetime(
            datetime(2015, 1, 7)).datetime
        self.reference_helper.create_visit(
            report_datetime=report_datetime, timepoint='T0')
        self.reference_helper.create_visit(
            report_datetime=report_datetime + relativedelta(years=1), timepoint='T1')
        self.reference_helper.create_visit(
            report_datetime=report_datetime + relativedelta(years=2), timepoint='T2')
        self.subject_visits = LongitudinalRefset(
            subject_identifier=self.subject_identifier,
            visit_model=self.visit_model,
            model=self.visit_model,
            reference_model_cls=self.reference_model
        ).order_by('report_datetime')

    def test_is_circumcised_none(self):
        pc = Predicates()
        self.assertFalse(pc.is_circumcised(self.subject_visits[0]))

    @tag('1')
    def test_is_circumcised_baseline_yes(self):
        pc = Predicates()
        self.reference_helper.create_for_model(
            report_datetime=self.subject_visits[0].report_datetime,
            model='circumcision',
            visit_code=self.subject_visits[0].visit_code,
            circumcised=YES)
        self.assertTrue(pc.is_circumcised(self.subject_visits[0]))

    @tag('1')
    def test_is_circumcised_baseline_no(self):
        pc = Predicates()
        self.reference_helper.create_for_model(
            report_datetime=self.subject_visits[0].report_datetime,
            model='circumcision',
            visit_code=self.subject_visits[0].visit_code,
            circumcised=NO)
        self.assertFalse(pc.is_circumcised(self.subject_visits[0]))

    @tag('1')
    def test_is_circumcised_baseline_no_t1_yes(self):
        pc = Predicates()
        self.reference_helper.create_for_model(
            report_datetime=self.subject_visits[0].report_datetime,
            model='circumcision',
            visit_code=self.subject_visits[0].visit_code,
            circumcised=NO)
        self.reference_helper.create_for_model(
            report_datetime=self.subject_visits[1].report_datetime,
            model='circumcision',
            visit_code=self.subject_visits[1].visit_code,
            circumcised=YES)
        self.assertFalse(pc.is_circumcised(self.subject_visits[0]))
        self.assertTrue(pc.is_circumcised(self.subject_visits[1]))

    @tag('1')
    def test_is_circumcised_baseline_yes_t1_no(self):
        """Assert any YES returns True.
        """
        pc = Predicates()
        self.reference_helper.create_for_model(
            report_datetime=self.subject_visits[0].report_datetime,
            model='circumcision',
            visit_code=self.subject_visits[0].visit_code,
            circumcised=YES)
        self.reference_helper.create_for_model(
            report_datetime=self.subject_visits[1].report_datetime,
            model='circumcision',
            visit_code=self.subject_visits[1].visit_code,
            circumcised=NO)
        self.assertTrue(pc.is_circumcised(self.subject_visits[0]))
        self.assertTrue(pc.is_circumcised(self.subject_visits[1]))

    @tag('1')
    def test_is_hic_enrolled(self):
        pc = Predicates()
        self.reference_helper.create_for_model(
            report_datetime=self.subject_visits[0].report_datetime,
            model='hicenrollment',
            visit_code=self.subject_visits[0].visit_code,
            hic_permission=YES)
        self.assertTrue(pc.is_hic_enrolled(self.subject_visits[0]))
