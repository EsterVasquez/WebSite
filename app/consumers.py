from channels.generic.websocket import AsyncJsonWebsocketConsumer


class DashboardChatConsumer(AsyncJsonWebsocketConsumer):
    group_name = "dashboard_chats"

    async def connect(self):
        user = self.scope.get("user")
        if user is None or not user.is_authenticated:
            await self.close(code=4401)
            return
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        # El dashboard no requiere mensajes entrantes por websocket.
        return

    async def chat_event(self, event):
        await self.send_json(
            {
                "event": event.get("event", "chat.updated"),
                "user_id": event.get("user_id"),
            }
        )
