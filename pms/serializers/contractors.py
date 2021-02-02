from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from pms.models.module_project import *
from pms.models.module_contractors import *
from django.contrib.auth.models import *
import time
from django.db import transaction, IntegrityError
from drf_extra_fields.fields import Base64ImageField
import os
from rest_framework.exceptions import APIException
import datetime
from rest_framework.response import Response
from pms.custom_filter import custom_filter
import pandas as pd
import numpy as np
import xlrd
from pms.custom_delete import *
from django.db.models import Q
import re
import json
from global_notification import send_notification, store_sent_notification
from global_function import send_mail,getHostWithPort
from django.db.models.functions import Concat
from django.db.models import Value,CharField

# Category

class ContractorsCategoryAddSerializer(serializers.ModelSerializer):
	created_by = serializers.CharField(default=serializers.CurrentUserDefault())
	class Meta:
		model = PmsContractorsCategoryMaster
		fields = '__all__'

class ContractorsCategoryListSerializer(serializers.ModelSerializer):	
	class Meta:
		model = PmsContractorsCategoryMaster
		fields = '__all__'

class ContractorsCategorySingleSerializer(serializers.ModelSerializer):
	created_by = serializers.CharField(default=serializers.CurrentUserDefault())
	
	class Meta:
		model = PmsContractorsCategoryMaster
		fields = '__all__'
		
class ContractorsCategoryEditSerializer(serializers.ModelSerializer):
	updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
	
	class Meta:
		model = PmsContractorsCategoryMaster
		fields = '__all__'

class ContractorsCategoryDeleteSerializer(serializers.ModelSerializer):
	updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
	contractors_exist = serializers.BooleanField(required=False)
	
	class Meta:
		model = PmsContractorsCategoryMaster
		fields = ('id','is_deleted','updated_by','contractors_exist')
	
	def update(self, instance, validated_data):
		try:
			with transaction.atomic():
				contractors_exist = True if 'contractors_exist' in validated_data else False
				if contractors_exist:
					instance.is_deleted = True
					instance.updated_by = validated_data.get('updated_by')
					instance.save()
					contractor_details = PmsContractor.objects.filter(category=instance,is_deleted=False)
					if contractor_details:
						for e_contractor_exist in contractor_details:
							e_contractor_exist.is_deleted = True
							e_contractor_exist.updated_by = validated_data.get('updated_by')
							e_contractor_exist.save()
					return instance
				else:
					contractor_details = PmsContractor.objects.filter(category=instance,is_deleted=False)
					if contractor_details:
						validated_data['contractors_exist'] = True
						return validated_data
					else:
						instance.is_deleted = True
						instance.updated_by = validated_data.get('updated_by')
						instance.save()
						return instance
						
					
				

		except Exception as e:
			raise APIException({"msg": e, "request_status": 0})

# Contractors

class ContractorsAddSerializer(serializers.ModelSerializer):
	created_by = serializers.CharField(default=serializers.CurrentUserDefault())
	email =  serializers.CharField(required=False,allow_null=True,allow_blank=True)
	website = serializers.CharField(required=False,allow_null=True,allow_blank=True)
	class Meta:
		model = PmsContractor
		fields = '__all__'

class ContractorsListSerializer(serializers.ModelSerializer):
	
    class Meta:
        model = PmsContractor
        fields = '__all__'
        depth = 1
	
class ContractorsEditSerializer(serializers.ModelSerializer):
	updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
	email =  serializers.CharField(required=False,allow_null=True,allow_blank=True)
	website = serializers.CharField(required=False,allow_null=True,allow_blank=True)
	class Meta:
		model = PmsContractor
		fields = '__all__'
		
class ContractorsDeleteSerializer(serializers.ModelSerializer):
	updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
	
	class Meta:
		model = PmsContractor
		fields = ('id','is_deleted','updated_by',)


	