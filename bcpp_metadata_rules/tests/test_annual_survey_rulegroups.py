from datetime import timedelta, date
from dateutil.relativedelta import relativedelta

from model_mommy import mommy

from django.test import TestCase, tag

from edc_constants.constants import NO, YES, POS, NEG, DECLINED
from edc_metadata.constants import REQUIRED, NOT_REQUIRED, KEYED
from edc_metadata.models import CrfMetadata

from ..constants import T0, T1, T2, MICROTUBE, VIRAL_LOAD, RESEARCH_BLOOD_DRAW

from .test_mixins import SubjectMixin


@tag('ANNUAL_RULE')
class TestAnnualRuleSurveyRuleGroups(SubjectMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.consent_data = {
            'identity': '31721515',
            'confirm_identity': '31721515',
        }
        self.survey_schedule = self.get_survey_schedule(index=0)
        self.bhs_subject_visit_male = self.make_subject_visit_for_consented_subject_male(
            T0, survey_schedule=self.survey_schedule, **self.consent_data)
        self.subject_identifier = self.bhs_subject_visit_male.subject_identifier

    def hivtest_review(self, subject_visit, hiv_status, report_datetime=None):
        report_datetime = report_datetime or self.get_utcnow()
        hiv_test_review = mommy.make_recipe(
            'bcpp_subject.hivtestreview',
            report_datetime=report_datetime,
            subject_visit=subject_visit,
            hiv_test_date=self.get_utcnow() - timedelta(days=50),
            recorded_hiv_result=hiv_status)
        return hiv_test_review

    def make_hivtesting_history(self, subject_visit, has_tested, has_record,
                                verbal_hiv_result, other_record,
                                report_datetime=None):
        report_datetime = report_datetime or self.get_utcnow()
        hivtesting_history = mommy.make_recipe(
            'bcpp_subject.hivtestinghistory',
            subject_visit=subject_visit,
            report_datetime=report_datetime,
            has_tested=has_tested,
            when_hiv_test='1 to 5 months ago',
            has_record=has_record,
            verbal_hiv_result=verbal_hiv_result,
            other_record=other_record
        )
        return hivtesting_history

    def make_subject_locator(self, subject_identifier, report_datetime=None):
        report_datetime = report_datetime or self.get_utcnow()
        subject_locator = mommy.make_recipe(
            'bcpp_subject.subjectlocator',
            subject_identifier=self.subject_identifier,
            report_datetime=report_datetime)
        return subject_locator

    def make_residency_mobility(self, subject_visit, permanent_resident,
                                intend_residency, report_datetime=None):
        report_datetime = report_datetime or self.get_utcnow()
        residency_mobility = mommy.make_recipe(
            'bcpp_subject.residencymobility',
            subject_visit=subject_visit,
            report_datetime=self.get_utcnow(),
            permanent_resident=permanent_resident,
            intend_residency=permanent_resident)
        return residency_mobility

    def make_requisition(self, subject_visit, panel, report_datetime=None):
        report_datetime = report_datetime or self.get_utcnow()
        subject_requisition = mommy.make_recipe(
            'bcpp_subject.subjectrequisition',
            subject_visit=subject_visit,
            report_datetime=report_datetime,
            panel_name=panel,
            is_drawn=YES
        )
        return subject_requisition

    def hiv_result(self, status, subject_visit, report_datetime=None):
        """ Create HivResult for a particular survey.
        """
        report_datetime = report_datetime or self.get_utcnow()
        mommy.make_recipe(
            'bcpp_subject.subjectrequisition',
            subject_visit=subject_visit,
            report_datetime=report_datetime,
            panel_name=MICROTUBE,
        )
        hiv_result = mommy.make_recipe(
            'bcpp_subject.hivresult',
            subject_visit=subject_visit,
            report_datetime=report_datetime,
            hiv_result=status, insufficient_vol=NO
        )
        return hiv_result

    def make_hic_enrolment(
            self, subject_visit, hic_permission, report_datetime=None):
        """Return an hic enrolment instance."""
        report_datetime = report_datetime or self.get_utcnow()
        return mommy.make_recipe(
            'bcpp_subject.hicenrollment',
            subject_visit=subject_visit,
            report_datetime=self.get_utcnow(),
            hic_permission=hic_permission)

    def make_hivcareadherence(self, subject_visit, report_datetime=None):
        report_datetime = report_datetime or self.get_utcnow()
        return mommy.make_recipe(
            'bcpp_subject.hivcareadherence',
            subject_visit=subject_visit,
            report_datetime=report_datetime,
            first_positive=None,
            medical_care=None,
            ever_recommended_arv=None,
            ever_taken_arv=NO,
            first_arv=None,
            on_arv=NO,
            clinic_receiving_from=None,
            next_appointment_date=None,
            arv_stop_date=None,
            arv_stop=None,
            adherence_4_day=None,
            adherence_4_wk=None,
            arv_evidence=NO)

    def make_hiv_care_adherence(
            self, subject_visit, ever_recommended_arv, medical_care,
            ever_taken_arv, on_arv, arv_evidence, report_datetime=None):
        report_datetime = report_datetime or self.get_utcnow()
        hiv_care_adherence = mommy.make_recipe(
            'bcpp_subject.hivcareadherence',
            first_positive=self.get_utcnow(),
            subject_visit=subject_visit,
            report_datetime=report_datetime,
            medical_care=medical_care,
            ever_recommended_arv=ever_recommended_arv,
            ever_taken_arv=ever_taken_arv,
            on_arv=on_arv,
            arv_evidence=arv_evidence,  # this is the rule field
        )
        return hiv_care_adherence

    def hiv_pos_nd_art_naive_at_bhs(self):
        """Enrollees at t0 who are HIV-positive and ART naive at BHS.

        pimacd4, RBD and VL required. Then Key RBD for later use in
        Annual survey.
        """
        self.make_hivtesting_history(
            self.bhs_subject_visit_male,
            YES, YES, POS, NO,
            self.bhs_subject_visit_male.report_datetime)

        self.hivtest_review(
            self.bhs_subject_visit_male,
            POS,
            self.bhs_subject_visit_male.report_datetime)

        self.assertEqual(
            self.requisition_metadata_obj(
                'bcpp_subject.subjectrequisition', REQUIRED,
                T0, RESEARCH_BLOOD_DRAW).count(), 1)

        self.make_requisition(
            self.bhs_subject_visit_male, RESEARCH_BLOOD_DRAW,
            self.bhs_subject_visit_male.report_datetime)

        # add HivCarAdherence,
        self.make_hiv_care_adherence(
            self.bhs_subject_visit_male, NO, NO, NO, NO,
            NO, self.bhs_subject_visit_male.report_datetime)

        self.assertEqual(
            self.crf_metadata_obj('bcpp_subject.pimacd4',
                                  REQUIRED, T0).count(),
            1)
        self.assertEqual(self.requisition_metadata_obj(
            'bcpp_subject.subjectrequisition', REQUIRED,
            T0, VIRAL_LOAD).count(), 1)
        self.assertEqual(self.requisition_metadata_obj(
            'bcpp_subject.subjectrequisition', KEYED,
            T0, RESEARCH_BLOOD_DRAW).count(), 1)

    @tag('ahs_circumcision_rules')
    def test_no_circumsition_in_y2(self):
        """Assert circumcision forms not required at ahs if filled at bhs."""
        mommy.make_recipe(
            'bcpp_subject.circumcision',
            subject_visit=self.bhs_subject_visit_male,
            circumcised=YES,
            report_datetime=self.get_utcnow()
        )
        mommy.make_recipe(
            'bcpp_subject.circumcised',
            subject_visit=self.bhs_subject_visit_male,
            report_datetime=self.get_utcnow(),
            where_circ='Lobatse',
            why_circ='not_sure'
        )

        # Create a year 2 subject visit.
        self.add_subject_visit_followup(
            self.bhs_subject_visit_male.household_member, T1)

        self.assertEqual(self.crf_metadata_obj(
            'bcpp_subject.circumcision', NOT_REQUIRED,
            T1).count(), 1)
        self.assertEqual(self.crf_metadata_obj(
            'bcpp_subject.circumcised', NOT_REQUIRED,
            T1).count(), 1)
        self.assertEqual(self.crf_metadata_obj(
            'bcpp_subject.uncircumcised', NOT_REQUIRED,
            T1).count(), 1)

    @tag('test_pos_in_y1_no_hiv_forms')
    def test_pos_in_y1_no_hiv_forms(self):
        """Assert that is a participant is positive in year 1
        hiv forms are not required the following year.
        """

        self.hivtest_review(
            self.bhs_subject_visit_male,
            POS,
            self.bhs_subject_visit_male.report_datetime)

        self._hiv_result = self.hiv_result(
            POS, self.bhs_subject_visit_male,
            self.bhs_subject_visit_male.report_datetime)

        # Create a year 2 subject visit.
        self.add_subject_visit_followup(
            self.bhs_subject_visit_male.household_member, T1)

        self.assertEqual(self.crf_metadata_obj(
            'bcpp_subject.hivtestreview', NOT_REQUIRED, T1).count(), 1)
        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.hivtested', NOT_REQUIRED, T1).count(), 1)
        self.assertEqual(self.crf_metadata_obj(
            'bcpp_subject.hivresultdocumentation',
            NOT_REQUIRED, T1).count(), 1)
        self.assertEqual(self.crf_metadata_obj(
            'bcpp_subject.hivtestinghistory', NOT_REQUIRED, T1).count(), 1)
        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.hivresult',
                NOT_REQUIRED, T1).count(), 1)
        self.assertEqual(self.requisition_metadata_obj(
            'bcpp_subject.subjectrequisition', NOT_REQUIRED,
            T1, MICROTUBE).count(), 1)

    @tag('reviewed')
    def test_hic_filled_in_y1_not_required_in_annual(self):
        """Assert that hic will not be required at year 1 if filled at bhs."""
        self.make_subject_locator(
            self.subject_identifier,
            self.bhs_subject_visit_male.report_datetime)
        self.make_residency_mobility(
            self.bhs_subject_visit_male, YES,
            NO, self.bhs_subject_visit_male.report_datetime)
        self.hiv_result(
            NEG, self.bhs_subject_visit_male,
            self.bhs_subject_visit_male.report_datetime)
        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.hicenrollment', REQUIRED, T0).count(), 1)

        self.make_hic_enrolment(
            self.bhs_subject_visit_male,
            YES,
            self.bhs_subject_visit_male.report_datetime)

        subject_visit_male_y2 = self.add_subject_visit_followup(
            self.bhs_subject_visit_male.household_member, T1)
        self.hiv_result(
            NEG, subject_visit_male_y2, subject_visit_male_y2.report_datetime)

        self.assertEqual(self.crf_metadata_obj(
            'bcpp_subject.hicenrollment', NOT_REQUIRED, T1).count(), 1)

        subject_visit_male_y3 = self.add_subject_visit_followup(
            subject_visit_male_y2.household_member, T2)

        self.hiv_result(
            NEG, subject_visit_male_y3, subject_visit_male_y3.report_datetime)

        self.assertEqual(self.crf_metadata_obj(
            'bcpp_subject.hicenrollment', NOT_REQUIRED, T2).count(), 1)

    @tag('reviewed')
    def test_microtube_always_required_for_hic_without_pos_hivresult(self):
        """ Tests an HIC enrollee who sero-converted,
            POS result not tested by BHP, will be tested by BHP at next visit.
        """

        self.make_subject_locator(
            self.subject_identifier, self.bhs_subject_visit_male.report_datetime)

        self.hiv_result(
            NEG, self.bhs_subject_visit_male, self.bhs_subject_visit_male.report_datetime)

        self.make_residency_mobility(
            self.bhs_subject_visit_male, YES, NO, self.bhs_subject_visit_male.report_datetime)

        self.make_hic_enrolment(
            self.bhs_subject_visit_male, YES, self.bhs_subject_visit_male.report_datetime)

        # Create a year 2 subject visit.
        ahs_subject_visit_male_y2 = self.add_subject_visit_followup(
            self.bhs_subject_visit_male.household_member, T1, **self.consent_data)

        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.hivresult', REQUIRED, T1).count(), 1)
        self.assertEqual(self.requisition_metadata_obj(
            'bcpp_subject.subjectrequisition', REQUIRED,
            T1, MICROTUBE).count(), 1)

        self.make_hivtesting_history(
            ahs_subject_visit_male_y2, YES, YES,
            POS, NO, report_datetime=ahs_subject_visit_male_y2.report_datetime)

        self.hivtest_review(
            ahs_subject_visit_male_y2, POS,
            report_datetime=ahs_subject_visit_male_y2.report_datetime)

        self.assertEqual(self.requisition_metadata_obj(
            'bcpp_subject.subjectrequisition', REQUIRED,
            T1, MICROTUBE).count(), 1)
        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.hivresult',
                REQUIRED, T1).count(), 1)

    def test_microtube_not_required_for_hic_with_pos_hivresult(self):
        """ Tests an HIC enrollee who sero-converted, tested by BHP,
            will not be tested again in next visit."""
        self.make_subject_locator(
            self.bhs_subject_visit_male.subject_identifier,
            self.bhs_subject_visit_male.report_datetime)

        mommy.make_recipe(
            'bcpp_subject.hivtestinghistory',
            subject_visit=self.bhs_subject_visit_male,
            report_datetime=self.bhs_subject_visit_male.report_datetime,
            has_tested=YES,
            when_hiv_test='1 to 5 months ago',
            has_record=YES,
            verbal_hiv_result=NEG,
            other_record=NO
        )
        mommy.make_recipe(
            'bcpp_subject.hivtestreview',
            report_datetime=self.bhs_subject_visit_male.report_datetime,
            subject_visit=self.bhs_subject_visit_male,
            hiv_test_date=self.get_utcnow() - timedelta(days=50),
            recorded_hiv_result=NEG)

        self.hiv_result(NEG, self.bhs_subject_visit_male, self.get_utcnow())

        self.make_residency_mobility(
            self.bhs_subject_visit_male, YES,
            NO, self.bhs_subject_visit_male.report_datetime)

        self.make_hic_enrolment(
            self.bhs_subject_visit_male, YES,
            self.bhs_subject_visit_male.report_datetime)

        subject_visit_male_y2 = self.add_subject_visit_followup(
            self.bhs_subject_visit_male.household_member, T1)

        report_datetime = subject_visit_male_y2.report_datetime
        self.hiv_result(POS, subject_visit_male_y2, report_datetime)

        mommy.make_recipe(
            'bcpp_subject.hivtestreview',
            report_datetime=subject_visit_male_y2.report_datetime,
            subject_visit=subject_visit_male_y2,
            hiv_test_date=self.get_utcnow() - timedelta(days=50),
            recorded_hiv_result=POS)

        # We are now in year 3 in which the participant is a known POS.
        report_datetime = self.get_utcnow() + relativedelta(years=3, months=6)
        self.consent_data.update(
            report_datetime=self.get_utcnow() + relativedelta(years=3, months=6))

        self.add_subject_visit_followup(
            subject_visit_male_y2.household_member,
            T2, household_log_report_date=report_datetime,
            **self.consent_data)

        self.assertEqual(self.requisition_metadata_obj(
            'bcpp_subject.subjectrequisition', NOT_REQUIRED,
            T2, MICROTUBE).count(), 1)
        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.hivresult',
                NOT_REQUIRED, T2).count(), 1)

    def test_hiv_pos_requisitions_y2(self):
        """ HIV Negative and in HIC at T0 and Tests Positive during home
            visits at T1 and is Not on ART at T1. Sero Converter,
            Should offer POC CD4, RBD and VL.
        """
        self.make_subject_locator(
            self.subject_identifier,
            self.bhs_subject_visit_male.report_datetime)

        self.make_residency_mobility(self.bhs_subject_visit_male, YES, NO)

        self.hiv_result(
            NEG, self.bhs_subject_visit_male,
            self.bhs_subject_visit_male.report_datetime)

        self.make_hic_enrolment(
            self.bhs_subject_visit_male, YES,
            self.bhs_subject_visit_male.report_datetime)

        subject_visit_male_y2 = self.add_subject_visit_followup(
            self.bhs_subject_visit_male.household_member, T1)

        self.hiv_result(
            POS, subject_visit_male_y2, subject_visit_male_y2.report_datetime)

        # add HivCarAdherence,
        self.make_hiv_care_adherence(
            subject_visit_male_y2,
            NO, NO, NO, NO, NO,
            subject_visit_male_y2.report_datetime)

        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.pimacd4', REQUIRED, T1).count(), 1)
        self.assertEqual(self.requisition_metadata_obj(
            'bcpp_subject.subjectrequisition', REQUIRED,
            T1, VIRAL_LOAD).count(), 1)
        self.assertEqual(self.requisition_metadata_obj(
            'bcpp_subject.subjectrequisition', REQUIRED,
            T1, RESEARCH_BLOOD_DRAW).count(), 1)

    @tag('test_Known_hiv_pos_y2_not_hic_require_no_testing')
    def test_Known_hiv_pos_y2_not_hic_require_no_testing(self):

        self.hiv_result(
            NEG, self.bhs_subject_visit_male,
            self.bhs_subject_visit_male.report_datetime)

        subject_visit_male_y2 = self.add_subject_visit_followup(
            self.bhs_subject_visit_male.household_member, T1)

        mommy.make_recipe(
            'bcpp_subject.hivtestinghistory',
            subject_visit=subject_visit_male_y2,
            report_datetime=subject_visit_male_y2.report_datetime,
            has_tested=YES,
            when_hiv_test='1 to 5 months ago',
            has_record=YES,
            verbal_hiv_result=POS,
            other_record=NO
        )
        mommy.make_recipe(
            'bcpp_subject.hivtestreview',
            report_datetime=subject_visit_male_y2.report_datetime,
            subject_visit=subject_visit_male_y2,
            hiv_test_date=self.get_utcnow() - timedelta(days=50),
            recorded_hiv_result=POS)

        self.hiv_result(
            POS, subject_visit_male_y2,
            subject_visit_male_y2.report_datetime)

        crf_count = CrfMetadata.objects.filter(
            model='bcpp_subject.hivresult',
            entry_status=KEYED,
            visit_code=T1,
            subject_identifier=subject_visit_male_y2.subject_identifier).count()

        self.assertEqual(crf_count, 1)

        report_datetime = self.get_utcnow() + relativedelta(years=3, months=6)
        self.consent_data.update(
            report_datetime=self.get_utcnow() + relativedelta(years=3, months=6))

        self.add_subject_visit_followup(
            subject_visit_male_y2.household_member,
            T2, household_log_report_date=report_datetime,
            **self.consent_data)

        crf_count = CrfMetadata.objects.filter(
            entry_status=NOT_REQUIRED,
            model='bcpp_subject.hivresult',
            visit_code=T2,
            subject_identifier=subject_visit_male_y2.subject_identifier).count()

        self.assertEqual(crf_count, 1)

    @tag('reviewed')
    def test_Known_hiv_pos_y3_not_hic_require_no_testing_missed_y2(self):

        # Known POS in T0
        self.make_hivtesting_history(
            self.bhs_subject_visit_male, YES, YES,
            POS, NO, self.bhs_subject_visit_male.report_datetime)

        self.hivtest_review(
            self.bhs_subject_visit_male, POS,
            self.bhs_subject_visit_male.report_datetime)

        subject_visit_male_y2 = self.add_subject_visit_followup(
            self.bhs_subject_visit_male.household_member, T1)

        # Misses T1, and is seen again at T2. They should not be Tested.
        report_datetime = self.get_utcnow() + relativedelta(years=3, months=6)
        self.consent_data.update(
            report_datetime=self.get_utcnow() + relativedelta(years=3, months=6))

        self.add_subject_visit_followup(
            subject_visit_male_y2.household_member,
            T2, household_log_report_date=report_datetime,
            **self.consent_data)

        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.hivresult', NOT_REQUIRED, T2).count(), 1)

    @tag("reviewed")
    def test_hic_enrolled_at_bhs(self):
        """ If there is an hic record at bhs then at ahs inspect the record
            then check for hic status if not enrolled then Hic_enrollment
            should be filled otherwise should not be filled.
        """
        self.make_subject_locator(
            self.subject_identifier,
            self.bhs_subject_visit_male.report_datetime)

        self.make_residency_mobility(
            self.bhs_subject_visit_male, YES,
            NO, self.bhs_subject_visit_male.report_datetime)

        self.hiv_result(
            NEG, self.bhs_subject_visit_male,
            self.bhs_subject_visit_male.report_datetime)

        self.make_hic_enrolment(
            self.bhs_subject_visit_male, YES,
            self.bhs_subject_visit_male.report_datetime)

        subject_visit_male_y2 = self.add_subject_visit_followup(
            self.bhs_subject_visit_male.household_member, T1)

        self.assertEqual(self.crf_metadata_obj(
            'bcpp_subject.hicenrollment', NOT_REQUIRED, T1).count(), 1)

        report_datetime = self.get_utcnow() + relativedelta(years=3, months=6)
        self.consent_data.update(
            report_datetime=self.get_utcnow() + relativedelta(years=3, months=6))

        self.add_subject_visit_followup(
            subject_visit_male_y2.household_member,
            T2, household_log_report_date=report_datetime,
            **self.consent_data)

        self.assertEqual(self.crf_metadata_obj(
            'bcpp_subject.hicenrollment', NOT_REQUIRED, T2).count(), 1)

    def test_known_neg_at_bhs_todays_hiv_required(self):
        """ Assert if a known smc neg at bhs today's HIV is required.
        """
        self.make_subject_locator(
            self.subject_identifier,
            self.bhs_subject_visit_male.report_datetime)

        circumcision_data = {
            "circumcised": "No",
            "circumcised_datetime": None,
            "circumcised_location": "N/A",
            "last_seen_circumcised": None,
            "report_datetime": self.bhs_subject_visit_male.report_datetime,
            "subject_visit": self.bhs_subject_visit_male}

        mommy.make_recipe(
            'bcpp_subject.circumcision',
            **circumcision_data)

        hivresultdocumentation_data = {
            "report_datetime": self.bhs_subject_visit_male.report_datetime,
            "result_date": date(2013, 10, 18),
            'result_recorded': NEG,
            "result_doc_type": "Tebelopele",
            "subject_visit": self.bhs_subject_visit_male}

        mommy.make_recipe(
            'bcpp_subject.hivresultdocumentation',
            **hivresultdocumentation_data)

        hivtested_data = {
            "arvs_hiv_test": "Yes",
            "hiv_pills": "Yes",
            "num_hiv_tests": 2,
            "report_datetime": self.bhs_subject_visit_male.report_datetime,
            "where_hiv_test": "Tebelopele VCT center",
            "why_hiv_test": "I read information on a brochure/flier that it is important for me to get tested for HIV",
            "subject_visit": self.bhs_subject_visit_male}

        mommy.make_recipe(
            'bcpp_subject.hivtested',
            **hivtested_data)

        hivtestinghistory_data = {
            "has_record": "Yes",
            "has_tested": "Yes",
            "other_record": "N/A",
            "report_datetime": self.bhs_subject_visit_male.report_datetime,
            "verbal_hiv_result": "NEG",
            "when_hiv_test": "6 to 12 months ago",
            "subject_visit": self.bhs_subject_visit_male}

        mommy.make_recipe(
            'bcpp_subject.hivtestinghistory',
            **hivtestinghistory_data)

        hivtestreview_data = {
            "hiv_test_date": "2013-09-14",
            "recorded_hiv_result": "NEG",
            "report_datetime": self.bhs_subject_visit_male.report_datetime,
            "subject_visit": self.bhs_subject_visit_male}

        mommy.make_recipe(
            'bcpp_subject.hivtestreview',
            **hivtestreview_data)

        uncircumcised_data = {
            "aware_free": "Television",
            "circumcised": "No",
            "future_circ": "Yes",
            "future_reasons_smc": "More information about risks",
            "reason_circ": "Procedure might be painful",
            "report_datetime": self.bhs_subject_visit_male.report_datetime,
            "service_facilities": "Yes",
            "subject_visit": self.bhs_subject_visit_male}

        mommy.make_recipe(
            'bcpp_subject.uncircumcised',
            **uncircumcised_data)

        self.make_residency_mobility(
            self.bhs_subject_visit_male, YES,
            NO, self.bhs_subject_visit_male.report_datetime)

        self.hiv_result(
            NEG, self.bhs_subject_visit_male,
            self.bhs_subject_visit_male.report_datetime)

        self.make_hic_enrolment(
            self.bhs_subject_visit_male, YES,
            self.bhs_subject_visit_male.report_datetime)

        self.add_subject_visit_followup(
            self.bhs_subject_visit_male.household_member, T1)

        self.assertEqual(self.crf_metadata_obj(
            'bcpp_subject.hivresult', REQUIRED, T1).count(), 1)

    @tag("reviewed")
    def test_hic_not_enrolled_at_bhs(self):
        """ Assert if is an hic record inspect the record then check for hic
            status if not enrolled then Hic_enrollment
            should be offered again at T1.
        """
        self.make_subject_locator(
            self.subject_identifier,
            self.bhs_subject_visit_male.report_datetime)

        self.make_residency_mobility(
            self.bhs_subject_visit_male, YES,
            NO, self.bhs_subject_visit_male.report_datetime)

        self.hiv_result(
            NEG, self.bhs_subject_visit_male,
            self.bhs_subject_visit_male.report_datetime)

        self.make_hic_enrolment(
            self.bhs_subject_visit_male, NO,
            self.bhs_subject_visit_male.report_datetime)

        subject_visit_male_y2 = self.add_subject_visit_followup(
            self.bhs_subject_visit_male.household_member, T1)

        self.hiv_result(
            NEG, subject_visit_male_y2,
            subject_visit_male_y2.report_datetime)

        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.hicenrollment', REQUIRED, T1).count(), 1)

    def test_hiv_pos_nd_art_naive_at_ahs_new_erollee(self):
        """New enrollees at T0 (i.e doing BHS procedures)
            who are HIV-positive and ART naive, then pimacd4 required.
        """
        # Known POS in T0
        self.make_hivtesting_history(
            self.bhs_subject_visit_male, YES, YES,
            POS, NO, report_datetime=self.get_utcnow())

        self.hivtest_review(
            self.bhs_subject_visit_male, POS, report_datetime=self.get_utcnow())

        subject_visit_male_y2 = self.add_subject_visit_followup(
            self.bhs_subject_visit_male.household_member, T1)
        report_datetime = subject_visit_male_y2.report_datetime

        # add HivCarAdherence,
        self.make_hiv_care_adherence(
            subject_visit_male_y2, NO, NO, NO, NO, NO, report_datetime)

        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.pimacd4', REQUIRED, T1).count(), 1)

    @tag("reviewed")
    def test_hiv_pos_nd_art_naive_at_ahs(self):
        """Previously enrollees at t0 who are HIV-positive but were not on ART,
            (i.e arv_naive) at the time of enrollment. Still arv_naive at AHS.
            pimacd4 and VL required. RBD keyed in T0, so not required.
        """
        # Known POS in T0
        self.make_hivtesting_history(
            self.bhs_subject_visit_male, YES, YES,
            POS, NO, self.bhs_subject_visit_male.report_datetime)

        self.hivtest_review(
            self.bhs_subject_visit_male, POS,
            self.bhs_subject_visit_male.report_datetime)

        self.assertEqual(
            self.requisition_metadata_obj(
                'bcpp_subject.subjectrequisition', REQUIRED,
                T0, RESEARCH_BLOOD_DRAW).count(), 1)

        self.make_requisition(
            self.bhs_subject_visit_male, RESEARCH_BLOOD_DRAW,
            self.bhs_subject_visit_male.report_datetime)

        # add HivCarAdherence,
        self.make_hiv_care_adherence(
            self.bhs_subject_visit_male, NO, NO, NO,
            NO, NO, self.bhs_subject_visit_male.report_datetime)

        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.pimacd4', REQUIRED, T0).count(), 1)
        self.assertEqual(self.requisition_metadata_obj(
            'bcpp_subject.subjectrequisition', REQUIRED,
            T0, VIRAL_LOAD).count(), 1)
        self.assertEqual(self.requisition_metadata_obj(
            'bcpp_subject.subjectrequisition', KEYED,
            T0, RESEARCH_BLOOD_DRAW).count(), 1)

        subject_visit_male_y2 = self.add_subject_visit_followup(
            self.bhs_subject_visit_male.household_member, T1)
        report_datetime = subject_visit_male_y2.report_datetime

        # add HivCarAdherence,
        self.make_hiv_care_adherence(
            subject_visit_male_y2, NO, YES,
            NO, NO, NO, report_datetime)

        self.assertEqual(
            self.crf_metadata_obj('bcpp_subject.pimacd4', REQUIRED, T1).count(), 1)
        self.assertEqual(self.requisition_metadata_obj(
            'bcpp_subject.subjectrequisition', REQUIRED, T1, VIRAL_LOAD).count(), 1)
        self.assertEqual(self.requisition_metadata_obj(
            'bcpp_subject.subjectrequisition', NOT_REQUIRED,
            T1, RESEARCH_BLOOD_DRAW).count(), 1)

    @tag("need_to_confirm_helper_not_correct")
    def test_hiv_pos_nd_on_art_at_ahs(self):
        """Assert that previously enrollees at t0 who are HIV-positive but were
            not on ART (i.e arv_naive) at the time of enrollment. But now on
            ART at T1. pimacd4 and VL required at T1(rule: art naive at enrollment).
            RBD keyed in T0, so not required. POC VL not required at T1.
        """
        # Known POS in T0
        self.make_hivtesting_history(
            self.bhs_subject_visit_male, YES, YES,
            POS, NO, self.bhs_subject_visit_male.report_datetime)

        self.hivtest_review(
            self.bhs_subject_visit_male, POS,
            self.bhs_subject_visit_male.report_datetime)

        self.make_hiv_care_adherence(
            self.bhs_subject_visit_male, NO, YES, NO,
            NO, NO, report_datetime=self.get_utcnow())

        self.assertEqual(
            self.requisition_metadata_obj(
                'bcpp_subject.subjectrequisition',
                REQUIRED, T0, RESEARCH_BLOOD_DRAW).count(), 1)

        self.make_requisition(
            self.bhs_subject_visit_male, RESEARCH_BLOOD_DRAW,
            self.bhs_subject_visit_male.report_datetime)

        subject_visit_male_y2 = self.add_subject_visit_followup(
            self.bhs_subject_visit_male.household_member, T1)
        report_datetime = subject_visit_male_y2.report_datetime

        # add HivCarAdherence,
        self.make_hiv_care_adherence(
            subject_visit_male_y2, YES, YES, YES,
            YES, YES, report_datetime=report_datetime)

        self.assertEqual(
            self.crf_metadata_obj('bcpp_subject.pimacd4', REQUIRED, T1).count(), 1)
        self.assertEqual(
            self.requisition_metadata_obj(
                'bcpp_subject.subjectrequisition', REQUIRED, T1, VIRAL_LOAD).count(), 1)
        self.assertEqual(
            self.requisition_metadata_obj(
                'bcpp_subject.subjectrequisition', NOT_REQUIRED,
                T1, RESEARCH_BLOOD_DRAW).count(), 1)

        report_datetime = self.get_utcnow() + relativedelta(years=3, months=6)
        self.consent_data.update(
            report_datetime=self.get_utcnow() + relativedelta(years=3, months=6))

        ahs_subject_visit_male_y3 = self.add_subject_visit_followup(
            subject_visit_male_y2.household_member,
            T2, household_log_report_date=report_datetime,
            **self.consent_data)
        report_datetime = ahs_subject_visit_male_y3.report_datetime

        # add HivCarAdherence,
        self.make_hiv_care_adherence(
            ahs_subject_visit_male_y3, YES, YES,
            YES, YES, YES, report_datetime=report_datetime)

        self.assertEqual(
            self.crf_metadata_obj('bcpp_subject.pimacd4', REQUIRED, T2).count(), 1)
        self.assertEqual(
            self.requisition_metadata_obj(
                'bcpp_subject.subjectrequisition', REQUIRED,
                T2, VIRAL_LOAD).count(), 1)
        self.assertEqual(
            self.requisition_metadata_obj(
                'bcpp_subject.subjectrequisition', NOT_REQUIRED,
                T2, RESEARCH_BLOOD_DRAW).count(), 1)

    @tag("test_hiv_pos_nd_on_art_at_y3_missed_y2")
    def test_hiv_pos_nd_on_art_at_y3_missed_y2(self):
        """Previously enrollees at t0 who are HIV-positive but were not on ART
            (i.e arv_naive) at the time of enrollment. Misses T1. But now on
            ART at T2. pimacd4 and VL required at T2(rule: art naive at enrollment).
            RBD keyed in T0, so not required. POC VL not required at T2.
        """

        # Known POS in T0
        mommy.make_recipe(
            'bcpp_subject.hivtestinghistory',
            subject_visit=self.bhs_subject_visit_male,
            has_tested=YES,
            when_hiv_test='1 to 5 months ago',
            has_record=YES,
            verbal_hiv_result=POS,
            other_record=NO,
            report_datetime=self.bhs_subject_visit_male.report_datetime
        )
        mommy.make_recipe(
            'bcpp_subject.hivtestreview',
            report_datetime=self.bhs_subject_visit_male.report_datetime,
            subject_visit=self.bhs_subject_visit_male,
            hiv_test_date=self.get_utcnow() - timedelta(days=50),
            recorded_hiv_result=POS)

        # add HivCarAdherence,
        mommy.make_recipe(
            'bcpp_subject.hivcareadherence',
            first_positive=self.get_utcnow(),
            subject_visit=self.bhs_subject_visit_male,
            report_datetime=self.bhs_subject_visit_male.report_datetime,
            medical_care=YES,
            ever_recommended_arv=NO,
            ever_taken_arv=NO,
            on_arv=NO,
            arv_evidence=NO,  # this is the rule field
        )

        mommy.make_recipe(
            'bcpp_subject.subjectrequisition',
            subject_visit=self.bhs_subject_visit_male,
            report_datetime=self.bhs_subject_visit_male.report_datetime,
            panel_name=RESEARCH_BLOOD_DRAW,
        )

        subject_visit_male_y2 = self.add_subject_visit_followup(
            self.bhs_subject_visit_male.household_member, T1)

        report_datetime = self.get_utcnow() + relativedelta(years=3, months=6)
        self.consent_data.update(
            report_datetime=self.get_utcnow() + relativedelta(years=3, months=6))

        ahs_subject_visit_male_y3 = self.add_subject_visit_followup(
            subject_visit_male_y2.household_member,
            T2, household_log_report_date=report_datetime,
            **self.consent_data)

        mommy.make_recipe(
            'bcpp_subject.hivcareadherence',
            first_positive=self.get_utcnow(),
            subject_visit=ahs_subject_visit_male_y3,
            report_datetime=ahs_subject_visit_male_y3.report_datetime,
            medical_care=YES,
            ever_recommended_arv=YES,
            ever_taken_arv=YES,
            on_arv=YES,
            arv_evidence=YES,  # this is the rule field
        )
        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.pimacd4', REQUIRED, T2).count(), 1)
        self.assertEqual(self.requisition_metadata_obj(
            'bcpp_subject.subjectrequisition', REQUIRED,
            T2, VIRAL_LOAD).count(), 1)
        self.assertEqual(self.requisition_metadata_obj(
            'bcpp_subject.subjectrequisition', NOT_REQUIRED,
            T2, RESEARCH_BLOOD_DRAW).count(), 1)

    @tag("reviewed")
    def test_hiv_pos_nd_not_on_art_at_ahs(self):
        """Previously enrollees at t0 who are HIV-positive but were not on ART
            (i.e art_naive) at the time of enrollment. pimacd4 required.
            Still HIV Positive and still not on ART at T1:
            Should offer POC CD4 and VL. No RBD
        """
        # Known POS in T0
        mommy.make_recipe(
            'bcpp_subject.hivtestinghistory',
            subject_visit=self.bhs_subject_visit_male,
            has_tested=YES,
            when_hiv_test='1 to 5 months ago',
            has_record=YES,
            verbal_hiv_result=POS,
            other_record=NO,
            report_datetime=self.bhs_subject_visit_male.report_datetime)

        self.hivtest_review(
            self.bhs_subject_visit_male, POS,
            self.bhs_subject_visit_male.report_datetime)
        self.assertEqual(self.crf_metadata_obj(
            'bcpp_subject.hivcareadherence', REQUIRED, T0).count(), 1)

        # ART naive at the time of enrollment, in this case T0.
        mommy.make_recipe(
            'bcpp_subject.hivcareadherence',
            first_positive=self.get_utcnow(),
            subject_visit=self.bhs_subject_visit_male,
            report_datetime=self.bhs_subject_visit_male.report_datetime,
            medical_care=NO,
            ever_recommended_arv=NO,
            ever_taken_arv=NO,
            on_arv=NO,
            arv_evidence=NO,  # this is the rule field
        )

        self.assertEqual(self.requisition_metadata_obj(
            'bcpp_subject.subjectrequisition', REQUIRED,
            T0, RESEARCH_BLOOD_DRAW).count(), 1)

        self.make_requisition(
            self.bhs_subject_visit_male, RESEARCH_BLOOD_DRAW, self.get_utcnow())

        self.assertEqual(self.requisition_metadata_obj(
            'bcpp_subject.subjectrequisition', KEYED,
            T0, RESEARCH_BLOOD_DRAW).count(), 1)

        # Move on to the first annual visit.
        subject_visit_male_y2 = self.add_subject_visit_followup(
            self.bhs_subject_visit_male.household_member, T1)

        self.assertEqual(
            self.crf_metadata_obj('bcpp_subject.pimacd4', REQUIRED, T1).count(), 1)
        self.assertEqual(self.requisition_metadata_obj(
            'bcpp_subject.subjectrequisition', REQUIRED,
            T1, VIRAL_LOAD).count(), 1)
        self.assertEqual(self.requisition_metadata_obj(
            'bcpp_subject.subjectrequisition', NOT_REQUIRED,
            T1, RESEARCH_BLOOD_DRAW).count(), 1)
        report_datetime = self.get_utcnow() + relativedelta(years=3, months=6)
        self.consent_data.update(
            report_datetime=self.get_utcnow() + relativedelta(years=3, months=6))
        # Move on to the second annual visit.
        self.add_subject_visit_followup(
            subject_visit_male_y2.household_member,
            T2, household_log_report_date=report_datetime,
            **self.consent_data)

    @tag("reviewed_hic")
    def test_hiv_pos_nd_not_on_art_at_y3_missed_y2(self):
        """Previously enrollees at t0 who are HIV-positive but were not on ART
            (i.e art_naive) at the time of enrollment. pimacd4 required. Misses
            T1. Found at T2 still HIV Positive and still not on ART:
            Should offer POC CD4 and VL. No RBD.
        """
        # Known POS in T0
        mommy.make_recipe(
            'bcpp_subject.hivtestinghistory',
            subject_visit=self.bhs_subject_visit_male,
            report_datetime=self.get_utcnow(),
            has_tested=YES,
            when_hiv_test='1 to 5 months ago',
            has_record=YES,
            verbal_hiv_result=POS,
            other_record=NO
        )
        self.hivtest_review(self.bhs_subject_visit_male, POS)
        self.assertEqual(self.crf_metadata_obj(
            'bcpp_subject.hivcareadherence', REQUIRED, T0).count(), 1)
        # ART naive at the time of enrollment, in this case T0.
        mommy.make_recipe(
            'bcpp_subject.hivcareadherence',
            first_positive=self.get_utcnow(),
            subject_visit=self.bhs_subject_visit_male,
            report_datetime=self.get_utcnow(),
            medical_care=NO,
            ever_recommended_arv=NO,
            ever_taken_arv=NO,
            on_arv=NO,
            arv_evidence=NO,  # this is the rule field
        )

        self.assertEqual(self.requisition_metadata_obj(
            'bcpp_subject.subjectrequisition', REQUIRED,
            T0, RESEARCH_BLOOD_DRAW).count(), 1)

        self.make_requisition(self.bhs_subject_visit_male, RESEARCH_BLOOD_DRAW)

        self.assertEqual(self.requisition_metadata_obj(
            'bcpp_subject.subjectrequisition', KEYED,
            T0, RESEARCH_BLOOD_DRAW).count(), 1)

        subject_visit_male_y2 = self.add_subject_visit_followup(
            self.bhs_subject_visit_male.household_member, T1)
        # JUMP first annual visit. Move on to the second annual visit.
        report_datetime = self.get_utcnow() + relativedelta(years=3, months=6)
        self.consent_data.update(
            report_datetime=self.get_utcnow() + relativedelta(years=3, months=6))
        # Move on to the second annual visit.
        self.add_subject_visit_followup(
            subject_visit_male_y2.household_member,
            T2, household_log_report_date=report_datetime,
            **self.consent_data)

        self.assertEqual(
            self.crf_metadata_obj('bcpp_subject.pimacd4', REQUIRED, T2).count(), 1)
        self.assertEqual(self.requisition_metadata_obj(
            'bcpp_subject.subjectrequisition', REQUIRED,
            T2, VIRAL_LOAD).count(), 1)
        self.assertEqual(self.requisition_metadata_obj(
            'bcpp_subject.subjectrequisition', NOT_REQUIRED,
            T2, RESEARCH_BLOOD_DRAW).count(), 1)

    @tag('test_hiv_pos_nd_on_art_at_ahs1')
    def test_hiv_pos_nd_on_art_at_ahs1(self):
        """Previously enrollees at t0 who are HIV-positive but were not on ART
            naive at the time of enrollment.
           pimacd4 required. HIV Positive not on ART at T1:
           Should offer POC CD4 and VL.
        """
        self.subject_identifier = self.bhs_subject_visit_male.subject_identifier

        self.make_hivtesting_history(
            self.bhs_subject_visit_male, YES, YES, POS, NO, self.get_utcnow())

        self.hivtest_review(
            self.bhs_subject_visit_male, POS, self.get_utcnow())

        # add HivCarAdherence,
        report_datetime = self.bhs_subject_visit_male.report_datetime
        self.make_hiv_care_adherence(
            self.bhs_subject_visit_male, NO, NO, NO,
            NO, NO, report_datetime=report_datetime)

        # self.annual_subject_visit_y2
        subject_visit_male_y2 = self.add_subject_visit_followup(
            self.bhs_subject_visit_male.household_member, T1)

        report_datetime = subject_visit_male_y2.report_datetime

        self.make_hiv_care_adherence(
            subject_visit_male_y2, YES, YES,
            YES, YES, YES, report_datetime)

        self.assertEqual(
            self.crf_metadata_obj('bcpp_subject.pimacd4', REQUIRED, T1).count(), 1)
        self.assertEqual(
            self.requisition_metadata_obj(
                'bcpp_subject.subjectrequisition', REQUIRED,
                T1, VIRAL_LOAD).count(), 1)

        report_datetime = self.get_utcnow() + relativedelta(years=3, months=6)
        self.consent_data.update(
            report_datetime=self.get_utcnow() + relativedelta(years=3, months=6))

        ahs_subject_visit_male_y3 = self.add_subject_visit_followup(
            subject_visit_male_y2.household_member,
            T2, household_log_report_date=report_datetime,
            **self.consent_data)
        report_datetime = ahs_subject_visit_male_y3.report_datetime

        self.make_hiv_care_adherence(
            ahs_subject_visit_male_y3, YES, YES,
            YES, YES, YES, report_datetime)

        self.assertEqual(
            self.crf_metadata_obj('bcpp_subject.pimacd4', REQUIRED, T1).count(), 1)
        self.assertEqual(
            self.requisition_metadata_obj(
                'bcpp_subject.subjectrequisition', REQUIRED,
                T1, VIRAL_LOAD).count(), 1)

    @tag("reviewed2")
    def test_hiv_pos_nd_not_art_at_y1_misses_y2(self):
        """Previously enrollees at t0 who are HIV-positive but were ART naive
            at the time of enrollment. pimacd4 required. Misses T2. HIV Positive
            and on ART at T3: Should offer POC CD4 and VL.
        """
        self.make_hivtesting_history(
            self.bhs_subject_visit_male, YES, YES, POS, NO)
        self.hivtest_review(self.bhs_subject_visit_male, POS)

        # add HivCarAdherence,
        self.make_hiv_care_adherence(
            self.bhs_subject_visit_male, NO, NO, NO, NO, NO, self.get_utcnow())

        subject_visit_male_y2 = self.add_subject_visit_followup(
            self.bhs_subject_visit_male.household_member, T1)

        report_datetime = self.get_utcnow() + relativedelta(years=3, months=6)
        self.consent_data.update(
            report_datetime=self.get_utcnow() + relativedelta(years=3, months=6))

        ahs_subject_visit_male_y3 = self.add_subject_visit_followup(
            subject_visit_male_y2.household_member,
            T2, household_log_report_date=report_datetime,
            **self.consent_data)

        report_datetime = ahs_subject_visit_male_y3.report_datetime

        self.make_hiv_care_adherence(
            ahs_subject_visit_male_y3, YES, YES,
            YES, YES, YES, report_datetime)

        self.assertEqual(
            self.crf_metadata_obj('bcpp_subject.pimacd4', REQUIRED, T2).count(), 1)
        self.assertEqual(
            self.requisition_metadata_obj(
                'bcpp_subject.subjectrequisition', REQUIRED,
                T2, VIRAL_LOAD).count(), 1)

    def hiv_pos_nd_on_art_bhs(self):
        """Enrollees at t0 who are HIV-positive and on ART at the time of enrollment.
           pimacd4 and POC VL NOT required. RBD, VL required.
        """

        self.hiv_result(POS, self.bhs_subject_visit_male)

        # add HivCarAdherence,
        self.make_hiv_care_adherence(
            self.bhs_subject_visit_male, YES, YES,
            YES, YES, YES, self.get_utcnow())

        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.pimacd4', NOT_REQUIRED, T0).count(), 1)
        self.assertEqual(
            self.requisition_metadata_obj(
                'bcpp_subject.subjectrequisition', REQUIRED,
                T0, VIRAL_LOAD).count(), 1)

        self.assertEqual(
            self.requisition_metadata_obj(
                'bcpp_subject.subjectrequisition', REQUIRED,
                T0, RESEARCH_BLOOD_DRAW).count(), 1)

    @tag("reviewed")
    def hiv_pos_nd_on_art_ahs(self):
        """Previously enrollees at t0 who are HIV-positive on ART at the time
            of enrollment. pimacd4 and POC VL NOT required. RBD, VL required.
        """
        self.hiv_pos_nd_on_art_bhs()

        subject_visit_male_y2 = self.add_subject_visit_followup(
            self.bhs_subject_visit_male.household_member, T1)

        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.pimacd4', NOT_REQUIRED, T1).count(), 1)
        self.assertEqual(
            self.requisition_metadata_obj(
                'bcpp_subject.subjectrequisition', NOT_REQUIRED,
                T1, VIRAL_LOAD).count(), 1)

        report_datetime = self.get_utcnow() + relativedelta(years=3, months=6)
        self.consent_data.update(
            report_datetime=self.get_utcnow() + relativedelta(years=3, months=6))

        self.add_subject_visit_followup(
            subject_visit_male_y2.household_member,
            T2, household_log_report_date=report_datetime,
            **self.consent_data)

        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.pimacd4', NOT_REQUIRED, T2).count(), 1)
        self.assertEqual(
            self.requisition_metadata_obj(
                'bcpp_subject.subjectrequisition', NOT_REQUIRED,
                T2, VIRAL_LOAD).count(), 1)

#     @tag("reviewed_pima")
#     def test_hiv_neg_bhs_and_pos_at_ahs(self):
#         """ HIV Negative and in HIC at T0 and now HIV POS not on ART at T1,
#             should Offer POC CD4, RBD and VL and pimacd4 VL.
#         """
#         self.make_subject_locator(self.subject_identifier, self.get_utcnow())
#
#         self.make_residency_mobility(self.bhs_subject_visit_male, YES, NO)
#
#         self.hiv_result(NEG, self.bhs_subject_visit_male, self.get_utcnow())
#
#         self.make_hic_enrolment(
#             self.bhs_subject_visit_male, YES, self.get_utcnow())
#
#         # self.annual_subject_visit_y2
#         subject_visit_male_y2 = self.add_subject_visit_followup(
#             self.bhs_subject_visit_male.household_member, T1)
#         report_datetime = subject_visit_male_y2.report_datetime
#
#         self.hiv_result(POS, subject_visit_male_y2, report_datetime)
#
#         self.assertEqual(
#             self.crf_metadata_obj('bcpp_subject.pimacd4', REQUIRED, T1).count(), 1)
#         self.assertEqual(
#             self.requisition_metadata_obj(
#                 'bcpp_subject.subjectrequisition', REQUIRED,
#                 T1, VIRAL_LOAD).count(), 1)
#         self.assertEqual(
#             self.requisition_metadata_obj(
#                 'bcpp_subject.subjectrequisition', REQUIRED,
#                 T1, RESEARCH_BLOOD_DRAW).count(), 1)

    def hiv_pos_at_bhs_and_hiv_care_adherence_is_required(self):
        """Enrollees at t0 who are HIV-positive and on ART at the time of
            enrollment. pimacd4 and POC VL NOT required. RBD, VL required.
        """
        self.hiv_result(POS, self.bhs_subject_visit_male, self.get_utcnow())

        self.add_subject_visit_followup(
            self.bhs_subject_visit_male.household_member, T1)

        self.assertEqual(self.crf_metadata_obj(
            'bcpp_subject.hivcareadherence', REQUIRED, T1).count(), 1)

    @tag('reviewed2')
    def test_not_known_pos_runs_hiv_and_cd4_ahs(self):
        """If not a known POS, requires HIV and CD4 (until
        today's result is known).
        """

        self.make_subject_locator(self.subject_identifier, self.get_utcnow())

        self.hiv_result(
            DECLINED, self.bhs_subject_visit_male, self.get_utcnow())

        subject_visit_male_y2 = self.add_subject_visit_followup(
            self.bhs_subject_visit_male.household_member, T1)
        report_datetime = subject_visit_male_y2.report_datetime

        self.hiv_result(POS, subject_visit_male_y2, report_datetime)

        self.assertEqual(
            self.requisition_metadata_obj(
                'bcpp_subject.subjectrequisition', REQUIRED,
                T1, VIRAL_LOAD).count(), 1)
        self.assertEqual(
            self.requisition_metadata_obj(
                'bcpp_subject.subjectrequisition', REQUIRED,
                T1, RESEARCH_BLOOD_DRAW).count(), 1)

    def test_not_known_neg_runs_hiv_and_cd4_ahs_1(self):
        """Assert If not a known POS, HIV and CD4 required."""

        self.make_subject_locator(self.subject_identifier, self.get_utcnow())

        self.hiv_result(NEG, self.bhs_subject_visit_male)

        subject_visit_male_y2 = self.add_subject_visit_followup(
            self.bhs_subject_visit_male.household_member, T1)
        report_datetime = subject_visit_male_y2.report_datetime

        self.hiv_result(
            DECLINED, subject_visit_male_y2, report_datetime)
        self.assertEqual(
            self.requisition_metadata_obj(
                'bcpp_subject.subjectrequisition', NOT_REQUIRED,
                T1, VIRAL_LOAD).count(), 1)
        self.assertEqual(
            self.requisition_metadata_obj(
                'bcpp_subject.subjectrequisition', NOT_REQUIRED,
                T1, RESEARCH_BLOOD_DRAW).count(), 1)

    @tag('pimacd4cd4')
    def test_not_known_pos_runs_hiv_and_cd4_ahs_2(self):
        """If not a known POS, requires HIV and CD4 ."""

        self.make_subject_locator(self.subject_identifier, self.get_utcnow())

        self.hiv_result(POS, self.bhs_subject_visit_male, self.get_utcnow())

        subject_visit_male_y2 = self.add_subject_visit_followup(
            self.bhs_subject_visit_male.household_member, T1)
        report_datetime = subject_visit_male_y2.report_datetime

        self.hiv_result(
            DECLINED, subject_visit_male_y2, report_datetime)

        self.assertEqual(
            self.crf_metadata_obj('bcpp_subject.pimacd4', REQUIRED, T1).count(), 1)
        self.assertEqual(
            self.requisition_metadata_obj(
                'bcpp_subject.subjectrequisition', REQUIRED,
                T1, VIRAL_LOAD).count(), 1)

    def test_not_known_pos_runs_hiv_and_cd4_ahs_y3(self):
        """If not a known POS, requires HIV and CD4 (until
        today's result is known).
        """
        self.make_subject_locator(self.subject_identifier, self.get_utcnow())

        self.hiv_result(
            DECLINED, self.bhs_subject_visit_male, self.get_utcnow())

        self.make_hivtesting_history(
            self.bhs_subject_visit_male,
            "DWTA", "Don't want to answer", "not_answering", NO)

        subject_visit_male_y2 = self.add_subject_visit_followup(
            self.bhs_subject_visit_male.household_member, T1)
        report_datetime = subject_visit_male_y2.report_datetime

        self.hiv_result(
            DECLINED, subject_visit_male_y2, report_datetime)

        self.make_hivtesting_history(
            subject_visit_male_y2,
            "DWTA", "Don't want to answer", "not_answering", NO,
            report_datetime)

        report_datetime = self.get_utcnow() + relativedelta(years=3, months=6)
        self.consent_data.update(
            report_datetime=self.get_utcnow() + relativedelta(years=3, months=6))

        subject_visit_male_y3 = self.add_subject_visit_followup(
            subject_visit_male_y2.household_member,
            T2, household_log_report_date=report_datetime,
            **self.consent_data)
        report_datetime = subject_visit_male_y3.report_datetime

        self.make_hivtesting_history(
            subject_visit_male_y3, YES, YES, POS, NO, report_datetime)

        self.hiv_result(POS, subject_visit_male_y3, report_datetime)

        self.assertEqual(
            self.crf_metadata_obj('bcpp_subject.pimacd4', REQUIRED, T2).count(), 1)
        self.assertEqual(
            self.requisition_metadata_obj(
                'bcpp_subject.subjectrequisition', REQUIRED, T2, VIRAL_LOAD).count(), 1)

    def test_not_known_neg_runs_hiv_and_cd4_ahs(self):
        """If not a known POS, requires HIV and CD4
        (until today's result is known).
        """
        self.make_subject_locator(self.subject_identifier, self.get_utcnow())
        self.hiv_result(
            'Declined', self.bhs_subject_visit_male, self.get_utcnow())

        subject_visit_male_y2 = self.add_subject_visit_followup(
            self.bhs_subject_visit_male.household_member, T1)
        report_datetime = subject_visit_male_y2.report_datetime

        self.hiv_result(NEG, subject_visit_male_y2, report_datetime)

        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.pimacd4', NOT_REQUIRED, T1).count(), 1)
        self.assertEqual(
            self.requisition_metadata_obj(
                'bcpp_subject.subjectrequisition',
                NOT_REQUIRED, T1, VIRAL_LOAD).count(), 1)
        self.assertEqual(
            self.requisition_metadata_obj(
                'bcpp_subject.subjectrequisition',
                NOT_REQUIRED, T1, RESEARCH_BLOOD_DRAW).count(), 1)

    @tag('pimacd4_ahs')
    def test_art_naive_at_previous_visit_and_ahs_require_linkage_to_care(self):
        """Previously enrollees at t0, t1 who are HIV-positive but
        were not on ART, (i.e arv_naive) at the time of enrollment.
        HivLinkageToCare REQUIRED.
        """
        self.hiv_pos_nd_art_naive_at_bhs()

        report_datetime = self.get_utcnow() + relativedelta(years=1)
        previous_member = self.bhs_subject_visit_male.household_member

        self.add_subject_visit_followup(previous_member, T1, report_datetime)

        self.assertEqual(self.crf_metadata_obj(
            'bcpp_subject.hivlinkagetocare', REQUIRED, T1).count(), 1)

    @tag('reviewed')
    def test_art_naive_at_previous_visit_and_ahs_require_linkage_to_care1(self):
        """Previously enrollees at t0, t1 who are HIV-positive
        but were not on ART, (i.e arv_naive) at the time of enrollment.
        HivLinkageToCare REQUIRED
        """
        self.hiv_pos_nd_art_naive_at_bhs()

        subject_visit_y2 = self.add_subject_visit_followup(
            self.bhs_subject_visit_male.household_member, T1)

        # add HivCarAdherence,
        self.make_hiv_care_adherence(
            subject_visit_y2, NO, NO, NO, NO, NO,
            subject_visit_y2.report_datetime)

        report_datetime = self.get_utcnow() + relativedelta(years=2)
        previous_member = subject_visit_y2.household_member
        subject_visit_y2 = self.add_subject_visit_followup(
            previous_member, T2, report_datetime)

        self.assertEqual(self.crf_metadata_obj(
            'bcpp_subject.hivlinkagetocare', REQUIRED, T2).count(), 1)

    @tag('test_art_naive_at_previous_visit_and_ahs_require_linkage_to_care2')
    def test_art_naive_at_previous_visit_and_ahs_require_linkage_to_care2(self):
        """Previously enrollees at t0, t1 who are HIV-positive but
        were not on ART, (i.e arv_naive) at the time of enrollment.
        HivLinkageToCare REQUIRED
        """
        self.hiv_pos_nd_art_naive_at_bhs()

        subject_visit_y2 = self.add_subject_visit_followup(
            self.bhs_subject_visit_male.household_member, T1)

        # add HivCarAdherence,
        self.make_hiv_care_adherence(
            subject_visit_y2, YES, YES, YES, YES, YES,
            subject_visit_y2.report_datetime)

        report_datetime = self.get_utcnow() + relativedelta(years=2)
        previous_member = subject_visit_y2.household_member
        subject_visit_y2 = self.add_subject_visit_followup(
            previous_member, T2, report_datetime)

        self.assertEqual(self.crf_metadata_obj(
            'bcpp_subject.hivlinkagetocare', REQUIRED, T2).count(), 1)

    @tag('reviewed')
    def test_on_art_at_previous_visit_and_ahs_require_linkage_to_care(self):
        """Previously enrollees at t0, t1 who are HIV-positive
        but were on ART, (i.e not arv_naive) at the time of enrollment.
        HivLinkageToCare NOT_REQUIRED 066-01990054-8
        """
        self.make_hivtesting_history(
            self.bhs_subject_visit_male,
            YES, YES, POS, NO, self.bhs_subject_visit_male.report_datetime)

        self.hivtest_review(
            self.bhs_subject_visit_male,
            POS, self.bhs_subject_visit_male.report_datetime)

        self.assertEqual(
            self.requisition_metadata_obj(
                'bcpp_subject.subjectrequisition',
                REQUIRED, T0, RESEARCH_BLOOD_DRAW).count(), 1)

        self.make_requisition(
            self.bhs_subject_visit_male,
            RESEARCH_BLOOD_DRAW,
            self.bhs_subject_visit_male.report_datetime)

        # add HivCarAdherence,
        self.make_hiv_care_adherence(
            self.bhs_subject_visit_male,
            NO, NO, NO, NO, NO, self.get_utcnow())

        subject_visit_male_y2 = self.add_subject_visit_followup(
            self.bhs_subject_visit_male.household_member, T1)

        # add HivCarAdherence,
        self.make_hiv_care_adherence(
            subject_visit_male_y2, YES, YES, YES, YES, NO,
            subject_visit_male_y2.report_datetime)
        report_datetime = self.get_utcnow() + relativedelta(years=3, months=6)
        self.consent_data.update(
            report_datetime=self.get_utcnow() + relativedelta(years=3, months=6))

        self.add_subject_visit_followup(
            subject_visit_male_y2.household_member,
            T2, household_log_report_date=report_datetime,
            **self.consent_data)

        self.assertEqual(self.crf_metadata_obj(
            'bcpp_subject.hivlinkagetocare', REQUIRED, T2).count(), 1)

    @tag('test_default_at_bhs_at_ahs_requires_linkage')
    def test_default_at_bhs_at_ahs_requires_linkage(self):
        """Previously enrollees at t0, t1 who are HIV-positive
        but were on ART, (i.e not arv_naive) at the time of enrollment.
        HivLinkageToCare NOT_REQUIRED 066-01990054-8
        """
        mommy.make_recipe(
            'bcpp_subject.hivtestinghistory',
            subject_visit=self.bhs_subject_visit_male,
            report_datetime=self.get_utcnow(),
            has_tested=YES,
            when_hiv_test='1 to 5 months ago',
            has_record=YES,
            verbal_hiv_result=POS,
            other_record=YES
        )

        mommy.make_recipe(
            'bcpp_subject.hivtestreview',
            report_datetime=self.get_utcnow(),
            subject_visit=self.bhs_subject_visit_male,
            hiv_test_date=self.get_utcnow() - timedelta(days=50),
            recorded_hiv_result=POS)

        mommy.make_recipe(
            'bcpp_subject.hivcareadherence',
            first_positive=self.get_utcnow(),
            subject_visit=self.bhs_subject_visit_male,
            report_datetime=self.get_utcnow(),
            medical_care=YES,
            ever_recommended_arv=YES,
            ever_taken_arv=YES,
            on_arv=NO,
            arv_evidence=YES,  # this is the rule field
        )

        self.assertEqual(
            self.requisition_metadata_obj(
                'bcpp_subject.subjectrequisition',
                REQUIRED, T0, RESEARCH_BLOOD_DRAW).count(), 1)

        subject_visit_male_y2 = self.add_subject_visit_followup(
            self.bhs_subject_visit_male.household_member, T1)

        crf_count = CrfMetadata.objects.filter(
            entry_status=REQUIRED,
            model='bcpp_subject.hivlinkagetocare',
            visit_code=subject_visit_male_y2.visit_code,
            subject_identifier=subject_visit_male_y2.subject_identifier)

        self.assertEqual(crf_count.count(), 1)

        # add HivCarAdherence,
        mommy.make_recipe(
            'bcpp_subject.hivcareadherence',
            first_positive=subject_visit_male_y2.report_datetime,
            subject_visit=subject_visit_male_y2,
            report_datetime=subject_visit_male_y2.report_datetime,
            medical_care=YES,
            ever_recommended_arv=YES,
            ever_taken_arv=YES,
            on_arv=YES,
            arv_evidence=YES,  # this is the rule field
        )
