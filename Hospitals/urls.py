from django.urls import path
from . import views

urlpatterns=[
  path('',views.home_page,name='home'),
  path('doctors/',views.home_page,name='doctors')
]