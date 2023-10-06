# Generated by Django 3.2.7 on 2023-10-04 03:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Hospitals', '0003_doctor'),
    ]

    operations = [
        migrations.AddField(
            model_name='hospital',
            name='description',
            field=models.TextField(default='A leading healthcare institution committed to providing high-quality medical care and compassionate services to our patients.'),
        ),
    ]
