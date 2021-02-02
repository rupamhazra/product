"""
Created by Shubhadeep on 07-09-2020
"""
from django.db import models
from django.contrib.auth.models import User
from dynamic_media import get_directory_path
from validators import validate_file_extension
import datetime
import time
from core.models import TCoreDepartment

class ETICKETResourceDeviceTypeMaster(models.Model):
    type_name = models.CharField(max_length=100)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='etr_devicetype_created_by',
                                 on_delete=models.CASCADE, blank=True, null=True)
    updated_by = models.ForeignKey(User, related_name='etr_devicetype_updated_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'eticket_resource_device_type_master'

class ETICKETResourceDeviceMaster(models.Model):
    device_type = models.ForeignKey(ETICKETResourceDeviceTypeMaster, related_name='etr_device_device_type',
                on_delete=models.CASCADE)    
    specification = models.CharField(max_length=1000, blank=False, null=False)
    request_no = models.CharField(max_length=100, blank=True, null=True)
    po_no = models.CharField(max_length=100, blank=False, null=False)
    purchased_at = models.DateTimeField(null=False)
    sr_no = models.CharField(max_length=100, blank=False, null=False)
    oem = models.CharField(max_length=100, blank=False, null=False)
    oem_sr_no = models.CharField(max_length=100, blank=False, null=False)
    tag_no = models.CharField(max_length=100, blank=False, null=False)
    model = models.CharField(max_length=100, blank=False, null=False)
    is_assigned = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='etr_device_created_by',
                                 on_delete=models.CASCADE, blank=True, null=True)
    updated_by = models.ForeignKey(User, related_name='etr_device_updated_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'eticket_resource_device_master'

class ETICKETResourceDeviceAssignment(models.Model):
    device = models.ForeignKey(ETICKETResourceDeviceMaster, related_name='etr_assign_device_type',
                on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(null=True)
    employee = models.ForeignKey(User, related_name='etr_assign_employee',
                on_delete=models.CASCADE, blank=True, null=True)
    assigned_by = models.ForeignKey(User, related_name='etr_assign_assigned_by',
                on_delete=models.CASCADE, blank=True, null=True)

    seat_no = models.CharField(max_length=100, blank=True, null=True)
    os = models.CharField(max_length=100, blank=True, null=True)
    ms_office = models.BooleanField(default=False)
    sap = models.BooleanField(default=False)
    e_scan = models.BooleanField(default=False)
    vpn = models.BooleanField(default=False)
    vpn_id = models.CharField(max_length=100, blank=True, null=True)
    is_current = models.BooleanField(default=False)

    is_deleted = models.BooleanField(default=False)
    
    unassigned_by = models.ForeignKey(User, related_name='etr_assign_unassigned_by',
                on_delete=models.CASCADE, blank=True, null=True)
    assigned_upto = models.DateTimeField(null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'eticket_resource_device_assignment'
