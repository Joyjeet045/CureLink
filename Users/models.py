from django.db import models

# Create your models here.
class AdminKey(models.Model):
  admin_key=models.CharField(max_length=50,unique=True)