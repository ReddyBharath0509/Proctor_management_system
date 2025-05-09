from django.contrib import admin
from .models import Student, Attendance, Marks

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('user', 'roll_number', 'department', 'semester', 'assigned_proctor')
    list_filter = ('department', 'semester')
    search_fields = ('user__username', 'roll_number', 'user__first_name', 'user__last_name')
    ordering = ('roll_number',)

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'subject', 'is_present')
    list_filter = ('is_present', 'date', 'subject')
    search_fields = ('student__user__username', 'student__roll_number', 'subject')
    ordering = ('-date',)

@admin.register(Marks)
class MarksAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'marks', 'semester', 'date')
    list_filter = ('semester', 'subject', 'date')
    search_fields = ('student__user__username', 'student__roll_number', 'subject')
    ordering = ('-date',)
