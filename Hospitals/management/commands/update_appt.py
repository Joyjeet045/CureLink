from datetime import date
from Hospitals.models import Appointment
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Update appointment status to False for appointments with appointment_date < today'

    def handle(self, *args, **options):
        today = date.today()
        appointments_to_update = Appointment.objects.filter(appointment_date__lt=today, status=True)
        for appointment in appointments_to_update:
            appointment.status = False
            appointment.save()
            self.stdout.write(self.style.SUCCESS(f"Updated status for appointment ID {appointment.id}"))

        self.stdout.write(self.style.SUCCESS('Appointment statuses updated successfully.'))