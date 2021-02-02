from crm.models import CrmLead, CrmOpportunity, CrmOpportunityMilestoneMap
from django_filters import rest_framework as filters
from django.db.models import Q


class M2MFilter(filters.Filter):

    def filter(self, qs, value):
        if not value:
            return qs
        values = value.split(',')
        qs = qs.filter(**{self.field_name+'__in':values})
        return qs


class AccountStatusM2MFilter(filters.Filter):

    def filter(self, qs, value):
        if not value:
            return qs
        values = value.split(',')
        is_null = '0' in values
        null_qs = qs.filter(**{self.field_name+'__isnull':is_null})
        qs = qs.filter(**{self.field_name+'__in':values}) | null_qs if is_null else qs.filter(**{self.field_name+'__in':values})

        return qs

class BoolFilter(filters.Filter):

    def filter(self, qs, value):
        if not value:
            return qs
        value = value == '1'
        qs = qs.filter(**{self.field_name:value})
        return qs


class IndiaGlobalFilter(filters.Filter):

    def filter(self, qs, value):
        if not value:
            return qs
        if value == '1':
            qs = qs.filter(**{'poc__country__name':'India'})
        elif value == '2':
            qs = qs.filter(~Q(**{'poc__country__name': 'India'}))
        return qs


class CrmLeadFilter(filters.FilterSet):
    status = M2MFilter(field_name='status')
    poc__source = M2MFilter(field_name='poc__source')
    poc__country = M2MFilter(field_name='poc__country')
    territory = M2MFilter(field_name='territory')

    class Meta:
        model = CrmLead
        fields = ('status', 'poc__source', 'poc__country', 'territory')


class CrmOpportunityFilter(filters.FilterSet):
    id = M2MFilter(field_name='id')
    stage = M2MFilter(field_name='stage')
    lead__poc__source = M2MFilter(field_name='lead__poc__source')
    engagement = M2MFilter(field_name='engagement')
    technology = M2MFilter(field_name='technology')

    class Meta:
        model = CrmOpportunity
        fields = ('id', 'stage', 'lead__poc__source', 'engagement', 'technology', )


class CrmCloseWonFilter(filters.FilterSet):
    lead__poc__source = M2MFilter(field_name='lead__poc__source')
    country = M2MFilter(field_name='country')
    territory = M2MFilter(field_name='territory')
    business_analyst = M2MFilter(field_name='business_analyst')
    project_lead = M2MFilter(field_name='project_lead')
    status_updated_by = M2MFilter(field_name='status_updated_by')

    class Meta:
        model = CrmOpportunity
        fields = ('lead__poc__source', 'country', 'territory', 'business_analyst', 'project_lead', 'status_updated_by')


class CrmLossAnalysisFilter(filters.FilterSet):
    lead__poc__source = M2MFilter(field_name='lead__poc__source')
    country = M2MFilter(field_name='country')
    territory = M2MFilter(field_name='territory')
    business_analyst = M2MFilter(field_name='business_analyst')
    project_lead = M2MFilter(field_name='project_lead')
    status_updated_by = M2MFilter(field_name='status_updated_by')

    class Meta:
        model = CrmOpportunity
        fields = ('lead__poc__source', 'country', 'territory', 'business_analyst', 'project_lead', 'status_updated_by')


class CrmAccountFilter(filters.FilterSet):
    crm_opp_lead__status = M2MFilter(field_name='crm_opp_lead__status')
    crm_opp_lead__department = M2MFilter(field_name='crm_opp_lead__department')
    crm_opp_lead__color_status = M2MFilter(field_name='crm_opp_lead__color_status')
    crm_opp_lead__business_analyst = M2MFilter(field_name='crm_opp_lead__business_analyst')
    crm_opp_lead__account_manager = M2MFilter(field_name='crm_opp_lead__account_manager')
    id = M2MFilter(field_name='id')

    class Meta:
        model = CrmLead
        fields = ('id', 'crm_opp_lead__status', 'crm_opp_lead__department', 'crm_opp_lead__color_status',
                  'crm_opp_lead__business_analyst', 'crm_opp_lead__account_manager')


class CrmLeadReportFilter(filters.FilterSet):
    poc__source = M2MFilter(field_name='poc__source')
    poc__country = M2MFilter(field_name='poc__country')

    class Meta:
        model = CrmLead
        fields = ('poc__source', 'poc__country')


class CrmInvoiceReportFilter(filters.FilterSet):
    milestone__is_paid = BoolFilter(field_name='milestone__is_paid')

    class Meta:
        model = CrmOpportunityMilestoneMap
        fields = ('milestone__is_paid',)


class CrmProjectReportFilter(filters.FilterSet):
    project_lead = M2MFilter(field_name='project_lead')
    lead = M2MFilter(field_name='lead')
    color_status = M2MFilter(field_name='color_status')

    class Meta:
        model = CrmOpportunity
        fields = ('lead', 'project_lead', 'color_status')

