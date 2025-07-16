from django.contrib import admin

# Register your models here.
from .models import Doctor,Hospital,Timing,Review,Appointment,Prescription,Medicine,Test,State,MedicineEntry, DoctorLeave, VideoAppointment, TestType

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
admin.site.register(Test)
admin.site.register(State)
admin.site.register(MedicineEntry)
admin.site.register(DoctorLeave)
admin.site.register(VideoAppointment)
admin.site.register(TestType)
