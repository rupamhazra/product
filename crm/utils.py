import os
import pandas as pd
from django.db.models import Q, Sum
from SSIL_SSO_MS import settings
from crm.constant import USER_TYPE
from crm.models import CrmOpportunityMilestoneChangeRequestDistribution, CrmLog, CrmLead, CrmOpportunity, \
    CrmCeleryRevoke
from global_function import getHostWithPort
from master.models import TMasterModuleRoleUser
from datetime import datetime
from SSIL_SSO_MS.celery import app


def soft_update(existed_ids=[],updated_ids=[]):
    deleted_ids = list(set(existed_ids) - set(updated_ids))
    added_ids = list(set(updated_ids) - set(existed_ids))
    return deleted_ids, added_ids


def soft_update_mapping(mapping_model,updated_ids=[],existed_dict={},existed_query_str=''):
    existed_ids = mapping_model.cmobjects.filter(**existed_dict).values_list(existed_query_str+'__id')
    deleted_ids, added_ids = soft_update(existed_ids=existed_ids,updated_ids=updated_ids)
    mapping_model.cmobjects.filter(**existed_dict, **{existed_query_str+'__in':deleted_ids}).update(
        is_deleted=True)
    for added_id in added_ids:
        mapping_model.objects.create(**existed_dict, **{existed_query_str+'_id':added_id})


def hard_update_mapping(mapping_model,updated_ids=[],existed_dict={},existed_query_str=''):
    existed_ids = mapping_model.cmobjects.filter(**existed_dict).values_list(existed_query_str+'__id')
    deleted_ids, added_ids = soft_update(existed_ids=existed_ids,updated_ids=updated_ids)
    mapping_model.cmobjects.filter(**existed_dict, **{existed_query_str+'__in':deleted_ids}).delete()
    for added_id in added_ids:
        mapping_model.objects.create(**existed_dict, **{existed_query_str+'_id':added_id})


def response_on_off_modified(response):
    data_dict = {}
    if 'results' in response.data:
        data_dict = response.data
    else:
        data_dict['results'] = response.data

    if response.data:
        data_dict['request_status'] = 1
        data_dict['msg'] = settings.MSG_SUCCESS
    elif len(response.data) == 0:
        data_dict['request_status'] = 1
        data_dict['msg'] = settings.MSG_NO_DATA
    else:
        data_dict['request_status'] = 0
        data_dict['msg'] = settings.MSG_ERROR

    return data_dict


def create_file_path(base_path='', file_name=''):
    if os.path.isdir(base_path):
        file_path_name = '{}/{}'.format(base_path, file_name)
    else:
        os.makedirs(base_path)
        file_path_name = '{}/{}'.format(base_path, file_name)
    return file_path_name


def download_url_generator(request, data=[],base_path='',extension_type='xlsx',file_name='',columns=[],headers=[]):
    df = pd.DataFrame.from_records(data)[columns]
    file_path_name = create_file_path(base_path=base_path, file_name=file_name)
    file_path = settings.MEDIA_ROOT_EXPORT + file_path_name
    if extension_type == 'xlsx':
        df.to_excel(file_path, index=None, header=headers)
    elif extension_type == 'csv':
        df.to_csv(file_path, index=None, header=headers)
    else:
        df.to_excel(file_path, index=None, header=headers)
    url = getHostWithPort(request) + file_path_name if file_path_name else None
    return url


def get_opportunity_probability(stage=1):
    """
    STAGE_CHOICE = (
        (1, 'Requirement Shared'),
        (2, 'Presales'),
        (3, 'Proposal'),
        (4, 'Negotiation'),
        (5, 'Verbal Commitment'),
        (6, 'Agreement')
    )
    :param stage:
    :return probability:
    """
    probability = {
        1:25,
        2:35,
        3:60,
        4:50,
        5:80,
        6:90
    }
    return probability.get(stage)


def get_user_type(user=None):
    user_role = TMasterModuleRoleUser.objects.filter(mmr_user=user, mmr_type=3, mmr_module__cm_url='sft-crm',
                                                     mmr_is_deleted=False).first()
    user_type = USER_TYPE.get(user_role.mmr_role.cr_name) if user_role else None
    return user_type


def get_query_by_user_type(login_user=None, assigned_users=[], table_type=''):
    user_type = get_user_type(user=login_user)
    query_by_user_type = Q()
    if user_type == 1:
        if table_type == 'opportunity':
            query_by_user_type = Q(Q(lead__assign_to__isnull=True) & Q(lead__created_by__in=assigned_users)) | \
                                Q(Q(lead__assign_to__isnull=False) & Q(lead__assign_to__in=assigned_users) &
                                Q(lead__assign_from=login_user))
            # query_by_user_type = Q(lead__created_by__in=assigned_users)|Q(Q(lead__assign_to__in=assigned_users)&
            #                     Q(lead__assign_from=login_user))
            # query_by_user_type = Q(lead__assign_to__in=assigned_users)&Q(lead__assign_from=login_user)

        elif table_type == 'lead':
            query_by_user_type = Q(Q(assign_to__isnull=True)&Q(created_by__in=assigned_users))|\
                                Q(Q(assign_to__isnull=False)&Q(assign_to__in=assigned_users) &
                                Q(assign_from=login_user))
            # query_by_user_type = Q(assign_to__in=assigned_users)&Q(assign_from=login_user)

    elif user_type == 2:
        if table_type == 'opportunity':
            query_by_user_type = Q(business_analyst=login_user)
        elif table_type == 'lead':
            lead_ids = list(CrmOpportunity.cmobjects.filter(business_analyst=login_user).values_list('lead', flat=True))
            query_by_user_type = Q(id__in=lead_ids)

    elif user_type == 4:
        if table_type == 'opportunity':
            query_by_user_type = Q(Q(lead__assign_to__isnull=True) & Q(lead__created_by=login_user)) | \
                                 Q(Q(lead__assign_to__isnull=False) & Q(lead__assign_to=login_user))
            # query_by_user_type = Q(lead__created_by=login_user)|Q(lead__assign_to=login_user)
            # query_by_user_type = Q(lead__assign_to=login_user)
        elif table_type == 'lead':
            query_by_user_type = Q(Q(assign_to__isnull=True)&Q(created_by=login_user))|\
                                Q(Q(assign_to__isnull=False)&Q(assign_to=login_user))
            # query_by_user_type = Q(assign_to=login_user)

    return query_by_user_type


def get_change_request_milestone_amount(opportunity=None, amount_type='total'):
    milestone_value, change_request_value = 0, 0
    if amount_type == 'all':
        milestone_value = opportunity.milestone.filter(is_deleted=False).aggregate(
            sum=Sum('value')).get('sum')
        change_request_value = CrmOpportunityMilestoneChangeRequestDistribution.cmobjects.filter(opportunity=opportunity,
                            milestone__is_deleted=False).aggregate(sum=Sum('cr_value')).get('sum')
    elif amount_type == 'paid':
        milestone_value = opportunity.milestone.filter(is_deleted=False, is_paid=True).aggregate(
            sum=Sum('value')).get('sum')
        change_request_value = CrmOpportunityMilestoneChangeRequestDistribution.cmobjects.filter(opportunity=opportunity,
                            milestone__is_paid=True, milestone__is_deleted=False).aggregate(sum=Sum('cr_value')).get('sum')
    elif amount_type == 'unpaid':
        milestone_value = opportunity.milestone.filter(is_deleted=False, is_paid=False).aggregate(
            sum=Sum('value')).get('sum')
        change_request_value = CrmOpportunityMilestoneChangeRequestDistribution.cmobjects.filter(opportunity=opportunity,
                            milestone__is_paid=False, milestone__is_deleted=False).aggregate(sum=Sum('cr_value')).get('sum')
    milestone_value = milestone_value if milestone_value else 0
    change_request_value = change_request_value if change_request_value else 0
    value = milestone_value + change_request_value
    return round(value, 2)


def get_users_by_type(type=None):
    user_query = TMasterModuleRoleUser.objects.filter(mmr_role__cr_name=type, mmr_type=3,
                mmr_module__cm_url='sft-crm', mmr_is_deleted=False)
    user_list = [user_obj.mmr_user for user_obj in user_query]
    return user_list


def log(la=None, lai=None, lt=None, l='', cb=None):
    """
    :param la: log_against
    :param lai: log_against_id
    :param lt: log_type
    :param l: log
    :param cb: created_by
    :return: None
    """
    CrmLog.objects.create(log_against=la, log_against_id=lai, log_type=lt, log=l, created_by=cb)
    return


def logs(q=Q()):
    """
    :param q: query
    :return: list of log
    """
    from crm.serializers import CrmLogSerializer
    logs = CrmLog.objects.filter(q)
    log_serializer = CrmLogSerializer(logs, many=True)
    return log_serializer.data


def convert_to_utc(date_time=datetime.now()):
    UTC_OFFSET_TIMEDELTA = datetime.now() - datetime.utcnow()
    return date_time - UTC_OFFSET_TIMEDELTA


def celery_task_revoke(type=None, type_id=None):
    celery_tasks = CrmCeleryRevoke.cmobjects.filter(type=type, type_id=type_id, is_revoked=False)
    celery_ids = list(celery_tasks.values_list('celery_id', flat=True))
    [app.control.revoke(celery_task_id, terminate=True) for celery_task_id in celery_ids]
    celery_tasks.update(is_revoked=True)
    return
