from pms import views
from django.conf.urls import url, include
from rest_framework import routers
from django.urls import path
from rest_framework.authtoken import views as rest_framework_views

urlpatterns = [
    
    # Category
    path('pms/contractors/category/add/', views.ContractorsCategoryAddView.as_view()), # Add
    path('pms/contractors/category/list/', views.ContractorsCategoryListView.as_view()), # List
    path('pms/contractors/category/edit/<pk>/', views.ContractorsCategoryEditView.as_view()), # Edit
    path('pms/contractors/category/delete/<pk>/', views.ContractorsCategoryDeleteView.as_view()), # Delete with all contractors under category
    
    # Contractors 
    path('pms/contractors/add/', views.ContractorsAddView.as_view()), # Add
    path('pms/contractors/list/', views.ContractorsListView.as_view()), # List
    path('pms/contractors/list/download/', views.ContractorsListDownloadView.as_view()), # Download
    path('pms/contractors/edit/<pk>/', views.ContractorsEditView.as_view()), # View | Edit
    path('pms/contractors/delete/<pk>/', views.ContractorsDeleteView.as_view()), # Delete
    

]
