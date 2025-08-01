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

class Commande(models.Model):
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)
    date_commande = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=8, decimal_places=2)
    statut = models.CharField(max_length=20, default='En attente')


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
