from datetime import datetime

from etask.models import TaskExtentionDateMap, TaskCompleteReopenMap, EtaskTaskSubAssignLog, ETaskComments, EtaskTask, \
    ETaskCommentsViewers
from global_function import userdetails, send_mail_list
from users.models import TCoreUserDetail


def get_task_flag(task=None):
    TASK_TYPES = ('overdue', 'ongoing', 'upcomming')
    cur_date =datetime.now().date()
    task_flag = None

    if (task.extended_date is not None and task.extended_date.date() < cur_date) or \
            (task.extended_date is None and task.end_date.date() < cur_date):
        task_flag = TASK_TYPES[0]
    elif (task.shifted_date is not None and task.shifted_date.date() <= cur_date) or (
            task.shifted_date is None and task.start_date.date() <= cur_date):
        task_flag = TASK_TYPES[1]
    elif (task.shifted_date is not None and task.shifted_date.date() > cur_date) or (
            task.shifted_date is None and task.start_date.date() > cur_date):
        task_flag = TASK_TYPES[2]
    return 'closed' if task.task_status == 4 else task_flag


def is_pending_extention(task=None):
    task_extention = TaskExtentionDateMap.objects.filter(task=task, status=1)
    return task_extention.count() > 0


def is_pending_closer(task=None):
    task_closer = TaskCompleteReopenMap.objects.filter(task=task, status=1)
    return task_closer.count() > 0


def is_subassign(task=None, login_user=None):
    etask_sub_assign_user = EtaskTaskSubAssignLog.objects.filter(task=task, assign_from=login_user,
                                                                 is_deleted=False)
    return etask_sub_assign_user.count() > 0


def create_comment(task=None, comments=None, loggedin_user=None):

    e_task_comments = ETaskComments.objects.create(task=task, comments=comments,
                                                created_by=loggedin_user,owned_by=loggedin_user)
    comment_save_send = ''
    users_list = EtaskTask.objects.filter(id=task.id, is_deleted=False).values('assign_by', 'assign_to')
    user_cat_list = users_list.values('task_categories', 'sub_assign_to_user')
    email_list = []
    if user_cat_list[0]['task_categories'] == 1:
        comment_view = ETaskCommentsViewers.objects.create(etcomments=e_task_comments,
                user_id=users_list[0]['assign_by'], task=task, created_by=loggedin_user, owned_by=loggedin_user)
        if loggedin_user == users_list[0]['assign_by']:
            viewer = ETaskCommentsViewers.objects.filter(etcomments=e_task_comments,
                    user_id=users_list[0]['assign_by'],task=task).update(is_view=True)

        assign_by_mail_id = TCoreUserDetail.objects.filter(cu_user_id=users_list[0]['assign_by'],
                                                        cu_is_deleted=False).values('cu_alt_email_id')
        email_list.append(assign_by_mail_id[0]['cu_alt_email_id'])
        if loggedin_user != users_list[0]['assign_by'] and comment_save_send == 'send':
            mail_data = {
                "recipient_name": userdetails(users_list[0]['assign_by']),
                "comment_sub": comments,
                "commented_by": userdetails(users_list[0]['assign_by']),
                "task_subject": task.task_subject,
                "assign_to_name": task.assign_to.get_full_name(),
                "start_date": task.start_date.date(),
                "end_date": task.extended_date.date() if task.extended_date else task.end_date.date()
            }
            send_mail_list('ET-COMMENT', email_list, mail_data, ics='')
    else:
        for user in users_list:
            for k, v in user.items():
                comment_view = ETaskCommentsViewers.objects.create(etcomments=e_task_comments,
                                                                user_id=v,
                                                                task=task,
                                                                created_by=loggedin_user,
                                                                owned_by=loggedin_user
                                                                )
                if loggedin_user == v:
                    viewer = ETaskCommentsViewers.objects.filter(etcomments=e_task_comments,
                            user_id=v, task=task).update(is_view=True)
                if loggedin_user != v:
                    mail_id = TCoreUserDetail.objects.filter(cu_user_id=v,
                                                            cu_is_deleted=False).values(
                        'cu_alt_email_id')
                    email_list.append(mail_id[0]['cu_alt_email_id'])
                    if comment_save_send == 'send':
                        mail_data = {
                            "recipient_name": userdetails(v),
                            "comment_sub": comments,
                            "commented_by": userdetails(loggedin_user),
                            "task_subject": task.task_subject,
                            "assign_to_name": task.assign_to.get_full_name(),
                            "start_date": task.start_date.date(),
                            "end_date": task.extended_date.date() if task.extended_date else task.end_date.date()
                        }
                        send_mail_list('ET-COMMENT', email_list, mail_data, ics='')
    sub_assign_email_list = []
    if user_cat_list[0]['sub_assign_to_user']:
        sub_comment_view = ETaskCommentsViewers.objects.create(etcomments=e_task_comments,
                                                            user_id=user_cat_list[0][
                                                                'sub_assign_to_user'],
                                                            task=task,
                                                            created_by=loggedin_user,
                                                            owned_by=loggedin_user
                                                            )
        if loggedin_user == user_cat_list[0]['sub_assign_to_user']:
            viewer = ETaskCommentsViewers.objects.filter(etcomments=e_task_comments,
                    user_id=user_cat_list[0]['sub_assign_to_user'],task=task).update(is_view=True)

        assign_by_mail_id = TCoreUserDetail.objects.filter(cu_user_id=users_list[0]['assign_by'],
                            cu_is_deleted=False).values('cu_alt_email_id')
        sub_assign_email_list.append(assign_by_mail_id[0]['cu_alt_email_id'])
        if loggedin_user != users_list[0]['assign_by'] and comment_save_send == 'send':
            mail_data = {
                "recipient_name": userdetails(users_list[0]['assign_by']),
                "comment_sub": comments,
                "commented_by": userdetails(user_cat_list[0]['sub_assign_to_user']),
                "task_subject": task.task_subject,
                "assign_to_name": task.assign_to.get_full_name(),
                "start_date": task.start_date.date(),
                "end_date": task.extended_date.date() if task.extended_date else task.end_date.date()
            }
            send_mail_list('ET-COMMENT', sub_assign_email_list, mail_data, ics='')

