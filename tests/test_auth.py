from flask import Flask

from EditableFlask import Edits


def test_sql_login(tmp_path):
    app = Flask(__name__)
    app.config.update(
        TESTING=True,
        SECRET_KEY="test-only",
        EDITS_PATH=tmp_path,
        SQL_EDITS_LOCKED=True,
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{tmp_path / 'users.db'}",
        EDITS_USERNAME="admin",
        EDITS_PASSWORD="correct-horse",
    )
    Edits(app)
    client = app.test_client()
    assert client.get("/edits/").status_code == 302
    response = client.post(
        "/edits/login", data={"username": "admin", "password": "correct-horse"}
    )
    assert response.status_code == 302
    assert client.get("/edits/").status_code == 200
