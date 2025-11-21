import time
import json
import jwt

from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async


class TimerConsumer(AsyncWebsocketConsumer):


    @database_sync_to_async
    def get_user(self, user_id):
        User = get_user_model()
        return User.objects.get(id=user_id)


    @database_sync_to_async
    def update_user_time(self, user_id, new_time):
        User = get_user_model()
        return User.objects.filter(id=user_id).update(total_time=new_time)

    async def connect(self):
        print("\n================ CONNECT EVENT ================")

        query_string = self.scope["query_string"].decode()
        token = None


        if "token=" in query_string:
            token = query_string.split("token=")[-1]

        if not token:
            print(" No token provided")
            await self.close()
            return


        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")
            self.user = await self.get_user(user_id)
        except Exception as e:
            print(f" Invalid token: {e}")
            await self.close()
            return

        self.old_total_time = int(self.user.total_time)
        print(f"User: {self.user.email}")
        print(f"Loaded total_time: {self.old_total_time}s")

        if self.old_total_time <= 0:
            print(" No remaining time. Closing connection.")
            await self.close()
            return


        self.start_time = time.time()


        await self.accept()

        await self.send(json.dumps({
            "message": "Timer started",
            "remaining_time": self.old_total_time,
            "user_type": self.user.plan_type
        }))

        print("=================================================\n")

    async def disconnect(self, close_code):
        print("\n================ DISCONNECT EVENT ================")

        if not hasattr(self, "start_time"):
            print("No valid timer session to compute.")
            return


        end_time = time.time()
        session_time = int(end_time - self.start_time)


        new_total_time = self.old_total_time - session_time

        if new_total_time < 0:
            new_total_time = 0

        print(f"User: {self.user.email}")
        print(f"Session Used: {session_time}s")
        print(f"Old Total Time: {self.old_total_time}s")
        print(f"New Remaining Time: {new_total_time}s")

 
        await self.update_user_time(self.user.id, new_total_time)

     
        try:
            await self.send(json.dumps({
                "message": "Timer stopped",
                "session_time": session_time,
                "remaining_time": new_total_time,
                "user_type": self.user.plan_type
            }))
        except:
            pass

        print("Saved updated remaining time to DB.")
