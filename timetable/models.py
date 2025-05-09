from django.db import models
from accounts.models import User
from teacher.models import Teacher
from student.models import Student

class TimeSlot(models.Model):
    DAY_CHOICES = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
    ]
    
    TIME_SLOTS = [
        ('09:00-10:00', '09:00 AM - 10:00 AM'),
        ('10:00-11:00', '10:00 AM - 11:00 AM'),
        ('11:00-12:00', '11:00 AM - 12:00 PM'),
        ('12:00-13:00', '12:00 PM - 01:00 PM'),
        ('14:00-15:00', '02:00 PM - 03:00 PM'),
        ('15:00-16:00', '03:00 PM - 04:00 PM'),
    ]
    
    day = models.CharField(max_length=10, choices=DAY_CHOICES)
    time = models.CharField(max_length=20, choices=TIME_SLOTS)
    
    class Meta:
        unique_together = ['day', 'time']
    
    def __str__(self):
        return f"{self.get_day_display()} - {self.get_time_display()}"

class Room(models.Model):
    name = models.CharField(max_length=50)
    capacity = models.IntegerField()
    is_lab = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.name} ({self.capacity} capacity)"

class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    credits = models.IntegerField()
    department = models.CharField(max_length=50)
    semester = models.IntegerField()
    
    def __str__(self):
        return f"{self.code} - {self.name}"

class Schedule(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)
    semester = models.IntegerField()
    department = models.CharField(max_length=50)
    is_lab = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['time_slot', 'room', 'semester', 'department']
    
    def __str__(self):
        return f"{self.subject.name} - {self.teacher.user.get_full_name()} - {self.time_slot}"

class Timetable(models.Model):
    semester = models.IntegerField()
    department = models.CharField(max_length=50)
    academic_year = models.CharField(max_length=9)  # e.g., "2023-2024"
    schedules = models.ManyToManyField(Schedule)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['semester', 'department', 'academic_year']
    
    def __str__(self):
        return f"{self.department} - Semester {self.semester} ({self.academic_year})" 