from django.shortcuts import render,redirect
from django.contrib.auth.models import User,auth
from django.contrib import messages
from .models import AdminKey
from Hospitals.models import Hospital, doctor_departments, Doctor

def register_page(request):
  if request.user.is_authenticated:
    messages.success(request,'You are already logged in!')
    return redirect('/')
  hospitals_list = Hospital.objects.all()
  depts = doctor_departments
  if request.method=='POST':
    first_name = request.POST['first_name']
    last_name = request.POST['last_name']
    email = request.POST['email']
    username = request.POST['username']
    password1 = request.POST['password1']
    password2 = request.POST['password2']
    is_doctor = request.POST.get('is_doctor')
    if(password1==password2):
      if User.objects.filter(username=username):
        messages.info(request,'Username already exists')
        return  redirect('register')
      elif User.objects.filter(email=email):
        messages.info(request,"You can't have account with same mail")
        return redirect('register')
      else:
        admin_key = request.POST.get('admin_key', '')
        if(admin_key=='') and not is_doctor:
          user=User.objects.create_user(username=username, password=password1, email=email,first_name=first_name, last_name=last_name)
          user.save()
          messages.success(request,"Successfully logged in!!")
          return redirect('login')
        elif is_doctor:
          user=User.objects.create_user(username=username, password=password1, email=email,first_name=first_name, last_name=last_name)
          user.save()
          mobile = request.POST.get('mobile','')
          department = request.POST.get('department','')
          qualifications = request.POST.get('qualifications','')
          hospitals = request.POST.getlist('hospitals')
          profile_pic = request.FILES.get('profile_pic')
          doctor = Doctor.objects.create(
            firstname=first_name,
            lastname=last_name,
            mobile=mobile,
            department=department,
            qualifications=qualifications,
            profile_pic=profile_pic
          )
          doctor.save()
          doctor.hospitals.set(hospitals)
          messages.success(request,"Doctor registered successfully!")
          return redirect('login')
        else:
          if(AdminKey.objects.filter(admin_key=admin_key).exists()):
            user=User.objects.create_user(username=username, password=password1, email=email,first_name=first_name, last_name=last_name)
            user.is_staff=True
            user.is_superuser = True
            user.save()
            messages.success(request,'Admin registered successfully')
            return redirect('login')
          else:
            messages.info(request,'Invalid access key')
            return redirect('register')
    else:
        messages.info(request,"Password's don't match")
        return redirect("/register")
  else:
    return  render(request,'Users/register.html',{'hospital_ch': hospitals_list, 'depts': depts})

def login_page(request):
  if request.user.is_authenticated:
    messages.info(request,"You are already logged in!!")
    return redirect('home')
  if request.method=='POST':
    username=request.POST['username']
    password=request.POST['password']
    user=auth.authenticate(username=username,password=password)
    if user is not None:
      auth.login(request,user)
      return redirect('home')
    else:
      messages.info(request, 'Invalid username or password')
      return redirect('login')
  else:
    return  render(request,'Users/login.html')
def logout_page(request):
  auth.logout(request)
  messages.success(request,"Successfully logged out")
  return render(request,'Users/logout.html')