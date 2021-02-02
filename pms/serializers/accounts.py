from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from pms.models.module_accounts import *
from django.contrib.auth.models import *
import time
from django.db import transaction, IntegrityError
import os
from rest_framework.exceptions import APIException
import datetime
from rest_framework.response import Response
from django.db.models import Q
from pms.models.module_daily_expence import PmsDailyExpenceApprovalConfiguration
# from pms.models.module_site_bills_invoices import PmsSiteBillsInvoicesApprovalConfiguration

class PmsAccountUserAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    name = serializers.SerializerMethodField(required=False)
    
    def get_name(self,PmsAccounts):
        return PmsAccounts.user.get_full_name()

    class Meta:
        model = PmsAccounts
        fields = '__all__'
        extra_fields = ('name')

    def create(self,validated_data):
        try:
            with transaction.atomic():
                PmsAccounts.objects.create(**validated_data)
                # daily_expence_configuration = PmsDailyExpenceApprovalConfiguration.objects.filter(level='Account',user=validated_data.get('user'))
                # if daily_expence_configuration:
                #     daily_expence_configuration.update(
                #         is_deleted=True,updated_by=validated_data.get("created_by"))
                
                PmsDailyExpenceApprovalConfiguration.objects.create(
                    level='Account',
                    level_no = 4,
                    user=validated_data.get('user'),
                    created_by = validated_data.get("created_by")
                )
                return validated_data

        except Exception as e:
            raise APIException({"msg": e, "request_status": 0})

class PmsAccountUserEditSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    name = serializers.SerializerMethodField(required=False)

    def get_name(self,PmsAccounts):
        return PmsAccounts.user.get_full_name()

    class Meta:
        model = PmsAccounts
        fields = '__all__'
        extra_fields = ('name')

    def update(self, instance, validated_data):
        try:
            with transaction.atomic():
                instance.is_deleted=True
                instance.updated_by = validated_data.get('updated_by')
                instance.save()
                validated_data.pop('updated_by')
                created = PmsAccounts.objects.create(**validated_data)

                PmsAccounts.objects.create(**validated_data)

                daily_expence_configuration = PmsDailyExpenceApprovalConfiguration.objects.filter(level='Account')
                if daily_expence_configuration:
                    daily_expence_configuration.update(
                        user = validated_data.get('user'),
                        updated_by=validated_data.get("created_by"))
                
                # PmsDailyExpenceApprovalConfiguration.objects.create(
                #     level='Account',
                #     user=validated_data.get('user'),
                #     created_by = validated_data.get("created_by")
                # )
                #print('created',created)
                return created

        except Exception as e:
            raise APIException({"msg": e, "request_status": 0})

class PmsHoUserAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    #name = serializers.SerializerMethodField(required=False)
    
    # def get_name(self,PmsHoUser):
    #     return PmsHoUser.user.get_full_name()

    class Meta:
        model = PmsHoUser
        fields = '__all__'
        #extra_fields = ('name')

    def create(self,validated_data):
        try:
            with transaction.atomic():
                PmsHoUser.objects.create(**validated_data)
                # daily_expence_configuration = PmsDailyExpenceApprovalConfiguration.objects.filter(level='HO')
                # if daily_expence_configuration:
                #     daily_expence_configuration.update(
                #         is_deleted=True,updated_by=validated_data.get("created_by"))
                
                PmsDailyExpenceApprovalConfiguration.objects.create(
                    level='HO',
                    level_no = 3,
                    user=validated_data.get('user'),
                    created_by = validated_data.get("created_by")
                )
                return validated_data

        except Exception as e:
            raise APIException({"msg": e, "request_status": 0})

class PmsHoUserEditSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    name = serializers.SerializerMethodField(required=False)

    def get_name(self,PmsHoUser):
        return PmsHoUser.user.get_full_name()

    class Meta:
        model = PmsHoUser
        fields = '__all__'
        extra_fields = ('name')

    def update(self, instance, validated_data):
        try:
            with transaction.atomic():
                instance.is_deleted=True
                instance.updated_by = validated_data.get('updated_by')
                instance.save()
                validated_data.pop('updated_by')
                created = PmsHoUser.objects.create(**validated_data)

                daily_expence_configuration = PmsDailyExpenceApprovalConfiguration.objects.filter(level='HO')
                if daily_expence_configuration:
                    daily_expence_configuration.update(
                        user = validated_data.get('user'),
                        updated_by=validated_data.get("created_by")
                        )
                return created

        except Exception as e:
            raise APIException({"msg": e, "request_status": 0})

class PmsTourAccountUserAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    # user = serializers.IntegerField(required=False)
    name = serializers.SerializerMethodField(required=False)

    def get_name(self, obj):
        if obj.user:
            return obj.user.get_full_name()
        else:
            return None

    class Meta:
        model = PmsTourAccounts
        fields = ('__all__')
        extra_fields = ('name')

    # def create(self, validated_data):
    #     try:
    #         with transaction.atomic():
    #             print(validated_data)
    #             PmsTourAccounts.objects.create(**validated_data)
    #             # daily_expence_configuration = PmsDailyExpenceApprovalConfiguration.objects.filter(level='Account',user=validated_data.get('user'))
    #             # if daily_expence_configuration:
    #             #     daily_expence_configuration.update(
    #             #         is_deleted=True,updated_by=validated_data.get("created_by"))
    #
    #             # PmsDailyExpenceApprovalConfiguration.objects.create(
    #             #     level='Account',
    #             #     level_no=4,
    #             #     user=validated_data.get('user'),
    #             #     created_by=validated_data.get("created_by")
    #             # )
    #             return validated_data
    #
    #     except Exception as e:
    #         raise APIException({"msg": e, "request_status": 0})

class PmsTourAccountUserEditSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    name = serializers.SerializerMethodField(required=False)

    def get_name(self, obj):
        if obj.user:
            return obj.user.get_full_name()
        else:
            return None

    class Meta:
        model = PmsTourAccounts
        fields = '__all__'
        extra_fields = ('name')

    def update(self, instance, validated_data):
        try:
            with transaction.atomic():
                print(instance)
                instance.is_deleted = True
                instance.updated_by = validated_data.get('updated_by')
                instance.save()
                validated_data.pop('updated_by')
                created = PmsTourAccounts.objects.create(**validated_data)

                # PmsAccounts.objects.create(**validated_data)
                #
                # daily_expence_configuration = PmsDailyExpenceApprovalConfiguration.objects.filter(level='Account')
                # if daily_expence_configuration:
                #     daily_expence_configuration.update(
                #         user=validated_data.get('user'),
                #         updated_by=validated_data.get("created_by"))

                # PmsDailyExpenceApprovalConfiguration.objects.create(
                #     level='Account',
                #     user=validated_data.get('user'),
                #     created_by = validated_data.get("created_by")
                # )
                # print('created',created)
                return created

        except Exception as e:
            raise APIException({"msg": e, "request_status": 0})

class PmsTourHoUserAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())

    # name = serializers.SerializerMethodField(required=False)

    # def get_name(self,PmsHoUser):
    #     return PmsHoUser.user.get_full_name()

    class Meta:
        model = PmsTourHoUser
        fields = '__all__'
        # extra_fields = ('name')

    def create(self, validated_data):
        try:
            with transaction.atomic():
                PmsTourHoUser.objects.create(**validated_data)
                # daily_expence_configuration = PmsDailyExpenceApprovalConfiguration.objects.filter(level='HO')
                # if daily_expence_configuration:
                #     daily_expence_configuration.update(
                #         is_deleted=True,updated_by=validated_data.get("created_by"))

                # PmsDailyExpenceApprovalConfiguration.objects.create(
                #     level='HO',
                #     level_no=3,
                #     user=validated_data.get('user'),
                #     created_by=validated_data.get("created_by")
                # )
                return validated_data

        except Exception as e:
            raise APIException({"msg": e, "request_status": 0})

class PmsTourHoUserEditSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    name = serializers.SerializerMethodField(required=False)

    def get_name(self, obj):
        return obj.user.get_full_name()

    class Meta:
        model = PmsTourHoUser
        fields = '__all__'
        extra_fields = ('name')

    def update(self, instance, validated_data):
        try:
            with transaction.atomic():
                instance.is_deleted = True
                instance.updated_by = validated_data.get('updated_by')
                instance.save()
                validated_data.pop('updated_by')
                created = PmsTourHoUser.objects.create(**validated_data)

                # daily_expence_configuration = PmsDailyExpenceApprovalConfiguration.objects.filter(level='HO')
                # if daily_expence_configuration:
                #     daily_expence_configuration.update(
                #         user=validated_data.get('user'),
                #         updated_by=validated_data.get("created_by")
                #     )

                # PmsDailyExpenceApprovalConfiguration.objects.create(
                #     level='HO',
                #     user=validated_data.get('user'),
                #     created_by = validated_data.get("created_by")
                # )

                # print('created',created)
                return created

        except Exception as e:
            raise APIException({"msg": e, "request_status": 0})

# class PmsSiteBillsInvoicesHoUserAddSerializer(serializers.ModelSerializer):
#     created_by = serializers.CharField(default=serializers.CurrentUserDefault())
#     #name = serializers.SerializerMethodField(required=False)
    
#     # def get_name(self,PmsHoUser):
#     #     return PmsHoUser.user.get_full_name()

#     class Meta:
#         model = PmsSiteBillsInvoicesHoUser
#         fields = '__all__'
#         #extra_fields = ('name')

#     def create(self,validated_data):
#         try:
#             with transaction.atomic():
#                 PmsSiteBillsInvoicesHoUser.objects.create(**validated_data)
#                 # daily_expence_configuration = PmsDailyExpenceApprovalConfiguration.objects.filter(level='HO')
#                 # if daily_expence_configuration:
#                 #     daily_expence_configuration.update(
#                 #         is_deleted=True,updated_by=validated_data.get("created_by"))
                
#                 PmsSiteBillsInvoicesApprovalConfiguration.objects.create(
#                     level='HO',
#                     level_no = 1,
#                     user=validated_data.get('user'),
#                     created_by = validated_data.get("created_by")
#                 )
#                 return validated_data

#         except Exception as e:
#             raise APIException({"msg": e, "request_status": 0})

# class PmsSiteBillsInvoicesHoUserEditSerializer(serializers.ModelSerializer):
#     created_by = serializers.CharField(default=serializers.CurrentUserDefault())
#     updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
#     name = serializers.SerializerMethodField(required=False)

#     def get_name(self,PmsSiteBillsInvoicesHoUser):
#         return PmsSiteBillsInvoicesHoUser.user.get_full_name()

#     class Meta:
#         model = PmsHoUser
#         fields = '__all__'
#         extra_fields = ('name')

#     def update(self, instance, validated_data):
#         try:
#             with transaction.atomic():
#                 instance.is_deleted=True
#                 instance.updated_by = validated_data.get('updated_by')
#                 instance.save()
#                 validated_data.pop('updated_by')
#                 created = PmsSiteBillsInvoicesHoUser.objects.create(**validated_data)

#                 site_bills_configuration = PmsSiteBillsInvoicesApprovalConfiguration.objects.filter(level='HO')
#                 if site_bills_configuration:
#                     site_bills_configuration.update(
#                         user = validated_data.get('user'),
#                         updated_by=validated_data.get("created_by")
#                         )
#                 return created

#         except Exception as e:
#             raise APIException({"msg": e, "request_status": 0})
