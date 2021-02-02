from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from tdms.models import *
from django.contrib.auth.models import *
import time
from django.db import transaction, IntegrityError
from drf_extra_fields.fields import Base64ImageField
import os
from rest_framework.exceptions import APIException
import datetime
from rest_framework.response import Response
from tdms.custom_filter import custom_filter
import pandas as pd
import numpy as np
import xlrd
from tdms.custom_delete import *
from django.db.models import Q
import re
import json
from datetime import datetime


#:::::::::::: PROJECTS ::::::::::::::::::::::::::::#
class DailyWorkAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owner = serializers.CharField(default=serializers.CurrentUserDefault())
    works_done = serializers.ListField(required=False)

    class Meta:
        model = TdmsDailyWorkSheet
        fields = ('created_by','owner','works_done')
        # extra_fields = ('items', 'paid_for',)

    def create(self, validated_data):
        try:
            print('validated_data', validated_data)
            obj_lst = validated_data.pop('works_done') if 'works_done' in validated_data else list()
            created_by = validated_data.pop('created_by')
            owner = validated_data.pop('owner')
            print('items', type(obj_lst))
            if obj_lst:
                for item in obj_lst:
                    print(item)
                    data = {}
                    data['owner'] = owner
                    data['created_by'] = created_by
                    data['work_done'] = item['work']
                    date = datetime.strptime(item['date'], "%Y-%m-%dT%H:%M:%S.%fZ")
                    print(date.date())
                    data['date'] = date
                    start_time = datetime.strptime(item['start_time'], "%Y-%m-%dT%H:%M:%S.%fZ")
                    data['start_time'] = start_time
                    end_time = datetime.strptime(item['end_time'], "%Y-%m-%dT%H:%M:%S.%fZ")
                    data['end_time'] = end_time
                    print(start_time,end_time)
                    a=TdmsDailyWorkSheet.objects.get_or_create(**data)
                    print(a)
            return validated_data
        except Exception as e:
            raise APIException({"msg": e, "request_status": 0})


class DailyWorkListSerializer(serializers.ModelSerializer):
    class Meta:
        model = TdmsDailyWorkSheet
        fields = "__all__"
        # extra_fields = ('items', 'paid_for',)


class DailyWorkSheetEditSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = TdmsDailyWorkSheet
        fields = ('work_done', 'date', 'start_time', 'end_time', 'updated_by')

    def update(self, instance, validated_data):
        instance.work_done = validated_data.get('work_done')
        instance.date = validated_data.get('date',instance.date)
        instance.start_time = validated_data.get('start_time', instance.start_time)
        instance.end_time = validated_data.get('end_time', instance.end_time)
        instance.updated_by = validated_data.get('updated_by')
        instance.save()
        return instance


class DailyWorkSheetDeleteSerializer(serializers.ModelSerializer):

    class Meta:
        model = TdmsDailyWorkSheet
        fields = '__all__'

    def update(self, instance, validated_data):
        instance.is_deleted = True
        instance.save()
        return instance

class DaylyWorkSheetListDownloadSerializerv(serializers.ModelSerializer):
    date = serializers.SerializerMethodField()
    work_done = serializers.SerializerMethodField()
    start_time = serializers.SerializerMethodField()
    end_time = serializers.SerializerMethodField()

    def get_date(self, obj):
        return obj.date.strftime("%d %b %Y") if obj.date else ''

    def get_work_done(self,obj):
        # task_name = obj.task_name
        if obj.work_done:
            work_done = obj.work_done
        else:
            work_done = ''
        return work_done

    def get_start_time(self, obj):
        return obj.start_time.strftime("%I:%M %p") if obj.start_time else ''

    def get_end_time(self, obj):
        return obj.end_time.strftime("%I:%M %p") if obj.end_time else ''



    class Meta:
        model = TdmsDailyWorkSheet
        fields = ('date','start_time', 'end_time','work_done')