from django.conf import settings
from notification.models import *
from core.models import *
import requests
import json

def send_notification(users=[],token_list=[], body='', title='', noti_type='',data={}, notification_id=0,url='etask'):
    #print('users',users)
    url='https://shyamsteel.tech/'+url+'/'
    #print('url',url)
    device_token_list = UserTokenMapping.objects.filter(user__in=users,is_deleted=False).values_list('device_token',flat=True)
    #print('device_token_list',device_token_list.query)
    device_token_list = list(device_token_list)
    #print('device_token_list',device_token_list)
    headers = {
                "Authorization": "key=AAAAyCbCSyI:APA91bG077lVyuxOFwSJ-HkEX_TGiswuxFg0FjwTyIMVDYgyp34tmzcV51Z9vlthAHpX_v9It_SR6hKWFSFT94M0fhJVP10g3WXK6gL2-fmrEZ5d-voikH3gY-DoNTHR4MFQ8V4ab0_A",
                "Content-Type": "application/json"
            }   
    payload = {
        "registration_ids": token_list if token_list else device_token_list,
        "notification": {
            "body": body,
            "title": title,
            "click_action": url,
            "vibrate": 1,
            "sound": 1,
            "priority":"high"
        },
        "data" : {
            "body" : body,
            "title": title,
            "data" : data,
            "notification_id" : notification_id,
            "app_module":data.get('app_module'),
	        "type":data.get('type'),
            "id":data.get('id')
        }
    }

    response = requests.post("https://fcm.googleapis.com/fcm/send", data=json.dumps(payload), headers=headers)
    json_raw_response = response.content.decode('utf-8')
    #json_decode_response = json.loads(json_raw_response)
    #print('json_decode_response',json_raw_response)
    # return json_decode_response

def store_sent_notification(users=[], body='', title='',code='',image=None,data=None,app_module_name=None):
    tcore_module = TCoreModule.objects.filter(cm_url=app_module_name).first()
    notification_master = NotificationMaster.objects.create(
        body=body,
        title=title,
        code=code,
        image=image,
        data=data
        )
    for user in users:
        UserNotificationMapping.objects.create(
            notification=notification_master,
            user=user,
            app_module_name=tcore_module
        )
    #print('notification_master.id',notification_master.id)
    return notification_master.id


    