from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Q, Count
from django import forms
from .models import (
    Utilisateur, Gerant, Client, Serveur, Admin,
    Categorie, Produit, Panier, LignePanier, AdresseLivraison,
    Commande, LigneCommande, Coupon, Paiement, 
    AbonnementNewsletter, ContactMessage, HistoriqueAction, Notification
)

# ------------------- FORMULAIRES PERSONNALISÉS -------------------
class ProduitForm(forms.ModelForm):
    class Meta:
        model = Produit
        fields = '__all__'
        widgets = {
            'description_longue': forms.Textarea(attrs={'rows': 3}),
            'ingredients': forms.Textarea(attrs={'rows': 3}),
        }



# ------------------- FILTRES PERSONNALISÉS -------------------
class RoleListFilter(admin.SimpleListFilter):
    title = 'Rôle'
    parameter_name = 'role'

    def lookups(self, request, model_admin):
        return Utilisateur.ROLE_CHOICES

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(role=self.value())
        return queryset

class StockFilter(admin.SimpleListFilter):
    title = 'Statut du stock'
    parameter_name = 'stock_status'

    def lookups(self, request, model_admin):
        return (
            ('in_stock', 'En stock'),
            ('low_stock', 'Stock faible'),
            ('out_of_stock', 'Rupture de stock'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'in_stock':
            return queryset.filter(quantite_disponible__gt=5)
        if self.value() == 'low_stock':
            return queryset.filter(quantite_disponible__gt=0, quantite_disponible__lte=5)
        if self.value() == 'out_of_stock':
            return queryset.filter(quantite_disponible=0)
        return queryset

class PopularProductFilter(admin.SimpleListFilter):
    title = 'Produit populaire'
    parameter_name = 'popular'

    def lookups(self, request, model_admin):
        return (
            ('popular', 'Populaire'),
            ('not_popular', 'Non populaire'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'popular':
            return queryset.filter(est_populaire=True)
        if self.value() == 'not_popular':
            return queryset.filter(est_populaire=False)
        return queryset

# ------------------- ACTIONS ADMIN PERSONNALISÉES -------------------
class ExportCSVMixin:
    """Mixin pour exporter les données sélectionnées en CSV"""
    @admin.action(description='Exporter en CSV')
    def export_as_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse
        from io import StringIO

        model_name = self.model.__name__
        field_names = [field.name for field in self.model._meta.fields]
        
        f = StringIO()
        writer = csv.writer(f)
        writer.writerow(field_names)
        
        for obj in queryset:
            writer.writerow([getattr(obj, field) for field in field_names])
        
        f.seek(0)
        response = HttpResponse(f, content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename={model_name.lower()}s.csv'
        return response

class TogglePopularActionMixin:
    """Mixin pour basculer l'état populaire des produits"""
    @admin.action(description='Basculer état populaire')
    def toggle_popular(self, request, queryset):
        for obj in queryset:
            obj.est_populaire = not obj.est_populaire
            obj.save()
        self.message_user(request, f"État 'populaire' modifié pour {queryset.count()} produits.")

# ------------------- CLASSES ADMIN DE BASE -------------------
class BaseAdmin(admin.ModelAdmin, ExportCSVMixin):
    list_per_page = 50
    actions = ['export_as_csv']

class BaseRoleAdmin(BaseAdmin):
    list_display = ('get_username', 'get_email', 'get_date_joined')
    search_fields = ('utilisateur__username', 'utilisateur__email')
    list_select_related = ('utilisateur',)
    readonly_fields = ('get_user_link',)

    def get_username(self, obj):
        return obj.utilisateur.username
    get_username.short_description = 'Nom d\'utilisateur'
    get_username.admin_order_field = 'utilisateur__username'

    def get_email(self, obj):
        return obj.utilisateur.email
    get_email.short_description = 'Email'
    get_email.admin_order_field = 'utilisateur__email'

    def get_date_joined(self, obj):
        return obj.utilisateur.date_joined
    get_date_joined.short_description = 'Date d\'inscription'
    get_date_joined.admin_order_field = 'utilisateur__date_joined'

    def get_user_link(self, obj):
        url = reverse('admin:app_utilisateur_change', args=[obj.utilisateur.id])
        return format_html('<a href="{}">{}</a>', url, obj.utilisateur.username)
    get_user_link.short_description = 'Lien vers l\'utilisateur'

# ------------------- ADMIN POUR CHAQUE MODÈLE -------------------
@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin, ExportCSVMixin):
    list_display = ('username', 'email', 'get_role_display', 'telephone', 'is_staff', 'is_active', 'date_joined')
    list_filter = (RoleListFilter, 'is_staff', 'is_superuser', 'is_active', 'groups', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'telephone')
    ordering = ('-date_joined',)
    readonly_fields = ('last_login', 'date_joined')
    actions = ['activate_users', 'deactivate_users', 'export_as_csv']

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informations personnelles', {'fields': ('first_name', 'last_name', 'email', 'telephone', 'role')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Dates importantes', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'telephone', 'role', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )

    def get_role_display(self, obj):
        return obj.get_role_display()
    get_role_display.short_description = 'Rôle'

    @admin.action(description='Activer les utilisateurs')
    def activate_users(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} utilisateurs activés.")

    @admin.action(description='Désactiver les utilisateurs')
    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} utilisateurs désactivés.")

@admin.register(Gerant)
class GerantAdmin(BaseRoleAdmin):
    pass

@admin.register(Client)
class ClientAdmin(BaseRoleAdmin):
    pass

@admin.register(Serveur)
class ServeurAdmin(BaseRoleAdmin):
    pass

@admin.register(Admin)
class AdminRoleAdmin(BaseRoleAdmin):
    pass

@admin.register(Categorie)
class CategorieAdmin(BaseAdmin):
    list_display = ('nom', 'slug', 'image_preview', 'nb_produits')
    prepopulated_fields = {"slug": ("nom",)}
    search_fields = ('nom', 'description')
    readonly_fields = ('image_preview',)
    actions = BaseAdmin.actions + ['clear_image']

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 50px;" />', obj.image.url)
        return "Aucune image"
    image_preview.short_description = 'Aperçu'

    def nb_produits(self, obj):
        return obj.produits.count()
    nb_produits.short_description = 'Nb produits'

    @admin.action(description='Supprimer les images sélectionnées')
    def clear_image(self, request, queryset):
        updated = queryset.update(image=None)
        self.message_user(request, f"{updated} images supprimées.")

@admin.register(Produit)
class ProduitAdmin(BaseAdmin, TogglePopularActionMixin):
    form = ProduitForm
    list_display = ('nom', 'categorie', 'prix', 'promotion', 'quantite_disponible', 'statut_stock', 'est_populaire', 'image_preview')
    list_editable = ('prix', 'promotion', 'quantite_disponible', 'est_populaire')
    search_fields = ('nom', 'description', 'description_longue', 'categorie__nom')
    list_filter = (StockFilter, PopularProductFilter, 'categorie', 'gerant__utilisateur__username')
    readonly_fields = ('image_preview', )
    raw_id_fields = ('gerant',)
    autocomplete_fields = ('categorie',)
    actions = BaseAdmin.actions + ['toggle_popular']

    fieldsets = (
        (None, {
            'fields': ('nom', 'categorie', 'gerant')
        }),
        ('Descriptions', {
            'fields': ('description', 'description_longue'),
            'classes': ('collapse',)
        }),
        ('Prix et stock', {
            'fields': ('prix', 'promotion',  'quantite_disponible')
        }),
        ('Caractéristiques', {
            'fields': ('ingredients', 'allergenes', 'poids_net', 'conseil_conservation'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('image', 'image_preview', 'est_populaire'),
            'classes': ('collapse',)
        }),
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 50px;" />', obj.image.url)
        return "Aucune image"
    image_preview.short_description = 'Aperçu'

    def statut_stock(self, obj):
        return obj.get_statut_stock()
    statut_stock.short_description = 'Statut du stock'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('categorie', 'gerant__utilisateur')

class LignePanierInline(admin.TabularInline):
    model = LignePanier
    extra = 0
    fields = ('produit', 'quantite', 'get_sous_total')
    readonly_fields = ('get_sous_total',)
    autocomplete_fields = ('produit',)
    
    def get_sous_total(self, obj):
        if obj.produit and obj.quantite:
            return f"{obj.produit.prix * obj.quantite:.2f} FCFA"
        return "0.00 FCFA"
    get_sous_total.short_description = 'Sous-total'

@admin.register(Panier)
class PanierAdmin(BaseAdmin):
    list_display = ('id', 'utilisateur', 'session_id', 'date_creation', 'nb_articles', 'total_panier')
    search_fields = ('utilisateur__username', 'session_id')
    list_filter = ('date_creation',)
    inlines = [LignePanierInline]

    def nb_articles(self, obj):
        return obj.lignes.count()
    nb_articles.short_description = 'Articles'

    def total_panier(self, obj):
        total = sum(ligne.produit.prix * ligne.quantite for ligne in obj.lignes.all())
        return f"{total:.2f} FCFA"
    total_panier.short_description = 'Total'

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('lignes__produit')

class LigneCommandeInline(admin.TabularInline):
    model = LigneCommande
    extra = 0
    fields = ('produit', 'quantite', 'prix_unitaire', 'sous_total')
    readonly_fields = ('sous_total',)
    autocomplete_fields = ('produit',)

@admin.register(Commande)
class CommandeAdmin(BaseAdmin):
    list_display = ('id', 'utilisateur', 'date_creation', 'total', 'statut', 'methode_paiement')
    list_filter = ('statut', 'methode_paiement', 'date_creation')
    search_fields = ('utilisateur__username', 'id')
    readonly_fields = ('date_creation', 'total')
    inlines = [LigneCommandeInline]
    actions = BaseAdmin.actions + ['mark_as_shipped', 'mark_as_delivered', 'mark_as_cancelled']

    @admin.action(description='Marquer comme expédié')
    def mark_as_shipped(self, request, queryset):
        queryset.update(statut='en_cours')
        self.message_user(request, f"{queryset.count()} commandes expédiées.")

    @admin.action(description='Marquer comme livré')
    def mark_as_delivered(self, request, queryset):
        queryset.update(statut='livree')
        self.message_user(request, f"{queryset.count()} commandes livrées.")

    @admin.action(description='Annuler les commandes')
    def mark_as_cancelled(self, request, queryset):
        queryset.update(statut='annulee')
        self.message_user(request, f"{queryset.count()} commandes annulées.")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('utilisateur')

@admin.register(AdresseLivraison)
class AdresseLivraisonAdmin(BaseAdmin):
    list_display = ('utilisateur', 'rue', 'ville', 'code_postal', 'pays')
    search_fields = ('utilisateur__username', 'rue', 'ville', 'code_postal')
    list_filter = ('pays', 'ville')
    raw_id_fields = ('utilisateur',)

@admin.register(Coupon)
class CouponAdmin(BaseAdmin):
    list_display = ('code', 'type_reduction', 'valeur', 'actif', 'date_fin', 'usage_actuel', 'usage_max')
    list_filter = ('actif', 'type_reduction', 'date_fin')
    search_fields = ('code',)
    readonly_fields = ('usage_actuel', 'date_creation')
    actions = BaseAdmin.actions + ['activate_coupons', 'deactivate_coupons']

    fieldsets = (
        (None, {
            'fields': ('code', 'type_reduction', 'valeur')
        }),
        ('Validité', {
            'fields': ('date_debut', 'date_fin', 'actif')
        }),
        ('Utilisation', {
            'fields': ('usage_max', 'usage_actuel', 'date_creation')
        }),
    )

    @admin.action(description='Activer les coupons')
    def activate_coupons(self, request, queryset):
        queryset.update(actif=True)
        self.message_user(request, f"{queryset.count()} coupons activés.")

    @admin.action(description='Désactiver les coupons')
    def deactivate_coupons(self, request, queryset):
        queryset.update(actif=False)
        self.message_user(request, f"{queryset.count()} coupons désactivés.")

@admin.register(Paiement)
class PaiementAdmin(BaseAdmin):
    list_display = ('id', 'commande_link', 'montant', 'date_paiement', 'statut')
    list_filter = ('statut', 'date_paiement')
    search_fields = ('commande__id',)
    readonly_fields = ('date_paiement',)
    raw_id_fields = ('commande',)

    def commande_link(self, obj):
        url = reverse('admin:app_commande_change', args=[obj.commande.id])
        return format_html('<a href="{}">Commande #{}</a>', url, obj.commande.id)
    commande_link.short_description = 'Commande'

@admin.register(AbonnementNewsletter)
class AbonnementNewsletterAdmin(BaseAdmin):
    list_display = ('email', 'date_abonnement', 'actif')
    list_filter = ('actif', 'date_abonnement')
    search_fields = ('email',)
    actions = BaseAdmin.actions + ['activate_subscriptions', 'deactivate_subscriptions']

    @admin.action(description='Activer les abonnements')
    def activate_subscriptions(self, request, queryset):
        queryset.update(actif=True)
        self.message_user(request, f"{queryset.count()} abonnements activés.")

    @admin.action(description='Désactiver les abonnements')
    def deactivate_subscriptions(self, request, queryset):
        queryset.update(actif=False)
        self.message_user(request, f"{queryset.count()} abonnements désactivés.")


@admin.register(HistoriqueAction)
class HistoriqueActionAdmin(BaseAdmin):
    list_display = ('utilisateur', 'type_action', 'objet_concerne', 'date_action')
    list_filter = ('type_action', 'date_action')
    search_fields = ('utilisateur__username', 'description', 'objet_concerne')
    readonly_fields = ('date_action',)
    date_hierarchy = 'date_action'

@admin.register(Notification)
class NotificationAdmin(BaseAdmin):
    list_display = ('utilisateur', 'type_notification', 'titre', 'lue', 'date_creation')
    list_filter = ('type_notification', 'lue', 'date_creation')
    search_fields = ('utilisateur__username', 'titre', 'message')
    readonly_fields = ('date_creation',)
    actions = BaseAdmin.actions + ['mark_as_read', 'mark_as_unread']

    @admin.action(description='Marquer comme lu')
    def mark_as_read(self, request, queryset):
        queryset.update(lue=True)
        self.message_user(request, f"{queryset.count()} notifications marquées comme lues.")

    @admin.action(description='Marquer comme non lu')
    def mark_as_unread(self, request, queryset):
        queryset.update(lue=False)
        self.message_user(request, f"{queryset.count()} notifications marquées comme non lues.")