from bcpp_labs.labs import microtube_panel, rdb_panel, viral_load_panel, elisa_panel, venous_panel
from edc_constants.constants import NO, YES, POS, NEG, FEMALE, IND, NOT_SURE
from edc_metadata import NOT_REQUIRED, REQUIRED
from edc_metadata_rules import CrfRuleGroup, CrfRule, RequisitionRuleGroup
from edc_metadata_rules import register, RequisitionRule, P, PF

from .predicates import Predicates


pc = Predicates()

app_label = 'bcpp_subject'


@register()
class SubjectVisitRuleGroup(CrfRuleGroup):

    circumcision = CrfRule(
        predicate=pc.func_requires_circumcision,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.circumcision',
                       f'{app_label}.circumcised',
                       f'{app_label}.uncircumcised'])

    gender_menopause = CrfRule(
        predicate=pc.func_is_female,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.reproductivehealth',
                       f'{app_label}.pregnancy',
                       f'{app_label}.nonpregnancy'])

    known_pos = CrfRule(
        predicate=pc.func_known_hiv_pos,
        consequence=NOT_REQUIRED,
        alternative=REQUIRED,
        target_models=[f'{app_label}.hivtestreview',
                       f'{app_label}.hivtested',
                       f'{app_label}.hivtestinghistory',
                       f'{app_label}.hivresultdocumentation',
                       f'{app_label}.hivresult',
                       f'{app_label}.hivuntested'])

    pima_cd4 = CrfRule(
        predicate=pc.func_requires_pima_cd4,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.pimacd4'])

    anonymous_forms = CrfRule(
        predicate=pc.func_anonymous_member,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.immigrationstatus',
                       f'{app_label}.accesstocare'])

    require_hivlinkagetocare = CrfRule(
        predicate=pc.func_requires_hivlinkagetocare,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.hivlinkagetocare'])

    class Meta:
        app_label = app_label


class VisitRequisitionRuleGroup(RequisitionRuleGroup):
    require_microtube = RequisitionRule(
        predicate=pc.func_requires_microtube,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_panels=[microtube_panel])

    vl_for_pos = RequisitionRule(
        predicate=pc.func_requires_vl,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_panels=[viral_load_panel], )

    rbd = RequisitionRule(
        predicate=pc.func_requires_rbd,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_panels=[rdb_panel], )

    class Meta:
        app_label = app_label
        requisition_model = f'{app_label}.subjectrequisition'


@register()
class ResourceUtilizationRuleGroup(CrfRuleGroup):

    out_patient = CrfRule(
        predicate=P('out_patient', 'eq', YES),
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.outpatientcare'])

    hospitalized = CrfRule(
        predicate=P('hospitalized', 'eq', 0),
        consequence=NOT_REQUIRED,
        alternative=REQUIRED,
        target_models=[f'{app_label}.hospitaladmission'])

    class Meta:
        app_label = app_label
        source_model = f'{app_label}.resourceutilization'


@register()
class HivTestingHistoryRuleGroup(CrfRuleGroup):

    has_record = CrfRule(
        predicate=pc.func_requires_hivtestreview,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.hivtestreview'])

    has_tested = CrfRule(
        predicate=P('has_tested', 'eq', YES),
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.hivtested'])

    hiv_untested = CrfRule(
        predicate=pc.func_requires_hivuntested,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.hivuntested'])

    other_record = CrfRule(
        predicate=PF(
            'has_tested', 'other_record',
            func=lambda x, y: True if x == YES and y == YES else False),
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.hivresultdocumentation'])

    require_todays_hiv_result = CrfRule(
        predicate=pc.func_requires_todays_hiv_result,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.hivresult'])

    verbal_hiv_result_hiv_care_baseline = CrfRule(
        predicate=P('verbal_hiv_result', 'eq', POS),
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.hivcareadherence',
                       f'{app_label}.positiveparticipant',
                       f'{app_label}.hivmedicalcare',
                       f'{app_label}.hivhealthcarecosts'])

    verbal_response = CrfRule(
        predicate=P('verbal_hiv_result', 'eq', NEG),
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.stigma',
                       f'{app_label}.stigmaopinion'])

    def method_result(self):
        return True

    class Meta:
        app_label = app_label
        source_model = f'{app_label}.hivtestinghistory'


@register()
class ReviewPositiveRuleGroup(CrfRuleGroup):

    recorded_hiv_result = CrfRule(
        predicate=pc.func_requires_todays_hiv_result,
        consequence=NOT_REQUIRED,
        alternative=REQUIRED,
        target_models=[f'{app_label}.hivcareadherence',
                       f'{app_label}.hivmedicalcare',
                       f'{app_label}.positiveparticipant'])

    recorded_hivresult = CrfRule(
        predicate=P('recorded_hiv_result', 'eq', NEG),
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.stigma', f'{app_label}.stigmaopinion'])

    require_todays_hiv_result = CrfRule(
        predicate=pc.func_requires_todays_hiv_result,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.hivresult'])

    class Meta:
        app_label = app_label
        source_model = f'{app_label}.hivtestreview'


@register()
class HivCareAdherenceRuleGroup(CrfRuleGroup):

    medical_care = CrfRule(
        predicate=P('medical_care', 'eq', YES),
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.hivmedicalcare'])

    pima_cd4 = CrfRule(
        predicate=pc.func_requires_pima_cd4,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.pimacd4'])

    require_todays_hiv_result = CrfRule(
        predicate=pc.func_requires_todays_hiv_result,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.hivresult'])

    class Meta:
        app_label = app_label
        source_model = f'{app_label}.hivcareadherence'


@register()
class SexualBehaviourRuleGroup(CrfRuleGroup):

    partners = CrfRule(
        predicate=pc.func_requires_recent_partner,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.recentpartner'])

    last_year_partners = CrfRule(
        predicate=pc.func_requires_second_partner_forms,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.secondpartner'])

    more_partners = CrfRule(
        predicate=pc.func_requires_third_partner_forms,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.thirdpartner'])

    ever_sex = CrfRule(
        predicate=PF(
            'ever_sex', 'gender',
            func=lambda x, y: True if x == YES and y == FEMALE else False),
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.reproductivehealth',
                       f'{app_label}.pregnancy',
                       f'{app_label}.nonpregnancy'])

    class Meta:
        app_label = app_label
        source_model = f'{app_label}.sexualbehaviour'


@register()
class CircumcisionRuleGroup(CrfRuleGroup):

    circumcised = CrfRule(
        predicate=P('circumcised', 'eq', YES),
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.circumcised'])

    uncircumcised = CrfRule(
        predicate=P('circumcised', 'eq', NO),
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.uncircumcised'])

    class Meta:
        app_label = app_label
        source_model = f'{app_label}.circumcision'


@register()
class ReproductiveRuleGroup(CrfRuleGroup):

    currently_pregnant = CrfRule(
        predicate=PF(
            'currently_pregnant', 'menopause',
            func=lambda x, y: True if x == YES or x == NOT_SURE and y == NO else False),
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.pregnancy'])

    non_pregnant = CrfRule(
        predicate=PF(
            'currently_pregnant', 'menopause',
            func=lambda x, y: True if x == NO and y == NO else False),
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.nonpregnancy'])

    class Meta:
        app_label = app_label
        source_model = f'{app_label}.reproductivehealth'


@register()
class MedicalDiagnosesRuleGroup(CrfRuleGroup):
    """Allows the heartattack, cancer, tb forms to be made available
    whether or not the participant has a record. see redmine 314.
    """
    heart_attack_record = CrfRule(
        predicate=P('heart_attack_record', 'eq', YES),
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.heartattack'])

    cancer_record = CrfRule(
        predicate=P('cancer_record', 'eq', YES),
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.cancer'])

    tb_record_tuberculosis = CrfRule(
        predicate=P('tb_record', 'eq', YES),
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.tuberculosis'])

    class Meta:
        app_label = app_label
        source_model = f'{app_label}.medicaldiagnoses'


class BaseCrfRuleGroup(CrfRuleGroup):

    pima_cd4 = CrfRule(
        predicate=pc.func_requires_pima_cd4,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.pimacd4'])

    hic_enrollment = CrfRule(
        predicate=pc.func_requires_hic_enrollment,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.hicenrollment'])

    class Meta:
        abstract = True


class BaseRequisitionRuleGroup(RequisitionRuleGroup):
    """Ensures an RBD requisition if HIV result is POS.
    """
    rbd = RequisitionRule(
        predicate=pc.func_requires_rbd,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_panels=[rdb_panel], )

    vl_for_pos = RequisitionRule(
        predicate=pc.func_requires_vl,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_panels=[viral_load_panel], )

    microtube = RequisitionRule(
        predicate=pc.func_requires_microtube,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_panels=[microtube_panel], )

    venous = RequisitionRule(
        predicate=pc.func_requires_venous,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_panels=[venous_panel], )

    class Meta:
        abstract = True


@register()
class CrfRuleGroup1(BaseCrfRuleGroup):

    serve_sti_form = CrfRule(
        predicate=pc.func_hiv_positive,
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.hivrelatedillness'])

    elisa_result = CrfRule(
        predicate=P('hiv_result', 'eq', IND),
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.elisahivresult'])

    class Meta:
        app_label = app_label
        source_model = f'{app_label}.hivresult'


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
        app_label = app_label
        source_model = f'{app_label}.hivresult'
        requisition_model = f'{app_label}.subjectrequisition'


@register()
class CrfRuleGroup2(BaseCrfRuleGroup):

    serve_hiv_care_adherence = CrfRule(
        predicate=P('verbal_hiv_result', 'eq', POS),
        consequence=REQUIRED,
        alternative=NOT_REQUIRED,
        target_models=[f'{app_label}.hivcareadherence',
                       f'{app_label}.hivmedicalcare'])

    class Meta:
        app_label = app_label
        source_model = f'{app_label}.hivtestinghistory'


@register()
class RequisitionRuleGroup2(BaseRequisitionRuleGroup):

    class Meta:
        app_label = app_label
        source_model = f'{app_label}.hivtestinghistory'
        requisition_model = f'{app_label}.subjectrequisition'


@register()
class CrfRuleGroup3(BaseCrfRuleGroup):

    class Meta:
        app_label = app_label
        source_model = f'{app_label}.hivtestreview'


@register()
class RequisitionRuleGroup3(BaseRequisitionRuleGroup):

    class Meta:
        app_label = app_label
        source_model = f'{app_label}.hivtestreview'
        requisition_model = f'{app_label}.subjectrequisition'


@register()
class CrfRuleGroup4(BaseCrfRuleGroup):

    class Meta:
        app_label = app_label
        source_model = f'{app_label}.hivresultdocumentation'


@register()
class RequisitionRuleGroup4(BaseRequisitionRuleGroup):

    class Meta:
        app_label = app_label
        source_model = f'{app_label}.hivresultdocumentation'
        requisition_model = f'{app_label}.subjectrequisition'


@register()
class CrfRuleGroup5(BaseCrfRuleGroup):

    class Meta:
        app_label = app_label
        source_model = f'{app_label}.elisahivresult'


@register()
class RequisitionRuleGroup5(BaseRequisitionRuleGroup):

    class Meta:
        app_label = app_label
        source_model = f'{app_label}.elisahivresult'
        requisition_model = f'{app_label}.subjectrequisition'


@register()
class CrfRuleGroup6(BaseCrfRuleGroup):

    class Meta:
        source_model = f'{app_label}.subjectrequisition'
