from django.core.management.base import BaseCommand
from ...tasks import send_appointment_reminders  # Import your reminder function

class Command(BaseCommand):
  help = 'Send appointment reminders'
  def handle(self, *args, **options):
    send_appointment_reminders()  