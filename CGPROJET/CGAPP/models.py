from django.db import models
from django.contrib.auth.models import AbstractUser
from django.templatetags.static import static
from django.utils.text import slugify
from django.core.validators import MinValueValidator
from decimal import Decimal, ROUND_HALF_UP

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
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    ordre_affichage = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ['ordre_affichage', 'nom']

    def __str__(self):
        return self.nom

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nom)
        super().save(*args, **kwargs)

    @property
    def produits_actifs(self):
        return self.produits.filter(quantite_disponible__gt=0)  
    
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
    # Informations de base
    nom = models.CharField(max_length=100, verbose_name="Nom du produit")
    description = models.CharField(max_length=200, verbose_name="Description courte", blank=True)
    description_longue = models.TextField(verbose_name="Description détaillée", blank=True)
    
    # Prix et disponibilité
    prix = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0)],
        verbose_name="Prix (FCFA)"
    )
    promotion = models.PositiveIntegerField(
        default=0,
        verbose_name="Pourcentage de réduction",
        help_text="Pourcentage de réduction (0-100)"
    )
    quantite_disponible = models.PositiveIntegerField(
        default=0,
        verbose_name="Quantité en stock"
    )
    
    # Images
    image = models.ImageField(
        upload_to='produits/',
        verbose_name="Image principale"
    )
    
    # Relations
    categorie = models.ForeignKey(
        'Categorie',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='produits',
        verbose_name="Catégorie"
    )
    gerant = models.ForeignKey(
        'Gerant',
        on_delete=models.CASCADE,
        related_name='produits',
        verbose_name="Gérant responsable"
    )
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    est_populaire = models.BooleanField(
        default=False,
        verbose_name="Produit populaire",
        help_text="Cochez pour afficher ce produit comme populaire"
    )
    
    # Caractéristiques
    ingredients = models.TextField(blank=True, verbose_name="Liste des ingrédients")
    allergenes = models.CharField(max_length=200, blank=True, verbose_name="Allergènes")
    poids_net = models.CharField(max_length=20, blank=True, verbose_name="Poids net")
    conseil_conservation = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Conseil de conservation",
        default="À conserver à -18°C"
    )

    class Meta:
        verbose_name = "Produit"
        verbose_name_plural = "Produits"
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['nom']),
            models.Index(fields=['categorie']),
            models.Index(fields=['prix']),
            models.Index(fields=['est_populaire']),
        ]

    def __str__(self):
        return self.nom

    @property
    def ancien_prix(self):
        """Retourne le prix avant promotion si applicable"""
        if self.promotion > 0:
            # Convertir les valeurs en Decimal
            promotion_decimal = Decimal(self.promotion) / Decimal('100')
            ancien = self.prix / (Decimal('1') - promotion_decimal)
            # Arrondir à 2 décimales comme un prix
            return ancien.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return None

    @property
    def en_stock(self):
        """Retourne True si le produit est en stock"""
        return self.quantite_disponible > 0

    @property
    def stock_faible(self):
        """Retourne True si le stock est faible (moins de 5 unités)"""
        return 0 < self.quantite_disponible < 5

    def get_statut_stock(self):
        """Retourne le statut du stock sous forme de texte"""
        if not self.en_stock:
            return "Rupture de stock"
        if self.stock_faible:
            return f"Plus que {self.quantite_disponible} en stock"
        return "En stock"


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
from django.db import models
from django.core.validators import RegexValidator, EmailValidator

class ContactMessage(models.Model):
    SUJET_CHOICES = [
        ('commande', 'Problème ou question sur une commande'),
        ('livraison', 'Problème ou retard de livraison'),
        ('produit', 'Question sur un produit (goût, disponibilité, allergènes, etc.)'),
        ('paiement', 'Problème de paiement'),
        ('partenariat', 'Demande de partenariat ou collaboration'),
        ('suggestion', 'Suggestion ou amélioration'),
        ('autre', 'Autre demande'),
    ]

    nom = models.CharField(max_length=100, verbose_name="Nom")
    prenom = models.CharField(max_length=100, verbose_name="Prénom", blank=True, null=True)
    email = models.EmailField(validators=[EmailValidator()], verbose_name="Email")
    telephone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[RegexValidator(regex=r'^\+?[0-9\s\-]+$', message="Numéro de téléphone invalide")]
    )
    sujet = models.CharField(max_length=50, choices=SUJET_CHOICES, verbose_name="Sujet")
    message = models.TextField(verbose_name="Message")
    date_soumission = models.DateTimeField(auto_now_add=True, verbose_name="Date de soumission")
    traite = models.BooleanField(default=False, verbose_name="Traité")

    class Meta:
        verbose_name = "Message de contact"
        verbose_name_plural = "Messages de contact"
        ordering = ['-date_soumission']

    def __str__(self):
        return f"{self.nom} - {self.get_sujet_display()} - {self.date_soumission.strftime('%d/%m/%Y')}"



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
