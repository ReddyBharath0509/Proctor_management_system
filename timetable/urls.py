from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.timetable_dashboard, name='timetable_dashboard'),
    path('create/', views.create_timetable, name='create_timetable'),
    path('view/<int:timetable_id>/', views.view_timetable, name='view_timetable'),
    path('student/', views.student_timetable, name='student_timetable'),
    path('teacher/', views.teacher_timetable, name='teacher_timetable'),
] 