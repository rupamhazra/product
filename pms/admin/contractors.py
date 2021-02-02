from django.contrib import admin
from pms.models.module_contractors import *

@admin.register(PmsContractorsCategoryMaster)
class PmsContractorsCategoryMaster(admin.ModelAdmin):
    list_display = [field.name for field in PmsContractorsCategoryMaster._meta.fields]

@admin.register(PmsContractor)
class PmsContractor(admin.ModelAdmin):
    list_display = [field.name for field in PmsContractor._meta.fields]