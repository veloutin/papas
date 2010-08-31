from django.template import Template, TemplateDoesNotExist

from . import models

_templates = {}

def add_template(template_name, text):
    global _templates
    _templates[template_name] = text

def load_template_source(template_name, dirs):
    global _templates
    if not template_name in _templates:
        raise TemplateDoesNotExist, template_name
    return _templates[template_name], template_name
load_template_source.is_usable = True
