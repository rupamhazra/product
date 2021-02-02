from attendance.models import *
from datetime import date,time
from datetime import datetime,timedelta
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from etask.models import *
from master.models import *
from master.models import TMasterModuleRole
from django.contrib.auth.models import *
from django.db import transaction, IntegrityError
from drf_extra_fields.fields import Base64ImageField
import os
from django.db.models import Sum
from custom_exception_message import *
from mailsend.views import *
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from users.models import TCoreUserDetail
from smssend.views import *
from threading import Thread
from django.db.models import When, Case, Value, CharField, IntegerField, F, Q
from holidays.models import *
from global_notification import send_notification, store_sent_notification
from pms.models import PmsTourAndTravelExpenseMaster,PmsTourAndTravelApprovalIntervalDaysMailOrNotificationConf,PmsTourHoUser,PmsTourAccounts
import requests
from global_function import userdetails,create_appointment,send_mail_list,get_last_day_of_month

def leave_calulate(employee_id,total_month_grace):
    total_grace={}
    date_object = datetime.now().date()
    print('employee_id',employee_id)
    advance_leave=EmployeeAdvanceLeaves.objects.filter(Q(employee=employee_id)&
                                                        Q(is_deleted=False)&
                                                        (Q(approved_status='pending')|Q(approved_status='approved'))
                                                        ).values('leave_type','start_date','end_date')
    print('advance_leave',advance_leave)     
    advance_cl=0
    advance_el=0
    advance_ab=0           
    day=0

    # date =self.request.query_params.get('employee', None)
    if advance_leave:
        for leave in advance_leave.iterator():
            #print('leave',leave)
            start_date=leave['start_date'].date()
            end_date=leave['end_date'].date()+timedelta(days=1)
            #print('start_date,end_date',start_date,end_date)
            if date_object < end_date:
                if date_object < start_date:
                    day=(end_date-start_date).days 
                    #print('day',day)
                elif date_object > start_date:
                    day=(end_date-date_object).days
                    #print('day2',day)
                else:
                    day=(end_date-date_object).days

            if leave['leave_type']=='CL':
                advance_cl+=day
                #print('advance_cl_1',advance_cl)
            elif leave['leave_type']=='EL':
                advance_el+=day
                #print('advance_el_2',advance_el)
            elif leave['leave_type']=='AB':
                advance_ab+=day

        

    print('advance_cl',advance_cl,type(advance_cl))
    print('advance_el',advance_el,type(advance_el))


    
    """ 
    LEAVE CALCULATION:-
    1)SINGLE LEAVE CALCULATION
    2)MULTIPLE LEAVE FOR ONE DAY IS AUTO CONVERTED TO ONE TYPE OF LEAVE 
    CREATED & EDITED BY :- Abhishek.singh@shyamfuture.com
    
    """ 
    #starttime = datetime.now()
    availed_hd_cl=0.0
    availed_hd_el=0.0
    availed_hd_sl=0.0
    availed_hd_ab=0.0
    availed_cl=0.0
    availed_el=0.0
    availed_sl=0.0
    availed_ab=0.0

    attendence_daily_data = AttendanceApprovalRequest.objects.filter(((Q(leave_type_changed_period__isnull=False)&(Q(leave_type_changed_period='FD')|Q(leave_type_changed_period='HD')))|
                                                                    (Q(leave_type_changed_period__isnull=True)&(Q(request_type='FD')|Q(request_type='HD')))),
                                                                    attendance__employee=employee_id,is_requested=True).values('duration_start__date').distinct()
    print("attendence_daily_data",attendence_daily_data)
    date_list = [x['duration_start__date'] for x in attendence_daily_data.iterator()]
    #print("date_list",date_list)
    # for data in attendence_daily_data.iterator():
        # print(datetime.now())
    availed_master_wo_reject_fd = AttendanceApprovalRequest.objects.\
            filter((Q(approved_status='pending')|Q(approved_status='approved')|Q(approved_status='reject')),
                    (Q(leave_type__isnull=False)|Q(leave_type_changed_period__isnull=False)),
                    attendance__employee=employee_id,
                    attendance_date__in=date_list,is_requested=True,is_deleted=False).annotate(
                        leave_type_final = Case(
                        When((Q(leave_type_changed_period__isnull=False)&Q(leave_type_changed_period='FD')),then=F('leave_type_changed')),
                        When((Q(leave_type_changed_period__isnull=True)&Q(request_type='FD')),then=F('leave_type')),
                        output_field=CharField()
                    ),
                    leave_type_final_hd = Case(
                        When((Q(leave_type_changed_period__isnull=False)&Q(leave_type_changed_period='HD')),then=F('leave_type_changed')),
                        When((Q(leave_type_changed_period__isnull=True)&Q(request_type='HD')),then=F('leave_type')),
                        output_field=CharField()
                    ),
                    ).values('leave_type_final','leave_type_final_hd','attendance_date').distinct()
    print("availed_master_wo_reject_fd",availed_master_wo_reject_fd)
    if availed_master_wo_reject_fd:

        for data in date_list:
            availed_FD=availed_master_wo_reject_fd.filter(attendance_date=data)
            
            #print("availed_HD",availed_FD)
            if availed_FD.filter(leave_type_final__isnull=False):
                if availed_FD.values('leave_type_final').count() >1:
                    if availed_FD.filter(leave_type_final='AB'):
                        availed_ab=availed_ab+1.0

                    elif availed_FD.filter(leave_type_final='CL'):
                        availed_cl=availed_cl+1.0
                                

                else:
                    l_type=availed_FD[0]['leave_type_final']
                    if l_type == 'CL':
                        availed_cl=availed_cl+1.0
                    elif l_type == 'EL':
                        availed_el=availed_el+1.0
                    elif l_type == 'SL':
                        availed_sl=availed_sl+1.0
                    elif l_type == 'AB':
                        availed_ab=availed_ab+1.0

            elif availed_FD.filter(leave_type_final_hd__isnull=False):
                if availed_FD.values('leave_type_final_hd').count() >1:
                    if availed_FD.filter(leave_type_final_hd='AB'):
                        availed_hd_ab=availed_hd_ab+1.0

                    elif availed_FD.filter(leave_type_final_hd='CL'):
                        availed_hd_cl=availed_hd_cl+1.0
                                

                else:
                    l_type=availed_FD[0]['leave_type_final_hd']
                    if l_type == 'CL':
                        availed_hd_cl=availed_hd_cl+1.0
                    elif l_type == 'EL':
                        availed_hd_el=availed_hd_el+1.0
                    elif l_type == 'SL':
                        availed_hd_sl=availed_hd_sl+1.0
                    elif l_type == 'AB':
                        availed_hd_ab=availed_hd_ab+1.0
    

    

    print("availed_cl",availed_cl,type(availed_cl))
    print("availed_el",availed_el,type(availed_el))

    print('availed_hd_cl',availed_hd_cl/2.0,type(availed_hd_cl/2.0))
    print('availed_hd_el',availed_hd_el/2.0,type(availed_hd_el/2.0))

    # if employee_id == '1881':
    #     total_grace['availed_cl']= 20.0
    #     print("total_grace['availed_cl']",total_grace['availed_cl'])

    #     total_grace['availed_el']=0.0
    #     print("total_grace['availed_el']",total_grace['availed_el'])
    #     total_grace['availed_sl']=float(availed_sl)+float(availed_hd_sl/2.0)
    #     print("total_grace['availed_sl']",total_grace['availed_sl'])
    #     total_grace['availed_ab']=float(availed_ab)+float(advance_ab)+float(availed_hd_ab/2.0)
    # else:
    total_grace['availed_cl']= float(availed_cl)+ float(advance_cl) +(float(availed_hd_cl)/2.0)
    print("total_grace['availed_cl']",total_grace['availed_cl'])

    total_grace['availed_el']=float(availed_el)+float(advance_el)+float(availed_hd_el/2.0)
    print("total_grace['availed_el']",total_grace['availed_el'])
    total_grace['availed_sl']=float(availed_sl)+float(availed_hd_sl/2.0)
    print("total_grace['availed_sl']",total_grace['availed_sl'])
    total_grace['availed_ab']=float(availed_ab)+float(advance_ab)+float(availed_hd_ab/2.0)


    # print("total_grace['availed_ab']",total_grace['availed_ab'])

    # total_grace['total_availed_leave']=total_grace['availed_cl'] +total_grace['availed_el'] + total_grace['availed_sl']
    core_user_detail=TCoreUserDetail.objects.filter(cu_user=employee_id,cu_is_deleted=False).values('joining_date',
                                                                                        'granted_cl',
                                                                                        'granted_sl',
                                                                                        'granted_el',
                                                                                        'is_confirm',
                                                                                        'salary_type__st_name'
                                                                                        )
    print('core_user_detail',core_user_detail)

    if core_user_detail:
        if core_user_detail[0]['salary_type__st_name']=='13' and core_user_detail[0]['is_confirm'] is False:
            total_grace['is_confirm'] = False
        else:
            total_grace['is_confirm'] = True
            # print("core_user_detail[0]['joining_date']",core_user_detail[0]['joining_date'],"total_month_grace[0]['year_start_date']",total_month_grace[0]['year_start_date'])
        if core_user_detail[0]['joining_date']>total_month_grace[0]['year_start_date']:
            approved_leave=JoiningApprovedLeave.objects.filter(employee=employee_id,is_deleted=False).values('cl', 'el', 'sl',
                                                                                                            'year', 'month',
                                                                                                            'first_grace')
            if approved_leave:
                total_grace['granted_cl']=approved_leave[0]['cl']
                total_grace['cl_balance']=float(approved_leave[0]['cl'] if approved_leave[0]['cl'] else 0.0) - float(total_grace['availed_cl'])
                total_grace['granted_el']=approved_leave[0]['el']
                total_grace['el_balance']=float(approved_leave[0]['el'] if approved_leave[0]['el'] else 0.0 ) - float(total_grace['availed_el'])
                total_grace['granted_sl']=approved_leave[0]['sl']
                total_grace['sl_balance']=float( approved_leave[0]['sl'] if approved_leave[0]['sl'] else 0.0 ) - float(total_grace['availed_sl'])
                # total_grace['total_granted_leave']=float(approved_leave[0]['cl'] if approved_leave[0]['cl'] else 0.0) + float(approved_leave[0]['el'] if approved_leave[0]['el'] else 0.0) + float(approved_leave[0]['sl'] if approved_leave[0]['sl'] else 0.0)
                # total_grace['total_leave_balances']=float(total_grace['total_granted_leave']) - float(total_grace['total_availed_leave'])
                if total_month_grace[0]['month']==approved_leave[0]['month']:    #for joining month only
                    total_grace['total_month_grace']=approved_leave[0]['first_grace']
                    total_grace['month_start']=core_user_detail[0]['joining_date']
                    # total_grace['grace_balance']=total_grace['total_month_grace'] - total_grace['availed_grace']
        else:

            # total_grace['granted_cl']=core_user_detail[0]['granted_cl']
            print("granted cl",core_user_detail[0]['granted_cl'],type(core_user_detail[0]['granted_cl']))
            print("availed_cl cl",total_grace['availed_cl'],type(total_grace['availed_cl']))
            total_grace['cl_balance']=float(core_user_detail[0]['granted_cl']) -  float(total_grace['availed_cl'])
            total_grace['granted_el']=core_user_detail[0]['granted_el']
            total_grace['el_balance']=float(core_user_detail[0]['granted_el']) - float(total_grace['availed_el'])
            total_grace['granted_sl']=core_user_detail[0]['granted_sl']
            total_grace['sl_balance']=float(core_user_detail[0]['granted_sl']) - float(total_grace['availed_sl'])
            # total_grace['total_granted_leave']=float(core_user_detail[0]['granted_cl']) + float(core_user_detail[0]['granted_el']) + float(core_user_detail[0]['granted_sl'])
            # total_grace['total_leave_balances']=float(total_grace['total_granted_leave']) - float(total_grace['total_availed_leave'])

    return total_grace 


def my_attendence_lock_job():
    print("LOG ENTRY FOR LOCK OF ATTENDENCE ON " ,datetime.now())
    try:
        date_object = datetime.now().date()
        current_date = datetime.now().date()
        current_month = current_date.month
        total_month_grace=AttendenceMonthMaster.objects.filter(month=current_month,is_deleted=False).values('lock_date__date'
                                                ,'year_start_date','year_end_date','month','month_start__date','month_end__date')
        # print("total_month_grace",total_month_grace)
        with transaction.atomic():
            if current_date == total_month_grace[0]['lock_date__date']:
                # user_details = TCoreUserDetail.objects.filter((~Q(cu_user__in=TMasterModuleRoleUser.objects.filter(Q(mmr_type=1)|
                #                                         Q(mmr_type=6)|Q(mmr_is_deleted=True)).values_list('mmr_user',flat=True))),
                #                                         (~Q(cu_punch_id__in=['PMSSITE000','#N/A',''])),
                #                                         cu_is_deleted=False).values_list('cu_user',flat=True).distinct()
                user_details=TMasterModuleRoleUser.objects.filter(
                    ~Q(mmr_user_id__in=(TCoreUserDetails.objects.filter(
                        cu_punch_id__in=('10111032','10011271','10111036','00000160','00000171','00000022','00000168','00000163',
                            '00000161','00000016','00000018','00000162')))),
                Q(mmr_type=3),Q(mmr_is_deleted=False),
                            Q(mmr_module__cm_name='ATTENDANCE & HRMS')).values_list('mmr_user',flat=True).distinct()
            
                print('user_details',user_details)
                for employee_id in user_details:
                    
                    '''
                        For Testing Pupose leave check before OD Approval
                    '''
                    total_grace_finalbefore = leave_calulate(employee_id,total_month_grace)
                    print("loop before od ",total_grace_finalbefore)
                    # print("employee_id",employee_id)
                    attendence_ids=AttendanceApprovalRequest.objects.filter(attendance_date__gte=total_month_grace[0]['month_start__date'],
                                                        attendance_date__lte=total_month_grace[0]['month_end__date'],is_late_conveyance=False,
                                                        is_requested=False,is_deleted=False,attendance__employee=employee_id).values_list('attendance',flat=True).distinct()
                    # print("attendence_ids",attendence_ids)
                    #OD AUTO APPROVAL
                    od_app_req_id=AttendanceApprovalRequest.objects.filter((Q(request_type='POD')|Q(request_type='FOD')),attendance__employee=employee_id
                                                                            ,is_requested=True,approved_status='pending').values_list('id',flat=True).distinct()
                    for app_req_id in list(od_app_req_id):
                        total_grace_final = leave_calulate(employee_id,total_month_grace)
                        print("Inside loop od grace",total_grace_final)
                        duration_length=AttendanceApprovalRequest.objects.get(id=app_req_id,
                                                                    is_requested=True).duration
                        if duration_length < 240:
                            if total_grace_final['cl_balance'] > 0.0:

                                update_auto = AttendanceApprovalRequest.objects.filter(id=app_req_id,is_late_conveyance=False,
                                                                        is_requested=True).\
                                                                            update(leave_type_changed_period='HD',leave_type_changed='CL',
                                                                            approved_status='approved',remarks='AUTO OD CONVERTED TO LEAVE & APPROVED')
                            elif total_grace_final['el_balance'] > 0.0:

                                update_auto = AttendanceApprovalRequest.objects.filter(id=app_req_id,is_late_conveyance=False,
                                                                        is_requested=True).\
                                                                            update(leave_type_changed_period='HD',leave_type_changed='EL',
                                                                            approved_status='approved',remarks='AUTO OD CONVERTED TO LEAVE & APPROVED')
                            else:

                                update_auto =AttendanceApprovalRequest.objects.filter(id=app_req_id,is_late_conveyance=False,
                                                                        is_requested=True).\
                                                                            update(leave_type_changed_period='HD',leave_type_changed='AB',
                                                                            approved_status='approved',remarks='AUTO OD CONVERTED TO LEAVE & APPROVED')
                        else:
                            if total_grace_final['cl_balance'] > 0.5:

                                update_auto =AttendanceApprovalRequest.objects.filter(id=app_req_id,is_late_conveyance=False,
                                                                        is_requested=True).\
                                                                            update(leave_type_changed_period='FD',leave_type_changed='CL',
                                                                            approved_status='approved',remarks='AUTO OD CONVERTED TO LEAVE & APPROVED')
                            elif total_grace_final['el_balance'] > 0.5:

                                update_auto = AttendanceApprovalRequest.objects.filter(id=app_req_id,is_late_conveyance=False,
                                                                        is_requested=True).\
                                                                            update(leave_type_changed_period='FD',leave_type_changed='EL',
                                                                            approved_status='approved',remarks='AUTO OD CONVERTED TO LEAVE & APPROVED')
                            else:

                                update_auto = AttendanceApprovalRequest.objects.filter(id=app_req_id,is_late_conveyance=False,
                                                                        is_requested=True).\
                                                                            update(leave_type_changed_period='FD',leave_type_changed='AB',
                                                                            approved_status='approved',remarks='AUTO OD CONVERTED TO LEAVE & APPROVED')                       
                
                    total_grace_final2 = leave_calulate(employee_id,total_month_grace)
                    print("after od leave calculate",total_grace_final2) 
                    for att_id in list(attendence_ids):
                        total_grace_final2 = leave_calulate(employee_id,total_month_grace)
                        print("Inside loop not requested grace",total_grace_final2)
                        duration_length=AttendanceApprovalRequest.objects.filter(attendance=att_id,is_late_conveyance=False,
                                                                    checkin_benchmark=False,is_requested=False).aggregate(Sum('duration'))['duration__sum']
                        print('duration_length',duration_length,'att_id',att_id)
                        if duration_length is not None and duration_length < 240:
                            if total_grace_final2['cl_balance'] > 0.0:

                                update_auto = AttendanceApprovalRequest.objects.filter(attendance=att_id,is_late_conveyance=False,
                                                                        checkin_benchmark=False,is_requested=False).\
                                                                            update(request_type='HD',leave_type='CL',justification='AUTO',is_requested=True,
                                                                            approved_status='approved',remarks='AUTO LEAVE APPROVED')
                            elif total_grace_final2['el_balance'] > 0.0:

                                update_auto = AttendanceApprovalRequest.objects.filter(attendance=att_id,is_late_conveyance=False,
                                                                        checkin_benchmark=False,is_requested=False).\
                                                                            update(request_type='HD',leave_type='EL',justification='AUTO',is_requested=True,
                                                                            approved_status='approved',remarks='AUTO LEAVE APPROVED')
                            else:

                                update_auto = AttendanceApprovalRequest.objects.filter(attendance=att_id,is_late_conveyance=False,
                                                                        checkin_benchmark=False,is_requested=False).\
                                                                            update(request_type='HD',leave_type='AB',justification='AUTO',is_requested=True,
                                                                            approved_status='approved',remarks='AUTO LEAVE APPROVED')
                        else:
                            if total_grace_final2['cl_balance'] > 0.5:

                                update_auto = AttendanceApprovalRequest.objects.filter(attendance=att_id,is_late_conveyance=False,
                                                                        checkin_benchmark=False,is_requested=False).\
                                                                            update(request_type='FD',leave_type='CL',justification='AUTO',is_requested=True,
                                                                            approved_status='approved',remarks='AUTO LEAVE APPROVED')
                            elif total_grace_final2['el_balance'] > 0.5:

                                update_auto = AttendanceApprovalRequest.objects.filter(attendance=att_id,is_late_conveyance=False,
                                                                        checkin_benchmark=False,is_requested=False).\
                                                                            update(request_type='FD',leave_type='EL',justification='AUTO',is_requested=True,
                                                                            approved_status='approved',remarks='AUTO LEAVE APPROVED')
                            else:

                                update_auto = AttendanceApprovalRequest.objects.filter(attendance=att_id,is_late_conveyance=False,
                                                                        checkin_benchmark=False,is_requested=False).\
                                                                            update(request_type='FD',leave_type='AB',justification='AUTO',is_requested=True,
                                                                            approved_status='approved',remarks='AUTO LEAVE APPROVED')                        
                    #for checking
                    total_grace_final2 = leave_calulate(employee_id,total_month_grace)
                    print("after grace leave calculate",total_grace_final2) 
                    auto_grace_approval =AttendanceApprovalRequest.objects.filter(attendance__employee=employee_id,
                                                                            is_requested=True,request_type='GR',approved_status='pending').\
                                                                                update(approved_status='approved',remarks='AUTO GRACE APPROVED')

                    auto_misspunch_approval =AttendanceApprovalRequest.objects.filter(attendance__employee=employee_id,
                                                                            is_requested=True,request_type='MP',approved_status='pending').\
                                                                                update(approved_status='approved',remarks='AUTO MISSPUNCH APPROVED') 
                    
                print("entered or noyt ")                                                                             
                lock=AttendanceApprovalRequest.objects.filter(attendance_date__gte=total_month_grace[0]['month_start__date'],
                                                        attendance_date__lte=total_month_grace[0]['month_end__date'],
                                                        is_deleted=False).\
                                                            update(lock_status=True)
                print("lock",lock)   

        return True

    except Exception as e:
        raise e


def my_attendence_mail_before_lock_job():

    '''
        ATTENDENCE REMINDER FOR ALL HRMS & ATTENDENCE USER 
    '''

    current_date = datetime.now().date()
    current_month = current_date.month
    print("current_date",current_date)

    total_month_grace=AttendenceMonthMaster.objects.filter(
        month=current_month,is_deleted=False).values(
        'lock_date__date','year_start_date','year_end_date',
        'month','month_start__date','month_end__date',
        'pending_action_mail__date')

    print("total_month_grace",total_month_grace)
    days_cnt = (total_month_grace[0]['lock_date__date'] - total_month_grace[0]['pending_action_mail__date']).days
    date_generated = [total_month_grace[0]['pending_action_mail__date'] + timedelta(days=x) for x in range(0,days_cnt)]

    print("date_day",date_generated)
    if current_date in date_generated:
        print("entered",current_date)
        #working query local and live 
        user_list=TMasterModuleRoleUser.objects.\
                    filter(
                        Q(mmr_type=3),Q(mmr_is_deleted=False),
                        Q(mmr_module__cm_name='ATTENDANCE & HRMS')).\
                        values_list('mmr_user',flat=True).distinct()
        #email extraction            
        user_mail_list_primary=TMasterModuleRoleUser.objects.\
                    filter(
                        Q(mmr_type=3),Q(mmr_is_deleted=False),
                        Q(mmr_module__cm_name='ATTENDANCE & HRMS'),
                        (Q(mmr_user__email__isnull=False) & ~Q(mmr_user__email=""))).\
                        values('mmr_user__email').distinct()

        user_mail_official = TCoreUserDetail.objects.filter(
            (Q(cu_alt_email_id__isnull=False) & ~Q(cu_alt_email_id="")),cu_user__in=list(user_list)).\
                values('cu_alt_email_id').distinct()
        # print("user_mail_list_primary",user_mail_list_primary)
        # print("user_mail_official",user_mail_official)
        umlp = [x['mmr_user__email'] for x in user_mail_list_primary]
        uma = [x['cu_alt_email_id'] for x in user_mail_official]

        user_mail_list = list(set(umlp + uma))
        print("user_mail_list",user_mail_list)

        
        
    #     emp_mob = TCoreUserDetail.objects.filter(cu_user__in=list(user_list),cu_phone_no__isnull=False).\
    #         values('cu_phone_no').distinct()
    #     emp_mob_no = [ x['cu_phone_no'] for x in emp_mob ]

        print("user_mail_list",user_mail_list)

        '''
            MAIL Functionality
        '''

        print("email",user_mail_list)
        if user_mail_list:
            mail_data = {
            'name':None
            }
            print('mail_data',mail_data)
            mail_list=[]
            while len(user_mail_list)>0:
                dummy_mail_list = user_mail_list[0:5]
                user_mail_list = list(set(user_mail_list) - set(dummy_mail_list ))
                print("user_mail_list",user_mail_list)
                mail_class = GlobleMailSend('ATP-PM', dummy_mail_list)
                mail_thread = Thread(target = mail_class.mailsend, args = (mail_data,None))
                mail_thread.start()
        
        '''
            SMS Functionality
        '''
        if emp_mob_no:
            message_data = {
                'name':None
            }
            sms_class = GlobleSmsSendTxtLocal('ATTPR',emp_mob_no)
            sms_thread = Thread(target = sms_class.sendSMS, args = (message_data,'sms'))
            sms_thread.start()

    return True


def attendence_mail_hod_pending_approval_job():
    user_mail_official = TCoreUserDetail.objects.filter(
        (Q(cu_alt_email_id__isnull=False) & ~Q(cu_alt_email_id="")),cu_user__in=list(user_list)).\
            values('cu_alt_email_id').distinct()
    print("user_mail_list_primary",user_mail_list_primary)
    print("user_mail_official",user_mail_official)
    umlp = [x['mmr_user__email'] for x in user_mail_list_primary]
    uma = [x['cu_alt_email_id'] for x in user_mail_official]

    user_mail_list = list(set(umlp + uma))

    emp_mob = TCoreUserDetail.objects.filter(cu_user__in=list(user_list),cu_phone_no__isnull=False).\
        values('cu_phone_no').distinct()
    emp_mob_no = [ x['cu_phone_no'] for x in emp_mob ]
    print("user_mail_list",user_mail_list)
    # ============= Mail Send Step ==============#

    print("email",user_mail_list)
    if user_mail_list:
        # for email in email_list:
        mail_data = {
        'name':None
        }
        print('mail_data',mail_data)
        for mail in user_mail_list:
            mail_class = GlobleMailSend('ATAP-PM', user_mail_list)
            print('mail_class',mail_class)
            mail_thread = Thread(target = mail_class.mailsend, args = (mail_data,None))
            mail_thread.start()
    
    #===============================================#

    # ============= Sms Send Step ==============#

    message_data = {
        'name':None
    }
    sms_class = GlobleSmsSendTxtLocal('ATTAPR',emp_mob_no)
    # sms_class = GlobleSmsSendTxtLocal('ATTPR',['7595914029'])
    sms_thread = Thread(target = sms_class.sendSMS, args = (message_data,'sms'))
    sms_thread.start()


    return True

'''
    @ Added by Rupam Hazra
'''
def my_attendence_pending_mail_on_every_week():

    '''
        ATTENDENCE REMINDER FOR ALL HRMS & ATTENDENCE USER 
    '''
    print('Current Time :: ',datetime.now())
    # current_date = datetime.now().date()
    # current_month = current_date.month
    # print("current_date",current_date)

    # user_list=TMasterModuleRoleUser.objects.filter(
    #                 Q(mmr_type=3),Q(mmr_is_deleted=False),
    #                 Q(mmr_module__cm_name='ATTENDANCE & HRMS')).\
    #                 values_list('mmr_user',flat=True).distinct()
    # #email extraction            
    # user_mail_list_primary=TMasterModuleRoleUser.objects.filter(
    #                 Q(mmr_type=3),Q(mmr_is_deleted=False),
    #                 Q(mmr_module__cm_name='ATTENDANCE & HRMS'),
    #                 (Q(mmr_user__email__isnull=False) & ~Q(mmr_user__email=""))).\
    #                 values('mmr_user__email').distinct()

    # user_mail_official = TCoreUserDetail.objects.filter(
    #     (Q(cu_alt_email_id__isnull=False) & ~Q(cu_alt_email_id="")),cu_user__in=list(user_list)).\
    #         values('cu_alt_email_id').distinct()
    # # print("user_mail_list_primary",user_mail_list_primary)
    # # print("user_mail_official",user_mail_official)
    # umlp = [x['mmr_user__email'] for x in user_mail_list_primary]
    # uma = [x['cu_alt_email_id'] for x in user_mail_official]

    # user_mail_list = list(set(umlp + uma))
    # print("user_mail_list",user_mail_list)
    
    # emp_mob = TCoreUserDetail.objects.filter(cu_user__in=list(user_list),cu_phone_no__isnull=False).\
    #     values('cu_phone_no').distinct()
    # emp_mob_no = [ x['cu_phone_no'] for x in emp_mob ]

    # print("user_mail_list",user_mail_list)

    '''
        MAIL Functionality
    '''
    user_mail_list = ['rupam@shyamfuture.com','bubai.das@shyamfuture.com']
    print("email",user_mail_list)
    if user_mail_list:
        mail_data = {
        'name':None
        }
        print('mail_data',mail_data)
        mail_class = GlobleMailSend('ATP-PM-EW', user_mail_list)
        mail_thread = Thread(target = mail_class.mailsend, args = (mail_data,None))
        mail_thread.start()
        #mail_list=[]
        # while len(user_mail_list)>0:
        #     dummy_mail_list = user_mail_list[0:5]
        #     user_mail_list = list(set(user_mail_list) - set(dummy_mail_list ))
        #     print("user_mail_list",user_mail_list)
        #     mail_class = GlobleMailSend('ATP-PM', dummy_mail_list)
        #     mail_thread = Thread(target = mail_class.mailsend, args = (mail_data,None))
        #     mail_thread.start()
    
    '''
        SMS Functionality
    '''
    # if emp_mob_no:
    #     message_data = {
    #         'name':None
    #     }
    #     sms_class = GlobleSmsSendTxtLocal('ATTPR',emp_mob_no)
    #     sms_thread = Thread(target = sms_class.sendSMS, args = (message_data,'sms'))
    #     sms_thread.start()

    return True

'''
    @ Added by Rupam Hazra
'''
def my_attendence_pending_mail_on_every_friday_in_a_week():

    '''
        ATTENDENCE REMINDER FOR ALL HRMS & ATTENDENCE USER 
    '''
    print('Current Time :: ',datetime.now())
    print('===============================')
    # current_date = datetime.now().date()
    # current_month = current_date.month
    # print("current_date",current_date)

    # user_list = TMasterModuleRoleUser.objects.filter(
    #                 Q(mmr_type=3),Q(mmr_is_deleted=False),
    #                 Q(mmr_module__cm_name='ATTENDANCE & HRMS')).\
    #                 values_list('mmr_user',flat=True).distinct()

    #email extraction            
    # user_mail_list_primary=TMasterModuleRoleUser.objects.filter(
    #                 Q(mmr_type=3),Q(mmr_is_deleted=False),
    #                 Q(mmr_module__cm_name='ATTENDANCE & HRMS'),
    #                 (Q(mmr_user__email__isnull=False) & ~Q(mmr_user__email=""))).\
    #                 values('mmr_user__email').distinct()

    user_mail_official = TCoreUserDetail.objects.filter(
        ~Q(attendance_type__in = ('PMS','CRM','Manual')),
        cu_is_deleted=False,
        cu_user__is_active = True,
        cu_alt_email_id__isnull = False
        ).exclude(cu_alt_email_id__exact='').values('cu_alt_email_id')

    #print("user_mail_official",user_mail_official.query)
    # print("user_mail_official",user_mail_official)
    #umlp = [x['mmr_user__email'] for x in user_mail_list_primary]
    uma = [x['cu_alt_email_id'] for x in user_mail_official]
    user_mail_list = list(set(uma))

    #user_mail_list = list(set(umlp + uma))
    #user_mail_list = list(set(uma))
    #print("user_mail_list",user_mail_list)
    
    # emp_mob = TCoreUserDetail.objects.filter(cu_user__in=list(user_list),cu_phone_no__isnull=False,cu_is_deleted=False).\
    #     values('cu_phone_no').distinct()
    # emp_mob_no = [ x['cu_phone_no'] for x in emp_mob ]

    

    #print("user_mail_list",user_mail_list)
    #print("user_mail_list",len(user_mail_list))

    '''
        MAIL Functionality
    '''
    #user_mail_list = ['rupam@shyamfuture.com']
    
    if user_mail_list:
        mail_data = {
        'name':None
        }
        print('mail_data',mail_data)
        mail_class = send_mail_list('ATP-PM-EW', user_mail_list,mail_data)
        #mail_thread = Thread(target = mail_class.mailsend, args = (mail_data,None))
        #mail_thread.start()

    # '''
    #     SMS Functionality
    # '''
    # if emp_mob_no:
    #     message_data = {
    #         'name':None
    #     }
    #     sms_class = GlobleSmsSendTxtLocal('ATTPR',emp_mob_no)
    #     sms_thread = Thread(target = sms_class.sendSMS, args = (message_data,'sms'))
    #     sms_thread.start()

    return True

'''
    PMS CRON JOB START

    Author : Rupam Hazra
    Date : 04.05.2020
    Reason : Update closing stock end of everyday.  
'''

def update_closing_stock_end_of_everyday():
    from pms.models import PmsExecutionStock
    current_date_time = datetime.now()
    print('Date ::', current_date_time)
    print('current_date_time',current_date_time)
    queryset_stocks = PmsExecutionStock.objects.filter(
        stock_date__date = current_date_time.date(),
        is_deleted = False
    )
    print('queryset_stocks',queryset_stocks)
    for each_stock in queryset_stocks:
        o_stock = each_stock.opening_stock if each_stock.opening_stock else 0
        r_stock = each_stock.recieved_stock if each_stock.recieved_stock else 0
        i_stock = each_stock.issued_stock if each_stock.issued_stock else 0
        c_stock =  (o_stock + r_stock) - i_stock
        print('queryset_stocks',c_stock)
        PmsExecutionStock.objects.filter(pk=each_stock.id).update(
            closing_stock = c_stock,
            updated_by_id = self.request.user.id
        )
    
    print('update result',queryset_stocks.values())
    return True

#### PMS Attendance Absent Day insert CRON ###

def insert_absent_data_for_all_users_on_attendance_end_of_everyday():
    
    from master.models import TMasterModuleRoleUser
    from users.models import TCoreUserDetail
    from pms.models import PmsAttendance
    from django.db.models import Q
    from django.db import transaction, IntegrityError

    filter = dict()
    filter['attendance_type'] = 'PMS'

    current_date = datetime.now()
    print('date',current_date)
    date_time_day = current_date.date()
    #date_time_day = '2020-09-20'
    
    print("==================================================================================")

    month_master = AttendenceMonthMaster.objects.filter(
            month_start__date__lte=date_time_day,
            month_end__date__gte=date_time_day,
            is_deleted=False
            ).first()

    termination_start_day = month_master.month_start
    termination_end_day = get_last_day_of_month(month_master.month_end)

    users_list_in_pms = TCoreUserDetail.objects.filter(
            ~Q(
                cu_user__in=(PmsAttendance.objects.filter(date__date=date_time_day,is_deleted=False).values_list('employee',flat=True))
                ),
            (
                Q(
                    Q(termination_date__isnull=False) & Q(
                        Q(
                            Q(termination_date__gte=termination_start_day)&Q(termination_date__lte=termination_end_day)
                        )|
                        Q(termination_date__date__gte=date_time_day)
                    )
                )
                |Q(Q(termination_date__isnull=True),cu_is_deleted=False)
            ),
            (Q(joining_date__date__lte=date_time_day)),
            **filter
        )
    print('users_list_in_pms',users_list_in_pms,len(users_list_in_pms))
    

    time = str(date_time_day) +'T'+'10:00:00'
    login_time = datetime.strptime(str(date_time_day) +'T'+'10:00:00',"%Y-%m-%dT%H:%M:%S")
    print('login_time',login_time)
    logout_time = datetime.strptime(str(date_time_day) +'T'+'18:00:00',"%Y-%m-%dT%H:%M:%S")
    print('logout_time',logout_time)
    dev_time = (logout_time - login_time)
    print('dev_time',dev_time)
    time_deviation = (datetime.min + dev_time).time().strftime('%H:%M:%S')
    print('time_deviation',time_deviation)

    try:
        with transaction.atomic():
            for each_user in users_list_in_pms:
                #print('each_user.cu_user',each_user,type(each_user))
                att_filter = {'type':1,'employee':each_user.cu_user,'date':time, 'created_by':each_user.cu_user,'owned_by':each_user.cu_user}
                log_filter = {'time':login_time,'login_logout_check':'Login', 'created_by':each_user.cu_user,'owned_by':each_user.cu_user}
                req_filter = {'from_time':login_time,'to_time':logout_time,'deviation_time':time_deviation,'duration':round((dev_time.seconds)/60)}

                attandance_data = PmsAttendance.objects.filter(date__date=date_time_day,employee=each_user.cu_user,is_deleted=False)
                if not attandance_data:
                    
                    project_user_mapping = PmsProjectUserMapping.objects.filter(user=each_user.cu_user, status=True).order_by('-id').values('project')
                    print("project_user_mapping",project_user_mapping)
                    if project_user_mapping:
                        project = project_user_mapping[0]['project']
                        print('project',project,type(project))
                        att_filter['user_project_id'] = project
                        #request.data['user_project_id'] = project
                        #print('project',project)
                        project_site = PmsProjects.objects.filter(pk=project).values('id','site_location','site_location__geo_fencing_area')
                        #print('project_site_details',project_site)
                        if project_site:
                            for e_project_site in project_site:
                                geofence = e_project_site['site_location__geo_fencing_area']
                                #print('geofence',geofence)
                                multi_lat_long=PmsSiteProjectSiteManagementMultipleLongLat.objects.filter(
                                project_site_id=e_project_site['site_location']).values()
                                #print('multi_lat_long',multi_lat_long)
                        else:
                            multi_lat_long = list()
                            pass
                    else:
                        multi_lat_long = list()
                        geofence = ''
                        att_filter['user_project_id'] = None
                    
                    ### Advance Leave Check ###
                    adv_leave_type = None
                    leave = EmployeeAdvanceLeaves.objects.filter(
                        Q(start_date__date__lte=date_time_day)&Q(end_date__date__gte=date_time_day)&Q(employee_id=each_user.cu_user)&  #changes by abhisek 21/11/19
                        (Q(approved_status='pending')|Q(approved_status='approved'))).values('leave_type','reason')
                    
                    print('leave',leave)
                    ### End ###

                    ### Special Leave Check ###
                    spl_leave_type = None   
                    spacial_leave = EmployeeSpecialLeaves.objects.filter(Q(start_date__date__lte=date_time_day)&Q(end_date__date__gte=date_time_day)&Q(employee_id=each_user.cu_user)&  
                        (Q(approved_status='pending')|Q(approved_status='approved'))).values('leave_type','reason')

                    print('spacial_leave',spacial_leave)
                    ### End ###

                    if spacial_leave:
                        spl_leave_type = spacial_leave[0]['leave_type']
                        att_filter['day_remarks'] = spacial_leave[0]['leave_type']
                        print('spacial leave found...')

                    elif leave:
                        adv_leave_type = leave[0]['leave_type']
                        # print("leave_type",leave[0]['leave_type'])
                        att_filter['day_remarks']= 'Leave'
                        
                    else:
                        att_filter['day_remarks']="Not Present"

                    if att_filter:
                        abs_att = pms_att_create(att_filter)
                        print('abs_att',abs_att,type(abs_att))
                        if abs_att:
                            log_filter['attandance'] = abs_att
                            login_log_details = pms_log_create(log_filter)
                            print('login_log_details',login_log_details)
                            if login_log_details:
                                log_filter['time'] = logout_time
                                log_filter['login_logout_check'] = 'Logout'
                                log_filter['login_id'] = login_log_details.id
                                logout_log_details = pms_log_create(log_filter)
                                print('logout_log_details',logout_log_details)
                                if logout_log_details:
                                    req_filter['attandance']= abs_att

                                    if spl_leave_type:
                                        req_filter['deviation_type']='FD'
                                        req_filter['approved_status'] = 2
                                        req_filter['leave_type'] = spl_leave_type
                                        req_filter['is_requested'] = True
                                        req_filter['justification'] = spacial_leave[0]['reason']
                                        req_filter['request_date'] = datetime.now()
                                    
                                    elif adv_leave_type:
                                        req_filter['deviation_type']='FD'
                                        req_filter['approved_status'] = 2
                                        req_filter['leave_type'] = adv_leave_type
                                        req_filter['is_requested'] = True
                                        req_filter['justification'] = leave[0]['reason']
                                        req_filter['request_date'] = datetime.now()

                                    if req_filter:
                                        abs_req = pms_request_create(req_filter,each_user)
                                        print('abs_req',abs_req)
                                        print('----------------------------------------------------------------')
                                           
        return True
    
    except Exception as e:
        raise e                           

    
def pms_att_create(filter: dict):
    from pms.models import PmsAttendance
    attendance,_ = PmsAttendance.objects.get_or_create(**filter)
    return attendance

def pms_log_create(filter: dict):
    from pms.models import PmsAttandanceLog
    log,_ = PmsAttandanceLog.objects.get_or_create(**filter)
    return log

def pms_request_create(filter: dict,user):
    from pms.models import PmsAttandanceDeviation
    logdin_user_id = 1  #attendance_date
    #print('logdin_user_id',logdin_user_id)
    if user.cu_is_deleted == True and user.cu_user.is_active == False:
        filter['deviation_type'] = 'FD'
        filter['leave_type'] = 'AB'
        filter['is_requested'] = True
        filter['request_date'] = datetime.now()
        
        filter['justification'] = 'Auto Absent'
        filter['remarks'] = 'Auto Absent'
        filter['justified_by_id'] = logdin_user_id
        filter['justified_at'] = datetime.now()

        filter['approved_status'] = '2' # Approved
        filter['approved_by_id'] = logdin_user_id
        filter['approved_at'] = datetime.now()

    request,_ = PmsAttandanceDeviation.objects.get_or_create(**filter)
    return request

#### END PMS Attendance Absent Day insert CRON ###


## Start | Rupam Hazra | Pending Notification Cron | Date : 02.09.2020 ##


def send_reminder_notification_for_pending_approval():
    import requests
    response = requests.get(settings.SERVER_URL+'pms/tour_and_travel/notification_mail/pending/')
    return response.status_code        

## End | Rupam Hazra | Pending Notification Cron | Date : 02.09.2020 ##

'''
    PMS CRON JOB END
'''

# auto approval
def tour_and_travel_auto_approval_job():
    import requests
    response = requests.get(settings.SERVER_URL+'pms/tour_and_travel/auto_approval/')
    return response.status_code
'''
    Attendance automate system | Rupam Hazra | Live Upload : 03.09.20202
'''
def attendance_automate():
    import requests
    response = requests.get(settings.SERVER_URL+'v2/attendance_automate/')
    return response.status_code


'''
    E-Task Cron Job
'''
    #### Insert Profile job according to recurrance period

def is_holiday(user_id,date):
    state = TCoreUserDetail.objects.filter(cu_user_id=user_id)
    print('state',state)
    if state:
        holiday = HolidayStateMapping.objects.filter(state_id = state[0].job_location_state,holiday__holiday_date=date).values_list('holiday__holiday_name')
        print('holidays',holiday)
        if holiday:
            return True
        else:
            return False
    else:
        return False

def etask_profile_job_recurrence():
    # etask_url = settings.SERVER_API_URL+'etask_task_profile_job_add_cron/'
    # print('etask_url',etask_url)
    # response = requests.get(etask_url,verify=False)
    # data = response.json() 
    #return response.status_code

    print('date::::', datetime.now())
    print("==================================================================================================")

    #task_end_date = request.data.get('date',datetime.now().date())
    task_end_date = datetime.now().date()
    #task_end_date = datetime.strptime('2020-11-04','%Y-%m-%d').date()
    ###print('requrest',request.data)
    profile_jobs_queryset = EtaskTask.objects.filter(task_type__in=[2,4],end_date__date=task_end_date)
    #profile_jobs_queryset = EtaskTask.objects.filter(task_type__in=['2','4'],end_date__date=task_end_date,assign_to_id='3331')
    print('profile jobs',profile_jobs_queryset)
   
    if profile_jobs_queryset:
        for e_profile_jobs_queryset in profile_jobs_queryset:
           
            user_name = userdetails(int(e_profile_jobs_queryset.assign_to_id))

            # Recurrance Frequence Set
            recurrance_frequency_days = 1 # Daily

            if e_profile_jobs_queryset.recurrance_frequency == 2: # Weekely
                recurrance_frequency_days = 7

            if e_profile_jobs_queryset.recurrance_frequency == 3: # Fortnightly
                recurrance_frequency_days = 15
            
            if e_profile_jobs_queryset.recurrance_frequency == 4: # Monthly
                recurrance_frequency_days = 30

            if e_profile_jobs_queryset.recurrance_frequency == 5: # Quarterly
                recurrance_frequency_days = 90
            
            if e_profile_jobs_queryset.recurrance_frequency == 6: # Half-Yearly
                recurrance_frequency_days = 180
            
            if e_profile_jobs_queryset.recurrance_frequency == 7: # Annualy
                recurrance_frequency_days = 365


            #########################################################################

            task_reference_id = e_profile_jobs_queryset.id
            start_date = e_profile_jobs_queryset.start_date
            end_date = e_profile_jobs_queryset.end_date

            reference_start_date = e_profile_jobs_queryset.start_date + timedelta(
                days=recurrance_frequency_days)
            reference_end_date = e_profile_jobs_queryset.end_date + timedelta(days=recurrance_frequency_days)

            print('reference_start_date', reference_start_date, 'reference_end_date', reference_end_date)
            if e_profile_jobs_queryset.task_reference_id != 0 and e_profile_jobs_queryset.reference_start_date and e_profile_jobs_queryset.reference_end_date:

                print('e_profile_jobs_queryset.task_reference_id',
                      type(e_profile_jobs_queryset.task_reference_id),
                      e_profile_jobs_queryset.task_reference_id)

                # Task master id
                task_reference_id = EtaskTask.objects.get(id=str(e_profile_jobs_queryset.task_reference_id)).id

                # set start date and end date for monthly | Quarterly | Half-Yearly | Annualy
                if e_profile_jobs_queryset.recurrance_frequency == 4 or e_profile_jobs_queryset.recurrance_frequency == 5 or e_profile_jobs_queryset.recurrance_frequency == 6 or e_profile_jobs_queryset.recurrance_frequency == 7:
                    start_date = e_profile_jobs_queryset.reference_start_date
                    end_date = e_profile_jobs_queryset.reference_end_date

                # reference start dates insert
                reference_start_date = e_profile_jobs_queryset.reference_start_date + timedelta(
                    days=recurrance_frequency_days)
                reference_end_date = e_profile_jobs_queryset.reference_end_date + timedelta(
                    days=recurrance_frequency_days)

            #########################################################################

            print('task_reference_id', task_reference_id)
            print('reference_start_date', reference_start_date)
            print('reference_end_date', reference_end_date)

            start_date = start_date + timedelta(days=recurrance_frequency_days)
            end_date = end_date + timedelta(days=recurrance_frequency_days)

            # Check holiday
            is_holiday_check_for_start_date = is_holiday(e_profile_jobs_queryset.assign_to_id,
                                                         start_date.date())
            is_holiday_check_for_end_date = is_holiday(e_profile_jobs_queryset.assign_to_id, end_date.date())

            # Check sunday
            week_day = start_date.date().strftime('%A')

            print('is_holiday_check_for_start_date', is_holiday_check_for_start_date)
            print('is_holiday_check_for_end_date', is_holiday_check_for_end_date)
            print('week_day', week_day)

            if is_holiday_check_for_start_date:
                start_date = start_date + timedelta(days=1)
                is_holiday(e_profile_jobs_queryset.assign_to_id, start_date.date())

            if is_holiday_check_for_end_date:
                end_date = end_date + timedelta(days=1)
                is_holiday(e_profile_jobs_queryset.assign_to_id, end_date.date())

            if week_day == 'Sunday':
                start_date = start_date + timedelta(days=1)
                end_date = end_date + timedelta(days=1)
                is_holiday(e_profile_jobs_queryset.assign_to_id, start_date.date())
                is_holiday(e_profile_jobs_queryset.assign_to_id, end_date.date())

            print('start_date',start_date)
            print('end_date', end_date)
                
            # Task create
            task = EtaskTask.objects.get(pk=e_profile_jobs_queryset.id)
            task.pk = None
            task.task_code_id = None
            task.start_date =  start_date
            task.end_date = end_date
            task.extended_date = None
            task.requested_end_date = None
            task.requested_comment = None
            task.requested_by= None
            task.is_closure = False
            task.is_reject = False
            task.is_transferred = False
            task.transferred_from = None
            task.date_of_transfer = None
            task.completed_date = None
            task.completed_by = None
            task.closed_date = None
            task.shifted_date= None
            task.extend_with_delay =False
            task.sub_assign_to_user = None
            task.task_reference_id = task_reference_id
            task.reference_start_date = reference_start_date
            task.reference_end_date = reference_end_date
            task.task_status = 1
            task.save()
            task.task_code_id = "TSK"+str(task.id)
            task.save()
            print('Task Save Done')

            # Add Etask user cc
            etask_usercc = EtaskUserCC.objects.filter(task_id=e_profile_jobs_queryset.id)
            if etask_usercc:
                for e_etask_usercc in etask_usercc:
                    etask_usercc_queryset = EtaskUserCC.objects.get(task_id=e_profile_jobs_queryset.id,pk=e_etask_usercc.id)
                    etask_usercc_queryset.pk = None
                    etask_usercc_queryset.task = task
                    etask_usercc_queryset.save()
            cc_name_list = [u_cc.user.get_full_name() for u_cc in etask_usercc]
            # Add Reporting dates
            reporting_dates_queryset = ETaskReportingDates.objects.filter(task=e_profile_jobs_queryset.id)
            print('reporting_dates_queryset',reporting_dates_queryset)
            reporting_obj_list = list()
            if reporting_dates_queryset:
                
                reporting_date_str = """"""
                r_time = ''
                count_id = 0
                ics_data = """BEGIN:VCALENDAR
VERSION:2.0
CALSCALE:GREGORIAN\n"""

                for e_reporting_dates_queryset in reporting_dates_queryset:

                    ###print('e_reporting_dates_queryset',e_reporting_dates_queryset)
                    e_reporting_dates = ETaskReportingDates.objects.get(task=e_profile_jobs_queryset.id,id=e_reporting_dates_queryset.id)
                    print('e_reporting_dates',e_reporting_dates)
                    e_reporting_dates.pk = None
                    e_reporting_dates.task = task.id
                    if e_reporting_dates.reporting_date:
                        e_reporting_dates.reporting_date = e_reporting_dates.reporting_date + timedelta(days=recurrance_frequency_days)
                    print('demo 1')
                    if e_reporting_dates.actual_reporting_date:
                        e_reporting_dates.actual_reporting_date = e_reporting_dates.actual_reporting_date + timedelta(days=recurrance_frequency_days)
                    print('demo 2')
                    e_reporting_dates.save()
                    reporting_obj_list.append(e_reporting_dates)
                    print('demo 3')
                    # Add Reporting action log
                    reporting_action_log = ETaskReportingActionLog.objects.filter(
                        task_id=e_profile_jobs_queryset.id,reporting_date_id=e_reporting_dates_queryset.id)
                    print('reporting_action_log',reporting_action_log)
                    if reporting_action_log:
                        #reporting_dates_action_log_queryset = ETaskReportingActionLog.objects.get(task_id=e_profile_jobs_queryset.id,reporting_date_id=e_reporting_dates_queryset.id)
                        reporting_dates_action_log_queryset = ETaskReportingActionLog.objects.filter(task_id=e_profile_jobs_queryset.id,reporting_date_id=e_reporting_dates_queryset.id)
                        if reporting_dates_action_log_queryset: 
                            reporting_dates_action_log_queryset = reporting_dates_action_log_queryset[0]
                        print('reporting_dates_action_log_queryset',reporting_dates_action_log_queryset.updated_date)
                        reporting_dates_action_log_queryset.pk = None
                        reporting_dates_action_log_queryset.task = task
                        reporting_dates_action_log_queryset.reporting_date = e_reporting_dates
                        reporting_dates_action_log_queryset.updated_date = reporting_dates_action_log_queryset.updated_date + timedelta(days=recurrance_frequency_days)
                        print('reporting_dates_action_log_queryset.updated_date',reporting_dates_action_log_queryset.updated_date)
                        reporting_dates_action_log_queryset.save()

                    print('demo 4')
                    count_id += 1
                    reporting_date_str += str(count_id)+'. '+e_reporting_dates.reporting_date.strftime("%m/%d/%Y, %I:%M:%S %p")+" "
                    r_time = e_reporting_dates.reporting_date.strftime("%Y%m%dT%H%M%S")
                    
                    

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
END:VEVENT\n""".replace("{r_time}",r_time).replace("{rep_sub}",task.task_subject)

                ics_data += "END:VCALENDAR"

                # Send mail to Assign to User

                user_email = User.objects.get(id=task.assign_to_id).cu_user.cu_alt_email_id
                print("user_email",user_email)
                mail_reporting_date_list = [r_date.reporting_date.strftime("%d/%m/%Y, %I:%M:%S %p") for r_date in reporting_obj_list]
                
                if user_email:
                    mail_data = {
                                "recipient_name" : user_name,        ## modified by manas Paul 21jan20
                                "task_subject": task.task_subject,
                                "reporting_date": mail_reporting_date_list,
                                "assign_to_name": task.assign_to.get_full_name(),
                                "created_by_name": task.created_by.get_full_name(),
                                "created_date_time": task.created_at,
                                "cc_to":','.join(cc_name_list),
                                "task_priority": task.get_task_priority_display(),
                                "start_date": task.start_date.date(),
                                "end_date": task.end_date.date()
                            }
                    mail_class = GlobleMailSend('ETRDC', [user_email])
                    ##print('mail_class',mail_class)
                    mail_thread = Thread(target = mail_class.mailsend, args = (mail_data,ics_data))
                    ##print('mail_thread-->',mail_thread)
                    mail_thread.start()
                print('Creating and mail appointment')  
                # Creating and mail appointment
                create_appointment(reporting_dates=reporting_obj_list,mail_send=False)
                print('End Code ...........................')
            print('End Complete Code ...........................')


#hrms probation automation employee reminder mail
def three_month_probation_reminder():
    response = requests.get(settings.SERVER_URL+'hrms/three_month_probation_review_reminder_job/')
    return response.status_code

#hrms five month probation automation employee reminder mail
def five_month_probation_reminder():
    response = requests.get(settings.SERVER_URL+'hrms/five_month_probation_review_reminder_job/')
    return response.status_code