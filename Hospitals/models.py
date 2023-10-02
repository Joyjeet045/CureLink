from django.db import models
from django.contrib.auth.models import User
# Create your models here.
doctor_departments = [
  "Cardiology",
  "Orthopedics",
  "Dermatology",
  "Pediatrics",
  "Obstetrics and Gynecology",
  "Neurology",
  "Ophthalmology",
  "ENT (Ear, Nose, and Throat)"
]
department_choices = [(department, department) for department in doctor_departments]
class State(models.Model):
  name=models.CharField(max_length=100)
  def __str__(self):
    return self.name
  7
class Hospital(models.Model):
  #each doctor can also be associated with multiple hospitals
  name=models.CharField(max_length=200)
  state = models.ForeignKey(State, on_delete=models.CASCADE)
  location=models.CharField(max_length=80)
  def __str__(self):
    return self.name
  
class Doctor(models.Model):
  # null=True is for allowing null in db and blank for form
  # mobile is passed as string
  #status is for whether doctor is available that day or not
  #we are not adding patient no here as it dynamic and will access through foreign key
  firstname=models.CharField(max_length=30)
  lastname=models.CharField(max_length=30)
  profile_pic=models.ImageField(upload_to='profile_pic/DoctorProfilePic/',null=True,blank=True)
  mobile=models.CharField(max_length=20)
  department=models.CharField(max_length=30,choices=department_choices,default="Cardiology")
  status=models.BooleanField(default=True)
  hospitals=models.ManyToManyField(Hospital,related_name='doctors')
  #getters
  @property
  def get_name(self):
    return self.user.first_name+" "+self.user.last_name
  @property
  def get_id(self):
    return self.user.id
  def __str__(self):
    return "{} ({})".format(self.user.first_name,self.department)

