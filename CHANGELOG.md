# Changelog

## 2.0.0

- Support Flask 3.1, Jinja 3.1, and Python 3.9 through 3.14.
- Replace private Jinja AST parsing with the supported extension API.
- Add safe defaults and Flask application-factory support.
- Make JSON writes atomic and normalize filesystem paths.
- Repair optional SQL authentication for modern Flask-SQLAlchemy.
- Prevent static-manager path traversal and unsafe ZIP extraction.
- Add automated compatibility, packaging, and PyPI release workflows.
