from model_mommy import mommy

from edc_metadata.models import CrfMetadata, RequisitionMetadata

from ..constants import MICROTUBE

from edc_constants.constants import NO, YES


class RuleGroupMixin:

    def crf_metadata_obj(
            self, model, entry_status, visit_code, subject_identifier):
        return CrfMetadata.objects.filter(
            entry_status=entry_status,
            model=model,
            visit_code=visit_code,
            subject_identifier=subject_identifier)

    def requisition_metadata_obj(
            self, entry_status, visit_code, panel_name, subject_identifier):
        return RequisitionMetadata.objects.filter(
            entry_status=entry_status,
            model='bcpp_subject.subjectrequisition',
            subject_identifier=subject_identifier,
            panel_name=panel_name,
            visit_code=visit_code)

    def make_hivtest_review(
            self, subject_visit, hiv_status,
            report_datetime, hiv_test_date):
        hiv_test_review = mommy.make_recipe(
            'bcpp_subject.hivtestreview',
            report_datetime=report_datetime,
            subject_visit=subject_visit,
            hiv_test_date=hiv_test_date,
            recorded_hiv_result=hiv_status)
        return hiv_test_review

    def make_subject_locator(self, subject_identifier, report_datetime):
        subject_locator = mommy.make_recipe(
            'bcpp_subject.subjectlocator',
            subject_identifier=subject_identifier,
            report_datetime=report_datetime)
        return subject_locator

    def make_residency_mobility(
            self, subject_visit, permanent_resident,
            intend_residency, report_datetime):
        residency_mobility = mommy.make_recipe(
            'bcpp_subject.residencymobility',
            subject_visit=subject_visit,
            report_datetime=report_datetime,
            permanent_resident=permanent_resident,
            intend_residency=permanent_resident)
        return residency_mobility

    def make_requisition(self, subject_visit, panel, report_datetime):
        subject_requisition = mommy.make_recipe(
            'bcpp_subject.subjectrequisition', subject_visit=subject_visit,
            report_datetime=report_datetime, panel_name=panel,
            is_drawn=YES)
        return subject_requisition

    def make_hiv_result(self, status, subject_visit, report_datetime):
        self.make_requisition(subject_visit, MICROTUBE, report_datetime)
        hiv_result = mommy.make_recipe(
            'bcpp_subject.hivresult', subject_visit=subject_visit,
            report_datetime=report_datetime,
            hiv_result=status, insufficient_vol=NO)
        return hiv_result

    def make_hiv_care_adherence(
            self, subject_visit, report_datetime, ever_recommended_arv,
            medical_care, ever_taken_arv, on_arv, arv_evidence):
        hiv_care_adherence = mommy.make_recipe(
            'bcpp_subject.hivcareadherence',
            first_positive=None,
            subject_visit=subject_visit,
            report_datetime=report_datetime,
            medical_care=medical_care,
            ever_recommended_arv=ever_recommended_arv,
            ever_taken_arv=ever_taken_arv,
            on_arv=on_arv,
            arv_evidence=arv_evidence,  # this is the rule field
            first_regimen=NO)
        return hiv_care_adherence

    def make_hivtesting_history(self, subject_visit, report_datetime,
                                has_tested, has_record, verbal_hiv_result,
                                other_record):
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
