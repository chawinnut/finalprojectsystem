from django import template

register = template.Library()

@register.filter
def int_range(value):
    try:
        if value is None:
            return []
        return range(1, int(value) + 1)
    except (ValueError, TypeError):
        return []