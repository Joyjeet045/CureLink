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

    def __str__(self):
        return f"{self.user.username} ({self.role})"
