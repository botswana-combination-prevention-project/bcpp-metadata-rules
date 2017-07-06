from model_mommy import mommy

from django.test import TestCase, tag

from edc_constants.constants import NO, YES, POS, NEG, IND, UNK, NOT_SURE
from edc_metadata.constants import REQUIRED, NOT_REQUIRED, KEYED

from ..constants import E0
from ..constants import VIRAL_LOAD, RESEARCH_BLOOD_DRAW
from ..models import CircumcisionBenefits
from .rule_group_mixins import RuleGroupMixin
from .test_mixins import SubjectMixin


@tag("COMMON_RULES")
class TestCommonMetaRuleGroups(SubjectMixin, RuleGroupMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.consent_data_male = {
            'identity': '31721515',
            'confirm_identity': '31721515', }
        survey_schedule = self.get_survey_schedule(index=2)
        self.subject_visit_male_E0 = self.make_subject_visit_for_consented_subject_male(
            E0,
            survey_schedule=survey_schedule,
            **self.consent_data_male)
        self.hiv_test_date = self.subject_visit_male_E0.report_datetime

    def test_hiv_car_adherence_and_pima1(self):
        """ HIV Positive took arv in the past but now defaulting, Should NOT offer POC CD4.
        """
        for subject_visit in [
                self.subject_visit_male_t0, self.subject_visit_male_E0]:
            self.assertEqual(
                self.crf_metadata_obj('bcpp_subject.hivcareadherence',
                                      REQUIRED, subject_visit.visit_code,
                                      subject_visit.subject_identifier).count(), 1)
            # suggest this is a defaulter
            mommy.make_recipe(
                'bcpp_subject.hivcareadherence',
                first_positive=None,
                subject_visit=subject_visit,
                report_datetime=self.get_utcnow(),
                medical_care=NO,
                ever_recommended_arv=NO,
                ever_taken_arv=YES,
                on_arv=NO,
                arv_evidence=NO)

            self.assertEqual(
                self.crf_metadata_obj('bcpp_subject.pimacd4',
                                      NOT_REQUIRED, subject_visit.visit_code,
                                      subject_visit.subject_identifier).count(), 1)

    def test_hiv_car_adherence_and_pima2(self):
        """If POS and on arv and have doc evidence, Pima not required, not a defaulter.

        Models:
            * HivCareAdherence
            * HivResult
        """
        for subject_visit in [
                self.subject_visit_male_t0, self.subject_visit_male_E0]:
            self.assertEqual(
                self.crf_metadata_obj('bcpp_subject.hivcareadherence',
                                      REQUIRED, subject_visit.visit_code,
                                      subject_visit.subject_identifier).count(), 1)

            self.assertEqual(
                self.crf_metadata_obj('bcpp_subject.pimacd4', NOT_REQUIRED, subject_visit.visit_code,
                                      subject_visit.subject_identifier).count(), 1)
            # add HivCarAdherence,
            self.make_hiv_care_adherence(
                subject_visit, self.get_utcnow(), NO, NO, NO, YES, YES)

            # on art so no need for CD4
            self.assertEqual(
                self.crf_metadata_obj('bcpp_subject.pimacd4',
                                      NOT_REQUIRED,
                                      subject_visit.visit_code,
                                      subject_visit.subject_identifier).count(), 1)

    def test_hiv_car_adherence_and_pima3(self):
        """If POS and on arv but do not have doc evidence, Pima required.

        Models:
            * HivCareAdherence
            * HivResult
        """
        for subject_visit in [
                self.subject_visit_male_t0, self.subject_visit_male_E0]:
            self.assertEqual(
                self.crf_metadata_obj('bcpp_subject.hivcareadherence',
                                      REQUIRED,
                                      subject_visit.visit_code,
                                      subject_visit.subject_identifier).count(), 1)

            self.assertEqual(
                self.crf_metadata_obj('bcpp_subject.pimacd4', NOT_REQUIRED,
                                      subject_visit.visit_code,
                                      subject_visit.subject_identifier).count(), 1)

            # add HivCarAdherence,
            self.make_hiv_care_adherence(
                subject_visit, self.get_utcnow(), NO, NO, NO, YES, NO)

            self.assertEqual(
                self.crf_metadata_obj('bcpp_subject.pimacd4', NOT_REQUIRED,
                                      subject_visit.visit_code,
                                      subject_visit.subject_identifier).count(), 1)

    def test_newly_pos_and_not_art_bhs(self):
        """Newly HIV Positive not on ART at subject_visit.visit_code, Should offer POC CD4.
        """
        for subject_visit in [
                self.subject_visit_male_t0, self.subject_visit_male_E0]:
            self.make_hiv_result(POS, subject_visit, self.get_utcnow())

            # add HivCarAdherence,
            self.make_hiv_care_adherence(
                subject_visit, self.get_utcnow(), NO, NO, NO, NO, NO)

            self.assertEqual(self.crf_metadata_obj(
                'bcpp_subject.pimacd4', REQUIRED,
                subject_visit.visit_code, subject_visit.subject_identifier).count(), 1)

    def test_not_known_pos_runs_hiv_and_cd4(self):
        """If not a known POS, requires HIV and CD4 (until today's result is known).
        """
        for subject_visit in [
                self.subject_visit_male_t0, self.subject_visit_male_E0]:
            # add hivtestreview,
            hiv_test_review = self.make_hivtest_review(
                subject_visit, NEG, self.get_utcnow(), self.hiv_test_date)

            def assert_crfs():
                self.assertEqual(
                    self.crf_metadata_obj('bcpp_subject.hivtestreview', KEYED,
                                          subject_visit.visit_code,
                                          subject_visit.subject_identifier).count(), 1)
                self.assertEqual(
                    self.crf_metadata_obj('bcpp_subject.hivresult', REQUIRED,
                                          subject_visit.visit_code,
                                          subject_visit.subject_identifier).count(), 1)
                self.assertEqual(
                    self.crf_metadata_obj('bcpp_subject.pimacd4', NOT_REQUIRED,
                                          subject_visit.visit_code,
                                          subject_visit.subject_identifier).count(), 1)

            assert_crfs()
            hiv_test_review.recorded_hiv_result = IND
            hiv_test_review.save()
            assert_crfs()

            hiv_test_review.recorded_hiv_result = UNK
            hiv_test_review.save()
            assert_crfs()

    def test_known_pos_completes_hiv_care_adherence(self):
        """If known POS (not including today's test), requires hiv_care_adherence."""
        for subject_visit in [
                self.subject_visit_male_t0, self.subject_visit_male_E0]:
            # add hivtestreview
            self.make_hivtest_review(
                subject_visit, POS, self.get_utcnow(), self.hiv_test_date)

            self.assertEqual(
                self.crf_metadata_obj('bcpp_subject.hivtestreview', KEYED,
                                      subject_visit.visit_code,
                                      subject_visit.subject_identifier).count(), 1)
            self.assertEqual(
                self.crf_metadata_obj('bcpp_subject.hivcareadherence', REQUIRED,
                                      subject_visit.visit_code,
                                      subject_visit.subject_identifier).count(), 1)

    def test_known_neg_does_not_complete_hiv_care_adherence(self):
        """If known POS (not including today's test), requires hiv_care_adherence.
        """
        for subject_visit in [
                self.subject_visit_male_t0, self.subject_visit_male_E0]:
            # add HivTestHistory,
            self.make_hivtesting_history(
                subject_visit, self.get_utcnow(), YES, YES, NEG, NO)

            self.assertEqual(
                self.crf_metadata_obj('bcpp_subject.hivtestinghistory', KEYED,
                                      subject_visit.visit_code,
                                      subject_visit.subject_identifier).count(), 1)
            self.assertEqual(
                self.crf_metadata_obj('bcpp_subject.hivtestreview', REQUIRED,
                                      subject_visit.visit_code,
                                      subject_visit.subject_identifier).count(), 1)

            # add HivTestReview,
            self.make_hivtest_review(subject_visit,
                                     NEG, self.get_utcnow(), self.hiv_test_date)

            self.assertEqual(
                self.crf_metadata_obj('bcpp_subject.hivtestreview', KEYED,
                                      subject_visit.visit_code,
                                      subject_visit.subject_identifier).count(), 1)
            self.assertEqual(
                self.crf_metadata_obj(
                    'bcpp_subject.hivcareadherence', NOT_REQUIRED,
                    subject_visit.visit_code,
                    subject_visit.subject_identifier).count(), 1)

    def test_known_neg_requires_hiv_test_today(self):
        """If previous result is NEG, need to test today (HivResult).

        See rule_groups.ReviewNotPositiveRuleGroup
        """
        for subject_visit in [
                self.subject_visit_male_t0, self.subject_visit_male_E0]:
            # add HivTestReview
            self.make_hivtest_review(
                subject_visit, NEG, self.get_utcnow(), self.hiv_test_date)
            self.assertEqual(
                self.crf_metadata_obj('bcpp_subject.hivtestreview', KEYED,
                                      subject_visit.visit_code,
                                      subject_visit.subject_identifier).count(), 1)
            self.assertEqual(
                self.crf_metadata_obj('bcpp_subject.hivresult', REQUIRED, subject_visit.visit_code,
                                      subject_visit.subject_identifier).count(), 1)

    @tag('shared_rule')
    def test_known_pos_does_not_require_hiv_test_today(self):
        """If previous result is POS, do not need to test today (HivResult).

        See rule_groups.ReviewNotPositiveRuleGroup
        """
        for subject_visit in [
                self.subject_visit_male_t0, self.subject_visit_male_E0]:
            # add hivtestreview
            self.make_hivtest_review(
                subject_visit, POS, self.get_utcnow(),
                self.hiv_test_date)

            self.assertEqual(
                self.crf_metadata_obj(
                    'bcpp_subject.hivtestreview', KEYED,
                    subject_visit.visit_code,
                    subject_visit.subject_identifier).count(), 1)
            self.assertEqual(
                self.crf_metadata_obj(
                    'bcpp_subject.hivresult', NOT_REQUIRED, subject_visit.visit_code,
                    subject_visit.subject_identifier).count(), 1)

    def test_known_pos_stigma_forms(self):
        """If known posetive, test stigma forms
        """
        self.make_hivtesting_history(
            self.subject_visit_male_t0, self.get_utcnow(), YES, YES, NEG, NO)

        self.assertEqual(
            self.crf_metadata_obj('bcpp_subject.hivtestinghistory', KEYED,
                                  self.subject_visit_male_t0.visit_code,
                                  self.subject_visit_male_t0.subject_identifier).count(), 1)
        self.assertEqual(
            self.crf_metadata_obj('bcpp_subject.stigma', REQUIRED,
                                  self.subject_visit_male_t0.visit_code,
                                  self.subject_visit_male_t0.subject_identifier).count(), 1)
        self.assertEqual(
            self.crf_metadata_obj('bcpp_subject.stigmaopinion', REQUIRED,
                                  self.subject_visit_male_t0.visit_code,
                                  self.subject_visit_male_t0.subject_identifier).count(), 1)

    def test_hiv_tested_forms(self):
        """If known posetive, test hivtested forms
        """
        for subject_visit in [
                self.subject_visit_male_t0, self.subject_visit_male_E0]:
            mommy.make_recipe(
                'bcpp_subject.hivtestinghistory',
                report_datetime=self.get_utcnow(),
                subject_visit=subject_visit,
            )
            self.assertEqual(
                self.crf_metadata_obj('bcpp_subject.hivtestinghistory', KEYED,
                                      subject_visit.visit_code,
                                      subject_visit.subject_identifier).count(), 1)
            self.assertEqual(
                self.crf_metadata_obj('bcpp_subject.hivtested', REQUIRED,
                                      subject_visit.visit_code,
                                      subject_visit.subject_identifier).count(), 1)
            self.assertEqual(
                self.crf_metadata_obj('bcpp_subject.hivuntested', NOT_REQUIRED,
                                      subject_visit.visit_code,
                                      subject_visit.subject_identifier).count(), 1)

            self.assertEqual(
                self.crf_metadata_obj('bcpp_subject.hivuntested', NOT_REQUIRED,
                                      subject_visit.visit_code,
                                      subject_visit.subject_identifier).count(), 1)
            self.assertEqual(
                self.crf_metadata_obj('bcpp_subject.hivtested', REQUIRED,
                                      subject_visit.visit_code,
                                      subject_visit.subject_identifier).count(), 1)

    def test_known_pos_on_art_no_doc_requires_cd4_only(self):
        """If previous result is POS on art but no evidence, need to run CD4 (Pima).

        See rule_groups.ReviewNotPositiveRuleGroup and
        """
        for subject_visit in [
                self.subject_visit_male_t0, self.subject_visit_male_E0]:
            # add HivTestReview,
            mommy.make_recipe(
                'bcpp_subject.hivtestreview',
                report_datetime=self.get_utcnow(),
                subject_visit=subject_visit,
                hiv_test_date=self.hiv_test_date,
                recorded_hiv_result=POS)

            self.assertEqual(
                self.crf_metadata_obj(
                    'bcpp_subject.hivcareadherence', REQUIRED,
                    subject_visit.visit_code,
                    subject_visit.subject_identifier).count(), 1)

            # add HivCareAdherence,
            hivcareadherence = mommy.make_recipe(
                'bcpp_subject.hivcareadherence',
                first_positive=None,
                subject_visit=subject_visit,
                report_datetime=self.get_utcnow(),
                medical_care=NO,
                ever_recommended_arv=NO,
                ever_taken_arv=YES,
                on_arv=YES,
                arv_evidence=NO,  # this is the rule field
                first_regimen=NO)

            self.assertEqual(
                self.crf_metadata_obj('bcpp_subject.hivtestreview', KEYED,
                                      subject_visit.visit_code,
                                      subject_visit.subject_identifier).count(), 1)
            self.assertEqual(
                self.crf_metadata_obj('bcpp_subject.hivcareadherence', KEYED,
                                      subject_visit.visit_code,
                                      subject_visit.subject_identifier).count(), 1)
            self.assertEqual(
                self.crf_metadata_obj('bcpp_subject.hivresult', NOT_REQUIRED,
                                      subject_visit.visit_code,
                                      subject_visit.subject_identifier).count(), 1)
            self.assertEqual(
                self.crf_metadata_obj('bcpp_subject.pimacd4', NOT_REQUIRED,
                                      subject_visit.visit_code,
                                      subject_visit.subject_identifier).count(), 1)

            hivcareadherence.ever_taken_arv = YES
            hivcareadherence.on_arv = NO
            hivcareadherence.save()
            self.assertEqual(self.crf_metadata_obj(
                'bcpp_subject.pimacd4', NOT_REQUIRED, subject_visit.visit_code,
                subject_visit.subject_identifier).count(), 1)

    def test_hiv_care_adherance_for_verbal_posetive_only(self):
        """HivCareAdharance form should be made available any verbal positive,
            not considering availability or lack thereof documentation.
        """
        for subject_visit in [
                self.subject_visit_male_t0, self.subject_visit_male_E0]:
            self.make_hivtesting_history(
                subject_visit, self.get_utcnow(), YES, NO, POS, NO)

            self.assertEqual(
                self.crf_metadata_obj(
                    'bcpp_subject.hivcareadherence',
                    REQUIRED,
                    subject_visit.visit_code,
                    subject_visit.subject_identifier).count(), 1)

    def test_known_pos_on_art_with_doc_requires_cd4_only(self):
        """If previous result is POS on art with doc evidence, do not run HIV or CD4.

        See rule_groups.ReviewNotPositiveRuleGroup and
        """
        for subject_visit in [
                self.subject_visit_male_t0, self.subject_visit_male_E0]:
            # add HivTestReview,
            self.make_hivtest_review(
                subject_visit, POS, self.get_utcnow(), self.hiv_test_date)

            self.assertEqual(
                self.crf_metadata_obj(
                    'bcpp_subject.hivcareadherence', REQUIRED,
                    subject_visit.visit_code,
                    subject_visit.subject_identifier).count(), 1)

            # add HivCareAdherence,
            self.make_hiv_care_adherence(
                subject_visit, self.get_utcnow(), NO, NO, NO, YES, YES)

            self.assertEqual(
                self.crf_metadata_obj(
                    'bcpp_subject.hivtestreview', KEYED, subject_visit.visit_code,
                    subject_visit.subject_identifier).count(), 1)
            self.assertEqual(
                self.crf_metadata_obj(
                    'bcpp_subject.hivcareadherence', KEYED, subject_visit.visit_code,
                    subject_visit.subject_identifier).count(), 1)
            self.assertEqual(
                self.crf_metadata_obj(
                    'bcpp_subject.hivresult', NOT_REQUIRED, subject_visit.visit_code,
                    subject_visit.subject_identifier).count(), 1)
            self.assertEqual(
                self.crf_metadata_obj('bcpp_subject.pimacd4', NOT_REQUIRED,
                                      subject_visit.visit_code,
                                      subject_visit.subject_identifier).count(), 1)

    @tag('pimacd4_common')
    def test_known_pos_no_art_but_has_doc_requires_cd4_only(self):
        """If previous result is POS on art but no evidence, need to run CD4 (Pima).

        This is a defaulter

        See rule_groups.ReviewNotPositiveRuleGroup and
        """
        for subject_visit in [
                self.subject_visit_male_t0, self.subject_visit_male_E0]:
            # add HivTestReview,
            self.make_hivtest_review(
                subject_visit, POS, self.get_utcnow(), self.hiv_test_date)

            self.assertEqual(
                self.crf_metadata_obj(
                    'bcpp_subject.hivcareadherence', REQUIRED,
                    subject_visit.visit_code,
                    subject_visit.subject_identifier).count(), 1)

            # add HivCareAdherence,
            self.make_hiv_care_adherence(
                subject_visit, self.get_utcnow(), NO, NO, NO, NO, YES)

            self.assertEqual(
                self.crf_metadata_obj(
                    'bcpp_subject.hivtestreview', KEYED,
                    subject_visit.visit_code,
                    subject_visit.subject_identifier).count(), 1)
            self.assertEqual(
                self.crf_metadata_obj(
                    'bcpp_subject.hivcareadherence', KEYED,
                    subject_visit.visit_code,
                    subject_visit.subject_identifier).count(), 1)
            self.assertEqual(
                self.crf_metadata_obj(
                    'bcpp_subject.hivresult', NOT_REQUIRED,
                    subject_visit.visit_code,
                    subject_visit.subject_identifier).count(), 1)
            self.assertEqual(
                self.crf_metadata_obj(
                    'bcpp_subject.pimacd4', NOT_REQUIRED, subject_visit.visit_code,
                    subject_visit.subject_identifier).count(), 1)

    @tag('elisa')
    def test_elisaresult_behaves_like_todayhivresult(self):
        """when an elisa result is keyed in, a +ve result should result in RBD and VL
            being REQUIRED just like Today's HivResult
        """
        for subject_visit in [
                self.subject_visit_male_t0, self.subject_visit_male_E0]:
            # add HivTestReview,
            self.make_hivtest_review(
                subject_visit, NEG, self.get_utcnow(), self.hiv_test_date)

            self.assertEqual(
                self.crf_metadata_obj('bcpp_subject.hivresult', REQUIRED,
                                      subject_visit.visit_code,
                                      subject_visit.subject_identifier).count(), 1)

            self.assertEqual(
                self.crf_metadata_obj(
                    'bcpp_subject.elisahivresult', NOT_REQUIRED,
                    subject_visit.visit_code,
                    subject_visit.subject_identifier).count(), 1)

            self.make_hiv_result(IND, subject_visit, self.get_utcnow())

            self.assertEqual(
                self.crf_metadata_obj(
                    'bcpp_subject.elisahivresult',
                    REQUIRED, subject_visit.visit_code,
                    subject_visit.subject_identifier).count(), 1)

            self.make_requisition(subject_visit, 'ELISA', self.get_utcnow())

            mommy.make_recipe(
                'bcpp_subject.elisahivresult',
                subject_visit=subject_visit, report_datetime=self.get_utcnow(),
                hiv_result=POS, hiv_result_datetime=self.get_utcnow()
            )

            self.assertEqual(
                self.crf_metadata_obj(
                    'bcpp_subject.elisahivresult',
                    KEYED, subject_visit.visit_code,
                    subject_visit.subject_identifier).count(), 1)
            self.assertEqual(self.requisition_metadata_obj(
                REQUIRED, subject_visit.visit_code,
                VIRAL_LOAD,
                subject_visit.subject_identifier).count(), 1)
            self.assertEqual(
                self.requisition_metadata_obj(
                    REQUIRED, subject_visit.visit_code,
                    RESEARCH_BLOOD_DRAW,
                    subject_visit.subject_identifier).count(), 1)

    @tag('shared_rule')
    def test_normal_circumsition_in_y1(self):

        def assert_circumsition(circumsition_entry_status,
                                uncircumcised_entry_status,
                                circumcised_entry_status, subject_visit):
            self.assertEqual(
                self.crf_metadata_obj(
                    'bcpp_subject.circumcision', circumsition_entry_status,
                    subject_visit.visit_code,
                    subject_visit.subject_identifier).count(), 1)
            self.assertEqual(
                self.crf_metadata_obj(
                    'bcpp_subject.uncircumcised', uncircumcised_entry_status,
                    subject_visit.visit_code,
                    subject_visit.subject_identifier).count(), 1)
            self.assertEqual(
                self.crf_metadata_obj(
                    'bcpp_subject.circumcised', circumcised_entry_status,
                    subject_visit.visit_code,
                    subject_visit.subject_identifier).count(), 1)

        for subject_visit in [
                self.subject_visit_male_t0, self.subject_visit_male_E0]:

            assert_circumsition(REQUIRED, REQUIRED, REQUIRED, subject_visit)
            CircumcisionBenefits.objects.all().delete()
            circumcition = mommy.make_recipe(
                'bcpp_subject.circumcision',
                subject_visit=subject_visit, report_datetime=self.get_utcnow(),
                circumcised=YES
            )
            assert_circumsition(KEYED, NOT_REQUIRED, REQUIRED, subject_visit)

            self.make_hiv_result(NEG, subject_visit, self.get_utcnow())

            # Enforce that entering an HivResult does not affect Circumcition
            # Meta Data.
            assert_circumsition(KEYED, NOT_REQUIRED, REQUIRED, subject_visit)

            circumcition.circumcised = NO
            circumcition.save()
            # uncircumcised is required,
            assert_circumsition(KEYED, REQUIRED, NOT_REQUIRED, subject_visit)

            circumcition.circumcised = NOT_SURE
            circumcition.save()

            assert_circumsition(
                KEYED, NOT_REQUIRED, NOT_REQUIRED, subject_visit)

    @tag('share_rule')
    def test_normal_circumsition_in_y1_female(self):
        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.circumcision', NOT_REQUIRED,
                self.subject_visit_female.visit_code,
                self.subject_visit_female.subject_identifier).count(), 1)
        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.uncircumcised', NOT_REQUIRED,
                self.subject_visit_female.visit_code,
                self.subject_visit_female.subject_identifier).count(), 1)
        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.circumcised', NOT_REQUIRED,
                self.subject_visit_female.visit_code,
                self.subject_visit_female.subject_identifier).count(), 1)

    @tag('shared_rule')
    def test_Known_hiv_pos_y1_require_no_testing(self):
        for subject_visit in [
                self.subject_visit_male_t0, self.subject_visit_male_E0]:
            self.make_hivtesting_history(
                subject_visit, self.get_utcnow(), YES, YES, POS, NO)

            self.make_hivtest_review(
                subject_visit, POS, self.get_utcnow(), self.hiv_test_date)

            self.assertEqual(
                self.crf_metadata_obj(
                    'bcpp_subject.hivresult',
                    NOT_REQUIRED, subject_visit.visit_code,
                    subject_visit.subject_identifier).count(), 1)

    @tag('shared_rule')
    def hiv_pos_nd_art_naive_at_bhs(self):
        """Enrollees at subject_visit.visit_code who are HIV-positive and ART naive at BHS.
           Pima, RBD and VL required. Then Key RBD for later use in Annual survey.
        """
        for subject_visit in [
                self.subject_visit_male_t0, self.subject_visit_male_E0]:
            # Known POS in subject_visit.visit_code

            self.make_hivtesting_history(
                subject_visit, self.get_utcnow(), YES, YES, POS, NO)

            self.make_hivtest_review(
                subject_visit, POS, self.get_utcnow(), self.hiv_test_date)

            self.assertEqual(self.requisition_metadata_obj(
                'bcpp_subject.subjectrequisition',
                REQUIRED, subject_visit.visit_code,
                RESEARCH_BLOOD_DRAW, subject_visit.subject_identifier).count(), 1)

            self.make_requisition(
                subject_visit, RESEARCH_BLOOD_DRAW, self.get_utcnow())

            # add HivCarAdherence,
            self.make_hiv_care_adherence(
                subject_visit, self.get_utcnow(), NO, NO, NO, NO, NO)

            self.assertEqual(self.crf_metadata_obj(
                'bcpp_subject.pimacd4', REQUIRED, subject_visit.visit_code,
                subject_visit.subject_identifier).count(), 1)
            self.assertEqual(self.requisition_metadata_obj(
                REQUIRED, subject_visit.visit_code, VIRAL_LOAD,
                subject_visit.subject_identifier).count(), 1)
            self.assertEqual((
                self.requisition_metadata_obj(KEYED, subject_visit.visit_code,
                                              RESEARCH_BLOOD_DRAW,
                                              subject_visit.subject_identifier).count(), 1))

    def test_hiv_pos_nd_not_on_art_at_bhs(self):
        """HIV Positive not on ART at subject_visit.visit_code, Should offer POC CD4, RBD and VL.
        """
        for subject_visit in [
                self.subject_visit_male_t0, self.subject_visit_male_E0]:
            # Known POS in subject_visit.visit_code
            self.make_hivtesting_history(
                subject_visit, self.get_utcnow(), YES, YES, POS, NO)

            self.make_hivtest_review(
                subject_visit, POS, self.get_utcnow(), self.hiv_test_date)

            # add HivCarAdherence,
            self.make_hiv_care_adherence(
                subject_visit, self.get_utcnow(), NO, NO, NO, NO, NO)

            self.assertEqual(self.crf_metadata_obj(
                'bcpp_subject.pimacd4', REQUIRED,
                subject_visit.visit_code, subject_visit.subject_identifier).count(), 1)

            self.assertEqual(
                self.requisition_metadata_obj(REQUIRED, subject_visit.visit_code,
                                              VIRAL_LOAD,
                                              subject_visit.subject_identifier).count(), 1)
            self.assertEqual(
                self.requisition_metadata_obj(
                    REQUIRED, subject_visit.visit_code,
                    RESEARCH_BLOOD_DRAW, subject_visit.subject_identifier).count(), 1)

    def test_partner_forms_know_pos(self):
        """HIV Positive not on ART at subject_visit.visit_code, Should offer POC CD4, RBD and VL.
        """
        for subject_visit in [
                self.subject_visit_male_t0, self.subject_visit_male_E0]:
            # make
            self.make_hivtesting_history(
                subject_visit, self.get_utcnow(), YES, NO, POS, NO)
            # Known POS in subject_visit.visit_code
            mommy.make_recipe(
                'bcpp_subject.sexualbehaviour',
                subject_visit=subject_visit,
                ever_sex=YES,
                lifetime_sex_partners=1,
                last_year_partners=1
            )

            self.assertEqual(
                self.crf_metadata_obj(
                    'bcpp_subject.recentpartner', REQUIRED,
                    subject_visit.visit_code, subject_visit.subject_identifier).count(), 1)

            self.assertEqual(
                self.crf_metadata_obj(
                    'bcpp_subject.secondpartner', NOT_REQUIRED,
                    subject_visit.visit_code, subject_visit.subject_identifier).count(), 1)

            self.assertEqual(
                self.crf_metadata_obj(
                    'bcpp_subject.thirdpartner', NOT_REQUIRED,
                    subject_visit.visit_code, subject_visit.subject_identifier).count(), 1)
