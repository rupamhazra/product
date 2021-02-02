from django.contrib import admin
from vendor.models import *


@admin.register(VendorContactDetails)
class VendorContactDetails(admin.ModelAdmin):
    list_display = [field.name for field in VendorContactDetails._meta.fields]


@admin.register(VendorDetails)
class VendorDetails(admin.ModelAdmin):
    list_display = [field.name for field in VendorDetails._meta.fields]
