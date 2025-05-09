from django.contrib import admin
from .models import Teacher, Meeting

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'designation')
    list_filter = ('department', 'designation')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'department')
    ordering = ('department',)

@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'student', 'date', 'time')
    list_filter = ('date', 'time')
    search_fields = ('teacher__user__username', 'student__user__username')
    ordering = ('-date', '-time')
