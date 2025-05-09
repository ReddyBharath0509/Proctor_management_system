from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

def send_email_notification(user, template_key, context):
    """
    Send an email notification to a user using the specified template.
    
    Args:
        user: The user to send the email to
        template_key: The key to look up the email template in settings.EMAIL_TEMPLATES
        context: Dictionary of context variables for the template
    """
    if not user.email:
        return False
    
    template_config = settings.EMAIL_TEMPLATES.get(template_key)
    if not template_config:
        return False
    
    subject = template_config['subject']
    template = template_config['template']
    
    # Render the email template
    html_message = render_to_string(template, context)
    
    # Send the email
    try:
        send_mail(
            subject=subject,
            message='',  # Plain text version (empty as we're using HTML)
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False 