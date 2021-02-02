from django.shortcuts import render
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from pms.models.module_accounts import *
from pms.serializers.accounts import *
import time
from multiplelookupfields import MultipleFieldLookupMixin
from django.conf import settings
from pagination import CSLimitOffestpagination,CSPageNumberPagination,OnOffPagination
from rest_framework import filters
import calendar
from datetime import datetime
from rest_framework.exceptions import APIException
from django_filters.rest_framework import DjangoFilterBackend
from users.models import TCoreUserDetail
from custom_decorator import *
import os
from knox.auth import TokenAuthentication
from rest_framework import permissions
from knox.models import AuthToken

class PmsAccountUserAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsAccounts.objects.filter(is_deleted=False)
    serializer_class = PmsAccountUserAddSerializer

    def get_queryset(self):
        sort_field='-id'
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        if field_name and order_by:
            if field_name =='user' and order_by=='asc':
                sort_field='user__username'
            if field_name =='user' and order_by=='desc':
                sort_field='-user__username'

        return self.queryset.order_by(sort_field)

    @response_modify_decorator_post
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
            
    @response_modify_decorator_list
    def list(self, request, *args, **kwargs):
        response = super(__class__, self).get(self, request, args, kwargs)
        return response

class PmsAccountUserEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsAccounts.objects.filter(is_deleted=False)
    serializer_class = PmsAccountUserEditSerializer

    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        response = super(__class__, self).get(self, request, args, kwargs)
        return response

    @response_modify_decorator_update
    def put(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

class PmsHoUserAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsHoUser.objects.filter(is_deleted=False)
    serializer_class = PmsHoUserAddSerializer

    def get_queryset(self):
        sort_field='-id'
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        if field_name and order_by:
            if field_name =='user' and order_by=='asc':
                sort_field='user__username'
            if field_name =='user' and order_by=='desc':
                sort_field='-user__username'

        return self.queryset.order_by(sort_field)

    @response_modify_decorator_post
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
            
    @response_modify_decorator_list
    def list(self, request, *args, **kwargs):
        response = super(__class__, self).get(self, request, args, kwargs)
        return response

class PmsHoUserEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsHoUser.objects.filter(is_deleted=False)
    serializer_class = PmsHoUserEditSerializer

    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        response = super(__class__, self).get(self, request, args, kwargs)
        return response

    @response_modify_decorator_update
    def put(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)


class PmsTourAccountUserAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsTourAccounts.objects.filter(is_deleted=False)
    serializer_class = PmsTourAccountUserAddSerializer

    def get_queryset(self):
        sort_field = '-id'
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        if field_name and order_by:
            if field_name == 'user' and order_by == 'asc':
                sort_field = 'user__username'
            if field_name == 'user' and order_by == 'desc':
                sort_field = '-user__username'

        return self.queryset.order_by(sort_field)

    @response_modify_decorator_post
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    @response_modify_decorator_list
    def list(self, request, *args, **kwargs):
        response = super(__class__, self).get(self, request, args, kwargs)
        return response

class PmsTourAccountUserEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsTourAccounts.objects.filter(is_deleted=False)
    serializer_class = PmsTourAccountUserEditSerializer

    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        response = super(__class__, self).get(self, request, args, kwargs)
        return response

    @response_modify_decorator_update
    def put(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

class PmsTourHoUserAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsTourHoUser.objects.filter(is_deleted=False)
    serializer_class = PmsTourHoUserAddSerializer

    def get_queryset(self):
        sort_field = '-id'
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        if field_name and order_by:
            if field_name == 'user' and order_by == 'asc':
                sort_field = 'user__username'
            if field_name == 'user' and order_by == 'desc':
                sort_field = '-user__username'

        return self.queryset.order_by(sort_field)

    @response_modify_decorator_post
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    @response_modify_decorator_list
    def list(self, request, *args, **kwargs):
        response = super(__class__, self).get(self, request, args, kwargs)
        return response

class PmTourHoUserEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsTourHoUser.objects.filter(is_deleted=False)
    serializer_class = PmsTourHoUserEditSerializer

    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        response = super(__class__, self).get(self, request, args, kwargs)
        return response

    @response_modify_decorator_update
    def put(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)


# class PmsSiteBillsInvoicesHoUserAddView(generics.ListCreateAPIView):
#     permission_classes = [IsAuthenticated]
#     authentication_classes = [TokenAuthentication]
#     queryset = PmsSiteBillsInvoicesHoUser.objects.filter(is_deleted=False)
#     serializer_class = PmsSiteBillsInvoicesHoUserAddSerializer

#     def get_queryset(self):
#         sort_field='-id'
#         field_name = self.request.query_params.get('field_name', None)
#         order_by = self.request.query_params.get('order_by', None)
#         if field_name and order_by:
#             if field_name =='user' and order_by=='asc':
#                 sort_field='user__username'
#             if field_name =='user' and order_by=='desc':
#                 sort_field='-user__username'

#         return self.queryset.order_by(sort_field)

#     @response_modify_decorator_post
#     def post(self, request, *args, **kwargs):
#         return super().post(request, *args, **kwargs)
            
#     @response_modify_decorator_list
#     def list(self, request, *args, **kwargs):
#         response = super(__class__, self).get(self, request, args, kwargs)
#         return response

# class PmsSiteBillsInvoicesHoUserEditView(generics.RetrieveUpdateAPIView):
#     permission_classes = [IsAuthenticated]
#     authentication_classes = [TokenAuthentication]
#     queryset = PmsSiteBillsInvoicesHoUser.objects.filter(is_deleted=False)
#     serializer_class = PmsSiteBillsInvoicesHoUserEditSerializer

#     @response_modify_decorator_get
#     def get(self, request, *args, **kwargs):
#         response = super(__class__, self).get(self, request, args, kwargs)
#         return response

#     @response_modify_decorator_update
#     def put(self, request, *args, **kwargs):
#         return super().update(request, *args, **kwargs)
