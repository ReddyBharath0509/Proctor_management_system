from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary using a key"""
    return dictionary.get(key)

@register.filter
def split(value, delimiter=','):
    """Split a string by the given delimiter and return a list."""
    return value.split(delimiter) 