from collections import OrderedDict
from jinja2.nodes import Template, TemplateData, Scope, Output
from jinja2.ext import Extension
import re


class EditableExtension(Extension):
    tags = {"editable"}

    def parse(self, parser):
        _db = self.environment.edits
        lineno = int(next(parser.stream).lineno)
        # Get section key
        key = parser.parse_expression().value
        # Read editable section
        section = parser.parse_statements(["name:endeditable"], drop_needle=True)
        # Render original section contents
        if isinstance(section, Template):
            original = section.render()
        elif isinstance(section, list):
            original = "".join(str(s) for s in section)
        else:
            original = section
        new = ''
        RemoveString = """Output(nodes=[TemplateData(data=" """
        RemoveString = RemoveString[:-1]
        for i in original:
            new = new + str(i)
            if new == "Output(nodes=[TemplateData(data='" or new == RemoveString:
                new = ''
        original = new[:-4]
        _db.setdefault(parser.name, OrderedDict())
        _db[parser.name].setdefault(key, OrderedDict())
        _db[parser.name][key].setdefault("original", original)
        _db[parser.name][key].setdefault("edited", None)
        if _db[parser.name][key].get("edited", None):
            if self.environment.edits_preview:
                if self.environment.globals["request"].args.get("preview"):
                    return [Output([TemplateData(_db[parser.name][key]["edited"])])]
                else:
                    return section
            else:
                return [Output([TemplateData(_db[parser.name][key]["edited"])])]
        else:
            return section
