from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Teacher, Meeting, Timetable
from student.models import Student, Attendance, Marks
from django.contrib import messages
from accounts.models import User
from notifications.models import Notification
from admin_panel.models import TimeSlot
from proctor.models import ProctorMeeting, Proctor
from django.urls import reverse
from accounts.utils import send_email_notification
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, time
from chat.models import ChatRoom, Message
from django.http import JsonResponse
from django.views.decorators.http import require_POST

# Create your views here.

@login_required
def teacher_dashboard(request):
    if request.user.role != 'teacher':
        return redirect('dashboard')
    
    try:
        teacher = request.user.teacher
        # Get the proctor instance for this teacher
        try:
            proctor = teacher.user.proctor
        except:
            from proctor.models import Proctor
            proctor = Proctor.objects.create(
                user=teacher.user,
                department=teacher.department,
                designation=teacher.designation,
                phone_number="Not Assigned",
                office_location="Not Assigned"
            )
    except Teacher.DoesNotExist:
        return redirect('dashboard')
    
    # Get today's date and time
    now = timezone.now()
    today = now.date()
    current_day = now.weekday()  # Monday is 0, Sunday is 6
    current_hour = now.hour
    
    # Get all time slots for the teacher
    time_slots = TimeSlot.objects.filter(teacher=teacher).order_by('day', 'time')
    
    # Get all meetings for the teacher
    meetings = Meeting.objects.filter(teacher=teacher).order_by('date', 'time')
    
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
    
    # Get assigned students using the proctor instance
    assigned_students = Student.objects.filter(assigned_proctor=proctor)
    
    # Get attendance records
    attendance_records = Attendance.objects.filter(
        student__in=assigned_students
    ).order_by('-date')[:10]
    
    # Calculate attendance statistics
    total_attendance = Attendance.objects.filter(student__in=assigned_students).count()
    present_count = Attendance.objects.filter(student__in=assigned_students, is_present=True).count()
    absent_count = total_attendance - present_count
    attendance_percentage = (present_count / total_attendance * 100) if total_attendance > 0 else 0
    
    # Get recent attendance
    recent_attendance = Attendance.objects.filter(
        student__in=assigned_students
    ).order_by('-date')[:5]
    
    # Get today's schedule
    today_schedule = time_slots.filter(day=current_day).order_by('time')
    
    # Get upcoming meetings for the next 7 days
    upcoming_meetings = []
    for i in range(7):
        day = (current_day + i) % 7
        meetings = time_slots.filter(day=day)
        if day == current_day:
            meetings = meetings.filter(time__gte=current_hour)
        upcoming_meetings.extend(meetings)
    
    # Get past meetings
    past_meetings = []
    for i in range(7):
        day = (current_day - i - 1) % 7
        meetings = time_slots.filter(day=day)
        if day == current_day:
            meetings = meetings.filter(time__lt=current_hour)
        past_meetings.extend(meetings)
    
    # Convert attendance status
    for attendance in recent_attendance:
        attendance.status = 'Present' if attendance.is_present else 'Absent'
    
    context = {
        'teacher': teacher,
        'proctor': proctor,
        'assigned_students': assigned_students,
        'assigned_students_count': assigned_students.count(),
        'upcoming_meetings_count': upcoming_meetings_count,
        'next_meeting': next_meeting,
        'next_scheduled_meeting': next_scheduled_meeting,
        'attendance_records': attendance_records,
        'attendance_stats': {
            'total': total_attendance,
            'present': present_count,
            'absent': absent_count,
            'percentage': round(attendance_percentage, 2)
        },
        'recent_attendance': recent_attendance,
        'regular_slots': time_slots,  # Changed from time_slots to regular_slots
        'today_schedule': today_schedule,
        'upcoming_meetings': upcoming_meetings[:5],  # Show only next 5 meetings
        'past_meetings': past_meetings[:5],  # Show only last 5 meetings
        'current_day': current_day,
        'current_hour': current_hour,
        'meetings': meetings,
        'total_meetings_count': len(upcoming_meetings) + len(past_meetings),  # Add total meetings count
    }
    
    return render(request, 'teacher/dashboard.html', context)

@login_required
def teacher_timetable(request):
    if request.user.role != 'teacher':
        return redirect('dashboard')
    
    try:
        teacher = request.user.teacher
    except Teacher.DoesNotExist:
        teacher = Teacher.objects.create(user=request.user)
    
    time_slots = TimeSlot.objects.filter(teacher=teacher)
    current_time = timezone.now()
    current_day = current_time.weekday()  # Monday is 0, Sunday is 6
    current_hour = current_time.hour
    
    # Add status to each time slot
    for slot in time_slots:
        slot_status = 'upcoming'
        if slot.day < current_day:
            slot_status = 'past'
        elif slot.day == current_day:
            if slot.time < current_hour:
                slot_status = 'past'
        slot.status = slot_status
    
    regular_slots = TimeSlot.objects.filter(teacher=teacher).order_by('day', 'time')
    day_choices = TimeSlot.DAY_CHOICES
    time_choices = TimeSlot.TIME_CHOICES
    
    context = {
        'time_slots': time_slots,
        'regular_slots': regular_slots,
        'day_choices': day_choices,
        'time_choices': time_choices,
    }
    return render(request, 'teacher/teacher_timetable.html', context)

@login_required
def mark_attendance(request, id):
    if request.user.role != 'teacher':
        return redirect('dashboard')
    
    try:
        # Try to get the time slot first
        time_slot = TimeSlot.objects.get(id=id, teacher__user=request.user)
        students = time_slot.students.all()
        is_time_slot = True
    except TimeSlot.DoesNotExist:
        try:
            # If not a time slot, try to get the student
            student = Student.objects.get(id=id, assigned_proctor__user=request.user)
            students = [student]
            is_time_slot = False
        except Student.DoesNotExist:
            messages.error(request, 'Invalid student or time slot')
            return redirect('teacher_dashboard')
    
    if request.method == 'POST':
        try:
            # Get today's date
            today = timezone.now().date()
            date = request.POST.get('date', today)
            
            # Create or update attendance records for each student
            for student in students:
                is_present = request.POST.get(f'status_{student.id}') == 'present'
                remarks = request.POST.get(f'remarks_{student.id}', '')
                subject = f'Proctor Meeting - {time_slot.get_time_display() if is_time_slot else "Individual Meeting"}'

                attendance, created = Attendance.objects.get_or_create(
                    student=student,
                    date=date,
                    subject=subject,
                    defaults={'is_present': is_present, 'remarks': remarks}
                )
                if not created:
                    attendance.is_present = is_present
                    attendance.remarks = remarks
                    attendance.save()
            
            messages.success(request, 'Attendance marked successfully')
            return redirect('teacher_dashboard')
        except Exception as e:
            messages.error(request, f'Error marking attendance: {str(e)}')
            return redirect('teacher_dashboard')
    
    # Get today's attendance records if they exist
    today = timezone.now().date()
    today_records = Attendance.objects.filter(
        student__in=students,
        date=today,
        subject=f'Proctor Meeting - {time_slot.get_time_display() if is_time_slot else "Individual Meeting"}'
    )
    
    attendance_status = {record.student_id: record.is_present for record in today_records}
    
    context = {
        'time_slot': time_slot if is_time_slot else None,
        'students': students,
        'attendance_status': attendance_status,
        'is_time_slot': is_time_slot,
        'today': today
    }
    return render(request, 'teacher/mark_attendance.html', context)

@login_required
def manage_marks(request):
    if request.user.role != 'teacher':
        return redirect('dashboard')
    
    try:
        teacher = request.user.teacher
        # Get the proctor instance for this teacher
        try:
            proctor = teacher.user.proctor
        except:
            from proctor.models import Proctor
            proctor = Proctor.objects.create(
                user=teacher.user,
                department=teacher.department,
                designation=teacher.designation,
                phone_number="Not Assigned",
                office_location="Not Assigned"
            )
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher profile not found. Please contact administrator.')
        return redirect('dashboard')
    
    # Get students assigned to this proctor
    assigned_students = Student.objects.filter(assigned_proctor=proctor)
    marks = Marks.objects.filter(student__in=assigned_students).order_by('-date')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        student_id = request.POST.get('student')
        subject = request.POST.get('subject')
        marks_value = request.POST.get('marks')
        semester = request.POST.get('semester')
        
        try:
            student = Student.objects.get(id=student_id, assigned_proctor=proctor)
            
            if action == 'update':
                # Update existing marks
                mark_id = request.POST.get('mark_id')
                mark = Marks.objects.get(id=mark_id, student=student)
                mark.subject = subject
                mark.marks = marks_value
                mark.semester = semester
                mark.save()
                
                # Create notification for update
                Notification.objects.create(
                    user=student.user,
                    title='Marks Updated',
                    message=f'Marks have been updated for {subject}',
                    notification_type='marks'
                )
                
                messages.success(request, f'Successfully updated marks for {student.user.get_full_name()}')
                return redirect('teacher_dashboard')
            else:
                # Create new marks record
                mark = Marks.objects.create(
                    student=student,
                    subject=subject,
                    marks=marks_value,
                    semester=semester
                )
                
                # Create notification for new marks
                Notification.objects.create(
                    user=student.user,
                    title='New Marks Added',
                    message=f'New marks have been added for {subject}',
                    notification_type='marks'
                )
                
                # Send email notification
                send_email_notification(
                    user=student.user,
                    template_key='marks_added',
                    context={
                        'user': student.user,
                        'subject': subject,
                        'marks': marks_value,
                        'semester': semester,
                        'dashboard_url': request.build_absolute_uri(reverse('student_dashboard'))
                    }
                )
                
                messages.success(request, f'Successfully added marks for {student.user.get_full_name()}')
                return redirect('teacher_dashboard')
                
        except Student.DoesNotExist:
            messages.error(request, 'Invalid student selection')
        except Marks.DoesNotExist:
            messages.error(request, 'Marks record not found')
        except Exception as e:
            messages.error(request, f'Error processing marks: {str(e)}')
    
    context = {
        'assigned_students': assigned_students,
        'marks': marks,
    }
    return render(request, 'teacher/manage_marks.html', context)

@login_required
def edit_marks(request, marks_id):
    if request.user.role != 'teacher':
        return redirect('dashboard')
    
    marks = get_object_or_404(Marks, id=marks_id)
    teacher = request.user.teacher
    
    if marks.student.assigned_proctor != teacher:
        messages.error(request, 'You do not have permission to edit these marks')
        return redirect('manage_marks')
    
    if request.method == 'POST':
        marks.subject = request.POST.get('subject')
        marks.marks = request.POST.get('marks')
        marks.semester = request.POST.get('semester')
        marks.save()
        
        messages.success(request, f'Successfully updated marks for {marks.student.user.get_full_name()}')
        return redirect('manage_marks')
    
    context = {
        'marks': marks,
    }
    return render(request, 'teacher/edit_marks.html', context)

@login_required
def delete_marks(request, marks_id):
    if request.user.role != 'teacher':
        return redirect('dashboard')
    
    try:
        teacher = request.user.teacher
        # Get the proctor instance for this teacher
        try:
            proctor = teacher.user.proctor
        except:
            from proctor.models import Proctor
            proctor = Proctor.objects.create(
                user=teacher.user,
                department=teacher.department,
                designation=teacher.designation,
                phone_number="Not Assigned",
                office_location="Not Assigned"
            )
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher profile not found. Please contact administrator.')
        return redirect('dashboard')
    
    try:
        marks = Marks.objects.get(id=marks_id)
        student = marks.student
        
        # Check if the student is assigned to this proctor
        if student.assigned_proctor != proctor:
            messages.error(request, 'You do not have permission to delete these marks')
            return redirect('teacher_dashboard')
        
        if request.method == 'POST':
            # Create notification before deleting
            Notification.objects.create(
                user=student.user,
                title='Marks Deleted',
                message=f'Marks for {marks.subject} have been deleted',
                notification_type='marks'
            )
            
            # Delete the marks
            marks.delete()
            messages.success(request, f'Successfully deleted marks for {student.user.get_full_name()}')
            return redirect('teacher_dashboard')
        
        context = {
            'marks': marks,
        }
        return render(request, 'teacher/delete_marks.html', context)
        
    except Marks.DoesNotExist:
        messages.error(request, 'Marks record not found')
        return redirect('teacher_dashboard')
    except Exception as e:
        messages.error(request, f'Error deleting marks: {str(e)}')
        return redirect('teacher_dashboard')

@login_required
def meeting_management(request):
    if request.user.role != 'teacher':
        return redirect('dashboard')
    
    teacher = Teacher.objects.get(user=request.user)
    assigned_students = Student.objects.filter(assigned_proctor__user=request.user)
    meetings = Meeting.objects.filter(teacher=teacher).order_by('-date', '-time')
    
    context = {
        'teacher': teacher,
        'assigned_students': assigned_students,
        'meetings': meetings
    }
    return render(request, 'teacher/meeting_management.html', context)

@login_required
def schedule_meeting(request):
    if request.user.role != 'teacher':
        return redirect('dashboard')
    
    if request.method == 'POST':
        try:
            # Get the selected day (0-6 for Monday-Sunday)
            day = int(request.POST.get('day'))
            hour = int(request.POST.get('time'))
            
            # Calculate the date for the next occurrence of the selected day
            today = timezone.now().date()
            days_ahead = (day - today.weekday()) % 7
            if days_ahead == 0 and timezone.now().hour >= hour:
                days_ahead = 7  # If today is the selected day and time has passed, schedule for next week
            meeting_date = today + timezone.timedelta(days=days_ahead)
            
            # Create the meeting time
            meeting_time = time(hour=hour, minute=0)
            
            # Create the meeting
            meeting = Meeting.objects.create(
                teacher=Teacher.objects.get(user=request.user),
                date=meeting_date,
                time=meeting_time
            )
            
            # Add students to the meeting
            student_ids = request.POST.getlist('students')
            students = Student.objects.filter(id__in=student_ids)
            meeting.students.set(students)
            
            # Create notifications for students
            for student in students:
                Notification.objects.create(
                    user=student.user,
                    title='New Meeting Scheduled',
                    message=f'A meeting has been scheduled for {meeting_date.strftime("%A, %B %d")} at {meeting_time.strftime("%I:%M %p")}',
                    notification_type='meeting'
                )
            
            messages.success(request, 'Meeting scheduled successfully')
        except Exception as e:
            messages.error(request, f'Error scheduling meeting: {str(e)}')
    
    return redirect('meeting_management')

@login_required
def teacher_meetings(request):
    if request.user.role != 'teacher':
        return redirect('dashboard')
    
    teacher = request.user.teacher
    meetings = Meeting.objects.filter(teacher=teacher).order_by('date', 'time')
    
    context = {
        'meetings': meetings,
    }
    return render(request, 'teacher/meetings.html', context)

@login_required
def teacher_meeting_details(request, meeting_id):
    if request.user.role != 'teacher':
        return redirect('dashboard')
    
    meeting = get_object_or_404(Meeting, id=meeting_id, teacher__user=request.user)
    
    context = {
        'meeting': meeting,
    }
    return render(request, 'teacher/meeting_details.html', context)

@login_required
def teacher_chat(request):
    try:
        # Check if user has a teacher profile
        teacher = request.user.teacher
    except Teacher.DoesNotExist:
        return redirect('home')
    
    # Get all chat rooms where the teacher is a participant
    chat_rooms = ChatRoom.objects.filter(teacher=teacher)
    
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
            active_room = chat_rooms.get(id=active_room_id)
            messages = active_room.messages.all().order_by('timestamp')
            # Mark messages as read
            active_room.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
        except ChatRoom.DoesNotExist:
            pass  # Silently handle missing chat room
    
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
                return redirect(f'{request.path}?room={active_room.id}')
    
    context = {
        'chat_rooms_with_unread': chat_rooms_with_unread,
        'active_room': active_room,
        'messages': messages,
    }
    return render(request, 'teacher/teacher_chat.html', context)

@login_required
def student_management(request):
    try:
        teacher = request.user.teacher
        proctor = teacher.user.proctor
    except (Teacher.DoesNotExist, Proctor.DoesNotExist):
        return redirect('teacher_dashboard')
    
    # Get assigned students
    assigned_students = Student.objects.filter(assigned_proctor=proctor)
    
    # Get all students for assignment
    all_students = Student.objects.filter(department=teacher.department)
    
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        action = request.POST.get('action')
        
        try:
            student = Student.objects.get(id=student_id)
            if action == 'assign':
                student.assigned_proctor = proctor
                student.save()
                messages.success(request, f'Successfully assigned {student.user.get_full_name()}')
            elif action == 'unassign':
                student.assigned_proctor = None
                student.save()
                messages.success(request, f'Successfully unassigned {student.user.get_full_name()}')
        except Student.DoesNotExist:
            messages.error(request, 'Student not found')
    
    context = {
        'assigned_students': assigned_students,
        'all_students': all_students,
        'teacher': teacher,
    }
    return render(request, 'teacher/student_management.html', context)

@login_required
def create_meeting(request):
    if request.user.role != 'teacher':
        return redirect('dashboard')
    
    try:
        teacher = request.user.teacher
    except Teacher.DoesNotExist:
        return redirect('dashboard')
    
    if request.method == 'POST':
        try:
            student_id = request.POST.get('student')
            date = request.POST.get('date')
            time = request.POST.get('time')
            agenda = request.POST.get('agenda')
            summary = request.POST.get('summary')
            
            student = Student.objects.get(id=student_id)
            
            Meeting.objects.create(
                teacher=teacher,
                student=student,
                date=date,
                time=time,
                agenda=agenda,
                summary=summary,
                status='upcoming'
            )
            
            messages.success(request, 'Meeting created successfully')
            return redirect('meeting_management')
        except Exception as e:
            messages.error(request, f'Error creating meeting: {str(e)}')
    
    # Get all students assigned to this teacher's proctor
    proctor = teacher.user.proctor
    students = Student.objects.filter(assigned_proctor=proctor)
    
    context = {
        'students': students,
    }
    return render(request, 'teacher/create_meeting.html', context)

@require_POST
@login_required
def update_meeting_status(request, meeting_id):
    meeting = get_object_or_404(Meeting, id=meeting_id, teacher__user=request.user)
    status = request.POST.get('status')
    if status in dict(Meeting.STATUS_CHOICES):
        meeting.status = status
        meeting.save()
        messages.success(request, 'Meeting status updated successfully.')
    else:
        messages.error(request, 'Invalid status value.')
    return redirect('meeting_management')
