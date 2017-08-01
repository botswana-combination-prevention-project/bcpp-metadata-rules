# from django.db import models
# from django.db.models.deletion import PROTECT
#
# from edc_appointment.model_mixins.create_appointments_mixin import CreateAppointmentsMixin
# from edc_appointment.models import Appointment
# from edc_base.model_mixins import BaseUuidModel
# from edc_metadata.model_mixins.creates import CreatesMetadataModelMixin
# from edc_metadata.model_mixins.updates import UpdatesCrfMetadataModelMixin
# from edc_metadata.model_mixins.updates import UpdatesRequisitionMetadataModelMixin
# from edc_offstudy.model_mixins import OffstudyModelMixin
# from edc_protocol.tests.utils import get_utcnow
# from edc_visit_schedule.model_mixins import EnrollmentModelMixin, DisenrollmentModelMixin
# from edc_visit_tracking.model_mixins import VisitModelMixin, CrfModelMixin
# from edc_identifier.model_mixins import NonUniqueSubjectIdentifierFieldMixin
#
#
# class HouseholdMember(NonUniqueSubjectIdentifierFieldMixin, BaseUuidModel):
#
#     gender = models.CharField(max_length=25)
#
#
# class SubjectVisit(VisitModelMixin, CreatesMetadataModelMixin, BaseUuidModel):
#
#     appointment = models.OneToOneField(Appointment, on_delete=PROTECT)
#
#     household_member = models.ForeignKey(HouseholdMember)
#
#     reason = models.CharField(max_length=25)
#
#
# class EnrollmentBhs(EnrollmentModelMixin, CreateAppointmentsMixin, BaseUuidModel):
#
#     class Meta(EnrollmentModelMixin.Meta):
#         visit_schedule_name = 'visit_schedule_bhs.bhs_schedule'
#
#
# class DisenrollmentBhs(DisenrollmentModelMixin, BaseUuidModel):
#
#     class Meta(DisenrollmentModelMixin.Meta):
#         visit_schedule_name = 'visit_schedule_bhs.bhs_schedule'
#
#
# class SubjectOffstudy(OffstudyModelMixin, BaseUuidModel):
#
#     class Meta(OffstudyModelMixin.Meta):
#         pass
#
#
# class SubjectRequisition(CrfModelMixin, UpdatesRequisitionMetadataModelMixin, BaseUuidModel):
#
#     subject_visit = models.ForeignKey(SubjectVisit)
#
#     panel_name = models.CharField(max_length=25)
