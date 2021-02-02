from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from tdms.models import *
from django.contrib.auth.models import *
import time
from django.db import transaction, IntegrityError
from drf_extra_fields.fields import Base64ImageField
import os
from rest_framework.exceptions import APIException
import datetime
from datetime import timedelta
from core.models import TCoreUnit
from rest_framework.response import Response
from tdms.custom_filter import custom_filter
import pandas as pd
import numpy as np
import xlrd
from tdms.custom_delete import *
from django.db.models import Q
import re
from tdms.serializers.project import *
from geopy.distance import great_circle
from decimal import Decimal
import threading
from attendance.models import JoiningApprovedLeave,EmployeeAdvanceLeaves,EmployeeSpecialLeaves,AttendenceMonthMaster,AttendanceCarryForwardLeaveBalanceYearly,AttendenceLeaveAllocatePerMonthPerUser
from employee_leave_calculation import *
from custom_exception_message import *
from attendance import logger
from global_function import userdetails,department,designation
from math import radians, cos, sin, asin, sqrt
from users.models import TCoreUserDetail,LoginLogoutLoggedTable

'''
    Reason : NEW FLEXI ATTENDANCE SYTEM
    Author : Rupam Hazra
    Start Date: 14-05-2020
'''
#::::::::::::::::::::: NEW ATTENDANCE SYTEM :::::::::::::::#

class TdmsAttendanceAdvanceLeaveAddV2Serializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    is_confirm = serializers.BooleanField(required=False)
    leave_without_pay = serializers.DictField(required=False)
    leave = serializers.DictField(required=False)
    #result = serializers.DictField(required=False)
    class Meta:
        model = EmployeeAdvanceLeaves
        fields = '__all__'
        extra_fields= ['is_confirm','leave_without_pay','leave']
   
    
    
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
        print('document:', type(validated_data.get('document')), validated_data.get('document'))
        is_confirm = bool(validated_data.pop('is_confirm'))
        print('is_confirm',is_confirm)
        current_date = datetime.date.today()
        print('current_date',current_date,type(current_date))
        current_date_15= current_date + datetime.timedelta(days=15)
        print('current_date_15',current_date_15, type(current_date_15))
        
        request_datetime = validated_data.get('start_date').strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        request_datetime = datetime.datetime.strptime(request_datetime,"%Y-%m-%dT%H:%M:%S.%fZ").date()

        request_end_datetime = validated_data.get('end_date').strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        request_end_datetime = datetime.datetime.strptime(request_end_datetime,"%Y-%m-%dT%H:%M:%S.%fZ").date()

        balance_el = 0.0
        balance_ab = 0.0
        #how_many_days_el_taken = 0.0
        #how_many_days_ab_taken = 0.0
        balance_al = 0.0
        #how_many_days_al_taken = 0.0

        request_how_many_days = (validated_data.get('end_date') - validated_data.get('start_date')).days + 1
        print('request_how_many_days',request_how_many_days)

        request_start_date_month = validated_data.get('start_date').strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        request_start_date_month = calendar.month_name[datetime.datetime.strptime(request_start_date_month,"%Y-%m-%dT%H:%M:%S.%fZ").month]
        
        print('request_start_date_month',request_start_date_month)

        request_end_date_month = validated_data.get('end_date').strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        request_end_date_month = calendar.month_name[datetime.datetime.strptime(request_end_date_month,"%Y-%m-%dT%H:%M:%S.%fZ").month]
        
        print('request_end_date_month',request_end_date_month)
        #print('request_datetime',request_datetime,type(request_datetime))

        if request_datetime < current_date :
            custom_exception_message(self,None,"Start Date should not less than today's date!")
        
        if request_datetime > request_end_datetime:
            custom_exception_message(self,None,"End Date should be greater than or euqual to start date!")
        
        if current_date_15 > request_datetime and request_how_many_days > 5:
            custom_exception_message(self,None,"Sorry!! to avail leaves of more than 5 days, need to apply at least 15 days in advance.")

        # userdetails from TCoreUserDetail
        empDetails_from_coreuserdetail = TCoreUserDetail.objects.filter(
            cu_user=validated_data.get('employee'))[0]
        #print('empDetails_from_coreuserdetail',empDetails_from_coreuserdetail)
        employee_id = validated_data.get('employee')

        if empDetails_from_coreuserdetail:
            '''
                Normal Leave Count From approval request
            '''
            availed_hd_ab=0.0
            availed_ab=0.0
            availed_al = 0.0
            availed_hd_al=0.0

            # start :: modified by Rajesh #
            carry_forward_leave = AttendanceCarryForwardLeaveBalanceYearly.objects.filter(employee=employee_id,is_deleted=False).first() #.aggregate(Sum('leave_balance'))
            print('carry_forward_leave',carry_forward_leave)

            salary13_carry_forward_al = 0.0
            if carry_forward_leave and empDetails_from_coreuserdetail.salary_type and empDetails_from_coreuserdetail.salary_type.st_name=='13':
                if empDetails_from_coreuserdetail.is_confirm:
                    salary13_carry_forward_al = carry_forward_leave.leave_balance
                else:
                    approved_leave = JoiningApprovedLeave.objects.filter(employee=empDetails_from_coreuserdetail.cu_user,is_deleted=False).first()
                    salary13_carry_forward_al = float(carry_forward_leave.leave_balance) - float(approved_leave.el)


            # salary13_carry_forward_al = carry_forward_leave.leave_balance if carry_forward_leave and empDetails_from_coreuserdetail.salary_type and empDetails_from_coreuserdetail.salary_type.st_name=='13'and empDetails_from_coreuserdetail.is_confirm else 0.0

            month_master=AttendenceMonthMaster.objects.filter(month_start__date__lte=request_datetime,
                                                        month_end__date__gte=request_datetime,is_deleted=False).first()
            # end :: modified by Rajesh #

            attendence_daily_data = TdmsAttandanceDeviation.objects.filter(((
                Q(leave_type_changed_period__isnull=False)&(Q(leave_type_changed_period='FD')|Q(leave_type_changed_period='HD')))|
                (Q(leave_type_changed_period__isnull=True)&(Q(deviation_type='FD')|Q(deviation_type='HD')))),
                from_time__date__gte=month_master.year_start_date.date(), # modified by Rajesh
                attandance__employee=employee_id,is_requested=True).values('from_time__date').distinct()
            #print("attendence_daily_data",attendence_daily_data)
            date_list = [x['from_time__date'] for x in attendence_daily_data.iterator()]
            #print("date_list",date_list)
            
            availed_master_wo_reject_fd = TdmsAttandanceDeviation.objects.\
                filter((Q(approved_status=1)|Q(approved_status=2)|Q(approved_status=3)),
                        (Q(leave_type__isnull=False)|Q(leave_type_changed_period__isnull=False)),
                        attandance__employee=employee_id,
                        attandance__date__date__in=date_list,is_requested=True).annotate(
                            leave_type_final = Case(
                            When((Q(leave_type_changed_period__isnull=False)&Q(leave_type_changed_period='FD')),then=F('leave_type_changed')),
                            When((Q(leave_type_changed_period__isnull=True)&Q(deviation_type='FD')),then=F('leave_type')),
                            output_field=CharField()
                        ),
                        leave_type_final_hd = Case(
                            When((Q(leave_type_changed_period__isnull=False)&Q(leave_type_changed_period='HD')),then=F('leave_type_changed')),
                            When((Q(leave_type_changed_period__isnull=True)&Q(deviation_type='HD')),then=F('leave_type')),
                            output_field=CharField()
                        ),
                        ).values('leave_type_final','leave_type_final_hd','attandance__date__date').distinct()
            #print('availed_master_wo_reject_fd',availed_master_wo_reject_fd)
            if availed_master_wo_reject_fd:
                for data in date_list:
                    availed_FD=availed_master_wo_reject_fd.filter(attandance__date__date=data)
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
            #leave_allocation_per_month = 0.0
            
            if empDetails_from_coreuserdetail.is_confirm == False: 
                if empDetails_from_coreuserdetail.salary_type and empDetails_from_coreuserdetail.salary_type.st_name=='13':

                    leave_allocation_per_month_d = AttendenceLeaveAllocatePerMonthPerUser.objects.filter(
                    month__month_start__date__gte= str(request_end_datetime.year)+'-04-01',
                    month__month_start__date__lte = request_end_datetime,
                    employee=validated_data.get('employee')).aggregate(Sum('round_figure_not_confirm'))
                    #print('leave_allocation_per_month_d',leave_allocation_per_month_d)
                    leave_allocation_per_month = leave_allocation_per_month_d['round_figure_not_confirm__sum'] if leave_allocation_per_month_d['round_figure_not_confirm__sum'] else 0.0
                    #print('leave_allocation_per_month',leave_allocation_per_month)
                else:
                    leave_allocation_per_month_d = AttendenceLeaveAllocatePerMonthPerUser.objects.filter(
                    month__month_start__date__gte= str(request_end_datetime.year)+'-04-01',
                    month__month_start__date__lte = request_end_datetime,
                    employee=validated_data.get('employee')).aggregate(Sum('round_figure'))
                    leave_allocation_per_month = leave_allocation_per_month_d['round_figure__sum'] if leave_allocation_per_month_d['round_figure__sum'] else 0.0

                    #print('leave_allocation_per_month',leave_allocation_per_month.query)
            else:
                leave_allocation_per_month_d = AttendenceLeaveAllocatePerMonthPerUser.objects.filter(
                    month__month_start__date__gte= str(request_end_datetime.year)+'-04-01',
                    month__month_start__date__lte = request_end_datetime,
                    employee=validated_data.get('employee')).aggregate(Sum('round_figure'))


                #print('leave_allocation_per_month_d',leave_allocation_per_month_d.query)
                #print('leave_allocation_per_month_d',leave_allocation_per_month_d)
                leave_allocation_per_month = leave_allocation_per_month_d['round_figure__sum'] if leave_allocation_per_month_d['round_figure__sum'] else 0.0
                #print('leave_allocation_per_month',leave_allocation_per_month.query)
            
            print('leave_allocation_per_month',leave_allocation_per_month)           

            last_attendence_date = TdmsAttandanceDeviation.objects.all().values_list(
                'attandance__date__date',flat=True).order_by('-attandance__date__date')[0]
            print('last_attendence_date',last_attendence_date)

            empDetails_from_advance_leave = EmployeeAdvanceLeaves.objects.filter(
                (Q(approved_status = 'pending') | Q(approved_status = 'approved')),
                 employee=validated_data.get('employee'),is_deleted=False,
                 start_date__date__gt = last_attendence_date,
                 end_date__date__gt = last_attendence_date,
                 
                )
            print('empDetails_from_advance_leave',empDetails_from_advance_leave)

            how_many_days_al_taken = 0.0
            how_many_days_ab_taken = 0.0
            if empDetails_from_advance_leave:
                
                for e_empDetails_from_advance_leave in empDetails_from_advance_leave:
                    print('e_empDetails_from_advance_leave',e_empDetails_from_advance_leave.leave_type)
                    if e_empDetails_from_advance_leave.leave_type == 'AL':
                        how_many_days_al_taken = how_many_days_al_taken + (e_empDetails_from_advance_leave.end_date - 
                            e_empDetails_from_advance_leave.start_date).days + 1
                        print('how_many_days_al_taken:::::',how_many_days_al_taken)
                    
                    if e_empDetails_from_advance_leave.leave_type == 'AB':
                        how_many_days_ab_taken = how_many_days_ab_taken + (e_empDetails_from_advance_leave.end_date - 
                            e_empDetails_from_advance_leave.start_date).days + 1
                

            '''
                Section for count total leave count which means 
                total of advance leaves and approval leave
            '''
            
            print('how_many_days_al_taken',how_many_days_al_taken)
            # print('how_many_days_ab_taken',how_many_days_ab_taken)
            
            #print("availed_el",availed_el)
            print("availed_al",availed_al)
            
            total_availed_al=float(availed_al)+float(how_many_days_al_taken)+float(availed_hd_al/2) 

            print("total_availed_al",total_availed_al)

            '''
                Section for remaining leaves from granted leave - availed leave
            '''
            # balance_al = float(leave_allocation_per_month) - float(total_availed_al) # commented by Rajesh
            print('leave_allocation_per_month', leave_allocation_per_month)
            print('salary13_carry_forward_al', salary13_carry_forward_al)
            print('total_availed_al', total_availed_al)

            balance_al = float(leave_allocation_per_month)+ float(salary13_carry_forward_al) - float(total_availed_al) # modified by Rajesh


            print('balance_al',balance_al)
            if balance_al < 0:
                balance_al = 0

            if request_how_many_days > balance_al:
                leaves = round_down(balance_al)
                print('leaves',leaves,type(leaves),round_down(balance_al))

                leave_end_date_al = request_datetime + datetime.timedelta(days=(int(leaves)-1))
                if round_down(balance_al) > 0:
                    leave_end_date = leave_end_date_al
                else:
                    request_datetime = None
                    leave_end_date = leave_end_date_al
                    leave_end_date_al = None
                    
                    
                absent_leaves = request_how_many_days - round_down(balance_al)
                absent_leaves_start_date = leave_end_date + datetime.timedelta(days=1)
                print('leave',leaves,absent_leaves)

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
                    return validated_data
                else:
                    return {
                            'is_confirm':False,
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
                print('asddsfdsfdfdsfsdf')
                EmployeeAdvanceLeaves.objects.get_or_create(
                        employee = validated_data.get('employee'),
                        leave_type = validated_data.get('leave_type'),
                        start_date = request_datetime,
                        end_date = request_end_datetime,
                        document = validated_data.get('document'),
                        reason = validated_data.get('reason'),
                        created_by = validated_data.get('created_by'),
                        owned_by = validated_data.get('created_by'),
                    )
               	validated_data['is_confirm'] = True
               	return validated_data


class TdmsAttandanceAdminOdMsiReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = TdmsAttandanceDeviation
        fields = '__all__'

class TdmsAttendanceLeaveApprovalListV2Serializer(serializers.ModelSerializer):
    employee_name=serializers.SerializerMethodField(required=False)
    employee_id=serializers.SerializerMethodField(required=False)
    department = serializers.SerializerMethodField(required=False)
    designation = serializers.SerializerMethodField(required=False)
    reporting_head = serializers.SerializerMethodField(required=False)
    hod = serializers.SerializerMethodField(required=False)
    #documents=serializers.SerializerMethodField(required=False)

    def get_employee_name(self,TdmsAttandanceDeviation):
        if TdmsAttandanceDeviation.attandance:
            first_name=TdmsAttandanceDeviation.attandance.employee.first_name if TdmsAttandanceDeviation.attandance.employee.first_name  else ''
            last_name=TdmsAttandanceDeviation.attandance.employee.last_name if TdmsAttandanceDeviation.attandance.employee.last_name else ''
            name=first_name+" "+last_name
            return name
    def get_employee_id(self,TdmsAttandanceDeviation):
        if TdmsAttandanceDeviation.attandance:
            return TdmsAttandanceDeviation.attandance.employee.id

    def get_department(self,TdmsAttandanceDeviation):
        if TdmsAttandanceDeviation.attandance:
            return TdmsAttandanceDeviation.attandance.employee.cu_user.department.cd_name if TdmsAttandanceDeviation.attandance.employee.cu_user.department else None
    
    def get_designation(self,TdmsAttandanceDeviation):
        if TdmsAttandanceDeviation.attandance:
            return TdmsAttandanceDeviation.attandance.employee.cu_user.designation.cod_name if TdmsAttandanceDeviation.attandance.employee.cu_user.designation else None

    def get_reporting_head(self,TdmsAttandanceDeviation):
        if TdmsAttandanceDeviation.attandance:
            return TdmsAttandanceDeviation.attandance.employee.cu_user.reporting_head.first_name+' '+TdmsAttandanceDeviation.attandance.employee.cu_user.reporting_head.last_name if TdmsAttandanceDeviation.attandance.employee.cu_user.reporting_head else None

    def get_hod(self,TdmsAttandanceDeviation):
        if TdmsAttandanceDeviation.attandance:
            name = TdmsAttandanceDeviation.attandance.employee.cu_user.hod.first_name+' '+TdmsAttandanceDeviation.attandance.employee.cu_user.hod.last_name if TdmsAttandanceDeviation.attandance.employee.cu_user.hod else None
            return name

    # def get_documents(self, obj):
    #     leave_type = obj.leave_type_changed if obj.leave_type_changed else obj.leave_type
    #     return get_documents(request=self.context['request'],attendance_request=obj) if leave_type == 'AL' or leave_type == 'AB' else list()

    class Meta:
        model = TdmsAttandanceDeviation
        fields = '__all__'
        extra_fields=('employee_name','employee_id','department','designation','reporting_head','hod')
   
class AttandanceDeviationApprovaEditV2Serializer(serializers.ModelSerializer):
    approved_by = serializers.CharField(default=serializers.CurrentUserDefault())
    approved_at = serializers.DateTimeField(default=datetime.datetime.now())
    attendence_approvals=serializers.ListField(required=False)
    approved_status_name = serializers.CharField(required=False)
    class Meta:
        model = TdmsAttandanceDeviation
        #fields = ('id', 'approved_status', 'remarks', 'approved_by')
        fields = ('id','remarks','approved_status','approved_status_name','approved_at','approved_by','attendence_approvals')

    def create(self,validated_data):

        '''
            >>>) Admin can provide mass update by selecting as much request he wanted 
                1)Approved
                2)Reject
                3)Release
            1) >>>APPROVED LEAVES,OD ON BLUK AS WELL AS SINGLE DATA 
            2) >>>REJECT LEAVE AND REQUEST TYPE CALCULATION:-
                1)REJECTED LEAVES CALCULATION
                    #IF REQUEST LEAVES REJECTED REQUEST(FD,FOD) WILL BE 
                        CONVERTED TO "FD" AND "AB"
                    #IF REQUEST LEAVES REJECTED REQUEST(HD,POD) WILL BE 
                        CONVERTED TO "HD" AND "AB"
                2)MULTIPLE LEAVE FOR ONE DAY IS AUTO CONVERTED TO ONE TYPE OF LEAVE
                3) REJECTED OD CALCULATION
                    #IF REQUEST DURATION CROSS 240min REJECTED REQUEST WILL BE 
                        CONVERTED TO "FD" AND "AL" IF LEAVE AVAILABLE THEN "AB"
                    #IF REQUEST DURATION LESS THAN 240min REJECTED REQUEST WILL BE 
                        CONVERTED TO "HD" AND "AL" IF LEAVE AVAILABLE THEN "AB"
            3) >>>RELEASE LEAVE AND REQUEST TYPE 
            
        '''

        print(validated_data)
        updated_by = validated_data.get('approved_by')
        remarks = validated_data.get('remarks')
        approved_status_res = ''
        approved_status_name = ''

        for data in validated_data.get('attendence_approvals'):
            approved_status= data['approved_status']
            
            cur_date = datetime.datetime.now()
            
            if approved_status=='approved':
                approved_status_name = data['approved_status']
                approved_status_res = TdmsAttandanceDeviation.objects.filter(approved_status = '2', id= data['req_id'])
                approved_data = TdmsAttandanceDeviation.objects.filter(id=data['req_id']).update(approved_status=2,
                                                                        approved_by=updated_by,remarks=remarks)
                req_type = TdmsAttandanceDeviation.objects.get(id=data['req_id']).deviation_type
                print("approved_data",approved_data,req_type)
                present_data = TdmsAttendance.objects.filter(id__in=TdmsAttandanceDeviation.objects.filter(
                                        (Q(deviation_type='OD')),id=data['req_id']).values_list('attandance')
                                        ).update(is_present=True,day_remarks='Present')
                
                if approved_data:
                    logger.log(self.context['request'].user,'approved'+" "+req_type,
                    'Approval','pending','Approved','PMS-TeamAttendance -AttendenceApproval') 

            elif approved_status=='reject':
                approved_status_name = data['approved_status']
                approved_status_res = TdmsAttandanceDeviation.objects.filter(approved_status = 3, id= data['req_id'])
                print("approved_status")
                
               
                if TdmsAttandanceDeviation.objects.filter(deviation_type='FD',id=data['req_id']) :
                    
                    # print("full day ")
                    TdmsAttandanceDeviation.objects.filter(deviation_type='FD',id=data['req_id']).\
                                                            update(approved_status=3,approved_by=updated_by,remarks=remarks,
                                                            leave_type_changed_period='FD',leave_type_changed='AB',approved_at=cur_date)
                
                elif TdmsAttandanceDeviation.objects.filter(deviation_type='OD',id=data['req_id']) :
                    # print("halfday day ")
                    duration_length=TdmsAttandanceDeviation.objects.get(id=data['req_id'],is_requested=True)
                    prev_cal = TdmsAttandanceDeviation.objects.filter(attandance=duration_length.attandance,is_requested=True,approved_status=3)
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
                            attendance_request = TdmsAttandanceDeviation.objects.filter(deviation_type='OD',id=data['req_id'])

                            tcore_user = TCoreUserDetail.objects.get(cu_user=attendance_request[0].attandance.employee)
                            calculated_balance = all_leave_calculation_upto_applied_date(
                                date_object=attendance_request[0].attandance.date.date(),user=tcore_user)        
                                    
                            advance_leave_calculation = advance_leave_calculation_excluding_current_month(
                                tcore_user=tcore_user, date_object=attendance_request[0].attandance.date.date())
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
                            
                           
                        
                            attendance_request.update(
                                approved_status=3,
                                approved_by=updated_by,remarks=remarks,
                                leave_type_changed_period='FD',leave_type_changed=leave_type_changed,approved_at=cur_date)
                            for x in ids:
                                TdmsAttandanceDeviation.objects.filter(id=x).update(
                                                        approved_by=updated_by,
                                                        leave_type_changed_period='FD',
                                                        leave_type_changed=leave_type_changed,approved_at=cur_date)
                        else:
                            attendance_request = TdmsAttandanceDeviation.objects.filter(deviation_type='OD',id=data['req_id'])
                            tcore_user = TCoreUserDetail.objects.get(cu_user=attendance_request[0].attandance.employee)
                            calculated_balance = all_leave_calculation_upto_applied_date(
                                date_object=attendance_request[0].attandance.date, user=tcore_user)
                                    
                            advance_leave_calculation = advance_leave_calculation_excluding_current_month(
                                tcore_user=tcore_user, date_object=attendance_request[0].attandance.date)
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

                            attendance_request.update(
                                approved_status=3,
                                approved_by=updated_by,
                                remarks=remarks,
                                leave_type_changed_period='HD',
                                leave_type_changed=leave_type_changed,
                                approved_at=cur_date)
                    else:
                        # print("duration_length",duration_length)
                        if duration_length.duration < 240:
                            attendance_request = TdmsAttandanceDeviation.objects.filter(deviation_type='OD',id=data['req_id'])

                            tcore_user = TCoreUserDetail.objects.get(cu_user=attendance_request[0].attandance.employee)
                            calculated_balance = all_leave_calculation_upto_applied_date(
                                date_object=attendance_request[0].attandance.date,user=tcore_user)
        
                            advance_leave_calculation = advance_leave_calculation_excluding_current_month(
                                tcore_user=tcore_user, date_object=attendance_request[0].attandance.date)
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

                            attendance_request.update(
                                approved_status=3,
                                approved_by=updated_by,
                                remarks=remarks,
                                leave_type_changed_period='HD',
                                leave_type_changed=leave_type_changed,
                                approved_at=cur_date)
                        else:
                            attendance_request = TdmsAttandanceDeviation.objects.filter(deviation_type='OD',id=data['req_id'])
                            #print('attendance_request',attendance_request[0].attandance.employee)
                            tcore_user = TCoreUserDetail.objects.get(cu_user=attendance_request[0].attandance.employee)
                            #print('tcore_user',tcore_user)
                            calculated_balance = all_leave_calculation_upto_applied_date(
                                date_object=attendance_request[0].attandance.date.date(),user=tcore_user)
                            
                            advance_leave_calculation = advance_leave_calculation_excluding_current_month(
                                tcore_user=tcore_user, date_object=attendance_request[0].attandance.date.date())
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

                            attendance_request.update(
                                approved_status=3,
                                approved_by=updated_by,
                                remarks=remarks,
                                leave_type_changed_period='FD',
                                leave_type_changed=leave_type_changed,
                                approved_at=cur_date)

                elif TdmsAttandanceDeviation.objects.filter(deviation_type='HD',id=data['req_id']) :
                    # print("halfday day ")
                    duration_length=TdmsAttandanceDeviation.objects.get(id=data['req_id'],is_requested=True)
                    prev_cal = TdmsAttandanceDeviation.objects.filter(
                        attandance=duration_length.attandance,is_requested=True,approved_status='3')

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
                            TdmsAttandanceDeviation.objects.filter(deviation_type='HD',id=data['req_id']).update(
                                approved_status=3,approved_by=updated_by,remarks=remarks,leave_type_changed_period='FD',
                                leave_type_changed='AB',approved_at=cur_date)

                            for x in ids:
                                TdmsAttandanceDeviation.objects.filter(id=x).update(
                                                                    approved_by=updated_by,
                                                                    leave_type_changed_period='FD',leave_type_changed='AB',
                                                                    approved_at=cur_date)
                        else:
                            TdmsAttandanceDeviation.objects.filter(deviation_type='HD',id=data['req_id']).update(
                                approved_status=3,approved_by=updated_by,remarks=remarks,
                                leave_type_changed_period='HD',leave_type_changed='AB',approved_at=cur_date)
                    else:
                        # print("duration_length",duration_length)
                        if duration_length.duration < 240:
                            TdmsAttandanceDeviation.objects.filter(deviation_type='HD',id=data['req_id']).update(
                                approved_status=3,approved_by=updated_by,remarks=remarks,leave_type_changed_period='HD',
                                leave_type_changed='AB',approved_at=cur_date)
                        else:
                            TdmsAttandanceDeviation.objects.filter(deviation_type='HD',id=data['req_id']).update(
                                approved_status=3,approved_by=updated_by,remarks=remarks,
                                leave_type_changed_period='FD',leave_type_changed='AB',approved_at=cur_date)

                req_type = TdmsAttandanceDeviation.objects.get(id=data['req_id']).deviation_type

                logger.log(self.context['request'].user,'rejected'+" "+req_type,
                    'Approval','pending','Rejected','PMS-TeamAttendance-AttendenceApproval') 
                

                ######################### MAIL SEND ################################
                
                od_detail = TdmsAttandanceDeviation.objects.filter(deviation_type='OD',id=data['req_id'])
              
                # if od_detail:
                #     full_name = userdetails(od_detail.values()[0]['justified_by_id'])
                #     date = (od_detail.values()[0]['from_time']).date()
                #     rejected_by = userdetails(updated_by.id)
                #     rejected_at = cur_date
                #     email = od_detail.values_list('attandance__employee__email',flat=True)[0]

                #     # ============= Mail Send ============== #
                #     if email:
                #         mail_data = {
                #                     "name": full_name,
                #                     "date": date,
                #                     "rejected_by": rejected_by,
                #                     "rejected_date": cur_date.date()
                #             }
                #         print('mail_data',mail_data)
                #         mail_class = GlobleMailSend('OD_reject', [email])
                #         mail_thread = Thread(target = mail_class.mailsend, args = (mail_data,))
                #         mail_thread.start()
                ###########################################

            elif approved_status=='relese':
                approved_status_name = data['approved_status']
                approved_status_res = TdmsAttandanceDeviation.objects.filter(approved_status = '5', id = data['req_id'])
                req_type = TdmsAttandanceDeviation.objects.get(id=data['req_id'])
                before_data = req_type.approved_status
                TdmsAttandanceDeviation.objects.filter(id=data['req_id']).update(
                    approved_status=5,
                    justification=None,
                    approved_by=updated_by,
                    remarks=remarks,
                    deviation_type=None,
                    is_requested=False,
                    leave_type = None,
                    leave_type_changed = None,
                    leave_type_changed_period = None
                    )

                logger.log(self.context['request'].user,'rejected'+" "+req_type.deviation_type,
                    'Approval',before_data,'Relese','PMS-TeamAttendance-AttendenceApproval') 
                
        #print('approved_status_res',approved_status_res)
        validated_data['approved_status'] = approved_status_res[0].approved_status
        validated_data['approved_status_name'] = approved_status_name
        data = validated_data

        return data

class AttandanceDeviationJustificationV2Serializer(serializers.ModelSerializer):

    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = TdmsAttandanceDeviation
        fields = ('__all__')

    
    def update(self,instance, validated_data):
        # print("instance",instance)
        updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
        
        try:
            print('validated_data',validated_data)
            updated_by = validated_data.get('updated_by')
            date = self.context['request'].query_params.get('date', None)
            print('date',type(date))
            #################################################################################
            #if you find error in datetime please remove only datetime from "date_object"   #
            #################################################################################
            
            date_object = datetime.datetime.strptime(date, '%Y-%m-%d').date()
            print('date_object',type(date_object))
            employee_id=self.context['request'].query_params.get('employee_id', None)
            total_grace={}
            data_dict = {}
            with transaction.atomic():
                request_type=validated_data.get('deviation_type') if validated_data.get('deviation_type') else ""
                present=TdmsAttandanceDeviation.objects.filter(id=instance.id,attandance__is_present=True)
                print('present',present)
                # REQUEST ONLY IF PRESENT AND HAVE DIVIATION
                if present:
                    print('request_type',request_type)
                    #*****************present but user want to give HD or FD request*********************************************************
                    if request_type == 'HD' or request_type == 'FD':
                        tcore_user = TCoreUserDetail.objects.get(cu_user=employee_id)
                        #print('tcore_user',tcore_user)
                        #balance_al, total_availed_al, leave_allocation_per_month = self.all_leave_calculation_upto_applied_date(date_object=date_object, user=tcore_user)
                        #print('balance_al:',balance_al)
                        advance_leave_calculation = advance_leave_calculation_excluding_current_month(tcore_user=tcore_user, date_object=date_object)
                        #print('advance_leave_calculation', advance_leave_calculation)
                        
                        leave_type=validated_data.get('leave_type')

                        
                        #return validated_data
                        if leave_type in ('CL','SL','EL'):

                            result = all_leave_calculation_upto_applied_date_tdms(date_object=date_object, user=tcore_user)
                            balance_el = result['el_balance']
                            balance_sl = result['sl_balance']
                            balance_cl = result['cl_balance']

                            if  leave_type == 'SL' :
                                if balance_sl>0.0:
                                    duration_length=TdmsAttandanceDeviation.objects.get(id=instance.id,is_requested=False)
                                    if request_type == 'HD':
                                        if duration_length.duration <=240 :
                                            # raise serializers.ValidationError("Please apply half day Your diviation exceeds 2.5 Hours")
                                    
                                            justify_attendence=TdmsAttandanceDeviation.objects.filter(id=instance.id,is_requested=False).\
                                                    update(
                                                    deviation_type=request_type,
                                                    is_requested=True,
                                                    approved_status=1,
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                            return validated_data

                                        elif duration_length.duration > 240 :
                                            custom_exception_message(self,None,"Please apply full day Your diviation exceeds 4 Hours")
                                            
                                    elif request_type == 'FD' and balance_sl>0.5:
                                        justify_attendence=TdmsAttandanceDeviation.objects.filter(id=instance.id,is_requested=False).\
                                            update(
                                            deviation_type=request_type,
                                            is_requested=True,
                                            approved_status=1,
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
                                    
                                    duration_length=TdmsAttandanceDeviation.objects.get(id=instance.id,is_requested=False)
                                    if request_type == 'HD':
                                        if duration_length.duration <=240:
                                            justify_attendence=TdmsAttandanceDeviation.objects.filter(id=instance.id,is_requested=False).\
                                                    update(
                                                    deviation_type=request_type,
                                                    is_requested=True,
                                                    approved_status=1,
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                            return validated_data
                                        
                                        elif duration_length.duration > 240 :
                                            custom_exception_message(self,None,"Please apply full day Your diviation exceeds 4 Hours")
                                            
                                    elif request_type == 'FD' and balance_cl>0.5:
                                        justify_attendence=TdmsAttandanceDeviation.objects.filter(id=instance.id,is_requested=False).\
                                            update(
                                            deviation_type=request_type,
                                            is_requested=True,
                                            approved_status=1,
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

                                    duration_length=TdmsAttandanceDeviation.objects.get(id=instance.id,is_requested=False)
                                    if request_type == 'HD':
                                        if duration_length.duration <=240:
                                            justify_attendence=TdmsAttandanceDeviation.objects.filter(id=instance.id,is_requested=False).\
                                                    update(
                                                    deviation_type=request_type,
                                                    is_requested=True,
                                                    approved_status=1,
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                            return validated_data

                                        elif duration_length.duration > 240:
                                            custom_exception_message(self,None,"Please apply full day Your diviation exceeds 4 Hours")
                                            return validated_data
                                    
                                    elif request_type == 'FD' and balance_el>0.5:
                                        justify_attendence=TdmsAttandanceDeviation.objects.filter(id=instance.id,is_requested=False).\
                                            update(
                                            deviation_type=request_type,
                                            is_requested=True,
                                            approved_status=1,
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

                        
                        elif leave_type =='AL':

                            result = all_leave_calculation_upto_applied_date_tdms(date_object=date_object, user=tcore_user)
                            balance_al = result['total_available_balance']
                            total_availed_al = result['total_consumption']
                            leave_allocation_per_month = result['total_accumulation']

                            if balance_al>0.0:
                                actual_balance = balance_al + advance_leave_calculation['advance_leave_balance']
                                is_balance_available = actual_balance > 0
                                print('is_balance_available', is_balance_available)
                                if advance_leave_calculation['is_advance_leave_taken'] and advance_leave_calculation['is_leave_taken_from_current_month'] and not is_balance_available:
                                    custom_exception_message(self,None,"Not enough leave balance. Your current month leave has been adjusted with advance leave.")
                                else:
                                    duration_length=TdmsAttandanceDeviation.objects.get(id=instance.id,is_requested=False)
                                    if request_type == 'HD':
                                        if duration_length.duration <=240:
                                            justify_attendence=TdmsAttandanceDeviation.objects.filter(id=instance.id,is_requested=False).\
                                                    update(
                                                    deviation_type=request_type,
                                                    is_requested=True,
                                                    approved_status=1,
                                                    request_date=datetime.datetime.now(),
                                                    justified_at=datetime.datetime.now(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                            return validated_data
                                        
                                        elif duration_length.duration > 240 :
                                            custom_exception_message(self,None,"Please apply full day Your diviation exceeds 4 Hours")
                                            
                                            
                                    elif request_type == 'FD' and balance_al>0.5:
                                        if actual_balance > 0.5:
                                            justify_attendence=TdmsAttandanceDeviation.objects.filter(id=instance.id,is_requested=False).\
                                                update(
                                                deviation_type=request_type,
                                                is_requested=True,
                                                approved_status=1,
                                                request_date=datetime.datetime.now(),
                                                justified_at=datetime.datetime.now(),
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
                            justify_attendence=TdmsAttandanceDeviation.objects.filter(id=instance.id,is_requested=False).\
                                update(
                                deviation_type=request_type,
                                is_requested=True,
                                approved_status=2,
                                request_date=datetime.datetime.now(),
                                justified_at=datetime.datetime.now(),
                                justification=validated_data.get('justification'),
                                justified_by=updated_by,
                                leave_type=validated_data.get('leave_type')
                                )

                            return validated_data

                        elif leave_type == 'AB':
                            justify_attendence=TdmsAttandanceDeviation.objects.filter(id=instance.id,is_requested=False).\
                                        update(
                                        deviation_type=request_type,
                                        is_requested=True,
                                        approved_status=1,
                                        request_date=datetime.datetime.now(),
                                        justified_at=datetime.datetime.now(),
                                        justification=validated_data.get('justification'),
                                        justified_by=updated_by,
                                        leave_type=validated_data.get('leave_type')
                                        )
                            return validated_data
                    
                    #*****************As the user is already present hence partial OD********************************************************
                    elif request_type == 'OD': 
                        
                        is_auto_od = TdmsAttandanceDeviation.objects.only('is_auto_od').get(id=instance.id,is_requested=False).is_auto_od
                        print('is_auto_od',is_auto_od)
                        if is_auto_od:
                            justify_attendence=TdmsAttandanceDeviation.objects.filter(id=instance.id,is_requested=False).\
                                update(
                                deviation_type='OD',
                                is_requested=True,
                                approved_status=2,
                                request_date=datetime.datetime.now(),
                                justified_at=datetime.datetime.now(),
                                justification=validated_data.get('justification'),
                                justified_by=updated_by,
                                remarks='Auto Approved'
                                )
                        else:
                            justify_attendence=TdmsAttandanceDeviation.objects.filter(id=instance.id,is_requested=False).\
                                update(
                                deviation_type='OD',
                                is_requested=True,
                                approved_status=1,
                                request_date=datetime.datetime.now(),
                                justified_at=datetime.datetime.now(),
                                justification=validated_data.get('justification'),
                                justified_by=updated_by
                                )

                        return validated_data
                    

                    return validated_data
                
                
                #REQUEST ONLY IF User ABSENT 
                else:

                    if request_type == 'FD':
                        tcore_user = TCoreUserDetail.objects.get(cu_user=employee_id)
                        #worst_late_beanchmark = tcore_user.worst_late
                        #balance_al, total_availed_al, leave_allocation_per_month = self.all_leave_calculation_upto_applied_date(date_object=date_object, user=tcore_user)
                        #print('balance_al:',balance_al)
                        
                        advance_leave_calculation = advance_leave_calculation_excluding_current_month(tcore_user=tcore_user, date_object=date_object)
                        #print('advance_leave_calculation', advance_leave_calculation)
                        leave_type=validated_data.get('leave_type')

                        if leave_type in ('CL','SL','EL'):

                            result = all_leave_calculation_upto_applied_date(date_object=date_object, user=tcore_user)
                            balance_el = result['el_balance']
                            balance_sl = result['sl_balance']
                            balance_cl = result['cl_balance']

                            if  leave_type == 'SL' :
                                if balance_sl>0.0:
                                    duration_length=TdmsAttandanceDeviation.objects.get(id=instance.id,is_requested=False)
                                    if request_type == 'HD':
                                        if duration_length.duration <=240 :
                                            # raise serializers.ValidationError("Please apply half day Your diviation exceeds 2.5 Hours")
                                    
                                            justify_attendence=TdmsAttandanceDeviation.objects.filter(id=instance.id,is_requested=False).\
                                                    update(
                                                    deviation_type=request_type,
                                                    is_requested=True,
                                                    approved_status=1,
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                            return validated_data

                                        elif duration_length.duration > 240 :
                                            custom_exception_message(self,None,"Please apply full day Your diviation exceeds 4 Hours")
                                            
                                    elif request_type == 'FD' and balance_sl>0.5:
                                        justify_attendence=TdmsAttandanceDeviation.objects.filter(id=instance.id,is_requested=False).\
                                            update(
                                            deviation_type=request_type,
                                            is_requested=True,
                                            approved_status=1,
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
                                    
                                    duration_length=TdmsAttandanceDeviation.objects.get(id=instance.id,is_requested=False)
                                    if request_type == 'HD':
                                        if duration_length.duration <=240:
                                            justify_attendence=TdmsAttandanceDeviation.objects.filter(id=instance.id,is_requested=False).\
                                                    update(
                                                    deviation_type=request_type,
                                                    is_requested=True,
                                                    approved_status=1,
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                            return validated_data
                                        
                                        elif duration_length.duration > 240 :
                                            custom_exception_message(self,None,"Please apply full day Your diviation exceeds 4 Hours")
                                            
                                    elif request_type == 'FD' and balance_cl>0.5:
                                        justify_attendence=TdmsAttandanceDeviation.objects.filter(id=instance.id,is_requested=False).\
                                            update(
                                            deviation_type=request_type,
                                            is_requested=True,
                                            approved_status=1,
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

                                    duration_length=TdmsAttandanceDeviation.objects.get(id=instance.id,is_requested=False)
                                    if request_type == 'HD':
                                        if duration_length.duration <=240:
                                            justify_attendence=TdmsAttandanceDeviation.objects.filter(id=instance.id,is_requested=False).\
                                                    update(
                                                    deviation_type=request_type,
                                                    is_requested=True,
                                                    approved_status=1,
                                                    request_date=datetime.date.today(),
                                                    justified_at=datetime.date.today(),
                                                    justification=validated_data.get('justification'),
                                                    justified_by=updated_by,
                                                    leave_type=validated_data.get('leave_type')
                                                    )

                                            return validated_data

                                        elif duration_length.duration > 240:
                                            custom_exception_message(self,None,"Please apply full day Your diviation exceeds 4 Hours")
                                            return validated_data
                                    
                                    elif request_type == 'FD' and balance_el>0.5:
                                        justify_attendence=TdmsAttandanceDeviation.objects.filter(id=instance.id,is_requested=False).\
                                            update(
                                            deviation_type=request_type,
                                            is_requested=True,
                                            approved_status=1,
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

                        elif leave_type =='AL':

                            result = all_leave_calculation_upto_applied_date(date_object=date_object, user=tcore_user)
                            balance_al = result['total_available_balance']
                            total_availed_al = result['total_consumption']
                            leave_allocation_per_month = result['total_accumulation']

                            if balance_al>0.0:
                                actual_balance = balance_al + advance_leave_calculation['advance_leave_balance']
                                is_balance_available = actual_balance > 0
                                print('is_balance_available', is_balance_available)
                                if advance_leave_calculation['is_advance_leave_taken'] and advance_leave_calculation['is_leave_taken_from_current_month'] and not is_balance_available:
                                    custom_exception_message(self,None,"Not enough leave balance. Your current month leave has been adjusted with advance leave.")
                                else:
                                    duration_length=TdmsAttandanceDeviation.objects.get(id=instance.id,is_requested=False)
                                    
                                    if request_type == 'FD' and balance_al>0.5:
                                        if actual_balance > 0.5:
                                            justify_attendence=TdmsAttandanceDeviation.objects.filter(id=instance.id,is_requested=False).\
                                                update(
                                                deviation_type=request_type,
                                                is_requested=True,
                                                approved_status=1,
                                                request_date=datetime.datetime.now(),
                                                justified_at=datetime.datetime.now(),
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
                            justify_attendence=TdmsAttandanceDeviation.objects.filter(id=instance.id,is_requested=False).\
                                update(
                                deviation_type=request_type,
                                is_requested=True,
                                approved_status=1,
                                request_date=datetime.datetime.now(),
                                justified_at=datetime.datetime.now(),
                                justification=validated_data.get('justification'),
                                justified_by=updated_by,
                                leave_type=validated_data.get('leave_type')
                                )

                            return validated_data

                        elif leave_type == 'AB':
                            justify_attendence=TdmsAttandanceDeviation.objects.filter(id=instance.id,is_requested=False).\
                                        update(
                                        deviation_type=request_type,
                                        is_requested=True,
                                        approved_status=1,
                                        request_date=datetime.datetime.now(),
                                        justified_at=datetime.datetime.now(),
                                        justification=validated_data.get('justification'),
                                        justified_by=updated_by,
                                        leave_type=validated_data.get('leave_type')
                                        )

                            return validated_data


                    elif request_type == 'OD':
                        justify_attendence=TdmsAttandanceDeviation.objects.filter(id=instance.id,is_requested=False).\
                            update(
                            deviation_type='OD',
                            is_requested=True,
                            approved_status=1,
                            request_date=datetime.datetime.now(),
                            justified_at=datetime.datetime.now(),
                            justification=validated_data.get('justification'),
                            justified_by=updated_by,
                            )

                        return validated_data
                   
                    return validated_data

        except Exception as e:
            raise e

class AttendanceAddV2Serializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    employee = serializers.CharField(default=serializers.CurrentUserDefault())
    date = serializers.DateTimeField(required=True)
    login_time = serializers.DateTimeField(required=True)

    class Meta:
        model = TdmsAttendance
        fields = ('id', 'type', 'employee', 'user_project', 'date', 'login_time', 'login_latitude', 'login_longitude',
                  'login_address',
                  'logout_time', 'logout_latitude', 'logout_longitude', 'logout_address', 'approved_status',
                  'justification',
                  'created_by', 'owned_by',)

class AttendanceLogOutV2Serializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    is_checkout = serializers.BooleanField(required=False)
    is_checkout_auto_od = serializers.BooleanField(required=False)
    device_details = serializers.CharField(required=False,allow_blank=True,allow_null=True)

    class Meta:
        model = TdmsAttendance
        fields = ('id', 'logout_time', 'logout_latitude', 'logout_longitude', 'logout_address', 'updated_by','is_checkout','is_checkout_auto_od','device_details')


    def update(self, instance, validated_data):
        time = validated_data.get("logout_time")
        latitude = validated_data.get("logout_latitude")
        longitude = validated_data.get("logout_longitude")
        address = validated_data.get("logout_address")
        updated_by = validated_data.get("updated_by")
        is_checkout = validated_data.get("is_checkout")
        is_checkout_auto_od = validated_data.get("is_checkout_auto_od")
        device_details =  validated_data.get("device_details") if 'device_details' in validated_data else None
        request = self.context['request']
        token_full = request.META.get('HTTP_AUTHORIZATION')
        token = token_full.split(' ')
        is_checkout = validated_data.get("is_checkout") if 'is_checkout' in validated_data else False
        is_checkout_auto_od = validated_data.get("is_checkout_auto_od") if 'is_checkout_auto_od' in validated_data else False

        last_login_id = TdmsAttandanceLog.objects.filter(attandance = instance, login_logout_check='Login', login_id__isnull=True).values_list('id',flat=True).last()
        logout_log_details, created = TdmsAttandanceLog.objects.get_or_create(
                    attandance = instance,
                    login_logout_check = 'Logout',
                    time=time,
                    latitude=latitude,
                    longitude=longitude,
                    address=address,
                    created_by=updated_by,
                    owned_by=updated_by,
                    login_id = last_login_id,
                    is_checkout=is_checkout,
                    is_checkout_auto_od=is_checkout_auto_od,
                    device_details=device_details,
                    token = token[1]
                )
        # sf = TdmsAttendance.objects.filter(employee_id= 4).values()        
        # print('logout_log_details',sf)
        self.add_deviations(instance.id, time, updated_by,logout_log_details,last_login_id)
        return instance

    def add_deviations(self, att_id, log_out_time, owned_by,logout_log_details,last_login_id):
        from datetime import timedelta
        owned_by = owned_by
        att_id = att_id
        #last_login  = TdmsAttandanceLog.objects.filter(login_logout_check='Login').values_list('id',flat=True).last()
        print('last_login_id',last_login_id)
        print('logout_log_details.id',logout_log_details.id)
        log_details = TdmsAttandanceLog.objects.filter(
            attandance_id=att_id,
            pk__gte=last_login_id,
            pk__lte=logout_log_details.id
            )

        #print('log_details',log_details)
        flag = 0
        check_len = 0
        if len(log_details) == 1:
            # print("if len(log_details) == 1")
            for log in log_details:
                # print("log 11",log)
                from_time = log.time
                to_time = log_out_time
                # print("step 1", from_time, to_time)
                self.calculate_deviation(att_id, from_time, to_time, owned_by)
        else:
            # print("else len(log_details) == 1")
            for log in log_details:
                # print("log 22",log)
                check_len += 1
                # print("check_len: ", check_len)
                checkout = log.is_checkout
                checkout_auto_od = log.is_checkout_auto_od
                # print("checkout :", checkout)
                if checkout == True and checkout_auto_od == True:
                    # print("if checkout == True:")
                    if flag == 1:
                        # print("if flag == 1:")
                        # if not to_time:
                        if check_len == len(log_details):
                            to_time = log_out_time
                            print("to_time:", to_time)
                            self.calculate_deviation(att_id, from_time, to_time, owned_by,is_auto_od=True)
                    else:
                        # print("else flag == 1:")
                        flag = 1
                        from_time = log.time

                        # print("from_time:", from_time)

                # if checkout == False and checkout_auto_od == True:
                #     # print("if checkout == True:")
                #     if flag == 1:
                #         # print("if flag == 1:")
                #         # if not to_time:
                #         if check_len == len(log_details):
                #             to_time = log_out_time
                #             print("to_time:", to_time)
                #             self.calculate_deviation(att_id, from_time, to_time, owned_by,is_auto_od=True)
                #     else:
                #         # print("else flag == 1:")
                #         flag = 1
                #         from_time = log.time

                #         # print("from_time:", from_time)

                elif checkout == True and checkout_auto_od == False:
                    # print("if checkout == True:")
                    if flag == 1:
                        # print("if flag == 1:")
                        # if not to_time:
                        if check_len == len(log_details):
                            to_time = log_out_time
                            print("to_time:", to_time)
                            self.calculate_deviation(att_id, from_time, to_time, owned_by,is_auto_od=False)
                    else:
                        # print("else flag == 1:")
                        flag = 1
                        from_time = log.time
                else:
                    # print("else checkout == True:")
                    if flag == 1:
                        flag = 0
                        to_time = log.time
                        # print("to_time", to_time)
                        self.calculate_deviation(att_id, from_time, to_time, owned_by)

    def calculate_deviation(self, att_id, from_time, to_time, owned_by,is_auto_od=False):

        data_dict = {}
        # print("===calculate_deviation===")
        print("from_time",from_time,to_time)
        # print("to_time",to_time)
        dev_time = (to_time - from_time)
        # dev_time = (from_time - to_time)
        # print("dev_time",dev_time)
        time_deviation = (datetime.datetime.min + dev_time).time().strftime('%H:%M:%S')
        data_dict["attandance_id"] = att_id
        data_dict["from_time"] = from_time.strftime('%Y-%m-%dT%H:%M:%S')
        data_dict["to_time"] = to_time.strftime('%Y-%m-%dT%H:%M:%S')
        data_dict["deviation_time"] = time_deviation
        data_dict["owned_by"] = owned_by
        data_dict["duration"] = round((dev_time.seconds)/60)
        data_dict['is_auto_od'] = is_auto_od
        if data_dict["duration"] >= 1:
            if data_dict:
                TdmsAttandanceDeviation.objects.get_or_create(**data_dict)

        self.logout()

    def logout(self):
        request = self.context['request']
        token_full = request.META.get('HTTP_AUTHORIZATION')
        token= token_full.split(' ')
        LoginLogoutLogged = LoginLogoutLoggedTable.objects.filter(user=request.user, token=token[1])
        if LoginLogoutLogged:
            LoginLogoutLogged.update(logout_time=datetime.datetime.now())
            request._auth.delete()


class AttendanceUpdateLogOutTimeFailedOnLogoutV2Serializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = TdmsAttendance
        fields = ('id', 'logout_time', 'updated_by')
    
    def update(self, instance, validated_data):
        time = validated_data.get("logout_time")
        updated_by = validated_data.get("updated_by")
        last_login_id = TdmsAttandanceLog.objects.filter(login_logout_check='Login').values_list('id',flat=True).last()
        logout_log_details, created = TdmsAttandanceLog.objects.get_or_create(
                    attandance = instance,
                    login_logout_check = 'Logout',
                    time=time,
                    created_by=updated_by,
                    owned_by=updated_by,
                    login_id = last_login_id
        )
        return instance

class AttendanceListV2Serializer(serializers.ModelSerializer):
    class Meta:
        model = TdmsAttendance
        fields = ('id', 'type', 'employee', 'user_project', 'date','day_remarks','is_present')

class AttandanceALLDetailsListByPermissonV2Serializer(serializers.ModelSerializer):
    employee_details = serializers.SerializerMethodField()
    # log_details = serializers.SerializerMethodField()
    login_logout_details = serializers.SerializerMethodField()
    user_project = ProjectDetailsSerializer()

    
    def get_employee_details(self, TdmsAttendance):
        from users.models import TCoreUserDetail
        from users.serializers import UserModuleSerializer, UserSerializer
        user_details = TCoreUserDetail.objects.filter(cu_user=TdmsAttendance.employee)  # Whatever your query may be
        serializer = UserModuleSerializer(instance=user_details, many=True)
        return serializer.data

    def get_login_logout_details(self, TdmsAttendance):

        login_logout_list = list()
        queryset_att_log = TdmsAttandanceLog.objects.filter(attandance=TdmsAttendance.id,login_logout_check__in=('Logout',))
        # print("TdmsAttendance: ",TdmsAttendance)
        if queryset_att_log:
            for e_queryset_att_log in queryset_att_log:
                login_logout_dict=dict()
                login_logout_dict['login_time'] = TdmsAttandanceLog.objects.filter(
                    attandance=TdmsAttendance.id,id=e_queryset_att_log.login_id).values_list('time',flat=True).first()
                login_logout_dict['logout_time'] = e_queryset_att_log.time
                login_logout_list.append(login_logout_dict)
        
                attendance_deviation = TdmsAttandanceDeviation.objects.filter(
                    attandance_id=TdmsAttendance.id,
                    from_time__gte=login_logout_dict['login_time'],
                    to_time__lte=login_logout_dict['logout_time']
                    )
                serializer = AttandanceDeviationSerializer(instance=attendance_deviation, many=True)
                login_logout_dict['deviation_details']= serializer.data
        # print("serializer.data: ",serializer.data)
        return login_logout_list

    class Meta:
        model = TdmsAttendance
        fields = ('id', 'user_project','employee', 'date','day_remarks','fortnight_deviation_type','fortnight_leave_type','fortnight_day_remarks','is_present','approved_status', 'justification', 'employee_details', 'login_logout_details')

class AttandanceListWithOnlyDeviationByPermissonV2Serializer(serializers.ModelSerializer):
    employee_details = serializers.SerializerMethodField()
    # log_details = serializers.SerializerMethodField()
    login_logout_details = serializers.SerializerMethodField()
    user_project = ProjectDetailsSerializer()

    def get_employee_details(self, TdmsAttendance):
        from users.models import TCoreUserDetail
        from users.serializers import UserModuleSerializer, UserSerializer
        user_details = TCoreUserDetail.objects.filter(cu_user=TdmsAttendance.employee)  # Whatever your query may be
        serializer = UserModuleSerializer(instance=user_details, many=True)
        return serializer.data

    def get_login_logout_details(self, TdmsAttendance):

        login_logout_list = list()
        queryset_att_log = TdmsAttandanceLog.objects.filter(attandance=TdmsAttendance.id,login_logout_check__in=('Logout',))
        # print("TdmsAttendance: ",TdmsAttendance)
        if queryset_att_log:
            for e_queryset_att_log in queryset_att_log:
                login_logout_dict=dict()
                login_logout_dict['login_time'] = TdmsAttandanceLog.objects.filter(
                    attandance=TdmsAttendance.id,id=e_queryset_att_log.login_id).values_list('time',flat=True).first()
                login_logout_dict['logout_time'] = e_queryset_att_log.time
                login_logout_list.append(login_logout_dict)
        
                attendance_deviation = TdmsAttandanceDeviation.objects.filter(
                    attandance_id=TdmsAttendance.id,
                    from_time__gte=login_logout_dict['login_time'],
                    to_time__lte=login_logout_dict['logout_time'],
                    approved_status='1'
                    
                    )
                if attendance_deviation:
                    serializer = AttandanceDeviationSerializer(instance=attendance_deviation, many=True)
                    login_logout_dict['deviation_details']= serializer.data
                else:
                    login_logout_list.remove(login_logout_dict)

        # print("serializer.data: ",serializer.data)
        return login_logout_list


    class Meta:
        model = TdmsAttendance
        fields = ('id', 'user_project','day_remarks','is_present', 'date','approved_status', 'justification', 'employee_details', 'login_logout_details')

class TdmsFlexiTeamFortnightAttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TdmsAttendance
        fields = '__all__'



#::::::::::::::::::::: END NEW ATTENDANCE SYTEM :::::::::::::::#


#:::::::::::: ATTENDENCE ::::::::::::#
class TdmsAttendanceAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    employee = serializers.CharField(default=serializers.CurrentUserDefault())
    type = serializers.IntegerField(required=True)
    user_project_id = serializers.IntegerField(required=True)
    date = serializers.DateField(required=True)
    login_time = serializers.TimeField(required=True)
    login_latitude = serializers.CharField(required=True)
    login_longitude = serializers.CharField(required=True)
    login_address = serializers.CharField(required=True)

    class Meta:
        model = TdmsAttendance
        fields = (
        'id', 'type', 'employee', 'user_project_id', 'date', 'login_time', 'login_latitude', 'login_longitude',
        'login_address', 'created_by', 'owned_by',)

    def create(self, validated_data):
        try:
            attendance_data = TdmsAttendance.objects.create(**validated_data)
            print('attendance_data: ', attendance_data.type)
            return attendance_data
        except Exception as e:
            raise APIException({"msg": e, "request_status": 0})

class AttendanceLogOutSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = TdmsAttendance
        fields = ('id', 'logout_time', 'logout_latitude', 'logout_longitude', 'logout_address', 'updated_by')

    def update(self, instance, validated_data):
        instance.logout_time = validated_data.get("logout_time", instance.logout_time)
        instance.logout_latitude = validated_data.get("logout_latitude", instance.logout_latitude)
        instance.logout_longitude = validated_data.get("logout_longitude", instance.logout_longitude)
        instance.logout_address = validated_data.get("logout_address", instance.logout_address)
        instance.updated_by = validated_data.get("updated_by")
        instance.save()
        print("instance.attandance: ", type(instance.id))
        # log_details = TdmsAttandanceLog.objects.filter()
        self.add_deviations(instance.id, instance.logout_time, instance.updated_by)
        return instance

    def add_deviations(self, att_id, log_out_time, owned_by):
        from datetime import timedelta
        owned_by = owned_by
        att_id = att_id

        log_details = TdmsAttandanceLog.objects.filter(attandance_id=att_id).order_by('id')
        flag = 0
        check_len = 0
        if len(log_details) == 1:
            # print("if len(log_details) == 1")
            for log in log_details:
                # print("log 11",log)
                from_time = log.time
                to_time = log_out_time
                # print("step 1", from_time, to_time)
                self.calculate_deviation(att_id, from_time, to_time, owned_by)
        else:
            # print("else len(log_details) == 1")
            for log in log_details:
                # print("log 22",log)
                check_len += 1
                # print("check_len: ", check_len)
                checkout = log.is_checkout
                # print("checkout :", checkout)
                if checkout == True:
                    # print("if checkout == True:")
                    if flag == 1:
                        # print("if flag == 1:")
                        # if not to_time:
                        if check_len == len(log_details):
                            to_time = log_out_time
                            print("to_time:", to_time)
                            self.calculate_deviation(att_id, from_time, to_time, owned_by)
                    else:
                        # print("else flag == 1:")
                        flag = 1
                        from_time = log.time
                        # print("from_time:", from_time)
                else:
                    # print("else checkout == True:")
                    if flag == 1:
                        flag = 0
                        to_time = log.time
                        # print("to_time", to_time)
                        self.calculate_deviation(att_id, from_time, to_time, owned_by)

    def calculate_deviation(self, att_id, from_time, to_time, owned_by):
        data_dict = {}
        # print("===calculate_deviation===")
        # print("from_time",from_time)
        # print("to_time",to_time)
        dev_time = (to_time - from_time)
        # dev_time = (from_time - to_time)
        # print("dev_time",dev_time)
        time_deviation = (datetime.datetime.min + dev_time).time().strftime('%H:%M:%S')
        data_dict["attandance_id"] = att_id
        data_dict["from_time"] = from_time.strftime('%Y-%m-%dT%H:%M:%S')
        data_dict["to_time"] = to_time.strftime('%Y-%m-%dT%H:%M:%S')
        data_dict["deviation_time"] = time_deviation
        data_dict["owned_by"] = owned_by
        if dev_time.seconds <= 3600 * 5 and dev_time.seconds >= 3600 * 2.5:
            data_dict["deviation_type"] = "HD"
        elif dev_time.seconds > 3600 * 5:
            data_dict["deviation_type"] = "FD"
        else:
            data_dict["deviation_type"] = "OD"

        if data_dict:
            TdmsAttandanceDeviation.objects.get_or_create(**data_dict)

class AttendanceAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    employee = serializers.CharField(default=serializers.CurrentUserDefault())
    date = serializers.DateTimeField(required=True)
    login_time = serializers.DateTimeField(required=True)

    # employee_details=serializers.SerializerMethodField()
    # def get_employee_details(self, TdmsAttendance):
    #     from users.models import TCoreUserDetail
    #     from users.serializers import UserModuleSerializer, UserSerializer
    #     user_details = TCoreUserDetail.objects.filter(cu_user=TdmsAttendance.employee)  # Whatever your query may be
    #     serializer = UserModuleSerializer(instance=user_details, many=True)
    #     return serializer.data
    class Meta:
        model = TdmsAttendance
        fields = ('id', 'type', 'employee', 'user_project', 'date', 'login_time', 'login_latitude', 'login_longitude',
                  'login_address',
                  'logout_time', 'logout_latitude', 'logout_longitude', 'logout_address', 'approved_status',
                  'justification',
                  'created_by', 'owned_by')



class AttendanceListSerializer(serializers.ModelSerializer):
    class Meta:
        model = TdmsAttendance
        fields = ('id', 'type', 'employee', 'user_project', 'date', 'login_time',
                  'logout_time', 'approved_status', 'justification')
class AttendanceSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = TdmsAttendance
        fields = ('id', 'type', 'employee', 'date', 'login_time', 'login_latitude', 'login_longitude', 'login_address',
                  'logout_time', 'logout_latitude', 'logout_longitude', 'logout_address', 'approved_status',
                  'justification', 'updated_by')
class AttendanceApprovalListSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    employee_details = serializers.SerializerMethodField()

    def get_employee_details(self, TdmsAttendance):
        from users.models import TCoreUserDetail
        from users.serializers import UserModuleSerializer, UserSerializer
        user_details = TCoreUserDetail.objects.filter(cu_user=TdmsAttendance.employee)  # Whatever your query may be
        serializer = UserModuleSerializer(instance=user_details, many=True)
        return serializer.data

    class Meta:
        model = TdmsAttendance
        fields = ('id', 'type', 'employee', 'user_project', 'date', 'login_time', 'login_latitude', 'login_longitude',
                  'login_address',
                  'logout_time', 'logout_latitude', 'logout_longitude', 'logout_address', 'approved_status',
                  'justification',
                  'created_by', 'owned_by', 'employee_details')

class AttandanceALLDetailsListSerializer(serializers.ModelSerializer):
    employee_details = serializers.SerializerMethodField()
    # log_details = serializers.SerializerMethodField()
    deviation_details = serializers.SerializerMethodField()
    user_project = ProjectDetailsSerializer()

    def get_employee_details(self, TdmsAttendance):
        from users.models import TCoreUserDetail
        from users.serializers import UserModuleSerializer, UserSerializer
        user_details = TCoreUserDetail.objects.filter(cu_user=TdmsAttendance.employee)  # Whatever your query may be
        serializer = UserModuleSerializer(instance=user_details, many=True)
        return serializer.data

    def get_deviation_details(self, TdmsAttendance):
        # print("TdmsAttendance: ",TdmsAttendance)
        attendance_deviation = TdmsAttandanceDeviation.objects.filter(attandance_id=TdmsAttendance.id)
        serializer = AttandanceDeviationSerializer(instance=attendance_deviation, many=True)
        # print("serializer.data: ",serializer.data)
        return serializer.data

    class Meta:
        model = TdmsAttendance
        fields = ('id', 'user_project', 'date', 'login_time',
                  'logout_time', 'approved_status', 'justification', 'employee_details', 'deviation_details')


class AttandanceALLDetailsListByPermissonSerializer(serializers.ModelSerializer):
    employee_details = serializers.SerializerMethodField()
    # log_details = serializers.SerializerMethodField()
    deviation_details = serializers.SerializerMethodField()
    user_project = ProjectDetailsSerializer()

    # def get_log_details(self, TdmsAttendance):
    #     # print("TdmsAttendance: ",TdmsAttendance)
    #     attendance_log = TdmsAttandanceLog.objects.filter(attandance_id=TdmsAttendance.id)
    #     serializer = AttandanceLogSerializer(instance=attendance_log, many=True)
    #     # print("serializer.data: ",serializer.data)
    #     return serializer.data
    def get_employee_details(self, TdmsAttendance):
        from users.models import TCoreUserDetail
        from users.serializers import UserModuleSerializer, UserSerializer
        user_details = TCoreUserDetail.objects.filter(cu_user=TdmsAttendance.employee)  # Whatever your query may be
        serializer = UserModuleSerializer(instance=user_details, many=True)
        return serializer.data

    def get_deviation_details(self, TdmsAttendance):
        # print("TdmsAttendance: ",TdmsAttendance)
        attendance_deviation = TdmsAttandanceDeviation.objects.filter(attandance_id=TdmsAttendance.id)
        serializer = AttandanceDeviationSerializer(instance=attendance_deviation, many=True)
        # print("serializer.data: ",serializer.data)
        return serializer.data

    class Meta:
        model = TdmsAttendance
        fields = ('id', 'user_project', 'date', 'login_time',
                  'logout_time', 'approved_status', 'justification', 'employee_details', 'deviation_details')

class AttandanceListWithOnlyDeviationByPermissonSerializer(serializers.ModelSerializer):
    employee_details = serializers.SerializerMethodField()
    # log_details = serializers.SerializerMethodField()
    deviation_details = serializers.SerializerMethodField()
    user_project = ProjectDetailsSerializer()

    # def get_log_details(self, TdmsAttendance):
    #     # print("TdmsAttendance: ",TdmsAttendance)
    #     attendance_log = TdmsAttandanceLog.objects.filter(attandance_id=TdmsAttendance.id)
    #     serializer = AttandanceLogSerializer(instance=attendance_log, many=True)
    #     # print("serializer.data: ",serializer.data)
    #     return serializer.data
    def get_employee_details(self, TdmsAttendance):
        from users.models import TCoreUserDetail
        from users.serializers import UserModuleSerializer, UserSerializer
        user_details = TCoreUserDetail.objects.filter(cu_user=TdmsAttendance.employee)  # Whatever your query may be
        serializer = UserModuleSerializer(instance=user_details, many=True)
        return serializer.data

    def get_deviation_details(self, TdmsAttendance):
        # print("TdmsAttendance: ",TdmsAttendance)
        attendance_deviation = TdmsAttandanceDeviation.objects.filter(approved_status=4,attandance_id=TdmsAttendance.id)
        serializer = AttandanceDeviationSerializer(instance=attendance_deviation, many=True)
        # print("serializer.data: ",serializer.data)
        return serializer.data

    class Meta:
        model = TdmsAttendance
        fields = ('id', 'user_project', 'date', 'login_time',
                  'logout_time', 'approved_status', 'justification', 'employee_details', 'deviation_details')



#:::::::::::: TdmsAttandanceLog ::::::::::::#
class AttandanceLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = TdmsAttandanceLog
        fields = (
        'id', 'attandance', 'time', 'latitude', 'longitude', 'address', 'approved_status', 'justification', 'remarks',
        'is_checkout')
class AttandanceLogAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    # logdetails = serializers.ListField(required=False)
    # attendence_log_list= serializers.ListField(required=False)

    class Meta:
        model = TdmsAttandanceLog
        fields = ('id', 'attandance', 'time', 'latitude', 'longitude', 'address', 'approved_status', 'justification',
                  'is_checkout', 'created_by', 'owned_by')

    def geofencing(self, cur_location, s_location, geo_fencing_area):
        try:

            if geo_fencing_area.endswith("km"):
                geo_fencing_area = re.findall('^\d+', geo_fencing_area)
                geo_fencing_area = int(geo_fencing_area[0]) * 1000

            else:
                geo_fencing_area = re.findall('^\d+', geo_fencing_area)
                geo_fencing_area = int(geo_fencing_area[0])

            distance = great_circle(cur_location, s_location).meters
            print("distance", distance)
            if distance > geo_fencing_area:
                return True
            else:
                return False
        except Exception as e:
            raise e

    def create(self, validated_data):
        try:
            # is_checkout=True
            attandance_id = validated_data.get('attandance')
            current_user = validated_data.get('created_by')
            latitude = validated_data.get('latitude')
            longitude = validated_data.get('longitude')
            cur_location = (latitude, longitude,)
            assign_project = TdmsAttendance.objects.only('user_project_id').get(pk=attandance_id.id).user_project_id
            print("current_user: ", current_user)
            print("user_project_id: ", assign_project)
            # log_count = TdmsAttandanceLog.objects.filter(attandance_id=attandance_id).count()
            if not assign_project:
                # print('log_count: ', log_count)
                if latitude and longitude:
                    import math
                    lat = float(latitude)
                    lon = float(longitude)
                    print(lat, lon)
                    R = 6378.1  # earth radius
                    # R = 6371  # earth radius
                    distance = 10  # distance in km
                    lat1 = lat - math.degrees(distance / R)
                    lat2 = lat + math.degrees(distance / R)
                    long1 = lon - math.degrees(distance / R / math.cos(math.degrees(lat)))
                    long2 = lon + math.degrees(distance / R / math.cos(math.degrees(lat)))

                    # site_details = TdmsSiteProjectSiteManagement.objects.filter(Q(latitude__gte=lat1, latitude__lte=lat2) | Q(longitude__gte=long1, longitude__lte=long2))
                    site_details = TdmsSiteProjectSiteManagement.objects.filter(latitude__gte=lat1,
                                                                               latitude__lte=lat2).filter(
                        longitude__gte=long1, longitude__lte=long2)
                    site_id_list = [i.id for i in site_details]
                    print("site_id_list: ", site_id_list)
                    # project_on_sites = TdmsProject.objects.filter(site_location_)
                    project_user_mapping = TdmsProjectUserMapping.objects.filter(user=current_user, status=True,
                                                                                project__site_location_id__in=site_id_list)[
                                           :1]
                    # print(project_user_mapping.query)
                    for project in project_user_mapping:
                        print('project_user_mapping: ', project.project_id)
                        site_lat = project.project.site_location.latitude
                        site_long = project.project.site_location.longitude
                        geo_fencing_area = project.project.site_location.geo_fencing_area
                        s_location = (site_lat, site_long,)

                        TdmsAttendance.objects.filter(pk=attandance_id.id).update(user_project_id=project.project_id)
            else:
                attandance_details = TdmsAttendance.objects.filter(pk=attandance_id.id)
                for project in attandance_details:
                    print('attandance_project_id: ', project.user_project_id)
                    site_lat = project.user_project.site_location.site_latitude
                    site_long = project.user_project.site_location.site_longitude
                    geo_fencing_area = project.user_project.site_location.geo_fencing_area

                    s_location = (site_lat, site_long,)

            try:

                print('s_location',s_location)
                is_checkout = self.geofencing(cur_location, s_location, geo_fencing_area)
            except Exception as e:
                print(e)
                is_checkout = True

            # print("is_checkout: ", is_checkout)
            attandance_log, created = TdmsAttandanceLog.objects.get_or_create(**validated_data, is_checkout=is_checkout)
            print("created: ", created)
            return attandance_log

        except Exception as e:
            raise e

class AttandanceLogMultipleAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    logdetails = serializers.ListField(required=False)
    attendence_log_list= serializers.ListField(required=False)

    class Meta:
        model = TdmsAttandanceLog
        fields = ('__all__')
        extra_fields = ('logdetails')
    def create(self, validated_data):
        try:
            logdetails = validated_data.pop('logdetails') if 'logdetails' in validated_data else ""
            print(validated_data)
            owned_by = validated_data.get('owned_by')
            created_by = validated_data.get('created_by')
            '''
                Modified by Rupam Hazra [ remove with transaction.atomic()]
            '''
            
            #with transaction.atomic():
                # pedp_data, created1 = TdmsExecutionDailyProgress.objects.get_or_create(**validated_data)
            attendence_log_list = []
            print("log_data",logdetails)
            for data in logdetails:
                if data['is_checkout']=='':
                    data['is_checkout']= False
                # print("log_data",data)
                # print("date_of_completion::::::::",pro_data['date_of_completion'],type(pro_data['date_of_completion']))
                log_data, created1 = TdmsAttandanceLog.objects.get_or_create(
                    created_by=created_by,
                    owned_by=owned_by,
                    **data
                    )
                log_data.__dict__.pop('_state') if "_state" in log_data.__dict__.keys() else log_data.__dict__
                attendence_log_list.append(log_data.__dict__)
                validated_data['logdetails']=attendence_log_list
                # print("progress_list:::::", type(progress_list[0]['planned_start_date']))
                # pedp_data.__dict__["progress_data"] = progress_list

            return validated_data



        except Exception as e:
            raise e
    


class AttandanceLogEditSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = TdmsAttandanceLog
        fields = ('id', 'justification', 'updated_by')

    def update(self, instance, validated_data):
        instance.justification = validated_data.get("justification", instance.justification)
        instance.updated_by = validated_data.get("updated_by")
        instance.save()
        return instance
class AttandanceLogApprovalEditSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = TdmsAttandanceLog
        fields = ('id', 'approved_status', 'remarks', 'updated_by')

    def put(self, instance, validated_data):
        instance.justification = validated_data.get("approved_status", instance.justification)
        instance.remarks = validated_data.get("remarks", instance.remarks)
        instance.updated_by = validated_data.get("updated_by")
        instance.save()
        return instance


# ---------------------------------- Tdms Attandance Deviation------------------------------------
class AttandanceDeviationSerializer(serializers.ModelSerializer):
    approved_status_name = serializers.SerializerMethodField(required=False)
    def get_approved_status_name(self, TdmsAttandanceDeviation):
        return TdmsAttandanceDeviation.get_approved_status_display()
        
    class Meta:
        model = TdmsAttandanceDeviation
        fields = "__all__"
        extra_fields = ('approved_status_name',)
class AttandanceDeviationJustificationEditSerializer(serializers.ModelSerializer):
    justified_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = TdmsAttandanceDeviation
        fields = ('id', 'deviation_type', 'justification', 'justified_by')

    def update(self, instance, validated_data):
        instance.deviation_type = validated_data.get("deviation_type", instance.deviation_type)
        instance.justification = validated_data.get("justification", instance.justification)
        instance.justified_by = validated_data.get("justified_by")
        instance.save()
        return instance
class AttandanceDeviationApprovaEditSerializer(serializers.ModelSerializer):
    approved_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = TdmsAttandanceDeviation
        fields = ('id', 'approved_status', 'remarks', 'approved_by')

    def update(self, instance, validated_data):
        instance.approved_status = validated_data.get("approved_status", instance.approved_status)
        instance.remarks = validated_data.get("remarks", instance.remarks)
        instance.approved_by = validated_data.get("approved_by")
        instance.save()
        return instance

class AttandanceMassDeviationApprovaEditSerializer(serializers.ModelSerializer):
    approved_by = serializers.CharField(default=serializers.CurrentUserDefault())
    deviation_id=serializers.ListField(required=False)
    class Meta:
        model = TdmsAttandanceDeviation
        fields = ('id', 'approved_status', 'remarks', 'approved_by','deviation_id')
    def create(self,validated_data):
        try:
            approved_by = validated_data.get('approved_by')
            approved_status = validated_data.get("approved_status")
            remarks = validated_data.get("remarks")
            for data in validated_data.get('deviation_id'):
                all_closed_task = TdmsAttandanceDeviation.objects.filter(id=data['id']).update(approved_status=approved_status,
                                                                                            remarks=remarks,
                                                                                            approved_by=approved_by)
                
            return validated_data
        except Exception as e:
            raise e
#:::::::::::: TdmsAttandanceLeaves ::::::::::::#
# class AdvanceLeavesAddSerializer(serializers.ModelSerializer):
#     employee = serializers.CharField(default=serializers.CurrentUserDefault())
#     created_by = serializers.CharField(default=serializers.CurrentUserDefault())
#     owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
#
#     class Meta:
#         model = TdmsEmployeeLeave
#         fields = (
#         'id', 'employee', 'leave_type', 'approved_status', 'start_date', 'end_date', 'reason', 'created_by', 'owned_by')
class AdvanceLeavesAddSerializer(serializers.ModelSerializer):
    employee = serializers.CharField(default=serializers.CurrentUserDefault())
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    leave_type = serializers.CharField(required=False)
    start_date = serializers.DateTimeField(required=True)
    end_date = serializers.DateTimeField(required=True)
    reason = serializers.CharField(required=False)
    employee_first_name = serializers.CharField(required=False)
    employee_last_name = serializers.CharField(required=False)
    class Meta:
        model = TdmsEmployeeLeave
        fields = (
        'id', 'employee', 'leave_type', 'approved_status', 'start_date', 'end_date', 'reason', 'created_by', 'owned_by',
        'employee_first_name', 'employee_last_name')
    def create(self, validated_data):
        data_dict = {}
        leave_data, created11 = TdmsEmployeeLeave.objects.get_or_create(**validated_data)
        employee_first_name = User.objects.only('first_name').get(id=leave_data.__dict__['employee_id']).first_name
        employee_last_name = User.objects.only('last_name').get(id=leave_data.__dict__['employee_id']).last_name
        leave_data.__dict__.pop('_state') if "_state" in leave_data.__dict__.keys() else leave_data.__dict__

        data_dict = leave_data.__dict__
        data_dict['employee_first_name']=employee_first_name
        data_dict['employee_last_name']=employee_last_name
        # print("data_dict",data_dict)
        return data_dict

class AdvanceLeaveEditSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = TdmsEmployeeLeave
        fields = ('id', 'approved_status', 'updated_by')
class AdvanceLeaveMassEditSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    leave_id=serializers.ListField(required=False)
    remarks = serializers.CharField(required=False,allow_blank=True)
    class Meta:
        model = TdmsEmployeeLeave
        fields = ('id', 'approved_status', 'updated_by','leave_id','remarks')
    def create(self,validated_data):
        try:
            updated_by = validated_data.get('updated_by')
            approved_status = validated_data.get("approved_status")
            remarks = validated_data.get("remarks")
            # print("approved_status", approved_status , type(approved_status), remarks)
            if approved_status==4:
                for data in validated_data.get('leave_id'):
                    all_closed_task = TdmsEmployeeLeave.objects.filter(id=data['id']).update(approved_status=approved_status,
                                                                                            reason=remarks,updated_by=updated_by)
            else:
                for data in validated_data.get('leave_id'):
                    all_closed_task = TdmsEmployeeLeave.objects.filter(id=data['id']).update(approved_status=approved_status,
                                                                                            updated_by=updated_by)
                print("all_closed_task",all_closed_task)
            return validated_data
        except Exception as e:
            raise e


class LeaveListByEmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TdmsEmployeeLeave
        fields = ('id', 'employee', 'leave_type', 'start_date', 'end_date', 'reason',
                  'approved_status')
class AttandanceDeviationByAttandanceListSerializer(serializers.ModelSerializer):
    class Meta:
        model = TdmsAttandanceDeviation
        fields ='__all__'

#:::::::::::::::::::::: PMS EMPLOYEE CONVEYANCE:::::::::::::::::::::::::::#
class EmployeeConveyanceAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    employee = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = TdmsEmployeeConveyance
        fields = ('id', 'project', 'employee', 'eligibility_per_day', 'date', 'from_place', 'to_place', 'vechicle_type',
                  'purpose', 'job_alloted_by', 'approved_status', 'ammount', 'created_by', 'owned_by')

class EmployeeConveyanceEditSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = TdmsEmployeeConveyance
        fields = ('id', 'approved_status', 'updated_by')


class EmployeeConveyanceListSerializer(serializers.ModelSerializer):
    employee_details = serializers.SerializerMethodField(required=False)
    job_alloted_by_name = serializers.SerializerMethodField(required=False)
    user_project = serializers.SerializerMethodField(required=False)

    def get_employee_details(self, TdmsEmployeeConveyance):
        from users.models import TCoreUserDetail
        from users.serializers import UserModuleSerializer, UserSerializer
        user_details = TCoreUserDetail.objects.filter(cu_user=TdmsEmployeeConveyance.employee)  # Whatever your query may be
        serializer = UserModuleSerializer(instance=user_details, many=True)
        return serializer.data

    class Meta:
        model = TdmsEmployeeConveyance
        fields = ('id', 'project', 'employee', 'eligibility_per_day', 'date', 'from_place', 'to_place', 'vechicle_type',
                  'purpose', 'job_alloted_by', 'approved_status', 'ammount', 'created_by', 'owned_by', 'employee_details',
                  'job_alloted_by_name', 'user_project')

    def get_job_alloted_by_name(self, TdmsEmployeeConveyance):
        from users.models import TCoreUserDetail
        from users.serializers import UserModuleSerializer, UserSerializer
        user_details = TCoreUserDetail.objects.filter(cu_user=TdmsEmployeeConveyance.job_alloted_by)  # Whatever your query may be.
        serializer = UserModuleSerializer(instance=user_details, many=True)
        name = serializer.data[0]['cu_user']['first_name']+" "+serializer.data[0]['cu_user']['last_name']
        # return serializer.data
        return name

    def get_user_project(self, TdmsEmployeeConveyance):
        project = TdmsProject.objects.filter(is_deleted=False,id=TdmsEmployeeConveyance.project.id).values('name')
        if project:
            return project[0]['name']
        else:
            None


#:::::::::::::::::::::::::::::::::::PMS EMPLOYEE FOODING:::::::::::::::::::::::::::::::#
class EmployeeFoodingAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = TdmsEmployeeFooding
        fields = ('id', 'attandance', 'approved_status', 'ammount', 'created_by', 'owned_by', 'updated_by')

    def create(self, validated_data):
        fooding_data = TdmsEmployeeFooding.objects.filter(is_deleted=False,attandance=validated_data['attandance']).update(
            approved_status=validated_data['approved_status'],ammount=Decimal(100.00) if validated_data['approved_status']==2 else Decimal(0.0),
            updated_by=validated_data['created_by']
        )
        if fooding_data:
            return validated_data
        else:
            fooding_data = TdmsEmployeeFooding.objects.create(ammount=Decimal(100.00) 
            if validated_data['approved_status']==2 else Decimal(0.0),**validated_data)
            fooding_data.__dict__.pop('_state') if "_state" in fooding_data.__dict__.keys() else fooding_data.__dict__
            return validated_data

class AttandanceAllDetailsListWithFoodingSerializer(serializers.ModelSerializer):
    employee_details = serializers.SerializerMethodField()
    user_project = ProjectDetailsSerializer()
    fooding_details = serializers.SerializerMethodField()

    def get_employee_details(self, TdmsAttendance):
        from users.models import TCoreUserDetail
        from users.serializers import UserModuleSerializer, UserSerializer
        user_details = TCoreUserDetail.objects.filter(cu_user=TdmsAttendance.employee)  # Whatever your query may be
        serializer = UserModuleSerializer(instance=user_details, many=True)
        return serializer.data

    def get_fooding_details(self, TdmsAttendance):
        fooding = TdmsEmployeeFooding.objects.filter(is_deleted=False,attandance_id=TdmsAttendance.id)
        if fooding:
            fooding[0].__dict__.pop('_state') if "_state" in fooding[0].__dict__.keys() else fooding[0].__dict__
            return fooding[0].__dict__
        else:
            return {}

    class Meta:
        model = TdmsAttendance
        fields = ('id', 'user_project', 'date', 'login_time',
                  'logout_time', 'approved_status', 'justification', 'employee_details', 'fooding_details')

'''
    @@ Added By Rupam Hazra on [10-01-2020] line number 864-868 @@
    
'''
class AttendanceUpdateLogOutTimeFailedOnLogoutSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = TdmsAttendance
        fields = ('id', 'logout_time', 'updated_by')

'''
    @@ Added By Rupam Hazra on [10-01-2020] line number 876-926 @@
    
'''
class AttandanceLogMultipleByThreadAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    logdetails = serializers.ListField(required=False)
    attendence_log_list= serializers.ListField(required=False)

    class Meta:
        model = TdmsAttandanceLog
        fields = ('__all__')
        extra_fields = ('logdetails')
    def create(self, validated_data):
        try:
            logdetails = validated_data.pop('logdetails') if 'logdetails' in validated_data else ""
            print(validated_data)
            owned_by = validated_data.get('owned_by')
            created_by = validated_data.get('created_by')
            '''
                Modified by Rupam Hazra [ remove with transaction.atomic()]
            '''
            attendence_log_list = []
            #print("log_data_count",len(logdetails))
            #time.sleep(2)
            ServiceThread(logdetails, owned_by, created_by).start()
            return validated_data

        except Exception as e:
            raise e
    
class ServiceThread(threading.Thread):
    def __init__(self, request_data, owned_by, created_by):
        self.request_data = request_data
        self.owned_by = owned_by
        self.created_by = created_by
        threading.Thread.__init__(self)

    def run (self):
        for data in self.request_data:
            #time.sleep(1)
            if data['is_checkout']=='':
                data['is_checkout']= False
            
            log_data, created1 = TdmsAttandanceLog.objects.get_or_create(
            created_by=self.created_by,
            owned_by=self.owned_by,
            **data
            )
            # created1 = TdmsAttandanceLog.objects.create(
            # created_by=self.created_by,
            # owned_by=self.owned_by,
            # **data
            # )
            print('created1....')

class TdmsLiveTrackingForAllEmployeesSerializer(serializers.ModelSerializer):

    class Meta:
        model = TdmsProjectUserMapping
        fields = ('id','project','user','user_details')

       