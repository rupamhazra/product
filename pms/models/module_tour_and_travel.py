from django.db import models
from django.contrib.auth.models import User
from dynamic_media import get_directory_path
#from django_mysql.models import EnumField
from validators import validate_file_extension
from pms.models import PmsProjects
import  datetime


class PmsTourAndTravelExpenseMaster(models.Model):
    
    status_choice=((1,'starting'),
                    (2,'pending'),
                    (3,'completed'),
                    )
    status_choice_check = (
        ('Pending For Project Manager Approval', 'Pending For Project Manager Approval'),
        ('Pending For Project Coordinator Approval', 'Pending For Project Coordinator Approval'),
        ('Pending For HO Approval', 'Pending For HO Approval'),
        ('Pending For Account Approval', 'Pending For Account Approval'),
        ('Approve', 'Approve'),
        ('Reject', 'Reject'),
    )
    type_of_user=((1,'employee'),
                    (2,'guest'))
    type_of_approved_status=((1,'approve'),
                             (2,'reject'),
                             (3,'modification'))

    travel_stage_status=models.IntegerField(choices=status_choice, null=True, blank=True,default=1)
    project = models.ForeignKey(PmsProjects, related_name='tour_exp_proejct', on_delete=models.CASCADE, blank=True,
                                null=True)
    status = models.CharField(max_length=50, choices=status_choice_check, null=True, blank=True,
                              default='Pending For Project Manager Approval')

    company_name=models.CharField(max_length=200, blank=True, null=True)
    paid_to = models.CharField(max_length=50, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    user_type=models.IntegerField(choices=type_of_user,null=True,blank=True)
    employee= models.ForeignKey(User, related_name='t_a_t_e_m_employee_name',
                                   on_delete=models.CASCADE, blank=True, null=True)
    branch_name = models.CharField(max_length=30, blank=True, null=True)
    guest= models.CharField(max_length=200, blank=True, null=True)                              
    journey_number=models.TextField(blank=True, null=True)
    booking_date=models.DateTimeField(blank=True, null=True)
    booking_by=models.CharField(max_length=200, blank=True, null=True)
    place_of_travel=models.CharField(max_length=200, blank=True, null=True)
    from_date=models.DateTimeField(blank=True, null=True)
    to_date=models.DateTimeField(blank=True, null=True)
    non=models.CharField(max_length=200, blank=True, null=True)
    extra_day=models.IntegerField(blank=True, null=True)
    approved_status=models.IntegerField(choices=type_of_approved_status,null=True,blank=True)
    request_modification=models.TextField(blank=True,null=True)
    total_expense= models.DecimalField(max_digits=10,decimal_places=2,blank=True,null=True)
    limit_exceed_by=models.DecimalField(max_digits=10,decimal_places=2,blank=True,null=True)
    total_flight_fare=models.DecimalField(max_digits=10,decimal_places=2,blank=True,null=True)
    advance=models.DecimalField(max_digits=10,decimal_places=2,blank=True,null=True)
    is_deleted = models.BooleanField(default=False)
    current_level_of_approval = models.CharField(max_length=30, null=True, blank=True, default='Project_Manager')
    created_by = models.ForeignKey(User, related_name='t_a_t_e_m_created_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    updated_by = models.ForeignKey(User, related_name='t_a_t_e_m_updated_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    owned_by = models.ForeignKey(User, related_name='t_a_t_e_m_owned_by',
                                 on_delete=models.CASCADE, blank=True, null=True)
    is_paid = models.BooleanField(default=False)
    approve_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)
    class Meta:
        db_table = 'pms_tour_and_travel_expense_master'


class PmsTourAndTravelExpenseApprovalStatus(models.Model):
    level_choice = (
        ('Project Manager','Project Manager'),
        ('Project Coordinator', 'Project Coordinator'),
        ('HO', 'HO'),
        ('Account', 'Account'),
        )
    approval_type = (
        ('Pending', 'Pending'),
        ('Reject', 'Reject'),
        ('Approve', 'Approve'),
        ('Modify', 'Modify'),
    )
    tour = models.ForeignKey(PmsTourAndTravelExpenseMaster, related_name='tour_exp_master',on_delete=models.CASCADE, blank=True, null=True)
    level = models.CharField(max_length=30,choices=level_choice, null=True, blank=True)
    level_no = models.IntegerField(null=True, blank=True)
    approval_status = models.CharField(max_length=30, choices=approval_type, null=True, blank=True, default='Pending')
    comment = models.CharField(max_length=200,null=True,blank=True)
    user = models.ForeignKey(User, related_name='tour_exp_approval_user', on_delete=models.CASCADE, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='tour_exp_approval_created_by',on_delete=models.CASCADE, blank=True, null=True)
    updated_by = models.ForeignKey(User, related_name='tour_exp_approval_updated_by', on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(default = datetime.datetime.now)
    updated_at = models.DateTimeField(auto_now=True, blank=True,null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'tour_expense_approval_configuration'

class PmsTourAndTravelRemarks(models.Model):
    level_choice = (
        ('Project Manager', 'Project Manager'),
        ('Project Coordinator', 'Project Coordinator'),
        ('HO', 'HO'),
        ('Account', 'Account'),
        ('Payment', 'Payment'),
    )

    tour = models.ForeignKey(PmsTourAndTravelExpenseMaster, related_name='tour_remark_exp_master',on_delete=models.CASCADE, blank=True, null=True)
    level = models.CharField(max_length=30,choices=level_choice, null=True, blank=True)
    comment = models.CharField(max_length=200,null=True,blank=True)
    user = models.ForeignKey(User, related_name='tour_remark_exp_approval_user', on_delete=models.CASCADE, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='tour_remark_exp_approval_created_by',on_delete=models.CASCADE, blank=True, null=True)
    updated_by = models.ForeignKey(User, related_name='tour_remark_exp_approval_updated_by', on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(default = datetime.datetime.now)
    updated_at = models.DateTimeField(auto_now=True, blank=True,null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'tour_remark_expense_approval_configuration'

class PmsTourAndTravelEmployeeDailyExpenses(models.Model):
    expenses_master = models.ForeignKey(PmsTourAndTravelExpenseMaster,related_name='t_a_t_e_d_e_expenses_master',
                                   on_delete=models.CASCADE, blank=True, null=True)
    date = models.DateTimeField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    fare = models.DecimalField(max_digits=10,decimal_places=2,blank=True,null=True)
    local_conveyance = models.DecimalField(max_digits=10,decimal_places=2,blank=True,null=True)
    lodging_expenses = models.DecimalField(max_digits=10,decimal_places=2,blank=True,null=True)
    fooding_expenses = models.DecimalField(max_digits=10,decimal_places=2,blank=True,null=True)
    da = models.DecimalField(max_digits=10,decimal_places=2,blank=True,null=True)
    other_expenses = models.DecimalField(max_digits=10,decimal_places=2,blank=True,null=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='t_a_t_e_d_e_created_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    updated_by = models.ForeignKey(User, related_name='t_a_t_e_d_e_updated_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    owned_by = models.ForeignKey(User, related_name='t_a_t_e_d_e_owned_by',
                                 on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)
    class Meta:
        db_table = 'pms_tour_and_travel_employee_daily_expenses'

class TravelEmployeeDocument(models.Model):
    # tour_and_travel_session_id used to maintaine the relationship with all the table related to tour and travel expences
    tour_and_travel_session_id = models.IntegerField(blank=True, null=True)
    type = models.CharField(max_length=100,blank=True, null=True)
    document = models.FileField(upload_to=get_directory_path,
                                default=None,
                                blank=True, null=True,
                                validators=[validate_file_extension])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'pms_tour_and_travel_document'

class PmsTourAndTravelEmployeeDailyExpensesDocument(models.Model):
    pms_daily_expense = models.ForeignKey(PmsTourAndTravelEmployeeDailyExpenses,related_name='pms_daily_expenses',
                                   on_delete=models.CASCADE, blank=True, null=True)
    fare_document = models.FileField(upload_to=get_directory_path,
                                     default=None,
                                     blank=True, null=True,
                                     validators=[validate_file_extension])
    local_conveyance_document = models.FileField(upload_to=get_directory_path,
                                                 default=None,
                                                 blank=True, null=True,
                                                 validators=[validate_file_extension])
    lodging_expenses_document = models.FileField(upload_to=get_directory_path,
                                                 default=None,
                                                 blank=True, null=True,
                                                 validators=[validate_file_extension])
    fooding_expenses_document = models.FileField(upload_to=get_directory_path,
                                                 default=None,
                                                 blank=True, null=True,
                                                 validators=[validate_file_extension])
    da_document = models.FileField(upload_to=get_directory_path,
                                   default=None,
                                   blank=True, null=True,
                                   validators=[validate_file_extension])
    other_expenses_document = models.FileField(upload_to=get_directory_path,
                                               default=None,
                                               blank=True, null=True,
                                               validators=[validate_file_extension])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)
    class Meta:
        db_table = 'pms_tour_and_travel_employee_daily_expenses_document'
    
class PmsTourAndTravelVendorOrEmployeeDetails(models.Model):
    type_of_approved_status=((1,'approve'),
                             (2,'reject'),
                             (3,'modification'))
    type_of_vendor_or_employee=((1,'vendor'),
                            (2,'employee'))
    expenses_master = models.ForeignKey(PmsTourAndTravelExpenseMaster,related_name='t_a_t_v_o_e_d_expenses_master',
                                   on_delete=models.CASCADE, blank=True, null=True)
    bill_number = models.CharField(max_length=200, blank=True, null=True)
    employee_or_vendor_type=models.IntegerField(choices=type_of_vendor_or_employee,null=True,blank=True) 
    empolyee_or_vendor_id=models.IntegerField(blank=True,null=True)
    bill_amount = models.DecimalField(max_digits=10,decimal_places=2,blank=True,null=True)
    advance_amount = models.DecimalField(max_digits=10,decimal_places=2,blank=True,null=True)
    approved_status=models.IntegerField(choices=type_of_approved_status,null=True,blank=True)
    request_modification=models.TextField(blank=True,null=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='t_a_t_v_o_e_d_created_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    updated_by = models.ForeignKey(User, related_name='t_a_t_v_o_e_d_updated_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    owned_by = models.ForeignKey(User, related_name='t_a_t_v_o_e_d_owned_by',
                                 on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)
    class Meta:
        db_table = 'pms_tour_and_travel_vendor_or_employee_details'

class PmsTourAndTravelBillReceived(models.Model):
    type_of_approved_status=((1,'approve'),
                             (2,'reject'),
                             (3,'modification'))
    type_of_vendor_or_employee=((1,'vendor'),
                            (2,'employee'))
    expenses_master = models.ForeignKey(PmsTourAndTravelExpenseMaster,related_name='t_a_t_b_r_expenses_master',
                                   on_delete=models.CASCADE, blank=True, null=True)
    date = models.DateTimeField(blank=True, null=True)
    parking_expense = models.DecimalField(max_digits=10,decimal_places=2,blank=True,null=True)
    posting_expense = models.DecimalField(max_digits=10,decimal_places=2,blank=True,null=True)
    employee_or_vendor_type=models.IntegerField(choices=type_of_vendor_or_employee,null=True,blank=True) 
    empolyee_or_vendor_id=models.IntegerField(blank=True,null=True)
    less_amount =models.DecimalField(max_digits=10,decimal_places=2,blank=True,null=True)
    cgst = models.DecimalField(max_digits=20,decimal_places=2,blank=True,null=True)
    sgst = models.DecimalField(max_digits=20,decimal_places=2,blank=True,null=True)
    igst =models.DecimalField(max_digits=20,decimal_places=2,blank=True,null=True)
    document_number = models.CharField(max_length=200, blank=True, null=True)
    cost_center_number = models.CharField(max_length=200, blank=True, null=True)
    net_expenditure = models.DecimalField(max_digits=10,decimal_places=2,blank=True,null=True)
    advance_amount=models.DecimalField(max_digits=10,decimal_places=2,blank=True,null=True)
    fare_and_conveyance=models.DecimalField(max_digits=10,decimal_places=2,blank=True,null=True)
    lodging_fooding_and_da=models.DecimalField(max_digits=10,decimal_places=2,blank=True,null=True)
    expense_mans_per_day=models.DecimalField(max_digits=10,decimal_places=2,blank=True,null=True)
    total_expense = models.DecimalField(max_digits=10,decimal_places=2,blank=True,null=True)
    limit_exceeded_by =  models.DecimalField(max_digits=10,decimal_places=2,blank=True,null=True)
    remarks = models.TextField(blank=True, null=True)
    approved_status=models.IntegerField(choices=type_of_approved_status,null=True,blank=True)
    request_modification=models.TextField(blank=True,null=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='t_a_t_b_r_created_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    updated_by = models.ForeignKey(User, related_name='t_a_t_b_r_updated_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    owned_by = models.ForeignKey(User, related_name='t_a_t_b_r_owned_by',
                                 on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)
    class Meta:
        db_table = 'pms_tour_and_travel_bill_received'

class PmsTourAndTravelWorkSheetFlightBookingQuotation(models.Model):
    type_of_booking_quotations=((1,'onward_journey'),
                            (2,'return_journey'))
    expenses_master = models.ForeignKey(PmsTourAndTravelExpenseMaster,
                                        related_name='t_a_t_w_s_f_b_q_expenses_master',
                                        on_delete=models.CASCADE, blank=True, null=True)
    flight_booking_quotation_type=models.IntegerField(choices=type_of_booking_quotations, null=True, blank=True)
    date = models.DateField(blank=True, null=True)
    sector= models.CharField(max_length=200, blank=True, null=True)
    airline= models.CharField(max_length=200, blank=True, null=True)
    flight_number=models.CharField(max_length=200, blank=True, null=True)
    time=models.TimeField(blank=True, null=True)
    corporate_fare_agent_1=models.DecimalField(max_digits=10,decimal_places=2,blank=True,null=True)
    corporate_fare_agent_2= models.DecimalField(max_digits=10,decimal_places=2,blank=True,null=True)
    retail_fare_agent_1= models.DecimalField(max_digits=10,decimal_places=2,blank=True,null=True)
    retail_fare_agent_2= models.DecimalField(max_digits=10,decimal_places=2,blank=True,null=True)
    airline_fare= models.DecimalField(max_digits=10,decimal_places=2,blank=True,null=True)
    others=models.TextField(blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='t_a_t_w_s_f_b_q_created_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    updated_by = models.ForeignKey(User, related_name='t_a_t_w_s_f_b_q_updated_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    owned_by = models.ForeignKey(User, related_name='t_a_t_w_s_f_b_q_owned_by',
                                 on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return str(self.id)
    class Meta:
        db_table = 'pms_tour_and_travel_work_sheet_flight_booking_quotation'

class PmsTourAndTravelFinalBookingDetails(models.Model):
    type_of_approved_status=((1,'approve'),
                             (2,'reject'),
                             (3,'modification'))
    type_of_vendor_or_employee=((1,'vendor'),
                            (2,'employee'))
    expenses_master = models.ForeignKey(PmsTourAndTravelExpenseMaster,
                                        related_name='t_a_t_f_b_d_expenses_master',
                                        on_delete=models.CASCADE, blank=True, null=True)
    employee_or_vendor_type=models.IntegerField(choices=type_of_vendor_or_employee,null=True,blank=True)
    empolyee_or_vendor_id=models.IntegerField(blank=True,null=True)
    date_of_journey=models.DateField(blank=True, null=True)
    time=models.TimeField(blank=True, null=True)
    flight_no=models.CharField(max_length=200, blank=True, null=True)
    travel_sector=models.CharField(max_length=200, blank=True, null=True)
    number_of_persons=models.IntegerField( blank=True, null=True)
    rate_per_person= models.DecimalField(max_digits=15,decimal_places=2,blank=True,null=True)
    total_cost= models.DecimalField(max_digits=15,decimal_places=2,blank=True,null=True)
    approved_status=models.IntegerField(choices=type_of_approved_status,null=True,blank=True)
    request_modification=models.TextField(blank=True,null=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='t_a_t_f_b_d_created_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    updated_by = models.ForeignKey(User, related_name='t_a_t_f_b_d_updated_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    owned_by = models.ForeignKey(User, related_name='t_a_t_f_b_d_owned_by',
                                 on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)
    class Meta:
        db_table = 'pms_tour_and_travel_final_booking_details'

class PmsTourAndTravelApprovalIntervalDaysMailOrNotificationConf(models.Model):
    level_choice = (
        ('Project Manager','Project Manager'),
        ('Project Coordinator', 'Project Coordinator'),
        ('HO', 'HO'),
        ('Account', 'Account'),
        )
    level = models.CharField(max_length=30,choices=level_choice, null=True, blank=True)
    level_no = models.IntegerField(null=True, blank=True)
    action_interval_days = models.IntegerField(null=True, blank=True)
    pending_interval_days = models.IntegerField(null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name='tour_days_con_updated_by', on_delete=models.CASCADE, blank=True, null=True)
    updated_at = models.DateTimeField(default = datetime.datetime.now)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'pms_tour_travel_approval_interval_days_mail_or_notification_conf'
