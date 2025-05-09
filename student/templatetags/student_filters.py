from django import template
from chat.models import Message

register = template.Library()

@register.filter
def unread_messages_count(room, user):
    return Message.objects.filter(
        room=room,
        is_read=False
    ).exclude(sender=user).count() 