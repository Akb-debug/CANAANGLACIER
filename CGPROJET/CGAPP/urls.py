from django.urls import path
from . import views

urlpatterns = [
    # Accueil
    path('', views.home, name='home'),
    
    # Produits
    path('produits/', views.ProduitListView.as_view(), name='produits'),
    path('produits/<slug:categorie_slug>/', views.ProduitListView.as_view(), name='produits_par_categorie'),
    path('produit/<int:pk>/', views.ProduitDetailView.as_view(), name='detail_produit'),
    
    # Panier
    path('panier/', views.PanierView.as_view(), name='panier'),
    path('panier/ajouter/<int:produit_id>/', views.ajouter_au_panier, name='ajouter_panier'),
    path('panier/supprimer/<int:commande_id>/', views.supprimer_du_panier, name='supprimer_panier'),
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
   # path('commande/confirmation/', views.commande_confirmation, name='commande_confirmation'),
    
    # Compte
    path('compte/', views.ProfileView.as_view(), name='profile'),
   # path('compte/commandes/', views.HistoriqueCommandesView.as_view(), name='historique_commandes'),
    
    # Contact
    #path('contact/', views.ContactView.as_view(), name='contact'),
    #path('contact/success/', views.contact_success, name='contact_success'),
    
    # Newsletter
    path('newsletter/', views.NewsletterView.as_view(), name='newsletter'),
    #path('newsletter/success/', views.newsletter_success, name='newsletter_success'),
]