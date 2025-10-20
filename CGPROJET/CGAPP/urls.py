from django.urls import path, include
from . import views
from .views import CustomPasswordChangeView, DeleteAccountView, deconnexion
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
    path('produit/<int:pk>/', views.ProduitDetailView.as_view(), name='produit_detail'),
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
    path("commande/finaliser/", views.finaliser_commande, name="finaliser_commande"),
    path("commande/<int:pk>/", views.commande_detail, name="commande_detail"), 
    path('commande/<int:commande_id>/paiement/', views.processus_paiement, name='processus_paiement'),
   
   
   # path('commande/<int:commande_id>/traiter-paiement/', views.traiter_paiement, name='traiter_paiement'),
    path('commande/<int:commande_id>/annuler-paiement/', views.annuler_paiement, name='annuler_paiement'),

    # Page de paiement (checkout)
    #path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    # Compte
    path('mon-compte/', views.mon_compte, name='mon_compte'),
    path('compte/', views.ProfileView.as_view(), name='profile'),
    path('changer-mot-de-passe/', CustomPasswordChangeView.as_view(), name='password_change'),
    path('supprimer-compte/', DeleteAccountView.as_view(), name='delete_account'),
    path('deconnexion/', views.deconnexion, name='deconnexion'),
    
    # Dashboards
    path('dashboard/admin/', views.dashboard_admin, name='dashboard_admin'),
    path('dashboard/serveur/', views.dashboard_serveur, name='dashboard_serveur'),
    # path('dashboard/gerant/', views.dashboard_gerant, name='dashboard_gerant'),
    path('dashboard/client/', views.dashboard_client, name='dashboard_client'),
    
    # Actions pour les dashboards
    path('commande/changer-statut/<int:commande_id>/', views.changer_statut_commande, name='changer_statut_commande'),
    
    # Gestion des utilisateurs    # Audit et sécurité
    path('gestion/audit-securite/', views.audit_securite, name='audit_securite'),
    path('gestion/creer-sauvegarde/', views.creer_sauvegarde, name='creer_sauvegarde'),
    path('gestion/telecharger-sauvegarde/<int:sauvegarde_id>/', views.telecharger_sauvegarde, name='telecharger_sauvegarde'),
    path('gestion/configurer-sauvegarde-auto/', views.configurer_sauvegarde_auto, name='configurer_sauvegarde_auto'),
    
    # ===== URLS GÉRANT =====
    # Gérant - Gestion financière
    path('gerant/gestion-financiere/', views.gestion_financiere_gerant, name='gestion_financiere_gerant'),
    # Gérant - Gestion avancée des stocks
    path('gerant/gestion-stocks-avancee/', views.gestion_stocks_avancee, name='gestion_stocks_avancee'),
    # Gérant - Analyse des performances
    path('gerant/analyse-performances/', views.analyse_performances_gerant, name='analyse_performances_gerant'),
    # Gérant - Gestion avancée des serveurs
    path('gerant/gestion-serveurs-avancee/', views.gestion_serveurs_avancee, name='gestion_serveurs_avancee'),
    path('gerant/planifier-tache/', views.planifier_tache, name='planifier_tache'),
    path('gerant/evaluer-serveur/', views.evaluer_serveur, name='evaluer_serveur'),
    # Gérant - Communication et notifications
    path('gerant/communication-notifications/', views.communication_notifications, name='communication_notifications'),
    path('gerant/envoyer-notification-push/', views.envoyer_notification_push, name='envoyer_notification_push'),
    path('gerant/envoyer-message/', views.envoyer_message, name='envoyer_message'),
    path('gestion/categories/ajouter/', views.ajouter_categorie, name='ajouter_categorie'),
    path('gestion/categories/modifier/<int:categorie_id>/', views.modifier_categorie, name='modifier_categorie'),
    path('gestion/categories/supprimer/<int:categorie_id>/', views.supprimer_categorie, name='supprimer_categorie'),
    path('gestion/coupons/', views.gestion_coupons, name='gestion_coupons'),
    # path('gestion/coupons/ajouter/', views.ajouter_coupon, name='ajouter_coupon'),
    path('gestion/ajouter-coupon/', views.ajouter_coupon, name='ajouter_coupon'),
    path('gestion/creer-gerant/', views.creer_gerant, name='creer_gerant'),
    # URL déplacée vers la section gérant
    path('gerant/creer-serveur/', views.creer_serveur, name='creer_serveur_gerant'),
    path('gestion/liste-utilisateurs/', views.liste_utilisateurs, name='liste_utilisateurs'),
    path('gestion/categories/', views.gestion_categories, name='gestion_categories'),
    path('gestion/coupons/modifier/<int:coupon_id>/', views.modifier_coupon, name='modifier_coupon'),
    path('gestion/coupons/supprimer/<int:coupon_id>/', views.supprimer_coupon, name='supprimer_coupon'),
    path('gestion/rapports/', views.rapports_admin, name='rapports_admin'),
    path('gestion/parametres/', views.parametres_systeme, name='parametres_systeme'),
    path('gestion/parametres/ajouter/', views.ajouter_parametre, name='ajouter_parametre'),
    path('gestion/parametres/modifier/<int:parametre_id>/', views.modifier_parametre, name='modifier_parametre'),
    path('gestion/stocks/ajuster/', views.ajuster_stock, name='ajuster_stock'),
    path('gestion/journal-connexions/', views.journal_connexions, name='journal_connexions'),
    path('gestion/sauvegardes/', views.sauvegardes_systeme, name='sauvegardes_systeme'),
    path('gestion/historique/actions/', views.historique_actions_gestion, name='historique_actions_gerant'),
    
    # URLs manquantes pour le dashboard admin
    path('gestion/utilisateurs/', views.gestion_utilisateurs, name='gestion_utilisateurs'),
    path('gestion/commandes/', views.gestion_commandes_admin, name='gestion_commandes_admin'),
    path('gestion/statistiques/', views.statistiques_admin, name='statistiques_admin'),
    
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
    
    path('commande/<int:commande_id>/changer-statut-dahboard/', views.changer_statut, name='changer_statut'),

    #Gestion serveur

      # Interface serveur
    path('serveur/commande/nouvelle/', views.nouvelle_commande_serveur, name='nouvelle_commande_serveur'),
    path('serveur/commande/<int:commande_id>/ajouter-produit/', views.ajouter_produit_commande, name='ajouter_produit_commande'),
    path('serveur/commande/<int:commande_id>/modifier-quantite/<int:ligne_id>/', views.modifier_quantite, name='modifier_quantite_serveur'),
    path('serveur/commande/<int:commande_id>/supprimer-produit/<int:ligne_id>/', views.supprimer_produit, name='supprimer_produit_serveur'),
    path('serveur/commande/<int:commande_id>/finaliser/', views.finaliser_commande_serveur, name='finaliser_commande_serveur'),
    path('serveur/commande/<int:commande_id>/paiement/', views.paiement_commande_serveur, name='paiement_commande_serveur'),
    path('serveur/commande/<int:commande_id>/recu/', views.generer_recu, name='generer_recu_serveur'),
    path('serveur/commande/<int:commande_id>/annuler/', views.annuler_commande_serveur, name='annuler_commande_serveur'),
     path('serveur/produits/', views.ListeProduitsServeurView.as_view(), name='liste_produits_serveur'),
    
    # Gestion des commandes
    path('commandes/en-attente/', views.commandes_en_attente, name='commandes_en_attente'),
    path('commandes/<int:commande_id>/prendre-en-charge/', views.prendre_en_charge_commande, name='prendre_en_charge_commande'),
    path('commandes/serveur/<int:commande_id>/', views.detail_commande, name='detail_commande'),
    path('commande/<int:commande_id>/changer-statut/', views.changer_statut_commande, name='changer_statut_commande'),
    path('serveur/commandes-livrees/', views.CommandesLivreesServeurView.as_view(), name='commandes_livrees_serveur'),
    # path('commande/<int:commande_id>/', views.detail_commande, name='detail_commande'),
    path('commandes-en-cours/', views.commandes_en_cours, name='commandes_en_cours'),

    #Gestion par client
    path('client/produit/<int:produit_id>/', views.detail_produit_client, name='detail_produit_client'),
    path('mon-compte/historique/', views.historique_client, name='historique_client'),
    #Avis client
     # URLs pour le système d'avis et préférences
    path('mon-compte/avis/', views.tableau_de_bord_avis, name='tableau_avis'),
    path('mon-compte/preferences/', views.gerer_preferences, name='gerer_preferences'),
    path('mon-compte/preferences/modifier/<int:preference_id>/', views.modifier_preference, name='modifier_preference'),
    path('mon-compte/preferences/supprimer/<int:preference_id>/', views.supprimer_preference, name='supprimer_preference'),
    path('mon-compte/avis/laisser/', views.laisser_avis, name='laisser_avis'),
    path('mon-compte/avis/laisser/commande/<int:commande_id>/', views.laisser_avis, name='laisser_avis_commande'),
    path('mon-compte/avis/laisser/produit/<int:produit_id>/', views.laisser_avis, name='laisser_avis_produit'),
    path('mon-compte/mes-avis/', views.mes_avis, name='mes_avis'),
    path('mon-compte/avis/modifier/<int:avis_id>/', views.modifier_avis, name='modifier_avis'),
    path('mon-compte/avis/supprimer/<int:avis_id>/', views.supprimer_avis, name='supprimer_avis'),

     # URLs pour la notation des commandes
    path('noter-commande/<int:commande_id>/', views.noter_commande_complete, name='noter_commande'),
    path('notation-commande/<int:notation_id>/', views.detail_notation_commande, name='detail_notation_commande'),
    path('signaler-probleme/<int:commande_id>/', views.signaler_probleme, name='signaler_probleme'),
    path('mes-notations-commandes/', views.mes_notations_commandes, name='mes_notations_commandes'),
    #Urls pour le livreur
    path('dashboard/', views.dashboard_livreur, name='dashboard_livreur'),
    path('commandes/a-livrer/', views.commandes_a_livrer, name='commandes_a_livrer'),
    path('commandes/livrees/', views.commandes_livrees, name='commandes_livrees'),
    path('commande/livreur/<int:commande_id>/', views.detail_commande_livreur, name='detail_commande_livreur'),
    path('historique-actions/livreur', views.historique_actions, name='historique_actions'),
    path('profil/', views.profil_livreur, name='profil_livreur'),
    path('commande/<int:commande_id>/livrer/', views.changer_statut_commande_livreur, name='livrer_commande'),
    #Paiement avec cinetpay
    path("paiement/<int:commande_id>/traiter/", views.traiter_paiement, name="traiter_paiement"),
    path("cinetpay/notify/", views.cinetpay_notify, name="cinetpay_notify"),

    #Gestion livreur par admin
    path('gestion_admin/livreurs/ajouter/', views.ajouter_livreur, name='ajouter_livreur'),
    
    
    # ==================== URLs POUR LA GESTION DES UTILISATEURS PAR L'ADMIN ====================
    
    
    # URLs pour les Gérants
    path('gestion/gerant/<int:pk>/modifier/', views.modifier_gerant, name='modifier_gerant'),
    path('gestion/gerant/<int:pk>/supprimer/', views.supprimer_gerant, name='supprimer_gerant'),
    
    # URLs pour les Serveurs
    path('gestion_admin/serveurs/<int:pk>/modifier/', views.modifier_serveur, name='modifier_serveur'),
    path('gestion_admin/serveurs/<int:pk>/supprimer/', views.supprimer_serveur, name='supprimer_serveur'),
    
    # URLs pour les Livreurs
    path('gestion_admin/livreurs/<int:pk>/modifier/', views.modifier_livreur, name='modifier_livreur'),
    path('gestion_admin/livreurs/<int:pk>/supprimer/', views.supprimer_livreur, name='supprimer_livreur'),
    
    # URLs pour les Clients
    path('gestion_admin/clients/<int:pk>/modifier/', views.modifier_client, name='modifier_client'),
    path('gestion_admin/clients/<int:pk>/supprimer/', views.supprimer_client, name='supprimer_client'),
    path('stocks/produit/<int:produit_id>/', views.get_produit_details, name='get_produit_details'),

    path('gerant/dashboard/', views.dashboard_gerant, name='dashboard_gerant'),
path('gerant/statistiques-ventes/', views.statistiques_ventes, name='statistiques_ventes'),

   
]