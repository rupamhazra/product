'''
Redis Handler URL Module
File added by Shubhadeep on 27-08-2020
'''

from redis_handler import views
from django.urls import path

urlpatterns = [
    path('redis_pub_demo/', views.RedisPubDemo.as_view()),
]