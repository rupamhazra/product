from pms import views
from django.conf.urls import url, include
from rest_framework import routers
from django.urls import path
from rest_framework.authtoken import views as rest_framework_views

urlpatterns = [
    
    #Category with approval configuration
    path('pms/site_bills_invoices/category/add/', views.SiteBillsInvoicesCategoryAddView.as_view()),
    path('pms/site_bills_invoices/category/list/', views.SiteBillsInvoicesCategoryListView.as_view()),
    path('pms/site_bills_invoices/category/edit/<pk>/', views.SiteBillsInvoicesCategoryEditView.as_view()),
    
    #Site Bills and Invoices
    path('pms/site_bills_invoices/add/', views.SiteBillsInvoicesAddView.as_view()),
    path('pms/site_bills_invoices/list/', views.SiteBillsInvoicesListView.as_view()),
    path('pms/site_bills_invoices/edit/<pk>/', views.SiteBillsInvoicesEditView.as_view()), # View | Edit
    path('pms/site_bills_invoices/delete/<pk>/', views.SiteBillsInvoicesDeleteView.as_view()), # Delete
    
    # Approval
    path('pms/site_bills_invoices/approval/',views.SiteBillsInvoicesApprovalView.as_view()), # status update(Approve|Reject)
]
