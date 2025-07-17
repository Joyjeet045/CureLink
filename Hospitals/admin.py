from django.contrib import admin
from django import forms
from django.contrib.admin.sites import AlreadyRegistered, NotRegistered

# Register your models here.
from .models import Doctor,Hospital,Timing,Review,Appointment,Prescription,Medicine,Test,State,MedicineEntry, DoctorLeave, VideoAppointment, TestType, MedicineOrder, MedicineOrderItem, TestOrder, TestOrderItem, DoctorHospitalRequest

@admin.register(Timing)
class TimingAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'hospital', 'day_of_week', 'start_time', 'end_time', 'max_capacity')
    list_filter = ('day_of_week', 'hospital', 'doctor__department')
    search_fields = ('doctor__firstname', 'doctor__lastname', 'hospital__name')
    ordering = ('day_of_week', 'start_time')

@admin.register(MedicineOrder)
class MedicineOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'order_date', 'expected_delivery_date', 'delivery_pincode', 'total_amount', 'status', 'payment_status')
    list_filter = ('status', 'payment_status', 'order_date')
    search_fields = ('user__username', 'user__email', 'delivery_address', 'delivery_pincode')
    readonly_fields = ('order_date',)
    ordering = ('-order_date',)

@admin.register(MedicineOrderItem)
class MedicineOrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'medicine', 'quantity', 'price_per_unit', 'total_price')
    list_filter = ('medicine__cure_to',)
    search_fields = ('order__user__username', 'medicine__name')
    readonly_fields = ('total_price',)

@admin.register(TestOrder)
class TestOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'hospital', 'test_date', 'test_time', 'total_amount', 'status', 'payment_status')
    list_filter = ('status', 'payment_status', 'test_date', 'hospital')
    search_fields = ('user__username', 'user__email', 'hospital__name', 'notes')
    readonly_fields = ('order_date',)
    ordering = ('-order_date',)

@admin.register(TestOrderItem)
class TestOrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'test', 'price')
    list_filter = ('test__test_type__name', 'test__hospital')
    search_fields = ('order__user__username', 'test__test_type__name', 'test__hospital__name')
    readonly_fields = ('price',)

class TestTypeAdminForm(forms.ModelForm):
    preferred_time_slots = forms.MultipleChoiceField(
        choices=TestType.SLOT_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Allowed Time Slots",
        help_text="Select allowed time slots for this test. Leave blank for all slots."
    )

    class Meta:
        model = TestType
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['preferred_time_slots'].initial = self.instance.preferred_time_slots

    def clean_preferred_time_slots(self):
        data = self.cleaned_data['preferred_time_slots']
        return data

class TestTypeAdmin(admin.ModelAdmin):
    form = TestTypeAdminForm
    list_display = ('name', 'sample_required', 'get_preferred_slots_display')

    def get_preferred_slots_display(self, obj):
        if not obj.preferred_time_slots:
            return 'All slots'
        return ', '.join([dict(TestType.SLOT_CHOICES).get(slot, slot) for slot in obj.preferred_time_slots])
    get_preferred_slots_display.short_description = 'Allowed Slots'

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
admin.site.register(DoctorHospitalRequest)
try:
    admin.site.unregister(TestType)
except NotRegistered:
    pass
admin.site.register(TestType, TestTypeAdmin)
