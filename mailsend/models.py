from django.db import models

class MailTemplate(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    html_content = models.TextField()
    template_variable = models.TextField()

    class Meta:
        db_table = 'mail_template'

    def __str__(self):
        return self.name

# added by Shubhadeep to implement email service

class MailHistory(models.Model):
    status_choices = (
                ('pending', 'pending'),
                ('sent', 'sent'),
                ('error','error'),)
    ## cc and bcc fields are added by Swarup Adhikary(23.12.2020)
    code = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True, null=True)
    recipient_list = models.TextField(null=True)
    cc = models.TextField(null=True)
    bcc = models.TextField(null=True)
    subject = models.TextField(null=True)
    body = models.TextField(null=True)
    attachment = models.TextField(null=True)
    status = models.TextField(choices=status_choices, default='pending')
    error_msg = models.TextField(default='')

    class Meta:
        db_table = 'mail_history'

    def __str__(self):
        return self.code

# --

# added by Shubhadeep to handle sequence and uid in ICS files

class MailICSMapping(models.Model):
    email = models.CharField(max_length=255, default='')
    uuid = models.CharField(max_length=255)
    module = models.CharField(max_length=20)
    event_id = models.IntegerField(default=0)
    sequence = models.IntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = 'mail_ics_mapping'

    def __str__(self):
        return self.code

# --
