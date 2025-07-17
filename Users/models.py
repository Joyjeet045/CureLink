from django.db import models
from django.contrib.auth.models import User
from Hospitals.models import Hospital

class AdminKey(models.Model):
  admin_key=models.CharField(max_length=50,unique=True)

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('doctor', 'Doctor'),
        ('seller', 'Seller'),
        ('hospital_admin', 'Hospital Admin'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    address = models.TextField(default="123 Main Street, Apartment 4B, City Center, New Delhi", help_text="Delivery address for medicines")
    pincode = models.CharField(max_length=10, default="110001", help_text="Pincode for delivery")

    def __str__(self):
        return f"{self.user.username} ({self.role})"

class HospitalAdminMapping(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hospital_admin_mappings')
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='admin_mappings')

    class Meta:
        unique_together = ('user', 'hospital')

    def __str__(self):
        return f"{self.user.username} - {self.hospital.name}"
