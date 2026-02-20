from django.urls import re_path

from app.consumers import DashboardChatConsumer


websocket_urlpatterns = [
    re_path(r"^ws/chats/$", DashboardChatConsumer.as_asgi()),
]
