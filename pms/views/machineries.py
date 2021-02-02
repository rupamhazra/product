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
from holidays.models import *
import collections
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
import random
from global_function import getHostWithPort
'''
    For Knox 
    Author : Rupam Hazra
    Date : 16.03.2020
'''
from knox.auth import TokenAuthentication
from rest_framework import permissions
from knox.models import AuthToken

#:::::::::::::::::  MECHINARY MASTER :::::::::::::::#
class MachineriesAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsMachineries.objects.filter(is_deleted=False).order_by('-id')
    serializer_class = MachineriesAddSerializer
    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        return response
    # def get(self, request, *args, **kwargs):
    #     response = super(MachineriesAddView, self).get(self, request, args, kwargs)
    #     print('response.data',response.data)
    #     for data in response.data:
    #         if data["owner_type"] == 1:
    #             machinary_rented_details_queryset = PmsMachinaryRentedDetails.objects.filter(
    #                 equipment=data["id"],is_deleted=False)
    #             rental_details = dict()
    #             for machinary_rent in machinary_rented_details_queryset:
    #                 rental_details['id'] = machinary_rent.id
    #                 rental_details['equipment'] = machinary_rent.equipment.id
    #                 rental_details['vendor'] = machinary_rent.vendor.id
    #                 rental_details['rent_amount'] = machinary_rent.rent_amount
    #                 rental_details['type_of_rent'] = machinary_rent.type_of_rent.id
    #             if rental_details:
    #                 data["rental_details"] = rental_details
    #         elif data["owner_type"] == 2:
    #             owner_queryset = PmsMachinaryOwnerDetails.objects.filter(equipment=data["id"], is_deleted=False)
    #             owner_dict = {}
    #             for owner in owner_queryset:
    #                 owner_dict['id'] = owner.id
    #                 owner_dict['equipment'] = owner.equipment.id
    #                 owner_dict['purchase_date'] = owner.purchase_date
    #                 owner_dict['price'] = owner.price
    #
    #                 if owner.is_emi_available:
    #                     emi_queryset = PmsMachinaryOwnerEmiDetails.objects.filter(equipment_owner_details=owner,
    #                                                                               equipment=data["id"],
    #                                                                               is_deleted=False)
    #                     emi_dict = {}
    #                     for emi in emi_queryset:
    #                         emi_dict['id'] = emi.id
    #                         emi_dict['equipment'] = emi.equipment
    #                         emi_dict['equipment_owner_details'] = emi.equipment_owner_details
    #                         emi_dict['amount'] = emi.amount
    #                         emi_dict['start_date'] = emi.start_date
    #                         emi_dict['no_of_total_installment'] = emi.no_of_total_installment
    #
    #                     if emi_dict:
    #                         owner_dict['owner_emi_details'] = emi_dict
    #             if owner_dict:
    #                 data['owner_details'] = owner_dict
    #         elif data["owner_type"] == 3:
    #             contract_queryset = PmsMachinaryContractDetails.objects.filter(equipment=data["id"], is_deleted=False)
    #             contract_dict = {}
    #             for contract in contract_queryset:
    #                 contract_dict['id'] = contract.id
    #                 contract_dict['equipment'] = contract.equipment.id
    #                 contract_dict['contractor'] = contract.contractor.id
    #             data['contract_details'] = contract_dict
    #         else:
    #             pass
    #     return response
class MachineriesEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsMachineries.objects.all()
    serializer_class = MachineriesEditSerializer
    def get(self, request, *args, **kwargs):
        response = super(MachineriesEditView, self).get(self, request, args, kwargs)
        #print('response', response.data)
        #print('equipment_category', type(response.data['equipment_category']))

        ## Start Functional Specification Document - PMS_V4.0 | Date : 22-07-2020 | Rupam Hazra ##
        pmsProjectsMachinaryMapping = PmsProjectsMachinaryMapping.objects.filter(machinary=response.data['id'],is_deleted=False).annotate(
                name=F('project__name'),
                project_g_id = F('project__project_g_id'),
                start_date = F('machinary_s_d_req'),
                end_date = F('machinary_e_d_req'),
                ).values('project','name','project_g_id','start_date','end_date')

        response.data['project_list'] = pmsProjectsMachinaryMapping

        ## Start Functional Specification Document - PMS_V4.0 | Date : 22-07-2020 | Rupam Hazra ##

        w_c_details = {}
        PmsMachineriesWorkingCategoryde = PmsMachineriesWorkingCategory.objects.filter(
            id=response.data['equipment_category'],is_deleted=False)
        #print('PmsMachineriesWorkingCategory',PmsMachineriesWorkingCategoryde)
        for e_PmsMachineriesWorkingCategoryde in PmsMachineriesWorkingCategoryde:
            w_c_details = { 'id':e_PmsMachineriesWorkingCategoryde.id,
                            'name':e_PmsMachineriesWorkingCategoryde.name,
                            'is_deleted': e_PmsMachineriesWorkingCategoryde.is_deleted,
                            }

        response.data['equipment_category_details'] = w_c_details
        PmsMachineriesDoc = PmsMachineriesDetailsDocument.objects.filter(
            equipment=response.data['id'],is_deleted=False)
        #print('PmsMachineriesDoc', PmsMachineriesDoc)
        m_d_details_list=[]
        #request = self.context.get('request')
        for e_PmsMachineriesDoc in PmsMachineriesDoc:
            m_d_details = { 'id':e_PmsMachineriesDoc.id,
                            'name':e_PmsMachineriesDoc.document_name,
                            'document': request.build_absolute_uri(e_PmsMachineriesDoc.document.url),
                            'is_deleted': e_PmsMachineriesDoc.is_deleted,
                            }
            m_d_details_list.append(m_d_details)
        #print('m_d_details_list',m_d_details_list)
        response.data['document_details'] = m_d_details_list
        if response.data["owner_type"] == 1:
            # print('xyz',gfsdsdf)
            machinary_rented_details_queryset = PmsMachinaryRentedDetails.objects.filter(equipment=response.data["id"],
                                                                                         is_deleted=False)
            #print('machinary_rented_details_queryset',machinary_rented_details_queryset)
            rental_details = dict()
            for machinary_rent in machinary_rented_details_queryset:
                rental_details['id'] = machinary_rent.id
                rental_details['equipment'] = machinary_rent.equipment.id
                rental_details['vendor'] = machinary_rent.vendor.id if machinary_rent.vendor else None
                rental_details['rent_amount'] = machinary_rent.rent_amount
                rental_details['type_of_rent'] = machinary_rent.type_of_rent.id if machinary_rent.type_of_rent else None
                rental_details['start_date'] =machinary_rent.start_date
                rental_details['end_date'] =machinary_rent.end_date
            if rental_details:
                response.data["rental_details"] = rental_details
                if machinary_rent.vendor:
                    m_rented_details_vendor = PmsExternalUsers.objects.filter(
                        pk=machinary_rent.vendor.id,is_deleted=False)
                    # print('m_rented_details_vendor',m_rented_details_vendor)
                    if m_rented_details_vendor:
                        for e_m_rented_details_vendor in m_rented_details_vendor:
                            m_v_details = {'id': e_m_rented_details_vendor.id,
                                        'name': e_m_rented_details_vendor.contact_person_name,
                                        'is_deleted': e_m_rented_details_vendor.is_deleted,
                                        }
                        response.data["rental_details"]['vendor_details']= m_v_details
                    else:
                        response.data["rental_details"]['vendor_details']= {}
                else:
                    response.data["rental_details"]['vendor_details']= {}
            else:
                response.data["rental_details"] = {}
        elif response.data["owner_type"] == 2:
            owner_queryset = PmsMachinaryOwnerDetails.objects.filter(equipment=response.data["id"], is_deleted=False)
            print('owner_queryset',owner_queryset)
            owner_dict = {}
            for owner in owner_queryset:
                owner_dict['id'] = owner.id
                owner_dict['equipment'] = owner.equipment.id
                owner_dict['purchase_date'] = owner.purchase_date
                owner_dict['price'] = owner.price
                owner_dict['is_emi_available'] = owner.is_emi_available

                if owner.is_emi_available:
                    emi_queryset = PmsMachinaryOwnerEmiDetails.objects.filter(equipment_owner_details=owner,
                                                                              equipment=response.data["id"],
                                                                              is_deleted=False)
                    #print('emi_queryset',emi_queryset)
                    emi_dict = {}
                    for emi in emi_queryset:
                        emi_dict['id'] = emi.id
                        emi_dict['equipment'] = emi.equipment.id
                        emi_dict['equipment_owner_details'] = emi.equipment_owner_details.id
                        emi_dict['amount'] = emi.amount
                        emi_dict['start_date'] = emi.start_date
                        emi_dict['no_of_total_installment'] = emi.no_of_total_installment

                    if emi_dict:
                        owner_dict['owner_emi_details'] = emi_dict
                        print('owner_dict',owner_dict)
                    else:
                        owner_dict['owner_emi_details'] ={}

            if owner_dict:
                response.data['owner_details'] = owner_dict
            else:
                response.data['owner_details'] = {}
        elif response.data["owner_type"] == 3:
            contract_queryset = PmsMachinaryContractDetails.objects.filter(equipment=response.data["id"],
                                                                           is_deleted=False)
            contract_dict = {}
            for contract in contract_queryset:
                contract_dict['id'] = contract.id
                contract_dict['equipment'] = contract.equipment.id
                contract_dict['contractor'] = contract.contractor.id if contract.contractor else None
            if contract_dict:
                response.data['contract_details'] = contract_dict
            else:
                response.data['contract_details'] = {}
        else:
            lease_details=PmsMachinaryLeaseDetails.objects.filter(equipment=response.data["id"],
                                                                           is_deleted=False)
            lease_dict={}
            for l_d in lease_details:
                lease_dict['id']=l_d.id
                lease_dict['vendor']=l_d.vendor.id if l_d.vendor else None
                lease_dict['lease_amount']=l_d.lease_amount
                lease_dict['start_date']=l_d.start_date
                lease_dict['lease_period']=l_d.lease_period
            if lease_dict:
                response.data['lease_details'] = lease_dict
            else:
                response.data['lease_details'] = {}
        return response
class MachineriesListDetailsView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    pagination_class = CSPageNumberPagination
    queryset = PmsMachineries.objects.filter(is_deleted=False)
    serializer_class = MachineriesListDetailsSerializer

    def get_queryset(self):
        filter = dict()
        sort = '-id'
        project= self.request.query_params.get('project', None)
        owner_type=self.request.query_params.get('owner_type', None)
        search = self.request.query_params.get('search', None)
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)

        if search:
            filter['equipment_name__icontains'] = search

        if field_name and order_by:
            if field_name == 'equipment_name' and order_by == 'asc':
                sort = 'equipment_name'
            elif field_name == 'equipment_name' and order_by == 'desc':
                sort = '-equipment_name'
            elif field_name == 'equipment_category' and order_by == 'asc':
                sort = 'equipment_category__name'
            elif field_name == 'equipment_category' and order_by == 'desc':
                sort = '-equipment_category__name'
            elif field_name == 'equipment_make' and order_by == 'asc':
                sort = 'equipment_make'
            elif field_name == 'equipment_make' and order_by == 'desc':
                sort = '-equipment_make'
            elif field_name == 'equipment_model_no' and order_by == 'asc':
                sort = 'equipment_model_no'
            elif field_name == 'equipment_model_no' and order_by == 'desc':
                sort = '-equipment_model_no'

        if project:
            project = project.split(',')
            filter['pk__in'] = PmsProjectsMachinaryMapping.objects.filter(project__in=project,is_deleted=False).values_list('machinary',flat=True)
           
        if owner_type:
            filter['owner_type__in'] = owner_type
           
        return self.queryset.filter(**filter).order_by(sort)


class MachineriesListWPDetailsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsMachineries.objects.filter(is_deleted=False).order_by('-id')
    serializer_class = MachineriesListDetailsSerializer
    # filter_backends = (filters.SearchFilter,)
    # search_fields = ('equipment_name', 'equipment_model_no', 'equipment_registration_no')
class MachineriesListForReportView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsMachineries.objects.filter(is_deleted=False).order_by('-id')
    serializer_class = MachineriesListDetailsSerializer

    def get(self, request, *args, **kwargs):

        '''
            Added By Rupam Hazra [264 - 274] on 2020-27-01 
            for filter by project id and date
        '''
        #print('request',self.request.query_params.get())
        project = self.request.query_params.get('project_id', None)
        #print('project',project)
        input_date = self.request.query_params.get('date', None)
        input_date = datetime.strptime(input_date,"%Y-%m-%d").date()
        #print('input_date',input_date)
        #time.sleep(10)
        response=list()
        todays_date = datetime.now()
        machineries_filter_list = PmsProjectsMachinaryMapping.objects.\
            filter(
            machinary_s_d_req__lte=input_date,
            machinary_e_d_req__gte=input_date,
            project_id = int(project)
        )

        # response=list()
        # todays_date = datetime.now()
        # machineries_filter_list = PmsProjectsMachinaryMapping.objects.\
        #     filter(
        #     machinary_s_d_req__lte=todays_date.date(),
        #     machinary_e_d_req__gte=todays_date.date()
        # )
        #print('machineries_filter_list_query',machineries_filter_list.query)
        #print('machineries_filter_list', machineries_filter_list)
        mech_list=list()
        for e_machine in machineries_filter_list:
            mech_list.append(e_machine.machinary.id)
        #print('mech_list',mech_list)
        mechine_details_list = PmsMachineries.objects.\
            filter(is_deleted=False,pk__in=mech_list)
        #print('mechine_details_list',mechine_details_list)
        w_c_details={}
        for e_mechine_details in mechine_details_list:
             
            response_d = {
                'id': e_mechine_details.id,
                'equipment_name': e_mechine_details.equipment_name,
                'equipment_category': e_mechine_details.equipment_category.id if e_mechine_details.equipment_category else None,
                'equipment_type': e_mechine_details.equipment_type.name if e_mechine_details.equipment_type else None,
                'owner_type': e_mechine_details.owner_type,
                'equipment_make': e_mechine_details.equipment_make,
                'equipment_model_no': e_mechine_details.equipment_model_no,
                'equipment_registration_no': e_mechine_details.equipment_registration_no,
                'equipment_chassis_serial_no': e_mechine_details.equipment_chassis_serial_no,
                'equipment_engine_serial_no': e_mechine_details.equipment_engine_serial_no,
                'equipment_power': e_mechine_details.equipment_power,
                'measurement_by': e_mechine_details.measurement_by,
                'measurement_quantity': e_mechine_details.measurement_quantity,
                'fuel_consumption': e_mechine_details.fuel_consumption,
                'remarks': e_mechine_details.remarks,
                'reading_type':e_mechine_details.reading_type
            }
            if e_mechine_details.equipment_category:
                PmsMachineriesWorkingCategoryde = PmsMachineriesWorkingCategory.objects.\
                    filter(id=e_mechine_details.equipment_category.id,is_deleted=False)
                #print('PmsMachineriesWorkingCategoryde',PmsMachineriesWorkingCategoryde)
                for e_PmsMachineriesWorkingCategoryde in PmsMachineriesWorkingCategoryde:
                    w_c_details = { 'id':e_PmsMachineriesWorkingCategoryde.id,
                                    'name':e_PmsMachineriesWorkingCategoryde.name,
                                    'is_deleted': e_PmsMachineriesWorkingCategoryde.is_deleted,
                                    }
                #print('w_c_details',w_c_details)
                response_d['equipment_category_details'] = w_c_details
            else:
                response_d['equipment_category_details'] = dict()


            PmsMachineriesDoc = PmsMachineriesDetailsDocument.objects.filter(
                equipment=e_mechine_details.id,is_deleted=False)
            #print('PmsMachineriesDoc', PmsMachineriesDoc)
            m_d_details_list=[]
            #request = self.context.get('request')
            for e_PmsMachineriesDoc in PmsMachineriesDoc:
                m_d_details = { 'id':e_PmsMachineriesDoc.id,
                                'name':e_PmsMachineriesDoc.document_name,
                                'document': request.build_absolute_uri(e_PmsMachineriesDoc.document.url),
                                'is_deleted': e_PmsMachineriesDoc.is_deleted,
                                }
                m_d_details_list.append(m_d_details)
            #print('m_d_details_list',m_d_details_list)
            response_d['document_details'] = m_d_details_list
            if e_mechine_details.owner_type == 1:
                # print('xyz',gfsdsdf)
                machinary_rented_details_queryset = PmsMachinaryRentedDetails.objects.filter(equipment=e_mechine_details.id,
                                                                                             is_deleted=False)
                #print('machinary_rented_details_queryset',machinary_rented_details_queryset)
                rental_details = dict()
                for machinary_rent in machinary_rented_details_queryset:
                    rental_details['id'] = machinary_rent.id
                    rental_details['equipment'] = machinary_rent.equipment.id
                    rental_details['vendor'] = machinary_rent.vendor.id
                    rental_details['rent_amount'] = machinary_rent.rent_amount
                    rental_details['type_of_rent'] = machinary_rent.type_of_rent.id
                if rental_details:
                    response_d["rental_details"] = rental_details
                    m_rented_details_vendor = PmsExternalUsers.objects.filter(
                        pk=machinary_rent.vendor.id,is_deleted=False)
                    #print('m_rented_details_vendor',m_rented_details_vendor)
                    for e_m_rented_details_vendor in m_rented_details_vendor:
                        m_v_details = {'id': e_m_rented_details_vendor.id,
                                       'name': e_m_rented_details_vendor.contact_person_name,
                                       'is_deleted': e_m_rented_details_vendor.is_deleted,
                                       }
                    response_d["rental_details"]['vendor_details']= m_v_details
            elif e_mechine_details.owner_type == 2:
                owner_queryset = PmsMachinaryOwnerDetails.objects.filter(equipment=e_mechine_details.id,
                                                                         is_deleted=False)
                #print('owner_queryset',owner_queryset)
                owner_dict = {}
                for owner in owner_queryset:
                    owner_dict['id'] = owner.id
                    owner_dict['equipment'] = owner.equipment.id
                    owner_dict['purchase_date'] = owner.purchase_date
                    owner_dict['price'] = owner.price
                    owner_dict['is_emi_available'] = owner.is_emi_available
                    if owner.is_emi_available:
                        emi_queryset = PmsMachinaryOwnerEmiDetails.objects.filter(equipment_owner_details=owner,
                                                                                  equipment=e_mechine_details.id,
                                                                                  is_deleted=False)
                        #print('emi_queryset',emi_queryset)
                        emi_dict = {}
                        for emi in emi_queryset:
                            emi_dict['id'] = emi.id
                            emi_dict['equipment'] = emi.equipment.id
                            emi_dict['equipment_owner_details'] = emi.equipment_owner_details.id
                            emi_dict['amount'] = emi.amount
                            emi_dict['start_date'] = emi.start_date
                            emi_dict['no_of_total_installment'] = emi.no_of_total_installment

                        if emi_dict:
                            owner_dict['owner_emi_details'] = emi_dict
                            #print('owner_dict',owner_dict)
                if owner_dict:
                    response_d['owner_details'] = owner_dict
            else:
                contract_queryset = PmsMachinaryContractDetails.objects.filter(equipment=e_mechine_details.id,
                                                                               is_deleted=False)
                contract_dict = {}
                for contract in contract_queryset:
                    contract_dict['id'] = contract.id
                    contract_dict['equipment'] = contract.equipment.id
                    contract_dict['contractor_id'] = contract.contractor.id
                    contract_dict['contractor'] = contract.contractor.contact_person_name
                response_d['contract_details'] = contract_dict
            response.append(response_d)
            #print('response',response)
        return Response(response)
class MachineriesListFilterForReportView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    pagination_class = CSPageNumberPagination

    serializer_class = MachineriesListDetailsSerializer
    filter_backends = (DjangoFilterBackend,filters.OrderingFilter)
    filterset_fields = ('equipment_name','owner_type')
    ordering_fields = '__all__'
    def get_queryset(self):
        project = self.request.query_params.get('project', None)
        if project:
            PmsProjectsMachinaryMapping_d = PmsProjectsMachinaryMapping.objects.filter(is_deleted=False,project_id=int(project))
            print('PmsProjectsMachinaryMapping_d',PmsProjectsMachinaryMapping_d)
            mapping_ids = list()
            for e_PmsProjectsMachinaryMapping_d in PmsProjectsMachinaryMapping_d:
                mapping_ids.append(e_PmsProjectsMachinaryMapping_d.machinary.id)
            print('mapping_ids',mapping_ids)

            queryset = PmsMachineries.objects.filter(pk__in=mapping_ids,is_deleted=False).order_by('-id')
            print('queryset',queryset)

        else:
            queryset = PmsMachineries.objects.filter(is_deleted=False).order_by('-id')
        return queryset

    def list(self, request, *args, **kwargs):
        response = super(MachineriesListFilterForReportView, self).list(request, args, kwargs)
        for data in response.data['results']:
            PmsMachineriesWorkingCategoryde = PmsMachineriesWorkingCategory.objects.filter(
                id=data['equipment_category'],is_deleted=False)
            for e_PmsMachineriesWorkingCategoryde in PmsMachineriesWorkingCategoryde:
                w_c_details = { 'id':e_PmsMachineriesWorkingCategoryde.id,
                                'name':e_PmsMachineriesWorkingCategoryde.name,
                                'is_deleted': e_PmsMachineriesWorkingCategoryde.is_deleted,
                                }
            data['equipment_category_details'] = w_c_details
            PmsMachineriesDoc = PmsMachineriesDetailsDocument.objects.filter(
                equipment=data['id'],is_deleted=False)
            m_d_details_list=[]
            for e_PmsMachineriesDoc in PmsMachineriesDoc:
                m_d_details = { 'id':e_PmsMachineriesDoc.id,
                                'name':e_PmsMachineriesDoc.document_name,
                                'document': request.build_absolute_uri(e_PmsMachineriesDoc.document.url),
                                'is_deleted': e_PmsMachineriesDoc.is_deleted,
                                }
                m_d_details_list.append(m_d_details)
            data['document_details'] = m_d_details_list
            if data['owner_type'] == 1:
                machinary_rented_details_queryset = PmsMachinaryRentedDetails.objects.filter(
                    equipment=data['id'],is_deleted=False)
                #print('machinary_rented_details_queryset',machinary_rented_details_queryset)
                rental_details = dict()
                if machinary_rented_details_queryset:
                    for machinary_rent in machinary_rented_details_queryset:
                        equipment=machinary_rent.equipment.id if machinary_rent.equipment else None
                        vendor=machinary_rent.vendor.id if machinary_rent.vendor else None
                        type_of_rent=machinary_rent.type_of_rent.id if machinary_rent.type_of_rent else None
                        rental_details['id'] = machinary_rent.id
                        rental_details['equipment'] = equipment
                        rental_details['vendor'] = vendor
                        rental_details['rent_amount'] = machinary_rent.rent_amount
                        rental_details['type_of_rent'] = type_of_rent
                    if rental_details:
                        data["rental_details"] = rental_details
                        if machinary_rent.vendor:
                            m_rented_details_vendor = PmsExternalUsers.objects.filter(
                                pk=machinary_rent.vendor.id,is_deleted=False)
                            #print('m_rented_details_vendor',m_rented_details_vendor)
                            if m_rented_details_vendor:
                                for e_m_rented_details_vendor in m_rented_details_vendor:
                                    m_v_details = {'id': e_m_rented_details_vendor.id,
                                                'name': e_m_rented_details_vendor.contact_person_name,
                                                'is_deleted': e_m_rented_details_vendor.is_deleted,
                                                }
                                data["rental_details"]['vendor_details']= m_v_details
                            else:
                                data["rental_details"]['vendor_details']= None
                else:
                    data['rental_details']=None
            elif data['owner_type'] == 2:
                owner_queryset = PmsMachinaryOwnerDetails.objects.filter(
                    equipment=data['id'],is_deleted=False)
                #print('owner_queryset',owner_queryset)
                owner_dict = {}
                for owner in owner_queryset:
                    owner_dict['id'] = owner.id
                    owner_dict['equipment'] = owner.equipment.id
                    owner_dict['purchase_date'] = owner.purchase_date
                    owner_dict['price'] = owner.price
                    owner_dict['is_emi_available'] = owner.is_emi_available
                    if owner.is_emi_available:
                        emi_queryset = PmsMachinaryOwnerEmiDetails.objects.filter(
                            equipment_owner_details=owner,
                              equipment=data['id'],
                              is_deleted=False
                        )
                        #print('emi_queryset',emi_queryset)
                        emi_dict = {}
                        for emi in emi_queryset:
                            emi_dict['id'] = emi.id
                            emi_dict['equipment'] = emi.equipment.id
                            emi_dict['equipment_owner_details'] = emi.equipment_owner_details.id
                            emi_dict['amount'] = emi.amount
                            emi_dict['start_date'] = emi.start_date
                            emi_dict['no_of_total_installment'] = emi.no_of_total_installment

                        if emi_dict:
                            data['owner_emi_details'] = emi_dict
                            #print('owner_dict',owner_dict)
                if owner_dict:
                    data['owner_details'] = owner_dict
            else:
                contract_queryset = PmsMachinaryContractDetails.objects.filter(
                    equipment=data['id'],is_deleted=False)
                contract_dict = {}
                for contract in contract_queryset:
                    contract_dict['id'] = contract.id
                    contract_dict['equipment'] = contract.equipment.id
                    contract_dict['contractor_id'] = contract.contractor.id
                    contract_dict['contractor'] = contract.contractor.contact_person_name
                data['contract_details'] = contract_dict
        return response
class MachineriesDeleteView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsMachineries.objects.all()
    serializer_class = MachineriesDeleteSerializer

#::::::::::::::::: MECHINARY WORKING CATEGORY  :::::::::::::::#
class MachineriesWorkingCategoryAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsMachineriesWorkingCategory.objects.filter(is_deleted=False).order_by('-id')
    serializer_class= MachineriesWorkingCategoryAddSerializer
class MachineriesWorkingCategoryEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsMachineriesWorkingCategory.objects.all()
    serializer_class = MachineriesWorkingCategoryEditSerializer
class MachineriesWorkingCategoryDeleteView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsMachineriesWorkingCategory.objects.all()
    serializer_class = MachineriesWorkingCategoryDeleteSerializer

#::::::::::::::::: MECHINARY DETAILS DOCUMENT  :::::::::::::::#
class MachineriesDetailsDocumentAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsMachineriesDetailsDocument.objects.all()
    serializer_class = MachineriesDetailsDocumentAddSerializer
class MachineriesDetailsDocumentEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsMachineriesDetailsDocument.objects.all()
    serializer_class = MachineriesDetailsDocumentEditSerializer
class MachineriesDetailsDocumentDeleteView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsMachineriesDetailsDocument.objects.all()
    serializer_class = MachineriesDetailsDocumentDeleteSerializer
class MachineriesDetailsDocumentListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    serializer_class = MachineriesDetailsDocumentListSerializer
    def get_queryset(self):
        equipment_id = self.kwargs['equipment_id']
        queryset = PmsMachineriesDetailsDocument.objects.filter(equipment_id=equipment_id,is_deleted=False).order_by('-id')
        return queryset

#::::::::::::::: Pms Machinary Rented Type Master:::::::::::::::::::::#
class MachinaryRentedTypeMasterAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsMachinaryRentedTypeMaster.objects.filter(is_deleted=False).order_by('-id')
    serializer_class = MachinaryRentedTypeMasterAddSerializer
class MachinaryRentedTypeMasterEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsMachinaryRentedTypeMaster.objects.all()
    serializer_class = MachinaryRentedTypeMasterEditSerializer
class MachinaryRentedTypeMasterDeleteView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsMachinaryRentedTypeMaster.objects.all()
    serializer_class = MachinaryRentedTypeMasterDeleteSerializer

#:::::::::::: MECHINARY REPORTS ::::::::::::::::::::::::::::#
class MachineriesReportAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsProjectsMachinaryReport.objects.filter(is_deleted=False)
    serializer_class = MachineriesReportAddSerializer
    pagination_class = CSPageNumberPagination

    # @response_modify_decorator_get_after_execution
    def get(self ,request, *args, **kwargs):
        return super(MachineriesReportAddView, self).list(request, *args, **kwargs)
    
    def get_queryset(self):
        project=self.request.query_params.get('project', None)
        field_name = self.request.query_params.get('field_name', None)
        
        order_by = self.request.query_params.get('order_by', None)

        search = self.request.query_params.get('search', None)

        queryset = PmsProjectsMachinaryReport.objects.filter(is_deleted=False)

        if project:
            machinary=PmsProjectsMachinaryMapping.objects.filter(project=project)
            machinary_report = PmsProjectsMachinaryReport.objects.none()
            for e_machinary in machinary:
                machinary_report = machinary_report | PmsProjectsMachinaryReport.objects.filter(machine=e_machinary.machinary.id)
            
            queryset = machinary_report

        if queryset and search:
            queryset = queryset.filter(machine__equipment_name__icontains=search)

        if queryset and field_name and order_by:
            if field_name=='machine_name' and order_by == 'asc':
                queryset = queryset.order_by('machine__equipment_name')
            elif field_name=='machine_name' and order_by == 'desc':
                queryset = queryset.order_by('-machine__equipment_name')
            elif field_name=='date' and order_by == 'asc':
                queryset = queryset.order_by('date')
            elif field_name=='date' and order_by == 'desc':
                queryset = queryset.order_by('-date')
            elif field_name=='opening_balance' and order_by == 'asc':
                queryset = queryset.order_by('opening_balance')
            elif field_name=='opening_balance' and order_by == 'desc':
                queryset = queryset.order_by('-opening_balance')
            elif field_name=='cash_purchase' and order_by == 'asc':
                queryset = queryset.order_by('cash_purchase')
            elif field_name=='cash_purchase' and order_by == 'desc':
                queryset = queryset.order_by('-cash_purchase')
            elif field_name=='total_diesel_available' and order_by == 'asc':
                queryset = queryset.order_by('total_diesel_available')
            elif field_name=='total_diesel_available' and order_by == 'desc':
                queryset = queryset.order_by('-total_diesel_available')
            elif field_name=='opening_meter_reading' and order_by == 'asc':
                queryset = queryset.order_by('opening_meter_reading')
            elif field_name=='opening_meter_reading' and order_by == 'desc':
                queryset = queryset.order_by('-opening_meter_reading')
            elif field_name=='closing_meter_reading' and order_by == 'asc':
                queryset = queryset.order_by('closing_meter_reading')
            elif field_name=='closing_meter_reading' and order_by == 'desc':
                queryset = queryset.order_by('-closing_meter_reading')
            elif field_name=='diesel_balance' and order_by == 'asc':
                queryset = queryset.order_by('diesel_balance')
            elif field_name=='diesel_balance' and order_by == 'desc':
                queryset = queryset.order_by('-diesel_balance')

        return queryset

class MachineriesReportEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsProjectsMachinaryReport.objects.all()
    serializer_class = MachineriesReportEditSerializer

## Change Request PMS Daily [Modifications Required in PMS System] | Date : 25-06-2020 | Rupam Hazra ##

class MachineriesByProjectView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsMachineries.objects.filter(is_deleted=False).order_by('-id')
    serializer_class = MachineriesListDetailsSerializer

    def get_queryset(self):
        site_id = self.kwargs["site_id"]
        filter = {
        'pk__in':PmsProjectsMachinaryMapping.objects.filter(
            project_id__in=(PmsProjects.objects.filter(site_location_id=site_id).values_list('id',flat=True))).values_list('machinary',flat=True)
        }
        queryset = self.queryset.filter(**filter)
        return queryset

    @response_modify_decorator_list
    def list(self ,request, *args, **kwargs):
        return super(MachineriesByProjectView, self).list(request, *args, **kwargs)

## Change Request PMS Daily [Modifications Required in PMS System] | Date : 25-06-2020 | Rupam Hazra ##


## Start Functional Specification Document - PMS_V4.0 | Date : 22-07-2020 | Rupam Hazra ##

class MachineriesReportAddV2View(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsProjectsMachinaryReport.objects.filter(is_deleted=False)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return MachineriesReportAddV2Serializer
        
        return MachineriesReportDetailsV2Serializer
        
    def get_queryset(self):

        filter = dict()

        site_location=self.request.query_params.get('site_location', None)
        project = self.request.query_params.get('project', None)
        date=self.request.query_params.get('date', None)

        if project:
            filter['project'] = project

        if site_location:
            filter['site_location'] = site_location

        if date:
            filter['date__date'] = date

        queryset = self.queryset.filter(**filter)
        print('queryset',queryset.query)
        return queryset

    @response_modify_decorator_get_single
    def get(self ,request, *args, **kwargs):
        return super(MachineriesReportAddV2View, self).get(request, *args, **kwargs)


    @response_modify_decorator_post
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class MachineriesReportEditV2View(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsProjectsMachinaryReport.objects.all()
    serializer_class = MachineriesReportEditV2Serializer

    @response_modify_decorator_update
    def put(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

class MachineryDieselConsumptionReportView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    pagination_class = OnOffPagination
    queryset = PmsMachinaryDieselConsumptionData.objects.filter(is_deleted=False)
    serializer_class = MachineryDieselConsumptionReportSerializer

    def get_queryset(self):
        filter = dict()
        sort = '-id'
        
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        site_location=self.request.query_params.get('site_location', None)
        project = self.request.query_params.get('project', None)
        start_date=self.request.query_params.get('start_date', None)
        end_date=self.request.query_params.get('end_date', None)

        if project:
            filter['machinary_report__project'] = project

        if site_location:
            filter['machinary_report__site_location'] = site_location

        if start_date and end_date:
            filter['created_at__date__gte'] = start_date
            filter['created_at__date__lte'] = end_date
           
        return self.queryset.filter(**filter).order_by(sort)

    @response_modify_decorator_list_or_get_before_execution_for_onoff_pagination
    def list(self ,request, *args, **kwargs):
        return response

class MachineriesDailyReportView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsMachinaryDieselConsumptionData.objects.filter(is_deleted=False)
    serializer_class = MachineriesDailyReportSerializer

    def get_queryset(self):
        filter = dict()
        sort = '-id'
        project = self.request.query_params.get('project', None)
        date=self.request.query_params.get('date', None)
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)

        if project:
            filter['machinary_report__project'] = project

        if date:
            filter['machinary_report__date__date'] = date

        if field_name and order_by:

            if field_name=='equipment_name' and order_by == 'asc':
                sort = 'machine__equipment_name'
            if field_name=='equipment_name' and order_by == 'desc':
                sort = '-machine__equipment_name'

            if field_name=='diesel_consumption_by_equipment' and order_by == 'asc':
                sort = 'diesel_consumption_by_equipment'
            if field_name=='diesel_consumption_by_equipment' and order_by == 'desc':
                sort = '-diesel_consumption_by_equipment'

            if field_name=='opening_meter_reading' and order_by == 'asc':
                sort = 'opening_meter_reading'
            if field_name=='opening_meter_reading' and order_by == 'desc':
                sort = '-opening_meter_reading'

            if field_name=='closing_meter_reading' and order_by == 'asc':
                sort = 'closing_meter_reading'
            if field_name=='closing_meter_reading' and order_by == 'desc':
                sort = '-closing_meter_reading'

            if field_name=='difference_kms' and order_by == 'asc':
                sort = 'difference_kms'
            if field_name=='difference_kms' and order_by == 'desc':
                sort = '-difference_kms'

            if field_name=='running_km_hr' and order_by == 'asc':
                sort = 'machine__running_km_hr'
            if field_name=='running_km_hr' and order_by == 'desc':
                sort = '-machine__running_km_hr'

            if field_name=='standard_fuel_consumption' and order_by == 'asc':
                sort = 'machine__standard_fuel_consumption'
            if field_name=='standard_fuel_consumption' and order_by == 'desc':
                sort = '-machine__standard_fuel_consumption'

            if field_name=='last_em_maintenance_date' and order_by == 'asc':
                sort = 'last_em_maintenance_date'
            if field_name=='last_em_maintenance_date' and order_by == 'desc':
                sort = '-last_em_maintenance_date'

            if field_name=='next_em_maintenance_schedule' and order_by == 'asc':
                sort = 'next_em_maintenance_schedule'
            if field_name=='next_em_maintenance_schedule' and order_by == 'desc':
                sort = '-next_em_maintenance_schedule'

        return self.queryset.filter(**filter).order_by(sort)

    def get(self ,request, *args, **kwargs):
        response = super(MachineriesDailyReportView, self).get(request, args, kwargs)
        #print('response',response.data)
        data_dict = dict()
        filter = dict()
        project = self.request.query_params.get('project', None)
        date=self.request.query_params.get('date', None)

        import operator

        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)

        if field_name=='hsd_average' and order_by == 'desc':
            response.data = sorted(response.data, key=operator.itemgetter('hsd_average'))
       


        if project:
            filter['project'] = project
        if date:
            filter['date__date'] = date

        pmsProjectsMachinaryReport = PmsProjectsMachinaryReport.objects.filter(**filter).values(
            'id','project','date','opening_balance','cash_purchase','diesel_transfer_from_other_site',
            'other_consumption','miscellaneous_consumption','vendor','vendor__contact_person_name','received_qty')

        if pmsProjectsMachinaryReport:
            data_dict = pmsProjectsMachinaryReport[0]
            received_qty = data_dict['received_qty']
            cash_purchase = float(data_dict['cash_purchase']) if data_dict['cash_purchase'] else float(0)
            opening_balance = float(data_dict['opening_balance']) if data_dict['opening_balance'] else float(0)
            diesel_transfer_from_other_site = float(data_dict['diesel_transfer_from_other_site']) if data_dict['diesel_transfer_from_other_site'] else float(0)

            data_dict['total_diesel_available'] = float(opening_balance + cash_purchase + diesel_transfer_from_other_site)
            data_dict['total_diesel_consumption_by_equipment'] = PmsMachinaryDieselConsumptionData.objects.filter(
                machinary_report=pmsProjectsMachinaryReport[0]['id']).aggregate(Sum('diesel_consumption_by_equipment'))['diesel_consumption_by_equipment__sum']
            
            total_diesel_consumption_by_equipment = data_dict['total_diesel_consumption_by_equipment'] if data_dict['total_diesel_consumption_by_equipment'] else float(0)
            other_consumption = float(data_dict['other_consumption']) if data_dict['other_consumption'] else float(0)
            miscellaneous_consumption = float(data_dict['miscellaneous_consumption']) if data_dict['miscellaneous_consumption'] else float(0)
            data_dict['total_diesel_consumed'] = float(total_diesel_consumption_by_equipment) + other_consumption + miscellaneous_consumption
            data_dict['diesel_balance'] = data_dict['total_diesel_available'] - data_dict['total_diesel_consumed']

        data_dict['daily_data'] = response.data
        return Response({'results':data_dict,'status':'success','msg':'data found'})    

class MachineriesDailyReportDownloadView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsMachinaryDieselConsumptionData.objects.filter(is_deleted=False)
    serializer_class = MachineriesDailyReportSerializer

    def get_queryset(self):
        filter = dict()
        sort = '-id'
        project = self.request.query_params.get('project', None)
        date=self.request.query_params.get('date', None)
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)

        if project:
            filter['machinary_report__project'] = project

        if date:
            filter['machinary_report__date__date'] = date

        if field_name and order_by:

            if field_name=='equipment_name' and order_by == 'asc':
                sort = 'machine__equipment_name'
            if field_name=='equipment_name' and order_by == 'desc':
                sort = '-machine__equipment_name'

            if field_name=='diesel_consumption_by_equipment' and order_by == 'asc':
                sort = 'diesel_consumption_by_equipment'
            if field_name=='diesel_consumption_by_equipment' and order_by == 'desc':
                sort = '-diesel_consumption_by_equipment'

            if field_name=='opening_meter_reading' and order_by == 'asc':
                sort = 'opening_meter_reading'
            if field_name=='opening_meter_reading' and order_by == 'desc':
                sort = '-opening_meter_reading'

            if field_name=='closing_meter_reading' and order_by == 'asc':
                sort = 'closing_meter_reading'
            if field_name=='closing_meter_reading' and order_by == 'desc':
                sort = '-closing_meter_reading'

            if field_name=='difference_kms' and order_by == 'asc':
                sort = 'difference_kms'
            if field_name=='difference_kms' and order_by == 'desc':
                sort = '-difference_kms'

            if field_name=='running_km_hr' and order_by == 'asc':
                sort = 'machine__running_km_hr'
            if field_name=='running_km_hr' and order_by == 'desc':
                sort = '-machine__running_km_hr'

            if field_name=='standard_fuel_consumption' and order_by == 'asc':
                sort = 'machine__standard_fuel_consumption'
            if field_name=='standard_fuel_consumption' and order_by == 'desc':
                sort = '-machine__standard_fuel_consumption'

            if field_name=='last_em_maintenance_date' and order_by == 'asc':
                sort = 'last_em_maintenance_date'
            if field_name=='last_em_maintenance_date' and order_by == 'desc':
                sort = '-last_em_maintenance_date'

            if field_name=='next_em_maintenance_schedule' and order_by == 'asc':
                sort = 'next_em_maintenance_schedule'
            if field_name=='next_em_maintenance_schedule' and order_by == 'desc':
                sort = '-next_em_maintenance_schedule'

        return self.queryset.filter(**filter).order_by(sort)

    def get(self ,request, *args, **kwargs):
        response = super(MachineriesDailyReportDownloadView, self).get(request, args, kwargs)
        #print('response',response.data)
        data_dict = dict()
        filter = dict()
        project = self.request.query_params.get('project', None)
        date=self.request.query_params.get('date', None)
        daily_data = list()
        import operator

        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)

        if field_name=='hsd_average' and order_by == 'desc':
            response.data = sorted(response.data, key=operator.itemgetter('hsd_average'))
       


        if project:
            filter['project'] = project
        if date:
            filter['date__date'] = date

        pmsProjectsMachinaryReport = PmsProjectsMachinaryReport.objects.filter(**filter).values(
            'id','project','date','opening_balance','cash_purchase','diesel_transfer_from_other_site',
            'other_consumption','miscellaneous_consumption','vendor','vendor__contact_person_name')

        if pmsProjectsMachinaryReport:
            data_dict = pmsProjectsMachinaryReport[0]

            cash_purchase = float(data_dict['cash_purchase']) if data_dict['cash_purchase'] else float(0)
            opening_balance = float(data_dict['opening_balance']) if data_dict['opening_balance'] else float(0)
            diesel_transfer_from_other_site = float(data_dict['diesel_transfer_from_other_site']) if data_dict['diesel_transfer_from_other_site'] else float(0)

            data_dict['total_diesel_available'] = float(opening_balance + cash_purchase + diesel_transfer_from_other_site)
            data_dict['total_diesel_consumption_by_equipment'] = PmsMachinaryDieselConsumptionData.objects.filter(
                machinary_report=pmsProjectsMachinaryReport[0]['id']).aggregate(Sum('diesel_consumption_by_equipment'))['diesel_consumption_by_equipment__sum']
            total_diesel_consumption_by_equipment = data_dict['total_diesel_consumption_by_equipment'] if data_dict['total_diesel_consumption_by_equipment'] else float(0)
            other_consumption = float(data_dict['other_consumption']) if data_dict['other_consumption'] else float(0)
            miscellaneous_consumption = float(data_dict['miscellaneous_consumption']) if data_dict['miscellaneous_consumption'] else float(0)
            data_dict['total_diesel_consumed'] = float(total_diesel_consumption_by_equipment) + other_consumption + miscellaneous_consumption
            data_dict['diesel_balance'] = data_dict['total_diesel_available'] - data_dict['total_diesel_consumed']

            #daily_data.append(['Opening Balance :'+ str(opening_balance)])
        count = 0
        for e_data in response.data:
            count +=1
            contractor = e_data['machine_details']['contractor_o_vendor_details']['contract_details']['contractor'] if e_data['machine_details']['contractor_o_vendor_details']['contract_details'] else ''
            daily_data.append(
                [
                    count,
                    e_data['machine_details']['equipment_name'],
                    e_data['diesel_consumption_by_equipment'],
                    e_data['opening_meter_reading'],
                    e_data['closing_meter_reading'],
                    e_data['difference_kms'],
                    e_data['opening_hours_reading'],
                    e_data['closing_hours_reading'],
                    e_data['difference_hrs'],
                    e_data['machine_details']['running_km_hr'],
                    e_data['hsd_average'],
                    e_data['machine_details']['standard_fuel_consumption'],
                    contractor,
                    e_data['last_em_maintenance_date'][0:10],
                    e_data['next_em_maintenance_schedule'][0:10],
                ]
                )

        file_name = ''
        if daily_data:
            if os.path.isdir('media/pms/machineries/document/'):
                file_name = 'media/pms/machineries/document/pms_machinery_daily_report.xlsx'
                file_path = settings.MEDIA_ROOT_EXPORT + file_name
            else:
                os.makedirs('media/pms/machineries/document/')
                file_name = 'media/pms/machineries/document/pms_daily_report.xlsx'
                file_path = settings.MEDIA_ROOT_EXPORT + file_name

            
            final_df = pd.DataFrame(daily_data,columns=['SL No.','Equipment','Diesel Consumption By Equipment',
                'Opening Meter Reading','Closing Meter Reading','Difference in Reading(Kms)',
                'Opening Hours Reading','Closing Hours Reading','Difference in Reading(Hrs)',
                'Running(Kms/Hrs)','HSD Average','Standard Fuel Consumption','Contractor Name','Last EM Date','Next EM schedule'])

                
            writer = pd.ExcelWriter(file_path, engine='xlsxwriter') 
            final_df.to_excel(writer, startrow=5, startcol=0,index = None, header=True)
            workbook  = writer.book
            worksheet = writer.sheets['Sheet1']
            bold = workbook.add_format({'bold': True})

            worksheet.merge_range('A2:A4', "Date : "+str(date),bold)

            worksheet.write('B2', 'Opening Balance : ',bold)
            worksheet.write('C2', str(opening_balance),bold)
            worksheet.write('D2', 'Cash Purchase : ',bold)
            worksheet.write('E2', str(cash_purchase),bold)
            worksheet.write('F2', 'Vendor : ',bold)
            worksheet.write('G2', str(data_dict['vendor__contact_person_name'] if data_dict['vendor__contact_person_name'] else ''),bold)
            worksheet.write('H2', 'Diesel Transfer From Other Site : ',bold)
            worksheet.write('I2', str(diesel_transfer_from_other_site),bold)
            worksheet.write('J2', 'Total Diesel Available : ',bold)
            worksheet.write('K2', str(data_dict['total_diesel_available']),bold)

            worksheet.write('B4', 'Total Diesel Consumption By Equipment : ',bold)
            worksheet.write('C4', str(data_dict['total_diesel_consumption_by_equipment']),bold)
            worksheet.write('D4', 'Other Consumption : ',bold)
            worksheet.write('E4', str(other_consumption),bold)
            worksheet.write('F4', 'Misc. Consumption : ',bold)
            worksheet.write('G4', str(miscellaneous_consumption),bold)
            worksheet.write('H4', 'Total Diesel Consumed : ',bold)
            worksheet.write('I4', str(data_dict['total_diesel_consumed']),bold)
            worksheet.write('J4', 'Diesel Balance : ',bold)
            worksheet.write('K4', str(data_dict['diesel_balance']),bold)
            writer.save()

           

        url = getHostWithPort(request) + file_name if file_name else None
        data_dict['url'] = url
        return Response({'results':data_dict,'status':'success','msg':'data found'})  

class MachineriesMonthlyReportView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsMachinaryDieselConsumptionData.objects.filter(is_deleted=False)
    serializer_class = MachineriesDailyReportSerializer
    pagination_class = OnOffPagination

    def get_queryset(self):
        filter = dict()
        sort = '-id'
        project = self.request.query_params.get('project', None)
        from_date=self.request.query_params.get('from_date', None)
        to_date = self.request.query_params.get('to_date', None)
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)

        if project:
            filter['machinary_report__project'] = project

        if from_date and to_date:
            filter['machinary_report__date__date__gte'] = from_date
            filter['machinary_report__date__date__lte'] = to_date

        if field_name and order_by:

            if field_name=='equipment_name' and order_by == 'asc':
                sort = 'machine__equipment_name'
            if field_name=='equipment_name' and order_by == 'desc':
                sort = '-machine__equipment_name'

            if field_name=='diesel_consumption_by_equipment' and order_by == 'asc':
                sort = 'diesel_consumption_by_equipment'
            if field_name=='diesel_consumption_by_equipment' and order_by == 'desc':
                sort = '-diesel_consumption_by_equipment'

            if field_name=='opening_meter_reading' and order_by == 'asc':
                sort = 'opening_meter_reading'
            if field_name=='opening_meter_reading' and order_by == 'desc':
                sort = '-opening_meter_reading'

            if field_name=='closing_meter_reading' and order_by == 'asc':
                sort = 'closing_meter_reading'
            if field_name=='closing_meter_reading' and order_by == 'desc':
                sort = '-closing_meter_reading'

            if field_name=='difference_kms' and order_by == 'asc':
                sort = 'difference_kms'
            if field_name=='difference_kms' and order_by == 'desc':
                sort = '-difference_kms'

            if field_name=='running_km_hr' and order_by == 'asc':
                sort = 'machine__running_km_hr'
            if field_name=='running_km_hr' and order_by == 'desc':
                sort = '-machine__running_km_hr'

            if field_name=='standard_fuel_consumption' and order_by == 'asc':
                sort = 'machine__standard_fuel_consumption'
            if field_name=='standard_fuel_consumption' and order_by == 'desc':
                sort = '-machine__standard_fuel_consumption'

            if field_name=='last_em_maintenance_date' and order_by == 'asc':
                sort = 'last_em_maintenance_date'
            if field_name=='last_em_maintenance_date' and order_by == 'desc':
                sort = '-last_em_maintenance_date'

            if field_name=='next_em_maintenance_schedule' and order_by == 'asc':
                sort = 'next_em_maintenance_schedule'
            if field_name=='next_em_maintenance_schedule' and order_by == 'desc':
                sort = '-next_em_maintenance_schedule'

        return self.queryset.filter(**filter).order_by(sort)

    @response_modify_decorator_list_or_get_before_execution_for_onoff_pagination
    def get(self ,request, *args, **kwargs):
        response = super(MachineriesMonthlyReportView, self).get(request, args, kwargs)
        return response
    
class MachineriesMonthlyReportDetailsCalculationView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsMachinaryDieselConsumptionData.objects.filter(is_deleted=False).order_by('machinary_report__date')
    serializer_class = MachineriesDailyReportSerializer

    def get_queryset(self):
        filter = dict()
        sort = '-id'
        project = self.request.query_params.get('project', None)
        from_date=self.request.query_params.get('from_date', None)
        to_date = self.request.query_params.get('to_date', None)
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)

        if project:
            filter['machinary_report__project'] = project

        if from_date and to_date:
            filter['machinary_report__date__date__gte'] = from_date
            filter['machinary_report__date__date__lte'] = to_date

        if field_name and order_by:

            if field_name=='equipment_name' and order_by == 'asc':
                sort = 'machine__equipment_name'
            if field_name=='equipment_name' and order_by == 'desc':
                sort = '-machine__equipment_name'

            if field_name=='diesel_consumption_by_equipment' and order_by == 'asc':
                sort = 'diesel_consumption_by_equipment'
            if field_name=='diesel_consumption_by_equipment' and order_by == 'desc':
                sort = '-diesel_consumption_by_equipment'

            if field_name=='opening_meter_reading' and order_by == 'asc':
                sort = 'opening_meter_reading'
            if field_name=='opening_meter_reading' and order_by == 'desc':
                sort = '-opening_meter_reading'

            if field_name=='closing_meter_reading' and order_by == 'asc':
                sort = 'closing_meter_reading'
            if field_name=='closing_meter_reading' and order_by == 'desc':
                sort = '-closing_meter_reading'

            if field_name=='difference_kms' and order_by == 'asc':
                sort = 'difference_kms'
            if field_name=='difference_kms' and order_by == 'desc':
                sort = '-difference_kms'

            if field_name=='running_km_hr' and order_by == 'asc':
                sort = 'machine__running_km_hr'
            if field_name=='running_km_hr' and order_by == 'desc':
                sort = '-machine__running_km_hr'

            if field_name=='standard_fuel_consumption' and order_by == 'asc':
                sort = 'machine__standard_fuel_consumption'
            if field_name=='standard_fuel_consumption' and order_by == 'desc':
                sort = '-machine__standard_fuel_consumption'

            if field_name=='last_em_maintenance_date' and order_by == 'asc':
                sort = 'last_em_maintenance_date'
            if field_name=='last_em_maintenance_date' and order_by == 'desc':
                sort = '-last_em_maintenance_date'

            if field_name=='next_em_maintenance_schedule' and order_by == 'asc':
                sort = 'next_em_maintenance_schedule'
            if field_name=='next_em_maintenance_schedule' and order_by == 'desc':
                sort = '-next_em_maintenance_schedule'

        return self.queryset.filter(**filter).order_by(sort)

    def get(self ,request, *args, **kwargs):
        response = super(MachineriesMonthlyReportDetailsCalculationView, self).get(request, args, kwargs)
        #print('response',response.data)
        data_dict = dict()
        filter = dict()
        project = self.request.query_params.get('project', None)
        from_date=self.request.query_params.get('from_date', None)
        to_date = self.request.query_params.get('to_date', None)

        import operator

        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)

        if field_name=='hsd_average' and order_by == 'desc':
            response.data = sorted(response.data, key=operator.itemgetter('hsd_average'))

        if project:
            filter['project'] = project

        if from_date and to_date:
            filter['date__date__gte'] = from_date
            filter['date__date__lte'] = to_date
            #filter['date__date'] = from_date

        pmsProjectsMachinaryReport_ids = PmsProjectsMachinaryReport.objects.filter(**filter).values_list('id',flat=True)


        opening_balance = PmsProjectsMachinaryReport.objects.filter(project=project,date__date=from_date).values_list('opening_balance',flat=True).first()
        data_dict['opening_balance'] = opening_balance if opening_balance else float(0)

        received_qty = PmsProjectsMachinaryReport.objects.filter(**filter).aggregate(Sum('received_qty'))['received_qty__sum']
        data_dict['received_qty'] = received_qty if received_qty else float(0)

        cash_purchase = PmsProjectsMachinaryReport.objects.filter(**filter).aggregate(Sum('cash_purchase'))['cash_purchase__sum']
        data_dict['cash_purchase'] = cash_purchase if cash_purchase else float(0)

        other_consumption = PmsProjectsMachinaryReport.objects.filter(**filter).aggregate(Sum('other_consumption'))['other_consumption__sum']
        data_dict['other_consumption'] = float(other_consumption) if other_consumption else float(0)
        
        miscellaneous_consumption = PmsProjectsMachinaryReport.objects.filter(**filter).aggregate(Sum('miscellaneous_consumption'))['miscellaneous_consumption__sum']
        data_dict['miscellaneous_consumption'] = float(miscellaneous_consumption) if miscellaneous_consumption else float(0)

        diesel_transfer_from_other_site = PmsProjectsMachinaryReport.objects.filter(**filter).aggregate(
            Sum('diesel_transfer_from_other_site'))['diesel_transfer_from_other_site__sum']

        diesel_transfer_from_other_site = float(diesel_transfer_from_other_site) if diesel_transfer_from_other_site else float(0)

        data_dict['total_diesel_available'] = float(data_dict['opening_balance']) + float(data_dict['cash_purchase']) + diesel_transfer_from_other_site + float(data_dict['received_qty'])

        data_dict['total_diesel_consumption_by_equipment'] = PmsMachinaryDieselConsumptionData.objects.filter(
            machinary_report__in=pmsProjectsMachinaryReport_ids).aggregate(Sum('diesel_consumption_by_equipment'))['diesel_consumption_by_equipment__sum']

        data_dict['total_diesel_consumption_by_equipment'] = data_dict['total_diesel_consumption_by_equipment'] if data_dict['total_diesel_consumption_by_equipment'] else float(0)
        data_dict['total_diesel_consumed'] = float(data_dict['total_diesel_consumption_by_equipment']) + data_dict['other_consumption'] + data_dict['miscellaneous_consumption']

        data_dict['diesel_balance'] = data_dict['total_diesel_available'] - data_dict['total_diesel_consumed']

        
        return Response({'results':data_dict,'status':'success','msg':'data found'})

class MachineriesMonthlyReportExportDownloadView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsMachinaryDieselConsumptionData.objects.filter(is_deleted=False)
    serializer_class = MachineriesDailyReportSerializer

    def get_queryset(self):
        filter = dict()
        sort = '-id'
        project = self.request.query_params.get('project', None)
        from_date=self.request.query_params.get('from_date', None)
        to_date = self.request.query_params.get('to_date', None)
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)

        if project:
            filter['machinary_report__project'] = project

        if from_date and to_date:
            filter['machinary_report__date__date__gte'] = from_date
            filter['machinary_report__date__date__lte'] = to_date

        if field_name and order_by:

            if field_name=='equipment_name' and order_by == 'asc':
                sort = 'machine__equipment_name'
            if field_name=='equipment_name' and order_by == 'desc':
                sort = '-machine__equipment_name'

            if field_name=='diesel_consumption_by_equipment' and order_by == 'asc':
                sort = 'diesel_consumption_by_equipment'
            if field_name=='diesel_consumption_by_equipment' and order_by == 'desc':
                sort = '-diesel_consumption_by_equipment'

            if field_name=='opening_meter_reading' and order_by == 'asc':
                sort = 'opening_meter_reading'
            if field_name=='opening_meter_reading' and order_by == 'desc':
                sort = '-opening_meter_reading'

            if field_name=='closing_meter_reading' and order_by == 'asc':
                sort = 'closing_meter_reading'
            if field_name=='closing_meter_reading' and order_by == 'desc':
                sort = '-closing_meter_reading'

            if field_name=='difference_kms' and order_by == 'asc':
                sort = 'difference_kms'
            if field_name=='difference_kms' and order_by == 'desc':
                sort = '-difference_kms'

            if field_name=='running_km_hr' and order_by == 'asc':
                sort = 'machine__running_km_hr'
            if field_name=='running_km_hr' and order_by == 'desc':
                sort = '-machine__running_km_hr'

            if field_name=='standard_fuel_consumption' and order_by == 'asc':
                sort = 'machine__standard_fuel_consumption'
            if field_name=='standard_fuel_consumption' and order_by == 'desc':
                sort = '-machine__standard_fuel_consumption'

            if field_name=='last_em_maintenance_date' and order_by == 'asc':
                sort = 'last_em_maintenance_date'
            if field_name=='last_em_maintenance_date' and order_by == 'desc':
                sort = '-last_em_maintenance_date'

            if field_name=='next_em_maintenance_schedule' and order_by == 'asc':
                sort = 'next_em_maintenance_schedule'
            if field_name=='next_em_maintenance_schedule' and order_by == 'desc':
                sort = '-next_em_maintenance_schedule'

        return self.queryset.filter(**filter).order_by(sort)

    def get(self ,request, *args, **kwargs):
        response = super(MachineriesMonthlyReportExportDownloadView, self).get(request, args, kwargs)
        print('response',len(response.data))
        data_dict = dict()
        filter = dict()
        project = self.request.query_params.get('project', None)
        from_date=self.request.query_params.get('from_date', None)
        to_date = self.request.query_params.get('to_date', None)

        import operator

        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)

        if field_name=='hsd_average' and order_by == 'desc':
            response.data = sorted(response.data, key=operator.itemgetter('hsd_average'))

        if project:
            filter['project'] = project
        if from_date and to_date:
            filter['date__date__gte'] = from_date
            filter['date__date__lte'] = to_date


        pmsProjectsMachinaryReport_ids = PmsProjectsMachinaryReport.objects.filter(**filter).values_list('id',flat=True)
        #print('pmsProjectsMachinaryReport_ids',len(pmsProjectsMachinaryReport_ids))

        opening_balance = PmsProjectsMachinaryReport.objects.filter(project=project,date__date=from_date).values_list('opening_balance',flat=True).first()
        data_dict['opening_balance'] = opening_balance if opening_balance else float(0)

        received_qty = PmsProjectsMachinaryReport.objects.filter(**filter).aggregate(Sum('received_qty'))['received_qty__sum']
        data_dict['received_qty'] = received_qty if received_qty else float(0)

        cash_purchase = PmsProjectsMachinaryReport.objects.filter(**filter).aggregate(Sum('cash_purchase'))['cash_purchase__sum']
        data_dict['cash_purchase'] = cash_purchase if cash_purchase else float(0)

        other_consumption = PmsProjectsMachinaryReport.objects.filter(**filter).aggregate(Sum('other_consumption'))['other_consumption__sum']
        data_dict['other_consumption'] = float(other_consumption) if other_consumption else float(0)
        
        miscellaneous_consumption = PmsProjectsMachinaryReport.objects.filter(**filter).aggregate(Sum('miscellaneous_consumption'))['miscellaneous_consumption__sum']
        data_dict['miscellaneous_consumption'] = float(miscellaneous_consumption) if miscellaneous_consumption else float(0)

        diesel_transfer_from_other_site = PmsProjectsMachinaryReport.objects.filter(**filter).aggregate(
            Sum('diesel_transfer_from_other_site'))['diesel_transfer_from_other_site__sum']

        diesel_transfer_from_other_site = float(diesel_transfer_from_other_site) if diesel_transfer_from_other_site else float(0)

        data_dict['total_diesel_available'] = float(data_dict['opening_balance']) + float(data_dict['cash_purchase']) + diesel_transfer_from_other_site + float(data_dict['received_qty'])

        data_dict['total_diesel_consumption_by_equipment'] = PmsMachinaryDieselConsumptionData.objects.filter(
            machinary_report__in=pmsProjectsMachinaryReport_ids).aggregate(Sum('diesel_consumption_by_equipment'))['diesel_consumption_by_equipment__sum']

        data_dict['total_diesel_consumption_by_equipment'] = data_dict['total_diesel_consumption_by_equipment'] if data_dict['total_diesel_consumption_by_equipment'] else float(0)
        data_dict['total_diesel_consumed'] = float(data_dict['total_diesel_consumption_by_equipment']) + data_dict['other_consumption'] + data_dict['miscellaneous_consumption']

        data_dict['diesel_balance'] = data_dict['total_diesel_available'] - data_dict['total_diesel_consumed']

        daily_data = list()
        #data_dict['daily_data'] = response.data
        count = 0
        for e_data in response.data:
            count +=1
            contractor = e_data['machine_details']['contractor_o_vendor_details']['contract_details']['contractor'] if e_data['machine_details']['contractor_o_vendor_details']['contract_details'] else ''
            daily_data.append(
                [
                    count,
                    e_data['machine_details']['equipment_name'],
                    e_data['diesel_consumption_by_equipment'],
                    e_data['opening_meter_reading'],
                    e_data['closing_meter_reading'],
                    e_data['difference_kms'],
                    e_data['opening_hours_reading'],
                    e_data['closing_hours_reading'],
                    e_data['difference_hrs'],
                    e_data['machine_details']['running_km_hr'],
                    e_data['hsd_average'],
                    e_data['machine_details']['standard_fuel_consumption'],
                    contractor,
                    e_data['last_em_maintenance_date'][0:10] if e_data['last_em_maintenance_date'] else None,
                    e_data['next_em_maintenance_schedule'][0:10] if e_data['next_em_maintenance_schedule'] else None,
                ]
                )

        file_name = ''
        if daily_data:
            if os.path.isdir('media/pms/machineries/document/'):
                file_name = 'media/pms/machineries/document/pms_machinery_monthly_report.xlsx'
                file_path = settings.MEDIA_ROOT_EXPORT + file_name
            else:
                os.makedirs('media/pms/machineries/document/')
                file_name = 'media/pms/machineries/document/pms_machinery_monthly_report.xlsx'
                file_path = settings.MEDIA_ROOT_EXPORT + file_name

            
            final_df = pd.DataFrame(daily_data,columns=['SL No.','Equipment','Diesel Consumption By Equipment',
                'Opening Meter Reading','Closing Meter Reading','Difference in Reading(Kms)',
                'Opening Hours Reading','Closing Hours Reading','Difference in Reading(Hrs)',
                'Running(Kms/Hrs)','HSD Average','Standard Fuel Consumption','Contractor Name','Last EM Date','Next EM schedule'])

            #print('count',count) 
            row_num = str(count+2)
            row_num_e = str(count+3)   
            writer = pd.ExcelWriter(file_path, engine='xlsxwriter') 
            final_df.to_excel(writer, startrow=0, startcol=0,index = False, header=True)
            workbook  = writer.book
            worksheet = writer.sheets['Sheet1']
            header_format = workbook.add_format({'bold': True,'bg_color':'#3CB371','font_color':'white','border': 1})
            style_property_1 = workbook.add_format({'bold': True, 'bg_color':'#6495ED','font_color':'white','valign': 'vcenter'})
            
            # for col_num, value in enumerate(final_df.columns.values):
            #     worksheet.write(1, col_num, value, header_format)
            
            worksheet.merge_range('B'+row_num+':'+'B'+row_num_e, 'Total Diesel Available : ',style_property_1)
            worksheet.merge_range('C'+row_num+':'+'C'+row_num_e, str(data_dict['total_diesel_available']),style_property_1)

            worksheet.merge_range('D'+row_num+':'+'D'+row_num_e, 'Total Diesel Consumption By Equipment : ',style_property_1)
            worksheet.merge_range('E'+row_num+':'+'E'+row_num_e, str(data_dict['total_diesel_consumption_by_equipment']),style_property_1)

            worksheet.merge_range('F'+row_num+':'+'F'+row_num_e, 'Other Consumption : ',style_property_1)
            worksheet.merge_range('G'+row_num+':'+'G'+row_num_e, str(data_dict['other_consumption']),style_property_1)

            worksheet.merge_range('H'+row_num+':'+'H'+row_num_e, 'Misc. Consumption : ',style_property_1)
            worksheet.merge_range('I'+row_num+':'+'I'+row_num_e, str(data_dict['miscellaneous_consumption']),style_property_1)

            worksheet.merge_range('J'+row_num+':'+'J'+row_num_e, 'Total Diesel Consumed : ',style_property_1)
            worksheet.merge_range('K'+row_num+':'+'K'+row_num_e, str(data_dict['total_diesel_consumed']),style_property_1)

            worksheet.merge_range('L'+row_num+':'+'L'+row_num_e, 'Diesel Balance : ',style_property_1)
            worksheet.merge_range('M'+row_num+':'+'M'+row_num_e, str(data_dict['diesel_balance']),style_property_1)
 
            writer.save()

        url = getHostWithPort(request) + file_name if file_name else None
        data_dict['url'] = url
        return Response({'results':data_dict,'status':'success','msg':'data found'})  



class MachineryDieselConsumptionReportDwonloadView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsMachinaryDieselConsumptionData.objects.filter(is_deleted=False)
    serializer_class = MachineryDieselConsumptionReportSerializer

    def get_queryset(self):
        filter = dict()
        sort = '-id'
        
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        site_location=self.request.query_params.get('site_location', None)
        project = self.request.query_params.get('project', None)
        start_date=self.request.query_params.get('start_date', None)
        end_date=self.request.query_params.get('end_date', None)

        if project:
            filter['machinary_report__project'] = project

        if site_location:
            filter['machinary_report__site_location'] = site_location

        if start_date and end_date:
            filter['created_at__date__gte'] = start_date
            filter['created_at__date__lte'] = end_date
           
        return self.queryset.filter(**filter).order_by(sort)


    def list(self ,request, *args, **kwargs):
        response = super(MachineryDieselConsumptionReportDwonloadView, self).list(request, args, kwargs)
        daily_data = list()
        count = 0
        for e_data in response.data:
            count +=1 
            daily_data.append(
                [
                    count,
                    e_data['machine_details']['equipment_name'],
                    e_data['machine_details']['equipment_make'],
                    e_data['machine_details']['equipment_model_no'],
                    e_data['planned_avaliability'],
                    e_data['opening_meter_reading'],
                    e_data['closing_meter_reading'],
                    e_data['total_kms'],
                    e_data['opening_hours_reading'],
                    e_data['closing_hours_reading'],
                    e_data['total_hrs'],
                    e_data['breakdown_hours'],
                    e_data['idle_period'],
                    e_data['utilization'],
                    e_data['diesel_consumption_by_equipment'],
                    'Kms.' if e_data['uom'] == 'distence' else 'Hrs.',
                    e_data['actual_average'],
                    e_data['standard_average'],
                ]
                )
        file_name = ''
        if daily_data:
            if os.path.isdir('media/pms/machineries/document/'):
                file_name = 'media/pms/machineries/document/pms_machinery_diesel_consumption_report.xlsx'
                file_path = settings.MEDIA_ROOT_EXPORT + file_name
            else:
                os.makedirs('media/pms/machineries/document/')
                file_name = 'media/pms/machineries/document/pms_machinery_diesel_consumption_report.xlsx'
                file_path = settings.MEDIA_ROOT_EXPORT + file_name

            
            final_df = pd.DataFrame(daily_data,columns=['SL No.','Equipment Desciption','Equipment Make','Equipment Model','Planned Availability',
                'Start KMS Reading','Closing KMS Reading','Total Working KMS',
                'Start HRS Reading','Closing HRS Reading','Total working HRS',
                'B/D Period','Idle Period','Utilization %','HSD Consumed Period','UOM','Act. Avg.','Std. Avg.'])

            export_csv = final_df.to_excel (file_path, index = None, header=True)
           

        url = getHostWithPort(request) + file_name if file_name else None
        return Response({'results':{'url':url},'status':'success','msg':'data found'}) 

class MachineriesListDetailsDownloadView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsMachineries.objects.filter(is_deleted=False)
    serializer_class = MachineriesListDetailsSerializer

    def get_queryset(self):
        filter = dict()
        sort = '-id'
        project= self.request.query_params.get('project', None)
        owner_type=self.request.query_params.get('owner_type', None)
        search = self.request.query_params.get('search', None)
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)

        if search:
            filter['equipment_name__icontains'] = search

        if field_name and order_by:
            if field_name == 'equipment_name' and order_by == 'asc':
                sort = 'equipment_name'
            elif field_name == 'equipment_name' and order_by == 'desc':
                sort = '-equipment_name'
            elif field_name == 'equipment_category' and order_by == 'asc':
                sort = 'equipment_category__name'
            elif field_name == 'equipment_category' and order_by == 'desc':
                sort = '-equipment_category__name'
            elif field_name == 'equipment_make' and order_by == 'asc':
                sort = 'equipment_make'
            elif field_name == 'equipment_make' and order_by == 'desc':
                sort = '-equipment_make'
            elif field_name == 'equipment_model_no' and order_by == 'asc':
                sort = 'equipment_model_no'
            elif field_name == 'equipment_model_no' and order_by == 'desc':
                sort = '-equipment_model_no'

        if project:
            project = project.split(',')
            filter['pk__in'] = PmsProjectsMachinaryMapping.objects.filter(project__in=project,is_deleted=False).values_list('machinary',flat=True)
           
        if owner_type:
            filter['owner_type__in'] = owner_type
           
        return self.queryset.filter(**filter).order_by(sort)

    def list(self ,request, *args, **kwargs):
        response = super(MachineriesListDetailsDownloadView, self).list(request, args, kwargs)
        daily_data = list()
        owner_type=self.request.query_params.get('owner_type', None)
        count = 0

        if owner_type == '1':
            for e_data in response.data:
                count +=1 
                project_list = e_data['project']
                project = ' , '.join([str(elem['name']) for elem in project_list]) 
                daily_data.append(
                    [
                        count,
                        e_data['equipment_name'],
                        e_data['equipment_category_details']['name'] if e_data['equipment_category_details'] else '',
                        project,
                        e_data['equipment_make'],
                        e_data['equipment_model_no'],
                        e_data['equipment_chassis_serial_no'],
                        e_data['equipment_engine_serial_no'],
                        e_data['equipment_registration_no'],
                        e_data['equipment_power'],
                        'Kms.' if e_data['measurement_by'] == 'distence' else 'Hrs.',
                        e_data['standard_fuel_consumption'],
                        e_data['reading_type'],
                        e_data['running_km_hr'],
                        e_data['rented_details']['vendor_name'] if e_data['rented_details'] else '',
                        e_data['rented_details']['type_of_rent'] if e_data['rented_details'] else '',
                        e_data['rented_details']['rent_amount'] if e_data['rented_details'] else '',
                        str(e_data['rented_details']['start_date'])[0:10] if e_data['rented_details'] else '',
                        str(e_data['rented_details']['end_date'])[0:10] if e_data['rented_details'] else '',

                    ]

                )

        if owner_type == '2':
            for e_data in response.data:
                count +=1 
                project_list = e_data['project']
                project = ' , '.join([str(elem['name']) for elem in project_list]) 
                daily_data.append(
                    [
                        count,
                        e_data['equipment_name'],
                        e_data['equipment_category_details']['name'] if e_data['equipment_category_details'] else '',
                        project,
                        e_data['equipment_make'],
                        e_data['equipment_model_no'],
                        e_data['equipment_chassis_serial_no'],
                        e_data['equipment_engine_serial_no'],
                        e_data['equipment_registration_no'],
                        e_data['equipment_power'],
                        'Kms.' if e_data['measurement_by'] == 'distence' else 'Hrs.',
                        e_data['standard_fuel_consumption'],
                        e_data['reading_type'],
                        e_data['running_km_hr'],
                        e_data['owner_emi_details']['price'] if e_data['owner_emi_details'] else '',
                        e_data['owner_emi_details']['purchase_date'] if e_data['owner_emi_details'] else '',

                    ]

                )

        if owner_type == '3':
            for e_data in response.data:
                count +=1 
                project_list = e_data['project']
                project = ' , '.join([str(elem['name']) for elem in project_list]) 
                daily_data.append(
                    [
                        count,
                        e_data['equipment_name'],
                        e_data['equipment_category_details']['name'] if e_data['equipment_category_details'] else '',
                        project,
                        e_data['equipment_make'],
                        e_data['equipment_model_no'],
                        e_data['equipment_chassis_serial_no'],
                        e_data['equipment_engine_serial_no'],
                        e_data['equipment_registration_no'],
                        e_data['equipment_power'],
                        'Kms.' if e_data['measurement_by'] == 'distence' else 'Hrs.',
                        e_data['standard_fuel_consumption'],
                        e_data['reading_type'],
                        e_data['running_km_hr'],
                        e_data['contractor_details']['contractor_name'] if e_data['contractor_details'] else ''
                    ]

                )
                
        if owner_type == '4':
            for e_data in response.data:
                count +=1 
                project_list = e_data['project']
                project = ' , '.join([str(elem['name']) for elem in project_list]) 
                daily_data.append(
                    [
                        count,
                        e_data['equipment_name'],
                        e_data['equipment_category_details']['name'] if e_data['equipment_category_details'] else '',
                        project,
                        e_data['equipment_make'],
                        e_data['equipment_model_no'],
                        e_data['equipment_chassis_serial_no'],
                        e_data['equipment_engine_serial_no'],
                        e_data['equipment_registration_no'],
                        e_data['equipment_power'],
                        'Kms.' if e_data['measurement_by'] == 'distence' else 'Hrs.',
                        e_data['standard_fuel_consumption'],
                        e_data['reading_type'],
                        e_data['running_km_hr'],
                        e_data['lease_details']['vendor_name'] if e_data['lease_details'] else '',
                        e_data['lease_details']['lease_amount'] if e_data['lease_details'] else '',
                        str(e_data['lease_details']['start_date'])[0:10] if e_data['lease_details'] else '',
                        str(e_data['lease_details']['lease_period'])[0:10] if e_data['lease_details'] else '',

                    ]

                )      
            
       
        file_name = ''
        if daily_data:
            if os.path.isdir('media/pms/machineries/document/'):
                file_name = 'media/pms/machineries/document/pms_machinery_list.xlsx'
                file_path = settings.MEDIA_ROOT_EXPORT + file_name
            else:
                os.makedirs('media/pms/machineries/document/')
                file_name = 'media/pms/machineries/document/pms_machinery_list.xlsx'
                file_path = settings.MEDIA_ROOT_EXPORT + file_name

            columns=['SL No.','Equipment Desciption','Equipment Category','Projects','Equipment Make',
                'Equipment Model','Equipment Chassis Serial No','Equipment Engine Serial No','Equipment Registration No','Power/Ratings',
                'Unit','Standard Fuel Consumption','Equipment Reading in','Running KM/HR']

            if owner_type == '1':
                columns.append('Vendor')
                columns.append('Rent Type')
                columns.append('Rent Amount')
                columns.append('Start Date')
                columns.append('End Date')

            if owner_type == '2':
                columns.append('Equipment Price')
                columns.append('Equipment Purchase Date')

            if owner_type == '3':
                columns.append('Contractor')

            if owner_type == '4':
                columns.append('Vendor')
                columns.append('Lease Amount')
                columns.append('Start Date')
                columns.append('Lease Period')
            
            final_df = pd.DataFrame(daily_data,columns=columns)
            export_csv = final_df.to_excel (file_path, index = None, header=True)
           

        url = getHostWithPort(request) + file_name if file_name else None
        return Response({'results':{'url':url},'status':'success','msg':'data found'}) 

## End Functional Specification Document - PMS_V4.0 | Date : 22-07-2020 | Rupam Hazra ##
