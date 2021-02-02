
from django.shortcuts import render
from django.conf import settings
from rest_framework import mixins
from rest_framework import filters
from datetime import datetime, timedelta
import collections
from rest_framework.parsers import FileUploadParser
from django_filters.rest_framework import DjangoFilterBackend
import os
import platform
from django.http import JsonResponse
from decimal import Decimal
#from django.db.models import Q
from custom_exception_message import *
from decimal import *
import math
# from django.contrib.auth.models import *
from django.db.models import F
from django.db.models import Count
from core.models import *
from etask.models import *
from users.models import TCoreUserDetail, UserTempReportingHeadMap
from attendance.models import AttendenceMonthMaster
import re
from dateutil.relativedelta import relativedelta
import platform

from redis_handler import pub as email_pub
from django.template import Context, Template
from mailsend.models import MailHistory, MailTemplate, MailICSMapping
import json


def userdetails(user):
    # print(type(user))
    f_name_l_name = None
    if isinstance(user, (int)):
        name = User.objects.filter(id=user)
        for i in name:
            # print("i",i)
            f_name_l_name = i.first_name + " " + i.last_name
            # print("f_name_l_name",f_name_l_name)
    elif isinstance(user, (str)):
        # print(user ,"str")
        name = User.objects.filter(username=user)
        for i in name:
            # print("i",i)
            f_name_l_name = i.first_name + " " + i.last_name
            # print("f_name_l_name",f_name_l_name)
    else:
        f_name_l_name = None

    return f_name_l_name


def designation(designation):
    if isinstance(designation, (str)):
        desg_data = TCoreUserDetail.objects.filter(cu_user__username=designation)
        if desg_data:
            for desg in desg_data:
                return desg.designation.cod_name
        else:
            return None
    elif isinstance(designation, (int)):
        desg_data = TCoreUserDetail.objects.filter(cu_user=designation)
        if desg_data:
            for desg in desg_data:
                return desg.designation.cod_name
        else:
            return None


def department(department):
    if isinstance(department, (str)):
        desg_data = TCoreUserDetail.objects.filter(cu_user__username=department)
        if desg_data:
            for desg in desg_data:
                return desg.department.cd_name
        else:
            return None
    elif isinstance(department, (int)):
        desg_data = TCoreUserDetail.objects.filter(cu_user=department)
        if desg_data:
            for desg in desg_data:
                return desg.department.cd_name
        else:
            return None


def getHostWithPort(request, media=False):
    if os.environ.get('SERVER_GATEWAY_INTERFACE') == 'Web':
        protocol = 'https://' if request.is_secure() else 'http://'
        url = protocol+request.get_host()+'/media/' if media else protocol+request.get_host()+'/'
    else:
        url = settings.SERVER_URL+'media/' if media else settings.SERVER_URL
    return url

# added by Shubhadeep


def getPathFromMediaURL(url):
    spiltted = url.split('media/')
    relative_path = spiltted[1]
    path = os.path.join(settings.MEDIA_ROOT, relative_path)
    os_name = platform.system().lower()
    if os_name == "windows":
        path = path.replace('/', '\\')
    return path
# --


def raw_query_extract(query):

    return query.query


def round_calculation(days: int, leave_count: int) -> float:
    print('days', days, ":int,", leave_count)
    int_value = days*leave_count//365
    frq_value = round((days*leave_count/365), 2) - int_value
    print("int_value", int_value, "frq_value", frq_value)
    frq_add = 0.0
    if frq_value < 0.25:
        value = float(int_value)+frq_add
    elif frq_value >= 0.25 and frq_value < 0.75:
        frq_add = 0.5
        value = float(int_value)+frq_add
    elif frq_value >= 0.75:
        frq_add = 1.0
        value = float(int_value)+frq_add
    print("value", value)
    return value


def round_calculation_V2(days: int, leave_count: int) -> float:
    # print('days', days,":int,", leave_count)

    return value


def convert24(str1):

    # 1:56PM

    # Checking if last two elements of time
    # is AM and first two elements are 12
    if str1[-2:] == "AM" and str1[:2] == "12":
        return "00" + str1[2:-2]

    # remove the AM
    elif str1[-2:] == "AM":
        # return "0"+str1[:-2]
        return str1[:-2]

    # Checking if last two elements of time
    # is PM and first two elements are 12
    elif str1[-2:] == "PM" and str1[:2] == "12":
        print('str 1', str1[:-2])
        return str1[:-2]

    else:

        # add 12 to hours and remove PM
        return str(int(str1[:1]) + 12) + str1[1:4]


def get_users_under_reporting_head(user=None):
    reporting_heads = list(TCoreUserDetail.objects.filter(reporting_head=user, cu_is_deleted=False, cu_user__isnull=False).values_list('cu_user__id', flat=True))
    temp_reporting_heads = list(UserTempReportingHeadMap.objects.filter(temp_reporting_head=user, is_deleted=False).values_list('user__id', flat=True))
    reporting_heads.extend(temp_reporting_heads)
    return reporting_heads


def get_user_reporting_heads(user=None):
    reporting_head = list(TCoreUserDetail.objects.filter(cu_user=user, cu_is_deleted=False, cu_user__isnull=False).values_list('reporting_head__id', flat=True))
    temp_reporting_heads = list(UserTempReportingHeadMap.objects.filter(user=user, is_deleted=False).values_list('temp_reporting_head__id', flat=True))
    reporting_head.extend(temp_reporting_heads)
    return reporting_head


def get_time_diff(DurationFrom, durationTo):
    date_format = "%H:%M:%S"
    durationTo = datetime.strptime(str(durationTo), date_format)
    DurationFrom = datetime.strptime(str(DurationFrom), date_format)
    timediff = (durationTo-DurationFrom).total_seconds()
    hours = round(timediff / 3600, 2)
    return hours


def get_pagination_offset(page=1, page_count=10):
    return slice(page_count*(page-1), page*page_count)


def create_appointment(reporting_dates=[]):
    reporting_ids = [rd.id for rd in reporting_dates]
    reporting_dates_query = ETaskReportingDates.objects.filter(id__in=reporting_ids)
    for reporting_date_obj in reporting_dates_query:
        reporting_date = reporting_date_obj.reporting_date
        reporting_end_date = reporting_date_obj.reporting_end_date if reporting_date_obj.reporting_end_date else reporting_date
        if reporting_date_obj.is_manual_time_entry:
            task = EtaskTask.objects.get(id=reporting_date_obj.task)
            data = dict()
            data['facilitator'] = 2
            data['appointment_subject'] = task.task_subject
            data['start_date'] = reporting_date
            data['end_date'] = reporting_end_date
            data['start_time'] = reporting_date.time()
            data['end_time'] = reporting_end_date.time()
            data['Appointment_status'] = 'ongoing'
            data['owned_by'] = reporting_date_obj.created_by
            data['created_by'] = reporting_date_obj.created_by
            data['location'] = ''
            apointment_create = EtaskAppointment.objects.create(**data)

            subassign_log = EtaskTaskSubAssignLog.objects.filter(task=task, assign_from=apointment_create.owned_by, is_deleted=False).first()
            assign_to = subassign_log.sub_assign if subassign_log else task.assign_to

            mail = {'name': assign_to.get_full_name(), 'email': assign_to.cu_user.cu_alt_email_id}
            mail_list = [mail, {'name': apointment_create.owned_by.get_full_name(), 'email': apointment_create.owned_by.cu_user.cu_alt_email_id}]
            EtaskInviteEmployee.objects.create(appointment=apointment_create, user=assign_to)

            s_date = reporting_date.strftime("%Y%m%dT%H%M%S")
            e_date = reporting_end_date.strftime("%Y%m%dT%H%M%S")
            invitation_from = '{} ({})'.format(apointment_create.owned_by.get_full_name(), apointment_create.owned_by.cu_user.cu_alt_email_id)
            invited_to = '{} ({})'.format(assign_to.get_full_name(), assign_to.cu_user.cu_alt_email_id)
            ics_data = """BEGIN:VCALENDAR
VERSION:2.0
CALSCALE:GREGORIAN
BEGIN:VEVENT
SUMMARY:Appointment of {}
DTSTART;TZID=Asia/Kolkata:{}
DTEND;TZID=Asia/Kolkata:{}
LOCATION:Shyam Tower,Kolkata-700091
DESCRIPTION: Appointment Invitation From-> {}  Invited People-> {}
STATUS:CONFIRMED
SEQUENCE:3
BEGIN:VALARM
TRIGGER:-PT10M
DESCRIPTION:Pickup Reminder
ACTION:DISPLAY
END:VALARM
END:VEVENT
END:VCALENDAR""".format(apointment_create.appointment_subject, s_date, e_date, invitation_from, invited_to)

            #===============================================#
            for mail_dict in mail_list:
                if mail_dict['email']:
                    mail_data = {
                        "recipient_name": mail_dict['name'],  # modified by manas Paul 21jan20
                        "appointment_subject": apointment_create.appointment_subject,
                        "facilitator_name": apointment_create.owned_by.get_full_name(),
                        "location": 'NA',
                        "start_date": reporting_date.date(),
                        "end_date": reporting_end_date.date(),
                        "start_time": reporting_date.time(),
                        "end_time": reporting_end_date.time(),
                        "internal_invitees": [mail],
                        "external_invitees": [],
                        "invitee_count": 1
                    }
                    send_mail('ETAP', mail_dict['email'], mail_data, ics_data)


def send_mail(code, user_email, mail_data, cc=None, bcc=None, ics='', final_sub=''):
    if bcc is None:
        bcc = list()
    if cc is None:
        cc = list()
    send_mail_list(code, [user_email], mail_data, cc, bcc, ics, final_sub)


def send_mail_list(code, user_email_list, mail_data, cc=None, bcc=None, ics='', final_sub=''):
    if bcc is None:
        bcc = list()
    if cc is None:
        cc = list()
    mail_content = MailTemplate.objects.get(code=code)
    subject = mail_content.subject + final_sub
    template_variable = mail_content.template_variable.split(",")
    html_content = Template(mail_content.html_content)
    match_data_dict = {}
    for data in template_variable:
        if data.strip() in mail_data:
            match_data_dict[data.strip()] = mail_data[data.strip()]
    if match_data_dict:
        context_data = Context(match_data_dict)
        html_content = html_content.render(context_data)

    entry = MailHistory()
    entry.code = code
    entry.recipient_list = json.dumps(user_email_list)
    ## Cc and Bcc are added by Swarup Adhikary(23.12.2020)
    entry.cc = json.dumps(cc)
    entry.bcc = json.dumps(bcc)
    entry.body = html_content
    entry.subject = subject
    entry.attachment = ics
    entry.save()
    success, msg = email_pub.publish('email', [entry.id])

# added by Shubhadeep to handle sequence and uid in ICS files


def get_uid_sequence_for_event(email_id, module, event_id):
    email_id = str(email_id).lower()
    instance = MailICSMapping.objects.filter(module=module, event_id=event_id, email=email_id)
    if instance:
        instance = instance[0]
        instance.sequence += 1
        instance.save()
    else:
        import uuid
        instance = MailICSMapping()
        instance.uuid = uuid.uuid4()
        instance.module = module
        instance.email = email_id
        instance.sequence = 0
        instance.event_id = event_id
        instance.save()
    return (instance.sequence, instance.uuid)
# --


# added by Shubhadeep for writing excel using xlsxwriter
def worksheet_write(worksheet, cell_width_map, row_idx, col_idx, val, cell_format):
    worksheet.write(row_idx, col_idx, val, cell_format)
    width = 8
    if len(str(val)) > 8:
        width = len(str(val)) * 0.9
    if col_idx in cell_width_map and cell_width_map[col_idx] > width:
        width = cell_width_map[col_idx]
    cell_width_map[col_idx] = width
    worksheet.set_column(col_idx, col_idx, width=cell_width_map[col_idx])


def worksheet_merge_range(worksheet, cell_height_map, row_idx1, col_idx1, row_idx2, col_idx2, val, format):
    worksheet.merge_range(row_idx1, col_idx1, row_idx2, col_idx2, val, format)
    height = 15
    for c in str(val):
        if c == '\n':
            height += 16
    if row_idx1 in cell_height_map and cell_height_map[row_idx1] > height:
        height = cell_height_map[row_idx1]
    cell_height_map[row_idx1] = height
    worksheet.set_row(row_idx1, height=cell_height_map[row_idx1])


def worksheet_merge_range_by_width(worksheet, cell_width_map, row_idx1, col_idx1, row_idx2, col_idx2, val, format):
    worksheet.merge_range(row_idx1, col_idx1, row_idx2, col_idx2, val, format)
    width = 8
    if len(str(val)) > 8:
        width = len(str(val)) * 0.9
    col_idx = col_idx1
    if col_idx in cell_width_map and cell_width_map[col_idx] > width:
        width = cell_width_map[col_idx]
    cell_width_map[col_idx] = width
    worksheet.set_column(col_idx, col_idx, width=cell_width_map[col_idx])

def get_last_day_of_month(datetime_obj):
    # get close to the end of the month for any day, and add 4 days 'over'
    next_month = datetime_obj.replace(day=28) + timedelta(days=4)
    # subtract the number of remaining 'overage' days to get last day of current month, or said programattically said, the previous day of the first of next month
    return next_month - timedelta(days=next_month.day)

def get_current_financial_year_details():
    c_date = datetime.now()
    #c_date = '2018-01-01'
    current_financial_year_details = AttendenceMonthMaster.objects.filter(
            year_start_date__date__lte=c_date,
            year_end_date__date__gte=c_date,
            is_deleted=False
            ).values('month_start__date','month_end__date','year_start_date__year','year_end_date__year')
    if  current_financial_year_details:
        return current_financial_year_details.first()
    else :

        raise APIException({'result':{'status':404,'msg':'Current Financial Year Details Not Found'}})
    

