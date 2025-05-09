from django.contrib import admin
from .models import ProctorMeeting

@admin.register(ProctorMeeting)
class ProctorMeetingAdmin(admin.ModelAdmin):
    list_display = ('proctor', 'date', 'time', 'is_completed', 'is_cancelled')
    list_filter = ('is_completed', 'is_cancelled', 'date', 'time')
    search_fields = ('proctor__user__username', 'students__user__username')
    filter_horizontal = ('students',)
    ordering = ('-date', '-time')
