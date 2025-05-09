from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Proctor, ProctorMeeting
from admin_panel.models import TimeSlot
from student.models import Student, Issue, IssueComment, Attendance
from notifications.models import Notification
from django.db.models import Count
import logging

logger = logging.getLogger(__name__)

@login_required
def student_list(request):
    proctor = get_object_or_404(Proctor, user=request.user)
    students = Student.objects.filter(assigned_proctor=proctor).order_by('user__first_name', 'user__last_name')
    
    # Get attendance statistics for each student
    for student in students:
        total_attendance = Attendance.objects.filter(student=student).count()
        present_count = Attendance.objects.filter(student=student, is_present=True).count()
        student.attendance_percentage = (present_count / total_attendance * 100) if total_attendance > 0 else 0
        
        # Get open issues count
        student.open_issues_count = Issue.objects.filter(student=student, status='open').count()
    
    context = {
        'students': students
    }
    return render(request, 'proctor/student_list.html', context)

@login_required
def proctor_timetable(request):
    proctor = get_object_or_404(Proctor, user=request.user)
    today = timezone.now().date()
    weekday = today.weekday()
    
    # Get all time slots for the proctor
    time_slots = TimeSlot.objects.filter(teacher=proctor, is_active=True).order_by('day', 'time')
    
    # Group time slots by day
    timetable = {}
    for day, day_name in TimeSlot.DAY_CHOICES:
        timetable[day] = {
            'name': day_name,
            'slots': time_slots.filter(day=day)
        }
    
    context = {
        'timetable': timetable,
        'today_weekday': weekday
    }
    return render(request, 'proctor/timetable.html', context)

@login_required
def proctor_meetings(request):
    proctor = get_object_or_404(Proctor, user=request.user)
    today = timezone.now().date()
    
    # Get upcoming meetings
    upcoming_meetings = ProctorMeeting.objects.filter(
        proctor=proctor,
        date__gte=today,
        is_completed=False,
        is_cancelled=False
    ).order_by('date', 'time')
    
    # Get past meetings
    past_meetings = ProctorMeeting.objects.filter(
        proctor=proctor,
        date__lt=today
    ).order_by('-date', '-time')
    
    # Get completed meetings
    completed_meetings = ProctorMeeting.objects.filter(
        proctor=proctor,
        is_completed=True
    ).order_by('-date', '-time')
    
    # Get cancelled meetings
    cancelled_meetings = ProctorMeeting.objects.filter(
        proctor=proctor,
        is_cancelled=True
    ).order_by('-date', '-time')
    
    context = {
        'upcoming_meetings': upcoming_meetings,
        'past_meetings': past_meetings,
        'completed_meetings': completed_meetings,
        'cancelled_meetings': cancelled_meetings,
        'today': today
    }
    return render(request, 'proctor/meetings.html', context)

@login_required
def meeting_detail(request, meeting_id):
    meeting = get_object_or_404(ProctorMeeting, id=meeting_id, proctor=request.user.proctor)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'complete':
            meeting.is_completed = True
            meeting.save()
            messages.success(request, 'Meeting marked as completed.')
            return redirect('proctor_dashboard')
        elif action == 'cancel':
            meeting.is_cancelled = True
            meeting.save()
            messages.warning(request, 'Meeting has been cancelled.')
            return redirect('proctor_dashboard')
    
    context = {
        'meeting': meeting
    }
    return render(request, 'proctor/meeting_detail.html', context)

@login_required
def mark_attendance(request):
    proctor = get_object_or_404(Proctor, user=request.user)
    today = timezone.now().date()
    
    # Get today's time slots
    time_slots = TimeSlot.objects.filter(
        teacher=proctor,
        day=today.weekday(),
        is_active=True
    ).order_by('time')
    
    if request.method == 'POST':
        time_slot_id = request.POST.get('time_slot')
        time_slot = get_object_or_404(TimeSlot, id=time_slot_id, teacher=proctor)
        
        # Get all students assigned to this proctor
        students = Student.objects.filter(assigned_proctor=proctor)
        
        for student in students:
            is_present = request.POST.get(f'student_{student.id}') == 'present'
            remarks = request.POST.get(f'remarks_{student.id}', '')
            
            # Create or update attendance record
            attendance, created = Attendance.objects.update_or_create(
                student=student,
                date=today,
                defaults={
                    'is_present': is_present,
                    'subject': f'Proctor Meeting - {time_slot.get_time_display()}',
                    'remarks': f'Proctor: {proctor.user.get_full_name()} - {remarks}'
                }
            )
            
            # Create notification for student
            Notification.objects.create(
                user=student.user,
                title='Attendance Marked',
                message=f'Your attendance has been marked as {"Present" if is_present else "Absent"} for the proctor meeting at {time_slot.get_time_display()}.',
                notification_type='attendance'
            )
        
        messages.success(request, 'Attendance marked successfully.')
        return redirect('proctor_dashboard')
    
    context = {
        'time_slots': time_slots,
        'students': Student.objects.filter(assigned_proctor=proctor).order_by('user__first_name', 'user__last_name')
    }
    return render(request, 'proctor/mark_attendance.html', context)

@login_required
def proctor_issues(request):
    proctor = get_object_or_404(Proctor, user=request.user)
    issues = Issue.objects.filter(student__assigned_proctor=proctor).order_by('-created_at')
    
    if request.method == 'POST':
        issue_id = request.POST.get('issue_id')
        status = request.POST.get('status')
        comment = request.POST.get('comment')
        
        issue = get_object_or_404(Issue, id=issue_id, student__assigned_proctor=proctor)
        
        if status:
            issue.status = status
            if status == 'resolved':
                issue.resolved_at = timezone.now()
            issue.save()
            
            # Create notification for student
            Notification.objects.create(
                user=issue.student.user,
                title='Issue Status Updated',
                message=f'Your issue "{issue.title}" has been marked as {issue.get_status_display()}',
                notification_type='general'
            )
        
        if comment:
            IssueComment.objects.create(
                issue=issue,
                user=request.user,
                comment=comment
            )
            
            # Create notification for student
            Notification.objects.create(
                user=issue.student.user,
                title='New Comment on Your Issue',
                message=f'Your proctor has commented on your issue "{issue.title}"',
                notification_type='general'
            )
        
        messages.success(request, 'Issue updated successfully.')
        return redirect('proctor_dashboard')
    
    context = {
        'issues': issues,
        'status_choices': Issue.STATUS_CHOICES
    }
    return render(request, 'proctor/issues.html', context)

@login_required
def issue_detail(request, issue_id):
    proctor = get_object_or_404(Proctor, user=request.user)
    issue = get_object_or_404(Issue, id=issue_id, student__assigned_proctor=proctor)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        comment = request.POST.get('comment')
        
        if status:
            issue.status = status
            if status == 'resolved':
                issue.resolved_at = timezone.now()
            issue.save()
            
            # Create notification for student
            Notification.objects.create(
                user=issue.student.user,
                title='Issue Status Updated',
                message=f'Your issue "{issue.title}" has been marked as {issue.get_status_display()}',
                notification_type='general'
            )
        
        if comment:
            IssueComment.objects.create(
                issue=issue,
                user=request.user,
                comment=comment
            )
            
            # Create notification for student
            Notification.objects.create(
                user=issue.student.user,
                title='New Comment on Your Issue',
                message=f'Your proctor has commented on your issue "{issue.title}"',
                notification_type='general'
            )
        
        messages.success(request, 'Issue updated successfully.')
        return redirect('issue_detail', issue_id=issue_id)
    
    context = {
        'issue': issue,
        'comments': issue.comments.all(),
        'status_choices': Issue.STATUS_CHOICES
    }
    return render(request, 'proctor/issue_detail.html', context)

@login_required
def proctor_dashboard(request):
    proctor = get_object_or_404(Proctor, user=request.user)
    
    # Get student count
    student_count = Student.objects.filter(assigned_proctor=proctor).count()
    
    # Get today's meetings
    today = timezone.now().date()
    today_schedule = TimeSlot.objects.filter(
        teacher=proctor,
        day=today.weekday(),
        is_active=True
    ).order_by('time')
    today_meetings_count = today_schedule.count()
    
    # Get pending attendance count
    pending_attendance_count = Attendance.objects.filter(
        student__assigned_proctor=proctor,
        date=today,
        is_present__isnull=True
    ).count()
    
    # Get open issues count
    open_issues_count = Issue.objects.filter(
        student__assigned_proctor=proctor,
        status='open'
    ).count()
    
    # Get recent issues
    recent_issues = Issue.objects.filter(
        student__assigned_proctor=proctor
    ).order_by('-created_at')[:5]
    
    context = {
        'proctor': proctor,
        'student_count': student_count,
        'today_schedule': today_schedule,
        'today_meetings_count': today_meetings_count,
        'pending_attendance_count': pending_attendance_count,
        'open_issues_count': open_issues_count,
        'recent_issues': recent_issues
    }
    return render(request, 'proctor/dashboard.html', context)
