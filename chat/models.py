from django.db import models
from accounts.models import User
from teacher.models import Teacher
from student.models import Student

class ChatRoom(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='chat_rooms')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='chat_rooms')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['teacher', 'student']
        ordering = ['-updated_at']

    def __str__(self):
        return f"Chat between {self.teacher.user.get_full_name()} and {self.student.user.get_full_name()}"

class Message(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'

    def __str__(self):
        return ""  # Return empty string to prevent popups
