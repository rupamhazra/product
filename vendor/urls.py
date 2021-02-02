from vendor import views
from django.conf.urls import url, include
from rest_framework import routers
from django.urls import path
from rest_framework.authtoken import views as rest_framework_views

'''
    This module prepared by @@ Swarup Adhikary and Prashonto. Any kind of issues occurred, ask me first !!!
    Version - 1.0
'''

urlpatterns = [
    path('vendor_basic_details/add/', views.VendorAddView.as_view()),
    path('vendor_basic_details/edit/<pk>/', views.VendorBasicDetailEditView.as_view()),
    path('vendor_contact_details/add/', views.VendorContactAddView.as_view()),
    path('vendor_basic_details/', views.VendorBasicDetailView.as_view()),
    path('vendor_contact_details/list/', views.VendorContactListView.as_view()),

    path('vendor_approval_list/', views.VendorApprovalListView.as_view()),

    path('vendor_master_approval/',views.VendorMasterApprovalView.as_view()),
    path('vendor_master_reject/',views.VendorMasterRejectView.as_view()),
# VendorBasicDetailView

]