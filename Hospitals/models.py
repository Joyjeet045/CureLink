from django.db import models
from django.db.models import Avg
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import date,datetime
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
 
  
class Hospital(models.Model):
  #each doctor can also be associated with multiple hospitals
  name=models.CharField(max_length=200)
  state = models.ForeignKey(State, on_delete=models.CASCADE)
  location=models.CharField(max_length=80,default="Kolkata")
  description=models.TextField(default="A leading healthcare institution committed to providing high-quality medical care and compassionate services to our patients.")
  hospital_pic=models.ImageField(upload_to='profile_pic/HospitalPic/',null=True,blank=True)
  rating=models.BigIntegerField(default=3)
  def __str__(self):
    return self.name
  @property
  def get_url(self):
    if self.hospital_pic:
      return self.hospital_pic.url
    return '/media/df-h.jpg'
  def average_doctor_rating(self):
    avg_rating=self.doctors.aggregate(Avg('reviews__rating'))['reviews__rating__avg']
    if avg_rating is not None:
      self.rating=int(avg_rating)
      return int(avg_rating)
    return 3
  
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
  qualifications = models.TextField(blank=True, null=True)

  #getters
  @property
  def get_name(self):
    return self.firstname+" "+self.lastname
  
  def __str__(self):
    return "{} ({})".format(self.firstname,self.department)

class Timing(models.Model):
  doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
  hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
  day_of_week = models.CharField(max_length=10, choices=[
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ])
  start_time = models.TimeField()
  end_time = models.TimeField()
  def __str__(self):
    return f"{self.doctor.get_name}'s Timing at {self.hospital.name} on {self.day_of_week} ({self.start_time} - {self.end_time})"
  def save(self, *args, **kwargs):
    super().save(*args, **kwargs)
    # Add the hospital to the doctor's list of hospitals
    if self.doctor and self.hospital:
        self.doctor.hospitals.add(self.hospital)


def validate_rating(value):
  if value>5 or value<0:
    raise ValidationError('Invalid Rating')
class Review(models.Model):
  doctor=models.ForeignKey(Doctor,on_delete=models.CASCADE,related_name='reviews')
  user=models.ForeignKey(User,on_delete=models.CASCADE)
  rating=models.BigIntegerField(default=0,validators=[validate_rating])
  comment=models.TextField()
  created_at=models.DateTimeField(auto_now_add=True)
  def __str__(self):
    return f'{self.user.username} - {self.doctor.get_name}'

  class Meta:
      ordering = ['-created_at']

class Appointment(models.Model):
  user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments')
  doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)  
  hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)  
  appointment_date = models.DateField()
  time = models.TimeField()
  notes=models.TextField(blank=True)
  status=models.BooleanField(default=True)
  # Add more fields as needed, such as appointment status, notes, etc.

  def __str__(self):
    return f"Appointment with Dr. {self.doctor.get_name} at {self.hospital.name} on {self.appointment_date}"
  def save(self, *args, **kwargs):
    if self.appointment_date<date.today():
      self.status = False  # Set status to False if the date is in the past
    super(Appointment, self).save(*args, **kwargs)
  class Meta:
    ordering = ['appointment_date', 'time']

