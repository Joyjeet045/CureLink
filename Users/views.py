# Standard Django imports
from django.shortcuts import render, redirect
from django.contrib.auth.models import User, auth
from django.contrib import messages
from .models import AdminKey, UserProfile
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
        role = request.POST.get('role', 'user')
        if password1 == password2:
            if User.objects.filter(username=username).exists():
                messages.info(request,'Username already exists')
                return redirect('register')
            elif User.objects.filter(email=email).exists():
                messages.info(request,"You can't have account with same mail")
                return redirect('register')
            else:
                admin_key = request.POST.get('admin_key', '')
                if admin_key == '' and role == 'user':
                    user = User.objects.create_user(username=username, password=password1, email=email, first_name=first_name, last_name=last_name)
                    user.save()
                    UserProfile.objects.create(user=user, role='user')
                    messages.success(request,"Successfully registered as user!!")
                    return redirect('login')
                elif role == 'doctor':
                    user = User.objects.create_user(username=username, password=password1, email=email, first_name=first_name, last_name=last_name)
                    user.save()
                    UserProfile.objects.create(user=user, role='doctor')
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
                elif role == 'seller':
                    user = User.objects.create_user(username=username, password=password1, email=email, first_name=first_name, last_name=last_name)
                    user.save()
                    UserProfile.objects.create(user=user, role='seller')
                    messages.success(request,"Seller registered successfully!")
                    return redirect('login')
                else:
                    if(AdminKey.objects.filter(admin_key=admin_key).exists()):
                        user=User.objects.create_user(username=username, password=password1, email=email,first_name=first_name, last_name=last_name)
                        user.is_staff=True
                        user.is_superuser = True
                        user.save()
                        UserProfile.objects.create(user=user, role='user')
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