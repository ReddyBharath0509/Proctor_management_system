from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('assignments/', views.manage_assignments, name='manage_assignments'),
    path('assignments/remove/<int:student_id>/', views.remove_assignment, name='remove_assignment'),
    path('users/', views.manage_users, name='manage_users'),
    path('users/edit/<int:user_id>/', views.edit_user, name='edit_user'),
    path('users/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('timetable/', views.manage_timetable, name='manage_timetable'),
    path('timetable/delete/<int:slot_id>/', views.delete_time_slot, name='delete_time_slot_timetable'),
    path('time-slots/', views.time_slots, name='time_slots'),
    path('time-slots/add/', views.add_time_slot, name='add_time_slot'),
    path('time-slots/edit/<int:slot_id>/', views.edit_time_slot, name='edit_time_slot'),
    path('time-slots/delete/<int:slot_id>/', views.delete_time_slot, name='delete_time_slot'),
    path('routine-generator/settings/', views.routine_generator_settings, name='routine_generator_settings'),
    path('routine-generator/generate/', views.generate_routine, name='generate_routine'),
    path('routine-generator/view/', views.view_routine, name='view_routine'),
] 