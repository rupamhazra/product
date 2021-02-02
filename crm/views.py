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

from core.models import TCoreCountry
from crm.constant import DEFAULT_CURRENCY
from crm.currency_converter import realtime_exchange_value
from crm.filters import (CrmLeadFilter, CrmOpportunityFilter, CrmAccountFilter, CrmCloseWonFilter,
                         CrmLossAnalysisFilter, CrmLeadReportFilter, CrmInvoiceReportFilter, CrmProjectReportFilter)

from crm.tasks import hello_crm
from crm.utils import (response_on_off_modified, download_url_generator, get_user_type, get_query_by_user_type,
                       get_users_by_type, convert_to_utc)
from custom_decorator import (response_modify_decorator_get, response_modify_decorator_update,
                              response_modify_decorator_list_or_get_after_execution_for_pagination,
                              response_modify_decorator_list_or_get_before_execution_for_onoff_pagination,
                              response_with_status_get, response_modify_decorator_get_after_execution)
from crm.models import (CrmLead, CrmTask, CrmOpportunity, CrmProject, CrmDepartment, CrmTechnology, CrmSource,
                        CrmUserTypeMap, CrmPoc, CrmPaymentMode, CrmColorStatus, CrmOpportunityMilestoneMap, CrmDocument,
                        CrmChangeRequest, CrmLeadDocument, CrmResource, CrmDocumentTag, CrmRequestHandler,
                        CrmOpportunityDocumentTag)
from crm import serializers
from global_function import get_users_under_reporting_head
from master.models import TMasterModuleRoleUser
from pagination import CSPageNumberPagination, OnOffPagination
from datetime import datetime, timedelta, timezone

from users.models import TCoreUserDetail, UserTempReportingHeadMap


class CrmDatabaseQueryView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get(self, request, *args, **kwargs):
        action_confirm = self.request.query_params.get('action_confirm', 'no')
        action = self.request.query_params.get('action', None)
        query_set = None

        if action == 'CREATE_OR_UPDATE_COUNTRY_LIST':
            query_set = TCoreCountry.objects.all()
            if action_confirm == 'yes':
                with transaction.atomic():
                    import pycountry
                    #print(phonenumbers.COUNTRY_CODE_TO_REGION_CODE)
                    print('query_set:',query_set)
                    for country in pycountry.countries:
                        print(dir(country))
                        country_obj, is_created = TCoreCountry.objects.get_or_create(name=country.name)
                        country_obj.code = country.alpha_2
                        country_obj.code_3 = country.alpha_3
                        country_obj.save()
        if action == 'CREATE_OR_UPDATE_DIALING_CODE':
            query_set = TCoreCountry.objects.all()
            if action_confirm == 'yes':
                with transaction.atomic():
                    import phonenumbers
                    for dcode, countries in phonenumbers.COUNTRY_CODE_TO_REGION_CODE.items():
                        filtered_countries = query_set.filter(code__in=countries)
                        filtered_countries.update(dialing_code=str(dcode))

        if action == 'CELERY_EXECUTE_DELAY':
            query_set = CrmTask.cmobjects.filter(is_completed=False)
            if action_confirm == 'yes':
                with transaction.atomic():
                    current_date = convert_to_utc(date_time=datetime.now())
                    celery_task = hello_crm.apply_async(eta=current_date + timedelta(seconds=120))
                    print(celery_task.id, type(celery_task), dir(celery_task))

                    from SSIL_SSO_MS.celery import app
                    app.control.revoke(celery_task.id, terminate=True)


        return Response({'action':action, 'action_confirm': action_confirm, 'query_set': query_set.values() if query_set else None})


# :::::::::::::::::::::: Document ::::::::::::::::::::::::::: #
class CrmDocumentAddView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    parser_classes = [MultiPartParser]
    queryset = CrmDocument.cmobjects.all()
    serializer_class = serializers.CrmDocumentAddSerializer
    pagination_class = OnOffPagination

    @response_modify_decorator_list_or_get_before_execution_for_onoff_pagination
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CrmDocumentMultiUploadView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    parser_classes = [MultiPartParser]
    queryset = CrmDocument.cmobjects.all()
    serializer_class = serializers.CrmDocumentMultiUploadSerializer
    pagination_class = OnOffPagination

    @response_modify_decorator_update
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


# :::::::::::::::::::::: Department ::::::::::::::::::::::::::: #
class CrmDepartmentAddView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmDepartment.cmobjects.all()
    serializer_class = serializers.CrmDepartmentAddSerializer
    pagination_class = OnOffPagination

    @response_modify_decorator_list_or_get_before_execution_for_onoff_pagination
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CrmDepartmentEditView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmDepartment.cmobjects.all()
    serializer_class = serializers.CrmDepartmentEditSerializer


class CrmDepartmentDeleteView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmDepartment.cmobjects.all()
    serializer_class = serializers.CrmDepartmentDeleteSerializer


# :::::::::::::::::::::: Resource ::::::::::::::::::::::::::: #
class CrmResourceAddView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmResource.cmobjects.all()
    serializer_class = serializers.CrmResourceAddSerializer
    pagination_class = OnOffPagination

    @response_modify_decorator_list_or_get_before_execution_for_onoff_pagination
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CrmResourceEditView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmResource.cmobjects.all()
    serializer_class = serializers.CrmResourceEditSerializer


class CrmResourceDeleteView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmResource.cmobjects.all()
    serializer_class = serializers.CrmResourceDeleteSerializer


# :::::::::::::::::::::: DocumentTag ::::::::::::::::::::::::::: #
class CrmDocumentTagAddView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmDocumentTag.cmobjects.all()
    serializer_class = serializers.CrmDocumentTagAddSerializer
    pagination_class = OnOffPagination

    @response_modify_decorator_list_or_get_before_execution_for_onoff_pagination
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CrmDocumentTagEditView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmDocumentTag.cmobjects.all()
    serializer_class = serializers.CrmDocumentTagEditSerializer


class CrmDocumentTagDeleteView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmDocumentTag.cmobjects.all()
    serializer_class = serializers.CrmDocumentTagDeleteSerializer


# :::::::::::::::::::::: Technology ::::::::::::::::::::::::::: #
class CrmTechnologyAddView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmTechnology.cmobjects.all()
    serializer_class = serializers.CrmTechnologyAddSerializer
    pagination_class = OnOffPagination

    @response_modify_decorator_list_or_get_before_execution_for_onoff_pagination
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CrmTechnologyEditView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmTechnology.cmobjects.all()
    serializer_class = serializers.CrmTechnologyEditSerializer


class CrmTechnologyDeleteView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmTechnology.cmobjects.all()
    serializer_class = serializers.CrmTechnologyDeleteSerializer


# :::::::::::::::::::::: Source ::::::::::::::::::::::::::: #
class CrmSourceAddView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmSource.cmobjects.all()
    serializer_class = serializers.CrmSourceAddSerializer
    pagination_class = OnOffPagination

    @response_modify_decorator_list_or_get_before_execution_for_onoff_pagination
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CrmSourceEditView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmSource.cmobjects.all()
    serializer_class = serializers.CrmSourceEditSerializer


class CrmSourceDeleteView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmSource.cmobjects.all()
    serializer_class = serializers.CrmSourceDeleteSerializer


# :::::::::::::::::::::: PaymentMode ::::::::::::::::::::::::::: #
class CrmPaymentModeAddView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmPaymentMode.cmobjects.all()
    serializer_class = serializers.CrmPaymentModeAddSerializer
    pagination_class = OnOffPagination

    @response_modify_decorator_list_or_get_before_execution_for_onoff_pagination
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CrmPaymentModeEditView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmPaymentMode.cmobjects.all()
    serializer_class = serializers.CrmPaymentModeEditSerializer


class CrmPaymentModeDeleteView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmPaymentMode.cmobjects.all()
    serializer_class = serializers.CrmPaymentModeDeleteSerializer


# :::::::::::::::::::::: ColorStatus ::::::::::::::::::::::::::: #
class CrmColorStatusAddView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmColorStatus.cmobjects.all()
    serializer_class = serializers.CrmColorStatusAddSerializer
    pagination_class = OnOffPagination

    @response_modify_decorator_list_or_get_before_execution_for_onoff_pagination
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CrmColorStatusEditView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmColorStatus.cmobjects.all()
    serializer_class = serializers.CrmColorStatusEditSerializer


class CrmColorStatusDeleteView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmColorStatus.cmobjects.all()
    serializer_class = serializers.CrmColorStatusDeleteSerializer


class CrmLeadListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = CrmLeadFilter
    filterset_fields = ['status', 'poc__source', 'poc__country', 'territory']
    search_fields = ['business_name', 'poc__first_name', 'poc__last_name', 'poc__country__name', 'poc__phone',
                     'poc__email', 'poc__source__name', 'social_link']
    ordering_fields = ['business_name', 'poc__first_name', 'poc__last_name', 'poc__country__name', 'poc__phone',
                       'poc__email']
    ordering = ['-id']
    queryset = CrmLead.cmobjects.all()
    serializer_class = serializers.CrmLeadListSerializer
    pagination_class = CSPageNumberPagination

    def get_queryset(self):
        current_datetime = datetime.now()
        login_user = self.request.query_params.get('login_user')
        days_old = self.request.query_params.get('days_old')
        list_type = self.request.query_params.get('list_type')
        assigned_users = self.request.query_params.get('assigned_users')
        assigned_users = assigned_users.split(',') if assigned_users else get_users_by_type(type='Prospecting Team Member')

        query_by_user_type = get_query_by_user_type(login_user=login_user, assigned_users=assigned_users, table_type='lead')
        query_set = CrmLead.objects.none()
        if list_type == 'assigned_from_sm':
            query_set = self.queryset.filter(~Q(Q(status=5)|Q(status=6))).filter(query_by_user_type).filter(
                            ~Q(Q(assign_to__isnull=True)&Q(created_by_id=2450)))
        elif list_type == 'pool':
            query_set = self.queryset.filter(Q(Q(assign_to__isnull=True)&Q(Q(created_by=login_user)|Q(created_by_id=2450)))|
                            Q(Q(status=5)|Q(status=6)))
        elif list_type == 'assigned_to_ptm':
            query_set = self.queryset.filter(~Q(Q(status=5)|Q(status=6))).filter(query_by_user_type).filter(
                            ~Q(Q(assign_to__isnull=True)&Q(created_by_id=2450)))
        elif list_type == 'lead_history':
            query_set = self.queryset.filter(Q(status=5)|Q(status=6)).filter(query_by_user_type)

        if days_old:
            query = None
            if days_old == 'recent':
                min_date = current_datetime.date() - timedelta(days=0)
                max_date = current_datetime.date() - timedelta(days=7)
                query = Q(created_at__date__lte=min_date)&Q(created_at__date__gte=max_date)
            elif days_old == '7days_old':
                min_date = current_datetime.date() - timedelta(days=8)
                max_date = current_datetime.date() - timedelta(days=14)
                query = Q(created_at__date__lte=min_date)&Q(created_at__date__gte=max_date)
            elif days_old == 'fortnight':
                min_date = current_datetime.date() - timedelta(days=14)
                query = Q(created_at__date__lt=min_date)

            query_set = query_set.filter(query)
        return query_set

    @response_modify_decorator_list_or_get_after_execution_for_pagination
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CrmLeadCreateView(CreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmLead.cmobjects.all()
    serializer_class = serializers.CrmLeadCreateSerializer

    @response_modify_decorator_update
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


class CrmLeadUpdateView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmLead.cmobjects.all()
    serializer_class = serializers.CrmLeadUpdateSerializer

    @response_modify_decorator_update
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class CrmLeadBulkUploadView(CreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmLeadDocument.cmobjects.all()
    serializer_class = serializers.CrmLeadBulkUploadSerializer

    @response_modify_decorator_update
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


class CrmStatusUpdateMultiLeadView(CreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmLead.cmobjects.all()
    serializer_class = serializers.CrmStatusUpdateMultiLeadSerializer

    @response_modify_decorator_update
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


class CrmLeadStatusUpdateView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmLead.cmobjects.all()
    serializer_class = serializers.CrmLeadStatusUpdateSerializer

    @response_modify_decorator_update
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class CrmLeadAssignView(CreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmLead.cmobjects.all()
    serializer_class = serializers.CrmLeadAssignSerializer

    @response_modify_decorator_update
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


class CrmAddTaskToLeadView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmLead.cmobjects.all()
    serializer_class = serializers.CrmAddTaskToLeadSerializer

    @response_modify_decorator_update
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class CrmLeadRequestReassignView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmLead.cmobjects.all()
    serializer_class = serializers.CrmLeadRequestReassignSerializer

    @response_modify_decorator_update
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class CrmLeadDetailsView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmLead.cmobjects.all()
    serializer_class = serializers.CrmLeadDetailsSerializer

    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CrmTaskUpdateView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmTask.cmobjects.all()
    serializer_class = serializers.CrmTaskUpdateSerializer

    @response_modify_decorator_update
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class CrmPocUpdateView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmPoc.cmobjects.all()
    serializer_class = serializers.CrmPocUpdateSerializer

    @response_modify_decorator_update
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class CrmOpportunityCreateView(CreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmOpportunity.cmobjects.all()
    serializer_class = serializers.CrmOpportunityCreateSerializer

    @response_modify_decorator_update
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


class CrmOpportunitySnapshotListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = CrmOpportunityFilter
    filterset_fields = ['id', 'lead__poc__source', 'engagement', 'technology', 'stage']
    ordering_fields = ['lead__created_at', 'lead__poc__source__name', 'business_name', 'value']
    search_fields = ['business_name', 'lead__poc__source__name', 'opportunity_name']
    ordering = ['-id']
    queryset = CrmOpportunity.cmobjects.filter(status=0)
    serializer_class = serializers.CrmOpportunitySnapshotListSerializer
    pagination_class = OnOffPagination

    def get_queryset(self):
        login_user = self.request.query_params.get('login_user')
        assigned_users = self.request.query_params.get('assigned_users')
        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')
        assigned_users = assigned_users.split(',') if assigned_users else get_users_by_type(type='Prospecting Team Member')

        filters = dict()
        if from_date and to_date:
            filters['lead__created_at__date__gte'] = from_date
            filters['lead__created_at__date__lte'] = to_date

        query_by_user_type = get_query_by_user_type(login_user=login_user, assigned_users=assigned_users,
                                                    table_type='opportunity')

        return self.queryset.filter(query_by_user_type, **filters)

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        login_user = self.request.query_params.get('login_user')
        is_download = self.request.query_params.get('is_download')
        extension_type = self.request.query_params.get('extension_type')

        if is_download == 'yes':
            if len(response.data):
                column_header = collections.OrderedDict()
                column_header['lead_date'] = 'Lead Date'
                column_header['source_name'] = 'Source'
                column_header['opportunity_name'] = 'Opportunity Name'
                column_header['business_name'] = 'Business Name'
                column_header['engagement_name'] = 'Engagement'
                column_header['technologies'] = 'Technology'
                column_header['stage_name'] = 'Current Opp Stage'
                column_header['value'] = 'Deal Value'
                column_header['probability'] = 'Probability'
                column_header['prospecting_member_name'] = 'Prospecting'
                column_header['sales_manager_name'] = 'Closure'
                column_header['latest_remarks'] = 'Remarks'

                columns = list(column_header.keys())
                headers = list(column_header.values())
                file_name = 'pipeline_snapshot.{}'.format(extension_type)
                url = download_url_generator(request, data=response.data, base_path='media/crm',
                                             extension_type=extension_type, file_name=file_name, columns=columns,
                                             headers=headers)

                # url = download_url_generator(request, data=response.data,base_path='media/crm',
                #                              file_name='pipeline_snapshot.xlsx',columns=columns,headers=headers)
                return Response({'request_status': 1, 'msg': 'Success', 'url': url})
            else:
                return Response({'request_status': 0, 'msg': 'Data Not Found'})

        else:
            response_dict = response_on_off_modified(response)
            total_value = CrmOpportunity.cmobjects.filter(Q(lead__created_by=login_user) |
                Q(lead__assign_to=login_user),status=0).annotate(
                converted_value=F('value')*F('conversion_rate_to_inr')).aggregate(
                sum=Sum('converted_value')).get('sum')
            total_value = round(total_value, 2) if total_value else 0
            response_dict['total_value'] = realtime_exchange_value(from_currency='INR', to_currency=DEFAULT_CURRENCY, value=total_value)
            response_dict['default_currency'] = DEFAULT_CURRENCY
            return Response(response_dict)


class CrmOpportunityListGroupByStageView(ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmOpportunity.cmobjects.filter(status=0, is_project_form_open=False)
    serializer_class = serializers.CrmOpportunityListGroupByStageSerializer

    def get_queryset(self):
        login_user = self.request.query_params.get('login_user')
        assigned_users = self.request.query_params.get('assigned_users')
        assigned_users = assigned_users.split(',') if assigned_users else get_users_by_type(type='Prospecting Team Member')

        filters = dict()
        query_by_user_type = get_query_by_user_type(login_user=login_user, assigned_users=assigned_users,
                                                    table_type='opportunity')

        return self.queryset.filter(query_by_user_type, **filters)

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        login_user = self.request.query_params.get('login_user')
        user_type = get_user_type(user=login_user)
        opportunity_list = list()
        count = 0
        for stage, stage_name in CrmOpportunity.STAGE_CHOICE:
            if user_type == 2 and stage == 1:
                continue
            opportunity_dict = dict()
            opportunity_list_by_stage = list(filter(lambda x: x['stage'] == stage, response.data))
            if user_type == 2 and stage == 2:
                opportunity_list_by_stage = sorted(opportunity_list_by_stage, key=lambda x: x['turnaround_time_of_assessment'], reverse=False)

            if user_type == 2 and stage == 5:
                opportunity_list_by_stage = sorted(opportunity_list_by_stage, key=lambda x: x['turnaround_time_of_agreement'], reverse=False)

            opportunity_dict['opportunity'] = opportunity_list_by_stage
            opportunity_dict['count'] = len(opportunity_list_by_stage)
            count = count + len(opportunity_list_by_stage)
            opportunity_dict['stage_name'] = 'Assessment Request' if user_type == 2 and stage == 2 else stage_name
            opportunity_dict['stage'] = stage
            total_value = sum([float(dict(obj)['value'])*float(dict(obj)['conversion_rate_to_inr']) for obj in opportunity_dict['opportunity']])
            opportunity_dict['value'] = realtime_exchange_value(from_currency='INR', to_currency=DEFAULT_CURRENCY, value=total_value)
            opportunity_dict['default_currency'] = DEFAULT_CURRENCY
            opportunity_list.append(opportunity_dict)
        response.data = opportunity_list
        response_dict = response_on_off_modified(response)
        response_dict['count'] = count
        return Response(response_dict)


class CrmCheckIfProjectFormOpenView(ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmOpportunity.cmobjects.filter(status=0,is_project_form_open=True)
    serializer_class = serializers.CrmCheckIfProjectFormOpenSerializer

    def get_queryset(self):
        login_user = self.request.query_params.get('login_user')
        assigned_users = self.request.query_params.get('assigned_users')
        assigned_users = assigned_users.split(',') if assigned_users else get_users_by_type(
            type='Prospecting Team Member')

        filters = dict()


        query_by_user_type = get_query_by_user_type(login_user=login_user, assigned_users=assigned_users,
                                                    table_type='opportunity')

        return self.queryset.filter(query_by_user_type, project_form_opened_by=login_user, **filters).order_by('-id')

    @response_with_status_get
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CrmUserListByTypeView(ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmUserTypeMap.cmobjects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user__id', 'type']
    serializer_class = serializers.CrmUserListByTypeSerializer

    def get_queryset(self):
        return self.queryset.order_by('-id')

    @response_with_status_get
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CrmUserListByRoleModuleView(ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TMasterModuleRoleUser.objects.filter(mmr_type=3, mmr_module__cm_url='sft-crm', mmr_is_deleted=False)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['mmr_role__cr_name']
    serializer_class = serializers.CrmUserListByRoleModuleSerializer

    def get_queryset(self):
        return self.queryset.order_by('-id')

    @response_with_status_get
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CrmUsersUnderReportingHeadView(ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = User.objects.filter(is_superuser=False, is_active=True)
    serializer_class = serializers.CrmUsersUnderReportingHeadSerializer

    def get_queryset(self):
        user = self.request.query_params.get('user', None)
        reporting_heads = list(
            TCoreUserDetail.objects.filter(reporting_head=user, cu_is_deleted=False, cu_user__isnull=False).values_list(
                'cu_user__id', flat=True))
        temp_reporting_heads = list(
            UserTempReportingHeadMap.objects.filter(temp_reporting_head=user, is_deleted=False).values_list('user__id',
                                                                                                            flat=True))
        reporting_heads.extend(temp_reporting_heads)
        return self.queryset.filter(pk__in=reporting_heads)

    @response_modify_decorator_get_after_execution
    def get(self, request, *args, **kwargs):
        return super(__class__, self).get(self, request, *args, **kwargs)


class CrmOpportunityPresaleUpdateView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmOpportunity.cmobjects.all()
    serializer_class = serializers.CrmOpportunityPresaleUpdateSerializer

    @response_modify_decorator_update
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class CrmOpportunityProposalUpdateView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmOpportunity.cmobjects.all()
    serializer_class = serializers.CrmOpportunityProposalUpdateSerializer

    @response_modify_decorator_update
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class CrmOpportunityAgreementUploadView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmOpportunity.cmobjects.all()
    serializer_class = serializers.CrmOpportunityAgreementUploadSerializer

    @response_modify_decorator_update
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class CrmOpportunityUpdateView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmOpportunity.cmobjects.all()
    serializer_class = serializers.CrmOpportunityUpdateSerializer

    @response_modify_decorator_update
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class CrmOpportunityBAUpdateView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmOpportunity.cmobjects.all()
    serializer_class = serializers.CrmOpportunityBAUpdateSerializer

    @response_modify_decorator_update
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class CrmOpportunityHourConsumeUpdateView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmOpportunity.cmobjects.all()
    serializer_class = serializers.CrmOpportunityHourConsumeUpdateSerializer

    @response_modify_decorator_update
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class CrmOpportunityDocumentDeleteRetrieveView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmOpportunityDocumentTag.cmobjects.all()
    serializer_class = serializers.CrmOpportunityDocumentDeleteRetrieveSerializer

    @response_modify_decorator_update
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class CrmRequestCreateView(CreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmRequestHandler.cmobjects.all()
    serializer_class = serializers.CrmRequestCreateSerializer

    @response_modify_decorator_update
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


class CrmRequestAcceptView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmRequestHandler.cmobjects.all()
    serializer_class = serializers.CrmRequestAcceptSerializer

    @response_modify_decorator_update
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class CrmRequestCompleteView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmRequestHandler.cmobjects.all()
    serializer_class = serializers.CrmRequestCompleteSerializer

    @response_modify_decorator_update
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class CrmOpportunityColorStatusUpdateView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmOpportunity.cmobjects.all()
    serializer_class = serializers.CrmOpportunityColorStatusUpdateSerializer

    @response_modify_decorator_update
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class CrmOpportunityTagUpdateView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmOpportunity.cmobjects.all()
    serializer_class = serializers.CrmOpportunityTagUpdateSerializer

    @response_modify_decorator_update
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class CrmOpportunityFileUploadView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]
    authentication_classes = [TokenAuthentication]
    queryset = CrmOpportunity.cmobjects.all()
    serializer_class = serializers.CrmOpportunityFileUploadSerializer

    @response_modify_decorator_update
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class CrmOpportunityStageStatusUpdateView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmOpportunity.cmobjects.all()
    serializer_class = serializers.CrmOpportunityStageStatusUpdateSerializer

    @response_modify_decorator_update
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class CrmProjectFormOpenOrCancelView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmOpportunity.cmobjects.all()
    serializer_class = serializers.CrmProjectFormOpenOrCancelSerializer

    @response_modify_decorator_update
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class CrmAddTaskToOpportunityView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmOpportunity.cmobjects.all()
    serializer_class = serializers.CrmAddTaskToOpportunitySerializer

    @response_modify_decorator_update
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class CrmProjectCreateView(CreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    # parser_classes = [MultiPartParser]
    queryset = CrmProject.cmobjects.all()
    serializer_class = serializers.CrmProjectCreateSerializer

    @response_modify_decorator_update
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


class CrmAccountListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = CrmAccountFilter
    filterset_fields = ['id', 'crm_opp_lead__status', 'crm_opp_lead__department', 'crm_opp_lead__color_status',
                        'crm_opp_lead__business_analyst', 'crm_opp_lead__account_manager']
    search_fields = ['business_name']
    queryset = CrmLead.cmobjects.filter(crm_opp_lead__isnull=False).distinct()
    serializer_class = serializers.CrmAccountListSerializer
    pagination_class = CSPageNumberPagination

    def get_serializer_context(self):
        login_user = self.request.query_params.get('login_user', self.request.user)
        return {
            'request': self.request,
            'login_user': login_user,
            'crm_opp_lead__status': self.request.query_params.get('crm_opp_lead__status', None),
            'crm_opp_lead__department': self.request.query_params.get('crm_opp_lead__department', None),
            'crm_opp_lead__color_status': self.request.query_params.get('crm_opp_lead__color_status', None),
            'crm_opp_lead__business_analyst': self.request.query_params.get('crm_opp_lead__business_analyst', None),
            'crm_opp_lead__account_manager': self.request.query_params.get('crm_opp_lead__account_manager', None)
        }

    def get_queryset(self):
        login_user = self.request.query_params.get('login_user', self.request.user)
        assigned_users = self.request.query_params.get('assigned_users')

        assigned_users = assigned_users.split(',') if assigned_users else get_users_by_type(
            type='Prospecting Team Member')

        filters = dict()

        query_by_user_type = get_query_by_user_type(login_user=login_user, assigned_users=assigned_users,
                                                    table_type='lead')

        return self.queryset.filter(query_by_user_type, **filters)

    @response_modify_decorator_list_or_get_after_execution_for_pagination
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CrmAddPocToOpportunityView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmOpportunity.cmobjects.all()
    serializer_class = serializers.CrmAddPocToOpportunitySerializer

    @response_modify_decorator_update
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class CrmAddMilestoneToOpportunityView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmOpportunity.cmobjects.all()
    serializer_class = serializers.CrmAddMilestoneToOpportunitySerializer

    @response_modify_decorator_update
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class CrmUpdateMilestoneInOpportunityView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmOpportunity.cmobjects.all()
    serializer_class = serializers.CrmUpdateMilestoneInOpportunitySerializer

    @response_modify_decorator_update
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class CrmDeleteMilestoneFromOpportunityView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmOpportunity.cmobjects.all()
    serializer_class = serializers.CrmDeleteMilestoneFromOpportunitySerializer

    @response_modify_decorator_update
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class CrmAddChangeRequestToOpportunityView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmOpportunity.cmobjects.all()
    serializer_class = serializers.CrmAddChangeRequestToOpportunitySerializer

    @response_modify_decorator_update
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class CrmUpdateChangeRequestInOpportunityView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmOpportunity.cmobjects.all()
    serializer_class = serializers.CrmUpdateChangeRequestInOpportunitySerializer

    @response_modify_decorator_update
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class CrmChangeRequestDetailsOpportunityWiseView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmChangeRequest.cmobjects.all()
    serializer_class = serializers.CrmChangeRequestDetailsOpportunityWiseSerializer

    def get_serializer_context(self):
        return {
            'opportunity': self.request.query_params.get('opportunity', 0),
            'request':self.request
        }

    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CrmOpportunityDetailsView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmOpportunity.cmobjects.all()
    serializer_class = serializers.CrmOpportunityDetailsSerializer

    def get_serializer_context(self):
        return {
            'request':self.request
        }

    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CrmOpportunityPocUpdatePrimaryView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmOpportunity.cmobjects.all()
    serializer_class = serializers.CrmOpportunityPocUpdatePrimarySerializer

    @response_modify_decorator_update
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)


class CrmCloseWonListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = CrmCloseWonFilter
    filterset_fields = ['lead__poc__source', 'country', 'territory', 'business_analyst', 'project_lead', 'status_updated_by']
    ordering_fields = ['business_name', 'status_update_at', 'created_at', 'value', 'opportunity_name',
                       'opportunity_date', 'expected_closer_date']
    ordering = ['-status_update_at']
    queryset = CrmOpportunity.cmobjects.filter(status=1)
    serializer_class = serializers.CrmCloseWonListSerializer
    pagination_class = OnOffPagination

    def get_queryset(self):
        login_user = self.request.query_params.get('login_user')
        assigned_users = self.request.query_params.get('assigned_users')
        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')
        year = self.request.query_params.get('year')

        assigned_users = assigned_users.split(',') if assigned_users else get_users_by_type(
            type='Prospecting Team Member')

        filters = dict()
        if from_date and to_date:
            filters['status_update_at__date__gte'] = from_date
            filters['status_update_at__date__lte'] = to_date

        if year:
            filters['status_update_at__date__year'] = year

        query_by_user_type = get_query_by_user_type(login_user=login_user, assigned_users=assigned_users,
                                                    table_type='opportunity')

        return self.queryset.filter(query_by_user_type, **filters)

    def get_serializer_context(self):
        return {
            'login_user': self.request.query_params.get('login_user', None),
            'assigned_users': self.request.query_params.get('assigned_users', '')
        }

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        login_user = self.request.query_params.get('login_user')

        is_download = self.request.query_params.get('is_download')
        extension_type = self.request.query_params.get('extension_type')

        assigned_users = self.request.query_params.get('assigned_users')
        assigned_users = assigned_users.split(',') if assigned_users else get_users_by_type(
            type='Prospecting Team Member')

        if is_download == 'yes':
            if len(response.data):
                column_header = collections.OrderedDict()
                column_header['business_name'] = 'Business Name'
                column_header['opportunity_name'] = 'Opportunity Name'
                column_header['opp_date'] = 'Opportunity Date'
                column_header['value'] = 'Deal Value'
                column_header['territory_name'] = 'Territory'
                column_header['won_date'] = 'Closer Date'
                column_header['country_name'] = 'Country'
                column_header['source_name'] = 'Source'
                column_header['status_updated_by_name'] = 'Closed By'
                column_header['business_analyst_name'] = 'Business Analyst'
                column_header['project_lead_name'] = 'Project Manager'

                columns = list(column_header.keys())
                headers = list(column_header.values())
                file_name = 'close_won.{}'.format(extension_type)
                url = download_url_generator(request, data=response.data,base_path='media/crm',
                                extension_type=extension_type,file_name=file_name,columns=columns,headers=headers)
                return Response({'request_status': 1, 'msg': 'Success', 'url': url})
            else:
                return Response({'request_status': 0, 'msg': 'Data Not Found'})
        else:
            response_dict = response_on_off_modified(response)
            query_by_user_type_opp = get_query_by_user_type(login_user=login_user, assigned_users=assigned_users,
                                                            table_type='opportunity')
            query_by_user_type_lead = get_query_by_user_type(login_user=login_user, assigned_users=assigned_users,
                                                             table_type='lead')

            response_dict['active_opportunities'] = CrmOpportunity.cmobjects.filter(query_by_user_type_opp,status=0).count()
            response_dict['active_leads'] = CrmLead.cmobjects.filter(~Q(Q(status=5)|Q(status=6)),query_by_user_type_lead).count()
            total_value = CrmOpportunity.cmobjects.filter(query_by_user_type_opp,status=1).annotate(
                            converted_value=F('value')*F('conversion_rate_to_inr')).aggregate(
                            sum=Sum('converted_value')).get('sum')
            total_value = round(total_value, 2) if total_value else 0
            response_dict['total_value'] = realtime_exchange_value(from_currency='INR', to_currency=DEFAULT_CURRENCY, value=total_value)
            response_dict['default_currency'] = DEFAULT_CURRENCY
            return Response(response_dict)


class CrmLossAnalysisListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = CrmLossAnalysisFilter
    filterset_fields = ['lead__poc__source', 'country', 'territory', 'business_analyst', 'project_lead', 'status_updated_by']
    ordering_fields = ['business_name', 'status_update_at', 'created_at', 'value', 'opportunity_name',
                       'opportunity_date', 'expected_closer_date']
    ordering = ['-status_update_at']
    queryset = CrmOpportunity.cmobjects.filter(status=2)
    serializer_class = serializers.CrmLossAnalysisListSerializer
    pagination_class = OnOffPagination

    def get_queryset(self):
        login_user = self.request.query_params.get('login_user')
        assigned_users = self.request.query_params.get('assigned_users')
        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')
        year = self.request.query_params.get('year')

        assigned_users = assigned_users.split(',') if assigned_users else get_users_by_type(
            type='Prospecting Team Member')


        filters = dict()
        if from_date and to_date:
            filters['status_update_at__date__gte'] = from_date
            filters['status_update_at__date__lte'] = to_date

        if year:
            filters['status_update_at__date__year'] = year

        query_by_user_type = get_query_by_user_type(login_user=login_user, assigned_users=assigned_users,
                                                    table_type='opportunity')

        return self.queryset.filter(query_by_user_type, **filters)

    def get_serializer_context(self):
        return {
            'login_user': self.request.query_params.get('login_user', None),
            'assigned_users': self.request.query_params.get('assigned_users', None)
        }

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        login_user = self.request.query_params.get('login_user')

        is_download = self.request.query_params.get('is_download')
        extension_type = self.request.query_params.get('extension_type')

        assigned_users = self.request.query_params.get('assigned_users')
        assigned_users = assigned_users.split(',') if assigned_users else get_users_by_type(
            type='Prospecting Team Member')

        if is_download == 'yes':
            if len(response.data):
                column_header = collections.OrderedDict()
                column_header['business_name'] = 'Business Name'
                column_header['opportunity_name'] = 'Opportunity Name'
                column_header['opp_date'] = 'Opportunity Date'
                column_header['value'] = 'Deal Value'
                column_header['territory_name'] = 'Territory'
                column_header['won_date'] = 'Deal Lost Date'
                column_header['country_name'] = 'Country'
                column_header['source_name'] = 'Source'
                column_header['status_updated_by_name'] = 'Closed By'
                column_header['business_analyst_name'] = 'Business Analyst'
                column_header['project_lead_name'] = 'Project Manager'

                columns = list(column_header.keys())
                headers = list(column_header.values())
                file_name = 'loss_analysis.{}'.format(extension_type)
                url = download_url_generator(request, data=response.data,base_path='media/crm',
                                extension_type=extension_type,file_name=file_name,columns=columns,headers=headers)
                return Response({'request_status': 1, 'msg': 'Success', 'url': url})
            else:
                return Response({'request_status': 0, 'msg': 'Data Not Found'})
        else:

            response_dict = response_on_off_modified(response)
            query_by_user_type_opp = get_query_by_user_type(login_user=login_user, assigned_users=assigned_users,
                                                        table_type='opportunity')
            query_by_user_type_lead = get_query_by_user_type(login_user=login_user, assigned_users=assigned_users,
                                                            table_type='lead')

            response_dict['active_opportunities'] = CrmOpportunity.cmobjects.filter(query_by_user_type_opp,status=0).count()
            response_dict['active_leads'] = CrmLead.cmobjects.filter(~Q(Q(status=5)|Q(status=6)),query_by_user_type_lead).count()
            total_value = CrmOpportunity.cmobjects.filter(query_by_user_type_opp,status=2).annotate(
                                converted_value=F('value')*F('conversion_rate_to_inr')).aggregate(
                                sum=Sum('converted_value')).get('sum')
            total_value = round(total_value, 2) if total_value else 0
            response_dict['total_value'] = realtime_exchange_value(from_currency='INR', to_currency=DEFAULT_CURRENCY, value=total_value)
            response_dict['default_currency'] = DEFAULT_CURRENCY
            return Response(response_dict)


class CrmAccountLeadFilterListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = CrmLead.cmobjects.filter(crm_opp_lead__isnull=False).distinct()
    serializer_class = serializers.CrmAccountLeadFilterListSerializer

    def get_queryset(self):
        return self.queryset.order_by('-id')

    @response_with_status_get
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CrmUserFilterListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = User.objects.all()
    serializer_class = serializers.CrmUserSerializer

    def get_queryset(self):
        list_for = self.request.query_params.get('list_for', None)
        login_user = self.request.query_params.get('login_user')
        assigned_users = self.request.query_params.get('assigned_users')
        assigned_users = assigned_users.split(',') if assigned_users else get_users_by_type(
            type='Prospecting Team Member')

        query_by_user_type_opp = get_query_by_user_type(login_user=login_user, assigned_users=assigned_users,
                                                    table_type='opportunity')
        query_by_user_type_lead = get_query_by_user_type(login_user=login_user, assigned_users=assigned_users,
                                                        table_type='lead')


        user_list = list()
        if list_for == 'close_won_status_updated_by' or list_for == 'loss_analysis_status_updated_by':
            query_set = CrmOpportunity.cmobjects.filter(query_by_user_type_opp)
            if list_for == 'close_won_status_updated_by':
                user_list = list(query_set.filter(status=1).values_list('status_updated_by_id', flat=True))
            elif list_for == 'loss_analysis_status_updated_by':
                user_list = list(query_set.filter(status=2).values_list('status_updated_by_id', flat=True))

        return self.queryset.filter(pk__in=user_list)

    @response_with_status_get
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CrmLeadReportListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = CrmLeadReportFilter
    filterset_fields = ['poc__source', 'poc__country']
    search_fields = ['business_name', 'poc__first_name', 'poc__last_name', 'poc__country__name', 'poc__source__name']
    ordering_fields = ['business_name', 'poc__country__name', 'poc__source__name', 'created_at']
    ordering = ['-id']
    queryset = CrmLead.cmobjects.all()
    serializer_class = serializers.CrmLeadReportListSerializer
    pagination_class = OnOffPagination

    def get_queryset(self):
        login_user = self.request.query_params.get('login_user')
        assigned_users = self.request.query_params.get('assigned_users')
        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')

        assigned_users = assigned_users.split(',') if assigned_users else get_users_by_type(
            type='Prospecting Team Member')

        query_by_user_type_opp = get_query_by_user_type(login_user=login_user, assigned_users=assigned_users,
                                                    table_type='lead')

        query_set = self.queryset.filter(~Q(Q(status=5)|Q(status=6))).filter(query_by_user_type_opp)

        filters = dict()
        if from_date and to_date:
            filters['created_at__date__gte'] = from_date
            filters['created_at__date__lte'] = to_date

        return query_set.filter(**filters)

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        is_download = self.request.query_params.get('is_download')
        extension_type = self.request.query_params.get('extension_type')

        if is_download == 'yes':
            if len(response.data):
                column_header = collections.OrderedDict()
                column_header['lead_date'] = 'Lead Creation Date'
                column_header['business_name'] = 'Lead Name'
                column_header['source_name'] = 'Source'
                column_header['country_name'] = 'Country'
                column_header['prospecting_member_name'] = 'Prospecting'

                columns = list(column_header.keys())
                headers = list(column_header.values())
                file_name = 'lead_report.{}'.format(extension_type)
                url = download_url_generator(request, data=response.data,base_path='media/crm',
                                extension_type=extension_type,file_name=file_name,columns=columns,headers=headers)
                return Response({'request_status': 1, 'msg': 'Success', 'url': url})
            else:
                return Response({'request_status': 0, 'msg': 'Data Not Found'})

        else:
            response_dict = response_on_off_modified(response)
            return Response(response_dict)


class CrmCustomerReportListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering_fields = ['lead__business_name']
    search_fields = ['lead__business_name']
    ordering = ['-id']
    queryset = CrmOpportunity.cmobjects.filter(~Q(status=2))
    serializer_class = serializers.CrmCustomerReportListSerializer
    pagination_class = OnOffPagination

    def get_queryset(self):
        login_user = self.request.query_params.get('login_user')
        assigned_users = self.request.query_params.get('assigned_users')

        filters = dict()
        assigned_users = assigned_users.split(',') if assigned_users else get_users_by_type(
            type='Prospecting Team Member')

        query_by_user_type_opp = get_query_by_user_type(login_user=login_user, assigned_users=assigned_users,
                                                    table_type='opportunity')

        query_set = self.queryset.filter(query_by_user_type_opp)

        return query_set.filter(**filters).order_by('-id')

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        is_download = self.request.query_params.get('is_download')
        extension_type = self.request.query_params.get('extension_type')

        if is_download == 'yes':
            if len(response.data):
                column_header = collections.OrderedDict()
                column_header['business_name'] = 'Account Name'
                column_header['account_manager_name'] = 'Account Manager'
                column_header['active_opportunities'] = 'Active opportunities'
                column_header['total_opportunities_value'] = 'Total opportunity value'
                column_header['won_value'] = 'Won value'
                column_header['won_opportunities'] = 'Won opportunities'
                column_header['invoiced_amount'] = 'Total Invoiced Amount'
                column_header['realized_amount'] = 'Amount Realized'
                column_header['due_amount'] = 'Amount due'
                column_header['latest_color_remarks'] = 'Remarks'

                columns = list(column_header.keys())
                headers = list(column_header.values())
                file_name = 'customer_report.{}'.format(extension_type)
                url = download_url_generator(request, data=response.data,base_path='media/crm',
                                    extension_type=extension_type,file_name=file_name,columns=columns,headers=headers)
                return Response({'request_status': 1, 'msg': 'Success', 'url': url})
            else:
                return Response({'request_status': 0, 'msg': 'Data Not Found'})

        else:
            response_dict = response_on_off_modified(response)
            return Response(response_dict)


class CrmInvoiceReportListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = CrmInvoiceReportFilter
    filterset_fields = ['milestone__is_paid']
    search_fields = ['opportunity__lead__business_name']
    queryset = CrmOpportunityMilestoneMap.cmobjects.all()
    serializer_class = serializers.CrmInvoiceReportListSerializer
    pagination_class = OnOffPagination

    def get_queryset(self):
        login_user = self.request.query_params.get('login_user')
        assigned_users = self.request.query_params.get('assigned_users')
        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')
        assigned_users = assigned_users.split(',') if assigned_users else get_users_by_type(
            type='Prospecting Team Member')

        query_by_user_type_opp = get_query_by_user_type(login_user=login_user, assigned_users=assigned_users,
                                                    table_type='opportunity')


        filters = dict()
        if from_date and to_date:
            filters['milestone__due_date__date__gte'] = from_date
            filters['milestone__due_date__date__lte'] = to_date

        # query_set = CrmOpportunityMilestoneMap.cmobjects.none()
        opportunity_list = list(CrmOpportunity.cmobjects.filter(query_by_user_type_opp).values_list('id', flat=True))
        query_set = self.queryset.filter(opportunity__in=opportunity_list)

        return query_set.filter(**filters).order_by('-id')

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        is_download = self.request.query_params.get('is_download')
        extension_type = self.request.query_params.get('extension_type')

        if is_download == 'yes':
            if len(response.data):
                column_header = collections.OrderedDict()
                column_header['business_name'] = 'Account Name'
                column_header['project_name'] = 'Project'
                column_header['invoice_status'] = 'Invoice status'
                column_header['invoice_date'] = 'Invoice date'
                column_header['total_amount'] = 'Total amount'
                column_header['invoice_no'] = 'Invoice no'
                column_header['is_paid'] = 'Payment Received'
                column_header['transaction_id'] = 'Transaction id'
                column_header['mode_of_payment_name'] = 'Mode of Payment'
                column_header['due_date'] = 'Due Date'

                columns = list(column_header.keys())
                headers = list(column_header.values())
                file_name = 'invoice_report.{}'.format(extension_type)
                url = download_url_generator(request, data=response.data,base_path='media/crm',
                                    extension_type=extension_type,file_name=file_name,columns=columns,headers=headers)
                return Response({'request_status': 1, 'msg': 'Success', 'url': url})
            else:
                return Response({'request_status': 0, 'msg': 'Data Not Found'})

        else:
            response_dict = response_on_off_modified(response)
            return Response(response_dict)


class CrmProjectReportListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = CrmProjectReportFilter
    filterset_fields = ['lead', 'project_lead', 'color_status']
    ordering_fields = ['business_name']
    search_fields = ['business_name']
    ordering = ['-id']
    queryset = CrmOpportunity.cmobjects.filter(~Q(status=2))
    serializer_class = serializers.CrmProjectReportListSerializer
    pagination_class = OnOffPagination

    def get_queryset(self):
        login_user = self.request.query_params.get('login_user')
        assigned_users = self.request.query_params.get('assigned_users')

        assigned_users = assigned_users.split(',') if assigned_users else get_users_by_type(
            type='Prospecting Team Member')

        query_by_user_type_opp = get_query_by_user_type(login_user=login_user, assigned_users=assigned_users,
                                                    table_type='opportunity')

        filters = dict()

        query_set = self.queryset.filter(query_by_user_type_opp)

        return query_set.filter(**filters).order_by('-id')

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        is_download = self.request.query_params.get('is_download')
        extension_type = self.request.query_params.get('extension_type')

        if is_download == 'yes':
            if len(response.data):
                column_header = collections.OrderedDict()
                column_header['business_name'] = 'Account Name'
                column_header['opportunity_name'] = 'Project Name'
                column_header['project_lead_name'] = 'Project Manager'
                column_header['resource_timeline'] = 'Timeline'
                column_header['total_effort'] = 'Total Effort'
                column_header['resource_hour_consumed'] = 'Hours Consumed'
                column_header['complete_percentage'] = 'Complete Percentage'
                column_header['total_amount'] = 'Project Value'
                column_header['realized_amount'] = 'Realized'
                column_header['due_amount'] = 'Due'
                column_header['collection_percentage'] = 'Collection Percentage'
                column_header['status_name'] = 'Project Status'
                column_header['color_status_name'] = 'RAG Status'
                column_header['account_manager_name'] = 'Deal POC'
                column_header['latest_color_remarks'] = 'Remarks'

                columns = list(column_header.keys())
                headers = list(column_header.values())
                file_name = 'project_report.{}'.format(extension_type)
                url = download_url_generator(request, data=response.data, base_path='media/crm',
                                extension_type=extension_type, file_name=file_name, columns=columns, headers=headers)
                return Response({'request_status': 1, 'msg': 'Success', 'url': url})
            else:
                return Response({'request_status': 0, 'msg': 'Data Not Found'})

        else:
            response_dict = response_on_off_modified(response)
            return Response(response_dict)

