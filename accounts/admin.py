from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, EmailVerification

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff', 'is_email_verified')
    list_filter = ('role', 'is_staff', 'is_email_verified')
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'phone_number', 'address', 'is_email_verified')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('role', 'phone_number', 'address', 'is_email_verified')}),
    )

admin.site.register(User, CustomUserAdmin)
admin.site.register(EmailVerification)
