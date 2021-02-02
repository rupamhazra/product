from django.shortcuts import render
from rest_framework import generics
from eticket.serializers import *
from rest_framework.response import Response
from rest_framework import filters
from rest_framework.permissions import IsAuthenticated, IsAdminUser, IsAuthenticatedOrReadOnly
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings
from pagination import CSLimitOffestpagination, CSPageNumberPagination,OnOffPagination
from django_filters.rest_framework import DjangoFilterBackend
from master.models import TMasterOtherRole, TMasterModuleRoleUser
import collections
from rest_framework import mixins
from custom_decorator import *
from rest_framework.views import APIView
from django.db.models import When, Case, Value, CharField, IntegerField, F, Q
import datetime
from users.serializers import UserSerializer
'''
    For Knox 
    Author : Rupam Hazra
    Date : 16.03.2020
'''
from knox.auth import TokenAuthentication
from rest_framework import permissions
from knox.models import AuthToken

class ETICKETUserDetailsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = User.objects
    serializer_class = ETicketUserSerializer
    pagination_class = None

    def get_queryset(self,*args,**kwargs):
        user = self.request.user
        self.queryset = self.queryset.filter(pk=user.id)
        return self.queryset

class ETICKETModuleMasterAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = ETICKETModuleMaster.objects.filter(is_deleted=False)
    serializer_class = ETICKETModuleMasterAddSerializer
    pagination_class = OnOffPagination
    filter_backends = [filters.OrderingFilter]
    
    def get_queryset(self,*args,**kwargs):
        dept = self.request.query_params.get('dept', None)
        if dept:
            dept_ids = TCoreDepartment.objects.filter(cd_parent_id=dept).values_list('id', flat=True)
            if dept_ids:
                dept_ids = list(dept_ids)
            else:
                dept_ids = []
            dept_ids.append(dept)
            self.queryset = self.queryset.filter(department_id__in=dept_ids)        

        return self.queryset.all()

class ETICKETModuleMasterEditView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = ETICKETModuleMaster.objects.filter(is_deleted=False)
    serializer_class = ETICKETModuleMasterAddSerializer

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save()

class EticketReportingHeadAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    pagination_class =OnOffPagination
    queryset = ETICKETReportingHead.objects.filter(is_deleted=False)
    serializer_class = EticketReportingHeadAddSerializer
    filter_backends = [filters.OrderingFilter]

    def get_queryset(self):
        id = self.request.query_params.get('id',None)
        dept = self.request.query_params.get('dept', None)
        module = self.request.query_params.get('module', None)
        ordering = self.request.query_params.get('ordering', None)
        if ordering is None:
            ordering = '-id'
        if id:
            self.queryset = self.queryset.filter(id = id)
        else:
            self.queryset = self.queryset.order_by(ordering)         
            if dept:
                dept_ids = TCoreDepartment.objects.filter(cd_parent_id=dept).values_list('id', flat=True)
                if dept_ids:
                    dept_ids = list(dept_ids)
                else:
                    dept_ids = []
                dept_ids.append(dept)
                self.queryset = self.queryset.filter(department_id__in=dept_ids)        
            if module:
                self.queryset = self.queryset.filter(module_id=module)

        return self.queryset

class EticketReportingHeadEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = ETICKETReportingHead.objects.filter(is_deleted=False)
    serializer_class = EticketReportingHeadAddSerializer

class EticketTicketSubjectListByDepartmentAddView(generics.ListCreateAPIView, mixins.UpdateModelMixin):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = ETICKETSubjectOfDepartment.objects.filter(is_deleted=False)
    pagination_class = OnOffPagination
    serializer_class = EticketTicketSubjectListByDepartmentAddSerializer
    filter_backends = (filters.SearchFilter,)

    def get_queryset(self):
        id = self.request.query_params.get('id',None)
        dept = self.request.query_params.get('dept', None)
        module = self.request.query_params.get('module', None)
        ordering = self.request.query_params.get('ordering', None)
        if ordering is None:
            ordering = '-id'
        
        if id:
            self.queryset = self.queryset.filter(id = id)
        else:
            self.queryset = self.queryset.order_by(ordering)         
            if dept:
                dept_ids = TCoreDepartment.objects.filter(cd_parent_id=dept).values_list('id', flat=True)
                if dept_ids:
                    dept_ids = list(dept_ids)
                else:
                    dept_ids = []
                dept_ids.append(dept)
                self.queryset = self.queryset.filter(department_id__in=dept_ids)            
            if module:
                self.queryset = self.queryset.filter(module_id=module)

        return self.queryset

class EticketTicketSubjectListByDepartmentEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = ETICKETSubjectOfDepartment.objects.filter(is_deleted=False)
    serializer_class = EticketTicketSubjectListByDepartmentAddSerializer

class EticketTicketDocumentAddView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = ETICKETTicketDoc.objects.filter(is_deleted=False)
    serializer_class = EticketTicketDocumentAddSerializer

class EticketTicketCommentAddView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = ETICKETTicketComment.objects.filter(is_deleted=False)
    serializer_class = EticketTicketCommentAddSerializer

class EticketTicketListByStatusView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    pagination_class = OnOffPagination
    queryset = ETICKETTicket.objects.filter(is_deleted=False)
    serializer_class = EticketTicketRaisedByMeListSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = '__all__'

    def get_queryset(self):
        qset = self.queryset
        status_details = self.kwargs
        
        # filter by department, module or subject
        dept = self.request.query_params.get('dept', None)
        module = self.request.query_params.get('module', None)
        subject = self.request.query_params.get('subject', None)
        ordering = self.request.query_params.get('ordering', None)
        if ordering is None:
            ordering = '-updated_at'
        if subject is not None:
            subject = int(subject)
            qset = qset.filter(subject_id=subject)
        elif module is not None:
            module = int(module)
            qset = qset.filter(module_id=module)
        elif dept is not None:
            dept = int(dept)
            child_depts = TCoreDepartment.objects.filter(Q(cd_parent_id=dept))
            cd_child_ids = child_depts.values_list('id', flat=True)
            all_dept_ids = [dept]
            if cd_child_ids:
                all_dept_ids.extend(list(cd_child_ids))
            qset = qset.filter(department_id__in=all_dept_ids)

        # filter by priority
        priority = self.request.query_params.get('priority', None)
        if priority is not None:
            qset = qset.filter(priority=priority)
        
        # filter by datetime
        fromdt_str = self.request.query_params.get('fromdate', None)
        todt_str = self.request.query_params.get('todate', None)
        if fromdt_str is not None and todt_str is not None:
            from_date = datetime.datetime.strptime(fromdt_str, '%Y-%m-%d')
            to_date = datetime.datetime.strptime(todt_str, '%Y-%m-%d')
            to_date = to_date.replace(hour=23, minute=59, second=59)
            qset = qset.filter(created_at__gte=from_date, created_at__lte=to_date)

        if status_details['status'].lower() == 're-open':
            qset = qset.filter(ticket_closed_date__isnull=False,status='Open')
        elif status_details['status'].lower() == 'open':
            qset = qset.filter(ticket_closed_date__isnull=True,status=status_details['status'])
        else:
            qset = qset.filter(status=status_details['status'])
        
        qset = qset.order_by(ordering)
        return qset

class EticketTicketSubjectListByDepartmentView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    pagination_class = OnOffPagination
    queryset = ETICKETSubjectOfDepartment.objects.filter(is_deleted=False)
    serializer_class = EticketTicketSubjectListByDepartmentSerializer

    def get_queryset(self):
        department_id = self.kwargs['department_id']
        return self.queryset.filter(department_id=department_id)

# region - added / updated by Shubhadeep

class EticketTicketAddView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = ETICKETTicket.objects.filter(is_deleted=False)
    serializer_class = EticketTicketAddSerializer
    filter_backends = (filters.SearchFilter,)

    @response_modify_decorator_post
    def post(self, request, *args, **kwargs):
        response = super().post(request,*args,**kwargs)
        return response

class EticketTicketEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = ETICKETTicket.objects.filter(is_deleted=False)
    serializer_class = EticketTicketEditSerializer

    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @response_modify_decorator_update
    def put(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        tic_obj = ETICKETTicket.objects.latest("id")
        tic_obj.assigned_to = None
        tic_obj.save()
        return response

class EticketTicketAssignedToMeListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    pagination_class = OnOffPagination
    queryset = ETICKETTicket.objects.filter(is_deleted=False)
    serializer_class = EticketTicketAssignedToMeListSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = '__all__'

    def get_queryset(self):
        current_user = self.request.user
        userid_by_filter = self.request.query_params.get('userId', None)
        is_dashboard = self.request.query_params.get('dashboard', False)
        ordering = self.request.query_params.get('ordering', None)
        if ordering is None:
            ordering = '-updated_at'
        if is_dashboard:
            tic_history_obj = ETICKETTicketAssignHistory.objects.filter(Q(assigned_to_id=current_user),
                                                                        current_status=True).values_list('ticket',
                                                                                                            flat=True)
            qset1, qset2 = self.queryset.filter(Q(id__in=tic_history_obj)), None
            reporting_head_details_1 = ETICKETReportingHead.objects.filter(reporting_head = current_user, module__isnull=True)
            reporting_head_details_2 = ETICKETReportingHead.objects.filter(reporting_head = current_user, module__isnull=False)
            if reporting_head_details_1:
                reporting_head_depts = reporting_head_details_1.values_list('department_id',flat=True)
                child_depts = TCoreDepartment.objects.filter(Q(cd_parent_id__in=reporting_head_depts))
                cd_child_ids = child_depts.values_list('id', flat=True)
                all_dept_ids = list(reporting_head_depts)
                if cd_child_ids:
                    all_dept_ids.extend(list(cd_child_ids))
                qset2 = self.queryset.filter(department_id__in=all_dept_ids)
            elif reporting_head_details_2:
                reporting_head_modules = reporting_head_details_2.values_list('module_id',flat=True)
                qset2 = self.queryset.filter(module_id__in=reporting_head_modules)
            if qset2:
                qset = qset1 | qset2
            else:
                qset = qset1
        else:
            user_ids = []
            if userid_by_filter:
                user_ids = [userid_by_filter]
            else:
                '''edited by Swarup Adhikary on 25.11.2020'''
                qset = get_user_list_under_user(current_user).values_list('id', flat=True)
                user_ids = list(qset) if len(qset) > 0 else []
            tic_history_obj = ETICKETTicketAssignHistory.objects.filter(Q(assigned_to_id__in=user_ids), current_status=True).values_list('ticket',flat=True)
            qset = self.queryset.filter(Q(id__in=tic_history_obj))
        
        # filter by department, module or subject
        dept = self.request.query_params.get('dept', None)
        module = self.request.query_params.get('module', None)
        subject = self.request.query_params.get('subject', None)
        if subject is not None:
            subject = int(subject)
            qset = qset.filter(subject_id=subject)
        elif module is not None:
            module = int(module)
            qset = qset.filter(module_id=module)
        elif dept is not None:
            dept = int(dept)
            child_depts = TCoreDepartment.objects.filter(Q(cd_parent_id=dept))
            cd_child_ids = child_depts.values_list('id', flat=True)
            all_dept_ids = [dept]
            if cd_child_ids:
                all_dept_ids.extend(list(cd_child_ids))
            qset = qset.filter(department_id__in=all_dept_ids)

        # filter by priority
        priority = self.request.query_params.get('priority', None)
        if priority is not None:
            qset = qset.filter(priority=priority)

        # filter by datetime
        fromdt_str = self.request.query_params.get('fromdate', None)
        todt_str = self.request.query_params.get('todate', None)
        if fromdt_str is not None and todt_str is not None:
            from_date = datetime.datetime.strptime(fromdt_str, '%Y-%m-%d')
            to_date = datetime.datetime.strptime(todt_str, '%Y-%m-%d')
            to_date = to_date.replace(hour=23, minute=59, second=59)
            qset = qset.filter(created_at__gte=from_date, created_at__lte=to_date)

        # filter by status
        status = self.request.query_params.get('status', None)
        if status is not None:
            if status == 'Re-open':
                qset = qset.filter(ticket_closed_date__isnull=False,status='Open')
            elif status == 'Open':
                qset = qset.filter(ticket_closed_date__isnull=True,status='Open')
            else:
                qset = qset.filter(status=status)
        
        qset = qset.order_by(ordering)
        return qset

# class EticketTicketChangePersonResponsibleView(generics.RetrieveUpdateAPIView):
#     permission_classes = [IsAuthenticated]
#     authentication_classes = [TokenAuthentication]
#     queryset = ETICKETTicket.objects.all()
#     serializer_class = EticketTicketChangePersonResponsibleSerializer

class EticketTicketChangeMassPersonResponsibleView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = ETICKETTicket.objects.all()
    serializer_class = EticketTicketChangeMassPersonResponsibleSerializer

class EticketTicketChangeStatusView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = ETICKETTicket.objects.all()
    serializer_class = EticketTicketChangeStatusSerializer

class EticketTicketChangeMassStatusView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = ETICKETTicket.objects.all()
    serializer_class = EticketTicketChangeMassStatusSerializer

class EticketTicketRaisedByMeListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    pagination_class = OnOffPagination
    queryset = ETICKETTicket.objects.filter(is_deleted=False)
    serializer_class = EticketTicketRaisedByMeListSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = '__all__'
    
    def get_queryset(self):
        current_user = self.request.user
        userid_by_filter = self.request.query_params.get('userId',None)
        is_dashboard = self.request.query_params.get('dashboard', False)
        ordering = self.request.query_params.get('ordering', None)
        if ordering is None:
            ordering = '-updated_at'
        if is_dashboard:
            qset = self.queryset.filter(created_by=current_user)
        else:
            user_ids = []
            if userid_by_filter:
                user_ids = [userid_by_filter]
            else:
                qset = get_user_list_under_user(current_user).values_list('id', flat=True)
                user_ids = list(qset) if len(qset) > 0 else []
            qset = self.queryset.filter(Q(created_by_id__in=user_ids))
        
        # filter by department, module or subject
        dept = self.request.query_params.get('dept', None)
        module = self.request.query_params.get('module', None)
        subject = self.request.query_params.get('subject', None)
        if subject is not None:
            subject = int(subject)
            qset = qset.filter(subject_id=subject)
        elif module is not None:
            module = int(module)
            qset = qset.filter(module_id=module)
        elif dept is not None:
            dept = int(dept)
            child_depts = TCoreDepartment.objects.filter(Q(cd_parent_id=dept))
            cd_child_ids = child_depts.values_list('id', flat=True)
            all_dept_ids = [dept]
            if cd_child_ids:
                all_dept_ids.extend(list(cd_child_ids))
            qset = qset.filter(department_id__in=all_dept_ids)

        # filter by from department
        from_dept = self.request.query_params.get('from_dept', None)
        if from_dept is not None:
            user_ids = TCoreUserDetail.objects.filter(Q(department_id=from_dept) | Q(sub_department_id=from_dept)).values_list('cu_user',flat=True)
            print('from_dept', from_dept, len(user_ids))
            qset = qset.filter(created_by__in=user_ids)

        # filter by priority
        priority = self.request.query_params.get('priority', None)
        if priority is not None:
            qset = qset.filter(priority=priority)

        # filter by datetime
        fromdt_str = self.request.query_params.get('fromdate', None)
        todt_str = self.request.query_params.get('todate', None)
        if fromdt_str is not None and todt_str is not None:
            from_date = datetime.datetime.strptime(fromdt_str, '%Y-%m-%d')
            to_date = datetime.datetime.strptime(todt_str, '%Y-%m-%d')
            to_date = to_date.replace(hour=23, minute=59, second=59)
            qset = qset.filter(created_at__gte=from_date, created_at__lte=to_date)

        # filter by status
        status = self.request.query_params.get('status', None)
        if status is not None:
            if status == 'Re-open':
                qset = qset.filter(ticket_closed_date__isnull=False,status='Open')
            elif status == 'Open':
                qset = qset.filter(ticket_closed_date__isnull=True,status='Open')
            else:
                qset = qset.filter(status=status)
        
        qset = qset.order_by(ordering)
        return qset


class EticketGetUserListByDeptView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = User.objects.filter(is_active=True)
    serializer_class = ETicketUserSerializer

    def get_queryset(self):
        department_details = self.kwargs
        dept_id = department_details['department_id']
        user_ids = TCoreUserDetail.objects.filter(Q(department_id=dept_id) | Q(sub_department_id=dept_id)).values_list('cu_user',flat=True)
        return self.queryset.filter(pk__in=user_ids)


class EticketUserListUnderLoginUserView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    serializer_class = ETicketUserSerializer
    pagination_class = OnOffPagination

    def get_queryset(self):
        return get_user_list_under_user(self.request.user)

def get_user_list_under_user(user):
    queryset = User.objects.filter(is_active=True)
    if user.is_superuser:
        user_ids = TCoreUserDetail.objects.filter(is_deleted=False).values_list('cu_user',flat=True)
        return queryset.filter(pk__in=user_ids)
    else:
        is_reporting_head_check = ETICKETReportingHead.objects.filter(reporting_head = user, module__isnull = True)
        if is_reporting_head_check:
            dept_id = ETICKETReportingHead.objects.get(reporting_head = user, module__isnull = True).department.id
            dept_ids = TCoreDepartment.objects.filter(cd_parent_id=dept_id).values_list('id', flat=True)
            if dept_ids:
                dept_ids = list(dept_ids)
            else:
                dept_ids = []
            dept_ids.append(dept_id)
            user_ids = TCoreUserDetail.objects.filter(Q(department_id__in=dept_ids) | Q(sub_department_id__in=dept_ids)).values_list('cu_user',flat=True)
            return queryset.filter(pk__in=user_ids)
        else:
            return queryset.filter(pk=user.id)

# endregion