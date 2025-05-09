from django.db import models
from teacher.models import Teacher
from student.models import Student

# Create your models here.

class TimeSlot(models.Model):
    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    TIME_CHOICES = [
        (1, '9:00 AM - 10:00 AM'),
        (2, '10:00 AM - 11:00 AM'),
        (3, '11:00 AM - 12:00 PM'),
        (4, '12:00 PM - 1:00 PM'),
        (5, '2:00 PM - 3:00 PM'),
        (6, '3:00 PM - 4:00 PM'),
        (7, '4:00 PM - 5:00 PM'),
    ]

    day = models.IntegerField(choices=DAY_CHOICES)
    time = models.IntegerField(choices=TIME_CHOICES)
    teacher = models.ForeignKey('teacher.Teacher', on_delete=models.CASCADE, related_name='time_slots')
    students = models.ManyToManyField('student.Student', related_name='time_slots')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    subject = models.CharField(max_length=100, default="", blank=True)

    class Meta:
        unique_together = ['day', 'time', 'teacher']
        ordering = ['day', 'time']

    def __str__(self):
        return f"{self.get_day_display()} - {self.get_time_display()} - {self.teacher.user.get_full_name()}"

    def get_day_display(self):
        try:
            return dict(self.DAY_CHOICES)[self.day]
        except (KeyError, TypeError):
            return 'Unknown Day'

    def get_time_display(self):
        try:
            return dict(self.TIME_CHOICES)[self.time]
        except (KeyError, TypeError):
            return 'Unknown Time'

    def get_students_count(self):
        return self.students.count()

    def get_attendance_records(self, date):
        """Get attendance records for all students in this time slot for a specific date"""
        from student.models import Attendance
        return Attendance.objects.filter(
            student__in=self.students.all(),
            date=date,
            subject=f'Proctor Meeting - {self.get_time_display()}'
        )

class RoutineGeneratorSettings(models.Model):
    students_per_slot = models.IntegerField(default=5, help_text="Maximum number of students per time slot")
    min_slots_per_teacher = models.IntegerField(default=2, help_text="Minimum number of slots each teacher should have")
    max_slots_per_teacher = models.IntegerField(default=5, help_text="Maximum number of slots each teacher can have")
    preferred_days = models.JSONField(default=list, help_text="List of preferred days for scheduling (0-6, where 0 is Monday)")
    preferred_times = models.JSONField(default=list, help_text="List of preferred time slots for scheduling (1-7)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # New fields for constraints
    teacher_constraints = models.JSONField(default=dict, help_text="Constraints for specific teachers (e.g., {'teacher_id': {'preferred_days': [0,1,2], 'preferred_times': [1,2,3]}})")
    student_constraints = models.JSONField(default=dict, help_text="Constraints for specific students (e.g., {'student_id': {'preferred_days': [0,1,2], 'preferred_times': [1,2,3]}})")
    avoid_conflicts = models.BooleanField(default=True, help_text="Avoid scheduling conflicts for teachers and students")
    balance_load = models.BooleanField(default=True, help_text="Balance the load among teachers")
    
    # Proctor details configuration
    use_existing_proctors = models.BooleanField(default=True, help_text="Use existing proctor assignments when generating routine")
    allow_proctor_changes = models.BooleanField(default=False, help_text="Allow changes to existing proctor assignments")
    
    # Student semester configuration
    semester_filter = models.JSONField(default=list, help_text="List of semesters to include in routine generation")
    group_by_semester = models.BooleanField(default=False, help_text="Group students by semester when generating routine")

    class Meta:
        verbose_name = "Routine Generator Settings"
        verbose_name_plural = "Routine Generator Settings"

    def __str__(self):
        return f"Routine Generator Settings (Updated: {self.updated_at})"

    def get_preferred_days_display(self):
        return [dict(TimeSlot.DAY_CHOICES)[day] for day in self.preferred_days]

    def get_preferred_times_display(self):
        return [dict(TimeSlot.TIME_CHOICES)[time] for time in self.preferred_times]
