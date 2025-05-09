from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from accounts.models import User
from notifications.models import Notification
from student.models import Student, Attendance, Marks, Issue, IssueComment
from teacher.models import Teacher
from proctor.models import Proctor, ProctorMeeting
from .models import TimeSlot
from django.utils import timezone
from accounts.utils import send_email_notification
from .models import RoutineGeneratorSettings
import random
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Q

@login_required
def admin_dashboard(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
    
    total_students = Student.objects.count()
    total_teachers = Teacher.objects.count()
    
    context = {
        'total_students': total_students,
        'total_teachers': total_teachers,
    }
    return render(request, 'admin_panel/dashboard.html', context)

@login_required
def time_slots(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
    
    time_slots = TimeSlot.objects.all().order_by('day', 'time')
    
    context = {
        'time_slots': time_slots,
        'day_choices': TimeSlot.DAY_CHOICES,
        'time_choices': TimeSlot.TIME_CHOICES,
    }
    return render(request, 'admin_panel/time_slots.html', context)

@login_required
def manage_assignments(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
    
    if request.method == 'POST':
        student_id = request.POST.get('student')
        teacher_id = request.POST.get('teacher')
        
        try:
            student = Student.objects.get(id=student_id)
            teacher = Teacher.objects.get(id=teacher_id)
            
            # Get or create proctor instance for the teacher
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
            
            # Assign the proctor to the student
            student.assigned_proctor = proctor
            student.save()
            
            messages.success(request, f'Successfully assigned {student.user.get_full_name()} to {teacher.user.get_full_name()}')
            return redirect('admin_dashboard')
        except (Student.DoesNotExist, Teacher.DoesNotExist):
            messages.error(request, 'Invalid student or teacher selection')
        except Exception as e:
            messages.error(request, f'Error assigning student: {str(e)}')
    
    # Get all unassigned students
    unassigned_students = Student.objects.filter(assigned_proctor__isnull=True)
    # Get all teachers
    teachers = Teacher.objects.all()
    
    # Get all assignments
    assignments = Student.objects.filter(assigned_proctor__isnull=False)
    
    context = {
        'unassigned_students': unassigned_students,
        'teachers': teachers,
        'assignments': assignments,
    }
    return render(request, 'admin_panel/manage_assignments.html', context)

@login_required
def remove_assignment(request, student_id):
    if request.user.role != 'admin':
        return redirect('dashboard')
    
    try:
        student = Student.objects.get(id=student_id)
        teacher_name = student.assigned_proctor.user.get_full_name()
        student.assigned_proctor = None
        student.save()
        messages.success(request, f'Removed assignment for {student.user.get_full_name()} from {teacher_name}')
    except Student.DoesNotExist:
        messages.error(request, 'Student not found')
    
    return redirect('admin_dashboard')

@login_required
def manage_users(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
    
    users = User.objects.all().order_by('-date_joined')
    context = {
        'users': users,
    }
    return render(request, 'admin_panel/manage_users.html', context)

@login_required
def edit_user(request, user_id):
    if request.user.role != 'admin':
        return redirect('dashboard')
    
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.phone_number = request.POST.get('phone_number')
        user.address = request.POST.get('address')
        user.role = request.POST.get('role')
        user.save()
        
        messages.success(request, f'Successfully updated user: {user.get_full_name()}')
        return redirect('admin_dashboard')
    
    context = {
        'user': user,
    }
    return render(request, 'admin_panel/edit_user.html', context)

@login_required
def delete_user(request, user_id):
    if request.user.role != 'admin' and not request.user.is_superuser:
        return redirect('dashboard')
    
    try:
        user_to_delete = User.objects.get(id=user_id)
        
        if request.method == 'POST':
            try:
                # Delete related records based on user role
                if user_to_delete.role == 'student':
                    try:
                        student = user_to_delete.student
                        TimeSlot.objects.filter(student=student).delete()
                        Attendance.objects.filter(student=student).delete()
                        Mark.objects.filter(student=student).delete()
                        Issue.objects.filter(student=student).delete()
                    except:
                        pass  # User doesn't have a student profile
                elif user_to_delete.role == 'teacher':
                    try:
                        teacher = user_to_delete.teacher
                        TimeSlot.objects.filter(teacher=teacher).delete()
                        Meeting.objects.filter(teacher=teacher).delete()
                    except:
                        pass  # User doesn't have a teacher profile
                elif user_to_delete.role == 'proctor':
                    try:
                        proctor = user_to_delete.proctor
                        Student.objects.filter(proctor=proctor).update(proctor=None)
                    except:
                        pass  # User doesn't have a proctor profile
                    
                # Delete notifications
                Notification.objects.filter(user=user_to_delete).delete()
                
                # Delete the user
                user_to_delete.delete()
                messages.success(request, 'User deleted successfully.')
                return render(request, 'admin_panel/user_deleted.html')
            except Exception as e:
                messages.error(request, f'Error deleting user: {str(e)}')
        
        return render(request, 'admin_panel/delete_user.html', {'user': user_to_delete})
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('manage_users')
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')
        return redirect('manage_users')

@login_required
def manage_timetable(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
    
    if request.method == 'POST':
        day = request.POST.get('day')
        time = request.POST.get('time')
        teacher_id = request.POST.get('teacher')
        student_ids = request.POST.getlist('students')
        subject = request.POST.get('subject')
        
        try:
            teacher = Teacher.objects.get(id=teacher_id)
            
            # Check if time slot already exists
            existing_slot = TimeSlot.objects.filter(
                day=int(day),
                time=int(time),
                teacher=teacher
            ).first()
            
            if existing_slot:
                messages.error(request, f'Time slot already exists for {teacher.user.get_full_name()} on {existing_slot.get_day_display()} at {existing_slot.get_time_display()}')
                return redirect('admin_dashboard')
            
            time_slot = TimeSlot.objects.create(
                day=int(day),
                time=int(time),
                teacher=teacher,
                subject=subject
            )
            
            students = Student.objects.filter(id__in=student_ids)
            time_slot.students.set(students)
            
            # Create in-app notifications
            Notification.objects.create(
                user=teacher.user,
                title='New Proctor Meeting Scheduled',
                message=f'You have a new proctor meeting scheduled for {time_slot.get_day_display()} at {time_slot.get_time_display()}',
                notification_type='meeting'
            )
            
            # Send email to teacher
            send_email_notification(
                user=teacher.user,
                template_key='meeting_scheduled',
                context={
                    'user': teacher.user,
                    'day': time_slot.get_day_display(),
                    'time': time_slot.get_time_display(),
                    'students': ', '.join([s.user.get_full_name() for s in students]),
                    'dashboard_url': request.build_absolute_uri(reverse('teacher_timetable'))
                }
            )
            
            for student in students:
                # Create in-app notification
                Notification.objects.create(
                    user=student.user,
                    title='New Proctor Meeting Scheduled',
                    message=f'You have a new proctor meeting scheduled with {teacher.user.get_full_name()} on {time_slot.get_day_display()} at {time_slot.get_time_display()}',
                    notification_type='meeting'
                )
                
                # Send email to student
                send_email_notification(
                    user=student.user,
                    template_key='meeting_scheduled',
                    context={
                        'user': student.user,
                        'day': time_slot.get_day_display(),
                        'time': time_slot.get_time_display(),
                        'teacher': teacher.user.get_full_name(),
                        'dashboard_url': request.build_absolute_uri(reverse('student_timetable'))
                    }
                )
            
            messages.success(request, 'Successfully created time slot')
            return redirect('admin_dashboard')
        except Exception as e:
            messages.error(request, f'Error creating time slot: {str(e)}')
            return redirect('admin_dashboard')
    
    # Get all teachers and students
    teachers = Teacher.objects.all()
    students = Student.objects.all()
    
    context = {
        'teachers': teachers,
        'students': students,
        'day_choices': TimeSlot.DAY_CHOICES,
        'time_choices': TimeSlot.TIME_CHOICES,
    }
    return render(request, 'admin_panel/manage_timetable.html', context)

@login_required
def delete_time_slot(request, slot_id):
    if request.user.role != 'admin':
        return redirect('dashboard')
    
    time_slot = get_object_or_404(TimeSlot, id=slot_id)
    
    if request.method == 'POST':
        try:
            # Store references for cleanup
            teacher = time_slot.teacher
            students = list(time_slot.students.all())
            
            # Delete the time slot
            time_slot.delete()
            
            # Delete related notifications
            Notification.objects.filter(
                user__in=[teacher.user] + [s.user for s in students],
                notification_type='meeting',
                title__in=['Proctor Meeting Updated', 'Proctor Meeting Deleted']
            ).delete()
            
            # Create deletion notifications
            Notification.objects.create(
                user=teacher.user,
                title='Proctor Meeting Deleted',
                message=f'Your proctor meeting on {time_slot.get_day_display()} at {time_slot.get_time_display()} has been deleted',
                notification_type='meeting'
            )
            
            for student in students:
                Notification.objects.create(
                    user=student.user,
                    title='Proctor Meeting Deleted',
                    message=f'Your proctor meeting with {teacher.user.get_full_name()} on {time_slot.get_day_display()} at {time_slot.get_time_display()} has been deleted',
                    notification_type='meeting'
                )
            
            messages.success(request, 'Time slot deleted successfully')
            return redirect('time_slots')
            
        except Exception as e:
            messages.error(request, f'Error deleting time slot: {str(e)}')
            return redirect('time_slots')
    
    context = {
        'time_slot': time_slot,
    }
    return render(request, 'admin_panel/delete_time_slot.html', context)

@login_required
def routine_generator_settings(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
    
    settings, created = RoutineGeneratorSettings.objects.get_or_create(pk=1)
    
    if request.method == 'POST':
        settings.students_per_slot = request.POST.get('students_per_slot', 5)
        settings.min_slots_per_teacher = request.POST.get('min_slots_per_teacher', 2)
        settings.max_slots_per_teacher = request.POST.get('max_slots_per_teacher', 5)
        settings.preferred_days = [int(day) for day in request.POST.getlist('preferred_days')]
        settings.preferred_times = [int(time) for time in request.POST.getlist('preferred_times')]
        settings.save()
        
        messages.success(request, 'Routine generator settings updated successfully.')
        return redirect('routine_generator_settings')
    
    context = {
        'settings': settings,
        'day_choices': TimeSlot.DAY_CHOICES,
        'time_choices': TimeSlot.TIME_CHOICES,
    }
    return render(request, 'admin_panel/routine_generator_settings.html', context)

@login_required
def generate_routine(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
    
    settings = get_object_or_404(RoutineGeneratorSettings, pk=1)
    teachers = Teacher.objects.all()
    students = Student.objects.all()
    
    if request.method == 'POST':
        try:
            # Clear existing time slots
            TimeSlot.objects.all().delete()
            
            # Generate new routine
            routine = generate_optimal_routine(teachers, students, settings)
            
            if routine:
                messages.success(request, 'Routine generated successfully.')
            else:
                messages.error(request, 'Failed to generate routine. Please check the settings and try again.')
            
            return redirect('view_routine')
            
        except Exception as e:
            messages.error(request, f'Error generating routine: {str(e)}')
            return redirect('routine_generator_settings')
    
    context = {
        'settings': settings,
        'teachers_count': teachers.count(),
        'students_count': students.count(),
    }
    return render(request, 'admin_panel/generate_routine.html', context)

def generate_optimal_routine(teachers, students, settings):
    """
    Generate an optimal routine based on the given settings and constraints.
    Returns True if successful, False otherwise.
    """
    try:
        # Create a list of all possible time slots
        time_slots = []
        for day in settings.preferred_days:
            for time in settings.preferred_times:
                time_slots.append((day, time))
        
        # Shuffle time slots to randomize distribution
        random.shuffle(time_slots)
        
        # Assign students to teachers
        student_groups = []
        current_group = []
        
        for student in students:
            current_group.append(student)
            if len(current_group) >= settings.students_per_slot:
                student_groups.append(current_group)
                current_group = []
        
        if current_group:
            student_groups.append(current_group)
        
        # Assign time slots to teachers
        teacher_slots = {teacher: 0 for teacher in teachers}
        slot_index = 0
        
        for group in student_groups:
            # Find teacher with minimum slots
            min_slots_teacher = min(teacher_slots.items(), key=lambda x: x[1])[0]
            
            if teacher_slots[min_slots_teacher] >= settings.max_slots_per_teacher:
                continue
            
            # Create time slot
            day, time = time_slots[slot_index % len(time_slots)]
            TimeSlot.objects.create(
                day=day,
                time=time,
                teacher=min_slots_teacher
            ).students.set(group)
            
            teacher_slots[min_slots_teacher] += 1
            slot_index += 1
        
        return True
        
    except Exception as e:
        print(f"Error in generate_optimal_routine: {str(e)}")
        return False

@login_required
def view_routine(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
    
    time_slots = TimeSlot.objects.all().order_by('day', 'time')
    current_time = timezone.now()
    current_day = current_time.weekday()  # Monday is 0, Sunday is 6
    current_hour = current_time.hour
    
    # Group time slots by day and add status
    routine_by_day = {}
    for slot in time_slots:
        if slot.day not in routine_by_day:
            routine_by_day[slot.day] = []
        
        # Determine if the meeting is upcoming or past
        slot_status = 'upcoming'
        if slot.day < current_day:
            slot_status = 'past'
        elif slot.day == current_day:
            # Convert time slot to 24-hour format for comparison
            slot_hour = int(slot.time.split(':')[0])
            if slot_hour < current_hour:
                slot_status = 'past'
        
        # Add status to the slot
        slot.status = slot_status
        routine_by_day[slot.day].append(slot)
    
    context = {
        'routine_by_day': routine_by_day,
        'day_choices': dict(TimeSlot.DAY_CHOICES),
        'time_choices': dict(TimeSlot.TIME_CHOICES),
        'current_day': current_day,
        'current_time': current_time,
    }
    return render(request, 'admin_panel/view_routine.html', context)

@login_required
def add_time_slot(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
    
    if request.method == 'POST':
        day = request.POST.get('day')
        time = request.POST.get('time')
        teacher_id = request.POST.get('teacher')
        student_ids = request.POST.getlist('students')
        
        try:
            teacher = Teacher.objects.get(id=teacher_id)
            
            # Check if time slot already exists
            existing_slot = TimeSlot.objects.filter(
                day=int(day),
                time=int(time),
                teacher=teacher
            ).first()
            
            if existing_slot:
                messages.error(request, f'Time slot already exists for {teacher.user.get_full_name()} on {existing_slot.get_day_display()} at {existing_slot.get_time_display()}')
                return redirect('time_slots')
            
            time_slot = TimeSlot.objects.create(
                day=int(day),
                time=int(time),
                teacher=teacher
            )
            
            students = Student.objects.filter(id__in=student_ids)
            time_slot.students.set(students)
            
            # Create in-app notifications
            Notification.objects.create(
                user=teacher.user,
                title='New Proctor Meeting Scheduled',
                message=f'You have a new proctor meeting scheduled for {time_slot.get_day_display()} at {time_slot.get_time_display()}',
                notification_type='meeting'
            )
            
            # Send email to teacher
            send_email_notification(
                user=teacher.user,
                template_key='meeting_scheduled',
                context={
                    'user': teacher.user,
                    'day': time_slot.get_day_display(),
                    'time': time_slot.get_time_display(),
                    'students': ', '.join([s.user.get_full_name() for s in students]),
                    'dashboard_url': request.build_absolute_uri(reverse('teacher_timetable'))
                }
            )
            
            for student in students:
                # Create in-app notification
                Notification.objects.create(
                    user=student.user,
                    title='New Proctor Meeting Scheduled',
                    message=f'You have a new proctor meeting scheduled with {teacher.user.get_full_name()} on {time_slot.get_day_display()} at {time_slot.get_time_display()}',
                    notification_type='meeting'
                )
                
                # Send email to student
                send_email_notification(
                    user=student.user,
                    template_key='meeting_scheduled',
                    context={
                        'user': student.user,
                        'day': time_slot.get_day_display(),
                        'time': time_slot.get_time_display(),
                        'teacher': teacher.user.get_full_name(),
                        'dashboard_url': request.build_absolute_uri(reverse('student_timetable'))
                    }
                )
            
            messages.success(request, 'Successfully created time slot')
            return redirect('time_slots')
        except Exception as e:
            messages.error(request, f'Error creating time slot: {str(e)}')
            return redirect('time_slots')
    
    # Get all teachers and students
    teachers = Teacher.objects.all()
    students = Student.objects.all()
    
    context = {
        'teachers': teachers,
        'students': students,
        'day_choices': TimeSlot.DAY_CHOICES,
        'time_choices': TimeSlot.TIME_CHOICES,
    }
    return render(request, 'admin_panel/add_time_slot.html', context)

@login_required
def edit_time_slot(request, slot_id):
    if request.user.role != 'admin':
        return redirect('dashboard')
    
    time_slot = get_object_or_404(TimeSlot, id=slot_id)
    settings = RoutineGeneratorSettings.objects.first()
    
    if request.method == 'POST':
        day = request.POST.get('day')
        time = request.POST.get('time')
        teacher_id = request.POST.get('teacher')
        student_ids = request.POST.getlist('students')
        is_active = request.POST.get('is_active') == 'on'
        
        try:
            # Validate teacher selection
            if not teacher_id:
                raise ValueError('Please select a teacher')
            
            teacher = Teacher.objects.get(id=teacher_id)
            
            # Validate number of students
            if len(student_ids) > settings.students_per_slot:
                raise ValueError(f'Maximum {settings.students_per_slot} students allowed per slot')
            
            # Check if time slot already exists (excluding the current one)
            existing_slot = TimeSlot.objects.filter(
                day=int(day),
                time=int(time),
                teacher=teacher
            ).exclude(id=slot_id).first()
            
            if existing_slot:
                raise ValueError(f'Time slot already exists for {teacher.user.get_full_name()} on {existing_slot.get_day_display()} at {existing_slot.get_time_display()}')
            
            # Update time slot
            time_slot.day = int(day)
            time_slot.time = int(time)
            time_slot.teacher = teacher
            time_slot.is_active = is_active
            time_slot.save()
            
            # Update students
            students = Student.objects.filter(id__in=student_ids)
            time_slot.students.set(students)
            
            # Delete old notifications
            Notification.objects.filter(
                user__in=[teacher.user] + [s.user for s in time_slot.students.all()],
                notification_type='meeting',
                title='Proctor Meeting Updated'
            ).delete()
            
            # Create new notifications
            Notification.objects.create(
                user=teacher.user,
                title='Proctor Meeting Updated',
                message=f'Your proctor meeting has been updated to {time_slot.get_day_display()} at {time_slot.get_time_display()}',
                notification_type='meeting'
            )
            
            # Send email to teacher
            send_email_notification(
                user=teacher.user,
                template_key='meeting_updated',
                context={
                    'user': teacher.user,
                    'day': time_slot.get_day_display(),
                    'time': time_slot.get_time_display(),
                    'students': ', '.join([s.user.get_full_name() for s in students]),
                    'dashboard_url': request.build_absolute_uri(reverse('teacher_timetable'))
                }
            )
            
            for student in students:
                # Create in-app notification
                Notification.objects.create(
                    user=student.user,
                    title='Proctor Meeting Updated',
                    message=f'Your proctor meeting with {teacher.user.get_full_name()} has been updated to {time_slot.get_day_display()} at {time_slot.get_time_display()}',
                    notification_type='meeting'
                )
                
                # Send email to student
                send_email_notification(
                    user=student.user,
                    template_key='meeting_updated',
                    context={
                        'user': student.user,
                        'day': time_slot.get_day_display(),
                        'time': time_slot.get_time_display(),
                        'teacher': teacher.user.get_full_name(),
                        'dashboard_url': request.build_absolute_uri(reverse('student_timetable'))
                    }
                )
            
            messages.success(request, 'Time slot updated successfully')
            return redirect('time_slots')
            
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('edit_time_slot', slot_id=slot_id)
        except Exception as e:
            messages.error(request, f'Error updating time slot: {str(e)}')
            return redirect('edit_time_slot', slot_id=slot_id)
    
    # Get all teachers and students
    teachers = Teacher.objects.all()
    students = Student.objects.all()
    
    context = {
        'time_slot': time_slot,
        'teachers': teachers,
        'students': students,
        'day_choices': TimeSlot.DAY_CHOICES,
        'time_choices': TimeSlot.TIME_CHOICES,
        'max_students': settings.students_per_slot if settings else 5,
    }
    return render(request, 'admin_panel/edit_time_slot.html', context)
