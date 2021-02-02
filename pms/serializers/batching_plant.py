"""
Created by Bishal on 28-08-2020
Reviewd and updated by Shubhadeep
"""
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from django.core import serializers as core_serializers
from pms.models.module_project import *
from pms.models.module_batching_plant import *
from django.contrib.auth.models import *
import datetime
from rest_framework.response import Response
from pms.custom_filter import custom_filter
from pms.custom_delete import *
from django.db.models import Q
import re
import json


class PmsBatchingPlantBrandOfCementMasterSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = PmsBatchingPlantBrandOfCementMaster
        fields = ('__all__')

class PmsBatchingPlantPurposeMasterSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = PmsBatchingPlantPurposeMaster
        fields = ('__all__')

class PmsBatchingPlantConcreteMasterSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    brand_of_cement_ids = serializers.ListField(required=False)
    purpose_ids = serializers.ListField(required=False, allow_null=True)
    brand_of_cement_details = serializers.SerializerMethodField()
    purpose_details = serializers.SerializerMethodField()

    class Meta:
        model = PmsBatchingPlantConcreteMaster
        fields = ('id', 'concrete_name', 'is_deleted', 'created_by',
                  'updated_by', 'created_at', 'updated_at', 'purpose_ids', 'brand_of_cement_ids',
                  'brand_of_cement_details', 'purpose_details')
    
    
    def map_cement_and_purpose(self, instance, brand_of_cement_ids, purpose_ids=None):
        for brand_of_cement_id in brand_of_cement_ids:
            new_cement_mapping = PmsBatchingPlantMappingConcreteBrandOfCement()
            new_cement_mapping.concrete_master_id = instance.id
            new_cement_mapping.brand_of_cement_master_id = brand_of_cement_id
            new_cement_mapping.save()
        
        if purpose_ids:
            for purpose_id in purpose_ids:
                new_purpose_mapping = PmsBatchingPlantMappingConcretePurpose()
                new_purpose_mapping.concrete_master_id = instance.id
                new_purpose_mapping.purpose_master_id = purpose_id
                new_purpose_mapping.save()


    def update(self, instance, validated_data):
        brand_of_cement_ids = validated_data.get('brand_of_cement_ids')
        purpose_ids = validated_data.get('purpose_ids')

        PmsBatchingPlantMappingConcreteBrandOfCement.objects.filter(concrete_master=instance).delete()
        PmsBatchingPlantMappingConcretePurpose.objects.filter(concrete_master=instance).delete()

        self.map_cement_and_purpose(instance, brand_of_cement_ids, purpose_ids)

        instance.updated_by = validated_data.get('updated_by')
        instance.concrete_name = validated_data.get('concrete_name')

        instance.save()

        return instance

    def create(self, validated_data):
        brand_of_cement_ids = validated_data.get('brand_of_cement_ids')
        purpose_ids = validated_data.get('purpose_ids')
        validated_data.pop('brand_of_cement_ids')
        if 'purpose_ids' in validated_data.keys():
            validated_data.pop('purpose_ids')

        instance = PmsBatchingPlantConcreteMaster.objects.create(**validated_data)
        self.map_cement_and_purpose(instance, brand_of_cement_ids, purpose_ids)
        return instance
    
    def get_brand_of_cement_details(self, PmsBatchingPlantConcrete):
        mapped_cements = PmsBatchingPlantMappingConcreteBrandOfCement.objects.filter(concrete_master=PmsBatchingPlantConcrete)
        data = []
        for cement in mapped_cements:
            data.append({
                'id': cement.brand_of_cement_master.id,
                'brand_of_cement': cement.brand_of_cement_master.brand_of_cement
            })
        return data

    def get_purpose_details(self, PmsBatchingPlantConcrete):
        mapped_purposes = PmsBatchingPlantMappingConcretePurpose.objects.filter(concrete_master=PmsBatchingPlantConcrete)
        data = []
        for purpose in mapped_purposes:
            data.append({
                'id': purpose.purpose_master.id,
                'purpose': purpose.purpose_master.purpose
            })
        return data

class PmsBatchingPlantConcreteIngredientMasterSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    concrete_details = serializers.SerializerMethodField()
    brand_of_cement_details = serializers.SerializerMethodField()
    purpose_details = serializers.SerializerMethodField()
    project_details = serializers.SerializerMethodField()

    class Meta:
        model = PmsBatchingPlantConcreteIngredientMaster
        fields = ('id', 'project', 'concrete_master', 'brand_of_cement_master', 'purpose_master', 
                'cement','fly_ash', 'sand', 'agg_20mm','agg_10mm','water','admixture','slump', 
                'is_deleted', 'created_by', 'updated_by', 'created_at', 'updated_at', 'brand_of_cement_details',
                'purpose_details', 'concrete_details', 'project_details')
    
    def create(self, validated_data):
        instances = PmsBatchingPlantConcreteIngredientMaster.objects.filter(
            project=validated_data.get('project'),
            concrete_master=validated_data.get('concrete_master'),
            brand_of_cement_master=validated_data.get('brand_of_cement_master'),
            purpose_master=validated_data.get('purpose_master'))
        
        instance = None
        
        if instances:
            instances.update(**validated_data)
            instance = instances[0]
        else:
            instance = PmsBatchingPlantConcreteIngredientMaster.objects.create(**validated_data)
        
        return instance


    def get_concrete_details(self, PmsBatchingPlantConcreteIngredient):
        return {
            'id': PmsBatchingPlantConcreteIngredient.concrete_master.id,
            'concrete_name': PmsBatchingPlantConcreteIngredient.concrete_master.concrete_name
        }
    
    def get_brand_of_cement_details(self, PmsBatchingPlantConcreteIngredient):
        return {
            'id': PmsBatchingPlantConcreteIngredient.brand_of_cement_master.id,
            'brand_of_cement': PmsBatchingPlantConcreteIngredient.brand_of_cement_master.brand_of_cement
        }
    
    def get_purpose_details(self, PmsBatchingPlantConcreteIngredient):
        if PmsBatchingPlantConcreteIngredient.purpose_master:
            return {
                'id': PmsBatchingPlantConcreteIngredient.purpose_master.id,
                'purpose': PmsBatchingPlantConcreteIngredient.purpose_master.purpose
            }
        else:
            return None
    
    def get_project_details(self, PmsBatchingPlantConcreteIngredient):
        if PmsBatchingPlantConcreteIngredient.project:
            return {
                'id': PmsBatchingPlantConcreteIngredient.project.id,
                'name': PmsBatchingPlantConcreteIngredient.project.name
            }
        else:
            return None

class PmsBatchingPlantBatchingEntryAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    concrete_details = serializers.SerializerMethodField()
    brand_of_cement_details = serializers.SerializerMethodField()
    purpose_details = serializers.SerializerMethodField()
    project_details = serializers.SerializerMethodField()
    acceptance_status_code = serializers.SerializerMethodField()
    document_status_code = serializers.SerializerMethodField()
    entry_details = serializers.SerializerMethodField()
    manual_entries = serializers.ListField(required=False)

    class Meta:
        model = PmsBatchingPlantBatchingEntry
        fields = ('__all__')
    
    def update_manual_entries(self, instance, manual_entries):
        for entry in manual_entries:
            entry['batching_entry'] = instance
            if 'id' in entry.keys():
                del entry['id']
            PmsBatchingPlantBatchingEntryDetails.objects.create(**entry)

    def create(self, validated_data):
        manual_entries = []
        if 'manual_entries' in validated_data.keys():
            manual_entries = validated_data.get('manual_entries')
            validated_data.pop('manual_entries')
            validated_data['document_status'] = 3
            validated_data['acceptance_status'] = 2
            validated_data['document_processed_at'] = datetime.datetime.now()
        instance = PmsBatchingPlantBatchingEntry.objects.create(**validated_data)
        self.update_manual_entries(instance, manual_entries)

        return instance

    def update(self, instance, validated_data):
        manual_entries = validated_data.get('manual_entries')
        validated_data.pop('manual_entries')
        PmsBatchingPlantBatchingEntryDetails.objects.filter(batching_entry=instance).delete()
        self.update_manual_entries(instance, manual_entries)
        for attr, value in validated_data.items(): 
            setattr(instance, attr, value)
        instance.save()

        return instance

    def get_concrete_details(self, PmsBatchingPlantBatchingEntry):
        if PmsBatchingPlantBatchingEntry.concrete_master:
            return {
                'id': PmsBatchingPlantBatchingEntry.concrete_master.id,
                'concrete_name': PmsBatchingPlantBatchingEntry.concrete_master.concrete_name
            }
        else:
            return None
    
    def get_brand_of_cement_details(self, PmsBatchingPlantBatchingEntry):
        if PmsBatchingPlantBatchingEntry.brand_of_cement_master:
            return {
                'id': PmsBatchingPlantBatchingEntry.brand_of_cement_master.id,
                'brand_of_cement': PmsBatchingPlantBatchingEntry.brand_of_cement_master.brand_of_cement
            }
        else:
            return None
    
    def get_purpose_details(self, PmsBatchingPlantBatchingEntry):
        if PmsBatchingPlantBatchingEntry.purpose_master:
            return {
                'id': PmsBatchingPlantBatchingEntry.purpose_master.id,
                'purpose': PmsBatchingPlantBatchingEntry.purpose_master.purpose
            }
        else:
            return None
    
    def get_project_details(self, PmsBatchingPlantBatchingEntry):
        if PmsBatchingPlantBatchingEntry.project:
            return {
                'id': PmsBatchingPlantBatchingEntry.project.id,
                'name': PmsBatchingPlantBatchingEntry.project.name
            }
        else:
            return None
    
    def get_acceptance_status_code(self, PmsBatchingPlantBatchingEntry):
        return PmsBatchingPlantBatchingEntry.get_acceptance_status_display()
    
    def get_document_status_code(self, PmsBatchingPlantBatchingEntry):
        return PmsBatchingPlantBatchingEntry.get_document_status_display()
    
    def get_entry_details(self, PmsBatchingPlantBatchingEntry):
        details_entries = PmsBatchingPlantBatchingEntryDetails.objects.filter(batching_entry=PmsBatchingPlantBatchingEntry)
        data = []
        for entry in details_entries:
            serialized_string = core_serializers.serialize('json', [entry,])
            serialized_obj = json.loads(serialized_string)[0]['fields']
            data.append(serialized_obj)
        return data

class PmsBatchingPlantBatchingEntryChangeStatusSerializer(PmsBatchingPlantBatchingEntryAddSerializer):
    status_code = serializers.CharField(required=False)

    class Meta:
        model = PmsBatchingPlantBatchingEntry
        fields = ('__all__')
    
    def update(self, instance, validated_data):
        acceptance_status_code = str(validated_data.get('status_code')).lower()
        if acceptance_status_code == 'approved':
            acceptance_status = 2
        elif acceptance_status_code == 'rejected':
            acceptance_status = 3
        else:
            acceptance_status = 1
        instance.acceptance_status = acceptance_status
        instance.save()
        return instance
        
