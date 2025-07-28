from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from .models import Produit, Categorie, Panier, Commande, Contact, AbonnementNewsletter
from .forms import ContactForm, NewsletterForm, CommandeForm

# Vue Accueil
def home(request):
    produits_nouveautes = Produit.objects.order_by('-id')[:8]
    produits_populaires = Produit.objects.order_by('?')[:4]
    categories = Categorie.objects.all()[:6]
    
    context = {
        'nouveautes': produits_nouveautes,
        'populaires': produits_populaires,
        'categories': categories,
    }
    return render(request, 'frontOfice/home/index.html', context)

# Liste des Produits
class ProduitListView(ListView):
    model = Produit
    template_name = 'produits/liste.html'
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
    template_name = 'produits/detail.html'
    context_object_name = 'produit'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['produits_similaires'] = Produit.objects.filter(
            categorie=self.object.categorie
        ).exclude(id=self.object.id)[:4]
        return context

# Gestion Panier
class PanierView(LoginRequiredMixin, ListView):
    template_name = 'panier/panier.html'
    context_object_name = 'commandes'
    
    def get_queryset(self):
        panier, created = Panier.objects.get_or_create(client__utilisateur=self.request.user)
        return panier.commande_set.all()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        panier = Panier.objects.get(client__utilisateur=self.request.user)
        total = sum(commande.produit.prix * commande.quantite for commande in context['commandes'])
        context['total'] = total
        return context

def ajouter_au_panier(request, produit_id):
    produit = get_object_or_404(Produit, id=produit_id)
    panier, created = Panier.objects.get_or_create(client__utilisateur=request.user)
    commande, created = Commande.objects.get_or_create(
        panier=panier,
        produit=produit,
        defaults={'quantite': 1}
    )
    if not created:
        commande.quantite += 1
        commande.save()
    messages.success(request, f"{produit.nom} ajouté à votre panier")
    return redirect('panier')

def supprimer_du_panier(request, commande_id):
    commande = get_object_or_404(Commande, id=commande_id, panier__client__utilisateur=request.user)
    commande.delete()
    messages.success(request, "Produit retiré du panier")
    return redirect('panier')

# Checkout
class CheckoutView(LoginRequiredMixin, CreateView):
    template_name = 'panier/checkout.html'
    form_class = CommandeForm
    success_url = reverse_lazy('commande_confirmation')
    
    def form_valid(self, form):
        panier = Panier.objects.get(client__utilisateur=self.request.user)
        commandes = panier.commande_set.all()
        
        if not commandes.exists():
            messages.error(self.request, "Votre panier est vide")
            return redirect('panier')
            
        # Créer la commande et le paiement
        # ... logique de traitement ...
        
        # Vider le panier
        panier.commande_set.all().delete()
        
        messages.success(self.request, "Votre commande a été passée avec succès!")
        return super().form_valid(form)

# Contact
class ContactView(CreateView):
    model = Contact
    form_class = ContactForm
    template_name = 'contact/contact.html'
    success_url = reverse_lazy('contact_success')
    
    def form_valid(self, form):
        messages.success(self.request, "Votre message a été envoyé avec succès!")
        return super().form_valid(form)

# Newsletter
class NewsletterView(CreateView):
    model = AbonnementNewsletter
    form_class = NewsletterForm
    template_name = 'newsletter/subscribe.html'
    success_url = reverse_lazy('newsletter_success')
    
    def form_valid(self, form):
        messages.success(self.request, "Merci pour votre inscription à notre newsletter!")
        return super().form_valid(form)

# Compte Utilisateur
class ProfileView(LoginRequiredMixin, UpdateView):
    template_name = 'compte/profile.html'
    fields = ['first_name', 'last_name', 'email', 'telephone']
    success_url = reverse_lazy('profile')
    
    def get_object(self):
        return self.request.user


    def commande_confirmation(request):
        return render(request, 'commande/confirmation.html')  # crée aussi ce template
