from pms import views
from django.conf.urls import url, include
from rest_framework import routers
from django.urls import path

from rest_framework.authtoken import views as rest_framework_views


urlpatterns = [
    path('pms/account_user/add/', views.PmsAccountUserAddView.as_view()),
    path('pms/account_user/edit/<pk>/', views.PmsAccountUserEditView.as_view()),
    path('pms/ho_user/add/', views.PmsHoUserAddView.as_view()),
    path('pms/ho_user/edit/<pk>/', views.PmsHoUserEditView.as_view()),
    path('pms/tour_account_user/add/', views.PmsTourAccountUserAddView.as_view()),
    path('pms/tour_account_user/edit/<pk>/', views.PmsTourAccountUserEditView.as_view()),
    path('pms/tour_ho_user/add/', views.PmsTourHoUserAddView.as_view()),
    path('pms/tour_ho_user/edit/<pk>/', views.PmTourHoUserEditView.as_view()),
    # path('pms/site_bills_invoices_ho_user/add/', views.PmsSiteBillsInvoicesHoUserAddView.as_view()),
    # path('pms/site_bills_invoices_ho_user/edit/<pk>/', views.PmsSiteBillsInvoicesHoUserEditView.as_view()),
]