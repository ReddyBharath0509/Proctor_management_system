from django.db import models
from django.conf import settings
from django.utils import timezone

# Create your models here.

class Proctor(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    office_location = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.department}"

class ProctorMeeting(models.Model):
    proctor = models.ForeignKey(Proctor, on_delete=models.CASCADE)
    students = models.ManyToManyField('student.Student', related_name='proctor_meetings')
    date = models.DateField()
    time = models.TimeField(null=True, blank=True, default='09:00:00')
    is_completed = models.BooleanField(default=False)
    is_cancelled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date', 'time']
        unique_together = ['proctor', 'date', 'time']

    def __str__(self):
        return f"Meeting with {self.proctor} on {self.date} at {self.time}"

    def get_status(self):
        if self.is_completed:
            return "Completed"
        elif self.is_cancelled:
            return "Cancelled"
        else:
            return "Upcoming"

class MeetingSummary(models.Model):
    meeting = models.OneToOneField(ProctorMeeting, on_delete=models.CASCADE, related_name='summary')
    summary_text = models.TextField()
    action_items = models.TextField(blank=True, null=True)
    next_meeting_suggestions = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Summary for meeting on {self.meeting.date}"

    class Meta:
        verbose_name_plural = "Meeting Summaries"
