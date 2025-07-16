from django.contrib import admin

# Register your models here.
from .models import Doctor,Hospital,Timing,Review,Appointment,Prescription,Medicine

@admin.register(Timing)
class TimingAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'hospital', 'day_of_week', 'start_time', 'end_time', 'max_capacity')
    list_filter = ('day_of_week', 'hospital', 'doctor__department')
    search_fields = ('doctor__firstname', 'doctor__lastname', 'hospital__name')
    ordering = ('day_of_week', 'start_time')

admin.site.register(Doctor)
admin.site.register(Hospital)
admin.site.register(Review)
admin.site.register(Appointment)
admin.site.register(Prescription)
admin.site.register(Medicine)
