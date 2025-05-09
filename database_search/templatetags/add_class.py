from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(value, arg):
    css_class = value.field.widget.attrs.get('class', '') + ' ' + arg
    return value.as_widget(attrs={'class': css_class.strip()})