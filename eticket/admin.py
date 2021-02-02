from django.contrib import admin
from eticket.models import *
from eticket.models_resource_mgmnt import *

# Register your models here.


@admin.register(ETICKETModuleMaster)
class ETICKETModuleMaster(admin.ModelAdmin):
    list_display = [field.name for field in ETICKETModuleMaster._meta.fields]

@admin.register(ETICKETReportingHead)
class ETICKETReportingHead(admin.ModelAdmin):
    list_display = [field.name for field in ETICKETReportingHead._meta.fields]

@admin.register(ETICKETSubjectOfDepartment)
class ETICKETSubjectOfDepartment(admin.ModelAdmin):
    list_display = [field.name for field in ETICKETSubjectOfDepartment._meta.fields]

@admin.register(ETICKETTicket)
class ETICKETTicket(admin.ModelAdmin):
    list_display = [field.name for field in ETICKETTicket._meta.fields]

@admin.register(ETICKETTicketDoc)
class ETICKETTicketDoc(admin.ModelAdmin):
    list_display = [field.name for field in ETICKETTicketDoc._meta.fields]

@admin.register(ETICKETTicketComment)
class ETICKETTicketComment(admin.ModelAdmin):
    list_display = [field.name for field in ETICKETTicketComment._meta.fields]

# resource management starts here

@admin.register(ETICKETResourceDeviceTypeMaster)
class ETICKETResourceDeviceTypeMaster(admin.ModelAdmin):
    list_display = [field.name for field in ETICKETResourceDeviceTypeMaster._meta.fields]

@admin.register(ETICKETResourceDeviceMaster)
class ETICKETResourceDeviceMaster(admin.ModelAdmin):
    list_display = [field.name for field in ETICKETResourceDeviceMaster._meta.fields]

@admin.register(ETICKETResourceDeviceAssignment)
class ETICKETResourceDeviceAssignment(admin.ModelAdmin):
    list_display = [field.name for field in ETICKETResourceDeviceAssignment._meta.fields]
# --
@admin.register(ETICKETTicketAssignHistory)
class ETICKETTicketAssignHistory(admin.ModelAdmin):
    list_display = [field.name for field in ETICKETTicketAssignHistory._meta.fields]

