# session_manager.py
import secrets
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from django.db import models
from .models import UserSession

class SessionManager:
    def __init__(self):
        self.cookie_settings = {
            'httponly': False,
            'secure': False,
            'samesite': 'Lax'
        }
    
    def generate_session_id(self):
        return secrets.token_urlsafe(32)
    
    def create_session(self, user_id, user_type, tokens):
        session_id = self.generate_session_id()
        expires_at = timezone.now() + settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']
        
        UserSession.objects.create(
            session_id=session_id,
            user_id=user_id,
            user_type=user_type,
            access_token=tokens['access'],
            refresh_token=tokens['refresh'],
            expires_at=expires_at
        )
        return session_id
    
    def get_session(self, session_id):
        try:
            session = UserSession.objects.get(
                session_id=session_id,
                is_active=True,
                expires_at__gt=timezone.now()
            )
            # Update last used timestamp
            session.save()
            return session
        except UserSession.DoesNotExist:
            return None
    
    def invalidate_session(self, session_id):
        UserSession.objects.filter(session_id=session_id).update(
            is_active=False
        )
    
    def cleanup_expired_sessions(self):
        UserSession.objects.filter(
            models.Q(expires_at__lt=timezone.now()) |
            models.Q(last_used__lt=timezone.now() - timedelta(days=7))
        ).delete()
