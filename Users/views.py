from django.shortcuts import render,redirect
from django.contrib.auth.models import User,auth
from django.contrib import messages
from .models import AdminKey
# Create your views here.

def register_page(request):
  if request.user.is_authenticated:
    messages.success(request,'You are already logged in!')
    return redirect('/')
  if request.method=='POST':
    first_name = request.POST['first_name']
    last_name = request.POST['last_name']
    email = request.POST['email']
    username = request.POST['username']
    password1 = request.POST['password1']
    password2 = request.POST['password2']
    if(password1==password2):
      #if the username matches reject them
      if User.objects.filter(username=username):
        messages.info(request,'Username already exists')
        return  redirect('/register')
      elif User.objects.filter(email=email):
        messages.info(request,"You can\'t have account with same mail")
        return redirect('/register')
      else:
        #check if user is admin
        admin_key=request.POST['admin_key']
        if(admin_key==''):
          #user is not an admin
          user=User.objects.create_user(username=username, password=password1, email=email,first_name=first_name, last_name=last_name)
          user.save()
          messages.success(request,"Successfully logged in!!")
          return redirect('/login')
        else:
          #user is an admin
          if(AdminKey.objects.filter(admin_key=admin_key).exists()):
            user=User.objects.create_user(username=username, password=password1, email=email,first_name=first_name, last_name=last_name)
            #whether the user is admin/not is handled by django itself
            user.is_staff=True
            user.save()
            messages.success(request,'Admin registered successfully')
            return redirect('/login')
          else:
            messages.info(request,'Invalid access key')
            return redirect('/register')
    else:
        messages.info(request,"Password's don\'t match")
        return redirect("/register")
  else:
    return  render(request,'Users/register.html')  

def login_page(request):
  if request.user.is_authenticated:
    messages.info(request,"You are already logged in!!")
    return redirect('/')
  if request.method=='POST':
    username=request.POST['username']
    password=request.POST['password']
    user=auth.authenticate(username=username,password=password)
    if user is not None:
      auth.login(request,user)
      return redirect('/login')
    else:
      messages.info(request, 'Invalid username or password')
      return redirect('/login')
  #probably a GET request
  else:
    return  render(request,'Users/login.html')
def logout_page(request):
  auth.logout(request)
  messages.success(request,"Successfully logged out")
  return render(request,'Users/logout.html')