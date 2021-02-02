from django.contrib import admin
from etask.models import *

# Register your models here.
@admin.register(EtaskTask)
class EtaskTask(admin.ModelAdmin):
    list_display = [field.name for field in EtaskTask._meta.fields]
    search_fields = ('id','owner__username','assign_to__username','assign_by__username')

@admin.register(EtaskUserCC)
class EtaskUserCC(admin.ModelAdmin):
    list_display = [field.name for field in EtaskUserCC._meta.fields]

# @admin.register(EtaskAssignTo)
# class EtaskAssignTo(admin.ModelAdmin):
#     list_display = [field.name for field in EtaskAssignTo._meta.fields]

@admin.register(ETaskReportingDates)
class ETaskReportingDates(admin.ModelAdmin):
    list_display = [field.name for field in ETaskReportingDates._meta.fields]

@admin.register(ETaskReportingActionLog)
class ETaskReportingActionLog(admin.ModelAdmin):
    list_display = [field.name for field in ETaskReportingActionLog._meta.fields]

@admin.register(ETaskComments)
class ETaskComments(admin.ModelAdmin):
    list_display = [field.name for field in ETaskComments._meta.fields]

@admin.register(ETaskCommentsViewers)
class ETaskCommentsViewers(admin.ModelAdmin):
    list_display = [field.name for field in ETaskCommentsViewers._meta.fields]

@admin.register(EtaskIncludeAdvanceCommentsCostDetails)
class EtaskIncludeAdvanceCommentsCostDetails(admin.ModelAdmin):
    list_display = [field.name for field in EtaskIncludeAdvanceCommentsCostDetails._meta.fields]

@admin.register(EtaskIncludeAdvanceCommentsOtherDetails)
class EtaskIncludeAdvanceCommentsOtherDetails(admin.ModelAdmin):
    list_display = [field.name for field in EtaskIncludeAdvanceCommentsOtherDetails._meta.fields]

@admin.register(EtaskIncludeAdvanceCommentsDocuments)
class EtaskIncludeAdvanceCommentsDocuments(admin.ModelAdmin):
    list_display = [field.name for field in EtaskIncludeAdvanceCommentsDocuments._meta.fields]

@admin.register(EtaskFollowUP)
class EtaskFollowUP(admin.ModelAdmin):
    list_display = [field.name for field in EtaskFollowUP._meta.fields]
    search_fields = ('created_by__username',)


@admin.register(FollowupComments)
class FollowupComments(admin.ModelAdmin):
    list_display = [field.name for field in FollowupComments._meta.fields]

@admin.register(FollowupIncludeAdvanceCommentsCostDetails)
class FollowupIncludeAdvanceCommentsCostDetails(admin.ModelAdmin):
    list_display = [field.name for field in FollowupIncludeAdvanceCommentsCostDetails._meta.fields]

@admin.register(FollowupIncludeAdvanceCommentsOtherDetails)
class FollowupIncludeAdvanceCommentsOtherDetails(admin.ModelAdmin):
    list_display = [field.name for field in FollowupIncludeAdvanceCommentsOtherDetails._meta.fields]
@admin.register(EtaskAppointment)
class EtaskAppointment(admin.ModelAdmin):
    list_display = [field.name for field in EtaskAppointment._meta.fields]

@admin.register(EtaskInviteEmployee)
class EtaskInviteEmployee(admin.ModelAdmin):
    list_display = [field.name for field in EtaskInviteEmployee._meta.fields]

@admin.register(EtaskInviteExternalPeople)
class EtaskInviteExternalPeople(admin.ModelAdmin):
    list_display = [field.name for field in EtaskInviteExternalPeople._meta.fields]

@admin.register(FollowupIncludeAdvanceCommentsDocuments)
class FollowupIncludeAdvanceCommentsDocuments(admin.ModelAdmin):
    list_display = [field.name for field in FollowupIncludeAdvanceCommentsDocuments._meta.fields]

@admin.register(AppointmentComments)
class AppointmentComments(admin.ModelAdmin):
    list_display = [field.name for field in AppointmentComments._meta.fields]

@admin.register(AppointmentIncludeAdvanceCommentsCostDetails)
class AppointmentIncludeAdvanceCommentsCostDetails(admin.ModelAdmin):
    list_display = [field.name for field in AppointmentIncludeAdvanceCommentsCostDetails._meta.fields]

@admin.register(AppointmentIncludeAdvanceCommentsOtherDetails)
class AppointmentIncludeAdvanceCommentsOtherDetails(admin.ModelAdmin):
    list_display = [field.name for field in AppointmentIncludeAdvanceCommentsOtherDetails._meta.fields]

@admin.register(AppointmentIncludeAdvanceCommentsDocuments)
class AppointmentIncludeAdvanceCommentsDocuments(admin.ModelAdmin):
    list_display = [field.name for field in AppointmentIncludeAdvanceCommentsDocuments._meta.fields]


@admin.register(EtaskMonthlyReportingDate)
class EtaskMonthlyReportingDate(admin.ModelAdmin):
    list_display = [field.name for field in EtaskMonthlyReportingDate._meta.fields]

@admin.register(EtaskTaskEditLog)
class EtaskTaskEditLog(admin.ModelAdmin):
    list_display = [field.name for field in EtaskTaskEditLog._meta.fields]

@admin.register(EtaskTaskTransferLog)
class EtaskTaskTransferLog(admin.ModelAdmin):
    list_display = [field.name for field in EtaskTaskTransferLog._meta.fields]

@admin.register(EtaskTaskSubAssignLog)
class EtaskTaskSubAssignLog(admin.ModelAdmin):
    list_display = [field.name for field in EtaskTaskSubAssignLog._meta.fields]

@admin.register(EtaskUserCCEdit)
class EtaskUserCCEdit(admin.ModelAdmin):
    list_display = [field.name for field in EtaskUserCCEdit._meta.fields]

@admin.register(ETaskReportingDatesEdit)
class ETaskReportingDatesEdit(admin.ModelAdmin):
    list_display = [field.name for field in ETaskReportingDatesEdit._meta.fields]

@admin.register(ETaskReportingActionLogEdit)
class ETaskReportingActionLogEdit(admin.ModelAdmin):
    list_display = [field.name for field in ETaskReportingActionLogEdit._meta.fields]

@admin.register(EtaskFollowUPEdit)
class EtaskFollowUPEdit(admin.ModelAdmin):
    list_display = [field.name for field in EtaskFollowUPEdit._meta.fields]


@admin.register(DailyWorkTimeSheet)
class DailyWorkTimeSheet(admin.ModelAdmin):
    list_display = [field.name for field in DailyWorkTimeSheet._meta.fields]
    search_fields = ('owner__username',)


@admin.register(TaskExtentionDateMap)
class TaskExtentionDateMap(admin.ModelAdmin):
    list_display = [field.name for field in TaskExtentionDateMap._meta.fields]
    search_fields = ('=task_id','requested_by__username',)

    
@admin.register(TaskCompleteReopenMap)
class TaskCompleteReopenMap(admin.ModelAdmin):
    list_display = [field.name for field in TaskCompleteReopenMap._meta.fields]
    search_fields = ('=task_id','completed_by__username',)


@admin.register(EtaskTaskOwnershipTransferLog)
class EtaskTaskOwnershipTransferLog(admin.ModelAdmin):
    list_display = [field.name for field in EtaskTaskOwnershipTransferLog._meta.fields]

    