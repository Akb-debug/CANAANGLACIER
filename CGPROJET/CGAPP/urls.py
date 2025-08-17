from django.urls import path,include
from . import views
from .views import CustomPasswordChangeView,DeleteAccountView
from django.contrib.auth.decorators import login_required


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
    path('panier/', views.voir_panier, name='panier'),
    path('panier/ajouter/<int:produit_id>/', views.ajouter_au_panier, name='ajouter_au_panier'),
    path('panier/augmenter/<int:ligne_id>/', views.augmenter_quantite, name='augmenter_quantite'),
    path('panier/diminuer/<int:ligne_id>/', views.diminuer_quantite, name='diminuer_quantite'),
    path('panier/supprimer/<int:ligne_id>/', views.supprimer_du_panier, name='supprimer_du_panier'),
    path('panier/vider/', views.vider_panier, name='vider_panier'),

    # URLs pour la commande
    path('commande/valider/', views.valider_commande, name='valider_commande'),
    path('commande/suivi/<int:commande_id>/', views.suivi_commande, name='suivi_commande'),
    path('commande/ajouter-adresse/', views.ajouter_adresse, name='ajouter_adresse'),
    path('commande/appliquer-coupon/', views.appliquer_coupon, name='appliquer_coupon'),
    path('finaliser-commande/', views.finalisation_commande, name='finaliser_commande'),
    path('confirmation-commande/<int:commande_id>/', views.confirmation_commande, name='confirmation_commande'),

    # Page de paiement (checkout)
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    # Compte
    path('mon-compte/', views.mon_compte, name='mon_compte'),
    path('compte/', views.ProfileView.as_view(), name='profile'),
    path('changer-mot-de-passe/', CustomPasswordChangeView.as_view(), name='password_change'),
    path('supprimer-compte/', DeleteAccountView.as_view(), name='delete_account'),
    
    # Dashboards
    path('dashboard/admin/', views.dashboard_admin, name='dashboard_admin'),
    path('dashboard/serveur/', views.dashboard_serveur, name='dashboard_serveur'),
    path('dashboard/gerant/', views.dashboard_gerant, name='dashboard_gerant'),
    path('dashboard/client/', views.dashboard_client, name='dashboard_client'),
    
    # Actions pour les dashboards
    path('commande/changer-statut/<int:commande_id>/', views.changer_statut_commande, name='changer_statut_commande'),
    
    # Gestion des utilisateurs par l'admin
    path('gestion/creer-gerant/', views.creer_gerant, name='creer_gerant'),
    path('gestion/creer-serveur/', views.creer_serveur, name='creer_serveur'),
    path('gestion/liste-utilisateurs/', views.liste_utilisateurs, name='liste_utilisateurs'),
    path('gestion/historique-actions/', views.historique_actions, name='historique_actions'),
    
    # Gestion des produits par le gérant
      # CRUD
    path('listeProduit/', login_required(views.ListeProduitsView.as_view()), name='liste_produits'),
    path('ajouterProduit/', login_required(views.AjouterProduitView.as_view()), name='ajouter_produit'),
    path('<int:pk>/detail', login_required(views.DetailProduitView.as_view()), name='detail_produit'),
    path('<int:pk>/modifier/', login_required(views.ModifierProduitView.as_view()), name='modifier_produit'),
    path('<int:pk>/supprimer/', login_required(views.SupprimerProduitView.as_view()), name='supprimer_produit'),
    
    # Recherche et filtrage
    path('recherche/', login_required(views.recherche_produits), name='recherche_produits'),
    path('api/produits/', login_required(views.ProduitAPIView.as_view()), name='api_produits'),
    #Gestion serveurs
    path('serveurs/', login_required(views.ListeServeursView.as_view()), name='liste_serveurs'),
    path('serveurs/<int:pk>/rapport/', login_required(views.rapport_serveur), name='rapport_serveur'),
    # Notifications
    path('notifications/', views.mes_notifications, name='mes_notifications'),
    path('notifications/marquer-lue/<int:notification_id>/', views.marquer_notification_lue, name='marquer_notification_lue'),
    path('api/notifications/count/', views.notifications_non_lues_count, name='notifications_count'),
    
    # Contact
    path('contact/', views.contact_view, name='contact'),
    path('contact/success/', views.contact_success, name='contact_success'),
    
    # Newsletter
     path('abonnement-newsletter/', views.NewsletterSubscribeView.as_view(), name='newsletter_subscribe'),
    #path('newsletter/success/', views.newsletter_success, name='newsletter_success'),
    # Inscription et connexion
    path('inscription/', views.InscriptionView.as_view(), name='inscription'),
    path('connexion/', views.connexion, name='connexion'),
    path('deconnexion/', views.deconnexion, name='deconnexion'),
    path('password-reset/', include('django.contrib.auth.urls')),
    
    # Dashboards
    path('dashboard/admin/', views.dashboard_admin, name='dashboard_admin'),
    path('dashboard/serveur/', views.dashboard_serveur, name='dashboard_serveur'),
    path('dashboard/gerant/', views.dashboard_gerant, name='dashboard_gerant'),
    path('dashboard/client/', views.dashboard_client, name='dashboard_client'),
    path('commande/<int:commande_id>/changer-statut/', views.changer_statut_commande, name='changer_statut_commande'),
]