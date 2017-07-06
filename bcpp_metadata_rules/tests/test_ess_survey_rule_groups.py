from model_mommy import mommy
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.test.utils import tag

from edc_constants.constants import NO, YES, POS, NEG, UNK, DWTA, NOT_APPLICABLE, IND
from edc_metadata.constants import REQUIRED, NOT_REQUIRED
from edc_metadata.models import RequisitionMetadata, CrfMetadata
from member.models.household_member import HouseholdMember

from ..constants import E0, MICROTUBE, ELISA, CAPILLARY
from .rule_group_mixins import RuleGroupMixin
from .test_mixins import SubjectMixin


@tag('ESSRULE')
class TestEssSurveyRuleGroups(SubjectMixin, RuleGroupMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.consent_data_female = {
            'identity': '31722515',
            'confirm_identity': '31722515',
        }
        self.consent_data_male = {
            'identity': '31721515',
            'confirm_identity': '31721515',
        }
        survey_schedule = self.get_survey_schedule(index=2)
        self.subject_visit_male = self.make_subject_visit_for_consented_subject_male(
            E0, survey_schedule=survey_schedule, **self.consent_data_male)
        self.subject_visit_female = self.make_subject_visit_for_consented_subject_female(
            E0, survey_schedule=survey_schedule, **self.consent_data_female)
        self.household_member = HouseholdMember.objects.filter(
            subject_identifier=self.subject_visit_male.subject_identifier)
        self.subject_identifier = self.subject_visit_male.subject_identifier
        self.hiv_test_date = timezone.now() - timedelta(days=50)

    def test_partner_forms_know_pos(self):
        """HIV Positive not on ART at T0, Should offer POC CD4, RBD and VL.
        """
        mommy.make_recipe(
            'bcpp_subject.hivtestinghistory',
            subject_visit=self.subject_visit_male,
            report_datetime=self.get_utcnow(),
            has_tested=YES,
            when_hiv_test='1 to 5 months ago',
            has_record=NO,
            verbal_hiv_result=POS,
            other_record=NO)

        # Known POS in T0
        mommy.make_recipe(
            'bcpp_subject.sexualbehaviour',
            subject_visit=self.subject_visit_male,
            ever_sex=YES,
            lifetime_sex_partners=1,
            last_year_partners=1
        )

        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.recentpartner',
                REQUIRED, E0, self.subject_identifier).count(), 1)

        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.secondpartner',
                NOT_REQUIRED, E0, self.subject_identifier).count(), 1)

        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.thirdpartner',
                NOT_REQUIRED, E0, self.subject_identifier).count(), 1)

    def test_partner_forms_know_pos_1(self):
        """HIV Positive not on ART at T0, Should offer POC CD4, RBD and VL.
        """
        self.subject_identifier = self.subject_visit_male.subject_identifier
        # make
        self.make_hivtesting_history(
            self.subject_visit_male, self.get_utcnow(), YES, NO, POS, NO)
        # Known POS in T0
        mommy.make_recipe(
            'bcpp_subject.sexualbehaviour',
            subject_visit=self.subject_visit_male,
            ever_sex=YES,
            lifetime_sex_partners=2,
            last_year_partners=2
        )

        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.recentpartner',
                REQUIRED, E0, self.subject_identifier).count(), 1)

        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.secondpartner',
                REQUIRED, E0, self.subject_identifier).count(), 1)

        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.thirdpartner',
                NOT_REQUIRED, E0, self.subject_identifier).count(), 1)

    def test_partner_forms_know_pos_2(self):
        """HIV Positive not on ART at T0, Should offer POC CD4, RBD and VL.
        """
        self.subject_identifier = self.subject_visit_male.subject_identifier
        # make
        self.make_hivtesting_history(
            self.subject_visit_male, self.get_utcnow(), YES, NO, POS, NO)
        # Known POS in T0
        mommy.make_recipe(
            'bcpp_subject.sexualbehaviour',
            subject_visit=self.subject_visit_male,
            ever_sex=YES,
            lifetime_sex_partners=3,
            last_year_partners=3
        )

        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.recentpartner',
                REQUIRED, E0, self.subject_identifier).count(), 1)

        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.secondpartner',
                REQUIRED, E0, self.subject_identifier).count(), 1)

        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.thirdpartner',
                REQUIRED, E0, self.subject_identifier).count(), 1)

    @tag("hivcareadherence")
    def test_hiv_care_adherence_not_required(self):

        self.subject_identifier = self.subject_visit_male.subject_identifier
        self.make_hivtesting_history(
            self.subject_visit_male, self.get_utcnow(), YES, YES, NEG, NO)

        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.hivcareadherence',
                NOT_REQUIRED, E0, self.subject_identifier).count(), 1)

        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.hivmedicalcare',
                NOT_REQUIRED, E0, self.subject_identifier).count(), 1)

    @tag("hivcareadherence")
    def test_hiv_care_adherence_required(self):
        """ HIV Positive took arv in the past but now defaulting.

        Should NOT offer POC CD4.

        Models:
            * HivCareAdherence
            * HivResult
        """
        self.subject_identifier = self.subject_visit_male.subject_identifier

        self.make_hivtesting_history(
            self.subject_visit_male, self.get_utcnow(), YES, YES, POS, NO)

        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.hivcareadherence',
                REQUIRED, E0, self.subject_identifier).count(), 1)

        self.assertEqual(
            self.requisition_metadata_obj(REQUIRED, self.subject_visit_male.visit_code,
                                          MICROTUBE,
                                          self.subject_visit_male.subject_identifier).count(), 1)

        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.hivmedicalcare',
                REQUIRED, E0, self.subject_identifier).count(), 1)

    @tag("hivcareadherence")
    def test_hiv_care_adherence_has_record_DWTA(self):

        self.subject_identifier = self.subject_visit_male.subject_identifier
        self.make_hivtesting_history(
            self.subject_visit_male, self.get_utcnow(), DWTA, DWTA, DWTA, NO)

        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.hivcareadherence',
                NOT_REQUIRED, E0, self.subject_identifier).count(), 1)

        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.hivmedicalcare',
                NOT_REQUIRED, E0, self.subject_identifier).count(), 1)

    @tag("hivcareadherence")
    def test_hiv_care_adherence_required3(self):
        self.subject_identifier = self.subject_visit_male.subject_identifier

        self.make_hivtesting_history(
            self.subject_visit_male, self.get_utcnow(), YES, YES, UNK, NO)

        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.hivcareadherence',
                NOT_REQUIRED, E0, self.subject_identifier).count(), 1)

        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.hivmedicalcare',
                NOT_REQUIRED, E0, self.subject_identifier).count(), 1)

    def test_hiv_care_adherence_required1(self):

        self.subject_identifier = self.subject_visit_male.subject_identifier

        report_datetime = (
            self.subject_visit_male.report_datetime + timedelta(hours=1))

        self.make_hiv_care_adherence(
            self.subject_visit_male, report_datetime, NO, NO, NO, NO, NO)

        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.arvhistory', REQUIRED, E0,
                self.subject_identifier).count(), 1)

    def test_hiv_care_adherence_required2(self):

        self.subject_identifier = self.subject_visit_male.subject_identifier

        report_datetime = (
            self.subject_visit_male.report_datetime + timedelta(hours=1))

        hivcare_adherence = self.make_hiv_care_adherence(
            self.subject_visit_male, report_datetime, NO, NO, NO, NO, NO)
        hivcare_adherence.first_regimen = YES
        hivcare_adherence.save()

        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.arvhistory', NOT_REQUIRED, E0,
                self.subject_identifier).count(), 1)

    @tag('reproductive_rules')
    def test_reproductive_health(self):

        self.subject_identifier = self.subject_visit_male.subject_identifier

        mommy.make_recipe(
            'bcpp_subject.reproductivehealth',
            subject_visit=self.subject_visit_male)

        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.nonpregnancy', REQUIRED, E0,
                self.subject_identifier).count(), 1)

        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.pregnancy', NOT_REQUIRED, E0,
                self.subject_identifier).count(), 1)

    @tag('reproductive_rules')
    def test_reproductive_health1(self):

        self.subject_identifier = self.subject_visit_male.subject_identifier

        reproductivehealth = mommy.make_recipe(
            'bcpp_subject.reproductivehealth', subject_visit=self.subject_visit_male)
        reproductivehealth.currently_pregnant = YES
        reproductivehealth.menopause = NO
        reproductivehealth.save()

        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.pregnancy', REQUIRED, E0,
                self.subject_identifier).count(), 1)

        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.nonpregnancy', NOT_REQUIRED, E0,
                self.subject_identifier).count(), 1)

    @tag('reproductive_rules')
    def test_reproductive_health2(self):

        self.subject_identifier = self.subject_visit_male.subject_identifier

        reproductivehealth = mommy.make_recipe(
            'bcpp_subject.reproductivehealth', subject_visit=self.subject_visit_male)
        reproductivehealth.currently_pregnant = 'Not Sure'
        reproductivehealth.menopause = NO
        reproductivehealth.save()

        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.pregnancy', REQUIRED, E0,
                self.subject_identifier).count(), 1)

        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.nonpregnancy', NOT_REQUIRED, E0,
                self.subject_identifier).count(), 1)

    @tag('reproductive_rules')
    def test_3(self):

        self.subject_identifier = self.subject_visit_male.subject_identifier

        reproductivehealth = mommy.make_recipe(
            'bcpp_subject.reproductivehealth', subject_visit=self.subject_visit_male)
        reproductivehealth.currently_pregnant = 'Not Sure'
        reproductivehealth.menopause = NO
        reproductivehealth.save()

        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.pregnancy', REQUIRED, E0,
                self.subject_identifier).count(), 1)

        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.nonpregnancy', NOT_REQUIRED, E0,
                self.subject_identifier).count(), 1)

    @tag('hivresultdocumentation')
    def test_hivresult_documentation_required(self):

        self.subject_identifier = self.subject_visit_male.subject_identifier

        mommy.make_recipe(
            'bcpp_subject.hivtestinghistory',
            subject_visit=self.subject_visit_male,
            report_datetime=self.get_utcnow(),
            has_tested=YES,
            when_hiv_test='1 to 5 months ago',
            has_record=YES,
            verbal_hiv_result=POS,
            other_record=NO)

        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.hivresultdocumentation', REQUIRED, E0,
                self.subject_identifier).count(), 1)

    @tag('hivresultdocumentation')
    def test_hivresult_documentation_required1(self):

        self.subject_identifier = self.subject_visit_male.subject_identifier

        mommy.make_recipe(
            'bcpp_subject.hivtestinghistory',
            subject_visit=self.subject_visit_male,
            report_datetime=self.get_utcnow(),
            has_tested=YES,
            when_hiv_test='1 to 5 months ago',
            has_record=NO,
            verbal_hiv_result=POS,
            other_record=NO)

        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.hivresultdocumentation',
                REQUIRED, E0, self.subject_identifier).count(), 1)

    @tag('hivresultdocumentation')
    def test_hivresult_documentation_required2(self):

        self.subject_identifier = self.subject_visit_male.subject_identifier

        mommy.make_recipe(
            'bcpp_subject.hivtestinghistory',
            subject_visit=self.subject_visit_male,
            report_datetime=self.get_utcnow(),
            has_tested=YES,
            when_hiv_test='1 to 5 months ago',
            has_record=NO,
            verbal_hiv_result=POS,
            other_record=NO)

        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.hivresultdocumentation',
                NOT_REQUIRED, E0, self.subject_identifier).count(), 1)

    @tag('hivresultdocumentation')
    def test_hivresult_documentation_required5(self):

        self.subject_identifier = self.subject_visit_male.subject_identifier

        mommy.make_recipe(
            'bcpp_subject.hivtestinghistory',
            subject_visit=self.subject_visit_male,
            report_datetime=self.get_utcnow(),
            has_tested=YES,
            when_hiv_test='1 to 5 months ago',
            has_record=NO,
            verbal_hiv_result=NEG,
            other_record=NO)

        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.hivresultdocumentation',
                NOT_REQUIRED, E0, self.subject_identifier).count(), 1)

    @tag('hivresultdocumentation')
    def test_hivresult_documentation_required4(self):

        self.subject_identifier = self.subject_visit_male.subject_identifier

        mommy.make_recipe(
            'bcpp_subject.hivtestinghistory',
            subject_visit=self.subject_visit_male,
            report_datetime=self.get_utcnow(),
            has_tested=YES,
            when_hiv_test='1 to 5 months ago',
            has_record=NO,
            verbal_hiv_result=NEG,
            other_record=NO)

        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.hivresultdocumentation',
                NOT_REQUIRED, E0, self.subject_identifier).count(), 1)

    @tag('hivresultdocumentation')
    def test_hivresult_documentation_required6(self):

        self.subject_identifier = self.subject_visit_male.subject_identifier

        self.make_hivtesting_history(
            self.subject_visit_male, self.get_utcnow(), YES, NO, NEG, NO)

        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.hivresultdocumentation',
                NOT_REQUIRED, E0, self.subject_identifier).count(), 1)

    @tag('immigrationstatus')
    def test_immigration_notrequired_noncitizens(self):

        self.subject_identifier = self.subject_visit_male.subject_identifier

        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.immigrationstatus',
                NOT_REQUIRED, E0, self.subject_identifier).count(), 1)

    @tag('accesstocare')
    def test_access_tocare(self):

        self.subject_identifier = self.subject_visit_male.subject_identifier

        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.accesstocare',
                NOT_REQUIRED, E0, self.subject_identifier).count(), 1)

    @tag('test_requires_microtube_without_documentation')
    def test_requires_microtube_without_documentation(self):

        self.subject_identifier = self.subject_visit_male.subject_identifier

        mommy.make_recipe(
            'bcpp_subject.hivtestinghistory',
            subject_visit=self.subject_visit_male,
            report_datetime=self.get_utcnow(),
            has_tested=YES,
            when_hiv_test='1 to 5 months ago',
            has_record=NO,
            verbal_hiv_result=POS,
            other_record=NO)

        self.assertEqual(
            self.crf_metadata_obj(
                'bcpp_subject.hivresultdocumentation',
                NOT_REQUIRED, E0, self.subject_identifier).count(), 1)

        req = RequisitionMetadata.objects.filter(
            entry_status=REQUIRED,
            model='bcpp_subject.subjectrequisition',
            subject_identifier=self.subject_identifier,
            panel_name=MICROTUBE,
            visit_code=E0)
        self.assertEqual(req.count(), 1)

    @tag('test_requires_microtube_without_documentation')
    def test_requires_microtube_declined_testing(self):

        self.subject_identifier = self.subject_visit_male.subject_identifier

        mommy.make_recipe(
            'bcpp_subject.hivtestinghistory',
            subject_visit=self.subject_visit_male,
            report_datetime=self.get_utcnow(),
            has_tested=NO,
            when_hiv_test='1 to 5 months ago',
            has_record=NO,
            verbal_hiv_result=None,
            other_record=NO)

        req = RequisitionMetadata.objects.filter(
            entry_status=REQUIRED,
            model='bcpp_subject.subjectrequisition',
            subject_identifier=self.subject_identifier,
            panel_name=MICROTUBE,
            visit_code=E0)
        self.assertEqual(req.count(), 1)

    @tag('test_requires_microtube_without_documentation')
    def test_requires_microtube_declined_with_hivtest_neg(self):

        self.subject_identifier = self.subject_visit_male.subject_identifier

        mommy.make_recipe(
            'bcpp_subject.hivtestinghistory',
            subject_visit=self.subject_visit_male,
            report_datetime=self.get_utcnow(),
            has_tested=NO,
            when_hiv_test='1 to 5 months ago',
            has_record=NO,
            verbal_hiv_result=None,
            other_record=NO)

        req = RequisitionMetadata.objects.filter(
            entry_status=REQUIRED,
            model='bcpp_subject.subjectrequisition',
            subject_identifier=self.subject_identifier,
            panel_name=MICROTUBE,
            visit_code=E0)
        self.assertEqual(req.count(), 1)

    @tag('test_requires_elisa_requisition')
    def test_requires_elisa_requisition(self):

        self.subject_identifier = self.subject_visit_male.subject_identifier

        mommy.make_recipe(
            'bcpp_subject.hivtestinghistory',
            subject_visit=self.subject_visit_male,
            report_datetime=self.get_utcnow(),
            has_tested=YES,
            when_hiv_test='1 to 5 months ago',
            has_record=NO,
            verbal_hiv_result=NEG,
            other_record=NOT_APPLICABLE)

        mommy.make_recipe(
            'bcpp_subject.subjectrequisition',
            subject_visit=self.subject_visit_male,
            report_datetime=self.subject_visit_male.report_datetime,
            panel_name=MICROTUBE,
        )
        mommy.make_recipe(
            'bcpp_subject.hivresult',
            subject_visit=self.subject_visit_male,
            report_datetime=self.subject_visit_male.report_datetime,
            hiv_result=IND,
            blood_draw_type=CAPILLARY,
            insufficient_vol=NO
        )

        crf_count = CrfMetadata.objects.filter(
            entry_status=REQUIRED,
            model='bcpp_subject.elisahivresult',
            visit_code=self.subject_visit_male.visit_code,
            subject_identifier=self.subject_visit_male.subject_identifier).count()
        self.assertEqual(crf_count, 1)

        req = RequisitionMetadata.objects.filter(
            entry_status=REQUIRED,
            model='bcpp_subject.subjectrequisition',
            subject_identifier=self.subject_identifier,
            panel_name=ELISA,
            visit_code=E0)

        self.assertEqual(req.count(), 1)
