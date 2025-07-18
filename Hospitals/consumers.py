import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from .models import Doctor, VideoAppointment
import subprocess
import sys
import os
from datetime import datetime

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

class SymptomRequestConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Check if user has a doctor profile using database_sync_to_async
        has_doctor_profile = await self.check_doctor_profile()
        
        if has_doctor_profile:
            doctor_id = await self.get_doctor_id()
            self.doctor_group = f'doctor_requests_{doctor_id}'
            await self.channel_layer.group_add(
                self.doctor_group,
                self.channel_name
            )
            await self.accept()
        else:
            await self.close()

    @database_sync_to_async
    def check_doctor_profile(self):
        """Check if user has a doctor profile"""
        try:
            return hasattr(self.user, 'doctor_profile') and self.user.doctor_profile is not None
        except:
            return False

    @database_sync_to_async
    def get_doctor_id(self):
        """Get the doctor ID for the current user"""
        try:
            return self.user.doctor_profile.id
        except:
            return None

    async def disconnect(self, close_code):
        if hasattr(self, 'doctor_group'):
            await self.channel_layer.group_discard(
                self.doctor_group,
                self.channel_name
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'join_request':
            await self.handle_join_request(data)
        elif message_type == 'decline_request':
            await self.handle_decline_request(data)

    async def handle_join_request(self, data):
        appointment_id = data.get('appointment_id')
        success = await self.join_video_appointment(appointment_id)
        if success:
            # Notify other doctors that this request has been accepted
            await self.notify_request_accepted(appointment_id)

    async def handle_decline_request(self, data):
        appointment_id = data.get('appointment_id')
        await self.decline_video_appointment(appointment_id)

    async def notify_request_accepted(self, appointment_id):
        """Notify all doctors that this request has been accepted by someone"""
        channel_layer = get_channel_layer()
        # Get all online doctors
        doctors = await self.get_online_doctors()
        current_doctor_id = await self.get_doctor_id()
        
        # Notify other doctors that request was accepted
        for doctor in doctors:
            if doctor.id != current_doctor_id:  # Don't notify the accepting doctor
                await channel_layer.group_send(
                    f'doctor_requests_{doctor.id}',
                    {
                        'type': 'request_accepted',
                        'appointment_id': appointment_id
                    }
                )
        
        # Notify the patient that their request was accepted
        doctor_name = await self.get_doctor_name()
        await channel_layer.group_send(
            f'patient_waiting_{appointment_id}',
            {
                'type': 'doctor_accepted',
                'appointment_id': appointment_id,
                'doctor_name': doctor_name
            }
        )

    @database_sync_to_async
    def get_doctor_name(self):
        """Get the doctor name for the current user"""
        try:
            return self.user.doctor_profile.get_name
        except:
            return "Doctor"

    @database_sync_to_async
    def get_online_doctors(self):
        return list(Doctor.objects.filter(video_online=True))

    @database_sync_to_async
    def join_video_appointment(self, appointment_id):
        try:
            appointment = VideoAppointment.objects.get(id=appointment_id, status='pending')
            doctor = self.get_doctor_profile()
            if doctor:
                appointment.doctor = doctor
                appointment.status = 'active'
                appointment.start_time = datetime.now()
                appointment.save()
                return True
            return False
        except VideoAppointment.DoesNotExist:
            return False

    @database_sync_to_async
    def decline_video_appointment(self, appointment_id):
        try:
            appointment = VideoAppointment.objects.get(id=appointment_id, status='pending')
            appointment.status = 'ended'
            appointment.save()
            return True
        except VideoAppointment.DoesNotExist:
            return False

    def get_doctor_profile(self):
        """Get the doctor profile for the current user"""
        try:
            return self.user.doctor_profile
        except:
            return None

    async def send_request(self, event):
        """Send a symptom-based request to the doctor"""
        await self.send(text_data=json.dumps({
            'type': 'symptom_request',
            'appointment_id': event['appointment_id'],
            'patient_name': event['patient_name'],
            'symptoms': event['symptoms'],
            'specialties': event['specialties']
        }))

    async def request_accepted(self, event):
        """Notify when a request has been accepted by another doctor"""
        await self.send(text_data=json.dumps({
            'type': 'request_accepted',
            'appointment_id': event['appointment_id']
        }))

    async def request_declined(self, event):
        """Notify when a request has been declined"""
        await self.send(text_data=json.dumps({
            'type': 'request_declined',
            'appointment_id': event['appointment_id']
        }))

class PatientWaitingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'patient_waiting_{self.room_id}'
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
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'cancel_request':
            await self.handle_cancel_request(data)

    async def handle_cancel_request(self, data):
        room_id = data.get('room_id')
        await self.cancel_video_appointment(room_id)

    @database_sync_to_async
    def cancel_video_appointment(self, room_id):
        try:
            appointment = VideoAppointment.objects.get(id=room_id, status='pending')
            appointment.status = 'ended'
            appointment.save()
            return True
        except VideoAppointment.DoesNotExist:
            return False

    async def doctor_accepted(self, event):
        """Notify patient that a doctor has accepted their request"""
        await self.send(text_data=json.dumps({
            'type': 'doctor_accepted',
            'appointment_id': event['appointment_id'],
            'doctor_name': event['doctor_name']
        }))

    async def request_cancelled(self, event):
        """Notify patient that their request has been cancelled"""
        await self.send(text_data=json.dumps({
            'type': 'request_cancelled',
            'appointment_id': event['appointment_id']
        })) 