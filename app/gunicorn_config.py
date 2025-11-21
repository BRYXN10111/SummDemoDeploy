"""
Gunicorn configuration file for production deployment.

This file contains production settings for Gunicorn server.
Usage: gunicorn -c gunicorn_config.py wsgi:application
"""

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "flask_user_profile_app"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (uncomment and configure if using HTTPS)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

