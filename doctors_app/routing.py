from django.urls import re_path
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from Hospitals.consumers import VideoCallConsumer, ChatConsumer, OnlineDoctorCountConsumer, SymptomRequestConsumer, PatientWaitingConsumer

websocket_urlpatterns = [
    re_path(r'ws/video/(?P<room_name>[^/]+)/$', VideoCallConsumer.as_asgi()),
    re_path(r'ws/chat/(?P<room_name>[^/]+)/$', ChatConsumer.as_asgi()),
    re_path(r'ws/online_doctor_count/$', OnlineDoctorCountConsumer.as_asgi()),
    re_path(r'ws/doctor_requests/$', SymptomRequestConsumer.as_asgi()),
    re_path(r'ws/patient_waiting/(?P<room_id>[^/]+)/$', PatientWaitingConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
}) 