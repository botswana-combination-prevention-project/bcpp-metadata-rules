from django.test.testcases import TestCase

from edc_constants.constants import YES, NO, MALE
from edc_metadata.constants import REQUIRED, NOT_REQUIRED

from edc_appointment.models import Appointment
from edc_registration.models import RegisteredSubject
from edc_metadata.models import CrfMetadata
from edc_visit_schedule.site_visit_schedules import site_visit_schedules
from edc_visit_tracking.constants import SCHEDULED
from pprint import pprint

from .models import SubjectVisit, EnrollmentBhs, HouseholdMember


class TestMetadataRules(TestCase):

    def setUp(self):
        pprint(site_visit_schedules.registry)
        self.subject_identifier = '1234567'
        RegisteredSubject.objects.create(
            subject_identifier=self.subject_identifier,
            gender=MALE)
        EnrollmentBhs.objects.create(
            subject_identifier=self.subject_identifier)
        visit_code = 'T0'
        household_member = HouseholdMember.objects.create(
            subject_identifier=self.subject_identifier,
            gender=MALE)
        appointment = Appointment.objects.get(
            subject_identifier=self.subject_identifier,
            visit_code=visit_code)
        SubjectVisit.objects.create(
            appointment=appointment,
            household_member=household_member,
            subject_identifier=self.subject_identifier,
            visit_code=visit_code,
            reason=SCHEDULED)

    def test_hiv_car_adherence_and_pima1(self):
        """ HIV Positive took arv in the past but now defaulting,
        Should NOT offer POC CD4.
        """
        for subject_visit in SubjectVisit.objects.all():
            CrfMetadata.objects.get(
                model='bcpp_metadata_rules.hivcareadherence')
            self.assertEqual(
                self.crf_metadata_obj(
                    'bcpp_metadata_rules.hivcareadherence',
                    REQUIRED, subject_visit.visit_code,
                    subject_visit.subject_identifier).count(), 1)
            # suggest this is a defaulter
            HiveCareAdherence.objects.create(
                first_positive=None,
                subject_visit=subject_visit,
                report_datetime=self.get_utcnow(),
                medical_care=NO,
                ever_recommended_arv=NO,
                ever_taken_arv=YES,
                on_arv=NO,
                arv_evidence=NO)

            self.assertEqual(
                self.crf_metadata_obj(
                    'bcpp_metadata_rules.pimacd4',
                    NOT_REQUIRED, subject_visit.visit_code,
                    subject_visit.subject_identifier).count(), 1)
