from pms import views
from django.conf.urls import url, include
from rest_framework import routers
from django.urls import path
from rest_framework.authtoken import views as rest_framework_views


urlpatterns = [
    path('tour_and_travel_expense_add/', views.TourAndTravelExpenseAddView.as_view()),
    path('tour_and_travel_vendor_or_employee_details_approval/',views.TourAndTravelVendorOrEmployeeDetailsApprovalView.as_view()),
    path('tour_and_travel_bill_received_approval/',views.TourAndTravelBillReceivedApprovalView.as_view()),
    path('tour_and_travel_final_booking_details_approval/',views.TourAndTravelFinalBookingDetailsApprovalView.as_view()),
    path('tour_and_travel_expense_master_approval/<pk>/',views.TourAndTravelExpenseMasterApprovalView.as_view()),
    path('tour_and_travel_expense_approval_list/', views.TourAndTravelExpenseApprovalList.as_view()),
    path('employee_tour_and_travel_expense_approval_list/', views.UserTourAndTravelExpenseApprovalList.as_view()),
    path('pms/employee_tour_and_travel_expense_list/download/', views.UserTourAndTravelExpenseReportDownload.as_view()),
    path('pms/tour_and_travel_expense_add_document/', views.TourAndTravelDocumentEditView.as_view()),
    path('pms/tour_and_travel_expense/list/', views.TourAndTravelExpenseList.as_view()),
    path('pms/employee_tour_and_travel_expense_report/download/', views.TourAndTravelExpenseReportDownload.as_view()),
    path('pms/tour_and_travel_expense/payment/update/', views.DailyTourPaymentUpdateView.as_view()),

    # multiple approve
    path('pms/tour_and_travel_expense_master_approval/',views.MultipleTourAndTravelExpenseMasterApprovalV2View.as_view()),
    path('pms/tour_and_travel_expense_master_reject/',views.MultipleTourAndTravelExpenseMasterRejectV2View.as_view()),

    # For pending notification cron
    path('pms/tour_and_travel/notification_mail/pending/',views.TourTravelNotificationMailPendingView.as_view()),

    # auto approval
    path('pms/tour_and_travel/auto_approval/',views.TourTravelLeveAutoApproval.as_view()),

]







