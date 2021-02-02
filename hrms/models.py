from django.db import models
from django.contrib.auth.models import User
from dynamic_media import get_directory_path
from validators import validate_file_extension
from core.models import *
from pms.models import *
# Create your models here.

class HrmsBenefitsProvided(models.Model):
    benefits_name = models.CharField(max_length=200, blank=True, null=True)
    # allowance = models.CharField(max_length=200, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='hr_b_p_created_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    owned_by = models.ForeignKey(User, related_name='hr_b_p_owned_by',
                                 on_delete=models.CASCADE, blank=True, null=True)
    updated_by = models.ForeignKey(User, related_name='hr_b_p_updated_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'hrms_benefits_provided'
        
class HrmsUsersBenefits(models.Model):
    user= models.ForeignKey(User,related_name='hr_u_b_user',
                                   on_delete=models.CASCADE, blank=True, null=True)
    benefits= models.ForeignKey(HrmsBenefitsProvided,related_name='hr_u_b_benefits',
                                   on_delete=models.CASCADE, blank=True, null=True)
    allowance = models.CharField(max_length=200, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='hr_u_b_created_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    owned_by = models.ForeignKey(User, related_name='hr_u_b_owned_by',
                                 on_delete=models.CASCADE, blank=True, null=True)
    updated_by = models.ForeignKey(User, related_name='hr_u_b_updated_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'hrms_users_benefits'

class HrmsUsersOtherFacilities(models.Model):
    user= models.ForeignKey(User,related_name='hr_u_o_f_user',
                                   on_delete=models.CASCADE, blank=True, null=True)
    other_facilities=models.CharField(max_length=200, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='hr_u_o_f_created_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    owned_by = models.ForeignKey(User, related_name='hr_u_o_f_owned_by',
                                 on_delete=models.CASCADE, blank=True, null=True)
    updated_by = models.ForeignKey(User, related_name='hr_u_o_f_updated_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'hrms_users_other_facilities'

class HrmsDocument(models.Model):
    user= models.ForeignKey(User,related_name='hr_d_user',
                                   on_delete=models.CASCADE, blank=True, null=True)
    tab_name= models.CharField(max_length=200, blank=True, null=True)
    field_label=models.CharField(max_length=200, blank=True, null=True)
    document_name= models.CharField(max_length=200, blank=True, null=True)
    document =models.FileField(upload_to=get_directory_path,
                               default=None,
                               blank=True, null=True,
                               validators=[validate_file_extension]
                               )
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='hr_d_created_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    owned_by = models.ForeignKey(User, related_name='hr_d_owned_by',
                                 on_delete=models.CASCADE, blank=True, null=True)
    updated_by = models.ForeignKey(User, related_name='hr_d_updated_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'hrms_document'

class HrmsDynamicSectionFieldLabelDetailsWithDoc(models.Model):
    user= models.ForeignKey(User,related_name='hr_d_s_f_l_d_w_d_user',
                                   on_delete=models.CASCADE, blank=True, null=True)
    tab_name= models.CharField(max_length=200, blank=True, null=True)
    field_label=models.CharField(max_length=200, blank=True, null=True)
    field_label_value=models.CharField(max_length = 200, blank=True, null=True)
    document_name= models.CharField(max_length=200, blank=True, null=True)
    document =models.FileField(upload_to=get_directory_path,
                               default=None,
                               blank=True, null=True,
                               validators=[validate_file_extension]
                               )
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='hr_d_s_f_l_d_w_d_created_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    owned_by = models.ForeignKey(User, related_name='hr_d_s_f_l_d_w_d_owned_by',
                                 on_delete=models.CASCADE, blank=True, null=True)
    updated_by = models.ForeignKey(User, related_name='hr_d_s_f_l_d_w_d_updated_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'hrms_dynamic_section_field_label_details_with_doc'

class HrmsQualificationMaster(models.Model):
    name=models.CharField(max_length=100, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='hr_q_m_created_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    owned_by = models.ForeignKey(User, related_name='hr_q_m_owned_by',
                                 on_delete=models.CASCADE, blank=True, null=True)
    updated_by = models.ForeignKey(User, related_name='hr_q_m_updated_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'hrms_qualification_master'

class HrmsUserQualification(models.Model):
    user=models.ForeignKey(User,related_name='hr_u_q_user',
                                   on_delete=models.CASCADE, blank=True, null=True)
    qualification=models.ForeignKey(HrmsQualificationMaster,related_name='hr_u_q_qualification',
                                   on_delete=models.CASCADE, blank=True, null=True)
    details=models.CharField(max_length=200, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='hr_u_q_created_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    owned_by = models.ForeignKey(User, related_name='hr_u_q_owned_by',
                                 on_delete=models.CASCADE, blank=True, null=True)
    updated_by = models.ForeignKey(User, related_name='hr_u_q_updated_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'hrms_user_qualification'

class HrmsUserQualificationDocument(models.Model):
    user_qualification=models.ForeignKey(HrmsUserQualification,related_name='hr_u_q_d_user_qualification',
                                   on_delete=models.CASCADE, blank=True, null=True)
    document=models.FileField(upload_to=get_directory_path,
                               default=None,
                               blank=True, null=True,
                               validators=[validate_file_extension]
                               )
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='hr_u_q_d_created_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    owned_by = models.ForeignKey(User, related_name='hr_u_q_d_owned_by',
                                 on_delete=models.CASCADE, blank=True, null=True)
    updated_by = models.ForeignKey(User, related_name='hr_u_q_d_updated_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'hrms_user_qualification_document'


#****************************HRMS RECUREMENTS AND ONBOARDING****************************************#


class HrmsNewRequirement(models.Model):

    tab_choice = (
        (1,'New_Requirement'),
        (2,'Requirement_Approval'),
        (3,'Shedule_Interview'),
        (4,'Interview_Status'),
        (5,'candidature_approval'),
        (6,'Completed')
    )

    vacancy_choice = (
            ('new','New'),
            ('replacement','Replacement')
    )

    requirement_type_choice = (
        ('immediate','Immediate'),
        ('standard','Standard')
    )

    age_group_choice = (
        (1,'18-25'),
        (2,'25-32'),
        (3,'32-40'),
        (4,'above 40+')
    )

    gender_choice = (
        ('male','Male'),
        ('female','Female'),
        ('other','other')
    )

    issuing_department = models.ForeignKey(TCoreDepartment,related_name='hr_n_r_department',
                                   on_delete=models.CASCADE, blank=True, null=True)
    date =  models.DateTimeField(blank=True, null=True)
    closing_date =  models.DateTimeField(blank=True, null=True)
    type_of_vacancy = models.CharField(max_length=15,choices=vacancy_choice, default=None)
    type_of_requirement = models.CharField(max_length=15,choices=requirement_type_choice, default=None)
    reason= models.CharField(max_length=200, blank=True, null=True)
    number_of_position = models.IntegerField(blank=True,null=True)
    proposed_designation = models.ForeignKey(TCoreDesignation,related_name='hr_n_r_designation',
                                   on_delete=models.CASCADE, blank=True, null=True)
    location = models.CharField(max_length=100,blank=True,null=True)
    substantiate_justification = models.CharField(max_length=1000,null=True,blank = True)
    document = models.FileField(upload_to=get_directory_path,
                                default=None,
                                null=True,blank=True,
                                validators=[validate_file_extension])

    desired_qualification = models.CharField(max_length=10,blank=True,null=True)
    desired_experience= models.CharField(max_length=10,blank=True,null=True)
    desired_age_group = models.IntegerField(choices=age_group_choice,null=True,blank=True)
    tab_status = models.IntegerField(choices=tab_choice,null=True,blank=True,default=1)
    gender = models.CharField(max_length=15,choices=gender_choice, default=None)
    reporting_to = models.ForeignKey(User,related_name='hr_n_r_reporting_to',
                                   on_delete=models.CASCADE, blank=True, null=True)

    number_of_subordinates = models.IntegerField(blank=True,null=True)
    ctc = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    required_skills = models.CharField(max_length=200,blank=True,null=True)

    level_approval= models.BooleanField(default=False)
    reciever_approval= models.BooleanField(default=False)
    approval_permission_user_level =  models.ForeignKey(PmsApprovalPermissonMatser, related_name='hr_n_r_permission_id',
                                   on_delete=models.CASCADE, blank=True, null=True)

    reciever_remarks = models.CharField(max_length=100,blank=True,null=True)

    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='hr_n_r_created_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    owned_by = models.ForeignKey(User, related_name='hr_n_r_owned_by',
                                 on_delete=models.CASCADE, blank=True, null=True)
    updated_by = models.ForeignKey(User, related_name='hr_n_r_updated_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'hrms_new_requirement'

class HrmsNewRequirementLog(models.Model):

    tab_choice = (
        (1,'New_Requirement'),
        (2,'Requirement_Approval'),
        (3,'Shedule_Interview'),
        (4,'Interview_Status'),
        (5,'candidature_approval'),
        (6,'Completed')
    )

    vacancy_choice = (
            ('new','New'),
            ('replacement','Replacement')
    )

    requirement_type_choice = (
        ('immediate','Immediate'),
        ('standard','Standard')
    )

    age_group_choice = (
        (1,'18-25'),
        (2,'25-32'),
        (3,'32-40'),
        (4,'above 40+')
    )

    gender_choice = (
        ('male','Male'),
        ('female','Female'),
        ('other','other')
    )
    master_hnr = models.ForeignKey(HrmsNewRequirement,related_name='hr_n_r_log_master',
                                   on_delete=models.CASCADE, blank=True, null=True)
    issuing_department = models.ForeignKey(TCoreDepartment,related_name='hr_n_r_log_department',
                                   on_delete=models.CASCADE, blank=True, null=True)
    date =  models.DateTimeField(blank=True, null=True)
    type_of_vacancy = models.CharField(max_length=15,choices=vacancy_choice, default=None)
    type_of_requirement = models.CharField(max_length=15,choices=requirement_type_choice, default=None)
    reason= models.CharField(max_length=200, blank=True, null=True)
    number_of_position = models.IntegerField(blank=True,null=True)
    proposed_designation = models.ForeignKey(TCoreDesignation,related_name='hr_n_r_log_designation',
                                   on_delete=models.CASCADE, blank=True, null=True)
    location = models.CharField(max_length=100,blank=True,null=True)
    substantiate_justification = models.CharField(max_length=1000,null=True,blank = True)
    document = models.FileField(upload_to=get_directory_path,
                                default=None,
                                null=True,blank=True,
                                validators=[validate_file_extension])

    desired_qualification = models.CharField(max_length=10,blank=True,null=True)
    desired_experience= models.CharField(max_length=10,blank=True,null=True)
    desired_age_group = models.IntegerField(choices=age_group_choice,null=True,blank=True)
    tab_status = models.IntegerField(choices=tab_choice,null=True,blank=True,default=1)
    gender = models.CharField(max_length=15,choices=gender_choice, default=None)
    reporting_to = models.ForeignKey(User,related_name='hr_n_r_log_reporting_to',
                                   on_delete=models.CASCADE, blank=True, null=True)

    number_of_subordinates = models.IntegerField(blank=True,null=True)
    ctc = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    required_skills = models.CharField(max_length=200,blank=True,null=True)
    # reciever_approval= models.BooleanField(default=False)
    level_approval= models.BooleanField(default=False)
    approval_permission_user_level =  models.ForeignKey(PmsApprovalPermissonMatser, related_name='hr_n_r_log_permission_id',
                                   on_delete=models.CASCADE, blank=True, null=True)
    # approval_permission_reciver_level =  models.ForeignKey(PmsApprovalPermissonMatser, related_name='hr_n_r_log_permission_rec_id',
    #                             on_delete=models.CASCADE, blank=True, null=True)

    reciever_remarks = models.CharField(max_length=100,blank=True,null=True)
    tag_name = models.CharField(max_length=100,blank=True,null=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='hr_n_r_log_created_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    owned_by = models.ForeignKey(User, related_name='hr_n_r_log_owned_by',
                                 on_delete=models.CASCADE, blank=True, null=True)
    updated_by = models.ForeignKey(User, related_name='hr_n_r_log_updated_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'hrms_new_requirement_log'


class HrmsInterviewType(models.Model):
    name= models.CharField(max_length=100,blank=True,null=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='hr_i_t_created_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    owned_by = models.ForeignKey(User, related_name='hr_i_t_owned_by',
                                 on_delete=models.CASCADE, blank=True, null=True)
    updated_by = models.ForeignKey(User, related_name='hr_i_t_updated_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'hrms_interview_type'

class HrmsInterviewLevel(models.Model):
    name= models.CharField(max_length=100,blank=True,null=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='hr_i_l_created_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    owned_by = models.ForeignKey(User, related_name='hr_i_l_owned_by',
                                 on_delete=models.CASCADE, blank=True, null=True)
    updated_by = models.ForeignKey(User, related_name='hr_i_l_updated_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'hrms_interview_level'

class HrmsScheduleInterview(models.Model):
    action_choice = (
        (1,'approved'),
        (2,'rejected'),
        (3,'OnProcess')
    )
    requirement=models.ForeignKey(HrmsNewRequirement,related_name='hr_s_i_requirement',
                                   on_delete=models.CASCADE, blank=True, null=True)
    candidate_name= models.CharField(max_length=50,blank=True,null=True)
    contact_no= models.CharField(max_length=10,blank=True,null=True,unique=True)
    email= models.EmailField(max_length=70,blank=True,null=True)
    note= models.CharField(max_length=100,blank=True,null=True)
    resume=models.FileField(upload_to=get_directory_path,
                                default=None,
                                null=True,blank=True,
                                validators=[validate_file_extension])
    notice_period = models.CharField(max_length=100,blank=True,null=True)
    expected_ctc = models.IntegerField(blank=True,null=True)
    current_ctc = models.IntegerField(blank=True,null=True)
    action_approval = models.IntegerField(choices=action_choice,null=True,blank=True,default=3)
    level_approval= models.BooleanField(default=False)
    approval_permission_user_level =  models.ForeignKey(PmsApprovalPermissonMatser, related_name='hr_s_i_log_permission_id',
                                   on_delete=models.CASCADE, blank=True, null=True)

    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='hr_s_i_created_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    owned_by = models.ForeignKey(User, related_name='hr_s_i_owned_by',
                                 on_delete=models.CASCADE, blank=True, null=True)
    updated_by = models.ForeignKey(User, related_name='hr_s_i_updated_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'hrms_schedule_interview'

class HrmsScheduleAnotherRoundInterview(models.Model):
    status_choice = (
        (1,'Rescheduled'),
        (2,'On Hold'),
        (3,'Completed'),
        (4,'Cancelled'),
        (5,'On Process')
    )
    schedule_interview=models.ForeignKey(HrmsScheduleInterview,related_name='hr_s_a_r_i_schedule_interview',
                                   on_delete=models.CASCADE, blank=True, null=True)
    planned_date_of_interview= models.DateTimeField(blank=True, null=True)
    planned_time_of_interview= models.TimeField(blank=True, null=True)
    actual_date_of_interview= models.DateTimeField(blank=True, null=True)
    actual_time_of_interview= models.TimeField(blank=True, null=True)
    type_of_interview=models.ForeignKey(HrmsInterviewType,related_name='hr_s_a_r_i_type_of_interview',
                                   on_delete=models.CASCADE, blank=True, null=True)
    level_of_interview=models.ForeignKey(HrmsInterviewLevel,related_name='hr_s_a_r_i_level_of_interview',
                                   on_delete=models.CASCADE, blank=True, null=True)
    interview_status= models.IntegerField(choices=status_choice,null=True,blank=True,default=5)
    is_resheduled = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='hr_s_a_r_i_created_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    owned_by = models.ForeignKey(User, related_name='hr_s_a_r_i_owned_by',
                                 on_delete=models.CASCADE, blank=True, null=True)
    updated_by = models.ForeignKey(User, related_name='hr_s_a_r_i_updated_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'hrms_schedule_another_round_interview'

class HrmsScheduleInterviewLog(models.Model):
    action_choice = (
        (1,'approved'),
        (2,'rejected'),
        (3,'pending')
    )
    hsi_master=models.ForeignKey(HrmsScheduleInterview,related_name='hr_s_i_log_master',
                                   on_delete=models.CASCADE, blank=True, null=True)
    requirement=models.ForeignKey(HrmsNewRequirement,related_name='hr_s_i_log_requirement',
                                   on_delete=models.CASCADE, blank=True, null=True)
    candidate_name= models.CharField(max_length=50,blank=True,null=True)
    contact_no= models.CharField(max_length=10,blank=True,null=True)
    email= models.EmailField(max_length=70,blank=True,null=True)
    note= models.CharField(max_length=100,blank=True,null=True)
    resume=models.FileField(upload_to=get_directory_path,
                                default=None,
                                null=True,blank=True,
                                validators=[validate_file_extension])
    notice_period = models.CharField(max_length=100,blank=True,null=True)
    expected_ctc = models.IntegerField(blank=True,null=True)
    current_ctc = models.IntegerField(blank=True,null=True)
    action_approval = models.IntegerField(choices=action_choice,null=True,blank=True,default=3)
    level_approval= models.BooleanField(default=False)
    approval_permission_user_level =  models.ForeignKey(PmsApprovalPermissonMatser, related_name='hr_s_i_log_log_permission_id',
                                   on_delete=models.CASCADE, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='hr_s_i_log_created_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    owned_by = models.ForeignKey(User, related_name='hr_s_i_log_owned_by',
                                 on_delete=models.CASCADE, blank=True, null=True)
    updated_by = models.ForeignKey(User, related_name='hr_s_i_log_updated_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'hrms_schedule_interview_log'

class HrmsScheduleInterviewWith(models.Model):
    interview=models.ForeignKey(HrmsScheduleAnotherRoundInterview,related_name='hr_s_i_w_interview',
                                   on_delete=models.CASCADE, blank=True, null=True)
    user=models.ForeignKey(User,related_name='hr_s_i_w_user',
                                   on_delete=models.CASCADE, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='hr_s_i_w_created_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    owned_by = models.ForeignKey(User, related_name='hr_s_i_w_owned_by',
                                 on_delete=models.CASCADE, blank=True, null=True)
    updated_by = models.ForeignKey(User, related_name='hr_s_i_w_updated_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'hrms_schedule_interview_with'

class HrmsScheduleInterviewFeedback(models.Model):
    interview=models.ForeignKey(HrmsScheduleAnotherRoundInterview,related_name='hr_s_i_f_interview',
                                   on_delete=models.CASCADE, blank=True, null=True)
    upload_feedback=models.FileField(upload_to=get_directory_path,
                                default=None,
                                null=True,blank=True,
                                validators=[validate_file_extension])
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='hr_s_i_f_created_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    owned_by = models.ForeignKey(User, related_name='hr_s_i_f_owned_by',
                                 on_delete=models.CASCADE, blank=True, null=True)
    updated_by = models.ForeignKey(User, related_name='hr_s_i_f_updated_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'hrms_schedule_interview_feedback'


class HrmsThreeMonthsProbationReviewForm(models.Model):
    option_choice = (
        ('Yes', 'Yes'),
        ('No', 'No')
    )
    employee= models.ForeignKey(User,related_name='prob_user',
                                   on_delete=models.CASCADE, blank=True, null=True)
    how_do_you_like_your_job_as_of_now = models.CharField(choices=option_choice, max_length=15, default='No',blank=True,null=True)
    is_the_work_allotted_to_you_as_per_your_JD = models.CharField(choices=option_choice, max_length=15,default='No',blank=True,null=True)
    what_is_it_that_you_are_working_on = models.CharField(max_length=500, blank=True,null=True)
    have_you_been_explained_the_work_that_you_need_to_do = models.CharField(choices=option_choice,max_length=15, default='No',blank=True,null=True)
    have_you_been_able_to_understand_the_teams_responsibilities = models.CharField(choices=option_choice,max_length=15, default='No',blank=True,null=True)
    have_you_been_given_enough_knowledge_on_your_job_profile = models.CharField(choices=option_choice,max_length=15, default='No',blank=True,null=True)
    do_you_think_you_are_able_to_fit_in_with_the_JD = models.CharField(choices=option_choice, max_length=15,default='No',blank=True,null=True)
    have_you_been_made_aware_of_your_targets_KRAs = models.CharField(choices=option_choice,max_length=15, default='No', blank=True,null=True)
    would_you_want_hr_to_address_any_issue = models.CharField(max_length=500, blank=True,null=True)
    reminder_state = models.IntegerField(default=0)
    first_reminder_date = models.DateTimeField(blank=True,null=True)
    latest_reminder_date = models.DateTimeField(blank=True, null=True)
    submission_pending = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    owned_by = models.ForeignKey(User, related_name='prob_owned_by',
                                 on_delete=models.CASCADE, blank=True, null=True)
    updated_by = models.ForeignKey(User, related_name='prob_updated_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'hrms_three_month_probation_form'
#
class HrmsThreeMonthsProbationReviewForApproval(models.Model):
    status_choice = (
        (1, '0%'),
        (2, '50%'),
        (3, '75%'),
        (4, '100%'),
        (5, 'Difficult to stay')
    )
    option_choice = (
        ('Yes', 'Yes'),
        ('No', 'No')
    )
    employee_form= models.ForeignKey(HrmsThreeMonthsProbationReviewForm,related_name='prob_form',
                                   on_delete=models.CASCADE, blank=True, null=True)
    # the_json = jsonfield.JSONField(blank=True,null=True)
    have_you_given_him_or_her_the_work_that_needs_to_be_done = models.CharField(choices=option_choice, max_length=15, default='No', blank=True, null=True)
    have_you_shared_the_goals_of_the_team_and_organisaton =\
        models.CharField(choices=option_choice, max_length=15, default='No', blank=True, null=True)
    do_you_think_he_or_she_is_a_fine_fitment_to_the_team_and_task = models.CharField(choices=option_choice, max_length=15, default='No', blank=True,null=True)
    fitment_suggestion = models.CharField(max_length=500, blank=True, null=True)
    would_you_call_him_or_her_a_good_hire = models.CharField(choices=option_choice, max_length=15, default='No', blank=True,null=True)
    is_he_a_slow_learner = models.CharField(choices=option_choice, max_length=15, default='No', blank=True, null=True)
    slow_learner_suggestion = models.CharField(max_length=500, blank=True, null=True)
    are_you_satisfied_with_the_response_on_the_work = models.CharField(choices=option_choice, max_length=15, default='No', blank=True,null=True)
    what_would_be_his_chance_of_being_confirmed = models.IntegerField(choices=status_choice, null=True, blank=True)
    would_you_want_hr_to_address_any_issue_with_him_or_her = models.CharField(max_length=500, blank=True, null=True)
    reminder_state = models.IntegerField(default=0)
    first_reminder_date = models.DateTimeField(blank=True, null=True)
    reminder_date = models.DateTimeField(blank=True, null=True)
    submission_pending = models.BooleanField(default=True)
    review_submission_date = models.DateTimeField(null=True,blank=True)
    is_deleted = models.BooleanField(default=False)
    owned_by = models.ForeignKey(User, related_name='rh_owned_by',
                                 on_delete=models.CASCADE, blank=True, null=True)
    updated_by = models.ForeignKey(User, related_name='rh_updated_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'hrms_three_month_probation_review_form'

class HrmsFiveMonthsProbationReviewForm(models.Model):
    employee= models.ForeignKey(User,related_name='prob_five_user',
                                   on_delete=models.CASCADE, blank=True, null=True)

    indicate_any_factor_that_restricted_your_performance = models.CharField(max_length=500, blank=True,null=True)
    any_trainings_that_provide_to_improve_your_performance = models.CharField(max_length=500, blank=True,null=True)
    reminder_state = models.IntegerField(default=0)
    first_reminder_date = models.DateTimeField(blank=True, null=True)
    latest_reminder_date = models.DateTimeField(blank=True, null=True)
    submission_pending = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    owned_by = models.ForeignKey(User, related_name='prob_five_owned_by',
                                 on_delete=models.CASCADE, blank=True, null=True)
    updated_by = models.ForeignKey(User, related_name='prob_five_updated_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'hrms_five_month_probation_form'


class FiveMonthProbationWorkAssignments(models.Model):
    probation = models.ForeignKey(HrmsFiveMonthsProbationReviewForm,related_name='prob_work_assignment',
                                  on_delete=models.CASCADE,blank=True,null=True)
    assignment_no = models.IntegerField(default=0)
    assignment_description = models.CharField(max_length=500,blank=True,null=True)
    is_deleted = models.BooleanField(default=False)
    owned_by = models.ForeignKey(User, related_name='prob_assignment_owned_by',
                                 on_delete=models.CASCADE, blank=True, null=True)
    updated_by = models.ForeignKey(User, related_name='prob_assignment_updated_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'hrms_five_month_probation_assignment'


class FiveMonthProbationAchievements(models.Model):
    probation = models.ForeignKey(HrmsFiveMonthsProbationReviewForm,related_name='prob_achievements',
                                  on_delete=models.CASCADE,blank=True,null=True)
    achievements_no = models.IntegerField(default=0)
    achievements_description = models.CharField(max_length=500,blank=True,null=True)
    is_deleted = models.BooleanField(default=False)
    owned_by = models.ForeignKey(User, related_name='prob_achievements_owned_by',
                                 on_delete=models.CASCADE, blank=True, null=True)
    updated_by = models.ForeignKey(User, related_name='prob_achievements_updated_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'hrms_five_month_probation_achievements'


class HrmsFiveMonthsProbationReviewForApproval(models.Model):
    status_choice = (
        (1, 'Improvement Required'),
        (2, 'Satisfactory '),
        (3, 'Good '),
        (4, 'Excellent ')
    )
    option_choice = (
        ('Yes', 'Yes'),
        ('No', 'No')
    )
    employee_form= models.ForeignKey(HrmsFiveMonthsProbationReviewForm,related_name='prob_five_form',
                                   on_delete=models.CASCADE, blank=True, null=True)
    # the_json = jsonfield.JSONField(blank=True,null=True)
    team_fitment = models.CharField(choices=option_choice, max_length=15, default='No', blank=True, null=True)
    fitment_suggestion = models.CharField(max_length=500, blank=True, null=True)
    good_hire_status = models.CharField(choices=option_choice, max_length=15, default='No', blank=True, null=True)
    progress_appropriate_status = models.CharField(choices=option_choice, max_length=15, default='No', blank=True, null=True)
    satisfied_with_the_response = models.CharField(choices=option_choice, max_length=15, default='No', blank=True, null=True)
    task_given_are_completed_on_time = models.CharField(choices=option_choice, max_length=15, default='No', blank=True, null=True)
    quality_of_work = models.IntegerField(choices=status_choice, null=True, blank=True)
    relations_with_supervisor = models.IntegerField(choices=status_choice, null=True, blank=True)
    cooperation_with_colleagues = models.IntegerField(choices=status_choice,null=True,blank=True)
    fitment_in_your_team = models.IntegerField(choices=status_choice,null=True,blank=True)
    willingness_to_take_up_assignments_or_jobs = models.IntegerField(choices=status_choice, null=True, blank=True)
    competency_in_the_role = models.IntegerField(choices=status_choice, null=True, blank=True)
    trainings_recommended = models.CharField(choices=option_choice, max_length=15, default='No', blank=True, null=True)
    recommended_training = models.CharField(max_length=500, blank=True, null=True)
    to_be_confirmed = models.CharField(choices=option_choice, max_length=15, default='No', blank=True, null=True)
    reminder_state = models.IntegerField(default=0)
    first_reminder_date = models.DateTimeField(blank=True, null=True)
    reminder_date = models.DateTimeField(blank=True, null=True)
    submission_pending = models.BooleanField(default=True)
    review_submission_date = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    owned_by = models.ForeignKey(User, related_name='rh_five_owned_by',
                                 on_delete=models.CASCADE, blank=True, null=True)
    updated_by = models.ForeignKey(User, related_name='rh_five_updated_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'hrms_five_month_probation_review_form'

class HrmsIntercom(models.Model):
    floor = models.ForeignKey(TCoreFloor, related_name='floor_id',on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=200, blank=True, null=True)
    ext_no = models.CharField(max_length=10,blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='hr_in_created_by',on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, related_name='rh_in_updated_by',on_delete=models.CASCADE, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'hrms_intercom'
    
class PreJoiningCandidateData(models.Model):
    attendance_choice_type = (('HRMS', 'HRMS'),
                              ('PMS', 'PMS'),
                              ('CRM', 'CRM'),
                              ('Manual', 'Manual')
                             )

    term_insurence_coverage_choice_type = (
                                            ('2 years','2 years'),
                                            ('3 years','3 years'),
                                            ('4 yaers','4 years'),
                                            ('5 years','5 yaers')
                                            )

    pay_roll_type = (
        ('on payroll' , 'on payroll'),
        ('off payroll' , 'off payroll')
    )
    prejoin_approval_status_choice = (
        ('Pending', 'Pending'),
        ('BGV in progress', 'BGV in progress'),
        ('BGV completed', 'BGV completed'),
        ('Pre-joining documentation in progress', 'Pre-joining documentation in progress'),
        ('Pre-joining documentation completed', 'Pre-joining documentation completed'),
        ('Resource allocation in progress', 'Resource allocation in progress'),
        ('Resource allocation completed', 'Resource allocation completed'),
        ('Candidate yet to join', 'Candidate yet to join')
    )

    def increment_candidate_id():
        last_candidate_id = PreJoiningCandidateData.objects.all().order_by('id').last()
        if not last_candidate_id:
            return 'CAN0001'
        candidate_id = last_candidate_id.candidate_id
        candidate_int = int(candidate_id.split('CAN')[-1])
        width = 4
        new_candidate_int = candidate_int + 1
        formatted = (width - len(str(new_candidate_int))) * "0" + str(new_candidate_int)
        new_candidate_id = 'CAN' + str(formatted)
        return new_candidate_id

    candidate_id = models.CharField(max_length=500,default=increment_candidate_id,null=True, blank=True)
    candidate_first_name = models.CharField(max_length = 255, blank=True,null=True)
    candidate_last_name = models.CharField(max_length = 255, blank=True,null=True)
    contact_no = models.CharField(max_length = 15, blank=True,null=True)
    email_id = models.EmailField(max_length=70,blank=True,null=True)
    department = models.ForeignKey(TCoreDepartment,on_delete=models.CASCADE,related_name='on_boarding_department',blank=True,null=True)
    sub_department = models.ForeignKey(TCoreDepartment,on_delete=models.CASCADE,related_name='on_boarding_sub_department',blank=True,null=True)
    designation=models.ForeignKey(TCoreDesignation,on_delete=models.CASCADE,related_name='on_boarding_designation',blank=True,null=True)
    company = models.ForeignKey(TCoreCompany, on_delete=models.CASCADE, related_name='transfer_on_boarding_company', blank=True,null=True)
    hod = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transfer_on_boarding_hod', blank=True, null=True)
    reporting_head = models.ForeignKey(User, on_delete=models.CASCADE, related_name='on_boarding_reporting_head', blank=True,null=True)
    employee_grade = models.ForeignKey(TCoreGrade, on_delete=models.CASCADE, related_name='employee_grade',blank=True,null=True)
    employee_sub_grade = models.ForeignKey(TCoreSubGrade, on_delete=models.CASCADE, related_name='employee_sub_grade', blank=True,null=True)
    salary_type = models.ForeignKey(TCoreSalaryType, on_delete=models.CASCADE, related_name='on_boarding_salary_type',blank=True,null=True)
    cost_centre=models.ForeignKey(TCoreCompanyCostCentre,on_delete=models.CASCADE,related_name='on_boarding_cost_center',blank=True,null=True)
    location = models.ForeignKey(TCoreState, on_delete=models.CASCADE, related_name='can_job_location',blank=True,null=True)
    attendance_type = models.CharField(choices=attendance_choice_type, max_length=15, blank=True, null=True)
    payroll_Type = models.CharField(choices=pay_roll_type, max_length=15, blank=True, null=True)
    eligiblity_for_pf = models.BooleanField(default=False)
    applicable_for_esic = models.BooleanField(default=False)
    seat_no = models.CharField(max_length = 25, blank=True,null=True)
    expected_joining_date = models.DateTimeField(blank=True, null=True)
    term_insurence = models.BooleanField(default=False)
    term_insurence_coverage = models.CharField(choices=term_insurence_coverage_choice_type, default=None, max_length=15, blank=True, null=True)
    eligible_for_bgv = models.BooleanField(default=False)
    aadhar_card_no = models.CharField(max_length=12, blank=True, null=True)
    upload_aadhar_card = models.ImageField(upload_to=get_directory_path, default=None,null=True, blank=True)
    pan_no = models.CharField(max_length=12, blank=True, null=True)
    upload_pan = models.ImageField(upload_to=get_directory_path, default=None,null=True, blank=True)
    bank_name = models.ForeignKey(TCoreBank, on_delete=models.CASCADE, related_name='candidate_bank_name',blank=True,null=True)
    bank_account_number= models.CharField(max_length=15, blank=True, null=True)
    branch_name = models.CharField(max_length=30, blank=True, null=True)
    prejoin_approval_status = models.CharField(max_length=30, choices=prejoin_approval_status_choice, null=True, blank=True,
                                              default='Pending')
    ifsc_code = models.CharField(max_length=15, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pre_joining_data_created_by', blank=True,
                                   null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pre_joining_data_updated_by', blank=True,
                                   null=True)
    deleted_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    deleted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pre_joining_data_deleted_by', blank=True,
                                   null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'pre_joining_candidate_onset'


class PreJoineeResourceAllocation(models.Model):
    facility_choice = (
        ('Laptop', 'Laptop'),
        ('Desktop', 'Desktop'),
        ('Mobile Phone', 'Mobile Phone'),
        ('Sim', 'Sim'),
        ('Dongle', 'Dongle'),
        ('Stationary (Basic)', 'Stationary (Basic)'),
        ('Stationary (Advanced)', 'Stationary (Advanced)'),
        ('Email', 'Email'),
        ('EPBAX', 'EPBAX'),
        ('SAP Access', 'SAP Access'),
        ('CRM', 'CRM'),
        ('Vendor Code','Vendor Code')
    )
    status_choice = (
        ('Open', 'Open'),
        ('Closed', 'Closed'),
        ('Completed', 'Completed'),
        ('In Progress', 'In Progress')
    )

    employee = models.ForeignKey(PreJoiningCandidateData, on_delete=models.CASCADE, related_name='prejoinee_employee',blank=True,null=True)
    # facility = models.ForeignKey(TCoreResource, on_delete=models.CASCADE,related_name='pre_facility',blank=True,null=True)
    expected_date_of_joining = models.DateTimeField(blank=True, null=True)
    facility_details = models.CharField(max_length=30, choices=facility_choice, null=True, blank=True, default='Laptop')
    responsible_department = models.ForeignKey(TCoreDepartment, on_delete=models.CASCADE,related_name='pre_department',blank=True,null=True)
    status = models.CharField(max_length=30, choices=status_choice, null=True, blank=True, default='Open')
    actual_date_of_assignation = models.DateTimeField(blank=True, null=True)
    expected_date_of_assignation = models.DateTimeField(blank=True, null=True)
    comment = models.CharField(max_length=255, blank=True, null=True)
    reminder_state = models.IntegerField(default=0)
    first_reminder_date = models.DateTimeField(blank=True, null=True)
    latest_reminder_date = models.DateTimeField(blank=True, null=True)
    submission_pending = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resource_created_by',
                                   blank=True,
                                   null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resource_updated_by',
                                   blank=True,
                                   null=True)
    deleted_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    deleted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resource_deleted_by',
                                   blank=True,
                                   null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'pre_joinee_resource_allocation'

class EmployeeMediclaimDetails(models.Model):
    GENDER = (('male','male'),
            ('female','female'),
            ('others','others'))
    marital_status_type = (('Married', 'Married'),
                           ('Single', 'Single'),
                           )

    employee = models.ForeignKey(User,related_name='employee_office_details_for_mediclaim',on_delete=models.CASCADE,blank=True,null=True)
    spouse_name = models.CharField(max_length=255, blank=True, null=True)
    marital_status = models.CharField(choices = marital_status_type,max_length = 15,blank=True,null=True)
    spouse_gender = models.CharField(max_length=30, choices=GENDER, null=True, blank=True)
    spouse_dob = models.DateField(max_length=8, default=None, blank=True,null=True)
    first_child_name = models.CharField(max_length=255, blank=True, null=True)
    first_child_gender = models.CharField(max_length=30, choices=GENDER, null=True, blank=True)
    first_child_dob = models.DateField(max_length=8, default=None, blank=True,null=True)
    second_child_name = models.CharField(max_length=255, blank=True, null=True)
    second_child_gender = models.CharField(max_length=30, choices=GENDER, null=True, blank=True)
    second_child_dob = models.DateField(max_length=8, default=None, blank=True,null=True)
    include_parents = models.BooleanField(default=False)
    father_name = models.CharField(max_length=255, blank=True, null=True)
    father_dob = models.DateField(max_length=8, default=None, blank=True,null=True)
    mother_name = models.CharField(max_length=255, blank=True, null=True)
    mother_dob = models.DateField(max_length=8, default=None, blank=True,null=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mediclaim_created_by',
                                   blank=True,
                                   null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mediclaim_updated_by',
                                   blank=True,
                                   null=True)
    deleted_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    deleted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mediclaim_deleted_by',
                                   blank=True,
                                   null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'employee_mediclaim_details'


class MediclaimEnableTimeFrame(models.Model):
    start_time = models.DateTimeField(default=None, blank=True, null=True)
    end_time = models.DateTimeField(default=None, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mediclaim_enable_created_by',
                                   blank=True,
                                   null=True)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mediclaim_enable_updated_by',
                                   blank=True,
                                   null=True)
    deleted_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    deleted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mediclaim_enable_deleted_by',
                                   blank=True,
                                   null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'employee_mediclaim_editable'