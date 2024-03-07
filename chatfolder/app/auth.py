from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user
import random
from .models import User
from . import db

auth = Blueprint('auth', __name__)

def get_random_color():
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            session['color'] = get_random_color()  # Зберігаємо коллір в сессії
            return redirect(url_for('chat_management.list_chatrooms')) 
        else:
            flash('Please check your login details and try again.')
            return redirect(url_for('auth.login'))
    
    return render_template('login.html')

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user:
            flash('Username already exists')
            return redirect(url_for('auth.signup'))
        
        new_user = User(username=username, password_hash=generate_password_hash(password, method='pbkdf2:sha256'))
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('signup.html')