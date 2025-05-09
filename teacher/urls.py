from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('timetable/', views.teacher_timetable, name='teacher_timetable'),
    path('attendance/<int:id>/', views.mark_attendance, name='mark_attendance'),
    path('marks/', views.manage_marks, name='manage_marks'),
    path('marks/edit/<int:marks_id>/', views.edit_marks, name='edit_marks'),
    path('marks/delete/<int:marks_id>/', views.delete_marks, name='delete_marks'),
    path('meetings/', views.meeting_management, name='meeting_management'),
    path('meetings/create/', views.create_meeting, name='create_meeting'),
    path('meetings/schedule/', views.schedule_meeting, name='schedule_meeting'),
    path('meetings/update_status/<int:meeting_id>/', views.update_meeting_status, name='update_meeting_status'),
    path('chat/', views.teacher_chat, name='teacher_chat'),
    path('students/', views.student_management, name='student_management'),
] 