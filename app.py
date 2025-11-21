from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, IntegerField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length, NumberRange, ValidationError
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'  # Change this in production!

# Database configuration
DATABASE = 'users.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    # Create users table with all necessary fields for profile management
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            age INTEGER,
            bio TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def get_db_connection():
    """
    Create and return a database connection.
    This helper function centralizes database connection logic.
    """
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn

class RegistrationForm(FlaskForm):
    """Form for user registration with validation rules."""
    username = StringField('Username', validators=[
        DataRequired(message='Username is required'),
        Length(min=3, max=20, message='Username must be between 3 and 20 characters')
    ])
    email = EmailField('Email', validators=[
        DataRequired(message='Email is required'),
        Email(message='Please enter a valid email address')
    ])
    password = StringField('Password', validators=[
        DataRequired(message='Password is required'),
        Length(min=6, message='Password must be at least 6 characters long')
    ])
    full_name = StringField('Full Name', validators=[
        DataRequired(message='Full name is required'),
        Length(min=2, max=100, message='Full name must be between 2 and 100 characters')
    ])
    age = IntegerField('Age', validators=[
        NumberRange(min=1, max=150, message='Age must be between 1 and 150')
    ])
    bio = TextAreaField('Bio', validators=[
        Length(max=500, message='Bio cannot exceed 500 characters')
    ])
    submit = SubmitField('Register')

    def validate_username(self, username):
        """
        Custom validation to check if username already exists in database.
        This prevents duplicate usernames during registration.
        """
        conn = get_db_connection()
        user = conn.execute(
            'SELECT id FROM users WHERE username = ?', (username.data,)
        ).fetchone()
        conn.close()
        if user:
            raise ValidationError('This username is already taken. Please choose another.')

    def validate_email(self, email):
        """
        Custom validation to check if email already exists in database.
        This ensures each user has a unique email address.
        """
        conn = get_db_connection()
        user = conn.execute(
            'SELECT id FROM users WHERE email = ?', (email.data,)
        ).fetchone()
        conn.close()
        if user:
            raise ValidationError('This email is already registered. Please use another email.')

class UpdateProfileForm(FlaskForm):
    """Form for updating user profile information."""
    email = EmailField('Email', validators=[
        DataRequired(message='Email is required'),
        Email(message='Please enter a valid email address')
    ])
    full_name = StringField('Full Name', validators=[
        DataRequired(message='Full name is required'),
        Length(min=2, max=100, message='Full name must be between 2 and 100 characters')
    ])
    age = IntegerField('Age', validators=[
        NumberRange(min=1, max=150, message='Age must be between 1 and 150')
    ])
    bio = TextAreaField('Bio', validators=[
        Length(max=500, message='Bio cannot exceed 500 characters')
    ])
    submit = SubmitField('Update Profile')

    def validate_email(self, email):
        """
        Custom validation to check if email is already taken by another user.
        Allows the current user to keep their existing email.
        """
        if 'user_id' in session:
            conn = get_db_connection()
            user = conn.execute(
                'SELECT id FROM users WHERE email = ? AND id != ?',
                (email.data, session['user_id'])
            ).fetchone()
            conn.close()
            if user:
                raise ValidationError('This email is already registered to another user.')

@app.route('/')
def index():
    """Home page route that redirects to registration or profile based on login status."""
    if 'user_id' in session:
        return redirect(url_for('profile'))
    return redirect(url_for('register'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Handle user registration.
    GET: Display the registration form
    POST: Process form submission, validate data, and store user in database
    """
    form = RegistrationForm()
    
    if form.validate_on_submit():
        # Hash the password before storing for security
        hashed_password = generate_password_hash(form.password.data)
        
        conn = get_db_connection()
        try:
            # Insert new user into database with hashed password
            conn.execute('''
                INSERT INTO users (username, email, password, full_name, age, bio)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                form.username.data,
                form.email.data,
                hashed_password,
                form.full_name.data,
                form.age.data if form.age.data else None,
                form.bio.data if form.bio.data else None
            ))
            conn.commit()
            
            # Get the newly created user's ID for session management
            user = conn.execute(
                'SELECT id, username FROM users WHERE username = ?',
                (form.username.data,)
            ).fetchone()
            conn.close()
            
            # Set session to keep user logged in after registration
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Registration successful! Welcome!', 'success')
            return redirect(url_for('profile'))
        except sqlite3.IntegrityError:
            # Handle database integrity errors (e.g., duplicate username/email)
            conn.close()
            flash('An error occurred during registration. Please try again.', 'error')
    
    return render_template('register.html', form=form)

@app.route('/profile')
def profile():
    """
    Display the user's profile information.
    Requires user to be logged in (session must contain user_id).
    """
    if 'user_id' not in session:
        flash('Please log in to view your profile.', 'error')
        return redirect(url_for('register'))
    
    conn = get_db_connection()
    # Fetch user data from database using session user_id
    user = conn.execute(
        'SELECT id, username, email, full_name, age, bio, created_at, updated_at FROM users WHERE id = ?',
        (session['user_id'],)
    ).fetchone()
    conn.close()
    
    if not user:
        flash('User not found.', 'error')
        session.clear()
        return redirect(url_for('register'))
    
    return render_template('profile.html', user=user)

@app.route('/update', methods=['GET', 'POST'])
def update_profile():
    """
    Handle profile updates.
    GET: Display update form pre-filled with current user data
    POST: Process form submission and update user data in database
    """
    if 'user_id' not in session:
        flash('Please log in to update your profile.', 'error')
        return redirect(url_for('register'))
    
    form = UpdateProfileForm()
    conn = get_db_connection()
    
    # Fetch current user data to pre-populate the form
    user = conn.execute(
        'SELECT email, full_name, age, bio FROM users WHERE id = ?',
        (session['user_id'],)
    ).fetchone()
    conn.close()
    
    if not user:
        flash('User not found.', 'error')
        session.clear()
        return redirect(url_for('register'))
    
    if form.validate_on_submit():
        # Update user data in database with new information from form
        conn = get_db_connection()
        conn.execute('''
            UPDATE users 
            SET email = ?, full_name = ?, age = ?, bio = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (
            form.email.data,
            form.full_name.data,
            form.age.data if form.age.data else None,
            form.bio.data if form.bio.data else None,
            session['user_id']
        ))
        conn.commit()
        conn.close()
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    
    # Pre-populate form fields with existing user data on GET request
    if request.method == 'GET':
        form.email.data = user['email']
        form.full_name.data = user['full_name']
        form.age.data = user['age']
        form.bio.data = user['bio']
    
    return render_template('update.html', form=form)

@app.route('/logout')
def logout():
    """Clear user session and log out the user."""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('register'))

if __name__ == '__main__':
    # Initialize database on application startup
    init_db()
    app.run(debug=True)


