# treks/apps.py
from django.apps import AppConfig

class TreksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'treks'
    def ready(self): import treks.signals