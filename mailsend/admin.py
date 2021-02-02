from django.contrib import admin

from mailsend.models import MailTemplate, MailHistory

@admin.register(MailTemplate)
class MailTemplate(admin.ModelAdmin):
    list_display = [field.name for field in MailTemplate._meta.fields]
    save_as = True

@admin.register(MailHistory)
class MailHistory(admin.ModelAdmin):
    list_display = [field.name for field in MailHistory._meta.fields]
    save_as = True
