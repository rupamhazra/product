from django.contrib import admin
from tdms.models.module_site_location import *

@admin.register(TdmsSiteTypeProjectSiteManagement)
class TdmsSiteTypeProjectSiteManagement(admin.ModelAdmin):
    list_display = [field.name for field in TdmsSiteTypeProjectSiteManagement._meta.fields]

@admin.register(TdmsSiteProjectSiteManagement)
class TdmsSiteProjectSiteManagement(admin.ModelAdmin):
    list_display = [field.name for field in TdmsSiteProjectSiteManagement._meta.fields]


@admin.register(TdmsSiteUserMapping)
class TdmsSiteUserMapping(admin.ModelAdmin):
    list_display = [field.name for field in TdmsSiteUserMapping._meta.fields]
