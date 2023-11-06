import os
from django.core.wsgi import get_wsgi_application
from django.conf import settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "doctors_app.settings")
application = get_wsgi_application()
from datetime import datetime,date,timedelta
from Hospitals.models import Appointment,Doctor
from django.db.models import Q
from django.db.models import Count

# hospital_name = "Apollo Gleneagles Hospitals" 
# location="Kolkata"
# hospital=Hospital.objects.filter(location=location)
# for h in hospital:
#   print(h.description)
# hospital = Hospital.objects.get(name=hospital_name).location

# l_hospital=Hospital.objects.filter(location=location)
# for hospital in l_hospital:
#   print(hospital.state)

# unique_locations = Hospital.objects.values_list('location', flat=True).distinct()
# for location in unique_locations:
#   print(location)


# hospitals_list = Hospital.objects.all()
# print(len(hospitals_list))  # Add this line to check if it contains data

# doctor=Doctor.objects.first()
# hospitals=doctor.hospitals.all()
# for hospital in hospitals:
#   print(hospital.name)
# print(doctor.profile_pic.width)
# print(doctor.profile_pic.url)

# states = State.objects.all()
# print(states)

# hospital=Hospital.objects.select_related('state').order_by("state__name")
# for h in hospital:
#   print(h.state)

# name="Indraprastha Apollo Hospitals"
# hospital=Hospital.objects.get(name=name)

# print(hospital.hospital_pic.url)

# print(settings.MEDIA_URL)



# from datetime import date
# from Hospitals.models import Appointment

# Appointment.objects.filter(appointment_date__lt=date.today()).update(status=False)

# from geopy.geocoders import Nominatim

# # Create a Nominatim geocoder instance
# geolocator = Nominatim(user_agent="GetLoc")

# # Geocode an address to get its coordinates
# location = geolocator.geocode("Kangra")

# if location:
#     print("Latitude:", location.latitude)
#     print("Longitude:", location.longitude)
# else:
#     print("Location not found.")


# print(datetime.now().time())
# appt_time=Appointment.objects.filter(hospital__name="Fortis Hospital & Kidney Institute",user__username="Joyjeet031",time__lt=datetime.now().time())
# for i in appt_time:
#   print(i.time)

# current_time = datetime.now().time()
# target_time = datetime.strptime("10:00:00", "%H:%M:%S").time()
# if current_time < target_time:
#     print("Current time is before the target time.")
# elif current_time > target_time:
#     print("Current time is after the target time.")
# else:
#     print("Current time is the same as the target time.")
# appt_time=Appointment.objects.filter(user__username="Joyjeet031",time__lt=datetime.now().time())
# for i in appt_time:
#   print(i.appointment_date)

# today=date.today()
# now = datetime.now()

# print(today)
# print()
# upcoming_appointments = Appointment.objects.filter(
#     Q(user__username="Joyjeet031", appointment_date=today,time__gt=now.time())
# | Q(user__username="Joyjeet031",appointment_date__gt=today))

# for apt in upcoming_appointments:
#   print(apt.appointment_date)


# print(datetime.now().time())
doctor=Doctor.objects.get(firstname="Parth")
today=date.today()+timedelta(hours=24)
appointment_count =Appointment.objects.filter(
  doctor=doctor,
  appointment_date=today
).count()

# print(date.today()+timedelta(hours=5))
print(appointment_count)