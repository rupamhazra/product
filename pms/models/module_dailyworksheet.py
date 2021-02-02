from django.db import models
from django.contrib.auth.models import User
from dynamic_media import get_directory_path
from django_mysql.models import EnumField
from validators import validate_file_extension
from core.models import TCoreUnit
import datetime
import time

# ::::::::::::::::::::::::::::::::::::::::::::::::work sheet::::::::::::::::::::::::::::::::::::::::


class PmsDailyWorkSheet(models.Model):
    owner = models.ForeignKey(User, related_name='dws_owner', on_delete=models.CASCADE, blank=True, null=True)
    work_done = models.TextField(blank=True, null=True)
    date = models.DateTimeField(blank=True, null=True)
    start_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='work_sheet_created_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    updated_by = models.ForeignKey(User, related_name='work_sheet_updated_by',
                                   on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)
    class Meta:
        db_table = 'pms_daily_work_sheet'

