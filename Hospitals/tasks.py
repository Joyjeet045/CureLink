from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime, timedelta
from .models import Appointment
from django.db.models import Q

@shared_task
def send_appointment_reminders():
    now = datetime.now()
    print(f"[Celery Task] Current datetime: {now}")
    end = now + timedelta(hours=5)
    today = now.date()
    end_date = end.date()
    if today == end_date:
        upcoming_appointments = Appointment.objects.filter(
            appointment_date=today,
            time__gte=now.time(),
            time__lte=end.time()
        )
    else:
        upcoming_appointments = Appointment.objects.filter(
            Q(appointment_date=today, time__gte=now.time()) |
            Q(appointment_date=end_date, time__lte=end.time())
        )
    for appointment in upcoming_appointments:
        patient_name = appointment.user.username
        patient_email = appointment.user.email
        print(f"Sending a reminder to {patient_name} ({patient_email})")

        subject = "Upcoming Appointment Reminder"
        message = f'Hello {patient_name},\n\n' \
                  f'You have an upcoming appointment with Dr. {appointment.doctor.get_name} ' \
                  f'at {appointment.hospital.name} on {appointment.appointment_date} at {appointment.time}.\n\n' \
                  f'Please remember to prepare for your appointment.\n\n' \
                  f'Best regards,\nYour CureLink Team'

        from_email = settings.EMAIL_HOST_USER
        recipient_list = [patient_email]

        send_mail(subject, message, from_email, recipient_list)
