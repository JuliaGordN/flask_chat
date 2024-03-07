from flask import Blueprint, request, redirect, url_for, render_template, flash
from flask_login import login_required, current_user
from .models import User, Chatroom, UserChatroomLink, Message, Invitation
from . import db

chat_management = Blueprint('chat_management', __name__)

@chat_management.route('/create_room_form')
@login_required
def create_room_form():
    # Форма стоврення нової кімнати
    return render_template('create_chatroom.html')

@chat_management.route('/create_room', methods=['POST'])
@login_required
def create_room():
    room_name = request.form.get('room_name')
    is_invitation_only = request.form.get('is_invitation_only') == 'on'  # Перевірка чи кімната тільки з запрошенями.

    if room_name:
        existing_room = Chatroom.query.filter_by(name=room_name).first()
        if existing_room is None:
            new_room = Chatroom(name=room_name, owner_id=current_user.id, is_invitation_only=is_invitation_only)
            db.session.add(new_room)
            db.session.commit()
            flash('Chat room created successfully.', 'success')
            return redirect(url_for('main.chatroom', chatroom_id=new_room.id))
        else:
            flash('A room with this name already exists.', 'error')
    else:
        flash('Room name cannot be empty.', 'error')
    return redirect(url_for('main.create_room_form'))

@chat_management.route('/list_chatrooms', methods=['GET'])
@login_required
def list_chatrooms():
    chatrooms = Chatroom.query.all()
    # Додаємо запит для отримання відкладених запрошень
    pending_invitations = Invitation.query.filter_by(invitee_id=current_user.id, status='pending').all()
    return render_template('list_chatrooms.html', chatrooms=chatrooms, pending_invitations=pending_invitations)


@chat_management.route('/chatroom/<int:chatroom_id>', methods=['GET'])
@login_required
def chatroom(chatroom_id):
    room = Chatroom.query.get_or_404(chatroom_id)

    # Дозволити власнику чату доступ без запрошення
    if room.owner_id != current_user.id:
        # Перевірка чи чат доступний лише за запрошеннями для тих, хто не є його власником
        if room.is_invitation_only:
            # Перевірте, чи користувач прийняв запрошення
            invitation = Invitation.query.filter_by(chatroom_id=chatroom_id, invitee_id=current_user.id, status='accepted').first()
            if not invitation:
                flash('This chatroom is invitation-only. You must be invited to view it.', 'danger')
                return redirect(url_for('chat_management.list_chatrooms'))
    
    messages = Message.query.filter_by(chatroom_id=chatroom_id).order_by(Message.timestamp.asc()).all()
    return render_template('chatroom.html', room=room, messages=messages)



@chat_management.route('/join_chatroom/<int:chatroom_id>', methods=['GET'])
@login_required
def join_chatroom(chatroom_id):
    chatroom = Chatroom.query.get_or_404(chatroom_id)
    
    # Перевірка, чи чат доступний лише за запрошеннями
    if chatroom.is_invitation_only:
        # Перевірка, чи має користувач прийняте запрошення
        invitation = Invitation.query.filter_by(chatroom_id=chatroom_id, invitee_id=current_user.id, status='accepted').first()
        if not invitation:
            flash('You must be invited to join this chatroom.', 'danger')
            return redirect(url_for('chat_management.list_chatrooms'))
    
    # Додавання користувача до чату, якщо він ще не є його учасником
    link = UserChatroomLink.query.filter_by(user_id=current_user.id, chatroom_id=chatroom_id).first()
    if not link:
        new_link = UserChatroomLink(user_id=current_user.id, chatroom_id=chatroom_id)
        db.session.add(new_link)
        db.session.commit()
        flash('You have successfully joined the chatroom.', 'success')
    
    return redirect(url_for('chat_management.chatroom', chatroom_id=chatroom_id))



@chat_management.route('/invite_to_chatroom', methods=['POST'])
@login_required
def invite_to_chatroom():
    chatroom_id = request.form.get('chatroom_id')
    invitee_username = request.form.get('invitee_username')
    chatroom = Chatroom.query.get_or_404(chatroom_id)
    invitee = User.query.filter_by(username=invitee_username).first()

    if not invitee:
        flash('User not found.', 'error')
        return redirect(url_for('chat_management.list_chatrooms'))

    if chatroom.owner_id != current_user.id:
        flash('You are not authorized to invite users to this chatroom.', 'error')
        return redirect(url_for('chat_management.list_chatrooms'))

    new_invitation = Invitation(
        chatroom_id=chatroom_id, 
        invitee_id=invitee.id, 
        inviter_id=current_user.id,  # Встановити поточного користувача як запрошеного
        status='pending'
    )
    db.session.add(new_invitation)
    db.session.commit()

    flash('Invitation sent successfully.', 'success')
    return redirect(url_for('chat_management.list_chatrooms'))



@chat_management.route('/accept_invitation/<int:invitation_id>', methods=['GET'])
@login_required
def accept_invitation(invitation_id):
    invitation = Invitation.query.get_or_404(invitation_id)
    if invitation.invitee_id != current_user.id:
        flash('You are not authorized to accept this invitation.', 'error')
        return redirect(url_for('main.index'))
    if invitation.status != 'pending':
        flash('This invitation has already been responded to.', 'info')
        return redirect(url_for('main.index'))
    
    invitation.status = 'accepted'
    db.session.commit()
    flash('Invitation accepted. You can now access the chat room.', 'success')
    return redirect(url_for('chat_management.chatroom', chatroom_id=invitation.chatroom_id))

@chat_management.route('/respond_to_invitation/<int:invitation_id>/<response>', methods=['POST'])
@login_required
def respond_to_invitation(invitation_id, response):
    invitation = Invitation.query.get_or_404(invitation_id)
    
    if invitation.invitee_id != current_user.id:
        flash('You are not authorized to respond to this invitation.', 'error')
        return redirect(url_for('chat_management.list_chatrooms'))
    
    if response == 'accept':
        invitation.status = 'accepted'
    elif response == 'decline':
        invitation.status = 'declined'
    else:
        flash('Invalid response.', 'error')
        return redirect(url_for('chat_management.list_chatrooms'))
    
    db.session.commit()
    flash('Invitation response updated.', 'success')
    return redirect(url_for('chat_management.list_chatrooms'))
