from django.contrib import admin
from crm import models


@admin.register(models.CrmTask)
class CrmTaskAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.CrmTask._meta.fields]
    # search_fields = ('user', 'user__username')


@admin.register(models.CrmTechnology)
class CrmTechnologyAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.CrmTechnology._meta.fields]
    # search_fields = ('user', 'user__username')


@admin.register(models.CrmSource)
class CrmSourceAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.CrmSource._meta.fields]
    # search_fields = ('user', 'user__username')


@admin.register(models.CrmDepartment)
class CrmDepartmentAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.CrmDepartment._meta.fields]
    # search_fields = ('user', 'user__username')


@admin.register(models.CrmPoc)
class CrmPocAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.CrmPoc._meta.fields]
    # search_fields = ('user', 'user__username')


@admin.register(models.CrmLead)
class CrmLeadAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.CrmLead._meta.fields]
    # search_fields = ('user', 'user__username')


@admin.register(models.CrmOpportunity)
class CrmOpportunityAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.CrmOpportunity._meta.fields]
    # search_fields = ('user', 'user__username')


@admin.register(models.CrmOpportunityPresaleLog)
class CrmOpportunityPresaleLogAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.CrmOpportunityPresaleLog._meta.fields]
    # search_fields = ('user', 'user__username')


@admin.register(models.CrmOpportunityStageChangesLog)
class CrmOpportunityStageChangesLogAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.CrmOpportunityStageChangesLog._meta.fields]
    # search_fields = ('user', 'user__username')


@admin.register(models.CrmOpportunityTaskMap)
class CrmOpportunityTaskMapAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.CrmOpportunityTaskMap._meta.fields]
    # search_fields = ('user', 'user__username')


@admin.register(models.CrmLeadTaskMap)
class CrmLeadTaskMapAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.CrmLeadTaskMap._meta.fields]
    # search_fields = ('user', 'user__username')


@admin.register(models.CrmOpportunityTechnologyMap)
class CrmOpportunityTechnologyMapAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.CrmOpportunityTechnologyMap._meta.fields]
    # search_fields = ('user', 'user__username')


@admin.register(models.CrmOpportunityPocMap)
class CrmOpportunityPocMapAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.CrmOpportunityPocMap._meta.fields]
    # search_fields = ('user', 'user__username')


@admin.register(models.CrmProject)
class CrmProjectAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.CrmProject._meta.fields]
    # search_fields = ('user', 'user__username')


@admin.register(models.CrmProjectTechnologyMap)
class CrmProjectTechnologyMapAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.CrmProjectTechnologyMap._meta.fields]
    # search_fields = ('user', 'user__username')


@admin.register(models.CrmUserTypeMap)
class CrmUserTypeMapAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.CrmUserTypeMap._meta.fields]
    # search_fields = ('user', 'user__username')


@admin.register(models.CrmPaymentMode)
class CrmPaymentModeAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.CrmPaymentMode._meta.fields]
    # search_fields = ('user', 'user__username')


@admin.register(models.CrmOpportunityRemarks)
class CrmOpportunityRemarksAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.CrmOpportunityRemarks._meta.fields]
    # search_fields = ('user', 'user__username')


@admin.register(models.CrmColorStatus)
class CrmColorStatusAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.CrmColorStatus._meta.fields]
    # search_fields = ('user', 'user__username')


@admin.register(models.CrmLeadReassignLog)
class CrmLeadReassignLogAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.CrmLeadReassignLog._meta.fields]
    # search_fields = ('user', 'user__username')


@admin.register(models.CrmOpportunityBAChangeLog)
class CrmOpportunityBAChangeLogAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.CrmOpportunityBAChangeLog._meta.fields]
    # search_fields = ('user', 'user__username')


@admin.register(models.CrmDocument)
class CrmDocumentAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.CrmDocument._meta.fields]
    # search_fields = ('user', 'user__username')


@admin.register(models.CrmOpportunityChangeRequestMap)
class CrmOpportunityChangeRequestMapAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.CrmOpportunityChangeRequestMap._meta.fields]
    # search_fields = ('user', 'user__username')


@admin.register(models.CrmOpportunityMilestoneChangeRequestDistribution)
class CrmOpportunityMilestoneChangeRequestDistributionAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.CrmOpportunityMilestoneChangeRequestDistribution._meta.fields]
    # search_fields = ('user', 'user__username')


@admin.register(models.CrmChangeRequest)
class CrmChangeRequestAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.CrmChangeRequest._meta.fields]
    # search_fields = ('user', 'user__username')


@admin.register(models.CrmMilestone)
class CrmMilestoneAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.CrmMilestone._meta.fields]
    # search_fields = ('user', 'user__username')


@admin.register(models.CrmOpportunityMilestoneMap)
class CrmOpportunityMilestoneAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.CrmOpportunityMilestoneMap._meta.fields]
    # search_fields = ('user', 'user__username')


@admin.register(models.CrmCurrencyConversionHistory)
class CrmCurrencyConversionHistoryAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.CrmCurrencyConversionHistory._meta.fields]
    # search_fields = ('user', 'user__username')


@admin.register(models.CrmLeadDocument)
class CrmLeadDocumentAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.CrmLeadDocument._meta.fields]
    # search_fields = ('user', 'user__username')


@admin.register(models.CrmResource)
class CrmResourceAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.CrmResource._meta.fields]
    # search_fields = ('user', 'user__username')


@admin.register(models.CrmRequestHandler)
class CrmRequestHandlerAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.CrmRequestHandler._meta.fields]
    # search_fields = ('user', 'user__username')


@admin.register(models.CrmOpportunityResourceManagement)
class CrmOpportunityResourceManagementAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.CrmOpportunityResourceManagement._meta.fields]
    # search_fields = ('user', 'user__username')


@admin.register(models.CrmOpportunityDocumentTag)
class CrmOpportunityProposalDocumentAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.CrmOpportunityDocumentTag._meta.fields]
    # search_fields = ('user', 'user__username')


@admin.register(models.CrmDocumentTag)
class CrmDocumentTagAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.CrmDocumentTag._meta.fields]
    # search_fields = ('user', 'user__username')


@admin.register(models.CrmProjectFormLog)
class CrmProjectFormLogAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.CrmProjectFormLog._meta.fields]
    # search_fields = ('user', 'user__username')


@admin.register(models.CrmCeleryRevoke)
class CrmCeleryRevokeAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.CrmCeleryRevoke._meta.fields]
    # search_fields = ('user', 'user__username')

