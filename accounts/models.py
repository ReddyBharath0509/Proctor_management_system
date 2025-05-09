from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid
from django.utils import timezone

class User(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('admin', 'Admin'),
    )
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)
    password_reset_token = models.CharField(max_length=32, null=True, blank=True)
    password_reset_expires = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return self.get_full_name()

    def get_profile(self):
        if self.role == 'student':
            return self.student
        elif self.role == 'teacher':
            return self.teacher
        return None

class EmailVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"Verification for {self.user.get_full_name()}"
