from django.shortcuts import render,get_object_or_404,redirect

from django.db import transaction
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from .models import Doctor,Hospital,State,Timing,Review
from .constants import doctor_departments
# Create your views here.
def is_admin(user):
  return user.is_staff

def home_page(request):
  states=State.objects.all()
  state_filter=request.GET.get('state')
  list=range(1,6)
  if state_filter and state_filter != "All":
    hospitals= Hospital.objects.filter(state=state_filter)
  else:
    hospitals = Hospital.objects.all()
  return render(request,'Hospital/home.html',{"hospitals":hospitals,"states":states,"list":list})
@transaction.atomic
# @user_passes_test(is_admin,login_url="{% url 'login' %}")
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

def view_all_doctors(request,hospital_id):
  hospital=get_object_or_404(Hospital,pk=hospital_id)
  doctors=hospital.doctors.all()
  timings=Timing.objects.filter(doctor__in=doctors,hospital=hospital)
  return render(request,"Hospital/view_all_doctors.html", {'hospital': hospital, 'doctors': doctors,'timings':timings,'hospital_id':hospital_id})

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

def doctor_profile(request,doctor_id):
  doctor=get_object_or_404(Doctor,id=doctor_id)
  reviews=Review.objects.filter(doctor=doctor).order_by('-rating')
  list=range(1,6)
  top_review_count=len(reviews)//2+1
  top_reviews=reviews[:top_review_count]
  return render(request,'Hospital/view_profile.html',{'doctor':doctor,'top_reviews':top_reviews,'list':list})
  
def doctor_appointments(request,hospital_id,doctor_id):
  return render(request,'Hospital/book_appointment.html')