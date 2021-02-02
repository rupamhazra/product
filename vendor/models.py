from django.db import models
from django.db import models
from django.contrib.auth.models import User
from dynamic_media import get_directory_path
from validators import validate_file_extension
from master.models import *
# Create your models here.
from core.models import TCoreCity
import datetime


class VendorDetails(models.Model):
    TITLE_CHOICE = (
        ('Mr', 'Mr'),
        ('Mrs', 'Mrs'),
        ('Ms', 'Ms'),
        ('Company', 'Company'),
        ('Mr & Mrs', 'Mr & Mrs')
    )
    approval_type = (
        ('Pending', 'Pending'),
        ('Reject', 'Reject'),
        ('Approve', 'Approve'),
        ('Modify', 'Modify'),
    )

    creation_id = models.CharField(default=None, max_length=10, blank=True, null=True)
    vendor_code = models.CharField(default=None, max_length=10, blank=True, null=True )
    title = models.CharField(choices=TITLE_CHOICE, default="Mr", max_length=10, blank=True, null=True)
    name1 = models.CharField(max_length =100, blank=True, null=True)
    name2 = models.CharField(max_length=100, blank=True, null=True)
    sort1 = models.CharField(max_length=20, blank=True, null=True)
    sort2 = models.CharField(max_length=20, blank=True, null=True)
    approver_name = models.CharField(max_length=20, blank=True, null=True)
    pincode = models.CharField(max_length=15, blank=True, null=True)
    city = models.ForeignKey(TCoreCity, on_delete=models.CASCADE, related_name='city', blank=True,null=True)
    country = models.CharField(max_length=60, blank=True, null=True)
    address_1st_line = models.CharField(max_length=60, blank=True, null=True)
    address_2nd_line = models.CharField(max_length=60, blank=True, null=True)
    address_3rd_line = models.CharField(max_length=60, blank=True, null=True)
    street = models.CharField(max_length=60, blank=True, null=True)
    region = models.CharField(max_length=60, blank=True, null=True)
    mobile_no = models.CharField(max_length=15, blank=True, null=True)
    telephone_no = models.CharField(max_length=15, blank=True, null=True)
    email_id = models.EmailField(max_length=70, blank=True, null=True)
    fax_no = models.CharField(max_length=15, blank=True, null=True)
    vendor_approval_status = models.CharField(max_length=30, choices=approval_type, null=True, blank=True, default='Pending')
    is_approve = models.BooleanField(default=False)
    is_reject = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vendor_created_by', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vendor_updated_by', blank=True, null=True)
    deleted_at = models.DateTimeField(auto_now=True)
    deleted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vendor_deleted_by', blank=True, null=True)

    def __str__(self):
        return str(self.id)
    class Meta:
        db_table = 'vendor_details'

# VendorApprovalStatus model created  by Swarup Adhikary on 14.01.2020 to track the vendor wise approval status


class VendorApprovalStatus(models.Model):
    approval_type = (
        ('Pending', 'Pending'),
        ('Reject', 'Reject'),
        ('Approve', 'Approve'),
        ('Modify', 'Modify'),
    )
    vendor = models.ForeignKey(VendorDetails, related_name='vendor_master', on_delete=models.CASCADE,
                             blank=True, null=True)
    # level = models.CharField(max_length=30, choices=level_choice, null=True, blank=True)
    # level_no = models.IntegerField(null=True, blank=True)
    approval_status = models.CharField(max_length=30, choices=approval_type, null=True, blank=True, default='Pending')
    comment = models.CharField(max_length=200, null=True, blank=True)
    user = models.ForeignKey(User, related_name='vendor_approval_user', on_delete=models.CASCADE, blank=True,
                             null=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='vendor_approval_created_by', on_delete=models.CASCADE,
                                   blank=True, null=True)
    updated_by = models.ForeignKey(User, related_name='vendor_approval_updated_by', on_delete=models.CASCADE,
                                   blank=True, null=True)
    created_at = models.DateTimeField(default=datetime.datetime.now)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'vendor_approval_status'



class VendorContactDetails(models.Model):
    TITLE_CHOICE = (
        ('Mr', 'Mr'),
        ('Mrs', 'Mrs'),
        ('Ms', 'Ms'),
        ('Company', 'Company'),
        ('Mr & Mrs', 'Mr & Mrs')
    )
    vendor = models.ForeignKey(VendorDetails, on_delete=models.CASCADE, related_name='vendor', blank=True,null=True)
    title = models.CharField(choices=TITLE_CHOICE, default="Mr", max_length=10, blank=True, null=True)
    mobile_no = models.CharField(max_length=15, blank=True, null=True)
    telephone_no = models.CharField(max_length=15, blank=True, null=True)
    email_id = models.EmailField(max_length=70, blank=True, null=True)
    fax_no = models.CharField(max_length=15, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vendor_contact_created_by', blank=True,
                                   null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vendor_contact_updated_by', blank=True,
                                   null=True)
    deleted_at = models.DateTimeField(auto_now=True)
    deleted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vendor_contact_deleted_by', blank=True,
                                   null=True)

    def __str__(self):
        return str(self.id)
    class Meta:
        db_table = 'vendor_contact_details'
