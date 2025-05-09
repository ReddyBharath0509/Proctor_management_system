from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import User
from teacher.models import Teacher, Meeting
from admin_panel.models import TimeSlot
from .models import Student, Attendance, Marks, Issue, IssueComment
from proctor.models import ProctorMeeting
from notifications.models import Notification
from django.db import models
from django.utils import timezone
from django.db.models import Count, Avg
from django.http import JsonResponse
import logging
from chat.models import ChatRoom, Message

logger = logging.getLogger(__name__)

# Create your views here.

@login_required
def student_dashboard(request):
    if request.user.role != 'student':
        return redirect('dashboard')
    
    try:
        student = request.user.student
    except Student.DoesNotExist:
        return redirect('dashboard')
    
    # Get proctor details
    proctor = student.assigned_proctor
    
    # Get today's date and time
    now = timezone.now()
    today = now.date()
    current_day = now.weekday()  # Monday is 0, Sunday is 6
    current_hour = now.hour
    
    # Get all time slots for the student
    time_slots = TimeSlot.objects.filter(students=student).order_by('day', 'time')
    
    # Get all meetings for the student
    meetings = Meeting.objects.filter(student=student).order_by('date', 'time')
    
    # Count upcoming meetings (both time slots and scheduled meetings)
    upcoming_meetings_count = 0
    for slot in time_slots:
        # Handle Sunday (day=6) specially
        if slot.day == 6:  # Sunday
            if current_day == 6:  # Today is Sunday
                if slot.time >= current_hour:
                    upcoming_meetings_count += 1
            else:  # Any other day of the week
                upcoming_meetings_count += 1
        else:  # Monday to Saturday
            if slot.day > current_day:
                upcoming_meetings_count += 1
            elif slot.day == current_day:
                if slot.time >= current_hour:
                    upcoming_meetings_count += 1
    
    # Add upcoming scheduled meetings
    upcoming_meetings_count += meetings.filter(date__gte=today).count()
    
    # Get next meeting (from both time slots and scheduled meetings)
    next_meeting = None
    next_scheduled_meeting = meetings.filter(date__gte=today).order_by('date', 'time').first()
    
    for slot in time_slots:
        if slot.day == 6:  # Sunday
            if current_day == 6:  # Today is Sunday
                if slot.time >= current_hour:
                    next_meeting = slot
                    break
            else:  # Any other day of the week
                next_meeting = slot
                break
        else:  # Monday to Saturday
            if slot.day > current_day:
                next_meeting = slot
                break
            elif slot.day == current_day:
                if slot.time >= current_hour:
                    next_meeting = slot
                    break
    
    # Get attendance records
    attendance_records = Attendance.objects.filter(
        student=student
    ).order_by('-date')[:10]
    
    # Calculate attendance statistics
    total_attendance = Attendance.objects.filter(student=student).count()
    present_count = Attendance.objects.filter(student=student, is_present=True).count()
    absent_count = total_attendance - present_count
    attendance_percentage = (present_count / total_attendance * 100) if total_attendance > 0 else 0
    
    # Get marks by semester
    marks_by_semester = {}
    for mark in Marks.objects.filter(student=student).order_by('-date'):
        if mark.semester not in marks_by_semester:
            marks_by_semester[mark.semester] = []
        marks_by_semester[mark.semester].append(mark)
    
    # Get recent attendance
    recent_attendance = Attendance.objects.filter(
        student=student
    ).order_by('-date')[:5]
    
    # Get open issues count
    open_issues_count = Issue.objects.filter(student=student, status='open').count()
    
    context = {
        'student': student,
        'proctor': proctor,
        'attendance_records': attendance_records,
        'attendance_percentage': attendance_percentage,
        'present_count': present_count,
        'absent_count': absent_count,
        'marks_by_semester': marks_by_semester,
        'upcoming_meetings_count': upcoming_meetings_count,
        'next_meeting': next_meeting,
        'next_scheduled_meeting': next_scheduled_meeting,
        'meetings': meetings,
        'time_slots': time_slots,
        'today': today,
        'recent_attendance': recent_attendance,
        'open_issues_count': open_issues_count,
        'current_day': current_day,
        'current_hour': current_hour
    }
    
    return render(request, 'student/dashboard.html', context)

@login_required
def student_timetable(request):
    student = request.user.student
    regular_slots = TimeSlot.objects.filter(students=student).order_by('day', 'time')
    day_choices = TimeSlot.DAY_CHOICES
    time_choices = TimeSlot.TIME_CHOICES
    context = {
        'regular_slots': regular_slots,
        'day_choices': day_choices,
        'time_choices': time_choices,
    }
    return render(request, 'student/student_timetable.html', context)

@login_required
def view_proctor_details(request):
    if request.user.role != 'student':
        return redirect('dashboard')
    
    try:
        student = request.user.student
    except Student.DoesNotExist:
        student = Student.objects.create(user=request.user)
    
    context = {
        'student': student,
        'proctor': student.assigned_proctor
    }
    return render(request, 'student/proctor_details.html', context)

@login_required
def student_meetings(request):
    if request.user.role != 'student':
        return redirect('dashboard')
    
    student = request.user.student
    meetings = Meeting.objects.filter(student=student).order_by('-date', '-time')
    
    context = {
        'meetings': meetings,
    }
    return render(request, 'student/meetings.html', context)

@login_required
def student_profile(request):
    if request.user.role != 'student':
        return redirect('dashboard')
    
    student = request.user.student
    context = {
        'student': student,
    }
    return render(request, 'student/profile.html', context)

@login_required
def student_marks(request):
    if request.user.role != 'student':
        return redirect('dashboard')
    
    student = request.user.student
    marks = Marks.objects.filter(student=student).order_by('-date')
    
    # Calculate statistics
    total_subjects = marks.values('subject').distinct().count()
    average_marks = marks.aggregate(avg_marks=models.Avg('marks'))['avg_marks'] or 0
    
    context = {
        'marks': marks,
        'total_subjects': total_subjects,
        'average_marks': round(average_marks, 2),
    }
    return render(request, 'student/marks.html', context)

@login_required
def student_attendance(request):
    if request.user.role != 'student':
        return redirect('dashboard')
    
    student = request.user.student
    attendance_records = Attendance.objects.filter(student=student).order_by('-date')
    
    # Calculate attendance statistics
    total_classes = attendance_records.count()
    present_count = attendance_records.filter(is_present=True).count()
    absent_count = total_classes - present_count
    attendance_percentage = (present_count / total_classes * 100) if total_classes > 0 else 0
    
    # Get attendance by subject
    attendance_by_subject = {}
    for record in attendance_records:
        if record.subject not in attendance_by_subject:
            attendance_by_subject[record.subject] = {
                'total': 0,
                'present': 0,
                'absent': 0,
                'percentage': 0
            }
        attendance_by_subject[record.subject]['total'] += 1
        if record.is_present:
            attendance_by_subject[record.subject]['present'] += 1
        else:
            attendance_by_subject[record.subject]['absent'] += 1
        attendance_by_subject[record.subject]['percentage'] = round(
            (attendance_by_subject[record.subject]['present'] / attendance_by_subject[record.subject]['total'] * 100),
            2
        )
    
    # Debug logging
    print(f"Student: {student.user.get_full_name()}")
    print(f"Total attendance records: {total_classes}")
    print(f"Present count: {present_count}")
    print(f"Absent count: {absent_count}")
    print(f"Attendance percentage: {attendance_percentage}")
    
    context = {
        'attendance_records': attendance_records,
        'total_classes': total_classes,
        'present_count': present_count,
        'absent_count': absent_count,
        'attendance_percentage': round(attendance_percentage, 2),
        'attendance_by_subject': attendance_by_subject,
    }
    return render(request, 'student/attendance.html', context)

@login_required
def student_proctor_details(request):
    if request.user.role != 'student':
        return redirect('dashboard')
    
    student = request.user.student
    context = {
        'student': student,
        'proctor': student.assigned_proctor
    }
    return render(request, 'student/proctor_details.html', context)

@login_required
def report_issue(request):
    if request.method == 'POST':
        student = Student.objects.get(user=request.user)
        title = request.POST.get('title')
        description = request.POST.get('description')
        priority = request.POST.get('priority')

        Issue.objects.create(
            student=student,
            title=title,
            description=description,
            priority=priority
        )
        messages.success(request, 'Issue reported successfully.')
        return redirect('student_dashboard')
    
    return redirect('student_dashboard')

@login_required
def student_issues(request):
    student = Student.objects.get(user=request.user)
    issues = Issue.objects.filter(student=student).order_by('-created_at')
    
    context = {
        'issues': issues,
    }
    return render(request, 'student/issues.html', context)

@login_required
def issue_detail(request, issue_id):
    student = get_object_or_404(Student, user=request.user)
    issue = get_object_or_404(Issue, id=issue_id, student=student)
    
    if request.method == 'POST':
        comment = request.POST.get('comment')
        
        if comment:
            try:
                IssueComment.objects.create(
                    issue=issue,
                    user=request.user,
                    comment=comment
                )
                
                # Create notification for proctor
                Notification.objects.create(
                    user=student.assigned_proctor.user,
                    title='New Comment on Issue',
                    message=f'Student {student.user.get_full_name()} has commented on issue: {issue.title}',
                    notification_type='issue'
                )
                
                messages.success(request, 'Comment added successfully')
                return redirect('student_dashboard')
            except Exception as e:
                messages.error(request, f'Error adding comment: {str(e)}')
    
    context = {
        'issue': issue,
        'comments': IssueComment.objects.filter(issue=issue).order_by('created_at')
    }
    return render(request, 'student/issue_detail.html', context)

@login_required
def view_meeting_summaries(request):
    if request.user.role != 'student':
        return redirect('dashboard')
    
    student = request.user.student
    meetings_with_summaries = ProctorMeeting.objects.filter(
        students=student,
        is_completed=True
    ).select_related('summary').order_by('-date')
    
    context = {
        'meetings_with_summaries': meetings_with_summaries
    }
    return render(request, 'student/meeting_summaries.html', context)

@login_required
def add_meeting_summary(request, meeting_id):
    if request.user.role != 'student':
        return redirect('dashboard')
    
    meeting = get_object_or_404(ProctorMeeting, id=meeting_id, students=request.user.student)
    
    if request.method == 'POST':
        summary_text = request.POST.get('summary_text')
        action_items = request.POST.get('action_items')
        next_meeting_suggestions = request.POST.get('next_meeting_suggestions')
        
        try:
            MeetingSummary.objects.create(
                meeting=meeting,
                summary_text=summary_text,
                action_items=action_items,
                next_meeting_suggestions=next_meeting_suggestions
            )
            messages.success(request, 'Meeting summary added successfully')
            return redirect('view_meeting_summaries')
        except Exception as e:
            messages.error(request, f'Error adding meeting summary: {str(e)}')
    
    context = {
        'meeting': meeting
    }
    return render(request, 'student/add_meeting_summary.html', context)

@login_required
def view_meeting_summary(request, meeting_id):
    if request.user.role != 'student':
        return redirect('dashboard')
    
    meeting = get_object_or_404(ProctorMeeting, id=meeting_id, students=request.user.student)
    summary = get_object_or_404(MeetingSummary, meeting=meeting)
    
    context = {
        'meeting': meeting,
        'summary': summary
    }
    return render(request, 'student/view_meeting_summary.html', context)

@login_required
def student_chat(request):
    if request.user.role != 'student':
        return redirect('dashboard')
    
    try:
        student = request.user.student
    except Student.DoesNotExist:
        return redirect('dashboard')
    
    # Get all teachers the student can chat with
    teacher_ids = set()
    
    # Get teachers from meetings
    meeting_teachers = Teacher.objects.filter(
        meeting__student=student
    ).values_list('id', flat=True)
    teacher_ids.update(meeting_teachers)
    
    # Get teachers from the same department
    department_teachers = Teacher.objects.filter(
        department=student.department
    ).values_list('id', flat=True)
    teacher_ids.update(department_teachers)
    
    # Get teachers from time slots
    time_slot_teachers = Teacher.objects.filter(
        time_slots__students=student,
        time_slots__is_active=True
    ).values_list('id', flat=True)
    teacher_ids.update(time_slot_teachers)
    
    # Get all unique teachers
    teachers = Teacher.objects.filter(id__in=teacher_ids)
    
    # Get or create chat rooms for each teacher
    chat_rooms = []
    for teacher in teachers:
        room, created = ChatRoom.objects.get_or_create(
            teacher=teacher,
            student=student
        )
        chat_rooms.append(room)
    
    # Calculate unread counts for each room
    chat_rooms_with_unread = []
    for room in chat_rooms:
        unread_count = room.messages.filter(
            is_read=False
        ).exclude(sender=request.user).count()
        chat_rooms_with_unread.append({
            'room': room,
            'unread_count': unread_count
        })
    
    # Get the active chat room (if specified)
    active_room_id = request.GET.get('room')
    active_room = None
    messages = []
    
    if active_room_id:
        try:
            # Find the active room from the list of chat rooms
            active_room = next((room for room in chat_rooms if room.id == int(active_room_id)), None)
            if active_room:
                messages = active_room.messages.all().order_by('timestamp')
                # Mark messages as read
                active_room.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
            else:
                messages.error(request, "Chat room not found.")
        except (ValueError, TypeError):
            messages.error(request, "Invalid chat room ID.")
    
    # Handle message submission
    if request.method == 'POST' and active_room:
        content = request.POST.get('content')
        if content:
            try:
                # Create the message
                message = Message.objects.create(
                    room=active_room,
                    sender=request.user,
                    content=content,
                    is_read=False  # Mark as unread for the recipient
                )
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': {
                            'id': message.id,
                            'content': message.content,
                            'timestamp': message.timestamp.strftime('%I:%M %p'),
                            'sender': message.sender.username
                        }
                    })
                return redirect(f'{request.path}?room={active_room.id}')
            except Exception as e:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': str(e)
                    }, status=500)
                messages.error(request, f"Failed to send message: {str(e)}")
    
    context = {
        'chat_rooms_with_unread': chat_rooms_with_unread,
        'active_room': active_room,
        'messages': messages,
    }
    
    return render(request, 'student/chat.html', context)
