
from django import template
from django.db import models

register = template.Library()

@register.filter
def get_model_fields(instance):
    if not instance:
        return []
    return [{
        'name': field.name,
        'field_type': field.get_internal_type(),
        'value': getattr(instance, field.name) if instance else None
    } for field in instance._meta.fields if isinstance(field, models.ImageField)]

@register.filter
def split_underscore(value):
    return value.replace('_', ' ')

