from django.shortcuts import render
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated , AllowAny
#from rest_framework.authentication import TokenAuthentication
#from rest_framework.authtoken.models import Token
from pms.models import *
from pms.serializers import *
import time
from multiplelookupfields import MultipleFieldLookupMixin
from rest_framework.views import APIView
from django.conf import settings
from pagination import CSLimitOffestpagination,CSPageNumberPagination
from rest_framework import filters
import calendar
from holidays.models import *
import collections
from rest_framework.exceptions import APIException
import pandas as pd
import numpy as np
from django_filters.rest_framework import DjangoFilterBackend
from master.serializers import UserModuleWiseListSerializer
from master.models import TMasterModuleRole
from users.models import TCoreUserDetail , TMasterModuleRole , TCoreRole, TMasterModuleRoleUser , UserAttendanceTypeTransferHistory
from custom_decorator import *
from rest_framework.parsers import FileUploadParser
import os
from pms.custom_filter import *
from django.db.models import Q
from global_function import *
from attendance.models import AttendenceMonthMaster
from attendance.models import EmployeeAdvanceLeaves,EmployeeSpecialLeaves
from employee_leave_calculation import get_leave_type_from_type,get_flexi_hours_for_work_days,get_fortnight_leave_deduction,calculate_day_remarks,get_documents
from users.models import TCoreUserDetail
from pandas import DataFrame
from datetime import datetime,timedelta,date
from django.db import transaction, IntegrityError

'''
    For Knox 
    Author : Rupam Hazra
    Date : 16.03.2020
'''
from knox.auth import TokenAuthentication
from rest_framework import permissions
from knox.models import AuthToken



'''
    Reason : NEW FLEXI ATTENDANCE SYTEM
    Author : Rupam Hazra
    Start Date: 14-05-2020
'''
#::::::::::::::::::::: NEW ATTENDANCE SYSTEM :::::::::::::::#

class PmsAttendanceAdvanceLeaveAddV2View(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = EmployeeAdvanceLeaves.objects.filter(is_deleted=False)
    serializer_class = PmsAttendanceAdvanceLeaveAddV2Serializer

    @response_modify_decorator_post
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class PmsAttandanceAdminOdMsiReportView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    serializer_class = PmsAttandanceAdminOdMsiReportSerializer

    @response_modify_decorator_list_after_execution
    def get(self, request, *args, **kwargs):
        total_list = []
        year =self.request.query_params.get('year', None)
        month =self.request.query_params.get('month', None)

        month_range = AttendenceMonthMaster.objects.filter(month=month,month_end__year=year).values('month_start__date','month_end__date')
        if month_range:
            month_start = month_range[0]['month_start__date']
            month_end = month_range[0]['month_end__date']
            
            module_user_list = list(TCoreUserDetail.objects.filter(
                attendance_type='PMS',cu_user__is_active=True,cu_is_deleted=False).values_list('cu_user',flat=True))

            print('module_user_list',module_user_list)
            od_emp_list = set(PmsAttandanceDeviation.objects.filter(
                Q(is_requested=True)&
                Q(from_time__date__gte=month_start)&
                Q(from_time__date__lte=month_end)&
                Q(deviation_type='OD')&
                (Q(approved_status='1')|
                Q(approved_status='2')|
                Q(approved_status='3')),
                attandance__employee__in=module_user_list).values_list('attandance__employee', flat=True))

            print("get_od_emp_details",od_emp_list)
            od_details = PmsAttandanceDeviation.objects.filter(Q(is_requested=True)&
                                                                    Q(from_time__date__gte=month_start)&
                                                                    Q(from_time__date__lte=month_end)&
                                                                    Q(deviation_type='OD')&
                                                                    (Q(approved_status='1')|Q(approved_status='2')|
                                                                    Q(approved_status='3')),attandance__employee__in=od_emp_list)

            if od_emp_list:
                for emp in od_emp_list:
                    data_list = []
                    print("emp",emp)
                    od_duration = od_details.filter(attandance__employee=emp).aggregate(Sum('duration'))['duration__sum']
                    approved_od = od_details.filter(attandance__employee=emp,approved_status='2').count()
                    pending_od = od_details.filter(attandance__employee=emp,approved_status='1').count()
                    reject_od = od_details.filter(attandance__employee=emp,approved_status='3').count()
                    total_od = approved_od + pending_od + reject_od

                    print("khlkhkjg", total_od , approved_od , pending_od , reject_od)

                    # user_details = TCoreUserDetail.objects.filter(cu_user=emp,cu_is_deleted=False).values('cu_user__first_name',
                    #                                                 'cu_user__last_name', 'cu_punch_id', 'hod__first_name','hod__last_name')#reporting_head
                    user_details = TCoreUserDetail.objects.filter(cu_user=emp,cu_is_deleted=False).annotate(
                                                                        user_first_name=Case(
                                                                        When(cu_user__first_name__isnull=True, then=Value("")),
                                                                        When(cu_user__first_name__isnull=False, then=F('cu_user__first_name')),
                                                                        output_field=CharField()
                                                                        ),user_last_name=Case(
                                                                        When(cu_user__last_name__isnull=True, then=Value("")),
                                                                        When(cu_user__last_name__isnull=False, then=F('cu_user__last_name')),
                                                                        output_field=CharField()
                                                                        ),reporting_head_first_name=Case(
                                                                        When(reporting_head__first_name__isnull=True, then=Value("")),
                                                                        When(reporting_head__first_name__isnull=False, then=F('reporting_head__first_name')),
                                                                        output_field=CharField()
                                                                        ),reporting_head_last_name=Case(
                                                                        When(reporting_head__last_name__isnull=True, then=Value("")),
                                                                        When(reporting_head__last_name__isnull=False, then=F('reporting_head__last_name')),
                                                                        output_field=CharField()
                                                                        ),hod_first_name=Case(
                                                                        When(hod__first_name__isnull=True, then=Value("")),
                                                                        When(hod__first_name__isnull=False, then=F('hod__first_name')),
                                                                        output_field=CharField()
                                                                        ),hod_last_name=Case(
                                                                        When(hod__last_name__isnull=True, then=Value("")),
                                                                        When(hod__last_name__isnull=False, then=F('hod__last_name')),
                                                                        output_field=CharField()
                                                                        ),cu_emp_code_n=Case(
                                                                        When(cu_emp_code__isnull=True, then=Value("")),
                                                                        When(cu_emp_code__isnull=False, then=F('cu_emp_code')),
                                                                        output_field=CharField()),).values(
                                                                        'user_first_name','user_last_name','reporting_head_first_name','reporting_head_last_name',
                                                                        'hod_first_name','hod_last_name','cu_emp_code_n').order_by('-hod_first_name')
                    print("user_details",  user_details[0])
                    employee_name = user_details[0]['user_first_name']+" "+user_details[0]['user_last_name']
                    reporting_head = user_details[0]['reporting_head_first_name']+" "+user_details[0]['reporting_head_last_name']
                    hod_name = user_details[0]['hod_first_name']+" "+user_details[0]['hod_last_name']
                    # data_dict['employee_name'] = user_details.__dict__['cu_user__first_name']
                    employee_code = user_details[0]['cu_emp_code_n']
                    data_list = [employee_name, reporting_head, hod_name, employee_code, total_od, od_duration, approved_od, pending_od, reject_od]

                    total_list.append(data_list)

        # updated by Shubhadeep - follow this code for any file donwload
        relative_dir_path = 'media/pms/attendance/od_mis_report/document'
        dir_path = os.path.join(settings.MEDIA_ROOT_EXPORT, relative_dir_path)
        if not os.path.isdir(dir_path):
            os.makedirs(dir_path)
        file_name = os.path.join(dir_path, 'od_mis_report.xlsx')
        relative_file_name = os.path.join(relative_dir_path, 'od_mis_report.xlsx')
        
        #########################################################
        df = DataFrame(total_list, columns= ['Employee Name', 'Reporting Head', 'HOD Name', 'Employee_code', 'Total Od', 'Total Min', 'Approved', 'Pending', 'Rejected'])
        df.sort_values(['Reporting Head'], inplace=True,ascending=True)
        export_csv = df.to_excel (file_name, index = None, header=True)

        #########################################################
        #url_path = request.build_absolute_uri(file_name) if file_name else None
        #print("url_path",url_path)
        
        '''
            Editied By Rupam Hazra on 2019-12-17
        '''
        #print('host',request.get_host())

        if request.is_secure():
            protocol = 'https://'
        else:
            protocol = 'http://'

        url = getHostWithPort(request) + relative_file_name if relative_file_name else None
        #print('url',url)
        #url = re.search('https://(\d+\.)+\d+\:\d{4}\/',str(url_path)).group()
        #print("url",url)
        #url_path = url+file_name
        # url_path = "http://13.232.240.233:8000/"+file_name
        return Response(url)

class PmsAttandanceAdminSAPReportView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    # serializer_class = AttandanceAdminOdMsiReportSerializer

    @response_modify_decorator_list_after_execution
    def get(self, request, *args, **kwargs):
        '''
            If "is_sap = 1" then API returns excel with SAP id otherwise return with Epm_name,code,punch id.
        '''
        total_list = []
        cur_date =self.request.query_params.get('cur_date', None)
        dept_filter =self.request.query_params.get('dept_filter', None)
        is_sap =self.request.query_params.get('is_sap', None)
        year = self.request.query_params.get('year', None)
        month = self.request.query_params.get('month', None)
        emp_list = []
        total_user_list = []
        module_user_list = []
        req_filter = {}
        date_range = []
        header = []
        '''
            This API is use to generate SAP report as .csv file on "Full/Half Day" leave Basic.Conditions are below:-
            'date'-> It is current date value, from front end. Used to get previous month's date range.
            'module_user_list'-> Get 'ATTENDANCE & HRMS' module users as list formet.
        '''
        if cur_date:
            date = datetime.strptime(cur_date, "%Y-%m-%d")
            date_range_first = AttendenceMonthMaster.objects.filter(month_start__date__lte=date,month_end__date__gte=date).values('month_start__date','month_end__date')
            date = date_range_first[0]['month_start__date'] - timedelta(days=1)
            date_range = AttendenceMonthMaster.objects.filter(month_start__date__lte=date,month_end__date__gte=date).values('month_start__date','month_end__date')

        elif year and month:
            #date_range = AttendenceMonthMaster.objects.filter(month=month,month_end__year=year).values('month_start__date','month_end__date')
            date_range = AttendenceMonthMaster.objects.filter(month=month,month_end__year=year).values('month_start__date','month_end__date')
            #print('date_range',date_range)
            #time.sleep(15)


        if date_range:
            #print("date_range",date_range)
            req_filter['from_time__date__gte']=date_range[0]['month_start__date']
            req_filter['from_time__date__lte']=date_range[0]['month_end__date']
            req_filter['is_requested'] = True

           
            
            module_user_list = list(TCoreUserDetail.objects.filter(
                    attendance_type='PMS',user_type__in=('User',)).values_list('cu_user',flat=True).exclude(sap_personnel_no__in=['37200030','37200146','37200081','37200071']))

            if dept_filter:
                dept_list = dept_filter.split(',')
                emp_list = list(TCoreUserDetail.objects.filter(department__in=dept_list).values_list('cu_user',flat=True))
                print("emp_list",emp_list)
                # req_filter['attendance__employee__in']=emp_list
                total_user_list = [val for val in module_user_list if val in emp_list]
                req_filter['attandance__employee__in']=total_user_list
            else:
                req_filter['attandance__employee__in']=module_user_list
            #print(req_filter['attendance__employee__in'])
            #time.sleep(15)
            

        if req_filter:
            #print('sdfdddddddddddddddddddddddddddddddddddd',req_filter)
            #time.sleep(15)
            request_details = PmsAttandanceDeviation.objects.filter(
                ((Q(leave_type_changed_period__isnull=False)&
                (Q(leave_type_changed_period='FD')|Q(leave_type_changed_period='HD')))|
                (Q(leave_type_changed_period__isnull=True)&(Q(deviation_type='FD')|Q(deviation_type='HD')))),
                **req_filter)

            print("request_details",request_details)
            #time.sleep(15)
            lv_emp_list = set(request_details.filter().values_list('attandance__employee',flat=True))
            if lv_emp_list:
                print("lv_emp_list",lv_emp_list)
                for employee_id in lv_emp_list:
                    sap_no = None
                    employee_obj = TCoreUserDetail.objects.get(cu_user=employee_id)
                    sap_no = employee_obj.sap_personnel_no
                    company_code = employee_obj.company
                    name = User.objects.get(pk=employee_id).get_full_name()
                    dept = employee_obj.department.cd_name if employee_obj.department else ''
                    is_exit = 'Yes' if  employee_obj.termination_date else ''
                    termination_date = employee_obj.termination_date
                    # user_details = TCoreUserDetail.objects.filter(cu_user=employee_id).values('cu_user__first_name','cu_user__last_name','sap_personnel_no',
                    #                                                                             'cu_emp_code','cu_punch_id')
                    print("sap_no",sap_no)
                    if sap_no and sap_no!='#N/A':
            
                        date_list = set(request_details.filter(attandance__employee=employee_id).values_list('from_time__date',flat=True))
                        
                        availed_master_wo_reject_fd = request_details.\
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
                        print("availed_master_wo_reject_fd",availed_master_wo_reject_fd)

                        if availed_master_wo_reject_fd:
                            for data in date_list:
                                data_str = data.strftime("%d.%m.%Y")
                                # print("data_str",data_str, type(data_str))
                                subtype = None
                                data_list = []
                                availed_FD=availed_master_wo_reject_fd.filter(attandance__date__date=data)
                                
                                #print("availed_HD",availed_FD)
                                if availed_FD.filter(leave_type_final__isnull=False):
                                    if availed_FD.values('leave_type_final').count() >1:
                                        if availed_FD.filter(leave_type_final='AL'):
                                            # availed_ab=availed_ab+1.0
                                            subtype = TCoreLeaveCodeForSapReport.objects.only('code').get(name='All Leave').code
                                        
                                        elif availed_FD.filter(leave_type_final='AB'):
                                            # availed_ab=availed_ab+1.0
                                            subtype = TCoreLeaveCodeForSapReport.objects.only('code').get(name='Absent').code

                                        elif availed_FD.filter(leave_type_final='CL'):
                                            # availed_cl=availed_cl+1.0
                                            subtype = TCoreLeaveCodeForSapReport.objects.only('code').get(name='Casual Leave').code

                                        elif availed_FD.filter(leave_type_final='EL'):
                                            # availed_cl=availed_cl+1.0
                                            subtype = TCoreLeaveCodeForSapReport.objects.only('code').get(name='Earn Leave').code
                                        
                                        elif availed_FD.filter(leave_type_final='SL'):
                                            # availed_cl=availed_cl+1.0
                                            subtype = TCoreLeaveCodeForSapReport.objects.only('code').get(name='Sick Leave').code
                                                    

                                    else:
                                        l_type=availed_FD[0]['leave_type_final']
                                        if l_type == 'AB':
                                            # availed_ab=availed_ab+1.0
                                            subtype = TCoreLeaveCodeForSapReport.objects.only('code').get(name='Absent').code
                                            
                                        elif l_type == 'AL':
                                            # availed_ab=availed_ab+1.0
                                            subtype = TCoreLeaveCodeForSapReport.objects.only('code').get(name='All Leave').code

                                        elif l_type == 'CL':
                                            # availed_cl=availed_cl+1.0
                                            subtype = TCoreLeaveCodeForSapReport.objects.only('code').get(name='Casual Leave').code
                                        elif l_type == 'EL':
                                            # availed_el=availed_el+1.0
                                            
                                            subtype = TCoreLeaveCodeForSapReport.objects.only('code').get(name='Earn Leave').code
                                        elif l_type == 'SL':
                                            # availed_sl=availed_sl+1.0
                                            
                                            subtype = TCoreLeaveCodeForSapReport.objects.only('code').get(name='Sick Leave').code
                                        

                                elif availed_FD.filter(leave_type_final_hd__isnull=False):
                                    if availed_FD.values('leave_type_final_hd').count() >1:
                                        if availed_FD.filter(leave_type_final_hd='AL'):
                                            # availed_hd_cl=availed_hd_cl+0.5
                                            subtype = TCoreLeaveCodeForSapReport.objects.only('code').get(name='All Leave(Half)').code
                                        elif availed_FD.filter(leave_type_final_hd='AB'):
                                            # availed_hd_ab=availed_hd_ab+0.5
                                            subtype = TCoreLeaveCodeForSapReport.objects.only('code').get(name='Absent(Half)').code

                                        elif availed_FD.filter(leave_type_final_hd='CL'):
                                            # availed_hd_cl=availed_hd_cl+0.5
                                            subtype = TCoreLeaveCodeForSapReport.objects.only('code').get(name='Casual Leave(Half)').code
                                        elif availed_FD.filter(leave_type_final_hd='EL'):
                                            # availed_hd_cl=availed_hd_cl+0.5
                                            subtype = TCoreLeaveCodeForSapReport.objects.only('code').get(name='Earn Leave(Half)').code
                                        elif availed_FD.filter(leave_type_final_hd='SL'):
                                            # availed_hd_cl=availed_hd_cl+0.5
                                            subtype = TCoreLeaveCodeForSapReport.objects.only('code').get(name='Sick Leave(Half)').code

                                        
                                                    

                                    else:
                                        l_type=availed_FD[0]['leave_type_final_hd']
                                        if l_type == 'AL':
                                            # availed_hd_ab=availed_hd_ab+1.0
                                            subtype = TCoreLeaveCodeForSapReport.objects.only('code').get(name='All Leave(Half)').code
                                            
                                        elif l_type == 'AB':
                                            # availed_hd_ab=availed_hd_ab+1.0
                                            subtype = TCoreLeaveCodeForSapReport.objects.only('code').get(name='Absent(Half)').code
                                        elif l_type == 'CL':
                                            # availed_hd_cl=availed_hd_cl+0.5
                                           subtype = TCoreLeaveCodeForSapReport.objects.only('code').get(name='Casual Leave(Half)').code

                                        elif l_type == 'EL':
                                            # availed_hd_el=availed_hd_el+0.5
                                            subtype = TCoreLeaveCodeForSapReport.objects.only('code').get(name='Earn Leave(Half)').code
                                        elif l_type == 'SL':
                                            # availed_hd_sl=availed_hd_sl+0.5
                                            subtype = TCoreLeaveCodeForSapReport.objects.only('code').get(name='Sick Leave(Half)').code

                                        

                                        

                                if subtype:
                                    data_list = [name,dept,sap_no, subtype, data_str, data_str,is_exit,termination_date]
                                    # header = ['PERSONNEL NUMBER(SAP ID)',' SUBTYPE',' BEGIN DATE',' ENDDATE']
                                    total_list.append(data_list)
                                # elif subtype:
                                #     data_list = [user_name, cu_emp_code, cu_punch_id, subtype, data_str, data_str]
                                #     header = ['FULL NAME','EMPLOYEE CODE','PUNCH ID',' SUBTYPE',' BEGIN DATE',' ENDDATE']
                                # total_list.append(data_list)

            ## add fortnight Leaves  to list
            fortnightLeaves = PmsAttandanceFortnightLeaveDeductionLog.objects.filter(
                            attendance_date__gte=date_range[0]['month_start__date'],
                            attendance_date__lte=date_range[0]['month_end__date'],
                            attendance__employee__in=module_user_list,
                            is_deleted=False
                            )
            logger.info(fortnightLeaves.query)
            logger.info(len(fortnightLeaves))
            #print('fortnightLeaves',fortnightLeaves)
            data_list_fortnight = list()
            if fortnightLeaves:
                
                for e_fortnightLeaves in fortnightLeaves:
                    logger.info(e_fortnightLeaves.employee)
                    list_fortnight = list()
                    data_str = e_fortnightLeaves.attendance.date.strftime("%d.%m.%Y")
                    subtype = None
                    sap_no = None
                    employee_obj = TCoreUserDetail.objects.get(cu_user=e_fortnightLeaves.employee)
                    sap_no = employee_obj.sap_personnel_no
                    company_code = employee_obj.company
                    name = employee_obj.cu_user.get_full_name()
                    dept = employee_obj.department.cd_name if employee_obj.department else ''
                    is_exit = 'Yes' if employee_obj.termination_date else ''
                    termination_date = employee_obj.termination_date

                    if sap_no and sap_no!='#N/A':
                        if e_fortnightLeaves.deviation_type == 'FD':
                            if e_fortnightLeaves.leave_type == 'AL':
                                subtype = TCoreLeaveCodeForSapReport.objects.only('code').get(name='All Leave').code
                            if e_fortnightLeaves.leave_type == 'AB':
                                subtype = TCoreLeaveCodeForSapReport.objects.only('code').get(name='Absent').code
                            if e_fortnightLeaves.leave_type == 'CL':
                                subtype = TCoreLeaveCodeForSapReport.objects.only('code').get(name='Casual Leave').code
                            if e_fortnightLeaves.leave_type == 'EL':
                                subtype = TCoreLeaveCodeForSapReport.objects.only('code').get(name='Earn Leave').code
                            if e_fortnightLeaves.leave_type == 'SL':
                                subtype = TCoreLeaveCodeForSapReport.objects.only('code').get(name='Sick Leave').code

                        if e_fortnightLeaves.deviation_type == 'HD':

                            if e_fortnightLeaves.leave_type == 'AL':
                                subtype = TCoreLeaveCodeForSapReport.objects.only('code').get(name='All Leave(Half)').code
                            if e_fortnightLeaves.leave_type == 'AB':
                                subtype = TCoreLeaveCodeForSapReport.objects.only('code').get(name='Absent(Half)').code
                            if e_fortnightLeaves.leave_type == 'CL':
                                subtype = TCoreLeaveCodeForSapReport.objects.only('code').get(name='Casual Leave(Half)').code
                            if e_fortnightLeaves.leave_type == 'EL':
                                subtype = TCoreLeaveCodeForSapReport.objects.only('code').get(name='Earn Leave(Half)').code
                            if e_fortnightLeaves.leave_type == 'SL':
                                subtype = TCoreLeaveCodeForSapReport.objects.only('code').get(name='Sick Leave(Half)').code

                        if subtype:
                            list_fortnight = [name, dept, sap_no, subtype, data_str, data_str,is_exit,termination_date]
                            # header = ['PERSONNEL NUMBER(SAP ID)',' SUBTYPE',' BEGIN DATE',' ENDDATE']
                            data_list_fortnight.append(list_fortnight)

        logger.info('data_list_fortnight')                 
        logger.info(len(data_list_fortnight))
        total_list = total_list + data_list_fortnight
        # updated by Shubhadeep - follow this code for any file donwload
        relative_dir_path = 'media/pms/attendance/sap_report/document'
        dir_path = os.path.join(settings.MEDIA_ROOT_EXPORT, relative_dir_path)
        if not os.path.isdir(dir_path):
            os.makedirs(dir_path)
        file_name = os.path.join(dir_path, 'sap_report.csv')
        relative_file_name = os.path.join(relative_dir_path, 'sap_report.csv')
        
        #########################################################
        df = DataFrame(total_list, columns= ['NAME','DEPT','PERSONNEL NUMBER(SAP ID)',' SUBTYPE',' BEGIN DATE',' ENDDATE','IS EXIT','TERMINATION DATE'])
        export_csv = df.to_csv (file_name, index = None, header=True)

        if request.is_secure():
            protocol = 'https://'
        else:
            protocol = 'http://'

        url = getHostWithPort(request) + relative_file_name if relative_file_name else None
        print('url',url)

        return Response(url)

class PmsAttendanceLeaveApprovalListV2View(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    serializer_class = PmsAttendanceLeaveApprovalListV2Serializer
    pagination_class = CSPageNumberPagination
    queryset = PmsAttandanceDeviation.objects.filter(Q(is_requested=True)&
                                                        Q(lock_status=False)&
                                                        ~Q(leave_type=None)&
                                                        (Q(approved_status='1')|
                                                        Q(approved_status='5')))
    def get_queryset(self):
        print('self.queryset',self.queryset)
        team_approval_flag = self.request.query_params.get('team_approval_flag', None)
        sort_field='-id'
        search_sort_flag = True
        if team_approval_flag == '1':
            login_user_details = self.request.user
            print('login_user_details',login_user_details)
            print('login_user_details',login_user_details.is_superuser)
            if login_user_details.is_superuser == False:
                #print('check')
                users_list_under_the_login_user = TCoreUserDetail.objects.filter(
                    reporting_head = login_user_details,
                    cu_is_deleted = False
                ).values_list('cu_user')
                print('users_list_under_the_login_user',users_list_under_the_login_user)
                if users_list_under_the_login_user:
                    attendence_id_list = PmsAttendance.objects.filter(
                                employee__in=users_list_under_the_login_user,
                                is_deleted = False
                                ).values_list('id')
                    print('attedence_details',attendence_id_list)
                    if attendence_id_list:
                        
                        result = self.queryset.filter(attandance__in=attendence_id_list)
                        print('result',result)
                        if result:
                            search_sort_flag = True
                            self.queryset = result
                        else:
                            search_sort_flag = False
                            #self.queryset = []
                        #print('self.queryset',self.queryset.query)
                    else:
                        search_sort_flag = False
                        #self.queryset = self.queryset
                else:
                    search_sort_flag = False
                    #self.queryset =  self.queryset
                
            else:
                search_sort_flag = True
                self.queryset = self.queryset  
        if search_sort_flag:     
            print('enter') 
            filter = dict()  
            field_name = self.request.query_params.get('field_name', None)
            order_by = self.request.query_params.get('order_by', None)
            search= self.request.query_params.get('search', None)
            leave_type=self.request.query_params.get('leave_type', None)
            users = self.request.query_params.get('users', None)
            dept_filter = self.request.query_params.get('dept_filter', None)
            designation = self.request.query_params.get('designation', None)
            reporting_head = self.request.query_params.get('reporting_head', None)
            hod = self.request.query_params.get('hod', None)
            from_date = self.request.query_params.get('from_date', None)
            to_date = self.request.query_params.get('to_date', None)
            request_type=self.request.query_params.get('request_type', None)
            leave_type=self.request.query_params.get('leave_type', None)

            if users:
                user_lst = users.split(',')
                filter['attandance__employee__in'] = user_lst
        
            if field_name and order_by:      
                if field_name =='date' and order_by=='asc':
                    sort_field='duration_start__date'
                    # return self.queryset.all().order_by('duration_start__date')
                if field_name =='date' and order_by=='desc':
                    sort_field='-duration_start__date'
                    # return self.queryset.all().order_by('-duration_start__date')
                if field_name =='duration_start' and order_by=='asc':
                    sort_field='duration_start'
                    # return self.queryset.all().order_by('duration_start')
                if field_name =='duration_start' and order_by=='desc':
                    sort_field='-duration_start'
                    # return self.queryset.all().order_by('-duration_start')

                if field_name =='duration_end' and order_by=='asc':
                    sort_field='duration_end'
                    # return self.queryset.all().order_by('duration_end')
                if field_name =='duration_end' and order_by=='desc':
                    sort_field='-duration_end'
                    # return self.queryset.all().order_by('-duration_end')

                if field_name =='duration' and order_by=='asc':
                    sort_field='duration'
                    # return self.queryset.all().order_by('duration')
                if field_name =='duration' and order_by=='desc':
                    sort_field='-duration'
                    # return self.queryset.all().order_by('-duration')
                if field_name =='department' and order_by=='desc':
                    sort_field='-attandance__employee__cu_user__department'
                if field_name =='department' and order_by=='asc':
                    sort_field='attandance__employee__cu_user__department'
                if field_name =='designation' and order_by=='desc':
                    sort_field='-attandance__employee__cu_user__designation'
                if field_name =='designation' and order_by=='asc':
                    sort_field='attandance__employee__cu_user__designation'
                if field_name =='reporting_head' and order_by=='desc':
                    sort_field='-attandance__employee__cu_user__reporting_head'
                if field_name =='reporting_head' and order_by=='asc':
                    sort_field='attandance__employee__cu_user__reporting_head'
                if field_name =='hod' and order_by=='desc':
                    sort_field='-attandance__employee__cu_user__hod'
                if field_name =='hod' and order_by=='asc':
                    sort_field='attandance__employee__cu_user__hod'


            if from_date and to_date:
                start_object = datetime.strptime(from_date, '%Y-%m-%d').date()
                filter['duration_start__date__gte'] = start_object
                end_object = datetime.strptime(to_date, '%Y-%m-%d').date()
                filter['duration_start__date__lte'] = end_object + timedelta(days=1)
            
            if dept_filter:
                dept_list = dept_filter.split(',')
                emp_list = TCoreUserDetail.objects.filter(department__in=dept_list).values_list('cu_user',flat=True)
                filter['attandance__employee__in'] = emp_list

            if designation:
                    designation_list = designation.split(',')
                    emp_list = TCoreUserDetail.objects.filter(designation__in=designation_list).values_list('cu_user',flat=True)
                    filter['attandance__employee__in'] = emp_list
                
            if reporting_head:
                filter['attandance__employee__cu_user__reporting_head'] = reporting_head

            if hod:
                filter['attandance__employee__cu_user__hod'] = hod
            
            if leave_type:
                leave_type_list=leave_type.split(',')
                filter['leave_type__in']= leave_type_list

            if request_type:
                request_type_list=request_type.split(',')
                filter['request_type__in']= request_type_list

            if search :
                search_data = list(map(str,search.split(" ")))
                print("This is if condition entry")
                if len(search.split(" "))>0 and len(search.split(" "))<2:
                    print("length 1 hai ")
                    queryset = self.queryset.filter((Q(attandance__employee__first_name__icontains=search_data[0])|Q(attandance__employee__last_name__icontains=search_data[0])),
                                                    **filter).order_by(sort_field)                            
                    return queryset
                elif len(search.split(" "))>1:
                    print("length 2 hai ")
                    queryset = self.queryset.filter((Q(attandance__employee__first_name__icontains=search_data[0]) & Q(attandance__employee__last_name__icontains=search_data[1])),
                                                    **filter).order_by(sort_field)
                    return queryset      
           
            
            else:
                # print('filter',**filter)
                queryset = self.queryset.filter(**filter).order_by(sort_field)
                return queryset
        else:
            print('sdsdsdsds')
            return []

    @response_modify_decorator_list_or_get_after_execution_for_pagination
    def get(self, request, *args, **kwargs):
        response=super(__class__, self).get(self, request, args, kwargs)
        return response

class PmsAttendanceGraceLeaveListModifiedV2View(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsAttandanceDeviation.objects.all()

    def get(self, request, *args, **kwargs):
        # response=super(AttendanceGraceLeaveListModifiedView,self).get(self, request, args, kwargs)
        date =self.request.query_params.get('date', None)
        # print('date',type(date))
        date_object = datetime.strptime(date, '%Y-%m-%d').date()
        #date_object = datetime.now().date()
        #print('date_object',date_object)
        employee_id=self.request.query_params.get('employee_id', None)
        total_grace={}
        data_dict = {}
        is_previous=self.request.query_params.get('is_previous', None)
        #is_previous = 'true'

        aa = datetime.now()
        total_month_grace=AttendenceMonthMaster.objects.filter(month_start__date__lte=date_object,
                                        month_end__date__gte=date_object,is_deleted=False).values('grace_available',
                                                                                 'year_start_date',
                                                                                 'year_end_date',
                                                                                 'month',
                                                                                 'month_start',
                                                                                 'month_end')
        if is_previous == "true":
            #print('sada',type(total_month_grace[0]['month_start']))
            '''
                Changed by Rupam Hazra due to same variable date_object
            '''
            date_object = total_month_grace[0]['month_start'].date()- timedelta(days=1)

        print('date_object',date_object)
        user = TCoreUserDetail.objects.filter(cu_user=employee_id,cu_is_deleted=False).first()
        result = all_leave_calculation_upto_applied_date_pms(date_object=date_object, user=user)
        
        data_dict['result'] = result
        time_last = datetime.now()-aa
        #print("time_last",time_last)
        # data_dict['result'] = "Successful"
        if result:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_SUCCESS
        elif len(result) == 0:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_NO_DATA
        else:
            data_dict['request_status'] = 0
            data_dict['msg'] = settings.MSG_ERROR
        return Response(data_dict)

class AttandanceDeviationApprovaEditV2View(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsAttandanceDeviation.objects.filter(Q(is_requested=True)&
                                                        Q(lock_status=False)&
                                                        (Q(approved_status='1')|
                                                        Q(approved_status='5')))
    serializer_class = AttandanceDeviationApprovaEditV2Serializer

class AttandanceDeviationJustificationV2EditView(generics.RetrieveUpdateAPIView):
	permission_classes = [IsAuthenticated]
	authentication_classes = [TokenAuthentication]
	queryset = PmsAttandanceDeviation.objects.all()
	serializer_class =  AttandanceDeviationJustificationV2Serializer

class AbsentAttendanceInsertCronView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    

    def pms_att_create(self, filter: dict):
        attendance,_ = PmsAttendance.objects.get_or_create(**filter)
        return attendance

    def pms_log_create(self, filter: dict):
        log,_ = PmsAttandanceLog.objects.get_or_create(**filter)
        return log

    def pms_request_create(self, filter: dict,user):
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
        #print('request',request)
        #time.sleep(10)
        return request

    def get(self, request, *args, **kwargs):
        
        filter = dict()
        filter['attendance_type'] = 'PMS'
        
        employee_id = self.request.query_params.get('employee_id', None)
        date_time_day = self.request.query_params.get('current_date', None)
        
        if not date_time_day:
            current_date = datetime.now()
            date_time_day = current_date.date()

        if employee_id:
            filter['cu_user_id'] =  employee_id
            
        
        print("==================================================================================")

        month_master = AttendenceMonthMaster.objects.filter(
            month_start__date__lte=date_time_day,
            month_end__date__gte=date_time_day,
            is_deleted=False
            ).first()

        #print("month_master:", month_master)

        termination_start_day = month_master.month_start
        termination_end_day = get_last_day_of_month(month_master.month_end)

        #print('termination_start_day',termination_start_day)
        #print('termination_end_day',termination_end_day)

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
        
        #raise APIException({'userlist': len(users_list_in_pms),'ids': users_list_in_pms, 'query':users_list_in_pms.query})

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
                            abs_att = self.pms_att_create(att_filter)
                            print('abs_att',abs_att,type(abs_att))
                            if abs_att:
                                log_filter['attandance'] = abs_att
                                login_log_details = self.pms_log_create(log_filter)
                                print('login_log_details',login_log_details)
                                if login_log_details:
                                    log_filter['time'] = logout_time
                                    log_filter['login_logout_check'] = 'Logout'
                                    log_filter['login_id'] = login_log_details.id
                                    logout_log_details = self.pms_log_create(log_filter)
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
                                            abs_req = self.pms_request_create(req_filter,each_user)
                                            print('abs_req',abs_req)
                                            print('----------------------------------------------------------------')
                                        
                    
                return Response({'msg':'success'})
        
        except Exception as e:
            raise APIException({'error':e})


class AttendanceAddV2View(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsAttendance.objects.all()
    serializer_class = AttendanceAddV2Serializer

    def post(self, request, *args,**kwargs):
        # print("request",request.user.email)
        # response = super(AttendanceAddView, self).post(request, args, kwargs)
        login_date =datetime.strptime(request.data['login_time'],'%Y-%m-%dT%H:%M:%S').date()
        #print("login_date",login_date)
        attandance_data = custom_filter(
                self,
                PmsAttendance,
                filter_columns={"date__date": login_date, "employee__username":request.user.username}, #modified by Rupam
                fetch_columns=['id', 'type', 'employee', 'user_project', 'date', 'login_time', 'login_latitude', 'login_longitude',
                  'login_address','logout_time', 'logout_latitude', 'logout_longitude', 'logout_address', 'approved_status',
                  'justification','created_by', 'owned_by'],
                single_row=True
                          )
        #print("req",request.user)
        #print("login_time_data",attandance_data)

        project_user_mapping = PmsProjectUserMapping.objects.filter(user=request.user, status=True).order_by('-id').values('project')
        #print("project_user_mapping",project_user_mapping)
        if project_user_mapping:
            project = project_user_mapping[0]['project']
            request.data['user_project_id'] = project
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
        
        #print('request.data',request.data)
        time = request.data.pop('login_time')
        latitude = request.data.pop('login_latitude')
        longitude = request.data.pop('login_longitude')
        address = request.data.pop('login_address')
        is_checkout = request.data.pop('is_checkout')
        is_checkout_auto_od = request.data.pop('is_checkout_auto_od')
        device_details = request.data.pop('device_details') if 'device_details' in request.data else None
        token_full = request.META.get('HTTP_AUTHORIZATION')
        token = token_full.split(' ')
        #print('request.data',device_details)

        if attandance_data:
            PmsAttandanceLog.objects.get_or_create(
                    attandance_id = attandance_data['id'],
                    login_logout_check = 'Login',
                    time=time,
                    latitude=latitude,
                    longitude=longitude,
                    address=address,
                    created_by=request.user,
                    owned_by=request.user,
                    is_checkout= is_checkout,
                    is_checkout_auto_od = is_checkout_auto_od,
                    device_details=device_details,
                    token = token[1]
                )
            
            attandance_data['user_project_details'] = multi_lat_long
            attandance_data['geo_fencing_area'] = geofence
            return Response({'result':attandance_data,
                             'request_status': 1,
                             'msg': settings.MSG_SUCCESS
                             })
        else:
            attendance_add, created = PmsAttendance.objects.get_or_create(
                employee=request.user,
                created_by=request.user,
                owned_by=request.user,
                day_remarks='Present',
                is_present= True,
                **request.data
            )

            PmsAttandanceLog.objects.get_or_create(
                    attandance = attendance_add,
                    login_logout_check = 'Login',
                    time=time,
                    latitude=latitude,
                    longitude=longitude,
                    address=address,
                    created_by=request.user,
                    owned_by=request.user,
                    is_checkout= is_checkout,
                    is_checkout_auto_od = is_checkout_auto_od,
                    device_details=device_details,
                    token=token[1]
                )
            
            #print("attendance_add",attendance_add.__dict__)
            attendance_add.__dict__.pop('_state') if "_state" in attendance_add.__dict__.keys() else attendance_add.__dict__
            attendance_add.__dict__['user_project_details'] = multi_lat_long
            attendance_add.__dict__['geo_fencing_area'] = geofence

            return Response({'result':attendance_add.__dict__,
                             'request_status': 1,
                             'msg': settings.MSG_SUCCESS
                             })

class AttendanceLogOutV2View(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsAttendance.objects.filter(is_deleted=False)
    serializer_class = AttendanceLogOutV2Serializer

    def put(self, request,* args, **kwargs):
        response = super(AttendanceLogOutV2View, self).put(request, args, kwargs)
        # print('request: ', request.data)
        data_dict = {}
        data_dict['result'] = request.data
        if response.data:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_SUCCESS
        else:
            data_dict['request_status'] = 0
            data_dict['msg'] = settings.MSG_ERROR

        response.data = data_dict
        return response

class AttendanceUpdateLogOutTimeFailedOnLogoutV2View(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsAttendance.objects.filter(is_deleted=False)
    serializer_class = AttendanceUpdateLogOutTimeFailedOnLogoutV2Serializer

    @response_modify_decorator_update
    def put(self, request,* args, **kwargs):
        return super().update(request, *args, **kwargs)

class AttendanceListByEmployeeV2View(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsAttendance.objects.filter(is_deleted=False)
    serializer_class = AttendanceListV2Serializer
    filter_backends = (filters.OrderingFilter, filters.SearchFilter,)
    search_fields = ('date', 'employee', 'employee__username', 'login_time', 'logout_time', 'type')
    ordering = ('-created_at',)

    def get_queryset(self):
        filter = {}
        date_range = None
        emp_id = self.kwargs["employee_id"]
        is_previous = self.request.query_params.get('is_previous', None)
        current_date = self.request.query_params.get('current_date', None)

        year = int(self.request.query_params['year']) if 'year' in self.request.query_params else int(
            datetime.now().date().strftime("%Y"))
        month = int(self.request.query_params['month']) if 'month' in self.request.query_params else int(
            datetime.now().date().strftime("%m"))
        
        if emp_id:
            filter['employee']=emp_id
            self.emp_id = emp_id

        if current_date:
            #print("current_date",current_date)
            date = datetime.strptime(current_date, "%Y-%m-%d")
            date_range = AttendenceMonthMaster.objects.filter(month_start__date__lte=date,month_end__date__gte=date).values('month_start__date','month_end__date')
            # print("date_range",date_range)
            self.date_range_str = date_range[0]['month_start__date']
            self.date_range_end = date.date()

            if is_previous == 'true':
                # print("is_previous",is_previous)
                date = date_range[0]['month_start__date'] - timedelta(days=1)
                # print("date",date)
                date_range = AttendenceMonthMaster.objects.filter(month_start__date__lte=date,month_end__date__gte=date).values('month_start__date','month_end__date')
                # print("is_previous_date_range",date_range)
                self.date_range_str = date_range[0]['month_start__date']
                self.date_range_end = date_range[0]['month_end__date']
            # print("date_range",date_range)

            filter['date__date__gte'] = self.date_range_str
            filter['date__date__lte'] = self.date_range_end

        elif month and year and emp_id:
            date_range = AttendenceMonthMaster.objects.filter(month=month,month_end__year=year).values(
                'month_start__date','month_end__date')
            filter['date__date__gte'] = date_range[0]['month_start__date']
            filter['date__date__lte'] = date_range[0]['month_end__date']
            #print("date_range",date_range)
        
        if filter :
            queryset = self.queryset.filter(**filter)
            return queryset


    def list(self, request, *args, **kwargs):
        try:
            response = super(__class__, self).list(request, args, kwargs)
            results_data_listofdict = response.data
            date_list_data = []
            
            for od in results_data_listofdict:
                date_list_data.append(datetime.strptime(od['date'], "%Y-%m-%dT%H:%M:%S").date())
                #print('od',od)
                #time.sleep(3)
                cng_leave_type = None
                oth_leave_period = None
                daily_leave_type = None
                daily_leave_period = None
                oth_leave_type = None
                day_remarks = None
                
                queryset_att_log = PmsAttandanceLog.objects.filter(attandance=od['id'],login_logout_check__in=('Logout',))
                login_logout_list = list()
                #print('queryset_att_log',queryset_att_log.query,queryset_att_log)
                if queryset_att_log:

                    for e_queryset_att_log in queryset_att_log:
                        
                        #print('fffff')
                        login_logout_dict=dict()
                        #login_logout_dict['day_remarks'] = "Present"
                        login_logout_dict['login_time'] = PmsAttandanceLog.objects.filter(
                            attandance=od['id'],id=e_queryset_att_log.login_id).values_list('time',flat=True).first()
                        login_logout_dict['logout_time'] = e_queryset_att_log.time
                        login_logout_list.append(login_logout_dict)

                        deviation_details = PmsAttandanceDeviation.objects.filter(
                            attandance=od['id'],
                            from_time__gte=login_logout_dict['login_time'],
                            to_time__lte=login_logout_dict['logout_time']
                            )
                        #print('deviation_details',deviation_details.query)
                        total_deviation_time = timedelta(hours=00, minutes=00, seconds=00)
                        deviation_list=[]
                        if deviation_details:                   
                            for deviation in deviation_details:
                                #print('deviation',deviation.attandance.date.date())
                                
                                leave_day_remarks = calculate_day_remarks(user=od['employee'], date_obj=deviation.attandance.date.date(),which_module='PMS')
                                #print('leave_day_remarks',leave_day_remarks)
                                #time.sleep(2)
                                if leave_day_remarks:
                                    day_remarks = leave_day_remarks

                                if deviation.approved_status== '1' and att_req.deviation_type =='OD':
                                    day_remarks = 'OD'
                              

                                

                                if deviation.deviation_time:
                                    deviation_time = datetime.strptime(deviation.deviation_time,'%H:%M:%S').time()
                                    deviation_time_timedelta= timedelta(hours=deviation_time.hour, minutes=deviation_time.minute, seconds=deviation_time.second)
                                    total_deviation_time = total_deviation_time + deviation_time_timedelta

                                justified_by=deviation.justified_by.id if deviation.justified_by else None
                                justified_by_name=userdetails(justified_by)  
                                approved_by=deviation.approved_by.id if deviation.approved_by else None
                                approved_by_name=userdetails(approved_by)
                                #deviation_time = datetime.strptime(deviation.deviation_time,'%H:%M:%S').hour
                                #print('deviation_time',deviation_time)
                                deviation_time = datetime.strptime(deviation.deviation_time,"%H:%M:%S")
                                total_seconds = deviation_time.second + deviation_time.minute*60 + deviation_time.hour*3600

                                if deviation.leave_type_changed:
                                    cng_leave_type= deviation.leave_type_changed
                                    if deviation.leave_type_changed_period=='FD':
                                        cng_leave_period = 1
                                    elif deviation.leave_type_changed_period=='HD':
                                        cng_leave_period = 0.5
                                elif deviation.leave_type:
                                    oth_leave_type= deviation.leave_type
                                    if deviation.deviation_type=='FD':
                                        oth_leave_period = 1
                                    elif deviation.deviation_type=='HD':
                                        oth_leave_period = 0.5

                                if cng_leave_type:
                                    daily_leave_type=cng_leave_type
                                    daily_leave_period=cng_leave_period

                                elif oth_leave_type:
                                    daily_leave_type=oth_leave_type
                                    daily_leave_period=oth_leave_period

                                deviation_time = round((total_seconds)/60)
                                deviation_dict={
                                    'id':deviation.id,
                                    'from_time':deviation.from_time,
                                    'to_time':deviation.to_time,
                                    'deviation_time': deviation_time,
                                    'duration':deviation.duration,
                                    'deviation_type':deviation.deviation_type,
                                    'deviation_type_name':deviation.get_deviation_type_display(),
                                    'justification':deviation.justification,
                                    'approved_status':deviation.approved_status,
                                    'approved_status_name':deviation.get_approved_status_display(),
                                    'remarks':deviation.remarks,
                                    'justified_by':justified_by,
                                    'justified_by_name':justified_by_name,
                                    'justified_at':deviation.justified_at,
                                    'approved_by':approved_by,
                                    'approved_by_name':approved_by_name,
                                    'approved_at':deviation.approved_at,
                                    'lock_status':deviation.lock_status,
                                    'leave_type_changed_period':deviation.leave_type_changed_period,
                                    'leave_type_changed':deviation.leave_type_changed,
                                    'request_date':deviation.request_date,
                                    'is_requested':deviation.is_requested,
                                    'leave_type':deviation.leave_type,
                                    #'day_remarks':leave_day_remarks
                                }
                                deviation_list.append(deviation_dict)

                        
                        
                        
                        if deviation_details:
                            login_logout_dict['is_deviation'] = 1
                        else:
                            login_logout_dict['is_deviation'] = 0
               
                        login_logout_dict['deviation_details'] = deviation_list

                    

                else:
                    login_logout_dict=dict()
                    login_logout_dict['login_time'] = PmsAttandanceLog.objects.filter(
                        attandance=od['id'],login_logout_check='Login').values_list('time',flat=True).first()
                    login_logout_dict['logout_time'] = None
                    login_logout_dict['is_deviation'] = 0
                    login_logout_dict['deviation_details'] = list()
                    login_logout_list.append(login_logout_dict)

                week_day = datetime.strptime(od['date'], '%Y-%m-%dT%H:%M:%S').strftime('%A')
                od['date'] = datetime.strptime(od['date'], '%Y-%m-%dT%H:%M:%S').strftime('%Y-%m-%d')
                od['week_day'] = week_day
                od['present'] = od['is_present']
                od['holiday'] = 0
                od['login_logout_details'] = login_logout_list
                od['daily_leave_type'] = daily_leave_type
                od['daily_leave_period'] = daily_leave_period

                #print('day_remarks',day_remarks)
                #time.sleep(2)
                if day_remarks:
                    od['day_remarks'] = day_remarks
                

        
            ### For New Joinee in current month ###
            day_list = self.last_day_of_month(self.date_range_str,self.date_range_end)
            joining_date = None
            joining_date = TCoreUserDetail.objects.only('joining_date').get(cu_user=self.emp_id).joining_date.date()
            new_dict = {}

            if date_list_data:
                for day in day_list:
                    if day not in date_list_data:
                        # print("day", day)
                        new_dict={
                            'id' : None,
                            'date' : day.strftime("%Y-%m-%dT%H:%M:%S"),
                            'is_present' : False,
                            "day_remarks": "Absent",
                            "is_deleted":False,
                            'week_day': day.strftime('%A'),
                            "daily_leave_type":"",
                            "daily_leave_period":'',
                            "login_logout_list": list()
                            }
                        if joining_date:
                            if joining_date > day:
                                new_dict['day_remarks']="Not Joined"
                            # elif joining_date == day:
                            #     new_dict['day_remarks']="Joining date"
                        
                        results_data_listofdict.append(new_dict)

            response_data_dict = collections.OrderedDict()
            response_data_dict['count'] = len(results_data_listofdict)
            response_data_dict['results'] = results_data_listofdict
            response_data_dict['request_status'] = 1
            if response_data_dict['count'] > 0:
                response_data_dict['msg'] = settings.MSG_SUCCESS
            else:
                response_data_dict['msg'] = 'No Data Found'
            # print(response_data_dict)
            return Response(self.list_synchronization(response_data_dict))
        except Exception as e:
            raise e
            # raise APIException({'request_status': 0, 'msg': e})

    
    def last_day_of_month(self,sdate, edate):
        days_list = []
        delta = edate - sdate       # as timedelta
        for i in range(delta.days + 1):
            day = sdate + timedelta(days=i)
            # print(day)
            days_list.append(day)
        return days_list
    
    def list_synchronization(self, list_data: list)-> list:
        data = pd.DataFrame(list_data["results"])
        data = data.replace(np.nan, 0, regex=True)
        if list_data["results"]:
            data.sort_values("date", axis = 0, ascending = True, inplace = True,)
        col_list = data.columns.values
        row_list = data.values.tolist()
        total_result = list()
        for row in row_list:
            data_dict = dict(zip(col_list,row))
            total_result.append(data_dict)
        list_data["results"] = total_result
        return list_data
   
class AttendanceSummaryByEmployeeV2View(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsAttendance.objects.filter(is_deleted=False)
    serializer_class = AttendanceListV2Serializer
    filter_backends = (filters.OrderingFilter, filters.SearchFilter,)
    search_fields = ('date', 'employee', 'employee__username', 'login_time', 'logout_time', 'type')
    ordering = ('-created_at',)

    def get_queryset(self):
        filter = {}
        date_range = None
        emp_id = self.kwargs["employee_id"]

        year = int(self.request.query_params['year']) if 'year' in self.request.query_params else int(
            datetime.now().date().strftime("%Y"))
        month = int(self.request.query_params['month']) if 'month' in self.request.query_params else int(
            datetime.now().date().strftime("%m"))

        if month and year and emp_id:
            date_range = AttendenceMonthMaster.objects.filter(month=month,month_end__year=year).values(
                'month_start__date','month_end__date')
            print("date_range",date_range)

        if date_range:
            print("This is if")
            filter['employee']=emp_id
            filter['date__date__gte'] = date_range[0]['month_start__date']
            filter['date__date__lte'] = date_range[0]['month_end__date']
        if filter :
            queryset = self.queryset.filter(**filter)
            return queryset

    def list(self, request, *args, **kwargs):
        try:
            response = super(__class__, self).list(request, args, kwargs)
            results_data_listofdict = response.data
        
            for od in results_data_listofdict:
                cng_leave_type = None
                oth_leave_period = None
                daily_leave_type = None
                daily_leave_period = None
                oth_leave_type = None
                day_remarks = None
                queryset_att_log = PmsAttandanceLog.objects.filter(attandance=od['id'],login_logout_check__in=('Logout',))
                login_logout_list = list()
                #print('queryset_att_log',queryset_att_log.query,queryset_att_log)
                if queryset_att_log:
                    for e_queryset_att_log in queryset_att_log:
                        
                        login_logout_dict=dict()
                        #login_logout_dict['day_remarks'] = "Present"
                        login_logout_dict['login_time'] = PmsAttandanceLog.objects.filter(
                            attandance=od['id'],id=e_queryset_att_log.login_id).values_list('time',flat=True).first()
                        login_logout_dict['logout_time'] = e_queryset_att_log.time
                        login_logout_list.append(login_logout_dict)

                        deviation_details = PmsAttandanceDeviation.objects.filter(
                            attandance=od['id'],
                            from_time__gte=login_logout_dict['login_time'],
                            to_time__lte=login_logout_dict['logout_time']
                            )
                        #print('deviation_details',deviation_details.query)
                        total_deviation_time = timedelta(hours=00, minutes=00, seconds=00)
                        deviation_list=[]
                        if deviation_details:                   
                            for deviation in deviation_details:

                                leave_day_remarks = calculate_day_remarks(user=od['employee'], date_obj=deviation.attandance.date.date(),which_module='PMS')
                                #print('leave_day_remarks',leave_day_remarks)
                                #time.sleep(2)
                                if leave_day_remarks:
                                    day_remarks = leave_day_remarks
                                elif deviation.approved_status==1 and deviation.deviation_type =='OD':
                                    day_remarks = 'OD'

                                if deviation.deviation_time:
                                    deviation_time = datetime.strptime(deviation.deviation_time,'%H:%M:%S').time()
                                    deviation_time_timedelta= timedelta(hours=deviation_time.hour, minutes=deviation_time.minute, seconds=deviation_time.second)
                                    total_deviation_time = total_deviation_time + deviation_time_timedelta

                                justified_by=deviation.justified_by.id if deviation.justified_by else None
                                justified_by_name=userdetails(justified_by)  
                                approved_by=deviation.approved_by.id if deviation.approved_by else None
                                approved_by_name=userdetails(approved_by)
                                #deviation_time = datetime.strptime(deviation.deviation_time,'%H:%M:%S').hour
                                #print('deviation_time',deviation_time)
                                deviation_time = datetime.strptime(deviation.deviation_time,"%H:%M:%S")
                                total_seconds = deviation_time.second + deviation_time.minute*60 + deviation_time.hour*3600

                                if deviation.leave_type_changed:
                                    cng_leave_type= deviation.leave_type_changed
                                    if deviation.leave_type_changed_period=='FD':
                                        cng_leave_period = 1
                                    elif deviation.leave_type_changed_period=='HD':
                                        cng_leave_period = 0.5
                                elif deviation.leave_type:
                                    oth_leave_type= deviation.leave_type
                                    if deviation.deviation_type=='FD':
                                        oth_leave_period = 1
                                    elif deviation.deviation_type=='HD':
                                        oth_leave_period = 0.5

                                if cng_leave_type:
                                    daily_leave_type=cng_leave_type
                                    daily_leave_period=cng_leave_period

                                elif oth_leave_type:
                                    daily_leave_type=oth_leave_type
                                    daily_leave_period=oth_leave_period

                                deviation_time = round((total_seconds)/60)
                                deviation_dict={
                                    'id':deviation.id,
                                    'from_time':deviation.from_time,
                                    'to_time':deviation.to_time,
                                    'deviation_time': deviation_time,
                                    'duration':deviation.duration,
                                    'deviation_type':deviation.deviation_type,
                                    'deviation_type_name':deviation.get_deviation_type_display(),
                                    'justification':deviation.justification,
                                    'approved_status':deviation.approved_status,
                                    'approved_status_name':deviation.get_approved_status_display(),
                                    'remarks':deviation.remarks,
                                    'justified_by':justified_by,
                                    'justified_by_name':justified_by_name,
                                    'justified_at':deviation.justified_at,
                                    'approved_by':approved_by,
                                    'approved_by_name':approved_by_name,
                                    'approved_at':deviation.approved_at,
                                    'lock_status':deviation.lock_status,
                                    'leave_type_changed_period':deviation.leave_type_changed_period,
                                    'leave_type_changed':deviation.leave_type_changed,
                                    'request_date':deviation.request_date,
                                    'is_requested':deviation.is_requested,
                                    'leave_type':deviation.leave_type
                                }
                                deviation_list.append(deviation_dict)

                        if deviation_details:
                            login_logout_dict['is_deviation'] = 1
                        else:
                            login_logout_dict['is_deviation'] = 0
               
                        login_logout_dict['deviation_details'] = deviation_list

                else:
                    login_logout_dict=dict()
                    login_logout_dict['login_time'] = PmsAttandanceLog.objects.filter(
                        attandance=od['id'],login_logout_check='Login').values_list('time',flat=True).first()
                    login_logout_dict['logout_time'] = None
                    login_logout_dict['is_deviation'] = 0
                    login_logout_dict['deviation_details'] = list()
                    login_logout_list.append(login_logout_dict)

                week_day = datetime.strptime(od['date'], '%Y-%m-%dT%H:%M:%S').strftime('%A')
                od['date'] = datetime.strptime(od['date'], '%Y-%m-%dT%H:%M:%S').strftime('%Y-%m-%d')
                od['week_day'] = week_day
                od['present'] = od['is_present']
                od['holiday'] = 0
                od['login_logout_details'] = login_logout_list
                od['daily_leave_type'] = daily_leave_type
                od['daily_leave_period'] = daily_leave_period
                if day_remarks:
                    od['day_remarks'] = day_remarks
        
            response_data_dict = collections.OrderedDict()
            response_data_dict['count'] = len(results_data_listofdict)
            response_data_dict['results'] = results_data_listofdict
            response_data_dict['request_status'] = 1
            if response_data_dict['count'] > 0:
                response_data_dict['msg'] = settings.MSG_SUCCESS
            else:
                response_data_dict['msg'] = 'No Data Found'
            # print(response_data_dict)
            return Response(self.list_synchronization(response_data_dict))
        except Exception as e:
            raise e
            # raise APIException({'request_status': 0, 'msg': e})

    def list_synchronization(self, list_data: list)-> list:
        print('list_data',list_data)
        data = pd.DataFrame(list_data["results"])
        data = data.replace(np.nan, '', regex=True)
        if list_data["results"]:
            data.sort_values("date", axis = 0, ascending = True, inplace = True,)
        col_list = data.columns.values
        row_list = data.values.tolist()
        total_result = list()
        for row in row_list:
            data_dict = dict(zip(col_list,row))
            total_result.append(data_dict)
        list_data["results"] = total_result
        return list_data

class AttandanceAllDetailsListByPermissonV2View(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsAttendance.objects.filter(
        is_deleted=False,
        date__gte = str(datetime.now().year-1)+'-04'+'-01',
        date__lte = str(int(datetime.now().year))+'-03'+'-31')
    serializer_class = AttandanceALLDetailsListByPermissonV2Serializer
    pagination_class = CSPageNumberPagination

    def get_queryset(self):
        
        mode = self.request.GET.get('mode', None) # For HR view
        user_project = self.request.query_params.get('user_project', None)
        employee = self.request.query_params.get('employee', None)
        user_designation = self.request.query_params.get('user_designation', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        date = self.request.query_params.get('date', None)
        attendance = self.request.query_params.get('attendance', None)
        approved_status = self.request.query_params.get('approved_status', None)
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        module_name = self.request.query_params.get('module_name', None)
        module_id = str(TCoreModule.objects.get(cm_name=module_name))
        month = self.request.query_params.get('month', None)
        year = self.request.query_params.get('year', None)

        '''
            Sorting Start
        '''

        sort_field = '-id'
        if field_name != "" and order_by != "":
            if field_name == 'sort_first_name' and order_by == 'asc':
                sort_field='employee__first_name'
                
            elif field_name == 'sort_first_name' and order_by == 'desc':
                sort_field='-employee__first_name'
            
            elif field_name == 'sort_created_at' and order_by == 'asc':
                sort_field='created_at'
            
            elif field_name == 'sort_created_at' and order_by == 'desc':
                sort_field='-created_at'
            
            elif field_name == 'sort_user_project' and order_by == 'asc':
                sort_field='user_project'
            
            elif field_name == 'sort_user_project' and order_by == 'desc':
                sort_field='-user_project'
            
        if module_id:
            
            login_user_details = self.request.user
            #print('login_user_details',login_user_details.id)
            if login_user_details.is_superuser == False:

                '''
                    Added By Rupam Hazra 27.01.2020 from 563-660 for user type = module admin
                '''
                if mode and mode == 'hr':
                    users_list_under_the_login_user = TMasterModuleRoleUser.objects.filter(
                            mmr_module=module_id,mmr_is_deleted=False).values_list('mmr_user',flat=True)

                else:
                    which_type_of_user = TMasterModuleRoleUser.objects.filter(
                        mmr_module_id= module_id,
                        mmr_user=login_user_details,
                        mmr_is_deleted=False
                    ).values_list('mmr_type',flat=True)[0]

                    if which_type_of_user == 2: #[module admin]
                        
                        users_list_under_the_login_user = TMasterModuleRoleUser.objects.filter(
                                mmr_module=module_id,mmr_is_deleted=False).values_list('mmr_user',flat=True)
                        if users_list_under_the_login_user:
                            filter = {'employee_id__in': users_list_under_the_login_user}

                        if start_date and end_date:
                            end_date = end_date + 'T23:59:59'
                            start_object = datetime.strptime(start_date, '%Y-%m-%d')
                            end_object = datetime.strptime(end_date, '%Y-%m-%dT%H:%M:%S')
                            filter['created_at__range'] = (start_object, end_object)

                        if date:
                            date = datetime.strptime(date, '%Y-%m-%d')
                            filter['created_at__date']= date

                        if user_project:
                            filter['user_project__in'] = user_project.split(',')

                        # if user_designation:
                        #     filter['employee__mmr_user'] = user_designation

                        if attendance:
                            filter['id'] = attendance

                        if employee:
                            filter['employee'] = employee

                        if approved_status:
                            filter['approved_status'] = approved_status

                        
                        queryset = self.queryset.filter(is_deleted=False, **filter).order_by(sort_field)
                        # print("queryset",queryset.query)
                        return queryset
                        
                    else:
                        users_list_under_the_login_user = list()
                           
                        for a in TCoreUserDetail.objects.raw(
                            'SELECT * FROM t_core_user_details AS tcud'+
                            ' JOIN t_master_module_role_user AS tmmru ON tmmru.mmr_user_id=tcud.cu_user_id'+
                            ' WHERE tmmru.mmr_module_id=%s'+
                            ' AND tcud.reporting_head_id=%s'+' AND tcud.cu_is_deleted=0',[module_id,login_user_details.id]
                            ):
                            users_list_under_the_login_user.append(a.cu_user_id)
                            
                        #print('users_list_under_the_login_user',users_list_under_the_login_user)
                    
                if users_list_under_the_login_user:
                    filter = {'employee_id__in': users_list_under_the_login_user}

                    if start_date and end_date:
                        end_date = end_date+'T23:59:59'
                        start_object = datetime.strptime(start_date, '%Y-%m-%d')
                        end_object = datetime.strptime(end_date, '%Y-%m-%dT%H:%M:%S')
                        filter['created_at__range']=(start_object, end_object)

                    if date:
                        date = datetime.strptime(date, '%Y-%m-%d')
                        filter['created_at__date']= date
                    
                    if user_project:
                        filter['user_project__in']= user_project.split(',')

                    if user_designation:
                        filter['employee__mmr_user']= user_designation

                    if attendance:
                        filter['id'] = attendance

                    if employee:
                        filter['employee'] = employee

                    if month and year:
                        filter['date__date__month'] = month
                        filter['date__date__year'] = year

                    if approved_status:
                        filter['approved_status'] = approved_status

                    queryset = self.queryset.filter(is_deleted=False,**filter).order_by(sort_field)
                    #print('queryset',queryset.query)
                    return queryset
                        
                    
                else:
                    return list()
            else:

                users_list_under_the_login_user = TMasterModuleRoleUser.objects.filter(
                            mmr_module=module_id,mmr_is_deleted=False).values_list('mmr_user',flat=True)
                if users_list_under_the_login_user:
                    filter = {'employee_id__in': users_list_under_the_login_user}

                if start_date and end_date:
                    end_date = end_date + 'T23:59:59'
                    start_object = datetime.strptime(start_date, '%Y-%m-%d')
                    end_object = datetime.strptime(end_date, '%Y-%m-%dT%H:%M:%S')
                    filter['created_at__range'] = (start_object, end_object)

                if date:
                    date = datetime.strptime(date, '%Y-%m-%d')
                    filter['created_at__date']= date

                if user_project:
                    filter['user_project__in'] = user_project.split(',')

                if user_designation:
                    filter['employee__mmr_user'] = user_designation

                if attendance:
                    filter['id'] = attendance

                if employee:
                    filter['employee'] = employee

                if month and year:
                    filter['date__date__month'] = month
                    filter['date__date__year'] = year

                if approved_status:
                    filter['approved_status'] = approved_status

                queryset = self.queryset.filter(is_deleted=False, **filter).order_by(sort_field)
                # print("queryset",queryset.query)
                return queryset
        
        else:
            filter = dict()
            if attendance:
                filter['id'] = attendance
            return self.queryset.filter(is_deleted=False,**filter).order_by(sort_field)
    
    # End For permisson lavel check modified by @Rupam
    
    def list_synchronization(self, list_data: list)-> list:
        data = pd.DataFrame(list_data)
        #data = data.replace(np.nan, 0, regex=True)
        data.sort_values("date", axis = 0, ascending = True, inplace = True,)
        col_list = data.columns.values
        row_list = data.values.tolist()
        total_result = list()
        for row in row_list:
            data_dict = dict(zip(col_list,row))
            total_result.append(data_dict)
        list_data = total_result
        return list_data

    def list(self, request, *args, **kwargs):
        response = super(AttandanceAllDetailsListByPermissonV2View, self).list(request,args,kwargs)
        response.data['request_status'] = 0
        response.data['msg'] = settings.MSG_ERROR

        if response.data['results']:
            day_remarks = None
            for data in response.data['results']:
                date_obj = datetime.strptime(data['date'], "%Y-%m-%dT%H:%M:%S").date()
                for login_logout in data['login_logout_details']:
                    for deviation in login_logout['deviation_details']:
                        leave_day_remarks = calculate_day_remarks(user=data['employee'], date_obj=date_obj,which_module='PMS')
                        if leave_day_remarks:
                            day_remarks = leave_day_remarks
                        elif deviation['approved_status']==1 and deviation['deviation_type'] =='OD':
                            day_remarks = 'OD'
                if day_remarks:
                    data['day_remarks'] = day_remarks
    
                if not data['user_project']:
                    data['user_project'] = {}
            response.data['results'] = self.list_synchronization(list(response.data['results']))
            response.data['request_status'] = 1
            response.data['msg'] = settings.MSG_SUCCESS
        return response

class AttandanceListWithOnlyDeviationByPermissonV2View(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsAttendance.objects.filter(
        is_deleted=False,
        date__gte = str(datetime.now().year-1)+'-04'+'-01',
        date__lte = str(int(datetime.now().year))+'-03'+'-31')
    serializer_class = AttandanceListWithOnlyDeviationByPermissonV2Serializer
    pagination_class = CSPageNumberPagination
    # For permisson lavel check modified by @Rupam
    def get_queryset(self):
        module_id = self.request.GET.get('module_id', None)

        att_ids = PmsAttandanceDeviation.objects.filter(attandance__date__date__gte = str(datetime.now().year-1)+'-04'+'-01',
        attandance__date__date__lte = str(int(datetime.now().year))+'-03'+'-31',approved_status=1).values_list('attandance',flat=True).distinct()

        print("att_ids",att_ids)
        self.queryset = self.queryset.filter(id__in=att_ids)

        print("queryset111",self.queryset)
        sort_field='-id'
        if module_id:
            login_user_details = self.request.user
            print('login_user_details',login_user_details.is_superuser)

            if login_user_details.is_superuser == False:

                '''
                    Added By Rupam Hazra 27.01.2020 from 563-660 for user type = module admin
                '''
                which_type_of_user = TMasterModuleRoleUser.objects.filter(
                    mmr_module_id= module_id,
                    mmr_user=login_user_details,
                    mmr_is_deleted=False
                ).values_list('mmr_type',flat=True)[0]

                if which_type_of_user == 2: #[module admin]
                    queryset = self.queryset
                    if queryset:
                        filter = {}
                        user_project = self.request.query_params.get('user_project', None)
                        employee = self.request.query_params.get('employee', None)
                        user_designation = self.request.query_params.get('user_designation', None)
                        user_first_name = self.request.query_params.get('user_first_name', None)
                        user_last_name = self.request.query_params.get('user_last_name', None)
                        user_name = self.request.query_params.get('user_name', None)
                        start_date = self.request.query_params.get('start_date', None)
                        date = self.request.query_params.get('date', None)
                        end_date = self.request.query_params.get('end_date', None)
                        attendance = self.request.query_params.get('attendance', None)
                        approved_status = self.request.query_params.get('approved_status', None)
                        field_name = self.request.query_params.get('field_name', None)
                        order_by = self.request.query_params.get('order_by', None)

                        if field_name != "" and order_by != "":
                            if field_name == 'sort_first_name' and order_by == 'asc':
                                # queryset = queryset.filter(is_deleted=False).order_by('employee__first_name')
                                # return queryset
                                sort_field='employee__first_name'
                            elif field_name == 'sort_first_name' and order_by == 'desc':
                                # queryset = queryset.filter(is_deleted=False).order_by('-employee__first_name')
                                # return queryset
                                sort_field='-employee__first_name'
                            elif field_name == 'sort_created_at' and order_by == 'asc':
                                # queryset = queryset.filter(is_deleted=False).order_by('created_at')
                                # return queryset
                                sort_field='created_at'
                            elif field_name == 'sort_created_at' and order_by == 'desc':
                                # queryset = queryset.filter(is_deleted=False).order_by('-created_at')
                                # return queryset
                                sort_field='-created_at'
                            elif field_name == 'sort_user_project' and order_by == 'asc':
                                # queryset = queryset.filter(is_deleted=False).order_by('user_project')
                                # return queryset
                                sort_field='user_project'
                            elif field_name == 'sort_user_project' and order_by == 'desc':
                                # queryset = queryset.filter(is_deleted=False).order_by('-user_project')
                                # return queryset
                                sort_field='-user_project'

                        if user_first_name:
                            filter['employee__first_name__icontains'] = user_first_name
                        if user_last_name:
                            filter['employee__last_name__icontains'] = user_last_name

                        if start_date and end_date:
                            end_date = end_date + 'T23:59:59'
                            start_object = datetime.strptime(start_date, '%Y-%m-%d')
                            end_object = datetime.strptime(end_date, '%Y-%m-%dT%H:%M:%S')
                            filter['created_at__range'] = (start_object, end_object)
                        if date:
                            date = datetime.strptime(date, '%Y-%m-%d')
                            filter['created_at__date']= date
                        if user_project:
                            filter['user_project__in'] = user_project.split(',')

                        if user_designation:
                            filter['employee__mmr_user'] = user_designation

                        if attendance:
                            filter['id'] = attendance

                        if employee:
                            filter['employee'] = employee

                        if approved_status:
                            filter['approved_status'] = approved_status

                        if filter:
                            queryset = queryset.filter(is_deleted=False, **filter).order_by(sort_field)
                            # print("queryset",queryset.query)
                            return queryset
                        elif user_name:
                            if '@' in user_name:
                                queryset = queryset.filter(is_deleted=False, employee__email__icontains=user_name).order_by(
                                    sort_field)
                                return queryset
                            else:
                                # print("user_name")
                                name = user_name.split(" ")
                                # print("name", name)
                                if name:
                                    queryset_all = PmsAttendance.objects.none()
                                    # print("len(name)",len(name))
                                    for i in name:
                                        queryset = queryset.filter(
                                            Q(is_deleted=False) & Q(employee__first_name__icontains=i) |
                                            Q(employee__last_name__icontains=i)).order_by(sort_field)
                                        queryset_all = (queryset_all | queryset)
                                    return queryset_all
                        else:
                            queryset = queryset.filter(is_deleted=False).order_by(sort_field)
                            return queryset
                    else:
                        return self.queryset.filter(is_deleted=False).order_by(sort_field)
                else:
                    users_list_under_the_login_user = list()
                    for a in TCoreUserDetail.objects.raw(
                        'SELECT * FROM t_core_user_details AS tcud'+
                        ' JOIN t_master_module_role_user AS tmmru ON tmmru.mmr_user_id=tcud.cu_user_id'+
                        ' WHERE tmmru.mmr_module_id=%s'+
                        ' AND tcud.reporting_head_id=%s'+' AND tcud.cu_is_deleted=0',[module_id,login_user_details.id]
                        ):
                        users_list_under_the_login_user.append(a.cu_user_id)
                    
                    print('users_list_under_the_login_user',users_list_under_the_login_user)
                    if users_list_under_the_login_user:
                        queryset = self.queryset.filter(
                                    employee_id__in=users_list_under_the_login_user,
                                    is_deleted = False
                                    ).order_by(sort_field)
                        print('queryset',queryset)
                        if queryset:
                            filter = {}
                            user_project = self.request.query_params.get('user_project', None)
                            employee = self.request.query_params.get('employee', None)
                            user_designation = self.request.query_params.get('user_designation', None)
                            user_first_name = self.request.query_params.get('user_first_name', None)
                            user_last_name = self.request.query_params.get('user_last_name', None)
                            user_name = self.request.query_params.get('user_name', None)
                            start_date = self.request.query_params.get('start_date', None)
                            end_date = self.request.query_params.get('end_date', None)
                            date = self.request.query_params.get('date', None)
                            attendance = self.request.query_params.get('attendance', None)
                            approved_status = self.request.query_params.get('approved_status', None)
                            field_name=self.request.query_params.get('field_name',None)
                            order_by = self.request.query_params.get('order_by', None)

                            if field_name != "" and order_by != "":
                                if field_name == 'sort_first_name' and order_by == 'asc':
                                    # queryset = queryset.filter(is_deleted=False).order_by('employee__first_name')
                                    # return queryset
                                    sort_field='employee__first_name'
                                elif field_name == 'sort_first_name' and order_by == 'desc':
                                    # queryset = queryset.filter(is_deleted=False).order_by('-employee__first_name')
                                    # return queryset
                                    sort_field='-employee__first_name'
                                elif field_name == 'sort_created_at' and order_by == 'asc':
                                    # queryset =  queryset.filter(is_deleted=False).order_by('created_at')
                                    # return queryset
                                    sort_field='created_at'
                                elif field_name == 'sort_created_at' and order_by == 'desc':
                                    # queryset = queryset.filter(is_deleted=False).order_by('-created_at')
                                    # return queryset
                                    sort_field='-created_at'
                                elif field_name == 'sort_user_project' and order_by == 'asc':
                                    # queryset = queryset.filter(is_deleted=False).order_by('user_project')
                                    # return queryset
                                    sort_field='user_project'
                                elif field_name == 'sort_user_project' and order_by == 'desc':
                                    # queryset = queryset.filter(is_deleted=False).order_by('-user_project')
                                    # return queryset
                                    sort_field='-user_project'
                            if user_first_name:
                                filter['employee__first_name__icontains'] = user_first_name
                            if user_last_name:
                                filter['employee__last_name__icontains'] = user_last_name
                            if start_date and end_date:
                                end_date = end_date+'T23:59:59'
                                start_object = datetime.strptime(start_date, '%Y-%m-%d')
                                end_object = datetime.strptime(end_date, '%Y-%m-%dT%H:%M:%S')
                                filter['created_at__range']=(start_object, end_object)
                            if date:
                                date = datetime.strptime(date, '%Y-%m-%d')
                                filter['created_at__date']= date
                            if user_project:
                                filter['user_project__in']= user_project.split(',')
                            if user_designation:
                                filter['employee__mmr_user']= user_designation
                            if attendance:
                                filter['id'] = attendance
                            if employee:
                                filter['employee'] = employee
                            if approved_status:
                                filter['approved_status'] = approved_status
                            if filter:
                                queryset = queryset.filter(is_deleted=False,**filter).order_by(sort_field)
                                # print("queryset",queryset.query)
                                return queryset
                            elif user_name:
                                if '@' in user_name:
                                    queryset = queryset.filter(is_deleted=False, employee__email__icontains=user_name).order_by(sort_field)
                                    return queryset
                                else:
                                    #print("user_name")
                                    name = user_name.split(" ")
                                    #print("name", name)
                                    if name:
                                        queryset_all = PmsAttendance.objects.none()
                                        #print("len(name)",len(name))
                                        for i in name:
                                            queryset = queryset.filter(Q(is_deleted=False) & Q(employee__first_name__icontains=i) |
                                                                            Q(employee__last_name__icontains=i)).order_by(sort_field)
                                            queryset_all = (queryset_all|queryset)
                                        return queryset_all
                            else:
                                queryset = queryset.filter(is_deleted=False).order_by(sort_field)
                                return queryset
                        else:
                            return queryset
                    else:
                        return list()  
            else:
                #+++++++++++++
                queryset = self.queryset
                if queryset:
                    filter = {}
                    user_project = self.request.query_params.get('user_project', None)
                    employee = self.request.query_params.get('employee', None)
                    user_designation = self.request.query_params.get('user_designation', None)
                    user_first_name = self.request.query_params.get('user_first_name', None)
                    user_last_name = self.request.query_params.get('user_last_name', None)
                    user_name = self.request.query_params.get('user_name', None)
                    start_date = self.request.query_params.get('start_date', None)
                    end_date = self.request.query_params.get('end_date', None)
                    date = self.request.query_params.get('date', None)
                    attendance = self.request.query_params.get('attendance', None)
                    approved_status = self.request.query_params.get('approved_status', None)
                    field_name = self.request.query_params.get('field_name', None)
                    order_by = self.request.query_params.get('order_by', None)

                    if field_name != "" and order_by != "":
                        if field_name == 'sort_first_name' and order_by == 'asc':
                            sort_field='employee__first_name'
                            # queryset = queryset.filter(is_deleted=False).order_by('employee__first_name')
                            # return queryset
                        elif field_name == 'sort_first_name' and order_by == 'desc':
                            # queryset = queryset.filter(is_deleted=False).order_by('-employee__first_name')
                            # return queryset
                            sort_field='-employee__first_name'
                        elif field_name == 'sort_created_at' and order_by == 'asc':
                            # queryset = queryset.filter(is_deleted=False).order_by('created_at')
                            # return queryset
                            sort_field='created_at'
                        elif field_name == 'sort_created_at' and order_by == 'desc':
                            # queryset = queryset.filter(is_deleted=False).order_by('-created_at')
                            # return queryset
                            sort_field='-created_at'
                        elif field_name == 'sort_user_project' and order_by == 'asc':
                            # queryset = queryset.filter(is_deleted=False).order_by('user_project')
                            # return queryset
                            sort_field='user_project'
                        elif field_name == 'sort_user_project' and order_by == 'desc':
                            # queryset = queryset.filter(is_deleted=False).order_by('-user_project')
                            # return queryset
                            sort_field='-user_project'

                    if user_first_name:
                        filter['employee__first_name__icontains'] = user_first_name
                    if user_last_name:
                        filter['employee__last_name__icontains'] = user_last_name

                    if start_date and end_date:
                        end_date = end_date + 'T23:59:59'
                        start_object = datetime.strptime(start_date, '%Y-%m-%d')
                        end_object = datetime.strptime(end_date, '%Y-%m-%dT%H:%M:%S')
                        filter['created_at__range'] = (start_object, end_object)

                    if date:
                        date = datetime.strptime(date, '%Y-%m-%d')
                        filter['created_at__date']= date
                    if user_project:
                        filter['user_project__in'] = user_project.split(',')

                    if user_designation:
                        filter['employee__mmr_user'] = user_designation

                    if attendance:
                        filter['id'] = attendance

                    if employee:
                        filter['employee'] = employee

                    if approved_status:
                        filter['approved_status'] = approved_status

                    if filter:
                        queryset = queryset.filter(is_deleted=False, **filter).order_by(sort_field)
                        # print("queryset",queryset.query)
                        return queryset
                    elif user_name:
                        if '@' in user_name:
                            queryset = queryset.filter(is_deleted=False, employee__email__icontains=user_name).order_by(
                                sort_field)
                            return queryset
                        else:
                            # print("user_name")
                            name = user_name.split(" ")
                            # print("name", name)
                            if name:
                                queryset_all = PmsAttendance.objects.none()
                                # print("len(name)",len(name))
                                for i in name:
                                    queryset = queryset.filter(
                                        Q(is_deleted=False) & Q(employee__first_name__icontains=i) |
                                        Q(employee__last_name__icontains=i)).order_by(sort_field)
                                    queryset_all = (queryset_all | queryset)
                                return queryset_all
                    else:
                        queryset = queryset.filter(is_deleted=False).order_by(sort_field)
                        return queryset
                else:
                    return self.queryset.filter(is_deleted=False).order_by(sort_field)

                #+++++++++++++
        else:
            return self.queryset.filter(is_deleted=False).order_by(sort_field)
    
    # End For permisson lavel check modified by @Rupam
    
    def list_synchronization(self, list_data: list)-> list:
        data = pd.DataFrame(list_data)
        data = data.replace(np.nan, 0, regex=True)
        #data.sort_values("date", axis = 0, ascending = True, inplace = True,)
        col_list = data.columns.values
        row_list = data.values.tolist()
        total_result = list()
        for row in row_list:
            data_dict = dict(zip(col_list,row))
            # print("data_dict",data_dict['deviation_details'])
            if len(data_dict['login_logout_details'])>0:
                total_result.append(data_dict)
        list_data = total_result
        return list_data
    @response_modify_decorator_list_or_get_after_execution_for_pagination
    def list(self, request, *args, **kwargs):
        response = super(AttandanceListWithOnlyDeviationByPermissonV2View, self).list(request,args,kwargs)
        if response.data['results']:
            for data in response.data['results']:
                if not data['user_project']:
                    data['user_project'] = {}
            response.data['results'] = self.list_synchronization(list(response.data['results']))
        return response

class PmsFlexiTeamFortnightAttendance(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    # pagination_class = CSPageNumberPagination
    queryset = PmsAttendance.objects.filter(is_deleted=False)
    serializer_class = AttendanceListV2Serializer
    filter_backends = (filters.OrderingFilter, filters.SearchFilter,)
    search_fields = ('date', 'employee', 'employee__username', 'login_time', 'logout_time', 'type')
    ordering = ('-created_at',)

    def get_queryset(self):
        emp_id = self.emp_id
        f_start_date = self.f_start_date
        f_end_date = self.f_end_date
        filter = {}
        if self.queryset.count():
            filter['employee']=emp_id
            filter['date__date__gte'] = f_start_date
            filter['date__date__lte'] = f_end_date
        queryset = self.queryset.filter(**filter)
        return queryset

    def attendance_list(self, request, *args, **kwargs):
        current_date = datetime.now().date()
        #print('current_date',current_date)
        year = int(self.request.query_params['year']) if 'year' in self.request.query_params else int(current_date.strftime("%Y"))
        month = int(self.request.query_params['month']) if 'month' in self.request.query_params else int(current_date.strftime("%m"))
        
        response = super(__class__, self).list(request, args, kwargs)
        results_data_listofdict = response.data
        #print("results_data_listofdict, ", results_data_listofdict)
        month_date_list = self.get_month_dates(year, month)
        #absent_date_list = []
        present_date_list = [oddata['date'][0:10] for oddata in results_data_listofdict]
        #print("present_date_list>>>>>", present_date_list)

        for od in results_data_listofdict:
            queryset_att_log = PmsAttandanceLog.objects.filter(attandance=od['id'],login_logout_check__in=('Logout',))
            login_logout_list = list()
            #print('queryset_att_log',queryset_att_log.query,queryset_att_log)
            if queryset_att_log:
                for e_queryset_att_log in queryset_att_log:
                    
                    login_logout_dict=dict()
                    #login_logout_dict['day_remarks'] = "Present"
                    login_logout_dict['login_time'] = PmsAttandanceLog.objects.filter(
                        attandance=od['id'],id=e_queryset_att_log.login_id).values_list('time',flat=True).first()
                    login_logout_dict['logout_time'] = e_queryset_att_log.time
                    login_logout_list.append(login_logout_dict)

                    deviation_details = PmsAttandanceDeviation.objects.filter(
                        attandance=od['id'],
                        from_time__gte=login_logout_dict['login_time'],
                        to_time__lte=login_logout_dict['logout_time']
                        )
                    #print('deviation_details',deviation_details.query)
                    total_deviation_time = timedelta(hours=00, minutes=00, seconds=00)
                    deviation_list=[]
                    if deviation_details:                   
                        for deviation in deviation_details:
                            if deviation.deviation_time:
                                deviation_time = datetime.strptime(deviation.deviation_time,'%H:%M:%S').time()
                                deviation_time_timedelta= timedelta(hours=deviation_time.hour, minutes=deviation_time.minute, seconds=deviation_time.second)
                                total_deviation_time = total_deviation_time + deviation_time_timedelta

                            justified_by=deviation.justified_by.id if deviation.justified_by else None
                            justified_by_name=userdetails(justified_by)  
                            approved_by=deviation.approved_by.id if deviation.approved_by else None
                            approved_by_name=userdetails(approved_by)
                            #deviation_time = datetime.strptime(deviation.deviation_time,'%H:%M:%S').hour
                            #print('deviation_time',deviation_time)
                            deviation_time = datetime.strptime(deviation.deviation_time,"%H:%M:%S")
                            total_seconds = deviation_time.second + deviation_time.minute*60 + deviation_time.hour*3600

                            deviation_time = round((total_seconds)/60)
                            deviation_dict={
                                'id':deviation.id,
                                'from_time':deviation.from_time,
                                'to_time':deviation.to_time,
                                'deviation_time': deviation_time,
                                'duration':deviation.duration,
                                'deviation_type':deviation.deviation_type,
                                'deviation_type_name':deviation.get_deviation_type_display(),
                                'justification':deviation.justification,
                                'approved_status':deviation.approved_status,
                                'approved_status_name':deviation.get_approved_status_display(),
                                'remarks':deviation.remarks,
                                'justified_by':justified_by,
                                'justified_by_name':justified_by_name,
                                'justified_at':deviation.justified_at,
                                'approved_by':approved_by,
                                'approved_by_name':approved_by_name,
                                'approved_at':deviation.approved_at,
                                'lock_status':deviation.lock_status,
                                'leave_type_changed_period':deviation.leave_type_changed_period,
                                'leave_type_changed':deviation.leave_type_changed,
                                'request_date':deviation.request_date,
                                'is_requested':deviation.is_requested,
                                'leave_type':deviation.leave_type
                            }
                            deviation_list.append(deviation_dict)

                    total_time = timedelta(hours=00, minutes=00, seconds=00)
                    login_time = login_logout_dict['login_time']
                    logout_time = login_logout_dict['logout_time']
                    if deviation_details:
                        login_logout_dict['is_deviation'] = 1
                        login_time_timedelta = timedelta(hours=login_time.hour, minutes=login_time.minute,
                                                    seconds=login_time.second)
                        logout_time_timedelta = timedelta(hours=logout_time.hour, minutes=logout_time.minute,
                                                        seconds=logout_time.second)
                        
                    else:
                        login_logout_dict['is_deviation'] = 0
            
                    login_logout_dict['deviation_details'] = deviation_list

            
            week_day = datetime.strptime(od['date'], '%Y-%m-%dT%H:%M:%S').strftime('%A')
            #print('week_day',week_day)
            od['date'] = datetime.strptime(od['date'], '%Y-%m-%dT%H:%M:%S').strftime('%Y-%m-%d')
            od['week_day'] = week_day
            od['present'] = od['is_present']
            od['holiday'] = 0
            od['login_logout_details'] = login_logout_list
    
        response_data_dict = collections.OrderedDict()
        response_data_dict['count'] = len(results_data_listofdict)
        response_data_dict['results'] = results_data_listofdict
        response_data_dict['request_status'] = 1
        response_data_dict['msg'] = settings.MSG_SUCCESS
        # print(response_data_dict)
        return self.list_synchronization(response_data_dict)

    @response_modify_decorator_list_after_execution
    def get(self, request, *args, **kwargs):
        
        setattr(self, 'emp_id', None)
        setattr(self, 'f_start_date', None)
        setattr(self, 'f_end_date', None)

        employee_id = self.request.query_params.get('employee_id', None)
        month = self.request.query_params.get('month', None)
        year = self.request.query_params.get('year', None)


        data_list = list()

        tcore_users = TCoreUserDetail.objects.filter(cu_user__in = (TMasterModuleRoleUser.objects.filter(
            mmr_module__cm_name='PMS',mmr_is_deleted=False).values_list('mmr_user',flat=True)),
            attendance_type='PMS',termination_date__isnull=True,cu_is_deleted=False)
        if employee_id:
            tcore_users = tcore_users.filter(cu_user=employee_id)

        for tuser in tcore_users:
            attendance_month_master = AttendenceMonthMaster.objects.filter(month=month,month_end__year=year, is_deleted=False)

            #print(attendance_month_master)
            #print(tuser)
            for month_master in attendance_month_master:
                #print(tuser.cu_user.get_full_name())
                self.emp_id = tuser.cu_user.id
                first_flexi = dict()
                first_flexi['employee_name'] = tuser.cu_user.get_full_name()
                first_flexi['start_date'] = month_master.month_start.date()
                first_flexi['end_date'] = month_master.fortnight_date.date()

                total_hrs_mins, working_hrs_mins, deficit_hrs_mins, leave_deduction, in_number = self.get_pms_total_working_deficit_hrs_mins(tcore_user=tuser, start_date=month_master.month_start, end_date=month_master.fortnight_date)
                first_flexi['total_hour'] = total_hrs_mins
                first_flexi['working_hour'] = working_hrs_mins
                first_flexi['time_deficit'] = deficit_hrs_mins
                first_flexi['leave_deduction'] = leave_deduction

                self.f_start_date = month_master.month_start.date()
                self.f_end_date = month_master.fortnight_date.date()
                response = self.attendance_list(request, *args, **kwargs)
                # print(response)
                first_flexi['fortnight'] = response
                data_list.append(first_flexi)

                second_flexi = dict()
                second_flexi['employee_name'] = tuser.cu_user.get_full_name()
                second_flexi['start_date'] = (month_master.fortnight_date + timedelta(days=1)).date()
                second_flexi['end_date'] = month_master.month_end.date()

                total_hrs_mins, working_hrs_mins, deficit_hrs_mins, leave_deduction, in_number = self.get_pms_total_working_deficit_hrs_mins(tcore_user=tuser, start_date=month_master.fortnight_date + timedelta(days=1), end_date=month_master.month_end)
                second_flexi['total_hour'] = total_hrs_mins
                second_flexi['working_hour'] = working_hrs_mins
                second_flexi['time_deficit'] = deficit_hrs_mins
                second_flexi['leave_deduction'] = leave_deduction

                self.f_start_date = (month_master.fortnight_date + timedelta(days=1)).date()
                self.f_end_date = month_master.month_end.date()
                response = self.attendance_list(request, *args, **kwargs)
                second_flexi['fortnight'] = response
                data_list.append(second_flexi)
        
        return Response(data_list)

    def list_synchronization(self, list_data: list)-> list:
        data = pd.DataFrame(list_data["results"])
        #print('data',data)
        data = data.replace(np.nan, 0, regex=True)
        total_result = list()
        if len(data):
            data.sort_values("date", axis = 0, ascending = True, inplace = True,)
            col_list = data.columns.values
            row_list = data.values.tolist()
            for row in row_list:
                data_dict = dict(zip(col_list,row))
                total_result.append(data_dict)
        list_data["results"] = total_result
        return list_data

    def get_month_dates(self, year, month)-> list:
        date_list = []
        cal = calendar.Calendar()
        for cal_date in cal.itermonthdates(year, month):
            if cal_date.month == month:
                cal_d = cal_date.strftime('%Y-%m-%d')

                date_list.append(cal_d)
        return date_list

    def get_pms_total_working_deficit_hrs_mins(self, tcore_user=None, start_date=None, end_date=None):
        total_hours, working_hours = get_pms_flexi_hours_for_work_days(tcore_user=tcore_user, start_date=start_date, end_date=end_date)
        print("total_hours, working_hours",total_hours, working_hours)

        total_hrs, total_mins = divmod(int(total_hours), 60)
        total_hrs_mins = '{} hrs {} mins'.format(total_hrs, total_mins) if total_hrs else '{} mins'.format(total_mins)
        print("total_hrs_mins",total_hrs_mins)

        working_hrs, working_mins = divmod(int(working_hours), 60)
        working_hrs_mins = '{} hrs {} mins'.format(working_hrs, working_mins) if working_hrs else '{} mins'.format(working_mins)

        time_deficit = total_hours - working_hours
        deficit_hours = time_deficit if time_deficit >= 0.0 else 0.0
        deficit_hrs, deficit_mins = divmod(int(deficit_hours), 60)
        deficit_hrs_mins = '{} hrs {} mins'.format(deficit_hrs, deficit_mins) if deficit_hrs else '{} mins'.format(deficit_mins)
        
        leave_deduction = 0
        if deficit_hours:
            leave_deduction = get_fortnight_leave_deduction(hour=int(deficit_hours)/60)
        in_number = dict(total_hour=total_hours,working_hour=working_hours,time_deficit=deficit_hours,leave_deduction=leave_deduction)
        return total_hrs_mins, working_hrs_mins, deficit_hrs_mins, leave_deduction, in_number



#::::::::::::::::::::: END NEW ATTENDANCE SYTEM :::::::::::::::#

#:::::::::::: ATTENDENCE ::::::::::::::::::::::::::::#
class AttendanceLoginView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsAttendance.objects.all()
    serializer_class = PmsAttendanceAddSerializer

    def post(self, request, *args, **kwargs):
        response = super(AttendanceLoginView, self).post(request,args,kwargs)
        try:
            response.data['msg'] = settings.MSG_SUCCESS
            response.data['request_status'] = 1
        except Exception as e:
            response.data['msg'] = settings.MSG_ERROR
            response.data['request_status'] = 0

        return response



class AttendanceAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsAttendance.objects.all()
    serializer_class = AttendanceAddSerializer

    def post(self, request, *args,**kwargs):
        # print("request",request.user.email)
        # response = super(AttendanceAddView, self).post(request, args, kwargs)
        login_date =datetime.strptime(request.data['login_time'],'%Y-%m-%dT%H:%M:%S').date()
        # print("login_date",login_date)
        attandance_data = custom_filter(
                self,
                PmsAttendance,
                filter_columns={"login_time__date": login_date, "employee__username":request.user.username}, #modified by Rupam
                fetch_columns=['id', 'type', 'employee', 'user_project', 'date', 'login_time', 'login_latitude', 'login_longitude',
                  'login_address','logout_time', 'logout_latitude', 'logout_longitude', 'logout_address', 'approved_status',
                  'justification','created_by', 'owned_by'],
                single_row=True
                          )
        #print("req",request.user)
        # print("login_time_data",attandance_data)

        project_user_mapping = PmsProjectUserMapping.objects.filter(user=request.user, status=True).order_by('-id').values('project')
        print("project_user_mapping",project_user_mapping)
        if project_user_mapping:
            project = project_user_mapping[0]['project']
            request.data['user_project_id'] = project
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
            
        if attandance_data:

            # print("attandance_data",attandance_data)
            if attandance_data:
                if attandance_data['logout_time'] is None:
                    # print("attandance_data",attandance_data['logout_time'])
                    return Response({'result':attandance_data,
                                     'request_status': 1,
                                     'msg': settings.MSG_SUCCESS
                                     })
                else:
                    return Response({'request_status': 0,
                                     'msg': "You are not able to login for today"
                                     })
        else:

            attendance_add, created = PmsAttendance.objects.get_or_create(employee=request.user,created_by=request.user,
                                                                          owned_by=request.user,**request.data)
            # print("attendance_add",attendance_add.__dict__)
            attendance_add.__dict__.pop('_state') if "_state" in attendance_add.__dict__.keys() else attendance_add.__dict__
            attendance_add.__dict__['user_project_details'] = multi_lat_long
            attendance_add.__dict__['geo_fencing_area'] = geofence

            return Response({'result':attendance_add.__dict__,
                             'request_status': 1,
                             'msg': settings.MSG_SUCCESS
                             })

class AttendanceListByEmployeeView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    # pagination_class = CSPageNumberPagination
    queryset = PmsAttendance.objects.filter(is_deleted=False)
    serializer_class = AttendanceListSerializer
    filter_backends = (filters.OrderingFilter, filters.SearchFilter,)
    search_fields = ('date', 'employee', 'employee__username', 'login_time', 'logout_time', 'type')
    ordering = ('-created_at',)

    def get_queryset(self):
        employee_id = self.kwargs["employee_id"]
        year = int(self.request.query_params['year']) if 'year' in self.request.query_params else int(
            datetime.now().date().strftime("%Y"))
        month = int(self.request.query_params['month']) if 'month' in self.request.query_params else int(
            datetime.now().date().strftime("%m"))
        return self.queryset.filter(employee_id= employee_id, created_at__year = year, created_at__month=month,is_deleted=False)

    def get_holidays_list(self):
        holidays_list = HolidaysList.objects.filter(status=True)
        holidays_dict = {}
        for data in holidays_list:
            dt_str = data.holiday_date.strftime('%Y-%m-%d')
            holidays_dict[dt_str] = data.holiday_name
        return holidays_dict

    def list(self, request, *args, **kwargs):
        try:
            holidays_dict = self.get_holidays_list()
            # print("holidays_dict: ", holidays_dict)
            current_date = datetime.now().date()
            print('current_date',current_date)
            year = int(self.request.query_params['year']) if 'year' in self.request.query_params else int(current_date.strftime("%Y"))
            month = int(self.request.query_params['month']) if 'month' in self.request.query_params else int(current_date.strftime("%m"))
          
            response = super(AttendanceListByEmployeeView, self).list(request, args, kwargs)
            results_data_listofdict = response.data
            print("results_data_listofdict, ", results_data_listofdict)
            month_date_list = self.get_month_dates(year, month)
            absent_date_list = []
            present_date_list = [oddata['date'][0:10] for oddata in results_data_listofdict]
            print("present_date_list>>>>>", present_date_list)

            for date in month_date_list:
                if date not in present_date_list:
                    # print("date.....>>>",date)
                    present_date = datetime.strptime(date, '%Y-%m-%d').date()
                    rest_day = current_date - present_date
                    if rest_day.days >= 0:
                        absent_date_list.append(date)

            for od in results_data_listofdict:
                # print("od['id']",od['id'])
                deviation_details = PmsAttandanceDeviation.objects.filter(attandance=od['id'])
                # print("deviation",deviation_details)      
                login_time = PmsAttendance.objects.only('login_time').get(id=od['id']).login_time
                logout_time = PmsAttendance.objects.only('logout_time').get(id=od['id']).logout_time
                total_time = timedelta(hours=00, minutes=00, seconds=00)

                if login_time and logout_time:
                    login_time_timedelta = timedelta(hours=login_time.hour, minutes=login_time.minute,
                                                     seconds=login_time.second)
                    logout_time_timedelta = timedelta(hours=logout_time.hour, minutes=logout_time.minute,
                                                      seconds=logout_time.second)
                    total_time = logout_time_timedelta - login_time_timedelta
                # print("total_time", total_time)

                total_deviation_time = timedelta(hours=00, minutes=00, seconds=00)

                deviation_list=[]
                if deviation_details:                   
                    for deviation in deviation_details:
                        if deviation.deviation_time:
                            deviation_time = datetime.strptime(deviation.deviation_time,'%H:%M:%S').time()
                            deviation_time_timedelta= timedelta(hours=deviation_time.hour, minutes=deviation_time.minute, seconds=deviation_time.second)
                            total_deviation_time = total_deviation_time + deviation_time_timedelta
                        justified_by=deviation.justified_by.id if deviation.justified_by else None
                        justified_by_name=userdetails(justified_by)  
                        approved_by=deviation.approved_by.id if deviation.approved_by else None
                        approved_by_name=userdetails(approved_by)
                        deviation_dict={
                            'id':deviation.id,
                            'from_time':deviation.from_time,
                            'to_time':deviation.to_time,
                            'deviation_time':deviation.deviation_time,
                            'duration':deviation.duration,
                            'deviation_type':deviation.deviation_type,
                            'deviation_type_name':deviation.get_deviation_type_display(),
                            'justification':deviation.justification,
                            'approved_status':deviation.approved_status,
                            'approved_status_name':deviation.get_approved_status_display(),
                            'remarks':deviation.remarks,
                            'justified_by':justified_by,
                            'justified_by_name':justified_by_name,
                            'justified_at':deviation.justified_at,
                            'approved_by':approved_by,
                            'approved_by_name':approved_by_name,
                            'approved_at':deviation.approved_at,
                            'lock_status':deviation.lock_status,
                            'leave_type_changed_period':deviation.leave_type_changed_period,
                            'leave_type_changed':deviation.leave_type_changed,
                            'request_date':deviation.request_date,
                            'is_requested':deviation.is_requested,
                            'leave_type':deviation.leave_type
                        }
                        deviation_list.append(deviation_dict)
                    # print("total_deviation_time",str(total_deviation_time))
                    od['is_deviation'] = 1
                    od['deviation_details'] =deviation_list
                else:
                    od['is_deviation'] = 0
                    od['deviation_details'] =deviation_list
                working_time = total_time - total_deviation_time
                # print("working_time", str(working_time))
                # print("working_time", working_time.seconds)
                if working_time.seconds > 36000:
                    od['is_ten_hrs'] = 1
                else:
                    od['is_ten_hrs'] = 0

                print('date',od['date'])
                week_day = datetime.strptime(od['date'], '%Y-%m-%dT%H:%M:%S').strftime('%A')
                print('week_day',week_day)
                od['date'] = datetime.strptime(od['date'], '%Y-%m-%dT%H:%M:%S').strftime('%Y-%m-%d')
                od['week_day'] = week_day
                od['present'] = 1
                od['is_present'] = od['present']
                od['holiday'] = 0

            for absent_date in absent_date_list:
                ab_week_day = datetime.strptime(absent_date, '%Y-%m-%d').strftime('%A')
                data_dict = {
                    "type": 1,
                    "employee": self.kwargs["employee_id"],
                    "user_project": "",
                    "date": absent_date,
                    "login_time": "",
                    "logout_time": "",
                    "approved_status": 0,
                    "justification": "Auto genareted absent",
                    "day_remarks":"Auto genareted absent",
                    "week_day": ab_week_day,
                    "present": 0,
                    "is_presnt":False,
                    "holiday": 0,
                    "deviation_details":[]
                }
                if absent_date in holidays_dict.keys():
                    data_dict["holiday"] = 1
                    data_dict["justification"] = holidays_dict[absent_date]
                    data_dict['day_remarks'] = holidays_dict[absent_date]



                results_data_listofdict.append(data_dict)

            response_data_dict = collections.OrderedDict()
            response_data_dict['count'] = len(results_data_listofdict)
            response_data_dict['results'] = results_data_listofdict
            response_data_dict['request_status'] = 1
            response_data_dict['msg'] = settings.MSG_SUCCESS
            # print(response_data_dict)
            return Response(self.list_synchronization(response_data_dict))
        except Exception as e:
            raise e
            # raise APIException({'request_status': 0, 'msg': e})

    def list_synchronization(self, list_data: list)-> list:
        data = pd.DataFrame(list_data["results"])
        data = data.replace(np.nan, 0, regex=True)
        data.sort_values("date", axis = 0, ascending = True, inplace = True,)
        col_list = data.columns.values
        row_list = data.values.tolist()
        total_result = list()
        for row in row_list:
            data_dict = dict(zip(col_list,row))
            total_result.append(data_dict)
        list_data["results"] = total_result
        return list_data


    def get_month_dates(self, year, month)-> list:
        date_list = []
        cal = calendar.Calendar()
        for cal_date in cal.itermonthdates(year, month):
            if cal_date.month == month:
                cal_d = cal_date.strftime('%Y-%m-%d')

                date_list.append(cal_d)
        return date_list

class AttendanceSummaryByEmployeeView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    # pagination_class = CSPageNumberPagination
    queryset = PmsAttendance.objects.filter(is_deleted=False)
    serializer_class = AttendanceListSerializer
    filter_backends = (filters.OrderingFilter, filters.SearchFilter,)
    search_fields = ('date', 'employee', 'employee__username', 'login_time', 'logout_time', 'type')
    ordering = ('-created_at',)

    def get_queryset(self):
        employee_id = self.kwargs["employee_id"]
        year = int(self.request.query_params['year']) if 'year' in self.request.query_params else int(
            datetime.now().date().strftime("%Y"))
        month = int(self.request.query_params['month']) if 'month' in self.request.query_params else int(
            datetime.now().date().strftime("%m"))
        return self.queryset.filter(employee_id= employee_id, created_at__year = year, created_at__month=month,is_deleted=False)

    def get_holidays_list(self,state_id:list()):
        holidays_dict = {}
        if state_id:
            holidays_list = HolidaysList.objects.filter(
                status=True,
                pk__in=HolidayStateMapping.objects.filter(state=state_id).values_list('holiday',flat=True))
            #holidays_dict = {}
            for data in holidays_list:
                dt_str = data.holiday_date.strftime('%Y-%m-%d')
                holidays_dict[dt_str] = data.holiday_name
        return holidays_dict

    def list(self, request, *args, **kwargs):
        try:
            employee_id = self.kwargs["employee_id"]
            holidays_dict = self.get_holidays_list(TCoreUserDetail.objects.filter(
                cu_user_id=employee_id).values_list('job_location_state',flat=True).first())
            # print("holidays_dict: ", holidays_dict)
            current_date = datetime.now().date()
            print('current_date',current_date)
            year = int(self.request.query_params['year']) if 'year' in self.request.query_params else int(current_date.strftime("%Y"))
            month = int(self.request.query_params['month']) if 'month' in self.request.query_params else int(current_date.strftime("%m"))
          
            response = super(AttendanceSummaryByEmployeeView, self).list(request, args, kwargs)
            results_data_listofdict = response.data
            print("results_data_listofdict, ", results_data_listofdict)
            month_date_list = self.get_month_dates(year, month)
            absent_date_list = []
            present_date_list = [oddata['date'][0:10] for oddata in results_data_listofdict]
            print("present_date_list>>>>>", present_date_list)

            for date in month_date_list:
                if date not in present_date_list:
                    # print("date.....>>>",date)
                    present_date = datetime.strptime(date, '%Y-%m-%d').date()
                    rest_day = current_date - present_date
                    if rest_day.days >= 0:
                        absent_date_list.append(date)

            for od in results_data_listofdict:
                # print("od['id']",od['id'])
                deviation_details = PmsAttandanceDeviation.objects.filter(attandance=od['id'])
                # print("deviation",deviation_details)      
                login_time = PmsAttendance.objects.only('login_time').get(id=od['id']).login_time
                logout_time = PmsAttendance.objects.only('logout_time').get(id=od['id']).logout_time
                total_time = timedelta(hours=00, minutes=00, seconds=00)

                if login_time and logout_time:
                    login_time_timedelta = timedelta(hours=login_time.hour, minutes=login_time.minute,
                                                     seconds=login_time.second)
                    logout_time_timedelta = timedelta(hours=logout_time.hour, minutes=logout_time.minute,
                                                      seconds=logout_time.second)
                    total_time = logout_time_timedelta - login_time_timedelta
                # print("total_time", total_time)

                total_deviation_time = timedelta(hours=00, minutes=00, seconds=00)

                deviation_list=[]
                if deviation_details:                   
                    for deviation in deviation_details:
                        if deviation.deviation_time:
                            deviation_time = datetime.strptime(deviation.deviation_time,'%H:%M:%S').time()
                            deviation_time_timedelta= timedelta(hours=deviation_time.hour, minutes=deviation_time.minute, seconds=deviation_time.second)
                            total_deviation_time = total_deviation_time + deviation_time_timedelta
                        justified_by=deviation.justified_by.id if deviation.justified_by else None
                        justified_by_name=userdetails(justified_by)  
                        approved_by=deviation.approved_by.id if deviation.approved_by else None
                        approved_by_name=userdetails(approved_by)
                        deviation_dict={
                            'id':deviation.id,
                            'from_time':deviation.from_time,
                            'to_time':deviation.to_time,
                            'deviation_time':deviation.deviation_time,
                            'duration':deviation.duration,
                            'deviation_type':deviation.deviation_type,
                            'deviation_type_name':deviation.get_deviation_type_display(),
                            'justification':deviation.justification,
                            'approved_status':deviation.approved_status,
                            'approved_status_name':deviation.get_approved_status_display(),
                            'remarks':deviation.remarks,
                            'justified_by':justified_by,
                            'justified_by_name':justified_by_name,
                            'justified_at':deviation.justified_at,
                            'approved_by':approved_by,
                            'approved_by_name':approved_by_name,
                            'approved_at':deviation.approved_at,
                            'lock_status':deviation.lock_status,
                            'leave_type_changed_period':deviation.leave_type_changed_period,
                            'leave_type_changed':deviation.leave_type_changed,
                            'request_date':deviation.request_date,
                            'is_requested':deviation.is_requested,
                            'leave_type':deviation.leave_type
                        }
                        deviation_list.append(deviation_dict)
                    # print("total_deviation_time",str(total_deviation_time))
                    od['is_deviation'] = 1
                    od['deviation_details'] =deviation_list
                else:
                    od['is_deviation'] = 0
                    od['deviation_details'] =deviation_list
                working_time = total_time - total_deviation_time
                # print("working_time", str(working_time))
                # print("working_time", working_time.seconds)
                if working_time.seconds > 36000:
                    od['is_ten_hrs'] = 1
                else:
                    od['is_ten_hrs'] = 0

                print('date',od['date'])
                week_day = datetime.strptime(od['date'], '%Y-%m-%dT%H:%M:%S').strftime('%A')
                print('week_day',week_day)
                od['date'] = datetime.strptime(od['date'], '%Y-%m-%dT%H:%M:%S').strftime('%Y-%m-%d')
                od['week_day'] = week_day
                od['present'] = 1
                od['is_present'] = od['present']
                od['holiday'] = 0
                od['day_remarks'] = 'Present'

            for absent_date in absent_date_list:
                ab_week_day = datetime.strptime(absent_date, '%Y-%m-%d').strftime('%A')
                leave_check_from_advance_leave = get_leave_type_from_type(absent_date)
                data_dict = {
                    "type": 1,
                    "employee": self.kwargs["employee_id"],
                    "user_project": "",
                    "date": absent_date,
                    "login_time": "",
                    "logout_time": "",
                    "approved_status": 0,
                    "justification": "Auto genareted absent",
                    "day_remarks":"Auto genareted absent",
                    "week_day": ab_week_day,
                    "present": 0,
                    "is_present": False,
                    "holiday": 0,
                    "daily_leave_type":"",
                    "daily_leave_period":"",
                    "deviation_details":[]
                }
                if leave_check_from_advance_leave:
                    data_dict['daily_leave_type'] = leave_check_from_advance_leave['leave_type']
                    data_dict['daily_leave_period'] = 1
                    data_dict['approved_status'] = leave_check_from_advance_leave['approved_status']
                    data_dict['day_remarks'] = leave_check_from_advance_leave['leave_type']

                if absent_date in holidays_dict.keys():
                    data_dict["holiday"] = 1
                    data_dict["justification"] = holidays_dict[absent_date]
                    data_dict['day_remarks'] = holidays_dict[absent_date]



                results_data_listofdict.append(data_dict)

            response_data_dict = collections.OrderedDict()
            response_data_dict['count'] = len(results_data_listofdict)
            response_data_dict['results'] = results_data_listofdict
            response_data_dict['request_status'] = 1
            response_data_dict['msg'] = settings.MSG_SUCCESS
            # print(response_data_dict)
            return Response(self.list_synchronization(response_data_dict))
        except Exception as e:
            raise e
            # raise APIException({'request_status': 0, 'msg': e})

    def list_synchronization(self, list_data: list)-> list:
        data = pd.DataFrame(list_data["results"])
        data = data.replace(np.nan, 0, regex=True)
        data.sort_values("date", axis = 0, ascending = True, inplace = True,)
        col_list = data.columns.values
        row_list = data.values.tolist()
        total_result = list()
        for row in row_list:
            data_dict = dict(zip(col_list,row))
            total_result.append(data_dict)
        list_data["results"] = total_result
        return list_data


    def get_month_dates(self, year, month)-> list:
        date_list = []
        cal = calendar.Calendar()
        for cal_date in cal.itermonthdates(year, month):
            if cal_date.month == month:
                cal_d = cal_date.strftime('%Y-%m-%d')

                date_list.append(cal_d)
        return date_list


class AttendanceApprovalList(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    pagination_class = CSPageNumberPagination
    queryset = PmsAttendance.objects.filter(approved_status=1)
    serializer_class = AttendanceApprovalListSerializer

    def get_queryset(self):
        user_name = self.request.query_params.get('user_name', None)

        if user_name:
            if '@' in user_name:
                queryset = self.queryset.filter(is_deleted=False, employee__email__icontains=user_name).order_by('-id')
                return queryset
            else:
                # print("user_name")
                name = user_name.split(" ")
                # print("name", name)
                if name:
                    queryset_all = PmsAttendance.objects.none()
                    # print("len(name)",len(name))
                    for i in name:
                        queryset = self.queryset.filter(Q(is_deleted=False) & Q(approved_status=1) & Q(employee__first_name__icontains=i) |
                                                        Q(employee__last_name__icontains=i)).order_by('-id')
                        queryset_all = (queryset_all|queryset)
                    return queryset_all
        else:
            queryset = self.queryset.filter(is_deleted=False,approved_status=1).order_by('-id')
            return queryset
        
    def list(self, request, *args, **kwargs):
        response = super(AttendanceApprovalList, self).list(request, args, kwargs)
        response.data['request_status'] = 0
        response.data['msg'] = settings.MSG_ERROR
        response.data['per_page_count'] = len(response.data['results'])
        if response.data['results']:
            response.data['request_status'] = 1
            response.data['msg'] = settings.MSG_SUCCESS
        return response
class AttendanceEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsAttendance.objects.filter(is_deleted=False)
    serializer_class = AttendanceSerializer

    def put(self, request,* args, **kwargs):
        response = super(AttendanceEditView, self).put(request, args, kwargs)
        print('request: ', request.data)
        data_dict = {}
        data_dict['result'] = request.data
        if response.data:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_SUCCESS
        # elif len(response.data) == 0:
        #     data_dict['request_status'] = 1
        #     data_dict['msg'] = settings.MSG_NO_DATA
        else:
            data_dict['request_status'] = 0
            data_dict['msg'] = settings.MSG_ERROR

        response.data = data_dict
        return response

class AttendanceLogOutView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsAttendance.objects.filter(is_deleted=False)
    serializer_class = AttendanceLogOutSerializer

    def put(self, request,* args, **kwargs):
        response = super(AttendanceLogOutView, self).put(request, args, kwargs)
        # print('request: ', request.data)
        data_dict = {}
        data_dict['result'] = request.data
        if response.data:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_SUCCESS
        else:
            data_dict['request_status'] = 0
            data_dict['msg'] = settings.MSG_ERROR

        response.data = data_dict
        return response

class AttandanceAllDetailsListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsAttendance.objects.all()
    serializer_class = AttandanceALLDetailsListSerializer
    pagination_class = CSPageNumberPagination

    def get_queryset(self):
        # from django.db.models import Q
        filter = {}
        user_project = self.request.query_params.get('user_project', None)
        employee = self.request.query_params.get('employee', None)
        user_designation = self.request.query_params.get('user_designation', None)

        user_first_name = self.request.query_params.get('user_first_name', None)
        user_last_name = self.request.query_params.get('user_last_name', None)
        user_name = self.request.query_params.get('user_name', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        date = self.request.query_params.get('date', None)
        attendance = self.request.query_params.get('attendance', None)
        approved_status = self.request.query_params.get('approved_status', None)
        field_name=self.request.query_params.get('field_name',None)
        order_by = self.request.query_params.get('order_by', None)

        if field_name != "" and order_by != "":
            if field_name == 'sort_first_name' and order_by == 'asc':
                queryset = self.queryset.filter(is_deleted=False).order_by('employee__first_name')
                return queryset
            elif field_name == 'sort_first_name' and order_by == 'desc':
                queryset = self.queryset.filter(is_deleted=False).order_by('-employee__first_name')
                return queryset
            elif field_name == 'sort_created_at' and order_by == 'asc':
                queryset =  self.queryset.filter(is_deleted=False).order_by('created_at')
                return queryset
            elif field_name == 'sort_created_at' and order_by == 'desc':
                queryset = self.queryset.filter(is_deleted=False).order_by('-created_at')
                return queryset
            elif field_name == 'sort_user_project' and order_by == 'asc':
                queryset = self.queryset.filter(is_deleted=False).order_by('user_project')
                return queryset
            elif field_name == 'sort_user_project' and order_by == 'desc':
                queryset = self.queryset.filter(is_deleted=False).order_by('-user_project')
                return queryset

        if user_first_name:
            filter['employee__first_name__icontains'] = user_first_name
        if user_last_name:
            filter['employee__last_name__icontains'] = user_last_name

        if start_date and end_date:
            start_object = datetime.strptime(start_date, '%Y-%m-%d')
            end_object = datetime.strptime(end_date, '%Y-%m-%d')
            filter['created_at__range']=(start_object, end_object)
        
        if date:
            date = datetime.strptime(date, '%Y-%m-%d')
            filter['created_at__date']= date

        if user_project:
            filter['user_project__in']= user_project.split(',')

        if user_designation:
            filter['employee__mmr_user']= user_designation

        if attendance:
            filter['id'] = attendance

        if employee:
            filter['employee'] = employee

        if approved_status:
            filter['approved_status'] = approved_status

        if filter:
            queryset = self.queryset.filter(is_deleted=False,**filter).order_by('-id')
            print("queryset",queryset.query)
            return queryset
        elif user_name:
            if '@' in user_name:
                queryset = self.queryset.filter(is_deleted=False, employee__email__icontains=user_name).order_by('-id')
                return queryset
            else:
                print("user_name")
                name = user_name.split(" ")
                print("name", name)
                if name:
                    queryset_all = PmsAttendance.objects.none()
                    print("len(name)",len(name))
                    for i in name:
                        queryset = self.queryset.filter(Q(is_deleted=False) & Q(employee__first_name__icontains=i) |
                                                        Q(employee__last_name__icontains=i)).order_by('-id')
                        queryset_all = (queryset_all|queryset)
                    return queryset_all
        else:
            queryset = self.queryset.filter(is_deleted=False).order_by('-id')
            return queryset

    def list_synchronization(self, list_data: list)-> list:
        data = pd.DataFrame(list_data)
        data = data.replace(np.nan, 0, regex=True)
        data.sort_values("date", axis = 0, ascending = True, inplace = True,)
        col_list = data.columns.values
        row_list = data.values.tolist()
        total_result = list()
        for row in row_list:
            data_dict = dict(zip(col_list,row))
            total_result.append(data_dict)
        list_data = total_result
        return list_data

    def list(self, request, *args, **kwargs):
        response = super(AttandanceAllDetailsListView, self).list(request,args,kwargs)
        response.data['request_status'] = 0
        response.data['msg'] = settings.MSG_ERROR

        if response.data['results']:
            for data in response.data['results']:
                if data['user_project']:
                    print("data_id",data['user_project']['site_location']['id'])
                    long_lat_data=PmsSiteProjectSiteManagementMultipleLongLat.objects.filter(project_site=data['user_project']['site_location']['id']).values('latitude','longitude')
                    data['user_project']['long_lat_details']=long_lat_data
                    print("data['user_project']",data['user_project'])
                # if not data['user_project']:
                else:
                    data['user_project'] = {}
            response.data['results'] = self.list_synchronization(list(response.data['results']))
            response.data['request_status'] = 1
            response.data['msg'] = settings.MSG_SUCCESS
        return response

class AttandanceAllDetailsListByPermissonView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    # queryset = PmsAttendance.objects.order_by('-date')
    queryset = PmsAttendance.objects.filter(is_deleted=False)
    serializer_class = AttandanceALLDetailsListByPermissonSerializer
    pagination_class = CSPageNumberPagination

    # For permisson lavel check modified by @Rupam
    def get_queryset(self):
        
        print('sdsddsddd')
        module_id = self.request.GET.get('module_id', None)
        #print('module_id',type(module_id))
        sort_field='-date'
        if module_id:
            login_user_details = self.request.user
            #print('login_user_details',login_user_details.id)
            if login_user_details.is_superuser == False:

                '''
                    Added By Rupam Hazra 27.01.2020 from 563-660 for user type = module admin
                '''
                which_type_of_user = TMasterModuleRoleUser.objects.filter(
                    mmr_module_id= module_id,
                    mmr_user=login_user_details,
                    mmr_is_deleted=False
                ).values_list('mmr_type',flat=True)[0]

                # print('which_type_of_user',which_type_of_user,type(which_type_of_user))
                # time.sleep(10)

                if which_type_of_user == 2: #[module admin]
                    queryset = PmsAttendance.objects.filter(is_deleted=False)
                    if queryset:
                        print('queryset1111...else', queryset)
                        filter = {}
                        user_project = self.request.query_params.get('user_project', None)
                        employee = self.request.query_params.get('employee', None)
                        user_designation = self.request.query_params.get('user_designation', None)
                        user_first_name = self.request.query_params.get('user_first_name', None)
                        user_last_name = self.request.query_params.get('user_last_name', None)
                        user_name = self.request.query_params.get('user_name', None)
                        start_date = self.request.query_params.get('start_date', None)
                        end_date = self.request.query_params.get('end_date', None)
                        date = self.request.query_params.get('date', None)
                        attendance = self.request.query_params.get('attendance', None)
                        approved_status = self.request.query_params.get('approved_status', None)
                        field_name = self.request.query_params.get('field_name', None)
                        order_by = self.request.query_params.get('order_by', None)

                        month = self.request.query_params.get('month', None)
                        year = self.request.query_params.get('year', None)

                        

                        if field_name != "" and order_by != "":
                            if field_name == 'sort_first_name' and order_by == 'asc':
                                sort_field='employee__first_name'
                                # queryset = queryset.filter(is_deleted=False).order_by('employee__first_name')
                                # return queryset
                            elif field_name == 'sort_first_name' and order_by == 'desc':
                                # queryset = queryset.filter(is_deleted=False).order_by('-employee__first_name')
                                # return queryset
                                sort_field='-employee__first_name'
                            elif field_name == 'sort_created_at' and order_by == 'asc':
                                # queryset = queryset.filter(is_deleted=False).order_by('created_at')
                                # return queryset
                                sort_field='created_at'
                            elif field_name == 'sort_created_at' and order_by == 'desc':
                                # queryset = queryset.filter(is_deleted=False).order_by('-created_at')
                                # return queryset
                                sort_field='-created_at'
                            elif field_name == 'sort_user_project' and order_by == 'asc':
                                # queryset = queryset.filter(is_deleted=False).order_by('user_project')
                                # return queryset
                                sort_field='user_project'
                            elif field_name == 'sort_user_project' and order_by == 'desc':
                                # queryset = queryset.filter(is_deleted=False).order_by('-user_project')
                                # return queryset
                                sort_field='-user_project'

                        if user_first_name:
                            filter['employee__first_name__icontains'] = user_first_name
                        if user_last_name:
                            filter['employee__last_name__icontains'] = user_last_name

                        if start_date and end_date:
                            end_date = end_date + 'T23:59:59'
                            start_object = datetime.strptime(start_date, '%Y-%m-%d')
                            end_object = datetime.strptime(end_date, '%Y-%m-%dT%H:%M:%S')
                            filter['created_at__range'] = (start_object, end_object)

                        if date:
                            date = datetime.strptime(date, '%Y-%m-%d')
                            filter['created_at__date']= date

                        if month and year:
                            filter['date__date__month']= month
                            filter['date__date__year']= year

                        if user_project:
                            filter['user_project__in'] = user_project.split(',')

                        if user_designation:
                            filter['employee__mmr_user'] = user_designation

                        if attendance:
                            filter['id'] = attendance

                        if employee:
                            filter['employee'] = employee

                        if approved_status:
                            filter['approved_status'] = approved_status

                        if filter:
                            print("filter",filter)
                            queryset = queryset.filter(is_deleted=False, **filter).order_by(sort_field)
                            print("queryset",queryset.query)
                            return queryset
                        elif user_name:
                            if '@' in user_name:
                                queryset = queryset.filter(is_deleted=False, employee__email__icontains=user_name).order_by(
                                    sort_field)
                                return queryset
                            else:
                                # print("user_name")
                                name = user_name.split(" ")
                                # print("name", name)
                                if name:
                                    queryset_all = PmsAttendance.objects.none()
                                    # print("len(name)",len(name))
                                    for i in name:
                                        queryset = queryset.filter(
                                            Q(is_deleted=False) & Q(employee__first_name__icontains=i) |
                                            Q(employee__last_name__icontains=i)).order_by(sort_field)
                                        queryset_all = (queryset_all | queryset)
                                    return queryset_all
                        else:
                            queryset = queryset.filter(is_deleted=False).order_by(sort_field)
                            return queryset
                else:
                    users_list_under_the_login_user = list()
                    for a in TCoreUserDetail.objects.raw(
                        'SELECT * FROM t_core_user_details AS tcud'+
                        ' JOIN t_master_module_role_user AS tmmru ON tmmru.mmr_user_id=tcud.cu_user_id'+
                        ' WHERE tmmru.mmr_module_id=%s'+
                        ' AND tcud.reporting_head_id=%s'+' AND tcud.cu_is_deleted=0',[module_id,login_user_details.id]
                        ):
                        users_list_under_the_login_user.append(a.cu_user_id)
                    
                    #print('users_list_under_the_login_user',users_list_under_the_login_user)
                    if users_list_under_the_login_user:
                        queryset = PmsAttendance.objects.filter(
                                    employee_id__in=users_list_under_the_login_user,
                                    is_deleted = False
                                    )
                        print('attedence_details',queryset)
                        if queryset:
                            filter = {}
                            user_project = self.request.query_params.get('user_project', None)
                            employee = self.request.query_params.get('employee', None)
                            user_designation = self.request.query_params.get('user_designation', None)
                            user_first_name = self.request.query_params.get('user_first_name', None)
                            user_last_name = self.request.query_params.get('user_last_name', None)
                            user_name = self.request.query_params.get('user_name', None)
                            start_date = self.request.query_params.get('start_date', None)
                            end_date = self.request.query_params.get('end_date', None)
                            date = self.request.query_params.get('date', None)
                            attendance = self.request.query_params.get('attendance', None)
                            approved_status = self.request.query_params.get('approved_status', None)
                            field_name=self.request.query_params.get('field_name',None)
                            order_by = self.request.query_params.get('order_by', None)
                            month = self.request.query_params.get('month', None)
                            year = self.request.query_params.get('year', None)

                            if field_name != "" and order_by != "":
                                if field_name == 'sort_first_name' and order_by == 'asc':
                                    queryset = queryset.filter(is_deleted=False).order_by('employee__first_name')
                                    return queryset
                                elif field_name == 'sort_first_name' and order_by == 'desc':
                                    queryset = queryset.filter(is_deleted=False).order_by('-employee__first_name')
                                    return queryset
                                elif field_name == 'sort_created_at' and order_by == 'asc':
                                    queryset = queryset.filter(is_deleted=False).order_by('created_at')
                                    return queryset
                                elif field_name == 'sort_created_at' and order_by == 'desc':
                                    queryset = queryset.filter(is_deleted=False).order_by('-created_at')
                                    return queryset
                                elif field_name == 'sort_user_project' and order_by == 'asc':
                                    queryset = queryset.filter(is_deleted=False).order_by('user_project')
                                    return queryset
                                elif field_name == 'sort_user_project' and order_by == 'desc':
                                    queryset = queryset.filter(is_deleted=False).order_by('-user_project')
                                    return queryset


                            if user_first_name:
                                filter['employee__first_name__icontains'] = user_first_name
                            if user_last_name:
                                filter['employee__last_name__icontains'] = user_last_name

                            if start_date and end_date:
                                end_date = end_date+'T23:59:59'
                                start_object = datetime.strptime(start_date, '%Y-%m-%d')
                                end_object = datetime.strptime(end_date, '%Y-%m-%dT%H:%M:%S')
                                filter['created_at__range']=(start_object, end_object)

                            if date:
                                date = datetime.strptime(date, '%Y-%m-%d')
                                filter['created_at__date']= date

                            if month and year:
                                filter['date__date__month'] = month
                                filter['date__date__year'] = year
                            
                            if user_project:
                                filter['user_project__in']= user_project.split(',')

                            if user_designation:
                                filter['employee__mmr_user']= user_designation

                            if attendance:
                                filter['id'] = attendance

                            if employee:
                                filter['employee'] = employee

                            if approved_status:
                                filter['approved_status'] = approved_status

                            if filter:
                                queryset = queryset.filter(is_deleted=False,**filter).order_by('-date')
                                print("queryset",queryset.query)
                                return queryset
                            elif user_name:
                                if '@' in user_name:
                                    queryset = queryset.filter(is_deleted=False, employee__email__icontains=user_name).order_by('-date')
                                    return queryset
                                else:
                                    #print("user_name")
                                    name = user_name.split(" ")
                                    #print("name", name)
                                    if name:
                                        queryset_all = PmsAttendance.objects.none()
                                        #print("len(name)",len(name))
                                        for i in name:
                                            queryset = queryset.filter(Q(is_deleted=False) & Q(employee__first_name__icontains=i) |
                                                                            Q(employee__last_name__icontains=i)).order_by('-date')
                                            queryset_all = (queryset_all|queryset)
                                        return queryset_all
                            else:
                                queryset = queryset.filter(is_deleted=False).order_by('-date')
                                return queryset
                        else:
                            #print('fgdfggfdgdffggf')
                            return queryset
                    else:
                        return list()
            else:
                queryset = PmsAttendance.objects.filter(is_deleted=False)
                if queryset:
                    print('queryset1111...else', queryset)
                    filter = {}
                    user_project = self.request.query_params.get('user_project', None)
                    employee = self.request.query_params.get('employee', None)
                    user_designation = self.request.query_params.get('user_designation', None)
                    user_first_name = self.request.query_params.get('user_first_name', None)
                    user_last_name = self.request.query_params.get('user_last_name', None)
                    user_name = self.request.query_params.get('user_name', None)
                    start_date = self.request.query_params.get('start_date', None)
                    end_date = self.request.query_params.get('end_date', None)
                    date = self.request.query_params.get('date', None)
                    attendance = self.request.query_params.get('attendance', None)
                    approved_status = self.request.query_params.get('approved_status', None)
                    field_name = self.request.query_params.get('field_name', None)
                    order_by = self.request.query_params.get('order_by', None)


                    if field_name != "" and order_by != "":
                        if field_name == 'sort_first_name' and order_by == 'asc':
                            # queryset = queryset.filter(is_deleted=False).order_by('employee__first_name')
                            # return queryset
                            sort_field='employee__first_name'
                        elif field_name == 'sort_first_name' and order_by == 'desc':
                            # queryset = queryset.filter(is_deleted=False).order_by('-employee__first_name')
                            # return queryset
                            sort_field='-employee__first_name'
                        elif field_name == 'sort_created_at' and order_by == 'asc':
                            # queryset = queryset.filter(is_deleted=False).order_by('created_at')
                            # return queryset
                            sort_field='created_at'
                        elif field_name == 'sort_created_at' and order_by == 'desc':
                            # queryset = queryset.filter(is_deleted=False).order_by('-created_at')
                            # return queryset
                            sort_field='-created_at'
                        elif field_name == 'sort_user_project' and order_by == 'asc':
                            # queryset = queryset.filter(is_deleted=False).order_by('user_project')
                            # return queryset
                            sort_field='user_project'
                        elif field_name == 'sort_user_project' and order_by == 'desc':
                            # queryset = queryset.filter(is_deleted=False).order_by('-user_project')
                            # return queryset
                            sort_field='-user_project'

                    if user_first_name:
                        filter['employee__first_name__icontains'] = user_first_name
                    if user_last_name:
                        filter['employee__last_name__icontains'] = user_last_name

                    if start_date and end_date:
                        end_date = end_date + 'T23:59:59'
                        start_object = datetime.strptime(start_date, '%Y-%m-%d')
                        end_object = datetime.strptime(end_date, '%Y-%m-%dT%H:%M:%S')
                        filter['created_at__range'] = (start_object, end_object)

                    if date:
                        date = datetime.strptime(date, '%Y-%m-%d')
                        filter['created_at__date']= date

                    if user_project:
                        filter['user_project__in'] = user_project.split(',')

                    if user_designation:
                        filter['employee__mmr_user'] = user_designation

                    if attendance:
                        filter['id'] = attendance

                    if employee:
                        filter['employee'] = employee

                    if approved_status:
                        filter['approved_status'] = approved_status

                    if filter:
                        print("filter",filter)
                        queryset = queryset.filter(is_deleted=False, **filter).order_by(sort_field)
                        # print("queryset",queryset.query)
                        return queryset
                    elif user_name:
                        if '@' in user_name:
                            queryset = queryset.filter(is_deleted=False, employee__email__icontains=user_name).order_by(
                                sort_field)
                            return queryset
                        else:
                            # print("user_name")
                            name = user_name.split(" ")
                            # print("name", name)
                            if name:
                                queryset_all = PmsAttendance.objects.none()
                                # print("len(name)",len(name))
                                for i in name:
                                    queryset = queryset.filter(
                                        Q(is_deleted=False) & Q(employee__first_name__icontains=i) |
                                        Q(employee__last_name__icontains=i)).order_by(sort_field)
                                    queryset_all = (queryset_all | queryset)
                                return queryset_all
                    else:
                        queryset = queryset.filter(is_deleted=False).order_by(sort_field)
                        return queryset

        else:
            return self.queryset.filter(is_deleted=False).order_by(sort_field)
    
    # End For permisson lavel check modified by @Rupam
    
    def list_synchronization(self, list_data: list)-> list:
        data = pd.DataFrame(list_data)
        data = data.replace(np.nan, 0, regex=True)
        data.sort_values("date", axis = 0, ascending = False, inplace = True,)
        col_list = data.columns.values
        row_list = data.values.tolist()
        total_result = list()
        for row in row_list:
            data_dict = dict(zip(col_list,row))
            total_result.append(data_dict)
        list_data = total_result
        return list_data

    def list(self, request, *args, **kwargs):
        response = super(AttandanceAllDetailsListByPermissonView, self).list(request,args,kwargs)
        response.data['request_status'] = 0
        response.data['msg'] = settings.MSG_ERROR

        if response.data['results']:
            for data in response.data['results']:
                if not data['user_project']:
                    data['user_project'] = {}
            response.data['results'] = self.list_synchronization(list(response.data['results']))
            response.data['request_status'] = 1
            response.data['msg'] = settings.MSG_SUCCESS
        return response

class AttandanceListWithOnlyDeviationByPermissonView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsAttendance.objects.filter(is_deleted=False)
    serializer_class = AttandanceListWithOnlyDeviationByPermissonSerializer
    pagination_class = CSPageNumberPagination
    # For permisson lavel check modified by @Rupam
    def get_queryset(self):
        module_id = self.request.GET.get('module_id', None)
        self.queryset = self.queryset.filter(is_deleted=False,id__in=PmsAttandanceDeviation.objects.filter(approved_status=4).
                                             values_list('attandance'))
        #print("queryset111",self.queryset)
        sort_field='-id'
        if module_id:
            login_user_details = self.request.user
            print('login_user_details',login_user_details.is_superuser)

            if login_user_details.is_superuser == False:

                '''
                    Added By Rupam Hazra 27.01.2020 from 563-660 for user type = module admin
                '''
                which_type_of_user = TMasterModuleRoleUser.objects.filter(
                    mmr_module_id= module_id,
                    mmr_user=login_user_details,
                    mmr_is_deleted=False
                ).values_list('mmr_type',flat=True)[0]

                if which_type_of_user == 2: #[module admin]
                    queryset = self.queryset
                    if queryset:
                        filter = {}
                        user_project = self.request.query_params.get('user_project', None)
                        employee = self.request.query_params.get('employee', None)
                        user_designation = self.request.query_params.get('user_designation', None)
                        user_first_name = self.request.query_params.get('user_first_name', None)
                        user_last_name = self.request.query_params.get('user_last_name', None)
                        user_name = self.request.query_params.get('user_name', None)
                        start_date = self.request.query_params.get('start_date', None)
                        date = self.request.query_params.get('date', None)
                        end_date = self.request.query_params.get('end_date', None)
                        attendance = self.request.query_params.get('attendance', None)
                        approved_status = self.request.query_params.get('approved_status', None)
                        field_name = self.request.query_params.get('field_name', None)
                        order_by = self.request.query_params.get('order_by', None)

                        if field_name != "" and order_by != "":
                            if field_name == 'sort_first_name' and order_by == 'asc':
                                # queryset = queryset.filter(is_deleted=False).order_by('employee__first_name')
                                # return queryset
                                sort_field='employee__first_name'
                            elif field_name == 'sort_first_name' and order_by == 'desc':
                                # queryset = queryset.filter(is_deleted=False).order_by('-employee__first_name')
                                # return queryset
                                sort_field='-employee__first_name'
                            elif field_name == 'sort_created_at' and order_by == 'asc':
                                # queryset = queryset.filter(is_deleted=False).order_by('created_at')
                                # return queryset
                                sort_field='created_at'
                            elif field_name == 'sort_created_at' and order_by == 'desc':
                                # queryset = queryset.filter(is_deleted=False).order_by('-created_at')
                                # return queryset
                                sort_field='-created_at'
                            elif field_name == 'sort_user_project' and order_by == 'asc':
                                # queryset = queryset.filter(is_deleted=False).order_by('user_project')
                                # return queryset
                                sort_field='user_project'
                            elif field_name == 'sort_user_project' and order_by == 'desc':
                                # queryset = queryset.filter(is_deleted=False).order_by('-user_project')
                                # return queryset
                                sort_field='-user_project'

                        if user_first_name:
                            filter['employee__first_name__icontains'] = user_first_name
                        if user_last_name:
                            filter['employee__last_name__icontains'] = user_last_name

                        if start_date and end_date:
                            end_date = end_date + 'T23:59:59'
                            start_object = datetime.strptime(start_date, '%Y-%m-%d')
                            end_object = datetime.strptime(end_date, '%Y-%m-%dT%H:%M:%S')
                            filter['created_at__range'] = (start_object, end_object)
                        if date:
                            date = datetime.strptime(date, '%Y-%m-%d')
                            filter['created_at__date']= date
                        if user_project:
                            filter['user_project__in'] = user_project.split(',')

                        if user_designation:
                            filter['employee__mmr_user'] = user_designation

                        if attendance:
                            filter['id'] = attendance

                        if employee:
                            filter['employee'] = employee

                        if approved_status:
                            filter['approved_status'] = approved_status

                        if filter:
                            queryset = queryset.filter(is_deleted=False, **filter).order_by(sort_field)
                            # print("queryset",queryset.query)
                            return queryset
                        elif user_name:
                            if '@' in user_name:
                                queryset = queryset.filter(is_deleted=False, employee__email__icontains=user_name).order_by(
                                    sort_field)
                                return queryset
                            else:
                                # print("user_name")
                                name = user_name.split(" ")
                                # print("name", name)
                                if name:
                                    queryset_all = PmsAttendance.objects.none()
                                    # print("len(name)",len(name))
                                    for i in name:
                                        queryset = queryset.filter(
                                            Q(is_deleted=False) & Q(employee__first_name__icontains=i) |
                                            Q(employee__last_name__icontains=i)).order_by(sort_field)
                                        queryset_all = (queryset_all | queryset)
                                    return queryset_all
                        else:
                            queryset = queryset.filter(is_deleted=False).order_by(sort_field)
                            return queryset
                    else:
                        return self.queryset.filter(is_deleted=False).order_by(sort_field)
                else:
                    users_list_under_the_login_user = list()
                    for a in TCoreUserDetail.objects.raw(
                        'SELECT * FROM t_core_user_details AS tcud'+
                        ' JOIN t_master_module_role_user AS tmmru ON tmmru.mmr_user_id=tcud.cu_user_id'+
                        ' WHERE tmmru.mmr_module_id=%s'+
                        ' AND tcud.reporting_head_id=%s'+' AND tcud.cu_is_deleted=0',[module_id,login_user_details.id]
                        ):
                        users_list_under_the_login_user.append(a.cu_user_id)
                    
                    print('users_list_under_the_login_user',users_list_under_the_login_user)
                    if users_list_under_the_login_user:
                        queryset = self.queryset.filter(
                                    employee_id__in=users_list_under_the_login_user,
                                    is_deleted = False
                                    ).order_by(sort_field)
                        print('queryset',queryset)
                        if queryset:
                            filter = {}
                            user_project = self.request.query_params.get('user_project', None)
                            employee = self.request.query_params.get('employee', None)
                            user_designation = self.request.query_params.get('user_designation', None)
                            user_first_name = self.request.query_params.get('user_first_name', None)
                            user_last_name = self.request.query_params.get('user_last_name', None)
                            user_name = self.request.query_params.get('user_name', None)
                            start_date = self.request.query_params.get('start_date', None)
                            end_date = self.request.query_params.get('end_date', None)
                            date = self.request.query_params.get('date', None)
                            attendance = self.request.query_params.get('attendance', None)
                            approved_status = self.request.query_params.get('approved_status', None)
                            field_name=self.request.query_params.get('field_name',None)
                            order_by = self.request.query_params.get('order_by', None)

                            if field_name != "" and order_by != "":
                                if field_name == 'sort_first_name' and order_by == 'asc':
                                    # queryset = queryset.filter(is_deleted=False).order_by('employee__first_name')
                                    # return queryset
                                    sort_field='employee__first_name'
                                elif field_name == 'sort_first_name' and order_by == 'desc':
                                    # queryset = queryset.filter(is_deleted=False).order_by('-employee__first_name')
                                    # return queryset
                                    sort_field='-employee__first_name'
                                elif field_name == 'sort_created_at' and order_by == 'asc':
                                    # queryset =  queryset.filter(is_deleted=False).order_by('created_at')
                                    # return queryset
                                    sort_field='created_at'
                                elif field_name == 'sort_created_at' and order_by == 'desc':
                                    # queryset = queryset.filter(is_deleted=False).order_by('-created_at')
                                    # return queryset
                                    sort_field='-created_at'
                                elif field_name == 'sort_user_project' and order_by == 'asc':
                                    # queryset = queryset.filter(is_deleted=False).order_by('user_project')
                                    # return queryset
                                    sort_field='user_project'
                                elif field_name == 'sort_user_project' and order_by == 'desc':
                                    # queryset = queryset.filter(is_deleted=False).order_by('-user_project')
                                    # return queryset
                                    sort_field='-user_project'
                            if user_first_name:
                                filter['employee__first_name__icontains'] = user_first_name
                            if user_last_name:
                                filter['employee__last_name__icontains'] = user_last_name
                            if start_date and end_date:
                                end_date = end_date+'T23:59:59'
                                start_object = datetime.strptime(start_date, '%Y-%m-%d')
                                end_object = datetime.strptime(end_date, '%Y-%m-%dT%H:%M:%S')
                                filter['created_at__range']=(start_object, end_object)
                            if date:
                                date = datetime.strptime(date, '%Y-%m-%d')
                                filter['created_at__date']= date
                            if user_project:
                                filter['user_project__in']= user_project.split(',')
                            if user_designation:
                                filter['employee__mmr_user']= user_designation
                            if attendance:
                                filter['id'] = attendance
                            if employee:
                                filter['employee'] = employee
                            if approved_status:
                                filter['approved_status'] = approved_status
                            if filter:
                                queryset = queryset.filter(is_deleted=False,**filter).order_by(sort_field)
                                # print("queryset",queryset.query)
                                return queryset
                            elif user_name:
                                if '@' in user_name:
                                    queryset = queryset.filter(is_deleted=False, employee__email__icontains=user_name).order_by(sort_field)
                                    return queryset
                                else:
                                    #print("user_name")
                                    name = user_name.split(" ")
                                    #print("name", name)
                                    if name:
                                        queryset_all = PmsAttendance.objects.none()
                                        #print("len(name)",len(name))
                                        for i in name:
                                            queryset = queryset.filter(Q(is_deleted=False) & Q(employee__first_name__icontains=i) |
                                                                            Q(employee__last_name__icontains=i)).order_by(sort_field)
                                            queryset_all = (queryset_all|queryset)
                                        return queryset_all
                            else:
                                queryset = queryset.filter(is_deleted=False).order_by(sort_field)
                                return queryset
                        else:
                            return queryset
                    else:
                        return list()  
            else:
                #+++++++++++++
                queryset = self.queryset
                if queryset:
                    filter = {}
                    user_project = self.request.query_params.get('user_project', None)
                    employee = self.request.query_params.get('employee', None)
                    user_designation = self.request.query_params.get('user_designation', None)
                    user_first_name = self.request.query_params.get('user_first_name', None)
                    user_last_name = self.request.query_params.get('user_last_name', None)
                    user_name = self.request.query_params.get('user_name', None)
                    start_date = self.request.query_params.get('start_date', None)
                    end_date = self.request.query_params.get('end_date', None)
                    date = self.request.query_params.get('date', None)
                    attendance = self.request.query_params.get('attendance', None)
                    approved_status = self.request.query_params.get('approved_status', None)
                    field_name = self.request.query_params.get('field_name', None)
                    order_by = self.request.query_params.get('order_by', None)

                    if field_name != "" and order_by != "":
                        if field_name == 'sort_first_name' and order_by == 'asc':
                            sort_field='employee__first_name'
                            # queryset = queryset.filter(is_deleted=False).order_by('employee__first_name')
                            # return queryset
                        elif field_name == 'sort_first_name' and order_by == 'desc':
                            # queryset = queryset.filter(is_deleted=False).order_by('-employee__first_name')
                            # return queryset
                            sort_field='-employee__first_name'
                        elif field_name == 'sort_created_at' and order_by == 'asc':
                            # queryset = queryset.filter(is_deleted=False).order_by('created_at')
                            # return queryset
                            sort_field='created_at'
                        elif field_name == 'sort_created_at' and order_by == 'desc':
                            # queryset = queryset.filter(is_deleted=False).order_by('-created_at')
                            # return queryset
                            sort_field='-created_at'
                        elif field_name == 'sort_user_project' and order_by == 'asc':
                            # queryset = queryset.filter(is_deleted=False).order_by('user_project')
                            # return queryset
                            sort_field='user_project'
                        elif field_name == 'sort_user_project' and order_by == 'desc':
                            # queryset = queryset.filter(is_deleted=False).order_by('-user_project')
                            # return queryset
                            sort_field='-user_project'

                    if user_first_name:
                        filter['employee__first_name__icontains'] = user_first_name
                    if user_last_name:
                        filter['employee__last_name__icontains'] = user_last_name

                    if start_date and end_date:
                        end_date = end_date + 'T23:59:59'
                        start_object = datetime.strptime(start_date, '%Y-%m-%d')
                        end_object = datetime.strptime(end_date, '%Y-%m-%dT%H:%M:%S')
                        filter['created_at__range'] = (start_object, end_object)

                    if date:
                        date = datetime.strptime(date, '%Y-%m-%d')
                        filter['created_at__date']= date
                    if user_project:
                        filter['user_project__in'] = user_project.split(',')

                    if user_designation:
                        filter['employee__mmr_user'] = user_designation

                    if attendance:
                        filter['id'] = attendance

                    if employee:
                        filter['employee'] = employee

                    if approved_status:
                        filter['approved_status'] = approved_status

                    if filter:
                        queryset = queryset.filter(is_deleted=False, **filter).order_by(sort_field)
                        # print("queryset",queryset.query)
                        return queryset
                    elif user_name:
                        if '@' in user_name:
                            queryset = queryset.filter(is_deleted=False, employee__email__icontains=user_name).order_by(
                                sort_field)
                            return queryset
                        else:
                            # print("user_name")
                            name = user_name.split(" ")
                            # print("name", name)
                            if name:
                                queryset_all = PmsAttendance.objects.none()
                                # print("len(name)",len(name))
                                for i in name:
                                    queryset = queryset.filter(
                                        Q(is_deleted=False) & Q(employee__first_name__icontains=i) |
                                        Q(employee__last_name__icontains=i)).order_by(sort_field)
                                    queryset_all = (queryset_all | queryset)
                                return queryset_all
                    else:
                        queryset = queryset.filter(is_deleted=False).order_by(sort_field)
                        return queryset
                else:
                    return self.queryset.filter(is_deleted=False).order_by(sort_field)

                #+++++++++++++
        else:
            return self.queryset.filter(is_deleted=False).order_by(sort_field)
    
    # End For permisson lavel check modified by @Rupam
    
    def list_synchronization(self, list_data: list)-> list:
        data = pd.DataFrame(list_data)
        data = data.replace(np.nan, 0, regex=True)
        data.sort_values("date", axis = 0, ascending = True, inplace = True,)
        col_list = data.columns.values
        row_list = data.values.tolist()
        total_result = list()
        for row in row_list:
            data_dict = dict(zip(col_list,row))
            # print("data_dict",data_dict['deviation_details'])
            if len(data_dict['deviation_details'])>0:
                total_result.append(data_dict)
        list_data = total_result
        return list_data
    @response_modify_decorator_list_or_get_after_execution_for_pagination
    def list(self, request, *args, **kwargs):
        response = super(AttandanceListWithOnlyDeviationByPermissonView, self).list(request,args,kwargs)
        if response.data['results']:
            for data in response.data['results']:
                if not data['user_project']:
                    data['user_project'] = {}
            response.data['results'] = self.list_synchronization(list(response.data['results']))
        return response


#:::::::::::: PmsAttandanceLog ::::::::::::::::::::::::::::#
class AttandanceLogAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsAttandanceLog.objects.filter(is_deleted=False)
    serializer_class = AttandanceLogAddSerializer
    # pagination_class=CSPageNumberPagination
    # filter_backends = (DjangoFilterBackend,)
    # filterset_fields = ('attandance',)
    ##results

    def get_queryset(self):
        filter = {}
        attandance = self.request.query_params.get('attandance', None)
        start_time = self.request.query_params.get('start_time', None)
        end_time = self.request.query_params.get('end_time', None)

        if attandance:
            filter['attandance_id']=attandance
        if start_time and end_time:
            start_object = datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S')
            end_object = datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%S')
            filter['time__gte']=start_object
            filter['time__lte']=end_object

        if filter:
            # print("filter", filter)
            return self.queryset.filter(is_deleted=False,**filter)
        else:
            return self.queryset.none()

    # def list(self, request, *args, **kwargs):
    #     response = super(AttandanceLogAddView, self).list(request,args,kwargs)
    #     print("response", response.data)
    #     # response.data['results'] = response.data
    #     return response
    def list(self, request, *args, **kwargs):
        data_dict = {}
        response = super(AttandanceLogAddView, self).list(request, args, kwargs)
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
        response.data = data_dict
        return response

class AttandanceLogMultipleAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsAttandanceLog.objects.filter(is_deleted=False)
    serializer_class = AttandanceLogMultipleAddSerializer

    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        return response
class AttendanceLogEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsAttandanceLog.objects.all()
    serializer_class = AttandanceLogEditSerializer
class AttandanceLogApprovalEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsAttandanceLog.objects.all()
    serializer_class = AttandanceLogApprovalEditSerializer

#:::::::::::: Pms Attandance leave ::::::::::::::::::::::::::::#
# class AdvanceLeaveAddView(generics.ListCreateAPIView):
#     permission_classes = [IsAuthenticated]
#     authentication_classes = [TokenAuthentication]
#     pagination_class = CSPageNumberPagination
#     queryset = PmsEmployeeLeaves.objects.all()
#     serializer_class=AdvanceLeavesAddSerializer

class AdvanceLeaveAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    pagination_class = CSPageNumberPagination
    queryset = PmsEmployeeLeaves.objects.filter(approved_status=1)
    serializer_class=AdvanceLeavesAddSerializer

    def get(self, request, *args, **kwargs):
        response=super(AdvanceLeaveAddView,self).get(request,args,kwargs)
        for data in response.data['results']:
            employee_first_name = User.objects.only('first_name').get(username=data['employee']).first_name
            employee_last_name = User.objects.only('last_name').get(username=data['employee']).last_name
            data['employee_first_name']=employee_first_name
            data['employee_last_name']=employee_last_name
        return response

    def get_queryset(self):
        filter = {}
        user=self.request.user
        print('login_user_details',user.is_superuser)
        print('user',user)
        users_list=(list(TCoreUserDetail.objects.filter(reporting_head=user,cu_is_deleted=False).values_list('cu_user',flat=True)))
        print('users_list',users_list)
        sort_field='-id'
        user_name = self.request.query_params.get('user_name', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        leave_type = self.request.query_params.get('leave_type', None)
        field_name=self.request.query_params.get('field_name',None)
        order_by = self.request.query_params.get('order_by', None)
        employee = self.request.query_params.get('employee', None)

        if field_name != "" and order_by != "":
            if field_name == 'sort_first_name' and order_by == 'asc':
                # queryset = self.queryset.filter(is_deleted=False).order_by('employee__first_name')
                # return queryset
                sort_field='employee__first_name'
            elif field_name == 'sort_first_name' and order_by == 'desc':
                # queryset = self.queryset.filter(is_deleted=False).order_by('-employee__first_name')
                # return queryset
                sort_field='-employee__first_name'
            elif field_name == 'sort_email' and order_by == 'asc':
                # queryset = self.queryset.filter(is_deleted=False).order_by('employee__email')
                # return queryset
                sort_field='employee__email'
            elif field_name == 'sort_email' and order_by == 'desc':
                # queryset = self.queryset.filter(is_deleted=False).order_by('-employee__email')
                # return queryset
                sort_field='-employee__email'
            elif field_name == 'sort_start_date' and order_by == 'asc':
                # queryset =  self.queryset.filter(is_deleted=False).order_by('start_date')
                # return queryset
                sort_field='start_date'
            elif field_name == 'sort_start_date' and order_by == 'desc':
                # queryset = self.queryset.filter(is_deleted=False).order_by('-start_date')
                # return queryset
                sort_field='-start_date'

        if start_date and end_date:
            start_object = datetime.strptime(start_date, '%Y-%m-%d')
            end_object = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            filter['start_date__range']=(start_object, end_object)

        if leave_type:
            filter['leave_type'] = leave_type

        if employee:
            filter['employee'] = employee
        if user.is_superuser == False:
            if users_list:
                if filter:
                    queryset = self.queryset.filter(employee__in=users_list,is_deleted=False,**filter).order_by(sort_field)
                    # print("queryset",queryset.query)
                    return queryset
                elif user_name:
                    if '@' in user_name:
                        queryset = self.queryset.filter(is_deleted=False, employee__email__icontains=user_name).order_by(sort_field)
                        return queryset
                    else:
                        # print("user_name")
                        name = user_name.split(" ")
                        # print("name", name)
                        if name:
                            queryset_all = PmsAttendance.objects.none()
                            # print("len(name)",len(name))
                            for i in name:
                                queryset = self.queryset.filter(Q(is_deleted=False) & Q(employee__first_name__icontains=i) |
                                                                Q(employee__last_name__icontains=i)).order_by(sort_field)
                                queryset_all = (queryset_all|queryset)
                            return queryset_all
                else:
                    queryset = self.queryset.filter(employee__in=users_list,is_deleted=False).order_by(sort_field)
                    return queryset
            else:
                return []
        else:
            if filter:
                queryset = self.queryset.filter(is_deleted=False,**filter).order_by(sort_field)
                # print("queryset",queryset.query)
                return queryset
            elif user_name:
                if '@' in user_name:
                    queryset = self.queryset.filter(is_deleted=False, employee__email__icontains=user_name).order_by(sort_field)
                    return queryset
                else:
                    # print("user_name")
                    name = user_name.split(" ")
                    # print("name", name)
                    if name:
                        queryset_all = PmsAttendance.objects.none()
                        # print("len(name)",len(name))
                        for i in name:
                            queryset = self.queryset.filter(Q(is_deleted=False) & Q(employee__first_name__icontains=i) |
                                                            Q(employee__last_name__icontains=i)).order_by(sort_field)
                            queryset_all = (queryset_all|queryset)
                        return queryset_all
            else:
                queryset = self.queryset.filter(is_deleted=False).order_by(sort_field)
                return queryset
            
class AdvanceLeaveEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsEmployeeLeaves.objects.all()
    serializer_class=AdvanceLeaveEditSerializer
    def put(self, request,* args, **kwargs):
        response = super(AdvanceLeaveEditView, self).put(request, args, kwargs)
        # print('request: ', request.data)
        data_dict = {}
        data_dict['result'] = request.data
        if response.data:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_SUCCESS
        else:
            data_dict['request_status'] = 0
            data_dict['msg'] = settings.MSG_ERROR
        response.data = data_dict
        return response
class AdvanceLeaveMassEditView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsEmployeeLeaves.objects.all()
    serializer_class = AdvanceLeaveMassEditSerializer
    
    @response_modify_decorator_post
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class LeaveListByEmployeeView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    pagination_class = CSPageNumberPagination
    queryset = PmsEmployeeLeaves.objects.all()
    serializer_class = LeaveListByEmployeeSerializer

    def get_queryset(self,*args,**kwargs):
        employee_id=self.kwargs['employee_id']
        # print('employee_id',employee_id)
        return self.queryset.filter(employee=employee_id).order_by('-id')

    def list(self, request, *args, **kwargs):
        response = super(LeaveListByEmployeeView, self).list(request, args, kwargs)
        response.data['request_status'] = 0
        response.data['msg'] = settings.MSG_ERROR
        response.data['per_page_count'] = len(response.data['results'])
        if response.data['results']:
            response.data['request_status'] = 1
            response.data['msg'] = settings.MSG_SUCCESS
        return response

#:::::::::::::::::::Pms Attandance Deviation::::::::::::::::::::#
class AttandanceDeviationJustificationEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsAttandanceDeviation.objects.all()
    serializer_class = AttandanceDeviationJustificationEditSerializer
    def put(self, request,* args, **kwargs):
        response = super(AttandanceDeviationJustificationEditView, self).put(request, args, kwargs)
        # print('request: ', request.data)
        data_dict = {}
        data_dict['result'] = request.data
        if response.data:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_SUCCESS
        else:
            data_dict['request_status'] = 0
            data_dict['msg'] = settings.MSG_ERROR
        response.data = data_dict
        return response

class AttandanceDeviationApprovaEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsAttandanceDeviation.objects.all()
    serializer_class = AttandanceDeviationApprovaEditSerializer

class AttandanceMassDeviationApprovaEditView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsAttandanceDeviation.objects.all()
    serializer_class = AttandanceMassDeviationApprovaEditSerializer
    @response_modify_decorator_post
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class AttandanceDeviationByAttandanceListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsAttandanceDeviation.objects.all()
    serializer_class =AttandanceDeviationByAttandanceListSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('attandance',)
    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        return response

#:::::::::::::::::::::: PMS EMPLOYEE CONVEYANCE:::::::::::::::::::::::::::#
class EmployeeConveyanceAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsEmployeeConveyance.objects.all()
    serializer_class = EmployeeConveyanceAddSerializer
class EmployeeConveyanceEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsEmployeeConveyance.objects.all()
    serializer_class = EmployeeConveyanceEditSerializer

    def put(self, request,* args, **kwargs):
        response = super(EmployeeConveyanceEditView, self).put(request, args, kwargs)
        # print('request: ', request.data)
        data_dict = {}
        data_dict['result'] = request.data
        if response.data:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_SUCCESS
        else:
            data_dict['request_status'] = 0
            data_dict['msg'] = settings.MSG_ERROR
        response.data = data_dict
        return response
class EmployeeConveyanceListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsEmployeeConveyance.objects.filter(is_deleted=False)
    serializer_class = EmployeeConveyanceListSerializer
    pagination_class = CSPageNumberPagination
    def get_queryset(self):
        filter = {}
        project = self.request.query_params.get('project', None)
        employee = self.request.query_params.get('employee', None)
        project_site = self.request.query_params.get('project_site', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        approved_status = self.request.query_params.get('approved_status', None)
        user_name = self.request.query_params.get('user_name', None)
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)

        user=self.request.user
        print('login_user_details',user.is_superuser)
        print('user',user)
        users_list=(list(TCoreUserDetail.objects.filter(reporting_head=user,cu_is_deleted=False).values_list('cu_user',flat=True)))
        print('users_list',users_list)
        sort_field='-id'

        if field_name != "" and order_by != "":
            if field_name == 'date' and order_by == 'asc':
                sort_field='date'
                # queryset = self.queryset.filter(is_deleted=False).order_by('date')
                # return queryset
            elif field_name == 'date' and order_by == 'desc':
                sort_field='-date'
                # queryset = self.queryset.filter(is_deleted=False).order_by('-date')
                # return queryset
            if field_name == 'ammount' and order_by == 'asc':
                sort_field='ammount'
                # queryset = self.queryset.filter(is_deleted=False).order_by('ammount')
                # return queryset
            elif field_name == 'ammount' and order_by == 'desc':
                sort_field='-ammount'
                # queryset = self.queryset.filter(is_deleted=False).order_by('-ammount')
                # return queryset
            if field_name == 'eligibility_per_day' and order_by == 'asc':
                sort_field='eligibility_per_day'
                # queryset = self.queryset.filter(is_deleted=False).order_by('eligibility_per_day')
                # return queryset
            elif field_name == 'eligibility_per_day' and order_by == 'desc':
                sort_field='-eligibility_per_day'
                # queryset = self.queryset.filter(is_deleted=False).order_by('-eligibility_per_day')
                # return queryset
        
        if start_date and end_date:
            start_object = datetime.strptime(start_date, '%Y-%m-%d')
            end_object = datetime.strptime(end_date, '%Y-%m-%d')
            filter['date__range']=(start_object, end_object)

        if project:
            filter['project__in'] = project.split(',')

        if employee:
            filter['employee'] = employee

        if approved_status:
            filter['approved_status'] = approved_status

        if project_site:
            filter['project__site_location__in'] = project_site.split(',')

        if user.is_superuser==False:
            if users_list:
                if filter:
                    queryset = self.queryset.filter(employee__in=users_list,is_deleted=False, **filter).order_by(sort_field)
                    # print("queryset", queryset.query)
                    return queryset
                elif user_name:
                    if '@' in user_name:
                        queryset = self.queryset.filter(is_deleted=False, employee__email__icontains=user_name).order_by(sort_field)
                        return queryset
                    else:
                        print("user_name")
                        name = user_name.split(" ")
                        print("name", name)
                        if name:
                            queryset_all = PmsAttendance.objects.none()
                            print("len(name)",len(name))
                            for i in name:
                                queryset = self.queryset.filter(Q(is_deleted=False) & Q(employee__first_name__icontains=i) |
                                                                Q(employee__last_name__icontains=i)).order_by(sort_field)
                                queryset_all = (queryset_all|queryset)
                            return queryset_all
                else:
                    queryset = self.queryset.filter(employee__in=users_list,is_deleted=False).order_by(sort_field)
                    return queryset
            else:
                return []
        else:
            if filter:
                    queryset = self.queryset.filter(is_deleted=False, **filter).order_by(sort_field)
                    # print("queryset", queryset.query)
                    return queryset
            elif user_name:
                if '@' in user_name:
                    queryset = self.queryset.filter(is_deleted=False, employee__email__icontains=user_name).order_by(sort_field)
                    return queryset
                else:
                    print("user_name")
                    name = user_name.split(" ")
                    print("name", name)
                    if name:
                        queryset_all = PmsAttendance.objects.none()
                        print("len(name)",len(name))
                        for i in name:
                            queryset = self.queryset.filter(Q(is_deleted=False) & Q(employee__first_name__icontains=i) |
                                                            Q(employee__last_name__icontains=i)).order_by(sort_field)
                            queryset_all = (queryset_all|queryset)
                        return queryset_all
            else:
                queryset = self.queryset.filter(is_deleted=False).order_by(sort_field)
                return queryset


    def list(self, request, *args, **kwargs):
        response = super(EmployeeConveyanceListView, self).list(request, args, kwargs)
        response.data['request_status'] = 0
        response.data['msg'] = settings.MSG_ERROR

        if response.data['results']:
            for data in response.data['results']:
                if not data['user_project']:
                    data['user_project'] = {}
            # response.data['results'] = self.list_synchronization(list(response.data['results']))
            response.data['request_status'] = 1
            response.data['msg'] = settings.MSG_SUCCESS
        return response
#:::::::::::::::::::::::::::::::::::PMS EMPLOYEE FOODING:::::::::::::::::::::::::::::::#
class EmployeeFoodingAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsEmployeeFooding.objects.filter(is_deleted=False)
    serializer_class = EmployeeFoodingAddSerializer
class AttandanceAllDetailsListWithFoodingView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsAttendance.objects.filter(is_deleted=False)
    serializer_class = AttandanceAllDetailsListWithFoodingSerializer
    pagination_class = CSPageNumberPagination

    def get_queryset(self):
        # from django.db.models import Q
        filter = {}
        user_project = self.request.query_params.get('user_project', None)
        employee = self.request.query_params.get('employee', None)
        user_designation = self.request.query_params.get('user_designation', None)

        user_first_name = self.request.query_params.get('user_first_name', None)
        user_last_name = self.request.query_params.get('user_last_name', None)
        user_name = self.request.query_params.get('user_name', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        attendance = self.request.query_params.get('attendance', None)
        approved_status = self.request.query_params.get('approved_status', None)
        field_name=self.request.query_params.get('field_name',None)
        order_by = self.request.query_params.get('order_by', None)

        user=self.request.user
        print('login_user_details',user.is_superuser)
        print('user',user)
        users_list=(list(TCoreUserDetail.objects.filter(reporting_head=user,cu_is_deleted=False).values_list('cu_user',flat=True)))
        print('users_list',users_list)
        sort_field='-id'

        if field_name !="" and order_by !="":
            print("field_name is not None and order_by is not None")
            if field_name == 'sort_first_name' and order_by == 'asc':
                sort_field='employee__first_name'
                # queryset = self.queryset.filter(is_deleted=False).order_by('employee__first_name')
                # return queryset
            elif field_name == 'sort_first_name' and order_by == 'desc':
                sort_field='-employee__first_name'
                # queryset = self.queryset.filter(is_deleted=False).order_by('-employee__first_name')
                # return queryset
            elif field_name == 'sort_created_at' and order_by == 'asc':
                sort_field='date'
                # queryset =  self.queryset.filter(is_deleted=False).order_by('date')
                # return queryset
            elif field_name == 'sort_created_at' and order_by == 'desc':
                sort_field='-date'
                # queryset = self.queryset.filter(is_deleted=False).order_by('-date')
                # return queryset
            elif field_name == 'sort_user_project' and order_by == 'asc':
                sort_field='user_project'
                # queryset = self.queryset.filter(is_deleted=False).order_by('user_project')
                # return queryset
            elif field_name == 'sort_user_project' and order_by == 'desc':
                sort_field='-user_project'
                # queryset = self.queryset.filter(is_deleted=False).order_by('-user_project')
                # return queryset

        if user_first_name:
            filter['employee__first_name__icontains'] = user_first_name
        if user_last_name:
            filter['employee__last_name__icontains'] = user_last_name

        if start_date and end_date:
            start_object = datetime.strptime(start_date, '%Y-%m-%d')
            end_object = datetime.strptime(end_date, '%Y-%m-%d')
            filter['created_at__range']=(start_object, end_object)
        if user_project:
            filter['user_project__in']= user_project.split(',')

        if user_designation:
            filter['employee__mmr_user']= user_designation

        if attendance:
            filter['id'] = attendance

        if employee:
            filter['employee'] = employee

        if approved_status:
            filter['approved_status'] = approved_status
        if user.is_superuser==False:
            if users_list:
                if filter:
                    queryset = self.queryset.filter(employee__in=users_list,is_deleted=False,**filter).order_by(sort_field)
                    print("queryset",queryset.query)
                    return queryset
                elif user_name:
                    if '@' in user_name:
                        queryset = self.queryset.filter(is_deleted=False, employee__email__icontains=user_name).order_by(sort_field)
                        return queryset
                    else:
                        print("user_name")
                        name = user_name.split(" ")
                        print("name", name)
                        if name:
                            queryset_all = PmsAttendance.objects.none()
                            print("len(name)",len(name))
                            for i in name:
                                queryset = self.queryset.filter(Q(is_deleted=False) & Q(employee__first_name__icontains=i) |
                                                                Q(employee__last_name__icontains=i)).order_by(sort_field)
                                queryset_all = (queryset_all|queryset)
                            return queryset_all
                else:
                    queryset = self.queryset.filter(employee__in=users_list,is_deleted=False).order_by(sort_field)
                    return queryset
            else:
                return []
        else:
            if filter:
                queryset = self.queryset.filter(is_deleted=False,**filter).order_by(sort_field)
                # print("queryset",queryset.query)
                return queryset
            elif user_name:
                if '@' in user_name:
                    queryset = self.queryset.filter(is_deleted=False, employee__email__icontains=user_name).order_by(sort_field)
                    return queryset
                else:
                    print("user_name")
                    name = user_name.split(" ")
                    print("name", name)
                    if name:
                        queryset_all = PmsAttendance.objects.none()
                        print("len(name)",len(name))
                        for i in name:
                            queryset = self.queryset.filter(Q(is_deleted=False) & Q(employee__first_name__icontains=i) |
                                                            Q(employee__last_name__icontains=i)).order_by(sort_field)
                            queryset_all = (queryset_all|queryset)
                        return queryset_all
            else:
                queryset = self.queryset.filter(is_deleted=False).order_by(sort_field)
                return queryset


    def list_synchronization(self, list_data: list)-> list:
        data = pd.DataFrame(list_data)
        data = data.replace(np.nan, 0, regex=True)
        data.sort_values("date", axis = 0, ascending = True, inplace = True,)
        col_list = data.columns.values
        row_list = data.values.tolist()
        total_result = list()
        for row in row_list:
            data_dict = dict(zip(col_list,row))
            total_result.append(data_dict)
        list_data = total_result
        return list_data

    def list(self, request, *args, **kwargs):
        response = super(AttandanceAllDetailsListWithFoodingView, self).list(request,args,kwargs)
        response.data['request_status'] = 0
        response.data['msg'] = settings.MSG_ERROR

        if response.data['results']:
            for data in response.data['results']:
                if not data['user_project']:
                    data['user_project'] = {}
            # response.data['results'] = self.list_synchronization(list(response.data['results']))
            response.data['request_status'] = 1
            response.data['msg'] = settings.MSG_SUCCESS
        return response


#:::::::::::::::::::::::::::::::: ATTENDENCE LIST EXPORT ::::::::::::::::::::::::::::::#
class AttandanceListExportView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsAttendance.objects.all()

    def get(self, request, *args, **kwargs):
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        filter = {}
        if start_date and end_date:
            end_date = end_date + 'T23:59:59'
            start_object = datetime.strptime(start_date, '%Y-%m-%d')
            end_object = datetime.strptime(end_date, '%Y-%m-%dT%H:%M:%S')
            filter['date__range'] = (start_object, end_object)

        else:
            # cur_date = timezone.now().date()###,date__date=timezone.now().date()
            return Response({
                'status': 0,
                'msz':'Enter proper Date range',
                })
        attemdance_data = PmsAttendance.objects.filter(is_deleted=False,**filter).values(
            'id','employee__first_name','employee__last_name','login_time','logout_time','user_project__name','justification','approved_status').order_by('-date')

        data_list = []
        count = 0

        for att_data in attemdance_data:
            # print("data", att_data)
            login_time = att_data['login_time'].strftime("%I:%M:%S %p")
            if att_data['logout_time']:
                logout_time = att_data['logout_time'].strftime("%I:%M:%S %p")
                logout_datetime = att_data['logout_time'].strftime("%d/%m/%Y, %I:%M:%S %p")
            else:
                logout_time = ""
                logout_datetime = ""

            name = ""
            if att_data['employee__first_name']:
                name = att_data['employee__first_name']
                if att_data['employee__first_name']:
                    name += " " + att_data['employee__last_name']

            if att_data['approved_status']==1:
                approved_status = "pending"
            elif att_data['approved_status'] == 2:
                approved_status = "approved"
            elif att_data['approved_status'] == 3:
                approved_status = "reject"
            else:
                approved_status = "regular"

            deviation_data = PmsAttandanceDeviation.objects.filter(attandance=att_data['id']).values('from_time','to_time')
            if deviation_data:
                for dev_data in deviation_data:
                    count += 1
                    # print("dev_data",dev_data)
                    from_time = dev_data['from_time'].strftime("%I:%M:%S %p")
                    to_time = dev_data['to_time'].strftime("%I:%M:%S %p")
                    attemdance_list = [count,att_data['id'],name,login_time,logout_time,logout_datetime,
                        att_data['user_project__name'],att_data['justification'],approved_status,from_time,to_time]

                    # print("attemdance_list",attemdance_list)
                    data_list.append(attemdance_list)
            else:
                count+=1
                attemdance_list = [count,att_data['id'],name,login_time,logout_time,logout_datetime,
                        att_data['user_project__name'],att_data['justification'],approved_status,"",""]

                data_list.append(attemdance_list)

        # print("data_list",data_list)
        if data_list:
            file_path = self.creat_excel(data_list)

        return Response({
            'status': 1,
            'msz':'successful',
            'results': file_path
        })

    def creat_excel(self, data_list):
        import pandas as pd
        path = "/home/nooralam/Desktop/Scores.xlsx"
        table = pd.DataFrame(data_list)
        table.columns = ['Serial no','Attendance id','Employee Name','Login Time','Logout Time','Logout Datetime','Project Name',
                        'Justification','Approved status','From time(Deviation)','To time(Deviation)']
        writer = pd.ExcelWriter(path)
        table.to_excel(writer, 'Scores 1', index=False)
        writer.save()

        return path


'''
    @@ Added By Rupam Hazra on [10-01-2020] line number 1597-1606 @@
    
'''
class AttendanceUpdateLogOutTimeFailedOnLogoutView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsAttendance.objects.filter(is_deleted=False)
    serializer_class = AttendanceUpdateLogOutTimeFailedOnLogoutSerializer

    @response_modify_decorator_update
    def put(self, request,* args, **kwargs):
        return super().update(request, *args, **kwargs)

class AttandanceLogMultipleByThreadAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsAttandanceLog.objects.filter(is_deleted=False)
    serializer_class = AttandanceLogMultipleByThreadAddSerializer

    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        return response

    @response_modify_decorator_post
    def post(self, request,* args, **kwargs):
        return super().post(request, *args, **kwargs)


#:::::::::::::::::::::::::::::::: ATTENDENCE LIST EXPORT ::::::::::::::::::::::::::::::#

class PmsAttandanceSAPExportView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsAttendance.objects.all()

    @response_modify_decorator_list_after_execution
    def get(self, request, *args, **kwargs):
        total_list = list()
        req_filter = dict()
        cur_date =self.request.query_params.get('cur_date', None)
        year = self.request.query_params.get('year', None)
        month = self.request.query_params.get('month', None)

        if cur_date:
            date = datetime.strptime(cur_date, "%Y-%m-%d")
            date_range_first = AttendenceMonthMaster.objects.filter(month_start__date__lte=date,month_end__date__gte=date).values('month_start__date','month_end__date')
            date = date_range_first[0]['month_start__date'] - timedelta(days=1)
            date_range = AttendenceMonthMaster.objects.filter(month_start__date__lte=date,month_end__date__gte=date).values('month_start__date','month_end__date')

        elif year and month:
            date_range = AttendenceMonthMaster.objects.filter(month=month,month_end__year=year).values('month_start__date','month_end__date')

        if date_range:
            #print("date_range",date_range)
            req_filter['duration_start__date__gte']=date_range[0]['month_start__date']
            req_filter['duration_start__date__lte']=date_range[0]['month_end__date']
            req_filter['is_requested'] = True
            req_filter['is_deleted'] = False

            # Avoid director punch ids in SAP report.
            director_user_id = list(TCoreUserDetail.objects.filter(user_type__in=('User','Housekeeper')).values_list('cu_user',flat=True))
            module_user_list = list(TMasterModuleRoleUser.objects.filter(~Q(mmr_user__in=director_user_id),mmr_module__cm_name='PMS',mmr_type=3).values_list('mmr_user',flat=True))
            #print('module_user_list',module_user_list)
            req_filter['attendance__employee__in']=module_user_list
            print(req_filter['attendance__employee__in'])

        if req_filter:
            request_details = PmsAttandanceDeviation.objects.filter(
                ((Q(leave_type_changed_period__isnull=False)&
                (Q(leave_type_changed_period='FD')|Q(leave_type_changed_period='HD')))|
                (Q(leave_type_changed_period__isnull=True)&(Q(request_type='FD')|Q(request_type='HD')))),
                *req_filter)
            pass

        return Response({
            'status': 1,
            'msz':'successful',
            'results': ''
        })
    


#:::::::::::::::::::: L I V E   T R A C K I N G :::::::::::::::::#

class PmsLiveTrackingForAllEmployeesView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsProjectUserMapping.objects.filter(is_deleted=False,status=True)
    serializer_class = PmsLiveTrackingForAllEmployeesSerializer
    
    def get_queryset(self):
        project_id = self.kwargs['project_id']
        queryset = self.queryset.filter(project=project_id)
        return queryset

    @response_modify_decorator_get_after_execution
    def get(self, request, *args, **kwargs):
        response = super(__class__, self).get(request,args,kwargs)
        #print('response',response.data)
        current_date_time = datetime.now()
        project_id = self.kwargs['project_id']
        data_dict = PmsProjects.objects.filter(pk=project_id).values(
            'id','project_g_id','site_location_id',
            'site_location__site_latitude','site_location__site_longitude','site_location__office_latitude',
            'site_location__office_latitude','site_location__office_longitude','site_location__gest_house_latitude',
            'site_location__gest_house_longitude','site_location__geo_fencing_area')[0]
        data_dict['lat_lng'] = PmsSiteProjectSiteManagementMultipleLongLat.objects.filter(
            project_site_id=data_dict['site_location_id']).values()
        for data in response.data:
            queryset = PmsAttandanceLog.objects.filter(
            (
                Q(
                    time__date=current_date_time.date(),
                    time__hour=current_date_time.hour,
                    time__minute=current_date_time.minute,
                )|
                Q(
                    time__date=current_date_time.date(),
                    time__hour=current_date_time.hour,
                    time__minute__lte=current_date_time.minute,
                )
            ),
            created_by_id=data['user']
            ).values('id','attandance','attandance__login_time','time','latitude','longitude','address')
            #print('queryset',queryset.query)
            #print('queryset',queryset)
            if queryset:
                data['current_position_details'] = queryset[0]
            else:
                queryset = PmsAttandanceLog.objects.filter(attandance__employee_id=data['user'],attandance__is_present=True).values('id','attandance','attandance__login_time','time','latitude','longitude','address').order_by('-id')
                if queryset:
                    data['current_position_details'] = queryset[0]
                else:
                    data['current_position_details'] = None

        data_dict['employee_details'] = response.data
        response.data = data_dict
        return response

class PmsLiveTrackingForAEmployeeInAProjectView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsProjectUserMapping.objects.filter(is_deleted=False,status=True)
    serializer_class = PmsLiveTrackingForAllEmployeesSerializer
    
    def get_queryset(self):
        employee_id = self.kwargs['employee_id']
        queryset = self.queryset.filter(user=employee_id)
        return queryset

    @response_modify_decorator_get_after_execution
    def get(self, request, *args, **kwargs):
        response = super(__class__, self).get(request,args,kwargs)
        #print('response',response.data)
        current_date_time = datetime.now()
        employee_id = self.kwargs['employee_id']
        data_dict = User.objects.filter(pk=employee_id).values(
            'id','first_name','last_name')[0]
        data_dict['current_project_details'] = PmsAttendance.objects.filter(
            employee_id=employee_id,
            #date__date = current_date_time.date(),
            #login_time__date = current_date_time.date()
            ).values('id','login_time','user_project','user_project__project_g_id','user_project__site_location_id','user_project__site_location__name',
            'user_project__site_location__site_latitude',
            'user_project__site_location__site_longitude','user_project__site_location__office_latitude',
            'user_project__site_location__office_latitude','user_project__site_location__office_longitude',
            'user_project__site_location__gest_house_latitude','user_project__site_location__gest_house_longitude',
            'user_project__site_location__geo_fencing_area').order_by('-id').first()
        data_dict['current_project_details']['lat_lng'] = PmsSiteProjectSiteManagementMultipleLongLat.objects.filter(
            project_site_id=data_dict['current_project_details']['user_project__site_location_id']).values()

        if data_dict['current_project_details']:
            queryset = PmsAttandanceLog.objects.filter(
                (
                    Q(
                        time__date=current_date_time.date(),
                        time__hour=current_date_time.hour,
                        time__minute=current_date_time.minute,
                    )|
                    Q(
                        time__date=current_date_time.date(),
                        time__hour=current_date_time.hour,
                        time__minute__lte=current_date_time.minute,
                    )
                ),
                created_by_id = employee_id
                ).values('id','attandance','time','latitude','longitude','address').first()
            #print('queryset',queryset.query)
            #print('queryset',queryset)
            data_dict['current_project_details']['current_position_details'] = queryset
        else:
            data_dict['current_project_details'] = None
        response.data = data_dict
        return response



class PmsAttendanceCronView(APIView):
    permission_classes = [AllowAny]
    #authentication_classes = [TokenAuthentication]
    
    def all_leave_calculation_upto_applied_date(self, date_object=None, user=None,fortnight=None):
        from django.db.models import Sum

        '''
        Start :: Normal leave availed by user
        '''
        sl_eligibility = 0
        el_eligibility = 0
        cl_eligibility = 0

        availed_hd_ab=0.0
        availed_ab=0.0
        availed_al = 0.0
        availed_cl = 0.0
        availed_el = 0.0
        availed_sl = 0.0

        availed_hd_al=0.0
        availed_hd_cl=0.0
        availed_hd_sl=0.0
        availed_hd_el=0.0

        carry_forward_leave = AttendanceCarryForwardLeaveBalanceYearly.objects.filter(employee=user.cu_user,is_deleted=False).first() #.aggregate(Sum('leave_balance'))
        #print('carry_forward_leave:',carry_forward_leave)

        salary13_carry_forward_al = 0.0
        total_carry_forward_leave = 0.0

        if carry_forward_leave and user.salary_type and (user.salary_type.st_code=='FF' or user.salary_type.st_code=='EE'):
            salary13_carry_forward_al = carry_forward_leave.leave_balance
        
        # salary13_carry_forward_al = carry_forward_leave.leave_balance if carry_forward_leave and user.salary_type and user.salary_type.st_name=='13'and user.is_confirm else 0.0
        #print('salary13_carry_forward_al:', salary13_carry_forward_al)

        month_master=AttendenceMonthMaster.objects.filter(month_start__date__lte=date_object,
                                                    month_end__date__gte=date_object,is_deleted=False).first()
        
        #print("month_master:", month_master)
        attendence_daily_data = PmsAttandanceDeviation.objects.filter(((
            Q(leave_type_changed_period__isnull=False)&(Q(leave_type_changed_period='FD')|Q(leave_type_changed_period='HD')))|
            (Q(leave_type_changed_period__isnull=True)&(Q(deviation_type='FD')|Q(deviation_type='HD')))),
            from_time__date__gte=month_master.year_start_date.date(),
            attandance__employee=user.cu_user.id,is_requested=True).values('from_time__date').distinct()
        #print("attendence_daily_data",attendence_daily_data)
        date_list = [x['from_time__date'] for x in attendence_daily_data.iterator()]
        #print("date_list",date_list)
        
        availed_master_wo_reject_fd = PmsAttandanceDeviation.objects.\
            filter((Q(approved_status=1)|Q(approved_status=2)|Q(approved_status=3)),
                    (Q(leave_type__isnull=False)|Q(leave_type_changed_period__isnull=False)),
                    attandance__employee=user.cu_user.id,
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
                #print('availed_FD',availed_FD)
                if availed_FD.filter(leave_type_final__isnull=False):
                    if availed_FD.values('leave_type_final').count() >1:
                        if availed_FD.filter(leave_type_final='AB'):
                            availed_ab=availed_ab+1.0
                        elif availed_FD.filter(leave_type_final='AL'):
                            availed_al = availed_al + 1.0
                        elif availed_FD.filter(leave_type_final='EL'):
                            availed_el = availed_el + 1.0
                        elif availed_FD.filter(leave_type_final='SL'):
                            availed_sl = availed_sl + 1.0
                        elif availed_FD.filter(leave_type_final='CL'):
                            availed_cl = availed_cl + 1.0
                    else:
                        l_type=availed_FD[0]['leave_type_final']
                        if l_type == 'AL':
                            availed_al = availed_al + 1.0
                        elif l_type == 'AB':
                            availed_ab=availed_ab+1.0
                        elif l_type == 'EL':
                            availed_el=availed_el+1.0
                        elif l_type == 'SL':
                            availed_sl=availed_sl+1.0
                        elif l_type == 'CL':
                            availed_cl=availed_cl+1.0

                elif availed_FD.filter(leave_type_final_hd__isnull=False):
                    #print('saddsadsdasdasdasdsadsadsdasdasdad')
                    #print('leave_type_final_hd', availed_FD.values('leave_type_final_hd').count())
                    #time.sleep(10)
                    if availed_FD.values('leave_type_final_hd').count() >1:
                        if availed_FD.filter(leave_type_final_hd='AB'):
                            availed_hd_ab=availed_hd_ab+1.0
                        elif availed_FD.filter(leave_type_final_hd='AL'):
                            availed_hd_al=availed_hd_al+1.0
                        elif availed_FD.filter(leave_type_final_hd='CL'):
                            availed_hd_cl=availed_hd_cl+1.0
                        elif availed_FD.filter(leave_type_final_hd='EL'):
                            availed_hd_el=availed_hd_el+1.0
                        elif availed_FD.filter(leave_type_final_hd='SL'):
                            availed_hd_sl=availed_hd_sl+1.0
                    else:
                        l_type=availed_FD[0]['leave_type_final_hd']
                        if l_type == 'AL':
                            availed_hd_al=availed_hd_al+1.0
                        elif l_type == 'AB':
                            availed_hd_ab=availed_hd_ab+1.0
                        elif l_type == 'CL':
                            availed_hd_cl=availed_hd_cl+1.0
                        elif l_type == 'SL':
                            availed_hd_sl=availed_hd_sl+1.0
                        elif l_type == 'EL':
                            availed_hd_el=availed_hd_el+1.0

        #print('availed_al',availed_hd_al)
        #time.sleep(10)
        
        '''
            Get total leave allocation(monthly) by request start and end date
        '''
        leave_allocation_per_month = 0.0
        leave_allocation_per_month_cl = 0.0
        leave_allocation_per_month_sl = 0.0
        leave_allocation_per_month_el = 0.0

        leave_allocation_per_month_d = AttendenceLeaveAllocatePerMonthPerUser.objects.filter(
            (
                Q(month__month_start__date__gte=month_master.year_start_date.date(),month__month_end__date__lte=date_object)|
                Q(month__month_start__date__lte=date_object,month__month_end__date__gte=date_object)
            ),employee=user.cu_user)

        if user.salary_type:
        
            if user.salary_type.st_code == 'FF' or user.salary_type.st_code == 'EE':
                leave_allocation_per_month = leave_allocation_per_month_d.aggregate(Sum('round_figure'))['round_figure__sum']

            if user.salary_type.st_code == 'CC' or user.salary_type.st_code == 'DD':
                #print('round_cl_allotted',leave_allocation_per_month_d.aggregate(Sum('round_cl_allotted'))['round_cl_allotted__sum'])
                #print('round_el_allotted',leave_allocation_per_month_d.aggregate(Sum('round_el_allotted'))['round_el_allotted__sum'])
                #print('round_sl_allotted',leave_allocation_per_month_d.aggregate(Sum('round_sl_allotted'))['round_sl_allotted__sum'])
                leave_allocation_per_month_cl = leave_allocation_per_month_d.aggregate(Sum('round_cl_allotted'))['round_cl_allotted__sum']
                leave_allocation_per_month_el = leave_allocation_per_month_d.aggregate(Sum('round_el_allotted'))['round_el_allotted__sum']
                leave_allocation_per_month_sl = leave_allocation_per_month_d.aggregate(Sum('round_sl_allotted'))['round_sl_allotted__sum']

            
            if user.salary_type.st_code == 'BB':
                leave_allocation_per_month_cl = leave_allocation_per_month_d.aggregate(Sum('round_cl_allotted'))['round_cl_allotted__sum']
                leave_allocation_per_month_el = leave_allocation_per_month_d.aggregate(Sum('round_el_allotted'))['round_el_allotted__sum']
        
            if user.salary_type.st_code == 'AA':
                leave_allocation_per_month_cl = 0
                leave_allocation_per_month_el = 0
                leave_allocation_per_month_sl = 0
                leave_allocation_per_month = 0

        else:
            leave_allocation_per_month_cl = 0
            leave_allocation_per_month_el = 0
            leave_allocation_per_month_sl = 0

        print('leave_allocation_per_month',leave_allocation_per_month)           


        # ::````Advance Leave Calculation```:: #
        '''
            Advance leave calculation from  after last attendance date to current month master end date.
        '''
        advance_leave=EmployeeAdvanceLeaves.objects.filter(Q(employee=user.cu_user)&
                                                           Q(is_deleted=False)&
                                                           (Q(approved_status='pending')|Q(approved_status='approved'))&
                                                           Q(start_date__date__lte=month_master.month_end.date())
                                                          ).values('leave_type','start_date','end_date')
        #print('advance_leave',advance_leave)     
        advance_al=0
        advance_ab=0
        advance_el=0
        advance_cl=0
        day=0

        last_attendance = PmsAttendance.objects.filter(employee=user.cu_user).values_list('date__date',flat=True).order_by('-date')[:1]
        #print("last_attendance",last_attendance)
        last_attendance = last_attendance[0] if last_attendance else date_object
        
        if last_attendance<month_master.month_end.date():
            #print("last_attendancehfthtfrhfth",last_attendance)
            adv_str_date = last_attendance+timedelta(days=1)
            adv_end_date = month_master.month_end.date()+timedelta(days=1)
            if advance_leave:
                for leave in advance_leave:
                    #print('leave',leave)
                    start_date=leave['start_date'].date()
                    end_date=leave['end_date'].date()+timedelta(days=1)
                    #print('start_date,end_date',start_date,end_date)

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
                    elif leave['leave_type']=='CL':
                        advance_cl+=day
                    elif leave['leave_type']=='EL':
                        advance_el+=day
                    #print('advance_al loop', advance_al)


        '''
            Section for count total leave count which means 
            total of advance leaves and approval leave
        '''
        
        #print('advance_al',advance_al)
        # print('how_many_days_ab_taken',how_many_days_ab_taken)
        
        #print("availed_el",availed_el)

        # print("availed_al",availed_al)
        # print('availed_ab',availed_ab)
        # print('advance_ab',advance_ab)
        # print('availed_hd_ab',availed_hd_ab)
        # print('availed_hd_al',availed_hd_al)
        # time.sleep(5)
        total_availed_al=float(availed_al)+float(advance_al)+float(availed_hd_al/2)
        total_availed_ab=float(availed_ab) + float(advance_ab) +float(availed_hd_ab/2)
        total_availed_cl=float(availed_cl) + float(advance_cl) +float(availed_hd_cl/2)
        total_availed_el=float(availed_el) + float(advance_el) +float(availed_hd_el/2)
        total_availed_sl=float(availed_sl) + float(availed_hd_sl/2)

        # print("total_availed_al",total_availed_al)
        # print('total_availed_ab', total_availed_ab)

        '''
            Section for remaining leaves from granted leave - availed leave
        '''
        leave_allocation_per_month  = float(leave_allocation_per_month) + float(salary13_carry_forward_al)
        balance_al = leave_allocation_per_month - float(total_availed_al)
        balance_cl = float(leave_allocation_per_month_cl) - float(total_availed_cl)
        balance_sl = float(leave_allocation_per_month_sl) - float(total_availed_sl)
        balance_el = float(leave_allocation_per_month_el) - float(total_availed_el)



        availed_grace = PmsAttandanceDeviation.objects.filter(Q(attandance__employee=user.cu_user) &
                                                                Q(from_time__gte=month_master.month_start) &
                                                                Q(from_time__lte=month_master.month_end) &
                                                                Q(is_requested=True)).aggregate(Sum('duration'))['duration__sum']

        availed_grace = availed_grace if availed_grace else 0
        total_month_grace = month_master.grace_available
        grace_balance = total_month_grace - availed_grace

        yearly_leave_allocation = float(user.granted_cl) + float(user.granted_sl) + float(user.granted_el) + float(total_carry_forward_leave)
        sl_eligibility = float(user.granted_sl)
        el_eligibility = float(user.granted_el)
        cl_eligibility = float(user.granted_cl)

        month_start = month_master.month_start

        if user.joining_date > month_master.year_start_date:
            approved_leave=JoiningApprovedLeave.objects.filter(employee=user.cu_user,is_deleted=False).first()
            if approved_leave:

                yearly_leave_allocation = float(approved_leave.cl) + float(approved_leave.sl) + float(approved_leave.el)
                sl_eligibility = float(approved_leave.sl)
                el_eligibility = float(approved_leave.el)
                cl_eligibility = float(approved_leave.cl)


                if month_master.month==approved_leave.month:    #for joining month only
                    total_month_grace=approved_leave.first_grace
                    month_start=user.joining_date
                    grace_balance=total_month_grace - availed_grace
        
        
        if user.salary_type:
            
            if user.salary_type.st_code == 'FF' or user.salary_type.st_code == 'EE':
                yearly_leave_allocation = yearly_leave_allocation
                leave_allocation_per_month = leave_allocation_per_month
                total_availed_al = total_availed_al
                balance_al = balance_al
                
            if user.salary_type.st_code == 'CC' or user.salary_type.st_code == 'DD':
                yearly_leave_allocation = cl_eligibility + el_eligibility + sl_eligibility
                leave_allocation_per_month = leave_allocation_per_month_cl + leave_allocation_per_month_el + leave_allocation_per_month_sl
                total_availed_al = total_availed_cl + total_availed_el + total_availed_sl
                balance_al = balance_cl + balance_el + balance_sl
                
            if user.salary_type.st_code == 'BB':
                yearly_leave_allocation = cl_eligibility + el_eligibility
                leave_allocation_per_month = leave_allocation_per_month_cl + leave_allocation_per_month_el
                total_availed_al = total_availed_cl + total_availed_el
                balance_al = balance_cl + balance_el
                
            if user.salary_type.st_code == 'AA':
                yearly_leave_allocation = 0
                leave_allocation_per_month = 0
                total_availed_al = 0
                balance_al = 0
        
        else:
            yearly_leave_allocation = 0
            leave_allocation_per_month = 0
            total_availed_al = 0
            balance_al = 0

        result = {
            "employee_id":user.cu_user.id,
            "employee_username":user.cu_user.username,
            "month_start":month_start,
            "month_end":month_master.month_end,
            "year_start":month_master.year_start_date,
            "year_end":month_master.year_end_date,
            "is_confirm": False,
            
            "salary_type_code": user.salary_type.st_code if user.salary_type else "",
            "salary_type": user.salary_type.st_name if user.salary_type else "",

            "total_absent": total_availed_ab,

            "total_eligibility": yearly_leave_allocation,
            "total_accumulation": leave_allocation_per_month,
            "total_consumption": total_availed_al,
            "total_available_balance": balance_al,

            "cl_eligibility":cl_eligibility,
            "granted_cl":leave_allocation_per_month_cl,
            "availed_cl":total_availed_cl,
            "cl_balance":balance_cl if balance_cl > 0 else 0.0,

            "el_eligibility":el_eligibility,
            "granted_el":leave_allocation_per_month_el,
            "availed_el":total_availed_el,
            "el_balance":balance_el if balance_el > 0 else 0.0,

            "sl_eligibility":sl_eligibility,
            "granted_sl":leave_allocation_per_month_sl,
            "availed_sl":total_availed_sl,
            "sl_balance": balance_sl if  balance_sl > 0 else 0.0,

            }

        return result
    
    def get_flexi_hours_calculation(self, date_object=None, user=None,fortnight=None):

        result = self.all_leave_calculation_upto_applied_date(date_object=date_object, user=user,fortnight=fortnight)

        #print('result',result)
        balance_al = result['total_available_balance']
        total_availed_ab = result['total_absent']

        month_master=AttendenceMonthMaster.objects.filter(month_start__date__lte=date_object,month_end__date__gte=date_object,is_deleted=False).first()

        fortnight_response = list()
        deviation_in_hours = 0
        leave_deduction = 0.0
        last_attendance_date = None
        deviation_hrs_mins_1st = 0
        fortnight_start_date = None
        fortnight_end_date = None

        if fortnight and fortnight == '1':

            fortnight_start_date = month_master.month_start
            fortnight_end_date = month_master.fortnight_date
            
            total_hours_1st, working_hours_1st = get_pms_flexi_hours_for_work_days(tcore_user=user, start_date=fortnight_start_date, end_date=fortnight_end_date,fortnight_flag_cron=True)
            #print('total_hours_1st',total_hours_1st,'working_hours_1st',working_hours_1st)
            #time.sleep(10)
            #print('total_hours_1st',total_hours_1st)

            ''' 
                Start Added by Rupam Hazra for 26.07.2020 - Not log in by official circular as PMS New Attendace Live
            '''

            total_hours_1st = (float(total_hours_1st) - float(480)) if month_master.payroll_month == 'AUGUST' else total_hours_1st

            ''' 
                End Added by Rupam Hazra for 26.07.2020 - Not log in by official circular as PMS New Attendace Live
            '''
            
            total_hrs_1st, total_mins_1st = divmod(int(total_hours_1st), 60)
            total_hrs_mins_1st = '{} hrs {} mins'.format(total_hrs_1st, total_mins_1st) if total_hrs_1st else '{} mins'.format(total_mins_1st)
            
            working_hrs_1st, working_mins_1st = divmod(int(working_hours_1st), 60)
            working_hrs_mins_1st = '{} hrs {} mins'.format(working_hrs_1st, working_mins_1st) if working_hrs_1st else '{} mins'.format(working_mins_1st)
            #print('working_hrs_mins_1st',working_hrs_mins_1st)
            #time.sleep(10)

            ## Start Deviation Hours Calculation ##

            deviation_hours_fortnight_1st = total_hours_1st - working_hours_1st
            if deviation_hours_fortnight_1st > 0 :
                #auto_od_approved = self.auto_approved_od_by_user(date_object=month_master.fortnight_date,user=user,fortnight=fortnight,balance_al=balance_al)
                
                deviation_hours_fortnight_1st = deviation_hours_fortnight_1st

                deviation_hrs_1st, deviation_mins_1st = divmod(int(deviation_hours_fortnight_1st), 60)
                deviation_hrs_mins_1st = '{} hrs {} mins'.format(deviation_hrs_1st, deviation_mins_1st) if deviation_hrs_1st else '{} mins'.format(deviation_mins_1st)
                deviation_in_hours = int(deviation_hours_fortnight_1st)
                leave_deduction = get_fortnight_leave_deduction(hour=int(deviation_hours_fortnight_1st)/60)
                
            else:
                deviation_hours_fortnight_1st = 0
                deviation_hrs_mins_1st = 0
                leave_deduction = 0.0

                
            last_attendance_date = month_master.fortnight_date
            ## End Deviation Hours Calculation ##

            fortnight_response.append({
                'fortnight': 1,
                'is_active': date_object <= month_master.fortnight_date.date(),
                'flexi_start_date': month_master.month_start,
                'flexi_end_date': month_master.fortnight_date,
                'total_hours': total_hrs_mins_1st,
                'working_hours': working_hrs_mins_1st,
                'deviation_in_hours_mins':deviation_hrs_mins_1st,
                'deviation_in_hours':int(deviation_hours_fortnight_1st),
                'leave_deduction':leave_deduction,
               

            })

        elif fortnight and fortnight == '2':
            fortnight_start_date = month_master.fortnight_date + timedelta(days=1)
            fortnight_end_date = month_master.month_end
            ### Start Total and Working Hours Calculation ###

            total_hours_2st, working_hours_2st = get_pms_flexi_hours_for_work_days(tcore_user=user, start_date=fortnight_start_date, end_date=fortnight_end_date,fortnight_flag_cron=True)
            
            total_hours_2st = (float(total_hours_2st) - float(480)) if month_master.payroll_month == 'DECEMBER' else total_hours_2st
            
            #print('total_hours_2st',total_hours_2st,'working_hours_2st',working_hours_2st)
            total_hrs_2st, total_mins_2st = divmod(int(total_hours_2st), 60)
            total_hrs_mins_2st = '{} hrs {} mins'.format(total_hrs_2st, total_mins_2st) if total_hrs_2st else '{} mins'.format(total_mins_2st)
            
            working_hrs_2st, working_mins_2st = divmod(int(working_hours_2st), 60)
            working_hrs_mins_2st = '{} hrs {} mins'.format(working_hrs_2st, working_mins_2st) if working_hrs_2st else '{} mins'.format(working_mins_2st)
            #print('working_hrs_mins_2st',working_hrs_mins_2st)
            #time.sleep(10)

            ## Start Total and Working Hours Calculation ##


            ### Start Deviation Hours Calculation ###

            deviation_hours_fortnight_2st = total_hours_2st - working_hours_2st
            if deviation_hours_fortnight_2st > 0 :
                #auto_od_approved = self.auto_approved_od_by_user(date_object=month_master.fortnight_date,user=user,fortnight=fortnight,balance_al=balance_al)

                deviation_hours_fortnight_2st = deviation_hours_fortnight_2st
                deviation_hrs_2st, deviation_mins_2st = divmod(int(deviation_hours_fortnight_2st), 60)
                deviation_hrs_mins_2st = '{} hrs {} mins'.format(deviation_hrs_2st, deviation_mins_2st) if deviation_hrs_2st else '{} mins'.format(deviation_mins_2st)
                deviation_in_hours = int(deviation_hours_fortnight_2st)
                leave_deduction = get_fortnight_leave_deduction(hour=int(deviation_hours_fortnight_2st)/60)
            else:
                deviation_hours_fortnight_2st = 0
                deviation_hrs_mins_2st = 0
                leave_deduction = 0.0


            
            last_attendance_date = month_master.month_end
            ## End Deviation Hours Calculation ##

            fortnight_response.append({
                    'fortnight': 2,
                    'is_active': date_object > month_master.fortnight_date.date(),
                    'flexi_start_date': month_master.fortnight_date + timedelta(days=1),
                    'flexi_end_date': month_master.month_end,
                    'total_hours': total_hrs_mins_2st,
                    'working_hours': working_hrs_mins_2st,
                    'deviation_in_hours_mins':deviation_hrs_mins_2st,
                    'deviation_in_hours':int(deviation_hours_fortnight_2st),
                    'leave_deduction':leave_deduction,
                    
                })
        
          
        print('leave_deduction',leave_deduction, type(leave_deduction))

        if leave_deduction!= 0.0:
            self.add_fortnight_leave_deduction_log(leave_deduction,deviation_in_hours,result,last_attendance_date,user.cu_user,fortnight_start_date,fortnight_end_date)

        self.update_lock_status(user.cu_user,fortnight_start_date,fortnight_end_date)
        result['fortnight'] = fortnight_response
        return result

    def add_fortnight_leave_deduction_log(self,leave_deduction,deviation_in_hours,result,last_attendance_date,employee,fortnight_start_date,fortnight_end_date):
        
        balance_al = result['total_available_balance']
        balance_cl = result['cl_balance']
        balance_el = result['el_balance']
        balance_sl = result['sl_balance']


        fd_count,hd = str(leave_deduction).split('.')
        #fd_count = 0
        #hd=1
        #hd_count = 0
        
        #fortnight_end_date = '2020-12-24'
        print('fd_count',fd_count,type(fd_count),'hd_count',hd,type(hd))
        

        leave_type = 'AB'
        fortnight_day_remarks = leave_type+'(Absent)'

        attendance_details = PmsAttendance.objects.filter(
            #is_present=True,
            Q(
                date__date__gte=fortnight_start_date,
                date__date__lte=fortnight_end_date,
                employee=employee,
                is_deleted=False
            )
            |
            Q(
                is_present=False,
                pk__in = (
                    PmsAttandanceDeviation.objects.filter(
                        attandance__employee=employee,
                        attandance__date__date__gte=fortnight_start_date,
                        attandance__date__date__lte=fortnight_end_date,
                        approved_status = 4,
                        is_requested = False
                        )
                )
            )
            ).order_by('-date__date')

        #print('attendance_details',attendance_details.query,attendance_details)
        #logger.info('attendance_details')
        
        if fd_count!='0' and hd!='0':
            #print('fdhdfdhdfdhdfdhjd',)
            attendance_ids = list()
            if fd_count!='0':
                if attendance_details:
                    attendance_details_fd = attendance_details[:int(fd_count)]
                    #print('attendance_details_fd',attendance_details_fd,type(attendance_details_fd))
                    for attendance in attendance_details_fd :
                        attendance_ids.append(attendance.id)
                        if employee.cu_user.salary_type.st_code == 'FF' or employee.cu_user.salary_type.st_code == 'EE':
                            if balance_al > 0:
                                leave_type = 'AL'
                                fortnight_day_remarks = leave_type +'(All Leave)'
                                balance_al = balance_al - 1
                            else:
                                leave_type = 'AB'
                                fortnight_day_remarks = leave_type +'(Absent)'    
                            
                        if employee.cu_user.salary_type.st_code == 'CC' or employee.cu_user.salary_type.st_code == 'DD':
                            if balance_cl > 0:
                                leave_type = 'CL'
                                fortnight_day_remarks = leave_type +'(Casual Leave)'
                                balance_cl = balance_cl - 1
                            elif balance_el > 0:
                                leave_type = 'EL'
                                fortnight_day_remarks = leave_type +'(Earn Leave)'
                                balance_el = balance_el - 1
                            elif balance_sl > 0:
                                leave_type = 'SL' 
                                fortnight_day_remarks = leave_type +'(Sick Leave)'
                                balance_sl = balance_sl - 1
                            else:
                                leave_type = 'AB'
                                fortnight_day_remarks = leave_type +'(Absent)' 
                            
                        if employee.cu_user.salary_type.st_code == 'BB':
                            if balance_cl > 0:
                                leave_type = 'CL'
                                fortnight_day_remarks = leave_type +'(Casual Leave)'
                                balance_cl = balance_cl - 1 
                            elif balance_el > 0:
                                leave_type = 'EL'
                                fortnight_day_remarks = leave_type +'(Earn Leave)'
                                balance_el = balance_el - 1
                            else:
                                leave_type = 'AB'
                                fortnight_day_remarks = leave_type +'(Absent)' 
                        self.insert_leave_data_to_model(employee,attendance,leave_type,'FD',fortnight_day_remarks)
            if hd!='0':
                attendance_details = attendance_details.exclude(pk__in=attendance_ids)
                if attendance_details:
                    attendance_details = attendance_details[:1][0]
                    #print('attendance_details_hd',attendance_details)
                    if employee.cu_user.salary_type.st_code == 'FF' or employee.cu_user.salary_type.st_code == 'EE':
                        if balance_al > 0:
                            leave_type = 'AL'
                            fortnight_day_remarks = leave_type +'(All Leave)'
                            balance_al = balance_al - 0.5 
                        else:
                            leave_type = 'AB' 
                            fortnight_day_remarks = leave_type +'(Absent)'      
                        
                    if employee.cu_user.salary_type.st_code == 'CC' or employee.cu_user.salary_type.st_code == 'DD':
                        if balance_cl > 0:
                            leave_type = 'CL'
                            fortnight_day_remarks = leave_type +'(Casual Leave)'
                            balance_cl = balance_cl - 0.5
                        elif balance_el > 0:
                            leave_type = 'EL'
                            fortnight_day_remarks = leave_type +'(Earn Leave)'
                            balance_el = balance_el - 0.5
                        elif balance_sl > 0:
                            leave_type = 'SL'
                            fortnight_day_remarks = leave_type +'(Sick Leave)'
                            balance_sl = balance_sl - 0.5
                        else:
                            leave_type = 'AB'
                            fortnight_day_remarks = leave_type +'(Absent)'   
                        
                    if employee.cu_user.salary_type.st_code == 'BB':
                        if balance_cl > 0:
                            leave_type = 'CL'
                            fortnight_day_remarks = leave_type +'(Casual Leave)'
                            balance_cl = balance_cl - 0.5 
                        elif balance_el > 0:
                            leave_type = 'EL'
                            fortnight_day_remarks = leave_type +'(Earn Leave)'
                            balance_el = balance_el - 0.5
                        else:
                            leave_type = 'AB'
                            fortnight_day_remarks = leave_type +'(Absent)'   
                    self.insert_leave_data_to_model(employee,attendance_details,leave_type,'HD',fortnight_day_remarks)

        if fd_count!='0' and hd=='0':
            #print('fdddddddddddddddddddddddddddddddddddd')
            if attendance_details:
                attendance_details = attendance_details[:int(fd_count)]
                for attendance in attendance_details :
                    if employee.cu_user.salary_type.st_code == 'FF' or employee.cu_user.salary_type.st_code == 'EE':
                        if balance_al > 0:
                            leave_type = 'AL'
                            fortnight_day_remarks = leave_type +'(All Leave)'
                            balance_al = balance_al - 1 
                        else:
                            leave_type = 'AB'
                            fortnight_day_remarks = leave_type +'(Absent)'    
                        
                    if employee.cu_user.salary_type.st_code == 'CC' or employee.cu_user.salary_type.st_code == 'DD':
                        if balance_cl > 0:
                            leave_type = 'CL'
                            fortnight_day_remarks = leave_type +'(Casual Leave)'
                            balance_cl = balance_cl - 1
                        elif balance_el > 0:
                            leave_type = 'EL'
                            fortnight_day_remarks = leave_type +'(Earn Leave)'
                            balance_el = balance_el - 1
                        elif balance_sl > 0:
                            leave_type = 'SL'
                            fortnight_day_remarks = leave_type +'(Sick Leave)' 
                            balance_sl = balance_sl - 1
                        else:
                            leave_type = 'AB'
                            fortnight_day_remarks = leave_type +'(Absent)'
                        
                    if employee.cu_user.salary_type.st_code == 'BB':
                        if balance_cl > 0:
                            leave_type = 'CL'
                            fortnight_day_remarks = leave_type +'(Casual Leave)'
                            balance_cl = balance_cl - 1 
                        elif balance_el > 0:
                            leave_type = 'EL'
                            fortnight_day_remarks = leave_type +'(Earn Leave)'
                            balance_el = balance_el - 1
                        else:
                            leave_type = 'AB'
                            fortnight_day_remarks = leave_type +'(Absent)'
                    self.insert_leave_data_to_model(employee,attendance,leave_type,'FD',fortnight_day_remarks)

        if hd!='0' and fd_count == '0':
            #print('hdddddddddddddddddddddddddddddddddddddddddddddddd')
            if attendance_details:
                attendance = attendance_details[0]
                if employee.cu_user.salary_type.st_code == 'FF' or employee.cu_user.salary_type.st_code == 'EE':
                    if balance_al > 0:
                        leave_type = 'AL'
                        fortnight_day_remarks = leave_type +'(All Leave)'
                        balance_al = balance_al - 0.5 
                    else:
                        leave_type = 'AB'
                        fortnight_day_remarks = leave_type +'(Absent)'    
                    
                if employee.cu_user.salary_type.st_code == 'CC' or employee.cu_user.salary_type.st_code == 'DD':
                    if balance_cl > 0:
                        leave_type = 'CL'
                        fortnight_day_remarks = leave_type +'(Casual Leave)'
                        balance_cl = balance_cl - 0.5
                    elif balance_el > 0:
                        leave_type = 'EL'
                        fortnight_day_remarks = leave_type +'(Earn Leave)'
                        balance_el = balance_el - 0.5
                    elif balance_sl > 0:
                        leave_type = 'SL' 
                        fortnight_day_remarks = leave_type +'(Sick Leave)'
                        balance_sl = balance_sl - 0.5
                    else:
                        leave_type = 'AB'
                        fortnight_day_remarks = leave_type +'(Absent)'
                    
                if employee.cu_user.salary_type.st_code == 'BB':
                    if balance_cl > 0:
                        leave_type = 'CL'
                        fortnight_day_remarks = leave_type +'(Casual Leave)'
                        balance_cl = balance_cl - 0.5 
                    elif balance_el > 0:
                        leave_type = 'EL'
                        fortnight_day_remarks = leave_type +'(Earn Leave)'
                        balance_el = balance_el - 0.5
                    else:
                        leave_type = 'AB'
                        fortnight_day_remarks = leave_type +'(Absent)'

                self.insert_leave_data_to_model(employee,attendance,leave_type,'HD',fortnight_day_remarks)

    def insert_leave_data_to_model(self,employee,attendance,leave_type,deviation_type,fortnight_day_remarks):
        duration = PmsAttandanceDeviation.objects.only('duration').get(attandance=attendance).duration
        _,created = PmsAttandanceFortnightLeaveDeductionLog.objects.get_or_create(
                            sap_personnel_no = employee.cu_user.sap_personnel_no,
                            employee = employee,
                            attendance_date = attendance.date,
                            attendance = attendance,
                            duration = duration,
                            deviation_type = deviation_type,
                            leave_type = leave_type,
                            remarks = 'Auto Deducted Due To Adjusted Fortnight Attendance',
                            created_by_id = 1
                            )
        self.insert_fortnight_day_remarks_to_attendance(employee,attendance,deviation_type,leave_type,fortnight_day_remarks)
    
    def insert_fortnight_day_remarks_to_attendance(self,employee,attendance,deviation_type,leave_type,fortnight_day_remarks):
        return PmsAttendance.objects.filter(
            pk=attendance.id).update(
            fortnight_deviation_type = deviation_type,
            fortnight_leave_type = leave_type,
            fortnight_day_remarks=fortnight_day_remarks
            )

    def auto_approved_hd_fd_by_user(self, date_object=None, user=None):
        deviation_requests = PmsAttandanceDeviation.objects.filter(
            (Q(deviation_type = 'FD')| Q(deviation_type='HD')),
            #~Q(attandance__date__date='2020-12-25'),
            attandance__employee=user.cu_user,
            attandance__date__date__lte=date_object,
            is_requested = True,
            lock_status = False,
            approved_status = 1
            ).update(
                approved_status=2,
                remarks = 'Auto Approved',
                approved_at = datetime.now()
            )

        #print('deviation_requests',deviation_requests.query)
        #print('deviation_requests',deviation_requests)

    def auto_approved_od_by_user(self, date_object=None, user=None,fortnight=str,balance_al=float):

        check_report = False
        check_employee = False
        ## Reporting Head has not been approved ##
        deviation_details_pending_reporting_head = PmsAttandanceDeviation.objects.filter(
            approved_status = 1,
            deviation_type = 'OD',
            attandance__employee=user.cu_user,
            attandance__date__date__lte=date_object,
            lock_status = False,
            is_requested=True
            )
        for e_deviation_details in deviation_details_pending_reporting_head:
            self.all_leave_calculation_upto_applied_date(date_object=date_object, user=user,fortnight=fortnight)
            #print('deviation_requests',deviation_requests.query)

            if e_deviation_details.duration < 240:
                if balance_al > 0.0:
                    leave_type_changed_period='HD'
                    leave_type_changed = 'AL'
                else:
                    leave_type_changed_period='HD'
                    leave_type_changed = 'AB'
            else:
                if balance_al > 0.5:
                    leave_type_changed_period='FD'
                    leave_type_changed = 'AL'
                else:
                    leave_type_changed_period='FD'
                    leave_type_changed = 'AB'

            update_auto = PmsAttandanceDeviation.objects.filter(
                id=e_deviation_details.id,
                approved_status = 1,
                deviation_type = 'OD',
                attandance__employee=user.cu_user,
                attandance__date__date__lte=date_object,
                lock_status = False,
                is_requested=True
                ).update(
                leave_type_changed_period=leave_type_changed_period,
                leave_type_changed=leave_type_changed,
                approved_status=2,
                remarks='AUTO OD CONVERTED TO LEAVE & APPROVED'
                )
            check_report = True

            
        ## Employee has not been applied the deviation ##
        attendance_ids = PmsAttandanceDeviation.objects.filter(
            approved_status = 4,
            deviation_type = 'OD',
            attandance__employee=user.cu_user,
            attandance__date__date__lte=date_object,
            lock_status = False,
            is_requested=False
            ).values_list('attandance',flat=True).distinct()
        print('attendance_ids',attendance_ids)
        for attendance_id in attendance_ids:
            self.all_leave_calculation_upto_applied_date(date_object=date_object, user=user,fortnight=fortnight)
            duration_length = PmsAttandanceDeviation.objects.filter(
            attandance=attendance_id,
            approved_status = 4,
            deviation_type = 'OD',
            attandance__employee=user.cu_user,
            attandance__date__date__lte=date_object,
            lock_status = False,
            is_requested=False
            ).aggregate(Sum('duration'))['duration__sum']
            print('duration_length',duration_length)
            if duration_length is not None and duration_length < 240:
                if balance_al > 0.0:
                    deviation_type='HD'
                    leave_type = 'AL'
                else:
                    deviation_type='HD'
                    leave_type = 'AB'
            else:
                if balance_al > 0.5:
                    deviation_type='FD'
                    leave_type = 'AL'
                else:
                    deviation_type='FD'
                    leave_type = 'AB'

            update_auto = PmsAttandanceDeviation.objects.filter(
                attandance=attendance_id,
                approved_status = 4,
                deviation_type = 'OD',
                attandance__employee=user.cu_user,
                attandance__date__date__lte=date_object,
                lock_status = False,
                is_requested=False
                ).update(
                deviation_type=deviation_type,
                leave_type=leave_type,
                justification='AUTO',
                is_requested=True,
                approved_status=2,
                remarks='AUTO LEAVE APPROVED'
                )
            check_employee = True
        # if check_employee and check_report:
        #     return True
        # else:
        #     return False

    def update_lock_status(self,employee,fortnight_start_date,fortnight_end_date):
        PmsAttandanceDeviation.objects.filter(
            attandance__date__date__gte=fortnight_start_date,
            attandance__date__date__lte=fortnight_end_date,
            attandance__employee=employee
            ).update(lock_status=True)

    def get(self, request, *args, **kwargs):

        '''
            1) Auto approved HD or FD.
            2) Auto OD approved.[removed the functionality ]
            2) Leave Auto Deducted Due To Adjusted Fortnight Attendance. 

            Note : Before execute the cron or api please check the below points.
                    1) All deviation has been applied.
                    2) All OD has been approved by his/her reporting head.
                    3) Check the fortnight date in Attendance Month Master Table becasue that is very important.
                    4) fortnight parameter should be checked it's denote which fortnight first(1) and second(2).
                    5) current date parameter denote the fortnight date for fortnight 1 and 2 accordingly.
                    6) If you send employee id then it's only excute for employee else it's excute for all users.
        '''


        
        fortnight =  self.request.query_params.get('fortnight', None)
        employee_id= self.request.query_params.get('employee_id', None)
        current_date = self.request.query_params.get('current_date', None)
        filter = dict()
        exclude = {
        'cu_user_id__in':(3345,2512,),
        'sap_personnel_no__in':('37200077','37200082','37200085','37200086','37200087','37200091','37200092','37200094','37200098','37200099','37200118','37200120','37200122','37200148','37200149','78200033','80000032',)
        }



        if employee_id:
            filter['cu_user_id'] = employee_id

        if not current_date:
            current_date = datetime.now().date()
        else:
            current_date = datetime.strptime(current_date, '%Y-%m-%d').date()

        current_month = current_date.month
        current_year = current_date.year

        total_result = list()
        data_dict = dict()
       
        total_month_grace = AttendenceMonthMaster.objects.filter(month=current_month,month_end__year=current_year,is_deleted=False).values(
            'grace_available','year_start_date','year_end_date','month','month_start','month_end','fortnight_date')
       
        #print('total_month_grace',total_month_grace)

        if fortnight == '1':
            date_object = total_month_grace[0]['fortnight_date'].date()
        else:
            date_object = total_month_grace[0]['month_end'].date()

        #print('date_object',date_object)


        with transaction.atomic():
            if current_date == date_object:
                user_list = TCoreUserDetail.objects.filter(
                    ~Q(cu_user_id__in=(3345,2512,)),
                    ~Q(sap_personnel_no__in=('37200030','37200071','37200077','37200082','37200085','37200086','37200087','37200091','37200092','37200094','37200098','37200099','37200118','37200120','37200122','37200148','37200149','78200033','80000032','37100001',)),
                    (
                        Q(
                            Q(termination_date__isnull=False)&Q(
                                Q(
                                    Q(termination_date__year=current_date.year)&Q(termination_date__month=current_date.month)
                                )|
                                Q(termination_date__date__gte=current_date)
                            )
                        )|
                        Q(Q(termination_date__isnull=True),cu_is_deleted=False)
                    ),
                    attendance_type='PMS',
                    user_type='User',
                    **filter,
                    )

                #print('user_list',user_list.query)
                for user in user_list:
                    self.auto_approved_hd_fd_by_user(date_object=date_object, user=user)
                    result = self.get_flexi_hours_calculation(date_object=date_object, user=user,fortnight=fortnight)
                    #result = list()
                    total_result.append(result)
        
        data_dict['result'] = total_result
        if result:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_SUCCESS
        elif len(result) == 0:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_NO_DATA
        else:
            data_dict['request_status'] = 0
            data_dict['msg'] = settings.MSG_ERROR
        return Response(data_dict)


class PmsAttendanceLeaveBalanceTransferUserView(APIView):
    permission_classes = [AllowAny]
    
    def get_leave_apply_upto_transfer_date(self, attendance_type_present, date_object=None, user=None):

        current_financial_year_details = get_current_financial_year_details()

        #raise APIException('asasasa')
        
        leave_details = PmsAttandanceDeviation.objects.filter(
            (Q(approved_status=1)|Q(approved_status=2)|Q(approved_status=3)),
            (
                (
                    Q(leave_type_changed_period__isnull=False)&
                    (
                        Q(leave_type_changed_period='FD')|Q(leave_type_changed_period='HD')
                    )
                )
                |
                (
                    Q(leave_type_changed_period__isnull=True)&
                    (
                        Q(deviation_type='FD')|Q(deviation_type='HD')
                    )
                )
            ),
            from_time__date__gte=current_financial_year_details['month_start__date'],
            from_time__date__lte=date_object,
            attandance__employee=user.cu_user,
            is_requested=True,
            is_deleted=False
            )

        #print('attendence_daily_data',attendence_daily_data.query)
        #print('attendence_daily_data',attendence_daily_data)

        self.insert_to_UserAttendanceTypeTransferHistory(user,attendance_type_present,date_object)
        self.insert_to_PmsAttandanceLeaveBalanceTransferLog(leave_details,user)
        
        result = {
                "employee_id":user.cu_user.id,
                "employee_username":user.cu_user.username,
                "month_start":current_financial_year_details['month_start__date'],
                "month_end":current_financial_year_details['month_end__date'],
                "attendance_type":user.attendance_type,
                "leave_details":leave_details.values()
            }
        return result

    def insert_to_UserAttendanceTypeTransferHistory(self,user,attendance_type_present,date_object):
        details,_ = UserAttendanceTypeTransferHistory.objects.get_or_create(
            user = user.cu_user,
            attendance_type_prev = user.attendance_type,
            transfer_date = date_object,
            attendance_type_present = attendance_type_present
            )
        self.update_UserAttendanceType(user,attendance_type_present)
        return True

    def update_UserAttendanceType(self,user,attendance_type_present):
        return TCoreUserDetail.objects.filter(pk=user.id,cu_is_deleted=False).update(attendance_type=attendance_type_present)

    def insert_to_PmsAttandanceLeaveBalanceTransferLog(self,leave_details,user):
        for each in leave_details:
            PmsAttandanceLeaveBalanceTransferLog.objects.get_or_create(
                sap_personnel_no=user.sap_personnel_no,
                employee = user.cu_user,
                attendance = each.attandance,
                attendance_date = each.attandance.date,
                attendance_deviation = each,
                duration = each.duration,
                deviation_type = each.deviation_type,
                leave_type = each.leave_type,
                approved_status = each.approved_status,
                approved_at = each.approved_at
                )
        return True
        
    
    def get(self, request, *args, **kwargs):

        '''
            Note : Leave Balance insert for transfer a user from PMS to HRMS upto transfer date 
                    1) Check PmsAttandanceDeviation and PmsAttandance model to check leave which are approved,pending,reject.
                        carry forward + apply leave + advance + special + fortnight  
                        [apply leave + fortnight = consider]


        '''

        employee_id= self.request.query_params.get('employee_id', None)
        transfer_date = self.request.query_params.get('transfer_date', None)
        attendance_type_present = self.request.query_params.get('attendance_type_present', None)

        filter = dict()

        if employee_id:
            filter['cu_user_id'] = employee_id

        if not transfer_date:
            transfer_date = datetime.now().date()
        else:
            transfer_date = datetime.strptime(transfer_date, '%Y-%m-%d').date()

        current_month = transfer_date.month
        current_year = transfer_date.year

        total_result = list()
        data_dict = dict()

        with transaction.atomic():     
            user = TCoreUserDetail.objects.filter(
                termination_date__isnull = True,
                cu_is_deleted = False,
                cu_user__is_active = True,
                user_type='User',
                **filter,
                )

            print('user',user)
            if user:
                user = user[0]
            result = self.get_leave_apply_upto_transfer_date(attendance_type_present,date_object=transfer_date, user=user)
            total_result.append(result)
        
        data_dict['result'] = total_result
        if total_result:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_SUCCESS
        elif len(total_result) == 0:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_NO_DATA
        else:
            data_dict['request_status'] = 0
            data_dict['msg'] = settings.MSG_ERROR
        return Response(data_dict)
