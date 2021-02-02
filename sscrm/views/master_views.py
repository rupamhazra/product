import collections

from celery.result import AsyncResult
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import F, Q, Sum
from rest_framework.generics import (ListAPIView, CreateAPIView, UpdateAPIView, RetrieveAPIView, ListCreateAPIView,
                                     RetrieveUpdateAPIView)
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from knox.auth import TokenAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from  sscrm.serializers import master_serializers
from global_function import get_users_under_reporting_head
from master.models import TMasterModuleRoleUser
from pagination import CSPageNumberPagination, OnOffPagination
from datetime import datetime, timedelta, timezone
from custom_decorator import (response_modify_decorator_get, response_modify_decorator_update,
                              response_modify_decorator_list_or_get_after_execution_for_pagination,
                              response_modify_decorator_list_or_get_before_execution_for_onoff_pagination,
                              response_with_status_get, response_modify_decorator_get_after_execution)

from sscrm.models import (SSCrmCustomer,SSCrmContractType,SSCrmCustomerCodeType)
from sscrm import serializers


# :::::::::::::::::::::: Customer ::::::::::::::::::::::::::: #
class SSCrmCustomerAddView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = SSCrmCustomer.cmobjects.all()
    serializer_class = serializers.SSCrmCustomerAddSerializer
    pagination_class = OnOffPagination

    @response_modify_decorator_list_or_get_before_execution_for_onoff_pagination
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class SSCrmCustomerEditView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = SSCrmCustomer.cmobjects.all()
    serializer_class = serializers.SSCrmCustomerEditSerializer

class SSCrmCustomerDeleteView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = SSCrmCustomer.cmobjects.all()
    serializer_class = serializers.SSCrmCustomerDeleteSerializer


#:::::::::::::::::::::::: CustomerCodeType ::::::::::::::::::::::::::: #
class SSCrmCustomerCodeTypeAddView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = SSCrmCustomerCodeType.cmobjects.all()
    serializer_class = serializers.SSCrmCustomerCodeTypeDeleteViewAddSerializer
    pagination_class = OnOffPagination

    @response_modify_decorator_list_or_get_before_execution_for_onoff_pagination
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class SSCrmCustomerCodeTypeEditView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = SSCrmCustomerCodeType.cmobjects.all()
    serializer_class = serializers.SSCrmCustomerCodeTypeDeleteViewEditSerializer

class SSCrmCustomerCodeTypeDeleteView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = SSCrmCustomerCodeType.cmobjects.all()
    serializer_class = serializers.SSCrmCustomerCodeTypeDeleteViewDeleteSerializer
    

#:::::::::::::::::::::::: ContractType ::::::::::::::::::::::::::: #
class SSCrmContractTypeAddView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = SSCrmContractType.cmobjects.all()
    serializer_class = serializers.SSCrmContractTypeAddSerializer
    pagination_class = OnOffPagination

    @response_modify_decorator_list_or_get_before_execution_for_onoff_pagination
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class SSCrmContractTypeEditView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = SSCrmContractType.cmobjects.all()
    serializer_class = serializers.SSCrmContractTypeEditSerializer


class SSCrmContractTypeDeleteView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = SSCrmContractType.cmobjects.all()
    serializer_class = serializers.SSCrmContractTypeDeleteSerializer