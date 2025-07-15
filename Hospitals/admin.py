from django.contrib import admin

# Register your models here.
from .models import Doctor,Hospital,Timing,Review,Appointment,Prescription,Medicine
admin.site.register(Doctor)
admin.site.register(Hospital)
admin.site.register(Timing)
admin.site.register(Review)
admin.site.register(Appointment)
admin.site.register(Prescription)
admin.site.register(Medicine)
