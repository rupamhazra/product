from django.contrib import admin
from pms.models.module_site_bills_invoices import *

@admin.register(PmsSiteBillsInvoicesCategoryMaster)
class PmsSiteBillsInvoicesCategoryMaster(admin.ModelAdmin):
    list_display = [field.name for field in PmsSiteBillsInvoicesCategoryMaster._meta.fields]

@admin.register(PmsSiteBillsInvoicesApprovalConfiguration)
class PmsSiteBillsInvoicesApprovalConfiguration(admin.ModelAdmin):
    list_display = [field.name for field in PmsSiteBillsInvoicesApprovalConfiguration._meta.fields]

@admin.register(PmsSiteBillsInvoices)
class PmsSiteBillsInvoices(admin.ModelAdmin):
    list_display = [field.name for field in PmsSiteBillsInvoices._meta.fields]

@admin.register(PmsSiteBillsInvoicesRemarks)
class PmsSiteBillsInvoicesRemarks(admin.ModelAdmin):
    list_display = [field.name for field in PmsSiteBillsInvoicesRemarks._meta.fields]

@admin.register(PmsSiteBillsInvoicesApproval)
class PmsSiteBillsInvoicesApproval(admin.ModelAdmin):
    list_display = [field.name for field in PmsSiteBillsInvoicesApproval._meta.fields]



