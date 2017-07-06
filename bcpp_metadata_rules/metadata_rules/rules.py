from edc_constants.constants import NO, YES, POS, NEG, FEMALE, IND, NOT_SURE
from edc_metadata.constants import NOT_REQUIRED, REQUIRED
from edc_metadata.rules import CrfRule, CrfRuleGroup
from edc_metadata.rules import P, PF, register
from edc_metadata.rules import RequisitionRule, RequisitionRuleGroup

from ..labs import microtube_panel, rdb_panel, viral_load_panel, elisa_panel, venous_panel
from .funcs import (
    func_anonymous_member,
    func_hiv_positive,
    func_is_female,
    func_known_hiv_pos,
    func_requires_circumcision,
    func_requires_hic_enrollment,
    func_requires_hivlinkagetocare,
    func_requires_hivuntested,
    func_requires_microtube,
    func_requires_pima_cd4,
    func_requires_rbd,
    func_requires_recent_partner,
    func_requires_second_partner_forms,
    func_requires_third_partner_forms,
    func_requires_todays_hiv_result,
    func_requires_vl,
    func_requires_hivtestreview,
    func_requires_venous)


@register()
class SubjectVisitRuleGroup(CrfRuleGroup):

    circumcision = CrfRule(
        predicate=func_requires_circumcision,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=['circumcision', 'circumcised', 'uncircumcised'])

    gender_menopause = CrfRule(
        predicate=func_is_female,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=['reproductivehealth', 'pregnancy', 'nonpregnancy'])

    known_pos = CrfRule(
        predicate=func_known_hiv_pos,
        consequence=NOT_REQUIRED,
        alternative=REQUIRED,
        target_models=['hivtestreview', 'hivtested', 'hivtestinghistory',
                       'hivresultdocumentation', 'hivresult', 'hivuntested'])

    pima_cd4 = CrfRule(
        predicate=func_requires_pima_cd4,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=['pimacd4'])

    anonymous_forms = CrfRule(
        predicate=func_anonymous_member,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=['immigrationstatus', 'accesstocare'])

    require_hivlinkagetocare = CrfRule(
        predicate=func_requires_hivlinkagetocare,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=['hivlinkagetocare'])

    class Meta:
        app_label = 'bcpp_subject'


class VisitRequisitionRuleGroup(RequisitionRuleGroup):
    require_microtube = RequisitionRule(
        predicate=func_requires_microtube,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_panels=[microtube_panel])

    vl_for_pos = RequisitionRule(
        predicate=func_requires_vl,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_panels=[viral_load_panel], )

    rbd = RequisitionRule(
        predicate=func_requires_rbd,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_panels=[rdb_panel], )

    class Meta:
        app_label = 'bcpp_subject'
        requisition_model = 'bcpp_subject.subjectrequisition'


@register()
class ResourceUtilizationRuleGroup(CrfRuleGroup):

    out_patient = CrfRule(
        predicate=P('out_patient', 'eq', YES),
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=['bcpp_subject.outpatientcare'])

    hospitalized = CrfRule(
        predicate=P('hospitalized', 'eq', 0),
        consequence=NOT_REQUIRED,
        alternative=REQUIRED,
        target_models=['bcpp_subject.hospitaladmission'])

    class Meta:
        app_label = 'bcpp_subject'
        source_model = 'bcpp_subject.resourceutilization'


@register()
class HivTestingHistoryRuleGroup(CrfRuleGroup):

    has_record = CrfRule(
        predicate=func_requires_hivtestreview,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=['hivtestreview'])

    has_tested = CrfRule(
        predicate=P('has_tested', 'eq', YES),
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=['hivtested'])

    hiv_untested = CrfRule(
        predicate=func_requires_hivuntested,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=['hivuntested'])

    other_record = CrfRule(
        predicate=PF(
            'has_tested', 'other_record',
            func=lambda x, y: True if x == YES and y == YES else False),
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=['hivresultdocumentation'])

    require_todays_hiv_result = CrfRule(
        predicate=func_requires_todays_hiv_result,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=['hivresult'])

    verbal_hiv_result_hiv_care_baseline = CrfRule(
        predicate=P('verbal_hiv_result', 'eq', POS),
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=['hivcareadherence', 'positiveparticipant',
                       'hivmedicalcare', 'hivhealthcarecosts'])

    verbal_response = CrfRule(
        predicate=P('verbal_hiv_result', 'eq', NEG),
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=['stigma', 'stigmaopinion'])

    def method_result(self):
        return True

    class Meta:
        app_label = 'bcpp_subject'
        source_model = 'bcpp_subject.hivtestinghistory'


@register()
class ReviewPositiveRuleGroup(CrfRuleGroup):

    recorded_hiv_result = CrfRule(
        predicate=func_requires_todays_hiv_result,
        consequence=NOT_REQUIRED,
        alternative=REQUIRED,
        target_models=['hivcareadherence', 'hivmedicalcare', 'positiveparticipant'])

    recorded_hivresult = CrfRule(
        predicate=P('recorded_hiv_result', 'eq', NEG),
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=['stigma', 'stigmaopinion'])

    require_todays_hiv_result = CrfRule(
        predicate=func_requires_todays_hiv_result,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=['hivresult'])

    class Meta:
        app_label = 'bcpp_subject'
        source_model = 'bcpp_subject.hivtestreview'


@register()
class HivCareAdherenceRuleGroup(CrfRuleGroup):

    medical_care = CrfRule(
        predicate=P('medical_care', 'eq', YES),
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=['hivmedicalcare'])

    pima_cd4 = CrfRule(
        predicate=func_requires_pima_cd4,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=['pimacd4'])

    require_todays_hiv_result = CrfRule(
        predicate=func_requires_todays_hiv_result,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=['hivresult'])

    class Meta:
        app_label = 'bcpp_subject'
        source_model = 'bcpp_subject.hivcareadherence'


@register()
class SexualBehaviourRuleGroup(CrfRuleGroup):

    partners = CrfRule(
        predicate=func_requires_recent_partner,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=['recentpartner'])

    last_year_partners = CrfRule(
        predicate=func_requires_second_partner_forms,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=['secondpartner'])

    more_partners = CrfRule(
        predicate=func_requires_third_partner_forms,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=['thirdpartner'])

    ever_sex = CrfRule(
        predicate=PF(
            'ever_sex', 'gender',
            func=lambda x, y: True if x == YES and y == FEMALE else False),
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=['reproductivehealth', 'pregnancy', 'nonpregnancy'])

    class Meta:
        app_label = 'bcpp_subject'
        source_model = 'bcpp_subject.sexualbehaviour'


@register()
class CircumcisionRuleGroup(CrfRuleGroup):

    circumcised = CrfRule(
        predicate=P('circumcised', 'eq', YES),
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=['circumcised'])

    uncircumcised = CrfRule(
        predicate=P('circumcised', 'eq', NO),
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=['bcpp_subject.uncircumcised'])

    class Meta:
        app_label = 'bcpp_subject'
        source_model = 'bcpp_subject.circumcision'


@register()
class ReproductiveRuleGroup(CrfRuleGroup):

    currently_pregnant = CrfRule(
        predicate=PF(
            'currently_pregnant', 'menopause',
            func=lambda x, y: True if x == YES or x == NOT_SURE and y == NO else False),
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=['bcpp_subject.pregnancy'])

    non_pregnant = CrfRule(
        predicate=PF(
            'currently_pregnant', 'menopause',
            func=lambda x, y: True if x == NO and y == NO else False),
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=['bcpp_subject.nonpregnancy'])

    class Meta:
        app_label = 'bcpp_subject'
        source_model = 'bcpp_subject.reproductivehealth'


@register()
class MedicalDiagnosesRuleGroup(CrfRuleGroup):
    """Allows the heartattack, cancer, tb forms to be made available
    whether or not the participant has a record. see redmine 314.
    """
    heart_attack_record = CrfRule(
        predicate=P('heart_attack_record', 'eq', YES),
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=['heartattack'])

    cancer_record = CrfRule(
        predicate=P('cancer_record', 'eq', YES),
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=['cancer'])

    tb_record_tuberculosis = CrfRule(
        predicate=P('tb_record', 'eq', YES),
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=['tuberculosis'])

    class Meta:
        app_label = 'bcpp_subject'
        source_model = 'bcpp_subject.medicaldiagnoses'


class BaseCrfRuleGroup(CrfRuleGroup):

    pima_cd4 = CrfRule(
        predicate=func_requires_pima_cd4,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=['pimacd4'])

    hic_enrollment = CrfRule(
        predicate=func_requires_hic_enrollment,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=['hicenrollment'])

    class Meta:
        abstract = True


class BaseRequisitionRuleGroup(RequisitionRuleGroup):
    """Ensures an RBD requisition if HIV result is POS.
    """
    rbd = RequisitionRule(
        predicate=func_requires_rbd,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_panels=[rdb_panel], )

    vl_for_pos = RequisitionRule(
        predicate=func_requires_vl,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_panels=[viral_load_panel], )

    microtube = RequisitionRule(
        predicate=func_requires_microtube,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_panels=[microtube_panel], )

    class Meta:
        abstract = True


@register()
class CrfRuleGroup1(BaseCrfRuleGroup):

    serve_sti_form = CrfRule(
        predicate=func_hiv_positive,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=['bcpp_subject.hivrelatedillness'])

    elisa_result = CrfRule(
        predicate=P('hiv_result', 'eq', IND),
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=['bcpp_subject.elisahivresult'])

    class Meta:
        app_label = 'bcpp_subject'
        source_model = 'bcpp_subject.hivresult'


@register()
class RequisitionRuleGroup1(BaseRequisitionRuleGroup):

    """Ensures an ELISA blood draw requisition if HIV result is IND.
    """
    elisa_for_ind = RequisitionRule(
        predicate=P('hiv_result', 'eq', IND),
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_panels=[elisa_panel])

    class Meta:
        app_label = 'bcpp_subject'
        source_model = 'bcpp_subject.hivresult'
        requisition_model = 'bcpp_subject.subjectrequisition'


@register()
class CrfRuleGroup2(BaseCrfRuleGroup):

    serve_hiv_care_adherence = CrfRule(
        predicate=P('verbal_hiv_result', 'eq', POS),
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=['hivcareadherence', 'hivmedicalcare'])

    class Meta:
        app_label = 'bcpp_subject'
        source_model = 'bcpp_subject.hivtestinghistory'


@register()
class RequisitionRuleGroup2(BaseRequisitionRuleGroup):

    class Meta:
        app_label = 'bcpp_subject'
        source_model = 'bcpp_subject.hivtestinghistory'
        requisition_model = 'bcpp_subject.subjectrequisition'


@register()
class CrfRuleGroup3(BaseCrfRuleGroup):

    class Meta:
        app_label = 'bcpp_subject'
        source_model = 'bcpp_subject.hivtestreview'


@register()
class RequisitionRuleGroup3(BaseRequisitionRuleGroup):

    class Meta:
        app_label = 'bcpp_subject'
        source_model = 'bcpp_subject.hivtestreview'
        requisition_model = 'bcpp_subject.subjectrequisition'


@register()
class CrfRuleGroup4(BaseCrfRuleGroup):

    class Meta:
        app_label = 'bcpp_subject'
        source_model = 'bcpp_subject.hivresultdocumentation'


@register()
class RequisitionRuleGroup4(BaseRequisitionRuleGroup):

    class Meta:
        app_label = 'bcpp_subject'
        source_model = 'bcpp_subject.hivresultdocumentation'
        requisition_model = 'bcpp_subject.subjectrequisition'


@register()
class CrfRuleGroup5(BaseCrfRuleGroup):

    class Meta:
        app_label = 'bcpp_subject'
        source_model = 'bcpp_subject.elisahivresult'


@register()
class RequisitionRuleGroup5(BaseRequisitionRuleGroup):

    class Meta:
        app_label = 'bcpp_subject'
        source_model = 'bcpp_subject.elisahivresult'
        requisition_model = 'bcpp_subject.subjectrequisition'


@register()
class CrfRuleGroup6(BaseCrfRuleGroup):

    class Meta:
        app_label = 'bcpp_subject'
        source_model = 'bcpp_subject.subjectrequisition'


@register()
class RequisitionRuleGroup6(BaseRequisitionRuleGroup):

    venous_for_vol = RequisitionRule(
        predicate=func_requires_venous,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_panels=[venous_panel], )

    class Meta:
        app_label = 'bcpp_subject'
        source_model = 'bcpp_subject.subjectrequisition'
        requisition_model = 'bcpp_subject.subjectrequisition'
