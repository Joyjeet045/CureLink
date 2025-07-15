from django.db import models
from django.db.models import Avg
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import date

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

  def __str__(self):
    return f"Appointment with Dr. {self.doctor.get_name} at {self.hospital.name} on {self.appointment_date}"
  def save(self, *args, **kwargs):
    if self.appointment_date<date.today():
      self.status = False  
    super(Appointment, self).save(*args, **kwargs)
  class Meta:
    ordering = ['appointment_date', 'time']

class Prescription(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='prescription')
    diagnosis = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f'Prescription for {self.appointment}'

class Medicine(models.Model):
    CURE_CHOICES = [
        ('Body Pain', 'Body Pain'),
        ('Diabetes', 'Diabetes'),
        ('Fever', 'Fever'),
        ('Cold', 'Cold'),
        ('Hypertension', 'Hypertension'),
        ('Allergy', 'Allergy'),
        ('Asthma', 'Asthma'),
        ('Other', 'Other'),
    ]
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    requires_prescription = models.BooleanField(default=False)
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='medicines')
    stock = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    picture = models.ImageField(upload_to='medicine_pics/', null=True, blank=True)
    cure_to = models.CharField(max_length=30, choices=CURE_CHOICES, default='Body Pain')
    def __str__(self):
        return self.name

class MedicineEntry(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='medicines')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    dosage = models.PositiveIntegerField()
    dosage_unit = models.CharField(max_length=20, default='Tablet(s)')
    num_days = models.PositiveIntegerField()
    frequency = models.CharField(max_length=50)
    food_relation = models.CharField(max_length=50, blank=True)
    def __str__(self):
        return f'{self.medicine.name} ({self.dosage} {self.dosage_unit})'

