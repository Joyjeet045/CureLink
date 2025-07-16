import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Doctor

class VideoCallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'video_{self.room_name}'
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'signal_message',
                'message': text_data
            }
        )

    async def signal_message(self, event):
        await self.send(text_data=event['message'])

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': text_data
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=event['message'])

class OnlineDoctorCountConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = 'online_doctor_count'
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()
        # Send the current count on connect
        count = await self.get_online_doctor_count()
        await self.send(json.dumps({'count': count}))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def doctor_count_update(self, event):
        count = event['count']
        await self.send(json.dumps({'count': count}))

    @database_sync_to_async
    def get_online_doctor_count(self):
        return Doctor.objects.filter(video_online=True).count() 