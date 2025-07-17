from django.db import models
from django.db.models import Avg
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import date
from datetime import datetime, timedelta

doctor_departments = [
  "Cardiology",
  "Orthopedics",
  "Dermatology",
  "Pediatrics",
  "Obstetrics and Gynecology",
  "Neurology",
  "Ophthalmology",
  "ENT (Ear, Nose, and Throat)"
]
department_choices = [(department, department) for department in doctor_departments]
class State(models.Model):
  name=models.CharField(max_length=100)
  def __str__(self):
    return self.name
 
  
class Hospital(models.Model):
  name=models.CharField(max_length=200)
  state = models.ForeignKey(State, on_delete=models.CASCADE)
  address = models.CharField(max_length=80, default="Kolkata")
  latitude = models.FloatField(default=22.5744)
  longitude = models.FloatField(default=88.3629)
  description=models.TextField(default="A leading healthcare institution committed to providing high-quality medical care and compassionate services to our patients.")
  hospital_pic=models.ImageField(upload_to='profile_pic/HospitalPic/',null=True,blank=True)
  rating=models.BigIntegerField(default=3)
  def __str__(self):
    return self.name
  @property
  def get_url(self):
    if self.hospital_pic:
      return self.hospital_pic.url
    return '/media/df-h.jpg'
  def average_doctor_rating(self):
    avg_rating=self.doctors.aggregate(Avg('reviews__rating'))['reviews__rating__avg']
    if avg_rating is not None:
      self.rating=int(avg_rating)
      return int(avg_rating)
    return 3
  
class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    profile_pic = models.ImageField(upload_to='profile_pic/DoctorProfilePic/', null=True, blank=True)
    mobile = models.CharField(max_length=20)
    department = models.CharField(max_length=30, choices=department_choices, default="Cardiology")
    status = models.BooleanField(default=True)
    video_online = models.BooleanField(default=False)
    hospitals = models.ManyToManyField(Hospital, related_name='doctors')
    qualifications = models.TextField(blank=True, null=True)

    @property
    def get_name(self):
        return f"{self.user.first_name} {self.user.last_name}"

    def get_available_slots(self, hospital, appointment_date, user=None):
        day_name = appointment_date.strftime('%A')
        timings = Timing.objects.filter(
            doctor=self,
            hospital=hospital,
            day_of_week=day_name
        )
        available_slots = []
        for timing in timings:
            available_capacity = timing.get_available_capacity(appointment_date, user=user)
            if available_capacity > 0:
                available_slots.append({
                    'timing': timing,
                    'start_time': timing.start_time,
                    'end_time': timing.end_time,
                    'available_capacity': available_capacity,
                    'max_capacity': timing.max_capacity
                })
        return available_slots

    def __str__(self):
        return f"{self.get_name} ({self.department})"

class Timing(models.Model):
  doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
  hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
  day_of_week = models.CharField(max_length=10, choices=[
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ])
  start_time = models.TimeField()
  end_time = models.TimeField()
  max_capacity = models.PositiveIntegerField(default=10, help_text="Maximum number of appointments allowed in this time slot")
  
  def __str__(self):
    return f"{self.doctor.get_name}'s Timing at {self.hospital.name} on {self.day_of_week} ({self.start_time} - {self.end_time})"
  
  def get_available_capacity(self, appointment_date, user=None):
    """Get the number of available slots for a specific date"""
    # Get the day of week for the appointment date
    day_name = appointment_date.strftime('%A')
    # Check if this timing applies to the appointment date
    if day_name != self.day_of_week:
        return 0
    # Count existing appointments for this doctor, hospital, date, and time slot
    existing_appointments = Appointment.objects.filter(
        doctor=self.doctor,
        hospital=self.hospital,
        appointment_date=appointment_date,
        time__gte=self.start_time,
        time__lt=self.end_time,
        status=True
    )
    existing_count = existing_appointments.count()
    return max(0, self.max_capacity - existing_count)
  
  def is_available(self, appointment_date, user=None):
    """Check if there are available slots for a specific date"""
    return self.get_available_capacity(appointment_date, user=user) > 0
  
  def check_overlapping_timings(self):
    """Check if this timing overlaps with other timings for the same doctor, hospital, and day"""
    overlapping = Timing.objects.filter(
      doctor=self.doctor,
      hospital=self.hospital,
      day_of_week=self.day_of_week
    ).exclude(pk=self.pk).filter(
      models.Q(start_time__lt=self.end_time, end_time__gt=self.start_time)
    )
    return overlapping.exists()
  
  def save(self, *args, **kwargs):
    # Check for overlapping timings before saving
    if self.pk is None:  # Only check for new timings
      if self.check_overlapping_timings():
        raise ValidationError(
          f"Timing slot overlaps with existing timing for Dr. {self.doctor.get_name} "
          f"at {self.hospital.name} on {self.day_of_week}. "
          f"Please choose a different time range."
        )
    
    super().save(*args, **kwargs)
    if self.doctor and self.hospital:
        self.doctor.hospitals.add(self.hospital)

  class Meta:
    constraints = [
        models.CheckConstraint(
            check=models.Q(start_time__lt=models.F('end_time')),
            name='timing_start_before_end'
        ),
    ]

def validate_rating(value):
  if value>5 or value<0:
    raise ValidationError('Invalid Rating')
class Review(models.Model):
  doctor=models.ForeignKey(Doctor,on_delete=models.CASCADE,related_name='reviews')
  user=models.ForeignKey(User,on_delete=models.CASCADE)
  rating=models.BigIntegerField(default=0,validators=[validate_rating])
  comment=models.TextField()
  created_at=models.DateTimeField(auto_now_add=True)
  def __str__(self):
    return f'{self.user.username} - {self.doctor.get_name}'

  class Meta:
      ordering = ['-created_at']

class Appointment(models.Model):
  user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments')
  doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)  
  hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)  
  appointment_date = models.DateField()
  time = models.TimeField()
  notes=models.TextField(blank=True)
  status=models.BooleanField(default=True)

  def __str__(self):
    return f"Appointment with Dr. {self.doctor.get_name} at {self.hospital.name} on {self.appointment_date}"
  
  def clean(self):
    """Validate appointment capacity and prevent double booking"""
    from django.core.exceptions import ValidationError
    
    if self.appointment_date and self.time and self.doctor and self.hospital:
      day_name = self.appointment_date.strftime('%A')
      matching_timings = Timing.objects.filter(
        doctor=self.doctor,
        hospital=self.hospital,
        day_of_week=day_name,
        start_time__lte=self.time,
        end_time__gt=self.time
      )
      
      if not matching_timings.exists():
        raise ValidationError("No timing slot found for this doctor, hospital, and time.")
      
      timing = min(matching_timings, key=lambda t: time_to_seconds(t.end_time) - time_to_seconds(t.start_time))
      
      double_booking_query = Appointment.objects.filter(
        user=self.user,
        appointment_date=self.appointment_date,
        time__gte=timing.start_time,
        time__lt=timing.end_time,
        status=True
      )
      
      if self.pk:
        double_booking_query = double_booking_query.exclude(pk=self.pk)
      
      if double_booking_query.exists():
        existing_appointment = double_booking_query.first()
        raise ValidationError(
          f"You already have an appointment on {self.appointment_date} at {existing_appointment.time.strftime('%H:%M')} "
          f"with Dr. {existing_appointment.doctor.get_name} at {existing_appointment.hospital.name}. "
          "Please choose a different time slot or date."
        )
      
      available_capacity = timing.get_available_capacity(self.appointment_date)
      
      if not self.pk:
        if available_capacity <= 0:
          raise ValidationError(f"No available slots for this time. Maximum capacity ({timing.max_capacity}) has been reached.")
      else:
        existing_count = Appointment.objects.filter(
          doctor=self.doctor,
          hospital=self.hospital,
          appointment_date=self.appointment_date,
          time__gte=timing.start_time,
          time__lt=timing.end_time,
          status=True
        ).exclude(pk=self.pk).count()
        
        if existing_count >= timing.max_capacity:
          raise ValidationError(f"No available slots for this time. Maximum capacity ({timing.max_capacity}) has been reached.")
  
  def save(self, *args, **kwargs):
    if self.appointment_date<date.today():
      self.status = False
    self.clean() 
    super(Appointment, self).save(*args, **kwargs)
  
  class Meta:
    ordering = ['appointment_date', 'time']

class Prescription(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='prescription')
    diagnosis = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f'Prescription for {self.appointment}'

class Medicine(models.Model):
    CURE_CHOICES = [
        ('Body Pain', 'Body Pain'),
        ('Diabetes', 'Diabetes'),
        ('Fever', 'Fever'),
        ('Cold', 'Cold'),
        ('Hypertension', 'Hypertension'),
        ('Allergy', 'Allergy'),
        ('Asthma', 'Asthma'),
        ('Other', 'Other'),
    ]
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    requires_prescription = models.BooleanField(default=False)
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='medicines')
    stock = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    picture = models.ImageField(upload_to='medicine_pics/', null=True, blank=True)
    cure_to = models.CharField(max_length=30, choices=CURE_CHOICES, default='Body Pain')
    def __str__(self):
        return self.name

class MedicineEntry(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='medicines')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    dosage = models.PositiveIntegerField()
    dosage_unit = models.CharField(max_length=20, default='Tablet(s)')
    num_days = models.PositiveIntegerField()
    frequency = models.CharField(max_length=50)
    food_relation = models.CharField(max_length=50, blank=True)
    def __str__(self):
        return f'{self.medicine.name} ({self.dosage} {self.dosage_unit})'

class DoctorLeave(models.Model):
    doctor = models.ForeignKey('Doctor', on_delete=models.CASCADE, related_name='leaves')
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{str(self.doctor)} leave from {self.start_date} to {self.end_date}"


# Utility functions for capacity management
def get_doctor_schedule_with_capacity(doctor, hospital, date, user=None):
    """
    Get doctor's schedule for a specific date with capacity information
    """
    day_name = date.strftime('%A')
    timings = Timing.objects.filter(
        doctor=doctor,
        hospital=hospital,
        day_of_week=day_name
    )
    
    schedule = []
    for timing in timings:
        available_capacity = timing.get_available_capacity(date, user=user)
        schedule.append({
            'timing': timing,
            'start_time': timing.start_time,
            'end_time': timing.end_time,
            'available_capacity': available_capacity,
            'max_capacity': timing.max_capacity,
            'is_available': available_capacity > 0
        })
    
    return schedule


def time_to_seconds(t):
    return t.hour * 3600 + t.minute * 60 + t.second


def check_appointment_availability(doctor, hospital, appointment_date, appointment_time, user=None):
    """
    Check if an appointment slot is available
    """
    day_name = appointment_date.strftime('%A')
    
    matching_timings = Timing.objects.filter(
        doctor=doctor,
        hospital=hospital,
        day_of_week=day_name,
        start_time__lte=appointment_time,
        end_time__gt=appointment_time
    )
    
    if not matching_timings.exists():
        return False
    
    timing = min(matching_timings, key=lambda t: time_to_seconds(t.end_time) - time_to_seconds(t.start_time))
    return timing.get_available_capacity(appointment_date, user=user) > 0


def get_user_existing_appointments(user, appointment_date):
    """
    Get user's existing appointments for a specific date
    """
    return Appointment.objects.filter(
        user=user,
        appointment_date=appointment_date,
        status=True
    ).select_related('doctor', 'hospital')


def check_user_double_booking(user, appointment_date, timing_start, timing_end, exclude_appointment_id=None):
    """
    Check if user has any existing appointments in the given time range
    """
    query = Appointment.objects.filter(
        user=user,
        appointment_date=appointment_date,
        time__gte=timing_start,
        time__lt=timing_end,
        status=True
    )
    
    if exclude_appointment_id:
        query = query.exclude(pk=exclude_appointment_id)
    
    return query.exists()

class VideoAppointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('ended', 'Ended'),
    ]
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='video_appointments')
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='video_appointments')
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"VideoAppointment: {self.patient.username} with Dr. {self.doctor.get_name} ({self.status})"


class TestType(models.Model):
    SAMPLE_CHOICES = [
        ('blood', 'Blood'),
        ('urine', 'Urine'),
        ('saliva', 'Saliva'),
        ('stool', 'Stool'),
        ('swab', 'Swab'),
    ]
    SLOT_CHOICES = [
        ('09:00-10:00', '09:00 - 10:00'),
        ('10:00-11:00', '10:00 - 11:00'),
        ('11:00-12:00', '11:00 - 12:00'),
        ('12:00-13:00', '12:00 - 13:00'),
        ('14:00-15:00', '14:00 - 15:00'),
        ('15:00-16:00', '15:00 - 16:00'),
        ('16:00-17:00', '16:00 - 17:00'),
    ]
    name = models.CharField(max_length=100, unique=True)
    sample_required = models.CharField(max_length=20, choices=SAMPLE_CHOICES, blank=True, help_text="Type of sample required")
    preferred_time_slots = models.JSONField(default=list, blank=True, help_text="Allowed time slots for this test. Leave blank for all slots.")

    def get_allowed_slots(self):
        if not self.preferred_time_slots:
            return [slot[0] for slot in self.SLOT_CHOICES]
        return self.preferred_time_slots

    def __str__(self):
        return self.name

class Test(models.Model):
    test_type = models.ForeignKey(TestType, on_delete=models.CASCADE, related_name='hospital_tests', null=True, blank=True)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='tests')
    price = models.DecimalField(max_digits=8, decimal_places=2)
    available = models.BooleanField(default=True)
    test_included = models.CharField(max_length=1000, blank=True, help_text="Comma-separated list of included test names (for packages)")
    package_discount = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Discount percentage for the package, if applicable")
    pre_test_instructions = models.TextField(blank=True, help_text="Instructions for the patient before taking the test or package")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.test_type.name if self.test_type else 'No TestType'} at {self.hospital.name}"

class MedicineOrder(models.Model):
    STATUS_CHOICES = [
        ('ordered', 'Ordered'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='medicine_orders')
    order_date = models.DateTimeField(auto_now_add=True)
    expected_delivery_date = models.DateField()
    delivery_address = models.TextField(default="123 Main Street, Apartment 4B, City Center, New Delhi")
    delivery_pincode = models.CharField(max_length=10, default="110001")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ordered')
    payment_status = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Order #{self.id} - {self.user.username} - {self.status}"
    
    def get_status_progress(self):
        """Returns the progress percentage for the status bar"""
        status_order = ['ordered', 'processing', 'shipped', 'delivered']
        try:
            current_index = status_order.index(self.status)
            return (current_index + 1) * 25  # 25% per step
        except ValueError:
            return 0

class MedicineOrderItem(models.Model):
    order = models.ForeignKey(MedicineOrder, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def save(self, *args, **kwargs):
        if not self.total_price:
            self.total_price = self.quantity * self.price_per_unit
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.quantity}x {self.medicine.name} - Order #{self.order.id}"


class TestOrder(models.Model):
    STATUS_CHOICES = [
        ('booked', 'Booked'),
        ('sample_collected', 'Sample Collected'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='test_orders')
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='test_orders')
    order_date = models.DateTimeField(auto_now_add=True)
    test_date = models.DateField()
    test_time = models.TimeField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='booked')
    payment_status = models.BooleanField(default=False)
    notes = models.TextField(blank=True, help_text="Additional notes for the test")
    
    def __str__(self):
        return f"Test Order #{self.id} - {self.user.username} - {self.status}"
    
    def get_status_progress(self):
        """Returns the progress percentage for the status bar"""
        status_order = ['booked', 'sample_collected', 'processing', 'completed']
        try:
            current_index = status_order.index(self.status)
            return (current_index + 1) * 25  # 25% per step
        except ValueError:
            return 0

class TestOrderItem(models.Model):
    order = models.ForeignKey(TestOrder, on_delete=models.CASCADE, related_name='items')
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def save(self, *args, **kwargs):
        if not self.price:
            self.price = self.test.price
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.test.test_type.name if self.test.test_type else 'Test'} - Order #{self.order.id}"

