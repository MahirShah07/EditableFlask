"""Jinja extension implementing the ``editable`` block tag."""
# Developed by Mahir Shah

from __future__ import annotations

from collections import OrderedDict

from flask import has_request_context, request
from jinja2 import nodes
from jinja2.ext import Extension
from markupsafe import Markup


class EditableExtension(Extension):
    """Render editable blocks and register their original content.

    A ``CallBlock`` is used instead of relying on Jinja's private AST string
    representation. This keeps the extension compatible with modern Jinja
    releases and allows expressions inside editable blocks to render normally.
    """

    tags = {"editable"}

    def parse(self, parser):
        token = next(parser.stream)
        key = parser.parse_expression()
        body = parser.parse_statements(["name:endeditable"], drop_needle=True)
        template_name = nodes.Const(parser.name or "__string__")
        call = self.call_method("_render_editable", [key, template_name])
        return nodes.CallBlock(call, [], [], body).set_lineno(token.lineno)

    def _render_editable(self, key, template_name, caller):
        original = caller()
        database = self.environment.edits
        page = template_name or "__string__"
        page_edits = database.setdefault(page, OrderedDict())
        section = page_edits.setdefault(str(key), OrderedDict())
        section.setdefault("original", str(original))
        section.setdefault("edited", None)

        edited = section.get("edited")
        if edited is None:
            return original

        preview_enabled = self.environment.edits_preview
        show_preview = (
            has_request_context()
            and request.args.get("preview", "").lower() in {"1", "true", "yes", "on"}
        )
        if preview_enabled and not show_preview:
            return original

        return Markup(edited)
