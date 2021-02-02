from django.contrib import admin
from sscrm import models


@admin.register(models.SSCrmCustomer)
class SSCrmCustomerAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.SSCrmCustomer._meta.fields]
    # search_fields = ('user', 'user__username')


@admin.register(models.SSCrmCustomerCodeType)
class SSCrmCustomerCodeTypeAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.SSCrmCustomerCodeType._meta.fields]
    # search_fields = ('user', 'user__username')


@admin.register(models.SSCrmContractType)
class SSCrmContractTypeAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.SSCrmContractType._meta.fields]
    # search_fields = ('user', 'user__username')
