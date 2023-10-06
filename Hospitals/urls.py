
from django.urls import path
from . import views

urlpatterns=[
  path('',views.home_page,name='home'),
  path('add-doctors/',views.add_doctor,name='doctors'),
  path('hospital/<int:hospital_id>/doctors/', views.view_all_doctors, name='view_all_doctors'),
  path('add_review/<int:doctor_id>/',views.add_review,name='add_review'),
  path("doctor/<int:doctor_id>/",views.doctor_profile,name="doctor_profile"),
  path('hospital/<int:hospital_id>/doctor/<int:doctor_id>/appointments/', views.doctor_appointments, name='doctor_appointment')
]
