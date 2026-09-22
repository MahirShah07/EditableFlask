"""EditableFlask extension for editable regions in Flask templates."""
# Developed by Mahir Shah

from __future__ import annotations

import json
from collections import OrderedDict
from pathlib import Path

from jinja2.environment import copy_cache

from .editable import EditableExtension
from .views import create_edits_blueprint, init_login

__version__ = "2.0.1"


class Edits:
    """Register EditableFlask on an application."""

    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.config.setdefault("EDITS_URL", "/edits")
        app.config.setdefault("EDITS_PREVIEW", False)
        app.config.setdefault("EDITS_SUMMERNOTE", False)
        app.config.setdefault("EDITS_STATIC", False)
        app.config.setdefault("EDITS_LOCKED", False)
        app.config.setdefault("SQL_EDITS_LOCKED", False)
        app.config.setdefault("LOGIN_ROUTE", app.config.get("EDITS_ROUTE", "/login"))

        configured_path = app.config.get("EDITS_PATH") or app.config.get("FILE_PATH")
        if not configured_path:
            configured_path = app.instance_path
        data_directory = Path(configured_path).expanduser().resolve()
        data_directory.mkdir(parents=True, exist_ok=True)
        edits_file = data_directory / "edits.json"

        try:
            with edits_file.open(encoding="utf-8") as file:
                database = json.load(file, object_pairs_hook=OrderedDict)
        except FileNotFoundError:
            database = OrderedDict()
            self._write_database(edits_file, database)
        except json.JSONDecodeError as error:
            raise RuntimeError(f"Invalid EditableFlask data file: {edits_file}") from error

        app.extensions.setdefault("editable_flask", {})
        state = app.extensions["editable_flask"]
        state.update({"database": database, "data_file": edits_file})

        app.jinja_env.add_extension(EditableExtension)
        app.jinja_env.edits = database
        app.jinja_env.edits_preview = bool(app.config["EDITS_PREVIEW"])
        app.jinja_env.edits_cache = copy_cache(app.jinja_env.cache)
        if app.jinja_env.edits_preview:
            app.jinja_env.cache = None

        if app.config["SQL_EDITS_LOCKED"]:
            init_login(app)

        blueprint = create_edits_blueprint()
        app.register_blueprint(blueprint, url_prefix=app.config["EDITS_URL"].rstrip("/"))

    @staticmethod
    def _write_database(path: Path, database):
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(database, indent=2), encoding="utf-8")
        temporary.replace(path)


__all__ = ["Edits", "EditableExtension"]
