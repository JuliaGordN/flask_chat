from . import db, login_manager
from datetime import datetime 
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

# Модель користувача
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    chatrooms = db.relationship('Chatroom', secondary='user_chatroom_link', back_populates='users')

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
# Модель кімнати
class Chatroom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    owner = db.relationship('User', backref=db.backref('owned_chatrooms', lazy=True))
    messages = db.relationship('Message', backref='chatroom', lazy='dynamic')
    users = db.relationship('User', secondary='user_chatroom_link', back_populates='chatrooms')
    is_invitation_only = db.Column(db.Boolean, default=False, nullable=False)  # Add this line

class UserChatroomLink(db.Model):
    __tablename__ = 'user_chatroom_link'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    chatroom_id = db.Column(db.Integer, db.ForeignKey('chatroom.id'), primary_key=True)
# Модель запрошень
class Invitation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chatroom_id = db.Column(db.Integer, db.ForeignKey('chatroom.id'), nullable=False)
    invitee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    inviter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Add this line
    status = db.Column(db.String(20), nullable=False, default='pending')  # Adjusted default status to 'pending'

    chatroom = db.relationship('Chatroom', backref=db.backref('invitations', lazy='dynamic'))
    invitee = db.relationship('User', foreign_keys=[invitee_id], backref=db.backref('invitations_received', lazy='dynamic'))
    inviter = db.relationship('User', foreign_keys=[inviter_id], backref=db.backref('invitations_sent', lazy='dynamic'))  # Add this line
# Модель повідомлень
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('messages', lazy=True))
    chatroom_id = db.Column(db.Integer, db.ForeignKey('chatroom.id'))
