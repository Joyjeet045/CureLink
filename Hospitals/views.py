from django.shortcuts import render, get_object_or_404, redirect
from django.core import serializers
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Doctor, Hospital, State, Timing, Review, Appointment
from .constants import doctor_departments
from datetime import datetime, date, timedelta
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from django.views.decorators.csrf import csrf_exempt

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
  
  states=State.objects.all()
  state_filter=request.GET.get('state')
  list=range(1,6)
  if state_filter and state_filter != "All":
    hospitals= Hospital.objects.filter(state=state_filter)
  else:
    hospitals=Hospital.objects.all()
  paginator = Paginator(hospitals, 8)  # 8 items per page
  page = request.GET.get('page')
  hospitals = paginator.get_page(page)
  nearest_hospitals=[]
  if request.method=='POST':
    user_latitude=request.POST.get('user_latitude')
    user_longitude = request.POST.get('user_longitude')
    user_coords=[float(user_latitude),float(user_longitude)]
    hospitals=Hospital.objects.all()
    for hospital in hospitals:
      result=geocode_hospitals(hospital.location)
      if result[0] is not None and result[1] is not None:
        hospital_latitude, hospital_longitude = result
        hospital_coords = (hospital_latitude, hospital_longitude)
        distance=geodesic(user_coords,hospital_coords).kilometers
        nearest_hospitals.append((hospital, distance))
    nearest_hospitals=sorted(nearest_hospitals,key=lambda x:x[1])[:5]
    print(nearest_hospitals)

  past_appointments = Appointment.objects.filter(user=request.user)
  departments = set(appointment.doctor.department for appointment in past_appointments)
  shuffled_doctors = Doctor.objects.filter(department__in=departments).order_by('?')[:5]
  top_doctors=Doctor.objects.annotate(avg_rating=Avg("reviews__rating")).annotate(review_count=Count("reviews")).filter(avg_rating__gte=4).order_by('-avg_rating')
  return render(request,'Hospital/home.html',{"hospitals":hospitals,"states":states,"list":list, 'nearest_hospitals': nearest_hospitals,'doctors':shuffled_doctors,'top_doctors':top_doctors})
@transaction.atomic
@user_passes_test(is_admin,login_url="login")
def add_doctor(request):
  if request.method=='POST':
    first_name = request.POST['first_name']
    last_name = request.POST['last_name']
    mobile=request.POST['mobile']
    profile_pic=request.FILES['profile_pic']
    #select field->dept,hospital
    department=request.POST['department']
    hospitals=request.POST.getlist('hospitals')
    doctor=Doctor.objects.create(
      firstname=first_name,
      lastname=last_name,
      mobile=mobile,
      profile_pic=profile_pic,
      department=department
    )
    doctor.save()
    doctor.hospitals.set(hospitals)
    return redirect("/")
  hospitals_list=Hospital.objects.all()
  state=State.objects.all()
  return render(request,'Hospital/create_doctor.html',{'hospital_ch':hospitals_list,'state_ch':state,'depts':doctor_departments})

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

def doctor_profile(request,doctor_id=None):
  user = request.user
  if doctor_id is None and user.is_authenticated:
    if Doctor.objects.filter(firstname=user.first_name, lastname=user.last_name).exists():
      doctor = Doctor.objects.get(firstname=user.first_name, lastname=user.last_name)
    else:
      return redirect('home')
  else:
    doctor=get_object_or_404(Doctor,id=doctor_id)
  reviews=Review.objects.filter(doctor=doctor).order_by('-rating')
  list=range(1,6)
  top_review_count=len(reviews)//2+1
  top_reviews=reviews[:top_review_count]
  update_doctor_status(doctor)
  if request.method == 'POST':
        review_id_to_delete = request.POST.get('review_id_to_delete')
        if review_id_to_delete:
            if Review.objects.filter(pk=review_id_to_delete).exists():
                review = get_object_or_404(Review, pk=review_id_to_delete)
                review.delete()
  return render(request,'Hospital/view_profile.html',{'doctor':doctor,'top_reviews':top_reviews,'list':list})
  
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
    appointment=Appointment(
      user=user,
      doctor=doctor,
      hospital=hospital,
      appointment_date=appointment_date,
      time=time,
      notes=notes
    )
    appointment.save()
    messages.success(request, 'Appointment booked successfully.')
    return redirect('/dashboard/me/')
  return render(request,'Hospital/book_appointment.html',{'doctor':doctor,'hospital':hospital,'doctor_json': doctor_json,'hospital_json': hospital_json})

def get_available_timings(request):
  if request.method == 'GET':
    selected_date_str= request.GET.get('selected_date')
    hospital=request.GET.get('hospital')
    doctor=request.GET.get('doctor')
    selected_date=datetime.strptime(selected_date_str,'%a %b %d %Y %H:%M:%S GMT%z (India Standard Time)')
    day_of_week = selected_date.strftime("%A")
    available_timings = Timing.objects.filter(day_of_week=day_of_week,doctor__id=doctor,hospital__name=hospital).values('start_time', 'end_time')
    
    return JsonResponse(list(available_timings), safe=False)
  
def dashboard(request):
  user = request.user
  today = date.today()
  now = datetime.now()
  from .models import Doctor
  is_doctor = Doctor.objects.filter(firstname=user.first_name, lastname=user.last_name).exists()
  if is_doctor:
    doctor = Doctor.objects.get(firstname=user.first_name, lastname=user.last_name)
    upcoming_appointments = Appointment.objects.filter(
      Q(doctor=doctor, appointment_date=today, time__gt=now.time()) |
      Q(doctor=doctor, appointment_date__gt=today)
    )
    past_appointments = Appointment.objects.filter(doctor=doctor, appointment_date__lt=today)
    return render(request, 'Hospital/dashboard.html', {
      'upcoming_appointments': upcoming_appointments,
      'past_appointments': past_appointments,
      'is_doctor': True
    })
  else:
    upcoming_appointments = Appointment.objects.filter(
      Q(user=user, appointment_date=today, time__gt=now.time()) |
      Q(user=user, appointment_date__gt=today)
    )
    past_appointments = Appointment.objects.filter(user=user, appointment_date__lt=today)
    return render(request, 'Hospital/dashboard.html', {
      'upcoming_appointments': upcoming_appointments,
      'past_appointments': past_appointments,
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
            appointment.save()  
            messages.success(request, 'Appointment rescheduled successfully.')
            return redirect('user_dashboard')  
        else:
            return render(request, 'Hospital/reschedule_form.html', {'appointment': appointment,'doctor_json':doctor_json,'hospital_json':hospital_json})
    except Appointment.DoesNotExist:
        messages.error(request, 'Appointment not found.')
        return redirect('user_dashboard')

@csrf_exempt
def prescription_modal(request, appointment_id):
    from .models import Appointment, Prescription, MedicineEntry
    appointment = Appointment.objects.get(id=appointment_id)
    prescription = getattr(appointment, 'prescription', None)
    if request.method == 'POST':
        data = request.POST
        diagnosis = data.get('diagnosis', '')
        medicines = data.getlist('medicine')
        dosages = data.getlist('dosage')
        dosage_units = data.getlist('dosage_unit')
        num_days_list = data.getlist('num_days')
        num_days_units = data.getlist('num_days_unit')
        frequencies = data.getlist('frequency')
        food_relations = data.getlist('food_relation')
        if prescription:
            prescription.diagnosis = diagnosis
            prescription.save()
            prescription.medicines.all().delete()
        else:
            prescription = Prescription.objects.create(
                appointment=appointment,
                diagnosis=diagnosis
            )
        for i in range(len(medicines)):
            MedicineEntry.objects.create(
                prescription=prescription,
                medicine=medicines[i],
                dosage=dosages[i],
                dosage_unit=dosage_units[i],
                num_days=num_days_list[i],
                num_days_unit=num_days_units[i],
                frequency=frequencies[i],
                food_relation=food_relations[i]
            )
        return JsonResponse({'success': True, 'message': 'Prescription sent to patient.'})
    return render(request, 'Hospital/prescription_form.html', {'appointment': appointment, 'prescription': prescription})


