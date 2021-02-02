from django.shortcuts import render
from rest_framework import generics
#from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import Permission
# from django.contrib.auth.models import *
from users.models import *
from users.serializers import *
from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework import filters
from global_function import *

# permission checking
from rest_framework.permissions import IsAuthenticated, IsAdminUser, IsAuthenticatedOrReadOnly, AllowAny
#from rest_framework.authentication import TokenAuthentication, SessionAuthentication
# collections 
import collections
# get_current_site
from django.contrib.sites.shortcuts import get_current_site
from mailsend.views import *
from rest_framework.exceptions import APIException
from threading import Thread  # for threading
from django.conf import settings
from django.db.models import Q
# pagination
from pagination import CSLimitOffestpagination, CSPageNumberPagination, OnOffPagination
from datetime import datetime
from custom_decorator import *
from core.serializers import *

'''
    New Token Authentication [knox] 
    Reason : Multiple token generated every time on login and store on Knox Auth Token Table as digest
    Author : Rupam Hazra 
    Date : [14.03.2020] 
'''
from knox.auth import TokenAuthentication
from rest_framework import permissions
from knox.models import AuthToken
#from AuthTokenSerializer import *
from knox_views.views import LoginView as KnoxLoginView
from django.contrib.auth import login
from knox.settings import CONSTANTS, knox_settings


class LoginView(KnoxLoginView):
    permission_classes = [AllowAny]

    # serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        #print('fdfdfdfdfdfdfd')
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
        update_last_login(None, user)

        login_data = login(request, user)
        #print('login_data', login_data)
        if user:
            odict = self.getUserDetails(user, request)
            return Response(odict)

    def getUserDetails(self, user, request):
        applications = self.getApplications(request, user)
        user_details = TCoreUserDetail.objects.get(cu_user=user)
        profile_pic = request.build_absolute_uri(user_details.cu_profile_img.url) if user_details.cu_profile_img else ''
        odict = collections.OrderedDict()
        odict['user_id'] = user.pk
        odict['token'] = AuthToken.objects.create(user)[1]
        odict['username'] = user.username
        odict['first_name'] = user.first_name
        odict['last_name'] = user.last_name
        odict['email'] = user_details.cu_alt_email_id
        odict['job_location_state'] = user_details.job_location_state.id if user_details.job_location_state else None
        odict['official_email'] = user_details.cu_alt_email_id if user_details.cu_alt_email_id else None
        odict['is_superuser'] = user.is_superuser
        odict['cu_phone_no'] = user_details.cu_phone_no
        odict['is_flexi_hour'] = user_details.is_flexi_hour
        odict['salary_type_code'] = user_details.salary_type.st_code if user_details.salary_type else None
        odict['cu_profile_img'] = profile_pic
        odict['cu_change_pass'] = user_details.cu_change_pass
        odict['module_access'] = applications
        odict['request_status'] = 1
        odict['msg'] = "Logged in successfully .."
        odict['switchUser'] = ''
        odict['project_details'] = self.getProjectDetails(user) 

        browser, ip, os = self.detectBrowser()
        log = LoginLogoutLoggedTable.objects.create(
            user=user, token=odict['token'], ip_address=ip, browser_name=browser, os_name=os)

        #print('log',log)
        return odict

    def getApplications(self, request, user):
        print('getApplications')
        mmr_details = TMasterModuleRoleUser.objects.filter(mmr_user=user)
        # print('mmr_details',mmr_details)
        applications = list()
        for mmr_data in mmr_details:
            # print('mmr_details111111',mmr_data)
            module_dict = collections.OrderedDict()
            module_dict["id"] = mmr_data.id
            # print('module_dict',module_dict)
            # print('type(mmr_data.mmr_type)',mmr_data.mmr_type)
            if mmr_data.mmr_type:
                module_dict["user_type_details"] = collections.OrderedDict({
                    "id": mmr_data.mmr_type,
                    "name": 'Module Admin' if mmr_data.mmr_type == 2 else 'Module User' if mmr_data.mmr_type == 3 else 'Demo User' if mmr_data.mmr_type == 6 else 'Super User'
                })
            else:
                module_dict["user_type_details"] = collections.OrderedDict({})

            module_dict["module"] = collections.OrderedDict({
                "id": mmr_data.mmr_module.id,
                "cm_name": mmr_data.mmr_module.cm_name,
                "cm_url": mmr_data.mmr_module.cm_url,
                "cm_icon": request.build_absolute_uri(mmr_data.mmr_module.cm_icon.url),
                # "cm_icon": "http://" + get_current_site(request).domain + mmr_data.mmr_module.cm_icon.url,
            })
            # print('module_dict["module"]',module_dict["module"])
            # print('dfdfdfffffffffffffffffffffffffffff')
            # print('mmr_data.mmr_module',mmr_data.mmr_type)
            if (mmr_data.mmr_type == 1):
                module_dict["role"] = collections.OrderedDict({})

            else:
                # print(' mmr_data.mmr_role',  mmr_data.mmr_role)
                if mmr_data.mmr_role:
                    module_dict["role"] = collections.OrderedDict({
                        "id": mmr_data.mmr_role.id,
                        "cr_name": mmr_data.mmr_role.cr_name,
                        "cr_parent_id": mmr_data.mmr_role.cr_parent_id,
                    })
                else:
                    module_dict["role"] = collections.OrderedDict()

                if mmr_data.mmr_role:
                    # print('e_tMasterModuleOther_other',type(e_tMasterModuleOther['mmo_other__id']))
                    tMasterOtherUser = TMasterOtherUser.objects.filter(
                        # mor_role=mmr_data.mmr_role,
                        mou_user=user,
                        mou_is_deleted=False,
                        mou_other__cot_parent_id=0
                        # mor_other_id=e_tMasterModuleOther['mmo_other__id']
                    )
                    # print('tMasterOtherUser', tMasterOtherUser)
                    if tMasterOtherUser:
                        tMasterModuleOther_list = list()
                        for e_tMasterOtherUser in tMasterOtherUser:
                            tMasterModuleOther_e_dict = dict()
                            tMasterModuleOther_e_dict['id'] = e_tMasterOtherUser.mou_other.id
                            tMasterModuleOther_e_dict['name'] = e_tMasterOtherUser.mou_other.cot_name
                            tMasterModuleOther_e_dict['parent'] = e_tMasterOtherUser.mou_other.cot_parent_id
                            tMasterModuleOther_e_dict[
                                'permission'] = e_tMasterOtherUser.mou_permissions.id if e_tMasterOtherUser.mou_permissions else 0
                            # print('mmr_data.mmr_role.id',mmr_data.mmr_role.id)
                            tMasterModuleOther_e_dict['child_details'] = self.getChildOtherListForLogin(
                                role_id=mmr_data.mmr_role.id,
                                parent_other_id=e_tMasterOtherUser.mou_other.id, user_id=user.id)
                            tMasterModuleOther_list.append(tMasterModuleOther_e_dict)
                    else:

                        tMasterOtherRole = TMasterOtherRole.objects.filter(
                            mor_role=mmr_data.mmr_role,
                            # mou_user = user,
                            mor_is_deleted=False,
                            mor_other__cot_parent_id=0
                            # mor_other_id=e_tMasterModuleOther['mmo_other__id']
                        )
                        # print('tMasterOtherRole', tMasterOtherRole)
                        if tMasterOtherRole:
                            tMasterModuleOther_list = list()
                            for e_tMasterOtherRole in tMasterOtherRole:
                                tMasterModuleOther_e_dict = dict()
                                tMasterModuleOther_e_dict['id'] = e_tMasterOtherRole.mor_other.id
                                tMasterModuleOther_e_dict['name'] = e_tMasterOtherRole.mor_other.cot_name
                                tMasterModuleOther_e_dict['parent'] = e_tMasterOtherRole.mor_other.cot_parent_id
                                tMasterModuleOther_e_dict[
                                    'permission'] = e_tMasterOtherRole.mor_permissions.id if e_tMasterOtherRole.mor_permissions else 0
                                # print('mmr_data.mmr_role.id',mmr_data.mmr_role.id)
                                tMasterModuleOther_e_dict['child_details'] = self.getChildOtherListForRoleLogin(
                                    role_id=mmr_data.mmr_role.id,
                                    parent_other_id=e_tMasterOtherRole.mor_other.id)
                                tMasterModuleOther_list.append(tMasterModuleOther_e_dict)

                        else:
                            tMasterModuleOther_list = list()
                        # tMasterModuleOther_e_dict['child_details'] = 1
                    # print('tMasterModuleOther_list',tMasterModuleOther_list)
                    # response.data['results'] = tMasterModuleOther_list
                else:
                    tMasterModuleOther_list = list()
                module_dict["object_details"] = tMasterModuleOther_list
                # print('module_dict["permissions"]',module_dict["object_details"])
                applications.append(module_dict)

        return applications

    def detectBrowser(self):
        #print('self.request',dir(self.request.META))
        import httpagentparser
        user_ip = self.request.META.get('REMOTE_ADDR')
        agent = self.request.META.get('HTTP_USER_AGENT')
        browser = httpagentparser.detect(agent)
        browser_name = agent.split('/')[0] if not "browser" in browser.keys() else browser['browser']['name']
        os = "" if not "os" in browser.keys() else browser['os']['name']
        return browser_name, user_ip, os

    def getChildOtherListForLogin(self, role_id: int, parent_other_id: int = 0, user_id: int = 0) -> list:
        try:
            # print('role_id',role_id)
            # permissionList = TCorePermissions.objects.all().values('id', 'name')
            childlist = []
            childlist_data = TCoreOther.objects.filter(cot_parent_id=parent_other_id)
            # print('childlist_data',childlist_data)
            for child in childlist_data:
                data_dict = collections.OrderedDict()
                # print('child::',child)
                data_dict['id'] = child.id
                data_dict['cot_name'] = child.cot_name
                data_dict['description'] = child.description
                data_dict['cot_is_deleted'] = child.cot_is_deleted
                data_dict['cot_parent_id'] = child.cot_parent_id
                # print('child.id',type(child.id))
                tMasterOtherRole = TMasterOtherUser.objects.filter(
                    # mou_role_id=role_id,
                    mou_other_id=child.id,
                    mou_user_id=user_id
                )
                data_dict['parent_permission'] = 0
                # Checking only child Permisson
                if tMasterOtherRole:
                    # print('tMasterOtherRole', tMasterOtherRole)
                    for e_tMasterOtherRole in tMasterOtherRole:
                        data_dict[
                            'permission'] = e_tMasterOtherRole.mou_permissions.id if e_tMasterOtherRole.mou_permissions else 0
                else:
                    data_dict['permission'] = 0
                data_dict['child_details'] = self.getChildOtherListForLogin(
                    role_id=role_id,
                    parent_other_id=child.id,
                    user_id=user_id
                )
                # print('data_dict:: ', data_dict)
                childlist.append(data_dict)
            return childlist
        except Exception as e:
            raise e

    def getChildOtherListForRoleLogin(self, role_id: int, parent_other_id: int = 0) -> list:
        try:
            # print('role_id',role_id)
            # permissionList = TCorePermissions.objects.all().values('id', 'name')
            childlist = []
            childlist_data = TCoreOther.objects.filter(cot_parent_id=parent_other_id)
            # print('childlist_data',childlist_data)
            for child in childlist_data:
                data_dict = collections.OrderedDict()
                # print('child::',child)
                data_dict['id'] = child.id
                data_dict['cot_name'] = child.cot_name
                data_dict['description'] = child.description
                data_dict['cot_is_deleted'] = child.cot_is_deleted
                data_dict['cot_parent_id'] = child.cot_parent_id
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
                data_dict['child_details'] = self.getChildOtherListForRoleLogin(
                    role_id=role_id,
                    parent_other_id=child.id,
                )
                # print('data_dict:: ', data_dict)
                childlist.append(data_dict)
            return childlist
        except Exception as e:
            raise e

    def getProjectDetails(self, user):
        from pms.models.module_project import PmsProjectUserMapping,PmsSiteProjectSiteManagementMultipleLongLat,PmsProjects
        project = None
        project_user_mapping = PmsProjectUserMapping.objects.filter(user=user, status=True).order_by('-id').values('project')
        #print("project_user_mapping",project_user_mapping)
        if project_user_mapping:
            project = project_user_mapping[0]['project']
            #request.data['user_project_id'] = project
            #print('project',project)
            project_site = PmsProjects.objects.filter(pk=project).values('id','site_location','site_location__geo_fencing_area')
            #print('project_site_details',project_site)
            if project_site:
                for e_project_site in project_site:
                    geofence = e_project_site['site_location__geo_fencing_area']
                    #print('geofence',geofence)
                    multi_lat_long=PmsSiteProjectSiteManagementMultipleLongLat.objects.filter(
                    project_site_id=e_project_site['site_location']).values()
                    #print('multi_lat_long',multi_lat_long)

            else:
                multi_lat_long = list()
            
        else:
            multi_lat_long = list()
            geofence = ''

        return {
        'user_project_id':project,
        'user_project_details':multi_lat_long,
        'geo_fencing_area':geofence
        }

'''
    END KNOX
'''


class UsersSignInListCreate(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    # pagination_class =CSPageNumberPagination
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer

class ChangePasswordView(generics.UpdateAPIView):
    """
    For changing password.
    password is changing using login user token.
    needs old password and new password,
    check old password is exiest or not
    if exiest than it works
    """
    serializer_class = ChangePasswordSerializer
    model = User
    permission_classes = (IsAuthenticated,)
    authentication_classes = [TokenAuthentication]

    def get_object(self, queryset=None):
        obj = self.request.user
        return obj

    def update(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            user_data = self.request.user
            mail_id = user_data.email
            print('user',user_data)
            if not self.object.check_password(serializer.data.get("old_password")):
                return Response({'request_status': 1, 'msg': "Wrong password..."}, status=status.HTTP_400_BAD_REQUEST)
            self.object.set_password(serializer.data.get("new_password"))
            self.object.save()
            TCoreUserDetail.objects.filter(cu_user=self.request.user, cu_change_pass=True).update(
                cu_change_pass=False,password_to_know = serializer.data.get("new_password"))
            # ============= Mail Send ==============#
            if mail_id:
                mail_data = {
                            "name": user_data.first_name+ '' + user_data.last_name,
                            "password": serializer.data.get("new_password")
                    }
                mail_class = GlobleMailSend('CHP', [mail_id])
                mail_thread = Thread(target = mail_class.mailsend, args = (mail_data,))
                mail_thread.start()
            else:
                # ============= SMS Send ==============#
                cu_phone_no = TCoreUserDetail.objects.only('cu_phone_no').get(cu_user=user_data).cu_phone_no
                print('cu_phone_no',cu_phone_no)
                if cu_phone_no:
                    message_data = {
                        "password": serializer.data.get("new_password") 
                    }
                    sms_class = GlobleSmsSendTxtLocal('FP100',[cu_phone_no])
                    sms_thread = Thread(target = sms_class.sendSMS, args = (message_data,'sms'))
                    sms_thread.start()
            return Response({'request_status': 0, 'msg': "New Password Save Success..."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordWithUsernameView(generics.UpdateAPIView):
    """
    For changing password.
    password is changing using login user token.
    needs old password and new password,
    check old password is exiest or not
    if exiest than it works
    """
    serializer_class = ChangePasswordSerializer
    model = User
    permission_classes = (IsAuthenticated,)
    authentication_classes = [TokenAuthentication]

    def update(self, request, *args, **kwargs):
        #self.object = self.get_object()
        #serializer = self.get_serializer(data=request.data)
        username = self.request.data['username']
        #print('username',username)

        user_data = User.objects.get(username = username)
        print('user',user_data)

        new_password = self.request.data['new_password']
        user_data.set_password(new_password) 
        user_data.save()

        TCoreUserDetail.objects.filter(
            cu_user=user_data).update(
            cu_change_pass=False,password_to_know = new_password)

        # if not self.object.check_password(serializer.data.get("old_password")):
        #     return Response({'request_status': 1, 'msg': "Wrong password..."}, status=status.HTTP_400_BAD_REQUEST)
        # self.object.set_password(serializer.data.get("new_password"))
        # self.object.save()
        
        
        return Response({'request_status': 0, 'msg': "New Password Save Success..."}, status=status.HTTP_200_OK)

class ForgotPasswordView(APIView):
    """
    Forgot password using mail id ,
    randomly set password,
    mail send using thread,
    using post method
    """

    model = User
    permission_classes = []
    authentication_classes = []

    def post(self, request, format=None):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            mail_id = serializer.data.get("mail_id")
            cu_phone_no = serializer.data.get("cu_phone_no")
            password = 'Shyam@123'  # default password
            if mail_id:
                user_details_exiest = TCoreUserDetail.objects.filter(cu_user__email=mail_id)
            if cu_phone_no:
                user_details_exiest = TCoreUserDetail.objects.filter(cu_phone_no=cu_phone_no)
            #print("user_details_exiest",user_details_exiest)
            if user_details_exiest:
                for user_data in user_details_exiest:
                    user_data.cu_change_pass = True
                    user_data.password_to_know = password
                    fast_name = user_data.cu_user.first_name
                    last_name = user_data.cu_user.last_name
                    send_mail_to = user_data.cu_user.email
                    send_sms_to = user_data.cu_phone_no if user_data.cu_phone_no else ""
                    user_data.cu_user.set_password(password)  # set password...
                    user_data.cu_user.save()
                    user_data.save()
                    #print('user_data',user_data.cu_user.password)
                # ============= Mail Send ==============#
                if mail_id:
                    mail_data = {
                                "name": user_data.cu_user.first_name+ '' + user_data.cu_user.last_name,
                                "password": password
                        }
                    mail_class = GlobleMailSend('FP100', [mail_id])
                    mail_thread = Thread(target = mail_class.mailsend, args = (mail_data,))
                    mail_thread.start()
                # ============= SMS Send ==============#
                if cu_phone_no:
                    message_data = {
                        "password": password 
                    }
                    sms_class = GlobleSmsSendTxtLocal('FP100',[cu_phone_no])
                    sms_thread = Thread(target = sms_class.sendSMS, args = (message_data,'sms'))
                    sms_thread.start()
                
                return Response({'request_status': 1, 'msg': "New Password Save Success..."}, status=status.HTTP_200_OK)
            else:
                raise APIException({'request_status': 1, 'msg': "User does not exist."})

        return Response({'request_status': 0, 'msg': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class ActiveInactiveUserView(generics.RetrieveUpdateAPIView):
    """
    send parameter 'is_active'
    View for user update active and in_active
    using user ID
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    serializer_class = UserSerializer
    queryset = User.objects.all()

class EditUserView(generics.RetrieveUpdateAPIView):
    """
    View for user update
    using user ID
    login user and provided user must be same.. or must be admin
    email, cu_emp_code and username only change by admin
    if img is exist and need to update, than, it will be deleted fast and than update
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    serializer_class = EditUserSerializer
    lookup_field = 'cu_user_id'

    def get_queryset(self):
        user_id = self.kwargs["cu_user_id"]
        if str(self.request.user.id) == user_id or self.request.user.is_superuser:
            return TCoreUserDetail.objects.filter(cu_user_id=user_id)
        else:
            raise APIException({'request_status': 0, 'msg': 'Login user is different'})

class ModuleUserList(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreUserDetail.objects.filter(cu_user__is_active=True,cu_user__is_superuser=False).order_by('-cu_user_id')
    serializer_class = UserModuleSerializer
    pagination_class = CSPageNumberPagination
    filter_backends = (filters.SearchFilter,)
    search_fields = ('cu_user__username', 'cu_phone_no','cu_user__email','cu_emp_code',)
    def get_queryset(self):
        try:
            order_by = self.request.query_params.get('order_by', None)
            field_name = self.request.query_params.get('field_name', None)
            if order_by and order_by.lower() == 'desc' and field_name:
                queryset = self.queryset.order_by('-' + field_name)
            elif order_by and order_by.lower() == 'asc' and field_name:
                queryset = self.queryset.order_by(field_name)
            else:
                queryset = self.queryset
            return queryset.filter(~Q(cu_user_id=self.request.user.id))
        except Exception as e:
            # raise e
            raise APIException({'request_status': 0, 'msg': e})


class UserUpdateEmployeeCode(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreUserDetail.objects.filter(cu_user__is_active=True).order_by('cu_user_id')
    def post(self, request, format=None):
        data = [
        ]

        for d in data:
            #print('d',d['username'])
            ud = User.objects.get(username__iexact= d['username'])
            print('ud',ud)
            TCoreUserDetail.objects.filter(cu_user=ud).update(cu_emp_code=d['cu_emp_code'])

class UserPermissionEditView(generics.RetrieveUpdateAPIView):
    """
    View for user update
    using user ID
    login user and provided user must be same.. or must be admin
    email, cu_emp_code and username only change by admin
    if img is exist and need to update, than, it will be deleted fast and than update
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    serializer_class = UserPermissionEditSerializer
    lookup_field = 'cu_user_id'

    def get_queryset(self):
        user_id = self.kwargs["cu_user_id"]
        result = TCoreUserDetail.objects.filter(cu_user_id=user_id)
        #print('result',result)
        return result


class EditUserNewView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    # pagination_class =CSPageNumberPagination
    queryset = User.objects.all()
    serializer_class = EditUserNewSerializer

class EditUserGetNewView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    # pagination_class =CSPageNumberPagination
    queryset = User.objects.all()
    serializer_class = EditUserGetNewSerializer
    
class UserListByDepartmentView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserSerializer

    def get_queryset(self):
        #print('self.kwargs',self.kwargs)
        department_details = self.kwargs
        user_ids = TCoreUserDetail.objects.filter(
            department_id=department_details['department_id']).values_list('cu_user',flat=True)
        return self.queryset.filter(pk__in=user_ids)
    
    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
class UserListUnderLoginUserView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserSerializer
    pagination_class = OnOffPagination

    def get_queryset(self):
        head_type = self.request.query_params.get('type',None)
        user = self.request.user
        if user.is_superuser:
            return self.queryset.filter(is_active=True)
        else:
            if head_type:
                if head_type.lower() == 'hod':
                    user_ids = TCoreUserDetail.objects.filter(
                        hod=user).values_list('cu_user',flat=True)
                    return self.queryset.filter(pk__in=user_ids)
                elif head_type.lower() == 'reporting-head':
                    user_ids = TCoreUserDetail.objects.filter(
                        reporting_head=user).values_list('cu_user',flat=True)
                    return self.queryset.filter(pk__in=user_ids)
            else:
                return list()

    @response_modify_decorator_list_or_get_before_execution_for_onoff_pagination
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
 
class HodListWithDepartmentView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = TCoreDepartment.objects.filter(cd_is_deleted=False)
    serializer_class = CoreDepartmentEditSerializer
    pagination_class = OnOffPagination
    
    @response_modify_decorator_list_or_get_after_execution_for_onoff_pagination
    def get(self, request, *args, **kwargs):
        response = super(self.__class__, self).get(self, request, args, kwargs)
        hod_list = TCoreUserDetail.objects.filter(
            cu_is_deleted=False,hod__isnull=False).values_list('hod',flat=True).distinct()
        print('hod_list',hod_list)
        details_list = list()

        if 'results' in response.data:
            data_dict = response.data['results']
        else:
            data_dict = response.data

        for data in data_dict:
            data['department'] = data['cd_name']
            data.pop('cd_name')
            #print('data',type(data['id']))
            department_head_details = ''
            for e_hod in hod_list:
                #print('e_hod',type(e_hod))
                dept = TCoreUserDetail.objects.only('department').get(cu_user=e_hod).department
                if dept is not None:
                    #print('dept',type(dept.id))
                    if dept.id == data['id']:
                        department_head_details = User.objects.get(pk=e_hod)
                        #print('department_head_details',department_head_details)
                        data['first_name'] = department_head_details.first_name
                        data['last_name'] = department_head_details.last_name
                    else:
                        data['first_name'] = ''
                        data['last_name'] = ''
        return response     

class HodOrReportingHeadListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    
    def get(self,request,*args,**kwargs):
        try:
            data_dict={}
            user_type = self.request.query_params.get('user_type', None)
            hod_details_list=[]
            if user_type == 'hod':
                hod_details=list(TCoreUserDetail.objects.filter(hod__isnull=False,cu_is_deleted=False).values_list('hod',flat=True).distinct())            
                print('hod_details',hod_details)
                if hod_details:
                    for h_d in hod_details:
                        h_d_dict={
                            'id':h_d,
                            'name':userdetails(h_d)
                        }
                        hod_details_list.append(h_d_dict)

            if user_type == 'reporting_head':
                rh_details=list(TCoreUserDetail.objects.filter(reporting_head__isnull=False,cu_is_deleted=False).values_list('reporting_head',flat=True).distinct())            
                print('rh_details',rh_details)
                if rh_details:
                    for h_d in rh_details:
                        h_d_dict={
                            'id':h_d,
                            'name':userdetails(h_d)
                        }
                        hod_details_list.append(h_d_dict)

            
            data_dict['result'] = hod_details_list
            if hod_details_list:
                data_dict['request_status'] = 1
                data_dict['msg'] = settings.MSG_SUCCESS
            elif len(hod_details_list) == 0:
                data_dict['request_status'] = 1
                data_dict['msg'] = settings.MSG_NO_DATA
            else:
                data_dict['request_status'] = 0
                data_dict['msg'] = settings.MSG_ERROR

            return Response(data_dict)
            
        except Exception as e:
            raise e


        