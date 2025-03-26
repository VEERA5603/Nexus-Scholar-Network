# studentnsn/apps.py
from django.apps import AppConfig

class StudentnsnConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'studentnsn'
    
    def ready(self):
        # Import admin to register models
        from . import admin