from django.db import models
from django.contrib.auth.models import User
from dynamic_media import get_directory_path
from django_mysql.models import EnumField
from validators import validate_file_extension
from core.models import TCoreUnit
from users.models import TCoreUserDetail
import datetime
import time


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


class TdmsSiteTypeProjectSiteManagement(UpdateBaseAbstractStructure):
    name = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'tdms_site_type_project_site_management'

class TdmsSiteProjectSiteManagement(UpdateBaseAbstractStructure):
    name = models.CharField(max_length=200, blank=True, null=True)
    address = models.CharField(max_length=200, blank=True, null=True)
    site_latitude=models.DecimalField(max_digits=40, decimal_places=16, blank=True, null=True)
    site_longitude=models.DecimalField(max_digits=40, decimal_places=16, blank=True, null=True)
    office_latitude=models.DecimalField(max_digits=40, decimal_places=16, blank=True, null=True)
    office_longitude=models.DecimalField(max_digits=40, decimal_places=16, blank=True, null=True)
    gest_house_latitude=models.DecimalField(max_digits=40, decimal_places=16, blank=True, null=True)
    gest_house_longitude=models.DecimalField(max_digits=40, decimal_places=16, blank=True, null=True)
    type = models.ForeignKey(TdmsSiteTypeProjectSiteManagement, related_name='project_site_management_type',
                             on_delete=models.CASCADE, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    gst_no = models.CharField(max_length=255, blank=True, null=True)
    geo_fencing_area = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'tdms_site_project_site_management'

class TdmsSiteProjectSiteManagementMultipleLongLat(UpdateBaseAbstractStructure):
    project_site = models.ForeignKey(TdmsSiteProjectSiteManagement, 
    related_name='p_s_p_s_m_m_l_l_project_site', on_delete=models.CASCADE, blank=True, null=True)
    latitude = models.DecimalField(max_digits=40, decimal_places=16, blank=True, null=True)
    longitude = models.DecimalField(max_digits=40, decimal_places=16, blank=True, null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'tdms_site_project_site_management_multiple_long_lat'

def unique_rand_project():
    while True:
        code = "P" + str(int(time.time()))
        if not TdmsProject.objects.filter(project_g_id=code).exists():
            return code

#:::::::::::::::: SITE USER MAPPING :::::::::::#

class TdmsSiteUserMapping(UpdateBaseAbstractStructure):
    site_location = models.ForeignKey(TdmsSiteProjectSiteManagement,
                               related_name='td_s_management_id',
                               on_delete=models.CASCADE,
                               blank=True,
                               null=True
                               )
    user = models.ForeignKey(User, related_name='td_user_mapping_user',
                             on_delete=models.CASCADE, blank=True, null=True)
    start_date = models.DateTimeField(auto_now_add=False, blank=True, null=True)
    expire_date = models.DateTimeField(auto_now_add=False, blank=True, null=True)
    status = models.BooleanField(default=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'tdms_site_user_mapping'

    
    def user_details(self):
        queryset = TCoreUserDetail.objects.filter(cu_user=self.user).values(
            'cu_user__first_name','cu_user__last_name','designation__cod_name')
        #print('queryset111111111111111111',queryset)
        return queryset[0]
