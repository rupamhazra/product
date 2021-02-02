from django.shortcuts import render
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from pms.models import *
from pms.serializers import *
import time
from multiplelookupfields import MultipleFieldLookupMixin
from rest_framework.views import APIView
from django.conf import settings
from pagination import CSLimitOffestpagination,CSPageNumberPagination,OnOffPagination
from rest_framework import filters
import calendar
from datetime import datetime
import collections
from rest_framework.exceptions import APIException
import pandas as pd
import numpy as np
from django_filters.rest_framework import DjangoFilterBackend
from users.models import TCoreUserDetail
from custom_decorator import *
from rest_framework.parsers import FileUploadParser
import os
from pms.custom_filter import *
from global_function import getHostWithPort

'''
    For Knox 
    Author : Rupam Hazra
    Date : 16.03.2020
'''
from knox.auth import TokenAuthentication
from rest_framework import permissions
from knox.models import AuthToken

#:::::::::::: PROJECTS ::::::::::::::::::::::::::::#

class DailyExpenceAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsDailyExpence.objects.filter(is_deleted=False).order_by('-id')
    serializer_class=DailyExpenceAddSerializer
    pagination_class = OnOffPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DailyExpenceAddSerializer
        
        return DailyExpenceListSerializer


    @response_modify_decorator_post
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
    
    @response_modify_decorator_list_or_get_after_execution_for_onoff_pagination
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
  
class DailyExpenceListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsDailyExpence.objects.filter(is_deleted=False)
    serializer_class=DailyExpenceListSerializer
    pagination_class = OnOffPagination

    def get_queryset(self):
        filter = {}
        exclude = {}
        sort_field='-id'

        approval_level = self.request.query_params.get('approval_level', None) # for approval [list]
        report = self.request.query_params.get('report', None) # for approval [Report]
        approval_person = self.request.query_params.get('approval_person', None) # for approval [list]
        
        if approval_level:
            login_user_id = self.request.user.id
            #print('login_user_id',self.request.user)
            login_user_level = None
            login_user_level_details = PmsDailyExpenceApprovalConfiguration.objects.filter(
                user = self.request.user,
                level=approval_person,
                is_deleted=False
                )
            #print('login_user_level_details1111',login_user_level_details)
            if login_user_level_details:
                login_user_level = login_user_level_details.values('id','level','project')[0]
                login_user_level_ids = login_user_level_details.values_list('id',flat=True)
                login_user_level_projects = login_user_level_details.values_list('project',flat=True)
                #print('login_user_level',login_user_level)
                if login_user_level['level'] == 'Project Manager':
                    filter['status'] = 'Pending For Project Manager Approval'
                    filter['created_by__in'] = PmsProjectUserMapping.objects.filter(
                        project__in=login_user_level_projects,is_deleted=False).values_list('user',flat=True)
                    if report:
                        del filter['status']
                        filter['pk__in'] = PmsDailyExpenceApproval.objects.filter(
                            approval_user_level__in=login_user_level_ids,
                            approval_status__in=('Approve','Reject','Pending',),
                            is_deleted=False
                            ).values_list('daily_expence',flat=True)
                    
                if login_user_level['level'] == 'Project Coordinator':
                    filter['status'] = 'Pending For Project Coordinator Approval'
                    filter['created_by__in'] = PmsProjectUserMapping.objects.filter(
                        project__in=login_user_level_projects,is_deleted=False).values_list('user',flat=True)

                    if report:
                        del filter['status']
                        filter['pk__in'] = PmsDailyExpenceApproval.objects.filter(
                            (Q(daily_expence__status='Pending For Project Coordinator Approval')|Q(approval_status__in=('Approve','Reject',))),
                            approval_user_level__in=login_user_level_ids,
                            is_deleted=False
                            ).values_list('daily_expence',flat=True)

                if login_user_level['level'] == 'HO':
                    filter['status'] = 'Pending For HO Approval'
                    if report:
                        del filter['status']
                        filter['pk__in'] = PmsDailyExpenceApproval.objects.filter(
                            (Q(daily_expence__status='Pending For HO Approval')|Q(approval_status__in=('Approve','Reject',))),
                            approval_user_level__in=login_user_level_ids,
                            is_deleted=False
                            ).values_list('daily_expence',flat=True)

                if login_user_level['level'] == 'Account':
                    filter['status'] = 'Pending For Account Approval'
                    if report:
                        del filter['status']
                        filter['status__in'] = ['Pending For Account Approval','Approve']
                        filter['pk__in'] = PmsDailyExpenceApproval.objects.filter(
                            approval_user_level__in=login_user_level_ids,
                            approval_status__in=('Approve','Reject','Pending',),
                            is_deleted=False
                            ).values_list('daily_expence',flat=True)

            else:
                return list()

        #print('login_user_level_details',login_user_level)
        
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        status = self.request.query_params.get('status', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        employee_id = self.request.query_params.get('employee_id', None) # for my conveyance
        project = self.request.query_params.get('project', None)
        is_paid = self.request.query_params.get('is_paid', None)
        #date = self.request.query_params.get('date', None)
       

        ## Filter section

        if employee_id:
            filter['created_by__id'] = employee_id

        if status:
            filter['status__in'] = status.split(',')

        if start_date and end_date:
            filter['date__date__gte'] = start_date
            filter['date__date__lte'] = end_date

        if is_paid:
            filter['is_paid'] = is_paid

        if project:
            filter['project'] = project

        ## Sorting section
        if field_name and order_by:
            
            if field_name == 'created_by' and order_by == 'asc':
                sort_field ='created_by__username'

            if field_name =='created_by' and order_by=='desc':
                sort_field ='-created_by__username'

            if field_name == 'amount' and order_by == 'asc':
                sort_field ='amount'

            if field_name =='amount' and order_by=='desc':
                sort_field ='-amount'

            if field_name =='date' and order_by=='asc':
                sort_field='date'

            if field_name =='date' and order_by=='desc':
                sort_field='-date'

        #print('filter',filter)
        queryset = self.queryset.filter(**filter).exclude(**exclude).order_by(sort_field)
        #print('queryset',queryset.query)
        #time.sleep(5)
        return queryset


    @response_modify_decorator_list_or_get_after_execution_for_onoff_pagination
    def list(self, request, *args, **kwargs):
        response = super(__class__, self).list(self, request, args, kwargs)
        return response

class DailyExpenceListDownloadView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsDailyExpence.objects.filter(is_deleted=False)
    serializer_class=DailyExpenceListSerializer

    def get_queryset(self):
        filter = {}
        exclude = {}
        sort_field='-id'

        approval_level = self.request.query_params.get('approval_level', None) # for approval [list]
        report = self.request.query_params.get('report', None) # for approval [Report]
        approval_person = self.request.query_params.get('approval_person', None) # for approval [list]
        
        if approval_level:
            login_user_id = self.request.user.id
            #print('login_user_id',self.request.user)
            login_user_level = None
            login_user_level_details = PmsDailyExpenceApprovalConfiguration.objects.filter(
                user = self.request.user,
                level=approval_person,
                is_deleted=False
                )
            #print('login_user_level_details1111',login_user_level_details)
            if login_user_level_details:
                login_user_level = login_user_level_details.values('id','level','project')[0]
                login_user_level_ids = login_user_level_details.values_list('id',flat=True)
                login_user_level_projects = login_user_level_details.values_list('project',flat=True)
                #print('login_user_level',login_user_level)
                if login_user_level['level'] == 'Project Manager':
                    filter['status'] = 'Pending For Project Manager Approval'
                    filter['created_by__in'] = PmsProjectUserMapping.objects.filter(
                        project__in=login_user_level_projects,is_deleted=False).values_list('user',flat=True)
                    if report:
                        del filter['status']
                        filter['pk__in'] = PmsDailyExpenceApproval.objects.filter(
                            approval_user_level__in=login_user_level_ids,
                            approval_status__in=('Approve','Reject','Pending',),
                            is_deleted=False
                            ).values_list('daily_expence',flat=True)
                    
                if login_user_level['level'] == 'Project Coordinator':
                    filter['status'] = 'Pending For Project Coordinator Approval'
                    filter['created_by__in'] = PmsProjectUserMapping.objects.filter(
                        project__in=login_user_level_projects,is_deleted=False).values_list('user',flat=True)

                    if report:
                        del filter['status']
                        filter['pk__in'] = PmsDailyExpenceApproval.objects.filter(
                            (Q(daily_expence__status='Pending For Project Coordinator Approval')|Q(approval_status__in=('Approve','Reject',))),
                            approval_user_level__in=login_user_level_ids,
                            is_deleted=False
                            ).values_list('daily_expence',flat=True)

                if login_user_level['level'] == 'HO':
                    filter['status'] = 'Pending For HO Approval'
                    if report:
                        del filter['status']
                        filter['pk__in'] = PmsDailyExpenceApproval.objects.filter(
                            (Q(daily_expence__status='Pending For HO Approval')|Q(approval_status__in=('Approve','Reject',))),
                            approval_user_level__in=login_user_level_ids,
                            is_deleted=False
                            ).values_list('daily_expence',flat=True)

                if login_user_level['level'] == 'Account':
                    filter['status'] = 'Pending For Account Approval'
                    if report:
                        del filter['status']
                        filter['status__in'] = ['Pending For Account Approval','Approve']
                        filter['pk__in'] = PmsDailyExpenceApproval.objects.filter(
                            approval_user_level__in=login_user_level_ids,
                            approval_status__in=('Approve','Reject','Pending',),
                            is_deleted=False
                            ).values_list('daily_expence',flat=True)

            else:
                return list()

        #print('login_user_level_details',login_user_level)
        
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        status = self.request.query_params.get('status', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        employee_id = self.request.query_params.get('employee_id', None) # for my conveyance
        project = self.request.query_params.get('project', None)
        is_paid = self.request.query_params.get('is_paid', None)
        #date = self.request.query_params.get('date', None)
       

        ## Filter section

        if employee_id:
            filter['created_by__id'] = employee_id

        if status:
            filter['status__in'] = status.split(',')

        if start_date and end_date:
            filter['date__date__gte'] = start_date
            filter['date__date__lte'] = end_date

        if is_paid:
            filter['is_paid'] = is_paid

        if project:
            filter['project'] = project

        ## Sorting section
        if field_name and order_by:
            
            if field_name == 'created_by' and order_by == 'asc':
                sort_field ='created_by__username'

            if field_name =='created_by' and order_by=='desc':
                sort_field ='-created_by__username'

            if field_name == 'amount' and order_by == 'asc':
                sort_field ='amount'

            if field_name =='amount' and order_by=='desc':
                sort_field ='-amount'

            if field_name =='date' and order_by=='asc':
                sort_field='date'

            if field_name =='date' and order_by=='desc':
                sort_field='-date'

        #print('filter',filter)
        queryset = self.queryset.filter(**filter).exclude(**exclude).order_by(sort_field)
        #print('queryset',queryset.query)
        #time.sleep(5)
        return queryset


    def list(self, request, *args, **kwargs):
        response = super(__class__, self).list(self, request, args, kwargs)
        data_list = list()
        #print('response.data',response.data)
        count = 0
        
        for data in response.data:
            count += 1 
            items = ','.join(['{0}'.format(item['item']) for item in data['items']])
            
           

            data_list.append(
            [
            count,
            data['employee_name'],
            data['project_details']['name'],
            data['date'][:10],
            data['voucher_no'],
            items,
            data['paid_to'],
            data['amount'],
            data['approve_amount'],
            data['status'],
            data['current_level_of_approval_details']['approved_by'],
            data['current_level_of_approval_details']['status'],
            'Yes' if data['is_paid'] else 'No',
            
            ]
            )

        file_name = ''
        if data_list:
            if os.path.isdir('media/attendance/daily_expence/document'):
                file_name = 'media/attendance/daily_expence/document/daily_expence_report.xlsx'
                file_path = settings.MEDIA_ROOT_EXPORT + file_name
            else:
                os.makedirs('media/attendance/daily_expence/document')
                file_name = 'media/attendance/daily_expence/document/daily_expence_report.xlsx'
                file_path = settings.MEDIA_ROOT_EXPORT + file_name

                print('file_path',file_path)

            final_df = pd.DataFrame(
                data_list, 
                columns=[
                'SL No.',
                'Employee Name',
                'Project',
                'Date',
                'Voucher No',
                'Items',
                'Paid To',
                'Amount',
                'Approved Amount',
                'Status',
                'Current Level of Approved By',
                'Current Level of Approved Status',
                'Paid Status'
                
                ]
                )
            
            #Panda with xlsxwritter
            writer = pd.ExcelWriter(file_path, engine='xlsxwriter')
            final_df.to_excel(writer, startrow=1, startcol=0,index = False, header=False)
            workbook  = writer.book
            worksheet = writer.sheets['Sheet1']
            style_property_1 = workbook.add_format({'bg_color':'#6495ED','font_color':'white','valign': 'vcenter'})
            header_fmt = workbook.add_format({'bg_color':'#6B8E23','font_color':'white'})
            red_font = workbook.add_format({'font_color':'red'})
            green_font = workbook.add_format({'font_color':'green'})

            # Header row color set
            for col_num, value in enumerate(final_df.columns.values):
                worksheet.write(0, col_num, value, header_fmt)
            

            # Paid column color set                                     
            worksheet.conditional_format('M2:M'+str(count+1), {'type': 'cell',
                                         'criteria': '==',
                                         'value': '"Yes"',
                                         'format': green_font})
            worksheet.conditional_format('M2:M'+str(count+1), {'type': 'cell',
                                         'criteria': '==',
                                         'value': '"No"',
                                         'format': red_font})
            writer.save()

        url = getHostWithPort(request) + file_name if file_name else None

        if url:                    
            return Response({'request_status':1,'msg':'Success', 'url': url})
        else:
            return Response({'request_status':0,'msg':'Not Found', 'url': url})  

class DailyExpenceStatusUpdateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsDailyExpence.objects.filter(is_deleted=False)
    serializer_class=DailyExpenceStatusUpdateSerializer

    @response_modify_decorator_post
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
  
class DailyExpencePaymentUpdateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsDailyExpence.objects.filter(is_deleted=False)
    serializer_class=DailyExpencePaymentUpdateSerializer

    @response_modify_decorator_post
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
