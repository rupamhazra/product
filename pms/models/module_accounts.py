from django.db import models
from django.contrib.auth.models import User
from validators import validate_file_extension
import datetime

class PmsAccounts(models.Model):
    user =  models.ForeignKey(User, related_name='account_user',on_delete=models.CASCADE, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='account_created_by',on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(default=datetime.datetime.now)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'pms_accounts'

class PmsHoUser(models.Model):
    user =  models.ForeignKey(User, related_name='ho_user',on_delete=models.CASCADE, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='ho_created_by',on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(default=datetime.datetime.now)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'pms_ho_user'


class PmsTourAccounts(models.Model):
    user = models.ForeignKey(User, related_name='tour_account_user',on_delete=models.CASCADE, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='tour_account_created_by',on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(default=datetime.datetime.now)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'pms_tour_accounts'


class PmsTourHoUser(models.Model):
    user = models.ForeignKey(User, related_name='tour_ho_user',on_delete=models.CASCADE, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='tour_ho_created_by',on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(default=datetime.datetime.now)

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'pms_tour_ho_user'


# class PmsSiteBillsInvoicesHoUser(models.Model):
#     user =  models.ForeignKey(User, related_name='site_ho_user',on_delete=models.CASCADE, blank=True, null=True)
#     is_deleted = models.BooleanField(default=False)
#     created_by = models.ForeignKey(User, related_name='site_ho_created_by',on_delete=models.CASCADE, blank=True, null=True)
#     created_at = models.DateTimeField(default=datetime.datetime.now)

#     def __str__(self):
#         return str(self.id)

#     class Meta:
#         db_table = 'pms_site_bills_invoices_ho_user'