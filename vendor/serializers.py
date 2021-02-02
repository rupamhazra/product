from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from vendor.models import *
from django.contrib.auth.models import *
from rest_framework.exceptions import APIException
from django.conf import settings
# from rest_framework.validators import *
from drf_extra_fields.fields import Base64ImageField # for image base 64
from django.db import transaction, IntegrityError
from master.models import TMasterModuleOther,TMasterOtherRole,TMasterOtherUser,TMasterModuleRoleUser
from users.models import *



class VendorAddSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = VendorDetails

        fields = ("id","created_by", "creation_id", "vendor_code", "title", "name1", "name2", "sort1",  "sort2","pincode","country",
                  "address_1st_line", "address_2nd_line","address_3rd_line", "street", "region", "mobile_no","telephone_no",
                  "email_id", "fax_no", "is_active", "city", "updated_by", "deleted_by")


class VendorBasicDetailEditSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())

    class Meta:
        model = VendorDetails
        fields = ("id","created_by", "creation_id", "vendor_code", "title", "name1", "name2", "sort1",  "sort2","pincode","country",
                  "address_1st_line", "address_2nd_line","address_3rd_line", "street", "region", "mobile_no","telephone_no",
                  "email_id", "fax_no", "is_active", "city", "updated_by", "deleted_by")

class VendorBasicDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorDetails
        fields = ('__all__')


class VendorContactsAddSerializer(serializers.ModelSerializer):
    vendor = serializers.IntegerField(required=True)
    contacts = serializers.ListField(required=False)
    created_by = serializers.CharField(default=serializers.CurrentUserDefault())
    class Meta:
        model = VendorContactDetails
        fields = ('vendor','contacts','created_by')

    def create(self, validated_data):
        contacts = validated_data.get('contacts') if 'contacts' in validated_data else None
        if contacts:
            # work_obj = json.loads(work_assignments)
            vendor = VendorDetails.objects.filter(id=validated_data.get('vendor')) if validated_data.get('vendor') else ''
            if vendor:
                VendorContactDetails.objects.filter(vendor__id=vendor[0].id).delete()
                for each in contacts:
                    each['created_by'] = validated_data.get('created_by')
                    each['vendor_id'] = VendorDetails.objects.get(
                        id=validated_data.get('vendor')).id if validated_data.get('vendor') else ''
                    each['created_by'] = validated_data.get('created_by')
                    VendorContactDetails.objects.create(**each)
                    del each['created_by']
            del validated_data['created_by']
            return validated_data


class VendorContactListSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorContactDetails
        fields = ('id', 'vendor', 'name', 'title', 'email_id', 'telephone_no', 'mobile_no', 'fax_no')

class VendorApprovelListSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorDetails
        fields = ('id', 'creation_id', 'vendor_code', 'name1', 'approver_name')


# multiple vendor Approve created by Swarup Adhikary(14.01.2020)


class VendorApprovalStatusUpdateSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    # request_by = serializers.CharField(required=False)
    comment = serializers.CharField(required=False)
    vendor_list_approvals = serializers.ListField(required=False)
    # notification = serializers.BooleanField(required=False)

    class Meta:
        model = VendorDetails
        fields = ('updated_by', 'comment', 'vendor_list_approvals')

    def create(self, validated_data):
        try:
            with transaction.atomic():
                print('validated_data',validated_data)
                vendor_list_approvals = validated_data.get('vendor_list_approvals')
                # request_by = validated_data.get('request_by')
                updated_by = validated_data.get('updated_by')
                comment = validated_data.get('comment') if 'comment' in validated_data else ''
                for each in vendor_list_approvals:
                    instance = VendorDetails.objects.get(id=int(each))
                    instance.is_approve = True
                    instance.vendor_approval_status = "Approve"
                    instance.updated_by = updated_by
                    vendor = instance
                    if VendorApprovalStatus.objects.filter(vendor=vendor).count():
                        VendorApprovalStatus.objects.filter(vendor=vendor).update(approval_status="Approve", comment=comment, user=updated_by)
                    else:
                        VendorApprovalStatus.objects.create(vendor=vendor,approval_status="Approve", comment=comment, user=updated_by)

                return validated_data
        except Exception as e:
            raise APIException({"msg": e, "request_status": 0})


# multiple vendor reject created by Swarup Adhikary(15.01.2020)
class VendorRejectStatusUpdateSerializer(serializers.ModelSerializer):
    updated_by = serializers.CharField(default=serializers.CurrentUserDefault())
    # request_by = serializers.CharField(required=False)
    comment = serializers.CharField(required=False)
    vendor_list_approvals = serializers.ListField(required=False)
    # notification = serializers.BooleanField(required=False)

    class Meta:
        model = VendorDetails
        fields = ('updated_by', 'comment', 'vendor_list_approvals')

    def create(self, validated_data):
        try:
            with transaction.atomic():
                print('validated_data',validated_data)
                vendor_list_approvals = validated_data.get('vendor_list_approvals')
                # request_by = validated_data.get('request_by')
                updated_by = validated_data.get('updated_by')
                comment = validated_data.get('comment') if 'comment' in validated_data else ''
                # project = None
                for each in vendor_list_approvals:
                    instance = VendorDetails.objects.get(id=int(each))
                    instance.is_approve = False
                    instance.updated_by = updated_by
                    instance.vendor_approval_status = "Reject"
                    instance.is_reject = True
                    instance.save()
                    vendor = instance
                    if VendorApprovalStatus.objects.filter(vendor=vendor).count():
                        VendorApprovalStatus.objects.filter(vendor=vendor).update(approval_status="Reject", comment=comment, user=updated_by)
                    else:
                        VendorApprovalStatus.objects.create(vendor=vendor,approval_status="Reject", comment=comment, user=updated_by)

                return validated_data
        except Exception as e:
            raise APIException({"msg": e, "request_status": 0})

