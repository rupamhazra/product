from django.shortcuts import render
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from pms.models import *
from pms.serializers import *
import time
import datetime
from multiplelookupfields import MultipleFieldLookupMixin
from rest_framework.views import APIView
from django.conf import settings
from rest_framework import filters
import calendar
from holidays.models import *
import collections
from rest_framework.exceptions import APIException
from django_filters.rest_framework import DjangoFilterBackend
from master.serializers import UserModuleWiseListSerializer
from master.models import TMasterModuleRole
from users.models import TCoreUserDetail
from custom_decorator import *
import os
from pms.custom_filter import *
from decimal import *
from global_notification import send_notification, store_sent_notification
from global_function import send_mail


class TourAndTravelExpenseAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    travel_stage_status=serializers.CharField(default=2)
    daily_expenses=serializers.ListField(required=False)
    vendor_or_employee_details=serializers.ListField(required=False)
    bill_received=serializers.ListField(required=False)
    flight_booking_quotations=serializers.ListField(required=False)
    final_booking_details=serializers.ListField(required=False)
    employee_name=serializers.SerializerMethodField(required=False)
    project_name = serializers.SerializerMethodField(required=False)
    notification = serializers.BooleanField(required=False)
    def get_employee_name(self,PmsTourAndTravelExpenseMaster):
        if PmsTourAndTravelExpenseMaster.employee: 
            emp_name = User.objects.filter(id=PmsTourAndTravelExpenseMaster.employee.id)
            for e_n in emp_name:
                first_name=e_n.first_name
                last_name=e_n.last_name
                full_name=first_name+""+last_name
            return full_name
    def get_project_name(self,obj):
        if obj.project:
            return obj.project.name
        else:
            return None
    class Meta:
        model = PmsTourAndTravelExpenseMaster
        fields = '__all__'
        extra_fields=('daily_expenses','vendor_or_employee_details','bill_received','flight_booking_quotations','final_booking_details','employee_name','notification')

    def create(self, validated_data):
        # try:
        daily_expenses = validated_data.pop('daily_expenses') if 'daily_expenses' in validated_data else ""
        # print(daily_expenses)
        # daily_expenses = json.loads(daily_expenses[0])
        # print(daily_expenses)
        notification = validated_data.pop('notification') if 'notification' in validated_data else False
        vendor_or_employee_details = validated_data.pop(
            'vendor_or_employee_details') if 'vendor_or_employee_details' in validated_data else ""
        bill_received = validated_data.pop('bill_received') if 'bill_received' in validated_data else ""
        flight_booking_quotations = validated_data.pop(
            'flight_booking_quotations') if 'flight_booking_quotations' in validated_data else ""
        final_booking_details = validated_data.pop(
            'final_booking_details') if 'final_booking_details' in validated_data else ""
        owned_by = validated_data.get('owned_by')
        created_by = validated_data.get('created_by')
        daily_ex_list = []
        v_e_details_list = []
        bill_received_list = []
        flight_booking_quotations_list = []
        final_booking_details_list = []
        # amount = 0.0
        with transaction.atomic():
            travel_master, created = PmsTourAndTravelExpenseMaster.objects.get_or_create(**validated_data)
            # print('travel_master',travel_master)
            all_other_expenses = Decimal(0.0)
            all_limit_exc_by = Decimal(0.0)
            all_expense = Decimal(0.0)
            all_flight_fare = Decimal(0.0)
            all_total_cost = Decimal(0.0)
            all_total = Decimal(0.0)
            all_advance_amount = Decimal(0.0)
            for d_e in daily_expenses:
                try:
                    all_other_expenses += Decimal(d_e['other_expenses'])
                except:
                    all_other_expenses += Decimal(0.0)
                # all_other_expenses += Decimal(d_e['other_expenses'])
                daily_ex_data, created = PmsTourAndTravelEmployeeDailyExpenses.objects.get_or_create(
                    expenses_master=travel_master,
                    date=datetime.datetime.strptime(d_e['date'], "%Y-%m-%dT%H:%M:%S.%fZ"),
                    description=d_e['description'],
                    fare=d_e['fare'],
                    local_conveyance=d_e['local_conveyance'],
                    lodging_expenses=d_e['lodging_expenses'],
                    fooding_expenses=d_e['fooding_expenses'],
                    da=d_e['da'],
                    other_expenses=d_e['other_expenses'],
                    created_by=created_by,
                    owned_by=owned_by
                    )
                # amount = amount + Decimal(d_e['fare'])
                daily_ex_data.__dict__.pop(
                    '_state') if "_state" in daily_ex_data.__dict__.keys() else daily_ex_data.__dict__
                # print('daily_ex_data',daily_ex_data)
                daily_ex_list.append(daily_ex_data.__dict__)
            # print('all_other_expenses',all_other_expenses)

            for v_e in vendor_or_employee_details:
                try:
                    del v_e['document']
                except:
                    pass
                try:
                    del v_e['added_docs']
                except:
                    pass
                try:
                    del v_e['empolyee_or_vendor_name']
                except:
                    pass
                # amount = amount + Decimal(v_e['bill_amount'])
                vendor_or_emp_data, created = PmsTourAndTravelVendorOrEmployeeDetails.objects.get_or_create(
                    expenses_master=travel_master,
                    **v_e,
                    created_by=created_by,
                    owned_by=owned_by
                    )
                # print('vendor_or_emp_data',vendor_or_emp_data)
                vendor_or_emp_data.__dict__.pop(
                    '_state') if '_state' in vendor_or_emp_data.__dict__.keys() else vendor_or_emp_data.__dict__
                v_e_details_list.append(vendor_or_emp_data.__dict__)

            for b_r in bill_received:
                try:
                    all_limit_exc_by += Decimal(b_r['limit_exceeded_by'])
                except:
                    all_limit_exc_by += Decimal(0.0)
                try:
                    all_expense += Decimal(b_r['total_expense'])
                except:
                    all_expense += Decimal(0.0)
                try:
                    all_advance_amount += Decimal(b_r['advance_amount'])
                except:
                    all_advance_amount += Decimal(0.0)
                # amount = amount + Decimal(b_r['total_expense'])
                bill_received_data, created = PmsTourAndTravelBillReceived.objects.get_or_create(
                    expenses_master=travel_master,
                    date=datetime.datetime.strptime(b_r['date'], "%Y-%m-%dT%H:%M:%S.%fZ"),
                    parking_expense=b_r['parking_expense'],
                    posting_expense=b_r['posting_expense'],
                    employee_or_vendor_type=b_r['employee_or_vendor_type'],
                    empolyee_or_vendor_id=b_r['empolyee_or_vendor_id'],
                    less_amount=b_r['less_amount'],
                    cgst=b_r['cgst'],
                    sgst=b_r['sgst'],
                    igst=b_r['igst'],
                    cost_center_number=b_r['cost_center_number'],
                    document_number=b_r['document_number'],
                    net_expenditure=b_r['net_expenditure'],
                    advance_amount=b_r['advance_amount'],
                    fare_and_conveyance=b_r['fare_and_conveyance'],
                    lodging_fooding_and_da=b_r['lodging_fooding_and_da'],
                    expense_mans_per_day=b_r['expense_mans_per_day'],
                    total_expense=b_r['total_expense'],
                    limit_exceeded_by=b_r['limit_exceeded_by'],
                    remarks=b_r['remarks'],
                    created_by=created_by,
                    owned_by=owned_by)
                # print('bill_received_data',bill_received_data)
                bill_received_data.__dict__.pop(
                    '_state') if '_state' in bill_received_data.__dict__.keys() else bill_received_data.__dict__

                bill_received_list.append(bill_received_data.__dict__)
            # print('all_limit_exc_by',all_limit_exc_by)
            # print('all_expense',all_expense)

            for f_b in flight_booking_quotations:
                all_flight_fare += Decimal(f_b['airline_fare'])
                try:
                    del f_b['document']
                except:
                    pass
                try:
                    del f_b['added_docs']
                except:
                    pass
                try:
                    del f_b['empolyee_or_vendor_name']
                except:
                    pass
                # amount = amount + Decimal()
                flight_booking_data, created = PmsTourAndTravelWorkSheetFlightBookingQuotation.objects.get_or_create(
                    expenses_master=travel_master,
                    **f_b,
                    created_by=created_by,
                    owned_by=owned_by)
                # print('flight_booking_data',flight_booking_data)
                flight_booking_data.__dict__.pop(
                    '_state') if '_state' in flight_booking_data.__dict__.keys() else flight_booking_data.__dict__
                flight_booking_quotations_list.append(flight_booking_data.__dict__)
            # print('all_flight_fare',all_flight_fare)

            for f_b_d in final_booking_details:
                try:
                    del f_b_d['document']
                except:
                    pass
                try:
                    del f_b_d['added_docs']
                except:
                    pass
                try:
                    del f_b_d['empolyee_or_vendor_name']
                except:
                    pass

                all_total_cost = Decimal(f_b_d['total_cost'])
                # print("no error")
                # print(f_b_d)
                final_booking_data, created = PmsTourAndTravelFinalBookingDetails.objects.get_or_create(
                    expenses_master=travel_master,
                    **f_b_d,
                    created_by=created_by,
                    owned_by=owned_by)
                # print("error")
                # print('final_booking_data',final_booking_data)
                final_booking_data.__dict__.pop(
                    '_state') if '_state' in final_booking_data.__dict__.keys() else final_booking_data.__dict__
                final_booking_details_list.append(final_booking_data.__dict__)
            # print('all_total_cost',all_total_cost)
            expense_master_obj = PmsTourAndTravelExpenseMaster.objects.latest('id')
            level_dict = {
                1: 'Project Manager',
                2: 'Project Coordinator',
                3: 'HO',
                4: 'Account',
            }
            for i in list(range(1, 5)):
                PmsTourAndTravelExpenseApprovalStatus.objects.get_or_create(
                    tour=expense_master_obj,
                    level=level_dict[i],
                    level_no=i,
                    created_by=created_by
                )

            all_total = all_other_expenses + all_expense + all_total_cost
            # print('all_total',all_total)
            travel_master.__dict__['total_expense'] = all_total
            travel_master.__dict__['limit_exceed_by'] = all_limit_exc_by
            travel_master.__dict__['total_flight_fare'] = all_flight_fare
            travel_master.__dict__['advance'] = all_advance_amount
            travel_master.save()

            travel_master.__dict__['daily_expenses'] = daily_ex_list
            travel_master.__dict__['vendor_or_employee_details'] = v_e_details_list
            travel_master.__dict__['bill_received'] = bill_received_list
            travel_master.__dict__['flight_booking_quotations'] = flight_booking_quotations_list
            travel_master.__dict__['final_booking_details'] = final_booking_details_list
            print('checkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk')

            ## Start | Sent Mail & Notification Functionality | Rupam Hazra | Date : 31-08-2020 ##

            if notification:
                project_manager_details = [travel_master.project.project_manager]
                # users = [project_manager_details]
                amount = float(travel_master.amount) if travel_master.amount else ''
                app_module = 'pms'
                title = 'A new application has been submitted.Please check the details and take necessary action.'
                body = 'Employee Name: {} \nAmount:{} \nBranch Name:{}'.format(travel_master.employee.get_full_name(),
                                                                               amount, travel_master.branch_name)
                data = {
                    "app_module": app_module,
                    "type": "travel-and-tour",
                    "sub_type": "approval/project-manager",
                    "id": travel_master.id
                }
                data_str = json.dumps(data)
                # print('data_str',data_str)
                notification_id = store_sent_notification(users=project_manager_details, body=body, title=title,
                                                          data=data_str, app_module_name=app_module)
                send_notification(users=project_manager_details, body=body, title=title, data=data,
                                  notification_id=notification_id, url=app_module)

                # Mail
                user_email = travel_master.project.project_manager.cu_user.cu_alt_email_id
                if user_email:
                    mail_data = {
                        "recipient_name": travel_master.project.project_manager.get_full_name(),
                        "name": travel_master.employee.get_full_name(),
                        "project_name": travel_master.project.name,
                        "amount": float(travel_master.amount) if travel_master.amount else '',
                        "branch_name": travel_master.branch_name if travel_master.branch_name else '',
                        "company_name": travel_master.company_name if travel_master.company_name else '',
                        "from_date": travel_master.from_date if travel_master.from_date else '',
                        "to_date": travel_master.to_date if travel_master.to_date else '',
                        "paid_to": travel_master.paid_to if travel_master.paid_to else ''
                    }

                    send_mail('PMS-TT-CN', user_email, mail_data)

            ## End | Sent Mail & Notification Functionality | Rupam Hazra | Date : 31-08-2020 ##

            return travel_master

        # except Exception as e:
        #     raise e
            # raise APIException({'request_status': 0,
            #                     'error': e,
            #                     'msg': settings.MSG_ERROR})
class TourAndTravelVendorOrEmployeeDetailsApprovalSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    # request_modification=serializers.CharField(required=False)

    class Meta:
        model = PmsTourAndTravelVendorOrEmployeeDetails
        fields = ('id','expenses_master','approved_status','request_modification', 'updated_by')
        # extra_fields = ('documents')

    def create(self,validated_data):
        try:
            
            with transaction.atomic():
                response_list=[]
                # vendor_or_emp_approval={}
                exist_vendor_or_emp_approval=PmsTourAndTravelVendorOrEmployeeDetails.objects.filter(expenses_master=validated_data.get('expenses_master'))

                if exist_vendor_or_emp_approval:
                    
                    for e_exist_vendor_or_emp_approval in exist_vendor_or_emp_approval:
                        e_exist_vendor_or_emp_approval.approved_status=validated_data.get('approved_status')
                        e_exist_vendor_or_emp_approval.request_modification=validated_data.get('request_modification')
                        e_exist_vendor_or_emp_approval.updated_by=validated_data.get('updated_by')
                        e_exist_vendor_or_emp_approval.save()

                        vendor_or_emp_approval= {
                        'id': e_exist_vendor_or_emp_approval.id,
                        'expenses_master': e_exist_vendor_or_emp_approval.expenses_master.id,
                        'approved_status': e_exist_vendor_or_emp_approval.approved_status,
                        'request_modification': e_exist_vendor_or_emp_approval.request_modification,
                        'updated_by': e_exist_vendor_or_emp_approval.updated_by
                        }
                        # print('vendor_or_emp_approval',vendor_or_emp_approval)
                        response_list.append(vendor_or_emp_approval)
                    
                    return validated_data 
        except Exception as e:
            raise e 
class TourAndTravelBillReceivedApprovalSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    # request_modification=serializers.CharField(required=False)
    class Meta:
        model = PmsTourAndTravelBillReceived
        fields = ('id','expenses_master','approved_status','request_modification','updated_by')
    def create(self,validated_data):
        try:
           
            with transaction.atomic():
                response_list=[]
                exist_bill_received=PmsTourAndTravelBillReceived.objects.filter(expenses_master=validated_data.get('expenses_master'))
                if exist_bill_received:
                    for e_exist_bill_received in exist_bill_received:
                        e_exist_bill_received.approved_status=validated_data.get('approved_status')
                        e_exist_bill_received.request_modification=validated_data.get('request_modification')
                        e_exist_bill_received.updated_by=validated_data.get('updated_by')
                        e_exist_bill_received.save()


                        bill_received_approval={
                            'id': e_exist_bill_received.id,
                            'expenses_master': e_exist_bill_received.expenses_master.id,
                            'approved_status': e_exist_bill_received.approved_status,
                            'request_modification': e_exist_bill_received.request_modification,
                            'updated_by': e_exist_bill_received.updated_by
                            }
                        response_list.append(bill_received_approval)

                    return validated_data
            
        except Exception as e:
            raise e
class TourAndTravelFinalBookingDetailsApprovalSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    # request_modification=serializers.CharField(required=False)
    class Meta:
        model = PmsTourAndTravelFinalBookingDetails
        fields = ('id','expenses_master','approved_status','request_modification','updated_by')
    def create(self,validated_data):
        try:
            response_list=[]
            with transaction.atomic():
                exist_final_booking_details=PmsTourAndTravelFinalBookingDetails.objects.filter(expenses_master=validated_data.get('expenses_master'))
                if exist_final_booking_details:
                    for e_exist_final_booking_details in exist_final_booking_details:
                        e_exist_final_booking_details.approved_status=validated_data.get('approved_status')
                        e_exist_final_booking_details.request_modification=validated_data.get('request_modification')
                        e_exist_final_booking_details.updated_by=validated_data.get('updated_by')
                        e_exist_final_booking_details.save()

                        final_booking_approval={
                            'id': e_exist_final_booking_details.id,
                            'expenses_master': e_exist_final_booking_details.expenses_master.id,
                            'approved_status': e_exist_final_booking_details.approved_status,
                            'request_modification': e_exist_final_booking_details.request_modification,
                            'updated_by':e_exist_final_booking_details.updated_by
                            }
                        response_list.append(final_booking_approval)
                return validated_data
        except Exception as e:
            raise e

class TourAndTravelExpenseMasterApprovalSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    # request_modification=serializers.CharField(required=False)
    class Meta:
        model = PmsTourAndTravelExpenseMaster
        fields =('id','approved_status','request_modification','updated_by')
    

class TourAndTravelExpenseApprovalListSerializer(serializers.ModelSerializer):
    level_approval = serializers.SerializerMethodField()
    project_name = serializers.SerializerMethodField()
    employee_name = serializers.SerializerMethodField()
    remarks = serializers.SerializerMethodField()

    def get_project_name(self, obj):
        if obj.project:
            return obj.project.name
        else:
            return None
    def get_remarks(self,obj):
        if obj:
            data_dict = PmsTourAndTravelRemarks.objects.filter(tour=obj.id).values('level','comment','user','user__username','created_at')
            data_dict = list(data_dict)
            count = 0
            for each in data_dict:
                # print(each)
                # print(count)
                if each['user']:
                    data_dict[count]['name'] = User.objects.get(id=int(each['user'])).get_full_name()
                    # print("£££££££££££££££",type(each['user']))
                else:
                    data_dict[count]['name'] = ''
                count = count + 1

            return data_dict
            # print(data_dict)
            # print(list(data_dict))
            # return list(data_dict)
        else:
            return list()

    def get_employee_name(self, obj):
        if obj.employee:
            return obj.employee.get_full_name()
        else:
            return None

    def get_level_approval(self, obj):
        if obj.id:
            data_dict = PmsTourAndTravelExpenseApprovalStatus.objects.filter(tour=obj.id).values('tour', 'level',
                                                                                                        'user__username',
                                                                                                        'level_no',
                                                                                                        'approval_status',
                                                                                                        'comment',
                                                                                                        'user',
                                                                                                        'created_at',
                                                                                                        'updated_at')
            data_dict = list(data_dict)
            data_dict_reject = PmsTourAndTravelExpenseApprovalStatus.objects.filter(tour=obj.id).values('level_no','approval_status')
            data_dict_reject = list(data_dict_reject)
            final_data = None
            for each in data_dict_reject:
                if each['approval_status'] == 'Reject':
                    final_data = each
            # final_approval_status = None
            primary_lst = [1, 2, 3, 4]
            final_approval_list = list()
            for each in data_dict_reject:
                if each['approval_status'] == 'Approve':
                    index = primary_lst.index(each['level_no'])
                    final_approval_list = primary_lst[0:index]

            # print(final_approval_list)

            count = 0
            for each in data_dict:
                # print(each)
                # print(count)
                if final_data:
                    if each['approval_status'] not in ['Reject', 'Approve']:
                        data_dict[count]['approval_status'] = 'Not Applicable'
                if final_approval_list:
                    if each['level_no'] in final_approval_list and each['approval_status'] not in ['Approve']:
                        data_dict[count]['approval_status'] = 'Not Applicable'

                if each['user']:
                    data_dict[count]['name'] = User.objects.get(id=int(each['user'])).get_full_name()
                    # print("£££££££££££££££",type(each['user']))
                else:
                    data_dict[count]['name'] = ''
                count = count + 1
            return data_dict
            # print(data_dict)
            # print(list(data_dict))
            # return list(data_dict)
        else:
            return list()
    class Meta:
        model = PmsTourAndTravelExpenseMaster
        fields = ('id','user_type','project','remarks','project_name','employee_name','employee','guest','place_of_travel','total_expense','limit_exceed_by','total_flight_fare','advance','from_date','to_date','is_paid','status','approved_status','level_approval')

class EmployeeTourAndTravelExpenseListSerializer(serializers.ModelSerializer):
    from_date = serializers.SerializerMethodField(required=False)
    to_date = serializers.SerializerMethodField(required=False)
    approved_status = serializers.SerializerMethodField(required=False)
    project_manager_approval_status = serializers.SerializerMethodField(required=False)
    site_coordinator_approval_status = serializers.SerializerMethodField(required=False)
    HO_status = serializers.SerializerMethodField(required=False)
    accounts_approval_status = serializers.SerializerMethodField(required=False)
    def get_from_date(self,obj):
        if obj.from_date:
            return obj.from_date.date()
        else:
            return  None
    def get_to_date(self,obj):
        if obj.to_date:
            return obj.to_date.date()
        else:
            return None
    def get_approved_status(self,obj):
        if obj.approved_status:
            a = {1:'approve',2:'reject',3:'modification'}
            if obj.approved_status:
                return a[int(obj.approved_status)]
        else:
            return None

    def get_project_manager_approval_status(self, obj):
        if obj.id:
            try:
                data_dict = PmsTourAndTravelExpenseApprovalStatus.objects.get(tour=obj.id, level_no=1)
                # print(data_dict)
                # print(list(data_dict))
                # print(data_dict.approval_status)
                approval_status_lst = PmsTourAndTravelExpenseApprovalStatus.objects.filter(tour=obj.id,
                                                                                           level_no__in=[2, 3,
                                                                                                         4]).values_list(
                    'approval_status', flat=True)
                approval_status_lst = list(approval_status_lst)
                if obj.status == "Reject" and data_dict.approval_status not in ['Approve', 'Reject']:
                    return 'Not Applicable'
                elif 'Approve' in approval_status_lst and data_dict.approval_status not in ['Approve', 'Reject']:
                    return 'Not Applicable'
                elif data_dict.approval_status == "Approve":
                    return "Approve"
                elif data_dict.approval_status == "Reject":
                    return 'Reject'
                else:
                    return "Pending"
            except:
                return "pending"
        else:
            return None

    def get_site_coordinator_approval_status(self, obj):
        if obj.id:
            try:
                data_dict = PmsTourAndTravelExpenseApprovalStatus.objects.get(tour=obj.id, level_no=2)
                # print(data_dict)
                # print(list(data_dict))
                approval_status_lst = PmsTourAndTravelExpenseApprovalStatus.objects.filter(tour=obj.id, level_no__in=[3,
                                                                                                                      4]).values_list(
                    'approval_status', flat=True)
                approval_status_lst = list(approval_status_lst)
                if obj.status == "Reject" and data_dict.approval_status not in ['Approve', 'Reject']:
                    return 'Not Applicable'
                elif 'Approve' in approval_status_lst and data_dict.approval_status not in ['Approve', 'Reject']:
                    return 'Not Applicable'
                elif data_dict.approval_status == "Approve":
                    return "Approve"
                elif data_dict.approval_status == "Reject":
                    return 'Reject'
                else:
                    return "Pending"

            except:
                return "pending"
        else:
            return None

    def get_HO_status(self, obj):
        if obj.id:
            try:
                data_dict = PmsTourAndTravelExpenseApprovalStatus.objects.get(tour=obj.id, level_no=3)
                # print(data_dict)
                # print(list(data_dict))
                approval_status_lst = PmsTourAndTravelExpenseApprovalStatus.objects.filter(tour=obj.id, level_no__in=[
                    4]).values_list('approval_status', flat=True)
                approval_status_lst = list(approval_status_lst)
                if obj.status == "Reject" and data_dict.approval_status not in ['Approve', 'Reject']:
                    return 'Not Applicable'
                elif 'Approve' in approval_status_lst and data_dict.approval_status not in ['Approve', 'Reject']:
                    return 'Not Applicable'
                elif data_dict.approval_status == "Approve":
                    return "Approve"
                elif data_dict.approval_status == "Reject":
                    return 'Reject'
                else:
                    return "Pending"
            except:
                return "pending"
        else:
            return None

    def get_accounts_approval_status(self, obj):
        if obj.id:
            try:
                data_dict = PmsTourAndTravelExpenseApprovalStatus.objects.get(tour=obj.id, level_no=4)
                # print(data_dict)
                # print(list(data_dict))
                if obj.status == "Reject" and data_dict.approval_status not in ['Approve', 'Reject']:
                    print(data_dict.approval_status)
                    return 'Not Applicable'
                elif data_dict.approval_status == "Approve":
                    return "Approve"
                elif data_dict.approval_status == "Reject":
                    return 'Reject'
                else:
                    return "Pending"
            except:
                return "pending"
        else:
            return None

    class Meta:
        model = PmsTourAndTravelExpenseMaster
        fields = ('id','user_type','employee','guest','place_of_travel','total_expense','limit_exceed_by','total_flight_fare','advance','from_date','to_date','approved_status','project_manager_approval_status','site_coordinator_approval_status','HO_status','accounts_approval_status')


class TourAndTravelApprovalListSerializer(serializers.ModelSerializer):
    level_approval = serializers.SerializerMethodField()
    project_name = serializers.SerializerMethodField()
    employee_name = serializers.SerializerMethodField()
    remarks = serializers.SerializerMethodField()
    def get_project_name(self,obj):
        if obj.project:
            return obj.project.name
        else:
            return None
    def get_employee_name(self,obj):
        if obj.employee:
            return obj.employee.get_full_name()
        else:
            return None
    def get_level_approval(self,obj):
        if obj.id:
            data_dict = PmsTourAndTravelExpenseApprovalStatus.objects.filter(tour=obj.id).values('tour', 'level', 'level_no',
                                                                                            'approval_status','comment','user','user__username','created_at','updated_at')
            # print(data_dict)
            # print(list(data_dict))
            data_dict = list(data_dict)
            data_dict_reject = PmsTourAndTravelExpenseApprovalStatus.objects.filter(tour=obj.id).values('level_no',
                                                                                                        'approval_status')
            data_dict_reject = list(data_dict_reject)
            final_data = None
            for each in data_dict_reject:
                if each['approval_status'] == 'Reject':
                    final_data = each

            primary_lst = [1, 2, 3, 4]
            final_approval_list = list()
            for each in data_dict_reject:
                if each['approval_status'] == 'Approve':
                    index = primary_lst.index(each['level_no'])
                    final_approval_list = primary_lst[0:index]

            # print(final_approval_list)
            count = 0
            for each in data_dict:
                # print(each)
                # print(count)
                if final_data:
                    if each['approval_status'] not in ['Reject','Approve']:
                        data_dict[count]['approval_status'] = 'Not Applicable'

                if final_approval_list:
                    if each['level_no'] in final_approval_list and each['approval_status'] not in ['Approve']:
                        data_dict[count]['approval_status'] = 'Not Applicable'
                if each['user']:
                    data_dict[count]['name'] = User.objects.get(id=int(each['user'])).get_full_name()
                    # print("£££££££££££££££",type(each['user']))
                else:
                    data_dict[count]['name'] = ''
                count = count + 1
            return data_dict
        else:
            return list()
    def get_remarks(self,obj):
        if obj:
            data_dict = PmsTourAndTravelRemarks.objects.filter(tour=obj.id).values('level','comment','user','user__username','created_at')
            # print(data_dict)
            # print(list(data_dict))
            data_dict = list(data_dict)
            count = 0
            for each in data_dict:
                # print(each)
                # print(count)
                if each['user']:
                    data_dict[count]['name'] = User.objects.get(id=int(each['user'])).get_full_name()
                    # print("£££££££££££££££",type(each['user']))
                else:
                    data_dict[count]['name'] = ''
                count = count + 1

            return data_dict
        else:
            return list()
    class Meta:
        model = PmsTourAndTravelExpenseMaster
        fields = ('id','user_type','project','project_name','employee','employee_name','remarks','level_approval','guest','is_paid','status','place_of_travel','total_expense','limit_exceed_by','total_flight_fare','advance','from_date','to_date','approved_status')
        # extra_fields = ('level_approval')


class TourExpencePaymentUpdateSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    tour_expence_approvals = serializers.ListField(required=False)
    remarks = serializers.CharField(required=False,allow_null=True)
    notification = serializers.BooleanField(required=False)

    class Meta:
        model = PmsTourAndTravelExpenseMaster
        fields = ('id','is_paid','updated_by','tour_expence_approvals','remarks','notification')

    def send_notification_to_user(self,project,travel_master,user):
        app_module = 'pms'

        # For send to User
        users = [user]
        user_email = user.cu_user.cu_alt_email_id
        recipient_name = user.get_full_name()
        remarks = None
        remark_details = PmsTourAndTravelRemarks.objects.filter(tour=travel_master,user=travel_master.updated_by)
        if remark_details:
            remark_details = remark_details[0]
            remarks = remark_details.comment

        title = 'Your application payment status has been updated.Please check the details.'
        body ='Approvar Name: {} \nUpdated At:{} \nRemarks'.format(
            travel_master.updated_by.get_full_name(),
            travel_master.updated_at,
            remarks
            )
        data = {
                    "app_module":app_module,
                    "type":"travel-and-tour",
                    "sub_type":"my-tours",
                    "id":travel_master.id
                }
        data_str = json.dumps(data)
        #print('data_str',data_str)
        notification_id = store_sent_notification(users=users,body=body,title=title,data=data_str,app_module_name=app_module)
        send_notification(users=users,body=body,title=title,data=data,notification_id=notification_id,url=app_module)

        # Mail
        if user_email:
            mail_data = {
                            "recipient_name":recipient_name,
                            "name": travel_master.employee.get_full_name(),
                            "project_name":travel_master.project.name,
                            "amount": travel_master.amount if travel_master.amount else '',
                            "branch_name": travel_master.branch_name if travel_master.branch_name else '',
                            "company_name":travel_master.company_name if travel_master.company_name else '',
                            "from_date":travel_master.from_date if travel_master.from_date  else '',
                            "to_date":travel_master.to_date if travel_master.to_date else '',
                            "paid_to":travel_master.paid_to if travel_master.paid_to else ''
                        }
            
            send_mail('PMS-TT-PN',user_email,mail_data)
       

    def create(self, validated_data):
        try:
            with transaction.atomic():
                #notification = validated_data.pop('notification') if 'notification' in validated_data else False
                notification = True
                tour_expence_ids = validated_data.get('tour_expence_approvals')
                comment = validated_data.get('remarks')
                updated_by = validated_data.get('updated_by')
                #print(tour_expence_ids)
                for e_tour_expence_id in tour_expence_ids:
                    expence_obj = PmsTourAndTravelExpenseMaster.objects.get(id=e_tour_expence_id)
                    expence_obj.is_paid = True
                    expence_obj.save()
                    if comment:
                        PmsTourAndTravelRemarks.objects.create(tour=expence_obj, comment=comment,
                                                               level='Payment',user=updated_by,created_by=updated_by)

                    if notification:
                        self.send_notification_to_user(project,expence_obj,expence_obj.employee)

                return validated_data
        except Exception as e:
            raise APIException({"msg": e, "request_status": 0})



class TourExpenceStatusUpdateSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    request_by = serializers.CharField(required=False)
    comment = serializers.CharField(required=False)
    tour_expence_approvals = serializers.ListField(required=False)
    notification = serializers.BooleanField(required=False)

    class Meta:
        model = PmsTourAndTravelExpenseMaster
        fields = ('request_by', 'updated_by', 'comment','tour_expence_approvals','notification')

    def send_notification_to_approvar(self,request_by,project,travel_master,user):
        user_email = None
        recipient_name = None
        if request_by == 'project_manager':
            users = [travel_master.project.project_coordinator]
            recipient_name = travel_master.project.project_coordinator.get_full_name()
            user_email = travel_master.project.project_coordinator.cu_user.cu_alt_email_id
            #print('users',users)
        if request_by == 'project_coordinator':
            ho_details = PmsTourHoUser.objects.filter(is_deleted=False)
            if ho_details:
                ho_details = ho_details[0]
                users = [ho_details.user]
                user_email = ho_details.user.cu_user.cu_alt_email_id
                recipient_name = ho_details.user.get_full_name()
        if request_by == 'HO':
            request_by = 'ho'
            account_details = PmsTourAccounts.objects.filter(is_deleted=False)
            if account_details:
                account_details = account_details[0]
                users = [account_details.user]
                user_email = account_details.user.cu_user.cu_alt_email_id
                recipient_name = account_details.user.get_full_name()
        
        app_module = 'pms'
        level = request_by.replace('_',' ')
        if request_by != 'account_approval':    

            # For send to approvar
            title = 'A new application has been approved by '+request_by.replace('_',' ')+'.Please check the details and take necessary action.'
            body ='Employee Name: {} \nAmount:{} \nBranch Name:{}'.format(travel_master.employee.get_full_name(),travel_master.amount,travel_master.branch_name)
            data = {
                        "app_module":app_module,
                        "type":"travel-and-tour",
                        "sub_type":"approval/"+request_by.replace('_','-'),
                        "id":travel_master.id
                    }
            data_str = json.dumps(data)
            notification_id = store_sent_notification(users=users,body=body,title=title,data=data_str,app_module_name=app_module)
            send_notification(users=users,body=body,title=title,data=data,notification_id=notification_id,url=app_module)

            # Mail
            
            if user_email:
                mail_data = {
                                "status":'Approved',
                                "request_by":request_by.replace('_',' '),
                                "recipient_name":recipient_name,
                                "name": travel_master.employee.get_full_name(),
                                "project_name":travel_master.project.name,
                                "amount": travel_master.amount if travel_master.amount else '',
                                "branch_name": travel_master.branch_name if travel_master.branch_name else '',
                                "company_name":travel_master.company_name if travel_master.company_name else '',
                                "from_date":travel_master.from_date if travel_master.from_date  else '',
                                "to_date":travel_master.to_date if travel_master.to_date else '',
                                "paid_to":travel_master.paid_to if travel_master.paid_to else ''
                            }
                
                send_mail('PMS-TT-AN',user_email,mail_data)



        else:
            level = 'Account'
        
            # For send to User
            users = [user]
            recipient_name = user.get_full_name()
            user_email = user.cu_user.cu_alt_email_id
            approvar_details = PmsTourAndTravelExpenseApprovalStatus.objects.filter(tour=travel_master,is_deleted=False,level=level)
            #print('approvar_details1111',approvar_details.query)
            #print('approvar_details',approvar_details)
            remarks = None
            if approvar_details:
                approvar_details = approvar_details[0]
                remark_details = PmsTourAndTravelRemarks.objects.filter(tour=travel_master,level=level)
                if remark_details:
                    remark_details = remark_details[0]
                    remarks = remark_details.comment
            
            title_for_user = 'your application has been approved by '+level+'.Please check the details.'
            body_for_user ='Approvar Name: {} \nApproved At:{} \nRemarks'.format(
                approvar_details.user.get_full_name(),
                approvar_details.updated_at,
                remarks
                )
            data_for_user = {
                        "app_module":app_module,
                        "type":"travel-and-tour",
                        "sub_type":"my-tours",
                        "id":travel_master.id
                    }
            data_str = json.dumps(data_for_user)
            notification_id = store_sent_notification(users=users,body=body_for_user,title=title_for_user,data=data_str,app_module_name=app_module)
            send_notification(users=users,body=body_for_user,title=title_for_user,data=data_for_user,notification_id=notification_id,url=app_module)

            # For Mail
            if user_email:
                mail_data = {
                                "status":'Approved',
                                "request_by":level,
                                "recipient_name":recipient_name,
                                "name": travel_master.employee.get_full_name(),
                                "project_name":travel_master.project.name,
                                "amount": travel_master.amount if travel_master.amount else '',
                                "branch_name": travel_master.branch_name if travel_master.branch_name else '',
                                "company_name":travel_master.company_name if travel_master.company_name else '',
                                "from_date":travel_master.from_date if travel_master.from_date  else '',
                                "to_date":travel_master.to_date if travel_master.to_date else '',
                                "paid_to":travel_master.paid_to if travel_master.paid_to else ''
                            }
                
                send_mail('PMS-TT-UN',user_email,mail_data)

    def create(self, validated_data):
        try:
            with transaction.atomic():
                print('validated_data',validated_data)
                tour_expence_ids = validated_data.get('tour_expence_approvals')
                request_by = validated_data.get('request_by')
                updated_by = validated_data.get('updated_by')
                #notification = validated_data.pop('notification') if 'notification' in validated_data else False
                notification = True
                comment = validated_data.get('comment') if 'comment' in validated_data else ''
                project = None
                for each in tour_expence_ids:
                    instance = PmsTourAndTravelExpenseMaster.objects.get(id=int(each))
                    project = instance.project
                    if request_by == "project_manager":
                        if instance.current_level_of_approval == "Project_Manager" and instance.status == "Pending For Project Manager Approval":
                            instance.current_level_of_approval = "Project_Coordinator"
                            instance.status = "Pending For Project Coordinator Approval"
                            instance.updated_by = updated_by
                            instance.save()
                            expense_config_obj = PmsTourAndTravelExpenseApprovalStatus.objects.get(tour=instance.id, level_no=1)
                            # print(expense_config_obj)
                            expense_config_obj.comment = comment
                            expense_config_obj.approval_status = "Approve"
                            expense_config_obj.user = updated_by
                            expense_config_obj.updated_by = updated_by
                            expense_config_obj.save()
                            if comment:
                                PmsTourAndTravelRemarks.objects.create(tour=instance,comment=comment,user=updated_by,
                                                                       level='Project Manager',created_by=updated_by)
                    elif request_by == "project_coordinator":
                        if instance.current_level_of_approval in ["Project_Manager","Project_Coordinator"] and instance.status in ["Pending For Project Manager Approval","Pending For Project Coordinator Approval"]:
                            instance.current_level_of_approval = "HO"
                            instance.status = "Pending For HO Approval"
                            instance.updated_by = updated_by
                            instance.save()
                            expense_config_obj = PmsTourAndTravelExpenseApprovalStatus.objects.get(tour=instance.id, level_no=2)
                            # print(expense_config_obj)
                            expense_config_obj.comment = comment
                            expense_config_obj.approval_status = "Approve"
                            expense_config_obj.user = updated_by
                            expense_config_obj.updated_by = updated_by
                            expense_config_obj.save()
                            if comment:
                                PmsTourAndTravelRemarks.objects.create(tour=instance,comment=comment,user=updated_by,
                                                                       level='Project Coordinator',created_by=updated_by)
                    elif request_by == "HO":
                        if instance.current_level_of_approval in ["Project_Manager","Project_Coordinator","HO"] and instance.status in ["Pending For Project Manager Approval","Pending For Project Coordinator Approval","Pending For HO Approval"]:
                            instance.current_level_of_approval = "Account_Approval"
                            instance.status = "Pending For Account Approval"
                            instance.updated_by = updated_by
                            instance.save()
                            expense_config_obj = PmsTourAndTravelExpenseApprovalStatus.objects.get(tour=instance.id, level_no=3)
                            # print(expense_config_obj)
                            expense_config_obj.comment = comment
                            expense_config_obj.approval_status = "Approve"
                            expense_config_obj.user = updated_by
                            expense_config_obj.updated_by = updated_by
                            expense_config_obj.save()
                            if comment:
                                PmsTourAndTravelRemarks.objects.create(tour=instance,comment=comment,
                                                                       level='HO',user=updated_by,created_by=updated_by)
                    elif request_by == "account_approval":
                        if instance.current_level_of_approval in ["Project_Manager","Project_Coordinator","HO","Account_Approval"] and instance.status in ["Pending For Project Manager Approval",
                                            "Pending For Project Coordinator Approval","Pending For HO Approval",
                                            "Pending For Account Approval"]:

                            instance.current_level_of_approval = "Approve"
                            instance.status = "Approve"
                            instance.updated_by = updated_by
                            instance.approved_status = 1
                            instance.save()
                            expense_config_obj = PmsTourAndTravelExpenseApprovalStatus.objects.get(tour=instance.id, level_no=4)
                            # print(expense_config_obj)
                            expense_config_obj.comment = comment
                            expense_config_obj.approval_status = "Approve"
                            expense_config_obj.user = updated_by
                            expense_config_obj.updated_by = updated_by
                            expense_config_obj.save()
                            if comment:
                                PmsTourAndTravelRemarks.objects.create(tour=instance,comment=comment,
                                                                       level='Account',user=updated_by,created_by=updated_by)

                    if notification:
                        self.send_notification_to_approvar(request_by,project,instance,instance.employee)        
                                
                
                return validated_data

        except Exception as e:
            raise APIException({"msg": e, "request_status": 0})

class TourExpenceStatusRejectSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    request_by = serializers.CharField(required=False)
    comment = serializers.CharField(required=False)
    tour_expence_approvals = serializers.ListField(required=False)
    notification = serializers.BooleanField(required=False)


    class Meta:
        model = PmsTourAndTravelExpenseMaster
        fields = ('request_by', 'updated_by', 'comment','tour_expence_approvals','notification')

    def send_notification_to_user(self,request_by,project,travel_master,user):        
        users = [user]
        user_email = user.cu_user.cu_alt_email_id
        recipient_name = user.get_full_name()
        level = request_by.replace('_',' ')
        #print('level',level)
        approvar_details = PmsTourAndTravelExpenseApprovalStatus.objects.filter(tour=travel_master,is_deleted=False,level=level)
        #print('approvar_details',approvar_details)
        remarks = None
        if approvar_details:
            approvar_details = approvar_details[0]
            remark_details = PmsTourAndTravelRemarks.objects.filter(tour=travel_master,level=level)
            if remark_details:
                remark_details = remark_details[0]
                remarks = remark_details.comment

        app_module = 'pms'
        title = 'Your application has been rejected by '+level+'.Please check the details.'
        body ='Approvar Name: {} \nRejected At:{} \nRemarks'.format(
            approvar_details.user.get_full_name(),
            approvar_details.updated_at,
            remarks
            )
        data = {
                    "app_module":app_module,
                    "type":"travel-and-tour",
                    "sub_type":"my-tours",
                    "id":travel_master.id
                }
        data_str = json.dumps(data)
        notification_id = store_sent_notification(users=users,body=body,title=title,data=data_str,app_module_name=app_module)
        send_notification(users=users,body=body,title=title,data=data,notification_id=notification_id,url=app_module)

        # Mail
        if user_email:
            mail_data = {
                            "status":'Rejected',
                            "request_by":level,
                            "recipient_name":recipient_name,
                            "name": travel_master.employee.get_full_name(),
                            "project_name":travel_master.project.name,
                            "amount": travel_master.amount if travel_master.amount else '',
                            "branch_name": travel_master.branch_name if travel_master.branch_name else '',
                            "company_name":travel_master.company_name if travel_master.company_name else '',
                            "from_date":travel_master.from_date if travel_master.from_date  else '',
                            "to_date":travel_master.to_date if travel_master.to_date else '',
                            "paid_to":travel_master.paid_to if travel_master.paid_to else ''
                        }
            
            send_mail('PMS-TT-UN',user_email,mail_data)


    def create(self, validated_data):
        try:
            with transaction.atomic():
                print('validated_data',validated_data)
                tour_expence_ids = validated_data.get('tour_expence_approvals')
                request_by = validated_data.get('request_by')
                updated_by = validated_data.get('updated_by')
                #notification = validated_data.pop('notification') if 'notification' in validated_data else False
                notification = True
                comment = validated_data.get('comment') if 'comment' in validated_data else ''
                for each in tour_expence_ids:
                    instance = PmsTourAndTravelExpenseMaster.objects.get(id=int(each))
                    if request_by == "project_manager":
                        if instance.current_level_of_approval == "Project_Manager" and instance.status == "Pending For Project Manager Approval" \
                                and instance.status != "Reject":
                            instance.current_level_of_approval = "Reject"
                            instance.status = "Reject"
                            instance.updated_by = updated_by
                            instance.save()
                            expense_config_obj = PmsTourAndTravelExpenseApprovalStatus.objects.get(
                                tour=instance.id, level_no=1)
                            # print(expense_config_obj)
                            expense_config_obj.comment = comment
                            expense_config_obj.approval_status = "Reject"
                            expense_config_obj.user = updated_by
                            expense_config_obj.updated_by = updated_by
                            expense_config_obj.save()
                            if comment:
                                PmsTourAndTravelRemarks.objects.create(tour=instance,comment=comment,user=updated_by,
                                                                       level='Project Manager',created_by=updated_by)
                        request_by = 'Project Manager'
                    elif request_by == "project_coordinator":
                        if instance.current_level_of_approval in ["Project_Manager",
                                                                  "Project_Coordinator"] and instance.status in [
                            "Pending For Project Manager Approval", "Pending For Project Coordinator Approval"] \
                                and instance.status != "Reject":
                            instance.current_level_of_approval = "Reject"
                            instance.status = "Reject"
                            instance.updated_by = updated_by
                            instance.save()
                            expense_config_obj = PmsTourAndTravelExpenseApprovalStatus.objects.get(
                                tour=instance.id, level_no=2)
                            # print(expense_config_obj)
                            expense_config_obj.comment = comment
                            expense_config_obj.approval_status = "Reject"
                            expense_config_obj.user = updated_by
                            expense_config_obj.updated_by = updated_by
                            expense_config_obj.save()
                            if comment:
                                PmsTourAndTravelRemarks.objects.create(tour=instance,comment=comment,user=updated_by,
                                                                       level='Project Coordinator',created_by=updated_by)
                        request_by = 'Project Coordinator'
                    elif request_by == "HO":
                        if instance.current_level_of_approval in ["Project_Manager", "Project_Coordinator",
                                                                  "HO"] and instance.status in [
                            "Pending For Project Manager Approval", "Pending For Project Coordinator Approval",
                            "Pending For HO Approval"] and instance.status != "Reject":
                            instance.current_level_of_approval = "Reject"
                            instance.status = "Reject"
                            instance.updated_by = updated_by
                            instance.save()
                            expense_config_obj = PmsTourAndTravelExpenseApprovalStatus.objects.get(
                                tour=instance.id, level_no=3)
                            # print(expense_config_obj)
                            expense_config_obj.comment = comment
                            expense_config_obj.approval_status = "Reject"
                            expense_config_obj.user = updated_by
                            expense_config_obj.updated_by = updated_by
                            expense_config_obj.save()
                            if comment:
                                PmsTourAndTravelRemarks.objects.create(tour=instance,comment=comment,user=updated_by,
                                                                       level='HO',created_by=updated_by)
                    elif request_by == "account_approval":
                        if instance.current_level_of_approval in ["Project_Manager", "Project_Coordinator", "HO",
                                                                  "Account_Approval"] \
                                and instance.status in ["Pending For Project Manager Approval",
                                                        "Pending For Project Coordinator Approval",
                                                        "Pending For HO Approval",
                                                        "Pending For Account Approval"] and instance.status != "Reject":
                            instance.current_level_of_approval = "Reject"
                            instance.status = "Reject"
                            instance.updated_by = updated_by
                            instance.approved_status = 2
                            instance.save()
                            expense_config_obj = PmsTourAndTravelExpenseApprovalStatus.objects.get(
                                tour=instance.id, level_no=4)
                            # print(expense_config_obj)
                            expense_config_obj.comment = comment
                            expense_config_obj.approval_status = "Reject"
                            expense_config_obj.user = updated_by
                            expense_config_obj.updated_by = updated_by
                            expense_config_obj.save()
                            if comment:
                                PmsTourAndTravelRemarks.objects.create(tour=instance,comment=comment,user=updated_by,
                                                                       level='Account',created_by=updated_by)

                        request_by = 'Account'

                    if notification:
                        self.send_notification_to_user(request_by,project,instance,instance.employee)
                
                return validated_data

        except Exception as e:
            raise APIException({"msg": e, "request_status": 0})


class EmployeeTourAndTravelExpenseReportSerializer(serializers.ModelSerializer):
    from_date = serializers.SerializerMethodField(required=False)
    to_date = serializers.SerializerMethodField(required=False)
    approved_status = serializers.SerializerMethodField(required=False)
    employee = serializers.SerializerMethodField(required=False)
    payment_status = serializers.SerializerMethodField(required=False)
    project_manager_approval_status = serializers.SerializerMethodField(required=False)
    site_coordinator_approval_status = serializers.SerializerMethodField(required=False)
    HO_status = serializers.SerializerMethodField(required=False)
    accounts_approval_status = serializers.SerializerMethodField(required=False)
    def get_employee(self,obj):
        if obj.employee:
            print(obj.employee.get_full_name())
            return obj.employee.get_full_name()
        else:
            return None
    def get_payment_status(selfself,obj):
        if obj.is_paid:
            return "Paid"
        else:
            return "Unpaid"
    def get_from_date(self,obj):
        if obj.from_date:
            return obj.from_date.date()
        else:
            return None
    def get_to_date(self,obj):
        if obj.to_date:
            return obj.to_date.date()
        else:
            return None
    def get_approved_status(self,obj):
        if obj.approved_status:
            a = {1:'approve',2:'reject',3:'modification'}
            if obj.approved_status:
                return a[int(obj.approved_status)]
        else:
            return "pending"
    def get_project_manager_approval_status(self,obj):
        if obj.id:
            try:
                data_dict = PmsTourAndTravelExpenseApprovalStatus.objects.get(tour=obj.id, level_no=1)
                # print(data_dict)
                # print(list(data_dict))
                # print(data_dict.approval_status)
                approval_status_lst = PmsTourAndTravelExpenseApprovalStatus.objects.filter(tour=obj.id, level_no__in=[2,3,4]).values_list('approval_status', flat=True)
                approval_status_lst = list(approval_status_lst)
                if obj.status == "Reject" and data_dict.approval_status not in ['Approve', 'Reject']:
                    return 'Not Applicable'
                elif 'Approve' in approval_status_lst and data_dict.approval_status not in ['Approve','Reject']:
                    return 'Not Applicable'
                elif data_dict.approval_status == "Approve":
                    return "Approve"
                elif data_dict.approval_status == "Reject":
                    return 'Reject'
                else:
                    return "Pending"
            except:
                return "pending"
        else:
            return None
    def get_site_coordinator_approval_status(self,obj):
        if obj.id:
            try:
                data_dict = PmsTourAndTravelExpenseApprovalStatus.objects.get(tour=obj.id, level_no=2)
                # print(data_dict)
                # print(list(data_dict))
                approval_status_lst = PmsTourAndTravelExpenseApprovalStatus.objects.filter(tour=obj.id, level_no__in=[3,4]).values_list('approval_status', flat=True)
                approval_status_lst = list(approval_status_lst)
                if obj.status == "Reject" and data_dict.approval_status not in ['Approve', 'Reject']:
                    return 'Not Applicable'
                elif 'Approve' in approval_status_lst and data_dict.approval_status not in ['Approve', 'Reject']:
                    return 'Not Applicable'
                elif data_dict.approval_status == "Approve":
                    return "Approve"
                elif data_dict.approval_status == "Reject":
                    return 'Reject'
                else:
                    return "Pending"

            except:
                return "pending"
        else:
            return None
    def get_HO_status(self,obj):
        if obj.id:
            try:
                data_dict = PmsTourAndTravelExpenseApprovalStatus.objects.get(tour=obj.id, level_no=3)
                # print(data_dict)
                # print(list(data_dict))
                approval_status_lst = PmsTourAndTravelExpenseApprovalStatus.objects.filter(tour=obj.id, level_no__in=[4]).values_list('approval_status', flat=True)
                approval_status_lst = list(approval_status_lst)
                if obj.status == "Reject" and data_dict.approval_status not in ['Approve', 'Reject']:
                    return 'Not Applicable'
                elif 'Approve' in approval_status_lst and data_dict.approval_status not in ['Approve', 'Reject']:
                    return 'Not Applicable'
                elif data_dict.approval_status == "Approve":
                    return "Approve"
                elif data_dict.approval_status == "Reject":
                    return 'Reject'
                else:
                    return "Pending"
            except:
                return "pending"
        else:
            return None
    def get_accounts_approval_status(self,obj):
        if obj.id:
            try:
                data_dict = PmsTourAndTravelExpenseApprovalStatus.objects.get(tour=obj.id, level_no=4)
                # print(data_dict)
                # print(list(data_dict))
                if obj.status == "Reject" and data_dict.approval_status not in ['Approve', 'Reject']:
                    print(data_dict.approval_status)
                    return 'Not Applicable'
                elif data_dict.approval_status == "Approve":
                    return "Approve"
                elif data_dict.approval_status == "Reject":
                    return 'Reject'
                else:
                    return "Pending"
            except:
                return "pending"
        else:
            return None

    class Meta:
        model = PmsTourAndTravelExpenseMaster
        fields = ('id','user_type','employee','guest','place_of_travel','total_expense','limit_exceed_by','total_flight_fare','advance','from_date','to_date','approved_status','payment_status','project_manager_approval_status','site_coordinator_approval_status','HO_status','accounts_approval_status')