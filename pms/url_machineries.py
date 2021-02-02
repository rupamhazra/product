from pms import views
from django.conf.urls import url, include
from rest_framework import routers
from django.urls import path
from rest_framework.authtoken import views as rest_framework_views

urlpatterns = [

    #:::::::::::::::::  MECHINARY WORKING CATEGORY ::::::::::::::::::::#
    path('machineries_working_category_add/', views.MachineriesWorkingCategoryAddView.as_view()),
    path('machineries_working_category_edit/<pk>/', views.MachineriesWorkingCategoryEditView.as_view()),
    path('machineries_working_category_delete/<pk>/', views.MachineriesWorkingCategoryDeleteView.as_view()),

    #:::::::::::::::::  MECHINARY ::::::::::::::::::::#
    path('machineries_add/', views.MachineriesAddView.as_view()),
    path('machineries_edit/<pk>/', views.MachineriesEditView.as_view()),
    path('machineries_list/', views.MachineriesListDetailsView.as_view()),
    path('machineries_wp_list/', views.MachineriesListWPDetailsView.as_view()),
    path('machineries_list_for_report/', views.MachineriesListForReportView.as_view()),
    path('machineries_list_filter_for_report/', views.MachineriesListFilterForReportView.as_view()),
    path('machineries_delete/<pk>/', views.MachineriesDeleteView.as_view()),
    path('machineries_details_document_add/', views.MachineriesDetailsDocumentAddView.as_view()),
    path('machineries_details_document_edit/<pk>/', views.MachineriesDetailsDocumentEditView.as_view()),
    path('machineries_details_document_delete/<pk>/', views.MachineriesDetailsDocumentDeleteView.as_view()),
    path('machineries_details_document_list/<equipment_id>/', views.MachineriesDetailsDocumentListView.as_view()),
    path('machinary_rented_type_master_add/', views.MachinaryRentedTypeMasterAddView.as_view()),
    path('machinary_rented_type_master_edit/<pk>/', views.MachinaryRentedTypeMasterEditView.as_view()),
    path('machinary_rented_type_master_delete/<pk>/', views.MachinaryRentedTypeMasterDeleteView.as_view()),
    #:::::::::::::::::  MECHINARY REPORTS ::::::::::::::::::::#
    path('machineries_report_add/', views.MachineriesReportAddView.as_view()),
    path('machineries_report_edit/<pk>/', views.MachineriesReportEditView.as_view()),

    ## Change Request PMS Daily [Modifications Required in PMS System] | Date : 25-06-2020 | Rupam Hazra ##

    path('machineries_by_project/<site_id>/', views.MachineriesByProjectView.as_view()),

    ## Functional Specification Document - PMS_V4.0 | Date : 22-07-2020 | Rupam Hazra ##

    path('v2/machineries_report_add/', views.MachineriesReportAddV2View.as_view()),
    path('v2/machineries_report_edit/<pk>/', views.MachineriesReportEditV2View.as_view()),

    path('v2/machineries_daily_report/', views.MachineriesDailyReportView.as_view()),
    path('v2/machineries_daily_report/download/', views.MachineriesDailyReportDownloadView.as_view()),
    
    path('v2/machineries_monthly_report/', views.MachineriesMonthlyReportView.as_view()),
    path('v2/machineries_monthly_report/details_calculation/', views.MachineriesMonthlyReportDetailsCalculationView.as_view()),
    path('v2/machineries_monthly_report/download/', views.MachineriesMonthlyReportExportDownloadView.as_view()),


    path('machineries_dieselconsumption_report/',views.MachineryDieselConsumptionReportView.as_view()),
    path('machineries_dieselconsumption_report/download/',views.MachineryDieselConsumptionReportDwonloadView.as_view()),

    path('machineries_list/download/', views.MachineriesListDetailsDownloadView.as_view()),

]