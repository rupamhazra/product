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
from pagination import CSLimitOffestpagination,CSPageNumberPagination
from rest_framework import filters
import calendar
from datetime import datetime,timedelta
from holidays.models import *
import collections
from rest_framework.exceptions import APIException
import pandas as pd
import numpy as np
from django_filters.rest_framework import DjangoFilterBackend
from master.serializers import UserModuleWiseListSerializer
from master.models import TMasterModuleRole
from users.models import TCoreUserDetail
from users.serializers import UserSerializer
from custom_decorator import *
from rest_framework.parsers import FileUploadParser
import os
from pms.custom_filter import *

'''
    For Knox 
    Author : Rupam Hazra
    Date : 16.03.2020
'''
from knox.auth import TokenAuthentication
from rest_framework import permissions
from knox.models import AuthToken

#::::::::::::: Pms Site Type Project Site Management ::::::::::::::::::::#
class SiteTypeProjectSiteManagementAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsSiteTypeProjectSiteManagement.objects.filter(is_deleted=False).order_by('-id')
    serializer_class = SiteTypeProjectSiteManagementAddSerializer
    @response_modify_decorator_list
    def list(self, request, *args, **kwargs):
        return response

class SiteTypeProjectSiteManagementEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsSiteTypeProjectSiteManagement.objects.all()
    serializer_class = SiteTypeProjectSiteManagementEditSerializer

class SiteTypeProjectSiteManagementDeleteView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsSiteTypeProjectSiteManagement.objects.all()
    serializer_class = SiteTypeProjectSiteManagementDeleteSerializer

#::::::::::::::: Pms Site Project Site Management ::::::::::::::::::::#
class ProjectSiteManagementSiteAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsSiteProjectSiteManagement.objects.filter(is_deleted=False)
    serializer_class = ProjectSiteManagementSiteAddSerializer
    filter_backends = ( filters.SearchFilter,filters.OrderingFilter,)
    search_fields =('name','address','company_name','gst_no','geo_fencing_area','type__name')
    ordering = ('-id',)

    def list(self, request, *args, **kwargs):
        response = super(ProjectSiteManagementSiteAddView, self).list(request, args, kwargs)
        print('response: ', response.data)
        data_dict = {}
        for data in response.data:
            print("data_id",data['id'])
            long_lat_data=PmsSiteProjectSiteManagementMultipleLongLat.objects.filter(project_site=data['id']).values('latitude','longitude')
            data['long_lat_details']=long_lat_data
        data_dict['result'] = response.data
        if response.data:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_SUCCESS
        elif len(response.data)==0:
            data_dict['request_status'] = 1
            data_dict['msg'] =settings.MSG_NO_DATA
        else:
            data_dict['request_status'] = 0
            data_dict['msg'] = settings.MSG_ERROR

        response.data = data_dict
        return response

class ProjectSiteManagementSiteEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsSiteProjectSiteManagement.objects.filter(is_deleted=False)
    serializer_class = ProjectSiteManagementSiteEditSerializer

class ProjectSiteManagementSiteDeleteView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsSiteProjectSiteManagement.objects.all()
    serializer_class = ProjectSiteManagementSiteDeleteSerializer

class ProjectSiteManagementSiteListWPView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsSiteProjectSiteManagement.objects.filter(is_deleted=False)
    serializer_class = ProjectSiteManagementSiteAddSerializer
    # filter_backends = ( filters.SearchFilter,filters.OrderingFilter,)
    # search_fields =('name','address','company_name','gst_no','geo_fencing_area','type__name')
    # ordering = ('-id',)

#:::::::::::: PROJECTS ::::::::::::::::::::::::::::#
class ProjectsAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsProjects.objects.all()
    serializer_class=ProjectsAddSerializer

class ProjectsListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsProjects.objects.filter(is_deleted=False).order_by('-id')
    serializer_class=ProjectsListSerializer
    pagination_class = CSPageNumberPagination
    def get_queryset(self):
        filter = {}
        approval_dict={}
        from_start_date = self.request.query_params.get('from_start_date', None)
        start_date_to = self.request.query_params.get('start_date_to', None)
        from_end_date = self.request.query_params.get('from_end_date', None)
        end_date_to = self.request.query_params.get('end_date_to', None)
        site_location = self.request.query_params.get('site_location', None)
        approvals = self.request.query_params.get('approvals', None)
        state = self.request.query_params.get('state', None)

        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)

        search = self.request.query_params.get('search', None)

        if search:
            queryset= self.queryset.filter(is_deleted=False,project_g_id=search,status=True)
            return queryset

        if field_name and order_by:
            if field_name=='tender_g_id' and order_by == 'asc':
                return self.queryset.filter(status=True,is_deleted=False).order_by('tender__tender_g_id')
            elif field_name=='tender_g_id' and order_by == 'desc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('-tender__tender_g_id')
            elif field_name == 'project_g_id' and order_by == 'asc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('project_g_id')
            elif field_name == 'project_g_id' and order_by == 'desc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('-project_g_id')
            elif field_name == 'start_date' and order_by == 'asc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('start_date')
            elif field_name == 'start_date' and order_by == 'desc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('-start_date')
            elif field_name == 'end_date' and order_by == 'asc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('end_date')
            elif field_name == 'end_date' and order_by == 'desc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('-end_date')

        if from_start_date and start_date_to:
            start_object = datetime.strptime(from_start_date, '%Y-%m-%d')
            end_object = datetime.strptime(start_date_to, '%Y-%m-%d')
            filter['start_date__range'] = (start_object, end_object)

        if from_end_date and end_date_to:
            start_object = datetime.strptime(from_end_date, '%Y-%m-%d')
            end_object = datetime.strptime(end_date_to, '%Y-%m-%d')
            filter['end_date__range'] = (start_object, end_object)

        if site_location:
            site_location_list = site_location.split(',')
            # print('site_location_list',site_location_list)
            filter['site_location__in']=site_location_list
        # else: None
        if approvals:
            approvals_list=approvals.split(',')
            # print('approvals_list',approvals_list)
            approval_dict['pre_execution_tabs__in']=approvals_list
            pre_approvals=PmsPreExecutionApproval.objects.filter(**approval_dict,is_deleted=False)
            project_id_list=[]
            for p_a in pre_approvals:
                if p_a.approved_status == 1:
                    project_id_list.append(p_a.project.id)
            filter['id__in']=project_id_list

        if state:
            if state == 'ongoing':
                filter['state__in'] = [1,2,3]
            else:
                filter['state'] = 4
        queryset = self.queryset.filter(is_deleted=False, **filter, status=True)
        # print('queryset',queryset.query)
        return queryset

        

class ClosedProjectsListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsProjects.objects.filter(is_deleted=False,state=4).order_by('-id')
    serializer_class=ProjectsListSerializer
    pagination_class = CSPageNumberPagination
    def get_queryset(self):
        filter = {}
        approval_dict={}
        from_start_date = self.request.query_params.get('from_start_date', None)
        # print('from_start_date',from_start_date)
        start_date_to = self.request.query_params.get('start_date_to', None)
        from_end_date = self.request.query_params.get('from_end_date', None)
        end_date_to = self.request.query_params.get('end_date_to', None)
        site_location = self.request.query_params.get('site_location', None)
        approvals= self.request.query_params.get('approvals', None)

        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)

        search = self.request.query_params.get('search', None)

        if search:
            queryset= self.queryset.filter(is_deleted=False,project_g_id=search,status=True)
            return queryset

        if field_name and order_by:
            if field_name=='tender_g_id' and order_by == 'asc':
                return self.queryset.filter(status=True,is_deleted=False).order_by('tender__tender_g_id')
            elif field_name=='tender_g_id' and order_by == 'desc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('-tender__tender_g_id')
            elif field_name == 'project_g_id' and order_by == 'asc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('project_g_id')
            elif field_name == 'project_g_id' and order_by == 'desc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('-project_g_id')
            elif field_name == 'start_date' and order_by == 'asc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('start_date')
            elif field_name == 'start_date' and order_by == 'desc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('-start_date')
            elif field_name == 'end_date' and order_by == 'asc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('end_date')
            elif field_name == 'end_date' and order_by == 'desc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('-end_date')

        if from_start_date and start_date_to:
            start_object = datetime.strptime(from_start_date, '%Y-%m-%d')
            end_object = datetime.strptime(start_date_to, '%Y-%m-%d')
            filter['start_date__range'] = (start_object, end_object)

        if from_end_date and end_date_to:
            start_object = datetime.strptime(from_end_date, '%Y-%m-%d')
            end_object = datetime.strptime(end_date_to, '%Y-%m-%d')
            filter['end_date__range'] = (start_object, end_object)

        if site_location:
            site_location_list = site_location.split(',')
            # print('site_location_list',site_location_list)
            filter['site_location__in']=site_location_list
        # else: None
        if approvals:
            approvals_list=approvals.split(',')
            # print('approvals_list',approvals_list)
            approval_dict['pre_execution_tabs__in']=approvals_list
            pre_approvals=PmsPreExecutionApproval.objects.filter(**approval_dict,is_deleted=False)
            project_id_list=[]
            for p_a in pre_approvals:
                if p_a.approved_status == 1:
                    project_id_list.append(p_a.project.id)
            filter['id__in']=project_id_list

        if filter:
            queryset = self.queryset.filter(is_deleted=False, **filter, status=True)
            # print('queryset',queryset.query)
            return queryset

        else:
            queryset = self.queryset.filter(is_deleted=False, status=True)
            return queryset

class ProjectsListWPView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsProjects.objects.filter(is_deleted=False).order_by('-id')
    serializer_class=ProjectsListSerializer
    def get_queryset(self):
        # print('sdgfsdfsd')
        filter = {}
        start_date = self.request.query_params.get('start_date', None)
        # print("start_date",start_date)
        end_date = self.request.query_params.get('end_date', None)
        site_location = self.request.query_params.get('site_location', None)

        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)

        search = self.request.query_params.get('search', None)

        if search:
            queryset= self.queryset.filter(is_deleted=False,project_g_id=search,status=True)
            return queryset

        if field_name and order_by:
            if field_name=='tender_g_id' and order_by == 'asc':
                return self.queryset.filter(status=True,is_deleted=False).order_by('tender__tender_g_id')
            elif field_name=='tender_g_id' and order_by == 'desc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('-tender__tender_g_id')
            elif field_name == 'project_g_id' and order_by == 'asc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('project_g_id')
            elif field_name == 'project_g_id' and order_by == 'desc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('-project_g_id')
            elif field_name == 'start_date' and order_by == 'asc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('start_date')
            elif field_name == 'start_date' and order_by == 'desc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('-start_date')
            elif field_name == 'end_date' and order_by == 'asc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('end_date')
            elif field_name == 'end_date' and order_by == 'desc':
                return self.queryset.filter(status=True, is_deleted=False).order_by('-end_date')

        if start_date and end_date:
            # print("hjvgfa")
            start_object = datetime.strptime(start_date, '%Y-%m-%d')
            end_object = datetime.strptime(end_date, '%Y-%m-%d')
            filter['start_date__range'] = (start_object, end_object)
        if site_location:
            site_location_list = site_location.split(',')
            # print('site_location_list',site_location_list)
            filter['site_location__in']=site_location_list

        if filter:
            queryset = self.queryset.filter(is_deleted=False, status=True, **filter)
            # print('queryset',queryset.query)
            return queryset

        else:
            queryset = self.queryset.filter(is_deleted=False, status=True)
            return queryset

    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        return response

class ProjectsListCountView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsProjects.objects.filter(is_deleted=False).order_by('-id')
    serializer_class = ProjectsListCountSerializer
    def get(self, request, *args, **kwargs):
        dic={}
        total_projects = PmsProjects.objects.all().count()
        # print('total_projects', type(total_projects))

        active_projects = PmsProjects.objects.filter(status=True, is_deleted=False).count()
        # print('active_projects',active_projects)

        archived_projects=PmsProjects.objects.filter(status=False).count()
        # print('archived_projects',archived_projects)

        closed_projects=PmsProjects.objects.filter(state=4).count()

        completed_projects=PmsProjects.objects.filter(state=4).count()

        cancelled_projects=PmsProjects.objects.filter(state=5).count()

        pre_execution_projects=PmsProjects.objects.filter(state=1, is_deleted=False).count()
        execution_projects=PmsProjects.objects.filter(state=2, is_deleted=False).count()
        post_execution_projects=PmsProjects.objects.filter(state=3, is_deleted=False).count()

        dic= {'total_projects': total_projects,
               'active_projects': active_projects,
               'archived_projects': archived_projects,
               'closed_projects': closed_projects,
               'completed_projects': completed_projects,
               'cancelled_projects': cancelled_projects,
               'pre_execution_projects': pre_execution_projects,
               'execution_projects': execution_projects,
               'post_execution_projects': post_execution_projects,
               }

        data_dict = {}
        data_dict['result'] =dic
        if dic:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_SUCCESS
        elif len(dic) == 0:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_NO_DATA
        else:
            data_dict['request_status'] = 0
            data_dict['msg'] = settings.MSG_ERROR
        dic = data_dict

        return Response(dic)

class ProjectsEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsProjects.objects.all()
    serializer_class = ProjectsEditSerializer
    def get(self, request, *args, **kwargs):
        response=dict()
        project = PmsProjects.objects.filter(is_deleted=False,pk=kwargs['pk'])
        # print('project',project)
        for e_project in project:
            updated_by  = e_project.updated_by  if e_project.updated_by else ''
            #print('update_by',updated_by)
            # print("e_project.site_location.id",e_project.site_location)
            bidder_type=PmsTenderBidderType.objects.filter(tender=e_project.tender.id,is_deleted=False)
            # print('bidder_type',bidder_type)
            if bidder_type:
                for b_d in bidder_type:
                    response={
                        'bidder_type':b_d.bidder_type
                    }
            else:
                 response={
                        'bidder_type':None
                    }

            if e_project.site_location is not None:
                response['id']=int(e_project.id)
                response['project_g_id']=e_project.project_g_id
                response['tender_id']=e_project.tender.id
                response['name']=e_project.name
                response['site_location']=e_project.site_location.id
                response['start_date']=e_project.start_date
                response['end_date']=e_project.end_date
                response['project_coordinator'] = e_project.project_coordinator.id if e_project.project_coordinator else None
                response['project_manager'] = e_project.project_manager.id if e_project.project_manager else None
                response['updated_by']=str(updated_by)
                
            else:
                response['id']=int(e_project.id)
                response['project_g_id']=e_project.project_g_id
                response['tender_id']=e_project.tender.id
            m_list = list()
            e_list = list()
            machinary_list = PmsProjectsMachinaryMapping.objects.filter(project=e_project.id,
                                                                        is_deleted=False)

            if machinary_list is None:
                m_list = []
            else:
                for e_machinary in machinary_list:
                    m_list.append(
                        {'id': int(e_machinary.id),
                         'machinary': e_machinary.machinary.id,
                         'project': e_machinary.project.id,
                         'machinary_s_d_req': e_machinary.machinary_s_d_req,
                         'machinary_e_d_req': e_machinary.machinary_e_d_req
                         }
                    )

            response['machinary_list'] = m_list
            employee_list = PmsProjectUserMapping.objects.filter(project=e_project.id, is_deleted=False)
            if employee_list is None:
                e_list=[]
            else:
                for e_l in employee_list:
                    e_list.append(
                        {'id': int(e_l.id),
                         'user': e_l.user.id,
                         'project': e_l.project.id,
                         'start_date': e_l.start_date,
                         'expire_date': e_l.expire_date
                         }
                    )
            response['employee_list'] = e_list
        #print('response',response)
        return Response(response)

class ProjectsDeleteView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsProjects.objects.all()
    serializer_class = ProjectsDeleteSerializer

class ProjectsDetailsByProjectSiteIdView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsProjects.objects.all()
    serializer_class = ProjectsDetailsByProjectSiteIdSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('site_location',)
    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        return response

class ProjectsListWithLatLongView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsProjects.objects.filter(is_deleted=False).order_by('-id')
    serializer_class=ProjectsListWithLatLongSerializer
    
    @response_modify_decorator_get
    def get(self,request,*args,**kwargs):
        return response

class ProjectsManpowerReassignTransferView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsProjectUserMapping.objects.all()
    serializer_class = ProjectsManpowerReassignTransferSerializer
    
    @response_modify_decorator_post
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class ProjectsMachinaryReassignTransferView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsProjectsMachinaryMapping.objects.all()
    serializer_class = ProjectsMachinaryReassignTransferSerializer
    
    @response_modify_decorator_post
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class ProjectStartToEndDateListView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsProjects.objects.filter(is_deleted=False)
    serializer_class=ProjectsListCountSerializer

    def get_month_value(self, month_range) -> list:
        from collections import OrderedDict
        month_list = []
        start, end = [datetime.strptime(_, "%Y-%m-%d") for _ in month_range]
        month_list = OrderedDict(
            ((start + timedelta(_)).strftime(r"%B-%Y"), None) for _ in range((end - start).days)).keys()
        return month_list
        
    
    def get(self, request, *args, **kwargs):

        response = super(self.__class__, self).get(self, request, args, kwargs)
        print('response',response.data)
        if response.data:
            m_len_list = list()
            project = self.kwargs['pk']
            queryset = self.queryset.filter(pk=project).values('start_date', 'end_date')[0]
            print('queryset',queryset)
           
            if queryset['start_date'] and queryset['end_date']:
                start_date = datetime.strftime(queryset['start_date'].date(), '%Y-%m-%d')
                end_date = datetime.strftime(queryset['end_date'].date(), '%Y-%m-%d')
                month_range = [start_date, end_date]
                month_length = self.get_month_value(month_range)
                m_len_list = [x for x in month_length]
                print("month_length", m_len_list)
        
        data_dict = dict()
        if response.data:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_SUCCESS
            data_dict['result'] = m_len_list 
        elif len(response.data) == 0:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_NO_DATA
            data_dict['result'] = []
        else:
            data_dict['request_status'] = 0
            data_dict['msg'] = settings.MSG_ERROR
            data_dict['result'] = []
        
        return Response(data_dict)

## Change Request PMS Daily [Modifications Required in PMS System] | Date : 25-06-2020 | Rupam Hazra ##

class EmployeeListBySiteProjectListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = User.objects.filter(is_superuser=False,is_active=True)
    serializer_class=UserSerializer

    def get_queryset(self):
        #print('sddsffdffdsffds')
        site_id = self.kwargs["site_id"]
        filter = {
        'pk__in':PmsProjectUserMapping.objects.filter(
            project_id__in=(PmsProjects.objects.filter(site_location_id=site_id).values_list('id',flat=True))).values_list('user',flat=True)
        }
        queryset = self.queryset.filter(**filter)
        return queryset
    
    @response_modify_decorator_get
    def get(self,request,*args,**kwargs):
        return response

class ProjectSitesByLoginUserView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsSiteProjectSiteManagement.objects.filter(is_deleted=False)
    serializer_class = ProjectSiteManagementSiteAddSerializer
    filter_backends = ( filters.SearchFilter,filters.OrderingFilter,)
    search_fields =('name','address','company_name','gst_no','geo_fencing_area','type__name')
    ordering = ('-id',)

    def get_queryset(self):
        login_user = self.request.user
        user_projects = PmsProjectUserMapping.objects.filter(user=login_user).values_list('project__site_location',flat=True)
        #print('user_projects',user_projects)
        queryset = self.queryset.filter(pk__in=user_projects)
        return queryset


    def list(self, request, *args, **kwargs):
        response = super(ProjectSitesByLoginUserView, self).list(request, args, kwargs)
        #print('response: ', response.data)
        data_dict = {}
        for data in response.data:
            #print("data_id",data['id'])
            long_lat_data=PmsSiteProjectSiteManagementMultipleLongLat.objects.filter(project_site=data['id']).values('latitude','longitude')
            data['long_lat_details']=long_lat_data
        data_dict['result'] = response.data
        if response.data:
            data_dict['request_status'] = 1
            data_dict['msg'] = settings.MSG_SUCCESS
        elif len(response.data)==0:
            data_dict['request_status'] = 1
            data_dict['msg'] =settings.MSG_NO_DATA
        else:
            data_dict['request_status'] = 0
            data_dict['msg'] = settings.MSG_ERROR

        response.data = data_dict
        return response

## Change Request PMS Daily [Modifications Required in PMS System] | Date : 25-06-2020 | Rupam Hazra ##


class ProjectByLoginUserView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsProjects.objects.filter(is_deleted=False)
    serializer_class = ProjectsListSerializer
    ordering = ('-id',)

    def get_queryset(self):
        login_user = self.request.user
        user_projects = PmsProjectUserMapping.objects.filter(user=login_user).values_list('project',flat=True)
        #print('user_projects',user_projects)
        queryset = self.queryset.filter(pk__in=user_projects)
        return queryset

    @response_modify_decorator_list
    def list(self, request, *args, **kwargs):
        response = super(ProjectByLoginUserView, self).list(request, args, kwargs)
        return response
