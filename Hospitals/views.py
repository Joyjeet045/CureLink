from django.shortcuts import render
from django.db import transaction
from django.contrib.auth.decorators import user_passes_test
from .models import Doctor,Hospital,State
# Create your views here.
def is_admin(user):
  return user.is_staff

@transaction.atomic
@user_passes_test(is_admin,login_url="{% url 'login' %}")
def add_doctor(request):
  if request.method=='POST':
    first_name = request.POST['first_name']
    last_name = request.POST['last_name']
    mobile=request.POST['mobile']
    profile_pic=request.FILES['profile_pic']
    #select field->dept,hospital
    department=request.POST['department']
    hospitals=request.POST.getlist('hospitals')
    status=bool(request.POST['status'])
    doctor=Doctor.objects.create(
      firstname=first_name,
      lastname=last_name,
      mobile=mobile,
      profile_pic=profile_pic,
      status=status,
      department=department
    )
    doctor.hospitals.set(hospitals)
  
  hospitals=Hospital.objects.all()
  state=State.objects.all()
  return render(request,{'hospital_ch':hospitals,'state_ch':state})
