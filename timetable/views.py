from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import TimeSlot, Room, Subject, Schedule, Timetable
from teacher.models import Teacher
from student.models import Student

def is_admin(user):
    return user.role == 'admin'

@login_required
@user_passes_test(is_admin)
def timetable_dashboard(request):
    timetables = Timetable.objects.all().order_by('-academic_year', 'department', 'semester')
    context = {
        'timetables': timetables,
    }
    return render(request, 'timetable/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def create_timetable(request):
    if request.method == 'POST':
        semester = request.POST.get('semester')
        department = request.POST.get('department')
        academic_year = request.POST.get('academic_year')
        
        # Create timetable
        timetable = Timetable.objects.create(
            semester=semester,
            department=department,
            academic_year=academic_year
        )
        
        # Get all subjects for the department and semester
        subjects = Subject.objects.filter(department=department, semester=semester)
        
        # Create schedules for each subject
        for subject in subjects:
            teacher_id = request.POST.get(f'teacher_{subject.id}')
            room_id = request.POST.get(f'room_{subject.id}')
            time_slot_id = request.POST.get(f'time_slot_{subject.id}')
            
            if teacher_id and room_id and time_slot_id:
                teacher = Teacher.objects.get(id=teacher_id)
                room = Room.objects.get(id=room_id)
                time_slot = TimeSlot.objects.get(id=time_slot_id)
                
                # Check for conflicts
                if not Schedule.objects.filter(
                    time_slot=time_slot,
                    room=room,
                    semester=semester,
                    department=department
                ).exists():
                    Schedule.objects.create(
                        subject=subject,
                        teacher=teacher,
                        room=room,
                        time_slot=time_slot,
                        semester=semester,
                        department=department,
                        is_lab=subject.is_lab
                    )
                else:
                    messages.warning(request, f'Conflict detected for {subject.name} at {time_slot}')
        
        messages.success(request, 'Timetable created successfully!')
        return redirect('timetable_dashboard')
    
    # Get all departments and semesters
    departments = Subject.objects.values_list('department', flat=True).distinct()
    semesters = Subject.objects.values_list('semester', flat=True).distinct()
    
    # Get all rooms and time slots
    rooms = Room.objects.all()
    time_slots = TimeSlot.objects.all()
    
    # Get all teachers
    teachers = Teacher.objects.all()
    
    context = {
        'departments': departments,
        'semesters': semesters,
        'rooms': rooms,
        'time_slots': time_slots,
        'teachers': teachers,
        'subjects': Subject.objects.all(),  # Will be filtered in template
    }
    return render(request, 'timetable/create_timetable.html', context)

@login_required
def view_timetable(request, timetable_id):
    timetable = get_object_or_404(Timetable, id=timetable_id)
    
    # Get all time slots
    time_slots = TimeSlot.objects.all().order_by('day', 'time')
    
    # Get all schedules for this timetable
    schedules = timetable.schedules.all()
    
    # Create a matrix of schedules
    schedule_matrix = {}
    for time_slot in time_slots:
        schedule_matrix[time_slot.id] = {}
        for day in TimeSlot.DAY_CHOICES:
            schedule_matrix[time_slot.id][day[0]] = schedules.filter(
                time_slot__day=day[0],
                time_slot__time=time_slot.time
            ).first()
    
    context = {
        'timetable': timetable,
        'time_slots': time_slots,
        'schedule_matrix': schedule_matrix,
        'days': [day[1] for day in TimeSlot.DAY_CHOICES],
    }
    return render(request, 'timetable/view_timetable.html', context)

@login_required
def student_timetable(request):
    student = request.user.student
    timetable = Timetable.objects.filter(
        department=student.department,
        semester=student.semester
    ).first()
    
    if not timetable:
        messages.warning(request, 'No timetable found for your department and semester.')
        return redirect('student_dashboard')
    
    return view_timetable(request, timetable.id)

@login_required
def teacher_timetable(request):
    teacher = request.user.teacher
    schedules = Schedule.objects.filter(teacher=teacher)
    
    # Get all time slots
    time_slots = TimeSlot.objects.all().order_by('day', 'time')
    
    # Create a matrix of schedules
    schedule_matrix = {}
    for time_slot in time_slots:
        schedule_matrix[time_slot.id] = {}
        for day in TimeSlot.DAY_CHOICES:
            schedule_matrix[time_slot.id][day[0]] = schedules.filter(
                time_slot__day=day[0],
                time_slot__time=time_slot.time
            ).first()
    
    # Get unique subjects
    subjects = Subject.objects.filter(schedule__teacher=teacher).distinct()
    
    # Calculate statistics
    total_classes = schedules.count()
    total_students = sum(schedule.timetable.schedules.count() for schedule in schedules)
    departments = set(schedule.department for schedule in schedules)
    
    context = {
        'teacher': teacher,
        'time_slots': time_slots,
        'schedule_matrix': schedule_matrix,
        'days': [day[1] for day in TimeSlot.DAY_CHOICES],
        'subjects': subjects,
        'total_classes': total_classes,
        'total_students': total_students,
        'departments': departments,
    }
    return render(request, 'timetable/teacher_timetable.html', context) 