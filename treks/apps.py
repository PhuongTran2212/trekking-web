<<<<<<< HEAD
# treks/apps.py
from django.apps import AppConfig

class TreksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'treks'
    def ready(self): import treks.signals
=======
from django.apps import AppConfig


class TreksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'treks'
>>>>>>> 2a3c570e2a74a83ea4beae6f32f15af4df86cb43
