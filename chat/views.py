from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import ChatRoom, Message
from teacher.models import Teacher
from student.models import Student

# Create your views here.

@login_required
def chat_room_list(request):
    if request.user.role == 'teacher':
        teacher = request.user.teacher
        chat_rooms = ChatRoom.objects.filter(teacher=teacher)
    else:
        student = request.user.student
        chat_rooms = ChatRoom.objects.filter(student=student)
    
    context = {
        'chat_rooms': chat_rooms,
    }
    return render(request, 'chat/room_list.html', context)

@login_required
def chat_room(request, room_id):
    chat_room = get_object_or_404(ChatRoom, id=room_id)
    
    # Check if user has access to this chat room
    if request.user.role == 'teacher':
        if chat_room.teacher.user != request.user:
            return redirect('chat_room_list')
    else:
        if chat_room.student.user != request.user:
            return redirect('chat_room_list')
    
    messages = chat_room.messages.all().order_by('timestamp')
    
    context = {
        'chat_room': chat_room,
        'messages': messages,
    }
    return render(request, 'chat/room.html', context)

@login_required
def start_chat(request, user_id):
    if request.user.role == 'teacher':
        teacher = request.user.teacher
        student = get_object_or_404(Student, user_id=user_id)
    else:
        student = request.user.student
        teacher = get_object_or_404(Teacher, user_id=user_id)
    
    # Get or create chat room
    chat_room, created = ChatRoom.objects.get_or_create(
        teacher=teacher,
        student=student
    )
    
    return redirect('chat_room', room_id=chat_room.id)
