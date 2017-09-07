from arrow.arrow import Arrow
from bcpp_community.surveys import BCPP_YEAR_2, BCPP_YEAR_3
from bcpp_metadata_rules.predicates import Predicates
from bcpp_status.status_helper import StatusHelper
from bcpp_status.tests import StatusHelperTestMixin
from datetime import datetime
from dateutil.relativedelta import relativedelta
from django.test import TestCase, tag
from edc_constants.constants import NEG, POS, YES, NO, MALE, FEMALE
from edc_reference import LongitudinalRefset, get_reference_name
from edc_reference.tests import ReferenceTestHelper
from edc_registration.models import RegisteredSubject

MICROTUBE = 'Microtube'


class MyReferenceTestHelper(ReferenceTestHelper):

    def create_visit(self, subject_identifier=None, **kwargs):
        """Updates the status history after creating a new visit.

        Simulates the SubjectVisit post-save signal.
        """
        reference = super().create_visit(**kwargs)
        reference.subject_identifier = subject_identifier
        reference.visit_code = reference.timepoint
        StatusHelper(visit=reference, update_history=True)
        return reference


class TestPredicates(StatusHelperTestMixin, TestCase):

    reference_helper_cls = MyReferenceTestHelper
    visit_model = 'bcpp_subject.subjectvisit'
    reference_model = 'edc_reference.reference'
    app_label = 'bcpp_subject'

    def setUp(self):
        self.subject_identifier = '111111111'
        self.reference_helper = self.reference_helper_cls(
            visit_model='bcpp_subject.subjectvisit',
            subject_identifier=self.subject_identifier)

        report_datetime = Arrow.fromdatetime(
            datetime(2015, 1, 7)).datetime
        self.reference_helper.create_visit(
            subject_identifier=self.subject_identifier,
            report_datetime=report_datetime, timepoint='T0')
        self.reference_helper.create_visit(
            subject_identifier=self.subject_identifier,
            report_datetime=report_datetime + relativedelta(years=1), timepoint='T1')
        self.reference_helper.create_visit(
            subject_identifier=self.subject_identifier,
            report_datetime=report_datetime + relativedelta(years=2), timepoint='T2')

    def run_metadata_rule(self, func, visit=None):
        """Updates status history before running func or rule.

        Simulates the method that runs metadata rules that is
        called in the metadata signal.
        """
        StatusHelper(visit=visit, update_history=True)
        return func(visit)

    @property
    def subject_visits(self):
        return LongitudinalRefset(
            subject_identifier=self.subject_identifier,
            visit_model=self.visit_model,
            name=self.visit_model,
            reference_model_cls=self.reference_model
        ).order_by('report_datetime')

    def test_is_circumcised_none(self):
        pc = Predicates()
        self.assertFalse(pc.is_circumcised(self.subject_visits[0]))

    def test_is_circumcised_baseline_yes(self):
        pc = Predicates()
        self.reference_helper.create_for_model(
            report_datetime=self.subject_visits[0].report_datetime,
            reference_name=f'{self.app_label}.circumcision',
            visit_code=self.subject_visits[0].visit_code,
            circumcised=YES)
        self.assertTrue(pc.is_circumcised(self.subject_visits[0]))

    def test_is_circumcised_baseline_no(self):
        pc = Predicates()
        self.reference_helper.create_for_model(
            report_datetime=self.subject_visits[0].report_datetime,
            reference_name=f'{self.app_label}.circumcision',
            visit_code=self.subject_visits[0].visit_code,
            circumcised=NO)
        self.assertFalse(pc.is_circumcised(self.subject_visits[0]))

    def test_is_circumcised_baseline_no_t1_yes(self):
        pc = Predicates()
        self.reference_helper.create_for_model(
            report_datetime=self.subject_visits[0].report_datetime,
            reference_name=f'{self.app_label}.circumcision',
            visit_code=self.subject_visits[0].visit_code,
            circumcised=NO)
        self.reference_helper.create_for_model(
            report_datetime=self.subject_visits[1].report_datetime,
            reference_name=f'{self.app_label}.circumcision',
            visit_code=self.subject_visits[1].visit_code,
            circumcised=YES)
        self.assertFalse(pc.is_circumcised(self.subject_visits[0]))
        self.assertTrue(pc.is_circumcised(self.subject_visits[1]))

    def test_is_circumcised_baseline_yes_t1_no(self):
        """Assert any YES returns True.
        """
        pc = Predicates()
        self.reference_helper.create_for_model(
            report_datetime=self.subject_visits[0].report_datetime,
            reference_name=f'{self.app_label}.circumcision',
            visit_code=self.subject_visits[0].visit_code,
            circumcised=YES)
        self.reference_helper.create_for_model(
            report_datetime=self.subject_visits[1].report_datetime,
            reference_name=f'{self.app_label}.circumcision',
            visit_code=self.subject_visits[1].visit_code,
            circumcised=NO)
        self.assertTrue(pc.is_circumcised(self.subject_visits[0]))
        self.assertTrue(pc.is_circumcised(self.subject_visits[1]))

    def test_is_hic_enrolled_yes(self):
        pc = Predicates()
        self.reference_helper.create_for_model(
            report_datetime=self.subject_visits[0].report_datetime,
            reference_name=f'{self.app_label}.hicenrollment',
            visit_code=self.subject_visits[0].visit_code,
            hic_permission=YES)
        self.assertTrue(pc.is_hic_enrolled(self.subject_visits[0]))
        self.assertTrue(pc.is_hic_enrolled(self.subject_visits[1]))
        self.assertTrue(pc.is_hic_enrolled(self.subject_visits[2]))

    def test_is_hic_enrolled_no(self):
        pc = Predicates()
        self.reference_helper.create_for_model(
            report_datetime=self.subject_visits[0].report_datetime,
            reference_name=f'{self.app_label}.hicenrollment',
            visit_code=self.subject_visits[0].visit_code,
            hic_permission=NO)
        self.assertFalse(pc.is_hic_enrolled(self.subject_visits[0]))
        self.assertFalse(pc.is_hic_enrolled(self.subject_visits[1]))
        self.assertFalse(pc.is_hic_enrolled(self.subject_visits[2]))

    def test_is_hic_enrolled_nonoe(self):
        pc = Predicates()
        self.assertFalse(pc.is_hic_enrolled(self.subject_visits[0]))
        self.assertFalse(pc.is_hic_enrolled(self.subject_visits[1]))
        self.assertFalse(pc.is_hic_enrolled(self.subject_visits[2]))

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

    def test_func_requires_recent_partner_none(self):
        pc = Predicates()
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_requires_recent_partner,
                self.subject_visits[0]))
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_requires_recent_partner,
                self.subject_visits[1]))
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_requires_recent_partner,
                self.subject_visits[2]))

    def test_func_requires_recent_partner_0(self):
        pc = Predicates()
        self.reference_helper.create_for_model(
            report_datetime=self.subject_visits[0].report_datetime,
            reference_name=f'{self.app_label}.sexualbehaviour',
            visit_code=self.subject_visits[0].visit_code,
            last_year_partners=0)
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_requires_recent_partner,
                self.subject_visits[0]))
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_requires_recent_partner,
                self.subject_visits[1]))
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_requires_recent_partner,
                self.subject_visits[2]))

    def func_requires_recent_partner_1(self):
        pc = Predicates()
        self.reference_helper.create_for_model(
            report_datetime=self.subject_visits[0].report_datetime,
            reference_name=f'{self.app_label}.sexualbehaviour',
            visit_code=self.subject_visits[0].visit_code,
            last_year_partners=1)

        self.assertTrue(
            self.run_metadata_rule(
                pc.func_requires_recent_partner,
                self.subject_visits[0]))
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_requires_recent_partner,
                self.subject_visits[1]))
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_requires_recent_partner,
                self.subject_visits[2]))

        self.assertFalse(
            self.run_metadata_rule(
                pc.func_requires_second_partner_forms,
                self.subject_visits[0]))

        self.assertFalse(
            self.run_metadata_rule(
                pc.func_requires_third_partnerforms,
                self.subject_visits[0]))

    def test_func_requires_partner_2(self):
        pc = Predicates()
        self.reference_helper.create_for_model(
            report_datetime=self.subject_visits[0].report_datetime,
            reference_name=f'{self.app_label}.sexualbehaviour',
            visit_code=self.subject_visits[0].visit_code,
            last_year_partners=2)

        self.assertTrue(pc.func_requires_recent_partner(
            self.subject_visits[0]))
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_requires_recent_partner,
                self.subject_visits[1]))
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_requires_recent_partner,
                self.subject_visits[2]))
        self.assertTrue(
            self.run_metadata_rule(
                pc.func_requires_second_partner_forms,
                self.subject_visits[0]))
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_requires_second_partner_forms,
                self.subject_visits[1]))
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_requires_second_partner_forms,
                self.subject_visits[2]))
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_requires_third_partner_forms,
                self.subject_visits[0]))

    def test_func_requires_partner_3(self):
        pc = Predicates()
        self.reference_helper.create_for_model(
            report_datetime=self.subject_visits[0].report_datetime,
            reference_name=f'{self.app_label}.sexualbehaviour',
            visit_code=self.subject_visits[0].visit_code,
            last_year_partners=3)
        self.assertTrue(
            self.run_metadata_rule(
                pc.func_requires_recent_partner,
                self.subject_visits[0]))
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_requires_recent_partner,
                self.subject_visits[1]))
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_requires_recent_partner,
                self.subject_visits[2]))
        self.assertTrue(
            self.run_metadata_rule(
                pc.func_requires_second_partner_forms,
                self.subject_visits[0]))
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_requires_second_partner_forms,
                self.subject_visits[1]))
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_requires_second_partner_forms,
                self.subject_visits[2]))
        self.assertTrue(
            self.run_metadata_rule(
                pc.func_requires_third_partner_forms,
                self.subject_visits[0]))
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_requires_third_partner_forms,
                self.subject_visits[1]))
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_requires_third_partner_forms,
                self.subject_visits[2]))

    def test_func_requires_hivlinkagetocare(self):
        pc = Predicates()
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_requires_hivlinkagetocare,
                self.subject_visits[0]))
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_requires_hivlinkagetocare,
                self.subject_visits[1]))
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_requires_hivlinkagetocare,
                self.subject_visits[2]))

    def test_func_requires_hivlinkagetocare_defaulter_baseline(self):
        pc = Predicates()
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_requires_hivlinkagetocare,
                self.subject_visits[0]))
        self.prepare_art_status(visit=self.subject_visits[0], defaulter=True)
        self.assertTrue(
            self.run_metadata_rule(
                pc.func_requires_hivlinkagetocare,
                self.subject_visits[0]))
        self.assertTrue(
            self.run_metadata_rule(
                pc.func_requires_hivlinkagetocare,
                self.subject_visits[1]))
        self.assertTrue(
            self.run_metadata_rule(
                pc.func_requires_hivlinkagetocare,
                self.subject_visits[2]))

    def test_func_requires_hivlinkagetocare_naive_baseline(self):
        pc = Predicates()
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_requires_hivlinkagetocare,
                self.subject_visits[0]))

        self.prepare_art_status(visit=self.subject_visits[0], naive=True)

        self.assertTrue(
            self.run_metadata_rule(
                pc.func_requires_hivlinkagetocare,
                self.subject_visits[0]))
        self.assertTrue(
            self.run_metadata_rule(
                pc.func_requires_hivlinkagetocare,
                self.subject_visits[1]))
        self.assertTrue(
            self.run_metadata_rule(
                pc.func_requires_hivlinkagetocare,
                self.subject_visits[2]))

    def test_func_art_defaulter(self):
        pc = Predicates()
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_art_defaulter, self.subject_visits[0]))
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_art_defaulter, self.subject_visits[1]))
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_art_defaulter, self.subject_visits[2]))

    def test_func_art_defaulter_true1(self):
        pc = Predicates()
        self.prepare_art_status(visit=self.subject_visits[0], defaulter=True)
        self.assertTrue(
            self.run_metadata_rule(pc.func_art_defaulter, self.subject_visits[0]))
        self.assertTrue(
            self.run_metadata_rule(pc.func_art_defaulter, self.subject_visits[1]))
        self.assertTrue(
            self.run_metadata_rule(pc.func_art_defaulter, self.subject_visits[2]))

    def test_func_art_defaulter_true2(self):
        pc = Predicates()

        self.prepare_art_status(visit=self.subject_visits[1], defaulter=True)
        self.prepare_art_status(visit=self.subject_visits[2], defaulter=True)
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_art_defaulter, self.subject_visits[0]))
        self.assertTrue(
            self.run_metadata_rule(
                pc.func_art_defaulter, self.subject_visits[1]))
        self.assertTrue(
            self.run_metadata_rule(
                pc.func_art_defaulter, self.subject_visits[2]))

    def test_func_art_naive(self):
        pc = Predicates()
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_art_naive, self.subject_visits[0]))
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_art_naive, self.subject_visits[1]))
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_art_naive, self.subject_visits[2]))

    def test_func_art_naive_true1(self):
        pc = Predicates()
        self.prepare_art_status(visit=self.subject_visits[0], naive=True)
        self.assertTrue(
            self.run_metadata_rule(
                pc.func_art_naive, self.subject_visits[0]))
        self.assertTrue(
            self.run_metadata_rule(
                pc.func_art_naive, self.subject_visits[1]))
        self.assertTrue(
            self.run_metadata_rule,
            pc.func_art_naive(self.subject_visits[2]))

    def test_func_art_naive_true2(self):
        pc = Predicates()
        self.prepare_art_status(visit=self.subject_visits[1], naive=True)
        self.prepare_art_status(visit=self.subject_visits[2], naive=True)
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_art_naive, self.subject_visits[0]))
        self.assertTrue(
            self.run_metadata_rule(
                pc.func_art_naive, self.subject_visits[1]))
        self.assertTrue(
            self.run_metadata_rule(
                pc.func_art_naive, self.subject_visits[2]))

    def test_func_on_art(self):
        pc = Predicates()
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_on_art, self.subject_visits[0]))
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_on_art, self.subject_visits[1]))
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_on_art, self.subject_visits[2]))

    def test_func_on_art_true1(self):
        pc = Predicates()
        self.prepare_art_status(visit=self.subject_visits[0], on_art=True)
        self.assertTrue(
            self.run_metadata_rule(
                pc.func_on_art, self.subject_visits[0]))
        self.assertTrue(
            self.run_metadata_rule(
                pc.func_on_art, self.subject_visits[1]))
        self.assertTrue(
            self.run_metadata_rule(
                pc.func_on_art, self.subject_visits[2]))

    def test_func_on_art_true2(self):
        pc = Predicates()
        self.prepare_art_status(visit=self.subject_visits[1], on_art=True)
        self.prepare_art_status(visit=self.subject_visits[2], on_art=True)
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_on_art, self.subject_visits[0]))
        self.assertTrue(
            self.run_metadata_rule(
                pc.func_on_art, self.subject_visits[1]))
        self.assertTrue(
            self.run_metadata_rule(
                pc.func_on_art, self.subject_visits[2]))

    def test_func_requires_todays_hiv_result(self):
        pc = Predicates()
        self.assertTrue(
            self.run_metadata_rule(
                pc.func_requires_todays_hiv_result,
                self.subject_visits[0]))
        self.assertTrue(
            self.run_metadata_rule(
                pc.func_requires_todays_hiv_result,
                self.subject_visits[1]))
        self.assertTrue(
            self.run_metadata_rule(
                pc.func_requires_todays_hiv_result,
                self.subject_visits[2]))

    def test_func_requires_todays_hiv_result1(self):
        pc = Predicates()
        self.prepare_hiv_status(visit=self.subject_visits[0], result=NEG)
        self.assertTrue(
            self.run_metadata_rule(
                pc.func_requires_todays_hiv_result,
                self.subject_visits[0]))
        self.assertTrue(
            self.run_metadata_rule(
                pc.func_requires_todays_hiv_result,
                self.subject_visits[1]))
        self.assertTrue(
            self.run_metadata_rule(
                pc.func_requires_todays_hiv_result,
                self.subject_visits[2]))

    def test_func_requires_todays_hiv_result2(self):
        pc = Predicates()
        self.prepare_hiv_status(visit=self.subject_visits[0], result=POS)
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_requires_todays_hiv_result,
                self.subject_visits[0]))
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_requires_todays_hiv_result,
                self.subject_visits[1]))
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_requires_todays_hiv_result,
                self.subject_visits[2]))

    def test_func_requires_pima_cd4(self):
        pc = Predicates()
        self.prepare_art_status(
            visit=self.subject_visits[0], naive=True, result=POS)
        self.assertTrue(
            self.run_metadata_rule(
                pc.func_requires_pima_cd4, self.subject_visits[0]))

    def test_func_requires_pima_cd4_1(self):
        pc = Predicates()
        self.prepare_art_status(
            visit=self.subject_visits[0], naive=True, result=POS)
        self.assertTrue(
            self.run_metadata_rule(
                pc.func_requires_pima_cd4, self.subject_visits[0]))
        self.assertTrue(
            self.run_metadata_rule(
                pc.func_requires_pima_cd4, self.subject_visits[1]))

    def test_func_requires_pima_cd4_2(self):
        pc = Predicates()
        self.prepare_art_status(
            visit=self.subject_visits[0], on_art=True)
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_requires_pima_cd4, self.subject_visits[0]))
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_requires_pima_cd4, self.subject_visits[1]))

    def test_func_requires_pima_cd4_3(self):
        pc = Predicates()
        self.prepare_art_status(
            visit=self.subject_visits[0], defaulter=True)
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_requires_pima_cd4, self.subject_visits[0]))
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_requires_pima_cd4, self.subject_visits[1]))

    def test_func_known_hiv_pos(self):
        pc = Predicates()
        self.prepare_known_positive(visit=self.subject_visits[0])
        self.assertTrue(
            self.run_metadata_rule(
                pc.func_known_hiv_pos, self.subject_visits[0]))

    def test_func_requires_vl(self):
        pc = Predicates()
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_requires_vl, self.subject_visits[0]))
        self.prepare_known_positive(visit=self.subject_visits[0])
        self.assertTrue(
            self.run_metadata_rule(
                pc.func_requires_vl, self.subject_visits[0]))

    def test_func_requires_rbd(self):
        pc = Predicates()
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_requires_rbd, self.subject_visits[0]))
        self.prepare_hiv_status(visit=self.subject_visits[0], result=POS)
        self.assertTrue(
            self.run_metadata_rule(
                pc.func_requires_rbd, self.subject_visits[0]))

    def test_func_requires_hivuntested(self):
        pc = Predicates()
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_requires_hivuntested, self.subject_visits[0]))

    def test_func_requires_hivuntested2(self):
        pc = Predicates()
        self.reference_helper.create_for_model(
            report_datetime=self.subject_visits[0].report_datetime,
            reference_name=f'{self.app_label}.hivtestinghistory',
            visit_code=self.subject_visits[0].visit_code,
            has_tested=NO)
        self.assertTrue(
            self.run_metadata_rule(
                pc.func_requires_hivuntested, self.subject_visits[0]))

    def test_func_requires_hivtestreview(self):
        pc = Predicates()
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_requires_hivtestreview,
                self.subject_visits[0]))

    def test_func_requires_hivtestreview2(self):
        pc = Predicates()
        self.reference_helper.create_for_model(
            report_datetime=self.subject_visits[0].report_datetime,
            reference_name=f'{self.app_label}.hivtestinghistory',
            visit_code=self.subject_visits[0].visit_code,
            has_record=YES)
        self.assertTrue(
            self.run_metadata_rule(
                pc.func_requires_hivtestreview, self.subject_visits[0]))

    def test_func_anonymous_member(self):
        pc = Predicates()
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_anonymous_member, self.subject_visits[0]))

    def test_func_anonymous_member1(self):
        pc = Predicates()
        self.reference_helper.create_for_model(
            report_datetime=self.subject_visits[0].report_datetime,
            reference_name=f'{self.app_label}.anonymousconsent',
            visit_code=self.subject_visits[0].visit_code,
            consent_datetime=self.subject_visits[0].report_datetime)
        self.assertTrue(
            self.run_metadata_rule(
                pc.func_anonymous_member, self.subject_visits[0]))

    def test_func_requires_circumcision_male(self):
        RegisteredSubject.objects.create(
            subject_identifier=self.subject_identifier,
            gender=MALE)
        pc = Predicates()
        self.assertTrue(
            self.run_metadata_rule(
                pc.func_requires_circumcision, self.subject_visits[0]))
        self.prepare_hiv_status(visit=self.subject_visits[0], result=POS)
        self.assertTrue(
            self.run_metadata_rule(
                pc.func_requires_circumcision, self.subject_visits[0]))

    def test_func_requires_circumcision_female(self):
        RegisteredSubject.objects.create(
            subject_identifier=self.subject_identifier,
            gender=FEMALE)
        pc = Predicates()
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_requires_circumcision, self.subject_visits[0]))
        self.prepare_hiv_status(visit=self.subject_visits[0], result=POS)
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_requires_circumcision, self.subject_visits[0]))

    def test_func_requires_microtube(self):
        pc = Predicates()
        self.assertTrue(
            self.run_metadata_rule(
                pc.func_requires_microtube, self.subject_visits[0]))

    def test_func_requires_microtube1(self):
        pc = Predicates()
        # hivtestreview
        self.reference_helper.create_for_model(
            report_datetime=self.subject_visits[0].report_datetime,
            reference_name=f'{self.app_label}.hivtestreview',
            visit_code=self.subject_visits[0].visit_code,
            recorded_hiv_result=NEG,
            hiv_test_date=(self.subject_visits[0].report_datetime - relativedelta(days=50)).date())
        self.assertTrue(
            self.run_metadata_rule(
                pc.func_requires_microtube, self.subject_visits[0]))

    def test_func_requires_microtube2(self):
        pc = Predicates()
        # hivtestreview
        self.reference_helper.create_for_model(
            report_datetime=self.subject_visits[0].report_datetime,
            reference_name=f'{self.app_label}.hivtestreview',
            visit_code=self.subject_visits[0].visit_code,
            recorded_hiv_result=POS,
            hiv_test_date=(self.subject_visits[0].report_datetime - relativedelta(days=50)).date())
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_requires_microtube, self.subject_visits[0]))

    def test_func_not_requires_microtube_at_baseline_known_pos(self):
        pc = Predicates()
        self.prepare_known_positive(self.subject_visits[0])
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_requires_microtube, self.subject_visits[0]))

    def test_func_not_requires_microtube_known_pos(self):
        pc = Predicates()
        self.prepare_known_positive(self.subject_visits[0])
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_requires_microtube, self.subject_visits[1]))

    def test_func_requires_microtube_baseline_neg_interim_neg(self):
        pc = Predicates()
        # hivtestreview
        self.reference_helper.create_for_model(
            report_datetime=self.subject_visits[0].report_datetime,
            reference_name=f'{self.app_label}.hivtestreview',
            visit_code=self.subject_visits[0].visit_code,
            recorded_hiv_result=NEG,
            hiv_test_date=(self.subject_visits[0].report_datetime - relativedelta(days=50)).date())
        self.reference_helper.create_for_model(
            report_datetime=self.subject_visits[1].report_datetime,
            reference_name=f'{self.app_label}.hivtestreview',
            visit_code=self.subject_visits[1].visit_code,
            recorded_hiv_result=NEG,
            hiv_test_date=(self.subject_visits[1].report_datetime - relativedelta(days=50)).date())
        self.assertTrue(
            self.run_metadata_rule(
                pc.func_requires_microtube, self.subject_visits[1]))

    def test_func_not_requires_microtube_if_baseline_pos(self):
        pc = Predicates()
        # hivtestreview
        self.reference_helper.create_for_model(
            report_datetime=self.subject_visits[0].report_datetime,
            reference_name=f'{self.app_label}.hivtestreview',
            visit_code=self.subject_visits[0].visit_code,
            recorded_hiv_result=POS,
            hiv_test_date=(self.subject_visits[0].report_datetime - relativedelta(days=50)).date())
        self.reference_helper.create_for_model(
            report_datetime=self.subject_visits[1].report_datetime,
            reference_name=f'{self.app_label}.hivtestreview',
            visit_code=self.subject_visits[1].visit_code,
            recorded_hiv_result=POS,
            hiv_test_date=(self.subject_visits[1].report_datetime - relativedelta(days=50)).date())
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_requires_microtube, self.subject_visits[1]))

    def test_func_requires_microtube_for_neg_regardless_of_interim_pos(self):
        pc = Predicates()
        # neg at baseline
        self.prepare_hiv_status(visit=self.subject_visits[0], result=NEG)
        # tested POS during the year
        self.prepare_interim_pos(visit=self.subject_visits[1])
        # still required
        self.assertTrue(
            self.run_metadata_rule(
                pc.func_requires_microtube, self.subject_visits[1]))

    def test_func_hiv_positive(self):
        pc = Predicates()
        self.prepare_hiv_status(visit=self.subject_visits[0], result=POS)
        self.assertTrue(
            self.run_metadata_rule(
                pc.func_hiv_positive, self.subject_visits[0]))

    def test_func_requires_venous1(self):
        pc = Predicates()
        self.reference_helper.create_for_model(
            report_datetime=self.subject_visits[0].report_datetime,
            reference_name=get_reference_name(
                f'{self.app_label}.subjectrequisition', MICROTUBE),
            visit_code=self.subject_visits[0].visit_code,
            panel_name=MICROTUBE,
            is_drawn=NO,
            reason_not_drawn='collection_failed')
        self.assertTrue(
            self.run_metadata_rule(
                pc.func_requires_venous, self.subject_visits[0]))

    def test_func_requires_venous2(self):
        pc = Predicates()
        self.reference_helper.create_for_model(
            report_datetime=self.subject_visits[0].report_datetime,
            reference_name=get_reference_name(
                f'{self.app_label}.subjectrequisition', MICROTUBE),
            visit_code=self.subject_visits[0].visit_code,
            panel_name=MICROTUBE,
            is_drawn=YES,
            reason_not_drawn=None)
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_requires_venous, self.subject_visits[0]))

    def test_func_requires_hic_enrollment(self):
        pc = Predicates()
        self.assertFalse(
            self.run_metadata_rule(
                pc.func_requires_hic_enrollment,
                self.subject_visits[0]))

    def test_func_requires_hic_enrollment2(self):
        pc = Predicates()
        self.reference_helper.update_for_model(
            reference_name=f'{self.app_label}.subjectvisit',
            report_datetime=self.subject_visits[0].report_datetime,
            visit_code=self.subject_visits[0].visit_code,
            valueset=[('survey_schedule', 'CharField', BCPP_YEAR_2)])
        self.prepare_hiv_status(visit=self.subject_visits[0], result=NEG)
        self.assertTrue(
            self.run_metadata_rule(
                pc.func_requires_hic_enrollment,
                self.subject_visits[0]))

    def test_func_requires_hic_enrollment3(self):
        pc = Predicates()
        self.reference_helper.update_for_model(
            reference_name=f'{self.app_label}.subjectvisit',
            report_datetime=self.subject_visits[0].report_datetime,
            visit_code=self.subject_visits[0].visit_code,
            valueset=[('survey_schedule', 'CharField', BCPP_YEAR_3)])
        self.prepare_hiv_status(visit=self.subject_visits[0], result=NEG)

        self.assertFalse(
            self.run_metadata_rule(
                pc.func_requires_hic_enrollment,
                self.subject_visits[0]))
