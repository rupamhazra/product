from django.contrib import admin
from attendance.models import *

# Register your models here.
@admin.register(DeviceMaster)
class DeviceMaster(admin.ModelAdmin):
    list_display = [field.name for field in DeviceMaster._meta.fields]

@admin.register(AttendenceMonthMaster)
class AttendenceMonthMaster(admin.ModelAdmin):
    list_display = [field.name for field in AttendenceMonthMaster._meta.fields]

@admin.register(JoiningApprovedLeave)
class JoiningApprovedLeave(admin.ModelAdmin):
    list_display = [field.name for field in JoiningApprovedLeave._meta.fields]
    search_fields = ('employee__username',)

@admin.register(Attendance)
class Attendance(admin.ModelAdmin):
    list_display = [field.name for field in Attendance._meta.fields]
    search_fields = ('employee__username','date','employee__cu_user__cu_punch_id',)

@admin.register(AttendanceLog)
class AttendanceLog(admin.ModelAdmin):
    list_display = [field.name for field in AttendanceLog._meta.fields]

@admin.register(AttendanceApprovalRequest)
class AttendanceApprovalRequest(admin.ModelAdmin):
    list_display = [field.name for field in AttendanceApprovalRequest._meta.fields]
    search_fields = ('attendance__id','attendance__employee__username','id',)

@admin.register(AttandanceApprovalDocuments)
class AttandanceApprovalDocuments(admin.ModelAdmin):
    list_display = [field.name for field in AttandanceApprovalDocuments._meta.fields]

@admin.register(EmployeeAdvanceLeaves)
class EmployeeAdvanceLeaves(admin.ModelAdmin):
    list_display = [field.name for field in EmployeeAdvanceLeaves._meta.fields]
    search_fields = ('employee__username',)

@admin.register(AttandancePerDayDocuments)
class AttandancePerDayDocuments(admin.ModelAdmin):
    list_display = [field.name for field in AttandancePerDayDocuments._meta.fields]

@admin.register(VehicleTypeMaster)
class VehicleTypeMaster(admin.ModelAdmin):
    list_display = [field.name for field in VehicleTypeMaster._meta.fields]

@admin.register(AttendenceSaturdayOffMaster)
class AttendenceSaturdayOffMaster(admin.ModelAdmin):
    list_display = [field.name for field in AttendenceSaturdayOffMaster._meta.fields]
    search_fields = ('employee__username',)

@admin.register(AttendenceSaturdayOffLogMaster)
class AttendenceSaturdayOffLogMaster(admin.ModelAdmin):
    list_display = [field.name for field in AttendenceSaturdayOffLogMaster._meta.fields]
    search_fields = ('employee__username',)

@admin.register(AttendanceSpecialdayMaster)
class AttendanceSpecialdayMaster(admin.ModelAdmin):
    list_display = [field.name for field in AttendanceSpecialdayMaster._meta.fields]

@admin.register(AttendenceAction)
class AttendenceAction(admin.ModelAdmin):
    list_display = [field.name for field in AttendenceAction._meta.fields]


@admin.register(AttendenceLeaveAllocatePerMonthPerUser)
class AttendenceLeaveAllocatePerMonthPerUser(admin.ModelAdmin):
    list_display = [field.name for field in AttendenceLeaveAllocatePerMonthPerUser._meta.fields]
    search_fields = ('employee__username',)


@admin.register(AttendanceCarryForwardLeaveBalanceYearly)
class AttendanceCarryForwardLeaveBalanceYearly(admin.ModelAdmin):
    list_display = [field.name for field in AttendanceCarryForwardLeaveBalanceYearly._meta.fields]
    search_fields = ('employee__username',)


@admin.register(EmployeeSpecialLeaves)
class EmployeeSpecialLeaves(admin.ModelAdmin):
    list_display = [field.name for field in EmployeeSpecialLeaves._meta.fields]


@admin.register(WorkFromHomeDeviation)
class WorkFromHomeDeviation(admin.ModelAdmin):
    list_display = [field.name for field in WorkFromHomeDeviation._meta.fields]

@admin.register(ConveyanceConfiguration)
class ConveyanceConfiguration(admin.ModelAdmin):
    list_display = [field.name for field in ConveyanceConfiguration._meta.fields]
    search_fields = ('grade__cg_name',)

@admin.register(ConveyanceApprovalConfiguration)
class ConveyanceApprovalConfiguration(admin.ModelAdmin):
    list_display = [field.name for field in ConveyanceApprovalConfiguration._meta.fields]
    search_fields = ('user__username',)

@admin.register(ConveyanceMaster)
class ConveyanceMaster(admin.ModelAdmin):
    list_display = [field.name for field in ConveyanceMaster._meta.fields]
    search_fields = ('request__attendance__employee__username','request__id','status',)

@admin.register(ConveyanceApproval)
class ConveyanceApproval(admin.ModelAdmin):
    list_display = [field.name for field in ConveyanceApproval._meta.fields]
    search_fields = ('conveyance__id',)

@admin.register(ConveyanceComment)
class ConveyanceComment(admin.ModelAdmin):
    list_display = [field.name for field in ConveyanceComment._meta.fields]
    search_fields = ('conveyance__id','user__username',)

@admin.register(ConveyanceDocument)
class ConveyanceDocument(admin.ModelAdmin):
    list_display = [field.name for field in ConveyanceDocument._meta.fields]
    search_fields = ('conveyance__id',)

@admin.register(ConveyancePlacesMapping)
class ConveyancePlacesMapping(admin.ModelAdmin):
    list_display = [field.name for field in ConveyancePlacesMapping._meta.fields]
    search_fields = ('conveyance__id',)

@admin.register(AttendanceSapReport)
class AttendanceSapReport(admin.ModelAdmin):
    list_display = [field.name for field in AttendanceSapReport._meta.fields]
    search_fields = ('sap_no',)

@admin.register(AttendanceAutoApprovalRequestStatus)
class AttendanceAutoApprovalRequestStatus(admin.ModelAdmin):
    list_display = [field.name for field in AttendanceAutoApprovalRequestStatus._meta.fields]


@admin.register(AttendanceFileRawDta)
class AttendanceFileRawDta(admin.ModelAdmin):
    list_display = [field.name for field in AttendanceFileRawDta._meta.fields]

@admin.register(AttendanceFRSRawData)
class AttendanceFRSRawData(admin.ModelAdmin):
    list_display = [field.name for field in AttendanceFRSRawData._meta.fields]