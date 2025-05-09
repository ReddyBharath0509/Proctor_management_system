from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.proctor_dashboard, name='proctor_dashboard'),
    path('students/', views.student_list, name='student_list'),
    path('timetable/', views.proctor_timetable, name='proctor_timetable'),
    path('meetings/', views.proctor_meetings, name='proctor_meetings'),
    path('meetings/<int:meeting_id>/', views.meeting_detail, name='meeting_detail'),
    path('attendance/', views.mark_attendance, name='mark_attendance'),
    path('issues/', views.proctor_issues, name='proctor_issues'),
    path('issues/<int:issue_id>/', views.issue_detail, name='proctor_issue_detail'),
] 