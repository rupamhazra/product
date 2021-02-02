from django.shortcuts import render
from rest_framework import generics
# from rest_framework.authtoken.views import ObtainAuthToken
# from rest_framework.authtoken.models import Token
# from django.contrib.auth.models import Permission
# from django.contrib.auth.models import *
from vendor.serializers import *
from rest_framework.response import Response
from rest_framework import filters
# permission checking
from rest_framework.permissions import IsAuthenticated, IsAdminUser, IsAuthenticatedOrReadOnly
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
# get_current_site
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings
from pagination import CSLimitOffestpagination, CSPageNumberPagination, OnOffPagination
from django_filters.rest_framework import DjangoFilterBackend
from master.models import TMasterOtherRole, TMasterModuleRoleUser
import collections
from custom_decorator import *
from rest_framework.views import APIView
from django.db.models import When, Case, Value, CharField, IntegerField, F, Q
from users.models import *
from knox.auth import TokenAuthentication
from vendor.models import *


class VendorAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = VendorDetails.objects.filter(is_deleted=False)
    serializer_class = VendorAddSerializer


class VendorBasicDetailView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = VendorDetails.objects.filter(is_deleted=False)
    serializer_class = VendorBasicDetailSerializer
    pagination_class = CSPageNumberPagination

    def get_queryset(self):
        vendor = self.request.query_params.get('vendor_id', None)
        filter = {}
        if vendor:
            filter['id'] = vendor
        result = self.queryset.filter(**filter)
        return result

    @response_modify_decorator_list_or_get_after_execution_for_pagination
    def get(self, request, *args, **kwargs):
        response = super(__class__, self).get(self, request, args, kwargs)
        for data in response.data['results']:
            response.data['results'] = data
            city_obj = TCoreCity.objects.get(id=data['id']).name
            data['city_name'] = city_obj
        del response.data['count']
        del response.data['next']
        del response.data['previous']
        return response


class VendorContactAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = VendorContactDetails.objects.filter(is_deleted=False)
    serializer_class = VendorContactsAddSerializer


class VendorContactListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = VendorContactDetails.objects.filter(is_deleted=False)
    serializer_class = VendorContactListSerializer
    pagination_class = CSPageNumberPagination

    def get_queryset(self):
        vendor = self.request.query_params.get('vendor_id', None)
        filter = {}
        if vendor:
            filter['vendor__id'] = vendor
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        # sort_field = '-id'
        result = self.queryset.filter(**filter)
        return result

    # @response_modify_decorator_get
    @response_modify_decorator_list_or_get_after_execution_for_pagination
    def get(self, request, *args, **kwargs):
        response = super(__class__, self).get(self, request, *args, **kwargs)
        del response.data['count']
        del response.data['next']
        del response.data['previous']
        return response

class VendorApprovalListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = VendorDetails.objects.filter(is_deleted=False)
    serializer_class = VendorApprovelListSerializer
    pagination_class = CSPageNumberPagination

    def get_queryset(self):
        creation_id = self.request.query_params.get('creation_id',None)
        vendor_code = self.request.query_params.get('vendor_code',None)
        vendor_name = self.request.query_params.get('vendor_name', None)
        account_group = self.request.query_params.get('account_group', None)
        approver_name = self.request.query_params.get('approver_name', None)
        is_approve= self.request.query_params.get('is_approve', None)
        is_active = self.request.query_params.get('is_active', None)
        sort_field='-id'
        filter = dict()

        if vendor_code:
            filter['vendor_code__icontains'] = vendor_code

        if creation_id:
            filter['creation_id__icontains'] = creation_id

        if vendor_name:
            filter['name1__icontains'] = vendor_name

        if account_group:
            filter['account_group__icontains'] = account_group

        if approver_name:
            filter['approver_name__icontains'] = approver_name

        if is_approve:
            if is_approve == "1":
                filter['is_approve'] = True
                if is_active:
                    if is_active == "1":
                        filter['is_active'] = True
                    else:
                        filter['is_active'] = False
            else:
                filter['is_approve'] = False
      
        queryset = self.queryset.filter(**filter).order_by(sort_field)
        return queryset

    @response_modify_decorator_list_or_get_after_execution_for_pagination
    def get(self, request, *args, **kwargs):
        response = super(__class__, self).get(self, request, *args, **kwargs)
        # del response.data['count']
        # del response.data['next']
        # del response.data['previous']
        return response


class VendorBasicDetailEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = VendorDetails.objects.all()
    serializer_class = VendorBasicDetailEditSerializer


class VendorMasterApprovalView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = VendorDetails.objects.filter(is_deleted=False)
    serializer_class =VendorApprovalStatusUpdateSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('user_type',)

    @response_modify_decorator_post
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class VendorMasterRejectView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = VendorDetails.objects.filter(is_deleted=False)
    serializer_class =VendorRejectStatusUpdateSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('user_type',)

    @response_modify_decorator_post
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)