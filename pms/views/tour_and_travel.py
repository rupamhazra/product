from django.shortcuts import render
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated,AllowAny
from rest_framework.authentication import TokenAuthentication
from pms.models import *
from pms.serializers import *
from django.conf import settings
from pagination import *
from rest_framework import filters
from datetime import datetime,timedelta
import collections
from rest_framework.exceptions import APIException
from django_filters.rest_framework import DjangoFilterBackend
from master.serializers import UserModuleWiseListSerializer
from master.models import TMasterModuleRole
from users.models import TCoreUserDetail
from custom_decorator import *
from rest_framework.parsers import FileUploadParser
import os
from pms.custom_filter import *
from custom_decorator import *
from decimal import *
from django.db.models import Q
from global_function import userdetails,getHostWithPort,send_mail
from django.contrib.auth.models import User


'''
    For Knox 
    Author : Rupam Hazra
    Date : 16.03.2020
'''
from knox.auth import TokenAuthentication
from rest_framework import permissions
from knox.models import AuthToken


class TourAndTravelExpenseAddView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsTourAndTravelExpenseMaster.objects.filter(is_deleted=False)
    serializer_class = TourAndTravelExpenseAddSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('employee','guest','id')
    # from rest_framework.parsers import MultiPartParser, FormParser
    # parser_classes = [MultiPartParser,FormParser]
    @response_modify_decorator_get_after_execution
    def get(self, request, *args, **kwargs):
        response=super(TourAndTravelExpenseAddView,self).get(self, request, args, kwargs)
        # print('response',response.data)
        # daily_ex = self.kwargs['daily_expenses']
        # print(daily_ex)
        # print(daily_ex[0]['added_docs'])
        doc_flag = self.request.query_params.get('doc_flag',None)
        for data in response.data:
            # print('dd',data['id'])
            daily_expenses=PmsTourAndTravelEmployeeDailyExpenses.objects.filter(expenses_master=data['id'],is_deleted=False)
            daily_expenses_list=[]
            for d_e in daily_expenses:

                if doc_flag:
                    doc = TravelEmployeeDocument.objects.filter(tour_and_travel_session_id=d_e.id,
                                                                type='daily').values_list('document', flat=True)
                    temp_lst = list()
                    for each in list(doc):
                        doc_dict = {}
                        doc_dict['document'] = getHostWithPort(request,True) + each
                        temp_lst.append(doc_dict)

                    doc = temp_lst
                else:
                    doc = TravelEmployeeDocument.objects.filter(tour_and_travel_session_id=d_e.id,
                                                                type='daily').values_list('document', flat=True)
                    # print(doc)
                    doc = list(map(lambda x: getHostWithPort(request,True) + x, doc))
                    # .replace("tour_and_travel_expense_add", "media")



                daily_travel={
                    'id':d_e.id,
                    'date':d_e.date,
                    'description':d_e.description,
                    'fare':d_e.fare,
                    'local_conveyance':d_e.local_conveyance,
                    'lodging_expenses':d_e.lodging_expenses,
                    'fooding_expenses':d_e.fooding_expenses,
                    'da':d_e.da,
                    'other_expenses':d_e.other_expenses,
                    'documents':doc
                }
                daily_expenses_list.append(daily_travel)
            data['daily_expenses']=daily_expenses_list
            vendor_or_emp_det=PmsTourAndTravelVendorOrEmployeeDetails.objects.filter(expenses_master=data['id'],is_deleted=False)
            emp_det_list=[]
            if vendor_or_emp_det:
                for e_d in vendor_or_emp_det:
                    if e_d.employee_or_vendor_type ==1:
                        vendor_name = PmsExternalUsers.objects.filter(id=e_d.empolyee_or_vendor_id,is_deleted=False).values('contact_person_name')
                        if vendor_name:
                            name=vendor_name[0]['contact_person_name']
                            # print("e_d.employee_or_vendor_type",name)
                    else:
                        name=userdetails(e_d.empolyee_or_vendor_id)
                        # print('name_1',name)
                    # doc = TravelEmployeeDocument.objects.filter(tour_and_travel_session_id=e_d.id, type='vendor').values_list('document', flat=True)
                    # print(doc)
                    # doc = list(map(lambda x: request.build_absolute_uri(x), doc))
                    if doc_flag:
                        doc = TravelEmployeeDocument.objects.filter(tour_and_travel_session_id=e_d.id,
                                                                    type='vendor').values_list('document', flat=True)
                        temp_lst = list()
                        for each in list(doc):
                            doc_dict = {}
                            doc_dict['document'] = getHostWithPort(request,True) + each
                            temp_lst.append(doc_dict)

                        doc = temp_lst

                        # doc = doc_dict
                    else:
                        doc = TravelEmployeeDocument.objects.filter(tour_and_travel_session_id=e_d.id,
                                                                    type='vendor').values_list('document', flat=True)
                        # print(doc)
                        # print(doc)
                        doc = list(map(lambda x: getHostWithPort(request, True) + x, doc))
                        # .replace("tour_and_travel_expense_add", "media")
                    employee_details={
                        'id':e_d.id,
                        'bill_number':e_d.bill_number,
                        'employee_or_vendor_type':e_d.employee_or_vendor_type,
                        'empolyee_or_vendor_id':e_d.empolyee_or_vendor_id,
                        'bill_amount':e_d.bill_amount,
                        'advance_amount':e_d.advance_amount,
                        'empolyee_or_vendor_name':name,
                        'documents': doc
                    }
                
                    emp_det_list.append(employee_details)
            data['vendor_or_employee_details']=emp_det_list
            bill_received=PmsTourAndTravelBillReceived.objects.filter(expenses_master=data['id'],is_deleted=False)
            bill_received_list=[]
            if bill_received:
                for b_r in bill_received:
                    if b_r.employee_or_vendor_type ==1:
                        vendor_name = PmsExternalUsers.objects.filter(id=b_r.empolyee_or_vendor_id,is_deleted=False).values('contact_person_name')
                        if vendor_name:
                            name=vendor_name[0]['contact_person_name']
                            # print("b_r.employee_or_vendor_type",name)
                    
                    else:
                        name=userdetails(b_r.empolyee_or_vendor_id)
                        # print('name_2',name)
                    # doc = TravelEmployeeDocument.objects.filter(tour_and_travel_session_id=b_r.id, type='bill').values_list(
                    #     'document', flat=True)
                    # doc = list(map(lambda x: request.build_absolute_uri(x), doc))
                    # print(doc)
                    if doc_flag:
                        doc = TravelEmployeeDocument.objects.filter(tour_and_travel_session_id=b_r.id,
                                                                    type='bill').values_list('document', flat=True)
                        temp_lst = list()
                        for each in list(doc):
                            doc_dict = {}
                            doc_dict['document'] = getHostWithPort(request, True) + each
                            temp_lst.append(doc_dict)

                        doc = temp_lst
                    else:
                        doc = TravelEmployeeDocument.objects.filter(tour_and_travel_session_id=b_r.id,
                                                                    type='bill').values_list('document', flat=True)
                        # print(doc)
                        doc = list(map(lambda x: getHostWithPort(request, True) + x, doc))
                        # .replace("tour_and_travel_expense_add", "media")
                    bill_details={
                        'id':b_r.id,
                        'date':b_r.date,
                        'parking_expense':b_r.parking_expense,
                        'posting_expense':b_r.posting_expense,
                        'employee_or_vendor_type':b_r.employee_or_vendor_type,
                        'empolyee_or_vendor_id':b_r.empolyee_or_vendor_id,
                        'empolyee_or_vendor_name':name,
                        'less_amount':b_r.less_amount,
                        'cgst':b_r.cgst,
                        'sgst':b_r.sgst,
                        'igst':b_r.igst,
                        'document_number':b_r.document_number,
                        'cost_center_number':b_r.cost_center_number,
                        'net_expenditure':b_r.net_expenditure,
                        'advance_amount':b_r.advance_amount,
                        'fare_and_conveyance':b_r.fare_and_conveyance,
                        'lodging_fooding_and_da':b_r.lodging_fooding_and_da,
                        'expense_mans_per_day':b_r.expense_mans_per_day,
                        'total_expense':b_r.total_expense,
                        'limit_exceeded_by':b_r.limit_exceeded_by,
                        'remarks':b_r.remarks,
                        'documents': doc
                    }
                    bill_received_list.append(bill_details)
            data['bill_received']=bill_received_list
            flight_booking=PmsTourAndTravelWorkSheetFlightBookingQuotation.objects.filter(expenses_master=data['id'],is_deleted=False)
            flight_booking_list=[]
            if flight_booking:
                for f_b in flight_booking:
                    # doc = TravelEmployeeDocument.objects.filter(tour_and_travel_session_id=f_b.id, type__in=['flightonward','flightreturn']).values_list(
                    #     'document', flat=True)
                    # print(doc)
                    # doc = list(map(lambda x: request.build_absolute_uri(x), doc))
                    if doc_flag:
                        doc = TravelEmployeeDocument.objects.filter(tour_and_travel_session_id=f_b.id,
                                                                    type__in=['flightonward','flightreturn']).values_list('document', flat=True)
                        temp_lst = list()
                        for each in list(doc):
                            doc_dict = {}
                            doc_dict['document'] = getHostWithPort(request,True) + each
                            temp_lst.append(doc_dict)

                        doc = temp_lst
                    else:
                        doc = TravelEmployeeDocument.objects.filter(tour_and_travel_session_id=f_b.id,
                                                                    type__in=['flightonward','flightreturn']).values_list('document', flat=True)
                        # print(doc)
                        doc = list(map(lambda x: getHostWithPort(request, True) + x, doc))
                        # .replace("tour_and_travel_expense_add", "media")
                    flight_booking_details={
                        'id':f_b.id,
                        'flight_booking_quotation_type':f_b.flight_booking_quotation_type,
                        'date':f_b.date,
                        'sector':f_b.sector,
                        'airline':f_b.airline,
                        'flight_number':f_b.flight_number,
                        'time':f_b.time,
                        'corporate_fare_agent_1':f_b.corporate_fare_agent_1,
                        'corporate_fare_agent_2':f_b.corporate_fare_agent_2,
                        'retail_fare_agent_1':f_b.retail_fare_agent_1,
                        'retail_fare_agent_2':f_b.retail_fare_agent_2,
                        'airline_fare':f_b.airline_fare,
                        'others':f_b.others,
                        'documents': doc
                    }
                    flight_booking_list.append(flight_booking_details)
            data['flight_booking_quotation']=flight_booking_list
            final_booking_details=PmsTourAndTravelFinalBookingDetails.objects.filter(expenses_master=data['id'],is_deleted=False)
            final_booking_list=[]
            if final_booking_details:
                for f_b_d in final_booking_details:
                    if f_b_d.employee_or_vendor_type ==1:
                        vendor_name = PmsExternalUsers.objects.filter(id=f_b_d.empolyee_or_vendor_id,is_deleted=False).values('contact_person_name')
                        if vendor_name:
                            name=vendor_name[0]['contact_person_name']
                            # print("f_b_d.employee_or_vendor_type",name)
                    
                    else:
                        name=userdetails(f_b_d.empolyee_or_vendor_id)
                        # print('name_3',name)
                    # doc = TravelEmployeeDocument.objects.filter(tour_and_travel_session_id=f_b_d.id, type='final').values_list(
                    #     'document', flat=True)
                    # print(doc)
                    # doc = list(map(lambda x: request.build_absolute_uri(x), doc))
                    if doc_flag:
                        doc = TravelEmployeeDocument.objects.filter(tour_and_travel_session_id=f_b_d.id,
                                                                    type='final').values_list('document', flat=True)
                        temp_lst = list()
                        for each in list(doc):
                            doc_dict = {}
                            doc_dict['document'] = getHostWithPort(request,True) + each
                            temp_lst.append(doc_dict)

                        doc = temp_lst
                    else:
                        doc = TravelEmployeeDocument.objects.filter(tour_and_travel_session_id=f_b_d.id,
                                                                    type='final').values_list('document', flat=True)
                        # print(doc)
                        doc = list(map(lambda x: getHostWithPort(request, True) + x, doc))
                        # .replace("tour_and_travel_expense_add", "media")
                    final_booking={
                        'id':f_b_d.id,
                        'employee_or_vendor_type':f_b_d.employee_or_vendor_type,
                        'empolyee_or_vendor_id':f_b_d.empolyee_or_vendor_id,
                        'empolyee_or_vendor_name':name,
                        'date_of_journey':f_b_d.date_of_journey,
                        'time':f_b_d.time,
                        'flight_no':f_b_d.flight_no,
                        'travel_sector':f_b_d.travel_sector,
                        'number_of_persons':f_b_d.number_of_persons,
                        'rate_per_person':f_b_d.rate_per_person,
                        'total_cost':f_b_d.total_cost,
                        'documents': doc
                    }
                    final_booking_list.append(final_booking)
            data['final_booking_details']=final_booking_list
                
        return response    

class TourAndTravelVendorOrEmployeeDetailsApprovalView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsTourAndTravelVendorOrEmployeeDetails.objects.filter(is_deleted=False)
    serializer_class = TourAndTravelVendorOrEmployeeDetailsApprovalSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('expenses_master','employee_or_vendor_type')
    # @response_modify_decorator_get
    @response_modify_decorator_get_after_execution
    def get(self, request, *args, **kwargs):
        response=super(TourAndTravelVendorOrEmployeeDetailsApprovalView,self).get(self, request, args, kwargs)
        response_dict={}

        if response.data:
           
            response.data=response.data[0]
            response_dict={
                'expenses_master':response.data['expenses_master'],
                'approved_status':response.data['approved_status'],
                'request_modification':response.data['request_modification'],
                'updated_by':response.data['updated_by']

            }
        
        return Response(response_dict)

class TourAndTravelBillReceivedApprovalView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsTourAndTravelBillReceived.objects.filter(is_deleted=False)
    serializer_class = TourAndTravelBillReceivedApprovalSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('expenses_master','employee_or_vendor_type')
    @response_modify_decorator_get_after_execution
    def get(self, request, *args, **kwargs):
        response=super(TourAndTravelBillReceivedApprovalView,self).get(self, request, args, kwargs)
        response_dict={}

        if response.data:
           
            response.data=response.data[0]
            response_dict={
                'expenses_master':response.data['expenses_master'],
                'approved_status':response.data['approved_status'],
                'request_modification':response.data['request_modification'],
                'updated_by':response.data['updated_by']

            }
        
        return Response(response_dict)
class TourAndTravelFinalBookingDetailsApprovalView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsTourAndTravelFinalBookingDetails.objects.filter(is_deleted=False)
    serializer_class =TourAndTravelFinalBookingDetailsApprovalSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('expenses_master','employee_or_vendor_type')
    @response_modify_decorator_get_after_execution
    def get(self, request, *args, **kwargs):
        response=super(TourAndTravelFinalBookingDetailsApprovalView,self).get(self, request, args, kwargs)
        response_dict={}

        if response.data:
           
            response.data=response.data[0]
            response_dict={
                'expenses_master':response.data['expenses_master'],
                'approved_status':response.data['approved_status'],
                'request_modification':response.data['request_modification'],
                'updated_by':response.data['updated_by']

            }
        
        return Response(response_dict)

class TourAndTravelExpenseMasterApprovalView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsTourAndTravelExpenseMaster.objects.filter(is_deleted=False)
    serializer_class =TourAndTravelExpenseMasterApprovalSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('user_type',)
    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        return response

class TourAndTravelExpenseApprovalList(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    pagination_class = CSPageNumberPagination
    queryset = PmsTourAndTravelExpenseMaster.objects.filter(is_deleted=False).order_by('-id')
    serializer_class = TourAndTravelExpenseApprovalListSerializer

    def get_queryset(self):
        filter = {}
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        from_expense_range=self.request.query_params.get('from_expense_range', None)
        expense_range_to=self.request.query_params.get('expense_range_to', None)
        from_limit_exceeded_range=self.request.query_params.get('from_limit_exceeded_range', None)
        limit_exceeded_range_to=self.request.query_params.get('limit_exceeded_range_to', None)
        search=self.request.query_params.get('search', None)

        field_name=self.request.query_params.get('field_name',None)
        order_by=self.request.query_params.get('order_by',None)

        if field_name and order_by:
            if field_name == 'from_date' and order_by == 'asc':
                return self.queryset.filter(is_deleted=False).order_by('from_date')
            elif field_name == 'from_date' and order_by == 'desc':
                return self.queryset.filter(is_deleted=False).order_by('-from_date')
            elif field_name == 'to_date' and order_by == 'asc':
                return self.queryset.filter(is_deleted=False).order_by('to_date')
            elif field_name == 'to_date' and order_by == 'desc':
                return self.queryset.filter(is_deleted=False).order_by('-to_date')
            elif field_name == 'total_expense' and order_by == 'asc':
                return self.queryset.filter(is_deleted=False).order_by('total_expense')
            elif field_name == 'total_expense' and order_by == 'desc':
                return self.queryset.filter(is_deleted=False).order_by('-total_expense')
            elif field_name == 'limit_exceed_by' and order_by == 'asc':
                return self.queryset.filter(is_deleted=False).order_by('limit_exceed_by')
            elif field_name == 'limit_exceed_by' and order_by == 'desc':
                return self.queryset.filter(is_deleted=False).order_by('-limit_exceed_by')
            elif field_name == 'total_flight_fare' and order_by == 'asc':
                return self.queryset.filter(is_deleted=False).order_by('total_flight_fare')
            elif field_name == 'total_flight_fare' and order_by == 'desc':
                return self.queryset.filter(is_deleted=False).order_by('-total_flight_fare')
            elif field_name == 'advance' and order_by == 'asc':
                return self.queryset.filter(is_deleted=False).order_by('advance')
            elif field_name == 'advance' and order_by == 'desc':
                return self.queryset.filter(is_deleted=False).order_by('-advance')

        if start_date and end_date :
            start_object = datetime.strptime(start_date, '%Y-%m-%d').date()
            filter['from_date__gte'] = start_object
            end_object = datetime.strptime(end_date, '%Y-%m-%d').date()+ timedelta(days=1)
            filter['to_date__lte'] = end_object    
          
        if from_expense_range and expense_range_to:
            filter['total_expense__range']=(from_expense_range,expense_range_to)

        if from_limit_exceeded_range and limit_exceeded_range_to:
            filter['limit_exceed_by__range']=(from_limit_exceeded_range,limit_exceeded_range_to)

        if search:
            queryset_all = PmsTourAndTravelExpenseMaster.objects.none()
            g_query=self.queryset.filter(guest__icontains=search,is_deleted=False)
            queryset_all=(queryset_all|g_query)
            name=search.split(" ")
            # print('name',name)                                                                                                                                                                                                                                                                            
            if name:
                for i in name:
                    queryset = self.queryset.filter(Q(is_deleted=False) & Q(employee__first_name__icontains=i) |
                                                    Q(employee__last_name__icontains=i)).order_by('-id')
                    queryset_all = (queryset_all|queryset)

            return queryset_all

        if filter:
            queryset = self.queryset.filter(**filter)
            # print('queryset',queryset)
            return queryset

        else:
            queryset = self.queryset.filter(is_deleted=False)
            return queryset
    
    def get(self, request, *args, **kwargs):
        response = super(TourAndTravelExpenseApprovalList, self).get(self, request, args, kwargs)
        # print("response.data",response.data)
        for data in response.data['results']:   
            if data['employee'] and data['user_type'] == 1:
                first_name = User.objects.only('first_name').get(id=data['employee']).first_name
                last_name = User.objects.only('last_name').get(id=data['employee']).last_name
                data['name'] = {
                    'id': data['employee'],
                    'name' : str(first_name) + " " + str(last_name)
                }
            if data['user_type'] == 2:
                data['name'] = {
                    'id': "",
                    'name' : data['guest']
                }        
        if response.data['count'] > 0:
            response.data['request_status'] = 0
            response.data['msg'] = settings.MSG_SUCCESS
        else:
            response.data['request_status'] = 1
            response.data['msg'] = settings.MSG_NO_DATA

        return response


class UserTourAndTravelExpenseApprovalList(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    pagination_class = CSPageNumberPagination
    queryset = PmsTourAndTravelExpenseMaster.objects.filter(is_deleted=False).order_by('-id')
    serializer_class = TourAndTravelExpenseApprovalListSerializer

    def get_queryset(self):
        filter = {}
        logged_in_user = self.request.user.id
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        from_expense_range = self.request.query_params.get('from_expense_range', None)
        expense_range_to = self.request.query_params.get('expense_range_to', None)
        from_limit_exceeded_range = self.request.query_params.get('from_limit_exceeded_range', None)
        limit_exceeded_range_to = self.request.query_params.get('limit_exceeded_range_to', None)
        search = self.request.query_params.get('search', None)
        user = self.request.query_params.get('user', None)

        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)
        order = '-id'
        if field_name and order_by:
            if field_name == 'from_date' and order_by == 'asc':
                order = 'from_date'
                # return self.queryset.filter(is_deleted=False).order_by('from_date')
            elif field_name == 'from_date' and order_by == 'desc':
                order = '-from_date'
                # return self.queryset.filter(is_deleted=False).order_by('-from_date')
            elif field_name == 'to_date' and order_by == 'asc':
                order = 'to_date'
                # return self.queryset.filter(is_deleted=False).order_by('to_date')
            elif field_name == 'to_date' and order_by == 'desc':
                order = '-to_date'
                # return self.queryset.filter(is_deleted=False).order_by('-to_date')
            elif field_name == 'total_expense' and order_by == 'asc':
                order = 'total_expense'
                # return self.queryset.filter(is_deleted=False).order_by('total_expense')
            elif field_name == 'total_expense' and order_by == 'desc':
                order = '-total_expense'
                # return self.queryset.filter(is_deleted=False).order_by('-total_expense')
            elif field_name == 'limit_exceed_by' and order_by == 'asc':
                order = 'limit_exceed_by'
                # return self.queryset.filter(is_deleted=False).order_by('limit_exceed_by')
            elif field_name == 'limit_exceed_by' and order_by == 'desc':
                order = '-limit_exceed_by'
                # return self.queryset.filter(is_deleted=False).order_by('-limit_exceed_by')
            elif field_name == 'total_flight_fare' and order_by == 'asc':
                order = 'total_flight_fare'
                # return self.queryset.filter(is_deleted=False).order_by('total_flight_fare')
            elif field_name == 'total_flight_fare' and order_by == 'desc':
                order = '-total_flight_fare'
                # return self.queryset.filter(is_deleted=False).order_by('-total_flight_fare')
            elif field_name == 'advance' and order_by == 'asc':
                order = 'advance'
                # return self.queryset.filter(is_deleted=False).order_by('advance')
            elif field_name == 'advance' and order_by == 'desc':
                order = '-advance'
                # return self.queryset.filter(is_deleted=False).order_by('-advance')

        if start_date and end_date:
            start_object = datetime.strptime(start_date, '%Y-%m-%d').date()
            filter['from_date__gte'] = start_object
            end_object = datetime.strptime(end_date, '%Y-%m-%d').date() + timedelta(days=1)
            filter['to_date__lte'] = end_object

        if from_expense_range and expense_range_to:
            filter['total_expense__range'] = (from_expense_range, expense_range_to)

        if from_limit_exceeded_range and limit_exceeded_range_to:
            filter['limit_exceed_by__range'] = (from_limit_exceeded_range, limit_exceeded_range_to)

        if search:
            queryset_all = PmsTourAndTravelExpenseMaster.objects.none()
            g_query = self.queryset.filter(guest__icontains=search, is_deleted=False)
            queryset_all = (queryset_all | g_query)
            name = search.split(" ")
            # print('name',name)
            if name:
                for i in name:
                    queryset = self.queryset.filter(Q(is_deleted=False) & Q(employee__first_name__icontains=i) |
                                                    Q(employee__last_name__icontains=i)).order_by('-id')
                    queryset_all = (queryset_all | queryset)

            return queryset_all

        if filter:
            if user:
                queryset = self.queryset.filter(**filter, employee__id=user).order_by(order)
            else:
                queryset = self.queryset.filter(**filter, employee__id=logged_in_user).order_by(order)

            # print('queryset',queryset)
            return queryset

        else:
            if user:
                queryset = self.queryset.filter(employee__id=user,is_deleted=False).order_by(order)
            else:
                queryset = self.queryset.filter(employee__id=logged_in_user,is_deleted=False).order_by(order)
            return queryset

    def get(self, request, *args, **kwargs):
        response = super(UserTourAndTravelExpenseApprovalList, self).get(self, request, args, kwargs)
        # print("response.data",response.data)
        for data in response.data['results']:
            if data['employee'] and data['user_type'] == 1:
                first_name = User.objects.only('first_name').get(id=data['employee']).first_name
                last_name = User.objects.only('last_name').get(id=data['employee']).last_name
                data['name'] = {
                    'id': data['employee'],
                    'name': str(first_name) + " " + str(last_name)
                }
            if data['user_type'] == 2:
                data['name'] = {
                    'id': "",
                    'name': data['guest']
                }
        if response.data['count'] > 0:
            response.data['request_status'] = 0
            response.data['msg'] = settings.MSG_SUCCESS
        else:
            response.data['request_status'] = 1
            response.data['msg'] = settings.MSG_NO_DATA

        return response


class UserTourAndTravelExpenseReportDownload(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    # pagination_class = CSPageNumberPagination
    queryset = PmsTourAndTravelExpenseMaster.objects.filter(is_deleted=False).order_by('-id')
    serializer_class = EmployeeTourAndTravelExpenseListSerializer

    def get_queryset(self):
        filter = {}
        logged_in_user = self.request.user.id
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        from_expense_range = self.request.query_params.get('from_expense_range', None)
        expense_range_to = self.request.query_params.get('expense_range_to', None)
        from_limit_exceeded_range = self.request.query_params.get('from_limit_exceeded_range', None)
        limit_exceeded_range_to = self.request.query_params.get('limit_exceeded_range_to', None)
        search = self.request.query_params.get('search', None)
        user = self.request.query_params.get('user', None)

        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)

        order = '-id'
        if field_name and order_by:
            if field_name == 'from_date' and order_by == 'asc':
                order = 'from_date'
                # return self.queryset.filter(is_deleted=False).order_by('from_date')
            elif field_name == 'from_date' and order_by == 'desc':
                order = 'from_date'
                # return self.queryset.filter(is_deleted=False).order_by('-from_date')
            elif field_name == 'to_date' and order_by == 'asc':
                order = 'to_date'
                # return self.queryset.filter(is_deleted=False).order_by('to_date')
            elif field_name == 'to_date' and order_by == 'desc':
                order = '-to_date'
                # return self.queryset.filter(is_deleted=False).order_by('-to_date')
            elif field_name == 'total_expense' and order_by == 'asc':
                order = 'total_expense'
                # return self.queryset.filter(is_deleted=False).order_by('total_expense')
            elif field_name == 'total_expense' and order_by == 'desc':
                order = '-total_expense'
                # return self.queryset.filter(is_deleted=False).order_by('-total_expense')
            elif field_name == 'limit_exceed_by' and order_by == 'asc':
                order = 'limit_exceed_by'
                # return self.queryset.filter(is_deleted=False).order_by('limit_exceed_by')
            elif field_name == 'limit_exceed_by' and order_by == 'desc':
                order = '-limit_exceed_by'
                # return self.queryset.filter(is_deleted=False).order_by('-limit_exceed_by')
            elif field_name == 'total_flight_fare' and order_by == 'asc':
                order = 'total_flight_fare'
                # return self.queryset.filter(is_deleted=False).order_by('total_flight_fare')
            elif field_name == 'total_flight_fare' and order_by == 'desc':
                order = '-total_flight_fare'
                # return self.queryset.filter(is_deleted=False).order_by('-total_flight_fare')
            elif field_name == 'advance' and order_by == 'asc':
                order = 'advance'
                # return self.queryset.filter(is_deleted=False).order_by('advance')
            elif field_name == 'advance' and order_by == 'desc':
                order = '-advance'
                # return self.queryset.filter(is_deleted=False).order_by('-advance')

        if start_date and end_date:
            start_object = datetime.strptime(start_date, '%Y-%m-%d').date()
            filter['from_date__gte'] = start_object
            end_object = datetime.strptime(end_date, '%Y-%m-%d').date() + timedelta(days=1)
            filter['to_date__lte'] = end_object

        if from_expense_range and expense_range_to:
            filter['total_expense__range'] = (from_expense_range, expense_range_to)

        if from_limit_exceeded_range and limit_exceeded_range_to:
            filter['limit_exceed_by__range'] = (from_limit_exceeded_range, limit_exceeded_range_to)

        if search:
            queryset_all = PmsTourAndTravelExpenseMaster.objects.none()
            g_query = self.queryset.filter(guest__icontains=search, is_deleted=False)
            queryset_all = (queryset_all | g_query)
            name = search.split(" ")
            # print('name',name)
            if name:
                for i in name:
                    queryset = self.queryset.filter(Q(is_deleted=False) & Q(employee__first_name__icontains=i) |
                                                    Q(employee__last_name__icontains=i)).order_by('-id')
                    queryset_all = (queryset_all | queryset)

            return queryset_all

        if filter:
            if user:
                queryset = self.queryset.filter(**filter, employee__id=user).order_by(order)
            else:
                queryset = self.queryset.filter(**filter,employee__id=logged_in_user).order_by(order)

            # print('queryset',queryset)
            return queryset

        else:
            if user:
                queryset = self.queryset.filter(employee__id=user,is_deleted=False).order_by(order)
            else:
                queryset = self.queryset.filter(employee__id=logged_in_user,is_deleted=False).order_by(order)
            return queryset

    def get(self, request, *args, **kwargs):
        response = super(UserTourAndTravelExpenseReportDownload, self).get(self, request, args, kwargs)
        # print("response.data",response.data)
        for data in response.data:
            if data['employee'] and data['user_type'] == 1:
                first_name = User.objects.only('first_name').get(id=data['employee']).first_name
                last_name = User.objects.only('last_name').get(id=data['employee']).last_name
                data['user_type']= 'employee'
                data['name'] = str(first_name) + " " + str(last_name)
                #     'id': data['employee'],
                #     'name': str(first_name) + " " + str(last_name)
                # }
            if data['user_type'] == 2:
                data['user_type'] = 'guest'
                data['name'] = data['guest']
                    # 'id': "",
                    # 'name': data['guest']
                # }
            data['employee'] = User.objects.get(id=data['employee']).get_full_name()
        if len(response.data):
            df_report = pd.DataFrame.from_records(response.data)
            # print(dict(df_report)['results'])
            # print(df_report[['employee','user_type']])
            df_report = df_report[['user_type','employee','guest','place_of_travel','total_expense','limit_exceed_by','total_flight_fare','advance','from_date','to_date','approved_status','project_manager_approval_status','site_coordinator_approval_status','HO_status','accounts_approval_status']]
            # df_report = df_report[['employee','user_type','name','place_of_travel','total_expense','limit_exceed_by','total_flight_fare','advance','from_date','from_date','approved_status']]
            file_path = settings.MEDIA_ROOT_EXPORT + self.create_file_path()
            df_report.to_excel(file_path,index=None,header=['User Type','Employee','Guest','place of Travel','Total Expense','Limit Exceed By','Total Flight Fare','Advance','From_Date','To_Date','Approved Status','Project Manager Approval Status','Site Coordinator Approval Status','HO Approval Status','Accounts Approval Status'])
            file_name = self.create_file_path()
            url = getHostWithPort(request) + file_name if file_name else None
            return Response({'request_status':1,'msg':'Success', 'url': url})
        else:
            return Response({'request_status':0,'msg':'Data Not Found'})

    def create_file_path(self):
        if os.path.isdir('media/pms'):
            file_name = 'media/pms/employee_tour_and_travel_report.xlsx'
        else:
            os.makedirs('media/pms')
            file_name = 'media/pms/employee_tour_and_travel_report.xlsx'
        return file_name


class TourAndTravelDocumentEditView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    def post(self, request, *args, **kwargs):
        # print(kwargs)
        document_dict = dict(request.data)
        expenses = list(document_dict.keys())
        print(expenses)
        # daily = list(filter(lambda x: x if 'daily' in x else None, document_dict.keys()))
        # print(daily)
        # vendor = list(filter(lambda x: x if 'vendor' in x else None, document_dict.keys()))
        # bill = list(filter(lambda x: x if 'bill' in x else None, document_dict.keys()))
        # daily_expenses_id = []
        # for each in daily:
        #     daily_expenses_id.append(each.split('_')[-1])
        # # daily_expenses_id = set(list(filter(lambda x: x.split('_')[2], daily)))
        # daily_expenses_id = list(set(daily_expenses_id))
        # print(daily_expenses_id)
        # vendor_id = []
        # for each in vendor:
        #     vendor_id.append(each.split('_')[-1])
        # print(vendor_id)
        # bill_id = []
        # for each in bill:
        #     bill_id.append(each.split('_')[-1])
        # print(bill_id)
        # daily expenses document add
        if expenses:
            for each in expenses:
                splited_doc = each.split('_')
                print(splited_doc)
                # daily_obj = PmsTourAndTravelEmployeeDailyExpenses.objects.get(id=splited_doc[-1])
                # print(daily_obj)
                '''Tour and Travel Document add
                    Writen_by:Swarup Adhikary'''
                Travel_doc_obj = TravelEmployeeDocument.objects.create(tour_and_travel_session_id=int(splited_doc[-1]),type=splited_doc[0])
                print(Travel_doc_obj)
                Travel_doc_obj = TravelEmployeeDocument.objects.latest('id')

                document= request.FILES[each]
                print(document)
                if document:
                    print("in local")
                    Travel_doc_obj.document = document
                Travel_doc_obj.save()
                #
                # local_conveyance_document = request.FILES[
                #     'daily_local_conveyance_document_' + str(each)] if 'daily_local_conveyance_document_' + str(
                #     each) in daily else None
                # if local_conveyance_document:
                #     print("in local")
                #     pms_daily_doc_obj.local_conveyance_document = local_conveyance_document
                #
                # lodging_expenses_document = request.FILES[
                #     'daily_lodging_expenses_document_' + str(each)] if 'daily_lodging_expenses_document_' + str(
                #     each) in daily else None
                # if local_conveyance_document:
                #     print("in local")
                #     pms_daily_doc_obj.lodging_expenses_document = lodging_expenses_document
                #
                # fooding_expenses_document = request.FILES[
                #     'daily_fooding_expenses_document_' + str(each)] if 'daily_fooding_expenses_document_' + str(
                #     each) in daily else None
                # if fooding_expenses_document:
                #     print("in local")
                #     pms_daily_doc_obj.fooding_expenses_document = fooding_expenses_document
                #
                # da_document = request.FILES[
                #     'daily_da_document_' + str(each)] if 'daily_da_document_' + str(
                #     each) in daily else None
                # if da_document:
                #     print("in local")
                #     pms_daily_doc_obj.da_document = da_document
                # other_expenses_document = request.FILES[
                #     'daily_other_expenses_document_' + str(each)] if 'daily_other_expenses_document_' + str(
                #     each) in daily else None
                # if other_expenses_document:
                #     print("in local")
                #     pms_daily_doc_obj.other_expenses_document = other_expenses_document
                # pms_daily_doc_obj.save()


        # # vendor document add
        # if vendor_id:
        #     for each in vendor_id:
        #         vendor_obj = PmsTourAndTravelVendorOrEmployeeDetails.objects.get(id=each)
        #         print(vendor_obj)
        #         pms_vendor_doc_obj = PmsTourAndTravelVendorOrEmployeeDetailsDocument.objects.create(
        #             pms_vendor=vendor_obj)
        #         print(pms_vendor_doc_obj)
        #         pms_vendor_doc_obj = PmsTourAndTravelVendorOrEmployeeDetailsDocument.objects.latest('id')
        #
        #         document = request.FILES['vendor_document_' + str(each)] if 'vendor_document_' + str(
        #             each) in vendor else None
        #         print(document)
        #         if document:
        #             print("in local")
        #             pms_vendor_doc_obj.document = document
        #             pms_vendor_doc_obj.save()
        #
        # # bill received document add
        # if bill_id:
        #     pass




        print("saved")
        # print(args)
        return Response({
                         'msg': 'Documents are added successfully',
                         "request_status": 1})


# tour and travel expense listing
class TourAndTravelExpenseList(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    pagination_class = CSPageNumberPagination
    queryset = PmsTourAndTravelExpenseMaster.objects.filter(is_deleted=False).order_by('-id')
    serializer_class = TourAndTravelApprovalListSerializer

    def get_queryset(self):
        filter = {}
        approval_level = self.request.query_params.get('approval_level', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        from_expense_range = self.request.query_params.get('from_expense_range', None)
        expense_range_to = self.request.query_params.get('expense_range_to', None)
        from_limit_exceeded_range = self.request.query_params.get('from_limit_exceeded_range', None)
        limit_exceeded_range_to = self.request.query_params.get('limit_exceeded_range_to', None)
        search = self.request.query_params.get('search', None)
        project = self.request.query_params.get('project', None)
        employee = self.request.query_params.get('employee', None)

        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)

        order = '-id'
        if field_name and order_by:
            if field_name == 'from_date' and order_by == 'asc':
                order = 'from_date'
                # return self.queryset.filter(is_deleted=False).order_by('from_date')
            elif field_name == 'from_date' and order_by == 'desc':
                order = '-from_date'
                # return self.queryset.filter(is_deleted=False).order_by('-from_date')
            elif field_name == 'to_date' and order_by == 'asc':
                order = 'to_date'
                # return self.queryset.filter(is_deleted=False).order_by('to_date')
            elif field_name == 'to_date' and order_by == 'desc':
                order = '-to_date'
                # return self.queryset.filter(is_deleted=False).order_by('-to_date')
            elif field_name == 'total_expense' and order_by == 'asc':
                order = 'total_expense'
                # return self.queryset.filter(is_deleted=False).order_by('total_expense')
            elif field_name == 'total_expense' and order_by == 'desc':
                order = '-total_expense'
                # return self.queryset.filter(is_deleted=False).order_by('-total_expense')
            elif field_name == 'limit_exceed_by' and order_by == 'asc':
                order = 'limit_exceed_by'
                # return self.queryset.filter(is_deleted=False).order_by('limit_exceed_by')
            elif field_name == 'limit_exceed_by' and order_by == 'desc':
                order = '-limit_exceed_by'
                # return self.queryset.filter(is_deleted=False).order_by('-limit_exceed_by')
            elif field_name == 'total_flight_fare' and order_by == 'asc':
                order = 'total_flight_fare'
                # return self.queryset.filter(is_deleted=False).order_by('total_flight_fare')
            elif field_name == 'total_flight_fare' and order_by == 'desc':
                order = '-total_flight_fare'
                # return self.queryset.filter(is_deleted=False).order_by('-total_flight_fare')
            elif field_name == 'advance' and order_by == 'asc':
                order = 'advance'
                # return self.queryset.filter(is_deleted=False).order_by('advance')
            elif field_name == 'advance' and order_by == 'desc':
                order = '-advance'
                # return self.queryset.filter(is_deleted=False).order_by('-advance')
        if project:
            filter['project__id'] = project
        if employee:
            filter['employee__id'] = employee


        if start_date and end_date:
            start_object = datetime.strptime(start_date, '%Y-%m-%d').date()
            filter['from_date__gte'] = start_object
            end_object = datetime.strptime(end_date, '%Y-%m-%d').date() + timedelta(days=1)
            filter['to_date__lte'] = end_object

        if from_expense_range and expense_range_to:
            filter['total_expense__range'] = (from_expense_range, expense_range_to)

        if from_limit_exceeded_range and limit_exceeded_range_to:
            filter['limit_exceed_by__range'] = (from_limit_exceeded_range, limit_exceeded_range_to)

        if approval_level:
            if approval_level == "project_manager":
                print("in if statement")
                queryset = self.queryset.filter(project__project_manager__id=self.request.user.id,
                                     status="Pending For Project Manager Approval",current_level_of_approval='Project_Manager',**filter).order_by(order)
                # print("-----------------------------------",queryset)
                return queryset
                # self.queryset.filter(project__project_manager__id=self.request.user.id,
                #                      status="Pending For Project Manager Approval",current_level_of_approval='Project_Manager')
            elif approval_level == "project_coordinator":
                queryset = self.queryset.filter(project__project_coordinator__id=self.request.user.id,
                                     status__in=["Pending For Project Manager Approval","Pending For Project Coordinator Approval"],
                                     current_level_of_approval__in=['Project_Coordinator','Project_Manager'],**filter).order_by(order)
                # print("-----------------------------------", queryset)
                return queryset
            elif approval_level == "HO":
                # project__project_coordinator__id = self.request.user.id,
                ho_user_obj = PmsTourHoUser.objects.filter(user=self.request.user.id,is_deleted=False)
                if ho_user_obj:
                    queryset = self.queryset.filter(project__isnull=False,
                                                    status__in=["Pending For Project Manager Approval",
                                                                "Pending For Project Coordinator Approval",
                                                                "Pending For HO Approval"],
                                                    current_level_of_approval__in=['Project_Coordinator',
                                                                                   'Project_Manager', 'HO'],
                                                    **filter).order_by(order)
                    # print("-----------------------------------", queryset)
                    return queryset
                else:
                    queryset = self.queryset.filter(current_level_of_approval="abc")
                    return queryset

            elif approval_level == "account_approval":
                # project__project_coordinator__id = self.request.user.id,
                account_user_obj = PmsTourAccounts.objects.filter(user=self.request.user.id,is_deleted=False)
                if account_user_obj:
                    queryset = self.queryset.filter(project__isnull=False,
                                                    status__in=["Pending For Project Manager Approval",
                                                                "Pending For Project Coordinator Approval",
                                                                "Pending For HO Approval",
                                                                "Pending For Account Approval"],
                                                    current_level_of_approval__in=['Project_Coordinator',
                                                                                   'Project_Manager', 'HO',
                                                                                   'Account_Approval'],
                                                    **filter).order_by(order)
                    # print("-----------------------------------", queryset)
                    return queryset
                else:
                    queryset = self.queryset.filter(current_level_of_approval="abc")
                    return queryset

            elif approval_level == "payment":
                # project__project_coordinator__id = self.request.user.id,
                queryset = self.queryset.filter(project__isnull=False,status__in=["Approve"],is_paid=False,**filter).order_by(order)
                # print("-----------------------------------", queryset)
                return queryset
            elif approval_level == "payment_report":
                # project__project_coordinator__id = self.request.user.id,
                queryset = self.queryset.filter(project__isnull=False,status__in=["Approve"],is_paid__in=[True,False],**filter).order_by(order)
                # print("-----------------------------------", queryset)
                return queryset
            elif approval_level == "report":
                account_user_obj = PmsTourAccounts.objects.filter(user=self.request.user.id)
                ho_user_obj = PmsTourHoUser.objects.filter(user=self.request.user.id)
                if account_user_obj or ho_user_obj:
                    queryset = self.queryset.filter(
                        status__in=["Pending For Project Manager Approval", "Pending For Project Coordinator Approval",
                                    "Pending For HO Approval", "Pending For Account Approval", "Approve", "Reject"],
                        # current_level_of_approval__in=['Project_Coordinator', 'Project_Manager', 'HO', 'Account_Approval'],
                        **filter).order_by(order)
                    return queryset
                else:
                    print("else part")
                    queryset = self.queryset.filter((Q(project__project_manager__id=self.request.user.id) | Q(
                        project__project_coordinator__id=self.request.user.id)),
                                                    status__in=["Pending For Project Manager Approval",
                                                                "Pending For Project Coordinator Approval",
                                                                "Pending For HO Approval",
                                                                "Pending For Account Approval", "Approve", "Reject"],
                                                    # current_level_of_approval__in=['Project_Coordinator', 'Project_Manager', 'HO', 'Account_Approval'],
                                                    **filter).order_by(order)
                    return queryset
            else:
                queryset = self.queryset.filter(
                    status__in=["Pending For Project Manager Approval", "Pending For Project Coordinator Approval",
                                "Pending For HO Approval", "Pending For Account Approval","Approve","Reject"],
                    # current_level_of_approval__in=['Project_Coordinator', 'Project_Manager', 'HO', 'Account_Approval'],
                    **filter).order_by(order)
                # print("-----------------------------------", queryset)
                return queryset






        if search:
            queryset_all = PmsTourAndTravelExpenseMaster.objects.none()
            g_query = self.queryset.filter(guest__icontains=search, is_deleted=False)
            queryset_all = (queryset_all | g_query)
            name = search.split(" ")
            # print('name',name)
            if name:
                for i in name:
                    queryset = self.queryset.filter(Q(is_deleted=False) & Q(employee__first_name__icontains=i) |
                                                    Q(employee__last_name__icontains=i)).order_by(order)
                    queryset_all = (queryset_all | queryset)

            return queryset_all

        # if filter:
        #     queryset = self.queryset.filter(**filter).order_by(order)
        #     # print('queryset',queryset)
        #     return queryset
        #
        # else:
        #     queryset = queryset.filter(is_deleted=False).order_by(order)
        #     return queryset

    def get(self, request, *args, **kwargs):
        response = super(TourAndTravelExpenseList, self).get(self, request, args, kwargs)
        # print("response.data",response.data)
        for data in response.data['results']:
            if data['employee'] and data['user_type'] == 1:
                first_name = User.objects.only('first_name').get(id=data['employee']).first_name
                last_name = User.objects.only('last_name').get(id=data['employee']).last_name
                data['name'] = {
                    'id': data['employee'],
                    'name': str(first_name) + " " + str(last_name)
                }
            if data['user_type'] == 2:
                data['name'] = {
                    'id': "",
                    'name': data['guest']
                }
        if response.data['count'] > 0:
            response.data['request_status'] = 0
            response.data['msg'] = settings.MSG_SUCCESS
        else:
            response.data['request_status'] = 1
            response.data['msg'] = settings.MSG_NO_DATA

        return response


class DailyTourPaymentUpdateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsTourAndTravelExpenseMaster.objects.filter(is_deleted=False)
    serializer_class=TourExpencePaymentUpdateSerializer

    @response_modify_decorator_post
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class MultipleTourAndTravelExpenseMasterApprovalV2View(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsTourAndTravelExpenseMaster.objects.filter(is_deleted=False)
    serializer_class =TourExpenceStatusUpdateSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('user_type',)

    @response_modify_decorator_post
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class MultipleTourAndTravelExpenseMasterRejectV2View(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = PmsTourAndTravelExpenseMaster.objects.filter(is_deleted=False)
    serializer_class =TourExpenceStatusRejectSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('user_type',)

    @response_modify_decorator_post
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class TourAndTravelExpenseReportDownload(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    # pagination_class = CSPageNumberPagination
    queryset = PmsTourAndTravelExpenseMaster.objects.filter(is_deleted=False).order_by('-id')
    serializer_class = EmployeeTourAndTravelExpenseReportSerializer

    def get_queryset(self):
        filter = {}
        approval_level = self.request.query_params.get('approval_level', None)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        from_expense_range = self.request.query_params.get('from_expense_range', None)
        expense_range_to = self.request.query_params.get('expense_range_to', None)
        from_limit_exceeded_range = self.request.query_params.get('from_limit_exceeded_range', None)
        limit_exceeded_range_to = self.request.query_params.get('limit_exceeded_range_to', None)
        search = self.request.query_params.get('search', None)
        project = self.request.query_params.get('project', None)
        employee = self.request.query_params.get('employee', None)

        field_name = self.request.query_params.get('field_name', None)
        order_by = self.request.query_params.get('order_by', None)

        order = '-id'
        if field_name and order_by:
            if field_name == 'from_date' and order_by == 'asc':
                order = 'from_date'
                # return self.queryset.filter(is_deleted=False).order_by('from_date')
            elif field_name == 'from_date' and order_by == 'desc':
                order = '-from_date'
                # return self.queryset.filter(is_deleted=False).order_by('-from_date')
            elif field_name == 'to_date' and order_by == 'asc':
                order = 'to_date'
                # return self.queryset.filter(is_deleted=False).order_by('to_date')
            elif field_name == 'to_date' and order_by == 'desc':
                order = '-to_date'
                # return self.queryset.filter(is_deleted=False).order_by('-to_date')
            elif field_name == 'total_expense' and order_by == 'asc':
                order = 'total_expense'
                # return self.queryset.filter(is_deleted=False).order_by('total_expense')
            elif field_name == 'total_expense' and order_by == 'desc':
                order = '-total_expense'
                # return self.queryset.filter(is_deleted=False).order_by('-total_expense')
            elif field_name == 'limit_exceed_by' and order_by == 'asc':
                order = 'limit_exceed_by'
                # return self.queryset.filter(is_deleted=False).order_by('limit_exceed_by')
            elif field_name == 'limit_exceed_by' and order_by == 'desc':
                order = '-limit_exceed_by'
                # return self.queryset.filter(is_deleted=False).order_by('-limit_exceed_by')
            elif field_name == 'total_flight_fare' and order_by == 'asc':
                order = 'total_flight_fare'
                # return self.queryset.filter(is_deleted=False).order_by('total_flight_fare')
            elif field_name == 'total_flight_fare' and order_by == 'desc':
                order = '-total_flight_fare'
                # return self.queryset.filter(is_deleted=False).order_by('-total_flight_fare')
            elif field_name == 'advance' and order_by == 'asc':
                order = 'advance'
                # return self.queryset.filter(is_deleted=False).order_by('advance')
            elif field_name == 'advance' and order_by == 'desc':
                order = '-advance'
                # return self.queryset.filter(is_deleted=False).order_by('-advance')
        if project:
            filter['project__id'] = project
        if employee:
            filter['employee__id'] = employee


        if start_date and end_date:
            start_object = datetime.strptime(start_date, '%Y-%m-%d').date()
            filter['from_date__gte'] = start_object
            end_object = datetime.strptime(end_date, '%Y-%m-%d').date() + timedelta(days=1)
            filter['to_date__lte'] = end_object

        if from_expense_range and expense_range_to:
            filter['total_expense__range'] = (from_expense_range, expense_range_to)

        if from_limit_exceeded_range and limit_exceeded_range_to:
            filter['limit_exceed_by__range'] = (from_limit_exceeded_range, limit_exceeded_range_to)

        if approval_level:
            if approval_level == "project_manager":
                print("in if statement")
                queryset = self.queryset.filter(project__project_manager__id=self.request.user.id,
                                     status="Pending For Project Manager Approval",current_level_of_approval='Project_Manager',**filter).order_by(order)
                # print("-----------------------------------",queryset)
                return queryset
                # self.queryset.filter(project__project_manager__id=self.request.user.id,
                #                      status="Pending For Project Manager Approval",current_level_of_approval='Project_Manager')
            elif approval_level == "project_coordinator":
                queryset = self.queryset.filter(project__project_coordinator__id=self.request.user.id,
                                     status__in=["Pending For Project Manager Approval","Pending For Project Coordinator Approval"],
                                     current_level_of_approval__in=['Project_Coordinator','Project_Manager'],**filter).order_by(order)
                # print("-----------------------------------", queryset)
                return queryset
            elif approval_level == "HO":
                # project__project_coordinator__id = self.request.user.id,
                ho_user_obj = PmsTourHoUser.objects.filter(user=self.request.user.id)
                if ho_user_obj:
                    queryset = self.queryset.filter(project__isnull=False,
                                                    status__in=["Pending For Project Manager Approval",
                                                                "Pending For Project Coordinator Approval",
                                                                "Pending For HO Approval"],
                                                    current_level_of_approval__in=['Project_Coordinator',
                                                                                   'Project_Manager', 'HO'],
                                                    **filter).order_by(order)
                    # print("-----------------------------------", queryset)
                    return queryset
                else:
                    queryset = self.queryset.filter(current_level_of_approval="abc")
                    return queryset

            elif approval_level == "account_approval":
                # project__project_coordinator__id = self.request.user.id,
                account_user_obj = PmsTourAccounts.objects.filter(user=self.request.user.id)
                if account_user_obj:
                    queryset = self.queryset.filter(project__isnull=False,
                                                    status__in=["Pending For Project Manager Approval",
                                                                "Pending For Project Coordinator Approval",
                                                                "Pending For HO Approval",
                                                                "Pending For Account Approval"],
                                                    current_level_of_approval__in=['Project_Coordinator',
                                                                                   'Project_Manager', 'HO',
                                                                                   'Account_Approval'],
                                                    **filter).order_by(order)
                    # print("-----------------------------------", queryset)
                    return queryset
                else:
                    queryset = self.queryset.filter(current_level_of_approval="abc")
                    return queryset


            elif approval_level == "payment":
                # project__project_coordinator__id = self.request.user.id,
                queryset = self.queryset.filter(project__isnull=False,status__in=["Approve"],is_paid=False,**filter).order_by(order)
                # print("-----------------------------------", queryset)
                return queryset
            elif approval_level == "payment_report":
                # project__project_coordinator__id = self.request.user.id,
                queryset = self.queryset.filter(project__isnull=False,status__in=["Approve"],is_paid__in=[True,False],**filter).order_by(order)
                # print("-----------------------------------", queryset)
                return queryset
            elif approval_level == "report":
                account_user_obj = PmsTourAccounts.objects.filter(user=self.request.user.id)
                ho_user_obj = PmsTourHoUser.objects.filter(user=self.request.user.id)
                if account_user_obj or ho_user_obj:
                    queryset = self.queryset.filter(
                        status__in=["Pending For Project Manager Approval", "Pending For Project Coordinator Approval",
                                    "Pending For HO Approval", "Pending For Account Approval", "Approve", "Reject"],
                        # current_level_of_approval__in=['Project_Coordinator', 'Project_Manager', 'HO', 'Account_Approval'],
                        **filter).order_by(order)
                    return queryset
                else:
                    print("else part")
                    queryset = self.queryset.filter((Q(project__project_manager__id=self.request.user.id)|Q(project__project_coordinator__id = self.request.user.id)),
                        status__in=["Pending For Project Manager Approval", "Pending For Project Coordinator Approval",
                                    "Pending For HO Approval", "Pending For Account Approval", "Approve", "Reject"],
                        # current_level_of_approval__in=['Project_Coordinator', 'Project_Manager', 'HO', 'Account_Approval'],
                        **filter).order_by(order)
                    return queryset


            else:
                queryset = self.queryset.filter(
                    status__in=["Pending For Project Manager Approval", "Pending For Project Coordinator Approval",
                                "Pending For HO Approval", "Pending For Account Approval","Approve","Reject"],
                    # current_level_of_approval__in=['Project_Coordinator', 'Project_Manager', 'HO', 'Account_Approval'],
                    **filter).order_by(order)
                # print("-----------------------------------", queryset)
                return queryset






        if search:
            queryset_all = PmsTourAndTravelExpenseMaster.objects.none()
            g_query = self.queryset.filter(guest__icontains=search, is_deleted=False)
            queryset_all = (queryset_all | g_query)
            name = search.split(" ")
            # print('name',name)
            if name:
                for i in name:
                    queryset = self.queryset.filter(Q(is_deleted=False) & Q(employee__first_name__icontains=i) |
                                                    Q(employee__last_name__icontains=i)).order_by(order)
                    queryset_all = (queryset_all | queryset)

            return queryset_all

        # if filter:
        #     queryset = self.queryset.filter(**filter).order_by(order)
        #     # print('queryset',queryset)
        #     return queryset
        #
        # else:
        #     queryset = queryset.filter(is_deleted=False).order_by(order)
        #     return queryset

    def get(self, request, *args, **kwargs):
        response = super(TourAndTravelExpenseReportDownload, self).get(self, request, args, kwargs)
        # print("response.data",response.data)
        for data in response.data:
            if data['employee'] and data['user_type'] == 1:
                # first_name = User.objects.only('first_name').get(id=data['employee']).first_name
                # last_name = User.objects.only('last_name').get(id=data['employee']).last_name
                data['user_type'] = 'employee'
                # data['guest_name'] = str(first_name) + " " + str(last_name)
                #     'id': data['employee'],
                #     'name': str(first_name) + " " + str(last_name)
                # }
            if data['user_type'] == 2:
                data['user_type'] = 'guest'
                # data['name'] = data['guest']
                # 'id': "",
                # 'name': data['guest']
                # }
        if len(response.data):
            df_report = pd.DataFrame.from_records(response.data)
            # print(dict(df_report)['results'])
            # print(df_report[['employee','user_type']])
            df_report = df_report[
                ['user_type', 'employee', 'guest', 'place_of_travel', 'total_expense', 'limit_exceed_by',
                 'total_flight_fare', 'advance', 'from_date', 'to_date', 'approved_status','project_manager_approval_status','site_coordinator_approval_status','HO_status','accounts_approval_status','payment_status']]
            # df_report = df_report[['employee','user_type','name','place_of_travel','total_expense','limit_exceed_by','total_flight_fare','advance','from_date','from_date','approved_status']]
            file_path = settings.MEDIA_ROOT_EXPORT + self.create_file_path()
            df_report.to_excel(file_path, index=None,
                               header=['User Type', 'Employee', 'Guest', 'place of Travel', 'Total Expense',
                                       'Limit Exceed By', 'Total Flight Fare', 'Advance', 'From_Date', 'To_Date',
                                       'Approved Status','Project Manager Approval Status','Site Coordinator Approval Status','HO Approval Status','Accounts Approval Status','Payment Status'])
            file_name = self.create_file_path()
            url = getHostWithPort(request) + file_name if file_name else None
            return Response({'request_status': 1, 'msg': 'Success', 'url': url})
        else:
            return Response({'request_status': 0, 'msg': 'Data Not Found'})

    def create_file_path(self):
        if os.path.isdir('media/pms'):
            file_name = 'media/pms/employee_tour_and_travel_report.xlsx'
        else:
            os.makedirs('media/pms')
            file_name = 'media/pms/employee_tour_and_travel_report.xlsx'
        return file_name


class TourTravelNotificationMailPendingView(APIView):
    permission_classes = [AllowAny]
    #authentication_classes = [TokenAuthentication]
    #queryset = PmsTourAndTravelExpenseMaster.objects.filter(is_deleted=False).order_by('-id')

    def send_notification_to_approvar(self,type,pending_details):
        #print('pending_details',pending_details,type)
        count = pending_details['count']
        if count !=0:
            app_module = 'pms'
            user_email = pending_details['user_email']
            recipient_name = pending_details['name']
           
            title = 'This is a reminder that you have '+str(pending_details['count'])+' pending application waiting for approval.Please take necessary action as soon as possible.'
            body = 'Approval Pending Reminder'
            data = {
                        "app_module":app_module,
                        "type":"travel-and-tour",
                        "sub_type":"approval/"+type.lower(),
                        "id":None
                    }
            data_str = json.dumps(data)
            notification_id = store_sent_notification(users=[pending_details['users']],body=body,title=title,data=data_str,app_module_name=app_module)
            send_notification(users=[pending_details['users']],body=body,title=title,data=data,notification_id=notification_id,url=app_module)

            # Mail
            if user_email:
                mail_data = {
                                "count":pending_details['count'],
                                "recipient_name":recipient_name,
                            }
                
                send_mail('PMS-TT-APR',user_email,mail_data)


    def get(self, request, *args, **kwargs):

        data_dict = dict()
        date = datetime.now().date()
        print('-----------------------------------------------------------')
        ho_approval_count = 0 
        account_approval_count = 0
        project_manager_details = list()
        project_coordinator_details = list()
        projects_for_manger = set()
        projects_for_coordinator = set()

        interval_days_details = PmsTourAndTravelApprovalIntervalDaysMailOrNotificationConf.objects.all()
        for e_interval_days_details in interval_days_details:
            pmsTourAndTravelExpenseMaster = PmsTourAndTravelExpenseMaster.objects.filter(
                is_deleted=False,
                is_paid=False,
                status='Pending For '+e_interval_days_details.level+' Approval'
                ).exclude(
                status__in=['Approve','Reject'])
            if pmsTourAndTravelExpenseMaster:
                for e_pmsTourAndTravelExpenseMaster in pmsTourAndTravelExpenseMaster:
                    pending_date = e_pmsTourAndTravelExpenseMaster.created_at.date() + timedelta(days=int(e_interval_days_details.pending_interval_days))
                    #print('pending_date',pending_date)
                    if pending_date == date:
                        if e_interval_days_details.level == 'Project Manager':
                            projects_for_manger.add(e_pmsTourAndTravelExpenseMaster.project)
                        
                        if e_interval_days_details.level == 'Project Coordinator':
                            projects_for_coordinator.add(e_pmsTourAndTravelExpenseMaster.project)
                        
                        if e_interval_days_details.level == 'HO':
                            ho_approval_count +=1
                        
                        if e_interval_days_details.level == 'Account':
                            account_approval_count +=1

                if e_interval_days_details.level == 'Project Manager':
                    for e_project in projects_for_manger:
                        details_dict = {
                        'users':e_project.project_manager,
                        'user_email':e_project.project_manager.cu_user.cu_alt_email_id,
                        'name':e_project.project_manager.get_full_name(),
                        'count':pmsTourAndTravelExpenseMaster.filter(project=e_project).count()
                        }
                        #project_manager_details.append(details_dict)
                        self.send_notification_to_approvar('project-manager',details_dict)
                
                if e_interval_days_details.level == 'Project Coordinator':
                    for e_project in projects_for_coordinator:
                        details_dict = {
                        'users':e_project.project_coordinator,
                        'user_email':e_project.project_coordinator.cu_user.cu_alt_email_id,
                        'name':e_project.project_coordinator.get_full_name(),
                        #'project':e_project.id,
                        'count':pmsTourAndTravelExpenseMaster.filter(project=e_project).count()
                        }
                        #project_coordinator_details.append(details_dict)
                        self.send_notification_to_approvar('project-coordinator',details_dict)

                if e_interval_days_details.level == 'HO':
                    ho_details = PmsTourHoUser.objects.filter(is_deleted=False)
                    if ho_details:
                        ho_details = ho_details[0]
                        ho_approval_details = {
                        'count':ho_approval_count,
                        'users':ho_details.user,
                        'user_email':ho_details.user.cu_user.cu_alt_email_id,
                        'name':ho_details.user.get_full_name(),
                        }
                        self.send_notification_to_approvar('HO',ho_approval_details)

                if e_interval_days_details.level == 'Account':
                    account_details = PmsTourAccounts.objects.filter(is_deleted=False)
                    if account_details:
                        account_details = account_details[0]
                        account_approval_details = {
                        'count':account_approval_count,
                        'users': account_details.user,
                        'user_email':account_details.user.cu_user.cu_alt_email_id,
                        'name':account_details.user.get_full_name(),
                        }
                        self.send_notification_to_approvar('Account',account_approval_details)

        return Response({})


class TourTravelLeveAutoApproval(APIView):
    permission_classes = [AllowAny]

    def send_notification_to_approvar(self,request_by,travel_master):
        user_email = None
        recipient_name = None
        if request_by == '1':
            lavel = 'project_manager'
            users = [travel_master.project.project_coordinator]
            recipient_name = travel_master.project.project_coordinator.get_full_name()
            user_email = travel_master.project.project_coordinator.cu_user.cu_alt_email_id
            #print('users',users)
        if request_by == '2':
            lavel = 'project_coordinator'
            ho_details = PmsTourHoUser.objects.filter(is_deleted=False)
            if ho_details:
                ho_details = ho_details[0]
                users = [ho_details.user]
                user_email = ho_details.user.cu_user.cu_alt_email_id
                recipient_name = ho_details.user.get_full_name()
        if request_by == 'HO':
            lavel = 'ho'
            account_details = PmsTourAccounts.objects.filter(is_deleted=False)
            if account_details:
                account_details = account_details[0]
                users = [account_details.user]
                user_email = account_details.user.cu_user.cu_alt_email_id
                recipient_name = account_details.user.get_full_name()
        
        app_module = 'pms'

        # For send to approvar
        title = 'A new application has been auto approved by '+lavel.replace('_',' ')+'.Please check the details and take necessary action.'
        body ='Employee Name: {} \nAmount:{} \nBranch Name:{}'.format(travel_master.employee.get_full_name(),travel_master.amount,travel_master.branch_name)
        data = {
                    "app_module":app_module,
                    "type":"travel-and-tour",
                    "sub_type":"approval/"+lavel.replace('_','-'),
                    "id":travel_master.id
                }
        data_str = json.dumps(data)
        notification_id = store_sent_notification(users=users,body=body,title=title,data=data_str,app_module_name=app_module)
        send_notification(users=users,body=body,title=title,data=data,notification_id=notification_id,url=app_module)

        # Mail
        
        if user_email:
            mail_data = {
                            "status":'Auto Approved',
                            "request_by":lavel,
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



    def get(self, request, *args, **kwargs):
        date = datetime.now()
        # print(date)
        interval_obj = PmsTourAndTravelApprovalIntervalDaysMailOrNotificationConf.objects.filter(level_no__in=[1,2,3]).values('level_no','action_interval_days')
        interval_obj = list(interval_obj)
        interval_dict = dict()
        for each in interval_obj:
            key = each['level_no']
            value = each['action_interval_days']
            interval_dict[value] = key

        tours_id = PmsTourAndTravelExpenseApprovalStatus.objects.filter(level_no=4,approval_status="Pending").values_list('tour',flat=True)
        tours = list(tours_id)
        #print('tours',tours)
        for each in tours:
            # print(type(each))
            tour_obj = PmsTourAndTravelExpenseMaster.objects.get(id=int(each))
            # print(tour_obj.created_at)
            diff = date.date() - tour_obj.created_at.date()
            no_of_days = diff.days + 1
            #print(no_of_days)
            status = {1:"Pending For Project Coordinator Approval", 2:"Pending For HO Approval",
                      3:"Pending For Account Approval"}
            current_level = {1:"Project_Coordinator", 2:"HO",
                      3:"Account_Approval"}
            #print('interval_dict',interval_dict)
            if no_of_days:
                #print('cccccccccccccccccccccccccc')
                #print('tour_obj',tour_obj)
                try:
                    #print('interval_dict[no_of_days]',interval_dict[no_of_days],type(interval_dict[no_of_days]))
                    level_approval_status = PmsTourAndTravelExpenseApprovalStatus.objects.filter(
                        tour=tour_obj,
                        approval_status="Pending",
                        level_no=1)
                    #print('level_approval_status',level_approval_status)
                    if level_approval_status:
                        level_approval_status.update(
                            approval_status = "Approve",
                        ) 
                        #level_approval_status.approval_status = "Approve"
                        #level_approval_status.save()
                        tour_obj.status = status[interval_dict[no_of_days]]
                        tour_obj.current_level_of_approval = current_level[interval_dict[no_of_days]]
                        tour_obj.save()
                        self.send_notification_to_approvar(status[interval_dict[no_of_days]],tour_obj)

                except:
                    #print('dsffdsff')
                    pass

        return Response({'request_status': 1, 'msg': 'Success'})
