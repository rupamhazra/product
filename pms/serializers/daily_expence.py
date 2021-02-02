from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from pms.models.module_project import *
from pms.models.module_daily_expence import *
from django.contrib.auth.models import *
import time
from django.db import transaction, IntegrityError
from drf_extra_fields.fields import Base64ImageField
import os
from rest_framework.exceptions import APIException
import datetime
from rest_framework.response import Response
from pms.custom_filter import custom_filter
import pandas as pd
import numpy as np
import xlrd
from pms.custom_delete import *
from django.db.models import Q
import re
import json
from global_notification import send_notification, store_sent_notification
from global_function import send_mail

#:::::::::::: PROJECTS ::::::::::::::::::::::::::::#
class DailyExpenceAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    items = serializers.ListField(required=False)

    class Meta:
        model = PmsDailyExpence
        fields = '__all__'
        extra_fields = ('items',)
    
    def send_notification_mail(self,expence_data):

        project_manager_details = [expence_data.project.project_manager]
        app_module = 'pms'
        title = 'A new application has been submitted.Please check the details and take necessary action.'
        body ='Employee Name: {} \nAmount:{} \nVoucher No:{}'.format(expence_data.created_by.get_full_name(),expence_data.amount,expence_data.voucher_no)
        data = {
                    "app_module":app_module,
                    "type":"daily-expense",
                    "sub_type":"approval/project-manager",
                    "id":expence_data.id
                }
        data_str = json.dumps(data)
        #print('data_str',data_str)
        notification_id = store_sent_notification(users=project_manager_details,body=body,title=title,data=data_str,app_module_name=app_module)
        send_notification(users=project_manager_details,body=body,title=title,data=data,notification_id=notification_id,url=app_module)
        
        # Mail
        user_email = expence_data.project.project_manager.cu_user.cu_alt_email_id
        if user_email:
            mail_data = {
                            "recipient_name":expence_data.project.project_manager.get_full_name(),
                            "name": expence_data.created_by.get_full_name(),
                            "project_name":expence_data.project.name,
                            "amount": expence_data.amount if expence_data.amount else '',
                            "voucher_no": expence_data.voucher_no if expence_data.voucher_no else '',
                            "paid_to":expence_data.paid_to if expence_data.paid_to else ''
                        }
            
            send_mail('PMS-DE-CN',user_email,mail_data)

    def create(self, validated_data):
        try:
            with transaction.atomic():
                #print('validated_data',validated_data)
                items = validated_data.pop('items')
                items_j = json.loads(items[0])
                #print('items',items)
                expence_data = PmsDailyExpence.objects.create(**validated_data)
                if expence_data:
                    for item in items_j:
                        PmsDailyExpenceItemMapping.objects.create(
                            item = item['item'],
                            daily_expence = expence_data,
                            created_by = validated_data.get('created_by'),
                            owned_by = validated_data.get('created_by'),
                            )
                    _dailyexpenceApprovalConfiguration_project = PmsDailyExpenceApprovalConfiguration.objects.filter(
                        is_deleted=False,project=validated_data.get('project'))
                    #print('_dailyexpenceApprovalConfiguration',_dailyexpenceApprovalConfiguration)
                    if _dailyexpenceApprovalConfiguration_project:
                        for _e_dailyexpenceApprovalConfiguration_project in _dailyexpenceApprovalConfiguration_project:
                            PmsDailyExpenceApproval.objects.get_or_create(
                                approval_user_level_id=_e_dailyexpenceApprovalConfiguration_project.id,
                                daily_expence_id = expence_data.id,
                                created_by = _e_dailyexpenceApprovalConfiguration_project.user
                                )

                    _dailyexpenceApprovalConfiguration = PmsDailyExpenceApprovalConfiguration.objects.filter(
                        is_deleted=False,project__isnull=True)
                    #print('_dailyexpenceApprovalConfiguration',_dailyexpenceApprovalConfiguration)
                    if _dailyexpenceApprovalConfiguration:
                        for _e_dailyexpenceApprovalConfiguration in _dailyexpenceApprovalConfiguration:
                            PmsDailyExpenceApproval.objects.get_or_create(
                                approval_user_level_id=_e_dailyexpenceApprovalConfiguration.id,
                                daily_expence_id = expence_data.id,
                                created_by = _e_dailyexpenceApprovalConfiguration.user
                                )


                self.send_notification_mail(expence_data)
                return validated_data
        except Exception as e:
            raise APIException({"msg": e, "request_status": 0})
        
class DailyExpenceListSerializer(serializers.ModelSerializer):
    paid_for = serializers.SerializerMethodField(required=False)
    items = serializers.SerializerMethodField(required=False)
    project_details= serializers.SerializerMethodField(required=False)
    employee_name = serializers.SerializerMethodField(required=False)
    remarks = serializers.SerializerMethodField(required=False)
    approvals = serializers.SerializerMethodField(required=False)
    current_level_of_approval_details = serializers.SerializerMethodField(required=False)

    def get_items(self,PmsDailyExpence):
        return PmsDailyExpenceItemMapping.objects.filter(daily_expence=PmsDailyExpence.id).values()

    def get_paid_for(self,PmsDailyExpence):
        return PmsDailyExpenceItemMapping.objects.filter(daily_expence=PmsDailyExpence.id).values()

    def get_project_details(self,PmsDailyExpence):
    	project_details = PmsProjects.objects.filter(pk=PmsDailyExpence.project.id)
    	if project_details:
    		return project_details.values()[0]

    def get_employee_name(self,PmsDailyExpence):
    	return PmsDailyExpence.created_by.get_full_name()

    def get_remarks(self,PmsDailyExpence):
        remarks_details = PmsDailyExpenceRemarks.objects.filter(daily_expence_id=PmsDailyExpence.id,is_deleted=False)
        result = []
        if remarks_details:
            for each_remarks_details in remarks_details:
                result.append({
                    "remarks":each_remarks_details.remarks,
                    'author_name':each_remarks_details.user.get_full_name(),
                    'remarks_at':each_remarks_details.created_at
                    })
        return result

    def get_approvals(self,PmsDailyExpence):
        approval_con = PmsDailyExpenceApprovalConfiguration.objects.filter(project=PmsDailyExpence.project,is_deleted=False).order_by('level_no')
        approval_list = list()
        for each_approval in approval_con:
            result = {
            "id":each_approval.id,
            "level":each_approval.level,
            "user":each_approval.user_id,
            "name":each_approval.user.get_full_name(),
            "status": PmsDailyExpenceApproval.objects.filter(
                daily_expence_id=PmsDailyExpence.id,approval_user_level_id=each_approval.id,is_deleted=False).values_list('approval_status',flat=True)[0] if PmsDailyExpenceApproval.objects.filter(
                daily_expence_id=PmsDailyExpence.id,approval_user_level_id=each_approval.id,is_deleted=False) else None
            }
            approval_list.append(result)

        approval_con = PmsDailyExpenceApprovalConfiguration.objects.filter(project__isnull=True,is_deleted=False).order_by('level_no')
        for each_approval in approval_con:
            result = {
            "id":each_approval.id,
            "level":each_approval.level,
            "user":each_approval.user_id,
            "name":each_approval.user.get_full_name(),
            "status": PmsDailyExpenceApproval.objects.filter(
                daily_expence_id=PmsDailyExpence.id,approval_user_level_id=each_approval.id,is_deleted=False).values_list('approval_status',flat=True)[0] if PmsDailyExpenceApproval.objects.filter(
                daily_expence_id=PmsDailyExpence.id,approval_user_level_id=each_approval.id,is_deleted=False) else None
            }
            approval_list.append(result)
        return approval_list

    def get_current_level_of_approval_details(self,PmsDailyExpence):
        approval_con = PmsDailyExpenceApproval.objects.filter(
            approval_user_level__in = PmsDailyExpenceApprovalConfiguration.objects.filter(
                (Q(project=PmsDailyExpence.project)|Q(project__isnull=True)),
                is_deleted=False,
                level=PmsDailyExpence.current_level_of_approval
                ).values_list('id',flat=True),
            daily_expence = PmsDailyExpence.id
            )
        if approval_con:
            approval_con = approval_con[0]
            return {
                'approved_by':approval_con.created_by.get_full_name() if approval_con.created_by else '',
                'status': approval_con.approval_status
            }

    class Meta:
        model = PmsDailyExpence
        fields = '__all__'
        extra_fields = ('items','paid_for','project_details','employee_name','remarks','approvals','current_level_of_approval_details')
   
class DailyExpenceStatusUpdateSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    approval_user_level = serializers.CharField(required=False)
    daily_expence_approvals = serializers.ListField(required=False)
    remarks = serializers.CharField(required=False,allow_blank=True)
    approval_user_level_name =  serializers.CharField(required=False)


    class Meta:
        model = PmsDailyExpence
        fields = ('id','status','updated_by','daily_expence_approvals','approval_user_level','remarks','approval_user_level_name','approve_amount')

    
    def send_mail_notification_to_approvar(self,request_by,expence_data,user,approved_status_name):
        user_email = None
        recipient_name = None
        if request_by == 'Project Manager':
            users = [expence_data.project.project_coordinator]
            recipient_name = expence_data.project.project_coordinator.get_full_name()
            user_email = expence_data.project.project_coordinator.cu_user.cu_alt_email_id
            #print('users',users)
        if request_by == 'Project Coordinator':
            ho_details = PmsDailyExpenceApprovalConfiguration.objects.filter(is_deleted=False,level='HO',project__isnull=True)
            print('ho_details',ho_details)
            if ho_details:
                ho_details = ho_details[0]
                users = [ho_details.user]
                user_email = ho_details.user.cu_user.cu_alt_email_id
                recipient_name = ho_details.user.get_full_name()
        if request_by == 'HO':
            #request_by = 'ho'
            account_details = PmsDailyExpenceApprovalConfiguration.objects.filter(is_deleted=False,level='Account',project__isnull=True)
            if account_details:
                account_details = account_details[0]
                users = [account_details.user]
                user_email = account_details.user.cu_user.cu_alt_email_id
                recipient_name = account_details.user.get_full_name()
        
        app_module = 'pms'
        level = request_by

        if approved_status_name == 'Approved':

            if request_by != 'Account':    

                # For send to approvar
                title = 'A new application has been '+approved_status_name+' by '+request_by+'.Please check the details and take necessary action.'
                body ='Employee Name: {} \nAmount:{} \nVoucher No:{}'.format(expence_data.created_by.get_full_name(),expence_data.amount,expence_data.voucher_no)
                data = {
                        "app_module":app_module,
                        "type":"daily-expense",
                        "sub_type":"approval/"+request_by.replace(' ','-').lower(),
                        "id":expence_data.id
                    }
                data_str = json.dumps(data)
                notification_id = store_sent_notification(users=users,body=body,title=title,data=data_str,app_module_name=app_module)
                send_notification(users=users,body=body,title=title,data=data,notification_id=notification_id,url=app_module)

                # Mail
                
                if user_email:
                    mail_data = {
                                    "status":approved_status_name,
                                    "request_by":request_by,
                                    "recipient_name":recipient_name,
                                    "name": expence_data.created_by.get_full_name(),
                                    "project_name":expence_data.project.name,
                                    "amount": expence_data.amount if expence_data.amount else '',
                                    "voucher_no": expence_data.voucher_no if expence_data.voucher_no else '',
                                    "paid_to":expence_data.paid_to if expence_data.paid_to else ''
                                }
                    
                    send_mail('PMS-DE-AN',user_email,mail_data)

            else:
                level = 'Account'
            
                # For send to User
                users = [user]
                recipient_name = user.get_full_name()
                user_email = user.cu_user.cu_alt_email_id
                remarks = None
                remark_details = PmsDailyExpenceRemarks.objects.filter(daily_expence=expence_data,user=expence_data.updated_by)
                if remark_details:
                    remark_details = remark_details[0]
                    remarks = remark_details.remarks
                
                title_for_user = 'Your application has been '+approved_status_name+' by '+level+'.Please check the details.'
                body_for_user ='Approvar Name: {} \nApproved At:{} \nRemarks'.format(
                    expence_data.updated_by.get_full_name(),
                    expence_data.updated_at,
                    remarks
                    )
                data_for_user = {
                            "app_module":app_module,
                            "type":"daily-expense",
                            "sub_type":"my-expense",
                            "id":expence_data.id
                        }
                data_str = json.dumps(data_for_user)
                notification_id = store_sent_notification(users=users,body=body_for_user,title=title_for_user,data=data_str,app_module_name=app_module)
                send_notification(users=users,body=body_for_user,title=title_for_user,data=data_for_user,notification_id=notification_id,url=app_module)

                # For Mail
                if user_email:
                    mail_data = {
                                    "status":approved_status_name,
                                    "request_by":level,
                                    "recipient_name":recipient_name,
                                    "name": expence_data.created_by.get_full_name(),
                                    "project_name":expence_data.project.name,
                                    "amount": expence_data.amount if expence_data.amount else '',
                                    "voucher_no": expence_data.voucher_no if expence_data.voucher_no else '',
                                    "paid_to":expence_data.paid_to if expence_data.paid_to else ''
                                }
                    
                    send_mail('PMS-DE-UN',user_email,mail_data)

        else:
            users = [user]
            #print('users',users)
            recipient_name = user.get_full_name()
            user_email = user.cu_user.cu_alt_email_id
            remarks = None
            remark_details = PmsDailyExpenceRemarks.objects.filter(daily_expence=expence_data,user=expence_data.updated_by)
            #print('remark_details',remark_details)
            if remark_details:
                remark_details = remark_details[0]
                remarks = remark_details.remarks
            #print('expence_data.updated_by',expence_data.updated_by)
            title_for_user = 'Your application has been '+approved_status_name+' by '+level+'.Please check the details.'
            body_for_user ='Approvar Name: {} \nApproved At:{} \nRemarks'.format(
                expence_data.updated_by.get_full_name(),
                expence_data.updated_at,
                remarks
                )
            data_for_user = {
                        "app_module":app_module,
                        "type":"daily-expense",
                        "sub_type":"my-expense",
                        "id":expence_data.id
                    }
            data_str = json.dumps(data_for_user)
            notification_id = store_sent_notification(users=users,body=body_for_user,title=title_for_user,data=data_str,app_module_name=app_module)
            send_notification(users=users,body=body_for_user,title=title_for_user,data=data_for_user,notification_id=notification_id,url=app_module)

            # For Mail
            if user_email:
                mail_data = {
                                "status":approved_status_name,
                                "request_by":level,
                                "recipient_name":recipient_name,
                                "name": expence_data.created_by.get_full_name(),
                                "project_name":expence_data.project.name,
                                "amount": expence_data.amount if expence_data.amount else '',
                                "voucher_no": expence_data.voucher_no if expence_data.voucher_no else '',
                                "paid_to":expence_data.paid_to if expence_data.paid_to else ''
                            }
                
                send_mail('PMS-DE-UN',user_email,mail_data)

    def _addRemark(self,validated_data,e_daily_expence_id):
        if validated_data.get('remarks'):
            return PmsDailyExpenceRemarks.objects.create(
                        remarks = validated_data.get('remarks'),
                        daily_expence_id = e_daily_expence_id,
                        user = validated_data.get('updated_by'),
                        created_by = validated_data.get('updated_by'),
                        )

    def create(self, validated_data):
        try:
            with transaction.atomic():
                daily_expence_ids = validated_data.get('daily_expence_approvals')
                status = ''
                approved_status_name = validated_data.get('status')+'ed'
                approved_status = ''
                current_level_of_approval = None

                if validated_data.get('status') == 'Approve' or validated_data.get('status') == 'Modify':
                    
                    if validated_data.get('approval_user_level_name') == 'Project Manager':
                        status = "Pending For Project Coordinator Approval"
                        approved_status_name = 'Approved'
                        current_level_of_approval = 'Project Coordinator'


                    if validated_data.get('approval_user_level_name') == 'Project Coordinator':
                        status = "Pending For HO Approval"
                        approved_status_name = 'Approved'
                        current_level_of_approval = 'HO'

                    if validated_data.get('approval_user_level_name') == 'HO':
                        status = "Pending For Account Approval"
                        approved_status_name = 'Approved'
                        current_level_of_approval = 'Account'

                    if validated_data.get('approval_user_level_name') == 'Account':
                        status = "Approve"
                        approved_status_name = 'Approved'
                        current_level_of_approval = 'Account'

                if validated_data.get('status') == 'Reject':
                    
                    if validated_data.get('approval_user_level_name') == 'Project Manager':
                        status = "Reject"
                        approved_status_name = 'Rejected'

                    if validated_data.get('approval_user_level_name') == 'Project Coordinator':
                        status = "Reject"
                        approved_status_name = 'Rejected'

                    if validated_data.get('approval_user_level_name') == 'HO':
                        status = "Reject"
                        approved_status_name = 'Rejected'

                    if validated_data.get('approval_user_level_name') == 'Account':
                        status = "Reject"
                        approved_status_name = 'Rejected'

                for e_daily_expence_id in daily_expence_ids:
                    #print('e_daily_expence_id',e_daily_expence_id)
                    _pmsDailyExpenceApproval = PmsDailyExpenceApproval.objects.filter(
                        daily_expence_id = e_daily_expence_id,
                        approval_user_level=validated_data.get('approval_user_level'),
                        is_deleted=False
                        ).update(approval_status = validated_data.get('status'),updated_by = validated_data.get('updated_by'))
                    #print('status',status)
                    _pmsDailyExpence = PmsDailyExpence.objects.get(pk=e_daily_expence_id,is_deleted=False)
                    _pmsDailyExpence.status = status

                    if 'approve_amount' in validated_data:
                        _pmsDailyExpence.approve_amount = validated_data.get('approve_amount')
                    else:
                        if not _pmsDailyExpence.approve_amount:
                            _pmsDailyExpence.approve_amount = _pmsDailyExpence.amount
                    

                    _pmsDailyExpence.updated_by = validated_data.get('updated_by')
                    if current_level_of_approval:
                        _pmsDailyExpence.current_level_of_approval = current_level_of_approval
                    _pmsDailyExpence.save()

                    self._addRemark(validated_data,e_daily_expence_id)

                    # Mail and Notification
                    self.send_mail_notification_to_approvar(validated_data.get('approval_user_level_name'),_pmsDailyExpence,_pmsDailyExpence.created_by,approved_status_name)

                return validated_data

        except Exception as e:
            raise APIException({"msg": e, "request_status": 0})

class DailyExpencePaymentUpdateSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    daily_expence_approvals = serializers.ListField(required=False)
    remarks = serializers.CharField(required=False,allow_null=True)

    class Meta:
        model = PmsDailyExpence
        fields = ('id','is_paid','updated_by','daily_expence_approvals','remarks')

    def send_mail_notification_to_user(self,expence_data,user):
        app_module = 'pms'

        # For send to User
        users = [user]
        user_email = user.cu_user.cu_alt_email_id
        recipient_name = user.get_full_name()
        remarks = None
        remark_details = PmsDailyExpenceRemarks.objects.filter(daily_expence=expence_data,user=expence_data.updated_by)
        if remark_details:
            remark_details = remark_details[0]
            remarks = remark_details.remarks

        title = 'Your application payment status has been updated.Please check the details.'
        body ='Approvar Name: {} \nUpdated At:{} \nRemarks'.format(
            expence_data.updated_by.get_full_name(),
            expence_data.updated_at,
            remarks
            )
        data = {
                    "app_module":app_module,
                    "type":"daily-expense",
                    "sub_type":"my-expense",
                    "id":expence_data.id
                }
        data_str = json.dumps(data)
        #print('data_str',data_str)
        notification_id = store_sent_notification(users=users,body=body,title=title,data=data_str,app_module_name=app_module)
        send_notification(users=users,body=body,title=title,data=data,notification_id=notification_id,url=app_module)

        # Mail
        if user_email:
            mail_data = {
                            "recipient_name":recipient_name,
                            "name": expence_data.created_by.get_full_name(),
                            "project_name":expence_data.project.name,
                            "amount": expence_data.amount if expence_data.amount else '',
                            "voucher_no": expence_data.voucher_no if expence_data.voucher_no else '',
                            "paid_to":expence_data.paid_to if expence_data.paid_to else ''
                        }
            
            send_mail('PMS-DE-PN',user_email,mail_data)
      

    def _addRemark(self,validated_data,e_daily_expence_id):
        return PmsDailyExpenceRemarks.objects.create(
                    remarks = validated_data.get('remarks'),
                    daily_expence_id = e_daily_expence_id,
                    user = validated_data.get('updated_by'),
                    created_by = validated_data.get('updated_by'),
                    )

    def create(self, validated_data):
        try:
            with transaction.atomic():
                daily_expence_ids = validated_data.get('daily_expence_approvals')
                for e_daily_expence_id in daily_expence_ids:
                    e_daily_expence = PmsDailyExpence.objects.get(pk=e_daily_expence_id)
                    daily_expence = PmsDailyExpence.objects.filter(pk=e_daily_expence_id,is_deleted=False,status='Approve').update(
                        is_paid=validated_data.get('is_paid'),updated_by = validated_data.get('updated_by'))
                    self._addRemark(validated_data,e_daily_expence_id)
                    # Mail and Notification
                    self.send_mail_notification_to_user(e_daily_expence,e_daily_expence.created_by)
                return validated_data
        except Exception as e:
            raise APIException({"msg": e, "request_status": 0})


    
    

    
   
    

    
   