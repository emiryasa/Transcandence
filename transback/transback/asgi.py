import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from transbackend.consumers import PongConsumer as GameConsumer, MatchmakingConsumer, OnlineStatusConsumer

from channels.auth import AuthMiddlewareStack
from django.urls import path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transback.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
            URLRouter([
                path("ws/matchmaking/", MatchmakingConsumer.as_asgi()),
                path("ws/game/<int:room_id>/", GameConsumer.as_asgi()),
                path("ws/online-status/", OnlineStatusConsumer.as_asgi()),
            ])
        ),
})
