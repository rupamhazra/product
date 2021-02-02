from pms import views
from django.conf.urls import url, include
from rest_framework import routers
from django.urls import path
from rest_framework.authtoken import views as rest_framework_views

urlpatterns = [
    #::::::::::::::: PMS PROJECTS ::::::::::::::::::::::::::::#
    path('pms/daily_expence/add/', views.DailyExpenceAddView.as_view()),
    path('pms/daily_expence/list/', views.DailyExpenceListView.as_view()), # All list and reports
    path('pms/daily_expence/list/download/', views.DailyExpenceListDownloadView.as_view()), # All list and reports
    path('pms/daily_expence/status/update/', views.DailyExpenceStatusUpdateView.as_view()), # status update by all approval level
    path('pms/daily_expence/payment/update/', views.DailyExpencePaymentUpdateView.as_view()), # payment update by all approval level
]
