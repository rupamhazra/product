from django.db import models
from django.contrib.auth.models import User
from dynamic_media import get_directory_path
from django.core.validators import URLValidator

class TCorePermissions(models.Model):
    name = models.CharField(max_length=20, null=True, blank=True)
    cp_created_by = models.ForeignKey(User, on_delete=models.CASCADE,related_name='cp_created_by',blank=True,null=True)
    cp_created_at=models.DateTimeField(auto_now_add=True)
    cp_updated_at=models.DateTimeField(auto_now =True)
    cp_updated_by=models.ForeignKey(User, on_delete=models.CASCADE, related_name='cp_updated_by',blank=True,null=True)
    cp_deleted_at = models.DateTimeField(auto_now=True)
    cp_deleted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cp_deleted_by', blank=True,
                                      null=True)
    class Meta:
        db_table = 't_core_permissions'
    def __str__(self):
        return str(self.id)

class TCoreRole(models.Model):
    """ t_core_roles """
    cr_name = models.CharField(max_length=100, blank=True,null=True)
    cr_parent_id = models.IntegerField(default = 0)
    cr_is_deleted = models.BooleanField(default=False)

    cr_created_by = models.ForeignKey(User, on_delete=models.CASCADE,related_name='cr_created_by',blank=True,null=True)
    cr_created_at=models.DateTimeField(auto_now_add=True)
    cr_updated_at=models.DateTimeField(auto_now =True)
    cr_updated_by=models.ForeignKey(User, on_delete=models.CASCADE, related_name='cr_updated_by',blank=True,null=True)
    cr_deleted_at=models.DateTimeField(auto_now =True)
    cr_deleted_by=models.ForeignKey(User, on_delete=models.CASCADE, related_name='cr_deleted_by',blank=True,null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 't_core_roles'
        # unique_together = ('cr_name', 'cr_parent_id',)

class TCoreModule(models.Model):
    permission_type = (
        (1, 'Public Read/Write'),
        (2, 'Public Read Only'),
        (3, 'Private')
    )
    cm_name = models.CharField(max_length=100, blank=True,null=True, unique=True)
    cm_desc = models.TextField(blank=True, null=True)
    cm_icon = models.ImageField(upload_to=get_directory_path, default=None, blank=True, null=True)
    cm_url = models.TextField(blank=True, null=True)
    cm_is_deleted = models.BooleanField(default=False)
    cm_is_editable = models.BooleanField(default=True)

    cm_created_by = models.ForeignKey(User, on_delete=models.CASCADE,related_name='cm_created_by',blank=True,null=True)
    cm_created_at=models.DateTimeField(auto_now_add=True)
    cm_updated_at=models.DateTimeField(auto_now =True)
    cm_updated_by=models.ForeignKey(User, on_delete=models.CASCADE, related_name='cm_updated_by',blank=True,null=True)
    cm_deleted_at=models.DateTimeField(auto_now =True)
    cm_deleted_by=models.ForeignKey(User, on_delete=models.CASCADE, related_name='cm_deleted_by',blank=True,null=True)
    
    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 't_core_modules'

class TCoreUnit(models.Model):
    c_name = models.CharField(max_length=100, blank=True, null=True)
    c_is_deleted = models.BooleanField(default=False)

    c_created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='c_created_by', blank=True,
                                       null=True)
    c_created_at = models.DateTimeField(auto_now_add=True)
    c_updated_at = models.DateTimeField(auto_now=True)
    c_updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='c_updated_by', blank=True,
                                       null=True)
    c_owned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='c_owned_by', blank=True,
                                       null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 't_core_units'

class TCoreOther(models.Model):
    cot_name = models.CharField(max_length=100, blank=True,null=True)
    description = models.TextField(blank=True, null=True)
    cot_parent_id = models.IntegerField(default=0)
    cot_is_deleted = models.BooleanField(default=False)
    cot_created_by = models.ForeignKey(User, on_delete=models.CASCADE,related_name='cot_created_by',blank=True,null=True)
    cot_created_at=models.DateTimeField(auto_now_add=True)
    cot_updated_at=models.DateTimeField(auto_now =True)
    cot_updated_by=models.ForeignKey(User, on_delete=models.CASCADE, related_name='cot_updated_by',blank=True,null=True)
    cot_deleted_at=models.DateTimeField(auto_now =True)
    cot_deleted_by=models.ForeignKey(User, on_delete=models.CASCADE, related_name='cot_deleted_by',blank=True,null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 't_core_others'

class TCoreDepartment(models.Model):
    cd_name=models.CharField(max_length=100, blank=True,null=True)
    cd_parent_id=models.IntegerField(default=0,blank=True, null=True)
    cd_is_deleted = models.BooleanField(default=False)
    cd_created_by = models.ForeignKey(User, on_delete=models.CASCADE,related_name='cd_created_by',blank=True,null=True)
    cd_created_at=models.DateTimeField(auto_now_add=True)
    cd_updated_at=models.DateTimeField(auto_now =True)
    cd_updated_by=models.ForeignKey(User, on_delete=models.CASCADE, related_name='cd_updated_by',blank=True,null=True)
    cd_deleted_at=models.DateTimeField(auto_now =True)
    cd_deleted_by=models.ForeignKey(User, on_delete=models.CASCADE, related_name='cd_deleted_by',blank=True,null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 't_core_department'


class TCoreResource(models.Model):
    resource_name = models.CharField(max_length=100, blank=True,null=True)
    department = models.ForeignKey(TCoreDepartment, on_delete=models.CASCADE, related_name='rs_department', blank=True,null=True)
    sub_department = models.ForeignKey(TCoreDepartment, on_delete=models.CASCADE, related_name='rs_sub_department', blank=True,null=True)
    resource_allocator = models.ForeignKey(User, on_delete=models.CASCADE,related_name='resource_allocator', blank=True,null=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE,related_name='rs_cre_by',blank=True,null=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now =True)
    updated_by=models.ForeignKey(User, on_delete=models.CASCADE, related_name='rs_up_by',blank=True,null=True)
    deleted_at=models.DateTimeField(auto_now =True)
    deleted_by=models.ForeignKey(User, on_delete=models.CASCADE, related_name='rs_del_by',blank=True,null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 't_core_resource'


class TCoreDesignation(models.Model):
    cod_name=models.CharField(max_length=100, blank=True,null=True)
    cod_is_deleted = models.BooleanField(default=False)
    cod_created_by = models.ForeignKey(User, on_delete=models.CASCADE,related_name='cod_created_by',blank=True,null=True)
    cod_created_at=models.DateTimeField(auto_now_add=True)
    cod_updated_at=models.DateTimeField(auto_now =True)
    cod_updated_by=models.ForeignKey(User, on_delete=models.CASCADE, related_name='cod_updated_by',blank=True,null=True)
    cod_deleted_at=models.DateTimeField(auto_now =True)
    cod_deleted_by=models.ForeignKey(User, on_delete=models.CASCADE, related_name='cod_deleted_by',blank=True,null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 't_core_designation'

class TCoreCompany(models.Model):
    coc_name=models.CharField(max_length=100, blank=True,null=True)
    coc_code=models.CharField(max_length=20, blank=True,null=True)
    coc_details=models.TextField(blank=True, null=True)
    coc_is_deleted = models.BooleanField(default=False)
    coc_created_by = models.ForeignKey(User, on_delete=models.CASCADE,related_name='coc_created_by',blank=True,null=True)
    coc_created_at=models.DateTimeField(auto_now_add=True)
    coc_updated_at=models.DateTimeField(auto_now =True)
    coc_updated_by=models.ForeignKey(User, on_delete=models.CASCADE, related_name='coc_updated_by',blank=True,null=True)
    coc_deleted_at=models.DateTimeField(auto_now =True)
    coc_deleted_by=models.ForeignKey(User, on_delete=models.CASCADE, related_name='coc_deleted_by',blank=True,null=True)

    def __str__(self):
        return str(self.id)
    
    def get_name(self):
        return str(self.coc_name)


    class Meta:
        db_table = 't_core_company'


class TCoreCompanyCostCentre(models.Model):
    company = models.ForeignKey(TCoreCompany,on_delete=models.CASCADE, related_name='company_cs', blank=True, null=True)
    cost_centre_name = models.CharField(max_length=100, blank=True, null=True)
    cost_centre_code = models.CharField(max_length=20, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE,blank=True, related_name='c3_created_by',
                                       null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True,null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True,null=True)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, related_name='c3_updated_by',
                                       null=True)
    deleted_at = models.DateTimeField(auto_now=True, blank=True,null=True)
    deleted_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True,related_name='c3_deleted_by',
                                       null=True)

    def __str__(self):
        return str(self.id)

    def get_name(self):
        return str(self.cost_centre_name)


class TCoreGrade(models.Model):
    cg_name=models.CharField(max_length=100, blank=True,null=True)
    cg_parent_id=models.IntegerField(default=0,blank=True, null=True)
    cg_is_deleted = models.BooleanField(default=False)
    cg_created_by = models.ForeignKey(User, on_delete=models.CASCADE,related_name='cg_created_by',blank=True,null=True)
    cg_created_at=models.DateTimeField(auto_now_add=True)
    cg_updated_at=models.DateTimeField(auto_now =True)
    cg_updated_by=models.ForeignKey(User, on_delete=models.CASCADE, related_name='cg_updated_by',blank=True,null=True)
    cg_deleted_at=models.DateTimeField(auto_now =True)
    cg_deleted_by=models.ForeignKey(User, on_delete=models.CASCADE, related_name='cg_deleted_by',blank=True,null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 't_core_grade'


class TCoreSubGrade(models.Model):
    name=models.CharField(max_length=100, blank=True,null=True)
    parent_id=models.IntegerField(default=0,blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE,related_name='csg_created_by',blank=True,null=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now =True)
    updated_by=models.ForeignKey(User, on_delete=models.CASCADE, related_name='csg_updated_by',blank=True,null=True)
    deleted_at=models.DateTimeField(auto_now =True)
    deleted_by=models.ForeignKey(User, on_delete=models.CASCADE, related_name='csg_deleted_by',blank=True,null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 't_core_sub_grade'


class TCoreState(models.Model):
    cs_state_name=models.CharField(max_length=50, blank=True,null=True)
    cs_tin_number=models.IntegerField(default=0)
    cs_state_code=models.CharField(max_length=10, blank=True,null=True)
    cs_description=models.TextField(blank=True,null=True)
    cs_status=models.BooleanField(default=True)    
    cs_is_deleted =models.BooleanField(default=False)
    cs_created_by =models.ForeignKey(User, on_delete=models.CASCADE,related_name='cs_created_by',blank=True,null=True)
    cs_created_at=models.DateTimeField(auto_now_add=True)
    cs_updated_at=models.DateTimeField(auto_now =True)
    cs_updated_by=models.ForeignKey(User, on_delete=models.CASCADE, related_name='cs_updated_by',blank=True,null=True)
    cs_deleted_at=models.DateTimeField(auto_now =True)
    cs_deleted_by=models.ForeignKey(User, on_delete=models.CASCADE, related_name='cs_deleted_by',blank=True,null=True)

    def __str__(self):
        return '{}, {}'.format(self.cs_state_name, self.cs_state_code)

    class Meta:
        db_table = 't_core_state'

class TCoreSalaryType(models.Model):
    st_name=models.CharField(max_length=100, blank=True,null=True)
    st_code = models.CharField(max_length=100, blank=True,null=True)
    st_is_deleted =models.BooleanField(default=False)
    st_created_by =models.ForeignKey(User, on_delete=models.CASCADE,related_name='st_created_by',blank=True,null=True)
    st_created_at=models.DateTimeField(auto_now_add=True)
    st_updated_at=models.DateTimeField(auto_now =True)
    st_updated_by=models.ForeignKey(User, on_delete=models.CASCADE, related_name='st_updated_by',blank=True,null=True)
    st_deleted_at=models.DateTimeField(auto_now =True)
    st_deleted_by=models.ForeignKey(User, on_delete=models.CASCADE, related_name='st_deleted_by',blank=True,null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 't_core_salary_type'


class TCoreBank(models.Model):
    name=models.CharField(max_length=100, blank=True,null=True)
    is_deleted =models.BooleanField(default=False)
    created_by =models.ForeignKey(User, on_delete=models.CASCADE,related_name='b_created_by',blank=True,null=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now =True)
    updated_by=models.ForeignKey(User, on_delete=models.CASCADE, related_name='b_updated_by',blank=True,null=True)
    deleted_at=models.DateTimeField(auto_now =True)
    deleted_by=models.ForeignKey(User, on_delete=models.CASCADE, related_name='b_deleted_by',blank=True,null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 't_core_bank'


class TCoreCountry(models.Model):
    name = models.CharField(max_length=50, blank=True, null=True)
    code = models.CharField(max_length=50, blank=True, null=True)
    code_3 = models.CharField(max_length=50, blank=True, null=True)
    dialing_code = models.CharField(max_length=10, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tcc_created_by', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tcc_updated_by', blank=True, null=True)
    deleted_at = models.DateTimeField(auto_now=True)
    deleted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tcc_deleted_by', blank=True, null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 't_core_country'


class TCoreCurrency(models.Model):
    name = models.CharField(max_length=50, blank=True, null=True)
    code = models.CharField(max_length=20, blank=True, null=True)
    symbol = models.CharField(max_length=50, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tccurr_created_by', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tccurr_updated_by', blank=True, null=True)
    deleted_at = models.DateTimeField(auto_now=True)
    deleted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tccurr_deleted_by', blank=True, null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 't_core_currency'


class TCoreDomain(models.Model):
    name = models.CharField(max_length=50, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tcdom_created_by', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tcdom_updated_by', blank=True, null=True)
    deleted_at = models.DateTimeField(auto_now=True)
    deleted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tcdom_deleted_by', blank=True, null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 't_core_domain'

class TCoreCity(models.Model):
    name=models.CharField(max_length=100, blank=True,null=True)
    is_deleted =models.BooleanField(default=False)
    created_by =models.ForeignKey(User, on_delete=models.CASCADE,related_name='city_created_by',blank=True,null=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now =True)
    updated_by=models.ForeignKey(User, on_delete=models.CASCADE, related_name='city_updated_by',blank=True,null=True)
    deleted_at=models.DateTimeField(auto_now =True)
    deleted_by=models.ForeignKey(User, on_delete=models.CASCADE, related_name='city_deleted_by',blank=True,null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'city'

class TCoreLeaveCodeForSapReport(models.Model):
    name=models.CharField(max_length=100,)
    code = models.CharField(max_length=100, blank=True,null=True)
    is_deleted =models.BooleanField(default=False)
    created_by =models.ForeignKey(User, on_delete=models.CASCADE,related_name='leave_code_created_by',blank=True,null=True)
    created_at=models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 't_core_leave_code_for_sap_report'

class TCoreFloor(models.Model):
    name=models.CharField(max_length=15)
    is_deleted =models.BooleanField(default=False)
    created_by =models.ForeignKey(User, on_delete=models.CASCADE,related_name='fl_created_by',blank=True,null=True)
    created_at=models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 't_core_floor'