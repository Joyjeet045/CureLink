# Standard Django and third-party imports
from django.shortcuts import render, get_object_or_404, redirect
from django.core import serializers
from django.db import transaction
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Doctor, Hospital, State, Timing, Review, Appointment, Medicine, Prescription, MedicineEntry, DoctorLeave, VideoAppointment, TestType, Test, MedicineOrder, MedicineOrderItem, TestOrder, TestOrderItem, TestReport
import heapq
from geopy.distance import geodesic
from .constants import doctor_departments
from datetime import datetime, date, timedelta
from geopy.geocoders import Nominatim
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.conf import settings

from django.views.decorators.csrf import csrf_exempt
from Users.models import UserProfile
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from Users.models import HospitalAdminMapping
from .models import DoctorHospitalRequest
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import uuid
import subprocess
import json

from django import forms

class AddTestForm(forms.Form):
    test_type = forms.ModelChoiceField(queryset=TestType.objects.all(), label="Test Type")
    price = forms.DecimalField(max_digits=8, decimal_places=2)
    test_included = forms.CharField(max_length=1000, required=False, label="Included Tests (comma-separated)")
    package_discount = forms.DecimalField(max_digits=5, decimal_places=2, required=False, label="Package Discount (%)")
    pre_test_instructions = forms.CharField(widget=forms.Textarea, required=False, label="Pre-test Instructions")

class TestReportForm(forms.ModelForm):
    class Meta:
        model = TestReport
        fields = ['findings_positive', 'findings_negative', 'report_file']
        labels = {
            'findings_positive': 'Positive Findings',
            'findings_negative': 'Negative Findings',
            'report_file': 'Attach Report File (PDF, Image, etc.)',
        }
        widgets = {
            'findings_positive': forms.Textarea(attrs={'rows': 3, 'placeholder': 'E.g. Normal blood count, no infection...'}),
            'findings_negative': forms.Textarea(attrs={'rows': 3, 'placeholder': 'E.g. High cholesterol, abnormal ECG...'}),
        }


def is_authenticated(user):
  return user.is_authenticated
def is_admin(user):
  return user.is_staff

def geocode_hospitals(h_location):
  geolocator = Nominatim(user_agent="GetLoc")
  location = geolocator.geocode(h_location)
  if location is not None:
    return location.latitude, location.longitude
  return None,None

@user_passes_test(is_authenticated,login_url="/login/")
def home_page(request):
    user = request.user
    # Check if user is a seller
    if hasattr(user, 'profile') and user.profile.role == 'seller':
        # Handle form submission for adding medicine
        if request.method == 'POST':
            medicine_id = request.POST.get('medicine_id')
            new_medicine_name = request.POST.get('new_medicine_name')
            description = request.POST.get('description', '')
            requires_prescription = request.POST.get('requires_prescription') == 'on'
            stock = request.POST.get('stock', 0)
            price = request.POST.get('price', 0)
            picture = request.FILES.get('picture')
            category = request.POST.get('category', 'Body Pain')
            
            try:
                if new_medicine_name:
                    # Add a new medicine
                    medicine = Medicine.objects.create(
                        name=new_medicine_name,
                        description=description,
                        requires_prescription=requires_prescription,
                        seller=user,
                        stock=stock,
                        price=price,
                        picture=picture,
                        cure_to=category
                    )
                    messages.success(request, f'Medicine "{new_medicine_name}" added successfully!')
                elif medicine_id:
                    # Update existing medicine
                    medicine = Medicine.objects.get(id=medicine_id, seller=user)
                    medicine.stock += int(stock)
                    medicine.price = price
                    medicine.save()
                    messages.success(request, f'Stock updated for "{medicine.name}" successfully!')
                else:
                    messages.error(request, 'Please select an existing medicine or enter a new medicine name.')
                    all_medicines = Medicine.objects.filter(seller=user)
                    
                    # Prepare medicine data for JavaScript
                    medicine_data = {}
                    for med in all_medicines:
                        medicine_data[str(med.id)] = {
                            'name': med.name,
                            'description': med.description,
                            'category': med.cure_to,
                            'price': str(med.price),
                            'requires_prescription': med.requires_prescription,
                            'stock': str(med.stock)
                        }
                    
                    return render(request, 'Hospital/seller_home.html', {
                        'all_medicines': all_medicines, 
                        'cure_choices': Medicine.CURE_CHOICES,
                        'form_data': request.POST,
                        'selected_medicine_id': medicine_id,
                        'medicine_data_json': medicine_data
                    })
                
                # Redirect to prevent form resubmission
                return redirect('home')
                
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
                all_medicines = Medicine.objects.filter(seller=user)
                
                # Prepare medicine data for JavaScript
                medicine_data = {}
                for med in all_medicines:
                    medicine_data[str(med.id)] = {
                        'name': med.name,
                        'description': med.description,
                        'category': med.cure_to,
                        'price': str(med.price),
                        'requires_prescription': med.requires_prescription,
                        'stock': str(med.stock)
                    }
                
                return render(request, 'Hospital/seller_home.html', {
                    'all_medicines': all_medicines, 
                    'cure_choices': Medicine.CURE_CHOICES,
                    'form_data': request.POST,
                    'selected_medicine_id': medicine_id,
                    'medicine_data_json': medicine_data
                })
        
        # GET request - show form
        all_medicines = Medicine.objects.filter(seller=user)
        
        # Prepare medicine data for JavaScript
        medicine_data = {}
        for med in all_medicines:
            medicine_data[str(med.id)] = {
                'name': med.name,
                'description': med.description,
                'category': med.cure_to,
                'price': str(med.price),
                'requires_prescription': med.requires_prescription,
                'stock': str(med.stock)
            }
        
        return render(request, 'Hospital/seller_home.html', {
            'all_medicines': all_medicines, 
            'cure_choices': Medicine.CURE_CHOICES,
            'medicine_data_json': medicine_data
        })

    states = State.objects.all()
    state_filter = request.GET.get('state')
    list = range(1, 6)
    if state_filter and state_filter != "All":
        hospitals = Hospital.objects.filter(state=state_filter)
    else:
        hospitals = Hospital.objects.all()
    paginator = Paginator(hospitals, 8)  # 8 items per page
    page = request.GET.get('page')
    hospitals = paginator.get_page(page)
    nearest_hospitals = []
    if request.method == 'POST':
        user_latitude = request.POST.get('user_latitude')
        user_longitude = request.POST.get('user_longitude')
        user_coords = [float(user_latitude), float(user_longitude)]
        hospitals = Hospital.objects.all()
        for hospital in hospitals:
            result = geocode_hospitals(hospital.location)
            if result[0] is not None and result[1] is not None:
                hospital_latitude, hospital_longitude = result
                hospital_coords = (hospital_latitude, hospital_longitude)
                distance = geodesic(user_coords, hospital_coords).kilometers
                nearest_hospitals.append((hospital, distance))
        nearest_hospitals = sorted(nearest_hospitals, key=lambda x: x[1])[:5]
        print(nearest_hospitals)

    past_appointments = Appointment.objects.filter(user=request.user)
    departments = set(appointment.doctor.department for appointment in past_appointments)
    shuffled_doctors = Doctor.objects.filter(department__in=departments).order_by('?')[:5]
    top_doctors = Doctor.objects.annotate(avg_rating=Avg("reviews__rating")).annotate(review_count=Count("reviews")).filter(avg_rating__gte=4).order_by('-avg_rating')
    return render(request, 'Hospital/home.html', {"hospitals": hospitals, "states": states, "list": list, 'nearest_hospitals': nearest_hospitals, 'doctors': shuffled_doctors, 'top_doctors': top_doctors})

def view_doctors(request):
  doctor_categories = [
  "Cardiology",
  "Orthopedics",
  "Dermatology",
  "Pediatrics",
  "Obstetrics and Gynecology",
  "Neurology",
  "Ophthalmology",
  "ENT (Ear, Nose, and Throat)"
  ]
  doctors=Doctor.objects.all()
  doctor_categories = [category for category in doctor_categories]
  department_filter = request.GET.get('department')
  if department_filter and department_filter != "All":
    doctors = doctors.filter(department=department_filter)
  return render(request,'Hospital/view_doctors.html',{'doctors':doctors,'doctor_categories':doctor_categories})

def view_all_doctors(request,hospital_id):
  noMatchFound=True
  hospital=get_object_or_404(Hospital,pk=hospital_id)
  doctors=hospital.doctors.all()
  timings=Timing.objects.filter(doctor__in=doctors,hospital=hospital)
  return render(request,"Hospital/view_all_doctors.html", {'hospital': hospital, 'doctors': doctors,'timings':timings,'hospital_id':hospital_id,'noMatchFound': noMatchFound})

def add_review(request,doctor_id):
  doctor=get_object_or_404(Doctor,id=doctor_id)
  
  # Check if user has previously consulted with this doctor
  has_consulted = Appointment.objects.filter(
    user=request.user,
    doctor=doctor,
    status=False  # Past appointments (status=False means completed/cancelled appointments)
  ).exists()
  
  if not has_consulted:
    messages.error(request, "You can only give feedback for doctors you have previously consulted with.")
    return redirect('doctor_profile',doctor.id)
  
  if request.method=='POST':
    rating=request.POST.get('rating')
    comment = request.POST.get('comment')
    if not rating or int(rating) < 1 or int(rating) > 5:
      messages.error(request, 'Invalid rating. Please enter a rating between 1 and 5.')
    else:
      review=Review(doctor=doctor,user=request.user,rating=rating,comment=comment)
      review.save()        
      messages.success(request, 'Review added successfully.')
      return redirect('doctor_profile',doctor.id)
  return render(request,'Hospital/add_review.html',{'doctor':doctor})

  

def update_doctor_status(doctor):
  today=date.today()+timedelta(hours=24)
  appointment_count =Appointment.objects.filter(
    doctor=doctor,
    appointment_date=today,
  ).count()
  if appointment_count >= 2:
        doctor.status = False  
        doctor.save()

def doctor_profile(request, doctor_id=None):
    user = request.user
    if doctor_id is None and user.is_authenticated:
        if Doctor.objects.filter(user_id=user.id).exists():
            doctor = Doctor.objects.get(user_id=user.id)
            reviews = Review.objects.filter(doctor=doctor).order_by('-rating')
            list_range = range(1, 6)
            top_review_count = len(reviews) // 2 + 1
            top_reviews = reviews[:top_review_count]
            update_doctor_status(doctor)
            today = date.today()
            on_leave = DoctorLeave.objects.filter(doctor=doctor, start_date__lte=today, end_date__gte=today).exists()
            doctor_status = 'Unavailable' if on_leave else 'Available'
            
            # Check if user has previously consulted with this doctor
            has_consulted = Appointment.objects.filter(
                user=user,
                doctor=doctor,
                status=False  # Past appointments
            ).exists()
            
            if request.method == 'POST':
                review_id_to_delete = request.POST.get('review_id_to_delete')
                if review_id_to_delete:
                    if Review.objects.filter(pk=review_id_to_delete).exists():
                        review = get_object_or_404(Review, pk=review_id_to_delete)
                        review.delete()
            return render(request, 'Hospital/view_profile.html', {
                'doctor': doctor, 
                'top_reviews': top_reviews, 
                'list': list_range, 
                'doctor_status': doctor_status,
                'has_consulted': has_consulted
            })
        else:
            return render(request, 'Hospital/view_profile.html', {'doctor': None})
    else:
        doctor = get_object_or_404(Doctor, id=doctor_id)
        reviews = Review.objects.filter(doctor=doctor).order_by('-rating')
        list_range = range(1, 6)
        top_review_count = len(reviews) // 2 + 1
        top_reviews = reviews[:top_review_count]
        update_doctor_status(doctor)
        today = date.today()
        on_leave = DoctorLeave.objects.filter(doctor=doctor, start_date__lte=today, end_date__gte=today).exists()
        doctor_status = 'Unavailable' if on_leave else 'Available'
        
        # Check if user has previously consulted with this doctor
        has_consulted = Appointment.objects.filter(
            user=user,
            doctor=doctor,
            status=False  # Past appointments
        ).exists()
        
        if request.method == 'POST':
            review_id_to_delete = request.POST.get('review_id_to_delete')
            if review_id_to_delete:
                if Review.objects.filter(pk=review_id_to_delete).exists():
                    review = get_object_or_404(Review, pk=review_id_to_delete)
                    review.delete()
        return render(request, 'Hospital/view_profile.html', {
            'doctor': doctor, 
            'top_reviews': top_reviews, 
            'list': list_range, 
            'doctor_status': doctor_status,
            'has_consulted': has_consulted
        })
  
def is_doctor_available(doctor, date):
    return not DoctorLeave.objects.filter(doctor=doctor, start_date__lte=date, end_date__gte=date).exists()

def doctor_appointments(request,hospital_id,doctor_id):
  doctor=Doctor.objects.get(id=doctor_id)
  hospital=Hospital.objects.get(id=hospital_id)
  doctor_json = serializers.serialize('json', [doctor])
  hospital_json = serializers.serialize('json', [hospital])
  if request.method=='POST':
    appointment_date_str = request.POST.get('appointment_date')
    appointment_date = datetime.strptime(appointment_date_str, '%Y-%m-%d').date()  
    time_str=request.POST.get('end_time')
    time = datetime.strptime(time_str,'%H:%M:%S').time()
    notes=request.POST.get('notes')
    user=request.user
    # Prevent booking if doctor is on leave
    if not is_doctor_available(doctor, appointment_date):
        messages.error(request, 'Doctor is unavailable on the selected date due to leave. Please choose another date.')
        return render(request,'Hospital/book_appointment.html',{'doctor':doctor,'hospital':hospital,'doctor_json': doctor_json,'hospital_json': hospital_json})
    
    # Check capacity before booking
    try:
        appointment=Appointment(
          user=user,
          doctor=doctor,
          hospital=hospital,
          appointment_date=appointment_date,
          time=time,
          notes=notes
        )
        appointment.full_clean()  # This will trigger the clean method with capacity validation
        appointment.save()
        messages.success(request, 'Appointment booked successfully.')
        return redirect('/dashboard/me/')
    except ValidationError as e:
        # Extract the error message properly
        if hasattr(e, 'message_dict') and '__all__' in e.message_dict:
            error_message = e.message_dict['__all__'][0]
        elif hasattr(e, 'message_dict'):
            error_message = '; '.join([msg[0] if isinstance(msg, list) else str(msg) for msg in e.message_dict.values()])
        else:
            error_message = str(e)
        messages.error(request, error_message)
        return render(request,'Hospital/book_appointment.html',{'doctor':doctor,'hospital':hospital,'doctor_json': doctor_json,'hospital_json': hospital_json})
    
  return render(request,'Hospital/book_appointment.html',{'doctor':doctor,'hospital':hospital,'doctor_json': doctor_json,'hospital_json': hospital_json})

def get_available_timings(request):
  if request.method == 'GET':
    selected_date_str= request.GET.get('selected_date')
    hospital=request.GET.get('hospital')
    doctor=request.GET.get('doctor')
    selected_date=datetime.strptime(selected_date_str,'%a %b %d %Y %H:%M:%S GMT%z (India Standard Time)')
    day_of_week = selected_date.strftime("%A")
    timings = Timing.objects.filter(day_of_week=day_of_week,doctor__id=doctor,hospital__name=hospital)
    
    available_timings = []
    for timing in timings:
      available_capacity = timing.get_available_capacity(selected_date.date())
      max_capacity = timing.max_capacity
      
      # Check if user already has an appointment in this slot
      user_existing_appointment = Appointment.objects.filter(
        user=request.user,
        doctor__id=doctor,
        hospital__name=hospital,
        appointment_date=selected_date.date(),
        time__gte=timing.start_time,
        time__lt=timing.end_time,
        status=True
      ).first()
      
      # Check if user has any appointment with this doctor on the same day
      user_same_day_appointment = Appointment.objects.filter(
        user=request.user,
        doctor__id=doctor,
        appointment_date=selected_date.date(),
        status=True
      ).exists()
      
      # Determine slot status
      slot_status = 'available'
      if user_existing_appointment:
        slot_status = 'already_booked'
      elif available_capacity <= 0:
        slot_status = 'fully_booked'
      elif user_same_day_appointment:
        slot_status = 'same_day_booking'
      
      available_timings.append({
        'start_time': timing.start_time.strftime('%H:%M:%S'),
        'end_time': timing.end_time.strftime('%H:%M:%S'),
        'available_capacity': available_capacity,
        'max_capacity': max_capacity,
        'remaining_slots': available_capacity,
        'slot_status': slot_status,
        'already_booked_by_user': user_existing_appointment is not None,
        'user_same_day_appointment': user_same_day_appointment,
        'time_range_display': f"{timing.start_time.strftime('%H:%M')} - {timing.end_time.strftime('%H:%M')}"
      })
    
    return JsonResponse(available_timings, safe=False)
  
def dashboard(request):
    user = request.user
    today = date.today()
    now = datetime.now()
    is_doctor = Doctor.objects.filter(user_id=user.id).exists()
    doctor_status = None
    if is_doctor:
        doctor = Doctor.objects.get(user_id=user.id)
        on_leave = DoctorLeave.objects.filter(doctor=doctor, start_date__lte=today, end_date__gte=today).exists()
        doctor_status = 'Unavailable' if on_leave else 'Available'
        upcoming_appointments = Appointment.objects.filter(
            Q(doctor=doctor, appointment_date=today, time__gt=now.time()) |
            Q(doctor=doctor, appointment_date__gt=today)
        )
        past_appointments = Appointment.objects.filter(doctor=doctor, appointment_date__lt=today)
        return render(request, 'Hospital/dashboard.html', {
            'upcoming_appointments': upcoming_appointments,
            'past_appointments': past_appointments,
            'is_doctor': True,
            'doctor_status': doctor_status
        })
    else:
        upcoming_appointments = Appointment.objects.filter(
            Q(user=user, appointment_date=today, time__gt=now.time()) |
            Q(user=user, appointment_date__gt=today)
        )
        past_appointments = Appointment.objects.filter(user=user, appointment_date__lt=today)
        # Get medicine orders for the user
        medicine_orders = MedicineOrder.objects.filter(user=user).order_by('-order_date')
        # Get test orders for the user, separated into upcoming and past
        upcoming_test_orders = TestOrder.objects.filter(user=user, test_date__gte=today).order_by('test_date', 'test_time')
        past_test_orders = TestOrder.objects.filter(user=user, test_date__lt=today).order_by('-test_date', '-test_time')
        return render(request, 'Hospital/dashboard.html', {
            'upcoming_appointments': upcoming_appointments,
            'past_appointments': past_appointments,
            'medicine_orders': medicine_orders,
            'upcoming_test_orders': upcoming_test_orders,
            'past_test_orders': past_test_orders,
            'is_doctor': False
        })

def cancel_appointment(request,appointment_id):
  try:
    appointment=Appointment.objects.get(id=appointment_id)
    appointment.delete()
    messages.success(request, 'Appointment canceled successfully.')
  except Appointment.DoesNotExist:
      messages.error(request, 'Appointment not found.')
  return redirect('user_dashboard')

def reschedule_appointment(request, appointment_id):
    try:
        appointment = Appointment.objects.get(id=appointment_id)
        doctor_json = serializers.serialize('json', [appointment.doctor])
        hospital_json = serializers.serialize('json', [appointment.hospital])
        if request.method == 'POST':
            new_date_str = request.POST.get('new_date')
            new_time_str = request.POST.get('new_time')
            new_date = datetime.strptime(new_date_str, '%Y-%m-%d').date()
            new_time = datetime.strptime(new_time_str, '%H:%M:%S').time()
            appointment.appointment_date = new_date
            appointment.time = new_time
            try:
                appointment.full_clean()  # This will trigger capacity validation
                appointment.save()  
                messages.success(request, 'Appointment rescheduled successfully.')
                return redirect('user_dashboard')
            except ValidationError as e:
                # Extract the error message properly
                if hasattr(e, 'message_dict') and '__all__' in e.message_dict:
                    error_message = e.message_dict['__all__'][0]
                elif hasattr(e, 'message_dict'):
                    error_message = '; '.join([msg[0] if isinstance(msg, list) else str(msg) for msg in e.message_dict.values()])
                else:
                    error_message = str(e)
                messages.error(request, error_message)
                return render(request, 'Hospital/reschedule_form.html', {'appointment': appointment,'doctor_json':doctor_json,'hospital_json':hospital_json})
        else:
            return render(request, 'Hospital/reschedule_form.html', {'appointment': appointment,'doctor_json':doctor_json,'hospital_json':hospital_json})
    except Appointment.DoesNotExist:
        messages.error(request, 'Appointment not found.')
        return redirect('user_dashboard')

def medicines_page(request):
    cure_to_filter = request.GET.get('cure_to', '')
    medicines = Medicine.objects.all()
    if cure_to_filter:
        medicines = medicines.filter(cure_to=cure_to_filter)
    cure_choices = Medicine.CURE_CHOICES
    return render(request, 'Hospital/medicines.html', {
        'medicines': medicines,
        'cure_choices': cure_choices,
        'selected_cure': cure_to_filter
    })
def tests_page(request):
    test_types = TestType.objects.all()
    return render(request, 'Hospital/tests.html', {'test_types': test_types})

def add_prescription(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    medicines = Medicine.objects.all()
    if request.method == 'POST':
        medicine_ids = request.POST.getlist('medicine')
        dosages = request.POST.getlist('dosage')
        dosage_units = request.POST.getlist('dosage_unit')
        num_days_list = request.POST.getlist('num_days')
        frequencies = request.POST.getlist('frequency')
        food_relations = request.POST.getlist('food_relation')
        diagnosis = request.POST.get('diagnosis', '')
        with transaction.atomic():
            Prescription.objects.filter(appointment=appointment).delete()
            prescription = Prescription.objects.create(appointment=appointment, diagnosis=diagnosis)
            for i in range(len(medicine_ids)):
                medicine_obj = Medicine.objects.get(id=medicine_ids[i])
                MedicineEntry.objects.create(
                    prescription=prescription,
                    medicine=medicine_obj,
                    dosage=dosages[i],
                    dosage_unit=dosage_units[i],
                    num_days=num_days_list[i],
                    frequency=frequencies[i],
                    food_relation=food_relations[i]
                )
        return JsonResponse({'success': True, 'message': 'Prescription sent to patient.'})
    return render(request, 'Hospital/prescription_form.html', {'appointment': appointment, 'medicines': medicines})

@require_GET
def get_prescription_details(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    if request.user != appointment.user:
        raise PermissionDenied("You are not authorized to view this prescription.")
    try:
        prescription = appointment.prescription
    except Prescription.DoesNotExist:
        return JsonResponse({"success": False, "error": "No prescription found for this appointment."}, status=404)
    medicines = [
        {
            "id": entry.medicine.id,
            "name": entry.medicine.name,
            "dosage": entry.dosage,
            "dosage_unit": entry.dosage_unit,
            "num_days": entry.num_days,
            "frequency": entry.frequency,
            "food_relation": entry.food_relation,
        }
        for entry in prescription.medicines.all()
    ]
    data = {
        "success": True,
        "diagnosis": prescription.diagnosis,
        "medicines": medicines,
        "doctor_notes": appointment.notes,
        "doctor_name": appointment.doctor.get_name,
    }
    return JsonResponse(data)

@require_GET
@user_passes_test(is_authenticated, login_url='/login/')
def check_existing_appointments(request):
    """Check for existing appointments on a specific date"""
    appointment_date_str = request.GET.get('appointment_date')
    if not appointment_date_str:
        return JsonResponse({"existing_appointments": []})
    
    try:
        appointment_date = datetime.strptime(appointment_date_str, '%Y-%m-%d').date()
        existing_appointments = Appointment.objects.filter(
            user=request.user,
            appointment_date=appointment_date,
            status=True
        ).select_related('doctor', 'hospital')
        
        appointments_data = []
        for appointment in existing_appointments:
            appointments_data.append({
                'id': appointment.id,
                'time': appointment.time.strftime('%H:%M'),
                'doctor_name': appointment.doctor.get_name,
                'hospital_name': appointment.hospital.name,
                'notes': appointment.notes
            })
        
        return JsonResponse({
            "existing_appointments": appointments_data
        })
    except ValueError:
        return JsonResponse({"existing_appointments": []})

@require_POST
@user_passes_test(lambda u: u.is_authenticated and hasattr(u, 'first_name') and hasattr(u, 'last_name'), login_url='/login/')
def doctor_take_leave(request):
    user = request.user
    # Find doctor by user name (adjust if you have a better relation)
    doctor = Doctor.objects.filter(user=user).first()
    if not doctor:
        return redirect('user_dashboard')
    leave_range = request.POST.get('leave_dates', '')
    if ' to ' in leave_range:
        start_str, end_str = leave_range.split(' to ')
    elif ' - ' in leave_range:
        start_str, end_str = leave_range.split(' - ')
    else:
        start_str = end_str = leave_range
    try:
        start_date = datetime.strptime(start_str.strip(), '%Y-%m-%d').date()
        end_date = datetime.strptime(end_str.strip(), '%Y-%m-%d').date()
    except Exception:
        messages.error(request, 'Invalid date format.')
        return redirect('user_dashboard')
    DoctorLeave.objects.create(doctor=doctor, start_date=start_date, end_date=end_date)
    messages.success(request, f'Leave applied from {start_date} to {end_date}.')
    return redirect('user_dashboard')

@require_POST
@login_required
def toggle_video_online(request):
    # Find the doctor for the logged-in user
    doctor = Doctor.objects.filter(user=request.user).first()
    if doctor is None:
        return JsonResponse({'error': 'Doctor not found.'}, status=404)
    doctor.video_online = not doctor.video_online
    doctor.save()
    # Broadcast the new online doctor count
    channel_layer = get_channel_layer()
    count = Doctor.objects.filter(video_online=True).count()
    async_to_sync(channel_layer.group_send)(
        'online_doctor_count',
        {
            'type': 'doctor_count_update',
            'count': count
        }
    )
    return JsonResponse({'online': doctor.video_online})

@csrf_exempt
@login_required
def submit_symptoms(request):
    if request.method == "POST":
        appointment = VideoAppointment.objects.create(
            patient=request.user
        )
        return JsonResponse({"success": True, "room_id": appointment.id})
    return JsonResponse({"success": False}, status=400)

@login_required
def video_consultation(request, room_id=None):
    appointment = None
    if room_id:
        appointment = VideoAppointment.objects.filter(id=room_id).first()
    return render(request, 'Hospital/video_consultation.html', {
        'room_id': room_id,
        'appointment': appointment,
    })

@login_required
def start_video_consultation(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    # Only allow if doctor is online (optional: add check)
    video_appt = VideoAppointment.objects.create(
        doctor=doctor,
        patient=request.user,
        status='pending'
    )
    room_name = str(video_appt.id)
    return redirect(reverse('video_consultation_room', kwargs={'room_name': room_name}))

@require_GET
def online_doctor_count(request):
    count = Doctor.objects.filter(video_online=True).count()
    return JsonResponse({'count': count})

@require_GET
def doctor_video_online_state(request):
    if not request.user.is_authenticated:
        return JsonResponse({'online': False})
    doctor = Doctor.objects.filter(user=request.user).first()
    if doctor is None:
        return JsonResponse({'online': False})
    return JsonResponse({'online': doctor.video_online})

def view_hospitals_for_testtype(request, testtype_id):
    from django.shortcuts import get_object_or_404
    test_type = get_object_or_404(TestType, id=testtype_id)
    tests = test_type.hospital_tests.select_related('hospital').filter(available=True)

    user_lat = request.session.get('user_lat') or request.GET.get('user_lat')
    user_lng = request.session.get('user_lng') or request.GET.get('user_lng')
    if not user_lat or not user_lng:
        return render(request, 'Hospital/hospitals_for_testtype.html', {
            'test_type': test_type,
            'tests': [],
            'need_location': True
        })
    try:
        user_lat = float(user_lat)
        user_lng = float(user_lng)
    except Exception:
        return render(request, 'Hospital/hospitals_for_testtype.html', {
            'test_type': test_type,
            'tests': [],
            'need_location': True
        })

    hospital_test_list = []
    for test in tests:
        hospital = test.hospital
        if hospital.latitude is not None and hospital.longitude is not None:
            distance_km = geodesic((user_lat, user_lng), (hospital.latitude, hospital.longitude)).km
            if distance_km <= 50:
                hospital_test_list.append({
                    'test': test,
                    'hospital': hospital,
                    'price': test.price,
                    'distance': round(distance_km, 2)
                })

    hospital_test_list = heapq.nsmallest(10, hospital_test_list, key=lambda x: x['distance'])

    sort_by = request.GET.get('sort', 'distance')
    if sort_by == 'price':
        hospital_test_list.sort(key=lambda x: x['price'])
    else:
        hospital_test_list.sort(key=lambda x: x['distance'])

    return render(request, 'Hospital/hospitals_for_testtype.html', {
        'test_type': test_type,
        'tests': hospital_test_list,
        'need_location': False,
        'sort_by': sort_by
    })
def add_to_cart(request, test_id):
    from django.shortcuts import get_object_or_404, redirect
    test = get_object_or_404(Test, id=test_id)
    cart = request.session.get('cart', None)
    if cart:
        if cart['hospital_id'] != test.hospital.id:
            if request.POST.get('confirm_replace') == 'yes':
                cart = {'hospital_id': test.hospital.id, 'tests': [test.id]}
                messages.success(request, f"Cart replaced with test from {test.hospital.name}.")
            else:
                return render(request, 'Hospital/confirm_replace_cart.html', {
                    'current_hospital': cart['hospital_id'],
                    'new_hospital': test.hospital,
                    'test': test
                })
        else:
            if test.id not in cart['tests']:
                cart['tests'].append(test.id)
                messages.success(request, f"Test added to cart.")
            else:
                messages.info(request, f"Test already in cart.")
    else:
        cart = {'hospital_id': test.hospital.id, 'tests': [test.id]}
        messages.success(request, f"Test added to cart.")
    request.session['cart'] = cart
    # Always redirect to the tests page
    return redirect('tests_page')

def add_medicine_to_cart(request, medicine_id):
    from django.shortcuts import get_object_or_404, redirect
    medicine = get_object_or_404(Medicine, id=medicine_id)
    quantity = int(request.POST.get('quantity', 1))
    
    # Validate quantity
    if quantity <= 0:
        messages.error(request, "Quantity must be greater than 0.")
        return redirect('medicines')
    
    if quantity > medicine.stock:
        messages.error(request, f"Only {medicine.stock} items available in stock.")
        return redirect('medicines')
    
    # Get or initialize medicine cart
    medicine_cart = request.session.get('medicine_cart', {})
    
    # Check if medicine already in cart
    if str(medicine_id) in medicine_cart:
        # Update quantity if medicine already exists
        current_quantity = medicine_cart[str(medicine_id)]['quantity']
        new_quantity = current_quantity + quantity
        
        if new_quantity > medicine.stock:
            messages.error(request, f"Cannot add {quantity} more items. Total quantity would exceed available stock ({medicine.stock}).")
            return redirect('medicines')
        
        medicine_cart[str(medicine_id)]['quantity'] = new_quantity
        messages.success(request, f"Updated quantity for {medicine.name} in cart.")
    else:
        # Add new medicine to cart
        medicine_cart[str(medicine_id)] = {
          'name': medicine.name,
          'price': float(medicine.price),
          'quantity': quantity,
          'seller_id': medicine.seller.id,
          'requires_prescription': medicine.requires_prescription
        }
        messages.success(request, f"{quantity} x {medicine.name} added to cart.")
    
    request.session['medicine_cart'] = medicine_cart
    return redirect('medicines')

def medicine_cart_checkout(request):
    """Display medicine cart checkout page"""
    medicine_cart = request.session.get('medicine_cart', {})
    
    if not medicine_cart:
        messages.warning(request, "Your cart is empty.")
        return redirect('medicines')
    
    # Get medicine details for cart items
    cart_items = []
    total_amount = 0
    
    for medicine_id, item_data in medicine_cart.items():
        try:
            medicine = Medicine.objects.get(id=medicine_id)
            item_total = item_data['price'] * item_data['quantity']
            total_amount += item_total
            
            cart_items.append({
                'medicine': medicine,
                'quantity': item_data['quantity'],
                'price': item_data['price'],
                'total': item_total,
                'requires_prescription': item_data['requires_prescription']
            })
        except Medicine.DoesNotExist:
            # Remove invalid medicine from cart
            del medicine_cart[medicine_id]
            continue
    
    # Update session cart (remove invalid items)
    request.session['medicine_cart'] = medicine_cart
    
    # Calculate expected delivery date (3-5 business days)
    from datetime import date, timedelta
    delivery_date = date.today() + timedelta(days=4)  # 4 days from now
    
    # Get user's delivery address and pincode
    user_address = request.user.profile.address if hasattr(request.user, 'profile') else "123 Main Street, Apartment 4B, City Center, New Delhi"
    user_pincode = request.user.profile.pincode if hasattr(request.user, 'profile') else "110001"
    
    context = {
        'cart_items': cart_items,
        'total_amount': total_amount,
        'expected_delivery_date': delivery_date,
        'delivery_address': user_address,
        'delivery_pincode': user_pincode,
    }
    
    return render(request, 'Hospital/medicine_checkout.html', context)

def process_medicine_payment(request):
    """Process medicine order payment and create order (restored to original logic)"""
    if request.method != 'POST':
        return redirect('medicine_cart_checkout')
    
    medicine_cart = request.session.get('medicine_cart', {})
    
    if not medicine_cart:
        messages.error(request, "Your cart is empty.")
        return redirect('medicines')
    
    # Get delivery address and pincode from form
    delivery_address = request.POST.get('delivery_address', '')
    delivery_pincode = request.POST.get('delivery_pincode', '')
    if not delivery_address:
        messages.error(request, "Please provide a valid delivery address.")
        return redirect('medicine_cart_checkout')
    
    if not delivery_pincode:
        messages.error(request, "Please provide a valid pincode.")
        return redirect('medicine_cart_checkout')
    
    try:
        with transaction.atomic():
            # Calculate total amount
            total_amount = 0
            cart_items = []
            
            for medicine_id, item_data in medicine_cart.items():
                medicine = Medicine.objects.get(id=medicine_id)
                item_total = item_data['price'] * item_data['quantity']
                total_amount += item_total
                
                cart_items.append({
                    'medicine': medicine,
                    'quantity': item_data['quantity'],
                    'price': item_data['price'],
                    'total': item_total
                })
            
            # Calculate expected delivery date
            from datetime import date, timedelta
            delivery_date = date.today() + timedelta(days=4)
            
            # Create medicine order
            order = MedicineOrder.objects.create(
                user=request.user,
                expected_delivery_date=delivery_date,
                delivery_address=delivery_address,
                delivery_pincode=delivery_pincode,
                total_amount=total_amount,
                payment_status=True  # Mark as paid
            )
            
            # Create order items and update stock
            for item in cart_items:
                MedicineOrderItem.objects.create(
                    order=order,
                    medicine=item['medicine'],
                    quantity=item['quantity'],
                    price_per_unit=item['price'],
                    total_price=item['total']
                )
                
                # Update medicine stock
                item['medicine'].stock -= item['quantity']
                item['medicine'].save()
            
            # Clear cart
            request.session['medicine_cart'] = {}
            
            messages.success(request, f"Order placed successfully! Order #: {order.id}")
            return redirect('user_dashboard')
            
    except Exception as e:
        messages.error(request, f"Error processing order: {str(e)}")
        return redirect('medicine_cart_checkout')

def update_order_status(request, order_id):
    """Update order status (for admin/seller use)"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to update order status.")
        return redirect('user_dashboard')
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(MedicineOrder.STATUS_CHOICES):
            order = get_object_or_404(MedicineOrder, id=order_id)
            order.status = new_status
            order.save()
            messages.success(request, f"Order #{order_id} status updated to {new_status}.")
    
    return redirect('user_dashboard')

def test_cart_checkout(request):
    """Display test cart checkout page with date and slot selection"""
    cart = request.session.get('cart', {})
    
    if not cart or 'tests' not in cart or not cart['tests']:
        messages.warning(request, "Your test cart is empty.")
        return redirect('tests_page')
    
    try:
        hospital = Hospital.objects.get(id=cart['hospital_id'])
    except Hospital.DoesNotExist:
        messages.error(request, "Selected hospital not found.")
        request.session['cart'] = {}
        return redirect('tests_page')
    
    # Get test details for cart items
    cart_items = []
    total_amount = 0
    all_allowed_slots = None
    slot_label_map = dict(TestType.SLOT_CHOICES)
    slot_conflicts = []
    
    for test_id in cart['tests']:
        try:
            test = Test.objects.get(id=test_id, hospital=hospital, available=True)
            total_amount += test.price
            cart_items.append({'test': test, 'price': test.price})
            allowed_slots = set(test.test_type.get_allowed_slots())
            if all_allowed_slots is None:
                all_allowed_slots = allowed_slots
            else:
                all_allowed_slots = all_allowed_slots & allowed_slots
            if not allowed_slots:
                slot_conflicts.append(f"{test.test_type.name}: All slots allowed")
            else:
                slot_conflicts.append(f"{test.test_type.name}: {', '.join([slot_label_map[s] for s in allowed_slots])}")
        except Test.DoesNotExist:
            cart['tests'].remove(test_id)
            continue
    request.session['cart'] = cart
    if not cart_items:
        messages.warning(request, "No valid tests in your cart.")
        return redirect('tests_page')
    # If no intersection, show error and list allowed slots for each test
    if not all_allowed_slots:
        messages.error(request, "No common time slot is available for all selected tests. Please review your selection.\n" + '\n'.join(slot_conflicts))
        return redirect('tests_page')
    # Only show slots in the intersection
    time_slots = [(slot, slot_label_map[slot]) for slot in all_allowed_slots]
    # Get available dates (next 30 days, excluding Sundays)
    from datetime import date, timedelta
    available_dates = []
    current_date = date.today()
    for i in range(1, 31):
        check_date = current_date + timedelta(days=i)
        if check_date.weekday() != 6:
            available_dates.append(check_date)
    context = {
        'cart_items': cart_items,
        'total_amount': total_amount,
        'hospital': hospital,
        'available_dates': available_dates,
        'time_slots': time_slots,
    }
    return render(request, 'Hospital/test_checkout.html', context)


def process_test_payment(request):
    """Process test order payment and create order"""
    if request.method != 'POST':
        return redirect('test_cart_checkout')
    cart = request.session.get('cart', {})
    if not cart or 'tests' not in cart or not cart['tests']:
        messages.error(request, "Your test cart is empty.")
        return redirect('tests_page')
    test_date_str = request.POST.get('test_date', '')
    test_time_str = request.POST.get('test_time', '')
    notes = request.POST.get('notes', '')
    if not test_date_str or not test_time_str:
        messages.error(request, "Please select a date and time for your test.")
        return redirect('test_cart_checkout')
    try:
        test_date = datetime.strptime(test_date_str, '%Y-%m-%d').date()
        test_time = datetime.strptime(test_time_str, '%H:%M').time()
    except ValueError:
        messages.error(request, "Invalid date or time format.")
        return redirect('test_cart_checkout')
    current_datetime = datetime.now()
    test_datetime = datetime.combine(test_date, test_time)
    if test_datetime <= current_datetime:
        messages.error(request, "Cannot book tests for past dates or times.")
        return redirect('test_cart_checkout')
    # Validate slot intersection again
    try:
        hospital = Hospital.objects.get(id=cart['hospital_id'])
    except Hospital.DoesNotExist:
        messages.error(request, "Selected hospital not found.")
        return redirect('tests_page')
    slot_label_map = dict(TestType.SLOT_CHOICES)
    selected_slot = None
    for slot, label in TestType.SLOT_CHOICES:
        if slot.startswith(test_time.strftime('%H:%M')):
            selected_slot = slot
            break
    if not selected_slot:
        messages.error(request, "Selected time does not match any valid slot.")
        return redirect('test_cart_checkout')
    all_allowed_slots = None
    slot_conflicts = []
    cart_items = []
    total_amount = 0
    for test_id in cart['tests']:
        test = Test.objects.get(id=test_id, hospital=hospital, available=True)
        allowed_slots = set(test.test_type.get_allowed_slots())
        if all_allowed_slots is None:
            all_allowed_slots = allowed_slots
        else:
            all_allowed_slots = all_allowed_slots & allowed_slots
        cart_items.append(test)
        if not allowed_slots:
            slot_conflicts.append(f"{test.test_type.name}: All slots allowed")
        else:
            slot_conflicts.append(f"{test.test_type.name}: {', '.join([slot_label_map[s] for s in allowed_slots])}")
        total_amount += test.price
    if not all_allowed_slots or selected_slot not in all_allowed_slots:
        messages.error(request, "The selected time slot is not allowed for all selected tests. Please review your selection.\n" + '\n'.join(slot_conflicts))
        return redirect('test_cart_checkout')
    try:
        with transaction.atomic():
            order = TestOrder.objects.create(
                user=request.user,
                hospital=hospital,
                test_date=test_date,
                test_time=test_time,
                total_amount=total_amount,
                payment_status=True,
                notes=notes
            )
            for test in cart_items:
                TestOrderItem.objects.create(
                    order=order,
                    test=test,
                    price=test.price
                )
            request.session['cart'] = {}
            messages.success(request, f"Test order placed successfully! Order #: {order.id}")
            return redirect('user_dashboard')
    except Exception as e:
        messages.error(request, f"Error processing test order: {str(e)}")
        return redirect('test_cart_checkout')

def update_test_order_status(request, order_id):
    """Update test order status (for admin use)"""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to update test order status.")
        return redirect('user_dashboard')
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(TestOrder.STATUS_CHOICES):
            order = get_object_or_404(TestOrder, id=order_id)
            order.status = new_status
            order.save()
            messages.success(request, f"Test Order #{order_id} status updated to {new_status}.")
    
    return redirect('user_dashboard')

def create_test_report(request, order_id):
    order = get_object_or_404(TestOrder, id=order_id)
    # Only allow if no report exists and order belongs to this hospital
    if hasattr(order, 'report'):
        messages.warning(request, 'A report has already been created for this order.')
        return redirect('hospital_admin_home')
    if request.method == 'POST':
        form = TestReportForm(request.POST, request.FILES)
        if form.is_valid():
            report = form.save(commit=False)
            report.order = order
            report.sent_to_patient = True
            report.save()
            # Send report to patient via email (with findings in body, file as attachment if present)
            subject = f"Your Test Report for Order #{order.id}"
            message = f"Dear {order.user.get_full_name() or order.user.username},\n\nHere are your test report findings:\n\nPositive Findings:\n{report.findings_positive}\n\nNegative Findings:\n{report.findings_negative}\n\nBest regards,\n{order.hospital.name}"
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [order.user.email]
            # Send email with or without attachment
            if report.report_file:
                from django.core.mail import EmailMessage
                email = EmailMessage(subject, message, from_email, recipient_list)
                email.attach(report.report_file.name, report.report_file.read(), report.report_file.file.content_type)
                email.send()
            else:
                send_mail(subject, message, from_email, recipient_list)
            messages.success(request, 'Report created and sent to patient successfully!')
            return redirect('hospital_admin_home')
    else:
        form = TestReportForm()
    return render(request, 'Hospital/create_test_report.html', {'form': form, 'order': order})

def hospital_admin_home(request):
    user = request.user
    if not user.is_authenticated or not hasattr(user, 'profile') or user.profile.role != 'hospital_admin':
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("You are not authorized to view this page.")
    mapping = HospitalAdminMapping.objects.filter(user=user).first()
    if not mapping:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("No hospital mapping found for this admin.")
    hospital = mapping.hospital
    tests = hospital.tests.all()
    # Add included_list attribute to each test
    for test in tests:
        if test.test_included:
            test.included_list = test.test_included.split(',')
        else:
            test.included_list = []
    # Fetch booked test orders for this hospital
    booked_orders = hospital.test_orders.filter(status='booked').select_related('user').prefetch_related('items__test')
    # Fetch pending doctor requests for this hospital
    pending_requests = DoctorHospitalRequest.objects.filter(hospital=hospital, is_approved=False).select_related('doctor')
    return render(request, 'Hospital/hospital_admin_home.html', {
        'hospital': hospital,
        'tests': tests,
        'booked_orders': booked_orders,
        'pending_requests': pending_requests,
    })

def add_test_for_hospital(request):
    user = request.user
    if not user.is_authenticated or not hasattr(user, 'profile') or user.profile.role != 'hospital_admin':
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("You are not authorized to add tests.")
    mapping = HospitalAdminMapping.objects.filter(user=user).first()
    if not mapping:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("No hospital mapping found for this admin.")
    hospital = mapping.hospital
    if request.method == 'POST':
        form = AddTestForm(request.POST)
        if form.is_valid():
            test_type = form.cleaned_data['test_type']
            price = form.cleaned_data['price']
            test_included = form.cleaned_data['test_included']
            package_discount = form.cleaned_data['package_discount']
            pre_test_instructions = form.cleaned_data['pre_test_instructions']
            test = Test.objects.create(
                test_type=test_type,
                hospital=hospital,
                price=price,
                available=True,
                test_included=test_included,
                package_discount=package_discount,
                pre_test_instructions=pre_test_instructions
            )
            messages.success(request, f"Test '{test_type.name}' added successfully!")
            return redirect('hospital_admin_home')
    else:
        form = AddTestForm()
    return render(request, 'Hospital/add_test_for_hospital.html', {
        'form': form,
        'hospital': hospital,
    })

@login_required
def approve_doctor_request(request, request_id):
    req = get_object_or_404(DoctorHospitalRequest, id=request_id, is_approved=False)
    # Only allow if this admin manages the hospital
    if not HospitalAdminMapping.objects.filter(user=request.user, hospital=req.hospital).exists():
        return HttpResponseForbidden('You are not authorized to approve this request.')
    req.is_approved = True
    req.save()
    req.doctor.hospitals.add(req.hospital)
    messages.success(request, f'Doctor {req.doctor.get_name} approved for {req.hospital.name}.')
    return redirect('hospital_admin_home')


