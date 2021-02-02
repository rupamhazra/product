from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from etask.models import *
from django.contrib.auth.models import *
from django.db import transaction, IntegrityError
from drf_extra_fields.fields import Base64ImageField
import os
import datetime
from custom_exception_message import *
from etask.utils import get_task_flag, is_pending_extention, is_pending_closer, create_comment
from mailsend.views import *
from threading import Thread   
from datetime import datetime
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from users.models import TCoreUserDetail
from smssend.views import *
from threading import Thread
from django.db.models import When, Case, Value, CharField, IntegerField, F, Q
from global_function import (department, designation, userdetails, getHostWithPort,
                             raw_query_extract, get_user_reporting_heads, create_appointment,
                             send_mail, send_mail_list, get_users_under_reporting_head)
from employee_leave_calculation import daterange
from global_notification import send_notification, store_sent_notification


class EtaskTaskAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    user_cc = serializers.ListField(required=False)
    assignto = serializers.ListField(required=False)
    reporting_date = serializers.ListField(required=False)
    is_forcefully = serializers.BooleanField(required=False)
    followup_date = serializers.DateTimeField(required=False)
    class Meta:
        model = EtaskTask
        fields = '__all__'
        extra_fields = ('user_cc','assignto','reporting_date')
    
    def create(self,validated_data):
        try:
            with transaction.atomic():
                created_by = validated_data.get('created_by')
                owned_by = validated_data.get('owned_by')
                is_forcefully = validated_data.pop('is_forcefully') if 'is_forcefully' in validated_data.keys() else False
                followup_date = validated_data.pop('followup_date') if 'followup_date' in validated_data.keys() else None
                # followup_date = datetime.strptime(validated_data.pop('followup_date'), "%Y-%m-%dT%H:%M:%S.%fZ") if 'followup_date' in validated_data else None
                #print("followup_date",followup_date)
                user_cc = validated_data.pop('user_cc') if 'user_cc' in validated_data else ""
                # assignto = validated_data.pop('assignto') if 'assignto' in validated_data else ""
                reporting_date = validated_data.pop('reporting_date') if 'reporting_date' in validated_data else ""

                #print("validated_data['task_categories']", validated_data['start_date'])

                if validated_data['task_type'] in [3,4]:
                    start_date_data = validated_data['start_date'].date()
                    end_date_data = validated_data['end_date'].date()
                    if EtaskTask.objects.filter(start_date__date__lte=start_date_data,end_date__date__gte=end_date_data,
                        id=validated_data['parent_id']):
                        #print("PROPER TIME")
                        pass
                    else:
                        raise APIException({'msg':'Please put Task date in between parent task date range',
                                    "request_status": 0
                                    })


                if validated_data['task_categories']==1:
                    validated_data["owner"]=created_by
                    validated_data["assign_by"]= created_by
                    validated_data["assign_to"]= created_by
                elif validated_data['task_categories']==2:
                    validated_data["assign_by"]=validated_data['owner']
                    validated_data["assign_to"]=created_by
                elif validated_data['task_categories']==3:
                    validated_data["assign_by"]=created_by
                    validated_data['owner']=created_by              

            ### Etask Created modified By Manas Paul,[ get_or_create --> create ], Cause Tak Subject can not possible to create same Subject ###
            ### Changing approved by Tonmoy Sardar ###
                if validated_data["assign_to"] and reporting_date != "" and is_forcefully is False:
                    for report_dt in reporting_date:
                        reporting_date_data = datetime.strptime(report_dt['reporting_date'], "%Y-%m-%dT%H:%M:%S.%fZ")
                        if EtaskTask.objects.filter(Q(Q(task_status=1)|Q(task_status=3)),
                                                            Q(Q(assign_to_id=validated_data["assign_to"])|
                                                            Q(sub_assign_to_user_id=validated_data["assign_to"])),
                                                            id__in=list(ETaskReportingDates.objects.filter(task_type=1,reporting_status=2,
                                                            reporting_date=reporting_date_data).values_list('task',flat=True))):
                            '''
                                "request_status": 2 >> User define exception or condition checking by front end
                            '''
                            reporting_date_formet = reporting_date_data.strftime("%m/%d/%Y, %I:%M:%S %p")
                            raise APIException({'msg': reporting_date_formet+' is already blocked on your Calendar',
                                                "request_status": 2
                                                })
                    

                task_create = EtaskTask.objects.create(         
                    **validated_data
                )
                EtaskTask.objects.filter(id=task_create.id).update(task_code_id="TSK"+str(task_create.id))
                #print("task_create.id",task_create.id)

                if followup_date:
                    #print("followup_date",followup_date)
                    if validated_data['task_categories']==1:
                        EtaskFollowUP.objects.get_or_create(task=task_create,assign_to=created_by,follow_up_task=validated_data['task_subject'],
                                                            follow_up_date=followup_date,created_by=created_by)
                    else:
                        if 'assign_to' in validated_data:
                            EtaskFollowUP.objects.get_or_create(task=task_create,follow_up_task=validated_data['task_subject'],
                                                                assign_to=validated_data["assign_to"],follow_up_date=followup_date,created_by=validated_data["assign_to"])
                        if 'owner' in validated_data:
                            EtaskFollowUP.objects.get_or_create(task=task_create,follow_up_task=validated_data['task_subject'],
                                                                assign_to=validated_data['owner'],follow_up_date=followup_date,created_by=validated_data['owner'])
                
                usercc_list = []
                for u_cc in user_cc:
                    ucc_details,created_1 = EtaskUserCC.objects.get_or_create(
                        task = task_create, ** u_cc, created_by=created_by , owned_by = owned_by
                    )
                    ucc_details.__dict__.pop('_state') if "_state" in ucc_details.__dict__.keys() else ucc_details.__dict__
                    usercc_list.append(ucc_details.__dict__)
              
                reporting_date_list = []
                #print("task_create",task_create.__dict__['id'])
                # #print("r_date['reporting_date']",r_date['reporting_date'])
                reporting_date_str = """"""
                r_time = ''
                ics_data = """BEGIN:VCALENDAR
VERSION:2.0
CALSCALE:GREGORIAN\n"""
                user_name = userdetails(int(task_create.__dict__['assign_to_id']))
                count_id = 0
                for r_date in reporting_date:
                    rdate_details,created = ETaskReportingDates.objects.get_or_create(
                        task_type=1,
                        task = task_create.__dict__['id'],
                        reporting_date = datetime.strptime(r_date['reporting_date'], "%Y-%m-%dT%H:%M:%S.%fZ"),
                        created_by=created_by,
                        owned_by=owned_by
                    )
                    # #print('rdate_details',rdate_details,type(rdate_details))
                    reporting_log,created=ETaskReportingActionLog.objects.get_or_create(
                                                                                        task_id = task_create.__dict__['id'],
                                                                                        reporting_date_id =str(rdate_details),
                                                                                        updated_date=datetime.now().date(),
                                                                                        status=2,
                                                                                        created_by=created_by,
                                                                                        owned_by=owned_by
                                                                                    )
                    # #print('reporting_log',reporting_log)

                    rdate_details.__dict__.pop('_state') if "_state" in rdate_details.__dict__.keys() else rdate_details.__dict__
                    reporting_date_list.append(rdate_details.__dict__)
                    ###################################################
                    count_id += 1
                    # reporting_date_str += datetime.strptime(x['reporting_date'], "%m/%d/%Y, %I:%M:%S %p")+'\n'
                    reporting_date_str += str(count_id)+'. '+rdate_details.__dict__['reporting_date'].strftime("%m/%d/%Y, %I:%M:%S %p")+" "
                    r_time = rdate_details.__dict__['reporting_date'].strftime("%Y%m%dT%H%M%S")
                    ics_data +=   """BEGIN:VEVENT
SUMMARY:Reporting of {rep_sub}
DTSTART;TZID=Asia/Kolkata:{r_time}
LOCATION:Shyam Tower,Kolkata-700091
DESCRIPTION: Reporting dates.
STATUS:CONFIRMED
SEQUENCE:3
BEGIN:VALARM
TRIGGER:-PT10M
DESCRIPTION:Pickup Reminder
ACTION:DISPLAY
END:VALARM
END:VEVENT\n""".replace("{r_time}",r_time).replace("{rep_sub}",task_create.__dict__['task_subject'])


                
                ##############################################################
                #DTEND;TZID=Asia/Kolkata:{r_time}
                ics_data += "END:VCALENDAR"
                #print("reporting_date_str",reporting_date_str)
                # email change to TCoreUserDetail email
                user_email = User.objects.get(id=task_create.__dict__['assign_to_id']).cu_user.cu_alt_email_id
                #print("user_email",user_email)
                
                if user_email:
                    mail_data = {
                                "recipient_name" : user_name,        ## modified by manas Paul 21jan20
                                "task_subject": task_create.__dict__['task_subject'],
                                "reporting_date": reporting_date_str,
                            }
                    # #print('mail_data',mail_data)
                    # #print('mail_id-->',mail)
                    # #print('mail_id-->',[mail])
                    # mail_class = GlobleMailSend('ETAP', email_list)
                    # mail_class = GlobleMailSend('ETRDC', [user_email])
                    # #print('mail_class',mail_class)
                    # mail_thread = Thread(target = mail_class.mailsend, args = (mail_data,ics_data))
                    # #print('mail_thread-->',mail_thread)
                    # mail_thread.start()
                    send_mail_list('ETRDC', [user_email], mail_data, ics=ics_data)
                ######################################  

                validated_data['user_cc']=usercc_list
                # validated_data['assignto']=assignto_list
                validated_data['reporting_date']=reporting_date_list
                return validated_data

        except Exception as e:
            raise e
            # raise APIException({'request_status': 0, 'msg': e})


class EtaskTaskAddSerializerV2(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    user_cc = serializers.ListField(required=False)
    assignto = serializers.ListField(required=False)
    reporting_date = serializers.ListField(required=False)
    is_forcefully = serializers.BooleanField(required=False)
    followup_date = serializers.DateTimeField(required=False)
    proceed_without_reporting_date = serializers.BooleanField(required=False)

    class Meta:
        model = EtaskTask
        fields = '__all__'
        extra_fields = ('user_cc','assignto','reporting_date')
    
    def create(self,validated_data):
        try:
            with transaction.atomic():
                current_date = datetime.now()
                created_by = validated_data.get('created_by')
                owned_by = validated_data.get('owned_by')
                is_forcefully = validated_data.pop('is_forcefully') if 'is_forcefully' in validated_data.keys() else False
                followup_date = validated_data.pop('followup_date') if 'followup_date' in validated_data.keys() else None

                # followup_date = datetime.strptime(validated_data.pop('followup_date'), "%Y-%m-%dT%H:%M:%S.%fZ") if 'followup_date' in validated_data else None
                #print("followup_date",followup_date)
                user_cc = validated_data.pop('user_cc') if 'user_cc' in validated_data else ""
                # assignto = validated_data.pop('assignto') if 'assignto' in validated_data else ""
                reporting_date = validated_data.pop('reporting_date') if 'reporting_date' in validated_data else ""
                proceed_without_reporting_date = validated_data.pop('proceed_without_reporting_date') if 'proceed_without_reporting_date' in validated_data.keys() else False
                #print('proceed_without_reporting_date:', proceed_without_reporting_date)
                #print("validated_data['task_categories']", validated_data['start_date'])

                if validated_data['task_type']==3:
                    start_date_data = validated_data['start_date'].date()
                    end_date_data = validated_data['end_date'].date()
                    if EtaskTask.objects.filter((Q(Q(extended_date__isnull=False)&Q(extended_date__date__gte=end_date_data))
                                                |Q(Q(extended_date__isnull=True)&Q(end_date__date__gte=end_date_data))),
                                                start_date__date__lte=start_date_data,id=validated_data['parent_id']):
                        #print("PROPER TIME")
                        pass
                    else:
                        raise APIException({'msg':'Please put Task date in between parent task date range',
                                    "request_status": 0
                                    })

                if validated_data['task_categories']==1:
                    validated_data["owner"]=created_by
                    validated_data["assign_by"]= created_by
                    validated_data["assign_to"]= created_by
                elif validated_data['task_categories']==2:
                    validated_data["assign_by"]=validated_data['owner']
                    validated_data["assign_to"]=created_by
                elif validated_data['task_categories']==3:
                    validated_data["assign_by"]=created_by
                    validated_data['owner']=created_by              

                ### Etask Created modified By Manas Paul,[ get_or_create --> create ], Cause Tak Subject can not possible to create same Subject ###
                ### Changing approved by Tonmoy Sardar ###
                if validated_data['task_categories'] != 1 and validated_data["assign_to"] and reporting_date != "" and is_forcefully is False:
                    for report_dt in reporting_date:
                        reporting_date_data = datetime.strptime(report_dt['reporting_date'], "%Y-%m-%dT%H:%M:%S.%fZ")
                        if EtaskTask.objects.filter(Q(Q(task_status=1)|Q(task_status=3)),
                                                            Q(Q(assign_to_id=validated_data["assign_to"])|
                                                            Q(sub_assign_to_user_id=validated_data["assign_to"])),
                                                            id__in=list(ETaskReportingDates.objects.filter(task_type=1,reporting_status=2,
                                                            reporting_date=reporting_date_data).values_list('task',flat=True))):
                            '''
                                "request_status": 2 >> User define exception or condition checking by front end
                            '''
                            reporting_date_formet = reporting_date_data.strftime("%m/%d/%Y, %I:%M:%S %p")
                            raise APIException({'msg': reporting_date_formet+' is already blocked on your Calendar',
                                                "request_status": 2
                                                })
                
                default_reporting_dates = EtaskMonthlyReportingDate.objects.filter(employee=validated_data["assign_to"],
                                                            owned_by=validated_data['owner']).values_list('field_value',flat=True)
                
                reporting_date_set = set()
                reporting_date_dict = dict()
                reporting_end_date_dict = dict() 

                if validated_data['task_categories'] != 1:
                    reporting_date_dict.update({str(validated_data['end_date'].date()):str(validated_data['end_date'].replace(hour=10, minute=00).strftime("%Y-%m-%dT%H:%M:%S"))})
                    reporting_end_date_dict.update({str(validated_data['end_date'].date()):str(validated_data['end_date'].replace(hour=10, minute=00).strftime("%Y-%m-%dT%H:%M:%S"))})
                    reporting_date_set.add(str(validated_data['end_date'].date()))
                    
                    reporting_date_set.update({rd['reporting_date'].split('T')[0] for rd in reporting_date})
                    reporting_date_dict.update({rd['reporting_date'].split('T')[0]: rd['reporting_date'].split('.')[0] for rd in reporting_date})
                    reporting_end_date_dict.update({rd['reporting_end_date'].split('T')[0]: rd['reporting_end_date'].split('.')[0] for rd in reporting_date})
                    reporting_date_with_manual_time = {rd['reporting_date'].split('T')[0]: rd['is_manual_time_entry'] for rd in reporting_date}
                    
                    if validated_data['task_priority'] == 1:
                        for date_ob in daterange(validated_data['start_date'].date(),validated_data['end_date'].date()):

                            if date_ob.day in default_reporting_dates and date_ob >= current_date.date():
                                print(date_ob, type(date_ob))
                                reporting_date_set.add(str(date_ob))
                                default_reporting_date = EtaskMonthlyReportingDate.objects.filter(employee=validated_data["assign_to"],
                                                field_value=date_ob.day,owned_by=validated_data['owner']).values('field_value','start_time','end_time').first()
                                
                                reporting_date_dict[str(date_ob)] = str(date_ob)+'T'+str(default_reporting_date['start_time']) if default_reporting_date['start_time'] else str(date_ob)+'T10:00:00'
                                reporting_end_date_dict[str(date_ob)] = str(date_ob)+'T'+str(default_reporting_date['end_time']) if default_reporting_date['end_time'] else str(date_ob)+'T10:00:00'
                                break

                        if not len(reporting_date_set) and not proceed_without_reporting_date:
                            raise APIException({'msg': 'Default reporting date is not in between task start date and end date.',
                                                "request_status": 3
                                                })
                        # elif not len(reporting_date_set) and proceed_without_reporting_date:
                        #     reporting_date_set.add(str(validated_data['end_date'].date()))
                        #     reporting_date_dict[str(validated_data['end_date'].date())] = str(validated_data['end_date'])
                elif validated_data['task_categories'] == 1 and validated_data['task_priority'] == 2:
                    reporting_date_set.update({rd['reporting_date'].split('T')[0] for rd in reporting_date})
                    reporting_date_dict.update({rd['reporting_date'].split('T')[0]: rd['reporting_date'].split('.')[0] for rd in reporting_date})
                    reporting_end_date_dict.update({rd['reporting_end_date'].split('T')[0]: rd['reporting_end_date'].split('.')[0] for rd in reporting_date})
                    reporting_date_with_manual_time = {rd['reporting_date'].split('T')[0]: rd['is_manual_time_entry'] for rd in reporting_date}
                    

                task_create = EtaskTask.objects.create(         
                    **validated_data
                )
                EtaskTask.objects.filter(id=task_create.id).update(task_code_id="TSK"+str(task_create.id))
                #print("task_create.id",task_create.id)

                if followup_date:
                    #print("followup_date",followup_date)
                    if validated_data['task_categories']==1:
                        EtaskFollowUP.objects.get_or_create(task=task_create,assign_to=created_by,follow_up_task=validated_data['task_subject'],
                                                            follow_up_date=followup_date,created_by=created_by)
                    else:
                        if 'assign_to' in validated_data:
                            EtaskFollowUP.objects.get_or_create(task=task_create,follow_up_task=validated_data['task_subject'],
                                                                assign_to=validated_data["assign_to"],follow_up_date=followup_date,created_by=validated_data["assign_to"])
                        if 'owner' in validated_data:
                            EtaskFollowUP.objects.get_or_create(task=task_create,follow_up_task=validated_data['task_subject'],
                                                                assign_to=validated_data['owner'],follow_up_date=followup_date,created_by=validated_data['owner'])
                print('reporting date',reporting_date_dict)
                usercc_list = []
                mail_reporting_date_list = [datetime.strptime(reporting_date_dict[r_date], "%Y-%m-%dT%H:%M:%S").strftime("%d/%m/%Y, %I:%M:%S %p") for i, r_date in enumerate(reporting_date_set)]
                cc_name_list = [userdetails(int(u_cc['user_id'])) for u_cc in user_cc]
                for u_cc in user_cc:
                    ucc_details,created_1 = EtaskUserCC.objects.get_or_create(
                        task = task_create, ** u_cc, created_by=created_by , owned_by = owned_by
                    )
                    ucc_details.__dict__.pop('_state') if "_state" in ucc_details.__dict__.keys() else ucc_details.__dict__
                    usercc_list.append(ucc_details.__dict__)

                    cc_user_name = userdetails(int(u_cc['user_id']))
                    cc_user_email = User.objects.get(id=int(u_cc['user_id'])).cu_user.cu_alt_email_id
                    #cc_name_list.append(cc_user_name)
                    if cc_user_email:
                        mail_data = {
                                    "recipient_name" : cc_user_name,
                                    "task_subject": task_create.task_subject,        ## modified by manas Paul 21jan20
                                    "reporting_date": mail_reporting_date_list,
                                    "assign_to_name": task_create.assign_to.get_full_name(),
                                    "created_by_name": task_create.created_by.get_full_name(),
                                    "created_date_time": task_create.created_at,
                                    "cc_to":','.join(cc_name_list),
                                    "task_priority": task_create.get_task_priority_display(),
                                    "start_date": task_create.start_date.date(),
                                    "end_date": task_create.end_date.date()
                                }
                        # mail_class = GlobleMailSend('ET-CTCCU', [cc_user_email])
                        # mail_thread = Thread(target = mail_class.mailsend, args = (mail_data,))
                        # mail_thread.start()
                        send_mail_list('ET-CTCCU', [cc_user_email], mail_data, ics='')

                reporting_date_list = []
                #print("task_create",task_create.__dict__['id'])
                # #print("r_date['reporting_date']",r_date['reporting_date'])
                reporting_date_str = """"""
                r_time = ''
                ics_data = """BEGIN:VCALENDAR
VERSION:2.0
CALSCALE:GREGORIAN\n"""
                user_name = userdetails(int(task_create.__dict__['assign_to_id']))
                count_id = 0
                print('reporting_date_dict',reporting_date_dict)
                reporting_obj_list = list()

                for r_date in reporting_date_set:
                    rdate_details,created = ETaskReportingDates.objects.get_or_create(
                        task_type=1,
                        task = task_create.__dict__['id'],
                        is_manual_time_entry=reporting_date_with_manual_time.get(r_date,False),
                        reporting_date = datetime.strptime(reporting_date_dict[r_date], "%Y-%m-%dT%H:%M:%S"),
                        reporting_end_date = datetime.strptime(reporting_end_date_dict[r_date], "%Y-%m-%dT%H:%M:%S"),
                        created_by=created_by,
                        owned_by=validated_data['owner']
                    )
                    if created:
                        reporting_obj_list.append(rdate_details)
                    
                    # #print('rdate_details',rdate_details,type(rdate_details))
                    reporting_log,created=ETaskReportingActionLog.objects.get_or_create(
                                                                                        task_id = task_create.__dict__['id'],
                                                                                        reporting_date_id =str(rdate_details),
                                                                                        updated_date=datetime.now().date(),
                                                                                        status=2,
                                                                                        created_by=created_by,
                                                                                        owned_by=validated_data['owner']
                                                                                    )
                    # #print('reporting_log',reporting_log)

                    rdate_details.__dict__.pop('_state') if "_state" in rdate_details.__dict__.keys() else rdate_details.__dict__
                    reporting_date_list.append(rdate_details.__dict__)
                    ###################################################
                    count_id += 1
                    # reporting_date_str += datetime.strptime(x['reporting_date'], "%m/%d/%Y, %I:%M:%S %p")+'\n'
                    reporting_date_str += str(count_id)+'. '+rdate_details.__dict__['reporting_date'].strftime("%m/%d/%Y, %I:%M:%S %p")+" "
                    # mail_reporting_date_list.append(str(count_id)+'. '+rdate_details.__dict__['reporting_date'].strftime("%m/%d/%Y, %I:%M:%S %p"))
                    r_time = rdate_details.__dict__['reporting_date'].strftime("%Y%m%dT%H%M%S")
                    ics_data +=   """BEGIN:VEVENT
SUMMARY:Reporting of {rep_sub}
DTSTART;TZID=Asia/Kolkata:{r_time}
LOCATION:Shyam Tower,Kolkata-700091
DESCRIPTION: Reporting dates.
STATUS:CONFIRMED
SEQUENCE:3
BEGIN:VALARM
TRIGGER:-PT10M
DESCRIPTION:Pickup Reminder
ACTION:DISPLAY
END:VALARM
END:VEVENT\n""".replace("{r_time}",r_time).replace("{rep_sub}",task_create.__dict__['task_subject'])


                
                ##############################################################
                #DTEND;TZID=Asia/Kolkata:{r_time}
                ics_data += "END:VCALENDAR"
                #print("reporting_date_str",reporting_date_str)
                # email change to TCoreUserDetail email
                user_email = User.objects.get(id=task_create.__dict__['assign_to_id']).cu_user.cu_alt_email_id
                #print("user_email",user_email)
                
                if validated_data['task_categories'] != 1 and user_email:
                    mail_data = {
                                "recipient_name" : user_name,
                                "task_subject": task_create.task_subject,
                                "reporting_date": mail_reporting_date_list,
                                "assign_to_name": task_create.assign_to.get_full_name(),
                                "on_behalf_of": task_create.assign_by.get_full_name() if task_create.task_categories==2 else None,
                                "created_by_name": task_create.created_by.get_full_name(),
                                "created_date_time": task_create.created_at,
                                "cc_to":','.join(cc_name_list),
                                "task_priority": task_create.get_task_priority_display(),
                                "start_date": task_create.start_date.date(),
                                "end_date": task_create.end_date.date()
                            }
                    # #print('mail_data',mail_data)
                    # #print('mail_id-->',mail)
                    # #print('mail_id-->',[mail])
                    # mail_class = GlobleMailSend('ETAP', email_list)
                    # mail_class = GlobleMailSend('ETRDC', [user_email])
                    # #print('mail_class',mail_class)
                    # mail_thread = Thread(target = mail_class.mailsend, args = (mail_data,ics_data))
                    # #print('mail_thread-->',mail_thread)
                    # mail_thread.start()
                    send_mail_list('ETRDC', [user_email], mail_data, ics=ics_data)
                ######################################  

                # Creating and mail appointment
                create_appointment(reporting_dates=reporting_obj_list)
                
                validated_data['user_cc']=usercc_list
                # validated_data['assignto']=assignto_list
                validated_data['reporting_date']=reporting_date_list

                '''
                Rajesh Samui
                03/07/2020
                Topic :: Sending Notification
                '''

                users = [task_create.assign_to]
                title = 'A new task has been created.'
                body ='Task: {} \nDetails:{}'.format(task_create.task_subject,task_create.task_description)

                data = {
                            "app_module":"etask",
                            "type":"task",
                            "id":task_create.id
                        }
                data_str = json.dumps(data)
                if validated_data['task_categories'] != 1:
                    notification_id = store_sent_notification(users=users,body=body,title=title,data=data_str,app_module_name='etask')
                    send_notification(users=users,body=body,title=title,data=data,notification_id=notification_id)
                
                return validated_data

        except Exception as e:
            raise e


class EtaskTaskRepostSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    assign_to_name = serializers.SerializerMethodField()
    assign_by_name = serializers.SerializerMethodField()
    owner_name = serializers.SerializerMethodField()
    reporting_dates = serializers.SerializerMethodField()

    def get_assign_to_name(self, EtaskTask):
        name = None
        full_name = ""
        if EtaskTask.assign_to:
            name = User.objects.get(id=EtaskTask.assign_to.id)
            if name:
                full_name = name.__dict__['first_name'] + " " + name.__dict__['last_name']
                # #print("full_name",full_name)
            return full_name

    def get_assign_by_name(self, EtaskTask):
        name = None
        full_name = ""
        if EtaskTask.assign_by:
            name = User.objects.get(id=EtaskTask.assign_by.id)
            if name:
                full_name = name.__dict__['first_name'] + " " + name.__dict__['last_name']
                # #print("full_name",full_name)
            return full_name
    def get_owner_name(self, EtaskTask):
        name = None
        full_name = ""
        if EtaskTask.assign_by:
            name = User.objects.get(id=EtaskTask.owner.id)
            if name:
                full_name = name.__dict__['first_name'] + " " + name.__dict__['last_name']
                # #print("full_name",full_name)
            return full_name

    def get_reporting_dates(self, EtaskTask):
        if EtaskTask.id:
            report_date_list = []
            report_date = ETaskReportingDates.objects.filter( task=EtaskTask.id, is_deleted=False)
            # #print("report_date",report_date)
            current_date = datetime.now().date()
            if report_date:
                for dt in report_date:
                    pre_report = dt.reporting_date.date()
                    # #print('pre_report',pre_report)
                    if dt.reporting_status == 2:
                        days_count = (current_date - pre_report).days
                        #print('days_count', days_count)
                    else:
                        days_count = 0
                    dt_dict = {
                        'id': dt.id,
                        'reporting_date': dt.reporting_date,
                        'reporting_status': dt.reporting_status,
                        'reporting_status_name': dt.get_reporting_status_display(),
                        'crossed_by': days_count
                    }
                    report_date_list.append(dt_dict)

                return report_date_list
            else:
                return []



    class Meta:
        model = EtaskTask
        fields = '__all__'
        extra_fields = ('assign_to_name', 'assign_by_name', 'owner_name','reporting_dates')


class EtaskTaskRepostSerializerV2(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    assign_to_name = serializers.SerializerMethodField()
    assign_by_name = serializers.SerializerMethodField()
    owner_name = serializers.SerializerMethodField()
    reporting_dates = serializers.SerializerMethodField()
    task_priority_name = serializers.CharField(source='get_task_priority_display')
    recurrance_frequency_name = serializers.CharField(source='get_recurrance_frequency_display')
    task_categories_name = serializers.CharField(source='get_task_categories_display')
    task_status_name = serializers.CharField(source='get_task_status_display')
    task_flag = serializers.SerializerMethodField()
    sub_assign_to_name = serializers.SerializerMethodField()
    extended_dates = serializers.SerializerMethodField()
    task_assign_flow = serializers.SerializerMethodField()
    sub_tasks = serializers.SerializerMethodField()
    task_flag = serializers.SerializerMethodField()
    overdue_by = serializers.SerializerMethodField()
    status_with_pending_request = serializers.SerializerMethodField()

    class Meta:
        model = EtaskTask
        fields = '__all__'
        extra_fields = ('assign_to_name', 'assign_by_name', 'owner_name','reporting_dates','task_categories_name',
                        'task_assign_flow','task_status_name','task_flag','sub_assign_to_name','extended_dates',
                        'sub_tasks','task_flag','overdue_by','status_with_pending_request')

    def get_overdue_by(self, obj):
        cur_date=datetime.now().date()
        overdue_by = None
        if obj.extended_date:
            if obj.extended_date and obj.extended_date.date() <= cur_date:
                extended_date = obj.extended_date.date()
                days_extended=(cur_date - extended_date).days
                #print("days_extended",days_extended,type(days_extended))
                if days_extended==1:
                    overdue_by = str(days_extended)+" day"
                elif days_extended >1:
                    overdue_by = str(days_extended)+" days"
                else:
                    overdue_by = None
        else:
            if obj.end_date and obj.end_date.date() <= cur_date:
                end_date = obj.end_date.date()
                days_extended=(cur_date - end_date).days
                #print("days_extended",days_extended,type(days_extended))
                if days_extended ==1:
                    overdue_by = str(days_extended)+" day"
                elif days_extended >1:
                    overdue_by = str(days_extended)+" days"
                else:
                    overdue_by = None
        return overdue_by

    def get_status_with_pending_request(self, obj):
        status = list()
        task_extention = TaskExtentionDateMap.objects.filter(task=obj, status=1)
        if task_extention.count():
            status.append('Pending Extention')
        task_closer = TaskCompleteReopenMap.objects.filter(task=obj,status=1)
        if task_closer.count():
            status.append('Pending Closure')
        if (obj.task_status == 1 or obj.task_status == 4) and not task_extention.count() and not task_extention.count():
            status.append(obj.get_task_status_display())
        return ' and '.join(status)

    def get_sub_tasks(self, obj):
        sub_tasks_data = EtaskTask.objects.filter(~Q(task_status=4),parent_id=obj.id,is_deleted=False).values('id','task_subject')
        return sub_tasks_data if sub_tasks_data else list() 

    def get_task_assign_flow(self, obj):
        assign_user = [{'id':user.id,'name':user.get_full_name()} for user in [obj.assign_by,obj.assign_to]]
        if obj.sub_assign_to_user:
            sub_assign_uaers = EtaskTaskSubAssignLog.objects.filter(task=obj,is_deleted=False)
            for sub_assign_uaer in sub_assign_uaers:
                assign_user.append({'id':sub_assign_uaer.sub_assign.id,'name':sub_assign_uaer.sub_assign.get_full_name()})
        return assign_user

    def get_extended_dates(self, obj):
        extended_date_list = list(TaskExtentionDateMap.objects.filter(task=obj,status=2).values('extended_date','extend_with_delay'))
        if not len(extended_date_list) and obj.extended_date:
            extended_date_list.append({'extended_date':obj.extended_date,'extend_with_delay':obj.extend_with_delay})
        return extended_date_list

    def get_task_flag(self, obj):
        TASK_TYPES = ('overdue', 'ongoing', 'upcomming')
        cur_date=datetime.now().date()
        task_flag = None
        
        if (obj.extended_date is not None and obj.extended_date.date() < cur_date) or (obj.extended_date is None and obj.end_date.date() < cur_date):
            task_flag = TASK_TYPES[0]
        elif (obj.shifted_date is not None and obj.shifted_date.date() <= cur_date) or (obj.shifted_date is None and obj.start_date.date() <= cur_date):
            task_flag = TASK_TYPES[1]
        elif (obj.shifted_date is not None and obj.shifted_date.date() > cur_date) or (obj.shifted_date is None and obj.start_date.date() > cur_date):
            task_flag = TASK_TYPES[2]
        return None if obj.task_status == 4 else task_flag

    def get_assign_to_name(self, EtaskTask):
        name = None
        full_name = ""
        if EtaskTask.assign_to:
            name = User.objects.get(id=EtaskTask.assign_to.id)
            if name:
                full_name = name.__dict__['first_name'] + " " + name.__dict__['last_name']
                # #print("full_name",full_name)
            return full_name

    def get_sub_assign_to_name(self, EtaskTask):
        name = None
        full_name = ""
        if EtaskTask.sub_assign_to_user:
            name = User.objects.get(id=EtaskTask.sub_assign_to_user.id)
            if name:
                full_name = name.__dict__['first_name'] + " " + name.__dict__['last_name']
                # #print("full_name",full_name)
            return full_name


    def get_assign_by_name(self, EtaskTask):
        name = None
        full_name = ""
        if EtaskTask.assign_by:
            name = User.objects.get(id=EtaskTask.assign_by.id)
            if name:
                full_name = name.__dict__['first_name'] + " " + name.__dict__['last_name']
                # #print("full_name",full_name)
            return full_name
    def get_owner_name(self, EtaskTask):
        name = None
        full_name = ""
        if EtaskTask.assign_by:
            name = User.objects.get(id=EtaskTask.owner.id)
            if name:
                full_name = name.__dict__['first_name'] + " " + name.__dict__['last_name']
                # #print("full_name",full_name)
            return full_name

    def get_reporting_dates(self, EtaskTask):
        if EtaskTask.id:
            report_date_list = []
            report_date = ETaskReportingDates.objects.filter(owned_by=EtaskTask.assign_by,task=EtaskTask.id, is_deleted=False).order_by('reporting_date')
            # #print("report_date",report_date)
            current_date = datetime.now().date()
            if report_date:
                for dt in report_date:
                    pre_report = dt.reporting_date.date()
                    # #print('pre_report',pre_report)
                    if dt.reporting_status == 2:
                        days_count = (current_date - pre_report).days
                        #print('days_count', days_count)
                    else:
                        days_count = 0
                    dt_dict = {
                        'id': dt.id,
                        'reporting_date': dt.reporting_date,
                        'reporting_status': dt.reporting_status,
                        'reporting_status_name': dt.get_reporting_status_display(),
                        'crossed_by': days_count
                    }
                    report_date_list.append(dt_dict)

                return report_date_list
            else:
                return []


class EtaskTaskEditSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    user_cc = serializers.ListField(required=False)
    assignto = serializers.ListField(required=False)
    reporting_date = serializers.ListField(required=False)
    reporting_date_new = serializers.ListField(required=False)
    is_forcefully = serializers.BooleanField(required=False)
    followup_date = serializers.DateTimeField(required=False)
    class Meta:
        model = EtaskTask
        fields = '__all__'
        extra_fields = ('user_cc','assignto','reporting_date','reporting_date_new')
    
    def update(self,instance,validated_data):
        try:
            with transaction.atomic():
                created_by = validated_data.get('created_by')
                owned_by = validated_data.get('owned_by')
                updated_by = validated_data.get('updated_by')
                
                is_forcefully = validated_data.pop('is_forcefully') if 'is_forcefully' in validated_data.keys() else False
                followup_date = validated_data.pop('followup_date') if 'followup_date' in validated_data.keys() else None
                # followup_date = datetime.strptime(validated_data.pop('followup_date'), "%Y-%m-%dT%H:%M:%S.%fZ") if 'followup_date' in validated_data else None
                ##print("followup_date",followup_date)
                user_cc = validated_data.pop('user_cc') if 'user_cc' in validated_data else ""
                # assignto = validated_data.pop('assignto') if 'assignto' in validated_data else ""
                reporting_date = validated_data.pop('reporting_date') if 'reporting_date' in validated_data else ""
                reporting_date_new = validated_data.pop('reporting_date_new') if 'reporting_date_new' in validated_data else ""

                ##print("validated_data['task_categories']", validated_data['start_date'])

                if validated_data['task_type'] in [3,4]:
                    start_date_data = validated_data['start_date'].date()
                    end_date_data = validated_data['end_date'].date()
                    if EtaskTask.objects.filter(
                        start_date__date__lte=start_date_data,
                        end_date__date__gte=end_date_data,
                        id=validated_data['parent_id']):
                        #print("PROPER TIME")
                        pass
                    else:
                        raise APIException({'msg':'Please put Task date in between parent task date range',
                                    "request_status": 0
                                    })


                if validated_data['task_categories']==1:
                    validated_data["owner"]=updated_by
                    validated_data["assign_by"]= updated_by
                    validated_data["assign_to"]= updated_by

                elif validated_data['task_categories']==2:
                    validated_data["assign_by"]=validated_data['owner']
                    validated_data["assign_to"]=updated_by

                elif validated_data['task_categories']==3: # task_categories - assign_to
                    validated_data["assign_by"]=updated_by
                    validated_data['owner']=updated_by  
                    
                # EtaskTask get data and create EtaskTaskEditLog by previous data 
                if validated_data['task_categories' ]== 2 or validated_data['task_categories'] == 3:
                    existTask = EtaskTask.objects.get(pk=instance.id)
                    etaskTaskEditLog_create_dict = {
                        'task' : instance,
                        'parent_id':existTask.parent_id,
                        'owner':existTask.owner,
                        'assign_to':existTask.assign_to,
                        'assign_by':existTask.assign_by,
                        'task_subject':existTask.task_subject,
                        'task_description':existTask.task_description,
                        'task_categories':existTask.task_categories,
                        'start_date':existTask.start_date,
                        'end_date':existTask.end_date,
                        'requested_end_date':existTask.requested_end_date,
                        'requested_comment':existTask.requested_comment,
                        'requested_by':existTask.requested_by,
                        'is_closure':existTask.is_closure,
                        'is_reject':existTask.is_reject,
                        'is_transferred':existTask.is_transferred,
                        'transferred_from':existTask.transferred_from,
                        'date_of_transfer':existTask.date_of_transfer,
                        'completed_date':existTask.completed_date,
                        'completed_by':existTask.completed_by,
                        'closed_date':existTask.closed_date,
                        'extended_date':existTask.extended_date,
                        'extend_with_delay':existTask.extend_with_delay,
                        'task_priority': existTask.task_priority,
                        'task_type':existTask.task_type,
                        'task_status':existTask.task_status,
                        'recurrance_frequency':existTask.recurrance_frequency,
                        'sub_assign_to_user':existTask.sub_assign_to_user,
                        'created_by':existTask.created_by,
                        'owned_by':existTask.owned_by
                    }
                    new_instance = EtaskTaskEditLog.objects.create(**etaskTaskEditLog_create_dict)
                             

            ### Etask Created modified By Manas Paul,[ get_or_create --> create ], Cause Tak Subject can not possible to create same Subject ###
            ### Changing approved by Tonmoy Sardar ###
                if validated_data["assign_to"] and reporting_date != "" and is_forcefully is False:
                    ##print('validated_data["assign_to"]',validated_data["assign_to"])
                    for report_dt in reporting_date_new:
                        reporting_date_data = datetime.strptime(report_dt['reporting_date'], "%Y-%m-%dT%H:%M:%S.%fZ")
                        ##print('reporting_date_data',reporting_date_data)
                        if EtaskTask.objects.filter(Q(Q(task_status=1)|Q(task_status=3)),
                                                            Q(Q(assign_to_id=validated_data["assign_to"])|
                                                            Q(sub_assign_to_user_id=validated_data["assign_to"])),
                                                            id__in=list(ETaskReportingDates.objects.filter(task_type=1,reporting_status=2,
                                                            reporting_date=reporting_date_data).values_list('task',flat=True))):
                            '''
                                "request_status": 2 >> User define exception or condition checking by front end
                            '''
                            reporting_date_formet = reporting_date_data.strftime("%m/%d/%Y, %I:%M:%S %p")
                            raise APIException({'msg': reporting_date_formet+' is already blocked on your Calendar',
                                                "request_status": 2
                                                })
                    

                
                ##print('task filtrer....',EtaskTask.objects.filter(pk=instance.id))
                task_update1 = EtaskTask.objects.filter(         
                   pk=instance.id
                ).update(**validated_data)
                ##print("task_update.id",task_update1,type(task_update1))
                task_update = EtaskTask.objects.get(pk=instance.id)
                ##print('task_update_assign_to',task_update.assign_to.id)
                
                if followup_date:
                    existEtaskFollowUP = EtaskFollowUP.objects.filter(task=instance)
                        ##print('existEtaskFollowUP',existEtaskFollowUP)
                    if existEtaskFollowUP:
                        for existEtaskFollowUP_e in existEtaskFollowUP:
                            #existEtaskFollowUP = EtaskFollowUP.objects.get(task=instance)
                            existEtaskFollowUP_dict = {
                                'follow_up_task':existEtaskFollowUP_e.follow_up_task,
                                'task':existEtaskFollowUP_e.task,
                                'assign_to':existEtaskFollowUP_e.assign_to,
                                'assign_for':existEtaskFollowUP_e.assign_for,
                                'follow_up_date':existEtaskFollowUP_e.follow_up_date,
                                'followup_status':existEtaskFollowUP_e.followup_status,
                                'completed_date':existEtaskFollowUP_e.completed_date,
                                'created_by':existEtaskFollowUP_e.created_by,
                                'owned_by':existEtaskFollowUP_e.owned_by
                            }
                            EtaskFollowUPEdit.objects.get_or_create(**existEtaskFollowUP_dict)
                    if validated_data['task_categories']==1:
                        EtaskFollowUP.objects.filter(task=instance).delete()
                        EtaskFollowUP.objects.create(task=instance,assign_to=created_by,follow_up_task=validated_data['task_subject'],
                                                            follow_up_date=followup_date,created_by=created_by)
                    else:
                       
                        if 'assign_to' in validated_data:
                            
                            EtaskFollowUP.objects.filter(task=instance).delete()
                            EtaskFollowUP.objects.create(task=instance,follow_up_task=validated_data['task_subject'],
                                                                assign_to=validated_data["assign_to"],follow_up_date=followup_date,created_by=validated_data["assign_to"])
                        
                        if 'owner' in validated_data:
                            EtaskFollowUP.objects.filter(task=instance).delete()
                            EtaskFollowUP.objects.create(task=instance,follow_up_task=validated_data['task_subject'],
                                                                assign_to=validated_data['owner'],follow_up_date=followup_date,created_by=validated_data['owner'])
                
                usercc_list = []
                if user_cc:
                    existEtaskuser_cc = EtaskUserCC.objects.filter(task=instance)
                    ##print('existEtaskuser_cc',existEtaskuser_cc)
                    if existEtaskuser_cc:
                        #existEtaskuser_cc = EtaskUserCC.objects.filter(task=instance)
                        for u_cc in existEtaskuser_cc:
                            ##print('u_cc',u_cc)
                            existEtaskuser_cc_dict = {
                                'task':u_cc.task,
                                'user':u_cc.user,
                                'created_by':u_cc.created_by,
                                'owned_by':u_cc.owned_by
                            }
                            ##print('existEtaskuser_cc_dict',existEtaskuser_cc_dict)
                            EtaskUserCCEdit.objects.get_or_create(**existEtaskuser_cc_dict)

                    EtaskUserCC.objects.filter(task = instance).delete()
                    for u_cc in user_cc:
                        ucc_details= EtaskUserCC.objects.create(task=instance,
                            ** u_cc, created_by=created_by , owned_by = owned_by
                        )
                        ucc_details.__dict__.pop('_state') if "_state" in ucc_details.__dict__.keys() else ucc_details.__dict__
                        usercc_list.append(ucc_details.__dict__)
                
                reporting_date_list = []
                ##print("task_create",task_create.__dict__['id'])
                reporting_date_str = """"""
                r_time = ''
                ics_data = """BEGIN:VCALENDAR
VERSION:2.0
CALSCALE:GREGORIAN\n"""
                user_name = userdetails(int(task_update.assign_to.id))
                count_id = 0
                

                existETaskReportingDates = ETaskReportingDates.objects.filter(task=task_update.id)
                if existETaskReportingDates:
                    for r_date in existETaskReportingDates:
                        existETaskReportingDates_dict = {
                            'task_type':r_date.task_type,
                            'task':int(task_update.id),
                            'reporting_date':r_date.reporting_date,
                            'actual_reporting_date':r_date.actual_reporting_date,
                            'reporting_status':r_date.reporting_status,
                            'created_by':r_date.created_by,
                            'owned_by':r_date.owned_by
                        }
                        ETaskReportingDatesEdit.objects.get_or_create(**existETaskReportingDates_dict)

                existETaskReportingActionLogEdit = ETaskReportingActionLog.objects.filter(task=task_update.id)
                ##print('existETaskReportingActionLogEdit',existETaskReportingActionLogEdit)
                if existETaskReportingActionLogEdit:
                    for r_date_action in existETaskReportingActionLogEdit:
                        ##print('r_date_action',r_date_action.task)
                        existETaskReportingActionLogEdit_dict = {
                            'task':r_date_action.task,
                            'reporting_date':r_date_action.reporting_date,
                            'updated_date':r_date_action.updated_date,
                            'status':r_date_action.status,
                            'created_by':r_date_action.created_by,
                            'owned_by':r_date_action.owned_by
                        }
                        #print('existETaskReportingActionLogEdit_dict',existETaskReportingActionLogEdit_dict)
                        ETaskReportingActionLogEdit.objects.get_or_create(**existETaskReportingActionLogEdit_dict)
                        ##print('ssssd',sddsd)
                        
                        


                ETaskReportingDates.objects.filter(task = task_update.id).delete()
                ETaskReportingActionLog.objects.filter(task = task_update).delete()
                for r_date in reporting_date:
                    rdate_details,created = ETaskReportingDates.objects.get_or_create(
                        task_type=1,
                        task = task_update.id,
                        reporting_date = datetime.strptime(r_date['reporting_date'], "%Y-%m-%dT%H:%M:%S.%fZ"),
                        created_by=created_by,
                        owned_by=owned_by
                    )
                    #print('rdate_details',rdate_details,type(rdate_details))

                    reporting_log, created=ETaskReportingActionLog.objects.get_or_create(task_id = task_update.id,
                                                                                        reporting_date_id =str(rdate_details),
                                                                                        updated_date=datetime.now().date(),
                                                                                        status=2,
                                                                                        created_by=created_by,
                                                                                        owned_by=owned_by
                                                                                    )
                    # #print('reporting_log',reporting_log)

                    rdate_details.__dict__.pop('_state') if "_state" in rdate_details.__dict__.keys() else rdate_details.__dict__
                    reporting_date_list.append(rdate_details.__dict__)
                    ###################################################
                    count_id += 1
                    # reporting_date_str += datetime.strptime(x['reporting_date'], "%m/%d/%Y, %I:%M:%S %p")+'\n'
                    reporting_date_str += str(count_id)+'. '+rdate_details.__dict__['reporting_date'].strftime("%m/%d/%Y, %I:%M:%S %p")+" "
                    r_time = rdate_details.__dict__['reporting_date'].strftime("%Y%m%dT%H%M%S")
                    ics_data +=   """BEGIN:VEVENT
SUMMARY:Reporting of {rep_sub}
DTSTART;TZID=Asia/Kolkata:{r_time}
LOCATION:Shyam Tower,Kolkata-700091
DESCRIPTION: Reporting dates.
STATUS:CONFIRMED
SEQUENCE:3
BEGIN:VALARM
TRIGGER:-PT10M
DESCRIPTION:Pickup Reminder
ACTION:DISPLAY
END:VALARM
END:VEVENT\n""".replace("{r_time}",r_time).replace("{rep_sub}",task_update.__dict__['task_subject'])


                
                ##############################################################
                #DTEND;TZID=Asia/Kolkata:{r_time}
                ics_data += "END:VCALENDAR"
                #print("reporting_date_str",reporting_date_str)
                #print("assign_id",task_update.assign_to.id)
                user_email = User.objects.get(id=task_update.assign_to.id).cu_user.cu_alt_email_id
                #print("user_email",user_email)
                
                if user_email:
                    mail_data = {
                                "recipient_name" : user_name,        ## modified by manas Paul 21jan20
                                "task_subject": task_update.task_subject,
                                "reporting_date": reporting_date_str,
                            }
                    # #print('mail_data',mail_data)
                    # #print('mail_id-->',mail)
                    # #print('mail_id-->',[mail])
                    #mail_class = GlobleMailSend('ETAP', email_list)
                    # mail_class = GlobleMailSend('ETRDC', [user_email])
                    # #print('mail_class',mail_class)
                    # mail_thread = Thread(target = mail_class.mailsend, args = (mail_data,ics_data))
                    # #print('mail_thread-->',mail_thread)
                    # mail_thread.start()
                    send_mail_list('ETRDC', [user_email], mail_data, ics=ics_data)
                ######################################  

                validated_data['user_cc']=usercc_list
                # validated_data['assignto']=assignto_list
                validated_data['reporting_date']=reporting_date_list
                return validated_data

        except Exception as e:
            raise e
            # raise APIException({'request_status': 0, 'msg': e})


class EtaskTaskEditSerializerV2(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    user_cc = serializers.ListField(required=False)
    assignto = serializers.ListField(required=False)
    reporting_date = serializers.ListField(required=False)
    reporting_date_new = serializers.ListField(required=False)
    is_forcefully = serializers.BooleanField(required=False)
    followup_date = serializers.DateTimeField(required=False)

    class Meta:
        model = EtaskTask
        fields = '__all__'
        extra_fields = ('user_cc','assignto','reporting_date','reporting_date_new')

    def update(self,instance,validated_data):
        try:
            with transaction.atomic():
                created_by = validated_data.get('created_by')
                owned_by = validated_data.get('owned_by')
                updated_by = validated_data.get('updated_by')
                
                is_forcefully = validated_data.pop('is_forcefully') if 'is_forcefully' in validated_data.keys() else False
                followup_date = validated_data.pop('followup_date') if 'followup_date' in validated_data.keys() else None
                # followup_date = datetime.strptime(validated_data.pop('followup_date'), "%Y-%m-%dT%H:%M:%S.%fZ") if 'followup_date' in validated_data else None
                ##print("followup_date",followup_date)
                user_cc = validated_data.pop('user_cc') if 'user_cc' in validated_data else ""
                # assignto = validated_data.pop('assignto') if 'assignto' in validated_data else ""
                reporting_date = validated_data.pop('reporting_date') if 'reporting_date' in validated_data else ""
                reporting_date_new = validated_data.pop('reporting_date_new') if 'reporting_date_new' in validated_data else ""
                # start_date_new = validated_data.pop('start_date_new') if 'start_date_new' in validated_data else ""
                ##print("validated_data['task_categories']", validated_data['start_date'])

                if validated_data['task_type']==3:
                    start_date_data = validated_data['start_date'].date()
                    end_date_data = validated_data['end_date'].date()
                    if EtaskTask.objects.filter((Q(Q(extended_date__isnull=False)&Q(extended_date__date__gte=end_date_data))
                                                |Q(Q(extended_date__isnull=True)&Q(end_date__date__gte=end_date_data))),
                                                start_date__date__lte=start_date_data,id=validated_data['parent_id']):
                        #print("PROPER TIME")
                        pass
                    else:
                        raise APIException({'msg':'Please put Task date in between parent task date range',
                                    "request_status": 0
                                    })


                if validated_data['task_categories']==1:
                    validated_data["owner"]=updated_by
                    validated_data["assign_by"]= updated_by
                    validated_data["assign_to"]= updated_by

                elif validated_data['task_categories']==2:
                    validated_data["assign_by"]=instance.assign_by
                    validated_data["assign_to"]=instance.assign_to

                elif validated_data['task_categories']==3: # task_categories - assign_to
                    validated_data["assign_by"]=updated_by
                    validated_data['owner']=updated_by  
                    
                # EtaskTask get data and create EtaskTaskEditLog by previous data 
                if validated_data['task_categories' ]== 2 or validated_data['task_categories'] == 3:
                    existTask = EtaskTask.objects.get(pk=instance.id)
                    etaskTaskEditLog_create_dict = {
                        'task' : instance,
                        'parent_id':existTask.parent_id,
                        'owner':existTask.owner,
                        'assign_to':existTask.assign_to,
                        'assign_by':existTask.assign_by,
                        'task_subject':existTask.task_subject,
                        'task_description':existTask.task_description,
                        'task_categories':existTask.task_categories,
                        'start_date':existTask.start_date,
                        'end_date':existTask.end_date,
                        'requested_end_date':existTask.requested_end_date,
                        'requested_comment':existTask.requested_comment,
                        'requested_by':existTask.requested_by,
                        'is_closure':existTask.is_closure,
                        'is_reject':existTask.is_reject,
                        'is_transferred':existTask.is_transferred,
                        'transferred_from':existTask.transferred_from,
                        'date_of_transfer':existTask.date_of_transfer,
                        'completed_date':existTask.completed_date,
                        'completed_by':existTask.completed_by,
                        'closed_date':existTask.closed_date,
                        'extended_date':existTask.extended_date,
                        'extend_with_delay':existTask.extend_with_delay,
                        'task_priority': existTask.task_priority,
                        'task_type':existTask.task_type,
                        'task_status':existTask.task_status,
                        'recurrance_frequency':existTask.recurrance_frequency,
                        'sub_assign_to_user':existTask.sub_assign_to_user,
                        'created_by':existTask.created_by,
                        'owned_by':existTask.owned_by
                    }
                    new_instance = EtaskTaskEditLog.objects.create(**etaskTaskEditLog_create_dict)
                             

            ### Etask Created modified By Manas Paul,[ get_or_create --> create ], Cause Tak Subject can not possible to create same Subject ###
            ### Changing approved by Tonmoy Sardar ###
                if validated_data['task_categories'] !=1 and validated_data["assign_to"] and reporting_date != "" and is_forcefully is False:
                    ##print('validated_data["assign_to"]',validated_data["assign_to"])
                    for report_dt in reporting_date_new:
                        reporting_date_data = datetime.strptime(report_dt['reporting_date'], "%Y-%m-%dT%H:%M:%S.%fZ")
                        ##print('reporting_date_data',reporting_date_data)
                        if EtaskTask.objects.filter(Q(Q(task_status=1)|Q(task_status=3)),
                                                            Q(Q(assign_to_id=validated_data["assign_to"])|
                                                            Q(sub_assign_to_user_id=validated_data["assign_to"])),
                                                            id__in=list(ETaskReportingDates.objects.filter(task_type=1,reporting_status=2,
                                                            reporting_date=reporting_date_data).values_list('task',flat=True))):
                            '''
                                "request_status": 2 >> User define exception or condition checking by front end
                            '''
                            reporting_date_formet = reporting_date_data.strftime("%m/%d/%Y, %I:%M:%S %p")
                            raise APIException({'msg': reporting_date_formet+' is already blocked on your Calendar',
                                                "request_status": 2
                                                })
                    

                
                ##print('task filtrer....',EtaskTask.objects.filter(pk=instance.id))
                task_update1 = EtaskTask.objects.filter(         
                   pk=instance.id
                ).update(**validated_data)
                ##print("task_update.id",task_update1,type(task_update1))
                task_update = EtaskTask.objects.get(pk=instance.id)
                ##print('task_update_assign_to',task_update.assign_to.id)
                if task_update.task_type == 1 or task_update.task_type == 3:
                    task_update.recurrance_frequency = None
                    task_update.save()

                if followup_date:
                    existEtaskFollowUP = EtaskFollowUP.objects.filter(task=instance)
                        ##print('existEtaskFollowUP',existEtaskFollowUP)
                    if existEtaskFollowUP:
                        for existEtaskFollowUP_e in existEtaskFollowUP:
                            #existEtaskFollowUP = EtaskFollowUP.objects.get(task=instance)
                            existEtaskFollowUP_dict = {
                                'follow_up_task':existEtaskFollowUP_e.follow_up_task,
                                'task':existEtaskFollowUP_e.task,
                                'assign_to':existEtaskFollowUP_e.assign_to,
                                'assign_for':existEtaskFollowUP_e.assign_for,
                                'follow_up_date':existEtaskFollowUP_e.follow_up_date,
                                'followup_status':existEtaskFollowUP_e.followup_status,
                                'completed_date':existEtaskFollowUP_e.completed_date,
                                'created_by':existEtaskFollowUP_e.created_by,
                                'owned_by':existEtaskFollowUP_e.owned_by
                            }
                            EtaskFollowUPEdit.objects.get_or_create(**existEtaskFollowUP_dict)
                    if validated_data['task_categories']==1:
                        EtaskFollowUP.objects.filter(task=instance).delete()
                        EtaskFollowUP.objects.create(task=instance,assign_to=created_by,follow_up_task=validated_data['task_subject'],
                                                            follow_up_date=followup_date,created_by=created_by)
                    else:
                       
                        if 'assign_to' in validated_data:
                            
                            EtaskFollowUP.objects.filter(task=instance).delete()
                            EtaskFollowUP.objects.create(task=instance,follow_up_task=validated_data['task_subject'],
                                                                assign_to=validated_data["assign_to"],follow_up_date=followup_date,created_by=validated_data["assign_to"])
                        
                        if 'owner' in validated_data:
                            EtaskFollowUP.objects.filter(task=instance).delete()
                            EtaskFollowUP.objects.create(task=instance,follow_up_task=validated_data['task_subject'],
                                                                assign_to=validated_data['owner'],follow_up_date=followup_date,created_by=validated_data['owner'])
                
                
                mail_reporting_date_list = [datetime.strptime(r_date['reporting_date'], "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%d/%m/%Y, %I:%M:%S %p") for i, r_date in enumerate(reporting_date)]
                cc_name_list = [userdetails(int(u_cc['user_id'])) for u_cc in user_cc] if user_cc else []
                usercc_list = []
                if user_cc:
                    existEtaskuser_cc = EtaskUserCC.objects.filter(task=instance)
                    ##print('existEtaskuser_cc',existEtaskuser_cc)
                    if existEtaskuser_cc:
                        #existEtaskuser_cc = EtaskUserCC.objects.filter(task=instance)
                        for u_cc in existEtaskuser_cc:
                            ##print('u_cc',u_cc)
                            existEtaskuser_cc_dict = {
                                'task':u_cc.task,
                                'user':u_cc.user,
                                'created_by':u_cc.created_by,
                                'owned_by':u_cc.owned_by
                            }
                            ##print('existEtaskuser_cc_dict',existEtaskuser_cc_dict)
                            EtaskUserCCEdit.objects.get_or_create(**existEtaskuser_cc_dict)

                    EtaskUserCC.objects.filter(task = instance).delete()
                    
                    for u_cc in user_cc:
                        ucc_details= EtaskUserCC.objects.create(task=instance,
                            ** u_cc, created_by=created_by , owned_by = owned_by
                        )
                        ucc_details.__dict__.pop('_state') if "_state" in ucc_details.__dict__.keys() else ucc_details.__dict__
                        usercc_list.append(ucc_details.__dict__)

                        cc_user_name = userdetails(int(u_cc['user_id']))
                        cc_user_email = User.objects.get(id=int(u_cc['user_id'])).cu_user.cu_alt_email_id

                        if cc_user_email:
                            mail_data = {
                                        "recipient_name" : cc_user_name,       
                                        "task_subject": task_update.__dict__['task_subject'],
                                        "reporting_date": mail_reporting_date_list,
                                        "assign_to_name": task_update.assign_to.get_full_name(),
                                        "created_by_name": task_update.created_by.get_full_name(),
                                        "created_date_time": task_update.created_at,
                                        "cc_to":','.join(cc_name_list),
                                        "task_priority": task_update.get_task_priority_display(),
                                        "start_date": task_update.start_date.date(),
                                        "end_date": task_update.extended_date.date() if task_update.extended_date else task_update.end_date.date()
                                    }
                            # mail_class = GlobleMailSend('ET-CTCCU', [cc_user_email])
                            # mail_thread = Thread(target = mail_class.mailsend, args = (mail_data,))
                            # mail_thread.start()
                            send_mail_list('ET-CTCCU', [cc_user_email], mail_data, ics='')
                
                reporting_date_list = []
                ##print("task_create",task_create.__dict__['id'])
                reporting_date_str = """"""
                r_time = ''
                ics_data = """BEGIN:VCALENDAR
VERSION:2.0
CALSCALE:GREGORIAN\n"""
                user_name = userdetails(int(task_update.assign_to.id))
                count_id = 0
                

                existETaskReportingDates = ETaskReportingDates.objects.filter(task=task_update.id)
                if existETaskReportingDates:
                    for r_date in existETaskReportingDates:
                        existETaskReportingDates_dict = {
                            'task_type':r_date.task_type,
                            'task':int(task_update.id),
                            'reporting_date':r_date.reporting_date,
                            'actual_reporting_date':r_date.actual_reporting_date,
                            'reporting_status':r_date.reporting_status,
                            'created_by':r_date.created_by,
                            'owned_by':r_date.owned_by
                        }
                        ETaskReportingDatesEdit.objects.get_or_create(**existETaskReportingDates_dict)

                existETaskReportingActionLogEdit = ETaskReportingActionLog.objects.filter(task=task_update.id)
                ##print('existETaskReportingActionLogEdit',existETaskReportingActionLogEdit)
                if existETaskReportingActionLogEdit:
                    for r_date_action in existETaskReportingActionLogEdit:
                        ##print('r_date_action',r_date_action.task)
                        existETaskReportingActionLogEdit_dict = {
                            'task':r_date_action.task,
                            'reporting_date':r_date_action.reporting_date,
                            'updated_date':r_date_action.updated_date,
                            'status':r_date_action.status,
                            'created_by':r_date_action.created_by,
                            'owned_by':r_date_action.owned_by
                        }
                        #print('existETaskReportingActionLogEdit_dict',existETaskReportingActionLogEdit_dict)
                        ETaskReportingActionLogEdit.objects.get_or_create(**existETaskReportingActionLogEdit_dict)
                        ##print('ssssd',sddsd)
                        
                        


                ETaskReportingDates.objects.filter(task = task_update.id).delete()
                ETaskReportingActionLog.objects.filter(task = task_update).delete()
                reporting_date_with_manual_time = {rd['reporting_date'].split('T')[0]: rd['is_manual_time_entry'] for rd in reporting_date}
                reporting_date_with_manual_time_new = {rd['reporting_date'].split('T')[0]: rd['is_manual_time_entry'] for rd in reporting_date_new}
                
                reporting_obj_list = list()
                for r_date in reporting_date:
                    reporting_datetime = datetime.strptime(r_date['reporting_date'], "%Y-%m-%dT%H:%M:%S.%fZ")
                    reporting_end_datetime = datetime.strptime(r_date['reporting_end_date'], "%Y-%m-%dT%H:%M:%S.%fZ")
                    rdate_details,created = ETaskReportingDates.objects.get_or_create(
                        task_type=1,
                        task = task_update.id,
                        is_manual_time_entry=reporting_date_with_manual_time.get(str(reporting_datetime.date()),False),
                        reporting_date = reporting_datetime,
                        reporting_end_date = reporting_end_datetime,
                        created_by=created_by,
                        owned_by=validated_data['owner']
                    )
                    if str(reporting_datetime.date()) in reporting_date_with_manual_time_new.keys():
                        reporting_obj_list.append(rdate_details)

                    reporting_log, created=ETaskReportingActionLog.objects.get_or_create(task_id = task_update.id,
                                                                                        reporting_date_id =str(rdate_details),
                                                                                        updated_date=datetime.now().date(),
                                                                                        status=2,
                                                                                        created_by=created_by,
                                                                                        owned_by=validated_data['owner']
                                                                                    )
                    # #print('reporting_log',reporting_log)

                    rdate_details.__dict__.pop('_state') if "_state" in rdate_details.__dict__.keys() else rdate_details.__dict__
                    reporting_date_list.append(rdate_details.__dict__)
                    ###################################################
                    count_id += 1
                    # reporting_date_str += datetime.strptime(x['reporting_date'], "%m/%d/%Y, %I:%M:%S %p")+'\n'
                    reporting_date_str += str(count_id)+'. '+rdate_details.__dict__['reporting_date'].strftime("%m/%d/%Y, %I:%M:%S %p")+" "
                    r_time = rdate_details.__dict__['reporting_date'].strftime("%Y%m%dT%H%M%S")
                    ics_data +=   """BEGIN:VEVENT
SUMMARY:Reporting of {rep_sub}
DTSTART;TZID=Asia/Kolkata:{r_time}
LOCATION:Shyam Tower,Kolkata-700091
DESCRIPTION: Reporting dates.
STATUS:CONFIRMED
SEQUENCE:3
BEGIN:VALARM
TRIGGER:-PT10M
DESCRIPTION:Pickup Reminder
ACTION:DISPLAY
END:VALARM
END:VEVENT\n""".replace("{r_time}",r_time).replace("{rep_sub}",task_update.__dict__['task_subject'])


                
                ##############################################################
                #DTEND;TZID=Asia/Kolkata:{r_time}
                ics_data += "END:VCALENDAR"
                #print("reporting_date_str",reporting_date_str)
                #print("assign_id",task_update.assign_to.id)
                user_email = User.objects.get(id=task_update.assign_to.id).cu_user.cu_alt_email_id
                #print("user_email",user_email)
                
                if validated_data['task_categories'] != 1 and user_email:
                    mail_data = {
                                "recipient_name" : user_name,        ## modified by manas Paul 21jan20
                                "task_subject": task_update.task_subject,
                                "reporting_date": mail_reporting_date_list,
                                "assign_to_name": task_update.assign_to.get_full_name(),
                                "on_behalf_of": task_update.assign_by.get_full_name() if task_update.task_categories==2 else None,
                                "created_by_name": task_update.created_by.get_full_name(),
                                "created_date_time": task_update.created_at,
                                "cc_to":','.join(cc_name_list),
                                "task_priority": task_update.get_task_priority_display(),
                                "start_date": task_update.start_date.date(),
                                "end_date": task_update.extended_date.date() if task_update.extended_date else task_update.end_date.date()
                            }
                    # #print('mail_data',mail_data)
                    # #print('mail_id-->',mail)
                    # #print('mail_id-->',[mail])
                    #mail_class = GlobleMailSend('ETAP', email_list)
                    # mail_class = GlobleMailSend('ET-EUR', [user_email])
                    # #print('mail_class',mail_class)
                    # mail_thread = Thread(target = mail_class.mailsend, args = (mail_data,ics_data))
                    # #print('mail_thread-->',mail_thread)
                    # mail_thread.start()
                    send_mail_list('ET-EUR', [user_email], mail_data, ics=ics_data)
                ######################################  

                # Creating and mail appointment
                create_appointment(reporting_dates=reporting_obj_list)

                validated_data['user_cc']=usercc_list
                # validated_data['assignto']=assignto_list
                validated_data['reporting_date']=reporting_date_list
                
                '''
                Rajesh Samui
                02/07/2020
                Topic :: Sending Notification
                '''

                users = [task_update.assign_to]
                title = 'The task with task_code {} has been updated.'.format(task_update.task_code_id)
                body ='Task: {} \nDetails:{}'.format(task_update.task_subject,task_update.task_description)

                data = {
                            "app_module":"etask",
                            "type":"task",
                            "id":task_update.id
                        }
                data_str = json.dumps(data)
                if validated_data['task_categories']!=1:
                    notification_id = store_sent_notification(users=users,body=body,title=title,data=data_str,app_module_name='etask')
                    send_notification(users=users,body=body,title=title,data=data,notification_id=notification_id)
                
                return validated_data

        except Exception as e:
            raise e
            # raise APIException({'request_status': 0, 'msg': e})


class EtaskTaskDeleteSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = EtaskTask
        fields = '__all__'
    def update(self,instance,validated_data):
        try:
            updated_by=validated_data.get('updated_by')
            with transaction.atomic():
                instance.is_deleted=True
                instance.updated_by=updated_by
                instance.save()
                
                user_cc=EtaskUserCC.objects.filter(task=instance,is_deleted=False).update(is_deleted=True,updated_by_id=updated_by)
                reporting_dates=ETaskReportingDates.objects.filter(task=str(instance),task_type=1,is_deleted=False).update(is_deleted=True,updated_by_id=updated_by)
                reporting_action_log=ETaskReportingActionLog.objects.filter(task=instance,is_deleted=False).update(is_deleted=True,updated_by_id=updated_by)
                etaskTaskTransferLog = EtaskTaskTransferLog.objects.filter(task=instance,is_deleted=False).update(is_deleted=True)
                etaskTaskSubAssignLog = EtaskTaskSubAssignLog.objects.filter(task=instance,is_deleted=False).update(is_deleted=True)
                
                etaskTaskEditLog = EtaskTaskEditLog.objects.filter(task=instance,is_deleted=False).update(is_deleted=True)
                etaskUserCCEdit = EtaskUserCCEdit.objects.filter(task=instance,is_deleted=False).update(is_deleted=True)
                eTaskReportingDatesEdit = ETaskReportingDatesEdit.objects.filter(task=str(instance),is_deleted=False).update(is_deleted=True)
                eTaskReportingActionLogEdit = ETaskReportingActionLogEdit.objects.filter(task=instance,is_deleted=False).update(is_deleted=True)
                etaskFollowUPEdit = EtaskFollowUPEdit.objects.filter(task=instance,is_deleted=False).update(is_deleted=True)
                
                follow_ups=EtaskFollowUP.objects.filter(task=instance,is_deleted=False)
                if follow_ups:
                    for follow_up in follow_ups:
                        follow_up.is_deleted=True
                        follow_up.updated_by=updated_by
                        follow_up.save()
                        cost_details=FollowupIncludeAdvanceCommentsCostDetails.objects.filter(flcomments=follow_up.id,is_deleted=False).update(is_deleted=True,updated_by_id=updated_by)
                        other_details=FollowupIncludeAdvanceCommentsOtherDetails.objects.filter(flcomments=follow_up.id,is_deleted=False).update(is_deleted=True,updated_by_id=updated_by)
                        document_details=FollowupIncludeAdvanceCommentsDocuments.objects.filter(flcomments=follow_up.id,is_deleted=False).update(is_deleted=True,updated_by_id=updated_by)

                comments=ETaskComments.objects.filter(task=instance,is_deleted=False)
                if comments:
                    for e_c in comments:
                        e_c.is_deleted=True
                        e_c.updated_by=updated_by
                        e_c.save()
                        # #print('advance_comment',e_c.advance_comment)
                        cost_details=EtaskIncludeAdvanceCommentsCostDetails.objects.filter(etcomments_id=e_c.id,is_deleted=False).update(is_deleted=True,updated_by_id=updated_by)
                        other_details=EtaskIncludeAdvanceCommentsOtherDetails.objects.filter(etcomments_id=e_c.id,is_deleted=False).update(is_deleted=True,updated_by_id=updated_by)
                        document_details=EtaskIncludeAdvanceCommentsDocuments.objects.filter(etcomments_id=e_c.id,is_deleted=False).update(is_deleted=True,updated_by_id=updated_by)
                
                return instance
        except Exception as e:
            raise e


class EtaskTaskDeleteSerializerV2(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = EtaskTask
        fields = '__all__'
    def update(self,instance,validated_data):
        try:
            updated_by=validated_data.get('updated_by')
            with transaction.atomic():
                instance.is_deleted=True
                instance.updated_by=updated_by
                instance.save()
                
                etask_parent = EtaskTask.objects.filter(parent_id=instance.id,is_deleted=False)
                if etask_parent.count():
                    raise APIException({'msg':"You can't delete this task as this task has subtask.",
                        "request_status": 0})
                user_cc=EtaskUserCC.objects.filter(task=instance,is_deleted=False).update(is_deleted=True,updated_by_id=updated_by)
                reporting_dates=ETaskReportingDates.objects.filter(task=str(instance),task_type=1,is_deleted=False).update(is_deleted=True,updated_by_id=updated_by)
                reporting_action_log=ETaskReportingActionLog.objects.filter(task=instance,is_deleted=False).update(is_deleted=True,updated_by_id=updated_by)
                etaskTaskTransferLog = EtaskTaskTransferLog.objects.filter(task=instance,is_deleted=False).update(is_deleted=True)
                etaskTaskSubAssignLog = EtaskTaskSubAssignLog.objects.filter(task=instance,is_deleted=False).update(is_deleted=True)
                
                etaskTaskEditLog = EtaskTaskEditLog.objects.filter(task=instance,is_deleted=False).update(is_deleted=True)
                etaskUserCCEdit = EtaskUserCCEdit.objects.filter(task=instance,is_deleted=False).update(is_deleted=True)
                eTaskReportingDatesEdit = ETaskReportingDatesEdit.objects.filter(task=str(instance),is_deleted=False).update(is_deleted=True)
                eTaskReportingActionLogEdit = ETaskReportingActionLogEdit.objects.filter(task=instance,is_deleted=False).update(is_deleted=True)
                etaskFollowUPEdit = EtaskFollowUPEdit.objects.filter(task=instance,is_deleted=False).update(is_deleted=True)
                
                follow_ups=EtaskFollowUP.objects.filter(task=instance,is_deleted=False)
                if follow_ups:
                    for follow_up in follow_ups:
                        follow_up.is_deleted=True
                        follow_up.updated_by=updated_by
                        follow_up.save()
                        cost_details=FollowupIncludeAdvanceCommentsCostDetails.objects.filter(flcomments=follow_up.id,is_deleted=False).update(is_deleted=True,updated_by_id=updated_by)
                        other_details=FollowupIncludeAdvanceCommentsOtherDetails.objects.filter(flcomments=follow_up.id,is_deleted=False).update(is_deleted=True,updated_by_id=updated_by)
                        document_details=FollowupIncludeAdvanceCommentsDocuments.objects.filter(flcomments=follow_up.id,is_deleted=False).update(is_deleted=True,updated_by_id=updated_by)

                comments=ETaskComments.objects.filter(task=instance,is_deleted=False)
                if comments:
                    for e_c in comments:
                        e_c.is_deleted=True
                        e_c.updated_by=updated_by
                        e_c.save()
                        # #print('advance_comment',e_c.advance_comment)
                        cost_details=EtaskIncludeAdvanceCommentsCostDetails.objects.filter(etcomments_id=e_c.id,is_deleted=False).update(is_deleted=True,updated_by_id=updated_by)
                        other_details=EtaskIncludeAdvanceCommentsOtherDetails.objects.filter(etcomments_id=e_c.id,is_deleted=False).update(is_deleted=True,updated_by_id=updated_by)
                        document_details=EtaskIncludeAdvanceCommentsDocuments.objects.filter(etcomments_id=e_c.id,is_deleted=False).update(is_deleted=True,updated_by_id=updated_by)
                
                return instance
        except Exception as e:
            raise e


class EtaskParentTaskListSerializer(serializers.ModelSerializer):
    task_type_name = serializers.SerializerMethodField()
    def get_task_type_name(self,obj):
        if obj.task_type:
            if obj.task_type == 1:
                return 'One Time'
            elif obj.task_type == 2:
                return 'Profile Job'
            else:
                return 'Sub Task'
        else:
            return None
    class Meta:
        model = EtaskTask
        fields = ('id','task_subject','start_date','task_type','recurrance_frequency','end_date','extended_date','task_type_name')
        # extra_fields = ('task_type_name')

class EtaskMyTaskListSerializer(serializers.ModelSerializer):
    class Meta:
        model = EtaskTask
        fields = ('id','parent_id','task_subject','task_description','start_date','end_date','task_status','completed_date',
                    'task_code_id','closed_date','extended_date','assign_by','assign_to','sub_assign_to_user','get_task_status_display') #,'assign_by_name','sub_task_list','sub_assign_to_name')

class EtaskCompletedTaskListSerializer(serializers.ModelSerializer):
    class Meta:
        model = EtaskTask
        fields = ('id','parent_id','task_subject','task_description','start_date','end_date','task_status','completed_date',
                    'task_code_id','extended_date','assign_by','assign_to','sub_assign_to_user') #,'sub_assign_to_user','assign_to_name','sub_task_list','sub_assign_to_name')


class EtaskClosedTaskListSerializer(serializers.ModelSerializer):
    class Meta:
        model = EtaskTask
        fields = ('id','task_code_id','parent_id','task_subject','task_description','start_date','end_date','task_status','closed_date',
                    'extended_date','assign_by','assign_to','sub_assign_to_user','get_task_status_display') #,'assign_to_name','sub_task_list', 'sub_assign_to_name','assign_by_name')

    

class EtaskOverdueTaskListSerializer(serializers.ModelSerializer):
    class Meta:
        model = EtaskTask
        fields = ('id','task_code_id','parent_id','task_subject','task_description','start_date','end_date','task_status','completed_date',
                    'extended_date','assign_by','assign_to','sub_assign_to_user','sub_assign_to_user') #,'assign_to_name','sub_task_list','sub_assign_to_name','assign_by_name','overdue_by_day')
   

class EtasktaskListSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = EtaskTask
        fields = ('id','parent_id','task_subject')


class EtaskTaskStatusListSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    
    class Meta:
        model = EtaskTask
        fields = '__all__'


class ETaskAllTasklistSerializer(serializers.ModelSerializer):
    parent_task=serializers.SerializerMethodField(required=False)
    sub_data = EtaskTask.objects.filter(parent_id=0,is_deleted=False)
    task_type_name=serializers.CharField(source='get_task_type_display')
    recurrance_frequency_name=serializers.CharField(source='get_recurrance_frequency_display')
    task_status_name=serializers.CharField(source='get_task_status_display')
    assign_by_name = serializers.SerializerMethodField()
    assign_to_name= serializers.SerializerMethodField()
    sub_assign_to_user_name= serializers.SerializerMethodField()

    class Meta:
        model = EtaskTask
        fields = ('__all__')

    def get_parent_task(self,EtaskTask):
        if EtaskTask.parent_id:
            if EtaskTask.parent_id !=0:
                if self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject'):
                    parent_data=self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject')[0]
                    return parent_data

    def user_name(self, user_id):
        name = None
        full_name = ""
        name = User.objects.get(id=user_id)
        if name:
            full_name =  name.__dict__['first_name']+" "+name.__dict__['last_name']
        return full_name

    def get_assign_by_name(self,EtaskTask):
        name = None
        full_name = ""
        if EtaskTask.assign_by:
            name = User.objects.get(id=EtaskTask.assign_by.id)
            if name:
                full_name =  name.__dict__['first_name']+" "+name.__dict__['last_name']
                # #print("full_name",full_name)
            return full_name

    def get_sub_assign_to_user_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.sub_assign_to_user:
            name=User.objects.get(id=EtaskTask.sub_assign_to_user.id)
            if name:
                full_name= name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name

    def get_assign_to_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.assign_to:
            name =User.objects.get(id=EtaskTask.assign_to.id)
            if name:
                full_name=name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name

class ETaskUpcomingCompletionListSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = EtaskTask
        fields = '__all__'

class EtaskTaskCompleteViewSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    # completed_date = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = EtaskTask
        fields = '__all__'
    def update(self, instance, validated_data):
        try:
            with transaction.atomic():
                current_date = datetime.now()
                end_date = instance.end_date.date()
                # #print('end_date-->',end_date)
                updated_by = validated_data.get('updated_by')
                # #print('parent_id',instance.parent_id)
                flag=False
                if instance.parent_id == 0:
                    child_task=EtaskTask.objects.filter(parent_id=str(instance),is_deleted=False).values('task_status')
                    if child_task:
                        # #print('child_task',child_task)         
                        for c_t in child_task:
                            # #print('c_t',c_t['task_status'])
                            if c_t['task_status'] != 2:
                                flag=True
                        # return flag
                        #print('flag',flag)
                    else:
                        instance.task_status=2
                        instance.completed_date = current_date
                        instance.completed_by=updated_by
                        instance.is_closure=True
                        instance.updated_by = updated_by
                        instance.save()
                        reporting_status = ETaskReportingDates.objects.filter(task_type=1,
                                                                        task=instance.id,
                                                                        reporting_date__date=end_date).values('reporting_status')
                        # #print('reporting_status->',reporting_status)
                        if reporting_status:
                            if int(reporting_status[0]['reporting_status']) == 0 or int(reporting_status[0]['reporting_status']) == 2 :
                                etask_reporting_dates = ETaskReportingDates.objects.filter(task_type=1,task=instance.id,is_deleted=False)

                                # #print('etask_reporting_dates-->',etask_reporting_dates)
                                if etask_reporting_dates:
                                    for e_r in etask_reporting_dates:
                                        e_r.reporting_status=3
                                        e_r.actual_reporting_date = current_date
                                        e_r.updated_by = updated_by
                                        e_r.save()
                                        action_log=ETaskReportingActionLog.objects.create(task_id = instance.id,
                                                                            reporting_date_id=e_r.id,
                                                                            status = 3,
                                                                            updated_by = updated_by
                                                                            )
                                        # #print('action_log-->',action_log)
                            else:
                                etask_reporting_dates = ETaskReportingDates.objects.filter(task_type=1,task=instance.id,is_deleted=False)

                                # #print('etask_reporting_dates-->',etask_reporting_dates)
                                if etask_reporting_dates:
                                    action_log=ETaskReportingActionLog.objects.create(task_id = instance.id,
                                                                        status = 4,
                                                                        updated_by = updated_by
                                                                        )
                                    # #print('action_log-->',action_log)
                        return instance
                    
                if flag == False or instance.parent_id != 0:
                    instance.task_status=2
                    instance.completed_date = current_date
                    instance.completed_by=updated_by
                    instance.is_closure=True
                    instance.updated_by = updated_by
                    instance.save()
                    reporting_status = ETaskReportingDates.objects.filter(task_type=1,
                                                                        task=instance.id,
                                                                        reporting_date__date=end_date).values('reporting_status')
                    # #print('reporting_status->',reporting_status[0]['reporting_status'])
                    if reporting_status:
                        if int(reporting_status[0]['reporting_status']) == 0 or int(reporting_status[0]['reporting_status']) == 2 :
                            etask_reporting_dates = ETaskReportingDates.objects.filter(task_type=1,task=instance.id,is_deleted=False)

                            # #print('etask_reporting_dates-->',etask_reporting_dates)
                            if etask_reporting_dates:
                                for e_r in etask_reporting_dates:
                                    e_r.reporting_status=3
                                    e_r.actual_reporting_date = current_date
                                    e_r.updated_by = updated_by
                                    e_r.save()
                                    action_log=ETaskReportingActionLog.objects.create(task_id = instance.id,
                                                                        reporting_date_id=e_r.id,
                                                                        status = 3,
                                                                        updated_by = updated_by
                                                                        )
                                    # #print('action_log-->',action_log)
                        else:
                            etask_reporting_dates = ETaskReportingDates.objects.filter(task_type=1,task=instance.id,is_deleted=False)

                            # #print('etask_reporting_dates-->',etask_reporting_dates)
                            if etask_reporting_dates:
                                action_log=ETaskReportingActionLog.objects.create(task_id = instance.id,
                                                                    status = 4,
                                                                    updated_by = updated_by
                                                                    )
                                # #print('action_log-->',action_log)
                    return instance
                else:
                    raise APIException("Child task is not completed."
                                )
        except Exception as e:
            raise e
            # raise APIException({'msg':e,
            #                     "request_status": 0
            #                     })


class EtaskTaskCompleteViewSerializerV2(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = EtaskTask
        fields = '__all__'

    def update(self, instance, validated_data):
        try:
            with transaction.atomic():
                current_date = datetime.now()
                end_date = instance.end_date.date()
                # #print('end_date-->',end_date)
                user = self.context['request'].user
                updated_by = validated_data.get('updated_by')
                # #print('parent_id',instance.parent_id)
                flag=False
                if instance.parent_id == 0:
                    child_task=EtaskTask.objects.filter(Q(Q(task_status=1)|Q(task_status=3)),parent_id=str(instance),is_deleted=False).values('task_status')
                    if child_task:
                        flag=True
                        # return flag
                        #print('flag',flag)
                    else:
                        if TaskCompleteReopenMap.objects.filter(task=instance,status=1).count():
                            raise APIException({'msg':'You have already requested a closer for this task.',
                                                "request_status": 0})

                        task_complete_reopen, is_created = TaskCompleteReopenMap.objects.get_or_create(task=instance,status=1)
                        task_complete_reopen.completed_date = current_date
                        task_complete_reopen.completed_by = updated_by
                        task_complete_reopen.created_by = updated_by
                        
                        if user == instance.assign_by:
                            instance.task_status= 4
                            instance.closed_date = current_date
                            task_complete_reopen.approved_date = current_date
                            task_complete_reopen.approved_by = updated_by
                            task_complete_reopen.status = 2
                        else:
                            instance.task_status= 2

                        instance.completed_date = current_date
                        instance.completed_by=updated_by
                        instance.is_closure=True
                        instance.updated_by = updated_by
                        instance.save()
                        task_complete_reopen.save()
                        reporting_status = ETaskReportingDates.objects.filter(task_type=1,
                                                                        task=instance.id,
                                                                        reporting_date__date=end_date).values('reporting_status')
                        # #print('reporting_status->',reporting_status)
                        if reporting_status:
                            if int(reporting_status[0]['reporting_status']) == 0 or int(reporting_status[0]['reporting_status']) == 2 :
                                etask_reporting_dates = ETaskReportingDates.objects.filter(task_type=1,task=instance.id,is_deleted=False)

                                # #print('etask_reporting_dates-->',etask_reporting_dates)
                                if etask_reporting_dates:
                                    for e_r in etask_reporting_dates:
                                        e_r.reporting_status=3
                                        e_r.actual_reporting_date = current_date
                                        e_r.updated_by = updated_by
                                        e_r.save()
                                        action_log=ETaskReportingActionLog.objects.create(task_id = instance.id,
                                                                            reporting_date_id=e_r.id,
                                                                            status = 3,
                                                                            updated_by = updated_by
                                                                            )
                                        # #print('action_log-->',action_log)
                            else:
                                etask_reporting_dates = ETaskReportingDates.objects.filter(task_type=1,task=instance.id,is_deleted=False)

                                # #print('etask_reporting_dates-->',etask_reporting_dates)
                                if etask_reporting_dates:
                                    action_log=ETaskReportingActionLog.objects.create(task_id = instance.id,
                                                                        status = 4,
                                                                        updated_by = updated_by
                                                                        )
                                    # #print('action_log-->',action_log)
                        return instance
                    
                if flag == False or instance.parent_id != 0:
                    if TaskCompleteReopenMap.objects.filter(task=instance,status=1).count():
                        raise APIException({'msg':'You have already requested a closer for this task.',
                                            "request_status": 0})

                    task_complete_reopen, is_created = TaskCompleteReopenMap.objects.get_or_create(task=instance,status=1)
                    task_complete_reopen.completed_date = current_date
                    task_complete_reopen.completed_by = updated_by
                    task_complete_reopen.created_by = updated_by

                    if user == instance.assign_by:
                        instance.task_status= 4
                        instance.closed_date = current_date
                        task_complete_reopen.approved_date = current_date
                        task_complete_reopen.approved_by = updated_by
                        task_complete_reopen.status = 2
                    else:
                        instance.task_status= 2
                    instance.completed_date = current_date
                    instance.completed_by=updated_by
                    instance.is_closure=True
                    instance.updated_by = updated_by
                    instance.save()
                    task_complete_reopen.save()
                    reporting_status = ETaskReportingDates.objects.filter(task_type=1,
                                                                        task=instance.id,
                                                                        reporting_date__date=end_date).values('reporting_status')
                    # #print('reporting_status->',reporting_status[0]['reporting_status'])
                    if reporting_status:
                        if int(reporting_status[0]['reporting_status']) == 0 or int(reporting_status[0]['reporting_status']) == 2 :
                            etask_reporting_dates = ETaskReportingDates.objects.filter(task_type=1,task=instance.id,is_deleted=False)

                            # #print('etask_reporting_dates-->',etask_reporting_dates)
                            if etask_reporting_dates:
                                for e_r in etask_reporting_dates:
                                    e_r.reporting_status=3
                                    e_r.actual_reporting_date = current_date
                                    e_r.updated_by = updated_by
                                    e_r.save()
                                    action_log=ETaskReportingActionLog.objects.create(task_id = instance.id,
                                                                        reporting_date_id=e_r.id,
                                                                        status = 3,
                                                                        updated_by = updated_by
                                                                        )
                                    # #print('action_log-->',action_log)
                        else:
                            etask_reporting_dates = ETaskReportingDates.objects.filter(task_type=1,task=instance.id,is_deleted=False)

                            # #print('etask_reporting_dates-->',etask_reporting_dates)
                            if etask_reporting_dates:
                                action_log=ETaskReportingActionLog.objects.create(task_id = instance.id,
                                                                    status = 4,
                                                                    updated_by = updated_by
                                                                    )
                                # #print('action_log-->',action_log)
                    return instance
                else:
                    raise APIException("Child task is not completed."
                                )
        except Exception as e:
            raise e

class EtaskMultiTaskCompleteViewSerializerV2(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    request_status = serializers.CharField(required=False)
    message = serializers.CharField(required=False)
    task_ids = serializers.ListField(required=False)
    is_confirm = serializers.BooleanField(default=False)

    class Meta:
        model = EtaskTask
        fields = ('id','updated_by','message','request_status','task_ids','is_confirm')
    def create(self, validated_data):
        with transaction.atomic():
            updated_by = validated_data.pop('updated_by')
            login_user_details = updated_by
            current_date = datetime.now()
            task_list = validated_data.pop('task_ids')
            is_confirm = validated_data.pop('is_confirm')

            error_list = list()
            success_list = list()
            if task_list:
                
                for each in task_list:
                    instance = EtaskTask.objects.get(id=each)
                    task_closer = TaskCompleteReopenMap.objects.filter(task_id=each, status=1)
                    is_pending_closer = task_closer.count() > 0
                    if instance.parent_id == 0 and is_pending_closer == False:
                        child_task = EtaskTask.objects.filter(Q(Q(task_status=1)|Q(task_status=3)),parent_id=str(instance), is_deleted=False).values(
                            'task_status')
                        if child_task:
                            error_list.append(str(instance.task_code_id))
                        else:
                            if TaskCompleteReopenMap.objects.filter(task=instance, status=1).count():
                                error_list.append(str(instance.task_code_id))
                            else:
                                success_list.append(str(instance.task_code_id))
                    else:
                        error_list.append(str(instance.task_code_id))

                if not error_list or is_confirm:
                    for each in task_list:
                        instance = EtaskTask.objects.get(id=each)
                        end_date = instance.end_date.date()
                        task_closer = TaskCompleteReopenMap.objects.filter(task_id=each, status=1)
                        is_pending_closer = task_closer.count() > 0
                        if instance.parent_id == 0 and is_pending_closer == False:
                            child_task = EtaskTask.objects.filter(Q(Q(task_status=1)|Q(task_status=3)),
                                            parent_id=str(instance), is_deleted=False).values('task_status')
                            if child_task:
                                #error_list.append(str(instance.task_code_id))
                                pass
                            else:
                                if TaskCompleteReopenMap.objects.filter(task=instance, status=1).count():
                                    #error_list.append(str(instance.task_code_id))
                                    pass
                                else:
                                    task_complete_reopen, is_created = TaskCompleteReopenMap.objects.get_or_create(
                                        task=instance,
                                        status=1)
                                    task_complete_reopen.completed_date = current_date
                                    task_complete_reopen.completed_by = login_user_details
                                    task_complete_reopen.created_by = login_user_details
                                    if login_user_details == instance.assign_by:
                                        instance.task_status = 4
                                        instance.closed_date = current_date
                                        task_complete_reopen.approved_date = current_date
                                        task_complete_reopen.approved_by = login_user_details
                                        task_complete_reopen.status = 2
                                    else:
                                        instance.task_status = 2

                                    instance.completed_date = current_date
                                    instance.completed_by = login_user_details
                                    instance.is_closure = True
                                    instance.updated_by = login_user_details
                                    instance.save()
                                    task_complete_reopen.save()
                                    reporting_status = ETaskReportingDates.objects.filter(task_type=1,
                                                                                        task=instance.id,
                                                                                        reporting_date__date=end_date).values(
                                        'reporting_status')
                                    if reporting_status:
                                        if int(reporting_status[0]['reporting_status']) == 0 or int(
                                                reporting_status[0]['reporting_status']) == 2:
                                            etask_reporting_dates = ETaskReportingDates.objects.filter(task_type=1,
                                                                                                    task=instance.id,
                                                                                                    is_deleted=False)
                                            if etask_reporting_dates:
                                                for e_r in etask_reporting_dates:
                                                    e_r.reporting_status = 3
                                                    e_r.actual_reporting_date = current_date
                                                    e_r.updated_by = updated_by
                                                    e_r.save()
                                                    action_log = ETaskReportingActionLog.objects.create(task_id=instance.id,
                                                                                                        reporting_date_id=e_r.id,
                                                                                                        status=3,
                                                                                                        updated_by=updated_by
                                                                                                        )
                                        else:
                                            etask_reporting_dates = ETaskReportingDates.objects.filter(task_type=1,
                                                                                                    task=instance.id,
                                                                                                    is_deleted=False)

                                            if etask_reporting_dates:
                                                action_log = ETaskReportingActionLog.objects.create(task_id=instance.id,
                                                                                                    status=4,
                                                                                                    updated_by=login_user_details
                                                                                                    )
                                    #success_list.append(str(instance.task_code_id))
                        else:
                            #error_list.append(str(instance.task_code_id))
                            pass

            error_msg = 'Task with task_code {} can not be completed'.format(', '.join(error_list))
            success_msg = 'Task with task_code {} has been completed'.format(', '.join(success_list))
            if error_list and success_list:
                validated_data['message'] = '{} and {}.'.format(success_msg, error_msg)
            elif error_list and not success_list:
                validated_data['message'] = '{}.'.format(error_msg)
            elif not error_list and success_list:
                validated_data['message'] = '{}.'.format(success_msg)
            validated_data['request_status'] = 1 if not error_list or is_confirm else 0
            return validated_data


class EtaskMyTaskTodaysPlannerListSerializer(serializers.ModelSerializer):

    class Meta:
        model = EtaskTask
        fields = ('id','parent_id','task_subject','task_description','start_date','end_date','task_status','completed_date',
                    'closed_date','extended_date','assign_by','assign_to','sub_assign_to_user','get_task_status_display')

class EtaskEndDateExtensionRequestSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = EtaskTask
        fields = ('id','requested_end_date','requested_comment','updated_by','requested_by')
    def update(self, instance, validated_data):
        instance.requested_end_date = validated_data['requested_end_date']
        instance.requested_comment = validated_data['requested_comment']
        instance.requested_by=validated_data.get('updated_by')
        instance.updated_by = validated_data.get('updated_by')
        instance.save()
        return instance


class EtaskEndDateExtensionRequestSerializerV2(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = EtaskTask
        fields = ('id','requested_end_date','requested_comment','updated_by','requested_by')

    def update(self, instance, validated_data):
        requested_comment = validated_data['requested_comment']
        updated_by = validated_data.get('updated_by')
        requested_end_date = validated_data['requested_end_date']
        if TaskExtentionDateMap.objects.filter(task=instance,status=1).count():
            raise APIException({'msg':'You have already requested an extended date for this task.',
                                "request_status": 0})
        with transaction.atomic():

            task_extention_date = TaskExtentionDateMap.objects.create(
                                                                    status=1,
                                                                    task=instance,
                                                                    requested_end_date=requested_end_date,
                                                                    requested_comment=requested_comment,
                                                                    requested_by=updated_by,
                                                                    crated_by=updated_by
                                                                    )

            if updated_by == instance.assign_by:
                instance.extended_date = requested_end_date
                task_extention_date.extended_date = requested_end_date
                task_extention_date.status = 2
                task_extention_date.save()
            instance.requested_end_date = requested_end_date
            instance.requested_comment = requested_comment
            instance.requested_by=updated_by
            instance.updated_by =updated_by
            instance.save()
            sys_comment = 'Extension request for {}'.format(requested_end_date.strftime("%d %B %y"))
            create_comment(task=instance,comments=requested_comment, loggedin_user=updated_by)
            create_comment(task=instance, comments=sys_comment, loggedin_user=updated_by)

        return instance


class EtaskMultiEndDateExtensionRequestSerializerV2(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    requested_end_date = serializers.DateTimeField(required=False)
    requested_comment = serializers.CharField(required=False)
    task_ids = serializers.ListField(required=False)
    request_status = serializers.CharField(required=False)
    message = serializers.CharField(required=False)
    is_confirm = serializers.BooleanField(default=False)

    class Meta:
        model = EtaskTask
        fields = ('id','requested_end_date','requested_comment','updated_by','task_ids',
                'request_status','message','is_confirm')
    def create(self, validated_data):
        with transaction.atomic():
            current_date = datetime.now()
            requested_end_date = validated_data.pop('requested_end_date')
            requested_comment = validated_data.pop('requested_comment')
            login_user_details = validated_data.pop('updated_by')
            task_ids = validated_data.pop('task_ids')
            is_confirm = validated_data.pop('is_confirm')

            task_list = list()
            if task_ids:
                task_list = task_ids

            error_list = list()
            success_list = list()
            if task_list:

                
                for each in task_list:
                    instance = EtaskTask.objects.get(id=each)
                    if not TaskExtentionDateMap.objects.filter(task=instance,status=1).count():
                        if (instance.extended_date and requested_end_date.date()>instance.extended_date.date()) or (instance.extended_date == None and requested_end_date.date()>instance.end_date.date()):
                            success_list.append(instance.task_code_id)
                        else:
                            error_list.append(instance.task_code_id)

                    else:
                        error_list.append(instance.task_code_id)

                if not error_list or is_confirm:
                    for each in task_list:
                        instance = EtaskTask.objects.get(id=each)
                        date_validation = (instance.extended_date and requested_end_date.date()>instance.extended_date.date()) or (instance.extended_date == None and requested_end_date.date()>instance.end_date.date())
                        if not TaskExtentionDateMap.objects.filter(task=instance,status=1).count() and date_validation:
                            task_extention_date = TaskExtentionDateMap.objects.create(
                                status=1,
                                task=instance,
                                requested_end_date=requested_end_date,
                                requested_comment=requested_comment,
                                requested_by=login_user_details,
                                crated_by=login_user_details
                            )

                            if login_user_details == instance.assign_by:
                                instance.extended_date = requested_end_date
                                task_extention_date.extended_date = requested_end_date
                                task_extention_date.status = 2
                                task_extention_date.save()
                            instance.requested_end_date = requested_end_date
                            instance.requested_comment = requested_comment
                            instance.requested_by = login_user_details
                            instance.updated_by = login_user_details
                            instance.save()
                            sys_comment = 'Extension request for {}'.format(requested_end_date.strftime("%d %B %y"))
                            create_comment(task=instance,comments=requested_comment, loggedin_user=login_user_details)
                            create_comment(task=instance, comments=sys_comment, loggedin_user=login_user_details)

                        #
                        #     loggedin_user = self.context['request'].user.id
                        #     validated_data['task'] = EtaskTask.objects.get(id=each)
                        #     e_task_comments = ETaskComments.objects.create(task=EtaskTask.objects.get(id=each), comments=requested_comment,
                        #                                                 created_by=login_user_details,owned_by=login_user_details)
                        #     comment_save_send = ''
                        #     users_list = EtaskTask.objects.filter(id=str(validated_data.get('task')),
                        #                                         is_deleted=False).values(
                        #         'assign_by', 'assign_to')
                        #     task_obj = EtaskTask.objects.filter(id=str(validated_data.get('task')),
                        #                                         is_deleted=False).first()
                        #     user_cat_list = users_list.values('task_categories', 'sub_assign_to_user')
                        #     email_list = []
                        #     if user_cat_list[0]['task_categories'] == 1:
                        #         comment_view = ETaskCommentsViewers.objects.create(etcomments=e_task_comments,
                        #                                                         user_id=users_list[0]['assign_by'],
                        #                                                         task=validated_data.get('task'),
                        #                                                         created_by=login_user_details,
                        #                                                         owned_by=login_user_details
                        #                                                         )
                        #         if loggedin_user == users_list[0]['assign_by']:
                        #             viewer = ETaskCommentsViewers.objects.filter(etcomments=e_task_comments,
                        #                                                         user_id=users_list[0]['assign_by'],
                        #                                                         task=validated_data.get('task')).update(
                        #                 is_view=True)
                        #
                        #         assign_by_mail_id = TCoreUserDetail.objects.filter(cu_user_id=users_list[0]['assign_by'],
                        #                                                         cu_is_deleted=False).values(
                        #             'cu_alt_email_id')
                        #         email_list.append(assign_by_mail_id[0]['cu_alt_email_id'])
                        #         if loggedin_user != users_list[0]['assign_by'] and comment_save_send == 'send':
                        #             mail_data = {
                        #                 "recipient_name": userdetails(users_list[0]['assign_by']),
                        #                 "comment_sub": validated_data.get('comments'),
                        #                 "commented_by": userdetails(users_list[0]['assign_by']),
                        #                 "task_subject": task_obj.task_subject,
                        #                 "assign_to_name": task_obj.assign_to.get_full_name(),
                        #                 "start_date": task_obj.start_date.date(),
                        #                 "end_date": task_obj.extended_date.date() if task_obj.extended_date else task_obj.end_date.date()
                        #             }
                        #             # mail_class = GlobleMailSend('ET-COMMENT', email_list)
                        #             # mail_thread = Thread(target=mail_class.mailsend, args=(mail_data,))
                        #             # mail_thread.start()
                        #             send_mail_list('ET-COMMENT', email_list, mail_data, ics='')
                        #     else:
                        #         for user in users_list:
                        #             for k, v in user.items():
                        #                 comment_view = ETaskCommentsViewers.objects.create(etcomments=e_task_comments,
                        #                                                                 user_id=v,
                        #                                                                 task=validated_data.get('task'),
                        #                                                                 created_by=login_user_details,
                        #                                                                 owned_by=login_user_details
                        #                                                                 )
                        #                 if loggedin_user == v:
                        #                     viewer = ETaskCommentsViewers.objects.filter(etcomments=e_task_comments,
                        #                                                                 user_id=v,
                        #                                                                 task=validated_data.get(
                        #                                                                     'task')).update(is_view=True)
                        #                 if loggedin_user != v:
                        #                     mail_id = TCoreUserDetail.objects.filter(cu_user_id=v,
                        #                                                             cu_is_deleted=False).values(
                        #                         'cu_alt_email_id')
                        #                     email_list.append(mail_id[0]['cu_alt_email_id'])
                        #                     if comment_save_send == 'send':
                        #                         mail_data = {
                        #                             "recipient_name": userdetails(v),
                        #                             "comment_sub": validated_data.get('comments'),
                        #                             "commented_by": userdetails(loggedin_user),
                        #                             "task_subject": task_obj.task_subject,
                        #                             "assign_to_name": task_obj.assign_to.get_full_name(),
                        #                             "start_date": task_obj.start_date.date(),
                        #                             "end_date": task_obj.extended_date.date() if task_obj.extended_date else task_obj.end_date.date()
                        #                         }
                        #                         # mail_class = GlobleMailSend('ET-COMMENT', email_list)
                        #                         # mail_thread = Thread(target=mail_class.mailsend, args=(mail_data,))
                        #                         # mail_thread.start()
                        #                         send_mail_list('ET-COMMENT', email_list, mail_data, ics='')
                        #     sub_assign_email_list = []
                        #     if user_cat_list[0]['sub_assign_to_user']:
                        #         sub_comment_view = ETaskCommentsViewers.objects.create(etcomments=e_task_comments,
                        #                                                             user_id=user_cat_list[0][
                        #                                                                 'sub_assign_to_user'],
                        #                                                             task=validated_data.get('task'),
                        #                                                             created_by=login_user_details,
                        #                                                             owned_by=login_user_details
                        #                                                             )
                        #         if loggedin_user == user_cat_list[0]['sub_assign_to_user']:
                        #             viewer = ETaskCommentsViewers.objects.filter(etcomments=e_task_comments,
                        #                                                         user_id=user_cat_list[0][
                        #                                                             'sub_assign_to_user'],
                        #                                                         task=validated_data.get('task')).update(
                        #                 is_view=True)
                        #
                        #         assign_by_mail_id = TCoreUserDetail.objects.filter(cu_user_id=users_list[0]['assign_by'],
                        #                                                         cu_is_deleted=False).values(
                        #             'cu_alt_email_id')
                        #         sub_assign_email_list.append(assign_by_mail_id[0]['cu_alt_email_id'])
                        #         if loggedin_user != users_list[0]['assign_by'] and comment_save_send == 'send':
                        #             mail_data = {
                        #                 "recipient_name": userdetails(users_list[0]['assign_by']),
                        #                 "comment_sub": validated_data.get('comments'),
                        #                 "commented_by": userdetails(user_cat_list[0]['sub_assign_to_user']),
                        #                 "task_subject": task_obj.task_subject,
                        #                 "assign_to_name": task_obj.assign_to.get_full_name(),
                        #                 "start_date": task_obj.start_date.date(),
                        #                 "end_date": task_obj.extended_date.date() if task_obj.extended_date else task_obj.end_date.date()
                        #             }
                        #             # mail_class = GlobleMailSend('ET-COMMENT', sub_assign_email_list)
                        #             # mail_thread = Thread(target=mail_class.mailsend, args=(mail_data,))
                        #             # mail_thread.start()
                        #             send_mail_list('ET-COMMENT', sub_assign_email_list, mail_data, ics='')
                        #
                        #     # success_list.append(instance.task_code_id)
                        # else:
                        #     # error_list.append(instance.task_code_id)
                        #     pass


            error_msg = 'Task with task_code {} can not be submited for extenssion'.format(', '.join(error_list))
            success_msg = 'Task with task_code {} has been submited for extenssion'.format(', '.join(success_list))
            if error_list and success_list:
                validated_data['message'] = '{} and {}.'.format(success_msg, error_msg)
            elif error_list and not success_list:
                validated_data['message']= '{}.'.format(error_msg)
            elif not error_list and success_list:
                validated_data['message'] = '{}.'.format(success_msg)
            validated_data['request_status'] = 1 if not error_list or is_confirm else 0
            return validated_data


class EtaskManyExtendedListSerializer(serializers.ModelSerializer):

    class Meta:
        model = EtaskTask
        fields = '__all__'

class EtaskExtensionsListSerializer(serializers.ModelSerializer):
    parent_task=serializers.SerializerMethodField(required=False)
    sub_data = EtaskTask.objects.filter(parent_id=0,is_deleted=False)
    task_type_name=serializers.CharField(source='get_task_type_display')
    recurrance_frequency_name=serializers.CharField(source='get_recurrance_frequency_display')
    task_status_name=serializers.CharField(source='get_task_status_display')
    task_priority_name=serializers.CharField(source='get_task_priority_display')
    assign_by_name = serializers.SerializerMethodField()
    assign_to_name= serializers.SerializerMethodField()
    sub_assign_to_user_name= serializers.SerializerMethodField()
    reporting_dates = serializers.SerializerMethodField()
    class Meta:
        model= EtaskTask
        fields='__all__'

    def get_parent_task(self,EtaskTask):
        if EtaskTask.parent_id:
            if EtaskTask.parent_id !=0:
                if self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject','task_description'):
                    parent_data=self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject','task_description')[0]
                    return parent_data

    def user_name(self, user_id):
        name = None
        full_name = ""
        name = User.objects.get(id=user_id)
        if name:
            full_name =  name.__dict__['first_name']+" "+name.__dict__['last_name']
        return full_name

    def get_assign_by_name(self,EtaskTask):
        name = None
        full_name = ""
        if EtaskTask.assign_by:
            name = User.objects.get(id=EtaskTask.assign_by.id)
            if name:
                full_name =  name.__dict__['first_name']+" "+name.__dict__['last_name']
                # #print("full_name",full_name)
            return full_name

    def get_sub_assign_to_user_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.sub_assign_to_user:
            name=User.objects.get(id=EtaskTask.sub_assign_to_user.id)
            if name:
                full_name= name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name

    def get_assign_to_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.assign_to:
            name =User.objects.get(id=EtaskTask.assign_to.id)
            if name:
                full_name=name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name
    def get_reporting_dates(self,EtaskTask):
        if EtaskTask.id:
            report_date_list = []
            report_date=ETaskReportingDates.objects.filter(task_type=1,task=EtaskTask.id,is_deleted=False)
            # #print("report_date",report_date)
            if report_date:
                for dt in report_date:
                    dt_dict={
                        'id':dt.id,
                        'reporting_date':dt.reporting_date,
                        'reporting_status':dt.reporting_status,
                        'reporting_status_name':dt.get_reporting_status_display()
                       
                    }
                    report_date_list.append(dt_dict)
                                   
                return report_date_list
            else:
                return []


class EtaskExtensionsListSerializerV2(serializers.ModelSerializer):
    parent_task=serializers.SerializerMethodField(required=False)
    sub_data = EtaskTask.objects.filter(parent_id=0,is_deleted=False)
    task_type_name=serializers.CharField(source='get_task_type_display')
    recurrance_frequency_name=serializers.CharField(source='get_recurrance_frequency_display')
    task_status_name=serializers.CharField(source='get_task_status_display')
    task_priority_name=serializers.CharField(source='get_task_priority_display')
    assign_by_name = serializers.SerializerMethodField()
    assign_to_name= serializers.SerializerMethodField()
    sub_assign_to_user_name= serializers.SerializerMethodField()
    reporting_dates = serializers.SerializerMethodField()
    user_cc = serializers.SerializerMethodField()
    sub_tasks = serializers.SerializerMethodField()

    class Meta:
        model= EtaskTask
        fields='__all__'
        extra_fields = ('user_cc','sub_tasks')

    def get_sub_tasks(self, obj):
        sub_tasks_data = EtaskTask.objects.filter(~Q(task_status=4),parent_id=obj.id,is_deleted=False).values('id','task_subject')
        return sub_tasks_data if sub_tasks_data else list() 

    def get_user_cc(self, obj):
        user_cc=EtaskUserCC.objects.filter(task=obj,is_deleted=False).values('id','user__first_name', 'user__last_name')
        return user_cc if user_cc else list()

    def get_parent_task(self,EtaskTask):
        if EtaskTask.parent_id:
            if EtaskTask.parent_id !=0:
                if self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject','task_description'):
                    parent_data=self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject','task_description')[0]
                    return parent_data

    def user_name(self, user_id):
        name = None
        full_name = ""
        name = User.objects.get(id=user_id)
        if name:
            full_name =  name.__dict__['first_name']+" "+name.__dict__['last_name']
        return full_name

    def get_assign_by_name(self,EtaskTask):
        name = None
        full_name = ""
        if EtaskTask.assign_by:
            name = User.objects.get(id=EtaskTask.assign_by.id)
            if name:
                full_name =  name.__dict__['first_name']+" "+name.__dict__['last_name']
                # #print("full_name",full_name)
            return full_name

    def get_sub_assign_to_user_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.sub_assign_to_user:
            name=User.objects.get(id=EtaskTask.sub_assign_to_user.id)
            if name:
                full_name= name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name

    def get_assign_to_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.assign_to:
            name =User.objects.get(id=EtaskTask.assign_to.id)
            if name:
                full_name=name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name
    def get_reporting_dates(self,EtaskTask):
        if EtaskTask.id:
            report_date_list = []
            report_date=ETaskReportingDates.objects.filter(task_type=1,task=EtaskTask.id,is_deleted=False).order_by('reporting_date')
            # #print("report_date",report_date)
            if report_date:
                for dt in report_date:
                    dt_dict={
                        'id':dt.id,
                        'reporting_date':dt.reporting_date,
                        'reporting_status':dt.reporting_status,
                        'reporting_status_name':dt.get_reporting_status_display()
                       
                    }
                    report_date_list.append(dt_dict)
                                   
                return report_date_list
            else:
                return []


class EtaskExtensionsListDownloadSerializerV2(serializers.ModelSerializer):
    parent_task=serializers.SerializerMethodField(required=False)
    sub_data = EtaskTask.objects.filter(parent_id=0,is_deleted=False)
    task_type_name=serializers.CharField(source='get_task_type_display')
    recurrance_frequency_name=serializers.CharField(source='get_recurrance_frequency_display')
    task_status_name=serializers.CharField(source='get_task_status_display')
    task_priority_name=serializers.CharField(source='get_task_priority_display')
    assign_by_name = serializers.SerializerMethodField()
    assign_to_name= serializers.SerializerMethodField()
    sub_assign_to_user_name= serializers.SerializerMethodField()
    reporting_dates = serializers.SerializerMethodField()
    start_date = serializers.SerializerMethodField()
    end_date = serializers.SerializerMethodField()
    requested_end_date = serializers.SerializerMethodField()

    class Meta:
        model= EtaskTask
        fields='__all__'

    def get_start_date(self, obj):
        return obj.start_date.strftime("%d %b %Y") if obj.start_date else ''

    def get_end_date(self, obj):
        return obj.end_date.strftime("%d %b %Y") if obj.end_date else ''

    def get_requested_end_date(self, obj):
        return obj.requested_end_date.strftime("%d %b %Y") if obj.requested_end_date else ''

    def get_parent_task(self,EtaskTask):
        if EtaskTask.parent_id:
            if EtaskTask.parent_id !=0:
                if self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject','task_description'):
                    parent_data=self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject','task_description')[0]
                    return parent_data

    def user_name(self, user_id):
        name = None
        full_name = ""
        name = User.objects.get(id=user_id)
        if name:
            full_name =  name.__dict__['first_name']+" "+name.__dict__['last_name']
        return full_name

    def get_assign_by_name(self,EtaskTask):
        name = None
        full_name = ""
        if EtaskTask.assign_by:
            name = User.objects.get(id=EtaskTask.assign_by.id)
            if name:
                full_name =  name.__dict__['first_name']+" "+name.__dict__['last_name']
                # #print("full_name",full_name)
            return full_name

    def get_sub_assign_to_user_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.sub_assign_to_user:
            name=User.objects.get(id=EtaskTask.sub_assign_to_user.id)
            if name:
                full_name= name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name

    def get_assign_to_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.assign_to:
            name =User.objects.get(id=EtaskTask.assign_to.id)
            if name:
                full_name=name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name
    def get_reporting_dates(self,EtaskTask):
        if EtaskTask.id:
            report_date_list = []
            report_date=ETaskReportingDates.objects.filter(task_type=1,task=EtaskTask.id,is_deleted=False).order_by('reporting_date')
            # #print("report_date",report_date)
            if report_date:
                for dt in report_date:
                    dt_dict={
                        'id':dt.id,
                        'reporting_date':dt.reporting_date,
                        'reporting_status':dt.reporting_status,
                        'reporting_status_name':dt.get_reporting_status_display()
                       
                    }
                    report_date_list.append(dt_dict)
                                   
                return report_date_list
            else:
                return []


class EtaskExtensionsRejectSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model=EtaskTask
        fields=('id','is_reject','updated_by')
    def update(self,instance,validated_data):
        instance.is_reject=True
        instance.updated_by=validated_data.get('updated_by')
        instance.save()
        return instance


class EtaskExtensionsRejectSerializerV2(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model=EtaskTask
        fields=('id','is_reject','updated_by')
    def update(self,instance,validated_data):
        with transaction.atomic():
            current_date = datetime.now()
            TaskExtentionDateMap.objects.filter(status=1,task=instance).update(
                                                                            status=3,
                                                                            approved_by=validated_data.get('updated_by'),
                                                                            updated_by=validated_data.get('updated_by'),
                                                                            updated_at=current_date
                                                                            )

            instance.is_reject=True
            instance.updated_by=validated_data.get('updated_by')
            instance.save()
            return instance


class EtaskTaskDateExtendedViewSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    reporting_date = serializers.ListField(required=False)

    class Meta:
        model = EtaskTask
        fields = '__all__'
        extra_fields = ('reporting_date')


    def update(self, instance, validated_data):
        instance.extended_date = validated_data['extended_date']
        instance.updated_by = validated_data.get('updated_by')
        #print(validated_data.get('updated_by'))
        #print(validated_data)
        reporting_date = validated_data.pop('reporting_date') if 'reporting_date' in validated_data else ""
        #print(reporting_date)

        if reporting_date:
            #print(reporting_date)

            for r_date in reporting_date:
                #print(r_date)
                #print(r_date['reporting_date'])
                rdate_details, created = ETaskReportingDates.objects.get_or_create(
                    task_type=1,
                    task=instance.id,
                    reporting_date=datetime.strptime(r_date['reporting_date'], "%Y-%m-%dT%H:%M:%S.%fZ"),
                    created_by=instance.created_by,
                    owned_by=instance.owned_by
                )
                #print(rdate_details, created)
                # #print('rdate_details',rdate_details,type(rdate_details))
                reporting_log, created = ETaskReportingActionLog.objects.get_or_create(
                    task_id=instance.id,
                    reporting_date_id=str(rdate_details),
                    updated_date=datetime.now().date(),
                    status=2,
                    created_by=instance.created_by,
                    owned_by=instance.owned_by
                )
                #print(reporting_log, created)

        instance.save()
        return instance


class EtaskTaskDateExtendedViewSerializerV2(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    reporting_date = serializers.ListField(required=False)
    approved_comment = serializers.CharField(required=False)
    mark_as_reported_id = serializers.IntegerField(required=False)

    class Meta:
        model = EtaskTask
        fields = '__all__'
        extra_fields = ('reporting_date','approved_comment','mark_as_reported_id',)

    def update(self, instance, validated_data):
        with transaction.atomic():
            current_date = datetime.now()
            reporting_date = validated_data.pop('reporting_date') if 'reporting_date' in validated_data else []
            mark_as_reported_id = validated_data.get('mark_as_reported_id')
            updated_by = validated_data.get('updated_by')

            if instance.parent_id:
                parent_task = EtaskTask.objects.filter(id=instance.parent_id).first()
                extended_map = TaskExtentionDateMap.objects.filter(status=2,task=parent_task)

                clean_data = TaskExtentionDateMap.objects.filter(status=1,task=parent_task)
                if clean_data.count() > 1:
                    for deleted_data in clean_data[1:]:
                        deleted_data.delete()

                task_extention_date, is_created = TaskExtentionDateMap.objects.get_or_create(status=1,task=parent_task)
                task_extention_date.status=2
                task_extention_date.approved_by=validated_data.get('updated_by')
                task_extention_date.extended_date=validated_data['extended_date'].replace(hour=23, minute=59)
                task_extention_date.updated_by=validated_data.get('updated_by')
                task_extention_date.updated_at=current_date
                task_extention_date.approved_comment=validated_data.get('approved_comment')
                task_extention_date.extend_with_delay= extended_map.count() > 2
                task_extention_date.save()
                
                
                parent_task.extended_date = validated_data['extended_date'].replace(hour=23, minute=59)
                parent_task.updated_by = validated_data.get('updated_by')
                parent_task.extend_with_delay= extended_map.count() > 2
                parent_task.save()

            
            extended_map = TaskExtentionDateMap.objects.filter(status=2,task=instance)
        
            clean_data = TaskExtentionDateMap.objects.filter(status=1,task=instance)
            if clean_data.count() > 1:
                for deleted_data in clean_data[1:]:
                    deleted_data.delete()
            
            task_extention_date, is_created = TaskExtentionDateMap.objects.get_or_create(status=1,task=instance)
            task_extention_date.status=2
            task_extention_date.approved_by=updated_by
            task_extention_date.extended_date=validated_data.get('extended_date').replace(hour=23, minute=59)
            task_extention_date.updated_by=updated_by
            task_extention_date.updated_at=current_date
            task_extention_date.approved_comment=validated_data.get('approved_comment')
            task_extention_date.extend_with_delay= extended_map.count() > 2
            task_extention_date.save()
            

            instance.extended_date = validated_data.get('extended_date').replace(hour=23, minute=59)
            instance.updated_by = updated_by
            instance.extend_with_delay= extended_map.count() > 2
            instance.save()

            

            # Default Reporting Date will be added #
            reporting_date_dict = {str(validated_data['extended_date'].date()):str(validated_data['extended_date'].replace(hour=10, minute=00).strftime("%Y-%m-%dT%H:%M:%S"))}
            reporting_date_dict.update({rd['reporting_date'].split('T')[0]: rd['reporting_date'].split('.')[0] for rd in reporting_date})
            reporting_date_with_manual_time = {rd['reporting_date'].split('T')[0]: rd['is_manual_time_entry'] for rd in reporting_date}

            reporting_end_date_dict = {str(validated_data['extended_date'].date()):str(validated_data['extended_date'].replace(hour=10, minute=00).strftime("%Y-%m-%dT%H:%M:%S"))}
            reporting_end_date_dict.update({rd['reporting_end_date'].split('T')[0]: rd['reporting_end_date'].split('.')[0] for rd in reporting_date})

            default_reporting_dates = EtaskMonthlyReportingDate.objects.filter(employee=instance.assign_to,
                                                owned_by=instance.owner).values_list('field_value',flat=True)

            for date_ob in daterange(instance.start_date.date(),validated_data.get('extended_date').date()):
                if date_ob.day in default_reporting_dates and date_ob >= current_date.date():
                    default_reporting_date = EtaskMonthlyReportingDate.objects.filter(employee=instance.assign_to,
                                    field_value=date_ob.day,owned_by=instance.owner).values('field_value','start_time','end_time').first()
                    
                    reporting_date_dict[str(date_ob)] = str(date_ob)+'T'+str(default_reporting_date['start_time']) if default_reporting_date['start_time'] else str(date_ob)+'T10:00:00'
                    reporting_end_date_dict[str(date_ob)] = str(date_ob)+'T'+str(default_reporting_date['end_time']) if default_reporting_date['end_time'] else str(date_ob)+'T10:00:00'
                    break

            existed_reporting = list(ETaskReportingDates.objects.filter(task=instance.id,owned_by=instance.owner,
                                reporting_date__date__in=reporting_date_dict.keys()).values_list('reporting_date__date',flat=True))
            existed_reporting = list(map(str,existed_reporting))
            final_reporting_dict = {k:v for k,v in reporting_date_dict.items() if k not in existed_reporting}
            reporting_obj_list = []
            if final_reporting_dict:
                #print(reporting_date)

                for k,v in final_reporting_dict.items():
                    #print(r_date)
                    #print(r_date['reporting_date'])
                    rdate_details, created = ETaskReportingDates.objects.get_or_create(
                        task_type=1,
                        task=instance.id,
                        is_manual_time_entry=reporting_date_with_manual_time.get(k,False),
                        reporting_date=datetime.strptime(v, "%Y-%m-%dT%H:%M:%S"),
                        reporting_end_date=datetime.strptime(reporting_end_date_dict[k], "%Y-%m-%dT%H:%M:%S"),
                        created_by=instance.created_by,
                        owned_by=instance.owner
                    )
                    if created:
                        reporting_obj_list.append(rdate_details)
                    
                    #print(rdate_details, created)
                    # #print('rdate_details',rdate_details,type(rdate_details))
                    reporting_log, created = ETaskReportingActionLog.objects.get_or_create(
                        task_id=instance.id,
                        reporting_date_id=str(rdate_details),
                        updated_date=datetime.now().date(),
                        status=2,
                        created_by=instance.created_by,
                        owned_by=instance.owner
                    )
                    #print(reporting_log, created)

            # Creating and mail appointment
            create_appointment(reporting_dates=reporting_obj_list)

            if mark_as_reported_id:
                report_obj = ETaskReportingDates.objects.get(id=mark_as_reported_id)
                report_obj.task_type = 1
                report_obj.task_status=1
                report_obj.reporting_status = 1
                report_obj.actual_reporting_date = current_date
                report_obj.updated_by = updated_by
                report_obj.save()
                prev_action= ETaskReportingActionLog.objects.filter(
                    task_id = report_obj.task,
                    reporting_date_id = report_obj.id,
                    is_deleted=False
                    ).update(is_deleted=True)
                reporting_log = ETaskReportingActionLog.objects.create(
                    task_id = report_obj.task,
                    reporting_date_id = report_obj.id,
                    status = 1,
                    updated_by = updated_by
                    )

            '''
            Rajesh Samui
            03/07/2020
            Topic :: Sending Notification
            '''

            users = [instance.assign_to]
            title = 'Extention request for the task with task_code {} has been approved.'.format(instance.task_code_id)
            body ='Task: {} \nDetails:{}'.format(instance.task_subject,instance.task_description)

            data = {
                        "app_module":"etask",
                        "type":"task",
                        "id":instance.id
                    }
            data_str = json.dumps(data)
            notification_id = store_sent_notification(users=users,body=body,title=title,data=data_str,app_module_name='etask')
            send_notification(users=users,body=body,title=title,data=data,notification_id=notification_id)
            
            return instance


class EtaskMassDateExtendedSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    task_ids = serializers.ListField(required=False)
    approved_comment = serializers.CharField(required=False,allow_blank=True,allow_null=True)
    request_status = serializers.CharField(required=False)
    message = serializers.CharField(required=False)
    is_confirm = serializers.BooleanField(default=False)
    extend_with_delay = serializers.BooleanField(default=False)

    class Meta:
        model = EtaskTask
        fields = ('is_confirm','updated_by','extended_date','approved_comment','task_ids','request_status','message','extend_with_delay')

    def multiple_extended(self,task=None,extended_date=None,updated_by=None,current_date=None,approved_comment=None,extend_with_delay=False):

        if task.parent_id:
            parent_task = EtaskTask.objects.filter(id=task.parent_id).first()
            extended_map = TaskExtentionDateMap.objects.filter(status=2,task=parent_task)
            calculated_extend_with_delay = extend_with_delay if extend_with_delay else extended_map.count() > 2
            
            clean_data = TaskExtentionDateMap.objects.filter(status=1,task=parent_task)
            if clean_data.count() > 1:
                for deleted_data in clean_data[1:]:
                    deleted_data.delete()

            task_extention_date, is_created = TaskExtentionDateMap.objects.get_or_create(status=1,task=parent_task)
            task_extention_date.status=2
            task_extention_date.approved_by=updated_by
            task_extention_date.extended_date=extended_date
            task_extention_date.updated_by=updated_by
            task_extention_date.updated_at=current_date
            task_extention_date.approved_comment=approved_comment
            task_extention_date.extend_with_delay= calculated_extend_with_delay
            task_extention_date.save()
            
            
            parent_task.extended_date = extended_date
            parent_task.updated_by = updated_by
            parent_task.save()

        extended_map = TaskExtentionDateMap.objects.filter(status=2,task=task)
        calculated_extend_with_delay = extend_with_delay if extend_with_delay else extended_map.count() > 2
        
        clean_data = TaskExtentionDateMap.objects.filter(status=1,task=task)
        if clean_data.count() > 1:
            for deleted_data in clean_data[1:]:
                deleted_data.delete()

        task_extention_date, is_created = TaskExtentionDateMap.objects.get_or_create(status=1,task=task)
        task_extention_date.status=2
        task_extention_date.approved_by=updated_by
        task_extention_date.extended_date=extended_date
        task_extention_date.updated_by=updated_by
        task_extention_date.updated_at=current_date
        task_extention_date.approved_comment=approved_comment
        task_extention_date.extend_with_delay= calculated_extend_with_delay
        task_extention_date.save()
        

        task.extended_date = extended_date
        task.updated_by = updated_by
        task.extend_with_delay= calculated_extend_with_delay
        task.save()

        # Default Reporting Date will be added #
        reporting_date_dict = {str(extended_date.date()):str(extended_date.replace(hour=10, minute=00).strftime("%Y-%m-%dT%H:%M:%S"))}
        default_reporting_dates = EtaskMonthlyReportingDate.objects.filter(employee=task.assign_to,
                                            owned_by=task.owner).values_list('field_value',flat=True)

        for date_ob in daterange(task.start_date.date(),extended_date.date()):
            if date_ob.day in default_reporting_dates and date_ob >= current_date.date():
                default_reporting_date = EtaskMonthlyReportingDate.objects.filter(employee=task.assign_to,
                                field_value=date_ob.day,owned_by=task.owner).values('field_value','start_time').first()
                
                reporting_date_dict[str(date_ob)] = str(date_ob)+'T'+str(default_reporting_date['start_time']) if default_reporting_date['start_time'] else str(date_ob)+'T10:00:00'
                break

        existed_reporting = list(ETaskReportingDates.objects.filter(task=task.id,owned_by=task.owner,
                            reporting_date__date__in=reporting_date_dict.keys()).values_list('reporting_date__date',flat=True))
        existed_reporting = list(map(str,existed_reporting))
        final_reporting_dict = {k:v for k,v in reporting_date_dict.items() if k not in existed_reporting}


        if final_reporting_dict:
            for k,v in final_reporting_dict.items():
                rdate_details, created = ETaskReportingDates.objects.get_or_create(
                    task_type=1,
                    task=task.id,
                    reporting_date=datetime.strptime(v, "%Y-%m-%dT%H:%M:%S"),
                    created_by=task.created_by,
                    owned_by=task.owner
                )
                reporting_log, created = ETaskReportingActionLog.objects.get_or_create(
                    task_id=task.id,
                    reporting_date_id=str(rdate_details),
                    updated_date=datetime.now().date(),
                    status=2,
                    created_by=task.created_by,
                    owned_by=task.owner
                )


            '''
            Rajesh Samui
            03/07/2020
            Topic :: Sending Notification
            '''

            users = [task.assign_to]
            title = 'Extention request for the task with task_code {} has been approved.'.format(task.task_code_id)
            body ='Task: {} \nDetails:{}'.format(task.task_subject,task.task_description)

            data = {
                        "app_module":"etask",
                        "type":"task",
                        "id":task.id
                    }
            data_str = json.dumps(data)
            notification_id = store_sent_notification(users=users,body=body,title=title,data=data_str,app_module_name='etask')
            send_notification(users=users,body=body,title=title,data=data,notification_id=notification_id)

        return

    def create(self, validated_data):
        with transaction.atomic():
            current_date = datetime.now()
            task_ids = validated_data.pop('task_ids')
            updated_by = validated_data.pop('updated_by')
            extended_date = validated_data.get('extended_date').replace(hour=23, minute=59) if validated_data.get('extended_date') else None
            approved_comment = validated_data.pop('approved_comment')
            extend_with_delay = validated_data.get('extend_with_delay',False)
            is_confirm = validated_data.pop('is_confirm')

            tasks = EtaskTask.objects.filter(id__in=task_ids)

            success_list = list()
            error_list = list()


            for task in tasks:
                if extended_date and (updated_by == task.owner) and ((task.extended_date and task.extended_date.date()<extended_date.date()) or (not task.extended_date and task.end_date.date()<extended_date.date())):
                    success_list.append(task.task_code_id)
                elif not extended_date and (updated_by == task.owner):
                    success_list.append(task.task_code_id)
                else:
                    error_list.append(task.task_code_id)
            
            if not error_list or is_confirm:
                for task in tasks:
                    if extended_date and (updated_by == task.owner) and ((task.extended_date and task.extended_date.date()<extended_date.date()) or (not task.extended_date and task.end_date.date()<extended_date.date())):
                        self.multiple_extended(task=task,extended_date=extended_date,updated_by=updated_by,current_date=current_date,approved_comment=approved_comment,extend_with_delay=extend_with_delay)
                    elif not extended_date and (updated_by == task.owner):
                        extended_date = extended_date if extended_date else task.requested_end_date
                        self.multiple_extended(task=task,extended_date=extended_date,updated_by=updated_by,current_date=current_date,approved_comment=approved_comment,extend_with_delay=extend_with_delay)

                
            error_msg = 'Task with task_code {} can not be extended'.format(', '.join(error_list))
            success_msg = 'Task with task_code {} has been extended'.format(', '.join(success_list))
            msg = ''
            if error_list and success_list:
                msg = '{} and {}.'.format(success_msg,error_msg)
            elif error_list and not success_list:
                msg = '{}.'.format(error_msg)
            elif not error_list and success_list:
                msg = '{}.'.format(success_msg)
                
            validated_data['request_status'] = 1 if not error_list or is_confirm else 0
            validated_data['message'] = msg
            return validated_data


class EtaskTaskDateExtendedWithDelaySerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    reporting_date = serializers.ListField(required=False)

    class Meta:
        model = EtaskTask
        fields = '__all__'
        extra_fields = ('reporting_date',)

    def update(self, instance, validated_data):
        instance.extend_with_delay = True
        instance.extended_date = validated_data['extended_date']
        instance.updated_by = validated_data.get('updated_by')
        reporting_date = validated_data.pop('reporting_date') if 'reporting_date' in validated_data else ""
        if reporting_date:
            #print(reporting_date)

            for r_date in reporting_date:
                #print(r_date)
                #print(r_date['reporting_date'])
                rdate_details, created = ETaskReportingDates.objects.get_or_create(
                    task_type=1,
                    task=instance.id,
                    reporting_date=datetime.strptime(r_date['reporting_date'], "%Y-%m-%dT%H:%M:%S.%fZ"),
                    created_by=instance.created_by,
                    owned_by=instance.owned_by
                )
                #print(rdate_details, created)
                # #print('rdate_details',rdate_details,type(rdate_details))
                reporting_log, created = ETaskReportingActionLog.objects.get_or_create(
                    task_id=instance.id,
                    reporting_date_id=str(rdate_details),
                    updated_date=datetime.now().date(),
                    status=2,
                    created_by=instance.created_by,
                    owned_by=instance.owned_by
                )
                #print(reporting_log, created)

        instance.save()
        return instance


class EtaskTaskDateExtendedWithDelaySerializerV2(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    reporting_date = serializers.ListField(required=False)
    approved_comment = serializers.CharField(required=False)
    mark_as_reported_id = serializers.IntegerField(required=False)

    class Meta:
        model = EtaskTask
        fields = '__all__'
        extra_fields = ('reporting_date','approved_comment','mark_as_reported_id')

    def update(self, instance, validated_data):
        with transaction.atomic():
            current_date = datetime.now()
            mark_as_reported_id = validated_data.get('mark_as_reported_id')
            reporting_date = validated_data.pop('reporting_date') if 'reporting_date' in validated_data else ""
            updated_by = validated_data.get('updated_by')

            if instance.parent_id:
                parent_task = EtaskTask.objects.filter(id=instance.parent_id).first()
                
                clean_data = TaskExtentionDateMap.objects.filter(status=1,task=parent_task)
                if clean_data.count() > 1:
                    for deleted_data in clean_data[1:]:
                        deleted_data.delete()

                task_extention_date, is_created = TaskExtentionDateMap.objects.get_or_create(status=1,task=parent_task)
                task_extention_date.status=2
                task_extention_date.extend_with_delay=True
                task_extention_date.approved_by=updated_by
                task_extention_date.extended_date=validated_data['extended_date'].replace(hour=23, minute=59)
                task_extention_date.updated_by=updated_by
                task_extention_date.updated_at=current_date
                task_extention_date.approved_comment=validated_data.get('approved_comment')
                task_extention_date.save()
                
                parent_task.extend_with_delay = True
                parent_task.extended_date = validated_data['extended_date'].replace(hour=23, minute=59)
                parent_task.updated_by = updated_by
                parent_task.save()

            clean_data = TaskExtentionDateMap.objects.filter(status=1,task=instance)
            if clean_data.count() > 1:
                for deleted_data in clean_data[1:]:
                    deleted_data.delete()

            task_extention_date, is_created = TaskExtentionDateMap.objects.get_or_create(status=1,task=instance)
            task_extention_date.status=2
            task_extention_date.extend_with_delay=True
            task_extention_date.approved_by=updated_by
            task_extention_date.extended_date=validated_data['extended_date'].replace(hour=23, minute=59)
            task_extention_date.updated_by=updated_by
            task_extention_date.updated_at=current_date
            task_extention_date.approved_comment=validated_data.get('approved_comment')
            task_extention_date.save()


            instance.extend_with_delay = True
            instance.extended_date = validated_data['extended_date'].replace(hour=23, minute=59)
            instance.updated_by = updated_by
            instance.save()
            
            # Default Reporting Date will be added #
            reporting_date_dict = {str(validated_data['extended_date'].date()):str(validated_data['extended_date'].replace(hour=10, minute=00).strftime("%Y-%m-%dT%H:%M:%S"))}
            reporting_date_dict.update({rd['reporting_date'].split('T')[0]: rd['reporting_date'].split('.')[0] for rd in reporting_date})
            reporting_date_with_manual_time = {rd['reporting_date'].split('T')[0]: rd['is_manual_time_entry'] for rd in reporting_date}

            reporting_end_date_dict = {str(validated_data['extended_date'].date()):str(validated_data['extended_date'].replace(hour=10, minute=00).strftime("%Y-%m-%dT%H:%M:%S"))}
            reporting_end_date_dict.update({rd['reporting_end_date'].split('T')[0]: rd['reporting_end_date'].split('.')[0] for rd in reporting_date})

            default_reporting_dates = EtaskMonthlyReportingDate.objects.filter(employee=instance.assign_to,
                                                owned_by=instance.owner).values_list('field_value',flat=True)

            for date_ob in daterange(instance.start_date.date(),validated_data.get('extended_date').date()):
                if date_ob.day in default_reporting_dates and date_ob >= current_date.date():
                    default_reporting_date = EtaskMonthlyReportingDate.objects.filter(employee=instance.assign_to,
                                    field_value=date_ob.day,owned_by=instance.owner).values('field_value','start_time','end_time').first()
                    
                    reporting_date_dict[str(date_ob)] = str(date_ob)+'T'+str(default_reporting_date['start_time']) if default_reporting_date['start_time'] else str(date_ob)+'T10:00:00'
                    reporting_end_date_dict[str(date_ob)] = str(date_ob)+'T'+str(default_reporting_date['end_time']) if default_reporting_date['end_time'] else str(date_ob)+'T10:00:00'
                    break

            existed_reporting = list(ETaskReportingDates.objects.filter(task=instance.id,owned_by=instance.owner,
                                reporting_date__date__in=reporting_date_dict.keys()).values_list('reporting_date__date',flat=True))
            existed_reporting = list(map(str,existed_reporting))
            final_reporting_dict = {k:v for k,v in reporting_date_dict.items() if k not in existed_reporting}
            
            reporting_obj_list = list()
            if final_reporting_dict:
                for k,v in final_reporting_dict.items():
                    rdate_details, created = ETaskReportingDates.objects.get_or_create(
                        task_type=1,
                        task=instance.id,
                        is_manual_time_entry=reporting_date_with_manual_time.get(k,False),
                        reporting_date=datetime.strptime(v, "%Y-%m-%dT%H:%M:%S"),
                        reporting_end_date=datetime.strptime(reporting_end_date_dict[k], "%Y-%m-%dT%H:%M:%S"),
                        created_by=instance.created_by,
                        owned_by=instance.owner
                    )
                    if created:
                        reporting_obj_list.append(rdate_details)
                    
                    reporting_log, created = ETaskReportingActionLog.objects.get_or_create(
                        task_id=instance.id,
                        reporting_date_id=str(rdate_details),
                        updated_date=datetime.now().date(),
                        status=2,
                        created_by=instance.created_by,
                        owned_by=instance.owner
                    )
            
            # Creating and mail appointment
            create_appointment(reporting_dates=reporting_obj_list)

            if mark_as_reported_id:
                report_obj = ETaskReportingDates.objects.get(id=mark_as_reported_id)
                report_obj.task_type = 1
                report_obj.task_status=1
                report_obj.reporting_status = 1
                report_obj.actual_reporting_date = current_date
                report_obj.updated_by = updated_by
                report_obj.save()
                prev_action= ETaskReportingActionLog.objects.filter(
                    task_id = report_obj.task,
                    reporting_date_id = report_obj.id,
                    is_deleted=False
                    ).update(is_deleted=True)
                reporting_log = ETaskReportingActionLog.objects.create(
                    task_id = report_obj.task,
                    reporting_date_id = report_obj.id,
                    status = 1,
                    updated_by = updated_by
                    )

            return instance


class EtaskTaskReopenAndExtendWithDelaySerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    reporting_date = serializers.ListField(required=False)

    class Meta:
        model = EtaskTask
        fields = '__all__'
        extra_fields = ('reporting_date')

    def update(self, instance, validated_data):
        instance.extend_with_delay = True
        instance.extended_date = validated_data['extended_date']
        instance.completed_date = None
        instance.task_status = 1
        instance.updated_by = validated_data.get('updated_by')
        reporting_date = validated_data.pop('reporting_date') if 'reporting_date' in validated_data else ""

        if reporting_date:
            #print(reporting_date)

            for r_date in reporting_date:
                #print(r_date)
                #print(r_date['reporting_date'])
                rdate_details, created = ETaskReportingDates.objects.get_or_create(
                    task_type=1,
                    task=instance.id,
                    reporting_date=datetime.strptime(r_date['reporting_date'], "%Y-%m-%dT%H:%M:%S.%fZ"),
                    created_by=instance.created_by,
                    owned_by=instance.owned_by
                )
                #print(rdate_details, created)
                # #print('rdate_details',rdate_details,type(rdate_details))
                reporting_log, created = ETaskReportingActionLog.objects.get_or_create(
                    task_id=instance.id,
                    reporting_date_id=str(rdate_details),
                    updated_date=datetime.now().date(),
                    status=2,
                    created_by=instance.created_by,
                    owned_by=instance.owned_by
                )
                #print(reporting_log, created)

        instance.save()
        return instance


class EtaskTaskReopenAndExtendWithDelaySerializerV2(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    reporting_date = serializers.ListField(required=False)
    reopen_with_delay = serializers.BooleanField(required=False)
    approved_comment = serializers.CharField(required=False)

    class Meta:
        model = EtaskTask
        fields = '__all__'
        extra_fields = ('reporting_date','reopen_with_delay','approved_comment')

    def update(self, instance, validated_data):
        with transaction.atomic():
            current_date = datetime.now()
            updated_by = validated_data.get('updated_by')

            if (instance.extended_date and instance.extended_date.date()>validated_data['extended_date'].date()) or (not instance.extended_date and instance.end_date.date()>validated_data['extended_date'].date()):
                raise APIException({'msg':'Please Give Extended Date After The Task End Date',
                            "request_status": 0
                            })

            clean_data = TaskExtentionDateMap.objects.filter(status=1,task=instance)
            if clean_data.count() > 1:
                for deleted_data in clean_data[1:]:
                    deleted_data.delete()

            task_extention_date, is_created = TaskExtentionDateMap.objects.get_or_create(status=1,task=instance)
            task_extention_date.status=2
            task_extention_date.extend_with_delay=True
            task_extention_date.approved_by=updated_by
            task_extention_date.extended_date=validated_data['extended_date'].replace(hour=23, minute=59)
            task_extention_date.updated_by=updated_by
            task_extention_date.updated_at=current_date
            task_extention_date.requested_by=instance.completed_by
            task_extention_date.save()

            task_complete_reopen, is_created = TaskCompleteReopenMap.objects.get_or_create(task=instance,status=1)
            task_complete_reopen.status = 3
            task_complete_reopen.reopen_with_delay = validated_data.get('reopen_with_delay', False)
            task_complete_reopen.approved_date = current_date
            task_complete_reopen.approved_by = updated_by
            task_complete_reopen.approved_comment = validated_data.get('approved_comment')
            task_complete_reopen.updated_by = updated_by
            task_complete_reopen.updated_at = current_date
            task_complete_reopen.save()


            instance.extend_with_delay = True
            instance.extended_date = validated_data['extended_date'].replace(hour=23, minute=59)
            instance.completed_date = None
            instance.task_status = 1
            instance.updated_by = updated_by
            instance.save()

            reporting_date = validated_data.pop('reporting_date') if 'reporting_date' in validated_data else ""
            
            # Default Reporting Date will be added #
            reporting_date_dict = {str(validated_data['extended_date'].date()):str(validated_data['extended_date'].replace(hour=10, minute=00).strftime("%Y-%m-%dT%H:%M:%S"))}
            reporting_date_dict.update({rd['reporting_date'].split('T')[0]: rd['reporting_date'].split('.')[0] for rd in reporting_date})
            reporting_date_with_manual_time = {rd['reporting_date'].split('T')[0]: rd['is_manual_time_entry'] for rd in reporting_date}

            reporting_end_date_dict = {str(validated_data['extended_date'].date()):str(validated_data['extended_date'].replace(hour=10, minute=00).strftime("%Y-%m-%dT%H:%M:%S"))}
            reporting_end_date_dict.update({rd['reporting_end_date'].split('T')[0]: rd['reporting_end_date'].split('.')[0] for rd in reporting_date})
            
            
            default_reporting_dates = EtaskMonthlyReportingDate.objects.filter(employee=instance.assign_to,
                                                owned_by=instance.owner).values_list('field_value',flat=True)

            for date_ob in daterange(instance.start_date.date(),validated_data.get('extended_date').date()):
                if date_ob.day in default_reporting_dates and date_ob >= current_date.date():
                    default_reporting_date = EtaskMonthlyReportingDate.objects.filter(employee=instance.assign_to,
                                    field_value=date_ob.day,owned_by=instance.owner).values('field_value','start_time','end_time').first()
                    
                    reporting_date_dict[str(date_ob)] = str(date_ob)+'T'+str(default_reporting_date['start_time']) if default_reporting_date['start_time'] else str(date_ob)+'T10:00:00'
                    reporting_end_date_dict[str(date_ob)] = str(date_ob)+'T'+str(default_reporting_date['end_time']) if default_reporting_date['end_time'] else str(date_ob)+'T10:00:00'
                    break

            existed_reporting = list(ETaskReportingDates.objects.filter(task=instance.id,owned_by=instance.owner,
                                reporting_date__date__in=reporting_date_dict.keys()).values_list('reporting_date__date',flat=True))
            existed_reporting = list(map(str,existed_reporting))
            final_reporting_dict = {k:v for k,v in reporting_date_dict.items() if k not in existed_reporting}
            reporting_obj_list = list()
            if final_reporting_dict:
                #print(reporting_date)

                for k,v in final_reporting_dict.items():
                    #print(r_date)
                    #print(r_date['reporting_date'])
                    rdate_details, created = ETaskReportingDates.objects.get_or_create(
                        task_type=1,
                        task=instance.id,
                        is_manual_time_entry=reporting_date_with_manual_time.get(k,False),
                        reporting_date=datetime.strptime(v, "%Y-%m-%dT%H:%M:%S"),
                        reporting_end_date=datetime.strptime(reporting_end_date_dict[k], "%Y-%m-%dT%H:%M:%S"),
                        created_by=instance.created_by,
                        owned_by=instance.owner
                    )
                    if created:
                        reporting_obj_list.append(rdate_details)
                    
                    #print(rdate_details, created)
                    # #print('rdate_details',rdate_details,type(rdate_details))
                    reporting_log, created = ETaskReportingActionLog.objects.get_or_create(
                        task_id=instance.id,
                        reporting_date_id=str(rdate_details),
                        updated_date=datetime.now().date(),
                        status=2,
                        created_by=instance.created_by,
                        owned_by=instance.owner
                    )

            # Creating and mail appointment
            create_appointment(reporting_dates=reporting_obj_list)
            
            return instance


class EtaskTaskStartDateShiftSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    shift_date=serializers.DateTimeField(required=False)
    class Meta:
        model = EtaskTask
        fields = ('id','start_date','end_date','updated_by','shift_date','extended_date')
       
    def update(self, instance, validated_data):
        shift_date=validated_data.get('shift_date') 
        #print('shift_date',shift_date)
        #print('extended_date',instance.extended_date)
        if instance.extended_date:
            if shift_date.date()<=instance.extended_date.date():
                instance.start_date=shift_date
                instance.updated_by = validated_data.get('updated_by')
                instance.save()
                return instance
        elif shift_date.date()<=instance.end_date.date():
            instance.start_date=shift_date
            instance.updated_by = validated_data.get('updated_by')
            instance.save()
            return instance
        else:
            raise APIException({'msg':'Please Give Shift Date Before The Task End Date',
                        "request_status": 0
                        })


class EtaskTaskStartDateShiftSerializerV2(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    shift_date=serializers.DateTimeField(required=False)
    class Meta:
        model = EtaskTask
        fields = ('id','start_date','end_date','updated_by','shift_date','extended_date')
       
    def update(self, instance, validated_data):
        shift_date=validated_data.get('shift_date') 
        #print('shift_date',shift_date)
        #print('extended_date',instance.extended_date)
        if instance.extended_date and shift_date.date()<=instance.extended_date.date():
            instance.shifted_date=shift_date
            instance.updated_by = validated_data.get('updated_by')
            instance.save()
            return instance
        elif shift_date.date()<=instance.end_date.date():
            instance.shifted_date=shift_date
            instance.updated_by = validated_data.get('updated_by')
            instance.save()
            return instance
        else:
            raise APIException({'msg':'Please Give Shift Date Before The Task End Date',
                        "request_status": 0
                        })


class EtaskMassStartDateShiftSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    shift_date=serializers.DateTimeField(required=False)
    task_ids = serializers.ListField(required=False)
    message = serializers.CharField(required=False,allow_blank=True,allow_null=True)
    request_status = serializers.IntegerField(required=False)
    is_confirm = serializers.BooleanField(default=False)

    class Meta:
        model = EtaskTask
        fields = ('updated_by','shift_date','task_ids','message','request_status','is_confirm')
       
    def create(self, validated_data):
        shift_date=validated_data.pop('shift_date')
        task_ids = validated_data.pop('task_ids')
        updated_by = validated_data.pop('updated_by')
        message = validated_data.pop('message')
        is_confirm = validated_data.pop('is_confirm')
        tasks = EtaskTask.objects.filter(id__in=task_ids)
        success_list = list()
        error_list = list()
        
        for task in tasks:
            if task.task_status == 1:
                if task.extended_date:
                    if shift_date.date() <= task.extended_date.date():
                        success_list.append(task.task_code_id)
                    else:
                        error_list.append(task.task_code_id)
                elif shift_date.date() <= task.end_date.date():
                    success_list.append(task.task_code_id)
                else:
                    error_list.append(task.task_code_id)
            else:
                error_list.append(task.task_code_id)

        if not error_list or is_confirm:
            for task in tasks:
                if task.task_status == 1:
                    if task.extended_date:
                        if shift_date.date() <= task.extended_date.date():
                            task.shifted_date = shift_date
                            task.updated_by = updated_by
                            task.shifted_comment = message
                            task.save()
                            
                    elif shift_date.date() <= task.end_date.date():
                        task.shifted_date = shift_date
                        task.updated_by = updated_by
                        task.shifted_comment = message
                        task.save()



        error_msg = 'Task with task_code {} can not be shifted'.format(', '.join(error_list))
        success_msg = 'Task with task_code {} can be shifted'.format(', '.join(success_list))
        msg = ''
        if error_list and success_list:
            msg = '{} and {}.'.format(success_msg,error_msg)
        elif error_list and not success_list:
            msg = '{}.'.format(error_msg)
        elif not error_list and success_list:
            msg = '{}.'.format(success_msg)
            
        validated_data['request_status'] = 1 if not error_list or is_confirm else 0
        validated_data['message'] = msg
        return validated_data

class EtaskAllTypeTaskCountViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = EtaskTask
        fields = '__all__'

class EtaskTaskCCListviewSerializer(serializers.ModelSerializer):
    sub_tasks = serializers.SerializerMethodField()

    class Meta:
        model = EtaskUserCC
        fields = '__all__'
        extra_fields = ('sub_tasks',)

    def get_sub_tasks(self, obj):
        sub_tasks_data = EtaskTask.objects.filter(~Q(task_status=4),parent_id=obj.task.id,is_deleted=False).values('id','task_subject')
        return sub_tasks_data if sub_tasks_data else list() 
       

class EtaskTaskCCListDownloadSerializer(serializers.ModelSerializer):
    class Meta:
        model = EtaskUserCC
        fields = '__all__'


class EtaskTaskTransferredListviewSerializer(serializers.ModelSerializer):
    task_status_name=serializers.CharField(source='get_task_status_display')
    class Meta:
        model = EtaskTask
        fields = '__all__'

class ETaskCommentsSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    cost_details=serializers.ListField(required=False)
    other_details=serializers.ListField(required=False)
    
    class Meta:
        model=ETaskComments
        fields='__all__'
        extra_fields=('cost_details','other_details')

    def create(self,validated_data):
        try:
            loggedin_user=self.context['request'].user.id
            #print('loggedin_user',loggedin_user)
            cost_details=validated_data.pop('cost_details')if 'cost_details' in validated_data else ""
            other_details=validated_data.pop('other_details')if 'other_details' in validated_data else "" 
            created_by=validated_data.get('created_by')
            owned_by=validated_data.get('owned_by')
            cost_details_list=[]
            other_details_list=[]
            comment_save_send = self.context['request'].query_params.get('comment_save_send',None)
            #print('comment_save_send',comment_save_send)
            with transaction.atomic():
                e_task_comments=ETaskComments.objects.create(**validated_data)
                # #print("e_task_comments-->",e_task_comments)
                users_list=EtaskTask.objects.filter(id=str(validated_data.get('task')),is_deleted=False).values('assign_by','assign_to')
                # #print('assign_by',users_list[0]['assign_by'])
                user_cat_list=users_list.values('task_categories','sub_assign_to_user')
                # #print('user_cat_list',user_cat_list,user_cat_list[0]['task_categories'])
                email_list=[]
                if user_cat_list[0]['task_categories'] == 1:
                    comment_view=ETaskCommentsViewers.objects.create(etcomments=e_task_comments,
                                                                user_id=users_list[0]['assign_by'],
                                                                task=validated_data.get('task'),                          
                                                                created_by=created_by,
                                                                owned_by=owned_by
                                                                )
                    # #print('comment_view',comment_view)
                    if loggedin_user == users_list[0]['assign_by']:
                        viewer=ETaskCommentsViewers.objects.filter(etcomments=e_task_comments,user_id=users_list[0]['assign_by'],
                                                                    task=validated_data.get('task')).update(is_view=True)

                    assign_by_mail_id = TCoreUserDetail.objects.filter(cu_user_id=users_list[0]['assign_by'],cu_is_deleted=False).values('cu_alt_email_id')
                    email_list.append(assign_by_mail_id[0]['cu_alt_email_id'])
                    #print('email_list1',email_list)
                    if comment_save_send == 'send':
                        mail_data = {
                                "name": userdetails(users_list[0]['assign_by']),
                                "comment_sub": validated_data.get('comments'),
                                "commented_by": userdetails(users_list[0]['assign_by'])
                                    }
                        # #print('mail_data',mail_data)
                        # mail_class = GlobleMailSend('ET-COMMENT', email_list)
                        # mail_thread = Thread(target = mail_class.mailsend, args = (mail_data,))
                        # mail_thread.start()
                        send_mail_list('ET-COMMENT', email_list, mail_data, ics='')
                else:
                    for user in users_list:
                        #print('user',user)
                        for k,v in user.items():
                            #print('v',v,type(v))
                            comment_view=ETaskCommentsViewers.objects.create(etcomments=e_task_comments,
                                                                user_id=v,
                                                                task=validated_data.get('task'),                                                         
                                                                created_by=created_by,
                                                                owned_by=owned_by
                                                                )
                            # #print('comment_view',comment_view)
                            if loggedin_user == v:
                                viewer=ETaskCommentsViewers.objects.filter(etcomments=e_task_comments,user_id=v,
                                                                    task=validated_data.get('task')).update(is_view=True)
                            if loggedin_user != v:
                                mail_id = TCoreUserDetail.objects.filter(cu_user_id=v,cu_is_deleted=False).values('cu_alt_email_id')
                                email_list.append(mail_id[0]['cu_alt_email_id'])
                                #print('email_list2',email_list)
                                if comment_save_send == 'send':
                                    mail_data = {
                                            "name": userdetails(v),
                                            "comment_sub": validated_data.get('comments'),
                                            "commented_by": userdetails(loggedin_user)
                                                }
                                    # #print('mail_data',mail_data)
                                    # mail_class = GlobleMailSend('ET-COMMENT', email_list)
                                    # mail_thread = Thread(target = mail_class.mailsend, args = (mail_data,))
                                    # mail_thread.start()
                                    send_mail_list('ET-COMMENT', email_list, mail_data, ics='')
                sub_assign_email_list=[]
                if user_cat_list[0]['sub_assign_to_user']:
                    sub_comment_view=ETaskCommentsViewers.objects.create(etcomments=e_task_comments,
                                                                user_id=user_cat_list[0]['sub_assign_to_user'],
                                                                task=validated_data.get('task'),                          
                                                                created_by=created_by,
                                                                owned_by=owned_by
                                                                )
                    # #print('sub_comment_view',sub_comment_view)
                    if loggedin_user == user_cat_list[0]['sub_assign_to_user']:
                        viewer=ETaskCommentsViewers.objects.filter(etcomments=e_task_comments,user_id=user_cat_list[0]['sub_assign_to_user'],
                                                                    task=validated_data.get('task')).update(is_view=True)

                    assign_by_mail_id = TCoreUserDetail.objects.filter(cu_user_id=users_list[0]['assign_by'],cu_is_deleted=False).values('cu_alt_email_id')
                    sub_assign_email_list.append(assign_by_mail_id[0]['cu_alt_email_id'])
                    #print('sub_assign_email_list',sub_assign_email_list)
                    if comment_save_send == 'send':
                        mail_data = {
                                "name": userdetails(users_list[0]['assign_by']),
                                "comment_sub": validated_data.get('comments'),
                                "commented_by": userdetails(user_cat_list[0]['sub_assign_to_user'])
                                    }
                        # #print('mail_data',mail_data)
                        # mail_class = GlobleMailSend('ET-COMMENT', sub_assign_email_list)
                        # mail_thread = Thread(target = mail_class.mailsend, args = (mail_data,))
                        # mail_thread.start()
                        send_mail_list('ET-COMMENT', sub_assign_email_list, mail_data, ics='')
                for c_d in cost_details:
                    cost_data=EtaskIncludeAdvanceCommentsCostDetails.objects.create(etcomments=e_task_comments,
                                                                                                  **c_d,
                                                                                                  created_by=created_by,
                                                                                                  owned_by=owned_by
                                                                                                    )
                    cost_data.__dict__.pop('_state') if "_state" in cost_data.__dict__.keys() else cost_data.__dict__
                    cost_details_list.append(cost_data.__dict__)
                # #print('cost_details_list-->',cost_details_list)

                for o_d in other_details:
                    others_data=EtaskIncludeAdvanceCommentsOtherDetails.objects.create(etcomments=e_task_comments,
                                                                                                    **o_d,
                                                                                                    created_by=created_by,
                                                                                                    owned_by=owned_by
                                                                                                    )
                    others_data.__dict__.pop('_state')if '_state' in others_data.__dict__.keys() else others_data.__dict__
                    other_details_list.append(others_data.__dict__)
                # #print('other_details_list-->',other_details_list)

                e_task_comments.__dict__['cost_details']=cost_details_list
                e_task_comments.__dict__['other_details']=other_details_list
                return e_task_comments
               
        except Exception as e:
            raise e


class ETaskCommentsSerializerV2(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    cost_details=serializers.ListField(required=False)
    other_details=serializers.ListField(required=False)
    task_ids = serializers.ListField(required=False)
    # status = serializers.BooleanField(default=False,required=False)
    
    class Meta:
        model=ETaskComments
        fields='__all__'
        extra_fields=('cost_details','other_details','task_ids')

    def create(self,validated_data):
        try:
            loggedin_user=self.context['request'].user.id
            #print('loggedin_user',loggedin_user)
            cost_details=validated_data.pop('cost_details')if 'cost_details' in validated_data else ""
            other_details=validated_data.pop('other_details')if 'other_details' in validated_data else ""
            task_ids = validated_data.pop('task_ids')if 'task_ids' in validated_data else ""
            created_by=validated_data.get('created_by')

            owned_by=validated_data.get('owned_by')
            cost_details_list=[]
            other_details_list=[]
            comment_save_send = self.context['request'].query_params.get('comment_save_send',None)
            #print('comment_save_send',comment_save_send)
            if task_ids:
                for each in task_ids:
                    validated_data['task'] = EtaskTask.objects.get(id=each)
                    e_task_comments = ETaskComments.objects.create(**validated_data)
                    # #print("e_task_comments-->",e_task_comments)
                    print(validated_data.get('task'))
                    users_list = EtaskTask.objects.filter(id=str(validated_data.get('task')), is_deleted=False).values(
                        'assign_by', 'assign_to')
                    task_obj = EtaskTask.objects.filter(id=str(validated_data.get('task')), is_deleted=False).first()
                    # #print('assign_by',users_list[0]['assign_by'])
                    user_cat_list = users_list.values('task_categories', 'sub_assign_to_user')
                    # #print('user_cat_list',user_cat_list,user_cat_list[0]['task_categories'])
                    email_list = []
                    if user_cat_list[0]['task_categories'] == 1:
                        comment_view = ETaskCommentsViewers.objects.create(etcomments=e_task_comments,
                                                                           user_id=users_list[0]['assign_by'],
                                                                           task=validated_data.get('task'),
                                                                           created_by=created_by,
                                                                           owned_by=owned_by
                                                                           )
                        # #print('comment_view',comment_view)
                        if loggedin_user == users_list[0]['assign_by']:
                            viewer = ETaskCommentsViewers.objects.filter(etcomments=e_task_comments,
                                                                         user_id=users_list[0]['assign_by'],
                                                                         task=validated_data.get('task')).update(
                                is_view=True)

                        assign_by_mail_id = TCoreUserDetail.objects.filter(cu_user_id=users_list[0]['assign_by'],
                                                                           cu_is_deleted=False).values(
                            'cu_alt_email_id')
                        email_list.append(assign_by_mail_id[0]['cu_alt_email_id'])
                        # print('email_list1',email_list)
                        if loggedin_user != users_list[0]['assign_by'] and comment_save_send == 'send':
                            mail_data = {
                                "recipient_name": userdetails(users_list[0]['assign_by']),
                                "comment_sub": validated_data.get('comments'),
                                "commented_by": userdetails(users_list[0]['assign_by']),
                                "task_subject": task_obj.task_subject,
                                "assign_to_name": task_obj.assign_to.get_full_name(),
                                "start_date": task_obj.start_date.date(),
                                "end_date": task_obj.extended_date.date() if task_obj.extended_date else task_obj.end_date.date()
                            }
                            # #print('mail_data',mail_data)
                            # mail_class = GlobleMailSend('ET-COMMENT', email_list)
                            # mail_thread = Thread(target=mail_class.mailsend, args=(mail_data,))
                            # mail_thread.start()
                            send_mail_list('ET-COMMENT', email_list, mail_data, ics='')
                    else:
                        for user in users_list:
                            # print('user',user)
                            for k, v in user.items():
                                # print('v',v,type(v))
                                comment_view = ETaskCommentsViewers.objects.create(etcomments=e_task_comments,
                                                                                   user_id=v,
                                                                                   task=validated_data.get('task'),
                                                                                   created_by=created_by,
                                                                                   owned_by=owned_by
                                                                                   )
                                # #print('comment_view',comment_view)
                                if loggedin_user == v:
                                    viewer = ETaskCommentsViewers.objects.filter(etcomments=e_task_comments, user_id=v,
                                                                                 task=validated_data.get(
                                                                                     'task')).update(is_view=True)
                                if loggedin_user != v:
                                    mail_id = TCoreUserDetail.objects.filter(cu_user_id=v, cu_is_deleted=False).values(
                                        'cu_alt_email_id')
                                    email_list.append(mail_id[0]['cu_alt_email_id'])
                                    # print('email_list2',email_list)
                                    if comment_save_send == 'send':
                                        mail_data = {
                                            "recipient_name": userdetails(v),
                                            "comment_sub": validated_data.get('comments'),
                                            "commented_by": userdetails(loggedin_user),
                                            "task_subject": task_obj.task_subject,
                                            "assign_to_name": task_obj.assign_to.get_full_name(),
                                            "start_date": task_obj.start_date.date(),
                                            "end_date": task_obj.extended_date.date() if task_obj.extended_date else task_obj.end_date.date()
                                        }
                                        # #print('mail_data',mail_data)
                                        # mail_class = GlobleMailSend('ET-COMMENT', email_list)
                                        # mail_thread = Thread(target=mail_class.mailsend, args=(mail_data,))
                                        # mail_thread.start()
                                        send_mail_list('ET-COMMENT', email_list, mail_data, ics='')
                    sub_assign_email_list = []
                    if user_cat_list[0]['sub_assign_to_user']:
                        sub_comment_view = ETaskCommentsViewers.objects.create(etcomments=e_task_comments,
                                                                               user_id=user_cat_list[0][
                                                                                   'sub_assign_to_user'],
                                                                               task=validated_data.get('task'),
                                                                               created_by=created_by,
                                                                               owned_by=owned_by
                                                                               )
                        # #print('sub_comment_view',sub_comment_view)
                        if loggedin_user == user_cat_list[0]['sub_assign_to_user']:
                            viewer = ETaskCommentsViewers.objects.filter(etcomments=e_task_comments,
                                                                         user_id=user_cat_list[0]['sub_assign_to_user'],
                                                                         task=validated_data.get('task')).update(
                                is_view=True)

                        assign_by_mail_id = TCoreUserDetail.objects.filter(cu_user_id=users_list[0]['assign_by'],
                                                                           cu_is_deleted=False).values(
                            'cu_alt_email_id')
                        sub_assign_email_list.append(assign_by_mail_id[0]['cu_alt_email_id'])
                        # print('sub_assign_email_list',sub_assign_email_list)
                        if loggedin_user != users_list[0]['assign_by'] and comment_save_send == 'send':
                            mail_data = {
                                "recipient_name": userdetails(users_list[0]['assign_by']),
                                "comment_sub": validated_data.get('comments'),
                                "commented_by": userdetails(user_cat_list[0]['sub_assign_to_user']),
                                "task_subject": task_obj.task_subject,
                                "assign_to_name": task_obj.assign_to.get_full_name(),
                                "start_date": task_obj.start_date.date(),
                                "end_date": task_obj.extended_date.date() if task_obj.extended_date else task_obj.end_date.date()
                            }
                            # #print('mail_data',mail_data)
                            # mail_class = GlobleMailSend('ET-COMMENT', sub_assign_email_list)
                            # mail_thread = Thread(target=mail_class.mailsend, args=(mail_data,))
                            # mail_thread.start()
                            send_mail_list('ET-COMMENT', sub_assign_email_list, mail_data, ics='')
                    for c_d in cost_details:
                        cost_data = EtaskIncludeAdvanceCommentsCostDetails.objects.create(etcomments=e_task_comments,
                                                                                          **c_d,
                                                                                          created_by=created_by,
                                                                                          owned_by=owned_by
                                                                                          )
                        cost_data.__dict__.pop(
                            '_state') if "_state" in cost_data.__dict__.keys() else cost_data.__dict__
                        cost_details_list.append(cost_data.__dict__)
                    # #print('cost_details_list-->',cost_details_list)

                    for o_d in other_details:
                        others_data = EtaskIncludeAdvanceCommentsOtherDetails.objects.create(etcomments=e_task_comments,
                                                                                             **o_d,
                                                                                             created_by=created_by,
                                                                                             owned_by=owned_by
                                                                                             )
                        others_data.__dict__.pop(
                            '_state') if '_state' in others_data.__dict__.keys() else others_data.__dict__
                        other_details_list.append(others_data.__dict__)
                    # #print('other_details_list-->',other_details_list)

                    e_task_comments.__dict__['cost_details'] = cost_details_list
                    e_task_comments.__dict__['other_details'] = other_details_list

                    e_task = EtaskTask.objects.filter(id=str(validated_data.get('task')), is_deleted=False).first()

                    users_set = {e_task.assign_to, e_task.assign_by, e_task.sub_assign_to_user}
                    users_set.discard(created_by)
                    users_set.discard(None)
                    users = list(users_set)

                    title = '{} commented on the task with task code {}.'.format(created_by.get_full_name(),
                                                                                 e_task.task_code_id)
                    body = 'Task: {} \nDetails:{} \nComment:{}'.format(e_task.task_subject, e_task.task_description,
                                                                       e_task_comments.comments)

                    data = {
                        "app_module": "etask",
                        "type": "task",
                        "id": e_task.id
                    }
                    data_str = json.dumps(data)

                    notification_id = store_sent_notification(users=users, body=body, title=title, data=data_str,
                                                              app_module_name='etask')
                    send_notification(users=users, body=body, title=title, data=data, notification_id=notification_id)

                    return e_task_comments

            else:
                with transaction.atomic():
                    e_task_comments = ETaskComments.objects.create(**validated_data)
                    # #print("e_task_comments-->",e_task_comments)
                    users_list = EtaskTask.objects.filter(id=str(validated_data.get('task')), is_deleted=False).values(
                        'assign_by', 'assign_to')
                    task_obj = EtaskTask.objects.filter(id=str(validated_data.get('task')), is_deleted=False).first()
                    # #print('assign_by',users_list[0]['assign_by'])
                    user_cat_list = users_list.values('task_categories', 'sub_assign_to_user')
                    # #print('user_cat_list',user_cat_list,user_cat_list[0]['task_categories'])
                    email_list = []
                    if user_cat_list[0]['task_categories'] == 1:
                        comment_view = ETaskCommentsViewers.objects.create(etcomments=e_task_comments,
                                                                           user_id=users_list[0]['assign_by'],
                                                                           task=validated_data.get('task'),
                                                                           created_by=created_by,
                                                                           owned_by=owned_by
                                                                           )
                        # #print('comment_view',comment_view)
                        if loggedin_user == users_list[0]['assign_by']:
                            viewer = ETaskCommentsViewers.objects.filter(etcomments=e_task_comments,
                                                                         user_id=users_list[0]['assign_by'],
                                                                         task=validated_data.get('task')).update(
                                is_view=True)

                        assign_by_mail_id = TCoreUserDetail.objects.filter(cu_user_id=users_list[0]['assign_by'],
                                                                           cu_is_deleted=False).values(
                            'cu_alt_email_id')
                        email_list.append(assign_by_mail_id[0]['cu_alt_email_id'])
                        # print('email_list1',email_list)
                        if loggedin_user != users_list[0]['assign_by'] and comment_save_send == 'send':
                            mail_data = {
                                "recipient_name": userdetails(users_list[0]['assign_by']),
                                "comment_sub": validated_data.get('comments'),
                                "commented_by": userdetails(users_list[0]['assign_by']),
                                "task_subject": task_obj.task_subject,
                                "assign_to_name": task_obj.assign_to.get_full_name(),
                                "start_date": task_obj.start_date.date(),
                                "end_date": task_obj.extended_date.date() if task_obj.extended_date else task_obj.end_date.date()
                            }
                            # #print('mail_data',mail_data)
                            # mail_class = GlobleMailSend('ET-COMMENT', email_list)
                            # mail_thread = Thread(target=mail_class.mailsend, args=(mail_data,))
                            # mail_thread.start()
                            send_mail_list('ET-COMMENT', email_list, mail_data, ics='')
                    else:
                        for user in users_list:
                            # print('user',user)
                            for k, v in user.items():
                                # print('v',v,type(v))
                                comment_view = ETaskCommentsViewers.objects.create(etcomments=e_task_comments,
                                                                                   user_id=v,
                                                                                   task=validated_data.get('task'),
                                                                                   created_by=created_by,
                                                                                   owned_by=owned_by
                                                                                   )
                                # #print('comment_view',comment_view)
                                if loggedin_user == v:
                                    viewer = ETaskCommentsViewers.objects.filter(etcomments=e_task_comments, user_id=v,
                                                                                 task=validated_data.get(
                                                                                     'task')).update(is_view=True)
                                if loggedin_user != v:
                                    mail_id = TCoreUserDetail.objects.filter(cu_user_id=v, cu_is_deleted=False).values(
                                        'cu_alt_email_id')
                                    email_list.append(mail_id[0]['cu_alt_email_id'])
                                    # print('email_list2',email_list)
                                    if comment_save_send == 'send':
                                        mail_data = {
                                            "recipient_name": userdetails(v),
                                            "comment_sub": validated_data.get('comments'),
                                            "commented_by": userdetails(loggedin_user),
                                            "task_subject": task_obj.task_subject,
                                            "assign_to_name": task_obj.assign_to.get_full_name(),
                                            "start_date": task_obj.start_date.date(),
                                            "end_date": task_obj.extended_date.date() if task_obj.extended_date else task_obj.end_date.date()
                                        }
                                        # #print('mail_data',mail_data)
                                        # mail_class = GlobleMailSend('ET-COMMENT', email_list)
                                        # mail_thread = Thread(target=mail_class.mailsend, args=(mail_data,))
                                        # mail_thread.start()
                                        send_mail_list('ET-COMMENT', email_list, mail_data, ics='')
                    sub_assign_email_list = []
                    if user_cat_list[0]['sub_assign_to_user']:
                        sub_comment_view = ETaskCommentsViewers.objects.create(etcomments=e_task_comments,
                                                                               user_id=user_cat_list[0][
                                                                                   'sub_assign_to_user'],
                                                                               task=validated_data.get('task'),
                                                                               created_by=created_by,
                                                                               owned_by=owned_by
                                                                               )
                        # #print('sub_comment_view',sub_comment_view)
                        if loggedin_user == user_cat_list[0]['sub_assign_to_user']:
                            viewer = ETaskCommentsViewers.objects.filter(etcomments=e_task_comments,
                                                                         user_id=user_cat_list[0]['sub_assign_to_user'],
                                                                         task=validated_data.get('task')).update(
                                is_view=True)

                        assign_by_mail_id = TCoreUserDetail.objects.filter(cu_user_id=users_list[0]['assign_by'],
                                                                           cu_is_deleted=False).values(
                            'cu_alt_email_id')
                        sub_assign_email_list.append(assign_by_mail_id[0]['cu_alt_email_id'])
                        # print('sub_assign_email_list',sub_assign_email_list)
                        if loggedin_user != users_list[0]['assign_by'] and comment_save_send == 'send':
                            mail_data = {
                                "recipient_name": userdetails(users_list[0]['assign_by']),
                                "comment_sub": validated_data.get('comments'),
                                "commented_by": userdetails(user_cat_list[0]['sub_assign_to_user']),
                                "task_subject": task_obj.task_subject,
                                "assign_to_name": task_obj.assign_to.get_full_name(),
                                "start_date": task_obj.start_date.date(),
                                "end_date": task_obj.extended_date.date() if task_obj.extended_date else task_obj.end_date.date()
                            }
                            # #print('mail_data',mail_data)
                            # mail_class = GlobleMailSend('ET-COMMENT', sub_assign_email_list)
                            # mail_thread = Thread(target=mail_class.mailsend, args=(mail_data,))
                            # mail_thread.start()
                            send_mail_list('ET-COMMENT', sub_assign_email_list, mail_data, ics='')
                    for c_d in cost_details:
                        cost_data = EtaskIncludeAdvanceCommentsCostDetails.objects.create(etcomments=e_task_comments,
                                                                                          **c_d,
                                                                                          created_by=created_by,
                                                                                          owned_by=owned_by
                                                                                          )
                        cost_data.__dict__.pop(
                            '_state') if "_state" in cost_data.__dict__.keys() else cost_data.__dict__
                        cost_details_list.append(cost_data.__dict__)
                    # #print('cost_details_list-->',cost_details_list)

                    for o_d in other_details:
                        others_data = EtaskIncludeAdvanceCommentsOtherDetails.objects.create(etcomments=e_task_comments,
                                                                                             **o_d,
                                                                                             created_by=created_by,
                                                                                             owned_by=owned_by
                                                                                             )
                        others_data.__dict__.pop(
                            '_state') if '_state' in others_data.__dict__.keys() else others_data.__dict__
                        other_details_list.append(others_data.__dict__)
                    # #print('other_details_list-->',other_details_list)

                    e_task_comments.__dict__['cost_details'] = cost_details_list
                    e_task_comments.__dict__['other_details'] = other_details_list

                    e_task = EtaskTask.objects.filter(id=str(validated_data.get('task')), is_deleted=False).first()

                    users_set = {e_task.assign_to, e_task.assign_by, e_task.sub_assign_to_user}
                    users_set.discard(created_by)
                    users_set.discard(None)
                    users = list(users_set)

                    title = '{} commented on the task with task code {}.'.format(created_by.get_full_name(),
                                                                                 e_task.task_code_id)
                    body = 'Task: {} \nDetails:{} \nComment:{}'.format(e_task.task_subject, e_task.task_description,
                                                                       e_task_comments.comments)

                    data = {
                        "app_module": "etask",
                        "type": "task",
                        "id": e_task.id
                    }
                    data_str = json.dumps(data)

                    notification_id = store_sent_notification(users=users, body=body, title=title, data=data_str,
                                                              app_module_name='etask')
                    send_notification(users=users, body=body, title=title, data=data, notification_id=notification_id)

                    return e_task_comments

        except Exception as e:
            raise e



class ETaskCommentsViewersSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model=ETaskCommentsViewers
        fields='__all__'
    def create(self,validated_data):
        comment_id=self.context['request'].query_params.get('comment_id')
        #print('task_id',comment_id,type(comment_id))
        user_id=self.context['request'].query_params.get('user_id')
        #print('user_id',user_id)
        comment_viewers=ETaskCommentsViewers.objects.filter(etcomments=comment_id,user=user_id,is_deleted=False).update(is_view=True)
        #print('comment_viewers',comment_viewers,type(comment_viewers))
        return comment_viewers


class ETaskMassCommentsViewersSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    comment_ids = serializers.ListField(required=False)
    class Meta:
        model=ETaskCommentsViewers
        fields='__all__'
        extra_fields = ('comment_ids',)
    def create(self,validated_data):
        comment_ids=validated_data.get('comment_ids',[])
        user=self.context['request'].user
        comment_viewers=ETaskCommentsViewers.objects.filter(etcomments__in=comment_ids,user=user,is_deleted=False).update(is_view=True)
        return comment_viewers


class ETaskUnreadCommentsSerializer(serializers.ModelSerializer):
    task_status_name=serializers.CharField(source='get_task_status_display')
    class Meta:
        model=EtaskTask
        fields='__all__'


class ETaskUnreadCommentsSerializerV2(serializers.ModelSerializer):
    task_status_name=serializers.CharField(source='get_task_status_display')
    parent_task = serializers.SerializerMethodField()
    sub_tasks = serializers.SerializerMethodField()

    class Meta:
        model=EtaskTask
        fields='__all__'
        extra_fields = ('parent_task','sub_tasks')

    def get_sub_tasks(self, obj):
        sub_tasks_data = EtaskTask.objects.filter(~Q(task_status=4),parent_id=obj.id,is_deleted=False).values('id','task_subject')
        return sub_tasks_data if sub_tasks_data else list() 

    def get_parent_task(self,obj):
        if  obj.parent_id:
            parent_task = EtaskTask.objects.filter(id=obj.parent_id)
            if parent_task.count():
                parent_data=parent_task.values('id','task_subject')[0]
                return parent_data
        

class ETaskUnreadCommentsDownloadSerializerV2(serializers.ModelSerializer):
    task_subject = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    commented_by = serializers.SerializerMethodField()
    assign_by = serializers.SerializerMethodField()
    task_status = serializers.SerializerMethodField()

    class Meta:
        model=ETaskCommentsViewers
        fields='__all__'
        extra_fields=('task_subject','comments','commented_by','assign_by','task_status')

    def get_task_status(self, obj):
        return obj.task.get_task_status_display() if obj.task else ''

    def get_assign_by(self, obj):
        return obj.task.assign_by.get_full_name() if obj.task else ''

    def get_commented_by(self, obj):
        return obj.etcomments.created_by.get_full_name() if obj.etcomments else ''

    def get_comments(self, obj):
        return obj.etcomments.comments if obj.etcomments else ''

    def get_task_subject(self, obj):
        return obj.task.task_subject if obj.task else ''


class ETaskCommentsAdvanceAttachmentAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model=EtaskIncludeAdvanceCommentsDocuments
        fields='__all__'

class EtasCommentsListSerializer(serializers.ModelSerializer):
    
    class Meta:
        model=ETaskComments
        fields='__all__'

#::::::::::::::::::::::::: TASK COMMENTS:::::::::::::::::::::::::::#
class ETaskFollowupCommentsSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    cost_details=serializers.ListField(required=False)
    other_details=serializers.ListField(required=False)
    
    class Meta:
        model=FollowupComments
        fields='__all__'
        extra_fields=('cost_details','other_details')

    def create(self,validated_data):
        try:
            cost_details=validated_data.pop('cost_details')if 'cost_details' in validated_data else ""
            other_details=validated_data.pop('other_details')if 'other_details' in validated_data else "" 
            created_by=validated_data.get('created_by')
            owned_by=validated_data.get('owned_by')
            cost_details_list=[]
            other_details_list=[]
            
            with transaction.atomic():
                followup_comments=FollowupComments.objects.create(**validated_data)

                # #print("followup_comments-->",followup_comments)
                
                for c_d in cost_details:
                    cost_data=FollowupIncludeAdvanceCommentsCostDetails.objects.create(flcomments=followup_comments,
                                                                                                  **c_d,
                                                                                                  created_by=created_by,
                                                                                                  owned_by=owned_by
                                                                                                    )
                    cost_data.__dict__.pop('_state') if "_state" in cost_data.__dict__.keys() else cost_data.__dict__
                    cost_details_list.append(cost_data.__dict__)
                # #print('cost_details_list-->',cost_details_list)

                for o_d in other_details:
                    others_data=FollowupIncludeAdvanceCommentsOtherDetails.objects.create(flcomments=followup_comments,
                                                                                                    **o_d,
                                                                                                    created_by=created_by,
                                                                                                    owned_by=owned_by
                                                                                                    )
                    others_data.__dict__.pop('_state')if '_state' in others_data.__dict__.keys() else others_data.__dict__
                    other_details_list.append(others_data.__dict__)
                # #print('other_details_list-->',other_details_list)

                followup_comments.__dict__['cost_details']=cost_details_list
                followup_comments.__dict__['other_details']=other_details_list
                return followup_comments
               
        except Exception as e:
            raise e

class ETaskFollowupCommentsAdvanceAttachmentAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model=FollowupIncludeAdvanceCommentsDocuments
        fields='__all__'

class EtasCommentsListSerializer(serializers.ModelSerializer):
    
    class Meta:
        model=ETaskComments
        fields='__all__'



class ETaskSubAssignSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    # sub_assign=serializers.ListField(required=False)
    class Meta:
        model=EtaskTask
        fields=('id','sub_assign_to_user','updated_by')
    def update(self, instance, validated_data):
        cur_date = datetime.now().date()
        try:
            # sub_assign=validated_data.pop('sub_assign') if 'sub_assign'in validated_data else ""
            
            updated_by=validated_data.get('updated_by')
            with transaction.atomic():
                #======================= log ====================================#
                if instance.sub_assign_to_user:
                    assign_from = instance.sub_assign_to_user
                else:
                    assign_from = instance.assign_to
                sub_assign_log = EtaskTaskSubAssignLog.objects.create(task_id=instance.id,assign_from=assign_from,
                                                                    sub_assign=validated_data['sub_assign_to_user'],
                                                                    created_by=updated_by,owned_by=updated_by)
                ###################################################################
                instance.sub_assign_to_user= validated_data['sub_assign_to_user']
                instance.updated_by=updated_by
                instance.save()
                ####################################################################
                reporting_date = ETaskReportingDates.objects.filter(task=instance.id,task_type=1,reporting_status=2,
                                        reporting_date__date__gt=cur_date).values('reporting_date')
                #print("reporting_date",reporting_date)
                reporting_date_list = []
                # #print("task_create",task_create.__dict__['id'])
                # #print("r_date['reporting_date']",r_date['reporting_date'])
                reporting_date_str = """"""
                r_time = ''
                ics_data = """BEGIN:VCALENDAR
VERSION:2.0
CALSCALE:GREGORIAN\n"""
                #print("validated_data['sub_assign_to_user']",instance.sub_assign_to_user)
                user_name = userdetails(instance.sub_assign_to_user.id)
                count_id = 0
                for r_date in reporting_date:
                    #print("r_date['reporting_date']",r_date['reporting_date'])
                    count_id += 1
                    reporting_date_str += str(count_id)+'. '+r_date['reporting_date'].strftime("%m/%d/%Y, %I:%M:%S %p")+" "
                    r_time = r_date['reporting_date'].strftime("%Y%m%dT%H%M%S")
                    ics_data +=   """BEGIN:VEVENT
SUMMARY:Reporting of {rep_sub}
DTSTART;TZID=Asia/Kolkata:{r_time}
LOCATION:Shyam Tower,Kolkata-700091
DESCRIPTION: Reporting dates.
STATUS:CONFIRMED
SEQUENCE:3
BEGIN:VALARM
TRIGGER:-PT10M
DESCRIPTION:Pickup Reminder
ACTION:DISPLAY
END:VALARM
END:VEVENT\n""".replace("{r_time}",r_time).replace("{rep_sub}",instance.task_subject)

                #DTEND;TZID=Asia/Kolkata:{r_time}
                ics_data += "END:VCALENDAR"
                #print("reporting_date_str",reporting_date_str)
                user_email = User.objects.get(id= instance.sub_assign_to_user.id).cu_user.cu_alt_email_id
                #print("user_email",user_email)
                
                if user_email:
                    mail_data = {
                                "recipient_name" : user_name,        ## modified by manas Paul 21jan20
                                "task_subject": instance.task_subject,
                                "reporting_date": reporting_date_str,
                            }
                    # #print('mail_data',mail_data)
                    # #print('mail_id-->',mail)
                    # #print('mail_id-->',[mail])
                    # mail_class = GlobleMailSend('ETAP', email_list)
                    # mail_class = GlobleMailSend('ETRDC', [user_email])
                    # #print('mail_class',mail_class)
                    # mail_thread = Thread(target = mail_class.mailsend, args = (mail_data,ics_data))
                    # #print('mail_thread-->',mail_thread)
                    # mail_thread.start()
                    send_mail_list('ETRDC', [user_email], mail_data, ics=ics_data)
                ######################################  

                return instance     
        except Exception as e:
            raise e


class ETaskSubAssignSerializerV2(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    user_cc = serializers.ListField(required=False)
    reporting_date = serializers.ListField(required=False)

    class Meta:
        model=EtaskTask
        fields=('id','sub_assign_to_user','updated_by','user_cc','created_by','owned_by','reporting_date')

    def update(self, instance, validated_data):
        cur_date = datetime.now().date()
        try:
            # sub_assign=validated_data.pop('sub_assign') if 'sub_assign'in validated_data else ""
            
            updated_by=validated_data.get('updated_by')
            created_by = validated_data.get('created_by')
            owned_by = validated_data.get('owned_by')
            user_cc = validated_data.pop('user_cc') if 'user_cc' in validated_data else ""
            reporting_dates = validated_data.get('reporting_date',list())

            with transaction.atomic():
                #======================= log ====================================#
                etask_log_sub_assign = EtaskTaskSubAssignLog.objects.filter(task=instance,is_deleted=False)
                if etask_log_sub_assign.count()>=2:
                    raise APIException({'request_status': 0, 'msg': 'The task can not be sub-assigned further','result':etask_log_sub_assign.values()})
                if instance.sub_assign_to_user:
                    assign_from = instance.sub_assign_to_user
                else:
                    assign_from = instance.assign_to
                sub_assign_log = EtaskTaskSubAssignLog.objects.create(task_id=instance.id,assign_from=assign_from,
                                                                    sub_assign=validated_data['sub_assign_to_user'],
                                                                    created_by=updated_by,owned_by=updated_by)
                ###################################################################
                instance.sub_assign_to_user= validated_data['sub_assign_to_user']
                instance.updated_by=updated_by
                instance.save()
                ####################################################################
                reporting_date_obj = list()
                for r_date in reporting_dates:
                    rdate_details,created = ETaskReportingDates.objects.get_or_create(
                        task_type=1,
                        task = instance.id,
                        is_manual_time_entry = r_date['is_manual_time_entry'],
                        reporting_date = datetime.strptime(r_date['reporting_date'], "%Y-%m-%dT%H:%M:%S.%fZ"),
                        reporting_end_date = datetime.strptime(r_date['reporting_end_date'], "%Y-%m-%dT%H:%M:%S.%fZ"),
                        created_by=created_by,
                        owned_by=owned_by
                    )
                    if created:
                        reporting_date_obj.append(rdate_details)

                # create appointment and mail notification
                create_appointment(reporting_dates=reporting_date_obj)

                for u_cc in user_cc:
                    ucc_details, is_created = EtaskUserCC.objects.get_or_create(task=instance,
                                                ** u_cc, created_by=created_by , owned_by = owned_by
                                            )

                user_cc_list = EtaskUserCC.objects.filter(task=instance,is_deleted=False)
                reporting_date = ETaskReportingDates.objects.filter(task=instance.id,task_type=1,reporting_status=2,
                                        reporting_date__date__gt=cur_date,is_deleted=False).values('reporting_date')

                mail_reporting_date_list = [r_date['reporting_date'].strftime("%d/%m/%Y, %I:%M:%S %p") for r_date in reporting_date]
                cc_name_list = [u_cc.user.get_full_name() for u_cc in user_cc_list] if user_cc_list.count() else []
                
                #print("reporting_date",reporting_date)
                reporting_date_list = []
                # #print("task_create",task_create.__dict__['id'])
                # #print("r_date['reporting_date']",r_date['reporting_date'])
                reporting_date_str = """"""
                r_time = ''
                ics_data = """BEGIN:VCALENDAR
VERSION:2.0
CALSCALE:GREGORIAN\n"""
                #print("validated_data['sub_assign_to_user']",instance.sub_assign_to_user)
                user_name = userdetails(instance.sub_assign_to_user.id)
                count_id = 0
                for r_date in reporting_date:
                    #print("r_date['reporting_date']",r_date['reporting_date'])
                    count_id += 1
                    reporting_date_str += str(count_id)+'. '+r_date['reporting_date'].strftime("%m/%d/%Y, %I:%M:%S %p")+" "
                    r_time = r_date['reporting_date'].strftime("%Y%m%dT%H%M%S")
                    ics_data +=   """BEGIN:VEVENT
SUMMARY:Reporting of {rep_sub}
DTSTART;TZID=Asia/Kolkata:{r_time}
LOCATION:Shyam Tower,Kolkata-700091
DESCRIPTION: Reporting dates.
STATUS:CONFIRMED
SEQUENCE:3
BEGIN:VALARM
TRIGGER:-PT10M
DESCRIPTION:Pickup Reminder
ACTION:DISPLAY
END:VALARM
END:VEVENT\n""".replace("{r_time}",r_time).replace("{rep_sub}",instance.task_subject)

                #DTEND;TZID=Asia/Kolkata:{r_time}
                ics_data += "END:VCALENDAR"
                #print("reporting_date_str",reporting_date_str)
                user_email = User.objects.get(id= instance.sub_assign_to_user.id).cu_user.cu_alt_email_id
                #print("user_email",user_email)
                
                if user_email:
                    mail_data = {
                                "recipient_name" : user_name,        ## modified by manas Paul 21jan20
                                "task_subject": instance.task_subject,
                                "reporting_date": mail_reporting_date_list,
                                "assign_to_name": instance.assign_to.get_full_name(),
                                "created_by_name": instance.created_by.get_full_name(),
                                "created_date_time": instance.created_at,
                                "cc_to":','.join(cc_name_list),
                                "task_priority": instance.get_task_priority_display(),
                                "start_date": instance.start_date.date(),
                                "end_date": instance.extended_date.date() if instance.extended_date else instance.end_date.date()
                            }
                    # #print('mail_data',mail_data)
                    # #print('mail_id-->',mail)
                    # #print('mail_id-->',[mail])
                    # mail_class = GlobleMailSend('ETAP', email_list)
                    # mail_class = GlobleMailSend('ETRDC', [user_email])
                    # #print('mail_class',mail_class)
                    # mail_thread = Thread(target = mail_class.mailsend, args = (mail_data,ics_data))
                    # #print('mail_thread-->',mail_thread)
                    # mail_thread.start()
                    send_mail_list('ETRDC', [user_email], mail_data, ics=ics_data)
                ######################################  

                return instance     
        except Exception as e:
            raise e


class EtaskAddFollowUpSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    assign_to = serializers.CharField(default=serializers.CurrentUserDefault())
    # reporting_dates = serializers.ListField(required=False)
    class Meta:
        model=EtaskFollowUP
        fields='__all__'
        # extra_fields = 'reporting_dates'

    def create(self,validated_data):
        try:
            created_by = validated_data.get('created_by')
            # #print('created_by',created_by,type(created_by))
            owned_by = validated_data.get('owned_by')
           
            with transaction.atomic():
                # reporting_dates = validated_data.pop('reporting_dates') if 'reporting_dates' in validated_data else ''

                create_followup = EtaskFollowUP.objects.create(**validated_data)

                #print('create_followup-->',create_followup.__dict__)
                
                # reporting_dates = validated_data['reporting_dates'] 
                # #print('reporting_dates from user-->',reporting_dates)

                # report_date_list = []

                # for r_dates in reporting_dates:
                #     etask_report_date,create = ETaskReportingDates.objects.get_or_create(
                #         task_type = 2,
                #         task = str(create_followup),
                #         reporting_date = datetime.strptime(r_dates['r_dates'],"%Y-%m-%dT%H:%M:%S.%fZ"),
                #         created_by=created_by,
                #         owned_by=owned_by
                #     )
                #     report_date_list.append(etask_report_date.__dict__)
                #     etask_report_date.__dict__.pop('_state') if '_state' in etask_report_date.__dict__.keys() else etask_report_date.__dict__
                #     #print('etask_report_date-->',etask_report_date.__dict__)
                # validated_data['reporting_dates'] = report_date_list
                return create_followup
        except Exception as e:
            raise e


class EtaskAddFollowUpSerializerV2(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    assign_to = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model=EtaskFollowUP
        fields='__all__'

    def create(self,validated_data):
        try:
            created_by = validated_data.get('created_by')
            owned_by = validated_data.get('owned_by')
           
            with transaction.atomic():
                create_followup = EtaskFollowUP.objects.create(**validated_data)
                
                # users = [create_followup.assign_for]
                # title = 'Please follow up with {} on {}.'.format(create_followup.assign_to.get_full_name(),create_followup.follow_up_date.date())
                # body ='Follow Up: {} \nTask: {} \nDetails:{}'.format(create_followup.follow_up_task,create_followup.task.task_subject,create_followup.task.task_description)

                # data = {
                #             "app_module":"etask",
                #             "type":"follow_up",
                #             "id":create_followup.id
                #         }
                # data_str = json.dumps(data)
                # notification_id = store_sent_notification(users=users,body=body,title=title,data=data_str,app_module_name='etask')
                # send_notification(users=users,body=body,title=title,data=data,notification_id=notification_id)
                
                return create_followup
        except Exception as e:
            raise e



class EtaskFollowUpListSerializer(serializers.ModelSerializer):
    
    class Meta:
        model=EtaskFollowUP
        fields='__all__'
    

class EtaskFollowUpListSerializerV2(serializers.ModelSerializer):
    task_flag = serializers.SerializerMethodField()
    overdue_by = serializers.SerializerMethodField()

    class Meta:
        model=EtaskFollowUP
        fields='__all__'
        extra_fields = ('task_flag', 'overdue_by')

    def get_overdue_by(self, obj):
        cur_date=datetime.now().date()
        overdue_by = None
        if obj.follow_up_date and obj.follow_up_date.date() <= cur_date:
            follow_up_date = obj.follow_up_date.date()
            days_followup=(cur_date - follow_up_date).days
            #print("days_followup",days_followup,type(days_followup))
            if days_followup==1:
                overdue_by = str(days_followup)+" day"
            elif days_followup >1:
                overdue_by = str(days_followup)+" days"
            else:
                overdue_by = None
        
        return overdue_by

    def get_task_flag(self, obj):
        TASK_TYPES = ('overdue', 'ongoing', 'upcomming')
        cur_date=datetime.now().date()
        task_flag = None
        
        if obj.follow_up_date.date() < cur_date:
            task_flag = TASK_TYPES[0]
        elif obj.follow_up_date.date() == cur_date:
            task_flag = TASK_TYPES[1]
        elif obj.follow_up_date.date() > cur_date:
            task_flag = TASK_TYPES[2]
        return task_flag



class EtaskFollowUpDetailsSerializer(serializers.ModelSerializer):
    task_flag = serializers.SerializerMethodField()
    overdue_by = serializers.SerializerMethodField()
    assign_for_name = serializers.SerializerMethodField()
    assign_to_name = serializers.SerializerMethodField()

    class Meta:
        model=EtaskFollowUP
        fields='__all__'
        extra_fields = ('task_flag', 'overdue_by','assign_for_name','assign_to_name')

    def get_assign_to_name(self, obj):
        return obj.assign_to.get_full_name() if obj.assign_to else ''

    def get_assign_for_name(self, obj):
        return obj.assign_for.get_full_name() if obj.assign_for else ''

    def get_overdue_by(self, obj):
        cur_date=datetime.now().date()
        overdue_by = None
        if obj.follow_up_date and obj.follow_up_date.date() <= cur_date:
            follow_up_date = obj.follow_up_date.date()
            days_followup=(cur_date - follow_up_date).days
            #print("days_followup",days_followup,type(days_followup))
            if days_followup==1:
                overdue_by = str(days_followup)+" day"
            elif days_followup >1:
                overdue_by = str(days_followup)+" days"
            else:
                overdue_by = None
        
        return overdue_by

    def get_task_flag(self, obj):
        TASK_TYPES = ('overdue', 'ongoing', 'upcomming')
        cur_date=datetime.now().date()
        task_flag = None
        
        if obj.follow_up_date.date() < cur_date:
            task_flag = TASK_TYPES[0]
        elif obj.follow_up_date.date() == cur_date:
            task_flag = TASK_TYPES[1]
        elif obj.follow_up_date.date() > cur_date:
            task_flag = TASK_TYPES[2]
        return task_flag


class EtaskFollowUpListDownloadSerializerV2(serializers.ModelSerializer):
    task_flag = serializers.SerializerMethodField()
    overdue_by = serializers.SerializerMethodField()
    follow_up_date_format = serializers.SerializerMethodField()

    class Meta:
        model=EtaskFollowUP
        fields='__all__'
        extra_fields = ('task_flag', 'overdue_by','follow_up_date_format')

    def get_follow_up_date_format(self, obj):
        return obj.follow_up_date.strftime("%d %b %Y %I:%M %p") if obj.follow_up_date else ''

    def get_overdue_by(self, obj):
        cur_date=datetime.now().date()
        overdue_by = None
        if obj.follow_up_date and obj.follow_up_date.date() <= cur_date:
            follow_up_date = obj.follow_up_date.date()
            days_followup=(cur_date - follow_up_date).days
            #print("days_followup",days_followup,type(days_followup))
            if days_followup==1:
                overdue_by = str(days_followup)+" day"
            elif days_followup >1:
                overdue_by = str(days_followup)+" days"
            else:
                overdue_by = None
        
        return overdue_by

    def get_task_flag(self, obj):
        TASK_TYPES = ('overdue', 'ongoing', 'upcomming')
        cur_date=datetime.now().date()
        task_flag = None
        
        if obj.follow_up_date.date() < cur_date:
            task_flag = TASK_TYPES[0]
        elif obj.follow_up_date.date() == cur_date:
            task_flag = TASK_TYPES[1]
        elif obj.follow_up_date.date() > cur_date:
            task_flag = TASK_TYPES[2]
        return task_flag


class EtaskUpcomingFollowUpListSerializerV2(serializers.ModelSerializer):
    
    class Meta:
        model=EtaskFollowUP
        fields='__all__'


class EtaskUpcomingFollowUpListDownloadSerializerV2(serializers.ModelSerializer):
    follow_up_date_format = serializers.SerializerMethodField()
    
    class Meta:
        model=EtaskFollowUP
        fields='__all__'
        extra_fields = ('follow_up_date_format')

    def get_follow_up_date_format(self, obj):
        return obj.follow_up_date.strftime("%d %b %Y %I:%M %p") if obj.follow_up_date else ''


class EtaskFollowUpCompleteViewSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = EtaskFollowUP
        fields = '__all__'
    def update(self, instance, validated_data):
        instance.followup_status='completed'
        instance.completed_date = validated_data.get('completed_date')
        instance.updated_by = validated_data.get('updated_by')
        instance.save()
        return instance

class EtaskMultiFollowUpCompleteViewSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    ids = serializers.ListField(required=False)
    request_status = serializers.CharField(required=False)
    message = serializers.CharField(required=False)
    class Meta:
        model = EtaskFollowUP
        fields = ('ids','request_status','message','updated_by')
        # extra_fields = ('ids','request_status','message','updated_by')
    def create(self, validated_data):
        ids = validated_data.pop('ids') if 'ids' in validated_data else ''
        error_list = list()
        success_list = list()
        if ids:
            for each in ids:
                instance = EtaskFollowUP.objects.get(id=each)
                try:
                    current_date = datetime.now()
                    instance.followup_status = 'completed'
                    # instance.completed_date = validated_data.get('completed_date')
                    instance.completed_date = current_date
                    instance.updated_by = validated_data.get('updated_by')
                    instance.save()
                    success_list.append(str(instance.id))
                except:
                    error_list.append(str(instance.id))
        else:
             pass
        print(error_list, success_list)
        error_msg = 'Followup with id {} can not be completed'.format(', '.join(error_list))
        success_msg = 'Followup with id {} has been completed'.format(', '.join(success_list))
        # msg = ''
        if error_list and success_list:
            validated_data['message'] = '{} and {}.'.format(success_msg, error_msg)
        elif error_list and not success_list:
            validated_data['message'] = '{}.'.format(error_msg)
        elif not error_list and success_list:
            validated_data['message'] = '{}.'.format(success_msg)
        # print(success_list,error_list)
        # print(msg)
        validated_data['request_status'] = 1
        # validated_data['message'] = msg
        return validated_data

class EtaskFollowUpDeleteSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = EtaskFollowUP
        fields = ('id','is_deleted','updated_by')

    def update(self, instance, validated_data):
        try:
            with transaction.atomic():
                # reporting_dates = ETaskReportingDates.objects.filter(
                #     task=instance.id,
                #     is_deleted=False)
                # for r_dates in reporting_dates:
                #     #print('r_dates_PRE_Status',r_dates.is_deleted)
                #     r_dates.is_deleted = True
                #     r_dates.updated_by =  validated_data.get('updated_by')
                #     #print('r_dates_status', r_dates.is_deleted)
                #     r_dates.save()
                instance.updated_by = validated_data.get('updated_by')
                instance.is_deleted = True
                instance.save()
                # instance.__dict__['reporting_dates'] = reporting_dates
            return instance
        except Exception as e:
            raise e

class EtaskFollowUpEditSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    # reporting_dates = serializers.ListField(required=False)

    class Meta:
        model = EtaskFollowUP
        fields = '__all__'
        # extra_fields = 'reporting_dates'

    def update(self,instance, validated_data):
        try:
            # reporting_dates = validated_data.pop('reporting_dates')if 'reporting_dates' in validated_data else ''
            updated_by = validated_data.get('updated_by')
            with transaction.atomic():

                instance.follow_up_task = validated_data['follow_up_task']
                instance.assign_for = validated_data['assign_for']
                instance.follow_up_date = validated_data['follow_up_date'] 
                # instance.end_date = validated_data['end_date']
                # instance.follow_up_time = validated_data['follow_up_time']
                instance.updated_by=updated_by
                instance.save()

                # existing_reporting_date=ETaskReportingDates.objects.filter(
                #         task_type=2,task=instance.id,is_deleted=False)
                # if existing_reporting_date:
                #     existing_reporting_date.delete()

                # r_dates_list = []
                # for r_date in reporting_dates:
                #     r_dates_details = ETaskReportingDates.objects.create(
                #             task_type=2,
                #             task=instance.id,
                #             reporting_date= datetime.strptime(r_date['r_dates'],"%Y-%m-%dT%H:%M:%S.%fZ"),
                #             created_by=updated_by,
                #             owned_by=updated_by)
                #     r_dates_details.__dict__.pop('_state') if '_state' in r_dates_details.__dict__.keys() else r_dates_details.__dict__
                #     r_dates_list.append(r_dates_details.__dict__)
               
                # instance.__dict__['reporting_dates'] = r_dates_list
                return instance.__dict__
                
        except Exception as e:
            raise e

class EtaskFollowUpRescheduleSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = EtaskFollowUP
        fields = ('id','follow_up_date','updated_by')

class EtaskMultiFollowUpRescheduleSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    ids = serializers.ListField(required=False)
    request_status = serializers.CharField(required=False)
    message = serializers.CharField(required=False)
    class Meta:
        model = EtaskFollowUP
        fields = ('id','follow_up_date','updated_by','ids','request_status','message')
    def create(self, validated_data):
        follow_up_date = validated_data.pop('follow_up_date') if 'follow_up_date' in validated_data else ''
        updated_by = validated_data.pop('updated_by')
        ids = validated_data.pop('ids') if 'ids' in validated_data else ''
        error_list = list()
        success_list = list()
        if ids:
            for each in ids:
                instance = EtaskFollowUP.objects.get(id=each)
                try:

                    instance.follow_up_date = follow_up_date
                    # instance.completed_date = current_date
                    instance.updated_by = updated_by
                    instance.save()
                    success_list.append(str(instance.id))
                except:
                    error_list.append(str(instance.id))
        else:
            pass
        print(error_list, success_list)
        error_msg = 'Followup with id {} can not be rescheduled'.format(', '.join(error_list))
        success_msg = 'Followup with id {} has been rescheduled'.format(', '.join(success_list))
        # msg = ''
        if error_list and success_list:
            validated_data['message'] = '{} and {}.'.format(success_msg, error_msg)
        elif error_list and not success_list:
            validated_data['message'] = '{}.'.format(error_msg)
        elif not error_list and success_list:
            validated_data['message'] = '{}.'.format(success_msg)
        # print(success_list,error_list)
        # print(msg)
        validated_data['request_status'] = 1
        # validated_data['message'] = msg
        return validated_data




class ETaskAssignToListSerializer(serializers.ModelSerializer):
    class Meta:
        model = TCoreUserDetail
        fields = ('id','cu_user','reporting_head',) 


class ETaskAppointmentAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    internal_invite = serializers.ListField(required=False)
    external_invite = serializers.ListField(required=False)
    class Meta:
        model=EtaskAppointment
        fields='__all__'

    def create(self,validated_data):
        try:
            owned_by = validated_data.get('owned_by')
            created_by = validated_data.get('created_by')
            request = self.context.get('request')
            with transaction.atomic():
                email_list =[]
                internal_invite=validated_data.pop('internal_invite') if 'internal_invite' in validated_data else ""
                external_invite=validated_data.pop('external_invite') if 'external_invite' in validated_data else ""
                sd_date = validated_data.pop('start_date')
                ed_date = validated_data.pop('end_date')
                #print('start_date',sd_date,'enddate',ed_date)
                start_date =datetime.strptime(datetime.strftime(sd_date,"%Y-%m-%dT%H:%M:%S"),"%Y-%m-%dT%H:%M:%S")
                end_date = datetime.strptime(datetime.strftime(ed_date,"%Y-%m-%dT%H:%M:%S"),"%Y-%m-%dT%H:%M:%S")
                #print("start_date",start_date,type(start_date))
                #print("validated_data",validated_data)
                apointment_create = EtaskAppointment.objects.create(Appointment_status='ongoing',start_date=start_date,
                                                                    end_date=end_date,**validated_data)

                internal_invite_list = [EtaskInviteEmployee.objects.create(appointment=apointment_create,**int_invite) 
                                        for int_invite in internal_invite]
                external_invite_list = [EtaskInviteExternalPeople.objects.create(appointment=apointment_create,**ext_invite) 
                                        for ext_invite in external_invite]

                user_dict = {
                    "user_full_name" : userdetails(validated_data['created_by'].id),
                    "email_id" : User.objects.get(id=validated_data['created_by'].id).cu_user.cu_alt_email_id
                }
                email_list.append(user_dict)
                user_dict = {}

                for invites in internal_invite:
                    user_email = User.objects.get(id=invites['user_id']).cu_user.cu_alt_email_id

                    ## modified by manas Paul 21jan20
                    user_dict = {
                        "user_full_name" : userdetails(invites['user_id']),
                        "email_id" : user_email
                    }
                    email_list.append(user_dict)
                    user_dict = {}

                for invites in external_invite:
                    ## modified by manas Paul 21jan20
                    user_dict = {
                        "user_full_name" :invites['external_people'],
                        "email_id" : invites['external_email']
                    }
                    email_list.append(user_dict)
                    user_dict = {}
                
                #print("email_list",email_list)
             

                # ============= Mail Send Step ==============#
                # email = email_list
                # email_list = ['bubai.das@shyamfuture.com','rupam@shyamfuture.com','koushik.goswami@shyamfuture.com']
                # email_admin= 'abhishekrock94@shyamfuture.com'
                # #print("email",email_list) 

                #==============================================#
                s_date = start_date.strftime("%Y%m%dT%H%M%S")
                e_date = start_date.strftime("%Y%m%dT%H%M%S")
                ics_data = """BEGIN:VCALENDAR
VERSION:2.0
CALSCALE:GREGORIAN
BEGIN:VEVENT
SUMMARY:Appointment of {app_sub}
DTSTART;TZID=Asia/Kolkata:{s_date}
DTEND;TZID=Asia/Kolkata:{e_date}
LOCATION:Shyam Tower,Kolkata-700091
DESCRIPTION: Appointment.
STATUS:CONFIRMED
SEQUENCE:3
BEGIN:VALARM
TRIGGER:-PT10M
DESCRIPTION:Pickup Reminder
ACTION:DISPLAY
END:VALARM
END:VEVENT
END:VCALENDAR""".replace("{s_date}",s_date).replace("{e_date}",e_date).replace("{app_sub}",validated_data.get('appointment_subject'))

                #===============================================#
                
                if email_list:
                    # for email in email_list:
                    for mail in email_list: ## modified by manas Paul 21jan20
                        mail_data = {
                                    "recipient_name" : mail['user_full_name'],        ## modified by manas Paul 21jan20
                                    "taskSubject": validated_data.get('appointment_subject'),
                                    "location":validated_data.get('location'),
                                    "start_date":start_date,
                                    "end_date":end_date,
                                    "start_time":validated_data.get('start_time'),
                                    "end_time":validated_data.get('end_time'),
                            }
                        # #print('mail_data',mail_data)
                        # #print('mail_id-->',mail)
                        # #print('mail_id-->',[mail])
                        # mail_class = GlobleMailSend('ETAP', email_list)
                        # mail_class = GlobleMailSend('ETAP', [mail['email_id']])
                        # # #print('mail_class',mail_class)
                        # mail_thread = Thread(target = mail_class.mailsend, args = (mail_data,ics_data))
                        # # #print('mail_thread-->',mail_thread)
                        # mail_thread.start()
                        send_mail_list('ETAP', [mail['email_id']], mail_data, ics=ics_data)
                #===============================================#
           
                # #print("internal_invite_list",internal_invite_list,'external_invite_list',external_invite_list)
                validated_data['id']= apointment_create.id
                validated_data['start_date']=start_date
                validated_data['end_date']=end_date
                validated_data['Appointment_status']='ongoing'
                validated_data['internal_invite']=internal_invite
                validated_data['external_invite']=external_invite

                return validated_data  

        except Exception as e:
            raise e 


class ETaskAppointmentAddSerializerV2(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    #owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    internal_invite = serializers.ListField(required=False)
    external_invite = serializers.ListField(required=False)
    
    class Meta:
        model=EtaskAppointment
        fields='__all__'

    def create(self,validated_data):
        try:
            #owned_by = validated_data.get('owned_by')
            created_by = validated_data.get('created_by')
            request = self.context.get('request')
            with transaction.atomic():
                email_list =[]
                internal_invite=validated_data.pop('internal_invite') if 'internal_invite' in validated_data else ""
                external_invite=validated_data.pop('external_invite') if 'external_invite' in validated_data else ""
                sd_date = validated_data.pop('start_date')
                ed_date = validated_data.pop('end_date')
                facilitator = validated_data.get('facilitator',2)
                #print('start_date',sd_date,'enddate',ed_date)
                start_date =datetime.strptime(datetime.strftime(sd_date,"%Y-%m-%dT%H:%M:%S"),"%Y-%m-%dT%H:%M:%S")
                end_date = datetime.strptime(datetime.strftime(ed_date,"%Y-%m-%dT%H:%M:%S"),"%Y-%m-%dT%H:%M:%S")
                #print("start_date",start_date,type(start_date))
                #print("validated_data",validated_data)
                apointment_create = EtaskAppointment.objects.create(Appointment_status='ongoing',start_date=start_date,
                                                                    end_date=end_date,**validated_data)

                internal_invite_list = [EtaskInviteEmployee.objects.create(appointment=apointment_create,**int_invite) 
                                        for int_invite in internal_invite]
                external_invite_list = [EtaskInviteExternalPeople.objects.create(appointment=apointment_create,**ext_invite) 
                                        for ext_invite in external_invite]

                user_dict = {
                    "user_full_name" : apointment_create.owned_by.get_full_name(),
                    "email_id" : apointment_create.owned_by.cu_user.cu_alt_email_id
                }
                email_list.append(user_dict)
                if facilitator == 1:
                    email_list.append({
                            "user_full_name" : created_by.get_full_name(),
                            "email_id" : created_by.cu_user.cu_alt_email_id
                        })
                user_dict = {}
                internal_list = list()
                for invites in internal_invite:
                    user_email = User.objects.get(id=invites['user_id']).cu_user.cu_alt_email_id

                    ## modified by manas Paul 21jan20
                    user_dict = {
                        "user_full_name" : userdetails(invites['user_id']),
                        "email_id" : user_email
                    }
                    email_list.append(user_dict)
                    user_dict = {}
                    internal_list.append({'name':userdetails(invites['user_id']),'email':user_email})
                external_list = list()
                for invites in external_invite:
                    ## modified by manas Paul 21jan20
                    user_dict = {
                        "user_full_name" :invites['external_people'],
                        "email_id" : invites['external_email']
                    }
                    email_list.append(user_dict)
                    user_dict = {}
                    external_list.append({'name':invites['external_people'],'email':invites['external_email']})
                #print("email_list",email_list)


                # ============= Mail Send Step ==============#
                # email = email_list
                # email_list = ['bubai.das@shyamfuture.com','rupam@shyamfuture.com','koushik.goswami@shyamfuture.com']
                # email_admin= 'abhishekrock94@shyamfuture.com'
                # #print("email",email_list) 

                #==============================================#

                s_date = datetime.combine(start_date.date(),validated_data.get('start_time')).strftime("%Y%m%dT%H%M%S")
                e_date = datetime.combine(end_date.date(),validated_data.get('end_time')).strftime("%Y%m%dT%H%M%S")
                invitation_from = '{} ({})'.format(apointment_create.owned_by.get_full_name(), apointment_create.owned_by.cu_user.cu_alt_email_id)
                invited_to = ', '.join(['{} ({})'.format(ne['user_full_name'],ne['email_id']) for ne in email_list if ne['email_id'] != apointment_create.owned_by.cu_user.cu_alt_email_id])
                ics_data = """BEGIN:VCALENDAR
VERSION:2.0
CALSCALE:GREGORIAN
BEGIN:VEVENT
SUMMARY:Appointment of {}
DTSTART;TZID=Asia/Kolkata:{}
DTEND;TZID=Asia/Kolkata:{}
LOCATION:Shyam Tower,Kolkata-700091
DESCRIPTION: Appointment Invitation From-> {}  Invited People-> {}
STATUS:CONFIRMED
SEQUENCE:3
BEGIN:VALARM
TRIGGER:-PT10M
DESCRIPTION:Pickup Reminder
ACTION:DISPLAY
END:VALARM
END:VEVENT
END:VCALENDAR""".format(apointment_create.appointment_subject,s_date,e_date,invitation_from,invited_to)

                #===============================================#
                if email_list:
                    # for email in email_list:
                    print('email_list',email_list)
                    for mail in email_list: ## modified by manas Paul 21jan20
                        mail_data = {
                                    "recipient_name" : mail['user_full_name'],        ## modified by manas Paul 21jan20
                                    "appointment_subject": validated_data.get('appointment_subject'),
                                    "facilitator_name": apointment_create.owned_by.get_full_name(),
                                    "location":validated_data.get('location'),
                                    "start_date":start_date.date(),
                                    "end_date":end_date.date(),
                                    "start_time":validated_data.get('start_time'),
                                    "end_time":validated_data.get('end_time'),
                                    "internal_invitees":internal_list,
                                    "external_invitees":external_list,
                                    "invitee_count":len(internal_list)+len(external_list)
                                }
                        # #print('mail_data',mail_data)
                        # #print('mail_id-->',mail)
                        # #print('mail_id-->',[mail])
                        # mail_class = GlobleMailSend('ETAP', email_list)
                        # mail_class = GlobleMailSend('ETAP', [mail['email_id']])
                        # # #print('mail_class',mail_class)
                        # mail_thread = Thread(target = mail_class.mailsend, args = (mail_data,ics_data))
                        # # #print('mail_thread-->',mail_thread)
                        # mail_thread.start()
                        send_mail_list('ETAP', [mail['email_id']], mail_data, ics=ics_data)
                #===============================================#
           
                # #print("internal_invite_list",internal_invite_list,'external_invite_list',external_invite_list)
                validated_data['id']= apointment_create.id
                validated_data['start_date']=start_date
                validated_data['end_date']=end_date
                validated_data['Appointment_status']='ongoing'
                validated_data['internal_invite']=internal_invite
                validated_data['external_invite']=external_invite

                return validated_data  

        except Exception as e:
            raise e 


class ETaskAppointmentUpdateSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    internal_invite = serializers.ListField(required=False)
    external_invite = serializers.ListField(required=False)
    class Meta:
        model=EtaskAppointment
        fields='__all__'
    
    def update(self, instance, validated_data):
        email_list = []
        internal_emails =[]
        external_emails = []
        appointment_subject = validated_data.pop('appointment_subject') if 'appointment_subject' in validated_data else ""
        location = validated_data.pop('location') if 'location' in validated_data else ""
        sd_date = validated_data.pop('start_date') if 'start_date' in validated_data else ""
        ed_date = validated_data.pop('end_date') if 'end_date' in validated_data else ""
        start_time= validated_data.pop('start_time') if 'start_time' in validated_data else ""
        end_time= validated_data.pop('end_time') if 'end_time' in validated_data else ""
        internal_invite = validated_data.pop('internal_invite') if 'internal_invite' in validated_data else ""
        external_invite = validated_data.pop('external_invite') if 'external_invite' in validated_data else ""
        start_date =datetime.strptime(datetime.strftime(sd_date,"%Y-%m-%dT%H:%M:%S"),"%Y-%m-%dT%H:%M:%S")
        end_date = datetime.strptime(datetime.strftime(ed_date,"%Y-%m-%dT%H:%M:%S"),"%Y-%m-%dT%H:%M:%S")
        for invites in internal_invite:
            user_email = User.objects.get(id=invites['user_id']).cu_user.cu_alt_email_id
            internal_emails.append(user_email)
        for invites in external_invite:
            external_emails.append(invites['external_email'])

        #previous detials 
        previous_invites_email = EtaskInviteEmployee.objects.filter(appointment=instance.id).values_list('user__cu_user__cu_alt_email_id',flat=True)
        previous_external_emails = EtaskInviteExternalPeople.objects.filter(appointment=instance.id).values_list('external_email',flat=True)
        #print("previous_email_list",list(previous_invites_email),list(previous_external_emails))
        #print("new_email_list",internal_emails,external_emails)
        deleted_internal_invites = list(set(previous_invites_email)-set(internal_emails))
        added_internal_invites = list(set(internal_emails)-set(previous_invites_email))
        external_deleted_internal_invites = list(set(previous_external_emails)-set(external_emails))
        external_added_internal_invites = list(set(external_emails)-set(previous_external_emails))
        #print("deleted_internal_invites",deleted_internal_invites,external_deleted_internal_invites)
        #print("added_internal_invites",added_internal_invites,external_added_internal_invites)
        all_remaining_invites = list(set(internal_emails+external_emails)-set(added_internal_invites+external_added_internal_invites))
        #print("all_new_invites",all_remaining_invites)
        
        if instance.location != location or instance.start_date != start_date \
            or instance.end_date != end_date or instance.start_time != start_time or instance.end_time != end_time:
            EtaskAppointment.objects.filter(id=instance.id).update(location=location,start_date=start_date,
                        end_date=end_date,start_time=start_time,end_time=end_time)
            # ============= Mail Send Step ==============#
            # email = email_list
            # email_list = ['bubai.das@shyamfuture.com','rupam@shyamfuture.com','koushik.goswami@shyamfuture.com']
            # email_admin= 'abhishekrock94@shyamfuture.com'
            #print("email",email_list) 
            
            if all_remaining_invites:
                # for email in email_list:
                mail_data = {
                            "appointmentsubject":appointment_subject,
                            "location":location,
                            "start_date":start_date,
                            "end_date":end_date,
                            "start_time":start_time,
                            "end_time":end_time,

                    }
                #print('mail_data',mail_data)
                # mail_class = GlobleMailSend('ETAP-SU', all_remaining_invites)
                # #print('mail_class',mail_class)
                # mail_thread = Thread(target = mail_class.mailsend, args = (mail_data,None))
                # mail_thread.start()
                send_mail_list('ETAP-SU', all_remaining_invites, mail_data, ics='')
                #===============================================#
        
        if deleted_internal_invites or external_deleted_internal_invites:
            EtaskInviteEmployee.objects.filter(appointment=instance.id,user__cu_user__cu_alt_email_id__in=deleted_internal_invites).update(is_deleted=True)
            EtaskInviteExternalPeople.objects.filter(appointment=instance.id,external_email__in=external_deleted_internal_invites).update(is_deleted=True)

            email_list_deleted_appo = deleted_internal_invites + external_deleted_internal_invites
            if email_list_deleted_appo:
                # for email in email_list:
                mail_data = {
                            "appointmentsubject":appointment_subject,
                            "location":location,

                    }
                #print('mail_data',mail_data)
                # mail_class = GlobleMailSend('ETAP-CA', email_list_deleted_appo)
                # #print('mail_class',mail_class)
                # mail_thread = Thread(target = mail_class.mailsend, args = (mail_data,None))
                # mail_thread.start()
                send_mail_list('ETAP-CA', email_list_deleted_appo, mail_data, ics='')
                #===============================================#
        if added_internal_invites or external_added_internal_invites:
            user_id = User.objects.filter(email__in=added_internal_invites).values_list('id',flat=True)
            for x in list(user_id):
                EtaskInviteEmployee.objects.create(appointment_id=instance.id,user_id=x)
            for x in external_added_internal_invites:
                name = [ n['external_people'] for n in external_invite if n['external_email'] == x ]
                EtaskInviteExternalPeople.objects.create(appointment_id=instance.id,external_email=x,external_people=name[0])
            
            email_list_added_appo = added_internal_invites + external_added_internal_invites
            # ============= Mail Send Step ==============#
            # email = email_list
            # email_list = ['bubai.das@shyamfuture.com','rupam@shyamfuture.com','koushik.goswami@shyamfuture.com']
            # email_admin= 'abhishekrock94@shyamfuture.com'
            #print("email",email_list_added_appo) 
            
            if email_list_added_appo:
                # for email in email_list:
                mail_data = {
                        "taskSubject":appointment_subject,
                        "location":location,
                        "start_date":start_date,
                        "end_date":end_date,
                        "start_time":start_time,
                        "end_time":end_time,

                    }
                #print('mail_data',mail_data)
                # mail_class = GlobleMailSend('ETAP', email_list_added_appo)
                # #print('mail_class',mail_class)
                # mail_thread = Thread(target = mail_class.mailsend, args = (mail_data,None))
                # mail_thread.start()
                send_mail_list('ETAP', email_list_added_appo, mail_data, ics='')
                #===============================================#
            validated_data['appointment_subject']=appointment_subject
            validated_data['location']=location
            validated_data['start_date']=start_date
            validated_data['end_date']=end_date
            validated_data['start_time']=start_time
            validated_data['end_time']=end_time
            validated_data['internal_invite']=internal_invite
            validated_data['external_invite']=external_invite
        return validated_data


class ETaskAppointmentUpdateSerializerV2(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    #owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    internal_invite = serializers.ListField(required=False)
    external_invite = serializers.ListField(required=False)

    class Meta:
        model=EtaskAppointment
        fields='__all__'
    
    def update(self, instance, validated_data):
        email_list = []
        internal_emails =[]
        external_emails = []
        loggedin_user=self.context['request'].user
        created_by = validated_data.get('validated_data',loggedin_user)
        owned_by = validated_data.pop('owned_by') if 'owned_by' in validated_data else ""
        usr_obj = User.objects.get(id=owned_by.id)
        facilitator = validated_data.pop('facilitator') if 'facilitator' in validated_data else ""
        appointment_subject = validated_data.pop('appointment_subject') if 'appointment_subject' in validated_data else ""
        location = validated_data.pop('location') if 'location' in validated_data else ""
        sd_date = validated_data.pop('start_date') if 'start_date' in validated_data else ""
        ed_date = validated_data.pop('end_date') if 'end_date' in validated_data else ""
        start_time= validated_data.pop('start_time') if 'start_time' in validated_data else ""
        end_time= validated_data.pop('end_time') if 'end_time' in validated_data else ""
        internal_invite = validated_data.pop('internal_invite') if 'internal_invite' in validated_data else ""
        external_invite = validated_data.pop('external_invite') if 'external_invite' in validated_data else ""
        start_date =datetime.strptime(datetime.strftime(sd_date,"%Y-%m-%dT%H:%M:%S"),"%Y-%m-%dT%H:%M:%S")
        end_date = datetime.strptime(datetime.strftime(ed_date,"%Y-%m-%dT%H:%M:%S"),"%Y-%m-%dT%H:%M:%S")
        
        n_user = list()
        remain_invitee_name_email=list()
        internal_list = list()
        for invites in internal_invite:
            i_user = User.objects.get(id=invites['user_id'])
            n_user.append(i_user)
            user_email = i_user.cu_user.cu_alt_email_id
            internal_emails.append(user_email)
            internal_list.append({'name':i_user.get_full_name(),'email':user_email})
            if EtaskInviteEmployee.objects.filter(appointment=instance.id,user=i_user,is_deleted=False).count()>0:
                remain_invitee_name_email.append({'name':i_user.get_full_name(),'email':user_email})
        external_list = list()
        for invites in external_invite:
            external_emails.append(invites['external_email'])
            external_list.append({'name':invites['external_people'],'email':invites['external_email']})
            if EtaskInviteExternalPeople.objects.filter(appointment=instance.id,external_email=invites['external_email'],is_deleted=False).count()>0:
                remain_invitee_name_email.append({'name':invites['external_people'],'email':invites['external_email']})
        #previous detials 
        previous_invites_email = EtaskInviteEmployee.objects.filter(appointment=instance.id,is_deleted=False).values_list('user__cu_user__cu_alt_email_id',flat=True)
        previous_external_emails = EtaskInviteExternalPeople.objects.filter(appointment=instance.id,is_deleted=False).values_list('external_email',flat=True)
        #print("previous_email_list",list(previous_invites_email),list(previous_external_emails))
        #print("new_email_list",internal_emails,external_emails)
        deleted_internal_invites = list(set(previous_invites_email)-set(internal_emails))
        added_internal_invites = list(set(internal_emails)-set(previous_invites_email))
        external_deleted_internal_invites = list(set(previous_external_emails)-set(external_emails))
        external_added_internal_invites = list(set(external_emails)-set(previous_external_emails))
        #print("deleted_internal_invites",deleted_internal_invites,external_deleted_internal_invites)
        print("added_internal_invites",added_internal_invites,external_added_internal_invites)
        all_remaining_invites = list(set(internal_emails+external_emails)-set(added_internal_invites+external_added_internal_invites))
        print("all_new_invites",all_remaining_invites)
        

        s_date = datetime.combine(start_date.date(),start_time).strftime("%Y%m%dT%H%M%S")
        e_date = datetime.combine(end_date.date(),end_time).strftime("%Y%m%dT%H%M%S")
        invitation_from = '{} ({})'.format(instance.owned_by.get_full_name(), instance.owned_by.cu_user.cu_alt_email_id)
        total_invited_lists = external_list + internal_list
        invited_to = ', '.join(['{} ({})'.format(ne['name'],ne['email']) for ne in total_invited_lists if ne['email'] != instance.owned_by.cu_user.cu_alt_email_id])
        ics_data = """BEGIN:VCALENDAR
VERSION:2.0
CALSCALE:GREGORIAN
BEGIN:VEVENT
SUMMARY:Appointment of {}
DTSTART;TZID=Asia/Kolkata:{}
DTEND;TZID=Asia/Kolkata:{}
LOCATION:Shyam Tower,Kolkata-700091
DESCRIPTION: Appointment Invitation From-> {}  Invited People-> {}
STATUS:CONFIRMED
SEQUENCE:3
BEGIN:VALARM
TRIGGER:-PT10M
DESCRIPTION:Pickup Reminder
ACTION:DISPLAY
END:VALARM
END:VEVENT
END:VCALENDAR""".format(appointment_subject,s_date,e_date,invitation_from,invited_to)


        if instance.location != location or instance.start_date != start_date \
            or instance.end_date != end_date or instance.start_time != start_time or instance.end_time != end_time or\
                instance.appointment_subject != appointment_subject or instance.facilitator != facilitator or \
                instance.owned_by.id != usr_obj.id:
            EtaskAppointment.objects.filter(id=instance.id).update(location=location,start_date=start_date,
                        end_date=end_date,start_time=start_time,end_time=end_time,appointment_subject=appointment_subject,
                                                                   facilitator=facilitator,owned_by=usr_obj)
            # ============= Mail Send Step ==============#
            # email = email_list
            # email_list = ['bubai.das@shyamfuture.com','rupam@shyamfuture.com','koushik.goswami@shyamfuture.com']
            # email_admin= 'abhishekrock94@shyamfuture.com'
            #print("email",email_list)
            remain_invitee_name_email.append({'name': usr_obj.get_full_name(), 'email': usr_obj.cu_user.cu_alt_email_id})
            if facilitator == 1:
                remain_invitee_name_email.append(
                    {'name': created_by.get_full_name(), 'email': created_by.cu_user.cu_alt_email_id})
            
            if remain_invitee_name_email:
                print('remain_invitee_name_email',remain_invitee_name_email)
                for remain_invitee in remain_invitee_name_email:
                    mail_data = {

                                "recipient_name" : remain_invitee['name'],
                                "appointment_subject":appointment_subject,
                                "facilitator_name": usr_obj.get_full_name(),
                                "location":location,
                                "start_date":start_date.date(),
                                "end_date":end_date.date(),
                                "start_time":start_time,
                                "end_time":end_time,
                                "internal_invitees":internal_list,
                                "external_invitees":external_list,
                                "invitee_count":len(internal_list)+len(external_list)
                            }
                    #print('mail_data',mail_data)
                    # mail_class = GlobleMailSend('ETAP-SU', [remain_invitee['email']])
                    # #print('mail_class',mail_class)
                    # mail_thread = Thread(target = mail_class.mailsend, args = (mail_data,ics_data))
                    # mail_thread.start()
                    send_mail_list('ETAP-SU', [remain_invitee['email']], mail_data, ics=ics_data)
                #===============================================#
        
        if deleted_internal_invites or external_deleted_internal_invites:
            deleted_invitee = EtaskInviteEmployee.objects.filter(appointment=instance.id,user__cu_user__cu_alt_email_id__in=deleted_internal_invites,is_deleted=False)
            deleted_external = EtaskInviteExternalPeople.objects.filter(appointment=instance.id,external_email__in=external_deleted_internal_invites,is_deleted=False)

            deleted_inter_list = [{'name':internal.user.get_full_name(),'email':internal.user.cu_user.cu_alt_email_id} for internal in deleted_invitee]
            deleted_exter_list = [{'name':external.external_people,'email':external.external_email} for external in deleted_external]
            deleted_invitee_mail = deleted_inter_list + deleted_exter_list

            deleted_external.update(is_deleted=True)
            deleted_invitee.update(is_deleted=True)

            email_list_deleted_appo = deleted_internal_invites + external_deleted_internal_invites
            if email_list_deleted_appo:
                print('email_list_deleted_appo',email_list_deleted_appo)
                print('deleted_invitee_mail',deleted_invitee_mail)
                
                for deleted_mail in deleted_invitee_mail:
                    mail_data = {
                                    "recipient_name" : deleted_mail['name'],
                                    "appointment_subject":appointment_subject,
                                    "facilitator_name": instance.owned_by.get_full_name(),
                                    "location":location,
                                    "start_date":start_date.date(),
                                    "end_date":end_date.date(),
                                    "start_time":start_time,
                                    "end_time":end_time,
                                    "cancelled_by":loggedin_user.get_full_name()
                                }
                    #print('mail_data',mail_data)
                    # mail_class = GlobleMailSend('ETAP-CA', [deleted_mail['email']])
                    # #print('mail_class',mail_class)
                    # mail_thread = Thread(target = mail_class.mailsend, args = (mail_data,ics_data))
                    # mail_thread.start()
                    send_mail_list('ETAP-CA', [deleted_mail['email']], mail_data, ics=ics_data)
                #===============================================#
        invitee_name_email = list()
        if added_internal_invites or external_added_internal_invites:
            user_id = User.objects.filter(email__in=added_internal_invites).values_list('id',flat=True)
            for x in list(user_id):
                etask_invite_employee = EtaskInviteEmployee.objects.create(appointment_id=instance.id,user_id=x)
                invitee_name_email.append({'name':etask_invite_employee.user.get_full_name(),'email':etask_invite_employee.user.cu_user.cu_alt_email_id})
            for x in external_added_internal_invites:
                name = [ n['external_people'] for n in external_invite if n['external_email'] == x ]
                etask_external_people = EtaskInviteExternalPeople.objects.create(appointment_id=instance.id,external_email=x,external_people=name[0])
                invitee_name_email.append({'name':etask_external_people.external_people,'email':etask_external_people.external_email})
            email_list_added_appo = added_internal_invites + external_added_internal_invites
            # ============= Mail Send Step ==============#
            # email = email_list
            # email_list = ['bubai.das@shyamfuture.com','rupam@shyamfuture.com','koushik.goswami@shyamfuture.com']
            # email_admin= 'abhishekrock94@shyamfuture.com'
            #print("email",email_list_added_appo) 
            
            if invitee_name_email:
                print('invitee_name_email',invitee_name_email)
                for invitee in invitee_name_email:
                    mail_data = {
                            "recipient_name" : invitee['name'],
                            "appointment_subject":appointment_subject,
                            "facilitator_name": instance.owned_by.get_full_name(),
                            "location":location,
                            "start_date":start_date.date(),
                            "end_date":end_date.date(),
                            "start_time":start_time,
                            "end_time":end_time,
                            "internal_invitees":internal_list,
                            "external_invitees":external_list,
                            "invitee_count":len(internal_list)+len(external_list)
                        }
                    #print('mail_data',mail_data)
                    # mail_class = GlobleMailSend('ETAP', [invitee['email']])
                    # #print('mail_class',mail_class)
                    # mail_thread = Thread(target = mail_class.mailsend, args = (mail_data,ics_data))
                    # mail_thread.start()
                    send_mail_list('ETAP', [invitee['email']], mail_data, ics=ics_data)
                #===============================================#
            validated_data['appointment_subject']=appointment_subject
            validated_data['location']=location
            validated_data['start_date']=start_date
            validated_data['end_date']=end_date
            validated_data['start_time']=start_time
            validated_data['end_time']=end_time
            validated_data['internal_invite']=internal_invite
            validated_data['external_invite']=external_invite

            users = n_user
            title = 'The appointment has been sheduled on {}.'.format(start_date.date())
            body ='Appointment Subject: {} \nLocation:{}'.format(appointment_subject,location)

            data = {
                        "app_module":"etask",
                        "type":"appointment",
                        "id":instance.id
                    }
            data_str = json.dumps(data)
            notification_id = store_sent_notification(users=users,body=body,title=title,data=data_str,app_module_name='etask')
            send_notification(users=users,body=body,title=title,data=data,notification_id=notification_id)
                
        return validated_data


class ETaskAppointmentCalanderSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    internal_invite = serializers.ListField(required=False)
    external_invite = serializers.ListField(required=False)
    class Meta:
        model=EtaskAppointment
        fields='__all__'

#::::::::::::::::::::::::: TASK COMMENTS:::::::::::::::::::::::::::#
class ETaskAppointmentCommentsSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    cost_details=serializers.ListField(required=False)
    other_details=serializers.ListField(required=False)
    
    class Meta:
        model=AppointmentComments
        fields='__all__'
        extra_fields=('cost_details','other_details')

    def create(self,validated_data):
        try:
            cost_details=validated_data.pop('cost_details')if 'cost_details' in validated_data else ""
            other_details=validated_data.pop('other_details')if 'other_details' in validated_data else "" 
            created_by=validated_data.get('created_by')
            owned_by=validated_data.get('owned_by')
            cost_details_list=[]
            other_details_list=[]
            
            with transaction.atomic():
                appointment_comments=AppointmentComments.objects.create(**validated_data)

                # #print("appointment_comments-->",appointment_comments)
                
                for c_d in cost_details:
                    cost_data=AppointmentIncludeAdvanceCommentsCostDetails.objects.create(apcomments=appointment_comments,
                                                                                                  **c_d,
                                                                                                  created_by=created_by,
                                                                                                  owned_by=owned_by
                                                                                                    )
                    cost_data.__dict__.pop('_state') if "_state" in cost_data.__dict__.keys() else cost_data.__dict__
                    cost_details_list.append(cost_data.__dict__)
                # #print('cost_details_list-->',cost_details_list)

                for o_d in other_details:
                    others_data=AppointmentIncludeAdvanceCommentsOtherDetails.objects.create(apcomments=appointment_comments,
                                                                                                    **o_d,
                                                                                                    created_by=created_by,
                                                                                                    owned_by=owned_by
                                                                                                    )
                    others_data.__dict__.pop('_state')if '_state' in others_data.__dict__.keys() else others_data.__dict__
                    other_details_list.append(others_data.__dict__)
                # #print('other_details_list-->',other_details_list)

                appointment_comments.__dict__['cost_details']=cost_details_list
                appointment_comments.__dict__['other_details']=other_details_list
                return appointment_comments
               
        except Exception as e:
            raise e

class ETaskAppointmentCommentsAdvanceAttachmentAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model=AppointmentIncludeAdvanceCommentsDocuments
        fields='__all__'

class EtasCommentsListSerializer(serializers.ModelSerializer):
    
    class Meta:
        model=AppointmentComments
        fields='__all__'


class EtasCommentsListSerializerV2(serializers.ModelSerializer):
    
    class Meta:
        model=AppointmentComments
        fields='__all__'


class ETaskReportsSerializer(serializers.ModelSerializer):
    assign_by_name = serializers.SerializerMethodField()
    sub_data = EtaskTask.objects.filter(parent_id=0,is_deleted=False)
    parent_task=serializers.SerializerMethodField(required=False)
    reporting_dates=serializers.SerializerMethodField()
    class Meta:
        model=EtaskTask
        fields=('id','task_code_id','parent_id','task_subject','task_description','start_date','end_date','task_status','completed_date',
                    'extended_date','assign_by','assign_by_name','assign_to','sub_assign_to_user',
                    'reporting_dates','parent_task')
    def user_name(self, user_id):
        name = None
        full_name = ""
        name = User.objects.get(id=user_id)
        if name:
            full_name =  name.__dict__['first_name']+" "+name.__dict__['last_name']
        return full_name

    def get_assign_by_name(self,EtaskTask):
        name = None
        full_name = ""
        if EtaskTask.assign_by:
            name = User.objects.get(id=EtaskTask.assign_by.id)
            if name:
                full_name =  name.__dict__['first_name']+" "+name.__dict__['last_name']
                # #print("full_name",full_name)
            return full_name
    def get_reporting_dates(self,EtaskTask):
        if EtaskTask.id:
            report_date_list = []
            report_date=ETaskReportingDates.objects.filter(task_type=1,task=EtaskTask.id,is_deleted=False)
            # #print("report_date",report_date)
            current_date=datetime.now().date()
            if report_date:
                for dt in report_date:
                    pre_report= dt.reporting_date.date()
                    # #print('pre_report',pre_report)
                    if dt.reporting_status==2:
                        days_count=(current_date-pre_report).days
                        #print('days_count',days_count)
                    else:
                        days_count = 0
                    dt_dict={
                        'id':dt.id,
                        'reporting_date':dt.reporting_date,
                        'reporting_status':dt.reporting_status,
                        'reporting_status_name':dt.get_reporting_status_display(),
                        'crossed_by':days_count
                    }
                    report_date_list.append(dt_dict)
                
                    
                return report_date_list
            else:
                return []
   
    def get_parent_task(self,EtaskTask):
        if EtaskTask.parent_id:
            # id_data = EtaskTask.get('parent_id')
            # #print("id_data",id_data)
            # #print('sad',EtaskTask.parent_id)
            if  EtaskTask.parent_id !=0:
                if self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject'):
                    parent_data=self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject')[0]
                    # #print('parent_data',parent_data)
                    return parent_data
        

class EtaskUpcommingReportingListSerializer(serializers.ModelSerializer):

    class Meta:
        model = EtaskTask
        fields = '__all__'

class EtaskReportingDateReportedSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    completed_status = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = ETaskReportingDates
        fields = '__all__'
    def update(self, instance, validated_data):
        current_date = datetime.now()
        # #print('current_date-->',current_date)
        updated_by = validated_data.get('updated_by')
        instance.task_type = 1
        instance.task_status=1
        instance.reporting_status = 1
        instance.actual_reporting_date = current_date
        instance.updated_by = updated_by
        instance.save()
        prev_action= ETaskReportingActionLog.objects.filter(
            task_id = instance.task,
            reporting_date_id = instance.id,
            is_deleted=False
            ).update(is_deleted=True)
        reporting_log = ETaskReportingActionLog.objects.create(
            task_id = instance.task,
            reporting_date_id = instance.id,
            status = 1,
            updated_by = updated_by
            )
        # #print('reporting_log-->',reporting_log)
        return instance


class EtaskReportingDateReportedSerializerV2(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    completed_status = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = ETaskReportingDates
        fields = '__all__'

    def previous_reporting_mark_as_reported(self, reporting_date_obj=None, current_datetime=None, updated_by=None):

        # date_of_reporting = current_datetime if current_datetime > reporting_date_obj.reporting_date else reporting_date_obj.reporting_date
        previous_reportings_query = ETaskReportingDates.objects.filter(task=reporting_date_obj.task,owned_by=reporting_date_obj.owned_by,
                                reporting_date__lt=reporting_date_obj.reporting_date)

        for reporting_objj in previous_reportings_query:
            prev_action = ETaskReportingActionLog.objects.filter(
                task_id=reporting_objj.task,
                reporting_date_id=reporting_objj.id,
                is_deleted=False
            ).update(is_deleted=True)
            reporting_log = ETaskReportingActionLog.objects.create(
                task_id=reporting_objj.task,
                reporting_date_id=reporting_objj.id,
                status=1,
                updated_by=updated_by
            )
        previous_reportings_query.update(task_type=1,reporting_status=1,
                                actual_reporting_date=current_datetime,updated_by=updated_by)

        return

    def update(self, instance, validated_data):
        current_date = datetime.now()
        # #print('current_date-->',current_date)
        updated_by = validated_data.get('updated_by')
        instance.task_type = 1
        instance.task_status=1
        instance.reporting_status = 1
        instance.actual_reporting_date = current_date
        instance.updated_by = updated_by
        instance.save()
        prev_action= ETaskReportingActionLog.objects.filter(
            task_id = instance.task,
            reporting_date_id = instance.id,
            is_deleted=False
            ).update(is_deleted=True)
        reporting_log = ETaskReportingActionLog.objects.create(
            task_id = instance.task,
            reporting_date_id = instance.id,
            status = 1,
            updated_by = updated_by
            )

        # previous reporting dates aumatic reported
        self.previous_reporting_mark_as_reported(reporting_date_obj=instance, current_datetime=current_date, updated_by=updated_by)

        if instance.owned_by == updated_by:
            task = EtaskTask.objects.get(id=instance.task)
            end_date = task.extended_date if task.extended_date else task.end_date
            subassign_log = EtaskTaskSubAssignLog.objects.filter(task=task,assign_from=updated_by,is_deleted=False).first()
            if subassign_log:
                assign_to = subassign_log.sub_assign
            else:
                assign_to = task.assign_to
            
            # Default Reporting Date will be added #
            reporting_date_dict = {}
            default_reporting_dates = EtaskMonthlyReportingDate.objects.filter(employee=assign_to,
                                    owned_by=updated_by).values_list('field_value',flat=True)
            for date_ob in daterange(task.start_date.date(),end_date.date()):
                if date_ob.day in default_reporting_dates and date_ob >= current_date.date():
                    default_reporting_date = EtaskMonthlyReportingDate.objects.filter(employee=assign_to,
                                    field_value=date_ob.day,owned_by=updated_by).values('field_value','start_time').first()
                    
                    reporting_date_dict[str(date_ob)] = str(date_ob)+'T'+str(default_reporting_date['start_time']) if default_reporting_date['start_time'] else str(date_ob)+'T10:00:00'
                    break

            if reporting_date_dict:
                reporting_date_dict.update({str(end_date.date()):str(end_date.replace(hour=10, minute=00).strftime("%Y-%m-%dT%H:%M:%S"))})
            
            existed_reporting = list(ETaskReportingDates.objects.filter(task=task.id,owned_by=updated_by,
                                    reporting_date__date__in=reporting_date_dict.keys()).values_list('reporting_date__date',flat=True))
            
            existed_reporting = list(map(str,existed_reporting))
            final_reporting_dict = {k:v for k,v in reporting_date_dict.items() if k not in existed_reporting}

            if final_reporting_dict:
                for k,v in final_reporting_dict.items():
                    rdate_details, created = ETaskReportingDates.objects.get_or_create(
                        task_type=1,
                        task=task.id,
                        reporting_date=datetime.strptime(v, "%Y-%m-%dT%H:%M:%S"),
                        created_by=updated_by,
                        owned_by=updated_by
                    )
                    reporting_log, created = ETaskReportingActionLog.objects.get_or_create(
                        task_id=task.id,
                        reporting_date_id=str(rdate_details),
                        updated_date=datetime.now().date(),
                        status=2,
                        created_by=updated_by,
                        owned_by=updated_by
                    )
        
        return instance


class EtaskMassMarkAddReportingDateSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    #completed_status = serializers.CharField(default=serializers.CurrentUserDefault())
    reporting_date_ids = serializers.ListField()
    is_confirm = serializers.BooleanField(default=False)
    request_status = serializers.CharField(required=False)
    message = serializers.CharField(required=False)

    class Meta:
        model = ETaskReportingDates
        fields = '__all__'
        extra_fields = ('reporting_date_ids','is_confirm','request_status','message',)

    def previous_reporting_mark_as_reported(self, reporting_date_obj=None, current_datetime=None, updated_by=None):
        # date_of_reporting = current_datetime if current_datetime > reporting_date_obj.reporting_date else reporting_date_obj.reporting_date
        previous_reportings_query = ETaskReportingDates.objects.filter(task=reporting_date_obj.task,owned_by=reporting_date_obj.owned_by,
                                reporting_date__lt=reporting_date_obj.reporting_date)

        for reporting_objj in previous_reportings_query:
            prev_action = ETaskReportingActionLog.objects.filter(
                task_id=reporting_objj.task,
                reporting_date_id=reporting_objj.id,
                is_deleted=False
            ).update(is_deleted=True)
            reporting_log = ETaskReportingActionLog.objects.create(
                task_id=reporting_objj.task,
                reporting_date_id=reporting_objj.id,
                status=1,
                updated_by=updated_by
            )
        previous_reportings_query.update(task_type=1,reporting_status=1,
                                actual_reporting_date=current_datetime,updated_by=updated_by)

        return

    def create(self, validated_data):
        with transaction.atomic():
            current_date = datetime.now()
            # #print('current_date-->',current_date)
            updated_by = validated_data.get('updated_by')
            reporting_date_ids = validated_data.get('reporting_date_ids')
            is_confirm = validated_data.pop('is_confirm')

            success_list = list()
            error_list = list()
            reporting_obj_list = list()

            reporting_date_query = ETaskReportingDates.objects.filter(id__in=reporting_date_ids)

            for instance in reporting_date_query:
                task = EtaskTask.objects.get(id=instance.task)
                is_overdue = get_task_flag(task=task) == 'overdue'
                is_pending_exten = is_pending_extention(task=task)
                is_pending_close = is_pending_closer(task=task)

                if not is_overdue or (is_overdue and (is_pending_close or is_pending_exten)):
                    success_list.append(str(instance.reporting_date.date()))
                else:
                    error_list.append(str(instance.reporting_date.date()))

            if not error_list or is_confirm:
                for instance in reporting_date_query:
                    task = EtaskTask.objects.get(id=instance.task)
                    is_overdue = get_task_flag(task=task) == 'overdue'
                    is_pending_exten = is_pending_extention(task=task)
                    is_pending_close = is_pending_closer(task=task)

                    if not is_overdue or (is_overdue and (is_pending_close or is_pending_exten)):
                        instance.task_type = 1
                        instance.task_status=1
                        instance.reporting_status = 1
                        instance.actual_reporting_date = current_date
                        instance.updated_by = updated_by
                        instance.save()
                        prev_action= ETaskReportingActionLog.objects.filter(
                            task_id = instance.task,
                            reporting_date_id = instance.id,
                            is_deleted=False
                            ).update(is_deleted=True)
                        reporting_log = ETaskReportingActionLog.objects.create(
                            task_id = instance.task,
                            reporting_date_id = instance.id,
                            status = 1,
                            updated_by = updated_by
                            )

                        # previous reporting dates aumatic reported
                        self.previous_reporting_mark_as_reported(reporting_date_obj=instance, current_datetime=current_date,
                                                                 updated_by=updated_by)

                        if instance.owned_by == updated_by:
                            task = EtaskTask.objects.get(id=instance.task)
                            end_date = task.extended_date if task.extended_date else task.end_date
                            subassign_log = EtaskTaskSubAssignLog.objects.filter(task=task,assign_from=updated_by,is_deleted=False).first()
                            if subassign_log:
                                assign_to = subassign_log.sub_assign
                            else:
                                assign_to = task.assign_to

                            # Default Reporting Date will be added #
                            reporting_date_dict = {}
                            default_reporting_dates = EtaskMonthlyReportingDate.objects.filter(employee=assign_to,
                                                    owned_by=updated_by).values_list('field_value',flat=True)
                            for date_ob in daterange(task.start_date.date(),end_date.date()):
                                if date_ob.day in default_reporting_dates and date_ob >= current_date.date():
                                    default_reporting_date = EtaskMonthlyReportingDate.objects.filter(employee=assign_to,
                                                    field_value=date_ob.day,owned_by=updated_by).values('field_value','start_time').first()

                                    reporting_date_dict[str(date_ob)] = str(date_ob)+'T'+str(default_reporting_date['start_time']) if default_reporting_date['start_time'] else str(date_ob)+'T10:00:00'
                                    break

                            if reporting_date_dict:
                                reporting_date_dict.update({str(end_date.date()):str(end_date.replace(hour=10, minute=00).strftime("%Y-%m-%dT%H:%M:%S"))})

                            existed_reporting = list(ETaskReportingDates.objects.filter(task=task.id,owned_by=updated_by,
                                                    reporting_date__date__in=reporting_date_dict.keys()).values_list('reporting_date__date',flat=True))

                            existed_reporting = list(map(str,existed_reporting))
                            final_reporting_dict = {k:v for k,v in reporting_date_dict.items() if k not in existed_reporting}

                            if final_reporting_dict:
                                for k,v in final_reporting_dict.items():
                                    rdate_details, created = ETaskReportingDates.objects.get_or_create(
                                        task_type=1,
                                        task=task.id,
                                        reporting_date=datetime.strptime(v, "%Y-%m-%dT%H:%M:%S"),
                                        created_by=updated_by,
                                        owned_by=updated_by
                                    )
                                    reporting_log, created = ETaskReportingActionLog.objects.get_or_create(
                                        task_id=task.id,
                                        reporting_date_id=str(rdate_details),
                                        updated_date=datetime.now().date(),
                                        status=2,
                                        created_by=updated_by,
                                        owned_by=updated_by
                                    )

            error_msg = 'Following reporting date can not be mark as completed {}'.format(', '.join(set(error_list)))
            success_msg = 'Following reporting date has been mark as completed {}'.format(', '.join(set(success_list)))
            msg = ''
            if error_list and success_list:
                msg = '{} and {}.'.format(success_msg, error_msg)
            elif error_list and not success_list:
                msg = '{}.'.format(error_msg)
            elif not error_list and success_list:
                msg = '{}.'.format(success_msg)

            validated_data['request_status'] = 1 if not error_list or is_confirm else 0
            validated_data['message'] = msg
            return validated_data


############################################################################
class EtaskReportingDateShiftViewSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    shift_dates = serializers.ListField(required=False)
    class Meta:
        model = ETaskReportingDates
        fields = ('id','updated_by','shift_dates')
        # extra_fields = ('shift_date',)
    # def update(self,instance,validated_data):
    #     try:
    #         with transaction.atomic():
    #             #print('validated_data',validated_data.get('updated_by'))
    #             current_date=datetime.now().date()
    #             if instance.reporting_date.date()>current_date:
    #                 instance.reporting_date=validated_data.get('reporting_date')
    #                 instance.updated_by=validated_data.get('updated_by')
    #                 instance.save()
    #                 ETaskReportingActionLog.objects.filter(reporting_date=instance,is_deleted=False).update(updated_by_id=validated_data.get('updated_by'),is_deleted=True)
    #                 ETaskReportingActionLog.objects.create(reporting_date=instance,
    #                                                         status=2,
    #                                                         task_id=instance.task,
    #                                                         updated_date=datetime.now(),
    #                                                         updated_by=validated_data.get('updated_by')
    #                                                         )
    #             return instance.__dict__
    #     except Exception as e:
    #         raise e
    def create(self,validated_data):
        try:
            # #print('validated_data',validated_data)
            task_id=self.context['request'].query_params.get('task_id', None)
            # #print('task_id',task_id)
            shift_dates = validated_data.get('shift_dates')if 'shift_dates' in validated_data else ""
            updated_by = validated_data.get('updated_by')
            with transaction.atomic():
                # reporting_dates_details = ETaskReportingDates.objects.filter(task_type=1,task=task_id,is_deleted=False)
                # reporting_action_log=ETaskReportingActionLog.objects.filter(task_id=task_id,is_deleted=False)
                # if reporting_dates_details and reporting_action_log:
                #     reporting_dates_details.delete()
                #     reporting_action_log.delete()
                current_date=datetime.now().date()
                for r_dates in shift_dates:
                    reporting_date_create = ETaskReportingDates.objects.filter(id=r_dates['id'],
                                                                               task=task_id,
                                                                               task_type=1,
                                                                               is_deleted=False
                                                                                ).values('reporting_date','reporting_status','updated_by')
                                                                               
                    # #print('reporting_date_create',type(reporting_date_create[0]['reporting_status']))
                    if reporting_date_create[0]['reporting_date'].date() >= current_date and reporting_date_create[0]['reporting_status'] == 2:
                        reporting_date_create = ETaskReportingDates.objects.filter(id=r_dates['id'],
                                                                               task=task_id,
                                                                               task_type=1,
                                                                               is_deleted=False
                                                                                ).update(reporting_date=datetime.strptime(r_dates['reporting_date'], "%Y-%m-%dT%H:%M:%S.%fZ"),
                                                                                      updated_by=updated_by
                                                                                  ) 
                                                                                                                                                                                     
                        reporting_action_log=ETaskReportingActionLog.objects.filter(task_id=task_id,
                                                                                    reporting_date_id=r_dates['id'],
                                                                                    is_deleted=False
                                                                                    ).update(is_deleted=True, updated_by=updated_by)
                        reporting_action_log=ETaskReportingActionLog.objects.create(task_id=task_id,
                                                                                reporting_date_id=r_dates['id'],
                                                                                updated_date=datetime.now().date(),
                                                                                status=2,
                                                                                updated_by=updated_by
                                                                                )
                return validated_data
        except Exception as e:
            raise e
############################################################################
        
class ETaskAdminTaskReportSerializer(serializers.ModelSerializer):
    parent_task=serializers.SerializerMethodField(required=False)
    sub_data = EtaskTask.objects.filter(parent_id=0,is_deleted=False)
    task_type_name=serializers.CharField(source='get_task_type_display')
    recurrance_frequency_name=serializers.CharField(source='get_recurrance_frequency_display')
    task_status_name=serializers.CharField(source='get_task_status_display')
    assign_by_name = serializers.SerializerMethodField()
    assign_to_name= serializers.SerializerMethodField()
    sub_assign_to_user_name= serializers.SerializerMethodField()
    task_priority_name=serializers.CharField(source='get_task_priority_display')
    
    class Meta:
        model=EtaskTask
        fields='__all__'
    def get_parent_task(self,EtaskTask):
        parent_data = None
        if EtaskTask.parent_id:
            if EtaskTask.parent_id !=0:
                if self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject'):
                    task_details=self.sub_data.filter(id=EtaskTask.parent_id)
                    for t_d in task_details:
                        report_date=ETaskReportingDates.objects.filter(task_type=1,task=t_d.id,is_deleted=False).values('id','reporting_date')
                        reporting_date=report_date if report_date else []
                        assign_to=t_d.assign_to.id if t_d.assign_to else None
                        assign_by=t_d.assign_by.id if t_d.assign_by else None
                        sub_assign_to_user=t_d.sub_assign_to_user.id if t_d.sub_assign_to_user else None
                        owner=t_d.owner.id if t_d.owner else None
                        parent_data={
                            'id':t_d.id,
                            'task_code_id':t_d.task_code_id,
                            'parent_id':t_d.parent_id,
                            'owner':owner,
                            'owner_name':userdetails(owner),
                            'assign_to':assign_to,
                            'assign_to_name':userdetails(assign_to),
                            'assign_by':assign_by,
                            'assign_by_name':userdetails(assign_by),
                            'task_subject':t_d.task_subject,
                            'task_description':t_d.task_description,
                            'task_categories':t_d.task_categories,
                            'task_categories_name':t_d.get_task_categories_display(),
                            'start_date':t_d.start_date,
                            'end_date':t_d.end_date,
                            'completed_date':t_d.completed_date,
                            'closed_date':t_d.closed_date,
                            'extended_date':t_d.extended_date,
                            'extend_with_delay':t_d.extend_with_delay,
                            'task_priority':t_d.task_priority,
                            'task_priority_name':t_d.get_task_priority_display(),
                            'task_type':t_d.task_type,
                            'task_type_name':t_d.get_task_type_display(),
                            'task_status':t_d.task_status,
                            'task_status_name':t_d.get_task_status_display(),
                            'recurrance_frequency':t_d.recurrance_frequency,
                            'recurrance_frequency_name':t_d.get_recurrance_frequency_display(),
                            'sub_assign_to_user':sub_assign_to_user,
                            'sub_assign_to_user_name':userdetails(sub_assign_to_user),
                            'reporting_dates':reporting_date
                        } 
                        return parent_data
    def user_name(self, user_id):
        name = None
        full_name = ""
        name = User.objects.get(id=user_id)
        if name:
            full_name =  name.__dict__['first_name']+" "+name.__dict__['last_name']
        return full_name
    def get_assign_by_name(self,EtaskTask):
        name = None
        full_name = ""
        if EtaskTask.assign_by:
            name = User.objects.get(id=EtaskTask.assign_by.id)
            if name:
                full_name =  name.__dict__['first_name']+" "+name.__dict__['last_name']
                # #print("full_name",full_name)
            return full_name
    def get_sub_assign_to_user_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.sub_assign_to_user:
            name=User.objects.get(id=EtaskTask.sub_assign_to_user.id)
            if name:
                full_name= name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name

    def get_assign_to_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.assign_to:
            name =User.objects.get(id=EtaskTask.assign_to.id)
            if name:
                full_name=name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name

class ETaskAdminAppointmentReportSerializer(serializers.ModelSerializer):
    appointment_status_name=serializers.CharField(source='get_Appointment_status_display')
    class Meta:
        model=EtaskAppointment
        fields='__all__'

                
class ETaskAllCommentsSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    cost_details=serializers.ListField(required=False)
    other_details=serializers.ListField(required=False)
    id_tfa=serializers.IntegerField(required=False)
    
    class Meta:
        model=None
        fields='__all__'
        extra_fields=('cost_details','other_details')

    def create(self,validated_data):
        comment_section = self.context['request'].query_params.get('comment_section',None)
        #print(comment_section)
        if comment_section.lower() =='task':
            task = validated_data.pop('id_tfa')if 'id_tfa' in validated_data else ""
            cost_details=validated_data.pop('cost_details')if 'cost_details' in validated_data else ""
            other_details=validated_data.pop('other_details')if 'other_details' in validated_data else "" 
            created_by=validated_data.get('created_by')
            
            owned_by=validated_data.get('owned_by')
            cost_details_list=[]
            other_details_list=[]
            
            with transaction.atomic():
                #print("task",task)
                e_task_comments=ETaskComments.objects.create(task_id=task,**validated_data)

                #print("e_task_comments-->",e_task_comments)
                
                for c_d in cost_details:
                    cost_data=EtaskIncludeAdvanceCommentsCostDetails.objects.create(etcomments=e_task_comments,
                                                                                                **c_d,
                                                                                                created_by=created_by,
                                                                                                owned_by=owned_by
                                                                                                    )
                    cost_data.__dict__.pop('_state') if "_state" in cost_data.__dict__.keys() else cost_data.__dict__
                    cost_details_list.append(cost_data.__dict__)
                #print('cost_details_list-->',cost_details_list)

                for o_d in other_details:
                    others_data=EtaskIncludeAdvanceCommentsOtherDetails.objects.create(etcomments=e_task_comments,
                                                                                                    **o_d,
                                                                                                    created_by=created_by,
                                                                                                    owned_by=owned_by
                                                                                                    )
                    others_data.__dict__.pop('_state')if '_state' in others_data.__dict__.keys() else others_data.__dict__
                    other_details_list.append(others_data.__dict__)
                #print('other_details_list-->',other_details_list)

                e_task_comments.__dict__['cost_details']=cost_details_list
                e_task_comments.__dict__['other_details']=other_details_list

                # ============= Mail Send ============== #
                comment_save_send = self.context['request'].query_params.get('comment_save_send',None)
                # comments_detail = ETaskComments.objects.filter(task_id=task)
                # #print('comments_detail-->',comments_detail)
                assign_to_email = TCoreUserDetail.objects.filter(cu_user=EtaskTask.objects.only('assign_to').get(id=task).assign_to)
                #print('assign_to_email-->',assign_to_email)
                # email_list = []                

                if assign_to_email and comment_save_send == 'send':

                    #print('Email Send Process Started')

                    task_owner_email = list(set(TCoreUserDetail.objects.filter(cu_alt_email_id__isnull=False,cu_user=EtaskTask.objects.only('owner').get(id=task).assign_to
                                                                        ).values_list('cu_alt_email_id',flat=True)))
                    #print('task_owner_email-->',task_owner_email)
                    # task_owner_email = ['nuralam.islam@shyamfuture.com']      
                    task_cc_id_list =  list(set(EtaskUserCC.objects.filter(task=task,is_deleted=False).values_list('user',flat=True)))
                    #print('task_cc_id_list-->',task_cc_id_list)
                    
                    task_cc_list = []
                    for u_list in task_cc_id_list:
                        user_id = TCoreUserDetail.objects.filter(cu_alt_email_id__isnull=False,cu_user=u_list,cu_is_deleted=False).values('cu_alt_email_id')
                        # #print('user_id-->',user_id[0]['cu_alt_email_id'])
                        task_cc_list.append(user_id[0]['cu_alt_email_id'])

                    #print('task_cc_list-->',task_cc_list)

                    commented_by = userdetails(created_by.id)
                    comment_subject = validated_data['comments']
                    
                    email = list(set(assign_to_email.values_list('cu_alt_email_id',flat=True)))
                    #print('email-->',email)
                    email_list = task_owner_email + email + task_cc_list
                    #print('task_owner_email-->',email_list)
                    # full_name = EtaskTask.objects.only('assign_to_id').get(id=task).assign_to_id
                    full_name = userdetails(EtaskTask.objects.only('assign_to_id').get(id=task).assign_to_id)
                    #print('full_name-->',full_name)

                    ###### Main mail Send Block ######

                    if email_list:
                        mail_data = {
                                    "name": full_name,
                                    "comment_sub": comment_subject,
                                    "commented_by": commented_by
                            }
                        #print('mail_data',mail_data)
                        # mail_class = GlobleMailSend('ET-COMMENT', email_list)
                        # mail_thread = Thread(target = mail_class.mailsend, args = (mail_data,))
                        # mail_thread.start()
                        send_mail_list('ET-COMMENT', email_list, mail_data, ics='')
                    #################################

                return e_task_comments

        elif comment_section.lower() =='followup':
            #print("validated_data",validated_data)
            followup = validated_data.pop('id_tfa') if 'id_tfa' in validated_data else ""
            cost_details=validated_data.pop('cost_details')if 'cost_details' in validated_data else ""
            other_details=validated_data.pop('other_details')if 'other_details' in validated_data else "" 
            
            #print("followup",followup)
            created_by=validated_data.get('created_by')
            owned_by=validated_data.get('owned_by')
            cost_details_list=[]
            other_details_list=[]
            
            with transaction.atomic():
                #print("entered")
                followup_comments=FollowupComments.objects.create(followup_id=followup,**validated_data)

                # #print("followup_comments-->",followup_comments)
                
                for c_d in cost_details:
                    cost_data=FollowupIncludeAdvanceCommentsCostDetails.objects.create(flcomments=followup_comments,
                                                                                                **c_d,
                                                                                                created_by=created_by,
                                                                                                owned_by=owned_by
                                                                                                    )
                    cost_data.__dict__.pop('_state') if "_state" in cost_data.__dict__.keys() else cost_data.__dict__
                    cost_details_list.append(cost_data.__dict__)
                # #print('cost_details_list-->',cost_details_list)

                for o_d in other_details:
                    others_data=FollowupIncludeAdvanceCommentsOtherDetails.objects.create(flcomments=followup_comments,
                                                                                                    **o_d,
                                                                                                    created_by=created_by,
                                                                                                    owned_by=owned_by
                                                                                                    )
                    others_data.__dict__.pop('_state')if '_state' in others_data.__dict__.keys() else others_data.__dict__
                    other_details_list.append(others_data.__dict__)
                # #print('other_details_list-->',other_details_list)

                followup_comments.__dict__['cost_details']=cost_details_list
                followup_comments.__dict__['other_details']=other_details_list
                return followup_comments
        
        elif comment_section.lower() =='appointment':
            try:
                #print("val",validated_data)
                appointment = validated_data.pop('id_tfa') if 'id_tfa' in validated_data else ""
                cost_details=validated_data.pop('cost_details')if 'cost_details' in validated_data else ""
                other_details=validated_data.pop('other_details')if 'other_details' in validated_data else "" 
                created_by=validated_data.get('created_by')
                owned_by=validated_data.get('owned_by')
                cost_details_list=[]
                other_details_list=[]
                
                with transaction.atomic():
                    
                    appointment_comments=AppointmentComments.objects.create(appointment_id=appointment,**validated_data)

                    #print("appointment_comments-->",appointment_comments.__dict__)
                    appointment_subject=EtaskAppointment.objects.only('appointment_subject').get(id=appointment,is_deleted=False).appointment_subject
                    
                    for c_d in cost_details:
                        cost_data=AppointmentIncludeAdvanceCommentsCostDetails.objects.create(apcomments=appointment_comments,
                                                                                                    **c_d,
                                                                                                    created_by=created_by,
                                                                                                    owned_by=owned_by
                                                                                                        )
                        cost_data.__dict__.pop('_state') if "_state" in cost_data.__dict__.keys() else cost_data.__dict__
                        cost_details_list.append(cost_data.__dict__)
                    # #print('cost_details_list-->',cost_details_list)

                    for o_d in other_details:
                        others_data=AppointmentIncludeAdvanceCommentsOtherDetails.objects.create(apcomments=appointment_comments,
                                                                                                        **o_d,
                                                                                                        created_by=created_by,
                                                                                                        owned_by=owned_by
                                                                                                        )
                        others_data.__dict__.pop('_state')if '_state' in others_data.__dict__.keys() else others_data.__dict__
                        other_details_list.append(others_data.__dict__)
                    # #print('other_details_list-->',other_details_list)

                    appointment_comments.__dict__['cost_details']=cost_details_list
                    appointment_comments.__dict__['other_details']=other_details_list

                    # ============= Mail Send ============== # 
                    comment_save_send = self.context['request'].query_params.get('comment_save_send',None)
                    if comment_save_send == 'send':

                        internal_invites = EtaskInviteEmployee.objects.filter((Q(user__email__isnull=False) & ~Q(user__email="")),
                                                    appointment_id=appointment).values_list('user__cu_user__cu_alt_email_id',flat=True)
                        #print('internal_invites',internal_invites)
                        external_invites = EtaskInviteExternalPeople.objects.filter((Q(external_email__isnull=False) & ~Q(external_email=""))
                                                                ,appointment_id=appointment).values_list('external_email',flat=True)
                        #print('external_invites',external_invites)
                        total_emailid = list(set(list(internal_invites)+list(external_invites)))

                        if total_emailid:
                            mail_data = {
                                    "appointment_subject":appointment_subject,
                                    "appointment_comment":appointment_comments.__dict__['comments']
                                   
                            }
                            # if appointment_comments.__dict__['advance_comment'] == True:
                            #     mail_data["cost_details"]=cost_data.__dict__['cost_details']
                            #     mail_data["cost"]=cost_data.__dict__['cost']
                            #     mail_data["other_details"]=others_data.__dict__['other_details']
                            #     mail_data["value"]=others_data.__dict__['value']

                            #print('mail_data',mail_data)
                            # mail_class = GlobleMailSend('ET-APPONTMANET-COMMENT', total_emailid)
                            # mail_thread = Thread(target = mail_class.mailsend, args = (mail_data,))
                            # mail_thread.start()
                            send_mail_list('ET-APPONTMANET-COMMENT', total_emailid, mail_data, ics='')
                    return appointment_comments
                
            except Exception as e:
                raise e
       

class ETaskAllCommentsDocumentSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())    
    class Meta:
        model=None
        fields='__all__'

class ETaskAppointmentCancelSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = EtaskAppointment
        fields = '__all__'
    def update(self, instance, validated_data):
        cancelling_user = self.context['request'].user.first_name + " " +  self.context['request'].user.last_name
        internal_invites = EtaskInviteEmployee.objects.filter((Q(user__cu_user__cu_alt_email_id__isnull=False) & ~Q(user__cu_user__cu_alt_email_idl="")),
                                                    appointment=instance.id).values_list('user__cu_user__cu_alt_email_id',flat=True)
        external_invites = EtaskInviteExternalPeople.objects.filter((Q(external_email__isnull=False) & ~Q(external_email=""))
                                                ,appointment=instance.id).values_list('external_email',flat=True)
        total_cancle_emailid = list(set(list(internal_invites)+list(external_invites)))
        
        #update section 
        # EtaskInviteEmployee.objects.filter(appointment=instance.id).update(is_deleted=True)
        # EtaskInviteExternalPeople.objects.filter(appointment=instance.id).update(is_deleted=True)
        instance.Appointment_status = 'cancelled'
        # instance.is_deleted = True
        instance.save()




        # etask_appointment_creator = EtaskAppointment.objects.filter(id=instance.id,Appointment_status='ongoing',is_deleted=False)

        # #print('etask_appointment_creator-->',etask_appointment_creator)

        # if etask_appointment_creator :            

        #     #print('Email Send Process Started')

                        
        #     appintment_owner_email = list(set(TCoreUserDetail.objects.filter(cu_user__in=etask_appointment_creator.values_list('created_by',flat=True)
        #                                                                     ).values_list('cu_alt_email_id',flat=True)))
            
        #     # list(set(TCoreUserDetail.objects.filter(cu_alt_email_id__isnull=False,
        #     #                                         cu_user__in=TCoreUserDetail.objects.filter(cu_user=EtaskTask.objects.only('assign_by').get(id=task).assign_to
        #     #                                                     ).values_list('reporting_head',flat=True)).values_list('cu_alt_email_id',flat=True)))
        #     #print('appintment_owner_email-->',appintment_owner_email)
        #     # task_owner_email = ['nuralam.islam@shyamfuture.com']    

        #     # etask_invite_employee_list = EtaskInviteEmployee.objects.filter(appointment=instance,is_deleted=False)
        #     # #print('etask_invite_employee_list-->',etask_invite_employee_list)  
        #     invited_employee_list =  list(set(EtaskInviteEmployee.objects.filter(appointment=instance,is_deleted=False).values_list('user',flat=True)))
        #     #print('invited_employee_list-->',invited_employee_list)
        #     task_cc_list = []
        #     if invited_employee_list:
        #         for u_list in invited_employee_list:
        #             user_id = TCoreUserDetail.objects.filter(cu_user=u_list,cu_is_deleted=False).values('cu_alt_email_id')
        #             # #print('user_id-->',user_id[0]['cu_alt_email_id'])
        #             task_cc_list.append(user_id[0]['cu_alt_email_id'])

        #         #print('task_cc_list-->',task_cc_list)
            
        #     etask_invite_external_people = EtaskInviteExternalPeople.objects.filter(appointment=instance,is_deleted=False)
        #     etask_invite_external_people_list = []
        #     if etask_invite_external_people:
        #         etask_invite_external_people_list = list(set(etask_invite_external_people.values_list('external_email',flat=True)))

        #     # cancelled_by = userdetails(created_by.id)
        #     # comment_subject = validated_data['comments']

        #     email_list = task_owner_email + task_cc_list + etask_invite_external_people_list
        #     #print('task_owner_email-->',email_list)
        #     # full_name = EtaskTask.objects.only('assign_to_id').get(id=task).assign_to_id
        #     # full_name = userdetails(EtaskTask.objects.only('assign_to_id').get(id=task).assign_to_id)
        #     # #print('full_name-->',full_name)

        #     ###### Main mail Send Block ######

        if total_cancle_emailid:
            mail_data = {
                        "appointment_subject":instance.appointment_subject,
                        "cancelled_by": cancelling_user
                }
            #print('mail_data',mail_data)
            # mail_class = GlobleMailSend('ET-APPONTMANET-CANCEL', total_cancle_emailid)
            # mail_thread = Thread(target = mail_class.mailsend, args = (mail_data,))
            # mail_thread.start()
            send_mail_list('ET-APPONTMANET-CANCEL', total_cancle_emailid, mail_data, ics='')
        #################################


        return instance


class ETaskAppointmentCancelSerializerV2(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = EtaskAppointment
        fields = '__all__'
    def update(self, instance, validated_data):
        cancelling_user = self.context['request'].user.get_full_name()
        internal_invites = EtaskInviteEmployee.objects.filter((Q(user__cu_user__cu_alt_email_id__isnull=False) & ~Q(user__cu_user__cu_alt_email_id="")),
                                                    appointment=instance.id).values_list('user__cu_user__cu_alt_email_id',flat=True)
        external_invites = EtaskInviteExternalPeople.objects.filter((Q(external_email__isnull=False) & ~Q(external_email=""))
                                                ,appointment=instance.id).values_list('external_email',flat=True)
        total_cancle_emailid = list(set(list(internal_invites)+list(external_invites)))
        
        instance.Appointment_status = 'cancelled'
        instance.save()
        internal_query =EtaskInviteEmployee.objects.filter((Q(user__cu_user__cu_alt_email_id__isnull=False) & ~Q(user__cu_user__cu_alt_email_id="")),
                                                    appointment=instance.id)
        internal_list = [{'name':internal.user.get_full_name(),'email':internal.user.cu_user.cu_alt_email_id} for internal in internal_query]
        external_query = EtaskInviteExternalPeople.objects.filter((Q(external_email__isnull=False) & ~Q(external_email=""))
                                                ,appointment=instance.id)
        external_list = [{'name':external.external_people,'email':external.external_email} for external in external_query]
        total_cancel_mail_list = internal_list + external_list

        
        if total_cancel_mail_list:
            for cancel_mail in total_cancel_mail_list:
                mail_data = {
                                "recipient_name" : cancel_mail['name'],
                                "appointment_subject":instance.appointment_subject,
                                "facilitator_name": instance.owned_by.get_full_name(),
                                "location":instance.location,
                                "start_date":instance.start_date.date(),
                                "end_date":instance.end_date.date(),
                                "start_time":instance.start_time,
                                "end_time":instance.end_time,
                                "cancelled_by":cancelling_user
                            }
                #print('mail_data',mail_data)
                # mail_class = GlobleMailSend('ET-APPONTMANET-CANCEL', [cancel_mail['email']])
                # mail_thread = Thread(target = mail_class.mailsend, args = (mail_data,))
                # mail_thread.start()
                send_mail_list('ET-APPONTMANET-CANCEL', [cancel_mail['email']], mail_data,ics='')
        #################################

        internal_invites_user = EtaskInviteEmployee.objects.filter(
                        appointment=instance.id)
        users = [etii.user for etii in internal_invites_user]
        title = 'Your Appointment on {} has been canceled.'.format(instance.start_date.date())
        body ='Appointment: {} \nLocation:{}'.format(instance.appointment_subject,instance.location)

        data = {
                    "app_module":"etask",
                    "type":"task",
                    "id":instance.id
                }
        data_str = json.dumps(data)
        notification_id = store_sent_notification(users=users,body=body,title=title,data=data_str,app_module_name='etask')
        send_notification(users=users,body=body,title=title,data=data,notification_id=notification_id)


        return instance


class ETaskTeamOngoingTaskSerializer(serializers.ModelSerializer):
    parent_task=serializers.SerializerMethodField(required=False)
    sub_data = EtaskTask.objects.filter(parent_id=0,is_deleted=False)
    assign_to_name= serializers.SerializerMethodField()
    sub_assign_to_user_name= serializers.SerializerMethodField()
    class Meta:
        model=EtaskTask
        # fields='__all__' ## Modified By Manas Paul and below fields also.
        fields = ('id','parent_id','task_subject','task_description','start_date','end_date','task_status','completed_date','task_priority','extend_with_delay',
                    'task_code_id','closed_date','extended_date','assign_by','assign_to','sub_assign_to_user','get_task_status_display',
                    'sub_assign_to_user_name','parent_task','assign_to_name','sub_assign_to_user_name')
    def get_parent_task(self,EtaskTask):
        if EtaskTask.parent_id:
            if EtaskTask.parent_id !=0:
                if self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject'):
                    parent_data=self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject')[0]
                    return parent_data
    def user_name(self, user_id):
        name = None
        full_name = ""
        name = User.objects.get(id=user_id)
        if name:
            full_name =  name.__dict__['first_name']+" "+name.__dict__['last_name']
        return full_name
    def get_assign_to_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.assign_to:
            name =User.objects.get(id=EtaskTask.assign_to.id)
            if name:
                full_name=name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name
    def get_sub_assign_to_user_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.sub_assign_to_user:
            name=User.objects.get(id=EtaskTask.sub_assign_to_user.id)
            if name:
                full_name= name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name
class ETaskTeamCompletedTaskSerializer(serializers.ModelSerializer):
    parent_task=serializers.SerializerMethodField(required=False)
    sub_data = EtaskTask.objects.filter(parent_id=0,is_deleted=False)
    assign_to_name= serializers.SerializerMethodField()
    sub_assign_to_user_name= serializers.SerializerMethodField()
    class Meta:
        model=EtaskTask
        fields='__all__'
    def get_parent_task(self,EtaskTask):
        if EtaskTask.parent_id:
            if EtaskTask.parent_id !=0:
                if self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject'):
                    parent_data=self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject')[0]
                    return parent_data
    def user_name(self, user_id):
        name = None
        full_name = ""
        name = User.objects.get(id=user_id)
        if name:
            full_name =  name.__dict__['first_name']+" "+name.__dict__['last_name']
        return full_name
    def get_assign_to_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.assign_to:
            name =User.objects.get(id=EtaskTask.assign_to.id)
            if name:
                full_name=name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name
    def get_sub_assign_to_user_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.sub_assign_to_user:
            name=User.objects.get(id=EtaskTask.sub_assign_to_user.id)
            if name:
                full_name= name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name


class ETaskTeamClosedTaskSerializer(serializers.ModelSerializer):
    parent_task=serializers.SerializerMethodField(required=False)
    sub_data = EtaskTask.objects.filter(parent_id=0,is_deleted=False)
    assign_to_name= serializers.SerializerMethodField()
    sub_assign_to_user_name= serializers.SerializerMethodField()
    reporting_dates=serializers.SerializerMethodField()
    task_priority_name=serializers.CharField(source='get_task_priority_display')
    class Meta:
        model=EtaskTask
        fields='__all__'
    def get_parent_task(self,EtaskTask):
        if EtaskTask.parent_id:
            if EtaskTask.parent_id !=0:
                if self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject','task_description'):
                    parent_data=self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject','task_description')[0]
                    return parent_data
    def user_name(self, user_id):
        name = None
        full_name = ""
        name = User.objects.get(id=user_id)
        if name:
            full_name =  name.__dict__['first_name']+" "+name.__dict__['last_name']
        return full_name
    def get_assign_to_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.assign_to:
            name =User.objects.get(id=EtaskTask.assign_to.id)
            if name:
                full_name=name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name
    def get_sub_assign_to_user_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.sub_assign_to_user:
            name=User.objects.get(id=EtaskTask.sub_assign_to_user.id)
            if name:
                full_name= name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name
    def get_reporting_dates(self,EtaskTask):
        if EtaskTask.id:
            report_date_list = []
            report_date=ETaskReportingDates.objects.filter(task_type=1,task=EtaskTask.id,is_deleted=False)
            # #print("report_date",report_date)
            if report_date:
                for dt in report_date:
                    dt_dict={
                        'id':dt.id,
                        'reporting_date':dt.reporting_date,
                        'reporting_status':dt.reporting_status,
                        'reporting_status_name':dt.get_reporting_status_display()
                       
                    }
                    report_date_list.append(dt_dict)
                                   
                return report_date_list
            else:
                return []


class ETaskTeamClosedTaskSerializerV2(serializers.ModelSerializer):
    parent_task=serializers.SerializerMethodField(required=False)
    sub_data = EtaskTask.objects.filter(parent_id=0,is_deleted=False)
    assign_to_name= serializers.SerializerMethodField()
    sub_assign_to_user_name= serializers.SerializerMethodField()
    reporting_dates=serializers.SerializerMethodField()
    task_priority_name=serializers.CharField(source='get_task_priority_display')
    user_cc=serializers.SerializerMethodField()
    sub_tasks = serializers.SerializerMethodField()

    class Meta:
        model=EtaskTask
        fields='__all__'
        extra_fields = ('user_cc','sub_tasks')

    def get_sub_tasks(self, obj):
        sub_tasks_data = EtaskTask.objects.filter(~Q(task_status=4),parent_id=obj.id,is_deleted=False).values('id','task_subject')
        return sub_tasks_data if sub_tasks_data else list() 

    def get_user_cc(self, obj):
        user_cc=EtaskUserCC.objects.filter(task=obj,is_deleted=False).values('id','user__first_name', 'user__last_name')
        return user_cc if user_cc else list()

    def get_parent_task(self,EtaskTask):
        if EtaskTask.parent_id:
            if EtaskTask.parent_id !=0:
                if self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject','task_description'):
                    parent_data=self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject','task_description')[0]
                    return parent_data
    def user_name(self, user_id):
        name = None
        full_name = ""
        name = User.objects.get(id=user_id)
        if name:
            full_name =  name.__dict__['first_name']+" "+name.__dict__['last_name']
        return full_name
    def get_assign_to_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.assign_to:
            name =User.objects.get(id=EtaskTask.assign_to.id)
            if name:
                full_name=name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name
    def get_sub_assign_to_user_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.sub_assign_to_user:
            name=User.objects.get(id=EtaskTask.sub_assign_to_user.id)
            if name:
                full_name= name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name
    def get_reporting_dates(self,EtaskTask):
        if EtaskTask.id:
            report_date_list = []
            report_date=ETaskReportingDates.objects.filter(task_type=1,task=EtaskTask.id,is_deleted=False).order_by('reporting_date')
            # #print("report_date",report_date)
            if report_date:
                for dt in report_date:
                    dt_dict={
                        'id':dt.id,
                        'reporting_date':dt.reporting_date,
                        'reporting_status':dt.reporting_status,
                        'reporting_status_name':dt.get_reporting_status_display()
                       
                    }
                    report_date_list.append(dt_dict)
                                   
                return report_date_list
            else:
                return []


class ETaskTeamClosedTaskDownloadSerializerV2(serializers.ModelSerializer):
    parent_task=serializers.SerializerMethodField(required=False)
    sub_data = EtaskTask.objects.filter(parent_id=0,is_deleted=False)
    assign_to_name= serializers.SerializerMethodField()
    sub_assign_to_user_name= serializers.SerializerMethodField()
    reporting_dates=serializers.SerializerMethodField()
    task_priority_name=serializers.CharField(source='get_task_priority_display')
    start_date = serializers.SerializerMethodField(required=False)
    end_date = serializers.SerializerMethodField(required=False)
    completed_date = serializers.SerializerMethodField(required=False)

    class Meta:
        model=EtaskTask
        fields='__all__'

    def get_start_date(self, obj):
        return obj.start_date.strftime("%d %b %Y") if obj.start_date else ''

    def get_end_date(self, obj):
        return obj.end_date.strftime("%d %b %Y") if obj.end_date else ''

    def get_completed_date(self, obj):
        return obj.completed_date.strftime("%d %b %Y") if obj.completed_date else ''

    def get_parent_task(self,EtaskTask):
        if EtaskTask.parent_id:
            if EtaskTask.parent_id !=0:
                if self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject','task_description'):
                    parent_data=self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject','task_description')[0]
                    return parent_data
    def user_name(self, user_id):
        name = None
        full_name = ""
        name = User.objects.get(id=user_id)
        if name:
            full_name =  name.__dict__['first_name']+" "+name.__dict__['last_name']
        return full_name
    def get_assign_to_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.assign_to:
            name =User.objects.get(id=EtaskTask.assign_to.id)
            if name:
                full_name=name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name
    def get_sub_assign_to_user_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.sub_assign_to_user:
            name=User.objects.get(id=EtaskTask.sub_assign_to_user.id)
            if name:
                full_name= name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name
    def get_reporting_dates(self,EtaskTask):
        if EtaskTask.id:
            report_date_list = []
            report_date=ETaskReportingDates.objects.filter(task_type=1,task=EtaskTask.id,is_deleted=False).order_by('reporting_date')
            # #print("report_date",report_date)
            if report_date:
                for dt in report_date:
                    dt_dict={
                        'id':dt.id,
                        'reporting_date':dt.reporting_date,
                        'reporting_status':dt.reporting_status,
                        'reporting_status_name':dt.get_reporting_status_display()
                       
                    }
                    report_date_list.append(dt_dict)
                                   
                return report_date_list
            else:
                return []


class ETaskTeamOverdueTaskSerializer(serializers.ModelSerializer):
    parent_task=serializers.SerializerMethodField(required=False)
    sub_data = EtaskTask.objects.filter(parent_id=0,is_deleted=False)
    assign_to_name= serializers.SerializerMethodField()
    sub_assign_to_user_name= serializers.SerializerMethodField()
    class Meta:
        model=EtaskTask
        fields='__all__'
    def get_parent_task(self,EtaskTask):
        if EtaskTask.parent_id:
            if EtaskTask.parent_id !=0:
                if self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject'):
                    parent_data=self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject')[0]
                    return parent_data
    def user_name(self, user_id):
        name = None
        full_name = ""
        name = User.objects.get(id=user_id)
        if name:
            full_name =  name.__dict__['first_name']+" "+name.__dict__['last_name']
        return full_name
    def get_assign_to_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.assign_to:
            name =User.objects.get(id=EtaskTask.assign_to.id)
            if name:
                full_name=name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name
    def get_sub_assign_to_user_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.sub_assign_to_user:
            name=User.objects.get(id=EtaskTask.sub_assign_to_user.id)
            if name:
                full_name= name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name

class ETaskGetDetailsCommentsSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    
    class Meta:
        model=None
        fields='__all__'


class EtaskTaskCloseSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = EtaskTask
        fields = '__all__'
    def update(self, instance, validated_data):
        current_date = datetime.now()
        updated_by = validated_data.get('updated_by')
        instance.task_status=4
        # instance.is_closure=True
        instance.closed_date = current_date
        instance.updated_by = updated_by
        instance.save()
        return instance


class EtaskTaskCloseSerializerV2(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = EtaskTask
        fields = '__all__'
    def update(self, instance, validated_data):
        with transaction.atomic():
            current_date = datetime.now()
            updated_by = validated_data.get('updated_by')
            instance.task_status=4
            # instance.is_closure=True
            instance.closed_date = current_date
            instance.updated_by = updated_by
            instance.save()

            ETaskCommentsViewers.objects.filter(task=instance,is_view=False,is_deleted=False).update(is_view=True)
            task_complete_reopen, is_created = TaskCompleteReopenMap.objects.get_or_create(task=instance,status=1)
            task_complete_reopen.status = 2
            task_complete_reopen.approved_date = current_date
            task_complete_reopen.approved_by = updated_by
            task_complete_reopen.updated_by = updated_by
            task_complete_reopen.updated_at = current_date
            task_complete_reopen.save()

            users = [instance.assign_to] if not instance.sub_assign_to_user else [instance.sub_assign_to_user]
            title = 'The task with task_code {} has been closed.'.format(instance.task_code_id)
            body ='Task: {} \nDetails:{}'.format(instance.task_subject,instance.task_description)

            data = {
                        "app_module":"etask",
                        "type":"task",
                        "id":instance.id
                    }
            data_str = json.dumps(data)
            notification_id = store_sent_notification(users=users,body=body,title=title,data=data_str,app_module_name='etask')
            send_notification(users=users,body=body,title=title,data=data,notification_id=notification_id)

            return instance


class ETaskMassTaskCloseSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    closed_task=serializers.ListField(required=False)
    class Meta:
        model = EtaskTask
        fields = ('id','updated_by','closed_task')
    def create(self,validated_data):
        try:
            updated_by = validated_data.get('updated_by')
            # #print('closed_task', validated_data.get('closed_task'))
            for data in validated_data.get('closed_task'):
                cur_date =datetime.now()
                all_closed_task = EtaskTask.objects.filter(id=data['id'],is_deleted=False).update(task_status=4,
                                                                        updated_by=updated_by,closed_date=cur_date)
                
            return validated_data
        except Exception as e:
            raise e


class ETaskMassTaskCloseSerializerV2(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    closed_task=serializers.ListField(required=False)
    is_confirm = serializers.BooleanField(default=False)
    request_status = serializers.CharField(required=False)
    message = serializers.CharField(required=False)

    class Meta:
        model = EtaskTask
        fields = ('id','updated_by','closed_task','is_confirm','request_status','message',)
    def create(self,validated_data):
        with transaction.atomic():
            updated_by = validated_data.get('updated_by')
            closed_task_ids = validated_data.get('closed_task',[])
            is_confirm = validated_data.pop('is_confirm')

            success_list = list()
            error_list = list()


            cur_date =datetime.now()
            all_closed_task = EtaskTask.objects.filter(id__in=closed_task_ids,is_deleted=False)
            # all_closed_task.update(task_status=4,updated_by=updated_by,closed_date=cur_date)

            for task in all_closed_task:
                is_pennding_closer = TaskCompleteReopenMap.objects.filter(task=task,status=1).count()
                if updated_by == task.owner and is_pennding_closer:
                    success_list.append(task.task_code_id)
                else:
                    error_list.append(task.task_code_id)
            #print('success_list',success_list)
            #print('error_list',error_list)
            if not error_list or is_confirm:
                for task in all_closed_task:
                    is_pennding_closer = TaskCompleteReopenMap.objects.filter(task=task,status=1).count()
                    #print('is_pennding_closer',is_pennding_closer)
                    #print('updated_by == task.owner',updated_by == task.owner)
                    if updated_by == task.owner and is_pennding_closer:
                        task.task_status = 4
                        task.updated_by = updated_by
                        task.closed_date = cur_date
                        task.save()

                        ETaskCommentsViewers.objects.filter(task=task,is_view=False,is_deleted=False).update(is_view=True)
                        task_complete_reopen, is_created = TaskCompleteReopenMap.objects.get_or_create(task=task,status=1)
                        task_complete_reopen.status = 2
                        task_complete_reopen.approved_date = cur_date
                        task_complete_reopen.approved_by = updated_by
                        task_complete_reopen.updated_by = updated_by
                        task_complete_reopen.updated_at = cur_date
                        task_complete_reopen.save()

                        users = [task.assign_to] if not task.sub_assign_to_user else [task.sub_assign_to_user]
                        title = 'The task with task_code {} has been closed.'.format(task.task_code_id)
                        body ='Task: {} \nDetails:{}'.format(task.task_subject,task.task_description)

                        data = {
                                    "app_module":"etask",
                                    "type":"task",
                                    "id":task.id
                                }
                        data_str = json.dumps(data)
                        notification_id = store_sent_notification(users=users,body=body,title=title,data=data_str,app_module_name='etask')
                        send_notification(users=users,body=body,title=title,data=data,notification_id=notification_id)
        
            error_msg = 'Task with task_code {} can not be closed'.format(', '.join(error_list))
            success_msg = 'Task with task_code {} has been closed'.format(', '.join(success_list))
            msg = ''
            if error_list and success_list:
                msg = '{} and {}.'.format(success_msg,error_msg)
            elif error_list and not success_list:
                msg = '{}.'.format(error_msg)
            elif not error_list and success_list:
                msg = '{}.'.format(success_msg)
                
            validated_data['request_status'] = 1 if not error_list or is_confirm else 0
            validated_data['message'] = msg
            return validated_data


class EmployeeListWithoutDetailsForETaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields=('id','first_name','last_name')

class UsersUnderReportingHeadSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields=('id','first_name','last_name')



class UsersReportingHeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields=('id','first_name','last_name')


class UsersForEtaskFilterSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields=('id','first_name','last_name')


class UsersForCCFilterSerializer(serializers.ModelSerializer):
    count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields=('id','first_name','last_name', 'count')

    def get_count(self, obj):
        cur_date = datetime.now().date()
        user = self.context.get("user")
        list_for = self.context.get("list_for")
        users_under_reporting_head = get_users_under_reporting_head(user=user)

        count = 0
        if list_for == 'team_ongoing_task_cc_to':
            sub_assign_tasks = list(EtaskTaskSubAssignLog.objects.filter(assign_from=user,
                sub_assign__in=users_under_reporting_head,is_deleted=False).values_list('task__id',flat=True))
            all_ongoing_tasks = list(EtaskTask.objects.filter(
                (Q(assign_by=user)&Q(assign_to__in=users_under_reporting_head))|Q(id__in=sub_assign_tasks),
                Q(start_date__date__lte=cur_date),
                (Q(Q(extended_date__isnull=False) & Q(extended_date__date__gte=cur_date))
                |Q(Q(extended_date__isnull=True) & Q(end_date__date__gte=cur_date))),
                Q(task_status=1)|Q(task_status=2)).values_list('id', flat=True))
            count = EtaskUserCC.objects.filter(task_id__in=all_ongoing_tasks, user=obj, is_deleted=False).count()

        elif list_for == 'team_upcoming_task_cc_to':
            sub_assign_tasks = list(EtaskTaskSubAssignLog.objects.filter(assign_from=user,
                sub_assign__in=users_under_reporting_head, is_deleted=False).values_list('task__id', flat=True))
            upcoming_tasks = list(EtaskTask.objects.filter(
                (Q(assign_by=user) & Q(assign_to__in=users_under_reporting_head)) | Q(id__in=sub_assign_tasks),
                Q(start_date__date__gt=cur_date), task_status=1).values_list('id', flat=True))
            count = EtaskUserCC.objects.filter(task_id__in=upcoming_tasks, user=obj, is_deleted=False).count()

        elif list_for == 'team_overdue_task_cc_to':
            sub_assign_tasks = list(EtaskTaskSubAssignLog.objects.filter(assign_from=user,
                sub_assign__in=users_under_reporting_head, is_deleted=False).values_list('task__id', flat=True))

            all_overdue_tasks = list(EtaskTask.objects.filter(
                (Q(assign_by=user) & Q(assign_to__in=users_under_reporting_head)) | Q(id__in=sub_assign_tasks),
                (Q(Q(extended_date__isnull=False) & Q(extended_date__date__lt=cur_date))
                 | Q(Q(extended_date__isnull=True) & Q(end_date__date__lt=cur_date))),
                Q(task_status=1) | Q(task_status=2)).values_list('id', flat=True))

            count = EtaskUserCC.objects.filter(task_id__in=all_overdue_tasks, user=obj, is_deleted=False).count()

        elif list_for == 'team_overdue_reporting_cc_to':
            sub_assign_tasks_team = list(EtaskTaskSubAssignLog.objects.filter(assign_from=user,
                    sub_assign__in=users_under_reporting_head, is_deleted=False).values_list('task__id', flat=True))
            team_overdue_reporting = (ETaskReportingDates.objects.filter(owned_by=user, task_type=1, reporting_status=2,
                    reporting_date__date__lt=cur_date, task__in=list(EtaskTask.objects.filter(
                    (Q(assign_by=user) & Q(assign_to__in=users_under_reporting_head)) | Q(id__in=sub_assign_tasks_team),
                    task_status=1, is_deleted=False).values_list('id', flat=True))).values_list('task',flat=True))
            count = EtaskUserCC.objects.filter(task_id__in=team_overdue_reporting, user=obj, is_deleted=False).count()

        elif list_for == 'team_today_reporting_cc_to':
            sub_assign_tasks_team = list(EtaskTaskSubAssignLog.objects.filter(assign_from=user,
                    sub_assign__in=users_under_reporting_head, is_deleted=False).values_list('task__id', flat=True))
            team_today_reporting = list(ETaskReportingDates.objects.filter(owned_by=user, task_type=1, reporting_status=2,
                    reporting_date__date=cur_date, task__in=list(EtaskTask.objects.filter(
                    (Q(assign_by=user) & Q(assign_to__in=users_under_reporting_head)) | Q(id__in=sub_assign_tasks_team),
                    task_status=1, is_deleted=False).values_list('id', flat=True))).values_list('task', flat=True))
            count = EtaskUserCC.objects.filter(task_id__in=team_today_reporting, user=obj, is_deleted=False).count()

        elif list_for == 'team_upcoming_reporting_cc_to':
            sub_assign_tasks_team = list(EtaskTaskSubAssignLog.objects.filter(assign_from=user,
                    sub_assign__in=users_under_reporting_head, is_deleted=False).values_list('task__id', flat=True))
            team_upcoming_reporting = list(ETaskReportingDates.objects.filter(owned_by=user, task_type=1, reporting_status=2,
                    reporting_date__date__gt=cur_date, task__in=list(EtaskTask.objects.filter(
                    (Q(assign_by=user) & Q(assign_to__in=users_under_reporting_head)) | Q(id__in=sub_assign_tasks_team),
                    task_status=1, is_deleted=False).values_list('id', flat=True))).values_list('task',flat=True))
            count = EtaskUserCC.objects.filter(task_id__in=team_upcoming_reporting, user=obj, is_deleted=False).count()
        else:
            sub_assign_tasks = list(EtaskTaskSubAssignLog.objects.filter(sub_assign__in=users_under_reporting_head,
                    is_deleted=False).values_list('task__id',flat=True))
            tasks = list(EtaskTask.objects.filter(~Q(task_status=4), Q(assign_to__in=users_under_reporting_head) |
                    Q(id__in=sub_assign_tasks) | Q(owner__in=users_under_reporting_head)).values_list('id', flat=True))
            count = EtaskUserCC.objects.filter(task_id__in=tasks, user=obj, is_deleted=False).count()

        return count


class EtaskTodayAppointmentListSerializer(serializers.ModelSerializer):
    appointment = serializers.CharField(required=False)
    class Meta:
        model=EtaskInviteEmployee
        fields='__all__'
        

class UpcomingTaskPerUserSerializer(serializers.ModelSerializer):
    parent_task=serializers.SerializerMethodField(required=False)
    sub_data = EtaskTask.objects.filter(parent_id=0,is_deleted=False)
    task_type_name=serializers.CharField(source='get_task_type_display')
    recurrance_frequency_name=serializers.CharField(source='get_recurrance_frequency_display')
    task_status_name=serializers.CharField(source='get_task_status_display')
    assign_by_name = serializers.SerializerMethodField()
    assign_to_name= serializers.SerializerMethodField()
    sub_assign_to_user_name= serializers.SerializerMethodField()
    reporting_date=serializers.SerializerMethodField()
    class Meta:
        model = EtaskTask
        fields = ('__all__')

    def get_parent_task(self,EtaskTask):
        if EtaskTask.parent_id:
            if EtaskTask.parent_id !=0:
                if self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject'):
                    parent_data=self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject')[0]
                    return parent_data

    def user_name(self, user_id):
        name = None
        full_name = ""
        name = User.objects.get(id=user_id)
        if name:
            full_name =  name.__dict__['first_name']+" "+name.__dict__['last_name']
        return full_name

    def get_assign_by_name(self,EtaskTask):
        name = None
        full_name = ""
        if EtaskTask.assign_by:
            name = User.objects.get(id=EtaskTask.assign_by.id)
            if name:
                full_name =  name.__dict__['first_name']+" "+name.__dict__['last_name']
                # #print("full_name",full_name)
            return full_name

    def get_sub_assign_to_user_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.sub_assign_to_user:
            name=User.objects.get(id=EtaskTask.sub_assign_to_user.id)
            if name:
                full_name= name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name

    def get_assign_to_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.assign_to:
            name =User.objects.get(id=EtaskTask.assign_to.id)
            if name:
                full_name=name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name

    def get_reporting_date(self,EtaskTask):
        if EtaskTask.id:
            report_date_list = []
            report_date=ETaskReportingDates.objects.filter(task_type=1,task=EtaskTask.id,is_deleted=False)
            # #print("report_date",report_date)
            current_date=datetime.now().date()
            if report_date:
                for dt in report_date:
                    pre_report= dt.reporting_date.date()
                    # #print('pre_report',pre_report)
                    if pre_report>current_date:                     
                        dt_dict={
                            'id':dt.id,
                            'reporting_date':dt.reporting_date,
                        }
                        report_date_list.append(dt_dict)                             
                return report_date_list
            else:
                return []

class UpcomingTaskReportingPerUserSerializer(serializers.ModelSerializer):
    parent_task=serializers.SerializerMethodField(required=False)
    sub_data = EtaskTask.objects.filter(parent_id=0,is_deleted=False)
    task_type_name=serializers.CharField(source='get_task_type_display')
    recurrance_frequency_name=serializers.CharField(source='get_recurrance_frequency_display')
    task_status_name=serializers.CharField(source='get_task_status_display')
    assign_by_name = serializers.SerializerMethodField()
    assign_to_name= serializers.SerializerMethodField()
    sub_assign_to_user_name= serializers.SerializerMethodField()
    reporting_date=serializers.SerializerMethodField()
    class Meta:
        model = EtaskTask
        fields = ('__all__')

    def get_parent_task(self,EtaskTask):
        if EtaskTask.parent_id:
            if EtaskTask.parent_id !=0:
                if self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject'):
                    parent_data=self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject')[0]
                    return parent_data

    def user_name(self, user_id):
        name = None
        full_name = ""
        name = User.objects.get(id=user_id)
        if name:
            full_name =  name.__dict__['first_name']+" "+name.__dict__['last_name']
        return full_name

    def get_assign_by_name(self,EtaskTask):
        name = None
        full_name = ""
        if EtaskTask.assign_by:
            name = User.objects.get(id=EtaskTask.assign_by.id)
            if name:
                full_name =  name.__dict__['first_name']+" "+name.__dict__['last_name']
                # #print("full_name",full_name)
            return full_name

    def get_sub_assign_to_user_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.sub_assign_to_user:
            name=User.objects.get(id=EtaskTask.sub_assign_to_user.id)
            if name:
                full_name= name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name

    def get_assign_to_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.assign_to:
            name =User.objects.get(id=EtaskTask.assign_to.id)
            if name:
                full_name=name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name

    def get_reporting_date(self,EtaskTask):
        if EtaskTask.id:
            report_date_list = []
            report_date=ETaskReportingDates.objects.filter(task_type=1,task=EtaskTask.id,is_deleted=False)
            # #print("report_date",report_date)
            current_date=datetime.now().date()
            if report_date:
                for dt in report_date:
                    pre_report= dt.reporting_date.date()
                    # #print('pre_report',pre_report)
                    if pre_report>current_date:                     
                        dt_dict={
                            'id':dt.id,
                            'reporting_date':dt.reporting_date,
                        }
                        report_date_list.append(dt_dict)                             
                return report_date_list
            else:
                return []

#::::::::::::::::DEFAULT REPORTING DATES:::::::::::::::::::::::::::::::::::::#
class ETaskDefaultReportingDatesSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    monthly_data = serializers.ListField(required=False)
    class Meta:
        model = EtaskMonthlyReportingDate
        fields = ('id','employee','created_by','owned_by','monthly_data')
        #extra_fields = ('monthly_data',)  
    def create(self, validated_data):
        try:
            user=self.context['request'].user
            #print('user',user,type(user))
            #print('is_superuser',user.is_superuser)
            users_list=(list(TCoreUserDetail.objects.filter((Q(reporting_head=user)|Q(hod=user)),cu_is_deleted=False).values_list('cu_user',flat=True)))
            #print('users_list',users_list)
            if user.is_superuser==False:
                if users_list:
                    with transaction.atomic():
                        monthly_data = validated_data.get('monthly_data') if 'monthly_data' in validated_data else []
                        #print('monthly_data',monthly_data)                 
                        for data in monthly_data:
                            filter={}
                            search_filter={}
                            filter['employee_id']=data['employee']
                            search_filter['employee_id']=data['employee']
                            field_label_value = data['field_label_value'] if 'field_label_value' in data   else []
                            if field_label_value:
                                for f_l in field_label_value:
                                    filter['field_label']=f_l['field_label']
                                    filter['field_value']=f_l['field_value']
                                    search_filter['field_value']=f_l['field_value']
                                    #print('count', EtaskMonthlyReportingDate.objects.filter(**search_filter,is_deleted=False).count())
                                    if EtaskMonthlyReportingDate.objects.filter(**search_filter,is_deleted=False).count()==0:
                                        monthly_reporting_dates=EtaskMonthlyReportingDate.objects.create(**filter,created_by=user,owned_by=user)
                        return validated_data
                else:
                    return []
            else:
                return []
        except Exception as e:
            raise e


class ETaskDefaultReportingDatesSerializerV2(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    monthly_data = serializers.ListField(required=False)
    class Meta:
        model = EtaskMonthlyReportingDate
        fields = ('id','employee','created_by','owned_by','monthly_data')

    def get_ics_string(self,summery=None,dates=[],description=None):
        ics_data = """BEGIN:VCALENDAR
VERSION:2.0
CALSCALE:GREGORIAN\n"""
        for date in dates:
            ics_data +=   """BEGIN:VEVENT
SUMMARY:{}
DTSTART;TZID=Asia/Kolkata:{}
DTEND;TZID=Asia/Kolkata:{}
RRULE:FREQ=MONTHLY
LOCATION:Shyam Tower,Kolkata-700091
DESCRIPTION:{}
STATUS:CONFIRMED
SEQUENCE:3
UID:{}
BEGIN:VALARM
TRIGGER:-PT10M
DESCRIPTION:Pickup Reminder
ACTION:DISPLAY
END:VALARM
END:VEVENT\n""".format(summery,date['start_date'],date['end_date'],description,date['uid'])
        ics_data += "END:VCALENDAR"
        return ics_data

    def create(self, validated_data):
        try:
            user=self.context['request'].user
            with transaction.atomic():
                monthly_data = validated_data.get('monthly_data') if 'monthly_data' in validated_data else []
                cur_date = datetime.now()                 
                for data in monthly_data:
                    filter={}
                    search_filter={}
                    filter['employee_id']=data['employee']
                    search_filter['employee_id']=data['employee']
                    search_filter['owned_by']=user
                    field_label_value = data['field_label_value'] if 'field_label_value' in data   else []
                    if field_label_value:
                        day_date = dict()
                        for f_l in field_label_value:
                            filter['field_label']=f_l['field_label']
                            filter['field_value']=f_l['field_value']
                            filter['start_time']=f_l['start_time']
                            filter['end_time']=f_l['end_time']
                            search_filter['field_value']=f_l['field_value']
                            

                            #print('count', EtaskMonthlyReportingDate.objects.filter(**search_filter,is_deleted=False).count())
                            if EtaskMonthlyReportingDate.objects.filter(**search_filter,is_deleted=False).count()==0:
                                monthly_reporting_dates = EtaskMonthlyReportingDate.objects.create(**filter,created_by=user,owned_by=user)
                            else:
                                monthly_reporting_dates = EtaskMonthlyReportingDate.objects.filter(**search_filter,is_deleted=False).first()
                            
                            start_time_obj = datetime.strptime(f_l['start_time'], '%H:%M:%S').time()
                            end_time_obj = datetime.strptime(f_l['end_time'], '%H:%M:%S').time()
                            day_date[f_l['field_value']] = {
                                'start_date': datetime.combine(cur_date.replace(day=f_l['field_value']).date(),
                                                               start_time_obj).strftime("%Y%m%dT%H%M%S"),
                                'end_date': datetime.combine(cur_date.replace(day=f_l['field_value']).date(),
                                                               end_time_obj).strftime("%Y%m%dT%H%M%S"),
                                'uid': monthly_reporting_dates.uid
                            }

                        recipient_user = User.objects.get(id=int(data['employee']))
                        summery = 'Monthly Default Reporting Dates'
                        description = 'You will be reported to {}.'.format(user.get_full_name())
                        ics_file_data = self.get_ics_string(summery=summery,dates=day_date.values(),description=description)

                        if recipient_user.cu_user.cu_alt_email_id:
                            mail_data = {
                                        "recipient_name" : recipient_user.get_full_name(),
                                        "reporting_to": user.get_full_name(),
                                        "reporting_by": recipient_user.get_full_name(),
                                        "days": ', '.join(list(map(str,day_date.keys())))
                                    }

                            send_mail_list('DRDC', [recipient_user.cu_user.cu_alt_email_id], mail_data,
                                           ics=ics_file_data)

                        summery = 'Monthly Default Reporting Dates'
                        description = 'You will be reported by {}.'.format(recipient_user.get_full_name())
                        ics_file_data = self.get_ics_string(summery=summery, dates=day_date.values(),
                                                            description=description)
                        if user.cu_user.cu_alt_email_id:
                            mail_data = {
                                        "recipient_name" : user.get_full_name(),
                                        "reporting_to": user.get_full_name(),
                                        "reporting_by": recipient_user.get_full_name(),
                                        "days": ', '.join(list(map(str,day_date.keys())))
                                    }

                            send_mail_list('DRDC', [user.cu_user.cu_alt_email_id], mail_data,
                                           ics=ics_file_data)


                return validated_data
                
        except Exception as e:
            raise e


class EtaskReportingDateAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    is_manual_time_entry = serializers.BooleanField(default=False)

    class Meta:
        model = ETaskReportingDates
        fields = '__all__'
        extra_fields = ('is_manual_time_entry')

    def create_default_reporting(self,task=None,updated_by=None):
        current_date = datetime.now()
        end_date = task.extended_date if task.extended_date else task.end_date
        subassign_log = EtaskTaskSubAssignLog.objects.filter(task=task,assign_from=updated_by,is_deleted=False).first()
        if subassign_log:
            assign_to = subassign_log.sub_assign
        else:
            assign_to = task.assign_to
        
        # Default Reporting Date will be added #
        reporting_date_dict = {}
        default_reporting_dates = EtaskMonthlyReportingDate.objects.filter(employee=assign_to,
                                owned_by=updated_by).values_list('field_value',flat=True)
        for date_ob in daterange(task.start_date.date(),end_date.date()):
            if date_ob.day in default_reporting_dates and date_ob >= current_date.date():
                default_reporting_date = EtaskMonthlyReportingDate.objects.filter(employee=assign_to,
                                field_value=date_ob.day,owned_by=updated_by).values('field_value','start_time').first()
                
                reporting_date_dict[str(date_ob)] = str(date_ob)+'T'+str(default_reporting_date['start_time']) if default_reporting_date['start_time'] else str(date_ob)+'T10:00:00'
                break

        if reporting_date_dict:
            reporting_date_dict.update({str(end_date.date()):str(end_date.replace(hour=10, minute=00).strftime("%Y-%m-%dT%H:%M:%S"))})
        
        existed_reporting = list(ETaskReportingDates.objects.filter(task=task.id,owned_by=updated_by,
                                reporting_date__date__in=reporting_date_dict.keys()).values_list('reporting_date__date',flat=True))
        
        existed_reporting = list(map(str,existed_reporting))
        final_reporting_dict = {k:v for k,v in reporting_date_dict.items() if k not in existed_reporting}

        if final_reporting_dict:
            for k,v in final_reporting_dict.items():
                rdate_details, created = ETaskReportingDates.objects.get_or_create(
                    task_type=1,
                    task=task.id,
                    reporting_date=datetime.strptime(v, "%Y-%m-%dT%H:%M:%S"),
                    created_by=updated_by,
                    owned_by=updated_by
                )
                reporting_log, created = ETaskReportingActionLog.objects.get_or_create(
                    task_id=task.id,
                    reporting_date_id=str(rdate_details),
                    updated_date=datetime.now().date(),
                    status=2,
                    created_by=updated_by,
                    owned_by=updated_by
                )
    

    def create(self, validated_data):
            try:
                user=self.context['request'].user
                with transaction.atomic():
                    current_date=datetime.now()
                    created_by = validated_data.get('created_by')
                    task = validated_data.get('task')
                    # reporting_date = datetime.combine(reporting_date_without_time, current_date.time())
                    # is_manual_time_entry = validated_data.get('is_manual_time_entry')

                    reporting_obj = ETaskReportingDates.objects.create(**validated_data)

                    task_obj = EtaskTask.objects.get(id=task)
                    self.create_default_reporting(task=task_obj,updated_by=created_by)
                    create_appointment(reporting_dates=[reporting_obj])
                    return validated_data
                    
            except Exception as e:
                raise e


class EtaskMassReportingDateAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    reporting_date_ids = serializers.ListField(default=False)
    is_confirm = serializers.BooleanField(default=False)
    request_status = serializers.CharField(required=False)
    message = serializers.CharField(required=False)
    
    class Meta:
        model = ETaskReportingDates
        fields = '__all__'
        extra_fields = ('reporting_date_ids','is_confirm','request_status','message',)

    def create_default_reporting(self,task=None,updated_by=None):
        current_date = datetime.now()
        end_date = task.extended_date if task.extended_date else task.end_date
        subassign_log = EtaskTaskSubAssignLog.objects.filter(task=task,assign_from=updated_by,is_deleted=False).first()
        if subassign_log:
            assign_to = subassign_log.sub_assign
        else:
            assign_to = task.assign_to
        
        # Default Reporting Date will be added #
        reporting_date_dict = {}
        default_reporting_dates = EtaskMonthlyReportingDate.objects.filter(employee=assign_to,
                                owned_by=updated_by).values_list('field_value',flat=True)
        for date_ob in daterange(task.start_date.date(),end_date.date()):
            if date_ob.day in default_reporting_dates and date_ob >= current_date.date():
                default_reporting_date = EtaskMonthlyReportingDate.objects.filter(employee=assign_to,
                                field_value=date_ob.day,owned_by=updated_by).values('field_value','start_time').first()
                
                reporting_date_dict[str(date_ob)] = str(date_ob)+'T'+str(default_reporting_date['start_time']) if default_reporting_date['start_time'] else str(date_ob)+'T10:00:00'
                break

        if reporting_date_dict:
            reporting_date_dict.update({str(end_date.date()):str(end_date.replace(hour=10, minute=00).strftime("%Y-%m-%dT%H:%M:%S"))})
        
        existed_reporting = list(ETaskReportingDates.objects.filter(task=task.id,owned_by=updated_by,
                                reporting_date__date__in=reporting_date_dict.keys()).values_list('reporting_date__date',flat=True))
        
        existed_reporting = list(map(str,existed_reporting))
        final_reporting_dict = {k:v for k,v in reporting_date_dict.items() if k not in existed_reporting}

        if final_reporting_dict:
            for k,v in final_reporting_dict.items():
                rdate_details, created = ETaskReportingDates.objects.get_or_create(
                    task_type=1,
                    task=task.id,
                    reporting_date=datetime.strptime(v, "%Y-%m-%dT%H:%M:%S"),
                    created_by=updated_by,
                    owned_by=updated_by
                )
                reporting_log, created = ETaskReportingActionLog.objects.get_or_create(
                    task_id=task.id,
                    reporting_date_id=str(rdate_details),
                    updated_date=datetime.now().date(),
                    status=2,
                    created_by=updated_by,
                    owned_by=updated_by
                )

    def create(self, validated_data):
        with transaction.atomic():
            current_date = datetime.now()
            created_by = validated_data.get('created_by')
            owned_by = validated_data.get('owned_by')
            reporting_date_ids = validated_data.get('reporting_date_ids')
            reporting_date = validated_data.get('reporting_date')
            reporting_end_date = validated_data.get('reporting_end_date')
            is_manual_time_entry = validated_data.get('is_manual_time_entry')
            task_type = validated_data.get('task_type')
            is_confirm = validated_data.pop('is_confirm')

            success_list = list()
            error_list = list()
            reporting_obj_list = list()

            reporting_dates = ETaskReportingDates.objects.filter(id__in=reporting_date_ids)

            for reporting_obj in reporting_dates:
                task = EtaskTask.objects.get(id=reporting_obj.task)
                is_overdue = get_task_flag(task=task) == 'overdue'
                is_pending_exten = is_pending_extention(task=task)
                is_pending_close = is_pending_closer(task=task)

                if (owned_by == reporting_obj.owned_by) and \
                    ((task.extended_date and task.extended_date.date()>=reporting_date.date() and task.start_date.date()<=reporting_date.date()) or \
                    (not task.extended_date and task.end_date.date()>=reporting_date.date() and task.start_date.date()<=reporting_date.date())) and \
                    (not is_overdue or (is_overdue and (is_pending_close or is_pending_exten))):
                    success_list.append(task.task_code_id)
                else:
                    error_list.append(task.task_code_id)

            if not error_list or is_confirm:
                for reporting_date_obj in reporting_dates:
                    task = EtaskTask.objects.get(id=reporting_obj.task)
                    is_overdue = get_task_flag(task=task) == 'overdue'
                    is_pending_exten = is_pending_extention(task=task)
                    is_pending_close = is_pending_closer(task=task)

                    if (owned_by == reporting_obj.owned_by) and \
                        ((task.extended_date and task.extended_date.date()>=reporting_date.date() and task.start_date.date()<=reporting_date.date()) or \
                        (not task.extended_date and task.end_date.date()>=reporting_date.date() and task.start_date.date()<=reporting_date.date())) and \
                        (not is_overdue or (is_overdue and (is_pending_close or is_pending_exten))):
                        
                        reporting_obj, is_created = ETaskReportingDates.objects.get_or_create(
                            task=reporting_date_obj.task,
                            created_by=created_by,
                            owned_by=owned_by,
                            reporting_date=reporting_date,
                            reporting_end_date=reporting_end_date,
                            is_manual_time_entry=is_manual_time_entry,
                            task_type=task_type
                        )
                        if is_created:
                            reporting_obj_list.append(reporting_obj)

                        # create default reporting date
                        self.create_default_reporting(task=task,updated_by=created_by)

                        # previous reporting dates mark as reported.
                        report_obj = ETaskReportingDates.objects.get(id=reporting_date_obj.id)
                        report_obj.task_type = 1
                        report_obj.task_status=1
                        report_obj.reporting_status = 1
                        report_obj.actual_reporting_date = current_date
                        report_obj.updated_by = created_by
                        report_obj.save()
                        prev_action= ETaskReportingActionLog.objects.filter(
                            task_id = report_obj.task,
                            reporting_date_id = report_obj.id,
                            is_deleted=False
                            ).update(is_deleted=True)
                        reporting_log = ETaskReportingActionLog.objects.create(
                            task_id = report_obj.task,
                            reporting_date_id = report_obj.id,
                            status = 1,
                            updated_by = created_by
                            )


                create_appointment(reporting_dates=reporting_obj_list)

                
            error_msg = 'Reporting date can not be added to the following Task with task_code {}'.format(', '.join(set(error_list)))
            success_msg = 'Reporting date has been added to the following Task with task_code {}'.format(', '.join(set(success_list)))
            msg = ''
            if error_list and success_list:
                msg = '{} and {}.'.format(success_msg,error_msg)
            elif error_list and not success_list:
                msg = '{}.'.format(error_msg)
            elif not error_list and success_list:
                msg = '{}.'.format(success_msg)
                
            validated_data['request_status'] = 1 if not error_list or is_confirm else 0
            validated_data['message'] = msg
            return validated_data


class OverdueReportingListSerializer(serializers.ModelSerializer):
    task_code_id = serializers.SerializerMethodField()
    task_subject = serializers.SerializerMethodField()
    reporting_by = serializers.SerializerMethodField()
    reporting_to = serializers.SerializerMethodField()
    start_date = serializers.SerializerMethodField()
    end_date = serializers.SerializerMethodField()
    extended_date = serializers.SerializerMethodField()
    parent_task = serializers.SerializerMethodField()
    parent_id = serializers.SerializerMethodField()
    owner = serializers.SerializerMethodField()
    is_pending_extention = serializers.SerializerMethodField()
    is_pending_closer = serializers.SerializerMethodField()
    requested_end_date = serializers.SerializerMethodField()
    sub_tasks = serializers.SerializerMethodField()
    task_priority = serializers.SerializerMethodField()
    status_with_pending_request = serializers.SerializerMethodField()
    overdue_by = serializers.SerializerMethodField()
    overdue_days = serializers.SerializerMethodField()
    task_flag = serializers.SerializerMethodField()

    class Meta:
        model = ETaskReportingDates
        fields = ('id','task','task_code_id','task_subject','reporting_date','reporting_by',
                'reporting_to','start_date','end_date','extended_date','parent_task','parent_id',
                'is_pending_closer','is_pending_extention','owner','requested_end_date','owned_by',
                'sub_tasks','task_priority','status_with_pending_request','overdue_by','task_flag',
                'overdue_days')

    def get_task_flag(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        TASK_TYPES = ('overdue', 'ongoing', 'upcoming')
        cur_date=datetime.now().date()
        task_flag = None
        
        if (task.extended_date is not None and task.extended_date.date() < cur_date) or (task.extended_date is None and task.end_date.date() < cur_date):
            task_flag = TASK_TYPES[0]
        elif (task.shifted_date is not None and task.shifted_date.date() <= cur_date) or (task.shifted_date is None and task.start_date.date() <= cur_date):
            task_flag = TASK_TYPES[1]
        elif (task.shifted_date is not None and task.shifted_date.date() > cur_date) or (task.shifted_date is None and task.start_date.date() > cur_date):
            task_flag = TASK_TYPES[2]
        return task_flag

    def get_overdue_by(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        cur_date=datetime.now().date()
        overdue_by = None
        if task.extended_date:
            if task.extended_date and task.extended_date.date() <= cur_date:
                extended_date = task.extended_date.date()
                days_extended=(cur_date - extended_date).days
                #print("days_extended",days_extended,type(days_extended))
                if days_extended==1:
                    overdue_by = str(days_extended)+" day"
                elif days_extended >1:
                    overdue_by = str(days_extended)+" days"
                else:
                    overdue_by = None
        else:
            if task.end_date and task.end_date.date() <= cur_date:
                end_date = task.end_date.date()
                days_extended=(cur_date - end_date).days
                #print("days_extended",days_extended,type(days_extended))
                if days_extended ==1:
                    overdue_by = str(days_extended)+" day"
                elif days_extended >1:
                    overdue_by = str(days_extended)+" days"
                else:
                    overdue_by = None
        return overdue_by

    def get_overdue_days(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        cur_date=datetime.now().date()
        overdue_by = None
        if task.extended_date:
            extended_date = task.extended_date.date()
            overdue_by=(cur_date - extended_date).days
        else:
            end_date = task.end_date.date()
            overdue_by=(cur_date - end_date).days
        return overdue_by

    def get_status_with_pending_request(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        status = list()
        task_extention = TaskExtentionDateMap.objects.filter(task=task, status=1)
        if task_extention.count():
            status.append('Pending Extention')
        task_closer = TaskCompleteReopenMap.objects.filter(task=task,status=1)
        if task_closer.count():
            status.append('Pending Closure')
        if task.task_status == 1 and not task_extention.count() and not task_extention.count():
            status.append(task.get_task_status_display())
        return ' and '.join(status)

    def get_task_priority(self,obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        return task.task_priority

    def get_sub_tasks(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        sub_tasks_data = EtaskTask.objects.filter(~Q(task_status=4),parent_id=task.id,is_deleted=False).values('id','task_subject')
        return sub_tasks_data if sub_tasks_data else list() 

    def get_requested_end_date(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        return task.requested_end_date

    def get_is_pending_closer(self, obj):
        task_closer = TaskCompleteReopenMap.objects.filter(task_id=obj.task,status=1)
        return task_closer.count()>0

    def get_is_pending_extention(self, obj):
        task_extention = TaskExtentionDateMap.objects.filter(task_id=obj.task, status=1)
        return task_extention.count()>0

    def get_owner(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        return task.owner.id

    def get_parent_id(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        return task.parent_id

    def get_parent_task(self,obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        if task.parent_id and EtaskTask.objects.filter(id=task.parent_id).count():
            parent_data=EtaskTask.objects.filter(id=task.parent_id).values('id','task_subject','task_description')[0]
            return parent_data
    
    def get_start_date(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        return task.start_date

    def get_end_date(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        return task.end_date

    def get_extended_date(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        return task.extended_date

    def get_reporting_by(self, obj):
        login_user = self.context['request'].user
        task = EtaskTask.objects.filter(id=obj.task).first()
        etask_sub_assign = EtaskTaskSubAssignLog.objects.filter(task=obj.task,sub_assign=login_user,is_deleted=False).first()
        return etask_sub_assign.sub_assign.get_full_name() if etask_sub_assign else task.assign_to.get_full_name()

    def get_reporting_to(self, obj):
        login_user = self.context['request'].user
        task = EtaskTask.objects.filter(id=obj.task).first()
        etask_sub_assign = EtaskTaskSubAssignLog.objects.filter(task=obj.task,assign_from=login_user,is_deleted=False).first()
        return etask_sub_assign.assign_from.get_full_name() if etask_sub_assign else task.assign_by.get_full_name()

    def get_task_subject(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        return task.task_subject if task else ''

    def get_task_code_id(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        return task.task_code_id if task else ''


class EtaskReportingListDownloadSerializer(serializers.ModelSerializer):
    task_code_id = serializers.SerializerMethodField()
    task_subject = serializers.SerializerMethodField()
    reporting_by = serializers.SerializerMethodField()
    reporting_to = serializers.SerializerMethodField()
    start_date = serializers.SerializerMethodField()
    end_date = serializers.SerializerMethodField()
    reporting_date = serializers.SerializerMethodField()
    extended_date = serializers.SerializerMethodField()
    parent_task = serializers.SerializerMethodField()
    parent_id = serializers.SerializerMethodField()
    owner = serializers.SerializerMethodField()
    is_pending_extention = serializers.SerializerMethodField()
    is_pending_closer = serializers.SerializerMethodField()
    requested_end_date = serializers.SerializerMethodField()
    sub_tasks = serializers.SerializerMethodField()
    task_priority = serializers.SerializerMethodField()
    status_with_pending_request = serializers.SerializerMethodField()
    overdue_by = serializers.SerializerMethodField()
    overdue_days = serializers.SerializerMethodField()
    task_flag = serializers.SerializerMethodField()

    class Meta:
        model = ETaskReportingDates
        fields = ('id','task','task_code_id','task_subject','reporting_date','reporting_by',
                'reporting_to','start_date','end_date','extended_date','parent_task','parent_id',
                'is_pending_closer','is_pending_extention','owner','requested_end_date','owned_by',
                'sub_tasks','task_priority','status_with_pending_request','overdue_by','task_flag',
                'overdue_days')

    def get_task_flag(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        TASK_TYPES = ('overdue', 'ongoing', 'upcoming')
        cur_date=datetime.now().date()
        task_flag = None
        
        if (task.extended_date is not None and task.extended_date.date() < cur_date) or (task.extended_date is None and task.end_date.date() < cur_date):
            task_flag = TASK_TYPES[0]
        elif (task.shifted_date is not None and task.shifted_date.date() <= cur_date) or (task.shifted_date is None and task.start_date.date() <= cur_date):
            task_flag = TASK_TYPES[1]
        elif (task.shifted_date is not None and task.shifted_date.date() > cur_date) or (task.shifted_date is None and task.start_date.date() > cur_date):
            task_flag = TASK_TYPES[2]
        return task_flag

    def get_overdue_by(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        cur_date=datetime.now().date()
        overdue_by = None
        if task.extended_date:
            if task.extended_date and task.extended_date.date() <= cur_date:
                extended_date = task.extended_date.date()
                days_extended=(cur_date - extended_date).days
                #print("days_extended",days_extended,type(days_extended))
                if days_extended==1:
                    overdue_by = str(days_extended)+" day"
                elif days_extended >1:
                    overdue_by = str(days_extended)+" days"
                else:
                    overdue_by = None
        else:
            if task.end_date and task.end_date.date() <= cur_date:
                end_date = task.end_date.date()
                days_extended=(cur_date - end_date).days
                #print("days_extended",days_extended,type(days_extended))
                if days_extended ==1:
                    overdue_by = str(days_extended)+" day"
                elif days_extended >1:
                    overdue_by = str(days_extended)+" days"
                else:
                    overdue_by = None
        return overdue_by

    def get_overdue_days(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        cur_date=datetime.now().date()
        overdue_by = None
        if task.extended_date:
            extended_date = task.extended_date.date()
            overdue_by=(cur_date - extended_date).days
        else:
            end_date = task.end_date.date()
            overdue_by=(cur_date - end_date).days
        return overdue_by

    def get_status_with_pending_request(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        TASK_TYPES = ('Overdue', 'Ongoing', 'Upcoming')
        cur_date=datetime.now().date()
        task_flag = None
        
        if (task.extended_date is not None and task.extended_date.date() < cur_date) or (task.extended_date is None and task.end_date.date() < cur_date):
            task_flag = TASK_TYPES[0]
        elif (task.shifted_date is not None and task.shifted_date.date() <= cur_date) or (task.shifted_date is None and task.start_date.date() <= cur_date):
            task_flag = TASK_TYPES[1]
        elif (task.shifted_date is not None and task.shifted_date.date() > cur_date) or (task.shifted_date is None and task.start_date.date() > cur_date):
            task_flag = TASK_TYPES[2]

        status = list()
        task_extention = TaskExtentionDateMap.objects.filter(task=task, status=1)
        if task_extention.count():
            status.append('Pending Extention')
        task_closer = TaskCompleteReopenMap.objects.filter(task=task,status=1)
        if task_closer.count():
            status.append('Pending Closure')
        if task.task_status == 1 and not task_extention.count() and not task_extention.count():
            status.append(task_flag)
        return ' and '.join(status)

    def get_task_priority(self,obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        return task.task_priority

    def get_sub_tasks(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        sub_tasks_data = EtaskTask.objects.filter(~Q(task_status=4),parent_id=task.id,is_deleted=False).values('id','task_subject')
        return sub_tasks_data if sub_tasks_data else list() 

    def get_requested_end_date(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        return task.requested_end_date

    def get_is_pending_closer(self, obj):
        task_closer = TaskCompleteReopenMap.objects.filter(task_id=obj.task,status=1)
        return task_closer.count()>0

    def get_is_pending_extention(self, obj):
        task_extention = TaskExtentionDateMap.objects.filter(task_id=obj.task, status=1)
        return task_extention.count()>0

    def get_owner(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        return task.owner.id

    def get_parent_id(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        return task.parent_id

    def get_parent_task(self,obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        if task.parent_id and EtaskTask.objects.filter(id=task.parent_id).count():
            parent_data=EtaskTask.objects.filter(id=task.parent_id).values('id','task_subject','task_description')[0]
            return parent_data
    
    def get_start_date(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        return task.start_date.strftime("%d %b %Y")

    def get_end_date(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        return task.end_date.strftime("%d %b %Y")

    def get_reporting_date(self, obj):
        return obj.reporting_date.strftime("%d %b %Y, %I:%M %p") if obj.is_manual_time_entry else obj.reporting_date.strftime("%d %b %Y")

    def get_extended_date(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        return task.extended_date

    def get_reporting_by(self, obj):
        login_user = self.context['request'].user
        task = EtaskTask.objects.filter(id=obj.task).first()
        etask_sub_assign = EtaskTaskSubAssignLog.objects.filter(task=obj.task,sub_assign=login_user,is_deleted=False).first()
        return etask_sub_assign.sub_assign.get_full_name() if etask_sub_assign else task.assign_to.get_full_name()

    def get_reporting_to(self, obj):
        login_user = self.context['request'].user
        task = EtaskTask.objects.filter(id=obj.task).first()
        etask_sub_assign = EtaskTaskSubAssignLog.objects.filter(task=obj.task,assign_from=login_user,is_deleted=False).first()
        return etask_sub_assign.assign_from.get_full_name() if etask_sub_assign else task.assign_by.get_full_name()

    def get_task_subject(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        return task.task_subject if task else ''

    def get_task_code_id(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        return task.task_code_id if task else ''


class TodaysReportingListSerializer(serializers.ModelSerializer):
    task_code_id = serializers.SerializerMethodField()
    task_subject = serializers.SerializerMethodField()
    reporting_by = serializers.SerializerMethodField()
    reporting_to = serializers.SerializerMethodField()
    start_date = serializers.SerializerMethodField()
    end_date = serializers.SerializerMethodField()
    extended_date = serializers.SerializerMethodField()
    parent_task = serializers.SerializerMethodField()
    parent_id = serializers.SerializerMethodField()
    owner = serializers.SerializerMethodField()
    is_pending_extention = serializers.SerializerMethodField()
    is_pending_closer = serializers.SerializerMethodField()
    requested_end_date = serializers.SerializerMethodField()
    sub_tasks = serializers.SerializerMethodField()
    task_priority = serializers.SerializerMethodField()
    status_with_pending_request = serializers.SerializerMethodField()
    overdue_by = serializers.SerializerMethodField()
    task_flag = serializers.SerializerMethodField()
    overdue_days = serializers.SerializerMethodField()

    class Meta:
        model = ETaskReportingDates
        fields = ('id','task','task_code_id','task_subject','reporting_date','reporting_by',
                'reporting_to','start_date','end_date','extended_date','parent_task','parent_id',
                'is_pending_closer','is_pending_extention','owner','requested_end_date','owned_by',
                'sub_tasks','task_priority','status_with_pending_request','overdue_by','task_flag',
                'overdue_days')

    def get_task_flag(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        TASK_TYPES = ('overdue', 'ongoing', 'upcoming')
        cur_date=datetime.now().date()
        task_flag = None
        
        if (task.extended_date is not None and task.extended_date.date() < cur_date) or (task.extended_date is None and task.end_date.date() < cur_date):
            task_flag = TASK_TYPES[0]
        elif (task.shifted_date is not None and task.shifted_date.date() <= cur_date) or (task.shifted_date is None and task.start_date.date() <= cur_date):
            task_flag = TASK_TYPES[1]
        elif (task.shifted_date is not None and task.shifted_date.date() > cur_date) or (task.shifted_date is None and task.start_date.date() > cur_date):
            task_flag = TASK_TYPES[2]
        return task_flag

    def get_overdue_by(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        cur_date=datetime.now().date()
        overdue_by = None
        if task.extended_date:
            if task.extended_date and task.extended_date.date() <= cur_date:
                extended_date = task.extended_date.date()
                days_extended=(cur_date - extended_date).days
                #print("days_extended",days_extended,type(days_extended))
                if days_extended==1:
                    overdue_by = str(days_extended)+" day"
                elif days_extended >1:
                    overdue_by = str(days_extended)+" days"
                else:
                    overdue_by = None
        else:
            if task.end_date and task.end_date.date() <= cur_date:
                end_date = task.end_date.date()
                days_extended=(cur_date - end_date).days
                #print("days_extended",days_extended,type(days_extended))
                if days_extended ==1:
                    overdue_by = str(days_extended)+" day"
                elif days_extended >1:
                    overdue_by = str(days_extended)+" days"
                else:
                    overdue_by = None
        return overdue_by

    def get_overdue_days(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        cur_date=datetime.now().date()
        overdue_by = None
        if task.extended_date:
            extended_date = task.extended_date.date()
            overdue_by=(cur_date - extended_date).days
        else:
            end_date = task.end_date.date()
            overdue_by=(cur_date - end_date).days
        return overdue_by

    def get_status_with_pending_request(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        status = list()
        task_extention = TaskExtentionDateMap.objects.filter(task=task, status=1)
        if task_extention.count():
            status.append('Pending Extention')
        task_closer = TaskCompleteReopenMap.objects.filter(task=task,status=1)
        if task_closer.count():
            status.append('Pending Closure')
        if task.task_status == 1 and not task_extention.count() and not task_extention.count():
            status.append(task.get_task_status_display())
        return ' and '.join(status)

    def get_task_priority(self,obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        return task.task_priority

    def get_sub_tasks(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        sub_tasks_data = EtaskTask.objects.filter(~Q(task_status=4),parent_id=task.id,is_deleted=False).values('id','task_subject')
        return sub_tasks_data if sub_tasks_data else list() 

    def get_requested_end_date(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        return task.requested_end_date

    def get_is_pending_closer(self, obj):
        task_closer = TaskCompleteReopenMap.objects.filter(task_id=obj.task,status=1)
        return task_closer.count()>0

    def get_is_pending_extention(self, obj):
        task_extention = TaskExtentionDateMap.objects.filter(task_id=obj.task, status=1)
        return task_extention.count()>0

    def get_owner(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        return task.owner.id

    def get_parent_id(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        return task.parent_id

    def get_parent_task(self,obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        if task.parent_id and EtaskTask.objects.filter(id=task.parent_id).count():
            parent_data=EtaskTask.objects.filter(id=task.parent_id).values('id','task_subject','task_description')[0]
            return parent_data
    
    def get_start_date(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        return task.start_date

    def get_end_date(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        return task.end_date

    def get_extended_date(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        return task.extended_date

    def get_reporting_by(self, obj):
        login_user = self.context['request'].user
        task = EtaskTask.objects.filter(id=obj.task).first()
        etask_sub_assign = EtaskTaskSubAssignLog.objects.filter(task=obj.task,sub_assign=login_user,is_deleted=False).first()
        return etask_sub_assign.sub_assign.get_full_name() if etask_sub_assign else task.assign_to.get_full_name()

    def get_reporting_to(self, obj):
        login_user = self.context['request'].user
        task = EtaskTask.objects.filter(id=obj.task).first()
        etask_sub_assign = EtaskTaskSubAssignLog.objects.filter(task=obj.task,assign_from=login_user,is_deleted=False).first()
        return etask_sub_assign.assign_from.get_full_name() if etask_sub_assign else task.assign_by.get_full_name()

    def get_task_subject(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        return task.task_subject if task else ''

    def get_task_code_id(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        return task.task_code_id if task else ''


class UpcomingReportingListSerializer(serializers.ModelSerializer):
    task_code_id = serializers.SerializerMethodField()
    task_subject = serializers.SerializerMethodField()
    reporting_by = serializers.SerializerMethodField()
    reporting_to = serializers.SerializerMethodField()
    start_date = serializers.SerializerMethodField()
    end_date = serializers.SerializerMethodField()
    extended_date = serializers.SerializerMethodField()
    parent_task = serializers.SerializerMethodField()
    parent_id = serializers.SerializerMethodField()
    owner = serializers.SerializerMethodField()
    is_pending_extention = serializers.SerializerMethodField()
    is_pending_closer = serializers.SerializerMethodField()
    requested_end_date = serializers.SerializerMethodField()
    sub_tasks = serializers.SerializerMethodField()
    task_priority = serializers.SerializerMethodField()
    status_with_pending_request = serializers.SerializerMethodField()
    overdue_by = serializers.SerializerMethodField()
    task_flag = serializers.SerializerMethodField()
    overdue_days = serializers.SerializerMethodField()

    class Meta:
        model = ETaskReportingDates
        fields = ('id','task','task_code_id','task_subject','reporting_date','reporting_by',
                'reporting_to','start_date','end_date','extended_date','parent_task','parent_id',
                'is_pending_closer','is_pending_extention','owner','requested_end_date','owned_by',
                'sub_tasks','task_priority','status_with_pending_request','overdue_by','task_flag',
                'overdue_days')

    def get_task_flag(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        TASK_TYPES = ('overdue', 'ongoing', 'upcoming')
        cur_date=datetime.now().date()
        task_flag = None
        
        if (task.extended_date is not None and task.extended_date.date() < cur_date) or (task.extended_date is None and task.end_date.date() < cur_date):
            task_flag = TASK_TYPES[0]
        elif (task.shifted_date is not None and task.shifted_date.date() <= cur_date) or (task.shifted_date is None and task.start_date.date() <= cur_date):
            task_flag = TASK_TYPES[1]
        elif (task.shifted_date is not None and task.shifted_date.date() > cur_date) or (task.shifted_date is None and task.start_date.date() > cur_date):
            task_flag = TASK_TYPES[2]
        return task_flag

    def get_overdue_by(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        cur_date=datetime.now().date()
        overdue_by = None
        if task.extended_date:
            if task.extended_date and task.extended_date.date() <= cur_date:
                extended_date = task.extended_date.date()
                days_extended=(cur_date - extended_date).days
                #print("days_extended",days_extended,type(days_extended))
                if days_extended==1:
                    overdue_by = str(days_extended)+" day"
                elif days_extended >1:
                    overdue_by = str(days_extended)+" days"
                else:
                    overdue_by = None
        else:
            if task.end_date and task.end_date.date() <= cur_date:
                end_date = task.end_date.date()
                days_extended=(cur_date - end_date).days
                #print("days_extended",days_extended,type(days_extended))
                if days_extended ==1:
                    overdue_by = str(days_extended)+" day"
                elif days_extended >1:
                    overdue_by = str(days_extended)+" days"
                else:
                    overdue_by = None
        return overdue_by

    def get_overdue_days(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        cur_date=datetime.now().date()
        overdue_by = None
        if task.extended_date:
            extended_date = task.extended_date.date()
            overdue_by=(cur_date - extended_date).days
        else:
            end_date = task.end_date.date()
            overdue_by=(cur_date - end_date).days
        return overdue_by

    def get_status_with_pending_request(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        status = list()
        task_extention = TaskExtentionDateMap.objects.filter(task=task, status=1)
        if task_extention.count():
            status.append('Pending Extention')
        task_closer = TaskCompleteReopenMap.objects.filter(task=task,status=1)
        if task_closer.count():
            status.append('Pending Closure')
        if task.task_status == 1 and not task_extention.count() and not task_extention.count():
            status.append(task.get_task_status_display())
        return ' and '.join(status)

    def get_task_priority(self,obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        return task.task_priority

    def get_sub_tasks(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        sub_tasks_data = EtaskTask.objects.filter(~Q(task_status=4),parent_id=task.id,is_deleted=False).values('id','task_subject')
        return sub_tasks_data if sub_tasks_data else list() 

    def get_requested_end_date(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        return task.requested_end_date

    def get_is_pending_closer(self, obj):
        task_closer = TaskCompleteReopenMap.objects.filter(task_id=obj.task,status=1)
        return task_closer.count()>0

    def get_is_pending_extention(self, obj):
        task_extention = TaskExtentionDateMap.objects.filter(task_id=obj.task, status=1)
        return task_extention.count()>0

    def get_owner(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        return task.owner.id

    def get_parent_id(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        return task.parent_id

    def get_parent_task(self,obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        if task.parent_id and EtaskTask.objects.filter(id=task.parent_id).count():
            parent_data=EtaskTask.objects.filter(id=task.parent_id).values('id','task_subject','task_description')[0]
            return parent_data
    
    def get_start_date(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        return task.start_date

    def get_end_date(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        return task.end_date

    def get_extended_date(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        return task.extended_date

    def get_reporting_by(self, obj):
        login_user = self.context['request'].user
        task = EtaskTask.objects.filter(id=obj.task).first()
        etask_sub_assign = EtaskTaskSubAssignLog.objects.filter(task=obj.task,sub_assign=login_user,is_deleted=False).first()
        return etask_sub_assign.sub_assign.get_full_name() if etask_sub_assign else task.assign_to.get_full_name()

    def get_reporting_to(self, obj):
        login_user = self.context['request'].user
        task = EtaskTask.objects.filter(id=obj.task).first()
        etask_sub_assign = EtaskTaskSubAssignLog.objects.filter(task=obj.task,assign_from=login_user,is_deleted=False).first()
        return etask_sub_assign.assign_from.get_full_name() if etask_sub_assign else task.assign_by.get_full_name()

    def get_task_subject(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        return task.task_subject if task else ''

    def get_task_code_id(self, obj):
        task = EtaskTask.objects.filter(id=obj.task).first()
        return task.task_code_id if task else ''


class ETaskDefaultReportingDatesDownloadSerializerV2(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    monthly_data = serializers.ListField(required=False)
    class Meta:
        model = EtaskMonthlyReportingDate
        fields = ('id','employee','created_by','owned_by','monthly_data')


class ETaskAnotherDefaultReportingDatesSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = EtaskMonthlyReportingDate
        fields = '__all__'
    def create(self,validated_data):
        try:
            employee_id=self.context['request'].query_params.get('employee',None)
            #print('employee_id',employee_id)
            loggedin_user=self.context['request'].user
            field_label=validated_data.get('field_label') if 'field_label' in validated_data else ''
            field_value=validated_data.get('field_value') if 'field_value' in validated_data else ''
            another_date=EtaskMonthlyReportingDate.objects.create(employee_id=employee_id,
                                                                    field_label=field_label,
                                                                    field_value=field_value,
                                                                    created_by=loggedin_user,
                                                                    owned_by=loggedin_user
                                                                )
            
            another_date.__dict__.pop('_state') if '_state' in another_date.__dict__ else another_date.__dict__
            #print('another_date',another_date.__dict__,type(another_date))
            return another_date

        except Exception as e:
            raise e

 
class ETaskDefaultReportingDatesUpdateSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = EtaskMonthlyReportingDate
        fields = '__all__'
    def update(self,instance,validated_data):
        field_label=validated_data.get('field_label') if 'field_label' in validated_data else ''
        field_value=validated_data.get('field_value') if 'field_value' in validated_data else ''
        instance.field_label=field_label
        instance.field_value=field_value
        instance.updated_by=validated_data.get('updated_by')
        instance.save()
        return instance


class ETaskDefaultReportingDatesUpdateSerializerV2(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = EtaskMonthlyReportingDate
        fields = '__all__'
    def update(self,instance,validated_data):
        field_label=validated_data.get('field_label') if 'field_label' in validated_data else ''
        field_value=validated_data.get('field_value') if 'field_value' in validated_data else ''
        instance.field_label=field_label
        instance.field_value=field_value
        instance.start_time=validated_data.get('start_time')
        instance.end_time=validated_data.get('end_time')        
        instance.updated_by=validated_data.get('updated_by')
        instance.save()

        cur_date = datetime.now()
        day_start_date = dict()
        day_start_date[instance.field_value] = {
            'start_date': datetime.combine(cur_date.replace(day=instance.field_value).date(),
                                           instance.start_time).strftime("%Y%m%dT%H%M%S"),
            'end_date': datetime.combine(cur_date.replace(day=instance.field_value).date(),
                                           instance.end_time).strftime("%Y%m%dT%H%M%S"),
            'uid': instance.uid
        }

        recipient_user = instance.employee
        user = instance.owned_by
        summery = 'Monthly Default Reporting Dates'
        description = 'You will be reported to {}.'.format(user.get_full_name())
        ics_file_data = self.get_ics_string(summery=summery,start_dates=day_start_date.values(),description=description)
        if recipient_user.cu_user.cu_alt_email_id:
            mail_data = {
                        "recipient_name" : recipient_user.get_full_name(),
                        "reporting_to": user.get_full_name(),
                        "reporting_by": recipient_user.get_full_name(),
                        "days": ', '.join(list(map(str,day_start_date.keys())))
                    }
            send_mail_list('DRDC', [recipient_user.cu_user.cu_alt_email_id], mail_data, ics=ics_file_data)

        summery = 'Monthly Default Reporting Dates'
        description = 'You will be reported by {}.'.format(recipient_user.get_full_name())
        ics_file_data = self.get_ics_string(summery=summery,start_dates=day_start_date.values(),description=description)
        if user.cu_user.cu_alt_email_id:
            mail_data = {
                        "recipient_name" : user.get_full_name(),
                        "reporting_to": user.get_full_name(),
                        "reporting_by": recipient_user.get_full_name(),
                        "days": ', '.join(list(map(str,day_start_date.keys())))
                    }
            send_mail_list('DRDC', [user.cu_user.cu_alt_email_id], mail_data, ics=ics_file_data)

        return instance

    def get_ics_string(self,summery=None,start_dates=[],description=None):
        ics_data = """BEGIN:VCALENDAR
VERSION:2.0
CALSCALE:GREGORIAN\n"""
        for start_date in start_dates:
            ics_data +=   """BEGIN:VEVENT
METHOD:PUBLISH
SUMMARY:{}
DTSTART;TZID=Asia/Kolkata:{}
DTEND;TZID=Asia/Kolkata:{}
RRULE:FREQ=MONTHLY
LOCATION:Shyam Tower,Kolkata-700091
DESCRIPTION:{}
STATUS:CONFIRMED
SEQUENCE:3
UID:{}
BEGIN:VALARM
TRIGGER:-PT10M
DESCRIPTION:Pickup Reminder
ACTION:DISPLAY
END:VALARM
END:VEVENT\n""".format(summery,start_date['start_date'],start_date['end_date'],description,start_date['uid'])
        ics_data += "END:VCALENDAR"
        return ics_data


class ETaskDefaultReportingDatesDeleteSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = EtaskMonthlyReportingDate
        fields = '__all__'
    def update(self,instance,validated_data):
        instance.is_deleted=True
        instance.updated_by=validated_data.get('updated_by')
        instance.save()
        return instance


#:::::::::::::::::::::::::::::::::::::: TODAY LIST -NEW ::::::::::::::::::::::::::::::::::::::::::::#
class TodayTaskDetailsPerUserSerializer(serializers.ModelSerializer):
    parent_task=serializers.SerializerMethodField(required=False)
    sub_data = EtaskTask.objects.filter(parent_id=0,is_deleted=False)
    task_type_name=serializers.CharField(source='get_task_type_display')
    recurrance_frequency_name=serializers.CharField(source='get_recurrance_frequency_display')
    task_status_name=serializers.CharField(source='get_task_status_display')
    task_priority_name=serializers.CharField(source='get_task_priority_display')
    # assign_by_name = serializers.SerializerMethodField()
    assign_to_name= serializers.SerializerMethodField()
    # sub_assign_to_user_name= serializers.SerializerMethodField()
    reporting_dates=serializers.SerializerMethodField()
    class Meta:
        model = EtaskTask
        fields = ('__all__')

    def get_parent_task(self,EtaskTask):
        if EtaskTask.parent_id:
            if EtaskTask.parent_id !=0:
                if self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject','task_description'):
                    parent_data=self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject','task_description')[0]
                    return parent_data
    
    def get_assign_to_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.assign_to:
            name =User.objects.get(id=EtaskTask.assign_to.id)
            if name:
                full_name=name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name

    def get_reporting_dates(self,EtaskTask):
        if EtaskTask.id:
            report_date_list = []
            report_date=ETaskReportingDates.objects.filter(task_type=1,task=EtaskTask.id,is_deleted=False)
            # #print("report_date",report_date)
            current_date=datetime.now().date()
            if report_date:
                for dt in report_date:
                    pre_report= dt.reporting_date.date()
                    # #print('pre_report',pre_report)
                    # if pre_report>current_date:                     
                    dt_dict={
                        'id':dt.id,
                        'reporting_date':dt.reporting_date,
                        'reporting_status':dt.get_reporting_status_display()
                    }
                    report_date_list.append(dt_dict)                             
                return report_date_list
            else:
                return []


class UpcomingTaskDetailsPerUserSerializer(serializers.ModelSerializer):
    parent_task=serializers.SerializerMethodField(required=False)
    sub_data = EtaskTask.objects.filter(parent_id=0,is_deleted=False)
    task_type_name=serializers.CharField(source='get_task_type_display')
    task_priority_name=serializers.CharField(source='get_task_priority_display')
    recurrance_frequency_name=serializers.CharField(source='get_recurrance_frequency_display')
    task_status_name=serializers.CharField(source='get_task_status_display')
    # assign_by_name = serializers.SerializerMethodField()
    assign_to_name= serializers.SerializerMethodField()
    # sub_assign_to_user_name= serializers.SerializerMethodField()
    reporting_dates=serializers.SerializerMethodField()
    class Meta:
        model = EtaskTask
        fields = ('__all__')

    def get_parent_task(self,EtaskTask):
        if EtaskTask.parent_id:
            if EtaskTask.parent_id !=0:
                if self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject','task_description'):
                    parent_data=self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject','task_description')[0]
                    return parent_data

    def get_assign_to_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.assign_to:
            name =User.objects.get(id=EtaskTask.assign_to.id)
            if name:
                full_name=name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name

    def get_reporting_dates(self,EtaskTask):
        if EtaskTask.id:
            report_date_list = []
            report_date=ETaskReportingDates.objects.filter(task_type=1,task=EtaskTask.id,is_deleted=False)
            # #print("report_date",report_date)
            current_date=datetime.now().date()
            if report_date:
                for dt in report_date:                   
                    dt_dict={
                        'id':dt.id,
                        'reporting_date':dt.reporting_date,
                        'reporting_status':dt.get_reporting_status_display()
                    }
                    report_date_list.append(dt_dict)                             
                return report_date_list
            else:
                return []


class UpcomingTaskDetailsPerUserSerializerV2(serializers.ModelSerializer):
    parent_task=serializers.SerializerMethodField(required=False)
    sub_data = EtaskTask.objects.filter(parent_id=0,is_deleted=False)
    task_type_name=serializers.CharField(source='get_task_type_display')
    task_priority_name=serializers.CharField(source='get_task_priority_display')
    recurrance_frequency_name=serializers.CharField(source='get_recurrance_frequency_display')
    task_status_name=serializers.CharField(source='get_task_status_display')
    # assign_by_name = serializers.SerializerMethodField()
    assign_to_name= serializers.SerializerMethodField()
    # sub_assign_to_user_name= serializers.SerializerMethodField()
    reporting_dates=serializers.SerializerMethodField()
    user_cc=serializers.SerializerMethodField()
    sub_tasks = serializers.SerializerMethodField()

    class Meta:
        model = EtaskTask
        fields = ('__all__')
        extra_fields = ('user_cc','sub_tasks')

    def get_sub_tasks(self, obj):
        sub_tasks_data = EtaskTask.objects.filter(~Q(task_status=4),parent_id=obj.id,is_deleted=False).values('id','task_subject')
        return sub_tasks_data if sub_tasks_data else list() 

    def get_user_cc(self, obj):
        user_cc=EtaskUserCC.objects.filter(task=obj,is_deleted=False).values('id','user__id','user__first_name', 'user__last_name')
        return user_cc if user_cc else list()

    def get_parent_task(self,EtaskTask):
        if EtaskTask.parent_id:
            if EtaskTask.parent_id !=0:
                if self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject','task_description'):
                    parent_data=self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject','task_description')[0]
                    return parent_data

    def get_assign_to_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.assign_to:
            name =User.objects.get(id=EtaskTask.assign_to.id)
            if name:
                full_name=name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name

    def get_reporting_dates(self,EtaskTask):
        if EtaskTask.id:
            report_date_list = []
            current_date=datetime.now().date()

            login_user = self.context.get("login_user")
            login_user_and_reporting_heads = list(EtaskTaskSubAssignLog.objects.filter(task=EtaskTask,sub_assign=login_user,is_deleted=False).values_list('assign_from',flat=True))
            owned_user = [EtaskTask.assign_by] if int(login_user) == EtaskTask.assign_to.id else login_user_and_reporting_heads

            report_date=ETaskReportingDates.objects.filter(task_type=1,reporting_date__gte=current_date,
                                        owned_by__in=owned_user,task=EtaskTask.id,is_deleted=False).order_by('reporting_date').order_by('reporting_date')
            
            last_reporting_date=ETaskReportingDates.objects.filter(task_type=1,reporting_date__lt=current_date,
                                        owned_by__in=owned_user,task=EtaskTask.id,is_deleted=False).order_by('reporting_date').order_by('-reporting_date')
            if report_date:
                for dt in report_date:
                    pre_report= dt.reporting_date.date()
                    # #print('pre_report',pre_report)
                    if pre_report>=current_date:                     
                        dt_dict={
                            'id':dt.id,
                            'reporting_date':dt.reporting_date,
                            'reporting_status':dt.get_reporting_status_display()
                        }
                        report_date_list.append(dt_dict)
                        break                             
                return report_date_list
            elif last_reporting_date:
                for dt in last_reporting_date:
                    pre_report= dt.reporting_date.date()
                    # #print('pre_report',pre_report)
                    if pre_report<current_date:                     
                        dt_dict={
                            'id':dt.id,
                            'reporting_date':dt.reporting_date,
                            'reporting_status':dt.get_reporting_status_display()
                        }
                        report_date_list.append(dt_dict)
                        break                             
                return report_date_list
            else:
                return []


class UpcomingTaskDetailsPerUserDownloadSerializerV2(serializers.ModelSerializer):
    parent_task=serializers.SerializerMethodField(required=False)
    sub_data = EtaskTask.objects.filter(parent_id=0,is_deleted=False)
    task_type_name=serializers.CharField(source='get_task_type_display')
    task_priority_name=serializers.CharField(source='get_task_priority_display')
    recurrance_frequency_name=serializers.CharField(source='get_recurrance_frequency_display')
    task_status_name=serializers.CharField(source='get_task_status_display')
    # assign_by_name = serializers.SerializerMethodField()
    assign_to_name= serializers.SerializerMethodField()
    # sub_assign_to_user_name= serializers.SerializerMethodField()
    reporting_dates=serializers.SerializerMethodField()
    start_date = serializers.SerializerMethodField()
    end_date = serializers.SerializerMethodField()
    extended_date = serializers.SerializerMethodField()

    class Meta:
        model = EtaskTask
        fields = ('__all__')

    def get_start_date(self, obj):
        return obj.start_date.strftime("%d %b %Y") if obj.start_date else ''

    def get_end_date(self, obj):
        return obj.end_date.strftime("%d %b %Y") if obj.end_date else ''

    def get_extended_date(self, obj):
        return obj.extended_date.strftime("%d %b %Y") if obj.extended_date else ''

    def get_parent_task(self,EtaskTask):
        if EtaskTask.parent_id:
            if EtaskTask.parent_id !=0:
                if self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject','task_description'):
                    parent_data=self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject','task_description')[0]
                    return parent_data

    def get_assign_to_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.assign_to:
            name =User.objects.get(id=EtaskTask.assign_to.id)
            if name:
                full_name=name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name

    def get_reporting_dates(self,EtaskTask):
        if EtaskTask.id:
            report_date_list = ''
            report_date=ETaskReportingDates.objects.filter(task_type=1,task=EtaskTask.id,is_deleted=False).order_by('reporting_date')
            if report_date:
                for dt in report_date:
                    report_date_list += '{}, '.format(dt.reporting_date.strftime("%d %b %Y"))                            
                return report_date_list[:-2]
            else:
                return ''


class OverdueTaskDetailsPerUserSerializer(serializers.ModelSerializer):
    parent_task=serializers.SerializerMethodField(required=False)
    sub_data = EtaskTask.objects.filter(parent_id=0,is_deleted=False)
    task_type_name=serializers.CharField(source='get_task_type_display')
    task_priority_name=serializers.CharField(source='get_task_priority_display')
    recurrance_frequency_name=serializers.CharField(source='get_recurrance_frequency_display')
    task_status_name=serializers.CharField(source='get_task_status_display')
    # assign_by_name = serializers.SerializerMethodField()
    assign_to_name= serializers.SerializerMethodField()
    # sub_assign_to_user_name= serializers.SerializerMethodField()
    reporting_dates=serializers.SerializerMethodField()
    class Meta:
        model = EtaskTask
        fields = ('__all__')

    def get_parent_task(self,EtaskTask):
        if EtaskTask.parent_id:
            if EtaskTask.parent_id !=0:
                if self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject'):
                    parent_data=self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject','task_description')[0]
                    return parent_data

    def get_assign_to_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.assign_to:
            name =User.objects.get(id=EtaskTask.assign_to.id)
            if name:
                full_name=name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name

    def get_reporting_dates(self,EtaskTask):
        if EtaskTask.id:
            report_date_list = []
            report_date=ETaskReportingDates.objects.filter(task_type=1,task=EtaskTask.id,is_deleted=False)
            # #print("report_date",report_date)
            current_date=datetime.now().date()
            if report_date:
                for dt in report_date:                     
                    dt_dict={
                        'id':dt.id,
                        'reporting_date':dt.reporting_date,
                        'reporting_status':dt.get_reporting_status_display()
                    }
                    report_date_list.append(dt_dict)                             
                return report_date_list
            else:
                return []


class EtaskClosedTaskListSerializer(serializers.ModelSerializer):
    class Meta:
        model = EtaskTask
        fields = ('id','task_code_id','parent_id','task_subject','task_description','start_date','end_date','task_status','closed_date',
                    'extended_date','assign_by','assign_to','sub_assign_to_user','get_task_status_display') #,'assign_to_name','sub_task_list', 'sub_assign_to_name','assign_by_name')

class EtaskTodaysPlannerCountSerializer(serializers.ModelSerializer):
    class Meta:
        model = EtaskTask
        fields = '__all__'

#:::::::::::::::::::::::::::::::::::::: REPORTING ::::::::::::::::::::::::::::::::::::::::::::::::#
class TodayReportingDetailsPerUserSerializer(serializers.ModelSerializer):
    # reporting_dates=serializers.SerializerMethodField()
    class Meta:
        model=EtaskTask
        fields=('id','task_code_id','task_subject','assign_by','assign_to','sub_assign_to_user','owner')
    # def get_reporting_dates(self,EtaskTask):
    #     if EtaskTask.id:
    #         report_date=list(ETaskReportingDates.objects.filter(task_type=1,task=EtaskTask.id,is_deleted=False).values_list('reporting_date',flat=True))
    #         if report_date:
    #             return report_date[0]
    #         else:
    #             return None


class TodayReportingDetailsPerUserSerializerV2(serializers.ModelSerializer):
    parent_task=serializers.SerializerMethodField(required=False)
    reporting_dates=serializers.SerializerMethodField()
    user_cc=serializers.SerializerMethodField()
    sub_tasks = serializers.SerializerMethodField()

    class Meta:
        model=EtaskTask
        fields=('id','parent_id','parent_task','task_code_id','task_subject','assign_by','assign_to','sub_assign_to_user','reporting_dates',
        'owner','user_cc','extended_date','end_date','requested_end_date','sub_tasks')

    def get_sub_tasks(self, obj):
        sub_tasks_data = EtaskTask.objects.filter(~Q(task_status=4),parent_id=obj.id,is_deleted=False).values('id','task_subject')
        return sub_tasks_data if sub_tasks_data else list() 

    def get_parent_task(self,obj):
        if obj.parent_id !=0:
            if EtaskTask.objects.filter(id=obj.parent_id):
                parent_data=EtaskTask.objects.filter(id=obj.parent_id).values('id','task_subject','task_description')[0]
                return parent_data

    def get_user_cc(self, obj):
        user_cc=EtaskUserCC.objects.filter(task=obj,is_deleted=False).values('id','user__first_name', 'user__last_name')
        return user_cc if user_cc else list()

    def get_reporting_dates(self, obj):
        cur_date = datetime.now().date()
        if obj.id:
            login_user = self.context.get("login_user")
            # login_user_and_reporting_heads = get_user_reporting_heads(user=login_user)
            # login_user_and_reporting_heads.append(login_user.id)
            login_user_and_reporting_heads = list(EtaskTaskSubAssignLog.objects.filter(task=obj,sub_assign=login_user,is_deleted=False).values_list('assign_from',flat=True))
            owned_user = [obj.assign_by] if (int(login_user) == obj.assign_to.id) and not (obj.assign_by == obj.assign_to) else login_user_and_reporting_heads
            
            report_date=ETaskReportingDates.objects.filter(reporting_date__date__lte=cur_date,task_type=1,task=obj.id,reporting_status=2,
                        owned_by__in=owned_user,is_deleted=False).order_by('reporting_date')
            reporting_date_list = []
            for rd in report_date:
                etask_sub_assign = EtaskTaskSubAssignLog.objects.filter(task=obj,sub_assign=login_user,is_deleted=False).first()
                reporting_to_name = etask_sub_assign.assign_from.get_full_name() if etask_sub_assign else obj.assign_by.get_full_name()
                reporting_by_name = etask_sub_assign.sub_assign.get_full_name() if etask_sub_assign else obj.assign_to.get_full_name()
                
                reporting_to = etask_sub_assign.assign_from.id if etask_sub_assign else obj.assign_by.id
                reporting_by = etask_sub_assign.sub_assign.id if etask_sub_assign else obj.assign_to.id

                reporting_date_list.append({
                    'id':rd.id,
                    'reporting_date':rd.reporting_date,
                    'reporting_to_name':reporting_to_name,
                    'reporting_by_name':reporting_by_name,
                    'reporting_to':reporting_to,
                    'reporting_by':reporting_by
                })


            report_date_owner=ETaskReportingDates.objects.filter(reporting_date__date__lte=cur_date,task_type=1,task=obj.id,reporting_status=2,
                        owned_by=login_user,is_deleted=False).order_by('reporting_date')
            
            for rd in report_date_owner:
                etask_sub_assign = EtaskTaskSubAssignLog.objects.filter(task=obj,assign_from=login_user,is_deleted=False).first()
                reporting_to_name = etask_sub_assign.assign_from.get_full_name() if etask_sub_assign else obj.assign_by.get_full_name()
                reporting_by_name = etask_sub_assign.sub_assign.get_full_name() if etask_sub_assign else obj.assign_to.get_full_name()
                
                reporting_to = etask_sub_assign.assign_from.id if etask_sub_assign else obj.assign_by.id
                reporting_by = etask_sub_assign.sub_assign.id if etask_sub_assign else obj.assign_to.id

                reporting_date_list.append({
                    'id':rd.id,
                    'reporting_date':rd.reporting_date,
                    'reporting_to_name':reporting_to_name,
                    'reporting_by_name':reporting_by_name,
                    'reporting_to':reporting_to,
                    'reporting_by':reporting_by
                })
            return reporting_date_list


class TodayReportingDetailsPerUserDownloadSerializerV2(serializers.ModelSerializer):
    reporting_dates=serializers.SerializerMethodField()

    class Meta:
        model=EtaskTask
        fields=('id','task_code_id','task_subject','task_description','assign_by','assign_to','sub_assign_to_user','reporting_dates','owner')

    def get_reporting_dates(self,obj):
        # if EtaskTask.id:
        #     report_date_list = ''
        #     cur_date = datetime.now().date()
        #     login_user = self.context.get("login_user")
        #     login_user_and_reporting_heads = get_user_reporting_heads(user=login_user)
        #     login_user_and_reporting_heads.append(int(login_user))
        #     report_date=ETaskReportingDates.objects.filter(reporting_date__date__lte=cur_date,task_type=1,task=obj.id,reporting_status=2,
        #                 owned_by__in=login_user_and_reporting_heads,is_deleted=False).order_by('reporting_date')
        #     if report_date:
        #         for dt in report_date:
        #             report_date_list += '{}, '.format(dt.reporting_date.strftime("%d %b %Y"))                            
        #         return report_date_list[:-2]
        #     else:
        #         return ''
        cur_date = datetime.now().date()
        if obj.id:
            login_user = self.context.get("login_user")
            # login_user_and_reporting_heads = get_user_reporting_heads(user=login_user)
            # login_user_and_reporting_heads.append(login_user.id)
            login_user_and_reporting_heads = list(EtaskTaskSubAssignLog.objects.filter(task=obj,sub_assign=login_user,is_deleted=False).values_list('assign_from',flat=True))
            owned_user = [obj.assign_by] if (int(login_user) == obj.assign_to.id) and not (obj.assign_by == obj.assign_to) else login_user_and_reporting_heads
            
            report_date=ETaskReportingDates.objects.filter(reporting_date__date__lte=cur_date,task_type=1,task=obj.id,reporting_status=2,
                        owned_by__in=owned_user,is_deleted=False).order_by('reporting_date')
            reporting_date_list = []
            for rd in report_date:
                etask_sub_assign = EtaskTaskSubAssignLog.objects.filter(task=obj,sub_assign=login_user,is_deleted=False).first()
                reporting_to_name = etask_sub_assign.assign_from.get_full_name() if etask_sub_assign else obj.assign_by.get_full_name()
                reporting_by_name = etask_sub_assign.sub_assign.get_full_name() if etask_sub_assign else obj.assign_to.get_full_name()
                
                reporting_to = etask_sub_assign.assign_from.id if etask_sub_assign else obj.assign_by.id
                reporting_by = etask_sub_assign.sub_assign.id if etask_sub_assign else obj.assign_to.id

                reporting_date_list.append(rd.reporting_date.strftime("%d %b %Y"))


            report_date_owner=ETaskReportingDates.objects.filter(reporting_date__date__lte=cur_date,task_type=1,task=obj.id,reporting_status=2,
                        owned_by=login_user,is_deleted=False).order_by('reporting_date')
            
            for rd in report_date_owner:
                etask_sub_assign = EtaskTaskSubAssignLog.objects.filter(task=obj,assign_from=login_user,is_deleted=False).first()
                reporting_to_name = etask_sub_assign.assign_from.get_full_name() if etask_sub_assign else obj.assign_by.get_full_name()
                reporting_by_name = etask_sub_assign.sub_assign.get_full_name() if etask_sub_assign else obj.assign_to.get_full_name()
                
                reporting_to = etask_sub_assign.assign_from.id if etask_sub_assign else obj.assign_by.id
                reporting_by = etask_sub_assign.sub_assign.id if etask_sub_assign else obj.assign_to.id

                reporting_date_list.append(rd.reporting_date.strftime("%d %b %Y"))
            return ', '.join(reporting_date_list)


class UpcomingReportingDetailsPerUserSerializer(serializers.ModelSerializer):
    reporting_dates=serializers.SerializerMethodField()
    class Meta:
        model=EtaskTask
        fields=('id','task_code_id','task_subject','assign_by','assign_to','sub_assign_to_user','reporting_dates','owner')
    def get_reporting_dates(self,EtaskTask):
        cur_date = datetime.now().date()
        if EtaskTask.id:
            report_date=list(ETaskReportingDates.objects.filter(reporting_date__date__gt=cur_date,task_type=1,task=EtaskTask.id,
                                                                is_deleted=False).values('reporting_date'))
            return report_date


class UpcomingReportingDetailsPerUserSerializerV2(serializers.ModelSerializer):
    reporting_dates=serializers.SerializerMethodField()
    parent_task=serializers.SerializerMethodField(required=False)
    sub_tasks = serializers.SerializerMethodField()

    class Meta:
        model=EtaskTask
        fields=('id','parent_id','parent_task','task_code_id','task_subject','assign_by','assign_to','sub_assign_to_user','reporting_dates',
                'owner','extended_date','end_date','requested_end_date','sub_tasks')
    
    def get_sub_tasks(self, obj):
        sub_tasks_data = EtaskTask.objects.filter(~Q(task_status=4),parent_id=obj.id,is_deleted=False).values('id','task_subject')
        return sub_tasks_data if sub_tasks_data else list() 

    def get_parent_task(self,obj):
        if obj.parent_id !=0:
            if EtaskTask.objects.filter(id=obj.parent_id):
                parent_data=EtaskTask.objects.filter(id=obj.parent_id).values('id','task_subject','task_description')[0]
                return parent_data

    def get_reporting_dates(self,EtaskTask):
        cur_date = datetime.now().date()
        if EtaskTask.id:
            login_user = self.context.get("login_user")
            # login_user_and_reporting_heads = get_user_reporting_heads(user=login_user)
            # login_user_and_reporting_heads.append(login_user.id)
            login_user_and_reporting_heads = list(EtaskTaskSubAssignLog.objects.filter(task=EtaskTask,sub_assign=login_user,is_deleted=False).values_list('assign_from',flat=True))
            owned_user = [EtaskTask.assign_by] if (int(login_user) == EtaskTask.assign_to.id) and not (EtaskTask.assign_by == EtaskTask.assign_to) else login_user_and_reporting_heads
            #owned_user.append(login_user)
            report_date=ETaskReportingDates.objects.filter(reporting_date__date__gt=cur_date,task_type=1,task=EtaskTask.id,
                        owned_by__in=owned_user,is_deleted=False).order_by('reporting_date')
            reporting_date_list = []
            for rd in report_date:
                etask_sub_assign = EtaskTaskSubAssignLog.objects.filter(task=EtaskTask,sub_assign=login_user,is_deleted=False).first()
                reporting_to_name = etask_sub_assign.assign_from.get_full_name() if etask_sub_assign else EtaskTask.assign_by.get_full_name()
                reporting_by_name = etask_sub_assign.sub_assign.get_full_name() if etask_sub_assign else EtaskTask.assign_to.get_full_name()
                
                reporting_to = etask_sub_assign.assign_from.id if etask_sub_assign else EtaskTask.assign_by.id
                reporting_by = etask_sub_assign.sub_assign.id if etask_sub_assign else EtaskTask.assign_to.id

                reporting_date_list.append({
                    'id':rd.id,
                    'reporting_date':rd.reporting_date,
                    'reporting_to_name':reporting_to_name,
                    'reporting_by_name':reporting_by_name,
                    'reporting_to':reporting_to,
                    'reporting_by':reporting_by
                })


            report_date_owner=ETaskReportingDates.objects.filter(reporting_date__date__gt=cur_date,task_type=1,task=EtaskTask.id,
                        owned_by=login_user,is_deleted=False).order_by('reporting_date')
            
            for rd in report_date_owner:
                etask_sub_assign = EtaskTaskSubAssignLog.objects.filter(task=EtaskTask,assign_from=login_user,is_deleted=False).first()
                reporting_to_name = etask_sub_assign.assign_from.get_full_name() if etask_sub_assign else EtaskTask.assign_by.get_full_name()
                reporting_by_name = etask_sub_assign.sub_assign.get_full_name() if etask_sub_assign else EtaskTask.assign_to.get_full_name()
                
                reporting_to = etask_sub_assign.assign_from.id if etask_sub_assign else EtaskTask.assign_by.id
                reporting_by = etask_sub_assign.sub_assign.id if etask_sub_assign else EtaskTask.assign_to.id

                reporting_date_list.append({
                    'id':rd.id,
                    'reporting_date':rd.reporting_date,
                    'reporting_to_name':reporting_to_name,
                    'reporting_by_name':reporting_by_name,
                    'reporting_to':reporting_to,
                    'reporting_by':reporting_by
                })

            return reporting_date_list


class UpcomingReportingDetailsPerUserDownloadSerializerV2(serializers.ModelSerializer):
    reporting_dates=serializers.SerializerMethodField()
    class Meta:
        model=EtaskTask
        fields=('id','task_code_id','task_subject','task_description','assign_by','assign_to','sub_assign_to_user','reporting_dates','owner')
    def get_reporting_dates(self,EtaskTask):
        # if EtaskTask.id:
        #     login_user = self.context.get("login_user")
        #     login_user_and_reporting_heads = get_user_reporting_heads(user=login_user)
        #     login_user_and_reporting_heads.append(int(login_user))
        #     cur_date = datetime.now().date()
        #     report_date_list = ''
        #     report_date=ETaskReportingDates.objects.filter(reporting_date__date__gt=cur_date,task_type=1,task=EtaskTask.id,
        #                 owned_by__in=login_user_and_reporting_heads,is_deleted=False).order_by('reporting_date')
        #     if report_date:
        #         for dt in report_date:
        #             report_date_list += '{}, '.format(dt.reporting_date.strftime("%d %b %Y %I:%M %p"),dt.get_reporting_status_display())                            
        #         return report_date_list[:-2]
        #     else:
        #         return ''

        cur_date = datetime.now().date()
        if EtaskTask.id:
            login_user = self.context.get("login_user")
            # login_user_and_reporting_heads = get_user_reporting_heads(user=login_user)
            # login_user_and_reporting_heads.append(login_user.id)
            login_user_and_reporting_heads = list(EtaskTaskSubAssignLog.objects.filter(task=EtaskTask,sub_assign=login_user,is_deleted=False).values_list('assign_from',flat=True))
            owned_user = [EtaskTask.assign_by] if (int(login_user) == EtaskTask.assign_to.id) and not (EtaskTask.assign_by == EtaskTask.assign_to) else login_user_and_reporting_heads
            #owned_user.append(login_user)
            report_date=ETaskReportingDates.objects.filter(reporting_date__date__gt=cur_date,task_type=1,task=EtaskTask.id,
                        owned_by__in=owned_user,is_deleted=False).order_by('reporting_date')
            reporting_date_list = []
            for rd in report_date:
                etask_sub_assign = EtaskTaskSubAssignLog.objects.filter(task=EtaskTask,sub_assign=login_user,is_deleted=False).first()
                reporting_to_name = etask_sub_assign.assign_from.get_full_name() if etask_sub_assign else EtaskTask.assign_by.get_full_name()
                reporting_by_name = etask_sub_assign.sub_assign.get_full_name() if etask_sub_assign else EtaskTask.assign_to.get_full_name()
                
                reporting_to = etask_sub_assign.assign_from.id if etask_sub_assign else EtaskTask.assign_by.id
                reporting_by = etask_sub_assign.sub_assign.id if etask_sub_assign else EtaskTask.assign_to.id

                reporting_date_list.append(rd.reporting_date.strftime("%d %b %Y %I:%M %p"))


            report_date_owner=ETaskReportingDates.objects.filter(reporting_date__date__gt=cur_date,task_type=1,task=EtaskTask.id,
                        owned_by=login_user,is_deleted=False).order_by('reporting_date')
            
            for rd in report_date_owner:
                etask_sub_assign = EtaskTaskSubAssignLog.objects.filter(task=EtaskTask,assign_from=login_user,is_deleted=False).first()
                reporting_to_name = etask_sub_assign.assign_from.get_full_name() if etask_sub_assign else EtaskTask.assign_by.get_full_name()
                reporting_by_name = etask_sub_assign.sub_assign.get_full_name() if etask_sub_assign else EtaskTask.assign_to.get_full_name()
                
                reporting_to = etask_sub_assign.assign_from.id if etask_sub_assign else EtaskTask.assign_by.id
                reporting_by = etask_sub_assign.sub_assign.id if etask_sub_assign else EtaskTask.assign_to.id

                reporting_date_list.append(rd.reporting_date.strftime("%d %b %Y %I:%M %p"))

            return ', '.join(reporting_date_list)


class OverdueReportingDetailsPerUserSerializer(serializers.ModelSerializer):
    reporting_dates=serializers.SerializerMethodField()
    class Meta:
        model=EtaskTask
        fields=('id','task_code_id','task_subject','assign_by','assign_to','sub_assign_to_user','reporting_dates','owner')
    def get_reporting_dates(self,EtaskTask):
        cur_date = datetime.now().date()
        if EtaskTask.id:
            report_date=list(ETaskReportingDates.objects.filter(reporting_date__date__lt=cur_date,task_type=1,task=EtaskTask.id,
                                                                is_deleted=False).values('reporting_date'))
            return report_date

class TodayReportingMarkDateReportedSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    completed_status = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = ETaskReportingDates
        fields = '__all__'
    def update(self, instance, validated_data):
        current_date = datetime.now()
        # #print('current_date-->',current_date)
        updated_by = validated_data.get('updated_by')
        instance.task_type = 1
        instance.task_status=1
        instance.reporting_status = 1
        instance.actual_reporting_date = current_date
        instance.updated_by = updated_by
        instance.save()
        prev_action= ETaskReportingActionLog.objects.filter(
            task_id = instance.task,
            reporting_date_id = instance.id,
            is_deleted=False
            ).update(is_deleted=True)
        reporting_log = ETaskReportingActionLog.objects.create(
            task_id = instance.task,
            reporting_date_id = instance.id,
            status = 1,
            updated_by = updated_by
            )
        # #print('reporting_log-->',reporting_log)
        return instance
        

class TodayAppointmenDetailsPerUserSerializer(serializers.ModelSerializer):
    # appointment = serializers.CharField(required=False)
    class Meta:
        model=EtaskAppointment
        fields='__all__'


class UpcomingAppointmenDetailsPerUserSerializerV2(serializers.ModelSerializer):
    # appointment = serializers.CharField(required=False)
    class Meta:
        model=EtaskAppointment
        fields='__all__'


class UpcomingAppointmenDetailsPerUserDownloadSerializerV2(serializers.ModelSerializer):
    start_date = serializers.SerializerMethodField(required=False)
    end_date = serializers.SerializerMethodField(required=False)

    def get_start_date(self, obj):
        return obj.start_date.strftime("%d %b %Y %I:%M %p") if obj.start_date else ''

    def get_end_date(self, obj):
        return obj.end_date.strftime("%d %b %Y %I:%M %p") if obj.end_date else ''

    class Meta:
        model=EtaskAppointment
        fields='__all__'


class TodayAppointmenDetailsPerUserSerializerV2(serializers.ModelSerializer):
    # appointment = serializers.CharField(required=False)
    class Meta:
        model=EtaskAppointment
        fields='__all__'



class EtaskAppointmentDetailsSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField(required=False)
    internal_invite = serializers.SerializerMethodField(required=False)
    external_invites = serializers.SerializerMethodField(required=False)
    
    class Meta:
        model=EtaskAppointment
        fields='__all__'
        extra_fields = ('created_by_name','internal_invite','external_invites')

    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else ''

    def get_internal_invite(self,obj):
        internal_invite = EtaskInviteEmployee.objects.filter(appointment=obj,is_deleted=False).values('user')
        return [{'user_id':user_d['user'],'user_name':userdetails(user_d['user'])} for user_d in internal_invite]
        
    def get_external_invites(self,obj):
        return EtaskInviteExternalPeople.objects.filter(appointment=obj,is_deleted=False).values('external_people','external_email')

class TodayAppointmenDetailsPerUserDownloadSerializerV2(serializers.ModelSerializer):
    Appointment_status=serializers.CharField(source='get_Appointment_status_display')
    start_date = serializers.SerializerMethodField(required=False)
    end_date = serializers.SerializerMethodField(required=False)

    def get_start_date(self, obj):
        return obj.start_date.strftime("%d %b %Y %I:%M %p") if obj.start_date else ''

    def get_end_date(self, obj):
        return obj.end_date.strftime("%d %b %Y %I:%M %p") if obj.end_date else ''

    class Meta:
        model=EtaskAppointment
        fields='__all__'


class TodayAppoinmentMarkCompletedSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = EtaskAppointment
        fields = '__all__'
    def update(self, instance, validated_data):
        # #print('current_date-->',current_date)
        updated_by = validated_data.get('updated_by')
        instance.Appointment_status = 'completed'
        instance.updated_at = datetime.now()
        instance.updated_by = updated_by
        instance.save()

        return instance
#:::::::::::::::::::::::::::::::::::::: TASK TRANSFER ::::::::::::::::::::::::::::::::::::::::::::::::#
class ETaskMassTaskTransferSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    transferred_task=serializers.ListField(required=False)
    user=serializers.CharField(required=False)
    tranferred_from=serializers.CharField(required=False)
    class Meta:
        model = EtaskTask
        fields = ('id','updated_by','transferred_task','user','tranferred_from')
    def create(self,validated_data):
        try:
            cur_date=datetime.now()
            updated_by = validated_data.get('updated_by')
            transferred_task=validated_data.get('transferred_task')
            #print('transferred_task', transferred_task)
            user=validated_data.get('user')
            tranferred_from=validated_data.get('tranferred_from')
            #print('user',user,type(user))
            if transferred_task:
                for data in validated_data.get('transferred_task'):
                    #======================= log ====================================#
                    transferred_task_log = EtaskTaskTransferLog.objects.create(task_id=data['id'],transferred_from_id=tranferred_from,
                                                                                transferred_to_id=user,transfer_date=cur_date,
                                                                                created_by=updated_by,owned_by=updated_by)

                    #################################################################
                    all_transferred_task = EtaskTask.objects.filter(id=data['id'],is_deleted=False).update(assign_to=user,date_of_transfer=cur_date,
                                        is_transferred=True,sub_assign_to_user=None,transferred_from=tranferred_from,updated_by=updated_by)
                    #print("all_transferred_task",type(all_transferred_task),all_transferred_task)
                    ####################################################################
                    task_details = EtaskTask.objects.get(id=data['id'],is_deleted=False)
                    reporting_date = ETaskReportingDates.objects.filter(task=task_details.id,task_type=1,reporting_status=2,
                                        reporting_date__date__gt=cur_date).values('reporting_date')
                    #print("reporting_date",reporting_date)
                    reporting_date_list = []
                    # #print("task_create",task_create.__dict__['id'])
                    # #print("r_date['reporting_date']",r_date['reporting_date'])
                    reporting_date_str = """"""
                    r_time = ''
                    ics_data = """BEGIN:VCALENDAR
VERSION:2.0
CALSCALE:GREGORIAN\n"""
                    #print("validated_data['sub_assign_to_user']",task_details.assign_to)
                    user_name = userdetails(task_details.assign_to.id)
                    count_id = 0
                    for r_date in reporting_date:
                        #print("r_date['reporting_date']",r_date['reporting_date'])
                        count_id += 1
                        reporting_date_str += str(count_id)+'. '+r_date['reporting_date'].strftime("%m/%d/%Y, %I:%M:%S %p")+" "
                        r_time = r_date['reporting_date'].strftime("%Y%m%dT%H%M%S")
                        ics_data +=   """BEGIN:VEVENT
SUMMARY:Reporting of {rep_sub}
DTSTART;TZID=Asia/Kolkata:{r_time}
LOCATION:Shyam Tower,Kolkata-700091
DESCRIPTION: Reporting dates.
STATUS:CONFIRMED
SEQUENCE:3
BEGIN:VALARM
TRIGGER:-PT10M
DESCRIPTION:Pickup Reminder
ACTION:DISPLAY
END:VALARM
END:VEVENT\n""".replace("{r_time}",r_time).replace("{rep_sub}",task_details.task_subject)

                    #DTEND;TZID=Asia/Kolkata:{r_time}
                    ics_data += "END:VCALENDAR"
                    #print("reporting_date_str",reporting_date_str)
                    user_email = User.objects.get(id= task_details.assign_to.id).cu_user.cu_alt_email_id
                    #print("user_email",user_email)
                    
                    if user_email:
                        mail_data = {
                                    "recipient_name" : user_name,        ## modified by manas Paul 21jan20
                                    "task_subject": task_details.task_subject,
                                    "reporting_date": reporting_date_str,
                                }
                        # #print('mail_data',mail_data)
                        # #print('mail_id-->',mail)
                        # #print('mail_id-->',[mail])
                        # mail_class = GlobleMailSend('ETAP', email_list)
                        # mail_class = GlobleMailSend('ETRDC', [user_email])
                        # #print('mail_class',mail_class)
                        # mail_thread = Thread(target = mail_class.mailsend, args = (mail_data,ics_data))
                        # #print('mail_thread-->',mail_thread)
                        # mail_thread.start()

                        send_mail_list('ETRDC', [user_email], mail_data, ics=ics_data)

                    ######################################  

            return validated_data
        except Exception as e:
            raise e


class ETaskMassTaskTransferSerializerV2(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    transferred_task=serializers.ListField(required=False)
    user=serializers.CharField(required=False)
    tranferred_from=serializers.CharField(required=False)

    class Meta:
        model = EtaskTask
        fields = ('id','updated_by','transferred_task','user','tranferred_from')

    def get_task_assign_flow(self, task=None):
        assign_user = [task.assign_by,task.assign_to]
        if task.sub_assign_to_user:
            sub_assign_uaers = EtaskTaskSubAssignLog.objects.filter(task=task,is_deleted=False)
            for sub_assign_uaer in sub_assign_uaers:
                assign_user.append(sub_assign_uaer.sub_assign)
        return assign_user

    def create(self,validated_data):
        with transaction.atomic():
            cur_date=datetime.now()
            updated_by = validated_data.get('updated_by')
            transferred_task=validated_data.get('transferred_task')
            #print('transferred_task', transferred_task)
            user=validated_data.get('user')
            tranferred_from=validated_data.get('tranferred_from')
            #print('user',user,type(user))
            if transferred_task:
                error_list = list()
                transfer_to = User.objects.get(id=user)
                transfer_from = User.objects.get(id=int(tranferred_from))
                for data in validated_data.get('transferred_task'):
                    transferable_task = EtaskTask.objects.filter(id=data['id'],is_deleted=False).first()
                    assign_user_list = self.get_task_assign_flow(task=transferable_task)
                    etask_sub_assign = EtaskTaskSubAssignLog.objects.filter(task=transferable_task,assign_from=tranferred_from,is_deleted=False).first()
                    reporting_heads = get_user_reporting_heads(user=etask_sub_assign.sub_assign) if etask_sub_assign else []
                    if transfer_to in assign_user_list or (etask_sub_assign and transfer_to.id not in reporting_heads):
                        error_list.append(transferable_task.task_code_id)
                    
                msg = 'Task with {} can not be transfered to {}'.format(', '.join(error_list),transfer_to.get_full_name())

                if error_list:
                    raise APIException({'request_status': 0, 'msg': msg})

                for data in validated_data.get('transferred_task'):
                    #======================= log ====================================#
                    sub_assign_assign_from = EtaskTaskSubAssignLog.objects.filter(task=transferable_task,assign_from=tranferred_from,is_deleted=False).update(assign_from=transfer_to)
                    sub_assign_assign_to = EtaskTaskSubAssignLog.objects.filter(task=transferable_task,sub_assign=tranferred_from,is_deleted=False).update(sub_assign=transfer_to)
                    
                    transferred_task_log = EtaskTaskTransferLog.objects.create(task_id=data['id'],transferred_from_id=tranferred_from,
                                                                                transferred_to_id=user,transfer_date=cur_date,
                                                                                created_by=updated_by,owned_by=updated_by)

                    task_details = EtaskTask.objects.get(id=data['id'])
                    task_details.assign_to = transfer_to if task_details.assign_to == transfer_from else task_details.assign_to
                    task_details.date_of_transfer=cur_date
                    task_details.is_transferred=True
                    task_details.sub_assign_to_user=transfer_to if task_details.sub_assign_to_user == transfer_from else task_details.sub_assign_to_user
                    task_details.transferred_from=transfer_from
                    task_details.updated_by=updated_by
                    task_details.save()

                    reporting_date = ETaskReportingDates.objects.filter(task=task_details.id,task_type=1,reporting_status=2,
                                        reporting_date__date__gt=cur_date).values('reporting_date')
                    mail_reporting_date_list = [r_date['reporting_date'].strftime("%d/%m/%Y, %I:%M:%S %p") for r_date in reporting_date]
                    cc_name_list = [u_cc.user.get_full_name() for u_cc in EtaskUserCC.objects.filter(task=task_details,is_deleted=False)]
                    reporting_date_list = []
                    reporting_date_str = """"""
                    r_time = ''
                    ics_data = """BEGIN:VCALENDAR
VERSION:2.0
CALSCALE:GREGORIAN\n"""
                    user_name = transfer_to.get_full_name()
                    count_id = 0
                    for r_date in reporting_date:
                        count_id += 1
                        reporting_date_str += str(count_id)+'. '+r_date['reporting_date'].strftime("%m/%d/%Y, %I:%M:%S %p")+" "
                        r_time = r_date['reporting_date'].strftime("%Y%m%dT%H%M%S")
                        ics_data +=   """BEGIN:VEVENT
SUMMARY:Reporting of {rep_sub}
DTSTART;TZID=Asia/Kolkata:{r_time}
LOCATION:Shyam Tower,Kolkata-700091
DESCRIPTION: Reporting dates.
STATUS:CONFIRMED
SEQUENCE:3
BEGIN:VALARM
TRIGGER:-PT10M
DESCRIPTION:Pickup Reminder
ACTION:DISPLAY
END:VALARM
END:VEVENT\n""".replace("{r_time}",r_time).replace("{rep_sub}",task_details.task_subject)

                    ics_data += "END:VCALENDAR"
                    user_email = transfer_to.cu_user.cu_alt_email_id
                    
                    if user_email:
                        mail_data = {
                                    "recipient_name" : user_name,        ## modified by manas Paul 21jan20
                                    "task_subject": task_details.task_subject,
                                    "reporting_date": mail_reporting_date_list,
                                    "assign_to_name": transfer_to.get_full_name(),
                                    "on_behalf_of": task_details.assign_by.get_full_name() if task_details.task_categories==2 else None,
                                    "created_by_name": task_details.created_by.get_full_name(),
                                    "created_date_time": task_details.created_at,
                                    "cc_to":','.join(cc_name_list),
                                    "task_priority": task_details.get_task_priority_display(),
                                    "start_date": task_details.start_date.date(),
                                    "end_date": task_details.end_date.date()
                                }
                        # mail_class = GlobleMailSend('ETRDC', [user_email])
                        # mail_thread = Thread(target = mail_class.mailsend, args = (mail_data,ics_data))
                        # mail_thread.start()
                        send_mail_list('ETRDC', [user_email], mail_data, ics=ics_data)
                    ######################################  

            return validated_data


class ETaskOwnershipTransferSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    transferred_task=serializers.ListField(required=False)
    user=serializers.CharField(required=False)
    tranferred_from=serializers.CharField(required=False)

    class Meta:
        model = EtaskTask
        fields = ('id','updated_by','transferred_task','user','tranferred_from')
    def create(self,validated_data):
        with transaction.atomic():
            cur_date=datetime.now()
            updated_by = validated_data.get('updated_by')
            transferred_task=validated_data.get('transferred_task')
            #print('transferred_task', transferred_task)
            user=validated_data.get('user')
            tranferred_from=validated_data.get('tranferred_from')
            #print('user',user,type(user))
            if transferred_task:
                error_list = list()
                transfer_to = User.objects.get(id=user)
                for data in validated_data.get('transferred_task'):
                    transferable_task = EtaskTask.objects.filter(id=data['id'],is_deleted=False).first()
                    reporting_heads = get_user_reporting_heads(user=transferable_task.assign_to)
                    if transfer_to.id not in reporting_heads:
                        error_list.append(transferable_task.task_code_id)

                msg = 'Task with {} can not be transfered to {}'.format(', '.join(error_list),transfer_to.get_full_name())

                if error_list:
                    raise APIException({'request_status': 0, 'msg': msg})

                for data in validated_data.get('transferred_task'):
                    #======================= log ====================================#
                    transferred_task_log = EtaskTaskOwnershipTransferLog.objects.create(task_id=data['id'],
                                                                            ownership_transferred_from_id=tranferred_from,
                                                                            ownership_transferred_to_id=user,
                                                                            created_by=updated_by)

                    #################################################################
                    all_transferred_task = EtaskTask.objects.filter(id=data['id'],is_deleted=False).update(assign_by=user,
                                                                    updated_by=updated_by,owner=user,owned_by=user)
                    #print("all_transferred_task",type(all_transferred_task),all_transferred_task)
                    ####################################################################
                    task_details = EtaskTask.objects.get(id=data['id'],is_deleted=False)
                    reporting_date_query = ETaskReportingDates.objects.filter(task=task_details.id,task_type=1,reporting_status=2,
                                        reporting_date__date__gt=cur_date,owned_by=tranferred_from)
                    reporting_date = reporting_date_query.values('reporting_date')
                    reporting_date_query.update(owned_by=user)

                    #print("reporting_date",reporting_date)
                    reporting_date_list = []
                    # #print("task_create",task_create.__dict__['id'])
                    # #print("r_date['reporting_date']",r_date['reporting_date'])
                    reporting_date_str = """"""
                    r_time = ''
                    ics_data = """BEGIN:VCALENDAR
VERSION:2.0
CALSCALE:GREGORIAN\n"""
                    #print("validated_data['sub_assign_to_user']",task_details.assign_to)
                    user_name = userdetails(task_details.assign_to.id)
                    count_id = 0
                    for r_date in reporting_date:
                        #print("r_date['reporting_date']",r_date['reporting_date'])
                        count_id += 1
                        reporting_date_str += str(count_id)+'. '+r_date['reporting_date'].strftime("%m/%d/%Y, %I:%M:%S %p")+" "
                        r_time = r_date['reporting_date'].strftime("%Y%m%dT%H%M%S")
                        ics_data +=   """BEGIN:VEVENT
SUMMARY:Reporting of {rep_sub}
DTSTART;TZID=Asia/Kolkata:{r_time}
LOCATION:Shyam Tower,Kolkata-700091
DESCRIPTION: Reporting dates.
STATUS:CONFIRMED
SEQUENCE:3
BEGIN:VALARM
TRIGGER:-PT10M
DESCRIPTION:Pickup Reminder
ACTION:DISPLAY
END:VALARM
END:VEVENT\n""".replace("{r_time}",r_time).replace("{rep_sub}",task_details.task_subject)

                    #DTEND;TZID=Asia/Kolkata:{r_time}
                    ics_data += "END:VCALENDAR"
                    #print("reporting_date_str",reporting_date_str)
                    user_email = User.objects.get(id= task_details.assign_to.id).cu_user.cu_alt_email_id
                    #print("user_email",user_email)
                    
                    if user_email:
                        mail_data = {
                                    "recipient_name" : user_name,        ## modified by manas Paul 21jan20
                                    "task_subject": task_details.task_subject,
                                    "reporting_date": reporting_date_str,
                                }
                        # #print('mail_data',mail_data)
                        # #print('mail_id-->',mail)
                        # #print('mail_id-->',[mail])
                        # mail_class = GlobleMailSend('ETAP', email_list)
                        # mail_class = GlobleMailSend('ETRDC', [user_email])
                        # #print('mail_class',mail_class)
                        # mail_thread = Thread(target = mail_class.mailsend, args = (mail_data,ics_data))
                        # #print('mail_thread-->',mail_thread)
                        # mail_thread.start()

                        send_mail_list('ETRDC', [user_email],mail_data, ics=ics_data)

                    ######################################  

            return validated_data



class ETaskTeamTransferTasksListSerializer(serializers.ModelSerializer):
    parent_task=serializers.SerializerMethodField(required=False)
    sub_data = EtaskTask.objects.filter(parent_id=0,is_deleted=False)
    task_type_name=serializers.CharField(source='get_task_type_display')
    recurrance_frequency_name=serializers.CharField(source='get_recurrance_frequency_display')
    task_status_name=serializers.CharField(source='get_task_status_display')
    task_priority_name=serializers.CharField(source='get_task_priority_display')
    assign_by_name = serializers.SerializerMethodField()
    assign_to_name= serializers.SerializerMethodField()
    sub_assign_to_user_name= serializers.SerializerMethodField()
    reporting_dates=serializers.SerializerMethodField()
    sub_tasks = serializers.SerializerMethodField()

    class Meta:
        model = EtaskTask
        fields = ('__all__')
        extra_fields = ('sub_tasks',)

    def get_sub_tasks(self, obj):
        sub_tasks_data = EtaskTask.objects.filter(~Q(task_status=4),parent_id=obj.id,is_deleted=False).values('id','task_subject')
        return sub_tasks_data if sub_tasks_data else list() 

    def get_parent_task(self,EtaskTask):
        if EtaskTask.parent_id:
            if EtaskTask.parent_id !=0:
                if self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject','task_description'):
                    parent_data=self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject','task_description')[0]
                    return parent_data

    def user_name(self, user_id):
        name = None
        full_name = ""
        name = User.objects.get(id=user_id)
        if name:
            full_name =  name.__dict__['first_name']+" "+name.__dict__['last_name']
        return full_name

    def get_assign_by_name(self,EtaskTask):
        name = None
        full_name = ""
        if EtaskTask.assign_by:
            name = User.objects.get(id=EtaskTask.assign_by.id)
            if name:
                full_name =  name.__dict__['first_name']+" "+name.__dict__['last_name']
                # #print("full_name",full_name)
            return full_name

    def get_sub_assign_to_user_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.sub_assign_to_user:
            name=User.objects.get(id=EtaskTask.sub_assign_to_user.id)
            if name:
                full_name= name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name

    def get_assign_to_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.assign_to:
            name =User.objects.get(id=EtaskTask.assign_to.id)
            if name:
                full_name=name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name

    def get_reporting_dates(self,EtaskTask):
        if EtaskTask.id:
            report_date_list = []
            report_date=ETaskReportingDates.objects.filter(task_type=1,task=EtaskTask.id,is_deleted=False)
            # #print("report_date",report_date)
            if report_date:
                for dt in report_date:
                    dt_dict={
                        'id':dt.id,
                        'reporting_date':dt.reporting_date,
                    }
                    report_date_list.append(dt_dict)                             
                return report_date_list
            else:
                return []


class ETaskTeamOwnershipTransferredListSerializer(serializers.ModelSerializer):
    parent_task=serializers.SerializerMethodField(required=False)
    sub_data = EtaskTask.objects.filter(parent_id=0,is_deleted=False)
    task_type_name=serializers.CharField(source='get_task_type_display')
    recurrance_frequency_name=serializers.CharField(source='get_recurrance_frequency_display')
    task_status_name=serializers.CharField(source='get_task_status_display')
    task_priority_name=serializers.CharField(source='get_task_priority_display')
    assign_by_name = serializers.SerializerMethodField()
    assign_to_name= serializers.SerializerMethodField()
    sub_assign_to_user_name= serializers.SerializerMethodField()
    reporting_dates=serializers.SerializerMethodField()
    sub_tasks = serializers.SerializerMethodField()
    date_of_ownership_transfer = serializers.SerializerMethodField()
    ownership_transferred_from_name = serializers.SerializerMethodField()

    class Meta:
        model = EtaskTask
        fields = ('__all__')
        extra_fields = ('sub_tasks','date_of_ownership_transfer','ownership_transferred_from_name',)

    def get_ownership_transferred_from_name(self,obj):
        login_user = self.context.get("login_user")
        ownerhip_log = EtaskTaskOwnershipTransferLog.objects.filter(created_by=login_user,task=obj,is_deleted=False).order_by('-id')
        return ownerhip_log.first().ownership_transferred_from.get_full_name() if ownerhip_log.first() else ''

    def get_date_of_ownership_transfer(self,obj):
        login_user = self.context.get("login_user")
        ownerhip_log = EtaskTaskOwnershipTransferLog.objects.filter(created_by=login_user,task=obj,is_deleted=False).order_by('-id')
        return ownerhip_log.first().created_at if ownerhip_log.first() else ''

    def get_sub_tasks(self, obj):
        sub_tasks_data = EtaskTask.objects.filter(~Q(task_status=4),parent_id=obj.id,is_deleted=False).values('id','task_subject')
        return sub_tasks_data if sub_tasks_data else list() 

    def get_parent_task(self,EtaskTask):
        if EtaskTask.parent_id:
            if EtaskTask.parent_id !=0:
                if self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject','task_description'):
                    parent_data=self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject','task_description')[0]
                    return parent_data

    def user_name(self, user_id):
        name = None
        full_name = ""
        name = User.objects.get(id=user_id)
        if name:
            full_name =  name.__dict__['first_name']+" "+name.__dict__['last_name']
        return full_name

    def get_assign_by_name(self,EtaskTask):
        name = None
        full_name = ""
        if EtaskTask.assign_by:
            name = User.objects.get(id=EtaskTask.assign_by.id)
            if name:
                full_name =  name.__dict__['first_name']+" "+name.__dict__['last_name']
                # #print("full_name",full_name)
            return full_name

    def get_sub_assign_to_user_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.sub_assign_to_user:
            name=User.objects.get(id=EtaskTask.sub_assign_to_user.id)
            if name:
                full_name= name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name

    def get_assign_to_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.assign_to:
            name =User.objects.get(id=EtaskTask.assign_to.id)
            if name:
                full_name=name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name

    def get_reporting_dates(self,EtaskTask):
        if EtaskTask.id:
            report_date_list = []
            report_date=ETaskReportingDates.objects.filter(task_type=1,task=EtaskTask.id,is_deleted=False)
            # #print("report_date",report_date)
            if report_date:
                for dt in report_date:
                    dt_dict={
                        'id':dt.id,
                        'reporting_date':dt.reporting_date,
                    }
                    report_date_list.append(dt_dict)                             
                return report_date_list
            else:
                return []


class ETaskTeamTransferTasksListDownloadSerializer(serializers.ModelSerializer):
    parent_task=serializers.SerializerMethodField(required=False)
    sub_data = EtaskTask.objects.filter(parent_id=0,is_deleted=False)
    task_type_name=serializers.CharField(source='get_task_type_display')
    recurrance_frequency_name=serializers.CharField(source='get_recurrance_frequency_display')
    task_status_name=serializers.CharField(source='get_task_status_display')
    task_priority_name=serializers.CharField(source='get_task_priority_display')
    assign_by_name = serializers.SerializerMethodField()
    assign_to_name= serializers.SerializerMethodField()
    sub_assign_to_user_name= serializers.SerializerMethodField()
    reporting_dates=serializers.SerializerMethodField()
    startdate = serializers.SerializerMethodField(required=False)
    enddate = serializers.SerializerMethodField(required=False)
    transferdate = serializers.SerializerMethodField(required=False)

    class Meta:
        model = EtaskTask
        fields = ('__all__')
        extra_fields = ('startdate','enddate','transferdate')

    def get_startdate(self, obj):
        return obj.start_date.strftime("%d %b %Y") if obj.start_date else ''

    def get_enddate(self, obj):
        return obj.end_date.strftime("%d %b %Y") if obj.end_date else ''

    def get_transferdate(self, obj):
        return obj.date_of_transfer.strftime("%d %b %Y") if obj.date_of_transfer else ''

    def get_parent_task(self,EtaskTask):
        if EtaskTask.parent_id:
            if EtaskTask.parent_id !=0:
                if self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject','task_description'):
                    parent_data=self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject','task_description')[0]
                    return parent_data

    def user_name(self, user_id):
        name = None
        full_name = ""
        name = User.objects.get(id=user_id)
        if name:
            full_name =  name.__dict__['first_name']+" "+name.__dict__['last_name']
        return full_name

    def get_assign_by_name(self,EtaskTask):
        name = None
        full_name = ""
        if EtaskTask.assign_by:
            name = User.objects.get(id=EtaskTask.assign_by.id)
            if name:
                full_name =  name.__dict__['first_name']+" "+name.__dict__['last_name']
                # #print("full_name",full_name)
            return full_name

    def get_sub_assign_to_user_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.sub_assign_to_user:
            name=User.objects.get(id=EtaskTask.sub_assign_to_user.id)
            if name:
                full_name= name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name

    def get_assign_to_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.assign_to:
            name =User.objects.get(id=EtaskTask.assign_to.id)
            if name:
                full_name=name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name

    def get_reporting_dates(self,EtaskTask):
        if EtaskTask.id:
            report_date_list = []
            report_date=ETaskReportingDates.objects.filter(task_type=1,task=EtaskTask.id,is_deleted=False).order_by('reporting_date')
            # #print("report_date",report_date)
            if report_date:
                for dt in report_date:
                    dt_dict={
                        'id':dt.id,
                        'reporting_date':dt.reporting_date,
                    }
                    report_date_list.append(dt_dict)                             
                return report_date_list
            else:
                return []


class ETaskOwnershipTransferTasksListDownloadSerializer(serializers.ModelSerializer):
    parent_task=serializers.SerializerMethodField(required=False)
    sub_data = EtaskTask.objects.filter(parent_id=0,is_deleted=False)
    task_type_name=serializers.CharField(source='get_task_type_display')
    recurrance_frequency_name=serializers.CharField(source='get_recurrance_frequency_display')
    task_status_name=serializers.CharField(source='get_task_status_display')
    task_priority_name=serializers.CharField(source='get_task_priority_display')
    assign_by_name = serializers.SerializerMethodField()
    assign_to_name= serializers.SerializerMethodField()
    sub_assign_to_user_name= serializers.SerializerMethodField()
    reporting_dates=serializers.SerializerMethodField()
    startdate = serializers.SerializerMethodField(required=False)
    enddate = serializers.SerializerMethodField(required=False)
    transferdate = serializers.SerializerMethodField(required=False)
    ownership_transferred_from_name = serializers.SerializerMethodField()

    class Meta:
        model = EtaskTask
        fields = ('__all__')
        extra_fields = ('startdate','enddate','transferdate','ownership_transferred_from_name')

    def get_ownership_transferred_from_name(self,obj):
        login_user = self.context.get("login_user")
        ownerhip_log = EtaskTaskOwnershipTransferLog.objects.filter(created_by=login_user,task=obj,is_deleted=False).order_by('-id')
        return ownerhip_log.first().ownership_transferred_from.get_full_name() if ownerhip_log.first() else ''

    def get_startdate(self, obj):
        return obj.start_date.strftime("%d %b %Y") if obj.start_date else ''

    def get_enddate(self, obj):
        return obj.end_date.strftime("%d %b %Y") if obj.end_date else ''

    def get_transferdate(self, obj):
        login_user = self.context.get("login_user")
        ownerhip_log = EtaskTaskOwnershipTransferLog.objects.filter(created_by=login_user,task=obj,is_deleted=False).order_by('-id')
        return ownerhip_log.first().created_at.strftime("%d %b %Y") if ownerhip_log.first() else ''

    def get_parent_task(self,EtaskTask):
        if EtaskTask.parent_id:
            if EtaskTask.parent_id !=0:
                if self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject','task_description'):
                    parent_data=self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject','task_description')[0]
                    return parent_data

    def user_name(self, user_id):
        name = None
        full_name = ""
        name = User.objects.get(id=user_id)
        if name:
            full_name =  name.__dict__['first_name']+" "+name.__dict__['last_name']
        return full_name

    def get_assign_by_name(self,EtaskTask):
        name = None
        full_name = ""
        if EtaskTask.assign_by:
            name = User.objects.get(id=EtaskTask.assign_by.id)
            if name:
                full_name =  name.__dict__['first_name']+" "+name.__dict__['last_name']
                # #print("full_name",full_name)
            return full_name

    def get_sub_assign_to_user_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.sub_assign_to_user:
            name=User.objects.get(id=EtaskTask.sub_assign_to_user.id)
            if name:
                full_name= name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name

    def get_assign_to_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.assign_to:
            name =User.objects.get(id=EtaskTask.assign_to.id)
            if name:
                full_name=name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name

    def get_reporting_dates(self,EtaskTask):
        if EtaskTask.id:
            report_date_list = []
            report_date=ETaskReportingDates.objects.filter(task_type=1,task=EtaskTask.id,is_deleted=False).order_by('reporting_date')
            # #print("report_date",report_date)
            if report_date:
                for dt in report_date:
                    dt_dict={
                        'id':dt.id,
                        'reporting_date':dt.reporting_date,
                    }
                    report_date_list.append(dt_dict)                             
                return report_date_list
            else:
                return []


class DailysheetAddSerializer(serializers.ModelSerializer):
    owner = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = DailyWorkTimeSheet
        fields = '__all__'

    def create(self, validated_data):
        try:
            owner = validated_data.get("owner")
            task_name = validated_data.get("task_name")
            task_description = validated_data.get("task_description")
            start_time = validated_data.get("start_time")
            end_time = validated_data.get("end_time")
            if end_time and start_time:
                timediff = end_time - start_time
                hours = timediff.seconds / 3600
            else:
                hours = 0


            daily_sheet_obj = DailyWorkTimeSheet.objects.create(owner=owner, task_name=task_name,
                                                            task_description=task_description,start_time=start_time,
                                                            end_time=end_time,crated_by=owner, hours=round(hours, 2))

            return validated_data

        except Exception as e:
            raise e
            # raise APIException({'request_status': 0, 'msg': e})


class DailysheetAddSerializerV2(serializers.ModelSerializer):
    owner = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = DailyWorkTimeSheet
        fields = '__all__'

    def create(self, validated_data):
        owner = validated_data.get("owner")
        task_name = validated_data.get("task_name")
        task_description = validated_data.get("task_description")
        task = validated_data.get("task")
        appointment = validated_data.get("appointment")
        start_time = validated_data.get("start_time")
        end_time = validated_data.get("end_time")
        hours = 0
        if end_time and start_time:
            timediff = end_time - start_time
            hours = timediff.seconds / 3600
        daily_sheet_obj = DailyWorkTimeSheet.objects.create(
                                                task=task,appointment=appointment,
                                                owner=owner, task_name=task_name,
                                                task_description=task_description,start_time=start_time,
                                                end_time=end_time,crated_by=owner, hours=round(hours, 2))
        return validated_data



class DaylySheetListSerializer(serializers.ModelSerializer):
    name =  serializers.SerializerMethodField()
    date =  serializers.SerializerMethodField()
    task_name = serializers.SerializerMethodField()
    task_description = serializers.SerializerMethodField()
    start_time = serializers.SerializerMethodField()
    end_time = serializers.SerializerMethodField()
    total_hour = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()

    def get_id(self, obj):
        if obj:
            new_id = obj.id
            return new_id
        else:
            return None


    def get_name(self, obj):
        if obj:
            name = obj.owner.get_full_name()
            return name
    def get_date(self, obj):
        if obj:
            new_date = obj.date
            return  new_date
        else:
            return None
    def get_task_name(self,obj):
        task_name = obj.task_name
        return task_name

    def get_task_description(self,obj):
        task_description = obj.task_description
        return task_description

    def get_start_time(self, obj):
        start_time = obj.start_time  if obj else None
        return start_time

    def get_end_time(self, obj):
        end_time = obj.end_time if obj else None
        return end_time

    def get_total_hour(self, obj):
        if obj:
            timediff = obj.end_time - obj.start_time
            hours = timediff.seconds / 3600
            return round(hours, 2)
        else:
            return None
    def get_created_by(self, obj):
        if obj:

            return obj.owner.get_full_name()
        else:
            return None


    class Meta:
        model = DailyWorkTimeSheet
        fields = ('id','name','date', 'task_name', 'task_description', 'start_time', 'end_time', 'total_hour', 'created_by')


class DaylySheetListSerializerv2(serializers.ModelSerializer):
    name =  serializers.SerializerMethodField()
    task_name = serializers.SerializerMethodField()
    task_description = serializers.SerializerMethodField()
    total_hour = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()

    def get_type(self, obj):
        type = 3
        if obj.task:
            type = 1
        elif obj.appointment:
            type = 2
        return type

    def get_name(self, obj):
        return obj.owner.get_full_name() if obj.owner else ''

    def get_task_name(self,obj):
        task_name = obj.task_name
        if obj.task:
            task_name = obj.task.task_subject
        elif obj.appointment:
            task_name = obj.appointment.appointment_subject
        return task_name

    def get_task_description(self,obj):
        task_description = obj.task_description
        if obj.task:
            task_description = obj.task.task_description
        elif obj.appointment:
            task_description = ''
        return task_description

    def get_total_hour(self, obj):
        timediff = obj.end_time - obj.start_time
        hours = timediff.seconds / 3600
        return round(hours, 2)

    def get_created_by(self, obj):
        return obj.owner.get_full_name() if obj.owner else ''

    class Meta:
        model = DailyWorkTimeSheet
        fields = ('id','task','appointment','name','date', 'task_name', 'task_description', 'start_time', 'end_time', 
                'total_hour', 'created_by','type')


class DaylySheetListDownloadSerializerv2(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    name =  serializers.SerializerMethodField()
    date =  serializers.SerializerMethodField()
    task_name = serializers.SerializerMethodField()
    task_description = serializers.SerializerMethodField()
    start_time = serializers.SerializerMethodField()
    end_time = serializers.SerializerMethodField()
    total_hour = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()

    def get_type(self, obj):
        type = 'Task'
        if obj.task:
            type = 'Task'
        elif obj.appointment:
            type = 'Appointment'
        return type

    def get_id(self, obj):
        if obj:
            new_id = obj.id
            return new_id
        else:
            return None


    def get_name(self, obj):
        if obj:
            name = obj.owner.get_full_name()
            return name
    def get_date(self, obj):
        return obj.start_time.strftime("%d %b %Y") if obj.date else ''

    def get_task_name(self,obj):
        task_name = obj.task_name
        if obj.task:
            task_name = obj.task.task_subject
        elif obj.appointment:
            task_name = obj.appointment.appointment_subject
        return task_name

    def get_task_description(self,obj):
        task_description = obj.task_description
        if obj.task:
            task_description = obj.task.task_description
        elif obj.appointment:
            task_description = ''
        return task_description

    def get_start_time(self, obj):
        return obj.start_time.strftime("%I:%M %p") if obj.start_time else ''

    def get_end_time(self, obj):
        return obj.end_time.strftime("%I:%M %p") if obj.end_time else ''

    def get_total_hour(self, obj):
        if obj:
            timediff = obj.end_time - obj.start_time
            hours = timediff.seconds / 3600
            return round(hours, 2)
        else:
            return None
    def get_created_by(self, obj):
        if obj:

            return obj.owner.get_full_name()
        else:
            return None


    class Meta:
        model = DailyWorkTimeSheet
        fields = ('id','name','date','type','task_name', 'task_description', 'start_time', 'end_time', 'total_hour', 'created_by')


class DailySheetEditSerializer(serializers.ModelSerializer):
    # updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    task_name = serializers.CharField( required=False)
    task_description = serializers.CharField(required=False)
    start_time = serializers.DateTimeField(required=False)
    end_time = serializers.DateTimeField(required=False)

    class Meta:
        model = DailyWorkTimeSheet
        fields = ('task_name','task_description','start_time','end_time','hours')
    def update(self, instance, validated_data):
        try:

            if instance.date.date() == datetime.now().date():
                #print("same")
                instance.task_name = validated_data.get('task_name', instance.task_name)
                instance.task_description = validated_data.get('task_description', instance.task_description)
                instance.start_time = validated_data.get('start_time', instance.start_time)
                instance.end_time = validated_data.get('end_time', instance.end_time)
                timediff = instance.end_time - instance.start_time
                hours = timediff.seconds / 3600
                instance.hours = round(hours, 2)
                instance.save()
                # instance.save()
                return instance
            else:
                return {"error": "Evaluation time Expire"}


        except Exception as E:
            return E



class DailySheetEditSerializerV2(serializers.ModelSerializer):

    class Meta:
        model = DailyWorkTimeSheet
        fields = ('task','appointment','task_name','task_description','start_time','end_time',)

    def update(self, instance, validated_data):
        instance.task = validated_data.get('task')
        instance.appointment = validated_data.get('appointment')
        instance.task_name = validated_data.get('task_name', instance.task_name)
        instance.task_description = validated_data.get('task_description', instance.task_description)
        instance.start_time = validated_data.get('start_time', instance.start_time)
        instance.end_time = validated_data.get('end_time', instance.end_time)
        timediff = instance.end_time - instance.start_time
        hours = timediff.seconds / 3600
        instance.hours = round(hours, 2)
        instance.save()
        return instance



class DailySheetDeleteSerializer(serializers.ModelSerializer):

    class Meta:
        model = DailyWorkTimeSheet
        fields = "__all__"
    def update(self, instance, validated_data):
        try:
            instance.is_deleted = True

            instance.save()

            return instance
        except Exception as E:
            return E


class EtaskClosedTaskListSerializerv2(serializers.ModelSerializer):
    assign_to_name = serializers.SerializerMethodField()
    parent_task = serializers.SerializerMethodField()
    sub_data = EtaskTask.objects.filter(parent_id=0, is_deleted=False)
    user_cc=serializers.SerializerMethodField()
    sub_tasks = serializers.SerializerMethodField()
    
    class Meta:
        model = EtaskTask
        fields = ('id','user_cc','task_priority','task_code_id','parent_id','parent_task','task_subject','task_description','start_date','end_date','task_status','closed_date',
                    'extended_date','assign_by','assign_to','assign_to_name','sub_assign_to_user','get_task_status_display','sub_tasks') #,'assign_to_name','sub_task_list', 'sub_assign_to_name','assign_by_name')

    def get_sub_tasks(self, obj):
        sub_tasks_data = EtaskTask.objects.filter(~Q(task_status=4),parent_id=obj.id,is_deleted=False).values('id','task_subject')
        return sub_tasks_data if sub_tasks_data else list() 

    def get_parent_task(self, obj):
        if  obj.parent_id:
            parent_task = EtaskTask.objects.filter(id=obj.parent_id)
            if parent_task.count():
                parent_data=parent_task.values('id','task_subject')[0]
                return parent_data
        

    def get_assign_to_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.assign_to:
            name =User.objects.get(id=EtaskTask.assign_to.id)
            if name:
                full_name=name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name

    def get_user_cc(self, obj):
        user_cc=EtaskUserCC.objects.filter(task=obj,is_deleted=False).values('id','user__first_name', 'user__last_name')
        return user_cc if user_cc else list()



class EtaskClosedTaskListDownloadSerializerv2(serializers.ModelSerializer):
    assign_to_name = serializers.SerializerMethodField()
    parent_task = serializers.SerializerMethodField()
    sub_data = EtaskTask.objects.filter(parent_id=0, is_deleted=False)
    startdate = serializers.SerializerMethodField()
    enddate = serializers.SerializerMethodField()
    extendeddate = serializers.SerializerMethodField()
    closeddate = serializers.SerializerMethodField()
        
    def get_closeddate(self, obj):
        return obj.closed_date.strftime("%d %b %Y") if obj.closed_date else ''

    def get_startdate(self, obj):
        return obj.start_date.strftime("%d %b %Y") if obj.start_date else ''

    def get_enddate(self, obj):
        return obj.end_date.strftime("%d %b %Y") if obj.end_date else ''

    def get_extendeddate(self, obj):
        return obj.extended_date.strftime("%d %b %Y") if obj.extended_date else ''

    def get_parent_task(self, EtaskTask):
        parent_data = None
        if EtaskTask.parent_id:
            if EtaskTask.parent_id != 0:
                if self.sub_data.filter(id=EtaskTask.parent_id).values('id', 'task_subject'):
                    task_details = self.sub_data.filter(id=EtaskTask.parent_id)
                    for t_d in task_details:
                        report_date = ETaskReportingDates.objects.filter(task_type=1, task=t_d.id,
                                                                         is_deleted=False).values('id',
                                                                                                  'reporting_date')
                        reporting_date = report_date if report_date else []
                        assign_to = t_d.assign_to.id if t_d.assign_to else None
                        assign_by = t_d.assign_by.id if t_d.assign_by else None
                        sub_assign_to_user = t_d.sub_assign_to_user.id if t_d.sub_assign_to_user else None
                        owner = t_d.owner.id if t_d.owner else None
                        parent_data = {
                            'id': t_d.id,
                            'task_code_id': t_d.task_code_id,
                            'parent_id': t_d.parent_id,
                            'owner': owner,
                            'owner_name': userdetails(owner),
                            'assign_to': assign_to,
                            'assign_to_name': userdetails(assign_to),
                            'assign_by': assign_by,
                            'assign_by_name': userdetails(assign_by),
                            'task_subject': t_d.task_subject,
                            'task_description': t_d.task_description,
                            'task_categories': t_d.task_categories,
                            'task_categories_name': t_d.get_task_categories_display(),
                            'start_date': t_d.start_date,
                            'end_date': t_d.end_date,
                            'completed_date': t_d.completed_date,
                            'closed_date': t_d.closed_date,
                            'extended_date': t_d.extended_date,
                            'extend_with_delay': t_d.extend_with_delay,
                            'task_priority': t_d.task_priority,
                            'task_priority_name': t_d.get_task_priority_display(),
                            'task_type': t_d.task_type,
                            'task_type_name': t_d.get_task_type_display(),
                            'task_status': t_d.task_status,
                            'task_status_name': t_d.get_task_status_display(),
                            'recurrance_frequency': t_d.recurrance_frequency,
                            'recurrance_frequency_name': t_d.get_recurrance_frequency_display(),
                            'sub_assign_to_user': sub_assign_to_user,
                            'sub_assign_to_user_name': userdetails(sub_assign_to_user),
                            'reporting_dates': reporting_date
                        }
                        return parent_data
    def get_assign_to_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.assign_to:
            name =User.objects.get(id=EtaskTask.assign_to.id)
            if name:
                full_name=name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name

    class Meta:
        model = EtaskTask
        fields = ('id','task_code_id','parent_id','parent_task','task_subject','task_description','startdate','enddate','extendeddate','closeddate','start_date','end_date','task_status','closed_date',
                    'extended_date','assign_by','assign_to','assign_to_name','sub_assign_to_user','get_task_status_display') #,'assign_to_name','sub_task_list', 'sub_assign_to_name','assign_by_name')


class TodayTaskDetailsPerUserSerializerV2(serializers.ModelSerializer):
    parent_task=serializers.SerializerMethodField(required=False)
    sub_data = EtaskTask.objects.filter(parent_id=0,is_deleted=False)
    task_type_name=serializers.CharField(source='get_task_type_display')
    recurrance_frequency_name=serializers.CharField(source='get_recurrance_frequency_display')
    task_status_name=serializers.CharField(source='get_task_status_display')
    task_priority_name=serializers.CharField(source='get_task_priority_display')
    # assign_by_name = serializers.SerializerMethodField()
    assign_to_name= serializers.SerializerMethodField()
    # sub_assign_to_user_name= serializers.SerializerMethodField()
    reporting_dates=serializers.SerializerMethodField()
    task_flag = serializers.SerializerMethodField()
    overdue_by = serializers.SerializerMethodField()
    user_cc = serializers.SerializerMethodField()
    status_with_pending_request = serializers.SerializerMethodField()
    sub_tasks = serializers.SerializerMethodField()

    class Meta:
        model = EtaskTask
        fields = ('__all__')
        extra_fields = ('task_flag', 'overdue_by', 'user_cc','status_with_pending_request','sub_tasks')

    def get_sub_tasks(self, obj):
        sub_tasks_data = EtaskTask.objects.filter(~Q(task_status=4),parent_id=obj.id,is_deleted=False).values('id','task_subject')
        return sub_tasks_data if sub_tasks_data else list() 

    def get_status_with_pending_request(self, obj):
        status = list()
        task_extention = TaskExtentionDateMap.objects.filter(task=obj, status=1)
        if task_extention.count():
            status.append('Pending Extention')
        task_closer = TaskCompleteReopenMap.objects.filter(task=obj,status=1)
        if task_closer.count():
            status.append('Pending Closure')
        if obj.task_status == 1 and not task_extention.count() and not task_extention.count():
            status.append(obj.get_task_status_display())
        return ' and '.join(status)

    def get_user_cc(self, obj):
        user_cc=EtaskUserCC.objects.filter(task=obj,is_deleted=False).values('id','user__id','user__first_name', 'user__last_name')
        return user_cc if user_cc else list()

    def get_overdue_by(self, obj):
        cur_date=datetime.now().date()
        overdue_by = None
        if obj.extended_date:
            if obj.extended_date and obj.extended_date.date() <= cur_date:
                extended_date = obj.extended_date.date()
                days_extended=(cur_date - extended_date).days
                #print("days_extended",days_extended,type(days_extended))
                if days_extended==1:
                    overdue_by = str(days_extended)+" day"
                elif days_extended >1:
                    overdue_by = str(days_extended)+" days"
                else:
                    overdue_by = None
        else:
            if obj.end_date and obj.end_date.date() <= cur_date:
                end_date = obj.end_date.date()
                days_extended=(cur_date - end_date).days
                #print("days_extended",days_extended,type(days_extended))
                if days_extended ==1:
                    overdue_by = str(days_extended)+" day"
                elif days_extended >1:
                    overdue_by = str(days_extended)+" days"
                else:
                    overdue_by = None
        return overdue_by

    def get_task_flag(self, obj):
        TASK_TYPES = ('overdue', 'ongoing', 'upcoming')
        cur_date=datetime.now().date()
        task_flag = None
        
        if (obj.extended_date is not None and obj.extended_date.date() < cur_date) or (obj.extended_date is None and obj.end_date.date() < cur_date):
            task_flag = TASK_TYPES[0]
        elif (obj.shifted_date is not None and obj.shifted_date.date() <= cur_date) or (obj.shifted_date is None and obj.start_date.date() <= cur_date):
            task_flag = TASK_TYPES[1]
        elif (obj.shifted_date is not None and obj.shifted_date.date() > cur_date) or (obj.shifted_date is None and obj.start_date.date() > cur_date):
            task_flag = TASK_TYPES[2]
        return task_flag

    def get_parent_task(self,EtaskTask):
        if EtaskTask.parent_id:
            if EtaskTask.parent_id !=0:
                if self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject','task_description'):
                    parent_data=self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject','task_description')[0]
                    return parent_data

    def get_assign_to_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.assign_to:
            name =User.objects.get(id=EtaskTask.assign_to.id)
            if name:
                full_name=name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name

    def get_reporting_dates(self,EtaskTask):
        if EtaskTask.id:
            report_date_list = []
            current_date=datetime.now().date()

            login_user = self.context.get("login_user")
            login_user_and_reporting_heads = list(EtaskTaskSubAssignLog.objects.filter(task=EtaskTask,sub_assign=login_user,is_deleted=False).values_list('assign_from',flat=True))
            owned_user = [EtaskTask.assign_by] if int(login_user) == EtaskTask.assign_to.id else login_user_and_reporting_heads

            report_date=ETaskReportingDates.objects.filter(task_type=1,reporting_date__gte=current_date,
                                        owned_by__in=owned_user,task=EtaskTask.id,is_deleted=False).order_by('reporting_date').order_by('reporting_date')
            
            last_reporting_date=ETaskReportingDates.objects.filter(task_type=1,reporting_date__lt=current_date,
                                        owned_by__in=owned_user,task=EtaskTask.id,is_deleted=False).order_by('reporting_date').order_by('-reporting_date')
            if report_date:
                for dt in report_date:
                    pre_report= dt.reporting_date.date()
                    # #print('pre_report',pre_report)
                    if pre_report>=current_date:                     
                        dt_dict={
                            'id':dt.id,
                            'reporting_date':dt.reporting_date,
                            'reporting_status':dt.get_reporting_status_display()
                        }
                        report_date_list.append(dt_dict)
                        break                             
                return report_date_list
            elif last_reporting_date:
                for dt in last_reporting_date:
                    pre_report= dt.reporting_date.date()
                    # #print('pre_report',pre_report)
                    if pre_report<current_date:                     
                        dt_dict={
                            'id':dt.id,
                            'reporting_date':dt.reporting_date,
                            'reporting_status':dt.get_reporting_status_display()
                        }
                        report_date_list.append(dt_dict)
                        break                             
                return report_date_list
            else:
                return []


class TodayPriorityTaskDetailsPerUserSerializerV2(serializers.ModelSerializer):
    parent_task = serializers.SerializerMethodField(required=False)
    sub_data = EtaskTask.objects.filter(parent_id=0, is_deleted=False)
    task_type_name = serializers.CharField(source='get_task_type_display')
    recurrance_frequency_name = serializers.CharField(source='get_recurrance_frequency_display')
    task_status_name = serializers.CharField(source='get_task_status_display')
    task_priority_name = serializers.CharField(source='get_task_priority_display')
    # assign_by_name = serializers.SerializerMethodField()
    assign_to_name = serializers.SerializerMethodField()
    # sub_assign_to_user_name= serializers.SerializerMethodField()
    reporting_dates = serializers.SerializerMethodField()
    task_flag = serializers.SerializerMethodField()
    overdue_by = serializers.SerializerMethodField()
    user_cc = serializers.SerializerMethodField()
    status_with_pending_request = serializers.SerializerMethodField()
    sub_tasks = serializers.SerializerMethodField()

    class Meta:
        model = EtaskTask
        fields = ('__all__')
        extra_fields = ('task_flag', 'overdue_by', 'user_cc', 'status_with_pending_request', 'sub_tasks')

    def get_sub_tasks(self, obj):
        sub_tasks_data = EtaskTask.objects.filter(~Q(task_status=4), parent_id=obj.id, is_deleted=False).values('id',
                                                                                                                'task_subject')
        return sub_tasks_data if sub_tasks_data else list()

    def get_status_with_pending_request(self, obj):
        status = list()
        task_extention = TaskExtentionDateMap.objects.filter(task=obj, status=1)
        if task_extention.count():
            status.append('Pending Extention')
        task_closer = TaskCompleteReopenMap.objects.filter(task=obj, status=1)
        if task_closer.count():
            status.append('Pending Closure')
        if obj.task_status == 1 and not task_extention.count() and not task_extention.count():
            status.append(obj.get_task_status_display())
        return ' and '.join(status)

    def get_user_cc(self, obj):
        user_cc = EtaskUserCC.objects.filter(task=obj, is_deleted=False).values('id', 'user__id', 'user__first_name',
                                                                                'user__last_name')
        return user_cc if user_cc else list()

    def get_overdue_by(self, obj):
        cur_date = datetime.now().date()
        overdue_by = None
        if obj.extended_date:
            if obj.extended_date and obj.extended_date.date() <= cur_date:
                extended_date = obj.extended_date.date()
                days_extended = (cur_date - extended_date).days
                # print("days_extended",days_extended,type(days_extended))
                if days_extended == 1:
                    overdue_by = str(days_extended) + " day"
                elif days_extended > 1:
                    overdue_by = str(days_extended) + " days"
                else:
                    overdue_by = None
        else:
            if obj.end_date and obj.end_date.date() <= cur_date:
                end_date = obj.end_date.date()
                days_extended = (cur_date - end_date).days
                # print("days_extended",days_extended,type(days_extended))
                if days_extended == 1:
                    overdue_by = str(days_extended) + " day"
                elif days_extended > 1:
                    overdue_by = str(days_extended) + " days"
                else:
                    overdue_by = None
        return overdue_by

    def get_task_flag(self, obj):
        TASK_TYPES = ('overdue', 'ongoing', 'upcoming')
        cur_date = datetime.now().date()
        task_flag = None

        if (obj.extended_date is not None and obj.extended_date.date() < cur_date) or (
                obj.extended_date is None and obj.end_date.date() < cur_date):
            task_flag = TASK_TYPES[0]
        elif (obj.shifted_date is not None and obj.shifted_date.date() <= cur_date) or (
                obj.shifted_date is None and obj.start_date.date() <= cur_date):
            task_flag = TASK_TYPES[1]
        elif (obj.shifted_date is not None and obj.shifted_date.date() > cur_date) or (
                obj.shifted_date is None and obj.start_date.date() > cur_date):
            task_flag = TASK_TYPES[2]
        return task_flag

    def get_parent_task(self, EtaskTask):
        if EtaskTask.parent_id:
            if EtaskTask.parent_id != 0:
                if self.sub_data.filter(id=EtaskTask.parent_id).values('id', 'task_subject', 'task_description'):
                    parent_data = \
                    self.sub_data.filter(id=EtaskTask.parent_id).values('id', 'task_subject', 'task_description')[0]
                    return parent_data

    def get_assign_to_name(self, EtaskTask):
        name = None
        full_name = ""
        if EtaskTask.assign_to:
            name = User.objects.get(id=EtaskTask.assign_to.id)
            if name:
                full_name = name.__dict__['first_name'] + " " + name.__dict__['last_name']
                return full_name

    def get_reporting_dates(self, EtaskTask):
        if EtaskTask.id:
            report_date_list = []
            current_date = datetime.now().date()

            login_user = self.context.get("login_user")
            login_user_and_reporting_heads = list(
                EtaskTaskSubAssignLog.objects.filter(task=EtaskTask, sub_assign=login_user,
                                                     is_deleted=False).values_list('assign_from', flat=True))
            owned_user = [EtaskTask.assign_by] if int(
                login_user) == EtaskTask.assign_to.id else login_user_and_reporting_heads

            report_date = ETaskReportingDates.objects.filter(task_type=1, reporting_date__gte=current_date,
                                                             owned_by__in=owned_user, task=EtaskTask.id,
                                                             is_deleted=False).order_by('reporting_date').order_by(
                'reporting_date')

            last_reporting_date = ETaskReportingDates.objects.filter(task_type=1, reporting_date__lt=current_date,
                                                                     owned_by__in=owned_user, task=EtaskTask.id,
                                                                     is_deleted=False).order_by(
                'reporting_date').order_by('-reporting_date')
            if report_date:
                for dt in report_date:
                    pre_report = dt.reporting_date.date()
                    # #print('pre_report',pre_report)
                    if pre_report >= current_date:
                        dt_dict = {
                            'id': dt.id,
                            'reporting_date': dt.reporting_date,
                            'reporting_status': dt.get_reporting_status_display()
                        }
                        report_date_list.append(dt_dict)
                        break
                return report_date_list
            elif last_reporting_date:
                for dt in last_reporting_date:
                    pre_report = dt.reporting_date.date()
                    # #print('pre_report',pre_report)
                    if pre_report < current_date:
                        dt_dict = {
                            'id': dt.id,
                            'reporting_date': dt.reporting_date,
                            'reporting_status': dt.get_reporting_status_display()
                        }
                        report_date_list.append(dt_dict)
                        break
                return report_date_list
            else:
                return []


class DailySheetUserTaskListSerializer(serializers.ModelSerializer):
    class Meta:
        model = EtaskTask
        fields = ('id','task_subject','task_code_id',)


class DailySheetAppointmentListSerializer(serializers.ModelSerializer):
    class Meta:
        model = EtaskAppointment
        fields = ('id','appointment_subject',)


class TodayTaskDetailsPerUserDownloadSerializerV2(serializers.ModelSerializer):
    parent_task=serializers.SerializerMethodField(required=False)
    sub_data = EtaskTask.objects.filter(parent_id=0,is_deleted=False)
    task_type_name=serializers.CharField(source='get_task_type_display')
    recurrance_frequency_name=serializers.CharField(source='get_recurrance_frequency_display')
    task_status_name=serializers.CharField(source='get_task_status_display')
    task_priority_name=serializers.CharField(source='get_task_priority_display')
    # assign_by_name = serializers.SerializerMethodField()
    assign_to_name= serializers.SerializerMethodField()
    # sub_assign_to_user_name= serializers.SerializerMethodField()
    reporting_dates=serializers.SerializerMethodField()
    task_flag = serializers.SerializerMethodField()
    overdue_by = serializers.SerializerMethodField()
    startdate = serializers.SerializerMethodField()

    class Meta:
        model = EtaskTask
        fields = ('__all__')
        extra_fields = ('task_flag', 'overdue_by', 'startdate')

    def get_startdate(self, obj):
        return obj.start_date.strftime("%d %b %Y") if obj.start_date else ''

    def get_overdue_by(self, obj):
        cur_date=datetime.now().date()
        overdue_by = None
        if obj.extended_date:
            if obj.extended_date and obj.extended_date.date() <= cur_date:
                extended_date = obj.extended_date.date()
                days_extended=(cur_date - extended_date).days
                #print("days_extended",days_extended,type(days_extended))
                if days_extended==1:
                    overdue_by = str(days_extended)+" day"
                elif days_extended >1:
                    overdue_by = str(days_extended)+" days"
                else:
                    overdue_by = None
        else:
            if obj.end_date and obj.end_date.date() <= cur_date:
                end_date = obj.end_date.date()
                days_extended=(cur_date - end_date).days
                #print("days_extended",days_extended,type(days_extended))
                if days_extended ==1:
                    overdue_by = str(days_extended)+" day"
                elif days_extended >1:
                    overdue_by = str(days_extended)+" days"
                else:
                    overdue_by = None
        return overdue_by

    def get_task_flag(self, obj):
        TASK_TYPES = ('overdue', 'ongoing', 'upcomming')
        cur_date=datetime.now().date()
        task_flag = None
        
        if (obj.extended_date is not None and obj.extended_date.date() < cur_date) or (obj.extended_date is None and obj.end_date.date() < cur_date):
            task_flag = TASK_TYPES[0]
        elif (obj.shifted_date is not None and obj.shifted_date.date() <= cur_date) or (obj.shifted_date is None and obj.start_date.date() <= cur_date):
            task_flag = TASK_TYPES[1]
        elif (obj.shifted_date is not None and obj.shifted_date.date() > cur_date) or (obj.shifted_date is None and obj.start_date.date() > cur_date):
            task_flag = TASK_TYPES[2]
        return task_flag

    def get_parent_task(self,EtaskTask):
        if EtaskTask.parent_id:
            if EtaskTask.parent_id !=0:
                if self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject','task_description'):
                    parent_data=self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject','task_description')[0]
                    return parent_data
    
    def get_assign_to_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.assign_to:
            name =User.objects.get(id=EtaskTask.assign_to.id)
            if name:
                full_name=name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name

    def get_reporting_dates(self,EtaskTask):
        # if EtaskTask.id:
        #     report_date_list = ''
        #     login_user = self.context.get("login_user")
        #     login_user_and_reporting_heads = list(EtaskTaskSubAssignLog.objects.filter(task=EtaskTask,sub_assign=login_user,is_deleted=False).values_list('assign_from',flat=True))
        #     owned_user = [EtaskTask.assign_by] if int(login_user) == EtaskTask.assign_to.id else login_user_and_reporting_heads

        #     report_date=ETaskReportingDates.objects.filter(owned_by__in=owned_user,task_type=1,task=EtaskTask.id,is_deleted=False).order_by('reporting_date')
        #     if report_date:
        #         for dt in report_date:
        #             report_date_list += '{}, '.format(dt.reporting_date.strftime("%d %b %Y"))                            
        #         return report_date_list[:-2]
        #     else:
        #         return ''
        
        if EtaskTask.id:
            report_date_list = []
            current_date=datetime.now().date()

            login_user = self.context.get("login_user")
            login_user_and_reporting_heads = list(EtaskTaskSubAssignLog.objects.filter(task=EtaskTask,sub_assign=login_user,is_deleted=False).values_list('assign_from',flat=True))
            owned_user = [EtaskTask.assign_by] if int(login_user) == EtaskTask.assign_to.id else login_user_and_reporting_heads

            report_date=ETaskReportingDates.objects.filter(task_type=1,reporting_date__gte=current_date,
                                        owned_by__in=owned_user,task=EtaskTask.id,is_deleted=False).order_by('reporting_date').order_by('reporting_date')
            
            last_reporting_date=ETaskReportingDates.objects.filter(task_type=1,reporting_date__lt=current_date,
                                        owned_by__in=owned_user,task=EtaskTask.id,is_deleted=False).order_by('reporting_date').order_by('-reporting_date')
            if report_date:
                for dt in report_date:
                    pre_report= dt.reporting_date.date()
                    # #print('pre_report',pre_report)
                    if pre_report>=current_date:                     
                        dt_dict={
                            'id':dt.id,
                            'reporting_date':dt.reporting_date,
                            'reporting_status':dt.get_reporting_status_display()
                        }
                        report_date_list.append(dt.reporting_date.strftime("%d %b %Y"))
                        break                             
                return ', '.join(report_date_list)
            elif last_reporting_date:
                for dt in last_reporting_date:
                    pre_report= dt.reporting_date.date()
                    # #print('pre_report',pre_report)
                    if pre_report<current_date:                     
                        dt_dict={
                            'id':dt.id,
                            'reporting_date':dt.reporting_date,
                            'reporting_status':dt.get_reporting_status_display()
                        }
                        report_date_list.append(dt.reporting_date.strftime("%d %b %Y"))
                        break                             
                return ', '.join(report_date_list)
            else:
                return ''


class TodayPriorityTaskDetailsPerUserDownloadSerializerV2(serializers.ModelSerializer):
    parent_task = serializers.SerializerMethodField(required=False)
    sub_data = EtaskTask.objects.filter(parent_id=0, is_deleted=False)
    task_type_name = serializers.CharField(source='get_task_type_display')
    recurrance_frequency_name = serializers.CharField(source='get_recurrance_frequency_display')
    task_status_name = serializers.CharField(source='get_task_status_display')
    task_priority_name = serializers.CharField(source='get_task_priority_display')
    # assign_by_name = serializers.SerializerMethodField()
    assign_to_name = serializers.SerializerMethodField()
    # sub_assign_to_user_name= serializers.SerializerMethodField()
    reporting_dates = serializers.SerializerMethodField()
    task_flag = serializers.SerializerMethodField()
    overdue_by = serializers.SerializerMethodField()
    startdate = serializers.SerializerMethodField()

    class Meta:
        model = EtaskTask
        fields = ('__all__')
        extra_fields = ('task_flag', 'overdue_by', 'startdate')

    def get_startdate(self, obj):
        return obj.start_date.strftime("%d %b %Y") if obj.start_date else ''

    def get_overdue_by(self, obj):
        cur_date = datetime.now().date()
        overdue_by = None
        if obj.extended_date:
            if obj.extended_date and obj.extended_date.date() <= cur_date:
                extended_date = obj.extended_date.date()
                days_extended = (cur_date - extended_date).days
                # print("days_extended",days_extended,type(days_extended))
                if days_extended == 1:
                    overdue_by = str(days_extended) + " day"
                elif days_extended > 1:
                    overdue_by = str(days_extended) + " days"
                else:
                    overdue_by = None
        else:
            if obj.end_date and obj.end_date.date() <= cur_date:
                end_date = obj.end_date.date()
                days_extended = (cur_date - end_date).days
                # print("days_extended",days_extended,type(days_extended))
                if days_extended == 1:
                    overdue_by = str(days_extended) + " day"
                elif days_extended > 1:
                    overdue_by = str(days_extended) + " days"
                else:
                    overdue_by = None
        return overdue_by

    def get_task_flag(self, obj):
        TASK_TYPES = ('overdue', 'ongoing', 'upcomming')
        cur_date = datetime.now().date()
        task_flag = None

        if (obj.extended_date is not None and obj.extended_date.date() < cur_date) or (
                obj.extended_date is None and obj.end_date.date() < cur_date):
            task_flag = TASK_TYPES[0]
        elif (obj.shifted_date is not None and obj.shifted_date.date() <= cur_date) or (
                obj.shifted_date is None and obj.start_date.date() <= cur_date):
            task_flag = TASK_TYPES[1]
        elif (obj.shifted_date is not None and obj.shifted_date.date() > cur_date) or (
                obj.shifted_date is None and obj.start_date.date() > cur_date):
            task_flag = TASK_TYPES[2]
        return task_flag

    def get_parent_task(self, EtaskTask):
        if EtaskTask.parent_id:
            if EtaskTask.parent_id != 0:
                if self.sub_data.filter(id=EtaskTask.parent_id).values('id', 'task_subject', 'task_description'):
                    parent_data = \
                    self.sub_data.filter(id=EtaskTask.parent_id).values('id', 'task_subject', 'task_description')[0]
                    return parent_data

    def get_assign_to_name(self, EtaskTask):
        name = None
        full_name = ""
        if EtaskTask.assign_to:
            name = User.objects.get(id=EtaskTask.assign_to.id)
            if name:
                full_name = name.__dict__['first_name'] + " " + name.__dict__['last_name']
                return full_name

    def get_reporting_dates(self, EtaskTask):
        # if EtaskTask.id:
        #     report_date_list = ''
        #     login_user = self.context.get("login_user")
        #     login_user_and_reporting_heads = list(EtaskTaskSubAssignLog.objects.filter(task=EtaskTask,sub_assign=login_user,is_deleted=False).values_list('assign_from',flat=True))
        #     owned_user = [EtaskTask.assign_by] if int(login_user) == EtaskTask.assign_to.id else login_user_and_reporting_heads

        #     report_date=ETaskReportingDates.objects.filter(owned_by__in=owned_user,task_type=1,task=EtaskTask.id,is_deleted=False).order_by('reporting_date')
        #     if report_date:
        #         for dt in report_date:
        #             report_date_list += '{}, '.format(dt.reporting_date.strftime("%d %b %Y"))
        #         return report_date_list[:-2]
        #     else:
        #         return ''

        if EtaskTask.id:
            report_date_list = []
            current_date = datetime.now().date()

            login_user = self.context.get("login_user")
            login_user_and_reporting_heads = list(
                EtaskTaskSubAssignLog.objects.filter(task=EtaskTask, sub_assign=login_user,
                                                     is_deleted=False).values_list('assign_from', flat=True))
            owned_user = [EtaskTask.assign_by] if int(
                login_user) == EtaskTask.assign_to.id else login_user_and_reporting_heads

            report_date = ETaskReportingDates.objects.filter(task_type=1, reporting_date__gte=current_date,
                                                             owned_by__in=owned_user, task=EtaskTask.id,
                                                             is_deleted=False).order_by('reporting_date').order_by(
                'reporting_date')

            last_reporting_date = ETaskReportingDates.objects.filter(task_type=1, reporting_date__lt=current_date,
                                                                     owned_by__in=owned_user, task=EtaskTask.id,
                                                                     is_deleted=False).order_by(
                'reporting_date').order_by('-reporting_date')
            if report_date:
                for dt in report_date:
                    pre_report = dt.reporting_date.date()
                    # #print('pre_report',pre_report)
                    if pre_report >= current_date:
                        dt_dict = {
                            'id': dt.id,
                            'reporting_date': dt.reporting_date,
                            'reporting_status': dt.get_reporting_status_display()
                        }
                        report_date_list.append(dt.reporting_date.strftime("%d %b %Y"))
                        break
                return ', '.join(report_date_list)
            elif last_reporting_date:
                for dt in last_reporting_date:
                    pre_report = dt.reporting_date.date()
                    # #print('pre_report',pre_report)
                    if pre_report < current_date:
                        dt_dict = {
                            'id': dt.id,
                            'reporting_date': dt.reporting_date,
                            'reporting_status': dt.get_reporting_status_display()
                        }
                        report_date_list.append(dt.reporting_date.strftime("%d %b %Y"))
                        break
                return ', '.join(report_date_list)
            else:
                return ''


class TodayTaskHistoryPerUserSerializer(serializers.ModelSerializer):
    parent_task=serializers.SerializerMethodField(required=False)
    sub_data = EtaskTask.objects.filter(parent_id=0,is_deleted=False)
    task_type_name=serializers.CharField(source='get_task_type_display')
    recurrance_frequency_name=serializers.CharField(source='get_recurrance_frequency_display')
    task_status_name=serializers.CharField(source='get_task_status_display')
    task_priority_name=serializers.CharField(source='get_task_priority_display')
    # assign_by_name = serializers.SerializerMethodField()
    assign_to_name= serializers.SerializerMethodField()
    # sub_assign_to_user_name= serializers.SerializerMethodField()
    reporting_dates=serializers.SerializerMethodField()
    task_flag = serializers.SerializerMethodField()
    overdue_by = serializers.SerializerMethodField()

    class Meta:
        model = EtaskTask
        fields = ('__all__')
        extra_fields = ('task_flag', 'overdue_by')

    def get_overdue_by(self, obj):
        cur_date=datetime.now().date()
        overdue_by = None
        if obj.extended_date:
            if obj.extended_date and obj.extended_date.date() <= cur_date:
                extended_date = obj.extended_date.date()
                days_extended=(cur_date - extended_date).days
                #print("days_extended",days_extended,type(days_extended))
                if days_extended==1:
                    overdue_by = str(days_extended)+" day"
                elif days_extended >1:
                    overdue_by = str(days_extended)+" days"
                else:
                    overdue_by = None
        else:
            if obj.end_date and obj.end_date.date() <= cur_date:
                end_date = obj.end_date.date()
                days_extended=(cur_date - end_date).days
                #print("days_extended",days_extended,type(days_extended))
                if days_extended ==1:
                    overdue_by = str(days_extended)+" day"
                elif days_extended >1:
                    overdue_by = str(days_extended)+" days"
                else:
                    overdue_by = None
        return overdue_by

    def get_task_flag(self, obj):
        TASK_TYPES = ('overdue', 'ongoing', 'upcomming')
        cur_date=datetime.now().date()
        task_flag = None
        
        if (obj.extended_date is not None and obj.extended_date.date() < cur_date) or (obj.extended_date is None and obj.end_date.date() < cur_date):
            task_flag = TASK_TYPES[0]
        elif (obj.shifted_date is not None and obj.shifted_date.date() <= cur_date) or (obj.shifted_date is None and obj.start_date.date() <= cur_date):
            task_flag = TASK_TYPES[1]
        elif (obj.shifted_date is not None and obj.shifted_date.date() > cur_date) or (obj.shifted_date is None and obj.start_date.date() > cur_date):
            task_flag = TASK_TYPES[2]
        return task_flag

    def get_parent_task(self,EtaskTask):
        if EtaskTask.parent_id:
            if EtaskTask.parent_id !=0:
                if self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject','task_description'):
                    parent_data=self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject','task_description')[0]
                    return parent_data
    
    def get_assign_to_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.assign_to:
            name =User.objects.get(id=EtaskTask.assign_to.id)
            if name:
                full_name=name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name

    def get_reporting_dates(self,EtaskTask):
        if EtaskTask.id:
            report_date_list = []
            report_date=ETaskReportingDates.objects.filter(task_type=1,task=EtaskTask.id,is_deleted=False)
            # #print("report_date",report_date)
            current_date=datetime.now().date()
            if report_date:
                for dt in report_date:
                    pre_report= dt.reporting_date.date()
                    # #print('pre_report',pre_report)
                    # if pre_report>current_date:                     
                    dt_dict={
                        'id':dt.id,
                        'reporting_date':dt.reporting_date,
                        'reporting_status':dt.get_reporting_status_display()
                    }
                    report_date_list.append(dt_dict)                             
                return report_date_list
            else:
                return []


class TodayAppointmenDetailsPerUserSerializer2(serializers.ModelSerializer):
    # appointment = serializers.CharField(required=False)
    class Meta:
        model=EtaskAppointment
        fields='__all__'


class TodayAppointmenDetailsPerUserDownloadSerializer2(serializers.ModelSerializer):
    start_date = serializers.SerializerMethodField(required=False)
    end_date = serializers.SerializerMethodField(required=False)

    def get_start_date(self, obj):
        return obj.start_date.strftime("%d %b %Y %I:%M %p") if obj.start_date else ''

    def get_end_date(self, obj):
        return obj.end_date.strftime("%d %b %Y %I:%M %p") if obj.end_date else ''

    class Meta:
        model=EtaskAppointment
        fields='__all__'


class TeamTaskDetailsPerUserSerializerV2(serializers.ModelSerializer):
    parent_task = serializers.SerializerMethodField(required=False)
    sub_data = EtaskTask.objects.filter(parent_id=0, is_deleted=False)
    task_type_name = serializers.CharField(source='get_task_type_display')
    recurrance_frequency_name = serializers.CharField(source='get_recurrance_frequency_display')
    task_status_name = serializers.CharField(source='get_task_status_display')
    task_priority_name = serializers.CharField(source='get_task_priority_display')
    # assign_by_name = serializers.SerializerMethodField()
    assign_to_name = serializers.SerializerMethodField()
    # sub_assign_to_user_name= serializers.SerializerMethodField()
    reporting_dates = serializers.SerializerMethodField()
    task_flag = serializers.SerializerMethodField()
    # overdue_by = serializers.SerializerMethodField()
    user_cc=serializers.SerializerMethodField()
    task_assign_flow = serializers.SerializerMethodField()
    sub_tasks = serializers.SerializerMethodField()
    status_with_pending_request = serializers.SerializerMethodField()

    class Meta:
        model = EtaskTask
        fields = ('__all__')
        extra_fields = ('status_with_pending_request','task_flag','user_cc','task_assign_flow','sub_tasks')
    
    def get_status_with_pending_request(self, obj):
        status = list()
        task_extention = TaskExtentionDateMap.objects.filter(task=obj, status=1)
        if task_extention.count():
            status.append('Pending Extention')
        task_closer = TaskCompleteReopenMap.objects.filter(task=obj,status=1)
        if task_closer.count():
            status.append('Pending Closure')
        if obj.task_status == 1 and not task_extention.count() and not task_extention.count():
            status.append(obj.get_task_status_display())
        return ' and '.join(status)

    def get_sub_tasks(self, obj):
        sub_tasks_data = EtaskTask.objects.filter(~Q(task_status=4),parent_id=obj.id,is_deleted=False).values('id','task_subject')
        return sub_tasks_data if sub_tasks_data else list() 

    def get_task_assign_flow(self, obj):
        assign_user = [{'id':user.id,'name':user.get_full_name()} for user in [obj.assign_by,obj.assign_to]]
        if obj.sub_assign_to_user:
            sub_assign_uaers = EtaskTaskSubAssignLog.objects.filter(task=obj,is_deleted=False)
            for sub_assign_uaer in sub_assign_uaers:
                assign_user.append({'id':sub_assign_uaer.sub_assign.id,'name':sub_assign_uaer.sub_assign.get_full_name()})
        return assign_user

    def get_user_cc(self, obj):
        user_cc=EtaskUserCC.objects.filter(task=obj,is_deleted=False).values('id','user__first_name', 'user__last_name')
        return user_cc if user_cc else list()

    def get_task_flag(self, obj):
        TASK_TYPES = ('overdue', 'ongoing', 'upcomming')
        cur_date = datetime.now().date()
        task_flag = None
        if (obj.shifted_date is not None and obj.shifted_date.date() <= cur_date) or (
                obj.shifted_date is None and obj.start_date.date() <= cur_date):
            task_flag = TASK_TYPES[1]
        elif (obj.extended_date is not None and obj.extended_date.date() < cur_date) or (
                obj.extended_date is None and obj.end_date.date() < cur_date):
            task_flag = TASK_TYPES[0]
        elif (obj.shifted_date is not None and obj.shifted_date.date() > cur_date) or (
                obj.shifted_date is None and obj.start_date.date() > cur_date):
            task_flag = TASK_TYPES[2]
        return task_flag

    def get_parent_task(self, EtaskTask):
        if EtaskTask.parent_id:
            if EtaskTask.parent_id != 0:
                if self.sub_data.filter(id=EtaskTask.parent_id).values('id', 'task_subject', 'task_description'):
                    parent_data = \
                    self.sub_data.filter(id=EtaskTask.parent_id).values('id', 'task_subject', 'task_description')[0]
                    return parent_data

    def get_assign_to_name(self, EtaskTask):
        name = None
        full_name = ""
        if EtaskTask.assign_to:
            name = User.objects.get(id=EtaskTask.assign_to.id)
            if name:
                full_name = name.__dict__['first_name'] + " " + name.__dict__['last_name']
                return full_name

    def get_reporting_dates(self, EtaskTask):
        if EtaskTask.id:
            report_date_list = []
            current_date=datetime.now().date()
            login_user = self.context.get("login_user")
            report_date=ETaskReportingDates.objects.filter(task_type=1,reporting_date__gte=current_date,
                                        owned_by=login_user,task=EtaskTask.id,is_deleted=False).order_by('reporting_date').order_by('reporting_date')
            
            last_reporting_date=ETaskReportingDates.objects.filter(task_type=1,reporting_date__lt=current_date,
                                        owned_by=login_user,task=EtaskTask.id,is_deleted=False).order_by('reporting_date').order_by('-reporting_date')
            if report_date:
                for dt in report_date:
                    pre_report= dt.reporting_date.date()
                    # #print('pre_report',pre_report)
                    if pre_report>=current_date:                     
                        dt_dict={
                            'id':dt.id,
                            'reporting_date':dt.reporting_date,
                            'reporting_status':dt.get_reporting_status_display()
                        }
                        report_date_list.append(dt_dict)
                        break                             
                return report_date_list
            elif last_reporting_date:
                for dt in last_reporting_date:
                    pre_report= dt.reporting_date.date()
                    # #print('pre_report',pre_report)
                    if pre_report<current_date:                     
                        dt_dict={
                            'id':dt.id,
                            'reporting_date':dt.reporting_date,
                            'reporting_status':dt.get_reporting_status_display()
                        }
                        report_date_list.append(dt_dict)
                        break                             
                return report_date_list
            else:
                return []


class TeamPriorityTaskDetailsPerUserSerializerV2(serializers.ModelSerializer):
    parent_task = serializers.SerializerMethodField(required=False)
    sub_data = EtaskTask.objects.filter(parent_id=0, is_deleted=False)
    task_type_name = serializers.CharField(source='get_task_type_display')
    recurrance_frequency_name = serializers.CharField(source='get_recurrance_frequency_display')
    task_status_name = serializers.CharField(source='get_task_status_display')
    task_priority_name = serializers.CharField(source='get_task_priority_display')
    # assign_by_name = serializers.SerializerMethodField()
    assign_to_name = serializers.SerializerMethodField()
    # sub_assign_to_user_name= serializers.SerializerMethodField()
    reporting_dates = serializers.SerializerMethodField()
    task_flag = serializers.SerializerMethodField()
    # overdue_by = serializers.SerializerMethodField()
    user_cc = serializers.SerializerMethodField()
    task_assign_flow = serializers.SerializerMethodField()
    sub_tasks = serializers.SerializerMethodField()
    status_with_pending_request = serializers.SerializerMethodField()

    class Meta:
        model = EtaskTask
        fields = ('__all__')
        extra_fields = ('status_with_pending_request', 'task_flag', 'user_cc', 'task_assign_flow', 'sub_tasks')

    def get_status_with_pending_request(self, obj):
        status = list()
        task_extention = TaskExtentionDateMap.objects.filter(task=obj, status=1)
        if task_extention.count():
            status.append('Pending Extention')
        task_closer = TaskCompleteReopenMap.objects.filter(task=obj, status=1)
        if task_closer.count():
            status.append('Pending Closure')
        if obj.task_status == 1 and not task_extention.count() and not task_extention.count():
            status.append(obj.get_task_status_display())
        return ' and '.join(status)

    def get_sub_tasks(self, obj):
        sub_tasks_data = EtaskTask.objects.filter(~Q(task_status=4), parent_id=obj.id, is_deleted=False).values('id',
                                                                                                                'task_subject')
        return sub_tasks_data if sub_tasks_data else list()

    def get_task_assign_flow(self, obj):
        assign_user = [{'id': user.id, 'name': user.get_full_name()} for user in [obj.assign_by, obj.assign_to]]
        if obj.sub_assign_to_user:
            sub_assign_uaers = EtaskTaskSubAssignLog.objects.filter(task=obj, is_deleted=False)
            for sub_assign_uaer in sub_assign_uaers:
                assign_user.append(
                    {'id': sub_assign_uaer.sub_assign.id, 'name': sub_assign_uaer.sub_assign.get_full_name()})
        return assign_user

    def get_user_cc(self, obj):
        user_cc = EtaskUserCC.objects.filter(task=obj, is_deleted=False).values('id', 'user__first_name',
                                                                                'user__last_name')
        return user_cc if user_cc else list()

    def get_task_flag(self, obj):
        TASK_TYPES = ('overdue', 'ongoing', 'upcomming')
        cur_date = datetime.now().date()
        task_flag = None
        if (obj.shifted_date is not None and obj.shifted_date.date() <= cur_date) or (
                obj.shifted_date is None and obj.start_date.date() <= cur_date):
            task_flag = TASK_TYPES[1]
        elif (obj.extended_date is not None and obj.extended_date.date() < cur_date) or (
                obj.extended_date is None and obj.end_date.date() < cur_date):
            task_flag = TASK_TYPES[0]
        elif (obj.shifted_date is not None and obj.shifted_date.date() > cur_date) or (
                obj.shifted_date is None and obj.start_date.date() > cur_date):
            task_flag = TASK_TYPES[2]
        return task_flag

    def get_parent_task(self, EtaskTask):
        if EtaskTask.parent_id:
            if EtaskTask.parent_id != 0:
                if self.sub_data.filter(id=EtaskTask.parent_id).values('id', 'task_subject', 'task_description'):
                    parent_data = \
                        self.sub_data.filter(id=EtaskTask.parent_id).values('id', 'task_subject', 'task_description')[0]
                    return parent_data

    def get_assign_to_name(self, EtaskTask):
        name = None
        full_name = ""
        if EtaskTask.assign_to:
            name = User.objects.get(id=EtaskTask.assign_to.id)
            if name:
                full_name = name.__dict__['first_name'] + " " + name.__dict__['last_name']
                return full_name

    def get_reporting_dates(self, EtaskTask):
        if EtaskTask.id:
            report_date_list = []
            current_date = datetime.now().date()
            login_user = self.context.get("login_user")
            report_date = ETaskReportingDates.objects.filter(task_type=1, reporting_date__gte=current_date,
                                                             owned_by=login_user, task=EtaskTask.id,
                                                             is_deleted=False).order_by('reporting_date').order_by(
                'reporting_date')

            last_reporting_date = ETaskReportingDates.objects.filter(task_type=1, reporting_date__lt=current_date,
                                                                     owned_by=login_user, task=EtaskTask.id,
                                                                     is_deleted=False).order_by(
                'reporting_date').order_by('-reporting_date')
            if report_date:
                for dt in report_date:
                    pre_report = dt.reporting_date.date()
                    # #print('pre_report',pre_report)
                    if pre_report >= current_date:
                        dt_dict = {
                            'id': dt.id,
                            'reporting_date': dt.reporting_date,
                            'reporting_status': dt.get_reporting_status_display()
                        }
                        report_date_list.append(dt_dict)
                        break
                return report_date_list
            elif last_reporting_date:
                for dt in last_reporting_date:
                    pre_report = dt.reporting_date.date()
                    # #print('pre_report',pre_report)
                    if pre_report < current_date:
                        dt_dict = {
                            'id': dt.id,
                            'reporting_date': dt.reporting_date,
                            'reporting_status': dt.get_reporting_status_display()
                        }
                        report_date_list.append(dt_dict)
                        break
                return report_date_list
            else:
                return []


class TeamTaskDetailsPerUserDownloadSerializerV2(serializers.ModelSerializer):
    parent_task = serializers.SerializerMethodField(required=False)
    sub_data = EtaskTask.objects.filter(parent_id=0, is_deleted=False)
    task_type_name = serializers.CharField(source='get_task_type_display')
    recurrance_frequency_name = serializers.CharField(source='get_recurrance_frequency_display')
    task_status_name = serializers.CharField(source='get_task_status_display')
    task_priority_name = serializers.CharField(source='get_task_priority_display')
    assign_to_name = serializers.SerializerMethodField()
    reporting_dates = serializers.SerializerMethodField()
    task_flag = serializers.SerializerMethodField()
    start_date = serializers.SerializerMethodField()
    end_date = serializers.SerializerMethodField()
    extended_date = serializers.SerializerMethodField()

    class Meta:
        model = EtaskTask
        fields = ('__all__')
        extra_fields = ('task_flag')

    def get_start_date(self, obj):
        return obj.start_date.strftime("%d %b %Y") if obj.start_date else ''

    def get_end_date(self, obj):
        return obj.end_date.strftime("%d %b %Y") if obj.end_date else ''

    def get_extended_date(self, obj):
        return obj.extended_date.strftime("%d %b %Y") if obj.extended_date else ''

    def get_task_flag(self, obj):
        TASK_TYPES = ('overdue', 'ongoing', 'upcomming')
        cur_date = datetime.now().date()
        task_flag = None
        if (obj.shifted_date is not None and obj.shifted_date.date() <= cur_date) or (
                obj.shifted_date is None and obj.start_date.date() <= cur_date):
            task_flag = TASK_TYPES[1]
        elif (obj.extended_date is not None and obj.extended_date.date() < cur_date) or (
                obj.extended_date is None and obj.end_date.date() < cur_date):
            task_flag = TASK_TYPES[0]
        elif (obj.shifted_date is not None and obj.shifted_date.date() > cur_date) or (
                obj.shifted_date is None and obj.start_date.date() > cur_date):
            task_flag = TASK_TYPES[2]
        return task_flag

    def get_parent_task(self, EtaskTask):
        if EtaskTask.parent_id:
            if EtaskTask.parent_id != 0:
                if self.sub_data.filter(id=EtaskTask.parent_id).values('id', 'task_subject', 'task_description'):
                    parent_data = \
                    self.sub_data.filter(id=EtaskTask.parent_id).values('id', 'task_subject', 'task_description')[0]
                    return parent_data

    def get_assign_to_name(self, EtaskTask):
        name = None
        full_name = ""
        if EtaskTask.assign_to:
            name = User.objects.get(id=EtaskTask.assign_to.id)
            if name:
                full_name = name.__dict__['first_name'] + " " + name.__dict__['last_name']
                return full_name

    def get_reporting_dates(self,EtaskTask):
        # if EtaskTask.id:
        #     report_date_list = ''
        #     report_date=ETaskReportingDates.objects.filter(task_type=1,task=EtaskTask.id,is_deleted=False).order_by('reporting_date')
        #     if report_date:
        #         for dt in report_date:
        #             report_date_list += '{}, '.format(dt.reporting_date.strftime("%d %b %Y"))                            
        #         return report_date_list[:-2]
        #     else:
        #         return ''
        if EtaskTask.id:
            report_date_list = []
            current_date=datetime.now().date()
            login_user = self.context.get("login_user")
            report_date=ETaskReportingDates.objects.filter(task_type=1,reporting_date__gte=current_date,
                                        owned_by=login_user,task=EtaskTask.id,is_deleted=False).order_by('reporting_date').order_by('reporting_date')
            
            last_reporting_date=ETaskReportingDates.objects.filter(task_type=1,reporting_date__lt=current_date,
                                        owned_by=login_user,task=EtaskTask.id,is_deleted=False).order_by('reporting_date').order_by('-reporting_date')
            if report_date:
                for dt in report_date:
                    pre_report= dt.reporting_date.date()
                    # #print('pre_report',pre_report)
                    if pre_report>=current_date:                     
                        dt_dict={
                            'id':dt.id,
                            'reporting_date':dt.reporting_date,
                            'reporting_status':dt.get_reporting_status_display()
                        }
                        report_date_list.append(dt.reporting_date.strftime("%d %b %Y"))
                        break                             
                return ', '.join(report_date_list)
            elif last_reporting_date:
                for dt in last_reporting_date:
                    pre_report= dt.reporting_date.date()
                    # #print('pre_report',pre_report)
                    if pre_report<current_date:                     
                        dt_dict={
                            'id':dt.id,
                            'reporting_date':dt.reporting_date,
                            'reporting_status':dt.get_reporting_status_display()
                        }
                        report_date_list.append(dt.reporting_date.strftime("%d %b %Y"))
                        break                             
                return ', '.join(report_date_list)
            else:
                return ''


class TeamPriorityTaskDetailsPerUserDownloadSerializerV2(serializers.ModelSerializer):
    parent_task = serializers.SerializerMethodField(required=False)
    sub_data = EtaskTask.objects.filter(parent_id=0, is_deleted=False)
    task_type_name = serializers.CharField(source='get_task_type_display')
    recurrance_frequency_name = serializers.CharField(source='get_recurrance_frequency_display')
    task_status_name = serializers.CharField(source='get_task_status_display')
    task_priority_name = serializers.CharField(source='get_task_priority_display')
    assign_to_name = serializers.SerializerMethodField()
    reporting_dates = serializers.SerializerMethodField()
    task_flag = serializers.SerializerMethodField()
    start_date = serializers.SerializerMethodField()
    end_date = serializers.SerializerMethodField()
    extended_date = serializers.SerializerMethodField()

    class Meta:
        model = EtaskTask
        fields = ('__all__')
        extra_fields = ('task_flag')

    def get_start_date(self, obj):
        return obj.start_date.strftime("%d %b %Y") if obj.start_date else ''

    def get_end_date(self, obj):
        return obj.end_date.strftime("%d %b %Y") if obj.end_date else ''

    def get_extended_date(self, obj):
        return obj.extended_date.strftime("%d %b %Y") if obj.extended_date else ''

    def get_task_flag(self, obj):
        TASK_TYPES = ('overdue', 'ongoing', 'upcomming')
        cur_date = datetime.now().date()
        task_flag = None
        if (obj.shifted_date is not None and obj.shifted_date.date() <= cur_date) or (
                obj.shifted_date is None and obj.start_date.date() <= cur_date):
            task_flag = TASK_TYPES[1]
        elif (obj.extended_date is not None and obj.extended_date.date() < cur_date) or (
                obj.extended_date is None and obj.end_date.date() < cur_date):
            task_flag = TASK_TYPES[0]
        elif (obj.shifted_date is not None and obj.shifted_date.date() > cur_date) or (
                obj.shifted_date is None and obj.start_date.date() > cur_date):
            task_flag = TASK_TYPES[2]
        return task_flag

    def get_parent_task(self, EtaskTask):
        if EtaskTask.parent_id:
            if EtaskTask.parent_id != 0:
                if self.sub_data.filter(id=EtaskTask.parent_id).values('id', 'task_subject', 'task_description'):
                    parent_data = \
                        self.sub_data.filter(id=EtaskTask.parent_id).values('id', 'task_subject', 'task_description')[0]
                    return parent_data

    def get_assign_to_name(self, EtaskTask):
        name = None
        full_name = ""
        if EtaskTask.assign_to:
            name = User.objects.get(id=EtaskTask.assign_to.id)
            if name:
                full_name = name.__dict__['first_name'] + " " + name.__dict__['last_name']
                return full_name

    def get_reporting_dates(self, EtaskTask):
        # if EtaskTask.id:
        #     report_date_list = ''
        #     report_date=ETaskReportingDates.objects.filter(task_type=1,task=EtaskTask.id,is_deleted=False).order_by('reporting_date')
        #     if report_date:
        #         for dt in report_date:
        #             report_date_list += '{}, '.format(dt.reporting_date.strftime("%d %b %Y"))
        #         return report_date_list[:-2]
        #     else:
        #         return ''
        if EtaskTask.id:
            report_date_list = []
            current_date = datetime.now().date()
            login_user = self.context.get("login_user")
            report_date = ETaskReportingDates.objects.filter(task_type=1, reporting_date__gte=current_date,
                                                             owned_by=login_user, task=EtaskTask.id,
                                                             is_deleted=False).order_by('reporting_date').order_by(
                'reporting_date')

            last_reporting_date = ETaskReportingDates.objects.filter(task_type=1, reporting_date__lt=current_date,
                                                                     owned_by=login_user, task=EtaskTask.id,
                                                                     is_deleted=False).order_by(
                'reporting_date').order_by('-reporting_date')
            if report_date:
                for dt in report_date:
                    pre_report = dt.reporting_date.date()
                    # #print('pre_report',pre_report)
                    if pre_report >= current_date:
                        dt_dict = {
                            'id': dt.id,
                            'reporting_date': dt.reporting_date,
                            'reporting_status': dt.get_reporting_status_display()
                        }
                        report_date_list.append(dt.reporting_date.strftime("%d %b %Y"))
                        break
                return ', '.join(report_date_list)
            elif last_reporting_date:
                for dt in last_reporting_date:
                    pre_report = dt.reporting_date.date()
                    # #print('pre_report',pre_report)
                    if pre_report < current_date:
                        dt_dict = {
                            'id': dt.id,
                            'reporting_date': dt.reporting_date,
                            'reporting_status': dt.get_reporting_status_display()
                        }
                        report_date_list.append(dt.reporting_date.strftime("%d %b %Y"))
                        break
                return ', '.join(report_date_list)
            else:
                return ''


class TeamUpcomingTaskDetailsPerUserSerializerV2(serializers.ModelSerializer):
    parent_task = serializers.SerializerMethodField(required=False)
    sub_data = EtaskTask.objects.filter(parent_id=0, is_deleted=False)
    task_type_name = serializers.CharField(source='get_task_type_display')
    recurrance_frequency_name = serializers.CharField(source='get_recurrance_frequency_display')
    task_status_name = serializers.CharField(source='get_task_status_display')
    task_priority_name = serializers.CharField(source='get_task_priority_display')
    # assign_by_name = serializers.SerializerMethodField()
    assign_to_name = serializers.SerializerMethodField()
    # sub_assign_to_user_name= serializers.SerializerMethodField()
    reporting_dates = serializers.SerializerMethodField()
    task_flag = serializers.SerializerMethodField()
    # overdue_by = serializers.SerializerMethodField()
    user_cc=serializers.SerializerMethodField()
    sub_tasks = serializers.SerializerMethodField()

    class Meta:
        model = EtaskTask
        fields = ('__all__')
        extra_fields = ('task_flag','user_cc','sub_tasks')

    def get_sub_tasks(self, obj):
        sub_tasks_data = EtaskTask.objects.filter(~Q(task_status=4),parent_id=obj.id,is_deleted=False).values('id','task_subject')
        return sub_tasks_data if sub_tasks_data else list() 

    def get_user_cc(self, obj):
        user_cc=EtaskUserCC.objects.filter(task=obj,is_deleted=False).values('id','user__first_name', 'user__last_name')
        return user_cc if user_cc else list()

    def get_task_flag(self, obj):
        TASK_TYPES = ('overdue', 'ongoing', 'upcomming')
        cur_date = datetime.now().date()
        task_flag = None
        if (obj.shifted_date is not None and obj.shifted_date.date() <= cur_date) or (
                obj.shifted_date is None and obj.start_date.date() <= cur_date):
            task_flag = TASK_TYPES[1]
        elif (obj.extended_date is not None and obj.extended_date.date() < cur_date) or (
                obj.extended_date is None and obj.end_date.date() < cur_date):
            task_flag = TASK_TYPES[0]
        elif (obj.shifted_date is not None and obj.shifted_date.date() > cur_date) or (
                obj.shifted_date is None and obj.start_date.date() > cur_date):
            task_flag = TASK_TYPES[2]
        return task_flag

    def get_parent_task(self, EtaskTask):
        if EtaskTask.parent_id:
            if EtaskTask.parent_id != 0:
                if self.sub_data.filter(id=EtaskTask.parent_id).values('id', 'task_subject', 'task_description'):
                    parent_data = \
                    self.sub_data.filter(id=EtaskTask.parent_id).values('id', 'task_subject', 'task_description')[0]
                    return parent_data

    def get_assign_to_name(self, EtaskTask):
        name = None
        full_name = ""
        if EtaskTask.assign_to:
            name = User.objects.get(id=EtaskTask.assign_to.id)
            if name:
                full_name = name.__dict__['first_name'] + " " + name.__dict__['last_name']
                return full_name

    def get_reporting_dates(self, EtaskTask):
        if EtaskTask.id:
            report_date_list = []
            current_date=datetime.now().date()
            login_user = self.context.get("login_user")
            report_date=ETaskReportingDates.objects.filter(task_type=1,reporting_date__gte=current_date,
                                        owned_by=login_user,task=EtaskTask.id,is_deleted=False).order_by('reporting_date').order_by('reporting_date')
            
            last_reporting_date=ETaskReportingDates.objects.filter(task_type=1,reporting_date__lt=current_date,
                                        owned_by=login_user,task=EtaskTask.id,is_deleted=False).order_by('reporting_date').order_by('-reporting_date')
            if report_date:
                for dt in report_date:
                    pre_report= dt.reporting_date.date()
                    # #print('pre_report',pre_report)
                    if pre_report>=current_date:                     
                        dt_dict={
                            'id':dt.id,
                            'reporting_date':dt.reporting_date,
                            'reporting_status':dt.get_reporting_status_display()
                        }
                        report_date_list.append(dt_dict)
                        break                             
                return report_date_list
            elif last_reporting_date:
                for dt in last_reporting_date:
                    pre_report= dt.reporting_date.date()
                    # #print('pre_report',pre_report)
                    if pre_report<current_date:                     
                        dt_dict={
                            'id':dt.id,
                            'reporting_date':dt.reporting_date,
                            'reporting_status':dt.get_reporting_status_display()
                        }
                        report_date_list.append(dt_dict)
                        break                             
                return report_date_list
            else:
                return []


class TeamUpcomingTaskDetailsPerUserDownloadSerializerV2(serializers.ModelSerializer):
    parent_task = serializers.SerializerMethodField(required=False)
    sub_data = EtaskTask.objects.filter(parent_id=0, is_deleted=False)
    task_type_name = serializers.CharField(source='get_task_type_display')
    recurrance_frequency_name = serializers.CharField(source='get_recurrance_frequency_display')
    task_status_name = serializers.CharField(source='get_task_status_display')
    task_priority_name = serializers.CharField(source='get_task_priority_display')
    assign_to_name = serializers.SerializerMethodField()
    reporting_dates = serializers.SerializerMethodField()
    task_flag = serializers.SerializerMethodField()
    start_date = serializers.SerializerMethodField()
    end_date = serializers.SerializerMethodField()
    extended_date = serializers.SerializerMethodField()

    class Meta:
        model = EtaskTask
        fields = ('__all__')
        extra_fields = ('task_flag')

    def get_start_date(self, obj):
        return obj.start_date.strftime("%d %b %Y") if obj.start_date else ''

    def get_end_date(self, obj):
        return obj.end_date.strftime("%d %b %Y") if obj.end_date else ''

    def get_extended_date(self, obj):
        return obj.extended_date.strftime("%d %b %Y") if obj.extended_date else ''

    def get_task_flag(self, obj):
        TASK_TYPES = ('overdue', 'ongoing', 'upcomming')
        cur_date = datetime.now().date()
        task_flag = None
        if (obj.shifted_date is not None and obj.shifted_date.date() <= cur_date) or (
                obj.shifted_date is None and obj.start_date.date() <= cur_date):
            task_flag = TASK_TYPES[1]
        elif (obj.extended_date is not None and obj.extended_date.date() < cur_date) or (
                obj.extended_date is None and obj.end_date.date() < cur_date):
            task_flag = TASK_TYPES[0]
        elif (obj.shifted_date is not None and obj.shifted_date.date() > cur_date) or (
                obj.shifted_date is None and obj.start_date.date() > cur_date):
            task_flag = TASK_TYPES[2]
        return task_flag

    def get_parent_task(self, EtaskTask):
        if EtaskTask.parent_id:
            if EtaskTask.parent_id != 0:
                if self.sub_data.filter(id=EtaskTask.parent_id).values('id', 'task_subject', 'task_description'):
                    parent_data = \
                    self.sub_data.filter(id=EtaskTask.parent_id).values('id', 'task_subject', 'task_description')[0]
                    return parent_data

    def get_assign_to_name(self, EtaskTask):
        name = None
        full_name = ""
        if EtaskTask.assign_to:
            name = User.objects.get(id=EtaskTask.assign_to.id)
            if name:
                full_name = name.__dict__['first_name'] + " " + name.__dict__['last_name']
                return full_name

    def get_reporting_dates(self,EtaskTask):
        # if EtaskTask.id:
        #     report_date_list = ''
        #     report_date=ETaskReportingDates.objects.filter(task_type=1,task=EtaskTask.id,is_deleted=False).order_by('reporting_date')
        #     if report_date:
        #         for dt in report_date:
        #             report_date_list += '{}, '.format(dt.reporting_date.strftime("%d %b %Y"))                            
        #         return report_date_list[:-2]
        #     else:
        #         return ''
        if EtaskTask.id:
            report_date_list = []
            current_date=datetime.now().date()
            login_user = self.context.get("login_user")
            report_date=ETaskReportingDates.objects.filter(task_type=1,reporting_date__gte=current_date,
                                        owned_by=login_user,task=EtaskTask.id,is_deleted=False).order_by('reporting_date').order_by('reporting_date')
            
            last_reporting_date=ETaskReportingDates.objects.filter(task_type=1,reporting_date__lt=current_date,
                                        owned_by=login_user,task=EtaskTask.id,is_deleted=False).order_by('reporting_date').order_by('-reporting_date')
            if report_date:
                for dt in report_date:
                    pre_report= dt.reporting_date.date()
                    # #print('pre_report',pre_report)
                    if pre_report>=current_date:                     
                        dt_dict={
                            'id':dt.id,
                            'reporting_date':dt.reporting_date,
                            'reporting_status':dt.get_reporting_status_display()
                        }
                        report_date_list.append(dt.reporting_date.strftime("%d %b %Y"))
                        break                             
                return ', '.join(report_date_list)
            elif last_reporting_date:
                for dt in last_reporting_date:
                    pre_report= dt.reporting_date.date()
                    # #print('pre_report',pre_report)
                    if pre_report<current_date:                     
                        dt_dict={
                            'id':dt.id,
                            'reporting_date':dt.reporting_date,
                            'reporting_status':dt.get_reporting_status_display()
                        }
                        report_date_list.append(dt.reporting_date.strftime("%d %b %Y"))
                        break                             
                return ', '.join(report_date_list)
            else:
                return ''


class OverdueTaskDetailsPerUserV2Serializer(serializers.ModelSerializer):
    parent_task=serializers.SerializerMethodField(required=False)
    sub_data = EtaskTask.objects.filter(parent_id=0,is_deleted=False)
    task_type_name=serializers.CharField(source='get_task_type_display')
    task_priority_name=serializers.CharField(source='get_task_priority_display')
    recurrance_frequency_name=serializers.CharField(source='get_recurrance_frequency_display')
    task_status_name=serializers.CharField(source='get_task_status_display')
    # assign_by_name = serializers.SerializerMethodField()
    assign_to_name= serializers.SerializerMethodField()
    # sub_assign_to_user_name= serializers.SerializerMethodField()
    reporting_dates=serializers.SerializerMethodField()
    class Meta:
        model = EtaskTask
        fields = ('__all__')

    def get_parent_task(self,EtaskTask):
        if EtaskTask.parent_id:
            if EtaskTask.parent_id !=0:
                if self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject'):
                    parent_data=self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject','task_description')[0]
                    return parent_data


class TeamsUpcomingReportingDetailsPerUserSerializer(serializers.ModelSerializer):
    reporting_dates=serializers.SerializerMethodField()
    parent_task=serializers.SerializerMethodField(required=False)
    sub_tasks = serializers.SerializerMethodField()

    class Meta:
        model=EtaskTask
        fields=('id','parent_id','parent_task','task_code_id','task_subject','assign_by','assign_to','sub_assign_to_user','reporting_dates',
                'owner','extended_date','end_date','requested_end_date','sub_tasks')

    def get_sub_tasks(self, obj):
        sub_tasks_data = EtaskTask.objects.filter(~Q(task_status=4),parent_id=obj.id,is_deleted=False).values('id','task_subject')
        return sub_tasks_data if sub_tasks_data else list() 

    def get_parent_task(self,obj):
        if obj.parent_id !=0:
            if EtaskTask.objects.filter(id=obj.parent_id):
                parent_data=EtaskTask.objects.filter(id=obj.parent_id).values('id','task_subject','task_description')[0]
                return parent_data

    def get_reporting_dates(self,EtaskTask):
        cur_date = datetime.now().date()
        if EtaskTask.id:
            login_user = self.context.get("login_user")
            # login_user_and_reporting_heads = get_user_reporting_heads(user=login_user)
            # login_user_and_reporting_heads.append(login_user.id)
            report_date=list(ETaskReportingDates.objects.filter(reporting_date__date__gt=cur_date,task_type=1,task=EtaskTask.id,
                            owned_by=login_user,is_deleted=False).values('reporting_date').order_by('reporting_date'))
            return [report_date[0]] if report_date else []


class TeamsUpcomingReportingDetailsPerUserDownloadSerializer(serializers.ModelSerializer):
    reporting_dates=serializers.SerializerMethodField()

    class Meta:
        model=EtaskTask
        fields=('id','task_code_id','task_subject','task_description','assign_by','assign_to','sub_assign_to_user','reporting_dates','owner')
    def get_reporting_dates(self,EtaskTask):
        cur_date = datetime.now().date()
        report_date_list = ''
        if EtaskTask.id:
            login_user = self.context.get("login_user")
            login_user_and_reporting_heads = get_user_reporting_heads(user=login_user)
            login_user_and_reporting_heads.append(int(self.context.get("login_user")))
            report_date=ETaskReportingDates.objects.filter(reporting_date__date__gt=cur_date,task_type=1,task=EtaskTask.id,
                        owned_by__in=login_user_and_reporting_heads,is_deleted=False).order_by('reporting_date')
            if report_date:
                for dt in report_date:
                    report_date_list += '{}, '.format(dt.reporting_date.strftime("%d %b %Y %I:%M %p"))                            
                return report_date_list[:-2]
            else:
                return ''


class TeamsTodaysReportingDetailsPerUserSerializer(serializers.ModelSerializer):
    reporting_dates=serializers.SerializerMethodField()
    parent_task=serializers.SerializerMethodField(required=False)
    sub_tasks = serializers.SerializerMethodField()

    class Meta:
        model=EtaskTask
        fields=('id','parent_id','parent_task','task_code_id','task_subject','assign_by','assign_to','sub_assign_to_user','reporting_dates',
                'owner','extended_date','end_date','requested_end_date','sub_tasks')
    
    def get_sub_tasks(self, obj):
        sub_tasks_data = EtaskTask.objects.filter(~Q(task_status=4),parent_id=obj.id,is_deleted=False).values('id','task_subject')
        return sub_tasks_data if sub_tasks_data else list() 

    def get_parent_task(self,obj):
        if obj.parent_id !=0:
            if EtaskTask.objects.filter(id=obj.parent_id):
                parent_data=EtaskTask.objects.filter(id=obj.parent_id).values('id','task_subject','task_description')[0]
                return parent_data
    
    def get_reporting_dates(self,EtaskTask):
        cur_date = datetime.now().date()
        if EtaskTask.id:
            login_user = self.context.get("login_user")
            # login_user_and_reporting_heads = get_user_reporting_heads(user=login_user)
            # login_user_and_reporting_heads.append(login_user.id)
            report_date=list(ETaskReportingDates.objects.filter(reporting_date__date__lte=cur_date,task_type=1,task=EtaskTask.id,
                        owned_by=login_user,reporting_status=2,is_deleted=False).values('id','reporting_date').order_by('reporting_date'))
            return report_date


class TeamsTodaysReportingDetailsPerUserDownloadSerializer(serializers.ModelSerializer):
    reporting_dates=serializers.SerializerMethodField()

    class Meta:
        model=EtaskTask
        fields=('id','task_code_id','task_subject','task_description','assign_by','assign_to','sub_assign_to_user','reporting_dates','owner')

    def get_reporting_dates(self,EtaskTask):
        if EtaskTask.id:
            login_user = self.context.get("login_user")
            login_user_and_reporting_heads = get_user_reporting_heads(user=login_user)
            login_user_and_reporting_heads.append(int(login_user))
            report_date_list = ''
            cur_date = datetime.now().date()
            report_date=ETaskReportingDates.objects.filter(reporting_date__date__lte=cur_date,task_type=1,task=EtaskTask.id,
                        owned_by__in=login_user_and_reporting_heads,reporting_status=2,is_deleted=False).order_by('reporting_date')
            if report_date:
                for dt in report_date:
                    report_date_list += '{}, '.format(dt.reporting_date.strftime("%d %b %Y"))                            
                return report_date_list[:-2]
            else:
                return ''



class TeamsOverdueTaskDetailsPerUserSerializerV2(serializers.ModelSerializer):
    parent_task = serializers.SerializerMethodField(required=False)
    sub_data = EtaskTask.objects.filter(parent_id=0, is_deleted=False)
    task_type_name = serializers.CharField(source='get_task_type_display')
    recurrance_frequency_name = serializers.CharField(source='get_recurrance_frequency_display')
    task_status_name = serializers.CharField(source='get_task_status_display')
    task_priority_name = serializers.CharField(source='get_task_priority_display')
    # assign_by_name = serializers.SerializerMethodField()
    assign_to_name = serializers.SerializerMethodField()
    # sub_assign_to_user_name= serializers.SerializerMethodField()
    reporting_dates = serializers.SerializerMethodField()
    task_flag = serializers.SerializerMethodField()
    overdue_by = serializers.SerializerMethodField()
    user_cc=serializers.SerializerMethodField()
    sub_tasks = serializers.SerializerMethodField()
    status_with_pending_request = serializers.SerializerMethodField()

    class Meta:
        model = EtaskTask
        fields = ('__all__')
        extra_fields = ('status_with_pending_request','task_flag', 'overdue_by','user_cc','sub_tasks')
    
    def get_status_with_pending_request(self, obj):
        status = list()
        task_extention = TaskExtentionDateMap.objects.filter(task=obj, status=1)
        if task_extention.count():
            status.append('Pending Extention')
        task_closer = TaskCompleteReopenMap.objects.filter(task=obj,status=1)
        if task_closer.count():
            status.append('Pending Closure')
        if obj.task_status == 1 and not task_extention.count() and not task_extention.count():
            status.append('Overdue')
        return ' and '.join(status)

    def get_sub_tasks(self, obj):
        sub_tasks_data = EtaskTask.objects.filter(~Q(task_status=4),parent_id=obj.id,is_deleted=False).values('id','task_subject')
        return sub_tasks_data if sub_tasks_data else list() 

    def get_user_cc(self, obj):
        user_cc=EtaskUserCC.objects.filter(task=obj,is_deleted=False).values('id','user__first_name', 'user__last_name')
        return user_cc if user_cc else list()

    def get_overdue_by(self, obj):
        cur_date = datetime.now().date()
        overdue_by = None
        if obj.extended_date:
            if obj.extended_date and obj.extended_date.date() <= cur_date:
                extended_date = obj.extended_date.date()
                days_extended = (cur_date - extended_date).days
                #print("days_extended", days_extended, type(days_extended))
                if days_extended == 1:
                    overdue_by = str(days_extended) + " day"
                elif days_extended > 1:
                    overdue_by = str(days_extended) + " days"
                else:
                    overdue_by = None
        else:
            if obj.end_date and obj.end_date.date() <= cur_date:
                end_date = obj.end_date.date()
                days_extended = (cur_date - end_date).days
                #print("days_extended", days_extended, type(days_extended))
                if days_extended == 1:
                    overdue_by = str(days_extended) + " day"
                elif days_extended > 1:
                    overdue_by = str(days_extended) + " days"
                else:
                    overdue_by = None
        return overdue_by

    def get_task_flag(self, obj):
        TASK_TYPES = ('overdue', 'ongoing', 'upcomming')
        cur_date = datetime.now().date()
        task_flag = None

        if (obj.extended_date is not None and obj.extended_date.date() < cur_date) or (
                obj.extended_date is None and obj.end_date.date() < cur_date):
            task_flag = TASK_TYPES[0]
        elif (obj.shifted_date is not None and obj.shifted_date.date() <= cur_date) or (
                obj.shifted_date is None and obj.start_date.date() <= cur_date):
            task_flag = TASK_TYPES[1]
        elif (obj.shifted_date is not None and obj.shifted_date.date() > cur_date) or (
                obj.shifted_date is None and obj.start_date.date() > cur_date):
            task_flag = TASK_TYPES[2]
        return task_flag

    def get_parent_task(self, EtaskTask):
        if EtaskTask.parent_id:
            if EtaskTask.parent_id != 0:
                if self.sub_data.filter(id=EtaskTask.parent_id).values('id', 'task_subject', 'task_description'):
                    parent_data = \
                    self.sub_data.filter(id=EtaskTask.parent_id).values('id', 'task_subject', 'task_description')[0]
                    return parent_data

    def get_assign_to_name(self, EtaskTask):
        name = None
        full_name = ""
        if EtaskTask.assign_to:
            name = User.objects.get(id=EtaskTask.assign_to.id)
            if name:
                full_name = name.__dict__['first_name'] + " " + name.__dict__['last_name']
                return full_name

    def get_reporting_dates(self, EtaskTask):
        if EtaskTask.id:
            report_date_list = []
            current_date=datetime.now().date()
            login_user = self.context.get("login_user")
            report_date=ETaskReportingDates.objects.filter(task_type=1,reporting_date__gte=current_date,
                                        owned_by=login_user,task=EtaskTask.id,is_deleted=False).order_by('reporting_date').order_by('reporting_date')
            
            last_reporting_date=ETaskReportingDates.objects.filter(task_type=1,reporting_date__lt=current_date,
                                        owned_by=login_user,task=EtaskTask.id,is_deleted=False).order_by('reporting_date').order_by('-reporting_date')
            if report_date:
                for dt in report_date:
                    pre_report= dt.reporting_date.date()
                    # #print('pre_report',pre_report)
                    if pre_report>=current_date:                     
                        dt_dict={
                            'id':dt.id,
                            'reporting_date':dt.reporting_date,
                            'reporting_status':dt.get_reporting_status_display()
                        }
                        report_date_list.append(dt_dict)
                        break                             
                return report_date_list
            elif last_reporting_date:
                for dt in last_reporting_date:
                    pre_report= dt.reporting_date.date()
                    # #print('pre_report',pre_report)
                    if pre_report<current_date:                     
                        dt_dict={
                            'id':dt.id,
                            'reporting_date':dt.reporting_date,
                            'reporting_status':dt.get_reporting_status_display()
                        }
                        report_date_list.append(dt_dict)
                        break                             
                return report_date_list
            else:
                return []


class TeamsOverdueTaskDetailsPerUserDownloadSerializerV2(serializers.ModelSerializer):
    parent_task = serializers.SerializerMethodField(required=False)
    sub_data = EtaskTask.objects.filter(parent_id=0, is_deleted=False)
    task_type_name = serializers.CharField(source='get_task_type_display')
    recurrance_frequency_name = serializers.CharField(source='get_recurrance_frequency_display')
    task_status_name = serializers.CharField(source='get_task_status_display')
    task_priority_name = serializers.CharField(source='get_task_priority_display')
    # assign_by_name = serializers.SerializerMethodField()
    assign_to_name = serializers.SerializerMethodField()
    # sub_assign_to_user_name= serializers.SerializerMethodField()
    reporting_dates = serializers.SerializerMethodField()
    task_flag = serializers.SerializerMethodField()
    overdue_by = serializers.SerializerMethodField()
    start_date = serializers.SerializerMethodField()
    end_date = serializers.SerializerMethodField()

    class Meta:
        model = EtaskTask
        fields = ('__all__')
        extra_fields = ('task_flag', 'overdue_by')

    def get_start_date(self, obj):
        return obj.start_date.strftime("%d %b %Y") if obj.start_date else ''

    def get_end_date(self, obj):
        return obj.end_date.strftime("%d %b %Y") if obj.end_date else ''

    def get_overdue_by(self, obj):
        cur_date = datetime.now().date()
        overdue_by = None
        if obj.extended_date:
            if obj.extended_date and obj.extended_date.date() <= cur_date:
                extended_date = obj.extended_date.date()
                days_extended = (cur_date - extended_date).days
                #print("days_extended", days_extended, type(days_extended))
                if days_extended == 1:
                    overdue_by = str(days_extended) + " day"
                elif days_extended > 1:
                    overdue_by = str(days_extended) + " days"
                else:
                    overdue_by = None
        else:
            if obj.end_date and obj.end_date.date() <= cur_date:
                end_date = obj.end_date.date()
                days_extended = (cur_date - end_date).days
                #print("days_extended", days_extended, type(days_extended))
                if days_extended == 1:
                    overdue_by = str(days_extended) + " day"
                elif days_extended > 1:
                    overdue_by = str(days_extended) + " days"
                else:
                    overdue_by = None
        return overdue_by

    def get_task_flag(self, obj):
        TASK_TYPES = ('overdue', 'ongoing', 'upcomming')
        cur_date = datetime.now().date()
        task_flag = None

        if (obj.extended_date is not None and obj.extended_date.date() < cur_date) or (
                obj.extended_date is None and obj.end_date.date() < cur_date):
            task_flag = TASK_TYPES[0]
        elif (obj.shifted_date is not None and obj.shifted_date.date() <= cur_date) or (
                obj.shifted_date is None and obj.start_date.date() <= cur_date):
            task_flag = TASK_TYPES[1]
        elif (obj.shifted_date is not None and obj.shifted_date.date() > cur_date) or (
                obj.shifted_date is None and obj.start_date.date() > cur_date):
            task_flag = TASK_TYPES[2]
        return task_flag

    def get_parent_task(self, EtaskTask):
        if EtaskTask.parent_id:
            if EtaskTask.parent_id != 0:
                if self.sub_data.filter(id=EtaskTask.parent_id).values('id', 'task_subject', 'task_description'):
                    parent_data = \
                    self.sub_data.filter(id=EtaskTask.parent_id).values('id', 'task_subject', 'task_description')[0]
                    return parent_data

    def get_assign_to_name(self, EtaskTask):
        name = None
        full_name = ""
        if EtaskTask.assign_to:
            name = User.objects.get(id=EtaskTask.assign_to.id)
            if name:
                full_name = name.__dict__['first_name'] + " " + name.__dict__['last_name']
                return full_name

    def get_reporting_dates(self, EtaskTask):
        # if EtaskTask.id:
        #     report_date_list = []
        #     report_date = ETaskReportingDates.objects.filter(task_type=1, task=EtaskTask.id, is_deleted=False).order_by('reporting_date')
        #     if report_date:
        #         for dt in report_date:
        #             report_date_list += '{}, '.format(dt.reporting_date.strftime("%d %b %Y"))                            
        #         return report_date_list[:-2]
        #     else:
        #         return ''
        if EtaskTask.id:
            report_date_list = []
            current_date=datetime.now().date()
            login_user = self.context.get("login_user")
            report_date=ETaskReportingDates.objects.filter(task_type=1,reporting_date__gte=current_date,
                                        owned_by=login_user,task=EtaskTask.id,is_deleted=False).order_by('reporting_date').order_by('reporting_date')
            
            last_reporting_date=ETaskReportingDates.objects.filter(task_type=1,reporting_date__lt=current_date,
                                        owned_by=login_user,task=EtaskTask.id,is_deleted=False).order_by('reporting_date').order_by('-reporting_date')
            if report_date:
                for dt in report_date:
                    pre_report= dt.reporting_date.date()
                    # #print('pre_report',pre_report)
                    if pre_report>=current_date:                     
                        dt_dict={
                            'id':dt.id,
                            'reporting_date':dt.reporting_date,
                            'reporting_status':dt.get_reporting_status_display()
                        }
                        report_date_list.append(dt.reporting_date.strftime("%d %b %Y"))
                        break                             
                return ', '.join(report_date_list)
            elif last_reporting_date:
                for dt in last_reporting_date:
                    pre_report= dt.reporting_date.date()
                    # #print('pre_report',pre_report)
                    if pre_report<current_date:                     
                        dt_dict={
                            'id':dt.id,
                            'reporting_date':dt.reporting_date,
                            'reporting_status':dt.get_reporting_status_display()
                        }
                        report_date_list.append(dt.reporting_date.strftime("%d %b %Y"))
                        break                             
                return ', '.join(report_date_list)
            else:
                return ''


class ETaskAdminTaskReportSerializerV2(serializers.ModelSerializer):
    parent_task = serializers.SerializerMethodField(required=False)
    sub_data = EtaskTask.objects.filter(parent_id=0, is_deleted=False)
    task_type_name = serializers.CharField(source='get_task_type_display')
    recurrance_frequency_name = serializers.CharField(source='get_recurrance_frequency_display')
    task_status_name = serializers.CharField(source='get_task_status_display')
    assign_by_name = serializers.SerializerMethodField()
    assign_to_name = serializers.SerializerMethodField()
    sub_assign_to_user_name = serializers.SerializerMethodField()
    task_priority_name = serializers.CharField(source='get_task_priority_display')
    user_cc=serializers.SerializerMethodField()
    sub_tasks = serializers.SerializerMethodField()
    status_with_pending_request = serializers.SerializerMethodField()
    task_flag = serializers.SerializerMethodField()

    class Meta:
        model = EtaskTask
        fields = '__all__'
        extra_fields = ('user_cc','sub_tasks','status_with_pending_request','task_flag')
    
    def get_task_flag(self, obj):
        TASK_TYPES = ('closed', 'overdue', 'ongoing', 'upcoming')
        cur_date=datetime.now().date()
        task_flag = None
        if obj.task_status == 4:
            task_flag = TASK_TYPES[0]
        elif (obj.extended_date is not None and obj.extended_date.date() < cur_date) or (obj.extended_date is None and obj.end_date.date() < cur_date):
            task_flag = TASK_TYPES[1]
        elif (obj.shifted_date is not None and obj.shifted_date.date() <= cur_date) or (obj.shifted_date is None and obj.start_date.date() <= cur_date):
            task_flag = TASK_TYPES[2]
        elif (obj.shifted_date is not None and obj.shifted_date.date() > cur_date) or (obj.shifted_date is None and obj.start_date.date() > cur_date):
            task_flag = TASK_TYPES[3]
        return task_flag

    def get_status_with_pending_request(self, obj):
        cur_date=datetime.now().date()
        TASK_TYPES = ('Closed', 'Ongoing', 'Ongoing', 'Upcoming')
        status = list()
        task_extention = TaskExtentionDateMap.objects.filter(task=obj, status=1)
        if task_extention.count():
            status.append('Pending Extention')
        task_closer = TaskCompleteReopenMap.objects.filter(task=obj,status=1)
        if task_closer.count():
            status.append('Pending Closure')
        if not task_extention.count() and not task_extention.count():
            if obj.task_status == 4:
                status.append(TASK_TYPES[0])
            elif (obj.extended_date is not None and obj.extended_date.date() < cur_date) or (obj.extended_date is None and obj.end_date.date() < cur_date):
                status.append(TASK_TYPES[1])
            elif (obj.shifted_date is not None and obj.shifted_date.date() <= cur_date) or (obj.shifted_date is None and obj.start_date.date() <= cur_date):
                status.append(TASK_TYPES[2])
            elif (obj.shifted_date is not None and obj.shifted_date.date() > cur_date) or (obj.shifted_date is None and obj.start_date.date() > cur_date):
                status.append(TASK_TYPES[3])

        return ' and '.join(status)

    def get_sub_tasks(self, obj):
        sub_tasks_data = EtaskTask.objects.filter(~Q(task_status=4),parent_id=obj.id,is_deleted=False).values('id','task_subject')
        return sub_tasks_data if sub_tasks_data else list() 

    def get_user_cc(self, obj):
        user_cc=EtaskUserCC.objects.filter(task=obj,is_deleted=False).values('id','user__first_name', 'user__last_name')
        return user_cc if user_cc else list()

    def get_parent_task(self, EtaskTask):
        parent_data = None
        if EtaskTask.parent_id:
            if EtaskTask.parent_id != 0:
                if self.sub_data.filter(id=EtaskTask.parent_id).values('id', 'task_subject'):
                    task_details = self.sub_data.filter(id=EtaskTask.parent_id)
                    for t_d in task_details:
                        report_date = ETaskReportingDates.objects.filter(task_type=1, task=t_d.id,
                                                                         is_deleted=False).values('id',
                                                                                                  'reporting_date')
                        reporting_date = report_date if report_date else []
                        assign_to = t_d.assign_to.id if t_d.assign_to else None
                        assign_by = t_d.assign_by.id if t_d.assign_by else None
                        sub_assign_to_user = t_d.sub_assign_to_user.id if t_d.sub_assign_to_user else None
                        owner = t_d.owner.id if t_d.owner else None
                        parent_data = {
                            'id': t_d.id,
                            'task_code_id': t_d.task_code_id,
                            'parent_id': t_d.parent_id,
                            'owner': owner,
                            'owner_name': userdetails(owner),
                            'assign_to': assign_to,
                            'assign_to_name': userdetails(assign_to),
                            'assign_by': assign_by,
                            'assign_by_name': userdetails(assign_by),
                            'task_subject': t_d.task_subject,
                            'task_description': t_d.task_description,
                            'task_categories': t_d.task_categories,
                            'task_categories_name': t_d.get_task_categories_display(),
                            'start_date': t_d.start_date,
                            'end_date': t_d.end_date,
                            'completed_date': t_d.completed_date,
                            'closed_date': t_d.closed_date,
                            'extended_date': t_d.extended_date,
                            'extend_with_delay': t_d.extend_with_delay,
                            'task_priority': t_d.task_priority,
                            'task_priority_name': t_d.get_task_priority_display(),
                            'task_type': t_d.task_type,
                            'task_type_name': t_d.get_task_type_display(),
                            'task_status': t_d.task_status,
                            'task_status_name': t_d.get_task_status_display(),
                            'recurrance_frequency': t_d.recurrance_frequency,
                            'recurrance_frequency_name': t_d.get_recurrance_frequency_display(),
                            'sub_assign_to_user': sub_assign_to_user,
                            'sub_assign_to_user_name': userdetails(sub_assign_to_user),
                            'reporting_dates': reporting_date
                        }
                        return parent_data

    def user_name(self, user_id):
        name = None
        full_name = ""
        name = User.objects.get(id=user_id)
        if name:
            full_name = name.__dict__['first_name'] + " " + name.__dict__['last_name']
        return full_name

    def get_assign_by_name(self, EtaskTask):
        name = None
        full_name = ""
        if EtaskTask.assign_by:
            name = User.objects.get(id=EtaskTask.assign_by.id)
            if name:
                full_name = name.__dict__['first_name'] + " " + name.__dict__['last_name']
                # #print("full_name",full_name)
            return full_name

    def get_sub_assign_to_user_name(self, EtaskTask):
        name = None
        full_name = ""
        if EtaskTask.sub_assign_to_user:
            name = User.objects.get(id=EtaskTask.sub_assign_to_user.id)
            if name:
                full_name = name.__dict__['first_name'] + " " + name.__dict__['last_name']
                return full_name

    def get_assign_to_name(self, EtaskTask):
        name = None
        full_name = ""
        if EtaskTask.assign_to:
            name = User.objects.get(id=EtaskTask.assign_to.id)
            if name:
                full_name = name.__dict__['first_name'] + " " + name.__dict__['last_name']
                return full_name


class ETaskAdminTaskReportDownloadSerializerV2(serializers.ModelSerializer):
    parent_task = serializers.SerializerMethodField(required=False)
    sub_data = EtaskTask.objects.filter(parent_id=0, is_deleted=False)
    task_type_name = serializers.CharField(source='get_task_type_display')
    recurrance_frequency_name = serializers.CharField(source='get_recurrance_frequency_display')
    task_status_name = serializers.CharField(source='get_task_status_display')
    assign_by_name = serializers.SerializerMethodField()
    assign_to_name = serializers.SerializerMethodField()
    sub_assign_to_user_name = serializers.SerializerMethodField()
    task_priority_name = serializers.CharField(source='get_task_priority_display')
    startdate = serializers.SerializerMethodField()
    enddate = serializers.SerializerMethodField()
    extendeddate = serializers.SerializerMethodField()
    closerdate = serializers.SerializerMethodField()

    class Meta:
        model = EtaskTask
        fields = '__all__'
        extra_fields = ('startdate','enddate','extendeddate','closerdate')


    def get_startdate(self, obj):
        return obj.start_date.strftime("%d %b %Y") if obj.start_date else ''

    def get_enddate(self, obj):
        return obj.end_date.strftime("%d %b %Y") if obj.end_date else ''

    def get_extendeddate(self, obj):
        return obj.extended_date.strftime("%d %b %Y") if obj.extended_date else ''

    def get_closerdate(self, obj):
        return obj.closed_date.strftime("%d %b %Y") if obj.closed_date and obj.is_closure else ''

    def get_parent_task(self, EtaskTask):
        parent_data = None
        if EtaskTask.parent_id:
            if EtaskTask.parent_id != 0:
                if self.sub_data.filter(id=EtaskTask.parent_id).values('id', 'task_subject'):
                    task_details = self.sub_data.filter(id=EtaskTask.parent_id)
                    for t_d in task_details:
                        report_date = ETaskReportingDates.objects.filter(task_type=1, task=t_d.id,
                                                                         is_deleted=False).values('id',
                                                                                                  'reporting_date')
                        reporting_date = report_date if report_date else []
                        assign_to = t_d.assign_to.id if t_d.assign_to else None
                        assign_by = t_d.assign_by.id if t_d.assign_by else None
                        sub_assign_to_user = t_d.sub_assign_to_user.id if t_d.sub_assign_to_user else None
                        owner = t_d.owner.id if t_d.owner else None
                        parent_data = {
                            'id': t_d.id,
                            'task_code_id': t_d.task_code_id,
                            'parent_id': t_d.parent_id,
                            'owner': owner,
                            'owner_name': userdetails(owner),
                            'assign_to': assign_to,
                            'assign_to_name': userdetails(assign_to),
                            'assign_by': assign_by,
                            'assign_by_name': userdetails(assign_by),
                            'task_subject': t_d.task_subject,
                            'task_description': t_d.task_description,
                            'task_categories': t_d.task_categories,
                            'task_categories_name': t_d.get_task_categories_display(),
                            'start_date': t_d.start_date,
                            'end_date': t_d.end_date,
                            'completed_date': t_d.completed_date,
                            'closed_date': t_d.closed_date,
                            'extended_date': t_d.extended_date,
                            'extend_with_delay': t_d.extend_with_delay,
                            'task_priority': t_d.task_priority,
                            'task_priority_name': t_d.get_task_priority_display(),
                            'task_type': t_d.task_type,
                            'task_type_name': t_d.get_task_type_display(),
                            'task_status': t_d.task_status,
                            'task_status_name': t_d.get_task_status_display(),
                            'recurrance_frequency': t_d.recurrance_frequency,
                            'recurrance_frequency_name': t_d.get_recurrance_frequency_display(),
                            'sub_assign_to_user': sub_assign_to_user,
                            'sub_assign_to_user_name': userdetails(sub_assign_to_user),
                            'reporting_dates': reporting_date
                        }
                        return parent_data

    def user_name(self, user_id):
        name = None
        full_name = ""
        name = User.objects.get(id=user_id)
        if name:
            full_name = name.__dict__['first_name'] + " " + name.__dict__['last_name']
        return full_name

    def get_assign_by_name(self, EtaskTask):
        name = None
        full_name = ""
        if EtaskTask.assign_by:
            name = User.objects.get(id=EtaskTask.assign_by.id)
            if name:
                full_name = name.__dict__['first_name'] + " " + name.__dict__['last_name']
                # #print("full_name",full_name)
            return full_name

    def get_sub_assign_to_user_name(self, EtaskTask):
        name = None
        full_name = ""
        if EtaskTask.sub_assign_to_user:
            name = User.objects.get(id=EtaskTask.sub_assign_to_user.id)
            if name:
                full_name = name.__dict__['first_name'] + " " + name.__dict__['last_name']
                return full_name

    def get_assign_to_name(self, EtaskTask):
        name = None
        full_name = ""
        if EtaskTask.assign_to:
            name = User.objects.get(id=EtaskTask.assign_to.id)
            if name:
                full_name = name.__dict__['first_name'] + " " + name.__dict__['last_name']
                return full_name


class ETaskTeamTransferTasksListSerializerV2(serializers.ModelSerializer):
    parent_task=serializers.SerializerMethodField(required=False)
    sub_data = EtaskTask.objects.filter(parent_id=0,is_deleted=False)
    task_type_name=serializers.CharField(source='get_task_type_display')
    recurrance_frequency_name=serializers.CharField(source='get_recurrance_frequency_display')
    task_status_name=serializers.CharField(source='get_task_status_display')
    task_priority_name=serializers.CharField(source='get_task_priority_display')
    assign_by_name = serializers.SerializerMethodField()
    assign_to_name= serializers.SerializerMethodField()
    sub_assign_to_user_name= serializers.SerializerMethodField()
    reporting_dates=serializers.SerializerMethodField()
    user_cc=serializers.SerializerMethodField()
    sub_tasks = serializers.SerializerMethodField()
    task_flag = serializers.SerializerMethodField()
    status_with_pending_request = serializers.SerializerMethodField()

    class Meta:
        model = EtaskTask
        fields = ('__all__')
        extra_fields = ('user_cc','sub_tasks', 'task_flag', 'status_with_pending_request')

    def get_status_with_pending_request(self, obj):
        status = list()
        task_extention = TaskExtentionDateMap.objects.filter(task=obj, status=1)
        if task_extention.count():
            status.append('Pending Extention')
        task_closer = TaskCompleteReopenMap.objects.filter(task=obj,status=1)
        if task_closer.count():
            status.append('Pending Closure')
        if obj.task_status == 1 and not task_extention.count() and not task_extention.count():
            status.append(obj.get_task_status_display())
        return ' and '.join(status)

    def get_task_flag(self, obj):
        TASK_TYPES = ('overdue', 'ongoing', 'upcoming')
        cur_date = datetime.now().date()
        task_flag = None

        if (obj.extended_date is not None and obj.extended_date.date() < cur_date) or (
                obj.extended_date is None and obj.end_date.date() < cur_date):
            task_flag = TASK_TYPES[0]
        elif (obj.shifted_date is not None and obj.shifted_date.date() <= cur_date) or (
                obj.shifted_date is None and obj.start_date.date() <= cur_date):
            task_flag = TASK_TYPES[1]
        elif (obj.shifted_date is not None and obj.shifted_date.date() > cur_date) or (
                obj.shifted_date is None and obj.start_date.date() > cur_date):
            task_flag = TASK_TYPES[2]
        return task_flag

    def get_sub_tasks(self, obj):
        sub_tasks_data = EtaskTask.objects.filter(~Q(task_status=4),parent_id=obj.id,is_deleted=False).values('id','task_subject')
        return sub_tasks_data if sub_tasks_data else list() 

    def get_user_cc(self, obj):
        user_cc=EtaskUserCC.objects.filter(task=obj,is_deleted=False).values('id','user__first_name', 'user__last_name')
        return user_cc if user_cc else list()

    def get_parent_task(self,EtaskTask):
        if EtaskTask.parent_id:
            if EtaskTask.parent_id !=0:
                if self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject','task_description'):
                    parent_data=self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject','task_description')[0]
                    return parent_data

    def user_name(self, user_id):
        name = None
        full_name = ""
        name = User.objects.get(id=user_id)
        if name:
            full_name =  name.__dict__['first_name']+" "+name.__dict__['last_name']
        return full_name

    def get_assign_by_name(self,EtaskTask):
        name = None
        full_name = ""
        if EtaskTask.assign_by:
            name = User.objects.get(id=EtaskTask.assign_by.id)
            if name:
                full_name =  name.__dict__['first_name']+" "+name.__dict__['last_name']
                # #print("full_name",full_name)
            return full_name

    def get_sub_assign_to_user_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.sub_assign_to_user:
            name=User.objects.get(id=EtaskTask.sub_assign_to_user.id)
            if name:
                full_name= name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name

    def get_assign_to_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.assign_to:
            name =User.objects.get(id=EtaskTask.assign_to.id)
            if name:
                full_name=name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name

    def get_reporting_dates(self,EtaskTask):
        if EtaskTask.id:
            report_date_list = []
            report_date=ETaskReportingDates.objects.filter(task_type=1,task=EtaskTask.id,is_deleted=False).order_by('reporting_date')
            # #print("report_date",report_date)
            if report_date:
                for dt in report_date:
                    dt_dict={
                        'id':dt.id,
                        'reporting_date':dt.reporting_date,
                    }
                    report_date_list.append(dt_dict)
                return report_date_list
            else:
                return []


class ETaskTeamOwnershipTransferTaskListSerializer(serializers.ModelSerializer):
    parent_task=serializers.SerializerMethodField(required=False)
    sub_data = EtaskTask.objects.filter(parent_id=0,is_deleted=False)
    task_type_name=serializers.CharField(source='get_task_type_display')
    recurrance_frequency_name=serializers.CharField(source='get_recurrance_frequency_display')
    task_status_name=serializers.CharField(source='get_task_status_display')
    task_priority_name=serializers.CharField(source='get_task_priority_display')
    assign_by_name = serializers.SerializerMethodField()
    assign_to_name= serializers.SerializerMethodField()
    sub_assign_to_user_name= serializers.SerializerMethodField()
    reporting_dates=serializers.SerializerMethodField()
    user_cc=serializers.SerializerMethodField()
    sub_tasks = serializers.SerializerMethodField()
    task_flag = serializers.SerializerMethodField()
    status_with_pending_request = serializers.SerializerMethodField()

    class Meta:
        model = EtaskTask
        fields = ('__all__')
        extra_fields = ('user_cc','sub_tasks', 'task_flag','status_with_pending_request')

    def get_status_with_pending_request(self, obj):
        status = list()
        task_extention = TaskExtentionDateMap.objects.filter(task=obj, status=1)
        if task_extention.count():
            status.append('Pending Extention')
        task_closer = TaskCompleteReopenMap.objects.filter(task=obj,status=1)
        if task_closer.count():
            status.append('Pending Closure')
        if obj.task_status == 1 and not task_extention.count() and not task_extention.count():
            status.append(obj.get_task_status_display())
        return ' and '.join(status)

    def get_task_flag(self, obj):
        TASK_TYPES = ('overdue', 'ongoing', 'upcoming')
        cur_date = datetime.now().date()
        task_flag = None

        if (obj.extended_date is not None and obj.extended_date.date() < cur_date) or (
                obj.extended_date is None and obj.end_date.date() < cur_date):
            task_flag = TASK_TYPES[0]
        elif (obj.shifted_date is not None and obj.shifted_date.date() <= cur_date) or (
                obj.shifted_date is None and obj.start_date.date() <= cur_date):
            task_flag = TASK_TYPES[1]
        elif (obj.shifted_date is not None and obj.shifted_date.date() > cur_date) or (
                obj.shifted_date is None and obj.start_date.date() > cur_date):
            task_flag = TASK_TYPES[2]
        return task_flag

    def get_sub_tasks(self, obj):
        sub_tasks_data = EtaskTask.objects.filter(~Q(task_status=4),parent_id=obj.id,is_deleted=False).values('id','task_subject')
        return sub_tasks_data if sub_tasks_data else list() 

    def get_user_cc(self, obj):
        user_cc=EtaskUserCC.objects.filter(task=obj,is_deleted=False).values('id','user__first_name', 'user__last_name')
        return user_cc if user_cc else list()

    def get_parent_task(self,EtaskTask):
        if EtaskTask.parent_id:
            if EtaskTask.parent_id !=0:
                if self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject','task_description'):
                    parent_data=self.sub_data.filter(id=EtaskTask.parent_id).values('id','task_subject','task_description')[0]
                    return parent_data

    def user_name(self, user_id):
        name = None
        full_name = ""
        name = User.objects.get(id=user_id)
        if name:
            full_name =  name.__dict__['first_name']+" "+name.__dict__['last_name']
        return full_name

    def get_assign_by_name(self,EtaskTask):
        name = None
        full_name = ""
        if EtaskTask.assign_by:
            name = User.objects.get(id=EtaskTask.assign_by.id)
            if name:
                full_name =  name.__dict__['first_name']+" "+name.__dict__['last_name']
                # #print("full_name",full_name)
            return full_name

    def get_sub_assign_to_user_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.sub_assign_to_user:
            name=User.objects.get(id=EtaskTask.sub_assign_to_user.id)
            if name:
                full_name= name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name

    def get_assign_to_name(self,EtaskTask):
        name=None
        full_name=""
        if EtaskTask.assign_to:
            name =User.objects.get(id=EtaskTask.assign_to.id)
            if name:
                full_name=name.__dict__['first_name']+" "+name.__dict__['last_name']
                return full_name

    def get_reporting_dates(self,EtaskTask):
        if EtaskTask.id:
            report_date_list = []
            report_date=ETaskReportingDates.objects.filter(task_type=1,task=EtaskTask.id,is_deleted=False).order_by('reporting_date')
            # #print("report_date",report_date)
            if report_date:
                for dt in report_date:
                    dt_dict={
                        'id':dt.id,
                        'reporting_date':dt.reporting_date,
                    }
                    report_date_list.append(dt_dict)
                return report_date_list
            else:
                return []


class EtaskExtensionsRequestedListSerializer(serializers.ModelSerializer):
    parent_task = serializers.SerializerMethodField(required=False)
    sub_data = EtaskTask.objects.filter(parent_id=0, is_deleted=False)
    task_type_name = serializers.CharField(source='get_task_type_display')
    recurrance_frequency_name = serializers.CharField(source='get_recurrance_frequency_display')
    task_status_name = serializers.CharField(source='get_task_status_display')
    task_priority_name = serializers.CharField(source='get_task_priority_display')
    assign_by_name = serializers.SerializerMethodField()
    assign_to_name = serializers.SerializerMethodField()
    sub_assign_to_user_name = serializers.SerializerMethodField()
    reporting_dates = serializers.SerializerMethodField()
    sub_tasks = serializers.SerializerMethodField()

    class Meta:
        model = EtaskTask
        fields = '__all__'
        extra_fields = ('sub_tasks',)

    def get_sub_tasks(self, obj):
        sub_tasks_data = EtaskTask.objects.filter(~Q(task_status=4),parent_id=obj.id,is_deleted=False).values('id','task_subject')
        return sub_tasks_data if sub_tasks_data else list() 

    def get_parent_task(self, EtaskTask):
        if EtaskTask.parent_id:
            if EtaskTask.parent_id != 0:
                if self.sub_data.filter(id=EtaskTask.parent_id).values('id', 'task_subject', 'task_description'):
                    parent_data = \
                    self.sub_data.filter(id=EtaskTask.parent_id).values('id', 'task_subject', 'task_description')[0]
                    return parent_data

    def user_name(self, user_id):
        name = None
        full_name = ""
        name = User.objects.get(id=user_id)
        if name:
            full_name = name.__dict__['first_name'] + " " + name.__dict__['last_name']
        return full_name

    def get_assign_by_name(self, EtaskTask):
        name = None
        full_name = ""
        if EtaskTask.assign_by:
            name = User.objects.get(id=EtaskTask.assign_by.id)
            if name:
                full_name = name.__dict__['first_name'] + " " + name.__dict__['last_name']
                # #print("full_name",full_name)
            return full_name

    def get_sub_assign_to_user_name(self, EtaskTask):
        name = None
        full_name = ""
        if EtaskTask.sub_assign_to_user:
            name = User.objects.get(id=EtaskTask.sub_assign_to_user.id)
            if name:
                full_name = name.__dict__['first_name'] + " " + name.__dict__['last_name']
                return full_name

    def get_assign_to_name(self, EtaskTask):
        name = None
        full_name = ""
        if EtaskTask.assign_to:
            name = User.objects.get(id=EtaskTask.assign_to.id)
            if name:
                full_name = name.__dict__['first_name'] + " " + name.__dict__['last_name']
                return full_name

    def get_reporting_dates(self, EtaskTask):
        if EtaskTask.id:
            report_date_list = []
            report_date = ETaskReportingDates.objects.filter(task_type=1, task=EtaskTask.id, is_deleted=False).order_by('reporting_date')
            # #print("report_date",report_date)
            if report_date:
                for dt in report_date:
                    dt_dict = {
                        'id': dt.id,
                        'reporting_date': dt.reporting_date,
                        'reporting_status': dt.reporting_status,
                        'reporting_status_name': dt.get_reporting_status_display()

                    }
                    report_date_list.append(dt_dict)

                return report_date_list
            else:
                return []