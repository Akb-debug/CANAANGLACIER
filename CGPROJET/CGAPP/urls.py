from django.urls import path,include
from . import views

urlpatterns = [
    # Accueil
    path('', views.home, name='home'),
    # Apropos
    path('apropos',views.apropos, name='apropos'),
    
    # Produits
    path('produits/', views.ProduitListView.as_view(), name='produits'),
    path('produits/<slug:categorie_slug>/', views.ProduitListView.as_view(), name='produits_par_categorie'),
    path('produit/<int:pk>/', views.ProduitDetailView.as_view(), name='detail_produit'),
    path('categories/<int:id>/', views.detail_categorie, name='detail_categorie'),
    
    # #Panier
    # path('panier/', views.PanierView.as_view(), name='panier'),
    # path('panier/ajouter/<int:produit_id>/', views.ajouter_au_panier, name='ajouter_panier'),
    # path('panier/supprimer/<int:commande_id>/', views.supprimer_du_panier, name='supprimer_panier'),
    # path('panier/modifier/<int:commande_id>/', views.modifier_quantite, name='modifier_quantite'),
    # path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    #path('commande/confirmation/', views.commande_confirmation, name='commande_confirmation'),

    path('panier/', views.voir_panier, name='panier'),
    path('panier/ajouter/<int:produit_id>/', views.ajouter_au_panier, name='ajouter_au_panier'),
    path('panier/augmenter/<int:ligne_id>/', views.augmenter_quantite, name='augmenter_quantite'),
    path('panier/diminuer/<int:ligne_id>/', views.diminuer_quantite, name='diminuer_quantite'),
    path('panier/supprimer/<int:ligne_id>/', views.supprimer_du_panier, name='supprimer_du_panier'),
    path('panier/vider/', views.vider_panier, name='vider_panier'),
    #path('panier/valider/', views.valider_panier, name='valider_panier'),

    # URLs pour la commande
    path('commande/valider/', views.valider_commande, name='valider_commande'),
    path('commande/suivi/<int:commande_id>/', views.suivi_commande, name='suivi_commande'),
    path('commande/ajouter-adresse/', views.ajouter_adresse, name='ajouter_adresse'),
    path('commande/appliquer-coupon/', views.appliquer_coupon, name='appliquer_coupon'),
    # Page de paiement (checkout)
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    # Compte
    path('compte/', views.ProfileView.as_view(), name='profile'),
   # path('compte/commandes/', views.HistoriqueCommandesView.as_view(), name='historique_commandes'),
    
    # Contact
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('contact/success/', views.contact_success, name='contact_success'),
    
    # Newsletter
     path('abonnement-newsletter/', views.NewsletterSubscribeView.as_view(), name='newsletter_subscribe'),
    #path('newsletter/success/', views.newsletter_success, name='newsletter_success'),
    # Inscription et connexion
    path('inscription/', views.InscriptionView.as_view(), name='inscription'),
    path('connexion/', views.connexion, name='connexion'),
    path('deconnexion/', views.deconnexion, name='deconnexion'),
    #path('profil/', views.profil, name='profil'),
    path('password-reset/', include('django.contrib.auth.urls')),
]