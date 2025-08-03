from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from .models import Produit, Categorie, Panier, Commande, Contact, Utilisateur,LignePanier, AdresseLivraison, Coupon,Client, Gerant, Serveur, HistoriqueAction, Notification
from .forms import ContactForm, NewsletterForm, CommandeForm,InscriptionForm, ConnexionForm, CreerGerantForm, CreerServeurForm, ProduitForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db import models
from datetime import timedelta


# ==================== UTILITAIRES ====================

def enregistrer_action(utilisateur, type_action, description, objet_concerne=None, objet_id=None, details=None, request=None):
    """
    Enregistre une action dans l'historique
    """
    adresse_ip = None
    if request:
        adresse_ip = request.META.get('REMOTE_ADDR')
    
    HistoriqueAction.objects.create(
        utilisateur=utilisateur,
        type_action=type_action,
        description=description,
        objet_concerne=objet_concerne,
        objet_id=objet_id,
        details_supplementaires=details,
        adresse_ip=adresse_ip
    )

def creer_notification(utilisateur, type_notification, titre, message, commande=None):
    """
    Crée une notification pour un utilisateur
    """
    Notification.objects.create(
        utilisateur=utilisateur,
        type_notification=type_notification,
        titre=titre,
        message=message,
        commande=commande
    )


#inscription et connexion
class InscriptionView(CreateView):
    model = Utilisateur
    form_class = InscriptionForm
    template_name = 'frontOfice/compte/inscription.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)  
        messages.success(self.request, "Inscription réussie !")
        return response
    
def connexion(request):
    if request.method == 'POST':
        form = ConnexionForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f"Bienvenue {user.username} !")
                return redirect('home')
            else:
                messages.error(request, "Identifiants incorrects")
    else:
        form = ConnexionForm()
    
    return render(request, 'frontOfice/compte/connexion.html', {'form': form})

def deconnexion(request):
    logout(request)
    messages.success(request, "Vous avez été déconnecté avec succès.")
    return redirect('home')

# Vue Accueil

def detail_categorie(request, id):
    categorie = get_object_or_404(Categorie, id=id)
    return render(request, 'frontOfice/produits/detail.html', {'categorie': categorie})

def categories_context(request):
    categories = Categorie.objects.all()
    return {'categories': categories}

def home(request):
    produits_nouveautes = Produit.objects.order_by('-id')[:8]
    produits_populaires = Produit.objects.order_by('?')[:4]
    categories = Categorie.objects.all()[:6]
    
    context = {
        'nouveautes': produits_nouveautes,
        'populaires': produits_populaires,
        'categories': categories,
    }
    return render(request, 'frontOfice/index.html', context)

def apropos(request):
    return render(request,'frontOfice/apropos.html')

# Liste des Produits
class ProduitListView(ListView):
    model = Produit
    template_name = 'frontOfice/produits/liste.html'
    context_object_name = 'produits'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = super().get_queryset()
        categorie_slug = self.kwargs.get('categorie_slug')
        if categorie_slug:
            categorie = get_object_or_404(Categorie, slug=categorie_slug)
            queryset = queryset.filter(categorie=categorie)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Categorie.objects.all()
        return context

# Détail Produit
class ProduitDetailView(DetailView):
    model = Produit
    template_name = 'fontOfice/produits/detail.html'
    context_object_name = 'produit'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['produits_similaires'] = Produit.objects.filter(
            categorie=self.object.categorie
        ).exclude(id=self.object.id)[:4]
        return context

# Gestion Panier
# class PanierView(ListView):
#     template_name = 'frontOfice/paniers/panier.html'

#     def get(self, request):
#         if request.user.is_authenticated:
#             panier, created = Panier.objects.get_or_create(client__utilisateur=request.user)
#         else:
#             panier_id = request.session.get('panier_id')
#             if panier_id:
#                 panier = Panier.objects.filter(id=panier_id).first()
#             else:
#                 panier = Panier.objects.create()
#                 request.session['panier_id'] = panier.id

#         commandes = panier.commande_set.all()
#         total = sum(commande.produit.prix * commande.quantite for commande in commandes)

#         return render(request, self.template_name, {
#             'commandes': commandes,
#             'total': total,
#         })

# def ajouter_au_panier(request, produit_id):
#     produit = get_object_or_404(Produit, id=produit_id)

#     if request.user.is_authenticated:
#         panier, _ = Panier.objects.get_or_create(client__utilisateur=request.user)
#     else:
#         panier_id = request.session.get('panier_id')
#         if panier_id:
#             panier = Panier.objects.filter(id=panier_id).first()
#         else:
#             panier = Panier.objects.create()
#             request.session['panier_id'] = panier.id

#     commande, created = Commande.objects.get_or_create(
#         panier=panier,
#         produit=produit,
#         defaults={'quantite': 1}
#     )
#     if not created:
#         commande.quantite += 1
#         commande.save()

#     messages.success(request, f"{produit.nom} ajouté à votre panier")
#     return redirect('panier')


# def supprimer_du_panier(request, commande_id):
#     if request.user.is_authenticated:
#         panier = Panier.objects.filter(client__utilisateur=request.user).first()
#     else:
#         panier_id = request.session.get('panier_id')
#         panier = Panier.objects.filter(id=panier_id).first()

#     commande = get_object_or_404(Commande, id=commande_id, panier=panier)
#     commande.delete()

#     messages.success(request, "Produit retiré du panier")
#     return redirect('panier')

# def modifier_quantite(request, commande_id):
#     commande = get_object_or_404(Commande, id=commande_id, panier__client__utilisateur=request.user)
#     action = request.GET.get('action')
    
#     if action == 'increase':
#         commande.quantite += 1
#     elif action == 'decrease' and commande.quantite > 1:
#         commande.quantite -= 1
    
#     commande.save()
#     return redirect('panier')

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Produit, Panier, LignePanier, Commande

def base_view(request):
    cart_items_count = 0
    if request.user.is_authenticated:
        panier = Panier.objects.filter(utilisateur=request.user).first()
    else:
        panier = Panier.objects.filter(session_id=request.session.session_key).first()
    
    if panier:
        cart_items_count = panier.lignes.count()
    
    return render(request, 'base.html', {'cart_items_count': cart_items_count})

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Produit, Panier, LignePanier, Commande

def ajouter_au_panier(request, produit_id):
    produit = get_object_or_404(Produit, id=produit_id)

    if request.user.is_authenticated:
        panier, _ = Panier.objects.get_or_create(utilisateur=request.user)
    else:
        session_id = request.session.session_key or request.session.save()
        panier, _ = Panier.objects.get_or_create(session_id=request.session.session_key)

    ligne, created = LignePanier.objects.get_or_create(panier=panier, produit=produit)
    if not created:
        ligne.quantite += 1
        ligne.save()
        messages.success(request, f"Quantité de {produit.nom} augmentée dans votre panier")
    else:
        messages.success(request, f"{produit.nom} ajouté à votre panier")

    return redirect('produits')

def voir_panier(request):
    if request.user.is_authenticated:
        panier = Panier.objects.filter(utilisateur=request.user).first()
    else:
        panier = Panier.objects.filter(session_id=request.session.session_key).first()
    
    total = 0
    if panier:
        total = sum(l.produit.prix * l.quantite for l in panier.lignes.all())
    
    return render(request, 'frontOfice/paniers/panier.html', {
        'panier': panier,
        'total': total
    })

def augmenter_quantite(request, ligne_id):
    if request.user.is_authenticated:
        ligne = get_object_or_404(LignePanier, id=ligne_id, panier__utilisateur=request.user)
    else:
        ligne = get_object_or_404(LignePanier, id=ligne_id, panier__session_id=request.session.session_key)
    
    ligne.quantite += 1
    ligne.save()
    messages.success(request, f"Quantité de {ligne.produit.nom} augmentée à {ligne.quantite}")
    return redirect('panier')

def diminuer_quantite(request, ligne_id):
    if request.user.is_authenticated:
        ligne = get_object_or_404(LignePanier, id=ligne_id, panier__utilisateur=request.user)
    else:
        ligne = get_object_or_404(LignePanier, id=ligne_id, panier__session_id=request.session.session_key)
    
    if ligne.quantite > 1:
        ligne.quantite -= 1
        ligne.save()
        messages.success(request, f"Quantité de {ligne.produit.nom} diminuée à {ligne.quantite}")
    else:
        produit_nom = ligne.produit.nom
        ligne.delete()
        messages.warning(request, f"{produit_nom} retiré de votre panier")
    return redirect('panier')

def supprimer_du_panier(request, ligne_id):
    if request.user.is_authenticated:
        ligne = get_object_or_404(LignePanier, id=ligne_id, panier__utilisateur=request.user)
    else:
        ligne = get_object_or_404(LignePanier, id=ligne_id, panier__session_id=request.session.session_key)
    
    produit_nom = ligne.produit.nom
    ligne.delete()
    messages.warning(request, f"{produit_nom} retiré de votre panier")
    return redirect('panier')

def vider_panier(request):
    if request.user.is_authenticated:
        panier = get_object_or_404(Panier, utilisateur=request.user)
    else:
        panier = get_object_or_404(Panier, session_id=request.session.session_key)
    
    count = panier.lignes.count()
    panier.lignes.all().delete()
    
    if count > 0:
        messages.warning(request, "Votre panier a été vidé")
    else:
        messages.info(request, "Votre panier était déjà vide")
    
    return redirect('panier')


# Checkout
class CheckoutView(LoginRequiredMixin, View):
    template_name = 'frontOfice/panier/checkout.html'
    form_class = CommandeForm
    login_url = reverse_lazy('connexion')  # ou 'connexion'

    def get(self, request):
        panier = Panier.objects.filter(client__utilisateur=request.user).first()
        if not panier or not panier.commande_set.exists():
            messages.error(request, "Votre panier est vide")
            return redirect('panier')

        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)
        panier = Panier.objects.filter(client__utilisateur=request.user).first()

        if not panier or not panier.commande_set.exists():
            messages.error(request, "Votre panier est vide")
            return redirect('panier')

        if form.is_valid():
            # Traitement commande ici...
            panier.commande_set.all().delete()
            messages.success(request, "Votre commande a été passée avec succès!")
            return redirect('commande_confirmation')

        return render(request, self.template_name, {'form': form})


# Contact

def contact_success(request):
    return render(request, 'frontOfice/contactSuccess.html')

class ContactView(CreateView):
    model = Contact
    form_class = ContactForm
    template_name = 'frontOfice/contact.html'
    success_url = reverse_lazy('contact_success')  
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Votre message a été envoyé avec succès! Nous vous répondrons dans les plus brefs délais.")
        return response
    
    def form_invalid(self, form):
        messages.error(self.request, "Veuillez corriger les erreurs dans le formulaire.")
        return super().form_invalid(form)
# Newsletter
class NewsletterSubscribeView(CreateView):
    def post(self, request):
        form = NewsletterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Merci pour votre abonnement !")
        else:
            messages.error(request, "Email invalide ou déjà inscrit.")
        return redirect(request.META.get('HTTP_REFERER', '/')) 

# Compte Utilisateur
class ProfileView(LoginRequiredMixin, UpdateView):
    template_name = 'frontOfice/compte/profil.html'
    fields = ['first_name', 'last_name', 'email', 'telephone']
    success_url = reverse_lazy('profile')
    
    def get_object(self):
        return self.request.user


    from django.shortcuts import render, redirect, get_object_or_404

@login_required(login_url='connexion')
def valider_commande(request):
    # Récupérer le panier de l'utilisateur
    panier = get_object_or_404(Panier, utilisateur=request.user)
    
    if request.method == 'POST':
        # Traitement du formulaire de commande
        adresse_id = request.POST.get('adresse_id')
        methode_paiement = request.POST.get('methode_paiement')
        coupon_code = request.POST.get('coupon_code')

        # Création de la commande
        total = panier.total
        commande = Commande.objects.create(
            utilisateur=request.user,
            total=total,
            adresse_livraison_id=adresse_id,
            methode_paiement=methode_paiement
        )

        # 🔁 Création automatique du profil Client si inexistant
        if not hasattr(request.user, 'client'):
            Client.objects.create(utilisateur=request.user)

        # Redirection vers la page de confirmation
        return redirect('suivi_commande', commande_id=commande.id)
    
    # Afficher le formulaire de commande
    return render(request, 'frontOfice/commandes/confirmation.html')

@login_required
def suivi_commande(request, commande_id):
    commande = get_object_or_404(Commande, id=commande_id, utilisateur=request.user)
    return render(request, 'frontOfice/commandes/suivi.html', {'commande': commande})

@login_required
def ajouter_adresse(request):
    if request.method == 'POST':
        # Traitement du formulaire d'adresse
        rue = request.POST.get('rue')
        ville = request.POST.get('ville')
        code_postal = request.POST.get('code_postal')
        pays = request.POST.get('pays')
        
        adresse = AdresseLivraison.objects.create(
            utilisateur=request.user,
            rue=rue,
            ville=ville,
            code_postal=code_postal,
            pays=pays
        )
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'adresse_id': adresse.id})
        
        return redirect('valider_commande')
    
    return render(request, 'frontOfice/commandes/ajouter_adresse.html')

@login_required
def appliquer_coupon(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        code = request.POST.get('code')
        try:
            coupon = Coupon.objects.get(code=code, actif=True)
            return JsonResponse({
                'success': True,
                'reduction': coupon.reduction,
                'code': coupon.code
            })
        except Coupon.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Code coupon invalide'})


# ==================== DASHBOARDS ====================

# Dashboard Admin
@login_required
def dashboard_admin(request):
    # Vérifier si l'utilisateur est admin
    if request.user.role != 'admin':
        messages.error(request, "Accès non autorisé")
        return redirect('home')
    
    # Statistiques générales
    total_utilisateurs = Utilisateur.objects.count()
    total_produits = Produit.objects.count()
    total_commandes = Commande.objects.count()
    total_revenus = Commande.objects.aggregate(total=models.Sum('total'))['total'] or 0
    
    # Commandes récentes
    commandes_recentes = Commande.objects.select_related('utilisateur').order_by('-date_creation')[:5]
    
    # Produits les plus vendus (simulation)
    produits_populaires = Produit.objects.order_by('-quantite_disponible')[:5]
    
    # Messages de contact non lus
    messages_contact = Contact.objects.order_by('-date_contact')[:5]
    
    # Utilisateurs par rôle
    stats_roles = {
        'clients': Utilisateur.objects.filter(role='client').count(),
        'serveurs': Utilisateur.objects.filter(role='serveur').count(),
        'gerants': Utilisateur.objects.filter(role='gerant').count(),
        'admins': Utilisateur.objects.filter(role='admin').count(),
    }
    
    # Historique des actions récentes (toutes les actions)
    actions_recentes = HistoriqueAction.objects.select_related('utilisateur').order_by('-date_action')[:10]
    
    # Notifications non lues pour l'admin
    notifications_non_lues = Notification.objects.filter(utilisateur=request.user, lue=False).count()
    
    # Actions par type (statistiques)
    stats_actions = {
        'connexions': HistoriqueAction.objects.filter(type_action='connexion').count(),
        'commandes': HistoriqueAction.objects.filter(type_action='commande_statut').count(),
        'produits': HistoriqueAction.objects.filter(type_action__in=['produit_ajout', 'produit_modif', 'produit_suppr']).count(),
        'utilisateurs': HistoriqueAction.objects.filter(type_action='utilisateur_creation').count(),
    }
    
    context = {
        'total_utilisateurs': total_utilisateurs,
        'total_produits': total_produits,
        'total_commandes': total_commandes,
        'total_revenus': total_revenus,
        'commandes_recentes': commandes_recentes,
        'produits_populaires': produits_populaires,
        'messages_contact': messages_contact,
        'stats_roles': stats_roles,
        'actions_recentes': actions_recentes,
        'notifications_non_lues': notifications_non_lues,
        'stats_actions': stats_actions,
    }
    
    return render(request, 'dashboards/admin_dashboard.html', context)


# Dashboard Serveur
@login_required
def dashboard_serveur(request):
    # Vérifier si l'utilisateur est serveur
    if request.user.role != 'serveur':
        messages.error(request, "Accès non autorisé")
        return redirect('home')
    
    # Commandes à traiter par priorité
    commandes_en_attente = Commande.objects.filter(statut='en_attente').order_by('-date_creation')[:20]
    commandes_en_cours = Commande.objects.filter(statut='en_cours').order_by('-date_creation')[:15]
    commandes_livrees = Commande.objects.filter(statut='livree').order_by('-date_creation')[:10]
    
    # Statistiques détaillées du serveur
    aujourd_hui = timezone.now().date()
    cette_semaine = aujourd_hui - timedelta(days=7)
    ce_mois = timezone.now().replace(day=1).date()
    
    stats_serveur = {
        'commandes_jour': Commande.objects.filter(date_creation__date=aujourd_hui).count(),
        'commandes_semaine': Commande.objects.filter(date_creation__date__gte=cette_semaine).count(),
        'commandes_mois': Commande.objects.filter(date_creation__date__gte=ce_mois).count(),
        'commandes_traitees_aujourd_hui': HistoriqueAction.objects.filter(
            utilisateur=request.user,
            type_action='commande_statut',
            date_action__date=aujourd_hui
        ).count(),
    }
    
    # Commandes par statut pour vue d'ensemble
    commandes_par_statut = {
        'en_attente': Commande.objects.filter(statut='en_attente').count(),
        'en_cours': Commande.objects.filter(statut='en_cours').count(),
        'livree': Commande.objects.filter(statut='livree').count(),
        'annulee': Commande.objects.filter(statut='annulee').count(),
    }
    
    # Mes actions récentes
    mes_actions_recentes = HistoriqueAction.objects.filter(
        utilisateur=request.user
    ).order_by('-date_action')[:10]
    
    # Produits les plus commandés (pour information)
    produits_populaires = Produit.objects.order_by('-quantite_disponible')[:5]
    
    # Notifications non lues
    notifications_non_lues = Notification.objects.filter(utilisateur=request.user, lue=False).count()
    
    context = {
        'commandes_en_attente': commandes_en_attente,
        'commandes_en_cours': commandes_en_cours,
        'commandes_livrees': commandes_livrees,
        'stats_serveur': stats_serveur,
        'commandes_par_statut': commandes_par_statut,
        'mes_actions_recentes': mes_actions_recentes,
        'produits_populaires': produits_populaires,
        'notifications_non_lues': notifications_non_lues,
        # Compatibilité avec l'ancien template
        'total_commandes_jour': stats_serveur['commandes_jour'],
    }
    
    return render(request, 'dashboards/serveur_dashboard.html', context)


# Dashboard Gérant
@login_required
def dashboard_gerant(request):
    # Vérifier si l'utilisateur est gérant
    if request.user.role != 'gerant':
        messages.error(request, "Accès non autorisé")
        return redirect('home')
    
    # Statistiques business
    total_revenus_mois = Commande.objects.filter(
        date_creation__month=timezone.now().month,
        date_creation__year=timezone.now().year
    ).aggregate(total=models.Sum('total'))['total'] or 0
    
    commandes_mois = Commande.objects.filter(
        date_creation__month=timezone.now().month,
        date_creation__year=timezone.now().year
    ).count()
    
    # Produits du gérant
    try:
        gerant_obj = Gerant.objects.get(utilisateur=request.user)
        mes_produits = Produit.objects.filter(gerant=gerant_obj)
        produits_stock_faible = mes_produits.filter(quantite_disponible__lt=10)
    except Gerant.DoesNotExist:
        mes_produits = Produit.objects.none()
        produits_stock_faible = Produit.objects.none()
    
    # Commandes récentes pour les produits du gérant
    commandes_mes_produits = Commande.objects.all().order_by('-date_creation')[:10]
    
    # SUPERVISION DES SERVEURS
    # Liste des serveurs actifs
    serveurs = Utilisateur.objects.filter(role='serveur')
    
    # Activité des serveurs (actions récentes)
    activite_serveurs = []
    for serveur in serveurs:
        actions_serveur = HistoriqueAction.objects.filter(
            utilisateur=serveur,
            type_action='commande_statut'
        ).order_by('-date_action')[:5]
        
        commandes_traitees_aujourd_hui = HistoriqueAction.objects.filter(
            utilisateur=serveur,
            type_action='commande_statut',
            date_action__date=timezone.now().date()
        ).count()
        
        activite_serveurs.append({
            'serveur': serveur,
            'actions_recentes': actions_serveur,
            'commandes_aujourd_hui': commandes_traitees_aujourd_hui,
        })
    
    # Statistiques globales des serveurs
    stats_serveurs = {
        'total_serveurs': serveurs.count(),
        'commandes_traitees_mois': HistoriqueAction.objects.filter(
            utilisateur__role='serveur',
            type_action='commande_statut',
            date_action__month=timezone.now().month,
            date_action__year=timezone.now().year
        ).count(),
        'serveurs_actifs_aujourd_hui': HistoriqueAction.objects.filter(
            utilisateur__role='serveur',
            date_action__date=timezone.now().date()
        ).values('utilisateur').distinct().count(),
    }
    
    # Commandes par statut pour supervision
    commandes_par_statut = {
        'en_attente': Commande.objects.filter(statut='en_attente').count(),
        'en_cours': Commande.objects.filter(statut='en_cours').count(),
        'livree': Commande.objects.filter(statut='livree').count(),
        'annulee': Commande.objects.filter(statut='annulee').count(),
    }
    
    # Notifications non lues pour le gérant
    notifications_non_lues = Notification.objects.filter(utilisateur=request.user, lue=False).count()
    
    context = {
        'total_revenus_mois': total_revenus_mois,
        'commandes_mois': commandes_mois,
        'mes_produits': mes_produits,
        'produits_stock_faible': produits_stock_faible,
        'commandes_mes_produits': commandes_mes_produits,
        'nb_mes_produits': mes_produits.count(),
        # Supervision des serveurs
        'serveurs': serveurs,
        'activite_serveurs': activite_serveurs,
        'stats_serveurs': stats_serveurs,
        'commandes_par_statut': commandes_par_statut,
        'notifications_non_lues': notifications_non_lues,
    }
    
    return render(request, 'dashboards/gerant_dashboard.html', context)


# Action pour changer le statut d'une commande (pour serveurs)
@login_required
def changer_statut_commande(request, commande_id):
    if request.user.role != 'serveur':
        messages.error(request, "Accès non autorisé")
        return redirect('home')
    
    if request.method == 'POST':
        commande = get_object_or_404(Commande, id=commande_id)
        ancien_statut = commande.statut
        nouveau_statut = request.POST.get('statut')
        
        if nouveau_statut in ['en_attente', 'en_cours', 'livree', 'annulee']:
            commande.statut = nouveau_statut
            commande.save()
            
            # Enregistrer l'action dans l'historique
            enregistrer_action(
                utilisateur=request.user,
                type_action='commande_statut',
                description=f"Changement de statut de '{ancien_statut}' vers '{nouveau_statut}'",
                objet_concerne=f"Commande #{commande.id}",
                objet_id=commande.id,
                details={'ancien_statut': ancien_statut, 'nouveau_statut': nouveau_statut},
                request=request
            )
            
            # Créer une notification pour le client
            titre_notification = ""
            message_notification = ""
            type_notification = ""
            
            if nouveau_statut == 'en_cours':
                titre_notification = "Commande en préparation"
                message_notification = f"Votre commande #{commande.id} est maintenant en préparation."
                type_notification = 'commande_preparation'
            elif nouveau_statut == 'livree':
                titre_notification = "Commande livrée"
                message_notification = f"Votre commande #{commande.id} a été livrée avec succès !"
                type_notification = 'commande_livree'
            elif nouveau_statut == 'annulee':
                titre_notification = "Commande annulée"
                message_notification = f"Votre commande #{commande.id} a été annulée."
                type_notification = 'commande_annulee'
            
            if type_notification:
                creer_notification(
                    utilisateur=commande.utilisateur,
                    type_notification=type_notification,
                    titre=titre_notification,
                    message=message_notification,
                    commande=commande
                )
            
            messages.success(request, f"Statut de la commande #{commande.id} mis à jour")
        else:
            messages.error(request, "Statut invalide")
    
    return redirect('dashboard_serveur')


# Dashboard Client
@login_required
def dashboard_client(request):
    # Vérifier si l'utilisateur est client
    if request.user.role != 'client':
        messages.error(request, "Accès non autorisé")
        return redirect('home')
    
    # Commandes du client
    mes_commandes = Commande.objects.filter(utilisateur=request.user).order_by('-date_creation')
    commandes_recentes = mes_commandes[:5]
    
    # Statistiques du client
    total_commandes = mes_commandes.count()
    total_depense = mes_commandes.aggregate(total=models.Sum('total'))['total'] or 0
    commandes_en_cours = mes_commandes.filter(statut__in=['en_attente', 'en_cours']).count()
    
    # Panier actuel
    panier = None
    total_panier = 0
    nb_articles_panier = 0
    
    if request.user.is_authenticated:
        try:
            panier = Panier.objects.get(utilisateur=request.user)
            total_panier = sum(ligne.produit.prix * ligne.quantite for ligne in panier.lignes.all())
            nb_articles_panier = sum(ligne.quantite for ligne in panier.lignes.all())
        except Panier.DoesNotExist:
            pass
    
    # Mes adresses
    mes_adresses = AdresseLivraison.objects.filter(utilisateur=request.user).order_by('-date_creation')[:3]
    
    # Produits favoris (simulation - les plus commandés)
    produits_favoris = Produit.objects.all()[:4]  # À améliorer avec une vraie logique
    
    context = {
        'mes_commandes': commandes_recentes,
        'total_commandes': total_commandes,
        'total_depense': total_depense,
        'commandes_en_cours': commandes_en_cours,
        'panier': panier,
        'total_panier': total_panier,
        'nb_articles_panier': nb_articles_panier,
        'mes_adresses': mes_adresses,
        'produits_favoris': produits_favoris,
    }
    
    return render(request, 'dashboards/client_dashboard.html', context)


# Redirection intelligente vers le dashboard approprié
@login_required
def mon_compte(request):
    """
    Redirige l'utilisateur vers son dashboard spécifique selon son rôle
    """
    user_role = request.user.role
    
    if user_role == 'admin':
        return redirect('dashboard_admin')
    elif user_role == 'serveur':
        return redirect('dashboard_serveur')
    elif user_role == 'gerant':
        return redirect('dashboard_gerant')
    elif user_role == 'client':
        return redirect('dashboard_client')
    else:
        # Si le rôle n'est pas défini, rediriger vers le profil par défaut
        messages.warning(request, "Rôle utilisateur non défini. Redirection vers le profil.")
        return redirect('profile')


# ==================== VUES ADMIN POUR CRÉATION D'UTILISATEURS ====================

@login_required
def creer_gerant(request):
    """
    Vue pour que l'admin puisse créer un gérant
    """
    # Vérifier si l'utilisateur est admin
    if request.user.role != 'admin':
        messages.error(request, "Accès non autorisé")
        return redirect('home')
    
    if request.method == 'POST':
        form = CreerGerantForm(request.POST)
        if form.is_valid():
            try:
                gerant_user = form.save()
                
                # Enregistrer l'action dans l'historique
                enregistrer_action(
                    utilisateur=request.user,
                    type_action='utilisateur_creation',
                    description=f"Création d'un compte gérant pour {gerant_user.first_name} {gerant_user.last_name}",
                    objet_concerne=f"Utilisateur {gerant_user.username}",
                    objet_id=gerant_user.id,
                    details={'role': 'gerant', 'email': gerant_user.email},
                    request=request
                )
                
                messages.success(request, f"Gérant '{gerant_user.username}' créé avec succès !")
                return redirect('dashboard_admin')
            except Exception as e:
                messages.error(request, f"Erreur lors de la création du gérant: {str(e)}")
    else:
        form = CreerGerantForm()
    
    return render(request, 'dashboards/admin/creer_gerant.html', {'form': form})


@login_required
def creer_serveur(request):
    """
    Vue pour que l'admin puisse créer un serveur
    """
    # Vérifier si l'utilisateur est admin
    if request.user.role != 'admin':
        messages.error(request, "Accès non autorisé")
        return redirect('home')
    
    if request.method == 'POST':
        form = CreerServeurForm(request.POST)
        if form.is_valid():
            try:
                serveur_user = form.save()
                
                # Enregistrer l'action dans l'historique
                enregistrer_action(
                    utilisateur=request.user,
                    type_action='utilisateur_creation',
                    description=f"Création d'un compte serveur pour {serveur_user.first_name} {serveur_user.last_name}",
                    objet_concerne=f"Utilisateur {serveur_user.username}",
                    objet_id=serveur_user.id,
                    details={'role': 'serveur', 'email': serveur_user.email},
                    request=request
                )
                
                messages.success(request, f"Serveur '{serveur_user.username}' créé avec succès !")
                return redirect('dashboard_admin')
            except Exception as e:
                messages.error(request, f"Erreur lors de la création du serveur: {str(e)}")
    else:
        form = CreerServeurForm()
    
    return render(request, 'dashboards/admin/creer_serveur.html', {'form': form})


@login_required
def liste_utilisateurs(request):
    """
    Vue pour afficher la liste de tous les utilisateurs (pour l'admin)
    """
    # Vérifier si l'utilisateur est admin
    if request.user.role != 'admin':
        messages.error(request, "Accès non autorisé")
        return redirect('home')
    
    # Récupérer tous les utilisateurs groupés par rôle
    utilisateurs = {
        'admins': Utilisateur.objects.filter(role='admin'),
        'gerants': Utilisateur.objects.filter(role='gerant'),
        'serveurs': Utilisateur.objects.filter(role='serveur'),
        'clients': Utilisateur.objects.filter(role='client'),
    }
    
    context = {
        'utilisateurs': utilisateurs,
        'total_utilisateurs': Utilisateur.objects.count()
    }
    
    return render(request, 'dashboards/admin/liste_utilisateurs.html', context)


# ==================== GESTION DES NOTIFICATIONS ====================

@login_required
def mes_notifications(request):
    """
    Affiche toutes les notifications de l'utilisateur connecté
    """
    notifications = Notification.objects.filter(utilisateur=request.user).order_by('-date_creation')
    
    # Marquer les notifications comme lues si demandé
    if request.method == 'POST' and 'marquer_lues' in request.POST:
        notifications.filter(lue=False).update(lue=True)
        messages.success(request, "Toutes les notifications ont été marquées comme lues.")
        return redirect('mes_notifications')
    
    context = {
        'notifications': notifications,
        'notifications_non_lues': notifications.filter(lue=False).count()
    }
    
    return render(request, 'notifications/mes_notifications.html', context)


@login_required
def marquer_notification_lue(request, notification_id):
    """
    Marque une notification spécifique comme lue
    """
    notification = get_object_or_404(Notification, id=notification_id, utilisateur=request.user)
    notification.lue = True
    notification.save()
    
    return JsonResponse({'success': True})


@login_required
def notifications_non_lues_count(request):
    """
    Retourne le nombre de notifications non lues (pour AJAX)
    """
    count = Notification.objects.filter(utilisateur=request.user, lue=False).count()
    return JsonResponse({'count': count})


# ==================== HISTORIQUE DES ACTIONS ====================

@login_required
def historique_actions(request):
    """
    Affiche l'historique des actions (pour admin seulement)
    """
    if request.user.role != 'admin':
        messages.error(request, "Accès non autorisé")
        return redirect('home')
    
    # Filtres
    type_action = request.GET.get('type_action', '')
    utilisateur_id = request.GET.get('utilisateur', '')
    
    actions = HistoriqueAction.objects.select_related('utilisateur').order_by('-date_action')
    
    if type_action:
        actions = actions.filter(type_action=type_action)
    
    if utilisateur_id:
        actions = actions.filter(utilisateur_id=utilisateur_id)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(actions, 20)  # 20 actions par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Données pour les filtres
    types_actions = HistoriqueAction.TYPE_ACTION_CHOICES
    utilisateurs = Utilisateur.objects.filter(role__in=['admin', 'gerant', 'serveur']).order_by('username')
    
    context = {
        'page_obj': page_obj,
        'types_actions': types_actions,
        'utilisateurs': utilisateurs,
        'type_action_filtre': type_action,
        'utilisateur_filtre': utilisateur_id,
    }
    
    return render(request, 'dashboards/admin/historique_actions.html', context)


# ==================== GESTION DES PRODUITS (GÉRANT) ====================

@login_required
def ajouter_produit(request):
    """
    Vue pour que le gérant puisse ajouter un nouveau produit
    """
    if request.user.role != 'gerant':
        messages.error(request, "Accès non autorisé")
        return redirect('home')
    
    if request.method == 'POST':
        form = ProduitForm(request.POST, request.FILES)
        if form.is_valid():
            produit = form.save(commit=False)
            # Associer le produit au gérant si nécessaire
            try:
                gerant = Gerant.objects.get(utilisateur=request.user)
                produit.gerant = gerant
            except Gerant.DoesNotExist:
                pass
            
            produit.save()
            
            # Enregistrer l'action
            enregistrer_action(
                request.user, 
                'produit_ajout', 
                f"Ajout du produit '{produit.nom}'",
                objet_concerne='Produit',
                objet_id=produit.id,
                details={'nom': produit.nom, 'prix': float(produit.prix)},
                request=request
            )
            
            messages.success(request, f"Le produit '{produit.nom}' a été ajouté avec succès.")
            return redirect('dashboard_gerant')
    else:
        form = ProduitForm()
    
    context = {
        'form': form,
        'titre': 'Ajouter un Produit'
    }
    return render(request, 'dashboards/gerant/ajouter_produit.html', context)


@login_required
def modifier_produit(request, produit_id):
    """
    Vue pour que le gérant puisse modifier un produit existant
    """
    if request.user.role != 'gerant':
        messages.error(request, "Accès non autorisé")
        return redirect('home')
    
    produit = get_object_or_404(Produit, id=produit_id)
    
    if request.method == 'POST':
        form = ProduitForm(request.POST, request.FILES, instance=produit)
        if form.is_valid():
            ancien_nom = produit.nom
            produit = form.save()
            
            # Enregistrer l'action
            enregistrer_action(
                request.user, 
                'produit_modif', 
                f"Modification du produit '{ancien_nom}' -> '{produit.nom}'",
                objet_concerne='Produit',
                objet_id=produit.id,
                details={'ancien_nom': ancien_nom, 'nouveau_nom': produit.nom, 'prix': float(produit.prix)},
                request=request
            )
            
            messages.success(request, f"Le produit '{produit.nom}' a été modifié avec succès.")
            return redirect('dashboard_gerant')
    else:
        form = ProduitForm(instance=produit)
    
    context = {
        'form': form,
        'produit': produit,
        'titre': f'Modifier {produit.nom}'
    }
    return render(request, 'dashboards/gerant/modifier_produit.html', context)


@login_required
def supprimer_produit(request, produit_id):
    """
    Vue pour que le gérant puisse supprimer un produit
    """
    if request.user.role != 'gerant':
        messages.error(request, "Accès non autorisé")
        return redirect('home')
    
    produit = get_object_or_404(Produit, id=produit_id)
    
    if request.method == 'POST':
        nom_produit = produit.nom
        
        # Enregistrer l'action avant la suppression
        enregistrer_action(
            request.user, 
            'produit_suppr', 
            f"Suppression du produit '{nom_produit}'",
            objet_concerne='Produit',
            objet_id=produit.id,
            details={'nom': nom_produit, 'prix': float(produit.prix)},
            request=request
        )
        
        produit.delete()
        messages.success(request, f"Le produit '{nom_produit}' a été supprimé avec succès.")
        return redirect('dashboard_gerant')
    
    context = {
        'produit': produit
    }
    return render(request, 'dashboards/gerant/confirmer_suppression.html', context)


@login_required
def rapport_serveur(request, serveur_id):
    """
    Génère un rapport d'activité individuel pour un serveur spécifique
    """
    if request.user.role != 'gerant':
        messages.error(request, "Accès non autorisé")
        return redirect('home')
    
    serveur = get_object_or_404(Utilisateur, id=serveur_id, role='serveur')
    
    # Période (par défaut: 30 derniers jours)
    periode = request.GET.get('periode', '30')
    try:
        jours = int(periode)
    except ValueError:
        jours = 30
    
    date_debut = timezone.now().date() - timedelta(days=jours)
    
    # Actions du serveur sur la période
    actions = HistoriqueAction.objects.filter(
        utilisateur=serveur,
        date_action__date__gte=date_debut
    ).order_by('-date_action')
    
    # Statistiques
    stats = {
        'total_actions': actions.count(),
        'commandes_traitees': actions.filter(type_action='commande_statut').count(),
        'actions_par_jour': actions.filter(
            date_action__date=timezone.now().date()
        ).count(),
        'actions_par_type': {},
    }
    
    # Répartition par type d'action
    for action in actions:
        type_action = action.get_type_action_display()
        if type_action in stats['actions_par_type']:
            stats['actions_par_type'][type_action] += 1
        else:
            stats['actions_par_type'][type_action] = 1
    
    context = {
        'serveur': serveur,
        'actions': actions[:50],  # Limiter à 50 actions récentes
        'stats': stats,
        'periode': jours,
        'date_debut': date_debut,
    }
    
    return render(request, 'dashboards/gerant/rapport_serveur.html', context)
