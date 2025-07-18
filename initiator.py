# populate_states.py
import json
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "doctors_app.settings")
django.setup()

data={"Kolkata": [
  "Apollo Gleneagles Hospitals,Kolkata",
  "Calcutta Medical College and Hospital,Kolkata",
  "Fortis Hospital & Kidney Institute,Kolkata"
],
"Maharashtra": [
  "Tata Memorial Hospital,Mumbai",
  "Lilavati Hospital,Mumbai",
  "KEM Hospital,Mumbai"
],
"Gujarat": [
  "Sardar Vallabhbhai Patel Institute of Medical Sciences and Research,Ahmedabad",
  "Apollo Hospitals,Ahmedabad",
  "Sterling Hospitals,Ahmedabad"
],
"Haryana": [
  "Post Graduate Institute of Medical Sciences (PGIMS),Rohtak",
  "Fortis Memorial Research Institute,Gurugram",
  "Artemis Hospital,Guyrugram"
],
"Himachal Pradesh": [
  "Indira Gandhi Medical College and Hospital,Shimla",
  "Dr. Rajendra Prasad Medical College,Kangra",
  "Tanda Medical College,Kangra"
],
"Delhi": [
  "All India Institute of Medical Sciences (AIIMS),Delhi",
  "Indraprastha Apollo Hospitals,Delhi",
  "Max Super Speciality Hospital,Saket"
],
"Goa": [
  "Goa Medical College and Hospital,Panaji",
  "Manipal Hospitals,Goa",
  "Victor Hospital,Margao"
],
"Karnataka": [
  "All India Institute of Medical Sciences (AIIMS),Mangaluru",
  "Manipal Hospitals,Bengaluru",
  "Narayana Health,Bengaluru"
]}
from Hospitals.models import State,Hospital

for state,hospitals in data.items():
  state,created=State.objects.get_or_create(name=state)
  for hospital_info in hospitals:
    hospital_name,location=hospital_info.split(",",1)
    hospital,created=Hospital.objects.get_or_create(
      name=hospital_name.strip(),
      state=state,
      location=location.strip()
    )

