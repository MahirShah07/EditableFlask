"""editable_flask"""

from flask import request
from jinja2.environment import copy_cache
from jinja2 import Environment, BaseLoader
from markupsafe import Markup
from collections import OrderedDict
import json
import os
from .editable import EditableExtension
from .views import edits

class Edits(object):
    def __init__(self, app=None):
        self.app = app

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """
        Register the Jinja extension, load edits from app.config['EDITS_PATH'],
        and register blueprints.

        :param app:
            Flask application instance
        """
        app.config.setdefault('EDITS_URL', '/edits')
        app.config.setdefault('EDITS_PREVIEW', False)
        app.config.setdefault('EDITS_SUMMERNOTE', False)
        app.config.setdefault('LOGIN_ROUTE', '/login')

        if 'FILE_PATH' not in app.config:
            raise Exception('FILE_PATH not set in app configuration.')
        EDITS_PATH = app.config['FILE_PATH']+'/edits.json'
        if not os.path.isfile(EDITS_PATH):
            with open(EDITS_PATH, 'w') as f:
                json.dump({}, f)
        if os.path.isfile(EDITS_PATH):
            with open(EDITS_PATH) as f:
                _db = json.loads(f.read(), object_pairs_hook=OrderedDict)
        else:
            _db = OrderedDict()
        
        if app.config['SQL_EDITS_LOCKED']:
            from datetime import timedelta
            from .views import CreateLoginManager
            from flask_sqlalchemy import SQLAlchemy
            from flask import render_template, redirect, url_for
            from werkzeug.security import generate_password_hash, check_password_hash
            from flask_login import LoginManager, UserMixin, login_required, logout_user, current_user, login_user
            app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=60)
            if not 'SQLALCHEMY_DATABASE_URI' in app.config:
                app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
            if not 'SQLALCHEMY_TRACK_MODIFICATIONS' in app.config:
                app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
            db = SQLAlchemy(app)
            class User(db.Model, UserMixin):
                id = db.Column(db.Integer, primary_key=True)
                username = db.Column(db.String(80), unique=True, nullable=False)
                password_hash = db.Column(db.String(128), nullable=False)
                def verify_password(self, password):
                    return check_password_hash(self.password_hash, password)
                def __repr__(self):
                    return '<User %r>' % self.username
            if not os.path.exists(app.config['SQLALCHEMY_DATABASE_URI'][10:]):
                with app.app_context():
                    db.create_all()
            if 'EDITS_PASSWORD' in app.config or 'EDITS_USERNAME' in app.config:
                with app.app_context():
                    Username = app.config.get('EDITS_USERNAME', app.config.get('EDITS_PASSWORD', None))
                    Password = app.config.get('EDITS_PASSWORD', app.config.get('EDITS_USERNAME', None))
                    existing_user = User.query.filter_by(username=Username).first()
                    if existing_user:
                        existing_user.password_hash = generate_password_hash(Password)
                    else:
                        user = User(username=Username, password_hash=generate_password_hash(Password))
                        db.session.add(user)
                    db.session.commit()
            CreateLoginManager(app, User)
            @edits.route(app.config['LOGIN_ROUTE'], methods=['POST','GET'])
            def login():
                if current_user.is_authenticated:
                    return redirect(url_for('edits.index'))
                if request.form.get('username') and request.form.get('password'):
                    username = request.form.get('username')
                    password = request.form.get('password')
                    got_user = User.query.filter_by(username=username).first()
                    if got_user and got_user.username == username and got_user.verify_password(password):
                        login_user(got_user)
                        return redirect('/edits')
                return render_template("login_prompt.html")
            @edits.route('/logout')
            @login_required
            def logout():
                logout_user()
                return redirect(url_for('edits.login'))
        
        if app.config['SQL_EDITS_LOCKED'] or app.config['EDITS_LOCKED']:
            @edits.before_request
            def require_login():
                login_route = app.config['LOGIN_ROUTE']
                if current_user and current_user.is_authenticated:
                    pass
                elif request.path == login_route or request.path == '/edits'+login_route:
                    pass
                else:
                    if app.config['SQL_EDITS_LOCKED']:
                        return redirect(url_for('edits.login'))
                    else:
                        return redirect(login_route)

        

        env = Environment(loader=BaseLoader())
        app.jinja_env.add_extension(EditableExtension)
        app.jinja_env.edits = _db
        app.jinja_env.edits_preview = app.config['EDITS_PREVIEW']
        app.jinja_env.edits_cache = copy_cache(app.jinja_env.cache)
        if app.config['EDITS_PREVIEW']:
            app.jinja_env.cache = None

        app.register_blueprint(edits, url_prefix=app.config['EDITS_URL'])

