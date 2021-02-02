from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from pms.models.module_project import *
from pms.models.module_site_bills_invoices import *
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

class PmsSiteBillsInvoicesApprovalConfigurationSerializer(serializers.ModelSerializer):
	created_by = serializers.CharField(default=serializers.CurrentUserDefault())
	class Meta:
		model = PmsSiteBillsInvoicesApprovalConfiguration
		fields = '__all__'

class SiteBillsInvoicesCategoryAddSerializer(serializers.ModelSerializer):
	created_by = serializers.CharField(default=serializers.CurrentUserDefault())
	approval_configuration = serializers.ListField(required=False)
	
	class Meta:
		model = PmsSiteBillsInvoicesCategoryMaster
		fields = ('name','icon','approval_configuration','created_by',)

	def create(self,validated_data):
		try:
			with transaction.atomic():
				approval_configuration = validated_data.pop('approval_configuration')
				_categoryMaster = PmsSiteBillsInvoicesCategoryMaster.objects.create(**validated_data)
				
				for e_approval_configuration in approval_configuration:
					e_approval_configuration['category'] = _categoryMaster
					e_approval_configuration['created_by'] = validated_data.get('created_by')
					#print('e_approval_configuration',e_approval_configuration)
					PmsSiteBillsInvoicesApprovalConfiguration.objects.create(**e_approval_configuration)

				return validated_data
		
		except Exception as e:
			raise APIException({"msg": e, "request_status": 0})

class SiteBillsInvoicesCategoryListSerializer(serializers.ModelSerializer):
	approval_configuration = serializers.SerializerMethodField()
	
	def get_approval_configuration(self,PmsSiteBillsInvoicesCategoryMaster):
		return PmsSiteBillsInvoicesApprovalConfiguration.objects.filter(
		is_deleted=False,
		category=PmsSiteBillsInvoicesCategoryMaster.id
		).annotate(
		approver_name=
		Concat(
		'user__first_name',
		Value(' '),
		'user__last_name',
		output_field=CharField()
		)
		).values('id','category','level','level_no','user','approver_name')
		
	class Meta:
		model = PmsSiteBillsInvoicesCategoryMaster
		fields = '__all__'
		extra_fields = ('approval_configuration',)

class SiteBillsInvoicesCategorySingleSerializer(serializers.ModelSerializer):
	created_by = serializers.CharField(default=serializers.CurrentUserDefault())
	approval_configuration = serializers.SerializerMethodField()
	
	def get_approval_configuration(self,PmsSiteBillsInvoicesCategoryMaster):
		return PmsSiteBillsInvoicesApprovalConfiguration.objects.filter(is_deleted=False,category=PmsSiteBillsInvoicesCategoryMaster.id).values()
		
	class Meta:
		model = PmsSiteBillsInvoicesCategoryMaster
		fields = '__all__'
		extra_fields = ('approval_configuration',)

class SiteBillsInvoicesCategoryEditSerializer(serializers.ModelSerializer):
	updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
	approval_configuration = serializers.ListField(required=False)
	
	class Meta:
		model = PmsSiteBillsInvoicesCategoryMaster
		fields = '__all__'
		extra_fields = ('approval_configuration',)
		
	def update(self, instance, validated_data):
		#print('validated_data',validated_data)
		try:
			with transaction.atomic():
				approval_configuration = validated_data.pop('approval_configuration')
				instance.name = validated_data.get('name')
				instance.icon = validated_data.get('icon')
				instance.updated_by = validated_data.get('updated_by')
				instance.save()

				for e_approval_configuration in approval_configuration:
					e_approval_configuration['category'] = instance
					#print('e_approval_configuration',e_approval_configuration)
					if e_approval_configuration['check_level'] == 'new':
						p3 = PmsSiteBillsInvoicesApprovalConfiguration.objects.create(
						category = e_approval_configuration['category'],
						level = e_approval_configuration['level'],
						level_no = e_approval_configuration['level_no'],
						user_id = e_approval_configuration['user_id'],
						created_by = validated_data.get('updated_by')
						)
						#print('p3',p3)
						
					if e_approval_configuration['check_level'] == 'drop':
						highest_level_no = PmsSiteBillsInvoicesApprovalConfiguration.objects.filter(is_deleted=False).order_by('-level_no')
						if highest_level_no:
							highest_level = highest_level_no.values_list('level',flat=True)[0]
							highest_level_no = highest_level_no.values_list('level_no',flat=True)[0]

						#print('highest_level',highest_level)
						siteBillsInvoices = PmsSiteBillsInvoices.objects.filter(
							category = e_approval_configuration['category'],
							current_approval_level_view=highest_level,
							#status='Approve',
							is_deleted=False
							)
						#print('siteBillsInvoices',siteBillsInvoices)
						if siteBillsInvoices:
							for e_siteBillsInvoices in siteBillsInvoices:
								siteBillsInvoices.filter(pk = e_siteBillsInvoices.id).update(
										current_approval_level_view = 'L' + str(highest_level_no - 1),
										current_approval_level_no = highest_level_no - 1,
										status='Approve',
									)

						siteBillsInvoicesApproval = PmsSiteBillsInvoicesApproval.objects.filter(
							approval_user_level__level=highest_level,
							approval_user_level__category = e_approval_configuration['category'],
							approval_user_level__level_no = highest_level_no
							)

						if siteBillsInvoicesApproval:
							for e_siteBillsInvoicesApproval in siteBillsInvoicesApproval:
								siteBillsInvoicesApproval.filter(pk=e_siteBillsInvoicesApproval.id).update(
									is_deleted=True
									)

						p2 = PmsSiteBillsInvoicesApprovalConfiguration.objects.filter(pk=e_approval_configuration['id']).update(is_deleted=True)
						#print('p2',p2)
						
					if e_approval_configuration['check_level'] == 'exist':
						p1 = PmsSiteBillsInvoicesApprovalConfiguration.objects.filter(
						pk=e_approval_configuration['id'],
						category = e_approval_configuration['category'],
						level = e_approval_configuration['level'],
						level_no = e_approval_configuration['level_no']
						).update(user_id=e_approval_configuration['user_id'])
					   
						#print('p1',p1)
				return validated_data
		
		except Exception as e:
			raise APIException({"msg": e, "request_status": 0})
			
		return instance
		
		


class SiteBillsInvoicesAddSerializer(serializers.ModelSerializer):
	created_by = serializers.CharField(default=serializers.CurrentUserDefault())
	remarks = serializers.CharField(required=False,allow_null=True,allow_blank=True)
	
	class Meta:
		model = PmsSiteBillsInvoices
		fields = ('id','project','document','document_name','created_by','category','remarks',)

	def send_mail_notification(self,approval,user):
		app_module = 'pms'
		#print('approval',approval)

		app_conf = PmsSiteBillsInvoicesApprovalConfiguration.objects.get(
				level_no=1,
				is_deleted=False,
				category=approval.category
				)
		#print('approval_flag',approval_flag)
		
		#print('app_conf',app_conf)
		approved_by = app_conf.user.get_full_name()
		#print('approved_by',approved_by)
		code = 'PMS-SBI-CN'
		users = [app_conf.user]
		user_email = app_conf.user.cu_user.cu_alt_email_id
		recipient_name = app_conf.user.get_full_name()
		title = 'A new application has been submitted.Please check the details and take necessary action.'
		body ='Employee Name: {} \nFile Code:{} \nCategory Name:{}'.format(approval.created_by.get_full_name(),approval.file_code,approval.category.name)
		data = {
		"app_module":app_module,
		"type":"bills-invoices/",
		"sub_type":'approvals/'+approval.category.name+"/"+str(approval.category.id),
		"id":approval.id
		}

		data_str = json.dumps(data)
		#print('data_str',data_str)
		notification_id = store_sent_notification(users=users,body=body,title=title,data=data_str,app_module_name=app_module)
		send_notification(users=users,body=body,title=title,data=data,notification_id=notification_id,url=app_module)

		# Mail
		request = self.context.get('request')
		document = getHostWithPort(request,True)+str(approval.document) if approval.document else ''
		#print('document',document)
		if user_email:
			mail_data = {
			"recipient_name":recipient_name,
			"project_name":approval.project.name,
			"file_code": approval.file_code if approval.file_code else '',
			"category_name": approval.category.name if approval.category.name else '',
			"document_name":approval.document_name if approval.document_name else '',
			"document":document
			}
			
			
			send_mail(code,user_email,mail_data)


	def insertApprovalData(self,category,invoice):
		approvalConfiguration = PmsSiteBillsInvoicesApprovalConfiguration.objects.filter(is_deleted=False,category=category)
		#print('_dailyexpenceApprovalConfiguration',_dailyexpenceApprovalConfiguration)
		if approvalConfiguration:
			for e_approvalConfiguration in approvalConfiguration:
				PmsSiteBillsInvoicesApproval.objects.get_or_create(
					approval_user_level_id = e_approvalConfiguration.id,
					site_bills_invoices_id = invoice.id,
					created_by = e_approvalConfiguration.user
					)
			

	def create(self, validated_data):
		try:
			with transaction.atomic():
				#print('validated_data',validated_data)
				remarks = validated_data.pop('remarks')
				#file_code = self.file_code_generate()
				#print('file_code',file_code)
				#validated_data['file_code'] = file_code
				created = PmsSiteBillsInvoices.objects.create(**validated_data)
				self.insertApprovalData(validated_data.get('category'),created)
				self.send_mail_notification(created,created.created_by)
				print('remarks',remarks, type(remarks))
				if remarks!='null':
					PmsSiteBillsInvoicesRemarks.objects.create(remarks=remarks,created_by=created.created_by,site_bills_invoices=created,on_create=True)
				
				return created

		except Exception as e:
			raise APIException({"msg": e, "request_status": 0})

class SiteBillsInvoicesListSerializer(serializers.ModelSerializer):
	remarks_details = serializers.SerializerMethodField(required=False)
	approval_configuration = serializers.SerializerMethodField()
	
	def get_remarks_details(self,PmsSiteBillsInvoices):
		remarks_list = list()
		remarks_details = PmsSiteBillsInvoicesRemarks.objects.filter(site_bills_invoices_id=PmsSiteBillsInvoices.id)
		if remarks_details:
			for e_remarks_details in remarks_details:
				remarks_list.append({
				'id':e_remarks_details.id,
				'remarks':e_remarks_details.remarks,
				'created_by':e_remarks_details.created_by.id,
				'created_at':e_remarks_details.created_at,
				'created_by_name': e_remarks_details.created_by.get_full_name()
				})
		return remarks_list

	def get_approval_configuration(self,PmsSiteBillsInvoices):
		approval_con = PmsSiteBillsInvoicesApprovalConfiguration.objects.filter(
		is_deleted=False,category = PmsSiteBillsInvoices.category
		)
		#print('approval_con',approval_con)
		approval_list = list()
		for each_approval in approval_con:
			status = None
			updated_at = None
			approver_name =each_approval.user.get_full_name()
			invoicesApproval = PmsSiteBillsInvoicesApproval.objects.filter(
				site_bills_invoices_id=PmsSiteBillsInvoices.id,
				approval_user_level=each_approval,
				is_deleted=False
				)
			print('invoicesApproval',invoicesApproval)
			if invoicesApproval:
				invoicesApproval = invoicesApproval[0]
				status = invoicesApproval.approval_status
				updated_at = invoicesApproval.updated_at
				if invoicesApproval.updated_by:
					approver_name = invoicesApproval.updated_by.get_full_name() 
				else:
					approver_name = invoicesApproval.created_by.get_full_name()


			result = {
			"id":each_approval.id,
			"category":each_approval.category.id,
			"level":each_approval.level,
			"level_no":each_approval.level_no,
			"user":each_approval.user_id,
			"approver_name":approver_name,
			"updated_at":updated_at,
			"status": status
			}
			approval_list.append(result)

		return approval_list
	
	class Meta:
		model = PmsSiteBillsInvoices
		fields = '__all__'
		depth = 1
		extra_fields = ('remarks_details','approval_configuration',)
	
class SiteBillsInvoicesEditSerializer(serializers.ModelSerializer):
	updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
	is_deleted = serializers.CharField(required=False)
	remarks = serializers.CharField(required=False)
	remarks_details = serializers.SerializerMethodField(required=False)
	document = serializers.FileField(required=False)
	project_name = serializers.SerializerMethodField(required=False)
	category_name = serializers.SerializerMethodField(required=False)

	def get_remarks_details(slef,PmsSiteBillsInvoices):
		remarks_list = list()
		remarks_details = PmsSiteBillsInvoicesRemarks.objects.filter(site_bills_invoices_id=PmsSiteBillsInvoices.id)
		if remarks_details:
			for e_remarks_details in remarks_details:
				remarks_list.append( {
				'id':e_remarks_details.id,
				'remarks':e_remarks_details.remarks,
				'created_by':e_remarks_details.created_by.id,
				'created_by_name': e_remarks_details.created_by.get_full_name()
				})
		return remarks_list

	def get_project_name(self,PmsSiteBillsInvoices):
		return PmsSiteBillsInvoices.project.name

	def get_category_name(self,PmsSiteBillsInvoices):
		return PmsSiteBillsInvoices.category.name

	class Meta:
		model = PmsSiteBillsInvoices
		fields = ('id','project','document','document_name','updated_by','category','is_deleted','remarks',
			'remarks_details','project_name','category_name')
		#depth = 1

	def update(self, instance, validated_data):
		try:
			#with transaction.atomic():

			instance.project = validated_data.get('project')
			if 'document' in validated_data:
				instance.document = validated_data.get('document')
			instance.document_name = validated_data.get('document_name')
			instance.updated_by = validated_data.get('updated_by')
			instance.category = validated_data.get('category')
			
			if 'is_deleted' in validated_data:
				instance.is_deleted = validated_data.get('is_deleted')
			instance.save()

			if 'remarks' in validated_data:
				remarks = validated_data.get('remarks')
				pmsSiteBillsInvoicesRemarks = PmsSiteBillsInvoicesRemarks.objects.filter(created_by=instance.created_by,site_bills_invoices=instance)
				if pmsSiteBillsInvoicesRemarks:
					pmsSiteBillsInvoicesRemarks.update(remarks=remarks)
				else:
					PmsSiteBillsInvoicesRemarks.objects.create(remarks=remarks,created_by=instance.created_by,site_bills_invoices=instance,on_create=True)
			
			return instance

		except Exception as e:
			raise APIException({"msg": e, "request_status": 0}) 

class SiteBillsInvoicesDeleteSerializer(serializers.ModelSerializer):
	updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
	
	class Meta:
		model = PmsSiteBillsInvoices
		fields = ('id','is_deleted','updated_by',)
		#depth = 1

	def update(self, instance, validated_data):
		try:
			with transaction.atomic():
				instance.is_deleted = validated_data.get('is_deleted')
				instance.updated_by = validated_data.get('updated_by')
				instance.save()
				return instance

		except Exception as e:
			raise APIException({"msg": e, "request_status": 0}) 

class SiteBillsInvoicesApprovalSerializer(serializers.ModelSerializer):
	updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
	remarks = serializers.CharField(required=False,allow_blank=True)
	approval_list = serializers.ListField(required=False)
	approval_user_level = serializers.CharField(required=False)
	
	class Meta:
		model = PmsSiteBillsInvoices
		fields = ('id','approval_list','remarks','status','updated_by','category','approval_user_level')

	
	def send_mail_notification(self,approval,status,user,approval_flag):
		app_module = 'pms'
		mail_data = dict()
		#print('approval',approval)

		app_conf = PmsSiteBillsInvoicesApprovalConfiguration.objects.get(
				level_no=approval.current_approval_level_no,
				is_deleted=False,
				category=approval.category
				)
		#print('approval_flag',approval_flag)
		if approval_flag:
			print('app_conf',app_conf)
			approved_by = app_conf.user.get_full_name()
			print('approved_by',approved_by)
			code = 'PMS-SBI-APR'
			users = [app_conf.user]
			user_email = app_conf.user.cu_user.cu_alt_email_id
			recipient_name = app_conf.user.get_full_name()
			title = 'A new application has been '+status+' by '+approval.created_by.get_full_name()+'.Please check the details and take necessary action.'
			body ='Employee Name: {} \nFile Code:{} \nCategory Name:{}'.format(approval.created_by.get_full_name(),approval.file_code,approval.category.name)
			data = {
			"app_module":app_module,
			"type":"bills-invoices/",
			"sub_type":'approvals/'+approval.category.name+"/"+str(approval.category.id),
			"id":approval.id
			}

		else:
			approved_by = approval.updated_by.get_full_name()
			#print('approved_by',approved_by)
			# For send to User
			code = 'PMS-SBI-AN'
			users = [user]
			user_email = user.cu_user.cu_alt_email_id
			recipient_name = user.get_full_name()
			#print('recipient_name',recipient_name)
			remarks = ''
			remark_details = PmsSiteBillsInvoicesRemarks.objects.filter(site_bills_invoices_id=approval.id,created_by=approval.updated_by)
			#print('remark_details',remark_details.query,remark_details)
			if remark_details:
				remark_details = remark_details[0]
				remarks = remark_details.remarks
			#print('approval11111111111111111',approval.approved_by.get_full_name())
			title = 'Your bills approval status has been '+status+'.Please check the details.'
			body ='Approvar Name: {} \nUpdated At:{} \nRemarks'.format(approval.updated_by.get_full_name(),approval.updated_at,remarks)
			#print('body',body)
			data = {
			"app_module":app_module,
			"type":"bills-invoices/",
			"sub_type":'upload-bills/'+approval.category.name+"/"+str(approval.category.id),
			"id":approval.id
			}
			if status == 'Rejected':
				code = 'PMS-SBI-AN-RE'
				mail_data["remarks"] = remarks
			


		data_str = json.dumps(data)
		#print('data_str',data_str)
		notification_id = store_sent_notification(users=users,body=body,title=title,data=data_str,app_module_name=app_module)
		send_notification(users=users,body=body,title=title,data=data,notification_id=notification_id,url=app_module)

		# Mail
		request = self.context.get('request')
		document = getHostWithPort(request,True)+str(approval.document) if approval.document else ''
		
		if user_email:
			mail_data["recipient_name"] = recipient_name
			mail_data["project_name"] = approval.project.name
			mail_data["file_code"] = approval.file_code if approval.file_code else ''
			mail_data["category_name"] = approval.category.name if approval.category.name else ''
			mail_data["document_name"] = approval.document_name if approval.document_name else ''
			mail_data["status"] = status
			mail_data["approved_by"] = approved_by
			mail_data["document"] = document
			
			
			
			send_mail(code,user_email,mail_data)

	def addRemark(self,approval,remarks):
		pmsSiteBillsInvoicesRemarks = PmsSiteBillsInvoicesRemarks.objects.filter(
			created_by=approval.updated_by,
			site_bills_invoices=approval,
			on_create=False
			)
		#print('pmsSiteBillsInvoicesRemarks',pmsSiteBillsInvoicesRemarks)
		if pmsSiteBillsInvoicesRemarks:
			pmsSiteBillsInvoicesRemarks.update(remarks=remarks)
		else:
			PmsSiteBillsInvoicesRemarks.objects.create(remarks=remarks,created_by=approval.updated_by,site_bills_invoices=approval)

	def getFinalApprovalLevelId(self,category):
		approvalConfiguration = PmsSiteBillsInvoicesApprovalConfiguration.objects.filter(is_deleted=False,category=category).order_by('-level')
		if approvalConfiguration:
			return  approvalConfiguration.values_list('id',flat=True)[0]
		return None 
	
	def create(self, validated_data):
		try:
			with transaction.atomic():
				#print('validated_data',validated_data)
				approval_list = validated_data.get('approval_list')
				remarks = validated_data.get('remarks')
				status = ''
				approved_status_name = validated_data.get('status')+'ed'
				approved_status = ''
				current_level_of_approval = None

				if validated_data.get('status') == 'Approve':
					#approved_status_name = 'Approved'
					higest_approval_level_id = self.getFinalApprovalLevelId(validated_data.get('category'))
					#print('higest_approval_level_id',higest_approval_level_id)
					for e_approval in approval_list:
						site_invoice_approval = PmsSiteBillsInvoicesApproval.objects.get(
							site_bills_invoices_id=str(e_approval),
							approval_user_level_id=validated_data.get('approval_user_level')
							)
						#print('site_invoice_approval',site_invoice_approval)
						siteBillsInvoices = PmsSiteBillsInvoices.objects.get(pk=str(e_approval),is_deleted=False)
						#print('safasffd',str(higest_approval_level_id),type(str(higest_approval_level_id)),str(validated_data.get('approval_user_level')),type(str(validated_data.get('approval_user_level'))))
						if str(higest_approval_level_id) == str(validated_data.get('approval_user_level')):
							siteBillsInvoices.status = 'Approve'
							siteBillsInvoices.updated_by = validated_data.get('updated_by')
							siteBillsInvoices.approved_conf_id = validated_data.get('approval_user_level')
							self.send_mail_notification(siteBillsInvoices,'Approved',siteBillsInvoices.created_by,False)
						else:
							_approval_user_level_details = PmsSiteBillsInvoicesApprovalConfiguration.objects.get(
								id=str(validated_data.get('approval_user_level')),
								category=validated_data.get('category'),
								is_deleted=False
								)
							#print('_approval_user_level_details',_approval_user_level_details)
							_current_approval_level_view_list = _approval_user_level_details.level.split('L')
							#print('_current_approval_level_view_list',_current_approval_level_view_list)
							_current_approval_level_view = int(_current_approval_level_view_list[1]) + 1
							siteBillsInvoices.current_approval_level_view = 'L'+str(_current_approval_level_view)
							siteBillsInvoices.current_approval_level_no = _current_approval_level_view
							self.send_mail_notification(siteBillsInvoices,'Approved',siteBillsInvoices.created_by,True)

						siteBillsInvoices.updated_at = datetime.datetime.now()
						siteBillsInvoices.updated_by = validated_data.get('updated_by')
						siteBillsInvoices.save()

						site_invoice_approval.approval_status = validated_data.get('status')
						site_invoice_approval.updated_by = validated_data.get('updated_by')
						site_invoice_approval.updated_at = datetime.datetime.now()
						site_invoice_approval.save()

						# Remarks
						self.addRemark(siteBillsInvoices,remarks)

				if validated_data.get('status') == 'Reject':
					
					for e_approval in approval_list:
						site_invoice_approval = PmsSiteBillsInvoicesApproval.objects.get(
							site_bills_invoices_id=str(e_approval),
							approval_user_level_id=validated_data.get('approval_user_level')
							)
						siteBillsInvoices = PmsSiteBillsInvoices.objects.get(pk=str(e_approval),is_deleted=False)
						siteBillsInvoices.status = 'Reject'
						siteBillsInvoices.updated_by = validated_data.get('updated_by')
						siteBillsInvoices.updated_at = datetime.datetime.now()
						siteBillsInvoices.approved_conf_id = validated_data.get('approval_user_level')
						siteBillsInvoices.save()

						site_invoice_approval.approval_status = validated_data.get('status')
						site_invoice_approval.updated_by = validated_data.get('updated_by')
						site_invoice_approval.updated_at = datetime.datetime.now()
						site_invoice_approval.save()
				   
						# Remarks
						self.addRemark(siteBillsInvoices,remarks)

						# Mail and Notification
						self.send_mail_notification(siteBillsInvoices,'Rejected',siteBillsInvoices.created_by,False)

				return validated_data
		except Exception as e:
			raise APIException({"msg": e, "request_status": 0})
