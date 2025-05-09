from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('profile/', views.student_profile, name='student_profile'),
    path('attendance/', views.student_attendance, name='student_attendance'),
    path('marks/', views.student_marks, name='student_marks'),
    path('proctor-details/', views.student_proctor_details, name='student_proctor_details'),
    path('meetings/', views.student_meetings, name='student_meetings'),
    path('meetings/summaries/', views.view_meeting_summaries, name='view_meeting_summaries'),
    path('meetings/summaries/add/<int:meeting_id>/', views.add_meeting_summary, name='add_meeting_summary'),
    path('meetings/summaries/view/<int:meeting_id>/', views.view_meeting_summary, name='view_meeting_summary'),
    path('timetable/', views.student_timetable, name='student_timetable'),
    path('issues/', views.student_issues, name='student_issues'),
    path('issues/<int:issue_id>/', views.issue_detail, name='issue_detail'),
    path('chat/', views.student_chat, name='student_chat'),
] 