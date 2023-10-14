from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime,timedelta
from .models import Appointment
def send_appointment_reminders():
    threshold_time = timedelta(hours=10.5)
    #I am 5.5 hours ahead of server time(so for 5 hours we set +5.5 hrs)
    now = datetime.now()
    upcoming_appointments = Appointment.objects.filter(
        appointment_date=now.date(),
        time__gt=now.time(),
        time__lt=(now + threshold_time).time()
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
