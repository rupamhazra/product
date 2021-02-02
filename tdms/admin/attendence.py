from django.contrib import admin
from tdms.models.module_attendence import *

@admin.register(TdmsAttendance)
class TdmsAttendance(admin.ModelAdmin):
    list_display = [field.name for field in TdmsAttendance._meta.fields]
    search_fields = ('employee__username','id','login_time','logout_time','date',)

@admin.register(TdmsAttandanceLog)
class TdmsAttandanceLog(admin.ModelAdmin):
    list_display = [field.name for field in TdmsAttandanceLog._meta.fields]
    search_fields = ('attandance__id','attandance__employee__username','attandance__date')

@admin.register(TdmsAttandanceDeviation)
class TdmsAttandanceDeviation(admin.ModelAdmin):
    list_display = [field.name for field in TdmsAttandanceDeviation._meta.fields]
    search_fields = ('attandance__id','attandance__employee__username','owned_by__username')

@admin.register(TdmsEmployeeConveyance)
class TdmsEmployeeConveyance(admin.ModelAdmin):
    list_display = [field.name for field in TdmsEmployeeConveyance._meta.fields]

@admin.register(TdmsEmployeeFooding)
class TdmsEmployeeFooding(admin.ModelAdmin):
    list_display = [field.name for field in TdmsEmployeeFooding._meta.fields]

@admin.register(TdmsAttandanceFortnightLeaveDeductionLog)
class TdmsAttandanceFortnightLeaveDeductionLog(admin.ModelAdmin):
    list_display = [field.name for field in TdmsAttandanceFortnightLeaveDeductionLog._meta.fields]
    search_fields = ('attendance__id','attendance__employee__username','attendance__date')

@admin.register(TdmsAttandanceLeaveBalanceTransferLog)
class TdmsAttandanceLeaveBalanceTransferLog(admin.ModelAdmin):
    list_display = [field.name for field in TdmsAttandanceLeaveBalanceTransferLog._meta.fields]
    search_fields = ('attendance__id','employee__username','attendance_date','sap_personnel_no')