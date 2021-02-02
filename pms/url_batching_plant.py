"""
Created by Bishal on 28-08-2020
Reviewd and updated by Shubhadeep
"""
from pms import views
from django.conf.urls import url, include
from rest_framework import routers
from django.urls import path
from rest_framework.authtoken import views as rest_framework_views


urlpatterns = [
    #::::::::::::::: BATCHING PLANT MASTER TABLES ::::::::::::::::::::::::::::#
    # previous URL patterns has been updated to sub URL patterns
    path('pms/batching/brand_of_cement/add/', views.PmsBatchingPlantBrandOfCementMasterView.as_view()),
    path('pms/batching/brand_of_cement/edit/<pk>/', views.PmsBatchingPlantBrandOfCementMasterEditView.as_view()),
    path('pms/batching/purpose/add/', views.PmsBatchingPlantPurposeMasterView.as_view()),
    path('pms/batching/purpose/edit/<pk>/', views.PmsBatchingPlantPurposeMasterEditView.as_view()),
    path('pms/batching/concrete/add/', views.PmsBatchingPlantConcreteMasterView.as_view()),
    path('pms/batching/concrete/edit/<pk>/', views.PmsBatchingPlantConcreteMasterEditView.as_view()),
    path('pms/batching/concrete_ingredient/add/', views.PmsBatchingPlantConcreteIngredientMasterView.as_view()),
    path('pms/batching/concrete_ingredient/edit/<pk>/', views.PmsBatchingPlantConcreteIngredientMasterEditView.as_view()),

    #::::::::::::::: BATCHING PLANT ENTRY ::::::::::::::::::::::::::::#
    path('pms/batching/batching_entry/add/', views.PmsBatchingPlantBatchingEntryAddView.as_view()),
    path('pms/batching/batching_entry/list_download/', views.PmsBatchingPlantBatchingEntryDownloadView.as_view()),
    path('pms/batching/batching_entry/report/', views.PmsBatchingPlantBatchingReportView.as_view()),
    path('pms/batching/batching_entry/report_download/', views.PmsBatchingPlantBatchingReportDownloadView.as_view()),
    path('pms/batching/batching_entry/edit/<pk>/', views.PmsBatchingPlantBatchingEntryEditView.as_view()),
    path('pms/batching/batching_entry/change_status/<pk>/', views.PmsBatchingPlantBatchingEntryChangeStatusView.as_view()),
]