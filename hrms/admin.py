from django.contrib import admin
from hrms.models import *

# Register your models here.
@admin.register(HrmsBenefitsProvided)
class HrmsBenefitsProvided(admin.ModelAdmin):
    list_display = [field.name for field in HrmsBenefitsProvided._meta.fields]

@admin.register(HrmsUsersBenefits)
class HrmsUsersBenefits(admin.ModelAdmin):
    list_display = [field.name for field in HrmsUsersBenefits._meta.fields]

@admin.register(HrmsUsersOtherFacilities)
class HrmsUsersOtherFacilities(admin.ModelAdmin):
    list_display = [field.name for field in HrmsUsersOtherFacilities._meta.fields]

@admin.register(HrmsDocument)
class HrmsDocument(admin.ModelAdmin):
    list_display = [field.name for field in HrmsDocument._meta.fields]

@admin.register(HrmsDynamicSectionFieldLabelDetailsWithDoc)
class HrmsDynamicSectionFieldLabelDetailsWithDoc(admin.ModelAdmin):
    list_display = [field.name for field in HrmsDynamicSectionFieldLabelDetailsWithDoc._meta.fields]

@admin.register(HrmsNewRequirement)
class HrmsNewRequirement(admin.ModelAdmin):
    list_display = [field.name for field in HrmsNewRequirement._meta.fields]

@admin.register(HrmsInterviewType)
class HrmsInterviewType(admin.ModelAdmin):
    list_display = [field.name for field in HrmsInterviewType._meta.fields]

@admin.register(HrmsInterviewLevel)
class HrmsInterviewLevel(admin.ModelAdmin):
    list_display = [field.name for field in HrmsInterviewLevel._meta.fields]

@admin.register(HrmsScheduleInterview)
class HrmsScheduleInterview(admin.ModelAdmin):
    list_display = [field.name for field in HrmsScheduleInterview._meta.fields]

@admin.register(HrmsScheduleAnotherRoundInterview)
class HrmsScheduleAnotherRoundInterview(admin.ModelAdmin):
    list_display = [field.name for field in HrmsScheduleAnotherRoundInterview._meta.fields]

@admin.register(HrmsScheduleInterviewWith)
class HrmsScheduleInterviewWith(admin.ModelAdmin):
    list_display = [field.name for field in HrmsScheduleInterviewWith._meta.fields]

@admin.register(HrmsScheduleInterviewFeedback)
class HrmsScheduleInterviewFeedback(admin.ModelAdmin):
    list_display = [field.name for field in HrmsScheduleInterviewFeedback._meta.fields]

@admin.register(HrmsNewRequirementLog)
class HrmsNewRequirementLog(admin.ModelAdmin):
    list_display = [field.name for field in HrmsNewRequirementLog._meta.fields]


@admin.register(HrmsScheduleInterviewLog)
class HrmsScheduleInterviewLog(admin.ModelAdmin):
    list_display = [field.name for field in HrmsScheduleInterviewLog._meta.fields]


@admin.register(HrmsQualificationMaster)
class HrmsQualificationMaster(admin.ModelAdmin):
    list_display = [field.name for field in HrmsQualificationMaster._meta.fields]

@admin.register(HrmsUserQualification)
class HrmsUserQualification(admin.ModelAdmin):
    list_display = [field.name for field in HrmsUserQualification._meta.fields]

@admin.register(HrmsUserQualificationDocument)
class HrmsUserQualificationDocument(admin.ModelAdmin):
    list_display = [field.name for field in HrmsUserQualificationDocument._meta.fields]

@admin.register(HrmsThreeMonthsProbationReviewForm)
class HrmsThreeMonthsProbationReviewForm(admin.ModelAdmin):
    list_display = [field.name for field in HrmsThreeMonthsProbationReviewForm._meta.fields]

@admin.register(HrmsThreeMonthsProbationReviewForApproval)
class HrmsThreeMonthsProbationReviewForApproval(admin.ModelAdmin):
    list_display = [field.name for field in HrmsThreeMonthsProbationReviewForApproval._meta.fields]

@admin.register(HrmsFiveMonthsProbationReviewForm)
class HrmsFiveMonthsProbationReviewForm(admin.ModelAdmin):
    list_display = [field.name for field in HrmsFiveMonthsProbationReviewForm._meta.fields]

@admin.register(FiveMonthProbationWorkAssignments)
class FiveMonthProbationWorkAssignments(admin.ModelAdmin):
    list_display = [field.name for field in FiveMonthProbationWorkAssignments._meta.fields]

@admin.register(FiveMonthProbationAchievements)
class FiveMonthProbationAchievements(admin.ModelAdmin):
    list_display = [field.name for field in FiveMonthProbationAchievements._meta.fields]

@admin.register(HrmsFiveMonthsProbationReviewForApproval)
class HrmsFiveMonthsProbationReviewForApproval(admin.ModelAdmin):
    list_display = [field.name for field in HrmsFiveMonthsProbationReviewForApproval._meta.fields]

@admin.register(HrmsIntercom)
class HrmsIntercom(admin.ModelAdmin):
    list_display = [field.name for field in HrmsIntercom._meta.fields]
    search_fields = ('floor__name','name','ext_no')

@admin.register(PreJoiningCandidateData)
class PreJoiningCandidateData(admin.ModelAdmin):
    list_display = [field.name for field in PreJoiningCandidateData._meta.fields]

@admin.register(PreJoineeResourceAllocation)
class PreJoiningCandidateData(admin.ModelAdmin):
    list_display = [field.name for field in PreJoineeResourceAllocation._meta.fields]

@admin.register(EmployeeMediclaimDetails)
class EmployeeMediclaimDetails(admin.ModelAdmin):
    list_display = [field.name for field in EmployeeMediclaimDetails._meta.fields]

# MediclaimEnableTimeFrame
@admin.register(MediclaimEnableTimeFrame)
class MediclaimEnableTimeFrame(admin.ModelAdmin):
    list_display = [field.name for field in MediclaimEnableTimeFrame._meta.fields]