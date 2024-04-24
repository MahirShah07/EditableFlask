import os
import json
from jinja2.environment import copy_cache
from flask import Blueprint, current_app, render_template, request, redirect, url_for
from datetime import datetime
from zipfile import ZipFile
import urllib.parse
import shutil

def CreateLoginManager(current_app, User):
    from flask_login import LoginManager, UserMixin, login_required, logout_user, current_user, login_user
    from werkzeug.security import generate_password_hash, check_password_hash
    from werkzeug.utils import secure_filename
    login_manager = LoginManager()
    login_manager.login_view = '/edits'+current_app.config['LOGIN_ROUTE']
    login_manager.init_app(current_app)
    @login_manager.user_loader
    def load_user(user_id):
        """Flask-Login callback to load a user from the database by ID."""
        return User.query.get(int(user_id))
def OrginalLocation(location):
    directory = os.path.dirname(location)
    return os.path.join(directory, '')

edits = Blueprint('edits', __name__, template_folder='templates', static_folder='assets')

@edits.route('/static')
@edits.route('/static/<path:page>')
def retrive_static(page=None):
    if page:
        page = urllib.parse.unquote(page)
    STATIC_PATH = os.path.join(current_app.config['FILE_PATH'],current_app.static_folder)
    if not os.path.exists(STATIC_PATH):
        os.mkdir(STATIC_PATH)
    if page:
        folder_location = 'static/'+page
        FolderPath = STATIC_PATH + '/'+page
    else:
        folder_location = 'static'
        FolderPath = STATIC_PATH
    contents = {}
    for root, folders, files in os.walk(FolderPath):
        if root == FolderPath: 
            for folder in folders:
                relative_location = os.path.relpath(os.path.join(root, folder), STATIC_PATH)
                folder_path = os.path.join(root, folder)
                folder_stats = os.stat(folder_path)
                contents[folder] = {
                    "type": "folder",
                    "name": folder,
                    "location": '/static/'+relative_location,
                    "last_modified": datetime.fromtimestamp(folder_stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                    "size": str(round(folder_stats.st_size / 1024, 2))+" KiB",
                }
            for file in files:
                file_path = os.path.join(root, file)
                relative_location = os.path.relpath(file_path, STATIC_PATH)
                file_stats = os.stat(file_path)  # Get file stats
                filename, extension = os.path.splitext(file)
                contents[file] = {
                    "type": "file",
                    "name": filename+extension,
                    "extension": extension,
                    "location": '/static/'+relative_location,
                    "last_modified": datetime.fromtimestamp(file_stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                    "size": str(round(file_stats.st_size / 1024, 2))+" KiB",
                }
    return render_template('static.html', contents=contents, folder_location=folder_location) 

@edits.route('/static-view/<path:page>', methods=['POST'])
def static_view(page=None):
    location = request.form.get('location')
    if page == 'upload':
        files = request.files['file']
        files.save(os.path.join(current_app.config['FILE_PATH'],location, request.form.get('file_name')))
    elif page == 'create_folder':
        new_folder_path = os.path.join(current_app.config['FILE_PATH'], location, request.form.get('folder_name'))
        if not os.path.exists(new_folder_path):
            os.makedirs(new_folder_path)
    elif page == 'unzip':
        location = request.form.get('detail_location')
        location = current_app.config['FILE_PATH']+location
        new_folder_path, _ = os.path.splitext(location)
        if not os.path.exists(new_folder_path):
            os.makedirs(new_folder_path)
        with ZipFile(location, 'r') as zObject: 
            zObject.extractall(path=new_folder_path) 
    elif page == 'delete':
        location = request.form.get('detail_location')
        location = current_app.config['FILE_PATH']+location
        if os.path.exists(location):
            if os.path.isfile(location):
                os.remove(location)
            elif os.path.isdir(location):
                shutil.rmtree(location)  
    elif page == 'back':
        parts = location.split('/')
        parent_directory = '/'.join(parts[1:-1])  # Join parts starting from index 1 to the second-to-last index
        if parent_directory == '':
            return redirect(url_for('edits.retrive_static', page=None))
        return redirect(url_for('edits.retrive_static', page=parent_directory))
    elif page == 'rename':
        location = location+'/'+request.form.get('name')
        if os.path.exists(location):
            if os.path.isfile(location):
                directory = os.path.dirname(location)
                new_name = request.form.get('file_folder_name')
                base_name = new_name
                extension = os.path.splitext(location)[1]
                if new_name.find('.') != -1:
                    base_name, extension = os.path.splitext(new_name)
                new_location = os.path.join(directory, base_name + extension)
                os.rename(location, new_location)
            elif os.path.isdir(location):  # If it's a directory
                new_name = request.form.get('file_folder_name')
                new_location = os.path.join(os.path.dirname(location), new_name)
                os.rename(location, new_location)
    elif page == 'search':
        folder_path = current_app.config['FILE_PATH']+'/'+location
        search_input = request.form.get('searchInput')
        search_input = search_input.lower()
        contents = {}
        for root, folders, files in os.walk(folder_path):
            for folder in folders:
                if search_input in folder.lower():  # Compare in lowercase
                    relative_location = os.path.relpath(os.path.join(root, folder), folder_path)
                    folder_stats = os.stat(os.path.join(root, folder))
                    contents[folder] = {
                        "type": "folder",
                        "name": folder,
                        "location": '/static/'+relative_location,
                        "last_modified": datetime.fromtimestamp(folder_stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                        "size": str(round(folder_stats.st_size / 1024, 2))+" KiB",
                    }
            for file in files:
                if search_input in file.lower():  # Compare in lowercase
                    file_path = os.path.join(root, file)
                    relative_location = os.path.relpath(file_path, folder_path)
                    file_stats = os.stat(file_path)  # Get file stats
                    filename, extension = os.path.splitext(file)
                    contents[file] = {
                        "type": "file",
                        "name": filename+extension,
                        "extension": extension,
                        "location": '/static/'+relative_location,
                        "last_modified": datetime.fromtimestamp(file_stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                        "size": str(round(file_stats.st_size / 1024, 2))+" KiB",
                    }
        return render_template('static.html', contents=contents, searched_location=folder_path) 
    location = request.form.get('location')
    parts = location.split('/')
    if len(parts) == 1:
        location=None
    else:
        location = '/'.join(parts[-1:])
    return redirect(url_for('edits.retrive_static', page=location))

@edits.route('/')
@edits.route('/<path:page>')
def index(page=None):
    _db = current_app.jinja_env.edits
    if _db:
        if not page or page not in _db:
            page = next(iter(_db.keys())) if _db else None
    else:
        page = None
    return render_template('edits-admin.html',
                            edits=_db,
                            page=page,
                            summernote=current_app.config['EDITS_SUMMERNOTE'],
                            preview=current_app.jinja_env.edits_preview)
                            
@edits.route('/preview', methods=['POST'])
def preview():
    if request.form.get('state') == 'true':
        preview = True
        cache = None
    else:
        preview = False
        cache = copy_cache(current_app.jinja_env.edits_cache)

    current_app.jinja_env.edits_preview = preview
    current_app.jinja_env.cache = cache

    if current_app.jinja_env.cache:
        current_app.jinja_env.cache.clear()

    return ''

@edits.route('/save', methods=['POST'])
def save():
    _db = current_app.jinja_env.edits
    page = request.form.get('page')
    for field in request.form:
        if field != 'page' and field != 'files':  # Skip 'files' field
            value = request.form.get(field)
            if value == '':
                value = None
            _db[page][field]['edited'] = value
    if current_app.jinja_env.cache:
        current_app.jinja_env.cache.clear()
    with open(current_app.config['FILE_PATH']+'edits.json', 'w') as f:
        f.write(json.dumps(_db, indent=4))
    return redirect(url_for('edits.index', page=page))



    