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

# Category

class ContractorsCategoryAddView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsContractorsCategoryMaster.objects.filter(is_deleted=False).order_by('created_at')
    serializer_class=ContractorsCategoryAddSerializer
    pagination_class = OnOffPagination

    @response_modify_decorator_post
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
        
class ContractorsCategoryListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsContractorsCategoryMaster.objects.filter(is_deleted=False)
    serializer_class=ContractorsCategoryListSerializer
    pagination_class = OnOffPagination
    
    def get_queryset(self):
        filter = {}
        exclude = {}
        sort_field='-created_at'
        
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)

        if field_name and order_by:

            if field_name == 'name' and order_by == 'asc':
                sort_field ='name'

            if field_name =='name' and order_by=='desc':
                sort_field ='-name'

        queryset = self.queryset.filter(**filter).exclude(**exclude).order_by(sort_field)
        return queryset


    @response_modify_decorator_list_or_get_after_execution_for_onoff_pagination
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

class ContractorsCategoryEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsContractorsCategoryMaster.objects.filter(is_deleted=False).order_by('-id')
    serializer_class=ContractorsCategoryEditSerializer
    pagination_class = OnOffPagination
    
    def get_serializer_class(self):
        if self.request.method == 'PUT':
            return ContractorsCategoryEditSerializer
        
        return ContractorsCategorySingleSerializer

    @response_modify_decorator_update
    def put(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @response_modify_decorator_list_or_get_after_execution_for_onoff_pagination
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
class ContractorsCategoryDeleteView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsContractorsCategoryMaster.objects.filter(is_deleted=False).order_by('-id')
    serializer_class=ContractorsCategoryDeleteSerializer
    pagination_class = OnOffPagination
    
    @response_modify_decorator_update
    def put(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

# Contractors

class ContractorsAddView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsContractor.objects.filter(is_deleted=False).order_by('-id')
    serializer_class = ContractorsAddSerializer

    @response_modify_decorator_post
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
    
class ContractorsListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsContractor.objects.filter(is_deleted=False)
    serializer_class=ContractorsListSerializer
    pagination_class = OnOffPagination

    def get_queryset(self):
        filter = {}
        exclude = {}
        sort_field='-id'

        # Taking Parameter from URL

        category = self.request.query_params.get('category', None) 
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        created_by = self.request.query_params.get('created_by', None)
        name = self.request.query_params.get('name', None)
        search_key = self.request.query_params.get('search_key', None)

        ## Filter section

          
        if category:
            filter['category__in'] = category.split(',')

        if start_date and end_date:
            filter['created_at__date__gte'] = start_date
            filter['created_at__date__lte'] = end_date

        if created_by:
            filter['created_by'] = created_by
        
        if search_key:
            filter['pk__in'] = self.queryset.filter(
                Q(name__icontains=search_key) | 
                Q(phone_no__icontains=search_key) | 
                Q(email__icontains=search_key)
                ).values_list('id',flat=True)

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

            if field_name =='category' and order_by=='asc':
                sort_field='category'

            if field_name =='category' and order_by=='desc':
                sort_field='-category'
            
            if field_name =='contact_person_name' and order_by=='asc':
                sort_field='contact_person_name'

            if field_name =='contact_person_name' and order_by=='desc':
                sort_field='-contact_person_name'
            
            if field_name =='phone_no' and order_by=='asc':
                sort_field='phone_no'

            if field_name =='phone_no' and order_by=='desc':
                sort_field='-phone_no'
            
            if field_name =='email' and order_by=='asc':
                sort_field='email'

            if field_name =='email' and order_by=='desc':
                sort_field='-email'
            
            if field_name =='name' and order_by=='asc':
                sort_field='name'

            if field_name =='name' and order_by=='desc':
                sort_field='-name'

        # Final Queryset
        #print('filter',filter)
        queryset = self.queryset.filter(**filter).exclude(**exclude).order_by(sort_field)
        #print('queryset',queryset.query)
        return queryset


    @response_modify_decorator_list_or_get_after_execution_for_onoff_pagination
    def list(self, request, *args, **kwargs):
        response = super(__class__, self).list(self, request, args, kwargs)
        return response

class ContractorsListDownloadView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsContractor.objects.filter(is_deleted=False)
    serializer_class=ContractorsListSerializer

    def get_queryset(self):
        filter = {}
        exclude = {}
        sort_field='-id'

        # Taking Parameter from URL

        category = self.request.query_params.get('category', None) 
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        created_by = self.request.query_params.get('created_by', None)
        name = self.request.query_params.get('name', None)
        search_key = self.request.query_params.get('search_key', None)

        ## Filter section

          
        if category:
            filter['category__in'] = category.split(',')

        if start_date and end_date:
            filter['created_at__date__gte'] = start_date
            filter['created_at__date__lte'] = end_date

        if created_by:
            filter['created_by'] = created_by
        
        if search_key:
            filter['pk__in'] = self.queryset.filter(
                Q(name__icontains=search_key) | 
                Q(phone_no__icontains=search_key) | 
                Q(email__icontains=search_key)
                ).values_list('id',flat=True)

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

            if field_name =='category' and order_by=='asc':
                sort_field='category'

            if field_name =='category' and order_by=='desc':
                sort_field='-category'
            
            if field_name =='contact_person_name' and order_by=='asc':
                sort_field='contact_person_name'

            if field_name =='contact_person_name' and order_by=='desc':
                sort_field='-contact_person_name'
            
            if field_name =='phone_no' and order_by=='asc':
                sort_field='phone_no'

            if field_name =='phone_no' and order_by=='desc':
                sort_field='-phone_no'
            
            if field_name =='email' and order_by=='asc':
                sort_field='email'

            if field_name =='email' and order_by=='desc':
                sort_field='-email'
            
            if field_name =='name' and order_by=='asc':
                sort_field='name'

            if field_name =='name' and order_by=='desc':
                sort_field='-name'

        # Final Queryset
        print('filter',filter)
        queryset = self.queryset.filter(**filter).exclude(**exclude).order_by(sort_field)
        #print('queryset',queryset.query)
        return queryset


    
    def list(self, request, *args, **kwargs):
        response = super(__class__, self).list(self, request, args, kwargs)
        data_list = list()
        #print('response.data',response.data)
        count = 0
        
        for data in response.data:
            count += 1
            data_list.append(
            [
            count,
            data['category']['name'],
            data['name'],
            data['contact_person_name'],
            data['phone_no'],
            data['email'],
            data['website'],
            data['address']
            ]
            )

        file_name = ''
        if data_list:
            if os.path.isdir('media/pms/contractors/document'):
                file_name = 'media/pms/contractors/document/contractors_list.xlsx'
                file_path = settings.MEDIA_ROOT_EXPORT + file_name
            else:
                os.makedirs('media/pms/contractors/document')
                file_name = 'media/pms/contractors/document/contractors_list.xlsx'
                file_path = settings.MEDIA_ROOT_EXPORT + file_name

            #print('file_path',file_path)

            final_df = pd.DataFrame(
                data_list, 
                columns=[
                'SL No.',
                'Category',
                'Name',
                'Contact Person Name',
                'Phone No',
                'Email Id',
                'Website',
                'Address'
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
            
            writer.save()

        url = getHostWithPort(request) + file_name if file_name else None
        print('url',url)
        if url:                    
            return Response({'request_status':1,'msg':'Success', 'url': url})
        else:
            return Response({'request_status':0,'msg':'Not Found', 'url': url}) 

class ContractorsEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsContractor.objects.filter(is_deleted=False).order_by('-id')
    serializer_class=ContractorsEditSerializer

    @response_modify_decorator_update
    def put(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class ContractorsDeleteView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsContractor.objects.filter(is_deleted=False).order_by('-id')
    serializer_class=ContractorsDeleteSerializer

    @response_modify_decorator_update
    def put(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
