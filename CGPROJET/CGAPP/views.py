from django.shortcuts import render, redirect, get_object_or_404
import requests
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View,DeleteView,DetailView
from django.contrib.auth.mixins import LoginRequiredMixin,UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.db import models
from django.utils import timezone
from django.http import JsonResponse
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
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.paginator import Paginator
from django.core.exceptions import ObjectDoesNotExist

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Produit, Panier, LignePanier, Commande, LigneCommande, Notification, Gerant

from django.urls import reverse
import uuid
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse



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
        # Attribuer le rôle "client" avant de sauvegarder
        form.instance.role = 'client'
        
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
    
    # Toutes les catégories (même celles sans produit)
    categories = Categorie.objects.all().order_by('ordre_affichage')[:8]
    
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
    commandes_en_cours = Commande.objects.filter(statut='expediee').order_by('-date_creation')[:15]
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
        'expediee': Commande.objects.filter(statut='expediee').count(),
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
    commandes_recentes = Commande.objects.all().order_by('-date_creation')[:10]
    
    # Statistiques des commandes
    commandes_par_statut = {
        'en_attente': Commande.objects.filter(statut='en_attente').count(),
        'en_cours': Commande.objects.filter(statut='en_cours').count(),
        'livree': Commande.objects.filter(statut='livree').count(),
        'annulee': Commande.objects.filter(statut='annulee').count(),
    }
    
    # Préparer les données pour le graphique des ventes
    aujourd_hui = timezone.now().date()
    debut_semaine = aujourd_hui - timezone.timedelta(days=7)
    
    # Ventes des 7 derniers jours
    ventes_7_jours = []
    for i in range(7):
        date = debut_semaine + timezone.timedelta(days=i)
        total_ventes = Commande.objects.filter(
            date_creation__date=date
        ).aggregate(total=models.Sum('total'))['total'] or 0
        ventes_7_jours.append({
            'date': date,
            'total': float(total_ventes)
        })
    
    # Produits les plus vendus
    produits_vendus = LigneCommande.objects.values('produit__nom').annotate(
        total_vendu=models.Sum('quantite')
    ).order_by('-total_vendu')[:5]
    
    # Notifications non lues pour le gérant
    notifications_non_lues = Notification.objects.filter(utilisateur=request.user, lue=False).count()
    
    # Préparer les données pour le graphique des ventes (format JSON pour JavaScript)
    ventes_7_jours_json = json.dumps([{
        'date': vente['date'].strftime('%Y-%m-%d') if hasattr(vente['date'], 'strftime') else vente['date'],
        'total': vente['total']
    } for vente in ventes_7_jours])
    
    context = {
        'total_revenus_mois': total_revenus_mois,
        'commandes_mois': commandes_mois,
        'mes_produits': mes_produits[:5],  # Limiter à 5 produits pour l'affichage
        'produits_stock_faible': produits_stock_faible,
        'commandes_recentes': commandes_recentes,
        'nb_mes_produits': mes_produits.count(),
        'nb_commandes_attente': commandes_par_statut['en_attente'],
        'nb_commandes_en_cours': commandes_par_statut['en_cours'],
        'nb_commandes_livrees': commandes_par_statut['livree'],
        'nb_commandes_annulees': commandes_par_statut['annulee'],
        'ventes_7_jours': ventes_7_jours,
        'ventes_7_jours_json': ventes_7_jours_json,  # Pour le graphique JavaScript
        'produits_vendus': produits_vendus,
        'notifications_non_lues': notifications_non_lues,
        'aujourd_hui': timezone.now().date(),
        'mois_courant': timezone.now().strftime('%B %Y'),
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
    elif user_role == 'livreur':
        return redirect('dashboard_livreur')
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
def creer_serveur_gerant(request):
    """
    Vue pour que le gérant puisse créer un serveur
    """
    # Vérifier si l'utilisateur est gérant
    if request.user.role != 'gerant':
        messages.error(request, "Accès non autorisé")
        return redirect('dashboard_gerant')
    
    if request.method == 'POST':
        form = CreerServeurForm(request.POST)
        if form.is_valid():
            try:
                serveur_user = form.save(commit=False)
                serveur_user.role = 'serveur'  # S'assurer que le rôle est bien 'serveur'
                serveur_user.save()
                
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
                return redirect('gestion_serveurs_avancee')
            except Exception as e:
                messages.error(request, f"Erreur lors de la création du serveur: {str(e)}")
    else:
        form = CreerServeurForm()
    
    return render(request, 'dashboards/gerant/creer_serveur.html', {'form': form})


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


# ==================== GESTION DES CATÉGORIES (ADMIN) ====================

@login_required
def gestion_categories(request):
    """Vue pour gérer les catégories (Admin seulement)"""
    if request.user.role != 'admin':
        messages.error(request, "Accès non autorisé")
        return redirect('home')
    
    categories = Categorie.objects.all().order_by('ordre_affichage', 'nom')
    
    context = {
        'categories': categories,
        'total_categories': categories.count(),
    }
    
    return render(request, 'dashboards/admin/gestion_categories.html', context)

@login_required
def ajouter_categorie(request):
    """Vue pour ajouter une nouvelle catégorie"""
    if request.user.role != 'admin':
        messages.error(request, "Accès non autorisé")
        return redirect('home')
    
    if request.method == 'POST':
        form = CategorieForm(request.POST, request.FILES)
        if form.is_valid():
            categorie = form.save()
            
            # Enregistrer l'action
            enregistrer_action(
                utilisateur=request.user,
                type_action='categorie_ajout',
                description=f"Ajout de la catégorie '{categorie.nom}'",
                objet_concerne=f"Catégorie #{categorie.id}",
                objet_id=categorie.id,
                request=request
            )
            
            messages.success(request, f"Catégorie '{categorie.nom}' ajoutée avec succès")
            return redirect('gestion_categories')
    else:
        form = CategorieForm()
    
    return render(request, 'dashboards/admin/ajouter_categorie.html', {'form': form})

@login_required
def modifier_categorie(request, categorie_id):
    """Vue pour modifier une catégorie"""
    if request.user.role != 'admin':
        messages.error(request, "Accès non autorisé")
        return redirect('home')
    
    categorie = get_object_or_404(Categorie, id=categorie_id)
    
    if request.method == 'POST':
        form = CategorieForm(request.POST, request.FILES, instance=categorie)
        if form.is_valid():
            categorie = form.save()
            
            # Enregistrer l'action
            enregistrer_action(
                utilisateur=request.user,
                type_action='categorie_modif',
                description=f"Modification de la catégorie '{categorie.nom}'",
                objet_concerne=f"Catégorie #{categorie.id}",
                objet_id=categorie.id,
                request=request
            )
            
            messages.success(request, f"Catégorie '{categorie.nom}' modifiée avec succès")
            return redirect('gestion_categories')
    else:
        form = CategorieForm(instance=categorie)
    
    return render(request, 'dashboards/admin/modifier_categorie.html', {
        'form': form,
        'categorie': categorie
    })

@login_required
def supprimer_categorie(request, categorie_id):
    """Vue pour supprimer une catégorie"""
    if request.user.role != 'admin':
        messages.error(request, "Accès non autorisé")
        return redirect('home')
    
    categorie = get_object_or_404(Categorie, id=categorie_id)
    
    if request.method == 'POST':
        nom_categorie = categorie.nom
        
        # Vérifier s'il y a des produits liés
        if categorie.produits.exists():
            messages.error(request, f"Impossible de supprimer la catégorie '{nom_categorie}' car elle contient des produits")
            return redirect('gestion_categories')
        
        # Enregistrer l'action avant suppression
        enregistrer_action(
            utilisateur=request.user,
            type_action='categorie_suppr',
            description=f"Suppression de la catégorie '{nom_categorie}'",
            objet_concerne=f"Catégorie #{categorie.id}",
            objet_id=categorie.id,
            request=request
        )
        
        categorie.delete()
        messages.success(request, f"Catégorie '{nom_categorie}' supprimée avec succès")
        return redirect('gestion_categories')
    
    return render(request, 'dashboards/admin/supprimer_categorie.html', {
        'categorie': categorie,
        'nb_produits': categorie.produits.count()
    })

# ==================== GESTION DES COUPONS (ADMIN) ====================

@login_required
def gestion_coupons(request):
    """Vue pour gérer les coupons (Admin seulement)"""
    if request.user.role != 'admin':
        messages.error(request, "Accès non autorisé")
        return redirect('home')
    
    coupons = Coupon.objects.all().order_by('-date_creation')
    
    context = {
        'coupons': coupons,
        'total_coupons': coupons.count(),
        'coupons_actifs': coupons.filter(actif=True).count(),
    }
    
    return render(request, 'dashboards/admin/gestion_coupons.html', context)

@login_required
def ajouter_coupon(request):
    """Vue pour ajouter un nouveau coupon sans utiliser le Form"""
    if request.user.role != 'admin':
        messages.error(request, "Accès non autorisé")
        return redirect('home')
    
    if request.method == 'POST':
        # Récupération des données du formulaire
        code = request.POST.get('code', '').strip().upper()
        type_reduction = request.POST.get('type_reduction', 'pourcentage')
        valeur = request.POST.get('valeur', '0')
        date_debut = request.POST.get('date_debut')
        date_fin = request.POST.get('date_fin')
        usage_max = request.POST.get('usage_max', '1')
        actif = request.POST.get('actif') == 'on'
        
        # Validation des données
        errors = {}
        
        # Validation du code
        if not code:
            errors['code'] = "Le code du coupon est obligatoire."
        elif not code.replace('_', '').isalnum():  # Permet les underscores
            errors['code'] = "Le code ne doit contenir que des lettres, chiffres et underscores."
        elif Coupon.objects.filter(code=code).exists():
            errors['code'] = "Ce code de coupon existe déjà."
        
        # Validation de la valeur
        try:
            valeur_decimal = float(valeur)
            if valeur_decimal <= 0:
                errors['valeur'] = "La valeur doit être supérieure à 0."
            elif type_reduction == 'pourcentage' and valeur_decimal > 100:
                errors['valeur'] = "La valeur ne peut pas dépasser 100%."
        except ValueError:
            errors['valeur'] = "Veuillez entrer une valeur numérique valide."
        
        # Validation des dates
        try:
            date_debut_obj = timezone.datetime.strptime(date_debut, '%Y-%m-%dT%H:%M')
            date_fin_obj = timezone.datetime.strptime(date_fin, '%Y-%m-%dT%H:%M')
            
            if date_debut_obj >= date_fin_obj:
                errors['date_fin'] = "La date de fin doit être postérieure à la date de début."
        except (ValueError, TypeError):
            if not date_debut:
                errors['date_debut'] = "La date de début est obligatoire."
            if not date_fin:
                errors['date_fin'] = "La date de fin est obligatoire."
        
        # Validation de l'usage maximum
        try:
            usage_max_int = int(usage_max)
            if usage_max_int < 1:
                errors['usage_max'] = "L'usage maximum doit être au moins de 1."
        except ValueError:
            errors['usage_max'] = "Veuillez entrer un nombre entier valide."
        
        # Si aucune erreur, création du coupon
        if not errors:
            try:
                coupon = Coupon.objects.create(
                    code=code,
                    type_reduction=type_reduction,
                    valeur=valeur_decimal,
                    date_debut=date_debut_obj,
                    date_fin=date_fin_obj,
                    usage_max=usage_max_int,
                    actif=actif
                )
                
                # Enregistrer l'action (si vous avez cette fonction)
                try:
                    enregistrer_action(
                        utilisateur=request.user,
                        type_action='coupon_ajout',
                        description=f"Ajout du coupon '{coupon.code}'",
                        objet_concerne=f"Coupon #{coupon.id}",
                        objet_id=coupon.id,
                        request=request
                    )
                except NameError:
                    pass  # Si la fonction n'existe pas, on ignore
                
                messages.success(request, f"Coupon '{coupon.code}' ajouté avec succès")
                return redirect('gestion_coupons')
            except Exception as e:
                errors['global'] = f"Une erreur s'est produite lors de la création du coupon: {str(e)}"
        
        # S'il y a des erreurs, on réaffiche le formulaire avec les erreurs
        context = {
            'errors': errors,
            'form_data': {
                'code': code,
                'type_reduction': type_reduction,
                'valeur': valeur,
                'date_debut': date_debut,
                'date_fin': date_fin,
                'usage_max': usage_max,
                'actif': actif
            }
        }
        return render(request, 'dashboards/admin/ajouter_coupon.html', context)
    
    else:
        # GET request - afficher le formulaire vide
        return render(request, 'dashboards/admin/ajouter_coupon.html')

@login_required
def modifier_coupon(request, coupon_id):
    """Vue pour modifier un coupon"""
    if request.user.role != 'admin':
        messages.error(request, "Accès non autorisé")
        return redirect('home')
    
    coupon = get_object_or_404(Coupon, id=coupon_id)
    
    if request.method == 'POST':
        form = CouponForm(request.POST, instance=coupon)
        if form.is_valid():
            coupon = form.save()
            
            # Enregistrer l'action
            enregistrer_action(
                utilisateur=request.user,
                type_action='coupon_modif',
                description=f"Modification du coupon '{coupon.code}'",
                objet_concerne=f"Coupon #{coupon.id}",
                objet_id=coupon.id,
                request=request
            )
            
            messages.success(request, f"Coupon '{coupon.code}' modifié avec succès")
            return redirect('gestion_coupons')
    else:
        form = CouponForm(instance=coupon)
    
    return render(request, 'dashboards/admin/modifier_coupon.html', {
        'form': form,
        'coupon': coupon
    })

@login_required
def supprimer_coupon(request, coupon_id):
    """Vue pour supprimer un coupon"""
    if request.user.role != 'admin':
        messages.error(request, "Accès non autorisé")
        return redirect('home')
    
    coupon = get_object_or_404(Coupon, id=coupon_id)
    
    if request.method == 'POST':
        code_coupon = coupon.code
        
        # Enregistrer l'action avant suppression
        enregistrer_action(
            utilisateur=request.user,
            type_action='coupon_suppr',
            description=f"Suppression du coupon '{code_coupon}'",
            objet_concerne=f"Coupon #{coupon.id}",
            objet_id=coupon.id,
            request=request
        )
        
        coupon.delete()
        messages.success(request, f"Coupon '{code_coupon}' supprimé avec succès")
        return redirect('gestion_coupons')
    
    return render(request, 'dashboards/admin/supprimer_coupon.html', {
        'coupon': coupon
    })

# ==================== RAPPORTS ET ANALYSES (ADMIN) ====================
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q, Sum, F
from datetime import datetime, timedelta
from .models import Commande, Produit, Gerant, LigneCommande

@login_required
def rapports_admin(request):
    """Vue pour les rapports et analyses avancées (Admin et Gérant)"""
    if request.user.role not in ['admin', 'gerant']:
        messages.error(request, "Accès non autorisé")
        return redirect('home')
    
    # Période par défaut : 30 derniers jours
    fin = timezone.now()
    debut = fin - timedelta(days=30)
    
    # Filtres de date depuis la requête
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    
    if date_debut:
        debut = timezone.datetime.strptime(date_debut, '%Y-%m-%d').replace(tzinfo=timezone.get_current_timezone())
    if date_fin:
        fin = timezone.datetime.strptime(date_fin, '%Y-%m-%d').replace(tzinfo=timezone.get_current_timezone())
    
    # Statistiques générales
    commandes_periode = Commande.objects.filter(date_creation__range=[debut, fin])
    revenus_periode = commandes_periode.aggregate(total=Sum('total'))['total'] or 0
    
    # Ventes par jour
    ventes_par_jour = []
    current_date = debut.date()
    while current_date <= fin.date():
        ventes_jour = Commande.objects.filter(
            date_creation__date=current_date
        ).aggregate(total=Sum('total'))['total'] or 0
        
        ventes_par_jour.append({
            'date': current_date,
            'total': float(ventes_jour)
        })
        current_date += timedelta(days=1)
    
    # Top produits
    top_produits = Produit.objects.annotate(
        nb_commandes=Count('lignecommande', 
                         filter=Q(lignecommande__commande__date_creation__range=[debut, fin]),
                         distinct=True)
    ).filter(nb_commandes__gt=0).order_by('-nb_commandes')[:10]
    
    # Performance par gérant
    performance_gerants = []
    gerants = Gerant.objects.all()
    
    for gerant in gerants:
        # Calcul des revenus des produits du gérant via les commandes
        produits_gerant = Produit.objects.filter(gerant=gerant)
        
        # Calcul des revenus totaux pour les produits de ce gérant
        resultats = LigneCommande.objects.filter(
            produit__gerant=gerant,
            commande__date_creation__range=[debut, fin]
        ).aggregate(
            total_revenus=Sum(F('quantite') * F('prix_unitaire')),
            nb_commandes=Count('commande', distinct=True)
        )
        
        # Calcul du nombre de produits distincts vendus
        nb_produits_vendus = LigneCommande.objects.filter(
            produit__gerant=gerant,
            commande__date_creation__range=[debut, fin]
        ).values('produit').distinct().count()
        
        performance_gerants.append({
            'gerant': gerant,
            'revenus': resultats['total_revenus'] or 0,
            'nb_commandes': resultats['nb_commandes'] or 0,
            'nb_produits': produits_gerant.count(),
            'nb_produits_vendus': nb_produits_vendus
        })
    
    context = {
        'revenus_periode': revenus_periode,
        'nb_commandes_periode': commandes_periode.count(),
        'ventes_par_jour': ventes_par_jour,
        'top_produits': top_produits,
        'performance_gerants': performance_gerants,
        'date_debut': debut.date(),
        'date_fin': fin.date(),
        'user': request.user,  # Ajout de l'utilisateur au contexte
    }
    
    return render(request, 'dashboards/admin/rapports.html', context)

# ==================== PARAMÈTRES SYSTÈME (ADMIN) ====================

@login_required
def parametres_systeme(request):
    """Vue pour gérer les paramètres système"""
    if request.user.role != 'admin':
        messages.error(request, "Accès non autorisé")
        return redirect('home')
    
    parametres = ParametreSysteme.objects.all().order_by('cle')
    
    context = {
        'parametres': parametres,
        'total_parametres': parametres.count(),
    }
    
    return render(request, 'dashboards/admin/parametres_systeme.html', context)

@login_required
def ajouter_parametre(request):
    """Vue pour ajouter un paramètre système"""
    if request.user.role != 'admin':
        messages.error(request, "Accès non autorisé")
        return redirect('home')
    
    if request.method == 'POST':
        form = ParametreSystemeForm(request.POST)
        if form.is_valid():
            parametre = form.save()
            
            enregistrer_action(
                utilisateur=request.user,
                type_action='configuration',
                description=f"Ajout du paramètre '{parametre.cle}'",
                objet_concerne=f"Paramètre #{parametre.id}",
                objet_id=parametre.id,
                request=request
            )
            
            messages.success(request, f"Paramètre '{parametre.cle}' ajouté avec succès")
            return redirect('parametres_systeme')
    else:
        form = ParametreSystemeForm()
    
    return render(request, 'dashboards/admin/ajouter_parametre.html', {'form': form})

@login_required
def modifier_parametre(request, parametre_id):
    """Vue pour modifier un paramètre système"""
    if request.user.role != 'admin':
        messages.error(request, "Accès non autorisé")
        return redirect('home')
    
    parametre = get_object_or_404(ParametreSysteme, id=parametre_id)
    
    if request.method == 'POST':
        form = ParametreSystemeForm(request.POST, instance=parametre)
        if form.is_valid():
            parametre = form.save()
            
            enregistrer_action(
                utilisateur=request.user,
                type_action='configuration',
                description=f"Modification du paramètre '{parametre.cle}'",
                objet_concerne=f"Paramètre #{parametre.id}",
                objet_id=parametre.id,
                request=request
            )
            
            messages.success(request, f"Paramètre '{parametre.cle}' modifié avec succès")
            return redirect('parametres_systeme')
    else:
        form = ParametreSystemeForm(instance=parametre)
    
    return render(request, 'dashboards/admin/modifier_parametre.html', {
        'form': form,
        'parametre': parametre
    })

# ==================== AUDIT ET SÉCURITÉ (ADMIN) ====================

@login_required
def journal_connexions(request):
    """Vue pour consulter le journal des connexions"""
    if request.user.role != 'admin':
        messages.error(request, "Accès non autorisé")
        return redirect('home')
    
    connexions = JournalConnexion.objects.all().order_by('-date_connexion')[:100]
    
    context = {
        'connexions': connexions,
        'total_connexions': JournalConnexion.objects.count(),
        'connexions_echec': JournalConnexion.objects.filter(succes=False).count(),
    }
    
    return render(request, 'dashboards/admin/journal_connexions.html', context)

@login_required
def audit_securite(request):
    """Vue pour l'audit et la sécurité"""
    if request.user.role != 'admin':
        messages.error(request, "Accès non autorisé")
        return redirect('home')
    
    # Statistiques de sécurité (simulation)
    stats = {
        'connexions_suspectes': 3,
        'tentatives_echec': 12,
        'alertes_actives': 2,
        'derniere_sauvegarde': '2024-01-15 14:30',
    }
    
    # Journal des connexions récentes
    connexions_recentes = JournalConnexion.objects.all().order_by('-date_connexion')[:10]
    
    # Alertes de sécurité (simulation)
    alertes_securite = [
        {
            'type': 'Tentative de connexion suspecte',
            'description': 'Plusieurs tentatives échouées depuis IP 192.168.1.100',
            'date': '2024-01-15 10:30',
            'niveau': 'warning'
        },
        {
            'type': 'Accès non autorisé',
            'description': 'Tentative d\'accès à la zone admin par un utilisateur non autorisé',
            'date': '2024-01-15 09:15',
            'niveau': 'danger'
        }
    ]
    
    # Sauvegardes système
    sauvegardes = SauvegardeSysteme.objects.all().order_by('-date_creation')[:5]
    
    context = {
        'stats': stats,
        'connexions_recentes': connexions_recentes,
        'alertes_securite': alertes_securite,
        'sauvegardes': sauvegardes,
    }
    
    return render(request, 'dashboards/admin/audit_securite.html', context)

@login_required
def creer_sauvegarde(request):
    """Vue pour créer une sauvegarde"""
    if request.user.role != 'admin':
        return JsonResponse({'success': False, 'error': 'Accès non autorisé'})
    
    if request.method == 'POST':
        # Ici vous pourriez implémenter la création de sauvegarde
        # Pour l'instant, on simule juste le succès
        messages.success(request, "Sauvegarde créée avec succès")
        return redirect('audit_securite')
    
    return redirect('audit_securite')

@login_required
def telecharger_sauvegarde(request, sauvegarde_id):
    """Vue pour télécharger une sauvegarde"""
    if request.user.role != 'admin':
        messages.error(request, "Accès non autorisé")
        return redirect('home')
    
    # Ici vous pourriez implémenter le téléchargement
    messages.info(request, f"Téléchargement de la sauvegarde #{sauvegarde_id}")
    return redirect('audit_securite')

@login_required
def configurer_sauvegarde_auto(request):
    """Vue pour configurer les sauvegardes automatiques"""
    if request.user.role != 'admin':
        return JsonResponse({'success': False, 'error': 'Accès non autorisé'})
    
    if request.method == 'POST':
        # Ici vous pourriez implémenter la configuration
        messages.success(request, "Configuration des sauvegardes automatiques mise à jour")
        return redirect('audit_securite')
    
    return redirect('audit_securite')

@login_required
def gestion_financiere_gerant(request):
    """Vue pour la gestion financière du gérant"""
    if request.user.role != 'gerant':
        messages.error(request, "Accès non autorisé")
        return redirect('home')
    
    # Période de filtrage
    periode = request.GET.get('periode', '30')  # 30 jours par défaut
    try:
        jours = int(periode)
    except ValueError:
        jours = 30
    
    date_debut = timezone.now().date() - timedelta(days=jours)
    
    # Calculs financiers
    commandes_periode = Commande.objects.filter(
        date_creation__date__gte=date_debut,
        statut__in=['payee', 'livree']
    )
    
    # KPIs financiers
    chiffre_affaires = commandes_periode.aggregate(
        total=Sum('total')
    )['total'] or 0
    
    nb_commandes = commandes_periode.count()
    panier_moyen = chiffre_affaires / nb_commandes if nb_commandes > 0 else 0
    
    # Simulation des coûts et bénéfices
    couts_totaux = chiffre_affaires * 0.7  # 70% de coûts
    benefice_net = chiffre_affaires - couts_totaux
    marge_beneficiaire = (benefice_net / chiffre_affaires * 100) if chiffre_affaires > 0 else 0
    roi = (benefice_net / couts_totaux * 100) if couts_totaux > 0 else 0
    
    # Top produits par CA
    top_produits = []
    produits = Produit.objects.all()[:10]
    for produit in produits:
        # Simulation des ventes
        ventes_simulees = 20 + (produit.id % 50)
        ca_produit = ventes_simulees * produit.prix
        top_produits.append({
            'nom': produit.nom,
            'ventes': ventes_simulees,
            'ca': ca_produit,
            'pourcentage': (ca_produit / chiffre_affaires * 100) if chiffre_affaires > 0 else 0
        })
    
    # Données pour les graphiques (simulation)
    evolution_ca = [1200, 1350, 1100, 1450, 1600, 1400, 1550]  # 7 derniers jours
    repartition_ventes = [30, 25, 20, 15, 10]  # Par catégorie
    previsions = [1600, 1700, 1650, 1800, 1750, 1900, 1850]  # Prévisions
    
    # Recommandations
    recommandations = [
        {
            'type': 'success',
            'titre': 'Croissance positive',
            'description': f'Le CA a augmenté de 12% sur les {jours} derniers jours'
        },
        {
            'type': 'warning',
            'titre': 'Stock faible',
            'description': 'Certains produits populaires sont en rupture de stock'
        },
        {
            'type': 'info',
            'titre': 'Opportunité',
            'description': 'Considérez une promotion sur les produits à faible rotation'
        }
    ]
    
    context = {
        'periode': jours,
        'chiffre_affaires': chiffre_affaires,
        'benefice_net': benefice_net,
        'marge_beneficiaire': marge_beneficiaire,
        'roi': roi,
        'nb_commandes': nb_commandes,
        'panier_moyen': panier_moyen,
        'top_produits': top_produits,
        'evolution_ca': json.dumps(evolution_ca),
        'repartition_ventes': json.dumps(repartition_ventes),
        'previsions': json.dumps(previsions),
        'recommandations': recommandations,
    }
    
    return render(request, 'dashboards/gerant/gestion_financiere.html', context)


@login_required
def sauvegardes_systeme(request):
    """Vue pour gérer les sauvegardes système"""
    if request.user.role != 'admin':
        messages.error(request, "Accès non autorisé")
        return redirect('dashboard_admin')
    
    sauvegardes = SauvegardeSysteme.objects.all().order_by('-date_creation')
    
    context = {
        'sauvegardes': sauvegardes,
        'total_sauvegardes': sauvegardes.count(),
    }
    return render(request, 'dashboards/admin/sauvegardes_systeme.html', context)


# ==================== VUES MANQUANTES POUR LE DASHBOARD ADMIN ====================

@login_required
@user_passes_test(lambda u: u.role == 'admin')
def gestion_utilisateurs(request):
    """Vue pour la gestion des utilisateurs"""
    utilisateurs = Utilisateur.objects.all().order_by('-date_joined')
    
    context = {
        'utilisateurs': utilisateurs,
        'total_utilisateurs': utilisateurs.count(),
        'utilisateurs_actifs': utilisateurs.filter(is_active=True).count(),
        'nouveaux_utilisateurs': utilisateurs.filter(date_joined__gte=timezone.now() - timedelta(days=30)).count(),
    }
    return render(request, 'dashboards/admin/gestion_utilisateurs.html', context)

@login_required
@user_passes_test(lambda u: u.role == 'admin')
def gestion_commandes_admin(request):
    """Vue pour la gestion des commandes par l'admin"""
    commandes = Commande.objects.all().order_by('-date_creation')
    
    context = {
        'commandes': commandes,
        'total_commandes': commandes.count(),
        'commandes_en_attente': commandes.filter(statut='en_attente').count(),
        'commandes_livrees': commandes.filter(statut='livree').count(),
        'ca_total': commandes.filter(statut='livree').aggregate(total=Sum('total'))['total'] or 0,
    }
    return render(request, 'dashboards/admin/gestion_commandes.html', context)

@login_required
@user_passes_test(lambda u: u.role == 'admin')
def statistiques_admin(request):
    """Vue pour les statistiques détaillées"""
    # Statistiques générales
    stats = {
        'total_utilisateurs': Utilisateur.objects.count(),
        'total_produits': Produit.objects.count(),
        'total_commandes': Commande.objects.count(),
        'ca_mensuel': Commande.objects.filter(
            date_commande__month=timezone.now().month,
            statut='livree'
        ).aggregate(total=Sum('total'))['total'] or 0,
    }
    
    context = {
        'stats': stats,
        'ventes_mensuelles': [12000, 19000, 15000, 25000, 22000, 30000],
        'produits_populaires': ['Glace Vanille', 'Glace Chocolat', 'Sorbet Fraise'],
    }
    return render(request, 'dashboards/admin/statistiques.html', context)
    

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
def historique_actions_gestion(request):
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
        # Vérifier si l'utilisateur a un profil gérant
        if hasattr(self.request.user, 'gerant') and self.request.user.gerant:
            queryset = queryset.filter(gerant=self.request.user.gerant)
        else:
            # Si pas de gérant associé, retourner queryset vide
            queryset = queryset.none()
        
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

# class AjouterProduitView(CreateView):
#     model = Produit
#     form_class = ProduitForm
#     template_name = 'dashboards/gerant/ajouter_produit.html'
#     success_url = reverse_lazy('liste_produits')
    
#     def form_valid(self, form):
#         form.instance.gerant = self.request.user.gerant
#         messages.success(self.request, "Le produit a été ajouté avec succès.")
#         return super().form_valid(form)


from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView
from .models import Produit
from .forms import ProduitForm

class AjouterProduitView(LoginRequiredMixin, CreateView):
    model = Produit
    form_class = ProduitForm
    template_name = 'dashboards/gerant/ajouter_produit.html'
    success_url = reverse_lazy('liste_produits')
    
    def dispatch(self, request, *args, **kwargs):
        # Vérifier que l'utilisateur a le rôle admin ou est un gérant
        if not (hasattr(request.user, 'gerant') or 
                (hasattr(request.user, 'role') and request.user.role == 'admin')):
            messages.error(request, "Vous n'avez pas la permission d'ajouter des produits.")
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        """Passe l'utilisateur connecté au formulaire"""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        # Pour les admins, on n'assigne pas de gérant automatiquement
        # Le gérant sera sélectionné dans le formulaire
        if hasattr(self.request.user, 'gerant'):
            # L'utilisateur est un gérant
            form.instance.gerant = self.request.user.gerant
            messages.success(self.request, "Le produit a été ajouté avec succès à votre boutique.")
        else:
            # L'utilisateur est un admin
            messages.success(self.request, "Le produit a été ajouté avec succès.")
            
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titre'] = "Ajouter un produit"
        context['titre_icon'] = "plus"
        context['submit_text'] = "Ajouter le produit"
        context['est_admin'] = hasattr(self.request.user, 'role') and self.request.user.role == 'admin'
        context['est_gerant'] = hasattr(self.request.user, 'gerant')
        return context

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

@login_required
def gestion_serveurs_avancee(request):
    """Vue pour la gestion avancée des serveurs"""
    if request.user.role != 'gerant':
        messages.error(request, "Accès non autorisé")
        return redirect('home')
    
    # Récupérer tous les serveurs avec leurs statistiques
    serveurs = []
    for serveur in Utilisateur.objects.filter(role='serveur').order_by('last_name', 'first_name'):
        # Commandes traitées aujourd'hui
        commandes_aujourdhui = HistoriqueAction.objects.filter(
            utilisateur=serveur,
            type_action='commande_statut',
            date_action__date=timezone.now().date()
        ).count()
        
        # Dernière activité
        derniere_action = HistoriqueAction.objects.filter(utilisateur=serveur).order_by('-date_action').first()
        
        serveurs.append({
            'id': serveur.id,
            'nom_complet': f"{serveur.first_name} {serveur.last_name}",
            'email': serveur.email,
            'date_embauche': serveur.date_joined.date() if serveur.date_joined else None,
            'photo': serveur.photo_profil,
            'commandes_aujourdhui': commandes_aujourdhui,
            'derniere_activite': derniere_action.date_action if derniere_action else None,
            'statut': 'actif' if derniere_action and derniere_action.date_action >= timezone.now() - timedelta(hours=1) else 'inactif'
        })
    
    # Statistiques générales
    total_serveurs = len(serveurs)
    serveurs_actifs = len([s for s in serveurs if s['statut'] == 'actif'])
    
    # Commandes traitées aujourd'hui
    commandes_traitees = HistoriqueAction.objects.filter(
        type_action='commande_statut',
        date_action__date=timezone.now().date()
    ).count()
    
    # Temps moyen de traitement (basé sur les 30 derniers jours)
    actions_commandes = HistoriqueAction.objects.filter(
        type_action='commande_statut',
        date_action__gte=timezone.now() - timedelta(days=30)
    )
    
    temps_moyen = actions_commandes.aggregate(
        avg_temps=models.Avg('details__temps_traitement', output_field=models.FloatField())
    )['avg_temps'] or 15  # Valeur par défaut si pas de données
    
    # Efficacité basée sur le nombre de commandes traitées par rapport au nombre de commandes reçues
    commandes_recues = Commande.objects.filter(
        date_creation__gte=timezone.now() - timedelta(days=30)
    ).count()
    
    efficacite = 0
    if commandes_recues > 0:
        efficacite = min(100, (commandes_traitees / commandes_recues) * 100)
    
    stats = {
        'total_serveurs': total_serveurs,
        'serveurs_actifs': serveurs_actifs,
        'commandes_traitees': commandes_traitees,
        'temps_moyen_traitement': round(temps_moyen, 1),
        'efficacite_moyenne': round(efficacite, 1),
    }
    
    # Préparer le contexte pour le template
    context = {
        'stats': stats,
        'serveurs': serveurs,
        'page_title': 'Gestion avancée des serveurs',
        'now': timezone.now(),
    }
    
    # Ajout des données de performance aux serveurs
    serveurs_data = []
    for serveur in serveurs:
        # Simulation des données de performance
        serveur_data = serveur.copy()  # Copie des données existantes
        serveur_data.update({
            'est_actif_aujourd_hui': serveur['statut'] == 'actif',
            'temps_moyen_traitement': 12 + (serveur['id'] % 10),  # Simulation
            'efficacite': 70 + (serveur['id'] % 25),  # Simulation
            'note_moyenne': 3.5 + (serveur['id'] % 3) * 0.5,  # Simulation
        })
        serveurs_data.append(serveur_data)
    
    # Tâches planifiées (simulation)
    taches_planifiees = []
    
    # Évaluations récentes (simulation)
    evaluations_recentes = []
    
    # Statistiques hebdomadaires pour le graphique
    stats_hebdo = [25, 30, 28, 35, 32, 20, 15]  # Simulation
    
    # Mise à jour du contexte avec les nouvelles données
    context.update({
        'serveurs': serveurs_data,
        'taches_planifiees': taches_planifiees,
        'evaluations_recentes': evaluations_recentes,
        'stats_hebdo': json.dumps(stats_hebdo),
    })
    
    return render(request, 'dashboards/gerant/gestion_serveurs_avancee.html', context)

@login_required
def communication_notifications(request):
    """Vue pour la communication et les notifications"""
    if request.user.role != 'gerant':
        messages.error(request, "Accès non autorisé")
        return redirect('home')
    
    # Statistiques de communication (simulation)
    stats = {
        'messages_non_lus': 5,
        'messages_envoyes_mois': 42,
        'notifications_actives': 8,
        'taux_reponse': 87.5,
    }
    
    # Conversations (simulation)
    conversations = []
    
    # Serveurs et admins pour les destinataires
    serveurs = Utilisateur.objects.filter(role='serveur')
    admins = Utilisateur.objects.filter(role='admin')
    
    # Historique des notifications (simulation)
    historique_notifications = []
    
    context = {
        'stats': stats,
        'conversations': conversations,
        'serveurs': serveurs,
        'admins': admins,
        'historique_notifications': historique_notifications,
    }
    
    return render(request, 'dashboards/gerant/communication_notifications.html', context)

@login_required
def planifier_tache(request):
    """Vue pour planifier une tâche"""
    if request.user.role != 'gerant':
        return JsonResponse({'success': False, 'error': 'Accès non autorisé'})
    
    if request.method == 'POST':
        # Ici vous pourriez créer un modèle TachePlanifiee
        # Pour l'instant, on simule juste le succès
        messages.success(request, "Tâche planifiée avec succès")
        return redirect('gestion_serveurs_avancee')
    
    return redirect('gestion_serveurs_avancee')

@login_required
def evaluer_serveur(request):
    """Vue pour évaluer un serveur"""
    if request.user.role != 'gerant':
        return JsonResponse({'success': False, 'error': 'Accès non autorisé'})
    
    if request.method == 'POST':
        # Ici vous pourriez créer un modèle EvaluationServeur
        # Pour l'instant, on simule juste le succès
        messages.success(request, "Évaluation enregistrée avec succès")
        return redirect('gestion_serveurs_avancee')
    
    return redirect('gestion_serveurs_avancee')

@login_required
def envoyer_notification_push(request):
    """Vue pour envoyer une notification push"""
    if request.user.role != 'gerant':
        return JsonResponse({'success': False, 'error': 'Accès non autorisé'})
    
    if request.method == 'POST':
        # Ici vous pourriez implémenter l'envoi de notifications push
        # Pour l'instant, on simule juste le succès
        messages.success(request, "Notification envoyée avec succès")
        return redirect('communication_notifications')
    
    return redirect('communication_notifications')

@login_required
def envoyer_message(request):
    """Vue pour envoyer un message"""
    if request.user.role != 'gerant':
        return JsonResponse({'success': False, 'error': 'Accès non autorisé'})
    
    if request.method == 'POST':
        # Ici vous pourriez créer un modèle Message
        # Pour l'instant, on simule juste le succès
        messages.success(request, "Message envoyé avec succès")
        return redirect('communication_notifications')
    
    return redirect('communication_notifications')

@login_required
def gestion_stocks_avancee(request):
    """Vue pour la gestion avancée des stocks"""
    if request.user.role not in ['admin', 'gerant']:
        messages.error(request, "Accès non autorisé")
        return redirect('home')
    
    # Statistiques des stocks
    produits = Produit.objects.all()
    stock_critique = produits.filter(quantite_disponible__lte=5).count()
    stock_faible = produits.filter(quantite_disponible__lte=10, quantite_disponible__gt=5).count()
    
    # Valeur totale du stock
    valeur_stock = sum(p.prix * p.quantite_disponible for p in produits)
    
    # Rotation du stock (simulation)
    rotation_stock = 4.2
    
    stats = {
        'stock_critique': stock_critique,
        'stock_faible': stock_faible,
        'valeur_stock': valeur_stock,
        'rotation_stock': rotation_stock,
    }
    
    # Produits avec détails de stock
    produits_data = []
    for produit in produits:
        produit_data = {
            'id': produit.id,
            'nom': produit.nom,
            'categorie': produit.categorie.nom if produit.categorie else 'Sans catégorie',
            'quantite_disponible': produit.quantite_disponible,
            'prix': produit.prix,
            'valeur_stock': produit.prix * produit.quantite_disponible,
            'statut': 'critique' if produit.quantite_disponible <= 5 else 'faible' if produit.quantite_disponible <= 10 else 'normal',
            'derniere_commande': '2024-01-15',  # Simulation
            'rotation': 3.5 + (produit.id % 5),  # Simulation
        }
        produits_data.append(produit_data)
    
    # Données pour les graphiques
    categories_stock = {}
    for produit in produits:
        cat_nom = produit.categorie.nom if produit.categorie else 'Sans catégorie'
        if cat_nom not in categories_stock:
            categories_stock[cat_nom] = 0
        categories_stock[cat_nom] += produit.quantite_disponible
    
    context = {
        'stats': stats,
        'produits': produits_data,
        'categories_stock': json.dumps(list(categories_stock.values())),
        'categories_labels': json.dumps(list(categories_stock.keys())),
    }
    
    return render(request, 'dashboards/gerant/gestion_stocks_avancee.html', context)

@login_required
def ajuster_stock(request):
    """Vue pour ajuster le stock d'un produit"""
    if request.user.role not in ['admin', 'gerant']:
        return JsonResponse({'success': False, 'error': 'Accès non autorisé'}, status=403)
    
    if request.method == 'POST':
        try:
            produit_id = request.POST.get('produit_id')
            quantite = int(request.POST.get('quantite', 0))
            motif = request.POST.get('motif', '')
            
            produit = Produit.objects.get(id=produit_id)
            ancienne_quantite = produit.quantite_disponible
            
            # Mise à jour de la quantité
            produit.quantite_disponible = F('quantite_disponible') + quantite
            produit.save()
            produit.refresh_from_db()
            
            # Enregistrement de l'historique
            HistoriqueAction.objects.create(
                utilisateur=request.user,
                type_action='ajustement_stock',
                description=f"Ajustement de stock: {ancienne_quantite} → {produit.quantite_disponible}. {motif}",
                details={
                    'produit_id': produit.id,
                    'produit_nom': produit.nom,
                    'ancienne_quantite': ancienne_quantite,
                    'nouvelle_quantite': produit.quantite_disponible,
                    'quantite_ajustee': quantite,
                    'motif': motif
                }
            )
            
            return JsonResponse({
                'success': True,
                'quantite': produit.quantite_disponible,
                'statut': 'critique' if produit.quantite_disponible <= 5 else 'faible' if produit.quantite_disponible <= 10 else 'normal'
            })
            
        except (ValueError, Produit.DoesNotExist) as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)

@login_required
def analyse_performances_gerant(request):
    """Vue pour l'analyse des performances"""
    if request.user.role != 'gerant':
        messages.error(request, "Accès non autorisé")
        return redirect('home')
    
    # KPIs de performance
    total_commandes = Commande.objects.count()
    commandes_mois = Commande.objects.filter(
        date_commande__month=timezone.now().month
    ).count()
    
    # Chiffre d'affaires
    ca_total = Commande.objects.aggregate(
        total=Sum('total')
    )['total'] or 0
    
    ca_mois = Commande.objects.filter(
        date_commande__month=timezone.now().month
    ).aggregate(
        total=Sum('total')
    )['total'] or 0
    
    # Temps moyen de traitement (simulation)
    temps_moyen = 25  # minutes
    
    # Taux de satisfaction (simulation)
    taux_satisfaction = 92.5
    
    stats = {
        'total_commandes': total_commandes,
        'commandes_mois': commandes_mois,
        'ca_total': ca_total,
        'ca_mois': ca_mois,
        'temps_moyen': temps_moyen,
        'taux_satisfaction': taux_satisfaction,
    }
    
    # Top produits
    top_produits = []
    produits = Produit.objects.all()[:10]
    for produit in produits:
        # Simulation des ventes
        ventes = 50 + (produit.id % 100)
        ca_produit = ventes * produit.prix
        top_produits.append({
            'nom': produit.nom,
            'ventes': ventes,
            'ca': ca_produit,
            'marge': ca_produit * 0.3,  # Simulation 30% de marge
        })
    
    # Performance des serveurs (simulation)
    serveurs = Utilisateur.objects.filter(role='serveur')
    performance_serveurs = []
    for serveur in serveurs:
        performance_serveurs.append({
            'nom': f"{serveur.first_name} {serveur.last_name}",
            'commandes_traitees': 15 + (serveur.id % 20),
            'temps_moyen': 20 + (serveur.id % 15),
            'note': 3.5 + (serveur.id % 3) * 0.5,
        })
    
    # Données pour les graphiques (simulation)
    performance_data = [85, 92, 78, 96, 88, 91, 87]
    heures_pointe = [12, 15, 8, 25, 30, 35, 28, 22, 18, 15, 12, 10]
    
    context = {
        'stats': stats,
        'top_produits': top_produits,
        'performance_serveurs': performance_serveurs,
        'performance_data': json.dumps(performance_data),
        'heures_pointe': json.dumps(heures_pointe),
    }
    
    return render(request, 'dashboards/gerant/analyse_performances.html', context)

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
            # commande.statut = 'payée'
            # commande.save()
            
            messages.success(request, f"Paiement effectué avec succès! Numéro de transaction: {numero_transaction}")
            return redirect('commande_detail', pk=commande_id)
        
        elif methode == 'paiement_livraison':
            messages.info(request, "Vous paierez à la livraison de votre commande.")
            return redirect('commande_detail', pk=commande_id)
        
        elif methode == 'retrait_magasin':
            messages.info(request, "Vous paierez lors du retrait en magasin.")
            return redirect('commande_detail', pk=commande_id)
    
    return redirect('commande_detail', pk=commande_id)

# @login_required
# def traiter_paiement(request, commande_id):
#     commande = get_object_or_404(Commande, id=commande_id, utilisateur=request.user)
#     methode = commande.methode_paiement

#     if methode in ['carte_bancaire', 'flooz', 'tmoney']:
#         transaction_id = str(uuid.uuid4())  # ID unique CinetPay
#         montant = float(commande.total)

#         payload = {
#             "apikey": settings.CINETPAY_API_KEY,
#             "site_id": settings.CINETPAY_SITE_ID,
#             "transaction_id": transaction_id,
#             "amount": montant,
#             "currency": "XOF",
#             "description": f"Paiement commande #{commande.id}",
#             "notify_url": request.build_absolute_uri(reverse("cinetpay_notify")),
#             "return_url": request.build_absolute_uri(reverse("commande_detail", args=[commande.id])),
#             "channels": "ALL",
#             "lang": "fr"
#         }

#         response = requests.post(settings.CINETPAY_BASE_URL, json=payload)
#         data = response.json()

#         if data.get("code") == "201":
#             # Créer un paiement lié à la commande avec le transaction_id
#             Paiement.objects.update_or_create(
#                 commande=commande,
#                 defaults={
#                     "montant": commande.total,
#                     "statut": "en cours",
#                     "transaction_id": transaction_id  # ⚡ Sauvegarde l’ID de CinetPay
#                 }
#             )
#             return redirect(data["data"]["payment_url"])
#         else:
#             messages.error(request, f"Erreur CinetPay : {data.get('message', 'Inconnue')}")
#             return redirect("commande_detail", pk=commande.id)

#     elif methode == 'paiement_livraison':
#         messages.info(request, "Vous paierez à la livraison.")
#         return redirect('commande_detail', pk=commande_id)

#     elif methode == 'retrait_magasin':
#         messages.info(request, "Vous paierez lors du retrait en magasin.")
#         return redirect('commande_detail', pk=commande_id)

#     return redirect('commande_detail', pk=commande_id)


@csrf_exempt
def cinetpay_notify(request):
    if request.method == "POST":
        data = request.POST.dict()
        transaction_id = data.get("transaction_id")

        if not transaction_id:
            return JsonResponse({"error": "transaction_id manquant"}, status=400)

        # Vérification auprès de CinetPay
        payload = {
            "apikey": settings.CINETPAY_API_KEY,
            "site_id": settings.CINETPAY_SITE_ID,
            "transaction_id": transaction_id
        }
        response = requests.post(settings.CINETPAY_CHECK_URL, json=payload)
        result = response.json()

        if result.get("code") == "00":  # Paiement validé
            paiement = Paiement.objects.filter(transaction_id=transaction_id).first()
            if paiement:
                paiement.statut = "payé"
                paiement.save()
                paiement.commande.statut = "payée"
                paiement.commande.save()

        return JsonResponse({"status": "ok"})
    return JsonResponse({"error": "Méthode non autorisée"}, status=405)

@login_required
def annuler_paiement(request, commande_id):
    """Vue pour annuler un paiement"""
    commande = get_object_or_404(Commande, id=commande_id, utilisateur=request.user)
    
    # Réactiver le stock des produits (si nécessaire)
    for ligne in commande.lignes.all():
        ligne.produit.quantite_disponible += ligne.quantite
        ligne.produit.save()

   #Modification fait par Benjamin 12/09/2025 
    # Marquer la commande comme annulée
    commande.statut = Commande.STATUT_ANNULEE
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
            commande.statut = Commande.STATUT_TRAITEMENT
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
        ancien_statut = commande.statut
        
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

#-----------------------------Livreur-------------------------------------------



# Fonction utilitaire pour récupérer l'IP du client
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

# Fonction utilitaire pour obtenir ou créer l'objet Livreur
def get_livreur(user):
    """Retourne l'objet Livreur associé à l'utilisateur ou le crée s'il n'existe pas"""
    try:
        return user.livreur
    except ObjectDoesNotExist:
        # Si l'utilisateur a le rôle livreur mais pas d'objet Livreur, on le crée
        if hasattr(user, 'role') and user.role == 'livreur':
            livreur = Livreur.objects.create(utilisateur=user)
            return livreur
        return None

@login_required
def dashboard_livreur(request):
    if not hasattr(request.user, 'role') or request.user.role != 'livreur':
        messages.error(request, "Accès réservé aux livreurs.")
        return redirect('home')
    
    livreur = get_livreur(request.user)
    if livreur is None:
        messages.error(request, "Profil livreur non disponible.")
        return redirect('home')
    
    aujourd_hui = timezone.now().date()
    
    # Commandes à livrer aujourd'hui
    commandes_a_livrer = Commande.objects.filter(
        statut=Commande.STATUT_EXPEDIEE,
    ).order_by('date_creation')
    
    # Commandes livrées aujourd'hui par ce livreur
    commandes_livrees_aujourdhui = Commande.objects.filter(
        statut=Commande.STATUT_LIVREE,
        date_livraison__date=aujourd_hui,
        livreur=livreur
    ).count()
    
    # Statistiques
    stats = {
        'total_a_livrer': commandes_a_livrer.count(),
        'livrees_aujourdhui': commandes_livrees_aujourdhui,
        'en_retard': Commande.objects.filter(
            statut=Commande.STATUT_EXPEDIEE,
            date_creation__date__lt=aujourd_hui
        ).count()
    }
    
    context = {
        'commandes_a_livrer': commandes_a_livrer,
        'stats': stats,
        'aujourd_hui': aujourd_hui
    }
    
    return render(request, 'dashboards/livreur_dashboard.html', context)

@login_required
def commandes_a_livrer(request):
    if not hasattr(request.user, 'role') or request.user.role != 'livreur':
        messages.error(request, "Accès réservé aux livreurs.")
        return redirect('home')
    
    livreur = get_livreur(request.user)
    if livreur is None:
        messages.error(request, "Profil livreur non disponible.")
        return redirect('home')
    
    statut = request.GET.get('statut', 'expediee')
    
    # Filtres de base
    commandes = Commande.objects.filter(statut=Commande.STATUT_EXPEDIEE)
    
    # Filtre par date
    date_filter = request.GET.get('date')
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            commandes = commandes.filter(date_creation__date=filter_date)
        except ValueError:
            pass
    
    # Filtre par recherche
    search_query = request.GET.get('q')
    if search_query:
        commandes = commandes.filter(
            Q(id__icontains=search_query) |
            Q(utilisateur__username__icontains=search_query) |
            Q(adresse_livraison__ville__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(commandes.order_by('date_creation'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'statut_filter': statut,
        'date_filter': date_filter,
        'search_query': search_query
    }
    
    return render(request, 'dashboards/livreur/commandes_a_livrer.html', context)

@login_required
def detail_commande_livreur(request, commande_id):
    if not hasattr(request.user, 'role') or request.user.role != 'livreur':
        messages.error(request, "Accès réservé aux livreurs.")
        return redirect('home')
    
    livreur = get_livreur(request.user)
    if livreur is None:
        messages.error(request, "Profil livreur non disponible.")
        return redirect('home')
    
    commande = get_object_or_404(Commande, id=commande_id)
    
    if request.method == 'POST':
        # Marquer comme livrée
        if 'livrer' in request.POST:
            commande.statut = Commande.STATUT_LIVREE
            commande.date_livraison = timezone.now()
            commande.livreur = livreur
            commande.save()
            
            # Créer une notification pour le client
            Notification.objects.create(
                utilisateur=commande.utilisateur,
                type_notification='commande_livree',
                titre='Commande livrée',
                message=f'Votre commande #{commande.id} a été livrée avec succès.',
                commande=commande
            )
            
            # Historique d'action
            HistoriqueAction.objects.create(
                utilisateur=request.user,
                type_action='commande_statut',
                description=f'Commande #{commande.id} marquée comme livrée',
                objet_concerne=f'Commande #{commande.id}',
                objet_id=commande.id,
                adresse_ip=get_client_ip(request)
            )
            
            messages.success(request, f'Commande #{commande.id} marquée comme livrée avec succès.')
            return redirect('commandes_a_livrer')
    
    context = {
        'commande': commande,
        'lignes_commande': commande.lignes.all()
    }
    
    return render(request, 'dashboards/livreur/detail_commande.html', context)

@login_required
def commandes_livrees(request):
    if not hasattr(request.user, 'role') or request.user.role != 'livreur':
        messages.error(request, "Accès réservé aux livreurs.")
        return redirect('home')
    
    livreur = get_livreur(request.user)
    if livreur is None:
        messages.error(request, "Profil livreur non disponible.")
        return redirect('home')
    
    # Commandes livrées par ce livreur
    commandes = Commande.objects.filter(
        statut=Commande.STATUT_LIVREE,
        livreur=livreur
    )
    
    # Filtres
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    
    if date_debut:
        commandes = commandes.filter(date_livraison__date__gte=date_debut)
    if date_fin:
        commandes = commandes.filter(date_livraison__date__lte=date_fin)
    
    # Statistiques
    stats = {
        'total_livrees': commandes.count(),
        'livrees_semaine': commandes.filter(
            date_livraison__gte=timezone.now() - timedelta(days=7)
        ).count(),
        'moyenne_journaliere': commandes.filter(
            date_livraison__gte=timezone.now() - timedelta(days=30)
        ).count() / 30
    }
    
    # Pagination
    paginator = Paginator(commandes.order_by('-date_livraison'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'stats': stats,
        'date_debut': date_debut,
        'date_fin': date_fin
    }
    
    return render(request, 'dashboards/livreur/commandes_livrees.html', context)

@login_required
def historique_actions(request):
    if not hasattr(request.user, 'role') or request.user.role != 'livreur':
        messages.error(request, "Accès réservé aux livreurs.")
        return redirect('home')
    
    actions = HistoriqueAction.objects.filter(utilisateur=request.user)
    
    # Filtre par type d'action
    type_action = request.GET.get('type_action')
    if type_action:
        actions = actions.filter(type_action=type_action)
    
    # Filtre par date
    date_filter = request.GET.get('date')
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            actions = actions.filter(date_action__date=filter_date)
        except ValueError:
            pass
    
    # Pagination
    paginator = Paginator(actions.order_by('-date_action'), 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'type_action_filter': type_action,
        'date_filter': date_filter,
        'types_actions': HistoriqueAction.TYPE_ACTION_CHOICES
    }
    
    return render(request, 'dashboards/livreur/historique_actions.html', context)

@login_required
def profil_livreur(request):
    if not hasattr(request.user, 'role') or request.user.role != 'livreur':
        messages.error(request, "Accès réservé aux livreurs.")
        return redirect('home')
    
    livreur = get_livreur(request.user)
    if livreur is None:
        messages.error(request, "Profil livreur non disponible.")
        return redirect('home')
    
    if request.method == 'POST':
        # Mettre à jour les informations du profil
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.telephone = request.POST.get('telephone', user.telephone)
        user.save()
        
        messages.success(request, 'Profil mis à jour avec succès.')
        return redirect('profil_livreur')
    
    # Statistiques du livreur
    stats = {
        'commandes_livrees': Commande.objects.filter(
            livreur=livreur, 
            statut=Commande.STATUT_LIVREE
        ).count(),
        'commandes_mois': Commande.objects.filter(
            livreur=livreur,
            statut=Commande.STATUT_LIVREE,
            date_livraison__month=timezone.now().month
        ).count()
    }
    
    context = {
        'stats': stats
    }
    
    return render(request, 'dashboards/livreur/profil.html', context)

# views.py
@login_required
def changer_statut_commande_livreur(request, commande_id):
    """
    View pour changer le statut d'une commande de 'expédiée' à 'livrée'
    """
    if not hasattr(request.user, 'role') or request.user.role != 'livreur':
        messages.error(request, "Accès réservé aux livreurs.")
        return redirect('home')
    
    livreur = get_livreur(request.user)
    if livreur is None:
        messages.error(request, "Profil livreur non disponible.")
        return redirect('home')
    
    # Récupérer la commande
    commande = get_object_or_404(Commande, id=commande_id)
    
    # Vérifier que la commande est bien expédiée
    if commande.statut != Commande.STATUT_EXPEDIEE:
        messages.error(request, f"La commande #{commande.id} n'est pas expédiée.")
        return redirect('commandes_a_livrer')
    
    if request.method == 'POST':
        try:
            # Mettre à jour le statut de la commande
            commande.statut = Commande.STATUT_LIVREE
            commande.date_livraison = timezone.now()
            commande.livreur = livreur
            commande.save()
            
            # Créer une notification pour le client
            Notification.objects.create(
                utilisateur=commande.utilisateur,
                type_notification='commande_livree',
                titre='Commande livrée',
                message=f'Votre commande #{commande.id} a été livrée avec succès par {request.user.get_full_name()}.',
                commande=commande
            )
            
            # Enregistrer dans l'historique des actions
            HistoriqueAction.objects.create(
                utilisateur=request.user,
                type_action='commande_statut',
                description=f'Commande #{commande.id} marquée comme livrée',
                objet_concerne=f'Commande #{commande.id}',
                objet_id=commande.id,
                adresse_ip=get_client_ip(request)
            )
            
            messages.success(request, f'Commande #{commande.id} marquée comme livrée avec succès.')
            return redirect('commandes_a_livrer')
                
        except Exception as e:
            messages.error(request, f"Erreur lors de la mise à jour: {str(e)}")
            return redirect('detail_commande', commande_id=commande.id)
    
    # Si méthode GET, afficher la page de confirmation
    context = {
        'commande': commande,
        'lignes_commande': commande.lignes.all()
    }
    
    return render(request, 'dashboards/livreur/livreur_confirmation_livraison.html', context)




#++++++++++++++++++++++++++++ +++++++++++++++++++++++++++++++++++

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

