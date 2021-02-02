from django.contrib import admin
from pms.models.module_daily_expence import *

@admin.register(PmsDailyExpence)
class PmsDailyExpence(admin.ModelAdmin):
    list_display = [field.name for field in PmsDailyExpence._meta.fields]

@admin.register(PmsDailyExpenceItemMapping)
class PmsDailyExpenceItemMapping(admin.ModelAdmin):
    list_display = [field.name for field in PmsDailyExpenceItemMapping._meta.fields]

@admin.register(PmsDailyExpenceApprovalConfiguration)
class PmsDailyExpenceApprovalConfiguration(admin.ModelAdmin):
    list_display = [field.name for field in PmsDailyExpenceApprovalConfiguration._meta.fields]

@admin.register(PmsDailyExpenceApproval)
class PmsDailyExpenceApproval(admin.ModelAdmin):
    list_display = [field.name for field in PmsDailyExpenceApproval._meta.fields]

@admin.register(PmsDailyExpenceRemarks)
class PmsDailyExpenceRemarks(admin.ModelAdmin):
    list_display = [field.name for field in PmsDailyExpenceRemarks._meta.fields]

