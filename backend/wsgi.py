"""
WSGI config for DucksFinances project.

This module contains the WSGI application used by Django's development server
and any production WSGI deployments. It should expose a module-level variable
named ``application``. Django's ``runserver`` and ``runfcgi`` commands discover
this application via the ``WSGI_APPLICATION`` setting.

For more information on this file, see
https://docs.djangoproject.com/en/stable/howto/deployment/wsgi/
"""
import os
from django.core.wsgi import get_wsgi_application

# Set the default Django settings module for the 'wsgi' application.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

# This application object is used by any WSGI server configured to use this
# file. This includes Django's development server, if the WSGI_APPLICATION
# setting points here.
application = get_wsgi_application()
