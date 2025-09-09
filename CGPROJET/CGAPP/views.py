from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View,DeleteView,DetailView
from django.contrib.auth.mixins import LoginRequiredMixin,UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy
from .models import *
from .forms import *
from django.contrib.auth import login, authenticate, logout,get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.utils import timezone
from django.db import models,transaction
from datetime import timedelta
from django.contrib.auth.views import PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
User = get_user_model()
from django.db.models import Q,Sum,Avg,Count
from decimal import Decimal
from django.core.mail import send_mail
from django.conf import settings
import logging
logger = logging.getLogger(__name__)
import random
import time
import json
from django.core.paginator import Paginator

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

class InscriptionView(CreateView):
    model = Utilisateur
    form_class = InscriptionForm
    template_name = 'frontOfice/compte/inscription.html'

    def get_success_url(self):
        next_url = self.request.POST.get('next') or self.request.GET.get('next')
        return next_url if next_url else reverse_lazy('home')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)  
        messages.success(self.request, "Inscription réussie !")
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['next'] = self.request.GET.get('next', '')
        return context


def connexion(request):
    next_url = request.GET.get('next', 'home')

    if request.method == 'POST':
        form = ConnexionForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)

                # Fusionner panier session avec panier utilisateur
                panier_session = request.session.get('panier', {})
                if panier_session:
                    panier_user, created = Panier.objects.get_or_create(utilisateur=user)
                    for produit_id, quantite in panier_session.items():
                        produit = Produit.objects.get(id=produit_id)
                        ligne, created = LignePanier.objects.get_or_create(
                            panier=panier_user, produit=produit
                        )
                        if not created:
                            ligne.quantite += quantite
                            ligne.save()
                    del request.session['panier']

                messages.success(request, f"Bienvenue {user.username} !")
                return redirect(next_url)
            else:
                messages.error(request, "Identifiants incorrects")
    else:
        form = ConnexionForm()

    return render(request, 'frontOfice/compte/connexion.html', {'form': form, 'next': next_url})


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
    # Produits nouveaux (8 derniers produits)
    produits_nouveautes = Produit.objects.filter(
        quantite_disponible__gt=0
    ).order_by('-date_creation')[:8]
    
    # Produits populaires (marqués comme tels + en stock)
    produits_populaires = Produit.objects.filter(
        est_populaire=True,
        quantite_disponible__gt=0
    ).order_by('?')[:4]  # Mélange pour varier l'affichage
    
    # Catégories avec des produits disponibles
    categories = Categorie.objects.filter(
        produits__quantite_disponible__gt=0
    ).distinct().order_by('ordre_affichage')[:6]
    
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

@login_required
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



class CheckoutView(LoginRequiredMixin, View):
    template_name = 'frontOffice/panier/checkout.html'
    form_class = CommandeForm
    login_url = reverse_lazy('connexion')  

    def get(self, request):
        panier = Panier.objects.filter(client__utilisateur=request.user).first()
        
        if not panier or not panier.produits.exists():
            messages.error(request, "Votre panier est vide")
            return redirect('panier')

        initial_data = {
            'mode_livraison': 'emporter',
            'mode_paiement': 'espece',
        }
        
        form = self.form_class(initial=initial_data)
        return render(request, self.template_name, {
            'form': form,
            'panier': panier,
            'total': panier.get_total()
        })

    def post(self, request):
        form = self.form_class(request.POST)
        panier = Panier.objects.filter(client__utilisateur=request.user).first()

        if not panier or not panier.produits.exists():
            messages.error(request, "Votre panier est vide")
            return redirect('panier')

        if form.is_valid():
            commande = form.save(commit=False)
            commande.client = panier.client
            commande.panier = panier
            commande.montant_total = panier.get_total()
            commande.save()
            
            # Vider le panier après commande
            panier.produits.clear()
            
            messages.success(request, "Votre commande a été passée avec succès!")
            return redirect('commande_confirmation', commande_id=commande.id)

        return render(request, self.template_name, {
            'form': form,
            'panier': panier,
            'total': panier.get_total()
        })
# Contact

def contact_success(request):
    return render(request, 'frontOfice/contactSuccess.html')

def contact_view(request):
    faq_questions = [
    {
        'id': 'question1',
        'question': "Comment passer une commande ?",
        'reponse': "Sélectionnez vos glaces préférées, ajoutez-les au panier, puis validez votre commande en suivant les étapes de paiement."
    },
    {
        'id': 'question2',
        'question': "Quels modes de paiement acceptez-vous ?",
        'reponse': "Nous acceptons les paiements en espèces à la livraison, ainsi que par TMoney et Flooz."
    },
    {
        'id': 'question3',
        'question': "Proposez-vous un service de livraison ?",
        'reponse': "Oui, nous livrons à domicile selon les zones couvertes. Les frais et délais de livraison sont indiqués lors de la commande."
    },
    {
        'id': 'question4',
        'question': "Puis-je commander en grande quantité pour un événement ?",
        'reponse': "Oui, il est possible de passer une commande spéciale pour vos fêtes, mariages ou événements. Contactez-nous via la page de contact."
    },
    {
        'id': 'question5',
        'question': "Vos produits sont-ils faits maison ?",
        'reponse': "Oui, toutes nos glaces sont préparées avec soin à partir d’ingrédients de qualité et selon nos recettes artisanales."
    },
    {
        'id': 'question6',
        'question': "Comment savoir si ma commande est confirmée ?",
        'reponse': "Vous recevrez une confirmation par notification et par email une fois votre commande validée."
    },
    {
        'id': 'question7',
        'question': "Quels parfums de glaces proposez-vous ?",
        'reponse': "Nous proposons plusieurs parfums : vanille, chocolat, fraise, mangue, citron, et bien d’autres selon la saison."
    },
    {
        'id': 'question8',
        'question': "Puis-je annuler ma commande après validation ?",
        'reponse': "Oui, vous pouvez annuler votre commande avant qu’elle ne soit expédiée en contactant notre service client."
    },
]


    if request.method == 'POST':
        # Récupération des données
        nom = request.POST.get('nom')
        prenom = request.POST.get('prenom')
        email = request.POST.get('email')
        telephone = request.POST.get('telephone')
        sujet = request.POST.get('sujet')
        message = request.POST.get('message')

        # Validation
        if not nom or not email or not sujet or not message:
            messages.error(request, "Veuillez remplir tous les champs obligatoires.")
            return render(request, 'frontOfice/contact.html', {
                'submitted_data': request.POST,
                'faq_questions': faq_questions
            })

        try:
            # Enregistrement en base
            contact = ContactMessage.objects.create(
                nom=nom,
                prenom=prenom if prenom else None,
                email=email,
                telephone=telephone if telephone else None,
                sujet=sujet,
                message=message
            )

            # Envoi d'email
            sujet_email = f"[Canaan glacier Contact] {contact.get_sujet_display()}"
            message_email = f"""
            Nouveau message de contact:
            
            Nom: {contact.nom}
            Prénom: {contact.prenom if contact.prenom else 'Non fourni'}
            Email: {contact.email}
            Téléphone: {contact.telephone if contact.telephone else 'Non fourni'}
            Sujet: {contact.get_sujet_display()}
            
            Message:
            {contact.message}
            
            Date: {contact.date_soumission.strftime('%d/%m/%Y %H:%M')}
            """

            send_mail(
                sujet_email,
                message_email,
                settings.DEFAULT_FROM_EMAIL,
                ['allodekanybenjamin@gmail.com'],  
                fail_silently=False,
            )

            messages.success(request, "Votre message a bien été envoyé ! Nous vous contacterons bientôt.")
            return redirect('contact_success')

        except Exception as e:
            messages.error(request, f"Une erreur est survenue : {str(e)}")
            return render(request, 'frontOfice/contact.html', {
                'submitted_data': request.POST,
                'faq_questions': faq_questions
            })

    return render(request, 'frontOfice/contact.html', {
        'faq_questions': faq_questions
    })


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
    form_class = ProfilForm
    success_url = reverse_lazy('profile')  # ou 'profil' selon ton urls.py

    def get_object(self):
        return self.request.user

class CustomPasswordChangeView(SuccessMessageMixin, PasswordChangeView):
    template_name = 'frontOfice/compte/'
    success_url = reverse_lazy('profile')  
    success_message = "Votre mot de passe a été modifié avec succès."

class DeleteAccountView(LoginRequiredMixin, DeleteView):
    model = User
    template_name = 'frontOfice/compte/supprimer_compte.html'
    success_url = reverse_lazy('connexion')

    def get_object(self, queryset=None):
        return self.request.user

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
    messages_contact = ContactMessage.objects.order_by('-date_soumission')[:5]
    
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
def changer_statut(request, commande_id):
    if request.user.role != 'serveur':
        messages.error(request, "Accès non autorisé")
        return redirect('home')
    
    if request.method == 'POST':
        commande = get_object_or_404(Commande, id=commande_id)
        ancien_statut = commande.statut
        nouveau_statut = request.POST.get('statut')
        
        if nouveau_statut in ['en_attente', 'en_traitement', 'livree', 'annulee']:
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
            
            if nouveau_statut == 'en_traitement':
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

class ListeProduitsView(ListView):
    model = Produit
    template_name = 'dashboards/gerant/liste_produit.html'
    context_object_name = 'produits'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(gerant=self.request.user.gerant)
        
        # Filtrage par catégorie
        categorie_id = self.request.GET.get('categorie')
        if categorie_id:
            queryset = queryset.filter(categorie__id=categorie_id)
            
        # Filtrage par statut de stock
        stock_status = self.request.GET.get('stock_status')
        if stock_status == 'disponible':
            queryset = queryset.filter(quantite_disponible__gt=0)
        elif stock_status == 'epuise':
            queryset = queryset.filter(quantite_disponible=0)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Categorie.objects.all()
        return context

class AjouterProduitView(CreateView):
    model = Produit
    form_class = ProduitForm
    template_name = 'dashboards/gerant/ajouter_produit.html'
    success_url = reverse_lazy('liste_produits')
    
    def form_valid(self, form):
        form.instance.gerant = self.request.user.gerant
        messages.success(self.request, "Le produit a été ajouté avec succès.")
        return super().form_valid(form)

class ModifierProduitView(UpdateView):
    model = Produit
    form_class = ProduitForm
    template_name = 'dashboards/gerant/modifier_produit.html'
    success_url = reverse_lazy('liste_produits')
    
    def form_valid(self, form):
        messages.success(self.request, "Le produit a été modifié avec succès.")
        return super().form_valid(form)

class SupprimerProduitView(DeleteView):
    model = Produit
    template_name = 'dashboards/gerant/supprimer_produit.html'
    success_url = reverse_lazy('liste_produits')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, "Le produit a été supprimé avec succès.")
        return super().delete(request, *args, **kwargs)

class DetailProduitView(DetailView):
    model = Produit
    template_name = 'dashboards/gerant/detail_produit.html'
    context_object_name = 'produit'

def recherche_produits(request):
    query = request.GET.get('q', '')
    
    produits = Produit.objects.filter(
        Q(nom__icontains=query) | 
        Q(description__icontains=query),
        gerant=request.user.gerant
    ).order_by('nom')
    
    return render(request, 'dashboards/gerant/recherche_produits.html', {
        'produits': produits,
        'query': query
    })

class ProduitAPIView(ListView):
    model = Produit
    http_method_names = ['get']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(gerant=self.request.user.gerant)
        return queryset
    
    def render_to_response(self, context, **response_kwargs):
        produits = list(context['object_list'].values(
            'id', 'nom', 'prix', 'quantite_disponible', 'image'
        ))
        return JsonResponse({'produits': produits})
    

# ==================== GESTION DES SERVEURS (GÉRANT) ====================


class ListeServeursView(ListView):
    model = Utilisateur
    template_name = 'dashboards/gerant/liste_serveurs.html'
    context_object_name = 'serveurs'
    
    def get_queryset(self):
        # Utilisation du bon related_name 'actions'
        return Utilisateur.objects.filter(
            role='serveur'
        ).annotate(
            total_actions=Count('actions')
        ).order_by('-total_actions')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Ajoute les statistiques globales
        context['total_serveurs'] = self.get_queryset().count()
        context['actions_7j'] = HistoriqueAction.objects.filter(
            date_action__gte=timezone.now() - timedelta(days=7),
            utilisateur__role='serveur'
        ).count()
        
        # Statistiques supplémentaires
        context['total_actions'] = HistoriqueAction.objects.count()
        context['total_commandes'] = HistoriqueAction.objects.filter(
            type_action='commande_statut'
        ).count()
        context['actions_auj'] = HistoriqueAction.objects.filter(
            date_action__date=timezone.now().date()
        ).count()
        context['serveurs_actifs'] = Utilisateur.objects.filter(
            role='serveur',
            actions__isnull=False
        ).distinct().count()
        
        return context

@login_required
def rapport_serveur(request, pk):
    """
    Génère un rapport d'activité individuel pour un serveur spécifique
    """
    if request.user.role != 'gerant':
        messages.error(request, "Accès non autorisé")
        return redirect('home')
    
    serveur = get_object_or_404(Utilisateur, id=pk, role='serveur')
    
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
        stats['actions_par_type'][type_action] = stats['actions_par_type'].get(type_action, 0) + 1
    
    context = {
        'serveur': serveur,
        'actions': actions[:50],  # Limiter à 50 actions récentes
        'stats': stats,
        'periode': jours,
        'date_debut': date_debut,
    }
    
    return render(request, 'dashboards/gerant/rapport_serveur.html', context)

#===============================Client============================
@login_required
@transaction.atomic
def finaliser_commande(request):
    utilisateur = request.user if request.user.is_authenticated else None
    panier = Panier.objects.filter(utilisateur=utilisateur).first() if utilisateur else Panier.objects.filter(session_id=request.session.session_key).first()

    if not panier or not panier.lignes.exists():
        messages.error(request, "Votre panier est vide.")
        return redirect("produits")

    if request.method == "POST":
        methode_paiement = request.POST.get("methode_paiement")
        retrait_magasin = request.POST.get("retrait_magasin") == "on"

        adresse = None
        if not retrait_magasin:
            # Ne créer que si tous les champs existent
            adresse = AdresseLivraison.objects.create(
                utilisateur=utilisateur,
                rue=request.POST.get("rue"),
                ville=request.POST.get("ville"),
                code_postal=request.POST.get("code_postal"),
                pays=request.POST.get("pays"),
            )

        # Coupon
        coupon, total = None, panier.total
        coupon_code = request.POST.get("coupon")
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code, actif=True)
                if coupon.date_expiration < timezone.now().date():
                    messages.warning(request, "Le coupon est expiré.")
                    coupon = None
            except Coupon.DoesNotExist:
                messages.warning(request, "Coupon invalide.")
        if coupon:
            total -= total * (coupon.reduction / Decimal('100'))

        # Commande
        commande = Commande.objects.create(
            utilisateur=utilisateur,
            total=total,
            methode_paiement=methode_paiement,
            statut="en_attente",
            coupon=coupon
        )
        if adresse:
            commande.adresse_livraison = adresse
            commande.save()

        for ligne in panier.lignes.all():
            LigneCommande.objects.create(
                commande=commande,
                produit=ligne.produit,
                quantite=ligne.quantite,
                prix_unitaire=ligne.produit.prix
            )
            ligne.produit.quantite_disponible -= ligne.quantite
            ligne.produit.save()

        paiement_statut = "en attente"
        if methode_paiement in ["carte_bancaire", "flooz", "tmoney"]:
            paiement_statut = "en cours"

        Paiement.objects.create(commande=commande, montant=total, statut=paiement_statut)

        panier.lignes.all().delete()
        panier.delete()

        messages.success(request, f"Votre commande #{commande.id} a été créée avec succès !")
        return redirect("commande_detail", commande.id)

    return render(request, "frontOfice/commandes/finalisation.html", {"panier": panier})


def commande_detail(request, pk):
    commande = get_object_or_404(Commande, pk=pk, utilisateur=request.user)
    return render(request, "frontOfice/commandes/detail.html", {"commande": commande})

@login_required
def processus_paiement(request, commande_id):
    """Vue pour gérer le processus de paiement selon la méthode choisie"""
    commande = get_object_or_404(Commande, id=commande_id, utilisateur=request.user)
    
    # Vérifier si la commande est déjà payée
    if hasattr(commande, 'paiement') and commande.paiement.statut == 'payé':
        messages.info(request, "Cette commande a déjà été payée.")
        return redirect('commande_detail', pk=commande_id)
    
    # Déterminer le template en fonction de la méthode de paiement
    templates = {
        'carte_bancaire': 'frontOfice/paiement/carte_bancaire.html',
        'flooz': 'frontOfice/paiement/mobile_money.html',
        'tmoney': 'frontOfice/paiement/mobile_money.html',
        'paiement_livraison': 'frontOfice/paiement/paiement_livraison.html',
        'retrait_magasin': 'frontOfice/paiement/retrait_magasin.html',
    }
    
    template = templates.get(commande.methode_paiement, 'frontOfice/paiement/default.html')
    
    context = {
        'commande': commande,
        'methode_paiement': commande.methode_paiement,
    }
    
    return render(request, template, context)

@login_required
def traiter_paiement(request, commande_id):
    """Vue pour traiter le paiement (simulation)"""
    if request.method == 'POST':
        commande = get_object_or_404(Commande, id=commande_id, utilisateur=request.user)
        methode = commande.methode_paiement
        
        # Simulation de traitement selon la méthode
        if methode in ['carte_bancaire', 'flooz', 'tmoney']:
            # Simuler un délai de traitement
            time.sleep(2)
            
            # Générer un numéro de transaction aléatoire
            numero_transaction = ''.join([str(random.randint(0, 9)) for _ in range(12)])
            
            # Mettre à jour le statut du paiement
            paiement, created = Paiement.objects.get_or_create(commande=commande)
            paiement.montant = commande.total
            paiement.statut = 'payé'
            paiement.save()
            
            # Mettre à jour le statut de la commande
            commande.statut = 'payée'
            commande.save()
            
            messages.success(request, f"Paiement effectué avec succès! Numéro de transaction: {numero_transaction}")
            return redirect('commande_detail', pk=commande_id)
        
        elif methode == 'paiement_livraison':
            messages.info(request, "Vous paierez à la livraison de votre commande.")
            return redirect('commande_detail', pk=commande_id)
        
        elif methode == 'retrait_magasin':
            messages.info(request, "Vous paierez lors du retrait en magasin.")
            return redirect('commande_detail', pk=commande_id)
    
    return redirect('commande_detail', pk=commande_id)

@login_required
def annuler_paiement(request, commande_id):
    """Vue pour annuler un paiement"""
    commande = get_object_or_404(Commande, id=commande_id, utilisateur=request.user)
    
    # Réactiver le stock des produits (si nécessaire)
    for ligne in commande.lignes.all():
        ligne.produit.quantite_disponible += ligne.quantite
        ligne.produit.save()
    
    # Marquer la commande comme annulée
    commande.statut = 'annulee'
    commande.save()
    
    messages.info(request, "Paiement annulé. Votre commande a été annulée.")
    return redirect('commande_detail', pk=commande_id)


#Gestion serveur

def is_serveur(user):
    return user.is_authenticated and (user.is_staff or user.groups.filter(name='Serveurs').exists())

def nouvelle_commande_serveur(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            nom_complet = form.cleaned_data['nom_complet']
            telephone = form.cleaned_data['telephone']
            email = form.cleaned_data.get('email', f"{telephone}@client.com")
            
            client, created = Utilisateur.objects.get_or_create(
                telephone=telephone,
                defaults={
                    'username': telephone,
                    'email': email,
                    'first_name': nom_complet.split(' ')[0] if ' ' in nom_complet else nom_complet,
                    'last_name': ' '.join(nom_complet.split(' ')[1:]) if ' ' in nom_complet else '',
                }
            )
            
            panier, created = Panier.objects.get_or_create(
                utilisateur=client,
                defaults={'session_id': f"serveur_{timezone.now().timestamp()}"}
            )
            
            request.session['panier_serveur_id'] = panier.id
            request.session['client_id'] = client.id
            
            messages.success(request, f"Commande créée pour {nom_complet}")
            return redirect('ajouter_produit_commande', commande_id=panier.id)
    else:
        form = ClientForm()
    
    return render(request, 'dashboards/serveur/nouvelle_commande.html', {'form': form, 'title': 'Nouvelle Commande - Client'})

def ajouter_produit_commande(request, commande_id):
    panier = get_object_or_404(Panier, id=commande_id)
    client = panier.utilisateur
    
    # Préparer les données pour le template
    lignes_avec_max = []
    for ligne in panier.lignes.all():
        quantite_max = ligne.produit.quantite_disponible + ligne.quantite
        lignes_avec_max.append({
            'ligne': ligne,
            'quantite_max': quantite_max
        })
    
    if request.method == 'POST':
        form = ProduitPanierForm(request.POST)
        if form.is_valid():
            produit = form.cleaned_data['produit']
            quantite = form.cleaned_data['quantite']
            
            if produit.quantite_disponible < quantite:
                messages.error(request, f"Stock insuffisant pour {produit.nom}. Disponible: {produit.quantite_disponible}")
                return redirect('ajouter_produit_commande', commande_id=panier.id)
            
            ligne_existante = panier.lignes.filter(produit=produit).first()
            
            if ligne_existante:
                nouvelle_quantite = ligne_existante.quantite + quantite
                if nouvelle_quantite > produit.quantite_disponible + ligne_existante.quantite:
                    messages.error(request, f"Stock insuffisant pour {produit.nom}. Disponible: {produit.quantite_disponible}")
                    return redirect('ajouter_produit_commande', commande_id=panier.id)
                ligne_existante.quantite = nouvelle_quantite
                ligne_existante.save()
                messages.success(request, f"Quantité mise à jour pour {produit.nom}")
            else:
                panier.lignes.create(produit=produit, quantite=quantite)
                messages.success(request, f"{produit.nom} ajouté au panier")
            
            return redirect('ajouter_produit_commande', commande_id=panier.id)
    else:
        form = ProduitPanierForm()
    
    produits_disponibles = Produit.objects.filter(quantite_disponible__gt=0).order_by('-est_populaire', 'nom')[:10]
    
    return render(request, 'dashboards/serveur/ajouter_produits.html', {
        'form': form,
        'panier': panier,
        'client': client,
        'produits_disponibles': produits_disponibles,
        'lignes_avec_max': lignes_avec_max,  # Nouvelle donnée
        'title': f'Ajouter Produits - {client.get_full_name()}'
    })
def modifier_quantite(request, commande_id, ligne_id):
    panier = get_object_or_404(Panier, id=commande_id)
    ligne = get_object_or_404(LignePanier, id=ligne_id, panier=panier)
    
    if request.method == 'POST':
        nouvelle_quantite = int(request.POST.get('quantite', 1))
        
        if nouvelle_quantite > ligne.produit.quantite_disponible + ligne.quantite:
            messages.error(request, f"Stock insuffisant. Disponible: {ligne.produit.quantite_disponible}")
            return redirect('ajouter_produit_commande', commande_id=panier.id)
        
        if nouvelle_quantite > 0:
            ligne.quantite = nouvelle_quantite
            ligne.save()
            messages.success(request, f"Quantité de {ligne.produit.nom} mise à jour")
        else:
            ligne.delete()
            messages.success(request, f"{ligne.produit.nom} retiré du panier")
    
    return redirect('ajouter_produit_commande', commande_id=panier.id)


def supprimer_produit(request, commande_id, ligne_id):
    panier = get_object_or_404(Panier, id=commande_id)
    ligne = get_object_or_404(LignePanier, id=ligne_id, panier=panier)
    
    produit_nom = ligne.produit.nom
    ligne.delete()
    messages.success(request, f"{produit_nom} retiré du panier")
    
    return redirect('ajouter_produit_commande', commande_id=panier.id)


@transaction.atomic
def finaliser_commande_serveur(request, commande_id):
    panier = get_object_or_404(Panier, id=commande_id)
    client = panier.utilisateur
    
    if not panier.lignes.exists():
        messages.error(request, "Le panier est vide.")
        return redirect('ajouter_produit_commande', commande_id=panier.id)
    
    for ligne in panier.lignes.all():
        if ligne.quantite > ligne.produit.quantite_disponible:
            messages.error(request, f"Stock insuffisant pour {ligne.produit.nom}. Disponible: {ligne.produit.quantite_disponible}")
            return redirect('ajouter_produit_commande', commande_id=panier.id)
    
    try:
        commande = Commande.objects.create(
            utilisateur=client,
            total=panier.total,
            methode_paiement='a_definir',
            statut="en_attente",
        )
        
        for ligne_panier in panier.lignes.all():
            LigneCommande.objects.create(
                commande=commande,
                produit=ligne_panier.produit,
                quantite=ligne_panier.quantite,
                prix_unitaire=ligne_panier.produit.prix
            )
            
            ligne_panier.produit.quantite_disponible -= ligne_panier.quantite
            ligne_panier.produit.save()
        
        panier.lignes.all().delete()
        
        if 'panier_serveur_id' in request.session:
            del request.session['panier_serveur_id']
        
        messages.success(request, f"Commande #{commande.id} créée avec succès")
        return redirect('paiement_commande_serveur', commande_id=commande.id)
        
    except Exception as e:
        messages.error(request, f"Erreur: {str(e)}")
        return redirect('ajouter_produit_commande', commande_id=panier.id)


def paiement_commande_serveur(request, commande_id):
    commande = get_object_or_404(Commande, id=commande_id)
    
    if request.method == 'POST':
        form = PaiementServeurForm(request.POST)
        if form.is_valid():
            methode_paiement = form.cleaned_data['methode_paiement']
            montant_paye = form.cleaned_data['montant_paye']
            
            commande.methode_paiement = methode_paiement
            commande.statut = "en_cours"
            commande.save()
            
            Paiement.objects.create(
                commande=commande,
                montant=montant_paye,
                statut="payé",
                reference=f"BOUTIQUE_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
            )
            
            messages.success(request, f"Paiement de {montant_paye} FCFA enregistré")
            return redirect('generer_recu_serveur', commande_id=commande.id)
    else:
        form = PaiementServeurForm(initial={'montant_paye': commande.total})
    
    return render(request, 'dashboards/serveur/paiement.html', {
        'form': form,
        'commande': commande,
        'client': commande.utilisateur,
        'title': f'Paiement - Commande #{commande.id}'
    })


def generer_recu(request, commande_id):
    commande = get_object_or_404(Commande, id=commande_id)
    paiement = get_object_or_404(Paiement, commande=commande)
    
    return render(request, 'dashboards/serveur/recu.html', {
        'commande': commande,
        'paiement': paiement,
        'client': commande.utilisateur,
        'title': f'Reçu - Commande #{commande.id}'
    })



def commandes_en_attente(request):
    """Afficher les commandes en attente de traitement"""
    commandes_en_attente = Commande.objects.filter(statut='en_attente').order_by('date_creation')
    commandes_en_cours = Commande.objects.filter(statut='en_traitement').order_by('date_creation')
    
    # Définir les choix de statut pour le template
    statut_choices = {
        'en_attente': 'En attente',
        'en_traitement': 'En traitement',
        'expediee': 'Expédiée', 
        'livree': 'Livrée',
        'annulee': 'Annulée'
    }
    
    return render(request, 'dashboards/serveur/commande_liste.html', {
        'commandes_en_attente': commandes_en_attente,
        'commandes_en_cours': commandes_en_cours,
        'statut_choices': statut_choices,
        'title': 'Commandes en Attente'
    })

def prendre_en_charge_commande(request, commande_id):
    commande = get_object_or_404(Commande, id=commande_id)
    
    if commande.statut != Commande.STATUT_EN_ATTENTE:
        messages.warning(request, f"La commande #{commande.id} n'est plus en attente.")
        return redirect('commandes_en_attente')
    
    commande.statut = Commande.STATUT_TRAITEMENT
    commande.save()
    
    messages.success(request, f"Commande #{commande.id} prise en charge!")
    return redirect('commandes_en_attente')


def changer_statut_commande(request, commande_id):
    """Changer le statut d'une commande"""
    commande = get_object_or_404(Commande, id=commande_id)
    
    if request.method == 'POST':
        nouveau_statut = request.POST.get('statut')
        
        # Définir les statuts valides directement dans la vue
        statuts_valides = {
            'en_attente': 'En attente',
            'en_traitement': 'En traitement', 
            'expediee': 'Expédiée',
            'livree': 'Livrée',
            'annulee': 'Annulée'
        }
        
        if nouveau_statut in statuts_valides:
            commande.statut = nouveau_statut
            commande.save()
            messages.success(request, f"Statut de la commande #{commande.id} changé en {statuts_valides[nouveau_statut]}")
        else:
            messages.error(request, "Statut invalide")
    
    return redirect('commandes_en_attente')


def annuler_commande_serveur(request, commande_id):
    commande = get_object_or_404(Commande, id=commande_id)
    
    if commande.statut not in [Commande.STATUT_EN_ATTENTE, Commande.STATUT_TRAITEMENT]:
        messages.error(request, "Seules les commandes en attente ou en traitement peuvent être annulées")
        return redirect('commandes_en_attente')
    
    try:
        for ligne in commande.lignes.all():
            ligne.produit.quantite_disponible += ligne.quantite
            ligne.produit.save()
        
        commande.statut = Commande.STATUT_ANNULEE
        commande.save()
        
        messages.success(request, f"Commande #{commande.id} annulée et produits restockés")
    
    except Exception as e:
        messages.error(request, f"Erreur lors de l'annulation: {str(e)}")
    
    return redirect('commandes_en_attente')




@login_required
def detail_commande(request, commande_id):
    """Afficher le détail d'une commande spécifique"""
    commande = get_object_or_404(Commande, id=commande_id)
    return render(request, 'dashboards/serveur/commande_detail.html', {'commande': commande})

@login_required
def commandes_en_cours(request):
    """Afficher les commandes en cours de traitement"""
    commandes = Commande.objects.filter(
        statut__in=[Commande.STATUT_EN_ATTENTE, Commande.STATUT_TRAITEMENT]
    ).order_by('date_creation')
    
    return render(request, 'dashboards/serveur/commandes_en_cours.html', {
        'commandes': commandes,
        'title': 'Commandes en Cours'
    })

class ListeProduitsServeurView(ListView):
    model = Produit
    template_name = 'dashboards/serveur/liste_produits.html'
    context_object_name = 'produits'
    paginate_by = 12  # 12 produits par page
    
    def get_queryset(self):
        # Récupérer tous les produits avec leurs catégories
        return Produit.objects.select_related('categorie').all()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Ajouter des statistiques ou autres données au contexte si nécessaire
        context['total_produits'] = Produit.objects.count()
        return context

class CommandesLivreesServeurView(LoginRequiredMixin, ListView):
    model = Commande
    template_name = 'dashboards/serveur/commandes_livrees_serveur.html'
    context_object_name = 'commandes'
    paginate_by = 15
    
    def get_queryset(self):
        # Filtrer les commandes livrées (sans restriction de groupe)
        queryset = Commande.objects.filter(
            statut=Commande.STATUT_LIVREE
        ).select_related(
            'utilisateur', 
            'adresse_livraison', 
            'coupon'
        ).prefetch_related(
            'lignes__produit'
        ).order_by('-date_creation')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistiques
        context['total_commandes'] = self.get_queryset().count()
        
        # Chiffre d'affaires des commandes livrées
        chiffre_affaires = self.get_queryset().aggregate(
            total=Sum('total')
        )['total'] or 0
        
        context['chiffre_affaires'] = chiffre_affaires
        context['serveur_connecte'] = self.request.user
        return context
    
    # Méthode pour vérifier l'accès (plus permissive)
    def dispatch(self, request, *args, **kwargs):
        # Vérifier simplement que l'utilisateur est connecté
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
    
#==================================Gestion client=======================================


def detail_produit_client(request, produit_id):
    """Afficher le détail d'un produit pour le client"""
    produit = get_object_or_404(
        Produit.objects.select_related('categorie', 'gerant'),
        id=produit_id,
        quantite_disponible__gt=0  # Seulement les produits en stock
    )
    
    # Produits similaires (même catégorie ou produits populaires)
    produits_similaires = Produit.objects.filter(
        Q(categorie=produit.categorie) | Q(est_populaire=True),
        quantite_disponible__gt=0
    ).exclude(id=produit.id).select_related('categorie')[:4]
    
    context = {
        'produit': produit,
        'produits_similaires': produits_similaires,
    }
    
    return render(request, 'dashboards/client/detail_produit.html', context)


@login_required
def historique_client(request):
    """Afficher l'historique des activités du client connecté"""
    user = request.user
    
    # Commandes du client
    commandes = Commande.objects.filter(
        utilisateur=user
    ).select_related(
        'adresse_livraison', 
        'coupon'
    ).prefetch_related(
        'lignes__produit'
    ).order_by('-date_creation')
    
    # Statistiques des commandes
    total_commandes = commandes.count()
    total_depense = commandes.aggregate(total=Sum('total'))['total'] or 0
    commandes_livrees = commandes.filter(statut=Commande.STATUT_LIVREE).count()
    
    # Panier actuel - Vérification correcte
    panier_actuel = Panier.objects.filter(
        utilisateur=user
    ).prefetch_related('lignes').order_by('-date_creation').first()
    
    # Vérifier si le panier a des articles
    if panier_actuel and panier_actuel.lignes.count() == 0:
        panier_actuel = None
    
    # Historique des actions du client
    historique_actions = HistoriqueAction.objects.filter(
        utilisateur=user
    ).order_by('-date_action')[:10]
    
    # Notifications du client
    notifications = Notification.objects.filter(
        utilisateur=user
    ).order_by('-date_creation')[:5]
    
    # Calcul des statistiques mensuelles (exemple simplifié)
    commandes_mois = commandes.filter(
        date_creation__month=timezone.now().month,
        date_creation__year=timezone.now().year
    )
    depense_mensuelle = commandes_mois.aggregate(total=Sum('total'))['total'] or 0
    
    context = {
        'commandes': commandes,
        'total_commandes': total_commandes,
        'total_depense': total_depense,
        'commandes_livrees': commandes_livrees,
        'panier_actuel': panier_actuel,
        'historique_actions': historique_actions,
        'notifications': notifications,
        'commandes_mois_count': commandes_mois.count(),
        'depense_mensuelle': depense_mensuelle,
        'user': user,
    }
    
    return render(request, 'dashboards/client/historique.html', context)

#--------------------------------Avis clients-----------------------------------


@login_required
def tableau_de_bord_avis(request):
    """Tableau de bord principal pour les avis et préférences"""
    user = request.user
    
    # Préférences alimentaires de l'utilisateur
    preferences = PreferenceAlimentaire.objects.filter(
        utilisateur=user, 
        est_actif=True
    ).order_by('-date_creation')
    
    # Avis de l'utilisateur
    avis_utilisateur = AvisProduit.objects.filter(
        utilisateur=user
    ).select_related('produit').order_by('-date_creation')
    
    # Commandes éligibles pour avis (livrées et sans avis)
    commandes_sans_avis = Commande.objects.filter(
        utilisateur=user,
        statut=Commande.STATUT_LIVREE
    ).prefetch_related('lignes__produit').exclude(
        Q(avis__isnull=False) | Q(lignes__produit__avis__utilisateur=user)
    ).distinct()
    
    context = {
        'preferences': preferences,
        'avis_utilisateur': avis_utilisateur,
        'commandes_sans_avis': commandes_sans_avis,
        'total_avis': avis_utilisateur.count(),
        'moyenne_notes': avis_utilisateur.aggregate(avg=Avg('note'))['avg'] or 0,
    }
    
    return render(request, 'dashboards/client/tableau_avis.html', context)

@login_required
def gerer_preferences(request):
    """Gérer les préférences et allergies alimentaires"""
    user = request.user
    
    if request.method == 'POST':
        form = PreferenceAlimentaireForm(request.POST)
        if form.is_valid():
            preference = form.save(commit=False)
            preference.utilisateur = user
            preference.save()
            messages.success(request, 'Votre préférence a été enregistrée avec succès.')
            return redirect('gerer_preferences')
    else:
        form = PreferenceAlimentaireForm()
    
    preferences = PreferenceAlimentaire.objects.filter(utilisateur=user).order_by('-date_creation')
    
    context = {
        'form': form,
        'preferences': preferences,
    }
    
    return render(request, 'dashboards/client/gerer_preferences.html', context)

@login_required
def modifier_preference(request, preference_id):
    """Modifier une préférence existante"""
    preference = get_object_or_404(PreferenceAlimentaire, id=preference_id, utilisateur=request.user)
    
    if request.method == 'POST':
        form = PreferenceAlimentaireForm(request.POST, instance=preference)
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre préférence a été modifiée avec succès.')
            return redirect('gerer_preferences')
    else:
        form = PreferenceAlimentaireForm(instance=preference)
    
    context = {
        'form': form,
        'preference': preference,
    }
    
    return render(request, 'dashboards/client/modifier_preference.html', context)

@login_required
def supprimer_preference(request, preference_id):
    """Supprimer une préférence"""
    preference = get_object_or_404(PreferenceAlimentaire, id=preference_id, utilisateur=request.user)
    
    if request.method == 'POST':
        preference.delete()
        messages.success(request, 'Votre préférence a été supprimée avec succès.')
        return redirect('gerer_preferences')
    
    context = {
        'preference': preference,
    }
    
    return render(request, 'dashboards/client/supprimer_preference.html', context)
from django import forms
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator

# Widget personnalisé pour gérer plusieurs fichiers
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

@login_required
def laisser_avis(request, commande_id=None, produit_id=None):
    """Laisser un avis sur un produit"""
    user = request.user
    
    if commande_id:
        commande = get_object_or_404(Commande, id=commande_id, utilisateur=user)
        produits = commande.lignes.values_list('produit', flat=True)
    else:
        commande = None
        produits = None
    
    if produit_id:
        produit = get_object_or_404(Produit, id=produit_id)
        # Vérifier que l'utilisateur a bien commandé ce produit
        if not Commande.objects.filter(
            utilisateur=user, 
            lignes__produit=produit,
            statut=Commande.STATUT_LIVREE
        ).exists():
            messages.error(request, "Vous devez avoir commandé ce produit pour pouvoir laisser un avis.")
            return redirect('tableau_avis')
    else:
        produit = None
    
    # Vérifier si un avis existe déjà pour cette combinaison
    avis_existant = None
    if produit and commande:
        avis_existant = AvisProduit.objects.filter(
            utilisateur=user, 
            produit=produit, 
            commande=commande
        ).first()
    
    # Définition du formulaire simple basé sur votre modèle
    class SimpleAvisForm(forms.Form):
        NOTE_CHOICES = [
            (1, '★☆☆☆☆ - Très mauvais'),
            (2, '★★☆☆☆ - Mauvais'),
            (3, '★★★☆☆ - Moyen'),
            (4, '★★★★☆ - Bon'),
            (5, '★★★★★ - Excellent'),
        ]
        
        note = forms.ChoiceField(
            choices=NOTE_CHOICES,
            widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
            label="Note globale ★"
        )
        titre = forms.CharField(
            max_length=100,
            widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Titre de votre avis'}),
            label="Titre de votre avis"
        )
        commentaire = forms.CharField(
            widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Décrivez votre expérience avec ce produit...'}),
            label="Votre commentaire"
        )
        remarques = forms.CharField(
            required=False,
            widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Suggestions, points d\'amélioration...'}),
            label="Remarques supplémentaires"
        )
        images = MultipleFileField(
            required=False,
            label="Photos du produit"
        )
    
    if request.method == 'POST':
        form = SimpleAvisForm(request.POST, request.FILES)
        if form.is_valid():
            # Créer ou mettre à jour l'avis
            if avis_existant:
                avis = avis_existant
            else:
                avis = AvisProduit()
                
            avis.utilisateur = user
            avis.note = int(form.cleaned_data['note'])
            avis.titre = form.cleaned_data['titre']
            avis.commentaire = form.cleaned_data['commentaire']
            avis.remarques = form.cleaned_data['remarques']
            
            if produit:
                avis.produit = produit
            if commande:
                avis.commande = commande
                
            avis.save()
            
            # Gérer les images
            images = request.FILES.getlist('images')
            for image in images:
                MediaAvis.objects.create(avis=avis, image=image)
            
            messages.success(request, 'Votre avis a été enregistré avec succès. Merci !')
            return redirect('tableau_avis')
    else:
        # Pré-remplir le formulaire si un avis existe déjà
        initial_data = {}
        if avis_existant:
            initial_data = {
                'note': str(avis_existant.note),
                'titre': avis_existant.titre,
                'commentaire': avis_existant.commentaire,
                'remarques': avis_existant.remarques,
            }
        form = SimpleAvisForm(initial=initial_data)
    
    context = {
        'form': form,
        'commande': commande,
        'produit': produit,
        'avis_existant': avis_existant,
    }
    
    return render(request, 'dashboards/client/laisser_avis.html', context)
@login_required
def mes_avis(request):
    """Afficher tous les avis de l'utilisateur"""
    avis_list = AvisProduit.objects.filter(
        utilisateur=request.user
    ).select_related('produit', 'commande').prefetch_related('medias', 'reponses').order_by('-date_creation')
    
    paginator = Paginator(avis_list, 10)
    page_number = request.GET.get('page')
    avis = paginator.get_page(page_number)
    
    context = {
        'avis': avis,
    }
    
    return render(request, 'dashboards/client/mes_avis.html', context)

@login_required
def modifier_avis(request, avis_id):
    """Modifier un avis existant"""
    avis = get_object_or_404(AvisProduit, id=avis_id, utilisateur=request.user)
    
    if request.method == 'POST':
        form = AvisProduitForm(request.POST, request.FILES, instance=avis)
        if form.is_valid():
            form.save()
            
            # Gérer les nouvelles images
            images = request.FILES.getlist('images')
            for image in images:
                MediaAvis.objects.create(avis=avis, image=image)
            
            messages.success(request, 'Votre avis a été modifié avec succès.')
            return redirect('mes_avis')
    else:
        form = AvisProduitForm(instance=avis)
    
    context = {
        'form': form,
        'avis': avis,
    }
    
    return render(request, 'dashboards/client/modifier_avis.html', context)

@login_required
def supprimer_avis(request, avis_id):
    """Supprimer un avis"""
    avis = get_object_or_404(AvisProduit, id=avis_id, utilisateur=request.user)
    
    if request.method == 'POST':
        avis.delete()
        messages.success(request, 'Votre avis a été supprimé avec succès.')
        return redirect('mes_avis')
    
    context = {
        'avis': avis,
    }
    
    return render(request, 'dashboards/client/supprimer_avis.html', context)

@login_required
def noter_commande_complete(request, commande_id):
    """Noter une commande complète"""
    commande = get_object_or_404(Commande, id=commande_id, utilisateur=request.user)
    
    # Vérifier si la commande est livrée
    if commande.statut != Commande.STATUT_LIVREE:
        messages.error(request, "Vous ne pouvez noter que les commandes livrées.")
        return redirect('tableau_avis')
    
    # Vérifier si une notation existe déjà
    notation_existante = NotationCommande.objects.filter(
        utilisateur=request.user, 
        commande=commande
    ).first()
    
    if request.method == 'POST':
        form = NotationCommandeForm(request.POST, request.FILES, instance=notation_existante)
        if form.is_valid():
            notation = form.save(commit=False)
            notation.utilisateur = request.user
            notation.commande = commande
            notation.save()
            
            # Gérer les images
            images = request.FILES.getlist('images')
            for image in images:
                MediaNotationCommande.objects.create(notation=notation, image=image)
            
            messages.success(request, 'Merci d\'avoir noté votre commande !')
            return redirect('detail_notation_commande', notation_id=notation.id)
    else:
        form = NotationCommandeForm(instance=notation_existante)
    
    # Préparer les produits de la commande pour le template
    produits_commande = commande.lignes.select_related('produit').all()
    
    context = {
        'form': form,
        'commande': commande,
        'produits_commande': produits_commande,
        'notation_existante': notation_existante,
    }
    
    return render(request, 'dashboards/client/noter_commande.html', context)

@login_required
def detail_notation_commande(request, notation_id):
    """Voir le détail d'une notation de commande"""
    notation = get_object_or_404(NotationCommande, id=notation_id, utilisateur=request.user)
    
    context = {
        'notation': notation,
    }
    
    return render(request, 'client/detail_notation_commande.html', context)

@login_required
def signaler_probleme(request, commande_id):
    """Signaler un problème sur une commande"""
    commande = get_object_or_404(Commande, id=commande_id, utilisateur=request.user)
    
    # Préparer les produits de la commande pour le choix
    produits_commande = commande.lignes.select_related('produit').all()
    
    if request.method == 'POST':
        form = ProblemeCommandeForm(request.POST, request.FILES)
        if form.is_valid():
            probleme = form.save(commit=False)
            probleme.utilisateur = request.user
            probleme.commande = commande
            probleme.save()
            
            # Gérer les images
            images = request.FILES.getlist('images')
            for image in images:
                media = MediaNotationCommande.objects.create(image=image)
                probleme.photos.add(media)
            
            # Envoyer une notification au support
            messages.success(request, 'Votre problème a été signalé. Nous allons le traiter rapidement.')
            return redirect('detail_commande_client', commande_id=commande.id)
    else:
        form = ProblemeCommandeForm()
        form.fields['produit_concerne'].queryset = Produit.objects.filter(
            id__in=produits_commande.values_list('produit_id', flat=True)
        )
    
    context = {
        'form': form,
        'commande': commande,
        'produits_commande': produits_commande,
    }
    
    return render(request, 'client/signaler_probleme.html', context)

@login_required
def mes_notations_commandes(request):
    """Afficher toutes les notations de commandes de l'utilisateur"""
    notations = NotationCommande.objects.filter(
        utilisateur=request.user
    ).select_related('commande').prefetch_related('medias').order_by('-date_creation')
    
    paginator = Paginator(notations, 10)
    page_number = request.GET.get('page')
    notations_page = paginator.get_page(page_number)
    
    context = {
        'notations': notations_page,
    }
    
    return render(request, 'client/mes_notations_commandes.html', context)