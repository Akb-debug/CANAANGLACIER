from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from .models import Produit, Categorie, Panier, Commande, Contact, Utilisateur,LignePanier
from .forms import ContactForm, NewsletterForm, CommandeForm,InscriptionForm, ConnexionForm
from django.contrib.auth import login, authenticate, logout

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
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Commande, AdresseLivraison, Coupon

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
    
    return JsonResponse({'success': False, 'error': 'Requête invalide'})
