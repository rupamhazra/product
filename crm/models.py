from django.db import models
from django.contrib.auth.models import User
from dynamic_media import get_directory_path
from validators import validate_file_extension
from datetime import datetime
from core.models import (TCoreCountry, TCoreCurrency, TCoreDomain)


class CustomManager(models.Manager):
    def get_queryset(self):
        return super(__class__, self).get_queryset().filter(is_deleted=False)


class BaseAbstractStructure(models.Model):
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name='+')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    cmobjects = CustomManager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        super(__class__, self).save(*args, **kwargs)


class CrmDocument(BaseAbstractStructure):
    MODEL_TYPE_CHOICE = (
        (1, 'CrmOpportunity'),
        (2, 'CrmOpportunityPresaleLog'),
        (3, 'CrmProject'),
        (4, 'CrmChangeRequest'),
        (5, 'CrmLeadDocument')
    )
    FIELD_TYPE_CHOICE = (
        (1, 'scope_of_work'),
        (2, 'business_proposal'),
        (3, 'customer_consent'),
        (4, 'cr_document'),
        (5, 'lead_document')
    )
    name = models.CharField(max_length=250, blank=True, null=True)
    document = models.FileField(upload_to=get_directory_path, default=None, blank=True, null=True,
                                        validators=[validate_file_extension])
    #model_type = models.IntegerField(choices=MODEL_TYPE_CHOICE, blank=True, null=True)
    #model_obj_id = models.IntegerField(blank=True, null=True)
    #field_type = models.IntegerField(choices=FIELD_TYPE_CHOICE, blank=True, null=True)

    class Meta:
        db_table = 'crm_document'


class CrmColorStatus(BaseAbstractStructure):
    name = models.CharField(max_length=50, blank=True, null=True)
    hex = models.CharField(max_length=10, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'crm_color_status'


class CrmTask(BaseAbstractStructure):
    name = models.TextField(blank=True, null=True)
    date_time = models.DateTimeField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    is_completed = models.BooleanField(default=False)

    class Meta:
        db_table = 'crm_task'


class CrmCeleryRevoke(BaseAbstractStructure):
    TYPE_CHOICE = (
        (1, 'task'),
    )
    celery_id = models.CharField(max_length=500, blank=True, null=True)
    type = models.IntegerField(choices=TYPE_CHOICE, blank=True, null=True)
    type_id = models.IntegerField(blank=True, null=True)
    is_revoked = models.BooleanField(default=False)

    class Meta:
        db_table = 'crm_celery_revoke'


class CrmTechnology(BaseAbstractStructure):
    name = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        db_table = 'crm_technology'


class CrmDepartment(BaseAbstractStructure):
    name = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        db_table = 'crm_department'


class CrmPaymentMode(BaseAbstractStructure):
    name = models.CharField(max_length=250, blank=True, null=True)

    class Meta:
        db_table = 'crm_payment_mode'


class CrmSource(BaseAbstractStructure):
    name = models.CharField(max_length=250, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'crm_source'


class CrmResource(BaseAbstractStructure):
    name = models.CharField(max_length=250, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'crm_resource'


class CrmDocumentTag(BaseAbstractStructure):
    name = models.CharField(max_length=250, blank=True, null=True)
    is_deletable = models.BooleanField(default=True)
    is_editable = models.BooleanField(default=True)

    class Meta:
        db_table = 'crm_document_tag'


class CrmPoc(BaseAbstractStructure):
    SALUTATION_CHOICE = (
        (1, 'Mr.'),
        (2, 'Ms.'),
        (3, 'Mrs.'),
        (4, 'Other')
    )
    salutation = models.IntegerField(choices=SALUTATION_CHOICE, blank=True, null=True)
    first_name = models.CharField(max_length=250, blank=True, null=True)
    last_name = models.CharField(max_length=250, blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    mobile = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(max_length=250, blank=True, null=True)
    job_title = models.CharField(max_length=250, blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    url = models.CharField(max_length=500, blank=True, null=True)
    country = models.ForeignKey(TCoreCountry, on_delete=models.CASCADE, related_name='crm_poc_country', blank=True, null=True)
    source = models.ForeignKey(CrmSource, on_delete=models.CASCADE, related_name='crm_poc_source', blank=True, null=True)

    class Meta:
        db_table = 'crm_poc'


class CrmChangeRequest(BaseAbstractStructure):
    cr_no = models.IntegerField(default=1)
    name = models.CharField(max_length=250, blank=True, null=True)
    value = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    man_hours = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    cr_document = models.ForeignKey(CrmDocument, on_delete=models.CASCADE, related_name='crm_change_request_document', blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'crm_change_request'


class CrmMilestone(BaseAbstractStructure):
    name = models.CharField(max_length=250, blank=True, null=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    is_paid = models.BooleanField(default=False)
    percentage = models.IntegerField(default=0)
    description = models.TextField(blank=True, null=True)
    value = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    tentative_date = models.DateTimeField(blank=True, null=True)
    due_date = models.DateTimeField(blank=True, null=True)
    invoiced = models.BooleanField(default=False)
    invoice_date = models.DateTimeField(blank=True, null=True)
    invoice_no = models.CharField(max_length=50, blank=True, null=True)
    mode_of_payment = models.ForeignKey(CrmPaymentMode, on_delete=models.CASCADE,related_name='crm_mile_payment_mode',
                                        blank=True, null=True)

    class Meta:
        db_table = 'crm_milestone'


class CrmUserTypeMap(BaseAbstractStructure):
    TYPE_CHOICE = (
        (1, 'Sales Manager'),
        (2, 'Business Analyst'),
        (3, 'Project Lead'),
        (4, 'Prospecting Team Member')
        #(5, 'Account Manager')
    )
    type = models.IntegerField(choices=TYPE_CHOICE, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='crm_ut_user')

    class Meta:
        db_table = 'crm_user_type_map'


class CrmLead(BaseAbstractStructure):
    STATUS_CHOICE = (
        (1, 'Not Contacted'),
        (2, 'Contacted'),
        (3, 'Qualified'),
        (4, 'Not Qualified'),
        (5, 'Junk'),
        (6, 'Released')
    )
    TERRITORY_CHOICE = (
        (1, 'India'),
        (2, 'Global')
    )
    assign_from = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True,
                                        related_name='crm_lead_af')
    assign_to = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True,
                                        related_name='crm_lead_at')
    assign_to_date = models.DateTimeField(blank=True, null=True)

    status = models.IntegerField(choices=STATUS_CHOICE, default=1)
    business_name = models.CharField(max_length=500, blank=True, null=True)
    territory = models.IntegerField(choices=TERRITORY_CHOICE, blank=True, null=True)

    cin = models.CharField(max_length=50, blank=True, null=True)
    gstin = models.CharField(max_length=50, blank=True, null=True)
    pan = models.CharField(max_length=50, blank=True, null=True)

    remarks = models.TextField(blank=True, null=True)

    poc = models.ForeignKey(CrmPoc, on_delete=models.CASCADE, related_name='crm_lead_poc', blank=True, null=True)
    task = models.ManyToManyField(CrmTask, through='CrmLeadTaskMap', related_name='crm_lead_task')
    social_link = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        db_table = 'crm_lead'


class CrmLeadRemarks(BaseAbstractStructure):
    TYPE_CHOICE = (
        (1, 'junk'),
    )
    lead = models.ForeignKey(CrmLead, on_delete=models.CASCADE, related_name='crm_lr_lead',
                                        blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    type = models.IntegerField(choices=TYPE_CHOICE, blank=True, null=True)
    reason = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'crm_lead_remarks'


class CrmLeadReassignLog(BaseAbstractStructure):
    lead = models.ForeignKey(CrmLead, on_delete=models.CASCADE, related_name='crm_lead_reassign_log')

    pre_assign_to = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True,
                                        related_name='crm_lead_pre_assign_to')
    re_assign_to = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True,
                                        related_name='crm_lead_re_assign_to')
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'crm_lead_reassign_log'


class CrmLeadTaskMap(BaseAbstractStructure):
    lead = models.ForeignKey(CrmLead, on_delete=models.CASCADE)
    task = models.ForeignKey(CrmTask, on_delete=models.CASCADE)

    class Meta:
        db_table = 'crm_lead_task_map'


class CrmOpportunity(BaseAbstractStructure):
    ENGAGEMENT_CHOICE = (
        (1, 'Fixed Cost'),
        (2, 'Time and Material'),
        (3, 'Dedicated Hiring')
    )
    STAGE_CHOICE = (
        (1, 'Requirement Shared'),
        (2, 'Presales'),
        (3, 'Proposal'),
        (4, 'Negotiation'),
        (5, 'Verbal Commitment'),
        (6, 'Agreement')
    )
    STATUS_CHOICE = (
        (0, 'In Discussion'),
        (1, 'Won'),
        (2, 'Lost')
    )
    TERRITORY_CHOICE = (
        (1, 'India'),
        (2, 'Global')
    )

    lead = models.ForeignKey(CrmLead, on_delete=models.CASCADE, related_name='crm_opp_lead')
    color_status = models.ForeignKey(CrmColorStatus, on_delete=models.CASCADE, related_name='crm_opp_color_status',
                                    blank=True, null=True)
    status = models.IntegerField(choices=STATUS_CHOICE, default=0)
    status_update_at = models.DateTimeField(blank=True, null=True)
    status_updated_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True,
                                    related_name='crm_oppo_status_updated_by')
    is_project_form_open = models.BooleanField(default=False)
    project_form_opened_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True,
                                    related_name='crm_oppo_project_form_opened_by')

    stage = models.IntegerField(choices=STAGE_CHOICE, default=1)

    resource_timeline = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    resource_hour_consumed = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    proposal_requested_at = models.DateTimeField(blank=True, null=True)

    territory = models.IntegerField(choices=TERRITORY_CHOICE, blank=True, null=True)
    country = models.ForeignKey(TCoreCountry, on_delete=models.CASCADE, related_name='crm_oppo_country', blank=True,
                                    null=True)
    business_name = models.CharField(max_length=500, blank=True, null=True)
    cin = models.CharField(max_length=50, blank=True, null=True)
    gstin = models.CharField(max_length=50, blank=True, null=True)
    pan = models.CharField(max_length=50, blank=True, null=True)

    opportunity_name = models.CharField(max_length=250, blank=True, null=True)
    opportunity_date = models.DateTimeField(blank=True, null=True)
    expected_closer_date = models.DateTimeField(blank=True, null=True)

    engagement = models.IntegerField(choices=ENGAGEMENT_CHOICE, blank=True, null=True)
    department = models.ManyToManyField(CrmDepartment, through='CrmOpportunityDepartmentMap',
                                    related_name='crm_opp_department')
    technology = models.ManyToManyField(CrmTechnology, through='CrmOpportunityTechnologyMap',
                                    related_name='crm_opp_tech')
    domain = models.ManyToManyField(TCoreDomain, through='CrmOpportunityDomainMap', related_name='crm_oppo_domain')

    business_url = models.CharField(max_length=500, blank=True, null=True)

    project_lead = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True,
                                    related_name='crm_oppo_lead')
    business_analyst = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True,
                                    related_name='crm_oppo_ba')
    account_manager = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True,
                                    related_name='crm_oppo_am')

    scope_of_work = models.ForeignKey(CrmDocument, on_delete=models.CASCADE, related_name='crm_oppo_scope_of_work',
                                    blank=True, null=True)

    man_hours = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    value = models.DecimalField(max_digits=20, decimal_places=2, default=0.0)
    currency = models.ForeignKey(TCoreCurrency, on_delete=models.CASCADE, related_name='crm_opp_currency',
                                    blank=True, null=True)
    conversion_rate_to_inr = models.DecimalField(max_digits=10, decimal_places=4, default=1.0)

    mode_of_payment = models.ForeignKey(CrmPaymentMode, on_delete=models.CASCADE,related_name='crm_oppo_payment_mode',
                                    blank=True, null=True)
    milestone = models.ManyToManyField(CrmMilestone, through='CrmOpportunityMilestoneMap',
                                    related_name='crm_opportunity_milestone')
    change_request = models.ManyToManyField(CrmChangeRequest, through='CrmOpportunityChangeRequestMap',
                                    related_name='crm_opportunity_change_request')
    poc = models.ManyToManyField(CrmPoc, through='CrmOpportunityPocMap', related_name='crm_opp_poc')
    task = models.ManyToManyField(CrmTask, through='CrmOpportunityTaskMap', related_name='crm_opp_task')

    lost_reason = models.CharField(max_length=250, blank=True, null=True)
    lost_remarks = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'crm_opportunity'


class CrmRequestHandler(BaseAbstractStructure):
    REQUEST_CHOICE = (
        (1, 'Assessment'),
        (2, 'Agreement'),
        (3, 'Reassign')
    )
    REQUEST_AGAINST_CHOICE = (
        (1, 'lead'),
        (2, 'opportunity')
    )
    STATUS_CHOICE = (
        (1, 'Requested'),
        (2, 'Accepted'),
        (3, 'Completed')
    )
    request_against = models.IntegerField(choices=REQUEST_AGAINST_CHOICE, blank=True, null=True)
    request_against_id = models.IntegerField(blank=True, null=True)
    request_type = models.IntegerField(choices=REQUEST_CHOICE, blank=True, null=True)
    status = models.IntegerField(choices=STATUS_CHOICE, blank=True, null=True)
    request_accepted_date = models.DateTimeField(blank=True, null=True)
    turnaround_time = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    class Meta:
        db_table = 'crm_request_handler'


class CrmLog(BaseAbstractStructure):
    LOG_CHOICE = (
        (1, 'account'),
    )
    LOG_AGAINST_CHOICE = (
        (1, 'lead'),
        (2, 'opportunity')
    )
    log_against = models.IntegerField(choices=LOG_AGAINST_CHOICE, blank=True, null=True)
    log_against_id = models.IntegerField(blank=True, null=True)
    log_type = models.IntegerField(choices=LOG_CHOICE, blank=True, null=True)
    log = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'crm_log'


class CrmOpportunityResourceManagement(BaseAbstractStructure):
    opportunity = models.ForeignKey(CrmOpportunity, on_delete=models.CASCADE, related_name='crm_orm_opportunity')
    resource = models.ForeignKey(CrmResource, on_delete=models.CASCADE, related_name='crm_orm_resource')
    man_hours = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    resource_no = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    class Meta:
        db_table = 'crm_opportunity_resource_management'


class CrmOpportunityDocumentTag(BaseAbstractStructure):
    opportunity = models.ForeignKey(CrmOpportunity, on_delete=models.CASCADE, related_name='crm_opd_opportunity')
    document = models.ForeignKey(CrmDocument, on_delete=models.CASCADE, related_name='crm_opd_document')
    tag = models.ForeignKey(CrmDocumentTag, on_delete=models.CASCADE, related_name='crm_opd_tag')
    is_disabled = models.BooleanField(default=False)

    class Meta:
        db_table = 'crm_opportunity_document_tag'


class CrmOpportunityMilestoneChangeRequestDistribution(BaseAbstractStructure):
    opportunity = models.ForeignKey(CrmOpportunity, on_delete=models.CASCADE, related_name='crm_omcrd_opportunity')
    milestone = models.ForeignKey(CrmMilestone, on_delete=models.CASCADE, related_name='crm_omcrd_milestone')
    change_request = models.ForeignKey(CrmChangeRequest, on_delete=models.CASCADE, related_name='crm_omcrd_change_request')
    cr_value = models.DecimalField(max_digits=20, decimal_places=2, default=0.0)
    cr_percentage = models.SmallIntegerField(default=0)

    class Meta:
        db_table = 'crm_milestone_change_request_distribution'


class CrmOpportunityBAChangeLog(BaseAbstractStructure):
    opportunity = models.ForeignKey(CrmOpportunity, on_delete=models.CASCADE, related_name='crm_opportunity_ba_change_log')

    pre_assign_ba = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True,
                                        related_name='crm_opportunity_pre_assign_ba')
    re_assign_ba = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True,
                                        related_name='crm_opportunity_re_assign_ba')

    class Meta:
        db_table = 'crm_opportunity_ba_change_log'


class CrmOpportunityDomainMap(BaseAbstractStructure):
    opportunity = models.ForeignKey(CrmOpportunity, on_delete=models.CASCADE)
    domain = models.ForeignKey(TCoreDomain, on_delete=models.CASCADE)

    class Meta:
        db_table = 'crm_opportunity_domain_map'


class CrmOpportunityRemarks(BaseAbstractStructure):
    opportunity = models.ForeignKey(CrmOpportunity, on_delete=models.CASCADE, related_name='crm_opp_remarks',
                                        blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    is_color_remarks = models.BooleanField(default=False)

    class Meta:
        db_table = 'crm_opportunity_remarks'


class CrmOpportunityPresaleLog(BaseAbstractStructure):
    opportunity = models.ForeignKey(CrmOpportunity, on_delete=models.CASCADE, related_name='crm_opp_presale_log')
    department = models.ManyToManyField(CrmDepartment, through='CrmOpportunityPresaleLogDepartmentMap', related_name='crm_opp_pre_log_department')
    project_lead = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True,
                                     related_name='crm_oppo_presale_log_lead')
    business_analyst = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True,
                                         related_name='crm_oppo_presale_log_ba')
    scope_of_work = models.ForeignKey(CrmDocument, on_delete=models.CASCADE, related_name='crm_oppo_presale_log_scope_of_work',
                                      blank=True, null=True)

    class Meta:
        db_table = 'crm_opportunity_presale_log'


class CrmOpportunityStageChangesLog(BaseAbstractStructure):
    STAGE_CHOICE = (
        (1, 'Requirement Shared'),
        (2, 'Presales'),
        (3, 'Proposal'),
        (4, 'Negotiation'),
        (5, 'Verbal Commitment'),
        (6, 'Agreement')
    )
    opportunity = models.ForeignKey(CrmOpportunity, on_delete=models.CASCADE, related_name='crm_opp_stage_change_log')
    previous_stage = models.IntegerField(choices=STAGE_CHOICE, blank=True, null=True)
    current_stage = models.IntegerField(choices=STAGE_CHOICE, blank=True, null=True)
    changed_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='crm_oscl_changed_by', blank=True, null=True)

    class Meta:
        db_table = 'crm_opportunity_stage_changes_log'


class CrmOpportunityDepartmentMap(BaseAbstractStructure):
    opportunity = models.ForeignKey(CrmOpportunity, on_delete=models.CASCADE)
    department = models.ForeignKey(CrmDepartment, on_delete=models.CASCADE)

    class Meta:
        db_table = 'crm_opportunity_department_map'


class CrmOpportunityPresaleLogDepartmentMap(BaseAbstractStructure):
    opportunity_presale_log = models.ForeignKey(CrmOpportunityPresaleLog, on_delete=models.CASCADE)
    department = models.ForeignKey(CrmDepartment, on_delete=models.CASCADE)

    class Meta:
        db_table = 'crm_opportunity_presale_log_department_map'


class CrmOpportunityMilestoneMap(BaseAbstractStructure):
    opportunity = models.ForeignKey(CrmOpportunity, on_delete=models.CASCADE)
    milestone = models.ForeignKey(CrmMilestone, on_delete=models.CASCADE)

    class Meta:
        db_table = 'crm_opportunity_milestone_map'


class CrmOpportunityChangeRequestMap(BaseAbstractStructure):
    opportunity = models.ForeignKey(CrmOpportunity, on_delete=models.CASCADE)
    change_request = models.ForeignKey(CrmChangeRequest, on_delete=models.CASCADE)

    class Meta:
        db_table = 'crm_opportunity_change_request_map'


class CrmOpportunityTaskMap(BaseAbstractStructure):
    opportunity = models.ForeignKey(CrmOpportunity, on_delete=models.CASCADE)
    task = models.ForeignKey(CrmTask, on_delete=models.CASCADE)

    class Meta:
        db_table = 'crm_opportunity_task_map'


class CrmOpportunityTechnologyMap(BaseAbstractStructure):
    opportunity = models.ForeignKey(CrmOpportunity, on_delete=models.CASCADE)
    technology = models.ForeignKey(CrmTechnology, on_delete=models.CASCADE)

    class Meta:
        db_table = 'crm_opportunity_technology_map'


class CrmOpportunityPocMap(BaseAbstractStructure):
    opportunity = models.ForeignKey(CrmOpportunity, on_delete=models.CASCADE)
    poc = models.ForeignKey(CrmPoc, on_delete=models.CASCADE)

    class Meta:
        db_table = 'crm_opportunity_poc_map'


class CrmProject(BaseAbstractStructure):
    CLIENT_CHOICE = (
        (1, 'New Client'),
        (2, 'Existing Client')
    )
    TERRITORY_CHOICE = (
        (1, 'India'),
        (2, 'Global')
    )
    ENGAGEMENT_CHOICE = (
        (1, 'Fixed Cost'),
        (2, 'Time and Material'),
        (3, 'Dadicated Hiring')
    )

    opportunity = models.ForeignKey(CrmOpportunity, on_delete=models.CASCADE)
    client_type = models.IntegerField(choices=CLIENT_CHOICE, blank=True, null=True)
    territory = models.IntegerField(choices=TERRITORY_CHOICE, blank=True, null=True)

    account_name = models.CharField(max_length=250, blank=True, null=True)
    cin = models.CharField(max_length=50, blank=True, null=True)
    gstin = models.CharField(max_length=50, blank=True, null=True)
    pan = models.CharField(max_length=50, blank=True, null=True)

    poc = models.ForeignKey(CrmPoc, on_delete=models.CASCADE, related_name='crm_project_poc')
    department = models.ManyToManyField(CrmDepartment, through='CrmProjectDepartmentMap',
                                        related_name='crm_project_department')
    technology = models.ManyToManyField(CrmTechnology, through='CrmProjectTechnologyMap',
                                        related_name='crm_project_tech')
    domain = models.ManyToManyField(TCoreDomain, through='CrmProjectDomainMap', related_name='crm_project_domain')

    project_manager = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True,
                                        related_name='crm_project_manager')
    business_analyst = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True,
                                         related_name='crm_project_ba')

    milestone = models.ManyToManyField(CrmMilestone, through='CrmProjectMilestoneMap', related_name='crm_project_milestone')
    man_hours = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    total_cost = models.DecimalField(max_digits=20, decimal_places=2, default=0.0)

    engagement = models.IntegerField(choices=ENGAGEMENT_CHOICE, blank=True, null=True)

    description = models.TextField(blank=True, null=True)

    business_proposal = models.ForeignKey(CrmDocument, on_delete=models.CASCADE, related_name='crm_project_business_proposal',
                                            blank=True, null=True)

    customer_consent = models.ForeignKey(CrmDocument, on_delete=models.CASCADE, related_name='crm_project_customer_consent',
                                            blank=True, null=True)

    class Meta:
        db_table = 'crm_project'


class CrmProjectFormLog(BaseAbstractStructure):
    opportunity = models.ForeignKey(CrmOpportunity, on_delete=models.CASCADE, related_name='crm_pfl_opportunity')
    is_open = models.BooleanField(default=True)
    data = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'crm_project_from_log'


class CrmProjectDepartmentMap(BaseAbstractStructure):
    project = models.ForeignKey(CrmProject, on_delete=models.CASCADE)
    department = models.ForeignKey(CrmDepartment, on_delete=models.CASCADE)

    class Meta:
        db_table = 'crm_project_department_map'


class CrmProjectMilestoneMap(BaseAbstractStructure):
    project = models.ForeignKey(CrmProject, on_delete=models.CASCADE)
    milestone = models.ForeignKey(CrmMilestone, on_delete=models.CASCADE)

    class Meta:
        db_table = 'crm_project_milestone_map'


class CrmProjectTechnologyMap(BaseAbstractStructure):
    project = models.ForeignKey(CrmProject, on_delete=models.CASCADE)
    technology = models.ForeignKey(CrmTechnology, on_delete=models.CASCADE)

    class Meta:
        db_table = 'crm_project_technology_map'


class CrmProjectDomainMap(BaseAbstractStructure):
    project = models.ForeignKey(CrmProject, on_delete=models.CASCADE)
    domain = models.ForeignKey(TCoreDomain, on_delete=models.CASCADE)

    class Meta:
        db_table = 'crm_project_domain_map'


class CrmCurrencyConversionHistory(BaseAbstractStructure):
    from_currency = models.ForeignKey(TCoreCurrency, on_delete=models.CASCADE, blank=True, null=True,
                                        related_name='crm_ccch_from_history')
    to_currency = models.ForeignKey(TCoreCurrency, on_delete=models.CASCADE, blank=True, null=True,
                                        related_name='crm_ccch_to_history')
    rate = models.DecimalField(max_digits=10, decimal_places=4, default=1.0)

    class Meta:
        db_table = 'crm_currency_conversion_history'


class CrmLeadDocument(BaseAbstractStructure):
    lead_document = models.ForeignKey(CrmDocument, on_delete=models.CASCADE, related_name='crm_lead_document', blank=True, null=True)

    class Meta:
        db_table = 'crm_lead_document'
