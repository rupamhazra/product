"""
Created by Shubhadeep on 07-09-2020
"""
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework import serializers
from eticket.models_resource_mgmnt import *
from eticket.serializer_resource_mgmnt import *
from rest_framework.views import APIView
from django.conf import settings
from django.db.models import Q
from pagination import CSLimitOffestpagination,CSPageNumberPagination,OnOffPagination
from rest_framework import filters
from datetime import datetime
import collections
from rest_framework.exceptions import APIException
from django_filters.rest_framework import DjangoFilterBackend
from users.models import TCoreUserDetail
from custom_decorator import *
from rest_framework.parsers import FileUploadParser
import os
from pms.custom_filter import *
from global_function import getHostWithPort, worksheet_merge_range, worksheet_write, worksheet_merge_range_by_width
from knox.auth import TokenAuthentication
from rest_framework import permissions
from knox.models import AuthToken


class ETICKETResourceDeviceTypeMasterView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = ETICKETResourceDeviceTypeMaster.objects.filter(is_deleted=False)
    serializer_class = ETICKETResourceDeviceTypeMasterSerializer
    pagination_class = OnOffPagination
    filter_backends = [filters.OrderingFilter]
    
    def get_queryset(self,*args,**kwargs):
        return self.queryset.all()

class ETICKETResourceDeviceTypeMasterEditView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = ETICKETResourceDeviceTypeMaster.objects.filter(is_deleted=False)
    serializer_class = ETICKETResourceDeviceTypeMasterSerializer

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save()

class ETICKETResourceDeviceMasterView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = ETICKETResourceDeviceMaster.objects.filter(is_deleted=False)
    serializer_class = ETICKETResourceDeviceMasterSerializer
    pagination_class = OnOffPagination
    filter_backends = [filters.OrderingFilter]
    
    def get_queryset(self,*args,**kwargs):
        is_assigned = self.request.query_params.get('assigned', None)
        assigned_from_date_str = self.request.query_params.get('assigned_from_date', None)
        assigned_to_date_str = self.request.query_params.get('assigned_to_date', None)
        employee_ids_str = self.request.query_params.get('employee_ids', '')
        search_key = self.request.query_params.get('search_key', '').strip()

        if is_assigned is not None:
            is_assigned = int(is_assigned)
            self.queryset = self.queryset.filter(is_assigned=is_assigned)
        
        if len(search_key) > 0:
            self.queryset = self.queryset.filter(Q(specification__icontains=search_key) | 
                Q(po_no__icontains=search_key) | 
                Q(request_no__icontains=search_key) | 
                Q(sr_no__icontains=search_key) | 
                Q(oem__icontains=search_key) | 
                Q(oem_sr_no__icontains=search_key) | 
                Q(model__icontains=search_key) | 
                Q(tag_no__icontains=search_key))

        #region -this section filters in device assignement table
        device_assignment_query = None
        if assigned_from_date_str and assigned_to_date_str:
            from_date = datetime.strptime(assigned_from_date_str, '%Y-%m-%d')
            to_date = datetime.strptime(assigned_to_date_str, '%Y-%m-%d')
            to_date = to_date.replace(hour=23, minute=59, second=59)
            device_assignment_query = ETICKETResourceDeviceAssignment.objects.exclude(assigned_at__isnull=True).filter(
                            is_deleted=False,
                            device__in=self.queryset, 
                            assigned_at__gte=from_date,
                            assigned_at__lte=to_date)
        
        if employee_ids_str:
            if device_assignment_query is None:
                device_assignment_query = ETICKETResourceDeviceAssignment.objects.filter(is_deleted=False)
            employee_ids = []
            for val in employee_ids_str.split(','):
                if val.isdigit():
                    employee_ids.append(val)
            device_assignment_query = device_assignment_query.filter(
                            device__in=self.queryset, employee__in=employee_ids)
        
        if device_assignment_query is not None:
            filtered_device_ids = list(device_assignment_query.values_list('device_id', flat=True))
            self.queryset = self.queryset.filter(id__in=filtered_device_ids)
        #endregion

        return self.queryset.order_by('-updated_at')

class ETICKETResourceDeviceMasterDownloadView(ETICKETResourceDeviceMasterView):
    pagination_class = None

    def get(self, request, *args, **kwargs):
        response = super(__class__, self).get(request, args, kwargs)
        data = response.data
        if not os.path.isdir('media/eticket/resource_mngmngt/document'):
            os.makedirs('media/eticket/resource_mngmngt/document')
        file_name = 'media/eticket/resource_mngmngt/document/inventory_list.xlsx'
        file_path = settings.MEDIA_ROOT_EXPORT + file_name
        import xlsxwriter
        workbook = xlsxwriter.Workbook(file_path)
        worksheet = workbook.add_worksheet()
        header_format = workbook.add_format({'bold': True, 'font_size': 9, 'align': 'center', 'valign': 'vcenter'})
        cell_format = workbook.add_format({'font_size': 9, 'font_color': '#1e1e1e', 'align': 'center', 'valign': 'vcenter'})
        cell_width_map, cell_height_map = {}, {}
        
        headers = ['Sl No.', 'Device Type', 'OEM', 'Model', 'Date of Purchase', 'Specification', 'Request No.', 'PO No.', 'SR No.', 
                    'OEM SR No.', 'Tag No.', 'Status']
        assigment_headers = ['Employee', 'Assigned Date', 'Department', 'Location', 'Seat No.', 'OS', 'MS Office', 'SAP', 'E-Scan', 'VPS', 'VPN Id', 'Status']
        col_idx, row_idx = 0, 0
        for h_idx, header in enumerate(headers):
            worksheet_merge_range(worksheet, cell_height_map, row_idx, col_idx + h_idx, row_idx + 1, col_idx + h_idx, 
                header, header_format)
        worksheet_merge_range_by_width(worksheet, cell_width_map, row_idx, len(headers), row_idx, len(headers) + len(assigment_headers) - 1, 
                'Assignment Details', header_format)
        row_idx += 1
        col_idx = len(headers)
        for h_idx, header in enumerate(assigment_headers):
            worksheet_write(worksheet, cell_width_map, row_idx, col_idx + h_idx, header, header_format)
        row_idx += 1
        col_idx = 0
        for i, result in enumerate(response.data):
            purchase_date = '-'
            if result.get('purchased_at'):
                purchase_date = datetime.fromisoformat(result.get('purchased_at')).strftime('%d/%m/%Y')
            row = [i + 1, result.get('device_type_details')['type_name'],
                result.get('oem') if result.get('oem') else '-',
                result.get('model') if result.get('model') else '-',
                purchase_date,
                result.get('specification') if result.get('specification') else '-', 
                result.get('request_no') if result.get('request_no') else '-', 
                result.get('po_no') if result.get('po_no') else '-', 
                result.get('sr_no') if result.get('sr_no') else '-',
                result.get('oem_sr_no') if result.get('oem_sr_no') else '-',
                result.get('tag_no') if result.get('tag_no') else '-',
                'Assigned' if result.get('is_assigned') else 'Not Assigned'
                ]
            start_row_idx = row_idx    
            col_idx = len(headers)
            for assgn_row_id, assignment in enumerate(result['assignment_details']):
                assigned_at, status = '-', '-',
                if assignment.get('assigned_at'):
                    assigned_at = datetime.fromisoformat(assignment.get('assigned_at')).strftime('%d/%m/%Y')
                if assignment.get('is_current'):
                    status = 'Current User'
                else:
                    if assignment.get('assigned_upto'):
                        status = 'Unassigned on {0}'.format(
                                datetime.fromisoformat(assignment.get('assigned_upto')).strftime('%d/%m/%Y'))
                    else:
                        status = 'Unassigned'
                assignment_row = [assignment['employee_details']['name'], 
                        assigned_at,
                        assignment['employee_details']['department'],
                        assignment['employee_details']['location'] if assignment['employee_details']['location'] else '-',
                        assignment['seat_no'] if assignment['seat_no'] else '-',
                        assignment['os'] if assignment['os'] else '-',
                        'Yes' if assignment['ms_office'] else 'No',
                        'Yes' if assignment['sap'] else 'No',
                        'Yes' if assignment['e_scan'] else 'No',
                        'Yes' if assignment['vpn'] else 'No',
                        assignment['vpn_id'] if assignment['vpn_id'] else '-',
                        status]
                for item in assignment_row:
                    worksheet_write(worksheet, cell_width_map, row_idx, col_idx, str(item), cell_format)
                    col_idx += 1
                if assgn_row_id < len(result['assignment_details']) - 1:
                    row_idx += 1
                    col_idx = len(headers)
            col_idx = 0
            for item in row:
                if row_idx > start_row_idx:
                    worksheet_merge_range_by_width(worksheet, cell_width_map, start_row_idx, col_idx, row_idx, col_idx, 
                                        str(item), cell_format)
                else:
                    worksheet_write(worksheet, cell_width_map, row_idx, col_idx, str(item), cell_format)
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


class ETICKETResourceDeviceMasterEditView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = ETICKETResourceDeviceMaster.objects.filter(is_deleted=False)
    serializer_class = ETICKETResourceDeviceMasterSerializer

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save()

class ETICKETResourceDeviceAssignmentView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = ETICKETResourceDeviceAssignment.objects.filter(is_deleted=False)
    serializer_class = ETICKETResourceDeviceAssignmentSerializer
    pagination_class = OnOffPagination
    filter_backends = [filters.OrderingFilter]
    
    def get_queryset(self,*args,**kwargs):
        return self.queryset.all()

class ETICKETResourceDeviceAssignmentEditView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = ETICKETResourceDeviceAssignment.objects.filter(is_deleted=False)
    serializer_class = ETICKETResourceDeviceAssignmentSerializer

    def perform_destroy(self, instance):
        pass

class ETICKETResourceDeviceUnassignmentView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = ETICKETResourceDeviceMaster.objects.filter(is_deleted=False)
    serializer_class = ETICKETResourceDeviceUnassignmentSerializer

    def perform_destroy(self, instance):
        pass