"""SSIL_SSO_MS URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import *
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
   openapi.Info(
      title="SSIL Management API",
      default_version='v1',
      description="SSIL Management API",
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),

)

urlpatterns = [

    url(r'^apidoc(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    url(r'^apidoc/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    url(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    path('admin/', admin.site.urls),
    path('', include('users.urls')),
    path('', include('core.urls')),
    path('', include('master.urls')),
    path('', include('pms.urls')),
    path('', include('vms.urls')),
    path('', include('etask.urls')),
    path('', include('tickettool.urls')),
    path('', include('hrms.urls')),
    path('', include('holidays.urls')),
    path('', include('attendance.urls')),
    path('', include('appversion.urls')),
    path('', include('eticket.urls')),
    path('', include('mailsend.urls')),
    path('', include('notification.urls')),
    path('', include('redis_handler.urls')),
    path('vendor/', include('vendor.urls')),
    path('crm/', include('crm.urls')), # Shyam Future Tech CRM
    path('sscrm/', include('sscrm.urls')), # Shyam Steel CRM
    path('tdms/', include('tdms.urls')), # T & D
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

