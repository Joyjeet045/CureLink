from django.urls import path
from django.contrib import admin

from . import views


urlpatterns=[
  path('register/',views.register_page,name='register'),
  path('login/',views.login_page,name='login'),
  path('logout/',views.logout_page,name='logout'),
  path('update-address/',views.update_address,name='update_address'),
]
