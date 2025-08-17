from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View,DeleteView,DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from .models import *
from .forms import *
from django.contrib.auth import login, authenticate, logout,get_user_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db import models
from datetime import timedelta
from django.contrib.auth.views import PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
User = get_user_model()
from django.db.models import Q
from django.db.models import Count
from decimal import Decimal
from django.core.mail import send_mail
from django.conf import settings
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
# class InscriptionView(CreateView):
#     model = Utilisateur
#     form_class = InscriptionForm
#     template_name = 'frontOfice/compte/inscription.html'
#     success_url = reverse_lazy('home')

#     def form_valid(self, form):
#         response = super().form_valid(form)
#         login(self.request, self.object)  
#         messages.success(self.request, "Inscription réussie !")
#         return response
    

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

# def connexion(request):
#     if request.method == 'POST':
#         form = ConnexionForm(request.POST)
#         if form.is_valid():
#             username = form.cleaned_data['username']
#             password = form.cleaned_data['password']
#             user = authenticate(request, username=username, password=password)
            
#             if user is not None:
#                 login(request, user)
#                 messages.success(request, f"Bienvenue {user.username} !")
#                 return redirect('home')
#             else:
#                 messages.error(request, "Identifiants incorrects")
#     else:
#         form = ConnexionForm()
    
#     return render(request, 'frontOfice/compte/connexion.html', {'form': form})


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


@login_required
def finalisation_commande(request):
    # Récupération du panier de l'utilisateur connecté
    try:
        panier = Panier.objects.get(utilisateur=request.user)
        if not panier.lignes.exists():
            messages.warning(request, "Votre panier est vide")
            return redirect('produits')
    except Panier.DoesNotExist:
        messages.warning(request, "Votre panier est vide")
        return redirect('produits')

    total_panier = sum(l.produit.prix * l.quantite for l in panier.lignes.all())
    coupon_form = CouponForm(request.POST or None)
    coupon_message = None
    coupon = None

    # Application du coupon
    if request.method == 'POST' and 'appliquer_coupon' in request.POST:
        if coupon_form.is_valid():
            code = coupon_form.cleaned_data['code']
            try:
                coupon = Coupon.objects.get(code=code, actif=True)
                if hasattr(coupon, 'is_valide') and coupon.is_valide():
                    request.session['coupon_id'] = coupon.id
                    coupon_message = f"Coupon appliqué : {coupon.reduction}% de réduction"
                else:
                    coupon_message = "Ce coupon a expiré"
            except Coupon.DoesNotExist:
                coupon_message = "Coupon invalide"

    # Finalisation commande
    if request.method == 'POST' and 'finaliser_commande' in request.POST:
        nom = request.POST.get('nom')
        prenom = request.POST.get('prenom')
        email = request.POST.get('email')
        telephone = request.POST.get('telephone')

        mode_livraison = request.POST.get('mode_livraison')
        methode_paiement = request.POST.get('methode_paiement')

        adresse_livraison = None
        if mode_livraison == 'livraison':
            adresse_livraison = AdresseLivraison.objects.create(
                utilisateur=request.user,
                rue=request.POST.get('rue'),
                ville=request.POST.get('ville'),
                code_postal=request.POST.get('code_postal'),
                pays=request.POST.get('pays')
            )

        total = total_panier
        coupon_id = request.session.get('coupon_id')
        if coupon_id:
            coupon = Coupon.objects.get(id=coupon_id)
            if hasattr(coupon, 'is_valide') and coupon.is_valide():
                total = total * (Decimal(1) - (coupon.reduction / Decimal(100)))

        commande = Commande.objects.create(
            utilisateur=request.user,
            total=total,
            adresse_livraison=adresse_livraison,
            methode_paiement=methode_paiement,
            statut='en_attente',
            coupon=coupon if coupon_id else None
        )

        for ligne in panier.lignes.all():
            LigneCommande.objects.create(
                commande=commande,
                produit=ligne.produit,
                quantite=ligne.quantite,
                prix_unitaire=ligne.produit.prix
            )

        if methode_paiement in ['mobile_money', 'carte']:
            Paiement.objects.create(
                commande=commande,
                montant=total,
                statut='en_attente'
            )

        panier.lignes.all().delete()
        if 'coupon_id' in request.session:
            del request.session['coupon_id']

        return redirect('confirmation_commande', commande_id=commande.id)

    context = {
        'panier': panier,
        'total_panier': total_panier,
        'coupon_form': coupon_form,
        'coupon_message': coupon_message
    }
    return render(request, 'frontOfice/commandes/finalisation.html', context)

@login_required
def confirmation_commande(request, commande_id):
    commande = get_object_or_404(Commande, id=commande_id, utilisateur=request.user)
    
    # Envoyer notification WhatsApp (exemple simplifié)
    if commande.utilisateur.telephone:
        message = (
            f"Merci pour votre commande #{commande.id} chez Canaan Glacier!\n"
            f"Montant: {commande.total} FCFA\n"
            f"Statut: En préparation"
        )
        # Ici vous intégrerez l'API WhatsApp réelle
        # envoyer_whatsapp(commande.utilisateur.telephone, message)
    
    return render(request, 'commandes/confirmation.html', {'commande': commande})