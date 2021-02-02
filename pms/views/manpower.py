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
from datetime import datetime
from holidays.models import *
import collections
from rest_framework.exceptions import APIException
import pandas as pd
import numpy as np
from django_filters.rest_framework import DjangoFilterBackend
from master.serializers import UserModuleWiseListSerializer,UserModuleWiseUserListByDesignationIdSerializer
from master.models import TMasterModuleRoleUser
from core.models import TCoreDesignation
from core.serializers import CoreDesignationAddSerializer
from users.models import TCoreUserDetail
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

#:::::::::::::::::::  Manpower :::::::::::::::::::::::::::#
class ManPowerListWOView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TMasterModuleRoleUser.objects.filter(
        mmr_user__isnull=False,
        mmr_user__is_active=True,
        mmr_user__is_superuser=False,
        mmr_is_deleted=False,
        #mmr_type=3,
        mmr_user__in=(
            TCoreUserDetail.objects.filter(
                termination_date__isnull=True,cu_is_deleted=False).values_list('cu_user',flat=True)))
    
    serializer_class =UserModuleWiseListSerializer
    def get_queryset(self):
        module_id=self.kwargs['module_id']
        search = self.request.query_params.get('search', None)
        if search:
            return self.queryset.filter(mmr_module_id=module_id,mmr_user__in=(
            User.objects.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search),is_active=True)))
        else:
            return self.queryset.filter(mmr_module_id=module_id)
    @response_modify_decorator_get_after_execution
    def get(self,request,*args,**kwargs):
        response = super(ManPowerListWOView, self).get(self, request, args, kwargs)
        print('response',response.data)
        module_id = self.kwargs['module_id']
        for data in response.data:
            if data['mmr_user']:
                #print('data:',data)
                employee_details = TCoreUserDetail.objects.filter(cu_user=data['mmr_user'],cu_is_deleted=False)
                for employee in employee_details:
                    manpower_dict = {}
                    #print("employee: ", employee.cu_user_id)
                    manpower_dict['employee_id']=employee.cu_user_id
                    manpower_dict['employee_code'] = employee.cu_emp_code
                    name = employee.cu_user.first_name + ' ' +employee.cu_user.last_name
                    manpower_dict['employee_name']=name.strip()
                    manpower_dict['email_id']=employee.cu_user.email
                    manpower_dict['contact_no']=employee.cu_phone_no

                    project_details = PmsProjectUserMapping.objects.filter(user_id=employee.cu_user_id)
                    projects = []
                    for project in project_details:
                        project_data = {"id": project.project.id, "name": project.project.name}
                        projects.append(project_data)
                data['project'] = projects
                designation_details = TMasterModuleRoleUser.objects.filter(
                    mmr_user=data['mmr_user'],mmr_module=module_id,mmr_is_deleted=False)
                #print('designation_details',designation_details)
                if designation_details:
                    for designation in designation_details:
                        if designation.mmr_designation:
                            data['designation'] =designation.mmr_designation.cod_name
                        else:
                            data['designation'] = ""

                data['mmr_user'] = manpower_dict
        return response
class ManPowerListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    pagination_class = CSPageNumberPagination
    queryset = TMasterModuleRoleUser.objects.filter(
        mmr_user__isnull=False,
        mmr_user__is_active=True,
        mmr_user__is_superuser=False,
        mmr_is_deleted=False,
        #mmr_type=3,
        mmr_user__in=(
            TCoreUserDetail.objects.filter(
                termination_date__isnull=True,cu_is_deleted=False).values_list('cu_user',flat=True)))
    serializer_class = UserModuleWiseListSerializer
    def get_queryset(self):
        module_id = self.kwargs['module_id']
        project=self.request.query_params.get('project', None)
        designation=self.request.query_params.get('designation', None)
        #print('designation',designation)
        search=self.request.query_params.get('search', None)
        sort_field='-id'
        # print('project',project)
        user_p_list=[]
        designation_details_name=[]

        if search:
            if '@' in search:
                return self.queryset.filter(mmr_module_id=module_id,mmr_user__email__icontains=search)
            elif search.isdigit():
                user_id = TCoreUserDetail.objects.filter(cu_is_deleted=False,cu_phone_no__icontains=search).values('cu_user')
                if user_id:
                    user_id_list = [x['cu_user'] for x in user_id]
                    return self.queryset.filter(mmr_module_id=module_id,mmr_user__in=user_id_list)
                else:
                    return TMasterModuleRoleUser.objects.none()
            else:
                #print("user_name")
                name = search.split(" ")
                #print("name", name)
                userlist = list()
                if name:
                    for i in name:
                        users = User.objects.filter(Q(first_name__icontains=i) | Q(last_name__icontains=i))
                        for user in users:
                            userlist.append(user.id)
                    return self.queryset.filter(mmr_user__in=userlist,mmr_module_id=module_id)
            

        if project:
            project=project.split(',')
            user_list=PmsProjectUserMapping.objects.filter(project__in=project)
            # print(user_list)
            for u_l in user_list:
                user_p_list.append(u_l.user.id)
            print(user_p_list)
            # return  self.queryset.filter(mmr_module_id=module_id,mmr_user__in=user_p_list)

        if designation:
            designation=designation.split(',')
            desgnation_list=[]
            print(designation)
            for d in designation:
                designation_details_name=TCoreDesignation.objects.filter(cod_name=d).count()
                if designation_details_name:
                    designation_details_name = TCoreDesignation.objects.get(cod_name=d)
                    desgnation_list.append(designation_details_name)
        if user_p_list and designation_details_name:
            queryset=self.queryset.filter(mmr_module_id=module_id,mmr_user__in=user_p_list)
            return queryset.filter(mmr_designation__in =desgnation_list)
        elif user_p_list:
            return  self.queryset.filter(mmr_module_id=module_id,mmr_user__in=user_p_list)
        elif designation_details_name:
            return self.queryset.filter(mmr_module_id=module_id,mmr_designation__in=desgnation_list)
        else:
            return self.queryset.filter(mmr_module_id=module_id)

        # field_name = self.request.query_params.get('field_name', None)
        # order_by = self.request.query_params.get('order_by', None)

        # if field_name and order_by:
        #     if field_name == 'email_id' and order_by == 'asc':
        #         sort_field ='mmr_user__cu_user__cu_alt_email_id'

        #     if field_name =='email_id' and order_by=='desc':
        #         sort_field ='-mmr_user__cu_user__cu_alt_email_id'

           

        #     return self.queryset.filter(mmr_module_id=module_id).order_by(sort_field)

    def filter_order_by(self, obj):
        return dict(obj)

    def order_by_with_field_name(self, response):
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        ob = True if order_by == 'desc' else False
        # print('response end', response.data)
        if field_name and order_by:
            data_list = list(map(lambda x: dict(x), response.data['results']))
            response.data['results'] = sorted(data_list, key = lambda x: x['mmr_user'][field_name], reverse = ob)




    def get(self, request, *args, **kwargs):
        response = super(ManPowerListView, self).get(self, request, args, kwargs)
        # print('response', response.data)
        module_id = self.kwargs['module_id']
        # print('module_id', module_id)
        # print('module_id', type(module_id))



        for data in response.data['results']:
            if data['mmr_user']:
                #print('data:',data['mmr_user'])
                data['designation'] = TCoreUserDetail.objects.filter(
                    cu_user_id=data['mmr_user'], cu_is_deleted=False).values_list('designation__cod_name',flat=True).first()
                #print('designation_details',designation_details)
                 
                # if designation_details:
                #     for e_designation in designation_details:
                #         print('designation',designation.designation)
                        
                #         data['designation'] = designation.designation__cod_name if designation.designation else ""

                employee_details = TCoreUserDetail.objects.filter(cu_user=data['mmr_user'])
                for employee in employee_details:
                    manpower_dict = {}
                    # print("employee: ", employee.cu_user_id)
                    manpower_dict['employee_id'] = employee.cu_user_id
                    manpower_dict['reporting_head'] = employee.reporting_head.get_full_name() if employee.reporting_head else None
                    manpower_dict['hod'] = employee.hod.get_full_name() if employee.hod else None
                    manpower_dict['employee_code'] = employee.cu_emp_code
                    name = employee.cu_user.first_name + ' ' + employee.cu_user.last_name
                    manpower_dict['employee_name'] = name.strip()
                    manpower_dict['email_id'] = employee.cu_alt_email_id if employee.cu_alt_email_id else ''
                    manpower_dict['contact_no'] = employee.cu_phone_no
                    data['mmr_user'] = manpower_dict
                    project_details = PmsProjectUserMapping.objects.filter(
                        user_id=employee.cu_user_id)
                    projects = []
                    for project in project_details:
                        project_data = {
                            "id": project.project.id, 
                            "name": project.project.name,
                            "project_g_id":project.project.project_g_id,
                            "start_date":project.start_date,
                            "expire_date":project.expire_date
                            }
                        projects.append(project_data)
                    data['project'] = projects
                    # print('mmr_user',data['mmr_user'])
        self.order_by_with_field_name(response)
        return response


class ManPowerDesignationListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    pagination_class = CSPageNumberPagination
    queryset = TCoreDesignation.objects.filter(cod_is_deleted=False)
    serializer_class = CoreDesignationAddSerializer
    # filter_backends = (DjangoFilterBackend,)
    # filterset_fields = ('mmg_module',)
    @response_modify_decorator_list_or_get_before_execution_for_pagination
    def get(self, request, *args, **kwargs):
        return response
class ManPowerDesignationListWOPaginationView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreDesignation.objects.filter(cod_is_deleted=False)
    serializer_class = CoreDesignationAddSerializer
    #filter_backends = (DjangoFilterBackend,)
    #filterset_fields = ('mmr_module',)
    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        return response


class ManPowerListByDesignationIdView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    pagination_class = CSPageNumberPagination
    queryset = TMasterModuleRoleUser.objects.filter(mmr_user__isnull=False,mmr_user__is_active=True)
    serializer_class = UserModuleWiseUserListByDesignationIdSerializer
    def get_queryset(self):
        module_id = self.kwargs['module_id']
        designation_id = self.kwargs['designation_id']
        return self.queryset.filter(mmr_module_id=module_id,mmr_designation_id=designation_id)

    @response_modify_decorator_list_or_get_after_execution_for_pagination
    def get(self,request, *args, **kwargs):
        user_dict={}
        user_details=[]
        module_id = self.kwargs['module_id']
        designation_id = self.kwargs['designation_id']
        response = super(ManPowerListByDesignationIdView, self).get(self, request, args, kwargs)
        for data in response.data['results']:
            if data['mmr_user']:
                user_data=User.objects.filter(id=data['mmr_user']).values('first_name','last_name','email')
                user_List=[x for x in user_data][0]
                user_contact=TCoreUserDetail.objects.filter(id=data['mmr_user']).values('cu_phone_no')
                if user_contact : 
                    user_con_list=[x for x in user_contact][0]
                else:
                    user_con_list = None
                user_dict={
                        'name':user_List['first_name']+" "+user_List['last_name'],
                        'email':user_List['email'],
                        'contact': user_con_list['cu_phone_no'] if  user_con_list else None
                    }
                data['user_details'] = user_dict
        return response

class ManPowerListByDesignationIdWOPaginationView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TMasterModuleRoleUser.objects.filter(mmr_user__isnull=False,mmr_user__is_active=True)
    serializer_class = UserModuleWiseUserListByDesignationIdSerializer
    def get_queryset(self):
        module_id = self.kwargs['module_id']
        designation_id = self.kwargs['designation_id']
        return self.queryset.filter(mmr_module_id=module_id,mmr_designation_id=designation_id)

    @response_modify_decorator_get_after_execution
    def get(self,request, *args, **kwargs):
        user_dict={}
        user_details=[]
        module_id = self.kwargs['module_id']
        designation_id = self.kwargs['designation_id']
        response = super(ManPowerListByDesignationIdWOPaginationView, self).get(self, request, args, kwargs)
        for data in response.data:
            if data['mmr_user']:
                user_data=User.objects.filter(id=data['mmr_user']).values('first_name','last_name','email')
                user_List=[x for x in user_data][0]
                user_contact=TCoreUserDetail.objects.filter(id=data['mmr_user']).values('cu_phone_no')
                if user_contact : 
                    user_con_list=[x for x in user_contact][0]
                else:
                    user_con_list = None
                user_dict={
                        'name':user_List['first_name']+" "+user_List['last_name'],
                        'email':user_List['email'],
                        'contact': user_con_list['cu_phone_no'] if  user_con_list else None
                    }
                data['user_details'] = user_dict
        return response

class ManPowerListDownloadView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    #pagination_class = CSPageNumberPagination
    queryset = TMasterModuleRoleUser.objects.filter(
        mmr_user__isnull=False,
        mmr_user__is_active=True,
        mmr_user__is_superuser=False,
        mmr_is_deleted=False,
        #mmr_type=3,
        mmr_user__in=(
            TCoreUserDetail.objects.filter(
                termination_date__isnull=True,cu_is_deleted=False,attendance_type='PMS').values_list('cu_user',flat=True)))
    serializer_class = UserModuleWiseListSerializer
    def get_queryset(self):
        module_id = self.kwargs['module_id']
        project=self.request.query_params.get('project', None)
        designation=self.request.query_params.get('designation', None)
        #print('designation',designation)
        search=self.request.query_params.get('search', None)
        # print('project',project)
        user_p_list=[]
        designation_details_name=[]

        if search:
            if '@' in search:
                return self.queryset.filter(mmr_module_id=module_id,mmr_user__email__icontains=search)
            elif search.isdigit():
                user_id = TCoreUserDetail.objects.filter(cu_is_deleted=False,cu_phone_no__icontains=search).values('cu_user')
                if user_id:
                    user_id_list = [x['cu_user'] for x in user_id]
                    return self.queryset.filter(mmr_module_id=module_id,mmr_user__in=user_id_list)
                else:
                    return TMasterModuleRoleUser.objects.none()
            else:
                #print("user_name")
                name = search.split(" ")
                #print("name", name)
                if name:
                    queryset_all = TMasterModuleRoleUser.objects.none()
                    queryset = TMasterModuleRoleUser.objects.none()
                    #print("len(name)",len(name))
                    for i in name:
                        queryset = self.queryset.filter(Q(mmr_module_id=module_id) & Q(mmr_user__first_name__icontains=i) |
                                                        Q(mmr_user__last_name__icontains=i))
                        queryset_all = (queryset_all|queryset)
                    return queryset_all.filter(mmr_module_id=module_id)
            

        if project:
            project=project.split(',')
            user_list=PmsProjectUserMapping.objects.filter(project__in=project)
            # print(user_list)
            for u_l in user_list:
                user_p_list.append(u_l.user.id)
            print(user_p_list)
            # return  self.queryset.filter(mmr_module_id=module_id,mmr_user__in=user_p_list)

        if designation:
            designation=designation.split(',')
            desgnation_list=[]
            print(designation)
            for d in designation:
                designation_details_name=TCoreDesignation.objects.filter(cod_name=d).count()
                if designation_details_name:
                    designation_details_name = TCoreDesignation.objects.get(cod_name=d)
                    desgnation_list.append(designation_details_name)
        if user_p_list and designation_details_name:
            queryset=self.queryset.filter(mmr_module_id=module_id,mmr_user__in=user_p_list)
            return queryset.filter(mmr_designation__in =desgnation_list)
        elif user_p_list:
            return  self.queryset.filter(mmr_module_id=module_id,mmr_user__in=user_p_list)
        elif designation_details_name:
            return self.queryset.filter(mmr_module_id=module_id,mmr_designation__in=desgnation_list)
        else:
            return self.queryset.filter(mmr_module_id=module_id)

    def filter_order_by(self, obj):
        return dict(obj)

    def order_by_with_field_name(self, response):
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        ob = True if order_by == 'desc' else False
        # print('response end', response.data)
        if field_name and order_by:
            data_list = list(map(lambda x: dict(x), response.data['results']))
            response.data['results'] = sorted(data_list, key = lambda x: x['mmr_user'][field_name], reverse = ob)


    def get(self, request, *args, **kwargs):
        response = super(ManPowerListDownloadView, self).get(self, request, args, kwargs)
        # print('response', response.data)
        module_id = self.kwargs['module_id']
        data_list = list()
        count = 0
        # print('module_id', module_id)
        # print('module_id', type(module_id))

        

        for data in response.data:

            if data['mmr_user']:
                 
                #print('data:',data['mmr_user'])
                data['designation'] = TCoreUserDetail.objects.filter(
                    cu_user_id=data['mmr_user'], cu_is_deleted=False).values_list('designation__cod_name',flat=True).first()
                #print('designation_details',designation_details)
                 
                # if designation_details:
                #     for e_designation in designation_details:
                #         print('designation',designation.designation)
                        
                #         data['designation'] = designation.designation__cod_name if designation.designation else ""

                employee_details = TCoreUserDetail.objects.filter(cu_user=data['mmr_user'])
                for employee in employee_details:
                    count += 1
                    manpower_dict = {}
                    # print("employee: ", employee.cu_user_id)
                    manpower_dict['employee_id'] = employee.cu_user_id
                    manpower_dict['reporting_head'] = employee.reporting_head.get_full_name() if employee.reporting_head else None
                    manpower_dict['hod'] = employee.hod.get_full_name() if employee.hod else None
                    manpower_dict['employee_code'] = employee.cu_emp_code
                    name = employee.cu_user.first_name + ' ' + employee.cu_user.last_name
                    manpower_dict['employee_name'] = name.strip()
                    manpower_dict['email_id'] = employee.cu_alt_email_id
                    manpower_dict['contact_no'] = employee.cu_phone_no
                    manpower_dict['sap_no'] = employee.sap_personnel_no if employee.sap_personnel_no else ''
                    data['mmr_user'] = manpower_dict
                    project_details = PmsProjectUserMapping.objects.filter(user_id=employee.cu_user_id)
                    projects = []
                    projects_l = ''
                    for project in project_details:
                        # project_data = {
                        #     "id": project.project.id, 
                        #     "name": project.project.name,
                        #     "project_g_id":project.project.project_g_id,
                        #     "start_date":project.start_date,
                        #     "expire_date":project.expire_date
                        #     }
                        # projects.append(project_data)
                        projects_l += project.project.name+',' 
                    #projects_l = ','.join(['{0}'.format(item['item']) for item in projects])

                    #data['project'] = projects

                    data_list.append([
                                count,
                                employee.cu_emp_code,
                                name.strip(),
                                employee.cu_phone_no,
                                employee.cu_alt_email_id,
                                employee.reporting_head.get_full_name() if employee.reporting_head else None,
                                employee.hod.get_full_name() if employee.hod else None,
                                employee.sap_personnel_no if employee.sap_personnel_no else '',
                                projects_l
                                ])



                    # print('mmr_user',data['mmr_user'])
        
        file_name = ''
        if data_list:
            if os.path.isdir('media/pms/manpower/document'):
                file_name = 'media/pms/manpower/document/manpower_report.xlsx'
                file_path = settings.MEDIA_ROOT_EXPORT + file_name
            else:
                os.makedirs('media/pms/manpower/document')
                file_name = 'media/pms/manpower/document/manpower_report.xlsx'
                file_path = settings.MEDIA_ROOT_EXPORT + file_name

            #print('file_path',file_path)

            final_df = pd.DataFrame(
                data_list, 
                columns=[
                'SL No.',
                'Employee Id',
                'Employee Name',
                'Contact No.',
                'Email',
                'Reporting Head',
                'HOD',
                'SAP No.',
                'Projects',
                ]
                )
            writer = pd.ExcelWriter(file_path, engine='xlsxwriter')
            final_df.to_excel(writer, startrow=1, startcol=0,index = False, header=False)
            workbook  = writer.book
            worksheet = writer.sheets['Sheet1']
            style_property_1 = workbook.add_format({'bg_color':'#6495ED','font_color':'white','valign': 'vcenter'})
            header_fmt = workbook.add_format({'bg_color':'#6B8E23','font_color':'white'})
            # Header row color set
            for col_num, value in enumerate(final_df.columns.values):
                worksheet.write(0, col_num, value, header_fmt)

            writer.save()
            url = getHostWithPort(request) + file_name if file_name else None

            if url:                    
                return Response({'request_status':1,'msg':'Success', 'url': url})
            else:
                return Response({'request_status':0,'msg':'Not Found', 'url': url})
 
