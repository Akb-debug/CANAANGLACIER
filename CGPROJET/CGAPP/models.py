from django.db import models
from django.contrib.auth.models import AbstractUser
from django.templatetags.static import static

# -------------------- UTILISATEUR --------------------
class Utilisateur(AbstractUser):
    ROLE_CHOICES = (
        ('client', 'Client'),
        ('admin', 'Admin'),
        ('serveur', 'Serveur'),
        ('gerant', 'Gérant'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    telephone = models.CharField(max_length=15, blank=True, null=True)

    class Meta:
        verbose_name = "Utilisateur"


# -------------------- ROLES SPÉCIFIQUES --------------------
class Gerant(models.Model):
    utilisateur = models.OneToOneField(Utilisateur, on_delete=models.CASCADE)

    def __str__(self):
        return self.utilisateur.username


class Client(models.Model):
    utilisateur = models.OneToOneField(Utilisateur, on_delete=models.CASCADE)

    def __str__(self):
        return self.utilisateur.username


class Serveur(models.Model):
    utilisateur = models.OneToOneField(Utilisateur, on_delete=models.CASCADE)

    def __str__(self):
        return self.utilisateur.username


class Admin(models.Model):
    utilisateur = models.OneToOneField(Utilisateur, on_delete=models.CASCADE)

    def __str__(self):
        return self.utilisateur.username



# -------------------- CATEGORIE --------------------

class Categorie(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    slug = models.SlugField(max_length=100, unique=True)

    def __str__(self):
        return self.nom
    @property
    def image_url(self):
        """
        Retourne l'URL de l'image si elle existe, sinon un placeholder statique.
        """
        if self.image:
            return self.image.url
        return static('image/image.jpg')  

# -------------------- PRODUITS --------------------
class Produit(models.Model):
    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    quantite_disponible = models.PositiveIntegerField()
    image = models.ImageField(upload_to='produits/', blank=True, null=True)
    gerant = models.ForeignKey(Gerant, on_delete=models.CASCADE, related_name='produits')
    categorie = models.ForeignKey(Categorie, on_delete=models.SET_NULL, null=True, blank=True, related_name='produits')

    def __str__(self):
        return self.nom



# # -------------------- PANIER --------------------
# class Panier(models.Model):
#     client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True, blank=True)
#     date_creation = models.DateTimeField(auto_now_add=True)
#     session_id = models.CharField(max_length=100, null=True, blank=True)  # Pour suivre les utilisateurs anonymes
#     produits = models.ManyToManyField(Produit, through='Commande')

#     def __str__(self):
#         return f"Panier de {self.client.utilisateur.username}"


# # -------------------- COMMANDER --------------------
# class Commande(models.Model):
#     panier = models.ForeignKey(Panier, on_delete=models.CASCADE)
#     produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
#     quantite = models.PositiveIntegerField()
#     date_commande = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.quantite} x {self.produit.nom}"

class Panier(models.Model):
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100, null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)

class LignePanier(models.Model):
    panier = models.ForeignKey(Panier, on_delete=models.CASCADE, related_name='lignes')
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
    quantite = models.PositiveIntegerField(default=1)

class AdresseLivraison(models.Model):
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)
    rue = models.CharField(max_length=255)
    ville = models.CharField(max_length=100)
    code_postal = models.CharField(max_length=20)
    pays = models.CharField(max_length=100)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.rue}, {self.ville} {self.code_postal}, {self.pays}"

class Coupon(models.Model):
    code = models.CharField(max_length=20, unique=True)
    reduction = models.DecimalField(max_digits=5, decimal_places=2)
    actif = models.BooleanField(default=True)
    date_expiration = models.DateField()

    def __str__(self):
        return self.code

class Commande(models.Model):
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)
    date_creation = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    adresse_livraison = models.ForeignKey(AdresseLivraison, on_delete=models.SET_NULL, null=True)
    methode_paiement = models.CharField(max_length=50)
    statut = models.CharField(max_length=20, default='en_attente')
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Commande #{self.id} - {self.utilisateur.username}"

class LigneCommande(models.Model):
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name='lignes')
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
    quantite = models.PositiveIntegerField(default=1)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.produit.nom} x{self.quantite}"
    
    @property
    def sous_total(self):
        return self.quantite * self.prix_unitaire
# -------------------- PAIEMENT --------------------
class Paiement(models.Model):
    commande = models.OneToOneField(Commande, on_delete=models.CASCADE)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    date_paiement = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=20, default='en attente')

    def __str__(self):
        return f"Paiement de {self.montant} FCFA"


# -------------------- ABONNEMENT --------------------
class AbonnementNewsletter(models.Model):
    email = models.EmailField(unique=True)
    date_abonnement = models.DateTimeField(auto_now_add=True)
    actif = models.BooleanField(default=True)

    def __str__(self):
        return self.email



# -------------------- CONTACT --------------------
class Contact(models.Model):
    nom = models.CharField(max_length=100)
    email = models.EmailField()
    sujet = models.CharField(max_length=200)
    message = models.TextField()
    date_contact = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nom} - {self.sujet}"


# -------------------- HISTORIQUE DES ACTIONS --------------------
class HistoriqueAction(models.Model):
    TYPE_ACTION_CHOICES = [
        ('creation', 'Création'),
        ('modification', 'Modification'),
        ('suppression', 'Suppression'),
        ('connexion', 'Connexion'),
        ('commande_statut', 'Changement statut commande'),
        ('produit_ajout', 'Ajout produit'),
        ('produit_modif', 'Modification produit'),
        ('produit_suppr', 'Suppression produit'),
        ('utilisateur_creation', 'Création utilisateur'),
        ('utilisateur_suspension', 'Suspension utilisateur'),
        ('configuration', 'Modification configuration'),
    ]
    
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='actions')
    type_action = models.CharField(max_length=25, choices=TYPE_ACTION_CHOICES)
    description = models.TextField()
    objet_concerne = models.CharField(max_length=100, blank=True, null=True)  # Ex: "Commande #123", "Produit Glace Vanille"
    objet_id = models.PositiveIntegerField(blank=True, null=True)  # ID de l'objet concerné
    details_supplementaires = models.JSONField(blank=True, null=True)  # Données supplémentaires
    adresse_ip = models.GenericIPAddressField(blank=True, null=True)
    date_action = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Historique d'action"
        verbose_name_plural = "Historique des actions"
        ordering = ['-date_action']
    
    def __str__(self):
        return f"{self.utilisateur.username} - {self.get_type_action_display()} - {self.date_action.strftime('%d/%m/%Y %H:%M')}"


# -------------------- NOTIFICATIONS --------------------
class Notification(models.Model):
    TYPE_NOTIFICATION_CHOICES = [
        ('commande_confirmee', 'Commande confirmée'),
        ('commande_preparation', 'Commande en préparation'),
        ('commande_livraison', 'Commande en livraison'),
        ('commande_livree', 'Commande livrée'),
        ('commande_annulee', 'Commande annulée'),
        ('produit_stock_bas', 'Stock produit bas'),
        ('nouveau_message', 'Nouveau message contact'),
    ]
    
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='notifications')
    type_notification = models.CharField(max_length=25, choices=TYPE_NOTIFICATION_CHOICES)
    titre = models.CharField(max_length=200)
    message = models.TextField()
    lue = models.BooleanField(default=False)
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE, blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Notification"
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"{self.utilisateur.username} - {self.titre}"
