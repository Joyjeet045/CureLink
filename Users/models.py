from django.db import models
from django.contrib.auth.models import User

class AdminKey(models.Model):
  admin_key=models.CharField(max_length=50,unique=True)

class UserProfile(models.Model):
    USER_ROLES = [
        ('user', 'User'),
        ('doctor', 'Doctor'),
        ('seller', 'Seller'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=USER_ROLES, default='user')
    address = models.TextField(default="123 Main Street, Apartment 4B, City Center, New Delhi", help_text="Delivery address for medicines")
    pincode = models.CharField(max_length=10, default="110001", help_text="Pincode for delivery")

    def __str__(self):
        return f"{self.user.username} ({self.role})"
