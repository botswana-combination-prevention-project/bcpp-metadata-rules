from django.test import TestCase, tag
from bcpp_metadata_rules.predicates import Predicates


from arrow.arrow import Arrow
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta

from edc_constants.constants import NEG, POS, UNK, YES, IND, NAIVE, NO, MALE,\
    FEMALE
from edc_reference.tests import ReferenceTestHelper
from edc_reference import LongitudinalRefset
from pprint import pprint
from edc_registration.models import RegisteredSubject
from edc_reference.models import Reference
from bcpp_status.status_helper import StatusHelper
from bcpp_status.tests import StatusHelperTestMixin

MICROTUBE = 'Microtube'


class TestPredicates(StatusHelperTestMixin, TestCase):

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
    def test_is_hic_enrolled_yes(self):
        pc = Predicates()
        self.reference_helper.create_for_model(
            report_datetime=self.subject_visits[0].report_datetime,
            model='hicenrollment',
            visit_code=self.subject_visits[0].visit_code,
            hic_permission=YES)
        self.assertTrue(pc.is_hic_enrolled(self.subject_visits[0]))
        self.assertTrue(pc.is_hic_enrolled(self.subject_visits[1]))
        self.assertTrue(pc.is_hic_enrolled(self.subject_visits[2]))

    @tag('1')
    def test_is_hic_enrolled_no(self):
        pc = Predicates()
        self.reference_helper.create_for_model(
            report_datetime=self.subject_visits[0].report_datetime,
            model='hicenrollment',
            visit_code=self.subject_visits[0].visit_code,
            hic_permission=NO)
        self.assertFalse(pc.is_hic_enrolled(self.subject_visits[0]))
        self.assertFalse(pc.is_hic_enrolled(self.subject_visits[1]))
        self.assertFalse(pc.is_hic_enrolled(self.subject_visits[2]))

    @tag('1')
    def test_is_hic_enrolled_nonoe(self):
        pc = Predicates()
        self.assertFalse(pc.is_hic_enrolled(self.subject_visits[0]))
        self.assertFalse(pc.is_hic_enrolled(self.subject_visits[1]))
        self.assertFalse(pc.is_hic_enrolled(self.subject_visits[2]))

    @tag('1')
    def test_is_female(self):
        rs = RegisteredSubject.objects.create(
            subject_identifier=self.subject_identifier,
            gender=MALE)
        for gender in [MALE, FEMALE]:
            with self.subTest(gender=gender):
                pc = Predicates()
                rs.gender = gender
                rs.save()
                if gender == MALE:
                    self.assertFalse(pc.func_is_female(self.subject_visits[0]))
                    self.assertFalse(pc.func_is_female(self.subject_visits[1]))
                    self.assertFalse(pc.func_is_female(self.subject_visits[2]))
                elif gender == FEMALE:
                    self.assertTrue(pc.func_is_female(self.subject_visits[0]))
                    self.assertTrue(pc.func_is_female(self.subject_visits[1]))
                    self.assertTrue(pc.func_is_female(self.subject_visits[2]))

    @tag('1')
    def test_func_requires_recent_partner_0(self):
        pc = Predicates()
        self.reference_helper.create_for_model(
            report_datetime=self.subject_visits[0].report_datetime,
            model='sexualbehaviour',
            visit_code=self.subject_visits[0].visit_code,
            last_year_partners=0)
        self.assertFalse(pc.func_requires_recent_partner(
            self.subject_visits[0]))
        self.assertFalse(pc.func_requires_recent_partner(
            self.subject_visits[1]))
        self.assertFalse(pc.func_requires_recent_partner(
            self.subject_visits[2]))

    @tag('1')
    def func_requires_recent_partner_1(self):
        pc = Predicates()
        self.reference_helper.create_for_model(
            report_datetime=self.subject_visits[0].report_datetime,
            model='sexualbehaviour',
            visit_code=self.subject_visits[0].visit_code,
            last_year_partners=1)

        self.assertTrue(pc.func_requires_recent_partner(
            self.subject_visits[0]))
        self.assertFalse(pc.func_requires_recent_partner(
            self.subject_visits[1]))
        self.assertFalse(pc.func_requires_recent_partner(
            self.subject_visits[2]))

        self.assertFalse(pc.func_requires_second_partner_forms(
            self.subject_visits[0]))

        self.assertFalse(pc.func_requires_third_partnerforms(
            self.subject_visits[0]))

    @tag('1')
    def test_func_requires_partner_2(self):
        pc = Predicates()
        self.reference_helper.create_for_model(
            report_datetime=self.subject_visits[0].report_datetime,
            model='sexualbehaviour',
            visit_code=self.subject_visits[0].visit_code,
            last_year_partners=2)

        self.assertTrue(pc.func_requires_recent_partner(
            self.subject_visits[0]))
        self.assertFalse(pc.func_requires_recent_partner(
            self.subject_visits[1]))
        self.assertFalse(pc.func_requires_recent_partner(
            self.subject_visits[2]))

        self.assertTrue(pc.func_requires_second_partner_forms(
            self.subject_visits[0]))
        self.assertFalse(pc.func_requires_second_partner_forms(
            self.subject_visits[1]))
        self.assertFalse(pc.func_requires_second_partner_forms(
            self.subject_visits[2]))

        self.assertFalse(pc.func_requires_third_partner_forms(
            self.subject_visits[0]))

    @tag('1')
    def test_func_requires_partner_3(self):
        pc = Predicates()
        self.reference_helper.create_for_model(
            report_datetime=self.subject_visits[0].report_datetime,
            model='sexualbehaviour',
            visit_code=self.subject_visits[0].visit_code,
            last_year_partners=3)

        self.assertTrue(pc.func_requires_recent_partner(
            self.subject_visits[0]))
        self.assertFalse(pc.func_requires_recent_partner(
            self.subject_visits[1]))
        self.assertFalse(pc.func_requires_recent_partner(
            self.subject_visits[2]))

        self.assertTrue(pc.func_requires_second_partner_forms(
            self.subject_visits[0]))
        self.assertFalse(pc.func_requires_second_partner_forms(
            self.subject_visits[1]))
        self.assertFalse(pc.func_requires_second_partner_forms(
            self.subject_visits[2]))

        self.assertTrue(pc.func_requires_third_partner_forms(
            self.subject_visits[0]))
        self.assertFalse(pc.func_requires_third_partner_forms(
            self.subject_visits[1]))
        self.assertFalse(pc.func_requires_third_partner_forms(
            self.subject_visits[2]))

    @tag('1')
    def test_func_requires_hivlinkagetocare(self):
        pc = Predicates()
        self.assertFalse(pc.func_requires_hivlinkagetocare(
            self.subject_visits[0]))
        self.assertFalse(pc.func_requires_hivlinkagetocare(
            self.subject_visits[1]))
        self.assertFalse(pc.func_requires_hivlinkagetocare(
            self.subject_visits[2]))

    @tag('1')
    def test_func_requires_hivlinkagetocare_defaulter_baseline(self):
        pc = Predicates()
        self.assertFalse(pc.func_requires_hivlinkagetocare(
            self.subject_visits[0]))
        self.prepare_art_status(visit=self.subject_visits[0], defaulter=True)
        self.assertTrue(pc.func_requires_hivlinkagetocare(
            self.subject_visits[0]))
        self.assertTrue(pc.func_requires_hivlinkagetocare(
            self.subject_visits[1]))
        self.assertTrue(pc.func_requires_hivlinkagetocare(
            self.subject_visits[2]))

    @tag('1')
    def test_func_requires_hivlinkagetocare_naive_baseline(self):
        pc = Predicates()
        self.assertFalse(pc.func_requires_hivlinkagetocare(
            self.subject_visits[0]))

        self.prepare_art_status(visit=self.subject_visits[0], naive=True)

        self.assertTrue(pc.func_requires_hivlinkagetocare(
            self.subject_visits[0]))
        self.assertTrue(pc.func_requires_hivlinkagetocare(
            self.subject_visits[1]))
        self.assertTrue(pc.func_requires_hivlinkagetocare(
            self.subject_visits[2]))

    @tag('1')
    def test_func_art_defaulter(self):
        pc = Predicates()
        self.assertFalse(pc.func_art_defaulter(self.subject_visits[0]))
        self.assertFalse(pc.func_art_defaulter(self.subject_visits[1]))
        self.assertFalse(pc.func_art_defaulter(self.subject_visits[2]))

    @tag('1')
    def test_func_art_defaulter_true1(self):
        pc = Predicates()
        self.prepare_art_status(visit=self.subject_visits[0], defaulter=True)
        self.assertTrue(pc.func_art_defaulter(self.subject_visits[0]))
        self.assertTrue(pc.func_art_defaulter(self.subject_visits[1]))
        self.assertTrue(pc.func_art_defaulter(self.subject_visits[2]))

    @tag('1')
    def test_func_art_defaulter_true2(self):
        pc = Predicates()

        self.prepare_art_status(visit=self.subject_visits[1], defaulter=True)
        self.prepare_art_status(visit=self.subject_visits[2], defaulter=True)
        self.assertFalse(pc.func_art_defaulter(self.subject_visits[0]))
        self.assertTrue(pc.func_art_defaulter(self.subject_visits[1]))
        self.assertTrue(pc.func_art_defaulter(self.subject_visits[2]))
