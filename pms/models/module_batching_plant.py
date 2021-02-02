"""
Created by Bishal on 28-08-2020
Reviewd and updated by Shubhadeep
"""

from django.db import models
from django.contrib.auth.models import User
from dynamic_media import get_directory_path
from django_mysql.models import EnumField
from validators import validate_file_extension
from core.models import TCoreUnit
from pms.models import PmsProjects
import datetime
import time


class PmsBatchingPlantBrandOfCementMaster(models.Model):
    brand_of_cement = models.CharField(max_length=30,null=False,blank=False)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='p_b_p_b_o_c_m_created_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    updated_by = models.ForeignKey(User, related_name='p_b_p_b_o_c_m_updated_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'pms_batching_plant_brand_of_cement_master'


class PmsBatchingPlantPurposeMaster(models.Model):
    purpose = models.CharField(max_length=30,null=False,blank=False)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='p_b_p_p_m_created_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    updated_by = models.ForeignKey(User, related_name='p_b_p_p_m_updated_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'pms_batching_plant_purpose_master'



class PmsBatchingPlantConcreteMaster(models.Model):
    concrete_name = models.CharField(max_length=30,null=False,blank=False)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='p_b_p_c_m_created_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    updated_by = models.ForeignKey(User, related_name='p_b_p_c_m_updated_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'pms_batching_plant_concrete_master'


class PmsBatchingPlantMappingConcreteBrandOfCement(models.Model):
    concrete_master=models.ForeignKey(PmsBatchingPlantConcreteMaster, related_name='p_b_p_m_c_b_o_c_concrete_master',
                                   on_delete=models.CASCADE, blank=True, null=True)
    brand_of_cement_master = models.ForeignKey(PmsBatchingPlantBrandOfCementMaster, related_name='p_b_p_m_c_b_o_c_brand_cement_master',
                                   on_delete=models.CASCADE, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    
    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'pms_batching_plant_mapping_concrete_brand_of_cement'

class PmsBatchingPlantMappingConcretePurpose(models.Model):
    concrete_master = models.ForeignKey(PmsBatchingPlantConcreteMaster, related_name='p_b_p_m_c_p_concrete_master',
                                   on_delete=models.CASCADE, blank=True, null=True)
    purpose_master = models.ForeignKey(PmsBatchingPlantPurposeMaster, related_name='p_b_p_m_c_p_purpose_master',
                                   on_delete=models.CASCADE, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    
    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'pms_batching_plant_mapping_concrete_purpose'



class PmsBatchingPlantConcreteIngredientMaster(models.Model):
    project = models.ForeignKey(PmsProjects, related_name='p_b_p_c_i_m_proejct', on_delete=models.CASCADE, blank=True,
                            null=True)
    concrete_master = models.ForeignKey(PmsBatchingPlantConcreteMaster, related_name='p_b_p_c_i_m_concrete_master',
                                   on_delete=models.CASCADE, blank=True, null=True)
    brand_of_cement_master = models.ForeignKey(PmsBatchingPlantBrandOfCementMaster, related_name='p_b_p_c_i_m_brand_of_cement_master',
                                   on_delete=models.CASCADE, blank=True, null=True)
    purpose_master = models.ForeignKey(PmsBatchingPlantPurposeMaster, related_name='p_b_p_c_i_m_purpose_master',
                                   on_delete=models.CASCADE, blank=True, null=True)
    cement = models.DecimalField(max_digits=10, decimal_places=3, default=0, null=True)
    fly_ash = models.DecimalField(max_digits=10, decimal_places=3, default=0, null=True)
    sand = models.DecimalField(max_digits=10, decimal_places=3, default=0, null=True)
    agg_20mm = models.DecimalField(max_digits=10, decimal_places=3, default=0, null=True)
    agg_10mm = models.DecimalField(max_digits=10, decimal_places=3, default=0, null=True)
    water = models.DecimalField(max_digits=10, decimal_places=3, default=0, null=True)
    admixture = models.DecimalField(max_digits=10, decimal_places=3, default=0, null=True)
    slump = models.CharField(max_length=30)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='p_b_p_c_i_m_created_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    updated_by = models.ForeignKey(User, related_name='p_b_p_c_i_m_updated_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'pms_batching_plant_concrete_ingredient_master'

class PmsBatchingPlantBatchingEntry(models.Model):
    doc_status_choice = ((1,'pending'),
                (2,'processing'),
                (3,'completed'),
                (4,'error'),)
    acceptance_choice = ((1,'pending'),
                (2,'approved'),
                (3,'rejected'),)
    document = models.FileField(upload_to=get_directory_path,
                                default=None,
                                blank=True, null=True,
                                validators=[validate_file_extension])
    document_status = models.IntegerField(choices=doc_status_choice, default=1)
    acceptance_status = models.IntegerField(choices=acceptance_choice, default=1)
    error_msg = models.TextField(null=True, blank=True, default='')
    project = models.ForeignKey(PmsProjects, related_name='p_b_p_b_e_proejct', on_delete=models.CASCADE, blank=True,
                                null=True)
    brand_of_cement_master = models.ForeignKey(PmsBatchingPlantBrandOfCementMaster, related_name='p_b_p_b_e_brand_of_cement_master',
                                   on_delete=models.CASCADE, blank=True, null=True)
    purpose_master = models.ForeignKey(PmsBatchingPlantPurposeMaster, related_name='p_b_p_b_e_purpose_master',
                                   on_delete=models.CASCADE, blank=True, null=True)
    created_by = models.ForeignKey(User, related_name='p_b_p_b_e_created_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    updated_by = models.ForeignKey(User, related_name='p_b_p_b_e_updated_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    # below fields will be updated by OCR
    concrete_master = models.ForeignKey(PmsBatchingPlantConcreteMaster, related_name='p_b_p_b_e_concrete_master',
                                   on_delete=models.CASCADE, blank=True, null=True)
    concrete_quantity = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True)
    document_processed_at = models.DateTimeField(null=True)
    batch_processed_at = models.DateTimeField(null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'pms_batching_plant_batching_entry'

class PmsBatchingPlantBatchingEntryDetails(models.Model):
    batching_entry = models.ForeignKey(PmsBatchingPlantBatchingEntry, related_name='p_b_p_b_e_d_batching_entry',
                                   on_delete=models.CASCADE)    
    is_deleted = models.BooleanField(default=False)
    # below fields will be updated by OCR
    bat_no = models.IntegerField()
    cement = models.DecimalField(max_digits=10, decimal_places=3, default=0, null=True)
    fly_ash = models.DecimalField(max_digits=10, decimal_places=3, default=0, null=True)
    sand = models.DecimalField(max_digits=10, decimal_places=3, default=0, null=True)
    agg_20mm = models.DecimalField(max_digits=10, decimal_places=3, default=0, null=True)
    agg_10mm = models.DecimalField(max_digits=10, decimal_places=3, default=0, null=True)
    water = models.DecimalField(max_digits=10, decimal_places=3, default=0, null=True)
    admixture = models.DecimalField(max_digits=10, decimal_places=3, default=0, null=True)
    
    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'pms_batching_plant_batching_entry_details'