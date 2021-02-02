from django.contrib.auth.models import User
from django.db import models

from core.models import TCoreModule
from dynamic_media import get_directory_path


class UserTokenMapping(models.Model):
    DEVICE_TYPE = (('web', 'web'),
                   ('android', 'android'),
                   ('ios', 'ios'))
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='n_user', blank=True,
        null=True)
    device_token = models.TextField(blank=True, null=True)
    device_type = models.CharField(
        choices=DEVICE_TYPE, blank=True, null=True, max_length=20)
    device_details = models.CharField(blank=True, null=True, max_length=200)
    request_token = models.CharField(blank=True, null=True, max_length=200)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'user_token_mapping'

class NotificationMaster(models.Model):
    title = models.TextField(blank=True, null=True)
    body = models.TextField(blank=True, null=True)
    data = models.TextField(blank=True, null=True)
    code = models.CharField(blank=True, null=True, max_length=20)
    image = models.ImageField(
        upload_to=get_directory_path, default=None, null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'notification_master'

class UserNotificationMapping(models.Model):
    notification = models.ForeignKey(
        NotificationMaster, on_delete=models.CASCADE, related_name='n_map',
        blank=True, null=True)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='u_map', blank=True,
        null=True)
    read_status = models.BooleanField(default=False)
    app_module_name = models.ForeignKey(
        TCoreModule, on_delete=models.CASCADE, related_name='unm_module',
        blank=True, null=True)
    # click_action = models.ForeignKey(NotificationClickActionMaster, on_delete=models.CASCADE,related_name='unm_click_action')
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'user_notification_mapping'
