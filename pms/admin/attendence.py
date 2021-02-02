from django.contrib import admin
from pms.models.module_attendence import *

@admin.register(PmsAttendance)
class PmsAttendance(admin.ModelAdmin):
    list_display = [field.name for field in PmsAttendance._meta.fields]
    search_fields = ('employee__username','id','login_time','logout_time','date',)

@admin.register(PmsAttandanceLog)
class PmsAttandanceLog(admin.ModelAdmin):
    list_display = [field.name for field in PmsAttandanceLog._meta.fields]
    search_fields = ('attandance__id','attandance__employee__username','attandance__date')

@admin.register(PmsAttandanceDeviation)
class PmsAttandanceDeviation(admin.ModelAdmin):
    list_display = [field.name for field in PmsAttandanceDeviation._meta.fields]
    search_fields = ('attandance__id','attandance__employee__username','owned_by__username')

@admin.register(PmsEmployeeConveyance)
class PmsEmployeeConveyance(admin.ModelAdmin):
    list_display = [field.name for field in PmsEmployeeConveyance._meta.fields]

@admin.register(PmsEmployeeFooding)
class PmsEmployeeFooding(admin.ModelAdmin):
    list_display = [field.name for field in PmsEmployeeFooding._meta.fields]

@admin.register(PmsEmployeeLeaves)
class PmsEmployeeLeaves(admin.ModelAdmin):
    list_display = [field.name for field in PmsEmployeeLeaves._meta.fields]

@admin.register(PmsAttandanceFortnightLeaveDeductionLog)
class PmsAttandanceFortnightLeaveDeductionLog(admin.ModelAdmin):
    list_display = [field.name for field in PmsAttandanceFortnightLeaveDeductionLog._meta.fields]
    search_fields = ('attendance__id','attendance__employee__username','attendance__date')

@admin.register(PmsAttandanceLeaveBalanceTransferLog)
class PmsAttandanceLeaveBalanceTransferLog(admin.ModelAdmin):
    list_display = [field.name for field in PmsAttandanceLeaveBalanceTransferLog._meta.fields]
    search_fields = ('attendance__id','employee__username','attendance_date','sap_personnel_no')