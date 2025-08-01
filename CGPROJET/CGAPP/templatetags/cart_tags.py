from django import template
from ..models import Panier

register = template.Library()

@register.filter
def get_panier_by_session(session_key):
    try:
        return Panier.objects.get(session_id=session_key)
    except Panier.DoesNotExist:
        return None