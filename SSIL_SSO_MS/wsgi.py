"""
WSGI config for SSIL_SSO_MS project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('SERVER_GATEWAY_INTERFACE', 'Web')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SSIL_SSO_MS.settings')

application = get_wsgi_application()
