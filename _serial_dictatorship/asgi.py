# """
# ASGI config for serial_dictatorship project.

# It exposes the ASGI callable as a module-level variable named ``application``.

# For more information on this file, see
# https://docs.djangoproject.com/en/3.1/howto/deployment/asgi/
# """

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "_serial_dictatorship.settings")
django_asgi_app = get_asgi_application()

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

import main.routing

application = ProtocolTypeRouter({
  "http": django_asgi_app,

  "websocket":
        AllowedHostsOriginValidator(
            AuthMiddlewareStack(
                URLRouter(
                    main.routing.websocket_urlpatterns
                )
            ),
        ),
})