from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Utilisateur, Gerant, Client, Serveur, Admin,
    Categorie, Produit, Panier, Commande,
    Paiement, AbonnementNewsletter, Contact
)

# ----------------------------------------
# UTILISATEUR PERSONNALISÉ
# ----------------------------------------

@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'telephone', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'telephone')
    ordering = ('username',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informations personnelles', {'fields': ('first_name', 'last_name', 'email', 'telephone', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates importantes', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'telephone', 'role', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )

# ----------------------------------------
# ROLES SPÉCIFIQUES
# ----------------------------------------

@admin.register(Gerant)
class GerantAdmin(admin.ModelAdmin):
    list_display = ('utilisateur',)

# @admin.register(Client)
# class ClientAdmin(admin.ModelAdmin):
#     list_display = ('utilisateur',)

@admin.register(Serveur)
class ServeurAdmin(admin.ModelAdmin):
    list_display = ('utilisateur',)

@admin.register(Admin)
class AdminRoleAdmin(admin.ModelAdmin):  # éviter conflit avec admin.site
    list_display = ('utilisateur',)


# ----------------------------------------
# CATÉGORIE
# ----------------------------------------

@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ('nom', 'slug')
    prepopulated_fields = {"slug": ("nom",)}
    search_fields = ('nom',)
    list_filter = ('nom',)


# ----------------------------------------
# PRODUITS
# ----------------------------------------

@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = ('nom', 'categorie', 'prix', 'quantite_disponible', 'gerant')
    search_fields = ('nom', 'description')
    list_filter = ('categorie', 'gerant')


# ----------------------------------------
# PANIER
# ----------------------------------------

# @admin.register(Panier)
# class PanierAdmin(admin.ModelAdmin):
#     list_display = ('client',)
#     search_fields = ('client__utilisateur__username',)


# # ----------------------------------------
# # COMMANDE
# # ----------------------------------------

# @admin.register(Commande)
# class CommandeAdmin(admin.ModelAdmin):
#     list_display = ('panier', 'produit', 'quantite', 'date_commande')
#     search_fields = ('produit__nom',)
#     list_filter = ('date_commande',)


# ----------------------------------------
# PAIEMENT
# ----------------------------------------

@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ('commande', 'montant', 'date_paiement', 'statut')
    list_filter = ('statut', 'date_paiement')


# ----------------------------------------
# ABONNEMENT NEWSLETTER
# ----------------------------------------

@admin.register(AbonnementNewsletter)
class AbonnementNewsletterAdmin(admin.ModelAdmin):
    list_display = ('email', 'date_abonnement', 'actif')
    list_filter = ('actif',)


# ----------------------------------------
# CONTACT
# ----------------------------------------

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('nom', 'email', 'sujet', 'date_contact')
    search_fields = ('nom', 'email', 'sujet')
    list_filter = ('date_contact',)
