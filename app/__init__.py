"""
App factory and configuration.
- Uses an instance_path database file (safer than writing in source).
"""
import os
from flask import Flask
from .db import init_db

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_mapping(
        SECRET_KEY='dev-secret-key-change-me',  # change this for production
        DATABASE=os.path.join(app.instance_path, 'users.db')
    )

    if test_config is not None:
        # allow overriding config for testing
        app.config.update(test_config)

    # ensure the instance folder exists (where the DB file will live)
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # initialize sqlite DB file and schema (no-op if already exists)
    init_db(app.config['DATABASE'])

    # register routes blueprint
    from . import routes
    app.register_blueprint(routes.bp)

    return app