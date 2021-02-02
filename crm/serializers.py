import copy
import json
from crm.tasks import task_schedule_reminder
import numpy as np
import pandas as pd
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q, F, Sum
from rest_framework.exceptions import APIException
from rest_framework.fields import IntegerField, FileField
from rest_framework.serializers import (ModelSerializer, SerializerMethodField, CurrentUserDefault, CharField,
                                        ListField, BooleanField)
from datetime import datetime, timedelta

from SSIL_SSO_MS import settings
from core.models import TCoreCountry, TCoreCurrency, TCoreDomain
from crm.constant import DEFAULT_CURRENCY, USER_TYPE, PROJECT_ID, NOTIFICATION_ACTION
from crm.currency_converter import realtime_exchange_rate, realtime_exchange_value
from crm.models import (CrmLead, CrmTask, CrmPoc, CrmOpportunity, CrmTechnology, CrmProject, CrmDepartment, CrmSource,
                        CrmLeadTaskMap, CrmOpportunityPocMap, CrmOpportunityDepartmentMap, CrmOpportunityTechnologyMap,
                        CrmMilestone, CrmUserTypeMap, CrmOpportunityPresaleLog, CrmOpportunityStageChangesLog,
                        CrmOpportunityPresaleLogDepartmentMap, CrmOpportunityTaskMap, CrmProjectDepartmentMap,
                        CrmProjectDomainMap, CrmProjectTechnologyMap, CrmPaymentMode, CrmOpportunityRemarks,
                        CrmOpportunityDomainMap, CrmOpportunityMilestoneMap, CrmColorStatus,
                        CrmCurrencyConversionHistory, CrmLeadReassignLog, CrmOpportunityBAChangeLog,
                        CrmOpportunityMilestoneChangeRequestDistribution, CrmChangeRequest,
                        CrmOpportunityChangeRequestMap, CrmDocument, CrmLeadDocument, CrmOpportunityResourceManagement,
                        CrmRequestHandler, CrmResource, CrmOpportunityDocumentTag, CrmDocumentTag, CrmLeadRemarks,
                        CrmLog, CrmProjectFormLog, CrmCeleryRevoke)
from crm.utils import (hard_update_mapping, get_opportunity_probability, get_query_by_user_type,
                       get_change_request_milestone_amount, get_users_by_type, get_user_type, logs, log, convert_to_utc,
                       celery_task_revoke)
from global_function import send_mail_list
from global_notification import store_sent_notification, send_notification
from master.models import TMasterModuleRoleUser
from users.models import TCoreUserDetail


class CrmUserSerializer(ModelSerializer):

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name')


class CrmDocumentSerializer(ModelSerializer):

    class Meta:
        model = CrmDocument
        fields = ('id', 'name', 'document', 'created_at')


class CrmDocumentTagSerializer(ModelSerializer):

    class Meta:
        model = CrmDocumentTag
        fields = ('id', 'name')


class CrmOpportunityDocumentTagSerializer(ModelSerializer):
    document = CrmDocumentSerializer()
    tag = CrmDocumentTagSerializer()

    class Meta:
        model = CrmOpportunityDocumentTag
        fields = ('id', 'document', 'tag', 'is_disabled')


class CrmTaskSerializer(ModelSerializer):

    class Meta:
        model = CrmTask
        fields = '__all__'


class CrmSourceSerializer(ModelSerializer):

    class Meta:
        model = CrmSource
        fields = ('id', 'name', 'description')


class CrmResourceSerializer(ModelSerializer):

    class Meta:
        model = CrmResource
        fields = ('id', 'name',)


class CrmCountrySerializer(ModelSerializer):

    class Meta:
        model = TCoreCountry
        fields = ('id', 'name', 'code', 'dialing_code')


class CrmDepartmentSerializer(ModelSerializer):

    class Meta:
        model = CrmDepartment
        fields = ('id', 'name')


class CrmCurrencySerializer(ModelSerializer):

    class Meta:
        model = TCoreCurrency
        fields = ('id', 'name', 'code', 'symbol')


class CrmColorStatusSerializer(ModelSerializer):

    class Meta:
        model = CrmColorStatus
        fields = ('id', 'name', 'hex', 'description')


class CrmTechnologySerializer(ModelSerializer):

    class Meta:
        model = CrmTechnology
        fields = ('id', 'name')


class CrmDomainSerializer(ModelSerializer):

    class Meta:
        model = TCoreDomain
        fields = ('id', 'name')


class CrmLogSerializer(ModelSerializer):
    created_by = CrmUserSerializer()

    class Meta:
        model = CrmLog
        fields = ('log', 'created_at', 'created_by')


class CrmRequestHandlerSerializer(ModelSerializer):

    class Meta:
        model = CrmRequestHandler
        fields = ('id', 'request_against', 'request_against_id', 'request_type', 'status', 'request_accepted_date',
                  'turnaround_time')


class CrmChangeRequestSerializer(ModelSerializer):

    class Meta:
        model = CrmChangeRequest
        fields = '__all__'


class CrmChangeRequestGetSerializer(ModelSerializer):
    id = IntegerField(required=False)

    class Meta:
        model = CrmChangeRequest
        fields = ('id', 'cr_no', 'name', 'value', 'man_hours', 'cr_document', 'remarks')


class CrmMilestoneSerializer(ModelSerializer):

    class Meta:
        model = CrmMilestone
        fields = '__all__'


class CrmPocSerializer(ModelSerializer):

    class Meta:
        model = CrmPoc
        fields = '__all__'


class CrmPocGetSerializer(ModelSerializer):
    source = CrmSourceSerializer()
    country = CrmCountrySerializer()

    class Meta:
        model = CrmPoc
        fields = '__all__'


class CrmLeadSerializer(ModelSerializer):

    class Meta:
        model = CrmLead
        fields = '__all__'


class CrmLeadGetSerializer(ModelSerializer):
    poc = CrmPocGetSerializer()

    class Meta:
        model = CrmLead
        fields = '__all__'


class CrmLeadRemarksSerializer(ModelSerializer):
    created_by = CrmUserSerializer()

    class Meta:
        model = CrmLeadRemarks
        fields = ('id', 'remarks', 'reason', 'created_by', 'created_at')


class CrmLeadReassignLogSerializer(ModelSerializer):
    pre_assign_to = CrmUserSerializer()

    class Meta:
        model = CrmLeadReassignLog
        fields = ('pre_assign_to', 'remarks', 'created_at')


class CrmProjectFormLogSerializer(ModelSerializer):
    created_by = CrmUserSerializer()
    data = SerializerMethodField()

    class Meta:
        model = CrmProjectFormLog
        fields = ('is_open', 'data', 'created_at', 'created_by')

    def get_data(self, obj):
        data = dict()
        try:
            data = json.loads(obj.data)
        except Exception as e:
            pass
        return data


class CrmOpportunitySerializer(ModelSerializer):

    class Meta:
        model = CrmOpportunity
        fields = '__all__'


class CrmOpportunityMilestoneChangeRequestDistributionSerializer(ModelSerializer):
    opportunity = CrmOpportunitySerializer(required=False)
    change_request = CrmChangeRequestSerializer(required=False)

    class Meta:
        model = CrmOpportunityMilestoneChangeRequestDistribution
        fields = '__all__'


class CrmOpportunityGetSerializer(ModelSerializer):
    poc = CrmPocGetSerializer(many=True)
    status_name = CharField(source='get_status_display')
    business_analyst = CrmUserSerializer()
    department = CrmDepartmentSerializer(many=True)

    class Meta:
        model = CrmOpportunity
        fields = '__all__'
        extra_fields = ('status_name',)


# :::::::::::::::::::::: Document ::::::::::::::::::::::::::: #
class CrmDocumentAddSerializer(ModelSerializer):
    created_by = CharField(default=CurrentUserDefault())

    class Meta:
        model = CrmDocument
        fields = '__all__'


class CrmDocumentMultiUploadSerializer(ModelSerializer):
    created_by = CharField(default=CurrentUserDefault())
    documents = ListField(child=FileField(max_length=100000,allow_empty_file=False,use_url=False),required=False)
    document_ids = ListField(required=False)

    class Meta:
        model = CrmDocument
        fields = ('created_by', 'documents', 'document_ids')

    def create(self, validated_data):
        with transaction.atomic():
            documents = validated_data.get('documents')
            created_by = validated_data.get('created_by')
            doc_ids = list()
            for doc in documents:
                document = CrmDocument.objects.create(document=doc, created_by=created_by)
                doc_ids.append(document.id)

            validated_data['document_ids'] = doc_ids
            return validated_data


# :::::::::::::::::::::: Department ::::::::::::::::::::::::::: #
class CrmDepartmentAddSerializer(ModelSerializer):
    created_by = CharField(default=CurrentUserDefault())

    class Meta:
        model = CrmDepartment
        fields = '__all__'


class CrmDepartmentEditSerializer(ModelSerializer):
    updated_by = CharField(default=CurrentUserDefault())

    class Meta:
        model = CrmDepartment
        fields = '__all__'


class CrmDepartmentDeleteSerializer(ModelSerializer):
    updated_by = CharField(default=CurrentUserDefault())
    deleted_by = CharField(default=CurrentUserDefault())

    class Meta:
        model = CrmDepartment
        fields = '__all__'

    def update(self, instance, validated_data):
        with transaction.atomic():
            instance.is_deleted=True
            instance.updated_by = validated_data.get('updated_by')
            instance.deleted_by = validated_data.get('deleted_by')
            instance.save()
            return instance


# :::::::::::::::::::::: Resource ::::::::::::::::::::::::::: #
class CrmResourceAddSerializer(ModelSerializer):
    created_by = CharField(default=CurrentUserDefault())

    class Meta:
        model = CrmResource
        fields = '__all__'


class CrmResourceEditSerializer(ModelSerializer):
    updated_by = CharField(default=CurrentUserDefault())

    class Meta:
        model = CrmDepartment
        fields = '__all__'


class CrmResourceDeleteSerializer(ModelSerializer):
    updated_by = CharField(default=CurrentUserDefault())
    deleted_by = CharField(default=CurrentUserDefault())

    class Meta:
        model = CrmDepartment
        fields = '__all__'

    def update(self, instance, validated_data):
        with transaction.atomic():
            instance.is_deleted=True
            instance.updated_by = validated_data.get('updated_by')
            instance.deleted_by = validated_data.get('deleted_by')
            instance.save()
            return instance


# :::::::::::::::::::::: DocumentTag ::::::::::::::::::::::::::: #
class CrmDocumentTagAddSerializer(ModelSerializer):
    created_by = CharField(default=CurrentUserDefault())

    class Meta:
        model = CrmDocumentTag
        fields = '__all__'


class CrmDocumentTagEditSerializer(ModelSerializer):
    updated_by = CharField(default=CurrentUserDefault())

    class Meta:
        model = CrmDocumentTag
        fields = '__all__'


class CrmDocumentTagDeleteSerializer(ModelSerializer):
    updated_by = CharField(default=CurrentUserDefault())
    deleted_by = CharField(default=CurrentUserDefault())

    class Meta:
        model = CrmDocumentTag
        fields = '__all__'

    def update(self, instance, validated_data):
        with transaction.atomic():
            instance.is_deleted=True
            instance.updated_by = validated_data.get('updated_by')
            instance.deleted_by = validated_data.get('deleted_by')
            instance.save()
            return instance


# :::::::::::::::::::::: Technology ::::::::::::::::::::::::::: #
class CrmTechnologyAddSerializer(ModelSerializer):
    created_by = CharField(default=CurrentUserDefault())

    class Meta:
        model = CrmTechnology
        fields = '__all__'


class CrmTechnologyEditSerializer(ModelSerializer):
    updated_by = CharField(default=CurrentUserDefault())

    class Meta:
        model = CrmTechnology
        fields = '__all__'


class CrmTechnologyDeleteSerializer(ModelSerializer):
    updated_by = CharField(default=CurrentUserDefault())
    deleted_by = CharField(default=CurrentUserDefault())

    class Meta:
        model = CrmTechnology
        fields = '__all__'

    def update(self, instance, validated_data):
        with transaction.atomic():
            instance.is_deleted=True
            instance.updated_by = validated_data.get('updated_by')
            instance.deleted_by = validated_data.get('deleted_by')
            instance.save()
            return instance


# :::::::::::::::::::::: Source ::::::::::::::::::::::::::: #
class CrmSourceAddSerializer(ModelSerializer):
    created_by = CharField(default=CurrentUserDefault())

    class Meta:
        model = CrmSource
        fields = '__all__'


class CrmSourceEditSerializer(ModelSerializer):
    updated_by = CharField(default=CurrentUserDefault())

    class Meta:
        model = CrmSource
        fields = '__all__'


class CrmSourceDeleteSerializer(ModelSerializer):
    updated_by = CharField(default=CurrentUserDefault())
    deleted_by = CharField(default=CurrentUserDefault())

    class Meta:
        model = CrmSource
        fields = '__all__'

    def update(self, instance, validated_data):
        with transaction.atomic():
            instance.is_deleted=True
            instance.updated_by = validated_data.get('updated_by')
            instance.deleted_by = validated_data.get('deleted_by')
            instance.save()
            return instance


# :::::::::::::::::::::: PaymentMode ::::::::::::::::::::::::::: #
class CrmPaymentModeAddSerializer(ModelSerializer):
    created_by = CharField(default=CurrentUserDefault())

    class Meta:
        model = CrmPaymentMode
        fields = '__all__'


class CrmPaymentModeEditSerializer(ModelSerializer):
    updated_by = CharField(default=CurrentUserDefault())

    class Meta:
        model = CrmPaymentMode
        fields = '__all__'


class CrmPaymentModeDeleteSerializer(ModelSerializer):
    updated_by = CharField(default=CurrentUserDefault())
    deleted_by = CharField(default=CurrentUserDefault())

    class Meta:
        model = CrmPaymentMode
        fields = '__all__'

    def update(self, instance, validated_data):
        with transaction.atomic():
            instance.is_deleted=True
            instance.updated_by = validated_data.get('updated_by')
            instance.deleted_by = validated_data.get('deleted_by')
            instance.save()
            return instance


# :::::::::::::::::::::: ColorStatus ::::::::::::::::::::::::::: #
class CrmColorStatusAddSerializer(ModelSerializer):
    created_by = CharField(default=CurrentUserDefault())

    class Meta:
        model = CrmColorStatus
        fields = '__all__'


class CrmColorStatusEditSerializer(ModelSerializer):
    updated_by = CharField(default=CurrentUserDefault())

    class Meta:
        model = CrmColorStatus
        fields = '__all__'


class CrmColorStatusDeleteSerializer(ModelSerializer):
    updated_by = CharField(default=CurrentUserDefault())
    deleted_by = CharField(default=CurrentUserDefault())

    class Meta:
        model = CrmColorStatus
        fields = '__all__'

    def update(self, instance, validated_data):
        with transaction.atomic():
            instance.is_deleted=True
            instance.updated_by = validated_data.get('updated_by')
            instance.deleted_by = validated_data.get('deleted_by')
            instance.save()
            return instance


class CrmLeadListSerializer(ModelSerializer):
    status_name = CharField(source='get_status_display')
    created_by_name = SerializerMethodField()
    task = SerializerMethodField()
    poc = CrmPocGetSerializer()
    days_old = SerializerMethodField()
    prospecting_member_name = SerializerMethodField()
    reassign_request = SerializerMethodField()
    junk_latest_remarks = SerializerMethodField()
    junk_remarks_log = SerializerMethodField()

    class Meta:
        model = CrmLead
        fields = '__all__'
        extra_fields = ('days_old', 'status_name', 'prospecting_member_name', 'created_by_name', 'reassign_request',
                        'junk_latest_remarks', 'junk_remarks_log')


    def get_junk_remarks_log(self, obj):
        junk_remarks = CrmLeadRemarks.cmobjects.filter(lead=obj, type=1)
        junk_serializer = CrmLeadRemarksSerializer(junk_remarks, many=True)
        return junk_serializer.data

    def get_junk_latest_remarks(self, obj):
        junk_log = CrmLeadRemarks.cmobjects.filter(lead=obj, type=1).order_by('-id').first()
        junk_serializer = CrmLeadRemarksSerializer(junk_log, many=False)
        return junk_serializer.data

    def get_reassign_request(self, obj):
        request_handler = CrmRequestHandler.cmobjects.filter(request_against_id=obj.id, request_against=1,
                        request_type=3, status=1).order_by('-id').first()
        request_handler_serializer = CrmRequestHandlerSerializer(request_handler, many=False)
        return request_handler_serializer.data if request_handler else None

    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else ''

    def get_prospecting_member_name(self, obj):
        return obj.assign_to.get_full_name() if obj.assign_to else obj.created_by.get_full_name()

    def get_task(self, obj):
        return obj.task.filter(is_completed=False).values()

    def get_days_old(self, obj):
        current_date = datetime.now().date()
        return (current_date - obj.created_at.date()).days


class CrmLeadCreateSerializer(ModelSerializer):
    created_by = CharField(default=CurrentUserDefault())
    poc = CrmPocSerializer()

    class Meta:
        model = CrmLead
        fields = ('poc', 'created_by', 'business_name', 'cin', 'gstin', 'pan', 'remarks', 'social_link', 'territory')

    def create(self, validated_data):
        with transaction.atomic():
            print(validated_data)
            created_by = validated_data.get('created_by')
            business_name = validated_data.get('business_name')
            remarks = validated_data.get('remarks')
            poc = dict(validated_data.get('poc'))
            email = poc.get('email')
            phone = poc.get('phone')

            is_lead_existed = CrmLead.cmobjects.filter(Q(business_name=business_name)|Q(poc__email=email)|Q(poc__phone=phone)).count()
            if is_lead_existed:
                raise APIException({'request_status':0, 'msg':'Email, Phone or Business Name already exist.'})

            validated_data['poc'] = CrmPoc.objects.create(
                created_by=created_by,
                **dict(validated_data['poc'])
            )
            lead_obj = CrmLead.objects.create(**validated_data)

            if remarks:
                CrmLeadRemarks.objects.create(lead=lead_obj, remarks=remarks, created_by=created_by)


            if get_user_type(user=created_by) == 4:
                user_list = [{'recipient': user, 'lead': lead_obj} for user in get_users_by_type(type='Sales Manager')]
                self.send_mail_notification(user_list=user_list, created_by=created_by)

            return lead_obj

    def send_mail_notification(self,user_list=list(), created_by=None):
        for user_data in user_list:
            """
            Mail processing.
            """
            user_mail = user_data['recipient'].cu_user.cu_alt_email_id
            mail_data = {
                'recipient_name': user_data['recipient'].get_full_name(),
                'lead_name': user_data['lead'].business_name,
                'created_by': created_by.get_full_name(),
            }
            if user_mail:
                send_mail_list('SFT-CRM-LDCRT', [user_mail], mail_data, ics='')

            """
            Notification processing.
            """
            users = [user_data['recipient']]
            title = 'Following lead has been created by {}.'.format(created_by.get_full_name())
            body = 'Lead: {} \nPerson of Contact:{} {} \nCountry:{} \nPhone:{} \nEmail: {}'.format(
                user_data['lead'].business_name, user_data['lead'].poc.first_name, user_data['lead'].poc.last_name,
                user_data['lead'].poc.country.name, user_data['lead'].poc.phone, user_data['lead'].poc.email)

            data = {
                "app_module": "sft-crm",
                "type": "lead",
                "id": user_data['lead'].id,
                'action': NOTIFICATION_ACTION['lead']
            }
            data_str = json.dumps(data)
            notification_id = store_sent_notification(users=users, body=body, title=title, data=data_str,
                                                      app_module_name='sft-crm')
            send_notification(users=users, body=body, title=title, data=data, notification_id=notification_id)

        return


class CrmLeadUpdateSerializer(ModelSerializer):
    created_by = CharField(default=CurrentUserDefault())
    poc = CrmPocSerializer()

    class Meta:
        model = CrmLead
        fields = ('poc', 'created_by', 'business_name', 'cin', 'gstin', 'pan', 'remarks', 'social_link', 'territory')

    def update(self, instance, validated_data):
        with transaction.atomic():
            print(validated_data)
            created_by = validated_data.get('created_by')
            remarks = validated_data.get('remarks')
            business_name = validated_data.get('business_name')
            poc = dict(validated_data.get('poc'))
            email = poc.get('email')
            phone = poc.get('phone')

            is_lead_existed = CrmLead.cmobjects.exclude(id=instance.id).filter(Q(business_name=business_name)|Q(poc__email=email)|Q(poc__phone=phone)).count()
            if is_lead_existed:
                raise APIException({'request_status':0, 'msg':'Email, Phone or Business Name already exist.'})

            validated_data['poc'] = CrmPoc.objects.create(
                created_by=created_by,
                **dict(validated_data['poc'])
            )
            lead_obj = CrmLead.objects.filter(id=instance.id).update(**validated_data)

            if remarks:
                CrmLeadRemarks.objects.create(lead=instance, remarks=remarks, created_by=created_by)

            # Action Log
            log(la=1, lai=instance.id, l='This lead has been updated.', cb=created_by)

            return validated_data


class CrmLeadBulkUploadSerializer(ModelSerializer):
    created_by = CharField(default=CurrentUserDefault())
    lead_list = ListField(required=False)
    created_lead_list = ListField(required=False)
    skipped_lead_list = ListField(required=False)

    class Meta:
        model = CrmLeadDocument
        fields = ('created_by', 'lead_document', 'lead_list', 'created_lead_list', 'skipped_lead_list')

    def create(self, validated_data):
        with transaction.atomic():
            print(validated_data)
            print(self.context)
            created_by = validated_data.get('created_by')
            lead_document = validated_data.get('lead_document')
            file_path = settings.MEDIA_ROOT+'/' + lead_document.document.name

            data = pd.read_excel(file_path)
            data = data.replace(np.nan, '', regex=True)
            print(data.values)
            lead_list = list()
            created_lead_list = list()
            skipped_lead_list = list()
            for row in data.values:
                lead_dict = dict()
                print(row[0])
                lead_list.append(row)
                # mandatory 0,6,7,9,10,12,15
                lead_dict['created_by_id'] = created_by.id
                lead_dict['business_name'] = row[0]
                lead_dict['cin'] = row[1]
                lead_dict['gstin'] = row[2]
                lead_dict['pan'] = row[3]
                lead_dict['remarks'] = row[4]
                lead_dict['social_link'] = row[5]
                lead_dict['territory'] = row[6]
                lead_dict['poc'] = dict()
                lead_dict['poc']['first_name'] = row[7]
                lead_dict['poc']['last_name'] = row[8]
                lead_dict['poc']['phone'] = row[9]
                lead_dict['poc']['country_id'] = row[10]
                lead_dict['poc']['mobile'] = row[11]
                lead_dict['poc']['email'] = row[12]
                lead_dict['poc']['job_title'] = row[13]
                lead_dict['poc']['is_primary'] = True
                lead_dict['poc']['url'] = row[14]
                lead_dict['poc']['source_id'] = row[15]

                if row[6] and row[6].lower() == 'indian':
                    lead_dict['territory'] = 1
                elif row[6] and row[6].lower() == 'global':
                    lead_dict['territory'] = 2
                else:
                    lead_dict['territory'] = 0

                country = TCoreCountry.objects.filter(code_3=row[10]).first()
                lead_dict['poc']['country_id'] = country.id if country else None

                source = CrmSource.cmobjects.filter(name=row[15]).first()
                lead_dict['poc']['source_id'] = source.id if source else None

                lead_list.append(copy.deepcopy(lead_dict))
                print(lead_dict)
                is_lead_existed = CrmLead.cmobjects.filter(Q(business_name=lead_dict['business_name'])|
                                Q(poc__email=lead_dict['poc']['email'])|Q(poc__phone=lead_dict['poc']['phone'])).count()
                if is_lead_existed or not lead_dict['business_name'] or not lead_dict['territory'] or \
                    not lead_dict['poc']['first_name'] or not lead_dict['poc']['phone'] or \
                    not lead_dict['poc']['country_id'] or not lead_dict['poc']['email'] or \
                    not lead_dict['poc']['source_id']:
                    skipped_lead_list.append(row)
                    skipped_lead_list.append(copy.deepcopy(lead_dict))
                    continue
                else:
                    created_lead_list.append(row)
                    created_lead_list.append(copy.deepcopy(lead_dict))


                lead_dict['poc'] = CrmPoc.objects.create(
                    created_by=created_by,
                    **dict(lead_dict['poc'])
                )
                lead_obj = CrmLead.objects.create(**lead_dict)
                # lead_dict['poc'] = lead_dict['poc'].id
            validated_data['lead_list'] = lead_list
            validated_data['created_lead_list'] = created_lead_list
            validated_data['skipped_lead_list'] = skipped_lead_list
            return validated_data


class CrmStatusUpdateMultiLeadSerializer(ModelSerializer):
    updated_by = CharField(default=CurrentUserDefault())
    leads = ListField(required=False)
    remarks = CharField(required=False, allow_blank=True, allow_null=True)
    reason = CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = CrmLead
        fields = ('status', 'updated_by', 'leads', 'remarks', 'reason')

    def create(self, validated_data):
        with transaction.atomic():
            updated_by = validated_data.get('updated_by')
            leads = validated_data.get('leads')
            status = validated_data.get('status')
            remarks = validated_data.get('remarks')
            reason = validated_data.get('reason')

            lead_queryset = CrmLead.cmobjects.filter(id__in=leads)
            lead_queryset.update(status=status, updated_by=updated_by)
            
            if remarks and reason:
                [CrmLeadRemarks.objects.create(lead=lead, remarks=remarks, reason=reason, type=1, created_by=updated_by) for lead in lead_queryset]


            # Action Log
            msg = 'The status of this lead has been changed to {}.'
            [log(la=1, lai=lead.id, l=msg.format(lead.get_status_display()), cb=updated_by) for lead in lead_queryset]

            sales_managers = get_users_by_type(type='Sales Manager')
            user_list = [{'lead': lead, 'recipients':sales_managers} for lead in lead_queryset]
            self.send_mail_notification(user_list=user_list)

            return validated_data

    def send_mail_notification(self, user_list=list()):
        for user_data in user_list:
            """
            Notification processing.
            """
            users = user_data['recipients']
            title = 'The status of following lead has been changed to {}.'.format(user_data['lead'].get_status_display())
            body = 'Lead: {} \nPerson of Contact:{} {} \nCountry:{} \nPhone:{} \nEmail: {}'.format(
                user_data['lead'].business_name, user_data['lead'].poc.first_name, user_data['lead'].poc.last_name,
                user_data['lead'].poc.country.name, user_data['lead'].poc.phone, user_data['lead'].poc.email)

            data = {
                "app_module": "sft-crm",
                "type": "lead",
                "id": user_data['lead'].id,
                'action': NOTIFICATION_ACTION['lead']
            }
            data_str = json.dumps(data)
            notification_id = store_sent_notification(users=users, body=body, title=title, data=data_str,
                                                      app_module_name='sft-crm')
            send_notification(users=users, body=body, title=title, data=data, notification_id=notification_id)

        return


class CrmLeadStatusUpdateSerializer(ModelSerializer):
    #task = CrmTaskSerializer(many=True, required=False)
    updated_by = CharField(default=CurrentUserDefault())

    class Meta:
        model = CrmLead
        fields = ('updated_by', 'status')

    def update(self, instance, validated_data):
        with transaction.atomic():
            instance.status = validated_data.get('status', instance.status)
            instance.updated_by = validated_data.get('updated_by', instance.updated_by)
            instance.save()
            return instance


class CrmLeadAssignSerializer(ModelSerializer):
    updated_by = CharField(default=CurrentUserDefault())
    leads = ListField(required=False)
    is_reassign = BooleanField(required=False, default=False)
    is_notify_with_email = BooleanField(required=False, default=True)
    remarks = CharField(required=False,allow_blank=True, allow_null=True)

    class Meta:
        model = CrmLead
        fields = ('updated_by', 'assign_to', 'assign_from', 'leads', 'is_reassign', 'remarks', 'is_notify_with_email')

    def create(self, validated_data):
        with transaction.atomic():
            print(validated_data)
            current_date = datetime.now()
            leads = validated_data.pop('leads',[])
            is_reassign = validated_data.pop('is_reassign')
            is_notify_with_email = validated_data.pop('is_notify_with_email')
            assign_to = validated_data.get('assign_to')
            assign_from = validated_data.get('assign_from')
            updated_by = validated_data.get('updated_by')
            remarks = validated_data.get('remarks')

            lead_queryset = CrmLead.cmobjects.filter(id__in=leads)
            user_list = [{'lead': lead, 'recipient':assign_to, 'assign_to':assign_to} for lead in lead_queryset]
            if is_reassign:
                [CrmLeadReassignLog.objects.create(lead=lead, pre_assign_to=lead.assign_to, re_assign_to=assign_to,
                            created_by=updated_by, remarks=remarks) for lead in lead_queryset]
                user_list.extend([{'lead': lead, 'recipient':lead.assign_to, 'assign_to':assign_to} for lead in lead_queryset if lead.assign_to])
                lead_queryset.update(assign_from=assign_from, assign_to=assign_to, updated_by=updated_by,
                                     assign_to_date=current_date)
            else:
                lead_queryset.update(status=1,assign_from=assign_from, assign_to=assign_to, updated_by=updated_by,
                                     assign_to_date=current_date)

            if remarks:
                [CrmLeadRemarks.objects.create(lead=lead, remarks=remarks, created_by=updated_by) for lead in lead_queryset]

            lead_ids = list(lead_queryset.values_list('id', flat=True))
            CrmRequestHandler.cmobjects.filter(request_against_id__in=lead_ids, request_against=1, request_type=3,
                            status=1).update(status=2, updated_by=updated_by, request_accepted_date=current_date)

            # Action Log
            msg = 'This lead has been assigned to {}.'.format(assign_to.get_full_name())
            [log(la=1, lai=lead.id, l=msg, cb=updated_by) for lead in lead_queryset]

            self.send_mail_notification(user_list=user_list, is_notify_with_email=is_notify_with_email,
                                        is_reassign=is_reassign)
            return validated_data

    def send_mail_notification(self,user_list=list(), is_notify_with_email=True, is_reassign=False):
        for user_data in user_list:
            """
            Mail processing.
            """
            user_mail = user_data['recipient'].cu_user.cu_alt_email_id
            mail_data = {
                'recipient_name': user_data['recipient'].get_full_name(),
                'lead_name': user_data['lead'].business_name,
                'assign_to': user_data['assign_to'].get_full_name(),
                'is_reassign': is_reassign,
                'is_self': user_data['recipient'] == user_data['assign_to']
            }
            print(is_notify_with_email)
            print(user_mail)
            if is_notify_with_email and user_mail:
                send_mail_list('SFT-CRM-LDASS', [user_mail], mail_data, ics='')

            """
            Notification processing.
            """
            users = [user_data['recipient']]
            title = 'Following lead has been assigned to {}.'.format(user_data['assign_to'].get_full_name())
            body = 'Lead: {} \nPerson of Contact:{} {} \nCountry:{} \nPhone:{} \nEmail: {}'.format(
                user_data['lead'].business_name, user_data['lead'].poc.first_name, user_data['lead'].poc.last_name,
                user_data['lead'].poc.country.name, user_data['lead'].poc.phone, user_data['lead'].poc.email)

            data = {
                "app_module": "sft-crm",
                "type": "lead",
                "id": user_data['lead'].id,
                'action': NOTIFICATION_ACTION['lead']
            }
            data_str = json.dumps(data)
            notification_id = store_sent_notification(users=users, body=body, title=title, data=data_str,
                                                      app_module_name='sft-crm')
            send_notification(users=users, body=body, title=title, data=data, notification_id=notification_id)

        return


class CrmAddTaskToLeadSerializer(ModelSerializer):
    created_by = CharField(default=CurrentUserDefault())
    task = CrmTaskSerializer()

    class Meta:
        model = CrmLead
        fields = ('task', 'created_by')

    def update(self, instance, validated_data):
        with transaction.atomic():
            created_by = validated_data.get('created_by')
            task_obj = CrmTask.objects.create(
                    created_by=created_by,
                    **dict(validated_data['task'])
                )
            CrmLeadTaskMap.objects.create(lead=instance,task=task_obj,created_by=created_by)
            validated_data['task'] = task_obj.__dict__
            return validated_data


class CrmLeadRequestReassignSerializer(ModelSerializer):
    created_by = CharField(default=CurrentUserDefault())

    class Meta:
        model = CrmLead
        fields = ('created_by', )

    def update(self, instance, validated_data):
        with transaction.atomic():
            login_user = self.context['request'].user
            created_by = validated_data.get('created_by', login_user)
            user_list = [{'lead': instance, 'recipients':get_users_by_type(type='Sales Manager')}]
            print(user_list)
            self.send_mail_notification(user_list=user_list, user_id=created_by.id)

            return validated_data

    def send_mail_notification(self,user_list=list(), user_id=None):
        for user_data in user_list:
            """
            Notification processing.
            """
            users = user_data['recipients']
            title = 'Following lead has been requested for reassign.'
            body = 'Lead: {} \nPerson of Contact:{} {} \nCountry:{} \nPhone:{} \nEmail: {}'.format(
                user_data['lead'].business_name, user_data['lead'].poc.first_name, user_data['lead'].poc.last_name,
                user_data['lead'].poc.country.name, user_data['lead'].poc.phone, user_data['lead'].poc.email)

            data = {
                "app_module": "sft-crm",
                "type": "lead",
                "id": user_data['lead'].id,
                'user_id': user_id,
                'action': NOTIFICATION_ACTION['request_reassign']
            }
            data_str = json.dumps(data)
            notification_id = store_sent_notification(users=users, body=body, title=title, data=data_str,
                                                      app_module_name='sft-crm')
            send_notification(users=users, body=body, title=title, data=data, notification_id=notification_id)

        return


class CrmLeadDetailsSerializer(ModelSerializer):
    task = CrmTaskSerializer(many=True)
    poc = CrmPocGetSerializer()
    created_by = CrmUserSerializer()
    assign_to = CrmUserSerializer()
    owner_log = SerializerMethodField()
    remarks_log = SerializerMethodField()
    log = SerializerMethodField()

    class Meta:
        model = CrmLead
        fields = '__all__'
        extra_fields = ('owner_log', 'remarks_log', 'log')

    def get_log(self, obj):
        return logs(q=Q(log_against=1)&Q(log_against_id=obj.id))

    def get_remarks_log(self, obj):
        remarks = CrmLeadRemarks.cmobjects.filter(lead=obj)
        remarks_serializer = CrmLeadRemarksSerializer(remarks, many=True)
        return remarks_serializer.data

    def get_owner_log(self, obj):
        reassign_log = CrmLeadReassignLog.cmobjects.filter(lead=obj)
        reassign_log_serializer = CrmLeadReassignLogSerializer(reassign_log, many=True)
        return reassign_log_serializer.data


class CrmTaskUpdateSerializer(ModelSerializer):
    updated_by = CharField(default=CurrentUserDefault())

    class Meta:
        model = CrmTask
        fields = ('name', 'date_time', 'remarks', 'is_completed', 'updated_by',)

    def update(self, instance, validated_data):
        with transaction.atomic():
            updated_by = validated_data.get('updated_by')
            is_completed = validated_data.get('is_completed')
            date_time = validated_data.get('date_time')

            instance.name = validated_data.get('name',instance.name)
            instance.date_time = validated_data.get('date_time', instance.date_time)
            instance.remarks = validated_data.get('remarks', instance.remarks)
            instance.is_completed = validated_data.get('is_completed', instance.is_completed)
            instance.updated_by = validated_data.get('updated_by', instance.updated_by)
            instance.save()

            lead_task = CrmLeadTaskMap.cmobjects.filter(task=instance).first()
            print(lead_task)
            if lead_task:
                recipient_list = self.get_recipient_list(updated_by=updated_by, lead=lead_task.lead)
                title = 'The task "{}" has been updated for the following lead.'
                if is_completed:
                    title = 'The task "{}" has been completed for the following lead.'.format(instance.name)
                elif date_time:
                    title = 'The task "{}" has been reschedule on {} for the following lead.'.format(instance.name, date_time.strftime('%d/%m/%y'))

                body = 'Lead: {} \nPerson of Contact:{} {} \nCountry:{} \nPhone:{} \nEmail: {}'.format(
                    lead_task.lead.business_name, lead_task.lead.poc.first_name, lead_task.lead.poc.last_name,
                    lead_task.lead.poc.country.name, lead_task.lead.poc.phone, lead_task.lead.poc.email)

                print(recipient_list)
                user_list = [{'recipient': user, 'lead': lead_task.lead} for user in recipient_list if user]
                self.send_mail_notification(user_list=user_list, body=body, title=title, type='lead', task=instance, date_time=date_time)

            opportunity_task = CrmOpportunityTaskMap.cmobjects.filter(task=instance).first()
            if opportunity_task:
                recipient_list = self.get_recipient_list(updated_by=updated_by, lead=opportunity_task.opportunity.lead)
                title = 'The task "{}" has been updated on for the following opportunity.'
                if is_completed:
                    title = 'The task "{}" has been completed for the following opportunity.'.format(instance.name)
                elif date_time:
                    title = 'The task "{}" has been reschedule on {} for the following opportunity.'.format(instance.name, date_time.strftime('%d/%m/%y'))

                body = 'Opportunity Name: {} \nBusiness Name:{}'.format(opportunity_task.opportunity.opportunity_name,
                                                                        opportunity_task.opportunity.business_name)

                user_list = [{'recipient': user, 'opportunity': opportunity_task.opportunity} for user in recipient_list if user]
                self.send_mail_notification(user_list=user_list, body=body, title=title, type='opportunity', task=instance, date_time=date_time)

            return instance

    def get_recipient_list(self, updated_by=None, lead=None):
        recipient_list = []
        if get_user_type(user=updated_by) == 4:
            recipient_list.extend(get_users_by_type(type='Sales Manager'))

        elif get_user_type(user=updated_by) == 1:
            recipient = lead.assign_to if lead.assign_to else lead.created_by
            recipient_list.append(recipient)
        return recipient_list

    def send_mail_notification(self,user_list=list(), body='', title='', type='', task=None, date_time=None):
        # Revoke old scedule task
        celery_task_revoke(type=1, type_id=task.id)

        for user_data in user_list:
            """
            Task processing.
            """
            user_mail = user_data['recipient'].cu_user.cu_alt_email_id
            user_name = user_data['recipient'].get_full_name()
            if date_time and user_mail:
                utc_date_time = convert_to_utc(date_time=date_time)
                eta_15 = utc_date_time - timedelta(minutes=15)
                kwargs_dict = {
                    'recipient': user_name,
                    'user_email' : user_mail,
                    'task_id': task.id
                }
                celery_task_id_15 = task_schedule_reminder.apply_async(kwargs=kwargs_dict, eta=eta_15)

                eta_5 = utc_date_time - timedelta(minutes=5)
                celery_task_id_5 = task_schedule_reminder.apply_async(kwargs=kwargs_dict, eta=eta_5)

                CrmCeleryRevoke.objects.create(celery_id=celery_task_id_15.id, type=1, type_id=task.id)
                CrmCeleryRevoke.objects.create(celery_id=celery_task_id_5.id, type=1, type_id=task.id)

            """
            Notification processing.
            """
            users = [user_data['recipient']]
            data = {
                "app_module": "sft-crm",
                "type": type,
                "id": user_data[type].id,
                'action': NOTIFICATION_ACTION[type]
            }
            data_str = json.dumps(data)
            notification_id = store_sent_notification(users=users, body=body, title=title, data=data_str,
                                                      app_module_name='sft-crm')
            send_notification(users=users, body=body, title=title, data=data, notification_id=notification_id)

        return


class CrmPocUpdateSerializer(ModelSerializer):
    updated_by = CharField(default=CurrentUserDefault())

    class Meta:
        model = CrmPoc
        fields = '__all__'

    def update(self, instance, validated_data):
        with transaction.atomic():
            login_user = self.context['request'].user
            updated_by = validated_data.get('updated_by', login_user)
            instance.is_deleted = validated_data.get('is_deleted',instance.is_deleted)
            instance.first_name = validated_data.get('first_name', instance.first_name)
            instance.last_name = validated_data.get('last_name', instance.last_name)
            instance.phone = validated_data.get('phone', instance.phone)
            instance.mobile = validated_data.get('mobile', instance.mobile)
            instance.email = validated_data.get('email', instance.email)
            instance.job_title = validated_data.get('job_title', instance.job_title)
            instance.url = validated_data.get('url', instance.url)
            instance.country = validated_data.get('country', instance.country)
            instance.source = validated_data.get('source', instance.source)
            instance.updated_by = updated_by
            instance.save()
            return instance


class CrmOpportunityCreateSerializer(ModelSerializer):
    created_by = CharField(default=CurrentUserDefault())
    poc = CrmPocSerializer(many=True, required=False)
    department = ListField(required=False)
    technology = ListField(required=False)
    domain = ListField(required=False)
    remarks = CharField(required=False, allow_blank=True)

    class Meta:
        model = CrmOpportunity
        fields = ('territory', 'country', 'business_name', 'account_manager', 'project_lead', 'business_analyst',
                  'cin', 'pan', 'gstin', 'opportunity_name', 'opportunity_date', 'expected_closer_date',
                  'engagement', 'domain', 'department', 'technology', 'business_url', 'man_hours', 'value',
                  'currency', 'mode_of_payment', 'lead', 'poc', 'scope_of_work', 'created_by', 'remarks')

    def create(self, validated_data):
        with transaction.atomic():
            created_by = validated_data['created_by']
            lead = validated_data.get('lead')
            poc_list = validated_data.pop('poc')
            department_list = validated_data.pop('department')
            technology_list = validated_data.pop('technology')
            domain_list = validated_data.pop('domain')
            remarks = validated_data.pop('remarks')
            scope_of_work = validated_data.get('scope_of_work')

            opportunity_obj = CrmOpportunity.objects.create(**validated_data)

            rate_to_inr = realtime_exchange_rate(from_currency=opportunity_obj.currency.code)
            opportunity_obj.conversion_rate_to_inr = rate_to_inr
            opportunity_obj.save()
            inr_obj = TCoreCurrency.objects.get(code='INR')
            CrmCurrencyConversionHistory.objects.create(from_currency=opportunity_obj.currency,to_currency=inr_obj,rate=rate_to_inr)

            poc_objs = [CrmPoc.objects.create(url=lead.poc.url, country=lead.poc.country, source=lead.poc.source, **dict(poc)) for poc in poc_list]
            [CrmOpportunityPocMap.objects.create(opportunity=opportunity_obj, poc=poc_obj,created_by=created_by) for poc_obj in poc_objs]
            [CrmOpportunityDepartmentMap.objects.create(opportunity=opportunity_obj, department_id=department, created_by=created_by) for department in department_list]
            [CrmOpportunityTechnologyMap.objects.create(opportunity=opportunity_obj, technology_id=technology, created_by=created_by) for technology in technology_list]
            [CrmOpportunityDomainMap.objects.create(opportunity=opportunity_obj, domain_id=domain, created_by=created_by) for domain in domain_list]
            if remarks:
                CrmOpportunityRemarks.objects.create(opportunity=opportunity_obj, remarks=remarks, created_by=created_by)

            # Document create
            if scope_of_work:
                tag = CrmDocumentTag.cmobjects.filter(name='Scope of work').first()
                CrmOpportunityDocumentTag.objects.create(opportunity=opportunity_obj, created_by=created_by, tag=tag, document=scope_of_work)

            user_list = [{'recipient': user, 'opportunity': opportunity_obj} for user in [opportunity_obj.project_lead, opportunity_obj.business_analyst] if user]
            self.send_mail_notification(user_list=user_list)

            validated_data['id'] = opportunity_obj.id
            return validated_data

    def send_mail_notification(self,user_list=list()):
        for user_data in user_list:
            """
            Mail processing.
            """
            user_mail = user_data['recipient'].cu_user.cu_alt_email_id
            mail_data = {
                'recipient_name': user_data['recipient'].get_full_name(),
                'opportunity_name': user_data['opportunity'].opportunity_name
            }
            if user_mail:
                send_mail_list('SFT-CRM-OPPASS', [user_mail], mail_data, ics='')

            """
            Notification processing.
            """
            users = [user_data['recipient']]
            title = 'Following opportunity has been assigned to you.'
            body = 'Opportunity Name: {} \nBusiness Name:{}'.format(user_data['opportunity'].opportunity_name,
                                                                    user_data['opportunity'].business_name)

            data = {
                "app_module": "sft-crm",
                "type": "opportunity",
                "id": user_data['opportunity'].id,
                'action': NOTIFICATION_ACTION['pipeline']
            }
            data_str = json.dumps(data)
            notification_id = store_sent_notification(users=users, body=body, title=title, data=data_str,
                                                      app_module_name='sft-crm')
            send_notification(users=users, body=body, title=title, data=data, notification_id=notification_id)

        return


class CrmOpportunitySnapshotListSerializer(ModelSerializer):
    lead = CrmLeadGetSerializer()
    technology = CrmTechnologySerializer(many=True)
    probability = SerializerMethodField()
    stage_name = CharField(source='get_stage_display')
    engagement_name = CharField(source='get_engagement_display')
    currency = CrmCurrencySerializer()
    latest_remarks = SerializerMethodField()
    remarks = SerializerMethodField()
    prospecting_member_name = SerializerMethodField()
    sales_manager_name = SerializerMethodField()
    lead_date = SerializerMethodField()
    technologies = SerializerMethodField()
    source_name = SerializerMethodField()

    class Meta:
        model = CrmOpportunity
        fields = ('id', 'lead', 'technology', 'probability', 'stage', 'stage_name', 'engagement', 'engagement_name',
                  'latest_remarks', 'remarks', 'currency','prospecting_member_name', 'sales_manager_name', 'lead_date',
                  'source_name', 'technologies', 'business_name', 'opportunity_name', 'value', 'man_hours',
                  'proposal_requested_at')

    def get_source_name(self, obj):
        return obj.lead.poc.source.name if obj.lead.poc.source else ''

    def get_technologies(self, obj):
        # technology_ids = CrmOpportunityTechnologyMap.cmobjects.filter(opportunity=obj).values_list('technology_id', flat=True)
        # return ', '.join(list(CrmTechnology.cmobjects.filter(id__in=technology_ids).values_list('name', flat=True)))
        return ', '.join(list(obj.technology.values_list('name', flat=True)))

    def get_lead_date(self, obj):
        return obj.lead.created_at.strftime('%d/%m/%y')

    def get_prospecting_member_name(self, obj):
        return obj.lead.assign_to.get_full_name() if obj.lead.assign_to else obj.lead.created_by.get_full_name()

    def get_sales_manager_name(self, obj):
        prospecting_member = obj.lead.assign_to if obj.lead.assign_to else obj.lead.created_by
        tcore_user = TCoreUserDetail.objects.get(cu_user=prospecting_member)
        return obj.lead.assign_from.get_full_name() if obj.lead.assign_from else tcore_user.reporting_head.get_full_name()

    def get_probability(self, obj):
        return get_opportunity_probability(stage=obj.stage)

    def get_remarks(self, obj):
        return CrmOpportunityRemarks.cmobjects.filter(opportunity=obj).values('id', 'opportunity', 'remarks', 'created_by__first_name', 'created_by__last_name','created_at')

    def get_latest_remarks(self, obj):
        return CrmOpportunityRemarks.cmobjects.filter(opportunity=obj).order_by('-id').first().remarks if CrmOpportunityRemarks.cmobjects.filter(opportunity=obj).order_by('-id').first() else ''


class CrmOpportunityListGroupByStageSerializer(ModelSerializer):
    lead = CrmLeadSerializer()
    technology = CrmTechnologySerializer()
    task = SerializerMethodField()
    poc = CrmPocSerializer(many=True)
    currency = CrmCurrencySerializer()
    is_any_overdue_task = SerializerMethodField()
    business_analyst_name = SerializerMethodField()
    updated_by_name = SerializerMethodField()
    created_by_name = SerializerMethodField()

    turnaround_time_of_assessment = SerializerMethodField()
    is_assessment_request_accepted = SerializerMethodField()
    turnaround_time_of_agreement = SerializerMethodField()
    is_agreement_request_accepted = SerializerMethodField()
    is_agreement_requested = SerializerMethodField()
    is_agreement_uploaded = SerializerMethodField()
    agreement_status = SerializerMethodField()
    agreement_status_id = SerializerMethodField()

    agreement_request = SerializerMethodField()
    assessment_request = SerializerMethodField()

    total_man_hours = SerializerMethodField()

    class Meta:
        model = CrmOpportunity
        fields = '__all__'
        extra_fields = ('is_any_overdue_task', 'business_analyst_name', 'updated_by_name', 'turnaround_time_of_assessment',
                        'total_man_hours', 'is_assessment_request_accepted', 'turnaround_time_of_agreement',
                        'is_agreement_request_accepted', 'is_agreement_requested', 'is_agreement_uploaded',
                        'agreement_status', 'agreement_status_id', 'agreement_request', 'assessment_request',
                        'created_by_name')

    def get_assessment_request(self, obj):
        request_handler = CrmRequestHandler.cmobjects.filter(request_against_id=obj.id, request_against=2,
                        request_type=1).order_by('-id').first()
        request_handler_serializer = CrmRequestHandlerSerializer(request_handler, many=False)
        return request_handler_serializer.data if request_handler else None

    def get_agreement_request(self, obj):
        request_handler = CrmRequestHandler.cmobjects.filter(request_against_id=obj.id, request_against=2,
                        request_type=2).order_by('-id').first()
        request_handler_serializer = CrmRequestHandlerSerializer(request_handler, many=False)
        return request_handler_serializer.data if request_handler else None

    def get_agreement_status_id(self, obj):
        agreement_status = CrmRequestHandler.cmobjects.filter(request_against_id=obj.id, request_against=2,
                        request_type=2).order_by('-id').first()
        return agreement_status.status if agreement_status else None

    def get_agreement_status(self, obj):
        agreement_status = CrmRequestHandler.cmobjects.filter(request_against_id=obj.id, request_against=2,
                        request_type=2).order_by('-id').first()
        status = ''
        if agreement_status and agreement_status.status == 1:
            status = 'Awaited'
        elif agreement_status and agreement_status.status == 2:
            status = 'In progress'
        elif agreement_status and agreement_status.status == 3:
            status = 'Complete'
        return status

    def get_is_agreement_uploaded(self, obj):
        crm_opp_doc = CrmOpportunityDocumentTag.cmobjects.filter(opportunity=obj, tag__name='Agreement').first()
        return True if crm_opp_doc else False

    def get_total_man_hours(self, obj):
        total_effort = CrmOpportunityResourceManagement.cmobjects.filter(opportunity=obj).annotate(
            effort=F('man_hours') * F('resource_no')).aggregate(
            sum=Sum('effort')).get('sum')
        return round(total_effort,2) if total_effort else 0.0

    def get_is_agreement_requested(self, obj):
        agreement_request = CrmRequestHandler.cmobjects.filter(request_against_id=obj.id, request_against=2,
                        request_type=2, status=1).order_by('-id').first()
        return True if agreement_request and agreement_request.status == 1 else False

    def get_is_agreement_request_accepted(self, obj):
        agreement_request = CrmRequestHandler.cmobjects.filter(request_against_id=obj.id, request_against=2,
                        request_type=2).order_by('-id').first()
        return  True if agreement_request and agreement_request.status == 2 else False

    def get_turnaround_time_of_agreement(self, obj):
        current_date = datetime.now()
        agreement_request = CrmRequestHandler.cmobjects.filter(request_against_id=obj.id, request_against=2,
                        request_type=2, status=2).order_by('-id').first()
        current_turnaround_days = 0
        if agreement_request:
            current_turnaround_days = agreement_request.turnaround_time - (current_date.date() - agreement_request.request_accepted_date.date()).days
        return current_turnaround_days

    def get_is_assessment_request_accepted(self, obj):
        assessment_request = CrmRequestHandler.cmobjects.filter(request_against_id=obj.id, request_against=2,
                            request_type=1).order_by('-id').first()
        return  True if assessment_request and assessment_request.status == 2 else False

    def get_turnaround_time_of_assessment(self, obj):
        current_date = datetime.now()
        assessment_request = CrmRequestHandler.cmobjects.filter(request_against_id=obj.id, request_against=2,
                            request_type=1, status=2).order_by('-id').first()
        current_turnaround_days = 0
        if assessment_request:
            current_turnaround_days = assessment_request.turnaround_time - (current_date.date() - assessment_request.request_accepted_date.date()).days
        return current_turnaround_days

    def get_updated_by_name(self, obj):
        return obj.updated_by.get_full_name() if obj.updated_by else ''

    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else ''

    def get_business_analyst_name(self, obj):
        return obj.business_analyst.get_full_name() if obj.business_analyst else ''

    def get_task(self, obj):
        return obj.task.filter(is_deleted=False,is_completed=False).values('id','name','date_time','remarks')

    def get_is_any_overdue_task(self, obj):
        current_date = datetime.now().date()
        return obj.task.filter(date_time__date__lt=current_date).count()>0


class CrmCheckIfProjectFormOpenSerializer(ModelSerializer):

    class Meta:
        model = CrmOpportunity
        fields = ('id', 'is_project_form_open')


class CrmUserListByTypeSerializer(ModelSerializer):
    type_name = CharField(source='get_type_display')
    user = CrmUserSerializer()
    assigned_opportunities = SerializerMethodField()

    class Meta:
        model = CrmUserTypeMap
        fields = ('type', 'user', 'type_name', 'assigned_opportunities')

    def get_assigned_opportunities(self, obj):
        count = 0
        if obj.type == 2:
            count = CrmOpportunity.cmobjects.filter(business_analyst=obj.user).count()
        elif obj.type == 3:
            count = CrmOpportunity.cmobjects.filter(project_lead=obj.user).count()
        return count


class CrmUserListByRoleModuleSerializer(ModelSerializer):
    type = SerializerMethodField()
    type_name = SerializerMethodField()
    user = SerializerMethodField()
    assigned_opportunities = SerializerMethodField()

    class Meta:
        model = TMasterModuleRoleUser
        fields = ('type', 'user', 'type_name', 'assigned_opportunities')

    def get_user(self, obj):
        return CrmUserSerializer(obj.mmr_user).data

    def get_type(self, obj):
        return USER_TYPE[obj.mmr_role.cr_name]

    def get_type_name(self, obj):
        return obj.mmr_role.cr_name

    def get_assigned_opportunities(self, obj):
        count = 0
        if obj.mmr_role.cr_name == 'Business Analyst':
            count = CrmOpportunity.cmobjects.filter(business_analyst=obj.mmr_user).count()
        elif obj.mmr_role.cr_name == 'Project Lead':
            count = CrmOpportunity.cmobjects.filter(project_lead=obj.mmr_user).count()
        return count


class CrmUsersUnderReportingHeadSerializer(ModelSerializer):

    class Meta:
        model = User
        fields=('id','first_name','last_name')


class CrmOpportunityPresaleUpdateSerializer(ModelSerializer):
    updated_by = CharField(default=CurrentUserDefault())
    department = ListField(required=False)

    class Meta:
        model = CrmOpportunity
        fields = ('updated_by', 'stage', 'status', 'department', 'project_lead', 'business_analyst', 'scope_of_work')

    def update(self, instance, validated_data):
        with transaction.atomic():
            print(validated_data)
            current_datetime = datetime.now()
            login_user = self.context['request'].user
            updated_by = validated_data.get('updated_by', login_user)
            stage = validated_data.get('stage')
            status = validated_data.get('status')

            # Opportunity stage change
            if stage and instance.stage != stage:
                departments = validated_data.pop('department')
                project_lead = validated_data.pop('project_lead')
                business_analyst = validated_data.pop('business_analyst')
                scope_of_work = validated_data.pop('scope_of_work')
                # department_list = list(map(int,departments.split(',')))
                department_list = departments

                # opportunity presale update
                if instance.stage == 1 and stage == 2:
                    self.presale_update(instance=instance, project_lead=project_lead, business_analyst=business_analyst,
                                        scope_of_work=scope_of_work, updated_by=updated_by, department_list=department_list)

                print('updated_by', updated_by)
                # creating the opportunity stage change log
                CrmOpportunityStageChangesLog.objects.create(opportunity=instance, previous_stage=instance.stage,
                                                             current_stage=stage, changed_by=updated_by)

                # saving the opportunity instance
                instance.stage = stage
                instance.updated_by = updated_by
                instance.save()

            return validated_data

    def presale_update(self, instance=None, project_lead=None, business_analyst=None, scope_of_work=None, updated_by=None, department_list=[]):
        # creating the opportunity presale log
        opportunity_presale_log_obj = CrmOpportunityPresaleLog.objects.create(opportunity=instance,
            project_lead=project_lead, business_analyst=business_analyst, scope_of_work=scope_of_work)

        [CrmOpportunityPresaleLogDepartmentMap.objects.create(opportunity_presale_log=opportunity_presale_log_obj,
            department_id=department, created_by=updated_by) for department in department_list]

        # updating the opportunity instance
        instance.project_lead = project_lead
        instance.business_analyst = business_analyst
        instance.scope_of_work = scope_of_work
        instance.save()

        existing_department = list(instance.department.filter(is_deleted=False).values_list('id',flat=True))
        print('existing_department', existing_department)

        new_department_list = list(set(department_list) - set(existing_department))
        print('new_department_list', new_department_list)

        deleted_department_list = list(set(existing_department) - set(department_list))
        print('deleted_department_list', deleted_department_list)

        instance.department.filter(id__in=deleted_department_list,is_deleted=False).update(is_deleted=False)
        [CrmOpportunityDepartmentMap.objects.create(opportunity=instance, department_id=department,
            created_by=updated_by) for department in new_department_list]
        return


class CrmOpportunityProposalUpdateSerializer(ModelSerializer):
    updated_by = CharField(default=CurrentUserDefault())
    resource = ListField(required=False)
    document = ListField(required=False)

    class Meta:
        model = CrmOpportunity
        fields = ('updated_by', 'document', 'resource', 'resource_timeline')

    def update(self, instance, validated_data):
        with transaction.atomic():
            print(validated_data)
            current_date = datetime.now()
            login_user = self.context['request'].user
            updated_by = validated_data.get('updated_by', login_user)
            document = validated_data.get('document')
            resource = validated_data.get('resource')
            resource_timeline = validated_data.get('resource_timeline')

            CrmOpportunityResourceManagement.cmobjects.filter(opportunity=instance).update(is_deleted=True, updated_by=updated_by)
            [CrmOpportunityResourceManagement.objects.create(opportunity=instance, created_by=updated_by, **res) for res in resource]

            # CrmOpportunityDocumentTag.cmobjects.filter(opportunity=instance).update(is_deleted=True, updated_by=updated_by)
            [CrmOpportunityDocumentTag.objects.create(opportunity=instance, created_by=updated_by, **doc) for doc in document]

            instance.resource_timeline = resource_timeline
            instance.stage = 3
            instance.proposal_requested_at = current_date
            instance.updated_by = updated_by
            instance.save()
            CrmOpportunityStageChangesLog.objects.create(opportunity=instance, previous_stage=2, current_stage=3,
                                                         changed_by=updated_by, created_by=updated_by)
            return validated_data


class CrmOpportunityAgreementUploadSerializer(ModelSerializer):
    updated_by = CharField(default=CurrentUserDefault())
    document = IntegerField(required=False)

    class Meta:
        model = CrmOpportunity
        fields = ('updated_by', 'document', )

    def update(self, instance, validated_data):
        with transaction.atomic():
            print(validated_data)
            login_user = self.context['request'].user
            updated_by = validated_data.get('updated_by', login_user)
            document = validated_data.get('document')
            tag = CrmDocumentTag.cmobjects.filter(name='Agreement').first()
            CrmOpportunityDocumentTag.objects.create(opportunity=instance, created_by=updated_by, document_id=document, tag=tag)
            return validated_data


class CrmOpportunityUpdateSerializer(ModelSerializer):
    updated_by = CharField(default=CurrentUserDefault())
    poc = CrmPocSerializer(many=True, required=False)
    department = ListField(required=False)
    technology = ListField(required=False)
    domain = ListField(required=False)
    remarks = CharField(required=False, allow_blank=True)
    documents = ListField(required=False)

    class Meta:
        model = CrmOpportunity
        fields = ('territory', 'country', 'business_name', 'account_manager', 'project_lead', 'business_analyst',
                  'cin', 'pan', 'gstin', 'opportunity_name', 'opportunity_date', 'expected_closer_date',
                  'engagement', 'domain', 'department', 'technology', 'man_hours', 'value', 'currency',
                  'mode_of_payment', 'poc', 'updated_by', 'remarks', 'scope_of_work', 'documents')

    def update(self, instance, validated_data):
        with transaction.atomic():
            """
                Never use instance.save(). If you do, queryset.update(**validated_data) will not work properly.
            """
            login_user = self.context['request'].user
            updated_by = validated_data.get('updated_by', login_user)
            value = validated_data.get('value')
            currency = validated_data.get('currency')

            poc_list = validated_data.pop('poc')
            department_list = validated_data.pop('department')
            technology_list = validated_data.pop('technology')
            domain_list = validated_data.pop('domain')
            remarks = validated_data.pop('remarks')
            documents = validated_data.pop('documents')

            # Opportunity Update
            opportunity_queryset = CrmOpportunity.cmobjects.filter(id=instance.id)
            opportunity_queryset.update(**validated_data)

            if instance.value != value or instance.currency != currency:
                rate_to_inr = realtime_exchange_rate(from_currency=currency.code)
                opportunity_queryset.update(conversion_rate_to_inr=rate_to_inr)
                inr_obj = TCoreCurrency.objects.get(code='INR')
                CrmCurrencyConversionHistory.objects.create(from_currency=currency, to_currency=inr_obj, rate=rate_to_inr)

            # POC update
            instance.poc.clear()
            poc_objs = [CrmPoc.objects.create(url=instance.lead.poc.url, country=instance.lead.poc.country, source=instance.lead.poc.source, **dict(poc)) for poc in poc_list]
            [CrmOpportunityPocMap.objects.create(opportunity=instance, poc=poc_obj, created_by=updated_by) for poc_obj in poc_objs]
            # [opportunity_queryset.update(lead__poc=poc) for poc in poc_objs if poc.is_primary]


            # Department Update
            hard_update_mapping(CrmOpportunityDepartmentMap,updated_ids=department_list,
                                existed_dict={'opportunity':instance},existed_query_str='department')

            # Technology Update
            hard_update_mapping(CrmOpportunityTechnologyMap,updated_ids=technology_list,
                                existed_dict={'opportunity':instance},existed_query_str='technology')

            # Domain Update
            hard_update_mapping(CrmOpportunityDomainMap, updated_ids=domain_list,
                                existed_dict={'opportunity': instance}, existed_query_str='domain')
            if remarks:
                CrmOpportunityRemarks.objects.create(opportunity=instance, remarks=remarks, created_by=updated_by)

            # Document upload
            [CrmOpportunityDocumentTag.objects.create(opportunity=instance, created_by=updated_by, **doc) for doc in documents]

            # Action Log
            log(la=2, lai=instance.id, l='This opportunity has been updated.', cb=updated_by)

            return validated_data


class CrmOpportunityBAUpdateSerializer(ModelSerializer):
    updated_by = CharField(default=CurrentUserDefault())

    class Meta:
        model = CrmOpportunity
        fields = ('updated_by', 'business_analyst')

    def update(self, instance, validated_data):
        with transaction.atomic():
            login_user = self.context['request'].user
            updated_by = validated_data.get('updated_by', login_user)
            business_analyst = validated_data.get('business_analyst')
            CrmOpportunityBAChangeLog.objects.create(opportunity=instance, pre_assign_ba=instance.business_analyst,
                                                     re_assign_ba=business_analyst,created_by=updated_by)
            # Opportunity Update
            instance.business_analyst = business_analyst
            instance.updated_by = updated_by
            instance.save()

            user_list = [{'recipient': instance.business_analyst, 'opportunity': instance}]
            self.send_mail_notification(user_list=user_list)

            return validated_data

    def send_mail_notification(self,user_list=list()):
        for user_data in user_list:
            """
            Mail processing.
            """
            user_mail = user_data['recipient'].cu_user.cu_alt_email_id
            mail_data = {
                'recipient_name': user_data['recipient'].get_full_name(),
                'opportunity_name': user_data['opportunity'].opportunity_name
            }
            if user_mail:
                send_mail_list('SFT-CRM-OPPASS', [user_mail], mail_data, ics='')

            """
            Notification processing.
            """
            users = [user_data['recipient']]
            title = 'Following opportunity has been assigned to you.'
            body = 'Opportunity Name: {} \nBusiness Name:{}'.format(user_data['opportunity'].opportunity_name,
                                                                    user_data['opportunity'].business_name)

            data = {
                "app_module": "sft-crm",
                "type": "opportunity",
                "id": user_data['opportunity'].id,
                'action': NOTIFICATION_ACTION['pipeline']
            }
            data_str = json.dumps(data)
            notification_id = store_sent_notification(users=users, body=body, title=title, data=data_str,
                                                      app_module_name='sft-crm')
            send_notification(users=users, body=body, title=title, data=data, notification_id=notification_id)

        return


class CrmOpportunityHourConsumeUpdateSerializer(ModelSerializer):
    updated_by = CharField(default=CurrentUserDefault())

    class Meta:
        model = CrmOpportunity
        fields = ('updated_by', 'resource_hour_consumed')

    def update(self, instance, validated_data):
        with transaction.atomic():
            login_user = self.context['request'].user
            updated_by = validated_data.get('updated_by', login_user)
            resource_hour_consumed = validated_data.get('resource_hour_consumed')
            # Opportunity Update
            instance.resource_hour_consumed = resource_hour_consumed
            instance.updated_by = updated_by
            instance.save()
            return validated_data


class CrmOpportunityDocumentDeleteRetrieveSerializer(ModelSerializer):
    updated_by = CharField(default=CurrentUserDefault())

    class Meta:
        model = CrmOpportunityDocumentTag
        fields = ('updated_by', 'is_disabled')

    def update(self, instance, validated_data):
        with transaction.atomic():
            login_user = self.context['request'].user
            updated_by = validated_data.get('updated_by', login_user)
            is_disabled = validated_data.get('is_disabled')

            # Opportunity Document Update
            instance.is_disabled = is_disabled
            instance.updated_by = updated_by
            instance.save()
            return validated_data


class CrmRequestCreateSerializer(ModelSerializer):
    updated_by = CharField(default=CurrentUserDefault())
    # request_type = IntegerField(required=False)

    class Meta:
        model = CrmRequestHandler
        fields = ('updated_by', 'request_type', 'request_against', 'request_against_id')

    def create(self, validated_data):
        with transaction.atomic():
            login_user = self.context['request'].user
            updated_by = validated_data.get('updated_by', login_user)
            request_type = validated_data.get('request_type')
            request_against = validated_data.get('request_against')
            request_against_id = validated_data.get('request_against_id')

            request_handler = CrmRequestHandler.objects.filter(request_against=request_against,
                                request_against_id=request_against_id, request_type=request_type, status=1).count()
            if not request_handler:
                CrmRequestHandler.objects.create(request_against=request_against, request_against_id=request_against_id,
                                request_type=request_type, status=1, created_by=updated_by)

            return validated_data


class CrmRequestAcceptSerializer(ModelSerializer):
    updated_by = CharField(default=CurrentUserDefault())
    # turnaround_time = IntegerField(required=False)
    # request_type = IntegerField(required=False)

    class Meta:
        model = CrmRequestHandler
        fields = ('updated_by', 'turnaround_time',)

    def update(self, instance, validated_data):
        with transaction.atomic():
            print(validated_data)
            current_date = datetime.now()
            login_user = self.context['request'].user
            updated_by = validated_data.get('updated_by', login_user)
            turnaround_time = validated_data.get('turnaround_time')

            instance.status = 2
            instance.turnaround_time = turnaround_time
            instance.request_accepted_date = current_date
            instance.updated_by = updated_by
            instance.save()


            # opportunity_request =CrmOpportunityRequestHandler.objects.filter(opportunity=instance, request_type=request_type,
            #     status=1)
            #
            # if opportunity_request.count():
            #     opportunity_request.update(status=2, updated_by=updated_by,
            #                     turnaround_time=turnaround_time, request_accepted_date=current_date)
            # else:
            #     CrmOpportunityRequestHandler.objects.create(opportunity=instance, request_type=request_type,
            #             turnaround_time=turnaround_time, request_accepted_date=current_date, updated_by=updated_by,
            #             status=2)

            return validated_data


class CrmRequestCompleteSerializer(ModelSerializer):
    updated_by = CharField(default=CurrentUserDefault())
    # request_type = IntegerField(required=False)

    class Meta:
        model = CrmRequestHandler
        fields = ('updated_by', )

    def update(self, instance, validated_data):
        with transaction.atomic():
            print(validated_data)
            login_user = self.context['request'].user
            updated_by = validated_data.get('updated_by', login_user)

            instance.status = 3
            instance.updated_by = updated_by
            instance.save()


            # opportunity_request =CrmOpportunityRequestHandler.objects.filter(opportunity=instance, request_type=request_type,
            #     status=2)
            #
            # if opportunity_request.count():
            #     opportunity_request.update(status=3, updated_by=updated_by)
            # else:
            #     CrmOpportunityRequestHandler.objects.create(opportunity=instance, request_type=request_type,
            #             updated_by=updated_by, status=3)

            return validated_data


class CrmOpportunityColorStatusUpdateSerializer(ModelSerializer):
    updated_by = CharField(default=CurrentUserDefault())
    remarks = CharField(required=False, allow_blank=True)

    class Meta:
        model = CrmOpportunity
        fields = ('updated_by', 'color_status', 'remarks')

    def update(self, instance, validated_data):
        with transaction.atomic():
            login_user = self.context['request'].user
            updated_by = validated_data.get('updated_by', login_user)
            color_status = validated_data.get('color_status')
            remarks = validated_data.get('remarks')
            if remarks:
                CrmOpportunityRemarks.objects.create(opportunity=instance, remarks=remarks,
                                                     is_color_remarks=True,created_by=updated_by)
            # Opportunity Update
            instance.color_status = color_status
            instance.updated_by = updated_by
            instance.save()
            # Action Log
            msg = 'The RAG status of this opportunity has been changed to {}.'.format(instance.get_color_status_display())
            log(la=2, lai=instance.id, l=msg, cb=updated_by)

            return validated_data


class CrmOpportunityTagUpdateSerializer(ModelSerializer):
    updated_by = CharField(default=CurrentUserDefault())
    department = ListField(required=False)
    technology = ListField(required=False)

    class Meta:
        model = CrmOpportunity
        fields = ('updated_by', 'engagement', 'department', 'technology')

    def update(self, instance, validated_data):
        with transaction.atomic():
            login_user = self.context['request'].user
            updated_by = validated_data.get('updated_by', login_user)
            engagement = validated_data.get('engagement', instance.engagement)
            department = validated_data.get('department')
            technology = validated_data.get('technology')

            # Department Update
            if department:
                hard_update_mapping(CrmOpportunityDepartmentMap,updated_ids=department,
                                existed_dict={'opportunity':instance},existed_query_str='department')

            # Technology Update
            if technology:
                hard_update_mapping(CrmOpportunityTechnologyMap,updated_ids=technology,
                                existed_dict={'opportunity':instance},existed_query_str='technology')

            # Opportunity Update
            instance.engagement = engagement
            instance.updated_by = updated_by
            instance.save()
            return validated_data


class CrmOpportunityFileUploadSerializer(ModelSerializer):
    updated_by = CharField(default=CurrentUserDefault())
    poc = CrmPocSerializer(many=True, required=False)
    department = CharField(required=False)
    technology = ListField(required=False)
    domain = ListField(required=False)
    milestone = CrmMilestoneSerializer(many=True, required=False)
    task = CrmTaskSerializer(many=True, required=False)
    lead = CrmLeadSerializer(required=False)

    class Meta:
        model = CrmOpportunity
        fields = '__all__'

    def update(self, instance, validated_data):
        with transaction.atomic():
            login_user = self.context['request'].user
            updated_by = validated_data.get('updated_by', login_user)
            scope_of_work = validated_data.get('scope_of_work')

            instance.scope_of_work = scope_of_work
            instance.updated_by = updated_by
            instance.save()

            return validated_data


class CrmOpportunityStageStatusUpdateSerializer(ModelSerializer):
    updated_by = CharField(default=CurrentUserDefault())

    class Meta:
        model = CrmOpportunity
        fields = ('updated_by', 'stage', 'status', 'lost_reason', 'lost_remarks')

    def update(self, instance, validated_data):
        with transaction.atomic():
            current_datetime = datetime.now()
            login_user = self.context['request'].user
            updated_by = validated_data.get('updated_by', login_user)
            stage = validated_data.get('stage')
            status = validated_data.get('status')
            print('updated_by', updated_by)

            # Opportunity stage change
            if stage and instance.stage != stage:
                # creating the opportunity stage change log
                CrmOpportunityStageChangesLog.objects.create(opportunity=instance, previous_stage=instance.stage,
                                                             current_stage=stage, changed_by=updated_by)

                # saving the opportunity instance
                instance.stage = stage
                instance.updated_by = updated_by
                instance.save()

                # Action Log
                msg = 'The stage this opportunity has been changed to {}.'.format(instance.get_stage_display())
                log(la=2, lai=instance.id, l=msg, cb=updated_by)

            if status and instance.status != status:
                lost_reason = validated_data.pop('lost_reason')
                lost_remarks = validated_data.pop('lost_remarks')

                if not instance.status and status == 2:
                    instance.lost_reason = lost_reason
                    instance.lost_remarks = lost_remarks
                instance.status = status
                instance.status_update_at = current_datetime
                instance.updated_by = updated_by
                instance.status_updated_by = updated_by
                instance.save()
            print('instance.status_updated_by',instance.status_updated_by)
            return validated_data


class CrmProjectFormOpenOrCancelSerializer(ModelSerializer):
    updated_by = CharField(default=CurrentUserDefault())

    class Meta:
        model = CrmOpportunity
        fields = ('updated_by', 'is_project_form_open')

    def update(self, instance, validated_data):
        with transaction.atomic():
            login_user = self.context['request'].user
            updated_by = validated_data.get('updated_by', login_user)
            is_project_form_open = validated_data.get('is_project_form_open')
            print(validated_data)
            # saving the opportunity instance
            instance.is_project_form_open = is_project_form_open
            instance.project_form_opened_by = updated_by
            instance.updated_by = updated_by
            instance.save()

            # Project form log
            if is_project_form_open:
                CrmProjectFormLog.objects.create(opportunity=instance, created_by=updated_by)
            else:
                project_from_log = CrmProjectFormLog.objects.filter(opportunity=instance, is_open=True).order_by('-id').first()
                if project_from_log:
                    project_from_log.is_open = False
                    project_from_log.updated_by = updated_by
                    project_from_log.save()

            if not is_project_form_open:
                recipient_list = get_users_by_type(type='Sales Manager') if get_user_type(user=instance.project_form_opened_by) == 4 else []
                # if get_user_type(user=instance.project_form_opened_by) == 4:
                #     recipient_list.extend(get_users_by_type(type='Sales Manager'))
                # elif get_user_type(user=instance.project_form_opened_by) == 1:
                #     recipient = instance.assign_to if instance.assign_to else instance.created_by
                #     recipient_list.append(recipient)
                user_list = [{'recipient': user, 'opportunity': instance} for user in recipient_list]
                self.send_mail_notification(user_list=user_list)
            return validated_data

    def send_mail_notification(self,user_list=list()):
        for user_data in user_list:
            """
            Mail processing.
            """
            user_mail = user_data['recipient'].cu_user.cu_alt_email_id
            mail_data = {
                'recipient_name': user_data['recipient'].get_full_name(),
                'opportunity_name': user_data['opportunity'].opportunity_name
            }
            if user_mail:
                send_mail_list('SFT-CRM-PROJCNL', [user_mail], mail_data, ics='')

            """
            Notification processing.
            """
            users = [user_data['recipient']]
            title = 'The project from of the following opportunity has been cancel.'
            body = 'Opportunity Name: {} \nBusiness Name:{}'.format(user_data['opportunity'].opportunity_name,
                    user_data['opportunity'].business_name)

            data = {
                "app_module": "sft-crm",
                "type": "opportunity",
                "id": user_data['opportunity'].id,
                'action': NOTIFICATION_ACTION['pipeline']
            }
            data_str = json.dumps(data)
            notification_id = store_sent_notification(users=users, body=body, title=title, data=data_str,
                                                      app_module_name='sft-crm')
            send_notification(users=users, body=body, title=title, data=data, notification_id=notification_id)

        return


class CrmAddTaskToOpportunitySerializer(ModelSerializer):
    created_by = CharField(default=CurrentUserDefault())
    task = CrmTaskSerializer()

    class Meta:
        model = CrmOpportunity
        fields = ('task', 'created_by')

    def update(self, instance, validated_data):
        with transaction.atomic():
            created_by = validated_data.get('created_by')
            task_obj = CrmTask.objects.create(
                    created_by=created_by,
                    **dict(validated_data['task'])
                )
            CrmOpportunityTaskMap.objects.create(opportunity=instance,task=task_obj,created_by=created_by)
            validated_data['task'] = task_obj.__dict__
            return validated_data


class CrmProjectCreateSerializer(ModelSerializer):
    created_by = CharField(default=CurrentUserDefault())
    domain = ListField(required=False)
    department = ListField(required=False)
    technology = ListField(required=False)
    milestone = CrmMilestoneSerializer(many=True, required=False)
    poc = CharField(required=False)
    business_analyst = IntegerField(required=False)
    project_manager = IntegerField(required=False)

    first_name = CharField(required=False, allow_blank=True)
    last_name = CharField(required=False, allow_blank=True)
    phone = CharField(required=False)
    email = CharField(required=False)
    job_title = CharField(required=False)
    url = CharField(required=False)
    country = CharField(required=False)
    source = CharField(required=False)

    class Meta:
        model = CrmProject
        fields = '__all__'
        extra_fields = ('first_name', 'last_name', 'phone', 'email', 'job_title', 'url', 'country', 'source')

    def create(self, validated_data):
        with transaction.atomic():
            current_datetime = datetime.now()
            created_by = validated_data.get('created_by')
            validated_data['poc'] = CrmPoc.objects.create(
                created_by=created_by,
                first_name=validated_data.pop('first_name', ''),
                last_name = validated_data.pop('last_name', ''),
                phone = validated_data.pop('phone', ''),
                email = validated_data.pop('email', ''),
                job_title = validated_data.pop('job_title', ''),
                url = validated_data.pop('url', ''),
                country_id = int(validated_data.pop('country')) if validated_data.get('country') else None,
                source_id = int(validated_data.pop('source')) if validated_data.get('source') else None
            )
            domains = validated_data.pop('domain')
            departments = validated_data.pop('department')
            technologys = validated_data.pop('technology')

            domain_list = domains
            department_list = departments
            technology_list = technologys

            validated_data['project_manager_id'] = validated_data.pop('project_manager', None)
            validated_data['business_analyst_id'] = validated_data.pop('business_analyst', None)
            project_obj = CrmProject.objects.create(**validated_data)
            project_obj.opportunity.is_project_form_open=False
            project_obj.opportunity.status = 1
            project_obj.opportunity.status_update_at = current_datetime
            project_obj.opportunity.status_updated_by = created_by
            project_obj.opportunity.save()

            # creating many to many relation
            [CrmProjectDomainMap.objects.create(project=project_obj, domain_id=domain,
                created_by=created_by) for domain in domain_list]
            [CrmProjectDepartmentMap.objects.create(project=project_obj, department_id=department,
                created_by=created_by) for department in department_list]
            [CrmProjectTechnologyMap.objects.create(project=project_obj, technology_id=technology,
                created_by=created_by) for technology in technology_list]
            recipient_list = [project_obj.project_manager, project_obj.business_analyst, *get_users_by_type(type='Sales Manager')]
            user_list = [{'recipient': user, 'project': project_obj} for user in recipient_list if user]
            self.send_mail_notification(user_list=user_list)
            return validated_data

    def send_mail_notification(self,user_list=list()):
        for user_data in user_list:
            """
            Mail processing.
            """
            user_mail = user_data['recipient'].cu_user.cu_alt_email_id
            mail_data = {
                'recipient_name': user_data['recipient'].get_full_name(),
                'project_name': user_data['project'].opportunity.opportunity_name,
                'project_id': PROJECT_ID.format(user_data['project'].id)
            }
            if user_mail:
                send_mail_list('SFT-CRM-PROJCRT', [user_mail], mail_data, ics='')

            """
            Notification processing.
            """
            users = [user_data['recipient']]
            title = 'Following project has been created.'
            body = 'Project Name: {} \nAccount Name:{} \nDescription:{}'.format(
                user_data['project'].opportunity.opportunity_name, user_data['project'].account_name,
                user_data['project'].description)

            data = {
                "app_module": "sft-crm",
                "type": "project",
                "id": user_data['project'].id,
                'action': NOTIFICATION_ACTION['close_won']
            }
            data_str = json.dumps(data)
            notification_id = store_sent_notification(users=users, body=body, title=title, data=data_str,
                                                      app_module_name='sft-crm')
            send_notification(users=users, body=body, title=title, data=data, notification_id=notification_id)

        return


class CrmAccountOpportunitySerializer(ModelSerializer):
    status_name = CharField(source='get_status_display')
    business_analyst = CrmUserSerializer()
    account_manager = CrmUserSerializer()
    department = CrmDepartmentSerializer(many=True)
    currency = CrmCurrencySerializer()
    color_status = CrmColorStatusSerializer()
    color_remarks = SerializerMethodField()
    latest_color_remarks = SerializerMethodField()
    change_request = CrmChangeRequestSerializer(many=True)
    documents = SerializerMethodField()

    class Meta:
        model = CrmOpportunity
        fields = ('id', 'opportunity_name', 'change_request', 'value', 'currency', 'status_name', 'business_analyst',
                  'department', 'account_manager', 'color_status', 'color_remarks', 'latest_color_remarks',
                  'documents')

    def get_documents(self, obj):
        opportunity_documents = CrmOpportunityDocumentTag.cmobjects.filter(opportunity=obj)
        document_serializer = CrmOpportunityDocumentTagSerializer(opportunity_documents, many=True, context=self.context)
        return document_serializer.data

    def get_color_remarks(self, obj):
        return CrmOpportunityRemarks.cmobjects.filter(opportunity=obj, is_color_remarks=True).values('id', 'opportunity', 'remarks', 'created_by__first_name', 'created_by__last_name','created_at')

    def get_latest_color_remarks(self, obj):
        return CrmOpportunityRemarks.cmobjects.filter(opportunity=obj, is_color_remarks=True).order_by('-id').first().remarks if CrmOpportunityRemarks.cmobjects.filter(opportunity=obj,is_color_remarks=True).order_by('-id').first() else ''


class CrmAccountListSerializer(ModelSerializer):
    opportunity = SerializerMethodField()

    class Meta:
        model = CrmLead
        fields = ('id', 'business_name', 'opportunity')

    def get_opportunity(self, obj):
        filters = dict()
        if self.context.get("crm_opp_lead__status"):
            filters['status__in'] = self.context.get("crm_opp_lead__status").split(',')

        if self.context.get("crm_opp_lead__department"):
            filters['department__in'] = self.context.get("crm_opp_lead__department").split(',')

        if self.context.get("crm_opp_lead__color_status"):
            filters['color_status__in'] = self.context.get("crm_opp_lead__color_status").split(',')

        user_type = get_user_type(user=self.context.get("login_user"))
        print(user_type)
        if user_type == 2:
            filters['business_analyst'] = self.context.get("login_user")
        elif self.context.get("crm_opp_lead__business_analyst"):
            filters['business_analyst__in'] = self.context.get("crm_opp_lead__business_analyst").split(',')

        if self.context.get("crm_opp_lead__account_manager"):
            filters['account_manager__in'] = self.context.get("crm_opp_lead__account_manager").split(',')

        serializer = CrmAccountOpportunitySerializer(obj.crm_opp_lead.filter(~Q(status=2),**filters), many=True, context=self.context)
        return serializer.data


class CrmAddPocToOpportunitySerializer(ModelSerializer):
    created_by = CharField(default=CurrentUserDefault())
    poc = CrmPocSerializer()

    class Meta:
        model = CrmOpportunity
        fields = ('created_by', 'poc',)

    def update(self, instance, validated_data):
        with transaction.atomic():
            created_by = validated_data.get('created_by')
            poc_obj = CrmPoc.objects.create(
                    created_by=created_by,
                    url=instance.lead.poc.url,
                    country=instance.lead.poc.country,
                    source=instance.lead.poc.source,
                    **dict(validated_data['poc'])
                )
            CrmOpportunityPocMap.objects.create(opportunity=instance,poc=poc_obj,created_by=created_by)
            return validated_data


class CrmAddMilestoneToOpportunitySerializer(ModelSerializer):
    created_by = CharField(default=CurrentUserDefault())
    milestone = CrmMilestoneSerializer(many=True)

    class Meta:
        model = CrmOpportunity
        fields = ('created_by', 'milestone',)

    def update(self, instance, validated_data):
        with transaction.atomic():
            created_by = validated_data.get('created_by')
            milestone_list = validated_data.get('milestone')
            milestone_objs = [CrmMilestone.objects.create(**dict(milestone)) for milestone in milestone_list]
            [CrmOpportunityMilestoneMap.objects.create(opportunity=instance, milestone=milestone_obj, created_by=created_by) for milestone_obj in milestone_objs]
            return validated_data


class CrmMilestoneUpdateSerializer(ModelSerializer):
    id = IntegerField(required=False)

    class Meta:
        model = CrmMilestone
        fields = '__all__'


class CrmUpdateMilestoneInOpportunitySerializer(ModelSerializer):
    updated_by = CharField(default=CurrentUserDefault())
    milestone = CrmMilestoneUpdateSerializer(many=True)

    class Meta:
        model = CrmOpportunity
        fields = ('updated_by', 'milestone',)

    def update(self, instance, validated_data):
        with transaction.atomic():
            updated_by = validated_data.get('updated_by')
            milestone_list = validated_data.get('milestone')

            [CrmMilestone.objects.filter(id=milestone.get('id')).update(**dict(milestone),updated_by=updated_by) for milestone in milestone_list if dict(milestone).get('id')]
            milestone_objs = [CrmMilestone.objects.create(**dict(milestone)) for milestone in milestone_list if not dict(milestone).get('id')]
            [CrmOpportunityMilestoneMap.objects.create(opportunity=instance, milestone=milestone_obj, created_by=updated_by) for milestone_obj in milestone_objs]
            return validated_data


class CrmDeleteMilestoneFromOpportunitySerializer(ModelSerializer):
    updated_by = CharField(default=CurrentUserDefault())
    milestone = IntegerField()

    class Meta:
        model = CrmOpportunity
        fields = ('updated_by', 'milestone',)

    def update(self, instance, validated_data):
        with transaction.atomic():
            updated_by = validated_data.get('updated_by')
            milestone = validated_data.get('milestone')
            change_request_distribution = CrmOpportunityMilestoneChangeRequestDistribution.cmobjects.filter(opportunity=instance,milestone=milestone,cr_value__gt=0)
            if change_request_distribution.count():
                raise APIException({'request_status':0,'msg':'Please adjust change request distribution to delete this milestone'})
            else:
                CrmMilestone.objects.filter(id=milestone).update(is_deleted=True,updated_by=updated_by)
            return validated_data


class CrmAddChangeRequestToOpportunitySerializer(ModelSerializer):
    created_by = CharField(default=CurrentUserDefault())
    change_request = CrmChangeRequestSerializer()
    change_request_distribution = CrmOpportunityMilestoneChangeRequestDistributionSerializer(many=True)

    class Meta:
        model = CrmOpportunity
        fields = ('created_by', 'change_request', 'change_request_distribution')

    def update(self, instance, validated_data):
        with transaction.atomic():
            created_by = validated_data.get('created_by')
            change_request = validated_data.get('change_request')
            change_request_distribution_list = validated_data.get('change_request_distribution')
            change_request_obj = CrmChangeRequest.objects.create(**dict(change_request))
            # Log update
            # CrmDocument.cmobjects.filter(id=change_request_obj.cr_document.id).update(model_type=4,model_obj_id=change_request_obj.id,field_type=4,updated_by=created_by)

            CrmOpportunityChangeRequestMap.objects.create(opportunity=instance, change_request=change_request_obj, created_by=created_by)
            print(change_request_distribution_list)
            [CrmOpportunityMilestoneChangeRequestDistribution.objects.create(**dict(change_request_distribution_obj), opportunity=instance,
                    change_request=change_request_obj, created_by=created_by) for change_request_distribution_obj in change_request_distribution_list]
            return validated_data


class CrmUpdateChangeRequestInOpportunitySerializer(ModelSerializer):
    updated_by = CharField(default=CurrentUserDefault())
    change_request = CrmChangeRequestGetSerializer()
    change_request_distribution = CrmOpportunityMilestoneChangeRequestDistributionSerializer(many=True)

    class Meta:
        model = CrmOpportunity
        fields = ('updated_by', 'change_request', 'change_request_distribution')

    def update(self, instance, validated_data):
        with transaction.atomic():
            updated_by = validated_data.get('updated_by')
            change_request = validated_data.get('change_request')
            change_request_distribution_list = validated_data.get('change_request_distribution')
            change_request_query = CrmChangeRequest.objects.filter(id=dict(change_request).get('id'))
            change_request_query.update(**dict(change_request), updated_by=updated_by)
            CrmOpportunityMilestoneChangeRequestDistribution.cmobjects.filter(opportunity=instance,
                        change_request=change_request_query.first()).update(is_deleted=True, updated_by=updated_by)
            [CrmOpportunityMilestoneChangeRequestDistribution.objects.create(**dict(change_request_distribution_obj), opportunity=instance,
                        change_request=change_request_query.first(), created_by=updated_by) for change_request_distribution_obj in change_request_distribution_list]
            return validated_data


class CrmOpportunityDetailsChangeRequestDistributionSerializer(ModelSerializer):
    change_request = CrmChangeRequestSerializer()
    milestone = CrmMilestoneSerializer()

    class Meta:
        model = CrmOpportunityMilestoneChangeRequestDistribution
        fields = ('change_request', 'milestone', 'cr_value', 'cr_percentage')


class CrmChangeRequestDetailsOpportunityWiseSerializer(ModelSerializer):
    updated_by = CharField(default=CurrentUserDefault())
    change_request_distribution = SerializerMethodField()
    #cr_document = CrmDocumentSerializer()
    cr_document = SerializerMethodField()

    class Meta:
        model = CrmChangeRequest
        fields = '__all__'
        extra_fields = ('change_request_distribution', )

    def get_cr_document(self, obj):
        return CrmDocumentSerializer(obj.cr_document,many=False, context=self.context).data

    def get_change_request_distribution(self, obj):
        opportunity = int(self.context.get("opportunity"))
        change_request_distribution = CrmOpportunityMilestoneChangeRequestDistribution.cmobjects.filter(opportunity_id=opportunity, change_request=obj)
        return CrmOpportunityDetailsChangeRequestDistributionSerializer(change_request_distribution, many=True).data


class CrmOpportunityDetailsMilestoneSerializer(ModelSerializer):
    mode_of_payment_name = SerializerMethodField()

    class Meta:
        model = CrmMilestone
        fields = '__all__'
        extra_fields = ('mode_of_payment_name', )

    def get_mode_of_payment_name(self, obj):
        return obj.mode_of_payment.name if obj.mode_of_payment else ''


class CrmOpportunityDetailsResourceManagementSerializer(ModelSerializer):
    resource = CrmResourceSerializer()

    class Meta:
        model = CrmOpportunityResourceManagement
        fields = ('resource', 'man_hours', 'resource_no')


class CrmOpportunityDetailsSerializer(ModelSerializer):
    lead = CrmLeadGetSerializer()
    poc = SerializerMethodField()
    status_name = CharField(source='get_status_display')
    stage_name = CharField(source='get_stage_display')
    business_analyst = CrmUserSerializer()
    project_lead = CrmUserSerializer()

    department = CrmDepartmentSerializer(many=True)
    milestone = SerializerMethodField()
    technology = CrmTechnologySerializer(many=True)
    domain = CrmDomainSerializer(many=True)

    remarks = SerializerMethodField()
    prospecting_member_name = SerializerMethodField()
    sales_manager_name = SerializerMethodField()
    scope_of_work = SerializerMethodField()
    total_change_request_value = SerializerMethodField()
    realize_amount = SerializerMethodField()
    change_request = CrmChangeRequestSerializer(many=True)
    total_effort = SerializerMethodField()

    resource_management = SerializerMethodField()
    documents = SerializerMethodField()
    log = SerializerMethodField()
    project_form_raise_log = SerializerMethodField()

    class Meta:
        model = CrmOpportunity
        fields = '__all__'
        extra_fields = ('status_name', 'stage_name', 'remarks', 'prospecting_member_name', 'sales_manager_name',
                        'total_change_request_value', 'realize_amount', 'resource_management', 'resource_hour_consumed',
                        'total_effort', 'documents', 'log', 'project_form_raise_log')

    def get_project_form_raise_log(self, obj):
        project_form_log = CrmProjectFormLog.cmobjects.filter(opportunity=obj)
        log_serializer = CrmProjectFormLogSerializer(project_form_log, many=True)
        return log_serializer.data

    def get_log(self, obj):
        return logs(q=Q(log_against=2)&Q(log_against_id=obj.id))

    def get_documents(self, obj):
        opportunity_documents = CrmOpportunityDocumentTag.cmobjects.filter(opportunity=obj)
        document_serializer = CrmOpportunityDocumentTagSerializer(opportunity_documents, many=True, context=self.context)
        return document_serializer.data

    def get_total_effort(self, obj):
        total_effort = CrmOpportunityResourceManagement.cmobjects.filter(opportunity=obj).annotate(
            effort=F('man_hours') * F('resource_no')).aggregate(
            sum=Sum('effort')).get('sum')
        return round(total_effort,2) if total_effort else 0.0

    def get_resource_management(self, obj):
        resource_query = CrmOpportunityResourceManagement.cmobjects.filter(opportunity=obj)
        resource_serializer = CrmOpportunityDetailsResourceManagementSerializer(resource_query, many=True)
        return resource_serializer.data

    def get_realize_amount(self, obj):
        total_paid_value = get_change_request_milestone_amount(opportunity=obj, amount_type='paid')
        return total_paid_value

    def get_total_change_request_value(self, obj):
        change_request_value = obj.change_request.aggregate(
            sum=Sum('value')).get('sum')
        return round(change_request_value, 2) if change_request_value else 0

    def get_scope_of_work(self, obj):
            return CrmDocumentSerializer(obj.scope_of_work, many=False, context=self.context).data

    def get_milestone(self, obj):
        milestone_serializer = CrmOpportunityDetailsMilestoneSerializer(obj.milestone.filter(is_deleted=False), many=True)
        for data in milestone_serializer.data:
            change_request_distributions = CrmOpportunityMilestoneChangeRequestDistribution.cmobjects.filter(opportunity=obj,milestone=data['id'])
            change_request_distributions_serializer = CrmOpportunityDetailsChangeRequestDistributionSerializer(change_request_distributions, many=True)
            data['change_request'] = change_request_distributions_serializer.data
        return milestone_serializer.data

    def get_prospecting_member_name(self, obj):
        return obj.lead.assign_to.get_full_name() if obj.lead.assign_to else obj.lead.created_by.get_full_name()

    def get_sales_manager_name(self, obj):
        prospecting_member = obj.lead.assign_to if obj.lead.assign_to else obj.lead.created_by
        tcore_user = TCoreUserDetail.objects.get(cu_user=prospecting_member)
        return obj.lead.assign_from.get_full_name() if obj.lead.assign_from else tcore_user.reporting_head.get_full_name()

    def get_remarks(self, obj):
        return CrmOpportunityRemarks.cmobjects.filter(opportunity=obj).values('id', 'opportunity', 'remarks', 'created_by__first_name', 'created_by__last_name','created_at')

    def get_poc(self, obj):
        return obj.poc.filter(is_deleted=False).values()


class CrmOpportunityPocUpdatePrimarySerializer(ModelSerializer):
    updated_by = CharField(default=CurrentUserDefault())
    poc = IntegerField()

    class Meta:
        model = CrmOpportunity
        fields = ('poc', 'updated_by')

    def update(self, instance, validated_data):
        with transaction.atomic():
            updated_by = validated_data.get('updated_by')
            poc_id = validated_data.get('poc')
            instance.poc.update(is_primary=False, updated_by=updated_by)
            instance.poc.filter(id=poc_id).update(is_primary=True)
            return validated_data


class CrmCloseWonListSerializer(ModelSerializer):
    currency = CrmCurrencySerializer()
    country = CrmCountrySerializer()
    territory_name = CharField(source='get_territory_display')
    business_analyst_name = SerializerMethodField(required=False)
    project_lead_name = SerializerMethodField(required=False)
    status_updated_by_name = SerializerMethodField(required=False)
    source_name = SerializerMethodField(required=False)
    monthly_total_value = SerializerMethodField(required=False)
    project_id = SerializerMethodField(required=False)
    opp_date = SerializerMethodField()
    won_date = SerializerMethodField()
    country_name = SerializerMethodField()

    class Meta:
        model = CrmOpportunity
        fields = '__all__'
        extra_fields = ('territory_name', 'business_analyst_name', 'project_lead_name', 'source_name',
                        'status_updated_by_name', 'monthly_total_value', 'project_id', 'opp_date', 'won_date',
                        'country_name')

    def get_country_name(self, obj):
        return obj.country.name if obj.country else ''

    def get_won_date(self, obj):
        return obj.status_update_at.strftime('%d/%m/%y') if obj.status_update_at else ''

    def get_opp_date(self, obj):
        return obj.opportunity_date.strftime('%d/%m/%y') if obj.opportunity_date else ''

    def get_project_id(self, obj):
        pid = CrmProject.cmobjects.filter(opportunity=obj).first()
        return PROJECT_ID.format(pid.id) if pid else ''

    def get_monthly_total_value(self, obj):
        login_user = self.context.get("login_user")
        assigned_users = self.context.get("assigned_users")
        assigned_users = assigned_users.split(',') if assigned_users else get_users_by_type(
            type='Prospecting Team Member')

        query_by_user_type = get_query_by_user_type(login_user=login_user, assigned_users=assigned_users,
                                                    table_type='opportunity')
        query_set = CrmOpportunity.cmobjects.filter(query_by_user_type)

        total_value = 0
        if obj.status:
            total_value = query_set.filter(
                    Q(Q(status_update_at__year=obj.status_update_at.year)&Q(status_update_at__month=obj.status_update_at.month)),
                    status=1).annotate(converted_value=F('value') * F('conversion_rate_to_inr')).aggregate(
                    sum=Sum('converted_value')).get('sum')

        total_value = round(total_value, 2) if total_value else 0
        return realtime_exchange_value(from_currency='INR', to_currency=DEFAULT_CURRENCY, value=total_value)

    def get_source_name(self, obj):
        return obj.lead.poc.source.name if obj.lead.poc.source else ''

    def get_business_analyst_name(self, obj):
        return obj.business_analyst.get_full_name() if obj.business_analyst else ''

    def get_project_lead_name(self, obj):
        return obj.project_lead.get_full_name() if obj.project_lead else ''

    def get_status_updated_by_name(self, obj):
        return obj.status_updated_by.get_full_name() if obj.status_updated_by else ''


class CrmLossAnalysisListSerializer(ModelSerializer):
    currency = CrmCurrencySerializer()
    country = CrmCountrySerializer()
    territory_name = CharField(source='get_territory_display')
    business_analyst_name = SerializerMethodField(required=False)
    project_lead_name = SerializerMethodField(required=False)
    status_updated_by_name = SerializerMethodField(required=False)
    source_name = SerializerMethodField(required=False)
    monthly_total_value = SerializerMethodField(required=False)
    project_id = SerializerMethodField(required=False)
    opp_date = SerializerMethodField()
    won_date = SerializerMethodField()
    country_name = SerializerMethodField()

    class Meta:
        model = CrmOpportunity
        fields = '__all__'
        extra_fields = ('territory_name', 'business_analyst_name', 'project_lead_name', 'source_name',
                        'status_updated_by_name', 'monthly_total_value', 'project_id', 'opp_date', 'won_date',
                        'country_name')

    def get_country_name(self, obj):
        return obj.country.name if obj.country else ''

    def get_won_date(self, obj):
        return obj.status_update_at.strftime('%d/%m/%y') if obj.status_update_at else ''

    def get_opp_date(self, obj):
        return obj.opportunity_date.strftime('%d/%m/%y') if obj.opportunity_date else ''

    def get_project_id(self, obj):
        pid = CrmProject.cmobjects.filter(opportunity=obj).first()
        return PROJECT_ID.format(pid.id) if pid else ''

    def get_monthly_total_value(self, obj):
        login_user = self.context.get("login_user")
        assigned_users = self.context.get("assigned_users")
        assigned_users = assigned_users.split(',') if assigned_users else get_users_by_type(
            type='Prospecting Team Member')


        query_by_user_type = get_query_by_user_type(login_user=login_user, assigned_users=assigned_users,
                                                    table_type='opportunity')
        query_set = CrmOpportunity.cmobjects.filter(query_by_user_type)

        total_value = 0
        if obj.status:
            total_value = query_set.filter(
                    Q(Q(status_update_at__year=obj.status_update_at.year)&Q(status_update_at__month=obj.status_update_at.month)),
                    status=2).annotate(converted_value=F('value') * F('conversion_rate_to_inr')).aggregate(
                    sum=Sum('converted_value')).get('sum')
        total_value = round(total_value, 2) if total_value else 0
        return realtime_exchange_value(from_currency='INR', to_currency=DEFAULT_CURRENCY, value=total_value)

    def get_source_name(self, obj):
        return obj.lead.poc.source.name if obj.lead.poc.source else ''

    def get_business_analyst_name(self, obj):
        return obj.business_analyst.get_full_name() if obj.business_analyst else ''

    def get_project_lead_name(self, obj):
        return obj.project_lead.get_full_name() if obj.project_lead else ''

    def get_status_updated_by_name(self, obj):
        return obj.status_updated_by.get_full_name() if obj.status_updated_by else ''


class CrmAccountLeadFilterListSerializer(ModelSerializer):

    class Meta:
        model = CrmLead
        fields = ('id', 'business_name')


class CrmLeadReportListSerializer(ModelSerializer):
    poc = CrmPocGetSerializer()
    source_name = SerializerMethodField()
    country_name = SerializerMethodField()
    lead_date = SerializerMethodField()
    prospecting_member_name = SerializerMethodField()

    class Meta:
        model = CrmLead
        fields = ('business_name', 'source_name', 'poc', 'lead_date', 'prospecting_member_name', 'country_name',
                  'created_at')

    def get_source_name(self, obj):
        return obj.poc.source.name if obj.poc.source else ''

    def get_country_name(self, obj):
        return obj.poc.country.name if obj.poc.country else ''

    def get_lead_date(self, obj):
        return obj.created_at.strftime('%d/%m/%y')

    def get_prospecting_member_name(self, obj):
        return obj.assign_to.get_full_name() if obj.assign_to else obj.created_by.get_full_name()


class CrmCustomerReportListSerializer(ModelSerializer):
    account_manager_name = SerializerMethodField()
    account_manager = CrmUserSerializer()
    color_remarks = SerializerMethodField()
    latest_color_remarks = SerializerMethodField()
    active_opportunities = SerializerMethodField()
    won_opportunities = SerializerMethodField()
    total_opportunities_value = SerializerMethodField()
    won_value = SerializerMethodField()
    realized_amount = SerializerMethodField()
    invoiced_amount = SerializerMethodField()
    due_amount = SerializerMethodField()
    business_name = SerializerMethodField()
    default_currency = SerializerMethodField()

    class Meta:
        model = CrmOpportunity
        fields = ('business_name', 'account_manager_name', 'active_opportunities', 'total_opportunities_value',
                  'won_opportunities', 'won_value', 'account_manager', 'color_remarks', 'latest_color_remarks',
                  'realized_amount', 'due_amount', 'invoiced_amount', 'default_currency')

    def get_default_currency(self, obj):
        return DEFAULT_CURRENCY

    def get_account_manager_name(self, obj):
        return obj.account_manager.get_full_name() if obj.account_manager else ''

    def get_business_name(self, obj):
        return obj.lead.business_name

    def get_due_amount(self, obj):
        total_value = CrmOpportunityMilestoneMap.cmobjects.filter(opportunity__lead=obj.lead,
            milestone__is_paid=False, milestone__is_deleted=False).annotate(
            converted_value=F('milestone__value') * F('opportunity__conversion_rate_to_inr')).aggregate(
            sum=Sum('converted_value')).get('sum')
        total_value = round(total_value, 2) if total_value else 0
        return realtime_exchange_value(from_currency='INR', to_currency=DEFAULT_CURRENCY, value=total_value)

    def get_invoiced_amount(self, obj):
        total_value = CrmOpportunityMilestoneMap.cmobjects.filter(opportunity__lead=obj.lead,
            milestone__invoiced=True, milestone__is_deleted=False).annotate(
            converted_value=F('milestone__value') * F('opportunity__conversion_rate_to_inr')).aggregate(
            sum=Sum('converted_value')).get('sum')
        total_value = round(total_value, 2) if total_value else 0
        return realtime_exchange_value(from_currency='INR', to_currency=DEFAULT_CURRENCY, value=total_value)

    def get_realized_amount(self, obj):
        total_value = CrmOpportunityMilestoneMap.cmobjects.filter(opportunity__lead=obj.lead,
            milestone__is_paid=True, milestone__is_deleted=False).annotate(
            converted_value=F('milestone__value') * F('opportunity__conversion_rate_to_inr')).aggregate(
            sum=Sum('converted_value')).get('sum')
        total_value = round(total_value, 2) if total_value else 0
        return realtime_exchange_value(from_currency='INR', to_currency=DEFAULT_CURRENCY, value=total_value)

    def get_won_value(self, obj):
        total_value = CrmOpportunity.cmobjects.filter(status=1,lead=obj.lead).annotate(
            converted_value=F('value') * F('conversion_rate_to_inr')).aggregate(
            sum=Sum('converted_value')).get('sum')
        total_value = round(total_value, 2) if total_value else 0
        return realtime_exchange_value(from_currency='INR', to_currency=DEFAULT_CURRENCY, value=total_value)

    def get_won_opportunities(self,obj):
        return CrmOpportunity.cmobjects.filter(status=1,lead=obj.lead).count()

    def get_total_opportunities_value(self, obj):
        total_value = CrmOpportunity.cmobjects.filter(lead=obj.lead).annotate(
            converted_value=F('value') * F('conversion_rate_to_inr')).aggregate(
            sum=Sum('converted_value')).get('sum')
        total_value = round(total_value, 2) if total_value else 0
        return realtime_exchange_value(from_currency='INR', to_currency=DEFAULT_CURRENCY, value=total_value)

    def get_active_opportunities(self,obj):
        return CrmOpportunity.cmobjects.filter(~Q(status=2),lead=obj.lead).count()

    def get_color_remarks(self, obj):
        return CrmOpportunityRemarks.cmobjects.filter(opportunity=obj, is_color_remarks=True).values('id', 'opportunity', 'remarks', 'created_by__first_name', 'created_by__last_name','created_at')

    def get_latest_color_remarks(self, obj):
        return CrmOpportunityRemarks.cmobjects.filter(opportunity=obj, is_color_remarks=True).order_by('-id').first().remarks if CrmOpportunityRemarks.cmobjects.filter(opportunity=obj,is_color_remarks=True).order_by('-id').first() else ''


class CrmInvoiceReportListSerializer(ModelSerializer):
    business_name = SerializerMethodField()
    project_name = SerializerMethodField()
    invoice_status = SerializerMethodField()
    invoice_date = SerializerMethodField()
    total_amount = SerializerMethodField()
    invoice_no = SerializerMethodField()
    is_paid = SerializerMethodField()
    transaction_id = SerializerMethodField()
    mode_of_payment_name = SerializerMethodField()
    due_date = SerializerMethodField()
    default_currency = SerializerMethodField()

    class Meta:
        model = CrmOpportunityMilestoneMap
        fields = ('business_name', 'project_name', 'invoice_status', 'invoice_date', 'total_amount', 'invoice_no',
                  'is_paid', 'transaction_id', 'mode_of_payment_name', 'due_date', 'default_currency')

    def get_default_currency(self, obj):
        return DEFAULT_CURRENCY

    def get_due_date(self, obj):
        return obj.milestone.due_date.strftime('%d/%m/%y') if obj.milestone.due_date else ''

    def get_mode_of_payment_name(self, obj):
        return obj.milestone.mode_of_payment.name if obj.milestone.mode_of_payment else ''

    def get_transaction_id(self, obj):
        return obj.milestone.transaction_id if obj.milestone.transaction_id else ''

    def get_is_paid(self, obj):
        return 'yes' if obj.milestone.is_paid else 'no'

    def get_invoice_no(self, obj):
        return obj.milestone.invoice_no if obj.milestone.invoice_no else ''

    def get_total_amount(self, obj):
        total_value = obj.milestone.value if obj.milestone.value else 0
        return realtime_exchange_value(from_currency='INR', to_currency=DEFAULT_CURRENCY, value=total_value)

    def get_invoice_date(self, obj):
        return obj.milestone.invoice_date.strftime('%d/%m/%y') if obj.milestone.invoice_date else ''

    def get_invoice_status(self, obj):
        return 'yes' if obj.milestone.invoiced else 'no'

    def get_project_name(self, obj):
        project = CrmProject.cmobjects.filter(opportunity=obj.opportunity)
        return project.first().account_name if project.first() else ''

    def get_business_name(self, obj):
        return obj.opportunity.lead.business_name


class CrmProjectReportListSerializer(ModelSerializer):
    status_name = CharField(source='get_status_display')
    account_manager_name = SerializerMethodField()
    account_manager = CrmUserSerializer()
    project_lead_name = SerializerMethodField()
    project_lead = CrmUserSerializer()
    color_remarks = SerializerMethodField()
    latest_color_remarks = SerializerMethodField()
    realized_amount = SerializerMethodField()
    total_amount = SerializerMethodField()
    due_amount = SerializerMethodField()
    milestone = SerializerMethodField()
    total_change_request_value = SerializerMethodField()
    resource_management = SerializerMethodField()
    currency = CrmCurrencySerializer()
    total_effort = SerializerMethodField()
    complete_percentage = SerializerMethodField()
    collection_percentage = SerializerMethodField()
    color_status = CrmColorStatusSerializer()
    color_status_name = SerializerMethodField()

    class Meta:
        model = CrmOpportunity
        fields = ('opportunity_name', 'business_name', 'account_manager_name', 'account_manager', 'color_remarks',
                  'latest_color_remarks', 'realized_amount', 'total_change_request_value', 'resource_management',
                  'due_amount', 'milestone', 'project_lead_name', 'project_lead', 'resource_timeline', 'value',
                  'currency', 'total_effort', 'resource_hour_consumed', 'complete_percentage', 'color_status',
                  'collection_percentage', 'total_amount', 'status_name', 'color_status_name')

    def get_color_status_name(self, obj):
        return obj.color_status.name if obj.color_status else ''

    def get_total_amount(self, obj):
        change_request_value = obj.change_request.aggregate(sum=Sum('value')).get('sum')
        change_request_value = round(change_request_value, 2) if change_request_value else 0
        return change_request_value + obj.value

    def get_collection_percentage(self, obj):
        total_value = get_change_request_milestone_amount(opportunity=obj, amount_type='total')
        paid_value = get_change_request_milestone_amount(opportunity=obj, amount_type='paid')
        try:
            collection_percent = (float(paid_value)/float(total_value))*100
        except ZeroDivisionError:
            collection_percent = 0.0
        return collection_percent

    def get_complete_percentage(self, obj):
        total_effort = CrmOpportunityResourceManagement.cmobjects.filter(opportunity=obj).annotate(
            effort=F('man_hours') * F('resource_no')).aggregate(
            sum=Sum('effort')).get('sum')
        total_effort = round(total_effort, 2) if total_effort else 0.0
        try:
            complete_percent = (float(total_effort)/float(obj.resource_hour_consumed))*100
        except ZeroDivisionError:
            complete_percent = 0.0
        return round(complete_percent,2)

    def get_total_effort(self, obj):
        total_effort = CrmOpportunityResourceManagement.cmobjects.filter(opportunity=obj).annotate(
            effort=F('man_hours') * F('resource_no')).aggregate(
            sum=Sum('effort')).get('sum')
        return round(total_effort,2) if total_effort else 0.0

    def get_resource_management(self, obj):
        resource_query = CrmOpportunityResourceManagement.cmobjects.filter(opportunity=obj)
        resource_serializer = CrmOpportunityDetailsResourceManagementSerializer(resource_query, many=True)
        return resource_serializer.data

    def get_milestone(self, obj):
        milestone_serializer = CrmOpportunityDetailsMilestoneSerializer(obj.milestone.filter(is_deleted=False), many=True)
        for data in milestone_serializer.data:
            change_request_distributions = CrmOpportunityMilestoneChangeRequestDistribution.cmobjects.filter(opportunity=obj,milestone=data['id'])
            change_request_distributions_serializer = CrmOpportunityDetailsChangeRequestDistributionSerializer(change_request_distributions, many=True)
            data['change_request'] = change_request_distributions_serializer.data
        return milestone_serializer.data

    def get_project_lead_name(self, obj):
        return obj.project_lead.get_full_name() if obj.project_lead else ''

    def get_account_manager_name(self, obj):
        return obj.account_manager.get_full_name() if obj.account_manager else ''

    def get_due_amount(self, obj):
        total_unpaid_value = get_change_request_milestone_amount(opportunity=obj, amount_type='unpaid')
        return total_unpaid_value

    def get_realized_amount(self, obj):
        total_paid_value = get_change_request_milestone_amount(opportunity=obj, amount_type='paid')
        return total_paid_value

    def get_total_change_request_value(self, obj):
        change_request_value = obj.change_request.aggregate(sum=Sum('value')).get('sum')
        return round(change_request_value, 2) if change_request_value else 0

    def get_color_remarks(self, obj):
        return CrmOpportunityRemarks.cmobjects.filter(opportunity=obj, is_color_remarks=True).values('id', 'opportunity', 'remarks', 'created_by__first_name', 'created_by__last_name','created_at')

    def get_latest_color_remarks(self, obj):
        return CrmOpportunityRemarks.cmobjects.filter(opportunity=obj, is_color_remarks=True).order_by('-id').first().remarks if CrmOpportunityRemarks.cmobjects.filter(opportunity=obj,is_color_remarks=True).order_by('-id').first() else ''

