from django.contrib import admin

from notification.models import (NotificationMaster, UserNotificationMapping,
                                 UserTokenMapping)


@admin.register(UserTokenMapping)
class UserTokenMapping(admin.ModelAdmin):
    list_display = [field.name for field in UserTokenMapping._meta.fields]
    search_fields = ('user', 'user__username')


@admin.register(NotificationMaster)
class NotificationMaster(admin.ModelAdmin):
    list_display = [field.name for field in NotificationMaster._meta.fields]
    search_fields = ('=id', 'title', 'code')


@admin.register(UserNotificationMapping)
class UserNotificationMapping(admin.ModelAdmin):
    list_display = [
        field.name for field in UserNotificationMapping._meta.fields]
    search_fields = ('user', 'user__username', 'app_module_name')
