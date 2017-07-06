from django.apps import apps as django_apps
from edc_constants.constants import POS, NEG, NO, YES, FEMALE, NAIVE, DEFAULTER, ON_ART
from edc_registration.models import RegisteredSubject

from bcpp_community.surveys import BCPP_YEAR_3
from member.models import HouseholdMember

from ..constants import MICROTUBE
from ..models import is_circumcised
from ..subject_helper import SubjectHelper
from django.core.exceptions import ObjectDoesNotExist


class PredicateCollection:

    model_registry = dict(
        hicenrollment='bcpp_subject.hicenrollment',
        hivtestinghistory='bcpp_subject.hivtestinghistory',
        hivresult='bcpp_subject.hivresult',
        subjectrequisition='bcpp_subject.subjectrequisition',
        sexualbehaviour='bcpp_subject.sexualbehaviour',
    )

    def __init_(self, model_registry=None):
        self._model_registry = model_registry or self.model_registry

    def get_model(self, model_name=None):
        return django_apps.get_model(
            **self._model_registry.get(model_name).split(','))

    def is_hic_enrolled(self, visit_instance):
        """Returns True if subject is enrolled to Hic.
        """
        model_cls = self.get_model('hicenrollment')
        try:
            model_cls.objects.get(
                subject_visit__subject_identifier=visit_instance.subject_identifier,
                hic_permission=YES)
            return True
        except ObjectDoesNotExist:
            return False

    def func_is_female(self, visit_instance, *args):
        registered_subject = RegisteredSubject.objects.get(
            subject_identifier=visit_instance.subject_identifier)
        return registered_subject.gender == FEMALE

    def func_requires_recent_partner(self, visit_instance, *args):
        model_cls = self.get_model('sexualbehaviour')
        sexual_behaviour = model_cls.objects.get(
            subject_visit=visit_instance)
        if sexual_behaviour.last_year_partners:
            return True if int(sexual_behaviour.last_year_partners) >= 1 else False
        return False

    def func_requires_second_partner_forms(self, visit_instance, *args):
        model_cls = self.get_model('sexualbehaviour')
        sexual_behaviour = model_cls.objects.get(
            subject_visit=visit_instance)
        if sexual_behaviour.last_year_partners:
            return True if int(sexual_behaviour.last_year_partners) >= 2 else False
        return False

    def func_requires_third_partner_forms(self, visit_instance, *args):
        model_cls = self.get_model('sexualbehaviour')
        sexual_behaviour = model_cls.objects.get(
            subject_visit=visit_instance)
        if sexual_behaviour.last_year_partners:
            return True if int(sexual_behaviour.last_year_partners) >= 3 else False
        return False

    def func_requires_hivlinkagetocare(self, visit_instance, *args):
        """Returns True is a participant is a defaulter now or at baseline,
        is naive now or at baseline.
        """
        subject_helper = SubjectHelper(visit_instance)
        if subject_helper.defaulter_at_baseline:
            return True
        elif subject_helper.naive_at_baseline:
            return True
        return False

    def func_art_defaulter(self, visit_instance, *args):
        """Returns True is a participant is a defaulter.
        """
        subject_helper = SubjectHelper(visit_instance)
        return subject_helper.final_arv_status == DEFAULTER

    def func_art_naive(self, visit_instance, *args):
        """Returns True if the participant art naive.
        """
        subject_helper = SubjectHelper(visit_instance)
        return subject_helper.final_arv_status == NAIVE

    def func_on_art(self, visit_instance, *args):
        """Returns True if the participant is on art.
        """
        return SubjectHelper(visit_instance).final_arv_status == ON_ART

    def func_requires_todays_hiv_result(self, visit_instance, *args):
        subject_helper = SubjectHelper(visit_instance)
        return subject_helper.final_hiv_status != POS

    def func_requires_pima_cd4(self, visit_instance, *args):
        """Returns True if subject is POS and ART naive.

        Note: if naive at baseline, is also required.
        """
        subject_helper = SubjectHelper(visit_instance)
        return (subject_helper.final_hiv_status == POS
                and (subject_helper.final_arv_status == NAIVE
                     or subject_helper.naive_at_baseline))

    def func_known_hiv_pos(self, visit_instance, *args):
        """Returns True if participant is NOT newly diagnosed POS.
        """
        subject_helper = SubjectHelper(visit_instance)
        return subject_helper.known_positive

    def func_requires_hic_enrollment(self, visit_instance, *args):
        """If the participant is tested HIV NEG and was not HIC
        enrolled then HIC is REQUIRED.

        Not required for last survey / bcpp-year-3.
        """
        if visit_instance.survey_schedule_object.name == BCPP_YEAR_3:
            return False
        subject_helper = SubjectHelper(visit_instance)
        return (subject_helper.final_hiv_status == NEG
                and not is_hic_enrolled(visit_instance))

    def func_requires_microtube(self, visit_instance, *args):
        """Returns True to trigger the Microtube requisition if one is
        """
        # TODO: verify this
        model_cls = self.get_model('sexualbehaviour')
        subject_helper = SubjectHelper(visit_instance)
        try:
            hiv_result = model_cls.objects.get(subject_visit=visit_instance)
        except model_cls.DoesNotExist:
            today_hiv_result = None
        else:
            today_hiv_result = hiv_result.hiv_result
        return (
            subject_helper.final_hiv_status != POS
            and not today_hiv_result)

    def func_hiv_positive(self, visit_instance, *args):
        """Returns True if the participant is known or newly
        diagnosed HIV positive.
        """
        return SubjectHelper(visit_instance).final_hiv_status == POS

    def func_requires_circumcision(self, visit_instance, *args):
        """Return True if male is not reported as circumcised.
        """
        if visit_instance.household_member.gender == FEMALE:
            return False
        return not is_circumcised(visit_instance)

    def func_requires_rbd(self, visit_instance, *args):
        """Returns True if subject is POS.
        """
        if SubjectHelper(visit_instance).final_hiv_status == POS:
            return True
        return False

    def func_requires_vl(self, visit_instance, *args):
        """Returns True if subject is POS.
        """
        if SubjectHelper(visit_instance).final_hiv_status == POS:
            return True
        return False

    def func_requires_venous(self, visit_instance, *args):
        model_cls = self.get_model('subjectrequisition')
        try:
            model_cls.objects.get(
                is_drawn=NO,
                panel_name=MICROTUBE,
                subject_visit=visit_instance,
                reason_not_drawn='collection_failed')
        except model_cls.DoesNotExist:
            pass
        else:
            return True
        return False

    def func_requires_hivuntested(self, visit_instance, *args):
        """Only for ESS."""
        model_cls = self.get_model('hivtestinghistory')
        try:
            obj = model_cls.objects.get(
                subject_visit=visit_instance)
        except model_cls.DoesNotExist:
            pass
        else:
            if obj and obj.has_tested == NO:
                return True
        return False

    def func_requires_hivtestreview(self, visit_instance, *args):
        """Only for ESS."""
        model_cls = self.get_model('hivtestinghistory')
        try:
            obj = model_cls.objects.get(
                subject_visit=visit_instance)
        except model_cls.DoesNotExist:
            pass
        else:
            if obj and obj.has_record == YES:
                return True
        return False

    def func_anonymous_member(self, visit_instance, *args):
        model_cls = self.get_model('householdmember')
        try:
            household_member = model_cls.objects.get(
                subject_identifier=visit_instance.subject_identifier)
            return household_member.anonymous
        except model_cls.DoesNotExist:
            return False
        except model_cls.MultipleObjectsReturned:
            return False
