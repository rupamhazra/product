from django.shortcuts import render
from rest_framework import generics
# from rest_framework.authtoken.views import ObtainAuthToken
# from rest_framework.authtoken.models import Token
# from django.contrib.auth.models import Permission
# from django.contrib.auth.models import *
from core.serializers import *
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
'''
    For Knox 
    Author : Rupam Hazra
    Date : 16.03.2020
'''
from knox.auth import TokenAuthentication
from rest_framework import permissions
from knox.models import AuthToken

class PermissionsListCreate(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    # pagination_class =CSPageNumberPagination
    queryset = TCorePermissions.objects.all()
    serializer_class = TCorePermissionsSerializer
    filter_backends = (filters.SearchFilter,)


class ModuleListCreate(generics.ListCreateAPIView):
    """docstring for ClassName"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreModule.objects.filter(cm_is_deleted=False)
    serializer_class = TCoreModuleSerializer


class ModuleList(generics.ListAPIView):
    """docstring for ClassName"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreModule.objects.all()
    serializer_class = TCoreModuleListSerializer


class EditModuleById(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreModule.objects.all()
    serializer_class = TCoreModuleSerializer


class RoleListCreate(generics.ListCreateAPIView):
    """docstring for ClassName"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreRole.objects.all()
    serializer_class = TCoreRoleSerializer


class RoleRetrieveUpdateAPIView(generics.RetrieveUpdateAPIView):
    """docstring for ClassName"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreRole.objects.all()
    serializer_class = TCoreRoleSerializer


class UnitAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreUnit.objects.all()
    serializer_class = UnitAddSerializer


#:::::::::::::::: OBJECTS :::::::::::::#

class OtherAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreOther.objects.all()
    serializer_class = OtherAddSerializer


class OtherListForRoleView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    pagination_class = CSPageNumberPagination
    queryset = TMasterModuleOther.objects.filter(is_deleted=False)
    serializer_class = OtherListForRoleSerializer

    def list(self, request, *args, **kwargs):
        response = super(OtherListForRoleView, self).list(request, args, kwargs)
        role_id = self.request.GET.get('role_id')
        parent_role_id = self.request.GET.get('parent_role_id')
        module_id = self.kwargs['module_id']
        tMasterModuleOther_list = list()
        # Permisson List
        permissionList = TCorePermissions.objects.all().values('id', 'name')
        if parent_role_id and role_id:
            tMasterModuleOther = TMasterModuleOther.objects.filter(
                mmo_module=module_id,
                is_deleted=False,
                mmo_other__cot_parent_id=0).values(
                'mmo_other__id',
                'mmo_other__cot_name',
                'mmo_other__description',
                'mmo_other__cot_is_deleted',
                'mmo_other__cot_parent_id'
            )
            # print('tMasterModuleOther',tMasterModuleOther)
            for e_tMasterModuleOther in tMasterModuleOther:
                tMasterModuleOther_e_dict = {
                    'id': e_tMasterModuleOther['mmo_other__id'],
                    'cot_name': e_tMasterModuleOther['mmo_other__cot_name'],
                    'cot_parent_id': e_tMasterModuleOther['mmo_other__cot_parent_id'],
                    'description': e_tMasterModuleOther['mmo_other__description'],
                    'cot_is_deleted': e_tMasterModuleOther['mmo_other__cot_is_deleted'],
                    'permissionlist': permissionList
                }
                # print('e_tMasterModuleOther_other',type(e_tMasterModuleOther['mmo_other__id']))
                # Checking Parent Permisson
                tMasterOtherRole = TMasterOtherRole.objects.filter(
                    mor_role_id=parent_role_id,
                    mor_other_id=e_tMasterModuleOther['mmo_other__id']
                )
                print('tMasterOtherRole', tMasterOtherRole)
                if tMasterOtherRole:
                    for e_tMasterOtherRole in tMasterOtherRole:
                        tMasterModuleOther_e_dict[
                            'parent_permission'] = e_tMasterOtherRole.mor_permissions.id if e_tMasterOtherRole.mor_permissions else 0
                else:
                    tMasterModuleOther_e_dict['parent_permission'] = 0

                # Checking Child Permisson
                tMasterOtherRole_c = TMasterOtherRole.objects.filter(
                    mor_role_id=role_id,
                    mor_other_id=e_tMasterModuleOther['mmo_other__id']
                )
                # print('tMasterOtherRole', tMasterOtherRole.query)
                if tMasterOtherRole_c:
                    for e_tMasterOtherRole_c in tMasterOtherRole_c:
                        tMasterModuleOther_e_dict[
                            'permission'] = e_tMasterOtherRole_c.mor_permissions.id if e_tMasterOtherRole_c.mor_permissions else 0
                else:
                    tMasterModuleOther_e_dict['permission'] = 0

                tMasterModuleOther_e_dict['child_details'] = self.getChildOtherList(
                    other_parent_id=e_tMasterModuleOther['mmo_other__id'],
                    role_id=role_id,
                    mor_other_id=e_tMasterModuleOther['mmo_other__id'],
                    parent_id=parent_role_id)

                tMasterModuleOther_list.append(tMasterModuleOther_e_dict)
            response.data['results'] = tMasterModuleOther_list
        else:
            tMasterModuleOther = TMasterModuleOther.objects.filter(
                mmo_module=module_id,
                is_deleted=False,
                mmo_other__cot_parent_id=0).values(
                'mmo_other__id',
                'mmo_other__cot_name',
                'mmo_other__description',
                'mmo_other__cot_is_deleted',
                'mmo_other__cot_parent_id'
            )
            # print('tMasterModuleOther',tMasterModuleOther)
            for e_tMasterModuleOther in tMasterModuleOther:
                tMasterModuleOther_e_dict = {
                    'id': e_tMasterModuleOther['mmo_other__id'],
                    'cot_name': e_tMasterModuleOther['mmo_other__cot_name'],
                    'cot_parent_id': e_tMasterModuleOther['mmo_other__cot_parent_id'],
                    'description': e_tMasterModuleOther['mmo_other__description'],
                    'cot_is_deleted': e_tMasterModuleOther['mmo_other__cot_is_deleted'],
                    'permissionlist': permissionList
                }
                # print('e_tMasterModuleOther_other',type(e_tMasterModuleOther['mmo_other__id']))
                tMasterOtherRole = TMasterOtherRole.objects.filter(
                    mor_role_id=role_id,
                    mor_other_id=e_tMasterModuleOther['mmo_other__id']
                )
                # print('tMasterOtherRole', tMasterOtherRole.query)
                if tMasterOtherRole:
                    for e_tMasterOtherRole in tMasterOtherRole:
                        tMasterModuleOther_e_dict[
                            'permission'] = e_tMasterOtherRole.mor_permissions.id if e_tMasterOtherRole.mor_permissions else 0
                else:
                    tMasterModuleOther_e_dict['permission'] = 0

                tMasterModuleOther_e_dict['child_details'] = self.getChildOtherList(
                    other_parent_id=e_tMasterModuleOther['mmo_other__id'],
                    role_id=role_id,
                    mor_other_id=e_tMasterModuleOther['mmo_other__id']
                )
                tMasterModuleOther_list.append(tMasterModuleOther_e_dict)
            response.data['results'] = tMasterModuleOther_list
            # response.data['results']['dfdsffsdf'] = list()
        return response

    def getChildOtherList(self, other_parent_id: int, role_id: int, mor_other_id: int,
                          parent_id: int = 0) -> list:
        try:
            permissionList = TCorePermissions.objects.all().values('id', 'name')
            childlist = []
            childlist_data = TCoreOther.objects.filter(cot_parent_id=other_parent_id)
            if role_id and parent_id:
                for child in childlist_data:
                    data_dict = collections.OrderedDict()
                    # print('child::',child)
                    data_dict['id'] = child.id
                    data_dict['cot_name'] = child.cot_name
                    data_dict['description'] = child.description
                    data_dict['cot_is_deleted'] = child.cot_is_deleted
                    data_dict['cot_parent_id'] = child.cot_parent_id
                    data_dict['permissionlist'] = permissionList
                    # print('child.id',type(child.id))
                    # Checking Parent Permisson
                    tMasterOtherRole = TMasterOtherRole.objects.filter(
                        mor_role_id=parent_id,
                        mor_other_id=child.id
                    )
                    if tMasterOtherRole:
                        # print('tMasterOtherRole', tMasterOtherRole)
                        for e_tMasterOtherRole in tMasterOtherRole:
                            data_dict[
                                'parent_permission'] = e_tMasterOtherRole.mor_permissions.id if e_tMasterOtherRole.mor_permissions else 0
                    else:
                        data_dict['parent_permission'] = 0

                    # Checking Child Permisson
                    tMasterOtherRole_c = TMasterOtherRole.objects.filter(
                        mor_role_id=role_id,
                        mor_other_id=child.id
                    )
                    if tMasterOtherRole_c:
                        # print('tMasterOtherRole', tMasterOtherRole)
                        for e_tMasterOtherRole_c in tMasterOtherRole_c:
                            data_dict[
                                'permission'] = e_tMasterOtherRole_c.mor_permissions.id if e_tMasterOtherRole_c.mor_permissions else 0
                    else:
                        data_dict['permission'] = 0
                    data_dict['child_details'] = self.getChildOtherList(
                        other_parent_id=child.id,
                        role_id=role_id,
                        mor_other_id=child.id,
                        parent_id=parent_id
                    )
                    childlist.append(data_dict)
            else:
                for child in childlist_data:
                    data_dict = collections.OrderedDict()
                    # print('child::',child)
                    data_dict['id'] = child.id
                    data_dict['cot_name'] = child.cot_name
                    data_dict['description'] = child.description
                    data_dict['cot_is_deleted'] = child.cot_is_deleted
                    data_dict['cot_parent_id'] = child.cot_parent_id
                    data_dict['permissionlist'] = permissionList
                    # print('child.id',type(child.id))
                    tMasterOtherRole = TMasterOtherRole.objects.filter(
                        mor_role_id=role_id,
                        mor_other_id=child.id
                    )
                    data_dict['parent_permission'] = 0
                    # Checking only child Permisson
                    if tMasterOtherRole:
                        # print('tMasterOtherRole', tMasterOtherRole)
                        for e_tMasterOtherRole in tMasterOtherRole:
                            data_dict[
                                'permission'] = e_tMasterOtherRole.mor_permissions.id if e_tMasterOtherRole.mor_permissions else 0
                    else:
                        data_dict['permission'] = 0
                    data_dict['child_details'] = self.getChildOtherList(
                        other_parent_id=child.id,
                        role_id=role_id,
                        mor_other_id=child.id
                    )
                    # print('data_dict:: ', data_dict)
                    childlist.append(data_dict)
            return childlist
        except Exception as e:
            raise e


class OtherListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    pagination_class = CSPageNumberPagination
    queryset = TMasterModuleOther.objects.filter(is_deleted=False)
    serializer_class = OtherListSerializer

    def get_queryset(self):
        module_id = self.kwargs['module_id']
        # parent_id = self.kwargs['parent_id']
        return TMasterModuleOther.objects.filter(mmo_module=module_id,
                                                 mmo_other__cot_parent_id=0, is_deleted=False)

    @response_modify_decorator_list_or_get_after_execution_for_pagination
    def list(self, request, *args, **kwargs):
        response = super(OtherListView, self).list(request, args, kwargs)
        # print('data',response.data['results'])
        for data in response.data['results']:
            OtherDetails = TCoreOther.objects.filter(
                pk=data['mmo_other'], cot_is_deleted=False)
            print('OtherDetails query', OtherDetails.query)
            for e_OtherModuleDetails in OtherDetails:
                print('OtherDetails', OtherDetails)
                data['cot_name'] = e_OtherModuleDetails.cot_name
                data['description'] = e_OtherModuleDetails.description
                data['cot_parent_id'] = e_OtherModuleDetails.cot_parent_id
                data['cot_is_deleted'] = e_OtherModuleDetails.cot_is_deleted
                
        return response


class OtherListByParentView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    pagination_class = CSPageNumberPagination
    queryset = TMasterModuleOther.objects.filter(is_deleted=False)
    serializer_class = OtherListSerializer

    def get_queryset(self):
        module_id = self.kwargs['module_id']
        parent_id = self.kwargs['parent_id']
        return TMasterModuleOther.objects.filter(mmo_module=module_id, mmo_other__cot_parent_id=parent_id)

    @response_modify_decorator_list_or_get_after_execution_for_pagination
    def list(self, request, *args, **kwargs):
        response = super(OtherListByParentView, self).list(request, args, kwargs)
        parent_id = self.kwargs['parent_id']
        # print('type',type(parent_id))

        if parent_id != '0':
            print('parent_id', parent_id)
            tcoreother = TCoreOther.objects.filter(pk=parent_id)
            print('tcoreother', tcoreother.query)
            if tcoreother:
                response.data['parent_name'] = TCoreOther.objects.only('cot_name').get(pk=parent_id).cot_name
                for data in response.data['results']:
                    OtherDetails = TCoreOther.objects.filter(
                        pk=data['mmo_other'], cot_is_deleted=False)
                    print('otherDetails', OtherDetails.query)
                    if OtherDetails:
                        for e_OtherModuleDetails in OtherDetails:
                            print('e_OtherModuleDetails', e_OtherModuleDetails)
                            data['cot_name'] = e_OtherModuleDetails.cot_name
                            data['description'] = e_OtherModuleDetails.description
                            data['cot_parent_id'] = e_OtherModuleDetails.cot_parent_id
                            data['cot_is_deleted'] = e_OtherModuleDetails.cot_is_deleted
                            

        return response


class OtherEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreOther.objects.all()
    serializer_class = OtherEditSerializer


class OtherDeleteView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreOther.objects.all()
    serializer_class = OtherDeleteSerializer


#:::::::::::::::::::::: T CORE DEPARTMENT:::::::::::::::::::::::::::#
class CoreDepartmentAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreDepartment.objects.filter(cd_is_deleted=False,cd_parent_id=0)
    serializer_class = CoreDepartmentAddSerializer
    filter_backends = (DjangoFilterBackend,)
    # filterset_fields = ('cd_parent_id',)

    @response_modify_decorator_list
    def list(self, request, *args, **kwargs):

        return response


class CoreDepartmentListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreDepartment.objects.filter(cd_is_deleted=False)
    serializer_class = CoreDepartmentListSerializer
    pagination_class = CSPageNumberPagination

    def get_queryset(self):
        department = self.request.query_params.get('department', None)
        filter = {}
        if department:
            filter['id'] = department
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        sort_field = '-id'
        if field_name and order_by:
            if field_name == 'department_name' and order_by == 'asc':
                sort_field='cd_name'

            if field_name == 'department_name' and order_by == 'desc':
                sort_field='-cd_name'
        result = self.queryset.filter(**filter).order_by(sort_field)
        return result

    @response_modify_decorator_list_or_get_after_execution_for_pagination
    def get(self, request, *args, **kwargs):
        return super(__class__, self).get(self, request, *args, **kwargs)

class CoreDepartmentWithChildView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreDepartment.objects.filter(cd_is_deleted=False,cd_parent_id=0)
    serializer_class = CoreDepartmentAddSerializer
    # filter_backends = (DjangoFilterBackend,)
    # filterset_fields = ('cd_parent_id',)
    def get_queryset(self):
        parent_id = self.kwargs['parent_id']
        return self.queryset.filter(id=parent_id,cd_is_deleted=False)

    @response_modify_decorator_get_after_execution
    def get(self, request, *args, **kwargs):
        response = super(CoreDepartmentWithChildView, self).list(request, args, kwargs)
        # child={}
        print("response",response)
        for data in response.data:
            print("data",data['id'])
            child_data = TCoreDepartment.objects.filter(cd_is_deleted=False,cd_parent_id=data['id']).values()
            response.data =child_data if child_data else []
        return response


class CoreDepartmentEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreDepartment.objects.all()
    serializer_class = CoreDepartmentEditSerializer


class CoreDepartmentDeleteView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreDepartment.objects.all()
    serializer_class = CoreDepartmentDeleteSerializer


#:::::::::::::::::::::: T CORE DESIGNATION:::::::::::::::::::::::::::#
class CoreDesignationAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreDesignation.objects.filter(cod_is_deleted=False)
    serializer_class = CoreDesignationAddSerializer

    @response_modify_decorator_list
    def list(self, request, *args, **kwargs):
        return response


class CoreDesignationEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreDesignation.objects.all()
    serializer_class = CoreDesignationEditSerializer


class CoreDesignationDeleteView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreDesignation.objects.filter(cod_is_deleted=False)
    serializer_class = CoreDesignationDeleteSerializer

class CoreDesignationListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreDesignation.objects.filter(cod_is_deleted=False)
    serializer_class = CoreDesignationListSerializer
    pagination_class = CSPageNumberPagination

    def get_queryset(self):
        designation = self.request.query_params.get('designation', None)
        filter = {}
        if designation:
            filter['id'] = designation
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        sort_field = '-id'
        if field_name and order_by:
            if field_name == 'designation_name' and order_by == 'asc':
                sort_field='cod_name'

            if field_name == 'designation_name' and order_by == 'desc':
                sort_field='-cod_name'
        result = self.queryset.filter(**filter).order_by(sort_field)
        return result

    # @response_modify_decorator_get
    @response_modify_decorator_list_or_get_after_execution_for_pagination
    def get(self, request, *args, **kwargs):
        return super(__class__, self).get(self, request, *args, **kwargs)
# :::::::::::::::::::::::::::::::::::T CORE SUB GRADE :::::::::::::::::::::::::::::::::::::::::

class CoreSubGradeAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreSubGrade.objects.filter(is_deleted=False)
    serializer_class = CoreSubGradeAddSerializer

    @response_modify_decorator_list
    def list(self, request, *args, **kwargs):
        return response

class CoreSubGradeEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreSubGrade.objects.all()
    serializer_class = CoreSubGradeEditSerializer

class CoreSubGradeDeleteView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreSubGrade.objects.all()
    serializer_class = CoreSubGradeDeleteSerializer

class CoreSubGradeListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreSubGrade.objects.filter(is_deleted=False)
    serializer_class = CoreSubGradeListSerializer
    pagination_class = CSPageNumberPagination

    def get_queryset(self):
        sub_grade = self.request.query_params.get('sub_grade', None)
        filter = {}
        if sub_grade:
            filter['id'] = sub_grade
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        sort_field = '-id'
        if field_name and order_by:
            if field_name == 'sub_grade_name' and order_by == 'asc':
                sort_field='name'

            if field_name == 'sub_grade_name' and order_by == 'desc':
                sort_field='-name'
        result = self.queryset.filter(**filter).order_by(sort_field)
        return result

    # @response_modify_decorator_get
    @response_modify_decorator_list_or_get_after_execution_for_pagination
    def get(self, request, *args, **kwargs):
        return super(__class__, self).get(self, request, *args, **kwargs)

class CoreSubGradeListWithOutPaginationView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreSubGrade.objects.filter(is_deleted=False)
    serializer_class = CoreSubGradeListSerializer
    pagination_class = OnOffPagination

    def get_queryset(self):
        sub_grade = self.request.query_params.get('sub_grade', None)
        filter = {}
        if sub_grade:
            filter['id'] = sub_grade
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        sort_field = '-id'
        if field_name and order_by:
            if field_name == 'sub_grade_name' and order_by == 'asc':
                sort_field='name'

            if field_name == 'sub_grade_name' and order_by == 'desc':
                sort_field='-name'
        result = self.queryset.filter(**filter).order_by(sort_field)
        return result

    @response_modify_decorator_list_or_get_before_execution_for_onoff_pagination
    def get(self, request, *args, **kwargs):
        return super(__class__, self).get(self, request, *args, **kwargs)

# :::::::::::::::::::::::::::::::::: T CORE GRADE ADD ::::::::::::::::::::::::
class CoreGradeAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreGrade.objects.filter(cg_is_deleted=False)
    serializer_class = CoreGradeAddSerializer

    @response_modify_decorator_list
    def list(self, request, *args, **kwargs):
        return response

class CoreGradeEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreGrade.objects.all()
    serializer_class = CoreGradeEditSerializer

class CoreGradeDeleteView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreGrade.objects.all()
    serializer_class = CoreGradeDeleteSerializer

class CoreGradeListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreGrade.objects.filter(cg_is_deleted=False)
    serializer_class = CoreGradeListSerializer
    pagination_class = CSPageNumberPagination

    def get_queryset(self):
        grade = self.request.query_params.get('grade', None)
        filter = {}
        if grade:
            filter['id'] = grade
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        sort_field = '-id'
        if field_name and order_by:
            if field_name == 'grade_name' and order_by == 'asc':
                sort_field='cg_name'

            if field_name == 'grade_name' and order_by == 'desc':
                sort_field='-cg_name'
        result = self.queryset.filter(**filter).order_by(sort_field)
        return result

    # @response_modify_decorator_get
    @response_modify_decorator_list_or_get_after_execution_for_pagination
    def get(self, request, *args, **kwargs):
        return super(__class__, self).get(self, request, *args, **kwargs)

#:::::::::::::::::::::: T CORE COMPANY :::::::::::::::::::::::::::::#
class CoreCompanyAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreCompany.objects.filter(coc_is_deleted=False)
    serializer_class = CoreCompanyAddSerializer

    @response_modify_decorator_list
    def list(self, request, *args, **kwargs):
        return response


class CoreCompanyEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreCompany.objects.all()
    serializer_class = CoreCompanyEditSerializer


class CoreCompanyDeleteView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreCompany.objects.all()
    serializer_class = CoreCompanyDeleteSerializer


class CoreCompanyListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreCompany.objects.filter(coc_is_deleted=False)
    serializer_class = CoreCompanyListSerializer
    pagination_class = CSPageNumberPagination

    def get_queryset(self):
        company = self.request.query_params.get('company', None)
        filter = {}
        if company:
            filter['id'] = company
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        sort_field = '-id'
        if field_name and order_by:
            if field_name == 'company_name' and order_by == 'asc':
                sort_field='coc_name'

            if field_name == 'company_name' and order_by == 'desc':
                sort_field='-coc_name'
        result = self.queryset.filter(**filter).order_by(sort_field)
        return result

    # @response_modify_decorator_get
    @response_modify_decorator_list_or_get_after_execution_for_pagination
    def get(self, request, *args, **kwargs):
        return super(__class__, self).get(self, request, *args, **kwargs)

#:::::::::::::::::::::: COMPANY COST CENTRE:::::::::::::::::::::::::::::#
class CompanyCostCentreAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreCompanyCostCentre.objects.filter(is_deleted=False)
    serializer_class = CompanyCostCentreAddSerializer

    @response_modify_decorator_list
    def list(self, request, *args, **kwargs):
        return response

class CompanyCostCentreEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreCompanyCostCentre.objects.all()
    serializer_class = CompanyCostCentreEditSerializer

class CompanyCostCentreListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreCompanyCostCentre.objects.filter(is_deleted=False)
    serializer_class = CompanyCostCentreListSerializer
    pagination_class = CSPageNumberPagination

    def get_queryset(self):
        company = self.request.query_params.get('company', None)
        company_id = self.request.query_params.get('company_id', None)
        filter = {}
        if company:
            filter['id'] = company
        if company_id:
            filter['company__id'] = company_id
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        sort_field = '-id'
        if field_name and order_by:
            if field_name == 'company_name' and order_by == 'asc':
                sort_field='company'

            if field_name == 'company_name' and order_by == 'desc':
                sort_field='-company'
        result = self.queryset.filter(**filter).order_by(sort_field)
        return result

    # @response_modify_decorator_get
    @response_modify_decorator_list_or_get_after_execution_for_pagination
    def get(self, request, *args, **kwargs):
        return super(__class__, self).get(self, request, *args, **kwargs)


class CompanyCostCentreWithOutPaginationListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreCompanyCostCentre.objects.filter(is_deleted=False)
    serializer_class = CompanyCostCentreListSerializer
    # pagination_class = CSPageNumberPagination

    def get_queryset(self):
        # company = self.request.query_params.get('company', None)
        company_id = self.request.query_params.get('company_id', None)
        filter = {}
        if company_id:
            filter['company__id'] = company_id
        result = self.queryset.filter(**filter)
        return result

    def get(self, request, *args, **kwargs):
        return super(__class__, self).get(self, request, *args, **kwargs)


class CompanyCostCentreDeleteView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreCompanyCostCentre.objects.all()
    serializer_class = CompanyCostCentreDeleteSerializer


class OtherAddNewView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreOther.objects.all()
    serializer_class = OtherAddNewSerializer


class OtherListNewView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    # pagination_class = CSPageNumberPagination
    queryset = TMasterModuleOther.objects.filter(is_deleted=False)
    serializer_class = OtherListSerializer

    def get_queryset(self):
        module_name = self.kwargs['module_name']
        # parent_id = self.kwargs['parent_id']
        result = TMasterModuleOther.objects.filter(mmo_module__cm_name=module_name,

                                                   mmo_other__cot_parent_id=0, is_deleted=False)
        print('result', result)
        return result

    def get_child_list(self, object_id: int) -> list:
        try:
            childlist = []
            childlist_data = TCoreOther.objects.filter(cot_parent_id=object_id, cot_is_deleted=False)

            for child in childlist_data:
                print('child', child)
                data_dict = collections.OrderedDict()
                # print('child::',child)
                data_dict['id'] = child.id
                data_dict['cot_name'] = child.cot_name
                data_dict['cot_parent_id'] = child.cot_parent_id
                data_dict['cot_is_deleted'] = child.cot_is_deleted
                data_dict['child'] = self.get_child_list(object_id=child.id)
                data_dict['permission_list'] = list()
                # print('data_dict:: ', data_dict)
                childlist.append(data_dict)
            return childlist
        except Exception as e:
            raise e

    @response_modify_decorator_list_after_execution
    def list(self, request, *args, **kwargs):
        response = super(OtherListNewView, self).list(request, args, kwargs)
        # print('data',response.data)
        for data in response.data:
            # data['child'] = self.get_child_list(object_id=data['mmo_other'])
            OtherDetails = TCoreOther.objects.filter(
                pk=data['mmo_other'], cot_is_deleted=False)
            # print('OtherDetails query',OtherDetails.query)
            for e_OtherModuleDetails in OtherDetails:
                # print('OtherDetails',OtherDetails)
                data['id'] = e_OtherModuleDetails.id
                data['cot_name'] = e_OtherModuleDetails.cot_name
                data['description'] = e_OtherModuleDetails.description
                data['cot_parent_id'] = e_OtherModuleDetails.cot_parent_id
                data['cot_is_deleted'] = e_OtherModuleDetails.cot_is_deleted
                data['permission_list'] = TCorePermissions.objects.values()
                data['child'] = self.get_child_list(object_id=e_OtherModuleDetails.id)
        return response


class OtherListWithPermissionByRoleModuleNameView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    # pagination_class = CSPageNumberPagination
    queryset = TMasterOtherRole.objects.all()
    serializer_class = OtherListWithPermissionByRoleModuleNameSerializer

    def get_queryset(self):
        module_name = self.kwargs['module_name']
        role_name = self.kwargs['role_name']
        # parent_id = self.kwargs['parent_id']
        return TMasterOtherRole.objects.filter(
            mor_module__cm_name=module_name,
            mor_role__cr_name=role_name,
            mor_module__cm_is_deleted=False,
            mor_role__cr_is_deleted=False
        ).annotate(
            mor_permissions_n=Case(
                When(mor_permissions__isnull=True, then=Value(0)),
                When(mor_permissions__isnull=False, then=F('mor_permissions')),
                output_field=IntegerField()
            ),
        )

    @response_modify_decorator_list_after_execution
    def list(self, request, *args, **kwargs):
        response = super(OtherListWithPermissionByRoleModuleNameView, self).list(request, args, kwargs)
        print('data', response.data)
        for data in response.data:
            # data['child'] = self.get_child_list(object_id=data['mmo_other'])
            OtherDetails = TCoreOther.objects.filter(
                pk=data['mor_other'], cot_is_deleted=False)
            # print('OtherDetails query',OtherDetails.query)
            for e_OtherModuleDetails in OtherDetails:
                # print('OtherDetails',OtherDetails)
                # data['id'] = e_OtherModuleDetails.id
                data['cot_name'] = e_OtherModuleDetails.cot_name
                data['description'] = e_OtherModuleDetails.description
                data['cot_parent_id'] = e_OtherModuleDetails.cot_parent_id
                data['cot_is_deleted'] = e_OtherModuleDetails.cot_is_deleted

        return response


class OtherListWithPermissionByUserModuleNameView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    # pagination_class = CSPageNumberPagination
    queryset = TMasterOtherRole.objects.all()
    serializer_class = OtherListWithPermissionByUserModuleNameSerializer

    def get_queryset(self):
        module_name = self.kwargs['module_name']
        user_id = self.kwargs['user_id']
        result = TMasterOtherUser.objects.filter(
            mou_user=user_id,
            mou_module__cm_name=module_name,
            mou_module__cm_is_deleted=False,
            mou_is_deleted=False
        ).annotate(
            mou_permissions_n=Case(
                When(mou_permissions__isnull=True, then=Value(0)),
                When(mou_permissions__isnull=False, then=F('mou_permissions')),
                output_field=IntegerField()
            ),
        )
        print('result', result)
        if result:
            result = result
        else:

            pass
            # print('result',result)
        return result

    @response_modify_decorator_list_after_execution
    def list(self, request, *args, **kwargs):
        response = super(OtherListWithPermissionByUserModuleNameView, self).list(request, args, kwargs)
        print('data', response.data)
        module_name = self.kwargs['module_name']
        user_id = self.kwargs['user_id']
        if response.data:
            for data in response.data:
                # data['child'] = self.get_child_list(object_id=data['mmo_other'])
                OtherDetails = TCoreOther.objects.filter(
                    pk=data['mou_other'], cot_is_deleted=False)
                # print('OtherDetails query',OtherDetails.query)
                for e_OtherModuleDetails in OtherDetails:
                    # print('OtherDetails',OtherDetails)
                    # data['id'] = e_OtherModuleDetails.id
                    data['cot_name'] = e_OtherModuleDetails.cot_name
                    data['description'] = e_OtherModuleDetails.description
                    data['cot_parent_id'] = e_OtherModuleDetails.cot_parent_id
                    data['cot_is_deleted'] = e_OtherModuleDetails.cot_is_deleted
        else:
            pass
        return response


class OtherEditNewView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreOther.objects.all()
    serializer_class = OtherEditNewSerializer

    @response_modify_decorator_update
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    
#::::::::::::::: T Core State ::::::::::::::::#
class StatesListAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreState.objects.filter(cs_is_deleted=False).order_by('cs_state_name')
    serializer_class = StatesListAddSerializer

    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
	    return response

class AllStatesListAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreState.objects.all().order_by('cs_state_name')
    serializer_class = AllStatesListAddSerializer

    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
	    return response


class StatesListEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreState.objects.filter(cs_is_deleted=False)
    serializer_class = StatesListEditSerializer

class StatesListDeleteView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreState.objects.filter(cs_is_deleted=False)
    serializer_class = StatesListDeleteSerializer

#:::::::::::::::::::::: T CORE SALARY TYPE:::::::::::::::::::::::::::#
class CoreSalaryTypeAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreSalaryType.objects.all()
    serializer_class = CoreSalaryTypeAddSerializer

    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        return response

class CoreSalaryTypeEditView(generics.RetrieveUpdateAPIView):
	permission_classes = [IsAuthenticated]
	authentication_classes = [TokenAuthentication]
	queryset = TCoreSalaryType.objects.filter(st_is_deleted=False)
	serializer_class = CoreSalaryTypeEditSerializer


class CoreSalaryTypeDeleteView(generics.RetrieveUpdateAPIView):
	permission_classes = [IsAuthenticated]
	authentication_classes = [TokenAuthentication]
	queryset = TCoreSalaryType.objects.filter(st_is_deleted=False)
	serializer_class = CoreSalaryTypeDeleteSerializer


#:::::::::::::::::::::: T CORE BANK :::::::::::::::::::::::::::#
class CoreBankAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreBank.objects.filter(is_deleted=False)
    serializer_class = CoreBankAddSerializer

    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        return response

class CoreBankEditView(generics.RetrieveUpdateAPIView):
	permission_classes = [IsAuthenticated]
	authentication_classes = [TokenAuthentication]
	queryset = TCoreBank.objects.filter(is_deleted=False)
	serializer_class = CoreBankEditSerializer


class CoreBankDeleteView(generics.RetrieveUpdateAPIView):
	permission_classes = [IsAuthenticated]
	authentication_classes = [TokenAuthentication]
	queryset = TCoreBank.objects.filter(is_deleted=False)
	serializer_class = CoreBankDeleteSerializer

class CoreBankListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreBank.objects.filter(is_deleted=False)
    serializer_class = CoreBankListSerializer
    pagination_class = CSPageNumberPagination

    def get_queryset(self):
        bank = self.request.query_params.get('bank', None)
        filter = {}
        if bank:
            filter['id'] = bank
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        sort_field = '-id'
        if field_name and order_by:
            if field_name == 'bank_name' and order_by == 'asc':
                sort_field='name'

            if field_name == 'bank_name' and order_by == 'desc':
                sort_field='-name'
        result = self.queryset.filter(**filter).order_by(sort_field)
        return result

    # @response_modify_decorator_get
    @response_modify_decorator_list_or_get_after_execution_for_pagination
    def get(self, request, *args, **kwargs):
        return super(__class__, self).get(self, request, *args, **kwargs)



#:::::::::::::::::::::: T CORE DEPARTMENT:::::::::::::::::::::::::::#
class CoreSubDepartmentView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreDepartment.objects.filter(cd_is_deleted=False)
    serializer_class = CoreDepartmentAddSerializer
    filter_backends = (DjangoFilterBackend,)

    def get_queryset(self):
        department = self.kwargs['dept_id']
        return self.queryset.filter(cd_parent_id = department)
    @response_modify_decorator_list
    def list(self, request, *args, **kwargs):
        return response


#:::::::::::::::::::::: T CORE Country :::::::::::::::::::::::::::#
class CoreCountryAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreCountry.objects.filter(is_deleted=False).order_by('name')
    serializer_class = CoreCountryAddSerializer

    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        return response


class CoreCountryEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreCountry.objects.filter(is_deleted=False)
    serializer_class = CoreCountryEditSerializer


class CoreCountryDeleteView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreCountry.objects.filter(is_deleted=False)
    serializer_class = CoreCountryDeleteSerializer


#:::::::::::::::::::::: T CORE Currency :::::::::::::::::::::::::::#
class CoreCurrencyAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreCurrency.objects.filter(is_deleted=False)
    serializer_class = CoreCurrencyAddSerializer

    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        return response


class CoreCurrencyCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreCurrency.objects.filter(is_deleted=False)
    serializer_class = CoreCurrencyCreateSerializer


class CoreCurrencyEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreCurrency.objects.filter(is_deleted=False)
    serializer_class = CoreCurrencyEditSerializer


class CoreCurrencyDeleteView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreCurrency.objects.filter(is_deleted=False)
    serializer_class = CoreCurrencyDeleteSerializer


# :::::::::::::::::::::: T CORE Domain ::::::::::::::::::::::::::: #
class CoreDomainAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreDomain.objects.filter(is_deleted=False)
    serializer_class = CoreDomainAddSerializer
    pagination_class = OnOffPagination

    @response_modify_decorator_list_or_get_before_execution_for_onoff_pagination
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CoreDomainEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreDomain.objects.filter(is_deleted=False)
    serializer_class = CoreDomainEditSerializer


class CoreDomainDeleteView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreDomain.objects.filter(is_deleted=False)
    serializer_class = CoreDomainDeleteSerializer


#:::::::::::::::::::::: T CORE CITY :::::::::::::::::::::::::::::#
class CoreCityAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreCity.objects.filter(is_deleted=False)
    serializer_class = CoreCityAddSerializer

class CoreCityEditView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreCity.objects.all()
    serializer_class = CoreCityEditSerializer

class CoreCityDeleteView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreCity.objects.all()
    serializer_class = CoreCityDeleteSerializer


class CoreCityListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreCity.objects.filter(is_deleted=False)
    serializer_class = CoreCityListSerializer
    pagination_class = CSPageNumberPagination

    def get_queryset(self):
        company = self.request.query_params.get('city', None)
        filter = {}
        if company:
            filter['id'] = company
        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        sort_field = '-id'
        if field_name and order_by:
            if field_name == 'city_name' and order_by == 'asc':
                sort_field='name'

            if field_name == 'city_name' and order_by == 'desc':
                sort_field='-name'
        result = self.queryset.filter(**filter).order_by(sort_field)
        return result

    # @response_modify_decorator_get
    @response_modify_decorator_list_or_get_after_execution_for_pagination
    def get(self, request, *args, **kwargs):
        return super(__class__, self).get(self, request, *args, **kwargs)


class FloorListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreFloor.objects.filter(is_deleted=False)
    serializer_class = FloorListSerializer
    pagination_class = CSPageNumberPagination

    # @response_modify_decorator_get
    @response_modify_decorator_list_or_get_after_execution_for_pagination
    def get(self, request, *args, **kwargs):
        return super(__class__, self).get(self, request, *args, **kwargs)