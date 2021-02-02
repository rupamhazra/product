from pms import views
from django.conf.urls import url, include
from rest_framework import routers
from django.urls import path
from rest_framework.authtoken import views as rest_framework_views

urlpatterns = [
    #::::::::::::::: PMS PROJECTS DAILY WORK SHEET ::::::::::::::::::::::::::::#
    path('daily_work/add/', views.DailyWorkSheetAddView.as_view()),
    path('daily_work/list/', views.DailyWorkSheetListView.as_view()),
    path('daily_work/edit/<pk>/', views.DailyWorkSheetEditView.as_view()),
    path('daily_work/delete/<pk>/', views.DailyWorkSheetDeleteView.as_view()),
    path('daily_work/list/download/', views.DailyWorkSheetTaskListDownloadView.as_view())
]