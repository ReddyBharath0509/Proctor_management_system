from django.db import models
from django.conf import settings
from django.utils import timezone
from teacher.models import Teacher
from accounts.models import User
from proctor.models import Proctor

class Student(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    roll_number = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100)
    semester = models.IntegerField()
    assigned_proctor = models.ForeignKey('proctor.Proctor', on_delete=models.SET_NULL, null=True, related_name='assigned_students')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    date_of_birth = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.roll_number}"

class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    subject = models.CharField(max_length=100, null=True, blank=True)
    date = models.DateField()
    is_present = models.BooleanField(default=False)
    remarks = models.TextField(blank=True)

    class Meta:
        unique_together = ['student', 'subject', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.subject or 'General'} - {self.date}"

class Marks(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='marks')
    subject = models.CharField(max_length=100)
    marks = models.DecimalField(max_digits=5, decimal_places=2)
    semester = models.IntegerField()
    date = models.DateField(default=timezone.now)
    remarks = models.TextField(blank=True)

    class Meta:
        unique_together = ['student', 'subject', 'semester']
        ordering = ['-date']

    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.subject} - {self.marks}"

class Issue(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='issues')
    title = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_issues')
    resolution_notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} - {self.student.user.get_full_name()}"

    class Meta:
        ordering = ['-created_at']

class IssueComment(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.user.get_full_name()} on {self.issue.title}"
