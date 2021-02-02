from celery import shared_task

from crm.models import CrmTask
from mailsend.views import GlobleMailSend
from datetime import datetime


@shared_task
def hello_crm():
    print('Hello there! ',datetime.now())
    CrmTask.cmobjects.all().first()
    return {'test': 'hello there!!!'}


@shared_task
def task_schedule_reminder(*args, **kwargs):
    task_response = dict()
    try:
        recipient = kwargs['recipient']
        user_email = kwargs['user_email']
        task_id = kwargs['task_id']
        task_obj = CrmTask.cmobjects.filter(id=task_id, is_completed=False).first()
        date_time = None
        print(task_obj)
        if task_obj:
            date_time = task_obj.date_time
            task_name = task_obj.name
            mail_data = {
                'recipient_name': recipient,
                'task_name': task_name,
                'date_time': date_time
            }
            print(mail_data)
            mail_class = GlobleMailSend('SFT-CRM-TASK-SCHD', [user_email])
            mail_response = mail_class.mailsend(mail_data)

        task_response['mail'] = user_email
        task_response['date_time'] = date_time
        task_response['status'] = 'Success'
    except Exception as e:
        print(str(e))
        task_response['status'] = 'Error'
        task_response['message'] = str(e)

    return task_response

