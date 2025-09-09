from django import template

register = template.Library()

@register.filter(name='sub')
def subtract(value, arg):
    """Soustrait l'argument de la valeur"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0