import asyncio
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import json

from .models import Notifications
from .serializers import NotificationSerializer


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]

        if self.user.is_anonymous:
            await self.close()
        else:
            self.group_name = f"user_{self.user.id}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_notification(self, event):
        notification = event['notification']
        await self.send(text_data=json.dumps(notification))

    @database_sync_to_async
    def create_notification(self, message, related_object=None):
        notification = Notifications.objects.create(
            user = self.user,
            message = message,
            content_type = getattr(related_object, 'content_type', None) if related_object else None,
            object_id = getattr(related_object, 'id', None) if related_object else None,
        )

        return NotificationSerializer(notification).data