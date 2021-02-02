"""
Created by Shubhadeep on 07-09-2020
"""
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from django.core import serializers as core_serializers
from eticket.models_resource_mgmnt import *
from users.models import TCoreUserDetail
from django.contrib.auth.models import *
import datetime
from rest_framework.response import Response
from pms.custom_filter import custom_filter
from pms.custom_delete import *
from django.db.models import Q
import re
import json

class ETICKETResourceDeviceTypeMasterSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = ETICKETResourceDeviceTypeMaster
        fields = ('__all__')

class ETICKETResourceDeviceMasterSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    # additional fields needed for creating an entry
    assignment_history = serializers.ListField(required=False, allow_empty=True ) # list of dict : employee, assigned_at, assigned_upto
    #--

    # additional fields for get request (listing entries)
    assignment_details = serializers.SerializerMethodField()
    device_type_details = serializers.SerializerMethodField()
    # --

    class Meta:
        model = ETICKETResourceDeviceMaster
        fields = ('__all__')

    def get_device_type_details(self, instacne):        
        return {
                'id': instacne.device_type.id,
                'type_name': instacne.device_type.type_name
                }

    def get_assignment_details(self, instance):
        assignements = ETICKETResourceDeviceAssignment.objects.filter(device=instance).order_by('-assigned_at')
        data = []
        for entry in assignements:
            serialized_string = core_serializers.serialize('json', [entry,])
            serialized_obj = json.loads(serialized_string)[0]['fields']
            user_details = TCoreUserDetail.objects.get(cu_user=entry.employee)
            if entry.employee:
                serialized_obj['employee_details'] = {
                    'id': entry.employee.id,
                    'name': '{0} {1}'.format(entry.employee.first_name, entry.employee.last_name),
                    'department': user_details.department.cd_name if user_details.department else '',
                    'sub_department': user_details.sub_department.cd_name if user_details.sub_department else '',
                    'location': user_details.job_location
                }
            if entry.assigned_by:
                serialized_obj['assigned_by_details'] = {
                    'id': entry.assigned_by.id,
                    'name': '{0} {1}'.format(entry.assigned_by.first_name, entry.assigned_by.last_name)
                }
            if entry.unassigned_by:
                serialized_obj['unassigned_by_details'] = {
                    'id': entry.unassigned_by.id,
                    'name': '{0} {1}'.format(entry.unassigned_by.first_name, entry.unassigned_by.last_name)
                }
            serialized_obj.pop('employee')
            serialized_obj.pop('assigned_by')
            serialized_obj.pop('unassigned_by')
            data.append(serialized_obj)
        return data

    def create(self, validated_data):
        assignment_history = validated_data.get('assignment_history')
        if assignment_history:
            validated_data.pop('assignment_history')
        else:
            assignment_history = []

        instance = ETICKETResourceDeviceMaster.objects.create(**validated_data)
        current_assignment = False
        for assignment in assignment_history:
            if len(assignment.keys()) > 0:
                assignment_entry = {
                    'device': instance,
                    'assigned_at': datetime.datetime.strptime(assignment.get('assigned_at')
                                        , "%Y-%m-%dT%H:%M:%S.%fZ") if assignment.get('assigned_at') else None,
                    'assigned_upto': datetime.datetime.strptime(assignment.get('assigned_upto')
                                        , "%Y-%m-%dT%H:%M:%S.%fZ") if assignment.get('assigned_upto') else None,
                    'assigned_by': validated_data.get('created_by'),
                    'employee': User.objects.get(pk=assignment.get('employee')),
                    'is_current': assignment.get('is_current')
                }
                if assignment_entry['is_current']:
                    current_assignment = True
                ETICKETResourceDeviceAssignment.objects.create(**assignment_entry)
        instance.is_assigned = current_assignment
        instance.save()

        return instance

class ETICKETResourceDeviceAssignmentSerializer(serializers.ModelSerializer):
    assigned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    
    class Meta:
        model = ETICKETResourceDeviceAssignment
        fields = ('__all__')

    def create(self, validated_data):
        assigned_at = datetime.datetime.now()
        if not validated_data.get('assigned_at'):
            validated_data['assigned_at'] = assigned_at
        validated_data['is_current'] = True
        instacne = ETICKETResourceDeviceAssignment.objects.create(**validated_data)
        ETICKETResourceDeviceMaster.objects.filter(pk=instacne.device_id).update(is_assigned=True, updated_at=assigned_at,
                                                                                        updated_by=validated_data.get('assigned_by'))
        
        return instacne

class ETICKETResourceDeviceUnassignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ETICKETResourceDeviceMaster
        fields = ('id',)

    def update(self, instacne, validated_data):
        assigned_upto = datetime.datetime.now()
        unassigned_by = self.context['request'].user
        
        ETICKETResourceDeviceAssignment.objects.filter(device=instacne, assigned_upto=None).update(
            assigned_upto=assigned_upto, unassigned_by=unassigned_by, is_current=False
        )
        instacne.is_assigned = False
        instacne.updated_at = assigned_upto
        instacne.updated_by = unassigned_by
        instacne.save()

        return instacne