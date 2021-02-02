from django.contrib import admin
from pms.models.module_accounts import *

@admin.register(PmsAccounts)
class PmsAccounts(admin.ModelAdmin):
    list_display = [field.name for field in PmsAccounts._meta.fields]

@admin.register(PmsHoUser)
class PmsHoUser(admin.ModelAdmin):
    list_display = [field.name for field in PmsHoUser._meta.fields]


@admin.register(PmsTourAccounts)
class PmsTourAccounts(admin.ModelAdmin):
    list_display = [field.name for field in PmsTourAccounts._meta.fields]

@admin.register(PmsTourHoUser)
class PmsTourHoUser(admin.ModelAdmin):
    list_display = [field.name for field in PmsTourHoUser._meta.fields]

# @admin.register(PmsSiteBillsInvoicesHoUser)
# class PmsSiteBillsInvoicesHoUser(admin.ModelAdmin):
#     list_display = [field.name for field in PmsSiteBillsInvoicesHoUser._meta.fields]




