from django.http import JsonResponse
from django.views.generic import View
from rest_framework.pagination import LimitOffsetPagination,PageNumberPagination
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
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
from pagination import CSLimitOffestpagination,CSPageNumberPagination,CustomPagination,OnOffPagination
from rest_framework import filters
import calendar
from datetime import datetime
from holidays.models import *
# import collectionsPurchaseRequisitions
from rest_framework.exceptions import APIException
import pandas as pd
import numpy as np
from django_filters.rest_framework import DjangoFilterBackend
from master.serializers import UserModuleWiseListSerializer
from master.models import TMasterModuleRole
from users.models import TCoreUserDetail
from custom_decorator import *
from rest_framework.parsers import FileUploadParser
import os
from pms.custom_filter import *
from datetime import datetime
from pagination import CSLimitOffestpagination,CSPageNumberPagination
import calendar
from datetime import datetime,timedelta
from django.db.models import Sum
from django.db.models import Q
import re
import csv
import json
from pandas.io.json import json_normalize
from pandas import DataFrame
from global_function import department,designation,userdetails,getHostWithPort,raw_query_extract,get_time_diff,get_pagination_offset
from collections import OrderedDict 
import time
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, tables
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus.flowables import BalancedColumns
from django.db.models import Count
from dateutil.relativedelta import relativedelta
'''
    For Knox 
    Author : Rupam Hazra
    Date : 16.03.2020
'''
from knox.auth import TokenAuthentication
from rest_framework import permissions
from knox.models import AuthToken
import decimal


#::::::::::  PMS EXECUTION PLANNING AND REPORT ::::::::#
class ExecutionProjectPlaningAdd(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionProjectPlaningMaster.objects.all()
    serializer_class = ExecutionProjectPlaningAddSerializer


class ExecutionProjectPlaningview(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    # queryset = PmsExecutionProjectPlaningMaster.objects.all()
    serializer_class = ExecutionProjectPlaningviewSerializer

    def get(self, request, *args, **kwargs):
        response = dict()
        project_id = self.kwargs['project_id']
        site_id = self.kwargs['site_id']
        ppm_d = PmsExecutionProjectPlaningMaster.objects.filter(project=project_id, site_location=site_id).values(
            'id', 'project', 'site_location', 'name_of_work',
            'is_deleted', 'created_by', 'owned_by')
        site_details = PmsSiteProjectSiteManagement.objects.filter(id=site_id). \
            values('name', 'company_name')
        project_duration = PmsProjects.objects.filter(id=project_id). \
            values('start_date', 'end_date')
        project_details_of_site = {'site_details': site_details, 'project_duration': project_duration}
        response['project_details_of_site'] = project_details_of_site
        # print('ini_d',ini_d)
        if ppm_d:
            for d in ppm_d:
                ini_id = d['id']
                response['id'] = d['id']
                response['name_of_work'] = d['name_of_work']
                response['is_deleted'] = d['is_deleted']
                response['created_by'] = d['created_by']
                response['owned_by'] = d['owned_by']
            field_label_value_d = PmsExecutionProjectPlaningFieldLabel.objects.filter(
                project_planning=ini_id)
            #print("field_label_value_d:::",field_label_value_d)
            field_label_value = []
            for j in field_label_value_d:
                field_value = []
                field_label_value_v = PmsExecutionProjectPlaningFieldValue.objects.filter(
                    project_planning=ini_id,
                    initial_field_label=j.id)
                # print("field_label_value_v:::",field_label_value_v)
                for i in field_label_value_v:
                    if j.field_label == "Activities" or j.field_label == "activities":
                        #print(i.field_value)
                        activity_description=PmsExecutionPurchasesRequisitionsActivitiesMaster.objects.filter(id=i.field_value).values('id','description')
                        #print("activity_description:::::",activity_description)
                        # activity_description[0]:
                        if activity_description:
                            field_value.append([x for x in activity_description][0])
                        else:""
                    else:
                        field_value.append(i.field_value)
                field_label_val_dict = {
                    "field_label": j.field_label,
                    "field_value": field_value
                }
                field_label_value.append(field_label_val_dict)
            response['field_label_value'] = field_label_value
        else:
            response = ''
        return Response({'result': response})



class ExecutionDailyReportProgressAdd(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionDailyProgress.objects.all()
    serializer_class = DailyReportProgressSerializeradd
    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        return response

    @response_modify_decorator_post
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class ExecutionDailyReportLabourAdd(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionDailyProgress.objects.all()
    serializer_class = DailyReportlabourSerializeradd
    @response_modify_decorator_post
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class ExecutionDailyReportPandMAdd(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionDailyProgress.objects.all()
    serializer_class = DailyReportPandMSerializeradd
    @response_modify_decorator_post
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class ExecutionDailyReportProgressView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionDailyProgress.objects.filter(is_deleted=False).order_by('-id')
    serializer_class = DailyReportProgressSerializer

    def get_queryset(self):
        project_id = self.kwargs["project_id"]
        site_id = self.kwargs["site_id"]
        filter = {}

        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        date = self.request.query_params.get('date', None)
        report_type = int(self.request.query_params.get('report_type', None))

        if date:
            date_object = datetime.strptime(date, '%Y-%m-%d').date()
            filter['date_entry__year'] = date_object.year
            filter['date_entry__month'] = date_object.month
            filter['date_entry__day'] = date_object.day
            #queryset = self.queryset.filter(project_id=project_id, site_location=site_id,type_of_report=report_type, **filter)

       
        if start_date and end_date:
            start_object = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_object = datetime.strptime(end_date, '%Y-%m-%d').date()
            filter['date_entry__gte'] = start_object
            filter['date_entry__lte'] = end_object

        queryset = self.queryset.filter(project_id=project_id, site_location=site_id,type_of_report=report_type, **filter)
        return queryset

    #@response_modify_decorator_get_single_after_execution
    def get(self, request, *args, **kwargs):
        response = super(self.__class__, self).get(self, request, args, kwargs)
        #print("response",response.data)
        data_list = list()
        data1 = dict()
        data_dict = {}
        execution_daily_pro = list()
        for data in response.data:
            for e_execution_daily_pro in data['execution_daily_pro']:
                execution_daily_pro.append(e_execution_daily_pro)
                data1['date_entry'] = str(e_execution_daily_pro['date_entry'])[0:10]
                data1['Activities'] = e_execution_daily_pro['activity_details']['description']
                data1['Description'] = e_execution_daily_pro['description']
                data1['Uom'] = e_execution_daily_pro['uom_details']['c_name']
                data1['PlannedStart'] = e_execution_daily_pro['planned_start_time']
                data1['PlannedEnd'] = e_execution_daily_pro['planned_end_time']
                data1['ActualStart'] = e_execution_daily_pro['actual_start_time']
                data1['ActualEnd'] = e_execution_daily_pro['actual_end_time']
                data1['QuantityPlanned'] = e_execution_daily_pro['planned_quantity']
                data1['QuantityAchieved'] = e_execution_daily_pro['archieved_quantity']
                data1['AssignedTo'] = ','.join([ x['name'] for x in e_execution_daily_pro['assigned_to_details']])
                data1["Contractor'sname"] = e_execution_daily_pro['contractor_details']['contact_person_name']
                data1['RemarksHindrances'] = e_execution_daily_pro['remarks']
               
                data_list.append([data1['date_entry'],data1['Activities'],data1['Description'],data1['Uom'],data1['PlannedStart'],data1['PlannedEnd'],
                data1['ActualStart'],data1['ActualEnd'],data1['QuantityPlanned'],
                data1['QuantityAchieved'],data1['AssignedTo'],data1["Contractor'sname"],data1['RemarksHindrances']])
        file_name = ''
        if data_list:
            if os.path.isdir('media/pms/requisitions/document/pms_daily_progress_report/document'):
                file_name = 'media/pms/requisitions/document/pms_daily_progress_report.xlsx'
                file_path = settings.MEDIA_ROOT_EXPORT + file_name
            else:
                os.makedirs('media/pms/requisitions/document/pms_daily_progress_report/document')
                file_name = 'media/pms/requisitions/document/pms_daily_progress_report.xlsx'
                file_path = settings.MEDIA_ROOT_EXPORT + file_name

            
            final_df = pd.DataFrame(data_list, columns=['Date','Activities','Description','Uom','Planned Start','Planned End','Actual Start','Actual End',
                'Quantity Planned','Quantity Achieved','Assigned To',"Contractor's name",'Remarks/Hindrances'])
            export_csv = final_df.to_excel (file_path, index = None, header=True)
           

        url = getHostWithPort(request) + file_name if file_name else None
        data_dict['results'] = {
        'type_of_report':1,
        'url':url,
        'execution_daily_pro': execution_daily_pro
        }

        if execution_daily_pro:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_SUCCESS
        elif len(execution_daily_pro) == 0:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_NO_DATA
        else:
            data_dict['request_status'] = 0
            data_dict['msg'] = settings.MSG_ERROR

        return Response(data_dict)

class ExecutionDailyReportLabourView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionDailyProgress.objects.filter(is_deleted=False).order_by('-id')
    serializer_class = DailyReportlabourSerializerview

    def get_queryset(self):
        project_id = self.kwargs["project_id"]
        site_id = self.kwargs["site_id"]
        filter = {}
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        date = self.request.query_params.get('date', None)
        report_type = int(self.request.query_params.get('report_type', None))

        if date:
            date_object = datetime.strptime(date, '%Y-%m-%d').date()
            filter['date_entry__year'] = date_object.year
            filter['date_entry__month'] = date_object.month
            filter['date_entry__day'] = date_object.day
        
        if start_date and end_date:
            start_object = datetime.strptime(start_date, '%Y-%m-%d')
            filter['date_entry__gte'] = start_object
            end_object = datetime.strptime(end_date, '%Y-%m-%d')
            filter['date_entry__lte'] = end_object

        queryset = self.queryset.filter(project_id=project_id, site_location=site_id,type_of_report=report_type, **filter)
        return queryset

    
    #@response_modify_decorator_get_single_after_execution
    def get(self, request, *args, **kwargs):
        response = super(self.__class__, self).get(self, request, args, kwargs)
        #print("response",response.data)
        data_dict = {}
        data_list = list()
        data1 = dict()
        execution_daily_lab = list()
        for data in response.data:
            
            #print('data',data)
            #time.sleep(5)
            for e_execution_daily_lab in data['execution_daily_lab']:
                execution_daily_lab.append(e_execution_daily_lab)
                data1['date_entry'] = str(e_execution_daily_lab['date_entry'])[0:10]
                data1["NameOfContractor"] = e_execution_daily_lab['contractor_details']['contact_person_name']
                data1['DetailsOfActivity'] = e_execution_daily_lab['details_activity']
                data1['SkilledLabour'] = int(e_execution_daily_lab['number_skilled']) if e_execution_daily_lab['number_skilled'] else 0
                data1['UnskilledLabour'] = int(e_execution_daily_lab['number_unskilled']) if e_execution_daily_lab['number_unskilled'] else 0
                data1['TotalLabour'] = data1['SkilledLabour']  + data1['UnskilledLabour']
                data1['DurationFrom'] = e_execution_daily_lab['start_time']
                data1['DurationTo'] = e_execution_daily_lab['end_time']
                data1['Remarks'] = e_execution_daily_lab['remarks']
                #data_list.append([data1['Activities'],data1['Description']])
                data_list.append([data1['date_entry'],data1['NameOfContractor'],data1['SkilledLabour'],data1['UnskilledLabour'],
                data1['TotalLabour'],data1['DetailsOfActivity'],data1['DurationFrom'],data1['DurationTo'],data1['Remarks']])
            #data['execution_daily_lab1'] = execution_daily_lab
        file_name = ''
        if data_list:
            if os.path.isdir('media/pms/requisitions/document'):
                file_name = 'media/pms/requisitions/document/pms_daily_labour_report.xlsx'
                file_path = settings.MEDIA_ROOT_EXPORT + file_name
            else:
                os.makedirs('media/pms/requisitions/document')
                file_name = 'media/pms/requisitions/document/pms_daily_labour_report.xlsx'
                file_path = settings.MEDIA_ROOT_EXPORT + file_name

            #final_df = pd.DataFrame(data_list, columns=['Activities','Description'])
            final_df = pd.DataFrame(data_list, columns=['Date','Name Of Contractor','Skilled Labour','Unskilled Labour','Total Labour',
            'Details Of Activity','Duration From','Duration To','Remarks'])
            export_csv = final_df.to_excel (file_path, index = None, header=True)

        url = getHostWithPort(request) + file_name if file_name else None
            #print('url',url)
            #data['url'] = url
        data_dict['results'] = {
            'type_of_report':2,
            'url':url,
            'execution_daily_lab': execution_daily_lab
        }

        if execution_daily_lab:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_SUCCESS
        elif len(execution_daily_lab) == 0:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_NO_DATA
        else:
            data_dict['request_status'] = 0
            data_dict['msg'] = settings.MSG_ERROR

        return Response(data_dict)


class ExecutionDailyReportPandMView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionDailyProgress.objects.filter(is_deleted=False).order_by('-id')
    serializer_class = DailyReportPandMSerializerview

    def get_queryset(self):
        project_id = self.kwargs["project_id"]
        site_id = self.kwargs["site_id"]
        filter = {}
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        date = self.request.query_params.get('date', None)
        report_type = int(self.request.query_params.get('report_type', None))

        if date:
            date_object = datetime.strptime(date, '%Y-%m-%d').date()
            filter['date_entry__year'] = date_object.year
            filter['date_entry__month'] = date_object.month
            filter['date_entry__day'] = date_object.day
           
        if start_date and end_date:
            start_object = datetime.strptime(start_date, '%Y-%m-%d').date()
            filter['date_entry__gte'] = start_object
            end_object = datetime.strptime(end_date, '%Y-%m-%d').date()
            filter['date_entry__lte'] = end_object

        queryset = self.queryset.filter(project_id=project_id, site_location=site_id,type_of_report=report_type, **filter)

        return queryset

    #@response_modify_decorator_get_single_after_execution
    def get(self, request, *args, **kwargs):
    	
        response = super(self.__class__, self).get(self, request, args, kwargs)
        #print("response",response.data)
        data_list = list()
        data1 = dict()
        execution_daily_pandm = list()
        data_dict = {}
        for data in response.data:
            for e_execution_daily_pandm in data['execution_daily_pandm']:
                data1['DurationFrom'] = e_execution_daily_pandm['start_time'].strftime('%H:%M %p')
                data1['DurationTo'] = e_execution_daily_pandm['end_time'].strftime('%H:%M %p')
                e_execution_daily_pandm['duration_from_format'] = data1['DurationFrom']
                e_execution_daily_pandm['duration_to_format'] = data1['DurationTo']
                difference = get_time_diff(e_execution_daily_pandm['start_time'],e_execution_daily_pandm['end_time'])
                e_execution_daily_pandm['duration'] = difference
                
                data1['MeterreadingFrom'] = e_execution_daily_pandm['unit_from']
                data1['MeterreadingTo'] = e_execution_daily_pandm['unit_to']
                
                e_execution_daily_pandm['meter_reading_difference'] = data1['MeterreadingTo'] - data1['MeterreadingFrom']
                execution_daily_pandm.append(e_execution_daily_pandm)
                
                data1['date_entry'] = str(e_execution_daily_pandm['date_entry'])[0:10]
                data1['DetailsOfActivity'] = e_execution_daily_pandm['details_of_activity'] if e_execution_daily_pandm['details_of_activity'] else None
                data1['MachineryUsed'] = e_execution_daily_pandm['machinery_used_details']['equipment_name']
                data1['UsedBy'] = e_execution_daily_pandm['used_by']
                
                #data1['HourorKMs'] = e_execution_daily_pandm['uom_details']['c_name'] if e_execution_daily_pandm['uom_details']  else ''
                data1['Remarks'] = e_execution_daily_pandm['remarks']
                #data_list.append([data1['Activities'],data1['Description']])
                data_list.append([data1['date_entry'],data1['DetailsOfActivity'],data1['MachineryUsed'],data1['UsedBy'],data1['MeterreadingFrom'],
                	data1['MeterreadingTo'],e_execution_daily_pandm['meter_reading_difference'],data1['DurationFrom'],data1['DurationTo'],difference,data1['Remarks']])
        file_name = ''
        if data_list:
            if os.path.isdir('media/pms/requisitions/document'):
                file_name = 'media/pms/requisitions/document/pms_daily_progress_p_and_m_report.xlsx'
                file_path = settings.MEDIA_ROOT_EXPORT + file_name
            else:
                os.makedirs('media/pms/requisitions/document')
                file_name = 'media/pms/requisitions/document/pms_daily_progress_p_and_m_report.xlsx'
                file_path = settings.MEDIA_ROOT_EXPORT + file_name

            #final_df = pd.DataFrame(data_list, columns=['Activities','Description'])
            final_df = pd.DataFrame(data_list, columns=['Date','Details Of Activity','Machinery Used','Used By','Meter reading from',
            'Meter reading to','Meter reading in (Kms)','Duration From','Duration To','Duration in (Hours)','Remarks'])
            export_csv = final_df.to_excel (file_path, index = None, header=True)
           
        url = getHostWithPort(request) + file_name if file_name else None
            #print('url',url)
            #data['url'] = url
        data_dict['results'] = {
            'type_of_report':3,
            'url':url,
            'execution_daily_pandm': execution_daily_pandm
        }

        if execution_daily_pandm:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_SUCCESS
        elif len(execution_daily_pandm) == 0:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_NO_DATA
        else:
            data_dict['request_status'] = 0
            data_dict['msg'] = settings.MSG_ERROR

        return Response(data_dict)



#::::::::::  PMS EXECUTION PURCHASES REQUISITIONS ACTIVITIES MASTER ADD ;::::::::#



class ExecutionPurchasesRequisitionsActivitiesMasterAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesRequisitionsActivitiesMaster.objects.all()
    serializer_class = ExecutionPurchasesRequisitionsActivitiesMasterAddSerializer


    @response_modify_decorator_list
    def list(self, request, *args, **kwargs):
        # print(response)
        return response


#::::::::::  PMS EXECUTION PURCHASES REQUISITIONS ACTIVITIES MASTER ADD ;::::::::#
class ExecutionPurchasesRequisitionsActivitiesMasterEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesRequisitionsActivitiesMaster.objects.all()
    serializer_class = ExecutionPurchasesRequisitionsActivitiesMasterEditSerializer

#::::::::::  PMS EXECUTION PURCHASES REQUISITIONS ACTIVITIES MASTER ADD ;::::::::#
class ExecutionPurchasesRequisitionsActivitiesMasterDeleteView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesRequisitionsActivitiesMaster.objects.all()
    serializer_class = ExecutionPurchasesRequisitionsActivitiesMasterDeleteSerializer


#:::::::::: PMS EXECUTION PURCHASES REQUISITIONS ADD :::::::::#
class PurchaseRequisitionsAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesRequisitions.objects.filter(is_deleted=False)
    serializer_class = PurchaseRequisitionsAddSerializer

    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        return response
class PurchaseRequisitionsForAndroidAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesRequisitions.objects.filter(is_deleted=False)
    serializer_class = PurchaseRequisitionsForAndroidAddSerializer

    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        return response
class PurchaseRequisitionsSubmitApprovalView(generics.RetrieveUpdateAPIView):#
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesRequisitionsMaster.objects.filter(is_deleted=False)
    serializer_class = PurchaseRequisitionsSumbmitApprovalSerializer

    def get(self, request, *args, **kwargs):

        details = PmsExecutionPurchasesRequisitionsMaster.objects.filter(pk=self.kwargs['pk'])
        for e_d in details:

            e_dict = {'id':e_d.id,'status':e_d.status,'mr_date':e_d.mr_date,'type':e_d.type.id,'completed_status':e_d.completed_status}
            return Response({"result":e_dict})

#:::::::::: PMS EXECUTION PURCHASES REQUISITIONS DATA LIST :::::::::#
class PurchaseRequisitionsDataList(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesRequisitionsMaster.objects.filter(is_deleted=False)
    serializer_class = PurchaseRequisitionsListSerializer

    def get_queryset(self):
        requisition_id=self.kwargs["req_id"]
        req_master_data=PmsExecutionPurchasesRequisitionsMaster.objects.filter(id=requisition_id)
        return self.queryset.filter(
            requisitions_master=requisition_id,site_location=req_master_data.site_location,project=req_master_data.project_id)

    def get(self, request, *args, **kwargs):
        #:::::::::::::::::For PDF File:::::::::::::::::::::::::::::::::#
        if os.path.isdir('media/pms/requisition_report/document'):
            file_name = 'media/pms/requisition_report/document/requisition_report.pdf'
            #print('file_name',file_name)
        else:
            os.makedirs('media/pms/requisition_report/document')
            file_name = 'media/pms/requisition_report/document/requisition_report.pdf'
            #print('file_name',file_name)

        doc = SimpleDocTemplate(file_name,pagesize=landscape(letter),
                                rightMargin=30,leftMargin=30,
                                topMargin=20,bottomMargin=40)
        #print('doc',doc)
        Story=[]
        logo = ''
        if settings.DEBUG:
        	logo ="http://166.62.54.122/ssil/assets/img/shyam_infra_logo.png"
        else:
            logo ="https://shyamsteel.tech/assets/img/shyam_infra_logo.png"
            im = Image(logo, 2*inch)
            im.hAlign = 'CENTER'
            Story.append(im)
        # logo="logo.png"
        
        
        styles=getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
        ptext = '<font size="18">%s</font>' % 'Purchase Requisition:'
        Story.append(Paragraph(ptext, styles["Normal"]))
        Story.append(Spacer(1, 12))

        data_dict={}
        data = dict()
        reqMasterID = self.kwargs['req_id']
        # print(reqMasterID)     
        reqMasterDetails = PmsExecutionPurchasesRequisitionsMaster.objects.filter(id=reqMasterID)
        #print('reqMasterDetails',reqMasterDetails)
        # row_blank = False
        if reqMasterDetails:
            for getReqMasterDetails in reqMasterDetails:
                # row_blank = False
                data['requisition_master'] = {
                    'id' : getReqMasterDetails.id,
                    'mr_date' : getReqMasterDetails.mr_date,
                    'site_location_name' : getReqMasterDetails.site_location.name,
                    'site_location' : getReqMasterDetails.site_location.id,
                    'project' : getReqMasterDetails.project.id,
                    'project_name' : getReqMasterDetails.project.name,
                    'status':getReqMasterDetails.status
                    # 'type' : getReqMasterDetails.type.id,
                    # 'type_name' : getReqMasterDetails.type.type_name
                }
                # data_header= [['Project Name: ', getReqMasterDetails.project.name],
                #     ['Site Location',getReqMasterDetails.site_location.name],
                #     ['M.R DATE', getReqMasterDetails.mr_date],
                #     ['Type', getReqMasterDetails.type.type_name],
                #     ]
                reqDetails = PmsExecutionPurchasesRequisitions.objects.filter(requisitions_master=getReqMasterDetails.id, is_deleted=False)
                required_by = reqDetails.first().required_by if reqDetails.first() else ''
                data_header= [['Project Name','Site Location','M.R DATE','Type','Required By']]
                data_value= [getReqMasterDetails.project.name,getReqMasterDetails.site_location.name,
                getReqMasterDetails.mr_date.date(),getReqMasterDetails.type.type_name,required_by]
                data_header.append(data_value)
                STYLE = [
                    ('GRID',(0,0),(-1,-1),0.5,colors.darkgrey),
                    ('BACKGROUND',(0,0),(-1,0),colors.grey),
                    ]
                STYLE_FOOTER = [
                    ('GRID',(0,0),(-1,-1),0.5,colors.darkgrey),
                    ('BACKGROUND',(0,0),(-1,0),colors.grey),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ]
                t=tables.Table(data_header,style=STYLE)
                t.hAlign = 'LEFT'
                Story.append(t)

                

                styles=getSampleStyleSheet()
                styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
                
                ptext = '<font size="18">%s</font>' % 'Item Details:'
                Story.append(Paragraph(ptext, styles["Normal"]))
                Story.append(Spacer(1, 12))
                data_footer= [['Item Code','Description','UOM','Quantity','Current Stock','Site Procurement',
                         'HO Procurement','Required on','Remarks']]
                

                # doc.build(Story)
               
                # reqDetails = PmsExecutionPurchasesRequisitions.objects.filter(requisitions_master=getReqMasterDetails.id, is_deleted=False)
                # print(getReqMasterDetails.type.type_name)
                data['requisition_master']['type'] = {
                    'id': getReqMasterDetails.type.id,
                    'type_name': getReqMasterDetails.type.type_name,
                    'code': getReqMasterDetails.type.code
                }
                
                reqList = list()
                requisition_list=[]
                for reqData in reqDetails:
                    current_stock = 0.0
                    if getReqMasterDetails.status >= 1:
                        #print('sdsssddfsdfdfsd')
                        current_stock_details = PmsExecutionStock.objects.filter(
                            project=getReqMasterDetails.project.id, 
                            site_location=getReqMasterDetails.site_location.id,
                            type=getReqMasterDetails.type.id, 
                            uom=reqData.uom.id,
                            item=reqData.item
                            ).values('closing_stock','opening_stock','recieved_stock','issued_stock').order_by('-stock_date').first()
                        #current_stock = 0.0
                        #print('current_stock_details',current_stock_details)
                        if current_stock_details:
                            
                            #for e_current_stock in current_stock_details:
                                #print('e_current_stock',e_current_stock.opening_stock)
                            if current_stock_details['issued_stock']:
                                t_issued_stock = float(current_stock_details['issued_stock'])
                            else:
                                t_issued_stock = 0.0

                            if current_stock_details['opening_stock']:
                                t_opening_stock = float(current_stock_details['opening_stock'])
                            else:
                                t_opening_stock = 0.0

                            if current_stock_details['recieved_stock']:
                                t_recieved_stock = float(current_stock_details['recieved_stock'])
                            else:
                                t_recieved_stock = 0.0
                            current_stock = (t_opening_stock + t_recieved_stock)-t_issued_stock
                                #print('current_stock',current_stock)
                        else:
                            current_stock = 0.0

                    elif getReqMasterDetails.status == 0:
                        current_stock_details_f_req_table = PmsExecutionPurchasesRequisitions.objects.filter(
                        pk=reqData.id,
                        )
                        # current_stock_details_f_stock_table = PmsExecutionStock.objects.filter(
                        #     project=getReqMasterDetails.project.id,
                        #     site_location=getReqMasterDetails.site_location.id,
                        #     type=getReqMasterDetails.type.id,
                        #     uom=reqData.uom.id,
                        #     item=reqData.item
                        # )
                        current_stock_details_f_stock_table=PmsExecutionStock.objects.filter(
                            project=getReqMasterDetails.project.id, 
                            site_location=getReqMasterDetails.site_location.id, 
                            type=getReqMasterDetails.type.id, 
                            uom=reqData.uom.id,
                            item=reqData.item
                            ).values('closing_stock','opening_stock','recieved_stock','issued_stock').order_by('-stock_date').first()
                        #print('current_stock_details',current_stock_details)
                        if current_stock_details_f_stock_table:
                            e_c_s_d_f_stock_table = current_stock_details_f_stock_table
                            #for e_c_s_d_f_stock_table in current_stock_details_f_stock_table:

                            if e_c_s_d_f_stock_table['issued_stock']:
                                t_issued_stock = float(e_c_s_d_f_stock_table['issued_stock'])
                            else:
                                t_issued_stock = 0.0

                            if e_c_s_d_f_stock_table['opening_stock']:
                                t_opening_stock = float(e_c_s_d_f_stock_table['opening_stock'])
                            else:
                                t_opening_stock = 0.0

                            if e_c_s_d_f_stock_table['recieved_stock']:
                                t_recieved_stock = float(e_c_s_d_f_stock_table['recieved_stock'])
                            else:
                                t_recieved_stock = 0.0
                            current_stock = (t_opening_stock + t_recieved_stock)-t_issued_stock

                            if current_stock == 0.00:
                                #for e_c_s_d_f_req_table in current_stock_details_f_req_table:
                                current_stock = float(e_c_s_d_f_stock_table['closing_stock'])
                        else:
                            current_stock = 0.0


                    req_dict={
                        'id' : reqData.id,
                        'hsn_sac_code' : reqData.hsn_sac_code,
                        # 'item' : reqData.item,
                        'quantity' : reqData.quantity,
                        'current_stock' : current_stock,
                        'procurement_site' : reqData.procurement_site,
                        'procurement_ho' : reqData.procurement_ho,
                        'required_by' : reqData.required_by,
                        'required_on' : reqData.required_on,
                        'remarks' : reqData.remarks
                    }
                    # requisition_dict = OrderedDict()
                    # if row_blank is False:
                    #     requisition_dict['Project Name']=getReqMasterDetails.project.name
                    #     requisition_dict['Site Location Name']=getReqMasterDetails.site_location.name
                    #     requisition_dict['M.R. Date']=getReqMasterDetails.mr_date
                    #     requisition_dict['Type']=getReqMasterDetails.type.type_name
                    # else:
                    #     requisition_dict['Project Name']= ""
                    #     requisition_dict['Site Location Name']= ""
                    #     requisition_dict['M.R. Date']= ""
                    #     requisition_dict['Type']= ""
                                                                                
                    req_dict['uom_name'] = reqData.uom.c_name if reqData.uom else ''               
                    req_dict['uom'] = reqData.uom.id if reqData.uom else ''
                    type_details = getReqMasterDetails.type.type_name
                    # if type_details.lower() == "materials":
                    material_details = Materials.objects.filter(id=reqData.item)
                    item_data = []
                    for matdetaisl in material_details:
                        description = Paragraph(matdetaisl.description, styles["BodyText"])
                        req_dict['item_details'] = {
                            'id': matdetaisl.id,
                            'name' : matdetaisl.name,
                            'description' : matdetaisl.description,
                            'mat_code' : matdetaisl.mat_code
                        }
                        item_data.append(matdetaisl.mat_code)
                        item_data.append(description)
                    item_data.append(reqData.uom.c_name)
                    item_data.append(reqData.quantity)
                    item_data.append(current_stock)
                    item_data.append(reqData.procurement_site)
                    item_data.append(reqData.procurement_ho)
                    item_data.append(reqData.required_on.date())
                    remarks_c =  Paragraph(reqData.remarks, styles["BodyText"]) if reqData.remarks else ''
                    item_data.append(remarks_c)
                    data_footer.append(item_data)

                    if type_details.lower() == 'machinery':
                        machinery_details= PmsMachineries.objects.filter(id=reqData.item)
                        for mach in machinery_details:
                            req_dict['item_details'] = {
                                'id': mach.id,
                                'code' : mach.code,
                                'equipment_name' : mach.equipment_name

                            }
                        # print(machinery_details)

                    activity_details = PmsExecutionPurchasesRequisitionsMapWithActivities.objects.filter(
                        requisitions_id=reqData.id, is_deleted=False)
                    activity_list = list()
                    for e_activity_details in activity_details:
                        # print('e_activity_details',e_activity_details)
                        ac_d = {
                            'id': e_activity_details.activity.id,
                            'code': e_activity_details.activity.code,
                            'description': e_activity_details.activity.description
                        }
                        activity_list.append(ac_d)
                    req_dict['activity_details']=activity_list

                    #approval calculations#######################
                    from django.db.models import Sum
                    item_d = Materials.objects.filter(id=reqData.item).values('id','name')
                    # unit_d = PmsExecutionPurchasesRequisitions.objects. \
                    #              filter(requisitions_master=PmsExecutionPurchasesRequisitionsApproval.requisitions_master,
                    #                     item=PmsExecutionPurchasesRequisitionsApproval.uom).values('uom')[:1]
                    
                    #u = [x['uom'] for x in unit_d]
                    unit_details = TCoreUnit.objects.filter(pk=reqData.uom.id).values('id', 'c_name')
                    #print("unit_details:::::",unit_details)
                    if unit_details:
                        req_master_details = PmsExecutionPurchasesRequisitionsMaster.objects. \
                            filter(project=getReqMasterDetails.project,
                                site_location=getReqMasterDetails.site_location,
                                status=8, type=getReqMasterDetails.type).order_by('-id')
                        approval_list = []
                        query_list = []
                        totals = 0
                        c = 0
                        last_3_avg = 0
                        
                        for req_master in req_master_details:
                            if req_master:
                                qr_details = PmsExecutionPurchasesRequisitions.objects. \
                                    filter(requisitions_master=req_master.id, item=reqData.item). \
                                    aggregate(Sum('quantity'))['quantity__sum']
                                if qr_details is not None:
                                    totals = totals + qr_details
                                    if c < 3:
                                        last_3_avg = last_3_avg + qr_details
                                        c = c + 1
                        latest = PmsExecutionPurchasesRequisitions.objects. \
                            filter(requisitions_master=reqMasterID,
                                item=reqData.item). \
                            aggregate(Sum('quantity'))['quantity__sum']
                        remarks_details = PmsExecutionPurchasesRequisitions.objects. \
                            filter(requisitions_master=reqMasterID,
                                item=reqData.item).values("remarks").distinct()
                        #print("remarks_details:::::::", remarks_details)
                        approval_data=PmsExecutionPurchasesRequisitionsApproval.objects.filter(requisitions_master=reqMasterID,
                                        item=reqData.item,uom=reqData.uom).values('initial_estimate','as_per_drawing')

                        if approval_data:

                            #print("remarks_details:::::::", remarks_details)
                            actual_consumption = {}
                            actual_consumption = {'total_previous_requisition': totals,
                                                'avg_of_last_three_requsition': last_3_avg,
                                                'new_requsition': latest,
                                                'item_name': [x for x in item_d][0]['name'],
                                                # 'unit_name': None,
                                                'remarks': [x for x in remarks_details][0]['remarks'],
                                                'initial_estimate':approval_data[0]['initial_estimate'],
                                                'as_per_drawing':approval_data[0]['as_per_drawing']

                                                }
                        else:
                            actual_consumption = {}
                            actual_consumption = {'total_previous_requisition': totals,
                                                'avg_of_last_three_requsition': last_3_avg,
                                                'new_requsition': latest,
                                                'item_name': [x for x in item_d][0]['name'],
                                                # 'unit_name': None,
                                                'remarks': [x for x in remarks_details][0]['remarks'],
                                                'initial_estimate':0.0,
                                                'as_per_drawing':0.0

                                                }
                        

                        req_dict['actual_consumption']=actual_consumption
                    else:
                        req_master_details = PmsExecutionPurchasesRequisitionsMaster.objects. \
                            filter(project=getReqMasterDetails.project,
                                site_location=getReqMasterDetails.site_location,
                                status=8, type=getReqMasterDetails.type).order_by('-id')
                        approval_list = []
                        query_list = []
                        totals = 0
                        c = 0
                        last_3_avg = 0
                        
                        for req_master in req_master_details:
                            if req_master:
                                qr_details = PmsExecutionPurchasesRequisitions.objects. \
                                    filter(requisitions_master=req_master.id, item=reqData.item). \
                                    aggregate(Sum('quantity'))['quantity__sum']
                                if qr_details is not None:
                                    totals = totals + qr_details
                                    if c < 3:
                                        last_3_avg = last_3_avg + qr_details
                                        c = c + 1
                        latest = PmsExecutionPurchasesRequisitions.objects. \
                            filter(requisitions_master=reqMasterID,
                                item=reqData.item). \
                            aggregate(Sum('quantity'))['quantity__sum']
                        remarks_details = PmsExecutionPurchasesRequisitions.objects. \
                            filter(requisitions_master=reqMasterID,
                                item=reqData.item).values("remarks").distinct()
                        approval_data=PmsExecutionPurchasesRequisitionsApproval.objects.filter(requisitions_master=reqMasterID,
                                        item=reqData.item,uom=reqData.uom).values('initial_estimate','as_per_drawing')

                        if approval_data:

                            #print("remarks_details:::::::", remarks_details)
                            actual_consumption = {}
                            actual_consumption = {'total_previous_requisition': totals,
                                                'avg_of_last_three_requsition': last_3_avg,
                                                'new_requsition': latest,
                                                'item_name': [x for x in item_d][0]['name'],
                                                # 'unit_name': None,
                                                'remarks': [x for x in remarks_details][0]['remarks'],
                                                'initial_estimate':approval_data[0]['initial_estimate'],
                                                'as_per_drawing':approval_data[0]['as_per_drawing']

                                                }
                        else:
                            actual_consumption = {}
                            actual_consumption = {'total_previous_requisition': totals,
                                                'avg_of_last_three_requsition': last_3_avg,
                                                'new_requsition': latest,
                                                'item_name': [x for x in item_d][0]['name'],
                                                # 'unit_name': None,
                                                'remarks': [x for x in remarks_details][0]['remarks'],
                                                'initial_estimate':0.0,
                                                'as_per_drawing':0.0

                                                }
                        
                        req_dict['actual_consumption']=actual_consumption

                    #level of approvals list 

                    section_name = self.request.query_params.get('section_name', None)
                    if section_name:
                        # updated for project wise approver
                        permission_details = get_permission_details_for_requisition(reqMasterID, 
                            getReqMasterDetails.project.id if getReqMasterDetails.is_approval_project_specific else None,
                            req_dict['uom'], req_dict['item_details']['id'], section_name)
                        req_dict['permission_details'] = permission_details
                        # --
                        
                    reqList.append(req_dict)
                    # requisition_list.append(requisition_dict)
                data['requisition_master']['requisition_details'] = reqList
                footer=tables.Table(data_footer,style=STYLE_FOOTER,colWidths=[1*inch] *8)
                footer.hAlign = 'LEFT'
                Story.append(footer)
                dummy_header=[["","","","",""]]
                dummy_header.append(["","","","",""])
                dummy=tables.Table(dummy_header,style=STYLE_FOOTER,colWidths=[1*inch] *8)
                dummy.hAlign = 'LEFT'
                Story.append(dummy)
                ending_header= [['Prepared by','Site Incharge','Project Manager','Approved by','Purchase Head']]
                ending=tables.Table(ending_header,style=STYLE_FOOTER,colWidths=[1*inch] *8)
                #print('ending',ending,type(ending))
                ending.hAlign = 'LEFT'
                Story.append(ending)
                doc.build(Story)

                if request.is_secure():
                    protocol = 'https://'
                else:
                    protocol = 'http://'

                url = getHostWithPort(request) + file_name if file_name else None
        else:
            data=[]


        data_dict['result'] = data
        if data:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_SUCCESS
            data_dict['url'] =url
        elif len(data) == 0:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_NO_DATA
            data_dict['url'] =None
        else:
            data_dict['request_status'] = 0
            data_dict['msg'] = settings.MSG_ERROR
            data_dict['url'] =None
        data = data_dict


        return Response(data)

class PurchaseRequisitionsTotalDataList(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesRequisitionsMaster.objects.filter(is_deleted=False).order_by('-mr_date')
    serializer_class = PurchaseRequisitionsListSerializer
    pagination_class = CSPageNumberPagination

    # def get_queryset(self):
    #     requisition_id=self.kwargs["req_id"]
    #     req_master_data=PmsExecutionPurchasesRequisitionsMaster.objects.filter(id=requisition_id)
    #     return self.queryset.filter(
    #         requisitions_master=requisition_id,site_location=req_master_data.site_location,project=req_master_data.project_id)
    
    def get_queryset(self):
        section_name = self.request.query_params.get('section_name', None)
        if section_name == 'requisition':
            queryset=self.queryset.filter(Q(status=1)|Q(status=2))
        else:
            queryset = self.queryset
        
        # queryset = self.queryset

        filter = {}
        project = self.request.query_params.get('project', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        site_location = self.request.query_params.get('site_location', None)
        type_name = self.request.query_params.get('type_name', None)
        search = self.request.query_params.get('search', None)
        item_type = self.request.query_params.get('item_type', None)
        item = self.request.query_params.get('item', None)

        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)

        if search :
            #print("This is if condition entry")
            queryset = queryset.filter(project__project_g_id=search)
            #print('queryset_search::::::::::::::::::::', queryset)
            return queryset

        if field_name and order_by:
            if field_name == 'project' and order_by == 'asc':
                queryset = queryset.order_by('project__project_g_id')
            elif field_name == 'project' and order_by == 'desc':
                queryset = queryset.order_by('-project__project_g_id')
            elif field_name == 'site_location' and order_by == 'asc':
                queryset = queryset.order_by('site_location__name')
            elif field_name == 'site_location' and order_by == 'desc':
                queryset = queryset.order_by('-site_location__name')
            elif field_name == 'mr_date' and order_by == 'asc':
                queryset = queryset.order_by('mr_date')
            elif field_name == 'mr_date' and order_by == 'desc':
                queryset = queryset.order_by('-mr_date')

        if start_date and end_date:
            start_object = datetime.strptime(start_date, '%Y-%m-%d').date()
            filter['mr_date__gte'] = start_object
            end_object = datetime.strptime(end_date, '%Y-%m-%d').date()
            filter['mr_date__lte'] = end_object + timedelta(days=1)

        if site_location:
            filter['site_location__in']=list(map(int,site_location.split(",")))

        if project:
            filter['project__in']=list(map(int,project.split(",")))


        if type_name:
            filter['type'] = int(type_name)

        if item:
            filter['item__in']= list(map(int,item.split(",")))
            

        if filter:
            queryset = queryset.filter(**filter)
            return queryset
        else:
            queryset=queryset.filter()
            return queryset

    def get(self, request, *args, **kwargs):
        data_dict={}
        data= {}
        data_list=[]

        user = self.request.user
        section_name = self.request.query_params.get('section_name', None)
        section_details=TCoreOther.objects.get(cot_name__iexact=section_name)
        own_level_num = 0
        own_levels = PmsApprovalPermissonMatser.objects.filter(approval_user=user, section=section_details.id)
        for levl in own_levels:
            own_level_num = int(re.sub("\D", "", levl.permission_level))

        response = super(PurchaseRequisitionsTotalDataList, self).get(self, request, *args, **kwargs)

        for getReqMasterDetails in response.data['results']:
            data['requisition_master'] = {
                'id' : getReqMasterDetails['id'],
                'mr_date' : getReqMasterDetails['mr_date'],
                'site_location_name' :PmsSiteProjectSiteManagement.objects.get(id=getReqMasterDetails['site_location']).name,
                'site_location' : getReqMasterDetails['site_location'],
                'project' : getReqMasterDetails['project'],
                'project_name' : PmsProjects.objects.get(id=getReqMasterDetails['project']).name,
                'project_code' : PmsProjects.objects.get(id=getReqMasterDetails['project']).project_g_id,
                'status':getReqMasterDetails['status']
            }
            reqDetails = PmsExecutionPurchasesRequisitions.objects.filter(requisitions_master=getReqMasterDetails['id'], is_deleted=False)
            data['requisition_master']['type'] = {
                'id': getReqMasterDetails['type'],
                'type_name': PmsExecutionPurchasesRequisitionsTypeMaster.objects.get(id=getReqMasterDetails['type']).type_name,
                'code':  PmsExecutionPurchasesRequisitionsTypeMaster.objects.get(id=getReqMasterDetails['type']).code
            }
            reqList = list()
            for reqData in reqDetails:
                approvals = PmsExecutionPurchasesRequisitionsApproval.objects.filter(requisitions_master_id=getReqMasterDetails['id'],
                    item=reqData.item, uom=reqData.uom).order_by('id')
                show = False
                approved_level_num = 0
                for approval in approvals:
                    approved_level_num = int(re.sub("\D", "", approval.approval_permission_user_level.permission_level))
                if own_level_num > approved_level_num:
                    show = True
                print ('PurchaseRequisitionsTotalDataList - req. id {0}, item {1}, uom {2}, current user level {3}, approved level {4}, show {5}'
                    .format(getReqMasterDetails['id'], reqData.item, reqData.uom, own_level_num, approved_level_num, show))

                if show:
                    current_stock = 0.0
                    if getReqMasterDetails['status'] >= 1:
                        current_stock_details = PmsExecutionUpdatedStock.objects.filter(
                            project=getReqMasterDetails['project'], 
                            site_location=getReqMasterDetails['site_location'],
                            type=getReqMasterDetails['type'], 
                            uom=reqData.uom.id,
                            item=reqData.item
                            )
                        if current_stock_details:
                            for e_current_stock in current_stock_details:
                                if e_current_stock.issued_stock:
                                    t_issued_stock = float(e_current_stock.issued_stock)
                                else:
                                    t_issued_stock = 0.0
                
                                if e_current_stock.opening_stock:
                                    t_opening_stock = float(e_current_stock.opening_stock)
                                else:
                                    t_opening_stock = 0.0

                                if e_current_stock.recieved_stock:
                                    t_recieved_stock = float(e_current_stock.recieved_stock)
                                else:
                                    t_recieved_stock = 0.0
                                current_stock = (t_opening_stock + t_recieved_stock)-t_issued_stock
                        else:
                            current_stock = 0.0
                    elif getReqMasterDetails['status'] == 0:
                        current_stock_details_f_req_table = PmsExecutionPurchasesRequisitions.objects.filter(
                        pk=reqData.id,
                        )
                        current_stock_details_f_stock_table = PmsExecutionUpdatedStock.objects.filter(
                            project=getReqMasterDetails['project'], 
                            site_location=getReqMasterDetails['site_location'],
                            type=getReqMasterDetails['type'], 
                            uom=reqData.uom.id,
                            item=reqData.item
                        )
                        if current_stock_details_f_stock_table:
                            for e_c_s_d_f_stock_table in current_stock_details_f_stock_table:

                                if e_c_s_d_f_stock_table.issued_stock:
                                    t_issued_stock = float(e_c_s_d_f_stock_table.issued_stock)
                                else:
                                    t_issued_stock = 0.0

                                if e_c_s_d_f_stock_table.opening_stock:
                                    t_opening_stock = float(e_c_s_d_f_stock_table.opening_stock)
                                else:
                                    t_opening_stock = 0.0

                                if e_c_s_d_f_stock_table.recieved_stock:
                                    t_recieved_stock = float(e_c_s_d_f_stock_table.recieved_stock)
                                else:
                                    t_recieved_stock = 0.0
                                current_stock = (t_opening_stock + t_recieved_stock)-t_issued_stock

                                if current_stock == 0.00:
                                    for e_c_s_d_f_req_table in current_stock_details_f_req_table:
                                        current_stock = float(e_c_s_d_f_req_table.current_stock)
                        else:
                            for e_c_s_d_f_req_table in current_stock_details_f_req_table:
                                current_stock = float(e_c_s_d_f_req_table.current_stock)
                    
                    req_dict={
                        'id' : reqData.id,
                        'hsn_sac_code' : reqData.hsn_sac_code,
                        'quantity' : reqData.quantity,
                        'current_stock' : current_stock,
                        'procurement_site' : reqData.procurement_site,
                        'procurement_ho' : reqData.procurement_ho,
                        'required_by' : reqData.required_by,
                        'required_on' : reqData.required_on,
                        'remarks' : reqData.remarks
                    }
                    req_dict['uom_name'] = reqData.uom.c_name if reqData.uom else ''
                    req_dict['uom'] = reqData.uom.id if reqData.uom else ''
                    type_details =  PmsExecutionPurchasesRequisitionsTypeMaster.objects.get(id=getReqMasterDetails['type']).type_name
                    material_details = Materials.objects.filter(id=reqData.item)
                    for matdetaisl in material_details:
                        req_dict['item_details'] = {
                            'id': matdetaisl.id,
                            'name' : matdetaisl.name,
                            'description' : matdetaisl.description,
                            'mat_code' : matdetaisl.mat_code
                        }
                    if type_details.lower() == 'machinery':
                        machinery_details= PmsMachineries.objects.filter(id=reqData.item)
                        for mach in machinery_details:
                            req_dict['item_details'] = {
                                'id': mach.id,
                                'code' : mach.code,
                                'equipment_name' : mach.equipment_name
                            }

                    activity_details = PmsExecutionPurchasesRequisitionsMapWithActivities.objects.filter(
                        requisitions_id=reqData.id, is_deleted=False)
                    activity_list = list()
                    for e_activity_details in activity_details:
                        ac_d = {
                            'id': e_activity_details.activity.id,
                            'code': e_activity_details.activity.code,
                            'description': e_activity_details.activity.description
                        }
                        activity_list.append(ac_d)
                    req_dict['activity_details']=activity_list

                    from django.db.models import Sum
                    item_d = Materials.objects.filter(id=reqData.item).values('id','name')
                    unit_details = TCoreUnit.objects.filter(pk=reqData.uom.id).values('id', 'c_name')
                    if unit_details:
                        req_master_details = PmsExecutionPurchasesRequisitionsMaster.objects. \
                            filter(project=getReqMasterDetails['project'],
                                site_location=getReqMasterDetails['site_location'],
                                status=8, type=getReqMasterDetails['type']).order_by('-id')
                        approval_list = []
                        query_list = []
                        totals = 0
                        c = 0
                        last_3_avg = 0
                        
                        for req_master in req_master_details:
                            if req_master:
                                qr_details = PmsExecutionPurchasesRequisitions.objects. \
                                    filter(requisitions_master=req_master.id, item=reqData.item). \
                                    aggregate(Sum('quantity'))['quantity__sum']
                                if qr_details is not None:
                                    totals = totals + qr_details
                                    if c < 3:
                                        last_3_avg = last_3_avg + qr_details
                                        c = c + 1
                        latest = PmsExecutionPurchasesRequisitions.objects. \
                            filter(requisitions_master=getReqMasterDetails['id'],
                                item=reqData.item). \
                            aggregate(Sum('quantity'))['quantity__sum']
                        remarks_details = PmsExecutionPurchasesRequisitions.objects. \
                            filter(requisitions_master=getReqMasterDetails['id'],
                                item=reqData.item).values("remarks").distinct()
                        approval_data=PmsExecutionPurchasesRequisitionsApproval.objects.filter(requisitions_master=getReqMasterDetails['id'],
                                        item=reqData.item,uom=reqData.uom).values('initial_estimate','as_per_drawing')

                        if approval_data:
                            if item_d:
                                item_name=[x for x in item_d][0]['name']
                            else:
                                item_name=""
                            if remarks_details:
                                remarks=[x for x in remarks_details][0]['remarks']
                            else:
                                remarks=""
                            actual_consumption = {}
                            actual_consumption = {'total_previous_requisition': totals,
                                                'avg_of_last_three_requsition': last_3_avg,
                                                'new_requsition': latest,
                                                'item_name': item_name,
                                                'remarks': remarks,
                                                'initial_estimate':approval_data[0]['initial_estimate'],
                                                'as_per_drawing':approval_data[0]['as_per_drawing']

                                                }
                        else:
                            actual_consumption = {}
                            if item_d:
                             item_name=[x for x in item_d][0]['name']
                            else:
                                item_name=""
                            if remarks_details:
                                remarks=[x for x in remarks_details][0]['remarks']
                            else:
                                remarks=""
                            actual_consumption = {'total_previous_requisition': totals,
                                                'avg_of_last_three_requsition': last_3_avg,
                                                'new_requsition': latest,
                                                'item_name': item_name,
                                                'remarks': remarks,
                                                'initial_estimate':0.0,
                                                'as_per_drawing':0.0
                                                }
                        req_dict['actual_consumption']=actual_consumption
                    else:
                        req_master_details = PmsExecutionPurchasesRequisitionsMaster.objects. \
                            filter(project=getReqMasterDetails['project'],
                                site_location=getReqMasterDetails['site_location'],
                                status=8, type=getReqMasterDetails['type']).order_by('-id')
                        approval_list = []
                        query_list = []
                        totals = 0
                        c = 0
                        last_3_avg = 0
                        for req_master in req_master_details:
                            if req_master:
                                qr_details = PmsExecutionPurchasesRequisitions.objects. \
                                    filter(requisitions_master=req_master.id, item=reqData.item). \
                                    aggregate(Sum('quantity'))['quantity__sum']
                                if qr_details is not None:
                                    totals = totals + qr_details
                                    if c < 3:
                                        last_3_avg = last_3_avg + qr_details
                                        c = c + 1
                        latest = PmsExecutionPurchasesRequisitions.objects. \
                            filter(requisitions_master=getReqMasterDetails['id'],
                                item=reqData.item). \
                            aggregate(Sum('quantity'))['quantity__sum']
                        remarks_details = PmsExecutionPurchasesRequisitions.objects. \
                            filter(requisitions_master=getReqMasterDetails['id'],
                                item=reqData.item).values("remarks").distinct()
                        approval_data=PmsExecutionPurchasesRequisitionsApproval.objects.filter(requisitions_master=getReqMasterDetails['id'],
                                        item=reqData.item,uom=reqData.uom).values('initial_estimate','as_per_drawing')

                        if approval_data:
                            actual_consumption = {}
                            actual_consumption = {'total_previous_requisition': totals,
                                                'avg_of_last_three_requsition': last_3_avg,
                                                'new_requsition': latest,
                                                'item_name': [x for x in item_d][0]['name'],
                                                'remarks': [x for x in remarks_details][0]['remarks'],
                                                'initial_estimate':approval_data[0]['initial_estimate'],
                                                'as_per_drawing':approval_data[0]['as_per_drawing']

                                                }
                        else:
                            actual_consumption = {}
                            actual_consumption = {'total_previous_requisition': totals,
                                                'avg_of_last_three_requsition': last_3_avg,
                                                'new_requsition': latest,
                                                'item_name': [x for x in item_d][0]['name'],
                                                'remarks': [x for x in remarks_details][0]['remarks'],
                                                'initial_estimate':0.0,
                                                'as_per_drawing':0.0
                                                }
                        
                        req_dict['actual_consumption']=actual_consumption

                    if section_name:
                        # updated for project wise approver
                        permission_details = get_permission_details_for_requisition(getReqMasterDetails['id'], 
                            getReqMasterDetails['project'] if getReqMasterDetails['is_approval_project_specific'] else None,
                            req_dict['uom'], req_dict['item_details']['id'], section_name)
                        req_dict['permission_details'] = permission_details 
                        # --


                        # permission_details=[]
                        # approval_master_details = PmsApprovalPermissonMatser.objects.filter(section=section_details.id)
                        # log_details=PmsExecutionPurchasesRequisitionsApprovalLogTable.objects.\
                        #         filter(requisitions_master=getReqMasterDetails['id'],type=getReqMasterDetails['type'],uom=req_dict['uom'],item=req_dict['item_details']['id']).\
                        #             values('id','arm_approval','approval_permission_user_level','approved_quantity','created_at')
                        # amd_list=[]
                        # l_d_list=set()
                        # for l_d in log_details:
                        #     l_d_list.add(l_d['approval_permission_user_level'])
                    
                        # for a_m_d in approval_master_details:
                        #     if l_d_list:
                        #         if a_m_d.id in l_d_list:
                        #             l_d=log_details.filter(approval_permission_user_level=a_m_d.id).order_by('-id')[0]
                        #             f_name = a_m_d.approval_user.first_name if a_m_d.approval_user else '' 
                        #             l_name = a_m_d.approval_user.last_name if a_m_d.approval_user else '' 
                        #             var=a_m_d.permission_level
                        #             res = re.sub("\D", "", var)
                        #             permission_dict={
                        #                 "user_level":a_m_d.permission_level,
                        #                 "approval":l_d['arm_approval'],
                        #                 "permission_num":int(res),
                        #                 "approved_quantity":l_d['approved_quantity'],
                        #                 "approved_date":l_d['created_at'],
                        #                 "user_details":{
                        #                     "id":a_m_d.approval_user.id if a_m_d.approval_user else None,
                        #                     "email":a_m_d.approval_user.email if a_m_d.approval_user else None,
                        #                     "name":  f_name +' '+l_name,
                        #                     "username":a_m_d.approval_user.username
                        #                     }
                        #             }
                                        

                        #         else:
                        #             f_name = a_m_d.approval_user.first_name if a_m_d.approval_user else '' 
                        #             l_name = a_m_d.approval_user.last_name if a_m_d.approval_user else '' 
                        #             var=a_m_d.permission_level
                        #             res = re.sub("\D", "", var)
                        #             permission_dict={
                        #                 "user_level":a_m_d.permission_level,
                        #                 "permission_num":int(res),
                        #                 "approval":None,
                        #                 "user_details":{
                        #                     "id":a_m_d.approval_user.id if a_m_d.approval_user else None,
                        #                     "email":a_m_d.approval_user.email if a_m_d.approval_user else None,
                        #                     "name":  f_name +' '+l_name,
                        #                     "username":a_m_d.approval_user.username
                        #                     }
                        #             }

                        #         permission_details.append(permission_dict)
                        #     else:
                        #         f_name = a_m_d.approval_user.first_name if a_m_d.approval_user else '' 
                        #         l_name = a_m_d.approval_user.last_name if a_m_d.approval_user else '' 
                        #         var=a_m_d.permission_level
                        #         res = re.sub("\D", "", var)
                        #         permission_dict={
                        #                 "user_level":a_m_d.permission_level,
                        #                 "permission_num":int(res),
                        #                 "approval":None,
                        #                 "user_details":{
                        #                     "id":a_m_d.approval_user.id if a_m_d.approval_user else None,
                        #                     "email":a_m_d.approval_user.email if a_m_d.approval_user else None,
                        #                     "name":  f_name +' '+l_name,
                        #                     "username":a_m_d.approval_user.username
                        #                     }
                        #             }
                        #         permission_details.append(permission_dict)
                        # req_dict['permission_details']=permission_details

                    reqList.append(req_dict)
            if len(reqList) > 0:
                data['requisition_master']['requisition_details'] = reqList
                data_list.append(data)
            data={}
        
        print('purchase_requisition_total_approval_list', response.data['count'], len(data_list))
        response.data['results'] = data_list
        if response.data['count'] > 0:
            response.data['request_status'] = 1
            response.data['msg'] = settings.MSG_SUCCESS
        else:
            response.data['request_status'] = 1
            response.data['msg'] = settings.MSG_NO_DATA



        return response



#:::::::::: PMS EXECUTION PURCHASES REQUISITIONS TOTAL LIST :::::::::#
class PurchaseRequisitionsTotalListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    pagination_class = CSPageNumberPagination
    queryset = PmsExecutionPurchasesRequisitionsMaster.objects.filter(is_deleted=False).order_by('-mr_date')
    serializer_class = PurchaseRequisitionsTotalListSerializer


    def get_queryset(self):
        filter = {}
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        site_location = self.request.query_params.get('site_location', None)
        type_id = self.request.query_params.get('type_id', None)
        search = self.request.query_params.get('search', None)
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        item_type = self.request.query_params.get('item_type', None)
        # item = self.request.query_params.get('item', None)


        if field_name and order_by:

            if field_name == 'project' and order_by == 'asc':
                return self.queryset.filter(is_deleted=False).order_by('project__id')
            elif field_name == 'project' and order_by == 'desc':
                return self.queryset.filter(is_deleted=False).order_by('-project__id')

            elif field_name == 'site_location' and order_by == 'asc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('site_location__id')
            elif field_name == 'site_location' and order_by == 'desc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('-site_location__id')

            elif field_name == 'mr_date' and order_by == 'asc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('mr_date')
            elif field_name == 'mr_date' and order_by == 'desc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('-mr_date')

            elif field_name == 'item' and order_by == 'asc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('item')
            elif field_name == 'item' and order_by == 'desc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('-item')

        if search :
            #print("This is if condition entry")
            queryset = self.queryset.filter(project__project_g_id=search)
            # print('queryset', queryset.query)
            return queryset


        if start_date and end_date:
            start_object = datetime.strptime(start_date,'%Y-%m-%d').date()
            end_object = datetime.strptime(end_date, '%Y-%m-%d').date()
            filter['mr_date__range'] = (start_object, end_object)

        if site_location:
            filter['site_location__in']=site_location.split(",")

        if type_id:
            filter['type__in'] = type_id.split(",")

        if filter:
            queryset = self.queryset.filter(**filter)
            # print('queryset',queryset)
            return queryset

        else:
            queryset = self.queryset.filter(is_deleted=False)
            return queryset


    def get(self, request, *args, **kwargs):
        response = super(PurchaseRequisitionsTotalListView, self).get(self, request, args, kwargs)

        getItem = self.request.query_params.get('item', None)

        # print("getItem-->",getItem)

        reqMasterLisr = []
        if getItem is None or getItem == "":
            for data in response.data['results']:
                project_details = PmsProjects.objects.filter(id=data['project']).values('project_g_id','id')
                type_details = PmsExecutionPurchasesRequisitionsTypeMaster.objects.filter(id=data['type']).values(
                    'type_name','code','id')
                site_location_details = PmsSiteProjectSiteManagement.objects.filter(id=data['site_location']).values(
                    'name','id')


                data['type'] = type_details[0]['type_name']
                data['type_code'] = type_details[0]['code']
                data['type_id'] = type_details[0]['id']
                data['project'] = project_details[0]['project_g_id']
                data['project_id'] = project_details[0]['id']
                data['site_location'] = site_location_details[0]['name']
                data['site_location_id'] = site_location_details[0]['id']

                reqDetails = PmsExecutionPurchasesRequisitions.objects.filter(
                    requisitions_master=data['id'],
                    is_deleted=False)

                reqList = []
                for reqData in reqDetails:
                    req_dict = {
                        'id': reqData.id,
                        'hsn_sac_code': reqData.hsn_sac_code,
                        'quantity': reqData.quantity,
                        'current_stock': reqData.current_stock,
                        'procurement_site': reqData.procurement_site,
                        'procurement_ho': reqData.procurement_ho,
                        'required_by': reqData.required_by,
                        'required_on': reqData.required_on,
                        'remarks': reqData.remarks
                    }

                    req_dict['uom'] = reqData.uom.c_name if reqData.uom else ''
                    # if (type_details[0]['type_name']).lower() == "materials":
                    material_details = Materials.objects.filter(id=reqData.item)
                    for matdetaisl in material_details:
                        req_dict['item_details'] = {
                            'id': matdetaisl.id,
                            'name': matdetaisl.name,
                            'mat_code': matdetaisl.mat_code,
                            'description': matdetaisl.description
                        }
                    # print(material_details)
                    if (type_details[0]['type_name']).lower() == 'machinery':
                        machinery_details = PmsMachineries.objects.filter(id=reqData.item)
                        for mach in machinery_details:
                            req_dict['item_details'] = {
                                'id': mach.id,
                                'code': mach.code,
                                'equipment_name': mach.equipment_name
                            }

                    activity_details = PmsExecutionPurchasesRequisitionsMapWithActivities.objects.filter(
                        requisitions_id=reqData.id, is_deleted=False)
                    activity_list = []
                    for e_activity_details in activity_details:
                        # print('e_activity_details',e_activity_details)
                        ac_d = {
                            'id': e_activity_details.activity.id,
                            'code': e_activity_details.activity.code,
                            'description': e_activity_details.activity.description
                        }
                        activity_list.append(ac_d)
                    req_dict['activity_details'] = activity_list
                    reqList.append(req_dict)
                data['requisition_details'] = reqList

                # print("Data : -----> ",data)
        else:
            dammy_item = getItem
            for data in response.data['results']:
                
                project_details = PmsProjects.objects.filter(id=data['project']).values('project_g_id','id')
                type_details = PmsExecutionPurchasesRequisitionsTypeMaster.objects.filter(id=data['type']).values(
                    'type_name','code','id')
                site_location_details = PmsSiteProjectSiteManagement.objects.filter(id=data['site_location']).values(
                    'name','id')


                data['type'] = type_details[0]['type_name']
                data['type_code'] = type_details[0]['code']
                data['type_id'] = type_details[0]['id']
                data['project'] = project_details[0]['project_g_id']
                data['project_id'] = project_details[0]['id']
                data['site_location'] = site_location_details[0]['name']
                data['site_location_id'] = site_location_details[0]['id']

                getReqItem = PmsExecutionPurchasesRequisitions.objects.filter(is_deleted=False,requisitions_master=data['id'],item=dammy_item)
                # print("getReqItem-->",getReqItem)

                reqList = []
                for reqItem in getReqItem:
                    req_dict = {
                        'id': reqItem.id,
                        'hsn_sac_code': reqItem.hsn_sac_code,
                        'quantity': reqItem.quantity,
                        'current_stock': reqItem.current_stock,
                        'procurement_site': reqItem.procurement_site,
                        'procurement_ho': reqItem.procurement_ho,
                        'required_by': reqItem.required_by,
                        'required_on': reqItem.required_on,
                        'remarks': reqItem.remarks
                    }
                    req_dict['uom'] = reqItem.uom.c_name if reqItem.uom else ''
                    # if (type_details[0]['type_name']).lower() == "materials":
                    material_details = Materials.objects.filter(id=reqItem.item)
                    for matdetaisl in material_details:
                        req_dict['item_details'] = {
                            'id': matdetaisl.id,
                            'name': matdetaisl.name,
                            'mat_code': matdetaisl.mat_code,
                            'description': matdetaisl.description
                        }
                    # print(material_details)
                    if (type_details[0]['type_name']).lower() == 'machinery':
                        machinery_details = PmsMachineries.objects.filter(id=reqItem.item)
                        for mach in machinery_details:
                            req_dict['item_details'] = {
                                'id': mach.id,
                                'code': mach.code,
                                'equipment_name': mach.equipment_name
                            }

                    activity_details = PmsExecutionPurchasesRequisitionsMapWithActivities.objects.filter(
                        requisitions_id=reqItem.id, is_deleted=False)
                    activity_list = []
                    for e_activity_details in activity_details:
                        # print('e_activity_details',e_activity_details)
                        ac_d = {
                            'id': e_activity_details.activity.id,
                            'code': e_activity_details.activity.code,
                            'description': e_activity_details.activity.description
                        }
                        activity_list.append(ac_d)
                    req_dict['activity_details'] = activity_list
                    reqList.append(req_dict)
                data['requisition_details'] = reqList

        if response.data['count'] > 0:
            response.data['request_status'] = 1
            response.data['msg'] = settings.MSG_SUCCESS
        else:
            response.data['request_status'] = 1
            response.data['msg'] = settings.MSG_NO_DATA

        return response


#MOBILE LISTING FOR REQUISITION 
class PurchaseRequisitionsNotApprovalMobileListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    pagination_class = CSPageNumberPagination
    queryset = PmsExecutionPurchasesRequisitionsMaster.objects.filter(status=0,is_deleted=False).order_by('-id')
    serializer_class = PurchaseRequisitionsNotApprovalMobileListSerializer
    
    def get_queryset(self):
        filter = {}
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        site_location = self.request.query_params.get('site_location', None)
        type_id = self.request.query_params.get('type_id', None)
        search = self.request.query_params.get('search', None)
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        item_type = self.request.query_params.get('item_type', None)
        # item = self.request.query_params.get('item', None)


        if field_name and order_by:

            if field_name == 'project' and order_by == 'asc':
                return self.queryset.filter(is_deleted=False).order_by('project__id')
            elif field_name == 'project' and order_by == 'desc':
                return self.queryset.filter(is_deleted=False).order_by('-project__id')

            elif field_name == 'site_location' and order_by == 'asc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('site_location__id')
            elif field_name == 'site_location' and order_by == 'desc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('-site_location__id')

            elif field_name == 'mr_date' and order_by == 'asc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('mr_date')
            elif field_name == 'mr_date' and order_by == 'desc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('-mr_date')

            elif field_name == 'item' and order_by == 'asc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('mr_date')
            elif field_name == 'item' and order_by == 'desc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('-mr_date')

        if search :
            #print("This is if condition entry")
            queryset = self.queryset.filter(project__project_g_id=search)
            # print('queryset', queryset.query)
            return queryset


        if start_date and end_date:
            start_object = datetime.strptime(start_date,'%Y-%m-%d').date()
            end_object = datetime.strptime(end_date, '%Y-%m-%d').date()
            filter['mr_date__range'] = (start_object, end_object)

        if site_location:
            filter['site_location__in']=site_location.split(",")

        if type_id:
            filter['type__in'] = type_id.split(",")

        if filter:
            queryset = self.queryset.filter(**filter)
            # print('queryset',queryset)
            return queryset

        else:
            queryset = self.queryset.filter(is_deleted=False)
            return queryset




    def get(self, request, *args, **kwargs):
        response = super(PurchaseRequisitionsNotApprovalMobileListView, self).get(self, request, args, kwargs)

        getItem = self.request.query_params.get('item', None)

        # print("getItem-->",getItem)

        reqMasterLisr = []
        if getItem is None or getItem == "":
            for data in response.data['results']:
                project_details = PmsProjects.objects.filter(id=data['project']).values('project_g_id','id')
                type_details = PmsExecutionPurchasesRequisitionsTypeMaster.objects.filter(id=data['type']).values(
                    'type_name','code','id')
                site_location_details = PmsSiteProjectSiteManagement.objects.filter(id=data['site_location']).values(
                    'name','id')


                data['type'] = type_details[0]['type_name']
                data['type_code'] = type_details[0]['code']
                data['type_id'] = type_details[0]['id']
                data['project'] = project_details[0]['project_g_id']
                data['project_id'] = project_details[0]['id']
                data['site_location'] = site_location_details[0]['name']
                data['site_location_id'] = site_location_details[0]['id']

                reqDetails = PmsExecutionPurchasesRequisitions.objects.filter(
                    requisitions_master=data['id'],
                    is_deleted=False)

                reqList = []
                for reqData in reqDetails:
                    req_dict = {
                        'id': reqData.id,
                        # 'terms': reqData.terms,
                        'quantity': reqData.quantity,
                        'current_stock': reqData.current_stock,
                        'procurement_site': reqData.procurement_site,
                        'procurement_ho': reqData.procurement_ho,
                        'required_by': reqData.required_by,
                        'required_on': reqData.required_on,
                        'remarks': reqData.remarks
                    }

                    req_dict['uom'] = reqData.uom.c_name if reqData.uom else ''
                    # if (type_details[0]['type_name']).lower() == "materials":
                    material_details = Materials.objects.filter(id=reqData.item)
                    for matdetaisl in material_details:
                        req_dict['item_details'] = {
                            'id': matdetaisl.id,
                            'name': matdetaisl.name,
                            'mat_code': matdetaisl.mat_code,
                            'description': matdetaisl.description
                        }
                        # print(material_details)
                    if (type_details[0]['type_name']).lower() == 'machinery':
                        machinery_details = PmsMachineries.objects.filter(id=reqData.item)
                        for mach in machinery_details:
                            req_dict['item_details'] = {
                                'id': mach.id,
                                'code': mach.code,
                                'equipment_name': mach.equipment_name
                            }

                    activity_details = PmsExecutionPurchasesRequisitionsMapWithActivities.objects.filter(
                        requisitions_id=reqData.id, is_deleted=False)
                    activity_list = []
                    for e_activity_details in activity_details:
                        # print('e_activity_details',e_activity_details)
                        ac_d = {
                            'id': e_activity_details.activity.id,
                            'code': e_activity_details.activity.code,
                            'description': e_activity_details.activity.description
                        }
                        activity_list.append(ac_d)
                    req_dict['activity_details'] = activity_list
                    reqList.append(req_dict)
                data['requisition_details'] = reqList

                # print("Data : -----> ",data)
        else:
            dammy_item = getItem
            for data in response.data['results']:
                
                project_details = PmsProjects.objects.filter(id=data['project']).values('project_g_id','id')
                type_details = PmsExecutionPurchasesRequisitionsTypeMaster.objects.filter(id=data['type']).values(
                    'type_name','code','id')
                site_location_details = PmsSiteProjectSiteManagement.objects.filter(id=data['site_location']).values(
                    'name','id')


                data['type'] = type_details[0]['type_name']
                data['type_code'] = type_details[0]['code']
                data['type_id'] = type_details[0]['id']
                data['project'] = project_details[0]['project_g_id']
                data['project_id'] = project_details[0]['id']
                data['site_location'] = site_location_details[0]['name']
                data['site_location_id'] = site_location_details[0]['id']

                getReqItem = PmsExecutionPurchasesRequisitions.objects.filter(is_deleted=False,requisitions_master=data['id'],item=dammy_item)
                # print("getReqItem-->",getReqItem)

                reqList = []
                for reqItem in getReqItem:
                    req_dict = {
                        'id': reqItem.id,
                        'terms': reqItem.terms,
                        'quantity': reqItem.quantity,
                        'current_stock': reqItem.current_stock,
                        'procurement_site': reqItem.procurement_site,
                        'procurement_ho': reqItem.procurement_ho,
                        'required_by': reqItem.required_by,
                        'required_on': reqItem.required_on,
                        'remarks': reqItem.remarks
                    }
                    req_dict['uom'] = reqItem.uom.c_name if reqItem.uom else ''
                    # if (type_details[0]['type_name']).lower() == "materials":
                    material_details = Materials.objects.filter(id=reqItem.item)
                    for matdetaisl in material_details:
                        req_dict['item_details'] = {
                            'id': matdetaisl.id,
                            'name': matdetaisl.name,
                            'mat_code': matdetaisl.mat_code,
                            'description': matdetaisl.description
                        }
                    # print(material_details)
                    if (type_details[0]['type_name']).lower() == 'machinery':
                        machinery_details = PmsMachineries.objects.filter(id=reqItem.item)
                        for mach in machinery_details:
                            req_dict['item_details'] = {
                                'id': mach.id,
                                'code': mach.code,
                                'equipment_name': mach.equipment_name
                            }

                    activity_details = PmsExecutionPurchasesRequisitionsMapWithActivities.objects.filter(
                        requisitions_id=reqItem.id, is_deleted=False)
                    activity_list = []
                    for e_activity_details in activity_details:
                        # print('e_activity_details',e_activity_details)
                        ac_d = {
                            'id': e_activity_details.activity.id,
                            'code': e_activity_details.activity.code,
                            'description': e_activity_details.activity.description
                        }
                        activity_list.append(ac_d)
                    req_dict['activity_details'] = activity_list
                    reqList.append(req_dict)
                data['requisition_details'] = reqList

        if response.data['count'] > 0:
            response.data['request_status'] = 1
            response.data['msg'] = settings.MSG_SUCCESS
        else:
            response.data['request_status'] = 1
            response.data['msg'] = settings.MSG_NO_DATA

        return response

class PurchaseRequisitionsAfterApprovalMobileListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    pagination_class = CSPageNumberPagination
    queryset = PmsExecutionPurchasesRequisitionsMaster.objects.filter(status__gt=0,is_deleted=False).order_by('-id')
    serializer_class = PurchaseRequisitionsNotApprovalMobileListSerializer

    def get_queryset(self):
        filter = {}
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        site_location = self.request.query_params.get('site_location', None)
        type_id = self.request.query_params.get('type_id', None)
        search = self.request.query_params.get('search', None)
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        item_type = self.request.query_params.get('item_type', None)
        # item = self.request.query_params.get('item', None)


        if field_name and order_by:

            if field_name == 'project' and order_by == 'asc':
                return self.queryset.filter(is_deleted=False).order_by('project__id')
            elif field_name == 'project' and order_by == 'desc':
                return self.queryset.filter(is_deleted=False).order_by('-project__id')

            elif field_name == 'site_location' and order_by == 'asc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('site_location__id')
            elif field_name == 'site_location' and order_by == 'desc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('-site_location__id')

            elif field_name == 'mr_date' and order_by == 'asc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('mr_date')
            elif field_name == 'mr_date' and order_by == 'desc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('-mr_date')

            elif field_name == 'item' and order_by == 'asc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('mr_date')
            elif field_name == 'item' and order_by == 'desc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('-mr_date')

        if search :
            #print("This is if condition entry")
            queryset = self.queryset.filter(project__project_g_id=search)
            # print('queryset', queryset.query)
            return queryset


        if start_date and end_date:
            start_object = datetime.strptime(start_date,'%Y-%m-%d').date()
            end_object = datetime.strptime(end_date, '%Y-%m-%d').date()
            filter['mr_date__range'] = (start_object, end_object)

        if site_location:
            filter['site_location__in']=site_location.split(",")

        if type_id:
            filter['type__in'] = type_id.split(",")

        if filter:
            queryset = self.queryset.filter(**filter)
            # print('queryset',queryset)
            return queryset

        else:
            queryset = self.queryset.filter(is_deleted=False)
            return queryset



    def get(self, request, *args, **kwargs):
        response = super(PurchaseRequisitionsAfterApprovalMobileListView, self).get(self, request, args, kwargs)

        getItem = self.request.query_params.get('item', None)

        # print("getItem-->",getItem)

        reqMasterLisr = []
        if getItem is None or getItem == "":
            for data in response.data['results']:
                project_details = PmsProjects.objects.filter(id=data['project']).values('project_g_id','id')
                type_details = PmsExecutionPurchasesRequisitionsTypeMaster.objects.filter(id=data['type']).values(
                    'type_name','code','id')
                site_location_details = PmsSiteProjectSiteManagement.objects.filter(id=data['site_location']).values(
                    'name','id')


                data['type'] = type_details[0]['type_name']
                data['type_code'] = type_details[0]['code']
                data['type_id'] = type_details[0]['id']
                data['project'] = project_details[0]['project_g_id']
                data['project_id'] = project_details[0]['id']
                data['site_location'] = site_location_details[0]['name']
                data['site_location_id'] = site_location_details[0]['id']

                reqDetails = PmsExecutionPurchasesRequisitions.objects.filter(
                    requisitions_master=data['id'],
                    is_deleted=False)

                reqList = []
                for reqData in reqDetails:
                    req_dict = {
                        'id': reqData.id,
                        # 'terms': reqData.terms,
                        'quantity': reqData.quantity,
                        'current_stock': reqData.current_stock,
                        'procurement_site': reqData.procurement_site,
                        'procurement_ho': reqData.procurement_ho,
                        'required_by': reqData.required_by,
                        'required_on': reqData.required_on,
                        'remarks': reqData.remarks
                    }

                    req_dict['uom'] = reqData.uom.c_name if reqData.uom else ''
                    # if (type_details[0]['type_name']).lower() == "materials":
                    material_details = Materials.objects.filter(id=reqData.item)
                    for matdetaisl in material_details:
                        req_dict['item_details'] = {
                            'id': matdetaisl.id,
                            'name': matdetaisl.name,
                            'mat_code': matdetaisl.mat_code,
                            'description': matdetaisl.description
                        }
                        # print(material_details)
                    if (type_details[0]['type_name']).lower() == 'machinery':
                        machinery_details = PmsMachineries.objects.filter(id=reqData.item)
                        for mach in machinery_details:
                            req_dict['item_details'] = {
                                'id': mach.id,
                                'code': mach.code,
                                'equipment_name': mach.equipment_name
                            }

                    activity_details = PmsExecutionPurchasesRequisitionsMapWithActivities.objects.filter(
                        requisitions_id=reqData.id, is_deleted=False)
                    activity_list = []
                    for e_activity_details in activity_details:
                        # print('e_activity_details',e_activity_details)
                        ac_d = {
                            'id': e_activity_details.activity.id,
                            'code': e_activity_details.activity.code,
                            'description': e_activity_details.activity.description
                        }
                        activity_list.append(ac_d)
                    req_dict['activity_details'] = activity_list
                    reqList.append(req_dict)
                data['requisition_details'] = reqList

                # print("Data : -----> ",data)
        else:
            dammy_item = getItem
            for data in response.data['results']:
                
                project_details = PmsProjects.objects.filter(id=data['project']).values('project_g_id','id')
                type_details = PmsExecutionPurchasesRequisitionsTypeMaster.objects.filter(id=data['type']).values(
                    'type_name','code','id')
                site_location_details = PmsSiteProjectSiteManagement.objects.filter(id=data['site_location']).values(
                    'name','id')


                data['type'] = type_details[0]['type_name']
                data['type_code'] = type_details[0]['code']
                data['type_id'] = type_details[0]['id']
                data['project'] = project_details[0]['project_g_id']
                data['project_id'] = project_details[0]['id']
                data['site_location'] = site_location_details[0]['name']
                data['site_location_id'] = site_location_details[0]['id']

                getReqItem = PmsExecutionPurchasesRequisitions.objects.filter(is_deleted=False,requisitions_master=data['id'],item=dammy_item)
                # print("getReqItem-->",getReqItem)

                reqList = []
                for reqItem in getReqItem:
                    req_dict = {
                        'id': reqItem.id,
                        # 'terms': reqItem.terms,
                        'quantity': reqItem.quantity,
                        'current_stock': reqItem.current_stock,
                        'procurement_site': reqItem.procurement_site,
                        'procurement_ho': reqItem.procurement_ho,
                        'required_by': reqItem.required_by,
                        'required_on': reqItem.required_on,
                        'remarks': reqItem.remarks
                    }
                    req_dict['uom'] = reqItem.uom.c_name if reqItem.uom else ''
                    # if (type_details[0]['type_name']).lower() == "materials":
                    material_details = Materials.objects.filter(id=reqItem.item)
                    for matdetaisl in material_details:
                        req_dict['item_details'] = {
                            'id': matdetaisl.id,
                            'name': matdetaisl.name,
                            'mat_code': matdetaisl.mat_code,
                            'description': matdetaisl.description
                        }
                    # print(material_details)
                    if (type_details[0]['type_name']).lower() == 'machinery':
                        machinery_details = PmsMachineries.objects.filter(id=reqItem.item)
                        for mach in machinery_details:
                            req_dict['item_details'] = {
                                'id': mach.id,
                                'code': mach.code,
                                'equipment_name': mach.equipment_name
                            }

                    activity_details = PmsExecutionPurchasesRequisitionsMapWithActivities.objects.filter(
                        requisitions_id=reqItem.id, is_deleted=False)
                    activity_list = []
                    for e_activity_details in activity_details:
                        # print('e_activity_details',e_activity_details)
                        ac_d = {
                            'id': e_activity_details.activity.id,
                            'code': e_activity_details.activity.code,
                            'description': e_activity_details.activity.description
                        }
                        activity_list.append(ac_d)
                    req_dict['activity_details'] = activity_list
                    reqList.append(req_dict)
                data['requisition_details'] = reqList

        if response.data['count'] > 0:
            response.data['request_status'] = 1
            response.data['msg'] = settings.MSG_SUCCESS
        else:
            response.data['request_status'] = 1
            response.data['msg'] = settings.MSG_NO_DATA

        return response

#:::::::::: PMS EXECUTION PURCHASES REQUISITIONS DATA EDIT :::::::::#
class PurchaseRequisitionsEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesRequisitionsMaster.objects.filter(is_deleted=False)
    serializer_class = PurchaseRequisitionsEditSerializer

class PurchaseRequisitionsForAndroidEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesRequisitions.objects.filter(is_deleted=False)
    serializer_class = PurchaseRequisitionsForAndroidEditSerializer

    @response_modify_decorator_update
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

class PurchaseRequisitionsForAndroidEditItemView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesRequisitions.objects.filter(is_deleted=False)
    serializer_class = PurchaseRequisitionsForAndroidEditItemSerializer
    
    @response_modify_decorator_get_after_execution
    def get(self,request, *args, **kwargs):
        req_id = self.request.query_params.get('req_id')
        item_id = self.request.query_params.get('item_id')

        data = {}
        activityDict = {}

        getItemDetails = PmsExecutionPurchasesRequisitions.objects.filter(requisitions_master=req_id, id=item_id)
        getActivityDetails = PmsExecutionPurchasesRequisitionsMapWithActivities.objects.filter(requisitions=item_id)

        getReqMasterDetails = PmsExecutionPurchasesRequisitionsMaster.objects.filter(id=req_id,is_deleted=False).values(
            'project','site_location','type','status'
        )

        #print("getReqMasterDetails_status",getReqMasterDetails[0]['status'])

        for item_details in getItemDetails:

            ###################################################################################
            current_stock = 0.0
            if int(getReqMasterDetails[0]['status']) >= 1:
                #print('sdsssddfsdfdfsd')
                current_stock_details = PmsExecutionUpdatedStock.objects.filter(
                    project=getReqMasterDetails[0]['project'], 
                    site_location=getReqMasterDetails[0]['site_location'],
                    type=getReqMasterDetails[0]['type'], 
                    uom=item_details.uom.id,
                    item=item_details.item
                    )
                #current_stock = 0.0
                #print('current_stock_details',current_stock_details)
                if current_stock_details:
                    for e_current_stock in current_stock_details:
                        #print('e_current_stock',e_current_stock.opening_stock)
                        if e_current_stock.issued_stock:
                            t_issued_stock = float(e_current_stock.issued_stock)
                        else:
                            t_issued_stock = 0.0

                        if e_current_stock.opening_stock:
                            t_opening_stock = float(e_current_stock.opening_stock)
                        else:
                            t_opening_stock = 0.0

                        if e_current_stock.recieved_stock:
                            t_recieved_stock = float(e_current_stock.recieved_stock)
                        else:
                            t_recieved_stock = 0.0
                        current_stock = (t_opening_stock + t_recieved_stock)-t_issued_stock
                        #print('current_stock',current_stock)
                else:
                    current_stock = 0.0
            elif int(getReqMasterDetails[0]['status']) == 0:
                #print('11111111111111111111111111111111111111111111111111')
                current_stock_details_f_req_table = PmsExecutionPurchasesRequisitions.objects.filter(
                pk=item_details.id,
                )
                current_stock_details_f_stock_table = PmsExecutionUpdatedStock.objects.filter(
                    project=getReqMasterDetails[0]['project'],
                    site_location=getReqMasterDetails[0]['site_location'],
                    type=getReqMasterDetails[0]['type'],
                    uom=item_details.uom.id,
                    item=item_details.item
                )
                #print('current_stock_details',current_stock_details)
                if current_stock_details_f_stock_table:
                    for e_c_s_d_f_stock_table in current_stock_details_f_stock_table:

                        if e_c_s_d_f_stock_table.issued_stock:
                            t_issued_stock = float(e_c_s_d_f_stock_table.issued_stock)
                        else:
                            t_issued_stock = 0.0

                        if e_c_s_d_f_stock_table.opening_stock:
                            t_opening_stock = float(e_c_s_d_f_stock_table.opening_stock)
                        else:
                            t_opening_stock = 0.0

                        if e_c_s_d_f_stock_table.recieved_stock:
                            t_recieved_stock = float(e_c_s_d_f_stock_table.recieved_stock)
                        else:
                            t_recieved_stock = 0.0
                        current_stock = (t_opening_stock + t_recieved_stock)-t_issued_stock

                        if current_stock == 0.00:
                            for e_c_s_d_f_req_table in current_stock_details_f_req_table:
                                current_stock = float(e_c_s_d_f_req_table.current_stock)
                else:
                    for e_c_s_d_f_req_table in current_stock_details_f_req_table:
                        current_stock = float(e_c_s_d_f_req_table.current_stock)
            ####################################################################################

            #print("current_stock---->",current_stock)
            data = {
                'requisitions_master_id' : item_details.requisitions_master.id,
                'item_id' : item_details.id,
                # 'terms' : item_details.terms,
                'hsn_sac_code':item_details.hsn_sac_code,
                'quantity' : item_details.quantity,
                'current_stock' : current_stock,
                'procurement_site' : item_details.procurement_site,
                'procurement_ho' : item_details.procurement_ho,
                'required_by' : item_details.required_by,
                'required_on' : item_details.required_on,
                'remarks' : item_details.remarks
            }
            data['uom_name'] = item_details.uom.c_name if item_details.uom else ''
            data['uom'] = item_details.uom.id if item_details.uom else ''

            type = PmsExecutionPurchasesRequisitionsMaster.objects.only('type').get(id=item_details.requisitions_master.id).type
            type_details = PmsExecutionPurchasesRequisitionsTypeMaster.objects.only('type_name').get(id=str(type)).type_name
            # if type_details.lower() == "materials":
            material_details = Materials.objects.filter(id=item_details.item)
            for matdetaisl in material_details:
                data['item_details'] = {
                    'id': matdetaisl.id,
                    'name' : matdetaisl.name,
                    'description' : matdetaisl.description,
                    'mat_code' : matdetaisl.mat_code
                }
                # print(material_details)
            if type_details.lower() == 'machinery':
                machinery_details= PmsMachineries.objects.filter(id=item_details.item)
                for mach in machinery_details:
                    data['item_details'] = {
                        'id': mach.id,
                        'code' : mach.code,
                        'equipment_name' : mach.equipment_name

                    }
            activityList = []
            for ac_details in getActivityDetails:
                activityDict = {
                    'id' : ac_details.activity.id,
                    'activity_id' : ac_details.id,
                    'activity_code' : ac_details.activity.code,
                    'activity_description' : ac_details.activity.description,
                }
                activityList.append(activityDict)
            data['activity_details'] = activityList

        return Response(data)

#:::::::::: PMS EXECUTION PURCHASES REQUISITIONS DELETE :::::::::#
class PurchaseRequisitionsDeleteView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesRequisitions.objects.filter(is_deleted=False)
    serializer_class = PurchaseRequisitionsDeleteSerializer


    @response_modify_decorator_update
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

#::::::::::  PMS EXECUTION PURCHASES QUOTATIONS ;::::::::#
class ExecutionPurchaseQuotationsPaymentTermsMasterAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesQuotationsPaymentTermsMaster.objects.all()
    serializer_class = ExecutionPurchaseQuotationsPaymentTermsMasterAddSerializer

    @response_modify_decorator_list
    def list(self, request, args, *kwargs):
        # print(response)
        return response

class ExecutionPurchaseQuotationsPaymentTermsMasterEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesQuotationsPaymentTermsMaster.objects.all()
    serializer_class = ExecutionPurchaseQuotationsPaymentTermsMasterEditSerializer

class ExecutionPurchaseQuotationsPaymentTermsMasterDeleteView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesQuotationsPaymentTermsMaster.objects.all()
    serializer_class = ExecutionPurchaseQuotationsPaymentTermsMasterDeleteSerializer

class ExecutionPurchaseQuotationsAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesQuotations.objects.filter(is_deleted=False)
    serializer_class = ExecutionPurchaseQuotationsAddSerializer
    filter_backends = (DjangoFilterBackend,)

    @response_modify_decorator_list
    def list(self, request, *args, **kwargs):
        # print(response)
        return response

class ExecutionPurchaseQuotationsEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesQuotations.objects.filter(is_deleted=False)
    serializer_class = ExecutionPurchaseQuotationsEditSerializer

class ExecutionPurchaseQuotationsItemListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesQuotations.objects.filter(is_deleted=False)
    serializer_class = ExecutionPurchaseQuotationsItemListSerializer

    def get(self, request, *args, **kwargs):
        req_master_id = self.kwargs['req_master_id']
        item_id = self.kwargs['item_id']
        uom_id = self.kwargs['uom_id']

        # quot_data = dict()
        data = {}
        qout_list = []
        data_dict = {}

        quotation_details = PmsExecutionPurchasesQuotations.objects.filter(requisitions_master=req_master_id,
        item=item_id,
        unit_id = uom_id,
        is_deleted=False)

        for qout_details in quotation_details:
            #print("qout_details",type(qout_details.__dict__['document']))
            if qout_details.__dict__['document'] == "":
                file_url = ''
            else:
                file_url = request.build_absolute_uri(qout_details.document.url)
                # file_url = ''
            if qout_details.__dict__['document_name'] == "":
                # print("Documents-->", qout_details.document_name)
                doc_name = ""                
            else:
                # print("Documents-->", qout_details.document_name)
                doc_name = qout_details.document_name
        
            owned_by = str(qout_details.owned_by) if qout_details.owned_by else ''
            created_by = str(qout_details.created_by) if qout_details.created_by else ''
            created_at = str(qout_details.created_at) if qout_details.created_at else ''
            updated_by = str(qout_details.updated_by) if qout_details.updated_by else ''
            remarks=qout_details.remarks if qout_details.remarks else None
            #print('remarks',remarks)
            quot_data = {
                'id': qout_details.id,
                'vendor_id': qout_details.vendor.id,
                'vendor_code': qout_details.vendor.code,
                'vendor_name': qout_details.vendor.contact_person_name,
                'payment_terms' : qout_details.payment_terms.id,
                'payment_name': qout_details.payment_terms.name,
                'quantity': qout_details.quantity,
                'unit': qout_details.unit.id if qout_details.unit else '',
                'unit_name' : qout_details.unit.c_name if qout_details.unit else '',
                'item': qout_details.item,
                'price': qout_details.price,
                'delivery_date': qout_details.delivery_date,
                'remarks':remarks,
                'document_name': doc_name,
                'document': file_url,
                'created_by': created_by,
                'owned_by': owned_by,
                'created_at':created_at,
                'updated_by':updated_by

            }
            qout_list.append(quot_data)

        item_data = PmsExecutionPurchasesRequisitionsApproval.objects.filter(requisitions_master=req_master_id,arm_approval__gt=0 ).values('item','uom')
        item_uom_list=[x for x in item_data]
        bol_status_list=[]
        for list_value in item_uom_list:
            if PmsExecutionPurchasesQuotations.objects.filter(requisitions_master=req_master_id,item=list_value['item'],
                                unit_id = list_value['uom'],is_deleted=False):
                bol_status_list.append(True)
            else:
                bol_status_list.append(False)
        validation =set(bol_status_list)
        # print('validation',validation)
        if validation == {True}:
            # print("bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb")
            data_dict['quotation_status'] = 1
        else:
            data_dict['quotation_status'] = 0
        #print(data_dict['quotation_status'])
        data['Details'] = qout_list


        data_dict['result'] = qout_list
        # updated by Shubhadeep for CR1
        data_dict['has_comparitive_statement'] = PmsExecutionPurchasesComparitiveStatement.objects.filter(requisitions_master=req_master_id,
            item=item_id).count() > 1
        # --
        if data:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_SUCCESS
        elif len(data) == 0:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_NO_DATA
        else:
            data_dict['request_status'] = 0
            data_dict['msg'] = settings.MSG_ERROR
        data = data_dict

        return Response(data)

# added by Shubhadeep for CR1
class ExecutionPurchaseQuotationsPrevPurchasesView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesQuotations.objects.filter(is_deleted=False)
    serializer_class = ExecutionPurchaseQuotationsItemListSerializer

    def get(self, request, *args, **kwargs):
        item_id = self.kwargs['item_id']
        uom_id = self.kwargs['uom_id']

        skip_requisition = self.request.query_params.get('skip_requisition', None)
        
        data = {}
        qout_list = []
        average_price = 0.0

        quotation_details = PmsExecutionPurchasesQuotations.objects.filter(item=item_id,
        unit_id = uom_id,
        is_deleted=False)
        if skip_requisition is not None:
            quotation_details = quotation_details.exclude(requisitions_master=skip_requisition)
        quotation_details = quotation_details.order_by('-created_at')[:3]

        for qout_details in quotation_details:
            if qout_details.__dict__['document'] == "":
                file_url = ''
            else:
                file_url = request.build_absolute_uri(qout_details.document.url)
            if qout_details.__dict__['document_name'] == "":
                doc_name = ""                
            else:
                doc_name = qout_details.document_name
        
            owned_by = str(qout_details.owned_by) if qout_details.owned_by else ''
            created_by = str(qout_details.created_by) if qout_details.created_by else ''
            created_at = str(qout_details.created_at) if qout_details.created_at else ''
            updated_by = str(qout_details.updated_by) if qout_details.updated_by else ''
            remarks=qout_details.remarks if qout_details.remarks else None
            quot_data = {
                'id': qout_details.id,
                'vendor_id': qout_details.vendor.id,
                'vendor_code': qout_details.vendor.code,
                'vendor_name': qout_details.vendor.contact_person_name,
                'payment_terms' : qout_details.payment_terms.id,
                'payment_name': qout_details.payment_terms.name,
                'quantity': qout_details.quantity,
                'unit': qout_details.unit.id if qout_details.unit else '',
                'unit_name' : qout_details.unit.c_name if qout_details.unit else '',
                'item': qout_details.item,
                'price': qout_details.price,
                'delivery_date': qout_details.delivery_date,
                'remarks':remarks,
                'document_name': doc_name,
                'document': file_url,
                'created_by': created_by,
                'owned_by': owned_by,
                'created_at':created_at,
                'updated_by':updated_by

            }
            qout_list.append(quot_data)

        if len(qout_list) > 0:
            from statistics import mean 
            average_price = round(mean([d['price'] for d in qout_list]), 2)
        data['result'] = qout_list
        data['average_price'] = average_price

        return Response(data)
# --

class ExecutionPurchaseQuotationsDeleteView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesQuotations.objects.filter(is_deleted=False)
    serializer_class = ExecutionPurchaseQuotationsDeleteSerializer
    
class ExecutionPurchaseQuotationsApprovedListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesQuotations.objects.filter(is_deleted=False)
    serializer_class = ExecutionPurchaseQuotationsApprovedListSerializer

    def get(self, request, *args, **kwargs):
        data_dict = {}
        data = {}
        dataList = {}
        reqMasterID = self.kwargs['req_master_id']

        # print("reqMasterID",reqMasterID)
        reqApprovalDetails = PmsExecutionPurchasesRequisitionsApproval.objects.filter(
            arm_approval__gt=False,requisitions_master=reqMasterID,is_deleted=False)
        #print("reqApprovalDetails : ",reqApprovalDetails)

        reqList = []
        # clist=[]
        for getReqApprovalDetails in reqApprovalDetails:
            # print("getReqApprovalDetails",getReqApprovalDetails)
            data= {
                # 'requisitions_master' : getReqApprovalDetails.requisitions_master,
                'id':getReqApprovalDetails.id,
                'quotation_approved': getReqApprovalDetails.quotation_approved,
                'approved_quantity':float(getReqApprovalDetails.approved_quantity)
                # 'item_id': getReqApprovalDetails.item,
                # 'item' : getReqApprovalDetails.item,
                # 'item_name' : getReqApprovalDetails.item_code.name,
                # 'item_desctiption' : getReqApprovalDetails.item_code.description,
            }
            # print("Type ID : ",getReqApprovalDetails.type)
            type_name = PmsExecutionPurchasesRequisitionsTypeMaster.objects.only('type_name').get(
                id=getReqApprovalDetails.type.id).type_name
            # print("type_name",type_name)
            # if type_name.lower() == "materials":
            material_details = Materials.objects.filter(id=getReqApprovalDetails.item)
            for matdetaisl in material_details:
                data['item_type'] = {
                    'item_id': matdetaisl.id,
                    'name': matdetaisl.name,
                    'mat_code': matdetaisl.mat_code,
                    'description': matdetaisl.description
                }
                # print(material_details)
            if type_name.lower() == 'machinery':
                machinery_details = PmsMachineries.objects.filter(id=getReqApprovalDetails.item)
                for mach in machinery_details:
                    data['item_type'] = {
                        'item_id': mach.id,
                        'code': mach.code,
                        'equipment_name': mach.equipment_name
                    }

            # print("This Test------->")
            # print("Item --> ", getReqApprovalDetails.item)

            getRequisition = PmsExecutionPurchasesRequisitions.objects.filter(
                item=str(getReqApprovalDetails.item),requisitions_master=reqMasterID)

            # print("getRequisition -----> ", getRequisition)
            details = {}
            for reqDetails in getRequisition:
                # print("Requisition ID: ",reqDetails.id)
                # print("--> quantity: ",reqDetails.quantity)
                # print("--> Unit",reqDetails.uom)
                details = {
                    'quantity' : reqDetails.quantity,
                    'unit' : getReqApprovalDetails.uom.id if getReqApprovalDetails.uom else '',
                    'unit_name' : getReqApprovalDetails.uom.c_name if getReqApprovalDetails.uom else ''
                }
                # print("details",details)

            data['item_details'] = details
            # print(data)
            # clist.append(details)
            reqList.append(data)
            # print(reqList)
            dataList['Item_Approved_List'] = reqList

            # print("data", dataList)

        data_dict['result'] = dataList
        if data:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_SUCCESS
        elif len(data) == 0:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_NO_DATA
        else:
            data_dict['request_status'] = 0
            data_dict['msg'] = settings.MSG_ERROR
        data = data_dict

        return Response(data)

class PurchaseQuotationApprovedView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesRequisitionsApproval.objects.filter(is_deleted=False)
    serializer_class = PurchaseQuotationApprovedSerializer

# added by Shubhadeep for CR1
class PurchaseQuotationRevertApprovalView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesRequisitionsApproval.objects.filter(is_deleted=False)
    serializer_class = PurchaseQuotationRevertApprovalSerializer
# --

class ExecutionPurchaseQuotationsItemTotalListView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesQuotations.objects.filter(is_deleted=False)
    serializer_class = ExecutionPurchaseQuotationsItemListSerializer


    def get(self, request, *args, **kwargs):
        req_master_id = self.kwargs['req_master_id']

        # quot_data = dict()
        data = {}
        qout_list = []
        data_dict = {}
        idata = {}

        quotation_details = PmsExecutionPurchasesQuotations.objects.filter(requisitions_master=req_master_id,
                                                                           is_deleted=False)
        for qout_details in quotation_details:
            file_url = request.build_absolute_uri(qout_details.document.url)
            owned_by = str(qout_details.owned_by) if qout_details.owned_by else ''
            created_by = str(qout_details.created_by) if qout_details.created_by else ''
            quot_data = {
                'id': qout_details.id,
                'vendor_id': qout_details.vendor.id,
                'vendor_code': qout_details.vendor.code,
                'vendor_name': qout_details.vendor.contact_person_name,
                'remarks':qout_details.remarks,
                'payment_terms': qout_details.payment_terms.id,
                'payment_name': qout_details.payment_terms.name,
                'quantity': qout_details.quantity,
                'unit': qout_details.unit.id if qout_details.unit else '',
                'unit_name': qout_details.unit.c_name if qout_details.unit else '',
                'item': qout_details.item,
                'price': qout_details.price,
                'delivery_date': qout_details.delivery_date,
                'document_name': qout_details.document_name,
                'document': file_url,
                'created_by': created_by,
                'owned_by': owned_by

            }

            type = PmsExecutionPurchasesRequisitionsMaster.objects.only('type').get(id=req_master_id).type
            type_name = PmsExecutionPurchasesRequisitionsTypeMaster.objects.only('type_name').get(
                id=str(type)).type_name

            # print("type_name", type_name)
            # print("type_name", type_name)

            if type_name.lower() == "materials":
                material_details = Materials.objects.filter(id=qout_details.item)
                for matdetaisl in material_details:
                    quot_data['item_details'] = {
                        'id': matdetaisl.id,
                        'name': matdetaisl.name,
                        'mat_code': matdetaisl.mat_code,
                        'description': matdetaisl.description
                    }
                    # print(material_details)
            if type_name.lower() == 'machinery':
                machinery_details = PmsMachineries.objects.filter(id=qout_details.item)
                for mach in machinery_details:
                    quot_data['item_details'] = {
                        'id': mach.id,
                        'code': mach.code,
                        'equipment_name': mach.equipment_name
                    }

            qout_list.append(quot_data)

        data['Details'] = qout_list

        # print('<<<<<<<<<<<<<<<<< Data >>>>>>>>>>>>>>>\n',data)

        data_dict['result'] = qout_list
        if data:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_SUCCESS
        elif len(data) == 0:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_NO_DATA
        else:
            data_dict['request_status'] = 0
            data_dict['msg'] = settings.MSG_ERROR
        data = data_dict

        return Response(data)


class PurchaseQuotationsForApprovedListView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesRequisitionsMaster.objects.filter(is_deleted=False).order_by('-mr_date')
    serializer_class = PurchaseQuotationsForApprovedListSerializer
    pagination_class = CSPageNumberPagination

    def get_queryset(self):
        # queryset=self.queryset.filter(status=1)
        filter = {}
        exclude_fields = {}
        project = self.request.query_params.get('project', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        site_location = self.request.query_params.get('site_location', None)
        type_name = self.request.query_params.get('type_name', None)
        search = self.request.query_params.get('search', None)
        item_type = self.request.query_params.get('item_type', None)
        item = self.request.query_params.get('item', None)
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        sort_field='-id'

        section_name = self.request.query_params.get('section_name', None)
        logdin_user = self.request.user
        print('logdin_user_id',logdin_user)
        section_details=TCoreOther.objects.get(cot_name__iexact=section_name)
        approval_master_details = PmsApprovalPermissonMatser.objects.filter(section=section_details.id,approval_user=logdin_user,is_deleted=False)
        print('approval_master_details',approval_master_details)
        if approval_master_details:
            approval_master_details = approval_master_details[0]
            approval_user_level = approval_master_details.permission_level
            print('approval_user_level',approval_user_level)
           

            approval_level_count = PmsApprovalPermissonMatser.objects.filter(
                section=section_details.id,is_deleted=False).exclude(approval_user=logdin_user).count()
            print('approval_level_count',approval_level_count,type(approval_level_count))
            approval_ids = list()
            for level in range(1,approval_level_count+1):
                print('level',level)
                next_approval_level_no = 'L' + str(int(approval_user_level.split('L')[1]) + 1)
                pass
            # for e_approval_details in approval_details:
            #     
            #     print('next_approval_level',next_approval_level)
            #     next_id = PmsApprovalPermissonMatser.objects.filter(
            #         section=section_details.id,
            #         is_deleted=False,
            #         permission_level=next_approval_level
            #         ).exclude(approval_user=logdin_user).values_list('id',flat=True)
            #     approval_ids.add(next_id)
            # print('approval_ids',approval_ids)
            # exclude_fields['id__in']=PmsExecutionPurchasesComparitiveStatementLog.objects.filter(
            #     (Q(approval_permission_user_level_id=approval_master_details.id) | Q(approval_permission_user_level_id__in=approval_ids)),is_approved=True).values_list('requisitions_master',flat=True)
                        
        #print('exclude_fields',exclude_fields)
        if field_name and order_by:
            if field_name == 'project' and order_by == 'asc':
                sort_field='project__project_g_id'
                # return self.queryset.filter((Q(completed_status__isnull=True,status=4)|Q(status=3)),is_deleted=False).order_by('project__project_g_id')
            elif field_name == 'project' and order_by == 'desc':
                sort_field='-project__project_g_id'
                # return self.queryset.filter((Q(completed_status__isnull=True,status=4)|Q(status=3)),is_deleted=False).order_by('-project__project_g_id')

            elif field_name == 'site_location' and order_by == 'asc':
                sort_field='site_location__name'
                # return self.queryset.filter((Q(completed_status__isnull=True,status=4)|Q(status=3)), is_deleted=False).order_by('site_location__name')
            elif field_name == 'site_location' and order_by == 'desc':
                sort_field='-site_location__name'
                # return self.queryset.filter((Q(completed_status__isnull=True,status=4)|Q(status=3)), is_deleted=False).order_by('-site_location__name')

            elif field_name == 'mr_date' and order_by == 'asc':
                sort_field='mr_date'
                # return self.queryset.filter((Q(completed_status__isnull=True,status=4)|Q(status=3)), is_deleted=False).order_by('mr_date')
            elif field_name == 'mr_date' and order_by == 'desc':
                sort_field='-mr_date'
                # return self.queryset.filter((Q(completed_status__isnull=True,status=4)|Q(status=3)), is_deleted=False).order_by('-mr_date')

            # elif field_name == 'required_on' and order_by == 'asc':
            #     return self.queryset.filter(is_deleted=False).order_by('required_on')
            # elif field_name == 'required_on' and order_by == 'desc':
            #     return self.queryset.filter(is_deleted=False).order_by('-required_on')

            # elif field_name == 'item' and order_by == 'asc':
            #     return self.queryset.filter(status=True, is_deleted=False).order_by('item')
            # elif field_name == 'item' and order_by == 'desc':
            #     return self.queryset.filter(status=True, is_deleted=False).order_by('-item')  

        if search :
            filter['project__project_g_id']=search
            # print("This is if condition entry")
            # queryset = self.queryset.filter((Q(completed_status__isnull=True,status=4)|Q(status=3)),project__project_g_id=search)

            # print('queryset_search::::::::::::::::::::', queryset)
            # return queryset


        if start_date and end_date:
            start_object = datetime.strptime(start_date, '%Y-%m-%d').date()
            filter['mr_date__gte'] = start_object
            end_object = datetime.strptime(end_date, '%Y-%m-%d').date()
            filter['mr_date__lte'] = end_object + timedelta(days=1)

            # queryset = self.queryset.filter((Q(completed_status__isnull=True,status=4)|Q(status=3)),**filter)

            # return queryset

        if site_location:
            #print('site_location',site_location)
            filter['site_location__in']=list(map(int,site_location.split(",")))

        if project:
            filter['project__in']=list(map(int,project.split(",")))


        if type_name:
            filter['type'] = int(type_name)
            # print("halla ")
            # if type_name.lower() == 'materials':
            #     filter['type'] = 1
            # elif type_name.lower() == 'machinery':
            #     print("hala ")
            #     filter['type'] = 2

        if item:
            filter['item__in']= list(map(int,item.split(",")))
            # print("item:::::::::::::::::::",filter)
            

        if filter:
            #print('filter')
            queryset = self.queryset.filter((Q(completed_status__isnull=True,status=4)|Q(status=3)),**filter).exclude(**exclude_fields).order_by(sort_field)
            #print('queryset',queryset.query)
            return queryset
        else:
            queryset=self.queryset.filter(Q(completed_status__isnull=True,status=4)|Q(status=3)).exclude(**exclude_fields).order_by(sort_field)
            #print('queryset',queryset.query)
            return queryset
    
    def str_to_float(self, obj):
        obj['net_landed_cost'] = float(obj['net_landed_cost'])
        return obj

    def float_to_string(self, obj):
        obj['net_landed_cost'] = "{0:.2f}".format(obj['net_landed_cost'])
        return obj



    def get(self, request, *args, **kwargs):
        data_dict = {}
        po_data_dict = {}
        response = super(PurchaseQuotationsForApprovedListView, self).get(request, args, kwargs)



        master_list=[]
        for data in response.data['results']:
            #print("data_id",data)
   
            # item_dict = {}
            # approveItem_dict = {}
            po_data_dict = {}
            get_approval_details = PmsExecutionPurchasesRequisitionsApproval.objects.filter(
                requisitions_master=data['id'],
                is_deleted=False,arm_approval__gte=0) #,uom=data['uom']



            #print("get_approval_details",get_approval_details)
            if get_approval_details:
                approveItem_list = []
                for approve_data in get_approval_details:
                    approveItem_dict = {}

                    #print("approve_data_item",approve_data.item)
                    get_quotation_details = PmsExecutionPurchasesQuotations.objects.filter(requisitions_master=data['id'],
                    is_deleted=False,item = approve_data.item)
                    #print("quotation",get_quotation_details)
                    quoted_item_list =[]
                    quoatedData_list = [] #forvender
                    if get_quotation_details:

                        comparitiveStatement = PmsExecutionPurchasesComparitiveStatement.objects.filter(
                            requisitions_master=data['id'],item=approve_data.item,uom=approve_data.uom,is_deleted=False)
                        #print('comparitiveStatement',comparitiveStatement.values())
                        #ranking_details = list()
                        if comparitiveStatement:
                            comparitiveStatement = comparitiveStatement.values()
                            comparitiveStatement = list(map(self.str_to_float, comparitiveStatement))
                            list_data = sorted(comparitiveStatement, key = lambda i: i['net_landed_cost'])
                            comparitiveStatement = list(map(self.float_to_string, comparitiveStatement))
                            l = 0
                            for data1 in list_data:
                                l+=1
                                ll = "L"+str(l)
                                index = [index for (index, d) in enumerate(comparitiveStatement) if d['id']==data1['id']][0]
                                comparitiveStatement[index]['ranking']=ll
                            approveItem_dict['ranking_details'] = comparitiveStatement

                        vendor_list=[]
                        for quote_data in get_quotation_details:                            
                            quoatedData_dict = {
                                'vendor_id' : quote_data.vendor.id,
                                'vendor_name' : quote_data.vendor.contact_person_name,
                                'vendor_code' : quote_data.vendor.code,
                                'quantity' : quote_data.quantity,
                                'unit_id' : quote_data.unit.id if quote_data.unit else '',
                                'unit_name' : quote_data.unit.c_name if quote_data.unit else '',
                                'price' : quote_data.price,
                                'ranking':None
                            }
                            if comparitiveStatement:
                                for e_comparitiveStatement in comparitiveStatement:
                                    if quote_data.vendor.id == e_comparitiveStatement['vendor_id']:
                                        quoatedData_dict['ranking'] = e_comparitiveStatement['ranking']

                            vendor_list.append(quote_data.vendor.id)
                            quoatedData_list.append(quoatedData_dict)
                        #print("vendor_list",vendor_list)
                        #print("quoatedData_list",quoatedData_list)
                        approveItem_dict['vendor_details'] = quoatedData_list
                    else:
                        approveItem_dict['vendor_details'] = []

                    approveItem_dict['approved_item'] = approve_data.item
                    approveItem_dict['approved_quantity'] = approve_data.approved_quantity

                    # approveItem_dict['requisition_id']=data['id']
                    # approveItem_dict['project'] = data['project']
                    # approveItem_dict['site_location'] = data['site_location']

                    # approveItem_list.append(approveItem_dict)

                
                    type_name = PmsExecutionPurchasesRequisitionsTypeMaster.objects.only('type_name').get(id=approve_data.type.id).type_name
                    # if (type_name).lower() == "materials":
                    material_details = Materials.objects.filter(id=approve_data.item).values('name')
                    approveItem_dict['item_name'] = material_details[0]['name']
                    if (type_name).lower() == 'machinery':
                        machinery_details = PmsMachineries.objects.filter(id=approve_data.item).values('equipment_name')
                        approveItem_dict['item_name'] = machinery_details[0]['equipment_name']

                    approveItem_dict['uom'] = approve_data.uom.id
                    approveItem_dict['uom_name'] = approve_data.uom.c_name

                    #level of approvals list 
                    # requisitions_master_id = self.request.query_params.get('requisitions_master_id', None)
                    # item_id = self.request.query_params.get('item_id', None)
                    # uom = self.request.query_params.get('uom', None)

                    section_name = self.request.query_params.get('section_name', None)
                    if section_name:
                        permission_details=[]
                        section_details=TCoreOther.objects.get(cot_name__iexact=section_name)
                        approval_master_details = PmsApprovalPermissonMatser.objects.filter(section=section_details.id,is_deleted=False)
                        #print("approval_master_details",approval_master_details)
                        # type_details= PmsExecutionPurchasesRequisitionsMaster.objects.get(id=requisitions_master_id).type
                        log_details=PmsExecutionPurchasesComparitiveStatementLog.objects.\
                                filter(
                                    requisitions_master=data['id'],
                                    uom=approve_data.uom,
                                    item=approve_data.item,vendor__in=vendor_list).\
                                    values('id','is_approved','approval_permission_user_level','vendor__contact_person_name','vendor','created_at','comment')
                       
                        amd_list=[]
                        l_d_list=set()
                        for l_d in log_details:
                            l_d_list.add(l_d['approval_permission_user_level'])

                        for a_m_d in approval_master_details:
                            if l_d_list:
                                if a_m_d.id in l_d_list:
                                    l_d=log_details.filter(approval_permission_user_level=a_m_d.id).order_by('-id')[0]
                                    f_name = a_m_d.approval_user.first_name if a_m_d.approval_user else '' 
                                    l_name = a_m_d.approval_user.last_name if a_m_d.approval_user else '' 
                                    var=a_m_d.permission_level
                                    res = re.sub("\D", "", var)
                                    permission_dict={
                                        "user_level":a_m_d.permission_level,
                                        "approval":l_d['is_approved'],
                                        "permission_num":int(res),
                                        "approved_vendor":l_d['vendor__contact_person_name'],
                                        "approved_vendor_id":l_d['vendor'],
                                        "approved_date":l_d['created_at'],
                                        "approve_comment":l_d['comment'],
                                        "user_details":{
                                            "id":a_m_d.approval_user.id if a_m_d.approval_user else None,
                                            "email":a_m_d.approval_user.email if a_m_d.approval_user else None,
                                            "name":  f_name +' '+l_name,
                                            "username":a_m_d.approval_user.username
                                            }
                                    }
                                        

                                else:
                                    f_name = a_m_d.approval_user.first_name if a_m_d.approval_user else '' 
                                    l_name = a_m_d.approval_user.last_name if a_m_d.approval_user else '' 
                                    var=a_m_d.permission_level
                                    res = re.sub("\D", "", var)
                                    permission_dict={
                                        "user_level":a_m_d.permission_level,
                                        "permission_num":int(res),
                                        "approval":None,
                                        "approved_vendor":None,
                                        "approved_vendor_id":None,
                                        "approved_date":None,
                                        "approve_comment":None,
                                        "user_details":{
                                            "id":a_m_d.approval_user.id if a_m_d.approval_user else None,
                                            "email":a_m_d.approval_user.email if a_m_d.approval_user else None,
                                            "name":  f_name +' '+l_name,
                                            "username":a_m_d.approval_user.username
                                            }
                                    }

                                permission_details.append(permission_dict)
                            else:
                                f_name = a_m_d.approval_user.first_name if a_m_d.approval_user else '' 
                                l_name = a_m_d.approval_user.last_name if a_m_d.approval_user else '' 
                                var=a_m_d.permission_level
                                res = re.sub("\D", "", var)
                                permission_dict={
                                        "user_level":a_m_d.permission_level,
                                        "permission_num":int(res),
                                        "approval":None,
                                        "approved_vendor":None,
                                        "approved_vendor_id":None,
                                        "approved_date":None,
                                        "approve_comment":None,
                                        "user_details":{
                                            "id":a_m_d.approval_user.id if a_m_d.approval_user else None,
                                            "email":a_m_d.approval_user.email if a_m_d.approval_user else None,
                                            "name":  f_name +' '+l_name,
                                            "username":a_m_d.approval_user.username
                                            }
                                    }
                                permission_details.append(permission_dict)
                        approveItem_dict['permission_details']=permission_details    
                        




                        po_details = PmsExecutionPurchasesPO.objects.filter(is_deleted=False,requisitions_master=data['id']).order_by('-id')
                        # print("po_details",po_details)
                        if po_details:
                            for po in po_details:
                                # print("hkg",po.id)
                                item = PmsExecutionPurchasesPOItemsMAP.objects.filter(is_deleted=False,purchase_order=po.id,item=approve_data.item)
                                # print("item", item)
                                if item:
                                    po_data_dict={
                                        'po_no': po.__dict__['po_no'],
                                        'po_amount': po.__dict__['po_amount'],
                                        'po_date': po.__dict__['created_at']
                                    }
                                    break
                        else:
                            po_data_dict= {
                                'po_no': "",
                                'po_amount': "",
                                'po_date': ""
                            }
                

                        approveItem_dict['last_po'] = po_data_dict
                    
                    approveItem_list.append(approveItem_dict)
                reqquisition_data={}
                reqquisition_data['mr_date'] = data['mr_date']
                reqquisition_data['requisition_id']=data['id']
                reqquisition_data['project'] = data['project']
                reqquisition_data['project_code'] = PmsProjects.objects.only('project_g_id').get(pk=data['project']).project_g_id
                reqquisition_data['project_name'] = PmsProjects.objects.only('name').get(pk=data['project']).name
                reqquisition_data['site_location'] = data['site_location']
                reqquisition_data['site_location_name'] = PmsSiteProjectSiteManagement.objects.only('name').get(pk=data['site_location']).name
                reqquisition_data['item_data'] = approveItem_list
                reqquisition_data['type'] = {
                        'id': data['type'],
                        'type_name': PmsExecutionPurchasesRequisitionsTypeMaster.objects.get(id=data['type']).type_name,
                        'code':  PmsExecutionPurchasesRequisitionsTypeMaster.objects.get(id=data['type']).code
                    }
                master_list.append(reqquisition_data)
                # print("approveItem_list",approveItem_list)
        #data_dict['results'] = master_list
        response.data['results'] = master_list
        # data_dict['approval_dict']=approval_list
        # data_dict['permission_details']=permission_details
        if response.data:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_SUCCESS
        elif len(response.data) == 0:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_NO_DATA
        else:
            data_dict['request_status'] = 0
            data_dict['msg'] = settings.MSG_ERROR
        #response.data = data_dict
        return response




#::::::::::  PMS EXECUTION PURCHASES REQUISITIONS TYPE MASTER ADD ;::::::::#
class ExecutionPurchasesRequisitionsTypesMasterAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesRequisitionsTypeMaster.objects.filter(is_deleted=False) 
    serializer_class = ExecutionPurchasesRequisitionstypeMasterAddSerializer
    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        # print(response)
        #response = super(ExecutionPurchasesRequisitionsTypesMasterAddView, self).get(request, args, kwargs)

        return response

class ExecutionPurchasesRequisitionsTypesMasterEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesRequisitionsTypeMaster.objects.filter(is_deleted=False)
    serializer_class = ExecutionPurchasesRequisitionsTypesMasterEditSerializer

    @response_modify_decorator_list
    def list(self, request, *args, **kwargs):
        # print(response)
        return response

class ExecutionPurchasesRequisitionsTypesMasterDeleteView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesRequisitionsTypeMaster.objects.filter(is_deleted=False)
    serializer_class = ExecutionPurchasesRequisitionsTypesMasterDeleteSerializer

#:::::::::: PMS EXECUTION PURCHASES REQUISITIONS TYPE TO ITEM CODE LIST :::::::::#

class PurchasesRequisitionsTypeToItemCodeCurrentStockListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionUpdatedStock.objects.all()
    serializer_class =ExecutionCurrentStockReportSerializer
    
    def get(self, request,*args,**kwargs):
        try:
            data_dict={}
            project = self.request.query_params.get('project')
            site_location = self.request.query_params.get('site_location')
            item_code = self.request.query_params.get('item_code')
            unit = self.request.query_params.get('unit')
            type_code = self.request.query_params.get('type_code')

            if type_code and unit:
                type_name = PmsExecutionPurchasesRequisitionsTypeMaster.objects.only('type_name').get(
                    code=type_code).type_name
                #print('type_name',type_name)
                type_id = PmsExecutionPurchasesRequisitionsTypeMaster.objects.only('id').get(
                    code=type_code).id
                material_id = Materials.objects.only('id').get(
                    mat_code=item_code).id
            
                materials=Materials.objects.filter(id=material_id)
                if materials:
                    for m_l in materials:
                        mat_dict={
                            'id':m_l.id,
                            'code':m_l.mat_code,
                            'name':m_l.name,
                            'description':m_l.description
                        }
                    
                    unit_details = TCoreUnit.objects.filter(id=unit)
                    if unit_details : 
                        for u_l in unit_details:
                            unit_dict = {
                                'id': u_l.id,
                                'unit': u_l.c_name
                            }
                    else:
                        unit_dict = {}
                    stock_dict={
                        'id':mat_dict['id'],
                        'code':mat_dict['code'],
                        'name':mat_dict['name'],
                        'description':mat_dict['description'],
                        'unit':unit_dict,
                    }
                else:
                    stock_dict={}
                
                # stock_list.append(stock_dict)

                '''
                    Modified After implementation of CRON functionlaity
                    Author : Rupam Hazra
                    Date : 06.05.2020
                '''
                # stock_item=PmsExecutionUpdatedStock.objects.filter(
                #     project=project, 
                #     site_location=site_location, 
                #     type=type_id, 
                #     uom=unit,
                #     item=material_id
                #     )
                stock_item=PmsExecutionStock.objects.filter(
                    project=project, 
                    site_location=site_location, 
                    type=type_id, 
                    uom=unit,
                    item=material_id
                    ).values('closing_stock').order_by('-stock_date__date').first()
                #print("stock_item",stock_item)
                
                # if stock_item:
                #     for c_s in stock_item:
                #         if c_s.issued_stock:
                #             t_issued_stock = float(c_s.issued_stock)
                #         else:
                #             t_issued_stock = 0.0

                #         if c_s.opening_stock:
                #             t_opening_stock = float(c_s.opening_stock)
                #         else:
                #             t_opening_stock = 0.0

                #         if c_s.recieved_stock:
                #             t_recieved_stock = float(c_s.recieved_stock)
                #         else:
                #             t_recieved_stock = 0.0
                        
                #         print('check...',t_opening_stock+t_recieved_stock-t_issued_stock)
                if stock_item:
                    stock_dict['current_stock']=stock_item['closing_stock'] if stock_item['closing_stock'] else 0
                else:
                    stock_dict['current_stock'] = 0
                
            
            elif type_code and unit is None:
                type_name = PmsExecutionPurchasesRequisitionsTypeMaster.objects.only('type_name').get(
                    code=type_code).type_name
                type_id = PmsExecutionPurchasesRequisitionsTypeMaster.objects.only('id').get(
                    code=type_code).id
                material_id = Materials.objects.only('id').get(
                    mat_code=item_code).id

                materials=Materials.objects.filter(id=material_id)
                unit_list =[]
                if materials:
                    for m_l in materials:
                        stock_dict={
                            'id':m_l.id,
                            'code':m_l.mat_code,
                            'name':m_l.name,
                            'description':m_l.description
                        }
                        unit_details = MaterialsUnitMapping.objects.filter(material=m_l.id)                                            
                        if unit_details:
                            for u_d in unit_details:
                                unit_dict = {
                                    'id': u_d.unit.id,
                                    'unit': u_d.unit.c_name
                                }
                                '''
                                    Modified After implementation of CRON functionlaity
                                    Author : Rupam Hazra
                                    Date : 06.05.2020
                                '''
                                stock_item=PmsExecutionStock.objects.filter(
                                project=project, 
                                site_location=site_location, 
                                type=type_id, 
                                uom=u_d.unit.id,
                                item=material_id
                                ).values('closing_stock').order_by('-stock_date__date').first()
                                #print("stock_item",stock_item)  
                                if stock_item:
                                    unit_dict['current_stock']=stock_item['closing_stock'] if stock_item['closing_stock'] else 0
                                else:
                                    unit_dict['current_stock'] = 0
                                # stock_item=PmsExecutionUpdatedStock.objects.filter(
                                #     project=project, site_location=site_location, type=type_id, uom= u_d.unit.id,item=material_id)                 
                                # print("stock_item",stock_item)                  
                                # if stock_item:
                                #     for c_s in stock_item:
                                #         if c_s.issued_stock:
                                #             t_issued_stock = float(c_s.issued_stock)
                                #         else:
                                #             t_issued_stock = 0.0

                                #         if c_s.opening_stock:
                                #             t_opening_stock = float(c_s.opening_stock)
                                #         else:
                                #             t_opening_stock = 0.0

                                #         if c_s.recieved_stock:
                                #             t_recieved_stock = float(c_s.recieved_stock)
                                #         else:
                                #             t_recieved_stock = 0.0
                                
                                #unit_dict['current_stock']=(t_opening_stock+t_recieved_stock-t_issued_stock)
                                    
                                # else:
                                #     unit_dict['current_stock']=0

                                unit_list.append(unit_dict)
                        else:
                            unit_list=[]

                        stock_dict['unit'] = unit_list                       
                else:
                    stock_dict={}

            data_dict['results']=stock_dict
            if stock_dict:
                data_dict['request_status'] = 1
                data_dict['msg'] = settings.MSG_SUCCESS
            elif len(stock_dict) == 0:
                data_dict['request_status'] = 1
                data_dict['msg'] = settings.MSG_NO_DATA
            else:
                data_dict['request_status'] = 0
                data_dict['msg'] = settings.MSG_ERROR
            #stock_list = data_dict
            return Response(data_dict)
        except Exception as e:
            raise e


class PurchasesRequisitionsTypeToItemCodeListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesRequisitionsTypeMaster.objects.filter(is_deleted=False)
    serializer_class = PurchasesRequisitionsTypeToItemCodeListSerializer

    def get(self, request, *args, **kwargs):
        data = {}
        data_dict = {}
        type_code = self.request.query_params.get('type_code')
        # print('type_code', type_code)
        unit = self.request.query_params.get('unit')
        # item_code = self.request.query_params.get('item_code')
        search=self.request.query_params.get('search')
        #print('search', search)
        item_list = list()
        if type_code and unit:
            
            type_name = PmsExecutionPurchasesRequisitionsTypeMaster.objects.only('type_name').get(
                code=type_code).type_name
            #print('type_name', type_name.lower())
            type_id = PmsExecutionPurchasesRequisitionsTypeMaster.objects.only('id').get(
                code=type_code).id
            
            # if type_name.lower() == "materials":
            if search:
                search_data=search
                #print('search_data',search_data)
                material_details = Materials.objects.filter(is_deleted=False,description__icontains=search_data,type_code=type_code)
                #print('material_details',material_details)
                material_list = list()
                for details in material_details:
                    data_mat = {
                        'id': details.id,
                        'name': details.name,
                        'code': details.mat_code,
                        'description': details.description
                    }
                    # print('data_mat',data_mat)
                    item_list.append(data_mat)
                    getUnitDetails = MaterialsUnitMapping.objects.filter(
                        material=details.id,unit=unit)
                    # print(getUnitDetails)
                    unit_list = list()
                    for unitDetails in getUnitDetails:
                        # print(unitDetails.unit.c_name)
                        unit_dict = {
                            'id': unitDetails.unit.id,
                            'unit': unitDetails.unit.c_name
                        }
                        # print(unit_dict)
                        unit_list.append(unit_dict)
                        # print(unit_list)
                    data_mat['unit'] = unit_list
                        # current_stock_d = PmsExecutionUpdatedStock.objects.filter(
                        #     item=details.id,
                        #     type=type_id, uom_id=int(unit),
                        #     is_deleted=False)
                        # # print('current_stock_d', current_stock_d)
                        # if current_stock_d:
                        #     for e_current_stock_d in current_stock_d:
                        #         if e_current_stock_d.opening_stock and e_current_stock_d.recieved_stock and e_current_stock_d.issued_stock:

                        #             data_mat['current_stock'] = (float(e_current_stock_d.opening_stock) + float(e_current_stock_d.recieved_stock)) - float(e_current_stock_d.issued_stock)
                        #         else:
                        #             e_current_stock_d.opening_stock=0.0 
                        #             e_current_stock_d.recieved_stock=0.0 
                        #             e_current_stock_d.issued_stock=0.0
                        #             data_mat['current_stock'] = (float(e_current_stock_d.opening_stock) + float(e_current_stock_d.recieved_stock)) - float(e_current_stock_d.issued_stock)

                        # else:
                        #     data_mat['current_stock'] = 0
                        # #data['Materials'] = material_list
                        # print(data)
            if type_name.lower() == "machinery":
                # print('Material')
                # machineries_details = PmsMachineries.objects.all()
                machineries_details = PmsProjectsMachinaryMapping.objects.filter(project=project, is_deleted=False)
                # print('machineries_details', machineries_details)
                #machine_list = list()
                for m_details in machineries_details:
                    data_machine = {
                        'id': m_details.id,
                        'description':'',
                        'code': m_details.machinary.code,
                        'name': m_details.machinary.equipment_name,
                    }
                    item_list.append(data_machine)
                #data['Machinery'] = machine_list
            pass
        elif type_code and unit is None:
            #print('fdddfdffdf')
            type_name = PmsExecutionPurchasesRequisitionsTypeMaster.objects.only('type_name').get(
                code=type_code).type_name
            # if type_name.lower() == "materials":
                # print('Material')
                # unit_list = dict()
            if search:
                search_data=search
                material_details = Materials.objects.filter(description__icontains=search_data,is_deleted=False,type_code=type_code)
                #material_list = list()
                for details in material_details:
                    data_mat = {
                        'id': details.id,
                        'name': details.name,
                        'code': details.mat_code,
                        'description': details.description
                    }
                    item_list.append(data_mat)
                    getUnitDetails = MaterialsUnitMapping.objects.filter(
                        material=details.id)
                    # print(getUnitDetails)
                    unit_list = list()
                    for unitDetails in getUnitDetails:
                        # print(unitDetails.unit.c_name)
                        unit_dict = {
                            'id': unitDetails.unit.id,
                            'unit': unitDetails.unit.c_name
                        }
                        # print(unit_dict)
                        unit_list.append(unit_dict)
                        # print(unit_list)
                    data_mat['unit'] = unit_list
                    #data['Materials'] = material_list
                    # print(data)
            if type_name.lower() == "machinery":
                # print('Material')
                machineries_details = PmsMachineries.objects.filter(is_deleted=False)
                #machine_list = list()
                for m_details in machineries_details:
                    data_machine = {
                        'id': m_details.id,
                        'description':'',
                        'code': m_details.code,
                        'name': m_details.equipment_name,
                    }
                    item_list.append(data_machine)
            
                #data['Machinery'] = machine_list
        data_dict['result'] = item_list
        if item_list:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_SUCCESS
        elif len(item_list) == 0:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_NO_DATA
        else:
            data_dict['request_status'] = 0
            data_dict['msg'] = settings.MSG_ERROR
        data = data_dict
        # return data

        return Response(data)




class ExecutionPurchasesComparitiveStatementAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesComparitiveStatement.objects.filter()
    serializer_class = ExecutionPurchasesComparitiveStatementAddSerializer

    def get_queryset(self):
        requisitions_master_id = self.request.query_params.get('requisitions_master_id', None)
        item_id = self.request.query_params.get('item_id', None)
        uom = self.request.query_params.get('uom', None)
        # print('requisitions_master_id',requisitions_master_id)
        if requisitions_master_id and item_id and uom:
            # updated by shubhadeep
            queryset =  self.queryset.filter(requisitions_master=requisitions_master_id,item=item_id,uom=uom,is_deleted=False)
            return queryset

    def str_to_float(self, obj):
        obj['net_landed_cost'] = float(obj['net_landed_cost'])
        return obj

    def float_to_string(self, obj):
        obj['net_landed_cost'] = "{0:.2f}".format(obj['net_landed_cost'])
        return obj

    def get(self, request, *args, **kwargs):
        response = super(ExecutionPurchasesComparitiveStatementAddView, self).get(request, args, kwargs)
        #print(response.__dict__)
        data_dict={}
        po_data_dict = {}
        approval_list = []
        vendor_list=[]
        requisitions_master_id = self.request.query_params.get('requisitions_master_id', None)
        item_id = self.request.query_params.get('item_id', None)
        uom = self.request.query_params.get('uom', None)
        if response.data:
            response.data = list(map(self.str_to_float, response.data))
            list_data = sorted(response.data, key = lambda i: i['net_landed_cost'])
            response.data = list(map(self.float_to_string, response.data))
            l = 0
            for data in list_data:
                l+=1
                ll = "L"+str(l)
                #print(data)
                # d_dict={
                #     "name": ll,
                #     "id": data['id'],
                #     "item": data["item"],
                #     "vendor": data["vendor"],
                #     "vendor_name": data["vendor_name"],
                #     "uom": data["uom"],
                #     "net_landed_cost": data["net_landed_cost"],
                #     "is_approved": data["is_approved"]
                # }
                # approval_list.append(d_dict)
                vendor_list.append(data['vendor'])
                index = [index for (index, d) in enumerate(response.data) if d['id']==data['id']][0]
                #print(ll, data['net_landed_cost'], type(data['net_landed_cost']))
                response.data[index]['ranking']=ll
            
        #level of approvals list 
        requisitions_master_id = self.request.query_params.get('requisitions_master_id', None)
        item_id = self.request.query_params.get('item_id', None)
        uom = self.request.query_params.get('uom', None)

        section_name = self.request.query_params.get('section_name', None)
        if section_name:
            permission_details=[]
            section_details=TCoreOther.objects.get(cot_name__iexact=section_name)
            approval_master_details = PmsApprovalPermissonMatser.objects.filter(section=section_details.id)
            #print("approval_master_details",approval_master_details)
            # type_details= PmsExecutionPurchasesRequisitionsMaster.objects.get(id=requisitions_master_id).type
            log_details=PmsExecutionPurchasesComparitiveStatementLog.objects.\
                    filter(requisitions_master=requisitions_master_id,uom=uom,item=item_id,vendor__in=vendor_list)
            # print(log_details) 
            amd_list=[]
            l_d_list=[]
            for l_d in log_details.values('id','is_approved','approval_permission_user_level','vendor__contact_person_name','vendor','is_rejected','comment','created_at'):
                l_d_list.append(l_d['approval_permission_user_level'])

            for a_m_d in approval_master_details:
                if l_d_list:
                    if a_m_d.id in l_d_list:
                        l_d=log_details.filter(approval_permission_user_level=a_m_d.id).order_by('-id')[0]
                        #f_name = a_m_d.approval_user.first_name if a_m_d.approval_user else '' 
                        #l_name = a_m_d.approval_user.last_name if a_m_d.approval_user else '' 
                        var=a_m_d.permission_level
                        res = re.sub("\D", "", var)
                        permission_dict={
                            "user_level":a_m_d.permission_level,
                            "approval":l_d.is_approved,
                            "rejected":l_d.is_rejected,
                            "permission_num":int(res),
                            "approved_vendor":l_d.vendor.contact_person_name,
                            "approved_vendor_id":l_d.vendor.id,
                            "comment": l_d.comment,
                            "approved_date":l_d.created_at,
                            "user_details":{
                                "id":l_d.updated_by.id if l_d.updated_by else None,
                                #"email":a_m_d.approval_user.email if a_m_d.approval_user else None,
                                "name": l_d.updated_by.get_full_name(),
                                #"username":a_m_d.approval_user.username
                                }
                        }
                            

                    else:
                        f_name = a_m_d.approval_user.first_name if a_m_d.approval_user else '' 
                        l_name = a_m_d.approval_user.last_name if a_m_d.approval_user else '' 
                        var=a_m_d.permission_level
                        res = re.sub("\D", "", var)
                        permission_dict={
                            "user_level":a_m_d.permission_level,
                            "permission_num":int(res),
                            "approval":None,
                            "rejected":False,
                            "approved_date":None,
                            "user_details":{
                                "id":a_m_d.approval_user.id if a_m_d.approval_user else None,
                                "email":a_m_d.approval_user.email if a_m_d.approval_user else None,
                                "name":  f_name +' '+l_name,
                                "username":a_m_d.approval_user.username
                                }
                        }

                    permission_details.append(permission_dict)
                else:
                    f_name = a_m_d.approval_user.first_name if a_m_d.approval_user else '' 
                    l_name = a_m_d.approval_user.last_name if a_m_d.approval_user else '' 
                    var=a_m_d.permission_level
                    res = re.sub("\D", "", var)
                    permission_dict={
                            "user_level":a_m_d.permission_level,
                            "permission_num":int(res),
                            "approval":None,
                            "approved_date":None,
                            "user_details":{
                                "id":a_m_d.approval_user.id if a_m_d.approval_user else None,
                                "email":a_m_d.approval_user.email if a_m_d.approval_user else None,
                                "name":  f_name +' '+l_name,
                                "username":a_m_d.approval_user.username
                                }
                        }
                    permission_details.append(permission_dict)
            # data['permission_details']=permission_details    

        po_data = PmsExecutionPurchasesPOItemsMAP.objects.filter(is_deleted=False,uom=uom,item=item_id).order_by('-purchase_order__id').first()
        po_data_dict= {
                'po_no': po_data.purchase_order.po_no if po_data else "",
                'po_amount': po_data.purchase_order.po_amount if po_data else "",
                'po_date': po_data.purchase_order.created_at if po_data else ""
            }
       

        # reqList.append(req_dict)
        # data['requisition_master']['requisition_details'] = reqList
        # updated by shubhadeep for comparitive_statement_remarks
        requistion_entry = PmsExecutionPurchasesRequisitions.objects.get(requisitions_master_id=requisitions_master_id,
            item=item_id,uom=uom)
        data_dict['comparitive_statement_remarks'] = requistion_entry.comparitive_statement_remarks

        data_dict['last_po'] = po_data_dict
        data_dict['result'] = response.data
        # data_dict['approval_dict']=approval_list
        data_dict['permission_details']=permission_details
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


# added by shubhadeep
class ExecutionPurchasesComparitiveStatementDownloadView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesComparitiveStatement.objects.filter(is_deleted=False)
    serializer_class = ExecutionPurchasesComparitiveStatementAddSerializer

    def get_queryset(self):
        requisitions_master_id = self.kwargs.get('requisitions_master_id')
        if requisitions_master_id:
            queryset =  self.queryset.filter(requisitions_master=requisitions_master_id)
            return queryset

    def str_to_float(self, obj):
        obj['net_landed_cost'] = float(obj['net_landed_cost'])
        return obj

    def float_to_string(self, obj):
        obj['net_landed_cost'] = "{0:.2f}".format(obj['net_landed_cost'])
        return obj

    def get(self, request, *args, **kwargs):
        response = super(ExecutionPurchasesComparitiveStatementDownloadView,self).get(request,args,kwargs)
        response_data = []
        vendors = []
        for r in response.data:
            count = len([v for v in vendors if v['vendor_code'] == r['vendor_code']])
            if count == 0:
                vendor_data = {'vendor_code': r['vendor_code'], 
                    'vendor_name': r['vendor_name'], 
                    'vendor_id': r['vendor']}
                vendor_data['total_items'] = 0
                vendor_data['final_price'] = 0
                vendor_data['price_basis'] = 0
                vendor_data['total_order_value'] = 0
                vendor_data['net_landed_cost']  = 0
                vendor_data['freight_up_to_site'] = 0
                vendor_data['packaging_and_forwarding'] = {}
                vendor_data['packaging_and_forwarding_amt'] = 0
                vendor_data['cgst'] = {}
                vendor_data['cgst_amt'] = 0
                vendor_data['sgst'] = {}
                vendor_data['sgst_amt'] = 0
                vendor_data['igst'] = {}
                vendor_data['igst_amt'] = 0
                vendor_data['payment_terms'] = {}
                vendor_data['delivery_time']  = {}
                vendor_data['inco_terms']  = {}
                vendor_data['warranty_guarantee']  = {}
                vendor_data['make']  = {}
                vendors.append(vendor_data)
            
        requisitions_master_id = self.kwargs.get('requisitions_master_id')
        requisitions_master = PmsExecutionPurchasesRequisitionsMaster.objects.get(pk=requisitions_master_id) 
        requistion_entries = PmsExecutionPurchasesRequisitions.objects.filter(requisitions_master_id=requisitions_master_id)
        for requistion_entry in requistion_entries:
            data_dict = {}
            item_id = requistion_entry.item
            uom = requistion_entry.uom
            materials_details = Materials.objects.get(id=item_id)
            filtered_statements = [d for d in response.data if d['item_details'] and d['item_details']['id'] == item_id and d['item_details']['uom_id'] == uom.id]
            data_dict = {
                "id": item_id,
                "name": materials_details.__dict__['name'],
                "uom": uom.c_name,
                "uom_id": uom.id,
                "qty": requistion_entry.quantity,
                "mat_code": materials_details.__dict__['mat_code'],
                "description": materials_details.__dict__['description']
            }
            data_dict['vendors'] = []
            for v in vendors:
                v_data = {}
                v_data['vendor_id'] = v['vendor_id']
                v_data['vendor_name'] = v['vendor_name']
                v_data['vendor_code'] = v['vendor_code']
                price, discount, final, total, quantity = 0, 0, 0, 0, 0
                try:
                    quotation = PmsExecutionPurchasesQuotations.objects.get(requisitions_master_id=requisitions_master_id, 
                        item=item_id, unit=uom, vendor_id=v['vendor_id'])
                    stmt = [s for s in filtered_statements if s['vendor'] == v['vendor_id']][0]
                    price = decimal.Decimal(quotation.price)
                    discount = decimal.Decimal(stmt['discount'])
                    final = price - decimal.Decimal(discount * price / 100)
                    quantity = decimal.Decimal(quotation.quantity)
                    total = final * quantity
                    prices_basis = decimal.Decimal(stmt['final_price'])
                    packaging_percent = decimal.Decimal(stmt['packaging_and_forwarding'])
                    packaging_cost = prices_basis * packaging_percent / 100
                    cgst = decimal.Decimal(stmt['cgst'])
                    sgst = decimal.Decimal(stmt['sgst'])
                    igst = decimal.Decimal(stmt['igst'])
                    payment_term = PmsExecutionPurchasesQuotationsPaymentTermsMaster.objects.get(pk=stmt['payment_terms']).name

                    v['total_items'] += 1
                    v['final_price'] += prices_basis
                    v['price_basis'] += prices_basis
                    v['total_order_value'] += decimal.Decimal(stmt['total_order_value'])
                    v['net_landed_cost'] += decimal.Decimal(stmt['net_landed_cost'])
                    v['freight_up_to_site'] += decimal.Decimal(stmt['freight_up_to_site'])
                    
                    v['packaging_and_forwarding'][materials_details.__dict__['mat_code']] = str(packaging_percent)
                    v['cgst'][materials_details.__dict__['mat_code']] = str(cgst)
                    v['sgst'][materials_details.__dict__['mat_code']] = str(sgst)
                    v['igst'][materials_details.__dict__['mat_code']] = str(igst)
                    v['payment_terms'][materials_details.__dict__['mat_code']] = payment_term
                    v['delivery_time'][materials_details.__dict__['mat_code']] = str(stmt['delivery_time'])
                    v['inco_terms'][materials_details.__dict__['mat_code']]  = str(stmt['inco_terms']) if stmt['inco_terms'] else '-'
                    v['warranty_guarantee'][materials_details.__dict__['mat_code']]  = str(stmt['warranty_guarantee']) if stmt['warranty_guarantee']  else '-'
                    v['make'][materials_details.__dict__['mat_code']]  = str(stmt['make']) if stmt['make']  else '-'

                    v['packaging_and_forwarding_amt'] += packaging_cost
                    v['cgst_amt'] += (prices_basis + packaging_cost) * cgst / 100
                    v['sgst_amt'] += (prices_basis + packaging_cost) * sgst / 100
                    v['igst_amt'] += (prices_basis + packaging_cost) * igst / 100

                except Exception as e:
                    print (e)
                    v['packaging_and_forwarding'][materials_details.__dict__['mat_code']] = '-'
                    v['cgst'][materials_details.__dict__['mat_code']] = '-'
                    v['sgst'][materials_details.__dict__['mat_code']] = '-'
                    v['igst'][materials_details.__dict__['mat_code']] = '-'
                    v['payment_terms'][materials_details.__dict__['mat_code']] = '-'
                    v['delivery_time'][materials_details.__dict__['mat_code']] = '-'
                    v['inco_terms'][materials_details.__dict__['mat_code']]  = '-'
                    v['warranty_guarantee'][materials_details.__dict__['mat_code']]  = '-'
                    v['make'][materials_details.__dict__['mat_code']]  = '-'
                v_data['price'] = price
                v_data['discount'] = discount
                v_data['final'] = final
                v_data['total'] = total
                v_data['qty'] = quantity
                
                data_dict['vendors'].append(v_data)
            
            po_data = PmsExecutionPurchasesPOItemsMAP.objects.filter(is_deleted=False,uom=uom,item=item_id).order_by('-purchase_order__id').first()
            data_dict['po_no'] = po_data.purchase_order.po_no if po_data else "-"
            data_dict['po_amount'] = po_data.purchase_order.po_amount if po_data else "-"
            data_dict['po_date'] = po_data.purchase_order.created_at if po_data else "-"
                
            data_dict['comparitive_statement_remarks'] = requistion_entry.comparitive_statement_remarks

            response_data.append(data_dict)

        def unanimous(seq):
            it = iter(seq)
            try:
                first = next(it)
            except StopIteration:
                return True
            else:
                return all(i == first for i in it)

        v_keys = ['packaging_and_forwarding', 'cgst', 'sgst', 'igst', 'payment_terms', 'delivery_time' ,
            'warranty_guarantee', 'inco_terms', 'make']
        for v in vendors:
            for idx, v_key in enumerate(v_keys):
                val = ''
                unit = ''
                if idx <= 3:
                    unit = '%'
                elif idx == 5:
                    unit = ' Days'
                else:
                    unit = ''
                if unanimous(v[v_key].values()):
                    val = '{0}{1}'.format(list(v[v_key].values())[0], unit)
                else:
                    for key in v[v_key].keys():
                        val += '{0}{2}({1})\n'.format(v[v_key][key], key, unit)
                    val = val[:-1]
                v[v_key] = val

        list_data = sorted(vendors, key = lambda i: i['net_landed_cost'])
        l = 0
        for data in list_data:
            l += 1
            ll = "L"+str(l)
            index = [index for (index, d) in enumerate(vendors) if d['vendor_id']==data['vendor_id']][0]
            vendors[index]['ranking']=ll

        if not os.path.isdir('media/pms/requisition_report/document'):
            os.makedirs('media/pms/requisition_report/document')
        file_name = 'media/pms/requisition_report/document/comp_stmt_{0}.xlsx'.format(requisitions_master_id)
        file_path = settings.MEDIA_ROOT_EXPORT + file_name

        import xlsxwriter
        workbook = xlsxwriter.Workbook(file_path)
        worksheet = workbook.add_worksheet()
        merged_header_format = workbook.add_format({'bold': True, 'font_size': 11, 'align': 'center', 'valign': 'vcenter'})
        info_format = workbook.add_format({'bold': True, 'font_size': 10, 'align': 'left', 'valign': 'vcenter'})
        header_format = workbook.add_format({'bold': True, 'font_size': 9, 'align': 'center', 'valign': 'vcenter'})
        vendor_header_format = workbook.add_format({'bold': True, 'font_size': 9, 'align': 'right', 'valign': 'vcenter'})
        cell_format = workbook.add_format({'font_size': 9, 'font_color': '#1e1e1e', 'align': 'center', 'valign': 'vcenter'})
        cell_imp_format = workbook.add_format({'font_size': 9, 'font_color': '#1e1e1e', 'align': 'center', 'valign': 'vcenter'})
        cell_wrap_format = workbook.add_format({'font_size': 9, 'font_color': '#1e1e1e', 'align': 'center','text_wrap': True, 'valign': 'vcenter'})

        cell_width, cell_height = {}, {}
        def worksheet_write(row_idx, col_idx, val, cell_format):
            worksheet.write(row_idx, col_idx, val, cell_format)
            width = 8
            if len(str(val)) > 8:
                width = len(str(val)) * 0.9
            if col_idx in cell_width and cell_width[col_idx] > width:
                width = cell_width[col_idx]
            cell_width[col_idx] = width
            worksheet.set_column(col_idx, col_idx, width=cell_width[col_idx])

        def worksheet_merge_range(row_idx1, col_idx1, row_idx2, col_idx2, val, format):
            worksheet.merge_range(row_idx1, col_idx1, row_idx2, col_idx2, val, format)
            height = 15
            for c in str(val):
                if c == '\n':
                    height += 16
            if row_idx1 in cell_height and cell_height[row_idx1] > height:
                height = cell_height[row_idx1]
            cell_height[row_idx1] = height
            worksheet.set_row(row_idx1, height=cell_height[row_idx1])

        col_idx = 0
        worksheet_merge_range(4, col_idx, 4, col_idx + 4, 'Item Details', merged_header_format)
        col_idx += 5
        for v in vendors:
            worksheet_merge_range(4, col_idx, 4, col_idx + 4, 
                '{0} ({1})'.format(v['vendor_name'], v['vendor_code']), merged_header_format)
            col_idx += 5
        worksheet_merge_range(4, col_idx, 4, col_idx + 2, 
            'Last PO Details', merged_header_format)
        col_idx += 2
        worksheet_merge_range(0, 0, 0, col_idx, 'Comparitive Statement', merged_header_format)
        worksheet_merge_range(1, 0, 1, col_idx, 
            'Site:{0}'.format(requisitions_master.site_location.name), info_format)
        worksheet_merge_range(2, 0, 2, col_idx, 
            'Site Address:{0}'.format(requisitions_master.site_location.address), info_format)
        worksheet_merge_range(3, 0, 3, col_idx, 
            'M.R. Date:{0}'.format(requisitions_master.mr_date.strftime("%Y-%m-%d")), info_format)

        headings = ['Sl No', 'Material Code', 'Desc.', 'Qty', 'UOM']
        for v in vendors:
            headings.extend(['Quoted Price', 'Discount %', 'Final Price', 'Qty', 'Total Value'])
        headings.extend(['PO Amount', 'PO No.', 'PO Date'])
        
        rows = [headings]
        item_count = 1
        for r in response_data:
            row = []
            row.extend([item_count, r['mat_code'], r['description'], r['qty'], r['uom']])
            for v_data in r['vendors']:
                row.extend([round(v_data['price'], 2), round(v_data['discount'], 2), round(v_data['final'], 2), 
                    v_data['qty'], round(v_data['total'], 2)])
            row.extend([r['po_amount'], r['po_no'], r['po_date']])
            rows.append(row)
            item_count += 1
        
        row_idx, col_idx = 5, 0
        for row in rows:
            if row_idx == 5:
                format = header_format
            else:
                format = cell_format
            for item in row:
                worksheet_write(row_idx, col_idx, item, format)
                col_idx += 1
            row_idx += 1
            col_idx = 0
        
        col_idx = 0
        i = 0
        for i in range(15):
            if i == 0:
                worksheet_merge_range(row_idx, col_idx, row_idx, col_idx + 4, 
                    'Price Basis(INR/Euro/GBOP)', vendor_header_format)
                for v in vendors:
                    col_idx = col_idx + 5
                    worksheet_write(row_idx, col_idx + 4, round(v['price_basis'], 2), cell_format)
            elif i == 1:
                worksheet_merge_range(row_idx, col_idx, row_idx, col_idx + 4, 
                    'Make', vendor_header_format)
                for v in vendors:
                    col_idx = col_idx + 5
                    worksheet_merge_range(row_idx, col_idx, row_idx, col_idx + 4, v['make'], cell_wrap_format)
            elif i == 2:
                worksheet_merge_range(row_idx, col_idx, row_idx, col_idx + 4, 
                    'Base Price(INR)', vendor_header_format)
                for v in vendors:
                    col_idx = col_idx + 5
                    worksheet_write(row_idx, col_idx + 4, round(v['price_basis'], 2), cell_format)
            elif i == 3:
                worksheet_merge_range(row_idx, col_idx, row_idx, col_idx + 4, 
                    'Packaging and Forwarding', vendor_header_format)
                col_idx = col_idx + 5
                for v in vendors:
                    worksheet_write(row_idx, col_idx, 'Extra', cell_format)
                    col_idx = col_idx + 1
                    worksheet_merge_range(row_idx, col_idx, row_idx, col_idx + 2, v['packaging_and_forwarding'], cell_format)
                    col_idx = col_idx + 3
                    worksheet_write(row_idx, col_idx, round(v['packaging_and_forwarding_amt'], 2), cell_format)
                    col_idx = col_idx + 1
            elif i == 4:
                worksheet_merge_range(row_idx, col_idx, row_idx, col_idx + 4, 
                    'Freight up to Site', vendor_header_format)
                col_idx = col_idx + 5
                for v in vendors:
                    worksheet_write(row_idx, col_idx, 'Extra', cell_format)
                    col_idx = col_idx + 1
                    worksheet_merge_range(row_idx, col_idx, row_idx, col_idx + 3, round(v['freight_up_to_site'], 2), cell_wrap_format)
                    col_idx = col_idx + 4
            elif i == 5:
                worksheet_merge_range(row_idx, col_idx, row_idx, col_idx + 4, 
                    'CGST', vendor_header_format)
                col_idx = col_idx + 5
                for v in vendors:
                    worksheet_write(row_idx, col_idx, 'Extra', cell_format)
                    col_idx = col_idx + 1
                    worksheet_merge_range(row_idx, col_idx, row_idx, col_idx + 2, v['cgst'], cell_wrap_format)
                    col_idx = col_idx + 3
                    worksheet_write(row_idx, col_idx, round(v['cgst_amt'], 2), cell_format)
                    col_idx = col_idx + 1
            elif i == 6:
                worksheet_merge_range(row_idx, col_idx, row_idx, col_idx + 4, 
                    'SGST', vendor_header_format)
                col_idx = col_idx + 5
                for v in vendors:
                    worksheet_write(row_idx, col_idx, 'Extra', cell_format)
                    col_idx = col_idx + 1
                    worksheet_merge_range(row_idx, col_idx, row_idx, col_idx + 2, v['sgst'], cell_wrap_format)
                    col_idx = col_idx + 3
                    worksheet_write(row_idx, col_idx, round( v['sgst_amt'], 2), cell_format)
                    col_idx = col_idx + 1
            elif i == 7:
                worksheet_merge_range(row_idx, col_idx, row_idx, col_idx + 4, 
                    'IGST', vendor_header_format)
                col_idx = col_idx + 5
                for v in vendors:
                    worksheet_write(row_idx, col_idx, 'Extra', cell_format)
                    col_idx = col_idx + 1
                    worksheet_merge_range(row_idx, col_idx, row_idx, col_idx + 2, v['igst'], cell_wrap_format)
                    col_idx = col_idx + 3
                    worksheet_write(row_idx, col_idx, round(v['igst_amt'], 2), cell_format)
                    col_idx = col_idx + 1
            elif i == 8:
                worksheet_merge_range(row_idx, col_idx, row_idx, col_idx + 4, 
                    'Payment Terms', vendor_header_format)
                for v in vendors:
                    col_idx = col_idx + 5
                    worksheet_merge_range(row_idx, col_idx, row_idx, col_idx + 4, v['payment_terms'], cell_wrap_format)
            elif i == 9:
                worksheet_merge_range(row_idx, col_idx, row_idx, col_idx + 4, 
                    'Delivery Time', vendor_header_format)
                for v in vendors:
                    col_idx = col_idx + 5
                    worksheet_merge_range(row_idx, col_idx, row_idx, col_idx + 4, v['delivery_time'], cell_wrap_format)
            elif i == 10:
                worksheet_merge_range(row_idx, col_idx, row_idx, col_idx + 4, 
                    'Total Order Value(INR)', vendor_header_format)
                for v in vendors:
                    col_idx = col_idx + 5
                    worksheet_write(row_idx, col_idx + 4, round(v['total_order_value'], 2), cell_format)
            elif i == 11:
                worksheet_merge_range(row_idx, col_idx, row_idx, col_idx + 4, 
                    'Net Landed Cost(INR)', vendor_header_format)
                for v in vendors:
                    col_idx = col_idx + 5
                    worksheet_write(row_idx, col_idx + 4, round(v['net_landed_cost'], 2), cell_format)
            elif i == 12:
                worksheet_merge_range(row_idx, col_idx, row_idx, col_idx + 4, 
                    'Inco Terms', vendor_header_format)
                for v in vendors:
                    col_idx = col_idx + 5
                    worksheet_merge_range(row_idx, col_idx, row_idx, col_idx + 4, v['inco_terms'], cell_wrap_format)
            elif i == 13:
                worksheet_merge_range(row_idx, col_idx, row_idx, col_idx + 4, 
                    'Warranty Gurantee', vendor_header_format)
                for v in vendors:
                    col_idx = col_idx + 5
                    worksheet_merge_range(row_idx, col_idx, row_idx, col_idx + 4, v['warranty_guarantee'], cell_wrap_format)
            elif i == 14:
                worksheet_merge_range(row_idx, col_idx, row_idx, col_idx + 4, 
                    'Comm. Ranking', vendor_header_format)
                for v in vendors:
                    col_idx = col_idx + 5
                    worksheet_merge_range(row_idx, col_idx, row_idx, col_idx + 4, v['ranking'], vendor_header_format)

            col_idx = 0
            row_idx += 1
            i += 1
        
        workbook.close()

        if response_data:
            if request.is_secure():
                protocol = 'https://'
            else:
                protocol = 'http://'

            url = getHostWithPort(request) + file_name if file_name else None

            if url:                    
                return Response({'request_status':1,'msg':'Found', 'url': url})
            else:
                return Response({'request_status':0,'msg':'Not Found', 'url': url})
        else:
            return Response({'request_status':0, 'msg':'No Data', 'url': url})

class ExecutionPurchasesComparitiveStatementEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesComparitiveStatement.objects.filter(is_deleted=False)
    serializer_class = ExecutionPurchasesComparitiveStatementEditSerializer

class ExecutionPurchasesComparitiveStatementOrdListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesComparitiveStatement.objects.filter(is_deleted=False)
    serializer_class = ExecutionPurchasesComparitiveStatementOrdListViewSerializer

    def get_queryset(self,*args,**kwargs):
        requisitions_master_id=self.kwargs['requisitions_master_id']
        item_id=self.kwargs['item_id']
        # print('requisitions_master_id',requisitions_master_id)
        return self.queryset.filter(requisitions_master=requisitions_master_id,item=item_id)

    def get(self, request, *args, **kwargs):
        requisitions_master_id = self.kwargs['requisitions_master_id']
        item_id = self.kwargs['item_id']
        response=super(ExecutionPurchasesComparitiveStatementOrdListView,self).get(request,args,kwargs)
        #print("responce",response.data)
        min_net_landed_cost = 10000000000000  #minimum value check(static)>max value as your choice
        mn = [x['net_landed_cost'] for x in response.data]
        #print("mn",mn)
        for data in response.data:
            if min_net_landed_cost > float(data['net_landed_cost']):
                    min_net_landed_cost = float(data['net_landed_cost'])
                    comp_stat_id = data['id']

        if comp_stat_id:
            min_cost_approval = PmsExecutionPurchasesComparitiveStatement.objects.filter(id=comp_stat_id, item=item_id, requisitions_master=requisitions_master_id).update(is_approved=True)
            # print("min_cost_approval",min_cost_approval)

        return response

class ExecutionPurchasesComparitiveStatementApprovalView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesComparitiveStatement.objects.filter(is_deleted=False)
    serializer_class = ExecutionPurchasesComparitiveStatementApprovalSerializer

# added by Shubhadeep for CR1
class ExecutionPurchasesComparitiveStatementApprovalViewBatch(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesComparitiveStatement.objects.filter(is_deleted=False)
    serializer_class = ExecutionPurchasesComparitiveStatementApprovalSerializerBatch
# --

class ExecutionPurchasesComparitiveStatementDocumentAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesComparitiveStatementDocument.objects.filter(is_deleted=False)
    serializer_class =  ExecutionPurchasesComparitiveStatementDocumentAddSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('comparitive_statement',)
    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        return response

class ExecutionPurchasesComparitiveStatementApprovalListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesComparitiveStatement.objects.filter(is_deleted=False,is_approved=True)
    serializer_class = ExecutionPurchasesComparitiveStatementApprovalListSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('requisitions_master',)

    def get(self, request, *args, **kwargs):
        data_dict = {}
        app_list = []
        response = super(ExecutionPurchasesComparitiveStatementApprovalListView, self).get(request, args, kwargs)
        data_dict['result'] = []
        if response.data:
            for i in response.data:
                app_list.append(i['id'])
            data_dict['result'] = app_list
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

class ExecutionPurchasesPOListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset =  PmsExecutionPurchasesComparitiveStatement.objects.filter(is_deleted=False,is_approved=True)
    serializer_class = ExecutionPurchasesPOListSerializer

    # @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        req_id = self.kwargs['req_id']
        # print(req_id)

        data = {}
        approveList = []
        data_dict = {}
        itemDict= {}
        vedorDict={}
        vendorList=[]

        # permission_num = PmsApprovalPermissonLavelMatser.objects.get(section=TCoreOther.objects.get(cot_name=section_name)).permission_level
        # permission_level_data=PmsApprovalPermissonMatser.objects.get(id=str(validated_data.get('approval_permission_user_level'))).permission_level
        # permission_level=re.sub("\D", "",permission_level_data)
        comparitive_data=PmsExecutionPurchasesComparitiveStatement.objects.filter(requisitions_master=req_id,is_approved=True).values('vendor')
        comparitive_details=PmsExecutionPurchasesComparitiveStatement.objects.filter(requisitions_master=req_id,is_approved=True)
        vendor_id=list(set([x['vendor'] for x in comparitive_data]))
        #print("vendor_id",vendor_id)
        #print("comparitive_details",comparitive_details)
        # for comparitive_ids in comparitive_details:
        for vendor_d in vendor_id:

            # print('comparitive_ids',comparitive_ids)
            item_list = list()
            vedorDict = {
                'vendor_id': vendor_d,
                'vendor_name': PmsExternalUsers.objects.get(id=vendor_d).contact_person_name,
                'vendor_code': PmsExternalUsers.objects.get(id=vendor_d).code
            }

            item_details = PmsExecutionPurchasesComparitiveStatement.objects.filter(
                requisitions_master=req_id,vendor_id=vendor_d,is_approved=True)

            #print("item_details-->",item_details)
            for i_data in item_details:
                type = PmsExecutionPurchasesRequisitionsMaster.objects.only('type').get(id=req_id).type
                type_name = PmsExecutionPurchasesRequisitionsTypeMaster.objects.only('type_name').get(
                    id=str(type)).type_name
                # print("i_data.", i_data.uom.c_name)

                # if type_name.lower() == "materials":
                quotationQuantity = PmsExecutionPurchasesQuotations.objects.only('quantity').get(requisitions_master=req_id,
                                                                                        item = i_data.item,
                                                                                        unit = i_data.uom.id,
                                                                                        vendor_id = i_data.vendor.id,
                                                                                        is_deleted=False).quantity

                getApprovalDetails = PmsExecutionPurchasesRequisitionsApproval.objects.get(requisitions_master=req_id,
                                                                                            uom = i_data.uom.id,
                                                                                            arm_approval__gt=False,
                                                                                            item=i_data.item,is_deleted=False)
                material_details = Materials.objects.filter(id=i_data.item)
                for matdetaisl in material_details:
                    # print(matdetaisl.id,matdetaisl.name,matdetaisl.description)
                    itemDict = {
                        # 'id': matdetaisl.id,
                        'name': matdetaisl.name,
                        'mat_code': matdetaisl.mat_code,
                        'item': i_data.item,
                        'price': i_data.final_price,
                        'payment_terms_name': i_data.payment_terms.name,
                        'quantity' : getApprovalDetails.__dict__['approved_quantity'],
                        'available_quantity': getApprovalDetails.__dict__['available_quantity'],
                        'unit' : i_data.uom.c_name,
                        'unit_id': i_data.uom.id,
                        'quot_quantity' : quotationQuantity

                    }
                # print(material_details)
                if type_name.lower() == 'machinery':
                    quotationQuantity = PmsExecutionPurchasesQuotations.objects.only('quantity').get(requisitions_master=req_id,
                                                                                        item = i_data.item,
                                                                                        vendor_id = i_data.vendor.id,
                                                                                        is_deleted=False).quantity
                    getApprovalDetails = PmsExecutionPurchasesRequisitionsApproval.objects.get(requisitions_master=req_id,
                                                                                              arm_approval__gt=False,
                                                                                              item=i_data.item,is_deleted=False)
                    machinery_details = PmsMachineries.objects.filter(id=i_data.item)
                    for mach in machinery_details:
                        itemDict = {
                            # 'id': mach.id,
                            'code': mach.code,
                            'equipment_name': mach.equipment_name,
                            'item': i_data.item,
                            'price': i_data.final_price,
                            'payment_terms_name':  i_data.payment_terms.name,
                            'quantity' : getApprovalDetails.__dict__['approved_quantity'],
                            'available_quantity': getApprovalDetails.__dict__['available_quantity'],
                            'unit': "",
                            'unit_id': "",
                            'quot_quantity' : quotationQuantity
                        }
                item_list.append(itemDict)
                #print("item_details",i_data.item)
            vedorDict['item_details'] = item_list
            vendorList.append(vedorDict)
        data = vendorList
        # approveList.append(data)

        data_dict['result'] = data
        if data:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_SUCCESS
        elif len(data) == 0:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_NO_DATA
        else:
            data_dict['request_status'] = 0
            data_dict['msg'] = settings.MSG_ERROR
        data = data_dict


        return Response(data)


class ExecutionPurchasesPOAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesPO.objects.filter(is_deleted=False)
    serializer_class = ExecutionPurchasesPOAddSerializer

    @response_modify_decorator_list
    def list(self, request, *args, **kwargs):
        # print(response)
        return response

class ExecutionPurchasesPOTotalListView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesPO.objects.filter(is_deleted=False)
    serializer_class = ExecutionPurchasesPOTotalListSerializer

    def get(self, request, *args, **kwargs):
        req_id = self.kwargs['req_id']

        data = {}
        # poList = []
        data_dict = {}
        # poitemsDict = {}
        vendorList = []
        podocDict = {}

        poDetails = PmsExecutionPurchasesPO.objects.filter(requisitions_master=req_id)

        for poData in poDetails:
            vendorDict = {
                'vendor' : poData.vendor.id,
                'vendor_name': poData.vendor.contact_person_name,
                'vendor_code': poData.vendor.code,
                'date_of_po' : poData.date_of_po,
                'po_no' : poData.po_no,
                'po_amount' : poData.po_amount,
                'transport_cost_type' : poData.transport_cost_type.id ,
                'transport_cost_type_code' : poData.transport_cost_type.code,
                'transport_cost' : poData.transport_cost
            }

            documentsDetails = PmsExecutionPurchasesPODocument.objects.filter(purchase_order=poData,is_deleted=False)
            #print("documentsDetails-->", documentsDetails)
            podocList = []
            for docDetails in documentsDetails:
                file_url = request.build_absolute_uri(docDetails.document.url)
                podocDict = {
                    'document_name' : docDetails.document_name,
                    'document' : file_url
                }
                podocList.append(podocDict)

            poitemsList = []

            poItemsMAP = PmsExecutionPurchasesPOItemsMAP.objects.filter(purchase_order=poData.id,is_deleted=False)

            for poItemDetails in poItemsMAP:
                type = PmsExecutionPurchasesRequisitionsMaster.objects.only('type').get(id=req_id).type
                type_name = PmsExecutionPurchasesRequisitionsTypeMaster.objects.only('type_name').get(
                    id=str(type)).type_name

                #print("type_name", type_name)

                # if type_name.lower() == "materials":
                material_details = Materials.objects.filter(id=poItemDetails.item)
                for matdetaisl in material_details:
                    # print(matdetaisl.ipurchases_purchases_order_total_listd, matdetaisl.name, matdetaisl.description)
                    poitemsDict = {
                        'id': matdetaisl.id,
                        'name': matdetaisl.name,
                        'mat_code': matdetaisl.mat_code,
                        'description': matdetaisl.description,

                        'quantity': poItemDetails.quantity,
                        'uom': poItemDetails.uom.id if poItemDetails.uom else '',
                        'uom_name': poItemDetails.uom.c_name if poItemDetails.uom else ''
                    }
                # print(material_details)
                if type_name.lower() == 'machinery':
                    machinery_details = PmsMachineries.objects.filter(id=poItemDetails.item)
                    for mach in machinery_details:
                        poitemsDict = {
                            'id': mach.id,
                            'code': mach.code,
                            'equipment_name': mach.equipment_name,

                            'quantity': poItemDetails.quantity,
                            'uom': poItemDetails.uom.id if poItemDetails.uom else '',
                            'uom_name': poItemDetails.uom.c_name if poItemDetails.uom else ''
                        }

                poitemsList.append(poitemsDict)
            vendorDict['po_docs'] = podocList
            vendorDict['items'] = poitemsList
            vendorList.append(vendorDict)
        data = vendorList

        data_dict['result'] = data
        # print(data_dict)
        if data:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_SUCCESS
            data_dict['status'] = PmsExecutionPurchasesRequisitionsMaster.objects.only('completed_status').get(id=req_id).completed_status
        elif len(data) == 0:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_NO_DATA
        else:
            data_dict['request_status'] = 0
            data_dict['msg'] = settings.MSG_ERROR
        data = data_dict
        #
        return Response(data)

class ExecutionPOTransportCostMasterAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesPOTransportCostMaster.objects.filter(is_deleted=False)
    serializer_class = ExecutionPOTransportCostMasterAddSerializer

    @response_modify_decorator_list
    def list(self, request, *args, **kwargs):
        # print(response)
        return response
#
class ExecutionPOTransportCostMasterEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesPOTransportCostMaster.objects.filter(is_deleted=False)
    serializer_class = ExecutionPOTransportCostMasterEditSerializer

class ExecutionPOTransportCostMasterDeleteView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesPOTransportCostMaster.objects.filter(is_deleted=False)
    serializer_class = ExecutionPOTransportCostMasterDeleteSerializer


class ExecutionPurchasesPODocumentAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesPODocument.objects.filter(is_deleted=False)
    serializer_class = ExecutionPurchasesPODocumentAddSerializer

    @response_modify_decorator_list
    def list(self, request, *args, **kwargs):
        # print(response)
        return response

class ExecutionPurchasesPODocumentEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesPODocument.objects.filter(is_deleted=False)
    serializer_class = ExecutionPurchasesPODocumentEditSerializer

class ExecutionPurchasesPODocumentDeleteView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesPODocument.objects.filter(is_deleted=False)
    serializer_class = ExecutionPurchasesPODocumentDeleteSerializer


class PurchaseRequisitionsApproval(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesRequisitionsApproval.objects.filter(is_deleted=False)
    serializer_class = PurchaseRequisitionsApprovalSerializer

# added by Shubhadeep for CR1
class PurchaseRequisitionsApprovalBatch(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesRequisitionsApproval.objects.filter(is_deleted=False)
    serializer_class = PurchaseRequisitionsApprovalSerializerBatch
# --

class PurchaseRequisitionsApprovalList(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesRequisitionsApproval.objects.filter(is_deleted=False)
    serializer_class = PurchaseRequisitionsApprovalListSerializer
    def get_queryset(self):
        project_id = self.kwargs["project_id"]
        site_id=self.kwargs["site_id"]
        requisition_id=self.kwargs["requisition_id"]
        return self.queryset.filter(
            requisitions_master=requisition_id,site_location=site_id,project=project_id)
    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        # print(response)
        return response

class PurchaseRequisitionsTotalApprovalList(generics.ListAPIView,PageNumberPagination):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesRequisitions.objects.filter(requisitions_master__status=1,is_deleted=False)
    serializer_class = PurchaseRequisitionsApprovalTotalListSerializer
    pagination_class = CSPageNumberPagination

    def get_queryset(self):
        # queryset=self.queryset.filter(status=1)
        filter = {}
        project = self.request.query_params.get('project', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        site_location = self.request.query_params.get('site_location', None)
        type_name = self.request.query_params.get('type_name', None)
        search = self.request.query_params.get('search', None)
        item_type = self.request.query_params.get('item_type', None)
        item = self.request.query_params.get('item', None)

        if search :
            #print("This is if condition entry")
            queryset = self.queryset.filter(requisitions_master__status=1,requisitions_master__project__project_g_id=search)

            #print('queryset_search::::::::::::::::::::', queryset)
            return queryset


        if start_date and end_date:
            start_object = datetime.strptime(start_date, '%Y-%m-%d').date()
            filter['requisitions_master__mr_date__gte'] = start_object
            end_object = datetime.strptime(end_date, '%Y-%m-%d').date()
            filter['requisitions_master__mr_date__lte'] = end_object + timedelta(days=1)

            queryset = self.queryset.filter(requisitions_master__status=1,**filter)

            return queryset

        if site_location:
            filter['requisitions_master__site_location__in']=list(map(int,site_location.split(",")))

        if project:
            filter['requisitions_master__project__in']=list(map(int,project.split(",")))


        if type_name:
            #print("halla ")
            if type_name.lower() == 'materials':
                filter['requisitions_master__type'] = 1
            elif type_name.lower() == 'machinery':
                print("hala ")
                filter['requisitions_master__type'] = 2

        if item:
            filter['item__in']= list(map(int,item.split(",")))
            #print("item:::::::::::::::::::",filter)
            

        if filter:
            queryset = self.queryset.filter(requisitions_master__status=1,**filter)

            #print('queryset',queryset)
            return queryset
        else:
            queryset=self.queryset.filter(requisitions_master__status=1)
            return queryset

    @response_modify_decorator_list_or_get_after_execution_for_pagination
    def get(self,request,*args,**kwargs): 
        
        response = super(PurchaseRequisitionsTotalApprovalList, self).get(request, args, kwargs)
        master_id_list=list(set([x['requisitions_master'] for x in response.data['results']]))
        item_val = self.request.query_params.get('item', None)
        item_list=[]

        #################:Filtering:#############################################
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        if field_name and order_by:

            if field_name == 'project' and order_by == 'asc':
                master_queryset = PmsExecutionPurchasesRequisitionsMaster.objects.filter(id__in=master_id_list,is_deleted=False).order_by('project')

            elif field_name == 'project' and order_by == 'desc':
                master_queryset = PmsExecutionPurchasesRequisitionsMaster.objects.filter(id__in=master_id_list,is_deleted=False).order_by('-project')

            elif field_name == 'site_location' and order_by == 'asc':
                master_queryset = PmsExecutionPurchasesRequisitionsMaster.objects.filter(id__in=master_id_list,is_deleted=False).order_by('site_location')
            elif field_name == 'site_location' and order_by == 'desc':
                master_queryset = PmsExecutionPurchasesRequisitionsMaster.objects.filter(id__in=master_id_list,is_deleted=False).order_by('-site_location')

            elif field_name == 'mr_date' and order_by == 'asc':
                master_queryset = PmsExecutionPurchasesRequisitionsMaster.objects.filter(id__in=master_id_list,is_deleted=False).order_by('mr_date')

            elif field_name == 'mr_date' and order_by == 'desc':
                master_queryset = PmsExecutionPurchasesRequisitionsMaster.objects.filter(id__in=master_id_list,is_deleted=False).order_by('-mr_date')

            elif field_name == 'type' and order_by == 'asc':
                master_queryset = PmsExecutionPurchasesRequisitionsMaster.objects.filter(id__in=master_id_list,is_deleted=False).order_by('type')
            elif field_name == 'type' and order_by == 'desc':
                master_queryset = PmsExecutionPurchasesRequisitionsMaster.objects.filter(id__in=master_id_list,is_deleted=False).order_by('-type')
            else:
                master_queryset = PmsExecutionPurchasesRequisitionsMaster.objects.filter(id__in=master_id_list,is_deleted=False)
        else:
            master_queryset = PmsExecutionPurchasesRequisitionsMaster.objects.filter(id__in=master_id_list,is_deleted=False)
    

        data_dict={}

        data_list=[]
        requisiton_list=[]
        for response_data in master_queryset:
            #print('response_data::::::::::project',response_data.type,response_data.project)
            type_details=PmsExecutionPurchasesRequisitionsTypeMaster.objects.get(id=response_data.type.id)
            #print("type_details::::::::",type_details)
            project_details=PmsProjects.objects.filter(id=response_data.project.id).values('id','project_g_id')
            site_details=PmsSiteProjectSiteManagement.objects.filter(id=response_data.site_location.id).values('id','name')
            
            if item_val:
                item_list= list(map(int,item_val.split(",")))
                req_master_pending_id = PmsExecutionPurchasesRequisitions.objects.filter(is_deleted=False,requisitions_master=response_data.id,item__in=item_list)
            elif field_name == 'item' and order_by == 'asc':
                req_master_pending_id = PmsExecutionPurchasesRequisitions.objects.filter(is_deleted=False,requisitions_master=response_data.id).order_by('item')
            elif field_name == 'item' and order_by == 'desc':
                req_master_pending_id = PmsExecutionPurchasesRequisitions.objects.filter(is_deleted=False,requisitions_master=response_data.id).order_by('-item')
            else:    
                req_master_pending_id = PmsExecutionPurchasesRequisitions.objects.filter(is_deleted=False,requisitions_master=response_data.id)
            requisiton_dict={}

            if type_details.type_name.lower() == 'materials':
                for each in req_master_pending_id:
                    #print('each.id',each.id)
                    activity_map_data=PmsExecutionPurchasesRequisitionsMapWithActivities.objects.filter(requisitions=each.id).values('activity__description')
                    activity_map_data_list=[x['activity__description'] for x in activity_map_data]
                    item_details=Materials.objects.filter(id=each.item)
                    for item in item_details:
                        requisiton_dict={
                            'requisition_master_id':response_data.id,
                            'requsition_id':int(each.id),
                            'item_id':item.id,
                            'item_code':item.mat_code,
                            'item':item.name,
                            'description':item.description,
                            'uom':each.uom.c_name,
                            'Activity':activity_map_data_list,
                            'quantity':each.quantity,
                            'required_by':each.required_by,
                            'required_on':each.required_on,
                            'project':project_details[0],
                            'site_location':site_details[0],
                            'type':type_details.type_name,
                            'status':response_data.status,
                            'mr_date':response_data.mr_date
                        }

                        
                        approved_item = PmsExecutionPurchasesRequisitionsApproval.objects.filter(
                            arm_approval__gt=False,is_deleted=False,requisitions_master=response_data.id,item = item.id,uom = each.uom.id)

                        for approved in approved_item:
                            if approved.approval_permission_user_level:
                                requisiton_dict['approved_quantity'] = approved.approved_quantity
                                requisiton_dict['approval_date'] = approved.created_at
                                requisiton_dict['approved_unit'] = approved.uom.c_name if approved.uom else ''   
                                requisiton_dict['approval_level'] = approved.approval_permission_user_level.permission_level
                                requisiton_dict['approval_by'] = approved.approval_permission_user_level.approval_user.first_name+" "+approved.approval_permission_user_level.approval_user.last_name
                        requisiton_list.append(requisiton_dict)
            elif type_details.type_name.lower() == 'machinery':
               
                for each in req_master_pending_id:
                    activity_map_data=PmsExecutionPurchasesRequisitionsMapWithActivities.objects.filter(requisitions=each.id).values('activity__description')
                    activity_map_data_list=[x['activity__description'] for x in activity_map_data]
                    item_details=PmsMachineries.objects.filter(id=each.item)
                    for item in item_details:
                        requisiton_dict={
                            'requisition_master_id':response_data.id,
                            'requsition_id':int(each.id),
                            'item_id':item.id,
                            'item_code':item.code,
                            'item':item.equipment_name,
                            'description':'',
                            'uom':each.uom.c_name,
                            'Activity':activity_map_data_list,
                            'quantity':each.quantity,
                            'required_by':each.required_by,
                            'required_on':each.required_on,
                            'project':project_details[0],
                            'site_location':site_details[0],
                            'type':type_details.type_name,
                            'status':response_data.status,
                            'mr_date':response_data.mr_date

                        }
                        
                        approved_item = PmsExecutionPurchasesRequisitionsApproval.objects.filter(is_deleted=False,requisitions_master=response_data.id,item = item.id)

                        for approved in approved_item:
                            if approved.approval_permission_user_level:
                                requisiton_dict['approved_quantity'] = approved.approved_quantity
                                requisiton_dict['approval_date'] = approved.created_at 
                                requisiton_dict['approval_level'] = approved.approval_permission_user_level.permission_level
                                requisiton_dict['approval_by'] = approved.approval_permission_user_level.approval_user.first_name+" "+approved.approval_permission_user_level.approval_user.last_name
                        requisiton_list.append(requisiton_dict)


        response.data['results'] =requisiton_list

        return response



#:::::::::::::::::::::: PMS EXECUTION PURCHASES DISPATCH:::::::::::::::::::::::::::#
class ExecutionPurchasesDispatchAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesDispatch.objects.filter(is_deleted=False)
    serializer_class = ExecutionPurchasesDispatchAddSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('requisitions_master',)
    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        return response
class ExecutionPurchasesDispatchEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesDispatch.objects.filter(is_deleted=False)
    serializer_class = ExecutionPurchasesDispatchEditSerializer
class ExecutionPurchasesDispatchDeleteView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesDispatch.objects.filter(is_deleted=False)
    serializer_class = ExecutionPurchasesDispatchDeleteSerializer
class ExecutionPurchasesDispatchListView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    # pagination_class = CSPageNumberPagination
    queryset = PmsExecutionPurchasesDispatch.objects.filter(is_deleted=False)
    serializer_class = ExecutionPurchasesDispatchListSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('requisitions_master',)

    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        return response
class ExecutionPurchasesDispatchDocumentAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesDispatchDocument.objects.filter(is_deleted=False)
    serializer_class =  ExecutionPurchasesDispatchDocumentAddSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('dispatch',)
    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        return response
class ExecutionPurchasesDispatchDocumentEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesDispatchDocument.objects.all()
    serializer_class = ExecutionPurchasesDispatchDocumentEditSerializer

#:::::::::::::::::::::: PMS EXECUTION PURCHASES DELIVERY:::::::::::::::::::::::::::#
class ExecutionPurchasesDeliveryAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesDelivery.objects.filter(is_deleted=False)
    serializer_class = ExecutionPurchasesDeliveryAddSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('requisitions_master',)
    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        return response
class ExecutionPurchasesDeliveryListView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    # pagination_class = CSPageNumberPagination
    queryset = PmsExecutionPurchasesDelivery.objects.filter(is_deleted=False)
    serializer_class = ExecutionPurchasesDeliveryListSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('requisitions_master',)

    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        return response

class ExecutionPurchasesDeliveryEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesDelivery.objects.filter(is_deleted=False)
    serializer_class = ExecutionPurchasesDeliveryEditSerializer
class ExecutionPurchasesDeliveryDocumentAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesDeliveryDocument.objects.filter(is_deleted=False)
    serializer_class =  ExecutionPurchasesDeliveryDocumentAddSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('delivery',)
    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        return response
class ExecutionPurchasesDeliveryDeleteView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesDelivery.objects.filter(is_deleted=False)
    serializer_class = ExecutionPurchasesDeliveryDeleteSerializer


class ExecutionPurchasesTotalDeliveryMaterialRecievedListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesDelivery.objects.filter(requisitions_master__status=6,is_deleted=False)
    serializer_class = PurchaseRequisitionsTotalDeliveryMaterialRecievedListSerializer
    pagination_class = CSPageNumberPagination

    def get_queryset(self):
        # queryset=self.queryset.filter(status=1)
        filter = {}
        project = self.request.query_params.get('project', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        site_location = self.request.query_params.get('site_location', None)
        type_name = self.request.query_params.get('type_name', None)
        search = self.request.query_params.get('search', None)
        item_type = self.request.query_params.get('item_type', None)
        item = self.request.query_params.get('item', None)
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        
        if field_name and order_by:

            if field_name == 'project' and order_by == 'asc':
                return self.queryset.filter(is_deleted=False).order_by('project__id')
            elif field_name == 'project' and order_by == 'desc':
                return self.queryset.filter(is_deleted=False).order_by('-project__id')

            elif field_name == 'site_location' and order_by == 'asc':
                return self.queryset.filter(requisitions_master__status=6, is_deleted=False).order_by('requisitions_master__site_location')
            elif field_name == 'site_location' and order_by == 'desc':
                return self.queryset.filter(requisitions_master__status=6, is_deleted=False).order_by('-requisitions_master__site_location')
            elif field_name == 'vendor' and order_by == 'asc':
                return self.queryset.filter(requisitions_master__status=6, is_deleted=False).order_by('vendor')
            elif field_name == 'vendor' and order_by == 'desc':
                return self.queryset.filter(requisitions_master__status=6, is_deleted=False).order_by('-vendor')
            elif field_name == 'uom' and order_by == 'asc':
                return self.queryset.filter(requisitions_master__status=6, is_deleted=False).order_by('uom')
            elif field_name == 'uom' and order_by == 'desc':
                return self.queryset.filter(requisitions_master__status=6, is_deleted=False).order_by('-uom')
            elif field_name == 'date_of_delivery' and order_by == 'asc':
                return self.queryset.filter(requisitions_master__status=6, is_deleted=False).order_by('date_of_delivery')
            elif field_name == 'date_of_delivery' and order_by == 'desc':
                return self.queryset.filter(requisitions_master__status=6, is_deleted=False).order_by('-date_of_delivery')
            elif field_name == 'received_quantity' and order_by == 'asc':
                return self.queryset.filter(requisitions_master__status=6, is_deleted=False).order_by('received_quantity')
            elif field_name == 'received_quantity' and order_by == 'desc':
                return self.queryset.filter(requisitions_master__status=6, is_deleted=False).order_by('-received_quantity')

            elif field_name == 'received_item' and order_by == 'asc':
                return self.queryset.filter(requisitions_master__status=6, is_deleted=False).order_by('received_item')
            elif field_name == 'received_item' and order_by == 'desc':
                return self.queryset.filter(requisitions_master__status=6, is_deleted=False).order_by('-received_item')

        if search :
            #print("This is if condition entry")
            queryset = self.queryset.filter(requisitions_master__status=6,requisitions_master__project__project_g_id=search)

            #print('queryset_search::::::::::::::::::::', queryset)
            return queryset


        if start_date and end_date:
            start_object = datetime.strptime(start_date, '%Y-%m-%d').date()
            filter['requisitions_master__mr_date__gte'] = start_object
            end_object = datetime.strptime(end_date, '%Y-%m-%d').date()
            filter['requisitions_master__mr_date__lte'] = end_object + timedelta(days=1)

            queryset = self.queryset.filter(requisitions_master__status=6,**filter)

            return queryset

        if site_location:
            filter['requisitions_master__site_location__in']=list(map(int,site_location.split(",")))

        if project:
            filter['requisitions_master__project__in']=list(map(int,project.split(",")))


        if type_name:
            #print("halla ")
            if type_name.lower() == 'materials':
                filter['requisitions_master__type'] = 1
            elif type_name.lower() == 'machinery':
                #print("hala ")
                filter['requisitions_master__type'] = 2

        if item:
            filter['received_item__in']= list(map(int,item.split(",")))
            #print("item:::::::::::::::::::",filter)
            

        if filter:
            queryset = self.queryset.filter(requisitions_master__status=6,**filter)

            #print('queryset',queryset)
            return queryset
        else:
            queryset=self.queryset.filter(requisitions_master__status=6)
            return queryset

    @response_modify_decorator_list_or_get_after_execution_for_pagination
    def get(self,request,*args,**kwargs): 
        
        response = super(ExecutionPurchasesTotalDeliveryMaterialRecievedListView, self).get(request, args, kwargs)
        material_recieved=[]
        for data in response.data['results']:
            material_recieved_dict={}
            master_data=PmsExecutionPurchasesRequisitionsMaster.objects.filter(id=data['requisitions_master']).values('site_location','project','type','status')
            type_details=PmsExecutionPurchasesRequisitionsTypeMaster.objects.filter(id=master_data[0]['type']).values('id','type_name','code')
            project_details=PmsProjects.objects.filter(id=master_data[0]['project']).values('id','project_g_id')
            site_details=PmsSiteProjectSiteManagement.objects.filter(id=master_data[0]['site_location']).values('id','name')
            uom_details=TCoreUnit.objects.filter(id=data['uom']).values('id','c_name')
            material_details=Materials.objects.filter(id=data['received_item']).values('id','mat_code','name')
            vendor_details=PmsExternalUsers.objects.filter(id=data['vendor']).values('id','contact_person_name')
            required_by_name=PmsExecutionPurchasesRequisitions.objects.filter(requisitions_master=data['requisitions_master'],item=material_details[0]['id']).values('required_by')
            #print('vendor_details::::::::',vendor_details,'material_details::::::::',material_details)
            document_details=PmsExecutionPurchasesDeliveryDocument.objects.filter(delivery=data['id'])
            cost_data=PmsExecutionPurchasesDispatch.objects.filter(requisitions_master=data['requisitions_master'],dispatch_item=material_details[0]['id']).values('dispatch_cost')
            #print(document_details)
            material_recieved_dict={
                'id':data['id'],
                'status':master_data[0]['status'],
                'site_location':site_details[0],
                'project':project_details[0],
                'type':type_details[0],
                'item':material_details[0],
                'quantity':data['received_quantity'],
                'delivery_date':data['date_of_delivery'],
                'uom':uom_details[0],
                'vendor':vendor_details[0],
                'requisitions_master':data['requisitions_master'],
            }
            if cost_data:
                material_recieved_dict['cost']=cost_data[0]['dispatch_cost']
            else:
                material_recieved_dict['cost']='null'
            if required_by_name:
                material_recieved_dict['required_by']=required_by_name[0]
            else:
                material_recieved_dict['required_by']='null'
            # if document_details:
            #     doc=[]
            #     for x in document_details:
            #         print('doc',x['document'])
            #         doc.append(request.build_absolute_uri('./media/'+str(x['document'])))
            #     material_recieved_dict['document_details']=doc
            # else:
            #     material_recieved_dict['document_details']=[]
            if document_details:
                doc=[]
                for x in document_details:
                    doc.append(request.build_absolute_uri(x.document.url))
                material_recieved_dict['document_details']=doc
            else:
                material_recieved_dict['document_details']=[]

            material_recieved.append(material_recieved_dict)

        response.data['results']=material_recieved

        return response


#:::::::::::::::::::::::::::::::::PMS EXECUTION PURCHASES PAYMENT::::::::::::::::::::::::::::::::::::::::::::::::::::#
class ExecutionPurchasesPaymentPlanAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesPaymentPlan.objects.filter(is_deleted=False)
    serializer_class = ExecutionPurchasesPaymentPlanAddSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('requisitions_master',)
    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        return response
#:::::::::::::::::::::: PMS EXECUTION PURCHASES PAYMENTS MADE:::::::::::::::::::::::::::#
class ExecutionPurchasesPaymentsMadeAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesPaymentsMade.objects.filter(is_deleted=False)
    serializer_class = ExecutionPurchasesPaymentsMadeAddSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('requisitions_master',)
    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        return response

class ExecutionPurchasesPaymentsMadeEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesPaymentsMade.objects.all()
    serializer_class = ExecutionPurchasesPaymentsMadeEditSerializer
class ExecutionPurchasesPaymentsMadeDeleteView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesPaymentsMade.objects.all()
    serializer_class = ExecutionPurchasesPaymentsMadeDeleteSerializer
class ExecutionPurchasesPaymentsMadeDocumentAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesPaymentsMadeDocument.objects.filter(is_deleted=False)
    serializer_class =  ExecutionPurchasesPaymentsMadeDocumentAddSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('purchases_made','purchases_made__requisitions_master')
    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        return response
class ExecutionPurchasesPaymentsMadeDocumentEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesPaymentsMadeDocument.objects.all()
    serializer_class = ExecutionPurchasesPaymentsMadeDocumentEditSerializer
class ExecutionPurchasesPaymentsMadeDocumentDeleteView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesPaymentsMadeDocument.objects.all()
    serializer_class = ExecutionPurchasesPaymentsMadeDocumentDeleteSerializer
class ExecutionPurchasesPaymentsMadeListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesPaymentsMade.objects.filter(is_deleted=False)
    serializer_class = ExecutionPurchasesPaymentsMadeListSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('requisitions_master',)

    def get(self,request,*args,**kwargs):
        response=super(ExecutionPurchasesPaymentsMadeListView,self).get(request,args,kwargs)
        # print("response.data",response.data[0]['requisitions_master'])
        data_dict = {}
        requisitions_master = self.request.query_params.get('requisitions_master', None)
        completed_status = PmsExecutionPurchasesRequisitionsMaster.objects.only('completed_status').get(
            id=requisitions_master).completed_status
        data_dict['completed_status'] = completed_status

        data_dict['result'] = response.data
        for data in response.data:
            # print('data',data)
            doc_list = list()
            payment_doc=PmsExecutionPurchasesPaymentsMadeDocument.objects.filter(purchases_made_id=data['id'],is_deleted=False)
            for p_d in payment_doc:
                data1={
                    'id':p_d.id,
                    'purchases_made':p_d.purchases_made.id,
                    'document_name':p_d.document_name,
                    'document':request.build_absolute_uri(p_d.document.url)
                }
                doc_list.append(data1)
            #print('doc_list',doc_list)
            data['payment_made_document']=doc_list
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

class ExecutionPurchasesTotalAmountPayableListView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    # pagination_class = CSPageNumberPagination
    queryset = PmsExecutionPurchasesTotalAmountPayable.objects.filter(is_deleted=False)
    serializer_class = ExecutionPurchasesTotalAmountPayableListSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('requisitions_master',)

    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        return response


#:::::::::: PMS EXECUTION STOCK ::::::::::::::::::::::::::::::::::::#
class ExecutionStockIssueModeAdd(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionIssueMode.objects.all()
    serializer_class = StockIssueModeSerializeradd


    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        return response

class ExecutionStockIssueModeEdit(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionIssueMode.objects.all()
    serializer_class = StockIssueModeSerializeredit


class ExecutionStockMobileIssueEdit(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionStockIssue.objects.all()
    serializer_class = StockIssueMobileSerializeredit
    def get_queryset(self):
        pk=self.kwargs['pk']
        if pk:
            return self.queryset.filter(id=pk,is_deleted=False)

    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        # print(response)
        return response

class ExecutionStockMobileIssueDelete(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionStockIssue.objects.all()
    serializer_class = StockMobileIssueSerializerdelete

    def get_queryset(self):
        pk=self.kwargs['pk']
        if pk:
            return self.queryset.filter(id=pk,is_deleted=False)

    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        # print(response)
        return response

class ExecutionStockIssueModeDelete(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionIssueMode.objects.all()
    serializer_class = StockIssueModeSerializerdelete


class ExecutionStockIssueAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionStockIssueMaster.objects.all()
    serializer_class = StockIssueAddSerializer

class ExecutionStockMobileIssueAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionStockIssueMaster.objects.all()
    serializer_class = StockIssueMobileAddSerializer

class ExecutionStockIssueEdit(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionStockIssueMaster.objects.filter(is_deleted=False)
    serializer_class = StockIssueSerializeredit
    
    

class ExecutionStockIssueListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionStockIssueMaster.objects.filter(is_deleted=False)
    serializer_class = StockIssueListSerializer
    pagination_class = CSPageNumberPagination

    def get_queryset(self):
        project_id = self.kwargs['project_id']
        site_id = self.kwargs['site_id']
        #print('project_id',project_id)
        if project_id and site_id:
            return self.queryset.filter(project_id=project_id, site_location=site_id,is_deleted=False)



    @response_modify_decorator_list_or_get_before_execution_for_pagination
    def get(self, request, *args, **kwargs):
        # print(response)
        return response


class ExecutionStockEachIssueListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionStockIssue.objects.filter(is_deleted=False)
    serializer_class = StockIssueMobileEachListSerializer

    def get_queryset(self):
        pk = self.kwargs['pk']
        if pk:
            return self.queryset.filter(id=pk,is_deleted=False)


    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        # print(response)
        return response
class ExecutionStockIssueApprovedListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    pagination_class = CSPageNumberPagination
    queryset = PmsExecutionStockIssueMaster.objects.filter(is_deleted=False)
    serializer_class = StockIssueApprovedListSerializer

    def get_queryset(self):
        project_id = self.kwargs['project_id']
        site_id = self.kwargs['site_id']
        #print('project_id',project_id)
        if project_id and site_id:
            return self.queryset.filter(project_id=project_id, site_location=site_id,is_deleted=False,issue_stage_status__gt=1).order_by('-id')


    @response_modify_decorator_list_or_get_before_execution_for_pagination
    def get(self, request, *args, **kwargs):
        # print(response)
        return response

class ExecutionStockIssueNonApprovedListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    pagination_class = CSPageNumberPagination
    queryset = PmsExecutionStockIssueMaster.objects.filter(is_deleted=False)
    serializer_class = StockIssueNonApprovedListSerializer

    def get_queryset(self):
        project_id = self.kwargs['project_id']
        site_id = self.kwargs['site_id']
        #print('project_id',project_id)
        if project_id and site_id:
            return self.queryset.filter(project_id=project_id, site_location=site_id,is_deleted=False,issue_stage_status=1).order_by('-id')


    @response_modify_decorator_list_or_get_before_execution_for_pagination
    def get(self, request, *args, **kwargs):
        # print(response)
        return response

class ExecutionPurchasesComparitiveStatementItemSubmitApprovalView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesRequisitions.objects.filter(is_deleted=False)
    serializer_class = ExecutionPurchasesComparitiveStatementItemSumbmitApprovalSerializer

class ExecutionStockMonthReportListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionStock.objects.filter(is_deleted=False)
    serializer_class = StocMonthlyReportListSerializer
    pagination_class = OnOffPagination
    
    def get_queryset(self):
        project = self.kwargs["project_id"]
        site_location = self.kwargs["site_id"] 
        item_type_id = PmsExecutionPurchasesRequisitionsTypeMaster.objects.only('id').get(type_name='materials').id
        product_name = self.request.query_params.get('product_name',None)
        
        filter = dict()
        pk_list = list()
        queryset = self.queryset.values('item', 'uom').distinct()
        for each in queryset:
            #print('each',each)
            pk_stock_details = PmsExecutionStock.objects.filter(
                item=each['item'],uom=each['uom']).values_list('id',flat=True).order_by('-stock_date').first()
            pk_list.append(pk_stock_details)
        
        #print('pk_list',pk_list)
        filter['pk__in'] = pk_list
        if product_name:
            product_ids = Materials.objects.filter(name__contains=product_name.lower()).values_list('id',flat=True)
            filter['item__in'] = product_ids
        
        queryset = PmsExecutionStock.objects.filter(project=project, site_location=site_location, type=item_type_id,**filter)
        return queryset

    def get_month_dates(self, year, month) -> list:
        date_list = []
        cal = calendar.Calendar()
        for cal_date in cal.itermonthdates(year, month):
            if cal_date.month == month:
                cal_d = cal_date.strftime('%Y-%m-%d')
                date_list.append(cal_d)
        return date_list

    @response_modify_decorator_list_or_get_after_execution_for_onoff_pagination
    def list(self, request, *args, **kwargs):
        try:
            project_id = self.kwargs["project_id"]
            site_id = self.kwargs["site_id"]
            #print("project_id",project_id,"site_id",site_id)
            response = super(ExecutionStockMonthReportListView, self).list(request, args, kwargs)
            # print('request',response.data)

            response1 = response.data['results'] if 'results' in response.data else response.data

            current_date = datetime.today().date()
            year = self.request.query_params['year'] if 'year' in self.request.query_params else int(
                current_date.strftime("%Y"))
            month = self.request.query_params['month'] if 'month' in self.request.query_params else int(
                current_date.strftime("%m"))
            item_dict={}

            project_item = set()
            month_date_list = self.get_month_dates(int(year), int(month))

            from_date = self.request.query_params.get('from_date',None)
            to_date = self.request.query_params.get('to_date',None)

            if year and month:
                if from_date and to_date:
                    year_month_list = list()
                    for day in range(int(from_date),int(to_date) + 1):
                        if day in range(1,10):
                            year_month = str(year) +'-'+str(month)+'-0'+str(day)
                        else:
                            year_month = str(year) +'-'+str(month)+'-'+str(day)
                        year_month_list.append(year_month)
                    month_date_list = year_month_list
                    #print('year_month_list',year_month_list)
            
            for data in response1:
            
                stock_List = []
                item_dict ={
                    'item': [x for x in Materials.objects.filter(
                        id=data['item'],is_deleted=False).values('id', 'name')][0],
                    'unit': [x for x in TCoreUnit.objects.filter(
                        id=data['uom'],c_is_deleted=False).values('id', 'c_name')][0]
                }

                for date in month_date_list:
                    issued_stock = PmsExecutionStock.objects.filter(
                                            stock_date__date=date,
                                            item=data['item'],
                                            uom=data['uom'],is_deleted=False).aggregate(Sum('issued_stock'))['issued_stock__sum']

                    recieved_stock = PmsExecutionStock.objects.filter(
                                            stock_date__date=date,
                                            item=data['item'],
                                            uom=data['uom'],is_deleted=False).aggregate(Sum('recieved_stock'))['recieved_stock__sum']

                    purpose = PmsExecutionStock.objects.filter(
                        stock_date__date=date, item=data['item'],
                        uom=data['uom'],is_deleted=False).values_list('purpose',flat=True).last()
                        
                    stock_details = {
                        'date': date,
                        'recieved_stock': recieved_stock if recieved_stock else str(0.00),
                        'issued_stock': issued_stock if issued_stock else str(0.00),
                        'purpose': purpose,
                    }
                   
                    stock_List.append(stock_details)
                data['item'] = item_dict['item']
                data['uom']=item_dict['unit']
                data['month_stock_list_details'] = stock_List

            return response

        except Exception as e:
            raise e

class ExecutionStockMonthReportDownloadView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionStock.objects.filter(is_deleted=False)
    serializer_class = StocMonthlyReportListSerializer
    
    def get_queryset(self):
        project = self.kwargs["project_id"]
        site_location = self.kwargs["site_id"] 
        item_type_id = PmsExecutionPurchasesRequisitionsTypeMaster.objects.only('id').get(type_name='materials').id
        product_name = self.request.query_params.get('product_name',None)
        
        filter = dict()
        pk_list = list()
        queryset = self.queryset.values('item', 'uom').distinct()
        for each in queryset:
            #print('each',each)
            pk_stock_details = PmsExecutionStock.objects.filter(
                item=each['item'],uom=each['uom']).values_list('id',flat=True).order_by('-stock_date__date').first()
            pk_list.append(pk_stock_details)
        
        #print('pk_list',pk_list)
        filter['pk__in'] = pk_list
        if product_name:
            product_ids = Materials.objects.filter(name__contains=product_name.lower()).values_list('id',flat=True)
            filter['item__in'] = product_ids
        
        queryset = PmsExecutionStock.objects.filter(project=project, site_location=site_location, type=item_type_id,**filter)
        return queryset

    def get_month_dates(self, year, month) -> list:
        date_list = []
        cal = calendar.Calendar()
        for cal_date in cal.itermonthdates(year, month):
            if cal_date.month == month:
                cal_d = cal_date.strftime('%Y-%m-%d')
                date_list.append(cal_d)
        return date_list

    def list(self, request, *args, **kwargs):
        try:
            project_id = self.kwargs["project_id"]
            site_id = self.kwargs["site_id"]
            response = super(__class__, self).list(request, args, kwargs)
            response1 = response.data
            data_list = list()
            current_date = datetime.today().date()
            year = self.request.query_params['year'] if 'year' in self.request.query_params else int(
                current_date.strftime("%Y"))
            month = self.request.query_params['month'] if 'month' in self.request.query_params else int(
                current_date.strftime("%m"))
            item_dict={}

            project_item = set()
            month_date_list = self.get_month_dates(int(year), int(month))
            from_date = self.request.query_params.get('from_date',None)
            to_date = self.request.query_params.get('to_date',None)
            
            if year and month:
                if from_date and to_date:
                    year_month_list = list()
                    for day in range(int(from_date),int(to_date) + 1):
                        if day in range(1,10):
                            year_month = str(year) +'-'+str(month)+'-0'+str(day)
                        else:
                            year_month = str(year) +'-'+str(month)+'-'+str(day)
                        year_month_list.append(year_month)
                    month_date_list = year_month_list
            
            for data in response1:
                item_dict ={
                    'item': [x for x in Materials.objects.filter(
                        id=data['item'],is_deleted=False).values_list('name',flat=True)][0],
                    'unit': [x for x in TCoreUnit.objects.filter(
                        id=data['uom'],c_is_deleted=False).values_list('c_name',flat=True)][0]
                }
                stock_List = [item_dict['item'],item_dict['unit']]
                
                for date in month_date_list:
                    issued_stock = PmsExecutionStock.objects.filter(
                                            stock_date__date=date,
                                            item=data['item'],
                                            uom=data['uom'],is_deleted=False).aggregate(Sum('issued_stock'))['issued_stock__sum']

                    recieved_stock = PmsExecutionStock.objects.filter(
                                            stock_date__date=date,
                                            item=data['item'],
                                            uom=data['uom'],is_deleted=False).aggregate(Sum('recieved_stock'))['recieved_stock__sum']

                    purpose = PmsExecutionStock.objects.filter(
                        stock_date__date=date, item=data['item'],
                        uom=data['uom'],is_deleted=False).values_list('purpose',flat=True).last()
                        
                    
                    stock_List.append(recieved_stock if recieved_stock else str(0.00))
                    stock_List.append(issued_stock if issued_stock else str(0.00))
                    stock_List.append(purpose if purpose else '')
                    

                data_list.append(stock_List)

            #return response
            #print('data_list',len(data_list))
            #print('month_date_list',month_date_list,len(month_date_list))
            import calendar
            month = calendar.month_name[int(month)]
            
            '''
                Reason : Generate Excel using Multiindex
                Author : Rupam Hazra
                Date : 11-05-2020
            '''

            if os.path.isdir('media/pms/stock/document'):
                file_name = 'media/pms/stock/document/monthly_stock.xlsx'
                file_path = settings.MEDIA_ROOT_EXPORT + file_name
            else:
                os.makedirs('media/pms/stock/document')
                file_name = 'media/pms/stock/document/monthly_stock.xlsx'
                file_path = settings.MEDIA_ROOT_EXPORT + file_name

            from itertools import product
            year_cols = product(
                month_date_list,
                ['Received', 'Issued', 'Purpose']
            )
            item_unit_header = product(
                [str(month)+' '+str(year)],
                ['Item Description', 'Unit']
            )
            item_unit_cols = pd.MultiIndex.from_tuples(list(item_unit_header))
            year_columns = pd.MultiIndex.from_tuples(list(year_cols))
            
            vals =data_list
            final_df = pd.DataFrame(
                vals,columns=item_unit_cols.append(year_columns)
            )
            
            final_df.index = np.arange(1, len(final_df) + 1) # For start index 1 not 0
            export_csv = final_df.to_excel (file_path)

            if request.is_secure():
                protocol = 'https://'
            else:
                protocol = 'http://'

            url = getHostWithPort(request) + file_name if file_name else None

            if url:                    
                return Response({'request_status':1,'msg':'Found', 'url': url})
            else:
                return Response({'request_status':0,'msg':'Not Found', 'url': url})

        except Exception as e:
            raise e



class ExecutionStockIssueItemListByIssueIdView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionStockIssue.objects.all()
    serializer_class = ExecutionStockIssueItemListByIssueIdSerializer
    def get_queryset(self):
        issue_id = self.request.query_params['issue_id']
        if issue_id:
            return self.queryset.filter(issue_master_id=int(issue_id),is_deleted=False)

    def list(self, request, *args, **kwargs):
        response = super(self.__class__, self).list(request, args, kwargs)
        data_dict = {}
        issue_id = self.request.query_params['issue_id']
        stockMasterDetails_queryset = custom_filter(
            self, PmsExecutionStockIssueMaster,
            filter_columns={
                'id': int(issue_id), 'is_deleted': False
            },
        )
        #print('data_dict',stockMasterDetails_queryset.query)
        stock_master = dict()
        for stockMasterDetails in stockMasterDetails_queryset:
            #print("stockMasterDetails",stockMasterDetails.__dict__)
            stock_master['id'] = stockMasterDetails.id
            stock_master['issue_slip_no'] = stockMasterDetails.issue_slip_no
            stock_master['issue_date'] = stockMasterDetails.issue_date
            stock_master['name_of_contractor'] = stockMasterDetails.name_of_contractor.contact_person_name
            stock_master['issue_stage_status'] = stockMasterDetails.issue_stage_status
            if stockMasterDetails.created_by:
                stock_master['created_by'] = (stockMasterDetails.created_by.first_name +' '+ stockMasterDetails.created_by.last_name ) 
            if stockMasterDetails.requested_by:
                stock_master[
                    'requested_by'] = (stockMasterDetails.requested_by.first_name + ' ' + stockMasterDetails.requested_by.last_name) 
            if stockMasterDetails.authorized_by:
                stock_master[
                    'authorized_by'] = (stockMasterDetails.authorized_by.first_name + ' ' + stockMasterDetails.authorized_by.last_name) 
            if stockMasterDetails.recieved_by:
                stock_master[
                    'recieved_by'] = (stockMasterDetails.recieved_by.first_name + ' ' + stockMasterDetails.recieved_by.last_name) 
            if stockMasterDetails.store_keeper:
                stock_master[
                    'store_keeper'] = (stockMasterDetails.store_keeper.first_name + ' ' + stockMasterDetails.store_keeper.last_name) 
            #level of approvals list 

            section_name = self.request.query_params.get('section_name', None)
            if section_name:
                permission_details=[]
                section_details=TCoreOther.objects.get(cot_name__iexact=section_name)
                approval_master_details = PmsApprovalPermissonMatser.objects.filter(section=section_details.id)
                #print("approval_master_details",approval_master_details)
                log_details=PmsExecutionStockIssueMasterLogTable.objects.\
                        filter(issue_master=issue_id).\
                            values('id','issue_approval','approval_permission_user_level')
                # print(log_details) 
                amd_list=[]
                l_d_list=[]
                for l_d in log_details:
                    l_d_list.append(l_d['approval_permission_user_level'])

                for a_m_d in approval_master_details:
                    if l_d_list:
                        if a_m_d.id in l_d_list:
                            l_d=log_details.filter(approval_permission_user_level=a_m_d.id).order_by('-id')[0]
                            f_name = a_m_d.approval_user.first_name if a_m_d.approval_user else '' 
                            l_name = a_m_d.approval_user.last_name if a_m_d.approval_user else '' 
                            var=a_m_d.permission_level
                            res = re.sub("\D", "", var)
                            permission_dict={
                                "user_level":a_m_d.permission_level,
                                "approval":l_d['issue_approval'],
                                "permission_num":int(res),
                                "user_details":{
                                    "id":a_m_d.approval_user.id if a_m_d.approval_user else None,
                                    "email":a_m_d.approval_user.email if a_m_d.approval_user else None,
                                    "name":  f_name +' '+l_name,
                                    "username":a_m_d.approval_user.username
                                }
                            }
                                

                        else:
                            f_name = a_m_d.approval_user.first_name if a_m_d.approval_user else '' 
                            l_name = a_m_d.approval_user.last_name if a_m_d.approval_user else '' 
                            var=a_m_d.permission_level
                            res = re.sub("\D", "", var)
                            permission_dict={
                                "user_level":a_m_d.permission_level,
                                "permission_num":int(res),
                                "approval":None,
                                "user_details":{
                                    "id":a_m_d.approval_user.id if a_m_d.approval_user else None,
                                    "email":a_m_d.approval_user.email if a_m_d.approval_user else None,
                                    "name":  f_name +' '+l_name,
                                    "username":a_m_d.approval_user.username
                                }
                            }

                        permission_details.append(permission_dict)
                    else:
                        f_name = a_m_d.approval_user.first_name if a_m_d.approval_user else '' 
                        l_name = a_m_d.approval_user.last_name if a_m_d.approval_user else '' 
                        var=a_m_d.permission_level
                        res = re.sub("\D", "", var)
                        permission_dict={
                                "user_level":a_m_d.permission_level,
                                "permission_num":int(res),
                                "approval":None,
                                "user_details":{
                                    "id":a_m_d.approval_user.id if a_m_d.approval_user else None,
                                    "email":a_m_d.approval_user.email if a_m_d.approval_user else None,
                                    "name":  f_name +' '+l_name,
                                    "username":a_m_d.approval_user.username
                                }
                            }
                        permission_details.append(permission_dict)
                
                stock_master['permission_details']=permission_details    
        
        
        
        stock_master['issue_item_details'] = response.data

        data_dict['results'] = stock_master
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
class ExecutionStockIssueSubmitForApprovalView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionStockIssueMaster.objects.all()
    serializer_class = ExecutionStockIssueSubmitForApprovalSerializer

    def get_queryset(self):
        pk=self.kwargs['pk']
        return self.queryset.filter(is_deleted=False,id=pk)
        
class ExecutionCurrentStockReportView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionStock.objects.filter(is_deleted=False)
    serializer_class =ExecutionCurrentStockNewReportSerializer
    pagination_class = OnOffPagination

    def get_queryset(self):
        order_by = self.request.query_params.get('order_by', None)
        field_name = self.request.query_params.get('field_name', None)
        project = self.kwargs.get('project')
        site_location = self.kwargs.get('site_location')
        product_name = self.request.query_params.get('product_name',None)
        
        filter = dict()
        pk_list = list()
        
        queryset = self.queryset.values('item', 'uom').distinct()
        for each in queryset:
            #print('each',each)
            pk_stock_details = PmsExecutionStock.objects.filter(
                item=each['item'],uom=each['uom']).values_list('id',flat=True).order_by('-stock_date').first()
            pk_list.append(pk_stock_details)
        
        #print('pk_list',pk_list)
        filter['pk__in'] = pk_list
        
        #filter = {'pk__in': self.queryset}
        sort_field='-id'

        if product_name:
            product_ids = Materials.objects.filter(name__contains=product_name.lower()).values_list('id',flat=True)
            filter['item__in'] = product_ids
        
        if field_name and order_by:
            if field_name == 'closing_stock' and order_by == 'asc':
                sort_field = 'opening_stock'
            else:
                sort_field = '-opening_stock'
        
        queryset = PmsExecutionStock.objects.filter(project=project, site_location=site_location, **filter).order_by(sort_field)
        return queryset

    @response_modify_decorator_list_or_get_after_execution_for_onoff_pagination
    def get(self, request,*args,**kwargs):
       
        try:
            response = super(self.__class__, self).get(self, request, args, kwargs)
            #print('response',response.data)
            response1 = response.data['results'] if 'results' in response.data else response.data
            
            data_dict={}
            project = self.kwargs.get('project')
            site_location = self.kwargs.get('site_location')
            stock_list = []
            for data in response1:
                #print('data',data)
                materials=Materials.objects.filter(id=data['item'])
                # print('materials',materials)
                # time.sleep(15)
                for m_l in materials:
                    mat_dict={
                        'id':m_l.id,
                        'mat_code':m_l.mat_code,
                        'name':m_l.name,
                        'description':m_l.description
                    }
                if materials:
                    unit_details = TCoreUnit.objects.filter(id=data['uom'])
                    for u_l in unit_details:
                        unit_dict = {
                            'id': u_l.id,
                            'c_name': u_l.c_name
                        }
                    type_details = PmsExecutionPurchasesRequisitionsTypeMaster.objects.filter(
                            id=data['type'])
                    for t_l in type_details:
                        type_dict = {
                            'id': t_l.id,
                            'type_name': t_l.type_name,
                            'code': t_l.code
                        }
                    data['item_details'] = mat_dict
                    data['unit_details'] = unit_dict
                    data['type_details'] = type_dict
                    data['current_stock'] = data['closing_stock']
                else:

                    data['item_details'] = dict()
                    data['unit_details'] = dict()
                    data['type_details'] = dict()
                    data['current_stock'] = 0.00

            return response
        except Exception as e:
            raise e


class ExecutionCurrentStockReportDownloadView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionStock.objects.filter(is_deleted=False)
    serializer_class =ExecutionCurrentStockNewReportSerializer

    def get_queryset(self):
        order_by = self.request.query_params.get('order_by', None)
        field_name = self.request.query_params.get('field_name', None)
        project = self.kwargs.get('project')
        site_location = self.kwargs.get('site_location')
        product_name = self.request.query_params.get('product_name',None)
        
        filter = dict()
        pk_list = list()
        
        queryset = self.queryset.values('item', 'uom').distinct()
        for each in queryset:
            #print('each',each)
            pk_stock_details = PmsExecutionStock.objects.filter(
                item=each['item'],uom=each['uom']).values_list('id',flat=True).order_by('-stock_date__date').first()
            pk_list.append(pk_stock_details)
        
        #print('pk_list',pk_list)
        filter['pk__in'] = pk_list
        
        #filter = {'pk__in': self.queryset}
        sort_field='-id'

        if product_name:
            product_ids = Materials.objects.filter(name__contains=product_name.lower()).values_list('id',flat=True)
            filter['item__in'] = product_ids
        
        if field_name and order_by:
            if field_name == 'closing_stock' and order_by == 'asc':
                sort_field = 'opening_stock'
            else:
                sort_field = '-opening_stock'
        
        queryset = PmsExecutionStock.objects.filter(project=project, site_location=site_location, **filter).order_by(sort_field)
        return queryset

    def get(self, request,*args,**kwargs):
       
        try:
            response = super(self.__class__, self).get(self, request, args, kwargs)
            response1 = response.data['results'] if 'results' in response.data else response.data
            data_list = list()
            for data in response1:
                materials=Materials.objects.filter(id=data['item'])
                for m_l in materials:
                    mat_dict={
                        'id':m_l.id,
                        'mat_code':m_l.mat_code,
                        'name':m_l.name,
                        'description':m_l.description
                    }
                if materials:
                    unit_details = TCoreUnit.objects.filter(id=data['uom'])
                    for u_l in unit_details:
                        unit_dict = {
                            'id': u_l.id,
                            'c_name': u_l.c_name
                        }
                    type_details = PmsExecutionPurchasesRequisitionsTypeMaster.objects.filter(
                            id=data['type'])
                    for t_l in type_details:
                        type_dict = {
                            'id': t_l.id,
                            'type_name': t_l.type_name,
                            'code': t_l.code
                        }
                    data['current_stock'] = str(data['closing_stock']) if data['closing_stock'] else str(0.00)
                    data_list.append([mat_dict['name'],mat_dict['mat_code'],unit_dict['c_name'],data['current_stock']])

            file_name = ''
            
            if data_list:
                if os.path.isdir('media/pms/stock/document'):
                    file_name = 'media/pms/stock/document/current_stock.xlsx'
                    file_path = settings.MEDIA_ROOT_EXPORT + file_name
                else:
                    os.makedirs('media/pms/stock/document')
                    file_name = 'media/pms/stock/document/current_stock.xlsx'
                    file_path = settings.MEDIA_ROOT_EXPORT + file_name

                final_df = pd.DataFrame(data_list, columns=['Item Name','Item Code','Unit','Current Stock'])
                export_csv = final_df.to_excel (file_path, index = None, header=True)
                if request.is_secure():
                    protocol = 'https://'
                else:
                    protocol = 'http://'

            url = getHostWithPort(request) + file_name if file_name else None
            #response.data['url'] = url
            if url:                    
                return Response({'request_status':1,'msg':'Found', 'url': url}) 
            else:
                return Response({'request_status':0,'msg':'Not Found', 'url': url})
        except Exception as e:
            raise e







class ExecutionMaterialStockStatementReportView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionStock.objects.filter(is_deleted=False)
    serializer_class = ExecutionCurrentStockNewReportSerializer
    pagination_class = OnOffPagination
    
    def get_month_dates(self, year, month) -> list:
        date_list = []
        cal = calendar.Calendar()
        for cal_date in cal.itermonthdates(year, month):
            if cal_date.month == month:
                cal_d = cal_date.strftime('%Y-%m-%d')

                date_list.append(cal_d)

        return date_list
    def get_month_value(self, month_range) -> list:
        from collections import OrderedDict
        month_list = []
        start, end = [datetime.strptime(_, "%Y-%m-%d") for _ in month_range]
        month_list = OrderedDict(
            ((start + timedelta(_)).strftime(r"%B-%Y"), None) for _ in range((end - start).days)).keys()
        return month_list

    def get_queryset(self):
        '''
            Report generate from PmsExecutionStock 
            but unique item taking from PmsExecutionUpdatedStock
        '''
        project = self.kwargs.get('project')
        site_location = self.kwargs.get('site_location')
        product_name = self.request.query_params.get('product_name',None)
        
        item_type_id = PmsExecutionPurchasesRequisitionsTypeMaster.objects.only('id').get(type_name='Materials').id
        #print('item_type_id',item_type_id)
        filter = dict()
        pk_list = list()
        queryset = self.queryset.values('item', 'uom').distinct()
        for each in queryset:
            #print('each',each)
            pk_stock_details = PmsExecutionStock.objects.filter(
                item=each['item'],uom=each['uom']).values_list('id',flat=True).order_by('-stock_date').first()
            pk_list.append(pk_stock_details)
        
        #print('pk_list',pk_list)
        filter['pk__in'] = pk_list

        if product_name:
            product_ids = Materials.objects.filter(name__icontains=product_name.lower()).values_list('id',flat=True)
            filter['item__in'] = product_ids
        
        queryset = PmsExecutionStock.objects.filter(project=project, site_location=site_location,type_id=item_type_id, **filter)
        return queryset
        

    @response_modify_decorator_list_or_get_after_execution_for_onoff_pagination
    def list(self, request, *args, **kwargs):
        try:
            from time import strptime
            response = super(self.__class__, self).list(self, request, args, kwargs)
            #print('response',response.data)
            response1 = response.data['results'] if 'results' in response.data else response.data
            #print('response1',response1)
            data_dict = {}
            project = self.kwargs.get('project')
            site_location = self.kwargs.get('site_location')
            year = self.request.query_params.get('year', None)
            month = self.request.query_params.get('month',None)
            month_year = self.request.query_params.get('month_year',None)

            time_span = PmsProjects.objects.filter(id=project, is_deleted=False).values('start_date', 'end_date')[0]
            # print("time_span",time_span['start_date'] )
            start_date = datetime.strftime(time_span['start_date'].date(), '%Y-%m-%d')
            end_date = datetime.strftime(time_span['end_date'].date(), '%Y-%m-%d')
            month_range = [start_date, end_date]
            month_length = self.get_month_value(month_range)

            m_len_list = [x for x in month_length]
            #print("month_length", m_len_list)

            if month_year:
                m_len_list = month_year.split(',')
        
            #print("month_length", m_len_list)
            # print("start_date",start_date[0:10],"end_date",end_date[0:10])
            all_month = [('January', 1), ('February', 2), ('March', 3), ('April', 4), ('May', 5), ('June', 6), ('July', 7), ('August', 8),
                         ('September', 9), ('October', 10), ('November', 11), ('December', 12)]
            #al_yr = [('19', 2019), ('20', 2020), ('21', 2021), ('22', 2022)]
            al_yr = [('2018', 2018),('2019', 2019), ('2020', 2020), ('2021', 2021), ('2022', 2022)]

            stock_item = response1
            s_item = list(set([x['item'] for x in stock_item]))
            #print("s_item", s_item)
            stock_unit = list(set([x['uom'] for x in stock_item]))
            #print('stock_unit', stock_unit)

           

            for data in response1:
                data['item_details'] = {
                    'id':data['item'],
                    'name': Materials.objects.only('name').get(id=data['item']).name
                } 
                data['uom_details'] = {
                    'id':data['uom'],
                    'name': TCoreUnit.objects.only('c_name').get(id=data['uom']).c_name
                } 
                stock_list = list()
                for month in m_len_list:
                    month = month.split('-')
                    mm = month[0]
                    yr = month[1]
                    mm_num = strptime(mm, '%B').tm_mon
                    
                    for key, values in all_month:
                        #print('month',key)
                        if key == mm:
                            for k, v in al_yr:
                                stock_mm_list = list()
                                if k == yr:
                                    stock_dict = {
                                        'month': mm,
                                        'year': v
                                    }
                                    #print(stock_dict)
                                    #found = 0

                                    date_list = self.get_month_dates(v, values)

                                    stock_det_dict = {}
                                    i_opening_stock = 0
                                    stock_opening = PmsExecutionStock.objects.filter(
                                        project=project,
                                        site_location=site_location,
                                        item=data['item'],
                                        uom=data['uom'],
                                        stock_date__month=mm_num,
                                        stock_date__year=v,
                                    ).values('id','opening_stock','closing_stock').last()

                                    #print('stock_opening',stock_opening)
                                    #time.sleep(1)
                                    if stock_opening:
                                        #stock_opening = stock_opening[0]
                                        #print('stock_opening',stock_opening)
                                        #time.sleep(20)
                                        #found = 1
                                        #i_opening_stock = float(stock_opening.opening_stock)
                                        # stock_det_dict = {
                                        #     'id': stock_opening.id,
                                        #     'opening_stock': float(stock_opening.opening_stock),
                                        #     'closing_stock': float(stock_opening.closing_stock)
                                        # }
                                        stock_det_dict = stock_opening
                                    else:
                                        '''
                                            Set previous month closeing stock  = next month opening stock by below logic
                                        '''
                                        #print('mm_num',mm_num,type(mm_num))
                                        stock_closing = PmsExecutionStock.objects.filter(
                                            project=project,
                                            site_location=site_location,
                                            item=data['item'],
                                            uom=data['uom'],
                                            stock_date__month= mm_num - 1,
                                            stock_date__year=v,
                                        ).values('id','opening_stock','closing_stock').last()
                                        #print('stock_closing',stock_closing)
                                        if stock_closing:
                                            
                                            i_closing_stock = stock_closing['closing_stock'] if stock_closing['closing_stock'] else 0
                                            if i_closing_stock == 0:
                                                stock_det_dict['opening_stock'] = float(stock_closing['opening_stock'])
                                                stock_det_dict['closing_stock'] = str(0.00) 
                                            else:
                                                stock_det_dict['opening_stock'] = float(i_closing_stock)
                                                stock_det_dict['closing_stock'] = str(0.00)
                                        else:
                                            stock_det_dict['opening_stock'] = str(0.00)
                                            stock_det_dict['closing_stock'] = str(0.00)

                                        #stock_det_dict['closing_stock'] = stock_opening

                                    #print('stock_det_dict',stock_det_dict)

                                    filter = {}
                                    filter['stock_date__gte'] = datetime.strptime(date_list[0], "%Y-%m-%d")
                                    filter['stock_date__lte'] = datetime.strptime(date_list[-1], "%Y-%m-%d") + timedelta(days=1)
                                    

                                    stock_issue = PmsExecutionStock.objects.filter(
                                            project=project,
                                            site_location=site_location, 
                                            item=data['item'],uom=data['uom'],**filter).aggregate(
                                                Sum('issued_stock'))['issued_stock__sum']
                                    #print('stock_issue',stock_issue)
                                #
                                    if stock_issue:
                                        stock_det_dict['issued'] = stock_issue
                                    else:
                                        stock_det_dict['issued'] = 0

                                    stock_received = \
                                        PmsExecutionStock.objects.filter(
                                            project=project, site_location=site_location,
                                            item=data['item'], uom=data['uom'], **filter).aggregate(
                                            Sum('recieved_stock'))['recieved_stock__sum']

                                    #print('stock_received',stock_received)
                                    #time.sleep(1)
                                    
                                    if stock_received:
                                        stock_det_dict['received'] = stock_received
                                    else:
                                        stock_det_dict['received'] = 0
                                    
                    
                                    stock_dict['stock_details'] = stock_det_dict
                                    stock_list.append(stock_dict)

                data['year_stock_details'] = stock_list
            return response
            

        except Exception as e:
            raise e



class ExecutionMaterialStockStatementReportDownloadView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionStock.objects.filter(is_deleted=False)
    serializer_class = ExecutionCurrentStockNewReportSerializer
    
    def get_month_dates(self, year, month) -> list:
        date_list = []
        cal = calendar.Calendar()
        for cal_date in cal.itermonthdates(year, month):
            if cal_date.month == month:
                cal_d = cal_date.strftime('%Y-%m-%d')

                date_list.append(cal_d)

        return date_list
    def get_month_value(self, month_range) -> list:
        from collections import OrderedDict
        month_list = []
        start, end = [datetime.strptime(_, "%Y-%m-%d") for _ in month_range]
        month_list = OrderedDict(
            ((start + timedelta(_)).strftime(r"%B-%Y"), None) for _ in range((end - start).days)).keys()
        return month_list

    def get_queryset(self):
        '''
            Report generate from PmsExecutionStock 
            but unique item taking from PmsExecutionUpdatedStock
        '''
        project = self.kwargs.get('project')
        site_location = self.kwargs.get('site_location')
        product_name = self.request.query_params.get('product_name',None)
        
        item_type_id = PmsExecutionPurchasesRequisitionsTypeMaster.objects.only('id').get(type_name='Materials').id
        #print('item_type_id',item_type_id)
        filter = dict()
        pk_list = list()
        queryset = self.queryset.values('item', 'uom').distinct()
        for each in queryset:
            #print('each',each)
            pk_stock_details = PmsExecutionStock.objects.filter(
                item=each['item'],uom=each['uom']).values_list('id',flat=True).order_by('-stock_date__date').first()
            pk_list.append(pk_stock_details)
        
        #print('pk_list',pk_list)
        filter['pk__in'] = pk_list

        if product_name:
            product_ids = Materials.objects.filter(name__icontains=product_name.lower()).values_list('id',flat=True)
            filter['item__in'] = product_ids
        
        queryset = PmsExecutionStock.objects.filter(project=project, site_location=site_location,type_id=item_type_id, **filter)
        return queryset
        
    def list(self, request, *args, **kwargs):
        try:
            from time import strptime
            response = super(self.__class__, self).list(self, request, args, kwargs)
            #print('response',response.data)
            response1 = response.data
            #print('response1',response1)
            data_dict = {}
            project = self.kwargs.get('project')
            site_location = self.kwargs.get('site_location')
            year = self.request.query_params.get('year', None)
            month = self.request.query_params.get('month',None)
            month_year = self.request.query_params.get('month_year',None)

            time_span = PmsProjects.objects.filter(id=project, is_deleted=False).values('start_date', 'end_date')[0]
            # print("time_span",time_span['start_date'] )
            start_date = datetime.strftime(time_span['start_date'].date(), '%Y-%m-%d')
            end_date = datetime.strftime(time_span['end_date'].date(), '%Y-%m-%d')
            month_range = [start_date, end_date]
            month_length = self.get_month_value(month_range)

            m_len_list = [x for x in month_length]
            #print("month_length", m_len_list)

            if month_year:
                m_len_list = month_year.split(',')
        
            #print("month_length", m_len_list)
            # print("start_date",start_date[0:10],"end_date",end_date[0:10])
            all_month = [('January', 1), ('February', 2), ('March', 3), ('April', 4), ('May', 5), ('June', 6), ('July', 7), ('August', 8),
                         ('September', 9), ('October', 10), ('November', 11), ('December', 12)]
            #al_yr = [('19', 2019), ('20', 2020), ('21', 2021), ('22', 2022)]
            al_yr = [('2018', 2018),('2019', 2019), ('2020', 2020), ('2021', 2021), ('2022', 2022)]

            stock_item = response1
            s_item = list(set([x['item'] for x in stock_item]))
            #print("s_item", s_item)
            stock_unit = list(set([x['uom'] for x in stock_item]))
            #print('stock_unit', stock_unit)
            data_list = list()

            for data in response1:
                data['item_details'] = {
                    'id':data['item'],
                    'name': Materials.objects.only('name').get(id=data['item']).name
                } 
                data['uom_details'] = {
                    'id':data['uom'],
                    'name': TCoreUnit.objects.only('c_name').get(id=data['uom']).c_name
                } 
                stock_list = [data['item_details']['name'] ,data['uom_details']['name']]
                for month in m_len_list:
                    month = month.split('-')
                    mm = month[0]
                    yr = month[1]
                    mm_num = strptime(mm, '%B').tm_mon
                    
                    for key, values in all_month:
                        #print('month',key)
                        if key == mm:
                            for k, v in al_yr:
                                stock_mm_list = list()
                                if k == yr:
                                    stock_dict = {
                                        'month': mm,
                                        'year': v
                                    }
                                    #print(stock_dict)
                                    found = 0

                                    date_list = self.get_month_dates(v, values)

                                    stock_det_dict = {}
                                    i_opening_stock = 0
                                    stock_opening = PmsExecutionStock.objects.filter(
                                        project=project,
                                        site_location=site_location,
                                        item=data['item'],
                                        uom=data['uom'],
                                        stock_date__month=mm_num,
                                        stock_date__year=v,
                                    ).values('id','opening_stock','closing_stock').last()
                                    #print('stock_opening',stock_opening.query,'\n\n')
                                    if stock_opening:
                                        #stock_opening = stock_opening[0]
                                        #print('stock_opening',stock_opening)
                                        #time.sleep(20)
                                        #found = 1
                                        #i_opening_stock = float(stock_opening.opening_stock)
                                        # stock_det_dict = {
                                        #     'id': stock_opening.id,
                                        #     'opening_stock': float(stock_opening.opening_stock),
                                        # }
                                        opening_stock = stock_opening['opening_stock'] if stock_opening['opening_stock'] else str(0.00)
                                        closing_stock = stock_opening['closing_stock'] if stock_opening['closing_stock'] else str(0.00)

                                        stock_list.append(opening_stock)
                                        stock_list.append(closing_stock)
                                    else:
                                        '''
                                            Set previous month closeing stock  = next month opening stock by below logic
                                        '''
                                        #print('mm_num',mm_num,type(mm_num))
                                        stock_closing = PmsExecutionStock.objects.filter(
                                            project=project,
                                            site_location=site_location,
                                            item=data['item'],
                                            uom=data['uom'],
                                            stock_date__month= mm_num - 1,
                                            stock_date__year=v,
                                        )
                                        #print('stock_closing',stock_closing)
                                        if stock_closing:
                                            stock_closing = stock_closing[0]
                                            i_closing_stock = stock_closing.closing_stock if stock_closing.closing_stock else 0
                                            if i_closing_stock == 0:
                                                #stock_det_dict['opening_stock'] = float(stock_closing.opening_stock)
                                                stock_list.append(str(stock_closing.opening_stock))
                                                stock_list.append(str(0.00))
                                            else:
                                                #stock_det_dict['opening_stock'] = float(i_closing_stock)
                                                stock_list.append(str(i_closing_stock))
                                                stock_list.append(str(0.00))
                                        else:
                                            #stock_det_dict['opening_stock'] = 0.00
                                            stock_list.append(str(0.00))
                                            stock_list.append(str(0.00))

                                    #print('stock_det_dict',stock_det_dict)

                                    filter = {}
                                    filter['stock_date__gte'] = datetime.strptime(date_list[0], "%Y-%m-%d")
                                    filter['stock_date__lte'] = datetime.strptime(date_list[-1], "%Y-%m-%d") + timedelta(days=1)
                                    

                                    stock_issue = PmsExecutionStock.objects.filter(
                                            project=project,
                                            site_location=site_location, 
                                            item=data['item'],uom=data['uom'],**filter).aggregate(
                                                Sum('issued_stock'))['issued_stock__sum']
                                    #print('stock_issue',stock_issue)
                                
                                    if stock_issue:
                                        stock_det_dict['issued'] = stock_issue
                                        stock_list.append(str(stock_issue))
                                    else:
                                        stock_det_dict['issued'] = 0
                                        stock_list.append(str(0.00))

                                    stock_received = \
                                        PmsExecutionStock.objects.filter(
                                            project=project, site_location=site_location,
                                            item=data['item'], uom=data['uom'], **filter).aggregate(
                                            Sum('recieved_stock'))['recieved_stock__sum']
                                    # # print('stock_received', stock_received)
                                    if stock_received:
                                        stock_det_dict['received'] = stock_received
                                        stock_list.append(str(stock_received))
                                    else:
                                        stock_det_dict['received'] = 0
                                        stock_list.append(str(0.00))

                                    # if stock_det_dict['received'] and stock_det_dict['issued']:
                                    #     #stock_det_dict['closing_stock'] = stock_det_dict['received']-stock_det_dict['issued']
                                    #     stock_list.append(str(stock_det_dict['received']-stock_det_dict['issued']))
                                    # else:
                                    #     #stock_det_dict['closing_stock'] =  i_opening_stock
                                    #     stock_list.append(str(i_opening_stock))

                                #print('stock_list',stock_list,len(stock_list))
                                #time.sleep(5)
                                
                data_list.append(stock_list)
                #print('data_list',len(data_list))

            '''
                Reason : Generate Excel using Multiindex
                Author : Rupam Hazra
                Date : 11-05-2020
            '''

            if os.path.isdir('media/pms/stock/document'):
                file_name = 'media/pms/stock/document/material_stock.xlsx'
                file_path = settings.MEDIA_ROOT_EXPORT + file_name
            else:
                os.makedirs('media/pms/stock/document')
                file_name = 'media/pms/stock/document/material_stock.xlsx'
                file_path = settings.MEDIA_ROOT_EXPORT + file_name

            from itertools import product
            year_cols = product(
                m_len_list,
                ['Opening Stock','Issued','Received', 'Closing Stock']
            )
            item_unit_header = product(
                [''],
                ['Item Description', 'Unit']
            )
            item_unit_cols = pd.MultiIndex.from_tuples(list(item_unit_header))
            year_columns = pd.MultiIndex.from_tuples(list(year_cols))
            
            vals =data_list
            final_df = pd.DataFrame(
                vals,columns=item_unit_cols.append(year_columns)
            )
            
            final_df.index = np.arange(1, len(final_df) + 1) # For start index 1 not 0
            export_csv = final_df.to_excel (file_path)

            if request.is_secure():
                protocol = 'https://'
            else:
                protocol = 'http://'

            url = getHostWithPort(request) + file_name if file_name else None

            if url:                    
                return Response({'request_status':1,'msg':'Found', 'url': url})
            else:
                return Response({'request_status':0,'msg':'Not Found', 'url': url})
            
        except Exception as e:
            raise e





#::::::::::::::::::::::::::::::::::::  PMS EXECUTION ACTICVE PROJECTS LIST AND REPORTS  ;::::::::::::::::::::::::::::::#
class ExecutionActiveListAndReportForExternalUserView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExternalUsersExtraDetailsTenderMapping.objects.filter(is_deleted=False)
    pagination_class = CSPageNumberPagination
    serializer_class = ExecutionActiveListAndReportForExternalUserSerializer
    def get(self, request, *args, **kwargs):
        # print("response----",response.data)
        data = {}
        typeDict={}
        dataDict = {}
        tenderData = {}
        siteData = {}
        data_dict = {}
        project_id = self.request.query_params.get('project_id')
        type_select = self.request.query_params.get('type_select')
        if project_id:
            if 1 <= PmsProjects.objects.all().count():
                try:
                    project_details = PmsProjects.objects.filter(id=project_id,is_deleted=False)
                    #print("project_id",project_details)
                    if project_details:
                        for pid in project_details:
                            data = {
                                'project_id' : pid.id,
                                'name' : pid.name,
                                'project_g_id' : pid.project_g_id
                            }
                            #print("Tender: ",pid.tender)
                            if 1<= PmsTenders.objects.all().count():
                                tenderData = {
                                    'tender_id' : pid.tender.id,
                                    'tender_g_id' : PmsTenders.objects.only('tender_g_id').get(id=str(pid.tender)).tender_g_id
                                }
                                getTenderDetails = PmsExternalUsersExtraDetailsTenderMapping.objects.filter(tender_id=pid.tender.id)
                                if getTenderDetails:
                                    # print("getTenderDetails-->",getTenderDetails)
                                    typeList = []
                                    for t_data in getTenderDetails:
                                        # print('vendor_name', t_data.external_user_type)
                                        if type_select:
                                            getType = type_select.lower()
                                            typename = t_data.external_user_type.type_name
                                            if  typename.lower() == "vendor" and type_select.lower() =="vendor":
                                                # print("-----lower------: ",typename.lower())
                                                typeDict = {
                                                    'id': t_data.external_user.id,
                                                    'code': t_data.external_user.code,
                                                    'name': t_data.external_user.organisation_name,
                                                    'contact_person_name' : t_data.external_user.contact_person_name
                                                    
                                                }
                                                typeList.append(typeDict)
                                            elif typename.lower() == "contractor" and type_select.lower() =="contractor":
                                                typeDict = {
                                                    'id': t_data.external_user.id,
                                                    'code': t_data.external_user.code,
                                                    'name': t_data.external_user.organisation_name,
                                                    'contact_person_name': t_data.external_user.contact_person_name
                                                }
                                                typeList.append(typeDict)
                                            elif typename.lower() == "crusher" and type_select.lower() =="crusher":
                                                typeDict = {
                                                    'id': t_data.external_user.id,
                                                    'code': t_data.external_user.code,
                                                    'name': t_data.external_user.organisation_name,
                                                    'contact_person_name': t_data.external_user.contact_person_name
                                                }
                                                typeList.append(typeDict)
                                            elif typename.lower() == "partner" and type_select.lower() =="partner":
                                                typeDict = {
                                                    'id': t_data.external_user.id,
                                                    'code': t_data.external_user.code,
                                                    'name': t_data.external_user.organisation_name,
                                                    'contact_person_name': t_data.external_user.contact_person_name
                                                }
                                                typeList.append(typeDict)
                                        else:
                                            getType = 'user_type'
                                            typeDict = {
                                                'id': t_data.external_user.id,
                                                'code': t_data.external_user.code,
                                                'name': t_data.external_user.organisation_name,
                                                'contact_person_name': t_data.external_user.contact_person_name
                                            }
                                            typeList.append(typeDict)

                                    tenderData['external_user_details'] = typeList
                                else:
                                    tenderData['external_user_details'] = []

                            else:
                                tenderData['partner'] = []
                            if 1 <= PmsSiteProjectSiteManagement.objects.all().count():
                                siteData = {
                                    'site_localtion_id' : pid.site_location.id,
                                    'site_location_name' : PmsSiteProjectSiteManagement.objects.only('name').get(id=pid.site_location.id).name
                                }
                            else:
                                siteData = {}
                        data ['tender']= tenderData
                        data['site_location'] = siteData
                    else:
                        tenderData['partner'] = []
                except Exception as e:
                    raise e
            else:
                data = {}
        else:
            data = {}
        
        data_dict['result'] = data
        if data:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_SUCCESS
        elif len(data) == 0:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_NO_DATA
        else:
            data_dict['request_status'] = 0
            data_dict['msg'] = settings.MSG_ERROR
        data = data_dict
        return Response(data)

class ExecutionActiveListAndReportOfPartnerView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsTenderPartners.objects.filter(is_deleted=False)
    serializer_class = ExecutionActiveListAndReportOfPartnerSerializer
    def get(self, request, *args, **kwargs):
        data = {}
        tenderData = {}
        siteData = {}
        parnerDict = {}
        data_dict = {}
        project_id = self.request.query_params.get('project_id')
        #print("project_id", project_id)

        if project_id:
            if 1 <= PmsProjects.objects.all().count():
                try:
                    project_details = PmsProjects.objects.filter(id=project_id,is_deleted=False)
                    #print("project_id",project_details)
                    if project_details:
                        for pid in project_details:
                            data = {
                                'project_id' : pid.id,
                                'name' : pid.name,
                                'project_g_id' : pid.project_g_id
                            }
                            #print("Tender: ",pid.tender)
                            if 1<= PmsTenders.objects.all().count():
                                tenderData = {
                                    'tender_id' : pid.tender.id,
                                    'tender_g_id' : PmsTenders.objects.only('tender_g_id').get(id=str(pid.tender)).tender_g_id
                                }
                                parnerList = []
                                getpartnerDetails = PmsTenderPartners.objects.filter(tender_id=pid.tender,is_deleted=False)
                                if getpartnerDetails:
                                    #print("getpartnerDetails-->", getpartnerDetails)
                                    for partner in getpartnerDetails:
                                        parnerDict = {
                                            'partner_id' : partner.id,
                                            'name' : partner.name,
                                            'contact' : partner.contact,
                                            'address' : partner.address,
                                        }
                                        parnerList.append(parnerDict)
                                    tenderData['partner'] = parnerList
                                    # print("tenderData:--->",tenderData)
                                else:
                                    tenderData['partner'] = []
                            else:
                                tenderData['partner'] = []
                            if 1 <= PmsSiteProjectSiteManagement.objects.all().count():
                                siteData = {
                                    'site_localtion_id' : pid.site_location.id,
                                    'site_location_name' : PmsSiteProjectSiteManagement.objects.only('name').get(id=pid.site_location.id).name
                                }
                            else:
                                siteData = {}
                        data ['tender']= tenderData
                        data['site_location'] = siteData
                    else:
                        tenderData['partner'] = []
                except Exception as e:
                    raise e
            else:
                data = {}  
        else:
            data = {}                
        data_dict['result'] = data
        if data:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_SUCCESS
        elif len(data) == 0:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_NO_DATA
        else:
            data_dict['request_status'] = 0
            data_dict['msg'] = settings.MSG_ERROR
        data = data_dict
        return Response(data)


class PurchasesRequisitionsTypeToItemCodeStockListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesRequisitionsTypeMaster.objects.filter(is_deleted=False)
    serializer_class = PurchasesRequisitionsTypeToItemCodeListSerializer

    def get(self, request, *args, **kwargs):
        data = {}
        data_dict = {}
        type_code = self.request.query_params.get('type_code')
        project = self.request.query_params.get('project')
        site_location = self.request.query_params.get('site_location')
        # unit = self.request.query_params.get('unit')
        item_code = self.request.query_params.get('item_code')
        item_list = []
        if type_code :
            type_name = PmsExecutionPurchasesRequisitionsTypeMaster.objects.only('type_name').get(
                code=type_code).type_name
            type_id=PmsExecutionPurchasesRequisitionsTypeMaster.objects.only('id').get(code=type_code).id
            if type_name.lower() == "materials":
                material_details_stock = PmsExecutionStock.objects.filter(
                    is_deleted=False,project=project,site_location=site_location,type=type_id).values('item')
                mat_list=list(set([x['item'] for x in material_details_stock]))


                material_details = Materials.objects.filter(id__in=mat_list,is_deleted=False)
                for details in material_details:
                    data_mat = {
                        'id': details.id,
                        'name': details.name,
                        'code': details.mat_code,
                        'description': details.description
                    }
                    item_list.append(data_mat)
                    getUnitDetails = MaterialsUnitMapping.objects.filter(
                        material=details.id)
                    #print(getUnitDetails)
                    unit_list = list()
                    for unitDetails in getUnitDetails:
                        # print(unitDetails.unit.c_name)
                        unit_dict = {
                            'id': unitDetails.unit.id,
                            'unit': unitDetails.unit.c_name
                        }
                        '''
                            Modified After implementation of CRON functionlaity
                            Author : Rupam Hazra
                            Date : 06.05.2020
                        '''
                        stock_item=PmsExecutionStock.objects.filter(
                                    project=project, 
                                    site_location=site_location, 
                                    type=type_id, 
                                    uom=unit_dict['id'],
                                    item=details.id
                                    ).values('closing_stock').order_by('-stock_date').first()

                        if stock_item:
                            unit_dict['current_stock']=stock_item['closing_stock'] if stock_item['closing_stock'] else 0
                        else:
                            unit_dict['current_stock']= float(0.00)
                        # print(unit_dict)
                        unit_list.append(unit_dict)
                        # print(unit_list)
                    data_mat['unit'] = unit_list
            if type_name.lower() == "machinery":
                # print('Material')
                machinery_details_stock = PmsExecutionUpdatedStock.objects.filter(is_deleted=False,project=project,site_location=site_location,type=type_id).values('item')
                mach_list=list(set([x['item'] for x in machinery_details_stock]))
                machineries_details = PmsMachineries.objects.filter(is_deleted=False,id__in=mach_list)
                #machine_list = list()
                for m_details in machineries_details:
                    data_machine = {
                        'id': m_details.id,
                        'description':'',
                        'code': m_details.code,
                        'name': m_details.equipment_name,
                    }
                    item_list.append(data_machine)
            
                #data['Machinery'] = machine_list
        data_dict['result'] = item_list
        if item_list:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_SUCCESS
        elif len(item_list) == 0:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_NO_DATA
        else:
            data_dict['request_status'] = 0
            data_dict['msg'] = settings.MSG_ERROR
        data = data_dict
        # return data

        return Response(data)

class ClosingStockExcelFileAddView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
 
    @response_modify_decorator_post  
    def post(self, request, format=None):
        try:
            document = request.data['document']
            # print('document',document)
            data=pd.read_excel(document,converters={'Material':str})
            data = data.replace(np.nan,'',regex=True) 
            # print('data',data)          
            logdin_user_id = self.request.user.id
            total_result={}
            blank_mat_code_list=[]
            with transaction.atomic():
                for index,row in data.iterrows():
                    unit_filter={}
                    type_id=None
                    #print('row',row['Material'],index)
                    if row['Material'] == '':
                        blank_mat_code_dict={
                            'material_code':row['Material'],
                            'description':row['Material description'],
                            'unit':row['Bun'],
                            'opening_stock':row['Closing Stock']
                        }
                        blank_mat_code_list.append(blank_mat_code_dict)
                    else:
                        if row['Bun']:
                            unit_det=TCoreUnit.objects.filter(c_name=(row['Bun']).lower(),c_is_deleted=False)
                            if unit_det:
                                for det in unit_det:
                                    unit_filter['uom_id']=det.id
                        else:
                            unit_filter['uom_id']=None

                        if row['Material']:
                            material_det=Materials.objects.filter(mat_code=row['Material'],is_deleted=False)
                            if material_det:
                                for mat in material_det:
                                    unit_filter['item']=mat.id
                                    type_code=mat.type_code
                                    requisition_type=PmsExecutionPurchasesRequisitionsTypeMaster.objects.filter(code=type_code,is_deleted=False).values('id')
                                    type_id=requisition_type[0]['id']
                                                        
                                existing_stock_date_with_item_and_uom=PmsExecutionStock.objects.filter(**unit_filter,stock_date__date='2019-12-31',is_deleted=False).count()
                                #print('existing_stock_date_with_item_and_uom',existing_stock_date_with_item_and_uom)
                                if existing_stock_date_with_item_and_uom == 0:
                                    material_unit_mapping=PmsExecutionStock.objects.create(**unit_filter,
                                                                                            type_id=type_id,
                                                                                            project_id=16,
                                                                                            site_location_id=11,
                                                                                            opening_stock=row['Closing Stock'],
                                                                                            issued_stock = 0.00,
                                                                                            recieved_stock = 0.00,
                                                                                            closing_stock = 0.00,
                                                                                            created_by_id=logdin_user_id,
                                                                                            owned_by_id=logdin_user_id
                                                                                            )

                                # Added By Rupam Hazra
                                existing_stock_date_with_item_and_uom_u=PmsExecutionUpdatedStock.objects.filter(**unit_filter,stock_date__date='2019-12-31',is_deleted=False).count()
                                #print('existing_stock_date_with_item_and_uom',existing_stock_date_with_item_and_uom)
                                if existing_stock_date_with_item_and_uom_u == 0:
                                    material_unit_mapping_u=PmsExecutionUpdatedStock.objects.create(**unit_filter,
                                                                                            type_id=type_id,
                                                                                            project_id=16,
                                                                                            site_location_id=11,
                                                                                            opening_stock=row['Closing Stock'],
                                                                                            issued_stock = 0.00,
                                                                                            recieved_stock = 0.00,
                                                                                            closing_stock = 0.00,
                                                                                            created_by_id=logdin_user_id,
                                                                                            owned_by_id=logdin_user_id
                                                                                            )

                        total_result['blank_material_code_list']=blank_mat_code_list  

                return Response(total_result)
        except Exception as e:
            raise APIException({'msg':settings.MSG_ERROR,
                                'error':e,
                                "request_status": 0
                                })

class MatlaClosingStockExcelFileAddView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
 
    @response_modify_decorator_post  
    def post(self, request, format=None):
        try:
            document = request.data['document']
            # print('document',document)
            data=pd.read_excel(document,converters={'Material':str})
            data = data.replace(np.nan,'',regex=True) 
            # print('data',data)          
            logdin_user_id = self.request.user.id
            total_result={}
            blank_mat_code_list=[]
            with transaction.atomic():
                for index, row in data.iterrows():
                    unit_filter={}
                    type_id=None
                    #print('row',row['Bun'])
                    if row['Material'] == '':
                        blank_mat_code_dict={
                            'material_code':row['Material'],
                            'description':row['Material description'],
                            'unit':row['Bun'],
                            'opening_stock':row['Closing Stock']
                        }
                        blank_mat_code_list.append(blank_mat_code_dict)
                    else:
                        if row['Bun']:
                            unit_det=TCoreUnit.objects.filter(c_name=(row['Bun']).lower(),c_is_deleted=False)
                            if unit_det:
                                for det in unit_det:
                                    unit_filter['uom_id']=det.id
                        else:
                            unit_filter['uom_id']=None

                        if row['Material']:
                            material_det=Materials.objects.filter(mat_code=row['Material'],is_deleted=False)
                            if material_det:
                                for mat in material_det:
                                    unit_filter['item']=mat.id
                                    type_code=mat.type_code
                                    requisition_type=PmsExecutionPurchasesRequisitionsTypeMaster.objects.filter(code=type_code,is_deleted=False).values('id')
                                    type_id=requisition_type[0]['id']
                                               
                                existing_stock_date_with_item_and_uom=PmsExecutionStock.objects.filter(**unit_filter,stock_date__date='2019-12-31',is_deleted=False).count()
                                #print('existing_stock_date_with_item_and_uom',existing_stock_date_with_item_and_uom)
                                if existing_stock_date_with_item_and_uom == 0:
                                    material_unit_mapping=PmsExecutionStock.objects.create(**unit_filter,
                                                                                            project_id=1,
                                                                                            type_id=type_id,
                                                                                            site_location_id=1,
                                                                                            opening_stock=row['Closing Stock'],
                                                                                            issued_stock = 0.00,
                                                                                            recieved_stock = 0.00,
                                                                                            closing_stock = 0.00,
                                                                                            created_by_id=logdin_user_id,
                                                                                            owned_by_id=logdin_user_id
                                                                                            )

                                # Added By Rupam Hazra
                                existing_stock_date_with_item_and_uom_u=PmsExecutionUpdatedStock.objects.filter(**unit_filter,stock_date__date='2019-12-31',is_deleted=False).count()
                                #print('existing_stock_date_with_item_and_uom',existing_stock_date_with_item_and_uom)
                                if existing_stock_date_with_item_and_uom_u == 0:
                                    material_unit_mapping_u=PmsExecutionUpdatedStock.objects.create(**unit_filter,
                                                                                            project_id=1,
                                                                                            site_location_id=1,
                                                                                            type_id=type_id,
                                                                                            opening_stock=row['Closing Stock'],
                                                                                            issued_stock = 0.00,
                                                                                            recieved_stock = 0.00,
                                                                                            closing_stock = 0.00,
                                                                                            created_by_id=logdin_user_id,
                                                                                            owned_by_id=logdin_user_id
                                                                                            )

                        total_result['blank_material_code_list']=blank_mat_code_list  

                return Response(total_result)
        except Exception as e:
            raise APIException({'msg':settings.MSG_ERROR,
                                'error':e,
                                "request_status": 0
                                })

class MejiaClosingStockExcelFileAddView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
 
    @response_modify_decorator_post  
    def post(self, request, format=None):
        try:
            document = request.data['document']
            # print('document',document)
            data=pd.read_excel(document,converters={'Material':str})
            data = data.replace(np.nan,'',regex=True) 
            # print('data',data)
            logdin_user_id = self.request.user.id
            total_result={}
            blank_mat_code_list=[]
            with transaction.atomic():
                for index, row in data.iterrows():
                    unit_filter={}
                    type_id=None
                    #print('row',row['Bun'])
                    if row['Material'] == '':
                        blank_mat_code_dict={
                            'material_code':row['Material'],
                            'description':row['Material description'],
                            'unit':row['Bun'],
                            'opening_stock':row['Closing Stock']
                        }
                        blank_mat_code_list.append(blank_mat_code_dict)
                    else:
                        if row['Bun']:
                            unit_det=TCoreUnit.objects.filter(c_name=(row['Bun']).lower(),c_is_deleted=False)
                            if unit_det:
                                for det in unit_det:
                                    unit_filter['uom_id']=det.id
                        else:
                            unit_filter['uom_id']=None

                        if row['Material']:
                            material_det=Materials.objects.filter(mat_code=row['Material'],is_deleted=False)
                            if material_det:
                                for mat in material_det:
                                    unit_filter['item']=mat.id
                                    type_code=mat.type_code
                                    requisition_type=PmsExecutionPurchasesRequisitionsTypeMaster.objects.filter(code=type_code,is_deleted=False).values('id')
                                    type_id=requisition_type[0]['id']
                                                   
                                existing_stock_date_with_item_and_uom=PmsExecutionStock.objects.filter(**unit_filter,stock_date__date='2019-12-31',is_deleted=False).count()
                                #print('existing_stock_date_with_item_and_uom',existing_stock_date_with_item_and_uom)
                                if existing_stock_date_with_item_and_uom == 0:
                                    material_unit_mapping=PmsExecutionStock.objects.create(**unit_filter,
                                                                                            project_id=19,
                                                                                            type_id=type_id,
                                                                                            site_location_id=18,
                                                                                            opening_stock=row['Closing Stock'],
                                                                                            issued_stock = 0.00,
                                                                                            recieved_stock = 0.00,
                                                                                            closing_stock = 0.00,
                                                                                            created_by_id=logdin_user_id,
                                                                                            owned_by_id=logdin_user_id
                                                                                            )

                                # Added By Rupam Hazra
                                existing_stock_date_with_item_and_uom_u=PmsExecutionUpdatedStock.objects.filter(**unit_filter,stock_date__date='2019-12-31',is_deleted=False).count()
                                #print('existing_stock_date_with_item_and_uom',existing_stock_date_with_item_and_uom)
                                if existing_stock_date_with_item_and_uom_u == 0:
                                    material_unit_mapping_u=PmsExecutionUpdatedStock.objects.create(**unit_filter,
                                                                                            type_id=type_id,
                                                                                            project_id=19,
                                                                                            site_location_id=18,
                                                                                            opening_stock=row['Closing Stock'],
                                                                                            issued_stock = 0.00,
                                                                                            recieved_stock = 0.00,
                                                                                            closing_stock = 0.00,
                                                                                            created_by_id=logdin_user_id,
                                                                                            owned_by_id=logdin_user_id
                                                                                            )

                        total_result['blank_material_code_list']=blank_mat_code_list  

                return Response(total_result)
        except Exception as e:
            raise APIException({'msg':settings.MSG_ERROR,
                                'error':e,
                                "request_status": 0
                                })

class OctagonClosingStockExcelFileAddView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
 
    @response_modify_decorator_post  
    def post(self, request, format=None):
        try:
            document = request.data['document']
            # print('document',document)
            data=pd.read_excel(document,converters={'Material':str})
            data = data.replace(np.nan,'',regex=True) 
            # print('data',data)
            logdin_user_id = self.request.user.id
            total_result={}
            blank_mat_code_list=[]
            with transaction.atomic():
                for index, row in data.iterrows():
                    unit_filter={}
                    type_id=None
                    #print('row',row['Bun'])
                    if row['Material'] == '':
                        blank_mat_code_dict={
                            'material_code':row['Material'],
                            'description':row['Material description'],
                            'unit':row['Bun'],
                            'opening_stock':row['Closing Stock']
                        }
                        blank_mat_code_list.append(blank_mat_code_dict)
                    else:
                        if row['Bun']:
                            unit_det=TCoreUnit.objects.filter(c_name=(row['Bun']).lower(),c_is_deleted=False)
                            if unit_det:
                                for det in unit_det:
                                    unit_filter['uom_id']=det.id
                        else:
                            unit_filter['uom_id']=None

                        if row['Material']:
                            material_det=Materials.objects.filter(mat_code=row['Material'],is_deleted=False)
                            if material_det:
                                for mat in material_det:
                                    unit_filter['item']=mat.id
                                    type_code=mat.type_code
                                    requisition_type=PmsExecutionPurchasesRequisitionsTypeMaster.objects.filter(code=type_code,is_deleted=False).values('id')
                                    type_id=requisition_type[0]['id']
                                                   
                                existing_stock_date_with_item_and_uom=PmsExecutionStock.objects.filter(**unit_filter,stock_date__date='2019-12-31',is_deleted=False).count()
                                #print('existing_stock_date_with_item_and_uom',existing_stock_date_with_item_and_uom)
                                if existing_stock_date_with_item_and_uom == 0:
                                    material_unit_mapping=PmsExecutionStock.objects.create(**unit_filter,
                                                                                            type_id=type_id,
                                                                                            project_id=17,
                                                                                            site_location_id=16,
                                                                                            opening_stock=row['Closing Stock'],
                                                                                            issued_stock = 0.00,
                                                                                            recieved_stock = 0.00,
                                                                                            closing_stock = 0.00,
                                                                                            created_by_id=logdin_user_id,
                                                                                            owned_by_id=logdin_user_id
                                                                                            )

                                # Added By Rupam Hazra
                                existing_stock_date_with_item_and_uom_u=PmsExecutionUpdatedStock.objects.filter(**unit_filter,stock_date__date='2019-12-31',is_deleted=False).count()
                                #print('existing_stock_date_with_item_and_uom',existing_stock_date_with_item_and_uom)
                                if existing_stock_date_with_item_and_uom_u == 0:
                                    material_unit_mapping_u=PmsExecutionUpdatedStock.objects.create(**unit_filter,
                                                                                            type_id=type_id,
                                                                                            project_id=17,
                                                                                            site_location_id=16,
                                                                                            opening_stock=row['Closing Stock'],
                                                                                            issued_stock = 0.00,
                                                                                            recieved_stock = 0.00,
                                                                                            closing_stock = 0.00,
                                                                                            created_by_id=logdin_user_id,
                                                                                            owned_by_id=logdin_user_id
                                                                                            )

                        total_result['blank_material_code_list']=blank_mat_code_list  

                return Response(total_result)
        except Exception as e:
            raise APIException({'msg':settings.MSG_ERROR,
                                'error':e,
                                "request_status": 0
                                })

class RajkharsawanClosingStockExcelFileAddView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
 
    @response_modify_decorator_post  
    def post(self, request, format=None):
        try:
            document = request.data['document']
            # print('document',document)
            data=pd.read_excel(document,converters={'Material':str})
            data = data.replace(np.nan,'',regex=True) 
            # print('data',data)           
            logdin_user_id = self.request.user.id
            total_result={}
            blank_mat_code_list=[]
            with transaction.atomic():
                for index, row in data.iterrows():
                    unit_filter={}
                    type_id=None
                    #print('row',row['Bun'])
                    if row['Material'] == '':
                        blank_mat_code_dict={
                            'material_code':row['Material'],
                            'description':row['Material description'],
                            'unit':row['Bun'],
                            'opening_stock':row['Closing Stock']
                        }
                        blank_mat_code_list.append(blank_mat_code_dict)
                    else:
                        if row['Bun']:
                            unit_det=TCoreUnit.objects.filter(c_name=(row['Bun']).lower(),c_is_deleted=False)
                            if unit_det:
                                for det in unit_det:
                                    unit_filter['uom_id']=det.id
                        else:
                            unit_filter['uom_id']=None

                        if row['Material']:
                            material_det=Materials.objects.filter(mat_code=row['Material'],is_deleted=False)
                            if material_det:
                                for mat in material_det:
                                    unit_filter['item']=mat.id
                                    type_code=mat.type_code
                                    requisition_type=PmsExecutionPurchasesRequisitionsTypeMaster.objects.filter(code=type_code,is_deleted=False).values('id')
                                    type_id=requisition_type[0]['id']
                                                   
                                existing_stock_date_with_item_and_uom=PmsExecutionStock.objects.filter(**unit_filter,stock_date__date='2019-12-31',is_deleted=False).count()
                                #print('existing_stock_date_with_item_and_uom',existing_stock_date_with_item_and_uom)
                                if existing_stock_date_with_item_and_uom == 0:
                                    material_unit_mapping=PmsExecutionStock.objects.create(**unit_filter,
                                                                                            type_id=type_id,
                                                                                            project_id=14,
                                                                                            site_location_id=12,
                                                                                            opening_stock=row['Closing Stock'],
                                                                                            issued_stock = 0.00,
                                                                                            recieved_stock = 0.00,
                                                                                            closing_stock = 0.00,
                                                                                            created_by_id=logdin_user_id,
                                                                                            owned_by_id=logdin_user_id
                                                                                            )

                                # Added By Rupam Hazra
                                existing_stock_date_with_item_and_uom_u=PmsExecutionUpdatedStock.objects.filter(**unit_filter,stock_date__date='2019-12-31',is_deleted=False).count()
                                #print('existing_stock_date_with_item_and_uom',existing_stock_date_with_item_and_uom)
                                if existing_stock_date_with_item_and_uom_u == 0:
                                    material_unit_mapping_u=PmsExecutionUpdatedStock.objects.create(**unit_filter,
                                                                                            type_id=type_id,
                                                                                            project_id=14,
                                                                                            site_location_id=12,
                                                                                            opening_stock=row['Closing Stock'],
                                                                                            issued_stock = 0.00,
                                                                                            recieved_stock = 0.00,
                                                                                            closing_stock = 0.00,
                                                                                            created_by_id=logdin_user_id,
                                                                                            owned_by_id=logdin_user_id
                                                                                            )

                        total_result['blank_material_code_list']=blank_mat_code_list  

                return Response(total_result)
        except Exception as e:
            raise APIException({'msg':settings.MSG_ERROR,
                                'error':e,
                                "request_status": 0
                                })
class KharagpurClosingStockExcelFileAddView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
 
    @response_modify_decorator_post  
    def post(self, request, format=None):
        try:
            document = request.data['document']
            #print('document',document)
            data=pd.read_excel(document,converters={'Material':str})
            data = data.replace(np.nan,'',regex=True) 
            #print('data',data)           
            logdin_user_id = self.request.user.id
            total_result={}
            blank_mat_code_list=[]
            with transaction.atomic():
                for index, row in data.iterrows():
                    unit_filter={}
                    type_id=None
                    #print('row',row)
                    if row['Material'] == '':
                        blank_mat_code_dict={
                            'material_code':row['Material'],
                            'description':row['Material description'],
                            'unit':row['Bun'],
                            'opening_stock':row['Closing Stock']
                        }
                        blank_mat_code_list.append(blank_mat_code_dict)
                    else:
                        if row['Bun']:
                            unit_det=TCoreUnit.objects.filter(c_name=(row['Bun']).lower(),c_is_deleted=False)
                            if unit_det:
                                for det in unit_det:
                                    unit_filter['uom_id']=det.id
                        else:
                            unit_filter['uom_id']=None

                        if row['Material']:
                            material_det=Materials.objects.filter(mat_code=row['Material'],is_deleted=False)
                            if material_det:
                                for mat in material_det:
                                    unit_filter['item']=mat.id
                                    type_code=mat.type_code
                                    requisition_type=PmsExecutionPurchasesRequisitionsTypeMaster.objects.filter(code=type_code,is_deleted=False).values('id')
                                    type_id=requisition_type[0]['id']
                                                   
                                existing_stock_date_with_item_and_uom=PmsExecutionStock.objects.filter(**unit_filter,stock_date__date='2020-02-19',is_deleted=False).count()
                                #print('existing_stock_date_with_item_and_uom',existing_stock_date_with_item_and_uom)
                                if existing_stock_date_with_item_and_uom == 0:
                                    material_unit_mapping=PmsExecutionStock.objects.create(**unit_filter,
                                                                                            type_id=type_id,
                                                                                            project_id=20,
                                                                                            site_location_id=13,
                                                                                            opening_stock=row['Closing Stock'],
                                                                                            issued_stock = 0.00,
                                                                                            recieved_stock = 0.00,
                                                                                            closing_stock = 0.00,
                                                                                            created_by_id=logdin_user_id,
                                                                                            owned_by_id=logdin_user_id
                                                                                            )

                                existing_stock_date_with_item_and_uom_u=PmsExecutionUpdatedStock.objects.filter(**unit_filter,stock_date__date='2020-02-20',is_deleted=False).count()
                                #print('existing_stock_date_with_item_and_uom',existing_stock_date_with_item_and_uom)
                                if existing_stock_date_with_item_and_uom_u == 0:
                                    material_unit_mapping_u=PmsExecutionUpdatedStock.objects.create(**unit_filter,
                                                                                            type_id=type_id,
                                                                                            project_id=20,
                                                                                            site_location_id=13,
                                                                                            opening_stock=row['Closing Stock'],
                                                                                            issued_stock = 0.00,
                                                                                            recieved_stock = 0.00,
                                                                                            closing_stock = 0.00,
                                                                                            created_by_id=logdin_user_id,
                                                                                            owned_by_id=logdin_user_id
                                                                                            )

                        total_result['blank_material_code_list']=blank_mat_code_list  

                return Response(total_result)
        except Exception as e:
            # raise e
            raise APIException({'msg':settings.MSG_ERROR,
                                'error':e,
                                "request_status": 0
                                })


class PmsExecutionDailyClosingStockUpdateOnEverydayView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionStock.objects.all()

    def post(self, request, *args, **kwargs):
        #print('request',request.data)
        
        current_date_time = datetime.now()
        if request.data:
            input_date = self.request.data['date']
            month = self.request.data['month']
            if input_date:
                input_date = datetime.strptime(input_date, "%Y-%m-%d")
                current_date_time = input_date

        #print('current_date_time',current_date_time)
        queryset_stocks = PmsExecutionStock.objects.filter(
            stock_date__date = current_date_time.date(),
            is_deleted = False
        )
        #print('queryset_stocks',queryset_stocks)
        for each_stock in queryset_stocks:
            o_stock = each_stock.opening_stock if each_stock.opening_stock else 0
            r_stock = each_stock.recieved_stock if each_stock.recieved_stock else 0
            i_stock = each_stock.issued_stock if each_stock.issued_stock else 0
            c_stock =  (o_stock + r_stock) - i_stock
            #print('queryset_stocks',c_stock)
            PmsExecutionStock.objects.filter(pk=each_stock.id).update(
                closing_stock = c_stock,
                updated_by_id = self.request.user.id
            )

        return Response({'result':queryset_stocks.values()})
        

class PmsExecutionDailyClosingStockUpdateOnMonthView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionStock.objects.all()

    def post(self, request, *args, **kwargs):
        #print('request',request.data)
        if request.data:
            year = self.request.data['year']
            month = self.request.data['month']
            if year and month:
                queryset_stocks = PmsExecutionStock.objects.filter(
                    stock_date__year = year,
                    stock_date__month = month,
                    is_deleted = False
                )
                #print('queryset_stocks',queryset_stocks)
                for each_stock in queryset_stocks:
                    o_stock = each_stock.opening_stock if each_stock.opening_stock else 0
                    r_stock = each_stock.recieved_stock if each_stock.recieved_stock else 0
                    i_stock = each_stock.issued_stock if each_stock.issued_stock else 0
                    c_stock =  (o_stock + r_stock) - i_stock
                    #print('queryset_stocks',c_stock)
                    PmsExecutionStock.objects.filter(pk=each_stock.id).update(
                        closing_stock = c_stock,
                        updated_by_id = self.request.user.id
                    )

                return Response({'result':queryset_stocks.values()})


## Change Request PMS Daily [Modifications Required in PMS System] | Date : 25-06-2020 | Rupam Hazra ##

class ExecutionDailyReportProgressCommonDataView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionDailyProgress.objects.filter(is_deleted=False).order_by('-id')
    serializer_class = ExecutionDailyReportProgressEntryDataSerializer

    def get_queryset(self):
        project_id = self.kwargs["project_id"]
        site_id = self.kwargs["site_id"]
        filter = {}
        date = self.request.query_params.get('date', None)
        report_type = int(self.request.query_params.get('report_type', None))

        if date is not None:
            date_object = datetime.strptime(date, '%Y-%m-%d').date()
            filter['date_entry__year'] = date_object.year
            filter['date_entry__month'] = date_object.month
            filter['date_entry__day'] = date_object.day
            queryset = self.queryset.filter(project_id=project_id, site_location=site_id,type_of_report=report_type, **filter)
        return queryset

    @response_modify_decorator_get_single
    def get(self, request, *args, **kwargs):
        response = super(self.__class__, self).get(self, request, args, kwargs)
        return response


## Change Request PMS Daily [Modifications Required in PMS System] | Date : 25-06-2020 | Rupam Hazra ##


## Add a box in MR format on PMS | Date : 30-06-2020 | Rupam Hazra ##

# class PurchaseRequisitionsTotalListDownloadView(generics.ListAPIView):
#     permission_classes = [IsAuthenticated]
#     authentication_classes = [TokenAuthentication]
#     queryset = PmsExecutionPurchasesRequisitionsMaster.objects.filter(is_deleted=False).order_by('-mr_date')
#     serializer_class = PurchaseRequisitionsTotalListSerializer


#     def get_queryset(self):
#         filter = {}
#         start_date = self.request.query_params.get('start_date', None)
#         end_date = self.request.query_params.get('end_date', None)
#         site_location = self.request.query_params.get('site_location', None)
#         type_id = self.request.query_params.get('type_id', None)
#         search = self.request.query_params.get('search', None)
#         field_name = self.request.query_params.get('field_name', None)
#         order_by = self.request.query_params.get('order_by', None)
#         item_type = self.request.query_params.get('item_type', None)
#         # item = self.request.query_params.get('item', None)

#         if field_name and order_by:

#             if field_name == 'project' and order_by == 'asc':
#                 return self.queryset.filter(is_deleted=False).order_by('project__id')
#             elif field_name == 'project' and order_by == 'desc':
#                 return self.queryset.filter(is_deleted=False).order_by('-project__id')

#             elif field_name == 'site_location' and order_by == 'asc':
#                 return self.queryset.filter(status=True, is_deleted=False).order_by('site_location__id')
#             elif field_name == 'site_location' and order_by == 'desc':
#                 return self.queryset.filter(status=True, is_deleted=False).order_by('-site_location__id')

#             elif field_name == 'mr_date' and order_by == 'asc':
#                 return self.queryset.filter(status=True, is_deleted=False).order_by('mr_date')
#             elif field_name == 'mr_date' and order_by == 'desc':
#                 return self.queryset.filter(status=True, is_deleted=False).order_by('-mr_date')

#             elif field_name == 'item' and order_by == 'asc':
#                 return self.queryset.filter(status=True, is_deleted=False).order_by('item')
#             elif field_name == 'item' and order_by == 'desc':
#                 return self.queryset.filter(status=True, is_deleted=False).order_by('-item')

#         if search :
#             #print("This is if condition entry")
#             queryset = self.queryset.filter(project__project_g_id=search)
#             # print('queryset', queryset.query)
#             return queryset

#         if start_date and end_date:
#             start_object = datetime.strptime(start_date,'%Y-%m-%d').date()
#             end_object = datetime.strptime(end_date, '%Y-%m-%d').date()
#             filter['mr_date__date__range'] = (start_object, end_object)

#         if site_location:
#             filter['site_location__in']=site_location.split(",")

#         if type_id:
#             filter['type__in'] = type_id.split(",")

#         if filter:
#             queryset = self.queryset.filter(**filter)
#             # print('queryset',queryset)
#             return queryset

#         else:
#             queryset = self.queryset.filter(is_deleted=False)
#             return queryset


#     def get(self, request, *args, **kwargs):
#         response = super(PurchaseRequisitionsTotalListDownloadView, self).get(self, request, args, kwargs)
#         #print('response',response.data)
#         reqMasterLisr = []
#         data_dict = dict()
#         data_list = list()
#         data_list1 = list()
#         for data in response.data:
#             project_details = PmsProjects.objects.filter(id=data['project']).values('project_g_id','id')
#             type_details = PmsExecutionPurchasesRequisitionsTypeMaster.objects.filter(id=data['type']).values(
#                 'type_name','code','id')
#             site_location_details = PmsSiteProjectSiteManagement.objects.filter(id=data['site_location']).values(
#                 'name','id')

#             data['type'] = type_details[0]['type_name']
#             data['type_code'] = type_details[0]['code']
#             data['project'] = project_details[0]['project_g_id']
#             data['site_location'] = site_location_details[0]['name']

#             reqDetails = PmsExecutionPurchasesRequisitions.objects.filter(
#                 requisitions_master=data['id'],
#                 is_deleted=False)

#             reqList = []
#             item_code = list()
#             project_id = list()
#             data_list1 = list()
#             for reqData in reqDetails:
#                 req_dict = {
#                     'quantity': reqData.quantity,
#                 }
#                 req_dict['uom'] = reqData.uom.c_name if reqData.uom else ''
#                 material_details = Materials.objects.filter(id=reqData.item)
#                 if material_details:
#                     material_details = material_details[0]
#                 else:
#                     material_details = None
    
#                 data_list.append([data['project'],data['site_location'],data['mr_date'][0:10],data['get_status_display'],data['type'],material_details.description,material_details.mat_code,req_dict['uom'],req_dict['quantity']])
                
#         file_name = ''
#         if data_list:
#             if os.path.isdir('media/pms/requisitions/document'):
#                 file_name = 'media/pms/requisitions/document/pms_requisitions_report.xlsx'
#             else:
#                 os.makedirs('media/pms/requisitions/document')
#                 file_name = 'media/pms/requisitions/document/pms_requisitions_report.xlsx'

#             index = pd.MultiIndex.from_tuples(data_list, names=['Project Id','Site Location','M.R. Date','Status','Type','Item Description','Item Code','UOM','Quantity'])
#             final_df = pd.DataFrame(data_list,index=index)
#             final_df.drop(final_df.columns[[0,1,2,3,4,5,6,7,8]],axis = 1, inplace = True)
#             export_csv = final_df.to_excel (file_name,header=True)
            
#             if request.is_secure():
#                 protocol = 'https://'
#             else:
#                 protocol = 'http://'

#         url = getHostWithPort(request) + file_name if file_name else None

#         data_dict['url'] = url

#         if data_list:
#             data_dict['request_status'] = 1
#             data_dict['msg'] = settings.MSG_SUCCESS
#         elif len(data_list) == 0:
#             data_dict['request_status'] = 1
#             data_dict['msg'] = settings.MSG_NO_DATA
#         else:
#             data_dict['request_status'] = 0
#             data_dict['msg'] = settings.MSG_ERROR

#         return Response(data_dict)

class PurchaseRequisitionsTotalListDownloadView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesRequisitionsMaster.objects.filter(is_deleted=False).order_by('-mr_date')
    serializer_class = PurchaseRequisitionsTotalListSerializer


    def get_queryset(self):
        filter = {}
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        site_location = self.request.query_params.get('site_location', None)
        type_id = self.request.query_params.get('type_id', None)
        search = self.request.query_params.get('search', None)
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        item_type = self.request.query_params.get('item_type', None)
        # item = self.request.query_params.get('item', None)

        if field_name and order_by:

            if field_name == 'project' and order_by == 'asc':
                return self.queryset.filter(is_deleted=False).order_by('project__id')
            elif field_name == 'project' and order_by == 'desc':
                return self.queryset.filter(is_deleted=False).order_by('-project__id')

            elif field_name == 'site_location' and order_by == 'asc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('site_location__id')
            elif field_name == 'site_location' and order_by == 'desc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('-site_location__id')

            elif field_name == 'mr_date' and order_by == 'asc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('mr_date')
            elif field_name == 'mr_date' and order_by == 'desc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('-mr_date')

            elif field_name == 'item' and order_by == 'asc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('item')
            elif field_name == 'item' and order_by == 'desc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('-item')

        if search :
            #print("This is if condition entry")
            queryset = self.queryset.filter(project__project_g_id=search)
            # print('queryset', queryset.query)
            return queryset

        if start_date and end_date:
            start_object = datetime.strptime(start_date,'%Y-%m-%d').date()
            end_object = datetime.strptime(end_date, '%Y-%m-%d').date()
            filter['mr_date__date__range'] = (start_object, end_object)

        if site_location:
            filter['site_location__in']=site_location.split(",")

        if type_id:
            filter['type__in'] = type_id.split(",")

        if filter:
            queryset = self.queryset.filter(**filter)
            # print('queryset',queryset)
            return queryset

        else:
            queryset = self.queryset.filter(is_deleted=False)
            return queryset


    def get(self, request, *args, **kwargs):
        response = super(PurchaseRequisitionsTotalListDownloadView, self).get(self, request, args, kwargs)
        #print('response',response.data)
        reqMasterLisr = []
        data_dict = dict()
        data_list = list()
        data_list1 = list()
        for data in response.data:
            project_details = PmsProjects.objects.filter(id=data['project']).values('project_g_id','id')
            type_details = PmsExecutionPurchasesRequisitionsTypeMaster.objects.filter(id=data['type']).values(
                'type_name','code','id')
            site_location_details = PmsSiteProjectSiteManagement.objects.filter(id=data['site_location']).values(
                'name','id')

            data['type'] = type_details[0]['type_name']
            data['type_code'] = type_details[0]['code']
            data['project'] = project_details[0]['project_g_id']
            data['site_location'] = site_location_details[0]['name']

            reqDetails = PmsExecutionPurchasesRequisitions.objects.filter(
                requisitions_master=data['id'],
                is_deleted=False)

            reqList = []
            item_code = list()
            project_id = list()
            data_list1 = list()
            for reqData in reqDetails:
                req_dict = {
                    'quantity': reqData.quantity,
                }
                req_dict['uom'] = reqData.uom.c_name if reqData.uom else ''
                material_details = Materials.objects.filter(id=reqData.item)
                if material_details:
                    material_details = material_details[0]
                else:
                    material_details = None
    
                data_list.append([data['project'],data['site_location'],data['mr_date'][0:10],data['get_status_display'],data['type'],material_details.description,material_details.mat_code,req_dict['uom'],req_dict['quantity']])
                
        file_name = ''
        if data_list:
            if os.path.isdir('media/pms/requisitions/document'):
                file_name = 'media/pms/requisitions/document/pms_requisitions_report.xlsx'
                file_path = settings.MEDIA_ROOT_EXPORT + file_name
            else:
                os.makedirs('media/pms/requisitions/document')
                file_name = 'media/pms/requisitions/document/pms_requisitions_report.xlsx'
                file_path = settings.MEDIA_ROOT_EXPORT + file_name

            #index = pd.MultiIndex.from_tuples(data_list, names=['Project Id','Site Location','M.R. Date','Status','Type','Item Description','Item Code','UOM','Quantity'])
            final_df = pd.DataFrame(data_list,columns=['Project Id','Site Location','M.R. Date','Status','Type','Item Description','Item Code','UOM','Quantity'])
            #final_df.drop(final_df.columns[[0,1,2,3,4,5,6,7,8]],axis = 1, inplace = True)
            export_csv = final_df.to_excel (file_path,header=True)
            
            if request.is_secure():
                protocol = 'https://'
            else:
                protocol = 'http://'

        url = getHostWithPort(request) + file_name if file_name else None

        data_dict['url'] = url

        if data_list:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_SUCCESS
        elif len(data_list) == 0:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_NO_DATA
        else:
            data_dict['request_status'] = 0
            data_dict['msg'] = settings.MSG_ERROR

        return Response(data_dict)

class PurchaseRequisitionsTotalListNewView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    pagination_class = CSPageNumberPagination
    queryset = PmsExecutionPurchasesRequisitionsMaster.objects.filter(is_deleted=False).order_by('-mr_date')
    serializer_class = PurchaseRequisitionsTotalListSerializer


    def get_queryset(self):
        filter = {}
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        site_location = self.request.query_params.get('site_location', None)
        type_id = self.request.query_params.get('type_id', None)
        search = self.request.query_params.get('search', None)
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        item_type = self.request.query_params.get('item_type', None)
        # item = self.request.query_params.get('item', None)


        if field_name and order_by:

            if field_name == 'project' and order_by == 'asc':
                return self.queryset.filter(is_deleted=False).order_by('project__id')
            elif field_name == 'project' and order_by == 'desc':
                return self.queryset.filter(is_deleted=False).order_by('-project__id')

            elif field_name == 'site_location' and order_by == 'asc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('site_location__id')
            elif field_name == 'site_location' and order_by == 'desc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('-site_location__id')

            elif field_name == 'mr_date' and order_by == 'asc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('mr_date')
            elif field_name == 'mr_date' and order_by == 'desc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('-mr_date')

            elif field_name == 'item' and order_by == 'asc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('item')
            elif field_name == 'item' and order_by == 'desc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('-item')

        if search :
            #print("This is if condition entry")
            queryset = self.queryset.filter(project__project_g_id=search)
            # print('queryset', queryset.query)
            return queryset


        if start_date and end_date:
            start_object = datetime.strptime(start_date,'%Y-%m-%d').date()
            end_object = datetime.strptime(end_date, '%Y-%m-%d').date()
            filter['mr_date__range'] = (start_object, end_object)

        if site_location:
            filter['site_location__in']=site_location.split(",")

        if type_id:
            filter['type__in'] = type_id.split(",")

        if filter:
            queryset = self.queryset.filter(**filter)
            # print('queryset',queryset)
            return queryset

        else:
            queryset = self.queryset.filter(is_deleted=False)
            return queryset


    def get(self, request, *args, **kwargs):
        response = super(PurchaseRequisitionsTotalListNewView, self).get(self, request, args, kwargs)

        getItem = self.request.query_params.get('item', None)

        # print("getItem-->",getItem)

        reqMasterLisr = []
        if getItem is None or getItem == "":
            for data in response.data['results']:
                project_details = PmsProjects.objects.filter(id=data['project']).values('project_g_id','id')
                type_details = PmsExecutionPurchasesRequisitionsTypeMaster.objects.filter(id=data['type']).values(
                    'type_name','code','id')
                site_location_details = PmsSiteProjectSiteManagement.objects.filter(id=data['site_location']).values(
                    'name','id')


                data['type'] = type_details[0]['type_name']
                data['type_code'] = type_details[0]['code']
                data['type_id'] = type_details[0]['id']
                data['project'] = project_details[0]['project_g_id']
                data['project_id'] = project_details[0]['id']
                data['site_location'] = site_location_details[0]['name']
                data['site_location_id'] = site_location_details[0]['id']

                reqDetails = PmsExecutionPurchasesRequisitions.objects.filter(
                    requisitions_master=data['id'],
                    is_deleted=False)

                reqList = []
                for reqData in reqDetails:
                    req_dict = {
                        'id': reqData.id,
                        'hsn_sac_code': reqData.hsn_sac_code,
                        'quantity': reqData.quantity,
                        'current_stock': reqData.current_stock,
                        'procurement_site': reqData.procurement_site,
                        'procurement_ho': reqData.procurement_ho,
                        'required_by': reqData.required_by,
                        'required_on': reqData.required_on,
                        'remarks': reqData.remarks
                    }

                    req_dict['uom'] = reqData.uom.c_name if reqData.uom else ''
                    # if (type_details[0]['type_name']).lower() == "materials":
                    material_details = Materials.objects.filter(id=reqData.item)
                    for matdetaisl in material_details:
                        req_dict['item_details'] = {
                            'id': matdetaisl.id,
                            'name': matdetaisl.name,
                            'mat_code': matdetaisl.mat_code,
                            'description': matdetaisl.description
                        }
                    # print(material_details)
                    if (type_details[0]['type_name']).lower() == 'machinery':
                        machinery_details = PmsMachineries.objects.filter(id=reqData.item)
                        for mach in machinery_details:
                            req_dict['item_details'] = {
                                'id': mach.id,
                                'code': mach.code,
                                'equipment_name': mach.equipment_name
                            }

                    activity_details = PmsExecutionPurchasesRequisitionsMapWithActivities.objects.filter(
                        requisitions_id=reqData.id, is_deleted=False)
                    activity_list = []
                    for e_activity_details in activity_details:
                        # print('e_activity_details',e_activity_details)
                        ac_d = {
                            'id': e_activity_details.activity.id,
                            'code': e_activity_details.activity.code,
                            'description': e_activity_details.activity.description
                        }
                        activity_list.append(ac_d)
                    req_dict['activity_details'] = activity_list

                    ## Added By Rupam Hazra | Date : 18-8-2020 | For quantity modification ##
                    log_details=PmsExecutionPurchasesRequisitionsApprovalLogTable.objects.filter(
                            requisitions_master_id=data['id'],
                            type_id=type_details[0]['id'],
                            uom=reqData.uom,
                            item=reqData.item,
                            approved_quantity__isnull = False
                            ).values(
                            'id','arm_approval','approval_permission_user_level','approved_quantity','created_at','approver_remarks')

                    
                    # if log_details:
                    #     req_dict['quantity'] = log_details[0]['approved_quantity']
                    

                    ## Added By Rupam Hazra | Date : 18-8-2020 | For quantity modification ##






                    reqList.append(req_dict)
                data['requisition_details'] = reqList

                # print("Data : -----> ",data)
        else:
            dammy_item = getItem
            for data in response.data['results']:
                
                project_details = PmsProjects.objects.filter(id=data['project']).values('project_g_id','id')
                type_details = PmsExecutionPurchasesRequisitionsTypeMaster.objects.filter(id=data['type']).values(
                    'type_name','code','id')
                site_location_details = PmsSiteProjectSiteManagement.objects.filter(id=data['site_location']).values(
                    'name','id')


                data['type'] = type_details[0]['type_name']
                data['type_code'] = type_details[0]['code']
                data['type_id'] = type_details[0]['id']
                data['project'] = project_details[0]['project_g_id']
                data['project_id'] = project_details[0]['id']
                data['site_location'] = site_location_details[0]['name']
                data['site_location_id'] = site_location_details[0]['id']

                getReqItem = PmsExecutionPurchasesRequisitions.objects.filter(is_deleted=False,requisitions_master=data['id'],item=dammy_item)
                # print("getReqItem-->",getReqItem)

                reqList = []
                for reqItem in getReqItem:
                    req_dict = {
                        'id': reqItem.id,
                        'hsn_sac_code': reqItem.hsn_sac_code,
                        'quantity': reqItem.quantity,
                        'current_stock': reqItem.current_stock,
                        'procurement_site': reqItem.procurement_site,
                        'procurement_ho': reqItem.procurement_ho,
                        'required_by': reqItem.required_by,
                        'required_on': reqItem.required_on,
                        'remarks': reqItem.remarks
                    }
                    req_dict['uom'] = reqItem.uom.c_name if reqItem.uom else ''
                    # if (type_details[0]['type_name']).lower() == "materials":
                    material_details = Materials.objects.filter(id=reqItem.item)
                    for matdetaisl in material_details:
                        req_dict['item_details'] = {
                            'id': matdetaisl.id,
                            'name': matdetaisl.name,
                            'mat_code': matdetaisl.mat_code,
                            'description': matdetaisl.description
                        }
                    # print(material_details)
                    if (type_details[0]['type_name']).lower() == 'machinery':
                        machinery_details = PmsMachineries.objects.filter(id=reqItem.item)
                        for mach in machinery_details:
                            req_dict['item_details'] = {
                                'id': mach.id,
                                'code': mach.code,
                                'equipment_name': mach.equipment_name
                            }

                    activity_details = PmsExecutionPurchasesRequisitionsMapWithActivities.objects.filter(
                        requisitions_id=reqItem.id, is_deleted=False)
                    activity_list = []
                    for e_activity_details in activity_details:
                        # print('e_activity_details',e_activity_details)
                        ac_d = {
                            'id': e_activity_details.activity.id,
                            'code': e_activity_details.activity.code,
                            'description': e_activity_details.activity.description
                        }
                        activity_list.append(ac_d)
                    req_dict['activity_details'] = activity_list
                    reqList.append(req_dict)
                data['requisition_details'] = reqList

        if response.data['count'] > 0:
            response.data['request_status'] = 1
            response.data['msg'] = settings.MSG_SUCCESS
        else:
            response.data['request_status'] = 1
            response.data['msg'] = settings.MSG_NO_DATA

        return response

class PurchaseRequisitionsTotalListNewDownloadView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesRequisitionsMaster.objects.filter(is_deleted=False).order_by('-mr_date')
    serializer_class = PurchaseRequisitionsTotalListSerializer


    def get_queryset(self):
        filter = {}
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        site_location = self.request.query_params.get('site_location', None)
        type_id = self.request.query_params.get('type_id', None)
        search = self.request.query_params.get('search', None)
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        item_type = self.request.query_params.get('item_type', None)
        # item = self.request.query_params.get('item', None)

        if field_name and order_by:

            if field_name == 'project' and order_by == 'asc':
                return self.queryset.filter(is_deleted=False).order_by('project__id')
            elif field_name == 'project' and order_by == 'desc':
                return self.queryset.filter(is_deleted=False).order_by('-project__id')

            elif field_name == 'site_location' and order_by == 'asc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('site_location__id')
            elif field_name == 'site_location' and order_by == 'desc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('-site_location__id')

            elif field_name == 'mr_date' and order_by == 'asc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('mr_date')
            elif field_name == 'mr_date' and order_by == 'desc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('-mr_date')

            elif field_name == 'item' and order_by == 'asc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('item')
            elif field_name == 'item' and order_by == 'desc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('-item')

        if search :
            #print("This is if condition entry")
            queryset = self.queryset.filter(project__project_g_id=search)
            # print('queryset', queryset.query)
            return queryset

        if start_date and end_date:
            start_object = datetime.strptime(start_date,'%Y-%m-%d').date()
            end_object = datetime.strptime(end_date, '%Y-%m-%d').date()
            filter['mr_date__date__range'] = (start_object, end_object)

        if site_location:
            filter['site_location__in']=site_location.split(",")

        if type_id:
            filter['type__in'] = type_id.split(",")

        if filter:
            queryset = self.queryset.filter(**filter)
            # print('queryset',queryset)
            return queryset

        else:
            queryset = self.queryset.filter(is_deleted=False)
            return queryset


    def get(self, request, *args, **kwargs):
        response = super(PurchaseRequisitionsTotalListNewDownloadView, self).get(self, request, args, kwargs)
        #print('response',response.data)
        reqMasterLisr = []
        data_dict = dict()
        data_check_list = list()
        data_list = list()
        data_list1 = list()
        for data in response.data:
            project_details = PmsProjects.objects.filter(id=data['project']).values('project_g_id','id')
            type_details = PmsExecutionPurchasesRequisitionsTypeMaster.objects.filter(id=data['type']).values(
                'type_name','code','id')
            site_location_details = PmsSiteProjectSiteManagement.objects.filter(id=data['site_location']).values(
                'name','id')

            data['type'] = type_details[0]['type_name']
            data['type_code'] = type_details[0]['code']
            data['project'] = project_details[0]['project_g_id']
            data['site_location'] = site_location_details[0]['name']

            reqDetails = PmsExecutionPurchasesRequisitions.objects.filter(
                requisitions_master=data['id'],
                is_deleted=False)

            reqList = []
            item_code = list()
            project_id = list()
            data_list1 = list()
            for reqData in reqDetails:
                req_dict = {
                    'quantity': reqData.quantity,
                }
                req_dict['uom'] = reqData.uom.c_name if reqData.uom else ''
                material_details = Materials.objects.filter(id=reqData.item)
                if material_details:
                    material_details = material_details[0]
                else:
                    material_details = None


                ## Added By Rupam Hazra | Date : 18-8-2020 | For quantity modification ##
                #print("reqData.id",reqData.id,type_details[0]['id'],reqData.uom,reqData.item,type(reqData.item))
                log_details=PmsExecutionPurchasesRequisitionsApprovalLogTable.objects.filter(
                            requisitions_master_id=data['id'],
                            type_id=type_details[0]['id'],
                            uom=reqData.uom,
                            item=reqData.item,
                            approved_quantity__isnull = False
                            ).values(
                            'id','arm_approval','approval_permission_user_level','approved_quantity','created_at','approver_remarks')

                approved_quantity = 0
                if log_details:
                    approved_quantity = log_details[0]['approved_quantity']
                if approved_quantity == 0:
                    approved_quantity = req_dict['quantity']

                
                data_list.append([data['project'],data['site_location'],data['mr_date'][0:10],data['get_status_display'],data['type'],material_details.description,material_details.mat_code,req_dict['uom'],approved_quantity])
                
                ## Added By Rupam Hazra | Date : 18-8-2020 | For quantity modification ##

        file_name = ''
        if data_list:
            if os.path.isdir('media/pms/requisitions/document'):
                file_name = 'media/pms/requisitions/document/pms_requisitions_report.xlsx'
                file_path = settings.MEDIA_ROOT_EXPORT + file_name
            else:
                os.makedirs('media/pms/requisitions/document')
                file_name = 'media/pms/requisitions/document/pms_requisitions_report.xlsx'
                file_path = settings.MEDIA_ROOT_EXPORT + file_name

            #index = pd.MultiIndex.from_tuples(data_list, names=['Project Id','Site Location','M.R. Date','Status','Type','Item Description','Item Code','UOM','Quantity'])
            final_df = pd.DataFrame(data_list,columns=['Project Id','Site Location','M.R. Date','Status','Type','Item Description','Item Code','UOM','Quantity'])
            #final_df.drop(final_df.columns[[0,1,2,3,4,5,6,7,8]],axis = 1, inplace = True)
            export_csv = final_df.to_excel (file_path,header=True)
            
            if request.is_secure():
                protocol = 'https://'
            else:
                protocol = 'http://'

        url = getHostWithPort(request) + file_name if file_name else None

        data_dict['url'] = url
        data_dict['data_check_list'] = data_check_list

        if data_list:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_SUCCESS
        elif len(data_list) == 0:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_NO_DATA
        else:
            data_dict['request_status'] = 0
            data_dict['msg'] = settings.MSG_ERROR

        return Response(data_dict)

## Add a box in MR format on PMS | Date : 30-06-2020 | Rupam Hazra ##

class PurchaseQuotationsForApprovedListNewView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsExecutionPurchasesRequisitionsMaster.objects.filter(is_deleted=False).order_by('-mr_date')
    serializer_class = PurchaseQuotationsForApprovedListSerializer
    #pagination_class = CSPageNumberPagination

    def get_queryset(self):
        # queryset=self.queryset.filter(status=1)
        filter = {}
        exclude_fields = {}
        project = self.request.query_params.get('project', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        site_location = self.request.query_params.get('site_location', None)
        type_name = self.request.query_params.get('type_name', None)
        search = self.request.query_params.get('search', None)
        item_type = self.request.query_params.get('item_type', None)
        item = self.request.query_params.get('item', None)
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        sort_field='-id'

        section_name = self.request.query_params.get('section_name', None)
        logdin_user = self.request.user
        #print('logdin_user_id',logdin_user)
        section_details=TCoreOther.objects.get(cot_name__iexact=section_name)
        approval_master_details = PmsApprovalPermissonMatser.objects.filter(section=section_details.id,approval_user=logdin_user,is_deleted=False)
        #print('approval_master_details',approval_master_details)

        if not approval_master_details:
            filter['pk__in'] = list()

        if field_name and order_by:
            if field_name == 'project' and order_by == 'asc':
                sort_field='project__project_g_id'
                # return self.queryset.filter((Q(completed_status__isnull=True,status=4)|Q(status=3)),is_deleted=False).order_by('project__project_g_id')
            elif field_name == 'project' and order_by == 'desc':
                sort_field='-project__project_g_id'
                # return self.queryset.filter((Q(completed_status__isnull=True,status=4)|Q(status=3)),is_deleted=False).order_by('-project__project_g_id')

            elif field_name == 'site_location' and order_by == 'asc':
                sort_field='site_location__name'
                # return self.queryset.filter((Q(completed_status__isnull=True,status=4)|Q(status=3)), is_deleted=False).order_by('site_location__name')
            elif field_name == 'site_location' and order_by == 'desc':
                sort_field='-site_location__name'
                # return self.queryset.filter((Q(completed_status__isnull=True,status=4)|Q(status=3)), is_deleted=False).order_by('-site_location__name')

            elif field_name == 'mr_date' and order_by == 'asc':
                sort_field='mr_date'
                # return self.queryset.filter((Q(completed_status__isnull=True,status=4)|Q(status=3)), is_deleted=False).order_by('mr_date')
            elif field_name == 'mr_date' and order_by == 'desc':
                sort_field='-mr_date'
                # return self.queryset.filter((Q(completed_status__isnull=True,status=4)|Q(status=3)), is_deleted=False).order_by('-mr_date')

        if search :
            filter['project__project_g_id']=search
            # print("This is if condition entry")
            # queryset = self.queryset.filter((Q(completed_status__isnull=True,status=4)|Q(status=3)),project__project_g_id=search)

            # print('queryset_search::::::::::::::::::::', queryset)
            # return queryset


        if start_date and end_date:
            start_object = datetime.strptime(start_date, '%Y-%m-%d').date()
            filter['mr_date__gte'] = start_object
            end_object = datetime.strptime(end_date, '%Y-%m-%d').date()
            filter['mr_date__lte'] = end_object + timedelta(days=1)

            # queryset = self.queryset.filter((Q(completed_status__isnull=True,status=4)|Q(status=3)),**filter)

            # return queryset

        if site_location:
            #print('site_location',site_location)
            filter['site_location__in']=list(map(int,site_location.split(",")))

        if project:
            filter['project__in']=list(map(int,project.split(",")))


        if type_name:
            filter['type'] = int(type_name)
            # print("halla ")
            # if type_name.lower() == 'materials':
            #     filter['type'] = 1
            # elif type_name.lower() == 'machinery':
            #     print("hala ")
            #     filter['type'] = 2

        if item:
            filter['item__in']= list(map(int,item.split(",")))
            # print("item:::::::::::::::::::",filter)
            

        
        #print('filter')
        queryset = self.queryset.filter((Q(completed_status__isnull=True,status=4)|Q(status=3)),**filter).exclude(**exclude_fields).order_by(sort_field)
        #print('queryset',queryset.query)
        return queryset
       
    
    def str_to_float(self, obj):
        obj['net_landed_cost'] = float(obj['net_landed_cost'])
        return obj

    def float_to_string(self, obj):
        obj['net_landed_cost'] = "{0:.2f}".format(obj['net_landed_cost'])
        return obj



    def get(self, request, *args, **kwargs):
        data_dict = {}
        po_data_dict = {}
        response = super(PurchaseQuotationsForApprovedListNewView, self).get(request, args, kwargs)
        exclude_fields = {}

        page = int(self.request.query_params.get('page', 1))
        page_count = int(self.request.query_params.get('page_count', 10))
        pagination_offset_slice = get_pagination_offset(page=page,page_count=page_count) 

        section_name = self.request.query_params.get('section_name', None)
        logdin_user = self.request.user
        #print('logdin_user_id',logdin_user)
        section_details=TCoreOther.objects.get(cot_name__iexact=section_name)
        approval_master_details = PmsApprovalPermissonMatser.objects.filter(section=section_details.id,approval_user=logdin_user,is_deleted=False)
        #print('approval_master_details',approval_master_details)
        if approval_master_details:
            approval_master_details = approval_master_details[0]
            approval_user_level = approval_master_details.permission_level
            #print('approval_user_level',approval_user_level)
           
            approval_level_count = PmsApprovalPermissonMatser.objects.filter(
                section=section_details.id,is_deleted=False).count()
            #print('approval_level_count',approval_level_count,type(approval_level_count))
            approval_levels = list()
            #approval_ids = list()
            approval_user_level_no = int(approval_user_level.split('L')[1])
            for level in range(approval_user_level_no,approval_level_count):
                #print('level',level)
                next_approval_level = 'L' + str(int(level) + 1)
                approval_levels.append(next_approval_level)
                
            #print('approval_levels',approval_levels)
            approval_ids = PmsApprovalPermissonMatser.objects.filter(section=section_details.id,is_deleted=False,permission_level__in=(approval_levels)).values_list('id',flat=True)
            #print('approval_ids',approval_ids)
            exclude_fields['item__in']=PmsExecutionPurchasesComparitiveStatementLog.objects.filter(
                (Q(approval_permission_user_level_id=approval_master_details.id) | Q(approval_permission_user_level_id__in=approval_ids)),is_approved=True).values_list('item',flat=True)
                        
            #print('exclude_fields',exclude_fields)
        master_list=[]
        if response.data:
            for count,data in enumerate(response.data):
                po_data_dict = {}
               
                get_approval_details = PmsExecutionPurchasesRequisitionsApproval.objects.filter(
                    requisitions_master=data['id'],
                    is_deleted=False,arm_approval__gte=0).exclude(**exclude_fields)

                if get_approval_details:
                    approveItem_list = []
                    for approve_data in get_approval_details:
                        approveItem_dict = {}

                        #print("approve_data_item",approve_data.item)
                        get_quotation_details = PmsExecutionPurchasesQuotations.objects.filter(requisitions_master=data['id'],
                        is_deleted=False,item = approve_data.item)
                        #print("quotation",get_quotation_details)
                        quoted_item_list =[]
                        quoatedData_list = [] #forvender
                        vendor_list=[]
                        if get_quotation_details:

                            comparitiveStatement = PmsExecutionPurchasesComparitiveStatement.objects.filter(
                                requisitions_master=data['id'],item=approve_data.item,uom=approve_data.uom,is_deleted=False)
                            #print('comparitiveStatement',comparitiveStatement.values())
                            #ranking_details = list()
                            if comparitiveStatement:
                                comparitiveStatement = comparitiveStatement.values()
                                comparitiveStatement = list(map(self.str_to_float, comparitiveStatement))
                                list_data = sorted(comparitiveStatement, key = lambda i: i['net_landed_cost'])
                                comparitiveStatement = list(map(self.float_to_string, comparitiveStatement))
                                l = 0
                                for data1 in list_data:
                                    l+=1
                                    ll = "L"+str(l)
                                    index = [index for (index, d) in enumerate(comparitiveStatement) if d['id']==data1['id']][0]
                                    comparitiveStatement[index]['ranking']=ll
                                approveItem_dict['ranking_details'] = comparitiveStatement

                            
                            for quote_data in get_quotation_details:                            
                                quoatedData_dict = {
                                    'vendor_id' : quote_data.vendor.id,
                                    'vendor_name' : quote_data.vendor.contact_person_name,
                                    'vendor_code' : quote_data.vendor.code,
                                    'quantity' : quote_data.quantity,
                                    'unit_id' : quote_data.unit.id if quote_data.unit else '',
                                    'unit_name' : quote_data.unit.c_name if quote_data.unit else '',
                                    'price' : quote_data.price,
                                    'ranking':None
                                }
                                if comparitiveStatement:
                                    for e_comparitiveStatement in comparitiveStatement:
                                        if quote_data.vendor.id == e_comparitiveStatement['vendor_id']:
                                            quoatedData_dict['ranking'] = e_comparitiveStatement['ranking']

                                vendor_list.append(quote_data.vendor.id)
                                quoatedData_list.append(quoatedData_dict)
                            #print("vendor_list",vendor_list)
                            #print("quoatedData_list",quoatedData_list)
                            approveItem_dict['vendor_details'] = quoatedData_list
                        else:
                            approveItem_dict['vendor_details'] = []

                        

                        approveItem_dict['approved_item'] = approve_data.item
                        approveItem_dict['approved_quantity'] = approve_data.approved_quantity

                        # approveItem_dict['requisition_id']=data['id']
                        # approveItem_dict['project'] = data['project']
                        # approveItem_dict['site_location'] = data['site_location']

                        # approveItem_list.append(approveItem_dict)

                    
                        type_name = PmsExecutionPurchasesRequisitionsTypeMaster.objects.only('type_name').get(id=approve_data.type.id).type_name
                        # if (type_name).lower() == "materials":
                        material_details = Materials.objects.filter(id=approve_data.item).values('name')
                        approveItem_dict['item_name'] = material_details[0]['name']
                        if (type_name).lower() == 'machinery':
                            machinery_details = PmsMachineries.objects.filter(id=approve_data.item).values('equipment_name')
                            approveItem_dict['item_name'] = machinery_details[0]['equipment_name']

                        approveItem_dict['uom'] = approve_data.uom.id
                        approveItem_dict['uom_name'] = approve_data.uom.c_name

                        #level of approvals list 
                        # requisitions_master_id = self.request.query_params.get('requisitions_master_id', None)
                        # item_id = self.request.query_params.get('item_id', None)
                        # uom = self.request.query_params.get('uom', None)

                        #print('vendor_list',vendor_list)

                        section_name = self.request.query_params.get('section_name', None)
                        if section_name:
                            permission_details=[]
                            section_details=TCoreOther.objects.get(cot_name__iexact=section_name)
                            approval_master_details = PmsApprovalPermissonMatser.objects.filter(section=section_details.id,is_deleted=False)
                            #print("approval_master_details",approval_master_details)
                            # type_details= PmsExecutionPurchasesRequisitionsMaster.objects.get(id=requisitions_master_id).type
                            log_details=PmsExecutionPurchasesComparitiveStatementLog.objects.\
                                    filter(
                                        requisitions_master=data['id'],
                                        uom=approve_data.uom,
                                        item=approve_data.item,vendor__in=vendor_list)
                                        
                           
                            amd_list=[]
                            l_d_list=set()
                            for l_d in log_details.values('id','is_approved','approval_permission_user_level','vendor__contact_person_name','vendor','created_at','comment','is_rejected'):
                                l_d_list.add(l_d['approval_permission_user_level'])

                            for a_m_d in approval_master_details:
                                if l_d_list:
                                    if a_m_d.id in l_d_list:
                                        l_d=log_details.filter(approval_permission_user_level=a_m_d.id).order_by('-id')[0]
                                        #f_name = a_m_d.approval_user.first_name if a_m_d.approval_user else '' 
                                        #l_name = a_m_d.approval_user.last_name if a_m_d.approval_user else '' 
                                        var=a_m_d.permission_level
                                        res = re.sub("\D", "", var)
                                        permission_dict={
                                            "user_level":a_m_d.permission_level,
                                            "approval":l_d.is_approved,
                                            "permission_num":int(res),
                                            "approved_vendor":l_d.vendor.contact_person_name,
                                            "approved_vendor_id":l_d.vendor.id,
                                            "approved_date":l_d.created_at,
                                            "approve_comment":l_d.comment,
                                            "is_rejected":l_d.is_rejected,
                                            "user_details":{
                                                "id":l_d.updated_by.id if l_d.updated_by else None,
                                                #"email":a_m_d.approval_user.email if a_m_d.approval_user else None,
                                                "name":  l_d.updated_by.get_full_name() if l_d.updated_by else None,
                                                #"username":a_m_d.approval_user.username
                                                }
                                        }
                                            

                                    else:
                                        f_name = a_m_d.approval_user.first_name if a_m_d.approval_user else '' 
                                        l_name = a_m_d.approval_user.last_name if a_m_d.approval_user else '' 
                                        var=a_m_d.permission_level
                                        res = re.sub("\D", "", var)
                                        permission_dict={
                                            "user_level":a_m_d.permission_level,
                                            "permission_num":int(res),
                                            "approval":None,
                                            "approved_vendor":None,
                                            "approved_vendor_id":None,
                                            "approved_date":None,
                                            "approve_comment":None,
                                            "is_rejected":None,
                                            "user_details":{
                                                "id":a_m_d.approval_user.id if a_m_d.approval_user else None,
                                                "email":a_m_d.approval_user.email if a_m_d.approval_user else None,
                                                "name":  f_name +' '+l_name,
                                                "username":a_m_d.approval_user.username
                                                }
                                        }

                                    permission_details.append(permission_dict)
                                else:
                                    f_name = a_m_d.approval_user.first_name if a_m_d.approval_user else '' 
                                    l_name = a_m_d.approval_user.last_name if a_m_d.approval_user else '' 
                                    var=a_m_d.permission_level
                                    res = re.sub("\D", "", var)
                                    permission_dict={
                                            "user_level":a_m_d.permission_level,
                                            "permission_num":int(res),
                                            "approval":None,
                                            "approved_vendor":None,
                                            "approved_vendor_id":None,
                                            "approved_date":None,
                                            "approve_comment":None,
                                            "is_rejected":None,
                                            "user_details":{
                                                "id":a_m_d.approval_user.id if a_m_d.approval_user else None,
                                                "email":a_m_d.approval_user.email if a_m_d.approval_user else None,
                                                "name":  f_name +' '+l_name,
                                                "username":a_m_d.approval_user.username
                                                }
                                        }
                                    permission_details.append(permission_dict)
                            approveItem_dict['permission_details']=permission_details    
                            




                            po_details = PmsExecutionPurchasesPO.objects.filter(is_deleted=False,requisitions_master=data['id']).order_by('-id')
                            # print("po_details",po_details)
                            if po_details:
                                for po in po_details:
                                    # print("hkg",po.id)
                                    item = PmsExecutionPurchasesPOItemsMAP.objects.filter(is_deleted=False,purchase_order=po.id,item=approve_data.item)
                                    # print("item", item)
                                    if item:
                                        po_data_dict={
                                            'po_no': po.__dict__['po_no'],
                                            'po_amount': po.__dict__['po_amount'],
                                            'po_date': po.__dict__['created_at']
                                        }
                                        break
                            else:
                                po_data_dict= {
                                    'po_no': "",
                                    'po_amount': "",
                                    'po_date': ""
                                }
                    

                            approveItem_dict['last_po'] = po_data_dict
                        
                        if vendor_list:
                            approveItem_list.append(approveItem_dict)
                        


                    reqquisition_data={}
                    reqquisition_data['mr_date'] = data['mr_date']
                    reqquisition_data['requisition_id']=data['id']
                    reqquisition_data['project'] = data['project']
                    reqquisition_data['project_code'] = PmsProjects.objects.only('project_g_id').get(pk=data['project']).project_g_id
                    reqquisition_data['project_name'] = PmsProjects.objects.only('name').get(pk=data['project']).name
                    reqquisition_data['site_location'] = data['site_location']
                    reqquisition_data['site_location_name'] = PmsSiteProjectSiteManagement.objects.only('name').get(pk=data['site_location']).name
                    reqquisition_data['item_data'] = approveItem_list
                    reqquisition_data['type'] = {
                            'id': data['type'],
                            'type_name': PmsExecutionPurchasesRequisitionsTypeMaster.objects.get(id=data['type']).type_name,
                            'code':  PmsExecutionPurchasesRequisitionsTypeMaster.objects.get(id=data['type']).code
                        }
                    #print('dsdsa',reqquisition_data['item_data'])
                    if reqquisition_data['item_data']:
                        master_list.append(reqquisition_data)
                # print("approveItem_list",approveItem_list)

        response.data = master_list
        res = dict()
        res['count'] = len(response.data)
        res['request_status'] = 1
        res['msg'] = 'Success' if res['count'] else 'Data Not Found'
        res['results'] = response.data[pagination_offset_slice]

        return Response(data=res, status=200)
