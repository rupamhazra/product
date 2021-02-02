import copy
import json
from crm.tasks import task_schedule_reminder
import numpy as np
import pandas as pd
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q, F, Sum
from rest_framework.exceptions import APIException
from rest_framework.fields import IntegerField, FileField
from rest_framework.serializers import (ModelSerializer, SerializerMethodField, CurrentUserDefault, CharField,
                                        ListField, BooleanField)
from datetime import datetime, timedelta

from SSIL_SSO_MS import settings

from sscrm.models import (SSCrmCustomer,SSCrmContractType,SSCrmCustomerCodeType)


# :::::::::::::::::::::: Customer ::::::::::::::::::::::::::: #
class SSCrmCustomerAddSerializer(ModelSerializer):
    created_by = CharField(default=CurrentUserDefault())

    class Meta:
        model = SSCrmCustomer
        fields = '__all__'


class SSCrmCustomerEditSerializer(ModelSerializer):
    updated_by = CharField(default=CurrentUserDefault())

    class Meta:
        model = SSCrmCustomer
        fields = '__all__'


class SSCrmCustomerDeleteSerializer(ModelSerializer):
    updated_by = CharField(default=CurrentUserDefault())
    deleted_by = CharField(default=CurrentUserDefault())

    class Meta:
        model = SSCrmCustomer
        fields = '__all__'

    def update(self, instance, validated_data):
        with transaction.atomic():
            instance.is_deleted=True
            instance.updated_by = validated_data.get('updated_by')
            instance.deleted_by = validated_data.get('deleted_by')
            instance.save()
            return instance

#:::::::::::::::::::::::: CustomerCodeType ::::::::::::::::::::::::::: #
class SSCrmCustomerCodeTypeDeleteViewAddSerializer(ModelSerializer):
    created_by = CharField(default=CurrentUserDefault())

    class Meta:
        model = SSCrmCustomerCodeType
        fields = '__all__'


class SSCrmCustomerCodeTypeDeleteViewEditSerializer(ModelSerializer):
    updated_by = CharField(default=CurrentUserDefault())

    class Meta:
        model = SSCrmCustomerCodeType
        fields = '__all__'


class SSCrmCustomerCodeTypeDeleteViewDeleteSerializer(ModelSerializer):
    updated_by = CharField(default=CurrentUserDefault())
    deleted_by = CharField(default=CurrentUserDefault())

    class Meta:
        model = SSCrmCustomerCodeType
        fields = '__all__'

    def update(self, instance, validated_data):
        with transaction.atomic():
            instance.is_deleted=True
            instance.updated_by = validated_data.get('updated_by')
            instance.deleted_by = validated_data.get('deleted_by')
            instance.save()
            return instance


#:::::::::::::::::::::::: ContractType ::::::::::::::::::::::::::: #
class SSCrmContractTypeAddSerializer(ModelSerializer):
    created_by = CharField(default=CurrentUserDefault())

    class Meta:
        model = SSCrmContractType
        fields = '__all__'


class SSCrmContractTypeEditSerializer(ModelSerializer):
    updated_by = CharField(default=CurrentUserDefault())

    class Meta:
        model = SSCrmContractType
        fields = '__all__'


class SSCrmContractTypeDeleteSerializer(ModelSerializer):
    updated_by = CharField(default=CurrentUserDefault())
    deleted_by = CharField(default=CurrentUserDefault())

    class Meta:
        model = SSCrmContractType
        fields = '__all__'

    def update(self, instance, validated_data):
        with transaction.atomic():
            instance.is_deleted=True
            instance.updated_by = validated_data.get('updated_by')
            instance.deleted_by = validated_data.get('deleted_by')
            instance.save()
            return instance