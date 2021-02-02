from django.urls import path

from notification import views

urlpatterns = [
    # :::::::::::::::::::::::: Test ::::::::::::::::::::::::::: #
    path('notification_testing/', views.NotificationTestingView.as_view()),

    # :::::::::::::::::::::::: Add Device Token :::::::::::::::::::::: #
    path('add_device_token/', views.AddDeviceTokenView.as_view()),
    path('read_notification/<pk>/', views.ReadNotificationView.as_view()),

    # ::::::::::::::::: App Module Wise Notification List ::::::::::::::::::#
    path('etask_notification_list/', views.EtaskNotificationListView.as_view()),

    # ::::::::::::::::: App Module Wise Notification List ::::::::::::::::::#
    path('notification/list/<module_name>/', views.NotificationListView.as_view()),


]
