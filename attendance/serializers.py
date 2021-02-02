from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from attendance.models import *
from django.contrib.auth.models import *
from django.db import transaction, IntegrityError
from drf_extra_fields.fields import Base64ImageField
import os
from holidays.models import * 
# import datetime
from django.db.models import Q
from datetime import datetime,timedelta
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from users.models import TCoreUserDetail
from smssend.views import *
from threading import Thread
from attendance.views import *
from django.db.models import Sum
from custom_exception_message import *
from django.db.models import Q
import calendar
from django.db.models import When, Case, Value, CharField, IntegerField, F, Q
from datetime import date,time
from hrms.models import *
from global_function import userdetails,department,designation,send_mail
from master.models import *
from core.models import *
from attendance import logger

from mailsend.views import *
from smssend.views import *
from threading import Thread
from rest_framework.response import Response
from django.db.models import Sum
from employee_leave_calculation import *
#GLOBAL GRACE FUNCTION

# def GraceCalculation()

#:::::::::::::::::::::: DEVICE MASTER:::::::::::::::::::::::::::#
class DeviceMasterAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = DeviceMaster
        fields = ('id', 'device_no', 'device_name', 'frs_check_point','is_exit', 'created_by', 'owned_by')


class DeviceMasterEditSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = DeviceMaster
        fields = ('id', 'device_no', 'device_name', 'is_exit', 'updated_by')


class DeviceMasterDeleteSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = DeviceMaster
        fields = '__all__'
    def update(self, instance, validated_data):
        instance.is_deleted=True
        instance.updated_by = validated_data.get('updated_by')
        instance.save()
        return instance


#:::::::::::::::::::::: ATTENDENCE MONTH MASTER:::::::::::::::::::::::::::#
class AttendenceMonthMasterAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = AttendenceMonthMaster
        fields = ('id', 'year_start_date', 'year_end_date', 'month', 'month_start', 'month_end',
        'lock_date','pending_action_mail','grace_available', 'created_by', 'owned_by','fortnight_date')


class AttendenceMonthMasterEditSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = AttendenceMonthMaster
        fields = ('id', 'year_start_date', 'year_end_date', 'month', 'month_start', 'month_end', 'grace_available', 
        'lock_date','pending_action_mail','updated_by','fortnight_date')


class AttendenceMonthMasterDeleteSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = AttendenceMonthMaster
        fields = '__all__'
    def update(self, instance, validated_data):
        instance.is_deleted=True
        instance.updated_by = validated_data.get('updated_by')
        instance.save()
        return instance


class AttendencePerDayDocumentAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = AttandancePerDayDocuments
        fields = '__all__'


class AttendenceApprovalRequestEditSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())

    # attendence_approvals=serializers.ListField(required=False)

    class Meta:
        model = AttendanceApprovalRequest
        fields = ('__all__')
        # extra_fields=('attendence_approvals')

    def daterange(self,date1, date2):
        for n in range(int ((date2 - date1).days)+1):
            yield date1 + timedelta(n)

    def validate_3days_CL(self, month_master):
        '''
        Name :: Rajesh Samui
        Reason :: Validation of 3 days CL in a AttendenceMonthMaster 
        ( Can't take more than 3 days CL in a AttendenceMonthMaster )and Advance Casual Leave will 
        also be counted before applying date.
        Date :: 11 Mar, 2020
        '''
        
        normal_cl_month = AttendanceApprovalRequest.objects.filter(Q(leave_type='CL')&
                                                                    Q(is_requested=True)&
                                                                    Q(attendance_date__gte=month_master['month_start'].date())&
                                                                    Q(attendance_date__lt=self.instance.attendance_date)
                                                                    )
        # Creating a set of CL dates
        date_cl_set = set()
        for normal_cl_date in normal_cl_month: date_cl_set.add(normal_cl_date.attendance_date)
        
        advance_cl = EmployeeAdvanceLeaves.objects.filter(leave_type='CL')
        print('self.instance.attendance_date:',str(self.instance.attendance_date))
        for date in self.daterange(self.instance.attendance_date+timedelta(days=1), month_master['month_end'].date()):
            print('date',str(date))
            advance_cl_exist = advance_cl.filter(Q(start_date__date__lte=date)&
                                                        Q(end_date__date__gte=date)).count()
            if advance_cl_exist:
                date_cl_set.add(date)
        print('date_cl_set:', date_cl_set)
        if len(date_cl_set) >= 3:
            custom_exception_message(self,None,"You can't apply 3 CL for same month!")

    def update(self,instance, validated_data):
        # print("instance",instance)
        updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
        
        try:
            updated_by = validated_data.get('updated_by')
            date =self.context['request'].query_params.get('date', None)
            #print('date',type(date))
            #################################################################################
            #if you find error in datetime please remove only datetime from "date_object"   #
            #################################################################################
            date_object = datetime.datetime.strptime(date, '%Y-%m-%d').date()
            #print('date_object',type(date_object))
            employee_id=self.context['request'].query_params.get('employee_id', None)
            total_grace={}
            data_dict = {}
            with transaction.atomic():
                request_type=validated_data.get('request_type') if validated_data.get('request_type') else ""
                present=AttendanceApprovalRequest.objects.filter(id=instance.id,
                    attendance__is_present=True)
                total_month_grace=AttendenceMonthMaster.objects.filter(month_start__date__lte=date_object,
                                                    month_end__date__gte=date_object,is_deleted=False).values('grace_available',
                                                                                            'year_start_date',
                                                                                            'year_end_date',
                                                                                            'month',
                                                                                            'month_start',
                                                                                            'month_end'
                                                                                            )
                #############  CL Validation ##############
                # 3 days CL validation
                # if validated_data.get('leave_type') == 'CL':
                #     self.validate_3days_CL(total_month_grace.first())
                ###########################################


                #REQUEST ONLY IF PRESENT AND HAVE DIVIATION
                if present:
                    availed_grace=AttendanceApprovalRequest.objects.filter(Q(attendance__employee=employee_id) &
                                                            Q(duration_start__gte=total_month_grace[0]['month_start']) &
                                                            Q(duration_start__lte=total_month_grace[0]['month_end']) &
                                                            Q(is_requested=True) &
                                                            Q(is_deleted=False)&
                                                            (Q(request_type='GR')|Q(checkin_benchmark=True))
                                                            ).aggregate(Sum('duration'))['duration__sum']
                    
                    #print("availed_grace first 1 ",availed_grace)
                    
                    #*****************Request for Grace************************************************************************************
                    #print("total_month_grace",total_month_grace)
                    if request_type == 'GR':
                        worst_late_beanchmark=TCoreUserDetail.objects.get(cu_user=employee_id).worst_late
                        print("worst_late_beanchmark",worst_late_beanchmark)

                        duration_start_end=AttendanceApprovalRequest.objects.get(id=instance.id)
                        print("duration_start_end",duration_start_end)
                        core_user_detail=TCoreUserDetail.objects.filter(cu_user=employee_id,cu_is_deleted=False).values('joining_date')
                        print('core_user_detail',core_user_detail)
                        if core_user_detail:
                            if core_user_detail[0]['joining_date']>total_month_grace[0]['year_start_date']:
                                joining_grace=JoiningApprovedLeave.objects.filter(employee=employee_id,is_deleted=False).values('cl',
                                                                                                                                'el',
                                                                                                                                'sl',
                                                                                                                                'year',
                                                                                                                                'month',
                                                                                                                                'first_grace' )

                                if total_month_grace[0]['month']==joining_grace[0]['month']:    #for joining month only
                                    total_grace['total_month_grace']=joining_grace[0]['first_grace']
                                    total_grace['month_start']=core_user_detail[0]['joining_date']

                                    duration_length=AttendanceApprovalRequest.objects.get(id=instance.id,checkin_benchmark=False,is_requested=False)
                                    # if duration_length.duration < 240:
                                    if duration_length.duration <= 150:
                                    # total_grace['grace_balance']=total_grace['total_month_grace'] - availed_grace
                                        if availed_grace is None:
                                            availed_grace=0.0
                                        if (total_grace['total_month_grace']-(float(availed_grace)+float(duration_length.duration))) >= 0.0 :
                                        
                                            justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                update(
                                                request_type=request_type,
                                                is_requested=True,
                                                approved_status='pending',
                                                request_date=datetime.date.today(),
                                                justified_at=datetime.date.today(),
                                                justification=validated_data.get('justification'),
                                                justified_by=updated_by)

                                            return validated_data
                                        else:
                                            # raise serializers.ValidationError("Grace limit exceeds")
                                            custom_exception_message(self,None,"Grace limit exceeds")
                                    elif duration_length.duration >150 and duration_length.duration <=240:
                                        # raise serializers.ValidationError("Please apply half day Your diviation exceeds 2.5 Hours")
                                        custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                    elif duration_length.duration > 240 :
                                        if (duration_start_end.duration_start.time() and duration_start_end.duration_end.time()) < worst_late_beanchmark:
                                            custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                        elif duration_start_end.duration_start.time() < worst_late_beanchmark and duration_start_end.duration_end.time() > worst_late_beanchmark:
                                            custom_exception_message(self,None,"Please apply full day Your diviation exceeds 4 Hours")
                                        elif (duration_start_end.duration_start.time() and duration_start_end.duration_end.time()) > worst_late_beanchmark:
                                            custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                        
                                else:
                                    total_grace['total_month_grace']=float(total_month_grace[0]['grace_available']) if float(total_month_grace[0]['grace_available']) else 0.0
                                    duration_length=AttendanceApprovalRequest.objects.get(id=instance.id,checkin_benchmark=False,is_requested=False)
                                    #print('availed_grace12333',availed_grace)
                                    if duration_length.duration <= 150:
                                    # total_grace['grace_balance']=total_grace['total_month_grace'] - availed_grace
                                        if availed_grace is None:
                                            availed_grace=0.0
                                        if (total_grace['total_month_grace']-(float(availed_grace)+float(duration_length.duration))) >= 0.0 :
                                        
                                            justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                update(
                                                request_type=request_type,
                                                is_requested=True,
                                                approved_status='pending',
                                                request_date=datetime.date.today(),
                                                justified_at=datetime.date.today(),
                                                justification=validated_data.get('justification'),
                                                justified_by=updated_by)

                                            return validated_data
                                        else:
                                            # raise serializers.ValidationError("Grace limit exceeds")
                                            custom_exception_message(self,None,"Grace limit exceeds")
                                    elif duration_length.duration >150 and duration_length.duration <=240:
                                        # raise serializers.ValidationError("Please apply half day Your diviation exceeds 2.5 Hours")
                                        custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                    elif duration_length.duration > 240 :
                                        if (duration_start_end.duration_start.time() and duration_start_end.duration_end.time()) < worst_late_beanchmark:
                                            custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                        elif duration_start_end.duration_start.time() < worst_late_beanchmark and duration_start_end.duration_end.time() > worst_late_beanchmark:
                                            custom_exception_message(self,None,"Please apply full day Your diviation exceeds 4 Hours")
                                        elif (duration_start_end.duration_start.time() and duration_start_end.duration_end.time()) > worst_late_beanchmark:
                                            custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                            else:
                                total_grace['total_month_grace']=float(total_month_grace[0]['grace_available']) if float(total_month_grace[0]['grace_available']) else 0.0
                                duration_length=AttendanceApprovalRequest.objects.get(id=instance.id,checkin_benchmark=False,is_requested=False)
                                if duration_length.duration <= 150:
                                # total_grace['grace_balance']=total_grace['total_month_grace'] - availed_grace
                                    if availed_grace is None:
                                        availed_grace=0.0
                                    # print('total_grace',total_grace['total_month_grace'],availed_grace)
                                    if (total_grace['total_month_grace']-(float(availed_grace)+float(duration_length.duration))) > 0.0 :
                                    
                                        justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                            update(
                                            request_type=request_type,
                                            is_requested=True,
                                            approved_status='pending',
                                            request_date=datetime.date.today(),
                                            justified_at=datetime.date.today(),
                                            justification=validated_data.get('justification'),
                                            justified_by=updated_by)

                                        return validated_data
                                    else:
                                        # raise serializers.ValidationError("Grace limit exceeds")
                                        custom_exception_message(self,None,"Grace limit exceeds")
                                elif duration_length.duration >150 and duration_length.duration <=240:
                                    # raise serializers.ValidationError("Please apply half day Your diviation exceeds 2.5 Hours")
                                    custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                elif duration_length.duration > 240 :
                                    if (duration_start_end.duration_start.time() and duration_start_end.duration_end.time()) < worst_late_beanchmark:
                                        custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                    elif duration_start_end.duration_start.time() < worst_late_beanchmark and duration_start_end.duration_end.time() > worst_late_beanchmark:
                                        custom_exception_message(self,None,"Please apply full day Your diviation exceeds 4 Hours")
                                    elif (duration_start_end.duration_start.time() and duration_start_end.duration_end.time()) > worst_late_beanchmark:
                                        custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                    #*****************present but user want to give HD or FD request*********************************************************
                    elif request_type == 'HD' or request_type == 'FD':
                        worst_late_beanchmark=TCoreUserDetail.objects.get(cu_user=employee_id).worst_late
                        duration_start_end=AttendanceApprovalRequest.objects.get(id=instance.id)
                        leave_type=validated_data.get('leave_type')
                        #*************check and calculation of leave counts available****************** 
                        total_paid_leave={}
                        advance_leave=EmployeeAdvanceLeaves.objects.filter(Q(employee=employee_id)&
                                                           Q(is_deleted=False)&
                                                           (Q(approved_status='pending')|Q(approved_status='approved'))
                                                          ).values('leave_type','start_date','end_date')
                        #print('advance_leave11111111111111111111',advance_leave) 
                        #time.sleep(30)    
                        advance_cl=0
                        advance_el=0
                        advance_ab=0
                        day=0
                        # if advance_leave:
                        #     for leave in advance_leave:
                        #         print('leave',leave)
                        #         start_date=leave['start_date'].date()
                        #         end_date=leave['end_date'].date()+timedelta(days=1)
                        #         print('start_date,end_date',start_date,end_date)
                        #         if date_object < end_date:
                        #             if date_object < start_date:
                        #                 day=(end_date-start_date).days 
                        #                 print('day',day)
                        #             elif date_object > start_date:
                        #                 day=(end_date-date_object).days
                        #                 print('day2',day)
                        #             else:
                        #                 day=(end_date-date_object).days

                        #         if leave['leave_type']=='CL':
                        #             advance_cl+=day
                        #         elif leave['leave_type']=='EL':
                        #             advance_el+=day
                        #         elif leave['leave_type']=='AB':
                        #             advance_ab+=day
                                                                                
                        year_end_date = total_month_grace[0]['year_end_date']
                        last_attendance = Attendance.objects.filter(employee=employee_id).values_list('date__date',flat=True).order_by('-date')[:1]
                        print("last_attendance",last_attendance)
                        last_attendance = last_attendance[0] if last_attendance else date_object
                        
                        if last_attendance<year_end_date.date():
                            print("last_attendancehfthtfrhfth",last_attendance)
                            adv_str_date = last_attendance+timedelta(days=1)
                            adv_end_date = year_end_date.date()+timedelta(days=1)
                            if advance_leave:
                                for leave in advance_leave:
                                    print('leave',leave)
                                    start_date=leave['start_date'].date()
                                    end_date=leave['end_date'].date()+timedelta(days=1)
                                    print('start_date,end_date',start_date,end_date)

                                    if adv_str_date<=start_date and adv_end_date>=start_date:
                                        if adv_end_date>=end_date:
                                            day = (end_date-start_date).days
                                        elif adv_end_date<=end_date:
                                            day = (adv_end_date-start_date).days
                                    elif adv_str_date>start_date:
                                        if adv_end_date<=end_date:
                                            day = (adv_end_date-adv_str_date).days
                                        elif adv_str_date<=end_date and adv_end_date>=end_date:
                                            day = (end_date-adv_str_date).days
                                        
                                    if leave['leave_type']=='CL':
                                        advance_cl+=day
                                    elif leave['leave_type']=='EL':
                                        advance_el+=day
                                    elif leave['leave_type']=='AB':
                                        advance_ab+=day
                                        
                        """ 
                        LEAVE CALCULATION:-
                        1)SINGLE LEAVE CALCULATION
                        2)MULTIPLE LEAVE FOR ONE DAY IS AUTO CONVERTED TO ONE TYPE OF LEAVE 
                        EDITED BY :- Abhishek.singh@shyamfuture.com
                        
                        """ 
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
                        #print("attendence_daily_data1111111111111111111",attendence_daily_data)
                        date_list = [x['duration_start__date'] for x in attendence_daily_data.iterator()]
                        #print("date_list",date_list)
                        #time.sleep(10)
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
                        #print("availed_master_wo_reject_fd",availed_master_wo_reject_fd)
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

                        availed_cl_data=float(availed_cl)+float(advance_cl)+float(availed_hd_cl/2)
                        availed_el_data=float(availed_el)+float(advance_el)+float(availed_hd_el/2)
                        availed_sl_data=float(availed_sl)+float(availed_hd_sl/2)
                        availed_ab_data=float(availed_ab)+float(advance_ab)+float(availed_hd_ab/2)

                        total_paid_leave['availed_cl']=float(availed_cl)+float(advance_cl)+float(availed_hd_cl/2)
                        total_paid_leave['availed_el']=float(availed_el)+float(advance_el)+float(availed_hd_el/2)
                        total_paid_leave['availed_sl']=float(availed_sl)+float(availed_hd_sl/2)
                        total_paid_leave['availed_ab']=float(availed_ab)+float(advance_ab)+float(availed_hd_ab/2)
                        total_paid_leave['total_availed_leave']=availed_cl_data + availed_el_data + availed_ab_data

                        core_user_detail=TCoreUserDetail.objects.filter(cu_user=employee_id,cu_is_deleted=False).values('joining_date',
                                                                                                                    'granted_cl',
                                                                                                                    'granted_sl',
                                                                                                                    'granted_el'
                                                                                                                    )
                        #print('core_user_detail',core_user_detail)
                        # print('availed_sl_datadgdfgfsdggdgdfgdfgdfgd111111111111',availed_sl_data,approved_leave[0]['sl'])
                        # time.sleep(10)
                        if core_user_detail:
                            if core_user_detail[0]['joining_date']>total_month_grace[0]['year_start_date']:
                                #print("joining")
                                approved_leave=JoiningApprovedLeave.objects.filter(employee=employee_id,is_deleted=False).values('cl',
                                                                                                                                'el',
                                                                                                                                'sl',
                                                                                                                                'year',
                                                                                                                                'month',
                                                                                                                                'first_grace' 
                                                                                                                     )
                                #print("approved_leave",approved_leave)
                                total_paid_leave['granted_cl']=approved_leave[0]['cl'] 
                                total_paid_leave['cl_balance']=float(approved_leave[0]['cl']) -float(availed_cl_data)
                                total_paid_leave['granted_el']=approved_leave[0]['el']
                                total_paid_leave['el_balance']=float(approved_leave[0]['el']) -float(availed_el_data)
                                total_paid_leave['granted_sl']=approved_leave[0]['sl']
                                total_paid_leave['sl_balance']=float(approved_leave[0]['sl']) -float(availed_sl_data)
                                total_paid_leave['total_granted_leave']=float(approved_leave[0]['cl']) + float(approved_leave[0]['el']) + float(approved_leave[0]['sl'])
                                total_paid_leave['total_leave_balances']=float(total_paid_leave['total_granted_leave']) - float(total_paid_leave['total_availed_leave'])
                                #print("total_paid_leave",total_paid_leave)
                                #time.sleep(10)
                                #**********HALF DAY OR FULL DAY LEAVE CALCULATION for New  Joining*************************
                                if request_type == 'HD' or request_type == 'FD':
                                    if  leave_type == 'SL' :
                                        #print('total_paid_leave_sl_balance',total_paid_leave['sl_balance'])
                                        #time.sleep(10)
                                        if total_paid_leave['sl_balance']>0.0:
                                            duration_length=AttendanceApprovalRequest.objects.get(id=instance.id,checkin_benchmark=False,is_requested=False)
                                            if request_type == 'HD':
                                                if duration_length.duration <=240 :
                                                    # raise serializers.ValidationError("Please apply half day Your diviation exceeds 2.5 Hours")
                                            
                                                    justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                            update(
                                                            request_type=request_type,
                                                            is_requested=True,
                                                            approved_status='pending',
                                                            request_date=datetime.date.today(),
                                                            justified_at=datetime.date.today(),
                                                            justification=validated_data.get('justification'),
                                                            justified_by=updated_by,
                                                            leave_type=validated_data.get('leave_type')
                                                            )

                                                    return validated_data

                                                elif duration_length.duration > 240 :
                                                    if (duration_start_end.duration_start.time() and duration_start_end.duration_end.time()) < worst_late_beanchmark:
                                                        # custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                                        justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                            update(
                                                            request_type=request_type,
                                                            is_requested=True,
                                                            approved_status='pending',
                                                            request_date=datetime.date.today(),
                                                            justified_at=datetime.date.today(),
                                                            justification=validated_data.get('justification'),
                                                            justified_by=updated_by,
                                                            leave_type=validated_data.get('leave_type')
                                                            )

                                                        return validated_data
                                                    elif duration_start_end.duration_start.time() < worst_late_beanchmark and duration_start_end.duration_end.time() > worst_late_beanchmark:
                                                        custom_exception_message(self,None,"Please apply full day Your diviation exceeds 4 Hours")
                                                    elif (duration_start_end.duration_start.time() and duration_start_end.duration_end.time()) > worst_late_beanchmark:
                                                        # custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                                        justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                            update(
                                                            request_type=request_type,
                                                            is_requested=True,
                                                            approved_status='pending',
                                                            request_date=datetime.date.today(),
                                                            justified_at=datetime.date.today(),
                                                            justification=validated_data.get('justification'),
                                                            justified_by=updated_by,
                                                            leave_type=validated_data.get('leave_type')
                                                            )

                                                        return validated_data
                                            elif request_type == 'FD' and total_paid_leave['sl_balance']>0.5:
                                                justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                    update(
                                                    request_type=request_type,
                                                    is_requested=True,
                                                    approved_status='pending',
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                                return validated_data
                                            else:
                                                custom_exception_message(self,None,"Not enough sick leave balance")
                                        else:
                                            # raise serializers.ValidationError("Sick leave limit exceeds")
                                            custom_exception_message(self,None,"Sick leave limit exceeds")
                                            
                                    elif leave_type =='CL':

                                        if total_paid_leave['cl_balance']>0.0:
                                            duration_length=AttendanceApprovalRequest.objects.get(id=instance.id,checkin_benchmark=False,is_requested=False)
                                            if request_type == 'HD':
                                                if duration_length.duration <=240:
                                                    justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,is_late_conveyance=False,checkin_benchmark=False,is_requested=False).\
                                                            update(
                                                            request_type=request_type,
                                                            is_requested=True,
                                                            approved_status='pending',
                                                            request_date=datetime.date.today(),
                                                            justified_at=datetime.date.today(),
                                                            justification=validated_data.get('justification'),
                                                            justified_by=updated_by,
                                                            leave_type=validated_data.get('leave_type')
                                                            )

                                                    return validated_data
                                                
                                                elif duration_length.duration > 240 :
                                                    if (duration_start_end.duration_start.time() and duration_start_end.duration_end.time()) < worst_late_beanchmark:
                                                        # custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                                        justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                            update(
                                                            request_type=request_type,
                                                            is_requested=True,
                                                            approved_status='pending',
                                                            request_date=datetime.date.today(),
                                                            justified_at=datetime.date.today(),
                                                            justification=validated_data.get('justification'),
                                                            justified_by=updated_by,
                                                            leave_type=validated_data.get('leave_type')
                                                            )

                                                        return validated_data
                                                    elif duration_start_end.duration_start.time() < worst_late_beanchmark and duration_start_end.duration_end.time() > worst_late_beanchmark:
                                                        custom_exception_message(self,None,"Please apply full day Your diviation exceeds 4 Hours")
                                                    elif (duration_start_end.duration_start.time() and duration_start_end.duration_end.time()) > worst_late_beanchmark:
                                                        # custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                                        justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                            update(
                                                            request_type=request_type,
                                                            is_requested=True,
                                                            approved_status='pending',
                                                            request_date=datetime.date.today(),
                                                            justified_at=datetime.date.today(),
                                                            justification=validated_data.get('justification'),
                                                            justified_by=updated_by,
                                                            leave_type=validated_data.get('leave_type')
                                                            )

                                                        return validated_data
                                            elif request_type == 'FD' and total_paid_leave['cl_balance']>0.5:
                                                justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                    update(
                                                    request_type=request_type,
                                                    is_requested=True,
                                                    approved_status='pending',
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                                return validated_data
                                            else:
                                                custom_exception_message(self,None,"Not enough casual leave balance")
                                        else:
                                            # raise serializers.ValidationError("casual leave limit exceeds")
                                            custom_exception_message(self,None,"casual leave limit exceeds")
                                    elif leave_type == 'EL':
                                        if total_paid_leave['el_balance']>0.0:
                                            duration_length=AttendanceApprovalRequest.objects.get(id=instance.id,checkin_benchmark=False,is_requested=False)
                                            if request_type == 'HD':
                                                if duration_length.duration <=240:
                                                    justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                            update(
                                                            request_type=request_type,
                                                            is_requested=True,
                                                            approved_status='pending',
                                                            request_date=datetime.date.today(),
                                                            justified_at=datetime.date.today(),
                                                            justification=validated_data.get('justification'),
                                                            justified_by=updated_by,
                                                            leave_type=validated_data.get('leave_type')
                                                            )

                                                    return validated_data
                                                elif duration_length.duration > 240:
                                                    if (duration_start_end.duration_start.time() and duration_start_end.duration_end.time()) < worst_late_beanchmark:
                                                        # custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                                        justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                            update(
                                                            request_type=request_type,
                                                            is_requested=True,
                                                            approved_status='pending',
                                                            request_date=datetime.date.today(),
                                                            justified_at=datetime.date.today(),
                                                            justification=validated_data.get('justification'),
                                                            justified_by=updated_by,
                                                            leave_type=validated_data.get('leave_type')
                                                            )

                                                        return validated_data
                                                    elif duration_start_end.duration_start.time() < worst_late_beanchmark and duration_start_end.duration_end.time() > worst_late_beanchmark:
                                                        custom_exception_message(self,None,"Please apply full day Your diviation exceeds 4 Hours")
                                                    elif (duration_start_end.duration_start.time() and duration_start_end.duration_end.time()) > worst_late_beanchmark:
                                                        # custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                                        justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                            update(
                                                            request_type=request_type,
                                                            is_requested=True,
                                                            approved_status='pending',
                                                            request_date=datetime.date.today(),
                                                            justified_at=datetime.date.today(),
                                                            justification=validated_data.get('justification'),
                                                            justified_by=updated_by,
                                                            leave_type=validated_data.get('leave_type')
                                                            )

                                                        return validated_data
                                            
                                            elif request_type == 'FD' and total_paid_leave['el_balance']>0.5:
                                                justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                    update(
                                                    request_type=request_type,
                                                    is_requested=True,
                                                    approved_status='pending',
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                                return validated_data
                                            else:
                                                custom_exception_message(self,None,"Not enough earn leave balance")
                                        else:
                                            # raise serializers.ValidationError("Earned leave limit exceeds")
                                            custom_exception_message(self,None,"Earned leave limit exceeds")
                                            
                                    elif leave_type == 'AB':
                                        justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                    update(
                                                    request_type=request_type,
                                                    is_requested=True,
                                                    approved_status='pending',
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                        return validated_data
                            else:
                                total_paid_leave['granted_cl']=core_user_detail[0]['granted_cl']
                                total_paid_leave['cl_balance']=float(core_user_detail[0]['granted_cl']) - float(availed_cl_data)
                                total_paid_leave['granted_el']=core_user_detail[0]['granted_el']
                                total_paid_leave['el_balance']=float(core_user_detail[0]['granted_el']) - float(availed_el_data)
                                total_paid_leave['granted_sl']=core_user_detail[0]['granted_sl']
                                total_paid_leave['sl_balance']=float(core_user_detail[0]['granted_sl']) - float(availed_sl_data)
                                total_paid_leave['total_granted_leave']=float(core_user_detail[0]['granted_cl']) + float(core_user_detail[0]['granted_el']) + float(core_user_detail[0]['granted_sl'])
                                total_paid_leave['total_leave_balances']=float(total_paid_leave['total_granted_leave']) - float(total_paid_leave['total_availed_leave'])
                                print("total_paid_leave",total_paid_leave)
                                #**********HALF DAY OR FULL DAY LEAVE CALCULATION Regular *************************
                                if request_type == 'HD' or request_type == 'FD':
                                    if  leave_type == 'SL' :
                                        
                                        if total_paid_leave['sl_balance']>0.0:
                                            duration_length=AttendanceApprovalRequest.objects.get(id=instance.id,checkin_benchmark=False,is_requested=False)
                                            if request_type == 'HD':
                                                if duration_length.duration <=240 :
                                                    # raise serializers.ValidationError("Please apply half day Your diviation exceeds 2.5 Hours")
                                            
                                                    justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                            update(
                                                            request_type=request_type,
                                                            is_requested=True,
                                                            approved_status='pending',
                                                            request_date=datetime.date.today(),
                                                            justified_at=datetime.date.today(),
                                                            justification=validated_data.get('justification'),
                                                            justified_by=updated_by,
                                                            leave_type=validated_data.get('leave_type')
                                                            )

                                                    return validated_data

                                                elif duration_length.duration > 240 :
                                                    if (duration_start_end.duration_start.time() and duration_start_end.duration_end.time()) < worst_late_beanchmark:
                                                        # custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                                        justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                            update(
                                                            request_type=request_type,
                                                            is_requested=True,
                                                            approved_status='pending',
                                                            request_date=datetime.date.today(),
                                                            justified_at=datetime.date.today(),
                                                            justification=validated_data.get('justification'),
                                                            justified_by=updated_by,
                                                            leave_type=validated_data.get('leave_type')
                                                            )

                                                        return validated_data
                                                    elif duration_start_end.duration_start.time() < worst_late_beanchmark and duration_start_end.duration_end.time() > worst_late_beanchmark:
                                                        custom_exception_message(self,None,"Please apply full day Your diviation exceeds 4 Hours")
                                                    elif (duration_start_end.duration_start.time() and duration_start_end.duration_end.time()) > worst_late_beanchmark:
                                                        # custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                                        justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                            update(
                                                            request_type=request_type,
                                                            is_requested=True,
                                                            approved_status='pending',
                                                            request_date=datetime.date.today(),
                                                            justified_at=datetime.date.today(),
                                                            justification=validated_data.get('justification'),
                                                            justified_by=updated_by,
                                                            leave_type=validated_data.get('leave_type')
                                                            )

                                                        return validated_data
                                            elif request_type == 'FD' and total_paid_leave['sl_balance']>0.5:
                                                justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                    update(
                                                    request_type=request_type,
                                                    is_requested=True,
                                                    approved_status='pending',
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )
                                                return validated_data
                                            else:
                                                custom_exception_message(self,None,"Not enough sick leave balance")
                                                
                                        else:
                                            # raise serializers.ValidationError("Sick leave limit exceeds")
                                            custom_exception_message(self,None,"Sick leave limit exceeds")
                                            
                                    elif leave_type =='CL':
                                        if total_paid_leave['cl_balance']>0.0:
                                            duration_length=AttendanceApprovalRequest.objects.get(id=instance.id,checkin_benchmark=False,is_requested=False)
                                            if request_type == 'HD':
                                                if  duration_length.duration <=240:
                                                    justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,is_late_conveyance=False,checkin_benchmark=False,is_requested=False).\
                                                            update(
                                                            request_type=request_type,
                                                            is_requested=True,
                                                            approved_status='pending',
                                                            request_date=datetime.date.today(),
                                                            justified_at=datetime.date.today(),
                                                            justification=validated_data.get('justification'),
                                                            justified_by=updated_by,
                                                            leave_type=validated_data.get('leave_type')
                                                            )

                                                    return validated_data
                                                
                                                elif duration_length.duration > 240 :
                                                    if (duration_start_end.duration_start.time() and duration_start_end.duration_end.time()) < worst_late_beanchmark:
                                                        # custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                                        justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                            update(
                                                            request_type=request_type,
                                                            is_requested=True,
                                                            approved_status='pending',
                                                            request_date=datetime.date.today(),
                                                            justified_at=datetime.date.today(),
                                                            justification=validated_data.get('justification'),
                                                            justified_by=updated_by,
                                                            leave_type=validated_data.get('leave_type')
                                                            )

                                                        return validated_data
                                                    elif duration_start_end.duration_start.time() < worst_late_beanchmark and duration_start_end.duration_end.time() > worst_late_beanchmark:
                                                        custom_exception_message(self,None,"Please apply full day Your diviation exceeds 4 Hours")
                                                    elif (duration_start_end.duration_start.time() and duration_start_end.duration_end.time()) > worst_late_beanchmark:
                                                        # custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                                        justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                            update(
                                                            request_type=request_type,
                                                            is_requested=True,
                                                            approved_status='pending',
                                                            request_date=datetime.date.today(),
                                                            justified_at=datetime.date.today(),
                                                            justification=validated_data.get('justification'),
                                                            justified_by=updated_by,
                                                            leave_type=validated_data.get('leave_type')
                                                            )

                                                        return validated_data
                                            elif request_type == 'FD' and total_paid_leave['cl_balance']>0.5:
                                                justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                    update(
                                                    request_type=request_type,
                                                    is_requested=True,
                                                    approved_status='pending',
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                                return validated_data
                                            else:
                                                custom_exception_message(self,None,"Not enough casual leave balance")
                                        else:
                                            # raise serializers.ValidationError("casual leave limit exceeds")
                                            custom_exception_message(self,None,"casual leave limit exceeds")
                                    elif leave_type =='EL':
                                        if total_paid_leave['el_balance']>0.0:
                                            duration_length=AttendanceApprovalRequest.objects.get(id=instance.id,checkin_benchmark=False,is_requested=False)
                                            if request_type == 'HD':
                                                if  duration_length.duration <=240:
                                                    justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                            update(
                                                            request_type=request_type,
                                                            is_requested=True,
                                                            approved_status='pending',
                                                            request_date=datetime.date.today(),
                                                            justified_at=datetime.date.today(),
                                                            justification=validated_data.get('justification'),
                                                            justified_by=updated_by,
                                                            leave_type=validated_data.get('leave_type')
                                                            )

                                                    return validated_data
                                                elif duration_length.duration > 240:
                                                    if (duration_start_end.duration_start.time() and duration_start_end.duration_end.time()) < worst_late_beanchmark:
                                                        # custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                                        justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                            update(
                                                            request_type=request_type,
                                                            is_requested=True,
                                                            approved_status='pending',
                                                            request_date=datetime.date.today(),
                                                            justified_at=datetime.date.today(),
                                                            justification=validated_data.get('justification'),
                                                            justified_by=updated_by,
                                                            leave_type=validated_data.get('leave_type')
                                                            )

                                                        return validated_data
                                                    elif duration_start_end.duration_start.time() < worst_late_beanchmark and duration_start_end.duration_end.time() > worst_late_beanchmark:
                                                        custom_exception_message(self,None,"Please apply full day Your diviation exceeds 4 Hours")
                                                    elif (duration_start_end.duration_start.time() and duration_start_end.duration_end.time()) > worst_late_beanchmark:
                                                        # custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                                        justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                            update(
                                                            request_type=request_type,
                                                            is_requested=True,
                                                            approved_status='pending',
                                                            request_date=datetime.date.today(),
                                                            justified_at=datetime.date.today(),
                                                            justification=validated_data.get('justification'),
                                                            justified_by=updated_by,
                                                            leave_type=validated_data.get('leave_type')
                                                            )

                                                        return validated_data
                                            
                                            elif request_type == 'FD' and total_paid_leave['el_balance']>0.5:
                                                justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                    update(
                                                    request_type=request_type,
                                                    is_requested=True,
                                                    approved_status='pending',
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                                return validated_data
                                        else:
                                            # raise serializers.ValidationError("Earned leave limit exceeds")
                                            custom_exception_message(self,None,"Earned leave limit exceeds")
                                    elif leave_type == 'AB':
                                        justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                    update(
                                                    request_type=request_type,
                                                    is_requested=True,
                                                    approved_status='pending',
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                        return validated_data
                    
                    #*****************As the user is already present hence partial OD********************************************************
                    elif request_type == 'OD':          
                        vehicle_type= validated_data.get('vehicle_type') if validated_data.get('vehicle_type') else None
                        from_place= validated_data.get('from_place') if validated_data.get('from_place') else None
                        to_place= validated_data.get('to_place') if validated_data.get('to_place') else None
                        conveyance_expense= validated_data.get('conveyance_expense') if validated_data.get('conveyance_expense') else 0.0
                        conveyance_remarks= validated_data.get('conveyance_purpose') if validated_data.get('conveyance_purpose') else None
                        conveyance_alloted_by= validated_data.get('conveyance_alloted_by') if validated_data.get('conveyance_alloted_by') else None
                        #print(vehicle_type,from_place,to_place,conveyance_expense,conveyance_remarks,conveyance_alloted_by)
                        if from_place or to_place or conveyance_remarks:
                            #print("aisaichai ")
                            justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,is_requested=False).\
                                update(
                                request_type='POD',
                                is_requested=True,
                                approved_status='pending',
                                request_date=datetime.date.today(),
                                justified_at=datetime.date.today(),
                                justification=validated_data.get('justification'),
                                justified_by=updated_by,
                                is_conveyance=True,
                                conveyance_approval=0,
                                vehicle_type_id=vehicle_type,
                                conveyance_alloted_by_id=conveyance_alloted_by,
                                from_place=from_place,
                                to_place=to_place,
                                conveyance_expense=conveyance_expense,
                                conveyance_purpose=conveyance_remarks
                                )
                            print("justify_attendence",justify_attendence)

                            return validated_data
                        else:
                            justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                update(
                                request_type='POD',
                                is_requested=True,
                                approved_status='pending',
                                request_date=datetime.date.today(),
                                justified_at=datetime.date.today(),
                                justification=validated_data.get('justification'),
                                justified_by=updated_by,
                                is_conveyance=False,
                                )

                            return validated_data
                    
                    #*****************Request for mispunch************************************************************************************
                    elif request_type == 'MP': 
                        justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                update(
                                request_type=request_type,
                                is_requested=True,
                                approved_status='pending',
                                request_date=datetime.date.today(),
                                justified_at=datetime.date.today(),
                                justification=validated_data.get('justification'),
                                justified_by=updated_by)

                        return validated_data

                    return validated_data
                #REQUEST ONLY IF User ABSENT 
                else:
                    '''
                        Commented By Rupam Hazra 16/01/2020 for half day open for absent and added HD if condition
                    '''
                    # if request_type == 'FD':
                    #     leave_type=validated_data.get('leave_type')
                    #     #*************check and calculation of leave counts available****************** 
                    #     total_paid_leave={}
                    #     advance_leave=EmployeeAdvanceLeaves.objects.filter(Q(employee=employee_id)&
                    #                                        Q(is_deleted=False)&
                    #                                        (Q(approved_status='pending')|Q(approved_status='approved'))
                    #                                       ).values('leave_type','start_date','end_date')
                    #     print('advance_leave',advance_leave)     
                    #     advance_cl=0
                    #     advance_el=0
                    #     advance_ab=0
                    #     day=0
                    #     if advance_leave:
                    #         for leave in advance_leave:
                    #             print('leave',leave)
                    #             start_date=leave['start_date'].date()
                    #             end_date=leave['end_date'].date()+timedelta(days=1)
                    #             print('start_date,end_date',start_date,end_date)
                    #             if date_object < end_date:
                    #                 if date_object < start_date:
                    #                     day=(end_date-start_date).days 
                    #                     print('day',day)
                    #                 elif date_object > start_date:
                    #                     day=(end_date-date_object).days
                    #                     print('day2',day)
                    #                 else:
                    #                     day=(end_date-date_object).days

                    #             if leave['leave_type']=='CL':
                    #                 advance_cl+=day
                    #             elif leave['leave_type']=='EL':
                    #                 advance_el+=day
                    #             elif leave['leave_type']=='AB':
                    #                 advance_ab+=day
                        
                        
                        
                    #     """ 
                    #     LEAVE CALCULATION:-
                    #     1)SINGLE LEAVE CALCULATION
                    #     2)MULTIPLE LEAVE FOR ONE DAY IS AUTO CONVERTED TO ONE TYPE OF LEAVE 
                    #     EDITED BY :- Abhishek.singh@shyamfuture.com
                        
                    #     """ 
                    #     availed_hd_cl=0.0
                    #     availed_hd_el=0.0
                    #     availed_hd_sl=0.0
                    #     availed_hd_ab=0.0
                    #     availed_cl=0.0
                    #     availed_el=0.0
                    #     availed_sl=0.0
                    #     availed_ab=0.0

                    #     attendence_daily_data = AttendanceApprovalRequest.objects.filter(((Q(leave_type_changed_period__isnull=False)&(Q(leave_type_changed_period='FD')|Q(leave_type_changed_period='HD')))|
                    #                                                                     (Q(leave_type_changed_period__isnull=True)&(Q(request_type='FD')|Q(request_type='HD')))),
                    #                                                                     attendance__employee=employee_id,is_requested=True).values('duration_start__date').distinct()
                    #     print("attendence_daily_data",attendence_daily_data)
                    #     date_list = [x['duration_start__date'] for x in attendence_daily_data.iterator()]
                    #     print("date_list",date_list)
                    #     # for data in attendence_daily_data.iterator():
                    #         # print(datetime.now())
                    #     availed_master_wo_reject_fd = AttendanceApprovalRequest.objects.\
                    #             filter((Q(approved_status='pending')|Q(approved_status='approved')|Q(approved_status='reject')),
                    #                     (Q(leave_type__isnull=False)|Q(leave_type_changed_period__isnull=False)),
                    #                     attendance__employee=employee_id,
                    #                     attendance_date__in=date_list,is_requested=True,is_deleted=False).annotate(
                    #                         leave_type_final = Case(
                    #                         When((Q(leave_type_changed_period__isnull=False)&Q(leave_type_changed_period='FD')),then=F('leave_type_changed')),
                    #                         When((Q(leave_type_changed_period__isnull=True)&Q(request_type='FD')),then=F('leave_type')),
                    #                         output_field=CharField()
                    #                     ),
                    #                     leave_type_final_hd = Case(
                    #                         When((Q(leave_type_changed_period__isnull=False)&Q(leave_type_changed_period='HD')),then=F('leave_type_changed')),
                    #                         When((Q(leave_type_changed_period__isnull=True)&Q(request_type='HD')),then=F('leave_type')),
                    #                         output_field=CharField()
                    #                     ),
                    #                     ).values('leave_type_final','leave_type_final_hd','attendance_date').distinct()
                    #     print("availed_master_wo_reject_fd",availed_master_wo_reject_fd)
                    #     if availed_master_wo_reject_fd:

                    #         for data in date_list:
                    #             availed_FD=availed_master_wo_reject_fd.filter(attendance_date=data)
                                
                    #             print("availed_HD",availed_FD)
                    #             if availed_FD.filter(leave_type_final__isnull=False):
                    #                 if availed_FD.values('leave_type_final').count() >1:
                    #                     if availed_FD.filter(leave_type_final='AB'):
                    #                         availed_ab=availed_ab+1.0

                    #                     elif availed_FD.filter(leave_type_final='CL'):
                    #                         availed_cl=availed_cl+1.0
                                                    

                    #                 else:
                    #                     l_type=availed_FD[0]['leave_type_final']
                    #                     if l_type == 'CL':
                    #                         availed_cl=availed_cl+1.0
                    #                     elif l_type == 'EL':
                    #                         availed_el=availed_el+1.0
                    #                     elif l_type == 'SL':
                    #                         availed_sl=availed_sl+1.0
                    #                     elif l_type == 'AB':
                    #                         availed_ab=availed_ab+1.0

                    #             elif availed_FD.filter(leave_type_final_hd__isnull=False):
                    #                 if availed_FD.values('leave_type_final_hd').count() >1:
                    #                     if availed_FD.filter(leave_type_final_hd='AB'):
                    #                         availed_hd_ab=availed_hd_ab+1.0

                    #                     elif availed_FD.filter(leave_type_final_hd='CL'):
                    #                         availed_hd_cl=availed_hd_cl+1.0
                                                    

                    #                 else:
                    #                     l_type=availed_FD[0]['leave_type_final_hd']
                    #                     if l_type == 'CL':
                    #                         availed_hd_cl=availed_hd_cl+1.0
                    #                     elif l_type == 'EL':
                    #                         availed_hd_el=availed_hd_el+1.0
                    #                     elif l_type == 'SL':
                    #                         availed_hd_sl=availed_hd_sl+1.0
                    #                     elif l_type == 'AB':
                    #                         availed_hd_ab=availed_hd_ab+1.0


                    #     availed_cl_data=float(availed_cl)+float(advance_cl)+float(availed_hd_cl/2)
                    #     availed_el_data=float(availed_el)+float(advance_el)+float(availed_hd_el/2)
                    #     availed_sl_data=float(availed_sl)+float(availed_hd_sl/2)
                    #     availed_ab_data=float(availed_ab)+float(advance_ab)+float(availed_hd_ab/2)

                      
                    #     total_paid_leave['availed_cl']=float(availed_cl)+float(advance_cl)+float(availed_hd_cl/2)
                    #     total_paid_leave['availed_el']=float(availed_el)+float(advance_el)+float(availed_hd_el/2)
                    #     total_paid_leave['availed_sl']=float(availed_sl)+float(availed_hd_sl/2)
                    #     total_paid_leave['availed_ab']=float(availed_ab)+float(advance_ab)+float(availed_hd_ab/2)
                    #     total_paid_leave['total_availed_leave']=availed_cl_data + availed_el_data + availed_ab_data

                    #     core_user_detail=TCoreUserDetail.objects.filter(cu_user=employee_id,cu_is_deleted=False).values('joining_date',
                    #                                                                                                 'granted_cl',
                    #                                                                                                 'granted_sl',
                    #                                                                                                 'granted_el'
                    #                                                                                                 )
                    #     print('core_user_detail',core_user_detail)
                    #     if core_user_detail:
                    #         if core_user_detail[0]['joining_date']>total_month_grace[0]['year_start_date']:
                    #             print("joining")
                    #             approved_leave=JoiningApprovedLeave.objects.filter(employee=employee_id,is_deleted=False).values('cl',
                    #                                                                                                             'el',
                    #                                                                                                             'sl',
                    #                                                                                                             'year',
                    #                                                                                                             'month',
                    #                                                                                                             'first_grace' 
                    #                                                                                                             )
                    #             print("approved_leave",approved_leave)
                    #             total_paid_leave['granted_cl']=approved_leave[0]['cl'] 
                    #             total_paid_leave['cl_balance']=float(approved_leave[0]['cl']) -float(availed_cl_data)
                    #             total_paid_leave['granted_el']=approved_leave[0]['el']
                    #             total_paid_leave['el_balance']=float(approved_leave[0]['el']) -float(availed_el_data)
                    #             total_paid_leave['granted_sl']=approved_leave[0]['sl']
                    #             total_paid_leave['sl_balance']=float(approved_leave[0]['sl']) -float(availed_sl_data)
                    #             total_paid_leave['total_granted_leave']=float(approved_leave[0]['cl']) + float(approved_leave[0]['el']) + float(approved_leave[0]['sl'])
                    #             total_paid_leave['total_leave_balances']=float(total_paid_leave['total_granted_leave']) - float(total_paid_leave['total_availed_leave'])
                    #             print("total_paid_leave",total_paid_leave)
                    #             #**********HALF DAY OR FULL DAY LEAVE CALCULATION for New  Joining*************************
                    #             if request_type == 'FD':
                    #                 if leave_type == 'SL' :
                                        
                    #                     if total_paid_leave['sl_balance']>0.5:
                    #                         justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                    #                                 update(
                    #                                 request_type=request_type,
                    #                                 is_requested=True,
                    #                                 approved_status='pending',
                    #                                 request_date=datetime.date.today(),
                    #                                 justified_at=datetime.date.today(),
                    #                                 justification=validated_data.get('justification'),
                    #                                 justified_by=updated_by,
                    #                                 leave_type=validated_data.get('leave_type')
                    #                                 )

                    #                         return validated_data
                    #                     else:
                    #                         # raise serializers.ValidationError("Sick leave limit exceeds")
                    #                         custom_exception_message(self,None,"Not enough Sick leave to apply full day")
                    #                 elif leave_type =='CL':
                    #                     print("na na na ")
                    #                     if total_paid_leave['cl_balance']>0.5:
                    #                         justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                    #                                 update(
                    #                                 request_type=request_type,
                    #                                 is_requested=True,
                    #                                 approved_status='pending',
                    #                                 request_date=datetime.date.today(),
                    #                                 justified_at=datetime.date.today(),
                    #                                 justification=validated_data.get('justification'),
                    #                                 justified_by=updated_by,
                    #                                 leave_type=validated_data.get('leave_type')
                    #                                 )

                    #                         return validated_data
                    #                     else:
                    #                         # raise serializers.ValidationError("casual leave limit exceeds")
                    #                         custom_exception_message(self,None,"Not enough casual leave to apply full day")
                    #                 elif leave_type == 'EL':
                    #                     if total_paid_leave['el_balance']>0.5:
                    #                         justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                    #                                 update(
                    #                                 request_type=request_type,
                    #                                 is_requested=True,
                    #                                 approved_status='pending',
                    #                                 request_date=datetime.date.today(),
                    #                                 justified_at=datetime.date.today(),
                    #                                 justification=validated_data.get('justification'),
                    #                                 justified_by=updated_by,
                    #                                 leave_type=validated_data.get('leave_type')
                    #                                 )

                    #                         return validated_data
                    #                     else:
                    #                         # raise serializers.ValidationError("Earned leave limit exceeds")
                    #                         custom_exception_message(self,None,"Not enough Earned leave to apply full day")
                    #                 elif leave_type == 'AB':
                    #                     justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                    #                                 update(
                    #                                 request_type=request_type,
                    #                                 is_requested=True,
                    #                                 approved_status='pending',
                    #                                 request_date=datetime.date.today(),
                    #                                 justified_at=datetime.date.today(),
                    #                                 justification=validated_data.get('justification'),
                    #                                 justified_by=updated_by,
                    #                                 leave_type=validated_data.get('leave_type')
                    #                                 )

                    #                     return validated_data
                    #         else:
                    #             total_paid_leave['granted_cl']=core_user_detail[0]['granted_cl']
                    #             total_paid_leave['cl_balance']=float(core_user_detail[0]['granted_cl']) - float(availed_cl_data)
                    #             total_paid_leave['granted_el']=core_user_detail[0]['granted_el']
                    #             total_paid_leave['el_balance']=float(core_user_detail[0]['granted_el']) - float(availed_el_data)
                    #             total_paid_leave['granted_sl']=core_user_detail[0]['granted_sl']
                    #             total_paid_leave['sl_balance']=float(core_user_detail[0]['granted_sl']) - float(availed_sl_data)
                    #             total_paid_leave['total_granted_leave']=float(core_user_detail[0]['granted_cl']) + float(core_user_detail[0]['granted_el']) + float(core_user_detail[0]['granted_sl'])
                    #             total_paid_leave['total_leave_balances']=float(total_paid_leave['total_granted_leave']) - float(total_paid_leave['total_availed_leave'])
                    #             print("total_paid_leave",total_paid_leave)
                    #             #**********HALF DAY OR FULL DAY LEAVE CALCULATION Regular *************************
                    #             if request_type == 'FD':
                    #                 if leave_type =='SL':
                    #                     if total_paid_leave['sl_balance']>0.5:
                    #                         justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                    #                                 update(
                    #                                 request_type=request_type,
                    #                                 is_requested=True,
                    #                                 approved_status='pending',
                    #                                 request_date=datetime.date.today(),
                    #                                 justified_at=datetime.date.today(),
                    #                                 justification=validated_data.get('justification'),
                    #                                 justified_by=updated_by,
                    #                                 leave_type=validated_data.get('leave_type')
                    #                                 )

                    #                         return validated_data
                    #                     else:
                    #                         # raise serializers.ValidationError("Sick leave limit exceeds")
                    #                         custom_exception_message(self,None,"Not enough Sick leave to apply full day")
                    #                 elif leave_type =='CL':
                    #                     if total_paid_leave['cl_balance']>0.5:
                    #                         justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                    #                                 update(
                    #                                 request_type=request_type,
                    #                                 is_requested=True,
                    #                                 approved_status='pending',
                    #                                 request_date=datetime.date.today(),
                    #                                 justified_at=datetime.date.today(),
                    #                                 justification=validated_data.get('justification'),
                    #                                 justified_by=updated_by,
                    #                                 leave_type=validated_data.get('leave_type')
                    #                                 )

                    #                         return validated_data
                    #                     else:
                    #                         # raise serializers.ValidationError("casual leave limit exceeds")
                    #                         custom_exception_message(self,None,"Not enough casual leave to apply full day")
                    #                 elif leave_type =='EL':
                    #                     if total_paid_leave['el_balance']>0.5:
                    #                         justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                    #                                 update(
                    #                                 request_type=request_type,
                    #                                 is_requested=True,
                    #                                 approved_status='pending',
                    #                                 request_date=datetime.date.today(),
                    #                                 justified_at=datetime.date.today(),
                    #                                 justification=validated_data.get('justification'),
                    #                                 justified_by=updated_by,
                    #                                 leave_type=validated_data.get('leave_type')
                    #                                 )

                    #                         return validated_data
                    #                     else:
                    #                         # raise serializers.ValidationError("Earned leave limit exceeds")
                    #                         custom_exception_message(self,None,"Not enough Earned leave to apply full day")
                                    
                    #                 elif leave_type == 'AB':
                    #                     justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                    #                                 update(
                    #                                 request_type=request_type,
                    #                                 is_requested=True,
                    #                                 approved_status='pending',
                    #                                 request_date=datetime.date.today(),
                    #                                 justified_at=datetime.date.today(),
                    #                                 justification=validated_data.get('justification'),
                    #                                 justified_by=updated_by,
                    #                                 leave_type=validated_data.get('leave_type')
                    #                                 )

                    #                     return validated_data

                    if request_type == 'HD' or request_type == 'FD':
                        worst_late_beanchmark=TCoreUserDetail.objects.get(cu_user=employee_id).worst_late
                        duration_start_end=AttendanceApprovalRequest.objects.get(id=instance.id)
                        leave_type=validated_data.get('leave_type')
                        #*************check and calculation of leave counts available****************** 
                        total_paid_leave={}
                        advance_leave=EmployeeAdvanceLeaves.objects.filter(Q(employee=employee_id)&
                                                           Q(is_deleted=False)&
                                                           (Q(approved_status='pending')|Q(approved_status='approved'))
                                                          ).values('leave_type','start_date','end_date')
                        #print('advance_leave',advance_leave)     
                        advance_cl=0
                        advance_el=0
                        advance_ab=0
                        day=0
                        # if advance_leave:
                        #     for leave in advance_leave:
                        #         print('leave',leave)
                        #         start_date=leave['start_date'].date()
                        #         end_date=leave['end_date'].date()+timedelta(days=1)
                        #         print('start_date,end_date',start_date,end_date)
                        #         if date_object < end_date:
                        #             if date_object < start_date:
                        #                 day=(end_date-start_date).days 
                        #                 print('day',day)
                        #             elif date_object > start_date:
                        #                 day=(end_date-date_object).days
                        #                 print('day2',day)
                        #             else:
                        #                 day=(end_date-date_object).days

                        #         if leave['leave_type']=='CL':
                        #             advance_cl+=day
                        #         elif leave['leave_type']=='EL':
                        #             advance_el+=day
                        #         elif leave['leave_type']=='AB':
                        #             advance_ab+=day
                        year_end_date = total_month_grace[0]['year_end_date']
                        last_attendance = Attendance.objects.filter(employee=employee_id).values_list('date__date',flat=True).order_by('-date')[:1]
                        print("last_attendance",last_attendance)
                        last_attendance = last_attendance[0] if last_attendance else date_object
                        
                        if last_attendance<year_end_date.date():
                            print("last_attendancehfthtfrhfth",last_attendance)
                            adv_str_date = last_attendance+timedelta(days=1)
                            adv_end_date = year_end_date.date()+timedelta(days=1)
                            if advance_leave:
                                for leave in advance_leave:
                                    print('leave',leave)
                                    start_date=leave['start_date'].date()
                                    end_date=leave['end_date'].date()+timedelta(days=1)
                                    print('start_date,end_date',start_date,end_date)

                                    if adv_str_date<=start_date and adv_end_date>=start_date:
                                        if adv_end_date>=end_date:
                                            day = (end_date-start_date).days
                                        elif adv_end_date<=end_date:
                                            day = (adv_end_date-start_date).days
                                    elif adv_str_date>start_date:
                                        if adv_end_date<=end_date:
                                            day = (adv_end_date-adv_str_date).days
                                        elif adv_str_date<=end_date and adv_end_date>=end_date:
                                            day = (end_date-adv_str_date).days
                                        
                                    if leave['leave_type']=='CL':
                                        advance_cl+=day
                                    elif leave['leave_type']=='EL':
                                        advance_el+=day
                                    elif leave['leave_type']=='AB':
                                        advance_ab+=day
                        
                        """ 
                        LEAVE CALCULATION:-
                        1)SINGLE LEAVE CALCULATION
                        2)MULTIPLE LEAVE FOR ONE DAY IS AUTO CONVERTED TO ONE TYPE OF LEAVE 
                        EDITED BY :- Abhishek.singh@shyamfuture.com
                        
                        """ 
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
                        #print("attendence_daily_data",attendence_daily_data)
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
                        #print("availed_master_wo_reject_fd",availed_master_wo_reject_fd)
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

                        availed_cl_data=float(availed_cl)+float(advance_cl)+float(availed_hd_cl/2)
                        availed_el_data=float(availed_el)+float(advance_el)+float(availed_hd_el/2)
                        availed_sl_data=float(availed_sl)+float(availed_hd_sl/2)
                        availed_ab_data=float(availed_ab)+float(advance_ab)+float(availed_hd_ab/2)

                        total_paid_leave['availed_cl']=float(availed_cl)+float(advance_cl)+float(availed_hd_cl/2)
                        total_paid_leave['availed_el']=float(availed_el)+float(advance_el)+float(availed_hd_el/2)
                        total_paid_leave['availed_sl']=float(availed_sl)+float(availed_hd_sl/2)
                        total_paid_leave['availed_ab']=float(availed_ab)+float(advance_ab)+float(availed_hd_ab/2)
                        total_paid_leave['total_availed_leave']=availed_cl_data + availed_el_data + availed_ab_data

                        core_user_detail=TCoreUserDetail.objects.filter(cu_user=employee_id,cu_is_deleted=False).values('joining_date',
                                                                                                                    'granted_cl',
                                                                                                                    'granted_sl',
                                                                                                                    'granted_el'
                                                                                                                    )
                        #print('core_user_detail',core_user_detail)
                        if core_user_detail:
                            if core_user_detail[0]['joining_date']>total_month_grace[0]['year_start_date']:
                                #print("joining")
                                approved_leave=JoiningApprovedLeave.objects.filter(employee=employee_id,is_deleted=False).values('cl',
                                                                                                                                'el',
                                                                                                                                'sl',
                                                                                                                                'year',
                                                                                                                                'month',
                                                                                                                                'first_grace' 
                                                                                                                     )
                                #print("approved_leave",approved_leave)
                                total_paid_leave['granted_cl']=approved_leave[0]['cl'] 
                                total_paid_leave['cl_balance']=float(approved_leave[0]['cl']) -float(availed_cl_data)
                                total_paid_leave['granted_el']=approved_leave[0]['el']
                                total_paid_leave['el_balance']=float(approved_leave[0]['el']) -float(availed_el_data)
                                total_paid_leave['granted_sl']=approved_leave[0]['sl']
                                total_paid_leave['sl_balance']=float(approved_leave[0]['sl']) -float(availed_sl_data)
                                total_paid_leave['total_granted_leave']=float(approved_leave[0]['cl']) + float(approved_leave[0]['el']) + float(approved_leave[0]['sl'])
                                total_paid_leave['total_leave_balances']=float(total_paid_leave['total_granted_leave']) - float(total_paid_leave['total_availed_leave'])
                                #print("total_paid_leave",total_paid_leave)
                                #**********HALF DAY OR FULL DAY LEAVE CALCULATION for New  Joining*************************
                                if request_type == 'HD' or request_type == 'FD':
                                    if  leave_type == 'SL' :
                                        
                                        if total_paid_leave['sl_balance']>0.0:
                                            duration_length=AttendanceApprovalRequest.objects.get(id=instance.id,checkin_benchmark=False,is_requested=False)
                                            if request_type == 'HD':
                                                if duration_length.duration <=240 :
                                                    # raise serializers.ValidationError("Please apply half day Your diviation exceeds 2.5 Hours")
                                            
                                                    justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                            update(
                                                            request_type=request_type,
                                                            is_requested=True,
                                                            approved_status='pending',
                                                            request_date=datetime.date.today(),
                                                            justified_at=datetime.date.today(),
                                                            justification=validated_data.get('justification'),
                                                            justified_by=updated_by,
                                                            leave_type=validated_data.get('leave_type')
                                                            )

                                                    return validated_data

                                                elif duration_length.duration > 240 :
                                                    if (duration_start_end.duration_start.time() and duration_start_end.duration_end.time()) < worst_late_beanchmark:
                                                        # custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                                        justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                            update(
                                                            request_type=request_type,
                                                            is_requested=True,
                                                            approved_status='pending',
                                                            request_date=datetime.date.today(),
                                                            justified_at=datetime.date.today(),
                                                            justification=validated_data.get('justification'),
                                                            justified_by=updated_by,
                                                            leave_type=validated_data.get('leave_type')
                                                            )

                                                        return validated_data
                                                    elif duration_start_end.duration_start.time() < worst_late_beanchmark and duration_start_end.duration_end.time() > worst_late_beanchmark:
                                                        custom_exception_message(self,None,"Please apply full day Your diviation exceeds 4 Hours")
                                                    elif (duration_start_end.duration_start.time() and duration_start_end.duration_end.time()) > worst_late_beanchmark:
                                                        # custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                                        justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                            update(
                                                            request_type=request_type,
                                                            is_requested=True,
                                                            approved_status='pending',
                                                            request_date=datetime.date.today(),
                                                            justified_at=datetime.date.today(),
                                                            justification=validated_data.get('justification'),
                                                            justified_by=updated_by,
                                                            leave_type=validated_data.get('leave_type')
                                                            )

                                                        return validated_data
                                            elif request_type == 'FD' and total_paid_leave['sl_balance']>0.5:
                                                justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                    update(
                                                    request_type=request_type,
                                                    is_requested=True,
                                                    approved_status='pending',
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                                return validated_data
                                            else:
                                                custom_exception_message(self,None,"Not enough sick leave balance")
                                        else:
                                            # raise serializers.ValidationError("Sick leave limit exceeds")
                                            custom_exception_message(self,None,"Sick leave limit exceeds")
                                            
                                    elif leave_type =='CL':

                                        if total_paid_leave['cl_balance']>0.0:
                                            duration_length=AttendanceApprovalRequest.objects.get(id=instance.id,checkin_benchmark=False,is_requested=False)
                                            if request_type == 'HD':
                                                if duration_length.duration <=240:
                                                    justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,is_late_conveyance=False,checkin_benchmark=False,is_requested=False).\
                                                            update(
                                                            request_type=request_type,
                                                            is_requested=True,
                                                            approved_status='pending',
                                                            request_date=datetime.date.today(),
                                                            justified_at=datetime.date.today(),
                                                            justification=validated_data.get('justification'),
                                                            justified_by=updated_by,
                                                            leave_type=validated_data.get('leave_type')
                                                            )

                                                    return validated_data
                                                
                                                elif duration_length.duration > 240 :
                                                    if (duration_start_end.duration_start.time() and duration_start_end.duration_end.time()) < worst_late_beanchmark:
                                                        # custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                                        justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                            update(
                                                            request_type=request_type,
                                                            is_requested=True,
                                                            approved_status='pending',
                                                            request_date=datetime.date.today(),
                                                            justified_at=datetime.date.today(),
                                                            justification=validated_data.get('justification'),
                                                            justified_by=updated_by,
                                                            leave_type=validated_data.get('leave_type')
                                                            )

                                                        return validated_data
                                                    elif duration_start_end.duration_start.time() < worst_late_beanchmark and duration_start_end.duration_end.time() > worst_late_beanchmark:
                                                        custom_exception_message(self,None,"Please apply full day Your diviation exceeds 4 Hours")
                                                    elif (duration_start_end.duration_start.time() and duration_start_end.duration_end.time()) > worst_late_beanchmark:
                                                        # custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                                        justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                            update(
                                                            request_type=request_type,
                                                            is_requested=True,
                                                            approved_status='pending',
                                                            request_date=datetime.date.today(),
                                                            justified_at=datetime.date.today(),
                                                            justification=validated_data.get('justification'),
                                                            justified_by=updated_by,
                                                            leave_type=validated_data.get('leave_type')
                                                            )

                                                        return validated_data
                                            elif request_type == 'FD' and total_paid_leave['cl_balance']>0.5:
                                                justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                    update(
                                                    request_type=request_type,
                                                    is_requested=True,
                                                    approved_status='pending',
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                                return validated_data
                                            else:
                                                custom_exception_message(self,None,"Not enough casual leave balance")
                                        else:
                                            # raise serializers.ValidationError("casual leave limit exceeds")
                                            custom_exception_message(self,None,"casual leave limit exceeds")
                                    elif leave_type == 'EL':
                                        if total_paid_leave['el_balance']>0.0:
                                            duration_length=AttendanceApprovalRequest.objects.get(id=instance.id,checkin_benchmark=False,is_requested=False)
                                            if request_type == 'HD':
                                                if duration_length.duration <=240:
                                                    justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                            update(
                                                            request_type=request_type,
                                                            is_requested=True,
                                                            approved_status='pending',
                                                            request_date=datetime.date.today(),
                                                            justified_at=datetime.date.today(),
                                                            justification=validated_data.get('justification'),
                                                            justified_by=updated_by,
                                                            leave_type=validated_data.get('leave_type')
                                                            )

                                                    return validated_data
                                                elif duration_length.duration > 240:
                                                    if (duration_start_end.duration_start.time() and duration_start_end.duration_end.time()) < worst_late_beanchmark:
                                                        # custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                                        justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                            update(
                                                            request_type=request_type,
                                                            is_requested=True,
                                                            approved_status='pending',
                                                            request_date=datetime.date.today(),
                                                            justified_at=datetime.date.today(),
                                                            justification=validated_data.get('justification'),
                                                            justified_by=updated_by,
                                                            leave_type=validated_data.get('leave_type')
                                                            )

                                                        return validated_data
                                                    elif duration_start_end.duration_start.time() < worst_late_beanchmark and duration_start_end.duration_end.time() > worst_late_beanchmark:
                                                        custom_exception_message(self,None,"Please apply full day Your diviation exceeds 4 Hours")
                                                    elif (duration_start_end.duration_start.time() and duration_start_end.duration_end.time()) > worst_late_beanchmark:
                                                        # custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                                        justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                            update(
                                                            request_type=request_type,
                                                            is_requested=True,
                                                            approved_status='pending',
                                                            request_date=datetime.date.today(),
                                                            justified_at=datetime.date.today(),
                                                            justification=validated_data.get('justification'),
                                                            justified_by=updated_by,
                                                            leave_type=validated_data.get('leave_type')
                                                            )

                                                        return validated_data
                                            
                                            elif request_type == 'FD' and total_paid_leave['el_balance']>0.5:
                                                justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                    update(
                                                    request_type=request_type,
                                                    is_requested=True,
                                                    approved_status='pending',
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                                return validated_data
                                            else:
                                                custom_exception_message(self,None,"Not enough earn leave balance")
                                        else:
                                            # raise serializers.ValidationError("Earned leave limit exceeds")
                                            custom_exception_message(self,None,"Earned leave limit exceeds")
                                            
                                    elif leave_type == 'AB':
                                        justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                    update(
                                                    request_type=request_type,
                                                    is_requested=True,
                                                    approved_status='pending',
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                        return validated_data
                            else:
                                total_paid_leave['granted_cl']=core_user_detail[0]['granted_cl']
                                total_paid_leave['cl_balance']=float(core_user_detail[0]['granted_cl']) - float(availed_cl_data)
                                total_paid_leave['granted_el']=core_user_detail[0]['granted_el']
                                total_paid_leave['el_balance']=float(core_user_detail[0]['granted_el']) - float(availed_el_data)
                                total_paid_leave['granted_sl']=core_user_detail[0]['granted_sl']
                                total_paid_leave['sl_balance']=float(core_user_detail[0]['granted_sl']) - float(availed_sl_data)
                                total_paid_leave['total_granted_leave']=float(core_user_detail[0]['granted_cl']) + float(core_user_detail[0]['granted_el']) + float(core_user_detail[0]['granted_sl'])
                                total_paid_leave['total_leave_balances']=float(total_paid_leave['total_granted_leave']) - float(total_paid_leave['total_availed_leave'])
                                print("total_paid_leave",total_paid_leave)
                                #**********HALF DAY OR FULL DAY LEAVE CALCULATION Regular *************************
                                if request_type == 'HD' or request_type == 'FD':
                                    if  leave_type == 'SL' :
                                        
                                        if total_paid_leave['sl_balance']>0.0:
                                            duration_length=AttendanceApprovalRequest.objects.get(id=instance.id,checkin_benchmark=False,is_requested=False)
                                            if request_type == 'HD':
                                                if duration_length.duration <=240 :
                                                    # raise serializers.ValidationError("Please apply half day Your diviation exceeds 2.5 Hours")
                                            
                                                    justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                            update(
                                                            request_type=request_type,
                                                            is_requested=True,
                                                            approved_status='pending',
                                                            request_date=datetime.date.today(),
                                                            justified_at=datetime.date.today(),
                                                            justification=validated_data.get('justification'),
                                                            justified_by=updated_by,
                                                            leave_type=validated_data.get('leave_type')
                                                            )

                                                    return validated_data

                                                elif duration_length.duration > 240 :
                                                    if (duration_start_end.duration_start.time() and duration_start_end.duration_end.time()) < worst_late_beanchmark:
                                                        # custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                                        justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                            update(
                                                            request_type=request_type,
                                                            is_requested=True,
                                                            approved_status='pending',
                                                            request_date=datetime.date.today(),
                                                            justified_at=datetime.date.today(),
                                                            justification=validated_data.get('justification'),
                                                            justified_by=updated_by,
                                                            leave_type=validated_data.get('leave_type')
                                                            )

                                                        return validated_data
                                                    elif duration_start_end.duration_start.time() < worst_late_beanchmark and duration_start_end.duration_end.time() > worst_late_beanchmark:
                                                        custom_exception_message(self,None,"Please apply full day Your diviation exceeds 4 Hours")
                                                    elif (duration_start_end.duration_start.time() and duration_start_end.duration_end.time()) > worst_late_beanchmark:
                                                        # custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                                        justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                            update(
                                                            request_type=request_type,
                                                            is_requested=True,
                                                            approved_status='pending',
                                                            request_date=datetime.date.today(),
                                                            justified_at=datetime.date.today(),
                                                            justification=validated_data.get('justification'),
                                                            justified_by=updated_by,
                                                            leave_type=validated_data.get('leave_type')
                                                            )

                                                        return validated_data
                                            elif request_type == 'FD' and total_paid_leave['sl_balance']>0.5:
                                                justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                    update(
                                                    request_type=request_type,
                                                    is_requested=True,
                                                    approved_status='pending',
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )
                                                return validated_data
                                            else:
                                                custom_exception_message(self,None,"Not enough sick leave balance")
                                                
                                        else:
                                            # raise serializers.ValidationError("Sick leave limit exceeds")
                                            custom_exception_message(self,None,"Sick leave limit exceeds")
                                            
                                    elif leave_type =='CL':
                                        if total_paid_leave['cl_balance']>0.0:
                                            duration_length=AttendanceApprovalRequest.objects.get(id=instance.id,checkin_benchmark=False,is_requested=False)
                                            if request_type == 'HD':
                                                if  duration_length.duration <=240:
                                                    justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,is_late_conveyance=False,checkin_benchmark=False,is_requested=False).\
                                                            update(
                                                            request_type=request_type,
                                                            is_requested=True,
                                                            approved_status='pending',
                                                            request_date=datetime.date.today(),
                                                            justified_at=datetime.date.today(),
                                                            justification=validated_data.get('justification'),
                                                            justified_by=updated_by,
                                                            leave_type=validated_data.get('leave_type')
                                                            )

                                                    return validated_data
                                                
                                                elif duration_length.duration > 240 :
                                                    if (duration_start_end.duration_start.time() and duration_start_end.duration_end.time()) < worst_late_beanchmark:
                                                        # custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                                        justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                            update(
                                                            request_type=request_type,
                                                            is_requested=True,
                                                            approved_status='pending',
                                                            request_date=datetime.date.today(),
                                                            justified_at=datetime.date.today(),
                                                            justification=validated_data.get('justification'),
                                                            justified_by=updated_by,
                                                            leave_type=validated_data.get('leave_type')
                                                            )

                                                        return validated_data
                                                    elif duration_start_end.duration_start.time() < worst_late_beanchmark and duration_start_end.duration_end.time() > worst_late_beanchmark:
                                                        custom_exception_message(self,None,"Please apply full day Your diviation exceeds 4 Hours")
                                                    elif (duration_start_end.duration_start.time() and duration_start_end.duration_end.time()) > worst_late_beanchmark:
                                                        # custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                                        justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                            update(
                                                            request_type=request_type,
                                                            is_requested=True,
                                                            approved_status='pending',
                                                            request_date=datetime.date.today(),
                                                            justified_at=datetime.date.today(),
                                                            justification=validated_data.get('justification'),
                                                            justified_by=updated_by,
                                                            leave_type=validated_data.get('leave_type')
                                                            )

                                                        return validated_data
                                            elif request_type == 'FD' and total_paid_leave['cl_balance']>0.5:
                                                justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                    update(
                                                    request_type=request_type,
                                                    is_requested=True,
                                                    approved_status='pending',
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                                return validated_data
                                            else:
                                                custom_exception_message(self,None,"Not enough casual leave balance")
                                        else:
                                            # raise serializers.ValidationError("casual leave limit exceeds")
                                            custom_exception_message(self,None,"casual leave limit exceeds")
                                    elif leave_type =='EL':
                                        if total_paid_leave['el_balance']>0.0:
                                            duration_length=AttendanceApprovalRequest.objects.get(id=instance.id,checkin_benchmark=False,is_requested=False)
                                            if request_type == 'HD':
                                                if  duration_length.duration <=240:
                                                    justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                            update(
                                                            request_type=request_type,
                                                            is_requested=True,
                                                            approved_status='pending',
                                                            request_date=datetime.date.today(),
                                                            justified_at=datetime.date.today(),
                                                            justification=validated_data.get('justification'),
                                                            justified_by=updated_by,
                                                            leave_type=validated_data.get('leave_type')
                                                            )

                                                    return validated_data
                                                elif duration_length.duration > 240:
                                                    if (duration_start_end.duration_start.time() and duration_start_end.duration_end.time()) < worst_late_beanchmark:
                                                        # custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                                        justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                            update(
                                                            request_type=request_type,
                                                            is_requested=True,
                                                            approved_status='pending',
                                                            request_date=datetime.date.today(),
                                                            justified_at=datetime.date.today(),
                                                            justification=validated_data.get('justification'),
                                                            justified_by=updated_by,
                                                            leave_type=validated_data.get('leave_type')
                                                            )

                                                        return validated_data
                                                    elif duration_start_end.duration_start.time() < worst_late_beanchmark and duration_start_end.duration_end.time() > worst_late_beanchmark:
                                                        custom_exception_message(self,None,"Please apply full day Your diviation exceeds 4 Hours")
                                                    elif (duration_start_end.duration_start.time() and duration_start_end.duration_end.time()) > worst_late_beanchmark:
                                                        # custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                                        justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                            update(
                                                            request_type=request_type,
                                                            is_requested=True,
                                                            approved_status='pending',
                                                            request_date=datetime.date.today(),
                                                            justified_at=datetime.date.today(),
                                                            justification=validated_data.get('justification'),
                                                            justified_by=updated_by,
                                                            leave_type=validated_data.get('leave_type')
                                                            )

                                                        return validated_data
                                            
                                            elif request_type == 'FD' and total_paid_leave['el_balance']>0.5:
                                                justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                    update(
                                                    request_type=request_type,
                                                    is_requested=True,
                                                    approved_status='pending',
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                                return validated_data
                                        else:
                                            # raise serializers.ValidationError("Earned leave limit exceeds")
                                            custom_exception_message(self,None,"Earned leave limit exceeds")
                                    elif leave_type == 'AB':
                                        justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                    update(
                                                    request_type=request_type,
                                                    is_requested=True,
                                                    approved_status='pending',
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                        return validated_data
                    
                    
                    
                    elif request_type == 'OD':          
                        vehicle_type= validated_data.get('vehicle_type') if validated_data.get('vehicle_type') else None
                        from_place= validated_data.get('from_place') if validated_data.get('from_place') else None
                        to_place= validated_data.get('to_place') if validated_data.get('to_place') else None
                        conveyance_expense= validated_data.get('conveyance_expense') if validated_data.get('conveyance_expense') else 0.0
                        conveyance_remarks= validated_data.get('conveyance_remarks') if validated_data.get('conveyance_remarks') else None
                        conveyance_alloted_by= validated_data.get('conveyance_alloted_by') if validated_data.get('conveyance_alloted_by') else None

                        if from_place or to_place or conveyance_remarks:
                            justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,is_requested=False).\
                                update(
                                request_type='FOD',
                                is_requested=True,
                                approved_status='pending',
                                request_date=datetime.date.today(),
                                justified_at=datetime.date.today(),
                                justification=validated_data.get('justification'),
                                justified_by=updated_by,
                                is_conveyance=True,
                                vehicle_type_id=vehicle_type,
                                from_place=from_place,
                                to_place=to_place,
                                conveyance_alloted_by_id=conveyance_alloted_by,
                                conveyance_expense=conveyance_expense,
                                conveyance_remarks=conveyance_remarks
                                )

                            return validated_data
                        else:
                            justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                update(
                                request_type='FOD',
                                is_requested=True,
                                approved_status='pending',
                                request_date=datetime.date.today(),
                                justified_at=datetime.date.today(),
                                justification=validated_data.get('justification'),
                                justified_by=updated_by,
                                is_conveyance=False,
                                )
                            data=AttendanceApprovalRequest.objects.get(id=instance.id)

                            return validated_data
                    
                    
                    
                    #*****************Request for mispunch************************************************************************************
                    elif request_type == 'MP': 
                        justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                update(
                                request_type=request_type,
                                is_requested=True,
                                approved_status='pending',
                                request_date=datetime.date.today(),
                                justified_at=datetime.date.today(),
                                justification=validated_data.get('justification'),
                                justified_by=updated_by)

                        return validated_data
                    
                    return validated_data

        except Exception as e:
            raise e


class WorkFromHomeDeviationSerializerV2(serializers.ModelSerializer):

    class Meta:
        model = WorkFromHomeDeviation
        fields = ['start_date_time', 'end_date_time', 'work_done']


class AttendenceApprovalRequestEditSerializerV2(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    work_from_home = WorkFromHomeDeviationSerializerV2(many=True, required=False) # wfh

    ## Change Request Document__Attendance & HRMS (Conveyence Management) -CR-2 - V 1.2_Approved | Date: 23-06-2020 | Rupam Hazra ##
    #kilometers_travelled= serializers.CharField(required=False,allow_null=True) 
    conveyance = serializers.CharField(required=False)
    deviation_amount = serializers.CharField(required=False,allow_blank=True,allow_null=True)
    is_round = serializers.BooleanField(required=False)
    address  = serializers.ListField(required=False)

    class Meta:
        model = AttendanceApprovalRequest
        fields = ('__all__')
        extra_fields = ['work_from_home','conveyance','deviation_amount','is_round','address']

    def bench_15m_3days_check(self, instance=None, user=None):
        # instance.duration_end == instance.attendance.login_time or instance.duration_start == instance.attendance.logout_time 
        month_master = AttendenceMonthMaster.objects.filter(month_start__date__lte=instance.attendance_date,month_end__date__gte=instance.attendance_date).first()
        bench_15m_request = AttendanceApprovalRequest.objects.filter(
                                                        Q(attendance__employee=user.cu_user)&
                                                        Q(is_requested=True)&
                                                        Q(checkin_benchmark=False)&
                                                        Q(request_type='GR')&
                                                        Q(duration_start__date__gte=month_master.month_start.date())&
                                                        Q(duration_start__date__lt=instance.attendance_date)&
                                                        Q(is_deleted=False))
        print('bench_15m_request:',bench_15m_request)
        print('bench_15m_request count:',bench_15m_request.count())

        attendance_set = set()
        for attendance_request in bench_15m_request:
            attendance_set.add(attendance_request.attendance)
        print('attendance_set:', attendance_set)
        login_logout_requests = AttendanceApprovalRequest.objects.none()
        for attendance in attendance_set:
            login_logout_requests = login_logout_requests | bench_15m_request.filter(Q(attendance=attendance)&
                                                                                        Q(
                                                                                            Q(duration_end=attendance.login_time)|
                                                                                            Q(duration_start=attendance.logout_time)
                                                                                        )
                                                                                    )
        print('login_logout_requests:', login_logout_requests)
        
        
        return login_logout_requests.values('attendance').distinct().count()

    def work_from_home_time_calculation(self, work_from_home=None):
        total_deviation = 0
        for work_from_home_obj in work_from_home:
            total_deviation += (work_from_home_obj['end_date_time'] - work_from_home_obj['start_date_time']).seconds/60
        return total_deviation

    def insert_ConveyancePlacesMapping(self,address,conveyanceMaster,created_by):
        #amount = 0.0
        for each in address:
            each['conveyance'] = conveyanceMaster
            each['from_place'] = each['from_place']
            each['to_place'] = each['to_place']
            each['created_by'] = created_by
            each['vehicle_type_id'] = each['vehicle_type']
            each.pop('vehicle_type')
            each['amount'] = each['amount']
            each['place_deviation_amount'] = each['place_deviation_amount']
            each['kilometers_travelled'] = each['kilometers_travelled']
            ConveyancePlacesMapping.objects.create(**each)
            #amount = amount + float(each['conveyance_expense'])
            #deviation_amount = deviation_amount + float(each['deviation_amount'])
        return True

    def update(self,instance, validated_data):
        #print("validated_data",validated_data)
        updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
        
        try:
            updated_by = validated_data.get('updated_by')
            address  = validated_data.pop('address')
            date =self.context['request'].query_params.get('date', None)
            #print('date',type(date))
            #################################################################################
            #if you find error in datetime please remove only datetime from "date_object"   #
            #################################################################################
            date_object = datetime.datetime.strptime(date, '%Y-%m-%d').date()
            #print('date_object',type(date_object))
            employee_id=self.context['request'].query_params.get('employee_id', None)
            total_grace={}
            data_dict = {}
            with transaction.atomic():
                request_type=validated_data.get('request_type') if validated_data.get('request_type') else ""
                #print('request_type',request_type)

                present=AttendanceApprovalRequest.objects.filter(id=instance.id,attendance__is_present=True)



                total_month_grace=AttendenceMonthMaster.objects.filter(month_start__date__lte=date_object,
                                                    month_end__date__gte=date_object,is_deleted=False).values('grace_available',
                                                                                            'year_start_date',
                                                                                            'year_end_date',
                                                                                            'month',
                                                                                            'month_start',
                                                                                            'month_end'
                                                                                            )

                #REQUEST ONLY IF PRESENT AND HAVE DIVIATION
                availed_grace_daily = 0.0
                if present:
                    availed_grace=AttendanceApprovalRequest.objects.filter(Q(attendance__employee=employee_id) &
                                                            Q(duration_start__gte=total_month_grace[0]['month_start']) &
                                                            Q(duration_start__lte=total_month_grace[0]['month_end']) &
                                                            Q(is_requested=True) &
                                                            Q(is_deleted=False)&
                                                            (Q(request_type='GR')|Q(checkin_benchmark=True))
                                                            ).aggregate(Sum('duration'))['duration__sum']

                    availed_grace_daily=AttendanceApprovalRequest.objects.filter(Q(attendance__employee=employee_id) &
                                                            Q(duration_start__date=instance.duration_start.date()) &
                                                            Q(is_requested=True) &
                                                            Q(is_deleted=False)&
                                                            (Q(request_type='GR')|Q(checkin_benchmark=True))
                                                            ).aggregate(Sum('duration'))['duration__sum']
                    
                    if request_type == 'GR':
                        availed_grace_daily = availed_grace_daily if availed_grace_daily else 0.0
                        available_daily_grace = 60 - availed_grace_daily
                        tcore_user = TCoreUserDetail.objects.get(cu_user=employee_id)
                        worst_late_beanchmark = tcore_user.worst_late
                        print("worst_late_beanchmark", worst_late_beanchmark)

                        duration_start_end = AttendanceApprovalRequest.objects.get(id=instance.id)
                        print("duration_start_end", duration_start_end)
                        core_user_detail = TCoreUserDetail.objects.filter(cu_user=employee_id,
                                                                          cu_is_deleted=False).values('joining_date')
                        print('core_user_detail', core_user_detail)
                        if core_user_detail:
                            if core_user_detail[0]['joining_date'] > total_month_grace[0]['year_start_date']:
                                '''
                                TODO :: In v2 attendance, there is no cl/el/sl, only total_granted_leaves applicable.
                                '''
                                joining_grace = JoiningApprovedLeave.objects.filter(employee=employee_id,
                                        is_deleted=False).values('year', 'month', 'first_grace')
                                print('joining_grace:', joining_grace)
                                if total_month_grace[0]['month'] == joining_grace[0]['month']:  # for joining month only
                                    total_grace['total_month_grace'] = joining_grace[0]['first_grace']
                                    total_grace['month_start'] = core_user_detail[0]['joining_date']

                                    duration_length = AttendanceApprovalRequest.objects.get(id=instance.id,
                                                                                            is_requested=False)
                                    print('availed_grace', availed_grace)
                                    print('availed_grace_daily', availed_grace_daily)
                                    # if duration_length.duration < 240:
                                    '''
                                    TODO :: 180 min/day grace applicable in v2. ( 150 min/day was in previous version )
                                    '''
                                    if duration_length.duration <= 60 and available_daily_grace >= duration_length.duration:
                                        # total_grace['grace_balance']=total_grace['total_month_grace'] - availed_grace
                                        if availed_grace is None:
                                            availed_grace = 0.0
                                        print('balance', (total_grace['total_month_grace'] - (float(availed_grace) + float(duration_length.duration))))
                                        if (total_grace['total_month_grace'] - (float(availed_grace) + float(duration_length.duration))) >= 0.0:

                                            justify_attendence = AttendanceApprovalRequest.objects.filter(
                                                id=instance.id, is_requested=False). \
                                                update(
                                                request_type=request_type,
                                                is_requested=True,
                                                approved_status='pending',
                                                request_date=datetime.date.today(),
                                                justified_at=datetime.date.today(),
                                                justification=validated_data.get('justification'),
                                                justified_by=updated_by)

                                            return validated_data
                                        else:
                                            # raise serializers.ValidationError("Grace limit exceeds")
                                            custom_exception_message(self, None, "Grace limit exceeds")
                                    else:
                                        # raise serializers.ValidationError("Please apply half day Your diviation exceeds 2.5 Hours")
                                        custom_exception_message(self, None,
                                                                 "Grace is not applicable for this deviation")

                                else:
                                    total_grace['total_month_grace'] = float(
                                        total_month_grace[0]['grace_available']) if float(
                                        total_month_grace[0]['grace_available']) else 0.0
                                    duration_length = AttendanceApprovalRequest.objects.get(id=instance.id,
                                                                                            is_requested=False)
                                    # print('availed_grace12333',availed_grace)
                                    '''
                                    TODO :: less than 180 min/day grace applicable in v2. ( 150 min/day was in previous version )
                                    '''
                                    if duration_length.duration <= 60 and available_daily_grace >= duration_length.duration:
                                        # total_grace['grace_balance']=total_grace['total_month_grace'] - availed_grace
                                        if availed_grace is None:
                                            availed_grace = 0.0
                                        if (total_grace['total_month_grace'] - (
                                                float(availed_grace) + float(duration_length.duration))) >= 0.0:

                                            justify_attendence = AttendanceApprovalRequest.objects.filter(
                                                id=instance.id, is_requested=False). \
                                                update(
                                                request_type=request_type,
                                                is_requested=True,
                                                approved_status='pending',
                                                request_date=datetime.date.today(),
                                                justified_at=datetime.date.today(),
                                                justification=validated_data.get('justification'),
                                                justified_by=updated_by)

                                            return validated_data
                                        else:
                                            # raise serializers.ValidationError("Grace limit exceeds")
                                            custom_exception_message(self, None, "Grace limit exceeds")
                                    else:
                                        # raise serializers.ValidationError("Please apply half day Your diviation exceeds 2.5 Hours")
                                        custom_exception_message(self, None,
                                                                 "Grace is not applicable for this deviation")

                            else:
                                total_grace['total_month_grace'] = float(
                                    total_month_grace[0]['grace_available']) if float(
                                    total_month_grace[0]['grace_available']) else 0.0
                                duration_length = AttendanceApprovalRequest.objects.get(id=instance.id,
                                                                                        is_requested=False)
                                print('availed_grace', availed_grace)
                                print('availed_grace_daily', availed_grace_daily)
                                '''
                                TODO :: 180 min/day grace applicable in v2. ( 150 min/day was in previous version )
                                '''

                                if duration_length.duration <= 60 and available_daily_grace >= duration_length.duration:
                                    # total_grace['grace_balance']=total_grace['total_month_grace'] - availed_grace
                                    if availed_grace is None:
                                        availed_grace = 0.0
                                    # print('total_grace',total_grace['total_month_grace'],availed_grace)
                                    print('total_month_grace', total_grace['total_month_grace'])
                                    print('duration_length.duration', duration_length.duration)
                                    if (total_grace['total_month_grace'] - (
                                            float(availed_grace) + float(duration_length.duration))) >= 0.0:

                                        justify_attendence = AttendanceApprovalRequest.objects.filter(
                                            id=instance.id, is_requested=False). \
                                            update(
                                            request_type=request_type,
                                            is_requested=True,
                                            approved_status='pending',
                                            request_date=datetime.date.today(),
                                            justified_at=datetime.date.today(),
                                            justification=validated_data.get('justification'),
                                            justified_by=updated_by)

                                        return validated_data
                                    else:
                                        # raise serializers.ValidationError("Grace limit exceeds")
                                        custom_exception_message(self, None, "Grace limit exceeds")
                                else:
                                    # raise serializers.ValidationError("Please apply half day Your diviation exceeds 2.5 Hours")
                                    custom_exception_message(self, None,
                                                             "Grace is not applicable for this deviation")


                    #*****************present but user want to give HD or FD request*********************************************************
                    elif request_type == 'HD' or request_type == 'FD':
                        tcore_user = TCoreUserDetail.objects.get(cu_user=employee_id)
                        worst_late_beanchmark = tcore_user.worst_late

                        advance_leave_calculation = advance_leave_calculation_excluding_current_month(tcore_user=tcore_user, date_object=date_object)
                        #print('advance_leave_calculation', advance_leave_calculation)
                        
                        leave_type=validated_data.get('leave_type')

                        
                        

                        if leave_type in ('CL','SL','EL'):
                            
                            result = all_leave_calculation_upto_applied_date(date_object=date_object, user=tcore_user)
                            balance_el = result['el_balance']
                            balance_sl = result['sl_balance']
                            balance_cl = result['cl_balance']
                            #leave_allocation_per_month = result['total_accumulation']
                            #print('balance_el',balance_el)
                            #print('balance_sl',balance_sl)
                            #print('balance_cl',balance_cl)
                            #raise APIException({'sdsds':'sdsds'})

                            if  leave_type == 'SL' :
                                if balance_sl>0.0:
                                    duration_length=AttendanceApprovalRequest.objects.get(id=instance.id,checkin_benchmark=False,is_requested=False)
                                    if request_type == 'HD':
                                        if duration_length.duration <=240 :
                                            # raise serializers.ValidationError("Please apply half day Your diviation exceeds 2.5 Hours")
                                    
                                            justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                    update(
                                                    request_type=request_type,
                                                    is_requested=True,
                                                    approved_status='pending',
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                            return validated_data

                                        elif duration_length.duration > 240 :
                                            if (duration_start_end.duration_start.time() and duration_start_end.duration_end.time()) < worst_late_beanchmark:
                                                # custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                                justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                    update(
                                                    request_type=request_type,
                                                    is_requested=True,
                                                    approved_status='pending',
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                                return validated_data
                                            elif duration_start_end.duration_start.time() < worst_late_beanchmark and duration_start_end.duration_end.time() > worst_late_beanchmark:
                                                custom_exception_message(self,None,"Please apply full day Your diviation exceeds 4 Hours")
                                            elif (duration_start_end.duration_start.time() and duration_start_end.duration_end.time()) > worst_late_beanchmark:
                                                # custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                                justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                    update(
                                                    request_type=request_type,
                                                    is_requested=True,
                                                    approved_status='pending',
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                                return validated_data
                                    elif request_type == 'FD' and balance_sl>0.5:
                                        justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                            update(
                                            request_type=request_type,
                                            is_requested=True,
                                            approved_status='pending',
                                            request_date=datetime.date.today(),
                                            justified_at=datetime.date.today(),
                                            justification=validated_data.get('justification'),
                                            justified_by=updated_by,
                                            leave_type=validated_data.get('leave_type')
                                            )

                                        return validated_data
                                    else:
                                        custom_exception_message(self,None,"Not enough sick leave balance")
                                else:
                                    custom_exception_message(self,None,"Sick leave limit exceeds")

                            elif leave_type =='CL':

                                if balance_cl>0.0:
                                    actual_balance = balance_cl + advance_leave_calculation['advance_leave_balance_cl']
                                    is_balance_available = actual_balance > 0
                                    
                                    if advance_leave_calculation['is_advance_leave_taken_cl'] and advance_leave_calculation['is_leave_taken_from_current_month_cl'] and not is_balance_available:
                                        custom_exception_message(self,None,"Not enough leave balance. Your current month leave has been adjusted with advance leave.")
                                    
                                    duration_length=AttendanceApprovalRequest.objects.get(id=instance.id,checkin_benchmark=False,is_requested=False)
                                    if request_type == 'HD':
                                        if duration_length.duration <=240:
                                            justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,is_late_conveyance=False,checkin_benchmark=False,is_requested=False).\
                                                    update(
                                                    request_type=request_type,
                                                    is_requested=True,
                                                    approved_status='pending',
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                            return validated_data
                                        
                                        elif duration_length.duration > 240 :
                                            if (duration_start_end.duration_start.time() and duration_start_end.duration_end.time()) < worst_late_beanchmark:
                                                # custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                                justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                    update(
                                                    request_type=request_type,
                                                    is_requested=True,
                                                    approved_status='pending',
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                                return validated_data
                                            elif duration_start_end.duration_start.time() < worst_late_beanchmark and duration_start_end.duration_end.time() > worst_late_beanchmark:
                                                custom_exception_message(self,None,"Please apply full day Your diviation exceeds 4 Hours")
                                            elif (duration_start_end.duration_start.time() and duration_start_end.duration_end.time()) > worst_late_beanchmark:
                                                # custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                                justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                    update(
                                                    request_type=request_type,
                                                    is_requested=True,
                                                    approved_status='pending',
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                                return validated_data
                                    elif request_type == 'FD' and balance_cl>0.5:
                                        justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                            update(
                                            request_type=request_type,
                                            is_requested=True,
                                            approved_status='pending',
                                            request_date=datetime.date.today(),
                                            justified_at=datetime.date.today(),
                                            justification=validated_data.get('justification'),
                                            justified_by=updated_by,
                                            leave_type=validated_data.get('leave_type')
                                            )

                                        return validated_data
                                    else:
                                        custom_exception_message(self,None,"Not enough casual leave balance")
                                else:
                                    # raise serializers.ValidationError("casual leave limit exceeds")
                                    custom_exception_message(self,None,"Casual leave limit exceeds")
                            
                            elif leave_type == 'EL':
                                if balance_el>0.0:
                                    actual_balance = balance_el + advance_leave_calculation['advance_leave_balance_el']
                                    is_balance_available = actual_balance > 0
                                    
                                    if advance_leave_calculation['is_advance_leave_taken_el'] and advance_leave_calculation['is_leave_taken_from_current_month_el'] and not is_balance_available:
                                        custom_exception_message(self,None,"Not enough leave balance. Your current month leave has been adjusted with advance leave.")

                                    duration_length=AttendanceApprovalRequest.objects.get(id=instance.id,checkin_benchmark=False,is_requested=False)
                                    if request_type == 'HD':
                                        if duration_length.duration <=240:
                                            justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                    update(
                                                    request_type=request_type,
                                                    is_requested=True,
                                                    approved_status='pending',
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                            return validated_data
                                        elif duration_length.duration > 240:
                                            if (duration_start_end.duration_start.time() and duration_start_end.duration_end.time()) < worst_late_beanchmark:
                                                # custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                                justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                    update(
                                                    request_type=request_type,
                                                    is_requested=True,
                                                    approved_status='pending',
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                                return validated_data
                                            elif duration_start_end.duration_start.time() < worst_late_beanchmark and duration_start_end.duration_end.time() > worst_late_beanchmark:
                                                custom_exception_message(self,None,"Please apply full day Your diviation exceeds 4 Hours")
                                            elif (duration_start_end.duration_start.time() and duration_start_end.duration_end.time()) > worst_late_beanchmark:
                                                # custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                                justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                    update(
                                                    request_type=request_type,
                                                    is_requested=True,
                                                    approved_status='pending',
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                                return validated_data
                                    
                                    elif request_type == 'FD' and balance_el>0.5:
                                        justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                            update(
                                            request_type=request_type,
                                            is_requested=True,
                                            approved_status='pending',
                                            request_date=datetime.date.today(),
                                            justified_at=datetime.date.today(),
                                            justification=validated_data.get('justification'),
                                            justified_by=updated_by,
                                            leave_type=validated_data.get('leave_type')
                                            )

                                        return validated_data
                                    else:
                                        custom_exception_message(self,None,"Not enough earn leave balance")
                                else:
                                    # raise serializers.ValidationError("Earned leave limit exceeds")
                                    custom_exception_message(self,None,"Earned leave limit exceeds")

                        elif leave_type in ('AL'):
                            result = all_leave_calculation_upto_applied_date(date_object=date_object, user=tcore_user)
                            balance_al = result['total_available_balance']
                            total_availed_al = result['total_consumption']
                            leave_allocation_per_month = result['total_accumulation']

                            # print('balance_al', balance_al)
                            # print('total_availed_al', total_availed_al)
                            # print('leave_allocation_per_month', leave_allocation_per_month)

                            

                            #balance_al, total_availed_al, leave_allocation_per_month = self.all_leave_calculation_upto_applied_date(date_object=date_object, user=tcore_user)
                            if balance_al>0.0:
                                actual_balance = balance_al + advance_leave_calculation['advance_leave_balance']
                                is_balance_available = actual_balance > 0
                                if advance_leave_calculation['is_advance_leave_taken'] and advance_leave_calculation['is_leave_taken_from_current_month'] and not is_balance_available:
                                    custom_exception_message(self,None,"Not enough leave balance. Your current month leave has been adjusted with advance leave.")
                                else:
                                    duration_length=AttendanceApprovalRequest.objects.get(id=instance.id,checkin_benchmark=False,is_requested=False)
                                    if request_type == 'HD':
                                        if duration_length.duration <=240:
                                            justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,is_late_conveyance=False,checkin_benchmark=False,is_requested=False).\
                                                    update(
                                                    request_type=request_type,
                                                    is_requested=True,
                                                    approved_status='pending',
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                            return validated_data
                                        
                                        elif duration_length.duration > 240 :
                                            if (instance.duration_start.time() and instance.duration_end.time()) < worst_late_beanchmark:
                                                # custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                                justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                    update(
                                                    request_type=request_type,
                                                    is_requested=True,
                                                    approved_status='pending',
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                                return validated_data
                                            
                                            elif instance.duration_start.time() < worst_late_beanchmark and instance.duration_end.time() > worst_late_beanchmark:
                                                custom_exception_message(self,None,"Please apply full day Your diviation exceeds 4 Hours")
                                            
                                            elif (instance.duration_start.time() and instance.duration_end.time()) > worst_late_beanchmark:
                                                # custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                                justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                    update(
                                                    request_type=request_type,
                                                    is_requested=True,
                                                    approved_status='pending',
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                                return validated_data
                                    elif request_type == 'FD' and balance_al>0.5:
                                        if actual_balance > 0.5:
                                            justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                update(
                                                request_type=request_type,
                                                is_requested=True,
                                                approved_status='pending',
                                                request_date=datetime.date.today(),
                                                justified_at=datetime.date.today(),
                                                justification=validated_data.get('justification'),
                                                justified_by=updated_by,
                                                leave_type=validated_data.get('leave_type')
                                                )

                                            return validated_data
                                        else:
                                            custom_exception_message(self,None,"Not enough leave balance. Your current month leave has been adjusted with advance leave.")
                                    else:
                                        custom_exception_message(self,None,"Not enough leave balance")
                            else:
                                # raise serializers.ValidationError("casual leave limit exceeds")
                                custom_exception_message(self,None,"leave limit exceeds")

                        elif leave_type == 'ML' or leave_type == 'BL':
                            justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                update(
                                request_type=request_type,
                                is_requested=True,
                                approved_status='approved',
                                request_date=datetime.date.today(),
                                justified_at=datetime.date.today(),
                                justification=validated_data.get('justification'),
                                justified_by=updated_by,
                                leave_type=validated_data.get('leave_type')
                                )

                            return validated_data

                        elif leave_type == 'AB':
                            justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                        update(
                                        request_type=request_type,
                                        is_requested=True,
                                        approved_status='pending',
                                        request_date=datetime.date.today(),
                                        justified_at=datetime.date.today(),
                                        justification=validated_data.get('justification'),
                                        justified_by=updated_by,
                                        leave_type=validated_data.get('leave_type')
                                        )

                            return validated_data
                    
                    #*****************As the user is already present hence partial OD********************************************************
                    elif request_type == 'OD':          
                        
                        #vehicle_type= validated_data.get('vehicle_type') if validated_data.get('vehicle_type') else None
                        #from_place= validated_data.get('from_place') if validated_data.get('from_place') else None
                        #to_place= validated_data.get('to_place') if validated_data.get('to_place') else None
                        conveyance_expense= validated_data.get('conveyance_expense') if validated_data.get('conveyance_expense') else 0.0
                        conveyance_remarks= validated_data.get('conveyance_purpose') if validated_data.get('conveyance_purpose') else None
                        conveyance_alloted_by= validated_data.get('conveyance_alloted_by') if validated_data.get('conveyance_alloted_by') else None
                        #kilometers_travelled= validated_data.get('kilometers_travelled') if validated_data.get('kilometers_travelled') else None
                        conveyance_purpose= validated_data.get('conveyance_purpose') if validated_data.get('conveyance_purpose') else None
                        deviation_amount = validated_data.get('deviation_amount') if validated_data.get('deviation_amount') else None
                        is_round = validated_data.get('is_round')
                        
                        #print(vehicle_type,from_place,to_place,conveyance_expense,conveyance_remarks,conveyance_alloted_by)
                        
                        if address or conveyance_remarks:
                            
                            ## Commented For Below Change Request | Rupam Hazra | Date : 07-07-2020 ##
                            justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,is_requested=False).\
                                update(
                                request_type='POD',
                                is_requested=True,
                                approved_status='pending',
                                request_date=datetime.date.today(),
                                justified_at=datetime.date.today(),
                                justification=validated_data.get('justification'),
                                justified_by=updated_by,
                                is_conveyance=True
                                )
                            #print("justify_attendence",justify_attendence)

                            # Conveyance
                            conveyance_apply = ConveyanceMaster.objects.create(
                                request_id = instance.id,
                                #from_place = from_place,
                                #to_place = to_place,
                                #vehicle_type = vehicle_type,
                                conveyance_purpose = conveyance_purpose,
                                conveyance_expense = conveyance_expense,
                                approved_expenses = conveyance_expense,
                                #kilometers_travelled=kilometers_travelled,
                                conveyance_alloted_by=conveyance_alloted_by,
                                created_by=updated_by,
                                deviation_amount=deviation_amount,
                                is_round=is_round
                                )

                            conveyance = ConveyanceMaster.objects.get(request_id=instance.id,is_deleted=False)
                            validated_data['conveyance'] = conveyance
                            self.insert_ConveyancePlacesMapping(address,conveyance_apply,updated_by)


                            

                            # recipient_email = conveyance.request.attendance.employee.cu_user.reporting_head.cu_user.cu_alt_email_id
                            # if recipient_email:
                            #     mail_data = {
                            #         "employee_name":conveyance.request.attendance.employee.get_full_name(),
                            #         "recipient_name": conveyance.request.attendance.employee.cu_user.reporting_head.get_full_name(),
                            #         "created_at": str(conveyance.request.attendance_date)[0:10],
                            #         "from_place": conveyance.from_place,
                            #         "to_place": conveyance.to_place,
                            #         "vehicle_type":conveyance.vehicle_type.name,
                            #         "expenses":conveyance.conveyance_expense
                            #         }
                            #     send_mail('AT-CA-N',recipient_email,mail_data)

                            ## End Change Request Document__Attendance & HRMS (Conveyence Management) -CR-2 - V 1.2_Approved | Date: 23-06-2020 | Rupam Hazra ##

                            return validated_data
                        else:
                            justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                update(
                                request_type='POD',
                                is_requested=True,
                                approved_status='pending',
                                request_date=datetime.date.today(),
                                justified_at=datetime.date.today(),
                                justification=validated_data.get('justification'),
                                justified_by=updated_by,
                                is_conveyance=False,
                                )

                            return validated_data
                    
                    #*****************Request for mispunch************************************************************************************
                    elif request_type == 'MP': 
                        justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                update(
                                request_type=request_type,
                                is_requested=True,
                                approved_status='pending',
                                request_date=datetime.date.today(),
                                justified_at=datetime.date.today(),
                                justification=validated_data.get('justification'),
                                justified_by=updated_by)

                        return validated_data

                    #********************Work from home request implementation*****************************************************************
                    elif request_type == 'WFH':
                        work_from_home_deviation = validated_data.get('work_from_home')
                        print('work_from_home_deviation:',work_from_home_deviation)
                        
                        total_deviation = 0
                        if work_from_home_deviation:
                            total_deviation = self.work_from_home_time_calculation(work_from_home=work_from_home_deviation)
                            print('total_deviation:', total_deviation)
                        else:
                            custom_exception_message(self,None, "Please fill up the work from home deviations.")
                            

                        if instance.duration > total_deviation:
                            custom_exception_message(self,None, "Please complete your working hours.")
                        else:
                            justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                update(
                                request_type=request_type,
                                is_requested=True,
                                approved_status='pending',
                                request_date=datetime.date.today(),
                                justified_at=datetime.date.today(),
                                justification=validated_data.get('justification'),
                                justified_by=updated_by)

                            for wfh_obj in work_from_home_deviation:
                                WorkFromHomeDeviation.objects.create(
                                    request=instance,
                                    start_date_time=wfh_obj['start_date_time'],
                                    end_date_time=wfh_obj['end_date_time'],
                                    work_done=wfh_obj['work_done'],
                                    created_by=updated_by,
                                    updated_by=updated_by
                                )
                            
                            return validated_data

                    return validated_data
                
                #REQUEST ONLY IF User ABSENT 
                else:

                    if request_type == 'HD' or request_type == 'FD':
                        tcore_user = TCoreUserDetail.objects.get(cu_user=employee_id)
                        worst_late_beanchmark = tcore_user.worst_late
                        leave_type=validated_data.get('leave_type')

                        advance_leave_calculation = advance_leave_calculation_excluding_current_month(tcore_user=tcore_user, date_object=date_object)
                        #print('advance_leave_calculation', advance_leave_calculation)
                        
                        

                        if leave_type in ('CL','SL','EL'):
                            
                            result = all_leave_calculation_upto_applied_date(date_object=date_object, user=tcore_user)
                            balance_el = result['el_balance']
                            balance_sl = result['sl_balance']
                            balance_cl = result['cl_balance']

                            if  leave_type == 'SL' :
                                if balance_sl>0.0:
                                    duration_length=AttendanceApprovalRequest.objects.get(id=instance.id,checkin_benchmark=False,is_requested=False)
                                    if request_type == 'HD':
                                        if duration_length.duration <=240 :
                                            # raise serializers.ValidationError("Please apply half day Your diviation exceeds 2.5 Hours")
                                    
                                            justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                    update(
                                                    request_type=request_type,
                                                    is_requested=True,
                                                    approved_status='pending',
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                            return validated_data

                                        elif duration_length.duration > 240 :
                                            if (duration_start_end.duration_start.time() and duration_start_end.duration_end.time()) < worst_late_beanchmark:
                                                # custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                                justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                    update(
                                                    request_type=request_type,
                                                    is_requested=True,
                                                    approved_status='pending',
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                                return validated_data
                                            elif duration_start_end.duration_start.time() < worst_late_beanchmark and duration_start_end.duration_end.time() > worst_late_beanchmark:
                                                custom_exception_message(self,None,"Please apply full day Your diviation exceeds 4 Hours")
                                            elif (duration_start_end.duration_start.time() and duration_start_end.duration_end.time()) > worst_late_beanchmark:
                                                # custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                                justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                    update(
                                                    request_type=request_type,
                                                    is_requested=True,
                                                    approved_status='pending',
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                                return validated_data
                                    elif request_type == 'FD' and balance_sl>0.5:
                                        justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                            update(
                                            request_type=request_type,
                                            is_requested=True,
                                            approved_status='pending',
                                            request_date=datetime.date.today(),
                                            justified_at=datetime.date.today(),
                                            justification=validated_data.get('justification'),
                                            justified_by=updated_by,
                                            leave_type=validated_data.get('leave_type')
                                            )

                                        return validated_data
                                    else:
                                        custom_exception_message(self,None,"Not enough sick leave balance")
                                else:
                                    # raise serializers.ValidationError("Sick leave limit exceeds")
                                    custom_exception_message(self,None,"Sick leave limit exceeds")

                            elif leave_type =='CL':

                                if balance_cl>0.0:
                                    actual_balance = balance_cl + advance_leave_calculation['advance_leave_balance_cl']
                                    is_balance_available = actual_balance > 0
                                    
                                    if advance_leave_calculation['is_advance_leave_taken_cl'] and advance_leave_calculation['is_leave_taken_from_current_month_cl'] and not is_balance_available:
                                        custom_exception_message(self,None,"Not enough leave balance. Your current month leave has been adjusted with advance leave.")
                                    
                                    duration_length=AttendanceApprovalRequest.objects.get(id=instance.id,checkin_benchmark=False,is_requested=False)
                                    if request_type == 'HD':
                                        if duration_length.duration <=240:
                                            justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,is_late_conveyance=False,checkin_benchmark=False,is_requested=False).\
                                                    update(
                                                    request_type=request_type,
                                                    is_requested=True,
                                                    approved_status='pending',
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                            return validated_data
                                        
                                        elif duration_length.duration > 240 :
                                            if (duration_start_end.duration_start.time() and duration_start_end.duration_end.time()) < worst_late_beanchmark:
                                                # custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                                justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                    update(
                                                    request_type=request_type,
                                                    is_requested=True,
                                                    approved_status='pending',
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                                return validated_data
                                            elif duration_start_end.duration_start.time() < worst_late_beanchmark and duration_start_end.duration_end.time() > worst_late_beanchmark:
                                                custom_exception_message(self,None,"Please apply full day Your diviation exceeds 4 Hours")
                                            elif (duration_start_end.duration_start.time() and duration_start_end.duration_end.time()) > worst_late_beanchmark:
                                                # custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                                justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                    update(
                                                    request_type=request_type,
                                                    is_requested=True,
                                                    approved_status='pending',
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                                return validated_data
                                    elif request_type == 'FD' and balance_cl>0.5:
                                        justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                            update(
                                            request_type=request_type,
                                            is_requested=True,
                                            approved_status='pending',
                                            request_date=datetime.date.today(),
                                            justified_at=datetime.date.today(),
                                            justification=validated_data.get('justification'),
                                            justified_by=updated_by,
                                            leave_type=validated_data.get('leave_type')
                                            )

                                        return validated_data
                                    else:
                                        custom_exception_message(self,None,"Not enough casual leave balance")
                                else:
                                    # raise serializers.ValidationError("casual leave limit exceeds")
                                    custom_exception_message(self,None,"Casual leave limit exceeds")
                            
                            elif leave_type == 'EL':
                                if balance_el>0.0:
                                    actual_balance = balance_el + advance_leave_calculation['advance_leave_balance_el']
                                    is_balance_available = actual_balance > 0
                                    
                                    if advance_leave_calculation['is_advance_leave_taken_el'] and advance_leave_calculation['is_leave_taken_from_current_month_el'] and not is_balance_available:
                                        custom_exception_message(self,None,"Not enough leave balance. Your current month leave has been adjusted with advance leave.")

                                    duration_length=AttendanceApprovalRequest.objects.get(id=instance.id,checkin_benchmark=False,is_requested=False)
                                    if request_type == 'HD':
                                        if duration_length.duration <=240:
                                            justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                    update(
                                                    request_type=request_type,
                                                    is_requested=True,
                                                    approved_status='pending',
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                            return validated_data
                                        elif duration_length.duration > 240:
                                            if (duration_start_end.duration_start.time() and duration_start_end.duration_end.time()) < worst_late_beanchmark:
                                                # custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                                justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                    update(
                                                    request_type=request_type,
                                                    is_requested=True,
                                                    approved_status='pending',
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                                return validated_data
                                            elif duration_start_end.duration_start.time() < worst_late_beanchmark and duration_start_end.duration_end.time() > worst_late_beanchmark:
                                                custom_exception_message(self,None,"Please apply full day Your diviation exceeds 4 Hours")
                                            elif (duration_start_end.duration_start.time() and duration_start_end.duration_end.time()) > worst_late_beanchmark:
                                                # custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                                justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                    update(
                                                    request_type=request_type,
                                                    is_requested=True,
                                                    approved_status='pending',
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                                return validated_data
                                    
                                    elif request_type == 'FD' and balance_el>0.5:
                                        justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                            update(
                                            request_type=request_type,
                                            is_requested=True,
                                            approved_status='pending',
                                            request_date=datetime.date.today(),
                                            justified_at=datetime.date.today(),
                                            justification=validated_data.get('justification'),
                                            justified_by=updated_by,
                                            leave_type=validated_data.get('leave_type')
                                            )

                                        return validated_data
                                    else:
                                        custom_exception_message(self,None,"Not enough earn leave balance")
                                else:
                                    # raise serializers.ValidationError("Earned leave limit exceeds")
                                    custom_exception_message(self,None,"Earned leave limit exceeds")


                        elif leave_type in ('AL'):

                            result = all_leave_calculation_upto_applied_date(date_object=date_object, user=tcore_user)
                            balance_al = result['total_available_balance']
                            total_availed_al = result['total_consumption']
                            leave_allocation_per_month = result['total_accumulation']

                            #balance_al, total_availed_al, leave_allocation_per_month = self.all_leave_calculation_upto_applied_date(date_object=date_object, user=tcore_user)
                            if balance_al>0.0:
                                actual_balance = balance_al + advance_leave_calculation['advance_leave_balance']
                                is_balance_available = actual_balance > 0
                                #print('is_balance_available', is_balance_available)
                                if advance_leave_calculation['is_advance_leave_taken'] and advance_leave_calculation['is_leave_taken_from_current_month'] and not is_balance_available:
                                    custom_exception_message(self,None,"Not enough leave balance. Your current month leave has been adjusted with advance leave.")
                                else:
                                    duration_length=AttendanceApprovalRequest.objects.get(id=instance.id,checkin_benchmark=False,is_requested=False)
                                    if request_type == 'HD':
                                        if duration_length.duration <=240:
                                            justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,is_late_conveyance=False,checkin_benchmark=False,is_requested=False).\
                                                    update(
                                                    request_type=request_type,
                                                    is_requested=True,
                                                    approved_status='pending',
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                            return validated_data
                                        
                                        elif duration_length.duration > 240 :
                                            if (instance.duration_start.time() and instance.duration_end.time()) < worst_late_beanchmark:
                                                # custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                                justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                    update(
                                                    request_type=request_type,
                                                    is_requested=True,
                                                    approved_status='pending',
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                                return validated_data
                                            elif instance.duration_start.time() < worst_late_beanchmark and instance.duration_end.time() > worst_late_beanchmark:
                                                custom_exception_message(self,None,"Please apply full day Your diviation exceeds 4 Hours")
                                            elif (instance.duration_start.time() and instance.duration_end.time()) > worst_late_beanchmark:
                                                # custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                                justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                    update(
                                                    request_type=request_type,
                                                    is_requested=True,
                                                    approved_status='pending',
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                                return validated_data
                                    elif request_type == 'FD' and balance_al>0.5:
                                        if actual_balance > 0.5:
                                            justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                update(
                                                request_type=request_type,
                                                is_requested=True,
                                                approved_status='pending',
                                                request_date=datetime.date.today(),
                                                justified_at=datetime.date.today(),
                                                justification=validated_data.get('justification'),
                                                justified_by=updated_by,
                                                leave_type=validated_data.get('leave_type')
                                                )

                                            return validated_data
                                        else:
                                            custom_exception_message(self,None,"Not enough leave balance. Your current month leave has been adjusted with advance leave.")
                                    else:
                                        custom_exception_message(self,None,"Not enough casual leave balance")
                            else:
                                # raise serializers.ValidationError("casual leave limit exceeds")
                                custom_exception_message(self,None,"leave limit exceeds")

                        elif leave_type == 'ML' or leave_type == 'BL':
                            justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                update(
                                request_type=request_type,
                                is_requested=True,
                                approved_status='pending',
                                request_date=datetime.date.today(),
                                justified_at=datetime.date.today(),
                                justification=validated_data.get('justification'),
                                justified_by=updated_by,
                                leave_type=validated_data.get('leave_type')
                                )

                            return validated_data

                        elif leave_type == 'AB':
                            justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                        update(
                                        request_type=request_type,
                                        is_requested=True,
                                        approved_status='pending',
                                        request_date=datetime.date.today(),
                                        justified_at=datetime.date.today(),
                                        justification=validated_data.get('justification'),
                                        justified_by=updated_by,
                                        leave_type=validated_data.get('leave_type')
                                        )

                            return validated_data


                    elif request_type == 'OD': 
                        #print('validated_data',validated_data)         
                        #vehicle_type= validated_data.get('vehicle_type') if validated_data.get('vehicle_type') else None
                        #from_place= validated_data.get('from_place') if validated_data.get('from_place') else None
                        #to_place= validated_data.get('to_place') if validated_data.get('to_place') else None
                        conveyance_expense= validated_data.get('conveyance_expense') if validated_data.get('conveyance_expense') else 0.0
                        conveyance_remarks= validated_data.get('conveyance_remarks') if validated_data.get('conveyance_remarks') else None
                        conveyance_alloted_by= validated_data.get('conveyance_alloted_by') if validated_data.get('conveyance_alloted_by') else None
                        #kilometers_travelled= validated_data.get('kilometers_travelled') if validated_data.get('kilometers_travelled') else None
                        conveyance_purpose= validated_data.get('conveyance_purpose') if validated_data.get('conveyance_purpose') else None
                        deviation_amount = validated_data.get('deviation_amount') if validated_data.get('deviation_amount') else None
                        is_round = validated_data.get('is_round')

                        if address or conveyance_remarks:

                            ## Commented For Below Change Request | Rupam Hazra | Date : 07-07-2020 ##

                            justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,is_requested=False).\
                                update(
                                request_type='POD',
                                is_requested=True,
                                approved_status='pending',
                                request_date=datetime.date.today(),
                                justified_at=datetime.date.today(),
                                justification=validated_data.get('justification'),
                                justified_by=updated_by,
                                is_conveyance=True
                                )
                            #print("justify_attendence",justify_attendence)

                            # Conveyance
                            conveyance_apply = ConveyanceMaster.objects.create(
                                request_id = instance.id,
                                #from_place = from_place,
                                #to_place = to_place,
                                #vehicle_type = vehicle_type,
                                conveyance_purpose = conveyance_purpose,
                                conveyance_expense = conveyance_expense,
                                approved_expenses = conveyance_expense,
                                #kilometers_travelled=kilometers_travelled,
                                conveyance_alloted_by=conveyance_alloted_by,
                                created_by=updated_by,
                                deviation_amount=deviation_amount,
                                is_round=is_round
                                )

                            conveyance = ConveyanceMaster.objects.get(request_id=instance.id,is_deleted=False)
                            validated_data['conveyance'] = conveyance
                            self.insert_ConveyancePlacesMapping(address,conveyance_apply,updated_by)


                            
                            # recipient_email = conveyance.request.attendance.employee.cu_user.reporting_head.cu_user.cu_alt_email_id
                            # if recipient_email:
                            #     mail_data = {
                            #         "employee_name":conveyance.request.attendance.employee.get_full_name(),
                            #         "recipient_name": conveyance.request.attendance.employee.cu_user.reporting_head.get_full_name(),
                            #         "created_at": str(conveyance.request.attendance_date)[0:10],
                            #         "from_place": conveyance.from_place,
                            #         "to_place": conveyance.to_place,
                            #         "vehicle_type":conveyance.vehicle_type.name,
                            #         "expenses":conveyance.conveyance_expense
                            #         }
                            #     send_mail('AT-CA-N',recipient_email,mail_data)

                            return validated_data

                        else:
                            justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                update(
                                request_type='FOD',
                                is_requested=True,
                                approved_status='pending',
                                request_date=datetime.date.today(),
                                justified_at=datetime.date.today(),
                                justification=validated_data.get('justification'),
                                justified_by=updated_by,
                                is_conveyance=False,
                                )
                            data=AttendanceApprovalRequest.objects.get(id=instance.id)

                            return validated_data
                    
                    #*****************Request for mispunch************************************************************************************
                    elif request_type == 'MP': 
                        justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                update(
                                request_type=request_type,
                                is_requested=True,
                                approved_status='pending',
                                request_date=datetime.date.today(),
                                justified_at=datetime.date.today(),
                                justification=validated_data.get('justification'),
                                justified_by=updated_by)

                        return validated_data
                    
                    #********************Work from home request implementation*****************************************************************

                    elif request_type == 'WFH':
                        work_from_home_deviation = validated_data.get('work_from_home')
                        #print('work_from_home_deviation:',work_from_home_deviation)                        
                        total_deviation = 0
                        if work_from_home_deviation:
                            total_deviation = self.work_from_home_time_calculation(work_from_home=work_from_home_deviation)
                            #print('total_deviation:', total_deviation)
                        else:
                            custom_exception_message(self,None, "Please fill up the work from home deviations.")
                            
                        if instance.duration > total_deviation:
                            custom_exception_message(self,None, "Please complete your working hours.")
                        else:
                            justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                update(
                                request_type=request_type,
                                is_requested=True,
                                approved_status='pending',
                                request_date=datetime.date.today(),
                                justified_at=datetime.date.today(),
                                justification=validated_data.get('justification'),
                                justified_by=updated_by)

                            for wfh_obj in work_from_home_deviation:
                                WorkFromHomeDeviation.objects.create(
                                    request=instance,
                                    start_date_time=wfh_obj['start_date_time'],
                                    end_date_time=wfh_obj['end_date_time'],
                                    work_done=wfh_obj['work_done'],
                                    created_by=updated_by,
                                    updated_by=updated_by
                                )
                            
                            return validated_data

                    
                    ### Reason : Emergency Situation added a request type | Author : Rupam Hazra  | Date : 19-06-2020 ###

                    # elif request_type == 'WFH':
                    #     work_from_home_deviation = validated_data.get('work_from_home')
                    #     print('work_from_home_deviation:',work_from_home_deviation)                        
                    #     total_deviation = 0
                    #     if work_from_home_deviation:
                    #         total_deviation = self.work_from_home_time_calculation(work_from_home=work_from_home_deviation)
                    #         print('total_deviation:', total_deviation)
                    #     else:
                    #         custom_exception_message(self,None, "Please fill up the work from home deviations.")
                            
                    #     if instance.duration > total_deviation:
                    #         custom_exception_message(self,None, "Please complete your working hours.")
                    #     else:
                    #         justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                    #             update(
                    #             request_type=request_type,
                    #             is_requested=True,
                    #             approved_status='approved',
                    #             request_date=datetime.date.today(),
                    #             justified_at=datetime.date.today(),
                    #             justification=validated_data.get('justification'),
                    #             justified_by=updated_by,
                    #             approved_at = datetime.date.today(),
                    #             approved_by = updated_by
                    #             )

                    #         for wfh_obj in work_from_home_deviation:
                    #             WorkFromHomeDeviation.objects.create(
                    #                 request=instance,
                    #                 start_date_time=wfh_obj['start_date_time'],
                    #                 end_date_time=wfh_obj['end_date_time'],
                    #                 work_done=wfh_obj['work_done'],
                    #                 created_by=updated_by,
                    #                 updated_by=updated_by
                    #             )
                            
                    #         return validated_data


                    # elif request_type == 'P':
                    #     justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                    #             update(
                    #             request_type=request_type,
                    #             is_requested=True,
                    #             approved_status='approved',
                    #             request_date=datetime.date.today(),
                    #             justified_at=datetime.date.today(),
                    #             justification=validated_data.get('justification'),
                    #             justified_by=updated_by,
                    #             approved_at = datetime.date.today(),
                    #             approved_by = updated_by
                    #             )

                    #     return validated_data



                    return validated_data

        except Exception as e:
            raise e


class FlexiAttendenceApprovalRequestEditSerializerV2(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    work_from_home = WorkFromHomeDeviationSerializerV2(many=True, required=False) # wfh
    kilometers_travelled = serializers.CharField(required=False, allow_null=True)
    conveyance = serializers.CharField(required=False)
    deviation_amount = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = AttendanceApprovalRequest
        fields = ('__all__')
        extra_fields = ['work_from_home','kilometers_travelled','conveyance','deviation_amount'] # wfh

    def all_leave_calculation_upto_applied_date(self, date_object=None, user=None):
        from django.db.models import Sum

        '''
        Start :: Normal leave availed by user
        '''
        how_many_days_ab_taken = 0.0
        how_many_days_al_taken = 0.0

        availed_hd_ab=0.0
        availed_ab=0.0
        availed_al = 0.0
        availed_hd_al=0.0
        carry_forward_leave = AttendanceCarryForwardLeaveBalanceYearly.objects.filter(
                    employee=user.cu_user, 
                    is_deleted=False,
                    ).first() #.aggregate(Sum('leave_balance'))
        print('carry_forward_leave:',carry_forward_leave)

        salary13_carry_forward_al = 0.0
        if carry_forward_leave and user.salary_type and user.salary_type.st_name=='13':
            if user.is_confirm:
                salary13_carry_forward_al = carry_forward_leave.leave_balance
            else:
                approved_leave = JoiningApprovedLeave.objects.filter(employee=user.cu_user,is_deleted=False).first()
                salary13_carry_forward_al = float(carry_forward_leave.leave_balance) - float(approved_leave.el)

        # salary13_carry_forward_al = carry_forward_leave.leave_balance if carry_forward_leave and user.salary_type and user.salary_type.st_name=='13'and user.is_confirm else 0.0
        print('salary13_carry_forward_al:', salary13_carry_forward_al)


        month_master=AttendenceMonthMaster.objects.filter(month_start__date__lte=date_object,
                                                    month_end__date__gte=date_object,is_deleted=False).first()
        
        print("month_master:", month_master)
        attendence_daily_data = AttendanceApprovalRequest.objects.filter(((
            Q(leave_type_changed_period__isnull=False)&(Q(leave_type_changed_period='FD')|Q(leave_type_changed_period='HD')))|
            (Q(leave_type_changed_period__isnull=True)&(Q(request_type='FD')|Q(request_type='HD')))),
            duration_start__date__gte=month_master.year_start_date.date(),
            attendance__employee=user.cu_user.id,is_requested=True).values('duration_start__date').distinct()
        print("attendence_daily_data",attendence_daily_data)
        date_list = [x['duration_start__date'] for x in attendence_daily_data.iterator()]
        print("date_list",date_list)
        
        availed_master_wo_reject_fd = AttendanceApprovalRequest.objects.\
            filter((Q(approved_status='pending')|Q(approved_status='approved')|Q(approved_status='reject')),
                    (Q(leave_type__isnull=False)|Q(leave_type_changed_period__isnull=False)),
                    attendance__employee=user.cu_user.id,
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
        print('availed_master_wo_reject_fd',availed_master_wo_reject_fd)
        if availed_master_wo_reject_fd:
            for data in date_list:
                availed_FD=availed_master_wo_reject_fd.filter(attendance_date=data)
                #print("availed_HD",availed_FD)
                if availed_FD.filter(leave_type_final__isnull=False):
                    if availed_FD.values('leave_type_final').count() >1:
                        if availed_FD.filter(leave_type_final='AB'):
                            availed_ab=availed_ab+1.0
                        elif availed_FD.filter(leave_type_final='AL'):
                            availed_al = availed_al + 1.0
                    else:
                        l_type=availed_FD[0]['leave_type_final']
                        if l_type == 'AL':
                            availed_al = availed_al + 1.0
                        elif l_type == 'AB':
                            availed_ab=availed_ab+1.0

                elif availed_FD.filter(leave_type_final_hd__isnull=False):
                    if availed_FD.values('leave_type_final_hd').count() >1:
                        if availed_FD.filter(leave_type_final_hd='AB'):
                            availed_hd_ab=availed_hd_ab+1.0
                        elif availed_FD.filter(leave_type_final_hd='AL'):
                            availed_hd_al=availed_hd_al+1.0
                    else:
                        l_type=availed_FD[0]['leave_type_final_hd']
                        if l_type == 'AL':
                            availed_hd_al=availed_hd_al+1.0
                        elif l_type == 'AB':
                            availed_hd_ab=availed_hd_ab+1.0
        
        '''
            Get total leave allocation(monthly) by request start and end date
        '''
        leave_allocation_per_month = 0.0
        
        if user.is_confirm == False: 
            if user.salary_type and user.salary_type.st_name=='13':
                leave_allocation_per_month_d = AttendenceLeaveAllocatePerMonthPerUser.objects.filter((Q(month__month_start__date__gte=month_master.year_start_date.date(),
                    month__month_end__date__lte=date_object)|Q(month__month_start__date__lte=date_object,
                    month__month_end__date__gte=date_object)),employee=user.cu_user).aggregate(Sum('round_figure_not_confirm'))
                print('leave_allocation_per_month_d',leave_allocation_per_month_d)
                leave_allocation_per_month = leave_allocation_per_month_d['round_figure_not_confirm__sum'] if leave_allocation_per_month_d['round_figure_not_confirm__sum'] else 0.0
                print('leave_allocation_per_month',leave_allocation_per_month)
            else:
                leave_allocation_per_month_d = AttendenceLeaveAllocatePerMonthPerUser.objects.filter((Q(month__month_start__date__gte=month_master.year_start_date.date(),
                month__month_end__date__lte=date_object)|
                Q(month__month_start__date__lte=date_object,
                month__month_end__date__gte=date_object)),employee=user.cu_user).aggregate(
                    Sum('round_figure'))
                leave_allocation_per_month = leave_allocation_per_month_d['round_figure__sum'] if leave_allocation_per_month_d['round_figure__sum'] else 0.0

                print('leave_allocation_per_month',leave_allocation_per_month)
        else:
            leave_allocation_per_month_d = AttendenceLeaveAllocatePerMonthPerUser.objects.filter((Q(month__month_start__date__gte=month_master.year_start_date.date(),
                month__month_end__date__lte=date_object)|
                Q(month__month_start__date__lte=date_object,
                month__month_end__date__gte=date_object)),employee=user.cu_user).aggregate(
                    Sum('round_figure'))
            leave_allocation_per_month = leave_allocation_per_month_d['round_figure__sum'] if leave_allocation_per_month_d['round_figure__sum'] else 0.0
            print('leave_allocation_per_month',leave_allocation_per_month)
        
        print('leave_allocation_per_month',leave_allocation_per_month)           

        # current year leave + salary 13 leave carry forward
        # leave_allocation_yearly = leave_allocation_yearly + total_carry_forward_leave
        



        # ::````Advance Leave Calculation```:: #
        
        advance_leave=EmployeeAdvanceLeaves.objects.filter(Q(employee=user.cu_user)&
                                                           Q(is_deleted=False)&
                                                           (Q(approved_status='pending')|Q(approved_status='approved'))&
                                                           Q(start_date__date__lte=month_master.month_end.date())
                                                          ).values('leave_type','start_date','end_date')
        #print('advance_leave',advance_leave)     
        advance_al=0
        advance_ab=0
        day=0


        last_attendance = Attendance.objects.filter(employee=user.cu_user).values_list('date__date',flat=True).order_by('-date')[:1]
        print("last_attendance",last_attendance)
        last_attendance = last_attendance[0] if last_attendance else date_object
        
        if last_attendance<month_master.month_end.date():
            print("last_attendancehfthtfrhfth",last_attendance)
            adv_str_date = last_attendance+timedelta(days=1)
            adv_end_date = month_master.month_end.date()+timedelta(days=1)
            if advance_leave:
                for leave in advance_leave:
                    print('leave',leave)
                    start_date=leave['start_date'].date()
                    end_date=leave['end_date'].date()+timedelta(days=1)
                    print('start_date,end_date',start_date,end_date)

                    if adv_str_date<=start_date and adv_end_date>=start_date:
                        if adv_end_date>=end_date:
                            day = (end_date-start_date).days
                        elif adv_end_date<=end_date:
                            day = (adv_end_date-start_date).days
                    elif adv_str_date>start_date:
                        if adv_end_date<=end_date:
                            day = (adv_end_date-adv_str_date).days
                        elif adv_str_date<=end_date and adv_end_date>=end_date:
                            day = (end_date-adv_str_date).days

                    if leave['leave_type']=='AL':
                        advance_al+=day
                    elif leave['leave_type']=='AB':
                        advance_ab+=day


        '''
            Section for count total leave count which means 
            total of advance leaves and approval leave
        '''
        
        print('advance_al',advance_al)
        # print('how_many_days_ab_taken',how_many_days_ab_taken)
        
        #print("availed_el",availed_el)
        print("availed_al",availed_al)
        
        total_availed_al=float(availed_al)+float(advance_al)+float(availed_hd_al/2) 
        print("total_availed_al",total_availed_al)

        '''
            Section for remaining leaves from granted leave - availed leave
        '''
        leave_allocation_per_month  = float(leave_allocation_per_month) + float(salary13_carry_forward_al)
        balance_al = leave_allocation_per_month - float(total_availed_al)

        return balance_al, total_availed_al, leave_allocation_per_month

    def work_from_home_time_calculation(self, work_from_home=None):
        total_deviation = 0
        for work_from_home_obj in work_from_home:
            total_deviation += (work_from_home_obj['end_date_time'] - work_from_home_obj['start_date_time']).seconds/60
        return total_deviation

    def update(self,instance, validated_data):
        # print("instance",instance)
        updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
        
        try:
            updated_by = validated_data.get('updated_by')
            date =self.context['request'].query_params.get('date', None)
            #print('date',type(date))
            #################################################################################
            #if you find error in datetime please remove only datetime from "date_object"   #
            #################################################################################
            date_object = datetime.datetime.strptime(date, '%Y-%m-%d').date()
            #print('date_object',type(date_object))
            employee_id=self.context['request'].query_params.get('employee_id', None)
            total_grace={}
            data_dict = {}
            with transaction.atomic():
                request_type=validated_data.get('request_type') if validated_data.get('request_type') else ""
                present=AttendanceApprovalRequest.objects.filter(id=instance.id,
                    attendance__is_present=True)
                total_month_grace=AttendenceMonthMaster.objects.filter(month_start__date__lte=date_object,
                                                    month_end__date__gte=date_object,is_deleted=False).values('grace_available',
                                                                                            'year_start_date',
                                                                                            'year_end_date',
                                                                                            'month',
                                                                                            'month_start',
                                                                                            'month_end'
                                                                                            )

                # REQUEST ONLY IF PRESENT AND HAVE DIVIATION
                if present:
                    
                    #*****************present but user want to give HD or FD request*********************************************************
                    if request_type == 'HD' or request_type == 'FD':
                        tcore_user = TCoreUserDetail.objects.get(cu_user=employee_id)
                        worst_late_beanchmark = tcore_user.worst_late
                        balance_al, total_availed_al, leave_allocation_per_month = self.all_leave_calculation_upto_applied_date(date_object=date_object, user=tcore_user)
                        print('balance_al:',balance_al)
                        leave_type=validated_data.get('leave_type')

                        advance_leave_calculation = advance_leave_calculation_excluding_current_month(tcore_user=tcore_user, date_object=date_object)
                        print('advance_leave_calculation', advance_leave_calculation)

                        if leave_type =='AL':
                            
                            if balance_al>0.0:
                                actual_balance = balance_al + advance_leave_calculation['advance_leave_balance']
                                is_balance_available = actual_balance > 0
                                print('is_balance_available', is_balance_available)
                                if advance_leave_calculation['is_advance_leave_taken'] and advance_leave_calculation['is_leave_taken_from_current_month'] and not is_balance_available:
                                    custom_exception_message(self,None,"Not enough leave balance. Your current month leave has been adjusted with advance leave.")
                                else:
                                    duration_length=AttendanceApprovalRequest.objects.get(id=instance.id,checkin_benchmark=False,is_requested=False)
                                    if request_type == 'HD':
                                        if duration_length.duration <=240:
                                            justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,is_late_conveyance=False,checkin_benchmark=False,is_requested=False).\
                                                    update(
                                                    request_type=request_type,
                                                    is_requested=True,
                                                    approved_status='pending',
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                            return validated_data
                                        
                                        elif duration_length.duration > 240 :
                                            if (instance.duration_start.time() and instance.duration_end.time()) < worst_late_beanchmark:
                                                # custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                                justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                    update(
                                                    request_type=request_type,
                                                    is_requested=True,
                                                    approved_status='pending',
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                                return validated_data
                                            elif instance.duration_start.time() < worst_late_beanchmark and instance.duration_end.time() > worst_late_beanchmark:
                                                custom_exception_message(self,None,"Please apply full day Your diviation exceeds 4 Hours")
                                            elif (instance.duration_start.time() and instance.duration_end.time()) > worst_late_beanchmark:
                                                # custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                                justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                    update(
                                                    request_type=request_type,
                                                    is_requested=True,
                                                    approved_status='pending',
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                                return validated_data
                                    elif request_type == 'FD' and balance_al>0.5:
                                        if actual_balance > 0.5:
                                            justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                update(
                                                request_type=request_type,
                                                is_requested=True,
                                                approved_status='pending',
                                                request_date=datetime.date.today(),
                                                justified_at=datetime.date.today(),
                                                justification=validated_data.get('justification'),
                                                justified_by=updated_by,
                                                leave_type=validated_data.get('leave_type')
                                                )

                                            return validated_data
                                        else:
                                            custom_exception_message(self,None,"Not enough leave balance. Your current month leave has been adjusted with advance leave.")
                                    else:
                                        custom_exception_message(self,None,"Not enough leave balance")
                            else:
                                # raise serializers.ValidationError("casual leave limit exceeds")
                                custom_exception_message(self,None,"leave limit exceeds")

                        elif leave_type == 'ML' or leave_type == 'BL':
                            justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                update(
                                request_type=request_type,
                                is_requested=True,
                                approved_status='approved',
                                request_date=datetime.date.today(),
                                justified_at=datetime.date.today(),
                                justification=validated_data.get('justification'),
                                justified_by=updated_by,
                                leave_type=validated_data.get('leave_type')
                                )

                            return validated_data

                        elif leave_type == 'AB':
                            justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                        update(
                                        request_type=request_type,
                                        is_requested=True,
                                        approved_status='pending',
                                        request_date=datetime.date.today(),
                                        justified_at=datetime.date.today(),
                                        justification=validated_data.get('justification'),
                                        justified_by=updated_by,
                                        leave_type=validated_data.get('leave_type')
                                        )

                            return validated_data
                    
                    #*****************As the user is already present hence partial OD********************************************************
                    elif request_type == 'OD':          
                        vehicle_type= validated_data.get('vehicle_type') if validated_data.get('vehicle_type') else None
                        from_place= validated_data.get('from_place') if validated_data.get('from_place') else None
                        to_place= validated_data.get('to_place') if validated_data.get('to_place') else None
                        conveyance_expense= validated_data.get('conveyance_expense') if validated_data.get('conveyance_expense') else 0.0
                        conveyance_remarks= validated_data.get('conveyance_purpose') if validated_data.get('conveyance_purpose') else None
                        conveyance_alloted_by= validated_data.get('conveyance_alloted_by') if validated_data.get('conveyance_alloted_by') else None
                        conveyance_purpose= validated_data.get('conveyance_purpose') if validated_data.get('conveyance_purpose') else None
                        kilometers_travelled= validated_data.get('kilometers_travelled') if validated_data.get('kilometers_travelled') else None
                        deviation_amount= validated_data.get('deviation_amount') if validated_data.get('deviation_amount') else None
                        #print(vehicle_type,from_place,to_place,conveyance_expense,conveyance_remarks,conveyance_alloted_by)
                        
                        ## Commented For Below Change Request | Rupam Hazra | Date : 07-07-2020 ##
                        if from_place or to_place or conveyance_remarks:
                            # print("aisaichai ")
                            # justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,is_requested=False).\
                            #     update(
                            #     request_type='POD',
                            #     is_requested=True,
                            #     approved_status='pending',
                            #     request_date=datetime.date.today(),
                            #     justified_at=datetime.date.today(),
                            #     justification=validated_data.get('justification'),
                            #     justified_by=updated_by,
                            #     is_conveyance=True,
                            #     conveyance_approval=0,
                            #     vehicle_type_id=vehicle_type,
                            #     conveyance_alloted_by_id=conveyance_alloted_by,
                            #     from_place=from_place,
                            #     to_place=to_place,
                            #     conveyance_expense=conveyance_expense,
                            #     conveyance_purpose=conveyance_remarks
                            #     )
                            # print("justify_attendence",justify_attendence)

                            ## Start Change Request Document__Attendance & HRMS (Conveyence Management) -CR-2 - V 1.2_Approved | Date: 23-06-2020 | Rupam Hazra ##
                            
                            justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,is_requested=False).\
                                update(
                                request_type='POD',
                                is_requested=True,
                                approved_status='pending',
                                request_date=datetime.date.today(),
                                justified_at=datetime.date.today(),
                                justification=validated_data.get('justification'),
                                justified_by=updated_by,
                                is_conveyance=True
                                )
                            #print("justify_attendence",justify_attendence)


                            conveyance_apply = ConveyanceMaster.objects.create(
                                request_id = instance.id,
                                from_place = from_place,
                                to_place = to_place,
                                vehicle_type = vehicle_type,
                                conveyance_purpose = conveyance_purpose,
                                conveyance_expense = conveyance_expense,
                                approved_expenses = conveyance_expense,
                                kilometers_travelled=kilometers_travelled,
                                conveyance_alloted_by=conveyance_alloted_by,
                                created_by=updated_by,
                                deviation_amount=deviation_amount
                                )

                            validated_data['conveyance'] = ConveyanceMaster.objects.get(request_id=instance.id)
                            ## End Change Request Document__Attendance & HRMS (Conveyence Management) -CR-2 - V 1.2_Approved | Date: 23-06-2020 | Rupam Hazra ##



                            return validated_data
                        else:
                            justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                update(
                                request_type='POD',
                                is_requested=True,
                                approved_status='pending',
                                request_date=datetime.date.today(),
                                justified_at=datetime.date.today(),
                                justification=validated_data.get('justification'),
                                justified_by=updated_by,
                                is_conveyance=False,
                                )

                            return validated_data
                    
                    #*****************Request for mispunch************************************************************************************
                    elif request_type == 'MP': 
                        justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                update(
                                request_type=request_type,
                                is_requested=True,
                                approved_status='pending',
                                request_date=datetime.date.today(),
                                justified_at=datetime.date.today(),
                                justification=validated_data.get('justification'),
                                justified_by=updated_by)

                        return validated_data

                    #********************Work from home request implementation*****************************************************************
                    elif request_type == 'WFH':
                        work_from_home_deviation = validated_data.get('work_from_home')
                        print('work_from_home_deviation:',work_from_home_deviation)
                        
                        total_deviation = 0
                        if work_from_home_deviation:
                            deviation_start_time = instance.duration_start.replace(second=0, microsecond=0)
                            deviation_end_time = instance.duration_end.replace(second=0, microsecond=0)
                            for wfhd in work_from_home_deviation:
                                wfhd['start_date_time'] = wfhd['start_date_time'].replace(second=0, microsecond=0)
                                wfhd['end_date_time'] = wfhd['end_date_time'].replace(second=0, microsecond=0)
                                if (deviation_start_time > wfhd['start_date_time'] or wfhd['start_date_time'] > deviation_end_time) or (deviation_start_time > wfhd['end_date_time'] or wfhd['end_date_time'] > deviation_end_time):
                                    error_msg = 'Work from home should be between {} to {}'.format(instance.duration_start.strftime("%I:%M %p"), instance.duration_end.strftime("%I:%M %p"))
                                    custom_exception_message(self,None, error_msg)

                            total_deviation = self.work_from_home_time_calculation(work_from_home=work_from_home_deviation)
                            print('total_deviation:', total_deviation)
                        else:
                            custom_exception_message(self,None, "Please fill up the work from home deviations.")
                            

                        if instance.duration > total_deviation:
                            custom_exception_message(self,None, "Please complete your working hours.")
                        else:
                            justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                update(
                                request_type=request_type,
                                is_requested=True,
                                approved_status='pending',
                                request_date=datetime.date.today(),
                                justified_at=datetime.date.today(),
                                justification=validated_data.get('justification'),
                                justified_by=updated_by)

                            for wfh_obj in work_from_home_deviation:
                                WorkFromHomeDeviation.objects.create(
                                    request=instance,
                                    start_date_time=wfh_obj['start_date_time'],
                                    end_date_time=wfh_obj['end_date_time'],
                                    work_done=wfh_obj['work_done'],
                                    created_by=updated_by,
                                    updated_by=updated_by
                                )
                            
                            return validated_data


                    return validated_data
                #REQUEST ONLY IF User ABSENT 
                else:

                    if request_type == 'HD' or request_type == 'FD':
                        tcore_user = TCoreUserDetail.objects.get(cu_user=employee_id)
                        worst_late_beanchmark = tcore_user.worst_late
                        balance_al, total_availed_al, leave_allocation_per_month = self.all_leave_calculation_upto_applied_date(date_object=date_object, user=tcore_user)
                        print('balance_al:',balance_al)
                        leave_type=validated_data.get('leave_type')

                        advance_leave_calculation = advance_leave_calculation_excluding_current_month(tcore_user=tcore_user, date_object=date_object)
                        print('advance_leave_calculation', advance_leave_calculation)
                        
                        if leave_type =='AL':

                            if balance_al>0.0:
                                actual_balance = balance_al + advance_leave_calculation['advance_leave_balance']
                                is_balance_available = actual_balance > 0
                                print('is_balance_available', is_balance_available)
                                if advance_leave_calculation['is_advance_leave_taken'] and advance_leave_calculation['is_leave_taken_from_current_month'] and not is_balance_available:
                                    custom_exception_message(self,None,"Not enough leave balance. Your current month leave has been adjusted with advance leave.")
                                else:
                                    duration_length=AttendanceApprovalRequest.objects.get(id=instance.id,checkin_benchmark=False,is_requested=False)
                                    if request_type == 'HD':
                                        if duration_length.duration <=240:
                                            justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,is_late_conveyance=False,checkin_benchmark=False,is_requested=False).\
                                                    update(
                                                    request_type=request_type,
                                                    is_requested=True,
                                                    approved_status='pending',
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                            return validated_data
                                        
                                        elif duration_length.duration > 240 :
                                            if (instance.duration_start.time() and instance.duration_end.time()) < worst_late_beanchmark:
                                                # custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                                justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                    update(
                                                    request_type=request_type,
                                                    is_requested=True,
                                                    approved_status='pending',
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                                return validated_data
                                            elif instance.duration_start.time() < worst_late_beanchmark and instance.duration_end.time() > worst_late_beanchmark:
                                                custom_exception_message(self,None,"Please apply full day Your diviation exceeds 4 Hours")
                                            elif (instance.duration_start.time() and instance.duration_end.time()) > worst_late_beanchmark:
                                                # custom_exception_message(self,None,"Please apply half day Your diviation exceeds 2.5 Hours")
                                                justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                    update(
                                                    request_type=request_type,
                                                    is_requested=True,
                                                    approved_status='pending',
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                                return validated_data
                                    elif request_type == 'FD' and balance_al>0.5:
                                        if actual_balance > 0.5:
                                            justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                                update(
                                                request_type=request_type,
                                                is_requested=True,
                                                approved_status='pending',
                                                request_date=datetime.date.today(),
                                                justified_at=datetime.date.today(),
                                                justification=validated_data.get('justification'),
                                                justified_by=updated_by,
                                                leave_type=validated_data.get('leave_type')
                                                )

                                            return validated_data
                                        else:
                                            custom_exception_message(self,None,"Not enough leave balance. Your current month leave has been adjusted with advance leave.")
                                    else:
                                        custom_exception_message(self,None,"Not enough casual leave balance")
                            else:
                                # raise serializers.ValidationError("casual leave limit exceeds")
                                custom_exception_message(self,None,"leave limit exceeds")

                        elif leave_type == 'ML' or leave_type == 'BL':
                            justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                update(
                                request_type=request_type,
                                is_requested=True,
                                approved_status='pending',
                                request_date=datetime.date.today(),
                                justified_at=datetime.date.today(),
                                justification=validated_data.get('justification'),
                                justified_by=updated_by,
                                leave_type=validated_data.get('leave_type')
                                )

                            return validated_data

                        elif leave_type == 'AB':
                            justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                        update(
                                        request_type=request_type,
                                        is_requested=True,
                                        approved_status='pending',
                                        request_date=datetime.date.today(),
                                        justified_at=datetime.date.today(),
                                        justification=validated_data.get('justification'),
                                        justified_by=updated_by,
                                        leave_type=validated_data.get('leave_type')
                                        )

                            return validated_data


                    elif request_type == 'OD':          
                        vehicle_type= validated_data.get('vehicle_type') if validated_data.get('vehicle_type') else None
                        from_place= validated_data.get('from_place') if validated_data.get('from_place') else None
                        to_place= validated_data.get('to_place') if validated_data.get('to_place') else None
                        conveyance_expense= validated_data.get('conveyance_expense') if validated_data.get('conveyance_expense') else 0.0
                        conveyance_remarks= validated_data.get('conveyance_purpose') if validated_data.get('conveyance_purpose') else None
                        conveyance_alloted_by= validated_data.get('conveyance_alloted_by') if validated_data.get('conveyance_alloted_by') else None
                        kilometers_travelled= validated_data.get('kilometers_travelled') if validated_data.get('kilometers_travelled') else None
                        conveyance_purpose= validated_data.get('conveyance_purpose') if validated_data.get('conveyance_purpose') else None
                        deviation_amount= validated_data.get('deviation_amount') if validated_data.get('deviation_amount') else None


                        ## Commented For Below Change Request | Rupam Hazra | Date : 07-07-2020 ##

                        if from_place or to_place or conveyance_remarks:
                            # justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,is_requested=False).\
                            #     update(
                            #     request_type='FOD',
                            #     is_requested=True,
                            #     approved_status='pending',
                            #     request_date=datetime.date.today(),
                            #     justified_at=datetime.date.today(),
                            #     justification=validated_data.get('justification'),
                            #     justified_by=updated_by,
                            #     is_conveyance=True,
                            #     vehicle_type_id=vehicle_type,
                            #     from_place=from_place,
                            #     to_place=to_place,
                            #     conveyance_alloted_by_id=conveyance_alloted_by,
                            #     conveyance_expense=conveyance_expense,
                            #     conveyance_remarks=conveyance_remarks
                            #     )


                            ## Start Change Request Document__Attendance & HRMS (Conveyence Management) -CR-2 - V 1.2_Approved | Date: 23-06-2020 | Rupam Hazra ##
                                
                            justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,is_requested=False).\
                                update(
                                request_type='FOD',
                                is_requested=True,
                                approved_status='pending',
                                request_date=datetime.date.today(),
                                justified_at=datetime.date.today(),
                                justification=validated_data.get('justification'),
                                justified_by=updated_by,
                                is_conveyance=True
                                )
                            #print("justify_attendence",justify_attendence)


                            conveyance_apply = ConveyanceMaster.objects.create(
                                request_id = instance.id,
                                from_place = from_place,
                                to_place = to_place,
                                vehicle_type = vehicle_type,
                                conveyance_purpose = conveyance_purpose,
                                conveyance_expense = conveyance_expense,
                                approved_expenses = conveyance_expense,
                                kilometers_travelled = kilometers_travelled,
                                conveyance_alloted_by = conveyance_alloted_by,
                                created_by = updated_by,
                                deviation_amount = deviation_amount
                                )

                            validated_data['conveyance'] = ConveyanceMaster.objects.get(request_id=instance.id)
                            ## End Change Request Document__Attendance & HRMS (Conveyence Management) -CR-2 - V 1.2_Approved | Date: 23-06-2020 | Rupam Hazra ##

                            return validated_data

                        else:
                            justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                update(
                                request_type='FOD',
                                is_requested=True,
                                approved_status='pending',
                                request_date=datetime.date.today(),
                                justified_at=datetime.date.today(),
                                justification=validated_data.get('justification'),
                                justified_by=updated_by,
                                is_conveyance=False,
                                )
                            data=AttendanceApprovalRequest.objects.get(id=instance.id)

                            return validated_data
                    
                    #*****************Request for mispunch************************************************************************************
                    elif request_type == 'MP': 
                        justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                update(
                                request_type=request_type,
                                is_requested=True,
                                approved_status='pending',
                                request_date=datetime.date.today(),
                                justified_at=datetime.date.today(),
                                justification=validated_data.get('justification'),
                                justified_by=updated_by)

                        return validated_data
                    
                    #********************Work from home request implementation*****************************************************************
                    elif request_type == 'WFH':
                        work_from_home_deviation = validated_data.get('work_from_home')
                        print('work_from_home_deviation:',work_from_home_deviation)                        
                        total_deviation = 0
                        if work_from_home_deviation:
                            deviation_start_time = instance.duration_start.replace(second=0, microsecond=0)
                            deviation_end_time = instance.duration_end.replace(second=0, microsecond=0)
                            for wfhd in work_from_home_deviation:
                                wfhd['start_date_time'] = wfhd['start_date_time'].replace(second=0, microsecond=0)
                                wfhd['end_date_time'] = wfhd['end_date_time'].replace(second=0, microsecond=0)
                                if (deviation_start_time > wfhd['start_date_time'] or wfhd['start_date_time'] > deviation_end_time) or (deviation_start_time > wfhd['end_date_time'] or wfhd['end_date_time'] > deviation_end_time):
                                    error_msg = 'Work from home should be between {} to {}'.format(instance.duration_start.strftime("%I:%M %p"), instance.duration_end.strftime("%I:%M %p"))
                                    custom_exception_message(self,None, error_msg)

                            total_deviation = self.work_from_home_time_calculation(work_from_home=work_from_home_deviation)
                            print('total_deviation:', total_deviation)
                        else:
                            custom_exception_message(self,None, "Please fill up the work from home deviations.")
                            
                        if instance.duration > total_deviation:
                            custom_exception_message(self,None, "Please complete your working hours.")
                        else:
                            justify_attendence=AttendanceApprovalRequest.objects.filter(id=instance.id,checkin_benchmark=False,is_requested=False).\
                                update(
                                request_type=request_type,
                                is_requested=True,
                                approved_status='pending',
                                request_date=datetime.date.today(),
                                justified_at=datetime.date.today(),
                                justification=validated_data.get('justification'),
                                justified_by=updated_by)

                            for wfh_obj in work_from_home_deviation:
                                WorkFromHomeDeviation.objects.create(
                                    request=instance,
                                    start_date_time=wfh_obj['start_date_time'],
                                    end_date_time=wfh_obj['end_date_time'],
                                    work_done=wfh_obj['work_done'],
                                    created_by=updated_by,
                                    updated_by=updated_by
                                )
                            
                            return validated_data


                    return validated_data

        except Exception as e:
            raise e


class AttendanceGraceLeaveListSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceApprovalRequest
        fields = '__all__'


# class AttendanceGraceLeaveListModifiedSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = AttendanceApprovalRequest
#         fields = '__all__'


class AttendanceLateConveyanceApplySerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    #kilometers_travelled = serializers.CharField(required=False,allow_null=True)
    conveyance_type = serializers.CharField(required=False)
    conveyance = serializers.CharField(required=False)
    deviation_amount = serializers.CharField(required=False,allow_null=True,allow_blank=True)
    address  = serializers.ListField(required=False)

    class Meta:
        model = AttendanceApprovalRequest
        fields = ('id','conveyance_expense','conveyance_purpose','conveyance_alloted_by','updated_by','address','conveyance_type','conveyance','deviation_amount')
        #extra_fields=('kilometers_travelled','conveyance_type')

    def insert_ConveyancePlacesMapping(self,address,conveyanceMaster,created_by):
        #amount = 0.0
        for each in address:
            print('place_deviation_amount',type(each['place_deviation_amount']))
            each['conveyance'] = conveyanceMaster
            each['from_place'] = each['from_place']
            each['to_place'] = each['to_place']
            each['created_by'] = created_by
            each['vehicle_type_id'] = each['vehicle_type']
            each.pop('vehicle_type')
            each['amount'] = each['amount']
            each['place_deviation_amount'] = each['place_deviation_amount'] if each['place_deviation_amount'] else None
            each['kilometers_travelled'] = each['kilometers_travelled']
            ConveyancePlacesMapping.objects.create(**each)
            #amount = amount + float(each['conveyance_expense'])
            #deviation_amount = deviation_amount + float(each['deviation_amount'])
        return True

    def update(self,instance,validated_data):
        try:
            print("validated_data",validated_data)
            with transaction.atomic():
                if instance.__dict__['is_late_conveyance'] is True:
                    address  = validated_data.pop('address')
                    ## Start Commented For and Add below code | Change Request Document__Attendance & HRMS (Conveyence Management) -CR-2 - V 1.2_Approved | Date: 23-06-2020 | Rupam Hazra ##

                    # instance.vehicle_type = validated_data.get('vehicle_type')
                    # instance.from_place = validated_data.get('from_place')
                    # instance.to_place = validated_data.get('to_place')
                    # instance.conveyance_expense = validated_data.get('conveyance_expense')
                    # instance.conveyance_purpose=validated_data.get('conveyance_purpose')
                    # instance.conveyance_alloted_by=validated_data.get('conveyance_alloted_by')
                    # instance.conveyance_approval = 0
                    # instance.updated_by = validated_data.get('updated_by')
                    # instance.save()

                    conveyance_apply = ConveyanceMaster.objects.create(
                                    request_id = instance.id,
                                    #from_place = validated_data.get('from_place'),
                                    #to_place = validated_data.get('to_place'),
                                    #vehicle_type = validated_data.get('vehicle_type'),
                                    conveyance_purpose = validated_data.get('conveyance_purpose'),
                                    conveyance_expense = validated_data.get('conveyance_expense'),
                                    approved_expenses = validated_data.get('conveyance_expense'),
                                    #kilometers_travelled=validated_data.get('kilometers_travelled'),
                                    conveyance_alloted_by=validated_data.get('conveyance_alloted_by'),
                                    conveyance_type=validated_data.get('conveyance_type'),
                                    created_by = validated_data.get('updated_by'),
                                    deviation_amount = validated_data.get('deviation_amount') if validated_data.get('deviation_amount') else None,
                                    )

                    validated_data['conveyance'] = conveyance_apply
                    self.insert_ConveyancePlacesMapping(address,conveyance_apply,validated_data.get('updated_by'))
                ## End Change Request Document__Attendance & HRMS (Conveyence Management) -CR-2 - V 1.2_Approved | Date: 23-06-2020 | Rupam Hazra ##

                return validated_data
        except Exception as e:
            raise e


class AttendanceLateConveyanceDocumentAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = AttandanceApprovalDocuments
        fields = ('id','request','document_name','document','created_by','owned_by')


class AttandanceApprovalDocumentUploadSerializerV2(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = AttandanceApprovalDocuments
        fields = ('id','request','document_name','document','created_by','owned_by')


class AttendanceConveyanceApprovalListSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceApprovalRequest
        fields = ('id','is_conveyance','is_late_conveyance','deviation_amount','conveyance_approval','vehicle_type', 'deviation_amount',
        'conveyance_purpose','conveyance_alloted_by','from_place','to_place','conveyance_expense',
        'approved_expenses','conveyance_remarks','attendance','duration_start','duration_end','duration',
        'conveyance_approved_by','updated_by')

    # def create(self,validated_data):
    #     '''
    #         1)Admin can provide mass update by selecting as much request he wanted 
    #     '''
        
    #     updated_by = serializers.CharField(default=serializers.CurrentUserDefault())

    #     for data in validated_data:
    #         conveyance_approval= data['conveyance_approval']
    #         approved_expenses=data['approved_expenses']

    #         if conveyance_approval == 3 :
    #             AttendanceApprovalRequest.objects.filter(id=data['req_id']).update(conveyance_approval=conveyance_approval,
    #                                                                     conveyance_approved_by=updated_by,approved_expenses=approved_expenses)
    #         else:
    #             AttendanceApprovalRequest.objects.filter(id=req_id).update(conveyance_approval=conveyance_approval,
    #                                                                         conveyance_approved_by=updated_by)
    #         # print(AttendanceApprovalRequest.)
    #         if AttendanceApprovalRequest:

    #             return Response({'results': {'conveyance_approval': conveyance_approval, },
    #                             'msg': 'success',
    #                             "request_status": 1})
    #         else:
    #             return Response({'results': {'conveyance_approval': conveyance_approval, },
    #                             'msg': 'fail',
    #                             "request_status": 0})


class AttendanceSummaryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = '__all__'


class AttendanceSummaryListSerializerV2(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = '__all__'


class FlexiAttendanceSummaryListSerializerV2(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = '__all__'


class FlexiTeamFortnightAttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = '__all__'


class AttendanceDailyListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = '__all__'


class AttendanceDailyListSerializerV2(serializers.ModelSerializer):

    class Meta:
        model = Attendance
        fields = '__all__'

#:::::::::::::::::::::::::::ATTENDANCE ADVANCE LEAVE::::::::::::::::::::::::::::#
class AttendanceAdvanceLeaveListSerializer(serializers.ModelSerializer):
    leave_count = serializers.SerializerMethodField(required=False)
    department = serializers.SerializerMethodField(required=False)
    designation = serializers.SerializerMethodField(required=False)
    reporting_head = serializers.SerializerMethodField(required=False)
    hod = serializers.SerializerMethodField(required=False)

    def get_leave_count(self,EmployeeAdvanceLeaves):
        request_how_many_days = (EmployeeAdvanceLeaves.end_date - EmployeeAdvanceLeaves.start_date).days + 1
        return request_how_many_days

    def get_department(self,EmployeeAdvanceLeaves):
        return EmployeeAdvanceLeaves.employee.cu_user.department.cd_name if EmployeeAdvanceLeaves.employee.cu_user.department else None
    
    def get_designation(self,EmployeeAdvanceLeaves):
        return EmployeeAdvanceLeaves.employee.cu_user.designation.cod_name if EmployeeAdvanceLeaves.employee.cu_user.designation else None

    def get_reporting_head(self,EmployeeAdvanceLeaves):
        return EmployeeAdvanceLeaves.employee.cu_user.reporting_head.first_name+' '+EmployeeAdvanceLeaves.employee.cu_user.reporting_head.last_name if EmployeeAdvanceLeaves.employee.cu_user.reporting_head else None

    def get_hod(self,EmployeeAdvanceLeaves):
        name = EmployeeAdvanceLeaves.employee.cu_user.hod.first_name+' '+EmployeeAdvanceLeaves.employee.cu_user.hod.last_name if EmployeeAdvanceLeaves.employee.cu_user.hod else None
        return name

    class Meta:
        model = EmployeeAdvanceLeaves
        fields = '__all__'
        extra_fields = ['leave_count','department','designation','reporting_head','hod']
    

class AttendanceAdvanceLeaveListSerializerV2(serializers.ModelSerializer):
    leave_count = serializers.SerializerMethodField(required=False)
    department = serializers.SerializerMethodField(required=False)
    designation = serializers.SerializerMethodField(required=False)
    reporting_head = serializers.SerializerMethodField(required=False)
    hod = serializers.SerializerMethodField(required=False)
    company = serializers.SerializerMethodField(required=False)
    company_id = serializers.SerializerMethodField(required=False)
    department_id = serializers.SerializerMethodField(required=False)
    designation_id = serializers.SerializerMethodField(required=False)

    def get_company_id(self,EmployeeAdvanceLeaves):
        return EmployeeAdvanceLeaves.employee.cu_user.company.id if EmployeeAdvanceLeaves.employee.cu_user.company else None

    def get_company(self,EmployeeAdvanceLeaves):
        return EmployeeAdvanceLeaves.employee.cu_user.company.coc_name if EmployeeAdvanceLeaves.employee.cu_user.company else None

    def get_department_id(self,EmployeeAdvanceLeaves):
        return EmployeeAdvanceLeaves.employee.cu_user.department.id if EmployeeAdvanceLeaves.employee.cu_user.department else None

    def get_designation_id(self,EmployeeAdvanceLeaves):
        return EmployeeAdvanceLeaves.employee.cu_user.designation.id if EmployeeAdvanceLeaves.employee.cu_user.designation else None


    def get_leave_count(self,EmployeeAdvanceLeaves):
        request_how_many_days = (EmployeeAdvanceLeaves.end_date - EmployeeAdvanceLeaves.start_date).days + 1
        return request_how_many_days

    def get_department(self,EmployeeAdvanceLeaves):
        return EmployeeAdvanceLeaves.employee.cu_user.department.cd_name if EmployeeAdvanceLeaves.employee.cu_user.department else None
    
    def get_designation(self,EmployeeAdvanceLeaves):
        return EmployeeAdvanceLeaves.employee.cu_user.designation.cod_name if EmployeeAdvanceLeaves.employee.cu_user.designation else None

    def get_reporting_head(self,EmployeeAdvanceLeaves):
        return EmployeeAdvanceLeaves.employee.cu_user.reporting_head.first_name+' '+EmployeeAdvanceLeaves.employee.cu_user.reporting_head.last_name if EmployeeAdvanceLeaves.employee.cu_user.reporting_head else None

    def get_hod(self,EmployeeAdvanceLeaves):
        name = EmployeeAdvanceLeaves.employee.cu_user.hod.first_name+' '+EmployeeAdvanceLeaves.employee.cu_user.hod.last_name if EmployeeAdvanceLeaves.employee.cu_user.hod else None
        return name

    class Meta:
        model = EmployeeAdvanceLeaves
        fields = '__all__'
        extra_fields = ['leave_count', 'department','designation','reporting_head', 'hod', 'company',
                        'company_id', 'designation_id', 'department_id']


class AdminAttendanceAdvanceLeavePendingListSerializer(serializers.ModelSerializer):
    leave_count = serializers.SerializerMethodField(required=False)
    department = serializers.SerializerMethodField(required=False)
    designation = serializers.SerializerMethodField(required=False)
    reporting_head = serializers.SerializerMethodField(required=False)
    hod = serializers.SerializerMethodField(required=False)
    def get_leave_count(self,EmployeeAdvanceLeaves):
        request_how_many_days = (EmployeeAdvanceLeaves.end_date - EmployeeAdvanceLeaves.start_date).days + 1
        return request_how_many_days
    def get_department(self,EmployeeAdvanceLeaves):
        return EmployeeAdvanceLeaves.employee.cu_user.department.cd_name if EmployeeAdvanceLeaves.employee.cu_user.department else None
    
    def get_designation(self,EmployeeAdvanceLeaves):
        return EmployeeAdvanceLeaves.employee.cu_user.designation.cod_name if EmployeeAdvanceLeaves.employee.cu_user.designation else None

    def get_reporting_head(self,EmployeeAdvanceLeaves):
        return EmployeeAdvanceLeaves.employee.cu_user.reporting_head.first_name+' '+EmployeeAdvanceLeaves.employee.cu_user.reporting_head.last_name if EmployeeAdvanceLeaves.employee.cu_user.reporting_head else None

    def get_hod(self,EmployeeAdvanceLeaves):
        name = EmployeeAdvanceLeaves.employee.cu_user.hod.first_name+' '+EmployeeAdvanceLeaves.employee.cu_user.hod.last_name if EmployeeAdvanceLeaves.employee.cu_user.hod else None
        return name
    class Meta:
        model = EmployeeAdvanceLeaves
        fields = '__all__'
        extra_fields = ['leave_count', 'department','designation','reporting_head','hod']



class AdminAttendanceAdvanceLeavePendingListSerializerV2(serializers.ModelSerializer):
    leave_count = serializers.SerializerMethodField(required=False)
    department = serializers.SerializerMethodField(required=False)
    designation = serializers.SerializerMethodField(required=False)
    reporting_head = serializers.SerializerMethodField(required=False)
    hod = serializers.SerializerMethodField(required=False)
    
    def get_leave_count(self,EmployeeAdvanceLeaves):
        request_how_many_days = (EmployeeAdvanceLeaves.end_date - EmployeeAdvanceLeaves.start_date).days + 1
        return request_how_many_days
    def get_department(self,EmployeeAdvanceLeaves):
        return EmployeeAdvanceLeaves.employee.cu_user.department.cd_name if EmployeeAdvanceLeaves.employee.cu_user.department else None
    
    def get_designation(self,EmployeeAdvanceLeaves):
        return EmployeeAdvanceLeaves.employee.cu_user.designation.cod_name if EmployeeAdvanceLeaves.employee.cu_user.designation else None

    def get_reporting_head(self,EmployeeAdvanceLeaves):
        return EmployeeAdvanceLeaves.employee.cu_user.reporting_head.first_name+' '+EmployeeAdvanceLeaves.employee.cu_user.reporting_head.last_name if EmployeeAdvanceLeaves.employee.cu_user.reporting_head else None

    def get_hod(self,EmployeeAdvanceLeaves):
        name = EmployeeAdvanceLeaves.employee.cu_user.hod.first_name+' '+EmployeeAdvanceLeaves.employee.cu_user.hod.last_name if EmployeeAdvanceLeaves.employee.cu_user.hod else None
        return name
    class Meta:
        model = EmployeeAdvanceLeaves
        fields = '__all__'
        extra_fields = ['leave_count', 'department','designation','reporting_head','hod']


class AdminAttendanceAdvanceLeaveApprovalSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    advance_leaves_approvals= serializers.ListField(required=False)

    class Meta:
        model = EmployeeAdvanceLeaves
        fields = ('id', 'approved_status', 'remarks','updated_by','advance_leaves_approvals')

    def create(self,validated_data):
        '''
            1)Admin can provide mass update by selecting as much request he wanted 
        '''

        print(validated_data)
        updated_by = validated_data.get('updated_by')
        remarks = validated_data.get('remarks')
        # master_module_role = TMasterModuleRoleUser.objects.get(mmr_module__cm_name__iexact='hrms',mmr_user=self.context['request'].user).mmr_role
        # core_role = TCoreRole.objects.get(id=str(master_module_role)).cr_name
        for data in validated_data.get('advance_leaves_approvals'):
            approved_status= data['approved_status']
            req_type = EmployeeAdvanceLeaves.objects.get(id=data['req_id'])
            EmployeeAdvanceLeaves.objects.filter(id=data['req_id']).update(approved_status=approved_status,
                                                                    updated_by=updated_by,remarks=remarks)
        
            # if core_role.lower() == 'hr admin':
            logger.log(self.context['request'].user,approved_status+" "+req_type.leave_type,
                'Approval','pending',approved_status,'HRMS-TeamAttendance-LeaveApproval') 
            # elif core_role.lower() == 'hr user':
            #     logger.log(self.context['request'].user,AttendenceAction.ACTION_HR,'rejected'+" "+req_type.leave_type,
            #     'Approval','pending',approved_status,'HRMS-TeamAttendance-LeaveApproval')

        data = validated_data

        return data
    
    # def update(self,instance,validated_data):
    #     try:
    #         instance.approved_status = validated_data.get('approved_status')
    #         instance.remarks = validated_data.get('remarks')
    #         instance.updated_by = validated_data.get('updated_by')
    #         instance.save()
    #         return instance
    #     except Exception as e:
    #         raise e


class AttendanceAdvanceLeaveAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = EmployeeAdvanceLeaves
        fields = '__all__'

    def is2ndOr4thSaturday(self,date1):
        # if date1 is string then you convert the string to date object
        dt = datetime.datetime.strptime(date1, '%Y-%m-%d')
        year = dt.year
        month =  dt.month
        # print('year',year)
        # print('month',month)
        month_calender = calendar.monthcalendar(year, month)
        second_fourth_saturday = (1, 3) if month_calender[0][calendar.SATURDAY] else (2, 4)
        return any(dt.day == month_calender[i][calendar.SATURDAY] for i in second_fourth_saturday)
        
    def leaveDaysCountWithOutHoliday(self,date1, date2):
        request_leave_days = (date2 - date1).days + 1
        #print('request_leave_days',request_leave_days)
        holiday_count = 0
        for dt in self.daterange(date1, date2):
            #print(dt.strftime("%A"))
            day = dt.strftime("%A")
            '''
            Modified By :: Rajesh Samui
            Reason :: State Wise Holiday Calculation
            Line :: 2180-2182
            Date :: 10-02-2020
            '''
            #holiday_details = HolidaysList.objects.filter(holiday_date = dt.strftime("%Y-%m-%d"))
            user = self.context['request'].user
            state_obj = TCoreUserDetail.objects.get(cu_user=user).job_location_state
            default_state = TCoreState.objects.filter(cs_state_name__iexact='west bengal').first()
            t_core_state_id = state_obj.id if state_obj else default_state.id
            holiday_details = HolidayStateMapping.objects.filter(Q(holiday__holiday_date=dt.strftime("%Y-%m-%d"))&Q(state__id=t_core_state_id))
            if holiday_details or day == 'Sunday':
                holiday_count = holiday_count + 1
        
        #print('holiday_count',holiday_count)
        days_count = request_leave_days - holiday_count
        #print('days_count',days_count)
        return days_count   

    def daterange(self,date1, date2):
        for n in range(int ((date2 - date1).days)+1):
            yield date1 + timedelta(n)

    def getMonthsAndDaysBetweenDateRange(self,date1, date2):
        month_details = list()
        months = set()
        for dt in self.daterange(date1, date2):
            month_de = dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            month_de = calendar.month_name[datetime.datetime.strptime(month_de,"%Y-%m-%dT%H:%M:%S.%fZ").month]
            months.add(month_de)
        #print('months',months)
        for month in months:
            days = self.getDaysByMonth(month,date1, date2)
            month_details.append({
                'month':month,
                'days':days
            })
        return month_details

    def getDaysByMonth(self,month,date1, date2):
        days = 0
        for dt in self.daterange(date1, date2):
            month_de = dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            month_de = calendar.month_name[datetime.datetime.strptime(month_de,"%Y-%m-%dT%H:%M:%S.%fZ").month]
            day = dt.strftime("%A")
            '''
            Modified By :: Rajesh Samui
            Reason :: State Wise Holiday Calculation
            Line :: 2223-2225
            Date :: 10-02-2020
            '''
            #holiday_details = HolidaysList.objects.filter(holiday_date = dt.strftime("%Y-%m-%d"))
            user = self.context['request'].user
            state_obj = TCoreUserDetail.objects.get(cu_user=user).job_location_state
            default_state = TCoreState.objects.filter(cs_state_name__iexact='west bengal').first()
            t_core_state_id = state_obj.id if state_obj else default_state.id
            holiday_details = HolidayStateMapping.objects.filter(Q(holiday__holiday_date=dt.strftime("%Y-%m-%d"))&Q(state__id=t_core_state_id))
            if not holiday_details or day != 'Sunday':
                if month == month_de:
                    days = days + 1
        return days
        

    def create(self, validated_data):

        '''
            This Method prepared by @@ Rupam Hazra. Any kind of issues occurred, ask me first !!!

            Note :: 
            1) Used Date Format : yyyy-mm-dd
            2) Checking Start Date should not less than today's date!
            3) End Date should be greater than or euqual to start date!
            4) You can't apply 3 CL for same month!
            5) You have already taken 3 CL for same month!
            6) You requested leaves has not been granted, due to insufficient EL/CL
            7) Check 2nd and 4th satuday off by is2ndOr4thSaturday method
            8) Normal Leave Count and Advance Leave Count From Approval Request Table
        '''

        current_date = datetime.date.today()
        #print('current_date ::::',current_date)
        request_datetime = validated_data.get('start_date').strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        request_datetime = datetime.datetime.strptime(request_datetime,"%Y-%m-%dT%H:%M:%S.%fZ").date()


        request_end_datetime = validated_data.get('end_date').strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        request_end_datetime = datetime.datetime.strptime(request_end_datetime,"%Y-%m-%dT%H:%M:%S.%fZ").date()

        #request_how_many_days_cl = 0.0
        #request_how_many_days_el = 0.0
        how_many_days_cl_taken_on_same_month = 0.0
        balance_el = 0.0
        balance_cl = 0.0
        balance_ab = 0.0
        how_many_days_cl_taken = 0.0
        how_many_days_el_taken = 0.0
        how_many_days_ab_taken = 0.0
        
        # leaveDaysCountWithOutHoliday = self.leaveDaysCountWithOutHoliday(
        #     validated_data.get('start_date'),validated_data.get('end_date'))
        # print('leaveDaysCountWithOutHoliday',leaveDaysCountWithOutHoliday)

        request_how_many_days = (validated_data.get('end_date') - validated_data.get('start_date')).days + 1
        print('request_how_many_days',request_how_many_days)

        request_start_date_month = validated_data.get('start_date').strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        request_start_date_month = calendar.month_name[datetime.datetime.strptime(request_start_date_month,"%Y-%m-%dT%H:%M:%S.%fZ").month]
        
        #print('request_start_date_month',request_start_date_month)

        request_end_date_month = validated_data.get('end_date').strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        request_end_date_month = calendar.month_name[datetime.datetime.strptime(request_end_date_month,"%Y-%m-%dT%H:%M:%S.%fZ").month]
        
        #print('request_end_date_month',request_end_date_month)

        if request_datetime < current_date :
            custom_exception_message(self,None,"Start Date should not less than today's date!")
        
        if request_datetime > request_end_datetime:
            custom_exception_message(self,None,"End Date should be greater than or euqual to start date!")


        getMonthsAndDaysBetweenDateRange = self.getMonthsAndDaysBetweenDateRange(validated_data.get('start_date'),validated_data.get('end_date'))
        #print('getMonthsAndDaysBetweenDateRange',getMonthsAndDaysBetweenDateRange)

        if validated_data.get('leave_type') == 'CL':
            '''
                Checking You can't apply 3 CL for same month!
            '''
            for e_getMonthsAndDaysBetweenDateRange in getMonthsAndDaysBetweenDateRange:
                if e_getMonthsAndDaysBetweenDateRange['days'] > 3:
                    custom_exception_message(self,'',"You can't apply 3 CL for same month!")
                

        if validated_data.get('leave_type') == 'CL' and request_start_date_month == request_end_date_month :
            how_many_days_cl_taken_on_same_month = request_how_many_days

        # userdetails from TCoreUserDetail
        empDetails_from_coreuserdetail = TCoreUserDetail.objects.filter(
            cu_user=validated_data.get('employee'))[0]
        #print('empDetails_from_coreuserdetail',empDetails_from_coreuserdetail)
        employee_id = validated_data.get('employee')

        if empDetails_from_coreuserdetail:
            '''
                Normal Leave Count From approval request
            '''
            #starttime = datetime.now()
            availed_hd_cl=0.0
            availed_hd_el=0.0
            availed_hd_sl=0.0
            availed_hd_ab=0.0
            availed_cl=0.0
            availed_el=0.0
            availed_sl=0.0
            availed_ab=0.0
            attendence_daily_data = AttendanceApprovalRequest.objects.filter(((
                Q(leave_type_changed_period__isnull=False)&(Q(leave_type_changed_period='FD')|Q(leave_type_changed_period='HD')))|
                                                                        (Q(leave_type_changed_period__isnull=True)&(Q(request_type='FD')|Q(request_type='HD')))),
                                                                        attendance__employee=employee_id,is_requested=True).values('duration_start__date').distinct()
            #print("attendence_daily_data",attendence_daily_data)
            date_list = [x['duration_start__date'] for x in attendence_daily_data.iterator()]
            #print("date_list",date_list)
            
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
            #print('availed_master_wo_reject_fd',availed_master_wo_reject_fd)
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
                            # elif l_type == 'SL':
                            #     availed_sl=availed_sl+1.0
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
                            # elif l_type == 'SL':
                            #     availed_hd_sl=availed_hd_sl+1.0
                            elif l_type == 'AB':
                                availed_hd_ab=availed_hd_ab+1.0
            
            '''
                Advance Leave Calculation 
            '''

            last_attendence_date = AttendanceApprovalRequest.objects.all().values_list(
                'attendance_date',flat=True).order_by('-attendance_date')[0]
            print('last_attendence_date',last_attendence_date)

            joining_date = empDetails_from_coreuserdetail.joining_date
            #print('joining_date',joining_date)
            attendence_month_masters = AttendenceMonthMaster.objects.filter(
                year_start_date__gt = joining_date,
                year_end_date__lt = joining_date).order_by('-year_start_date')
            #print('attendence_month_masters',attendence_month_masters)

            if attendence_month_masters:
                joining_approved_leaves = JoiningApprovedLeave.objects.filter(
                    employee=validated_data.get('employee'))
                #print('joining_approved_leaves',joining_approved_leaves)
                if joining_approved_leaves:
                    joining_approved_leaves = JoiningApprovedLeave.objects.filter(
                    employee=validated_data.get('employee'))[0]
                    granted_cl = joining_approved_leaves.cl
                    #granted_sl = joining_approved_leaves.sl
                    granted_el = joining_approved_leaves.el
            else:
                granted_cl = empDetails_from_coreuserdetail.granted_cl
                #granted_sl = empDetails_from_coreuserdetail.granted_sl
                granted_el = empDetails_from_coreuserdetail.granted_el

            # total_granted_leave = (granted_cl + granted_sl + granted_el)
            # print('total_granted_leave',total_granted_leave)

            empDetails_from_advance_leave = EmployeeAdvanceLeaves.objects.filter(
                (Q(approved_status = 'pending') | Q(approved_status = 'approved')),
                 employee=validated_data.get('employee'),is_deleted=False,
                 start_date__date__gte = last_attendence_date,
                 end_date__date__gte = last_attendence_date,
                 
                )
            print('empDetails_from_advance_leave',empDetails_from_advance_leave)
            if empDetails_from_advance_leave:

                for e_empDetails_from_advance_leave in empDetails_from_advance_leave:

                    if e_empDetails_from_advance_leave.leave_type == 'CL':
                        '''
                            Checking taken cl not greater than 3 in a month
                        '''
                        start_month_details = calendar.month_name[datetime.datetime.strptime(
                            e_empDetails_from_advance_leave.start_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                            "%Y-%m-%dT%H:%M:%S.%fZ").month]
                        
                        #print('start_month_details',start_month_details)

                        end_month_details = calendar.month_name[datetime.datetime.strptime(
                            e_empDetails_from_advance_leave.end_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                            "%Y-%m-%dT%H:%M:%S.%fZ").month]
                        
                        #print('end_month_details',end_month_details)

                        if (start_month_details == request_start_date_month and start_month_details == request_end_date_month) or(
                            end_month_details == request_start_date_month and end_month_details == request_end_date_month):

                            how_many_days_cl_taken_on_same_month = how_many_days_cl_taken_on_same_month + (e_empDetails_from_advance_leave.end_date - 
                            e_empDetails_from_advance_leave.start_date).days + 1

                        #print('how_many_days_cl_taken_on_same_month:::',how_many_days_cl_taken_on_same_month)
                        how_many_days_cl_taken = how_many_days_cl_taken + (e_empDetails_from_advance_leave.end_date - 
                                e_empDetails_from_advance_leave.start_date).days + 1
                        
                        #print('how_many_days_cl_taken:::::',how_many_days_cl_taken)

                    if e_empDetails_from_advance_leave.leave_type == 'EL':
                        how_many_days_el_taken = how_many_days_el_taken + (e_empDetails_from_advance_leave.end_date - 
                            e_empDetails_from_advance_leave.start_date).days + 1
                        #print('how_many_days_el_taken:::::',how_many_days_el_taken)
                    
                    if e_empDetails_from_advance_leave.leave_type == 'AB':
                        how_many_days_ab_taken = how_many_days_ab_taken + (e_empDetails_from_advance_leave.end_date - 
                            e_empDetails_from_advance_leave.start_date).days + 1
                        #print('how_many_days_ab_taken:::::',how_many_days_ab_taken)

                if how_many_days_cl_taken_on_same_month > 3:
                    custom_exception_message(self,'',"You can't apply 3 CL for same month!")

            '''
                Section for count total cl and el count which means 
                total of advance leaves and approval leave
            '''
            print('how_many_days_cl_taken',how_many_days_cl_taken)
            print('how_many_days_el_taken',how_many_days_el_taken)
            # print('how_many_days_ab_taken',how_many_days_ab_taken)

            print("availed_cl",availed_cl)
            print("availed_el",availed_el)

            total_availed_cl=float(availed_cl)+float(how_many_days_cl_taken)+float(availed_hd_cl/2)
            print("total_availed_cl",total_availed_cl)
            total_availed_el=float(availed_el)+float(how_many_days_el_taken)+float(availed_hd_el/2)
            print("total_availed_el",total_availed_el)

            print('granted_cl',granted_cl)
            print('granted_el',granted_el)

            '''
                Section for count balance cl and el count which means 
                remaining leaves from granted leave - availed leave
            '''

            balance_cl = float(granted_cl) - float(total_availed_cl)
            print('balance_cl',balance_cl)
            balance_el = float(granted_el) - float(total_availed_el)
            print('balance_el',balance_el)

            # availed_sl=float(availed_sl)+float(availed_hd_sl/2)
            # print("availed_sl",availed_sl)
            # availed_ab=float(availed_ab)+float(how_many_days_ab_taken)+float(availed_hd_ab/2)
            # print("availed_ab",availed_ab)
            # total_availed_leave=availed_cl +availed_el + availed_sl
            # print('total_availed_leave',total_availed_leave)

            '''
                Validation on CL or EL modified
            '''

            #holiday_count = 0
            
            if validated_data.get('leave_type') == 'CL':
                #request_how_many_days_cl = request_how_many_days
                # for dt in self.daterange(validated_data.get('start_date'), validated_data.get('end_date')):
                #     #print(dt.strftime("%A"))
                #     day = dt.strftime("%A")
                #     holiday_details = HolidaysList.objects.filter(holiday_date = dt.strftime("%Y-%m-%d"))

                #     if (holiday_details or day == 'Saturday')  and empDetails_from_coreuserdetail.is_saturday_off:
                #         if  day == 'Saturday' and self.is2ndOr4thSaturday(dt.strftime("%Y-%m-%d")) == False:
                #             holiday_count = holiday_count + 1
                #         else:
                #             holiday_count = holiday_count
                    
                # #print('holiday_count',holiday_count)
                # if leaveDaysCountWithOutHoliday > 6 and holiday_count > 0 :
                #     request_how_many_days_cl = leaveDaysCountWithOutHoliday + holiday_count
                # else:
                #     request_how_many_days_cl = leaveDaysCountWithOutHoliday

                #print('request_how_many_days_cl111',request_how_many_days_cl)
                if request_how_many_days > balance_cl:
                    custom_exception_message(self,None,"You requested leaves has not been granted, due to insufficient CL")

            if validated_data.get('leave_type') == 'EL':
                #request_how_many_days_el = request_how_many_days
                # for dt in self.daterange(validated_data.get('start_date'), validated_data.get('end_date')):
                #     #print(dt.strftime("%A"))
                #     day = dt.strftime("%A")
                #     holiday_details = HolidaysList.objects.filter(holiday_date = dt.strftime("%Y-%m-%d"))

                #     if (holiday_details or day == 'Saturday')  and empDetails_from_coreuserdetail.is_saturday_off:
                #         if  day == 'Saturday' and self.is2ndOr4thSaturday(dt.strftime("%Y-%m-%d")) == False:
                #             holiday_count = holiday_count + 1
                #         else:
                #             holiday_count = holiday_count
                    
                # #print('holiday_count',holiday_count)
                # if leaveDaysCountWithOutHoliday > 6 and holiday_count > 0 :
                #     request_how_many_days_el = leaveDaysCountWithOutHoliday + holiday_count
                # else:
                #     request_how_many_days_el = leaveDaysCountWithOutHoliday
                
                # print('request_how_many_days_el',request_how_many_days_el)

                if request_how_many_days > balance_el:
                    custom_exception_message(self,None,"You requested leaves has not been granted, due to insufficient EL")
                
        return super().create(validated_data)


class ETaskAttendanceApprovalListSerializer(serializers.ModelSerializer):
    employee_name=serializers.SerializerMethodField(required=False)
    employee_id=serializers.SerializerMethodField(required=False) 
    department=serializers.SerializerMethodField(required=False)
    designation=serializers.SerializerMethodField(required=False)
    reporting_head=serializers.SerializerMethodField(required=False)
    hod=serializers.SerializerMethodField(required=False)
    
    def get_employee_name(self,AttendanceApprovalRequest):
        if AttendanceApprovalRequest.attendance:
            first_name=AttendanceApprovalRequest.attendance.employee.first_name if AttendanceApprovalRequest.attendance.employee.first_name  else ''
            last_name=AttendanceApprovalRequest.attendance.employee.last_name if AttendanceApprovalRequest.attendance.employee.last_name else ''
            name=first_name+" "+last_name
            return name
    def get_employee_id(self,AttendanceApprovalRequest):
        if AttendanceApprovalRequest.attendance:
            return AttendanceApprovalRequest.attendance.employee.id

    def get_department(self,AttendanceApprovalRequest):
        if AttendanceApprovalRequest.attendance:
            return AttendanceApprovalRequest.attendance.employee.cu_user.department.cd_name if AttendanceApprovalRequest.attendance.employee.cu_user.department else None
    
    def get_designation(self,AttendanceApprovalRequest):
        if AttendanceApprovalRequest.attendance:
            return AttendanceApprovalRequest.attendance.employee.cu_user.designation.cod_name if AttendanceApprovalRequest.attendance.employee.cu_user.designation else None

    def get_reporting_head(self,AttendanceApprovalRequest):
        if AttendanceApprovalRequest.attendance:
            return AttendanceApprovalRequest.attendance.employee.cu_user.reporting_head.first_name+' '+AttendanceApprovalRequest.attendance.employee.cu_user.reporting_head.last_name if AttendanceApprovalRequest.attendance.employee.cu_user.reporting_head else None

    def get_hod(self,AttendanceApprovalRequest):
        if AttendanceApprovalRequest.attendance:
            name = AttendanceApprovalRequest.attendance.employee.cu_user.hod.first_name+' '+AttendanceApprovalRequest.attendance.employee.cu_user.hod.last_name if AttendanceApprovalRequest.attendance.employee.cu_user.hod else None
            return name

    class Meta:
        model = AttendanceApprovalRequest
        fields = '__all__'
        extra_fields=('employee_name','employee_id','department','designation','reporting_head','hod')


class ETaskAttendanceApprovalListSerializerV2(serializers.ModelSerializer):
    employee_name=serializers.SerializerMethodField(required=False)
    employee_id=serializers.SerializerMethodField(required=False) 
    department=serializers.SerializerMethodField(required=False)
    designation=serializers.SerializerMethodField(required=False)
    reporting_head=serializers.SerializerMethodField(required=False)
    hod=serializers.SerializerMethodField(required=False)
    documents=serializers.SerializerMethodField(required=False)
    department_id = serializers.SerializerMethodField(required=False)
    company_id = serializers.SerializerMethodField(required=False)
    designation_id = serializers.SerializerMethodField(required=False)
    company = serializers.SerializerMethodField(required=False)


    def get_department_id(self, AttendanceApprovalRequest):
        if AttendanceApprovalRequest.attendance:
            department_id = AttendanceApprovalRequest.attendance.employee.cu_user.department.id if AttendanceApprovalRequest.attendance.employee.cu_user.department else ''
            return department_id

    def get_company_id(self, AttendanceApprovalRequest):
        if AttendanceApprovalRequest.attendance:
            company_id = AttendanceApprovalRequest.attendance.employee.cu_user.company.id if AttendanceApprovalRequest.attendance.employee.cu_user.company else ''
            return company_id

    def get_designation_id(self, AttendanceApprovalRequest):
        if AttendanceApprovalRequest.attendance:
            try:
                designation_id = AttendanceApprovalRequest.attendance.employee.cu_user.designation.id if AttendanceApprovalRequest.attendance.employee.cu_user.designation else ''
                return designation_id
            except:
                return None
    
    def get_employee_name(self,AttendanceApprovalRequest):
        if AttendanceApprovalRequest.attendance:
            first_name = AttendanceApprovalRequest.attendance.employee.first_name if AttendanceApprovalRequest.attendance.employee.first_name  else ''
            last_name = AttendanceApprovalRequest.attendance.employee.last_name if AttendanceApprovalRequest.attendance.employee.last_name else ''
            name = first_name+" "+last_name
            return name
    def get_employee_id(self,AttendanceApprovalRequest):
        if AttendanceApprovalRequest.attendance:
            return AttendanceApprovalRequest.attendance.employee.id

    def get_department(self,AttendanceApprovalRequest):
        if AttendanceApprovalRequest.attendance:
            return AttendanceApprovalRequest.attendance.employee.cu_user.department.cd_name if AttendanceApprovalRequest.attendance.employee.cu_user.department else None
    
    def get_designation(self,AttendanceApprovalRequest):
        try:
            if AttendanceApprovalRequest.attendance:
                return AttendanceApprovalRequest.attendance.employee.cu_user.designation.cod_name if AttendanceApprovalRequest.attendance.employee.cu_user.designation else None
        except:
            return None

    def get_reporting_head(self,AttendanceApprovalRequest):
        if AttendanceApprovalRequest.attendance:
            return AttendanceApprovalRequest.attendance.employee.cu_user.reporting_head.first_name+' '+AttendanceApprovalRequest.attendance.employee.cu_user.reporting_head.last_name if AttendanceApprovalRequest.attendance.employee.cu_user.reporting_head else None

    def get_hod(self,AttendanceApprovalRequest):
        if AttendanceApprovalRequest.attendance:
            name = AttendanceApprovalRequest.attendance.employee.cu_user.hod.first_name+' '+AttendanceApprovalRequest.attendance.employee.cu_user.hod.last_name if AttendanceApprovalRequest.attendance.employee.cu_user.hod else None
            return name
    def get_company(self, AttendanceApprovalRequest):
        if AttendanceApprovalRequest.attendance:
            company = AttendanceApprovalRequest.attendance.employee.cu_user.company.coc_name if AttendanceApprovalRequest.attendance.employee.cu_user.company else ''
            return company

    def get_documents(self, obj):
        leave_type = obj.leave_type_changed if obj.leave_type_changed else obj.leave_type
        return get_documents(request=self.context['request'],attendance_request=obj) if leave_type == 'AL' or leave_type == 'AB' else list()

    class Meta:
        model = AttendanceApprovalRequest
        fields = '__all__'
        extra_fields=('employee_name','employee_id','department','designation','department_id', 'designation_id',
                      'company_id', 'company','reporting_head','hod', 'documents')


class ETaskAttendanceApprovalGraceListSerializer(serializers.ModelSerializer):
    employee_name=serializers.SerializerMethodField(required=False)
    employee_id=serializers.SerializerMethodField(required=False) 
    def get_employee_name(self,AttendanceApprovalRequest):
        if AttendanceApprovalRequest.attendance:
            first_name=AttendanceApprovalRequest.attendance.employee.first_name if AttendanceApprovalRequest.attendance.employee.first_name  else ''
            last_name=AttendanceApprovalRequest.attendance.employee.last_name if AttendanceApprovalRequest.attendance.employee.last_name else ''
            name=first_name+" "+last_name
            return name
    def get_employee_id(self,AttendanceApprovalRequest):
        if AttendanceApprovalRequest.attendance:
            return AttendanceApprovalRequest.attendance.employee.id
    class Meta:
        model = AttendanceApprovalRequest
        fields = '__all__'
        extra_fields=('employee_name','employee_id')


class ETaskAttendanceApprovaWithoutGracelSerializer(serializers.ModelSerializer):
    employee_name=serializers.SerializerMethodField(required=False)
    employee_id=serializers.SerializerMethodField(required=False) 
    def get_employee_name(self,AttendanceApprovalRequest):
        if AttendanceApprovalRequest.attendance:
            first_name=AttendanceApprovalRequest.attendance.employee.first_name if AttendanceApprovalRequest.attendance.employee.first_name  else ''
            last_name=AttendanceApprovalRequest.attendance.employee.last_name if AttendanceApprovalRequest.attendance.employee.last_name else ''
            name=first_name+" "+last_name
            return name
    def get_employee_id(self,AttendanceApprovalRequest):
        if AttendanceApprovalRequest.attendance:
            return AttendanceApprovalRequest.attendance.employee.id
    class Meta:
        model = AttendanceApprovalRequest
        fields = '__all__'
        extra_fields=('employee_name','employee_id')


class ETaskAttendanceApprovaWithoutGracelSerializerV2(serializers.ModelSerializer):
    employee_name=serializers.SerializerMethodField(required=False)
    employee_id=serializers.SerializerMethodField(required=False)
    documents=serializers.SerializerMethodField(required=False)
    work_form_home=serializers.SerializerMethodField(required=False)

    def get_work_form_home(self, obj):
        work_form_home = WorkFromHomeDeviation.objects.filter(request=obj, is_deleted=False).values('start_date_time', 'end_date_time', 'work_done')
        return work_form_home

    def get_employee_name(self,AttendanceApprovalRequest):
        if AttendanceApprovalRequest.attendance:
            first_name=AttendanceApprovalRequest.attendance.employee.first_name if AttendanceApprovalRequest.attendance.employee.first_name  else ''
            last_name=AttendanceApprovalRequest.attendance.employee.last_name if AttendanceApprovalRequest.attendance.employee.last_name else ''
            name=first_name+" "+last_name
            return name
    def get_employee_id(self,AttendanceApprovalRequest):
        if AttendanceApprovalRequest.attendance:
            return AttendanceApprovalRequest.attendance.employee.id

    def get_documents(self, obj):
        leave_type = obj.leave_type_changed if obj.leave_type_changed else obj.leave_type
        return get_documents(request=self.context['request'],attendance_request=obj) if leave_type == 'AL' or leave_type == 'AB' else list()

    class Meta:
        model = AttendanceApprovalRequest
        fields = '__all__'
        extra_fields=('employee_name','employee_id', 'documents', 'work_form_home')


class ETaskAttendanceApprovalSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    attendence_approvals=serializers.ListField(required=False)
    
    class Meta:
        model = AttendanceApprovalRequest
        fields = ('id','updated_by','remarks','approved_status','attendence_approvals')
        # extra_fields=('attendence_approvals')

    def create(self,validated_data):
        '''
            ~~~~FEATURES~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            //////////////////////////////////////////////////////////////////////////
            >>>) Admin can provide mass update by selecting as much request he wanted 
                1)Approved
                2)Reject
                3)Release
            1) >>>APPROVED LEAVES,GRACE,MP,OD ON BLUK AS WELL AS SINGLE DATA 
            
            2) >>>REJECT LEAVE AND REQUEST TYPE CALCULATION:-
                1)REJECTED GRACE,OD,MP CALCULATION
                    #IF REQUEST DURATION CROSS 240min REJECTED REQUEST WILL BE 
                        CONVERTED TO "FD" AND "AB"
                    #IF REQUEST DURATION LESS THAN 240min REJECTED REQUEST WILL BE 
                        CONVERTED TO "HD" AND "AB"
                2)REJECTED LEAVES CALCULATION
                    #IF REQUEST LEAVES REJECTED REQUEST(FD,FOD) WILL BE 
                        CONVERTED TO "FD" AND "AB"
                    #IF REQUEST LEAVES REJECTED REQUEST(HD,POD) WILL BE 
                        CONVERTED TO "HD" AND "AB"
                2)MULTIPLE LEAVE FOR ONE DAY IS AUTO CONVERTED TO ONE TYPE OF LEAVE 
            3) >>>RELEASE LEAVE AND REQUEST TYPE 
            
            EDITED BY :- Abhishek.singh@shyamfuture.com
            //////////////////////////////////////////////////////////////////////////
            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~END~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        '''

        print(validated_data)
        updated_by = validated_data.get('updated_by')
        remarks = validated_data.get('remarks')
        # master_module_role = TMasterModuleRoleUser.objects.get(mmr_module__cm_name__iexact='hrms',mmr_user=self.context['request'].user).mmr_role
        # core_role = TCoreRole.objects.get(id=str(master_module_role)).cr_name
        for data in validated_data.get('attendence_approvals'):
            approved_status= data['approved_status']
            cur_date = datetime.datetime.now()
            
            if approved_status=='approved':
                approved_data = AttendanceApprovalRequest.objects.filter(id=data['req_id']).update(approved_status=approved_status,
                                                                        approved_by=updated_by,remarks=remarks)
                req_type = AttendanceApprovalRequest.objects.get(id=data['req_id']).request_type
                print("approved_data",approved_data,req_type)
                present_data = Attendance.objects.filter(id__in=AttendanceApprovalRequest.objects.filter(
                                        (Q(request_type='MP')|Q(request_type='FOD')),id=data['req_id']).values_list('attendance')
                                        ).update(is_present=True,day_remarks='Present')
                
                # if core_role.lower() == 'hr admin' and approved_data:
                if approved_data:
                    logger.log(self.context['request'].user,'approved'+" "+req_type,
                    'Approval','pending','Approved','HRMS-TeamAttendance -AttendenceApproval') 
                # elif approved_data:
                #     logger.log(self.context['request'].user,AttendenceAction.ACTION_HR,'approved'+" "+req_type,
                #     'Approval','pending','Approved','HRMS-TeamAttendance -AttendenceApproval')

                # if core_role.lower() == 'hr admin' and miss_punch_data:
                #     logger.log(self.context['request'].user,AttendenceAction.ACTION_ADMIN,'approved'+" "+req_type,
                #     'Approval','pending','Approved','HRMS-TeamAttendance -AttendenceApproval')
                # elif core_role.lower() == 'hr user' and miss_punch_data:
                #     logger.log(self.context['request'].user,AttendenceAction.ACTION_HR,'approved'+" "+req_type,
                #     'Approval','pending','Approved','HRMS-TeamAttendance -AttendenceApproval')

            elif approved_status=='reject':
                print("approved_status")
                if AttendanceApprovalRequest.objects.filter(id=data['req_id'],request_type='GR') :
                    # print("grace ")

                    duration_length=AttendanceApprovalRequest.objects.get(id=data['req_id'],is_requested=True)
                    #missing req type
                    prev_cal = AttendanceApprovalRequest.objects.filter(attendance=duration_length.attendance,is_requested=True,approved_status='reject')
                    reject_duration_sum_value = prev_cal.aggregate(Sum('duration'))['duration__sum']
                    rejected_ids = prev_cal.values('id')
                    # print('reject_sum_value',reject_duration_sum_value,'rejected_ids',rejected_ids)
                    # print("prev_cal",prev_cal)
                    # print("duration_length",duration_length)
                    if prev_cal:
                        # print("entered ")
                        ids =[x['id'] for x in rejected_ids] 
                        # print("ids",ids,duration_length.duration + reject_duration_sum_value)
                        if duration_length.duration + reject_duration_sum_value >= 240:
                            AttendanceApprovalRequest.objects.filter(id=data['req_id'],request_type='GR').update(approved_status=approved_status,
                                                                approved_by=updated_by,remarks=remarks,
                                                                leave_type_changed_period='FD',leave_type_changed='AB',approved_at=cur_date)
                            for x in ids:
                                AttendanceApprovalRequest.objects.filter(id=x).update(
                                                                    approved_by=updated_by,
                                                                    leave_type_changed_period='FD',leave_type_changed='AB',approved_at=cur_date)

                        else:
                            AttendanceApprovalRequest.objects.filter(id=data['req_id'],request_type='GR').update(approved_status=approved_status,
                                                                    approved_by=updated_by,remarks=remarks,
                                                                    leave_type_changed_period='HD',leave_type_changed='AB',approved_at=cur_date)
                    else:
                        if duration_length.duration < 240:

                            AttendanceApprovalRequest.objects.filter(id=data['req_id'],request_type='GR').update(approved_status=approved_status,
                                                                    approved_by=updated_by,remarks=remarks,
                                                                    leave_type_changed_period='HD',leave_type_changed='AB',approved_at=cur_date)
                        else:
                            AttendanceApprovalRequest.objects.filter(id=data['req_id'],request_type='GR').update(approved_status=approved_status,
                                                                    approved_by=updated_by,remarks=remarks,
                                                                    leave_type_changed_period='FD',leave_type_changed='AB',approved_at=cur_date)
                elif AttendanceApprovalRequest.objects.filter((Q(request_type='FD')                                           
                                                            |Q(request_type='FOD')),
                                                            id=data['req_id']) :
                    
                    # print("full day ")
                    AttendanceApprovalRequest.objects.filter((Q(request_type='FD')                                                 
                                                            |Q(request_type='FOD'))
                                                            ,id=data['req_id']).\
                                                            update(approved_status=approved_status,approved_by=updated_by,remarks=remarks,
                                                            leave_type_changed_period='FD',leave_type_changed='AB',approved_at=cur_date)

                elif AttendanceApprovalRequest.objects.filter((Q(request_type='HD')|Q(request_type='OD')                    
                                                            |Q(request_type='POD')|Q(request_type='MP')),
                                                            id=data['req_id']) :
                    # print("halfday day ")
                    duration_length=AttendanceApprovalRequest.objects.get(id=data['req_id'],is_requested=True)
                    prev_cal = AttendanceApprovalRequest.objects.filter(attendance=duration_length.attendance,is_requested=True,approved_status='reject')
                    reject_duration_sum_value = prev_cal.aggregate(Sum('duration'))['duration__sum']
                    rejected_ids = prev_cal.values('id')
                    # print('reject_sum_value',reject_duration_sum_value,'rejected_ids',rejected_ids)
                    # print("prev_cal",prev_cal)
                    # print("duration_length",duration_length)
                    if prev_cal:
                        # print("entered ")
                        ids =[x['id'] for x in rejected_ids] 
                        # print("ids",ids)
                        if duration_length.duration + reject_duration_sum_value >= 240:
                            AttendanceApprovalRequest.objects.filter((Q(request_type='HD')|Q(request_type='OD')                
                                                                    |Q(request_type='POD')|Q(request_type='MP'))
                                                                    ,id=data['req_id']).update(approved_status=approved_status,
                                                                approved_by=updated_by,remarks=remarks,
                                                                leave_type_changed_period='FD',leave_type_changed='AB',approved_at=cur_date)
                            for x in ids:
                                AttendanceApprovalRequest.objects.filter(id=x).update(
                                                                    approved_by=updated_by,
                                                                    leave_type_changed_period='FD',leave_type_changed='AB',approved_at=cur_date)
                        else:
                            AttendanceApprovalRequest.objects.filter((Q(request_type='HD')|Q(request_type='OD')                
                                                                    |Q(request_type='POD')|Q(request_type='MP'))
                                                                    ,id=data['req_id']).\
                                                                    update(approved_status=approved_status,approved_by=updated_by,remarks=remarks,
                                                                    leave_type_changed_period='HD',leave_type_changed='AB',approved_at=cur_date)
                    else:
                        # print("duration_length",duration_length)
                        if duration_length.duration < 240:
                            AttendanceApprovalRequest.objects.filter((Q(request_type='HD')|Q(request_type='OD')                
                                                                    |Q(request_type='POD')|Q(request_type='MP'))
                                                                    ,id=data['req_id']).\
                                                                    update(approved_status=approved_status,approved_by=updated_by,remarks=remarks,
                                                                    leave_type_changed_period='HD',leave_type_changed='AB',approved_at=cur_date)
                        else:
                            AttendanceApprovalRequest.objects.filter((Q(request_type='HD')|Q(request_type='OD')                
                                                                    |Q(request_type='POD')|Q(request_type='MP'))
                                                                    ,id=data['req_id']).\
                                                                    update(approved_status=approved_status,approved_by=updated_by,remarks=remarks,
                                                                    leave_type_changed_period='FD',leave_type_changed='AB',approved_at=cur_date)

                req_type = AttendanceApprovalRequest.objects.get(id=data['req_id']).request_type

                # if core_role.lower() == 'hr admin' and approved_data:
                logger.log(self.context['request'].user,'rejected'+" "+req_type,
                    'Approval','pending','Rejected','HRMS-TeamAttendance-AttendenceApproval') 
                # elif core_role.lower() == 'hr user' and approved_data:
                #     logger.log(self.context['request'].user,AttendenceAction.ACTION_HR,'rejected'+" "+req_type,
                #     'Approval','pending','Rejected','HRMS-TeamAttendance-AttendenceApproval')

                # if core_role.lower() == 'hr admin' and miss_punch_data:
                #     logger.log(request.user,AttendenceAction.ACTION_ADMIN,'rejected'+" "+req_type,
                #     'Approval','UnApproved','Approved','HRMS-AttendenceApproval-ConveyenceApprovals')
                # elif core_role.lower() == 'hr user' and approved_data:
                #     logger.log(request.user,AttendenceAction.ACTION_HR,'rejected'+" "+req_type,
                #     'Approval','UnApproved','Approved','HRMS-AttendenceApproval-ConveyenceApprovals')

                ######################### MAIL SEND ################################
                mp_detail = AttendanceApprovalRequest.objects.filter(Q(request_type='MP'), id=data['req_id'])
                od_detail = AttendanceApprovalRequest.objects.filter((Q(request_type='OD')
                                                            |Q(request_type='FOD')|Q(request_type='POD')), id=data['req_id'])
                if mp_detail:
                    print("AAAAA", userdetails(mp_detail.values()[0]['justified_by_id']))
                    full_name = userdetails(mp_detail.values()[0]['justified_by_id'])
                    date = (mp_detail.values()[0]['duration_start']).date()
                    rejected_by = userdetails(updated_by.id)
                    rejected_at = cur_date
                    email = mp_detail.values_list('attendance__employee__email',flat=True)[0]

                    # ============= Mail Send ============== #
                    if email:
                        mail_data = {
                                    "name": full_name,
                                    "date": date,
                                    "rejected_by": rejected_by,
                                    "rejected_date": cur_date.date()
                            }
                        print('mail_data',mail_data)
                        mail_class = GlobleMailSend('MP_reject', [email])
                        mail_thread = Thread(target = mail_class.mailsend, args = (mail_data,))
                        mail_thread.start()

                if od_detail:
                    full_name = userdetails(od_detail.values()[0]['justified_by_id'])
                    date = (od_detail.values()[0]['duration_start']).date()
                    rejected_by = userdetails(updated_by.id)
                    rejected_at = cur_date
                    email = od_detail.values_list('attendance__employee__email',flat=True)[0]

                    # ============= Mail Send ============== #
                    if email:
                        mail_data = {
                                    "name": full_name,
                                    "date": date,
                                    "rejected_by": rejected_by,
                                    "rejected_date": cur_date.date()
                            }
                        print('mail_data',mail_data)
                        mail_class = GlobleMailSend('OD_reject', [email])
                        mail_thread = Thread(target = mail_class.mailsend, args = (mail_data,))
                        mail_thread.start()
                ###########################################

                

            elif approved_status=='relese':
                req_type = AttendanceApprovalRequest.objects.get(id=data['req_id'])
                before_data = req_type.approved_status
                AttendanceApprovalRequest.objects.filter(id=data['req_id']).update(
                    approved_status=approved_status,
                    justification=None,
                    approved_by=updated_by,
                    remarks=remarks,
                    request_type=None,
                    is_requested=False,
                    leave_type = None,
                    leave_type_changed = None,
                    leave_type_changed_period = None
                    )
        
                # if core_role.lower() == 'hr admin' and approved_data:
                logger.log(self.context['request'].user,'rejected'+" "+req_type.request_type,
                    'Approval',before_data,'Relese','HRMS-TeamAttendance-AttendenceApproval') 
                # elif core_role.lower() == 'hr user' and approved_data:
                #     logger.log(self.context['request'].user,AttendenceAction.ACTION_HR,'rejected'+" "+req_type.request_type,
                #     'Approval',before_data,'Relese','HRMS-TeamAttendance-AttendenceApproval')

        data = validated_data

        return data
    

class ETaskAttendanceApprovalSerializerV2(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    attendence_approvals=serializers.ListField(required=False)
    
    class Meta:
        model = AttendanceApprovalRequest
        fields = ('id','updated_by','remarks','approved_status','attendence_approvals')
        # extra_fields=('attendence_approvals')

    def create(self,validated_data):
        '''
            ~~~~FEATURES~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            //////////////////////////////////////////////////////////////////////////
            >>>) Admin can provide mass update by selecting as much request he wanted 
                1)Approved
                2)Reject
                3)Release
            1) >>>APPROVED LEAVES,GRACE,MP,OD ON BLUK AS WELL AS SINGLE DATA 
            
            2) >>>REJECT LEAVE AND REQUEST TYPE CALCULATION:-
                1)REJECTED GRACE,MP CALCULATION
                    #IF REQUEST DURATION CROSS 240min REJECTED REQUEST WILL BE 
                        CONVERTED TO "FD" AND "AB"
                    #IF REQUEST DURATION LESS THAN 240min REJECTED REQUEST WILL BE 
                        CONVERTED TO "HD" AND "AB"
                2)REJECTED LEAVES CALCULATION
                    #IF REQUEST LEAVES REJECTED REQUEST(FD,FOD) WILL BE 
                        CONVERTED TO "FD" AND "AB"
                    #IF REQUEST LEAVES REJECTED REQUEST(HD,POD) WILL BE 
                        CONVERTED TO "HD" AND "AB"
                3)MULTIPLE LEAVE FOR ONE DAY IS AUTO CONVERTED TO ONE TYPE OF LEAVE
                4) REJECTED OD CALCULATION
                    #IF REQUEST DURATION CROSS 240min REJECTED REQUEST WILL BE 
                        CONVERTED TO "FD" AND "AL" IF LEAVE AVAILABLE THEN "AB"
                    #IF REQUEST DURATION LESS THAN 240min REJECTED REQUEST WILL BE 
                        CONVERTED TO "HD" AND "AL" IF LEAVE AVAILABLE THEN "AB"
            3) >>>RELEASE LEAVE AND REQUEST TYPE 
            
            EDITED BY :- Abhishek.singh@shyamfuture.com
            //////////////////////////////////////////////////////////////////////////
            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~END~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        '''

        #print(validated_data)
        updated_by = validated_data.get('updated_by')
        remarks = validated_data.get('remarks')
        # master_module_role = TMasterModuleRoleUser.objects.get(mmr_module__cm_name__iexact='hrms',mmr_user=self.context['request'].user).mmr_role
        # core_role = TCoreRole.objects.get(id=str(master_module_role)).cr_name
        for data in validated_data.get('attendence_approvals'):
            approved_status = data['approved_status']

            ## Emergency added for request type P ## As per Change Request Document - Attendance & HRMS -CR-3 | Date : 19-06-2020 | Rupam Hazra ##
            approved_data_check = AttendanceApprovalRequest.objects.only('request_type').get(id=data['req_id']).request_type
            #print('approved_data_check',approved_data_check)
            if approved_data_check == "P" and approved_status == 'reject':
                approved_status = 'relese'


            cur_date = datetime.datetime.now()
            
            if approved_status=='approved':
                approved_data = AttendanceApprovalRequest.objects.filter(id=data['req_id']).update(approved_status=approved_status,
                                                                        approved_by=updated_by,remarks=remarks)
                req_type = AttendanceApprovalRequest.objects.get(id=data['req_id']).request_type
                print("approved_data",approved_data,req_type)
                present_data = Attendance.objects.filter(id__in=AttendanceApprovalRequest.objects.filter(
                                        (Q(request_type='MP')|Q(request_type='FOD')),id=data['req_id']).values_list('attendance')
                                        ).update(is_present=True,day_remarks='Present')
                
                # if core_role.lower() == 'hr admin' and approved_data:
                # if approved_data:
                #     logger.log(self.context['request'].user,'approved'+" "+req_type,
                #     'Approval','pending','Approved','HRMS-TeamAttendance -AttendenceApproval') 
                # elif approved_data:
                #     logger.log(self.context['request'].user,AttendenceAction.ACTION_HR,'approved'+" "+req_type,
                #     'Approval','pending','Approved','HRMS-TeamAttendance -AttendenceApproval')

                # if core_role.lower() == 'hr admin' and miss_punch_data:
                #     logger.log(self.context['request'].user,AttendenceAction.ACTION_ADMIN,'approved'+" "+req_type,
                #     'Approval','pending','Approved','HRMS-TeamAttendance -AttendenceApproval')
                # elif core_role.lower() == 'hr user' and miss_punch_data:
                #     logger.log(self.context['request'].user,AttendenceAction.ACTION_HR,'approved'+" "+req_type,
                #     'Approval','pending','Approved','HRMS-TeamAttendance -AttendenceApproval')

            elif approved_status=='reject':
                print("approved_status")
                if AttendanceApprovalRequest.objects.filter(id=data['req_id'],request_type='GR') :
                    # print("grace ")

                    duration_length=AttendanceApprovalRequest.objects.get(id=data['req_id'],is_requested=True)
                    #missing req type
                    prev_cal = AttendanceApprovalRequest.objects.filter(attendance=duration_length.attendance,is_requested=True,approved_status='reject')
                    reject_duration_sum_value = prev_cal.aggregate(Sum('duration'))['duration__sum']
                    rejected_ids = prev_cal.values('id')
                    # print('reject_sum_value',reject_duration_sum_value,'rejected_ids',rejected_ids)
                    # print("prev_cal",prev_cal)
                    # print("duration_length",duration_length)
                    if prev_cal:
                        # print("entered ")
                        ids =[x['id'] for x in rejected_ids] 
                        # print("ids",ids,duration_length.duration + reject_duration_sum_value)
                        if duration_length.duration + reject_duration_sum_value >= 240:
                            AttendanceApprovalRequest.objects.filter(id=data['req_id'],request_type='GR').update(approved_status=approved_status,
                                                                approved_by=updated_by,remarks=remarks,
                                                                leave_type_changed_period='FD',leave_type_changed='AB',approved_at=cur_date)
                            for x in ids:
                                AttendanceApprovalRequest.objects.filter(id=x).update(
                                                                    approved_by=updated_by,
                                                                    leave_type_changed_period='FD',leave_type_changed='AB',approved_at=cur_date)

                        else:
                            AttendanceApprovalRequest.objects.filter(id=data['req_id'],request_type='GR').update(approved_status=approved_status,
                                                                    approved_by=updated_by,remarks=remarks,
                                                                    leave_type_changed_period='HD',leave_type_changed='AB',approved_at=cur_date)
                    else:
                        if duration_length.duration < 240:

                            AttendanceApprovalRequest.objects.filter(id=data['req_id'],request_type='GR').update(approved_status=approved_status,
                                                                    approved_by=updated_by,remarks=remarks,
                                                                    leave_type_changed_period='HD',leave_type_changed='AB',approved_at=cur_date)
                        else:
                            AttendanceApprovalRequest.objects.filter(id=data['req_id'],request_type='GR').update(approved_status=approved_status,
                                                                    approved_by=updated_by,remarks=remarks,
                                                                    leave_type_changed_period='FD',leave_type_changed='AB',approved_at=cur_date)
                
                elif AttendanceApprovalRequest.objects.filter((Q(request_type='FOD')),id=data['req_id']) :
                    
                    
                    fod_attendance_request = AttendanceApprovalRequest.objects.filter((Q(request_type='FOD'))
                                                            ,id=data['req_id'])
                    
                    tcore_user = TCoreUserDetail.objects.get(cu_user=fod_attendance_request[0].attendance.employee)
                    calculated_balance = all_leave_calculation_upto_applied_date(date_object=fod_attendance_request[0].attendance_date, 
                                                                               user=tcore_user)
                    
                    advance_leave_calculation = advance_leave_calculation_excluding_current_month(tcore_user=tcore_user, date_object=fod_attendance_request[0].attendance_date)
                    print('advance_leave_calculation', advance_leave_calculation)

                    actual_balance = calculated_balance['total_available_balance'] + advance_leave_calculation['advance_leave_balance']
                    leave_type_changed = 'AB'
                    if calculated_balance['total_available_balance'] >=1.0:
                        if advance_leave_calculation['is_advance_leave_taken'] and advance_leave_calculation['is_leave_taken_from_current_month'] and actual_balance <=0:
                            leave_type_changed = 'AB'
                        else:
                            leave_type_changed = 'AL'
                    else:
                        leave_type_changed = 'AB'
                    # leave_type_changed = 'AL' if calculated_balance['total_available_balance'] >=1.0 else 'AB'
                    
                    fod_attendance_request.update(approved_status=approved_status,approved_by=updated_by,remarks=remarks,
                                                        leave_type_changed_period='FD',leave_type_changed=leave_type_changed,approved_at=cur_date)

                    ## Start Change Request Document__Attendance & HRMS (Conveyence Management) -CR-2 - V 1.2_Approved | Date: 08-07-2020 | Rupam Hazra ##
                    ConveyanceMaster.objects.filter(request_id=data['req_id'],is_deleted=False).update(status='Reject')
                    ## End Change Request Document__Attendance & HRMS (Conveyence Management) -CR-2 - V 1.2_Approved | Date: 08-07-2020 | Rupam Hazra ##

                elif AttendanceApprovalRequest.objects.filter((Q(request_type='FD')),id=data['req_id']) :
                    
                    # print("full day ")
                    AttendanceApprovalRequest.objects.filter((Q(request_type='FD'))
                                                            ,id=data['req_id']).\
                                                            update(approved_status=approved_status,approved_by=updated_by,remarks=remarks,
                                                            leave_type_changed_period='FD',leave_type_changed='AB',approved_at=cur_date)
                
                elif AttendanceApprovalRequest.objects.filter((Q(request_type='OD')|Q(request_type='POD')|Q(request_type='WFH')),id=data['req_id']) :
                    # print("halfday day ")
                    duration_length=AttendanceApprovalRequest.objects.get(id=data['req_id'],is_requested=True)
                    prev_cal = AttendanceApprovalRequest.objects.filter(attendance=duration_length.attendance,is_requested=True,approved_status='reject')
                    reject_duration_sum_value = prev_cal.aggregate(Sum('duration'))['duration__sum']
                    rejected_ids = prev_cal.values('id')
                    if prev_cal:
                        # print("entered ")
                        ids =[x['id'] for x in rejected_ids] 
                        # print("ids",ids)
                        if duration_length.duration + reject_duration_sum_value >= 240:
                            attendance_request = AttendanceApprovalRequest.objects.filter((Q(request_type='OD')                
                                                                    |Q(request_type='POD')|Q(request_type='WFH'))
                                                                    ,id=data['req_id'])

                            tcore_user = TCoreUserDetail.objects.get(cu_user=attendance_request[0].attendance.employee)
                            calculated_balance = all_leave_calculation_upto_applied_date(date_object=attendance_request[0].attendance_date, 
                                                                                        user=tcore_user)        
                                    
                            advance_leave_calculation = advance_leave_calculation_excluding_current_month(tcore_user=tcore_user, date_object=attendance_request[0].attendance_date)
                            print('advance_leave_calculation', advance_leave_calculation)

                            actual_balance = calculated_balance['total_available_balance'] + advance_leave_calculation['advance_leave_balance']
                            leave_type_changed = 'AB'
                            if calculated_balance['total_available_balance'] >=1.0:
                                if advance_leave_calculation['is_advance_leave_taken'] and advance_leave_calculation['is_leave_taken_from_current_month'] and actual_balance <=0:
                                    leave_type_changed = 'AB'
                                else:
                                    leave_type_changed = 'AL'
                            else:
                                leave_type_changed = 'AB'
                            
                            # leave_type_changed = 'AL' if calculated_balance['total_available_balance'] >=1.0 else 'AB'
                        
                            attendance_request.update(approved_status=approved_status,
                                                        approved_by=updated_by,remarks=remarks,
                                                        leave_type_changed_period='FD',leave_type_changed=leave_type_changed,approved_at=cur_date)
                            for x in ids:
                                AttendanceApprovalRequest.objects.filter(id=x).update(
                                                        approved_by=updated_by,
                                                        leave_type_changed_period='FD',leave_type_changed=leave_type_changed,approved_at=cur_date)
                        else:
                            attendance_request = AttendanceApprovalRequest.objects.filter((Q(request_type='OD')                
                                                                    |Q(request_type='POD')|Q(request_type='WFH'))
                                                                    ,id=data['req_id'])
                            tcore_user = TCoreUserDetail.objects.get(cu_user=attendance_request[0].attendance.employee)
                            calculated_balance = all_leave_calculation_upto_applied_date(date_object=attendance_request[0].attendance_date, 
                                                                                        user=tcore_user)
                                    
                            advance_leave_calculation = advance_leave_calculation_excluding_current_month(tcore_user=tcore_user, date_object=attendance_request[0].attendance_date)
                            print('advance_leave_calculation', advance_leave_calculation)

                            actual_balance = calculated_balance['total_available_balance'] + advance_leave_calculation['advance_leave_balance']
                            leave_type_changed = 'AB'
                            if calculated_balance['total_available_balance'] >=0.5:
                                if advance_leave_calculation['is_advance_leave_taken'] and advance_leave_calculation['is_leave_taken_from_current_month'] and actual_balance <=0:
                                    leave_type_changed = 'AB'
                                else:
                                    leave_type_changed = 'AL'
                            else:
                                leave_type_changed = 'AB'
                            # leave_type_changed = 'AL' if calculated_balance['total_available_balance'] >= 0.5 else 'AB'

                            attendance_request.update(approved_status=approved_status,approved_by=updated_by,remarks=remarks,
                                                        leave_type_changed_period='HD',leave_type_changed=leave_type_changed,approved_at=cur_date)
                    else:
                        # print("duration_length",duration_length)
                        if duration_length.duration < 240:
                            attendance_request = AttendanceApprovalRequest.objects.filter((Q(request_type='OD')                
                                                                    |Q(request_type='POD')|Q(request_type='WFH'))
                                                                    ,id=data['req_id'])

                            tcore_user = TCoreUserDetail.objects.get(cu_user=attendance_request[0].attendance.employee)
                            calculated_balance = all_leave_calculation_upto_applied_date(date_object=attendance_request[0].attendance_date, 
                                                                                        user=tcore_user)
        
                            advance_leave_calculation = advance_leave_calculation_excluding_current_month(tcore_user=tcore_user, date_object=attendance_request[0].attendance_date)
                            print('advance_leave_calculation', advance_leave_calculation)

                            actual_balance = calculated_balance['total_available_balance'] + advance_leave_calculation['advance_leave_balance']
                            leave_type_changed = 'AB'
                            if calculated_balance['total_available_balance'] >=0.5:
                                if advance_leave_calculation['is_advance_leave_taken'] and advance_leave_calculation['is_leave_taken_from_current_month'] and actual_balance <=0:
                                    leave_type_changed = 'AB'
                                else:
                                    leave_type_changed = 'AL'
                            else:
                                leave_type_changed = 'AB'
                            # leave_type_changed = 'AL' if calculated_balance['total_available_balance'] >= 0.5 else 'AB'

                            attendance_request.update(approved_status=approved_status,approved_by=updated_by,remarks=remarks,
                                                        leave_type_changed_period='HD',leave_type_changed=leave_type_changed,approved_at=cur_date)
                        else:
                            attendance_request = AttendanceApprovalRequest.objects.filter((Q(request_type='OD')                
                                                                    |Q(request_type='POD')|Q(request_type='WFH'))
                                                                    ,id=data['req_id'])
                            tcore_user = TCoreUserDetail.objects.get(cu_user=attendance_request[0].attendance.employee)
                            calculated_balance = all_leave_calculation_upto_applied_date(date_object=attendance_request[0].attendance_date, 
                                                                                        user=tcore_user)
                            
                            advance_leave_calculation = advance_leave_calculation_excluding_current_month(tcore_user=tcore_user, date_object=attendance_request[0].attendance_date)
                            print('advance_leave_calculation', advance_leave_calculation)

                            actual_balance = calculated_balance['total_available_balance'] + advance_leave_calculation['advance_leave_balance']
                            leave_type_changed = 'AB'
                            if calculated_balance['total_available_balance'] >=1.0:
                                if advance_leave_calculation['is_advance_leave_taken'] and advance_leave_calculation['is_leave_taken_from_current_month'] and actual_balance <=0:
                                    leave_type_changed = 'AB'
                                else:
                                    leave_type_changed = 'AL'
                            else:
                                leave_type_changed = 'AB'
                            # leave_type_changed = 'AL' if calculated_balance['total_available_balance'] >= 1.0 else 'AB'

                            attendance_request.update(approved_status=approved_status,approved_by=updated_by,remarks=remarks,
                                                        leave_type_changed_period='FD',leave_type_changed=leave_type_changed,approved_at=cur_date)

                    ## Start Change Request Document__Attendance & HRMS (Conveyence Management) -CR-2 - V 1.2_Approved | Date: 08-07-2020 | Rupam Hazra ##
                    ConveyanceMaster.objects.filter(request_id=data['req_id'],is_deleted=False).update(status='Reject')
                    ## End Change Request Document__Attendance & HRMS (Conveyence Management) -CR-2 - V 1.2_Approved | Date: 08-07-2020 | Rupam Hazra ##


                elif AttendanceApprovalRequest.objects.filter((Q(request_type='HD')|Q(request_type='MP')),id=data['req_id']) :
                    # print("halfday day ")
                    duration_length=AttendanceApprovalRequest.objects.get(id=data['req_id'],is_requested=True)
                    prev_cal = AttendanceApprovalRequest.objects.filter(attendance=duration_length.attendance,is_requested=True,approved_status='reject')
                    reject_duration_sum_value = prev_cal.aggregate(Sum('duration'))['duration__sum']
                    rejected_ids = prev_cal.values('id')
                    # print('reject_sum_value',reject_duration_sum_value,'rejected_ids',rejected_ids)
                    # print("prev_cal",prev_cal)
                    # print("duration_length",duration_length)
                    if prev_cal:
                        # print("entered ")
                        ids =[x['id'] for x in rejected_ids] 
                        # print("ids",ids)
                        if duration_length.duration + reject_duration_sum_value >= 240:
                            AttendanceApprovalRequest.objects.filter((Q(request_type='HD')|Q(request_type='MP'))
                                                                    ,id=data['req_id']).update(approved_status=approved_status,
                                                                approved_by=updated_by,remarks=remarks,
                                                                leave_type_changed_period='FD',leave_type_changed='AB',approved_at=cur_date)
                            for x in ids:
                                AttendanceApprovalRequest.objects.filter(id=x).update(
                                                                    approved_by=updated_by,
                                                                    leave_type_changed_period='FD',leave_type_changed='AB',approved_at=cur_date)
                        else:
                            AttendanceApprovalRequest.objects.filter((Q(request_type='HD')|Q(request_type='MP'))
                                                                    ,id=data['req_id']).\
                                                                    update(approved_status=approved_status,approved_by=updated_by,remarks=remarks,
                                                                    leave_type_changed_period='HD',leave_type_changed='AB',approved_at=cur_date)
                    else:
                        # print("duration_length",duration_length)
                        if duration_length.duration < 240:
                            AttendanceApprovalRequest.objects.filter((Q(request_type='HD')|Q(request_type='MP'))
                                                                    ,id=data['req_id']).\
                                                                    update(approved_status=approved_status,approved_by=updated_by,remarks=remarks,
                                                                    leave_type_changed_period='HD',leave_type_changed='AB',approved_at=cur_date)
                        else:
                            AttendanceApprovalRequest.objects.filter((Q(request_type='HD')|Q(request_type='MP'))
                                                                    ,id=data['req_id']).\
                                                                    update(approved_status=approved_status,approved_by=updated_by,remarks=remarks,
                                                                    leave_type_changed_period='FD',leave_type_changed='AB',approved_at=cur_date)

                req_type = AttendanceApprovalRequest.objects.get(id=data['req_id']).request_type

                # if core_role.lower() == 'hr admin' and approved_data:
                # logger.log(self.context['request'].user,'rejected'+" "+req_type,
                #     'Approval','pending','Rejected','HRMS-TeamAttendance-AttendenceApproval') 
                # elif core_role.lower() == 'hr user' and approved_data:
                #     logger.log(self.context['request'].user,AttendenceAction.ACTION_HR,'rejected'+" "+req_type,
                #     'Approval','pending','Rejected','HRMS-TeamAttendance-AttendenceApproval')

                # if core_role.lower() == 'hr admin' and miss_punch_data:
                #     logger.log(request.user,AttendenceAction.ACTION_ADMIN,'rejected'+" "+req_type,
                #     'Approval','UnApproved','Approved','HRMS-AttendenceApproval-ConveyenceApprovals')
                # elif core_role.lower() == 'hr user' and approved_data:
                #     logger.log(request.user,AttendenceAction.ACTION_HR,'rejected'+" "+req_type,
                #     'Approval','UnApproved','Approved','HRMS-AttendenceApproval-ConveyenceApprovals')

                ######################### MAIL SEND ################################
                mp_detail = AttendanceApprovalRequest.objects.filter(Q(request_type='MP'), id=data['req_id'])
                od_detail = AttendanceApprovalRequest.objects.filter((Q(request_type='OD')
                                                            |Q(request_type='FOD')|Q(request_type='POD')), id=data['req_id'])
                if mp_detail:
                    print("AAAAA", userdetails(mp_detail.values()[0]['justified_by_id']))
                    full_name = userdetails(mp_detail.values()[0]['justified_by_id'])
                    date = (mp_detail.values()[0]['duration_start']).date()
                    rejected_by = userdetails(updated_by.id)
                    rejected_at = cur_date
                    email = mp_detail.values_list('attendance__employee__email',flat=True)[0]

                    # ============= Mail Send ============== #
                    if email:
                        mail_data = {
                                    "name": full_name,
                                    "date": date,
                                    "rejected_by": rejected_by,
                                    "rejected_date": cur_date.date()
                            }
                        print('mail_data',mail_data)
                        mail_class = GlobleMailSend('MP_reject', [email])
                        mail_thread = Thread(target = mail_class.mailsend, args = (mail_data,))
                        mail_thread.start()

                if od_detail:
                    full_name = userdetails(od_detail.values()[0]['justified_by_id'])
                    date = (od_detail.values()[0]['duration_start']).date()
                    rejected_by = userdetails(updated_by.id)
                    rejected_at = cur_date
                    email = od_detail.values_list('attendance__employee__email',flat=True)[0]

                    # ============= Mail Send ============== #
                    if email:
                        mail_data = {
                                    "name": full_name,
                                    "date": date,
                                    "rejected_by": rejected_by,
                                    "rejected_date": cur_date.date()
                            }
                        print('mail_data',mail_data)
                        mail_class = GlobleMailSend('OD_reject', [email])
                        mail_thread = Thread(target = mail_class.mailsend, args = (mail_data,))
                        mail_thread.start()
                ###########################################

            elif approved_status=='relese':
                req_type = AttendanceApprovalRequest.objects.get(id=data['req_id'])
                before_data = req_type.approved_status
                AttendanceApprovalRequest.objects.filter(id=data['req_id']).update(
                    approved_status=approved_status,
                    justification=None,
                    approved_by=updated_by,
                    remarks=remarks,
                    request_type=None,
                    is_requested=False,
                    leave_type = None,
                    leave_type_changed = None,
                    leave_type_changed_period = None,
                    is_conveyance=False,
                    conveyance_approval=None,
                    conveyance_approved_by=None,
                    vehicle_type=None,
                    conveyance_purpose=None,
                    conveyance_alloted_by=None,
                    from_place=None,
                    to_place=None,
                    conveyance_expense=None,
                    approved_expenses=None,
                    conveyance_remarks=None
                    )
                WorkFromHomeDeviation.objects.filter(request=data['req_id'], is_deleted=False).update(
                    is_deleted=True
                )
                AttandanceApprovalDocuments.objects.filter(request=data['req_id'], is_deleted=False).update(
                    is_deleted=True
                )

                ## Start Change Request Document__Attendance & HRMS (Conveyence Management) -CR-2 - V 1.2_Approved | Date: 23-06-2020 | Rupam Hazra ##

                ConveyanceMaster.objects.filter(request=data['req_id'], is_deleted=False).update(is_deleted=True,updated_by=updated_by)
                
                ## End Change Request Document__Attendance & HRMS (Conveyence Management) -CR-2 - V 1.2_Approved | Date: 23-06-2020 | Rupam Hazra ##


                # if core_role.lower() == 'hr admin' and approved_data:
                # logger.log(self.context['request'].user,'rejected'+" "+req_type.request_type,
                #     'Approval',before_data,'Relese','HRMS-TeamAttendance-AttendenceApproval') 
                # elif core_role.lower() == 'hr user' and approved_data:
                #     logger.log(self.context['request'].user,AttendenceAction.ACTION_HR,'rejected'+" "+req_type.request_type,
                #     'Approval',before_data,'Relese','HRMS-TeamAttendance-AttendenceApproval')

        data = validated_data

        return data


class ETaskAttendanceApprovalModifySerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    attendence_approvals=serializers.ListField(required=False)
    
    class Meta:
        model = AttendanceApprovalRequest
        fields = ('id','updated_by','remarks','approved_status','attendence_approvals')
        # extra_fields=('attendence_approvals')

    def leave_calulate(self,request_id):
        total_grace={}
        # date_object = datetime.now().date()
        
        ################################

        req_details = AttendanceApprovalRequest.objects.get(id=request_id,is_requested=True)

        # request_month = req_details.duration_start.month
        request_date = req_details.duration_start.date()
        print("request_date",request_date, req_details.duration_start)
        total_month_grace=AttendenceMonthMaster.objects.filter(month_start__date__lte=request_date,
                                        month_end__date__gte=request_date,is_deleted=False).values(
                                        'year_start_date','year_end_date','month','month_start__date','month_end__date')
        # print("total_month_grace",total_month_grace)

        employee_id = req_details.attendance.employee
        print('employee_id',employee_id)

        last_attendance = Attendance.objects.filter(employee=employee_id).values_list('date__date',flat=True).order_by('-date')[:1]
        print("last_attendance",last_attendance)
        last_attendance = last_attendance[0] if last_attendance else date_object
        print('last_attendance',last_attendance)
        date_object = last_attendance
        #################################

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

    def leave_type_return(self,leave_details,req_type):
        cl_balance = leave_details['cl_balance']
        el_balance = leave_details['el_balance']
        # sl_balance = leave_details['sl_balance']
        is_confirm = leave_details['is_confirm']
        leave_type = None
        if req_type=='HD':
            if cl_balance>=0.5:
                leave_type = 'CL'
            elif is_confirm is True and el_balance>=0.5:
                leave_type = 'EL'
            else:
                leave_type = 'AB'
        elif req_type=='FD':
            if cl_balance>=1.0:
                leave_type = 'CL'
            elif is_confirm is True and el_balance>=1.0:
                leave_type = 'EL'
            else:
                leave_type = 'AB'

        return leave_type

    def create(self,validated_data):
        '''
            ~~~~FEATURES~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            //////////////////////////////////////////////////////////////////////////
            >>>) Admin can provide mass update by selecting as much request he wanted 
                1)Approved
                2)Reject
                3)Release
            1) >>>APPROVED LEAVES,GRACE,MP,OD ON BLUK AS WELL AS SINGLE DATA 
            
            2) >>>REJECT LEAVE AND REQUEST TYPE CALCULATION:-
                1)REJECTED GRACE,OD,MP CALCULATION
                    #IF REQUEST DURATION CROSS 240min REJECTED REQUEST WILL BE 
                        CONVERTED TO "FD" AND "AB"
                    #IF REQUEST DURATION LESS THAN 240min REJECTED REQUEST WILL BE 
                        CONVERTED TO "HD" AND "AB"
                2)REJECTED LEAVES CALCULATION
                    #IF REQUEST LEAVES REJECTED REQUEST(FD,FOD) WILL BE 
                        CONVERTED TO "FD" AND "AB"
                    #IF REQUEST LEAVES REJECTED REQUEST(HD,POD) WILL BE 
                        CONVERTED TO "HD" AND "AB"
                2)MULTIPLE LEAVE FOR ONE DAY IS AUTO CONVERTED TO ONE TYPE OF LEAVE 
            3) >>>RELEASE LEAVE AND REQUEST TYPE 
            
            EDITED BY :- Abhishek.singh@shyamfuture.com
            //////////////////////////////////////////////////////////////////////////
            >>>) As per discussion with Shailendra Sir & Tonmoy Da on 24/01/2020:-
                1)Reject >>1. Grace
                           2. POD/FOD
                           3. MP
                Action:- check LEAVE balance >> CL >> EL & is_confirm >> AB
            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~END~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        '''

        print(validated_data)
        updated_by = validated_data.get('updated_by')
        remarks = validated_data.get('remarks')
        # master_module_role = TMasterModuleRoleUser.objects.get(mmr_module__cm_name__iexact='hrms',mmr_user=self.context['request'].user).mmr_role
        # core_role = TCoreRole.objects.get(id=str(master_module_role)).cr_name
        for data in validated_data.get('attendence_approvals'):
            approved_status= data['approved_status']
            cur_date = datetime.datetime.now()
            
            if approved_status=='approved':
                approved_data = AttendanceApprovalRequest.objects.filter(id=data['req_id']).update(approved_status=approved_status,
                                                                        approved_by=updated_by,remarks=remarks)
                req_type = AttendanceApprovalRequest.objects.get(id=data['req_id']).request_type
                print("approved_data",approved_data,req_type)
                present_data = Attendance.objects.filter(id__in=AttendanceApprovalRequest.objects.filter(
                                        (Q(request_type='MP')|Q(request_type='FOD')),id=data['req_id']).values_list('attendance')
                                        ).update(is_present=True,day_remarks='Present')
                
                # if core_role.lower() == 'hr admin' and approved_data:
                if approved_data:
                    logger.log(self.context['request'].user,'approved'+" "+req_type,
                    'Approval','pending','Approved','HRMS-TeamAttendance -AttendenceApproval') 
                # elif approved_data:
                #     logger.log(self.context['request'].user,AttendenceAction.ACTION_HR,'approved'+" "+req_type,
                #     'Approval','pending','Approved','HRMS-TeamAttendance -AttendenceApproval')

                # if core_role.lower() == 'hr admin' and miss_punch_data:
                #     logger.log(self.context['request'].user,AttendenceAction.ACTION_ADMIN,'approved'+" "+req_type,
                #     'Approval','pending','Approved','HRMS-TeamAttendance -AttendenceApproval')
                # elif core_role.lower() == 'hr user' and miss_punch_data:
                #     logger.log(self.context['request'].user,AttendenceAction.ACTION_HR,'approved'+" "+req_type,
                #     'Approval','pending','Approved','HRMS-TeamAttendance -AttendenceApproval')

            elif approved_status=='reject':
                print("approved_status")
                leave_details = self.leave_calulate(data['req_id'])
                print("leave_details",leave_details)
                lev_type_FD = self.leave_type_return(leave_details,'FD')
                lev_type_HD = self.leave_type_return(leave_details,'HD')
                print("lev_type",lev_type_FD, 'lev_type_HD', lev_type_HD)
                
                if AttendanceApprovalRequest.objects.filter(id=data['req_id'],request_type='GR'):
                    print("grace ")

                    duration_length=AttendanceApprovalRequest.objects.get(id=data['req_id'],is_requested=True)
                    prev_cal = AttendanceApprovalRequest.objects.filter(attendance=duration_length.attendance,is_requested=True,approved_status='reject')
                    reject_duration_sum_value = prev_cal.aggregate(Sum('duration'))['duration__sum']
                    rejected_ids = prev_cal.values('id')
                    # print('reject_sum_value',reject_duration_sum_value,'rejected_ids',rejected_ids)
                    # print("prev_cal",prev_cal)
                    # print("duration_length",duration_length)
                    if prev_cal:
                        # print("entered ")
                        ids =[x['id'] for x in rejected_ids] 
                        # print("ids",ids,duration_length.duration + reject_duration_sum_value)
                        if duration_length.duration + reject_duration_sum_value >= 240:
                            AttendanceApprovalRequest.objects.filter(id=data['req_id'],request_type='GR').update(approved_status=approved_status,
                                                                approved_by=updated_by,remarks=remarks,
                                                                leave_type_changed_period='FD',leave_type_changed=lev_type_FD,approved_at=cur_date)
                            for x in ids:
                                AttendanceApprovalRequest.objects.filter(id=x).update(
                                                                    approved_by=updated_by,
                                                                    leave_type_changed_period='FD',leave_type_changed=lev_type_FD,approved_at=cur_date)

                        else:
                            AttendanceApprovalRequest.objects.filter(id=data['req_id'],request_type='GR').update(approved_status=approved_status,
                                                                    approved_by=updated_by,remarks=remarks,
                                                                    leave_type_changed_period='HD',leave_type_changed=lev_type_HD,approved_at=cur_date)
                    else:
                        if duration_length.duration < 240:

                            AttendanceApprovalRequest.objects.filter(id=data['req_id'],request_type='GR').update(approved_status=approved_status,
                                                                    approved_by=updated_by,remarks=remarks,
                                                                    leave_type_changed_period='HD',leave_type_changed=lev_type_HD,approved_at=cur_date)
                        else:
                            AttendanceApprovalRequest.objects.filter(id=data['req_id'],request_type='GR').update(approved_status=approved_status,
                                                                    approved_by=updated_by,remarks=remarks,
                                                                    leave_type_changed_period='FD',leave_type_changed=lev_type_FD,approved_at=cur_date)
                # elif AttendanceApprovalRequest.objects.filter((Q(request_type='FD')                                           
                #                                             |Q(request_type='FOD')),
                #                                             id=data['req_id']) :
                    
                #     # print("full day ")
                #     AttendanceApprovalRequest.objects.filter((Q(request_type='FD')                                                 
                #                                             |Q(request_type='FOD'))
                #                                             ,id=data['req_id']).\
                #                                             update(approved_status=approved_status,approved_by=updated_by,remarks=remarks,
                #                                             leave_type_changed_period='FD',leave_type_changed='AB',approved_at=cur_date)

                elif AttendanceApprovalRequest.objects.filter(request_type='FD',id=data['req_id']):
                    
                    # print("full day ")
                    AttendanceApprovalRequest.objects.filter(request_type='FD',id=data['req_id']).\
                                                            update(approved_status=approved_status,approved_by=updated_by,remarks=remarks,
                                                            leave_type_changed_period='FD',leave_type_changed='AB',approved_at=cur_date)

                elif AttendanceApprovalRequest.objects.filter(request_type='FOD',id=data['req_id']) :
                    
                    # print("full day ")
                    AttendanceApprovalRequest.objects.filter(request_type='FOD',id=data['req_id']).\
                                                            update(approved_status=approved_status,approved_by=updated_by,remarks=remarks,
                                                            leave_type_changed_period='FD',leave_type_changed=lev_type_FD,approved_at=cur_date)

                elif AttendanceApprovalRequest.objects.filter((Q(request_type='HD')|Q(request_type='OD')                    
                                                            |Q(request_type='POD')|Q(request_type='MP')),
                                                            id=data['req_id']) :
                    # print("halfday day ")
                    duration_length=AttendanceApprovalRequest.objects.get(id=data['req_id'],is_requested=True)
                    prev_cal = AttendanceApprovalRequest.objects.filter(attendance=duration_length.attendance,is_requested=True,approved_status='reject')
                    reject_duration_sum_value = prev_cal.aggregate(Sum('duration'))['duration__sum']
                    rejected_ids = prev_cal.values('id')
                    # print('reject_sum_value',reject_duration_sum_value,'rejected_ids',rejected_ids)
                    # print("prev_cal",prev_cal)
                    # print("duration_length",duration_length)
                    if prev_cal:
                        # print("entered ")
                        ids =[x['id'] for x in rejected_ids] 
                        # print("ids",ids)
                        if duration_length.duration + reject_duration_sum_value >= 240:
                            AttendanceApprovalRequest.objects.filter((Q(request_type='HD')|Q(request_type='OD')                
                                                                    |Q(request_type='POD')|Q(request_type='MP'))
                                                                    ,id=data['req_id']).update(approved_status=approved_status,
                                                                approved_by=updated_by,remarks=remarks,
                                                                leave_type_changed_period='FD',leave_type_changed=lev_type_FD,approved_at=cur_date)
                            for x in ids:
                                AttendanceApprovalRequest.objects.filter(id=x).update(
                                                                    approved_by=updated_by,
                                                                    leave_type_changed_period='FD',leave_type_changed=lev_type_FD,approved_at=cur_date)
                        else:
                            AttendanceApprovalRequest.objects.filter((Q(request_type='OD')                
                                                                    |Q(request_type='POD')|Q(request_type='MP'))
                                                                    ,id=data['req_id']).\
                                                                    update(approved_status=approved_status,approved_by=updated_by,remarks=remarks,
                                                                    leave_type_changed_period='HD',leave_type_changed=lev_type_HD,approved_at=cur_date)

                            AttendanceApprovalRequest.objects.filter(request_type='HD',id=data['req_id']).\
                                                                    update(approved_status=approved_status,approved_by=updated_by,remarks=remarks,
                                                                    leave_type_changed_period='HD',leave_type_changed='AB',approved_at=cur_date)
                    else:
                        # print("duration_length",duration_length)
                        if duration_length.duration < 240:
                            AttendanceApprovalRequest.objects.filter((Q(request_type='OD')|Q(request_type='POD')|Q(request_type='MP'))
                                                                    ,id=data['req_id']).\
                                                                    update(approved_status=approved_status,approved_by=updated_by,remarks=remarks,
                                                                    leave_type_changed_period='HD',leave_type_changed=lev_type_HD,approved_at=cur_date)

                            AttendanceApprovalRequest.objects.filter(request_type='HD',id=data['req_id']).\
                                                                    update(approved_status=approved_status,approved_by=updated_by,remarks=remarks,
                                                                    leave_type_changed_period='HD',leave_type_changed='AB',approved_at=cur_date)
                        else:
                            AttendanceApprovalRequest.objects.filter((Q(request_type='OD')|Q(request_type='POD')|Q(request_type='MP')),id=data['req_id']).\
                                                                    update(approved_status=approved_status,approved_by=updated_by,remarks=remarks,
                                                                    leave_type_changed_period='FD',leave_type_changed=lev_type_FD,approved_at=cur_date)

                            AttendanceApprovalRequest.objects.filter(request_type='HD',id=data['req_id']).\
                                                                    update(approved_status=approved_status,approved_by=updated_by,remarks=remarks,
                                                                    leave_type_changed_period='FD',leave_type_changed='AB',approved_at=cur_date)

                req_type = AttendanceApprovalRequest.objects.get(id=data['req_id']).request_type

                # if core_role.lower() == 'hr admin' and approved_data:
                logger.log(self.context['request'].user,'rejected'+" "+req_type,
                    'Approval','pending','Rejected','HRMS-TeamAttendance-AttendenceApproval') 
                # elif core_role.lower() == 'hr user' and approved_data:
                #     logger.log(self.context['request'].user,AttendenceAction.ACTION_HR,'rejected'+" "+req_type,
                #     'Approval','pending','Rejected','HRMS-TeamAttendance-AttendenceApproval')

                # if core_role.lower() == 'hr admin' and miss_punch_data:
                #     logger.log(request.user,AttendenceAction.ACTION_ADMIN,'rejected'+" "+req_type,
                #     'Approval','UnApproved','Approved','HRMS-AttendenceApproval-ConveyenceApprovals')
                # elif core_role.lower() == 'hr user' and approved_data:
                #     logger.log(request.user,AttendenceAction.ACTION_HR,'rejected'+" "+req_type,
                #     'Approval','UnApproved','Approved','HRMS-AttendenceApproval-ConveyenceApprovals')

                ######################### MAIL SEND ################################
                mp_detail = AttendanceApprovalRequest.objects.filter(Q(request_type='MP'), id=data['req_id'])
                od_detail = AttendanceApprovalRequest.objects.filter((Q(request_type='OD')
                                                            |Q(request_type='FOD')|Q(request_type='POD')), id=data['req_id'])
                if mp_detail:
                    print("AAAAA", userdetails(mp_detail.values()[0]['justified_by_id']))
                    full_name = userdetails(mp_detail.values()[0]['justified_by_id'])
                    date = (mp_detail.values()[0]['duration_start']).date()
                    rejected_by = userdetails(updated_by.id)
                    rejected_at = cur_date
                    email = mp_detail.values_list('attendance__employee__email',flat=True)[0]

                    # ============= Mail Send ============== #
                    if email:
                        mail_data = {
                                    "name": full_name,
                                    "date": date,
                                    "rejected_by": rejected_by,
                                    "rejected_date": cur_date.date()
                            }
                        print('mail_data',mail_data)
                        mail_class = GlobleMailSend('MP_reject', [email])
                        mail_thread = Thread(target = mail_class.mailsend, args = (mail_data,))
                        mail_thread.start()

                if od_detail:
                    full_name = userdetails(od_detail.values()[0]['justified_by_id'])
                    date = (od_detail.values()[0]['duration_start']).date()
                    rejected_by = userdetails(updated_by.id)
                    rejected_at = cur_date
                    email = od_detail.values_list('attendance__employee__email',flat=True)[0]

                    # ============= Mail Send ============== #
                    if email:
                        mail_data = {
                                    "name": full_name,
                                    "date": date,
                                    "rejected_by": rejected_by,
                                    "rejected_date": cur_date.date()
                            }
                        print('mail_data',mail_data)
                        mail_class = GlobleMailSend('OD_reject', [email])
                        mail_thread = Thread(target = mail_class.mailsend, args = (mail_data,))
                        mail_thread.start()
                ###########################################

                

            elif approved_status=='relese':
                req_type = AttendanceApprovalRequest.objects.get(id=data['req_id'])
                before_data = req_type.approved_status
                AttendanceApprovalRequest.objects.filter(id=data['req_id']).update(approved_status=approved_status,justification=None,
                                                                        approved_by=updated_by,remarks=remarks,request_type=None,is_requested=False)
        
                # if core_role.lower() == 'hr admin' and approved_data:
                logger.log(self.context['request'].user,'rejected'+" "+req_type.request_type,
                    'Approval',before_data,'Relese','HRMS-TeamAttendance-AttendenceApproval') 
                # elif core_role.lower() == 'hr user' and approved_data:
                #     logger.log(self.context['request'].user,AttendenceAction.ACTION_HR,'rejected'+" "+req_type.request_type,
                #     'Approval',before_data,'Relese','HRMS-TeamAttendance-AttendenceApproval')

        data = validated_data

        return data
    

class AttendanceVehicleTypeMasterAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = VehicleTypeMaster
        fields = ('id', 'name', 'description', 'created_by', 'owned_by')


class AttendanceVehicleTypeMasterEditSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = VehicleTypeMaster
        fields = ('id', 'name', 'description', 'updated_by')


class AttendanceVehicleTypeMasterDeleteSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = VehicleTypeMaster
        fields = '__all__'
    def update(self, instance, validated_data):
        instance.is_deleted=True
        instance.updated_by = validated_data.get('updated_by')
        instance.save()
        return instance


class AttendanceAdminSummaryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = '__all__'


class AttendanceAdminSummaryListSerializerV2(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = '__all__'


class AttendanceAdminDailyListSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Attendance
        fields = '__all__'


class AttendanceAdminDailyListSerializerV2(serializers.ModelSerializer):
    
    class Meta:
        model = Attendance
        fields = '__all__'


class AttendanceFileUploadOldVersionSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = AttandancePerDayDocuments
        fields = '__all__'

    def create(self, validated_data):
        try:
            attendance_file = AttandancePerDayDocuments.objects.create(**validated_data)
            print('attendance_file: ', attendance_file)
            return attendance_file
        except Exception as e:
            raise APIException({"msg": e, "request_status": 0})


class AttendanceFileUploadSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = AttandancePerDayDocuments
        fields = '__all__'

    def create(self, validated_data):
        try:
            attendance_file = AttandancePerDayDocuments.objects.create(**validated_data)
            print('attendance_file: ', attendance_file)
            return attendance_file
        except Exception as e:
            raise APIException({"msg": e, "request_status": 0})


class AttendanceFileUploadSerializerV2(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = AttandancePerDayDocuments
        fields = '__all__'

    def create(self, validated_data):
        try:
            attendance_file = AttandancePerDayDocuments.objects.create(**validated_data)
            print('attendance_file: ', attendance_file)
            return attendance_file
        except Exception as e:
            raise APIException({"msg": e, "request_status": 0})


class AttendanceFileUploadFlexiHourSerializerV2(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = AttandancePerDayDocuments
        fields = '__all__'

    def create(self, validated_data):
        try:
            attendance_file = AttandancePerDayDocuments.objects.create(**validated_data)
            print('attendance_file: ', attendance_file)
            return attendance_file
        except Exception as e:
            raise APIException({"msg": e, "request_status": 0})


class AttendanceLeaveApprovalListSerializer(serializers.ModelSerializer):
    employee_name=serializers.SerializerMethodField(required=False)
    employee_id=serializers.SerializerMethodField(required=False)
    department = serializers.SerializerMethodField(required=False)
    designation = serializers.SerializerMethodField(required=False)
    reporting_head = serializers.SerializerMethodField(required=False)
    
    hod = serializers.SerializerMethodField(required=False)
    def get_employee_name(self,AttendanceApprovalRequest):
        if AttendanceApprovalRequest.attendance:
            first_name=AttendanceApprovalRequest.attendance.employee.first_name if AttendanceApprovalRequest.attendance.employee.first_name  else ''
            last_name=AttendanceApprovalRequest.attendance.employee.last_name if AttendanceApprovalRequest.attendance.employee.last_name else ''
            name=first_name+" "+last_name
            return name
    def get_employee_id(self,AttendanceApprovalRequest):
        if AttendanceApprovalRequest.attendance:
            return AttendanceApprovalRequest.attendance.employee.id

    def get_department(self,AttendanceApprovalRequest):
        if AttendanceApprovalRequest.attendance:
            return AttendanceApprovalRequest.attendance.employee.cu_user.department.cd_name if AttendanceApprovalRequest.attendance.employee.cu_user.department else None
    
    def get_designation(self,AttendanceApprovalRequest):
        if AttendanceApprovalRequest.attendance:
            return AttendanceApprovalRequest.attendance.employee.cu_user.designation.cod_name if AttendanceApprovalRequest.attendance.employee.cu_user.designation else None

    def get_reporting_head(self,AttendanceApprovalRequest):
        if AttendanceApprovalRequest.attendance:
            return AttendanceApprovalRequest.attendance.employee.cu_user.reporting_head.first_name+' '+AttendanceApprovalRequest.attendance.employee.cu_user.reporting_head.last_name if AttendanceApprovalRequest.attendance.employee.cu_user.reporting_head else None

    def get_hod(self,AttendanceApprovalRequest):
        if AttendanceApprovalRequest.attendance:
            name = AttendanceApprovalRequest.attendance.employee.cu_user.hod.first_name+' '+AttendanceApprovalRequest.attendance.employee.cu_user.hod.last_name if AttendanceApprovalRequest.attendance.employee.cu_user.hod else None
            return name

    class Meta:
        model = AttendanceApprovalRequest
        fields = '__all__'
        extra_fields=('employee_name','employee_id','department','designation','reporting_head','hod')



class AttendanceLeaveApprovalListSerializerV2(serializers.ModelSerializer):
    employee_name=serializers.SerializerMethodField(required=False)
    employee_id=serializers.SerializerMethodField(required=False)
    department = serializers.SerializerMethodField(required=False)
    designation = serializers.SerializerMethodField(required=False)
    reporting_head = serializers.SerializerMethodField(required=False)
    hod = serializers.SerializerMethodField(required=False)
    documents=serializers.SerializerMethodField(required=False)

    def get_employee_name(self,AttendanceApprovalRequest):
        if AttendanceApprovalRequest.attendance:
            first_name=AttendanceApprovalRequest.attendance.employee.first_name if AttendanceApprovalRequest.attendance.employee.first_name  else ''
            last_name=AttendanceApprovalRequest.attendance.employee.last_name if AttendanceApprovalRequest.attendance.employee.last_name else ''
            name=first_name+" "+last_name
            return name
    def get_employee_id(self,AttendanceApprovalRequest):
        if AttendanceApprovalRequest.attendance:
            return AttendanceApprovalRequest.attendance.employee.id

    def get_department(self,AttendanceApprovalRequest):
        if AttendanceApprovalRequest.attendance:
            return AttendanceApprovalRequest.attendance.employee.cu_user.department.cd_name if AttendanceApprovalRequest.attendance.employee.cu_user.department else None
    
    def get_designation(self,AttendanceApprovalRequest):
        if AttendanceApprovalRequest.attendance:
            return AttendanceApprovalRequest.attendance.employee.cu_user.designation.cod_name if AttendanceApprovalRequest.attendance.employee.cu_user.designation else None

    def get_reporting_head(self,AttendanceApprovalRequest):
        if AttendanceApprovalRequest.attendance:
            return AttendanceApprovalRequest.attendance.employee.cu_user.reporting_head.first_name+' '+AttendanceApprovalRequest.attendance.employee.cu_user.reporting_head.last_name if AttendanceApprovalRequest.attendance.employee.cu_user.reporting_head else None

    def get_hod(self,AttendanceApprovalRequest):
        if AttendanceApprovalRequest.attendance:
            name = AttendanceApprovalRequest.attendance.employee.cu_user.hod.first_name+' '+AttendanceApprovalRequest.attendance.employee.cu_user.hod.last_name if AttendanceApprovalRequest.attendance.employee.cu_user.hod else None
            return name

    def get_documents(self, obj):
        leave_type = obj.leave_type_changed if obj.leave_type_changed else obj.leave_type
        return get_documents(request=self.context['request'],attendance_request=obj) if leave_type == 'AL' or leave_type == 'AB' else list()

    class Meta:
        model = AttendanceApprovalRequest
        fields = '__all__'
        extra_fields=('employee_name','employee_id','department','designation','reporting_head','hod', 'documents')
   


class AttendanceAdminMispunchCheckerSerializer(serializers.ModelSerializer):

    class Meta:
        model = AttendanceApprovalRequest
        fields = ('id','attendance','duration_start','duration_end','duration','request_type','justification','remarks','is_requested','lock_status',
        'is_late_conveyance','checkin_benchmark','approved_status','created_at')


class AttendanceAdminMispunchCheckerCSVReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceApprovalRequest
        fields = ('id','attendance','duration_start','duration_end','duration','request_type','justification','remarks','is_requested','lock_status',
        'is_late_conveyance','checkin_benchmark','approved_status','created_at')


class AttandanceAdminOdMsiReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceApprovalRequest
        fields = '__all__'


class AttandanceRequestFreeByHRListSerializer(serializers.ModelSerializer):
    employee_name=serializers.SerializerMethodField(required=False)
    employee_id=serializers.SerializerMethodField(required=False) 
    def get_employee_name(self,AttendanceApprovalRequest):
        if AttendanceApprovalRequest.attendance:
            first_name=AttendanceApprovalRequest.attendance.employee.first_name if AttendanceApprovalRequest.attendance.employee.first_name  else ''
            last_name=AttendanceApprovalRequest.attendance.employee.last_name if AttendanceApprovalRequest.attendance.employee.last_name else ''
            name=first_name+" "+last_name
            return name
    def get_employee_id(self,AttendanceApprovalRequest):
        if AttendanceApprovalRequest.attendance:
            return AttendanceApprovalRequest.attendance.employee.id
    class Meta:
        model = AttendanceApprovalRequest
        fields = '__all__'
        extra_fields=('employee_name','employee_id')


class AttendanceMonthlyHRListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = '__all__'


class AttendanceMonthlyHRListSerializerV2(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = '__all__'


#:::::::::::::::::::::: ATTENDANCE SPECIALDAY MASTER:::::::::::::::::::::::::::#
class AttendanceSpecialdayMasterAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = AttendanceSpecialdayMaster
        fields = ('id', 'day_start_time', 'day_end_time','day_type', 'full_day', 'remarks', 'created_by', 'owned_by')
    def create(self,validated_data):
        try:
            day_start_time=validated_data.get('day_start_time') if 'day_start_time' in validated_data else None
            day_end_time =validated_data.get('day_end_time') if 'day_end_time' in validated_data else None
            day_type =validated_data.get('day_type') if 'day_type' in validated_data else ''
            full_day =validated_data.get('full_day') if 'full_day' in validated_data else None
            remarks=validated_data.get('remarks') if 'remarks' in validated_data else ''
            created_by=validated_data.get('created_by')
            owned_by=validated_data.get('owned_by')
            filter={}
            if day_type == 1:
                filter['full_day']=full_day
            elif day_type == 2:
                filter['day_start_time']=day_start_time
            elif day_type == 3:
                filter['day_end_time']=day_end_time
            elif  day_type == 4:
                filter['day_start_time']=day_start_time
                filter['day_end_time']=day_end_time
            elif  day_type == 5:
                filter['day_start_time']=day_start_time
                filter['day_end_time']=day_end_time

            special_day=AttendanceSpecialdayMaster.objects.create(day_type=day_type,
                                                                **filter,
                                                                remarks=remarks,
                                                                created_by=created_by,
                                                                owned_by=owned_by
                                                                    )
            # print('special_day',special_day)
            return special_day

        except Exception as e:
            raise APIException({'msg':settings.MSG_ERROR,
                                'error':e,
                                "request_status": 0
                                })


class AttendanceSpecialdayMasterEditSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = AttendanceSpecialdayMaster
        fields = ('id', 'day_start_time', 'day_end_time','day_type','full_day', 'remarks', 'updated_by')
    def update(self,instance,validated_data):
        try:
            day_start_time=validated_data.get('day_start_time') if 'day_start_time' in validated_data else None
            day_end_time =validated_data.get('day_end_time') if 'day_end_time' in validated_data else None
            day_type =validated_data.get('day_type') if 'day_type' in validated_data else ''
            full_day =validated_data.get('full_day') if 'full_day' in validated_data else None
            remarks=validated_data.get('remarks') if 'remarks' in validated_data else ''
            updated_by=validated_data.get('updated_by')
            current_date=datetime.datetime.now().date()
            # print('day_start_time',day_start_time.date())
            data={}
            
            if day_type == 1:
                if current_date<=full_day.date():
                    instance.delete()
                    full_day=AttendanceSpecialdayMaster.objects.create(day_type=day_type,
                                                            full_day=full_day,
                                                            remarks=remarks,
                                                            updated_by=updated_by
                                                            )
                    data=full_day
            elif day_type == 2:
                if current_date<=day_start_time.date():
                    instance.delete()
                    day_start=AttendanceSpecialdayMaster.objects.create(day_type=day_type,
                                                            day_start_time=day_start_time,
                                                            remarks=remarks,
                                                            updated_by=updated_by
                                                            )
                    data=day_start
            elif day_type == 3:
                if current_date<=day_end_time.date():
                    instance.delete() 
                    day_end=AttendanceSpecialdayMaster.objects.create(day_type=day_type,
                                                            day_end_time=day_end_time,
                                                            remarks=remarks,
                                                            updated_by=updated_by
                                                            )
                    data=day_end                                        
            elif  day_type == 4:
                if  current_date<=day_start_time.date() or current_date<=day_end_time.date():
                    instance.delete()
                    start_and_end=AttendanceSpecialdayMaster.objects.create(day_type=day_type,
                                                            day_start_time=day_start_time,
                                                            day_end_time=day_end_time,
                                                            remarks=remarks,
                                                            updated_by=updated_by
                                                            )
                    data=start_and_end 
            
            elif  day_type == 5:
                if  current_date<=day_start_time.date() or current_date<=day_end_time.date():
                    instance.delete()
                    start_and_end=AttendanceSpecialdayMaster.objects.create(day_type=day_type,
                                                            day_start_time=day_start_time,
                                                            day_end_time=day_end_time,
                                                            remarks=remarks,
                                                            updated_by=updated_by
                                                            )
                    data=start_and_end 
                
            return data

        except Exception as e:
            # raise e
            raise APIException({'msg':settings.MSG_ERROR,
                                'error':e,
                                "request_status": 0
                                })

    
class AttendanceSpecialdayMasterDeleteSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = AttendanceSpecialdayMaster
        fields = '__all__'
    def update(self, instance, validated_data):
        instance.is_deleted=True
        instance.updated_by = validated_data.get('updated_by')
        instance.save()
        return instance


class AttendanceEmployeeReportSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = TCoreUserDetail
        fields = ('cu_emp_code','cu_user')


class logListSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendenceAction
        fields= '__all__'


class AttendanceFileUploadCheckSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = Attendance
        fields = '__all__'


class EmailSMSAlertForRequestApprovalSerializer(serializers.ModelSerializer):

    class Meta:
        model = Attendance
        fields = '__all__'


class EmailSMSAlertForRequestApprovalExcludingPresentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Attendance
        fields = '__all__'


class CwsReportSerializer(serializers.ModelSerializer):

    class Meta:
        model = Attendance
        fields = '__all__'


class UserLeaveReportSerializer(serializers.ModelSerializer):
    attendance = serializers.ReadOnlyField()

    class Meta:
        model = AttendanceApprovalRequest
        fields = ['id', 'attendance', 'attendance_date', 'leave_type',]


class YearlyLeaveBalanceCarryForwardSerializerV2(serializers.ModelSerializer):
    attendance = serializers.ReadOnlyField()

    class Meta:
        model = AttendanceApprovalRequest
        fields = ['id', 'attendance', 'attendance_date', 'leave_type',]


class AttendanceAdvanceLeaveAddV2Serializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    is_confirm = serializers.BooleanField(required=False)
    leave_confirm = serializers.BooleanField(required=False)
    leave_without_pay = serializers.DictField(required=False)
    leave = serializers.DictField(required=False)
    result = serializers.DictField(required=False)
    module = serializers.CharField(required=False)
    hr_panel = serializers.BooleanField(required=False, default=False)

    class Meta:
        model = EmployeeAdvanceLeaves
        fields = '__all__'
        extra_fields= ['is_confirm','leave_without_pay','leave','result','module']
   
    def create(self, validated_data):

        '''
            This Method prepared by @@ Rupam Hazra. Any kind of issues occurred, ask me first !!!

            Note :: 
            1) Used Date Format : yyyy-mm-dd
            2) Checking Start Date should not less than today's date!
            3) End Date should be greater than or euqual to start date!
            4) Checking if user want to apply more then 5 days then it has to be apply before 15 days.
            5) Check leave calculation by confirm or not
            6) You requested leaves has not been granted, due to insufficient EL/CL
            8) Normal Leave Count and Advance Leave Count From Approval Request Table
        '''
        # print('document:', type(validated_data.get('document')), validated_data.get('document'))

        request_datetime = validated_data.get('start_date').strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        request_datetime = datetime.datetime.strptime(request_datetime,"%Y-%m-%dT%H:%M:%S.%fZ").date()

        request_end_datetime = validated_data.get('end_date').strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        request_end_datetime = datetime.datetime.strptime(request_end_datetime,"%Y-%m-%dT%H:%M:%S.%fZ").date()

        module = validated_data.get('module') if 'module' in validated_data else 'HRMS'

        #print('validated_data111',validated_data)

        if validated_data.get("leave_type")=="AB":
            # absent_leaves_start_date = datetime.datetime.strptime(request_end_datetime, "%Y-%m-%dT%H:%M:%S.%fZ").date()
            EmployeeAdvanceLeaves.objects.create(
                employee=validated_data.get('employee'),
                leave_type='AB',
                start_date=request_datetime,
                end_date=request_end_datetime,
                document=validated_data.get('document'),
                reason=validated_data.get('reason'),
                created_by=validated_data.get('created_by'),
                owned_by=validated_data.get('created_by'),

            )
            validated_data["is_confirm"] = True
            return validated_data

        else:
            is_confirm = bool(validated_data.get('is_confirm'))
            # print('is_confirm',is_confirm, type(is_confirm))
            #return validated_data
            current_date = datetime.date.today()
            # print('current_date',current_date,type(current_date))
            current_date_15= current_date + datetime.timedelta(days=15)
            # print('current_date_15',current_date_15, type(current_date_15))
            
            balance_el = 0.0
            balance_ab = 0.0
            #how_many_days_el_taken = 0.0
            #how_many_days_ab_taken = 0.0
            balance_al = 0.0
            #how_many_days_al_taken = 0.0

            request_how_many_days = (validated_data.get('end_date') - validated_data.get('start_date')).days + 1
            # print('request_how_many_days',request_how_many_days)

            request_start_date_month = validated_data.get('start_date').strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            request_start_date_month = calendar.month_name[datetime.datetime.strptime(request_start_date_month,"%Y-%m-%dT%H:%M:%S.%fZ").month]
            
            # print('request_start_date_month',request_start_date_month)

            request_end_date_month = validated_data.get('end_date').strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            request_end_date_month = calendar.month_name[datetime.datetime.strptime(request_end_date_month,"%Y-%m-%dT%H:%M:%S.%fZ").month]
            
            # print('request_end_date_month',request_end_date_month)
            #print('request_datetime',request_datetime,type(request_datetime))

            if request_datetime < current_date :
                custom_exception_message(self,None,"Start Date should not less than today's date!")
            
            if request_datetime > request_end_datetime:
                custom_exception_message(self,None,"End Date should be greater than or euqual to start date!")
            
            if current_date_15 > request_datetime and request_how_many_days > 5:
                custom_exception_message(self,None,"Sorry!! to avail leaves of more than 5 days, need to apply at least 15 days in advance.")

            # userdetails from TCoreUserDetail
            empDetails_from_coreuserdetail = TCoreUserDetail.objects.filter(cu_user=validated_data.get('employee')).first()
            #print('empDetails_from_coreuserdetail',empDetails_from_coreuserdetail.cu_user)
            #employee_id = validated_data.get('employee')

            if empDetails_from_coreuserdetail:
                #print('module',module)
                if module == 'PMS':
                    result = all_leave_calculation_upto_applied_date_pms(request_datetime,empDetails_from_coreuserdetail)
                else:
                    result = all_leave_calculation_upto_applied_date(request_datetime,empDetails_from_coreuserdetail)

                balance_al = result['total_available_balance']
                balance_el = result['el_balance']
                balance_cl = result['cl_balance']
                
                # print('balance_al',balance_al)
                # print('balance_el',balance_el)
                # print('balance_cl',balance_cl)

                #raise APIException('sddds')

                if validated_data.get("leave_type") == 'AL':

                    # print('request_how_many_days',request_how_many_days)
                    # print('balance_al',balance_al)

                    if request_how_many_days > balance_al:
                        leaves = round_down(balance_al)
                        # print('leaves',leaves,type(leaves),round_down(balance_al))

                        leave_end_date_al = request_datetime + datetime.timedelta(days=(int(leaves)-1))
                        if round_down(balance_al) > 0:
                            leave_end_date = leave_end_date_al
                        else:
                            request_datetime = None
                            leave_end_date = leave_end_date_al
                            leave_end_date_al = None
                            
                            
                        absent_leaves = request_how_many_days - round_down(balance_al)
                        absent_leaves_start_date = leave_end_date + datetime.timedelta(days=1)
                        # print('leave',leaves,absent_leaves)

                        if is_confirm:
                            if round_down(balance_al) > 0:
                                EmployeeAdvanceLeaves.objects.create(
                                    employee = validated_data.get('employee'),
                                    leave_type = 'AL',
                                    start_date = request_datetime,
                                    end_date = leave_end_date,
                                    document = validated_data.get('document'),
                                    reason = validated_data.get('reason'),
                                    created_by = validated_data.get('created_by'),
                                    owned_by = validated_data.get('created_by'),
                                )
                            EmployeeAdvanceLeaves.objects.create(
                                employee = validated_data.get('employee'),
                                leave_type = 'AB',
                                start_date = absent_leaves_start_date,
                                end_date = request_end_datetime,
                                document = validated_data.get('document'),
                                reason = validated_data.get('reason'),
                                created_by = validated_data.get('created_by'),
                                owned_by = validated_data.get('created_by'),

                            )
                            validated_data["is_confirm"] = True
                            return validated_data
                        else:
                            return {
                                    'is_confirm':False,
                                    #'leave_confirm':False,
                                    'leave_without_pay':{
                                        'absent_leaves_count':absent_leaves,
                                        'start_date':absent_leaves_start_date,
                                        'end_date':request_end_datetime
                                    },
                                    'leave':{
                                        'leave_count':leaves,
                                        'start_date':request_datetime,
                                        'end_date':leave_end_date_al
                                    }
                                }
                    
                    else:
                        EmployeeAdvanceLeaves.objects.create(
                                employee = validated_data.get('employee'),
                                leave_type = 'AL',
                                start_date = request_datetime,
                                end_date = request_end_datetime,
                                document = validated_data.get('document'),
                                reason = validated_data.get('reason'),
                                created_by = validated_data.get('created_by'),
                                owned_by = validated_data.get('created_by'),
                            )
                        validated_data["is_confirm"] = True
                        
                if validated_data.get("leave_type") == 'CL':

                    if request_how_many_days > balance_cl:
                        leaves = round_down(balance_cl)
                        # print('leaves',leaves,type(leaves),round_down(balance_al))

                        leave_end_date_cl = request_datetime + datetime.timedelta(days=(int(leaves)-1))
                        if round_down(balance_cl) > 0:
                            leave_end_date = leave_end_date_cl
                        else:
                            request_datetime = None
                            leave_end_date = leave_end_date_cl
                            leave_end_date_cl = None
                            
                            
                        absent_leaves = request_how_many_days - round_down(balance_cl)
                        absent_leaves_start_date = leave_end_date + datetime.timedelta(days=1)
                        # print('leave',leaves,absent_leaves)

                        if is_confirm:
                            if round_down(balance_cl) > 0:
                                EmployeeAdvanceLeaves.objects.create(
                                    employee = validated_data.get('employee'),
                                    leave_type = 'CL',
                                    start_date = request_datetime,
                                    end_date = leave_end_date,
                                    document = validated_data.get('document'),
                                    reason = validated_data.get('reason'),
                                    created_by = validated_data.get('created_by'),
                                    owned_by = validated_data.get('created_by'),
                                )
                            EmployeeAdvanceLeaves.objects.create(
                                employee = validated_data.get('employee'),
                                leave_type = 'AB',
                                start_date = absent_leaves_start_date,
                                end_date = request_end_datetime,
                                document = validated_data.get('document'),
                                reason = validated_data.get('reason'),
                                created_by = validated_data.get('created_by'),
                                owned_by = validated_data.get('created_by'),

                            )
                            validated_data["is_confirm"] = True
                            return validated_data
                        else:
                            return {
                                    'is_confirm':False,
                                    #'leave_confirm':False,
                                    'leave_without_pay':{
                                        'absent_leaves_count':absent_leaves,
                                        'start_date':absent_leaves_start_date,
                                        'end_date':request_end_datetime
                                    },
                                    'leave':{
                                        'leave_count':leaves,
                                        'start_date':request_datetime,
                                        'end_date':leave_end_date_cl
                                    }
                                }
                    
                    else:
                        #print('asddsfdsfdfdsfsdf')
                        EmployeeAdvanceLeaves.objects.create(
                                employee = validated_data.get('employee'),
                                leave_type = 'CL',
                                start_date = request_datetime,
                                end_date = request_end_datetime,
                                document = validated_data.get('document'),
                                reason = validated_data.get('reason'),
                                created_by = validated_data.get('created_by'),
                                owned_by = validated_data.get('created_by'),
                            )
                        validated_data["is_confirm"] = True
                        
                if validated_data.get("leave_type") == 'EL':

                    if request_how_many_days > balance_el:
                        leaves = round_down(balance_el)
                        # print('leaves',leaves,type(leaves),round_down(balance_al))

                        leave_end_date_el = request_datetime + datetime.timedelta(days=(int(leaves)-1))
                        if round_down(balance_el) > 0:
                            leave_end_date = leave_end_date_el
                        else:
                            request_datetime = None
                            leave_end_date = leave_end_date_el
                            leave_end_date_el = None
                            
                            
                        absent_leaves = request_how_many_days - round_down(balance_el)
                        absent_leaves_start_date = leave_end_date + datetime.timedelta(days=1)
                        # print('leave',leaves,absent_leaves)

                        if is_confirm:
                            if round_down(balance_el) > 0:
                                EmployeeAdvanceLeaves.objects.create(
                                    employee = validated_data.get('employee'),
                                    leave_type = 'EL',
                                    start_date = request_datetime,
                                    end_date = leave_end_date,
                                    document = validated_data.get('document'),
                                    reason = validated_data.get('reason'),
                                    created_by = validated_data.get('created_by'),
                                    owned_by = validated_data.get('created_by'),
                                )
                            EmployeeAdvanceLeaves.objects.create(
                                employee = validated_data.get('employee'),
                                leave_type = 'AB',
                                start_date = absent_leaves_start_date,
                                end_date = request_end_datetime,
                                document = validated_data.get('document'),
                                reason = validated_data.get('reason'),
                                created_by = validated_data.get('created_by'),
                                owned_by = validated_data.get('created_by'),

                            )
                            validated_data["is_confirm"] = True
                            return validated_data
                        else:
                            return {
                                    'is_confirm':False,
                                    #'leave_confirm':False,
                                    'leave_without_pay':{
                                        'absent_leaves_count':absent_leaves,
                                        'start_date':absent_leaves_start_date,
                                        'end_date':request_end_datetime
                                    },
                                    'leave':{
                                        'leave_count':leaves,
                                        'start_date':request_datetime,
                                        'end_date':leave_end_date_el
                                    }
                                }
                    
                    else:
                        #print('asddsfdsfdfdsfsdf')
                        EmployeeAdvanceLeaves.objects.create(
                                employee = validated_data.get('employee'),
                                leave_type = 'EL',
                                start_date = request_datetime,
                                end_date = request_end_datetime,
                                document = validated_data.get('document'),
                                reason = validated_data.get('reason'),
                                created_by = validated_data.get('created_by'),
                                owned_by = validated_data.get('created_by'),
                            )
                        validated_data["is_confirm"] = True
                        
        return validated_data

class AttendanceSpecialLeaveAddV2Serializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = EmployeeSpecialLeaves
        fields = '__all__'
    
    def create(self, validated_data):

        '''
            This Method prepared by @@ Rupam Hazra. Any kind of issues occurred, ask me first !!!

            Note :: 
            1) Used Date Format : yyyy-mm-dd
            2) Checking Start Date should not less than today's date!
            3) End Date should be greater than or euqual to start date!
            
        '''


        # is_confirm = validated_data.get('is_confirm')
        # print('is_confirm',is_confirm)
        current_date = datetime.date.today()
        print('current_date',current_date,type(current_date))
        # current_date_15= current_date + datetime.timedelta(days=15)
        # print('current_date_15',current_date_15, type(current_date_15))
        employee_id = validated_data.get('employee')
        hr_panel = validated_data.pop('hr_panel')
        request_datetime = validated_data.get('start_date').strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        request_datetime = datetime.datetime.strptime(request_datetime, "%Y-%m-%dT%H:%M:%S.%fZ").date()

        request_end_datetime = validated_data.get('end_date').strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        request_end_datetime = datetime.datetime.strptime(request_end_datetime, "%Y-%m-%dT%H:%M:%S.%fZ").date()
        if employee_id and hr_panel :
            AttendanceApprovalRequest.objects.filter(attendance__employee_id=employee_id,
                                                     attendance_date__gte=request_datetime,
                                                     attendance_date__lte=request_end_datetime).update(is_deleted=True)
            AttendanceLog.objects.filter(attendance__employee_id=employee_id,
                                         attendance__date__gte=request_datetime,
                                         attendance__date__lte=request_end_datetime).update(is_deleted=True)
            Attendance.objects.filter(employee_id=employee_id,
                                      date__gte=request_datetime,
                                      date__lte=request_end_datetime).update(is_deleted=True)


        # if request_datetime < current_date :
        #     attendance_obj = AttendanceApprovalRequest.objects.filter(attendance_date__gte=request_datetime,
        #                                                               attendance_date__lte=request_end_datetime
        #                                                               )
        #     attendance_final_filter = attendance_obj.filter(approved_status__in=["Pending", "Approved"])
        #     if attendance_obj.count() != attendance_final_filter.count():
        #         custom_exception_message(self, None, "Start Date should not less than today's date!")



        # balance_el = 0.0
        # balance_ab = 0.0
        # how_many_days_el_taken = 0.0
        # how_many_days_ab_taken = 0.0
        # balance_al = 0.0
        # how_many_days_al_taken = 0.0

        # request_how_many_days = (validated_data.get('end_date') - validated_data.get('start_date')).days + 1
        # print('request_how_many_days',request_how_many_days)

        # request_start_date_month = validated_data.get('start_date').strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        # request_start_date_month = calendar.month_name[datetime.datetime.strptime(request_start_date_month,"%Y-%m-%dT%H:%M:%S.%fZ").month]
        
        # print('request_start_date_month',request_start_date_month)

        # request_end_date_month = validated_data.get('end_date').strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        # request_end_date_month = calendar.month_name[datetime.datetime.strptime(request_end_date_month,"%Y-%m-%dT%H:%M:%S.%fZ").month]
        
        # print('request_end_date_month',request_end_date_month)
        #print('request_datetime',request_datetime,type(request_datetime))

        #modified by swarup adhikary on 24-12-2020
        #modified by shubhadeep on 28-01-2021

        
        if request_datetime > request_end_datetime:
            custom_exception_message(self,None,"End Date should be greater than or euqual to start date!")

        return super().create(validated_data)


class FlexiAddAttendanceRequestSerializerV2(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = AttendanceApprovalRequest
        fields = '__all__'
    
    def create(self, validated_data):

        print(validated_data)
        attendance = validated_data.get('attendance')
        print('attendance', attendance)

        attendance_requests = AttendanceApprovalRequest.objects.filter(attendance=attendance, is_deleted=False).order_by('duration_start')
        print('attendance_requests', attendance_requests.values('duration_start','duration_end'))

        duration_start = validated_data.get('duration_start')
        duration_end = validated_data.get('duration_end')
        validated_data['duration'] = int((duration_end - duration_start).seconds/60)
        day_start_datetime = datetime.datetime.strptime(str(attendance.date.date())+'T08:00:00','%Y-%m-%dT%H:%M:%S')
        day_end_datetime = datetime.datetime.strptime(str(attendance.date.date())+'T21:00:00','%Y-%m-%dT%H:%M:%S')
        print(day_start_datetime, day_end_datetime)

        if attendance.is_present:
            if (day_start_datetime <= duration_start < attendance.login_time and day_start_datetime <= duration_end < attendance.login_time) or\
                (attendance.logout_time < duration_start <= day_end_datetime and attendance.logout_time < duration_end <= day_end_datetime):
                
                att_req_excluding_login_logout_time = attendance_requests.filter((Q(duration_start__lt=attendance.login_time)|
                                                                                    Q(duration_start__gt=attendance.logout_time)))
                print('att_req_excluding_login_logout_time', att_req_excluding_login_logout_time)
                is_deviation_overlap = att_req_excluding_login_logout_time.filter((Q(duration_start__lte=duration_start)&
                                                                                    Q(duration_end__gte=duration_start))|
                                                                                    (Q(duration_start__lte=duration_end)&
                                                                                    Q(duration_end__gte=duration_end))).count() > 0
                print('is_deviation_overlap',is_deviation_overlap)
                if not is_deviation_overlap:
                   return super().create(validated_data)
                else:
                    custom_exception_message(self,None,"Please enter proper data. Deviation time overlaped!")
            else:
                custom_exception_message(self,None,"Please enter proper data. Deviation time should be before login(after 8:00 AM) or after logout(before 9:00PM)")
        else:
            if day_start_datetime <= duration_start <= day_end_datetime and day_start_datetime <= duration_end <= day_end_datetime:
                is_deviation_overlap = attendance_requests.filter((Q(duration_start__lte=duration_start)&
                                                                                    Q(duration_end__gte=duration_start))|
                                                                                    (Q(duration_start__lte=duration_end)&
                                                                                    Q(duration_end__gte=duration_end))).count() > 0
                print('is_deviation_overlap',is_deviation_overlap)
                if not is_deviation_overlap: 
                   return super().create(validated_data)
                else:
                    custom_exception_message(self,None,"Please enter proper data. Deviation time overlaped!")
            else:
                custom_exception_message(self,None,"Please enter proper data. Deviation time should be after 8:00 AM to 9:00 PM")



        # current_date = datetime.date.today()
        
        # request_datetime = validated_data.get('start_date').strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        # request_datetime = datetime.datetime.strptime(request_datetime,"%Y-%m-%dT%H:%M:%S.%fZ").date()

        # request_end_datetime = validated_data.get('end_date').strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        # request_end_datetime = datetime.datetime.strptime(request_end_datetime,"%Y-%m-%dT%H:%M:%S.%fZ").date()


        # if request_datetime < current_date :
        #     custom_exception_message(self,None,"Start Date should not less than today's date!")
        
        # if request_datetime > request_end_datetime:
        #     custom_exception_message(self,None,"End Date should be greater than or euqual to start date!")

        return validated_data


class AttendanceSpecialLeaveListV2Serializer(serializers.ModelSerializer):
    department = serializers.SerializerMethodField(required=False)
    hod = serializers.SerializerMethodField(required=False)
    reporting_head = serializers.SerializerMethodField(required=False)
    designation = serializers.SerializerMethodField(required=False)
    leave_count = serializers.SerializerMethodField(required=False)
    company = serializers.SerializerMethodField(required=False)
    company_id = serializers.SerializerMethodField(required=False)
    department_id = serializers.SerializerMethodField(required=False)
    designation_id = serializers.SerializerMethodField(required=False)

    def get_department(self,EmployeeSpecialLeaves):
        details = TCoreUserDetail.objects.filter(cu_user=EmployeeSpecialLeaves.employee)
        if details[0].department:
            return details[0].department.cd_name

    def get_department_id(self,EmployeeSpecialLeaves):
        details = TCoreUserDetail.objects.filter(cu_user=EmployeeSpecialLeaves.employee)
        if details[0].department:
            return details[0].department.id
    
    def get_designation(self,EmployeeSpecialLeaves):
        details = TCoreUserDetail.objects.filter(cu_user=EmployeeSpecialLeaves.employee)
        if details[0].designation:
            return details[0].designation.cod_name

    def get_designation_id(self,EmployeeSpecialLeaves):
        details = TCoreUserDetail.objects.filter(cu_user=EmployeeSpecialLeaves.employee)
        if details[0].designation:
            return details[0].designation.id

    def get_company(self,EmployeeSpecialLeaves):
        details = TCoreUserDetail.objects.filter(cu_user=EmployeeSpecialLeaves.employee)
        if details[0].company:
            return details[0].company.coc_name

    def get_company_id(self,EmployeeSpecialLeaves):
        details = TCoreUserDetail.objects.filter(cu_user=EmployeeSpecialLeaves.employee)
        if details[0].company:
            return details[0].company.id
    
    def get_hod(self,EmployeeSpecialLeaves):
        details = TCoreUserDetail.objects.filter(cu_user=EmployeeSpecialLeaves.employee)
        if details[0].hod:
            return details[0].hod.first_name +' '+ details[0].hod.last_name
    
    def get_reporting_head(self,EmployeeSpecialLeaves):
        details = TCoreUserDetail.objects.filter(cu_user=EmployeeSpecialLeaves.employee)
        if details[0].reporting_head:
            print('details[0].reporting_head',details[0].reporting_head.last_name)
            return details[0].reporting_head.first_name +' '+ details[0].reporting_head.last_name
    
    def get_leave_count(self,EmployeeSpecialLeaves):
        request_how_many_days = (EmployeeSpecialLeaves.end_date - EmployeeSpecialLeaves.start_date).days + 1
        return request_how_many_days

    class Meta:
        model = EmployeeSpecialLeaves
        fields = '__all__'
        extra_fields = ['department','hod','reporting_head','designation','leave_count','department_id',
                        'designation_id', 'company_id', 'company']

class AttendanceSpecialLeaveApprovalTeamHrV2Serializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    special_leaves_approvals= serializers.ListField(required=False)
    document = serializers.FileField(required=False)
    class Meta:
        model = EmployeeSpecialLeaves
        fields = ('id', 'approved_status', 'remarks','updated_by','special_leaves_approvals','document')

    def create(self,validated_data):
        '''
            1)Admin can provide mass update by selecting as much request he wanted 
        '''

        print(validated_data)
        updated_by = validated_data.get('updated_by')
        remarks = validated_data.get('remarks')
        # master_module_role = TMasterModuleRoleUser.objects.get(mmr_module__cm_name__iexact='hrms',mmr_user=self.context['request'].user).mmr_role
        # core_role = TCoreRole.objects.get(id=str(master_module_role)).cr_name
        for data in validated_data.get('special_leaves_approvals'):
            
            approved_status= data['approved_status']
            req_type = EmployeeSpecialLeaves.objects.get(id=data['req_id'])
            start_date = datetime.datetime.strptime(data['start_date'], "%Y-%m-%dT%H:%M:%S.%fZ") if data['start_date'] else req_type.start_date
            end_date = datetime.datetime.strptime(data['end_date'], "%Y-%m-%dT%H:%M:%S.%fZ") if data['end_date'] else req_type.end_date
            print('start_date',start_date)
            EmployeeSpecialLeaves.objects.filter(id=data['req_id']).update(
                approved_status=approved_status,updated_by=updated_by,remarks=remarks,start_date=start_date,end_date=end_date)
            # if core_role.lower() == 'hr admin':
            logger.log(self.context['request'].user,approved_status+" "+req_type.leave_type,
                'Approval','pending',approved_status,'HRMS-TeamAttendance-LeaveApproval') 
        data = validated_data
        return data

class AttendanceSpecialLeaveApprovalDocUploadV2Serializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    document = serializers.FileField(required=False)
    class Meta:
        model = EmployeeSpecialLeaves
        fields = ('id','updated_by','document')


class AttendanceAdvanceLeaveApprovalDocUploadV2Serializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    document = serializers.FileField(required=False)
    class Meta:
        model = EmployeeSpecialLeaves
        fields = ('id','updated_by','document')


class AttandanceNewJoinerReportSerializerV2(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    employee_code = serializers.SerializerMethodField()
    punch_id = serializers.SerializerMethodField()
    sap_id = serializers.SerializerMethodField()
    reporting_head = serializers.SerializerMethodField()
    hod = serializers.SerializerMethodField()
    joining_date = serializers.SerializerMethodField()
    company = serializers.SerializerMethodField()
    company_id = serializers.SerializerMethodField()
    department = serializers.SerializerMethodField()
    department_id = serializers.SerializerMethodField()
    designation = serializers.SerializerMethodField()
    designation_id = serializers.SerializerMethodField()
    job_location = serializers.SerializerMethodField()
    job_location_state = serializers.SerializerMethodField()
    phone_no = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    salary_per_month = serializers.SerializerMethodField()
    salary_type = serializers.SerializerMethodField()
    grade = serializers.SerializerMethodField()
    sub_grade = serializers.SerializerMethodField()
    total_experience = serializers.SerializerMethodField()
    dob = serializers.SerializerMethodField()
    initial_ctc = serializers.SerializerMethodField()
    current_ctc = serializers.SerializerMethodField()
    cost_centre = serializers.SerializerMethodField()
    branch_name = serializers.SerializerMethodField()
    uan_no = serializers.SerializerMethodField()
    employee_voluntary_provident_fund_contribution = serializers.SerializerMethodField()
    contributing_towards_pension_scheme = serializers.SerializerMethodField()
    provident_trust_fund = serializers.SerializerMethodField()
    pf_trust_code = serializers.SerializerMethodField()
    pf_description = serializers.SerializerMethodField()
    emp_pension_no = serializers.SerializerMethodField()
    pension_trust_id = serializers.SerializerMethodField()
    is_flexi_hour = serializers.SerializerMethodField()
    has_pf = serializers.SerializerMethodField()
    has_esi = serializers.SerializerMethodField()
    esi_dispensary = serializers.SerializerMethodField()
    esi_sub_type = serializers.SerializerMethodField()
    attendance_type = serializers.SerializerMethodField()
    care_of = serializers.SerializerMethodField()
    country_key = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()
    district = serializers.SerializerMethodField()
    retirement_date = serializers.SerializerMethodField()
    wbs_element = serializers.SerializerMethodField()
    work_schedule_rule = serializers.SerializerMethodField()
    time_management_status = serializers.SerializerMethodField()
    ptax_sub_type = serializers.SerializerMethodField()
    emergency_relationship = serializers.SerializerMethodField()
    emergency_contact_no = serializers.SerializerMethodField()
    emergency_contact_name = serializers.SerializerMethodField()

    def get_username(self, obj):
        return obj.cu_user.username if obj.cu_user else ''

    def get_first_name(self, obj):
        return obj.cu_user.first_name if obj.cu_user else ''

    def get_last_name(self, obj):
        return obj.cu_user.last_name if obj.cu_user else ''

    def get_employee_code(self, obj):
        return obj.cu_emp_code

    def get_punch_id(self, obj):
        return obj.cu_punch_id

    def get_sap_id(self, obj):
        return obj.sap_personnel_no

    def get_reporting_head(self, obj):
        return obj.reporting_head.get_full_name() if obj.reporting_head else ''

    def get_hod(self, obj):
        return obj.hod.get_full_name() if obj.hod else ''

    def get_joining_date(self, obj):
        if obj.rejoin_date:
            return obj.rejoin_date
        else:
            return obj.joining_date

    def get_company(self, obj):
        return obj.company.coc_name if obj.company else ''

    def get_company_id(self, obj):
        return obj.company.id if obj.company else ''

    def get_department(self, obj):
        return obj.department.cd_name if obj.department else ''

    def get_department_id(self, obj):
        return obj.department.id if obj.department else ''

    def get_designation(self, obj):
        return obj.designation.cod_name if obj.designation else ''
    def get_designation_id(self, obj):
        return obj.designation.id if obj.designation else ''

    def get_job_location(self, obj):
        return obj.job_location if obj.job_location else ''

    def get_job_location_state(self, obj):
        return obj.job_location_state.cs_state_name if obj.job_location_state else ''

    def get_phone_no(self, obj):
        return obj.cu_alt_phone_no if obj.cu_alt_phone_no else ''

    def get_email(self, obj):
        return obj.cu_alt_email_id if obj.cu_alt_email_id else ''

    def get_salary_per_month(self, obj):
        return obj.salary_per_month if obj.salary_per_month else ''

    def get_salary_type(self, obj):
        return obj.salary_type.st_name if obj.salary_type else ''

    def get_grade(self, obj):
        return obj.employee_grade.cg_name if obj.employee_grade else ''
    def get_sub_grade(self, obj):
        return obj.employee_sub_grade.name if obj.employee_sub_grade else ''
    def get_total_experience(self, obj):
        return obj.total_experience if obj.total_experience else ''

    def get_dob(self, obj):
        return obj.cu_dob if obj.cu_dob else ''

    def get_initial_ctc(self, obj):
        return obj.initial_ctc if obj.initial_ctc else ''

    def get_current_ctc(self, obj):
        return obj.current_ctc if obj.current_ctc else ''

    def get_cost_centre(self, obj):
        return obj.updated_cost_centre.cost_centre_code if obj.updated_cost_centre else ''

    def get_branch_name(self, obj):
        return obj.branch_name if obj.branch_name else ''

    def get_uan_no(self, obj):
        return obj.uan_no if obj.uan_no else ''

    def get_employee_voluntary_provident_fund_contribution(self, obj):
        return obj.employee_voluntary_provident_fund_contribution if obj.employee_voluntary_provident_fund_contribution else ''

    def get_contributing_towards_pension_scheme(self, obj):
        return obj.contributing_towards_pension_scheme if obj.contributing_towards_pension_scheme else ''

    def get_provident_trust_fund(self, obj):
        return obj.provident_trust_fund if obj.provident_trust_fund else ''

    def get_pf_trust_code(self, obj):
        return obj.pf_trust_code if obj.pf_trust_code else ''

    def get_pf_description(self, obj):
        return obj.pf_description if obj.pf_description else ''

    def get_emp_pension_no(self, obj):
        return obj.emp_pension_no if obj.emp_pension_no else ''

    def get_pension_trust_id(self, obj):
        return obj.pension_trust_id if obj.pension_trust_id else ''

    def get_is_flexi_hour(self, obj):
        return obj.is_flexi_hour

    def get_has_pf(self, obj):
        return obj.has_pf

    def get_has_esi(self, obj):
        return obj.has_esi

    def get_esi_dispensary(self, obj):
        return obj.esi_dispensary if obj.esi_dispensary else ''

    def get_esi_sub_type(self, obj):
        return obj.esi_sub_type if obj.esi_sub_type else ''

    def get_attendance_type(self, obj):
        return obj.attendance_type if obj.attendance_type else ''

    def get_care_of(self, obj):
        return obj.care_of if obj.care_of else ''

    def get_country_key(self, obj):
        return obj.country_key if obj.country_key else ''

    def get_city(self, obj):
        return obj.city if obj.city else ''

    def get_district(self, obj):
        return obj.district if obj.district else ''

    def get_retirement_date(self, obj):
        return obj.retirement_date if obj.retirement_date else ''

    def get_wbs_element(self, obj):
        return obj.wbs_element if obj.wbs_element else ''

    def get_work_schedule_rule(self, obj):
        return obj.work_schedule_rule if obj.work_schedule_rule else ''

    def get_time_management_status(self, obj):
        return obj.time_management_status if obj.time_management_status else ''

    def get_ptax_sub_type(self, obj):
        return obj.ptax_sub_type if obj.ptax_sub_type else ''

    def get_emergency_relationship(self, obj):
        return obj.emergency_relationship if obj.emergency_relationship else ''

    def get_emergency_contact_no(self, obj):
        return obj.emergency_contact_no if obj.emergency_contact_no else ''

    def get_emergency_contact_name(self, obj):
        return obj.emergency_contact_name if obj.emergency_contact_name else ''

    class Meta:
        model = TCoreUserDetail
        fields = ['cu_user','username', 'first_name', 'last_name', 'reporting_head', 'hod', 'joining_date', 'transfer_date', 'is_transfer',
                  'employee_code', 'sap_id', 'punch_id', 'company','company_id', 'department','department_id',
                  'designation','designation_id' ,'job_location', 'job_location_state', 'phone_no', 'email', 'user_type',
                  'salary_per_month', 'salary_type', 'grade','sub_grade' ,'total_experience', 'dob', 'initial_ctc',
                  'current_ctc', 'cost_centre', 'branch_name', 'uan_no',
                  'employee_voluntary_provident_fund_contribution',
                  'contributing_towards_pension_scheme', 'provident_trust_fund', 'pf_trust_code', 'pf_description',
                  'emp_pension_no', 'pension_trust_id', 'is_flexi_hour',
                  'has_pf', 'has_esi', 'esi_dispensary', 'esi_sub_type', 'attendance_type', 'care_of',
                  'country_key', 'city', 'district',
                  'retirement_date', 'wbs_element', 'work_schedule_rule', 'time_management_status', 'ptax_sub_type',
                  'emergency_relationship',
                  'emergency_contact_no', 'emergency_contact_name']


class AttandanceSAPHiringReportSerializerV2(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    pernr = serializers.SerializerMethodField()
    employee_name = serializers.SerializerMethodField()
    mode_of_payment = serializers.SerializerMethodField()
    bank_account_no = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    employee_code = serializers.SerializerMethodField()
    bank_key = serializers.SerializerMethodField()
    punch_id = serializers.SerializerMethodField()
    sap_id = serializers.SerializerMethodField()
    reporting_head = serializers.SerializerMethodField()
    hod = serializers.SerializerMethodField()
    joining_date = serializers.SerializerMethodField()
    group_joining_date = serializers.SerializerMethodField()
    company = serializers.SerializerMethodField()
    department = serializers.SerializerMethodField()
    designation = serializers.SerializerMethodField()
    job_location = serializers.SerializerMethodField()
    phone_no = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    salary_per_month = serializers.SerializerMethodField()
    salary_type = serializers.SerializerMethodField()
    grade = serializers.SerializerMethodField()
    total_experience = serializers.SerializerMethodField()
    address_sub_type = serializers.SerializerMethodField()
    care_of = serializers.SerializerMethodField()
    street_and_house_no = serializers.SerializerMethodField()
    address_2nd_line = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()
    district = serializers.SerializerMethodField()
    region = serializers.SerializerMethodField()
    region_no = serializers.SerializerMethodField()
    state_description = serializers.SerializerMethodField()
    state_code = serializers.SerializerMethodField()
    aadhar_no = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    company_code = serializers.SerializerMethodField()
    cost_centre = serializers.SerializerMethodField()
    wbs_element = serializers.SerializerMethodField()
    retirement_date = serializers.SerializerMethodField()
    last_date_of_working = serializers.SerializerMethodField()
    start_date = serializers.SerializerMethodField()
    personnel_no = serializers.SerializerMethodField()
    begin_date = serializers.SerializerMethodField()
    esi_no = serializers.SerializerMethodField()
    ifsc_code = serializers.SerializerMethodField()
    pan_no = serializers.SerializerMethodField()
    employee_provide_fund_account_number = serializers.SerializerMethodField()
    employee_voluntary_provident_fund_contribution = serializers.SerializerMethodField()
    pf_trust_code = serializers.SerializerMethodField()
    pf_description = serializers.SerializerMethodField()
    time_management_status = serializers.SerializerMethodField()
    uan_no = serializers.SerializerMethodField()

    def get_uan_no(self, obj):
        return obj.uan_no if obj.uan_no else ''

    def get_time_management_status(self, obj):
        return obj.time_management_status if obj.time_management_status else ''

    def get_pf_description(self, obj):
        return obj.pf_description if obj.pf_description else ''

    def get_pf_trust_code(self, obj):
        return obj.pf_trust_code if obj.pf_trust_code else ''

    def get_employee_voluntary_provident_fund_contribution(self, obj):
        return obj.employee_voluntary_provident_fund_contribution if obj.employee_voluntary_provident_fund_contribution else ''

    def get_employee_provide_fund_account_number(self, obj):
        return obj.pf_no if obj.pf_no else "XX/XXX/999999/999999".encode('utf-8').decode('unicode-escape')

    def get_pan_no(self, obj):
        return obj.pan_no if obj.pan_no else ''

    def get_ifsc_code(self, obj):
        return obj.ifsc_code if obj.ifsc_code else ''

    def get_bank_account_no(self, obj):
        return  obj.bank_account if obj.bank_account else ''

    def get_esi_no(self, obj):
        return obj.esic_no if obj.esic_no else 'xxxxxxxxxx'

    def get_begin_date(self, obj):
        date = obj.joining_date.strftime("%d-%m-%Y") if obj.joining_date else ''
        if date:
            return str(date).replace('-', '.')
        else:
            return ''

    def get_personnel_no(self, obj):
        return obj.sap_personnel_no if obj.sap_personnel_no else ''

    def get_start_date(self, obj):
        date = obj.joining_date.strftime("%d-%m-%Y") if obj.joining_date else ''
        # print(type(date))
        if date:
            return str(date).replace('-', '.')
        else:
            return ''
        # return obj.joining_date.strftime("%d-%m-%Y") if obj.joining_date else ''

    def get_last_date_of_working(self, obj):
        date = obj.termination_date.strftime("%d-%m-%Y") if obj.termination_date else ''
        if date:
            return str(date).replace('-', '.')
        else:
            return ''

    def get_retirement_date(self, obj):
        date = obj.retirement_date.strftime("%d-%m-%Y") if obj.retirement_date else ''
        if date:
            return str(date).replace('-', '.')
        else:
            return ''

    def get_wbs_element(self, obj):
        return obj.wbs_element if obj.wbs_element else ''    

    def get_cost_centre(self, obj):
        return obj.cost_centre if obj.cost_centre else ''  

    def get_company_name(self, obj):
        return obj.company.coc_name if obj.company else ''      

    def get_company_code(self, obj):
        return obj.company.coc_code if obj.company else ''

    def get_bank_key(self, obj):
        if obj.company:
            if obj.company.coc_code in ['5500', '1000']:
                if obj.bank_name_p and obj.bank_name_p.name == 'Axis Bank':
                    return '6360218'
                return "0007502"
            else:
                if obj.bank_name_p and obj.bank_name_p.name == 'Axis Bank':
                    return '6360218'
                return "4289"
        else:
            return ''

    def get_mode_of_payment(self, obj):
        if obj.bank_name_p and obj.bank_name_p.name == 'Axis Bank':
            return '6'
        return 'T'

    def get_aadhar_no(self, obj):
        return obj.aadhar_no if obj.aadhar_no else ''    

    def get_state_description(self, obj):
        return obj.state.cs_description if obj.state else ''    

    def get_region_no(self, obj):
        return obj.state.cs_tin_number if obj.state else '' 

    def get_state_code(self, obj):
        return obj.state.cs_state_code if obj.state else ''  
  

    def get_region(self, obj):
        state = obj.state.cs_state_name if obj.state else ''
        country = obj.country if obj.country else ''
        region_str = ''
        if state and country:
            region_str = '{},{}'.format(state, country)
        elif state:
            region_str = state
        elif country:
            region_str = country
        return region_str

    def get_district(self, obj):
        return obj.district if obj.district else ''    

    def get_city(self, obj):
        return obj.city if obj.city else ''    

    def get_address_2nd_line(self, obj):
        return obj.address_2nd_line if obj.address_2nd_line else ''    

    def get_street_and_house_no(self, obj):
        return obj.street_and_house_no if obj.street_and_house_no else ''

    def get_care_of(self, obj):
        return obj.care_of if obj.care_of else ''

    def get_address_sub_type(self, obj):
        return obj.address_sub_type if obj.address_sub_type else ''

    def get_username(self, obj):
        return obj.cu_user.username if obj.cu_user else ''
        
    def get_first_name(self, obj):
        return obj.cu_user.first_name if obj.cu_user else ''

    def get_last_name(self, obj):
        return obj.cu_user.last_name if obj.cu_user else ''

    def get_employee_name(self, obj):
        return obj.cu_user.get_full_name() if obj.cu_user else ''

    def get_employee_code(self, obj):
        return obj.cu_emp_code if obj.cu_emp_code else ''

    def get_punch_id(self, obj):
        return obj.cu_punch_id if obj.cu_punch_id else ''

    def get_sap_id(self, obj):
        return obj.sap_personnel_no if obj.sap_personnel_no else ''

    def get_pernr(self, obj):
        return obj.sap_personnel_no if obj.sap_personnel_no else ''

    def get_reporting_head(self, obj):
        return obj.reporting_head.get_full_name() if obj.reporting_head else ''

    def get_hod(self, obj):
        return obj.hod.get_full_name() if obj.hod else ''

    def get_joining_date(self, obj):
        # return obj.joining_date if obj.joining_date else ''
        date = obj.joining_date.strftime("%d-%m-%Y") if obj.joining_date else ''
        if date:
            return str(date).replace('-', '.')
        else:
            return ''

    def get_group_joining_date(self, obj):
        # return obj.joining_date if obj.joining_date else ''
        date = obj.joining_date.strftime("%d-%m-%Y") if obj.joining_date else ''
        if date:
            return str(date).replace('-', '.')
        else:
            return ''

    def get_company(self, obj):
        return obj.company.coc_name if obj.company else ''

    def get_department(self, obj):
        return obj.department.cd_name if obj.department else ''

    def get_designation(self, obj):
        return obj.designation.cod_name if obj.designation else ''

    def get_job_location(self, obj):
        return obj.job_location if obj.job_location else ''

    def get_phone_no(self, obj):
        return obj.cu_alt_phone_no if obj.cu_alt_phone_no else ''

    def get_email(self, obj):
        return obj.cu_alt_email_id if obj.cu_alt_email_id else ''

    def get_salary_per_month(self, obj):
        return obj.salary_per_month if obj.salary_per_month else ''

    def get_salary_type(self, obj):
        return obj.salary_type.st_name if obj.salary_type else ''

    def get_grade(self, obj):
        return obj.employee_grade.cg_name if obj.employee_grade else ''

    def get_total_experience(self, obj):
        return obj.total_experience if obj.total_experience else ''

    class Meta:
        model = TCoreUserDetail
        fields = [
        'username', 'first_name', 'last_name', 'reporting_head', 'hod', 'joining_date', 
        'employee_code', 'employee_name' ,'sap_id', 'punch_id', 'company', 'department', 'pincode',
        'designation', 'job_location', 'phone_no', 'email', 'user_type', 'address_sub_type',
        'salary_per_month', 'salary_type', 'grade', 'total_experience', 'care_of',
        'street_and_house_no', 'address_2nd_line', 'city', 'district', 'region', 'country_key',
        'region_no', 'state_description', 'aadhar_no', 'company_name', 'company_code', 
        'cost_centre', 'wbs_element', 'retirement_date', 'last_date_of_working', 'start_date',
        'personnel_no', 'begin_date', 'esi_sub_type', 'esi_no', 'esi_dispensary',
        'ifsc_code', 'pan_no', 'provident_trust_fund', 'pension_trust_id', 'employee_provide_fund_account_number',
        'emp_pension_no', 'employee_voluntary_provident_fund_contribution', 'contributing_towards_pension_scheme',
        'pf_trust_code', 'pf_description', 'work_schedule_rule', 'time_management_status',
        'ptax_sub_type', 'uan_no', 'state_code', 'group_joining_date', 'bank_key', 'bank_account_no','mode_of_payment','pernr'
        ]



class WorkFromHomeSerializerv2(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    department = serializers.SerializerMethodField()
    designation = serializers.SerializerMethodField()
    reporting_head = serializers.SerializerMethodField()
    hod = serializers.SerializerMethodField()
    company = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    # start_time = serializers.SerializerMethodField()
    # end_time = serializers.SerializerMethodField()
    # work_done = serializers.SerializerMethodField()
    approval_status = serializers.SerializerMethodField()
    work_from_home = serializers.SerializerMethodField(required=False)

    def get_work_from_home(self, obj):
        work_from_home = WorkFromHomeDeviation.objects.filter(request=obj, is_deleted=False).values('start_date_time', 'end_date_time',
                                                                                  'work_done')
        return work_from_home

    def get_name(self, obj):
        if obj.attendance:
            name = obj.attendance.employee.get_full_name()
            return name

    def get_department(self, obj):
        if obj.attendance:
            return obj.attendance.employee.cu_user.department.cd_name if obj.attendance.employee.cu_user.department else None

    def get_designation(self, obj):
        if obj.attendance:
            return obj.attendance.employee.cu_user.designation.cod_name if obj.attendance.employee.cu_user.designation else None

    def get_reporting_head(self, obj):
        if obj.attendance:
            return obj.attendance.employee.cu_user.reporting_head.first_name + ' ' + obj.attendance.employee.cu_user.reporting_head.last_name if obj.attendance.employee.cu_user.reporting_head else None

    def get_hod(self, obj):
        if obj.attendance:
            name = obj.attendance.employee.cu_user.hod.first_name + ' ' + obj.attendance.employee.cu_user.hod.last_name if obj.attendance.employee.cu_user.hod else None
            return name
    def get_company(self, obj):
        if obj.attendance:
            company = obj.attendance.employee.cu_user.company.coc_name if obj.attendance.employee.cu_user.company else None
            return company

    def get_location(self, obj):
        if obj.attendance:
            location = obj.attendance.employee.cu_user.job_location if obj.attendance.employee.cu_user else None
            return location
    def get_date(self, obj):

        date = obj.attendance.date if obj.attendance else None
        return str(date.date())
    # def get_start_time(self, obj):
    #     start_time = obj.duration_start  if obj else None
    #     return str(start_time)
    #
    # def get_end_time(self, obj):
    #     end_time = obj.duration_end if obj else None
    #     return str(end_time)
    #
    # def get_work_done(self, obj):
    #
    #     work_done = obj.conveyance_purpose if obj else None
    #     return work_done
    def get_approval_status(self, obj):
        approval_status = obj.approved_status if obj else None
        return approval_status



    class Meta:
        model = AttendanceApprovalRequest
        fields = ('name', 'department', 'designation', 'reporting_head', 'hod', 'company', 'location', 'date',
                  'approval_status', 'work_from_home')


        # extra_field = ('work_from_home')


class WorkFromHomeDownloadSerializerv2(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    department = serializers.SerializerMethodField()
    designation = serializers.SerializerMethodField()
    reporting_head = serializers.SerializerMethodField()
    hod = serializers.SerializerMethodField()
    company = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    start_time = serializers.SerializerMethodField()
    end_time = serializers.SerializerMethodField()
    work_done = serializers.SerializerMethodField()
    approval_status = serializers.SerializerMethodField()


    def get_name(self, obj):
        if obj.request.attendance:
            name = obj.request.attendance.employee.get_full_name()
            return name

    def get_department(self, obj):
        if obj.request.attendance:
            return obj.request.attendance.employee.cu_user.department.cd_name if obj.request.attendance.employee.cu_user.department else None

    def get_designation(self, obj):
        if obj.request.attendance:
            return obj.request.attendance.employee.cu_user.designation.cod_name if obj.request.attendance.employee.cu_user.designation else None

    def get_reporting_head(self, obj):
        if obj.request.attendance:
            return obj.request.attendance.employee.cu_user.reporting_head.first_name + ' ' + obj.request.attendance.employee.cu_user.reporting_head.last_name if obj.request.attendance.employee.cu_user.reporting_head else None

    def get_hod(self, obj):
        if obj.request.attendance:
            name = obj.request.attendance.employee.cu_user.hod.first_name + ' ' + obj.request.attendance.employee.cu_user.hod.last_name if obj.request.attendance.employee.cu_user.hod else None
            return name
    def get_company(self, obj):
        if obj.request.attendance:
            company = obj.request.attendance.employee.cu_user.company.coc_name if obj.request.attendance.employee.cu_user.company else None
            return company

    def get_location(self, obj):
        if obj.request.attendance:
            location = obj.request.attendance.employee.cu_user.job_location if obj.request.attendance.employee.cu_user else None
            return location
    def get_date(self, obj):

        date = obj.request.attendance.date if obj.request.attendance else None
        return str(date.date())
    def get_start_time(self, obj):
        start_time = obj.start_date_time  if obj else None
        return start_time.strftime("%I:%M %p")

    def get_end_time(self, obj):
        end_time = obj.end_date_time if obj else None
        return end_time.strftime("%I:%M %p")

    def get_work_done(self, obj):

        work_done = obj.work_done if obj else None
        return work_done
    def get_approval_status(self, obj):
        approval_status = obj.request.approved_status if obj.request else None
        return approval_status



    class Meta:
        model = WorkFromHomeDeviation
        fields = ('name', 'department', 'designation', 'reporting_head', 'hod', 'company', 'location', 'date', "start_time",
                  'end_time', 'work_done','approval_status')



class FlexyAttendanceDailyListSerializerV2(serializers.ModelSerializer):

    class Meta:
        model = Attendance
        fields = '__all__'



class FlexiAttendanceAdvanceLeaveListSerializerV2(serializers.ModelSerializer):
    leave_count = serializers.SerializerMethodField(required=False)
    department = serializers.SerializerMethodField(required=False)
    designation = serializers.SerializerMethodField(required=False)
    reporting_head = serializers.SerializerMethodField(required=False)
    hod = serializers.SerializerMethodField(required=False)

    def get_leave_count(self, EmployeeAdvanceLeaves):
        request_how_many_days = (EmployeeAdvanceLeaves.end_date - EmployeeAdvanceLeaves.start_date).days + 1
        return request_how_many_days

    def get_department(self, EmployeeAdvanceLeaves):
        return EmployeeAdvanceLeaves.employee.cu_user.department.cd_name if EmployeeAdvanceLeaves.employee.cu_user.department else None

    def get_designation(self, EmployeeAdvanceLeaves):
        return EmployeeAdvanceLeaves.employee.cu_user.designation.cod_name if EmployeeAdvanceLeaves.employee.cu_user.designation else None

    def get_reporting_head(self, EmployeeAdvanceLeaves):
        return EmployeeAdvanceLeaves.employee.cu_user.reporting_head.first_name + ' ' + EmployeeAdvanceLeaves.employee.cu_user.reporting_head.last_name if EmployeeAdvanceLeaves.employee.cu_user.reporting_head else None

    def get_hod(self, EmployeeAdvanceLeaves):
        name = EmployeeAdvanceLeaves.employee.cu_user.hod.first_name + ' ' + EmployeeAdvanceLeaves.employee.cu_user.hod.last_name if EmployeeAdvanceLeaves.employee.cu_user.hod else None
        return name

    class Meta:
        model = EmployeeAdvanceLeaves
        fields = '__all__'
        extra_fields = ['leave_count', 'department', 'designation', 'reporting_head', 'hod']



class FlexiAttendanceConveyanceApprovalListSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceApprovalRequest
        fields = ('id','is_conveyance','is_late_conveyance','deviation_amount','conveyance_approval','vehicle_type', 'deviation_amount',
        'conveyance_purpose','conveyance_alloted_by','from_place','to_place','conveyance_expense',
        'approved_expenses','conveyance_remarks','attendance','duration_start','duration_end','duration',
        'conveyance_approved_by','updated_by')


class FlexiAttendanceLeaveApprovalListSerializerV2(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField(required=False)
    employee_id = serializers.SerializerMethodField(required=False)
    department = serializers.SerializerMethodField(required=False)
    designation = serializers.SerializerMethodField(required=False)
    reporting_head = serializers.SerializerMethodField(required=False)
    hod = serializers.SerializerMethodField(required=False)
    documents = serializers.SerializerMethodField(required=False)

    def get_employee_name(self, AttendanceApprovalRequest):
        if AttendanceApprovalRequest.attendance:
            first_name = AttendanceApprovalRequest.attendance.employee.first_name if AttendanceApprovalRequest.attendance.employee.first_name else ''
            last_name = AttendanceApprovalRequest.attendance.employee.last_name if AttendanceApprovalRequest.attendance.employee.last_name else ''
            name = first_name + " " + last_name
            return name

    def get_employee_id(self, AttendanceApprovalRequest):
        if AttendanceApprovalRequest.attendance:
            return AttendanceApprovalRequest.attendance.employee.id

    def get_department(self, AttendanceApprovalRequest):
        if AttendanceApprovalRequest.attendance:
            return AttendanceApprovalRequest.attendance.employee.cu_user.department.cd_name if AttendanceApprovalRequest.attendance.employee.cu_user.department else None

    def get_designation(self, AttendanceApprovalRequest):
        if AttendanceApprovalRequest.attendance:
            return AttendanceApprovalRequest.attendance.employee.cu_user.designation.cod_name if AttendanceApprovalRequest.attendance.employee.cu_user.designation else None

    def get_reporting_head(self, AttendanceApprovalRequest):
        if AttendanceApprovalRequest.attendance:
            return AttendanceApprovalRequest.attendance.employee.cu_user.reporting_head.first_name + ' ' + AttendanceApprovalRequest.attendance.employee.cu_user.reporting_head.last_name if AttendanceApprovalRequest.attendance.employee.cu_user.reporting_head else None

    def get_hod(self, AttendanceApprovalRequest):
        if AttendanceApprovalRequest.attendance:
            name = AttendanceApprovalRequest.attendance.employee.cu_user.hod.first_name + ' ' + AttendanceApprovalRequest.attendance.employee.cu_user.hod.last_name if AttendanceApprovalRequest.attendance.employee.cu_user.hod else None
            return name

    def get_documents(self, obj):
        leave_type = obj.leave_type_changed if obj.leave_type_changed else obj.leave_type
        return get_documents(request=self.context['request'],
                             attendance_request=obj) if leave_type == 'AL' or leave_type == 'AB' else list()

    class Meta:
        model = AttendanceApprovalRequest
        fields = '__all__'
        extra_fields = (
        'employee_name', 'employee_id', 'department', 'designation', 'reporting_head', 'hod', 'documents')


class FlexiETaskAttendanceApprovaWithoutGracelSerializerV2(serializers.ModelSerializer):
    employee_name=serializers.SerializerMethodField(required=False)
    employee_id=serializers.SerializerMethodField(required=False)
    documents=serializers.SerializerMethodField(required=False)
    work_form_home=serializers.SerializerMethodField(required=False)

    def get_work_form_home(self, obj):
        work_form_home = WorkFromHomeDeviation.objects.filter(request=obj, is_deleted=False).values('start_date_time', 'end_date_time', 'work_done')
        return work_form_home

    def get_employee_name(self,AttendanceApprovalRequest):
        if AttendanceApprovalRequest.attendance:
            first_name=AttendanceApprovalRequest.attendance.employee.first_name if AttendanceApprovalRequest.attendance.employee.first_name  else ''
            last_name=AttendanceApprovalRequest.attendance.employee.last_name if AttendanceApprovalRequest.attendance.employee.last_name else ''
            name=first_name+" "+last_name
            return name
    def get_employee_id(self,AttendanceApprovalRequest):
        if AttendanceApprovalRequest.attendance:
            return AttendanceApprovalRequest.attendance.employee.id

    def get_documents(self, obj):
        leave_type = obj.leave_type_changed if obj.leave_type_changed else obj.leave_type
        return get_documents(request=self.context['request'],attendance_request=obj) if leave_type == 'AL' or leave_type == 'AB' else list()

    class Meta:
        model = AttendanceApprovalRequest
        fields = '__all__'
        extra_fields=('employee_name','employee_id', 'documents', 'work_form_home')




class FlexiAttendanceAdminDailyListSerializerV2(serializers.ModelSerializer):
    
    class Meta:
        model = Attendance
        fields = '__all__'


class FlexiAttendanceAdminSummaryListSerializerV2(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = '__all__'

## Change Request Document__Attendance & HRMS (Conveyence Management) -CR-2 - V 1.2_Approved | Date: 23-06-2020 | Rupam Hazra ##

class AttendanceConveyanceConfigurationAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    #grade_name = serializers.SerializerMethodField(required=False)
    eligibility_on_mode_of_transport_format = serializers.SerializerMethodField(required=False)
    sub_grade_name = serializers.SerializerMethodField(required=False)

    # def get_grade_name(self,ConveyanceConfiguration):
    #     return ConveyanceConfiguration.grade.cg_name

    def get_sub_grade_name(self,ConveyanceConfiguration):
        if ConveyanceConfiguration.sub_grade:
            return ConveyanceConfiguration.sub_grade.name

    def get_eligibility_on_mode_of_transport_format(self,ConveyanceConfiguration):
        if ConveyanceConfiguration.eligibility_on_mode_of_transport:
            modes = ConveyanceConfiguration.eligibility_on_mode_of_transport.split(",")
            response = list()
            for mode in modes:
                response.append(VehicleTypeMaster.objects.only('name').get(pk=mode).name)
            return response

    class Meta:
        model = ConveyanceConfiguration
        fields = '__all__'
        extra_fields = ('eligibility_on_mode_of_transport_format','sub_grade_name')

class AttendanceConveyanceConfigurationEditSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    eligibility_on_mode_of_transport_format = serializers.SerializerMethodField(required=False)
    #grade_details =  serializers.SerializerMethodField(required=False)
    sub_grade_name = serializers.SerializerMethodField(required=False)

    def get_sub_grade_name(self,ConveyanceConfiguration):
        if ConveyanceConfiguration.sub_grade:
            return ConveyanceConfiguration.sub_grade.name

    # def get_grade_details(self,ConveyanceConfiguration):
    #     is_sub = TCoreGrade.objects.filter(pk=ConveyanceConfiguration.grade.id).values_list('cg_parent_id',flat=True)[0]
    #     #print('is_sub',is_sub)
    #     response = dict()
    #     if is_sub !=0:
    #         response['id'] = is_sub
    #         response['child']= ConveyanceConfiguration.grade.id
    #     else:
    #         response['id']= ConveyanceConfiguration.grade.id 

    #     return response

    def get_eligibility_on_mode_of_transport_format(self,ConveyanceConfiguration):
        if ConveyanceConfiguration.eligibility_on_mode_of_transport:
            modes = map(int,ConveyanceConfiguration.eligibility_on_mode_of_transport.split(","))
            return modes
        # response = list()
        # for mode in modes:
        #     response.append(VehicleTypeMaster.objects.only('name').get(pk=mode).name)
        # return response

    class Meta:
        model = ConveyanceConfiguration
        fields = '__all__'
        extra_fields = ('eligibility_on_mode_of_transport_format','sub_grade_name')

class AttendanceConveyanceApprovalConfigurationAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    name = serializers.SerializerMethodField(required=False)
    
    def get_name(self,ConveyanceApprovalConfiguration):
        return ConveyanceApprovalConfiguration.user.get_full_name()

    class Meta:
        model = ConveyanceApprovalConfiguration
        fields = '__all__'
        extra_fields = ('name')

class AttendanceConveyanceApprovalConfigurationEditSerializer(serializers.ModelSerializer):
    #created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    name = serializers.SerializerMethodField(required=False)

    def get_name(self,ConveyanceApprovalConfiguration):
        return ConveyanceApprovalConfiguration.user.get_full_name()

    class Meta:
        model = ConveyanceApprovalConfiguration
        fields = '__all__'
        extra_fields = ('name')

    # def update(self, instance, validated_data):
    #     try:
    #         with transaction.atomic():
    #             instance.is_deleted=True
    #             instance.user = validated_data
    #             instance.updated_by = validated_data.get('updated_by')
    #             instance.save()
    #             validated_data.pop('updated_by')
    #             created = ConveyanceApprovalConfiguration.objects.create(**validated_data)
    #             #print('created',created)
    #             return created

    #     except Exception as e:
    #         raise APIException({"msg": e, "request_status": 0})

class AttendanceConveyanceApprovalConfigurationDeleteSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = ConveyanceApprovalConfiguration
        fields = ('id','is_deleted')
        


class AttendanceConveyanceSerializer(serializers.ModelSerializer):
    documents = serializers.SerializerMethodField(required=False)
    comments = serializers.SerializerMethodField(required=False)
    approvals = serializers.SerializerMethodField(required=False)
    conveyance_configuration = serializers.SerializerMethodField(required=False)
    deviation_amount = serializers.SerializerMethodField(required=False)
    login_user_approved_status = serializers.SerializerMethodField(required=False)
    cost_centre = serializers.SerializerMethodField(required=False)
    status_name = serializers.SerializerMethodField(required=False)
    employee_id = serializers.SerializerMethodField(required=False)
    employee_name = serializers.SerializerMethodField(required=False)
    company = serializers.SerializerMethodField(required=False)
    company_id = serializers.SerializerMethodField(required=False)
    department = serializers.SerializerMethodField(required=False)
    department_id = serializers.SerializerMethodField(required=False)
    reporting_head_id = serializers.SerializerMethodField(required=False)
    reporting_head = serializers.SerializerMethodField(required=False)
    approved_expenses = serializers.SerializerMethodField(required=False)
    address = serializers.SerializerMethodField(required=False)

    def get_company(self,ConveyanceMaster):
        if ConveyanceMaster.request.attendance.employee.cu_user.company:
            return ConveyanceMaster.request.attendance.employee.cu_user.company.coc_name
        else:
            return None

    def get_company_id(self,ConveyanceMaster):
        if ConveyanceMaster.request.attendance.employee.cu_user.company:
            return ConveyanceMaster.request.attendance.employee.cu_user.company.id
        else:
            return None

    def get_department(self,ConveyanceMaster):
        if ConveyanceMaster.request.attendance.employee.cu_user.department:
            return ConveyanceMaster.request.attendance.employee.cu_user.department.cd_name
        else:
            return None

    def get_department_id(self,ConveyanceMaster):
        if ConveyanceMaster.request.attendance.employee.cu_user.department:
            return ConveyanceMaster.request.attendance.employee.cu_user.department.id
        else:
            return None

    def get_reporting_head(self,ConveyanceMaster):
        if ConveyanceMaster.request.attendance.employee.cu_user.reporting_head:
            return ConveyanceMaster.request.attendance.employee.cu_user.reporting_head.get_full_name()
        else:
            return None

    def get_reporting_head_id(self,ConveyanceMaster):
        if ConveyanceMaster.request.attendance.employee.cu_user.reporting_head:
            return ConveyanceMaster.request.attendance.employee.cu_user.reporting_head.id
        else:
            return None

    def get_documents(self,ConveyanceMaster):
        request = self.context.get('request')
        conveyanceDocument_list = list()
        conveyanceDocuments = ConveyanceDocument.objects.filter(conveyance_id=ConveyanceMaster.id,is_deleted=False)
        if conveyanceDocuments:
            for each_conveyanceDocument in conveyanceDocuments:
                conveyanceDocument_list.append(
                {
                'id':each_conveyanceDocument.id,
                'document':request.build_absolute_uri(each_conveyanceDocument.document.url),
                'document_name':each_conveyanceDocument.document_name}
                )
        return conveyanceDocument_list

    def get_comments(self,ConveyanceMaster):
        comment_details = ConveyanceComment.objects.filter(conveyance_id=ConveyanceMaster.id,is_deleted=False)
        result = []
        if comment_details:
            for each_comment_details in comment_details:
                result.append({
                    "comment":each_comment_details.comment,
                    'author_name':each_comment_details.user.get_full_name(),
                    'commented_at':each_comment_details.created_at,
                    'is_seen':each_comment_details.is_seen
                    })
        return result

    def get_approvals(self,ConveyanceMaster):
        approval_con = ConveyanceApprovalConfiguration.objects.filter(is_deleted=False).order_by('level_no')
        approval_list = list()
        for each_approval in approval_con:
            approval_details = ConveyanceApproval.objects.filter(conveyance_id=ConveyanceMaster.id,
            approval_user_level_id=each_approval.id,is_deleted=False).values('approval_status','updated_at')
            status = None
            date = None
            if approval_details:
                approval_details = approval_details[0]
                status = approval_details['approval_status']
                
                if ConveyanceMaster.status == 'Reject':
                    status = approval_details['approval_status']
                    if approval_details['approval_status'] == 'Pending':
                        status = '--'
                
                date = approval_details['updated_at'] if approval_details['updated_at'] else None
            
            if status == 'Approve':
                status = 'Approved'
            if status == 'Reject':
                status = 'Rejected'

            result = {
            "id":each_approval.id,
            "level":each_approval.level,
            "user":each_approval.user_id,
            "name":each_approval.user.get_full_name(),
            "status": status,
            "date": date
            }
            approval_list.append(result)
        return approval_list

    def get_conveyance_configuration(self,ConveyanceMaster):
        if ConveyanceMaster.request.attendance.employee.cu_user.employee_sub_grade:
        #return ConveyanceConfiguration.objects.filter(grade_id=ConveyanceMaster.request.attendance.employee.cu_user.employee_grade.id).values('id','eligibility_on_mode_of_transport','grade_id')[0] if ConveyanceConfiguration.objects.filter(grade_id=ConveyanceMaster.request.attendance.employee.cu_user.employee_grade.id) else None
            return ConveyanceConfiguration.objects.filter(sub_grade_id=ConveyanceMaster.request.attendance.employee.cu_user.employee_sub_grade.id).values('id','eligibility_on_mode_of_transport','sub_grade_id')[0] if ConveyanceConfiguration.objects.filter(sub_grade_id=ConveyanceMaster.request.attendance.employee.cu_user.employee_sub_grade.id) else None
    
    def get_deviation_amount(self,ConveyanceMaster):
        return ConveyanceMaster.deviation_amount

    def get_address(self,ConveyanceMaster):
        request = self.context.get('request')
        conveyancePlacesMapping = ConveyancePlacesMapping.objects.filter(conveyance_id=ConveyanceMaster.id,is_deleted=False).values(
            'conveyance','from_place','to_place','vehicle_type','vehicle_type__name','kilometers_travelled','amount','place_deviation_amount')
        print('conveyancePlacesMapping',conveyancePlacesMapping)
        
        if conveyancePlacesMapping:
            for each in conveyancePlacesMapping:
                conveyanceDocument_list = list()
                #print('each',each)
                each['vehicle_type_name'] = each['vehicle_type__name']
                each.pop('vehicle_type__name')
                conveyanceDocuments = ConveyanceDocument.objects.filter(
                    conveyance_id = ConveyanceMaster.id,
                    from_place = each['from_place'],
                    to_place = each['to_place'],
                    is_deleted = False
                    )
                print('conveyanceDocuments',conveyanceDocuments)
                if conveyanceDocuments:
                    for each_conveyanceDocument in conveyanceDocuments:
                        conveyanceDocument_list.append(
                        {
                        'id':each_conveyanceDocument.id,
                        'document':request.build_absolute_uri(each_conveyanceDocument.document.url),
                        'document_name':each_conveyanceDocument.document_name}
                        )
                each['documents'] = conveyanceDocument_list
            return conveyancePlacesMapping
        # pass
        
    def get_login_user_approved_status(self,ConveyanceMaster):
        request = getattr(self.context, 'request', None)
        #print('request.user',self.context['request'].user)
        _conveyanceApprovalConfiguration = ConveyanceApprovalConfiguration.objects.filter(is_deleted=False,user=self.context['request'].user)
        
        if _conveyanceApprovalConfiguration:
            _approval_user_level_id = _conveyanceApprovalConfiguration.values_list('id',flat=True)[0]
            #print('approval_user_level_id',_approval_user_level_id)
            _approval_con = ConveyanceApproval.objects.filter(
                conveyance_id=ConveyanceMaster.id,
                approval_user_level_id = _approval_user_level_id,
                is_deleted=False
                )
            if _approval_con:
                status = _approval_con.values_list('approval_status',flat=True)[0]
                if status == 'Approve':
                    status = 'Approved'
                if status == 'Reject':
                    status = 'Rejected'
                return status
        else:
            return None

    def get_cost_centre(self,ConveyanceMaster):
        if ConveyanceMaster.request.attendance.employee.cu_user.updated_cost_centre:
            return ConveyanceMaster.request.attendance.employee.cu_user.updated_cost_centre.cost_centre_name
        else:
            return ConveyanceMaster.request.attendance.employee.cu_user.cost_centre

    def get_status_name(self,ConveyanceMaster):
        status = ConveyanceMaster.status
        if ConveyanceMaster.status == 'Approve':
            status = 'Approved'
        if ConveyanceMaster.status == 'Reject':
            status = 'Rejected'
        return status
        
    def get_employee_name(self,ConveyanceMaster):
        return ConveyanceMaster.request.attendance.employee.get_full_name()
    
    def get_employee_id(self,ConveyanceMaster):
        return ConveyanceMaster.request.attendance.employee.id
    
    def get_approved_expenses(self,ConveyanceMaster):
        if ConveyanceMaster.status in ['Pending for Accounts Approval','Reject','Approve','Modified']:
            return ConveyanceMaster.approved_expenses
    
    class Meta:
        model = ConveyanceMaster
        #fields = '__all__'
        depth=1
        extra_fields = ('documents','comments','approvals','conveyance_configuration','deviation_amount',
                        'login_user_approved_status','cost_centre','status_name','employee_name','company','company_id',
                        'department','department_id','reporting_head','reporting_head_id','employee_id','address')
        exclude = ['updated_at','updated_by']

class AttendanceConveyanceApprovalStatusUpdateByAccountSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    conveyance_approvals = serializers.ListField(required=False)
    comment = serializers.CharField(required=False,allow_blank=True,allow_null=True)
    class Meta:
        model = ConveyanceApproval
        fields = '__all__'
        extra_fields = ('conveyance_approvals','comment')

    def _getFinalApprovalLevelId(self):
        _conveyanceApprovalConfiguration = ConveyanceApprovalConfiguration.objects.filter(is_deleted=False).order_by('-level')
        if _conveyanceApprovalConfiguration:
            return  _conveyanceApprovalConfiguration.values_list('id',flat=True)[0]
        return None

    def _addComment(self,validated_data,_conveyance_approval):
        return ConveyanceComment.objects.create(
                    comment = validated_data.get('comment'),
                    conveyance = _conveyance_approval.conveyance,
                    user = validated_data.get('updated_by'),
                    created_by = validated_data.get('updated_by'),
                    )

    def create(self, validated_data):
        try:
            conveyance_approvals =  validated_data.get('conveyance_approvals')
            #print('conveyance_approvals',conveyance_approvals)

            if validated_data.get('approval_status') == 'Approve':
                approved_status_name = 'Approved'
                higest_approval_level_id = self._getFinalApprovalLevelId()
                #print('higest_approval_level_id',higest_approval_level_id)
                for e_conveyance in conveyance_approvals:
                    _conveyance_approval = ConveyanceApproval.objects.get(conveyance_id=str(e_conveyance),approval_user_level_id=validated_data.get('approval_user_level'))
                    _conveyanceMaster = ConveyanceMaster.objects.get(pk=str(e_conveyance),is_deleted=False)
                    #print('safasffd',str(higest_approval_level_id),type(str(higest_approval_level_id)),str(validated_data.get('approval_user_level')),type(str(validated_data.get('approval_user_level'))))
                    if str(higest_approval_level_id) == str(validated_data.get('approval_user_level')):
                        _conveyanceMaster.status = 'Approve'
                        _conveyanceMaster.updated_by = validated_data.get('updated_by')
                    else:
                        _approval_user_level_details = ConveyanceApprovalConfiguration.objects.get(id=str(validated_data.get('approval_user_level')),is_deleted=False)
                        #print('_approval_user_level_details',_approval_user_level_details)
                        _current_approval_level_view_list = _approval_user_level_details.level.split('L')
                        #print('_current_approval_level_view_list',_current_approval_level_view_list)
                        _current_approval_level_view = int(_current_approval_level_view_list[1]) + 1
                        _conveyanceMaster.current_approval_level_view = 'L'+str(_current_approval_level_view)

                    
                    _conveyanceMaster.save()

                    _conveyance_approval.approval_status = validated_data.get('approval_status')
                    _conveyance_approval.updated_at = datetime.datetime.now()
                    _conveyance_approval.save()
                    if validated_data.get('comment') is not None and validated_data.get('comment')!='':
                        self._addComment(validated_data,_conveyance_approval)

                    ## Start Mail 
                    recipient_email = _conveyanceMaster.created_by.cu_user.cu_alt_email_id
                    if recipient_email:
                        mail_data = {
                            "recipient_name": _conveyanceMaster.created_by.get_full_name(),
                            "created_at": str(_conveyanceMaster.created_at)[0:10],
                            "from_place": _conveyanceMaster.from_place,
                            "to_place": _conveyanceMaster.to_place,
                            "vehicle_type":_conveyanceMaster.vehicle_type.name,
                            "approved_expenses":_conveyanceMaster.approved_expenses,
                            "conveyance_approved_by":_conveyance_approval.approval_user_level.user.get_full_name(),
                            "status":approved_status_name,
                            "updated_at":str(_conveyance_approval.updated_at)[0:10] if _conveyance_approval.updated_at else '',
                            "approved_status_name":approved_status_name,
                            "department_label": "Accounts department"
                            }
                        #print('mail_data',mail_data)
                        send_mail('AT-CA-01',recipient_email,mail_data)
                        
                    ## End Mail


            if validated_data.get('approval_status') == 'Reject':
                approved_status_name = 'Rejected'
                for e_conveyance in conveyance_approvals:
                    _conveyance_approval = ConveyanceApproval.objects.get(
                        conveyance_id=str(e_conveyance),approval_user_level_id=validated_data.get('approval_user_level')
                        )
                    _conveyanceMaster = ConveyanceMaster.objects.get(pk=str(e_conveyance),is_deleted=False)
                    _conveyanceMaster.status = 'Reject'
                    _conveyanceMaster.updated_by = validated_data.get('updated_by')
                    _conveyanceMaster.updated_at = datetime.datetime.now()
                    _conveyanceMaster.save()

                    _conveyance_approval.approval_status = validated_data.get('approval_status')
                    _conveyance_approval.save()

                    self._addComment(validated_data,_conveyance_approval)

                    ## Start Mail 

                    recipient_email = _conveyanceMaster.created_by.cu_user.cu_alt_email_id
                    if recipient_email:
                        mail_data = {
                            "recipient_name": _conveyanceMaster.created_by.get_full_name(),
                            "created_at": str(_conveyanceMaster.created_at)[0:10],
                            "from_place": _conveyanceMaster.from_place,
                            "to_place": _conveyanceMaster.to_place,
                            "vehicle_type":_conveyanceMaster.vehicle_type.name,
                            "approved_expenses":_conveyanceMaster.approved_expenses,
                            "conveyance_approved_by":_conveyance_approval.approval_user_level.user.get_full_name(),
                            "status":approved_status_name,
                            "updated_at":str(_conveyance_approval.updated_at)[0:10] if _conveyance_approval.updated_at else '',
                            "approved_status_name":approved_status_name,
                            "department_label": "Accounts department"
                            }
                        #print('mail_data',mail_data)
                        send_mail('AT-CA-01-R',recipient_email,mail_data)
                    ## End Mail


            #print('created',created)
            return validated_data

        except Exception as e:
            raise APIException({"msg": e, "request_status": 0})

class AttendanceConveyanceStatusUpdateSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    approval_user_level = serializers.CharField(required=False, allow_null=True)
    conveyance_approvals = serializers.ListField(required=False)
    approved_expenses = serializers.CharField(required=False,allow_null=True)
    comment = serializers.CharField(required=False,allow_null=True,allow_blank=True)
    class Meta:
        model = ConveyanceMaster
        fields = ('id','approved_expenses','status','updated_by','conveyance_approvals','approval_user_level','comment')

    def create(self, validated_data):
        try:
            with transaction.atomic():
                conveyance_ids = validated_data.get('conveyance_approvals')
                status = validated_data.get('status')
                approved_status_name = validated_data.get('status')+'ed'
                if validated_data.get('status') == 'Pending for Accounts Approval' or validated_data.get('status') == 'Modified':
                    status = "Pending for Accounts Approval"
                    approved_status_name = 'Approved'

                for e_conveyance_id in conveyance_ids:
                    #print('e_conveyance_id',e_conveyance_id)
                    e_conveyance_id = e_conveyance_id['id']
                    conveyance = ConveyanceMaster.objects.get(pk=e_conveyance_id)
                    #print('conveyance',conveyance)
                    if validated_data.get('status') == 'Pending for Accounts Approval' or validated_data.get('status') == 'Modified':
                        #print('validated_data',validated_data)
                        _conveyanceApprovalConfiguration = ConveyanceApprovalConfiguration.objects.filter(is_deleted=False)
                        if _conveyanceApprovalConfiguration:
                            for _e_conveyanceApprovalConfiguration in _conveyanceApprovalConfiguration:
                                ConveyanceApproval.objects.get_or_create(
                                    approval_user_level_id=_e_conveyanceApprovalConfiguration.id,
                                    conveyance_id = conveyance.id,
                                    created_by = validated_data.get('updated_by')
                                    )
                        conveyance.current_approval_level_view = 'L1'
                    
                    if validated_data.get('approved_expenses') is not None:
                        #print('sddd',validated_data.get('approved_expenses'))
                        approved_expenses = float(validated_data.get('approved_expenses'))
                        conveyance_expense = float(conveyance.conveyance_expense)
                        deviation_amount = conveyance.deviation_amount if conveyance.deviation_amount else 0.0
                        if approved_expenses > conveyance_expense:
                            conveyance.deviation_amount = deviation_amount + (approved_expenses - conveyance_expense)
                        if approved_expenses < conveyance_expense:
                            if  conveyance.deviation_amount:
                                conveyance.deviation_amount = conveyance.deviation_amount - (conveyance_expense - approved_expenses)
                            
                        
                        conveyance.approved_expenses = approved_expenses
                    conveyance.status=status
                    conveyance.conveyance_approved_by = validated_data.get('updated_by')
                    conveyance.updated_by = validated_data.get('updated_by')
                    conveyance.updated_at = datetime.datetime.now()
                    conveyance.save()

                    if validated_data.get('comment') is not None and validated_data.get('comment')!='':
                        ConveyanceComment.objects.create(
                            conveyance_id = conveyance.id,
                            user = validated_data.get('updated_by'),
                            comment=validated_data.get('comment')
                        )

                    ## Start Mail 
                    if conveyance.status == 'Approve':
                        status = 'Approved'
                    if conveyance.status == 'Reject':
                        status = 'Rejected'

                    recipient_email = conveyance.created_by.cu_user.cu_alt_email_id
                    if recipient_email:
                        mail_data = {
                            "recipient_name": conveyance.created_by.get_full_name(),
                            "created_at": str(conveyance.request.attendance_date)[0:10],
                            "from_place": conveyance.from_place,
                            "to_place": conveyance.to_place,
                            "vehicle_type":conveyance.vehicle_type.name,
                            "approved_expenses":conveyance.approved_expenses,
                            "conveyance_approved_by":conveyance.conveyance_approved_by.get_full_name(),
                            "status":status,
                            "updated_at":str(conveyance.updated_at)[0:10] if conveyance.updated_at else '',
                            "approved_status_name":approved_status_name,
                            "department_label": "Reporting Head"
                            }
                        send_mail('AT-CA-01',recipient_email,mail_data)

                        if validated_data.get('status') != 'Reject':
                            conveyanceApproval = ConveyanceApproval.objects.get(
                                conveyance=conveyance,
                                approval_user_level__level='L1',
                                approval_user_level__level_no=1,
                                is_deleted=False
                                )
                            recipient_email = conveyanceApproval.approval_user_level.user.cu_user.cu_alt_email_id
                            if recipient_email : 
                                mail_data = {
                                    "employee_name": conveyance.request.attendance.employee.get_full_name(),
                                    "recipient_name": conveyanceApproval.approval_user_level.user.get_full_name(),
                                    "created_at": str(conveyance.request.attendance_date)[0:10],
                                    "from_place": conveyance.from_place,
                                    "to_place": conveyance.to_place,
                                    "vehicle_type":conveyance.vehicle_type.name,
                                    "approved_expenses":conveyance.approved_expenses,
                                    "conveyance_approved_by":conveyance.conveyance_approved_by.get_full_name(),
                                    "status":status,
                                    "updated_at":str(conveyance.updated_at)[0:10] if conveyance.updated_at else '',
                                    "approved_status_name":approved_status_name,
                                    "department_label": "Reporting Head"
                                    }
                                send_mail('AT-CA-N-AC',recipient_email,mail_data)
                    ## End Mail
                return validated_data

        except Exception as e:
            raise APIException({"msg": e, "request_status": 0})

class AttendanceConveyanceUpdateSerializer(serializers.ModelSerializer):
    documents = serializers.SerializerMethodField(required=False)
    comments = serializers.SerializerMethodField(required=False)
    approvals = serializers.SerializerMethodField(required=False)
    address = serializers.SerializerMethodField(required=False)
    conveyance_configuration = serializers.SerializerMethodField(required=False)
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())

    def get_documents(self,ConveyanceMaster):
        return ConveyanceDocument.objects.filter(conveyance_id=ConveyanceMaster.id,is_deleted=False).values('id','document_name','document')

    def get_comments(self,ConveyanceMaster):
        comment_details = ConveyanceComment.objects.filter(conveyance_id=ConveyanceMaster.id,is_deleted=False)
        result = []
        if comment_details:
            for each_comment_details in comment_details:
                result.append({
                    "comment":each_comment_details.comment,
                    'author_name':each_comment_details.user.get_full_name(),
                    'commented_at':each_comment_details.created_at,
                    'is_seen':each_comment_details.is_seen
                    })
        return result

    def get_approvals(self,ConveyanceMaster):
        approval_con = ConveyanceApprovalConfiguration.objects.filter(is_deleted=False)
        approval_list = list()
        for each_approval in approval_con:
            result = {
            "id":each_approval.id,
            "level":each_approval.level,
            "user":each_approval.user_id,
            "name":each_approval.user.get_full_name(),
            "status": ConveyanceApproval.objects.filter(
                conveyance_id=ConveyanceMaster.id,approval_user_level_id=each_approval.id,is_deleted=False).values_list('approval_status',flat=True)[0] if ConveyanceApproval.objects.filter(
                conveyance_id=ConveyanceMaster.id,approval_user_level_id=each_approval.id,is_deleted=False) else None
            }
            approval_list.append(result)
        return approval_list

    def get_conveyance_configuration(self,ConveyanceMaster):
        #return ConveyanceConfiguration.objects.filter(grade_id=ConveyanceMaster.request.attendance.employee.cu_user.employee_grade.id).values('id','eligibility_on_mode_of_transport','grade_id')[0] if ConveyanceConfiguration.objects.filter(grade_id=ConveyanceMaster.request.attendance.employee.cu_user.employee_grade.id) else None
        return ConveyanceConfiguration.objects.filter(sub_grade_id=ConveyanceMaster.request.attendance.employee.cu_user.employee_sub_grade.id).values('id','eligibility_on_mode_of_transport')[0] if ConveyanceConfiguration.objects.filter(sub_grade_id=ConveyanceMaster.request.attendance.employee.cu_user.employee_sub_grade.id) else None

    def get_address(self,ConveyanceMaster):
        request = self.context.get('request')
        conveyancePlacesMapping = ConveyancePlacesMapping.objects.filter(conveyance_id=ConveyanceMaster.id,is_deleted=False).values(
            'conveyance','from_place','to_place','vehicle_type','vehicle_type__name','kilometers_travelled','amount','place_deviation_amount')
        #print('conveyancePlacesMapping',conveyancePlacesMapping)
        
        if conveyancePlacesMapping:
            for each in conveyancePlacesMapping:
                conveyanceDocument_list = list()
                #print('each',each)
                each['vehicle_type_name'] = each['vehicle_type__name']
                each.pop('vehicle_type__name')
                conveyanceDocuments = ConveyanceDocument.objects.filter(
                    conveyance_id = ConveyanceMaster.id,
                    from_place = each['from_place'],
                    to_place = each['to_place'],
                    is_deleted = False
                    )
                if conveyanceDocuments:
                    for each_conveyanceDocument in conveyanceDocuments:
                        conveyanceDocument_list.append(
                        {
                        'id':each_conveyanceDocument.id,
                        'document':request.build_absolute_uri(each_conveyanceDocument.document.url),
                        'document_name':each_conveyanceDocument.document_name}
                        )
                each['documents'] = conveyanceDocument_list
            return conveyancePlacesMapping
        # pass
       

    class Meta:
        model = ConveyanceMaster
        fields = '__all__'
        depth = 1
        extra_fields = ('documents','comments','approvals','conveyance_configuration','address')

    def update(self, instance, validated_data):
        try:
            with transaction.atomic():

                check = ConveyanceMaster.objects.create(**validated_data)
                return check

        except Exception as e:
            raise APIException({"msg": e, "request_status": 0})

class AttendanceConveyanceAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    #kilometers_travelled = serializers.CharField(required=False,allow_null=True)
    prev_conveyance_id =  serializers.CharField(required=False)
    #deviation_amount = serializers.CharField(required=False)
    re_apply = serializers.BooleanField(default=True)
    address  = serializers.ListField(required=False)

    class Meta:
        model = ConveyanceMaster
        fields = ('id','request','conveyance_type','conveyance_purpose','address','conveyance_alloted_by','created_by','prev_conveyance_id','re_apply','is_round')

    def insert_ConveyancePlacesMapping(self,address,conveyanceMaster,created_by):
        #amount = 0.0
        for each in address:
            each['conveyance'] = conveyanceMaster
            each['from_place'] = each['from_place']
            each['to_place'] = each['to_place']
            each['created_by'] = created_by
            each['vehicle_type_id'] = each['vehicle_type']
            each.pop('vehicle_type')
            each['amount'] = each['amount']
            each['place_deviation_amount'] = each['place_deviation_amount']
            each['kilometers_travelled'] = each['kilometers_travelled']
            ConveyancePlacesMapping.objects.create(**each)
            #amount = amount + float(each['conveyance_expense'])
            #deviation_amount = deviation_amount + float(each['deviation_amount'])
        return True

    def insert_Documents(self,address,conveyanceMaster,created_by,prev_conveyance_id):
        for each_address in address:
            conveyanceDocument_details = ConveyanceDocument.objects.filter(
                conveyance_id=prev_conveyance_id,
                from_place=each_address['from_place'],
                to_place=each_address['to_place']
                ).values()
            #print('conveyanceDocument_details',conveyanceDocument_details.query)
            #print('conveyanceDocument_details',conveyanceDocument_details)
            for each in conveyanceDocument_details:
                each.pop('id')
                each['conveyance_id'] = conveyanceMaster.id
                each['created_by_id'] = created_by.id
                #print('each',each)
                ConveyanceDocument.objects.create(**each)
        #raise APIException('dsddsd')

        return True

    def create(self, validated_data):
        try:
            with transaction.atomic():
                #print('validated_data',validated_data)
                prev_conveyance_id = validated_data.get('prev_conveyance_id')
                address  = validated_data.pop('address')
                ConveyanceMaster.objects.filter(id=prev_conveyance_id).update(apply=False)
                validated_data['conveyance_expense'] = validated_data.get('conveyance_expense')
                validated_data['approved_expenses'] = validated_data.get('conveyance_expense')
                #validated_data['kilometers_travelled'] = validated_data.get('kilometers_travelled') if validated_data.get('kilometers_travelled') else None
                validated_data['deviation_amount'] = validated_data.get('deviation_amount') if validated_data.get('deviation_amount') else None
                #print('validated_data',validated_data)
                conveyanceMaster = ConveyanceMaster.objects.create(**validated_data)
                self.insert_ConveyancePlacesMapping(address,conveyanceMaster,validated_data.get('created_by'))
                #self.insert_Documents(address,conveyanceMaster,validated_data.get('created_by'),prev_conveyance_id)
                conveyanceMaster.save()
                return conveyanceMaster

        except Exception as e:
            raise APIException({"msg": e, "request_status": 0})      

class AttendanceConveyanceDocAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = ConveyanceDocument
        fields = '__all__'

class AttendanceConveyancePaymentUpdateSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    conveyance_list = serializers.ListField(required=False)
    comment = serializers.CharField(required=False,allow_null=True,allow_blank=True)
    class Meta:
        model = ConveyanceMaster
        fields = ('id','updated_by','conveyance_list','comment','is_paid')

    def create(self, validated_data):
        try:
            with transaction.atomic():
                conveyance_ids = validated_data.get('conveyance_list')
                for e_conveyance_id in conveyance_ids:
                    conveyance = ConveyanceMaster.objects.get(pk=e_conveyance_id)
                    #print('conveyance',conveyance)
                    conveyance.is_paid= validated_data.get('is_paid')
                    conveyance.updated_by = validated_data.get('updated_by')
                    conveyance.save()
                    if validated_data.get('comment') is not None and validated_data.get('comment')!='':
                        ConveyanceComment.objects.create(
                            conveyance_id = conveyance.id,
                            user = validated_data.get('updated_by'),
                            comment=validated_data.get('comment')
                            )
                return validated_data

        except Exception as e:
            raise APIException({"msg": e, "request_status": 0})
## Change Request Document__Attendance & HRMS (Conveyence Management) -CR-2 - V 1.2_Approved | Date: 23-06-2020 | Rupam Hazra ##


## Change Request HRMS_Conveyance CR-5.0 doc | Date: 16-09-2020 | Rupam Hazra ##

# Travel Mode,Price
class TravelModeAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    description = serializers.CharField(required=False,allow_null=True,allow_blank=True)
    price_per_km = serializers.CharField(required=False,allow_null=True,allow_blank=True)
    class Meta:
        model = VehicleTypeMaster
        fields = '__all__'


class TravelModeEditSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    description = serializers.CharField(required=False,allow_null=True,allow_blank=True)
    price_per_km = serializers.CharField(required=False,allow_null=True,allow_blank=True)
    class Meta:
        model = VehicleTypeMaster
        fields = '__all__'

class AttendanceConveyanceConfigurationDetailsSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    #grade_name = serializers.SerializerMethodField(required=False)
    eligibility_on_mode_of_transport_format = serializers.SerializerMethodField(required=False)
    sub_grade_name = serializers.SerializerMethodField(required=False)


    def get_sub_grade_name(self,ConveyanceConfiguration):
        if ConveyanceConfiguration.sub_grade:
            return ConveyanceConfiguration.sub_grade.name

    

    def get_eligibility_on_mode_of_transport_format(self,ConveyanceConfiguration):
        modes = map(int,ConveyanceConfiguration.eligibility_on_mode_of_transport.split(","))
        return VehicleTypeMaster.objects.filter(pk__in=modes).values()

    class Meta:
        model = ConveyanceConfiguration
        fields = '__all__'
        extra_fields = ('eligibility_on_mode_of_transport_format','sub_grade_name')




class AttendanceAutoApprovalStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceAutoApprovalRequestStatus
        fields = '__all__'

import re

class AttendanceFRSRawDataSerializer(serializers.ModelSerializer):
    sap_id = serializers.SerializerMethodField()

    def get_sap_id(self,obj):
        if obj.person_id:
            return obj.person_id.replace("'","")
        return ''

        

    class Meta:
        model = AttendanceFRSRawData
        fields = ('id','person_id','name','department','time','attendance_status','attendance_check_point','data_source','handling_type','temperature','abnormal','attendance_date')

    def create(self, validated_data):
        validated_data['is_manual']  = True       
        return AttendanceFRSRawData.objects.create(**validated_data)




