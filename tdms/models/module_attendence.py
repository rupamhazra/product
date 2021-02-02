from django.db import models
from django.contrib.auth.models import User
from dynamic_media import get_directory_path
from django_mysql.models import EnumField
from validators import validate_file_extension
from core.models import TCoreUnit
import datetime
import time
from tdms.models.module_site_location import *

class CustomManager(models.Manager):
    def get_queryset(self):
        return super(__class__, self).get_queryset().filter(is_deleted=False)

class DeleteBaseAbstractStructure(models.Model):
    is_deleted = models.BooleanField(default=False)

    objects = models.Manager()
    cmobjects = CustomManager()
    class Meta:
        abstract = True
    
class CreateBaseAbstractStructure(DeleteBaseAbstractStructure):
    created_at = models.DateTimeField(default=datetime.datetime.now)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name='+')
    class Meta:
        abstract = True 

class UpdateBaseAbstractStructure(CreateBaseAbstractStructure):
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name='+')
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        abstract = True


#:::  ATTENDENCE ::::#

class TdmsAttendance(UpdateBaseAbstractStructure):
    Type_of_attandance= (
        ('single site', 'single site'),
        ('all site', 'all site')
    )
    Type_of_deviation = (('HD', 'half day'),('FD', 'full day'))
    Type_of_leave = (
        ('EL', 'Earned Leave'),
        ('CL', 'Casual Leave'),
        ('SL', 'Sick Leave'),
        ('AB', 'Absent'),
        ('AL', 'All Leave'),
        ('ML', 'Maternity Leave'),
        ('BL', 'Bereavement Leave'),
        ('CVL', 'Covid Leave')
    )

    type = models.IntegerField(choices=Type_of_attandance, null=True, blank=True)
    employee=models.ForeignKey(User, related_name='td_attandance_employee_id',
                                   on_delete=models.CASCADE,blank=True,null=True)
    user_project = models.ForeignKey(TdmsSiteProjectSiteManagement, related_name='td_user_project',
                                   on_delete=models.CASCADE, blank=True, null=True)
    date= models.DateTimeField(auto_now_add=False,blank=True, null=True)
    day_remarks = models.CharField(max_length=200, blank=True, null=True)
    is_present = models.BooleanField(default=False)
    fortnight_deviation_type = models.CharField(max_length=2,choices=Type_of_deviation,blank=True,null=True)
    fortnight_leave_type = models.CharField(max_length=2,choices=Type_of_leave,blank=True,null=True)
    fortnight_day_remarks = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'tdms_attandance'

class TdmsAttandanceLog(UpdateBaseAbstractStructure):
    Type_of_approved = (
    (1, 'pending'),
    (2, 'approved'),
    (3, 'reject'),
    (4, 'regular'),
    )
    Type_of_login_logout = (
    ('Login','Login'),
    ('Logout','Logout'),
    )
    AUTO_OD_CHOICES = ((None,''), (True,'Yes'), (False, 'No'))
    attandance=models.ForeignKey(TdmsAttendance,related_name='td_a_l_attandance_id',on_delete=models.CASCADE,blank=True,null=True)
    login_logout_check = models.CharField(choices=Type_of_login_logout, max_length=20, blank=True, null=True)
    login_id = models.IntegerField(blank=True, null=True)
    time=models.DateTimeField(blank=True, null=True)
    latitude = models.CharField(max_length=200, blank=True, null=True)
    longitude = models.CharField(max_length=200, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    approved_status = models.IntegerField(choices=Type_of_approved, default=4)
    justification = models.TextField(blank=True, null=True)
    remarks=models.TextField(blank=True, null=True)
    is_checkout = models.BooleanField(default=False)
    is_checkout_auto_od = models.BooleanField(default=False)
    device_details = models.TextField(blank=True, null=True)
    token = models.TextField(blank=True, null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'tdms_attandance_log'

class TdmsAttandanceDeviation(UpdateBaseAbstractStructure):
    Type_of_approved = (
        (1, 'pending'),
        (2, 'approved'),
        (3, 'reject'),
        (4, 'regular'),
        (5, 'release'),
    )
    Type_of_deviation = (('OD', 'official duty'),
                     ('HD', 'half day'),
                     ('FD', 'full day'))

    Type_of_leave = (
        ('EL', 'Earned Leave'),
        ('CL', 'Casual Leave'),
        ('SL', 'Sick Leave'),
        ('AB', 'Absent'),
        ('AL', 'All Leave'),
        ('ML', 'Maternity Leave'),
        ('BL', 'Bereavement Leave'),
        ('CVL', 'Covid Leave')
    )

    attandance = models.ForeignKey(TdmsAttendance, related_name='td_a_d_attandance_id',
                                   on_delete=models.CASCADE, blank=True, null=True)
    from_time = models.DateTimeField(blank=True, null=True)
    to_time = models.DateTimeField(blank=True, null=True)
    deviation_time = models.CharField(max_length=10,blank=True, null=True)
    duration = models.IntegerField(null=True, blank=True)
    deviation_type = models.CharField(max_length=2,
                                  choices=Type_of_deviation,blank=True,null=True)
    justification = models.TextField(blank=True, null=True)
    approved_status = models.IntegerField(choices=Type_of_approved, default=4)
    remarks = models.TextField(blank=True, null=True)
    justified_by = models.ForeignKey(User, related_name='td_a_d_justified_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    justified_at = models.DateTimeField(blank=True, null=True)
    approved_by = models.ForeignKey(User, related_name='td_a_d_approved_by',
                                     on_delete=models.CASCADE, blank=True, null=True)
    approved_at = models.DateTimeField(blank=True, null=True)
    
    leave_type = models.CharField(max_length=2,
                                  choices=Type_of_leave,
                                  blank=True,null=True)
    
    is_requested = models.BooleanField(default=False)
    request_date = models.DateTimeField(blank=True, null=True)
    leave_type_changed = models.CharField(max_length=2,
                                  choices=Type_of_leave,
                                  blank=True,null=True)

    leave_type_changed_period = models.CharField(max_length=3,
                                  choices=Type_of_deviation,
                                  blank=True,null=True)
    
    lock_status = models.BooleanField(default=False)
    is_auto_od = models.BooleanField(default=False)
    

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'tdms_attandance_deviation'

class TdmsEmployeeConveyance(UpdateBaseAbstractStructure):
    Type_of_approved = (
        (1, 'pending'),
        (2, 'approved'),
        (3, 'reject'),
    )
    project = models.ForeignKey(TdmsSiteProjectSiteManagement, related_name='td_employee_conveyance_project',
                                     on_delete=models.CASCADE, blank=True, null=True)
    employee = models.ForeignKey(User, related_name='td_employee_conveyance_id',
                                 on_delete=models.CASCADE, blank=True, null=True)
    eligibility_per_day = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    date = models.DateTimeField(blank=True, null=True)
    from_place = models.TextField(blank=True, null=True)
    to_place = models.TextField(blank=True, null=True)
    vechicle_type = models.CharField(max_length=100,blank=True, null=True)
    purpose = models.TextField(blank=True, null=True)
    job_alloted_by = models.ForeignKey(User, related_name='td_employee_conveyance_job_alloted_by',
                                       on_delete=models.CASCADE, blank=True, null=True)
    ammount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    approved_status = models.IntegerField(choices=Type_of_approved, default=1)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'tdms_employee_conveyance'


#:::::::::::::::::::::::::::::::::::PMS EMPLOYEE FOODING:::::::::::::::::::::::::::::::#
class TdmsEmployeeFooding(UpdateBaseAbstractStructure):
    Type_of_approved = (
        (1, 'pending'),
        (2, 'approved'),
        (3, 'reject'),
    )
    attandance = models.ForeignKey(TdmsAttendance, related_name='td_employee_fooding_attandance_id',
                                   on_delete=models.CASCADE, blank=True, null=True)
    ammount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    approved_status = models.IntegerField(choices=Type_of_approved, default=1)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'tdms_employee_fooding'

#:::::::::::::::::::::::::::::::::::PMS EMPLOYEE FOODING:::::::::::::::::::::::::::::::#

class TdmsAttandanceFortnightLeaveDeductionLog(UpdateBaseAbstractStructure):
    Type_of_deviation = (
    	('HD', 'half day'),
    	('FD', 'full day'))

    Type_of_leave = (
        ('EL', 'Earned Leave'),
        ('CL', 'Casual Leave'),
        ('SL', 'Sick Leave'),
        ('AB', 'Absent'),
        ('AL', 'All Leave'),
    )
    sap_personnel_no = models.CharField(max_length=50,blank=True,null=True)
    employee = models.ForeignKey(User, related_name='td_fortnight_employee_id',on_delete=models.CASCADE, blank=True, null=True)
    attendance = models.ForeignKey(TdmsAttendance, related_name='td_fortnight_attandance_id',on_delete=models.CASCADE, blank=True, null=True)
    attendance_date = models.DateField(null=True, blank=True)
    duration = models.IntegerField(null=True, blank=True)
    deviation_type = models.CharField(max_length=2,choices=Type_of_deviation,blank=True,null=True)
    leave_type = models.CharField(max_length=2,choices=Type_of_leave,blank=True,null=True)
    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'tdms_attandance_fortnight_leave_deduction_log'

class TdmsAttandanceLeaveBalanceTransferLog(UpdateBaseAbstractStructure):
    Type_of_deviation = (
    	('HD', 'half day'),
    	('FD', 'full day'))

    Type_of_leave = (
        ('EL', 'Earned Leave'),
        ('CL', 'Casual Leave'),
        ('SL', 'Sick Leave'),
        ('AB', 'Absent'),
        ('AL', 'All Leave'),
    )

    Type_of_approved = (
        (1, 'pending'),
        (2, 'approved'),
        (3, 'reject'),
        (4, 'regular'),
        (5, 'release'),
    )

    sap_personnel_no = models.CharField(max_length=50,blank=True,null=True)
    employee = models.ForeignKey(User, related_name='td_transfer_employee_id',on_delete=models.CASCADE, blank=True, null=True)
    attendance = models.ForeignKey(TdmsAttendance, related_name='td_transfer_attandance_id',on_delete=models.CASCADE, blank=True, null=True)
    attendance_date = models.DateField(null=True, blank=True)
    attendance_deviation = models.ForeignKey(TdmsAttandanceDeviation, related_name='td_transfer_deviation_id',on_delete=models.CASCADE, blank=True, null=True)
    duration = models.IntegerField(null=True, blank=True)
    deviation_type = models.CharField(max_length=2,choices=Type_of_deviation,blank=True,null=True)
    leave_type = models.CharField(max_length=2,choices=Type_of_leave,blank=True,null=True)
    approved_status = models.IntegerField(choices=Type_of_approved, default=2)
    approved_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'tdms_attandance_leave_balance_transfer_log'
