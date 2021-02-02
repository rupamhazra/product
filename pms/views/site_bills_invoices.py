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
from knox.auth import TokenAuthentication
from rest_framework import permissions
from knox.models import AuthToken

#Category with approval configuration

class SiteBillsInvoicesCategoryAddView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsSiteBillsInvoicesCategoryMaster.objects.filter(is_deleted=False).order_by('created_at')
    serializer_class=SiteBillsInvoicesCategoryAddSerializer
    pagination_class = OnOffPagination

    @response_modify_decorator_post
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
        
class SiteBillsInvoicesCategoryListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsSiteBillsInvoicesCategoryMaster.objects.filter(is_deleted=False).order_by('created_at')
    serializer_class=SiteBillsInvoicesCategoryListSerializer
    pagination_class = OnOffPagination
    
    @response_modify_decorator_list_or_get_after_execution_for_onoff_pagination
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

class SiteBillsInvoicesCategoryEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsSiteBillsInvoicesCategoryMaster.objects.filter(is_deleted=False).order_by('-id')
    serializer_class=SiteBillsInvoicesCategoryEditSerializer
    pagination_class = OnOffPagination
    
    def get_serializer_class(self):
        if self.request.method == 'PUT':
            return SiteBillsInvoicesCategoryEditSerializer
        
        return SiteBillsInvoicesCategorySingleSerializer

    @response_modify_decorator_update
    def put(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @response_modify_decorator_list_or_get_after_execution_for_onoff_pagination
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


#Site Bills and Invoices

class SiteBillsInvoicesAddView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsSiteBillsInvoices.objects.filter(is_deleted=False).order_by('-id')
    serializer_class=SiteBillsInvoicesAddSerializer

    @response_modify_decorator_post
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
    
class SiteBillsInvoicesListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsSiteBillsInvoices.objects.filter(is_deleted=False)
    serializer_class=SiteBillsInvoicesListSerializer
    pagination_class = OnOffPagination

    def get_queryset(self):
        filter = {}
        exclude = {}
        sort_field='-id'

        # Taking Parameter from URL
        
        approval = self.request.query_params.get('approval', None) #for approval
        report = self.request.query_params.get('report', None) # for report
        category = self.request.query_params.get('category', None) 
        project = self.request.query_params.get('project', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        status = self.request.query_params.get('status', None)
        created_by = self.request.query_params.get('created_by', None)

        ## Filter section

        if approval:
            login_user_id = self.request.user.id
            print('login_user_id',self.request.user)
            login_user_level = None
            login_user_level_details = PmsSiteBillsInvoicesApprovalConfiguration.objects.filter(
                user = self.request.user,
                category_id = category,
                is_deleted=False
                )
            print('login_user_level_details',login_user_level_details)
            if login_user_level_details:
                login_user_level = login_user_level_details[0]
                print('login_user_level',login_user_level)
           
            if login_user_level:
                if report:
                    approve_status = ('Pending','Reject','Approve',)
                    print('login_user_level.level',login_user_level.level_no)
                    filter['current_approval_level_no__gte'] = login_user_level.level_no 
                else:
                    #filter['status'] = 'Pending'
                    approve_status = ('Pending',)
                    filter['current_approval_level_view'] = login_user_level.level

                filter['pk__in'] = PmsSiteBillsInvoicesApproval.objects.filter(
                    approval_status__in = approve_status,
                    approval_user_level=login_user_level,
                    is_deleted=False
                    ).values_list('site_bills_invoices',flat=True)
            else:
                filter['pk__in'] = list()
            
        if category:
            filter['category__in'] = category.split(',')
        
        if project:
            filter['project__in'] = project.split(',')
        
        if status:
            filter['status__in'] = status.split(',')

        if start_date and end_date:
            filter['created_at__date__gte'] = start_date
            filter['created_at__date__lte'] = end_date

        if created_by:
            filter['created_by'] = created_by

        ## Sorting section

        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)

        if field_name and order_by:

            if field_name == 'created_by' and order_by == 'asc':
                sort_field ='created_by'

            if field_name =='created_by' and order_by=='desc':
                sort_field ='-created_by'
            
            if field_name == 'created_at' and order_by == 'asc':
                sort_field ='created_at'

            if field_name =='created_at' and order_by=='desc':
                sort_field ='-created_at'

            if field_name == 'file_code' and order_by == 'asc':
                sort_field ='file_code'

            if field_name =='file_code' and order_by=='desc':
                sort_field ='-file_code'

            if field_name =='category' and order_by=='asc':
                sort_field='category'

            if field_name =='category' and order_by=='desc':
                sort_field='-category'

            if field_name =='project' and order_by=='asc':
                sort_field='project'

            if field_name =='project' and order_by=='desc':
                sort_field='-project'

            if field_name =='document_name' and order_by=='asc':
                sort_field='document_name'

            if field_name =='document_name' and order_by=='desc':
                sort_field='-document_name'

        # Final Queryset
        #print('filter',filter)
        queryset = self.queryset.filter(**filter).exclude(**exclude).order_by(sort_field)
        #print('queryset',queryset.query)
        return queryset


    @response_modify_decorator_list_or_get_after_execution_for_onoff_pagination
    def list(self, request, *args, **kwargs):
        response = super(__class__, self).list(self, request, args, kwargs)
        return response

class SiteBillsInvoicesEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsSiteBillsInvoices.objects.filter(is_deleted=False).order_by('-id')
    serializer_class=SiteBillsInvoicesEditSerializer

    @response_modify_decorator_update
    def put(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class SiteBillsInvoicesDeleteView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsSiteBillsInvoices.objects.filter(is_deleted=False).order_by('-id')
    serializer_class=SiteBillsInvoicesDeleteSerializer

    @response_modify_decorator_update
    def put(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

# Approval

class SiteBillsInvoicesApprovalView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsSiteBillsInvoices.objects.filter(is_deleted=False).order_by('-id')
    serializer_class=SiteBillsInvoicesApprovalSerializer

    @response_modify_decorator_post
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
 
