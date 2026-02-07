from django.apps import AppConfig

<<<<<<< HEAD
class GamificationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gamification'

    def ready(self):
        import gamification.signals  # <--- THÊM DÒNG NÀY
=======

class GamificationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gamification'
>>>>>>> 2a3c570e2a74a83ea4beae6f32f15af4df86cb43
