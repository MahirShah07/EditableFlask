import json

import pytest
from flask import Flask, render_template_string

from EditableFlask import Edits


@pytest.fixture()
def app(tmp_path):
    application = Flask(__name__)
    application.config.update(TESTING=True, EDITS_PATH=tmp_path)
    Edits(application)

    @application.get("/")
    def index():
        return render_template_string(
            "{% editable 'heading' %}<h1>Hello {{ name }}</h1>{% endeditable %}",
            name="World",
        )

    return application


def test_initializes_without_legacy_config(app):
    assert app.config["EDITS_LOCKED"] is False
    assert app.config["SQL_EDITS_LOCKED"] is False
    assert app.extensions["editable_flask"]["data_file"].exists()


def test_registers_and_renders_editable_expression(app):
    response = app.test_client().get("/")
    assert response.status_code == 200
    assert response.text == "<h1>Hello World</h1>"
    section = app.extensions["editable_flask"]["database"]["__string__"]["heading"]
    assert section["original"] == "<h1>Hello World</h1>"


def test_saves_and_renders_edited_content(app):
    client = app.test_client()
    client.get("/")
    response = client.post(
        "/edits/save", data={"page": "__string__", "heading": "<h1>Updated</h1>"}
    )
    assert response.status_code == 302
    assert client.get("/").text == "<h1>Updated</h1>"
    stored = json.loads(app.extensions["editable_flask"]["data_file"].read_text())
    assert stored["__string__"]["heading"]["edited"] == "<h1>Updated</h1>"


def test_preview_mode(app):
    client = app.test_client()
    client.get("/")
    client.post("/edits/save", data={"page": "__string__", "heading": "Draft"})
    client.post("/edits/preview", data={"state": "true"})
    assert client.get("/").text == "<h1>Hello World</h1>"
    assert client.get("/?preview=true").text == "Draft"


def test_custom_admin_prefix(app):
    custom = Flask("custom")
    custom.config.update(TESTING=True, EDITS_PATH=app.instance_path, EDITS_URL="/content")
    Edits(custom)
    assert custom.test_client().get("/content/").status_code == 200


def test_static_manager_rejects_path_traversal(app):
    app.config["EDITS_STATIC"] = True
    assert app.test_client().get("/edits/static/../../etc").status_code in {400, 404}
