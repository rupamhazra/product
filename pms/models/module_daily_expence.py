from django.db import models
from django.contrib.auth.models import User
from dynamic_media import get_directory_path
#from django_mysql.models import EnumField
from validators import validate_file_extension
from pms.models import PmsProjects
import datetime
import time

#::::::::::::::::  DAILY EXPENCE :::::::::::::::::::::::::::#
class PmsDailyExpence(models.Model):
    status_choice=(
        ('Pending For Project Manager Approval','Pending For Project Manager Approval'),
        ('Pending For Project Coordinator Approval','Pending For Project Coordinator Approval'),
        ('Pending For HO Approval','Pending For HO Approval'),
        ('Pending For Account Approval','Pending For Account Approval'),
        ('Approve', 'Approve'),
        ('Reject', 'Reject'),
    )
    project = models.ForeignKey(PmsProjects, related_name='daily_exp_proejct',on_delete=models.CASCADE, blank=True, null=True)
    date = models.DateTimeField(blank=True, null=True)
    voucher_no = models.CharField(max_length=50,blank=True,null=True)
    paid_to = models.CharField(max_length=50,blank=True,null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True) 
    document = models.FileField(upload_to=get_directory_path,
                                default=None,
                                blank=True, null=True,
                                validators=[validate_file_extension])
    status = models.CharField(max_length=50,choices=status_choice, null=True, blank=True,default='Pending For Project Manager Approval')
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='p_daily_exp_created_by',on_delete=models.CASCADE, blank=True, null=True)
    owned_by = models.ForeignKey(User, related_name='p_daily_exp_owned_by',on_delete=models.CASCADE, blank=True, null=True)
    updated_by = models.ForeignKey(User, related_name='p_daily_exp_updated_by',on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_paid = models.BooleanField(default=False)
    approve_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    current_level_of_approval = models.CharField(max_length=30,null=True, blank=True,default='Project Manager')

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'pms_daily_expence'


class PmsDailyExpenceItemMapping(models.Model):
    daily_expence = models.ForeignKey(PmsDailyExpence, related_name='p_daily_exp_id',
                                   on_delete=models.CASCADE, blank=True, null=True)
    item = models.TextField(blank=True,null=True)
    created_by = models.ForeignKey(User, related_name='p_daily_exp_map_created_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    owned_by = models.ForeignKey(User, related_name='p_daily_exp_map_owned_by',
                                 on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'pms_daily_expence_item_mapping'

class PmsDailyExpenceApprovalConfiguration(models.Model):
    level_choice = (
        ('Project Manager','Project Manager'),
        ('Project Coordinator', 'Project Coordinator'),
        ('HO', 'HO'),
        ('Account', 'Account'),
        )
    project = models.ForeignKey(PmsProjects, related_name='daily_exp_projects',on_delete=models.CASCADE, blank=True, null=True)
    level = models.CharField(max_length=30,choices=level_choice, null=True, blank=True)
    level_no = models.IntegerField(null=True, blank=True)
    user = models.ForeignKey(User, related_name='daily_exp_approval_user', on_delete=models.CASCADE, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='daily_exp_approval_created_by',on_delete=models.CASCADE, blank=True, null=True)
    updated_by = models.ForeignKey(User, related_name='daily_exp_approval_updated_by', on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(default = datetime.datetime.now)
    updated_at = models.DateTimeField(blank=True,null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'pms_daily_expence_approval_configuration'

class PmsDailyExpenceApproval(models.Model):
    approval_type = (
        ('Pending','Pending'),
        ('Reject', 'Reject'),
        ('Approve', 'Approve'),
        ('Modify', 'Modify'),
        )
    approval_user_level = models.ForeignKey(PmsDailyExpenceApprovalConfiguration, related_name='app_user_con',on_delete=models.CASCADE, blank=True, null=True)
    approval_status = models.CharField(max_length=30,choices=approval_type, null=True, blank=True,default='Pending')
    daily_expence = models.ForeignKey(PmsDailyExpence, related_name='daily_exp_master',on_delete=models.CASCADE, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='daily_exp_created_by',on_delete=models.CASCADE, blank=True, null=True)
    updated_by = models.ForeignKey(User, related_name='daily_exp_updated_by', on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(default = datetime.datetime.now)
    updated_at = models.DateTimeField(blank=True,null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'pms_daily_expence_approval'

class PmsDailyExpenceRemarks(models.Model):
    daily_expence = models.ForeignKey(PmsDailyExpence, related_name='der_daily_id',on_delete=models.CASCADE, blank=True, null=True)
    user = models.ForeignKey(User, related_name='der_user', on_delete=models.CASCADE, blank=True, null=True)
    remarks = models.TextField(blank=True,null=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='der_created_by',on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(default = datetime.datetime.now)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'pms_daily_expence_remarks'