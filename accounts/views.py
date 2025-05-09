from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.urls import reverse
from datetime import timedelta
from .forms import UserRegistrationForm, UserLoginForm, PasswordResetForm, SetPasswordForm, UserProfileForm
from student.models import Student
from teacher.models import Teacher
from .models import User, EmailVerification
from .utils import send_email_notification
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from notifications.models import Notification
import uuid

# Create your views here.

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'accounts/home.html')

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create appropriate profile based on role
            if user.role == 'student':
                Student.objects.create(
                    user=user,
                    roll_number=f"STU{user.id:03d}",
                    semester=form.cleaned_data.get('semester', 1),
                    department=form.cleaned_data.get('department', 'Not Assigned')
                )
            elif user.role == 'teacher':
                Teacher.objects.create(
                    user=user,
                    department=form.cleaned_data.get('department', 'Not Assigned'),
                    designation="Not Assigned"
                )
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            print(f"Attempting to authenticate user: {username}")  # Debug log
            
            user = authenticate(username=username, password=password)
            if user:
                print(f"User authenticated successfully: {user.username}")  # Debug log
                login(request, user)
                messages.success(request, 'Login successful!')
                return redirect('dashboard')
            else:
                print(f"Authentication failed for user: {username}")  # Debug log
                # Check if user exists
                try:
                    user_exists = User.objects.get(username=username)
                    print(f"User exists but password is incorrect: {username}")  # Debug log
                except User.DoesNotExist:
                    print(f"User does not exist: {username}")  # Debug log
                messages.error(request, 'Invalid username or password.')
    else:
        form = UserLoginForm()
    
    # Get unread notifications count for authenticated users
    unread_notifications_count = 0
    if request.user.is_authenticated:
        unread_notifications_count = Notification.objects.filter(user=request.user, is_read=False).count()
    
    return render(request, 'accounts/login.html', {
        'form': form,
        'unread_notifications_count': unread_notifications_count
    })

@login_required
def user_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('login')

@login_required
def dashboard(request):
    if request.user.role == 'student':
        return redirect('student_dashboard')
    elif request.user.role == 'teacher':
        return redirect('teacher_dashboard')
    else:
        return redirect('admin_dashboard')

@login_required
def notifications(request):
    notifications = Notification.objects.filter(user=request.user)
    unread_count = notifications.filter(is_read=False).count()
    
    context = {
        'notifications': notifications,
        'unread_count': unread_count,
    }
    return render(request, 'accounts/notifications.html', context)

@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect('notifications')

def password_reset_request(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                # Generate password reset token
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                reset_url = request.build_absolute_uri(f'/reset/{uid}/{token}/')
                
                # Send password reset email
                subject = 'Password Reset Requested'
                message = f'Hello {user.get_full_name()},\n\n'
                message += f'You have requested to reset your password. Please click the link below to reset it:\n\n'
                message += f'{reset_url}\n\n'
                message += 'If you did not request this, please ignore this email.\n\n'
                message += 'Best regards,\nProctor Management System'
                
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                return redirect('password_reset_done')
            except User.DoesNotExist:
                messages.error(request, 'No user found with this email address.')
    else:
        form = PasswordResetForm()
    return render(request, 'accounts/password_reset_request.html', {'form': form})

def password_reset_done(request):
    return render(request, 'accounts/password_reset_done.html')

def password_reset_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Your password has been reset successfully.')
                return redirect('password_reset_complete')
        else:
            form = SetPasswordForm(user)
        return render(request, 'accounts/password_reset_confirm.html', {'form': form})
    else:
        return render(request, 'accounts/password_reset_invalid.html')

def password_reset_complete(request):
    return render(request, 'accounts/password_reset_complete.html')

def verify_email(request, token):
    try:
        verification = EmailVerification.objects.get(
            token=token,
            is_verified=False,
            expires_at__gt=timezone.now()
        )
        
        # Mark email as verified
        user = verification.user
        user.is_email_verified = True
        user.save()
        
        verification.is_verified = True
        verification.save()
        
        messages.success(request, 'Your email has been verified successfully!')
        return redirect('login')
    except EmailVerification.DoesNotExist:
        messages.error(request, 'Invalid or expired verification link.')
        return redirect('login')

def resend_verification(request):
    if not request.user.is_authenticated:
        messages.error(request, 'Please log in to resend verification email.')
        return redirect('login')
    
    if request.user.is_email_verified:
        messages.info(request, 'Your email is already verified.')
        return redirect('dashboard')
    
    try:
        # Delete any existing verification
        EmailVerification.objects.filter(user=request.user).delete()
        
        # Create new verification
        verification = EmailVerification.objects.create(
            user=request.user,
            expires_at=timezone.now() + timedelta(days=settings.EMAIL_VERIFICATION_EXPIRY_DAYS)
        )
        
        # Send verification email
        verification_url = request.build_absolute_uri(
            reverse('verify_email', kwargs={'token': verification.token})
        )
        
        send_email_notification(
            user=request.user,
            template_key='verify_email',
            context={
                'user': request.user,
                'verification_url': verification_url
            }
        )
        
        messages.success(request, 'Verification email has been sent. Please check your inbox.')
        return redirect('dashboard')
    except Exception as e:
        messages.error(request, 'Failed to send verification email. Please try again later.')
        return redirect('dashboard')

@login_required
def profile(request):
    user = request.user
    context = {
        'user': user,
        'profile': user.get_profile(),  # This will return either Student or Teacher profile
    }
    return render(request, 'accounts/profile.html', context)

@login_required
def edit_profile(request):
    user = request.user
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=user)
    
    context = {
        'form': form,
        'user': user,
    }
    return render(request, 'accounts/edit_profile.html', context)
