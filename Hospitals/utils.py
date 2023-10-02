import json

from .models import State,Hospital

def add_hospitals(file_path):
  with open(file_path,'r') as json_file:
    data=json.load(json_file)
  for state_name,hospitals in data.items():
    state,_=State.objects.get_or_create(name=state_name)
    for hospital_info in hospitals:
      hospital_name, hospital_location = hospital_info.split(',')
      Hospital.objects.get_or_create(
          name=hospital_name,
          state=state,
          location=hospital_location
      )
add_hospitals("../hospitals.json")