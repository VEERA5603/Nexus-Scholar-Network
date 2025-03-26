# management/commands/cleanup_sessions.py
from django.core.management.base import BaseCommand
from ...session_manager import SessionManager

class Command(BaseCommand):
    help = 'Cleanup expired and inactive sessions'

    def handle(self, *args, **options):
        session_manager = SessionManager()
        session_manager.cleanup_expired_sessions()