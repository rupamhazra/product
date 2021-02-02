from django.db import models
from django.contrib.auth.models import User
from dynamic_media import get_directory_path
from validators import validate_file_extension
from pms.models import PmsProjects
import datetime
import time

class PmsSiteBillsInvoicesCategoryMaster(models.Model):
    name = models.CharField(max_length=100,blank=True, null=True)
    icon = models.CharField(max_length=50,blank=True,null=True)
    created_by = models.ForeignKey(User, related_name='bills_cat_created_by',on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, related_name='bills_cat_updated_by', on_delete=models.CASCADE, blank=True, null=True)
    updated_at = models.DateTimeField(blank=True,null=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'pms_site_bills_invoices_master'

class PmsSiteBillsInvoicesApprovalConfiguration(models.Model):
    category = models.ForeignKey(PmsSiteBillsInvoicesCategoryMaster, related_name='bills_approval_invoice_category',on_delete=models.CASCADE, blank=True, null=True)
    level = models.CharField(max_length=30,null=True, blank=True)
    level_no = models.IntegerField(null=True, blank=True)
    user = models.ForeignKey(User, related_name='bills_cat_approval_user', on_delete=models.CASCADE, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='bills_cat_approval_created_by',on_delete=models.CASCADE, blank=True, null=True)
    updated_by = models.ForeignKey(User, related_name='bills_cat_approval_updated_by', on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(default = datetime.datetime.now)
    updated_at = models.DateTimeField(blank=True,null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'pms_site_bills_invoices_approval_configuration'

def unique_rand_bills_invoice():
    while True:
        code = "F" + str(int(time.time()))
        if not PmsSiteBillsInvoices.objects.filter(file_code=code).exists():
            return code

class PmsSiteBillsInvoices(models.Model):
    status_choice=(
        ('Pending', 'Pending'),
        ('Approve', 'Approve'),
        ('Reject', 'Reject'),
    )
    file_code = models.CharField(max_length=200,unique=True,default=unique_rand_bills_invoice,editable=False)
    category = models.ForeignKey(PmsSiteBillsInvoicesCategoryMaster, related_name='bills_invoice_category',on_delete=models.CASCADE, blank=True, null=True)
    project = models.ForeignKey(PmsProjects, related_name='bills_invoice_main_proejct',on_delete=models.CASCADE, blank=True, null=True)
    document = models.FileField(upload_to=get_directory_path,default=None,blank=True, null=True,validators=[validate_file_extension])
    document_name = models.CharField(max_length=100,blank=True,null=True)
    status = models.CharField(max_length=50,choices=status_choice, null=True, blank=True,default='Pending')
    approved_conf =  models.ForeignKey(PmsSiteBillsInvoicesApprovalConfiguration, related_name='bills_invoice_approval_user',on_delete=models.CASCADE, blank=True, null=True)
    current_approval_level_view = models.CharField(max_length=10,blank=True,null=True,default='L1')
    current_approval_level_no = models.IntegerField(blank=True,null=True,default='1')
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='bills_invoice_main_created_by',on_delete=models.CASCADE, blank=True, null=True)
    updated_by = models.ForeignKey(User, related_name='bills_invoice_main_updated_by',on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(blank=True,null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'pms_site_bills_invoices'

class PmsSiteBillsInvoicesApproval(models.Model):
    approval_type = (
        ('Pending','Pending'),
        ('Reject', 'Reject'),
        ('Approve', 'Approve'),
        )
    site_bills_invoices = models.ForeignKey(PmsSiteBillsInvoices, related_name='site_bills_approvals_id',on_delete=models.CASCADE, blank=True, null=True)
    approval_user_level = models.ForeignKey(PmsSiteBillsInvoicesApprovalConfiguration, related_name='site_bills_approvals_user_level',on_delete=models.CASCADE, blank=True, null=True)
    approval_status = models.CharField(max_length=30,choices=approval_type, null=True, blank=True,default='Pending')
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='site_bills_approvals_created_by',on_delete=models.CASCADE, blank=True, null=True)
    updated_by = models.ForeignKey(User, related_name='site_bills_approvals_updated_by', on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(default = datetime.datetime.now)
    updated_at = models.DateTimeField(blank=True,null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'pms_site_bills_invoices_approval'

class PmsSiteBillsInvoicesRemarks(models.Model):
    site_bills_invoices = models.ForeignKey(PmsSiteBillsInvoices, related_name='site_bills_main_id',on_delete=models.CASCADE, blank=True, null=True)
    remarks = models.TextField(blank=True,null=True)
    is_deleted = models.BooleanField(default=False)
    on_create = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='remarks_created_by',on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(default = datetime.datetime.now)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'pms_site_bills_invoices_remarks'


