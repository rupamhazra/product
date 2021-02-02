from django.contrib import admin
from tdms.models.module_dailyworksheet import *

@admin.register(TdmsDailyWorkSheet)
class TdmsDailyWorkSheet(admin.ModelAdmin):
    list_display = [field.name for field in TdmsDailyWorkSheet._meta.fields]
    search_fields = ('owner__username','date',)