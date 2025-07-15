from django.contrib import admin
from django.urls import path
from . import views
urlpatterns=[
  path('',views.home_page,name='home'),
  path('add-doctors/',views.add_doctor,name='doctors'),
  path('doctors/',views.view_doctors,name='view_doctors'),
  path('hospital/<int:hospital_id>/doctors/', views.view_all_doctors, name='view_all_doctors'),
  path('add_review/<int:doctor_id>/',views.add_review,name='add_review'),
  path("doctor/<int:doctor_id>/",views.doctor_profile,name="doctor_profile"),
  path('hospital/<int:hospital_id>/doctor/<int:doctor_id>/appointments/', views.doctor_appointments, name='doctor_appointment'),
  path('get_available_timings/', views.get_available_timings, name='get_available_timings'),
  path('dashboard/me/', views.dashboard, name='user_dashboard'),
  path('cancel-appointment/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
  path('reschedule-appointment/<int:appointment_id>/', views.reschedule_appointment, name='reschedule_appointment'),
  path('api/prescription/<int:appointment_id>/', views.get_prescription_details, name='get_prescription_details'),
  path('medicines/', views.medicines_page, name='medicines'),
  path('lab-tests/', views.lab_tests_page, name='lab_tests'),
  path('appointment/<int:appointment_id>/prescription/', views.add_prescription, name='add_prescription'),
  path('doctor/take-leave/', views.doctor_take_leave, name='doctor_take_leave'),
]
