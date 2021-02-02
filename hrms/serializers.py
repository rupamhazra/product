from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from hrms.models import *
from django.contrib.auth.models import *
from django.db import transaction, IntegrityError
from drf_extra_fields.fields import Base64ImageField
from master.models import *
import os
from custom_exception_message import *
from datetime import datetime,timedelta
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from users.models import TCoreUserDetail
from smssend.views import *
from threading import Thread
from custom_decorator import *
from rest_framework.authtoken.models import Token
from attendance.models import *
from decimal import Decimal
from core.models import *
from pms.models import *
from users.models import UserTempReportingHeadMap,EmployeeTransferHistory
import re
import random
from mailsend.views import *
from global_function import round_calculation
from dateutil.relativedelta import *
from global_function import getHostWithPort

from django.contrib.admin.models import LogEntry

from employee_leave_calculation import *
import time
#:::::::::::::::::::::: HRMS BENEFITS PROVIDED:::::::::::::::::::::::::::#
class BenefitsProvidedAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = HrmsBenefitsProvided
        fields = ('id', 'benefits_name','created_by', 'owned_by')


class BenefitsProvidedEditSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = HrmsBenefitsProvided
        fields = ('id', 'benefits_name','updated_by')

class BenefitsProvidedDeleteSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = HrmsBenefitsProvided
        fields = '__all__'
    def update(self, instance, validated_data):
        instance.is_deleted=True
        instance.updated_by = validated_data.get('updated_by')
        instance.save()
        return instance

#:::::::::::::::::::::: HRMS QUALIFICATION MASTER:::::::::::::::::::::::::::#
class QualificationMasterAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = HrmsQualificationMaster
        fields = ('id', 'name', 'created_by', 'owned_by')


class QualificationMasterEditSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = HrmsQualificationMaster
        fields = ('id', 'name', 'updated_by')

class QualificationMasterDeleteSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = HrmsQualificationMaster
        fields = '__all__'
    def update(self, instance, validated_data):
        instance.is_deleted=True
        instance.updated_by = validated_data.get('updated_by')
        instance.save()
        return instance

#::::::::::::::::::::::::::::: HRMS EMPLOYEE:::::::::::::::::::::::::::::::::::::::#
class EmployeeAddSerializer(serializers.ModelSerializer):
    '''
        Last modified By Rupam Hazra on [13.02.2020] as per details

        1. "Employee Login ID" remove. It will be auto created
        2. SAP Personnel ID (Optional)
        3. Add official email id (Optional)
        4. Job Location State
        5. Department
        6. Designation
        -----------------------------------------------

        Date of Termination ->Release Date
        Resignation Date:
    '''
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    cu_phone_no = serializers.CharField(required=False)
    cu_punch_id= serializers.CharField(required=False)
    hod=serializers.CharField(required=False)
    grade=serializers.CharField(required=False,allow_null=True)
    cu_emp_code = serializers.CharField(required=False)
    sap_personnel_no=serializers.CharField(required=False,allow_null=True)
    mmr_module_id=serializers.CharField(required=False)
    mmr_type=serializers.CharField(required=False)
    reporting_head=serializers.CharField(required=False)
    cu_profile_img=serializers.FileField(required=False)
    reporting_head_name=serializers.CharField(required=False)
    company=serializers.CharField(required=False)
    cost_centre=serializers.CharField(required=False)
    hod_name=serializers.CharField(required=False)
    grade_name=serializers.CharField(required=False)
    joining_date=serializers.CharField(required=False)
    daily_loginTime=serializers.CharField(default="10:00:00")
    daily_logoutTime=serializers.CharField(default="19:00:00")
    lunch_start=serializers.CharField(default="13:30:00")
    lunch_end=serializers.CharField(default="14:00:00")
    salary_type= serializers.CharField(required=False,allow_null=True)
    cu_alt_email_id = serializers.CharField(required=False,allow_null=True)
    job_location_state = serializers.CharField(required=False)
    department = serializers.CharField(required=False)
    designation = serializers.CharField(required=False)
    sub_department = serializers.CharField(required=False,allow_null=True)

    class Meta:
        model = User
        fields = ('id','first_name','last_name','cu_phone_no','cu_emp_code','sap_personnel_no',
                'created_by','cu_profile_img','hod','grade','mmr_module_id','mmr_type','reporting_head',
                'reporting_head_name','hod_name','grade_name','joining_date','daily_loginTime','daily_logoutTime',
                'lunch_start','lunch_end','company','cost_centre','cu_punch_id','salary_type',
                'cu_alt_email_id','job_location_state','department','designation','sub_department')

    def create(self,validated_data):
        try:

            cu_phone_no = validated_data.pop('cu_phone_no')if 'cu_phone_no' in validated_data else ''

            cu_punch_id = validated_data.pop('cu_punch_id')if 'cu_punch_id' in validated_data else ''
            cu_emp_code = validated_data.pop('cu_emp_code') if 'cu_emp_code' in validated_data else ''

            hod = validated_data.pop('hod') if 'hod' in validated_data else ''

            company=validated_data.pop('company') if 'company' in validated_data else ''
            cost_centre=validated_data.pop('cost_centre') if 'cost_centre' in validated_data else ''

            #print('cost_centre',cost_centre)
            #print('grade',type(validated_data.get('grade')),validated_data.get('grade'))
            grade = '' if validated_data.get('grade') == 'null' else validated_data.pop('grade')
            #print('grade',type(grade),grade)
            cu_profile_img=validated_data.pop('cu_profile_img') if 'cu_profile_img' in validated_data else ''
            print('valid111ated_data111',validated_data)

            sap_personnel_no = validated_data.pop('sap_personnel_no')
            sap_personnel_no = None if sap_personnel_no == 'null' else sap_personnel_no

            print('sap_personnel_no',sap_personnel_no,type(sap_personnel_no))
            mmr_module_id= validated_data.pop('mmr_module_id') if 'mmr_module_id' in validated_data else ''
            mmr_type =  validated_data.pop('mmr_type') if 'mmr_type' in validated_data else ''
            reporting_head = validated_data.pop('reporting_head') if 'reporting_head' in validated_data else ''
            joining_date = validated_data.pop('joining_date') if 'joining_date' in validated_data else None
            joining_date = datetime.datetime.strptime(joining_date, "%Y-%m-%dT%H:%M:%S.%fZ")

            salary_type = validated_data.pop('salary_type')
            salary_type = '' if salary_type == 'null' else salary_type


            cu_alt_email_id = validated_data.pop('cu_alt_email_id')
            cu_alt_email_id = None if cu_alt_email_id == 'null' else cu_alt_email_id

            job_location_state=validated_data.pop('job_location_state') if 'job_location_state' in validated_data else ''
            department = validated_data.pop('department')
            designation = validated_data.pop('designation')

            sub_department = validated_data.pop('sub_department')
            sub_department = None if sub_department == 'null' else sub_department

            logdin_user_id = self.context['request'].user.id
            role_details_list=[]
            with transaction.atomic():

                username_generate = validated_data.get('first_name') + validated_data.get('last_name')
                check_user_exist = User.objects.filter(username = username_generate)
                if check_user_exist:
                    username_generate = username_generate+str(random.randint(1,6))
                print('username_generate',username_generate)
                print('last_name',type(validated_data.get('last_name')),validated_data.get('last_name'))
                if validated_data.get('last_name') != 'null':
                    last_name_c = validated_data.get('last_name')
                else:
                    last_name_c = ''
                print('last_name_c',last_name_c)
                user=User.objects.create(first_name=validated_data.get('first_name'),
                                        last_name=last_name_c,
                                        username=username_generate,
                                        )
                print('user',user)
                '''
                    Modified by Rupam Hazra to set default password
                '''
                password = 'Shyam@123'
                user.set_password(password)
                user.save()

                user_detail = TCoreUserDetail.objects.create(
                                                            cu_user=user,
                                                           cu_phone_no=cu_phone_no,
                                                           cu_profile_img=cu_profile_img,
                                                           password_to_know=password,
                                                           cu_emp_code=cu_emp_code,
                                                           sap_personnel_no=sap_personnel_no,
                                                           daily_loginTime=validated_data.get('daily_loginTime'),
                                                           daily_logoutTime=validated_data.get('daily_logoutTime'),
                                                           lunch_start=validated_data.get('lunch_start'),
                                                           lunch_end=validated_data.get('lunch_end'),
                                                           hod_id=hod,
                                                           reporting_head_id=reporting_head,
                                                           joining_date= joining_date,
                                                           cu_created_by_id=logdin_user_id,
                                                           employee_grade_id=grade,
                                                           company_id=company,
                                                           cost_centre=cost_centre,
                                                           cu_punch_id=cu_punch_id,
                                                           salary_type_id=salary_type,
                                                           job_location_state_id=job_location_state,
                                                           cu_alt_email_id = cu_alt_email_id,
                                                           department_id = department,
                                                           designation_id = designation,
                                                           sub_department_id =sub_department,
                                                           granted_cl = float(10),
                                                           granted_el = float(15),
                                                           granted_sl = float(7)
                                                           )
                #print('user_detail',user_detail)
                role_user=TMasterModuleRoleUser.objects.create(mmr_module_id=mmr_module_id,
                                                               mmr_type = mmr_type,
                                                               mmr_user = user,
                                                               mmr_created_by = validated_data['created_by']
                                                              )

                joining_date=joining_date.date()
                #print('joining_date',joining_date)
                joining_year=joining_date.year
                #print('joining_year',joining_year)
                leave_filter={}


                total_month_grace=AttendenceMonthMaster.objects.filter(month_start__date__lte=joining_date,
                                month_end__date__gte=joining_date,is_deleted=False).values('grace_available',
                                                                            'year_start_date',
                                                                            'year_end_date',
                                                                            'month',
                                                                            'month_start',
                                                                            'month_end')
                granted_cl = 10
                granted_el = 15
                granted_sl = 7
                print('total_month_grace',total_month_grace)
                if total_month_grace:
                    year_end_date=total_month_grace[0]['year_end_date'].date()
                    total_days=(year_end_date - joining_date).days
                    print('total_days',total_days)
                    # calculated_cl=round((total_days/365)* int(granted_cl))
                    leave_filter['cl']=round_calculation(total_days,granted_cl)
                    # calculated_el=round((total_days/365)* int(granted_el))
                    leave_filter['el']=round_calculation(total_days,granted_el)
                    if granted_sl:
                        # calculated_sl=round((total_days/365)* int(granted_sl))
                        # print('calculated_sl',calculated_sl)
                        leave_filter['sl']=round_calculation(total_days,granted_sl)
                    else:
                        leave_filter['sl']=None

                    month_start_date=total_month_grace[0]['month_start'].date()
                    month_end_date=total_month_grace[0]['month_end'].date()
                    # print('month_start_date',month_start_date,month_end_date)
                    month_days=(month_end_date-month_start_date).days
                    # print('month_days',month_days)
                    remaining_days=(month_end_date-joining_date).days
                    # print('remaining_days',remaining_days)
                    # available_grace=round(total_month_grace[0]['grace_available']/remaining_days)
                    available_grace = round((remaining_days/month_days)*int(total_month_grace[0]['grace_available']))
                    print('available_grace',available_grace)
                    print(total_month_grace[0]['year_start_date'])
                    print(joining_date)
                    if total_month_grace[0]['year_start_date'].date() < joining_date:

                        JoiningApprovedLeave.objects.get_or_create(employee=user,
                                                            year=joining_year,
                                                            month=total_month_grace[0]['month'],
                                                            **leave_filter,
                                                            first_grace=available_grace,
                                                            created_by=user,
                                                            owned_by=user
                                                            )
                        print('sdddsdsdsd11213231')


                if cu_alt_email_id:

                    #============= Mail Send ==============#

                    # Send mail to employee with login details
                    mail_data = {
                                "name": user.first_name+ '' + user.last_name,
                                "user": username_generate,
                                "pass": password
                        }
                    #print('mail_data',mail_data)
                    mail_class = GlobleMailSend('EMP001', [cu_alt_email_id])
                    mail_thread = Thread(target = mail_class.mailsend, args = (mail_data,))
                    mail_thread.start()

                    # Send mail to who added the employee
                    add_cu_alt_email_id = TCoreUserDetail.objects.filter(cu_user=self.context['request'].user)[0]

                    if add_cu_alt_email_id.cu_alt_email_id:
                        mail_data = {
                                    "name": self.context['request'].user.first_name+ ' ' + self.context['request'].user.last_name,
                                    "user": username_generate,
                                    "pass": password
                            }
                        #print('mail_data',mail_data)
                        mail_class = GlobleMailSend('EMPA001', [add_cu_alt_email_id.cu_alt_email_id])
                        mail_thread = Thread(target = mail_class.mailsend, args = (mail_data,))
                        mail_thread.start()

                data = {
                    'id': user.id,
                    'first_name':user.first_name,
                    'last_name':user.last_name,
                    'username':user.username,
                    'cu_emp_code': user_detail.cu_emp_code,

                  }
                print('data',data)
                return data

        except Exception as e:
            raise APIException({
                'request_status': 0,
                'msg': e
            })


class EmployeeEditSerializer(serializers.ModelSerializer):
    ##### Extra Fields for TCoreUserDetails #####################
    cu_phone_no =serializers.CharField(required=False,allow_null=True)
    cu_alt_phone_no =serializers.CharField(required=False,allow_null=True)
    cu_alt_email_id=serializers.CharField(required=False,allow_null=True)
    cu_emp_code =serializers.CharField(required=False,allow_null=True)
    cu_punch_id = serializers.CharField(required=False,allow_null=True)
    cu_profile_img=serializers.ImageField(required=False,allow_null=True)
    sap_personnel_no=serializers.CharField(required=False,allow_null=True)
    initial_ctc=serializers.CharField(required=False,allow_null=True)
    current_ctc=serializers.CharField(required=False,allow_null=True)
    cost_centre=serializers.CharField(required=False,allow_null=True)
    address =serializers.CharField(required=False,allow_null=True)
    blood_group=serializers.CharField(required=False,allow_null=True)
    total_experience=serializers.CharField(required=False,allow_null=True)
    job_description =serializers.CharField(required=False,allow_null=True)
    company=serializers.CharField(required=False,allow_null=True)
    granted_cl=serializers.CharField(required=False,allow_null=True)
    granted_sl=serializers.CharField(required=False,allow_null=True)
    granted_el=serializers.CharField(required=False,allow_null=True)
    hod = serializers.CharField(required=False,allow_null=True)
    reporting_head = serializers.CharField(required=False)
    designation = serializers.CharField(required=False,allow_null=True)
    department = serializers.CharField(required=False,allow_null=True)
    daily_loginTime=serializers.CharField(required=False,allow_null=True)
    daily_logoutTime=serializers.CharField(required=False,allow_null=True)
    lunch_start=serializers.CharField(required=False,allow_null=True)
    lunch_end=serializers.CharField(required=False,allow_null=True)
    saturday_off=serializers.DictField(required=False)
    salary_type= serializers.CharField(required=False,allow_null=True)
    is_confirm =  serializers.BooleanField(required=False)
    termination_date =serializers.CharField(required=False)
    ##### Extra Fields for another tables #####################
    employee_grade = serializers.CharField(required=False,allow_null=True)
    mmr_module_id =serializers.CharField(required=False,allow_null=True)
    mmr_type=serializers.CharField(required=False,allow_null=True)
    benefit_provided = serializers.ListField(required=False,allow_null=True)
    other_facilities = serializers.ListField(required=False,allow_null=True)

    '''
        Added by Rupam Hazra [13.02.2020] as per details confirmation
    '''
    job_location = serializers.CharField(required = False, allow_null=True)
    job_location_state = serializers.CharField(required=False,allow_null=True)
    source = serializers.CharField(required = False, allow_null=True)
    source_name = serializers.CharField(required = False, allow_null=True)
    bank_account = serializers.CharField(required = False, allow_null=True)
    ifsc_code = serializers.CharField(required = False, allow_null=True)
    branch_name = serializers.CharField(required = False, allow_null=True)
    pincode = serializers.CharField(required = False, allow_null=True)
    emergency_contact_no = serializers.CharField(required = False,allow_null=True)
    father_name = serializers.CharField(required = False,allow_null=True)
    pan_no = serializers.CharField(required = False,allow_null=True)
    aadhar_no = serializers.CharField(required = False,allow_null=True)
    uan_no = serializers.CharField(required = False,allow_null=True)
    pf_no = serializers.CharField(required = False,allow_null=True)
    esic_no = serializers.CharField(required = False,allow_null=True)
    marital_status = serializers.CharField(required = False,allow_null=True)
    salary_per_month=serializers.CharField(required = False,allow_null=True)
    cu_dob = serializers.CharField(required=False,allow_null=True)
    resignation_date = serializers.CharField(required=False,allow_null=True)
    cu_gender = serializers.CharField(required=False,allow_null=True)
    is_auto_od = serializers.BooleanField(required=False)
    sub_department = serializers.CharField(required=False,allow_null=True)
    attendance_type = serializers.CharField(required=False,allow_null=True)

    class Meta:
        model = User
        fields=('id','first_name','last_name','email',
        'employee_grade','department','cu_profile_img','termination_date',
        'reporting_head','designation','benefit_provided','other_facilities','is_confirm',
        'hod','blood_group','company','granted_cl','granted_sl','granted_el','salary_type',
        'job_description','total_experience','address','cost_centre','saturday_off','cu_punch_id',
        'current_ctc','initial_ctc','sap_personnel_no','cu_emp_code','cu_alt_email_id','cu_alt_phone_no',
        'cu_phone_no','mmr_module_id',"mmr_type",'daily_loginTime','daily_logoutTime','lunch_start','lunch_end',
        'cu_dob','job_location','job_location_state','source','source_name','bank_account','ifsc_code','branch_name',
        'pincode','emergency_contact_no','father_name','pan_no','aadhar_no','uan_no','pf_no','esic_no',
        'marital_status','salary_per_month','resignation_date','cu_gender','is_auto_od','sub_department','attendance_type')




    def update(self,instance,validated_data):
        try:
            print('validated_data',validated_data)
            list_type = self.context['request'].query_params.get('list_type', None)
            logdin_user_id = self.context['request'].user.id
            blood_group=validated_data.get('blood_group') if validated_data.get('blood_group') else ""
            total_experience=validated_data.get('total_experience') if validated_data.get('total_experience') else ""
            address=validated_data.get('address') if validated_data.get('address') else ""
            cu_profile_img=validated_data.get('cu_profile_img') if validated_data.get('cu_profile_img') else ""
            cu_alt_phone_no=validated_data.get('cu_alt_phone_no') if validated_data.get('cu_alt_phone_no') else ""
            cu_alt_email_id= validated_data.get('cu_alt_email_id') if  validated_data.get('cu_alt_email_id') else ""
            cu_emp_code=validated_data.get('cu_emp_code') if validated_data.get('cu_emp_code') else ""
            cu_punch_id = validated_data.get('cu_punch_id') if validated_data.get('cu_punch_id') else ""
            job_description=validated_data.get('job_description') if validated_data.get('job_description') else ""
            cu_phone_no=validated_data.get('cu_phone_no') if validated_data.get('cu_phone_no') else ""
            company=validated_data.get('company') if validated_data.get('company') else ""
            hod=validated_data.get('hod') if validated_data.get('hod') else ""
            reporting_head=validated_data.get('reporting_head') if validated_data.get('reporting_head') else ""
            department=validated_data.get('department') if validated_data.get('department') else ""
            designation=validated_data.get('designation') if validated_data.get('designation') else ""
            current_ctc=validated_data.get('current_ctc') if validated_data.get('current_ctc') else ""
            initial_ctc=validated_data.get('initial_ctc') if validated_data.get('initial_ctc') else ""
            sap_personnel_no= None if validated_data.get('sap_personnel_no') == 'null' else validated_data.get('sap_personnel_no')
            cost_centre=validated_data.get('cost_centre') if validated_data.get('cost_centre') else ""
            granted_cl=validated_data.get('granted_cl') if validated_data.get('granted_cl') else 0.0
            granted_el=validated_data.get('granted_el') if validated_data.get('granted_el') else 0.0
            granted_sl=validated_data.get('granted_sl') if validated_data.get('granted_sl') else 0.0
            daily_loginTime=validated_data.get('daily_loginTime') if validated_data.get('daily_loginTime') else None
            daily_logoutTime=validated_data.get('daily_logoutTime') if validated_data.get('daily_logoutTime') else None
            lunch_start=validated_data.get('lunch_start') if validated_data.get('lunch_start') else None
            lunch_end=validated_data.get('lunch_end') if validated_data.get('lunch_end') else None
            saturday_off=validated_data.get('saturday_off') if validated_data.get('saturday_off') else None
            salary_type = validated_data.get('salary_type') if validated_data.get('salary_type') else None
            attendance_type = validated_data.get('attendance_type') if validated_data.get('attendance_type') else None
            is_confirm = validated_data.get('is_confirm')
            termination_date=validated_data.get('termination_date') if validated_data.get('termination_date') else None
            is_auto_od=validated_data.get('is_auto_od') if validated_data.get('is_auto_od') else False
            sub_department=validated_data.get('sub_department') if validated_data.get('sub_department') else None

            '''
                Added by Rupam Hazra [13.02.2020] as perdetails
            '''
            # job_location=validated_data.get('job_location') if validated_data.get('job_location') else None
            job_location_state = validated_data.get('job_location_state') if validated_data.get('job_location_state') else None
            # source=validated_data.get('source') if validated_data.get('source') else None
            # source_name=validated_data.get('source_name') if validated_data.get('source_name') else None
            # bank_account=validated_data.get('bank_account') if validated_data.get('bank_account') else None
            # ifsc_code=validated_data.get('ifsc_code') if validated_data.get('ifsc_code') else None
            # branch_name=validated_data.get('branch_name') if validated_data.get('branch_name') else None
            # pincode=validated_data.get('pincode') if validated_data.get('pincode') else None
            # emergency_contact_no=validated_data.get('emergency_contact_no') if validated_data.get('emergency_contact_no') else None
            # father_name=validated_data.get('father_name') if validated_data.get('father_name') else None
            # pan_no=validated_data.get('pan_no') if validated_data.get('pan_no') else None
            # aadhar_no=validated_data.get('aadhar_no') if validated_data.get('aadhar_no') else None
            # uan_no=validated_data.get('uan_no') if validated_data.get('uan_no') else None
            # pf_no=validated_data.get('pf_no') if validated_data.get('pf_no') else None
            # esic_no=validated_data.get('esic_no') if validated_data.get('esic_no') else None
            # marital_status=validated_data.get('marital_status') if validated_data.get('marital_status') else None
            # salary_per_month=validated_data.get('salary_per_month') if validated_data.get('salary_per_month') else None

            resignation_date= validated_data.get('resignation_date') if validated_data.get('resignation_date') else None

            print('resignation_date',resignation_date,type(resignation_date))
            with transaction.atomic():
                if list_type == "personal": ### Checking for Personal
                    '''
                        Reason : Adding many fields on Employee Edit
                        Author : Rupam Hazra
                        Date : 19/02/2020
                        Line Number : 582
                    '''
                    cu_dob = None if validated_data.get('cu_dob')== 'null' else validated_data.get('cu_dob')
                    bank_account = None if validated_data.get('bank_account') == 'null' else validated_data.get('bank_account')
                    ifsc_code = None if validated_data.get('ifsc_code') == 'null' else validated_data.get('ifsc_code')
                    branch_name = None if validated_data.get('branch_name') == 'null' else validated_data.get('branch_name')
                    cu_gender = None if validated_data.get('cu_gender') == 'null' else validated_data.get('cu_gender')
                    state = None if validated_data.get('state') == 'null' else validated_data.get('state')
                    pincode = None if validated_data.get('pincode') == 'null' else validated_data.get('pincode')
                    emergency_contact_no = None if validated_data.get('emergency_contact_no') == 'null' else validated_data.get('emergency_contact_no')
                    father_name = None if validated_data.get('father_name') == 'null' else validated_data.get('father_name')
                    pan_no = None if validated_data.get('pan_no') == 'null' else validated_data.get('pan_no')
                    aadhar_no = None if validated_data.get('aadhar_no') == 'null' else validated_data.get('aadhar_no')
                    uan_no = None if validated_data.get('uan_no') == 'null' else validated_data.get('uan_no')
                    marital_status = None if validated_data.get('marital_status') == 'null' else validated_data.get('marital_status')

                    instance.first_name = validated_data['first_name']
                    instance.last_name = validated_data['last_name']
                    instance.email = validated_data['email']
                    instance.save()

                    user_details=TCoreUserDetail.objects.filter(cu_user=instance.id,cu_is_deleted=False)
                    for det in user_details:
                        det.blood_group = blood_group
                        det.total_experience = total_experience
                        det.cu_phone_no = cu_phone_no
                        det.cu_emp_code=cu_emp_code
                        det.address = address
                        det.cu_updated_by_id=logdin_user_id
                        det.job_location_state_id=job_location_state
                        det.cu_alt_email=cu_alt_email_id
                        existing_image='./media/' + str(det.cu_profile_img)
                        if cu_profile_img:
                            if os.path.isfile(existing_image):
                                os.remove(existing_image)
                            det.cu_profile_img = cu_profile_img
                            # print('det.cu_profile_img',det.cu_profile_img)
                        det.save()
                        instance.__dict__['cu_profile_img'] = det.cu_profile_img



                    instance.__dict__['cu_phone_no'] = cu_phone_no
                    instance.__dict__['cu_emp_code'] = cu_emp_code
                    instance.__dict__['address'] = address
                    instance.__dict__['blood_group'] = blood_group
                    instance.__dict__['total_experience'] = total_experience
                    instance.__dict__['cu_alt_email_id'] = cu_alt_email_id
                    instance.__dict__['job_location_state'] = job_location_state

                elif list_type == "role": ### Checking for Role

                    instance.first_name = validated_data['first_name']
                    instance.last_name = validated_data['last_name']
                    instance.save()

                    # print("termination_date",termination_date )
                    if termination_date:
                        # print("hsgdhhfgs", datetime.datetime.strptime(termination_date, "%Y-%m-%dT%H:%M:%S.%fZ"))
                        termination_date = datetime.datetime.strptime(termination_date, "%Y-%m-%dT%H:%M:%S.%fZ")
                    if resignation_date:
                        resignation_date = datetime.datetime.strptime(resignation_date, "%Y-%m-%dT%H:%M:%S.%fZ")

                    TCoreUserDetail.objects.filter(cu_user=instance.id,cu_is_deleted=False).update(
                        cu_alt_phone_no = cu_alt_phone_no,
                        cu_alt_email_id = cu_alt_email_id,
                        cu_emp_code =cu_emp_code,
                        company = company,
                        job_description = job_description,
                        hod=hod,
                        reporting_head_id=reporting_head,
                        department_id=department,
                        sub_department_id = sub_department,
                        designation_id=designation,
                        cu_updated_by=logdin_user_id,
                        employee_grade = validated_data['employee_grade'],
                        termination_date= termination_date,
                        resignation_date=resignation_date,
                        is_auto_od = is_auto_od,
                        attendance_type = attendance_type
                    )

                    '''
                        [  Removed By Rupam Hazra 22.01.2020 line 351-364 ]
                    '''
                    # if TMasterModuleRoleUser.objects.filter(mmr_user=instance,mmr_is_deleted=False):
                    #     TMasterModuleRoleUser.objects.filter(mmr_user=instance,mmr_is_deleted=False).update(
                    #                                                             mmr_module_id=validated_data['mmr_module_id'],
                    #                                                             mmr_type=validated_data['mmr_type'],
                    #                                                             mmr_updated_by=logdin_user_id
                    #                                                             )
                    # else:
                    #     TMasterModuleRoleUser.objects.create(
                    #         mmr_user=instance,
                    #         mmr_module_id=validated_data['mmr_module_id'],
                    #         mmr_type=validated_data['mmr_type'],
                    #         mmr_designation_id=designation,
                    #         mmr_created_by_id=logdin_user_id
                    #         )

                    core_details=TCoreUserDetail.objects.filter(cu_user=instance.id,cu_is_deleted=False).values(
                        'reporting_head','cu_alt_phone_no', 'cu_emp_code', 'cu_alt_email_id','designation','department','job_description',
                        'hod','company','termination_date','attendance_type')
                    instance.__dict__['cu_alt_phone_no'] =core_details[0]['cu_alt_phone_no'] if core_details[0]['cu_alt_phone_no'] else ''
                    instance.__dict__['cu_alt_email_id'] = core_details[0]['cu_alt_email_id'] if core_details[0]['cu_alt_email_id'] else ''
                    instance.__dict__['cu_emp_code'] = core_details[0]['cu_emp_code'] if core_details[0]['cu_emp_code'] else ''
                    instance.__dict__['employee_grade'] = validated_data['employee_grade']
                    instance.__dict__['designation'] = core_details[0]['designation'] if core_details[0]['designation'] else ''
                    instance.__dict__['department'] = core_details[0]['department']  if core_details[0]['department'] else ''
                    instance.__dict__['job_description'] = core_details[0]['job_description'] if core_details[0]['job_description'] else ''
                    instance.__dict__['hod'] = core_details[0]['hod'] if core_details[0]['hod'] else ''
                    instance.__dict__['reporting_head'] = core_details[0]['reporting_head'] if core_details[0]['reporting_head'] else ''
                    instance.__dict__['company'] = core_details[0]['company'] if core_details[0]['company'] else ''
                    instance.__dict__['mmr_module_id'] = validated_data['mmr_module_id']
                    instance.__dict__['mmr_type'] = validated_data['mmr_type']
                    instance.__dict__['termination_date'] =core_details[0]['termination_date'] if core_details[0]['termination_date'] else None
                    instance.__dict__['attendance_type'] =core_details[0]['attendance_type'] if core_details[0]['attendance_type'] else None

                elif list_type == "professional": ### Checking for Professional
                    '''
                        Reason : Adding many fields on Employee Edit
                        Author : Rupam Hazra
                        Date : 19/02/2020
                        Line Number : 582
                    '''



                    instance.first_name = validated_data['first_name']
                    instance.last_name = validated_data['last_name']
                    instance.save()

                    TCoreUserDetail.objects.filter(cu_user=instance.id,cu_is_deleted=False).update(
                        current_ctc = current_ctc,
                        cu_emp_code = cu_emp_code,
                        cu_punch_id = cu_punch_id,
                        initial_ctc = initial_ctc,
                        sap_personnel_no = sap_personnel_no,
                        cost_centre =cost_centre,
                        granted_cl= granted_cl,
                        granted_el= granted_el,
                        granted_sl= granted_sl,
                        daily_loginTime=datetime.datetime.strptime(daily_loginTime,"%H:%M:%S"),
                        daily_logoutTime=datetime.datetime.strptime(daily_logoutTime,"%H:%M:%S"),
                        lunch_start=datetime.datetime.strptime(lunch_start,"%H:%M:%S"),
                        lunch_end=datetime.datetime.strptime(lunch_end,"%H:%M:%S"),
                        salary_type=salary_type,
                        is_confirm=is_confirm,
                        cu_updated_by=logdin_user_id
                    )
                    if saturday_off:
                        prev_sat_data=AttendenceSaturdayOffMaster.objects.filter(employee=instance,is_deleted=False)
                        # print('prev_sat_data',prev_sat_data)
                        if prev_sat_data:
                            for p_s in prev_sat_data:
                                p_s.first=saturday_off['first']
                                p_s.second=saturday_off['second']
                                p_s.third=saturday_off['third']
                                p_s.fourth=saturday_off['fourth']
                                p_s.all_s_day=saturday_off['all_s_day']
                                p_s.updated_by_id=logdin_user_id
                                p_s.save()
                            AttendenceSaturdayOffLogMaster.objects.create(employee=instance,
                                                                         **saturday_off,
                                                                         updated_by_id=logdin_user_id,
                                                                        )
                        else:
                            saturday_data=AttendenceSaturdayOffMaster.objects.create(employee=instance,
                                                                                    **saturday_off,
                                                                                    created_by_id=logdin_user_id,
                                                                                    owned_by_id=logdin_user_id
                                                                                    )

                            # print('saturday_data',saturday_data)
                            AttendenceSaturdayOffLogMaster.objects.create(employee=instance,
                                                                         **saturday_off,
                                                                         created_by_id=logdin_user_id,
                                                                         owned_by_id=logdin_user_id
                                                                        )

                    leave_filter={}
                    '''
                        Reason : Change functionality adn add this code employee add portion
                        Author : Rupam Hazra
                        Date : 19/02/2020
                        Line Number : 657 - 706
                    '''
                    # joining_date_details=TCoreUserDetail.objects.filter(cu_user=instance.id,cu_is_deleted=False).values('joining_date')
                    # if joining_date_details:
                    #     joining_date=joining_date_details[0]['joining_date'].date()
                    #     joining_year=joining_date.year
                    #     # print('joining_year',joining_year)


                    #     total_month_grace=AttendenceMonthMaster.objects.filter(month_start__date__lte=joining_date,
                    #                     month_end__date__gte=joining_date,is_deleted=False).values('grace_available',
                    #                                                              'year_start_date',
                    #                                                              'year_end_date',
                    #                                                              'month',
                    #                                                              'month_start',
                    #                                                              'month_end'
                    #                                                              )
                    #     if total_month_grace:
                    #         year_end_date=total_month_grace[0]['year_end_date'].date()
                    #         total_days=(year_end_date - joining_date).days
                    #         # print('total_days',total_days)
                    #         calculated_cl=round((total_days/365)* int(granted_cl))
                    #         leave_filter['cl']=calculated_cl
                    #         calculated_el=round((total_days/365)* int(granted_el))
                    #         leave_filter['el']=calculated_el
                    #         if granted_sl:
                    #             calculated_sl=round((total_days/365)* int(granted_sl))
                    #             # print('calculated_sl',calculated_sl)
                    #             leave_filter['sl']=calculated_sl
                    #         else:
                    #             leave_filter['sl']=None

                    #         month_start_date=total_month_grace[0]['month_start'].date()
                    #         month_end_date=total_month_grace[0]['month_end'].date()
                    #         # print('month_start_date',month_start_date,month_end_date)
                    #         month_days=(month_end_date-month_start_date).days
                    #         # print('month_days',month_days)
                    #         remaining_days=(month_end_date-joining_date).days
                    #         # print('remaining_days',remaining_days)
                    #         # available_grace=round(total_month_grace[0]['grace_available']/remaining_days)
                    #         available_grace = round((remaining_days/month_days)*int(total_month_grace[0]['grace_available']))
                    #         # print('available_grace',available_grace)

                    #         if total_month_grace[0]['year_start_date']<joining_date_details[0]['joining_date']:
                    #             JoiningApprovedLeave.objects.get_or_create(employee_id=instance.id,
                    #                                                 year=joining_year,
                    #                                                 month=total_month_grace[0]['month'],
                    #                                                 **leave_filter,
                    #                                                 first_grace=available_grace,
                    #                                                 created_by_id=logdin_user_id,
                    #                                                 owned_by_id=logdin_user_id
                    #                                                 )


                    instance.__dict__['cu_emp_code'] =cu_emp_code
                    instance.__dict__['cu_punch_id'] =cu_punch_id
                    instance.__dict__['current_ctc'] = current_ctc
                    instance.__dict__['initial_ctc'] = initial_ctc
                    instance.__dict__['sap_personnel_no'] = sap_personnel_no
                    instance.__dict__['cost_centre'] = cost_centre
                    instance.__dict__['granted_cl'] = granted_cl
                    instance.__dict__['granted_el'] = granted_el
                    instance.__dict__['granted_sl'] = granted_sl
                    instance.__dict__['daily_loginTime'] = daily_loginTime
                    instance.__dict__['daily_logoutTime'] = daily_logoutTime
                    instance.__dict__['lunch_start'] = lunch_start
                    instance.__dict__['lunch_end'] = lunch_end
                    instance.__dict__['saturday_off'] = saturday_off
                    instance.__dict__['salary_type'] = salary_type
                    instance.__dict__['is_confirm'] = is_confirm

                    benefit_provided_details = validated_data.pop('benefit_provided') if 'benefit_provided' in validated_data else None
                    if benefit_provided_details:
                        benefits = HrmsUsersBenefits.objects.filter(user=instance,is_deleted=False)
                        if benefits:
                            benefits.delete()

                        benefits_list = []
                        for get_benefit in benefit_provided_details:
                            create_benefit = HrmsUsersBenefits.objects.create(
                                user_id = str(instance.id),
                                benefits_id = get_benefit['benefits'],
                                allowance=get_benefit['allowance'],
                                created_by_id = logdin_user_id
                            )
                            create_benefit.__dict__.pop('_state') if '_state' in create_benefit.__dict__.keys() else create_benefit.__dict__
                            benefits_list.append(create_benefit.__dict__)
                        instance.__dict__['benefit_provided'] = benefits_list
                    elif benefit_provided_details is None:
                        benefits = HrmsUsersBenefits.objects.filter(user=instance,is_deleted=False)
                        if benefits:
                            benefits.delete()
                    else:
                        instance.__dict__['benefit_provided'] = None

                    other_facilities_details = validated_data.pop('other_facilities') if 'other_facilities' in validated_data else None
                    if other_facilities_details:
                        facilities = HrmsUsersOtherFacilities.objects.filter(user=instance,is_deleted=False)
                        if facilities:
                            facilities.delete()
                        facility_list = []
                        for get_facility in other_facilities_details:
                            create_facilities = HrmsUsersOtherFacilities.objects.create(
                                user_id = str(instance.id),
                                other_facilities= get_facility['facilities'],
                                created_by_id = logdin_user_id
                            )
                            create_facilities.__dict__.pop('_state') if '_state' in create_facilities.__dict__.keys() else create_facilities.__dict__
                            facility_list.append(create_facilities.__dict__)
                        instance.__dict__['other_facilities'] = facility_list
                    elif other_facilities_details is None:
                        facilities = HrmsUsersOtherFacilities.objects.filter(user=instance,is_deleted=False)
                        if facilities:
                            facilities.delete()
                    else:
                        instance.__dict__['other_facilities'] = None

                return instance.__dict__
        except Exception as e:
            raise e


class EmployeeEditSerializerV2(serializers.ModelSerializer):
    ##### Extra Fields for TCoreUserDetails #####################
    cu_phone_no =serializers.CharField(required=False,allow_null=True)
    cu_alt_phone_no =serializers.CharField(required=False,allow_null=True)
    cu_alt_email_id=serializers.CharField(required=False,allow_null=True)
    cu_emp_code =serializers.CharField(required=False,allow_null=True)
    cu_punch_id = serializers.CharField(required=False,allow_null=True)
    cu_profile_img=serializers.ImageField(required=False,allow_null=True)
    sap_personnel_no=serializers.CharField(required=False,allow_null=True)
    initial_ctc=serializers.CharField(required=False,allow_null=True)
    current_ctc=serializers.CharField(required=False,allow_null=True)
    cost_centre=serializers.CharField(required=False,allow_null=True)
    address =serializers.CharField(required=False,allow_null=True)
    blood_group=serializers.CharField(required=False,allow_null=True)
    total_experience=serializers.CharField(required=False,allow_null=True)
    job_description =serializers.CharField(required=False,allow_null=True)
    company=serializers.CharField(required=False,allow_null=True)
    granted_cl=serializers.CharField(required=False,allow_null=True)
    granted_sl=serializers.CharField(required=False,allow_null=True)
    granted_el=serializers.CharField(required=False,allow_null=True)
    hod = serializers.CharField(required=False,allow_null=True)
    reporting_head = serializers.CharField(required=False)
    temp_reporting_heads = serializers.CharField(required=False,allow_null=True)
    designation = serializers.CharField(required=False,allow_null=True)
    department = serializers.CharField(required=False,allow_null=True)
    daily_loginTime=serializers.CharField(required=False,allow_null=True)
    daily_logoutTime=serializers.CharField(required=False,allow_null=True)
    lunch_start=serializers.CharField(required=False,allow_null=True)
    lunch_end=serializers.CharField(required=False,allow_null=True)
    saturday_off=serializers.DictField(required=False)
    salary_type= serializers.CharField(required=False,allow_null=True)
    is_confirm =  serializers.BooleanField(required=False)
    termination_date =serializers.CharField(required=False)
    ##### Extra Fields for another tables #####################
    employee_grade = serializers.CharField(required=False,allow_null=True)
    # 'allow_blank' field added by Shubhadeep
    employee_sub_grade = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    mmr_module_id =serializers.CharField(required=False,allow_null=True)
    mmr_type=serializers.CharField(required=False,allow_null=True)
    benefit_provided = serializers.ListField(required=False,allow_null=True)
    other_facilities = serializers.ListField(required=False,allow_null=True)

    '''
        Added by Rupam Hazra [13.02.2020] as per details confirmation
    '''
    job_location = serializers.CharField(required = False, allow_null=True)
    job_location_state = serializers.CharField(required=False,allow_null=True)
    source = serializers.CharField(required = False, allow_null=True)
    source_name = serializers.CharField(required = False, allow_null=True)
    bank_account = serializers.CharField(required = False, allow_null=True)
    ifsc_code = serializers.CharField(required = False, allow_null=True)
    branch_name = serializers.CharField(required = False, allow_null=True)
    pincode = serializers.CharField(required = False, allow_null=True)
    emergency_contact_no = serializers.CharField(required = False,allow_null=True)
    father_name = serializers.CharField(required = False,allow_null=True)
    pan_no = serializers.CharField(required = False,allow_null=True)
    aadhar_no = serializers.CharField(required = False,allow_null=True)
    uan_no = serializers.CharField(required = False,allow_null=True)
    pf_no = serializers.CharField(required = False,allow_null=True)
    esic_no = serializers.CharField(required = False,allow_null=True)
    marital_status = serializers.CharField(required = False,allow_null=True)
    salary_per_month=serializers.CharField(required = False,allow_null=True)
    # updated by Shubhadeep - doc was string before, it must be date
    cu_dob = serializers.DateField(required=False,allow_null=True)
    resignation_date = serializers.CharField(required=False,allow_null=True)
    cu_gender = serializers.CharField(required=False,allow_null=True)
    is_auto_od = serializers.BooleanField(required=False)
    sub_department = serializers.CharField(required=False,allow_null=True)
    attendance_type = serializers.CharField(required=False,allow_null=True)

    wbs_element = serializers.CharField(required=False,allow_null=True)
    retirement_date = serializers.CharField(required=False,allow_null=True)
    esi_dispensary = serializers.CharField(required=False,allow_null=True)
    emp_pension_no = serializers.CharField(required=False,allow_null=True)
    employee_voluntary_provident_fund_contribution = serializers.CharField(required=False,allow_null=True)
    care_of = serializers.CharField(required=False,allow_null=True)
    street_and_house_no = serializers.CharField(required=False,allow_null=True)
    address_2nd_line = serializers.CharField(required=False,allow_null=True)
    city = serializers.CharField(required=False,allow_null=True)
    district = serializers.CharField(required=False,allow_null=True)

    bus_facility = serializers.BooleanField(required=False)
    emergency_relationship = serializers.CharField(required=False,allow_null=True)
    emergency_contact_name = serializers.CharField(required=False,allow_null=True)

    has_pf = serializers.BooleanField(required=False)
    has_esi = serializers.BooleanField(required=False)
    bank_name_p = serializers.CharField(required=False,allow_null=True)

    state = serializers.CharField(required=False,allow_null=True)

    is_flexi_hour = serializers.BooleanField(required=False)
    is_transfer = serializers.BooleanField(required=False)

    class Meta:
        model = User
        fields=('id','first_name','last_name','email','is_active',
        'employee_grade','department','cu_profile_img','termination_date',
        'reporting_head','temp_reporting_heads','designation','benefit_provided','other_facilities','is_confirm',
        'hod','blood_group','company','granted_cl','granted_sl','granted_el','salary_type',
        'job_description','total_experience','address','cost_centre','saturday_off','cu_punch_id',
        'current_ctc','initial_ctc','sap_personnel_no','cu_emp_code','cu_alt_email_id','cu_alt_phone_no',
        'cu_phone_no','mmr_module_id',"mmr_type",'daily_loginTime','daily_logoutTime','lunch_start','lunch_end',
        'cu_dob','job_location','job_location_state','source','source_name','bank_account','ifsc_code','branch_name',
        'pincode','emergency_contact_no','father_name','pan_no','aadhar_no','uan_no','pf_no','esic_no',
        'marital_status','salary_per_month','resignation_date','cu_gender','is_auto_od','sub_department','attendance_type',
        'wbs_element', 'retirement_date', 'esi_dispensary', 'emp_pension_no',
        'employee_voluntary_provident_fund_contribution', 'care_of', 'street_and_house_no',
        'address_2nd_line', 'city', 'district','bus_facility','emergency_relationship',
        'emergency_contact_name','has_pf','has_esi','bank_name_p','state','is_flexi_hour','employee_sub_grade',
                'is_transfer')




    def update(self,instance,validated_data):
        try:
            #print('validated_data',validated_data)
            list_type = self.context['request'].query_params.get('list_type', None)
            logdin_user_id = self.context['request'].user.id
            is_transfer = validated_data.get('is_transfer') if validated_data.get('is_transfer') else ""
            blood_group=validated_data.get('blood_group') if validated_data.get('blood_group') else ""
            total_experience=validated_data.get('total_experience') if validated_data.get('total_experience') else ""
            address=validated_data.get('address') if validated_data.get('address') else ""
            cu_profile_img=validated_data.get('cu_profile_img') if validated_data.get('cu_profile_img') else ""
            cu_alt_phone_no=validated_data.get('cu_alt_phone_no') if validated_data.get('cu_alt_phone_no') else ""
            cu_alt_email_id= validated_data.get('cu_alt_email_id') if  validated_data.get('cu_alt_email_id') else ""
            cu_emp_code=validated_data.get('cu_emp_code') if validated_data.get('cu_emp_code') else ""
            cu_punch_id = validated_data.get('cu_punch_id') if validated_data.get('cu_punch_id') else ""
            job_description=validated_data.get('job_description') if validated_data.get('job_description') else ""
            cu_phone_no=validated_data.get('cu_phone_no') if validated_data.get('cu_phone_no') else ""
            company=validated_data.get('company') if validated_data.get('company') else ""
            hod=validated_data.get('hod') if validated_data.get('hod') else ""
            reporting_head=validated_data.get('reporting_head') if validated_data.get('reporting_head') else ""
            temp_reporting_heads=validated_data.get('temp_reporting_heads') if validated_data.get('temp_reporting_heads') else None
            department=validated_data.get('department') if validated_data.get('department') else ""
            designation=validated_data.get('designation') if validated_data.get('designation') else ""
            current_ctc=validated_data.get('current_ctc')
            initial_ctc=validated_data.get('initial_ctc')
            sap_personnel_no= None if validated_data.get('sap_personnel_no') == 'null' else validated_data.get('sap_personnel_no')
            cost_centre=validated_data.get('cost_centre') if validated_data.get('cost_centre') else ""
            granted_cl=validated_data.get('granted_cl') if validated_data.get('granted_cl') else 0.0
            granted_el=validated_data.get('granted_el') if validated_data.get('granted_el') else 0.0
            granted_sl=validated_data.get('granted_sl') if validated_data.get('granted_sl') else 0.0
            daily_loginTime=validated_data.get('daily_loginTime') if validated_data.get('daily_loginTime') else None
            daily_logoutTime=validated_data.get('daily_logoutTime') if validated_data.get('daily_logoutTime') else None
            lunch_start=validated_data.get('lunch_start') if validated_data.get('lunch_start') else None
            lunch_end=validated_data.get('lunch_end') if validated_data.get('lunch_end') else None
            saturday_off=validated_data.get('saturday_off') if validated_data.get('saturday_off') else None
            salary_type = int(validated_data.get('salary_type')) if validated_data.get('salary_type') else None
            attendance_type = validated_data.get('attendance_type') if validated_data.get('attendance_type') else None
            is_confirm = validated_data.get('is_confirm')
            termination_date=validated_data.get('termination_date') if validated_data.get('termination_date') else None
            is_auto_od=validated_data.get('is_auto_od') if validated_data.get('is_auto_od') else False
            sub_department=validated_data.get('sub_department') if validated_data.get('sub_department') else None

            care_of=validated_data.get('care_of') if validated_data.get('care_of') else None
            street_and_house_no=validated_data.get('street_and_house_no') if validated_data.get('street_and_house_no') else None
            address_2nd_line=validated_data.get('address_2nd_line') if validated_data.get('address_2nd_line') else None
            city=validated_data.get('city') if validated_data.get('city') else None
            district=validated_data.get('district') if validated_data.get('district') else None

            wbs_element=validated_data.get('wbs_element') if validated_data.get('wbs_element') else None
            retirement_date=validated_data.get('retirement_date') if validated_data.get('retirement_date') else None
            esic_no=validated_data.get('esic_no') if validated_data.get('esic_no') else None
            esi_dispensary=validated_data.get('esi_dispensary') if validated_data.get('esi_dispensary') else None
            pf_no=validated_data.get('pf_no') if validated_data.get('pf_no') else None
            emp_pension_no=validated_data.get('emp_pension_no') if validated_data.get('emp_pension_no') else None
            employee_voluntary_provident_fund_contribution=validated_data.get('employee_voluntary_provident_fund_contribution')

            '''
                Added by Rupam Hazra [13.02.2020] as perdetails
            '''
            job_location=validated_data.get('job_location') if validated_data.get('job_location') else None
            job_location_state = int(validated_data.get('job_location_state')) if validated_data.get('job_location_state') else None
            # source=validated_data.get('source') if validated_data.get('source') else None
            # source_name=validated_data.get('source_name') if validated_data.get('source_name') else None
            bank_account=validated_data.get('bank_account') if validated_data.get('bank_account') else None
            ifsc_code=validated_data.get('ifsc_code') if validated_data.get('ifsc_code') else None
            branch_name=validated_data.get('branch_name') if validated_data.get('branch_name') else None
            # pincode=validated_data.get('pincode') if validated_data.get('pincode') else None
            # emergency_contact_no=validated_data.get('emergency_contact_no') if validated_data.get('emergency_contact_no') else None
            father_name=validated_data.get('father_name') if validated_data.get('father_name') else None
            # pan_no=validated_data.get('pan_no') if validated_data.get('pan_no') else None
            # aadhar_no=validated_data.get('aadhar_no') if validated_data.get('aadhar_no') else None
            uan_no=validated_data.get('uan_no') if validated_data.get('uan_no') else None
            # pf_no=validated_data.get('pf_no') if validated_data.get('pf_no') else None
            # esic_no=validated_data.get('esic_no') if validated_data.get('esic_no') else None
            # marital_status=validated_data.get('marital_status') if validated_data.get('marital_status') else None
            # salary_per_month=validated_data.get('salary_per_month') if validated_data.get('salary_per_month') else None

            resignation_date= validated_data.get('resignation_date') if validated_data.get('resignation_date') else None
            bus_facility=validated_data.get('bus_facility') if validated_data.get('bus_facility') else False
            emergency_relationship = validated_data.get('emergency_relationship') if validated_data.get('emergency_relationship') else None
            emergency_contact_name = validated_data.get('emergency_contact_name') if validated_data.get('emergency_contact_name') else None

            has_pf=validated_data.get('has_pf') if validated_data.get('has_pf') else False
            has_esi=validated_data.get('has_esi') if validated_data.get('has_esi') else False
            bank_name_p=int(validated_data.get('bank_name_p')) if validated_data.get('bank_name_p') else None

            state = int(validated_data.get('state')) if validated_data.get('state') else None
            employee_sub_grade = int(validated_data.get("employee_sub_grade")) if validated_data.get("employee_sub_grade") else None
            # employee_grade = int(validated_data.get("employee_grade")) if validated_data.get("employee_grade") else None
            is_flexi_hour=validated_data.get('is_flexi_hour') if validated_data.get('is_flexi_hour') else False

            #print('resignation_date',resignation_date,type(resignation_date))
            with transaction.atomic():
                if list_type == "personal": ### Checking for Personal
                    '''
                        Reason : Adding many fields on Employee Edit
                        Author : Rupam Hazra
                        Date : 19/02/2020
                        Line Number : 582
                    '''
                    cu_dob = None if validated_data.get('cu_dob')== 'null' else validated_data.get('cu_dob')
                    bank_account = None if validated_data.get('bank_account') == 'null' else validated_data.get('bank_account')
                    ifsc_code = None if validated_data.get('ifsc_code') == 'null' else validated_data.get('ifsc_code')
                    branch_name = None if validated_data.get('branch_name') == 'null' else validated_data.get('branch_name')
                    cu_gender = None if validated_data.get('cu_gender') == 'null' else validated_data.get('cu_gender')
                    state = None if validated_data.get('state') == 'null' else validated_data.get('state')
                    pincode = None if validated_data.get('pincode') == 'null' else validated_data.get('pincode')
                    emergency_contact_no = None if validated_data.get('emergency_contact_no') == 'null' else validated_data.get('emergency_contact_no')
                    father_name = None if validated_data.get('father_name') == 'null' else validated_data.get('father_name')
                    pan_no = None if validated_data.get('pan_no') == 'null' else validated_data.get('pan_no')
                    aadhar_no = None if validated_data.get('aadhar_no') == 'null' else validated_data.get('aadhar_no')
                    uan_no = None if validated_data.get('uan_no') == 'null' else validated_data.get('uan_no')
                    marital_status = None if validated_data.get('marital_status') == 'null' else validated_data.get('marital_status')

                    instance.first_name = validated_data['first_name']
                    instance.last_name = validated_data['last_name']
                    instance.email = validated_data['email']
                    instance.save()

                    user_details=TCoreUserDetail.objects.filter(cu_user=instance.id,cu_is_deleted=False)
                    for det in user_details:
                        # if dob is set null, we won't rewrite it
                        det.cu_dob = cu_dob if cu_dob else det.cu_dob
                        det.blood_group = blood_group
                        det.total_experience = total_experience
                        det.cu_phone_no = cu_phone_no
                        det.cu_emp_code=cu_emp_code
                        det.address = address
                        det.cu_updated_by_id=logdin_user_id
                        det.cu_alt_email=cu_alt_email_id
                        existing_image='./media/' + str(det.cu_profile_img)
                        if cu_profile_img:
                            if os.path.isfile(existing_image):
                                os.remove(existing_image)
                            det.cu_profile_img = cu_profile_img
                            # #print('det.cu_profile_img',det.cu_profile_img)
                        det.care_of = care_of
                        det.street_and_house_no = street_and_house_no
                        det.address_2nd_line = address_2nd_line
                        det.city = city
                        det.district = district
                        det.aadhar_no=aadhar_no
                        det.pan_no=pan_no
                        det.cu_gender=cu_gender
                        det.pincode=pincode
                        det.emergency_relationship=emergency_relationship
                        det.emergency_contact_no=emergency_contact_no
                        det.emergency_contact_name=emergency_contact_name
                        det.marital_status=marital_status
                        det.father_name=father_name
                        det.state_id=state
                        # det.employee_sub_grade = employee_sub_grade
                        det.save()
                        instance.__dict__['cu_profile_img'] = det.cu_profile_img
                        #delete employee sub grade



                    instance.__dict__['cu_phone_no'] = cu_phone_no
                    instance.__dict__['cu_emp_code'] = cu_emp_code
                    instance.__dict__['cu_dob'] = cu_dob
                    instance.__dict__['address'] = address
                    instance.__dict__['blood_group'] = blood_group
                    instance.__dict__['total_experience'] = total_experience
                    instance.__dict__['cu_alt_email_id'] = cu_alt_email_id
                    instance.__dict__['job_location_state'] = job_location_state

                    instance.__dict__['care_of'] = care_of
                    instance.__dict__['street_and_house_no'] = street_and_house_no
                    instance.__dict__['address_2nd_line'] = address_2nd_line
                    instance.__dict__['city'] = city
                    instance.__dict__['district'] = district

                    instance.__dict__['aadhar_no'] = aadhar_no
                    instance.__dict__['pan_no'] = pan_no
                    instance.__dict__['cu_gender'] = cu_gender
                    instance.__dict__['pincode'] = pincode
                    instance.__dict__['emergency_relationship'] = emergency_relationship
                    instance.__dict__['emergency_contact_no'] = emergency_contact_no
                    instance.__dict__['emergency_contact_name'] = emergency_contact_name
                    instance.__dict__['marital_status'] = marital_status

                    instance.__dict__['father_name'] = father_name
                    instance.__dict__['state'] = state





                elif list_type == "role": ### Checking for Role

                    instance.first_name = validated_data['first_name']
                    instance.last_name = validated_data['last_name']
                    instance.save()

                    # #print("termination_date",termination_date )
                    if termination_date:
                        # #print("hsgdhhfgs", datetime.datetime.strptime(termination_date, "%Y-%m-%dT%H:%M:%S.%fZ"))
                        termination_date = datetime.datetime.strptime(termination_date, "%Y-%m-%dT%H:%M:%S.%fZ")
                    if resignation_date:
                        resignation_date = datetime.datetime.strptime(resignation_date, "%Y-%m-%dT%H:%M:%S.%fZ")

                    existed_ids = UserTempReportingHeadMap.objects.filter(user=instance, is_deleted=False).values_list('temp_reporting_head__id')
                    updated_ids = list()
                    if temp_reporting_heads:
                        updated_ids = list(map(int,temp_reporting_heads.split(',')))

                    deleted_ids = list(set(existed_ids)-set(updated_ids))
                    UserTempReportingHeadMap.objects.filter(user=instance, temp_reporting_head__in=deleted_ids).update(is_deleted=True)
                    added_ids = list(set(updated_ids)-set(existed_ids))
                    for added_id in added_ids:
                        UserTempReportingHeadMap.objects.create(
                            user=instance,
                            temp_reporting_head_id=added_id
                        )

                    TCoreUserDetail.objects.filter(cu_user=instance.id,cu_is_deleted=False).update(
                        cu_alt_phone_no = cu_alt_phone_no,
                        cu_alt_email_id = cu_alt_email_id,
                        cu_emp_code =cu_emp_code,
                        company = company,
                        job_description = job_description,
                        hod=hod,
                        reporting_head_id=reporting_head,
                        cost_centre=cost_centre,
                        updated_cost_centre_id=cost_centre,
                        # temp_reporting_head_id=temp_reporting_head,
                        department_id=department,
                        sub_department_id = sub_department,
                        designation_id=designation,
                        cu_updated_by=logdin_user_id,
                        # employee_grade = employee_grade,
                        employee_grade = validated_data['employee_grade'],
                        employee_sub_grade = employee_sub_grade,
                        termination_date= termination_date,
                        resignation_date=resignation_date,
                        is_auto_od = is_auto_od,
                        attendance_type = attendance_type,
                        is_flexi_hour=is_flexi_hour
                    )

                    '''
                        [  Removed By Rupam Hazra 22.01.2020 line 351-364 ]
                    '''
                    # if TMasterModuleRoleUser.objects.filter(mmr_user=instance,mmr_is_deleted=False):
                    #     TMasterModuleRoleUser.objects.filter(mmr_user=instance,mmr_is_deleted=False).update(
                    #                                                             mmr_module_id=validated_data['mmr_module_id'],
                    #                                                             mmr_type=validated_data['mmr_type'],
                    #                                                             mmr_updated_by=logdin_user_id
                    #                                                             )
                    # else:
                    #     TMasterModuleRoleUser.objects.create(
                    #         mmr_user=instance,
                    #         mmr_module_id=validated_data['mmr_module_id'],
                    #         mmr_type=validated_data['mmr_type'],
                    #         mmr_designation_id=designation,
                    #         mmr_created_by_id=logdin_user_id
                    #         )

                    core_details=TCoreUserDetail.objects.filter(cu_user=instance.id,cu_is_deleted=False).values(
                        'reporting_head','cu_alt_phone_no', 'cu_emp_code', 'cu_alt_email_id','designation','department','job_description',
                        'hod','company','termination_date','attendance_type', 'is_flexi_hour')
                    temp_reporting_heads = UserTempReportingHeadMap.objects.filter(user=instance,is_deleted=False).values('temp_reporting_head__id','temp_reporting_head__first_name','temp_reporting_head__last_name')

                    instance.__dict__['temp_reporting_heads'] =temp_reporting_heads if temp_reporting_heads else list()
                    instance.__dict__['cu_alt_phone_no'] =core_details[0]['cu_alt_phone_no'] if core_details[0]['cu_alt_phone_no'] else ''
                    instance.__dict__['cu_alt_email_id'] = core_details[0]['cu_alt_email_id'] if core_details[0]['cu_alt_email_id'] else ''
                    instance.__dict__['cu_emp_code'] = core_details[0]['cu_emp_code'] if core_details[0]['cu_emp_code'] else ''
                    instance.__dict__['employee_grade'] = validated_data['employee_grade']
                    instance.__dict__['employee_sub_grade'] = employee_sub_grade
                    instance.__dict__['designation'] = core_details[0]['designation'] if core_details[0]['designation'] else ''
                    instance.__dict__['department'] = core_details[0]['department']  if core_details[0]['department'] else ''
                    instance.__dict__['job_description'] = core_details[0]['job_description'] if core_details[0]['job_description'] else ''
                    instance.__dict__['hod'] = core_details[0]['hod'] if core_details[0]['hod'] else ''
                    instance.__dict__['reporting_head'] = core_details[0]['reporting_head'] if core_details[0]['reporting_head'] else ''
                    #instance.__dict__['temp_reporting_head'] = core_details[0]['temp_reporting_head'] if core_details[0]['temp_reporting_head'] else None
                    instance.__dict__['company'] = core_details[0]['company'] if core_details[0]['company'] else ''
                    instance.__dict__['mmr_module_id'] = validated_data['mmr_module_id']
                    instance.__dict__['mmr_type'] = validated_data['mmr_type']
                    instance.__dict__['termination_date'] =core_details[0]['termination_date'] if core_details[0]['termination_date'] else None
                    instance.__dict__['attendance_type'] =core_details[0]['attendance_type'] if core_details[0]['attendance_type'] else None
                    instance.__dict__['is_flexi_hour'] =core_details[0]['is_flexi_hour']
                    instance.__dict__['cost_centre'] = cost_centre

                elif list_type == "professional": ### Checking for Professional
                    '''
                        Reason : Adding many fields on Employee Edit
                        Author : Rupam Hazra
                        Date : 19/02/2020
                        Line Number : 582
                    '''





                    if retirement_date:
                        retirement_date = datetime.datetime.strptime(retirement_date, "%Y-%m-%dT%H:%M:%S.%fZ")
                    usr_salary_type_obj = TCoreUserDetail.objects.filter(cu_user=instance.id, cu_is_deleted=False)[0].salary_type
                    if usr_salary_type_obj:
                        usr_salary_type_obj = usr_salary_type_obj.st_name
                    else:
                        usr_salary_type_obj = None
                        
                    if is_transfer:
                        previous_obj = TCoreUserDetail.objects.get(cu_user=instance.id)
                        usr_transfer_obj = previous_obj.__dict__
                        del usr_transfer_obj['_state']
                        # decimale_field = ['initial_ctc','current_ctc','granted_cl','granted_sl','granted_el',
                        #                   'employee_voluntary_provident_fund_contribution','salary_per_month',
                        #                   'granted_leaves_cl_sl']

                        from pprint import pprint
                        pprint(usr_transfer_obj)
                        transfer_history = EmployeeTransferHistory.objects.create(**usr_transfer_obj)
                        TCoreUserDetail.objects.filter(cu_user=instance.id, cu_is_deleted=False).update(
                            sap_personnel_no=sap_personnel_no,
                            company=company,
                            # job_description=job_description,
                            hod=hod,
                            reporting_head_id=reporting_head,
                            # temp_reporting_head_id=temp_reporting_head,
                            department_id=department,
                            sub_department_id=sub_department,
                            designation_id=designation,
                            cost_centre=cost_centre,
                            salary_type_id=salary_type,
                            employee_sub_grade=employee_sub_grade,
                            job_location_state_id=job_location_state,
                            job_location=job_location,
                            is_transfer=True,
                            transfer_date=datetime.datetime.now(),
                            transfer_by=self.context['request'].user
                        )
                        # if cu_alt_email_id:
                        #
                        #     # ============= Mail Send ==============#
                        #
                        #     # Send mail to employee with login details
                        #     user_obj = TCoreUserDetail.objects.filter(cu_user=instance.id)[0]
                        #     mail_data = {
                        #         "name": instance.first_name + '' + instance.last_name,
                        #         "user": instance.username,
                        #         "pass": user_obj.password_to_know,
                        #         "sap_id":user_obj.sap_personnel_no
                        #     }
                        #     send_mail('EMPTR001', user_obj.cu_alt_email_id, mail_data)



                        # pass
                    else:
                        instance.first_name = validated_data['first_name']
                        instance.last_name = validated_data['last_name']
                        instance.save()
                        TCoreUserDetail.objects.filter(cu_user=instance.id, cu_is_deleted=False).update(
                            current_ctc=current_ctc,
                            cu_emp_code=cu_emp_code,
                            cu_punch_id=cu_punch_id,
                            initial_ctc=initial_ctc,
                            sap_personnel_no=sap_personnel_no,
                            # # cost_centre=cost_centre,
                            # updated_cost_centre_id = cost_centre,
                            granted_cl=granted_cl,
                            granted_el=granted_el,
                            granted_sl=granted_sl,
                            daily_loginTime=datetime.datetime.strptime(daily_loginTime, "%H:%M:%S"),
                            daily_logoutTime=datetime.datetime.strptime(daily_logoutTime, "%H:%M:%S"),
                            lunch_start=datetime.datetime.strptime(lunch_start, "%H:%M:%S"),
                            lunch_end=datetime.datetime.strptime(lunch_end, "%H:%M:%S"),
                            salary_type_id=salary_type,
                            is_confirm=is_confirm,
                            cu_updated_by=logdin_user_id,
                            wbs_element=wbs_element,
                            retirement_date=retirement_date,
                            esic_no=esic_no,
                            esi_dispensary=esi_dispensary,
                            pf_no=pf_no,
                            emp_pension_no=emp_pension_no,
                            employee_voluntary_provident_fund_contribution=employee_voluntary_provident_fund_contribution,
                            uan_no=uan_no,
                            branch_name=branch_name,
                            bank_account=bank_account,
                            ifsc_code=ifsc_code,
                            bus_facility=bus_facility,
                            has_pf=has_pf,
                            has_esi=has_esi,
                            bank_name_p_id=bank_name_p,
                            job_location_state_id=job_location_state,
                            job_location=job_location
                        )

                    # #print("in professional")
                    if salary_type:
                        new_salary_type_obj = TCoreSalaryType.objects.get(id=salary_type).st_code
                        # print(new_salary_type_obj)
                        usr_obj = TCoreUserDetail.objects.get(cu_user=instance.id, cu_is_deleted=False)
                        if usr_salary_type_obj != new_salary_type_obj:
                            # print("not same")
                            # str(new_salary_type_obj)
                            if str(new_salary_type_obj) == "AA":
                                usr_obj.granted_el = float(0)
                                usr_obj.granted_leaves_cl_sl = float(0)
                                usr_obj.save()
                                granted_cl = 0
                                granted_sl = 0
                                granted_el = 0
                            elif str(new_salary_type_obj) == "BB":
                                usr_obj.granted_el = float(15)
                                usr_obj.granted_leaves_cl_sl = float(10)
                                usr_obj.save()
                                granted_cl = 10
                                granted_sl = 0
                                granted_el = 15
                            elif str(new_salary_type_obj) == "FF":
                                usr_obj.granted_el = float(15)
                                usr_obj.granted_leaves_cl_sl = float(16)
                                usr_obj.save()
                                granted_cl = 16
                                granted_sl = 0
                                granted_el = 15
                            elif str(new_salary_type_obj) in ["CC", "DD"]:
                                usr_obj.granted_el = float(15)
                                usr_obj.granted_leaves_cl_sl = float(17)
                                usr_obj.save()
                                granted_cl = 10
                                granted_sl = 7
                                granted_el = 15
                            elif str(new_salary_type_obj) == "EE":
                                usr_obj.granted_el = float(15)
                                usr_obj.granted_leaves_cl_sl = float(16)
                                usr_obj.save()
                                granted_cl = 10
                                granted_sl = 6
                                granted_el = 15
                            usr_obj.granted_el = granted_el
                            usr_obj.granted_cl = granted_cl
                            usr_obj.granted_sl = granted_sl
                            usr_obj.save()


                            # print("salary type not same")
                            joining_date = usr_obj.joining_date.date()
                            # #print('joining_date',joining_date)
                            joining_year = joining_date.year
                            # #print('joining_year',joining_year)
                            try:
                                today = datetime.datetime.now()
                                current_month = AttendenceMonthMaster.objects.get(
                                    month_start__date__lte=today,
                                    month_end__date__gte=today, is_deleted=False)
                                year_start_date = current_month.year_start_date
                                year_end_date = current_month.year_end_date
                                joining_date = usr_obj.joining_date
                                print(joining_date)
                                from_date = year_start_date
                                to_date = year_end_date
                                print(from_date, to_date)
                                is_joining_year = False
                                if joining_date > from_date:
                                    is_joining_year = True
                                    from_date = joining_date
                                leave_filter = {}
                                attendenceMonthMaster = AttendenceMonthMaster.objects.filter(
                                    month_end__date__gte=from_date,
                                    month_end__date__lte=to_date, is_deleted=False).values('id', 'grace_available',
                                                                                                'year_start_date',
                                                                                                'year_end_date',
                                                                                                'month',
                                                                                                'month_start',
                                                                                                'month_end',
                                                                                                'days_in_month',
                                                                                                'payroll_month')

                                print(attendenceMonthMaster.count())
                                available_grace = grace_calculation(joining_date.date(), attendenceMonthMaster)
                                print('available_grace',available_grace)
                                year_end_date = attendenceMonthMaster[0]['year_end_date'].date()
                                total_days = ((to_date - from_date).days) + 1
                                print('total_days',total_days)
                                cl, al, el, sl = 0, 0, 0, 0
                                print("instance.cu_user.salary_type")
                                if instance.cu_user.salary_type:
                                    if instance.cu_user.salary_type.st_code in ['FF', 'EE']:
                                        print("in FF")
                                        al = round_calculation(total_days, (granted_cl + granted_sl + granted_el))
                                    elif instance.cu_user.salary_type.st_code in ['CC', 'DD']:
                                        cl = round_calculation(total_days, granted_cl)
                                        sl = round_calculation(total_days, granted_sl)
                                        el = round_calculation(total_days, granted_el)
                                    elif instance.cu_user.salary_type.st_code in ['BB']:
                                        cl = round_calculation(total_days, granted_cl)
                                        # sl = round_calculation(total_days, granted_sl)
                                        el = round_calculation(total_days, granted_el)
                                    else:
                                        pass
                                leave_confirm = round_calculation(total_days,
                                                                         (granted_cl + granted_sl + granted_el))
                                leave_part_2_not_cofirm = round_calculation(total_days, (granted_cl + granted_sl))
                                leave_filter['granted_leaves_cl_sl'] = leave_part_2_not_cofirm
                                if granted_el:
                                    leave_filter['el'] = round_calculation(total_days, granted_el)
                                else:
                                    leave_filter['el'] = float(0)
                                users = [instance.id]
                                # if str(usr_obj.salary_type.st_name) in ["Bonus 12.5","Bonus 13"]:
                                print("calling function")

                                roundOffLeaveCalculationUpdate(users, attendenceMonthMaster,
                                                               leave_confirm, leave_confirm,
                                                               total_days,
                                                               year_end_date, attendenceMonthMaster[0]['month_start'], joining_date, cl, sl, el, al, is_joining_year)

                                if available_grace:
                                    # #print(" in avilavel grace")
                                    if attendenceMonthMaster[0]['year_start_date'].date() < joining_date:
                                        JoiningApprovedLeave.objects.filter(employee=instance.id).update(
                                            year=joining_year,
                                            month=attendenceMonthMaster[0]['month'],
                                            **leave_filter,
                                            first_grace=available_grace,
                                            # created_by=user,
                                            # owned_by=user
                                        )
                            except:
                                pass



                    if saturday_off:
                        prev_sat_data=AttendenceSaturdayOffMaster.objects.filter(employee=instance,is_deleted=False)
                        # #print('prev_sat_data',prev_sat_data)
                        if prev_sat_data:
                            for p_s in prev_sat_data:
                                p_s.first=saturday_off['first']
                                p_s.second=saturday_off['second']
                                p_s.third=saturday_off['third']
                                p_s.fourth=saturday_off['fourth']
                                p_s.all_s_day=saturday_off['all_s_day']
                                p_s.updated_by_id=logdin_user_id
                                p_s.save()
                            AttendenceSaturdayOffLogMaster.objects.create(employee=instance,
                                                                         **saturday_off,
                                                                         updated_by_id=logdin_user_id,
                                                                        )
                        else:
                            saturday_data=AttendenceSaturdayOffMaster.objects.create(employee=instance,
                                                                                    **saturday_off,
                                                                                    created_by_id=logdin_user_id,
                                                                                    owned_by_id=logdin_user_id
                                                                                    )

                            # #print('saturday_data',saturday_data)
                            AttendenceSaturdayOffLogMaster.objects.create(employee=instance,
                                                                         **saturday_off,
                                                                         created_by_id=logdin_user_id,
                                                                         owned_by_id=logdin_user_id
                                                                        )

                    leave_filter={}
                    '''
                        Reason : Change functionality adn add this code employee add portion
                        Author : Rupam Hazra
                        Date : 19/02/2020
                        Line Number : 657 - 706
                    '''
                    # joining_date_details=TCoreUserDetail.objects.filter(cu_user=instance.id,cu_is_deleted=False).values('joining_date')
                    # if joining_date_details:
                    #     joining_date=joining_date_details[0]['joining_date'].date()
                    #     joining_year=joining_date.year
                    #     # #print('joining_year',joining_year)


                    #     total_month_grace=AttendenceMonthMaster.objects.filter(month_start__date__lte=joining_date,
                    #                     month_end__date__gte=joining_date,is_deleted=False).values('grace_available',
                    #                                                              'year_start_date',
                    #                                                              'year_end_date',
                    #                                                              'month',
                    #                                                              'month_start',
                    #                                                              'month_end'
                    #                                                              )
                    #     if total_month_grace:
                    #         year_end_date=total_month_grace[0]['year_end_date'].date()
                    #         total_days=(year_end_date - joining_date).days
                    #         # #print('total_days',total_days)
                    #         calculated_cl=round((total_days/365)* int(granted_cl))
                    #         leave_filter['cl']=calculated_cl
                    #         calculated_el=round((total_days/365)* int(granted_el))
                    #         leave_filter['el']=calculated_el
                    #         if granted_sl:
                    #             calculated_sl=round((total_days/365)* int(granted_sl))
                    #             # #print('calculated_sl',calculated_sl)
                    #             leave_filter['sl']=calculated_sl
                    #         else:
                    #             leave_filter['sl']=None

                    #         month_start_date=total_month_grace[0]['month_start'].date()
                    #         month_end_date=total_month_grace[0]['month_end'].date()
                    #         # #print('month_start_date',month_start_date,month_end_date)
                    #         month_days=(month_end_date-month_start_date).days
                    #         # #print('month_days',month_days)
                    #         remaining_days=(month_end_date-joining_date).days
                    #         # #print('remaining_days',remaining_days)
                    #         # available_grace=round(total_month_grace[0]['grace_available']/remaining_days)
                    #         available_grace = round((remaining_days/month_days)*int(total_month_grace[0]['grace_available']))
                    #         # #print('available_grace',available_grace)

                    #         if total_month_grace[0]['year_start_date']<joining_date_details[0]['joining_date']:
                    #             JoiningApprovedLeave.objects.get_or_create(employee_id=instance.id,
                    #                                                 year=joining_year,
                    #                                                 month=total_month_grace[0]['month'],
                    #                                                 **leave_filter,
                    #                                                 first_grace=available_grace,
                    #                                                 created_by_id=logdin_user_id,
                    #                                                 owned_by_id=logdin_user_id
                    #                                                 )


                    instance.__dict__['cu_emp_code'] =cu_emp_code
                    instance.__dict__['cu_punch_id'] =cu_punch_id
                    instance.__dict__['current_ctc'] = current_ctc
                    instance.__dict__['initial_ctc'] = initial_ctc
                    instance.__dict__['sap_personnel_no'] = sap_personnel_no
                    instance.__dict__['cost_centre'] = cost_centre
                    instance.__dict__['granted_cl'] = granted_cl
                    instance.__dict__['granted_el'] = granted_el
                    instance.__dict__['granted_sl'] = granted_sl
                    instance.__dict__['daily_loginTime'] = daily_loginTime
                    instance.__dict__['daily_logoutTime'] = daily_logoutTime
                    instance.__dict__['lunch_start'] = lunch_start
                    instance.__dict__['lunch_end'] = lunch_end
                    instance.__dict__['saturday_off'] = saturday_off
                    instance.__dict__['salary_type'] = salary_type
                    instance.__dict__['is_confirm'] = is_confirm

                    instance.__dict__['wbs_element'] = wbs_element
                    instance.__dict__['retirement_date'] = retirement_date
                    instance.__dict__['esic_no'] = esic_no
                    instance.__dict__['esi_dispensary'] = esi_dispensary
                    instance.__dict__['pf_no'] = pf_no
                    instance.__dict__['emp_pension_no'] = emp_pension_no
                    instance.__dict__['employee_voluntary_provident_fund_contribution'] = employee_voluntary_provident_fund_contribution

                    instance.__dict__['uan_no'] = uan_no
                    instance.__dict__['branch_name'] = branch_name
                    instance.__dict__['bank_account'] = bank_account
                    instance.__dict__['ifsc_code'] = ifsc_code
                    instance.__dict__['bus_facility'] = bus_facility

                    instance.__dict__['has_pf'] = has_pf
                    instance.__dict__['has_esi'] = has_esi
                    instance.__dict__['bank_name_p'] = bank_name_p
                    instance.__dict__['job_location_state'] = job_location_state
                    instance.__dict__['job_location'] = job_location



                    benefit_provided_details = validated_data.pop('benefit_provided') if 'benefit_provided' in validated_data else None
                    if benefit_provided_details:
                        benefits = HrmsUsersBenefits.objects.filter(user=instance,is_deleted=False)
                        if benefits:
                            benefits.delete()

                        benefits_list = []
                        for get_benefit in benefit_provided_details:
                            create_benefit = HrmsUsersBenefits.objects.create(
                                user_id = str(instance.id),
                                benefits_id = get_benefit['benefits'],
                                allowance=get_benefit['allowance'],
                                created_by_id = logdin_user_id
                            )
                            create_benefit.__dict__.pop('_state') if '_state' in create_benefit.__dict__.keys() else create_benefit.__dict__
                            benefits_list.append(create_benefit.__dict__)
                        instance.__dict__['benefit_provided'] = benefits_list
                    elif benefit_provided_details is None:
                        benefits = HrmsUsersBenefits.objects.filter(user=instance,is_deleted=False)
                        if benefits:
                            benefits.delete()
                    else:
                        instance.__dict__['benefit_provided'] = None

                    other_facilities_details = validated_data.pop('other_facilities') if 'other_facilities' in validated_data else None
                    if other_facilities_details:
                        facilities = HrmsUsersOtherFacilities.objects.filter(user=instance,is_deleted=False)
                        if facilities:
                            facilities.delete()
                        facility_list = []
                        for get_facility in other_facilities_details:
                            create_facilities = HrmsUsersOtherFacilities.objects.create(
                                user_id = str(instance.id),
                                other_facilities= get_facility['facilities'],
                                created_by_id = logdin_user_id
                            )
                            create_facilities.__dict__.pop('_state') if '_state' in create_facilities.__dict__.keys() else create_facilities.__dict__
                            facility_list.append(create_facilities.__dict__)
                        instance.__dict__['other_facilities'] = facility_list
                    elif other_facilities_details is None:
                        facilities = HrmsUsersOtherFacilities.objects.filter(user=instance,is_deleted=False)
                        if facilities:
                            facilities.delete()
                    else:
                        instance.__dict__['other_facilities'] = None

                return instance.__dict__
        except Exception as e:
            raise e


class EmployeeListSerializer(serializers.ModelSerializer):
    cu_user = serializers.CharField()
    class Meta:
        model = User
        # is_active field added by Shubhadeep
        fields=('id', 'first_name', 'last_name', 'cu_user', 'is_active')

class EmployeeListSerializerV2(serializers.ModelSerializer):
    # cu_user = serializers.CharField()
    company = serializers.SerializerMethodField()
    company_id = serializers.SerializerMethodField()
    department = serializers.SerializerMethodField()
    department_id = serializers.SerializerMethodField()
    designation = serializers.SerializerMethodField()
    designation_id = serializers.SerializerMethodField()
    is_deleted = serializers.SerializerMethodField()
    
    def get_company(self,instance):
        userDetails = TCoreUserDetail.objects.filter(cu_user=instance)
        if userDetails:
            userDetails = userDetails[0]
            return userDetails.company.coc_name if userDetails.company else None

    def get_company_id(self,instance):
        userDetails = TCoreUserDetail.objects.filter(cu_user=instance)
        if userDetails:
            userDetails = userDetails[0]
            return userDetails.company.id if userDetails.company else None

    def get_department_id(self,instance):
        userDetails = TCoreUserDetail.objects.filter(cu_user=instance)
        if userDetails:
            userDetails = userDetails[0]
            return userDetails.department.id if userDetails.department else None
    
    def get_department(self,instance):
        userDetails = TCoreUserDetail.objects.filter(cu_user=instance)
        if userDetails:
            userDetails = userDetails[0]
            return userDetails.department.cd_name if userDetails.department else None
    
    def get_designation(self,instance):
        userDetails = TCoreUserDetail.objects.filter(cu_user=instance)
        if userDetails:
            userDetails = userDetails[0]
            return userDetails.designation.cod_name if userDetails.designation else None

    def get_designation_id(self,instance):
        userDetails = TCoreUserDetail.objects.filter(cu_user=instance)
        if userDetails:
            userDetails = userDetails[0]
            return userDetails.designation.id if userDetails.designation else None

    def get_is_deleted(self,instance):
        userDetails = TCoreUserDetail.objects.filter(cu_user=instance)
        if userDetails:
            userDetails = userDetails[0]
            return userDetails.cu_is_deleted

    class Meta:
        model = User
        fields= '__all__'

class EmployeeActiveListSerializer(serializers.ModelSerializer):
    cu_user = serializers.CharField()
    class Meta:
        model = User
        fields=('id','first_name','last_name','cu_user')

class EmployeeListWithoutDetailsSerializer(serializers.ModelSerializer):
    sap_id = serializers.SerializerMethodField(required=False)
    department_name = serializers.SerializerMethodField(required=False)
    department_id = serializers.SerializerMethodField(required=False)
    def get_sap_id(self,obj):
        try:
            usr_obj = TCoreUserDetail.objects.get(cu_user=obj)
            if usr_obj.sap_personnel_no:
                return usr_obj.sap_personnel_no
            else:
                return None
        except:
            return ''
    def get_department_name(self,obj):
        try:
            usr_obj = TCoreUserDetail.objects.get(cu_user=obj)
            if usr_obj.department:
                return usr_obj.department.cd_name
            else:
                return None
        except:
            return ''
    def get_department_id(self,obj):
        try:
            usr_obj = TCoreUserDetail.objects.get(cu_user=obj)
            if usr_obj.department:
                return usr_obj.department.id
            else:
                return None
        except:
            return ''

    class Meta:
        model = User
        fields=('id','first_name','last_name','email','is_superuser','is_active','sap_id','department_id', 'department_name')

class DocumentAddSerializer(serializers.ModelSerializer):
    created_by=serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by=serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = HrmsDocument
        fields=('id','user','tab_name','field_label','document_name','document','created_by','owned_by')

class DocumentDeleteSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = HrmsDocument
        fields = '__all__'
    def update(self, instance, validated_data):
        instance.updated_by = validated_data.get('updated_by')
        instance.is_deleted = True
        instance.save()
        return instance
class HrmsEmployeeProfileDocumentAddSerializer(serializers.ModelSerializer):
    created_by=serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by=serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = HrmsDynamicSectionFieldLabelDetailsWithDoc
        fields=('id','user','tab_name','field_label','field_label_value','document_name','document','created_by','owned_by')



class HrmsEmployeeProfileDocumentDeleteSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = HrmsDynamicSectionFieldLabelDetailsWithDoc
        fields = '__all__'
    def update(self, instance, validated_data):
        instance.updated_by = validated_data.get('updated_by')
        instance.is_deleted = True
        instance.save()
        return instance

class HrmsEmployeeAcademicQualificationAddSerializer(serializers.ModelSerializer):
    created_by=serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by=serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = HrmsUserQualification
        fields='__all__'

class HrmsEmployeeAcademicQualificationDeleteSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = HrmsUserQualification
        fields = '__all__'
    def update(self, instance, validated_data):
        instance.updated_by = validated_data.get('updated_by')
        instance.is_deleted = True
        instance.save()
        qualification_doc=HrmsUserQualificationDocument.objects.filter(user_qualification=instance,is_deleted=False)
        if qualification_doc:
            for q_d in qualification_doc:
                existing_image='./media/' + str(q_d.document)
                # print('existing_image',existing_image)
                if os.path.isfile(existing_image):
                    os.remove(existing_image)
            qualification_doc.delete()
        return instance

class HrmsEmployeeAcademicQualificationDocumentAddSerializer(serializers.ModelSerializer):
    created_by=serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by=serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = HrmsUserQualificationDocument
        fields='__all__'

class HrmsEmployeeAcademicQualificationDocumentDeleteSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = HrmsUserQualificationDocument
        fields = '__all__'
    def update(self, instance, validated_data):
        instance.updated_by = validated_data.get('updated_by')
        instance.is_deleted = True
        instance.save()
        return instance

#:::::::::::::::::::::: HRMS NEW REQUIREMENT:::::::::::::::::::::::::::#
class HrmsNewRequirementAddSerializer(serializers.ModelSerializer):
    created_by=serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by=serializers.CharField(default=serializers.CurrentUserDefault())
    raised_by_data = serializers.DictField(required =False)
    class Meta:
        model = HrmsNewRequirement
        fields=('__all__')
        extra_fields= ('raised_by_data')

    def create(self,validated_data):
        print(validated_data)
        # for key,value in validated_data.items():
        #     if key == 'raised_by_data':


        validated_data.pop('raised_by_data')

        requirement_data= HrmsNewRequirement.objects.create(**validated_data,tab_status=2)
        return requirement_data

#:::::::::::::::::::::: HRMS INTERVIEW TYPE:::::::::::::::::::::::::::#
class InterviewTypeAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = HrmsInterviewType
        fields = ('id', 'name', 'created_by', 'owned_by')

class InterviewTypeEditSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = HrmsInterviewType
        fields = ('id', 'name', 'updated_by')

class InterviewTypeDeleteSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = HrmsInterviewType
        fields = '__all__'
    def update(self, instance, validated_data):
        instance.is_deleted=True
        instance.updated_by = validated_data.get('updated_by')
        instance.save()
        return instance

#:::::::::::::::::::::: HRMS INTERVIEW LEVEL:::::::::::::::::::::::::::#
class InterviewLevelAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = HrmsInterviewLevel
        fields = ('id', 'name', 'created_by', 'owned_by')

class InterviewLevelEditSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = HrmsInterviewLevel
        fields = ('id', 'name', 'updated_by')

class InterviewLevelDeleteSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = HrmsInterviewLevel
        fields = '__all__'
    def update(self, instance, validated_data):
        instance.is_deleted=True
        instance.updated_by = validated_data.get('updated_by')
        instance.save()
        return instance

#:::::::::::::::::::::: HRMS SCHEDULE INTERVIEW :::::::::::::::::::::::::::#

class ScheduleInterviewAddSerializer(serializers.ModelSerializer):
    created_by=serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by=serializers.CharField(default=serializers.CurrentUserDefault())
    interview_with=serializers.CharField(required=False)
    interviewers=serializers.ListField(required=False)
    resume=serializers.FileField(required=False,allow_null=True)
    resume_data=serializers.CharField(required=False)
    planned_date_of_interview=serializers.DateTimeField(required=False)
    planned_time_of_interview=serializers.TimeField(required=False)
    type_of_interview=serializers.IntegerField(required=False)
    level_of_interview=serializers.IntegerField(required=False)
    class Meta:
        model = HrmsScheduleInterview
        fields=('id','requirement','candidate_name','contact_no','email','note','resume','resume_data',
                 'planned_date_of_interview','planned_time_of_interview','type_of_interview',
                 'level_of_interview','interview_with','interviewers','created_by','owned_by','action_approval')

    def create(self,validated_data):
        try:

            created_by=validated_data.get('created_by')
            owned_by =validated_data.get('owned_by')
            # is_resheduled=validated_data.get('is_resheduled')
            candidate_name=validated_data.get('candidate_name') if 'candidate_name' in validated_data else None
            contact_no=validated_data.get('contact_no') if 'contact_no' in validated_data else None
            email=validated_data.get('email') if 'email' in validated_data else None
            note=validated_data.get('note') if 'note' in validated_data else None
            resume=validated_data.get('resume') if 'resume' in validated_data else None
            planned_date_of_interview=validated_data.get('planned_date_of_interview') if 'planned_date_of_interview' in validated_data else None
            planned_time_of_interview=validated_data.get('planned_time_of_interview') if 'planned_time_of_interview' in validated_data else None
            type_of_interview=validated_data.get('type_of_interview') if 'type_of_interview' in validated_data else None
            level_of_interview=validated_data.get('level_of_interview') if 'level_of_interview' in validated_data else None
            interview_with = validated_data.get('interview_with') if 'interview_with' in validated_data else None
            # print("interview_with",interview_with)
            with transaction.atomic():
                # print('validated_data',validated_data)
                print('requirement',validated_data.get('requirement'))
                tab_status=HrmsNewRequirement.objects.only('tab_status').get(id=str(validated_data.get('requirement')),
                                                                            is_deleted=False
                                                                            ).tab_status
                print('tab_status',tab_status)
                if tab_status >= 3:
                    if tab_status != 5 and tab_status != 6:
                        HrmsNewRequirement.objects.filter(id=str(validated_data.get('requirement')),
                                                        is_deleted=False).update(tab_status=4)
                    schedule_details,created=HrmsScheduleInterview.objects.get_or_create(
                                                                        requirement_id=str(validated_data.get('requirement')),
                                                                        candidate_name=candidate_name,
                                                                        contact_no=contact_no,
                                                                        email=email,
                                                                        note=note,
                                                                        resume=resume,
                                                                        created_by=created_by,
                                                                        owned_by=owned_by
                                                                        )
                    print('schedule_details',schedule_details.__dict__)
                    print('created',created)

                    schedule_another_details,created=HrmsScheduleAnotherRoundInterview.objects.get_or_create(schedule_interview=schedule_details,
                                                                                                            planned_date_of_interview=planned_date_of_interview,
                                                                                                            planned_time_of_interview=planned_time_of_interview,
                                                                                                            type_of_interview_id=str(type_of_interview),
                                                                                                            level_of_interview_id=str(level_of_interview),
                                                                                                            created_by=created_by,
                                                                                                            owned_by=owned_by
                                                                                                            )
                    print('schedule_another_details',schedule_another_details.__dict__)

                    interviewers_list=[]
                    if interview_with:
                        interviewers= interview_with.split(',')
                        print('interviewers',interviewers)
                        for i_w in interviewers:
                            interview_details,created_1=HrmsScheduleInterviewWith.objects.get_or_create(interview=schedule_another_details,
                                                                                        user_id=int(i_w),
                                                                                        created_by=created_by,
                                                                                        owned_by=owned_by
                                                                                    )
                            print('interview_details',interview_details.__dict__)
                            print('created_1',created_1)

                            interview_details.__dict__.pop('_state') if '_state' in interview_details.__dict__.keys() else interview_details.__dict__
                            interviewers_list.append(interview_details.__dict__)


                    schedule_details.__dict__['interviewers']=interviewers_list
                    schedule_details.__dict__['resume_data']=schedule_details.__dict__['resume']
                    schedule_details.__dict__['requirement']=validated_data.get('requirement')
                    schedule_details.__dict__['planned_date_of_interview']=schedule_another_details.__dict__['planned_date_of_interview']
                    schedule_details.__dict__['planned_time_of_interview']=schedule_another_details.__dict__['planned_time_of_interview']
                    schedule_details.__dict__['type_of_interview']=type_of_interview
                    schedule_details.__dict__['level_of_interview']=level_of_interview
                    return schedule_details.__dict__
                else:
                    return list()
        except Exception as e:
            raise e
class RescheduleInterviewAddSerializer(serializers.ModelSerializer):
    created_by=serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by=serializers.CharField(default=serializers.CurrentUserDefault())
    interview_with=serializers.CharField(required=False)
    interviewers=serializers.ListField(required=False)
    class Meta:
        model = HrmsScheduleAnotherRoundInterview
        fields=('id','planned_date_of_interview','planned_time_of_interview','type_of_interview',
        'level_of_interview','interview_status','is_resheduled','created_by','owned_by','interview_with','interviewers')
    def create(self,validated_data):
        try:
            schedule_interview = self.context['request'].query_params.get('schedule_interview', None)
            # print('schedule_interview',type(schedule_interview))
            created_by=validated_data.get('created_by')
            owned_by=validated_data.get('owned_by')
            planned_date_of_interview=validated_data.get('planned_date_of_interview') if 'planned_date_of_interview' in validated_data else None
            planned_time_of_interview=validated_data.get('planned_time_of_interview') if 'planned_time_of_interview' in validated_data else None
            type_of_interview=validated_data.get('type_of_interview') if 'type_of_interview' in validated_data else None
            level_of_interview=validated_data.get('level_of_interview') if 'level_of_interview' in validated_data else None
            interview_with = validated_data.get('interview_with') if 'interview_with' in validated_data else None
            with transaction.atomic():
                prev_schedule_interview=HrmsScheduleAnotherRoundInterview.objects.filter(schedule_interview_id=int(schedule_interview),
                                                                                        is_deleted=False)
                # print('prev_schedule_interview',prev_schedule_interview)
                if prev_schedule_interview:
                    for p_s_i in prev_schedule_interview:
                        p_s_i.is_resheduled=True
                        p_s_i.save()
                    schedule_another_details,created=HrmsScheduleAnotherRoundInterview.objects.get_or_create(schedule_interview_id=int(schedule_interview),
                                                                                                            planned_date_of_interview=planned_date_of_interview,
                                                                                                            planned_time_of_interview=planned_time_of_interview,
                                                                                                            type_of_interview_id=str(type_of_interview),
                                                                                                            level_of_interview_id=str(level_of_interview),
                                                                                                            created_by=created_by,
                                                                                                            owned_by=owned_by,
                                                                                                            )
                    # print('schedule_another_details',schedule_another_details.__dict__)
                    interviewers_list=[]
                    if interview_with:
                        interviewers= interview_with.split(',')
                        # print('interviewers',interviewers)
                        for i_w in interviewers:
                            interview_details,created_1=HrmsScheduleInterviewWith.objects.get_or_create(interview=schedule_another_details,
                                                                                        user_id=int(i_w),
                                                                                        created_by=created_by,
                                                                                        owned_by=owned_by
                                                                                    )
                            # print('interview_details',interview_details.__dict__)
                            # print('created_1',created_1)

                            interview_details.__dict__.pop('_state') if '_state' in interview_details.__dict__.keys() else interview_details.__dict__
                            interviewers_list.append(interview_details.__dict__)

                    schedule_another_details.__dict__['interviewers']=interviewers_list
                    schedule_another_details.__dict__['type_of_interview']=type_of_interview
                    schedule_another_details.__dict__['level_of_interview']=level_of_interview
                    return schedule_another_details.__dict__
        except Exception as e:
            raise e
class InterviewStatusAddSerializer(serializers.ModelSerializer):
    updated_by=serializers.CharField(default=serializers.CurrentUserDefault())
    interview_with=serializers.CharField(required=False)
    feedback=serializers.FileField(required=False)
    feedback_data = serializers.DictField(required=False)
    interviewers=serializers.ListField(required=False)
    # actual_date_of_interview=serializers.DateTimeField(required=False)
    # actual_time_of_interview=serializers.TimeField(required=False)
    # type_of_interview=serializers.IntegerField(required=False)
    # level_of_interview=serializers.IntegerField(required=False)
    # interview_status=serializers.IntegerField(required=False)
    class Meta:
        model = HrmsScheduleAnotherRoundInterview
        fields= ('id','actual_date_of_interview','actual_time_of_interview','type_of_interview',
        'level_of_interview','interview_status','interview_with','feedback','updated_by','feedback_data','interviewers')

    def update(self,instance,validated_data):
        try:
            actual_date_of_interview=validated_data.get('actual_date_of_interview') if 'actual_date_of_interview' in validated_data else None
            actual_time_of_interview=validated_data.get('actual_time_of_interview') if 'actual_time_of_interview' in validated_data else None
            type_of_interview=validated_data.get('type_of_interview') if 'type_of_interview' in validated_data else ""
            print('type_of_interview',type_of_interview)
            level_of_interview=validated_data.get('level_of_interview') if 'level_of_interview' in validated_data else ""
            interview_status=validated_data.get('interview_status') if 'interview_status' in validated_data else ""
            interview_with=validated_data.get('interview_with') if 'interview_with' in validated_data else None
            feedback=validated_data.get('feedback') if 'feedback' in validated_data else None

            updated_by=validated_data.get('updated_by')
            # print(instance.__dict__)
            data = {}
            with transaction.atomic():
                # schedule_another_details=HrmsScheduleAnotherRoundInterview.objects.filter(schedule_interview=instance,
                #                                                                             is_deleted=False
                #                                                                         )
                instance.actual_date_of_interview=actual_date_of_interview
                instance.actual_time_of_interview=actual_time_of_interview
                instance.type_of_interview=type_of_interview
                instance.level_of_interview=level_of_interview
                instance.interview_status=interview_status
                instance.updated_by=updated_by
                instance.save()

                if interview_with:
                    interviewers=interview_with.split(',')
                    interviewers_list = []
                    for i_w in interviewers:
                        int_det=HrmsScheduleInterviewWith.objects.filter(interview=instance,user_id=int(i_w),is_deleted=False)
                        # print('int_det',int_det)
                        if int_det:
                            int_det.delete()

                        create_interviewers,created = HrmsScheduleInterviewWith.objects.get_or_create(
                            interview =instance,
                            user_id= int(i_w),
                            created_by=updated_by,
                            owned_by=updated_by
                        )
                        # print('create_interviewers',create_interviewers)
                        create_interviewers.__dict__.pop('_state') if '_state' in create_interviewers.__dict__.keys() else create_interviewers.__dict__
                        interviewers_list.append(create_interviewers.__dict__)
                    instance.__dict__['interviewers'] = interviewers_list

                if feedback:
                    upload_feedback=HrmsScheduleInterviewFeedback.objects.create(interview=instance,
                                                                                upload_feedback=feedback,
                                                                                created_by=updated_by,
                                                                                owned_by=updated_by
                                                                                )
                    upload_feedback.__dict__.pop('_state') if '_state' in upload_feedback.__dict__.keys() else upload_feedback.__dict__
                    # print('upload_feedback',upload_feedback.__dict__)
                    # data =instance.__dict__
                    instance.__dict__['feedback_data']=upload_feedback.__dict__
                    # data['feedback']=upload_feedback.__dict__

                instance.__dict__['type_of_interview'] = type_of_interview
                instance.__dict__['level_of_interview'] = level_of_interview
                instance.__dict__['actual_date_of_interview'] = actual_date_of_interview
                instance.__dict__['actual_time_of_interview'] = actual_time_of_interview
                instance.__dict__['interview_status'] = interview_status
                # print("instance.__dict__",instance.__dict__)
                return instance
        except Exception as e:
            raise e

class InterviewStatusListSerializer(serializers.ModelSerializer):
    class Meta:
        model = HrmsScheduleInterview
        fields= '__all__'

class CandidatureUpdateEditSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = HrmsScheduleInterview
        fields = ('id','notice_period','expected_ctc','current_ctc', 'updated_by')

class CandidatureApproveEditSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = HrmsScheduleInterview
        fields = ('id','updated_by','level_approval','approval_permission_user_level')

    def update(self, instance, validated_data):
        try:
            req_id = self.context['request'].query_params.get('req_id', None)
            section_name = self.context['request'].query_params.get('section_name', None)
            with transaction.atomic():
                approved_data = HrmsScheduleInterview.objects.filter(requirement=req_id)
                check_full = HrmsNewRequirement.objects.get(id=req_id)
                print("check_full.tab_status",check_full.tab_status)
                if check_full.tab_status != 6:

                    approval_data = HrmsScheduleInterview.objects.filter(id=instance.id).update(**validated_data)
                    approved_list = HrmsScheduleInterview.objects.get(id=instance.id)
                    # print('approved_list',approved_list.__dict__)
                    approved_list.__dict__.pop('id')
                    approved_list.__dict__.pop('created_by_id')
                    approved_list.__dict__.pop('owned_by_id')
                    approved_list.__dict__.pop('updated_by_id')
                    approved_list.__dict__.pop('created_at')
                    approved_list.__dict__.pop('updated_at')

                    approved_list.__dict__.pop('_state')
                    print("approved_list.__dict__",approved_list.__dict__)

                    if approved_list:
                        print("entered the condition ")
                        print(instance.id)
                        HrmsScheduleInterviewLog.objects.create(hsi_master_id = instance.id,**(approved_list.__dict__))
                    # print('approved_list',approved_list)
                    count =0
                    no_of_pos = HrmsNewRequirement.objects.get(id=req_id).number_of_position
                    permission_level_value = PmsApprovalPermissonLavelMatser.objects.get(section__cot_name__icontains=section_name).permission_level
                    for data in approved_data:
                        if data.approval_permission_user_level:
                            var=data.approval_permission_user_level.permission_level
                            res = re.sub("\D", "", var)
                            print("res",res,type(res))
                            if int(res) == int(permission_level_value) and data.level_approval == True:
                                count =count+1
                    print("count",count, no_of_pos)
                    if count == no_of_pos:
                        HrmsNewRequirement.objects.filter(id=req_id).update(tab_status=6,closing_date=datetime.now)

                else:
                    custom_exception_message(self,None,"Number of position is Fullfilled")




                return validated_data


        except Exception as e:
            raise e

class OpenAndClosedRequirementListSerializer(serializers.ModelSerializer):
    department_name=serializers.SerializerMethodField(required=False)
    designation_name=serializers.SerializerMethodField(required=False)
    raised_by=serializers.SerializerMethodField(required=False)
    tab_status_name = serializers.CharField(source='get_tab_status_display')
    def get_raised_by(self,HrmsNewRequirement):
        if HrmsNewRequirement.created_by:
            user_detail=User.objects.filter(id=HrmsNewRequirement.created_by.id)
            for u_d in user_detail:
                name=u_d.first_name+" "+u_d.last_name
            return name
    def get_department_name(self,HrmsNewRequirement):
        if HrmsNewRequirement.issuing_department:
            return TCoreDepartment.objects.only('cd_name').get(id=HrmsNewRequirement.issuing_department.id).cd_name
    def get_designation_name(self,HrmsNewRequirement):
        if HrmsNewRequirement.proposed_designation:
            return TCoreDesignation.objects.only('cod_name').get(id=HrmsNewRequirement.proposed_designation.id).cod_name
    class Meta:
        model = HrmsNewRequirement
        fields= '__all__'

class UpcomingAndInterviewHistoryListSerializer(serializers.ModelSerializer):
    tab_status=serializers.SerializerMethodField(required=False)
    date_of_requirement=serializers.SerializerMethodField(required=False)
    department=serializers.SerializerMethodField(required=False)
    designation=serializers.SerializerMethodField(required=False)
    location=serializers.SerializerMethodField(required=False)
    candidature_name = serializers.CharField(source='get_action_approval_display')
    def get_tab_status(self,HrmsScheduleInterview):
        if HrmsScheduleInterview.requirement:
            tab_status=HrmsNewRequirement.objects.filter(id=HrmsScheduleInterview.requirement.id,
                                                                is_deleted=False)
            if tab_status:
                for t_s in tab_status:
                    tab_dict={
                        'tab_status_id':t_s.tab_status,
                        'tab_status_name':t_s.get_tab_status_display()
                    }
                return tab_dict
            else:
                return None
    def get_date_of_requirement(self,HrmsScheduleInterview):
        if HrmsScheduleInterview.requirement:
            return HrmsNewRequirement.objects.only('date').get(id=HrmsScheduleInterview.requirement.id,
                                                                is_deleted=False).date
    def get_department(self,HrmsScheduleInterview):
        if HrmsScheduleInterview.requirement:
            dept_det=HrmsNewRequirement.objects.filter(id=HrmsScheduleInterview.requirement.id,
                                                                is_deleted=False)
            if dept_det:
                for d_d in dept_det:
                    details={
                        'department_id':d_d.issuing_department.id,
                        'department_name':d_d.issuing_department.cd_name
                    }
                return details
            else:
                return None
    def get_designation(self,HrmsScheduleInterview):
        if HrmsScheduleInterview.requirement:
            desig_det=HrmsNewRequirement.objects.filter(id=HrmsScheduleInterview.requirement.id,
                                                                is_deleted=False)
            if desig_det:
                for d_d in desig_det:
                    details={
                        'designation_id':d_d.proposed_designation.id,
                        'designation_name':d_d.proposed_designation.cod_name
                    }
                return details
            else:
                return None
    def get_location(self,HrmsScheduleInterview):
        if HrmsScheduleInterview.requirement:
            return HrmsNewRequirement.objects.only('location').get(id=HrmsScheduleInterview.requirement.id,
                                                                is_deleted=False).location

    class Meta:
        model = HrmsScheduleInterview
        fields= '__all__'

class EmployeeActiveInactiveUserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=False)
    email = serializers.CharField(required=False)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    is_superuser = serializers.BooleanField(required=False)
    is_active = serializers.BooleanField(required=False)
    class Meta:
        model = User
        fields = ('id','first_name', 'last_name', 'username','email', 'is_superuser', 'is_active')

    def update(self, instance, validated_data):
        try:
            with transaction.atomic():

                instance.is_active = validated_data.get('is_active')
                instance.save()
                # print('instance',instance)
                if validated_data.get('is_active'):
                    TCoreUserDetail.objects.filter(cu_user=instance).update(cu_is_deleted=False)
                    TCoreUserDetail.objects.filter(cu_user=instance).update(termination_date=None)
                else:
                    TCoreUserDetail.objects.filter(cu_user=instance).update(cu_is_deleted=True)
                    usr_details_obj = TCoreUserDetail.objects.filter(cu_user=instance)
                    if not usr_details_obj[0].termination_date:
                        current_date = datetime.datetime.now()
                        TCoreUserDetail.objects.filter(cu_user=instance).update(termination_date=current_date)




                return instance
        except Exception as e:
            raise e

'''
    FOR NEW RULES & REGULATION IN ATTENDENCE SYSTEM FOR FINANCIAL YEAR [2020-2021]
    Author : Rupam Hazra
    Implementaion Starting Date : 17.03.2020
'''
'''
    CHANGES ON THE BASIS OF CHANGE REQUEST DOCUMENT SSIL-DASHBOARD ATTENDANCE AND HRMS Cr-3.0 [2020-2021]
    Author : Swarup Adhikary
    Implementaion Starting Date : 14.07.2020
'''


class EmployeeAddV2Serializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    cu_phone_no = serializers.CharField(required=False)
    cu_punch_id = serializers.CharField(required=False)
    hod = serializers.CharField(required=False)
    grade = serializers.CharField(required=False, allow_null=True)
    sub_grade = serializers.CharField(required=False, allow_null=True)
    cu_emp_code = serializers.CharField(required=False)
    sap_personnel_no = serializers.CharField(required=False, allow_null=True)
    mmr_module_id = serializers.CharField(required=False)
    mmr_type = serializers.CharField(required=False)
    reporting_head = serializers.CharField(required=False)
    cu_profile_img = serializers.FileField(required=False)
    reporting_head_name = serializers.CharField(required=False)
    company = serializers.CharField(required=False)
    cost_centre = serializers.CharField(required=False)
    hod_name = serializers.CharField(required=False)
    grade_name = serializers.CharField(required=False)
    joining_date = serializers.CharField(required=False)
    daily_loginTime = serializers.CharField(default="10:00:00")
    daily_logoutTime = serializers.CharField(default="19:00:00")
    lunch_start = serializers.CharField(default="13:30:00")
    lunch_end = serializers.CharField(default="14:00:00")
    salary_type = serializers.CharField(required=False, allow_null=True)
    cu_alt_email_id = serializers.CharField(required=False, allow_null=True)
    job_location_state = serializers.CharField(required=False)
    department = serializers.CharField(required=False)
    designation = serializers.CharField(required=False)
    sub_department = serializers.CharField(required=False, allow_null=True)
    total_granted_leaves = serializers.CharField(required=False, allow_null=True)
    attendance_type = serializers.CharField(required=False, allow_null=True)
    is_rejoin = serializers.BooleanField(required=False, default=False)
    is_transfer = serializers.BooleanField(required=False, default=False)
    previous_employee_id = serializers.IntegerField(required=False, default=0)

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'cu_phone_no', 'cu_emp_code', 'sap_personnel_no',
                  'created_by', 'cu_profile_img', 'hod', 'grade', 'sub_grade', 'mmr_module_id', 'mmr_type',
                  'reporting_head',
                  'reporting_head_name', 'hod_name', 'grade_name', 'joining_date', 'daily_loginTime',
                  'daily_logoutTime',
                  'lunch_start', 'lunch_end', 'company', 'cost_centre', 'cu_punch_id', 'salary_type',
                  'cu_alt_email_id', 'job_location_state', 'department', 'designation', 'sub_department',
                  'total_granted_leaves', 'attendance_type', 'is_rejoin', 'is_transfer', 'previous_employee_id')

    def create(self, validated_data):
        try:
            # print('valid111ated_data111',validated_data)
            is_rejoin = validated_data.pop('is_rejoin') if 'is_rejoin' in validated_data else ''
            print(is_rejoin)
            previous_employee_id = validated_data.pop('previous_employee_id') if validated_data else ''
            is_transfer = validated_data.pop('is_transfer') if 'is_transfer' in validated_data else ''
            print(is_transfer)
            cu_phone_no = validated_data.pop('cu_phone_no') if 'cu_phone_no' in validated_data else ''
            sub_grade = validated_data.pop('sub_grade') if 'sub_grade' in validated_data else ''

            cu_punch_id = validated_data.pop('cu_punch_id') if 'cu_punch_id' in validated_data else ''
            cu_emp_code = validated_data.pop('cu_emp_code') if 'cu_emp_code' in validated_data else ''
            company = validated_data.pop('company') if 'company' in validated_data.keys() else ''
            last_emp_code = TCoreUserDetail.objects.latest("id").cu_emp_code
            # last_coc_code = TCoreUserDetail.objects.latest("id").company.coc_code
            # last_emp_code = last_emp_code if last_emp_code else "0"
            # company_coc_code = TCoreCompany.objects.get(id=company).coc_code
            # # print(type(company_coc_code))
            # primary = "0{}".format(company_coc_code)
            # # print(primary)
            # try:
            #     last_emp_code = last_emp_code.split(last_coc_code)
            #     secondary = int(last_emp_code[-1]) + 1
            # except:
            #     secondary = 1

            # print(secondary)
            # cu_emp_code = "".join([primary,str(secondary)])
            # print(cu_emp_code)

            import random
            # try:
            #     last_file_no = TCoreUserDetail.objects.latest("id").file_no
            #     file_no = last_file_no + 1
            # except:
            #     file_no = random.randint(0,2000)

            hod = validated_data.pop('hod') if 'hod' in validated_data else ''

            # company=validated_data.pop('company') if 'company' in validated_data else ''
            cost_centre = validated_data.pop('cost_centre') if 'cost_centre' in validated_data else ''

            grade = validated_data.pop('grade')
            grade = '' if grade == 'null' else grade
            # grade = '' if validated_data.get('grade') == 'null' else validated_data.pop('grade')

            cu_profile_img = validated_data.pop('cu_profile_img') if 'cu_profile_img' in validated_data else ''

            sap_personnel_no = validated_data.pop('sap_personnel_no')
            sap_personnel_no = None if sap_personnel_no == 'null' else sap_personnel_no

            # print('sap_personnel_no',sap_personnel_no,type(sap_personnel_no))
            mmr_module_id = validated_data.pop('mmr_module_id') if 'mmr_module_id' in validated_data else ''
            mmr_type = validated_data.pop('mmr_type') if 'mmr_type' in validated_data else ''
            reporting_head = validated_data.pop('reporting_head') if 'reporting_head' in validated_data else ''
            joining_date = validated_data.pop('joining_date') if 'joining_date' in validated_data else None
            joining_date = datetime.datetime.strptime(joining_date, "%Y-%m-%dT%H:%M:%S.%fZ")

            salary_type = validated_data.pop('salary_type')
            salary_type = '' if salary_type == 'null' else salary_type

            attendance_type = validated_data.pop('attendance_type')
            attendance_type = '' if attendance_type == 'null' else attendance_type

            cu_alt_email_id = validated_data.pop('cu_alt_email_id')
            cu_alt_email_id = None if cu_alt_email_id == 'null' else cu_alt_email_id

            job_location_state = validated_data.pop(
                'job_location_state') if 'job_location_state' in validated_data else ''
            department = validated_data.pop('department')
            designation = validated_data.pop('designation')

            sub_department = validated_data.pop('sub_department')
            sub_department = '' if sub_department == 'null' else sub_department

            logdin_user_id = self.context['request'].user.id
            rejoin_by = self.context['request'].user
            role_details_list = []
            with transaction.atomic():
                # updated by Shubhadeep - handled blank space and same user name problem
                if validated_data.get('last_name') == 'null':
                    last_name_c = ''
                else:
                    last_name_c = validated_data.get('last_name')

                username_generate = validated_data.get('first_name') + last_name_c
                username_generate = username_generate.replace(' ', '')
                rejoin_username = username_generate

                check_user_exist = User.objects.filter(username=username_generate)
                i = 1
                while check_user_exist:
                    username_generate = username_generate + str(i)
                    check_user_exist = User.objects.filter(username=username_generate)
                    i += 1
                if is_rejoin:
                    print("in rejoin")
                    # rejoin_status
                    if previous_employee_id:
                        TCoreUserDetail.objects.filter(id=previous_employee_id).update(rejoin_status=True)
                    user = User.objects.create(first_name=validated_data.get('first_name'),
                                               last_name=last_name_c,
                                               username=username_generate,
                                               )
                    password = 'Shyam@123'
                    user.set_password(password)
                    personal_email = TCoreUserDetail.objects.get(id=previous_employee_id).cu_user.email
                    user.email = personal_email
                    user.save()
                    try:
                        previous_employee_obj = TCoreUserDetail.objects.get(id=previous_employee_id).cu_user.id
                        HrmsDynamicSectionFieldLabelDetailsWithDoc.objects.filter(user=previous_employee_obj,
                                                                                  is_deleted=False).update(user=user)
                        HrmsUserQualification.objects.filter(user=previous_employee_obj, is_deleted=False).update(
                            user=user)
                    except:
                        pass
                    try:
                        previous_employee_obj = TCoreUserDetail.objects.get(id=previous_employee_id)
                        previous_employee_obj = previous_employee_obj.__dict__
                        # from pprint import pprint
                        # pprint(previous_employee_obj)
                        ignoreable_field = ['cu_user_id', 'id', '_state', 'cu_phone_no', 'cu_profile_img',
                                            'password_to_know', 'cu_emp_code',
                                            'file_no', 'sap_personnel_no', 'daily_loginTime', 'daily_logoutTime',
                                            'lunch_start', 'lunch_end', 'hod_id', 'reporting_head_id', 'joining_date',
                                            'cu_created_by_id',
                                            'employee_grade_id', 'employee_sub_grade_id', 'company_id', 'cost_centre',
                                            'cu_punch_id',
                                            'salary_type_id', 'job_location_state_id', 'cu_alt_email_id',
                                            'department_id',
                                            'designation_id',
                                            'sub_department_id', 'granted_el', 'granted_leaves_cl_sl',
                                            'attendance_type',
                                            'user_type', 'is_rejoin', 'rejoin_date', 'rejoin_by_id', 'cu_is_deleted',
                                            'cu_change_pass','resignation_date', 'termination_date','rejoin_status','updated_cost_centre_id']

                        for each in ignoreable_field:
                            del previous_employee_obj[each]



                    except:
                        previous_employee_obj= {}
                        pass
                    user_detail = TCoreUserDetail.objects.create(
                        cu_user=user,
                        cu_phone_no=cu_phone_no,
                        cu_profile_img=cu_profile_img,
                        password_to_know=password,
                        cu_emp_code=cu_emp_code,
                        file_no=None,
                        sap_personnel_no=sap_personnel_no,
                        daily_loginTime=validated_data.get('daily_loginTime'),
                        daily_logoutTime=validated_data.get('daily_logoutTime'),
                        lunch_start=validated_data.get('lunch_start'),
                        lunch_end=validated_data.get('lunch_end'),
                        hod_id=hod,
                        reporting_head_id=reporting_head,
                        joining_date=joining_date,
                        cu_created_by_id=logdin_user_id,
                        employee_grade_id=grade,
                        employee_sub_grade_id=int(sub_grade) if sub_grade else None,
                        company_id=company,
                        #cost_centre=cost_centre,
                        updated_cost_centre_id=cost_centre,
                        cu_punch_id=cu_punch_id,
                        salary_type_id=salary_type,
                        job_location_state_id=job_location_state,
                        cu_alt_email_id=cu_alt_email_id,
                        department_id=department,
                        designation_id=designation,
                        sub_department_id=sub_department,
                        granted_el=float(0),
                        granted_leaves_cl_sl=float(0),
                        attendance_type=attendance_type,
                        user_type='User',
                        is_rejoin=True,
                        rejoin_date=datetime.datetime.now(),
                        rejoin_by=rejoin_by,
                        **previous_employee_obj
                    )
                    previous_employee = TCoreUserDetail.objects.get(id=previous_employee_id).cu_user
                    # print("*******************")
                    # print(previous_employee)
                    # print(type(previous_employee))
                    temp_rh_obj = UserTempReportingHeadMap.objects.filter(user__id=previous_employee.id)
                    print(temp_rh_obj)
                    for each in temp_rh_obj:
                        each.user = user
                        each.save()
                    usr_details_obj = TCoreUserDetail.objects.get(id=previous_employee_id)
                    usr_details_latest = TCoreUserDetail.objects.latest('id')
                    usr_details_latest.is_saturday_off = usr_details_obj.is_saturday_off
                    usr_details_latest.save()
                    saturday_off = AttendenceSaturdayOffMaster.objects.filter(employee__id=previous_employee.id)
                    for each in saturday_off:
                        each.employee = user
                        each.save()

                    try:
                        if not cu_profile_img:
                            usr_details_obj = TCoreUserDetail.objects.get(id=previous_employee_id)
                            usr_details_latest = TCoreUserDetail.objects.latest('id')
                            usr_details_latest.cu_profile_img = usr_details_obj.cu_profile_img
                            usr_details_latest.is_saturday_off = usr_details_obj.is_saturday_off
                            usr_details_latest.save()

                    except:
                        pass


                else:
                    user = User.objects.create(first_name=validated_data.get('first_name'),
                                               last_name=last_name_c,
                                               username=username_generate,
                                               )
                    password = 'Shyam@123'
                    user.set_password(password)
                    user.save()
                    user_detail = TCoreUserDetail.objects.create(
                        cu_user=user,
                        cu_phone_no=cu_phone_no,
                        cu_profile_img=cu_profile_img,
                        password_to_know=password,
                        cu_emp_code=cu_emp_code,
                        file_no=None,
                        sap_personnel_no=sap_personnel_no,
                        daily_loginTime=validated_data.get('daily_loginTime'),
                        daily_logoutTime=validated_data.get('daily_logoutTime'),
                        lunch_start=validated_data.get('lunch_start'),
                        lunch_end=validated_data.get('lunch_end'),
                        hod_id=hod,
                        reporting_head_id=reporting_head,
                        joining_date=joining_date,
                        cu_created_by_id=logdin_user_id,
                        employee_grade_id=grade,
                        employee_sub_grade_id=int(sub_grade) if sub_grade else None,
                        company_id=company,
                        cost_centre=cost_centre,
                        updated_cost_centre_id=cost_centre,
                        cu_punch_id=cu_punch_id,
                        salary_type_id=salary_type,
                        job_location_state_id=job_location_state,
                        cu_alt_email_id=cu_alt_email_id,
                        department_id=department,
                        designation_id=designation,
                        sub_department_id=sub_department,
                        granted_el=float(0),
                        granted_leaves_cl_sl=float(0),
                        attendance_type=attendance_type,
                        user_type='User'
                    )

                # print('user111111111111111111111',user,type(user))
                '''
                    Modified by Rupam Hazra to set default password
                '''
                '''modified on 04/12/2020 
                    by Swarup Adhikary(HRMS CR 15)'''
                usr_obj = TCoreUserDetail.objects.latest('id')
                if str(usr_obj.salary_type.st_code) == "AA":
                    usr_obj.granted_el = float(0)
                    usr_obj.granted_leaves_cl_sl = float(0)
                    usr_obj.save()
                    granted_cl = 0
                    granted_sl = 0
                    granted_el = 0
                elif str(usr_obj.salary_type.st_code) == "BB":
                    usr_obj.granted_el = float(15)
                    usr_obj.granted_leaves_cl_sl = float(10)
                    usr_obj.save()
                    granted_cl = 10
                    granted_sl = 0
                    granted_el = 15
                elif str(usr_obj.salary_type.st_code) == "FF":
                    usr_obj.granted_el = float(15)
                    usr_obj.granted_leaves_cl_sl = float(16)
                    usr_obj.save()
                    granted_cl = 16
                    granted_sl = 0
                    granted_el = 15
                elif str(usr_obj.salary_type.st_code) in ["CC", "DD"]:
                    usr_obj.granted_el = float(15)
                    usr_obj.granted_leaves_cl_sl = float(17)
                    usr_obj.save()
                    granted_cl = 10
                    granted_sl = 7
                    granted_el = 15
                elif str(usr_obj.salary_type.st_code) == "EE":
                    usr_obj.granted_el = float(15)
                    usr_obj.granted_leaves_cl_sl = float(16)
                    usr_obj.save()
                    granted_cl = 10
                    granted_sl = 6
                    granted_el = 15

                else:
                    granted_el = 0
                    granted_cl = 0
                    granted_sl = 0

                usr_obj.granted_el = granted_el
                usr_obj.granted_cl = granted_cl
                usr_obj.granted_sl = granted_sl
                usr_obj.save()
                # print('user_detail',user_detail)
                role_user = TMasterModuleRoleUser.objects.create(mmr_module_id=mmr_module_id,
                                                                 mmr_type=mmr_type,
                                                                 mmr_user=user,
                                                                 mmr_created_by=validated_data['created_by']
                                                                 )

                # joining_date = joining_date.date()
                # print('joining_date',joining_date)
                joining_year = joining_date.year
                # print('joining_year',joining_year)
                today = datetime.datetime.now()
                current_month = AttendenceMonthMaster.objects.get(
                    month_start__date__lte=today,
                    month_end__date__gte=today, is_deleted=False)
                year_start_date = current_month.year_start_date
                year_end_date = current_month.year_end_date
                joining_date = usr_obj.joining_date
                print(joining_date)
                from_date = year_start_date
                to_date = year_end_date
                print(from_date, to_date)
                is_joining_year = False
                if joining_date > from_date:
                    is_joining_year = True
                    from_date = joining_date
                leave_filter = {}
                print("from date????????", from_date)
                print("to date????????", to_date)

                attendenceMonthMaster = AttendenceMonthMaster.objects.filter(month_end__date__gte=from_date,
                                                                             month_end__date__lte=to_date,
                                                                             is_deleted=False).values('id',
                                                                                                      'grace_available',
                                                                                                      'year_start_date',
                                                                                                      'year_end_date',
                                                                                                      'month',
                                                                                                      'month_start',
                                                                                                      'month_end',
                                                                                                      'days_in_month',
                                                                                                      'payroll_month')
                print("attendenceMonthMaster-----------", attendenceMonthMaster)
                if attendenceMonthMaster:
                    available_grace = grace_calculation(joining_date.date(), attendenceMonthMaster)
                    # print('available_grace',available_grace)
                    year_end_date = attendenceMonthMaster[0]['year_end_date'].date()
                    month_start = attendenceMonthMaster[0]['month_start'].date()
                    # total_days = ((year_end_date - joining_date).days) + 1
                    total_days = ((to_date - from_date).days) + 1
                    # print('total_days',total_days)
                    cl,al,el,sl = 0,0,0,0
                    if user.cu_user.salary_type:
                        if user.cu_user.salary_type.st_code in ['FF', 'EE']:
                            al = round_calculation(total_days, (granted_cl + granted_sl + granted_el))
                        elif user.cu_user.salary_type.st_code in ['CC', 'DD']:
                            cl = round_calculation(total_days, granted_cl)
                            sl = round_calculation(total_days, granted_sl)
                            el = round_calculation(total_days, granted_el)
                        elif user.cu_user.salary_type.st_code in ['BB']:
                            cl = round_calculation(total_days, granted_cl)
                            # sl = round_calculation(total_days, granted_sl)
                            el = round_calculation(total_days, granted_el)
                        else:
                            pass

                    leave_confirm = round_calculation(total_days, (granted_cl + granted_sl + granted_el))
                    # leave_part_2_not_cofirm = round_calculation(total_days, (granted_cl + granted_sl))
                    # leave_part_2_not_cofirm = round_calculation(total_days, (granted_cl + granted_sl + granted_el))
                    leave_filter['granted_leaves_cl_sl'] = round_calculation(total_days, (granted_cl + granted_sl))
                    if granted_el:
                        leave_filter['el'] = round_calculation(total_days, granted_el)
                    else:
                        leave_filter['el'] = float(0)
                    leave_filter['cl'] = cl
                    leave_filter['sl'] = sl
                    users = [user.id]
                    roundOffLeaveCalculationUpdate(users, attendenceMonthMaster,
                                             leave_confirm, leave_confirm,
                                             total_days,
                                             year_end_date,attendenceMonthMaster[0]['month_start'], joining_date,
                                             cl, sl, el, al, is_joining_year)
                else:
                    available_grace = None
                if available_grace:
                    if attendenceMonthMaster[0]['year_start_date'].date() < joining_date.date():
                        JoiningApprovedLeave.objects.get_or_create(employee=user,
                                                                   year=joining_year,
                                                                   month=attendenceMonthMaster[0]['month'],
                                                                   **leave_filter,
                                                                   first_grace=available_grace,
                                                                   created_by=user,
                                                                   owned_by=user
                                                                   )

                if cu_alt_email_id:
                
                    # ============= Mail Send ==============#
                
                    # Send mail to employee with login details
                    mail_data = {
                        "name": user.first_name + '' + user.last_name,
                        "user": username_generate,
                        "pass": password
                    }
                    send_mail('EMP001', cu_alt_email_id, mail_data)
                
                    # Send mail to who added the employee
                    add_cu_alt_email_id = TCoreUserDetail.objects.filter(cu_user=self.context['request'].user)[0]
                    if add_cu_alt_email_id.cu_alt_email_id:
                        mail_data = {
                            "name": self.context['request'].user.first_name + ' ' + self.context[
                                'request'].user.last_name,
                            "user": username_generate,
                            "pass": password
                        }
                        send_mail('EMPA001', add_cu_alt_email_id.cu_alt_email_id, mail_data)

                data = {
                    'id': user.id,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'username': user.username,
                    'cu_emp_code': user_detail.cu_emp_code,

                }
                # print('data',data)
                return data

        except Exception as e:
            raise APIException({
                'request_status': 0,
                'msg': e
            })

class EmployeeLeaveAllocateV2Serializer(serializers.ModelSerializer):
    joining_date=serializers.CharField(required=False)
    request_status = serializers.CharField(required=False)
    msg = serializers.CharField(required=False)
    users = serializers.ListField(required=False)
    class Meta:
        model = User
        fields = ('id','joining_date','request_status','msg','users')

    def create(self,validated_data):
        try:
            joining_date = validated_data.get('joining_date') if 'joining_date' in validated_data else None
            users = validated_data.get('users') if 'users' in validated_data else None
            if joining_date:
                joining_date = datetime.datetime.strptime(joining_date, "%Y-%m-%dT%H:%M:%S.%fZ")
                joining_date=joining_date.date()
                #print('joining_date',joining_date)
                joining_year=joining_date.year
                #print('joining_year',joining_year)
                leave_filter={}

                attendenceMonthMaster=AttendenceMonthMaster.objects.filter(month_start__date__lte=joining_date,
                                month_end__date__gte=joining_date,is_deleted=False).values('id','grace_available',
                                                                            'year_start_date',
                                                                            'year_end_date',
                                                                            'month',
                                                                            'month_start',
                                                                            'month_end','days_in_month','payroll_month')
                granted_cl = 10
                granted_sl = 7
                granted_el = 15
                
                #print('attendenceMonthMaster',attendenceMonthMaster)
                if attendenceMonthMaster:
                    available_grace = grace_calculation(joining_date,attendenceMonthMaster)
                    print('available_grace',available_grace)
                    year_end_date = attendenceMonthMaster[0]['year_end_date'].date()
                    month_start = attendenceMonthMaster[0]['month_start'].date()
                    #month_end = attendenceMonthMaster[0]['month_end'].date()
                    total_days=((year_end_date - joining_date).days) + 1
                    print('total_days',total_days)
                    leave_part_1_confirm = round_calculation(total_days, (granted_cl + granted_sl + granted_el))
                    leave_part_2_not_cofirm = round_calculation(total_days, (granted_cl + granted_sl))
                    
                    print('leave_part_1_confirm leave_part_2_not_cofirm',leave_part_1_confirm,leave_part_2_not_cofirm)
                    users = [304]
                    roundOffLeaveCalculation(users,attendenceMonthMaster,
                    leave_part_1_confirm,leave_part_2_not_cofirm,total_days,year_end_date,month_start)
            else:
                from django.db.models import Q
                if users:
                    users = users
                else:
                    # users = User.objects.filter(is_superuser=False,is_active=True,id__in=(TCoreUserDetail.objects.filter(
                    # ~Q(cu_punch_id='#N/A'),termination_date__isnull=True, cu_is_deleted=False).values_list('cu_user',flat=True))).values_list('id',flat=True) 
                    # print('users',users,type(users))
                    # users = [2316]
                    # current_year = datetime.datetime.now().year
                    # print('current_year',current_year)
                    # total_days = 365
                    # leave_part_1_confirm = 32
                    # leave_part_2_not_cofirm = 17
                    # for user in users:
                    #     TCoreUserDetail.objects.filter(cu_user_id=user).update(granted_leaves_cl_sl='17')

                    query_set = JoiningApprovedLeave.objects.all()

                    for joining_approval_leave in query_set:
                        joining_approval_leave.granted_leaves_cl_sl = joining_approval_leave.cl + joining_approval_leave.sl
                        joining_approval_leave.save()
                    
                # attendenceMonthMaster=AttendenceMonthMaster.objects.filter(
                #     year_start_date__year=current_year,is_deleted=False).values('id','year_start_date',
                #                                                             'year_end_date',
                #                                                             'month',
                #                                                             'month_start',
                #                                                             'month_end','days_in_month','payroll_month')
                # print('attendenceMonthMaster',attendenceMonthMaster)
                # roundOffLeaveCalculation(users,attendenceMonthMaster,
                #     leave_part_1_confirm,leave_part_2_not_cofirm,total_days,
                #     attendenceMonthMaster[0]['year_end_date'],attendenceMonthMaster[0]['month_start'])

            return {
                'request_status':1,
                'msg':"created..",
                'users_count':users.count()
            }

        except Exception as e:
            raise APIException({
                'request_status': 0,
                'msg': e
            })



 
class EmployeeListSerializerv2(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    password = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    emp_code = serializers.SerializerMethodField()
    reporting_head = serializers.SerializerMethodField()
    hod_name = serializers.SerializerMethodField()
    joining_date = serializers.SerializerMethodField()
    sap_personnel_no = serializers.SerializerMethodField()
    punch_id = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()
    designation_name = serializers.SerializerMethodField()
    official_contact_no = serializers.SerializerMethodField()
    official_email_id = serializers.SerializerMethodField()
    user_type = serializers.SerializerMethodField()
    is_confirm = serializers.SerializerMethodField()
    salary_type = serializers.SerializerMethodField()
    grade = serializers.SerializerMethodField()
    sub_grade = serializers.SerializerMethodField()
    job_location = serializers.SerializerMethodField()
    salary_per_month = serializers.SerializerMethodField()
    vpf_no = serializers.SerializerMethodField()
    pf_no = serializers.SerializerMethodField()
    esic_no = serializers.SerializerMethodField()
    gender = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    state = serializers.SerializerMethodField()
    pincode = serializers.SerializerMethodField()
    emergency_relationship = serializers.SerializerMethodField()
    emergency_contact_no = serializers.SerializerMethodField()
    emergency_contact_name = serializers.SerializerMethodField()
    pan_no = serializers.SerializerMethodField()
    aadhar_no = serializers.SerializerMethodField()
    father_name = serializers.SerializerMethodField()
    marital_status = serializers.SerializerMethodField()
    personal_email_id = serializers.SerializerMethodField()
    bank_name = serializers.SerializerMethodField()
    bank_account = serializers.SerializerMethodField()
    ifsc_code = serializers.SerializerMethodField()
    blood_group = serializers.SerializerMethodField()
    bus_facility = serializers.SerializerMethodField()
    highest_qualification = serializers.SerializerMethodField()
    previous_employer = serializers.SerializerMethodField()
    total_experience = serializers.SerializerMethodField()





    def get_id(self, obj):
        return obj.id if obj.id else ''

    def get_username(self, obj):
        return obj.cu_user.username if obj.cu_user else ''
    def get_password(self, obj):
        return obj.password_to_know if obj.password_to_know else ''

    def get_first_name(self, obj):
        return obj.cu_user.first_name if obj.cu_user else ''

    def get_last_name(self, obj):
        return obj.cu_user.last_name if obj.cu_user else ''

    def get_emp_code(self, obj):
        return obj.cu_emp_code if obj.cu_emp_code else ''

    def get_reporting_head(self, obj):
        return obj.reporting_head.get_full_name() if obj.reporting_head else ''

    def get_hod_name(self, obj):

        return obj.hod.first_name if obj.hod else '' + ' ' + obj.hod.last_name if obj.hod else ''

    def get_joining_date(self, obj):
        return obj.joining_date if obj.joining_date else ''

    def get_sap_personnel_no(self, obj):

        return obj.sap_personnel_no if obj.sap_personnel_no else ''

    def get_punch_id(self,obj):
        return obj.cu_punch_id if obj.cu_punch_id else ''

    def get_company_name(self, obj):
        return obj.company.coc_name if obj.company else ''

    def get_department_name(self, obj):
        return  obj.department.cd_name if obj.department else ''

    def get_designation_name(self,obj):

        return  obj.designation.cod_name if obj.designation else ''

    def get_official_contact_no(self,obj):

        return obj.cu_alt_phone_no if obj.cu_alt_phone_no else ''

    def get_official_email_id(self,obj):

        return  obj.cu_alt_email_id if obj.cu_alt_email_id else ''
    def get_user_type(self,obj):

        return obj.user_type if obj.user_type else ''

    def get_is_confirm(self, obj):

        return obj.is_confirm if obj.is_confirm else ''

    def get_salary_type(self, obj):
        return obj.salary_type.st_name if obj.salary_type else ''

    def get_grade(self, obj):
        return obj.employee_grade.cg_name if obj.employee_grade else ''
    def get_sub_grade(self, obj):
        return obj.employee_sub_grade.name if obj.employee_sub_grade else ''

    def get_job_location(self,obj):
        return obj.job_location if obj.job_location else ''

    def get_salary_per_month(self,obj):
        return obj.salary_per_month if obj.salary_per_month else ''

    def get_vpf_no(self,obj):

        return obj.vpf_no if obj.vpf_no else 'No'


    def get_pf_no(self, obj):

        return obj.pf_no if obj.pf_no else 'No'

    def get_esic_no(self, obj):
        return  obj.esic_no if obj.esic_no else 'No'

    def get_gender(self, obj):
        return obj.cu_gender if obj.cu_gender else ''

    def get_address(self, obj):

        return  obj.address if obj.address else ''
    def get_state(self, obj):

        return obj.state.cs_state_name if obj.state else ''

    def get_pincode(self,obj):
        return obj.pincode if obj.pincode else ''

    def get_emergency_relationship(self,obj):
        return  obj.emergency_relationship if obj.emergency_relationship else ''

    def get_emergency_contact_no(self, obj):
        return obj.emergency_contact_no if obj.emergency_contact_no else ''

    def get_emergency_contact_name(self,obj):
        return obj.emergency_contact_name if obj.emergency_contact_name else ''

    def get_pan_no(self,obj):
        return obj.pan_no if obj.pan_no else ''

    def get_aadhar_no(self, obj):
        return  obj.aadhar_no if obj.aadhar_no else ''

    def get_father_name(self, obj):
        return obj.father_name if obj.father_name else ''

    def get_marital_status(self,obj):
        return obj.marital_status if obj.marital_status else ''

    def get_personal_email_id(self,obj):
        return  obj.cu_user.email if obj.cu_user else ''

    def get_bank_name(self, obj):

        return obj.bank_name_p.name if obj.bank_name_p else ''

    def get_bank_account(self, obj):
        return obj.bank_account if obj.bank_account else ''

    def get_ifsc_code(self,obj):
        return obj.ifsc_code if obj.ifsc_code else ''

    def get_blood_group(self,obj):
        return obj.blood_group if obj.blood_group else ''

    def get_bus_facility(self, obj):

        return obj.bus_facility if obj.bus_facility else ''
    def get_highest_qualification(self,obj):

        return  obj.highest_qualification if obj.highest_qualification else ''
    def get_previous_employer(self,obj):

        return obj.previous_employer if obj.previous_employer else ''
    def get_total_experience(self, obj):

        return obj.total_experience if  obj.total_experience else ''




    class Meta:
        model =  TCoreUserDetail
        fields = ('id', 'username', 'password' ,'first_name', 'last_name',  'reporting_head', 'hod_name', 'joining_date','emp_code',
                'sap_personnel_no', 'punch_id','company_name' ,'department_name', 'designation_name', 'official_contact_no', 'official_email_id',
                'user_type', 'is_confirm', 'salary_type', 'grade', 'sub_grade','job_location', 'salary_per_month', 'vpf_no', 'pf_no',
                'esic_no', 'gender', 'address', 'state', 'pincode', 'emergency_relationship', 'emergency_contact_no',
                'emergency_contact_name', 'emergency_contact_no', 'emergency_contact_name', 'pan_no', 'aadhar_no', 'father_name',
                'marital_status', 'personal_email_id', 'bank_name', 'bank_account', 'ifsc_code', 'blood_group', 'bus_facility',
                'highest_qualification', 'previous_employer', 'total_experience'
                )

    


class UnAppliedAttendanceSerializerv2(serializers.ModelSerializer):
    attendance_id =  serializers.SerializerMethodField()
    emp_code = serializers.SerializerMethodField()
    user_id = serializers.SerializerMethodField()
    reporting_head = serializers.SerializerMethodField()
    punch_id = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    phone_no = serializers.SerializerMethodField()
    sap_personnel_no = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    duration_start = serializers.SerializerMethodField()
    duration_end = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()

    def get_attendance_id(self, obj):
        if obj:
            at_id = obj.id
            return at_id
        else:
            return None

    # cu_emp_code
    def get_emp_code(self, obj):
        if obj.attendance:
            return obj.attendance.employee.cu_user.cu_emp_code if obj.attendance.employee.cu_user else None

    def get_user_id(self, obj):
        if obj.attendance:
            return obj.attendance.employee.id if obj.attendance.employee else None
    def get_reporting_head(self, obj):
        if obj.attendance:
            return obj.attendance.employee.cu_user.reporting_head.get_full_name() if obj.attendance.employee.cu_user.reporting_head else None
    def get_punch_id(self, obj):
        if obj.attendance:
            return obj.attendance.employee.cu_user.cu_punch_id if obj.attendance.employee.cu_user else None

    def get_name(self, obj):
        if obj.attendance:
            name = obj.attendance.employee.get_full_name()
            return name
        else:
            return None

    def get_phone_no(self, obj):
        if obj.attendance:
            return obj.attendance.employee.cu_user.cu_phone_no if obj.attendance.employee.cu_user else None

    def get_sap_personnel_no(self, obj):
        if obj.attendance:
            return obj.attendance.employee.cu_user.sap_personnel_no if obj.attendance.employee.cu_user else None

    def get_date(self, obj):
        if obj:
            return obj.attendance_date
        else:
            return None

    def get_duration_start(self, obj):
        if obj:
            name = obj.duration_start
            return name
        else:
            return None

    def get_duration_end(self, obj):
        if obj:
            company = obj.duration_end
            return company
        else:
            return None

    def get_duration(self, obj):
        if obj:
            duration = obj.duration
            return duration
        else:
            return None




    class Meta:
        model = AttendanceApprovalRequest
        fields = ('attendance_id', 'user_id','emp_code','punch_id','name', 'reporting_head','phone_no', 'sap_personnel_no',
                  'duration_start', 'duration_end', 'date','duration', 'request_type', 'justification')



class EmployeeListUnderReportingHeadSerializerv2(serializers.ModelSerializer):
    emp_id = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    password = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    emp_code = serializers.SerializerMethodField()
    reporting_head = serializers.SerializerMethodField()
    reporting_head_id = serializers.SerializerMethodField()
    hod_name = serializers.SerializerMethodField()
    joining_date = serializers.SerializerMethodField()
    sap_personnel_no = serializers.SerializerMethodField()
    # punch_id = serializers.SerializerMethodField()
    # company_name = serializers.SerializerMethodField()
    department_id = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()
    designation_name = serializers.SerializerMethodField()
    designation_id = serializers.SerializerMethodField()
    # official_contact_no = serializers.SerializerMethodField()
    # official_email_id = serializers.SerializerMethodField()
    # user_type = serializers.SerializerMethodField()
    # is_confirm = serializers.SerializerMethodField()
    # salary_type = serializers.SerializerMethodField()
    # grade = serializers.SerializerMethodField()
    # job_location = serializers.SerializerMethodField()
    # salary_per_month = serializers.SerializerMethodField()
    # vpf_no = serializers.SerializerMethodField()
    # pf_no = serializers.SerializerMethodField()
    # esic_no = serializers.SerializerMethodField()
    # gender = serializers.SerializerMethodField()
    # address = serializers.SerializerMethodField()
    # state = serializers.SerializerMethodField()
    # pincode = serializers.SerializerMethodField()
    # emergency_relationship = serializers.SerializerMethodField()
    # emergency_contact_no = serializers.SerializerMethodField()
    # emergency_contact_name = serializers.SerializerMethodField()
    # pan_no = serializers.SerializerMethodField()
    # aadhar_no = serializers.SerializerMethodField()
    # father_name = serializers.SerializerMethodField()
    # marital_status = serializers.SerializerMethodField()
    # personal_email_id = serializers.SerializerMethodField()
    # bank_name = serializers.SerializerMethodField()
    # bank_account = serializers.SerializerMethodField()
    # ifsc_code = serializers.SerializerMethodField()
    # blood_group = serializers.SerializerMethodField()
    # bus_facility = serializers.SerializerMethodField()
    # highest_qualification = serializers.SerializerMethodField()
    # previous_employer = serializers.SerializerMethodField()
    # total_experience = serializers.SerializerMethodField()
    salary_type = serializers.SerializerMethodField()





    def get_emp_id(self, obj):
        return obj.cu_user.id if obj.cu_user.id else ''

    def get_username(self, obj):
        return obj.cu_user.username if obj.cu_user else ''
    def get_password(self, obj):
        return obj.password_to_know if obj.password_to_know else ''

    def get_first_name(self, obj):
        return obj.cu_user.first_name if obj.cu_user else ''

    def get_last_name(self, obj):
        return obj.cu_user.last_name if obj.cu_user else ''

    def get_emp_code(self, obj):
        return obj.cu_emp_code if obj.cu_emp_code else ''

    def get_reporting_head(self, obj):
        return obj.reporting_head.get_full_name() if obj.reporting_head else ''
    def get_reporting_head_id(self, obj):
        return obj.reporting_head.id if obj.reporting_head else ''


    def get_hod_name(self, obj):

        return obj.hod.get_full_name() if obj.hod else ''

    def get_joining_date(self, obj):
        return obj.joining_date if obj.joining_date else ''

    def get_sap_personnel_no(self, obj):

        return obj.sap_personnel_no if obj.sap_personnel_no else ''

    # def get_punch_id(self,obj):
    #     #     return obj.cu_punch_id if obj.cu_punch_id else ''
    #     #
    #     # def get_company_name(self, obj):
    #     #     return obj.company.coc_name if obj.company else ''

    def get_department_name(self, obj):
        return  obj.department.cd_name if obj.department else ''
    def get_department_id(self, obj):
        return  obj.department.id if obj.department else ''

    def get_designation_name(self,obj):

        return  obj.designation.cod_name if obj.designation else ''
    def get_designation_id(self,obj):

        return  obj.designation.id if obj.designation else ''
    def get_salary_type(self,obj):
        return obj.salary_type.st_name if obj.salary_type else ''

    # def get_official_contact_no(self,obj):
    #
    #     return obj.cu_alt_phone_no if obj.cu_alt_phone_no else ''
    #
    # def get_official_email_id(self,obj):
    #
    #     return  obj.cu_alt_email_id if obj.cu_alt_email_id else ''
    # def get_user_type(self,obj):
    #
    #     return obj.user_type if obj.user_type else ''
    #
    # def get_is_confirm(self, obj):
    #
    #     return obj.is_confirm if obj.is_confirm else ''
    #
    # def get_salary_type(self, obj):
    #     return obj.salary_type.st_name if obj.salary_type else ''
    #
    # def get_grade(self, obj):
    #     return obj.employee_grade.cg_name if obj.employee_grade else ''
    #
    # def get_job_location(self,obj):
    #     return obj.job_location if obj.job_location else ''
    #
    # def get_salary_per_month(self,obj):
    #     return obj.salary_per_month if obj.salary_per_month else ''
    #
    # def get_vpf_no(self,obj):
    #
    #     return obj.vpf_no if obj.vpf_no else 'No'
    #
    #
    # def get_pf_no(self, obj):
    #
    #     return obj.pf_no if obj.pf_no else 'No'
    #
    # def get_esic_no(self, obj):
    #     return  obj.esic_no if obj.esic_no else 'No'
    #
    # def get_gender(self, obj):
    #     return obj.cu_gender if obj.cu_gender else ''
    #
    # def get_address(self, obj):
    #
    #     return  obj.address if obj.address else ''
    # def get_state(self, obj):
    #
    #     return obj.state.cs_state_name if obj.state else ''
    #
    # def get_pincode(self,obj):
    #     return obj.pincode if obj.pincode else ''
    #
    # def get_emergency_relationship(self,obj):
    #     return  obj.emergency_relationship if obj.emergency_relationship else ''
    #
    # def get_emergency_contact_no(self, obj):
    #     return obj.emergency_contact_no if obj.emergency_contact_no else ''
    #
    # def get_emergency_contact_name(self,obj):
    #     return obj.emergency_contact_name if obj.emergency_contact_name else ''
    #
    # def get_pan_no(self,obj):
    #     return obj.pan_no if obj.pan_no else ''
    #
    # def get_aadhar_no(self, obj):
    #     return  obj.aadhar_no if obj.aadhar_no else ''
    #
    # def get_father_name(self, obj):
    #     return obj.father_name if obj.father_name else ''
    #
    # def get_marital_status(self,obj):
    #     return obj.marital_status if obj.marital_status else ''
    #
    # def get_personal_email_id(self,obj):
    #     return  obj.cu_user.email if obj.cu_user else ''
    #
    # def get_bank_name(self, obj):
    #
    #     return obj.bank_name_p.name if obj.bank_name_p else ''
    #
    # def get_bank_account(self, obj):
    #     return obj.bank_account if obj.bank_account else ''
    #
    # def get_ifsc_code(self,obj):
    #     return obj.ifsc_code if obj.ifsc_code else ''
    #
    # def get_blood_group(self,obj):
    #     return obj.blood_group if obj.blood_group else ''
    #
    # def get_bus_facility(self, obj):
    #
    #     return obj.bus_facility if obj.bus_facility else ''
    # def get_highest_qualification(self,obj):
    #
    #     return  obj.highest_qualification if obj.highest_qualification else ''
    # def get_previous_employer(self,obj):
    #
    #     return obj.previous_employer if obj.previous_employer else ''
    # def get_total_experience(self, obj):
    #
    #     return obj.total_experience if  obj.total_experience else ''




    class Meta:
        model =  TCoreUserDetail
        fields = ('emp_id', 'username', 'password' ,'first_name', 'last_name',  'reporting_head','reporting_head_id', 'hod_name', 'joining_date','emp_code',
                'sap_personnel_no','department_name', 'designation_name','designation_id','department_id','salary_type'
                )


class ResignedReportingHeadDetailSerializer(serializers.ModelSerializer):
    email = serializers.SerializerMethodField()
    sap_personnel_no = serializers.SerializerMethodField()
    emp_code = serializers.SerializerMethodField()

    department_name = serializers.SerializerMethodField()
    designation_name = serializers.SerializerMethodField()
    resignation_date = serializers.SerializerMethodField()
    release_date = serializers.SerializerMethodField()

    def get_sap_personnel_no(self, obj):

        return obj.cu_user.sap_personnel_no if obj.cu_user.sap_personnel_no else ''
    def get_email(self, obj):

        return obj.email if obj.email else ''

    def get_emp_code(self, obj):
        return obj.cu_user.cu_emp_code if obj.cu_user.cu_emp_code else ''

    def get_resignation_date(self, obj):
        return obj.cu_user.resignation_date if obj.cu_user.resignation_date else ''

    def get_release_date(self, obj):
        return obj.cu_user.termination_date if obj.cu_user.termination_date else ''


    def get_department_name(self, obj):
        return  obj.cu_user.department.cd_name if obj.cu_user.department else ''

    def get_designation_name(self,obj):

        return  obj.cu_user.designation.cod_name if obj.cu_user.designation else ''
    class Meta:
        model = User
        fields = ('id','first_name', 'last_name', 'username','emp_code','email' ,'resignation_date','release_date','department_name',
                  'designation_name','sap_personnel_no')



class EmployeeListForRhSerializer(serializers.ModelSerializer):
    emp_code = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    sap_personnel_no = serializers.SerializerMethodField()
    def get_emp_code(self,obj):
        if obj.cu_user:
            return obj.cu_user.cu_emp_code
        else:
            return None

    def get_name(self,obj):
        return obj.get_full_name()

    def get_sap_personnel_no(self, obj):

        return obj.cu_user.sap_personnel_no if obj.cu_user.sap_personnel_no else ''

    class Meta:
        model = User
        fields= ('id','username','first_name','last_name','name','emp_code','sap_personnel_no')


class ProbationAddSerializer(serializers.ModelSerializer):
    employee = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = HrmsThreeMonthsProbationReviewForm
        fields = ('__all__')

    def create(self,validated_data):
        try:
            with transaction.atomic():
                user_id = validated_data.get('employee')
                print(user_id.id)
                tcore_usr_obj = TCoreUserDetail.objects.get(cu_user=user_id.id)
                tcore_usr_obj.first_probation_submission_status = True
                tcore_usr_obj.save()
                travel_master, created = HrmsThreeMonthsProbationReviewForm.objects.get_or_create(**validated_data)
                return travel_master
        except Exception as e:
            raise e

class UserDetailForProbationAddSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    emp_code = serializers.SerializerMethodField()
    reporting_head = serializers.SerializerMethodField()
    hod_name = serializers.SerializerMethodField()
    joining_date = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()
    designation_name = serializers.SerializerMethodField()
    probation_date = serializers.SerializerMethodField()


    def get_employee_name(self, obj):
        return obj.cu_user.get_full_name() if obj.cu_user else ''

    def get_emp_code(self, obj):
        return obj.cu_emp_code if obj.cu_emp_code else ''

    def get_reporting_head(self, obj):
        return obj.reporting_head.get_full_name() if obj.reporting_head else ''

    def get_hod_name(self, obj):
        return obj.hod.get_full_name() if obj.hod else ''

    def get_joining_date(self, obj):
        return obj.joining_date if obj.joining_date else ''
    def get_probation_date(self,obj):

        return obj.joining_date + relativedelta(months=+3)if obj.joining_date else ''

    def get_department_name(self, obj):
        return obj.department.cd_name if obj.department else ''

    def get_designation_name(self, obj):
        return obj.designation.cod_name if obj.designation else ''




    class Meta:
        model = TCoreUserDetail
        fields = (
         'employee_name', 'reporting_head', 'hod_name',
        'joining_date', 'probation_date','emp_code', 'department_name', 'designation_name'
        )

class PendingProbationEmployeeListSerializerv2(serializers.ModelSerializer):
    employee_id = serializers.SerializerMethodField()
    employee_name = serializers.SerializerMethodField()
    emp_code = serializers.SerializerMethodField()
    emp_email_id = serializers.SerializerMethodField()
    email_body = serializers.SerializerMethodField()
    email_subject = serializers.SerializerMethodField()
    reporting_head_name = serializers.SerializerMethodField()
    hod_name = serializers.SerializerMethodField()
    joining_date = serializers.SerializerMethodField()
    sap_personnel_no = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()
    designation_name = serializers.SerializerMethodField()
    official_email_id = serializers.SerializerMethodField()
    company = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    reporting_head_email = serializers.SerializerMethodField()
    reporting_head_id = serializers.SerializerMethodField()
    company_id = serializers.SerializerMethodField()
    probation_date = serializers.SerializerMethodField()
    mail_shoot_date = serializers.SerializerMethodField()


    def get_employee_id(self, obj):
        return obj.id if obj.id else ''

    def get_company(self, obj):
        return obj.company.coc_name if obj.company.coc_name else ''

    def get_company_id(self, obj):
        return obj.company.id if obj.company else ''

    def get_location(self, obj):
        return obj.job_location if obj.job_location else ''

    def get_employee_name(self, obj):
        return obj.cu_user.get_full_name() if obj.cu_user else ''

    def get_emp_email_id(self, obj):
        return obj.cu_alt_email_id if obj else ''

    def get_email_body(self, obj):
        mail_body = '''<table border="0" cellpadding="0" cellspacing="0" width="100%" style="border: 1px solid #cecece; padding: 10px;">
	<tr>
		<td colspan="2">
			<p style="padding-bottom:5px;">Dear  Ms./Mr/Mrs {},</p>
			<p style="padding-bottom:10px;">We haven’t received your Probation review form yet. Request you to visit the link below and fill up the form at the earliest.</p>
		</td>
	</tr>
	<tr>
		<td>
			<a href={{link}}>Link to the form</a>
		</td>
	</tr>
	<tr>
		<td colspan="2" align="left" style="padding-top:10px;">
			<p>Regards,
				<br>
					<b> HR Team</b>
				</p>
			</td>
		</tr>
	</table>'''.format(obj.cu_user.last_name)
        return mail_body

    def get_email_subject(self, obj):
        mail_sub = "3 Months Probation Review Form"
        return mail_sub

    def get_emp_code(self, obj):
        return obj.cu_emp_code if obj.cu_emp_code else ''

    def get_reporting_head_name(self, obj):
        return obj.reporting_head.get_full_name() if obj.reporting_head else ''

    def get_reporting_head_id(self, obj):
        return obj.reporting_head.id if obj.reporting_head else ''

    def get_hod_name(self, obj):

        return obj.hod.get_full_name() if obj.hod else ''

    def get_joining_date(self, obj):
        return obj.joining_date if obj.joining_date else ''

    def get_sap_personnel_no(self, obj):

        return obj.sap_personnel_no if obj.sap_personnel_no else ''


    def get_department_name(self, obj):
        return obj.department.cd_name if obj.department else ''

    def get_designation_name(self,obj):

        return obj.designation.cod_name if obj.designation else ''


    def get_official_email_id(self,obj):

        return obj.cu_alt_email_id if obj.cu_alt_email_id else ''
    def get_reporting_head_email(self,obj):

        return obj.reporting_head.cu_user.cu_alt_email_id if obj.reporting_head.cu_user.cu_alt_email_id else ''
    def get_probation_date(self,obj):
        probation_review_obj = HrmsThreeMonthsProbationReviewForm.objects.filter(employee=obj.cu_user)[0]
        if probation_review_obj.created_at:
            # print(probation_review_obj)
            return probation_review_obj.created_at
        else:
            return None

    def get_mail_shoot_date(self,obj):
        probation_review_obj = HrmsThreeMonthsProbationReviewForm.objects.filter(employee=obj.cu_user)[0]
        if probation_review_obj.created_at:
            # print(probation_review_obj)
            return probation_review_obj.created_at
        else:
            return None


    class Meta:
        model = TCoreUserDetail
        fields = ('employee_id', 'employee_name', 'emp_email_id','email_body','email_subject','reporting_head', 'reporting_head_name','hod','hod_name', 'joining_date','emp_code',
                'sap_personnel_no', 'department_name', 'department','designation_name','designation','official_email_id','company', 'company_id','location',
                  'reporting_head_email', 'reporting_head_id', 'probation_date','mail_shoot_date'
                )


class PendingProbationReportingHeadListSerializerv2(serializers.ModelSerializer):
    employee_id = serializers.SerializerMethodField()
    employee_name = serializers.SerializerMethodField()
    emp_code = serializers.SerializerMethodField()
    emp_email_id = serializers.SerializerMethodField()
    email_body = serializers.SerializerMethodField()
    email_subject = serializers.SerializerMethodField()
    reporting_head_name = serializers.SerializerMethodField()
    hod_name = serializers.SerializerMethodField()
    joining_date = serializers.SerializerMethodField()
    sap_personnel_no = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()
    designation_name = serializers.SerializerMethodField()
    official_email_id = serializers.SerializerMethodField()
    company = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    reporting_head_email = serializers.SerializerMethodField()
    reporting_head_id = serializers.SerializerMethodField()
    company_id = serializers.SerializerMethodField()
    probation_date = serializers.SerializerMethodField()
    mail_shoot_date = serializers.SerializerMethodField()


    def get_employee_id(self, obj):
        return obj.id if obj.id else ''

    def get_company(self, obj):
        return obj.company.coc_name if obj.company.coc_name else ''

    def get_company_id(self, obj):
        return obj.company.id if obj.company else ''

    def get_location(self, obj):
        return obj.job_location if obj.job_location else ''

    def get_employee_name(self, obj):
        return obj.cu_user.get_full_name() if obj.cu_user else ''

    def get_emp_email_id(self, obj):
        return obj.cu_alt_email_id if obj else ''

    def get_email_body(self, obj):
        mail_body = '''<table border="0" cellpadding="0" cellspacing="0" width="100%" style="border: 1px solid #cecece; padding: 10px;">
	<tr>
		<td colspan="2">
			<p style="padding-bottom:5px;">Dear  Ms./Mr/Mrs {},</p>
			<p style="padding-bottom:10px;">We haven’t received the 3 months Probation review form for {}, {} yet.
Request you to visit the link below and fill up the form at the earliest.</p>
		</td>
	</tr>
	<tr>
		<td>
			<a href={{link}}>Link to the form</a>
		</td>
	</tr>
	<tr>
		<td colspan="2" align="left" style="padding-top:10px;">
			<p>Regards,
				<br>
					<b> HR Team</b>
				</p>
			</td>
		</tr>
	</table>'''.format(obj.cu_user.last_name, obj.cu_user.get_full_name(),obj.designation.cod_name)
        return mail_body

    def get_email_subject(self, obj):
        mail_sub = "3 Months Probation Review Form: {}, {}".format(obj.cu_user.get_full_name(),obj.designation.cod_name)
        return mail_sub

    def get_emp_code(self, obj):
        return obj.cu_emp_code if obj.cu_emp_code else ''

    def get_reporting_head_name(self, obj):
        return obj.reporting_head.get_full_name() if obj.reporting_head else ''

    def get_reporting_head_id(self, obj):
        return obj.reporting_head.id if obj.reporting_head else ''

    def get_hod_name(self, obj):

        return obj.hod.get_full_name() if obj.hod else ''

    def get_joining_date(self, obj):
        return obj.joining_date if obj.joining_date else ''

    def get_sap_personnel_no(self, obj):

        return obj.sap_personnel_no if obj.sap_personnel_no else ''


    def get_department_name(self, obj):
        return obj.department.cd_name if obj.department else ''

    def get_designation_name(self,obj):

        return obj.designation.cod_name if obj.designation else ''


    def get_official_email_id(self,obj):

        return obj.cu_alt_email_id if obj.cu_alt_email_id else ''
    def get_reporting_head_email(self,obj):

        return obj.reporting_head.cu_user.cu_alt_email_id if obj.reporting_head.cu_user.cu_alt_email_id else ''
    def get_probation_date(self,obj):
        probation_review_obj = HrmsThreeMonthsProbationReviewForm.objects.filter(employee=obj.cu_user)[0]
        if probation_review_obj.created_at:
            # print(probation_review_obj)
            return probation_review_obj.created_at
        else:
            return None

    def get_mail_shoot_date(self,obj):
        probation_review_obj = HrmsThreeMonthsProbationReviewForm.objects.filter(employee=obj.cu_user)[0]
        if probation_review_obj.created_at:
            # print(probation_review_obj)
            return probation_review_obj.created_at
        else:
            return None


    class Meta:
        model = TCoreUserDetail
        fields = ('employee_id', 'employee_name', 'emp_email_id','email_body','email_subject','reporting_head', 'reporting_head_name','hod','hod_name', 'joining_date','emp_code',
                'sap_personnel_no', 'department_name', 'department','designation_name','designation','official_email_id','company', 'company_id','location',
                  'reporting_head_email', 'reporting_head_id', 'probation_date','mail_shoot_date'
                )


class PendingProbationAddSerializer(serializers.ModelSerializer):
    # employee = serializers.CharField(default=serializers.CurrentUserDefault())
    employee_name = serializers.SerializerMethodField(required=False)
    emp_code = serializers.SerializerMethodField(required=False)
    reporting_head_name = serializers.SerializerMethodField(required=False)
    hod_name = serializers.SerializerMethodField(required=False)
    joining_date = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()
    designation_name = serializers.SerializerMethodField()
    probation_date = serializers.SerializerMethodField()

    def get_employee_name(self, obj):
        return obj.employee.get_full_name() if obj.employee else ''

    def get_emp_code(self, obj):
        return obj.employee.cu_user.cu_emp_code if obj.employee.cu_user.cu_emp_code else ''

    def get_reporting_head_name(self, obj):
        return obj.employee.cu_user.reporting_head.get_full_name() if obj.employee.cu_user.reporting_head else ''

    def get_hod_name(self, obj):
        return obj.employee.cu_user.hod.get_full_name() if obj.employee.cu_user.hod else ''

    def get_joining_date(self, obj):
        return obj.employee.cu_user.joining_date if obj.employee.cu_user.joining_date else ''
    def get_probation_date(self,obj):

        return obj.created_at if obj.created_at else ''

    def get_department_name(self, obj):
        return obj.employee.cu_user.department.cd_name if obj.employee.cu_user.department else ''

    def get_designation_name(self, obj):
        return obj.employee.cu_user.designation.cod_name if obj.employee.cu_user.designation else ''

    class Meta:
        model = HrmsThreeMonthsProbationReviewForm
        fields = ('id','employee_name','emp_code','reporting_head_name','hod_name',
                  'joining_date', 'probation_date','department_name', 'designation_name',
                  'how_do_you_like_your_job_as_of_now','is_the_work_allotted_to_you_as_per_your_JD',
                  'what_is_it_that_you_are_working_on','have_you_been_explained_the_work_that_you_need_to_do',
                  'have_you_been_able_to_understand_the_teams_responsibilities',
                  'have_you_been_given_enough_knowledge_on_your_job_profile',
                  'do_you_think_you_are_able_to_fit_in_with_the_JD',
                  'have_you_been_made_aware_of_your_targets_KRAs','would_you_want_hr_to_address_any_issue',
                  'submission_pending','submission_pending')

    def update(self, instance, validated_data):
        try:
            with transaction.atomic():
                print(validated_data.get('how_do_you_like_your_job_as_of_now'))
                instance.how_do_you_like_your_job_as_of_now = validated_data.get('how_do_you_like_your_job_as_of_now') if 'how_do_you_like_your_job_as_of_now' in validated_data else 'No'
                instance.is_the_work_allotted_to_you_as_per_your_JD = validated_data.get('is_the_work_allotted_to_you_as_per_your_JD') if 'is_the_work_allotted_to_you_as_per_your_JD' in validated_data else 'No'
                instance.what_is_it_that_you_are_working_on = validated_data.get('what_is_it_that_you_are_working_on') if 'what_is_it_that_you_are_working_on' in validated_data else None
                instance.have_you_been_explained_the_work_that_you_need_to_do = validated_data.get('have_you_been_explained_the_work_that_you_need_to_do') if 'have_you_been_explained_the_work_that_you_need_to_do' in validated_data else 'No'
                instance.have_you_been_able_to_understand_the_teams_responsibilities = validated_data.get('have_you_been_able_to_understand_the_teams_responsibilities') if 'have_you_been_able_to_understand_the_teams_responsibilities' in validated_data else 'No'
                instance.have_you_been_given_enough_knowledge_on_your_job_profile = validated_data.get('have_you_been_given_enough_knowledge_on_your_job_profile') if 'have_you_been_given_enough_knowledge_on_your_job_profile' in validated_data else 'No'
                instance.do_you_think_you_are_able_to_fit_in_with_the_JD = validated_data.get('do_you_think_you_are_able_to_fit_in_with_the_JD') if 'do_you_think_you_are_able_to_fit_in_with_the_JD' in validated_data else 'No'
                instance.have_you_been_made_aware_of_your_targets_KRAs = validated_data.get('have_you_been_made_aware_of_your_targets_KRAs') if 'have_you_been_made_aware_of_your_targets_KRAs' in validated_data else 'No'
                instance.would_you_want_hr_to_address_any_issue = validated_data.get('would_you_want_hr_to_address_any_issue') if 'would_you_want_hr_to_address_any_issue' in validated_data else None
                instance.submission_pending = False
                instance.owned_by = instance.employee
                instance.updated_by = instance.employee
                instance.save()
                ins,data=HrmsThreeMonthsProbationReviewForApproval.objects.get_or_create(employee_form=instance)
                import base64
                obj = HrmsThreeMonthsProbationReviewForApproval.objects.latest('id')
                sample_string = str(obj.id)
                sample_string_bytes = sample_string.encode("ascii")
                base64_bytes = base64.b64encode(sample_string_bytes)
                base64_id = base64_bytes.decode("ascii")
                print(base64_id)
                user_email = instance.employee.cu_user.reporting_head.cu_user.cu_alt_email_id
                second_name = instance.employee.cu_user.reporting_head.last_name
                employee_name = instance.employee.get_full_name()
                designation = instance.employee.cu_user.designation.cod_name
                print(user_email)
                print(second_name)
                print(designation, employee_name)
                server_url = settings.SERVER_URL
                server_url = server_url.split(':' + server_url.split(':')[-1])[0]
                if user_email:
                    mail_data = {
                        "employee_name": employee_name,
                        "designation": designation,
                        "second_name": second_name,
                        "link": "http://3.7.231.128/hrms" + "/#/probation-form-review/" + base64_id,
                    }
                    from global_function import send_mail
                    sub = str(employee_name) + ',' + str(designation)
                    send_mail('HRMS-3P-RH-1R', user_email, mail_data,final_sub=sub)
                    date = datetime.datetime.now()
                    HrmsThreeMonthsProbationReviewForApproval.objects.filter(id=obj.id).update(reminder_state=0,
                                                                                               reminder_date=date,
                                                                                               first_reminder_date=date)

                return instance
        except Exception as e:
            raise e


class PendingProbationReviewAddSerializer(serializers.ModelSerializer):
    # employee = serializers.CharField(default=serializers.CurrentUserDefault())
    employee_name = serializers.SerializerMethodField(required=False)
    emp_code = serializers.SerializerMethodField(required=False)
    reporting_head_name = serializers.SerializerMethodField(required=False)
    hod_name = serializers.SerializerMethodField(required=False)
    joining_date = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()
    designation_name = serializers.SerializerMethodField()
    probation_date = serializers.SerializerMethodField()
    how_do_you_like_your_job_as_of_now = serializers.SerializerMethodField(required=False)
    is_the_work_allotted_to_you_as_per_your_JD = serializers.SerializerMethodField(required=False)
    what_is_it_that_you_are_working_on = serializers.SerializerMethodField(required=False)
    have_you_been_explained_the_work_that_you_need_to_do = serializers.SerializerMethodField(required=False)
    have_you_been_able_to_understand_the_teams_responsibilities = serializers.SerializerMethodField(required=False)
    have_you_been_given_enough_knowledge_on_your_job_profile = serializers.SerializerMethodField(required=False)
    do_you_think_you_are_able_to_fit_in_with_the_JD = serializers.SerializerMethodField(required=False)
    have_you_been_made_aware_of_your_targets_KRAs = serializers.SerializerMethodField(required=False)
    would_you_want_hr_to_address_any_issue = serializers.SerializerMethodField(required=False)

    def get_how_do_you_like_your_job_as_of_now(self,obj):
        return obj.employee_form.how_do_you_like_your_job_as_of_now if obj.employee_form.how_do_you_like_your_job_as_of_now else 'No'
    def get_is_the_work_allotted_to_you_as_per_your_JD(self,obj):
        return obj.employee_form.is_the_work_allotted_to_you_as_per_your_JD if obj.employee_form.is_the_work_allotted_to_you_as_per_your_JD else 'No'
    def get_what_is_it_that_you_are_working_on(self,obj):
        return obj.employee_form.what_is_it_that_you_are_working_on if obj.employee_form.what_is_it_that_you_are_working_on else ''

    def get_have_you_been_explained_the_work_that_you_need_to_do(self,obj):
        return obj.employee_form.have_you_been_explained_the_work_that_you_need_to_do if obj.employee_form.have_you_been_explained_the_work_that_you_need_to_do else 'No'
    def get_have_you_been_able_to_understand_the_teams_responsibilities(self,obj):
        return obj.employee_form.have_you_been_able_to_understand_the_teams_responsibilities if obj.employee_form.have_you_been_able_to_understand_the_teams_responsibilities else 'No'
    def get_have_you_been_given_enough_knowledge_on_your_job_profile(self,obj):
        return obj.employee_form.have_you_been_given_enough_knowledge_on_your_job_profile if obj.employee_form.have_you_been_given_enough_knowledge_on_your_job_profile else 'No'
    def get_do_you_think_you_are_able_to_fit_in_with_the_JD(self,obj):
        return obj.employee_form.do_you_think_you_are_able_to_fit_in_with_the_JD if obj.employee_form.do_you_think_you_are_able_to_fit_in_with_the_JD else 'No'

    def get_have_you_been_made_aware_of_your_targets_KRAs(self,obj):
        return obj.employee_form.have_you_been_made_aware_of_your_targets_KRAs if obj.employee_form.have_you_been_made_aware_of_your_targets_KRAs else 'No'
    def get_would_you_want_hr_to_address_any_issue(self,obj):
        return obj.employee_form.would_you_want_hr_to_address_any_issue if obj.employee_form.would_you_want_hr_to_address_any_issue else ''

    def get_employee_name(self, obj):
        return obj.employee_form.employee.get_full_name() if obj.employee_form.employee else ''

    def get_emp_code(self, obj):
        return obj.employee_form.employee.cu_user.cu_emp_code if obj.employee_form.employee.cu_user.cu_emp_code else ''

    def get_reporting_head_name(self, obj):
        return obj.employee_form.employee.cu_user.reporting_head.get_full_name() if obj.employee_form.employee.cu_user.reporting_head else ''

    def get_hod_name(self, obj):
        return obj.employee_form.employee.cu_user.hod.get_full_name() if obj.employee_form.employee.cu_user.hod else ''

    def get_joining_date(self, obj):
        return obj.employee_form.employee.cu_user.joining_date if obj.employee_form.employee.cu_user.joining_date else ''
    def get_probation_date(self,obj):

        return obj.employee_form.created_at if obj.employee_form.created_at else ''

    def get_department_name(self, obj):
        return obj.employee_form.employee.cu_user.department.cd_name if obj.employee_form.employee.cu_user.department else ''

    def get_designation_name(self, obj):
        return obj.employee_form.employee.cu_user.designation.cod_name if obj.employee_form.employee.cu_user.designation else ''

    class Meta:
        model = HrmsThreeMonthsProbationReviewForApproval
        fields = ('id','employee_name','emp_code','reporting_head_name','hod_name',
                  'joining_date', 'probation_date','department_name', 'designation_name','how_do_you_like_your_job_as_of_now','is_the_work_allotted_to_you_as_per_your_JD',
                  'what_is_it_that_you_are_working_on','have_you_been_explained_the_work_that_you_need_to_do',
                  'have_you_been_able_to_understand_the_teams_responsibilities',
                  'have_you_been_given_enough_knowledge_on_your_job_profile',
                  'do_you_think_you_are_able_to_fit_in_with_the_JD','have_you_been_made_aware_of_your_targets_KRAs',
                  'would_you_want_hr_to_address_any_issue',
                  'have_you_shared_the_goals_of_the_team_and_organisaton',
                  'do_you_think_he_or_she_is_a_fine_fitment_to_the_team_and_task','fitment_suggestion',
                  'would_you_call_him_or_her_a_good_hire',
                  'is_he_a_slow_learner','slow_learner_suggestion','are_you_satisfied_with_the_response_on_the_work',
                  'what_would_be_his_chance_of_being_confirmed','would_you_want_hr_to_address_any_issue_with_him_or_her',
                  'submission_pending','submission_pending')
    def update(self, instance, validated_data):
        try:
            with transaction.atomic():
                # print(validated_data.get('how_do_you_like_your_job_as_of_now'))
                instance.have_you_given_him_or_her_the_work_that_needs_to_be_done = validated_data.get('have_you_given_him_or_her_the_work_that_needs_to_be_done') if 'have_you_given_him_or_her_the_work_that_needs_to_be_done' in validated_data else 'No'
                instance.have_you_shared_the_goals_of_the_team_and_organisaton = validated_data.get('have_you_shared_the_goals_of_the_team_and_organisaton') if 'have_you_shared_the_goals_of_the_team_and_organisaton' in validated_data else 'No'
                instance.do_you_think_he_or_she_is_a_fine_fitment_to_the_team_and_task = validated_data.get('do_you_think_he_or_she_is_a_fine_fitment_to_the_team_and_task') if 'do_you_think_he_or_she_is_a_fine_fitment_to_the_team_and_task' in validated_data else 'No'
                instance.fitment_suggestion = validated_data.get('fitment_suggestion') if 'fitment_suggestion' in validated_data else None
                instance.would_you_call_him_or_her_a_good_hire = validated_data.get('would_you_call_him_or_her_a_good_hire') if 'would_you_call_him_or_her_a_good_hire' in validated_data else 'No'
                instance.is_he_a_slow_learner = validated_data.get('is_he_a_slow_learner') if 'is_he_a_slow_learner' in validated_data else 'No'
                instance.slow_learner_suggestion = validated_data.get('slow_learner_suggestion') if 'slow_learner_suggestion' in validated_data else None
                instance.are_you_satisfied_with_the_response_on_the_work = validated_data.get('are_you_satisfied_with_the_response_on_the_work') if 'are_you_satisfied_with_the_response_on_the_work' in validated_data else 'No'
                instance.what_would_be_his_chance_of_being_confirmed = validated_data.get('what_would_be_his_chance_of_being_confirmed') if 'what_would_be_his_chance_of_being_confirmed' in validated_data else None
                instance.would_you_want_hr_to_address_any_issue_with_him_or_her = validated_data.get(
                    'would_you_want_hr_to_address_any_issue_with_him_or_her') if 'would_you_want_hr_to_address_any_issue_with_him_or_her' in validated_data else None
                instance.review_submission_date = datetime.datetime.now()
                instance.submission_pending = False
                instance.save()

                return instance
        except Exception as e:
            raise e

# five month probation add serializer
class PendingFiveMonthsProbationAddSerializer(serializers.ModelSerializer):
    # employee = serializers.CharField(default=serializers.CurrentUserDefault())
    employee_name = serializers.SerializerMethodField(required=False)
    emp_code = serializers.SerializerMethodField(required=False)
    reporting_head_name = serializers.SerializerMethodField(required=False)
    hod_name = serializers.SerializerMethodField(required=False)
    joining_date = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()
    designation_name = serializers.SerializerMethodField()
    probation_date = serializers.SerializerMethodField()
    work_assignments = serializers.ListField(required=False)
    achievements = serializers.ListField(required=False)
    probation_work_assignments = serializers.SerializerMethodField(required=False)
    probation_achievements = serializers.SerializerMethodField(required=False)
    location = serializers.SerializerMethodField(required=False)

    def get_employee_name(self, obj):
        return obj.employee.get_full_name() if obj.employee else ''

    def get_emp_code(self, obj):
        return obj.employee.cu_user.cu_emp_code if obj.employee.cu_user.cu_emp_code else ''

    def get_reporting_head_name(self, obj):
        return obj.employee.cu_user.reporting_head.get_full_name() if obj.employee.cu_user.reporting_head else ''

    def get_hod_name(self, obj):
        return obj.employee.cu_user.hod.get_full_name() if obj.employee.cu_user.hod else ''

    def get_joining_date(self, obj):
        return obj.employee.cu_user.joining_date if obj.employee.cu_user.joining_date else ''

    def get_probation_date(self,obj):
        return obj.created_at if obj.created_at else ''

    def get_department_name(self, obj):
        return obj.employee.cu_user.department.cd_name if obj.employee.cu_user.department else ''

    def get_designation_name(self, obj):
        return obj.employee.cu_user.designation.cod_name if obj.employee.cu_user.designation else ''

    def get_location(self, obj):
        return obj.employee.cu_user.job_location if obj.employee.cu_user.job_location else ''

    def get_work_assignments(self, obj):
        assignment_obj = FiveMonthProbationWorkAssignments.objects.filter(probation=obj.id).\
            values_list('assignment_no','assignment_description')
        print(assignment_obj)
        if assignment_obj:
            return list(assignment_obj)
        else:
            return list()

    def get_achievements(self, obj):
        achievements_obj = FiveMonthProbationAchievements.objects.filter(probation=obj.id).\
            values_list('achievements_no','achievements_description')
        if achievements_obj:
            return list(achievements_obj)
        else:
            return list()

    def get_probation_work_assignments(self, obj):
        assignment_obj = FiveMonthProbationWorkAssignments.objects.filter(probation=obj.id).\
            values('assignment_no','assignment_description')
        print(assignment_obj)
        if assignment_obj:
            return list(assignment_obj)
        else:
            return list()

    def get_probation_achievements(self, obj):
        achievements_obj = FiveMonthProbationAchievements.objects.filter(probation=obj.id).\
            values('achievements_no','achievements_description')
        if achievements_obj:
            return list(achievements_obj)
        else:
            return list()

    class Meta:
        model = HrmsFiveMonthsProbationReviewForm
        fields = ('id','employee_name','emp_code','reporting_head_name','hod_name',
                  'joining_date', 'probation_date','department_name', 'designation_name','location',
                  'indicate_any_factor_that_restricted_your_performance',
                  'any_trainings_that_provide_to_improve_your_performance','work_assignments','achievements',
                  'submission_pending','probation_achievements','probation_work_assignments')
        # extra_fields = ('work_assignments','achievements')

    def update(self, instance, validated_data):
        try:
            with transaction.atomic():
                instance.indicate_any_factor_that_restricted_your_performance = validated_data.get('indicate_any_factor_that_restricted_your_performance') if 'indicate_any_factor_that_restricted_your_performance' in validated_data else ''
                instance.any_trainings_that_provide_to_improve_your_performance = validated_data.get('any_trainings_that_provide_to_improve_your_performance') if 'any_trainings_that_provide_to_improve_your_performance' in validated_data else ''
                work_assignments = validated_data.get('work_assignments') if 'work_assignments' in validated_data else None
                achievements = validated_data.get('achievements') if 'achievements' in validated_data else None
                print(work_assignments, achievements)
                if work_assignments:
                    # work_obj = json.loads(work_assignments)
                    for each in work_assignments:
                        obj,create_status = FiveMonthProbationWorkAssignments.objects.get_or_create(probation=instance,
                                                                                                    assignment_no=each['assignment_no'],
                                                                                                    assignment_description=each['assignment_description'])
                        # print(obj)
                if achievements:
                    # achievements_obj = json.loads(work_assignments)
                    for each in achievements:
                        obj, create_status = FiveMonthProbationAchievements.objects.get_or_create(probation=instance,
                                                                                                  achievements_no=each['achievements_no'],
                                                                                                  achievements_description=each['achievements_description'])

                        # print(obj)
                instance.submission_pending = False
                instance.owned_by = instance.employee
                instance.updated_by = instance.employee
                instance.save()
                ins,data=HrmsFiveMonthsProbationReviewForApproval.objects.get_or_create(employee_form=instance)
                import base64
                obj = HrmsFiveMonthsProbationReviewForApproval.objects.latest('id')
                sample_string = str(obj.id)
                sample_string_bytes = sample_string.encode("ascii")
                base64_bytes = base64.b64encode(sample_string_bytes)
                base64_id = base64_bytes.decode("ascii")
                print(base64_id)
                user_email = instance.employee.cu_user.reporting_head.cu_user.cu_alt_email_id
                second_name = instance.employee.cu_user.reporting_head.last_name
                employee_name = instance.employee.get_full_name()
                designation = instance.employee.cu_user.designation.cod_name
                print(user_email)
                print(second_name)
                print(designation, employee_name)
                server_url = settings.SERVER_URL
                server_url = server_url.split(':' + server_url.split(':')[-1])[0]
                if user_email:
                    mail_data = {
                        "employee_name": employee_name,
                        "designation": designation,
                        "second_name": second_name,
                        "link": "http://3.7.231.128/hrms" + "/#/final-review/" + base64_id,
                    }
                    from global_function import send_mail
                    sub = str(employee_name) + ',' + str(designation)
                    send_mail('HRMS-5P-RH-1R', user_email, mail_data, final_sub=sub)
                    date = datetime.datetime.now()
                    HrmsFiveMonthsProbationReviewForApproval.objects.filter(id=obj.id).update(reminder_state=0,
                                                                                               reminder_date=date,
                                                                                               first_reminder_date=date)

                return instance
        except Exception as e:
            raise e


# five month probation review add serializer
class PendingFiveMonthsProbationReviewAddSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField(required=False)
    emp_code = serializers.SerializerMethodField(required=False)
    reporting_head_name = serializers.SerializerMethodField(required=False)
    hod_name = serializers.SerializerMethodField(required=False)
    joining_date = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()
    designation_name = serializers.SerializerMethodField()
    probation_date = serializers.SerializerMethodField()
    work_assignments = serializers.SerializerMethodField(required=False)
    achievements = serializers.SerializerMethodField(required=False)
    indicate_any_factor_that_restricted_your_performance = serializers.SerializerMethodField(required=False)
    any_trainings_that_provide_to_improve_your_performance = serializers.SerializerMethodField(required=False)
    location = serializers.SerializerMethodField(required=False)

    def get_employee_name(self, obj):
        return obj.employee_form.employee.get_full_name() if obj.employee_form.employee else ''

    def get_emp_code(self, obj):
        return obj.employee_form.employee.cu_user.cu_emp_code if obj.employee_form.employee.cu_user.cu_emp_code else ''

    def get_reporting_head_name(self, obj):
        return obj.employee_form.employee.cu_user.reporting_head.get_full_name() if obj.employee_form.employee.cu_user.reporting_head else ''

    def get_hod_name(self, obj):
        return obj.employee_form.employee.cu_user.hod.get_full_name() if obj.employee_form.employee.cu_user.hod else ''

    def get_joining_date(self, obj):
        return obj.employee_form.employee.cu_user.joining_date if obj.employee_form.employee.cu_user.joining_date else ''

    def get_probation_date(self,obj):
        return obj.employee_form.employee.cu_user.joining_date + relativedelta(months=+5)if obj.employee_form.employee.cu_user.joining_date else ''

    def get_department_name(self, obj):
        return obj.employee_form.employee.cu_user.department.cd_name if obj.employee_form.employee.cu_user.department else ''

    def get_designation_name(self, obj):
        return obj.employee_form.employee.cu_user.designation.cod_name if obj.employee_form.employee.cu_user.designation else ''

    def get_location(self, obj):
        return obj.employee_form.employee.cu_user.job_location if obj.employee_form.employee.cu_user.job_location else ''

    def get_work_assignments(self, obj):
        assignment_obj = FiveMonthProbationWorkAssignments.objects.filter(probation=obj.employee_form).\
            values('assignment_no','assignment_description')
        print(assignment_obj)
        if assignment_obj:
            return list(assignment_obj)
        else:
            return list()

    def get_achievements(self, obj):
        achievements_obj = FiveMonthProbationAchievements.objects.filter(probation=obj.employee_form).\
            values('achievements_no','achievements_description')
        if achievements_obj:
            return list(achievements_obj)
        else:
            return list()

    def get_indicate_any_factor_that_restricted_your_performance(self, obj):
        if obj.employee_form.indicate_any_factor_that_restricted_your_performance:
            return obj.employee_form.indicate_any_factor_that_restricted_your_performance
        else:
            return None

    def get_any_trainings_that_provide_to_improve_your_performance(self, obj):
        if obj.employee_form.any_trainings_that_provide_to_improve_your_performance:
            return obj.employee_form.any_trainings_that_provide_to_improve_your_performance
        else:
            return None


    class Meta:
        model = HrmsFiveMonthsProbationReviewForApproval
        fields = ('id', 'employee_name', 'emp_code', 'reporting_head_name','hod_name',
                  'joining_date', 'probation_date', 'department_name', 'designation_name','location',
                  'indicate_any_factor_that_restricted_your_performance',
                  'any_trainings_that_provide_to_improve_your_performance',
                  'quality_of_work','team_fitment','fitment_suggestion','good_hire_status','progress_appropriate_status',
                  'satisfied_with_the_response','task_given_are_completed_on_time','relations_with_supervisor',
                  'cooperation_with_colleagues', 'fitment_in_your_team',
                  'willingness_to_take_up_assignments_or_jobs', 'competency_in_the_role',
                  'trainings_recommended', 'recommended_training', 'to_be_confirmed','submission_pending','work_assignments','achievements')
        # extra_fields = ('work_assignments','achievements')

    def update(self, instance, validated_data):
        try:
            with transaction.atomic():
                instance.quality_of_work = validated_data.get('quality_of_work') if 'quality_of_work' in validated_data else ''
                instance.relations_with_supervisor = validated_data.get('relations_with_supervisor') if 'relations_with_supervisor' in validated_data else ''
                instance.cooperation_with_colleagues = validated_data.get('cooperation_with_colleagues') if 'cooperation_with_colleagues' in validated_data else ''
                instance.fitment_in_your_team = validated_data.get('fitment_in_your_team') if 'fitment_in_your_team' in validated_data else ''
                instance.willingness_to_take_up_assignments_or_jobs = validated_data.get('willingness_to_take_up_assignments_or_jobs') if 'willingness_to_take_up_assignments_or_jobs' in validated_data else ''
                instance.competency_in_the_role = validated_data.get('competency_in_the_role') if 'competency_in_the_role' in validated_data else ''
                instance.trainings_recommended = validated_data.get('trainings_recommended') if 'trainings_recommended' in validated_data else ''
                instance.recommended_training = validated_data.get('recommended_training') if 'recommended_training' in validated_data else ''
                instance.to_be_confirmed = validated_data.get('to_be_confirmed') if 'to_be_confirmed' in validated_data else ''
                instance.team_fitment = validated_data.get(
                    'team_fitment') if 'team_fitment' in validated_data else 'No'
                instance.fitment_suggestion = validated_data.get(
                    'fitment_suggestion') if 'fitment_suggestion' in validated_data else ''
                instance.good_hire_status = validated_data.get(
                    'good_hire_status') if 'good_hire_status' in validated_data else 'No'
                instance.progress_appropriate_status = validated_data.get(
                    'progress_appropriate_status') if 'progress_appropriate_status' in validated_data else 'No'
                instance.satisfied_with_the_response = validated_data.get(
                    'satisfied_with_the_response') if 'satisfied_with_the_response' in validated_data else 'No'
                instance.task_given_are_completed_on_time = validated_data.get(
                    'task_given_are_completed_on_time') if 'task_given_are_completed_on_time' in validated_data else 'No'
                instance.submission_pending = False
                instance.review_submission_date = datetime.datetime.now()
                instance.owned_by = instance.employee_form.employee
                instance.updated_by = instance.employee_form.employee
                instance.save()
                # ins,data=HrmsThreeMonthsProbationReviewForApproval.objects.get_or_create(employee_form=instance)

                return instance
        except Exception as e:
            raise e


# five months pending probation listing
class PendingFiveMonthsProbationEmployeeListSerializer(serializers.ModelSerializer):
    employee_id = serializers.SerializerMethodField()
    employee_name = serializers.SerializerMethodField()
    emp_code = serializers.SerializerMethodField()
    emp_email_id = serializers.SerializerMethodField()
    email_body = serializers.SerializerMethodField()
    email_subject = serializers.SerializerMethodField()
    reporting_head_name = serializers.SerializerMethodField()
    hod_name = serializers.SerializerMethodField()
    joining_date = serializers.SerializerMethodField()
    sap_personnel_no = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()
    designation_name = serializers.SerializerMethodField()
    official_email_id = serializers.SerializerMethodField()
    company = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    reporting_head_email = serializers.SerializerMethodField()
    reporting_head_id = serializers.SerializerMethodField()
    company_id = serializers.SerializerMethodField()
    probation_date = serializers.SerializerMethodField()
    mail_shoot_date = serializers.SerializerMethodField()


    def get_employee_id(self, obj):
        return obj.id if obj.id else ''

    def get_company(self, obj):
        return obj.company.coc_name if obj.company.coc_name else ''

    def get_company_id(self, obj):
        return obj.company.id if obj.company else ''

    def get_location(self, obj):
        return obj.job_location if obj.job_location else ''

    def get_email_body(self, obj):
        mail_body = '''<table border="0" cellpadding="0" cellspacing="0" width="100%" style="border: 1px solid #cecece; padding: 10px;">
	<tr>
		<td colspan="2">
			<p style="padding-bottom:5px;">Dear  Ms./Mr/Mrs {},</p>
			<p style="padding-bottom:10px;">We haven’t received your 5 Months Probation review form yet. Request you to visit the link below
and fill up the form at the earliest.</p>
		</td>
	</tr>
	<tr>
		<td>
			<a href={{link}}>Link to the form</a>
		</td>
	</tr>
	<tr>
		<td colspan="2" align="left" style="padding-top:10px;">
			<p>Regards,
				<br>
					<b> HR Team</b>
				</p>
			</td>
		</tr>
	</table>'''.format(obj.cu_user.last_name)
        return mail_body
    def get_email_subject(self, obj):
        mail_sub = " Probation Review Form"
        return mail_sub

    def get_employee_name(self, obj):
        return obj.cu_user.get_full_name() if obj.cu_user else ''

    def get_emp_code(self, obj):
        return obj.cu_emp_code if obj.cu_emp_code else ''

    def get_emp_email_id(self, obj):
        return obj.cu_alt_email_id if obj else ''

    def get_reporting_head_name(self, obj):
        return obj.reporting_head.get_full_name() if obj.reporting_head else ''

    def get_hod_name(self, obj):
        return obj.hod.get_full_name() if obj.hod else ''

    def get_joining_date(self, obj):
        return obj.joining_date if obj.joining_date else ''

    def get_sap_personnel_no(self, obj):
        return obj.sap_personnel_no if obj.sap_personnel_no else ''


    def get_department_name(self, obj):
        return obj.department.cd_name if obj.department else ''

    def get_designation_name(self,obj):

        return obj.designation.cod_name if obj.designation else ''


    def get_official_email_id(self,obj):

        return obj.cu_alt_email_id if obj.cu_alt_email_id else ''

    def get_reporting_head_email(self,obj):
        return obj.reporting_head.cu_user.cu_alt_email_id if obj.reporting_head.cu_user.cu_alt_email_id else ''

    def get_reporting_head_id(self,obj):
        return obj.reporting_head.cu_user.id if obj.reporting_head.cu_user else ''

    def get_probation_date(self,obj):
        probation_review_obj = HrmsFiveMonthsProbationReviewForm.objects.filter(employee=obj.cu_user)[0]
        # print(probation_review_obj.created_at)
        if probation_review_obj.created_at:
            return probation_review_obj.created_at
        else:
            return None

    def get_mail_shoot_date(self,obj):
        probation_review_obj = HrmsFiveMonthsProbationReviewForm.objects.filter(employee=obj.cu_user)[0]
        # print(probation_review_obj.created_at)
        if probation_review_obj.created_at:
            return probation_review_obj.created_at
        else:
            return None


    class Meta:
        model = TCoreUserDetail
        fields = ('employee_id','employee_name','reporting_head', 'reporting_head_name','hod','hod_name', 'joining_date','emp_code','emp_email_id',
                'sap_personnel_no', 'email_body','email_subject', 'department_name', 'department','designation_name','designation','official_email_id','company', 'company_id','location',
                  'reporting_head_email','reporting_head_id', 'probation_date','mail_shoot_date'
                )


class PendingFiveMonthsProbationReportingHeadListSerializer(serializers.ModelSerializer):
    employee_id = serializers.SerializerMethodField()
    employee_name = serializers.SerializerMethodField()
    emp_code = serializers.SerializerMethodField()
    emp_email_id = serializers.SerializerMethodField()
    email_body = serializers.SerializerMethodField()
    email_subject = serializers.SerializerMethodField()
    reporting_head_name = serializers.SerializerMethodField()
    hod_name = serializers.SerializerMethodField()
    joining_date = serializers.SerializerMethodField()
    sap_personnel_no = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()
    designation_name = serializers.SerializerMethodField()
    official_email_id = serializers.SerializerMethodField()
    company = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    reporting_head_email = serializers.SerializerMethodField()
    reporting_head_id = serializers.SerializerMethodField()
    company_id = serializers.SerializerMethodField()
    probation_date = serializers.SerializerMethodField()
    mail_shoot_date = serializers.SerializerMethodField()


    def get_employee_id(self, obj):
        return obj.id if obj.id else ''

    def get_company(self, obj):
        return obj.company.coc_name if obj.company.coc_name else ''

    def get_company_id(self, obj):
        return obj.company.id if obj.company else ''

    def get_location(self, obj):
        return obj.job_location if obj.job_location else ''

    def get_email_body(self, obj):
        mail_body = '''<table border="0" cellpadding="0" cellspacing="0" width="100%" style="border: 1px solid #cecece; padding: 10px;"> <tr> <td colspan="2"> <p style="padding-bottom:5px;">Dear  Ms./Mr/Mrs {},</p> <p style="padding-bottom:10px;">We haven’t received the 5th Month Probation review form for {}, {} yet.Request you to visit the link below and fill up the form at the earliest.</p> </td> </tr><tr><td><a href={{link}}>Link to the form</a></td></tr><tr> <td colspan="2" align="left" style="padding-top:10px;"><p>Regards,<br><b> HR Team</b></p></td> </tr> </table>'''.format(obj.cu_user.last_name,obj.cu_user.get_full_name(),obj.designation.cod_name)
        return mail_body
    def get_email_subject(self, obj):
        mail_sub = "Probation Review Form: {}, {}".format(obj.cu_user.get_full_name(),obj.designation.cod_name)
        return mail_sub

    def get_employee_name(self, obj):
        return obj.cu_user.get_full_name() if obj.cu_user else ''

    def get_emp_code(self, obj):
        return obj.cu_emp_code if obj.cu_emp_code else ''

    def get_emp_email_id(self, obj):
        return obj.cu_alt_email_id if obj else ''

    def get_reporting_head_name(self, obj):
        return obj.reporting_head.get_full_name() if obj.reporting_head else ''

    def get_hod_name(self, obj):
        return obj.hod.get_full_name() if obj.hod else ''

    def get_joining_date(self, obj):
        return obj.joining_date if obj.joining_date else ''

    def get_sap_personnel_no(self, obj):
        return obj.sap_personnel_no if obj.sap_personnel_no else ''


    def get_department_name(self, obj):
        return obj.department.cd_name if obj.department else ''

    def get_designation_name(self,obj):

        return obj.designation.cod_name if obj.designation else ''


    def get_official_email_id(self,obj):

        return obj.cu_alt_email_id if obj.cu_alt_email_id else ''

    def get_reporting_head_email(self,obj):
        return obj.reporting_head.cu_user.cu_alt_email_id if obj.reporting_head.cu_user.cu_alt_email_id else ''

    def get_reporting_head_id(self,obj):
        return obj.reporting_head.cu_user.id if obj.reporting_head.cu_user else ''

    def get_probation_date(self,obj):
        probation_review_obj = HrmsFiveMonthsProbationReviewForm.objects.filter(employee=obj.cu_user)[0]
        # print(probation_review_obj.created_at)
        if probation_review_obj.created_at:
            return probation_review_obj.created_at
        else:
            return None

    def get_mail_shoot_date(self,obj):
        probation_review_obj = HrmsFiveMonthsProbationReviewForm.objects.filter(employee=obj.cu_user)[0]
        # print(probation_review_obj.created_at)
        if probation_review_obj.created_at:
            return probation_review_obj.created_at
        else:
            return None


    class Meta:
        model = TCoreUserDetail
        fields = ('employee_id','employee_name','reporting_head', 'reporting_head_name','hod','hod_name', 'joining_date','emp_code','emp_email_id',
                'sap_personnel_no', 'email_body','email_subject', 'department_name', 'department','designation_name','designation','official_email_id','company', 'company_id','location',
                  'reporting_head_email','reporting_head_id', 'probation_date','mail_shoot_date'
                )


class CompletedThreeMonthProbationReportSerializer(serializers.ModelSerializer):
    employee_id = serializers.SerializerMethodField()
    employee_name = serializers.SerializerMethodField()
    emp_code = serializers.SerializerMethodField()
    reporting_head_name = serializers.SerializerMethodField()
    hod_name = serializers.SerializerMethodField()
    joining_date = serializers.SerializerMethodField()
    sap_personnel_no = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()
    designation_name = serializers.SerializerMethodField()
    official_email_id = serializers.SerializerMethodField()
    company = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    reporting_head_email = serializers.SerializerMethodField()
    company_id = serializers.SerializerMethodField()
    probation_date = serializers.SerializerMethodField()
    mail_shoot_date = serializers.SerializerMethodField()
    completion_3rd_month_date = serializers.SerializerMethodField()

    def get_employee_id(self, obj):
        return obj.id if obj.id else ''
    def get_company(self, obj):
        return obj.company.coc_name if obj.company.coc_name else ''
    def get_company_id(self, obj):
        return obj.company.id if obj.company else ''
    def get_location(self, obj):
        return obj.job_location if obj.job_location else ''
    def get_employee_name(self, obj):
        return obj.cu_user.get_full_name() if obj.cu_user else ''
    def get_emp_code(self, obj):
        return obj.cu_emp_code if obj.cu_emp_code else ''
    def get_reporting_head_name(self, obj):
        return obj.reporting_head.get_full_name() if obj.reporting_head else ''
    def get_hod_name(self, obj):
        return obj.hod.get_full_name() if obj.hod else ''
    def get_joining_date(self, obj):
        return obj.joining_date if obj.joining_date else ''
    def get_sap_personnel_no(self, obj):
        return obj.sap_personnel_no if obj.sap_personnel_no else ''
    def get_department_name(self, obj):
        return  obj.department.cd_name if obj.department else ''
    def get_designation_name(self,obj):
        return obj.designation.cod_name if obj.designation else ''
    def get_official_email_id(self,obj):
        return obj.cu_alt_email_id if obj.cu_alt_email_id else ''
    def get_reporting_head_email(self,obj):
        return obj.reporting_head.cu_user.cu_alt_email_id if obj.reporting_head.cu_user.cu_alt_email_id else ''
    def get_probation_date(self,obj):
        if obj.joining_date:
            # print(probation_review_obj)
            return obj.joining_date + relativedelta(months=+3)
        else:
            return None
    def get_mail_shoot_date(self,obj):
        probation_review_obj = HrmsThreeMonthsProbationReviewForm.objects.filter(employee=obj.cu_user)[0]
        if probation_review_obj.created_at:
            # print(probation_review_obj)
            return probation_review_obj.created_at
        else:
            return None
    def get_completion_3rd_month_date(self,obj):
        prob_obj= HrmsThreeMonthsProbationReviewForApproval.objects.filter(employee_form__employee__cu_user__id=obj.id)
        if prob_obj:
            return prob_obj[0].review_submission_date
        else:
            return None

    class Meta:
        model = TCoreUserDetail
        fields = ('employee_id','employee_name','reporting_head' ,'reporting_head_name','hod','hod_name', 'joining_date','emp_code',
                'sap_personnel_no', 'department_name', 'department','designation_name','designation','official_email_id','company', 'company_id','location',
                  'reporting_head_email','probation_date','mail_shoot_date','completion_3rd_month_date'
                )

# five months pending probation listing
class CompletedThreeMonthProbationReportSerializer(serializers.ModelSerializer):
    employee_id = serializers.SerializerMethodField()
    employee_name = serializers.SerializerMethodField()
    emp_code = serializers.SerializerMethodField()
    reporting_head_name = serializers.SerializerMethodField()
    hod_name = serializers.SerializerMethodField()
    joining_date = serializers.SerializerMethodField()
    sap_personnel_no = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()
    designation_name = serializers.SerializerMethodField()
    official_email_id = serializers.SerializerMethodField()
    company = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    reporting_head_email = serializers.SerializerMethodField()
    company_id = serializers.SerializerMethodField()
    probation_date = serializers.SerializerMethodField()
    mail_shoot_date = serializers.SerializerMethodField()
    completion_3rd_month_review_date = serializers.SerializerMethodField()
    completion_5th_month_review_date = serializers.SerializerMethodField()


    def get_employee_id(self, obj):
        return obj.id if obj.id else ''

    def get_company(self, obj):
        return obj.company.coc_name if obj.company.coc_name else ''

    def get_company_id(self, obj):
        return obj.company.id if obj.company else ''

    def get_location(self, obj):
        return obj.job_location if obj.job_location else ''

    def get_employee_name(self, obj):
        return obj.cu_user.get_full_name() if obj.cu_user else ''

    def get_emp_code(self, obj):
        return obj.cu_emp_code if obj.cu_emp_code else ''

    def get_reporting_head_name(self, obj):
        return obj.reporting_head.get_full_name() if obj.reporting_head else ''

    def get_hod_name(self, obj):
        return obj.hod.get_full_name() if obj.hod else ''

    def get_joining_date(self, obj):
        return obj.joining_date if obj.joining_date else ''

    def get_sap_personnel_no(self, obj):
        return obj.sap_personnel_no if obj.sap_personnel_no else ''


    def get_department_name(self, obj):
        return obj.department.cd_name if obj.department else ''

    def get_designation_name(self,obj):

        return obj.designation.cod_name if obj.designation else ''


    def get_official_email_id(self,obj):

        return obj.cu_alt_email_id if obj.cu_alt_email_id else ''

    def get_reporting_head_email(self,obj):
        return obj.reporting_head.cu_user.cu_alt_email_id if obj.reporting_head.cu_user.cu_alt_email_id else ''

    def get_probation_date(self,obj):
        if obj.joining_date:
            return obj.joining_date + relativedelta(months=+5)
        else:
            return None

    def get_mail_shoot_date(self,obj):
        probation_review_obj = HrmsFiveMonthsProbationReviewForm.objects.filter(employee=obj.cu_user)[0]
        # print(probation_review_obj.created_at)
        if probation_review_obj.created_at:
            return probation_review_obj.created_at
        else:
            return None
    def get_completion_5th_month_review_date(self,obj):
        prob_obj= HrmsFiveMonthsProbationReviewForApproval.objects.filter(employee_form__employee__cu_user__id=obj.id)
        if prob_obj:
            return prob_obj[0].review_submission_date
        else:
            return None

    def get_completion_3rd_month_review_date(self,obj):
        prob_obj = HrmsThreeMonthsProbationReviewForApproval.objects.filter(employee_form__employee__cu_user__id=obj.id)
        if prob_obj:
            return prob_obj[0].review_submission_date
        else:
            return None

    class Meta:
        model = TCoreUserDetail
        fields = ('employee_id','employee_name','reporting_head' ,'reporting_head_name','hod','hod_name', 'joining_date','emp_code',
                'sap_personnel_no', 'department_name', 'department','designation_name','designation','official_email_id','company', 'company_id','location',
                  'reporting_head_email','probation_date','mail_shoot_date','completion_5th_month_review_date','completion_3rd_month_review_date'
                )



class ConfirmEmployeeSerializer(serializers.ModelSerializer):
    is_confirm = serializers.BooleanField(required=False,default=False)
    class Meta:
        model = TCoreUserDetail
        fields = '__all__'
    def update(self, instance, validated_data):
        is_confirm = validated_data.get('is_confirm')
        if is_confirm:
            instance.is_confirm = True
            instance.confirmation_date = datetime.datetime.now()
            instance.save()
            user_email = instance.cu_alt_email_id
            second_name = instance.cu_user.last_name
            # employee_name = instance.employee.get_full_name()
            # designation = instance.employee.cu_user.designation.cod_name
            # print(user_email)
            # print(second_name)
            # print(designation, employee_name)
            if user_email:
                mail_data = {
                    "second_name": second_name,
                }
                from global_function import send_mail
                send_mail('HRMS-5p-C', user_email, mail_data)
            return instance
        else:
            return instance


class RejoinEmployeeSuggestionListSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField(required=False)
    user_id = serializers.SerializerMethodField(required=False)
    def get_full_name(self,obj):
        if obj.cu_user:
            return obj.cu_user.get_full_name()
        else:
            return None
    def get_user_id(self,obj):
        if obj.id:
            return obj.id
        else:
            return None

    class Meta:
        model = TCoreUserDetail
        fields = ('user_id','sap_personnel_no','full_name','cu_emp_code')


class EmployeeRejoinAddSerializer(serializers.ModelSerializer):
    first_name = serializers.SerializerMethodField(required=False)
    last_name = serializers.SerializerMethodField(required=False)
    reporting_head_name = serializers.SerializerMethodField(required=False)
    hod_name = serializers.SerializerMethodField(required=False)
    designation_name = serializers.SerializerMethodField(required=False)
    department_name = serializers.SerializerMethodField(required=False)
    company_name = serializers.SerializerMethodField(required=False)
    grade_name = serializers.SerializerMethodField(required=False)
    sub_grade_name = serializers.SerializerMethodField(required=False)
    cost_centre = serializers.SerializerMethodField(required=False)

    def get_first_name(self,obj):
        if obj.cu_user.first_name:
            return obj.cu_user.first_name
        else:
            return None
    def get_cost_centre(self,obj):
        if obj.updated_cost_centre:
            return obj.updated_cost_centre.id
        else:
            return None

    def get_last_name(self,obj):
        if obj.cu_user.last_name:
            return obj.cu_user.last_name
        else:
            return None

    def get_reporting_head_name(self, obj):
        return obj.reporting_head.get_full_name() if obj.reporting_head else ''

    def get_hod_name(self, obj):

        return obj.hod.get_full_name() if obj.hod else ''
    def get_department_name(self,obj):
        if obj.department:
            return obj.department.cd_name
        else:
            return None

    def get_company_name(self, obj):
        return obj.company.coc_name if obj.company else ''

    def get_designation_name(self,obj):
        if obj.department:
            try:
                des_name = obj.designation.cod_name if obj.designation.cod_name else ''
            except:
                des_name=""
            return des_name
        else:
            return None

    def get_grade_name(self, obj):
        return obj.employee_grade.cg_name if obj.employee_grade else ''
    def get_sub_grade_name(self, obj):
        return obj.employee_sub_grade.name if obj.employee_sub_grade else ''
    class Meta:
        model = TCoreUserDetail
        fields = ['id','cu_user','first_name','last_name','cu_gender','cu_phone_no','cu_alt_phone_no','cu_alt_email_id','cu_punch_id','cu_emp_code',
                  'cu_profile_img','cu_dob','cu_profile_img','cu_dob','sap_personnel_no','initial_ctc','current_ctc',
                  'cost_centre','address','blood_group','total_experience','job_description','password_to_know',
                  'granted_cl','granted_sl','granted_el','joining_date','termination_date','daily_loginTime',
                  'daily_logoutTime','saturday_logout','lunch_start','lunch_end','worst_late','is_flexi_hour',
                  'cu_is_deleted','cu_change_pass','is_saturday_off','cu_created_at','cu_updated_at','cu_deleted_at',
                  'is_confirm','confirmation_date','job_location','source','source_name','bank_account','ifsc_code',
                  'branch_name','pincode','emergency_relationship','emergency_contact_no','emergency_contact_name',
                  'father_name','pan_no','aadhar_no','uan_no','vpf_no','employee_voluntary_provident_fund_contribution',
                  'contributing_towards_pension_scheme','pf_no','provident_trust_fund','pf_trust_code','pf_description',
                  'emp_pension_no','pension_trust_id','has_pf','esic_no','esi_dispensary','esi_sub_type','has_esi',
                  'marital_status','salary_per_month','resignation_date','user_type','launch_hour','is_auto_od',
                  'granted_leaves_cl_sl','bus_facility','highest_qualification','previous_employer','attendance_type',
                  'address_sub_type','care_of','street_and_house_no','address_2nd_line','care_of','street_and_house_no',
                  'country','province','country_key','city','district','file_no','retirement_date','wbs_element',
                  'work_schedule_rule','time_management_status','ptax_sub_type','cu_user','company','company_name','hod','hod_name',
                  'reporting_head', 'reporting_head_name','department','department_name','designation','grade_name',
                  'sub_grade_name','designation_name','salary_type','job_location_state','state','sub_department',
                  'bank_name_p','is_rejoin','rejoin_date','employee_grade','employee_sub_grade'
                  ]





class EmployeeTransferSerializer(serializers.ModelSerializer):
    ##### Extra Fields for TCoreUserDetails #####################
    cu_phone_no =serializers.CharField(required=False,allow_null=True)
    cu_alt_phone_no =serializers.CharField(required=False,allow_null=True)
    cu_alt_email_id=serializers.CharField(required=False,allow_null=True)
    cu_emp_code =serializers.CharField(required=False,allow_null=True)
    cu_punch_id = serializers.CharField(required=False,allow_null=True)
    cu_profile_img=serializers.ImageField(required=False,allow_null=True)
    sap_personnel_no=serializers.CharField(required=False,allow_null=True)
    initial_ctc=serializers.CharField(required=False,allow_null=True)
    current_ctc=serializers.CharField(required=False,allow_null=True)
    cost_centre=serializers.CharField(required=False,allow_null=True)
    address =serializers.CharField(required=False,allow_null=True)
    blood_group=serializers.CharField(required=False,allow_null=True)
    total_experience=serializers.CharField(required=False,allow_null=True)
    job_description =serializers.CharField(required=False,allow_null=True)
    company=serializers.CharField(required=False,allow_null=True)
    granted_cl=serializers.CharField(required=False,allow_null=True)
    granted_sl=serializers.CharField(required=False,allow_null=True)
    granted_el=serializers.CharField(required=False,allow_null=True)
    hod = serializers.CharField(required=False,allow_null=True)
    reporting_head = serializers.CharField(required=False)
    temp_reporting_heads = serializers.CharField(required=False,allow_null=True)
    designation = serializers.CharField(required=False,allow_null=True)
    department = serializers.CharField(required=False,allow_null=True)
    daily_loginTime=serializers.CharField(required=False,allow_null=True)
    daily_logoutTime=serializers.CharField(required=False,allow_null=True)
    lunch_start=serializers.CharField(required=False,allow_null=True)
    lunch_end=serializers.CharField(required=False,allow_null=True)
    saturday_off=serializers.DictField(required=False)
    salary_type= serializers.CharField(required=False,allow_null=True)
    is_confirm =  serializers.BooleanField(required=False)
    termination_date =serializers.CharField(required=False)
    ##### Extra Fields for another tables #####################
    employee_grade = serializers.CharField(required=False,allow_null=True)
    # 'allow_blank' field added by Shubhadeep
    employee_sub_grade = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    mmr_module_id =serializers.CharField(required=False,allow_null=True)
    mmr_type=serializers.CharField(required=False,allow_null=True)
    benefit_provided = serializers.ListField(required=False,allow_null=True)
    other_facilities = serializers.ListField(required=False,allow_null=True)

    '''
        Added by Rupam Hazra [13.02.2020] as per details confirmation
    '''
    job_location = serializers.CharField(required = False, allow_null=True)
    job_location_state = serializers.CharField(required=False,allow_null=True)
    source = serializers.CharField(required = False, allow_null=True)
    source_name = serializers.CharField(required = False, allow_null=True)
    bank_account = serializers.CharField(required = False, allow_null=True)
    ifsc_code = serializers.CharField(required = False, allow_null=True)
    branch_name = serializers.CharField(required = False, allow_null=True)
    pincode = serializers.CharField(required = False, allow_null=True)
    emergency_contact_no = serializers.CharField(required = False,allow_null=True)
    father_name = serializers.CharField(required = False,allow_null=True)
    pan_no = serializers.CharField(required = False,allow_null=True)
    aadhar_no = serializers.CharField(required = False,allow_null=True)
    uan_no = serializers.CharField(required = False,allow_null=True)
    pf_no = serializers.CharField(required = False,allow_null=True)
    esic_no = serializers.CharField(required = False,allow_null=True)
    marital_status = serializers.CharField(required = False,allow_null=True)
    salary_per_month=serializers.CharField(required = False,allow_null=True)
    # updated by Shubhadeep - doc was string before, it must be date
    cu_dob = serializers.DateField(required=False,allow_null=True)
    resignation_date = serializers.CharField(required=False,allow_null=True)
    cu_gender = serializers.CharField(required=False,allow_null=True)
    is_auto_od = serializers.BooleanField(required=False)
    sub_department = serializers.CharField(required=False,allow_null=True)
    attendance_type = serializers.CharField(required=False,allow_null=True)

    wbs_element = serializers.CharField(required=False,allow_null=True)
    retirement_date = serializers.CharField(required=False,allow_null=True)
    esi_dispensary = serializers.CharField(required=False,allow_null=True)
    emp_pension_no = serializers.CharField(required=False,allow_null=True)
    employee_voluntary_provident_fund_contribution = serializers.CharField(required=False,allow_null=True)
    care_of = serializers.CharField(required=False,allow_null=True)
    street_and_house_no = serializers.CharField(required=False,allow_null=True)
    address_2nd_line = serializers.CharField(required=False,allow_null=True)
    city = serializers.CharField(required=False,allow_null=True)
    district = serializers.CharField(required=False,allow_null=True)

    bus_facility = serializers.BooleanField(required=False)
    emergency_relationship = serializers.CharField(required=False,allow_null=True)
    emergency_contact_name = serializers.CharField(required=False,allow_null=True)

    has_pf = serializers.BooleanField(required=False)
    has_esi = serializers.BooleanField(required=False)
    bank_name_p = serializers.CharField(required=False,allow_null=True)

    state = serializers.CharField(required=False,allow_null=True)

    is_flexi_hour = serializers.BooleanField(required=False)
    # is_transfer = serializers.BooleanField(required=False)

    class Meta:
        model = User
        fields=('id','first_name','last_name','email','is_active',
        'employee_grade','department','cu_profile_img','termination_date',
        'reporting_head','temp_reporting_heads','designation','benefit_provided','other_facilities','is_confirm',
        'hod','blood_group','company','granted_cl','granted_sl','granted_el','salary_type',
        'job_description','total_experience','address','cost_centre','saturday_off','cu_punch_id',
        'current_ctc','initial_ctc','sap_personnel_no','cu_emp_code','cu_alt_email_id','cu_alt_phone_no',
        'cu_phone_no','mmr_module_id',"mmr_type",'daily_loginTime','daily_logoutTime','lunch_start','lunch_end',
        'cu_dob','job_location','job_location_state','source','source_name','bank_account','ifsc_code','branch_name',
        'pincode','emergency_contact_no','father_name','pan_no','aadhar_no','uan_no','pf_no','esic_no',
        'marital_status','salary_per_month','resignation_date','cu_gender','is_auto_od','sub_department','attendance_type',
        'wbs_element', 'retirement_date', 'esi_dispensary', 'emp_pension_no',
        'employee_voluntary_provident_fund_contribution', 'care_of', 'street_and_house_no',
        'address_2nd_line', 'city', 'district','bus_facility','emergency_relationship',
        'emergency_contact_name','has_pf','has_esi','bank_name_p','state','is_flexi_hour','employee_sub_grade')




    def update(self,instance,validated_data):
        try:
            #print('validated_data',validated_data)
            list_type = self.context['request'].query_params.get('list_type', None)
            logdin_user_id = self.context['request'].user.id
            # is_transfer = validated_data.get('is_transfer') if validated_data.get('is_transfer') else ""
            blood_group=validated_data.get('blood_group') if validated_data.get('blood_group') else ""
            total_experience=validated_data.get('total_experience') if validated_data.get('total_experience') else ""
            address=validated_data.get('address') if validated_data.get('address') else ""
            cu_profile_img=validated_data.get('cu_profile_img') if validated_data.get('cu_profile_img') else ""
            cu_alt_phone_no=validated_data.get('cu_alt_phone_no') if validated_data.get('cu_alt_phone_no') else ""
            cu_alt_email_id= validated_data.get('cu_alt_email_id') if  validated_data.get('cu_alt_email_id') else ""
            cu_emp_code=validated_data.get('cu_emp_code') if validated_data.get('cu_emp_code') else ""
            cu_punch_id = validated_data.get('cu_punch_id') if validated_data.get('cu_punch_id') else ""
            job_description=validated_data.get('job_description') if validated_data.get('job_description') else ""
            cu_phone_no=validated_data.get('cu_phone_no') if validated_data.get('cu_phone_no') else ""
            company=validated_data.get('company') if validated_data.get('company') else ""
            hod=validated_data.get('hod') if validated_data.get('hod') else ""
            reporting_head=validated_data.get('reporting_head') if validated_data.get('reporting_head') else ""
            temp_reporting_heads=validated_data.get('temp_reporting_heads') if validated_data.get('temp_reporting_heads') else None
            department=validated_data.get('department') if validated_data.get('department') else ""
            designation=validated_data.get('designation') if validated_data.get('designation') else ""
            current_ctc=validated_data.get('current_ctc') if validated_data.get('current_ctc') else ""
            initial_ctc=validated_data.get('initial_ctc') if validated_data.get('initial_ctc') else ""
            sap_personnel_no= None if validated_data.get('sap_personnel_no') == 'null' else validated_data.get('sap_personnel_no')
            cost_centre=validated_data.get('cost_centre') if validated_data.get('cost_centre') else ""
            granted_cl=validated_data.get('granted_cl') if validated_data.get('granted_cl') else 0.0
            granted_el=validated_data.get('granted_el') if validated_data.get('granted_el') else 0.0
            granted_sl=validated_data.get('granted_sl') if validated_data.get('granted_sl') else 0.0
            daily_loginTime=validated_data.get('daily_loginTime') if validated_data.get('daily_loginTime') else None
            daily_logoutTime=validated_data.get('daily_logoutTime') if validated_data.get('daily_logoutTime') else None
            lunch_start=validated_data.get('lunch_start') if validated_data.get('lunch_start') else None
            lunch_end=validated_data.get('lunch_end') if validated_data.get('lunch_end') else None
            saturday_off=validated_data.get('saturday_off') if validated_data.get('saturday_off') else None
            salary_type = int(validated_data.get('salary_type')) if validated_data.get('salary_type') else None
            attendance_type = validated_data.get('attendance_type') if validated_data.get('attendance_type') else None
            is_confirm = validated_data.get('is_confirm')
            termination_date=validated_data.get('termination_date') if validated_data.get('termination_date') else None
            is_auto_od=validated_data.get('is_auto_od') if validated_data.get('is_auto_od') else False
            sub_department=validated_data.get('sub_department') if validated_data.get('sub_department') else None

            care_of=validated_data.get('care_of') if validated_data.get('care_of') else None
            street_and_house_no=validated_data.get('street_and_house_no') if validated_data.get('street_and_house_no') else None
            address_2nd_line=validated_data.get('address_2nd_line') if validated_data.get('address_2nd_line') else None
            city=validated_data.get('city') if validated_data.get('city') else None
            district=validated_data.get('district') if validated_data.get('district') else None

            wbs_element=validated_data.get('wbs_element') if validated_data.get('wbs_element') else None
            retirement_date=validated_data.get('retirement_date') if validated_data.get('retirement_date') else None
            esic_no=validated_data.get('esic_no') if validated_data.get('esic_no') else None
            esi_dispensary=validated_data.get('esi_dispensary') if validated_data.get('esi_dispensary') else None
            pf_no=validated_data.get('pf_no') if validated_data.get('pf_no') else None
            emp_pension_no=validated_data.get('emp_pension_no') if validated_data.get('emp_pension_no') else None
            employee_voluntary_provident_fund_contribution=validated_data.get('employee_voluntary_provident_fund_contribution') if validated_data.get('employee_voluntary_provident_fund_contribution') else None

            '''
                Added by Rupam Hazra [13.02.2020] as perdetails
            '''
            job_location=validated_data.get('job_location') if validated_data.get('job_location') else None
            job_location_state = int(validated_data.get('job_location_state')) if validated_data.get('job_location_state') else None
            # source=validated_data.get('source') if validated_data.get('source') else None
            # source_name=validated_data.get('source_name') if validated_data.get('source_name') else None
            bank_account=validated_data.get('bank_account') if validated_data.get('bank_account') else None
            ifsc_code=validated_data.get('ifsc_code') if validated_data.get('ifsc_code') else None
            branch_name=validated_data.get('branch_name') if validated_data.get('branch_name') else None
            # pincode=validated_data.get('pincode') if validated_data.get('pincode') else None
            # emergency_contact_no=validated_data.get('emergency_contact_no') if validated_data.get('emergency_contact_no') else None
            father_name=validated_data.get('father_name') if validated_data.get('father_name') else None
            # pan_no=validated_data.get('pan_no') if validated_data.get('pan_no') else None
            # aadhar_no=validated_data.get('aadhar_no') if validated_data.get('aadhar_no') else None
            uan_no=validated_data.get('uan_no') if validated_data.get('uan_no') else None
            # pf_no=validated_data.get('pf_no') if validated_data.get('pf_no') else None
            # esic_no=validated_data.get('esic_no') if validated_data.get('esic_no') else None
            # marital_status=validated_data.get('marital_status') if validated_data.get('marital_status') else None
            # salary_per_month=validated_data.get('salary_per_month') if validated_data.get('salary_per_month') else None

            resignation_date= validated_data.get('resignation_date') if validated_data.get('resignation_date') else None
            bus_facility=validated_data.get('bus_facility') if validated_data.get('bus_facility') else False
            emergency_relationship = validated_data.get('emergency_relationship') if validated_data.get('emergency_relationship') else None
            emergency_contact_name = validated_data.get('emergency_contact_name') if validated_data.get('emergency_contact_name') else None

            has_pf=validated_data.get('has_pf') if validated_data.get('has_pf') else False
            has_esi=validated_data.get('has_esi') if validated_data.get('has_esi') else False
            bank_name_p=int(validated_data.get('bank_name_p')) if validated_data.get('bank_name_p') else None

            state = int(validated_data.get('state')) if validated_data.get('state') else None
            employee_sub_grade = int(validated_data.get("employee_sub_grade")) if validated_data.get("employee_sub_grade") else None
            employee_grade = int(validated_data.get("employee_grade")) if validated_data.get("employee_grade") else None
            is_flexi_hour=validated_data.get('is_flexi_hour') if validated_data.get('is_flexi_hour') else False

            #print('resignation_date',resignation_date,type(resignation_date))
            with transaction.atomic():
                if retirement_date:
                    retirement_date = datetime.datetime.strptime(retirement_date, "%Y-%m-%dT%H:%M:%S.%fZ")
                try:
                    usr_salary_type_obj = TCoreUserDetail.objects.filter(cu_user=instance.id, cu_is_deleted=False)[
                        0].salary_type.st_name
                except:
                    usr_salary_type_obj = None
                previous_obj = TCoreUserDetail.objects.get(cu_user=instance.id)
                usr_transfer_obj = previous_obj.__dict__
                del usr_transfer_obj['_state']
                usr_transfer_obj['cu_user'] = usr_transfer_obj['cu_user_id']
                del usr_transfer_obj['cu_user_id']
                del usr_transfer_obj['id']
                del usr_transfer_obj['rejoin_status']
                # del usr_transfer_obj['updated_cost_centre_id']
                # del usr_transfer_obj['cu_emp_code']
                from pprint import pprint
                # pprint(usr_transfer_obj)
                transfer_history = EmployeeTransferHistory.objects.create(**usr_transfer_obj)
                transfer_history_obj = EmployeeTransferHistory.objects.latest('id')
                transfer_history_obj.is_transfer = True
                transfer_history_obj.transfer_date = datetime.datetime.now()
                transfer_history_obj.transfer_by = self.context['request'].user
                cu_alt_email_id = transfer_history_obj.cu_alt_email_id
                transfer_history_obj.save()
                TCoreUserDetail.objects.filter(cu_user=instance.id, cu_is_deleted=False).update(
                    sap_personnel_no=sap_personnel_no,
                    company=company,
                    cu_emp_code=cu_emp_code,
                    # job_description=job_description,
                    hod=hod,
                    reporting_head_id=reporting_head,
                    # temp_reporting_head_id=temp_reporting_head,
                    department_id=department,
                    sub_department_id=sub_department,
                    designation_id=designation,
                    cost_centre=cost_centre,
                    updated_cost_centre_id=cost_centre,
                    salary_type_id=salary_type,
                    employee_sub_grade_id=employee_sub_grade,
                    employee_grade_id=employee_grade,
                    job_location_state_id=job_location_state,
                    job_location=job_location,
                    is_transfer=True,
                    transfer_date=datetime.datetime.now(),
                    transfer_by=self.context['request'].user
                )
                if cu_alt_email_id:

                    # ============= Mail Send ==============#

                    # Send mail to employee with login details
                    # print("in mail section")
                    user_obj = TCoreUserDetail.objects.filter(cu_user=instance.id)[0]
                    mail_data = {
                        "name": instance.first_name + '' + instance.last_name,
                        "user": instance.username,
                        "pass": user_obj.password_to_know,
                        "sap_id":user_obj.sap_personnel_no
                    }
                    # send_mail('EMPTR001', user_obj.cu_alt_email_id, mail_data)

                # pass

                # #print("in professional")
                if salary_type:
                    new_salary_type_obj = TCoreSalaryType.objects.get(id=salary_type).st_name
                    # print(new_salary_type_obj)
                    usr_obj = TCoreUserDetail.objects.get(cu_user=instance.id, cu_is_deleted=False)
                    if usr_salary_type_obj != new_salary_type_obj:
                        # print("not same")
                        if str(new_salary_type_obj) == "12":
                            usr_obj.granted_el = float(0)
                            usr_obj.granted_leaves_cl_sl = float(0)
                            usr_obj.save()
                            granted_cl = 0
                            granted_sl = 0
                            granted_el = 0
                        elif str(new_salary_type_obj) == "12.5(old)":
                            usr_obj.granted_el = float(15)
                            usr_obj.granted_leaves_cl_sl = float(10)
                            usr_obj.save()
                            granted_cl = 10
                            granted_sl = 0
                            granted_el = 15
                        elif str(new_salary_type_obj) == "12.5(new)":
                            usr_obj.granted_el = float(15)
                            usr_obj.granted_leaves_cl_sl = float(16)
                            usr_obj.save()
                            granted_cl = 16
                            granted_sl = 0
                            granted_el = 15
                        elif str(new_salary_type_obj) in ["13", "14"]:
                            usr_obj.granted_el = float(15)
                            usr_obj.granted_leaves_cl_sl = float(17)
                            usr_obj.save()
                            granted_cl = 10
                            granted_sl = 7
                            granted_el = 15
                        elif str(new_salary_type_obj) == "13(new)":
                            usr_obj.granted_el = float(15)
                            usr_obj.granted_leaves_cl_sl = float(17)
                            usr_obj.save()
                            granted_cl = 10
                            granted_sl = 7
                            granted_el = 15
                        # print("salary type not same")
                        joining_date = usr_obj.joining_date.date()
                        # #print('joining_date',joining_date)
                        joining_year = joining_date.year
                        # #print('joining_year',joining_year)
                        try:
                            leave_filter = {}
                            attendenceMonthMaster = AttendenceMonthMaster.objects.filter(
                                month_start__date__lte=joining_date,
                                month_end__date__gte=joining_date, is_deleted=False).values('id', 'grace_available',
                                                                                            'year_start_date',
                                                                                            'year_end_date',
                                                                                            'month',
                                                                                            'month_start',
                                                                                            'month_end',
                                                                                            'days_in_month',
                                                                                            'payroll_month')
                            # print(attendenceMonthMaster)
                            if attendenceMonthMaster:
                                # print(attendenceMonthMaster)
                                available_grace = grace_calculation(joining_date, attendenceMonthMaster)
                                # #print('available_grace',available_grace)
                                year_end_date = attendenceMonthMaster[0]['year_end_date'].date()
                                month_start = attendenceMonthMaster[0]['month_start'].date()
                                total_days = ((year_end_date - joining_date).days) + 1
                                # #print('total_days',total_days)
                                leave_part_1_confirm = round_calculation(total_days,
                                                                         (granted_cl + granted_sl + granted_el))
                                leave_part_2_not_cofirm = round_calculation(total_days, (granted_cl + granted_sl))
                                leave_filter['granted_leaves_cl_sl'] = leave_part_2_not_cofirm
                                if granted_el:
                                    leave_filter['el'] = round_calculation(total_days, granted_el)
                                else:
                                    leave_filter['el'] = float(0)
                                users = [instance.id]
                                # if str(usr_obj.salary_type.st_name) in ["Bonus 12.5","Bonus 13"]:
                                roundOffLeaveCalculationUpdate(users, attendenceMonthMaster,
                                                               leave_part_1_confirm, leave_part_2_not_cofirm,
                                                               total_days,
                                                               year_end_date, month_start, joining_date)

                            if available_grace:
                                # #print(" in avilavel grace")
                                if attendenceMonthMaster[0]['year_start_date'].date() < joining_date:
                                    JoiningApprovedLeave.objects.filter(employee=instance.id).update(
                                        year=joining_year,
                                        month=attendenceMonthMaster[0]['month'],
                                        **leave_filter,
                                        first_grace=available_grace,
                                        # created_by=user,
                                        # owned_by=user
                                    )
                        except:
                            pass

                if saturday_off:
                    prev_sat_data = AttendenceSaturdayOffMaster.objects.filter(employee=instance, is_deleted=False)
                    # #print('prev_sat_data',prev_sat_data)
                    if prev_sat_data:
                        for p_s in prev_sat_data:
                            p_s.first = saturday_off['first']
                            p_s.second = saturday_off['second']
                            p_s.third = saturday_off['third']
                            p_s.fourth = saturday_off['fourth']
                            p_s.all_s_day = saturday_off['all_s_day']
                            p_s.updated_by_id = logdin_user_id
                            p_s.save()
                        AttendenceSaturdayOffLogMaster.objects.create(employee=instance,
                                                                      **saturday_off,
                                                                      updated_by_id=logdin_user_id,
                                                                      )
                    else:
                        saturday_data = AttendenceSaturdayOffMaster.objects.create(employee=instance,
                                                                                   **saturday_off,
                                                                                   created_by_id=logdin_user_id,
                                                                                   owned_by_id=logdin_user_id
                                                                                   )

                        # #print('saturday_data',saturday_data)
                        AttendenceSaturdayOffLogMaster.objects.create(employee=instance,
                                                                      **saturday_off,
                                                                      created_by_id=logdin_user_id,
                                                                      owned_by_id=logdin_user_id
                                                                      )
            return instance
        except Exception as e:
            raise e



class EmployeeTransferHistorySerializer(serializers.ModelSerializer):
    emp_id = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    emp_code = serializers.SerializerMethodField()
    reporting_head = serializers.SerializerMethodField()
    reporting_head_id = serializers.SerializerMethodField()
    hod_name = serializers.SerializerMethodField()
    joining_date = serializers.SerializerMethodField()
    sap_personnel_no = serializers.SerializerMethodField()
    department_id = serializers.SerializerMethodField()
    sub_department_name = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()
    designation_name = serializers.SerializerMethodField()
    designation_id = serializers.SerializerMethodField()
    salary_type = serializers.SerializerMethodField()
    grade = serializers.SerializerMethodField()
    sub_grade = serializers.SerializerMethodField()
    job_location = serializers.SerializerMethodField()
    job_location_state = serializers.SerializerMethodField()
    transfer_date = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    state = serializers.SerializerMethodField()
    cost_centre = serializers.SerializerMethodField()

    def get_emp_id(self, obj):
        if obj.cu_user:
            return User.objects.get(id=obj.cu_user).id
        else:
            return None

    def get_full_name(self, obj):
        if obj.cu_user:
            return User.objects.get(id=obj.cu_user).get_full_name()
        else:
            return None

    def get_emp_code(self, obj):
        return obj.cu_emp_code if obj.cu_emp_code else ''

    def get_reporting_head(self, obj):
        return obj.reporting_head.get_full_name() if obj.reporting_head else ''
    def get_reporting_head_id(self, obj):
        return obj.reporting_head.id if obj.reporting_head else ''


    def get_hod_name(self, obj):

        return obj.hod.get_full_name() if obj.hod else ''

    def get_joining_date(self, obj):
        return obj.joining_date if obj.joining_date else ''

    def get_sap_personnel_no(self, obj):
        return obj.sap_personnel_no if obj.sap_personnel_no else ''

    def get_department_name(self, obj):
        return obj.department.cd_name if obj.department else ''
    def get_sub_department_name(self, obj):
        return obj.sub_department.cd_name if obj.sub_department else ''
    def get_department_id(self, obj):
        return obj.department.id if obj.department else ''

    def get_designation_name(self,obj):

        return  obj.designation.cod_name if obj.designation else ''
    def get_company_name(self,obj):

        return  obj.company.coc_name if obj.company else ''
    def get_designation_id(self,obj):

        return  obj.designation.id if obj.designation else ''
    def get_salary_type(self,obj):
        return obj.salary_type.st_name if obj.salary_type else ''
    def get_transfer_date(self,obj):
        return obj.transfer_date if obj.transfer_date else ''
    def get_grade(self, obj):
        return obj.employee_grade.cg_name if obj.employee_grade else ''
    def get_sub_grade(self, obj):
        return obj.employee_sub_grade.name if obj.employee_sub_grade else ''

    def get_job_location(self,obj):
        return obj.job_location if obj.job_location else ''
    def get_state(self,obj):
        return obj.state.cs_state_name if obj.state else ''

    def get_job_location_state(self,obj):
        return obj.job_location_state.cs_state_name if obj.job_location_state else ''
    def get_cost_centre(self,obj):
        if obj.updated_cost_centre:
            return obj.updated_cost_centre.cost_centre_name
        else:
            return obj.cost_centre if obj.cost_centre else ''


    class Meta:
        model = EmployeeTransferHistory
        fields = ('emp_id', 'full_name', 'reporting_head','reporting_head_id', 'hod_name', 'joining_date','emp_code',
                'sap_personnel_no','department_name', 'designation_name','designation_id','department_id',
                  'salary_type','grade','job_location','job_location_state','sub_grade','transfer_date','company_name',
                  'state','cost_centre','sub_department_name'
                )


class EmployeeListWithoutDetailsV2Serializer(serializers.ModelSerializer):
    sap_id = serializers.SerializerMethodField(required=False)
    # department_name = serializers.SerializerMethodField(required=False)
    # department_id = serializers.SerializerMethodField(required=False)

    first_name = serializers.SerializerMethodField(required=False)
    last_name = serializers.SerializerMethodField(required=False)
    email = serializers.SerializerMethodField(required=False)
    is_superuser = serializers.SerializerMethodField(required=False)
    is_active = serializers.SerializerMethodField(required=False)



    def get_first_name(self,obj):
       return obj.cu_user.first_name if obj.cu_user.first_name else None

    def get_last_name(self,obj):
       return obj.cu_user.last_name if obj.cu_user.last_name else None

    def get_email(self,obj):
       return obj.cu_user.email if obj.cu_user.email else None

    def get_is_superuser(self,obj):
       return obj.cu_user.is_superuser

    def get_is_active(self,obj):
       return obj.cu_user.is_active

    def get_sap_id(self,obj):
        return obj.sap_personnel_no if obj.sap_personnel_no else ''

    # def get_department_name(self,obj):
    #     return obj.department.cd_name if obj.department else ''
        
    # def get_department_id(self,obj):
    #     return obj.department.id if obj.department else ''
        

    class Meta:
        model = TCoreUserDetail
        fields=('id','first_name','last_name','email','is_superuser','is_active','sap_id')
        #fields=('id','sap_id','department_id', 'department_name')



class IntercomAddSerializer(serializers.ModelSerializer):
    floor_details = serializers.SerializerMethodField()
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())

    def get_floor_details(self,obj):
        return {
        'id':obj.floor.id,
        'name':obj.floor.name
        }
    class Meta:
        model = HrmsIntercom
        fields=('__all__')

    def update(self, instance, validated_data):
        instance.floor = validated_data.get('floor')
        instance.name = validated_data.get('name')
        instance.ext_no = validated_data.get('ext_no')
        instance.updated_by = validated_data.get('created_by')
        instance.save()
        return instance

class PreJoiningCandidateSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = PreJoiningCandidateData
        fields = ('candidate_first_name','candidate_last_name','contact_no','email_id','department','sub_department','designation','company','hod','reporting_head','employee_grade','employee_sub_grade','salary_type','cost_centre','location','attendance_type','payroll_Type','eligiblity_for_pf','applicable_for_esic','seat_no','expected_joining_date','term_insurence','term_insurence_coverage','eligible_for_bgv','aadhar_card_no','upload_aadhar_card','pan_no','upload_pan','bank_name','bank_account_number','branch_name','ifsc_code','created_by')

class PreJoiningCandidateListSerializer(serializers.ModelSerializer):
    designation = serializers.SerializerMethodField(required=False)
    department = serializers.SerializerMethodField(required=False)
    location = serializers.SerializerMethodField(required=False)
    def get_designation(self, obj):
        return {'designation_id': obj.designation.id, 'designation_name':obj.designation.cod_name} if obj.designation else {}
    def get_department(self, obj):
        return {'department_id': obj.department.id, 'department_name':obj.department.cd_name} if obj.department else {}
        #return TCoreDesignation.objects.filter(conveyance_id=ConveyanceMaster.id,is_deleted=False)
    def get_location(self, obj):
        return {'location_id': obj.location.id, 'location_name':obj.location.cs_state_name} if obj.location else {}

    class Meta:
        model = PreJoiningCandidateData
        fields = ('id','candidate_id','candidate_first_name','candidate_last_name','designation','department','location','expected_joining_date')


class PreJoiningUpdateSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    current_date =datetime.datetime.now()
    updated_at = current_date
    class Meta:
        model = PreJoiningCandidateData
        fields = ('id','candidate_id','candidate_first_name','candidate_last_name','contact_no','email_id','department','sub_department','designation','company','hod','reporting_head','employee_grade','employee_sub_grade','salary_type','cost_centre','location','attendance_type','payroll_Type','eligiblity_for_pf','applicable_for_esic','seat_no','expected_joining_date','term_insurence','term_insurence_coverage','eligible_for_bgv','aadhar_card_no','upload_aadhar_card','pan_no','upload_pan','bank_name','bank_account_number','branch_name','ifsc_code','updated_by','updated_at')



## prejoinee resource add serializer

class PreJoineeResourceAddSerializer(serializers.ModelSerializer):
    prejoinee_id = serializers.IntegerField(required=False)
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    resources = serializers.ListField(required=False)

    class Meta:
        model = PreJoineeResourceAllocation
        fields = ('prejoinee_id','resources', 'created_by')
        # extra_fields = ('work_assignments','achievements')

    def create(self, validated_data):
        try:
            with transaction.atomic():
                created_by = validated_data.get('created_by') if 'created_by' in validated_data else None
                resources = validated_data.get('resources') if 'resources' in validated_data else None
                prejoinee_id = validated_data.get('prejoinee_id') if 'prejoinee_id' in validated_data else None

                print(resources)
                if prejoinee_id:
                    if resources:
                        prejoinee_obj = PreJoiningCandidateData.objects.filter(id=prejoinee_id)
                        it_flag = 0
                        admin_flag = 0
                        facility_lst_for_it = ['Laptop','Desktop', 'Mobile Phone','Sim','Dongle','Email','EPBAX']
                        facility_lst_for_admin = ['Stationary (Basic)','Stationary (Advanced)']
                        facility_lst_for_hr = ['SAP Access']
                        if prejoinee_obj:
                            for each in resources:
                                each['created_by'] = created_by
                                each['employee'] = prejoinee_obj[0]
                                temp_responsible_department = each['responsible_department']
                                print("exceute")
                                department_obj = TCoreDepartment.objects.get(id=each['responsible_department'])
                                each['responsible_department'] = TCoreDepartment.objects.get(
                                    id=each['responsible_department'])
                                print(department_obj)
                                # if each['facility_details'] in facility_lst_for_it:
                                #     if department_obj.cd_parent_id == 2:
                                #         pass
                                #     else:
                                #         raise APIException({'msg': 'Enter a valid responsible_department for {}'.format(each['facility_details']),
                                #                             "request_status": 0})
                                # elif each['facility_details'] in facility_lst_for_admin:
                                #     if department_obj.cd_parent_id == 2:
                                #         pass
                                #     else:
                                #         raise APIException({'msg': 'Enter a valid responsible_department for {}'.format(
                                #             each['facility_details']),
                                #                             "request_status": 0})
                                # elif each['facility_details'] in facility_lst_for_hr:
                                #     if department_obj.cd_parent_id == 2:
                                #         pass
                                #     else:
                                #         raise APIException({'msg': 'Enter a valid responsible_department for {}'.format(
                                #             each['facility_details']),
                                #                             "request_status": 0})

                                print(each)
                                obj, create_status = PreJoineeResourceAllocation.objects.get_or_create(**each)
                                print(obj)
                                del each['created_by']
                                # del each['created_by']
                                each['responsible_department'] = temp_responsible_department
                                del each['employee']
                            employee_name = prejoinee_obj[0].candidate_first_name + ' ' + prejoinee_obj[0].candidate_last_name
                            date_of_joining = str(prejoinee_obj[0].expected_joining_date.date())
                            user_email = ['Up@shyamsteel.com', 'hemant@shyamsteel.com']
                            mail_data = {
                                "employee_name": employee_name,
                                "date_of_joining": date_of_joining,

                            }
                            from global_function import send_mail
                            cc = ['prakash.tripathi@shyamsteel.com']
                            sub = str(employee_name) + ':' + str(prejoinee_obj[0].candidate_id) + ' to join on ' + date_of_joining
                            # send_mail('HRMS-PJ-RA', user_email, mail_data, cc ,final_sub=sub)
                            date = datetime.datetime.now()
                            PreJoineeResourceAllocation.objects.filter(employee=prejoinee_obj[0]).update(reminder_state=0,
                                                                                                      latest_reminder_date=date,
                                                                                                      first_reminder_date=date)

                            return validated_data
                        else:
                            raise APIException({'msg': 'Enter a valid Prejoinee Id to Proceed.',
                                                "request_status": 0})


                else:
                    raise APIException({'msg': 'Enter Prejoinee Id to Proceed.',
                                        "request_status": 0})
        except Exception as e:
            raise e

class EmployeeMediclaimDetailAddSerializer(serializers.ModelSerializer):
    # employee = serializers.CharField(default=serializers.CurrentUserDefault())
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = EmployeeMediclaimDetails
        fields = ('employee', 'marital_status','spouse_name','spouse_gender','spouse_dob','first_child_name','first_child_gender','first_child_dob','second_child_name','second_child_gender','second_child_dob','include_parents','father_name','father_dob','mother_name','mother_dob','created_by')

    def create(self, validated_data):
        marital_status = validated_data.pop('marital_status') if 'marital_status' in validated_data else ''
        employee = validated_data.pop('employee') if 'employee' in validated_data else ''
        employee_obj = TCoreUserDetail.objects.filter(cu_user_id=employee)
        print(employee_obj[0])
        if marital_status and employee_obj[0]:
            if not employee_obj[0].marital_status:
                print("changing")
                usr_obj = TCoreUserDetail.objects.get(id=employee_obj[0].id)
                usr_obj.marital_status = marital_status
                usr_obj.save()
        validated_data['employee'] = employee
        validated_data['marital_status'] = marital_status
        requirement_data = EmployeeMediclaimDetails.objects.create(**validated_data)
        return requirement_data




class EmployeeMediclaimDetailListSerializer(serializers.ModelSerializer):
    employee_name= serializers.SerializerMethodField(required=False)
    employee_sap_id = serializers.SerializerMethodField(required=False)
    employee_code = serializers.SerializerMethodField(required=False)

    def get_employee_sap_id(self, obj):
        return  obj.employee.cu_user.sap_personnel_no if obj.employee.cu_user.sap_personnel_no else None

    def get_employee_name(self, obj):
        return  obj.employee.first_name + " " + obj.employee.last_name if obj.employee else None

    def get_employee_code(self, obj):
        return obj.employee.cu_user.cu_emp_code if obj.employee.cu_user else None

    
    class Meta:
        model = EmployeeMediclaimDetails
        fields = ('id','employee', 'marital_status', 'employee_code', 'employee_name','employee_sap_id','spouse_name','spouse_gender','spouse_dob','first_child_name','first_child_gender','first_child_dob','second_child_name','second_child_gender','second_child_dob','include_parents','father_name','father_dob','mother_name','mother_dob','created_by','created_at')

class EmployeeMediclaimDetailRetriveUpdateSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    current_date = datetime.datetime.now()
    updated_at = current_date

    class Meta:
        model = EmployeeMediclaimDetails
        fields = ('employee', 'marital_status','spouse_name','spouse_gender','spouse_dob','first_child_name','first_child_gender','first_child_dob','second_child_name','second_child_gender','second_child_dob','include_parents','father_name','father_dob','mother_name','mother_dob','updated_by','updated_at')

    def update(self, instance, validated_data):
        # instance.updated_by = validated_data.get('updated_by')
        # instance.is_deleted = True
        # instance.save()
        hr = self.context['request'].query_params.get('hr', None)
        enable_obj = MediclaimEnableTimeFrame.objects.latest('id')
        start_time = 0
        end_time = 0
        today_date = datetime.datetime.now()
        print(today_date)
        if enable_obj:
            start_time = enable_obj.start_time
            end_time = enable_obj.end_time
        print(start_time, end_time)
        if not hr:
            print("in if")
            if start_time and end_time:
                if today_date >= start_time and today_date <= end_time:
                    print("in 2nd if")
                    EmployeeMediclaimDetails.objects.filter(id=instance.id).update(**validated_data)
                else:
                    raise APIException({'msg': 'You are not able to edit the details.',
                                        "request_status": 0})
            else:
                raise APIException({'msg': 'You are not able to edit the details.',
                                    "request_status": 0})
        else:
            print(validated_data)
            EmployeeMediclaimDetails.objects.filter(id=instance.id).update(**validated_data)





        return instance



# serializer for enable mediclaim edit

class EmployeeMediclaimEnableEditSerializer(serializers.ModelSerializer):
    # employee = serializers.CharField(default=serializers.CurrentUserDefault())
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = MediclaimEnableTimeFrame
        fields = ('start_time', 'end_time', 'created_by')

    def create(self, validated_data):
        if MediclaimEnableTimeFrame.objects.all().count():
            MediclaimEnableTimeFrame.objects.all().delete()
        print(validated_data)
        requirement_data = MediclaimEnableTimeFrame.objects.create(**validated_data)
        return requirement_data