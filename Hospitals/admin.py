from django.contrib import admin

# Register your models here.
from .models import Doctor,Hospital,Timing,Review
admin.site.register(Doctor)
admin.site.register(Hospital)
admin.site.register(Timing)
admin.site.register(Review)
