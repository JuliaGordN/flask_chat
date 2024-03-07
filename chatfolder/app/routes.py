
# app/routes.py
from flask import Blueprint, redirect, url_for, request, session, flash, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room
from . import socketio, db
from .models import Message, Chatroom, Invitation
from flask_login import current_user, login_required
from .logger import setup_chatroom_logger
import os
from datetime import datetime

main = Blueprint('main', __name__)

# Основний роут
@main.route('/')
def index():
    return render_template('login.html')
# Роут стоврення кімнат
@main.route('/create_room', methods=['POST'])
@login_required
def create_room():
    room_name = request.form.get('room_name')
    is_invitation_only = request.form.get('is_invitation_only') == 'on'  # Перевірка чи кімната тільки з запрошеннями

    if room_name:
        existing_room = Chatroom.query.filter_by(name=room_name).first()
        if existing_room is None:
            new_room = Chatroom(name=room_name, is_invitation_only=is_invitation_only)
            db.session.add(new_room)
            db.session.commit()
            flash('Chat room created successfully.', 'success')
            return redirect(url_for('main.chatroom', chatroom_id=new_room.id))
        else:
            flash('A room with this name already exists.', 'error')
    else:
        flash('Room name cannot be empty.', 'error')
    return redirect(url_for('main.create_room_form'))

@main.route('/create_room_form')
@login_required
def create_room_form():
    return render_template('create_chatroom.html')

def log_message(chatroom_name, message):
    log_directory = os.path.join(os.getcwd(), 'logs')
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)
    
    log_filename = os.path.join(log_directory, f"{chatroom_name}.log")
    with open(log_filename, 'a') as log_file:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_file.write(f"{timestamp} - {message['username']}: {message['message']}\n")

@socketio.on('send_message')
def handle_send_message_event(data):
    logger = setup_chatroom_logger(data['chatroom_id'])
    # Створення і запис повідомлення в базу
    message = Message(
        body=data['message'],
        user_id=current_user.id,
        chatroom_id=data['chatroom_id']
    )
    db.session.add(message)
    db.session.commit()
    
    # Логування повідолмень
    
    logger.info(f"{data['username']}: {data['message']}")  # Прямо передаем значения в метод логгирования
    emit('receive_message', {
        'message': message.body,
        'username': current_user.username,
        'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'color': session.get('color', '#000')  # Пример использования цвета из сессии
    }, room=data['chatroom_id'])

user_rooms = {}

@socketio.on('join')
def on_join(data):
    join_room(data['chatroom_id'])
    # Зберігання інформації про кімнату і ім'я користувача
    user_rooms[request.sid] = {
        'chatroom_id': data['chatroom_id'],
        'username': data['username']
    }
    emit('receive_message', {
        'message': f"{data['username']} has joined the chat.",
        'color': '#999'
    }, room=data['chatroom_id'])

@socketio.on('disconnect')
def on_disconnect():
    user_info = user_rooms.get(request.sid)
    if user_info:
        chatroom_id = user_info['chatroom_id']
        username = user_info['username']
        emit('receive_message', {
            'message': f"{username} has left the chat.",
            'color': '#999'
        }, room=chatroom_id)
        # Видаляємо користувача зі словника після обробки відключень від кімнати
        del user_rooms[request.sid]

@main.route('/chatroom/<int:chatroom_id>', methods=['GET'])
@login_required
def chatroom(chatroom_id):
    room = Chatroom.query.get_or_404(chatroom_id)
    if room.is_invitation_only:
        # Перевірте, чи має користувач прийняте запрошення
        invitation = Invitation.query.filter_by(chatroom_id=chatroom_id, invitee_username=current_user.username, status='accepted').first()
        if not invitation:
            flash('This chat room is invitation-only.', 'error')
            return redirect(url_for('main.index'))
    messages = Message.query.filter_by(chatroom_id=chatroom_id).order_by(Message.timestamp.asc()).all()
    return render_template('chatroom.html', room=room, messages=messages)


