"""Views used by EditableFlask's administration blueprint."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from zipfile import ZipFile

from flask import Blueprint, abort, current_app, redirect, render_template, request, url_for
from jinja2.environment import copy_cache
from werkzeug.utils import secure_filename


def _state():
    return current_app.extensions["editable_flask"]


def _static_root() -> Path:
    root = Path(current_app.static_folder or "static")
    if not root.is_absolute():
        root = Path(current_app.root_path) / root
    root.mkdir(parents=True, exist_ok=True)
    return root.resolve()


def _safe_path(root: Path, value: str | None = None) -> Path:
    candidate = (root / (value or "").lstrip("/")).resolve()
    if candidate != root and root not in candidate.parents:
        abort(400, "Path escapes the configured static directory")
    return candidate


def _require_static_manager():
    if not current_app.config["EDITS_STATIC"]:
        abort(404)


def _write_database():
    path = _state()["data_file"]
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(_state()["database"], indent=2), encoding="utf-8")
    temporary.replace(path)


def _login_required():
    if not (current_app.config["SQL_EDITS_LOCKED"] or current_app.config["EDITS_LOCKED"]):
        return False
    try:
        from flask_login import current_user
        return not getattr(current_user, "is_authenticated", False)
    except (RuntimeError, AttributeError):
        return True


def create_edits_blueprint():
    edits = Blueprint("edits", __name__, template_folder="templates", static_folder="assets")

    @edits.before_request
    def require_login():
        if request.endpoint in {"edits.login", "edits.static"}:
            return None
        if _login_required():
            if current_app.config["SQL_EDITS_LOCKED"]:
                return redirect(url_for("edits.login", next=request.url))
            return redirect(current_app.config["LOGIN_ROUTE"])
        return None

    @edits.route("/")
    @edits.route("/<path:page>")
    def index(page=None):
        database = _state()["database"]
        if database and (not page or page not in database):
            page = next(iter(database))
        return render_template(
            "edits-admin.html", edits=database, page=page,
            summernote=current_app.config["EDITS_SUMMERNOTE"],
            preview=current_app.jinja_env.edits_preview,
            static_manager=current_app.config["EDITS_STATIC"],
            sql_locked=current_app.config["SQL_EDITS_LOCKED"],
        )

    @edits.post("/preview")
    def preview():
        enabled = request.form.get("state", "").lower() == "true"
        current_app.jinja_env.edits_preview = enabled
        current_app.jinja_env.cache = None if enabled else copy_cache(current_app.jinja_env.edits_cache)
        if current_app.jinja_env.cache:
            current_app.jinja_env.cache.clear()
        return "", 204

    @edits.post("/save")
    def save():
        database = _state()["database"]
        page = request.form.get("page")
        if not page or page not in database:
            abort(400, "Unknown editable page")
        for field, value in request.form.items():
            if field != "page" and field in database[page]:
                database[page][field]["edited"] = value or None
        _write_database()
        if current_app.jinja_env.cache:
            current_app.jinja_env.cache.clear()
        return redirect(url_for("edits.index", page=page))

    @edits.route("/login", methods=["GET", "POST"])
    def login():
        if not current_app.config["SQL_EDITS_LOCKED"]:
            abort(404)
        from flask_login import current_user, login_user
        if current_user.is_authenticated:
            return redirect(url_for("edits.index"))
        if request.method == "POST":
            model = _state()["user_model"]
            user = model.query.filter_by(username=request.form.get("username")).first()
            if user and user.verify_password(request.form.get("password", "")):
                login_user(user)
                return redirect(url_for("edits.index"))
        return render_template("login_prompt.html")

    @edits.get("/logout")
    def logout():
        if not current_app.config["SQL_EDITS_LOCKED"]:
            abort(404)
        from flask_login import logout_user
        logout_user()
        return redirect(url_for("edits.login"))

    @edits.get("/static")
    @edits.get("/static/<path:page>")
    def retrive_static(page=None):
        _require_static_manager()
        root = _static_root()
        folder = _safe_path(root, page)
        if not folder.is_dir():
            abort(404)
        contents = {}
        for item in sorted(folder.iterdir(), key=lambda value: (value.is_file(), value.name.lower())):
            stat = item.stat()
            relative = item.relative_to(root).as_posix()
            item_url = (
                url_for("edits.retrive_static", page=relative)
                if item.is_dir() else url_for("static", filename=relative)
            )
            contents[item.name] = {
                "type": "folder" if item.is_dir() else "file", "name": item.name,
                "extension": item.suffix, "location": item_url, "path": relative,
                "last_modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "size": f"{stat.st_size / 1024:.2f} KiB",
            }
        location = "static" + ("/" + page.strip("/") if page else "")
        return render_template("static.html", contents=contents, folder_location=location)

    @edits.post("/static-view/<action>")
    def static_view(action):
        _require_static_manager()
        root = _static_root()
        location = request.form.get("location", "static")
        location = location.removeprefix("static/").removeprefix("static")
        folder = _safe_path(root, location)
        if action == "upload":
            uploaded = request.files.get("file")
            name = secure_filename(request.form.get("file_name") or (uploaded.filename if uploaded else ""))
            if not uploaded or not name:
                abort(400, "A file and valid filename are required")
            uploaded.save(_safe_path(folder, name))
        elif action == "create_folder":
            name = secure_filename(request.form.get("folder_name", ""))
            if not name:
                abort(400, "A valid folder name is required")
            _safe_path(folder, name).mkdir(exist_ok=False)
        elif action in {"delete", "unzip"}:
            detail = request.form.get("detail_location", "")
            target = _safe_path(root, detail)
            if action == "delete":
                shutil.rmtree(target) if target.is_dir() else target.unlink(missing_ok=True)
            else:
                destination = target.with_suffix("")
                destination.mkdir(exist_ok=True)
                with ZipFile(target) as archive:
                    for member in archive.infolist():
                        _safe_path(destination, member.filename)
                    archive.extractall(destination)
        elif action == "rename":
            source = _safe_path(folder, request.form.get("name"))
            name = secure_filename(request.form.get("file_folder_name", ""))
            if not name:
                abort(400, "A valid name is required")
            if source.is_file() and not Path(name).suffix:
                name += source.suffix
            source.rename(_safe_path(folder, name))
        elif action == "back":
            parent = Path(location).parent.as_posix()
            return redirect(url_for("edits.retrive_static", page=None if parent == "." else parent))
        elif action == "search":
            query = request.form.get("searchInput", "").casefold()
            contents = {}
            for item in folder.rglob("*"):
                if query not in item.name.casefold():
                    continue
                stat = item.stat()
                relative = item.relative_to(root).as_posix()
                item_url = (
                    url_for("edits.retrive_static", page=relative)
                    if item.is_dir() else url_for("static", filename=relative)
                )
                contents[relative] = {
                    "type": "folder" if item.is_dir() else "file", "name": item.name,
                    "extension": item.suffix, "location": item_url, "path": relative,
                    "last_modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                    "size": f"{stat.st_size / 1024:.2f} KiB",
                }
            return render_template("static.html", contents=contents, searched_location=location)
        else:
            abort(400, "Unknown file action")
        page = folder.relative_to(root).as_posix()
        return redirect(url_for("edits.retrive_static", page=None if page == "." else page))

    return edits


def init_login(app):
    """Initialize the optional built-in SQLAlchemy authentication."""
    try:
        from flask_login import LoginManager, UserMixin
        from flask_sqlalchemy import SQLAlchemy
        from werkzeug.security import check_password_hash, generate_password_hash
    except ImportError as error:
        raise RuntimeError("SQL_EDITS_LOCKED requires EditableFlask[sql]") from error

    app.config.setdefault("PERMANENT_SESSION_LIFETIME", timedelta(minutes=60))
    app.config.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///editable_flask_users.db")
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
    db = app.extensions.get("sqlalchemy")
    if db is None:
        db = SQLAlchemy()
        db.init_app(app)

    class EditableFlaskUser(db.Model, UserMixin):
        __tablename__ = "editable_flask_users"
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(80), unique=True, nullable=False)
        password_hash = db.Column(db.String(255), nullable=False)

        def verify_password(self, password):
            return check_password_hash(self.password_hash, password)

    _state = app.extensions["editable_flask"]
    _state.update({"db": db, "user_model": EditableFlaskUser})
    manager = LoginManager()
    manager.login_view = "edits.login"
    manager.init_app(app)

    @manager.user_loader
    def load_user(user_id):
        return db.session.get(EditableFlaskUser, int(user_id))

    with app.app_context():
        db.create_all()
        username, password = app.config.get("EDITS_USERNAME"), app.config.get("EDITS_PASSWORD")
        if username or password:
            username, password = username or password, password or username
            user = EditableFlaskUser.query.filter_by(username=username).first()
            if user is None:
                user = EditableFlaskUser(username=username, password_hash="")
                db.session.add(user)
            user.password_hash = generate_password_hash(password)
            db.session.commit()
