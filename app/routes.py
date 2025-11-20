"""
Routes for the profiles app.
- List, register, view and update users.
- Uses the sqlite helper functions in app.db and ProfileForm from app.forms.
"""
from flask import Blueprint, current_app, render_template, redirect, url_for, request, flash
from .db import get_db_connection
from .forms import ProfileForm
import sqlite3

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Show a list of users."""
    db = get_db_connection(current_app.config['DATABASE'])
    users = db.execute('SELECT id, username, full_name, email FROM users ORDER BY id DESC').fetchall()
    db.close()
    return render_template('index.html', users=users)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Create a new user from form data."""
    form = ProfileForm()
    if form.validate_on_submit():
        db = get_db_connection(current_app.config['DATABASE'])
        try:
            db.execute(
                'INSERT INTO users (username, full_name, email, age, bio) VALUES (?, ?, ?, ?, ?)',
                (form.username.data.strip(), form.full_name.data.strip(), 
                 form.email.data.strip(), form.age.data or None, form.bio.data.strip())
            )
            db.commit()
            flash('User registered successfully.', 'success')
            return redirect(url_for('main.index'))
        except sqlite3.IntegrityError:
            # Handle unique constraint violations for username/email
            flash('Error: username or email already exists.', 'error')
        finally:
            db.close()
    return render_template('register.html', form=form)

@bp.route('/profile/<int:user_id>')
def profile(user_id):
    """Display a single user's profile dynamically."""
    db = get_db_connection(current_app.config['DATABASE'])
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    db.close()
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('main.index'))
    return render_template('profile.html', user=user)

@bp.route('/update/<int:user_id>', methods=['GET', 'POST'])
def update(user_id):
    """Preload user data into the form for update and save changes."""
    db = get_db_connection(current_app.config['DATABASE'])
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        db.close()
        flash('User not found', 'error')
        return redirect(url_for('main.index'))

    form = ProfileForm()
    if request.method == 'GET':
        # Preload current values into the form so user can edit them
        form.username.data = user['username']
        form.full_name.data = user['full_name']
        form.email.data = user['email']
        form.age.data = user['age']
        form.bio.data = user['bio']
    elif form.validate_on_submit():
        try:
            db.execute(
                'UPDATE users SET username = ?, full_name = ?, email = ?, age = ?, bio = ? WHERE id = ?',
                (form.username.data.strip(), form.full_name.data.strip(),
                 form.email.data.strip(), form.age.data or None, form.bio.data.strip(), user_id)
            )
            db.commit()
            flash('User updated successfully.', 'success')
            return redirect(url_for('main.profile', user_id=user_id))
        except sqlite3.IntegrityError:
            flash('Error updating user: username or email conflict.', 'error')
    db.close()
    return render_template('update.html', form=form, user=user)
