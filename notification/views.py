from knox.auth import TokenAuthentication
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from custom_decorator import (response_modify_decorator_get,
                              response_modify_decorator_update)
from notification.models import (NotificationMaster, UserNotificationMapping,
                                 UserTokenMapping)
from notification.serializers import (AddDeviceTokenSerializer,
                                      EtaskNotificationListSerializer,
                                      NotificationListSerializer,
                                      NotificationTestingSerializer,
                                      ReadNotificationSerializer)


class NotificationTestingView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    serializer_class = NotificationTestingSerializer

    @response_modify_decorator_update
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class AddDeviceTokenView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = UserTokenMapping.objects.filter(is_deleted=False)
    serializer_class = AddDeviceTokenSerializer

    @response_modify_decorator_update
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class ReadNotificationView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = NotificationMaster.objects.filter()
    serializer_class = ReadNotificationSerializer

    @response_modify_decorator_update
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)


class EtaskNotificationListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = UserNotificationMapping.objects.filter(
        is_deleted=False).order_by('-id')
    serializer_class = EtaskNotificationListSerializer

    def get_queryset(self):
        user = self.request.user
        return self.queryset.filter(
            app_module_name__cm_url='etask', user=user, read_status=False)

    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class NotificationListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    queryset = UserNotificationMapping.objects.filter(is_deleted=False).order_by('-id')
    serializer_class = NotificationListSerializer

    def get_queryset(self):
        user = self.request.user
        module_name = self.kwargs['module_name']
        return self.queryset.filter(app_module_name__cm_url=module_name, user=user, read_status=False)

    @response_modify_decorator_get
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


