from rest_framework.serializers import ModelSerializer
from .models import *

class NotificationSerializer(ModelSerializer):
    class Meta:
        model = Notifications
        fields = '__all__'