"""
Created by Bishal on 28-08-2020
Reviewd and updated by Shubhadeep
"""
from django.shortcuts import render
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework import serializers
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
from global_function import getHostWithPort
from knox.auth import TokenAuthentication
from rest_framework import permissions
from knox.models import AuthToken

from redis_handler import pub


class PmsBatchingPlantBrandOfCementMasterView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsBatchingPlantBrandOfCementMaster.objects.filter(is_deleted=False)
    serializer_class = PmsBatchingPlantBrandOfCementMasterSerializer
    pagination_class = OnOffPagination
    filter_backends = [filters.OrderingFilter]

    def get_queryset(self, *args, **kwargs):
        return self.queryset.all()

    def get(self, request, *args, **kwargs):
        response = super(__class__, self).get(request, args, kwargs)
        return response

    @response_modify_decorator_post
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class PmsBatchingPlantBrandOfCementMasterEditView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsBatchingPlantBrandOfCementMaster.objects.filter(is_deleted=False)
    serializer_class = PmsBatchingPlantBrandOfCementMasterSerializer

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save()

    @response_modify_decorator_update
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)


class PmsBatchingPlantPurposeMasterView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsBatchingPlantPurposeMaster.objects.filter(is_deleted=False)
    serializer_class = PmsBatchingPlantPurposeMasterSerializer
    pagination_class = OnOffPagination
    filter_backends = [filters.OrderingFilter]

    def get_queryset(self, *args, **kwargs):
        return self.queryset.all()

    def get(self, request, *args, **kwargs):
        response = super(__class__, self).get(request, args, kwargs)
        return response

    @response_modify_decorator_post
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class PmsBatchingPlantPurposeMasterEditView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsBatchingPlantPurposeMaster.objects.filter(is_deleted=False)
    serializer_class = PmsBatchingPlantPurposeMasterSerializer

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save()

    @response_modify_decorator_update
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)


class PmsBatchingPlantConcreteMasterView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsBatchingPlantConcreteMaster.objects.filter(is_deleted=False)
    serializer_class = PmsBatchingPlantConcreteMasterSerializer
    pagination_class = OnOffPagination
    filter_backends = [filters.OrderingFilter]

    def get_queryset(self, *args, **kwargs):
        return self.queryset.all()

    def get(self, request, *args, **kwargs):
        response = super(__class__, self).get(request, args, kwargs)
        return response

    @response_modify_decorator_post
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class PmsBatchingPlantConcreteMasterEditView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsBatchingPlantConcreteMaster.objects.filter(is_deleted=False)
    serializer_class = PmsBatchingPlantConcreteMasterSerializer

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save()

    @response_modify_decorator_update
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)


class PmsBatchingPlantConcreteIngredientMasterView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsBatchingPlantConcreteIngredientMaster.objects.filter(is_deleted=False)
    serializer_class = PmsBatchingPlantConcreteIngredientMasterSerializer
    pagination_class = OnOffPagination
    filter_backends = [filters.OrderingFilter]

    def get_queryset(self, *args, **kwargs):
        return self.queryset.all()

    def get(self, request, *args, **kwargs):
        response = super(__class__, self).get(request, args, kwargs)
        return response

    @response_modify_decorator_post
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class PmsBatchingPlantConcreteIngredientMasterEditView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsBatchingPlantConcreteIngredientMaster.objects.filter(is_deleted=False)
    serializer_class = PmsBatchingPlantConcreteIngredientMasterSerializer

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save()

    @response_modify_decorator_update
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)


class PmsBatchingPlantBatchingEntryAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsBatchingPlantBatchingEntry.objects.filter(is_deleted=False)
    serializer_class = PmsBatchingPlantBatchingEntryAddSerializer
    pagination_class = OnOffPagination
    filter_backends = [filters.OrderingFilter]

    def set_filters(self):
        # filter by datetime
        fromdt_str = self.request.query_params.get('fromdate', None)
        todt_str = self.request.query_params.get('todate', None)
        if fromdt_str is not None and todt_str is not None:
            from_date = datetime.strptime(fromdt_str, '%Y-%m-%d')
            to_date = datetime.strptime(todt_str, '%Y-%m-%d')
            to_date = to_date.replace(hour=23, minute=59, second=59)
            self.queryset = self.queryset.exclude(batch_processed_at__isnull=True).filter(batch_processed_at__gte=from_date, batch_processed_at__lte=to_date)

        # filter by project
        project = self.request.query_params.get('project', None)
        if project:
            self.queryset = self.queryset.filter(project=project)

    def get_queryset(self, *args, **kwargs):
        self.set_filters()
        return self.queryset.order_by('-id')

    def get(self, request, *args, **kwargs):
        response = super(__class__, self).get(request, args, kwargs)
        return response

    @response_modify_decorator_post
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        id = str(response.data['id'])
        document_status = response.data['document_status']
        if document_status == 1:
            print('Queueing batching plant entry {0}'.format(id))
            project_code, file_path = '', ''
            project_name = str(response.data['project_details']['name']).lower()
            if 'kendposi' in project_name:
                project_code = 'KD'
            elif 'rajkharsawan' in project_name:
                project_code = 'RJ'
            elif 'matla' in project_name:
                project_code = 'MT'
            if project_code != '':
                file_path = os.path.join(settings.MEDIA_ROOT, response.data['document'].split('/media/')[1])
                redis_data = [id, project_code, file_path]
                success, msg = pub.publish('ocr', redis_data)
            else:
                success, msg = False, "Project '{0}' is not configured for OCR processing".format(project_name)
            if not success:
                response.data['document_status'] = 4
                response.data['document_status_code'] = 'error'
                response.data['error_msg'] = msg
                PmsBatchingPlantBatchingEntry.objects.filter(pk=response.data['id']).update(document_status=4,
                                                                                            error_msg=msg)
        return response


class PmsBatchingPlantBatchingEntryEditView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsBatchingPlantBatchingEntry.objects.filter(is_deleted=False)
    serializer_class = PmsBatchingPlantBatchingEntryAddSerializer

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save()

    @response_modify_decorator_update
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)


class PmsBatchingPlantBatchingEntryChangeStatusView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsBatchingPlantBatchingEntry.objects.all()
    serializer_class = PmsBatchingPlantBatchingEntryChangeStatusSerializer

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save()

    @response_modify_decorator_post
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return response


class PmsBatchingPlantBatchingEntryDownloadView(PmsBatchingPlantBatchingEntryAddView):
    pagination_class = None

    def get(self, request, *args, **kwargs):
        response = super(__class__, self).get(request, args, kwargs)
        data = response.data
        if not os.path.isdir('media/pms/batching_plant/document'):
            os.makedirs('media/pms/batching_plant/document')
        file_name = 'media/pms/batching_plant/document/batching_list.xlsx'
        file_path = settings.MEDIA_ROOT_EXPORT + file_name
        import xlsxwriter
        workbook = xlsxwriter.Workbook(file_path)
        worksheet = workbook.add_worksheet()
        header_format = workbook.add_format({'bold': True, 'font_size': 9, 'align': 'center', 'valign': 'vcenter'})
        cell_format = workbook.add_format({'font_size': 9, 'font_color': '#1e1e1e', 'align': 'center', 'valign': 'vcenter'})
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

        headers = ['Sl No.', 'Project', 'Datetime', 'Grade of Concrete', 'Quantity', 'Brand of Cement', 'Purpose',
                   'Acceptance Status', 'Processing Status']

        col_idx, row_idx = 0, 0
        for h_idx, header in enumerate(headers):
            worksheet_write(row_idx, col_idx + h_idx, header, header_format)
        row_idx += 1
        for i, result in enumerate(response.data):
            date = '-'
            if result.get('batch_processed_at'):
                date = datetime.fromisoformat(result.get('batch_processed_at')).strftime('%d/%m/%Y %H:%M:%S')
            row = [i + 1, result.get('project_details')['name'], date,
                   result.get('concrete_details')['concrete_name'] if result.get('concrete_details') else '-',
                   result.get('concrete_quantity') if result.get('concrete_quantity') else '-',
                   result.get('brand_of_cement_details')['brand_of_cement'] if result.get('brand_of_cement_details') else '-',
                   result.get('purpose_details')['purpose'] if result.get('purpose_details') else '-',
                   result.get('acceptance_status_code'),
                   result.get('document_status_code')
                   ]
            for item in row:
                worksheet_write(row_idx, col_idx, str(item), cell_format)
                col_idx += 1
            row_idx += 1
            col_idx = 0

        workbook.close()

        if len(response.data):
            url = getHostWithPort(request) + file_name if file_name else None
            if url:
                return Response({'request_status': 1, 'msg': 'Found', 'url': url})
            else:
                return Response({'request_status': 0, 'msg': 'Not Found', 'url': url})
        else:
            return Response({'request_status': 0, 'msg': 'No Data', 'url': url})


class PmsBatchingPlantBatchingReportView(PmsBatchingPlantBatchingEntryAddView):
    def get_queryset(self, *args, **kwargs):
        self.set_filters()
        # filter out the completed batch entries only
        self.queryset = self.queryset.filter(document_status=3, batch_processed_at__isnull=False)
        ordering = self.request.query_params.get('ordering', None)
        if not ordering:
            ordering = '-batch_processed_at'
        print('PmsBatchingPlantBatchingReportView', ordering)
        return self.queryset.order_by(ordering)

    def get(self, request, *args, **kwargs):
        response = super(__class__, self).get(request, args, kwargs)
        data = response.data
        if type(data) is serializers.ReturnList:
            result = data
        else:
            result = data.get('results')

        formatted_entries = []
        for entry in result:
            entry_details = entry.get('entry_details')
            entry.pop('entry_details')
            consumption = {
                "cement": 0.0,
                "fly_ash": 0.0,
                "sand": 0.0,
                "agg_20mm": 0.0,
                "agg_10mm": 0.0,
                "water": 0.0,
                "admixture": 0.0
            }
            deviation = {
                "cement": None,
                "fly_ash": None,
                "sand": None,
                "agg_20mm": None,
                "agg_10mm": None,
                "water": None,
                "admixture": None
            }
            # calculate consumption per cum
            for item in entry_details:
                for key in consumption.keys():
                    consumption[key] += float(item.get(key))
            for key in consumption.keys():
                qty = float(entry.get('concrete_quantity')) if entry.get('concrete_quantity') else 0.0
                if qty > 0:
                    consumption[key] = round(consumption[key] / qty, 3)
                else:
                    consumption[key] = 0
            # --

            # calculate deviation
            ingrdnt_masters = PmsBatchingPlantConcreteIngredientMaster.objects.filter(
                project=entry.get('project'),
                concrete_master=entry.get('concrete_master'),
                brand_of_cement_master=entry.get('brand_of_cement_master'),
                purpose_master=entry.get('purpose_master'))

            if ingrdnt_masters:
                ingrdnt_master = ingrdnt_masters.first()
                for key in consumption.keys():
                    deviation[key] = round(consumption[key]
                                           - float(str(getattr(ingrdnt_master, key))), 3)
            # --

            entry['consumption'] = consumption
            entry['deviation'] = deviation
            formatted_entries.append(entry)

        if type(data) is serializers.ReturnList:
            response.data = formatted_entries
        else:
            response.data['results'] = formatted_entries

        return response


class PmsBatchingPlantBatchingReportDownloadView(PmsBatchingPlantBatchingReportView):
    pagination_class = None

    def get(self, request, *args, **kwargs):
        response = super(__class__, self).get(request, args, kwargs)
        if not os.path.isdir('media/pms/batching_plant/document'):
            os.makedirs('media/pms/batching_plant/document')
        file_name = 'media/pms/batching_plant/document/batching_report.xlsx'
        file_path = settings.MEDIA_ROOT_EXPORT + file_name

        import xlsxwriter
        workbook = xlsxwriter.Workbook(file_path)
        worksheet = workbook.add_worksheet()
        header_format = workbook.add_format({'bold': True, 'font_size': 9, 'align': 'center', 'valign': 'vcenter'})
        cell_format = workbook.add_format({'font_size': 9, 'font_color': '#1e1e1e', 'align': 'center', 'valign': 'vcenter'})
        header_wrap_format = workbook.add_format({'font_size': 9, 'bold': True, 'font_color': '#1e1e1e', 'align': 'center', 'text_wrap': True, 'valign': 'vcenter'})

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

        worksheet_merge_range(0, 0, 0, 4, '', header_format)
        worksheet_write(1, 0, 'Sl No', header_format)
        worksheet_write(1, 1, 'Project Name', header_format)
        worksheet_write(1, 2, 'Datetime', header_format)
        worksheet_write(1, 3, 'Grade of Concrete', header_format)
        worksheet_write(1, 4, 'Quantity', header_format)

        col_idx = 5
        headers = ['20 mm Aggregate\n(Kg/cum)', '10 mm Aggregate\n(Kg/cum)', 'Coarse Sand\n(Kg/cum)',
                   'Cement\n(Kg/cum)', 'Admixture\n(Kg/cum)', 'Water\n(Kg/cum)', 'FLY ASH\n(Kg/cum)']
        for i in range(2):
            if i == 0:
                txt = 'Consumption'
            else:
                txt = 'Deviation'
            worksheet_merge_range(0, col_idx, 0, col_idx + 6, txt, header_format)
            for h_idx, header in enumerate(headers):
                worksheet_write(1, col_idx + h_idx, header, header_wrap_format)
            col_idx = col_idx + 7

        for i, result in enumerate(response.data):
            date = '-'
            if result.get('batch_processed_at'):
                date = datetime.fromisoformat(result.get('batch_processed_at')).strftime('%d/%m/%Y %H:%M:%S')
            row = [i + 1, result.get('project_details')['name'], date, result.get('concrete_details')['concrete_name'],
                   result.get('concrete_quantity'),
                   result.get('consumption')['agg_20mm'] if result.get('consumption')['agg_20mm'] else '-',
                   result.get('consumption')['agg_10mm'] if result.get('consumption')['agg_10mm'] else '-',
                   result.get('consumption')['sand'] if result.get('consumption')['sand'] else '-',
                   result.get('consumption')['cement'] if result.get('consumption')['cement'] else '-',
                   result.get('consumption')['admixture'] if result.get('consumption')['admixture'] else '-',
                   result.get('consumption')['water'] if result.get('consumption')['water'] else '-',
                   result.get('consumption')['fly_ash'] if result.get('consumption')['fly_ash'] else '-',
                   result.get('deviation')['agg_20mm'] if result.get('deviation')['agg_20mm'] else '-',
                   result.get('deviation')['agg_10mm'] if result.get('deviation')['agg_10mm'] else '-',
                   result.get('deviation')['sand'] if result.get('deviation')['sand'] else '-',
                   result.get('deviation')['cement'] if result.get('deviation')['cement'] else '-',
                   result.get('deviation')['admixture'] if result.get('deviation')['admixture'] else '-',
                   result.get('deviation')['water'] if result.get('deviation')['water'] else '-',
                   result.get('deviation')['fly_ash'] if result.get('deviation')['fly_ash'] else '-']
            row_idx, col_idx = i + 2, 0
            for item in row:
                worksheet_write(row_idx, col_idx, str(item), cell_format)
                col_idx += 1

        workbook.close()

        if len(response.data):
            url = getHostWithPort(request) + file_name if file_name else None
            if url:
                return Response({'request_status': 1, 'msg': 'Found', 'url': url})
            else:
                return Response({'request_status': 0, 'msg': 'Not Found', 'url': url})
        else:
            return Response({'request_status': 0, 'msg': 'No Data', 'url': url})
