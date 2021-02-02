"""
Created by Shubhadeep on 07-09-2020
"""
from eticket import views_resource_mgmnt as views
from django.urls import path


urlpatterns = [
    path('eticket/resource/device_type/add/', views.ETICKETResourceDeviceTypeMasterView.as_view()),
    path('eticket/resource/device_type/edit/<pk>/', views.ETICKETResourceDeviceTypeMasterEditView.as_view()),
    
    path('eticket/resource/device/add/', views.ETICKETResourceDeviceMasterView.as_view()),
    path('eticket/resource/device/download_list/', views.ETICKETResourceDeviceMasterDownloadView.as_view()),
    path('eticket/resource/device/edit/<pk>/', views.ETICKETResourceDeviceMasterEditView.as_view()),

    path('eticket/resource/device/assign/', views.ETICKETResourceDeviceAssignmentView.as_view()),
    path('eticket/resource/device/assign/edit/<pk>/', views.ETICKETResourceDeviceAssignmentView.as_view()),

    path('eticket/resource/device/move_to_inventory/<pk>/', views.ETICKETResourceDeviceUnassignmentView.as_view()),

]