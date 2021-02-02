from django.shortcuts import render
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
# from rest_framework.authentication import TokenAuthentication
from users.models import UserTempReportingHeadMap
from hrms.models import *
from hrms.serializers import *
from .serializers import PreJoiningCandidateListSerializer
from pagination import CSLimitOffestpagination, CSPageNumberPagination, OnOffPagination , CustomPagination
from rest_framework.views import APIView
from django.conf import settings
from rest_framework import mixins
from rest_framework import filters
from datetime import datetime, timedelta
import collections
from rest_framework.parsers import FileUploadParser
from django_filters.rest_framework import DjangoFilterBackend
from custom_decorator import *
import os
from custom_exception_message import *
from django.http import JsonResponse
from datetime import datetime
from decimal import Decimal
import pandas as pd
import xlrd
import numpy as np
from django.db.models import Q
from custom_exception_message import *
from decimal import *
import math
from django.contrib.auth.models import *
from django.db.models import F
from django.db.models import Count
from core.models import *
from pms.models import *
import re
from global_function import department, designation
from django.contrib.admin.models import LogEntry
from global_function import userdetails, round_calculation
import time
from django.db.models import Value as V
from django.db.models.functions import Concat
from global_function import getHostWithPort
from employee_leave_calculation import all_leave_calculation_upto_applied_date
from django.contrib.auth import authenticate

'''
    For Knox 
    Author : Rupam Hazra
    Date : 16.03.2020
'''
from knox.auth import TokenAuthentication
from rest_framework import permissions
from knox.models import AuthToken


# Create your views here.

#:::::::::::::::::::::: HRMS BENEFITS PROVIDED:::::::::::::::::::::::::::#
class BenefitsProvidedAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = HrmsBenefitsProvided.objects.all()
    serializer_class = BenefitsProvidedAddSerializer


class BenefitsProvidedEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = HrmsBenefitsProvided.objects.all()
    serializer_class = BenefitsProvidedEditSerializer


class BenefitsProvidedDeleteView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = HrmsBenefitsProvided.objects.all()
    serializer_class = BenefitsProvidedDeleteSerializer


#:::::::::::::::::::::: HRMS QUALIFICATION MASTER:::::::::::::::::::::::::::#
class QualificationMasterAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = HrmsQualificationMaster.objects.filter(is_deleted=False)
    serializer_class = QualificationMasterAddSerializer

    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        return response


class QualificationMasterEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = HrmsQualificationMaster.objects.all()
    serializer_class = QualificationMasterEditSerializer


class QualificationMasterDeleteView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = HrmsQualificationMaster.objects.all()
    serializer_class = QualificationMasterDeleteSerializer


#:::::::::::::::::::::: HRMS EMPLOYEE:::::::::::::::::::::::::::#
class EmployeeAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = User.objects.all()
    serializer_class = EmployeeAddSerializer

    def post(self, request, *args, **kwargs):
        # print('check post...',request.data)
        # username = request.data['username']
        # if User.objects.filter(username=username).count() > 0:
        #     custom_exception_message(self,'Employee Login ID')

        cu_emp_code = request.data['cu_emp_code']
        if TCoreUserDetail.objects.filter(cu_emp_code=cu_emp_code).count() > 0:
            custom_exception_message(self, 'Employee Code')

        cu_phone_no = request.data['cu_phone_no']
        if TCoreUserDetail.objects.filter(cu_phone_no=cu_phone_no).count() > 0:
            custom_exception_message(self, 'Personal Contact No. ')

        sap_personnel_no = request.data['sap_personnel_no']
        # print('sap_personnel_no',sap_personnel_no,type(sap_personnel_no))
        # Added By RUpam Hazra request in form data type
        if sap_personnel_no != 'null':
            if TCoreUserDetail.objects.filter(sap_personnel_no=sap_personnel_no).count() > 0:
                custom_exception_message(self, 'SAP Personnel ID')

        cu_punch_id = request.data['cu_punch_id'] if request.data['cu_punch_id'] else None
        if TCoreUserDetail.objects.filter(cu_punch_id=cu_punch_id).count() > 0:
            custom_exception_message(self, 'Punching Machine Id')

        return super().post(request, *args, **kwargs)


class EmployeeEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = User.objects.all()
    serializer_class = EmployeeEditSerializer

    @response_modify_decorator_update
    def put(self, request, *args, **kwargs):

        # print('request',request.data)

        user_id = self.kwargs['pk']
        # print('user_id',type(user_id))
        list_type = self.request.query_params.get('list_type', None)

        cu_emp_code = request.data['cu_emp_code']
        if TCoreUserDetail.objects.filter(~Q(cu_user=user_id), cu_emp_code=cu_emp_code).count() > 0:
            custom_exception_message(self, 'Employee Code')

        if list_type == "professional":
            sap_personnel_no = request.data['sap_personnel_no']
            if sap_personnel_no != 'null':
                if TCoreUserDetail.objects.filter(~Q(cu_user=user_id), sap_personnel_no=sap_personnel_no).count() > 0:
                    custom_exception_message(self, 'SAP Personnel ID')

            cu_punch_id = request.data['cu_punch_id'] if request.data['cu_punch_id'] else None
            if TCoreUserDetail.objects.filter(~Q(cu_user=user_id), cu_punch_id=cu_punch_id).count() > 0:
                custom_exception_message(self, 'Punching Machine Id')

        if list_type == "personal":
            cu_phone_no = request.data['cu_phone_no']
            if TCoreUserDetail.objects.filter(~Q(cu_user=user_id), cu_phone_no=cu_phone_no).count() > 0:
                custom_exception_message(self, 'Personal Contact No. ')

            email = request.data['email']
            if User.objects.filter(~Q(id=user_id), email=email).count() > 0:
                custom_exception_message(self, 'Personal Email ID')

        if list_type == "role":
            pass
            # cu_alt_phone_no = request.data['cu_alt_phone_no']
            # if TCoreUserDetail.objects.filter(~Q(cu_user=user_id),cu_alt_phone_no=cu_alt_phone_no).count() > 0:
            #     custom_exception_message(self,'Official Contact No.')

            # cu_alt_email_id = request.data['cu_alt_email_id']
            # if TCoreUserDetail.objects.filter(~Q(cu_user=user_id),cu_alt_email_id=cu_alt_email_id).count() > 0:
            #     custom_exception_message(self,'Official Email ID')

        return super().put(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        get_id = self.kwargs['pk']
        list_type = self.request.query_params.get('list_type', None)
        module_id = self.request.query_params.get('module_id', None)
        response = User.objects.filter(id=get_id)
        data = {}
        data_dict = {}
        p_doc_dict = {}
        for user_data in response:
            data['first_name'] = user_data.first_name
            data['last_name'] = user_data.last_name
            if list_type == "professional":
                professional_details = TCoreUserDetail.objects.filter(
                    cu_user=user_data.id, cu_is_deleted=False
                ).values(
                    'cu_emp_code', 'daily_loginTime', 'joining_date',
                    'sap_personnel_no', 'daily_logoutTime', 'cu_punch_id',
                    'initial_ctc', 'current_ctc', 'lunch_start', 'lunch_end', 'salary_type__st_name',
                    'cost_centre', 'granted_cl', 'granted_sl', 'granted_el', 'salary_type', 'is_confirm',
                    'job_location_state', 'cu_alt_email_id')
                if professional_details:
                    data['emp_code'] = professional_details[0]['cu_emp_code'] if professional_details[0][
                        'cu_emp_code'] else None
                    data['cu_punch_id'] = professional_details[0]['cu_punch_id'] if professional_details[0][
                        'cu_punch_id'] else None
                    data['sap_personnel_no'] = professional_details[0]['sap_personnel_no'] if professional_details[0][
                        'sap_personnel_no'] else None
                    data['initial_ctc'] = professional_details[0]['initial_ctc'] if professional_details[0][
                        'initial_ctc'] else None
                    data['current_ctc'] = professional_details[0]['current_ctc'] if professional_details[0][
                        'current_ctc'] else None
                    data['cost_centre'] = professional_details[0]['cost_centre'] if professional_details[0][
                        'cost_centre'] else None
                    data['granted_cl'] = professional_details[0]['granted_cl'] if professional_details[0][
                        'granted_cl'] else None
                    data['granted_sl'] = professional_details[0]['granted_sl'] if professional_details[0][
                        'granted_sl'] else None
                    data['granted_el'] = professional_details[0]['granted_el'] if professional_details[0][
                        'granted_el'] else None
                    data['daily_loginTime'] = professional_details[0]['daily_loginTime'] if professional_details[0][
                        'daily_loginTime'] else None
                    data['daily_logoutTime'] = professional_details[0]['daily_logoutTime'] if professional_details[0][
                        'daily_logoutTime'] else None
                    data['lunch_start'] = professional_details[0]['lunch_start'] if professional_details[0][
                        'lunch_start'] else None
                    data['lunch_end'] = professional_details[0]['lunch_end'] if professional_details[0][
                        'lunch_end'] else None
                    data['joining_date'] = professional_details[0]['joining_date'] if professional_details[0][
                        'joining_date'] else None
                    data['salary_type'] = professional_details[0]['salary_type'] if professional_details[0][
                        'salary_type'] else None
                    data['salary_type_name'] = professional_details[0]['salary_type__st_name'] if \
                    professional_details[0]['salary_type__st_name'] else None
                    data['is_confirm'] = professional_details[0]['is_confirm']
                    data['job_location_state'] = professional_details[0]['job_location_state'] if \
                    professional_details[0]['job_location_state'] else None
                    data['official_email_id'] = professional_details[0]['cu_alt_email_id'] if professional_details[0][
                        'cu_alt_email_id'] else None

                saturday_off = AttendenceSaturdayOffMaster.objects.filter(employee=user_data.id, is_deleted=False)
                # print('saturday_off',saturday_off)
                if saturday_off:
                    for s_o in saturday_off:
                        sat_data = {
                            'id': s_o.id,
                            'first': s_o.first,
                            'second': s_o.second,
                            'third': s_o.third,
                            'fourth': s_o.fourth,
                            'all_s_day': s_o.all_s_day
                        }
                    data['saturday_off'] = sat_data
                else:
                    data['saturday_off'] = None

                user_benefits = HrmsUsersBenefits.objects.filter(user=user_data.id, is_deleted=False)
                benefits_list = []
                if user_benefits:
                    for u_b in user_benefits:
                        benefits = {
                            'id': u_b.id,
                            'benefits': u_b.benefits.id,
                            'benefits_name': u_b.benefits.benefits_name,
                            'allowance': u_b.allowance
                        }
                        benefits_list.append(benefits)
                    data['benefits_provided'] = benefits_list
                else:
                    data['benefits_provided'] = []
                other_facilities = HrmsUsersOtherFacilities.objects.filter(user=user_data.id, is_deleted=False)
                facilities_list = []
                if other_facilities:
                    for o_f in other_facilities:
                        facility = {
                            'id': o_f.id,
                            'other_facilities': o_f.other_facilities
                        }
                        facilities_list.append(facility)
                    data['other_facilities'] = facilities_list
                else:
                    data['other_facilities'] = []

                initial_ctc_dict = {}
                upload_files_dict = {}
                current_ctc_dict = {}
                professional_documents = HrmsDocument.objects.filter(user=user_data.id, is_deleted=False)
                if professional_documents:
                    upload_files_list = []
                    for doc_details in professional_documents:
                        if (doc_details.tab_name).lower() == "professional":
                            if doc_details.__dict__['document'] == "":
                                file_url = ''
                            else:
                                file_url = request.build_absolute_uri(doc_details.document.url)
                            if doc_details.__dict__['document_name'] == "":
                                doc_name = ''
                            else:
                                doc_name = doc_details.document_name
                            if doc_details.field_label == "Initial CTC":
                                initial_ctc_dict = {
                                    'id': doc_details.id,
                                    'document_name': doc_name,
                                    'document': file_url
                                }
                            if doc_details.field_label == "Upload Files":
                                upload_files_dict = {
                                    'id': doc_details.id,
                                    'document_name': doc_name,
                                    'document': file_url
                                }
                                upload_files_list.append(upload_files_dict)
                            if doc_details.field_label == "Current CTC":
                                current_ctc_dict = {
                                    'id': doc_details.id,
                                    'document_name': doc_name,
                                    'document': file_url
                                }
                    data['initial_ctc_doc'] = initial_ctc_dict if initial_ctc_dict else None
                    data['upload_files_doc'] = upload_files_list if upload_files_list else None
                    data['current_ctc_doc'] = current_ctc_dict if current_ctc_dict else None

                else:
                    data['initial_ctc_doc'] = None
                    data['upload_files_doc'] = []
                    data['current_ctc_doc'] = None
            if list_type == "role":
                role_details = TCoreUserDetail.objects.filter(cu_user=user_data.id, cu_is_deleted=False).values(
                    'cu_emp_code', 'cu_alt_phone_no', 'cu_alt_email_id', 'company__id', 'company__coc_name',
                    'job_description', 'hod__id',
                    'hod__first_name', 'hod__last_name', 'joining_date', 'termination_date',
                    'designation__id', 'designation__cod_name', 'department__id', 'department__cd_name',
                    'resignation_date',
                    'job_location_state', 'reporting_head__id', 'reporting_head__first_name',
                    'reporting_head__last_name',
                    'employee_grade__cg_name', 'employee_grade__id', 'is_auto_od', 'sub_department',
                    'sub_department__cd_name', 'attendance_type')
                if role_details:
                    data['emp_code'] = role_details[0]['cu_emp_code'] if role_details[0]['cu_emp_code'] else None
                    data['joining_date'] = role_details[0]['joining_date'] if role_details[0]['joining_date'] else None
                    data['official_contact_no'] = role_details[0]['cu_alt_phone_no'] if role_details[0][
                        'cu_alt_phone_no'] else None
                    data['official_email_id'] = role_details[0]['cu_alt_email_id'] if role_details[0][
                        'cu_alt_email_id'] else None
                    data['company'] = role_details[0]['company__id'] if role_details[0]['company__id'] else None
                    data['company_name'] = role_details[0]['company__coc_name'] if role_details[0][
                        'company__coc_name'] else None
                    data['job_description'] = role_details[0]['job_description'] if role_details[0][
                        'job_description'] else None
                    data['hod_id'] = role_details[0]['hod__id'] if role_details[0]['hod__id'] else None
                    hod__first_name = role_details[0]['hod__first_name'] if role_details[0]['hod__first_name'] else ''
                    hod__last_name = role_details[0]['hod__last_name'] if role_details[0]['hod__last_name'] else ''

                    data['hod'] = hod__first_name + " " + hod__last_name

                    data['designation_id'] = role_details[0]['designation__id'] if role_details[0][
                        'designation__id'] else None
                    data['designation_name'] = role_details[0]['designation__cod_name'] if role_details[0][
                        'designation__cod_name'] else None
                    data['department_id'] = role_details[0]['department__id'] if role_details[0][
                        'department__id'] else None
                    data['department_name'] = role_details[0]['department__cd_name'] if role_details[0][
                        'department__cd_name'] else None

                    data['reporting_head_id'] = role_details[0]['reporting_head__id'] if role_details[0][
                        'reporting_head__id'] else None

                    reporting_head__first_name = role_details[0]['reporting_head__first_name'] if role_details[0][
                        'reporting_head__first_name'] else ''
                    reporting_head__last_name = role_details[0]['reporting_head__last_name'] if role_details[0][
                        'reporting_head__last_name'] else ''
                    data['reporting_head_name'] = reporting_head__first_name + " " + reporting_head__last_name
                    # data['employee_grade_name']=role_details[0]['employee_grade__cg_name'] if role_details[0]['employee_grade__cg_name'] else None
                    # data['employee_grade_id']=role_details[0]['employee_grade__id'] if role_details[0]['employee_grade__id'] else None
                    data['termination_date'] = role_details[0]['termination_date'] if role_details[0][
                        'termination_date'] else None
                    data['resignation_date'] = role_details[0]['resignation_date'] if role_details[0][
                        'resignation_date'] else None
                    data['job_location_state'] = role_details[0]['job_location_state'] if role_details[0][
                        'job_location_state'] else None
                    data['is_auto_od'] = role_details[0]['is_auto_od'] if role_details[0]['is_auto_od'] else False
                    data['sub_department'] = role_details[0]['sub_department'] if role_details[0][
                        'sub_department'] else None
                    data['sub_department_name'] = role_details[0]['sub_department__cd_name'] if role_details[0][
                        'sub_department'] else None
                    data['attendance_type'] = role_details[0]['attendance_type'] if role_details[0][
                        'attendance_type'] else None

                    grade_details = TCoreGrade.objects.filter(id=role_details[0]['employee_grade__id'],
                                                              cg_is_deleted=False)

                    if grade_details:
                        grade_details = \
                        TCoreGrade.objects.filter(id=role_details[0]['employee_grade__id'], cg_is_deleted=False)[0]
                        grade_dict = dict()
                        # print('grade_details',grade_details.id)
                        if grade_details.cg_parent_id != 0:
                            parent = TCoreGrade.objects.filter(id=grade_details.cg_parent_id, cg_is_deleted=False)
                            for p_d in parent:
                                grade_dict['id'] = p_d.id
                                grade_dict['cg_name'] = p_d.cg_name

                            grade_dict['child'] = {
                                "id": grade_details.id,
                                "cg_name": grade_details.cg_name
                            }
                        else:
                            grade_dict['id'] = grade_details.id
                            grade_dict['cg_name'] = grade_details.cg_name
                            grade_dict['child'] = None

                        # print('grade_dict',grade_dict)

                        data['grade_details'] = grade_dict
                    else:
                        data['grade_details'] = None
            if list_type == "personal":
                personal_details = TCoreUserDetail.objects.filter(cu_user=user_data.id, cu_is_deleted=False)
                print('personal_details', personal_details)
                if personal_details:
                    for p_d in personal_details:
                        data['emp_code'] = p_d.cu_emp_code
                        data['cu_phone_no'] = p_d.cu_phone_no if p_d.cu_phone_no else ""
                        data['email'] = p_d.cu_user.email
                        data['address'] = p_d.address
                        data['joining_date'] = p_d.joining_date
                        data['blood_group'] = p_d.blood_group if p_d.blood_group else ''
                        data['photo'] = request.build_absolute_uri(
                            p_d.cu_profile_img.url) if p_d.cu_profile_img else None
                        data['total_experience'] = p_d.total_experience
                        data['job_location_state'] = p_d.job_location_state.id if p_d.job_location_state else None
                        data[
                            'job_location_state_name'] = p_d.job_location_state.cs_state_name if p_d.job_location_state else None
                        data['official_email_id'] = p_d.cu_alt_email_id

                licenses_and_certifications_dict = {}
                work_experience_dict = {}
                add_more_files_dict = {}
                personal_documents = HrmsDynamicSectionFieldLabelDetailsWithDoc.objects.filter(user=user_data.id,
                                                                                               is_deleted=False)
                print("personal_documents", personal_documents)
                if personal_documents:
                    licenses_and_certifications_list = []
                    add_more_files_list = []
                    work_experience_list = []
                    for doc_details in personal_documents:
                        if (doc_details.tab_name).lower() == "personal":
                            if doc_details.__dict__['document'] == "":
                                file_url = ''
                            else:
                                file_url = request.build_absolute_uri(doc_details.document.url)

                            if doc_details.__dict__['document_name'] == "":
                                doc_name = ""
                            else:
                                doc_name = doc_details.document_name

                            if doc_details.field_label == "Licenses and Certifications":
                                licenses_and_certifications_dict = {
                                    'id': doc_details.id,
                                    'field_label_value': doc_details.field_label_value if doc_details.field_label_value else None,
                                    'document_name': doc_name,
                                    'document': file_url
                                }
                                licenses_and_certifications_list.append(licenses_and_certifications_dict)

                            if doc_details.field_label == "Work Experience":
                                work_experience_dict = {
                                    'id': doc_details.id,
                                    'field_label_value': doc_details.field_label_value if doc_details.field_label_value else None,
                                    'document_name': doc_name,
                                    'document': file_url
                                }
                                work_experience_list.append(work_experience_dict)
                    data[
                        'licenses_and_certifications_doc'] = licenses_and_certifications_list if licenses_and_certifications_list else []
                    data['work_experience_doc'] = work_experience_list if work_experience_list else []
                else:
                    data['licenses_and_certifications_doc'] = []
                    data['work_experience_doc'] = []
                academic_qualification = HrmsUserQualification.objects.filter(user=user_data.id, is_deleted=False)
                print('academic_qualification', academic_qualification)
                if academic_qualification:
                    academic_qualification_list = []
                    academic_qualification_dict = {}
                    for a_q in academic_qualification:
                        academic_qualification_dict = {
                            'id': a_q.id,
                            'qualification': a_q.qualification.id,
                            'qualification_name': a_q.qualification.name,
                            'details': a_q.details
                        }
                        academic_doc = HrmsUserQualificationDocument.objects.filter(user_qualification=a_q.id,
                                                                                    is_deleted=False)
                        print('academic_doc', academic_doc)
                        if academic_doc:
                            academic_doc_dict = {}
                            academic_doc_list = []
                            for a_d in academic_doc:
                                academic_doc_dict = {
                                    'id': a_d.id,
                                    'document': request.build_absolute_uri(a_d.document.url)
                                }
                                academic_doc_list.append(academic_doc_dict)
                            academic_qualification_dict['qualification_doc'] = academic_doc_list
                        else:
                            academic_qualification_dict['qualification_doc'] = []
                        academic_qualification_list.append(academic_qualification_dict)
                    data['academic_qualification'] = academic_qualification_list
                else:
                    data['academic_qualification'] = []

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


class EmployeeEditViewV2(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = User.objects.all()
    serializer_class = EmployeeEditSerializerV2

    @response_modify_decorator_update
    def put(self, request, *args, **kwargs):

        ##print('request',request.data)

        user_id = self.kwargs['pk']
        is_transfer = request.data.get('is_transfer', False)
        ##print('user_id',type(user_id))
        list_type = self.request.query_params.get('list_type', None)
        # if not is_transfer:
        #     cu_emp_code = request.data['cu_emp_code']
        #     if TCoreUserDetail.objects.filter(~Q(cu_user=user_id), cu_emp_code=cu_emp_code).count() > 0:
        #         custom_exception_message(self, 'Employee Code')

        if list_type == "professional":
            if request.data['sap_personnel_no']:
                if not is_transfer:
                    sap_personnel_no = request.data['sap_personnel_no']
                    if sap_personnel_no != 'null':
                        if TCoreUserDetail.objects.filter(~Q(cu_user=user_id),
                                                          sap_personnel_no=sap_personnel_no).count() > 0:
                            custom_exception_message(self, 'SAP Personnel ID')

                    cu_punch_id = request.data['cu_punch_id'] if request.data['cu_punch_id'] else None
                    if TCoreUserDetail.objects.filter(~Q(cu_user=user_id), cu_punch_id=cu_punch_id).count() > 0:
                        custom_exception_message(self, 'Punching Machine Id')

        if list_type == "personal":
            cu_phone_no = request.data['cu_phone_no']
            if TCoreUserDetail.objects.filter(~Q(cu_user=user_id), cu_phone_no=cu_phone_no).count() > 0:
                custom_exception_message(self, 'Personal Contact No. ')

            email = request.data['email']
            if User.objects.filter(~Q(id=user_id), email=email).count() > 0:
                custom_exception_message(self, 'Personal Email ID')

        if list_type == "role":
            pass
            # cu_alt_phone_no = request.data['cu_alt_phone_no']
            # if TCoreUserDetail.objects.filter(~Q(cu_user=user_id),cu_alt_phone_no=cu_alt_phone_no).count() > 0:
            #     custom_exception_message(self,'Official Contact No.')

            # cu_alt_email_id = request.data['cu_alt_email_id']
            # if TCoreUserDetail.objects.filter(~Q(cu_user=user_id),cu_alt_email_id=cu_alt_email_id).count() > 0:
            #     custom_exception_message(self,'Official Email ID')

        return super().put(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        get_id = self.kwargs['pk']
        list_type = self.request.query_params.get('list_type', None)
        module_id = self.request.query_params.get('module_id', None)
        response = User.objects.filter(id=get_id)
        data = {}
        data_dict = {}
        p_doc_dict = {}
        for user_data in response:
            data['first_name'] = user_data.first_name
            data['last_name'] = user_data.last_name
            if list_type == "professional":
                professional_details = TCoreUserDetail.objects.filter(
                    cu_user=user_data.id).values(
                    'cu_emp_code', 'daily_loginTime', 'joining_date',
                    'sap_personnel_no', 'daily_logoutTime', 'cu_punch_id', 'company__id', 'company__coc_name',
                    'initial_ctc', 'current_ctc', 'lunch_start', 'lunch_end', 'salary_type__st_name',
                    'cost_centre', 'updated_cost_centre', 'granted_cl', 'granted_sl', 'granted_el', 'salary_type',
                    'is_confirm', 'cu_alt_email_id',
                    'care_of', 'street_and_house_no', 'address_2nd_line', 'city', 'district',
                    'wbs_element', 'retirement_date', 'esic_no', 'esi_dispensary', 'pf_no', 'emp_pension_no',
                    'employee_voluntary_provident_fund_contribution', 'uan_no', 'branch_name', 'bank_account',
                    'ifsc_code', 'bus_facility', 'has_pf', 'has_esi', 'job_location', 'job_location_state',
                    'bank_name_p', 'employee_grade', 'employee_sub_grade', 'file_no')
                # #print('professional_details', professional_details)
                if professional_details:
                    data['is_active'] = user_data.is_active
                    data['emp_code'] = professional_details[0]['cu_emp_code'] if professional_details[0][
                        'cu_emp_code'] else None
                    data['cu_punch_id'] = professional_details[0]['cu_punch_id'] if professional_details[0][
                        'cu_punch_id'] else None
                    data['sap_personnel_no'] = professional_details[0]['sap_personnel_no'] if professional_details[0][
                        'sap_personnel_no'] else None
                    data['initial_ctc'] = professional_details[0]['initial_ctc'] if professional_details[0][
                        'initial_ctc'] else None
                    data['current_ctc'] = professional_details[0]['current_ctc'] if professional_details[0][
                        'current_ctc'] else None
                    # data['cost_centre']=professional_details[0]['cost_centre'] if professional_details[0]['cost_centre'] else None
                    data['granted_cl'] = professional_details[0]['granted_cl'] if professional_details[0][
                        'granted_cl'] else None
                    data['granted_sl'] = professional_details[0]['granted_sl'] if professional_details[0][
                        'granted_sl'] else None
                    data['granted_el'] = professional_details[0]['granted_el'] if professional_details[0][
                        'granted_el'] else None
                    data['daily_loginTime'] = professional_details[0]['daily_loginTime'] if professional_details[0][
                        'daily_loginTime'] else None
                    data['daily_logoutTime'] = professional_details[0]['daily_logoutTime'] if professional_details[0][
                        'daily_logoutTime'] else None
                    data['lunch_start'] = professional_details[0]['lunch_start'] if professional_details[0][
                        'lunch_start'] else None
                    data['lunch_end'] = professional_details[0]['lunch_end'] if professional_details[0][
                        'lunch_end'] else None
                    data['joining_date'] = professional_details[0]['joining_date'] if professional_details[0][
                        'joining_date'] else None
                    data['salary_type'] = professional_details[0]['salary_type'] if professional_details[0][
                        'salary_type'] else None
                    data['salary_type_name'] = professional_details[0]['salary_type__st_name'] if \
                    professional_details[0]['salary_type__st_name'] else None
                    data['is_confirm'] = professional_details[0]['is_confirm']
                    data['official_email_id'] = professional_details[0]['cu_alt_email_id'] if professional_details[0][
                        'cu_alt_email_id'] else None

                    data['wbs_element'] = professional_details[0]['wbs_element'] if professional_details[0][
                        'wbs_element'] else None
                    data['retirement_date'] = professional_details[0]['retirement_date'] if professional_details[0][
                        'retirement_date'] else None
                    data['esic_no'] = professional_details[0]['esic_no'] if professional_details[0]['esic_no'] else None
                    data['esi_dispensary'] = professional_details[0]['esi_dispensary'] if professional_details[0][
                        'esi_dispensary'] else None
                    data['pf_no'] = professional_details[0]['pf_no'] if professional_details[0]['pf_no'] else None
                    data['emp_pension_no'] = professional_details[0]['emp_pension_no'] if professional_details[0][
                        'emp_pension_no'] else None
                    data['employee_voluntary_provident_fund_contribution'] = professional_details[0][
                        'employee_voluntary_provident_fund_contribution'] if professional_details[0][
                        'employee_voluntary_provident_fund_contribution'] else None
                    data['company'] = professional_details[0]['company__id'] if professional_details[0][
                        'company__id'] else None
                    data['company_name'] = professional_details[0]['company__coc_name'] if professional_details[0][
                        'company__coc_name'] else None
                    data['uan_no'] = professional_details[0]['uan_no'] if professional_details[0]['uan_no'] else None
                    data['branch_name'] = professional_details[0]['branch_name'] if professional_details[0][
                        'branch_name'] else None
                    data['bank_account'] = professional_details[0]['bank_account'] if professional_details[0][
                        'bank_account'] else None
                    data['ifsc_code'] = professional_details[0]['ifsc_code'] if professional_details[0][
                        'ifsc_code'] else None
                    data['file_no'] = professional_details[0]['file_no'] if professional_details[0]['file_no'] else None
                    data['bus_facility'] = professional_details[0]['bus_facility']

                    # 'has_pf','has_esi','job_location_state','bank_name_p'
                    data['has_pf'] = professional_details[0]['has_pf']
                    data['has_esi'] = professional_details[0]['has_esi']
                    data['job_location'] = professional_details[0]['job_location']
                    data['job_location_state'] = professional_details[0]['job_location_state']
                    job_location_state_name = TCoreState.objects.filter(
                        id=professional_details[0]['job_location_state']).first()
                    data[
                        'job_location_state_name'] = job_location_state_name.cs_state_name if job_location_state_name else None
                    data['bank_name_p'] = professional_details[0]['bank_name_p']
                    bank_name = TCoreBank.objects.filter(id=professional_details[0]['bank_name_p']).first()
                    data['bank_name'] = bank_name.name if bank_name else None
                    if professional_details[0]['updated_cost_centre']:
                        cc_obj = TCoreCompanyCostCentre.objects.filter(
                            id=professional_details[0]['updated_cost_centre'])
                        if cc_obj:
                            data['cost_centre'] = cc_obj[0].cost_centre_name
                            data['cost_centre_id'] = cc_obj[0].id
                        else:
                            data['cost_centre'] = professional_details[0]['cost_centre'] if professional_details[0][
                                'cost_centre'] else None
                            data['cost_centre_id'] = None
                    elif professional_details[0]['cost_centre']:
                        data['cost_centre'] = professional_details[0]['cost_centre'] if professional_details[0][
                            'cost_centre'] else None
                        data['cost_centre_id'] = None
                    else:
                        data['cost_centre'] = None
                        data['cost_centre_id'] = None

                    if professional_details[0]['employee_grade']:
                        grade = TCoreGrade.objects.get(id=professional_details[0]['employee_grade'])
                        data['grade'] = grade.cg_name
                    else:
                        data['grade'] = ""

                    if professional_details[0]['employee_sub_grade']:
                        sub_grade = TCoreSubGrade.objects.get(id=professional_details[0]['employee_sub_grade'])
                        data['sub_grade'] = sub_grade.name
                    else:
                        data['sub_grade'] = ""

                saturday_off = AttendenceSaturdayOffMaster.objects.filter(employee=user_data.id, is_deleted=False)
                ##print('saturday_off',saturday_off)
                if saturday_off:
                    for s_o in saturday_off:
                        sat_data = {
                            'id': s_o.id,
                            'first': s_o.first,
                            'second': s_o.second,
                            'third': s_o.third,
                            'fourth': s_o.fourth,
                            'all_s_day': s_o.all_s_day
                        }
                    data['saturday_off'] = sat_data
                else:
                    data['saturday_off'] = None

                user_benefits = HrmsUsersBenefits.objects.filter(user=user_data.id, is_deleted=False)
                # user_benefits = 0
                benefits_list = []
                if user_benefits:
                    for u_b in user_benefits:
                        benefits = {
                            'id': u_b.id,
                            'benefits': u_b.benefits.id,
                            'benefits_name': u_b.benefits.benefits_name,
                            'allowance': u_b.allowance
                        }
                        benefits_list.append(benefits)
                    data['benefits_provided'] = benefits_list
                else:
                    data['benefits_provided'] = []
                other_facilities = HrmsUsersOtherFacilities.objects.filter(user=user_data.id, is_deleted=False)
                facilities_list = []
                if other_facilities:
                    for o_f in other_facilities:
                        facility = {
                            'id': o_f.id,
                            'other_facilities': o_f.other_facilities
                        }
                        facilities_list.append(facility)
                    data['other_facilities'] = facilities_list
                else:
                    data['other_facilities'] = []

                initial_ctc_dict = {}
                upload_files_dict = {}
                current_ctc_dict = {}
                professional_documents = HrmsDocument.objects.filter(user=user_data.id, is_deleted=False)
                if professional_documents:
                    upload_files_list = []
                    for doc_details in professional_documents:
                        if (doc_details.tab_name).lower() == "professional":
                            if doc_details.__dict__['document'] == "":
                                file_url = ''
                            else:
                                file_url = request.build_absolute_uri(doc_details.document.url)
                            if doc_details.__dict__['document_name'] == "":
                                doc_name = ''
                            else:
                                doc_name = doc_details.document_name
                            if doc_details.field_label == "Initial CTC":
                                initial_ctc_dict = {
                                    'id': doc_details.id,
                                    'document_name': doc_name,
                                    'document': file_url
                                }
                            if doc_details.field_label == "Upload Files":
                                upload_files_dict = {
                                    'id': doc_details.id,
                                    'document_name': doc_name,
                                    'document': file_url
                                }
                                upload_files_list.append(upload_files_dict)
                            if doc_details.field_label == "Current CTC":
                                current_ctc_dict = {
                                    'id': doc_details.id,
                                    'document_name': doc_name,
                                    'document': file_url
                                }
                    data['initial_ctc_doc'] = initial_ctc_dict if initial_ctc_dict else None
                    data['upload_files_doc'] = upload_files_list if upload_files_list else None
                    data['current_ctc_doc'] = current_ctc_dict if current_ctc_dict else None

                else:
                    data['initial_ctc_doc'] = None
                    data['upload_files_doc'] = []
                    data['current_ctc_doc'] = None
            if list_type == "role":
                role_details = TCoreUserDetail.objects.filter(cu_user=user_data.id).values(
                    'cu_emp_code', 'cu_phone_no', 'cu_alt_phone_no', 'cu_alt_email_id', 'company__id',
                    'company__coc_name', 'job_description', 'hod__id',
                    'hod__first_name', 'hod__last_name', 'joining_date', 'termination_date', 'cost_centre',
                    'updated_cost_centre',
                    'designation__id', 'designation__cod_name', 'department__id', 'department__cd_name',
                    'resignation_date',
                    'job_location_state', 'reporting_head__id', 'reporting_head__first_name',
                    'reporting_head__last_name',
                    'employee_grade__cg_name', 'employee_grade__id', 'employee_sub_grade', 'is_auto_od',
                    'sub_department', 'sub_department__cd_name', 'attendance_type',
                    'is_flexi_hour', 'file_no')
                if role_details:
                    data['is_active'] = user_data.is_active
                    data['emp_code'] = role_details[0]['cu_emp_code'] if role_details[0]['cu_emp_code'] else None
                    data['joining_date'] = role_details[0]['joining_date'] if role_details[0]['joining_date'] else None
                    data['personal_contact_no'] = role_details[0]['cu_phone_no'] if role_details[0][
                        'cu_phone_no'] else None
                    data['official_contact_no'] = role_details[0]['cu_alt_phone_no'] if role_details[0][
                        'cu_alt_phone_no'] else None
                    data['official_email_id'] = role_details[0]['cu_alt_email_id'] if role_details[0][
                        'cu_alt_email_id'] else None
                    data['company'] = role_details[0]['company__id'] if role_details[0]['company__id'] else None
                    data['company_name'] = role_details[0]['company__coc_name'] if role_details[0][
                        'company__coc_name'] else None
                    data['job_description'] = role_details[0]['job_description'] if role_details[0][
                        'job_description'] else None
                    data['hod_id'] = role_details[0]['hod__id'] if role_details[0]['hod__id'] else None
                    data['file_no'] = role_details[0]['file_no'] if role_details[0]['file_no'] else None
                    hod__first_name = role_details[0]['hod__first_name'] if role_details[0]['hod__first_name'] else ''
                    hod__last_name = role_details[0]['hod__last_name'] if role_details[0]['hod__last_name'] else ''

                    data['hod'] = hod__first_name + " " + hod__last_name

                    data['designation_id'] = role_details[0]['designation__id'] if role_details[0][
                        'designation__id'] else None
                    data['designation_name'] = role_details[0]['designation__cod_name'] if role_details[0][
                        'designation__cod_name'] else None
                    data['department_id'] = role_details[0]['department__id'] if role_details[0][
                        'department__id'] else None
                    data['department_name'] = role_details[0]['department__cd_name'] if role_details[0][
                        'department__cd_name'] else None

                    data['reporting_head_id'] = role_details[0]['reporting_head__id'] if role_details[0][
                        'reporting_head__id'] else None

                    reporting_head__first_name = role_details[0]['reporting_head__first_name'] if role_details[0][
                        'reporting_head__first_name'] else ''
                    reporting_head__last_name = role_details[0]['reporting_head__last_name'] if role_details[0][
                        'reporting_head__last_name'] else ''
                    data['reporting_head_name'] = reporting_head__first_name + " " + reporting_head__last_name

                    # data['temp_reporting_head_id']=role_details[0]['temp_reporting_head__id'] if role_details[0]['temp_reporting_head__id'] else None

                    # temp_reporting_head__first_name = role_details[0]['temp_reporting_head__first_name'] if role_details[0]['temp_reporting_head__first_name'] else ''
                    # temp_reporting_head__last_name = role_details[0]['temp_reporting_head__last_name'] if role_details[0]['temp_reporting_head__last_name'] else ''
                    # data['temp_reporting_head_name']= temp_reporting_head__first_name  +" "+ temp_reporting_head__last_name

                    temp_reporting_heads = UserTempReportingHeadMap.objects.filter(user=user_data,
                                                                                   is_deleted=False).values(
                        'temp_reporting_head__id', 'temp_reporting_head__first_name', 'temp_reporting_head__last_name')
                    data['temp_reporting_heads'] = temp_reporting_heads

                    # data['employee_grade_name']=role_details[0]['employee_grade__cg_name'] if role_details[0]['employee_grade__cg_name'] else None
                    # data['employee_grade_id']=role_details[0]['employee_grade__id'] if role_details[0]['employee_grade__id'] else None
                    data['termination_date'] = role_details[0]['termination_date'] if role_details[0][
                        'termination_date'] else None
                    data['resignation_date'] = role_details[0]['resignation_date'] if role_details[0][
                        'resignation_date'] else None
                    data['job_location_state'] = role_details[0]['job_location_state'] if role_details[0][
                        'job_location_state'] else None
                    data['is_auto_od'] = role_details[0]['is_auto_od'] if role_details[0]['is_auto_od'] else False
                    data['sub_department'] = role_details[0]['sub_department'] if role_details[0][
                        'sub_department'] else None
                    data['sub_department_name'] = role_details[0]['sub_department__cd_name'] if role_details[0][
                        'sub_department'] else None
                    data['attendance_type'] = role_details[0]['attendance_type'] if role_details[0][
                        'attendance_type'] else None
                    data['is_flexi_hour'] = role_details[0]['is_flexi_hour']
                    if role_details[0]['updated_cost_centre']:
                        cc_obj = TCoreCompanyCostCentre.objects.filter(id=role_details[0]['updated_cost_centre'])
                        if cc_obj:
                            data['cost_centre'] = cc_obj[0].cost_centre_name
                            data['cost_centre_id'] = cc_obj[0].id
                        else:
                            data['cost_centre'] = role_details[0]['cost_centre'] if role_details[0][
                                'cost_centre'] else None
                            data['cost_centre_id'] = None
                    elif role_details[0]['cost_centre']:
                        data['cost_centre'] = role_details[0]['cost_centre'] if role_details[0][
                            'cost_centre'] else None
                        data['cost_centre_id'] = None
                    else:
                        data['cost_centre'] = None
                        data['cost_centre_id'] = None

                    if role_details[0]['employee_sub_grade']:
                        sub_grade = TCoreSubGrade.objects.get(id=role_details[0]['employee_sub_grade'])
                        data['sub_grade'] = sub_grade.name
                        data['sub_grade_id'] = sub_grade.id
                    else:
                        data['sub_grade'] = ""
                        data['sub_grade_id'] = ""

                    grade_details = TCoreGrade.objects.filter(id=role_details[0]['employee_grade__id'],
                                                              cg_is_deleted=False)

                    if grade_details:
                        grade_details = \
                        TCoreGrade.objects.filter(id=role_details[0]['employee_grade__id'], cg_is_deleted=False)[0]
                        grade_dict = dict()
                        ##print('grade_details',grade_details.id)
                        if grade_details.cg_parent_id != 0:
                            parent = TCoreGrade.objects.filter(id=grade_details.cg_parent_id, cg_is_deleted=False)
                            for p_d in parent:
                                grade_dict['id'] = p_d.id
                                grade_dict['cg_name'] = p_d.cg_name

                            grade_dict['child'] = {
                                "id": grade_details.id,
                                "cg_name": grade_details.cg_name
                            }
                        else:
                            grade_dict['id'] = grade_details.id
                            grade_dict['cg_name'] = grade_details.cg_name
                            grade_dict['child'] = None

                        ##print('grade_dict',grade_dict)

                        data['grade_details'] = grade_dict
                    else:
                        data['grade_details'] = None
            if list_type == "personal":
                personal_details = TCoreUserDetail.objects.filter(cu_user=user_data.id)
                # print('personal_details',personal_details)
                if personal_details:
                    for p_d in personal_details:
                        data['is_active'] = user_data.is_active
                        data['emp_code'] = p_d.cu_emp_code
                        data['cu_phone_no'] = p_d.cu_phone_no if p_d.cu_phone_no else ""
                        data['file_no'] = p_d.file_no if p_d.file_no else ""
                        data['email'] = p_d.cu_user.email
                        data['address'] = p_d.address
                        data['joining_date'] = p_d.joining_date
                        data['cu_dob'] = p_d.cu_dob
                        data['blood_group'] = p_d.blood_group if p_d.blood_group else ''
                        data['photo'] = request.build_absolute_uri(
                            p_d.cu_profile_img.url) if p_d.cu_profile_img else None
                        data['total_experience'] = p_d.total_experience
                        data['job_location_state'] = p_d.job_location_state.id if p_d.job_location_state else None
                        data[
                            'job_location_state_name'] = p_d.job_location_state.cs_state_name if p_d.job_location_state else None
                        data['official_email_id'] = p_d.cu_alt_email_id

                        data['care_of'] = p_d.care_of
                        data['street_and_house_no'] = p_d.street_and_house_no
                        data['address_2nd_line'] = p_d.address_2nd_line
                        data['city'] = p_d.city
                        data['district'] = p_d.district

                        data['aadhar_no'] = p_d.aadhar_no
                        data['pan_no'] = p_d.pan_no
                        data['cu_gender'] = p_d.cu_gender
                        data['pincode'] = p_d.pincode
                        data['emergency_relationship'] = p_d.emergency_relationship
                        data['emergency_contact_no'] = p_d.emergency_contact_no
                        data['emergency_contact_name'] = p_d.emergency_contact_name
                        data['marital_status'] = p_d.marital_status
                        data['father_name'] = p_d.father_name
                        data['state'] = p_d.state.id if p_d.state else None
                        data['state_name'] = p_d.state.cs_state_name if p_d.state else None

                licenses_and_certifications_dict = {}
                work_experience_dict = {}
                add_more_files_dict = {}
                other_documents_dict = {}

                personal_documents = HrmsDynamicSectionFieldLabelDetailsWithDoc.objects.filter(user=user_data.id,
                                                                                               is_deleted=False)
                # print("personal_documents",personal_documents)
                if personal_documents:
                    licenses_and_certifications_list = []
                    add_more_files_list = []
                    work_experience_list = []
                    other_documents_list = []
                    for doc_details in personal_documents:
                        if (doc_details.tab_name).lower() == "personal":
                            if doc_details.__dict__['document'] == "":
                                file_url = ''
                            else:
                                file_url = request.build_absolute_uri(doc_details.document.url)

                            if doc_details.__dict__['document_name'] == "":
                                doc_name = ""
                            else:
                                doc_name = doc_details.document_name

                            if doc_details.field_label == "Licenses and Certifications":
                                licenses_and_certifications_dict = {
                                    'id': doc_details.id,
                                    'field_label_value': doc_details.field_label_value if doc_details.field_label_value else None,
                                    'document_name': doc_name,
                                    'document': file_url
                                }
                                licenses_and_certifications_list.append(licenses_and_certifications_dict)

                            if doc_details.field_label == "Work Experience":
                                work_experience_dict = {
                                    'id': doc_details.id,
                                    'field_label_value': doc_details.field_label_value if doc_details.field_label_value else None,
                                    'document_name': doc_name,
                                    'document': file_url
                                }
                                work_experience_list.append(work_experience_dict)

                            if doc_details.field_label == "Other Documents":
                                other_documents_dict = {
                                    'id': doc_details.id,
                                    'field_label_value': doc_details.field_label_value if doc_details.field_label_value else None,
                                    'document_name': doc_name,
                                    'document': file_url
                                }
                                other_documents_list.append(other_documents_dict)

                    data[
                        'licenses_and_certifications_doc'] = licenses_and_certifications_list if licenses_and_certifications_list else []
                    data['work_experience_doc'] = work_experience_list if work_experience_list else []
                    data['other_documents_list'] = other_documents_list if other_documents_list else []

                else:
                    data['licenses_and_certifications_doc'] = []
                    data['work_experience_doc'] = []
                    data['other_documents_list'] = []

                academic_qualification = HrmsUserQualification.objects.filter(user=user_data.id, is_deleted=False)
                # print('academic_qualification',academic_qualification)
                if academic_qualification:
                    academic_qualification_list = []
                    academic_qualification_dict = {}
                    for a_q in academic_qualification:

                        academic_qualification_dict = {
                            'id': a_q.id,
                            'qualification': a_q.qualification.id if a_q.qualification else '',
                            'qualification_name': a_q.qualification.name if a_q.qualification else '',
                            'details': a_q.details if a_q.details else ''
                        }
                        academic_doc = HrmsUserQualificationDocument.objects.filter(user_qualification=a_q.id,
                                                                                    is_deleted=False)
                        # print('academic_doc',academic_doc)
                        if academic_doc:
                            academic_doc_dict = {}
                            academic_doc_list = []
                            for a_d in academic_doc:
                                academic_doc_dict = {
                                    'id': a_d.id,
                                    'document': request.build_absolute_uri(a_d.document.url) if a_d.document else ''
                                }
                                academic_doc_list.append(academic_doc_dict)
                            academic_qualification_dict['qualification_doc'] = academic_doc_list
                        else:
                            academic_qualification_dict['qualification_doc'] = []
                        academic_qualification_list.append(academic_qualification_dict)
                    data['academic_qualification'] = academic_qualification_list
                else:
                    data['academic_qualification'] = []

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


class EmployeeListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = User.objects.filter(is_superuser=False, is_active=True).order_by('-id')
    serializer_class = EmployeeListSerializer
    pagination_class = CSPageNumberPagination

    def get_queryset(self):
        '''
            eleminate login user on employee list added by Rupam Hazra Line number 458 - 459
        '''
        login_user = self.request.user.id
        # self.queryset = self.queryset.filter(
        #     ~Q(pk=login_user),
        #     pk__in=(TMasterModuleRoleUser.objects.filter(mmr_type='3')))
        self.queryset = self.queryset.filter(
            ~Q(pk=login_user), is_active=True)
        filter = {}
        # name = self.request.query_params.get('name', None)
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        search_keyword = self.request.query_params.get('search_keyword', None)

        '''
            Reason : Fetch Resignation employee list with date range
            Author : Rupam Hazra 
            Line number:  494 - 503
            Date : 19/02/2020
            Modify Date : 06/03/2020

        '''
        list_type = self.request.query_params.get('list_type', None)
        if list_type == 'resignation':
            from_date = self.request.query_params.get('from_date', None)
            to_date = self.request.query_params.get('to_date', None)
            # is_active and cu_is_deleted flag removed by Shubhadeep (08-09-2020)
            self.queryset = self.queryset.filter(
                ~Q(pk=login_user), id__in=(
                    TCoreUserDetail.objects.filter(
                        resignation_date__gte=from_date,
                        resignation_date__lte=to_date).values_list('cu_user', flat=True)))

        '''
            Reason : Fetch Release employee list with date range
            Author : Rupam Hazra 
            Line number:  515 - 523
            Date : 19/02/2020
            Modify Date : 06/03/2020

        '''
        if list_type == 'release':
            # is_active and cu_is_deleted flag removed by Shubhadeep (08-09-2020)
            from_date = self.request.query_params.get('from_date', None)
            to_date = self.request.query_params.get('to_date', None)
            self.queryset = self.queryset.filter(
                ~Q(pk=login_user), id__in=(
                    TCoreUserDetail.objects.filter(
                        termination_date__gte=from_date,
                        termination_date__lte=to_date).values_list('cu_user', flat=True)))

        '''
            Reason : Fetch employee list by user type with date range
            Author : Rupam Hazra 
            Line number:  532 - 537
            Date : 19/02/2020
            Modify Date : 06/03/2020

        '''

        if list_type == 'employee-list-by-type':
            which_type = self.request.query_params.get('which_type', None)
            self.queryset = self.queryset.filter(
                ~Q(pk=login_user), is_active=True, id__in=(
                    TCoreUserDetail.objects.filter(user_type=which_type, cu_is_deleted=False
                                                   ).values_list('cu_user', flat=True)))

        if field_name and order_by:
            # print('sfsffsfsfff')
            if field_name == 'email' and order_by == 'asc':
                return self.queryset.all().order_by('email')

            if field_name == 'email' and order_by == 'desc':
                return self.queryset.all().order_by('-email')

            if field_name == 'name' and order_by == 'asc':
                return self.queryset.all().order_by('first_name')

            if field_name == 'name' and order_by == 'desc':
                return self.queryset.all().order_by('-first_name')

            if field_name == 'grade' and order_by == 'asc':
                # print('user_grade_asc',order_by)
                user_grade = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('employee_grade__cg_name')
                # print('user_grade',user_grade)
                grade_list = []
                for u_g in user_grade:
                    grade_id = u_g.employee_grade.id if u_g.employee_grade else None
                    grade_list.append(grade_id)
                # print('grade_list',grade_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(grade_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=grade_list).extra(
                    select={'ordering': ordering}, order_by=('ordering',)
                )
                # print('queryset',queryset)
                return queryset

            if field_name == 'grade' and order_by == 'desc':
                # print('user_grade',order_by)
                user_grade = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('-employee_grade__cg_name')
                # print('user_grade_desc',user_grade)
                grade_list = []
                for u_g in user_grade:
                    grade_id = u_g.employee_grade.id if u_g.employee_grade else None
                    grade_list.append(grade_id)
                # print('grade_list',grade_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(grade_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=grade_list).extra(select={'ordering': ordering},
                                                                         order_by=('ordering',))
                # print('queryset',queryset)
                return queryset

            if field_name == 'designation' and order_by == 'desc':
                # print('user_grade',order_by)
                user_designation = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('-designation__cod_name')
                # print('user_designation_desc',user_designation)
                designation_list = []
                for u_g in user_designation:
                    designation_id = u_g.cu_user.id
                    designation_list.append(designation_id)
                # print('designation_list',designation_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(designation_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=designation_list).extra(select={'ordering': ordering},
                                                                               order_by=('ordering',))
                # print('queryset',queryset)
                return queryset

            if field_name == 'designation' and order_by == 'asc':
                # print('user_grade',order_by)
                user_designation = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('designation__cod_name')
                # print('user_designation_desc',user_designation)
                designation_list = []
                for u_g in user_designation:
                    designation_id = u_g.cu_user.id
                    designation_list.append(designation_id)
                # print('designation_list',designation_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(designation_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=designation_list).extra(select={'ordering': ordering},
                                                                               order_by=('ordering',))
                # print('queryset',queryset)
                return queryset

            if field_name == 'department' and order_by == 'asc':
                # print('user_department',order_by)
                user_department = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('department__cd_name')
                # print('user_department_asc',user_department)
                department_list = []
                for u_g in user_department:
                    department_id = u_g.cu_user.id
                    department_list.append(department_id)
                # print('department_list',department_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(department_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=department_list).extra(select={'ordering': ordering},
                                                                              order_by=('ordering',))
                # print('queryset',queryset)
                return queryset

            if field_name == 'department' and order_by == 'desc':
                # print('user_department',order_by)
                user_department = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('-department__cd_name')
                # print('user_department_asc',user_department)
                department_list = []
                for u_g in user_department:
                    department_id = u_g.cu_user.id
                    department_list.append(department_id)
                # print('department_list',department_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(department_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=department_list).extra(select={'ordering': ordering},
                                                                              order_by=('ordering',))
                # print('queryset',queryset)
                return queryset

            if field_name == 'company' and order_by == 'desc':
                # print('user_department',order_by)
                user_company = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('-company__coc_name')
                # print('user_company_asc',user_company)
                company_list = []
                for u_g in user_company:
                    company_id = u_g.cu_user.id
                    company_list.append(company_id)
                # print('company_list',company_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(company_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=company_list).extra(select={'ordering': ordering},
                                                                           order_by=('ordering',))
                # print('queryset',queryset)
                return queryset

            if field_name == 'company' and order_by == 'asc':
                # print('user_department',order_by)
                user_company = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('company__coc_name')
                # print('user_company_asc',user_company)
                company_list = []
                for u_g in user_company:
                    company_id = u_g.cu_user.id
                    company_list.append(company_id)
                # print('company_list',company_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(company_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=company_list).extra(select={'ordering': ordering},
                                                                           order_by=('ordering',))
                # print('queryset',queryset)
                return queryset

            if field_name == 'sap_no' and order_by == 'asc':
                # print('user_department',order_by)
                user_sap_no_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('sap_personnel_no')
                # print('user_sap_no_details_asc',user_sap_no_details)
                sap_no_details_list = []
                for u_g in user_sap_no_details:
                    sap_no_details_id = u_g.cu_user.id
                    sap_no_details_list.append(sap_no_details_id)
                # print('sap_no_details_list',sap_no_details_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(sap_no_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=sap_no_details_list).extra(select={'ordering': ordering},
                                                                                  order_by=('ordering',))
                # print('queryset',queryset)
                return queryset

            if field_name == 'sap_no' and order_by == 'desc':
                # print('user_department',order_by)
                user_sap_no_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('-sap_personnel_no')
                # print('user_sap_no_details_asc',user_sap_no_details)
                sap_no_details_list = []
                for u_g in user_sap_no_details:
                    sap_no_details_id = u_g.cu_user.id
                    sap_no_details_list.append(sap_no_details_id)
                # print('sap_no_details_list',sap_no_details_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(sap_no_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=sap_no_details_list).extra(select={'ordering': ordering},
                                                                                  order_by=('ordering',))
                # print('queryset',queryset)
                return queryset

            if field_name == 'initial_ctc' and order_by == 'desc':
                # print('user_department',order_by)
                user_initial_ctc_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('-initial_ctc')
                # print('user_initial_ctc_details_asc',user_initial_ctc_details)
                initial_ctc_details_list = []
                for u_g in user_initial_ctc_details:
                    initial_ctc_details_id = u_g.cu_user.id
                    initial_ctc_details_list.append(initial_ctc_details_id)
                # print('initial_ctc_details_list',initial_ctc_details_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(initial_ctc_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=initial_ctc_details_list).extra(select={'ordering': ordering},
                                                                                       order_by=('ordering',))
                # print('queryset',queryset)
                return queryset

            if field_name == 'initial_ctc' and order_by == 'asc':
                # print('user_department',order_by)
                user_initial_ctc_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('initial_ctc')
                # print('user_initial_ctc_details_asc',user_initial_ctc_details)
                initial_ctc_details_list = []
                for u_g in user_initial_ctc_details:
                    initial_ctc_details_id = u_g.cu_user.id
                    initial_ctc_details_list.append(initial_ctc_details_id)
                # print('initial_ctc_details_list',initial_ctc_details_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(initial_ctc_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=initial_ctc_details_list).extra(select={'ordering': ordering},
                                                                                       order_by=('ordering',))
                # print('queryset',queryset)
                return queryset

            if field_name == 'current_ctc' and order_by == 'desc':
                # print('user_department',order_by)
                user_current_ctc_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('-current_ctc')
                # print('user_current_ctc_details_asc',user_current_ctc_details)
                current_ctc_details_list = []
                for u_g in user_current_ctc_details:
                    current_ctc_details_id = u_g.cu_user.id
                    current_ctc_details_list.append(current_ctc_details_id)
                # print('current_ctc_details_list',current_ctc_details_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(current_ctc_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=current_ctc_details_list).extra(select={'ordering': ordering},
                                                                                       order_by=('ordering',))
                # print('queryset',queryset)
                return queryset

            if field_name == 'current_ctc' and order_by == 'asc':
                # print('user_department',order_by)
                user_current_ctc_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('current_ctc')
                # print('user_current_ctc_details_asc',user_current_ctc_details)
                current_ctc_details_list = []
                for u_g in user_current_ctc_details:
                    current_ctc_details_id = u_g.cu_user.id
                    current_ctc_details_list.append(current_ctc_details_id)
                # print('current_ctc_details_list',current_ctc_details_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(current_ctc_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=current_ctc_details_list).extra(select={'ordering': ordering},
                                                                                       order_by=('ordering',))
                # print('queryset',queryset)
                return queryset

            if field_name == 'granted_cl' and order_by == 'asc':
                # print('user_department',order_by)
                user_granted_cl_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('current_ctc')
                # print('user_current_ctc_details_asc',user_granted_cl_details)
                granted_cl_details_list = []
                for u_g in user_granted_cl_details:
                    granted_cl_details_id = u_g.cu_user.id
                    granted_cl_details_list.append(granted_cl_details_id)
                # print('current_ctc_details_list',granted_cl_details_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(granted_cl_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=granted_cl_details_list).extra(select={'ordering': ordering},
                                                                                      order_by=('ordering',))
                # print('queryset',queryset)
                return queryset

            if field_name == 'granted_cl' and order_by == 'desc':
                # print('user_department',order_by)
                user_granted_cl_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('-granted_cl')
                # print('user_current_ctc_details_asc',user_granted_cl_details)
                granted_cl_details_list = []
                for u_g in user_granted_cl_details:
                    granted_cl_details_id = u_g.cu_user.id
                    granted_cl_details_list.append(granted_cl_details_id)
                # print('current_ctc_details_list',granted_cl_details_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(granted_cl_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=granted_cl_details_list).extra(select={'ordering': ordering},
                                                                                      order_by=('ordering',))
                # print('queryset',queryset)
                return queryset

            if field_name == 'granted_sl' and order_by == 'desc':
                # print('user_department',order_by)
                user_granted_sl_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('-granted_sl')
                # print('user_current_ctc_details_asc', user_granted_sl_details)
                granted_sl_details_list = []
                for u_g in user_granted_sl_details:
                    granted_sl_details_id = u_g.cu_user.id
                    granted_sl_details_list.append(granted_sl_details_id)
                # print('current_ctc_details_list', granted_sl_details_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(granted_sl_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=granted_sl_details_list).extra(select={'ordering': ordering},
                                                                                      order_by=('ordering',))
                # print('queryset', queryset)
                return queryset

            if field_name == 'granted_sl' and order_by == 'asc':
                # print('user_department',order_by)
                user_granted_sl_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('granted_sl')
                # print('user_current_ctc_details_asc', user_granted_sl_details)
                granted_sl_details_list = []
                for u_g in user_granted_sl_details:
                    granted_sl_details_id = u_g.cu_user.id
                    granted_sl_details_list.append(granted_sl_details_id)
                # print('current_ctc_details_list', granted_sl_details_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(granted_sl_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=granted_sl_details_list).extra(select={'ordering': ordering},
                                                                                      order_by=('ordering',))
                # print('queryset', queryset)
                return queryset

            if field_name == 'granted_el' and order_by == 'desc':
                # print('user_department',order_by)
                user_granted_el_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('-granted_el')
                # print('user_current_ctc_details_asc', user_granted_el_details)
                granted_el_details_list = []
                for u_g in user_granted_el_details:
                    granted_el_details_id = u_g.cu_user.id
                    granted_el_details_list.append(granted_el_details_id)
                # print('current_ctc_details_list', granted_el_details_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(granted_el_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=granted_el_details_list).extra(select={'ordering': ordering},
                                                                                      order_by=('ordering',))
                # print('queryset', queryset)
                return queryset

            if field_name == 'granted_el' and order_by == 'asc':
                # print('user_department',order_by)
                user_granted_el_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('granted_el')
                # print('user_current_ctc_details_asc', user_granted_el_details)
                granted_el_details_list = []
                for u_g in user_granted_el_details:
                    granted_el_details_id = u_g.cu_user.id
                    granted_el_details_list.append(granted_el_details_id)
                # print('current_ctc_details_list', granted_el_details_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(granted_el_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=granted_el_details_list).extra(select={'ordering': ordering},
                                                                                      order_by=('ordering',))
                # print('queryset', queryset)
                return queryset

            if field_name == 'total_experience' and order_by == 'desc':
                # print('user_department',order_by)
                user_total_experience_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('-total_experience')
                # print('user_current_ctc_details_asc', user_total_experience_details)
                total_experience_details_list = []
                for u_g in user_total_experience_details:
                    total_experience_details_id = u_g.cu_user.id
                    total_experience_details_list.append(total_experience_details_id)
                # print('current_ctc_details_list', total_experience_details_list)
                clauses = ' '.join(
                    ['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(total_experience_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=total_experience_details_list).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset', queryset)
                return queryset

            if field_name == 'total_experience' and order_by == 'asc':
                # print('user_department',order_by)
                user_total_experience_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('total_experience')
                # print('user_current_ctc_details_asc', user_total_experience_details)
                total_experience_details_list = []
                for u_g in user_total_experience_details:
                    total_experience_details_id = u_g.cu_user.id
                    total_experience_details_list.append(total_experience_details_id)
                # print('current_ctc_details_list', total_experience_details_list)
                clauses = ' '.join(
                    ['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(total_experience_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=total_experience_details_list).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset', queryset)
                return queryset

            if field_name == 'cu_emp_code' and order_by == 'asc':
                # print('user_department',order_by)
                user_total_experience_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('cu_emp_code')
                # print('user_current_ctc_details_asc', user_total_experience_details)
                total_experience_details_list = []
                for u_g in user_total_experience_details:
                    total_experience_details_id = u_g.cu_user.id
                    total_experience_details_list.append(total_experience_details_id)
                # print('current_ctc_details_list', total_experience_details_list)
                clauses = ' '.join(
                    ['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(total_experience_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=total_experience_details_list).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset', queryset)
                return queryset

            if field_name == 'cu_emp_code' and order_by == 'desc':
                # print('user_department',order_by)
                user_total_experience_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('-cu_emp_code')
                # print('user_current_ctc_details_asc', user_total_experience_details)
                total_experience_details_list = []
                for u_g in user_total_experience_details:
                    total_experience_details_id = u_g.cu_user.id
                    total_experience_details_list.append(total_experience_details_id)
                # print('current_ctc_details_list', total_experience_details_list)
                clauses = ' '.join(
                    ['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(total_experience_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=total_experience_details_list).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset', queryset)
                return queryset

            if field_name == 'cu_alt_email_id' and order_by == 'asc':
                # print('user_department',order_by)
                user_total_experience_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('cu_alt_email_id')
                # print('user_current_ctc_details_asc', user_total_experience_details)
                total_experience_details_list = []
                for u_g in user_total_experience_details:
                    total_experience_details_id = u_g.cu_user.id
                    total_experience_details_list.append(total_experience_details_id)
                # print('current_ctc_details_list', total_experience_details_list)
                clauses = ' '.join(
                    ['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(total_experience_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=total_experience_details_list).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset', queryset)
                return queryset

            if field_name == 'cu_alt_email_id' and order_by == 'desc':
                # print('user_department',order_by)
                user_total_experience_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('-cu_alt_email_id')
                # print('user_current_ctc_details_asc', user_total_experience_details)
                total_experience_details_list = []
                for u_g in user_total_experience_details:
                    total_experience_details_id = u_g.cu_user.id
                    total_experience_details_list.append(total_experience_details_id)
                # print('current_ctc_details_list', total_experience_details_list)
                clauses = ' '.join(
                    ['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(total_experience_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=total_experience_details_list).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset', queryset)
                return queryset

        elif search_keyword:
            self.queryset = TCoreUserDetail.objects.filter(cu_is_deleted=False, cu_user__is_superuser=False)
            # print('self.queryset',self.queryset)
            f_name = search_keyword.split(' ')[0]
            l_name = ' '.join(search_keyword.split(' ')[1:])
            # print(l_name)

            if l_name:
                queryset = self.queryset.filter(
                    Q(cu_user__first_name__icontains=f_name) |
                    Q(cu_user__last_name__icontains=l_name) |
                    Q(cu_user__email__icontains=search_keyword) |
                    Q(cu_alt_email_id__icontains=search_keyword)
                )
            else:
                queryset = self.queryset.filter(
                    Q(cu_user__first_name__icontains=f_name) |
                    Q(cu_user__email__icontains=search_keyword) |
                    Q(cu_alt_email_id__icontains=search_keyword)
                )
            # print('queryset',queryset.query)
            return queryset

        else:
            queryset = self.queryset.all()
            return queryset

    @response_modify_decorator_list_or_get_after_execution_for_pagination
    def get(self, request, *args, **kwargs):
        response = super(EmployeeListView, self).get(self, request, args, kwargs)

        if 'results' in response.data:
            response_s = response.data['results']
        else:
            response_s = response.data

        print('response check::::::::::::::', response_s)
        list_type = self.request.query_params.get('list_type', None)
        module_id = self.request.query_params.get('module_id', None)
        search_keyword = self.request.query_params.get('search_keyword', None)
        download = self.request.query_params.get('download', None)
        # print('module_id',module_id)
        p_doc_dict = {}
        data_list = list()
        for data in response_s:
            if list_type == "professional":
                professional_details = TCoreUserDetail.objects.filter(cu_user=data['id'], cu_is_deleted=False).values(
                    'cu_emp_code', 'sap_personnel_no', 'initial_ctc', 'current_ctc', 'cu_punch_id',
                    'cost_centre', 'granted_cl', 'granted_sl', 'granted_el')

                if search_keyword:
                    professional_details = TCoreUserDetail.objects.filter(pk=data['id'], cu_is_deleted=False).values(
                        'cu_emp_code', 'sap_personnel_no', 'initial_ctc', 'current_ctc', 'cu_punch_id',
                        'cost_centre', 'granted_cl', 'granted_sl', 'granted_el', 'cu_user__first_name',
                        'cu_user__last_name', 'cu_user__id')
                    data['first_name'] = professional_details[0]['cu_user__first_name'] if professional_details[0][
                        'cu_user__first_name'] else ''
                    data['last_name'] = professional_details[0]['cu_user__last_name'] if professional_details[0][
                        'cu_user__last_name'] else ''
                    data['name'] = data['first_name'] + ' ' + data['last_name']
                    data['id'] = User.objects.only('id').get(pk=professional_details[0]['cu_user__id']).id

                # print('professional_details',professional_details)

                if professional_details:
                    data['emp_code'] = professional_details[0]['cu_emp_code'] if professional_details[0][
                        'cu_emp_code'] else None
                    data['cu_punch_id'] = professional_details[0]['cu_punch_id'] if professional_details[0][
                        'cu_punch_id'] else None
                    data['sap_personnel_no'] = professional_details[0]['sap_personnel_no'] if professional_details[0][
                        'sap_personnel_no'] else None
                    data['initial_ctc'] = professional_details[0]['initial_ctc'] if professional_details[0][
                        'initial_ctc'] else None
                    data['current_ctc'] = professional_details[0]['current_ctc'] if professional_details[0][
                        'current_ctc'] else None
                    data['cost_centre'] = professional_details[0]['cost_centre'] if professional_details[0][
                        'cost_centre'] else None
                    data['granted_cl'] = professional_details[0]['granted_cl'] if professional_details[0][
                        'granted_cl'] else None
                    data['granted_sl'] = professional_details[0]['granted_sl'] if professional_details[0][
                        'granted_sl'] else None
                    data['granted_el'] = professional_details[0]['granted_el'] if professional_details[0][
                        'granted_el'] else None

                user_benefits = HrmsUsersBenefits.objects.filter(user=data['id'], is_deleted=False)
                benefits_list = []
                if user_benefits:
                    for u_b in user_benefits:
                        benefits = {
                            'id': u_b.id,
                            'benefits': u_b.benefits.id,
                            'benefits_name': u_b.benefits.benefits_name,
                            'allowance': u_b.allowance
                        }
                        benefits_list.append(benefits)
                    data['benefits_provided'] = benefits_list
                else:
                    data['benefits_provided'] = []
                other_facilities = HrmsUsersOtherFacilities.objects.filter(user=data['id'], is_deleted=False)
                facilities_list = []
                if other_facilities:
                    for o_f in other_facilities:
                        facility = {
                            'id': o_f.id,
                            'other_facilities': o_f.other_facilities,
                        }
                        facilities_list.append(facility)
                    data['other_facilities'] = facilities_list
                else:
                    data['other_facilities'] = []
                p_doc_list = []
                professional_documents = HrmsDocument.objects.filter(user=data['id'], is_deleted=False)
                if professional_documents:
                    for doc_details in professional_documents:
                        if (doc_details.tab_name).lower() == "professional":
                            if doc_details.__dict__['document'] == "":
                                file_url = ''
                            else:
                                file_url = request.build_absolute_uri(doc_details.document.url)
                            if doc_details.__dict__['document_name'] == "":
                                doc_name = ""
                            else:
                                doc_name = doc_details.document_name

                            p_doc_dict = {
                                'tab_name': doc_details.tab_name if doc_details.tab_name else None,
                                'field_label': doc_details.field_label if doc_details.field_label else None,
                                'document_name': doc_name,
                                'document': file_url
                            }
                            p_doc_list.append(p_doc_dict)
                    data['documents'] = p_doc_list
                else:
                    data['documents'] = []
            if list_type == "role":
                role_details = TCoreUserDetail.objects.filter(cu_user=data['id'], cu_is_deleted=False).values(
                    'cu_user__username', 'cu_user__first_name', 'cu_user__last_name',
                    'cu_emp_code', 'cu_alt_phone_no', 'cu_alt_email_id', 'company__id', 'company__coc_name',
                    'job_description', 'hod__id', 'hod__first_name', 'hod__last_name',
                    'designation__id', 'cu_user__id', 'designation__cod_name', 'department__id', 'department__cd_name',
                    'reporting_head__id', 'reporting_head__first_name', 'reporting_head__last_name',
                    'employee_grade__id', 'employee_grade__cg_name', 'sub_department__cd_name')

                if search_keyword:
                    role_details = TCoreUserDetail.objects.filter(pk=data['id'], cu_is_deleted=False).values(
                        'cu_user__username',
                        'cu_user__first_name', 'cu_user__last_name', 'cu_emp_code', 'cu_user__id', 'cu_alt_phone_no',
                        'cu_alt_email_id', 'company__id', 'company__coc_name', 'job_description', 'hod__id',
                        'hod__first_name', 'hod__last_name', 'designation__id', 'designation__cod_name',
                        'department__id', 'employee_grade__id',
                        'department__cd_name', 'reporting_head__id', 'reporting_head__first_name',
                        'reporting_head__last_name', 'employee_grade__cg_name', 'sub_department__cd_name')

                if role_details:
                    first_name = role_details[0]['cu_user__first_name'] if role_details[0][
                        'cu_user__first_name'] else ''
                    last_name = role_details[0]['cu_user__last_name'] if role_details[0]['cu_user__last_name'] else ''
                    data['id'] = role_details[0]['cu_user__id']
                    data['name'] = first_name + " " + last_name
                    data['first_name'] = first_name
                    data['last_name'] = last_name
                    data['username'] = role_details[0]['cu_user__username'] if role_details[0][
                        'cu_user__username'] else None
                    data['emp_code'] = role_details[0]['cu_emp_code'] if role_details[0]['cu_emp_code'] else None
                    data['official_contact_no'] = role_details[0]['cu_alt_phone_no'] if role_details[0][
                        'cu_alt_phone_no'] else None
                    data['official_email_id'] = role_details[0]['cu_alt_email_id'] if role_details[0][
                        'cu_alt_email_id'] else None
                    data['company'] = role_details[0]['company__id'] if role_details[0]['company__id'] else None
                    data['company_name'] = role_details[0]['company__coc_name'] if role_details[0][
                        'company__coc_name'] else None
                    data['job_description'] = role_details[0]['job_description'] if role_details[0][
                        'job_description'] else None
                    data['hod_id'] = role_details[0]['hod__id'] if role_details[0]['hod__id'] else None
                    data['sub_department_name'] = role_details[0]['sub_department__cd_name'] if role_details[0][
                        'sub_department__cd_name'] else None

                    hod__first_name = role_details[0]['hod__first_name'] if role_details[0]['hod__first_name'] else ''
                    hod__last_name = role_details[0]['hod__last_name'] if role_details[0]['hod__last_name'] else ''

                    data['hod'] = hod__first_name + " " + hod__last_name

                    data['designation_id'] = role_details[0]['designation__id'] if role_details[0][
                        'designation__id'] else None
                    data['designation_name'] = role_details[0]['designation__cod_name'] if role_details[0][
                        'designation__cod_name'] else None
                    data['department_id'] = role_details[0]['department__id'] if role_details[0][
                        'department__id'] else None
                    data['department_name'] = role_details[0]['department__cd_name'] if role_details[0][
                        'department__cd_name'] else None

                    data['reporting_head_id'] = role_details[0]['reporting_head__id'] if role_details[0][
                        'reporting_head__id'] else None

                    reporting_head__first_name = role_details[0]['reporting_head__first_name'] if role_details[0][
                        'reporting_head__first_name'] else ''
                    reporting_head__last_name = role_details[0]['reporting_head__last_name'] if role_details[0][
                        'reporting_head__last_name'] else ''

                    data['reporting_head_name'] = reporting_head__first_name + " " + reporting_head__last_name
                    # data['employee_grade_name']=role_details[0]['employee_grade__cg_name'] if role_details[0]['employee_grade__id'] else None
                    # data['employee_grade_id']=role_details[0]['employee_grade__id'] if role_details[0]['employee_grade__id'] else None
                    grade_details = TCoreGrade.objects.filter(id=role_details[0]['employee_grade__id'],
                                                              cg_is_deleted=False)
                    if grade_details:
                        grade_details = \
                        TCoreGrade.objects.filter(id=role_details[0]['employee_grade__id'], cg_is_deleted=False)[0]
                        if grade_details:
                            grade_dict = dict()
                            print('grade_details', grade_details.id)
                            if grade_details.cg_parent_id != 0:
                                parent = TCoreGrade.objects.filter(id=grade_details.cg_parent_id, cg_is_deleted=False)
                                for p_d in parent:
                                    grade_dict['id'] = p_d.id
                                    grade_dict['cg_name'] = p_d.cg_name

                                grade_dict['child'] = {
                                    "id": grade_details.id,
                                    "cg_name": grade_details.cg_name
                                }
                            else:
                                grade_dict['id'] = grade_details.id
                                grade_dict['cg_name'] = grade_details.cg_name
                                grade_dict['child'] = None

                            print('grade_dict', grade_dict)

                            data['grade_details'] = grade_dict
                        else:
                            data['grade_details'] = None
                    else:
                        data['grade_details'] = None
            if list_type == "personal":
                personal_details = TCoreUserDetail.objects.filter(cu_user=data['id'], cu_is_deleted=False)
                if search_keyword:
                    personal_details = TCoreUserDetail.objects.filter(pk=data['id'], cu_is_deleted=False)

                if personal_details:
                    for p_d in personal_details:
                        data['id'] = p_d.cu_user.id
                        data['first_name'] = p_d.cu_user.first_name if p_d.cu_user.first_name else ''
                        data['last_name'] = p_d.cu_user.last_name if p_d.cu_user.last_name else ''
                        data['name'] = data['first_name'] + ' ' + data['last_name']
                        data['emp_code'] = p_d.cu_emp_code
                        data['personal_contact_no'] = p_d.cu_phone_no
                        data['personal_email_id'] = p_d.cu_user.email
                        data['address'] = p_d.address
                        data['blood_group'] = p_d.blood_group
                        data['photo'] = request.build_absolute_uri(
                            p_d.cu_profile_img.url) if p_d.cu_profile_img else None
                        data['total_experience'] = p_d.total_experience

                licenses_and_certifications_dict = {}
                work_experience_dict = {}
                add_more_files_dict = {}
                personal_documents = HrmsDynamicSectionFieldLabelDetailsWithDoc.objects.filter(user=data['id'],
                                                                                               is_deleted=False)
                print("personal_documents", personal_documents)
                if personal_documents:
                    licenses_and_certifications_list = []
                    add_more_files_list = []
                    work_experience_list = []
                    for doc_details in personal_documents:
                        if (doc_details.tab_name).lower() == "personal":
                            if doc_details.__dict__['document'] == "":
                                file_url = ''
                            else:
                                file_url = request.build_absolute_uri(doc_details.document.url)

                            if doc_details.__dict__['document_name'] == "":
                                doc_name = ""
                            else:
                                doc_name = doc_details.document_name

                            if doc_details.field_label == "Licenses and Certifications":
                                licenses_and_certifications_dict = {
                                    'id': doc_details.id,
                                    'field_label_value': doc_details.field_label_value if doc_details.field_label_value else None,
                                    'document_name': doc_name,
                                    'document': file_url
                                }
                                licenses_and_certifications_list.append(licenses_and_certifications_dict)

                            if doc_details.field_label == "Work Experience":
                                work_experience_dict = {
                                    'id': doc_details.id,
                                    'field_label_value': doc_details.field_label_value if doc_details.field_label_value else None,
                                    'document_name': doc_name,
                                    'document': file_url
                                }
                                work_experience_list.append(work_experience_dict)

                    data[
                        'licenses_and_certifications_doc'] = licenses_and_certifications_list if licenses_and_certifications_list else []
                    data['work_experience_doc'] = work_experience_list if work_experience_list else []

                else:
                    data['licenses_and_certifications_doc'] = []
                    data['work_experience_doc'] = []
                academic_qualification = HrmsUserQualification.objects.filter(user=data['id'], is_deleted=False)
                print('academic_qualification', academic_qualification)
                if academic_qualification:
                    academic_qualification_list = []
                    academic_qualification_dict = {}
                    for a_q in academic_qualification:
                        academic_qualification_dict = {
                            'id': a_q.id,
                            'qualification': a_q.qualification.id,
                            'qualification_name': a_q.qualification.name,
                            'details': a_q.details
                        }
                        academic_doc = HrmsUserQualificationDocument.objects.filter(user_qualification=a_q.id,
                                                                                    is_deleted=False)
                        print('academic_doc', academic_doc)
                        if academic_doc:
                            academic_doc_dict = {}
                            academic_doc_list = []
                            for a_d in academic_doc:
                                academic_doc_dict = {
                                    'id': a_d.id,
                                    'document': request.build_absolute_uri(a_d.document.url)
                                }
                                academic_doc_list.append(academic_doc_dict)
                            academic_qualification_dict['qualification_doc'] = academic_doc_list
                        else:
                            academic_qualification_dict['qualification_doc'] = []
                        academic_qualification_list.append(academic_qualification_dict)
                    data['academic_qualification'] = academic_qualification_list
                else:
                    data['academic_qualification'] = []
            if list_type == 'resignation' or list_type == 'release' or list_type == 'employee-list-by-type':
                '''
                    Reason : Fetch Resignation employee list
                    Author : Rupam Hazra 
                    Line number:  1245 - 1337
                    Date : 19/02/2020
                '''
                # time.sleep(10)
                role_details = TCoreUserDetail.objects.filter(
                    cu_user=data['id'], cu_is_deleted=False
                ).values(
                    'cu_user__username', 'cu_user__first_name', 'cu_user__last_name',
                    'cu_emp_code', 'cu_alt_phone_no', 'cu_alt_email_id', 'company__id', 'company__coc_name',
                    'job_description', 'hod__id', 'hod__first_name', 'hod__last_name', 'designation__id', 'cu_user__id',
                    'designation__cod_name', 'department__id', 'department__cd_name', 'reporting_head__id',
                    'reporting_head__first_name', 'reporting_head__last_name',
                    'employee_grade__id', 'employee_grade__cg_name', 'sap_personnel_no', 'cu_punch_id',
                    'termination_date', 'resignation_date')

                if search_keyword:
                    role_details = TCoreUserDetail.objects.filter(pk=data['id'], cu_is_deleted=False).values(
                        'cu_user__username',
                        'cu_user__first_name', 'cu_user__last_name', 'cu_emp_code', 'cu_user__id', 'cu_alt_phone_no',
                        'cu_alt_email_id', 'company__id', 'company__coc_name', 'job_description', 'hod__id',
                        'hod__first_name', 'hod__last_name', 'designation__id', 'designation__cod_name',
                        'department__id', 'employee_grade__id', 'department__cd_name', 'reporting_head__id',
                        'reporting_head__first_name', 'reporting_head__last_name', 'employee_grade__cg_name',
                        'sap_personnel_no', 'cu_punch_id', 'termination_date', 'resignation_date')

                if role_details:
                    first_name = role_details[0]['cu_user__first_name'] if role_details[0][
                        'cu_user__first_name'] else ''
                    last_name = role_details[0]['cu_user__last_name'] if role_details[0]['cu_user__last_name'] else ''
                    data['id'] = role_details[0]['cu_user__id']
                    data['name'] = first_name + " " + last_name
                    data['first_name'] = first_name
                    data['last_name'] = last_name
                    data['username'] = role_details[0]['cu_user__username'] if role_details[0][
                        'cu_user__username'] else None
                    data['emp_code'] = role_details[0]['cu_emp_code'] if role_details[0]['cu_emp_code'] else None
                    data['official_contact_no'] = role_details[0]['cu_alt_phone_no'] if role_details[0][
                        'cu_alt_phone_no'] else None
                    data['official_email_id'] = role_details[0]['cu_alt_email_id'] if role_details[0][
                        'cu_alt_email_id'] else None
                    data['company'] = role_details[0]['company__id'] if role_details[0]['company__id'] else None
                    data['company_name'] = role_details[0]['company__coc_name'] if role_details[0][
                        'company__coc_name'] else None
                    data['job_description'] = role_details[0]['job_description'] if role_details[0][
                        'job_description'] else None
                    data['hod_id'] = role_details[0]['hod__id'] if role_details[0]['hod__id'] else None
                    data['sap_personnel_no'] = role_details[0]['sap_personnel_no'] if role_details[0][
                        'sap_personnel_no'] else None
                    data['cu_punch_id'] = role_details[0]['cu_punch_id'] if role_details[0]['cu_punch_id'] else None
                    data['termination_date'] = role_details[0]['termination_date'] if role_details[0][
                        'termination_date'] else None
                    data['resignation_date'] = role_details[0]['resignation_date'] if role_details[0][
                        'resignation_date'] else None

                    hod__first_name = role_details[0]['hod__first_name'] if role_details[0]['hod__first_name'] else ''
                    hod__last_name = role_details[0]['hod__last_name'] if role_details[0]['hod__last_name'] else ''

                    data['hod'] = hod__first_name + " " + hod__last_name

                    data['designation_id'] = role_details[0]['designation__id'] if role_details[0][
                        'designation__id'] else None
                    data['designation_name'] = role_details[0]['designation__cod_name'] if role_details[0][
                        'designation__cod_name'] else None
                    data['department_id'] = role_details[0]['department__id'] if role_details[0][
                        'department__id'] else None
                    data['department_name'] = role_details[0]['department__cd_name'] if role_details[0][
                        'department__cd_name'] else None

                    data['reporting_head_id'] = role_details[0]['reporting_head__id'] if role_details[0][
                        'reporting_head__id'] else None

                    reporting_head__first_name = role_details[0]['reporting_head__first_name'] if role_details[0][
                        'reporting_head__first_name'] else ''
                    reporting_head__last_name = role_details[0]['reporting_head__last_name'] if role_details[0][
                        'reporting_head__last_name'] else ''

                    data['reporting_head_name'] = reporting_head__first_name + " " + reporting_head__last_name
                    # data['employee_grade_name']=role_details[0]['employee_grade__cg_name'] if role_details[0]['employee_grade__id'] else None
                    # data['employee_grade_id']=role_details[0]['employee_grade__id'] if role_details[0]['employee_grade__id'] else None
                    grade_details = TCoreGrade.objects.filter(id=role_details[0]['employee_grade__id'],
                                                              cg_is_deleted=False)
                    if grade_details:
                        grade_details = \
                        TCoreGrade.objects.filter(id=role_details[0]['employee_grade__id'], cg_is_deleted=False)[0]
                        if grade_details:
                            grade_dict = dict()
                            print('grade_details', grade_details.id)
                            if grade_details.cg_parent_id != 0:
                                parent = TCoreGrade.objects.filter(id=grade_details.cg_parent_id, cg_is_deleted=False)
                                for p_d in parent:
                                    grade_dict['id'] = p_d.id
                                    grade_dict['cg_name'] = p_d.cg_name

                                grade_dict['child'] = {
                                    "id": grade_details.id,
                                    "cg_name": grade_details.cg_name
                                }
                            else:
                                grade_dict['id'] = grade_details.id
                                grade_dict['cg_name'] = grade_details.cg_name
                                grade_dict['child'] = None

                            print('grade_dict', grade_dict)

                            data['grade_details'] = grade_dict
                        else:
                            data['grade_details'] = None
                    else:
                        data['grade_details'] = None

                    data_list.append([data['first_name'], data['last_name'], data['emp_code'], data['sap_personnel_no'],
                                      data['cu_punch_id'],
                                      data['department_name'], data['designation_name'], data['company_name'],
                                      data['hod'], data['reporting_head_name'],
                                      data['official_contact_no'], data['official_email_id'], data['termination_date'],
                                      data['resignation_date']])

        print('data_list', data_list, type(data_list))
        file_name = ''
        if data_list:
            if os.path.isdir('media/hrms/employee_list/document'):
                file_name = 'media/hrms/employee_list/document/employee_list.xlsx'
            else:
                os.makedirs('media/hrms/employee_list/document')
                file_name = 'media/hrms/employee_list/document/employee_list.xlsx'

            final_df = pd.DataFrame(data_list,
                                    columns=['First Name', 'Last Name', 'Emp. Code', 'SAP Id', 'Punch Id', 'Department',
                                             'Designation', 'Company', 'HOD', 'Reporting Head', 'Official Contact No',
                                             'Official Email Id', 'Termination Date',
                                             'Resignation Date'])
            export_csv = final_df.to_excel(file_name, index=None, header=True)
            if request.is_secure():
                protocol = 'https://'
            else:
                protocol = 'http://'

        url = getHostWithPort(request) + file_name if file_name else None
        response.data['url'] = url

        return response


class EmployeeListViewV2(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = User.objects.filter(is_superuser=False).order_by('-id')
    serializer_class = EmployeeListSerializerV2
    pagination_class = CSPageNumberPagination

    def get_queryset(self):
        '''
            eleminate login user on employee list added by Rupam Hazra Line number 458 - 459
        '''
        login_user = self.request.user.id
        # self.queryset = self.queryset.filter(
        #     ~Q(pk=login_user),
        #     pk__in=(TMasterModuleRoleUser.objects.filter(mmr_type='3')))
        '''
            As per discussion with TonmoyDa
            login user also included in the list.
            09/05/2020 Rajesh
        '''
        # self.queryset = self.queryset.filter(
        #     ~Q(pk=login_user),is_active=True)

        filter = {}
        # name = self.request.query_params.get('name', None)
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        search_keyword = self.request.query_params.get('search_keyword', None)
        download = self.request.query_params.get('download', None)
        company = self.request.query_params.get('company', None)
        designation = self.request.query_params.get('designation', None)
        department = self.request.query_params.get('department', None)
        employee = self.request.query_params.get('employee', None)

        '''
            Reason : Fetch Resignation employee list with date range
            Author : Rupam Hazra 
            Line number:  494 - 503
            Date : 19/02/2020
            Modify Date : 06/03/2020

        '''
        '''
            As per discussion with TonmoyDa
            login user also included in the list.
            09/05/2020 Rajesh
        '''
        list_type = self.request.query_params.get('list_type', None)
        if list_type == 'resignation':
            from_date = self.request.query_params.get('from_date', None)
            to_date = self.request.query_params.get('to_date', None)
            # is_active and cu_is_deleted flag removed by Shubhadeep (08-09-2020)
            self.queryset = self.queryset.filter(id__in=(
                TCoreUserDetail.objects.filter(
                    resignation_date__gte=from_date,
                    resignation_date__lte=to_date).values_list('cu_user', flat=True)))

        '''
            Reason : Fetch Release employee list with date range
            Author : Rupam Hazra 
            Line number:  515 - 523
            Date : 19/02/2020
            Modify Date : 06/03/2020

        '''
        '''
            As per discussion with TonmoyDa
            login user also included in the list.
            09/05/2020 Rajesh
        '''
        if list_type == 'release':
            from_date = self.request.query_params.get('from_date', None)
            to_date = self.request.query_params.get('to_date', None)
            # is_active and cu_is_deleted flag removed by Shubhadeep (08-09-2020)
            self.queryset = self.queryset.filter(id__in=(
                TCoreUserDetail.objects.filter(
                    termination_date__gte=from_date,
                    termination_date__lte=to_date).values_list('cu_user', flat=True)))

        '''
            Reason : Fetch employee list by user type with date range
            Author : Rupam Hazra 
            Line number:  532 - 537
            Date : 19/02/2020
            Modify Date : 06/03/2020

        '''
        '''
            As per discussion with TonmoyDa
            login user also included in the list.
            09/05/2020 Rajesh
        '''
        if list_type == 'employee-list-by-type':
            which_type = self.request.query_params.get('which_type', None)
            self.queryset = self.queryset.filter(
                id__in=(
                    TCoreUserDetail.objects.filter(user_type=which_type
                                                   ).values_list('cu_user', flat=True)))

        if company:
            self.queryset = self.queryset.filter(
                id__in=(
                    TCoreUserDetail.objects.filter(company__id=company
                                                   ).values_list('cu_user', flat=True)))
        if employee:
            self.queryset = self.queryset.filter(id=employee)

        if designation:
            self.queryset = self.queryset.filter(
                id__in=(
                    TCoreUserDetail.objects.filter(designation__id=designation
                                                   ).values_list('cu_user', flat=True)))
        if department:
            self.queryset = self.queryset.filter(
                id__in=(
                    TCoreUserDetail.objects.filter(department__id=department
                                                   ).values_list('cu_user', flat=True)))

        users = self.request.query_params.get('users', None)
        if users:
            user_lst = users.split(',')
            return self.queryset.filter(id__in=user_lst)

        if field_name and order_by:
            # print('sfsffsfsfff')
            if field_name == 'email' and order_by == 'asc':
                return self.queryset.all().order_by('email')

            if field_name == 'email' and order_by == 'desc':
                return self.queryset.all().order_by('-email')

            if field_name == 'name' and order_by == 'asc':
                return self.queryset.all().order_by('first_name')

            if field_name == 'name' and order_by == 'desc':
                return self.queryset.all().order_by('-first_name')

            if field_name == 'grade' and order_by == 'asc':
                # print('user_grade_asc',order_by)
                user_grade = TCoreUserDetail.objects.filter(
                    cu_is_deleted__in=[True, False]).order_by('employee_grade__cg_name')
                # print('user_grade',user_grade)
                grade_list = []
                for u_g in user_grade:
                    grade_id = u_g.employee_grade.id if u_g.employee_grade else None
                    grade_list.append(grade_id)
                # print('grade_list',grade_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(grade_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=grade_list).extra(
                    select={'ordering': ordering}, order_by=('ordering',)
                )
                # print('queryset',queryset)
                return queryset

            if field_name == 'grade' and order_by == 'desc':
                # print('user_grade',order_by)
                user_grade = TCoreUserDetail.objects.filter(
                    cu_is_deleted__in=[True, False]).order_by('-employee_grade__cg_name')
                # print('user_grade_desc',user_grade)
                grade_list = []
                for u_g in user_grade:
                    grade_id = u_g.employee_grade.id if u_g.employee_grade else None
                    grade_list.append(grade_id)
                # print('grade_list',grade_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(grade_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=grade_list).extra(select={'ordering': ordering},
                                                                         order_by=('ordering',))
                # print('queryset',queryset)
                return queryset

            if field_name == 'designation' and order_by == 'desc':
                # print('user_grade',order_by)
                user_designation = TCoreUserDetail.objects.filter(
                    cu_is_deleted__in=[True, False]).order_by('-designation__cod_name')
                # print('user_designation_desc',user_designation)
                designation_list = []
                for u_g in user_designation:
                    designation_id = u_g.cu_user.id
                    designation_list.append(designation_id)
                # print('designation_list',designation_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(designation_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=designation_list).extra(select={'ordering': ordering},
                                                                               order_by=('ordering',))
                # print('queryset',queryset)
                return queryset

            if field_name == 'designation' and order_by == 'asc':
                # print('user_grade',order_by)
                user_designation = TCoreUserDetail.objects.filter(
                    cu_is_deleted__in=[True, False]).order_by('designation__cod_name')
                # print('user_designation_desc',user_designation)
                designation_list = []
                for u_g in user_designation:
                    designation_id = u_g.cu_user.id
                    designation_list.append(designation_id)
                # print('designation_list',designation_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(designation_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=designation_list).extra(select={'ordering': ordering},
                                                                               order_by=('ordering',))
                # print('queryset',queryset)
                return queryset

            if field_name == 'department' and order_by == 'asc':
                # print('user_department',order_by)
                user_department = TCoreUserDetail.objects.filter(
                    cu_is_deleted__in=[True, False]).order_by('department__cd_name')
                # print('user_department_asc',user_department)
                department_list = []
                for u_g in user_department:
                    department_id = u_g.cu_user.id
                    department_list.append(department_id)
                # print('department_list',department_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(department_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=department_list).extra(select={'ordering': ordering},
                                                                              order_by=('ordering',))
                # print('queryset',queryset)
                return queryset

            if field_name == 'department' and order_by == 'desc':
                # print('user_department',order_by)
                user_department = TCoreUserDetail.objects.filter(
                    cu_is_deleted__in=[True, False]).order_by('-department__cd_name')
                # print('user_department_asc',user_department)
                department_list = []
                for u_g in user_department:
                    department_id = u_g.cu_user.id
                    department_list.append(department_id)
                # print('department_list',department_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(department_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=department_list).extra(select={'ordering': ordering},
                                                                              order_by=('ordering',))
                # print('queryset',queryset)
                return queryset

            if field_name == 'company' and order_by == 'desc':
                # print('user_department',order_by)
                user_company = TCoreUserDetail.objects.filter(
                    cu_is_deleted__in=[True, False]).order_by('-company__coc_name')
                # print('user_company_asc',user_company)
                company_list = []
                for u_g in user_company:
                    company_id = u_g.cu_user.id
                    company_list.append(company_id)
                # print('company_list',company_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(company_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=company_list).extra(select={'ordering': ordering},
                                                                           order_by=('ordering',))
                # print('queryset',queryset)
                return queryset

            if field_name == 'company' and order_by == 'asc':
                # print('user_department',order_by)
                user_company = TCoreUserDetail.objects.filter(
                    cu_is_deleted__in=[True, False]).order_by('company__coc_name')
                # print('user_company_asc',user_company)
                company_list = []
                for u_g in user_company:
                    company_id = u_g.cu_user.id
                    company_list.append(company_id)
                # print('company_list',company_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(company_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=company_list).extra(select={'ordering': ordering},
                                                                           order_by=('ordering',))
                # print('queryset',queryset)
                return queryset

            if field_name == 'sap_no' and order_by == 'asc':
                # print('user_department',order_by)
                user_sap_no_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted__in=[True, False]).order_by('sap_personnel_no')
                # print('user_sap_no_details_asc',user_sap_no_details)
                sap_no_details_list = []
                for u_g in user_sap_no_details:
                    sap_no_details_id = u_g.cu_user.id
                    sap_no_details_list.append(sap_no_details_id)
                # print('sap_no_details_list',sap_no_details_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(sap_no_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=sap_no_details_list).extra(select={'ordering': ordering},
                                                                                  order_by=('ordering',))
                # print('queryset',queryset)
                return queryset

            if field_name == 'sap_no' and order_by == 'desc':
                # print('user_department',order_by)
                user_sap_no_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted__in=[True, False]).order_by('-sap_personnel_no')
                # print('user_sap_no_details_asc',user_sap_no_details)
                sap_no_details_list = []
                for u_g in user_sap_no_details:
                    sap_no_details_id = u_g.cu_user.id
                    sap_no_details_list.append(sap_no_details_id)
                # print('sap_no_details_list',sap_no_details_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(sap_no_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=sap_no_details_list).extra(select={'ordering': ordering},
                                                                                  order_by=('ordering',))
                # print('queryset',queryset)
                return queryset

            if field_name == 'initial_ctc' and order_by == 'desc':
                # print('user_department',order_by)
                user_initial_ctc_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted__in=[True, False]).order_by('-initial_ctc')
                # print('user_initial_ctc_details_asc',user_initial_ctc_details)
                initial_ctc_details_list = []
                for u_g in user_initial_ctc_details:
                    initial_ctc_details_id = u_g.cu_user.id
                    initial_ctc_details_list.append(initial_ctc_details_id)
                # print('initial_ctc_details_list',initial_ctc_details_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(initial_ctc_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=initial_ctc_details_list).extra(select={'ordering': ordering},
                                                                                       order_by=('ordering',))
                # print('queryset',queryset)
                return queryset

            if field_name == 'initial_ctc' and order_by == 'asc':
                # print('user_department',order_by)
                user_initial_ctc_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted__in=[True, False]).order_by('initial_ctc')
                # print('user_initial_ctc_details_asc',user_initial_ctc_details)
                initial_ctc_details_list = []
                for u_g in user_initial_ctc_details:
                    initial_ctc_details_id = u_g.cu_user.id
                    initial_ctc_details_list.append(initial_ctc_details_id)
                # print('initial_ctc_details_list',initial_ctc_details_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(initial_ctc_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=initial_ctc_details_list).extra(select={'ordering': ordering},
                                                                                       order_by=('ordering',))
                # print('queryset',queryset)
                return queryset

            if field_name == 'current_ctc' and order_by == 'desc':
                # print('user_department',order_by)
                user_current_ctc_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted__in=[True, False]).order_by('-current_ctc')
                # print('user_current_ctc_details_asc',user_current_ctc_details)
                current_ctc_details_list = []
                for u_g in user_current_ctc_details:
                    current_ctc_details_id = u_g.cu_user.id
                    current_ctc_details_list.append(current_ctc_details_id)
                # print('current_ctc_details_list',current_ctc_details_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(current_ctc_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=current_ctc_details_list).extra(select={'ordering': ordering},
                                                                                       order_by=('ordering',))
                # print('queryset',queryset)
                return queryset

            if field_name == 'current_ctc' and order_by == 'asc':
                # print('user_department',order_by)
                user_current_ctc_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted__in=[True, False]).order_by('current_ctc')
                # print('user_current_ctc_details_asc',user_current_ctc_details)
                current_ctc_details_list = []
                for u_g in user_current_ctc_details:
                    current_ctc_details_id = u_g.cu_user.id
                    current_ctc_details_list.append(current_ctc_details_id)
                # print('current_ctc_details_list',current_ctc_details_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(current_ctc_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=current_ctc_details_list).extra(select={'ordering': ordering},
                                                                                       order_by=('ordering',))
                # print('queryset',queryset)
                return queryset

            if field_name == 'granted_cl' and order_by == 'asc':
                # print('user_department',order_by)
                user_granted_cl_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted__in=[True, False]).order_by('current_ctc')
                # print('user_current_ctc_details_asc',user_granted_cl_details)
                granted_cl_details_list = []
                for u_g in user_granted_cl_details:
                    granted_cl_details_id = u_g.cu_user.id
                    granted_cl_details_list.append(granted_cl_details_id)
                # print('current_ctc_details_list',granted_cl_details_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(granted_cl_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=granted_cl_details_list).extra(select={'ordering': ordering},
                                                                                      order_by=('ordering',))
                # print('queryset',queryset)
                return queryset

            if field_name == 'granted_cl' and order_by == 'desc':
                # print('user_department',order_by)
                user_granted_cl_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted__in=[True, False]).order_by('-granted_cl')
                # print('user_current_ctc_details_asc',user_granted_cl_details)
                granted_cl_details_list = []
                for u_g in user_granted_cl_details:
                    granted_cl_details_id = u_g.cu_user.id
                    granted_cl_details_list.append(granted_cl_details_id)
                # print('current_ctc_details_list',granted_cl_details_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(granted_cl_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=granted_cl_details_list).extra(select={'ordering': ordering},
                                                                                      order_by=('ordering',))
                # print('queryset',queryset)
                return queryset

            if field_name == 'granted_sl' and order_by == 'desc':
                # print('user_department',order_by)
                user_granted_sl_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted__in=[True, False]).order_by('-granted_sl')
                # print('user_current_ctc_details_asc', user_granted_sl_details)
                granted_sl_details_list = []
                for u_g in user_granted_sl_details:
                    granted_sl_details_id = u_g.cu_user.id
                    granted_sl_details_list.append(granted_sl_details_id)
                # print('current_ctc_details_list', granted_sl_details_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(granted_sl_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=granted_sl_details_list).extra(select={'ordering': ordering},
                                                                                      order_by=('ordering',))
                # print('queryset', queryset)
                return queryset

            if field_name == 'granted_sl' and order_by == 'asc':
                # print('user_department',order_by)
                user_granted_sl_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted__in=[True, False]).order_by('granted_sl')
                # print('user_current_ctc_details_asc', user_granted_sl_details)
                granted_sl_details_list = []
                for u_g in user_granted_sl_details:
                    granted_sl_details_id = u_g.cu_user.id
                    granted_sl_details_list.append(granted_sl_details_id)
                # print('current_ctc_details_list', granted_sl_details_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(granted_sl_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=granted_sl_details_list).extra(select={'ordering': ordering},
                                                                                      order_by=('ordering',))
                # print('queryset', queryset)
                return queryset

            if field_name == 'granted_el' and order_by == 'desc':
                # print('user_department',order_by)
                user_granted_el_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted__in=[True, False]).order_by('-granted_el')
                # print('user_current_ctc_details_asc', user_granted_el_details)
                granted_el_details_list = []
                for u_g in user_granted_el_details:
                    granted_el_details_id = u_g.cu_user.id
                    granted_el_details_list.append(granted_el_details_id)
                # print('current_ctc_details_list', granted_el_details_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(granted_el_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=granted_el_details_list).extra(select={'ordering': ordering},
                                                                                      order_by=('ordering',))
                # print('queryset', queryset)
                return queryset

            if field_name == 'granted_el' and order_by == 'asc':
                # print('user_department',order_by)
                user_granted_el_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted__in=[True, False]).order_by('granted_el')
                # print('user_current_ctc_details_asc', user_granted_el_details)
                granted_el_details_list = []
                for u_g in user_granted_el_details:
                    granted_el_details_id = u_g.cu_user.id
                    granted_el_details_list.append(granted_el_details_id)
                # print('current_ctc_details_list', granted_el_details_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(granted_el_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=granted_el_details_list).extra(select={'ordering': ordering},
                                                                                      order_by=('ordering',))
                # print('queryset', queryset)
                return queryset

            if field_name == 'total_experience' and order_by == 'desc':
                # print('user_department',order_by)
                user_total_experience_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted__in=[True, False]).order_by('-total_experience')
                # print('user_current_ctc_details_asc', user_total_experience_details)
                total_experience_details_list = []
                for u_g in user_total_experience_details:
                    total_experience_details_id = u_g.cu_user.id
                    total_experience_details_list.append(total_experience_details_id)
                # print('current_ctc_details_list', total_experience_details_list)
                clauses = ' '.join(
                    ['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(total_experience_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=total_experience_details_list).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset', queryset)
                return queryset

            if field_name == 'total_experience' and order_by == 'asc':
                # print('user_department',order_by)
                user_total_experience_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted__in=[True, False]).order_by('total_experience')
                # print('user_current_ctc_details_asc', user_total_experience_details)
                total_experience_details_list = []
                for u_g in user_total_experience_details:
                    total_experience_details_id = u_g.cu_user.id
                    total_experience_details_list.append(total_experience_details_id)
                # print('current_ctc_details_list', total_experience_details_list)
                clauses = ' '.join(
                    ['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(total_experience_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=total_experience_details_list).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset', queryset)
                return queryset

            if field_name == 'cu_emp_code' and order_by == 'asc':
                # print('user_department',order_by)
                user_total_experience_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted__in=[True, False]).order_by('cu_emp_code')
                # print('user_current_ctc_details_asc', user_total_experience_details)
                total_experience_details_list = []
                for u_g in user_total_experience_details:
                    total_experience_details_id = u_g.cu_user.id
                    total_experience_details_list.append(total_experience_details_id)
                # print('current_ctc_details_list', total_experience_details_list)
                clauses = ' '.join(
                    ['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(total_experience_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=total_experience_details_list).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset', queryset)
                return queryset

            if field_name == 'cu_emp_code' and order_by == 'desc':
                # print('user_department',order_by)
                user_total_experience_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted__in=[True, False]).order_by('-cu_emp_code')
                # print('user_current_ctc_details_asc', user_total_experience_details)
                total_experience_details_list = []
                for u_g in user_total_experience_details:
                    total_experience_details_id = u_g.cu_user.id
                    total_experience_details_list.append(total_experience_details_id)
                # print('current_ctc_details_list', total_experience_details_list)
                clauses = ' '.join(
                    ['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(total_experience_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=total_experience_details_list).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset', queryset)
                return queryset

            if field_name == 'cu_alt_email_id' and order_by == 'asc':
                # print('user_department',order_by)
                user_total_experience_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted__in=[True, False]).order_by('cu_alt_email_id')
                # print('user_current_ctc_details_asc', user_total_experience_details)
                total_experience_details_list = []
                for u_g in user_total_experience_details:
                    total_experience_details_id = u_g.cu_user.id
                    total_experience_details_list.append(total_experience_details_id)
                # print('current_ctc_details_list', total_experience_details_list)
                clauses = ' '.join(
                    ['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(total_experience_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=total_experience_details_list).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset', queryset)
                return queryset

            if field_name == 'cu_alt_email_id' and order_by == 'desc':
                # print('user_department',order_by)
                user_total_experience_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted__in=[True, False]).order_by('-cu_alt_email_id')
                # print('user_current_ctc_details_asc', user_total_experience_details)
                total_experience_details_list = []
                for u_g in user_total_experience_details:
                    total_experience_details_id = u_g.cu_user.id
                    total_experience_details_list.append(total_experience_details_id)
                # print('current_ctc_details_list', total_experience_details_list)
                clauses = ' '.join(
                    ['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(total_experience_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=total_experience_details_list).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset', queryset)
                return queryset

        elif search_keyword:
            self.queryset = TCoreUserDetail.objects.filter(cu_user__is_superuser=False)
            # print('self.queryset',self.queryset)
            f_name = search_keyword.split(' ')[0]
            l_name = ' '.join(search_keyword.split(' ')[1:])
            # print(l_name)

            if l_name:
                queryset = self.queryset.filter(
                    Q(cu_user__first_name__icontains=f_name) |
                    Q(cu_user__last_name__icontains=l_name) |
                    Q(cu_user__email__icontains=search_keyword) |
                    Q(cu_alt_email_id__icontains=search_keyword)
                )
            else:
                queryset = self.queryset.filter(
                    Q(cu_user__first_name__icontains=f_name) |
                    Q(cu_user__email__icontains=search_keyword) |
                    Q(cu_alt_email_id__icontains=search_keyword)
                )
            # print('queryset',queryset.query)
            return queryset

        else:
            queryset = self.queryset.all()
            return queryset

    @response_modify_decorator_list_or_get_after_execution_for_pagination
    def get(self, request, *args, **kwargs):
        response = super(EmployeeListViewV2, self).get(self, request, args, kwargs)

        if 'results' in response.data:
            response_s = response.data['results']
        else:
            response_s = response.data

        # print('response check::::::::::::::',response_s)
        list_type = self.request.query_params.get('list_type', None)
        module_id = self.request.query_params.get('module_id', None)
        search_keyword = self.request.query_params.get('search_keyword', None)
        download = self.request.query_params.get('download', None)

        # updated by Shubhadeep
        ignore_delete = self.request.query_params.get('ignore_delete', False)
        # --

        # print('module_id',module_id)
        p_doc_dict = {}
        data_list = list()
        for data in response_s:
            if list_type == "professional":
                tcore_user = TCoreUserDetail.objects.filter(cu_user=data['id'])

                professional_details = tcore_user.values(
                    'cu_emp_code', 'sap_personnel_no', 'initial_ctc', 'current_ctc', 'cu_punch_id',
                    'cost_centre', 'updated_cost_centre', 'granted_cl', 'granted_sl', 'granted_el', 'wbs_element',
                    'retirement_date', 'esic_no', 'esi_dispensary', 'pf_no', 'emp_pension_no',
                    'employee_voluntary_provident_fund_contribution',
                    'uan_no', 'branch_name', 'bank_account', 'ifsc_code', 'bus_facility',
                    'has_pf', 'has_esi', 'job_location', 'job_location_state__cs_state_name', 'employee_grade',
                    'employee_sub_grade', 'bank_name_p__name', 'file_no', 'is_transfer')

                if search_keyword:
                    professional_details = TCoreUserDetail.objects.filter(pk=data['id']).values(
                        'cu_emp_code', 'sap_personnel_no', 'initial_ctc', 'current_ctc', 'cu_punch_id',
                        'cost_centre', 'granted_cl', 'granted_sl', 'granted_el', 'cu_user__first_name',
                        'cu_user__last_name', 'cu_user__id')
                    data['first_name'] = professional_details[0]['cu_user__first_name'] if professional_details[0][
                        'cu_user__first_name'] else ''
                    data['last_name'] = professional_details[0]['cu_user__last_name'] if professional_details[0][
                        'cu_user__last_name'] else ''
                    data['name'] = data['first_name'] + ' ' + data['last_name']
                    data['id'] = User.objects.only('id').get(pk=professional_details[0]['cu_user__id']).id

                # print('professional_details',professional_details)

                if professional_details:
                    data['emp_code'] = professional_details[0]['cu_emp_code'] if professional_details[0][
                        'cu_emp_code'] else None
                    data['cu_punch_id'] = professional_details[0]['cu_punch_id'] if professional_details[0][
                        'cu_punch_id'] else None
                    data['sap_personnel_no'] = professional_details[0]['sap_personnel_no'] if professional_details[0][
                        'sap_personnel_no'] else None
                    data['initial_ctc'] = professional_details[0]['initial_ctc'] if professional_details[0][
                        'initial_ctc'] else None
                    data['current_ctc'] = professional_details[0]['current_ctc'] if professional_details[0][
                        'current_ctc'] else None
                    data['granted_cl'] = professional_details[0]['granted_cl'] if professional_details[0][
                        'granted_cl'] else None
                    data['granted_sl'] = professional_details[0]['granted_sl'] if professional_details[0][
                        'granted_sl'] else None
                    data['granted_el'] = professional_details[0]['granted_el'] if professional_details[0][
                        'granted_el'] else None
                    leave_calculation = all_leave_calculation_upto_applied_date(
                        date_object=datetime.datetime.now().date(), user=tcore_user.first())
                    advance_leave_balance = advance_leave_calculation_excluding_current_month(
                        tcore_user=tcore_user.first(), date_object=datetime.datetime.now().date())
                    data['granted_leaves'] = leave_calculation['total_eligibility']
                    data['leave_balance'] = leave_calculation['total_eligibility'] - leave_calculation[
                        'total_consumption'] - advance_leave_balance['advance_al']

                    data['wbs_element'] = professional_details[0]['wbs_element'] if professional_details[0][
                        'wbs_element'] else None
                    data['retirement_date'] = professional_details[0]['retirement_date'] if professional_details[0][
                        'retirement_date'] else None
                    data['esic_no'] = professional_details[0]['esic_no'] if professional_details[0]['esic_no'] else None
                    data['esi_dispensary'] = professional_details[0]['esi_dispensary'] if professional_details[0][
                        'esi_dispensary'] else None
                    data['pf_no'] = professional_details[0]['pf_no'] if professional_details[0][
                        'pf_no'] else 'XX/XXX/999999/999999'
                    data['emp_pension_no'] = professional_details[0]['emp_pension_no'] if professional_details[0][
                        'emp_pension_no'] else None
                    data['employee_voluntary_provident_fund_contribution'] = professional_details[0][
                        'employee_voluntary_provident_fund_contribution'] if professional_details[0][
                        'employee_voluntary_provident_fund_contribution'] else None

                    data['uan_no'] = professional_details[0]['uan_no'] if professional_details[0]['uan_no'] else None
                    data['branch_name'] = professional_details[0]['branch_name'] if professional_details[0][
                        'branch_name'] else None
                    data['bank_account'] = professional_details[0]['bank_account'] if professional_details[0][
                        'bank_account'] else None
                    data['ifsc_code'] = professional_details[0]['ifsc_code'] if professional_details[0][
                        'ifsc_code'] else None
                    data['bus_facility'] = professional_details[0]['bus_facility']
                    data['is_transfer'] = professional_details[0]['is_transfer'] if professional_details[0][
                        'is_transfer'] else False

                    # 'has_pf','has_esi','job_location_state__cs_state_name','bank_name_p__name'
                    data['has_pf'] = professional_details[0]['has_pf']
                    data['has_esi'] = professional_details[0]['has_esi']
                    data['job_location'] = professional_details[0]['job_location']
                    data['job_location_state'] = professional_details[0]['job_location_state__cs_state_name']
                    data['bank_name'] = professional_details[0]['bank_name_p__name']
                    data['file_no'] = professional_details[0]['file_no'] if professional_details[0]['file_no'] else None
                    if professional_details[0]['updated_cost_centre']:
                        cc_obj = TCoreCompanyCostCentre.objects.filter(
                            id=professional_details[0]['updated_cost_centre'])
                        if cc_obj:
                            data['cost_centre'] = cc_obj[0].cost_centre_name
                            data['cost_centre_id'] = cc_obj[0].id
                        else:
                            data['cost_centre'] = professional_details[0]['cost_centre'] if professional_details[0][
                                'cost_centre'] else None
                            data['cost_centre_id'] = None
                    elif professional_details[0]['cost_centre']:
                        data['cost_centre'] = professional_details[0]['cost_centre'] if professional_details[0][
                            'cost_centre'] else None
                        data['cost_centre_id'] = None
                    else:
                        data['cost_centre'] = None
                        data['cost_centre_id'] = None

                    # data['cost_centre'] = professional_details[0]['cost_centre'] if professional_details[0][
                    #     'cost_centre'] else None
                    if professional_details[0]['employee_grade']:
                        grade = TCoreGrade.objects.get(id=professional_details[0]['employee_grade'])
                        data['grade'] = grade.cg_name
                    else:
                        data['grade'] = ""

                    if professional_details[0]['employee_sub_grade']:
                        sub_grade = TCoreSubGrade.objects.get(id=professional_details[0]['employee_sub_grade'])
                        data['sub_grade'] = sub_grade.name
                    else:
                        data['sub_grade'] = ""

                user_benefits = HrmsUsersBenefits.objects.filter(user=data['id'], is_deleted=False)
                benefits_list = []
                if user_benefits:
                    for u_b in user_benefits:
                        benefits = {
                            'id': u_b.id,
                            'benefits': u_b.benefits.id,
                            'benefits_name': u_b.benefits.benefits_name,
                            'allowance': u_b.allowance
                        }
                        benefits_list.append(benefits)
                    data['benefits_provided'] = benefits_list
                else:
                    data['benefits_provided'] = []
                other_facilities = HrmsUsersOtherFacilities.objects.filter(user=data['id'], is_deleted=False)
                facilities_list = []
                if other_facilities:
                    for o_f in other_facilities:
                        facility = {
                            'id': o_f.id,
                            'other_facilities': o_f.other_facilities,
                        }
                        facilities_list.append(facility)
                    data['other_facilities'] = facilities_list
                else:
                    data['other_facilities'] = []
                p_doc_list = []
                professional_documents = HrmsDocument.objects.filter(user=data['id'], is_deleted=False)
                if professional_documents:
                    for doc_details in professional_documents:
                        if (doc_details.tab_name).lower() == "professional":
                            if doc_details.__dict__['document'] == "":
                                file_url = ''
                            else:
                                file_url = request.build_absolute_uri(doc_details.document.url)
                            if doc_details.__dict__['document_name'] == "":
                                doc_name = ""
                            else:
                                doc_name = doc_details.document_name

                            p_doc_dict = {
                                'tab_name': doc_details.tab_name if doc_details.tab_name else None,
                                'field_label': doc_details.field_label if doc_details.field_label else None,
                                'document_name': doc_name,
                                'document': file_url
                            }
                            p_doc_list.append(p_doc_dict)
                    data['documents'] = p_doc_list
                else:
                    data['documents'] = []
            if list_type == "role":
                # print(data['id'])
                role_details = TCoreUserDetail.objects.filter(cu_user=data['id']).values('cu_user__username',
                                                                                         'cu_user__first_name',
                                                                                         'cu_user__last_name',
                                                                                         'cost_centre',
                                                                                         'updated_cost_centre',
                                                                                         'cu_emp_code',
                                                                                         'cu_alt_phone_no',
                                                                                         'cu_alt_email_id',
                                                                                         'company__id',
                                                                                         'company__coc_name',
                                                                                         'job_description', 'hod__id',
                                                                                         'hod__first_name',
                                                                                         'hod__last_name',
                                                                                         'cu_user__id',
                                                                                         'department__id',
                                                                                         'department__cd_name',
                                                                                         'reporting_head__id',
                                                                                         'reporting_head__first_name',
                                                                                         'reporting_head__last_name',
                                                                                         'employee_grade__id',
                                                                                         'employee_grade__cg_name',
                                                                                         'employee_sub_grade__name',
                                                                                         'sub_department__cd_name',
                                                                                         'password_to_know',
                                                                                         'is_flexi_hour', 'file_no',
                                                                                         'is_transfer')

                if search_keyword:
                    role_details = TCoreUserDetail.objects.filter(pk=data['id']).values('cu_user__username',
                                                                                        'cost_centre',
                                                                                        'updated_cost_centre',
                                                                                        'cu_user__first_name',
                                                                                        'cu_user__last_name',
                                                                                        'cu_emp_code', 'cu_user__id',
                                                                                        'cu_alt_phone_no',
                                                                                        'cu_alt_email_id',
                                                                                        'company__id',
                                                                                        'company__coc_name',
                                                                                        'job_description', 'hod__id',
                                                                                        'hod__first_name',
                                                                                        'hod__last_name',
                                                                                        'department__id',
                                                                                        'employee_grade__id',
                                                                                        'password_to_know',
                                                                                        'department__cd_name',
                                                                                        'reporting_head__id',
                                                                                        'reporting_head__first_name',
                                                                                        'reporting_head__last_name',
                                                                                        'employee_grade__cg_name',
                                                                                        'sub_department__cd_name',
                                                                                        'is_flexi_hour', 'file_no')

                if role_details:
                    first_name = role_details[0]['cu_user__first_name'] if role_details[0][
                        'cu_user__first_name'] else ''
                    last_name = role_details[0]['cu_user__last_name'] if role_details[0]['cu_user__last_name'] else ''
                    data['id'] = role_details[0]['cu_user__id']
                    data['name'] = first_name + " " + last_name
                    data['first_name'] = first_name
                    data['last_name'] = last_name
                    data['password_to_know'] = role_details[0]['password_to_know']
                    data['username'] = role_details[0]['cu_user__username'] if role_details[0][
                        'cu_user__username'] else None
                    data['emp_code'] = role_details[0]['cu_emp_code'] if role_details[0]['cu_emp_code'] else None
                    data['official_contact_no'] = role_details[0]['cu_alt_phone_no'] if role_details[0][
                        'cu_alt_phone_no'] else None
                    data['official_email_id'] = role_details[0]['cu_alt_email_id'] if role_details[0][
                        'cu_alt_email_id'] else None
                    data['company'] = role_details[0]['company__id'] if role_details[0]['company__id'] else None
                    data['is_transfer'] = role_details[0]['is_transfer'] if role_details[0]['is_transfer'] else False
                    data['company_name'] = role_details[0]['company__coc_name'] if role_details[0][
                        'company__coc_name'] else None
                    data['job_description'] = role_details[0]['job_description'] if role_details[0][
                        'job_description'] else None
                    data['hod_id'] = role_details[0]['hod__id'] if role_details[0]['hod__id'] else None
                    data['sub_department_name'] = role_details[0]['sub_department__cd_name'] if role_details[0][
                        'sub_department__cd_name'] else None

                    hod__first_name = role_details[0]['hod__first_name'] if role_details[0]['hod__first_name'] else ''
                    hod__last_name = role_details[0]['hod__last_name'] if role_details[0]['hod__last_name'] else ''

                    data['hod'] = hod__first_name + " " + hod__last_name

                    # data['designation_id']=role_details[0]['designation__id'] if role_details[0]['designation__id'] else None
                    data['designation_name'] = data['designation']
                    data['department_id'] = role_details[0]['department__id'] if role_details[0][
                        'department__id'] else None
                    data['department_name'] = role_details[0]['department__cd_name'] if role_details[0][
                        'department__cd_name'] else None

                    data['reporting_head_id'] = role_details[0]['reporting_head__id'] if role_details[0][
                        'reporting_head__id'] else None
                    data['sub_grade'] = role_details[0]['employee_sub_grade__name'] if role_details[0][
                        'employee_sub_grade__name'] else None
                    data['is_flexi_hour'] = role_details[0]['is_flexi_hour']

                    reporting_head__first_name = role_details[0]['reporting_head__first_name'] if role_details[0][
                        'reporting_head__first_name'] else ''
                    reporting_head__last_name = role_details[0]['reporting_head__last_name'] if role_details[0][
                        'reporting_head__last_name'] else ''

                    data['reporting_head_name'] = reporting_head__first_name + " " + reporting_head__last_name
                    data['file_no'] = role_details[0]['file_no'] if role_details[0]['file_no'] else None

                    # temp_reporting_head__first_name = role_details[0]['temp_reporting_head__first_name'] if role_details[0]['temp_reporting_head__first_name'] else ''
                    # temp_reporting_head__last_name = role_details[0]['temp_reporting_head__last_name'] if role_details[0]['temp_reporting_head__last_name'] else ''

                    # data['temp_reporting_head_id'] = role_details[0]['temp_reporting_head__id'] if role_details[0]['temp_reporting_head__id'] else None
                    # data['temp_reporting_head_name'] = temp_reporting_head__first_name + ' ' +temp_reporting_head__last_name

                    temp_reporting_heads = UserTempReportingHeadMap.objects.filter(user=data['id'],
                                                                                   is_deleted=False).values(
                        'temp_reporting_head__id', 'temp_reporting_head__first_name', 'temp_reporting_head__last_name')
                    data['temp_reporting_heads'] = temp_reporting_heads
                    if role_details[0]['updated_cost_centre']:
                        cc_obj = TCoreCompanyCostCentre.objects.filter(id=role_details[0]['updated_cost_centre'])
                        if cc_obj:
                            data['cost_centre'] = cc_obj[0].cost_centre_name
                            data['cost_centre_id'] = cc_obj[0].id
                        else:
                            data['cost_centre'] = role_details[0]['cost_centre'] if role_details[0][
                                'cost_centre'] else None
                            data['cost_centre_id'] = None
                    elif role_details[0]['cost_centre']:
                        data['cost_centre'] = role_details[0]['cost_centre'] if role_details[0][
                            'cost_centre'] else None
                        data['cost_centre_id'] = None
                    else:
                        data['cost_centre'] = None
                        data['cost_centre_id'] = None

                    # data['employee_grade_name']=role_details[0]['employee_grade__cg_name'] if role_details[0]['employee_grade__id'] else None
                    # data['employee_grade_id']=role_details[0]['employee_grade__id'] if role_details[0]['employee_grade__id'] else None
                    grade_details = TCoreGrade.objects.filter(id=role_details[0]['employee_grade__id'],
                                                              cg_is_deleted=False)
                    if grade_details:
                        grade_details = \
                        TCoreGrade.objects.filter(id=role_details[0]['employee_grade__id'], cg_is_deleted=False)[0]
                        if grade_details:
                            grade_dict = dict()
                            # print('grade_details',grade_details.id)
                            if grade_details.cg_parent_id != 0:
                                parent = TCoreGrade.objects.filter(id=grade_details.cg_parent_id, cg_is_deleted=False)
                                for p_d in parent:
                                    grade_dict['id'] = p_d.id
                                    grade_dict['cg_name'] = p_d.cg_name

                                grade_dict['child'] = {
                                    "id": grade_details.id,
                                    "cg_name": grade_details.cg_name
                                }
                            else:
                                grade_dict['id'] = grade_details.id
                                grade_dict['cg_name'] = grade_details.cg_name
                                grade_dict['child'] = None

                            # print('grade_dict',grade_dict)

                            data['grade_details'] = grade_dict
                        else:
                            data['grade_details'] = None
                    else:
                        data['grade_details'] = None
            if list_type == "personal":
                personal_details = TCoreUserDetail.objects.filter(cu_user=data['id'])
                if search_keyword:
                    personal_details = TCoreUserDetail.objects.filter(pk=data['id'])

                if personal_details:
                    for p_d in personal_details:
                        data['id'] = p_d.cu_user.id
                        data['first_name'] = p_d.cu_user.first_name if p_d.cu_user.first_name else ''
                        data['last_name'] = p_d.cu_user.last_name if p_d.cu_user.last_name else ''
                        data['name'] = data['first_name'] + ' ' + data['last_name']
                        data['dob'] = p_d.cu_dob
                        data['emp_code'] = p_d.cu_emp_code
                        data['personal_contact_no'] = p_d.cu_phone_no
                        data['personal_email_id'] = p_d.cu_user.email
                        data['address'] = p_d.address
                        data['blood_group'] = p_d.blood_group
                        data['photo'] = request.build_absolute_uri(
                            p_d.cu_profile_img.url) if p_d.cu_profile_img else None
                        data['total_experience'] = p_d.total_experience

                        data['care_of'] = p_d.care_of
                        data['street_and_house_no'] = p_d.street_and_house_no
                        data['address_2nd_line'] = p_d.address_2nd_line
                        data['city'] = p_d.city
                        data['district'] = p_d.district
                        data['is_transfer'] = p_d.is_transfer

                        data['aadhar_no'] = p_d.aadhar_no
                        data['pan_no'] = p_d.pan_no
                        data['cu_gender'] = p_d.cu_gender
                        data['pincode'] = p_d.pincode
                        data['emergency_relationship'] = p_d.emergency_relationship
                        data['emergency_contact_no'] = p_d.emergency_contact_no
                        data['emergency_contact_name'] = p_d.emergency_contact_name
                        data['marital_status'] = p_d.marital_status

                        data['father_name'] = p_d.father_name
                        data['file_no'] = p_d.file_no

                licenses_and_certifications_dict = {}
                work_experience_dict = {}
                other_documents_dict = {}
                add_more_files_dict = {}
                personal_documents = HrmsDynamicSectionFieldLabelDetailsWithDoc.objects.filter(user=data['id'],
                                                                                               is_deleted=False)
                # print("personal_documents",personal_documents)
                if personal_documents:
                    licenses_and_certifications_list = []
                    add_more_files_list = []
                    work_experience_list = []
                    other_documents_list = []
                    for doc_details in personal_documents:
                        if (doc_details.tab_name).lower() == "personal":
                            if doc_details.__dict__['document'] == "":
                                file_url = ''
                            else:
                                file_url = request.build_absolute_uri(doc_details.document.url)

                            if doc_details.__dict__['document_name'] == "":
                                doc_name = ""
                            else:
                                doc_name = doc_details.document_name

                            if doc_details.field_label == "Licenses and Certifications":
                                licenses_and_certifications_dict = {
                                    'id': doc_details.id,
                                    'field_label_value': doc_details.field_label_value if doc_details.field_label_value else None,
                                    'document_name': doc_name,
                                    'document': file_url
                                }
                                licenses_and_certifications_list.append(licenses_and_certifications_dict)

                            if doc_details.field_label == "Work Experience":
                                work_experience_dict = {
                                    'id': doc_details.id,
                                    'field_label_value': doc_details.field_label_value if doc_details.field_label_value else None,
                                    'document_name': doc_name,
                                    'document': file_url
                                }
                                work_experience_list.append(work_experience_dict)

                            if doc_details.field_label == "Other Documents":
                                other_documents_dict = {
                                    'id': doc_details.id,
                                    'field_label_value': doc_details.field_label_value if doc_details.field_label_value else None,
                                    'document_name': doc_name,
                                    'document': file_url
                                }
                                other_documents_list.append(other_documents_dict)

                    data[
                        'licenses_and_certifications_doc'] = licenses_and_certifications_list if licenses_and_certifications_list else []
                    data['work_experience_doc'] = work_experience_list if work_experience_list else []
                    data['other_documents_list'] = other_documents_list if other_documents_list else []


                else:
                    data['licenses_and_certifications_doc'] = []
                    data['work_experience_doc'] = []
                    data['other_documents_list'] = []

                academic_qualification = HrmsUserQualification.objects.filter(user=data['id'], is_deleted=False)
                # print('academic_qualification',academic_qualification)
                if academic_qualification:
                    academic_qualification_list = []
                    academic_qualification_dict = {}
                    for a_q in academic_qualification:
                        academic_qualification_dict = {
                            'id': a_q.id,
                            'qualification': a_q.qualification.id,
                            'qualification_name': a_q.qualification.name,
                            'details': a_q.details
                        }
                        academic_doc = HrmsUserQualificationDocument.objects.filter(user_qualification=a_q.id,
                                                                                    is_deleted=False)
                        print('academic_doc', academic_doc)
                        if academic_doc:
                            academic_doc_dict = {}
                            academic_doc_list = []
                            for a_d in academic_doc:
                                academic_doc_dict = {
                                    'id': a_d.id,
                                    'document': request.build_absolute_uri(a_d.document.url)
                                }
                                academic_doc_list.append(academic_doc_dict)
                            academic_qualification_dict['qualification_doc'] = academic_doc_list
                        else:
                            academic_qualification_dict['qualification_doc'] = []
                        academic_qualification_list.append(academic_qualification_dict)
                    data['academic_qualification'] = academic_qualification_list
                else:
                    data['academic_qualification'] = []
            if list_type == 'resignation' or list_type == 'release' or list_type == 'employee-list-by-type':
                '''
                    Reason : Fetch Resignation employee list
                    Author : Rupam Hazra 
                    Line number:  1245 - 1337
                    Date : 19/02/2020
                '''
                # time.sleep(10)
                role_details = TCoreUserDetail.objects.filter(
                    cu_user=data['id']).values(
                    'cu_user__username', 'cu_user__first_name', 'cu_user__last_name',
                    'cu_emp_code', 'cu_alt_phone_no', 'cu_alt_email_id', 'company__id', 'company__coc_name',
                    'job_description', 'hod__id', 'hod__first_name', 'hod__last_name', 'designation__id', 'cu_user__id',
                    'designation__cod_name', 'department__id', 'department__cd_name', 'reporting_head__id',
                    'reporting_head__first_name', 'reporting_head__last_name',
                    'employee_grade__id', 'employee_grade__cg_name', 'sap_personnel_no', 'cu_punch_id',
                    'termination_date', 'resignation_date')

                if search_keyword:
                    role_details = TCoreUserDetail.objects.filter(pk=data['id']).values('cu_user__username',
                                                                                        'cu_user__first_name',
                                                                                        'cu_user__last_name',
                                                                                        'cu_emp_code', 'cu_user__id',
                                                                                        'cu_alt_phone_no',
                                                                                        'cu_alt_email_id',
                                                                                        'company__id',
                                                                                        'company__coc_name',
                                                                                        'job_description', 'hod__id',
                                                                                        'hod__first_name',
                                                                                        'hod__last_name',
                                                                                        'designation__id',
                                                                                        'designation__cod_name',
                                                                                        'department__id',
                                                                                        'employee_grade__id',
                                                                                        'department__cd_name',
                                                                                        'reporting_head__id',
                                                                                        'reporting_head__first_name',
                                                                                        'reporting_head__last_name',
                                                                                        'employee_grade__cg_name',
                                                                                        'sap_personnel_no',
                                                                                        'cu_punch_id',
                                                                                        'termination_date',
                                                                                        'resignation_date')

                if role_details:
                    first_name = role_details[0]['cu_user__first_name'] if role_details[0][
                        'cu_user__first_name'] else ''
                    last_name = role_details[0]['cu_user__last_name'] if role_details[0]['cu_user__last_name'] else ''
                    data['id'] = role_details[0]['cu_user__id']
                    data['name'] = first_name + " " + last_name
                    data['first_name'] = first_name
                    data['last_name'] = last_name
                    data['username'] = role_details[0]['cu_user__username'] if role_details[0][
                        'cu_user__username'] else None
                    data['emp_code'] = role_details[0]['cu_emp_code'] if role_details[0]['cu_emp_code'] else None
                    data['official_contact_no'] = role_details[0]['cu_alt_phone_no'] if role_details[0][
                        'cu_alt_phone_no'] else None
                    data['official_email_id'] = role_details[0]['cu_alt_email_id'] if role_details[0][
                        'cu_alt_email_id'] else None
                    data['company'] = role_details[0]['company__id'] if role_details[0]['company__id'] else None
                    data['company_name'] = role_details[0]['company__coc_name'] if role_details[0][
                        'company__coc_name'] else None
                    data['job_description'] = role_details[0]['job_description'] if role_details[0][
                        'job_description'] else None
                    data['hod_id'] = role_details[0]['hod__id'] if role_details[0]['hod__id'] else None
                    data['sap_personnel_no'] = role_details[0]['sap_personnel_no'] if role_details[0][
                        'sap_personnel_no'] else None
                    data['cu_punch_id'] = role_details[0]['cu_punch_id'] if role_details[0]['cu_punch_id'] else None
                    data['termination_date'] = role_details[0]['termination_date'] if role_details[0][
                        'termination_date'] else None
                    data['resignation_date'] = role_details[0]['resignation_date'] if role_details[0][
                        'resignation_date'] else None

                    hod__first_name = role_details[0]['hod__first_name'] if role_details[0]['hod__first_name'] else ''
                    hod__last_name = role_details[0]['hod__last_name'] if role_details[0]['hod__last_name'] else ''

                    data['hod'] = hod__first_name + " " + hod__last_name

                    data['designation_id'] = role_details[0]['designation__id'] if role_details[0][
                        'designation__id'] else None
                    data['designation_name'] = role_details[0]['designation__cod_name'] if role_details[0][
                        'designation__cod_name'] else None
                    data['department_id'] = role_details[0]['department__id'] if role_details[0][
                        'department__id'] else None
                    data['department_name'] = role_details[0]['department__cd_name'] if role_details[0][
                        'department__cd_name'] else None

                    data['reporting_head_id'] = role_details[0]['reporting_head__id'] if role_details[0][
                        'reporting_head__id'] else None

                    reporting_head__first_name = role_details[0]['reporting_head__first_name'] if role_details[0][
                        'reporting_head__first_name'] else ''
                    reporting_head__last_name = role_details[0]['reporting_head__last_name'] if role_details[0][
                        'reporting_head__last_name'] else ''

                    data['reporting_head_name'] = reporting_head__first_name + " " + reporting_head__last_name
                    # data['employee_grade_name']=role_details[0]['employee_grade__cg_name'] if role_details[0]['employee_grade__id'] else None
                    # data['employee_grade_id']=role_details[0]['employee_grade__id'] if role_details[0]['employee_grade__id'] else None
                    grade_details = TCoreGrade.objects.filter(id=role_details[0]['employee_grade__id'],
                                                              cg_is_deleted=False)
                    if grade_details:
                        grade_details = \
                        TCoreGrade.objects.filter(id=role_details[0]['employee_grade__id'], cg_is_deleted=False)[0]
                        if grade_details:
                            grade_dict = dict()
                            # print('grade_details',grade_details.id)
                            if grade_details.cg_parent_id != 0:
                                parent = TCoreGrade.objects.filter(id=grade_details.cg_parent_id, cg_is_deleted=False)
                                for p_d in parent:
                                    grade_dict['id'] = p_d.id
                                    grade_dict['cg_name'] = p_d.cg_name

                                grade_dict['child'] = {
                                    "id": grade_details.id,
                                    "cg_name": grade_details.cg_name
                                }
                            else:
                                grade_dict['id'] = grade_details.id
                                grade_dict['cg_name'] = grade_details.cg_name
                                grade_dict['child'] = None

                            # print('grade_dict',grade_dict)

                            data['grade_details'] = grade_dict
                        else:
                            data['grade_details'] = None
                    else:
                        data['grade_details'] = None

                    if download == 'yes':
                        data_list.append(
                            [data['first_name'], data['last_name'], data['emp_code'], data['sap_personnel_no'],
                             data['cu_punch_id'],
                             data['department_name'], data['designation_name'], data['company_name'], data['hod'],
                             data['reporting_head_name'],
                             data['official_contact_no'], data['official_email_id'], data['termination_date'],
                             data['resignation_date']])

        # print('data_list',data_list,type(data_list))
        if download == 'yes':
            file_name = ''
            if data_list:
                if os.path.isdir('media/hrms/employee_list/document'):
                    file_name = 'media/hrms/employee_list/document/employee_list.xlsx'
                else:
                    os.makedirs('media/hrms/employee_list/document')
                    file_name = 'media/hrms/employee_list/document/employee_list.xlsx'

                final_df = pd.DataFrame(data_list,
                                        columns=['First Name', 'Last Name', 'Emp. Code', 'SAP Id', 'Punch Id',
                                                 'Department',
                                                 'Designation', 'Company', 'HOD', 'Reporting Head',
                                                 'Official Contact No', 'Official Email Id', 'Termination Date',
                                                 'Resignation Date'])
                export_csv = final_df.to_excel(file_name, index=None, header=True)
                if request.is_secure():
                    protocol = 'https://'
                else:
                    protocol = 'http://'

            url = getHostWithPort(request) + file_name if file_name else None
            response.data['url'] = url

        return response


class EmployeeListExportDownloadView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = User.objects.filter(is_superuser=False).order_by('-id')
    serializer_class = EmployeeListSerializer

    def get_queryset(self):
        '''
            eleminate login user on employee list added by Rupam Hazra Line number 458 - 459
        '''
        login_user = self.request.user.id
        # self.queryset = self.queryset.filter(
        #     ~Q(pk=login_user),
        #     pk__in=(TMasterModuleRoleUser.objects.filter(mmr_type='3')))
        employee = self.request.query_params.get('employee', None)
        if employee:
            self.queryset = self.queryset.filter(~Q(pk=login_user),
                                                 id=employee)

        filter = {}
        # name = self.request.query_params.get('name', None)
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        search_keyword = self.request.query_params.get('search_keyword', None)
        company = self.request.query_params.get('company', None)
        designation = self.request.query_params.get('designation', None)
        department = self.request.query_params.get('department', None)

        '''
            Reason : Fetch Resignation employee list with date range
            Author : Rupam Hazra 
            Line number:  494 - 503
            Date : 19/02/2020
            Modify Date : 06/03/2020

        '''
        list_type = self.request.query_params.get('list_type', None)
        if list_type == 'resignation':
            from_date = self.request.query_params.get('from_date', None)
            to_date = self.request.query_params.get('to_date', None)
            # is_active and cu_is_deleted flag removed by Shubhadeep (08-09-2020)
            self.queryset = self.queryset.filter(
                ~Q(pk=login_user), id__in=(
                    TCoreUserDetail.objects.filter(
                        resignation_date__gte=from_date,
                        resignation_date__lte=to_date).values_list('cu_user', flat=True)))

        elif list_type == 'release':
            from_date = self.request.query_params.get('from_date', None)
            to_date = self.request.query_params.get('to_date', None)
            # is_active and cu_is_deleted flag removed by Shubhadeep (08-09-2020)
            self.queryset = self.queryset.filter(
                ~Q(pk=login_user), id__in=(
                    TCoreUserDetail.objects.filter(
                        termination_date__gte=from_date,
                        termination_date__lte=to_date).values_list('cu_user', flat=True)))

        elif list_type == 'employee-list-by-type':
            which_type = self.request.query_params.get('which_type', None)
            self.queryset = self.queryset.filter(
                ~Q(pk=login_user), id__in=(
                    TCoreUserDetail.objects.filter(user_type=which_type, cu_is_deleted=False
                                                   ).values_list('cu_user', flat=True)))

        ## is_active flag disabled by Shubhadeep
        # else:
        #     self.queryset = self.queryset.filter(is_active=True)

        if company:
            self.queryset = self.queryset.filter(
                id__in=(
                    TCoreUserDetail.objects.filter(company__id=company).values_list('cu_user', flat=True)))

        if designation:
            self.queryset = self.queryset.filter(
                id__in=(
                    TCoreUserDetail.objects.filter(designation__id=designation).values_list('cu_user', flat=True)))
        if department:
            self.queryset = self.queryset.filter(
                id__in=(
                    TCoreUserDetail.objects.filter(department__id=department).values_list('cu_user', flat=True)))

        users = self.request.query_params.get('users', None)
        if users:
            user_lst = users.split(',')
            return self.queryset.filter(id__in=user_lst)

        if field_name and order_by:
            # print('sfsffsfsfff')
            if field_name == 'email' and order_by == 'asc':
                return self.queryset.all().order_by('email')

            if field_name == 'email' and order_by == 'desc':
                return self.queryset.all().order_by('-email')

            if field_name == 'name' and order_by == 'asc':
                return self.queryset.all().order_by('first_name')

            if field_name == 'name' and order_by == 'desc':
                return self.queryset.all().order_by('-first_name')

            if field_name == 'grade' and order_by == 'asc':
                # print('user_grade_asc',order_by)
                user_grade = TCoreUserDetail.objects.order_by('employee_grade__cg_name')
                # print('user_grade',user_grade)
                grade_list = []
                for u_g in user_grade:
                    grade_id = u_g.employee_grade.id if u_g.employee_grade else None
                    grade_list.append(grade_id)
                # print('grade_list',grade_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(grade_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=grade_list).extra(
                    select={'ordering': ordering}, order_by=('ordering',)
                )
                # print('queryset',queryset)
                return queryset

            if field_name == 'grade' and order_by == 'desc':
                # print('user_grade',order_by)
                user_grade = TCoreUserDetail.objects.order_by('-employee_grade__cg_name')
                # print('user_grade_desc',user_grade)
                grade_list = []
                for u_g in user_grade:
                    grade_id = u_g.employee_grade.id if u_g.employee_grade else None
                    grade_list.append(grade_id)
                # print('grade_list',grade_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(grade_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=grade_list).extra(select={'ordering': ordering},
                                                                         order_by=('ordering',))
                # print('queryset',queryset)
                return queryset

            if field_name == 'designation' and order_by == 'desc':
                # print('user_grade',order_by)
                user_designation = TCoreUserDetail.objects.order_by('-designation__cod_name')
                # print('user_designation_desc',user_designation)
                designation_list = []
                for u_g in user_designation:
                    designation_id = u_g.cu_user.id
                    designation_list.append(designation_id)
                # print('designation_list',designation_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(designation_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=designation_list).extra(select={'ordering': ordering},
                                                                               order_by=('ordering',))
                # print('queryset',queryset)
                return queryset

            if field_name == 'designation' and order_by == 'asc':
                # print('user_grade',order_by)
                user_designation = TCoreUserDetail.objects.order_by('designation__cod_name')
                # print('user_designation_desc',user_designation)
                designation_list = []
                for u_g in user_designation:
                    designation_id = u_g.cu_user.id
                    designation_list.append(designation_id)
                # print('designation_list',designation_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(designation_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=designation_list).extra(select={'ordering': ordering},
                                                                               order_by=('ordering',))
                # print('queryset',queryset)
                return queryset

            if field_name == 'department' and order_by == 'asc':
                # print('user_department',order_by)
                user_department = TCoreUserDetail.objects.order_by('department__cd_name')
                # print('user_department_asc',user_department)
                department_list = []
                for u_g in user_department:
                    department_id = u_g.cu_user.id
                    department_list.append(department_id)
                # print('department_list',department_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(department_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=department_list).extra(select={'ordering': ordering},
                                                                              order_by=('ordering',))
                # print('queryset',queryset)
                return queryset

            if field_name == 'department' and order_by == 'desc':
                # print('user_department',order_by)
                user_department = TCoreUserDetail.objects.order_by('-department__cd_name')
                # print('user_department_asc',user_department)
                department_list = []
                for u_g in user_department:
                    department_id = u_g.cu_user.id
                    department_list.append(department_id)
                # print('department_list',department_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(department_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=department_list).extra(select={'ordering': ordering},
                                                                              order_by=('ordering',))
                # print('queryset',queryset)
                return queryset

            if field_name == 'company' and order_by == 'desc':
                # print('user_department',order_by)
                user_company = TCoreUserDetail.objects.order_by('-company__coc_name')
                # print('user_company_asc',user_company)
                company_list = []
                for u_g in user_company:
                    company_id = u_g.cu_user.id
                    company_list.append(company_id)
                # print('company_list',company_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(company_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=company_list).extra(select={'ordering': ordering},
                                                                           order_by=('ordering',))
                # print('queryset',queryset)
                return queryset

            if field_name == 'company' and order_by == 'asc':
                # print('user_department',order_by)
                user_company = TCoreUserDetail.objects.order_by('company__coc_name')
                # print('user_company_asc',user_company)
                company_list = []
                for u_g in user_company:
                    company_id = u_g.cu_user.id
                    company_list.append(company_id)
                # print('company_list',company_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(company_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=company_list).extra(select={'ordering': ordering},
                                                                           order_by=('ordering',))
                # print('queryset',queryset)
                return queryset

            if field_name == 'sap_no' and order_by == 'asc':
                # print('user_department',order_by)
                user_sap_no_details = TCoreUserDetail.objects.order_by('sap_personnel_no')
                # print('user_sap_no_details_asc',user_sap_no_details)
                sap_no_details_list = []
                for u_g in user_sap_no_details:
                    sap_no_details_id = u_g.cu_user.id
                    sap_no_details_list.append(sap_no_details_id)
                # print('sap_no_details_list',sap_no_details_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(sap_no_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=sap_no_details_list).extra(select={'ordering': ordering},
                                                                                  order_by=('ordering',))
                # print('queryset',queryset)
                return queryset

            if field_name == 'sap_no' and order_by == 'desc':
                # print('user_department',order_by)
                user_sap_no_details = TCoreUserDetail.objects.order_by('-sap_personnel_no')
                # print('user_sap_no_details_asc',user_sap_no_details)
                sap_no_details_list = []
                for u_g in user_sap_no_details:
                    sap_no_details_id = u_g.cu_user.id
                    sap_no_details_list.append(sap_no_details_id)
                # print('sap_no_details_list',sap_no_details_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(sap_no_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=sap_no_details_list).extra(select={'ordering': ordering},
                                                                                  order_by=('ordering',))
                # print('queryset',queryset)
                return queryset

            if field_name == 'initial_ctc' and order_by == 'desc':
                # print('user_department',order_by)
                user_initial_ctc_details = TCoreUserDetail.objects.order_by('-initial_ctc')
                # print('user_initial_ctc_details_asc',user_initial_ctc_details)
                initial_ctc_details_list = []
                for u_g in user_initial_ctc_details:
                    initial_ctc_details_id = u_g.cu_user.id
                    initial_ctc_details_list.append(initial_ctc_details_id)
                # print('initial_ctc_details_list',initial_ctc_details_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(initial_ctc_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=initial_ctc_details_list).extra(select={'ordering': ordering},
                                                                                       order_by=('ordering',))
                # print('queryset',queryset)
                return queryset

            if field_name == 'initial_ctc' and order_by == 'asc':
                # print('user_department',order_by)
                user_initial_ctc_details = TCoreUserDetail.objects.order_by('initial_ctc')
                # print('user_initial_ctc_details_asc',user_initial_ctc_details)
                initial_ctc_details_list = []
                for u_g in user_initial_ctc_details:
                    initial_ctc_details_id = u_g.cu_user.id
                    initial_ctc_details_list.append(initial_ctc_details_id)
                # print('initial_ctc_details_list',initial_ctc_details_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(initial_ctc_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=initial_ctc_details_list).extra(select={'ordering': ordering},
                                                                                       order_by=('ordering',))
                # print('queryset',queryset)
                return queryset

            if field_name == 'current_ctc' and order_by == 'desc':
                # print('user_department',order_by)
                user_current_ctc_details = TCoreUserDetail.objects.order_by('-current_ctc')
                # print('user_current_ctc_details_asc',user_current_ctc_details)
                current_ctc_details_list = []
                for u_g in user_current_ctc_details:
                    current_ctc_details_id = u_g.cu_user.id
                    current_ctc_details_list.append(current_ctc_details_id)
                # print('current_ctc_details_list',current_ctc_details_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(current_ctc_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=current_ctc_details_list).extra(select={'ordering': ordering},
                                                                                       order_by=('ordering',))
                # print('queryset',queryset)
                return queryset

            if field_name == 'current_ctc' and order_by == 'asc':
                # print('user_department',order_by)
                user_current_ctc_details = TCoreUserDetail.objects.order_by('current_ctc')
                # print('user_current_ctc_details_asc',user_current_ctc_details)
                current_ctc_details_list = []
                for u_g in user_current_ctc_details:
                    current_ctc_details_id = u_g.cu_user.id
                    current_ctc_details_list.append(current_ctc_details_id)
                # print('current_ctc_details_list',current_ctc_details_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(current_ctc_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=current_ctc_details_list).extra(select={'ordering': ordering},
                                                                                       order_by=('ordering',))
                # print('queryset',queryset)
                return queryset

            if field_name == 'granted_cl' and order_by == 'asc':
                # print('user_department',order_by)
                user_granted_cl_details = TCoreUserDetail.objects.order_by('current_ctc')
                # print('user_current_ctc_details_asc',user_granted_cl_details)
                granted_cl_details_list = []
                for u_g in user_granted_cl_details:
                    granted_cl_details_id = u_g.cu_user.id
                    granted_cl_details_list.append(granted_cl_details_id)
                # print('current_ctc_details_list',granted_cl_details_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(granted_cl_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=granted_cl_details_list).extra(select={'ordering': ordering},
                                                                                      order_by=('ordering',))
                # print('queryset',queryset)
                return queryset

            if field_name == 'granted_cl' and order_by == 'desc':
                # print('user_department',order_by)
                user_granted_cl_details = TCoreUserDetail.objects.order_by('-granted_cl')
                # print('user_current_ctc_details_asc',user_granted_cl_details)
                granted_cl_details_list = []
                for u_g in user_granted_cl_details:
                    granted_cl_details_id = u_g.cu_user.id
                    granted_cl_details_list.append(granted_cl_details_id)
                # print('current_ctc_details_list',granted_cl_details_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(granted_cl_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=granted_cl_details_list).extra(select={'ordering': ordering},
                                                                                      order_by=('ordering',))
                # print('queryset',queryset)
                return queryset

            if field_name == 'granted_sl' and order_by == 'desc':
                # print('user_department',order_by)
                user_granted_sl_details = TCoreUserDetail.objects.order_by('-granted_sl')
                # print('user_current_ctc_details_asc', user_granted_sl_details)
                granted_sl_details_list = []
                for u_g in user_granted_sl_details:
                    granted_sl_details_id = u_g.cu_user.id
                    granted_sl_details_list.append(granted_sl_details_id)
                # print('current_ctc_details_list', granted_sl_details_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(granted_sl_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=granted_sl_details_list).extra(select={'ordering': ordering},
                                                                                      order_by=('ordering',))
                # print('queryset', queryset)
                return queryset

            if field_name == 'granted_sl' and order_by == 'asc':
                # print('user_department',order_by)
                user_granted_sl_details = TCoreUserDetail.objects.order_by('granted_sl')
                # print('user_current_ctc_details_asc', user_granted_sl_details)
                granted_sl_details_list = []
                for u_g in user_granted_sl_details:
                    granted_sl_details_id = u_g.cu_user.id
                    granted_sl_details_list.append(granted_sl_details_id)
                # print('current_ctc_details_list', granted_sl_details_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(granted_sl_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=granted_sl_details_list).extra(select={'ordering': ordering},
                                                                                      order_by=('ordering',))
                # print('queryset', queryset)
                return queryset

            if field_name == 'granted_el' and order_by == 'desc':
                # print('user_department',order_by)
                user_granted_el_details = TCoreUserDetail.objects.order_by('-granted_el')
                # print('user_current_ctc_details_asc', user_granted_el_details)
                granted_el_details_list = []
                for u_g in user_granted_el_details:
                    granted_el_details_id = u_g.cu_user.id
                    granted_el_details_list.append(granted_el_details_id)
                # print('current_ctc_details_list', granted_el_details_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(granted_el_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=granted_el_details_list).extra(select={'ordering': ordering},
                                                                                      order_by=('ordering',))
                # print('queryset', queryset)
                return queryset

            if field_name == 'granted_el' and order_by == 'asc':
                # print('user_department',order_by)
                user_granted_el_details = TCoreUserDetail.objects.order_by('granted_el')
                # print('user_current_ctc_details_asc', user_granted_el_details)
                granted_el_details_list = []
                for u_g in user_granted_el_details:
                    granted_el_details_id = u_g.cu_user.id
                    granted_el_details_list.append(granted_el_details_id)
                # print('current_ctc_details_list', granted_el_details_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(granted_el_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=granted_el_details_list).extra(select={'ordering': ordering},
                                                                                      order_by=('ordering',))
                # print('queryset', queryset)
                return queryset

            if field_name == 'total_experience' and order_by == 'desc':
                # print('user_department',order_by)
                user_total_experience_details = TCoreUserDetail.objects.order_by('-total_experience')
                # print('user_current_ctc_details_asc', user_total_experience_details)
                total_experience_details_list = []
                for u_g in user_total_experience_details:
                    total_experience_details_id = u_g.cu_user.id
                    total_experience_details_list.append(total_experience_details_id)
                # print('current_ctc_details_list', total_experience_details_list)
                clauses = ' '.join(
                    ['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(total_experience_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=total_experience_details_list).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset', queryset)
                return queryset

            if field_name == 'total_experience' and order_by == 'asc':
                # print('user_department',order_by)
                user_total_experience_details = TCoreUserDetail.objects.order_by('total_experience')
                # print('user_current_ctc_details_asc', user_total_experience_details)
                total_experience_details_list = []
                for u_g in user_total_experience_details:
                    total_experience_details_id = u_g.cu_user.id
                    total_experience_details_list.append(total_experience_details_id)
                # print('current_ctc_details_list', total_experience_details_list)
                clauses = ' '.join(
                    ['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(total_experience_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=total_experience_details_list).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset', queryset)
                return queryset

            if field_name == 'cu_emp_code' and order_by == 'asc':
                # print('user_department',order_by)
                user_total_experience_details = TCoreUserDetail.objects.order_by('cu_emp_code')
                # print('user_current_ctc_details_asc', user_total_experience_details)
                total_experience_details_list = []
                for u_g in user_total_experience_details:
                    total_experience_details_id = u_g.cu_user.id
                    total_experience_details_list.append(total_experience_details_id)
                # print('current_ctc_details_list', total_experience_details_list)
                clauses = ' '.join(
                    ['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(total_experience_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=total_experience_details_list).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset', queryset)
                return queryset

            if field_name == 'cu_emp_code' and order_by == 'desc':
                # print('user_department',order_by)
                user_total_experience_details = TCoreUserDetail.objects.order_by('-cu_emp_code')
                # print('user_current_ctc_details_asc', user_total_experience_details)
                total_experience_details_list = []
                for u_g in user_total_experience_details:
                    total_experience_details_id = u_g.cu_user.id
                    total_experience_details_list.append(total_experience_details_id)
                # print('current_ctc_details_list', total_experience_details_list)
                clauses = ' '.join(
                    ['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(total_experience_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=total_experience_details_list).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset', queryset)
                return queryset

            if field_name == 'cu_alt_email_id' and order_by == 'asc':
                # print('user_department',order_by)
                user_total_experience_details = TCoreUserDetail.objects.order_by('cu_alt_email_id')
                # print('user_current_ctc_details_asc', user_total_experience_details)
                total_experience_details_list = []
                for u_g in user_total_experience_details:
                    total_experience_details_id = u_g.cu_user.id
                    total_experience_details_list.append(total_experience_details_id)
                # print('current_ctc_details_list', total_experience_details_list)
                clauses = ' '.join(
                    ['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(total_experience_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=total_experience_details_list).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset', queryset)
                return queryset

            if field_name == 'cu_alt_email_id' and order_by == 'desc':
                # print('user_department',order_by)
                user_total_experience_details = TCoreUserDetail.objects.order_by('-cu_alt_email_id')
                # print('user_current_ctc_details_asc', user_total_experience_details)
                total_experience_details_list = []
                for u_g in user_total_experience_details:
                    total_experience_details_id = u_g.cu_user.id
                    total_experience_details_list.append(total_experience_details_id)
                # print('current_ctc_details_list', total_experience_details_list)
                clauses = ' '.join(
                    ['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(total_experience_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=total_experience_details_list).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset', queryset)
                return queryset

        elif search_keyword:
            self.queryset = TCoreUserDetail.objects.filter(cu_user__is_superuser=False)
            # print('self.queryset',self.queryset)
            f_name = search_keyword.split(' ')[0]
            l_name = ' '.join(search_keyword.split(' ')[1:])
            # print(l_name)

            if l_name:
                queryset = self.queryset.filter(
                    Q(cu_user__first_name__icontains=f_name) |
                    Q(cu_user__last_name__icontains=l_name) |
                    Q(cu_user__email__icontains=search_keyword) |
                    Q(cu_alt_email_id__icontains=search_keyword)
                )
            else:
                queryset = self.queryset.filter(
                    Q(cu_user__first_name__icontains=f_name) |
                    Q(cu_user__email__icontains=search_keyword) |
                    Q(cu_alt_email_id__icontains=search_keyword)
                )
            # print('queryset',queryset.query)
            return queryset

        else:
            queryset = self.queryset.all()
            return queryset

    def get(self, request, *args, **kwargs):
        response = super(__class__, self).get(self, request, args, kwargs)

        # print('response check::::::::::::::',response.data)
        list_type = self.request.query_params.get('list_type', None)
        module_id = self.request.query_params.get('module_id', None)
        search_keyword = self.request.query_params.get('search_keyword', None)
        download = self.request.query_params.get('download', None)
        # print('module_id',module_id)
        p_doc_dict = {}
        data_list = list()
        for data in response.data:
            if list_type == "professional":
                professional_details = TCoreUserDetail.objects.filter(cu_user=data['id']).values(
                    'cu_emp_code', 'sap_personnel_no', 'initial_ctc', 'current_ctc', 'cu_punch_id',
                    'cost_centre', 'granted_cl', 'granted_sl', 'granted_el')

                if search_keyword:
                    professional_details = TCoreUserDetail.objects.filter(pk=data['id']).values(
                        'cu_emp_code', 'sap_personnel_no', 'initial_ctc', 'current_ctc', 'cu_punch_id',
                        'cost_centre', 'granted_cl', 'granted_sl', 'granted_el', 'cu_user__first_name',
                        'cu_user__last_name', 'cu_user__id')
                    data['first_name'] = professional_details[0]['cu_user__first_name'] if professional_details[0][
                        'cu_user__first_name'] else ''
                    data['last_name'] = professional_details[0]['cu_user__last_name'] if professional_details[0][
                        'cu_user__last_name'] else ''
                    data['name'] = data['first_name'] + ' ' + data['last_name']
                    data['id'] = User.objects.only('id').get(pk=professional_details[0]['cu_user__id']).id

                # print('professional_details',professional_details)

                if professional_details:
                    data['emp_code'] = professional_details[0]['cu_emp_code'] if professional_details[0][
                        'cu_emp_code'] else None
                    data['cu_punch_id'] = professional_details[0]['cu_punch_id'] if professional_details[0][
                        'cu_punch_id'] else None
                    data['sap_personnel_no'] = professional_details[0]['sap_personnel_no'] if professional_details[0][
                        'sap_personnel_no'] else None
                    data['initial_ctc'] = professional_details[0]['initial_ctc'] if professional_details[0][
                        'initial_ctc'] else None
                    data['current_ctc'] = professional_details[0]['current_ctc'] if professional_details[0][
                        'current_ctc'] else None
                    data['cost_centre'] = professional_details[0]['cost_centre'] if professional_details[0][
                        'cost_centre'] else None
                    data['granted_cl'] = professional_details[0]['granted_cl'] if professional_details[0][
                        'granted_cl'] else None
                    data['granted_sl'] = professional_details[0]['granted_sl'] if professional_details[0][
                        'granted_sl'] else None
                    data['granted_el'] = professional_details[0]['granted_el'] if professional_details[0][
                        'granted_el'] else None

                    user_benefits = HrmsUsersBenefits.objects.filter(user=data['id'], is_deleted=False)
                    benefits_list = []
                    ben_list = ''
                    alow_list = ''
                    if user_benefits:
                        for u_b in user_benefits:
                            benefits = {
                                'id': u_b.id,
                                'benefits': u_b.benefits.id if u_b.benefits else '',
                                'benefits_name': u_b.benefits.benefits_name if u_b.benefits else '',
                                'allowance': u_b.allowance
                            }
                            ben_list = ben_list + ',' + u_b.benefits.benefits_name
                            alow_list = alow_list + ',' + u_b.allowance
                            benefits_list.append(benefits)
                        data['benefits_provided'] = benefits_list
                    else:
                        data['benefits_provided'] = []
                    other_facilities = HrmsUsersOtherFacilities.objects.filter(user=data['id'], is_deleted=False)
                    facilities_list = []
                    if other_facilities:
                        for o_f in other_facilities:
                            facility = {
                                'id': o_f.id,
                                'other_facilities': o_f.other_facilities,
                            }
                            facilities_list.append(facility)
                        data['other_facilities'] = facilities_list
                    else:
                        data['other_facilities'] = []
                    p_doc_list = []
                    professional_documents = HrmsDocument.objects.filter(user=data['id'], is_deleted=False)
                    if professional_documents:
                        for doc_details in professional_documents:
                            if (doc_details.tab_name).lower() == "professional":
                                if doc_details.__dict__['document'] == "":
                                    file_url = ''
                                else:
                                    file_url = request.build_absolute_uri(doc_details.document.url)
                                if doc_details.__dict__['document_name'] == "":
                                    doc_name = ""
                                else:
                                    doc_name = doc_details.document_name

                                p_doc_dict = {
                                    'tab_name': doc_details.tab_name if doc_details.tab_name else None,
                                    'field_label': doc_details.field_label if doc_details.field_label else None,
                                    'document_name': doc_name,
                                    'document': file_url
                                }
                                p_doc_list.append(p_doc_dict)
                        data['documents'] = p_doc_list
                    else:
                        data['documents'] = []

                    # Active status added by Shubhadeep
                    data_list.append([data['first_name'], data['last_name'], data['emp_code'], data['sap_personnel_no'],
                                      data['cu_punch_id'],
                                      data['initial_ctc'], data['current_ctc'], data['cost_centre'], ben_list,
                                      alow_list, 'Active' if data['is_active'] else 'Inactive'])

            if list_type == "role":
                role_details = TCoreUserDetail.objects.filter(cu_user=data['id']).values('cu_user__username',
                                                                                         'cu_user__first_name',
                                                                                         'cu_user__last_name',
                                                                                         'cu_emp_code',
                                                                                         'cu_alt_phone_no',
                                                                                         'cu_alt_email_id',
                                                                                         'company__id',
                                                                                         'company__coc_name',
                                                                                         'job_description', 'hod__id',
                                                                                         'hod__first_name',
                                                                                         'hod__last_name',
                                                                                         'designation__id',
                                                                                         'cu_user__id',
                                                                                         'designation__cod_name',
                                                                                         'department__id',
                                                                                         'department__cd_name',
                                                                                         'reporting_head__id',
                                                                                         'reporting_head__first_name',
                                                                                         'reporting_head__last_name',
                                                                                         'employee_grade__id',
                                                                                         'employee_grade__cg_name',
                                                                                         'employee_sub_grade',
                                                                                         'sub_department__cd_name')

                if search_keyword:
                    role_details = TCoreUserDetail.objects.filter(pk=data['id']).values('cu_user__username',
                                                                                        'cu_user__first_name',
                                                                                        'cu_user__last_name',
                                                                                        'cu_emp_code', 'cu_user__id',
                                                                                        'cu_alt_phone_no',
                                                                                        'cu_alt_email_id',
                                                                                        'company__id',
                                                                                        'company__coc_name',
                                                                                        'job_description', 'hod__id',
                                                                                        'hod__first_name',
                                                                                        'hod__last_name',
                                                                                        'designation__id',
                                                                                        'designation__cod_name',
                                                                                        'department__id',
                                                                                        'employee_grade__id',
                                                                                        'department__cd_name',
                                                                                        'reporting_head__id',
                                                                                        'reporting_head__first_name',
                                                                                        'reporting_head__last_name',
                                                                                        'employee_grade__cg_name',
                                                                                        'employee_sub_grade',
                                                                                        'sub_department__cd_name')

                if role_details:
                    first_name = role_details[0]['cu_user__first_name'] if role_details[0][
                        'cu_user__first_name'] else ''
                    last_name = role_details[0]['cu_user__last_name'] if role_details[0]['cu_user__last_name'] else ''
                    data['id'] = role_details[0]['cu_user__id']
                    data['name'] = first_name + " " + last_name
                    data['first_name'] = first_name
                    data['last_name'] = last_name
                    data['username'] = role_details[0]['cu_user__username'] if role_details[0][
                        'cu_user__username'] else None
                    data['emp_code'] = role_details[0]['cu_emp_code'] if role_details[0]['cu_emp_code'] else None
                    data['official_contact_no'] = role_details[0]['cu_alt_phone_no'] if role_details[0][
                        'cu_alt_phone_no'] else None
                    data['official_email_id'] = role_details[0]['cu_alt_email_id'] if role_details[0][
                        'cu_alt_email_id'] else None
                    data['company'] = role_details[0]['company__id'] if role_details[0]['company__id'] else None
                    data['company_name'] = role_details[0]['company__coc_name'] if role_details[0][
                        'company__coc_name'] else None
                    data['job_description'] = role_details[0]['job_description'] if role_details[0][
                        'job_description'] else None
                    data['hod_id'] = role_details[0]['hod__id'] if role_details[0]['hod__id'] else None
                    data['sub_department_name'] = role_details[0]['sub_department__cd_name'] if role_details[0][
                        'sub_department__cd_name'] else None

                    hod__first_name = role_details[0]['hod__first_name'] if role_details[0]['hod__first_name'] else ''
                    hod__last_name = role_details[0]['hod__last_name'] if role_details[0]['hod__last_name'] else ''

                    data['hod'] = hod__first_name + " " + hod__last_name

                    data['designation_id'] = role_details[0]['designation__id'] if role_details[0][
                        'designation__id'] else None
                    data['designation_name'] = role_details[0]['designation__cod_name'] if role_details[0][
                        'designation__cod_name'] else None
                    data['department_id'] = role_details[0]['department__id'] if role_details[0][
                        'department__id'] else None
                    data['department_name'] = role_details[0]['department__cd_name'] if role_details[0][
                        'department__cd_name'] else None

                    data['reporting_head_id'] = role_details[0]['reporting_head__id'] if role_details[0][
                        'reporting_head__id'] else None

                    reporting_head__first_name = role_details[0]['reporting_head__first_name'] if role_details[0][
                        'reporting_head__first_name'] else ''
                    reporting_head__last_name = role_details[0]['reporting_head__last_name'] if role_details[0][
                        'reporting_head__last_name'] else ''

                    data['reporting_head_name'] = reporting_head__first_name + " " + reporting_head__last_name
                    # data['employee_grade_name']=role_details[0]['employee_grade__cg_name'] if role_details[0]['employee_grade__id'] else None
                    # data['employee_grade_id']=role_details[0]['employee_grade__id'] if role_details[0]['employee_grade__id'] else None
                    grade_details = TCoreGrade.objects.filter(id=role_details[0]['employee_grade__id'],
                                                              cg_is_deleted=False)
                    if grade_details:
                        grade_details = \
                        TCoreGrade.objects.filter(id=role_details[0]['employee_grade__id'], cg_is_deleted=False)[0]
                        if grade_details:
                            grade_dict = dict()
                            print('grade_details', grade_details.id)
                            if grade_details.cg_parent_id != 0:
                                parent = TCoreGrade.objects.filter(id=grade_details.cg_parent_id, cg_is_deleted=False)
                                for p_d in parent:
                                    grade_dict['id'] = p_d.id
                                    grade_dict['cg_name'] = p_d.cg_name

                                grade_dict['child'] = {
                                    "id": grade_details.id,
                                    "cg_name": grade_details.cg_name
                                }
                            else:
                                grade_dict['id'] = grade_details.id
                                grade_dict['cg_name'] = grade_details.cg_name
                                grade_dict['child'] = None

                            print('grade_dict', grade_dict)

                            data['grade_details'] = grade_dict
                        else:
                            data['grade_details'] = None
                    else:
                        data['grade_details'] = None
                    if role_details[0]['employee_sub_grade']:
                        sub_grade = TCoreSubGrade.objects.get(id=role_details[0]['employee_sub_grade'])
                        data['sub_grade'] = sub_grade.name
                    else:
                        data['sub_grade'] = ""

                    # Active status added by Shubhadeep
                    data_list.append([data['first_name'], data['last_name'], data['username'], data['emp_code'],
                                      data['department_name'], data['designation_name'], data['company_name'],
                                      data['hod'], data['reporting_head_name'],
                                      data['official_contact_no'], data['official_email_id'], data['job_description'],
                                      data['sub_grade'],
                                      'Active' if data['is_active'] else 'Inactive'])

            if list_type == "personal":
                personal_details = TCoreUserDetail.objects.filter(cu_user=data['id'])
                if search_keyword:
                    personal_details = TCoreUserDetail.objects.filter(pk=data['id'])

                if personal_details:
                    for p_d in personal_details:
                        data['id'] = p_d.cu_user.id
                        data['first_name'] = p_d.cu_user.first_name if p_d.cu_user.first_name else ''
                        data['last_name'] = p_d.cu_user.last_name if p_d.cu_user.last_name else ''
                        data['name'] = data['first_name'] + ' ' + data['last_name']
                        data['emp_code'] = p_d.cu_emp_code
                        data['personal_contact_no'] = p_d.cu_phone_no
                        data['personal_email_id'] = p_d.cu_user.email
                        data['address'] = p_d.address
                        data['blood_group'] = p_d.blood_group
                        data['photo'] = request.build_absolute_uri(
                            p_d.cu_profile_img.url) if p_d.cu_profile_img else None
                        data['total_experience'] = p_d.total_experience

                        licenses_and_certifications_dict = {}
                        work_experience_dict = {}
                        add_more_files_dict = {}
                        personal_documents = HrmsDynamicSectionFieldLabelDetailsWithDoc.objects.filter(user=data['id'],
                                                                                                       is_deleted=False)
                        # print("personal_documents",personal_documents)
                        if personal_documents:
                            licenses_and_certifications_list = []
                            add_more_files_list = []
                            work_experience_list = []
                            for doc_details in personal_documents:
                                if (doc_details.tab_name).lower() == "personal":
                                    if doc_details.__dict__['document'] == "":
                                        file_url = ''
                                    else:
                                        file_url = request.build_absolute_uri(doc_details.document.url)

                                    if doc_details.__dict__['document_name'] == "":
                                        doc_name = ""
                                    else:
                                        doc_name = doc_details.document_name

                                    if doc_details.field_label == "Licenses and Certifications":
                                        licenses_and_certifications_dict = {
                                            'id': doc_details.id,
                                            'field_label_value': doc_details.field_label_value if doc_details.field_label_value else None,
                                            'document_name': doc_name,
                                            'document': file_url
                                        }
                                        licenses_and_certifications_list.append(licenses_and_certifications_dict)

                                    if doc_details.field_label == "Work Experience":
                                        work_experience_dict = {
                                            'id': doc_details.id,
                                            'field_label_value': doc_details.field_label_value if doc_details.field_label_value else None,
                                            'document_name': doc_name,
                                            'document': file_url
                                        }
                                        work_experience_list.append(work_experience_dict)

                            data[
                                'licenses_and_certifications_doc'] = licenses_and_certifications_list if licenses_and_certifications_list else []
                            data['work_experience_doc'] = work_experience_list if work_experience_list else []

                        else:
                            data['licenses_and_certifications_doc'] = []
                            data['work_experience_doc'] = []

                        academic_qualification_l = ''
                        academic_qualification = HrmsUserQualification.objects.filter(user=data['id'], is_deleted=False)
                        # print('academic_qualification',academic_qualification)
                        if academic_qualification:
                            academic_qualification_list = []
                            academic_qualification_dict = {}
                            for a_q in academic_qualification:
                                academic_qualification_dict = {
                                    'id': a_q.id,
                                    'qualification': a_q.qualification.id,
                                    'qualification_name': a_q.qualification.name,
                                    'details': a_q.details
                                }
                                if academic_qualification_l:
                                    academic_qualification_l = academic_qualification_l + ',' + a_q.qualification.name
                                else:
                                    academic_qualification_l = a_q.qualification.name
                                academic_doc = HrmsUserQualificationDocument.objects.filter(user_qualification=a_q.id,
                                                                                            is_deleted=False)
                                # print('academic_doc',academic_doc)
                                if academic_doc:
                                    academic_doc_dict = {}
                                    academic_doc_list = []
                                    for a_d in academic_doc:
                                        academic_doc_dict = {
                                            'id': a_d.id,
                                            'document': request.build_absolute_uri(a_d.document.url)
                                        }
                                        academic_doc_list.append(academic_doc_dict)
                                    academic_qualification_dict['qualification_doc'] = academic_doc_list
                                else:
                                    academic_qualification_dict['qualification_doc'] = []
                                academic_qualification_list.append(academic_qualification_dict)
                            data['academic_qualification'] = academic_qualification_list
                        else:
                            data['academic_qualification'] = []

                        # Active status added by Shubhadeep
                        data_list.append([data['first_name'], data['last_name'], data['emp_code'],
                                          data['personal_contact_no'], data['personal_email_id'], data['address'],
                                          data['blood_group'],
                                          data['total_experience'], academic_qualification_l,
                                          'Active' if data['is_active'] else 'Inactive'])

            if list_type == 'resignation' or list_type == 'release' or list_type == 'employee-list-by-type':
                '''
                    Reason : Fetch Resignation employee list
                    Author : Rupam Hazra 
                    Line number:  1245 - 1337
                    Date : 19/02/2020
                '''
                # time.sleep(10)
                role_details = TCoreUserDetail.objects.filter(
                    cu_user=data['id']).values(
                    'cu_user__username', 'cu_user__first_name', 'cu_user__last_name',
                    'cu_emp_code', 'cu_alt_phone_no', 'cu_alt_email_id', 'company__id', 'company__coc_name',
                    'job_description', 'hod__id', 'hod__first_name', 'hod__last_name', 'designation__id', 'cu_user__id',
                    'designation__cod_name', 'department__id', 'department__cd_name', 'reporting_head__id',
                    'reporting_head__first_name', 'reporting_head__last_name',
                    'employee_grade__id', 'employee_grade__cg_name', 'sap_personnel_no', 'cu_punch_id',
                    'termination_date', 'resignation_date')

                if search_keyword:
                    role_details = TCoreUserDetail.objects.filter(pk=data['id']).values('cu_user__username',
                                                                                        'cu_user__first_name',
                                                                                        'cu_user__last_name',
                                                                                        'cu_emp_code', 'cu_user__id',
                                                                                        'cu_alt_phone_no',
                                                                                        'cu_alt_email_id',
                                                                                        'company__id',
                                                                                        'company__coc_name',
                                                                                        'job_description', 'hod__id',
                                                                                        'hod__first_name',
                                                                                        'hod__last_name',
                                                                                        'designation__id',
                                                                                        'designation__cod_name',
                                                                                        'department__id',
                                                                                        'employee_grade__id',
                                                                                        'department__cd_name',
                                                                                        'reporting_head__id',
                                                                                        'reporting_head__first_name',
                                                                                        'reporting_head__last_name',
                                                                                        'employee_grade__cg_name',
                                                                                        'sap_personnel_no',
                                                                                        'cu_punch_id',
                                                                                        'termination_date',
                                                                                        'resignation_date')

                if role_details:
                    first_name = role_details[0]['cu_user__first_name'] if role_details[0][
                        'cu_user__first_name'] else ''
                    last_name = role_details[0]['cu_user__last_name'] if role_details[0]['cu_user__last_name'] else ''
                    data['id'] = role_details[0]['cu_user__id']
                    data['name'] = first_name + " " + last_name
                    data['first_name'] = first_name
                    data['last_name'] = last_name
                    data['username'] = role_details[0]['cu_user__username'] if role_details[0][
                        'cu_user__username'] else None
                    data['emp_code'] = role_details[0]['cu_emp_code'] if role_details[0]['cu_emp_code'] else None
                    data['official_contact_no'] = role_details[0]['cu_alt_phone_no'] if role_details[0][
                        'cu_alt_phone_no'] else None
                    data['official_email_id'] = role_details[0]['cu_alt_email_id'] if role_details[0][
                        'cu_alt_email_id'] else None
                    data['company'] = role_details[0]['company__id'] if role_details[0]['company__id'] else None
                    data['company_name'] = role_details[0]['company__coc_name'] if role_details[0][
                        'company__coc_name'] else None
                    data['job_description'] = role_details[0]['job_description'] if role_details[0][
                        'job_description'] else None
                    data['hod_id'] = role_details[0]['hod__id'] if role_details[0]['hod__id'] else None
                    data['sap_personnel_no'] = role_details[0]['sap_personnel_no'] if role_details[0][
                        'sap_personnel_no'] else None
                    data['cu_punch_id'] = role_details[0]['cu_punch_id'] if role_details[0]['cu_punch_id'] else None
                    data['termination_date'] = role_details[0]['termination_date'] if role_details[0][
                        'termination_date'] else None
                    data['resignation_date'] = role_details[0]['resignation_date'] if role_details[0][
                        'resignation_date'] else None

                    hod__first_name = role_details[0]['hod__first_name'] if role_details[0]['hod__first_name'] else ''
                    hod__last_name = role_details[0]['hod__last_name'] if role_details[0]['hod__last_name'] else ''

                    data['hod'] = hod__first_name + " " + hod__last_name

                    data['designation_id'] = role_details[0]['designation__id'] if role_details[0][
                        'designation__id'] else None
                    data['designation_name'] = role_details[0]['designation__cod_name'] if role_details[0][
                        'designation__cod_name'] else None
                    data['department_id'] = role_details[0]['department__id'] if role_details[0][
                        'department__id'] else None
                    data['department_name'] = role_details[0]['department__cd_name'] if role_details[0][
                        'department__cd_name'] else None

                    data['reporting_head_id'] = role_details[0]['reporting_head__id'] if role_details[0][
                        'reporting_head__id'] else None

                    reporting_head__first_name = role_details[0]['reporting_head__first_name'] if role_details[0][
                        'reporting_head__first_name'] else ''
                    reporting_head__last_name = role_details[0]['reporting_head__last_name'] if role_details[0][
                        'reporting_head__last_name'] else ''

                    data['reporting_head_name'] = reporting_head__first_name + " " + reporting_head__last_name
                    # data['employee_grade_name']=role_details[0]['employee_grade__cg_name'] if role_details[0]['employee_grade__id'] else None
                    # data['employee_grade_id']=role_details[0]['employee_grade__id'] if role_details[0]['employee_grade__id'] else None
                    grade_details = TCoreGrade.objects.filter(id=role_details[0]['employee_grade__id'],
                                                              cg_is_deleted=False)
                    if grade_details:
                        grade_details = \
                        TCoreGrade.objects.filter(id=role_details[0]['employee_grade__id'], cg_is_deleted=False)[0]
                        if grade_details:
                            grade_dict = dict()
                            print('grade_details', grade_details.id)
                            if grade_details.cg_parent_id != 0:
                                parent = TCoreGrade.objects.filter(id=grade_details.cg_parent_id, cg_is_deleted=False)
                                for p_d in parent:
                                    grade_dict['id'] = p_d.id
                                    grade_dict['cg_name'] = p_d.cg_name

                                grade_dict['child'] = {
                                    "id": grade_details.id,
                                    "cg_name": grade_details.cg_name
                                }
                            else:
                                grade_dict['id'] = grade_details.id
                                grade_dict['cg_name'] = grade_details.cg_name
                                grade_dict['child'] = None

                            print('grade_dict', grade_dict)

                            data['grade_details'] = grade_dict
                        else:
                            data['grade_details'] = None
                    else:
                        data['grade_details'] = None

                    # Active status added by Shubhadeep
                    data_list.append([data['first_name'], data['last_name'], data['emp_code'], data['sap_personnel_no'],
                                      data['cu_punch_id'],
                                      data['department_name'], data['designation_name'], data['company_name'],
                                      data['hod'], data['reporting_head_name'],
                                      data['official_contact_no'], data['official_email_id'], data['termination_date'],
                                      data['resignation_date'],
                                      'Active' if data['is_active'] else 'Inactive'])

        # print('data_list',data_list,type(data_list))

        file_name = ''
        if data_list:
            if os.path.isdir('media/hrms/employee_list/document'):
                file_name = 'media/hrms/employee_list/document/employee_list.xlsx'
                file_path = settings.MEDIA_ROOT_EXPORT + file_name
            else:
                os.makedirs('media/hrms/employee_list/document')
                file_name = 'media/hrms/employee_list/document/employee_list.xlsx'
                file_path = settings.MEDIA_ROOT_EXPORT + file_name

            # Active status added by Shubhadeep
            if list_type == "professional":
                final_df = pd.DataFrame(data_list,
                                        columns=['First Name', 'Last Name', 'Emp. Code', 'SAP Id', 'Access Code',
                                                 'Initial CTC',
                                                 'Current CTC', 'Cost centre', 'Benifits', 'Allowance Limits',
                                                 'Active'])

            # Active status added by Shubhadeep
            elif list_type == "role":
                final_df = pd.DataFrame(data_list,
                                        columns=['First Name', 'Last Name', 'Username', 'Emp. Code', 'Department',
                                                 'Designation', 'Company', 'HOD', 'Reporting Head',
                                                 'Official Contact No', 'Official Email Id', 'Job Description',
                                                 'Sub Grade', 'Active'])

                # Active status added by Shubhadeep
            elif list_type == "personal":
                final_df = pd.DataFrame(data_list, columns=['First Name', 'Last Name', 'Emp. Code',
                                                            'Personal Contact No', 'Personal Email Id', 'Address',
                                                            'Blood Gr.', 'Total Exp.', 'Academic Qualification',
                                                            'Active'])

                # Active status added by Shubhadeep
            else:
                final_df = pd.DataFrame(data_list,
                                        columns=['First Name', 'Last Name', 'Emp. Code', 'SAP Id', 'Punch Id',
                                                 'Department',
                                                 'Designation', 'Company', 'HOD', 'Reporting Head',
                                                 'Official Contact No', 'Official Email Id', 'Termination Date',
                                                 'Resignation Date', 'Active'])

            export_csv = final_df.to_excel(file_path, index=None, header=True)
            if request.is_secure():
                protocol = 'https://'
            else:
                protocol = 'http://'

        url = getHostWithPort(request) + file_name if file_name else None
        # response.data['url'] = url
        if url:
            return Response({'request_status': 1, 'msg': 'Success', 'url': url})
        else:
            return Response({'request_status': 0, 'msg': 'Not Found', 'url': url})


class EmployeeListWithoutDetailsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = User.objects.filter(is_superuser=False)
    serializer_class = EmployeeListWithoutDetailsSerializer
    pagination_class = OnOffPagination

    def get_queryset(self):
        search_key = self.request.query_params.get('search_key', None)
        department = self.request.query_params.get('department', None)
        module = self.request.query_params.get('module', None)
        team_approval_flag = self.request.query_params.get('team_approval_flag', None)
        login_user_details = self.request.user
        filter = dict()
        is_active = self.request.query_params.get('is_active', None)

        if is_active:
            if is_active == '1':
                filter['cu_is_deleted'] = False
                filter['cu_user__is_active'] = True
            else:
                filter['cu_is_deleted'] = True
                filter['cu_user__is_active'] = False

        if team_approval_flag == '1':
            filter['cu_is_deleted'] = False
            filter['cu_user__is_active'] = True

        # print('login_user_details',login_user_details,login_user_details.id)

        if login_user_details.is_superuser == False:
            # print("--------in if")
            if module == 'pms':
                module = 'PMS'
            if module == 'hrms':
                module = 'ATTENDANCE & HRMS'
            if module == 'ETASK' or module == 'etask':
                module = 'E-Task'
            which_type_of_user = TMasterModuleRoleUser.objects.filter(
                mmr_module__cm_name=module,
                mmr_user=login_user_details,
                mmr_is_deleted=False
            ).values_list('mmr_type', flat=True)
            if which_type_of_user:
                which_type_of_user = TMasterModuleRoleUser.objects.filter(
                    mmr_module__cm_name=module,
                    mmr_user=login_user_details,
                    mmr_is_deleted=False
                ).values_list('mmr_type', flat=True)[0]

            if team_approval_flag == '1' and module is not None:

                if which_type_of_user == 2:  # [module admin]
                    filter_users = TMasterModuleRoleUser.objects.filter(
                        mmr_type__in=('3'),
                        mmr_module__cm_name=module,
                        mmr_is_deleted=False,
                        mmr_user_id__in=TCoreUserDetail.objects.filter(**filter).values_list(
                            'cu_user_id', flat=True)).values_list('mmr_user_id', flat=True)

                else:
                    filter_users = TMasterModuleRoleUser.objects.filter(
                        mmr_type__in=('3'),
                        mmr_module__cm_name=module,
                        mmr_is_deleted=False,
                        mmr_user_id__in=TCoreUserDetail.objects.filter(
                            reporting_head_id=login_user_details, **filter).values_list(
                            'cu_user_id', flat=True)).values_list('mmr_user_id', flat=True)

                if search_key:
                    print("-------------------in se")
                    queryset = User.objects.annotate(full_name=Concat('first_name', V(' '), 'last_name')).filter(
                        full_name__icontains=search_key,
                        pk__in=(filter_users),
                        # is_active=True,
                        is_superuser=False
                    )
                    # print(search_key, queryset)
                else:
                    print("---------in else")
                    queryset = User.objects.filter(
                        pk__in=(filter_users),
                        # is_active=True,
                        is_superuser=False
                    )
                # print('queryset',queryset.query)
                return queryset

            elif team_approval_flag == '1' and module is None:
                if search_key:
                    queryset = User.objects.annotate(full_name=Concat('first_name', V(' '), 'last_name')).filter(
                        full_name__icontains=search_key, pk__in=(
                            TCoreUserDetail.objects.filter(reporting_head_id=login_user_details, **filter).values_list(
                                'cu_user_id', flat=True)))
                else:
                    queryset = User.objects.filter(pk__in=(
                        TCoreUserDetail.objects.filter(reporting_head_id=login_user_details, **filter).values_list(
                            'cu_user_id', flat=True)))
                return queryset

            elif team_approval_flag is None:
                # print('modulekkkkkkkkkkkkkkkkkkkkkkkkkk',module)
                # time.sleep(5)
                if module.lower() == "vms":
                    if search_key:
                        return self.queryset.annotate(full_name=Concat('first_name', V(' '), 'last_name')).filter(
                            full_name__icontains=search_key)
                    else:
                        return self.queryset.all()

                elif module == "E-Task":
                    # print('checdkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk')
                    # time.sleep(10)
                    '''
                        Reason : 
                        1) on_behalf_of :According to changing function doc to show list of user highier level
                        2) assign_to / sub_assign_to : According to changing function doc to show list of user lower level or hod
                        Author : Rupam Hazra
                        Date : 21/02/2020
                        Line Number : 1419
                    '''
                    mode_for = self.request.query_params.get('mode_for', None)
                    if mode_for == 'on_behalf_of':
                        hi_user_list_details = TCoreUserDetail.objects.filter(
                            cu_user=login_user_details, reporting_head__isnull=False, **filter).values_list(
                            'reporting_head', flat=True)
                        # print('hi_user_list_details',hi_user_list_details)
                        if hi_user_list_details.count() > 0:
                            hi_user_details = hi_user_list_details[0]
                            # print('hi_user_details_up',hi_user_details,type(hi_user_details))
                            hi_user_details_l = self.getHighierLevelUserList(str(hi_user_details))
                            # print('hi_user_details_l',hi_user_details_l,type(hi_user_details_l))
                            time.sleep(10)
                            hi_user_details_l = [int(x) for x in hi_user_details_l.split(",")]
                            if search_key:
                                return self.queryset.annotate(
                                    full_name=Concat('first_name', V(' '), 'last_name')).filter(
                                    full_name__icontains=search_key, pk__in=hi_user_details_l)
                            else:
                                return self.queryset.filter(pk__in=hi_user_details_l)

                    elif mode_for == 'assign_to' or mode_for == 'sub_assign_to':

                        '''
                            Reason :  
                            1) assign_to / sub_assign_to : Comment the HOD checking as per discussion
                            Author : Rupam Hazra
                            Date : 04/03/2020
                            Line Number : 1446
                        '''

                        hi_user_list_details = TCoreUserDetail.objects.filter(
                            reporting_head=login_user_details, cu_user__isnull=False, **filter).values_list('cu_user',
                                                                                                            flat=True)
                        # print('hi_user_list_details',list(hi_user_list_details))
                        hi_user_details1 = ''
                        if hi_user_list_details.count() > 0:
                            for hi_user_details in hi_user_list_details:
                                hi_user_list_details = self.getLowerLevelUserList(str(hi_user_details),
                                                                                  list(hi_user_list_details))
                            # print('hi_user_details1',hi_user_list_details)
                            if search_key:
                                return self.queryset.annotate(
                                    full_name=Concat('first_name', V(' '), 'last_name')).filter(
                                    full_name__icontains=search_key, pk__in=hi_user_list_details)
                            else:
                                return self.queryset.filter(pk__in=hi_user_list_details)

                        # is_hod = TCoreUserDetail.objects.filter(
                        #     hod = login_user_details,cu_is_deleted=False,cu_user__isnull=False).values('hod').distinct()

                        # if is_hod:
                        #     department_d = TCoreUserDetail.objects.filter(
                        #         cu_user = login_user_details,cu_is_deleted=False,cu_user__isnull=False).values_list('department',flat=True)
                        #     #print('department_d',department_d)
                        #     if department_d:
                        #         hi_user_list_details = TCoreUserDetail.objects.filter(~Q(cu_user=login_user_details),department__in=department_d).values_list('cu_user',flat=True)
                        #         #print('hi_user_list_details',hi_user_list_details)
                        #         if search_key:
                        #             return self.queryset.filter((Q(first_name__icontains=search_key) | Q(last_name__icontains=search_key)),pk__in=hi_user_list_details)
                        #         else:
                        #             return self.queryset.filter(pk__in=hi_user_list_details)
                        # else:

                        #     hi_user_list_details = TCoreUserDetail.objects.filter(
                        #         reporting_head = login_user_details,cu_is_deleted=False,cu_user__isnull=False).values_list('cu_user',flat=True)
                        #     #print('hi_user_list_details',list(hi_user_list_details))
                        #     hi_user_details1 = ''
                        #     if hi_user_list_details.count() > 0 :
                        #         for hi_user_details in hi_user_list_details:
                        #             hi_user_list_details = self.getLowerLevelUserList(str(hi_user_details),list(hi_user_list_details))
                        #         #print('hi_user_details1',hi_user_list_details)
                        #         if search_key:
                        #             return self.queryset.filter((Q(first_name__icontains=search_key) | Q(last_name__icontains=search_key)),pk__in=hi_user_list_details)
                        #         else:
                        #             return self.queryset.filter(pk__in=hi_user_list_details)

                    else:
                        if search_key:
                            return self.queryset.annotate(full_name=Concat('first_name', V(' '), 'last_name')).filter(
                                ~Q(id=self.request.user.id), full_name__icontains=search_key)
                        else:
                            # return self.queryset.all()
                            return self.queryset.filter(~Q(id=self.request.user.id))

                elif module == "ATTENDANCE & HRMS":
                    if search_key:
                        # print("in if")
                        if department:
                            return self.queryset.annotate(full_name=Concat('first_name', V(' '), 'last_name')).filter(
                                full_name__icontains=search_key, cu_user__department_id=department)
                        else:
                            return self.queryset.annotate(full_name=Concat('first_name', V(' '), 'last_name')).filter(
                                full_name__icontains=search_key)


                    else:
                        # print("in else")
                        # ~Q(cu_punch_id__in=('#N/A'))
                        if department:
                            return self.queryset.filter(cu_user__department_id=department)
                        else:
                            return self.queryset.all()
                else:
                    if search_key:
                        # print("in under search")
                        queryset = User.objects.annotate(full_name=Concat('first_name', V(' '), 'last_name')).filter(
                            full_name__icontains=search_key
                            # pk__in=(
                            # TMasterModuleRoleUser.objects.filter(mmr_type__in=('3'),mmr_module__cm_name=module).values_list('mmr_user_id',flat=True)
                            # )
                        )
                    else:
                        # print("in under winthout search")
                        queryset = User.objects.filter(
                            # pk__in=(
                            # TMasterModuleRoleUser.objects.filter(mmr_module__cm_name=module,mmr_type__in=('3')).values_list('mmr_user_id',flat=True)
                            # )
                        )
                    print('queryset', queryset.query)
                    return queryset
        else:
            if search_key:
                if department:
                    # cu_user__department_id = department
                    queryset = self.queryset.annotate(full_name=Concat('first_name', V(' '), 'last_name')).filter(
                        full_name__icontains=search_key,cu_user__department_id=department)
                else:
                    queryset = self.queryset.annotate(full_name=Concat('first_name', V(' '), 'last_name')).filter(
                        full_name__icontains=search_key)
            else:
                if department:
                    queryset = self.queryset.filter(cu_user__department_id=department)
                else:
                    queryset = self.queryset.all()

            return queryset

    def getHighierLevelUserList(self, user_id='') -> list:
        try:
            hi_user_list = user_id
            hi_user_list_d = TCoreUserDetail.objects.filter(cu_user_id=str(user_id), cu_is_deleted=False,
                                                            reporting_head__isnull=False).values_list(
                'reporting_head', flat=True)
            if hi_user_list_d.count() > 0:
                hi_user_list1 = str(hi_user_list_d[0])
                hi_user_list = hi_user_list + ',' + str(self.getHighierLevelUserList(hi_user_list1))
            return hi_user_list.replace(',None', '')
        except Exception as e:
            raise e

    def getLowerLevelUserList(self, user_id='', main_list='') -> list:
        try:
            # print('user_id',user_id)
            # print('main_list',main_list)
            hi_user_list_details = TCoreUserDetail.objects.filter(reporting_head_id=str(user_id), cu_is_deleted=False,
                                                                  cu_user__isnull=False).values_list(
                'cu_user_id', flat=True)
            # print('hi_user_list_details1111',hi_user_list_details)
            if hi_user_list_details.count() > 0:
                for hi_user_details in hi_user_list_details:
                    main_list.append(hi_user_details)
                    self.getLowerLevelUserList(str(hi_user_details), main_list)
            return main_list
        except Exception as e:
            raise e

    @response_modify_decorator_list_or_get_before_execution_for_onoff_pagination
    def get(self, request, *args, **kwargs):
        # print('self',self.response)
        return response


class EmployeeListWOPaginationView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = User.objects.filter(is_active=True)
    serializer_class = EmployeeListSerializer

    def get_queryset(self):
        team_approval_flag = self.request.query_params.get('team_approval_flag', None)
        search_sort_flag = True
        if team_approval_flag == '1':
            login_user_details = self.request.user
            # print('login_user_details',login_user_details)
            # print('login_user_details',login_user_details.is_superuser)
            if login_user_details.is_superuser == False:
                users_list_under_the_login_user = TCoreUserDetail.objects.filter(
                    reporting_head=login_user_details,
                    cu_is_deleted=False
                ).annotate(
                    first_name=F('cu_user__first_name'),
                    last_name=F('cu_user__last_name'),
                ).values('id', 'cu_user', 'first_name', 'last_name')
                # print('users_list_under_the_login_user',users_list_under_the_login_user)
                if users_list_under_the_login_user:
                    return users_list_under_the_login_user
                else:
                    return list()
            else:
                return super().get_queryset()
        else:
            return super().get_queryset()

    @response_modify_decorator_get_after_execution
    def get(self, request, *args, **kwargs):
        department = self.request.query_params.get('department', None)
        # print('department',department)
        dept_list = None
        if department:
            dept_list = department.split(",")
            # print('dept_list',dept_list)
        response = super(EmployeeListWOPaginationView, self).get(self, request, args, kwargs)
        # print('response',response.data)
        dept_det = []
        if dept_list:
            for data in response.data:
                dept = TCoreUserDetail.objects.filter(cu_user_id=data['id'],
                                                      department__in=dept_list,
                                                      cu_is_deleted=False)
                print('dept', dept)
                for data in dept:
                    dept_dict = {
                        "id": data.id,
                        "cu_user": data.cu_user.id,
                        "first_name": data.cu_user.first_name,
                        "last_name": data.cu_user.last_name
                    }
                    dept_det.append(dept_dict)
                # print('dept_det',dept_det)
            return Response(dept_det)
        else:
            return response


class EmployeeListForHrView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = User.objects.filter(is_active=True).order_by('-id')
    serializer_class = EmployeeListWithoutDetailsSerializer
    pagination_class = CSPageNumberPagination

    def intersection(dept_list, date_list):
        return list(set(dept_list) & set(date_list))

    def get_queryset(self):
        login_user = self.request.user.id
        # self.queryset = self.queryset.filter(~Q(pk=login_user),
        # pk__in=(TMasterModuleRoleUser.objects.filter(mmr_type='3')))
        # self.queryset = self.queryset.filter(~Q(pk=login_user))
        filter = {}
        joining_date_filter = {}
        date_filter = {}
        total_filter = {}
        # name = self.request.query_params.get('name', None)
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        department = self.request.query_params.get('department', None)
        from_date = self.request.query_params.get('from_date', None)
        to_date = self.request.query_params.get('to_date', None)

        if department and from_date and to_date:
            # print('department',department)
            department = department.split(',')
            department_ids = TCoreUserDetail.objects.filter(department__in=department, cu_is_deleted=False)
            dept_list = []
            for d_i in department_ids:
                user_id = d_i.cu_user.id
                dept_list.append(user_id)
            # print('dept_list',dept_list)
            from_object = datetime.datetime.strptime(from_date, '%Y-%m-%d')
            to_object = datetime.datetime.strptime(to_date, '%Y-%m-%d')
            joining_date_filter['joining_date__date__gte'] = from_object
            joining_date_filter['joining_date__date__lte'] = to_object
            # joining_date_filter['joining_date__date__lte']= to_object + timedelta(days=1)
            date_ids = TCoreUserDetail.objects.filter(cu_is_deleted=False, **joining_date_filter)
            date_list = []
            for d_i in date_ids:
                emp_id = d_i.cu_user.id
                date_list.append(emp_id)
            # print('date_list',date_list)

            total_list = list(set(dept_list) & set(date_list))
            # print('total_list',total_list)
            total_filter['id__in'] = total_list


        # if department or (from_date and to_date):
        elif department:
            department = department.split(',')
            department_ids = TCoreUserDetail.objects.filter(department__in=department, cu_is_deleted=False).values_list(
                'cu_user', flat=True)
            # return self.queryset.filter(id__in=department_ids)
            # print('department_ids',department_ids)
            filter['id__in'] = department_ids

        elif from_date and to_date:
            from_object = datetime.datetime.strptime(from_date, '%Y-%m-%d')
            to_object = datetime.datetime.strptime(to_date, '%Y-%m-%d')
            joining_date_filter['joining_date__date__gte'] = from_object
            joining_date_filter['joining_date__date__lte'] = to_object
            # joining_date_filter['joining_date__date__lte']= to_object + timedelta(days=1)
            date_ids = TCoreUserDetail.objects.filter(cu_is_deleted=False, **joining_date_filter).values_list('cu_user',
                                                                                                              flat=True)
            date_filter['id__in'] = date_ids

        if field_name and order_by:
            if field_name == 'cu_emp_code' and order_by == 'asc':
                user_total_experience_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('cu_emp_code')
                total_experience_details_list = []
                for u_g in user_total_experience_details:
                    total_experience_details_id = u_g.cu_user.id
                    total_experience_details_list.append(total_experience_details_id)
                # print('current_ctc_details_list', total_experience_details_list)
                clauses = ' '.join(
                    ['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(total_experience_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=total_experience_details_list, **filter, **date_filter,
                                                **total_filter).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset', queryset)
                return queryset
            if field_name == 'cu_emp_code' and order_by == 'desc':
                # print('user_department',order_by)
                user_total_experience_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('-cu_emp_code')
                # print('user_current_ctc_details_asc', user_total_experience_details)
                total_experience_details_list = []
                for u_g in user_total_experience_details:
                    total_experience_details_id = u_g.cu_user.id
                    total_experience_details_list.append(total_experience_details_id)
                # print('current_ctc_details_list', total_experience_details_list)
                clauses = ' '.join(
                    ['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(total_experience_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=total_experience_details_list, **filter, **date_filter,
                                                **total_filter).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset', queryset)
                return queryset

            if field_name == 'cu_punch_id' and order_by == 'asc':
                user_total_experience_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('cu_punch_id')
                total_experience_details_list = []
                for u_g in user_total_experience_details:
                    total_experience_details_id = u_g.cu_user.id
                    total_experience_details_list.append(total_experience_details_id)
                # print('current_ctc_details_list', total_experience_details_list)
                clauses = ' '.join(
                    ['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(total_experience_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=total_experience_details_list, **filter, **date_filter,
                                                **total_filter).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset', queryset)
                return queryset
            if field_name == 'cu_punch_id' and order_by == 'desc':
                # print('user_department',order_by)
                user_total_experience_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('-cu_punch_id')
                # print('user_current_ctc_details_asc', user_total_experience_details)
                total_experience_details_list = []
                for u_g in user_total_experience_details:
                    total_experience_details_id = u_g.cu_user.id
                    total_experience_details_list.append(total_experience_details_id)
                # print('current_ctc_details_list', total_experience_details_list)
                clauses = ' '.join(
                    ['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(total_experience_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=total_experience_details_list, **filter, **date_filter,
                                                **total_filter).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset', queryset)
                return queryset
            if field_name == 'sap_personnel_no' and order_by == 'asc':
                user_total_experience_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('sap_personnel_no')
                total_experience_details_list = []
                for u_g in user_total_experience_details:
                    total_experience_details_id = u_g.cu_user.id
                    total_experience_details_list.append(total_experience_details_id)
                # print('current_ctc_details_list', total_experience_details_list)
                clauses = ' '.join(
                    ['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(total_experience_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=total_experience_details_list, **filter, **date_filter,
                                                **total_filter).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset', queryset)
                return queryset
            if field_name == 'sap_personnel_no' and order_by == 'desc':
                # print('user_department',order_by)
                user_total_experience_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('-sap_personnel_no')
                # print('user_current_ctc_details_asc', user_total_experience_details)
                total_experience_details_list = []
                for u_g in user_total_experience_details:
                    total_experience_details_id = u_g.cu_user.id
                    total_experience_details_list.append(total_experience_details_id)
                # print('current_ctc_details_list', total_experience_details_list)
                clauses = ' '.join(
                    ['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(total_experience_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=total_experience_details_list, **filter, **date_filter,
                                                **total_filter).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset', queryset)
                return queryset
            if field_name == 'joining_date' and order_by == 'asc':
                user_total_experience_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('joining_date')
                total_experience_details_list = []
                for u_g in user_total_experience_details:
                    total_experience_details_id = u_g.cu_user.id
                    total_experience_details_list.append(total_experience_details_id)
                # print('current_ctc_details_list', total_experience_details_list)
                clauses = ' '.join(
                    ['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(total_experience_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=total_experience_details_list, **filter, **date_filter,
                                                **total_filter).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset', queryset)
                return queryset
            if field_name == 'joining_date' and order_by == 'desc':
                # print('user_department',order_by)
                user_total_experience_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('-joining_date')
                # print('user_current_ctc_details_asc', user_total_experience_details)
                total_experience_details_list = []
                for u_g in user_total_experience_details:
                    total_experience_details_id = u_g.cu_user.id
                    total_experience_details_list.append(total_experience_details_id)
                # print('current_ctc_details_list', total_experience_details_list)
                clauses = ' '.join(
                    ['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(total_experience_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=total_experience_details_list, **filter, **date_filter,
                                                **total_filter).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset', queryset)
                return queryset
            if field_name == 'designation' and order_by == 'asc':
                # print('user_grade',order_by)
                user_designation = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('designation__cod_name')
                # print('user_designation_desc',user_designation)
                designation_list = []
                for u_g in user_designation:
                    designation_id = u_g.cu_user.id
                    designation_list.append(designation_id)
                # print('designation_list',designation_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(designation_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=designation_list, **filter, **date_filter, **total_filter).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset',queryset)
                return queryset
            if field_name == 'designation' and order_by == 'desc':
                # print('user_grade',order_by)
                user_designation = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('-designation__cod_name')
                # print('user_designation_desc',user_designation)
                designation_list = []
                for u_g in user_designation:
                    designation_id = u_g.cu_user.id
                    designation_list.append(designation_id)
                # print('designation_list',designation_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(designation_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=designation_list, **filter, **date_filter, **total_filter).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset',queryset)
                return queryset
            if field_name == 'reporting_head' and order_by == 'asc':
                # print('user_grade',order_by)
                user_designation = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('reporting_head_id__first_name')
                # print('user_designation_desc',user_designation)
                designation_list = []
                for u_g in user_designation:
                    designation_id = u_g.cu_user.id
                    designation_list.append(designation_id)
                # print('designation_list',designation_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(designation_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=designation_list, **filter, **date_filter, **total_filter).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset',queryset)
                return queryset
            if field_name == 'reporting_head' and order_by == 'desc':
                # print('user_grade',order_by)
                user_designation = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('-reporting_head_id__first_name')
                # print('user_designation_desc',user_designation)
                designation_list = []
                for u_g in user_designation:
                    designation_id = u_g.cu_user.id
                    designation_list.append(designation_id)
                # print('designation_list',designation_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(designation_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=designation_list, **filter, **date_filter, **total_filter).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset',queryset)
                return queryset
            if field_name == 'hod' and order_by == 'asc':
                # print('user_grade',order_by)
                user_designation = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('hod_id__first_name')
                # print('user_designation_desc',user_designation)
                designation_list = []
                for u_g in user_designation:
                    designation_id = u_g.cu_user.id
                    designation_list.append(designation_id)
                # print('designation_list',designation_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(designation_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=designation_list, **filter, **date_filter, **total_filter).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset',queryset)
                return queryset
            if field_name == 'hod' and order_by == 'desc':
                # print('user_grade',order_by)
                user_designation = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('-hod_id__first_name')
                # print('user_designation_desc',user_designation)
                designation_list = []
                for u_g in user_designation:
                    designation_id = u_g.cu_user.id
                    designation_list.append(designation_id)
                # print('designation_list',designation_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(designation_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=designation_list, **filter, **date_filter, **total_filter).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset',queryset)
                return queryset

        elif filter:
            return self.queryset.filter(**filter)
        elif date_filter:
            return self.queryset.filter(**date_filter)
        elif total_filter:
            return self.queryset.filter(**total_filter)
        else:
            user_total_experience_details = TCoreUserDetail.objects.filter(
                cu_is_deleted=False).order_by('-joining_date')
            total_experience_details_list = []
            for u_g in user_total_experience_details:
                total_experience_details_id = u_g.cu_user.id
                total_experience_details_list.append(total_experience_details_id)
            # print('current_ctc_details_list', total_experience_details_list)
            clauses = ' '.join(
                ['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(total_experience_details_list)])
            ordering = 'CASE %s END' % clauses
            queryset = self.queryset.filter(pk__in=total_experience_details_list).extra(
                select={'ordering': ordering}, order_by=('ordering',))
            # print('queryset', queryset)
            return queryset

    @response_modify_decorator_list_or_get_after_execution_for_pagination
    def get(self, request, *args, **kwargs):
        response = super(EmployeeListForHrView, self).get(self, request, args, kwargs)
        for data in response.data['results']:
            hr_details = TCoreUserDetail.objects.filter(cu_user=data['id'], cu_is_deleted=False).values(
                'cu_emp_code', 'sap_personnel_no', 'cu_punch_id', 'joining_date', 'cu_phone_no',
                'department__id', 'department__cd_name', 'reporting_head__id', 'designation__id',
                'designation__cod_name',
                'hod__id'
            )
            if hr_details:
                data['name'] = userdetails(data['id'])
                data['emp_code'] = hr_details[0]['cu_emp_code']
                data['cu_punch_id'] = hr_details[0]['cu_punch_id']
                data['sap_personnel_no'] = hr_details[0]['sap_personnel_no']
                data['joining_date'] = hr_details[0]['joining_date']
                data['cu_phone_no'] = hr_details[0]['cu_phone_no']
                data['department_id'] = hr_details[0]['department__id']
                data['department_name'] = hr_details[0]['department__cd_name']
                data['designation__id'] = hr_details[0]['designation__id']
                data['designation__cod_name'] = hr_details[0]['designation__cod_name']
                data['reporting_head__id'] = hr_details[0]['reporting_head__id']
                data['reporting_head__name'] = userdetails(data['reporting_head__id'])
                data['hod__id'] = hr_details[0]['hod__id']
                data['hod__name'] = userdetails(data['hod__id'])

        return response


class EmployeeListForHrExportDownloadView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = User.objects.filter(is_active=True, is_superuser=False).order_by('-id')
    serializer_class = EmployeeListWithoutDetailsSerializer

    def intersection(dept_list, date_list):
        return list(set(dept_list) & set(date_list))

    def get_queryset(self):
        login_user = self.request.user.id
        # self.queryset = self.queryset.filter(~Q(pk=login_user),
        # pk__in=(TMasterModuleRoleUser.objects.filter(mmr_type='3')))
        # self.queryset = self.queryset.filter(~Q(pk=login_user))
        filter = {}
        joining_date_filter = {}
        date_filter = {}
        total_filter = {}
        # name = self.request.query_params.get('name', None)
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        department = self.request.query_params.get('department', None)
        from_date = self.request.query_params.get('from_date', None)
        to_date = self.request.query_params.get('to_date', None)

        if department and from_date and to_date:
            # print('department',department)
            department = department.split(',')
            department_ids = TCoreUserDetail.objects.filter(department__in=department, cu_is_deleted=False)
            dept_list = []
            for d_i in department_ids:
                user_id = d_i.cu_user.id
                dept_list.append(user_id)
            # print('dept_list',dept_list)
            from_object = datetime.datetime.strptime(from_date, '%Y-%m-%d')
            to_object = datetime.datetime.strptime(to_date, '%Y-%m-%d')
            joining_date_filter['joining_date__date__gte'] = from_object
            joining_date_filter['joining_date__date__lte'] = to_object
            # joining_date_filter['joining_date__date__lte']= to_object + timedelta(days=1)
            date_ids = TCoreUserDetail.objects.filter(cu_is_deleted=False, **joining_date_filter)
            date_list = []
            for d_i in date_ids:
                emp_id = d_i.cu_user.id
                date_list.append(emp_id)
            # print('date_list',date_list)

            total_list = list(set(dept_list) & set(date_list))
            # print('total_list',total_list)
            total_filter['id__in'] = total_list


        # if department or (from_date and to_date):
        elif department:
            department = department.split(',')
            department_ids = TCoreUserDetail.objects.filter(department__in=department, cu_is_deleted=False).values_list(
                'cu_user', flat=True)
            # return self.queryset.filter(id__in=department_ids)
            # print('department_ids',department_ids)
            filter['id__in'] = department_ids

        elif from_date and to_date:
            from_object = datetime.datetime.strptime(from_date, '%Y-%m-%d')
            to_object = datetime.datetime.strptime(to_date, '%Y-%m-%d')
            joining_date_filter['joining_date__date__gte'] = from_object
            joining_date_filter['joining_date__date__lte'] = to_object
            # joining_date_filter['joining_date__date__lte']= to_object + timedelta(days=1)
            date_ids = TCoreUserDetail.objects.filter(cu_is_deleted=False, **joining_date_filter).values_list('cu_user',
                                                                                                              flat=True)
            date_filter['id__in'] = date_ids

        if field_name and order_by:
            if field_name == 'cu_emp_code' and order_by == 'asc':
                user_total_experience_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('cu_emp_code')
                total_experience_details_list = []
                for u_g in user_total_experience_details:
                    total_experience_details_id = u_g.cu_user.id
                    total_experience_details_list.append(total_experience_details_id)
                # print('current_ctc_details_list', total_experience_details_list)
                clauses = ' '.join(
                    ['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(total_experience_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=total_experience_details_list, **filter, **date_filter,
                                                **total_filter).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset', queryset)
                return queryset
            if field_name == 'cu_emp_code' and order_by == 'desc':
                # print('user_department',order_by)
                user_total_experience_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('-cu_emp_code')
                # print('user_current_ctc_details_asc', user_total_experience_details)
                total_experience_details_list = []
                for u_g in user_total_experience_details:
                    total_experience_details_id = u_g.cu_user.id
                    total_experience_details_list.append(total_experience_details_id)
                # print('current_ctc_details_list', total_experience_details_list)
                clauses = ' '.join(
                    ['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(total_experience_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=total_experience_details_list, **filter, **date_filter,
                                                **total_filter).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset', queryset)
                return queryset

            if field_name == 'cu_punch_id' and order_by == 'asc':
                user_total_experience_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('cu_punch_id')
                total_experience_details_list = []
                for u_g in user_total_experience_details:
                    total_experience_details_id = u_g.cu_user.id
                    total_experience_details_list.append(total_experience_details_id)
                # print('current_ctc_details_list', total_experience_details_list)
                clauses = ' '.join(
                    ['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(total_experience_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=total_experience_details_list, **filter, **date_filter,
                                                **total_filter).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset', queryset)
                return queryset
            if field_name == 'cu_punch_id' and order_by == 'desc':
                # print('user_department',order_by)
                user_total_experience_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('-cu_punch_id')
                # print('user_current_ctc_details_asc', user_total_experience_details)
                total_experience_details_list = []
                for u_g in user_total_experience_details:
                    total_experience_details_id = u_g.cu_user.id
                    total_experience_details_list.append(total_experience_details_id)
                # print('current_ctc_details_list', total_experience_details_list)
                clauses = ' '.join(
                    ['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(total_experience_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=total_experience_details_list, **filter, **date_filter,
                                                **total_filter).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset', queryset)
                return queryset
            if field_name == 'sap_personnel_no' and order_by == 'asc':
                user_total_experience_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('sap_personnel_no')
                total_experience_details_list = []
                for u_g in user_total_experience_details:
                    total_experience_details_id = u_g.cu_user.id
                    total_experience_details_list.append(total_experience_details_id)
                # print('current_ctc_details_list', total_experience_details_list)
                clauses = ' '.join(
                    ['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(total_experience_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=total_experience_details_list, **filter, **date_filter,
                                                **total_filter).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset', queryset)
                return queryset
            if field_name == 'sap_personnel_no' and order_by == 'desc':
                # print('user_department',order_by)
                user_total_experience_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('-sap_personnel_no')
                # print('user_current_ctc_details_asc', user_total_experience_details)
                total_experience_details_list = []
                for u_g in user_total_experience_details:
                    total_experience_details_id = u_g.cu_user.id
                    total_experience_details_list.append(total_experience_details_id)
                # print('current_ctc_details_list', total_experience_details_list)
                clauses = ' '.join(
                    ['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(total_experience_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=total_experience_details_list, **filter, **date_filter,
                                                **total_filter).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset', queryset)
                return queryset
            if field_name == 'joining_date' and order_by == 'asc':
                user_total_experience_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('joining_date')
                total_experience_details_list = []
                for u_g in user_total_experience_details:
                    total_experience_details_id = u_g.cu_user.id
                    total_experience_details_list.append(total_experience_details_id)
                # print('current_ctc_details_list', total_experience_details_list)
                clauses = ' '.join(
                    ['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(total_experience_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=total_experience_details_list, **filter, **date_filter,
                                                **total_filter).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset', queryset)
                return queryset
            if field_name == 'joining_date' and order_by == 'desc':
                # print('user_department',order_by)
                user_total_experience_details = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('-joining_date')
                # print('user_current_ctc_details_asc', user_total_experience_details)
                total_experience_details_list = []
                for u_g in user_total_experience_details:
                    total_experience_details_id = u_g.cu_user.id
                    total_experience_details_list.append(total_experience_details_id)
                # print('current_ctc_details_list', total_experience_details_list)
                clauses = ' '.join(
                    ['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(total_experience_details_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=total_experience_details_list, **filter, **date_filter,
                                                **total_filter).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset', queryset)
                return queryset
            if field_name == 'designation' and order_by == 'asc':
                # print('user_grade',order_by)
                user_designation = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('designation__cod_name')
                # print('user_designation_desc',user_designation)
                designation_list = []
                for u_g in user_designation:
                    designation_id = u_g.cu_user.id
                    designation_list.append(designation_id)
                # print('designation_list',designation_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(designation_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=designation_list, **filter, **date_filter, **total_filter).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset',queryset)
                return queryset
            if field_name == 'designation' and order_by == 'desc':
                # print('user_grade',order_by)
                user_designation = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('-designation__cod_name')
                # print('user_designation_desc',user_designation)
                designation_list = []
                for u_g in user_designation:
                    designation_id = u_g.cu_user.id
                    designation_list.append(designation_id)
                # print('designation_list',designation_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(designation_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=designation_list, **filter, **date_filter, **total_filter).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset',queryset)
                return queryset
            if field_name == 'reporting_head' and order_by == 'asc':
                # print('user_grade',order_by)
                user_designation = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('reporting_head_id__first_name')
                # print('user_designation_desc',user_designation)
                designation_list = []
                for u_g in user_designation:
                    designation_id = u_g.cu_user.id
                    designation_list.append(designation_id)
                # print('designation_list',designation_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(designation_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=designation_list, **filter, **date_filter, **total_filter).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset',queryset)
                return queryset
            if field_name == 'reporting_head' and order_by == 'desc':
                # print('user_grade',order_by)
                user_designation = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('-reporting_head_id__first_name')
                # print('user_designation_desc',user_designation)
                designation_list = []
                for u_g in user_designation:
                    designation_id = u_g.cu_user.id
                    designation_list.append(designation_id)
                # print('designation_list',designation_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(designation_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=designation_list, **filter, **date_filter, **total_filter).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset',queryset)
                return queryset
            if field_name == 'hod' and order_by == 'asc':
                # print('user_grade',order_by)
                user_designation = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('hod_id__first_name')
                # print('user_designation_desc',user_designation)
                designation_list = []
                for u_g in user_designation:
                    designation_id = u_g.cu_user.id
                    designation_list.append(designation_id)
                # print('designation_list',designation_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(designation_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=designation_list, **filter, **date_filter, **total_filter).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset',queryset)
                return queryset
            if field_name == 'hod' and order_by == 'desc':
                # print('user_grade',order_by)
                user_designation = TCoreUserDetail.objects.filter(
                    cu_is_deleted=False).order_by('-hod_id__first_name')
                # print('user_designation_desc',user_designation)
                designation_list = []
                for u_g in user_designation:
                    designation_id = u_g.cu_user.id
                    designation_list.append(designation_id)
                # print('designation_list',designation_list)
                clauses = ' '.join(['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(designation_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=designation_list, **filter, **date_filter, **total_filter).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset',queryset)
                return queryset

        elif filter:
            return self.queryset.filter(**filter)
        elif date_filter:
            return self.queryset.filter(**date_filter)
        elif total_filter:
            return self.queryset.filter(**total_filter)
        else:
            user_total_experience_details = TCoreUserDetail.objects.filter(
                cu_is_deleted=False).order_by('-joining_date')
            total_experience_details_list = []
            print('user_total_experience_details', user_total_experience_details)
            for u_g in user_total_experience_details:
                total_experience_details_id = u_g.cu_user.id if u_g.cu_user else None
                total_experience_details_list.append(total_experience_details_id)
            # print('current_ctc_details_list', total_experience_details_list)
            clauses = ' '.join(
                ['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(total_experience_details_list)])
            ordering = 'CASE %s END' % clauses
            queryset = self.queryset.filter(pk__in=total_experience_details_list).extra(
                select={'ordering': ordering}, order_by=('ordering',))
            # print('queryset', queryset)
            return queryset

    def get(self, request, *args, **kwargs):
        response = super(__class__, self).get(self, request, args, kwargs)
        data_list = list()
        for data in response.data:
            hr_details = TCoreUserDetail.objects.filter(cu_user=data['id'], cu_is_deleted=False).values(
                'cu_emp_code', 'sap_personnel_no', 'cu_punch_id', 'joining_date', 'cu_phone_no', 'cu_alt_phone_no',
                'department__id', 'department__cd_name', 'reporting_head__id', 'designation__id',
                'designation__cod_name',
                'hod__id'
            )
            if hr_details:
                data['name'] = userdetails(data['id'])
                data['emp_code'] = hr_details[0]['cu_emp_code']
                data['cu_punch_id'] = hr_details[0]['cu_punch_id']
                data['sap_personnel_no'] = hr_details[0]['sap_personnel_no']
                data['joining_date'] = hr_details[0]['joining_date']
                data['cu_alt_phone_no'] = hr_details[0]['cu_alt_phone_no']
                data['department_id'] = hr_details[0]['department__id']
                data['department_name'] = hr_details[0]['department__cd_name']
                data['designation__id'] = hr_details[0]['designation__id']
                data['designation__cod_name'] = hr_details[0]['designation__cod_name']
                data['reporting_head__id'] = hr_details[0]['reporting_head__id']
                data['reporting_head__name'] = userdetails(data['reporting_head__id'])
                data['hod__id'] = hr_details[0]['hod__id']
                data['hod__name'] = userdetails(data['hod__id'])

                data_list.append([data['name'], data['emp_code'], data['sap_personnel_no'], data['cu_punch_id'],
                                  data['joining_date'],
                                  data['department_name'], data['designation__cod_name'], data['hod__name'],
                                  data['reporting_head__name'],
                                  data['cu_alt_phone_no']])

        file_name = ''
        if data_list:
            if os.path.isdir('media/hrms/employee_list/document'):
                file_name = 'media/hrms/employee_list/document/employee_list_for_hr.xlsx'
                file_path = settings.MEDIA_ROOT_EXPORT + file_name
            else:
                os.makedirs('media/hrms/employee_list/document')
                file_name = 'media/hrms/employee_list/document/employee_list_for_hr.xlsx'
                file_path = settings.MEDIA_ROOT_EXPORT + file_name

            final_df = pd.DataFrame(data_list,
                                    columns=['Name', 'Emp. Code', 'SAP Id', 'Punch Id', 'Joining Date', 'Department',
                                             'Designation', 'HOD', 'Reporting Head', 'Official Contact No'])

            export_csv = final_df.to_excel(file_path, index=None, header=True)
            if request.is_secure():
                protocol = 'https://'
            else:
                protocol = 'http://'

        url = getHostWithPort(request) + file_name if file_name else None
        # response.data['url'] = url
        if url:
            return Response({'request_status': 1, 'msg': 'Found', 'url': url})
        else:
            return Response({'request_status': 0, 'msg': 'Not Found', 'url': url})


class DocumentAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = HrmsDocument.objects.filter(is_deleted=False)
    serializer_class = DocumentAddSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('user', 'tab_name', 'field_label')

    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        return response


class DocumentDeleteView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = HrmsDocument.objects.all()
    serializer_class = DocumentDeleteSerializer


class HrmsEmployeeProfileDocumentAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = HrmsDynamicSectionFieldLabelDetailsWithDoc.objects.filter(is_deleted=False)
    serializer_class = HrmsEmployeeProfileDocumentAddSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('user', 'tab_name', 'field_label')

    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        return response


class HrmsEmployeeProfileDocumentDeleteView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = HrmsDynamicSectionFieldLabelDetailsWithDoc.objects.all()
    serializer_class = HrmsEmployeeProfileDocumentDeleteSerializer


class HrmsEmployeeAcademicQualificationAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = HrmsUserQualification.objects.filter(is_deleted=False)
    serializer_class = HrmsEmployeeAcademicQualificationAddSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('user', 'qualification')

    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        return response


class HrmsEmployeeAcademicQualificationDeleteView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = HrmsUserQualification.objects.all()
    serializer_class = HrmsEmployeeAcademicQualificationDeleteSerializer


class HrmsEmployeeAcademicQualificationDocumentAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = HrmsUserQualificationDocument.objects.filter(is_deleted=False)
    serializer_class = HrmsEmployeeAcademicQualificationDocumentAddSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('user_qualification',)

    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        return response


class HrmsEmployeeAcademicQualificationDocumentDeleteView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = HrmsUserQualificationDocument.objects.all()
    serializer_class = HrmsEmployeeAcademicQualificationDocumentDeleteSerializer


class EmployeeAddByCSVorExcelView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    @response_modify_decorator_post
    def post(self, request, format=None):

        '''
            Modify as per details 05.02.2020
        '''
        try:
            import random
            document = request.data['document']
            # print('document',type(document))
            # print('document_name',document)
            logdin_user_id = self.request.user.id
            # print('logdin_user_id',logdin_user_id)
            user_list = []
            user_duplicate_list = []
            total_result = {}
            data = pd.read_excel(document, converters={
                'official_email_id': str,
                'punch_id': str, 'emp_code': str,
                'username': str, 'joining_date': str,
                'module_name': str, 'sap_personnel_no': str, 'job_location_state': str, 'phone_no': str})  # read excel
            data.dropna(axis=0, how='all', inplace=True)  # Remove blank rows with all nun column
            data = data.loc[:, ~data.columns.str.contains('^Unnamed')]  # Remove blank unnamed column
            data = data.replace(np.nan, '', regex=True)  # for replace blank value with nan

            # print('data',data)

            # data1=pd.DataFrame(data)
            # print('data1',data)
            filter_t_core_user = {}
            filter_grade = {}
            user_blank_list = []
            leave_filter = {}
            with transaction.atomic():
                for index, row in data.iterrows():
                    # pass
                    # return Response({})
                    if row['first_name'] != '' and row['last_name'] != '':
                        # print('row',row)
                        if row['punch_id'] == '' or row['joining_date'] == '' or row['module_name'] == '':
                            user_blank_dict = {
                                # 'cu_emp_code':row['emp_code'],
                                'cu_punch_id': row['punch_id'],
                                'module_name': row['module_name'],
                                'joining_date': row['joining_date'],
                                'first_name': row['first_name'],
                                'last_name': row['last_name']
                            }
                            user_blank_list.append(user_blank_dict)

                        else:
                            # print('sddsdsds')
                            # print('row',row['module_name'])
                            company_det = TCoreCompany.objects.filter(coc_name=(row['company_name']).lower(),
                                                                      coc_is_deleted=False)
                            if company_det:
                                for c_d in company_det:
                                    filter_t_core_user['company_id'] = c_d.id
                            else:
                                filter_t_core_user['company_id'] = None

                            department_det = TCoreDepartment.objects.filter(cd_name=(row['department_name']).lower(),
                                                                            cd_is_deleted=False)
                            if department_det:
                                for d_t in department_det:
                                    filter_t_core_user['department_id'] = d_t.id
                            else:
                                filter_t_core_user['department_id'] = None

                            designation_det = TCoreDesignation.objects.filter(
                                cod_name=(row['designation_name']).lower(), cod_is_deleted=False)
                            if designation_det:
                                for desig in designation_det:
                                    filter_t_core_user['designation_id'] = desig.id
                                    filter_grade['mmr_designation_id'] = desig.id
                            else:
                                filter_t_core_user['designation_id'] = None
                                filter_grade['mmr_designation_id'] = None

                            grade_det = TCoreGrade.objects.filter(cg_name=(row['grade_name']).lower(),
                                                                  cg_is_deleted=False)
                            if grade_det:
                                for g_t in grade_det:
                                    filter_t_core_user['employee_grade_id'] = g_t.id
                            else:
                                filter_t_core_user['employee_grade_id'] = None

                            salary_type = row['salary_type'] if row['salary_type'] else ''
                            # print('salary_type',type(salary_type))
                            salary_type_det = TCoreSalaryType.objects.filter(st_name=salary_type, st_is_deleted=False)
                            if salary_type_det:
                                for s_t in salary_type_det:
                                    filter_t_core_user['salary_type_id'] = s_t.id
                            else:
                                filter_t_core_user['salary_type_id'] = None

                            if row['job_location_state']:
                                job_location_state_det = TCoreState.objects.filter(
                                    cs_state_name=row['job_location_state'], cs_is_deleted=False)
                                if job_location_state_det:
                                    job_location_state_det = TCoreState.objects.get(
                                        cs_state_name=row['job_location_state'], cs_is_deleted=False)
                                    filter_t_core_user['job_location_state'] = job_location_state_det

                            else:
                                filter_t_core_user['job_location_state'] = None

                            gender = row['gender'] if row['gender'] else None
                            if gender:
                                if row['gender'].lower() == 'male':
                                    filter_t_core_user['cu_gender'] = 'male'
                                elif row['gender'].lower() == 'female':
                                    filter_t_core_user['cu_gender'] = 'female'

                            cu_phone_no = row['phone_no'] if row['phone_no'] else ''

                            # print('date_of_birth',len(row['date_of_birth']),type(row['date_of_birth']))

                            # if len(row['date_of_birth']) == 0:
                            #     cu_dob = None
                            # else:
                            #     cu_dob=datetime.datetime.strptime(row['date_of_birth'],"%Y-%m-%d %H:%M:%S").date()

                            # initial_ctc = row['initial_ctc'] if row['initial_ctc'] else Decimal(0.0)
                            # current_ctc= row['current_ctc'] if  row['current_ctc'] else Decimal(0.0)
                            cost_centre = row['cost_centre'] if row['cost_centre'] else ''
                            # address = row['address'] if row['address'] else ''
                            source = row['source'] if row['source'] else None
                            source_name = row['source_name'] if row['source_name'] else None
                            total_experience = row['total_experience'] if row['total_experience'] else Decimal(0.0)
                            job_location = row['job_location'] if row['job_location'] else ''
                            granted_cl = row['granted_cl'] if row['granted_cl'] else 10
                            granted_el = row['granted_el'] if row['granted_el'] else 15
                            granted_sl = row['granted_sl'] if row['granted_sl'] else 7
                            joining_date = row['joining_date']
                            joined_date = datetime.datetime.strptime(joining_date, "%Y-%m-%d %H:%M:%S").date()
                            joined_year = joined_date.year
                            pf_number = row['pf_number'] if row['pf_number'] else ''
                            esic_number = row['esic_number'] if row['esic_number'] else ''

                            daily_loginTime = row['daily_loginTime'] if row['daily_loginTime'] else "10:00:00"
                            daily_logoutTime = row['daily_logoutTime'] if row['daily_logoutTime'] else "19:00:00"
                            lunch_start = row['lunch_start'] if row['lunch_start'] else "13:30:00"
                            lunch_end = row['lunch_end'] if row['lunch_end'] else "14:00:00"
                            worst_late = row['worst_late'] if row['worst_late'] else "14:00:00"

                            # print('before_check')

                            if TCoreUserDetail.objects.filter((
                                                                      Q(cu_punch_id=row['punch_id'])) & Q(
                                cu_is_deleted=False)).count() == 0:
                                print('under')
                                username_generate = row['first_name'] + row['last_name']
                                print('username_generate', username_generate)
                                check_user_exist = User.objects.filter(username=username_generate)
                                print('check_user_exist', check_user_exist)
                                if check_user_exist:
                                    username_generate = username_generate + str(random.randint(1, 6))

                                print('username_generate', username_generate)
                                user = User.objects.create(first_name=row['first_name'],
                                                           last_name=row['last_name'],
                                                           username=username_generate,
                                                           email=row['official_email_id']
                                                           )
                                '''
                                    Modified by Rupam Hazra to set default password
                                '''
                                password = 'Shyam@123'
                                user.set_password(password)
                                user.save()
                                # print('user',user.id)
                                data_dict = {
                                    'id': user.id,
                                    'first_name': user.first_name,
                                    'last_name': user.last_name,
                                    'username': user.username,
                                    'email': user.email
                                }
                                # print('data_dict',data_dict)
                                company_coc_code = TCoreCompany.objects.get(
                                    id=filter_t_core_user['company_id']).coc_code
                                last_emp_code = TCoreUserDetail.objects.latest("id").cu_emp_code
                                last_coc_code = TCoreUserDetail.objects.latest("id").company.coc_code
                                last_emp_code = last_emp_code if last_emp_code else "0"
                                primary = "0{}".format(company_coc_code)
                                # print(primary)
                                try:
                                    last_emp_code = last_emp_code.spit(last_coc_code)
                                    secondary = int(last_emp_code) + 1
                                except:
                                    secondary = 1
                                # print(secondary)
                                cu_emp_code = "".join([primary, str(secondary)])
                                # print(cu_emp_code)
                                import random
                                file_no = random.randint(0, 2000)

                                user_detail = TCoreUserDetail.objects.create(cu_user=user,
                                                                             cu_phone_no=cu_phone_no,
                                                                             cu_alt_email_id=row['official_email_id'],
                                                                             password_to_know=password,
                                                                             cu_emp_code=cu_emp_code,
                                                                             cu_punch_id=row['punch_id'],
                                                                             file_no=file_no,
                                                                             # cu_dob=cu_dob,
                                                                             sap_personnel_no=row['sap_personnel_no'],
                                                                             # initial_ctc=initial_ctc,
                                                                             # current_ctc=current_ctc,
                                                                             cost_centre=cost_centre,
                                                                             # address=address,
                                                                             source=source,
                                                                             source_name=source_name,
                                                                             total_experience=total_experience,
                                                                             job_location=job_location,
                                                                             pf_no=pf_number,
                                                                             esic_no=esic_number,
                                                                             granted_cl=granted_cl,
                                                                             granted_el=granted_el,
                                                                             granted_sl=granted_sl,
                                                                             joining_date=joining_date,
                                                                             daily_loginTime=daily_loginTime,
                                                                             daily_logoutTime=daily_logoutTime,
                                                                             lunch_start=lunch_start,
                                                                             lunch_end=lunch_end,
                                                                             worst_late=worst_late,
                                                                             **filter_t_core_user,
                                                                             cu_created_by_id=logdin_user_id
                                                                             )
                                # print('user_detail',user_detail)
                                data_dict['cu_emp_code'] = user_detail.cu_emp_code
                                data_dict['cu_punch_id'] = user_detail.cu_punch_id
                                data_dict['sap_personnel_no'] = user_detail.sap_personnel_no
                                data_dict['cu_phone_no'] = user_detail.cu_phone_no if user_detail.cu_phone_no else None
                                data_dict[
                                    'joining_date'] = user_detail.joining_date if user_detail.joining_date else None
                                data_dict[
                                    'daily_loginTime'] = user_detail.daily_loginTime if user_detail.daily_loginTime else None
                                data_dict[
                                    'daily_logoutTime'] = user_detail.daily_logoutTime if user_detail.daily_logoutTime else None
                                data_dict['lunch_start'] = user_detail.lunch_start if user_detail.lunch_start else None
                                data_dict['lunch_end'] = user_detail.lunch_end if user_detail.lunch_end else None
                                data_dict['worst_late'] = user_detail.worst_late if user_detail.worst_late else None
                                # data_dict['initial_ctc']=user_detail.initial_ctc if user_detail.initial_ctc else None
                                # data_dict['current_ctc']=user_detail.current_ctc if user_detail.current_ctc else None
                                # data_dict['cost_centre']=user_detail.cost_centre if user_detail.cost_centre else None
                                # data_dict['address']=user_detail.address if user_detail.address else None
                                # data_dict['source']=user_detail.source if user_detail.source else None
                                # data_dict['total_experience']=user_detail.total_experience if user_detail.total_experience else None
                                # data_dict['job_location']=user_detail.job_location if user_detail.job_location else None
                                # data_dict['job_location_state']=user_detail.job_location_state if user_detail.job_location_state else None
                                # data_dict['granted_cl']=user_detail.granted_cl if user_detail.granted_cl else None
                                # data_dict['granted_el']=user_detail.granted_el if user_detail.granted_el else None
                                # data_dict['granted_sl']=user_detail.granted_sl if user_detail.granted_sl else None
                                # data_dict['company_id']=user_detail.company.id if user_detail.company else None
                                # data_dict['company_name']=user_detail.company.coc_name if user_detail.company else None
                                # data_dict['designation_id']=user_detail.designation.id if user_detail.designation else None
                                # data_dict['designation_name']=user_detail.designation.cod_name if user_detail.designation else None
                                # data_dict['department_id']=user_detail.department.id if user_detail.department else None
                                # data_dict['department_name']=user_detail.department.cd_name if user_detail.department else None
                                # data_dict['grade']=user_detail.employee_grade.id if user_detail.employee_grade else None
                                # data_dict['grade_name']=user_detail.employee_grade.cg_name if user_detail.employee_grade else None
                                # data_dict['cu_gender'] =user_detail.cu_gender if user_detail.cu_gender else None
                                # print('data_dict111',data_dict)

                                '''
                                    For multiple modules
                                '''
                                # print('module_name',row['module_name'])
                                modules = row['module_name'].split(',')
                                # print('modules',modules)
                                for module in modules:
                                    if module == 'HRMS':
                                        module = 'ATTENDANCE & HRMS'

                                    module_det = TCoreModule.objects.filter(cm_name=module, cm_is_deleted=False)
                                    # print('module_det',module_det)
                                    if module_det:
                                        for m_d in module_det:
                                            filter_grade['mmr_module_id'] = m_d.id
                                    else:
                                        filter_grade['mmr_module_id'] = None

                                    role_user = TMasterModuleRoleUser.objects.create(
                                        mmr_user=user,
                                        mmr_type=3,
                                        **filter_grade,
                                        mmr_created_by_id=logdin_user_id
                                    )

                                data_dict['module_id'] = role_user.mmr_module.id
                                data_dict['module_name'] = role_user.mmr_module.cm_name
                                data_dict['mmr_type'] = role_user.mmr_type

                                # print('data_dict',data_dict)

                                user_list.append(data_dict)

                                total_month_grace = AttendenceMonthMaster.objects.filter(
                                    month_start__date__lte=joined_date,
                                    month_end__date__gte=joined_date, is_deleted=False).values('grace_available',
                                                                                               'year_start_date',
                                                                                               'year_end_date',
                                                                                               'month',
                                                                                               'month_start',
                                                                                               'month_end'
                                                                                               )
                                if total_month_grace:
                                    year_start_date = total_month_grace[0]['year_start_date'].date()
                                    year_end_date = total_month_grace[0]['year_end_date'].date()
                                    total_days = (year_end_date - joined_date).days
                                    # print('total_days',total_days)
                                    # calculated_cl=round((total_days/365)* int(granted_cl))
                                    leave_filter['cl'] = round_calculation(total_days, granted_cl)
                                    calculated_el = round((total_days / 365) * int(granted_el))
                                    leave_filter['el'] = round_calculation(total_days, granted_el)
                                    if granted_sl:
                                        # calculated_sl=round((total_days/365)* int(granted_sl))
                                        # print('calculated_sl',calculated_sl)
                                        leave_filter['sl'] = round_calculation(total_days, granted_sl)
                                    else:
                                        leave_filter['sl'] = None

                                    month_start_date = total_month_grace[0]['month_start'].date()
                                    month_end_date = total_month_grace[0]['month_end'].date()
                                    # print('month_start_date',month_start_date,month_end_date)
                                    month_days = (month_end_date - month_start_date).days
                                    # print('month_days',month_days)
                                    remaining_days = (month_end_date - joined_date).days
                                    # print('remaining_days',remaining_days)
                                    available_grace = round(
                                        (remaining_days / month_days) * int(total_month_grace[0]['grace_available']))
                                    # print('available_grace',available_grace)

                                    if year_start_date < joined_date:
                                        JoiningApprovedLeave.objects.get_or_create(employee=user,
                                                                                   year=joined_year,
                                                                                   month=total_month_grace[0]['month'],
                                                                                   **leave_filter,
                                                                                   first_grace=available_grace,
                                                                                   created_by_id=logdin_user_id,
                                                                                   owned_by_id=logdin_user_id
                                                                                   )

                                if row['official_email_id']:
                                    # ============= Mail Send ==============#

                                    # Send mail to employee with login details
                                    mail_data = {
                                        "name": user.first_name + '' + user.last_name,
                                        "user": username_generate,
                                        "pass": password
                                    }
                                    # print('mail_data',mail_data)
                                    mail_class = GlobleMailSend('EMP001', [row['official_email_id']])
                                    mail_thread = Thread(target=mail_class.mailsend, args=(mail_data,))
                                    mail_thread.start()

                                # Send mail to who added the employee
                                t_core_user = TCoreUserDetail.objects.filter(cu_user=self.request.user)
                                if t_core_user:
                                    add_cu_alt_email_id = t_core_user[0]
                                    if add_cu_alt_email_id.cu_alt_email_id:
                                        mail_data = {
                                            "name": self.request.user.first_name + ' ' + self.request.user.last_name,
                                            "user": username_generate,
                                            "pass": password
                                        }
                                        # print('mail_data',mail_data)
                                        mail_class = GlobleMailSend('EMPA001', [add_cu_alt_email_id.cu_alt_email_id])
                                        mail_thread = Thread(target=mail_class.mailsend, args=(mail_data,))
                                        mail_thread.start()
                            else:
                                # print('duplicate')
                                duplicate_data = {
                                    'first_name': row['first_name'],
                                    'last_name': row['last_name'],
                                    # 'cu_emp_code':row['emp_code'],
                                    'cu_punch_id': row['punch_id'],
                                    'sap_personnel_no': row['sap_personnel_no'],
                                    'module_name': row['module_name'],
                                    'joining_date': row['joining_date']
                                }
                                user_duplicate_list.append(duplicate_data)

                        total_result['user_duplicate_list'] = user_duplicate_list
                        total_result['user_added_list'] = user_list
                        total_result['user_not_added_list_due_to_required_fields'] = user_blank_list

            return Response(total_result)

        except Exception as e:
            raise e
            # raise APIException({'msg':settings.MSG_ERROR,
            #                     'error':e,
            #                     "request_status": 0
            #                     })


class EmployeeDetailsUpdateThroughSAPPersonnelNoView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    @response_modify_decorator_post
    def post(self, request, format=None):
        try:
            document = request.data['document']
            # print('document',document)
            logdin_user_id = self.request.user.id
            # print('logdin_user_id',logdin_user_id)
            user_list = []
            duplicate_email_list = []
            total_result = {}
            data = pd.read_excel(document, converters={
                'SAP Personnel No': str})
            data.dropna(axis=0, how='all', inplace=True)
            data = data.loc[:, ~data.columns.str.contains('^Unnamed')]
            data = data.replace(np.nan, '', regex=True)
            # print('data',data)
            user_blank_list = []
            with transaction.atomic():
                for index, row in data.iterrows():
                    if row['SAP Personnel No'] == '':
                        user_blank_dict = {
                            'SAP Personnel No': row['SAP Personnel No'],
                            'Official Phone No': row['Official Phone No'],
                            'Official Email Id': row['Official Email Id'],
                        }
                        user_blank_list.append(user_blank_dict)
                    else:
                        user_dict = {}
                        duplicate_email_dict = {}
                        email_filter = {}
                        cu_phone_no = row['Official Phone No'] if row['Official Phone No'] else ''
                        cu_alt_email_id = row['Official Email Id'] if row['Official Email Id'] else ''
                        sap_personnel_no = row['SAP Personnel No']

                        if TCoreUserDetail.objects.filter(cu_alt_email_id=cu_alt_email_id, cu_is_deleted=False) == 0:
                            email_filter['cu_alt_email_id'] = cu_alt_email_id
                            # print('email_filter',email_filter)
                        else:
                            duplicate_email_dict['SAP Personnel No'] = sap_personnel_no
                            duplicate_email_dict['Official Phone No'] = cu_phone_no
                            duplicate_email_dict['Official Email Id'] = cu_alt_email_id
                            duplicate_email_list.append(duplicate_email_dict)

                        user_detail = TCoreUserDetail.objects.filter(sap_personnel_no=sap_personnel_no,
                                                                     cu_is_deleted=False).update(
                            cu_phone_no=cu_phone_no, **email_filter,
                            cu_updated_by=logdin_user_id)
                        user_after_update_details = TCoreUserDetail.objects.filter(sap_personnel_no=sap_personnel_no,
                                                                                   cu_is_deleted=False).values(
                            'cu_alt_email_id')
                        user_dict['SAP Personnel No'] = sap_personnel_no
                        user_dict['Official Phone No'] = cu_phone_no
                        user_dict['Official Email Id'] = user_after_update_details[0]['cu_alt_email_id'] if \
                        user_after_update_details[0]['cu_alt_email_id'] else ''
                        user_list.append(user_dict)

                    total_result['blank_sap_list'] = user_blank_list
                    total_result['sap_list'] = user_list
                    total_result['duplicate_email_list'] = duplicate_email_list
            return Response(total_result)

        except Exception as e:
            raise e


#:::::::::::::::::::::: HRMS NEW REQUIREMENT:::::::::::::::::::::::::::#
class HrmsNewRequirementAddView(generics.ListCreateAPIView, mixins.UpdateModelMixin):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = HrmsNewRequirement.objects.filter(is_deleted=False)
    serializer_class = HrmsNewRequirementAddSerializer

    # pagination_class = OnOffPagination

    def get_queryset(self):
        req_id = self.request.query_params.get('req_id', None)
        queryset = self.queryset.filter(id=req_id, tab_status__gte=2)

        return queryset

    # @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        # page_size = self.request.query_params.get('page_size', None)
        response = super(HrmsNewRequirementAddView, self).get(self, request, args, kwargs)
        data_dict = {}

        # print("response",response.data)

        def userdetails(user):
            # print(type(user))
            if isinstance(user, (int)):
                name = User.objects.filter(id=user)
                for i in name:
                    # print("i",i)
                    f_name_l_name = i.first_name + " " + i.last_name
                    # print("f_name_l_name",f_name_l_name)
            elif isinstance(user, (str)):
                # print(user ,"str")
                name = User.objects.filter(username=user)
                for i in name:
                    # print("i",i)
                    f_name_l_name = i.first_name + " " + i.last_name
                    print("f_name_l_name", f_name_l_name)
            else:
                f_name_l_name = None

            return f_name_l_name

        def designation(designation):
            if isinstance(designation, (str)):
                desg_data = TCoreUserDetail.objects.filter(cu_user__username=designation)
                if desg_data:
                    for desg in desg_data:
                        return desg.designation.cod_name
                else:
                    return None
            elif isinstance(designation, (int)):
                desg_data = TCoreDesignation.objects.filter(id=designation)
                if desg_data:
                    for desg in desg_data:
                        return desg.cod_name
                else:
                    return None

        def display(data):
            age_group_data = HrmsNewRequirement.objects.filter(id=response.data[0]['id'],
                                                               desired_age_group=data)
            for age_group in age_group_data:
                return age_group.get_desired_age_group_display()

        def department(department):
            if isinstance(department, (str)):
                desg_data = TCoreUserDetail.objects.filter(cu_user__username=department)
                if desg_data:
                    for desg in desg_data:
                        return desg.department.cd_name
                else:
                    return None
            elif isinstance(department, (int)):
                desg_data = TCoreDepartment.objects.filter(id=department)
                if desg_data:
                    for desg in desg_data:
                        return desg.cd_name
                else:
                    return None

        for data in response.data:

            response.data[0]['desired_age_group'] = display(data['desired_age_group'])
            data_dict['reporting_to_name'] = userdetails(data['reporting_to'])
            data_dict['issuing_department_name'] = department(data['issuing_department'])
            data_dict['proposed_designation_name'] = designation(data['proposed_designation'])
            # {
            #     'issuing_department_name':department(data['issuing_department']),
            #     'proposed_designation_name':designation(data['proposed_designation'])
            # }
            data_dict['raised_by_data'] = {
                "mrf_raised_by": userdetails(data['created_by']),
                "date": data['created_at'],
                "designation": designation(data['created_by']),
                "department": department(data['created_by'])
            }
            data_dict['recommended_by_data'] = {
                "recommended_by": userdetails(data['reporting_to']),
                "date": data['created_at'],
                "designation": designation(data['created_by']),
                "department": department(data['created_by'])
            }
            section_name = self.request.query_params.get('section_name', None)
            if section_name:
                permission_details = []
                section_details = TCoreOther.objects.get(cot_name__iexact=section_name)
                approval_master_details = PmsApprovalPermissonMatser.objects.filter(section=section_details.id)
                # print("approval_master_details",approval_master_details)
                log_details = HrmsNewRequirementLog.objects. \
                    filter(master_hnr=response.data[0]['id']). \
                    values('id', 'level_approval', 'approval_permission_user_level', 'tag_name', 'created_at')
                # print('log_details',log_details)
                amd_list = []
                l_d_list = []
                for l_d in log_details:
                    # if l_d['tag_name']=='approval':
                    l_d_list.append(l_d['approval_permission_user_level'])

                for a_m_d in approval_master_details:
                    if l_d_list:
                        if a_m_d.id in l_d_list:
                            l_d = log_details.get(approval_permission_user_level=a_m_d.id)
                            f_name = a_m_d.approval_user.first_name if a_m_d.approval_user else ''
                            l_name = a_m_d.approval_user.last_name if a_m_d.approval_user else ''
                            # var=a_m_d.permission_level
                            # res = re.sub("\D", "", var)
                            permission_dict = {
                                "user_level": a_m_d.permission_level,
                                "approval": l_d['level_approval'],
                                # "permission_num":int(res),
                                "tag_name": l_d['tag_name'],
                                "approved_date": l_d['created_at'],
                                "user_details": {
                                    "id": a_m_d.approval_user.id if a_m_d.approval_user else None,
                                    "email": a_m_d.approval_user.email if a_m_d.approval_user else None,
                                    "name": f_name + ' ' + l_name,
                                    "username": a_m_d.approval_user.username,
                                    "department": department(a_m_d.approval_user.id),
                                    "designation": designation(a_m_d.approval_user.id)
                                }
                            }


                        else:
                            f_name = a_m_d.approval_user.first_name if a_m_d.approval_user else ''
                            l_name = a_m_d.approval_user.last_name if a_m_d.approval_user else ''
                            # var=a_m_d.permission_level
                            # res = re.sub("\D", "", var)
                            permission_dict = {
                                "user_level": a_m_d.permission_level,
                                # "permission_num":int(res),
                                "approval": None,
                                "tag_name": None,
                                "approved_date": None,
                                "user_details": {
                                    "id": a_m_d.approval_user.id if a_m_d.approval_user else None,
                                    "email": a_m_d.approval_user.email if a_m_d.approval_user else None,
                                    "name": f_name + ' ' + l_name,
                                    "username": a_m_d.approval_user.username,
                                    "department": department(a_m_d.approval_user.id),
                                    "designation": designation(a_m_d.approval_user.id)
                                }
                            }

                        permission_details.append(permission_dict)
                    else:
                        f_name = a_m_d.approval_user.first_name if a_m_d.approval_user else ''
                        l_name = a_m_d.approval_user.last_name if a_m_d.approval_user else ''
                        # var=a_m_d.permission_level
                        # res = re.sub("\D", "", var)
                        permission_dict = {
                            "user_level": a_m_d.permission_level,
                            # "permission_num":int(res),
                            "approval": None,
                            "tag_name": None,
                            "approved_date": None,
                            "user_details": {
                                "id": a_m_d.approval_user.id if a_m_d.approval_user else None,
                                "email": a_m_d.approval_user.email if a_m_d.approval_user else None,
                                "name": f_name + ' ' + l_name,
                                "username": a_m_d.approval_user.username,
                                "department": department(a_m_d.approval_user.id),
                                "designation": designation(a_m_d.approval_user.id)
                            }
                        }
                        permission_details.append(permission_dict)

            data_dict['approved_by_data'] = permission_details

            # print("data_dict",data_dict)

        response.data[0].update(data_dict)
        data_sp_dict = {}
        data_sp_dict['result'] = response.data[0]
        if response.data:
            data_sp_dict['request_status'] = 1
            data_sp_dict['msg'] = settings.MSG_SUCCESS
        elif len(response.data) == 0:
            data_sp_dict['request_status'] = 1
            data_sp_dict['msg'] = settings.MSG_NO_DATA
        else:
            data_sp_dict['request_status'] = 0
            data_sp_dict['msg'] = settings.MSG_ERROR
        response.data = data_sp_dict
        return response

    def put(self, request, *args, **kwargs):
        updated_by = request.user
        created_by = request.user
        # print(updated_by)

        req_id = self.request.query_params.get('req_id', None)
        approval_tag = self.request.query_params.get('approval_tag', None)
        approval_permission_user_level = request.data['approval_permission_user_level']

        if approval_tag.lower() == 'approval':

            level_approval = request.data['level_approval']

            updating_table = HrmsNewRequirement.objects.filter(id=req_id).update(
                approval_permission_user_level=approval_permission_user_level,
                level_approval=level_approval, updated_by=updated_by
            )
            data = HrmsNewRequirement.objects.filter(id=req_id)
            for obj in data.values():
                print(obj)
                log_create = HrmsNewRequirementLog.objects.create(
                    master_hnr_id=obj['id'],
                    issuing_department_id=obj['issuing_department_id'],
                    date=obj['date'],
                    type_of_vacancy=obj['type_of_vacancy'],
                    type_of_requirement=obj['type_of_requirement'],
                    reason=obj['reason'],
                    number_of_position=obj['number_of_position'],
                    proposed_designation_id=obj['proposed_designation_id'],
                    location=obj['location'],
                    substantiate_justification=['substantiate_justification'],
                    document=obj['document'],
                    desired_qualification=obj['desired_qualification'],
                    desired_experience=obj['desired_experience'],
                    desired_age_group=obj['desired_age_group'],
                    tab_status=obj['tab_status'],
                    gender=obj['gender'],
                    reporting_to_id=obj['reporting_to_id'],
                    number_of_subordinates=obj['number_of_subordinates'],
                    ctc=obj['ctc'],
                    required_skills=obj['required_skills'],
                    level_approval=obj['level_approval'],
                    tag_name=approval_tag.lower(),
                    created_by=created_by,
                    approval_permission_user_level_id=obj['approval_permission_user_level_id']

                )

            return Response(request.data)

        elif approval_tag.lower() == 'recieved':

            reciever_approval = request.data['reciever_approval']
            reciever_remarks = request.data['reciever_remarks']
            if reciever_approval == 1:
                updating_table = HrmsNewRequirement.objects.filter(id=req_id).update(
                    approval_permission_user_level=approval_permission_user_level,
                    reciever_approval=reciever_approval, updated_by=updated_by,
                    reciever_remarks=reciever_remarks, tab_status=3
                )
            else:
                updating_table = HrmsNewRequirement.objects.filter(id=req_id).update(
                    approval_permission_user_level=approval_permission_user_level,
                    reciever_approval=reciever_approval, updated_by=updated_by,
                    reciever_remarks=reciever_remarks
                )

            data = HrmsNewRequirement.objects.filter(id=req_id)
            for obj in data.values():
                print(obj)
                log_create = HrmsNewRequirementLog.objects.create(
                    master_hnr_id=obj['id'],
                    issuing_department_id=obj['issuing_department_id'],
                    date=obj['date'],
                    type_of_vacancy=obj['type_of_vacancy'],
                    type_of_requirement=obj['type_of_requirement'],
                    reason=obj['reason'],
                    number_of_position=obj['number_of_position'],
                    proposed_designation_id=obj['proposed_designation_id'],
                    location=obj['location'],
                    substantiate_justification=obj['substantiate_justification'],
                    document=obj['document'],
                    desired_qualification=obj['desired_qualification'],
                    desired_experience=obj['desired_experience'],
                    desired_age_group=obj['desired_age_group'],
                    tab_status=obj['tab_status'],
                    gender=obj['gender'],
                    reporting_to_id=obj['reporting_to_id'],
                    number_of_subordinates=obj['number_of_subordinates'],
                    ctc=obj['ctc'],
                    required_skills=obj['required_skills'],
                    level_approval=obj['reciever_approval'],
                    tag_name=approval_tag.lower(),
                    reciever_remarks=reciever_remarks,
                    created_by=created_by,
                    approval_permission_user_level_id=obj['approval_permission_user_level_id']

                )

            return Response(request.data)


#:::::::::::::::::::::: HRMS INTERVIEW TYPE:::::::::::::::::::::::::::#
class InterviewTypeAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = HrmsInterviewType.objects.filter(is_deleted=False)
    serializer_class = InterviewTypeAddSerializer

    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        return response


class InterviewTypeEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = HrmsInterviewType.objects.all()
    serializer_class = InterviewTypeEditSerializer


class InterviewTypeDeleteView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = HrmsInterviewType.objects.all()
    serializer_class = InterviewTypeDeleteSerializer


#:::::::::::::::::::::: HRMS INTERVIEW LEVEL:::::::::::::::::::::::::::#
class InterviewLevelAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = HrmsInterviewLevel.objects.filter(is_deleted=False)
    serializer_class = InterviewLevelAddSerializer

    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        return response


class InterviewLevelEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = HrmsInterviewLevel.objects.all()
    serializer_class = InterviewLevelEditSerializer


class InterviewLevelDeleteView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = HrmsInterviewLevel.objects.all()
    serializer_class = InterviewLevelDeleteSerializer


#:::::::::::::::::::::: HRMS SCHEDULE INTERVIEW :::::::::::::::::::::::::::#

class ScheduleInterviewAddView(generics.ListCreateAPIView, mixins.UpdateModelMixin):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = HrmsScheduleInterview.objects.filter(is_deleted=False)
    serializer_class = ScheduleInterviewAddSerializer

    @response_modify_decorator_post
    def post(self, request, *args, **kwargs):
        # print('request',request.data)
        contact_no = request.data['contact_no']
        # print('contact_no',contact_no)
        if HrmsScheduleInterview.objects.filter(contact_no=contact_no).count() > 0:
            custom_exception_message(self, 'Contact no')
        return super().post(request, *args, **kwargs)

    @response_modify_decorator_update
    def put(self, request, *args, **kwargs):
        try:
            updated_by = request.user
            sed_id = self.request.query_params.get('sed_id', None)
            req_id = self.request.query_params.get('req_id', None)
            action_approval = request.data.get('action_approval')
            # print("action_approval",action_approval)

            with transaction.atomic():
                # no_of_pos = HrmsNewRequirement.objects.get(id=req_id).number_of_position
                # unique_appoval = HrmsScheduleInterview.objects.filter(requirement=req_id,action_approval=1).annotate(Count('candidate_name',
                #                      distinct=True)).count()
                # print("no_of_pos",no_of_pos,"unique_appoval",unique_appoval)
                # if no_of_pos != unique_appoval:
                HrmsScheduleInterview.objects.filter(id=sed_id).update(
                    action_approval=action_approval
                )
                HrmsNewRequirement.objects.filter(id=req_id).update(tab_status=5)
                # no_pos = HrmsNewRequirement.objects.get(id=req_id).number_of_position
                # unique_appoval_count = HrmsScheduleInterview.objects.filter(requirement=req_id,action_approval=1).annotate(Count('candidate_name',
                #                  distinct=True)).count()
                # print("no_of_pos",no_pos,"unique_appoval",unique_appoval_count)
                #     if no_pos == unique_appoval_count:
                #         HrmsNewRequirement.objects.filter(id=req_id).update(tab_status=5)
                #         HrmsScheduleInterview.objects.filter(requirement=req_id).exclude(action_approval=1).update(action_approval=2)
                # else:
                #     custom_exception_message(self,None,"Number of position is Fullfilled")

                return request
        except Exception as e:
            raise e


class RescheduleInterviewAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = HrmsScheduleAnotherRoundInterview.objects.filter(is_deleted=False)
    serializer_class = RescheduleInterviewAddSerializer


class InterviewStatusAddView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = HrmsScheduleAnotherRoundInterview.objects.all()
    serializer_class = InterviewStatusAddSerializer


class InterviewStatusListView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = HrmsScheduleInterview.objects.filter(is_deleted=False)
    serializer_class = InterviewStatusListSerializer

    def get_queryset(self):
        approved = self.request.query_params.get('approved', None)
        req_id = self.request.query_params.get('req_id', None)
        cad_id = self.request.query_params.get('cad_id', None)
        if approved:
            if approved.lower() == "yes":
                queryset = self.queryset.filter(requirement=req_id, is_deleted=False, action_approval=1)
        elif cad_id:
            queryset = self.queryset.filter(id=cad_id, requirement=req_id, is_deleted=False)

        else:
            queryset = self.queryset.filter(requirement=req_id, is_deleted=False)

        return queryset

    @response_modify_decorator_get_after_execution
    def get(self, request, *args, **kwargs):
        approved = self.request.query_params.get('approved', None)
        interview_details = self.get_queryset()
        # print('interview_details',interview_details)
        interview_details_list = []
        if interview_details:
            for i_d in interview_details:
                schedule_another_det = HrmsScheduleAnotherRoundInterview.objects.filter(schedule_interview=i_d,
                                                                                        is_deleted=False
                                                                                        )
                interview_rounds_list = []
                for s_a_d in schedule_another_det:
                    round_details = {
                        'id': s_a_d.id,
                        'planned_date_of_interview': s_a_d.planned_date_of_interview,
                        'planned_time_of_interview': s_a_d.planned_time_of_interview,
                        'actual_date_of_interview': s_a_d.actual_date_of_interview,
                        'actual_time_of_interview': s_a_d.actual_time_of_interview,
                        'type_of_interview': s_a_d.type_of_interview.id,
                        'interview_type_name': s_a_d.type_of_interview.name,
                        'level_of_interview': s_a_d.level_of_interview.id,
                        'interview_level_name': s_a_d.level_of_interview.name,
                        'interview_status': s_a_d.interview_status,
                        'interview_status_name': s_a_d.get_interview_status_display(),
                        'is_resheduled': s_a_d.is_resheduled
                    }
                    interview_rounds_list.append(round_details)

                    interviewers = HrmsScheduleInterviewWith.objects.filter(interview=s_a_d, is_deleted=False)
                    # print('interviewers',interviewers)
                    interviewers_list = []
                    int_dict = {}
                    section_name = self.request.query_params.get('section_name', None)
                    if section_name:
                        permission_details = []
                        section_details = TCoreOther.objects.get(cot_name__iexact=section_name)
                        approval_master_details = PmsApprovalPermissonMatser.objects.filter(section=section_details.id)
                        # print("approval_master_details",approval_master_details)
                        log_details = HrmsScheduleInterviewLog.objects. \
                            filter(hsi_master=i_d.id). \
                            values('id', 'level_approval', 'approval_permission_user_level', 'created_at')
                        # print('log_details',log_details)
                        amd_list = []
                        l_d_list = []
                        for l_d in log_details:
                            # if l_d['tag_name']=='approval':
                            l_d_list.append(l_d['approval_permission_user_level'])

                        for a_m_d in approval_master_details:
                            if l_d_list:
                                if a_m_d.id in l_d_list:
                                    l_d = log_details.get(approval_permission_user_level=a_m_d.id)
                                    f_name = a_m_d.approval_user.first_name if a_m_d.approval_user else ''
                                    l_name = a_m_d.approval_user.last_name if a_m_d.approval_user else ''
                                    var = a_m_d.permission_level
                                    res = re.sub("\D", "", var)
                                    permission_dict = {
                                        "user_level": a_m_d.permission_level,
                                        "approval": l_d['level_approval'],
                                        "permission_num": int(res),
                                        # "tag_name":l_d['tag_name'],
                                        "approved_date": l_d['created_at'],
                                        "user_details": {
                                            "id": a_m_d.approval_user.id if a_m_d.approval_user else None,
                                            "email": a_m_d.approval_user.email if a_m_d.approval_user else None,
                                            "name": f_name + ' ' + l_name,
                                            "username": a_m_d.approval_user.username,
                                            "department": department(a_m_d.approval_user.id),
                                            "designation": designation(a_m_d.approval_user.id)
                                        }
                                    }


                                else:
                                    f_name = a_m_d.approval_user.first_name if a_m_d.approval_user else ''
                                    l_name = a_m_d.approval_user.last_name if a_m_d.approval_user else ''
                                    var = a_m_d.permission_level
                                    res = re.sub("\D", "", var)
                                    permission_dict = {
                                        "user_level": a_m_d.permission_level,
                                        "permission_num": int(res),
                                        "approval": None,
                                        # "tag_name":None,
                                        "approved_date": None,
                                        "user_details": {
                                            "id": a_m_d.approval_user.id if a_m_d.approval_user else None,
                                            "email": a_m_d.approval_user.email if a_m_d.approval_user else None,
                                            "name": f_name + ' ' + l_name,
                                            "username": a_m_d.approval_user.username,
                                            "department": department(a_m_d.approval_user.id),
                                            "designation": designation(a_m_d.approval_user.id)
                                        }
                                    }

                                permission_details.append(permission_dict)
                            else:
                                f_name = a_m_d.approval_user.first_name if a_m_d.approval_user else ''
                                l_name = a_m_d.approval_user.last_name if a_m_d.approval_user else ''
                                var = a_m_d.permission_level
                                res = re.sub("\D", "", var)
                                permission_dict = {
                                    "user_level": a_m_d.permission_level,
                                    "permission_num": int(res),
                                    "approval": None,
                                    # "tag_name":None,
                                    "approved_date": None,
                                    "user_details": {
                                        "id": a_m_d.approval_user.id if a_m_d.approval_user else None,
                                        "email": a_m_d.approval_user.email if a_m_d.approval_user else None,
                                        "name": f_name + ' ' + l_name,
                                        "username": a_m_d.approval_user.username,
                                        "department": department(a_m_d.approval_user.id),
                                        "designation": designation(a_m_d.approval_user.id)
                                    }
                                }
                                permission_details.append(permission_dict)

                    # data_dict['approved_by_data']=permission_details
                    if interviewers:
                        for i_t in interviewers:
                            int_dict = {
                                'id': i_t.id,
                                'interview': i_t.interview.id,
                                'user': i_t.user.id,
                                'first_name': i_t.user.first_name,
                                'last_name': i_t.user.last_name,
                            }
                            interviewers_list.append(int_dict)
                    round_details['interviewers'] = interviewers_list

                    upload_feedback = HrmsScheduleInterviewFeedback.objects.filter(interview=s_a_d, is_deleted=False)
                    feedback_dict = {}
                    if upload_feedback:
                        for u_f in upload_feedback:
                            upload_feedback = request.build_absolute_uri(
                                u_f.upload_feedback.url) if u_f.upload_feedback else None
                            feedback_dict = {
                                'id': u_f.id,
                                'interview': u_f.interview.id,
                                'upload_feedback': upload_feedback
                            }
                    round_details['feedback'] = feedback_dict

                    resume = request.build_absolute_uri(i_d.resume.url) if i_d.resume else None
                    if approved and approved.lower() == "yes":
                        interview_dict = {
                            'id': i_d.id,
                            'candidate_name': i_d.candidate_name,
                            'contact_no': i_d.contact_no,
                            'email': i_d.email,
                            'note': i_d.note,
                            'resume': resume,
                            "interview_rounds": interview_rounds_list,
                            'notice_period': i_d.notice_period,
                            'expected_ctc': i_d.expected_ctc,
                            'current_ctc': i_d.current_ctc,
                            'action_approval': i_d.get_action_approval_display(),
                            'approved_by_data': permission_details
                        }
                    else:
                        interview_dict = {
                            'id': i_d.id,
                            'candidate_name': i_d.candidate_name,
                            'contact_no': i_d.contact_no,
                            'email': i_d.email,
                            'note': i_d.note,
                            'resume': resume,
                            "interview_rounds": interview_rounds_list,
                            'action_approval': i_d.get_action_approval_display(),
                            'approved_by_data': permission_details
                        }
                interview_details_list.append(interview_dict)

        return Response(interview_details_list)


class CandidatureUpdateEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = HrmsScheduleInterview.objects.filter(is_deleted=False)
    serializer_class = CandidatureUpdateEditSerializer


class CandidatureApproveEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = HrmsScheduleInterview.objects.filter(is_deleted=False)
    serializer_class = CandidatureApproveEditSerializer


class OpenAndClosedRequirementListView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = HrmsNewRequirement.objects.filter(is_deleted=False).order_by('-id')
    serializer_class = OpenAndClosedRequirementListSerializer
    pagination_class = CSPageNumberPagination

    def get_queryset(self):
        filter = {}
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        department = self.request.query_params.get('department', None)
        designation = self.request.query_params.get('designation', None)
        if self.queryset.count():
            if start_date and end_date:
                start_object = datetime.datetime.strptime(start_date, '%Y-%m-%d')
                end_object = datetime.datetime.strptime(end_date, '%Y-%m-%d')
                filter['date__date__gte'] = start_object
                filter['date__date__lte'] = end_object + timedelta(days=1)
            if department:
                department = department.split(',')
                filter['issuing_department__in'] = department

            if designation:
                designation = designation.split(',')
                filter['proposed_designation__in'] = designation

        if filter:
            # print('asda',self.queryset.filter(**filter,is_deleted=False))
            return self.queryset.filter(**filter, is_deleted=False)
        else:
            return self.queryset

    @response_modify_decorator_list_or_get_after_execution_for_pagination
    def get(self, request, *args, **kwargs):
        type = self.request.query_params.get('type', None)
        response = super(OpenAndClosedRequirementListView, self).get(self, request, args, kwargs)
        # print('response--->',response.data)
        if response.data['results']:
            data_list = []
            for data in response.data['results']:
                # print('data',data)
                if type.lower() == "open":
                    if data['tab_status'] <= 6:
                        data_list.append(data)

                elif type.lower() == "close":
                    if data['tab_status'] == 6:
                        data_list.append(data)

            response.data['results'] = data_list
            return response

        else:
            return response


class UpcomingAndInterviewHistoryListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = HrmsScheduleInterview.objects.filter(is_deleted=False).order_by('-id')
    serializer_class = UpcomingAndInterviewHistoryListSerializer
    pagination_class = CSPageNumberPagination

    def get_queryset(self):
        filter = {}
        planned_start_date = self.request.query_params.get('planned_start_date', None)
        planned_end_date = self.request.query_params.get('planned_end_date', None)
        actual_start_date = self.request.query_params.get('actual_start_date', None)
        actual_end_date = self.request.query_params.get('actual_end_date', None)
        interview_type = self.request.query_params.get('interview_type', None)
        department = self.request.query_params.get('department', None)
        designation = self.request.query_params.get('designation', None)
        search = self.request.query_params.get('search', None)
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)

        if field_name and order_by:
            if field_name == 'planned_date_of_interview' and order_by == 'asc':
                another_round = HrmsScheduleAnotherRoundInterview.objects.filter(is_deleted=False
                                                                                 ).order_by('planned_date_of_interview')
                # print('another_round',another_round)
                another_round_list = []
                for a_r in another_round:
                    schedule_id = a_r.schedule_interview.id
                    another_round_list.append(schedule_id)
                # print('another_round_list',another_round_list)
                clauses = ' '.join(
                    ['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(another_round_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=another_round_list).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset', queryset)
                return queryset

            if field_name == 'planned_date_of_interview' and order_by == 'desc':
                another_round = HrmsScheduleAnotherRoundInterview.objects.filter(is_deleted=False
                                                                                 ).order_by(
                    '-planned_date_of_interview')
                # print('another_round',another_round)
                another_round_list = []
                for a_r in another_round:
                    schedule_id = a_r.schedule_interview.id
                    another_round_list.append(schedule_id)
                # print('another_round_list',another_round_list)
                clauses = ' '.join(
                    ['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(another_round_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=another_round_list).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset', queryset)
                return queryset
            if field_name == 'actual_date_of_interview' and order_by == 'asc':
                another_round = HrmsScheduleAnotherRoundInterview.objects.filter(is_deleted=False
                                                                                 ).order_by('actual_date_of_interview')
                # print('another_round',another_round)
                another_round_list = []
                for a_r in another_round:
                    schedule_id = a_r.schedule_interview.id
                    another_round_list.append(schedule_id)
                # print('another_round_list',another_round_list)
                clauses = ' '.join(
                    ['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(another_round_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=another_round_list).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset', queryset)
                return queryset

            if field_name == 'actual_date_of_interview' and order_by == 'desc':
                another_round = HrmsScheduleAnotherRoundInterview.objects.filter(is_deleted=False
                                                                                 ).order_by('-actual_date_of_interview')
                # print('another_round',another_round)
                another_round_list = []
                for a_r in another_round:
                    schedule_id = a_r.schedule_interview.id
                    another_round_list.append(schedule_id)
                # print('another_round_list',another_round_list)
                clauses = ' '.join(
                    ['WHEN id=%s THEN %s' % (pk, i) for i, pk in enumerate(another_round_list)])
                ordering = 'CASE %s END' % clauses
                queryset = self.queryset.filter(pk__in=another_round_list).extra(
                    select={'ordering': ordering}, order_by=('ordering',))
                # print('queryset', queryset)
                return queryset
            if field_name == 'date_of_requirement' and order_by == 'asc':
                return self.queryset.all().order_by('requirement__date')

            if field_name == 'date_of_requirement' and order_by == 'desc':
                return self.queryset.all().order_by('-requirement__date')

        if interview_type:
            if interview_type.lower() == "upcoming":
                # queryset=self.queryset.filter(requirement__tab_status__lte=5,action_approval=3,is_deleted=False)
                filter['requirement__tab_status__lte'] = 5
                filter['action_approval'] = 3
            elif interview_type.lower() == "history":
                # queryset=self.queryset.filter(action_approval__lte=3,is_deleted=False)
                filter['action_approval__lte'] = 3
            # return queryset

        if planned_start_date and planned_end_date:
            planned_start_object = datetime.datetime.strptime(planned_start_date, '%Y-%m-%d')
            planned_end_object = datetime.datetime.strptime(planned_end_date, '%Y-%m-%d')
            another_round = HrmsScheduleAnotherRoundInterview.objects.filter(
                planned_date_of_interview__date__gte=planned_start_object,
                planned_date_of_interview__date__lte=(planned_end_object + timedelta(days=1))
                ).values_list('schedule_interview')
            # print('another_round',another_round)
            filter['id__in'] = another_round

        if actual_start_date and actual_end_date:
            actual_start_object = datetime.datetime.strptime(actual_start_date, '%Y-%m-%d')
            actual_end_object = datetime.datetime.strptime(actual_end_date, '%Y-%m-%d')
            actual_date_id = HrmsScheduleAnotherRoundInterview.objects.filter(
                actual_date_of_interview__date__gte=actual_start_object,
                actual_date_of_interview__date__lte=(actual_end_object + timedelta(days=1))
                ).values_list('schedule_interview')
            filter['id__in'] = actual_date_id

        if department:
            department = department.split(',')
            filter['requirement__issuing_department__in'] = department

        if designation:
            designation = designation.split(',')
            filter['requirement__proposed_designation__in'] = designation

        if search:
            search = search.split(",")
            for i in search:
                queryset_all = HrmsScheduleInterview.objects.none()
                queryset = self.queryset.filter(Q(candidate_name__icontains=i) |
                                                Q(contact_no__icontains=i) | Q(email__icontains=i)).order_by('-id')
                queryset_all = (queryset_all | queryset)
            return queryset_all

        if filter:
            return self.queryset.filter(**filter)

    @response_modify_decorator_list_or_get_after_execution_for_pagination
    def get(self, request, *args, **kwargs):
        response = super(UpcomingAndInterviewHistoryListView, self).get(self, request, args, kwargs)
        interview_type = self.request.query_params.get('interview_type', None)
        for data in response.data['results']:
            # print('data',data)
            schedule_another_det = HrmsScheduleAnotherRoundInterview.objects.filter(schedule_interview=data['id'],
                                                                                    is_deleted=False
                                                                                    )
            # print('schedule_another_det',schedule_another_det)
            for s_a_d in schedule_another_det:
                data['type_of_interview'] = s_a_d.type_of_interview.id
                data['interview_type_name'] = s_a_d.type_of_interview.name
                data['level_of_interview'] = s_a_d.level_of_interview.id
                data['interview_level_name'] = s_a_d.level_of_interview.name
                interviewers = HrmsScheduleInterviewWith.objects.filter(interview=s_a_d, is_deleted=False)
                interviewers_list = []
                if interviewers:
                    for i_t in interviewers:
                        int_dict = {
                            'id': i_t.id,
                            'interview': i_t.interview.id,
                            'user': i_t.user.id,
                            'first_name': i_t.user.first_name,
                            'last_name': i_t.user.last_name,
                        }
                        interviewers_list.append(int_dict)

                upload_feedback = HrmsScheduleInterviewFeedback.objects.filter(interview=s_a_d, is_deleted=False)
                feedback_list = []
                feedback_dict = {}
                if upload_feedback:
                    for u_f in upload_feedback:
                        upload_feedback = request.build_absolute_uri(
                            u_f.upload_feedback.url) if u_f.upload_feedback else None
                        feedback_dict = {
                            'id': u_f.id,
                            'interview': u_f.interview.id,
                            'upload_feedback': upload_feedback
                        }
                        feedback_list.append(feedback_dict)

                if interview_type and interview_type.lower() == "upcoming":
                    data['interview_round_id'] = s_a_d.id
                    data['planned_date_of_interview'] = s_a_d.planned_date_of_interview
                    data['planned_time_of_interview'] = s_a_d.planned_time_of_interview
                    data['interviewers'] = interviewers_list

                elif interview_type and interview_type.lower() == "history":
                    data['actual_date_of_interview'] = s_a_d.actual_date_of_interview
                    data['actual_time_of_interview'] = s_a_d.actual_time_of_interview
                    data['interviewers'] = interviewers_list
                    data['feedback'] = feedback_list
                    data['interview_status'] = s_a_d.interview_status
                    data['interview_status_name'] = s_a_d.get_interview_status_display()

        return response


class EmployeeActiveInactiveUserView(generics.RetrieveUpdateAPIView):
    """
    send parameter 'is_active'
    View for user update active and in_active
    using user ID
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    serializer_class = EmployeeActiveInactiveUserSerializer
    queryset = User.objects.all()


class EmployeeActiveUserListView(generics.ListAPIView):
    '''
        Reason : Get Active User List in Excel File
        Author : Rupam Hazra
        Line number:  3449 - 3465
        Date : 10/03/2020
    '''
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = User.objects.filter(is_superuser=False, is_active=True)
    serializer_class = EmployeeListSerializer
    pagination_class = OnOffPagination

    def get_queryset(self):
        '''
            eleminate login user on employee list added by Rupam Hazra Line number 458 - 459
        '''
        login_user = self.request.user.id
        self.queryset = self.queryset.filter(is_active=True)

        sort_field = '-id'
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        department = self.request.query_params.get('department', None)
        designation = self.request.query_params.get('designation', None)
        start_date = self.request.query_params.get('from_date', None)
        end_date = self.request.query_params.get('to_date', None)
        company = self.request.query_params.get('company', None)
        employee = self.request.query_params.get('employee', None)

        filter = dict()
        if company:
            filter['company'] = company

        if employee:
            print(employee)
            filter['cu_user__id'] = employee

        if start_date and end_date:
            start_object = datetime.datetime.strptime(start_date, '%Y-%m-%d')
            end_object = datetime.datetime.strptime(end_date, '%Y-%m-%d')
            filter['joining_date__date__gte'] = start_object.date()
            filter['joining_date__date__lte'] = end_object.date()

        if field_name and order_by:
            if field_name == 'username' and order_by == 'asc':
                sort_field = 'username'
            if field_name == 'username' and order_by == 'desc':
                sort_field = '-username'

        if department:
            filter['department_id'] = department
        if designation:
            filter['designation_id'] = designation

        queryset = self.queryset.filter(is_active=True, id__in=(
            TCoreUserDetail.objects.filter(
                ~Q(cu_punch_id='#N/A'), termination_date__isnull=True,
                cu_is_deleted=False, **filter
            ).values_list('cu_user', flat=True))).order_by(sort_field)

        return queryset

    def get_datalist_for_file(self, request, *args, **kwargs):
        self.request.query_params._mutable = True
        self.request.query_params['page'] = 1
        self.request.query_params['page_size'] = 0
        self.request.query_params._mutable = False
        full_response = super(EmployeeActiveUserListView, self).get(self, request, *args, **kwargs)
        print('length:', len(full_response.data))

        full_list = list()
        from pandas import DataFrame

        lst_length = 0

        for data in full_response.data:
            role_details = TCoreUserDetail.objects.filter(
                cu_user=data['id'], cu_is_deleted=False, cu_user__is_active=True
            ).values(
                'cu_user__username', 'cu_user__first_name', 'cu_user__last_name',
                'cu_emp_code', 'cu_alt_phone_no', 'cu_alt_email_id', 'company__id', 'company__coc_name',
                'joining_date', 'hod__id', 'hod__first_name', 'hod__last_name', 'designation__id', 'cu_user__id',
                'designation__cod_name', 'department__id', 'department__cd_name', 'reporting_head__id',
                'reporting_head__first_name', 'reporting_head__last_name', 'employee_grade__cg_name',
                'employee_sub_grade',
                'sap_personnel_no', 'cu_punch_id', 'user_type', 'is_confirm', 'salary_type__st_name', 'bank_name_p',
                'job_location', 'job_location_state', 'job_location_state__cs_state_name', 'salary_per_month', 'vpf_no',
                'pf_no', 'esic_no', 'cu_gender', 'address', 'state',
                'state__cs_state_name', 'pincode', 'emergency_relationship', 'emergency_contact_no',
                'emergency_contact_name',
                'pan_no', 'aadhar_no', 'father_name', 'marital_status', 'cu_user__email', 'bank_account',
                'bank_name_p__name',
                'ifsc_code', 'blood_group', 'bus_facility', 'highest_qualification', 'previous_employer',
                'total_experience',
                'cu_dob', 'initial_ctc', 'current_ctc', 'cost_centre', 'updated_cost_centre',
                'updated_cost_centre__cost_centre_code',
                'branch_name', 'uan_no', 'employee_voluntary_provident_fund_contribution',
                'contributing_towards_pension_scheme',
                'provident_trust_fund', 'pf_trust_code', 'pf_description', 'emp_pension_no', 'pension_trust_id',
                'is_flexi_hour',
                'has_pf', 'has_esi', 'esi_dispensary', 'esi_sub_type', 'attendance_type', 'care_of', 'country_key',
                'city', 'district',
                'retirement_date', 'wbs_element', 'work_schedule_rule', 'time_management_status', 'ptax_sub_type',
                'source', 'source_name', 'file_no'
            )

            username = role_details[0]['cu_user__username'] if role_details[0]['cu_user__username'] else None
            first_name = role_details[0]['cu_user__first_name'] if role_details[0]['cu_user__first_name'] else ''
            last_name = role_details[0]['cu_user__last_name'] if role_details[0]['cu_user__last_name'] else ''
            employee_name = first_name + ' ' + last_name

            reporting_head__first_name = role_details[0]['reporting_head__first_name'] if role_details[0][
                'reporting_head__first_name'] else ''
            reporting_head__last_name = role_details[0]['reporting_head__last_name'] if role_details[0][
                'reporting_head__last_name'] else ''
            reporting_head = reporting_head__first_name + " " + reporting_head__last_name

            hod__first_name = role_details[0]['hod__first_name'] if role_details[0]['hod__first_name'] else ''
            hod__last_name = role_details[0]['hod__last_name'] if role_details[0]['hod__last_name'] else ''
            hod_name = hod__first_name + " " + hod__last_name

            joining_date = role_details[0]['joining_date'] if role_details[0]['joining_date'] else ''
            emp_code = role_details[0]['cu_emp_code'] if role_details[0]['cu_emp_code'] else ''
            sap_personnel_no = role_details[0]['sap_personnel_no'] if role_details[0]['sap_personnel_no'] else ''
            punch_id = role_details[0]['cu_punch_id'] if role_details[0]['cu_punch_id'] else ''

            company_name = role_details[0]['company__coc_name'] if role_details[0]['company__coc_name'] else ''
            department_name = role_details[0]['department__cd_name'] if role_details[0]['department__cd_name'] else ''
            designation_name = role_details[0]['designation__cod_name'] if role_details[0][
                'designation__cod_name'] else ''

            official_contact_no = role_details[0]['cu_alt_phone_no'] if role_details[0]['cu_alt_phone_no'] else ''
            official_email_id = role_details[0]['cu_alt_email_id'] if role_details[0]['cu_alt_email_id'] else ''
            user_type = role_details[0]['user_type'] if role_details[0]['user_type'] else ''
            job_location = role_details[0]['job_location'] if role_details[0]['job_location'] else ''
            job_location_state = role_details[0]['job_location_state__cs_state_name'] if role_details[0][
                'job_location_state'] else ''
            salary_per_month = role_details[0]['salary_per_month'] if role_details[0]['salary_per_month'] else ''
            vpf_no = role_details[0]['vpf_no'] if role_details[0]['vpf_no'] else 'No'
            pf_no = role_details[0]['pf_no'] if role_details[0]['pf_no'] else 'No'
            esic_no = role_details[0]['esic_no'] if role_details[0]['esic_no'] else 'No'
            is_confirm = role_details[0]['is_confirm'] if role_details[0]['is_confirm'] else False
            salary_type = role_details[0]['salary_type__st_name'] if role_details[0]['salary_type__st_name'] else ''
            grade = role_details[0]['employee_grade__cg_name'] if role_details[0]['employee_grade__cg_name'] else ''
            gender = role_details[0]['cu_gender'] if role_details[0]['cu_gender'] else ''
            address = role_details[0]['address'] if role_details[0]['address'] else ''
            state = role_details[0]['state__cs_state_name'] if role_details[0]['state'] else ''
            pincode = role_details[0]['pincode'] if role_details[0]['pincode'] else ''
            emergency_relationship = role_details[0]['emergency_relationship'] if role_details[0][
                'emergency_relationship'] else ''
            emergency_contact_no = role_details[0]['emergency_contact_no'] if role_details[0][
                'emergency_contact_no'] else ''
            emergency_contact_name = role_details[0]['emergency_contact_name'] if role_details[0][
                'emergency_contact_name'] else ''
            pan_no = role_details[0]['pan_no'] if role_details[0]['pan_no'] else ''
            aadhar_no = role_details[0]['aadhar_no'] if role_details[0]['aadhar_no'] else ''
            father_name = role_details[0]['father_name'] if role_details[0]['father_name'] else ''
            marital_status = role_details[0]['marital_status'] if role_details[0]['marital_status'] else ''
            personal_email_id = role_details[0]['cu_user__email'] if role_details[0]['cu_user__email'] else ''
            bank_name = role_details[0]['bank_name_p__name'] if role_details[0]['bank_name_p'] else ''
            bank_account = role_details[0]['bank_account'] if role_details[0]['bank_account'] else ''
            ifsc_code = role_details[0]['ifsc_code'] if role_details[0]['ifsc_code'] else ''
            blood_group = role_details[0]['blood_group'] if role_details[0]['blood_group'] else ''
            bus_facility = role_details[0]['bus_facility'] if role_details[0]['bus_facility'] else ''
            highest_qualification = role_details[0]['highest_qualification'] if role_details[0][
                'highest_qualification'] else ''
            previous_employer = role_details[0]['previous_employer'] if role_details[0]['previous_employer'] else ''
            total_experience = role_details[0]['total_experience'] if role_details[0]['total_experience'] else ''
            dob = role_details[0]['cu_dob'] if role_details[0]['cu_dob'] else ''
            initial_ctc = role_details[0]['initial_ctc'] if role_details[0]['initial_ctc'] else ''
            current_ctc = role_details[0]['current_ctc'] if role_details[0]['current_ctc'] else ''
            # cost_centre = role_details[0]['cost_centre'] if role_details[0]['cost_centre'] else ''
            branch_name = role_details[0]['branch_name'] if role_details[0]['branch_name'] else ''
            uan_no = role_details[0]['uan_no'] if role_details[0]['uan_no'] else ''
            employee_voluntary_provident_fund_contribution = role_details[0][
                'employee_voluntary_provident_fund_contribution'] \
                if role_details[0]['employee_voluntary_provident_fund_contribution'] else ''
            contributing_towards_pension_scheme = role_details[0]['contributing_towards_pension_scheme'] if \
                role_details[0]['contributing_towards_pension_scheme'] else ''
            provident_trust_fund = role_details[0]['provident_trust_fund'] if role_details[0][
                'provident_trust_fund'] else ''
            pf_trust_code = role_details[0]['pf_trust_code'] if role_details[0]['pf_trust_code'] else ''
            pf_description = role_details[0]['pf_description'] if role_details[0]['pf_description'] else ''
            emp_pension_no = role_details[0]['emp_pension_no'] if role_details[0]['emp_pension_no'] else ''
            pension_trust_id = role_details[0]['pension_trust_id'] if role_details[0]['pension_trust_id'] else ''
            is_flexi_hour = role_details[0]['is_flexi_hour'] if role_details[0]['is_flexi_hour'] else ''
            has_pf = role_details[0]['has_pf'] if role_details[0]['has_pf'] else ''
            has_esi = role_details[0]['has_esi'] if role_details[0]['has_esi'] else ''
            esi_dispensary = role_details[0]['esi_dispensary'] if role_details[0]['esi_dispensary'] else ''
            esi_sub_type = role_details[0]['esi_sub_type'] if role_details[0]['esi_sub_type'] else ''
            attendance_type = role_details[0]['attendance_type'] if role_details[0]['attendance_type'] else ''
            care_of = role_details[0]['care_of'] if role_details[0]['care_of'] else ''
            country_key = role_details[0]['country_key'] if role_details[0]['country_key'] else ''
            city = role_details[0]['city'] if role_details[0]['city'] else ''
            file_no = role_details[0]['file_no'] if role_details[0]['file_no'] else ''
            district = role_details[0]['district'] if role_details[0]['district'] else ''
            retirement_date = role_details[0]['retirement_date'] if role_details[0]['retirement_date'] else ''
            wbs_element = role_details[0]['wbs_element'] if role_details[0]['wbs_element'] else ''
            work_schedule_rule = role_details[0]['work_schedule_rule'] if role_details[0]['work_schedule_rule'] else ''
            time_management_status = role_details[0]['time_management_status'] if role_details[0][
                'time_management_status'] else ''
            ptax_sub_type = role_details[0]['ptax_sub_type'] if role_details[0]['ptax_sub_type'] else ''
            source = role_details[0]['source'] if role_details[0]['source'] else ''
            source_name = role_details[0]['source_name'] if role_details[0]['source_name'] else ''
            cost_centre = role_details[0]['updated_cost_centre__cost_centre_code'] if role_details[0][
                'updated_cost_centre'] else None

            if role_details[0]['employee_sub_grade']:
                sub_grade = TCoreSubGrade.objects.get(id=role_details[0]['employee_sub_grade'])
                employee_sub_grade = sub_grade.name
                employee_sub_grade_id = sub_grade.id
            else:
                employee_sub_grade = ""
                employee_sub_grade_id = ""

            personal_documents = HrmsDynamicSectionFieldLabelDetailsWithDoc.objects.filter(user=data['id'],
                                                                                           is_deleted=False,
                                                                                           field_label="Other Documents")

            # other_documents_list = []
            # if personal_documents:
            #     for doc_details in personal_documents:
            #         if (doc_details.tab_name).lower() == "personal":
            #             if doc_details.__dict__['document'] == "":
            #                 file_url = ''
            #             else:
            #                 file_url = request.build_absolute_uri(doc_details.document.url)
            #
            #             if doc_details.__dict__['document_name'] == "":
            #                 doc_name = ""
            #             else:
            #                 doc_name = doc_details.document_name
            #
            #             if doc_details.field_label == "Other Documents":
            #                 other_documents_dict = {
            #                     'id': doc_details.id,
            #                     'field_label_value': doc_details.field_label_value if doc_details.field_label_value else None,
            #                     'document_name': doc_name,
            #                     'document': file_url
            #                 }
            #                 other_documents_list.append(other_documents_dict)

            # print(personal_documents)
            document_str = ''
            count_doc = 1
            if personal_documents:
                other_documents_list = []
                for doc_details in personal_documents:
                    if (doc_details.tab_name).lower() == "personal":

                        if doc_details.__dict__['document_name'] == "":
                            doc_name = ""
                        else:
                            doc_name = doc_details.document_name

                        if doc_details.field_label == "Other Documents":
                            field_label_value = str(
                                doc_details.field_label_value) if doc_details.field_label_value else ''

                            document_str = str(document_str) + str(count_doc) + '.' + "name:" + str(
                                doc_name) + ',' + "number:" + str(field_label_value) + ', '
                    count_doc = count_doc + 1


            else:
                document_str = document_str

            data['other_documents'] = document_str
            data['username'] = username
            data['first_name'] = first_name
            data['last_name'] = last_name
            data['reporting_head'] = reporting_head
            data['hod_name'] = hod_name
            data['joining_date'] = joining_date
            data['emp_code'] = emp_code
            data['sap_personnel_no'] = sap_personnel_no
            data['punch_id'] = punch_id
            data['company_name'] = company_name
            data['department_name'] = department_name
            data['designation_name'] = designation_name
            data['official_contact_no'] = official_contact_no
            data['official_email_id'] = official_email_id
            data['user_type'] = user_type
            data['is_confirm'] = is_confirm
            data['salary_type'] = salary_type
            data['grade'] = grade
            data['sub_grade'] = employee_sub_grade
            data["sub_grade_id"] = employee_sub_grade_id
            data['job_location'] = job_location
            data['job_location_state'] = job_location_state
            data['salary_per_month'] = salary_per_month
            data['vpf_no'] = vpf_no
            data['pf_no'] = pf_no
            data['esic_no'] = esic_no
            data['gender'] = gender
            data['address'] = address
            data['state'] = state
            data['pincode'] = pincode
            data['emergency_relationship'] = emergency_relationship
            data['emergency_contact_no'] = emergency_contact_no
            data['emergency_contact_name'] = emergency_contact_name
            data['pan_no'] = pan_no
            data['aadhar_no'] = aadhar_no
            data['father_name'] = father_name
            data['marital_status'] = marital_status
            data['personal_email_id'] = personal_email_id
            data['bank_name'] = bank_name
            data['bank_account'] = bank_account
            data['ifsc_code'] = ifsc_code
            data['blood_group'] = blood_group
            data['bus_facility'] = bus_facility
            data['highest_qualification'] = highest_qualification
            data['previous_employer'] = previous_employer
            data['total_experience'] = total_experience
            data['dob'] = dob
            data['initial_ctc'] = initial_ctc
            data['current_ctc'] = current_ctc
            data['cost_centre'] = cost_centre
            data['branch_name'] = branch_name
            data['uan_no'] = uan_no
            data['employee_voluntary_provident_fund_contribution'] = employee_voluntary_provident_fund_contribution
            data['contributing_towards_pension_scheme'] = contributing_towards_pension_scheme
            data['provident_trust_fund'] = provident_trust_fund
            data['pf_trust_code'] = pf_trust_code
            data['pf_description'] = pf_description
            data['emp_pension_no'] = emp_pension_no
            data['pension_trust_id'] = pension_trust_id
            data['is_flexi_hour'] = is_flexi_hour
            data['has_pf'] = has_pf
            data['has_esi'] = has_esi
            data['esi_dispensary'] = esi_dispensary
            data['esi_sub_type'] = esi_sub_type
            data['attendance_type'] = attendance_type
            data['care_of'] = care_of
            data['country_key'] = country_key
            data['city'] = city
            data['district'] = district
            data['retirement_date'] = retirement_date
            data['wbs_element'] = wbs_element
            data['work_schedule_rule'] = work_schedule_rule
            data['time_management_status'] = time_management_status
            data['ptax_sub_type'] = ptax_sub_type
            data['source'] = source
            data['source_name'] = source_name
            data['file_no'] = file_no

            data_list = [username, first_name, last_name, reporting_head, hod_name, joining_date, "'" + emp_code,
                         "'" + sap_personnel_no, "'" + punch_id, company_name, department_name, designation_name,
                         official_contact_no,
                         official_email_id, user_type, is_confirm, salary_type, grade, employee_sub_grade, job_location,
                         job_location_state, salary_per_month,
                         vpf_no, pf_no, esic_no, gender, address, state, pincode, emergency_relationship,
                         emergency_contact_no,
                         emergency_contact_name, pan_no, aadhar_no, father_name, marital_status, personal_email_id,
                         bank_name,
                         bank_account, ifsc_code, blood_group, bus_facility, highest_qualification, previous_employer,
                         total_experience, dob, initial_ctc, current_ctc, cost_centre,
                         branch_name, uan_no, employee_voluntary_provident_fund_contribution,
                         contributing_towards_pension_scheme,
                         provident_trust_fund, pf_trust_code, pf_description, emp_pension_no, pension_trust_id,
                         is_flexi_hour,
                         has_pf, has_esi, esi_dispensary, esi_sub_type, attendance_type, care_of, country_key,
                         city, district,
                         retirement_date, wbs_element, work_schedule_rule, time_management_status, ptax_sub_type,
                         source, source_name, document_str, file_no
                         ]

            full_list.append(data_list)

        # return full_response
        return full_list

    @response_modify_decorator_list_or_get_after_execution_for_onoff_pagination
    def get(self, request, *args, **kwargs):
        response = super(EmployeeActiveUserListView, self).get(self, request, args, kwargs)

        from pandas import DataFrame
        export_download = self.request.query_params.get('export_download', None)
        if export_download == 'yes':
            full_list = self.get_datalist_for_file(request, *args, **kwargs)
            print(full_list[0])
            print("print length fullist " + str(len(full_list)))

            response.data = list()
            file_name = ''
            if full_list:
                if os.path.isdir('media/attendance/active_users_report/document'):
                    file_name = 'media/attendance/active_users_report/document/active_users_report.xlsx'
                else:
                    os.makedirs('media/attendance/active_users_report/document')
                    file_name = 'media/attendance/active_users_report/document/active_users_report.xlsx'
                file_path = settings.MEDIA_ROOT_EXPORT + file_name
                columns = [
                    'Username', 'First Name', 'Last Name', 'Reporting Head',
                    'HOD', 'Joining Date', 'Emp code', 'SAP', 'Punch Id', 'Company',
                    'Department', 'Designation', 'Contact No', 'Email Id', 'User Type',
                    'Is Confirm', 'Salary Type', 'Grade', 'Sub Grade', 'Job Location', 'job_location_state',
                    'Salary Per Month',
                    'VPF', 'PF', 'ESI',
                    'Gender', 'Address', 'State', 'Pincode', 'Emergency Relationship', 'Emergency Contact No',
                    'Emergency Contact Name', 'PAN No.', 'Adhhar No.', "Father's name",
                    'Maritial Status', 'Personal Email', 'Bank Name', 'Bank A/C', 'IFSC', 'Blood Gr.',
                    'Bus Facility',
                    'Highest Qualification', 'Previous Employer', 'Total Exp.', 'Dob', 'Initial CTC', 'Current CTC',
                    'Cost Centre',
                    'Branch Name', 'Uan No', 'Employee Voluntary Provident Fund Contribution',
                    'Contributing Towards Pension Scheme',
                    'Provident Trust Fund', 'PF Trust Code', 'PF Description', 'Emp Pension No', 'Pension Trust Id',
                    'Is Flexi Hour',
                    'Has_pf', 'Has Esi', 'Esi Dispensary', 'Esi Sub Type', 'Attendance Type', 'Care Of',
                    'Country Key', 'City', 'District',
                    'Retirement Date', 'Wbs Element', 'Work Schedule Rule', 'Time Management Status',
                    'Ptax_Sub_Type', 'Source', 'Source Name', 'other_documents', 'File No'
                ]
                df = DataFrame(
                    full_list, columns=columns
                )

            export_csv = df.to_excel(file_path, index=None, header=True)
            if request.is_secure():
                protocol = 'https://'
            else:
                protocol = 'http://'
            url = getHostWithPort(request) + file_name if file_name else None
            data_dict = dict()
            data_dict['results'] = response.data
            data_dict['url'] = url
            response.data = data_dict
            return response
        else:
            if 'results' in response.data:
                response_s = response.data['results']
            else:
                response_s = response.data
            # print('response check::::::::::::::',response_s)
            list_type = self.request.query_params.get('list_type', None)
            module_id = self.request.query_params.get('module_id', None)

            p_doc_dict = {}
            total_list = list()

            for data in response_s:
                role_details = TCoreUserDetail.objects.filter(
                    cu_user=data['id'], cu_is_deleted=False, cu_user__is_active=True
                ).values(
                    'cu_user__username', 'cu_user__first_name', 'cu_user__last_name',
                    'cu_emp_code', 'cu_alt_phone_no', 'cu_alt_email_id', 'company__id', 'company__coc_name',
                    'joining_date', 'hod__id', 'hod__first_name', 'hod__last_name', 'designation__id', 'cu_user__id',
                    'designation__cod_name', 'department__id', 'department__cd_name', 'reporting_head__id',
                    'reporting_head__first_name', 'reporting_head__last_name', 'employee_grade__cg_name',
                    'employee_sub_grade',
                    'sap_personnel_no', 'cu_punch_id', 'user_type', 'is_confirm', 'salary_type__st_name', 'bank_name_p',
                    'job_location', 'job_location_state', 'job_location_state__cs_state_name', 'salary_per_month',
                    'vpf_no', 'pf_no', 'esic_no', 'cu_gender', 'address', 'state',
                    'state__cs_state_name', 'pincode', 'emergency_relationship', 'emergency_contact_no',
                    'emergency_contact_name',
                    'pan_no', 'aadhar_no', 'father_name', 'marital_status', 'cu_user__email', 'bank_account',
                    'bank_name_p__name',
                    'ifsc_code', 'blood_group', 'bus_facility', 'highest_qualification', 'previous_employer',
                    'total_experience',
                    'cu_dob', 'initial_ctc', 'current_ctc', 'cost_centre', 'updated_cost_centre',
                    'branch_name', 'uan_no', 'employee_voluntary_provident_fund_contribution',
                    'contributing_towards_pension_scheme',
                    'provident_trust_fund', 'pf_trust_code', 'pf_description', 'emp_pension_no', 'pension_trust_id',
                    'is_flexi_hour',
                    'has_pf', 'has_esi', 'esi_dispensary', 'esi_sub_type', 'attendance_type', 'care_of', 'country_key',
                    'city', 'district',
                    'retirement_date', 'wbs_element', 'work_schedule_rule', 'time_management_status', 'ptax_sub_type',
                    'source', 'source_name', 'file_no'
                )

                username = role_details[0]['cu_user__username'] if role_details[0]['cu_user__username'] else None
                first_name = role_details[0]['cu_user__first_name'] if role_details[0]['cu_user__first_name'] else ''
                last_name = role_details[0]['cu_user__last_name'] if role_details[0]['cu_user__last_name'] else ''
                employee_name = first_name + ' ' + last_name

                reporting_head__first_name = role_details[0]['reporting_head__first_name'] if role_details[0][
                    'reporting_head__first_name'] else ''
                reporting_head__last_name = role_details[0]['reporting_head__last_name'] if role_details[0][
                    'reporting_head__last_name'] else ''
                reporting_head = reporting_head__first_name + " " + reporting_head__last_name

                hod__first_name = role_details[0]['hod__first_name'] if role_details[0]['hod__first_name'] else ''
                hod__last_name = role_details[0]['hod__last_name'] if role_details[0]['hod__last_name'] else ''
                hod_name = hod__first_name + " " + hod__last_name

                joining_date = role_details[0]['joining_date'] if role_details[0]['joining_date'] else ''
                emp_code = role_details[0]['cu_emp_code'] if role_details[0]['cu_emp_code'] else ''
                sap_personnel_no = role_details[0]['sap_personnel_no'] if role_details[0]['sap_personnel_no'] else ''
                punch_id = role_details[0]['cu_punch_id'] if role_details[0]['cu_punch_id'] else ''

                company_name = role_details[0]['company__coc_name'] if role_details[0]['company__coc_name'] else ''
                department_name = role_details[0]['department__cd_name'] if role_details[0][
                    'department__cd_name'] else ''
                designation_name = role_details[0]['designation__cod_name'] if role_details[0][
                    'designation__cod_name'] else ''

                official_contact_no = role_details[0]['cu_alt_phone_no'] if role_details[0]['cu_alt_phone_no'] else ''
                official_email_id = role_details[0]['cu_alt_email_id'] if role_details[0]['cu_alt_email_id'] else ''
                user_type = role_details[0]['user_type'] if role_details[0]['user_type'] else ''
                job_location = role_details[0]['job_location'] if role_details[0]['job_location'] else ''
                job_location_state = role_details[0]['job_location_state__cs_state_name'] if role_details[0][
                    'job_location_state'] else ''
                salary_per_month = role_details[0]['salary_per_month'] if role_details[0]['salary_per_month'] else ''
                vpf_no = role_details[0]['vpf_no'] if role_details[0]['vpf_no'] else 'No'
                pf_no = role_details[0]['pf_no'] if role_details[0]['pf_no'] else 'No'
                esic_no = role_details[0]['esic_no'] if role_details[0]['esic_no'] else 'No'
                is_confirm = role_details[0]['is_confirm'] if role_details[0]['is_confirm'] else False
                salary_type = role_details[0]['salary_type__st_name'] if role_details[0]['salary_type__st_name'] else ''
                grade = role_details[0]['employee_grade__cg_name'] if role_details[0]['employee_grade__cg_name'] else ''
                gender = role_details[0]['cu_gender'] if role_details[0]['cu_gender'] else ''
                address = role_details[0]['address'] if role_details[0]['address'] else ''
                state = role_details[0]['state__cs_state_name'] if role_details[0]['state'] else ''
                pincode = role_details[0]['pincode'] if role_details[0]['pincode'] else ''
                emergency_relationship = role_details[0]['emergency_relationship'] if role_details[0][
                    'emergency_relationship'] else ''
                emergency_contact_no = role_details[0]['emergency_contact_no'] if role_details[0][
                    'emergency_contact_no'] else ''
                emergency_contact_name = role_details[0]['emergency_contact_name'] if role_details[0][
                    'emergency_contact_name'] else ''
                pan_no = role_details[0]['pan_no'] if role_details[0]['pan_no'] else ''
                aadhar_no = role_details[0]['aadhar_no'] if role_details[0]['aadhar_no'] else ''
                father_name = role_details[0]['father_name'] if role_details[0]['father_name'] else ''
                marital_status = role_details[0]['marital_status'] if role_details[0]['marital_status'] else ''
                personal_email_id = role_details[0]['cu_user__email'] if role_details[0]['cu_user__email'] else ''
                bank_name = role_details[0]['bank_name_p__name'] if role_details[0]['bank_name_p'] else ''
                bank_account = role_details[0]['bank_account'] if role_details[0]['bank_account'] else ''
                ifsc_code = role_details[0]['ifsc_code'] if role_details[0]['ifsc_code'] else ''
                blood_group = role_details[0]['blood_group'] if role_details[0]['blood_group'] else ''
                bus_facility = role_details[0]['bus_facility'] if role_details[0]['bus_facility'] else ''
                highest_qualification = role_details[0]['highest_qualification'] if role_details[0][
                    'highest_qualification'] else ''
                previous_employer = role_details[0]['previous_employer'] if role_details[0]['previous_employer'] else ''
                total_experience = role_details[0]['total_experience'] if role_details[0]['total_experience'] else ''

                dob = role_details[0]['cu_dob'] if role_details[0]['cu_dob'] else ''
                initial_ctc = role_details[0]['initial_ctc'] if role_details[0]['initial_ctc'] else ''
                current_ctc = role_details[0]['current_ctc'] if role_details[0]['current_ctc'] else ''
                # cost_centre = role_details[0]['cost_centre'] if role_details[0]['cost_centre'] else ''
                branch_name = role_details[0]['branch_name'] if role_details[0]['branch_name'] else ''
                uan_no = role_details[0]['uan_no'] if role_details[0]['uan_no'] else ''
                employee_voluntary_provident_fund_contribution = role_details[0][
                    'employee_voluntary_provident_fund_contribution'] \
                    if role_details[0]['employee_voluntary_provident_fund_contribution'] else ''
                contributing_towards_pension_scheme = role_details[0]['contributing_towards_pension_scheme'] if \
                    role_details[0]['contributing_towards_pension_scheme'] else ''
                provident_trust_fund = role_details[0]['provident_trust_fund'] if role_details[0][
                    'provident_trust_fund'] else ''
                pf_trust_code = role_details[0]['pf_trust_code'] if role_details[0]['pf_trust_code'] else ''
                pf_description = role_details[0]['pf_description'] if role_details[0]['pf_description'] else ''
                emp_pension_no = role_details[0]['emp_pension_no'] if role_details[0]['emp_pension_no'] else ''
                pension_trust_id = role_details[0]['pension_trust_id'] if role_details[0]['pension_trust_id'] else ''
                is_flexi_hour = role_details[0]['is_flexi_hour'] if role_details[0]['is_flexi_hour'] else ''
                has_pf = role_details[0]['has_pf'] if role_details[0]['has_pf'] else ''
                has_esi = role_details[0]['has_esi'] if role_details[0]['has_esi'] else ''
                esi_dispensary = role_details[0]['esi_dispensary'] if role_details[0]['esi_dispensary'] else ''
                esi_sub_type = role_details[0]['esi_sub_type'] if role_details[0]['esi_sub_type'] else ''
                attendance_type = role_details[0]['attendance_type'] if role_details[0]['attendance_type'] else ''
                care_of = role_details[0]['care_of'] if role_details[0]['care_of'] else ''
                country_key = role_details[0]['country_key'] if role_details[0]['country_key'] else ''
                city = role_details[0]['city'] if role_details[0]['city'] else ''

                district = role_details[0]['district'] if role_details[0]['district'] else ''
                retirement_date = role_details[0]['retirement_date'] if role_details[0]['retirement_date'] else ''
                wbs_element = role_details[0]['wbs_element'] if role_details[0]['wbs_element'] else ''
                work_schedule_rule = role_details[0]['work_schedule_rule'] if role_details[0][
                    'work_schedule_rule'] else ''
                time_management_status = role_details[0]['time_management_status'] if role_details[0][
                    'time_management_status'] else ''
                ptax_sub_type = role_details[0]['ptax_sub_type'] if role_details[0]['ptax_sub_type'] else ''
                file_no = role_details[0]['file_no'] if role_details[0]['file_no'] else ''

                source = role_details[0]['source'] if role_details[0]['source'] else ''
                source_name = role_details[0]['source_name'] if role_details[0]['source_name'] else ''

                if role_details[0]['updated_cost_centre']:
                    cc_obj = TCoreCompanyCostCentre.objects.filter(id=role_details[0]['updated_cost_centre'])
                    if cc_obj:
                        cost_centre = cc_obj[0].cost_centre_name
                    else:
                        cost_centre = role_details[0]['cost_centre'] if role_details[0][
                            'cost_centre'] else None
                elif role_details[0]['cost_centre']:
                    cost_centre = role_details[0]['cost_centre'] if role_details[0][
                        'cost_centre'] else None
                else:
                    cost_centre = None

                if role_details[0]['employee_sub_grade']:
                    sub_grade = TCoreSubGrade.objects.get(id=role_details[0]['employee_sub_grade'])
                    employee_sub_grade = sub_grade.name
                    employee_sub_grade_id = sub_grade.id
                else:
                    employee_sub_grade = ""
                    employee_sub_grade_id = ""

                # employee other document list
                personal_documents = HrmsDynamicSectionFieldLabelDetailsWithDoc.objects.filter(user=data['id'],
                                                                                               is_deleted=False,
                                                                                               field_label="Other Documents")

                document_str = ''
                count_doc = 1
                if personal_documents:
                    other_documents_list = []
                    for doc_details in personal_documents:
                        if (doc_details.tab_name).lower() == "personal":

                            if doc_details.__dict__['document_name'] == "":
                                doc_name = ""
                            else:
                                doc_name = doc_details.document_name

                            if doc_details.field_label == "Other Documents":
                                field_label_value = str(
                                    doc_details.field_label_value) if doc_details.field_label_value else ''

                                document_str = str(document_str) + str(count_doc) + '.' + "name:" + str(
                                    doc_name) + ',' + "number:" + str(field_label_value) + ', '
                        count_doc = count_doc + 1


                else:
                    document_str = document_str
                other_documents_list = []
                if personal_documents:
                    for doc_details in personal_documents:
                        if (doc_details.tab_name).lower() == "personal":
                            if doc_details.__dict__['document'] == "":
                                file_url = ''
                            else:
                                file_url = request.build_absolute_uri(doc_details.document.url)

                            if doc_details.__dict__['document_name'] == "":
                                doc_name = ""
                            else:
                                doc_name = doc_details.document_name

                            if doc_details.field_label == "Other Documents":
                                other_documents_dict = {
                                    'id': doc_details.id,
                                    'field_label_value': doc_details.field_label_value if doc_details.field_label_value else None,
                                    'document_name': doc_name,
                                    'document': file_url
                                }
                                other_documents_list.append(other_documents_dict)

                data['other_documents'] = other_documents_list
                data['username'] = username
                data['first_name'] = first_name
                data['last_name'] = last_name
                data['reporting_head'] = reporting_head
                data['hod_name'] = hod_name
                data['joining_date'] = joining_date
                data['emp_code'] = emp_code
                data['sap_personnel_no'] = sap_personnel_no
                data['punch_id'] = punch_id
                data['company_name'] = company_name
                data['department_name'] = department_name
                data['designation_name'] = designation_name
                data['official_contact_no'] = official_contact_no
                data['official_email_id'] = official_email_id
                data['user_type'] = user_type
                data['is_confirm'] = is_confirm
                data['salary_type'] = salary_type
                data['grade'] = grade
                data['sub_grade'] = employee_sub_grade
                data['sub_grade_id'] = employee_sub_grade_id
                data['job_location'] = job_location
                data['job_location_state'] = job_location_state
                data['salary_per_month'] = salary_per_month
                data['vpf_no'] = vpf_no
                data['pf_no'] = pf_no
                data['esic_no'] = esic_no
                data['gender'] = gender
                data['address'] = address
                data['state'] = state
                data['pincode'] = pincode
                data['emergency_relationship'] = emergency_relationship
                data['emergency_contact_no'] = emergency_contact_no
                data['emergency_contact_name'] = emergency_contact_name
                data['pan_no'] = pan_no
                data['aadhar_no'] = aadhar_no
                data['father_name'] = father_name
                data['marital_status'] = marital_status
                data['personal_email_id'] = personal_email_id
                data['bank_name'] = bank_name
                data['bank_account'] = bank_account
                data['ifsc_code'] = ifsc_code
                data['blood_group'] = blood_group
                data['bus_facility'] = bus_facility
                data['highest_qualification'] = highest_qualification
                data['previous_employer'] = previous_employer
                data['total_experience'] = total_experience
                data['dob'] = dob
                data['initial_ctc'] = initial_ctc
                data['current_ctc'] = current_ctc
                data['cost_centre'] = cost_centre
                data['branch_name'] = branch_name
                data['uan_no'] = uan_no
                data['employee_voluntary_provident_fund_contribution'] = employee_voluntary_provident_fund_contribution
                data['contributing_towards_pension_scheme'] = contributing_towards_pension_scheme
                data['provident_trust_fund'] = provident_trust_fund
                data['pf_trust_code'] = pf_trust_code
                data['pf_description'] = pf_description
                data['emp_pension_no'] = emp_pension_no
                data['pension_trust_id'] = pension_trust_id
                data['is_flexi_hour'] = is_flexi_hour
                data['has_pf'] = has_pf
                data['has_esi'] = has_esi
                data['esi_dispensary'] = esi_dispensary
                data['esi_sub_type'] = esi_sub_type
                data['attendance_type'] = attendance_type
                data['care_of'] = care_of
                data['country_key'] = country_key
                data['city'] = city
                data['district'] = district
                data['retirement_date'] = retirement_date
                data['wbs_element'] = wbs_element
                data['work_schedule_rule'] = work_schedule_rule
                data['time_management_status'] = time_management_status
                data['ptax_sub_type'] = ptax_sub_type
                data['source'] = source
                data['source_name'] = source_name
                data['file_no'] = file_no
                # print("in print data")

                data_list = [username, first_name, last_name, reporting_head, hod_name, joining_date, "'" + emp_code,
                             "'" + sap_personnel_no, "'" + punch_id, company_name, department_name, designation_name,
                             official_contact_no,
                             official_email_id, user_type, is_confirm, salary_type, grade, employee_sub_grade,
                             job_location, job_location_state,
                             salary_per_month,
                             vpf_no, pf_no, esic_no, gender, address, state, pincode, emergency_relationship,
                             emergency_contact_no,
                             emergency_contact_name, pan_no, aadhar_no, father_name, marital_status, personal_email_id,
                             bank_name,
                             bank_account, ifsc_code, blood_group, bus_facility, highest_qualification,
                             previous_employer,
                             total_experience, dob, initial_ctc, current_ctc, cost_centre,
                             branch_name, uan_no, employee_voluntary_provident_fund_contribution,
                             contributing_towards_pension_scheme,
                             provident_trust_fund, pf_trust_code, pf_description, emp_pension_no, pension_trust_id,
                             is_flexi_hour,
                             has_pf, has_esi, esi_dispensary, esi_sub_type, attendance_type, care_of, country_key,
                             city, district,
                             retirement_date, wbs_element, work_schedule_rule, time_management_status, ptax_sub_type,
                             source, source_name, document_str, file_no

                             ]

                # return Response({"status":"success"})
                total_list.append(data_list)

            data_dict = dict()
            field_name = self.request.query_params.get('field_name', None)
            order_by = self.request.query_params.get('order_by', None)

            if 'results' in response.data:
                if field_name and order_by:
                    if field_name == 'company' and order_by == 'asc':
                        response.data['results'] = sorted(response.data['results'], key=lambda i: i['company_name'])
                    if field_name == 'company' and order_by == 'desc':
                        response.data['results'] = sorted(response.data['results'], key=lambda i: i['company_name'],
                                                          reverse=True)
                data_dict = response.data

            else:
                if field_name and order_by:
                    if field_name == 'company' and order_by == 'asc':
                        response.data = sorted(response.data, key=lambda i: i['company_name'])
                    if field_name == 'company' and order_by == 'desc':
                        response.data = sorted(response.data, key=lambda i: i['company_name'], reverse=True)
                data_dict['results'] = response.data

            response.data = data_dict
            return response


class EmployeeInactiveUserListView(generics.ListAPIView):
    '''
        Reason : Get Inactive User List in Excel File
        Author : Rupam Hazra
        Line number:  3449 - 3465
        Date : 10/03/2020
    '''
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = User.objects.filter(is_superuser=False, is_active=False)
    serializer_class = EmployeeListSerializer
    pagination_class = OnOffPagination

    def get_queryset(self):
        '''
            eleminate login user on employee list added by Rupam Hazra Line number 458 - 459
        '''
        login_user = self.request.user.id
        self.queryset = self.queryset.filter(is_active=False)

        sort_field = '-id'
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        department = self.request.query_params.get('department', None)
        designation = self.request.query_params.get('designation', None)
        start_date = self.request.query_params.get('from_date', None)
        end_date = self.request.query_params.get('to_date', None)
        company = self.request.query_params.get('company', None)
        employee = self.request.query_params.get('employee', None)

        filter = dict()
        if company:
            filter['company'] = company

        if employee:
            filter['cu_user__id'] = employee

        if start_date and end_date:
            start_object = datetime.datetime.strptime(start_date, '%Y-%m-%d')
            end_object = datetime.datetime.strptime(end_date, '%Y-%m-%d')
            filter['joining_date__date__gte'] = start_object.date()
            filter['joining_date__date__lte'] = end_object.date()

        if field_name and order_by:
            if field_name == 'username' and order_by == 'asc':
                sort_field = 'username'
            if field_name == 'username' and order_by == 'desc':
                sort_field = '-username'

        if department:
            filter['department_id'] = department
        if designation:
            filter['designation_id'] = designation

        queryset = self.queryset.filter(is_active=False, id__in=(
            TCoreUserDetail.objects.filter(
                ~Q(cu_punch_id='#N/A'), termination_date__isnull=False,
                cu_is_deleted=True, **filter
            ).values_list('cu_user', flat=True))).order_by(sort_field)

        return queryset

    def get_datalist_for_file(self, request, *args, **kwargs):
        self.request.query_params._mutable = True
        self.request.query_params['page'] = 1
        self.request.query_params['page_size'] = 0
        self.request.query_params._mutable = False
        full_response = super(EmployeeInactiveUserListView, self).get(self, request, *args, **kwargs)
        # print('length:', len(full_response.data))

        full_list = list()
        from pandas import DataFrame

        for data in full_response.data:
            role_details = TCoreUserDetail.objects.filter(
                cu_user=data['id'], cu_is_deleted=True
            ).values(
                'cu_user__username', 'cu_user__first_name', 'cu_user__last_name',
                'cu_emp_code', 'cu_alt_phone_no', 'cu_alt_email_id', 'company__id', 'company__coc_name',
                'joining_date', 'hod__id', 'hod__first_name', 'hod__last_name', 'designation__id', 'cu_user__id',
                'designation__cod_name', 'department__id', 'department__cd_name', 'reporting_head__id',
                'reporting_head__first_name', 'reporting_head__last_name', 'employee_grade__cg_name',
                'employee_sub_grade',
                'sap_personnel_no', 'cu_punch_id', 'user_type', 'is_confirm', 'salary_type__st_name', 'bank_name_p',
                'job_location', 'salary_per_month', 'vpf_no', 'pf_no', 'esic_no', 'cu_gender', 'address', 'state',
                'state__cs_state_name', 'pincode', 'emergency_relationship', 'emergency_contact_no',
                'emergency_contact_name',
                'pan_no', 'aadhar_no', 'father_name', 'marital_status', 'cu_user__email', 'bank_account',
                'bank_name_p__name',
                'ifsc_code', 'blood_group', 'bus_facility', 'highest_qualification', 'previous_employer',
                'total_experience',
                'city', 'district', 'source', 'source_name', 'file_no')

            username = role_details[0]['cu_user__username'] if role_details[0]['cu_user__username'] else None
            first_name = role_details[0]['cu_user__first_name'] if role_details[0]['cu_user__first_name'] else ''
            last_name = role_details[0]['cu_user__last_name'] if role_details[0]['cu_user__last_name'] else ''
            employee_name = first_name + ' ' + last_name

            reporting_head__first_name = role_details[0]['reporting_head__first_name'] if role_details[0][
                'reporting_head__first_name'] else ''
            reporting_head__last_name = role_details[0]['reporting_head__last_name'] if role_details[0][
                'reporting_head__last_name'] else ''
            reporting_head = reporting_head__first_name + " " + reporting_head__last_name

            hod__first_name = role_details[0]['hod__first_name'] if role_details[0]['hod__first_name'] else ''
            hod__last_name = role_details[0]['hod__last_name'] if role_details[0]['hod__last_name'] else ''
            hod_name = hod__first_name + " " + hod__last_name

            joining_date = role_details[0]['joining_date'] if role_details[0]['joining_date'] else ''
            emp_code = role_details[0]['cu_emp_code'] if role_details[0]['cu_emp_code'] else ''
            sap_personnel_no = role_details[0]['sap_personnel_no'] if role_details[0]['sap_personnel_no'] else ''
            punch_id = role_details[0]['cu_punch_id'] if role_details[0]['cu_punch_id'] else ''

            company_name = role_details[0]['company__coc_name'] if role_details[0]['company__coc_name'] else ''
            department_name = role_details[0]['department__cd_name'] if role_details[0]['department__cd_name'] else ''
            designation_name = role_details[0]['designation__cod_name'] if role_details[0][
                'designation__cod_name'] else ''

            official_contact_no = role_details[0]['cu_alt_phone_no'] if role_details[0]['cu_alt_phone_no'] else ''
            official_email_id = role_details[0]['cu_alt_email_id'] if role_details[0]['cu_alt_email_id'] else ''
            user_type = role_details[0]['user_type'] if role_details[0]['user_type'] else ''
            job_location = role_details[0]['job_location'] if role_details[0]['job_location'] else ''
            salary_per_month = role_details[0]['salary_per_month'] if role_details[0]['salary_per_month'] else ''
            vpf_no = role_details[0]['vpf_no'] if role_details[0]['vpf_no'] else 'No'
            pf_no = role_details[0]['pf_no'] if role_details[0]['pf_no'] else 'No'
            esic_no = role_details[0]['esic_no'] if role_details[0]['esic_no'] else 'No'
            is_confirm = role_details[0]['is_confirm'] if role_details[0]['is_confirm'] else False
            salary_type = role_details[0]['salary_type__st_name'] if role_details[0]['salary_type__st_name'] else ''
            grade = role_details[0]['employee_grade__cg_name'] if role_details[0]['employee_grade__cg_name'] else ''
            # sub_grade = role_details[0]['employee_sub_grade__name'] if role_details[0]['employee_sub_grade'] else ''
            gender = role_details[0]['cu_gender'] if role_details[0]['cu_gender'] else ''
            address = role_details[0]['address'] if role_details[0]['address'] else ''
            state = role_details[0]['state__cs_state_name'] if role_details[0]['state'] else ''
            pincode = role_details[0]['pincode'] if role_details[0]['pincode'] else ''
            emergency_relationship = role_details[0]['emergency_relationship'] if role_details[0][
                'emergency_relationship'] else ''
            emergency_contact_no = role_details[0]['emergency_contact_no'] if role_details[0][
                'emergency_contact_no'] else ''
            emergency_contact_name = role_details[0]['emergency_contact_name'] if role_details[0][
                'emergency_contact_name'] else ''
            pan_no = role_details[0]['pan_no'] if role_details[0]['pan_no'] else ''
            aadhar_no = role_details[0]['aadhar_no'] if role_details[0]['aadhar_no'] else ''
            father_name = role_details[0]['father_name'] if role_details[0]['father_name'] else ''
            marital_status = role_details[0]['marital_status'] if role_details[0]['marital_status'] else ''
            personal_email_id = role_details[0]['cu_user__email'] if role_details[0]['cu_user__email'] else ''
            bank_name = role_details[0]['bank_name_p__name'] if role_details[0]['bank_name_p'] else ''
            bank_account = role_details[0]['bank_account'] if role_details[0]['bank_account'] else ''
            ifsc_code = role_details[0]['ifsc_code'] if role_details[0]['ifsc_code'] else ''
            blood_group = role_details[0]['blood_group'] if role_details[0]['blood_group'] else ''
            bus_facility = role_details[0]['bus_facility'] if role_details[0]['bus_facility'] else ''
            highest_qualification = role_details[0]['highest_qualification'] if role_details[0][
                'highest_qualification'] else ''
            previous_employer = role_details[0]['previous_employer'] if role_details[0]['previous_employer'] else ''
            total_experience = role_details[0]['total_experience'] if role_details[0]['total_experience'] else ''
            file_no = role_details[0]['file_no'] if role_details[0]['file_no'] else ''

            city = role_details[0]['city'] if role_details[0]['city'] else ''
            district = role_details[0]['district'] if role_details[0]['district'] else ''
            source = role_details[0]['source'] if role_details[0]['source'] else ''
            source_name = role_details[0]['source_name'] if role_details[0]['source_name'] else ''
            if role_details[0]['employee_sub_grade']:
                sub_grade = TCoreSubGrade.objects.get(id=role_details[0]['employee_sub_grade'])
                employee_sub_grade = sub_grade.name
                employee_sub_grade_id = sub_grade.id
            else:
                employee_sub_grade = ""
                employee_sub_grade_id = ""
            personal_documents = HrmsDynamicSectionFieldLabelDetailsWithDoc.objects.filter(user=data['id'],
                                                                                           is_deleted=False,
                                                                                           field_label="Other Documents")
            # print(personal_documents)
            document_str = ''
            count_doc = 1
            if personal_documents:
                other_documents_list = []
                for doc_details in personal_documents:
                    if (doc_details.tab_name).lower() == "personal":

                        if doc_details.__dict__['document_name'] == "":
                            doc_name = ""
                        else:
                            doc_name = doc_details.document_name

                        if doc_details.field_label == "Other Documents":
                            field_label_value = str(
                                doc_details.field_label_value) if doc_details.field_label_value else ''

                            document_str = str(document_str) + str(count_doc) + '.' + "name:" + str(
                                doc_name) + ',' + "number:" + str(field_label_value) + ', '
                    count_doc = count_doc + 1


            else:
                document_str = document_str

            data['other_documents'] = document_str

            data['username'] = username
            data['first_name'] = first_name
            data['last_name'] = last_name
            data['reporting_head'] = reporting_head
            data['hod_name'] = hod_name
            data['joining_date'] = joining_date
            data['emp_code'] = emp_code
            data['sap_personnel_no'] = sap_personnel_no
            data['punch_id'] = punch_id
            data['company_name'] = company_name
            data['department_name'] = department_name
            data['designation_name'] = designation_name
            data['official_contact_no'] = official_contact_no
            data['official_email_id'] = official_email_id
            data['user_type'] = user_type
            data['is_confirm'] = is_confirm
            data['salary_type'] = salary_type
            data['grade'] = grade
            data['sub_grade'] = employee_sub_grade
            data['sub_grade_id'] = employee_sub_grade_id
            data['job_location'] = job_location
            data['salary_per_month'] = salary_per_month
            data['vpf_no'] = vpf_no
            data['pf_no'] = pf_no
            data['esic_no'] = esic_no
            data['gender'] = gender
            data['address'] = address
            data['state'] = state
            data['pincode'] = pincode
            data['emergency_relationship'] = emergency_relationship
            data['emergency_contact_no'] = emergency_contact_no
            data['emergency_contact_name'] = emergency_contact_name
            data['pan_no'] = pan_no
            data['aadhar_no'] = aadhar_no
            data['father_name'] = father_name
            data['marital_status'] = marital_status
            data['personal_email_id'] = personal_email_id
            data['bank_name'] = bank_name
            data['bank_account'] = bank_account
            data['ifsc_code'] = ifsc_code
            data['blood_group'] = blood_group
            data['bus_facility'] = bus_facility
            data['highest_qualification'] = highest_qualification
            data['previous_employer'] = previous_employer
            data['total_experience'] = total_experience

            data['city'] = city
            data['district'] = district
            data['source'] = source
            data['source_name'] = source_name
            data['file_no'] = file_no

            data_list = [username, first_name, last_name, reporting_head, hod_name, joining_date, "'" + emp_code,
                         "'" + sap_personnel_no, "'" + punch_id, company_name, department_name, designation_name,
                         official_contact_no,
                         official_email_id, user_type, is_confirm, salary_type, grade, employee_sub_grade, job_location,
                         salary_per_month,
                         vpf_no, pf_no, esic_no, gender, address, state, pincode, emergency_relationship,
                         emergency_contact_no,
                         emergency_contact_name, pan_no, aadhar_no, father_name, marital_status, personal_email_id,
                         bank_name,
                         bank_account, ifsc_code, blood_group, bus_facility, highest_qualification, previous_employer,
                         total_experience, city, district, source, source_name, document_str, file_no
                         ]

            # return Response({"status":"success"})
            full_list.append(data_list)

        return full_list

    @response_modify_decorator_list_or_get_after_execution_for_onoff_pagination
    def get(self, request, *args, **kwargs):
        response = super(EmployeeInactiveUserListView, self).get(self, request, args, kwargs)

        export_download = self.request.query_params.get('export_download', None)
        if export_download == 'yes':
            full_list = self.get_datalist_for_file(request, *args, **kwargs)
            response.data = list()
            from pandas import DataFrame
            file_name = ''
            if full_list:
                if os.path.isdir('media/attendance/inactive_users_report/document'):
                    file_name = 'media/attendance/inactive_users_report/document/inactive_users_report.xlsx'
                else:
                    os.makedirs('media/attendance/inactive_users_report/document')
                    file_name = 'media/attendance/inactive_users_report/document/inactive_users_report.xlsx'

                df = DataFrame(
                    full_list, columns=[
                        'Username', 'First Name', 'Last Name', 'Reporting Head',
                        'HOD', 'Joining Date', 'Emp code', 'SAP', 'Punch Id', 'Company',
                        'Department', 'Designation', 'Contact No', 'Email Id', 'User Type',
                        'Is Confirm', 'Salary Type', 'Grade', 'Sub Grade', 'Job Location', 'Salary Per Month', 'VPF',
                        'PF', 'ESI',
                        'Gender', 'Address', 'State', 'Pincode', 'Emergency Relationship', 'Emergency Contact No',
                        'Emergency Contact Name', 'PAN No.', 'Adhhar No.', "Father's name",
                        'Maritial Status', 'Personal Email', 'Bank Name', 'Bank A/C', 'IFSC', 'Blood Gr.',
                        'Bus Facility',
                        'Highest Qualification', 'Previous Employer', 'Total Exp.', 'City', 'District', 'Source',
                        'Source Name', 'Others Document', 'File No'
                    ]
                )
                export_csv = df.to_excel(file_name, index=None, header=True)

            if request.is_secure():
                protocol = 'https://'
            else:
                protocol = 'http://'

            url = getHostWithPort(request) + file_name if file_name else None

            data_dict = dict()
            data_dict['results'] = response.data
            data_dict['url'] = url
            response.data = data_dict
            return response


        else:
            if 'results' in response.data:
                response_s = response.data['results']
            else:
                response_s = response.data

            # print('response check::::::::::::::',response_s)
            list_type = self.request.query_params.get('list_type', None)
            module_id = self.request.query_params.get('module_id', None)
            p_doc_dict = {}
            total_list = list()

            for data in response_s:
                role_details = TCoreUserDetail.objects.filter(
                    cu_user=data['id'], cu_is_deleted=True
                ).values(
                    'cu_user__username', 'cu_user__first_name', 'cu_user__last_name',
                    'cu_emp_code', 'cu_alt_phone_no', 'cu_alt_email_id', 'company__id', 'company__coc_name',
                    'joining_date', 'hod__id', 'hod__first_name', 'hod__last_name', 'designation__id', 'cu_user__id',
                    'designation__cod_name', 'department__id', 'department__cd_name', 'reporting_head__id',
                    'reporting_head__first_name', 'reporting_head__last_name', 'employee_grade__cg_name',
                    'employee_sub_grade',
                    'sap_personnel_no', 'cu_punch_id', 'user_type', 'is_confirm', 'salary_type__st_name', 'bank_name_p',
                    'job_location', 'salary_per_month', 'vpf_no', 'pf_no', 'esic_no', 'cu_gender', 'address', 'state',
                    'state__cs_state_name', 'pincode', 'emergency_relationship', 'emergency_contact_no',
                    'emergency_contact_name',
                    'pan_no', 'aadhar_no', 'father_name', 'marital_status', 'cu_user__email', 'bank_account',
                    'bank_name_p__name',
                    'ifsc_code', 'blood_group', 'bus_facility', 'highest_qualification', 'previous_employer',
                    'total_experience',
                    'city', 'district', 'source', 'source_name', 'file_no')

                username = role_details[0]['cu_user__username'] if role_details[0]['cu_user__username'] else None
                file_no = role_details[0]['file_no'] if role_details[0]['file_no'] else None
                first_name = role_details[0]['cu_user__first_name'] if role_details[0]['cu_user__first_name'] else ''
                last_name = role_details[0]['cu_user__last_name'] if role_details[0]['cu_user__last_name'] else ''
                employee_name = first_name + ' ' + last_name

                reporting_head__first_name = role_details[0]['reporting_head__first_name'] if role_details[0][
                    'reporting_head__first_name'] else ''
                reporting_head__last_name = role_details[0]['reporting_head__last_name'] if role_details[0][
                    'reporting_head__last_name'] else ''
                reporting_head = reporting_head__first_name + " " + reporting_head__last_name

                hod__first_name = role_details[0]['hod__first_name'] if role_details[0]['hod__first_name'] else ''
                hod__last_name = role_details[0]['hod__last_name'] if role_details[0]['hod__last_name'] else ''
                hod_name = hod__first_name + " " + hod__last_name

                joining_date = role_details[0]['joining_date'] if role_details[0]['joining_date'] else ''
                emp_code = role_details[0]['cu_emp_code'] if role_details[0]['cu_emp_code'] else ''
                sap_personnel_no = role_details[0]['sap_personnel_no'] if role_details[0]['sap_personnel_no'] else ''
                punch_id = role_details[0]['cu_punch_id'] if role_details[0]['cu_punch_id'] else ''

                company_name = role_details[0]['company__coc_name'] if role_details[0]['company__coc_name'] else ''
                department_name = role_details[0]['department__cd_name'] if role_details[0][
                    'department__cd_name'] else ''
                designation_name = role_details[0]['designation__cod_name'] if role_details[0][
                    'designation__cod_name'] else ''

                official_contact_no = role_details[0]['cu_alt_phone_no'] if role_details[0]['cu_alt_phone_no'] else ''
                official_email_id = role_details[0]['cu_alt_email_id'] if role_details[0]['cu_alt_email_id'] else ''
                user_type = role_details[0]['user_type'] if role_details[0]['user_type'] else ''
                job_location = role_details[0]['job_location'] if role_details[0]['job_location'] else ''
                salary_per_month = role_details[0]['salary_per_month'] if role_details[0]['salary_per_month'] else ''
                vpf_no = role_details[0]['vpf_no'] if role_details[0]['vpf_no'] else 'No'
                pf_no = role_details[0]['pf_no'] if role_details[0]['pf_no'] else 'No'
                esic_no = role_details[0]['esic_no'] if role_details[0]['esic_no'] else 'No'
                is_confirm = role_details[0]['is_confirm'] if role_details[0]['is_confirm'] else False
                salary_type = role_details[0]['salary_type__st_name'] if role_details[0]['salary_type__st_name'] else ''
                grade = role_details[0]['employee_grade__cg_name'] if role_details[0]['employee_grade__cg_name'] else ''
                # sub_grade = role_details[0]['employee_sub_grade__name'] if role_details[0]['employee_sub_grade'] else ''
                gender = role_details[0]['cu_gender'] if role_details[0]['cu_gender'] else ''
                address = role_details[0]['address'] if role_details[0]['address'] else ''
                state = role_details[0]['state__cs_state_name'] if role_details[0]['state'] else ''
                pincode = role_details[0]['pincode'] if role_details[0]['pincode'] else ''
                emergency_relationship = role_details[0]['emergency_relationship'] if role_details[0][
                    'emergency_relationship'] else ''
                emergency_contact_no = role_details[0]['emergency_contact_no'] if role_details[0][
                    'emergency_contact_no'] else ''
                emergency_contact_name = role_details[0]['emergency_contact_name'] if role_details[0][
                    'emergency_contact_name'] else ''
                pan_no = role_details[0]['pan_no'] if role_details[0]['pan_no'] else ''
                aadhar_no = role_details[0]['aadhar_no'] if role_details[0]['aadhar_no'] else ''
                father_name = role_details[0]['father_name'] if role_details[0]['father_name'] else ''
                marital_status = role_details[0]['marital_status'] if role_details[0]['marital_status'] else ''
                personal_email_id = role_details[0]['cu_user__email'] if role_details[0]['cu_user__email'] else ''
                bank_name = role_details[0]['bank_name_p__name'] if role_details[0]['bank_name_p'] else ''
                bank_account = role_details[0]['bank_account'] if role_details[0]['bank_account'] else ''
                ifsc_code = role_details[0]['ifsc_code'] if role_details[0]['ifsc_code'] else ''
                blood_group = role_details[0]['blood_group'] if role_details[0]['blood_group'] else ''
                bus_facility = role_details[0]['bus_facility'] if role_details[0]['bus_facility'] else ''
                highest_qualification = role_details[0]['highest_qualification'] if role_details[0][
                    'highest_qualification'] else ''
                previous_employer = role_details[0]['previous_employer'] if role_details[0]['previous_employer'] else ''
                total_experience = role_details[0]['total_experience'] if role_details[0]['total_experience'] else ''

                city = role_details[0]['city'] if role_details[0]['city'] else ''
                district = role_details[0]['district'] if role_details[0]['district'] else ''
                source = role_details[0]['source'] if role_details[0]['source'] else ''
                source_name = role_details[0]['source_name'] if role_details[0]['source_name'] else ''
                if role_details[0]['employee_sub_grade']:
                    sub_grade = TCoreSubGrade.objects.get(id=role_details[0]['employee_sub_grade'])
                    employee_sub_grade = sub_grade.name
                    employee_sub_grade_id = sub_grade.id
                else:
                    employee_sub_grade = ""
                    employee_sub_grade_id = ""
                personal_documents = HrmsDynamicSectionFieldLabelDetailsWithDoc.objects.filter(user=data['id'],
                                                                                               is_deleted=False,
                                                                                               field_label="Other Documents")
                # print(personal_documents)
                document_str = ''
                count_doc = 1
                if personal_documents:
                    other_documents_list = []
                    for doc_details in personal_documents:
                        if (doc_details.tab_name).lower() == "personal":

                            if doc_details.__dict__['document_name'] == "":
                                doc_name = ""
                            else:
                                doc_name = doc_details.document_name

                            if doc_details.field_label == "Other Documents":
                                field_label_value = str(
                                    doc_details.field_label_value) if doc_details.field_label_value else ''

                                document_str = str(document_str) + str(count_doc) + '.' + "name:" + str(
                                    doc_name) + ',' + "number:" + str(field_label_value) + ', '
                        count_doc = count_doc + 1


                else:
                    document_str = document_str
                other_documents_list = []
                if personal_documents:
                    for doc_details in personal_documents:
                        if (doc_details.tab_name).lower() == "personal":
                            if doc_details.__dict__['document'] == "":
                                file_url = ''
                            else:
                                file_url = request.build_absolute_uri(doc_details.document.url)

                            if doc_details.__dict__['document_name'] == "":
                                doc_name = ""
                            else:
                                doc_name = doc_details.document_name

                            if doc_details.field_label == "Other Documents":
                                other_documents_dict = {
                                    'id': doc_details.id,
                                    'field_label_value': doc_details.field_label_value if doc_details.field_label_value else None,
                                    'document_name': doc_name,
                                    'document': file_url
                                }
                                other_documents_list.append(other_documents_dict)

                data['other_documents'] = other_documents_list

                data['username'] = username
                data['first_name'] = first_name
                data['last_name'] = last_name
                data['reporting_head'] = reporting_head
                data['hod_name'] = hod_name
                data['joining_date'] = joining_date
                data['emp_code'] = emp_code
                data['sap_personnel_no'] = sap_personnel_no
                data['punch_id'] = punch_id
                data['company_name'] = company_name
                data['department_name'] = department_name
                data['designation_name'] = designation_name
                data['official_contact_no'] = official_contact_no
                data['official_email_id'] = official_email_id
                data['user_type'] = user_type
                data['is_confirm'] = is_confirm
                data['salary_type'] = salary_type
                data['grade'] = grade
                data['sub_grade'] = employee_sub_grade
                data['sub_grade_id'] = employee_sub_grade_id
                data['job_location'] = job_location
                data['salary_per_month'] = salary_per_month
                data['vpf_no'] = vpf_no
                data['pf_no'] = pf_no
                data['esic_no'] = esic_no
                data['gender'] = gender
                data['address'] = address
                data['state'] = state
                data['pincode'] = pincode
                data['emergency_relationship'] = emergency_relationship
                data['emergency_contact_no'] = emergency_contact_no
                data['emergency_contact_name'] = emergency_contact_name
                data['pan_no'] = pan_no
                data['aadhar_no'] = aadhar_no
                data['father_name'] = father_name
                data['marital_status'] = marital_status
                data['personal_email_id'] = personal_email_id
                data['bank_name'] = bank_name
                data['bank_account'] = bank_account
                data['ifsc_code'] = ifsc_code
                data['blood_group'] = blood_group
                data['bus_facility'] = bus_facility
                data['highest_qualification'] = highest_qualification
                data['previous_employer'] = previous_employer
                data['total_experience'] = total_experience

                data['city'] = city
                data['district'] = district
                data['source'] = source
                data['source_name'] = source_name
                data['file_no'] = file_no

                data_list = [username, first_name, last_name, reporting_head, hod_name, joining_date, "'" + emp_code,
                             "'" + sap_personnel_no, "'" + punch_id, company_name, department_name, designation_name,
                             official_contact_no,
                             official_email_id, user_type, is_confirm, salary_type, grade, employee_sub_grade,
                             job_location, salary_per_month,
                             vpf_no, pf_no, esic_no, gender, address, state, pincode, emergency_relationship,
                             emergency_contact_no,
                             emergency_contact_name, pan_no, aadhar_no, father_name, marital_status, personal_email_id,
                             bank_name,
                             bank_account, ifsc_code, blood_group, bus_facility, highest_qualification,
                             previous_employer,
                             total_experience, city, district, source, source_name, document_str, file_no
                             ]

                # return Response({"status":"success"})
                total_list.append(data_list)

            data_dict = dict()

            field_name = self.request.query_params.get('field_name', None)
            order_by = self.request.query_params.get('order_by', None)

            if 'results' in response.data:
                if field_name and order_by:
                    if field_name == 'company' and order_by == 'asc':
                        response.data['results'] = sorted(response.data['results'], key=lambda i: i['company_name'])
                    if field_name == 'company' and order_by == 'desc':
                        response.data['results'] = sorted(response.data['results'], key=lambda i: i['company_name'],
                                                          reverse=True)
                data_dict = response.data

            else:
                if field_name and order_by:
                    if field_name == 'company' and order_by == 'asc':
                        response.data = sorted(response.data, key=lambda i: i['company_name'])
                    if field_name == 'company' and order_by == 'desc':
                        response.data = sorted(response.data, key=lambda i: i['company_name'], reverse=True)
                data_dict['results'] = response.data

            response.data = data_dict
            return response


'''
    FOR NEW RULES & REGULATION IN ATTENDENCE SYSTEM FOR FINANCIAL YEAR [2020-2021]
    Author : Rupam Hazra
    Implementaion Starting Date : 17.03.2020
'''


class EmployeeAddV2View(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = User.objects.all()
    serializer_class = EmployeeAddV2Serializer

    def post(self, request, *args, **kwargs):
        # print('check post...',request.data)
        # username = request.data['username']
        # if User.objects.filter(username=username).count() > 0:
        #     custom_exception_message(self,'Employee Login ID')

        # cu_emp_code = request.data['cu_emp_code']
        # if TCoreUserDetail.objects.filter(cu_emp_code=cu_emp_code).count() > 0:
        #     custom_exception_message(self,'Employee Code')
        rejoin_status = request.data['is_rejoin'] if 'is_rejoin' in request.data else ''
        if not rejoin_status:
            cu_phone_no = request.data['cu_phone_no']
            if TCoreUserDetail.objects.filter(cu_phone_no=cu_phone_no).count() > 0:
                custom_exception_message(self, 'Personal Contact No. ')

        # print('sap_personnel_no',sap_personnel_no,type(sap_personnel_no))
        # Added By RUpam Hazra request in form data type
        sap_personnel_no = request.data['sap_personnel_no']
        if sap_personnel_no != 'null':
            if TCoreUserDetail.objects.filter(sap_personnel_no=sap_personnel_no).count() > 0:
                custom_exception_message(self, 'SAP Personnel ID')

        cu_punch_id = request.data['cu_punch_id'] if request.data['cu_punch_id'] else None
        if TCoreUserDetail.objects.filter(cu_punch_id=cu_punch_id).count() > 0:
            custom_exception_message(self, 'Punching Machine Id')

        return super().post(request, *args, **kwargs)


class EmployeeLeaveAllocateV2View(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = User.objects.all()
    serializer_class = EmployeeLeaveAllocateV2Serializer


# employee active user list version2 view


class EmployeeActiveUserListV2View(generics.ListAPIView):
    '''
        Reason : Get Active User List in Excel File
        Author :Swarup Adhikary
        Line number:  3449 - 3465
        Date : 22/04/2020
    '''
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreUserDetail.objects.filter(cu_user__is_superuser=False, cu_user__is_active=True)
    serializer_class = EmployeeListSerializerv2
    pagination_class = OnOffPagination

    def get_queryset(self):
        '''
            eleminate login user on employee list added by Rupam Hazra Line number 458 - 459
        '''
        login_user = self.request.user.id
        self.queryset = self.queryset.filter(cu_user__is_active=True)

        sort_field = '-id'
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        department = self.request.query_params.get('department', None)
        designation = self.request.query_params.get('designation', None)
        start_date = self.request.query_params.get('from_date', None)
        end_date = self.request.query_params.get('to_date', None)

        filter = dict()
        if start_date and end_date:
            start_object = datetime.datetime.strptime(start_date, '%Y-%m-%d')
            end_object = datetime.datetime.strptime(end_date, '%Y-%m-%d')
            filter['joining_date__date__gte'] = start_object.date()
            filter['joining_date__date__lte'] = end_object.date()

        if field_name and order_by:
            if field_name == 'username' and order_by == 'asc':
                sort_field = 'username'
            if field_name == 'username' and order_by == 'desc':
                sort_field = '-username'

        if department:
            filter['department_id'] = department
        if designation:
            filter['designation_id'] = designation

        queryset = self.queryset.filter(~Q(cu_punch_id='#N/A'), termination_date__isnull=True, cu_is_deleted=False,
                                        **filter).order_by(sort_field)

        return queryset

    @response_modify_decorator_list_or_get_after_execution_for_onoff_pagination
    def get(self, request, *args, **kwargs):
        response = super(EmployeeActiveUserListV2View, self).get(self, request, args, kwargs)
        data_dict = dict()
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)

        if 'results' in response.data:
            if field_name and order_by:
                if field_name == 'company' and order_by == 'asc':
                    response.data['results'] = sorted(response.data['results'], key=lambda i: i['company_name'])
                if field_name == 'company' and order_by == 'desc':
                    response.data['results'] = sorted(response.data['results'], key=lambda i: i['company_name'],
                                                      reverse=True)
            data_dict = response.data

        else:
            if field_name and order_by:
                if field_name == 'company' and order_by == 'asc':
                    response.data = sorted(response.data, key=lambda i: i['company_name'])
                if field_name == 'company' and order_by == 'desc':
                    response.data = sorted(response.data, key=lambda i: i['company_name'], reverse=True)
            data_dict['results'] = response.data

        response.data = data_dict

        return Response({**response.data, 'request_status': 1, 'msg': settings.MSG_SUCCESS})


# active user list download

class EmployeeActiveUserListDownload(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreUserDetail.objects.filter(cu_user__is_superuser=False, cu_user__is_active=True)
    serializer_class = EmployeeListSerializerv2

    def get_queryset(self):
        '''
            eleminate login user on employee list added by Rupam Hazra Line number 458 - 459
        '''
        login_user = self.request.user.id
        self.queryset = self.queryset.filter(cu_user__is_active=True)

        sort_field = '-id'
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        department = self.request.query_params.get('department', None)
        designation = self.request.query_params.get('designation', None)
        start_date = self.request.query_params.get('from_date', None)
        end_date = self.request.query_params.get('to_date', None)

        filter = dict()
        if start_date and end_date:
            start_object = datetime.datetime.strptime(start_date, '%Y-%m-%d')
            end_object = datetime.datetime.strptime(end_date, '%Y-%m-%d')
            filter['joining_date__date__gte'] = start_object.date()
            filter['joining_date__date__lte'] = end_object.date()

        if field_name and order_by:
            if field_name == 'username' and order_by == 'asc':
                sort_field = 'username'
            if field_name == 'username' and order_by == 'desc':
                sort_field = '-username'

        if department:
            filter['department_id'] = department
        if designation:
            filter['designation_id'] = designation

        queryset = self.queryset.filter(~Q(cu_punch_id='#N/A'), termination_date__isnull=True, cu_is_deleted=False,
                                        **filter).order_by(sort_field)

        return queryset

    def get(self, request, *args, **kwargs):
        response = super(EmployeeActiveUserListDownload, self).get(self, request, args, kwargs)

        if 'results' in response.data:
            # print("in if")
            response_s = response.data['results']
        else:
            # print("in else")
            response_s = response.data

        total_data_list = []
        for data in response_s:
            temp_dict = dict(data)
            a = list(temp_dict.values())
            # print(len(a))
            total_data_list.append(a[1:])

        from pandas import DataFrame
        if os.path.isdir('media/attendance/active_users_report/document'):
            file_name = 'media/attendance/active_users_report/document/active_users_report.xlsx'
            file_path = settings.MEDIA_ROOT_EXPORT + file_name
        else:
            os.makedirs('media/attendance/active_users_report/document')
            file_name = 'media/attendance/active_users_report/document/active_users_report.xlsx'
            file_path = settings.MEDIA_ROOT_EXPORT + file_name

        df = DataFrame(
            total_data_list, columns=[
                'Username', 'password', 'First Name', 'Last Name', 'Reporting Head',
                'HOD', 'Joining Date', 'Emp code', 'SAP', 'Punch Id', 'Company',
                'Department', 'Designation', 'Contact No', 'Email Id', 'User Type',
                'Is Confirm', 'Salary Type', 'Grade', 'Sub Grade', 'Job Location', 'Salary Per Month', 'VPF', 'PF',
                'ESI',
                'Gender', 'Address', 'State', 'Pincode', 'Emergency Relationship', 'Emergency Contact No',
                'Emergency Contact Name', 'PAN No.', 'Adhhar No.', "Father's name",
                'Maritial Status', 'Personal Email', 'Bank Name', 'Bank A/C', 'IFSC', 'Blood Gr.', 'Bus Facility',
                'Highest Qualification', 'Previous Employer', 'Total Exp.'
            ]
        )
        df.to_excel(file_path, index=None, header=True)
        url = getHostWithPort(request) + file_name if file_name else None

        return Response({'download_url': url, 'request_status': 1, 'msg': settings.MSG_SUCCESS})


class EmployeeViewPasswordVerification(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def post(self, request, *args, **kwargs):
        username = request.user.username
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            return Response({'request_status': 1, 'msg': settings.MSG_SUCCESS})
        else:
            return Response({'request_status': 0, 'msg': settings.MSG_ERROR})


class UnAppliedAttendanceListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    serializer_class = UnAppliedAttendanceSerializerv2
    pagination_class = OnOffPagination
    queryset = AttendanceApprovalRequest.objects.filter(
        Q(is_requested=False) 
        & Q(approved_status='regular')
        & Q(is_late_conveyance=False)
        & Q(lock_status=False)
        & Q(is_deleted=False)
        )

    def get_queryset(self):
        from datetime import datetime
        current_date = datetime.now().date()
        queryset = self.queryset
        # print(queryset)
        # month = 5 & year = 2020
        month = self.request.query_params.get('month', None)
        year = self.request.query_params.get('year', None)
        is_previous = self.request.query_params.get('is_previous', None)
        # print(is_previous)
        if is_previous:
            # print("in previous")
            first_day_of_current_month = datetime.today().date().replace(day=1)
            current_date = first_day_of_current_month - timedelta(days=7)
            # print(current_date)

            month_master = AttendenceMonthMaster.objects.filter(month_start__date__lte=current_date,
                                                                month_end__date__gte=current_date,
                                                                is_deleted=False).first()
            # print(month_master.month_start)
        elif month and year:
            # print("in else if")
            month_master = AttendenceMonthMaster.objects.filter(month=month,
                                                                month_end__date__year=year,
                                                                is_deleted=False).first()
            # print(month_master)


        else:

            month_master = AttendenceMonthMaster.objects.filter(month_start__date__lte=current_date,
                                                                month_end__date__gte=current_date,
                                                                is_deleted=False).first()
            # print(month_master.month_start)

        queryset = queryset.filter(
            Q(attendance_date__gte=month_master.month_start) & Q(attendance_date__lte=month_master.month_end))
        # print("queryset is",queryset)

        sort_field = '-id'

        employee_id = self.request.query_params.get('employee_id', None)
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        # approval_atatus = self.request.query_params.get('approval_status', None)
        start_date = self.request.query_params.get('from_date', None)
        end_date = self.request.query_params.get('to_date', None)

        if start_date and end_date:
            start_object = datetime.strptime(start_date, '%Y-%m-%d')
            delta = timedelta(days=1)
            end_object = datetime.strptime(end_date, '%Y-%m-%d')
            queryset = queryset.filter(Q(attendance__date__lte=end_object + delta),
                                       Q(attendance__date__gte=start_object))
        else:
            queryset = queryset

        filter = dict()
        if employee_id:
            # print(employee_id)
            filter['attendance__employee__id'] = employee_id

        if field_name and order_by:
            if field_name == 'attendance_date' and order_by == 'asc':
                sort_field = 'attendance_date'
            if field_name == 'attendance_date' and order_by == 'desc':
                sort_field = '-attendance_date'
            if field_name == 'duration_start' and order_by == 'asc':
                sort_field = 'duration_start'
            if field_name == 'duration_start' and order_by == 'desc':
                sort_field = '-duration_start'
            if field_name == 'duration_end' and order_by == 'asc':
                sort_field = 'duration_end'
            if field_name == 'duration_end' and order_by == 'desc':
                sort_field = '-duration_end'
            if field_name == 'duration' and order_by == 'asc':
                sort_field = 'duration'
            if field_name == 'duration' and order_by == 'desc':
                sort_field = '-duration'

        punch_id_list = ['00444756', 'DEMO1111113', 'DEMO1111112', 'DEMO1111111', '37200008', '11111111']

        queryset1 = queryset.filter(
            ~Q(attendance__employee__cu_user__cu_punch_id='#N/A'),
            (~Q(attendance__employee__cu_user__user_type = 'Director') | Q(attendance__employee__cu_user__user_type__isnull=True)),
            (~Q(attendance__employee__cu_user__attendance_type__in=('PMS','CRM','Manual')) | Q(attendance__employee__cu_user__attendance_type__isnull = True)),
            ~Q(attendance__employee__cu_user__cu_user_id__in=('3183','3184','3185','2647','35','2564')),
            ~Q(attendance__employee__cu_user__sap_personnel_no__in=('37200039','37200065')),
            ~Q(attendance__employee__cu_user__cu_punch_id__in=punch_id_list),
            **filter).order_by(sort_field)


        # print(len(queryset))
        return queryset1

    @response_modify_decorator_list_or_get_after_execution_for_onoff_pagination
    def get(self, request, *args, **kwargs):
        response = super(UnAppliedAttendanceListView, self).get(self, request, args, kwargs)
        return response


# unapproved attendance by swarup(26.12.2020)

class UnAttendedAttendanceListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    serializer_class = UnAppliedAttendanceSerializerv2
    pagination_class = OnOffPagination
    queryset = AttendanceApprovalRequest.objects.filter(
        Q(is_requested=True) &
        Q(approved_status='pending') &
        Q(is_deleted=False) &
        Q(is_late_conveyance=False) &
        Q(lock_status=False)
        )

    def get_queryset(self):
        from datetime import datetime
        current_date = datetime.now().date()
        queryset = self.queryset
        # print(queryset)
        # month = 5 & year = 2020
        month = self.request.query_params.get('month', None)
        year = self.request.query_params.get('year', None)
        is_previous = self.request.query_params.get('is_previous', None)
        # print(is_previous)
        if is_previous:
            # print("in previous")
            first_day_of_current_month = datetime.today().date().replace(day=1)
            current_date = first_day_of_current_month - timedelta(days=7)
            # print(current_date)

            month_master = AttendenceMonthMaster.objects.filter(month_start__date__lte=current_date,
                                                                month_end__date__gte=current_date,
                                                                is_deleted=False).first()
            # print(month_master.month_start)
        elif month and year:
            # print("in else if")
            try:
                month_master = AttendenceMonthMaster.objects.filter(month=month,
                                                                    month_end__date__year=year,
                                                                    is_deleted=False).first()
            except:
                print("in except")
                return AttendanceApprovalRequest.objects.none()

            # print(month_master)


        else:

            month_master = AttendenceMonthMaster.objects.filter(month_start__date__lte=current_date,
                                                                month_end__date__gte=current_date,
                                                                is_deleted=False).first()
            # print(month_master.month_start)
        try:
            queryset = queryset.filter(
                Q(attendance_date__gte=month_master.month_start) & Q(attendance_date__lte=month_master.month_end))
        except:
            return AttendanceApprovalRequest.objects.none()


        # print("queryset is",queryset)

        sort_field = '-id'

        employee_id = self.request.query_params.get('employee_id', None)
        reporting_head_id = self.request.query_params.get('reporting_head_id', None)
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        # approval_atatus = self.request.query_params.get('approval_status', None)
        start_date = self.request.query_params.get('from_date', None)
        end_date = self.request.query_params.get('to_date', None)
        request_type = self.request.query_params.get('request_type', None)
        department = self.request.query_params.get('department', None)

        if reporting_head_id:
            queryset = queryset.filter(Q(attendance__employee__cu_user__reporting_head_id=reporting_head_id))

        if department:
            queryset = queryset.filter(Q(attendance__employee__cu_user__department_id=department))

        if request_type:
            queryset = queryset.filter(Q(request_type=request_type))



        if start_date and end_date:
            start_object = datetime.strptime(start_date, '%Y-%m-%d')
            delta = timedelta(days=1)
            end_object = datetime.strptime(end_date, '%Y-%m-%d')
            queryset = queryset.filter(Q(attendance__date__lte=end_object + delta),
                                       Q(attendance__date__gte=start_object))
        else:
            queryset = queryset

        filter = dict()
        if employee_id:
            # print(employee_id)
            filter['attendance__employee__id'] = employee_id

        if field_name and order_by:
            if field_name == 'attendance_date' and order_by == 'asc':
                sort_field = 'attendance_date'
            if field_name == 'attendance_date' and order_by == 'desc':
                sort_field = '-attendance_date'
            if field_name == 'duration_start' and order_by == 'asc':
                sort_field = 'duration_start'
            if field_name == 'duration_start' and order_by == 'desc':
                sort_field = '-duration_start'
            if field_name == 'duration_end' and order_by == 'asc':
                sort_field = 'duration_end'
            if field_name == 'duration_end' and order_by == 'desc':
                sort_field = '-duration_end'
            if field_name == 'duration' and order_by == 'asc':
                sort_field = 'duration'
            if field_name == 'duration' and order_by == 'desc':
                sort_field = '-duration'

        punch_id_list = ['00444756', 'DEMO1111113', 'DEMO1111112', 'DEMO1111111', '37200008', '11111111']

        queryset1 = queryset.filter(
            ~Q(attendance__employee__cu_user__cu_punch_id='#N/A'),
            (~Q(attendance__employee__cu_user__user_type = 'Director') | Q(attendance__employee__cu_user__user_type__isnull=True)),
            (~Q(attendance__employee__cu_user__attendance_type__in=('PMS','CRM','Manual')) | Q(attendance__employee__cu_user__attendance_type__isnull = True)),
            ~Q(attendance__employee__cu_user__cu_user_id__in=('3183','3184','3185','2647','35','2564')),
            ~Q(attendance__employee__cu_user__sap_personnel_no__in=('37200039','37200065')),
            ~Q(attendance__employee__cu_user__cu_punch_id__in=punch_id_list),
            **filter).order_by(sort_field)
        # print(len(queryset))
        return queryset1

    @response_modify_decorator_list_or_get_after_execution_for_onoff_pagination
    def get(self, request, *args, **kwargs):
        response = super(UnAttendedAttendanceListView, self).get(self, request, args, kwargs)
        return response






class UnAppliedAttendanceReportDownloadView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    serializer_class = UnAppliedAttendanceSerializerv2
    queryset = AttendanceApprovalRequest.objects.filter(
        Q(is_requested=False)
        & Q(approved_status='regular')
        & Q(is_late_conveyance=False)
        & Q(lock_status=False)
        & Q(is_deleted=False)
        )

    def get_queryset(self):
        from datetime import datetime
        current_date = datetime.now().date()
        queryset = self.queryset
        # print(queryset)
        is_previous = self.request.query_params.get('is_previous', None)
        month = self.request.query_params.get('month', None)
        year = self.request.query_params.get('year', None)
        # print(is_previous)
        if is_previous:
            # print("in previous")
            first_day_of_current_month = datetime.today().date().replace(day=1)
            current_date = first_day_of_current_month - timedelta(days=7)
            # print(current_date)

            month_master = AttendenceMonthMaster.objects.filter(month_start__date__lte=current_date,
                                                                month_end__date__gte=current_date,
                                                                is_deleted=False).first()
            # print(month_master.month_start)
        elif month and year:
            # print("in else if")
            try:
                month_master = AttendenceMonthMaster.objects.filter(month=month,
                                                                    month_end__date__year=year,
                                                                    is_deleted=False).first()
            except:
                return AttendanceApprovalRequest.objects.none()

            # print(month_master)

        else:

            month_master = AttendenceMonthMaster.objects.filter(month_start__date__lte=current_date,
                                                                month_end__date__gte=current_date,
                                                                is_deleted=False).first()
            # print(month_master.month_start)

        try:
            queryset = queryset.filter(
                Q(attendance_date__gte=month_master.month_start) & Q(attendance_date__lte=month_master.month_end))
        except:
            return AttendanceApprovalRequest.objects.none()
        # print("queryset is",queryset)

        sort_field = '-id'

        employee_id = self.request.query_params.get('employee_id', None)
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        # approval_atatus = self.request.query_params.get('approval_status', None)
        start_date = self.request.query_params.get('from_date', None)
        end_date = self.request.query_params.get('to_date', None)
        reporting_head_id = self.request.query_params.get('reporting_head_id', None)
        request_type = self.request.query_params.get('request_type', None)
        department = self.request.query_params.get('department', None)

        if reporting_head_id:
            queryset = queryset.filter(Q(attendance__employee__cu_user__reporting_head_id=reporting_head_id))

        if department:
            queryset = queryset.filter(Q(attendance__employee__cu_user__department_id=department))

        if request_type:
            queryset = queryset.filter(Q(request_type=request_type))

        if start_date and end_date:
            start_object = datetime.strptime(start_date, '%Y-%m-%d')
            delta = timedelta(days=1)
            end_object = datetime.strptime(end_date, '%Y-%m-%d')
            queryset = queryset.filter(Q(attendance__date__lte=end_object + delta),
                                       Q(attendance__date__gte=start_object))
        else:
            queryset = queryset

        filter = dict()
        if employee_id:
            filter['attendance__employee__id'] = employee_id

        if field_name and order_by:
            if field_name == 'attendance_date' and order_by == 'asc':
                sort_field = 'attendance_date'
            if field_name == 'attendance_date' and order_by == 'desc':
                sort_field = '-attendance_date'
            if field_name == 'duration_start' and order_by == 'asc':
                sort_field = 'duration_start'
            if field_name == 'duration_start' and order_by == 'desc':
                sort_field = '-duration_start'
            if field_name == 'duration_end' and order_by == 'asc':
                sort_field = 'duration_end'
            if field_name == 'duration_end' and order_by == 'desc':
                sort_field = '-duration_end'
            if field_name == 'duration' and order_by == 'asc':
                sort_field = 'duration'
            if field_name == 'duration' and order_by == 'desc':
                sort_field = '-duration'

        punch_id_list = ['00444756', 'DEMO1111113', 'DEMO1111112', 'DEMO1111111', '37200008', '11111111']

        queryset1 = queryset.filter(
            ~Q(attendance__employee__cu_user__cu_punch_id='#N/A'),
            (~Q(attendance__employee__cu_user__user_type = 'Director') | Q(attendance__employee__cu_user__user_type__isnull=True)),
            (~Q(attendance__employee__cu_user__attendance_type__in=('PMS','CRM','Manual')) | Q(attendance__employee__cu_user__attendance_type__isnull = True)),
            ~Q(attendance__employee__cu_user__cu_user_id__in=('3183','3184','3185','2647','35','2564')),
            ~Q(attendance__employee__cu_user__sap_personnel_no__in=('37200039','37200065')),
            ~Q(attendance__employee__cu_user__cu_punch_id__in=punch_id_list),
            **filter).order_by(sort_field)
        # print(len(queryset))
        return queryset1

    def get(self, request, *args, **kwargs):
        response = super(UnAppliedAttendanceReportDownloadView, self).get(self, request, args, kwargs)
        # print(response.data)

        if 'results' in response.data:
            response_s = response.data['results']
        else:
            response_s = response.data

        total_data_list = []

        for data in response_s:
            temp_dict = dict(data)
            # print(temp_dict)
            temp_lst = list()
            # temp_lst.append(temp_dict['user_id'])
            # emp_code
            temp_lst.append(temp_dict['emp_code'])
            temp_lst.append(temp_dict['name'])
            temp_lst.append(temp_dict['punch_id'])
            temp_lst.append(temp_dict['reporting_head'])
            temp_lst.append(temp_dict['phone_no'])
            temp_lst.append(temp_dict['sap_personnel_no'])
            temp_lst.append(temp_dict['duration_start'])
            temp_lst.append(temp_dict['duration_end'])
            temp_lst.append(temp_dict['duration'])
            temp_lst.append(temp_dict['date'])

            total_data_list.append(temp_lst)

        if len(total_data_list) > 0:
            from pandas import DataFrame
            if os.path.isdir('media/attendance/Unapplied_attendance_report/document'):
                file_name = 'media/attendance/Unapplied_attendance_report/document/Unapplied_attendance_report.xlsx'
                file_path = settings.MEDIA_ROOT_EXPORT + file_name
            else:
                os.makedirs('media/attendance/Unapplied_attendance_report/document')
                file_name = 'media/attendance/Unapplied_attendance_report/document/Unapplied_attendance_report.xlsx'
                file_path = settings.MEDIA_ROOT_EXPORT + file_name

            df = DataFrame(
                total_data_list, columns=[
                    'Emp_code', 'Name', 'punch_id', 'Reporting_head', 'Contact_no', 'Sap_Personnel_No',
                    'Duration_start', 'Duration_end', 'Duration', 'date'
                ]
            )
            df.to_excel(file_path, index=None, header=True)
            url = getHostWithPort(request) + file_name if file_name else None

            return Response({'download_url': url, 'request_status': 1, 'msg': settings.MSG_SUCCESS})


        else:
            return Response({'request_status': 0, 'msg': "NO DATA FOUND"})



# unapprove attendance by swarup (28.12.2020)

class UnAttendedAttendanceReportDownloadView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    serializer_class = UnAppliedAttendanceSerializerv2
    queryset = AttendanceApprovalRequest.objects.filter(
        Q(is_requested=True) &
        Q(approved_status='pending') &
        Q(is_deleted=False) &
        Q(is_late_conveyance=False) &
        Q(lock_status=False)
        )

    def get_queryset(self):
        from datetime import datetime
        current_date = datetime.now().date()
        queryset = self.queryset
        # print(queryset)
        is_previous = self.request.query_params.get('is_previous', None)
        month = self.request.query_params.get('month', None)
        year = self.request.query_params.get('year', None)
        # print(is_previous)
        if is_previous:
            # print("in previous")
            first_day_of_current_month = datetime.today().date().replace(day=1)
            current_date = first_day_of_current_month - timedelta(days=7)
            # print(current_date)

            month_master = AttendenceMonthMaster.objects.filter(month_start__date__lte=current_date,
                                                                month_end__date__gte=current_date,
                                                                is_deleted=False).first()
            # print(month_master.month_start)
        elif month and year:
            # print("in else if")
            month_master = AttendenceMonthMaster.objects.filter(month=month,
                                                                month_end__date__year=year,
                                                                is_deleted=False).first()
            # print(month_master)

        else:

            month_master = AttendenceMonthMaster.objects.filter(month_start__date__lte=current_date,
                                                                month_end__date__gte=current_date,
                                                                is_deleted=False).first()
            # print(month_master.month_start)

        queryset = queryset.filter(
            Q(attendance_date__gte=month_master.month_start) & Q(attendance_date__lte=month_master.month_end))
        # print("queryset is",queryset)

        sort_field = '-id'

        employee_id = self.request.query_params.get('employee_id', None)
        reporting_head_id = self.request.query_params.get('reporting_head_id',None)
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        # approval_atatus = self.request.query_params.get('approval_status', None)
        start_date = self.request.query_params.get('from_date', None)
        end_date = self.request.query_params.get('to_date', None)

        if reporting_head_id:
            queryset = queryset.filter(Q(attendance__employee__cu_user__reporting_head_id=reporting_head_id))

        if start_date and end_date:
            start_object = datetime.strptime(start_date, '%Y-%m-%d')
            delta = timedelta(days=1)
            end_object = datetime.strptime(end_date, '%Y-%m-%d')
            queryset = queryset.filter(Q(attendance__date__lte=end_object + delta),
                                       Q(attendance__date__gte=start_object))
        else:
            queryset = queryset

        filter = dict()
        if employee_id:
            filter['attendance__employee__id'] = employee_id

        if field_name and order_by:
            if field_name == 'attendance_date' and order_by == 'asc':
                sort_field = 'attendance_date'
            if field_name == 'attendance_date' and order_by == 'desc':
                sort_field = '-attendance_date'
            if field_name == 'duration_start' and order_by == 'asc':
                sort_field = 'duration_start'
            if field_name == 'duration_start' and order_by == 'desc':
                sort_field = '-duration_start'
            if field_name == 'duration_end' and order_by == 'asc':
                sort_field = 'duration_end'
            if field_name == 'duration_end' and order_by == 'desc':
                sort_field = '-duration_end'
            if field_name == 'duration' and order_by == 'asc':
                sort_field = 'duration'
            if field_name == 'duration' and order_by == 'desc':
                sort_field = '-duration'

        punch_id_list = ['00444756', 'DEMO1111113', 'DEMO1111112', 'DEMO1111111', '37200008', '11111111']

        queryset1 = queryset.filter(
            ~Q(attendance__employee__cu_user__cu_punch_id='#N/A'),
            (~Q(attendance__employee__cu_user__user_type = 'Director') | Q(attendance__employee__cu_user__user_type__isnull=True)),
            (~Q(attendance__employee__cu_user__attendance_type__in=('PMS','CRM','Manual')) | Q(attendance__employee__cu_user__attendance_type__isnull = True)),
            ~Q(attendance__employee__cu_user__cu_user_id__in=('3183','3184','3185','2647','35','2564')),
            ~Q(attendance__employee__cu_user__sap_personnel_no__in=('37200039','37200065')),
            ~Q(attendance__employee__cu_user__cu_punch_id__in=punch_id_list),
            **filter).order_by(sort_field)
        return queryset1

    def get(self, request, *args, **kwargs):
        response = super(UnAttendedAttendanceReportDownloadView, self).get(self, request, args, kwargs)
        # print(response.data)

        if 'results' in response.data:
            response_s = response.data['results']
        else:
            response_s = response.data

        total_data_list = []

        for data in response_s:
            temp_dict = dict(data)
            # print(temp_dict)
            temp_lst = list()
            # temp_lst.append(temp_dict['user_id'])
            # emp_code
            temp_lst.append(temp_dict['emp_code'])
            temp_lst.append(temp_dict['name'])
            temp_lst.append(temp_dict['punch_id'])
            temp_lst.append(temp_dict['reporting_head'])
            temp_lst.append(temp_dict['phone_no'])
            temp_lst.append(temp_dict['sap_personnel_no'])
            temp_lst.append(temp_dict['duration_start'])
            temp_lst.append(temp_dict['duration_end'])
            temp_lst.append(temp_dict['duration'])
            temp_lst.append(temp_dict['request_type'])
            temp_lst.append(temp_dict['date'])
            temp_lst.append(temp_dict['justification'])

            total_data_list.append(temp_lst)

        if len(total_data_list) > 0:
            from pandas import DataFrame
            if os.path.isdir('media/attendance/Unapplied_attendance_report/document'):
                file_name = 'media/attendance/Unapplied_attendance_report/document/Unattended_attendance_report.xlsx'
                file_path = settings.MEDIA_ROOT_EXPORT + file_name
            else:
                os.makedirs('media/attendance/Unapplied_attendance_report/document')
                file_name = 'media/attendance/Unapplied_attendance_report/document/Unattended_attendance_report.xlsx'
                file_path = settings.MEDIA_ROOT_EXPORT + file_name

            df = DataFrame(
                total_data_list, columns=[
                    'Emp_code', 'Name', 'punch_id', 'Reporting_head', 'Contact_no', 'Sap_Personnel_No',
                    'Duration_start', 'Duration_end', 'Duration','Request Type', 'date','Justification'
                ]
            )
            df.to_excel(file_path, index=None, header=True)
            url = getHostWithPort(request) + file_name if file_name else None

            return Response({'download_url': url, 'request_status': 1, 'msg': settings.MSG_SUCCESS})


        else:
            return Response({'request_status': 0, 'msg': "NO DATA FOUND"})


class FlexiEmployeeListWithoutDetailsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = User.objects.filter(is_superuser=False, cu_user__is_flexi_hour=True)
    serializer_class = EmployeeListWithoutDetailsSerializer
    pagination_class = OnOffPagination

    def get_queryset(self):
        search_key = self.request.query_params.get('search_key', None)
        module = self.request.query_params.get('module', None)
        team_approval_flag = self.request.query_params.get('team_approval_flag', None)
        login_user_details = self.request.user

        # print('login_user_details', login_user_details, login_user_details.id)

        if login_user_details.is_superuser == False:
            if module == 'hrms':
                module = 'ATTENDANCE & HRMS'
            if module == 'ETASK' or module == 'etask':
                module = 'E-Task'
            which_type_of_user = TMasterModuleRoleUser.objects.filter(
                mmr_module__cm_name=module,
                mmr_user=login_user_details,
                mmr_is_deleted=False
            ).values_list('mmr_type', flat=True)
            if which_type_of_user:
                which_type_of_user = TMasterModuleRoleUser.objects.filter(
                    mmr_module__cm_name=module,
                    mmr_user=login_user_details,
                    mmr_is_deleted=False
                ).values_list('mmr_type', flat=True)[0]

            if team_approval_flag == '1' and module is not None:

                if which_type_of_user == 2:  # [module admin]
                    filter_users = TMasterModuleRoleUser.objects.filter(
                        mmr_type__in=('3'),
                        mmr_module__cm_name=module,
                        mmr_is_deleted=False,
                        mmr_user_id__in=TCoreUserDetail.objects.filter(cu_is_deleted=False,
                                                                       is_flexi_hour=True).values_list(
                            'cu_user_id', flat=True)).values_list('mmr_user_id', flat=True)

                else:
                    filter_users = TMasterModuleRoleUser.objects.filter(
                        mmr_type__in=('3'),
                        mmr_module__cm_name=module,
                        mmr_is_deleted=False,
                        mmr_user_id__in=TCoreUserDetail.objects.filter(
                            reporting_head_id=login_user_details, is_flexi_hour=True, cu_is_deleted=False).values_list(
                            'cu_user_id', flat=True)).values_list('mmr_user_id', flat=True)

                if search_key:
                    queryset = User.objects.annotate(full_name=Concat('first_name', V(' '), 'last_name')).filter(
                        full_name__icontains=search_key,
                        pk__in=(filter_users),
                        is_active=True,
                        is_superuser=False
                    )
                    # print(search_key, queryset)
                else:
                    queryset = User.objects.filter(
                        pk__in=(filter_users),
                        is_active=True,
                        is_superuser=False
                    )
                # print('queryset',queryset.query)
                return queryset

            elif team_approval_flag == '1' and module is None:
                if search_key:
                    queryset = User.objects.annotate(full_name=Concat('first_name', V(' '), 'last_name')).filter(
                        full_name__icontains=search_key, pk__in=(
                            TCoreUserDetail.objects.filter(reporting_head_id=login_user_details, is_flexi_hour=True,
                                                           cu_is_deleted=False).values_list('cu_user_id', flat=True)))
                else:
                    queryset = User.objects.filter(pk__in=(
                        TCoreUserDetail.objects.filter(reporting_head_id=login_user_details, is_flexi_hour=True,
                                                       cu_is_deleted=False).values_list('cu_user_id', flat=True)))
                return queryset

            elif team_approval_flag is None and module is not None:
                # print('modulekkkkkkkkkkkkkkkkkkkkkkkkkk',module)
                # time.sleep(5)
                if module.lower() == "vms":
                    if search_key:
                        return self.queryset.annotate(full_name=Concat('first_name', V(' '), 'last_name')).filter(
                            full_name__icontains=search_key)
                    else:
                        return self.queryset.all()

                elif module == "E-Task":
                    # print('checdkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk')
                    # time.sleep(10)
                    '''
                        Reason : 
                        1) on_behalf_of :According to changing function doc to show list of user highier level
                        2) assign_to / sub_assign_to : According to changing function doc to show list of user lower level or hod
                        Author : Rupam Hazra
                        Date : 21/02/2020
                        Line Number : 1419
                    '''
                    mode_for = self.request.query_params.get('mode_for', None)
                    if mode_for == 'on_behalf_of':
                        hi_user_list_details = TCoreUserDetail.objects.filter(
                            cu_user=login_user_details, cu_is_deleted=False, reporting_head__isnull=False).values_list(
                            'reporting_head', flat=True)
                        # print('hi_user_list_details',hi_user_list_details)
                        if hi_user_list_details.count() > 0:
                            hi_user_details = hi_user_list_details[0]
                            # print('hi_user_details_up',hi_user_details,type(hi_user_details))
                            hi_user_details_l = self.getHighierLevelUserList(str(hi_user_details))
                            print('hi_user_details_l', hi_user_details_l, type(hi_user_details_l))
                            time.sleep(10)
                            hi_user_details_l = [int(x) for x in hi_user_details_l.split(",")]
                            if search_key:
                                return self.queryset.annotate(
                                    full_name=Concat('first_name', V(' '), 'last_name')).filter(
                                    full_name__icontains=search_key, pk__in=hi_user_details_l)
                            else:
                                return self.queryset.filter(pk__in=hi_user_details_l)

                    elif mode_for == 'assign_to' or mode_for == 'sub_assign_to':

                        '''
                            Reason :  
                            1) assign_to / sub_assign_to : Comment the HOD checking as per discussion
                            Author : Rupam Hazra
                            Date : 04/03/2020
                            Line Number : 1446
                        '''

                        hi_user_list_details = TCoreUserDetail.objects.filter(
                            reporting_head=login_user_details, cu_is_deleted=False, cu_user__isnull=False).values_list(
                            'cu_user', flat=True)
                        # print('hi_user_list_details',list(hi_user_list_details))
                        hi_user_details1 = ''
                        if hi_user_list_details.count() > 0:
                            for hi_user_details in hi_user_list_details:
                                hi_user_list_details = self.getLowerLevelUserList(str(hi_user_details),
                                                                                  list(hi_user_list_details))
                            # print('hi_user_details1',hi_user_list_details)
                            if search_key:
                                return self.queryset.annotate(
                                    full_name=Concat('first_name', V(' '), 'last_name')).filter(
                                    full_name__icontains=search_key, pk__in=hi_user_list_details)
                            else:
                                return self.queryset.filter(pk__in=hi_user_list_details)

                        # is_hod = TCoreUserDetail.objects.filter(
                        #     hod = login_user_details,cu_is_deleted=False,cu_user__isnull=False).values('hod').distinct()

                        # if is_hod:
                        #     department_d = TCoreUserDetail.objects.filter(
                        #         cu_user = login_user_details,cu_is_deleted=False,cu_user__isnull=False).values_list('department',flat=True)
                        #     #print('department_d',department_d)
                        #     if department_d:
                        #         hi_user_list_details = TCoreUserDetail.objects.filter(~Q(cu_user=login_user_details),department__in=department_d).values_list('cu_user',flat=True)
                        #         #print('hi_user_list_details',hi_user_list_details)
                        #         if search_key:
                        #             return self.queryset.filter((Q(first_name__icontains=search_key) | Q(last_name__icontains=search_key)),pk__in=hi_user_list_details)
                        #         else:
                        #             return self.queryset.filter(pk__in=hi_user_list_details)
                        # else:

                        #     hi_user_list_details = TCoreUserDetail.objects.filter(
                        #         reporting_head = login_user_details,cu_is_deleted=False,cu_user__isnull=False).values_list('cu_user',flat=True)
                        #     #print('hi_user_list_details',list(hi_user_list_details))
                        #     hi_user_details1 = ''
                        #     if hi_user_list_details.count() > 0 :
                        #         for hi_user_details in hi_user_list_details:
                        #             hi_user_list_details = self.getLowerLevelUserList(str(hi_user_details),list(hi_user_list_details))
                        #         #print('hi_user_details1',hi_user_list_details)
                        #         if search_key:
                        #             return self.queryset.filter((Q(first_name__icontains=search_key) | Q(last_name__icontains=search_key)),pk__in=hi_user_list_details)
                        #         else:
                        #             return self.queryset.filter(pk__in=hi_user_list_details)

                    else:
                        if search_key:
                            return self.queryset.annotate(full_name=Concat('first_name', V(' '), 'last_name')).filter(
                                ~Q(id=self.request.user.id), full_name__icontains=search_key)
                        else:
                            # return self.queryset.all()
                            return self.queryset.filter(~Q(id=self.request.user.id))

                elif module.lower() == "ATTENDANCE & HRMS":
                    if search_key:
                        return self.queryset.annotate(full_name=Concat('first_name', V(' '), 'last_name')).filter(
                            full_name__icontains=search_key)
                    else:
                        return self.queryset.all()
                else:
                    if search_key:
                        queryset = User.objects.annotate(full_name=Concat('first_name', V(' '), 'last_name'),
                                                         cu_user__is_flexi_hour=True).filter(
                            full_name__icontains=search_key,
                            pk__in=(
                                TMasterModuleRoleUser.objects.filter(mmr_type__in=('3'),
                                                                     mmr_module__cm_name=module).values_list(
                                    'mmr_user_id', flat=True)
                            )
                        )
                    else:
                        queryset = User.objects.filter(
                            pk__in=(
                                TMasterModuleRoleUser.objects.filter(mmr_module__cm_name=module,
                                                                     mmr_type__in=('3'),
                                                                     cu_user__is_flexi_hour=True).values_list(
                                    'mmr_user_id',
                                    flat=True)
                            )
                        )
                    # print('queryset', queryset.query)
                    return queryset
        else:
            if search_key:
                queryset = self.queryset.annotate(full_name=Concat('first_name', V(' '), 'last_name')).filter(
                    full_name__icontains=search_key)
            else:
                queryset = self.queryset.all()

            return queryset

    def getHighierLevelUserList(self, user_id='') -> list:
        try:
            hi_user_list = user_id
            hi_user_list_d = TCoreUserDetail.objects.filter(cu_user_id=str(user_id), cu_is_deleted=False,
                                                            reporting_head__isnull=False).values_list(
                'reporting_head', flat=True)
            if hi_user_list_d.count() > 0:
                hi_user_list1 = str(hi_user_list_d[0])
                hi_user_list = hi_user_list + ',' + str(self.getHighierLevelUserList(hi_user_list1))
            return hi_user_list.replace(',None', '')
        except Exception as e:
            raise e

    def getLowerLevelUserList(self, user_id='', main_list='') -> list:
        try:
            # print('user_id',user_id)
            # print('main_list',main_list)
            hi_user_list_details = TCoreUserDetail.objects.filter(reporting_head_id=str(user_id), cu_is_deleted=False,
                                                                  cu_user__isnull=False).values_list(
                'cu_user_id', flat=True)
            # print('hi_user_list_details1111',hi_user_list_details)
            if hi_user_list_details.count() > 0:
                for hi_user_details in hi_user_list_details:
                    main_list.append(hi_user_details)
                    self.getLowerLevelUserList(str(hi_user_details), main_list)
            return main_list
        except Exception as e:
            raise e

    @response_modify_decorator_list_or_get_before_execution_for_onoff_pagination
    def get(self, request, *args, **kwargs):
        # print('self',self.response)
        return response


# eployee list under resigned reporting head
class EmployeeListUnderResignedReportingHeadV2View(generics.ListAPIView):
    '''
        Reason : Get Active User List in Excel File
        Author :Swarup Adhikary
        Line number:  3449 - 3465
        Date : 22/04/2020
    '''
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreUserDetail.objects.filter(cu_user__is_superuser=False, cu_user__is_active=True)
    serializer_class = EmployeeListUnderReportingHeadSerializerv2
    pagination_class = OnOffPagination

    def get_queryset(self):
        '''
            eleminate login user on employee list added by Rupam Hazra Line number 458 - 459
        '''
        login_user = self.request.user.id
        self.queryset = self.queryset.filter(cu_user__is_active=True)
        resigned_rh = TCoreUserDetail.objects.filter(cu_user__is_active=True,
                                                     reporting_head__cu_user__resignation_date__isnull=False).values(
            "reporting_head").distinct()
        rh_id_lst = list()
        for each in resigned_rh:
            rh_id_lst.append(each['reporting_head'])

        # print(rh_id_lst)

        self.queryset = self.queryset.filter(reporting_head__in=rh_id_lst)
        # print(self.queryset)

        sort_field = '-id'
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        department = self.request.query_params.get('department', None)
        designation = self.request.query_params.get('designation', None)
        company = self.request.query_params.get('company', None)

        filter = dict()

        if field_name and order_by:
            if field_name == 'username' and order_by == 'asc':
                sort_field = 'username'
            if field_name == 'username' and order_by == 'desc':
                sort_field = '-username'

        if department:
            filter['department_id'] = department
        if designation:
            filter['designation_id'] = designation

        queryset = self.queryset.filter(~Q(cu_punch_id='#N/A'), termination_date__isnull=True, cu_is_deleted=False,
                                        **filter).order_by(sort_field)

        # print(queryset)

        return queryset

    @response_modify_decorator_list_or_get_after_execution_for_onoff_pagination
    def get(self, request, *args, **kwargs):
        response = super(EmployeeListUnderResignedReportingHeadV2View, self).get(self, request, args, kwargs)
        # data_dict = dict()

        # response.data = data_dict
        # print(response.dict)
        return response
        # return Response({response ,'request_status': 1, 'msg': settings.MSG_SUCCESS})


# eployee list under resigned reporting head list download api view

class EmployeeListUnderResignedReportingHeadDownloadV2View(generics.ListAPIView):
    '''
        Reason : Get Active User List in Excel File
        Author :Swarup Adhikary
        Line number:  3449 - 3465
        Date : 25/06/2020
    '''
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreUserDetail.objects.filter(cu_user__is_superuser=False, cu_user__is_active=True)
    serializer_class = EmployeeListUnderReportingHeadSerializerv2
    pagination_class = None

    def get_queryset(self):
        '''
            eleminate login user on employee list added by Rupam Hazra Line number 458 - 459
        '''
        login_user = self.request.user.id
        self.queryset = self.queryset.filter(cu_user__is_active=True)
        resigned_rh = TCoreUserDetail.objects.filter(cu_user__is_active=True,
                                                     reporting_head__cu_user__resignation_date__isnull=False).values(
            "reporting_head").distinct()
        rh_id_lst = list()
        for each in resigned_rh:
            rh_id_lst.append(each['reporting_head'])

        # print(rh_id_lst)

        self.queryset = self.queryset.filter(reporting_head__in=rh_id_lst)
        # print(self.queryset)

        sort_field = '-id'
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        department = self.request.query_params.get('department', None)
        designation = self.request.query_params.get('designation', None)

        filter = dict()

        if field_name and order_by:
            if field_name == 'username' and order_by == 'asc':
                sort_field = 'username'
            if field_name == 'username' and order_by == 'desc':
                sort_field = '-username'

        if department:
            filter['department_id'] = department
        if designation:
            filter['designation_id'] = designation

        queryset = self.queryset.filter(~Q(cu_punch_id='#N/A'), termination_date__isnull=True, cu_is_deleted=False,
                                        **filter).order_by(sort_field)

        # print(queryset)

        return queryset

    def get(self, request, *args, **kwargs):
        response = super(__class__, self).get(self, request, *args, **kwargs)

        # print(response.data)
        data_list = list()
        for data in response.data:
            # print(data)
            data_list.append([data['emp_id'], data['username'], data['reporting_head'],
                              data['sap_personnel_no'], data['department_name'], data['designation_name'],
                              data['hod_name']])

        file_name = ''
        if data_list:

            if os.path.isdir('media/hrms/reportees/document'):
                file_name = 'media/hrms/reportees/document/reportees_for_new_rh.xlsx'
                file_path = settings.MEDIA_ROOT_EXPORT + file_name
                print(file_path)
            else:
                os.makedirs('media/hrms/reportees/document')
                file_name = 'media/hrms/reportees/document/reportees_for_new_rh.xlsx'
                file_path = settings.MEDIA_ROOT_EXPORT + file_name

            final_df = pd.DataFrame(data_list, columns=['Emp ID', 'Employee Username', 'Reporting Head',
                                                        'Sap Personal No', 'Department', 'Designation', 'Hod'])

            export_csv = final_df.to_excel(file_path, index=None, header=True)
            if request.is_secure():
                protocol = 'https://'
            else:
                protocol = 'http://'

        url = getHostWithPort(request) + file_name if file_name else None
        if url:
            return Response({'request_status': 1, 'msg': 'Success', 'url': url})
        else:
            return Response({'request_status': 0, 'msg': 'Not Found', 'url': url})


class ResignedRhDetailView(generics.RetrieveUpdateAPIView):
    """
    send parameter 'is_active'
    View for user update active and in_active
    using user ID
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    serializer_class = ResignedReportingHeadDetailSerializer
    queryset = User.objects.all()

    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        return response


class EmployeeListForNewReportingHeadV2View(generics.ListAPIView):
    '''
        Reason : Get Active User List in Excel File
        Author :Swarup Adhikary
        Line number:  3449 - 3465
        Date : 22/04/2020
    '''
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = User.objects.filter(is_superuser=False, is_active=True,
                                   cu_user__resignation_date__isnull=True)
    serializer_class = EmployeeListForRhSerializer

    # pagination_class = OnOffPagination

    def get_queryset(self):
        '''
            eleminate login user on employee list added by Rupam Hazra Line number 458 - 459
        '''
        print(self.queryset)

        selected_user = self.request.query_params.get('users', None)

        id_lst = list(map(int, selected_user.split(",")))

        sort_field = '-id'
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        department = self.request.query_params.get('department', None)
        designation = self.request.query_params.get('designation', None)

        filter = dict()

        if field_name and order_by:
            if field_name == 'username' and order_by == 'asc':
                sort_field = 'username'
            if field_name == 'username' and order_by == 'desc':
                sort_field = '-username'

        if department:
            filter['department_id'] = department
        if designation:
            filter['designation_id'] = designation

        queryset = self.queryset.filter(~Q(id__in=id_lst), cu_user__cu_is_deleted=False)

        return queryset

    # @response_modify_decorator_list_or_get_after_execution_for_onoff_pagination
    def get(self, request, *args, **kwargs):
        response = super(EmployeeListForNewReportingHeadV2View, self).get(self, request, args, kwargs)
        return response


# change the reporting head
class ReportingHeadChangeV2View(generics.ListAPIView):
    '''
        Reason : Get Active User List in Excel File
        Author :Swarup Adhikary
        Line number:  3449 - 3465
        Date : 22/04/2020
    '''
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get(self, request, *args, **kwargs):
        try:
            employees = self.request.query_params.get('employees', None)
            new_rh = self.request.query_params.get('new_rh', None)

            emp_lst = list(map(int, employees.split(",")))

            usr_object = TCoreUserDetail.objects.filter(cu_user__id__in=emp_lst)
            for each in usr_object:
                each.reporting_head = User.objects.get(id=new_rh)
                each.save()

            return Response({'request_status': 1, 'msg': settings.MSG_SUCCESS})
        except Exception as E:
            return Response({'request_status': 0, 'msg': "something went wrong {}".format(E)})


class ListOfReporteesView(generics.ListAPIView):
    '''
        Reason : Get Active User List in Excel File
        Author :Swarup Adhikary
        Line number:  3449 - 3465
        Date : 22/04/2020
    '''
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreUserDetail.objects.filter(cu_user__is_superuser=False, cu_user__is_active=True)
    serializer_class = EmployeeListUnderReportingHeadSerializerv2
    pagination_class = OnOffPagination

    def get_queryset(self):
        '''
            eleminate login user on employee list added by Rupam Hazra Line number 458 - 459
        '''
        login_user = self.request.user.id
        self.queryset = self.queryset.filter(cu_user__is_active=True)
        # resigned_rh = TCoreUserDetail.objects.filter(cu_user__is_active=True,
        #                                              reporting_head__cu_user__resignation_date__isnull=False).values("reporting_head").distinct()
        # rh_id_lst = list()
        # for each in resigned_rh:
        #     rh_id_lst.append(each['reporting_head'])
        #
        # print(rh_id_lst)
        #
        # self.queryset = self.queryset.filter(reporting_head__in=rh_id_lst)
        # print(self.queryset)

        sort_field = '-id'
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        department = self.request.query_params.get('department', None)
        designation = self.request.query_params.get('designation', None)
        user = self.request.query_params.get('user', None)

        filter = dict()

        if field_name and order_by:
            if field_name == 'username' and order_by == 'asc':
                sort_field = 'username'
            if field_name == 'username' and order_by == 'desc':
                sort_field = '-username'

        if department:
            filter['department_id'] = department
        if designation:
            filter['designation_id'] = designation

        queryset = self.queryset.filter(~Q(cu_punch_id='#N/A'), reporting_head__id=user, termination_date__isnull=True,
                                        cu_is_deleted=False,
                                        **filter).order_by(sort_field)

        # print(queryset)

        return queryset

    @response_modify_decorator_list_or_get_after_execution_for_onoff_pagination
    def get(self, request, *args, **kwargs):
        response = super(ListOfReporteesView, self).get(self, request, args, kwargs)
        # data_dict = dict()

        # response.data = data_dict
        # print(response.dict)
        return response
        # return Response({response ,'request_status': 1, 'msg': settings.MSG_SUCCESS})


class EmployeeLeaveAllcationModify(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreUserDetail.objects.filter()
    serializer_class = EmployeeListUnderReportingHeadSerializerv2

    def get_queryset(self):
        today = datetime.datetime.now()
        current_month = AttendenceMonthMaster.objects.get(
            month_start__date__lte=today,
            month_end__date__gte=today, is_deleted=False)
        year_start_date = current_month.year_start_date
        year_end_date = current_month.year_end_date

        employee_id = self.request.query_params.get('employee_id', None)
        if employee_id:
            employee_id_lst = employee_id.split(',')
            print(employee_id_lst)
            self.queryset = self.queryset.filter(cu_user__id__in=employee_id_lst)
        self.queryset = self.queryset.exclude(salary_type=None)

        self.queryset = self.queryset.filter(Q(cu_is_deleted=True,
                                               termination_date__gte=year_start_date,
                                               termination_date__lte=year_end_date)
                                             | Q(cu_is_deleted=False))
        print(self.queryset)
        for each in self.queryset:
            usr_obj = TCoreUserDetail.objects.get(cu_user=each.cu_user)
            joining_date = usr_obj.joining_date
            print(joining_date)
            from_date = year_start_date
            to_date = year_end_date
            print(from_date, to_date)
            is_joining_year = False
            if joining_date > from_date:
                print("in joining date")
                is_joining_year = True
                from_date = joining_date

            if str(usr_obj.salary_type.st_code) == "AA":
                granted_cl = 0
                granted_sl = 0
                granted_el = 0
            elif str(usr_obj.salary_type.st_code) == "BB":
                granted_cl = 10
                granted_sl = 0
                granted_el = 15
            elif str(usr_obj.salary_type.st_code) == "FF":
                granted_cl = 16
                granted_sl = 0
                granted_el = 15
            elif str(usr_obj.salary_type.st_code) in ["CC", "DD"]:
                granted_cl = 10
                granted_sl = 7
                granted_el = 15
            elif str(usr_obj.salary_type.st_code) == "EE":
                granted_cl = 10
                granted_sl = 6
                granted_el = 15
            else:
                granted_el = 0
                granted_cl = 0
                granted_sl = 0

            usr_obj.granted_el = granted_el
            usr_obj.granted_cl = granted_cl
            usr_obj.granted_sl = granted_sl
            usr_obj.save()

            attendenceMonthMaster = AttendenceMonthMaster.objects.filter(
                month_start__date__lte=from_date,
                month_end__date__gte=from_date, is_deleted=False).values('id', 'grace_available',
                                                                         'year_start_date',
                                                                         'year_end_date',
                                                                         'month',
                                                                         'month_start',
                                                                         'month_end',
                                                                         'days_in_month',
                                                                         'payroll_month')

            leave_filter = {}
            total_days = ((to_date - from_date).days) + 1
            # print("total-------------------",total_days)
            cl, al, el, sl = 0, 0, 0, 0
            if usr_obj.salary_type:
                if usr_obj.salary_type.st_code in ['FF', 'EE']:
                    al = round_calculation(total_days, (granted_cl + granted_sl + granted_el))
                    # print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%", al)
                elif usr_obj.salary_type.st_code in ['CC', 'DD']:
                    cl = round_calculation(total_days, granted_cl)
                    sl = round_calculation(total_days, granted_sl)
                    el = round_calculation(total_days, granted_el)
                    # print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&",cl,sl, el)
                elif usr_obj.salary_type.st_code in ['BB']:
                    cl = round_calculation(total_days, granted_cl)
                    # sl = round_calculation(total_days, granted_sl)
                    el = round_calculation(total_days, granted_el)
                else:
                    pass
            leave_confirm = round_calculation(total_days,
                                              (granted_cl + granted_sl + granted_el))
            leave_filter['cl'] = round_calculation(total_days, (granted_cl))
            leave_filter['sl'] = round_calculation(total_days, (granted_sl))
            if granted_el:
                leave_filter['el'] = round_calculation(total_days, granted_el)
            else:
                leave_filter['el'] = float(0)

            if is_joining_year:
                if attendenceMonthMaster:
                    available_grace = grace_calculation(joining_date.date(), attendenceMonthMaster)
                    if available_grace:
                        if JoiningApprovedLeave.objects.filter(employee=usr_obj.cu_user.id):
                            JoiningApprovedLeave.objects.filter(employee=usr_obj.cu_user.id).update(
                                year=joining_date.year,
                                month=attendenceMonthMaster[0]['month'],
                                **leave_filter,
                                first_grace=available_grace)

                        else:
                            JoiningApprovedLeave.objects.create(employee=usr_obj.cu_user, year=joining_date.year,
                                                                month=attendenceMonthMaster[0]['month'],
                                                                **leave_filter,
                                                                first_grace=available_grace)

            users = [usr_obj.cu_user.id]
            roundOffLeaveCalculationUpdate(users, attendenceMonthMaster,
                                           leave_confirm, leave_confirm,
                                           total_days, year_end_date, attendenceMonthMaster[0]['month_start'],
                                           joining_date, cl, sl, el, al, is_joining_year)

        return self.queryset

    # @response_modify_decorator_list_or_get_after_execution_for_pagination
    def get(self, request, *args, **kwargs):
        response = super(__class__, self).get(self, request, args, kwargs)
        return response
        # return {'result':"Done"}


class ProbationThreeMonthsAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = HrmsThreeMonthsProbationReviewForm.objects.filter(is_deleted=False)
    serializer_class = ProbationAddSerializer

    # filter_backends = (DjangoFilterBackend,)
    # filterset_fields = ('employee', 'guest', 'id')

    # from rest_framework.parsers import MultiPartParser, FormParser
    # parser_classes = [MultiPartParser,FormParser]
    @response_modify_decorator_get_after_execution
    def get(self, request, *args, **kwargs):
        response = super(ProbationThreeMonthsAddView, self).get(self, request, args, kwargs)
        # print('response',response.data)
        login_user_id = self.request.user.id
        # usr_obj = TCoreUserDetail.objects.get(cu_)
        # daily_ex = self.kwargs['daily_expenses']
        # print(daily_ex)
        # print(daily_ex[0]['added_docs'])
        # doc_flag = self.request.query_params.get('doc_flag', None)
        # for data in response.data:

        return response


class EmployeeDetailsForProbationAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreUserDetail.objects.filter(cu_is_deleted=False)
    serializer_class = UserDetailForProbationAddSerializer

    # filter_backends = (DjangoFilterBackend,)
    # filterset_fields = ('employee', 'guest', 'id')

    # from rest_framework.parsers import MultiPartParser, FormParser
    # parser_classes = [MultiPartParser,FormParser]
    def get_queryset(self):
        login_user_id = self.request.user.id
        queryset = self.queryset.get(cu_user__id=login_user_id)
        print(queryset.count())
        return queryset

    @response_modify_decorator_get_after_execution
    def get(self, request, *args, **kwargs):
        response = super(EmployeeDetailsForProbationAddView, self).get(self, request, args, kwargs)
        return response


class PendingThreeMonthsProbatinEmployeeListV2View(generics.ListAPIView):
    '''
        Reason : Get Active User List in Excel File
        Author :Swarup Adhikary
        Line number:  3449 - 3465
        Date : 03/09/2020
    '''
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreUserDetail.objects.filter(cu_user__is_superuser=False, cu_user__is_active=True)
    serializer_class = PendingProbationEmployeeListSerializerv2
    pagination_class = OnOffPagination

    def get_queryset(self):
        '''
            eleminate login user on employee list added by Rupam Hazra Line number 458 - 459
        '''
        login_user = self.request.user.id
        from datetime import datetime
        date = datetime.now()
        eight_days_before_date = date - timedelta(8)
        print(eight_days_before_date)
        pending_probation_obj = HrmsThreeMonthsProbationReviewForm.objects.filter(submission_pending=True,
                                                                                  first_reminder_date__lte=eight_days_before_date).values_list(
            'employee', flat=True)
        print(pending_probation_obj)
        pending_probation_obj = list(pending_probation_obj)
        self.queryset = self.queryset.filter(cu_user__in=pending_probation_obj)

        sort_field = '-id'
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        department = self.request.query_params.get('department', None)
        designation = self.request.query_params.get('designation', None)
        start_date = self.request.query_params.get('from_date', None)
        end_date = self.request.query_params.get('to_date', None)
        search_keyword = self.request.query_params.get('search_keyword', None)
        company = self.request.query_params.get('company', None)
        hod = self.request.query_params.get('hod', None)
        employee = self.request.query_params.get('employee', None)
        reporting_head = self.request.query_params.get('reporting_head', None)

        filter = dict()
        # if start_date and end_date:
        #     start_object = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        #     end_object = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        #     filter['joining_date__date__gte'] = start_object.date()
        #     filter['joining_date__date__lte'] = end_object.date()

        if field_name and order_by:
            if field_name == 'employee_name' and order_by == 'asc':
                sort_field = 'cu_user__first_name'
            if field_name == 'employee_name' and order_by == 'desc':
                sort_field = '-cu_user__first_name'
            if field_name == 'department_name' and order_by == 'asc':
                sort_field = 'department__cd_name'
            if field_name == 'department_name' and order_by == 'desc':
                sort_field = '-department__cd_name'
            if field_name == 'designation_name' and order_by == 'asc':
                sort_field = 'designation__cod_name'
            if field_name == 'designation_name' and order_by == 'desc':
                sort_field = '-designation__cod_name'
            if field_name == 'company' and order_by == 'asc':
                sort_field = 'company__coc_name'
            if field_name == 'company' and order_by == 'desc':
                sort_field = '-company__coc_name'
            if field_name == 'hod_name' and order_by == 'asc':
                sort_field = 'hod__first_name'
            if field_name == 'hod_name' and order_by == 'desc':
                sort_field = '-hod__first_name'
            if field_name == 'reporting_head_name' and order_by == 'asc':
                sort_field = 'reporting_head__first_name'
            if field_name == 'reporting_head_name' and order_by == 'desc':
                sort_field = '-reporting_head__first_name'
            if field_name == 'joining_date' and order_by == 'asc':
                sort_field = 'joining_date'
            if field_name == 'joining_date' and order_by == 'desc':
                sort_field = '-joining_date'
            if field_name == 'emp_code' and order_by == 'asc':
                sort_field = 'cu_emp_code'
            if field_name == 'emp_code' and order_by == 'desc':
                sort_field = '-cu_emp_code'
            if field_name == 'sap_personnel_no' and order_by == 'asc':
                sort_field = 'sap_personnel_no'
            if field_name == 'sap_personnel_no' and order_by == 'desc':
                sort_field = '-sap_personnel_no'

        if department:
            filter['department_id'] = department
        if designation:
            filter['designation_id'] = designation
        if company:
            filter['company_id'] = company
        if hod:
            filter['hod_id'] = hod
        if employee:
            filter['id'] = employee
        if reporting_head:
            filter['reporting_head__id'] = reporting_head

        if search_keyword:
            search_keyword = search_keyword.lstrip()
            search_keyword = search_keyword.rstrip()
            f_name = search_keyword.split(' ')[0]
            l_name = ' '.join(search_keyword.split(' ')[1:])
            print(f_name, l_name)
            if l_name:
                queryset = self.queryset.filter(~Q(cu_punch_id='#N/A'), Q(cu_user__first_name__icontains=f_name),
                                                Q(cu_user__last_name__icontains=l_name), termination_date__isnull=True,
                                                cu_is_deleted=False,

                                                **filter).order_by(sort_field)

            else:

                queryset = self.queryset.filter(~Q(cu_punch_id='#N/A'), Q(cu_user__first_name__icontains=f_name) |
                                                Q(cu_user__last_name__icontains=f_name), termination_date__isnull=True,
                                                cu_is_deleted=False,

                                                **filter).order_by(sort_field)
        else:
            queryset = self.queryset.filter(~Q(cu_punch_id='#N/A'), termination_date__isnull=True, cu_is_deleted=False,
                                            **filter).order_by(sort_field)

        return queryset

    @response_modify_decorator_list_or_get_after_execution_for_onoff_pagination
    def get(self, request, *args, **kwargs):
        response = super(PendingThreeMonthsProbatinEmployeeListV2View, self).get(self, request, args, kwargs)
        data_dict = dict()
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        if 'results' in response.data:
            if start_date and end_date:
                from datetime import datetime
                start_object = datetime.strptime(start_date, '%Y-%m-%d')
                delta = timedelta(days=1)
                end_object = datetime.strptime(end_date, '%Y-%m-%d')
                response.data['results'] = list(filter(
                    lambda i: i['mail_shoot_date'] >= start_object and i['mail_shoot_date'] <= end_object + delta,
                    response.data['results']))
                print(len(response.data['results']))

        if 'results' in response.data:
            if field_name and order_by:
                if field_name == 'company' and order_by == 'asc':
                    response.data['results'] = sorted(response.data['results'], key=lambda i: i['company_name'])
                if field_name == 'company' and order_by == 'desc':
                    response.data['results'] = sorted(response.data['results'], key=lambda i: i['company_name'],
                                                      reverse=True)
                # probation_date
                if field_name == 'probation_date' and order_by == 'asc':
                    response.data['results'] = sorted(response.data['results'], key=lambda i: i['probation_date'])
                if field_name == 'probation_date' and order_by == 'desc':
                    response.data['results'] = sorted(response.data['results'], key=lambda i: i['probation_date'],
                                                      reverse=True)
                # mail_shoot_date
                if field_name == 'mail_shoot_date' and order_by == 'asc':
                    response.data['results'] = sorted(response.data['results'], key=lambda i: i['mail_shoot_date'])
                if field_name == 'mail_shoot_date' and order_by == 'desc':
                    response.data['results'] = sorted(response.data['results'], key=lambda i: i['mail_shoot_date'],
                                                      reverse=True)
            data_dict = response.data

        else:
            if field_name and order_by:
                if field_name == 'company' and order_by == 'asc':
                    response.data = sorted(response.data, key=lambda i: i['company_name'])
                if field_name == 'company' and order_by == 'desc':
                    response.data = sorted(response.data, key=lambda i: i['company_name'], reverse=True)
                if field_name == 'probation_date' and order_by == 'asc':
                    response.data = sorted(response.data, key=lambda i: i['probation_date'])
                if field_name == 'probation_date' and order_by == 'desc':
                    response.data = sorted(response.data, key=lambda i: i['probation_date'], reverse=True)

                if field_name == 'mail_shoot_date' and order_by == 'asc':
                    response.data = sorted(response.data, key=lambda i: i['mail_shoot_date'])
                if field_name == 'mail_shoot_date' and order_by == 'desc':
                    response.data = sorted(response.data, key=lambda i: i['mail_shoot_date'], reverse=True)
            data_dict['results'] = response.data

        response.data = data_dict

        return Response({**response.data, 'request_status': 1, 'msg': settings.MSG_SUCCESS})

# submission pending reminder by hr

class PendingThreeMonthSubmissionReminderFromHr(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def send_reminder_for_probation(self, usr_obj, base64_id, cc,request=None):
        user_email = usr_obj.employee.cu_user.cu_alt_email_id
        second_name = usr_obj.employee.last_name
        # final_sub = obj.employee.get_full_name() + ' ' + obj.employee.designation.cod_name
        # employee_name = usr_obj.employee.get_full_name()
        # designation = usr_obj.employee.cu_user.designation.cod_name
        # final_str_for_subject_line = str(employee_name) + ',' + str(designation)
        print(user_email)
        server_url = settings.SERVER_URL
        server_url = server_url.split(':' + server_url.split(':')[-1])[0]
        if user_email:
            mail_data = {
                "second_name": second_name,
                "link": "http://3.7.231.128/hrms" + "/#/employee-probation-form/" + base64_id
            }
            from global_function import send_mail

            send_mail('HRMS-3P-R-RH', user_email, mail_data, cc)


    def post(self, request, *args, **kwargs):
        employee_id = request.data['employee_id']
        cc = request.data['cc']
        if cc:
            cc = cc.split(',')
        else:
            cc = cc
        import base64
        obj = HrmsThreeMonthsProbationReviewForm.objects.get(employee__cu_user__id=employee_id)
        print(obj)
        sample_string = str(obj.id)
        sample_string_bytes = sample_string.encode("ascii")
        base64_bytes = base64.b64encode(sample_string_bytes)
        print(base64_bytes)
        base64_id = base64_bytes.decode("ascii")
        print(base64_id)
        self.send_reminder_for_probation(obj, base64_id, cc, request)

        return Response({'request_status': 1, 'msg': 'Success'})


class PendingProbationThreeMonthsAddView(generics.RetrieveUpdateAPIView):
    # permission_classes = [IsAuthenticated]
    permission_classes = [AllowAny]
    # authentication_classes = [TokenAuthentication]
    queryset = HrmsThreeMonthsProbationReviewForm.objects.filter(is_deleted=False)
    serializer_class = PendingProbationAddSerializer

    def get_queryset(self):
        login_user = self.request.user.id
        user_id = self.kwargs['pk']
        print(user_id)
        queryset = self.queryset.filter(id=user_id)
        return queryset

    @response_modify_decorator_get_after_execution
    def get(self, request, *args, **kwargs):
        response = super(PendingProbationThreeMonthsAddView, self).get(self, request, args, kwargs)
        return response


class PendingProbationThreeMonthsReviewAddView(generics.RetrieveUpdateAPIView):
    # permission_classes = [IsAuthenticated]
    permission_classes = [AllowAny]
    # authentication_classes = [TokenAuthentication]
    queryset = HrmsThreeMonthsProbationReviewForApproval.objects.filter(is_deleted=False)
    serializer_class = PendingProbationReviewAddSerializer

    def get_queryset(self):
        login_user = self.request.user.id
        user_id = self.kwargs['pk']
        print(user_id)
        queryset = self.queryset.filter(id=user_id)
        return queryset

    @response_modify_decorator_get_after_execution
    def get(self, request, *args, **kwargs):
        response = super(PendingProbationThreeMonthsReviewAddView, self).get(self, request, args, kwargs)
        return response


class PendingThreeMonthsProbatinReviewListV2View(generics.ListAPIView):
    '''
        Reason : Get Active User List in Excel File
        Author :Swarup Adhikary
        Line number:  3449 - 3465
        Date : 03/09/2020
    '''
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreUserDetail.objects.filter(cu_user__is_superuser=False, cu_user__is_active=True)
    serializer_class = PendingProbationReportingHeadListSerializerv2
    pagination_class = OnOffPagination

    def get_queryset(self):
        '''
            eleminate login user on employee list added by Rupam Hazra Line number 458 - 459
        '''
        login_user = self.request.user.id
        from datetime import datetime
        date = datetime.now()
        eight_days_before_date = date - timedelta(8)
        pending_probation_review_obj = HrmsThreeMonthsProbationReviewForApproval.objects.filter(submission_pending=True,
                                                                                                first_reminder_date__lte=eight_days_before_date).values_list(
            'employee_form__employee', flat=True)
        print(pending_probation_review_obj)
        pending_probation_obj = list(pending_probation_review_obj)
        print(pending_probation_obj)
        self.queryset = self.queryset.filter(cu_user__in=pending_probation_obj)
        # self.queryset = self.queryset.filter(cu_user__in=pending_probation_obj)

        sort_field = '-id'
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        department = self.request.query_params.get('department', None)
        designation = self.request.query_params.get('designation', None)
        start_date = self.request.query_params.get('from_date', None)
        end_date = self.request.query_params.get('to_date', None)
        search_keyword = self.request.query_params.get('search_keyword', None)
        company = self.request.query_params.get('company', None)
        hod = self.request.query_params.get('hod', None)
        employee = self.request.query_params.get('employee', None)
        reporting_head = self.request.query_params.get('reporting_head', None)

        filter = dict()
        # if start_date and end_date:
        #     start_object = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        #     end_object = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        #     filter['joining_date__date__gte'] = start_object.date()
        #     filter['joining_date__date__lte'] = end_object.date()

        if field_name and order_by:
            if field_name == 'employee_name' and order_by == 'asc':
                sort_field = 'cu_user__first_name'
            if field_name == 'employee_name' and order_by == 'desc':
                sort_field = '-cu_user__first_name'
            if field_name == 'department_name' and order_by == 'asc':
                sort_field = 'department__cd_name'
            if field_name == 'department_name' and order_by == 'desc':
                sort_field = '-department__cd_name'
            if field_name == 'designation_name' and order_by == 'asc':
                sort_field = 'designation__cod_name'
            if field_name == 'designation_name' and order_by == 'desc':
                sort_field = '-designation__cod_name'
            if field_name == 'company' and order_by == 'asc':
                sort_field = 'company__coc_name'
            if field_name == 'company' and order_by == 'desc':
                sort_field = '-company__coc_name'
            if field_name == 'hod_name' and order_by == 'asc':
                sort_field = 'hod__first_name'
            if field_name == 'hod_name' and order_by == 'desc':
                sort_field = '-hod__first_name'
            if field_name == 'reporting_head_name' and order_by == 'asc':
                sort_field = 'reporting_head__first_name'
            if field_name == 'reporting_head_name' and order_by == 'desc':
                sort_field = '-reporting_head__first_name'
            if field_name == 'joining_date' and order_by == 'asc':
                sort_field = 'joining_date'
            if field_name == 'joining_date' and order_by == 'desc':
                sort_field = '-joining_date'
            if field_name == 'emp_code' and order_by == 'asc':
                sort_field = 'cu_emp_code'
            if field_name == 'emp_code' and order_by == 'desc':
                sort_field = '-cu_emp_code'
            if field_name == 'sap_personnel_no' and order_by == 'asc':
                sort_field = 'sap_personnel_no'
            if field_name == 'sap_personnel_no' and order_by == 'desc':
                sort_field = '-sap_personnel_no'

        if department:
            filter['department_id'] = department
        if designation:
            filter['designation_id'] = designation
        if company:
            filter['company__id'] = company
        if hod:
            filter['hod_id'] = hod
        if employee:
            filter['id'] = employee
        if reporting_head:
            filter['reporting_head__id'] = reporting_head

        if search_keyword:
            search_keyword = search_keyword.lstrip()
            search_keyword = search_keyword.rstrip()
            f_name = search_keyword.split(' ')[0]
            l_name = ' '.join(search_keyword.split(' ')[1:])
            print(f_name, l_name)
            if l_name:
                queryset = self.queryset.filter(~Q(cu_punch_id='#N/A'), Q(cu_user__first_name__icontains=f_name),
                                                Q(cu_user__last_name__icontains=l_name), termination_date__isnull=True,
                                                cu_is_deleted=False,

                                                **filter).order_by(sort_field)

            else:

                queryset = self.queryset.filter(~Q(cu_punch_id='#N/A'), Q(cu_user__first_name__icontains=f_name) |
                                                Q(cu_user__last_name__icontains=f_name), termination_date__isnull=True,
                                                cu_is_deleted=False,

                                                **filter).order_by(sort_field)

        else:
            queryset = self.queryset.filter(~Q(cu_punch_id='#N/A'), termination_date__isnull=True, cu_is_deleted=False,
                                            **filter).order_by(sort_field)

        return queryset

    @response_modify_decorator_list_or_get_after_execution_for_onoff_pagination
    def get(self, request, *args, **kwargs):
        response = super(PendingThreeMonthsProbatinReviewListV2View, self).get(self, request, args, kwargs)
        data_dict = dict()
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        if 'results' in response.data:
            if start_date and end_date:
                from datetime import datetime
                start_object = datetime.strptime(start_date, '%Y-%m-%d')
                delta = timedelta(days=1)
                end_object = datetime.strptime(end_date, '%Y-%m-%d')
                response.data['results'] = list(
                    filter(
                        lambda i: i['mail_shoot_date'] >= start_object and i['mail_shoot_date'] <= end_object + delta,
                        response.data['results']))
                print(len(response.data['results']))

        if 'results' in response.data:
            if field_name and order_by:
                if field_name == 'company' and order_by == 'asc':
                    response.data['results'] = sorted(response.data['results'], key=lambda i: i['company_name'])
                if field_name == 'company' and order_by == 'desc':
                    response.data['results'] = sorted(response.data['results'], key=lambda i: i['company_name'],
                                                      reverse=True)
                # probation_date
                if field_name == 'probation_date' and order_by == 'asc':
                    response.data['results'] = sorted(response.data['results'], key=lambda i: i['probation_date'])
                if field_name == 'probation_date' and order_by == 'desc':
                    response.data['results'] = sorted(response.data['results'], key=lambda i: i['probation_date'],
                                                      reverse=True)
                # mail_shoot_date
                if field_name == 'mail_shoot_date' and order_by == 'asc':
                    response.data['results'] = sorted(response.data['results'], key=lambda i: i['mail_shoot_date'])
                if field_name == 'mail_shoot_date' and order_by == 'desc':
                    response.data['results'] = sorted(response.data['results'], key=lambda i: i['mail_shoot_date'],
                                                      reverse=True)

            data_dict = response.data

        else:
            if field_name and order_by:
                if field_name == 'company' and order_by == 'asc':
                    response.data = sorted(response.data, key=lambda i: i['company_name'])
                if field_name == 'company' and order_by == 'desc':
                    response.data = sorted(response.data, key=lambda i: i['company_name'], reverse=True)

                if field_name == 'probation_date' and order_by == 'asc':
                    response.data = sorted(response.data, key=lambda i: i['probation_date'])
                if field_name == 'probation_date' and order_by == 'desc':
                    response.data = sorted(response.data, key=lambda i: i['probation_date'], reverse=True)

                if field_name == 'mail_shoot_date' and order_by == 'asc':
                    response.data = sorted(response.data, key=lambda i: i['mail_shoot_date'])
                if field_name == 'mail_shoot_date' and order_by == 'desc':
                    response.data = sorted(response.data, key=lambda i: i['mail_shoot_date'], reverse=True)
            data_dict['results'] = response.data

        response.data = data_dict

        return Response({**response.data, 'request_status': 1, 'msg': settings.MSG_SUCCESS})


# review reminder by hr

class PendingThreeMonthReviewSubmissionReminderFromHr(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def send_reminder_for_probation_review(self, usr_obj, base64_id, cc, request=None):
        user_email = usr_obj.employee_form.employee.cu_user.reporting_head.cu_user.cu_alt_email_id
        second_name = usr_obj.employee_form.employee.cu_user.reporting_head.last_name
        designation = usr_obj.employee_form.employee.cu_user.designation.cod_name if usr_obj.employee_form.employee.cu_user.designation else None
        employee_name = usr_obj.employee_form.employee.get_full_name()
        final_sub = usr_obj.employee_form.employee.get_full_name() + ',' + usr_obj.employee_form.employee.cu_user.designation.cod_name
        print(user_email)
        server_url = settings.SERVER_URL
        server_url = server_url.split(':' + server_url.split(':')[-1])[0]
        if user_email:
            mail_data = {
                "second_name": second_name,
                "employee_name": employee_name,
                "designation": designation,
                # "mail_body": mail_body,
                "link": "http://3.7.231.128/hrms" + "/#/probation-form-review/" + base64_id,
            }
            from global_function import send_mail

            send_mail('HRMS-3P-RR-RH', user_email, mail_data, cc, final_sub=final_sub)


    def post(self, request, *args, **kwargs):
        employee_id = request.data['employee_id']
        cc = request.data['cc']
        if cc:
            cc = cc.split(',')
        else:
            cc = cc
        # mail_subject = request.data['mail_subject']
        # mail_body = request.data['mail_body']
        # employee_mail = TCoreUserDetail.objects.get(cu_user_id=employee_id).cu_alt_email_id


        # print(employee_id, Cc,employee_mail)
        import base64
        obj = HrmsThreeMonthsProbationReviewForApproval.objects.get(employee_form__employee__cu_user__id=employee_id)
        print(obj)
        sample_string = str(obj.id)
        sample_string_bytes = sample_string.encode("ascii")
        base64_bytes = base64.b64encode(sample_string_bytes)
        print(base64_bytes)
        base64_id = base64_bytes.decode("ascii")
        print(base64_id)
        self.send_reminder_for_probation_review(obj, base64_id, cc, request)

        return Response({'request_status': 1, 'msg': 'Success'})



# three months reminder cron job
class EmployeeProbationReminder(APIView):
    permission_classes = [AllowAny]

    def send_reminder_for_probation(self, usr_obj, base64_id, request=None):
        user_email = usr_obj.employee.cu_user.cu_alt_email_id
        second_name = usr_obj.employee.last_name
        # employee_name = usr_obj.employee.get_full_name()
        # designation = usr_obj.employee.cu_user.designation.cod_name
        # final_str_for_subject_line = str(employee_name) + ',' + str(designation)
        print(user_email)
        server_url = settings.SERVER_URL
        server_url = server_url.split(':' + server_url.split(':')[-1])[0]
        if user_email:
            mail_data = {
                "second_name": second_name,
                # "link": "http://localhost:4200/#/employee-probation-form/" + base64_id,
                "link": "http://3.7.231.128/hrms" + "/#/employee-probation-form/" + base64_id
            }
            from global_function import send_mail

            send_mail('HRMS-3P-1R', user_email, mail_data)

    def send_next_reminder_for_probation(self, usr_obj, base64_id, reminder_state, request=None):
        user_email = usr_obj.employee.cu_user.cu_alt_email_id
        second_name = usr_obj.employee.last_name
        final_str_for_subject_line = "Reminder " + ' ' + str(reminder_state)
        print(user_email)
        server_url = settings.SERVER_URL
        server_url = server_url.split(':' + server_url.split(':')[-1])[0]
        if user_email:
            mail_data = {
                "second_name": second_name,
                "link": "http://3.7.231.128/hrms" + "/#/employee-probation-form/" + base64_id,
            }
            from global_function import send_mail

            send_mail('HRMS-3P-R', user_email, mail_data, final_sub=final_str_for_subject_line)

    def send_next_reminder_for_probation_to_rh(self, usr_obj, base64_id, reminder_state, request):
        user_email = usr_obj.employee_form.employee.cu_user.reporting_head.cu_user.cu_alt_email_id
        second_name = usr_obj.employee_form.employee.cu_user.reporting_head.last_name
        employee_name = usr_obj.employee_form.employee.get_full_name()
        designation = usr_obj.employee_form.employee.cu_user.designation.cod_name
        final_str_for_subject_line = str(employee_name) + ',' + str(designation) + ':' + "Reminder " + ' ' + str(
            reminder_state)
        print(user_email)
        server_url = settings.SERVER_URL
        server_url = server_url.split(':' + server_url.split(':')[-1])[0]
        if user_email:
            mail_data = {
                "employee_name": employee_name,
                "designation": designation,
                "second_name": second_name,
                "link": "http://3.7.231.128/hrms" + "/#/probation-form-review/" + base64_id,
            }
            from global_function import send_mail

            send_mail('HRMS-3P-RH-R', user_email, mail_data, final_sub=final_str_for_subject_line)

    def get(self, request, *args, **kwargs):
        from datetime import datetime
        date = datetime.now()
        search_join_date = date - relativedelta(months=+3)
        date_before_10 = search_join_date - timedelta(10)
        print(search_join_date)
        alredy_probation_user = HrmsThreeMonthsProbationReviewForm.objects.filter(submission_pending=True).values_list(
            'employee')
        alredy_probation_user = list(alredy_probation_user)
        import base64
        users_obj = TCoreUserDetail.objects.filter(~Q(cu_user__in=alredy_probation_user),
                                                   id__in=[4496, 4497, 4498, 4499, 4356], is_confirm=False,
                                                   joining_date__lte=search_join_date.date(),
                                                   joining_date__gte=date_before_10)
        # print(users_obj.count())
        for each in users_obj:
            print(each.cu_alt_email_id)
            obj, create = HrmsThreeMonthsProbationReviewForm.objects.get_or_create(employee=each.cu_user,
                                                                                   reminder_state=0,
                                                                                   latest_reminder_date=date,
                                                                                   first_reminder_date=date)
            print(obj, create)
            sample_string = str(obj.id)
            sample_string_bytes = sample_string.encode("ascii")

            base64_bytes = base64.b64encode(sample_string_bytes)
            print(base64_bytes)
            base64_id = base64_bytes.decode("ascii")
            print(base64_id)
            # base64_bytes = base64_id.encode("ascii")
            #
            # sample_string_bytes = base64.b64decode(base64_bytes)
            # sample_string = sample_string_bytes.decode("ascii")
            # print(sample_string)
            self.send_reminder_for_probation(obj, base64_id, request)
        # second reminder for three month probation
        two_days_before_date = date - timedelta(2)
        employee_for_2nd_reminder = HrmsThreeMonthsProbationReviewForm.objects.filter(
            first_reminder_date__lte=two_days_before_date,
            reminder_state=0, submission_pending=True)
        for each in employee_for_2nd_reminder:
            sample_string = str(each.id)
            sample_string_bytes = sample_string.encode("ascii")

            base64_bytes = base64.b64encode(sample_string_bytes)
            # print(base64_bytes)
            base64_id = base64_bytes.decode("ascii")
            # print(base64_id)
            self.send_next_reminder_for_probation(each, base64_id, str(1), request)
            HrmsThreeMonthsProbationReviewForm.objects.filter(id=each.id).update(reminder_state=1,
                                                                                 latest_reminder_date=date)

        # third reminder for three month probation
        Four_days_before_date = date - timedelta(4)
        employee_for_3rd_reminder = HrmsThreeMonthsProbationReviewForm.objects.filter(
            first_reminder_date__lte=Four_days_before_date,
            reminder_state=1, submission_pending=True)
        for each in employee_for_3rd_reminder:
            sample_string = str(each.id)
            sample_string_bytes = sample_string.encode("ascii")

            base64_bytes = base64.b64encode(sample_string_bytes)
            # print(base64_bytes)
            base64_id = base64_bytes.decode("ascii")
            print(base64_id)
            self.send_next_reminder_for_probation(each, base64_id, str(2), request)
            HrmsThreeMonthsProbationReviewForm.objects.filter(id=each.id).update(reminder_state=2,
                                                                                 latest_reminder_date=date)
        # fourth reminder for the employee
        eight_days_before_date = date - timedelta(6)
        employee_for_rm_reminder = HrmsThreeMonthsProbationReviewForm.objects.filter(
            first_reminder_date__lte=eight_days_before_date,
            reminder_state=2, submission_pending=True)
        for each in employee_for_rm_reminder:
            sample_string = str(each.id)
            sample_string_bytes = sample_string.encode("ascii")

            base64_bytes = base64.b64encode(sample_string_bytes)
            print(base64_bytes)
            base64_id = base64_bytes.decode("ascii")
            print(base64_id)
            self.send_next_reminder_for_probation(each, base64_id, str(3), request)
            HrmsThreeMonthsProbationReviewForm.objects.filter(id=each.id).update(reminder_state=3,
                                                                                 latest_reminder_date=date)
        # fourth reminder for the employee
        eight_days_before_date = date - timedelta(8)
        employee_for_rm_reminder = HrmsThreeMonthsProbationReviewForm.objects.filter(
            first_reminder_date__lte=eight_days_before_date,
            reminder_state=3, submission_pending=True)
        for each in employee_for_rm_reminder:
            user_email = each.employee.cu_user.reporting_head.cu_user.cu_alt_email_id
            second_name = each.employee.cu_user.reporting_head.last_name
            employee_name = each.employee.get_full_name()
            designation = each.employee.cu_user.designation.cod_name

            if user_email:
                mail_data = {
                    "employee_name": employee_name,
                    "designation": designation,
                    "second_name": second_name
                }
                from global_function import send_mail

                send_mail('HRMS-3P-RH', user_email, mail_data)

        # second reminder for the reporting head
        two_days_before_date = date - timedelta(2)
        reporting_head_for_2nd_reminder = HrmsThreeMonthsProbationReviewForApproval.objects.filter(
            first_reminder_date__lte=two_days_before_date,
            reminder_state=0, submission_pending=True)
        for each in reporting_head_for_2nd_reminder:
            sample_string = str(each.id)
            sample_string_bytes = sample_string.encode("ascii")

            base64_bytes = base64.b64encode(sample_string_bytes)
            # print(base64_bytes)
            base64_id = base64_bytes.decode("ascii")
            # print(base64_id)
            self.send_next_reminder_for_probation_to_rh(each, base64_id, str(1), request)
            HrmsThreeMonthsProbationReviewForApproval.objects.filter(id=each.id).update(reminder_state=1,
                                                                                        reminder_date=date)

        # third reminder for the reporting head
        four_days_before_date = date - timedelta(4)
        reporting_head_for_3nd_reminder = HrmsThreeMonthsProbationReviewForApproval.objects.filter(
            first_reminder_date__lte=four_days_before_date,
            reminder_state=1, submission_pending=True)
        for each in reporting_head_for_3nd_reminder:
            sample_string = str(each.id)
            sample_string_bytes = sample_string.encode("ascii")

            base64_bytes = base64.b64encode(sample_string_bytes)
            # print(base64_bytes)
            base64_id = base64_bytes.decode("ascii")
            # print(base64_id)
            self.send_next_reminder_for_probation_to_rh(each, base64_id, str(2), request)
            HrmsThreeMonthsProbationReviewForApproval.objects.filter(id=each.id).update(reminder_state=2,
                                                                                        reminder_date=date)

        # Fourth reminder for the reporting head
        six_days_before_date = date - timedelta(6)
        reporting_head_for_3nd_reminder = HrmsThreeMonthsProbationReviewForApproval.objects.filter(
            first_reminder_date__lte=six_days_before_date,
            reminder_state=2, submission_pending=True)
        for each in reporting_head_for_3nd_reminder:
            sample_string = str(each.id)
            sample_string_bytes = sample_string.encode("ascii")

            base64_bytes = base64.b64encode(sample_string_bytes)
            # print(base64_bytes)
            base64_id = base64_bytes.decode("ascii")
            # print(base64_id)
            self.send_next_reminder_for_probation_to_rh(each, base64_id, str(2), request)
            HrmsThreeMonthsProbationReviewForApproval.objects.filter(id=each.id).update(reminder_state=3,
                                                                                        reminder_date=date)

        return Response({'request_status': 1, 'msg': 'Success'})


# three month confirmation report
class ThreeMonthsProbationConfirmationReportView(generics.ListAPIView):
    '''
        Reason : Get Active User List in Excel File
        Author :Swarup Adhikary
        Line number:  3449 - 3465
        Date : 03/09/2020
    '''
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreUserDetail.objects.filter(cu_user__is_superuser=False, cu_user__is_active=True)
    serializer_class = CompletedThreeMonthProbationReportSerializer
    pagination_class = OnOffPagination

    def get_queryset(self):

        pending_probation_review_obj = HrmsThreeMonthsProbationReviewForApproval.objects.filter(
            submission_pending=False).values_list('employee_form__employee', flat=True)
        print(pending_probation_review_obj)
        pending_probation_obj = list(pending_probation_review_obj)
        print(pending_probation_obj)
        print(self.queryset.filter(cu_user__id__in=pending_probation_obj))
        self.queryset = self.queryset.filter(cu_user__in=pending_probation_obj)

        sort_field = '-id'
        print(self.queryset.count())
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        department = self.request.query_params.get('department', None)
        designation = self.request.query_params.get('designation', None)
        start_date = self.request.query_params.get('from_date', None)
        end_date = self.request.query_params.get('to_date', None)
        search_keyword = self.request.query_params.get('search_keyword', None)
        company = self.request.query_params.get('company', None)
        hod = self.request.query_params.get('hod', None)
        employee = self.request.query_params.get('employee', None)
        reporting_head = self.request.query_params.get('reporting_head', None)

        filter = dict()

        if field_name and order_by:
            if field_name == 'employee_name' and order_by == 'asc':
                sort_field = 'cu_user__first_name'
            if field_name == 'employee_name' and order_by == 'desc':
                sort_field = '-cu_user__first_name'
            if field_name == 'department_name' and order_by == 'asc':
                sort_field = 'department__cd_name'
            if field_name == 'department_name' and order_by == 'desc':
                sort_field = '-department__cd_name'
            if field_name == 'designation_name' and order_by == 'asc':
                sort_field = 'designation__cod_name'
            if field_name == 'designation_name' and order_by == 'desc':
                sort_field = '-designation__cod_name'
            if field_name == 'company' and order_by == 'asc':
                sort_field = 'company__coc_name'
            if field_name == 'company' and order_by == 'desc':
                sort_field = '-company__coc_name'
            if field_name == 'hod_name' and order_by == 'asc':
                sort_field = 'hod__first_name'
            if field_name == 'hod_name' and order_by == 'desc':
                sort_field = '-hod__first_name'
            if field_name == 'reporting_head_name' and order_by == 'asc':
                sort_field = 'reporting_head__first_name'
            if field_name == 'reporting_head_name' and order_by == 'desc':
                sort_field = '-reporting_head__first_name'
            if field_name == 'joining_date' and order_by == 'asc':
                sort_field = 'joining_date'
            if field_name == 'joining_date' and order_by == 'desc':
                sort_field = '-joining_date'
            if field_name == 'emp_code' and order_by == 'asc':
                sort_field = 'cu_emp_code'
            if field_name == 'emp_code' and order_by == 'desc':
                sort_field = '-cu_emp_code'
            if field_name == 'sap_personnel_no' and order_by == 'asc':
                sort_field = 'sap_personnel_no'
            if field_name == 'sap_personnel_no' and order_by == 'desc':
                sort_field = '-sap_personnel_no'

        if department:
            filter['department_id'] = department
        if designation:
            filter['designation_id'] = designation
        if company:
            filter['company__id'] = company
        if hod:
            filter['hod_id'] = hod
        if employee:
            filter['id'] = employee
        if reporting_head:
            filter['reporting_head__id'] = reporting_head

        if search_keyword:
            search_keyword = search_keyword.lstrip()
            search_keyword = search_keyword.rstrip()
            f_name = search_keyword.split(' ')[0]
            l_name = ' '.join(search_keyword.split(' ')[1:])
            print(f_name, l_name)
            if l_name:
                queryset = self.queryset.filter(~Q(cu_punch_id='#N/A'), Q(cu_user__first_name__icontains=f_name),
                                                Q(cu_user__last_name__icontains=l_name), termination_date__isnull=True,
                                                cu_is_deleted=False,
                                                **filter).order_by(sort_field)

            else:

                queryset = self.queryset.filter(~Q(cu_punch_id='#N/A'), Q(cu_user__first_name__icontains=f_name) |
                                                Q(cu_user__last_name__icontains=f_name), termination_date__isnull=True,
                                                cu_is_deleted=False,

                                                **filter).order_by(sort_field)
        else:
            print("in else")
            print(self.queryset)
            queryset = self.queryset.filter(~Q(cu_punch_id='#N/A'), termination_date__isnull=True, cu_is_deleted=False,
                                            **filter).order_by(sort_field)

        return queryset

    @response_modify_decorator_list_or_get_after_execution_for_onoff_pagination
    def get(self, request, *args, **kwargs):
        response = super(ThreeMonthsProbationConfirmationReportView, self).get(self, request, args, kwargs)
        data_dict = dict()
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        if 'results' in response.data:
            if start_date and end_date:
                from datetime import datetime
                start_object = datetime.strptime(start_date, '%Y-%m-%d')
                delta = timedelta(days=1)
                end_object = datetime.strptime(end_date, '%Y-%m-%d')
                response.data['results'] = list(
                    filter(lambda i: i['completion_3rd_month_review_date'] >= start_object and i[
                        'completion_3rd_month_review_date'] <= end_object + delta,
                           response.data['results']))
                print(len(response.data['results']))

        if 'results' in response.data:
            if field_name and order_by:
                if field_name == 'company' and order_by == 'asc':
                    response.data['results'] = sorted(response.data['results'], key=lambda i: i['company_name'])
                if field_name == 'company' and order_by == 'desc':
                    response.data['results'] = sorted(response.data['results'], key=lambda i: i['company_name'],
                                                      reverse=True)
                if field_name == 'probation_date' and order_by == 'asc':
                    response.data['results'] = sorted(response.data['results'], key=lambda i: i['probation_date'])
                if field_name == 'probation_date' and order_by == 'desc':
                    response.data['results'] = sorted(response.data['results'], key=lambda i: i['probation_date'],
                                                      reverse=True)
                if field_name == 'mail_shoot_date' and order_by == 'asc':
                    response.data['results'] = sorted(response.data['results'], key=lambda i: i['mail_shoot_date'])
                if field_name == 'mail_shoot_date' and order_by == 'desc':
                    response.data['mail_shoot_date'] = sorted(response.data['results'],
                                                              key=lambda i: i['mail_shoot_date'],
                                                              reverse=True)
            data_dict = response.data

        else:
            if field_name and order_by:
                if field_name == 'company' and order_by == 'asc':
                    response.data = sorted(response.data, key=lambda i: i['company_name'])
                if field_name == 'company' and order_by == 'desc':
                    response.data = sorted(response.data, key=lambda i: i['company_name'], reverse=True)

                if field_name == 'probation_date' and order_by == 'asc':
                    response.data = sorted(response.data, key=lambda i: i['probation_date'])
                if field_name == 'probation_date' and order_by == 'desc':
                    response.data = sorted(response.data, key=lambda i: i['probation_date'], reverse=True)

                if field_name == 'mail_shoot_date' and order_by == 'asc':
                    response.data = sorted(response.data, key=lambda i: i['mail_shoot_date'])
                if field_name == 'mail_shoot_date' and order_by == 'desc':
                    response.data = sorted(response.data, key=lambda i: i['mail_shoot_date'], reverse=True)
            data_dict['results'] = response.data

        response.data = data_dict

        return Response({**response.data, 'request_status': 1, 'msg': settings.MSG_SUCCESS})


# five month probation add view
class PendingFiveMonthsProbationAddView(generics.RetrieveUpdateAPIView):
    permission_classes = [AllowAny]
    queryset = HrmsFiveMonthsProbationReviewForm.objects.filter(is_deleted=False)
    serializer_class = PendingFiveMonthsProbationAddSerializer

    def get_queryset(self):
        user_id = self.kwargs['pk']
        print(user_id)
        queryset = self.queryset.filter(id=user_id)
        return queryset

    @response_modify_decorator_get_after_execution
    def get(self, request, *args, **kwargs):
        response = super(PendingFiveMonthsProbationAddView, self).get(self, request, args, kwargs)
        return response


# five month probation review add
class PendingFiveMonthsProbationReviewAddView(generics.RetrieveUpdateAPIView):
    permission_classes = [AllowAny]
    queryset = HrmsFiveMonthsProbationReviewForApproval.objects.filter(is_deleted=False)
    serializer_class = PendingFiveMonthsProbationReviewAddSerializer

    def get_queryset(self):
        login_user = self.request.user.id
        user_id = self.kwargs['pk']
        print(user_id)
        queryset = self.queryset.filter(id=user_id)
        return queryset

    @response_modify_decorator_get_after_execution
    def get(self, request, *args, **kwargs):
        response = super(__class__, self).get(self, request, *args, **kwargs)
        return response


# five months probation review pending list
class PendingFiveMonthsProbationEmployeeListView(generics.ListAPIView):
    '''
        Reason : Five Month Probation Pending List
        Author :Swarup Adhikary
        Last Update Date : 30/09/2020
    '''
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreUserDetail.objects.filter(cu_user__is_superuser=False, cu_user__is_active=True)
    serializer_class = PendingFiveMonthsProbationEmployeeListSerializer
    pagination_class = OnOffPagination

    def get_queryset(self):
        from datetime import datetime
        date = datetime.now()
        eight_days_before_date = date - timedelta(8)
        pending_probation_obj = HrmsFiveMonthsProbationReviewForm.objects.filter(submission_pending=True,
                                                                                 first_reminder_date__lte=eight_days_before_date).values_list(
            'employee', flat=True)
        print(pending_probation_obj)
        pending_probation_obj = list(pending_probation_obj)
        self.queryset = self.queryset.filter(cu_user__in=pending_probation_obj)

        sort_field = '-id'
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        department = self.request.query_params.get('department', None)
        designation = self.request.query_params.get('designation', None)
        search_keyword = self.request.query_params.get('search_keyword', None)
        company = self.request.query_params.get('company', None)
        hod = self.request.query_params.get('hod', None)
        employee = self.request.query_params.get('employee', None)
        reporting_head = self.request.query_params.get('reporting_head', None)

        filter = dict()

        if field_name and order_by:
            if field_name == 'employee_name' and order_by == 'asc':
                sort_field = 'cu_user__first_name'
            if field_name == 'employee_name' and order_by == 'desc':
                sort_field = '-cu_user__first_name'
            if field_name == 'department_name' and order_by == 'asc':
                sort_field = 'department__cd_name'
            if field_name == 'department_name' and order_by == 'desc':
                sort_field = '-department__cd_name'
            if field_name == 'designation_name' and order_by == 'asc':
                sort_field = 'designation__cod_name'
            if field_name == 'designation_name' and order_by == 'desc':
                sort_field = '-designation__cod_name'
            if field_name == 'company' and order_by == 'asc':
                sort_field = 'company__coc_name'
            if field_name == 'company' and order_by == 'desc':
                sort_field = '-company__coc_name'
            if field_name == 'hod_name' and order_by == 'asc':
                sort_field = 'hod__first_name'
            if field_name == 'hod_name' and order_by == 'desc':
                sort_field = '-hod__first_name'
            if field_name == 'reporting_head_name' and order_by == 'asc':
                sort_field = 'reporting_head__first_name'
            if field_name == 'reporting_head_name' and order_by == 'desc':
                sort_field = '-reporting_head__first_name'
            if field_name == 'joining_date' and order_by == 'asc':
                sort_field = 'joining_date'
            if field_name == 'joining_date' and order_by == 'desc':
                sort_field = '-joining_date'
            if field_name == 'emp_code' and order_by == 'asc':
                sort_field = 'cu_emp_code'
            if field_name == 'emp_code' and order_by == 'desc':
                sort_field = '-cu_emp_code'
            if field_name == 'sap_personnel_no' and order_by == 'asc':
                sort_field = 'sap_personnel_no'
            if field_name == 'sap_personnel_no' and order_by == 'desc':
                sort_field = '-sap_personnel_no'

        if department:
            filter['department_id'] = department
        if designation:
            filter['designation_id'] = designation
        if company:
            filter['company_id'] = company
        if hod:
            filter['hod_id'] = hod
        if employee:
            filter['id'] = employee
        if reporting_head:
            filter['reporting_head__id'] = reporting_head

        if search_keyword:
            search_keyword = search_keyword.lstrip()
            search_keyword = search_keyword.rstrip()
            f_name = search_keyword.split(' ')[0]
            l_name = ' '.join(search_keyword.split(' ')[1:])
            print(f_name, l_name)
            if l_name:
                queryset = self.queryset.filter(~Q(cu_punch_id='#N/A'), Q(cu_user__first_name__icontains=f_name),
                                                Q(cu_user__last_name__icontains=l_name), termination_date__isnull=True,
                                                cu_is_deleted=False,
                                                **filter).order_by(sort_field)

            else:

                queryset = self.queryset.filter(~Q(cu_punch_id='#N/A'), Q(cu_user__first_name__icontains=f_name) |
                                                Q(cu_user__last_name__icontains=f_name), termination_date__isnull=True,
                                                cu_is_deleted=False,

                                                **filter).order_by(sort_field)
        else:
            queryset = self.queryset.filter(~Q(cu_punch_id='#N/A'), termination_date__isnull=True, cu_is_deleted=False,
                                            **filter).order_by(sort_field)

        return queryset

    @response_modify_decorator_list_or_get_after_execution_for_onoff_pagination
    def get(self, request, *args, **kwargs):
        response = super(PendingFiveMonthsProbationEmployeeListView, self).get(self, request, args, kwargs)
        data_dict = dict()
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        if 'results' in response.data:
            if start_date and end_date:
                from datetime import datetime
                start_object = datetime.strptime(start_date, '%Y-%m-%d')
                delta = timedelta(days=1)
                end_object = datetime.strptime(end_date, '%Y-%m-%d')
                response.data['results'] = list(filter(
                    lambda i: i['mail_shoot_date'] >= start_object and i['mail_shoot_date'] <= end_object + delta,
                    response.data['results']))
                print(len(response.data['results']))

        if 'results' in response.data:
            if field_name and order_by:
                if field_name == 'company' and order_by == 'asc':
                    response.data['results'] = sorted(response.data['results'], key=lambda i: i['company_name'])
                if field_name == 'company' and order_by == 'desc':
                    response.data['results'] = sorted(response.data['results'], key=lambda i: i['company_name'],
                                                      reverse=True)
                # probation_date
                if field_name == 'probation_date' and order_by == 'asc':
                    response.data['results'] = sorted(response.data['results'], key=lambda i: i['probation_date'])
                if field_name == 'probation_date' and order_by == 'desc':
                    response.data['results'] = sorted(response.data['results'], key=lambda i: i['probation_date'],
                                                      reverse=True)
                # mail_shoot_date
                if field_name == 'mail_shoot_date' and order_by == 'asc':
                    response.data['results'] = sorted(response.data['results'], key=lambda i: i['mail_shoot_date'])
                if field_name == 'mail_shoot_date' and order_by == 'desc':
                    response.data['results'] = sorted(response.data['results'], key=lambda i: i['mail_shoot_date'],
                                                      reverse=True)
            data_dict = response.data

        else:
            if field_name and order_by:
                if field_name == 'company' and order_by == 'asc':
                    response.data = sorted(response.data, key=lambda i: i['company_name'])
                if field_name == 'company' and order_by == 'desc':
                    response.data = sorted(response.data, key=lambda i: i['company_name'], reverse=True)

                if field_name == 'probation_date' and order_by == 'asc':
                    response.data = sorted(response.data, key=lambda i: i['probation_date'])
                if field_name == 'probation_date' and order_by == 'desc':
                    response.data = sorted(response.data, key=lambda i: i['probation_date'], reverse=True)

                if field_name == 'mail_shoot_date' and order_by == 'asc':
                    response.data = sorted(response.data, key=lambda i: i['mail_shoot_date'])
                if field_name == 'mail_shoot_date' and order_by == 'desc':
                    response.data = sorted(response.data, key=lambda i: i['mail_shoot_date'], reverse=True)
            data_dict['results'] = response.data

        response.data = data_dict

        return Response({**response.data, 'request_status': 1, 'msg': settings.MSG_SUCCESS})

# five month reminder from hr

class PendingFiveMonthSubmissionReminderFromHr(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def send_reminder_for_probation(self, usr_obj, base64_id, cc, request=None):
        user_email = usr_obj.employee.cu_user.cu_alt_email_id
        second_name = usr_obj.employee.last_name
        # final_sub = obj.employee.get_full_name() + ' ' + obj.employee.designation.cod_name
        # employee_name = usr_obj.employee.get_full_name()
        # designation = usr_obj.employee.cu_user.designation.cod_name
        # final_str_for_subject_line = str(employee_name) + ',' + str(designation)
        print(user_email)
        server_url = settings.SERVER_URL
        server_url = server_url.split(':' + server_url.split(':')[-1])[0]
        if user_email:
            mail_data = {
                "second_name": second_name,
                "link": "http://3.7.231.128/hrms" + "/#/final-probation-form/" + base64_id,
            }
            from global_function import send_mail

            send_mail('HRMS-5P-R-RH', user_email, mail_data, cc)


    def post(self, request, *args, **kwargs):
        employee_id = request.data['employee_id']
        cc = request.data['cc']
        if cc:
            cc = cc.split(',')
        else:
            cc = cc
        # mail_subject = request.data['mail_subject']
        # mail_body = request.data['mail_body']
        # employee_mail = TCoreUserDetail.objects.get(cu_user_id=employee_id).cu_alt_email_id


        # print(employee_id, Cc,employee_mail)
        import base64
        obj = HrmsFiveMonthsProbationReviewForm.objects.get(employee__cu_user__id=employee_id)
        print(obj)
        sample_string = str(obj.id)
        sample_string_bytes = sample_string.encode("ascii")
        base64_bytes = base64.b64encode(sample_string_bytes)
        print(base64_bytes)
        base64_id = base64_bytes.decode("ascii")
        print(base64_id)
        self.send_reminder_for_probation(obj, base64_id, cc, request)

        return Response({'request_status': 1, 'msg': 'Success'})



# five months pending probation review listing

class PendingFiveMonthsProbatinReviewListView(generics.ListAPIView):
    '''
        Reason : Pending Review Probation Review
        Author :Swarup Adhikary
        Date : 30/09/2020
    '''
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreUserDetail.objects.filter(cu_user__is_superuser=False, cu_user__is_active=True)
    serializer_class = PendingFiveMonthsProbationReportingHeadListSerializer
    pagination_class = OnOffPagination

    def get_queryset(self):
        from datetime import datetime
        date = datetime.now()
        eight_days_before_date = date - timedelta(8)
        pending_probation_review_obj = HrmsFiveMonthsProbationReviewForApproval.objects.filter(submission_pending=True,
                                                                                               first_reminder_date__lte=eight_days_before_date).values_list(
            'employee_form__employee', flat=True)
        # print(pending_probation_review_obj)
        pending_probation_obj = list(pending_probation_review_obj)
        # self.queryset.filter(cu_user__in=pending_probation_obj)
        self.queryset = self.queryset.filter(cu_user__in=pending_probation_obj)

        sort_field = '-id'
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        department = self.request.query_params.get('department', None)
        designation = self.request.query_params.get('designation', None)
        search_keyword = self.request.query_params.get('search_keyword', None)
        company = self.request.query_params.get('company', None)
        hod = self.request.query_params.get('hod', None)
        employee = self.request.query_params.get('employee', None)
        reporting_head = self.request.query_params.get('reporting_head', None)

        filter = dict()

        if field_name and order_by:
            if field_name == 'employee_name' and order_by == 'asc':
                sort_field = 'cu_user__first_name'
            if field_name == 'employee_name' and order_by == 'desc':
                sort_field = '-cu_user__first_name'
            if field_name == 'department_name' and order_by == 'asc':
                sort_field = 'department__cd_name'
            if field_name == 'department_name' and order_by == 'desc':
                sort_field = '-department__cd_name'
            if field_name == 'designation_name' and order_by == 'asc':
                sort_field = 'designation__cod_name'
            if field_name == 'designation_name' and order_by == 'desc':
                sort_field = '-designation__cod_name'
            if field_name == 'company' and order_by == 'asc':
                sort_field = 'company__coc_name'
            if field_name == 'company' and order_by == 'desc':
                sort_field = '-company__coc_name'
            if field_name == 'hod_name' and order_by == 'asc':
                sort_field = 'hod__first_name'
            if field_name == 'hod_name' and order_by == 'desc':
                sort_field = '-hod__first_name'
            if field_name == 'reporting_head_name' and order_by == 'asc':
                sort_field = 'reporting_head__first_name'
            if field_name == 'reporting_head_name' and order_by == 'desc':
                sort_field = '-reporting_head__first_name'
            if field_name == 'joining_date' and order_by == 'asc':
                sort_field = 'joining_date'
            if field_name == 'joining_date' and order_by == 'desc':
                sort_field = '-joining_date'
            if field_name == 'emp_code' and order_by == 'asc':
                sort_field = 'cu_emp_code'
            if field_name == 'emp_code' and order_by == 'desc':
                sort_field = '-cu_emp_code'
            if field_name == 'sap_personnel_no' and order_by == 'asc':
                sort_field = 'sap_personnel_no'
            if field_name == 'sap_personnel_no' and order_by == 'desc':
                sort_field = '-sap_personnel_no'

        if department:
            filter['department_id'] = department
        if designation:
            filter['designation_id'] = designation
        if company:
            filter['company__id'] = company
        if hod:
            filter['hod_id'] = hod
        if employee:
            filter['id'] = employee
        if reporting_head:
            filter['reporting_head__id'] = reporting_head

        if search_keyword:
            search_keyword = search_keyword.lstrip()
            search_keyword = search_keyword.rstrip()
            f_name = search_keyword.split(' ')[0]
            l_name = ' '.join(search_keyword.split(' ')[1:])
            print(f_name, l_name)
            if l_name:
                queryset = self.queryset.filter(~Q(cu_punch_id='#N/A'), Q(cu_user__first_name__icontains=f_name),
                                                Q(cu_user__last_name__icontains=l_name), termination_date__isnull=True,
                                                cu_is_deleted=False,
                                                **filter).order_by(sort_field)

            else:

                queryset = self.queryset.filter(~Q(cu_punch_id='#N/A'), Q(cu_user__first_name__icontains=f_name) |
                                                Q(cu_user__last_name__icontains=f_name), termination_date__isnull=True,
                                                cu_is_deleted=False,
                                                **filter).order_by(sort_field)
        else:
            queryset = self.queryset.filter(~Q(cu_punch_id='#N/A'), termination_date__isnull=True, cu_is_deleted=False,
                                            **filter).order_by(sort_field)

        return queryset

    @response_modify_decorator_list_or_get_after_execution_for_onoff_pagination
    def get(self, request, *args, **kwargs):
        response = super(PendingFiveMonthsProbatinReviewListView, self).get(self, request, args, kwargs)
        data_dict = dict()
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        if 'results' in response.data:
            if start_date and end_date:
                from datetime import datetime
                start_object = datetime.strptime(start_date, '%Y-%m-%d')
                delta = timedelta(days=1)
                end_object = datetime.strptime(end_date, '%Y-%m-%d')
                response.data['results'] = list(
                    filter(
                        lambda i: i['mail_shoot_date'] >= start_object and i['mail_shoot_date'] <= end_object + delta,
                        response.data['results']))
                print(len(response.data['results']))

        if 'results' in response.data:
            if field_name and order_by:
                if field_name == 'company' and order_by == 'asc':
                    response.data['results'] = sorted(response.data['results'], key=lambda i: i['company_name'])
                if field_name == 'company' and order_by == 'desc':
                    response.data['results'] = sorted(response.data['results'], key=lambda i: i['company_name'],
                                                      reverse=True)

                if field_name == 'probation_date' and order_by == 'asc':
                    response.data['results'] = sorted(response.data['results'], key=lambda i: i['probation_date'])
                if field_name == 'probation_date' and order_by == 'desc':
                    response.data['results'] = sorted(response.data['results'], key=lambda i: i['probation_date'],
                                                      reverse=True)

                if field_name == 'mail_shoot_date' and order_by == 'asc':
                    response.data['results'] = sorted(response.data['results'], key=lambda i: i['mail_shoot_date'])
                if field_name == 'mail_shoot_date' and order_by == 'desc':
                    response.data['results'] = sorted(response.data['results'], key=lambda i: i['mail_shoot_date'],
                                                      reverse=True)
            data_dict = response.data

        else:
            if field_name and order_by:
                if field_name == 'company' and order_by == 'asc':
                    response.data = sorted(response.data, key=lambda i: i['company_name'])
                if field_name == 'company' and order_by == 'desc':
                    response.data = sorted(response.data, key=lambda i: i['company_name'], reverse=True)

                if field_name == 'probation_date' and order_by == 'asc':
                    response.data = sorted(response.data, key=lambda i: i['probation_date'])
                if field_name == 'probation_date' and order_by == 'desc':
                    response.data = sorted(response.data, key=lambda i: i['probation_date'], reverse=True)

                if field_name == 'mail_shoot_date' and order_by == 'asc':
                    response.data = sorted(response.data, key=lambda i: i['mail_shoot_date'])
                if field_name == 'mail_shoot_date' and order_by == 'desc':
                    response.data = sorted(response.data, key=lambda i: i['mail_shoot_date'], reverse=True)
            data_dict['results'] = response.data

        response.data = data_dict

        return Response({**response.data, 'request_status': 1, 'msg': settings.MSG_SUCCESS})

class PendingFiveMonthReviewSubmissionReminderFromHr(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def send_reminder_for_probation_review(self, usr_obj, base64_id, cc,request=None):
        user_email = usr_obj.employee_form.employee.cu_user.reporting_head.cu_user.cu_alt_email_id
        second_name = usr_obj.employee_form.employee.cu_user.reporting_head.last_name
        designation = usr_obj.employee_form.employee.cu_user.designation.cod_name if usr_obj.employee_form.employee.cu_user.designation else None
        employee_name = usr_obj.employee_form.employee.get_full_name()
        final_sub = usr_obj.employee_form.employee.get_full_name() + ',' + usr_obj.employee_form.employee.cu_user.designation.cod_name
        print(user_email)
        server_url = settings.SERVER_URL
        server_url = server_url.split(':' + server_url.split(':')[-1])[0]
        if user_email:
            mail_data = {
                "second_name": second_name,
                "employee_name": employee_name,
                "designation": designation,
                # "mail_body": mail_body,
                "link": "http://3.7.231.128/hrms" + "/#/probation-form-review/" + base64_id,
            }
            from global_function import send_mail

            send_mail('HRMS-5P-RR-RH', user_email, mail_data, cc, final_sub=final_sub)


    def post(self, request, *args, **kwargs):
        employee_id = request.data['employee_id']
        cc = request.data['cc']
        if cc:
            cc = cc.split(',')
        else:
            cc = cc
        # mail_subject = request.data['mail_subject']
        # mail_body = request.data['mail_body']
        # employee_mail = TCoreUserDetail.objects.get(cu_user_id=employee_id).cu_alt_email_id


        # print(employee_id, Cc,employee_mail)
        import base64
        obj = HrmsFiveMonthsProbationReviewForApproval.objects.get(employee_form__employee__cu_user__id=employee_id)
        print(obj)
        sample_string = str(obj.id)
        sample_string_bytes = sample_string.encode("ascii")
        base64_bytes = base64.b64encode(sample_string_bytes)
        print(base64_bytes)
        base64_id = base64_bytes.decode("ascii")
        print(base64_id)
        self.send_reminder_for_probation_review(obj, base64_id, cc,request)

        return Response({'request_status': 1, 'msg': 'Success'})




# five months probation confirmation report listing

class FiveMonthsProbationConfirmationReportView(generics.ListAPIView):
    '''
        Reason : completed five month probation employee listing
        Author :Swarup Adhikary
        Date : 30/09/2020
    '''
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreUserDetail.objects.filter(cu_user__is_superuser=False, cu_user__is_active=True)
    serializer_class = CompletedThreeMonthProbationReportSerializer
    pagination_class = OnOffPagination

    def get_queryset(self):
        pending_probation_review_obj = HrmsFiveMonthsProbationReviewForApproval.objects.filter(
            submission_pending=False).values_list('employee_form__employee', flat=True)
        # print(pending_probation_review_obj)
        pending_probation_obj = list(pending_probation_review_obj)
        # self.queryset.filter(cu_user__in=pending_probation_obj)
        self.queryset = self.queryset.filter(cu_user__in=pending_probation_obj)

        sort_field = '-id'
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        department = self.request.query_params.get('department', None)
        designation = self.request.query_params.get('designation', None)
        search_keyword = self.request.query_params.get('search_keyword', None)
        company = self.request.query_params.get('company', None)
        hod = self.request.query_params.get('hod', None)
        employee = self.request.query_params.get('employee', None)
        reporting_head = self.request.query_params.get('reporting_head', None)

        filter = dict()

        if field_name and order_by:
            if field_name == 'employee_name' and order_by == 'asc':
                sort_field = 'cu_user__first_name'
            if field_name == 'employee_name' and order_by == 'desc':
                sort_field = '-cu_user__first_name'
            if field_name == 'department_name' and order_by == 'asc':
                sort_field = 'department__cd_name'
            if field_name == 'department_name' and order_by == 'desc':
                sort_field = '-department__cd_name'
            if field_name == 'designation_name' and order_by == 'asc':
                sort_field = 'designation__cod_name'
            if field_name == 'designation_name' and order_by == 'desc':
                sort_field = '-designation__cod_name'
            if field_name == 'company' and order_by == 'asc':
                sort_field = 'company__coc_name'
            if field_name == 'company' and order_by == 'desc':
                sort_field = '-company__coc_name'
            if field_name == 'hod_name' and order_by == 'asc':
                sort_field = 'hod__first_name'
            if field_name == 'hod_name' and order_by == 'desc':
                sort_field = '-hod__first_name'
            if field_name == 'reporting_head_name' and order_by == 'asc':
                sort_field = 'reporting_head__first_name'
            if field_name == 'reporting_head_name' and order_by == 'desc':
                sort_field = '-reporting_head__first_name'
            if field_name == 'joining_date' and order_by == 'asc':
                sort_field = 'joining_date'
            if field_name == 'joining_date' and order_by == 'desc':
                sort_field = '-joining_date'
            if field_name == 'emp_code' and order_by == 'asc':
                sort_field = 'cu_emp_code'
            if field_name == 'emp_code' and order_by == 'desc':
                sort_field = '-cu_emp_code'
            if field_name == 'sap_personnel_no' and order_by == 'asc':
                sort_field = 'sap_personnel_no'
            if field_name == 'sap_personnel_no' and order_by == 'desc':
                sort_field = '-sap_personnel_no'

        if department:
            filter['department_id'] = department
        if designation:
            filter['designation_id'] = designation
        if company:
            filter['company__id'] = company
        if hod:
            filter['hod_id'] = hod
        if employee:
            filter['id'] = employee
        if reporting_head:
            filter['reporting_head__id'] = reporting_head

        if search_keyword:
            search_keyword = search_keyword.lstrip()
            search_keyword = search_keyword.rstrip()
            f_name = search_keyword.split(' ')[0]
            l_name = ' '.join(search_keyword.split(' ')[1:])
            print(f_name, l_name)
            if l_name:
                queryset = self.queryset.filter(~Q(cu_punch_id='#N/A'), Q(cu_user__first_name__icontains=f_name),
                                                Q(cu_user__last_name__icontains=l_name), termination_date__isnull=True,
                                                cu_is_deleted=False,

                                                **filter).order_by(sort_field)

            else:

                queryset = self.queryset.filter(~Q(cu_punch_id='#N/A'), Q(cu_user__first_name__icontains=f_name) |
                                                Q(cu_user__last_name__icontains=f_name), termination_date__isnull=True,
                                                cu_is_deleted=False,

                                                **filter).order_by(sort_field)
        else:
            queryset = self.queryset.filter(~Q(cu_punch_id='#N/A'), termination_date__isnull=True, cu_is_deleted=False,
                                            **filter).order_by(sort_field)

        return queryset

    @response_modify_decorator_list_or_get_after_execution_for_onoff_pagination
    def get(self, request, *args, **kwargs):
        response = super(FiveMonthsProbationConfirmationReportView, self).get(self, request, args, kwargs)
        data_dict = dict()
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        if 'results' in response.data:
            if start_date and end_date:
                from datetime import datetime
                start_object = datetime.strptime(start_date, '%Y-%m-%d')
                delta = timedelta(days=1)
                end_object = datetime.strptime(end_date, '%Y-%m-%d')
                response.data['results'] = list(
                    filter(lambda i: i['completion_3rd_month_review_date'] >= start_object and i[
                        'completion_3rd_month_review_date'] <= end_object + delta,
                           response.data['results']))
                print(len(response.data['results']))

        if 'results' in response.data:
            if field_name and order_by:
                if field_name == 'company' and order_by == 'asc':
                    response.data['results'] = sorted(response.data['results'], key=lambda i: i['company_name'])
                if field_name == 'company' and order_by == 'desc':
                    response.data['results'] = sorted(response.data['results'], key=lambda i: i['company_name'],
                                                      reverse=True)

                if field_name == 'probation_date' and order_by == 'asc':
                    response.data['results'] = sorted(response.data['results'], key=lambda i: i['probation_date'])
                if field_name == 'probation_date' and order_by == 'desc':
                    response.data['results'] = sorted(response.data['results'], key=lambda i: i['probation_date'],
                                                      reverse=True)

                if field_name == 'mail_shoot_date' and order_by == 'asc':
                    response.data['results'] = sorted(response.data['results'], key=lambda i: i['mail_shoot_date'])
                if field_name == 'mail_shoot_date' and order_by == 'desc':
                    response.data['results'] = sorted(response.data['results'], key=lambda i: i['mail_shoot_date'],
                                                      reverse=True)
            data_dict = response.data

        else:
            if field_name and order_by:
                if field_name == 'company' and order_by == 'asc':
                    response.data = sorted(response.data, key=lambda i: i['company_name'])
                if field_name == 'company' and order_by == 'desc':
                    response.data = sorted(response.data, key=lambda i: i['company_name'], reverse=True)

                if field_name == 'probation_date' and order_by == 'asc':
                    response.data = sorted(response.data, key=lambda i: i['probation_date'])
                if field_name == 'probation_date' and order_by == 'desc':
                    response.data = sorted(response.data, key=lambda i: i['probation_date'], reverse=True)

                if field_name == 'mail_shoot_date' and order_by == 'asc':
                    response.data = sorted(response.data, key=lambda i: i['mail_shoot_date'])
                if field_name == 'mail_shoot_date' and order_by == 'desc':
                    response.data = sorted(response.data, key=lambda i: i['mail_shoot_date'], reverse=True)
            data_dict['results'] = response.data

        response.data = data_dict

        return Response({**response.data, 'request_status': 1, 'msg': settings.MSG_SUCCESS})


# five months probation pending confirmation report listing

class FiveMonthsProbationPendingConfirmationListView(generics.ListAPIView):
    '''
        Reason : completed five month probation employee listing
        Author :Swarup Adhikary
        Date : 02/10/2020
    '''
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreUserDetail.objects.filter(cu_user__is_superuser=False, cu_user__is_active=True)
    serializer_class = CompletedThreeMonthProbationReportSerializer
    pagination_class = OnOffPagination

    def get_queryset(self):
        pending_probation_review_obj = HrmsFiveMonthsProbationReviewForApproval.objects.filter(submission_pending=False,
                                                                                               employee_form__employee__cu_user__is_confirm=False).values_list(
            'employee_form__employee', flat=True)
        print(pending_probation_review_obj)
        pending_probation_obj = list(pending_probation_review_obj)
        # self.queryset.filter(cu_user__in=pending_probation_obj)
        self.queryset = self.queryset.filter(cu_user__in=pending_probation_obj)
        print(self.queryset)

        sort_field = '-id'
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        department = self.request.query_params.get('department', None)
        designation = self.request.query_params.get('designation', None)
        search_keyword = self.request.query_params.get('search_keyword', None)
        company = self.request.query_params.get('company', None)
        hod = self.request.query_params.get('hod', None)
        employee = self.request.query_params.get('employee', None)
        reporting_head = self.request.query_params.get('reporting_head', None)

        filter = dict()

        if field_name and order_by:
            if field_name == 'employee_name' and order_by == 'asc':
                sort_field = 'cu_user__first_name'
            if field_name == 'employee_name' and order_by == 'desc':
                sort_field = '-cu_user__first_name'
            if field_name == 'department_name' and order_by == 'asc':
                sort_field = 'department__cd_name'
            if field_name == 'department_name' and order_by == 'desc':
                sort_field = '-department__cd_name'
            if field_name == 'designation_name' and order_by == 'asc':
                sort_field = 'designation__cod_name'
            if field_name == 'designation_name' and order_by == 'desc':
                sort_field = '-designation__cod_name'
            if field_name == 'company' and order_by == 'asc':
                sort_field = 'company__coc_name'
            if field_name == 'company' and order_by == 'desc':
                sort_field = '-company__coc_name'
            if field_name == 'hod_name' and order_by == 'asc':
                sort_field = 'hod__first_name'
            if field_name == 'hod_name' and order_by == 'desc':
                sort_field = '-hod__first_name'
            if field_name == 'reporting_head_name' and order_by == 'asc':
                sort_field = 'reporting_head__first_name'
            if field_name == 'reporting_head_name' and order_by == 'desc':
                sort_field = '-reporting_head__first_name'
            if field_name == 'joining_date' and order_by == 'asc':
                sort_field = 'joining_date'
            if field_name == 'joining_date' and order_by == 'desc':
                sort_field = '-joining_date'
            if field_name == 'emp_code' and order_by == 'asc':
                sort_field = 'cu_emp_code'
            if field_name == 'emp_code' and order_by == 'desc':
                sort_field = '-cu_emp_code'
            if field_name == 'sap_personnel_no' and order_by == 'asc':
                sort_field = 'sap_personnel_no'
            if field_name == 'sap_personnel_no' and order_by == 'desc':
                sort_field = '-sap_personnel_no'

        if department:
            filter['department_id'] = department
        if designation:
            filter['designation_id'] = designation
        if company:
            filter['company__id'] = company
        if hod:
            filter['hod_id'] = hod
        if employee:
            filter['id'] = employee
        if reporting_head:
            filter['reporting_head__id'] = reporting_head

        if search_keyword:
            search_keyword = search_keyword.lstrip()
            search_keyword = search_keyword.rstrip()
            f_name = search_keyword.split(' ')[0]
            l_name = ' '.join(search_keyword.split(' ')[1:])
            print(f_name, l_name)
            if l_name:
                queryset = self.queryset.filter(~Q(cu_punch_id='#N/A'), Q(cu_user__first_name__icontains=f_name),
                                                Q(cu_user__last_name__icontains=l_name), termination_date__isnull=True,
                                                cu_is_deleted=False,

                                                **filter).order_by(sort_field)

            else:

                queryset = self.queryset.filter(~Q(cu_punch_id='#N/A'), Q(cu_user__first_name__icontains=f_name) |
                                                Q(cu_user__last_name__icontains=f_name), termination_date__isnull=True,
                                                cu_is_deleted=False,

                                                **filter).order_by(sort_field)
        else:
            queryset = self.queryset.filter(~Q(cu_punch_id='#N/A'), termination_date__isnull=True, cu_is_deleted=False,
                                            **filter).order_by(sort_field)

        return queryset

    @response_modify_decorator_list_or_get_after_execution_for_onoff_pagination
    def get(self, request, *args, **kwargs):
        response = super(FiveMonthsProbationPendingConfirmationListView, self).get(self, request, args, kwargs)
        data_dict = dict()
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        if 'results' in response.data:
            if start_date and end_date:
                from datetime import datetime
                start_object = datetime.strptime(start_date, '%Y-%m-%d')
                delta = timedelta(days=1)
                end_object = datetime.strptime(end_date, '%Y-%m-%d')
                response.data['results'] = list(
                    filter(lambda i: i['completion_3rd_month_review_date'] >= start_object and i[
                        'completion_3rd_month_review_date'] <= end_object + delta,
                           response.data['results']))
                print(len(response.data['results']))

        if 'results' in response.data:
            if field_name and order_by:
                if field_name == 'company' and order_by == 'asc':
                    response.data['results'] = sorted(response.data['results'], key=lambda i: i['company_name'])
                if field_name == 'company' and order_by == 'desc':
                    response.data['results'] = sorted(response.data['results'], key=lambda i: i['company_name'],
                                                      reverse=True)

                if field_name == 'probation_date' and order_by == 'asc':
                    response.data['results'] = sorted(response.data['results'], key=lambda i: i['probation_date'])
                if field_name == 'probation_date' and order_by == 'desc':
                    response.data['results'] = sorted(response.data['results'], key=lambda i: i['probation_date'],
                                                      reverse=True)

                if field_name == 'mail_shoot_date' and order_by == 'asc':
                    response.data['results'] = sorted(response.data['results'], key=lambda i: i['mail_shoot_date'])
                if field_name == 'mail_shoot_date' and order_by == 'desc':
                    response.data['results'] = sorted(response.data['results'], key=lambda i: i['mail_shoot_date'],
                                                      reverse=True)
            data_dict = response.data

        else:
            if field_name and order_by:
                if field_name == 'company' and order_by == 'asc':
                    response.data = sorted(response.data, key=lambda i: i['company_name'])
                if field_name == 'company' and order_by == 'desc':
                    response.data = sorted(response.data, key=lambda i: i['company_name'], reverse=True)

                if field_name == 'probation_date' and order_by == 'asc':
                    response.data = sorted(response.data, key=lambda i: i['probation_date'])
                if field_name == 'probation_date' and order_by == 'desc':
                    response.data = sorted(response.data, key=lambda i: i['probation_date'], reverse=True)

                if field_name == 'mail_shoot_date' and order_by == 'asc':
                    response.data = sorted(response.data, key=lambda i: i['mail_shoot_date'])
                if field_name == 'mail_shoot_date' and order_by == 'desc':
                    response.data = sorted(response.data, key=lambda i: i['mail_shoot_date'], reverse=True)
            data_dict['results'] = response.data

        response.data = data_dict

        return Response({**response.data, 'request_status': 1, 'msg': settings.MSG_SUCCESS})


# Five months reminder cron job
class EmployeeFiveMonthsProbationReminder(APIView):
    permission_classes = [AllowAny]

    def send_reminder_for_probation(self, usr_obj, base64_id):
        user_email = usr_obj.employee.cu_user.cu_alt_email_id
        second_name = usr_obj.employee.last_name
        # employee_name = usr_obj.employee.get_full_name()
        # designation = usr_obj.employee.cu_user.designation.cod_name
        # final_str_for_subject_line = str(employee_name) + ',' + str(designation)
        print(user_email)
        server_url = settings.SERVER_URL
        server_url = server_url.split(':' + server_url.split(':')[-1])[0]
        if user_email:
            mail_data = {
                "second_name": second_name,
                "link": "http://3.7.231.128/hrms" + "/#/final-probation-form/" + base64_id,
            }
            from global_function import send_mail

            send_mail('HRMS-5P-1R', user_email, mail_data)

    def send_next_reminder_for_probation(self, usr_obj, base64_id, reminder_state):
        user_email = usr_obj.employee.cu_user.cu_alt_email_id
        second_name = usr_obj.employee.last_name
        final_str_for_subject_line = "Reminder " + ' ' + str(reminder_state)
        print(user_email)
        server_url = settings.SERVER_URL
        server_url = server_url.split(':' + server_url.split(':')[-1])[0]
        if user_email:
            mail_data = {
                "second_name": second_name,
                "link": "http://3.7.231.128/hrms" + "/#/final-probation-form/" + base64_id,
            }
            from global_function import send_mail

            send_mail('HRMS-5P-R', user_email, mail_data, final_sub=final_str_for_subject_line)

    def send_next_reminder_for_probation_to_rh(self, usr_obj, base64_id, reminder_state):
        user_email = usr_obj.employee_form.employee.cu_user.reporting_head.cu_user.cu_alt_email_id
        second_name = usr_obj.employee_form.employee.cu_user.reporting_head.last_name
        employee_name = usr_obj.employee_form.employee.get_full_name()
        designation = usr_obj.employee_form.employee.cu_user.designation.cod_name
        final_str_for_subject_line = str(employee_name) + ',' + str(designation) + ':' + "Reminder " + ' ' + str(
            reminder_state)
        print(user_email)
        if user_email:
            mail_data = {
                "employee_name": employee_name,
                "designation": designation,
                "second_name": second_name,
                "link": "http://localhost:4200/#/employee-probation-form/" + base64_id,
            }
            from global_function import send_mail

            send_mail('HRMS-3P-RH-R', user_email, mail_data, final_sub=final_str_for_subject_line)

    def get(self, request, *args, **kwargs):
        from datetime import datetime
        date = datetime.now()
        search_join_date = date - relativedelta(months=+5)
        date_before_10 = search_join_date - timedelta(10)
        print(search_join_date)
        alredy_probation_user = HrmsFiveMonthsProbationReviewForm.objects.filter(submission_pending=True).values_list(
            'employee')
        alredy_probation_user = list(alredy_probation_user)
        import base64
        users_obj = TCoreUserDetail.objects.filter(~Q(cu_user__in=alredy_probation_user),
                                                   id__in=[4496, 4497, 4498, 4499], is_confirm=False,
                                                   joining_date__lte=search_join_date.date(),
                                                   joining_date__gte=date_before_10)
        for each in users_obj:
            print(each.cu_alt_email_id)
            obj, create = HrmsFiveMonthsProbationReviewForm.objects.get_or_create(employee=each.cu_user,
                                                                                  reminder_state=0,
                                                                                  latest_reminder_date=date,
                                                                                  first_reminder_date=date)
            print(obj, create)
            sample_string = str(obj.id)
            sample_string_bytes = sample_string.encode("ascii")

            base64_bytes = base64.b64encode(sample_string_bytes)
            print(base64_bytes)
            base64_id = base64_bytes.decode("ascii")
            print(base64_id)
            # base64_bytes = base64_id.encode("ascii")
            #
            # sample_string_bytes = base64.b64decode(base64_bytes)
            # sample_string = sample_string_bytes.decode("ascii")
            # print(sample_string)
            self.send_reminder_for_probation(obj, base64_id)
        # second reminder for five month probation
        two_days_before_date = date - timedelta(2)
        employee_for_2nd_reminder = HrmsFiveMonthsProbationReviewForm.objects.filter(
            first_reminder_date__lte=two_days_before_date,
            reminder_state=0, submission_pending=True)
        for each in employee_for_2nd_reminder:
            sample_string = str(each.id)
            sample_string_bytes = sample_string.encode("ascii")

            base64_bytes = base64.b64encode(sample_string_bytes)
            # print(base64_bytes)
            base64_id = base64_bytes.decode("ascii")
            # print(base64_id)
            self.send_next_reminder_for_probation(each, base64_id, str(1))
            HrmsFiveMonthsProbationReviewForm.objects.filter(id=each.id).update(reminder_state=1,
                                                                                latest_reminder_date=date)

        # third reminder for five month probation
        Four_days_before_date = date - timedelta(4)
        employee_for_3rd_reminder = HrmsFiveMonthsProbationReviewForm.objects.filter(
            first_reminder_date__lte=Four_days_before_date,
            reminder_state=1, submission_pending=True)
        for each in employee_for_3rd_reminder:
            sample_string = str(each.id)
            sample_string_bytes = sample_string.encode("ascii")

            base64_bytes = base64.b64encode(sample_string_bytes)
            # print(base64_bytes)
            base64_id = base64_bytes.decode("ascii")
            print(base64_id)
            self.send_next_reminder_for_probation(each, base64_id, str(2))
            HrmsFiveMonthsProbationReviewForm.objects.filter(id=each.id).update(reminder_state=2,
                                                                                latest_reminder_date=date)
        # fourth reminder for the employee
        eight_days_before_date = date - timedelta(6)
        employee_for_rm_reminder = HrmsFiveMonthsProbationReviewForm.objects.filter(
            first_reminder_date__lte=eight_days_before_date,
            reminder_state=2, submission_pending=True)
        for each in employee_for_rm_reminder:
            sample_string = str(each.id)
            sample_string_bytes = sample_string.encode("ascii")

            base64_bytes = base64.b64encode(sample_string_bytes)
            print(base64_bytes)
            base64_id = base64_bytes.decode("ascii")
            print(base64_id)
            self.send_next_reminder_for_probation(each, base64_id, str(3))
            HrmsFiveMonthsProbationReviewForm.objects.filter(id=each.id).update(reminder_state=3,
                                                                                latest_reminder_date=date)
        # fourth reminder for the reporting head
        eight_days_before_date = date - timedelta(8)
        employee_for_rm_reminder = HrmsFiveMonthsProbationReviewForm.objects.filter(
            first_reminder_date__lte=eight_days_before_date,
            reminder_state=3, submission_pending=True)
        for each in employee_for_rm_reminder:
            user_email = each.employee.cu_user.reporting_head.cu_user.cu_alt_email_id
            second_name = each.employee.cu_user.reporting_head.last_name
            employee_name = each.employee.get_full_name()
            designation = each.employee.cu_user.designation.cod_name

            if user_email:
                mail_data = {
                    "employee_name": employee_name,
                    "designation": designation,
                    "second_name": second_name
                }
                from global_function import send_mail

                send_mail('HRMS-5P-RH', user_email, mail_data)
        # second reminder for the reporting head
        two_days_before_date = date - timedelta(2)
        reporting_head_for_2nd_reminder = HrmsFiveMonthsProbationReviewForApproval.objects.filter(
            first_reminder_date__lte=two_days_before_date,
            reminder_state=0, submission_pending=True)
        for each in reporting_head_for_2nd_reminder:
            sample_string = str(each.id)
            sample_string_bytes = sample_string.encode("ascii")

            base64_bytes = base64.b64encode(sample_string_bytes)
            # print(base64_bytes)
            base64_id = base64_bytes.decode("ascii")
            # print(base64_id)
            self.send_next_reminder_for_probation_to_rh(each, base64_id, str(1))
            HrmsThreeMonthsProbationReviewForApproval.objects.filter(id=each.id).update(reminder_state=1,
                                                                                        reminder_date=date)

        # third reminder for the reporting head
        four_days_before_date = date - timedelta(4)
        reporting_head_for_3nd_reminder = HrmsFiveMonthsProbationReviewForApproval.objects.filter(
            first_reminder_date__lte=four_days_before_date,
            reminder_state=1, submission_pending=True)
        for each in reporting_head_for_3nd_reminder:
            sample_string = str(each.id)
            sample_string_bytes = sample_string.encode("ascii")

            base64_bytes = base64.b64encode(sample_string_bytes)
            # print(base64_bytes)
            base64_id = base64_bytes.decode("ascii")
            # print(base64_id)
            self.send_next_reminder_for_probation_to_rh(each, base64_id, str(2))
            HrmsFiveMonthsProbationReviewForApproval.objects.filter(id=each.id).update(reminder_state=2,
                                                                                       reminder_date=date)

        # Fourth reminder for the reporting head
        six_days_before_date = date - timedelta(6)
        reporting_head_for_3nd_reminder = HrmsFiveMonthsProbationReviewForApproval.objects.filter(
            first_reminder_date__lte=six_days_before_date,
            reminder_state=2, submission_pending=True)
        for each in reporting_head_for_3nd_reminder:
            sample_string = str(each.id)
            sample_string_bytes = sample_string.encode("ascii")

            base64_bytes = base64.b64encode(sample_string_bytes)
            # print(base64_bytes)
            base64_id = base64_bytes.decode("ascii")
            # print(base64_id)
            self.send_next_reminder_for_probation_to_rh(each, base64_id, str(2))
            HrmsFiveMonthsProbationReviewForApproval.objects.filter(id=each.id).update(reminder_state=3,
                                                                                       reminder_date=date)

        return Response({'request_status': 1, 'msg': 'Success'})


class ProbationConfirmEmployeeView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreUserDetail.objects.all()
    serializer_class = ConfirmEmployeeSerializer


# employee rejoin
class EmployeeRejoinSuggestionListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreUserDetail.objects.filter(cu_user__is_active=False, rejoin_status=False)
    serializer_class = RejoinEmployeeSuggestionListSerializer

    def get_queryset(self):
        # one year previous date
        current_date = datetime.datetime.now()
        past_date = current_date - relativedelta(months=+12)
        print(past_date)
        result = self.queryset.filter(termination_date__gte=past_date)
        return result

    def get(self, request, *args, **kwargs):
        return super(__class__, self).get(self, request, *args, **kwargs)


class EmployeeRejoinViewV2(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = User.objects.all()
    serializer_class = EmployeeEditSerializerV2

    @response_modify_decorator_update
    def put(self, request, *args, **kwargs):

        ##print('request',request.data)

        user_id = self.kwargs['pk']
        ##print('user_id',type(user_id))
        list_type = self.request.query_params.get('list_type', None)

        cu_emp_code = request.data['cu_emp_code']
        if TCoreUserDetail.objects.filter(~Q(cu_user=user_id), cu_emp_code=cu_emp_code).count() > 0:
            custom_exception_message(self, 'Employee Code')

        if list_type == "professional":
            sap_personnel_no = request.data['sap_personnel_no']
            if sap_personnel_no != 'null':
                if TCoreUserDetail.objects.filter(~Q(cu_user=user_id), sap_personnel_no=sap_personnel_no).count() > 0:
                    custom_exception_message(self, 'SAP Personnel ID')

            cu_punch_id = request.data['cu_punch_id'] if request.data['cu_punch_id'] else None
            if TCoreUserDetail.objects.filter(~Q(cu_user=user_id), cu_punch_id=cu_punch_id).count() > 0:
                custom_exception_message(self, 'Punching Machine Id')

        if list_type == "personal":
            cu_phone_no = request.data['cu_phone_no']
            if TCoreUserDetail.objects.filter(~Q(cu_user=user_id), cu_phone_no=cu_phone_no).count() > 0:
                custom_exception_message(self, 'Personal Contact No. ')

            email = request.data['email']
            if User.objects.filter(~Q(id=user_id), email=email).count() > 0:
                custom_exception_message(self, 'Personal Email ID')

        if list_type == "role":
            pass
            # cu_alt_phone_no = request.data['cu_alt_phone_no']
            # if TCoreUserDetail.objects.filter(~Q(cu_user=user_id),cu_alt_phone_no=cu_alt_phone_no).count() > 0:
            #     custom_exception_message(self,'Official Contact No.')

            # cu_alt_email_id = request.data['cu_alt_email_id']
            # if TCoreUserDetail.objects.filter(~Q(cu_user=user_id),cu_alt_email_id=cu_alt_email_id).count() > 0:
            #     custom_exception_message(self,'Official Email ID')

        return super().put(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        get_id = self.kwargs['pk']
        list_type = self.request.query_params.get('list_type', None)
        module_id = self.request.query_params.get('module_id', None)
        response = User.objects.filter(id=get_id)
        data = {}
        data_dict = {}
        p_doc_dict = {}
        for user_data in response:
            data['first_name'] = user_data.first_name
            data['last_name'] = user_data.last_name
            if list_type == "professional":
                professional_details = TCoreUserDetail.objects.filter(
                    cu_user=user_data.id).values(
                    'cu_emp_code', 'daily_loginTime', 'joining_date',
                    'sap_personnel_no', 'daily_logoutTime', 'cu_punch_id',
                    'initial_ctc', 'current_ctc', 'lunch_start', 'lunch_end', 'salary_type__st_name',
                    'cost_centre', 'granted_cl', 'granted_sl', 'granted_el', 'salary_type', 'is_confirm',
                    'cu_alt_email_id',
                    'care_of', 'street_and_house_no', 'address_2nd_line', 'city', 'district',
                    'wbs_element', 'retirement_date', 'esic_no', 'esi_dispensary', 'pf_no', 'emp_pension_no',
                    'employee_voluntary_provident_fund_contribution', 'uan_no', 'branch_name', 'bank_account',
                    'ifsc_code', 'bus_facility', 'has_pf', 'has_esi', 'job_location', 'job_location_state',
                    'bank_name_p', 'employee_grade', 'employee_sub_grade', 'file_no')
                # #print('professional_details', professional_details)
                if professional_details:
                    data['is_active'] = user_data.is_active
                    data['emp_code'] = professional_details[0]['cu_emp_code'] if professional_details[0][
                        'cu_emp_code'] else None
                    data['cu_punch_id'] = professional_details[0]['cu_punch_id'] if professional_details[0][
                        'cu_punch_id'] else None
                    data['sap_personnel_no'] = professional_details[0]['sap_personnel_no'] if professional_details[0][
                        'sap_personnel_no'] else None
                    data['initial_ctc'] = professional_details[0]['initial_ctc'] if professional_details[0][
                        'initial_ctc'] else None
                    data['current_ctc'] = professional_details[0]['current_ctc'] if professional_details[0][
                        'current_ctc'] else None
                    data['cost_centre'] = professional_details[0]['cost_centre'] if professional_details[0][
                        'cost_centre'] else None
                    data['granted_cl'] = professional_details[0]['granted_cl'] if professional_details[0][
                        'granted_cl'] else None
                    data['granted_sl'] = professional_details[0]['granted_sl'] if professional_details[0][
                        'granted_sl'] else None
                    data['granted_el'] = professional_details[0]['granted_el'] if professional_details[0][
                        'granted_el'] else None
                    data['daily_loginTime'] = professional_details[0]['daily_loginTime'] if professional_details[0][
                        'daily_loginTime'] else None
                    data['daily_logoutTime'] = professional_details[0]['daily_logoutTime'] if professional_details[0][
                        'daily_logoutTime'] else None
                    data['lunch_start'] = professional_details[0]['lunch_start'] if professional_details[0][
                        'lunch_start'] else None
                    data['lunch_end'] = professional_details[0]['lunch_end'] if professional_details[0][
                        'lunch_end'] else None
                    data['joining_date'] = professional_details[0]['joining_date'] if professional_details[0][
                        'joining_date'] else None
                    data['salary_type'] = professional_details[0]['salary_type'] if professional_details[0][
                        'salary_type'] else None
                    data['salary_type_name'] = professional_details[0]['salary_type__st_name'] if \
                        professional_details[0]['salary_type__st_name'] else None
                    data['is_confirm'] = professional_details[0]['is_confirm']
                    data['official_email_id'] = professional_details[0]['cu_alt_email_id'] if professional_details[0][
                        'cu_alt_email_id'] else None

                    data['wbs_element'] = professional_details[0]['wbs_element'] if professional_details[0][
                        'wbs_element'] else None
                    data['retirement_date'] = professional_details[0]['retirement_date'] if professional_details[0][
                        'retirement_date'] else None
                    data['esic_no'] = professional_details[0]['esic_no'] if professional_details[0]['esic_no'] else None
                    data['esi_dispensary'] = professional_details[0]['esi_dispensary'] if professional_details[0][
                        'esi_dispensary'] else None
                    data['pf_no'] = professional_details[0]['pf_no'] if professional_details[0]['pf_no'] else None
                    data['emp_pension_no'] = professional_details[0]['emp_pension_no'] if professional_details[0][
                        'emp_pension_no'] else None
                    data['employee_voluntary_provident_fund_contribution'] = professional_details[0][
                        'employee_voluntary_provident_fund_contribution'] if professional_details[0][
                        'employee_voluntary_provident_fund_contribution'] else None

                    data['uan_no'] = professional_details[0]['uan_no'] if professional_details[0]['uan_no'] else None
                    data['branch_name'] = professional_details[0]['branch_name'] if professional_details[0][
                        'branch_name'] else None
                    data['bank_account'] = professional_details[0]['bank_account'] if professional_details[0][
                        'bank_account'] else None
                    data['ifsc_code'] = professional_details[0]['ifsc_code'] if professional_details[0][
                        'ifsc_code'] else None
                    data['file_no'] = professional_details[0]['file_no'] if professional_details[0]['file_no'] else None
                    data['bus_facility'] = professional_details[0]['bus_facility']

                    # 'has_pf','has_esi','job_location_state','bank_name_p'
                    data['has_pf'] = professional_details[0]['has_pf']
                    data['has_esi'] = professional_details[0]['has_esi']
                    data['job_location'] = professional_details[0]['job_location']
                    data['job_location_state'] = professional_details[0]['job_location_state']
                    job_location_state_name = TCoreState.objects.filter(
                        id=professional_details[0]['job_location_state']).first()
                    data[
                        'job_location_state_name'] = job_location_state_name.cs_state_name if job_location_state_name else None
                    data['bank_name_p'] = professional_details[0]['bank_name_p']
                    bank_name = TCoreBank.objects.filter(id=professional_details[0]['bank_name_p']).first()
                    data['bank_name'] = bank_name.name if bank_name else None

                    if professional_details[0]['employee_grade']:
                        grade = TCoreGrade.objects.get(id=professional_details[0]['employee_grade'])
                        data['grade'] = grade.cg_name
                    else:
                        data['grade'] = ""

                    if professional_details[0]['employee_sub_grade']:
                        sub_grade = TCoreSubGrade.objects.get(id=professional_details[0]['employee_sub_grade'])
                        data['sub_grade'] = sub_grade.name
                    else:
                        data['sub_grade'] = ""

                saturday_off = AttendenceSaturdayOffMaster.objects.filter(employee=user_data.id, is_deleted=False)
                ##print('saturday_off',saturday_off)
                if saturday_off:
                    for s_o in saturday_off:
                        sat_data = {
                            'id': s_o.id,
                            'first': s_o.first,
                            'second': s_o.second,
                            'third': s_o.third,
                            'fourth': s_o.fourth,
                            'all_s_day': s_o.all_s_day
                        }
                    data['saturday_off'] = sat_data
                else:
                    data['saturday_off'] = None

                user_benefits = HrmsUsersBenefits.objects.filter(user=user_data.id, is_deleted=False)
                benefits_list = []
                if user_benefits:
                    for u_b in user_benefits:
                        benefits = {
                            'id': u_b.id,
                            'benefits': u_b.benefits.id,
                            'benefits_name': u_b.benefits.benefits_name,
                            'allowance': u_b.allowance
                        }
                        benefits_list.append(benefits)
                    data['benefits_provided'] = benefits_list
                else:
                    data['benefits_provided'] = []
                other_facilities = HrmsUsersOtherFacilities.objects.filter(user=user_data.id, is_deleted=False)
                facilities_list = []
                if other_facilities:
                    for o_f in other_facilities:
                        facility = {
                            'id': o_f.id,
                            'other_facilities': o_f.other_facilities
                        }
                        facilities_list.append(facility)
                    data['other_facilities'] = facilities_list
                else:
                    data['other_facilities'] = []

                initial_ctc_dict = {}
                upload_files_dict = {}
                current_ctc_dict = {}
                professional_documents = HrmsDocument.objects.filter(user=user_data.id, is_deleted=False)
                if professional_documents:
                    upload_files_list = []
                    for doc_details in professional_documents:
                        if (doc_details.tab_name).lower() == "professional":
                            if doc_details.__dict__['document'] == "":
                                file_url = ''
                            else:
                                file_url = request.build_absolute_uri(doc_details.document.url)
                            if doc_details.__dict__['document_name'] == "":
                                doc_name = ''
                            else:
                                doc_name = doc_details.document_name
                            if doc_details.field_label == "Initial CTC":
                                initial_ctc_dict = {
                                    'id': doc_details.id,
                                    'document_name': doc_name,
                                    'document': file_url
                                }
                            if doc_details.field_label == "Upload Files":
                                upload_files_dict = {
                                    'id': doc_details.id,
                                    'document_name': doc_name,
                                    'document': file_url
                                }
                                upload_files_list.append(upload_files_dict)
                            if doc_details.field_label == "Current CTC":
                                current_ctc_dict = {
                                    'id': doc_details.id,
                                    'document_name': doc_name,
                                    'document': file_url
                                }
                    data['initial_ctc_doc'] = initial_ctc_dict if initial_ctc_dict else None
                    data['upload_files_doc'] = upload_files_list if upload_files_list else None
                    data['current_ctc_doc'] = current_ctc_dict if current_ctc_dict else None

                else:
                    data['initial_ctc_doc'] = None
                    data['upload_files_doc'] = []
                    data['current_ctc_doc'] = None
                personal_documents = HrmsDynamicSectionFieldLabelDetailsWithDoc.objects.filter(user=user_data.id,
                                                                                               is_deleted=False)
                # print("personal_documents",personal_documents)
                if personal_documents:
                    licenses_and_certifications_list = []
                    add_more_files_list = []
                    work_experience_list = []
                    other_documents_list = []
                    for doc_details in personal_documents:
                        if (doc_details.tab_name).lower() == "personal":
                            if doc_details.__dict__['document'] == "":
                                file_url = ''
                            else:
                                file_url = request.build_absolute_uri(doc_details.document.url)

                            if doc_details.__dict__['document_name'] == "":
                                doc_name = ""
                            else:
                                doc_name = doc_details.document_name

                            if doc_details.field_label == "Licenses and Certifications":
                                licenses_and_certifications_dict = {
                                    'id': doc_details.id,
                                    'field_label_value': doc_details.field_label_value if doc_details.field_label_value else None,
                                    'document_name': doc_name,
                                    'document': file_url
                                }
                                licenses_and_certifications_list.append(licenses_and_certifications_dict)

                            if doc_details.field_label == "Work Experience":
                                work_experience_dict = {
                                    'id': doc_details.id,
                                    'field_label_value': doc_details.field_label_value if doc_details.field_label_value else None,
                                    'document_name': doc_name,
                                    'document': file_url
                                }
                                work_experience_list.append(work_experience_dict)

                            if doc_details.field_label == "Other Documents":
                                other_documents_dict = {
                                    'id': doc_details.id,
                                    'field_label_value': doc_details.field_label_value if doc_details.field_label_value else None,
                                    'document_name': doc_name,
                                    'document': file_url
                                }
                                other_documents_list.append(other_documents_dict)

                    data[
                        'licenses_and_certifications_doc'] = licenses_and_certifications_list if licenses_and_certifications_list else []
                    data['work_experience_doc'] = work_experience_list if work_experience_list else []
                    data['other_documents_list'] = other_documents_list if other_documents_list else []

                else:
                    data['licenses_and_certifications_doc'] = []
                    data['work_experience_doc'] = []
                    data['other_documents_list'] = []

                # academic document
                academic_qualification = HrmsUserQualification.objects.filter(user=user_data.id, is_deleted=False)
                # print('academic_qualification',academic_qualification)
                if academic_qualification:
                    academic_qualification_list = []
                    academic_qualification_dict = {}
                    for a_q in academic_qualification:

                        academic_qualification_dict = {
                            'id': a_q.id,
                            'qualification': a_q.qualification.id if a_q.qualification else '',
                            'qualification_name': a_q.qualification.name if a_q.qualification else '',
                            'details': a_q.details if a_q.details else ''
                        }
                        academic_doc = HrmsUserQualificationDocument.objects.filter(user_qualification=a_q.id,
                                                                                    is_deleted=False)
                        # print('academic_doc',academic_doc)
                        if academic_doc:
                            academic_doc_dict = {}
                            academic_doc_list = []
                            for a_d in academic_doc:
                                academic_doc_dict = {
                                    'id': a_d.id,
                                    'document': request.build_absolute_uri(a_d.document.url) if a_d.document else ''
                                }
                                academic_doc_list.append(academic_doc_dict)
                            academic_qualification_dict['qualification_doc'] = academic_doc_list
                        else:
                            academic_qualification_dict['qualification_doc'] = []
                        academic_qualification_list.append(academic_qualification_dict)
                    data['academic_qualification'] = academic_qualification_list
                else:
                    data['academic_qualification'] = []
            # if list_type == "role":
            #     role_details = TCoreUserDetail.objects.filter(cu_user=user_data.id).values(
            #         'cu_emp_code', 'cu_alt_phone_no', 'cu_alt_email_id', 'company__id', 'company__coc_name',
            #         'job_description', 'hod__id',
            #         'hod__first_name', 'hod__last_name', 'joining_date', 'termination_date',
            #         'designation__id', 'designation__cod_name', 'department__id', 'department__cd_name',
            #         'resignation_date',
            #         'job_location_state', 'reporting_head__id', 'reporting_head__first_name',
            #         'reporting_head__last_name',
            #         'employee_grade__cg_name', 'employee_grade__id', 'employee_sub_grade', 'is_auto_od',
            #         'sub_department', 'sub_department__cd_name', 'attendance_type',
            #         'is_flexi_hour', 'file_no')
            #     if role_details:
            #         data['is_active'] = user_data.is_active
            #         data['emp_code'] = role_details[0]['cu_emp_code'] if role_details[0]['cu_emp_code'] else None
            #         data['joining_date'] = role_details[0]['joining_date'] if role_details[0]['joining_date'] else None
            #         data['official_contact_no'] = role_details[0]['cu_alt_phone_no'] if role_details[0][
            #             'cu_alt_phone_no'] else None
            #         data['official_email_id'] = role_details[0]['cu_alt_email_id'] if role_details[0][
            #             'cu_alt_email_id'] else None
            #         data['company'] = role_details[0]['company__id'] if role_details[0]['company__id'] else None
            #         data['company_name'] = role_details[0]['company__coc_name'] if role_details[0][
            #             'company__coc_name'] else None
            #         data['job_description'] = role_details[0]['job_description'] if role_details[0][
            #             'job_description'] else None
            #         data['hod_id'] = role_details[0]['hod__id'] if role_details[0]['hod__id'] else None
            #         data['file_no'] = role_details[0]['file_no'] if role_details[0]['file_no'] else None
            #         hod__first_name = role_details[0]['hod__first_name'] if role_details[0]['hod__first_name'] else ''
            #         hod__last_name = role_details[0]['hod__last_name'] if role_details[0]['hod__last_name'] else ''
            #
            #         data['hod'] = hod__first_name + " " + hod__last_name
            #
            #         data['designation_id'] = role_details[0]['designation__id'] if role_details[0][
            #             'designation__id'] else None
            #         data['designation_name'] = role_details[0]['designation__cod_name'] if role_details[0][
            #             'designation__cod_name'] else None
            #         data['department_id'] = role_details[0]['department__id'] if role_details[0][
            #             'department__id'] else None
            #         data['department_name'] = role_details[0]['department__cd_name'] if role_details[0][
            #             'department__cd_name'] else None
            #
            #         data['reporting_head_id'] = role_details[0]['reporting_head__id'] if role_details[0][
            #             'reporting_head__id'] else None
            #
            #         reporting_head__first_name = role_details[0]['reporting_head__first_name'] if role_details[0][
            #             'reporting_head__first_name'] else ''
            #         reporting_head__last_name = role_details[0]['reporting_head__last_name'] if role_details[0][
            #             'reporting_head__last_name'] else ''
            #         data['reporting_head_name'] = reporting_head__first_name + " " + reporting_head__last_name
            #
            #         # data['temp_reporting_head_id']=role_details[0]['temp_reporting_head__id'] if role_details[0]['temp_reporting_head__id'] else None
            #
            #         # temp_reporting_head__first_name = role_details[0]['temp_reporting_head__first_name'] if role_details[0]['temp_reporting_head__first_name'] else ''
            #         # temp_reporting_head__last_name = role_details[0]['temp_reporting_head__last_name'] if role_details[0]['temp_reporting_head__last_name'] else ''
            #         # data['temp_reporting_head_name']= temp_reporting_head__first_name  +" "+ temp_reporting_head__last_name
            #
            #         temp_reporting_heads = UserTempReportingHeadMap.objects.filter(user=user_data,
            #                                                                        is_deleted=False).values(
            #             'temp_reporting_head__id', 'temp_reporting_head__first_name', 'temp_reporting_head__last_name')
            #         data['temp_reporting_heads'] = temp_reporting_heads
            #
            #         # data['employee_grade_name']=role_details[0]['employee_grade__cg_name'] if role_details[0]['employee_grade__cg_name'] else None
            #         # data['employee_grade_id']=role_details[0]['employee_grade__id'] if role_details[0]['employee_grade__id'] else None
            #         data['termination_date'] = role_details[0]['termination_date'] if role_details[0][
            #             'termination_date'] else None
            #         data['resignation_date'] = role_details[0]['resignation_date'] if role_details[0][
            #             'resignation_date'] else None
            #         data['job_location_state'] = role_details[0]['job_location_state'] if role_details[0][
            #             'job_location_state'] else None
            #         data['is_auto_od'] = role_details[0]['is_auto_od'] if role_details[0]['is_auto_od'] else False
            #         data['sub_department'] = role_details[0]['sub_department'] if role_details[0][
            #             'sub_department'] else None
            #         data['sub_department_name'] = role_details[0]['sub_department__cd_name'] if role_details[0][
            #             'sub_department'] else None
            #         data['attendance_type'] = role_details[0]['attendance_type'] if role_details[0][
            #             'attendance_type'] else None
            #         data['is_flexi_hour'] = role_details[0]['is_flexi_hour']
            #         if role_details[0]['employee_sub_grade']:
            #             sub_grade = TCoreSubGrade.objects.get(id=role_details[0]['employee_sub_grade'])
            #             data['sub_grade'] = sub_grade.name
            #             data['sub_grade_id'] = sub_grade.id
            #         else:
            #             data['sub_grade'] = ""
            #             data['sub_grade_id'] = ""
            #
            #         grade_details = TCoreGrade.objects.filter(id=role_details[0]['employee_grade__id'],
            #                                                   cg_is_deleted=False)
            #
            #         if grade_details:
            #             grade_details = \
            #             TCoreGrade.objects.filter(id=role_details[0]['employee_grade__id'], cg_is_deleted=False)[0]
            #             grade_dict = dict()
            #             ##print('grade_details',grade_details.id)
            #             if grade_details.cg_parent_id != 0:
            #                 parent = TCoreGrade.objects.filter(id=grade_details.cg_parent_id, cg_is_deleted=False)
            #                 for p_d in parent:
            #                     grade_dict['id'] = p_d.id
            #                     grade_dict['cg_name'] = p_d.cg_name
            #
            #                 grade_dict['child'] = {
            #                     "id": grade_details.id,
            #                     "cg_name": grade_details.cg_name
            #                 }
            #             else:
            #                 grade_dict['id'] = grade_details.id
            #                 grade_dict['cg_name'] = grade_details.cg_name
            #                 grade_dict['child'] = None
            #
            #             ##print('grade_dict',grade_dict)
            #
            #             data['grade_details'] = grade_dict
            #         else:
            #             data['grade_details'] = None
            # if list_type == "personal":
            #     personal_details = TCoreUserDetail.objects.filter(cu_user=user_data.id)
            #     # print('personal_details',personal_details)
            #     if personal_details:
            #         for p_d in personal_details:
            #             data['is_active'] = user_data.is_active
            #             data['emp_code'] = p_d.cu_emp_code
            #             data['cu_phone_no'] = p_d.cu_phone_no if p_d.cu_phone_no else ""
            #             data['file_no'] = p_d.file_no if p_d.file_no else ""
            #             data['email'] = p_d.cu_user.email
            #             data['address'] = p_d.address
            #             data['joining_date'] = p_d.joining_date
            #             data['cu_dob'] = p_d.cu_dob
            #             data['blood_group'] = p_d.blood_group if p_d.blood_group else ''
            #             data['photo'] = request.build_absolute_uri(
            #                 p_d.cu_profile_img.url) if p_d.cu_profile_img else None
            #             data['total_experience'] = p_d.total_experience
            #             data['job_location_state'] = p_d.job_location_state.id if p_d.job_location_state else None
            #             data[
            #                 'job_location_state_name'] = p_d.job_location_state.cs_state_name if p_d.job_location_state else None
            #             data['official_email_id'] = p_d.cu_alt_email_id
            #
            #             data['care_of'] = p_d.care_of
            #             data['street_and_house_no'] = p_d.street_and_house_no
            #             data['address_2nd_line'] = p_d.address_2nd_line
            #             data['city'] = p_d.city
            #             data['district'] = p_d.district
            #
            #             data['aadhar_no'] = p_d.aadhar_no
            #             data['pan_no'] = p_d.pan_no
            #             data['cu_gender'] = p_d.cu_gender
            #             data['pincode'] = p_d.pincode
            #             data['emergency_relationship'] = p_d.emergency_relationship
            #             data['emergency_contact_no'] = p_d.emergency_contact_no
            #             data['emergency_contact_name'] = p_d.emergency_contact_name
            #             data['marital_status'] = p_d.marital_status
            #             data['father_name'] = p_d.father_name
            #             data['state'] = p_d.state.id if p_d.state else None
            #             data['state_name'] = p_d.state.cs_state_name if p_d.state else None
            #
            #     licenses_and_certifications_dict = {}
            #     work_experience_dict = {}
            #     add_more_files_dict = {}
            #     other_documents_dict = {}
            #
            #     personal_documents = HrmsDynamicSectionFieldLabelDetailsWithDoc.objects.filter(user=user_data.id,
            #                                                                                    is_deleted=False)
            #     # print("personal_documents",personal_documents)
            #     if personal_documents:
            #         licenses_and_certifications_list = []
            #         add_more_files_list = []
            #         work_experience_list = []
            #         other_documents_list = []
            #         for doc_details in personal_documents:
            #             if (doc_details.tab_name).lower() == "personal":
            #                 if doc_details.__dict__['document'] == "":
            #                     file_url = ''
            #                 else:
            #                     file_url = request.build_absolute_uri(doc_details.document.url)
            #
            #                 if doc_details.__dict__['document_name'] == "":
            #                     doc_name = ""
            #                 else:
            #                     doc_name = doc_details.document_name
            #
            #                 if doc_details.field_label == "Licenses and Certifications":
            #                     licenses_and_certifications_dict = {
            #                         'id': doc_details.id,
            #                         'field_label_value': doc_details.field_label_value if doc_details.field_label_value else None,
            #                         'document_name': doc_name,
            #                         'document': file_url
            #                     }
            #                     licenses_and_certifications_list.append(licenses_and_certifications_dict)
            #
            #                 if doc_details.field_label == "Work Experience":
            #                     work_experience_dict = {
            #                         'id': doc_details.id,
            #                         'field_label_value': doc_details.field_label_value if doc_details.field_label_value else None,
            #                         'document_name': doc_name,
            #                         'document': file_url
            #                     }
            #                     work_experience_list.append(work_experience_dict)
            #
            #                 if doc_details.field_label == "Other Documents":
            #                     other_documents_dict = {
            #                         'id': doc_details.id,
            #                         'field_label_value': doc_details.field_label_value if doc_details.field_label_value else None,
            #                         'document_name': doc_name,
            #                         'document': file_url
            #                     }
            #                     other_documents_list.append(other_documents_dict)
            #
            #         data[
            #             'licenses_and_certifications_doc'] = licenses_and_certifications_list if licenses_and_certifications_list else []
            #         data['work_experience_doc'] = work_experience_list if work_experience_list else []
            #         data['other_documents_list'] = other_documents_list if other_documents_list else []
            #
            #     else:
            #         data['licenses_and_certifications_doc'] = []
            #         data['work_experience_doc'] = []
            #         data['other_documents_list'] = []
            #
            #     academic_qualification = HrmsUserQualification.objects.filter(user=user_data.id, is_deleted=False)
            #     # print('academic_qualification',academic_qualification)
            #     if academic_qualification:
            #         academic_qualification_list = []
            #         academic_qualification_dict = {}
            #         for a_q in academic_qualification:
            #
            #             academic_qualification_dict = {
            #                 'id': a_q.id,
            #                 'qualification': a_q.qualification.id if a_q.qualification else '',
            #                 'qualification_name': a_q.qualification.name if a_q.qualification else '',
            #                 'details': a_q.details if a_q.details else ''
            #             }
            #             academic_doc = HrmsUserQualificationDocument.objects.filter(user_qualification=a_q.id,
            #                                                                         is_deleted=False)
            #             # print('academic_doc',academic_doc)
            #             if academic_doc:
            #                 academic_doc_dict = {}
            #                 academic_doc_list = []
            #                 for a_d in academic_doc:
            #                     academic_doc_dict = {
            #                         'id': a_d.id,
            #                         'document': request.build_absolute_uri(a_d.document.url) if a_d.document else ''
            #                     }
            #                     academic_doc_list.append(academic_doc_dict)
            #                 academic_qualification_dict['qualification_doc'] = academic_doc_list
            #             else:
            #                 academic_qualification_dict['qualification_doc'] = []
            #             academic_qualification_list.append(academic_qualification_dict)
            #         data['academic_qualification'] = academic_qualification_list
            #     else:
            #         data['academic_qualification'] = []

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


class EmployeeRejoinAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreUserDetail.objects.all()
    serializer_class = EmployeeRejoinAddSerializer

    def get_queryset(self):
        '''
            eleminate login user on employee list added by Rupam Hazra Line number 458 - 459
        '''
        login_user = self.request.user.id
        tcore_obj_id = self.request.query_params.get('employee_id', None)
        print(tcore_obj_id)
        queryset = self.queryset.filter(id=tcore_obj_id)

        # if department:
        #     filter['department_id'] = department
        # if designation:
        #     filter['designation_id'] = designation
        print(queryset)
        return queryset

    def get(self, request, *args, **kwargs):
        response = super(EmployeeRejoinAddView, self).get(self, request, args, kwargs)
        if 'results' in response.data:
            response_s = response.data['results']
        else:
            response_s = response.data

        p_doc_dict = {}
        data_list = list()
        for data in response_s:
            user_benefits = HrmsUsersBenefits.objects.filter(user=data['cu_user'])
            print(user_benefits)
            benefits_list = []
            if user_benefits:
                for u_b in user_benefits:
                    benefits = {
                        'id': u_b.id,
                        'benefits': u_b.benefits.id,
                        'benefits_name': u_b.benefits.benefits_name,
                        'allowance': u_b.allowance
                    }
                    benefits_list.append(benefits)
                data['benefits_provided'] = benefits_list
            else:
                data['benefits_provided'] = []
            other_facilities = HrmsUsersOtherFacilities.objects.filter(user=data['cu_user'], is_deleted=False)
            facilities_list = []
            if other_facilities:
                for o_f in other_facilities:
                    facility = {
                        'id': o_f.id,
                        'other_facilities': o_f.other_facilities,
                    }
                    facilities_list.append(facility)
                data['other_facilities'] = facilities_list
            else:
                data['other_facilities'] = []
            p_doc_list = []
            professional_documents = HrmsDocument.objects.filter(user=data['cu_user'], is_deleted=False)
            if professional_documents:
                for doc_details in professional_documents:
                    if (doc_details.tab_name).lower() == "professional":
                        if doc_details.__dict__['document'] == "":
                            file_url = ''
                        else:
                            file_url = request.build_absolute_uri(doc_details.document.url)
                        if doc_details.__dict__['document_name'] == "":
                            doc_name = ""
                        else:
                            doc_name = doc_details.document_name

                        p_doc_dict = {
                            'tab_name': doc_details.tab_name if doc_details.tab_name else None,
                            'field_label': doc_details.field_label if doc_details.field_label else None,
                            'document_name': doc_name,
                            'document': file_url
                        }
                        p_doc_list.append(p_doc_dict)
                data['documents'] = p_doc_list
            else:
                data['documents'] = []
            personal_documents = HrmsDynamicSectionFieldLabelDetailsWithDoc.objects.filter(user=data['cu_user'],
                                                                                           is_deleted=False)
            # print("personal_documents",personal_documents)
            if personal_documents:
                licenses_and_certifications_list = []
                add_more_files_list = []
                work_experience_list = []
                other_documents_list = []
                for doc_details in personal_documents:
                    if (doc_details.tab_name).lower() == "personal":
                        if doc_details.__dict__['document'] == "":
                            file_url = ''
                        else:
                            file_url = request.build_absolute_uri(doc_details.document.url)

                        if doc_details.__dict__['document_name'] == "":
                            doc_name = ""
                        else:
                            doc_name = doc_details.document_name

                        if doc_details.field_label == "Licenses and Certifications":
                            licenses_and_certifications_dict = {
                                'id': doc_details.id,
                                'field_label_value': doc_details.field_label_value if doc_details.field_label_value else None,
                                'document_name': doc_name,
                                'document': file_url
                            }
                            licenses_and_certifications_list.append(licenses_and_certifications_dict)

                        if doc_details.field_label == "Work Experience":
                            work_experience_dict = {
                                'id': doc_details.id,
                                'field_label_value': doc_details.field_label_value if doc_details.field_label_value else None,
                                'document_name': doc_name,
                                'document': file_url
                            }
                            work_experience_list.append(work_experience_dict)

                        if doc_details.field_label == "Other Documents":
                            other_documents_dict = {
                                'id': doc_details.id,
                                'field_label_value': doc_details.field_label_value if doc_details.field_label_value else None,
                                'document_name': doc_name,
                                'document': file_url
                            }
                            other_documents_list.append(other_documents_dict)

                data[
                    'licenses_and_certifications_doc'] = licenses_and_certifications_list if licenses_and_certifications_list else []
                data['work_experience_doc'] = work_experience_list if work_experience_list else []
                data['other_documents_list'] = other_documents_list if other_documents_list else []


            else:
                data['licenses_and_certifications_doc'] = []
                data['work_experience_doc'] = []
                data['other_documents_list'] = []

            academic_qualification = HrmsUserQualification.objects.filter(user=data['cu_user'], is_deleted=False)
            # print('academic_qualification',academic_qualification)
            if academic_qualification:
                academic_qualification_list = []
                academic_qualification_dict = {}
                for a_q in academic_qualification:
                    academic_qualification_dict = {
                        'id': a_q.id,
                        'qualification': a_q.qualification.id,
                        'qualification_name': a_q.qualification.name,
                        'details': a_q.details
                    }
                    academic_doc = HrmsUserQualificationDocument.objects.filter(user_qualification=a_q.id,
                                                                                is_deleted=False)
                    print('academic_doc', academic_doc)
                    if academic_doc:
                        academic_doc_dict = {}
                        academic_doc_list = []
                        for a_d in academic_doc:
                            academic_doc_dict = {
                                'id': a_d.id,
                                'document': request.build_absolute_uri(a_d.document.url)
                            }
                            academic_doc_list.append(academic_doc_dict)
                        academic_qualification_dict['qualification_doc'] = academic_doc_list
                    else:
                        academic_qualification_dict['qualification_doc'] = []
                    academic_qualification_list.append(academic_qualification_dict)
                data['academic_qualification'] = academic_qualification_list
            else:
                data['academic_qualification'] = []
            # if list_type == "professional":
            #     tcore_user = TCoreUserDetail.objects.filter(cu_user=data['id'])
        # user_benefits = HrmsUsersBenefits.objects.filter(user=data['id'], is_deleted=False)

        return response


class EmployeeTransferView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = User.objects.all()
    serializer_class = EmployeeTransferSerializer

    @response_modify_decorator_update
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)


class TransferHistoryListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = EmployeeTransferHistory.objects.filter(cu_is_deleted=False)
    serializer_class = EmployeeTransferHistorySerializer
    pagination_class = OnOffPagination

    def get_queryset(self):
        print("in queryset")
        user_id = self.request.query_params.get('employee_id', None)
        result = self.queryset.filter(cu_user=user_id)
        return result

    # @response_modify_decorator_get
    @response_modify_decorator_list_or_get_after_execution_for_onoff_pagination
    def get(self, request, *args, **kwargs):
        response = super(__class__, self).get(self, request, *args, **kwargs)
        return response


##employee payslip
class EmployeePaySlipDownloadView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get(self, request, *args, **kwargs):
        # print(response.data)
        year = self.request.query_params.get('year', None)
        month = self.request.query_params.get('month', None)
        user_id = self.request.query_params.get('employee_id', None)
        # user_id = self.requesr.user
        user_detail = TCoreUserDetail.objects.get(cu_user_id=user_id)
        emp_code = user_detail.cu_emp_code
        employee_name = user_detail.cu_user.get_full_name()
        employee_name = employee_name.upper()
        file_name = "Payslips" + emp_code + '_' + employee_name + '_' + employee_name
        month_dict = {1: "JAN", 2: "FEB", 3: "MAR", 4: "APR", 5: "MAY", 6: "JUN", 7: "JUL", 8: "AUG", 9: "SEP",
                      10: "OCT", 11: "NOV", 12: "DEC"}
        month = month_dict[int(month)]
        file_name = 'media/hrms/HrmsDocument/Documents/payslip/{}/{}/{}.PDF'.format(year, month, file_name)
        file_path = settings.MEDIA_ROOT_EXPORT + file_name
        try:
            if os.path.exists(file_path):
                url = settings.SERVER_URL + file_name if file_name else None
                return Response({'download_url': url, 'request_status': 1, 'msg': settings.MSG_SUCCESS})
            else:
                return Response({'request_status': 0, 'msg': 'Not Found'})
        except:
            return Response({'request_status': 0, 'msg': 'Not Found'})


class EmployeeListWithoutDetailsV2View(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreUserDetail.objects.filter(cu_user__is_superuser=False).values('cu_user').annotate(
            id = F('cu_user'),
            first_name =  F('cu_user__first_name'),
            last_name =  F('cu_user__last_name'),
            is_active =  F('cu_user__is_active'),
            is_superuser = F('cu_user__is_superuser'),
            email= F('cu_alt_email_id'),
            sap_id= F('sap_personnel_no'),
            department_id= F('department_id'),
            department_name= F('department__cd_name'),
            )

    @response_modify_decorator_for_get_after_execution_api_view
    def get(self,request, *args, **kwargs):
        import logging
        logging.getLogger(__name__)
        #print('queryset',self.queryset)
        search_key = self.request.query_params.get('search_key', None)
        department = self.request.query_params.get('department', None)
        module = self.request.query_params.get('module', None)
        team_approval_flag = self.request.query_params.get('team_approval_flag', None)
        login_user_details = self.request.user
        filter = dict()
        is_active = self.request.query_params.get('is_active', None)

        if is_active:
            if is_active == '1':
                filter['cu_is_deleted'] = False
                filter['cu_user__is_active'] = True
            else:
                filter['cu_is_deleted'] = True
                filter['cu_user__is_active'] = False

        
        if department:
            filter['department_id__in'] = department.split(',')

        #print('login_user_details',login_user_details.is_superuser)

        if login_user_details.is_superuser == False:
            
            which_type_of_user = TMasterModuleRoleUser.objects.filter(
                mmr_module__cm_name=module,
                mmr_user=login_user_details,
                mmr_is_deleted=False
            ).values_list('mmr_type', flat=True)

            if which_type_of_user:
                which_type_of_user = which_type_of_user[0]
            
            if module == 'pms':
                module = 'PMS'

            if module == 'hrms':
                module = 'ATTENDANCE & HRMS'

            if module == 'ETASK' or module == 'etask':
                module = 'E-Task'

            if module == 'vms':
                module = 'VMS'

            if team_approval_flag == '1':

                if which_type_of_user == 2:  # [Module Admin]
                    filter['cu_user__in'] = TMasterModuleRoleUser.objects.filter(
                        mmr_type__in=('3'),
                        mmr_module__cm_name=module,
                        mmr_is_deleted=False).values_list('mmr_user', flat=True)
                else:
                    filter['cu_user__in'] = TMasterModuleRoleUser.objects.filter(
                        mmr_type__in=('3'),
                        mmr_module__cm_name=module,
                        mmr_is_deleted=False,
                        mmr_user_id__in=self.queryset.filter(
                            reporting_head_id=login_user_details).values_list(
                            'cu_user_id', flat=True)).values_list('mmr_user', flat=True)

        #print('filter',filter)

        if search_key:
            search_key = search_key.lower()
            print('search_key',search_key)
            filter['cu_user__in'] = User.objects.annotate(
                    full_name=Concat('first_name', V(' '), 'last_name')).filter(
                    full_name__icontains=search_key)
        
        logging.info(filter)
        self.queryset = self.queryset.filter(**filter)
        #print('result',result.query)
        return Response(self.queryset)


class IntercomUploadExcelView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def post(self, request, *args, **kwargs):
        document = request.data['document']
        excel_data_df = pd.read_excel(document)
        excel_data_df = excel_data_df.to_dict(orient='record')
        for each in excel_data_df:
            floor  = TCoreFloor.objects.get(name=each['Floor'])
            HrmsIntercom.objects.get_or_create(
                floor = floor,
                name = each['Name'],
                ext_no = each['Ext. No'],
                created_by_id = 1
                )
        return Response({'result':excel_data_df})

class IntercomAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = HrmsIntercom.objects.all()
    serializer_class = IntercomAddSerializer
    pagination_class = OnOffPagination

    def get_queryset(self):
        filter = {}
        sort_field = '-id'
        name = self.request.query_params.get('name', None)
        floor = self.request.query_params.get('floor', None)
        ext_no = self.request.query_params.get('ext_no', None)
        if name:
            filter['name__icontains'] = name.replace(' ','')
        if floor:
            filter['floor__id__in'] = floor.split('.')
        if ext_no:
            filter['ext_no'] = ext_no
        result = self.queryset.filter(**filter).order_by('floor__name','name')
        return result

    @response_modify_decorator_post
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    @response_modify_decorator_list_or_get_before_execution_for_onoff_pagination
    def get(self, request, *args, **kwargs):
        return super(__class__, self).get(self, request, *args, **kwargs)

class IntercomEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = HrmsIntercom.objects.all()
    serializer_class = IntercomAddSerializer

    @response_modify_decorator_update
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        return super(__class__, self).get(self, request, *args, **kwargs)

class PreJoiningOnsetFormView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PreJoiningCandidateData.objects.filter(is_deleted=False)
    serializer_class = PreJoiningCandidateSerializer

class PreJoiningListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PreJoiningCandidateData.objects.filter(is_deleted=False)
    serializer_class = PreJoiningCandidateListSerializer
    pagination_class = OnOffPagination
    def get_queryset(self):
        sort_field='-id'
        filter = dict()
        queryset = self.queryset.filter(**filter).order_by(sort_field)
        return queryset


class PreJoiningUpdateView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PreJoiningCandidateData.objects.filter(is_deleted=False)
    serializer_class = PreJoiningUpdateSerializer

class PreJoinineeResourceAddView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PreJoineeResourceAllocation.objects.filter(is_deleted=False)
    serializer_class = PreJoineeResourceAddSerializer

class EmployeeMediclaimAddView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = EmployeeMediclaimDetails.objects.filter(is_deleted=False)
    serializer_class = EmployeeMediclaimDetailAddSerializer

class EmployeeMediclaimListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = EmployeeMediclaimDetails.objects.filter(is_deleted=False)
    serializer_class = EmployeeMediclaimDetailListSerializer
    pagination_class = OnOffPagination
    def get_queryset(self):
        sort_field='-id'
        filter = dict()
        employee_id = self.request.query_params.get('employee_id', None)
        employee_name = self.request.query_params.get('employee_name', None)
        employee_sap_id = self.request.query_params.get('employee_sap_id', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        if employee_sap_id:
            filter['employee__cu_user__sap_personnel_no'] = employee_sap_id

        if employee_id:
            filter['employee'] = employee_id

        if employee_name :
            employee_first_name = employee_name.lstrip()
            employee_last_name = employee_name.rstrip()
            f_name = employee_first_name.split(' ')[0]
            l_name = ' '.join(employee_last_name.split(' ')[1:])
            print(f_name + "*******" + l_name)
            filter['employee__first_name__icontains'] = f_name
            filter['employee__last_name__icontains'] = l_name

        if start_date and end_date:
            from datetime import datetime
            start_object = datetime.strptime(start_date, '%Y-%m-%d').date()
            filter['created_at__gte'] = start_object
            end_object = datetime.strptime(end_date, '%Y-%m-%d').date()
            delta = timedelta(days=1)
            end_delta_object = end_object + delta
            filter['created_at__lte'] = end_delta_object


        queryset = self.queryset.filter(**filter).order_by(sort_field)
        return queryset


class EmployeeMediclaimReportDownloadView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = EmployeeMediclaimDetails.objects.filter(is_deleted=False)
    serializer_class = EmployeeMediclaimDetailListSerializer
    # pagination_class = OnOffPagination
    def get_queryset(self):
        sort_field='-id'
        filter = dict()
        employee_id = self.request.query_params.get('employee_id', None)
        employee_name = self.request.query_params.get('employee_name', None)
        employee_sap_id = self.request.query_params.get('employee_sap_id', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        if employee_sap_id:
            filter['employee__cu_user__sap_personnel_no'] = employee_sap_id

        if employee_id:
            filter['employee'] = employee_id

        if employee_name :
            employee_first_name = employee_name.lstrip()
            employee_last_name = employee_name.rstrip()
            f_name = employee_first_name.split(' ')[0]
            l_name = ' '.join(employee_last_name.split(' ')[1:])
            print(f_name + "*******" + l_name)
            filter['employee__first_name__icontains'] = f_name
            filter['employee__last_name__icontains'] = l_name

        if start_date and end_date:
            from datetime import datetime
            start_object = datetime.strptime(start_date, '%Y-%m-%d').date()
            filter['created_at__gte'] = start_object
            end_object = datetime.strptime(end_date, '%Y-%m-%d').date()
            delta = timedelta(days=1)
            end_delta_object = end_object + delta
            filter['created_at__lte'] = end_delta_object


        queryset = self.queryset.filter(**filter).order_by(sort_field)
        return queryset

    def get(self, request, *args, **kwargs):
        response = super(__class__, self).get(self, request, *args, **kwargs)

        # 'id', 'employee', 'marital_status', 'employee_code', 'employee_name', 'employee_sap_id', 'spouse_name', 'spouse_gender', 'spouse_dob', 'first_child_name', 'first_child_gender', 'first_child_dob', 'second_child_name', 'second_child_gender', 'second_child_dob', 'include_parents', 'father_name', 'father_dob', 'mother_name', 'mother_dob', 'created_by', 'created_at'

        # print(response.data)
        data_list = list()
        for data in response.data:
            # print(data)
            data_list.append([data['employee_code'], data['employee_name'], data['employee_sap_id'],
                              data['spouse_name'], data['spouse_gender'], data['spouse_dob'],
                              data['first_child_name'], data['first_child_gender'], data['first_child_dob'],
                              data['second_child_name'], data['second_child_gender'], data['second_child_dob'],
                              data['father_name'], data['father_dob'], data['mother_name'], data['mother_dob']])

        file_name = ''
        if data_list:

            if os.path.isdir('media/hrms/mediclaim/document'):
                file_name = 'media/hrms/mediclaim/document/mediclaim_reporte.xlsx'
                file_path = settings.MEDIA_ROOT_EXPORT + file_name
                print(file_path)
            else:
                os.makedirs('media/hrms/mediclaim/document')
                file_name = 'media/hrms/mediclaim/document/mediclaim_reporte.xlsx'
                file_path = settings.MEDIA_ROOT_EXPORT + file_name

            final_df = pd.DataFrame(data_list, columns=['Employee_Code', 'Employee Name', 'Employee Sap Id',
                              'Spouse Name', 'Spouse Gender', 'Spouse Dob',
                              'First_Child_Name', 'First_Child_Gender', 'First_Child_Dob',
                              'Second_Child_Name', 'Second_Child_Gender', 'Second_Child_Dob',
                              'Father_Name', 'Father_Dob', 'Mother_Name', 'Mother_Dob'])

            export_csv = final_df.to_excel(file_path, index=None, header=True)
            if request.is_secure():
                protocol = 'https://'
            else:
                protocol = 'http://'

        url = getHostWithPort(request) + file_name if file_name else None
        if url:
            return Response({'request_status': 1, 'msg': 'Success', 'url': url})
        else:
            return Response({'request_status': 0, 'msg': 'Not Found', 'url': url})


class EmployeeMaritalStatusCheck(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get(self,request):
        if request.GET['employee_id']:
            marital_status = TCoreUserDetail.objects.filter(cu_user_id=request.GET['employee_id'])
            print(marital_status[0].marital_status)
            if marital_status:
                return JsonResponse({"marital_status":marital_status[0].marital_status},status=200)
            else:
                return JsonResponse({"error": "enter a valid employee id"}, status=400)

        else:
            return JsonResponse({"error": "First enter a employee_id"}, status=400)




class EmployeeMediclaimDetailsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = EmployeeMediclaimDetails.objects.filter(is_deleted=False)
    serializer_class = EmployeeMediclaimDetailListSerializer
    pagination_class = CSPageNumberPagination
    def get_queryset(self):
        sort_field='-id'
        filter = dict()
        employee_id = self.request.query_params.get('employee_id', None)
        if employee_id:
            filter['employee'] = employee_id
        queryset = self.queryset.filter(**filter).order_by(sort_field)
        return queryset

    @response_modify_decorator_list_or_get_after_execution_for_pagination
    def get(self, request, *args, **kwargs):
        response = super(__class__, self).get(self, request, args, kwargs)
        response.data['length'] = 1
        for data in response.data['results']:
            response.data['results'] = data
        if not response.data['results']:
            response.data['length'] = 0


        del response.data['count']
        del response.data['next']
        del response.data['previous']
        return response

class EmployeeMediclaimRetriveUpdateView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = EmployeeMediclaimDetails.objects.filter(is_deleted=False)
    serializer_class = EmployeeMediclaimDetailRetriveUpdateSerializer


class PreJoineeResourceAllocationReminder(APIView):
    permission_classes = [AllowAny]


    def send_next_reminder_for_probation(self, usr_obj,user_email,cc,request=None):
        employee_name = usr_obj.candidate_first_name + ' ' + usr_obj.candidate_last_name
        date_of_joining = str(usr_obj.expected_joining_date.date())
        final_str_for_subject_line = str(employee_name) + ':' + str(usr_obj.candidate_id) + ' to join on ' + date_of_joining + ":Reminder "
        if user_email:
            mail_data = {
                "employee_name": employee_name,
                "date_of_joining": date_of_joining,

            }
            from global_function import send_mail

            send_mail('HRMS-PJ-RA-R', user_email, mail_data,final_sub=final_str_for_subject_line)


    def get(self, request, *args, **kwargs):
        from datetime import datetime
        date = datetime.now()
        three_days_before_date = date - timedelta(3)
        prejoinee_obj = PreJoineeResourceAllocation.objects.filter(is_deleted=False,
                                                                   first_reminder_date__lte=three_days_before_date,
                                                                   reminder_state=0, submission_pending=True).values('employee').distinct()
        for each in prejoinee_obj:
            user_email = ['Up@shyamsteel.com', 'hemant@shyamsteel.com']
            cc = ['prakash.tripathi@shyamsteel.com']

        return Response({'request_status': 1, 'msg': 'Success'})



# mediclaim form enable edit

class EmployeeMediclaimEnableEditView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = MediclaimEnableTimeFrame.objects.filter(is_deleted=False)
    serializer_class = EmployeeMediclaimEnableEditSerializer