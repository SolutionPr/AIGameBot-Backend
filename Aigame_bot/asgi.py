"""
ASGI config for Aigame_bot project.
"""

import utils.clients
import utils.http_session
import utils.transport
import utils.session
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Aigame_bot.settings")

application = get_asgi_application()
