# from pprint import pprint
# import requests
import json

from rest_framework import serializers

# from django.db import transaction
from global_notification import send_notification, store_sent_notification
from notification.models import (NotificationMaster, UserNotificationMapping,
                                 UserTokenMapping)


class NotificationTestingSerializer(serializers.Serializer):
    device_token = serializers.CharField(max_length=500, required=True)

    def create(self, validated_data):
        user = self.context['request'].user
        device_token = validated_data.get('device_token')
        device_loken_list = [device_token]
        print(device_loken_list)
        send_notification(token_list=[device_token],
                          body='body', title='title')
        store_sent_notification(
            users=[user], body='body', title='title', app_module_name='etask')

        return validated_data


class AddDeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserTokenMapping
        fields = ('device_token', 'device_type',)

    def create(self, validated_data):
        user = self.context['request'].user
        device_token = validated_data.get('device_token')
        device_type = validated_data.get('device_type')
        device_details = self.context['request'].META.get('HTTP_USER_AGENT')
        request_token = self.context['request'].META.get(
            'HTTP_AUTHORIZATION').split(' ')[1]

        UserTokenMapping.objects.update_or_create(
            user=user, device_token=device_token, request_token=request_token,
            defaults={
                'user': user, 'device_token': device_token,
                'request_token': request_token,
                'device_details': device_details, 'device_type': device_type},
        )

        return validated_data


class ReadNotificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = NotificationMaster
        fields = ('__all__')

    def update(self, instance, validated_data):
        user = self.context['request'].user
        UserNotificationMapping.objects.filter(
            user=user, notification=instance).update(read_status=True)
        return validated_data


class NotificationMasterSerializer(serializers.ModelSerializer):
    data = serializers.SerializerMethodField()

    class Meta:
        model = NotificationMaster
        fields = ('id', 'title', 'body', 'image', 'data')

    def get_data(self, obj):
        data = dict()
        try:
            data = json.loads(obj.data)
        except Exception as e:
            print(e)
            data = {
                "app_module": "",
                "type": "",
                "id": 0
            }
        return data


class EtaskNotificationListSerializer(serializers.ModelSerializer):
    notification = NotificationMasterSerializer()

    class Meta:
        model = UserNotificationMapping
        fields = ('__all__')


class NotificationListSerializer(serializers.ModelSerializer):
    notification = NotificationMasterSerializer()

    class Meta:
        model = UserNotificationMapping
        fields = ('__all__')
