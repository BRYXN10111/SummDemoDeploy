"""
Single-file Flask application to register, view and update user profiles.
- Uses Flask + Flask-WTF for forms and validation.
- Stores data in a SQLite database file `users.db`.
- Templates are embedded; a helper injects content into BASE safely.

Run:
    pip install Flask Flask-WTF email-validator
    python flask_user_profiles_app.py

Then open http://127.0.0.1:5000/
"""
from flask import Flask, g, render_template_string, redirect, url_for, request, flash
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length, NumberRange
import sqlite3
import os

# -------------------- Configuration --------------------
DB_PATH = 'users.db'
SECRET_KEY = 'dev-secret-key-change-me'

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

# -------------------- Database helpers --------------------
def get_db():
    """Return a sqlite3 connection (attached to flask.g) with dict-like rows."""
    db = getattr(g, '_database', None)
    if db is None:
        db = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
        g._database = db
    return db

@app.teardown_appcontext
def close_connection(exception):
    """Close DB connection at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    """Create users table if it doesn't exist."""
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                age INTEGER,
                bio TEXT
            )
        ''')
        conn.commit()
        conn.close()
        print('Initialized database at', DB_PATH)

# -------------------- Forms --------------------
class ProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=30)])
    full_name = StringField('Full name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    age = IntegerField('Age', validators=[NumberRange(min=0, max=120)], default=None)
    bio = TextAreaField('Bio', validators=[Length(max=500)])
    submit = SubmitField('Save')

# -------------------- Templates --------------------
# BASE contains a placeholder {{ content|safe }} where page-specific content will be injected.
BASE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Flask Profiles</title>
  <style>
    body{font-family:Arial,Helvetica,sans-serif;margin:2rem}
    .container{max-width:800px;margin:auto}
    label{display:block;margin-top:0.5rem}
    input, textarea{width:100%;padding:0.5rem;margin-top:0.25rem}
    .flash{padding:0.5rem;border-radius:4px;margin-bottom:1rem}
    .flash.success{background:#e6ffed;border:1px solid #b6f2c7}
    .flash.error{background:#ffe6e6;border:1px solid #f2b6b6}
    .card{border:1px solid #ddd;padding:1rem;border-radius:6px;margin-bottom:1rem}
    .small{font-size:0.9rem;color:#555}
    .actions{margin-top:1rem}
    .btn{display:inline-block;padding:0.5rem 1rem;border-radius:4px;text-decoration:none;background:#1976d2;color:white}
    .error-text{color:#b00020}
  </style>
</head>
<body>
  <div class="container">
    <h1>Flask Profiles</h1>
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        {% for category, msg in messages %}
          <div class="flash {{ category }}">{{ msg }}</div>
        {% endfor %}
      {% endif %}
    {% endwith %}
    {{ content|safe }}
  </div>
</body>
</html>
"""

# Small helper to render a page: render child template string into BASE.
def render_page(content_template_str, **context):
    """
    Render a content template string with context, then inject into BASE.
    This avoids fragile use of Jinja inheritance with render_template_string.
    """
    # First render the content fragment (so `form`, `url_for`, etc. are resolved)
    rendered_content = render_template_string(content_template_str, **context)
    # Now render BASE with the rendered content injected
    return render_template_string(BASE, content=rendered_content)


# Now each template is only the page-specific content (no extends).
INDEX_TEMPLATE = """
  <div class="actions">
    <a class="btn" href="{{ url_for('register') }}">Register new user</a>
  </div>
  <h2>Registered users</h2>
  {% if users %}
    {% for u in users %}
      <div class="card">
        <strong>{{ u['full_name'] }} ({{ u['username'] }})</strong>
        <div class="small">{{ u['email'] }}</div>
        <div class="actions">
          <a href="{{ url_for('profile', user_id=u['id']) }}">View</a> |
          <a href="{{ url_for('update', user_id=u['id']) }}">Edit</a>
        </div>
      </div>
    {% endfor %}
  {% else %}
    <p>No users yet. Be the first to register.</p>
  {% endif %}
"""

REGISTER_TEMPLATE = """
  <h2>Register</h2>
  <form method="post">
    {{ form.hidden_tag() }}
    <label>Username
      {{ form.username(size=30) }}
      {% for err in form.username.errors %}<div class="small error-text">{{ err }}</div>{% endfor %}
    </label>

    <label>Full name
      {{ form.full_name(size=60) }}
      {% for err in form.full_name.errors %}<div class="small error-text">{{ err }}</div>{% endfor %}
    </label>

    <label>Email
      {{ form.email(size=60) }}
      {% for err in form.email.errors %}<div class="small error-text">{{ err }}</div>{% endfor %}
    </label>

    <label>Age
      {{ form.age() }}
      {% for err in form.age.errors %}<div class="small error-text">{{ err }}</div>{% endfor %}
    </label>

    <label>Bio
      {{ form.bio(rows=4) }}
      {% for err in form.bio.errors %}<div class="small error-text">{{ err }}</div>{% endfor %}
    </label>

    <div style="margin-top:1rem">{{ form.submit() }}</div>
  </form>
"""

PROFILE_TEMPLATE = """
  <h2>{{ user['full_name'] }} ({{ user['username'] }})</h2>
  <div class="card">
    <div><strong>Email:</strong> {{ user['email'] }}</div>
    <div><strong>Age:</strong> {{ user['age'] if user['age'] is not None else '—' }}</div>
    <div style="margin-top:0.5rem"><strong>Bio:</strong>
      <div class="small">{{ user['bio'] or 'No bio provided.' }}</div>
    </div>
    <div class="actions">
      <a href="{{ url_for('update', user_id=user['id']) }}">Edit profile</a> |
      <a href="{{ url_for('index') }}">Back to list</a>
    </div>
  </div>
"""

UPDATE_TEMPLATE = """
  <h2>Update {{ user['full_name'] }} ({{ user['username'] }})</h2>
  <form method="post">
    {{ form.hidden_tag() }}

    <label>Username
      {{ form.username(size=30) }}
      {% for err in form.username.errors %}<div class="small error-text">{{ err }}</div>{% endfor %}
    </label>

    <label>Full name
      {{ form.full_name(size=60) }}
      {% for err in form.full_name.errors %}<div class="small error-text">{{ err }}</div>{% endfor %}
    </label>

    <label>Email
      {{ form.email(size=60) }}
      {% for err in form.email.errors %}<div class="small error-text">{{ err }}</div>{% endfor %}
    </label>

    <label>Age
      {{ form.age() }}
      {% for err in form.age.errors %}<div class="small error-text">{{ err }}</div>{% endfor %}
    </label>

    <label>Bio
      {{ form.bio(rows=4) }}
      {% for err in form.bio.errors %}<div class="small error-text">{{ err }}</div>{% endfor %}
    </label>

    <div style="margin-top:1rem">{{ form.submit() }}</div>
  </form>
  <p class="small"><a href="{{ url_for('profile', user_id=user['id']) }}">Cancel</a></p>
"""

# -------------------- Routes & Views --------------------

@app.route('/')
def index():
    """Show a simple list of users with links to view or edit each profile."""
    db = get_db()
    users = db.execute('SELECT id, username, full_name, email FROM users ORDER BY id DESC').fetchall()
    return render_page(INDEX_TEMPLATE, users=users)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Display registration form and store user on valid POST."""
    form = ProfileForm()
    if form.validate_on_submit():
        db = get_db()
        try:
            age_value = form.age.data if form.age.data is not None else None
            bio_value = (form.bio.data or '').strip()
            db.execute(
                'INSERT INTO users (username, full_name, email, age, bio) VALUES (?, ?, ?, ?, ?)',
                ( (form.username.data or '').strip(),
                  (form.full_name.data or '').strip(),
                  (form.email.data or '').strip(),
                  age_value,
                  bio_value
                )
            )
            db.commit()
            flash('User registered successfully.', 'success')
            return redirect(url_for('index'))
        except sqlite3.IntegrityError:
            flash('Error saving user: username or email might already exist.', 'error')
    return render_page(REGISTER_TEMPLATE, form=form)

@app.route('/profile/<int:user_id>')
def profile(user_id):
    """Show stored user data dynamically from the DB."""
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('index'))
    return render_page(PROFILE_TEMPLATE, user=user)

@app.route('/update/<int:user_id>', methods=['GET', 'POST'])
def update(user_id):
    """Preload user data into the update form and save changes on POST."""
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('index'))

    form = ProfileForm()
    if request.method == 'GET':
        # Populate form fields with existing values so the user can edit them.
        form.username.data = user['username']
        form.full_name.data = user['full_name']
        form.email.data = user['email']
        form.age.data = user['age']
        form.bio.data = user['bio']
    elif form.validate_on_submit():
        try:
            age_value = form.age.data if form.age.data is not None else None
            bio_value = (form.bio.data or '').strip()
            db.execute(
                'UPDATE users SET username = ?, full_name = ?, email = ?, age = ?, bio = ? WHERE id = ?',
                ( (form.username.data or '').strip(),
                  (form.full_name.data or '').strip(),
                  (form.email.data or '').strip(),
                  age_value,
                  bio_value,
                  user_id
                )
            )
            db.commit()
            flash('User updated successfully.', 'success')
            return redirect(url_for('profile', user_id=user_id))
        except sqlite3.IntegrityError:
            flash('Error updating user: username or email might conflict with an existing user.', 'error')

    return render_page(UPDATE_TEMPLATE, form=form, user=user)

# -------------------- Application entry point --------------------
if __name__ == '__main__':
    init_db()
    # Insert example data if there are no users (helps demonstrate update flow quickly).
    db = sqlite3.connect(DB_PATH)
    c = db.cursor()
    try:
        c.execute('SELECT COUNT(*) FROM users')
        count = c.fetchone()[0]
    except sqlite3.Error:
        count = 0
    if count == 0:
        c.execute('INSERT INTO users (username, full_name, email, age, bio) VALUES (?, ?, ?, ?, ?)',
                  ('jdoe', 'John Doe', 'jdoe@example.com', 34, 'A short bio about John.'))
        c.execute('INSERT INTO users (username, full_name, email, age, bio) VALUES (?, ?, ?, ?, ?)',
                  ('asmith', 'Alice Smith', 'alice@example.com', 28, 'Alice loves coding and coffee.'))
        db.commit()
        print('Inserted sample users.')
    db.close()

    app.run(debug=True)