from django.db import models
from django.contrib.auth.models import User
from dynamic_media import get_directory_path
from validators import validate_file_extension
import datetime
import time

class PmsContractorsCategoryMaster(models.Model):
    name = models.CharField(max_length=100,blank=True, null=True)
    created_by = models.ForeignKey(User, related_name='con_cat_created_by',on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, related_name='con_cat_updated_by', on_delete=models.CASCADE, blank=True, null=True)
    updated_at = models.DateTimeField(blank=True,null=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'pms_contractors_category_master'

class PmsContractor(models.Model):
    category = models.ForeignKey(PmsContractorsCategoryMaster, related_name='contractor_category',on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=100,blank=True,null=True)
    contact_person_name = models.CharField(max_length=100,blank=True, null=True)
    phone_no = models.TextField(blank=True,null=True)
    email = models.CharField(max_length=100,null=True, blank=True)
    website =  models.CharField(max_length=200,blank=True, null=True)
    address = models.TextField(blank=True,null=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='contract_created_by',on_delete=models.CASCADE, blank=True, null=True)
    updated_by = models.ForeignKey(User, related_name='contract_updated_by',on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(blank=True,null=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'pms_contractor'