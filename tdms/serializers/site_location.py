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
from core.models import TCoreUnit
from rest_framework.response import Response
from tdms.custom_filter import custom_filter
import pandas as pd
import numpy as np
import xlrd
from tdms.custom_delete import *
from django.db.models import Q
import re
from tdms.serializers.tender import *

#--------------------- Tdms Site Type Project Site Management----------------#
class SiteTypeProjectSiteManagementAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = TdmsSiteTypeProjectSiteManagement
        fields = ('id', 'name', 'created_by', 'owned_by')
class SiteTypeProjectSiteManagementEditSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = TdmsSiteTypeProjectSiteManagement
        fields = ('id', 'name', 'updated_by')
class SiteTypeProjectSiteManagementDeleteSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = TdmsSiteTypeProjectSiteManagement
        fields = '__all__'
    def update(self, instance, validated_data):
        instance.is_deleted=True
        instance.updated_by = validated_data.get('updated_by')
        instance.save()
        return instance

#---------------------Tdms Site Project Site Management----------------------#
class ProjectSiteManagementMultipleLongLatAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = TdmsSiteProjectSiteManagementMultipleLongLat
        fields = ('id', 'project_site', 'latitude','longitude','is_deleted','created_by', 'owned_by')
    


class ProjectSiteManagementSiteAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    type_name = serializers.SerializerMethodField(required=False)
    project_site_lat_long_list = ProjectSiteManagementMultipleLongLatAddSerializer(many=True,required=False)
    
    def get_type_name(self,TdmsSiteProjectSiteManagement):
        
        p_site = TdmsSiteTypeProjectSiteManagement.objects.filter(pk=TdmsSiteProjectSiteManagement.type.id).values('name')
        for e_p_site in p_site:
            return e_p_site['name']
    class Meta:
        model = TdmsSiteProjectSiteManagement
        fields = ('id', 'name', 'address','type','type_name',
                  'description','company_name','site_latitude','site_longitude','office_latitude',
                  'office_longitude','gest_house_latitude','gest_house_longitude','gst_no', 
                  'geo_fencing_area', 'created_by', 'owned_by','project_site_lat_long_list')

    def create(self, validated_data):
        #print('validated_data',validated_data)
        project_site_lat_long_lists = validated_data.pop('project_site_lat_long_list')
        project_site_res = TdmsSiteProjectSiteManagement.objects.create(**validated_data)
        for project_site_lat_long_list in project_site_lat_long_lists:
            TdmsSiteProjectSiteManagementMultipleLongLat.objects.create(
                project_site=project_site_res, **project_site_lat_long_list)
            #print('dsddsddsdss')
        return project_site_res

class ProjectSiteManagementSiteEditSerializer(serializers.ModelSerializer):

    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    project_site_lat_long_list = ProjectSiteManagementMultipleLongLatAddSerializer(many=True,required=False)
    lat_longdetails = serializers.SerializerMethodField(required=False)
    class Meta:
        model = TdmsSiteProjectSiteManagement
        fields = ('id', 'name', 'address','type',
                  'description','company_name','site_latitude','site_longitude','office_latitude',
                  'office_longitude','gest_house_latitude','gest_house_longitude','gst_no', 
                  'geo_fencing_area', 'updated_by','project_site_lat_long_list','lat_longdetails')
    
    def get_lat_longdetails(self,TdmsSiteProjectSiteManagement):
        return TdmsSiteProjectSiteManagementMultipleLongLat.objects.filter(
            project_site=TdmsSiteProjectSiteManagement.id).values()
        
        
    def update(self, instance, validated_data):
        #print('validated_data',validated_data)
        project_site_lat_long_lists = validated_data.pop('project_site_lat_long_list')
        instance.name = validated_data.get('name', instance.name)
        instance.address = validated_data.get('address', instance.address)
        instance.type = validated_data.get('type', instance.type)
        instance.description = validated_data.get('description', instance.description)
        instance.site_latitude = validated_data.get('site_latitude', instance.site_latitude)
        instance.site_longitude = validated_data.get('site_longitude', instance.site_longitude)
        instance.office_latitude = validated_data.get('office_latitude', instance.office_latitude)
        instance.office_longitude = validated_data.get('office_longitude', instance.office_longitude)
        instance.gest_house_latitude = validated_data.get('gest_house_latitude', instance.gest_house_latitude)
        instance.gest_house_longitude = validated_data.get('gest_house_longitude', instance.gest_house_longitude)
        instance.gst_no = validated_data.get('gst_no', instance.gst_no)
        instance.geo_fencing_area = validated_data.get('geo_fencing_area', instance.geo_fencing_area)
        instance.company_name = validated_data.get('company_name', instance.company_name)
        instance.updated_by = validated_data.get('updated_by', instance.updated_by)
        instance.save()

        project_site_lat_long_e = TdmsSiteProjectSiteManagementMultipleLongLat.objects.filter(
                project_site=instance).count()
        if project_site_lat_long_e > 0:
            TdmsSiteProjectSiteManagementMultipleLongLat.objects.filter(
                project_site=instance).delete()
        for project_site_lat_long_list in project_site_lat_long_lists:
            TdmsSiteProjectSiteManagementMultipleLongLat.objects.create(
                project_site = instance,
                **project_site_lat_long_list
            )
        

        return instance    

class ProjectSiteManagementSiteDeleteSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = TdmsSiteProjectSiteManagement
        fields = '__all__'
    def update(self, instance, validated_data):
        instance.is_deleted=True
        instance.updated_by = validated_data.get('updated_by')
        instance.save()
        return instance

#:::::::::::: PROJECTS ::::::::::::::::::::::::::::#
class ProjectsAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    owned_by = serializers.CharField(default=serializers.CurrentUserDefault())
    status = serializers.BooleanField(default=True)

    class Meta:
        model = TdmsProject
        fields = ('id', 'tender', 'project_g_id', 'created_by', 'owned_by', 'status')

class ProjectsListSerializer(serializers.ModelSerializer):
    class Meta:
        model = TdmsProject
        fields = '__all__'

class ProjectsListSerializer(serializers.ModelSerializer):
    machinary_list = serializers.SerializerMethodField(required=False)
    tender_g_id = serializers.SerializerMethodField(required=False)
    site_location_name = serializers.SerializerMethodField(required=False)
    tender_bidder_type = serializers.SerializerMethodField(required=False)
    approvals = serializers.SerializerMethodField(required=False)
    def get_approvals(self,TdmsProject):
        approval_details=TdmsPreExecutionApproval.objects.filter(project=TdmsProject.id)
        # print('approval_details',approval_details)
        a_d_list=list()
        for a_d in approval_details:
            # print('a_d.pre_execution_tabs',a_d.pre_execution_tabs)
            if a_d.approved_status == 1:
                a_d_list.append(
                    {
                        'id': a_d.id,
                        'project': a_d.project.id,
                        'pre_execution_tabs': a_d.pre_execution_tabs,
                        'approved_status': a_d.approved_status,
                    }
                )
        return a_d_list

    def get_machinary_list(self, TdmsProject):
        machinary_list = TdmsProjectMachinaryMapping.objects.filter(project=TdmsProject.id)
        m_list = list()
        for e_machinary in machinary_list:
            m_list.append(
                {'id': e_machinary.id,
                 'machinary': e_machinary.machinary.id,
                 'project': e_machinary.project.id,
                 'machinary_s_d_req': e_machinary.machinary_s_d_req,
                 'machinary_e_d_req': e_machinary.machinary_e_d_req
                 }
            )
        return m_list

    def get_tender_g_id(self, TdmsProject):
        tender_d = TdmsTenders.objects.filter(pk=TdmsProject.tender.id).values('tender_g_id')
        # print('tender_d',tender_d)
        for e_tender in tender_d:
            return e_tender['tender_g_id']

    def get_site_location_name(self, TdmsProject):
        if TdmsProject.site_location is not None:
            s_loc_d = TdmsSiteProjectSiteManagement.objects.filter(pk=TdmsProject.site_location.id).values('name')
            # print('s_loc_d', s_loc_d)
            for e_s_loc in s_loc_d:
                return e_s_loc['name']

    def get_tender_bidder_type(self, TdmsProject):
        tender_b_t = TdmsTenderBidderType.objects.filter(tender=TdmsProject.tender.id).values('bidder_type')
        for e_tender_b_t in tender_b_t:
            return e_tender_b_t['bidder_type'].replace("_", " ")

    class Meta:
        model = TdmsProject
        fields = ('id', 'tender', 'tender_g_id', 'project_g_id', 'name', 'site_location',
                  'site_location_name', 'tender_bidder_type', 'start_date','state',
                  'end_date', 'machinary_list', 'created_by',
                  'updated_by', 'owned_by', 'status','approvals')
                  
class ProjectsListCountSerializer(serializers.ModelSerializer):
    class Meta:
        model = TdmsProject
        fields ='__all__'

class ProjectsEditSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    machinary_list = serializers.ListField(required=False)
    project_g_id = serializers.CharField(required=False)
    prev_machinary_list = serializers.CharField(required=False)
    employee_list = serializers.ListField(required=False)
    prev_employee_list = serializers.CharField(required=False)

    class Meta:
        model = TdmsProject
        fields = ('id', 'project_g_id', 'name', 'site_location', 'start_date',
                  'end_date', 'updated_by', 'machinary_list', "prev_machinary_list",
                  "prev_employee_list", "employee_list","project_manager","project_coordinator")

    def update(self, instance, validated_data):
        try:
            with transaction.atomic():

                #print('start_date_type',type(validated_data.get("start_date")))
                #print('start_date', validated_data.get("start_date"))
                response = dict()
                instance.name = validated_data.get("name")
                instance.site_location = validated_data.get("site_location")
                instance.start_date = validated_data.get("start_date")
                instance.end_date = validated_data.get("end_date")
                instance.project_manager = validated_data.get('project_manager')
                instance.project_coordinator = validated_data.get('project_coordinator')
                instance.save()

                ### Start Change Request 1.0 | Date : 07-08-2020 | Rupam Hazra ###
                
                daily_expence_configuration_for_pm = TdmsDailyExpenceApprovalConfiguration.objects.filter(level='Project Manager',project=instance)
                if daily_expence_configuration_for_pm:
                    daily_expence_configuration_for_pm.update(
                        user=validated_data.get('project_manager'),
                        updated_by=validated_data.get("updated_by")
                        )
                else:
                    TdmsDailyExpenceApprovalConfiguration.objects.create(
                        project=instance,
                        level='Project Manager',
                        level_no = 1,
                        user=validated_data.get('project_manager'),
                        created_by = validated_data.get("updated_by")
                    )
                daily_expence_configuration_for_pc = TdmsDailyExpenceApprovalConfiguration.objects.filter(level='Project Coordinator',project=instance,)
                if daily_expence_configuration_for_pc:
                    daily_expence_configuration_for_pc.update(
                        user=validated_data.get('project_coordinator'),
                        updated_by=validated_data.get("updated_by")
                        )
                else:
                    TdmsDailyExpenceApprovalConfiguration.objects.create(
                        project=instance,
                        level='Project Coordinator',
                        level_no = 2,
                        user=validated_data.get('project_coordinator'),
                        created_by = validated_data.get("updated_by")
                    )

                ### End Change Request 1.0 | Date : 07-08-2020 | Rupam Hazra ###


                prev_machinary_list = validated_data.get("prev_machinary_list")
                machinary_list = validated_data.get("machinary_list")
                prev_employee_list = validated_data.get("prev_employee_list")
                employee_list = validated_data.get("employee_list")
                m_list = list()
                e_list = list()
                #print('machinary_list',machinary_list)
                if prev_machinary_list == 'yes':
                    TdmsProjectMachinaryMapping.objects.filter(project=instance).delete()
                    for e_m in machinary_list:
                        machinary_s_d_req = e_m['machinary_s_d_req']
                        machinary_e_d_req = e_m['machinary_e_d_req']
                        machinary_s_d_req1 = datetime.datetime.strptime(machinary_s_d_req, "%Y-%m-%dT%H:%M:%S.%fZ")
                        machinary_e_d_req1 = datetime.datetime.strptime(machinary_e_d_req,"%Y-%m-%dT%H:%M:%S.%fZ")
                        MachinaryMapping = TdmsProjectMachinaryMapping.objects. \
                            create(
                            project=instance,
                            machinary_id=e_m['machinary'],
                            machinary_s_d_req=machinary_s_d_req1,
                            machinary_e_d_req=machinary_e_d_req1,
                            owned_by=instance.updated_by,
                            created_by=instance.updated_by
                        )
                        machinary_dict = {}
                        machinary_dict["id"] = MachinaryMapping.id
                        machinary_dict["project"] = MachinaryMapping.project.id
                        machinary_dict["machinary"] = MachinaryMapping.machinary.id
                        machinary_dict["machinary_s_d_req"] = MachinaryMapping.machinary_s_d_req
                        machinary_dict["machinary_e_d_req"] = MachinaryMapping.machinary_e_d_req
                        m_list.append(machinary_dict)
                else:
                    for e_m in machinary_list:
                        machinary_s_d_req = e_m['machinary_s_d_req']
                        machinary_e_d_req = e_m['machinary_e_d_req']
                        machinary_s_d_req1 = datetime.datetime.strptime(machinary_s_d_req, "%Y-%m-%dT%H:%M:%S.%fZ")
                        machinary_e_d_req1 = datetime.datetime.strptime(machinary_e_d_req, "%Y-%m-%dT%H:%M:%S.%fZ")
                        MachinaryMapping = TdmsProjectMachinaryMapping.objects. \
                            create(
                            project=instance,
                            machinary_id=e_m['machinary'],
                            machinary_s_d_req=machinary_s_d_req1,
                            machinary_e_d_req=machinary_e_d_req1,
                            owned_by=instance.updated_by,
                            created_by=instance.updated_by
                        )
                        # print('machinary_rental_details', machinary_rental_details)
                        machinary_dict = {}
                        machinary_dict["id"] = MachinaryMapping.id
                        machinary_dict["project"] = MachinaryMapping.project.id
                        machinary_dict["machinary"] = MachinaryMapping.machinary.id
                        machinary_dict["machinary_s_d_req"] = MachinaryMapping.machinary_s_d_req
                        machinary_dict["machinary_e_d_req"] = MachinaryMapping.machinary_e_d_req
                        m_list.append(machinary_dict)

                if prev_employee_list == 'yes':
                    TdmsProjectUserMapping.objects.filter(project=instance).delete()
                    for e_l in employee_list:
                        start_date = e_l['start_date']
                        expire_date = e_l['expire_date']
                        start_date = datetime.datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%S.%fZ")
                        expire_date = datetime.datetime.strptime(expire_date, "%Y-%m-%dT%H:%M:%S.%fZ")
                        UserMapping = TdmsProjectUserMapping.objects. \
                            create(
                            project=instance,
                            user_id=e_l['user'],
                            start_date=start_date,
                            expire_date=expire_date,
                            owned_by=instance.updated_by,
                            created_by=instance.updated_by
                        )
                        employee_dict = {}
                        employee_dict["id"] = UserMapping.id
                        employee_dict["project"] = UserMapping.project.id
                        employee_dict["user"] = UserMapping.user.id
                        employee_dict["start_date"] = UserMapping.start_date
                        employee_dict["expire_date"] = UserMapping.expire_date
                        e_list.append(employee_dict)
                else:
                    for e_l in employee_list:
                        start_date = e_l['start_date']
                        expire_date = e_l['expire_date']
                        start_date = datetime.datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%S.%fZ")
                        expire_date = datetime.datetime.strptime(expire_date, "%Y-%m-%dT%H:%M:%S.%fZ")
                        UserMapping = TdmsProjectUserMapping.objects. \
                            create(
                            project=instance,
                            user_id=e_l['user'],
                            start_date=start_date,
                            expire_date=expire_date,
                            owned_by=instance.updated_by,
                            created_by=instance.updated_by
                        )
                        # print('machinary_rental_details', machinary_rental_details)
                        employee_dict = {}
                        employee_dict["id"] = UserMapping.id
                        employee_dict["project"] = UserMapping.project.id
                        employee_dict["user"] = UserMapping.user.id
                        employee_dict["start_date"] = UserMapping.start_date
                        employee_dict["expire_date"] = UserMapping.expire_date
                        e_list.append(employee_dict)
                response["id"] = instance.id
                response['project_g_id'] = instance.project_g_id
                response['name'] = instance.name
                response['site_location'] = instance.site_location
                response['start_date'] = instance.start_date
                response['end_date'] = instance.end_date
                response["machinary_list"] = m_list
                response["employee_list"] = e_list
                response["project_manager"] = instance.project_manager
                response["project_coordinator"] = instance.project_coordinator
                return response

        except Exception as e:
            raise APIException({"msg": e, "request_status": 0})

class ProjectsDeleteSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = TdmsProject
        fields = '__all__'

    def update(self, instance, validated_data):
        instance.status = False
        instance.is_deleted = True
        instance.updated_by = validated_data.get('updated_by')
        instance.save()
        m_m_list = TdmsProjectMachinaryMapping.objects.filter(project=instance)
        # print('m_m_list',m_m_list)
        for e_m in m_m_list:
            e_m.is_deleted = True
            e_m.updated_by = validated_data.get('updated_by')
            e_m.save()
        return instance
class ProjectDetailsSerializer(serializers.ModelSerializer):
    site_location = ProjectSiteManagementSiteAddSerializer()
    class Meta:
        model = TdmsProject
        fields = ('id', 'name', 'tender', 'site_location', 'start_date', 'end_date', 'status')

class ProjectsDetailsByProjectSiteIdSerializer(serializers.ModelSerializer):
    site_location_details=serializers.SerializerMethodField(required=False)
    def get_site_location_details(self,TdmsProject):
        site_details=TdmsSiteProjectSiteManagement.objects.filter(id=TdmsProject.site_location.id)
        long_lat_data=TdmsSiteProjectSiteManagementMultipleLongLat.objects.filter(project_site=TdmsProject.site_location.id).values('latitude','longitude')
        print('site_details',site_details)
        for site in site_details:
            location_details={
                'id':site.id,
                'name':site.name,
                'address':site.address,
                # 'latitude':site.latitude,
                # 'longitude':site.longitude,
                'lat_lon_details':long_lat_data,
                'type':site.type.id,
                'description':site.description,
                'company_name':site.company_name,
                'gst_no':site.gst_no,
                'geo_fencing_area':site.geo_fencing_area,
            }
        return location_details
    class Meta:
        model = TdmsProject
        fields ='__all__'
        extra_fields=('site_location_details')

class ProjectsListWithLatLongSerializer(serializers.ModelSerializer):
    site_location_details=serializers.SerializerMethodField(required=False)
    class Meta:
        model = TdmsProject
        fields ='__all__'
    def get_site_location_details(self,TdmsProject):
        if TdmsProject.site_location: 
            site_details=TdmsSiteProjectSiteManagement.objects.filter(id=TdmsProject.site_location.id,is_deleted=False)
            print('site_details',site_details)
            if site_details:           
                for site in site_details:
                    site_location={
                        'site_latitude':site.site_latitude,
                        'site_longitude':site.site_longitude
                    }
            else:
                site_location=None
            
            return site_location

class ProjectsManpowerReassignTransferSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    project_list = serializers.ListField(required=False)
    

    class Meta:
        model = TdmsProjectUserMapping
        fields = ('id', 'created_by', "project_list","user")

    def create(self, validated_data):
        try:
            with transaction.atomic():
                response = dict()
                project_list = validated_data.get("project_list")
                p_list = list()
                TdmsProjectUserMapping.objects.filter(user=validated_data.get("user")).delete()
                for p_l in project_list:
                    start_date = p_l['start_date']
                    expire_date = p_l['expire_date']
                    start_date = datetime.datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%S.%fZ")
                    expire_date = datetime.datetime.strptime(expire_date, "%Y-%m-%dT%H:%M:%S.%fZ")
                    UserMapping = TdmsProjectUserMapping.objects. \
                        create(
                        project_id=p_l["project"],
                        user=validated_data.get("user"),
                        start_date=start_date,
                        expire_date=expire_date,
                        owned_by=validated_data.get("created_by"),
                        created_by=validated_data.get("created_by")
                    )
                    project_dict = {}
                    project_dict["id"] = UserMapping.id
                    project_dict["project"] = UserMapping.project.id
                    project_dict["user"] = UserMapping.user.id
                    project_dict["start_date"] = UserMapping.start_date
                    project_dict["expire_date"] = UserMapping.expire_date
                    p_list.append(project_dict)
                
                response["user"] = validated_data.get("user")
                response["project_list"] = p_list
                return response

        except Exception as e:
            raise APIException({"msg": e, "request_status": 0})
