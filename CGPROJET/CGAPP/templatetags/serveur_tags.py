from django import template
register = template.Library()

@register.filter
def commandes_traitees(serveur):
    return serveur.actions.filter(type_action='commande_statut').count()