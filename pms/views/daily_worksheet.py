from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from pms.models import *
from pms.serializers import *
import time
from multiplelookupfields import MultipleFieldLookupMixin
from rest_framework.views import APIView
from django.conf import settings
from pagination import CSLimitOffestpagination, CSPageNumberPagination, OnOffPagination
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
from global_function import *

'''
    For Knox 
    Author : Rupam Hazra
    Date : 16.03.2020
'''
from knox.auth import TokenAuthentication
from rest_framework import permissions
from knox.models import AuthToken


#:::::::::::: PROJECTS ::::::::::::::::::::::::::::#

class DailyWorkSheetAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsDailyWorkSheet.objects.filter(is_deleted=False).order_by('-id')
    serializer_class = DailyWorkAddSerializer

    @response_modify_decorator_post
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    @response_modify_decorator_list_or_get_after_execution_for_onoff_pagination
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

class DailyWorkSheetListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    serializer_class = DailyWorkListSerializer
    pagination_class = OnOffPagination
    queryset = PmsDailyWorkSheet.objects.filter(Q(is_deleted=False))

    def get_queryset(self):
        user = self.request.user.id
        print(user)
        queryset = self.queryset
        employee_id = self.request.query_params.get('employee_id', None)
        if employee_id:
            queryset = queryset.filter((Q(owner__id=employee_id)))
        else:
            queryset = queryset.filter((Q(owner__id=user)))
        sort_field = '-start_time'
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        date = self.request.query_params.get('date', None)
        filter = {}
        if date:
            date = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.%fZ")
            filter['date'] = date

        if field_name and order_by:
            if field_name == 'date' and order_by == 'asc':
                sort_field = 'date'
            if field_name == 'date' and order_by == 'desc':
                sort_field = '-date'
            if field_name == "start_time" and order_by == 'asc':
                sort_field = "start_time"
            if field_name == "start_time" and order_by == 'desc':
                sort_field = "-start_time"
            if field_name == "end_time" and order_by == 'asc':
                sort_field = "end_time"
            if field_name == "end_time" and order_by == 'desc':
                sort_field = "-end_time"
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        # print(queryset.count())
        if start_date and end_date:
            start_object = datetime.strptime(start_date, '%Y-%m-%d')
            delta = timedelta(days=1)
            end_object = datetime.strptime(end_date, '%Y-%m-%d')
            # print("in if")
            return queryset.filter(date__date__gte=start_object,
                                   date__date__lte=end_object + delta).order_by(sort_field)



        return queryset.order_by(sort_field)

    @response_modify_decorator_list_or_get_after_execution_for_onoff_pagination
    def get(self, request, *args, **kwargs):
        response = super(DailyWorkSheetListView, self).get(self, request, args, kwargs)
        return response


class DailyWorkSheetEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsDailyWorkSheet.objects.filter(Q(is_deleted=False))
    serializer_class = DailyWorkSheetEditSerializer

    @response_modify_decorator_update
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        response = super(__class__, self).get(self, request, args, kwargs)
        return response


class DailyWorkSheetDeleteView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsDailyWorkSheet.objects.filter(Q(is_deleted=False))
    serializer_class = DailyWorkSheetDeleteSerializer


class DailyWorkSheetTaskListDownloadView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    serializer_class = DaylyWorkSheetListDownloadSerializerv
    queryset = PmsDailyWorkSheet.objects.filter(Q(is_deleted=False))

    def get_queryset(self):
        user = self.request.user.id
        # print(user)
        queryset = self.queryset
        employee_id = self.request.query_params.get('employee_id', None)
        if employee_id:
            queryset = queryset.filter((Q(owner__id=employee_id)))
        else:
            queryset = queryset.filter((Q(owner__id=user)))
        sort_field = '-date'
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        date = self.request.query_params.get('date', None)
        filter = {}
        if date:
            date = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.%fZ")
            filter['date'] = date

        if field_name and order_by:
            if field_name == 'date' and order_by == 'asc':
                sort_field = 'date'
            if field_name == 'date' and order_by == 'desc':
                sort_field = '-date'
            if field_name == "start_time" and order_by == 'asc':
                sort_field = "start_time"
            if field_name == "start_time" and order_by == 'desc':
                sort_field = "-start_time"
            if field_name == "end_time" and order_by == 'asc':
                sort_field = "end_time"
            if field_name == "end_time" and order_by == 'desc':
                sort_field = "-end_time"
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        # print(queryset.count())
        if start_date and end_date:
            start_object = datetime.strptime(start_date, '%Y-%m-%d')
            delta = timedelta(days=1)
            end_object = datetime.strptime(end_date, '%Y-%m-%d')
            # print("in if")
            return queryset.filter(date__date__gte=start_object,
                                        date__date__lte=end_object + delta).order_by(sort_field)
        return queryset.order_by(sort_field)

    def get(self, request, *args, **kwargs):
        response = super(__class__, self).get(self, request, args, kwargs)
        if len(response.data):
            df_report = pd.DataFrame.from_records(response.data)
            df_report = df_report[['date','start_time', 'end_time','work_done']]
            file_path = settings.MEDIA_ROOT_EXPORT + self.create_file_path()
            df_report.to_excel(file_path,index=None,header=['Date','Start Time', 'End Time','Work Done'])
            file_name = self.create_file_path()
            url = getHostWithPort(request) + file_name if file_name else None
            return Response({'request_status':1,'msg':'Success', 'url': url})
        else:
            return Response({'request_status':0,'msg':'Data Not Found'})

    def create_file_path(self):
        if os.path.isdir('media/pms'):
            file_name = 'media/pms/daily_work_sheet.xlsx'
        else:
            os.makedirs('media/pms')
            file_name = 'media/pms/daily_work_sheet.xlsx'
        return file_name