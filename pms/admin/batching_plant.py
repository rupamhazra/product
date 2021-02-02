from django.contrib import admin
from pms.models.module_batching_plant import *


@admin.register(PmsBatchingPlantBrandOfCementMaster)
class PmsBatchingPlantBrandOfCementMaster(admin.ModelAdmin):
    list_display = [field.name for field in PmsBatchingPlantBrandOfCementMaster._meta.fields]


@admin.register(PmsBatchingPlantPurposeMaster)
class PmsBatchingPlantPurposeMaster(admin.ModelAdmin):
    list_display = [field.name for field in PmsBatchingPlantPurposeMaster._meta.fields]


@admin.register(PmsBatchingPlantConcreteMaster)
class PmsBatchingPlantConcreteMaster(admin.ModelAdmin):
    list_display = [field.name for field in PmsBatchingPlantConcreteMaster._meta.fields]


@admin.register(PmsBatchingPlantMappingConcreteBrandOfCement)
class PmsBatchingPlantMappingConcreteBrandOfCement(admin.ModelAdmin):
    list_display = [field.name for field in PmsBatchingPlantMappingConcreteBrandOfCement._meta.fields]


@admin.register(PmsBatchingPlantMappingConcretePurpose)
class PmsBatchingPlantMappingConcretePurpose(admin.ModelAdmin):
    list_display = [field.name for field in PmsBatchingPlantMappingConcretePurpose._meta.fields]


@admin.register(PmsBatchingPlantConcreteIngredientMaster)
class PmsBatchingPlantConcreteIngredientMaster(admin.ModelAdmin):
    list_display = [field.name for field in PmsBatchingPlantConcreteIngredientMaster._meta.fields]


@admin.register(PmsBatchingPlantBatchingEntry)
class PmsBatchingPlantBatchingEntry(admin.ModelAdmin):
    list_display = [field.name for field in PmsBatchingPlantBatchingEntry._meta.fields]


@admin.register(PmsBatchingPlantBatchingEntryDetails)
class PmsBatchingPlantBatchingEntryDetails(admin.ModelAdmin):
    list_display = [field.name for field in PmsBatchingPlantBatchingEntryDetails._meta.fields]
