from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from core.models import *
from django.contrib.auth.models import *
from rest_framework.exceptions import APIException
from django.conf import settings
from eticket.models import *
from django.db.models import When, Case, Value, CharField, IntegerField, F, Q
from users.models import *
from drf_extra_fields.fields import Base64ImageField  # for image base 64
from django.db import transaction, IntegrityError
from master.models import TMasterModuleOther, TMasterOtherRole, TMasterOtherUser, TMasterModuleRoleUser
from django.db.models.functions import Concat
from django.db.models import Value
from mailsend.views import *
import datetime
import global_function as gf


def get_module_details(instance):
    data = None
    if instance.module:
        data = {
            'id': instance.module.id,
            'name': instance.module.name,
        }
    return data


def get_department_details(instance):
    data = None
    if instance.department:
        data = {}
        dept = TCoreDepartment.objects.filter(~Q(cd_parent_id=0), pk=instance.department.id)
        if dept:
            dept = TCoreDepartment.objects.get(~Q(cd_parent_id=0), pk=instance.department.id)
            data = {
                'id': dept.cd_parent_id,
                'name': TCoreDepartment.objects.only('cd_name').get(pk=dept.cd_parent_id).cd_name,
                'child': {
                    'id': dept.id,
                    'name': dept.cd_name
                }
            }
        else:
            data = {
                'id': instance.department.id,
                'name': TCoreDepartment.objects.only('cd_name').get(pk=instance.department.id).cd_name,
                'child': None
            }
    return data

def get_person_responsible(ETICKETTicket, include_email=False):
    tic_obj = ETICKETTicketAssignHistory.objects.filter(ticket=ETICKETTicket, current_status=True)
    final_lst = []
    for each in tic_obj:
        temp_dict = {'id': each.assigned_to.id,
                    'name': each.assigned_to.first_name + ' ' + each.assigned_to.last_name,
                    'email': TCoreUserDetail.objects.get(cu_user=each.assigned_to).cu_alt_email_id
                    }
        final_lst.append(temp_dict)

    return final_lst


class ETICKETModuleMasterAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    # additional fields for get request (listing entries)
    department_details = serializers.SerializerMethodField()
    # --

    def get_department_details(self, instance):
        return get_department_details(instance)

    class Meta:
        model = ETICKETModuleMaster
        fields = ('__all__')


class EticketReportingHeadAddSerializer(serializers.ModelSerializer):
    created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())

    # additional fields for get request (listing entries)
    department_details = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()
    module_details = serializers.SerializerMethodField()
    reporting_head_name = serializers.SerializerMethodField()
    reporting_head_user_name = serializers.SerializerMethodField()
    # --

    def get_module_details(self, ETICKETReportingHead):
        return get_module_details(ETICKETReportingHead)

    def get_department_details(self, ETICKETReportingHead):
        return get_department_details(ETICKETReportingHead)

    def get_department_name(self, ETICKETReportingHead):
        if ETICKETReportingHead.department:
            return ETICKETReportingHead.department.cd_name
        return None

    def get_reporting_head_user_name(self, ETICKETReportingHead):
        return User.objects.only('username').get(pk=ETICKETReportingHead.reporting_head.id).username

    def get_reporting_head_name(self, ETICKETReportingHead):
        if ETICKETReportingHead.reporting_head:
            return ETICKETReportingHead.reporting_head.first_name + ' ' + ETICKETReportingHead.reporting_head.last_name
        else:
            return None

    def create(self, validated_data):
        dept = validated_data.get('department')
        module = validated_data.get('module')
        if module is not None:
            validated_data['department'] = module.department
        existing_entries = ETICKETReportingHead.objects.filter(department=validated_data.get('department'),
                                                               module=validated_data.get('module'), is_deleted=False)
        if existing_entries:
            instance = existing_entries.first()
            # print ('Existing Reporting Head', instance.department, instance.module, instance.reporting_head)
            instance.reporting_head = validated_data.get('reporting_head')
            instance.save()
        else:
            instance = ETICKETReportingHead.objects.create(**validated_data)
        return instance

    def update(self, instance, validated_data):
        dept = validated_data.get('department')
        module = validated_data.get('module')
        if module is not None:
            validated_data['department'] = module.department
        existing_entries = ETICKETReportingHead.objects.filter(department=validated_data.get('department'),
                                                               module=validated_data.get('module'), is_deleted=False)
        for entry in existing_entries:
            entry.is_deleted = True
            entry.save()
        if module is not None:
            instance.department = module.department
            instance.module = module
        else:
            instance.department = dept

        instance.reporting_head = validated_data.get('reporting_head')
        instance.updated_by = validated_data.get('updated_by')
        instance.is_deleted = False
        instance.save()
        return instance

    class Meta:
        model = ETICKETReportingHead
        fields = ('id', 'module', 'department', 'department_name', 'department_details', 'reporting_head', 'reporting_head_name',
                  'reporting_head_user_name', 'is_deleted', 'created_by', 'updated_by', 'module_details')


class EticketTicketSubjectListByDepartmentAddSerializer(serializers.ModelSerializer):
    created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())

    # additional fields for get request (listing entries)
    department_details = serializers.SerializerMethodField()
    module_details = serializers.SerializerMethodField()
    # --

    class Meta:
        model = ETICKETSubjectOfDepartment
        fields = ('__all__')

    def get_module_details(self, instance):
        return get_module_details(instance)

    def get_department_details(self, instance):
        return get_department_details(instance)

    def create(self, validated_data):
        dept = validated_data.get('department')
        module = validated_data.get('module')
        if module is not None:
            validated_data['department'] = module.department
        instance = ETICKETSubjectOfDepartment.objects.create(**validated_data)
        return instance

    def update(self, instance, validated_data):
        dept = validated_data.get('department')
        module = validated_data.get('module')
        if module is not None:
            instance.department = module.department
            instance.module = module
        else:
            instance.department = dept
        instance.subject = validated_data.get('subject')
        instance.updated_by = validated_data.get('updated_by')
        instance.save()
        return instance


class EticketTicketAddSerializer(serializers.ModelSerializer):
    created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())
    status = serializers.CharField(default="Open")
    created_at = serializers.CharField(required=False)

    class Meta:
        model = ETICKETTicket
        fields = ('id', 'ticket_number', 'subject', 'custom_subject', 'task_duration', 'department', 
                'module', 'priority', 'details', 'status', 'is_deleted', 'created_by', 'created_at', 'primary_assign')

    def create(self, validated_data):
        department = validated_data.get('department')
        module = validated_data.get('module')
        if module is not None:
            reporting_head_details = ETICKETReportingHead.objects.filter(module=module, is_deleted=False)
            if not reporting_head_details:
                reporting_head_details = ETICKETReportingHead.objects.filter(department=module.department, is_deleted=False)[0]
            else:
                reporting_head_details = reporting_head_details[0]
            validated_data['department'] = module.department
        else:
            reporting_head_details = ETICKETReportingHead.objects.filter(department=department, is_deleted=False)[0]

        validated_data['ticket_number'] = "SSILT" + str(int(time.time()))
        validated_data['primary_assign'] = reporting_head_details.reporting_head
        ticket_details = ETICKETTicket.objects.create(**validated_data)

        assigned_to = reporting_head_details.reporting_head
        assign_history = ETICKETTicketAssignHistory(assigned_to=assigned_to, 
                            ticket=ticket_details, updated_by=None)
        assign_history.save()
        status_history = ETICKETTicketStatusHistory(ticket=ticket_details, status=ticket_details.status, 
                        updated_by=None)
        status_history.save()

        mail_id = TCoreUserDetail.objects.get(cu_user=reporting_head_details.reporting_head).cu_alt_email_id
        user = validated_data.get('created_by')
        # ============= Mail Send ==============#
        if mail_id:
            mail_data = {
                "name": reporting_head_details.reporting_head.first_name + ' ' + reporting_head_details.reporting_head.last_name,
                "ticket_no": ticket_details.ticket_number,
                "ticket_sub": ticket_details.custom_subject if ticket_details.custom_subject else ticket_details.subject.subject,
                "priority": ticket_details.priority,
                'details': ticket_details.details,
                'raised_by': user.first_name + ' ' + user.last_name
            }
            gf.send_mail('E-T-DEPT', mail_id, mail_data)
        validated_data['id'] = ticket_details.id
        return validated_data


class EticketTicketEditSerializer(EticketTicketAddSerializer):
    class Meta:
        model = ETICKETTicket
        fields = ('id', 'task_duration')


class EticketTicketDocumentAddSerializer(serializers.ModelSerializer):
    created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = ETICKETTicketDoc
        fields = ('id', 'ticket', 'document', 'created_by')


class EticketTicketRaisedByMeListSerializer(serializers.ModelSerializer):
    subject = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    person_responsible = serializers.SerializerMethodField()
    raised_by_name = serializers.SerializerMethodField()
    primary_assign = serializers.SerializerMethodField()
    assigned_to_department = serializers.SerializerMethodField()
    document_details = serializers.SerializerMethodField()
    comment_details = serializers.SerializerMethodField()
    department_details = serializers.SerializerMethodField()
    module_details = serializers.SerializerMethodField()

    def get_module_details(self, ETICKETTicket):
        return get_module_details(ETICKETTicket)

    def get_department_details(self, ETICKETTicket):
        return get_department_details(ETICKETTicket)

    def get_subject(self, ETICKETTicket):
        if ETICKETTicket.custom_subject is None:
            return ETICKETTicket.subject.subject
        else:
            return ETICKETTicket.custom_subject

    def get_comment_count(self, ETICKETTicket):
        if ETICKETTicketComment.objects.filter(ticket=ETICKETTicket.id):
            return ETICKETTicketComment.objects.filter(ticket=ETICKETTicket.id).count()
        else:
            return 0

    # updated by Shubhadeep
    def get_person_responsible(self, ETICKETTicket):
        return get_person_responsible(ETICKETTicket)

    def get_raised_by_name(self, ETICKETTicket):
        if ETICKETTicket.created_by:
            return ETICKETTicket.created_by.first_name + ' '+ETICKETTicket.created_by.last_name
        else:
            return None

    def get_primary_assign(self, ETICKETTicket):
        if ETICKETTicket.primary_assign:
            return {
                'id': ETICKETTicket.primary_assign.id,
                'name': ETICKETTicket.primary_assign.first_name + ' '+ETICKETTicket.primary_assign.last_name
            }
        
        return None

    def get_assigned_to_department(self, ETICKETTicket):
        if ETICKETTicket.department:
            return ETICKETTicket.department.cd_name
        else:
            return None

    def get_document_details(self, ETICKETTicket):
        document = ETICKETTicketDoc.objects.filter(ticket=ETICKETTicket)
        request = self.context.get('request')
        response_list = []
        for each_document in document:
            file_url = request.build_absolute_uri(each_document.document.url)
            each_data = {
                "id": int(each_document.id),
                "document": file_url,
            }
            # print('each_data',each_data)
            response_list.append(each_data)
        return response_list

    def get_comment_details(self, ETICKETTicket):
        comment = ETICKETTicketComment.objects.annotate(
            name=Concat('created_by__first_name', Value(' '), 'created_by__last_name')).filter(
                ticket=ETICKETTicket).values('id', 'ticket', 'comment',
                                             'name', 'created_at')
        return comment

    class Meta:
        model = ETICKETTicket
        fields = ('id', 'ticket_number', 'task_duration', 'subject', 'department', 'assigned_to_department', 'module_details',
                  'person_responsible', 'priority', 'details', 'status', 'is_deleted', 'created_by', 'created_at', 'updated_at',
                  'ticket_closed_date', 'comment_count', 'document_details', 'department_details', 'comment_details', 'primary_assign', 'raised_by_name')


class EticketTicketChangeStatusSerializer(serializers.ModelSerializer):
    updated_by = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = ETICKETTicket
        fields = ('id', 'status', 'ticket_closed_date', 'updated_by')

    def update(self, instance, validated_data):
        ticket = instance
        old_status = ticket.status
        new_status = validated_data.get('status')
        send_to_assignee = False
        if old_status.lower() == 'closed' or old_status.lower() == 'completed':
            if new_status.lower() == 'open':
                new_status = 're-open'
                send_to_assignee = True
        elif new_status.lower() == 'closed':
            send_to_assignee = True

        if validated_data.get('status').lower() == 'closed' or validated_data.get('status').lower() == 'completed':
            instance.status = validated_data.get('status')
            instance.ticket_closed_date = datetime.datetime.now()
        else:
            instance.status = validated_data.get('status')

        status_history = ETICKETTicketStatusHistory(ticket=ticket, status=ticket.status,
                                                    updated_by=validated_data.get('updated_by'))
        status_history.save()

        mail_id_user = TCoreUserDetail.objects.get(cu_user=ticket.created_by).cu_alt_email_id
        # ============= Mail Send ==============#
        if mail_id_user:
            mail_data = {
                "name": ticket.created_by.first_name + ' ' + ticket.created_by.last_name,
                "ticket_no": ticket.ticket_number,
                "ticket_sub": ticket.custom_subject if ticket.custom_subject else ticket.subject.subject,
                "priority": ticket.priority,
                "details": ticket.details,
                "old_status": old_status,
                "new_status": new_status
            }
            gf.send_mail('E-T-DEPT-Status-Owner', mail_id_user, mail_data)
        if send_to_assignee:
            assignee_list = get_person_responsible(ticket, include_email=True)
            for assignee in assignee_list:
                if assignee['email']:
                    mail_data2 = {
                        "name": assignee['name'],
                        "ticket_no": ticket.ticket_number,
                        "ticket_sub": ticket.custom_subject if ticket.custom_subject else ticket.subject.subject,
                        "priority": ticket.priority,
                        "details": ticket.details,
                        "old_status": old_status,
                        "new_status": new_status,
                        "raised_by": ticket.created_by.first_name + ' ' + ticket.created_by.last_name,
                    }
                    gf.send_mail('E-T-DEPT-Status-Assignee', assignee['email'], mail_data2)
        instance.save()

        return instance


class EticketTicketChangeMassStatusSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    tickets = serializers.ListField(required=False)

    class Meta:
        model = ETICKETTicket
        fields = ('id', 'status', 'tickets', 'updated_by')

    def create(self, validated_data):
        updated_by = validated_data.get('updated_by')
        ticket_ids = validated_data.get('tickets', [])
        status = validated_data.get('status', None)
        cur_date = datetime.datetime.now()
        for ticket_id in ticket_ids:
            ticket = ETICKETTicket.objects.get(pk=ticket_id)
            old_status = ticket.status
            new_status = status
            send_to_assignee = False
            if old_status.lower() == 'closed' or old_status.lower() == 'completed':
                if new_status.lower() == 'open':
                    new_status = 're-open'
                    send_to_assignee = True
            elif new_status.lower() == 'closed':
                send_to_assignee = True

            if status.lower() == 'closed' or status.lower() == 'completed':
                ticket.status = validated_data.get('status')
                ticket.ticket_closed_date = cur_date
            else:
                ticket.status = validated_data.get('status')
            status_history = ETICKETTicketStatusHistory(ticket=ticket, status=ticket.status,
                                                        updated_by=updated_by)
            status_history.save()
            mail_id_user = TCoreUserDetail.objects.get(cu_user=ticket.created_by).cu_alt_email_id
            # ============= Mail Send ==============#
            if mail_id_user:
                mail_data = {
                    "name": ticket.created_by.first_name + ' ' + ticket.created_by.last_name,
                    "ticket_no": ticket.ticket_number,
                    "ticket_sub": ticket.custom_subject if ticket.custom_subject else ticket.subject.subject,
                    "priority": ticket.priority,
                    "details": ticket.details,
                    "old_status": old_status,
                    "new_status": new_status
                }
                gf.send_mail('E-T-DEPT-Status-Owner', mail_id_user, mail_data)
            if send_to_assignee:
                assignee_list = get_person_responsible(ticket, include_email=True)
                for assignee in assignee_list:
                    if assignee['email']:
                        mail_data2 = {
                            "name": assignee['name'],
                            "ticket_no": ticket.ticket_number,
                            "ticket_sub": ticket.custom_subject if ticket.custom_subject else ticket.subject.subject,
                            "priority": ticket.priority,
                            "details": ticket.details,
                            "old_status": old_status,
                            "new_status": new_status,
                            "raised_by": ticket.created_by.first_name + ' ' + ticket.created_by.last_name,
                        }
                        gf.send_mail('E-T-DEPT-Status-Assignee', assignee['email'], mail_data2)
            ticket.save()

        return validated_data


class EticketTicketAssignedToMeListSerializer(serializers.ModelSerializer):
    # udpated by Shubhadeep
    # department_users = serializers.SerializerMethodField()
    department_details = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    assigned_to_department = serializers.SerializerMethodField()
    raised_by_name = serializers.SerializerMethodField()
    document_details = serializers.SerializerMethodField()
    comment_details = serializers.SerializerMethodField()
    person_responsible = serializers.SerializerMethodField()
    primary_assign = serializers.SerializerMethodField()
    subject = serializers.SerializerMethodField()
    module_details = serializers.SerializerMethodField()

    def get_module_details(self, ETICKETTicket):
        return get_module_details(ETICKETTicket)

    def get_subject(self, ETICKETTicket):
        if ETICKETTicket.custom_subject is None:
            return ETICKETTicket.subject.subject
        else:
            return ETICKETTicket.custom_subject

    def get_department_details(self, ETICKETTicket):
        return get_department_details(ETICKETTicket)

    def get_department_users(self, ETICKETTicket):
        dept = TCoreDepartment.objects.filter(~Q(cd_parent_id=0), pk=ETICKETTicket.department.id)
        if dept:
            dept = TCoreDepartment.objects.get(~Q(cd_parent_id=0), pk=ETICKETTicket.department.id)
            # print("dept",dept)
            result = TCoreUserDetail.objects.annotate(
                name=Concat('cu_user__first_name', Value(' '), 'cu_user__last_name')).filter(department=dept.cd_parent_id).values('cu_user', 'name')
            # print("result parent",result)
            return result
        else:
            # print("ETICKETTicket.department",ETICKETTicket.department)
            result = TCoreUserDetail.objects.annotate(
                name=Concat('cu_user__first_name', Value(' '), 'cu_user__last_name')).filter(department=ETICKETTicket.department).values('cu_user', 'name')
            # print("result wo parent",result)
            return result

    def get_comment_count(self, ETICKETTicket):
        if ETICKETTicketComment.objects.filter(ticket=ETICKETTicket.id):
            return ETICKETTicketComment.objects.filter(ticket=ETICKETTicket.id).count()
        else:
            return 0

    def get_person_responsible(self, ETICKETTicket):
        return get_person_responsible(ETICKETTicket)


    def get_primary_assign(self, ETICKETTicket):
        if ETICKETTicket.primary_assign:
            return {
                'id': ETICKETTicket.primary_assign.id,
                'name': ETICKETTicket.primary_assign.first_name + ' '+ETICKETTicket.primary_assign.last_name
            }
        
        return None

    def get_assigned_to_department(self, ETICKETTicket):
        if ETICKETTicket.department:
            return ETICKETTicket.department.cd_name
        else:
            return None

    def get_raised_by_name(self, ETICKETTicket):
        if ETICKETTicket.created_by:
            return ETICKETTicket.created_by.first_name + ' '+ETICKETTicket.created_by.last_name
        else:
            return None

    def get_document_details(self, ETICKETTicket):
        document = ETICKETTicketDoc.objects.filter(ticket=ETICKETTicket)
        request = self.context.get('request')
        response_list = []
        for each_document in document:
            file_url = request.build_absolute_uri(each_document.document.url)
            each_data = {
                "id": int(each_document.id),
                "document": file_url,
            }
            # print('each_data',each_data)
            response_list.append(each_data)
        return response_list

    def get_comment_details(self, ETICKETTicket):
        comment = ETICKETTicketComment.objects.annotate(
            name=Concat('created_by__first_name', Value(' '), 'created_by__last_name')).filter(
                ticket=ETICKETTicket).values('id', 'ticket', 'comment',
                                             'name', 'created_at')
        return comment

    class Meta:
        model = ETICKETTicket
        fields = ('id', 'ticket_number', 'task_duration', 'subject', 'department', 'assigned_to_department', 'raised_by_name', 'module_details',
                  'priority', 'details', 'status', 'is_deleted', 'created_by', 'created_at', 'updated_at', 'ticket_closed_date', 'person_responsible',
                  'comment_count', 'document_details', 'comment_details', 'department_details', 'primary_assign')


class EticketTicketCommentAddSerializer(serializers.ModelSerializer):
    created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())
    name = serializers.SerializerMethodField()

    def get_name(self, ETICKETTicketComment):
        if ETICKETTicketComment.created_by:
            return ETICKETTicketComment.created_by.first_name + ' '+ETICKETTicketComment.created_by.last_name

    class Meta:
        model = ETICKETTicketComment
        fields = ('id', 'ticket', 'comment', 'created_by', 'created_at', 'name')


# class EticketTicketChangePersonResponsibleSerializer(serializers.ModelSerializer):
#     updated_by = serializers.HiddenField(default=serializers.CurrentUserDefault())
#     assigned_to = serializers.IntegerField()
    
#     class Meta:
#         model = ETICKETTicket
#         fields = ('id', 'assigned_to', 'updated_by')

#     def update(self, instance, validated_data):
#         ticket = instance
#         assigned_to_details = TCoreUserDetail.objects.get(pk=validated_data.get('assigned_to'))
#         instance.assigned_to = assigned_to_details
#         assignee_list = get_person_responsible(ticket, include_email=True)
#         assign_history = ETICKETTicketAssignHistory(assigned_to=assigned_to_details,
#                                                     ticket=ticket, updated_by=validated_data.get('updated_by'))
#         assign_history.save()
#         mail_id = TCoreUserDetail.objects.get(cu_user=assigned_to_details).cu_alt_email_id
#         # ============= Mail Send ==============#
#         if mail_id:
#             mail_data = {
#                 "name": assigned_to_details.first_name + ' ' + assigned_to_details.last_name,
#                 "ticket_no": ticket.ticket_number,
#                 "ticket_sub": ticket.custom_subject if ticket.custom_subject else ticket.subject.subject,
#                 "priority": ticket.priority,
#                 'details': ticket.details
#             }
#             gf.send_mail('E-T-DEPT-Assign', mail_id, mail_data)

#         for old_assignee in assignee_list:
#             if old_assignee['email']:
#                 mail_data2 = {
#                     "name": old_assignee['name'],
#                     "ticket_no": ticket.ticket_number,
#                     "ticket_sub": ticket.custom_subject if ticket.custom_subject else ticket.subject.subject,
#                     "priority": ticket.priority,
#                     'details': ticket.details
#                 }
#                 gf.send_mail('E-T-DEPT-Unassign', old_assignee['email'], mail_data2)
#         instance.save()

#         return instance

class EticketTicketChangeMassPersonResponsibleSerializer(serializers.ModelSerializer):
    ticket_id = serializers.IntegerField(required=False)
    updated_by = serializers.HiddenField(default=serializers.CurrentUserDefault())
    assigned_to = serializers.ListField(required=False)
    class Meta:
        model = ETICKETTicket
        fields = ('ticket_id','assigned_to', 'updated_by')

    def create(self, validated_data):
        ticket = ETICKETTicket.objects.get(id=validated_data.get('ticket_id'))
        assigned_to_ids = validated_data.get('assigned_to')
        old_assigned_ids = []
        old_assign = ETICKETTicketAssignHistory.objects.filter(ticket=ticket, current_status=True)
        for each in old_assign:
            print ('id check 1', each.assigned_to.id, assigned_to_ids)
            if each.assigned_to.id not in assigned_to_ids:
                old_assignee = {
                    'name': each.assigned_to.get_full_name(),
                    'email': TCoreUserDetail.objects.get(cu_user=each.assigned_to).cu_alt_email_id
                }
                each.current_status = False
                each.save()
                if old_assignee['email']:
                    mail_data2 = {
                        "name": old_assignee['name'],
                        "ticket_no": ticket.ticket_number,
                        "ticket_sub": ticket.custom_subject if ticket.custom_subject else ticket.subject.subject,
                        "priority": ticket.priority,
                        'details': ticket.details
                    }
                    gf.send_mail('E-T-DEPT-Unassign', old_assignee['email'], mail_data2)
            old_assigned_ids.append(each.assigned_to.id)
        for assign_to in assigned_to_ids:
            print ('id check 2', assign_to, old_assigned_ids)
            if assign_to not in old_assigned_ids:
                assigned_to_details = User.objects.get(id=assign_to)
                assign_history = ETICKETTicketAssignHistory(assigned_to=assigned_to_details,
                                                            ticket=ticket, updated_by=validated_data.get('updated_by'))
                assign_history.save()
                mail_id = TCoreUserDetail.objects.get(cu_user=assigned_to_details).cu_alt_email_id
                # ============= Mail Send ==============#
                if mail_id:
                    mail_data = {
                        "name": assigned_to_details.first_name + ' ' + assigned_to_details.last_name,
                        "ticket_no": ticket.ticket_number,
                        "ticket_sub": ticket.custom_subject if ticket.custom_subject else ticket.subject.subject,
                        "priority": ticket.priority,
                        'details': ticket.details
                    }
                    gf.send_mail('E-T-DEPT-Assign', mail_id, mail_data)

        ticket.save()
        return validated_data

class EticketTicketSubjectListByDepartmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = ETICKETSubjectOfDepartment
        fields = ('id', 'subject', 'department', 'is_deleted', 'created_by', 'created_at')


class ETicketUserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=False)
    email = serializers.CharField(required=False)
    department_details = serializers.SerializerMethodField()
    employee_code = serializers.SerializerMethodField()
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    is_superuser = serializers.BooleanField(required=False)
    is_active = serializers.BooleanField(required=False)

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'username', 'email', 'is_superuser', 'is_active', 'department_details', 'employee_code')

    def get_employee_code(self, User):
        user = TCoreUserDetail.objects.get(cu_user_id=User.id)
        return user.cu_emp_code

    def get_department_details(self, User):
        user = TCoreUserDetail.objects.get(cu_user_id=User.id)
        data = {}
        if user.department:
            data['dept'] = user.department.id
            data['dept_name'] = user.department.cd_name
        if user.sub_department:
            data['sub_dept'] = user.sub_department.id
            data['sub_dept_name'] = user.sub_department.cd_name
        return data
