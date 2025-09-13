from django.db import models
from django.contrib.auth.models import AbstractUser
from django.templatetags.static import static
from django.utils.text import slugify
from django.core.validators import MinValueValidator
from decimal import Decimal, ROUND_HALF_UP
from django.db import models
from django.core.validators import RegexValidator, EmailValidator

# -------------------- UTILISATEUR --------------------
class Utilisateur(AbstractUser):
    ROLE_CHOICES = (
        ('client', 'Client'),
        ('admin', 'Admin'),
        ('serveur', 'Serveur'),
        ('gerant', 'Gérant'),
        ('livreur', 'Livreur'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    telephone = models.CharField(max_length=15, blank=True, null=True)

    class Meta:
        verbose_name = "Utilisateur"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Créer le profil spécifique selon le rôle
        if is_new:
            self.create_profile_based_on_role()

    def create_profile_based_on_role(self):
        """Crée le profil spécifique selon le rôle de l'utilisateur"""
        if self.role == 'livreur':
            Livreur.objects.get_or_create(utilisateur=self)
        elif self.role == 'serveur':
            Serveur.objects.get_or_create(utilisateur=self)
        elif self.role == 'gerant':
            Gerant.objects.get_or_create(utilisateur=self)
        elif self.role == 'admin':
            Admin.objects.get_or_create(utilisateur=self)
        elif self.role == 'client':
            Client.objects.get_or_create(utilisateur=self)



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
    
class Livreur(models.Model):
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

    @property
    def total(self):
        """Somme totale du panier"""
        total = Decimal('0')
        for ligne in self.lignes.all():
            total += ligne.total  # ✅ utilise la propriété total de LignePanier
        return total


class LignePanier(models.Model):
    panier = models.ForeignKey(Panier, on_delete=models.CASCADE, related_name='lignes')
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
    quantite = models.PositiveIntegerField(default=1)

    @property
    def total(self):
        """Sous-total pour cette ligne du panier"""
        return self.produit.prix * self.quantite  # ✅ simple et direct

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

     # Constantes de statut
    STATUT_EN_ATTENTE = 'en_attente'
    STATUT_TRAITEMENT = 'en_traitement'
    STATUT_EXPEDIEE = 'expediee'
    STATUT_LIVREE = 'livree'
    STATUT_ANNULEE = 'annulee'

      
    STATUT_CHOICES = [
        (STATUT_EN_ATTENTE, 'En attente'),
        (STATUT_TRAITEMENT, 'En traitement'),
        (STATUT_EXPEDIEE, 'Expédiée'),
        (STATUT_LIVREE, 'Livrée'),
        (STATUT_ANNULEE, 'Annulée'),
    ]
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)
    date_creation = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    adresse_livraison = models.ForeignKey(AdresseLivraison, on_delete=models.SET_NULL, null=True,  blank=True)
    methode_paiement = models.CharField(max_length=50)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default=STATUT_EN_ATTENTE)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    date_modification = models.DateTimeField(auto_now=True)
    date_livraison = models.DateTimeField(null=True, blank=True)
    livreur = models.ForeignKey(Livreur, on_delete=models.SET_NULL, null=True, blank=True)
        

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


class Paiement(models.Model):
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('payé', 'Payé'),
        ('échoué', 'Échoué'),
        ('annulé', 'Annulé'),
    ]
    
    commande = models.OneToOneField(Commande, on_delete=models.CASCADE)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    date_paiement = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    reference = models.CharField(max_length=100, blank=True, null=True)

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


#------------------------------Gestion client --------------------------------

class PreferenceAlimentaire(models.Model):
    """Modèle pour stocker les préférences et allergies des clients"""
    TYPE_CHOICES = [
        ('allergie', 'Allergie'),
        ('intolerance', 'Intolérance'),
        ('preference', 'Préférence alimentaire'),
        ('regime', 'Régime spécial'),
        ('autre', 'Autre'),
    ]
    
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='preferences_alimentaires')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    description = models.TextField(verbose_name="Description de la préférence/allergie")
    severite = models.CharField(max_length=20, choices=[
        ('leger', 'Léger'),
        ('modere', 'Modéré'),
        ('severe', 'Sévère'),
        ('critique', 'Critique')
    ], default='modere')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    est_actif = models.BooleanField(default=True, verbose_name="Actif")

    class Meta:
        verbose_name = "Préférence alimentaire"
        verbose_name_plural = "Préférences alimentaires"
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.utilisateur.username} - {self.get_type_display()}"

class AvisProduit(models.Model):
    """Modèle pour les avis et remarques sur les produits"""
    NOTE_CHOICES = [
        (1, '★☆☆☆☆ - Très mauvais'),
        (2, '★★☆☆☆ - Mauvais'),
        (3, '★★★☆☆ - Moyen'),
        (4, '★★★★☆ - Bon'),
        (5, '★★★★★ - Excellent'),
    ]
    
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='avis_produits')
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name='avis')
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name='avis', null=True, blank=True)
    note = models.PositiveSmallIntegerField(choices=NOTE_CHOICES, verbose_name="Note")
    titre = models.CharField(max_length=100, verbose_name="Titre de l'avis")
    commentaire = models.TextField(verbose_name="Votre commentaire")
    remarques = models.TextField(blank=True, verbose_name="Remarques supplémentaires")
    est_approuve = models.BooleanField(default=False, verbose_name="Avis approuvé")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Avis produit"
        verbose_name_plural = "Avis produits"
        ordering = ['-date_creation']
        unique_together = ['utilisateur', 'produit', 'commande']

    def __str__(self):
        return f"Avis de {self.utilisateur.username} sur {self.produit.nom}"

class MediaAvis(models.Model):
    """Modèle pour les médias associés aux avis (photos)"""
    avis = models.ForeignKey(AvisProduit, on_delete=models.CASCADE, related_name='medias')
    image = models.ImageField(upload_to='avis/', verbose_name="Image")
    legende = models.CharField(max_length=200, blank=True, verbose_name="Légende")
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Média d'avis"
        verbose_name_plural = "Médias d'avis"

    def __str__(self):
        return f"Media pour {self.avis}"

class ReponseAvis(models.Model):
    """Modèle pour les réponses aux avis (par le gérant ou l'admin)"""
    avis = models.ForeignKey(AvisProduit, on_delete=models.CASCADE, related_name='reponses')
    auteur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, verbose_name="Auteur de la réponse")
    message = models.TextField(verbose_name="Réponse")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Réponse à l'avis"
        verbose_name_plural = "Réponses aux avis"
        ordering = ['date_creation']

    def __str__(self):
        return f"Réponse à l'avis #{self.avis.id}"
    

class NotationCommande(models.Model):
    """Modèle pour noter une commande complète"""
    NOTE_CHOICES = [
        (1, '★☆☆☆☆ - Très mauvais'),
        (2, '★★☆☆☆ - Mauvais'),
        (3, '★★★☆☆ - Moyen'),
        (4, '★★★★☆ - Bon'),
        (5, '★★★★★ - Excellent'),
    ]
    
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='notations_commandes')
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name='notations')
    note_globale = models.PositiveSmallIntegerField(choices=NOTE_CHOICES, verbose_name="Note globale")
    note_livraison = models.PositiveSmallIntegerField(choices=NOTE_CHOICES, verbose_name="Note livraison")
    note_emballage = models.PositiveSmallIntegerField(choices=NOTE_CHOICES, verbose_name="Note emballage")
    commentaire = models.TextField(verbose_name="Commentaire sur la commande")
    remarques = models.TextField(blank=True, verbose_name="Remarques supplémentaires")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Notation de commande"
        verbose_name_plural = "Notations de commandes"
        unique_together = ['utilisateur', 'commande']

    def __str__(self):
        return f"Notation de {self.utilisateur.username} pour commande #{self.commande.id}"

class MediaNotationCommande(models.Model):
    """Médias pour les notations de commande"""
    notation = models.ForeignKey(NotationCommande, on_delete=models.CASCADE, related_name='medias')
    image = models.ImageField(upload_to='notations-commandes/', verbose_name="Image")
    legende = models.CharField(max_length=200, blank=True, verbose_name="Légende")
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Média de notation"
        verbose_name_plural = "Médias de notations"

class ProblemeCommande(models.Model):
    """Modèle pour signaler des problèmes sur une commande"""
    TYPE_PROBLEME_CHOICES = [
        ('produit_manquant', 'Produit manquant'),
        ('produit_abime', 'Produit abîmé'),
        ('produit_erreur', 'Mauvais produit reçu'),
        ('emballage', 'Problème d\'emballage'),
        ('livraison', 'Problème de livraison'),
        ('qualite', 'Problème de qualité'),
        ('autre', 'Autre problème'),
    ]
    
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='problemes_commandes')
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name='problemes')
    type_probleme = models.CharField(max_length=20, choices=TYPE_PROBLEME_CHOICES, verbose_name="Type de problème")
    description = models.TextField(verbose_name="Description du problème")
    produit_concerne = models.ForeignKey(Produit, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Produit concerné")
    photos = models.ManyToManyField(MediaNotationCommande, blank=True, verbose_name="Photos")
    resolu = models.BooleanField(default=False, verbose_name="Problème résolu")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_resolution = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Problème de commande"
        verbose_name_plural = "Problèmes de commandes"

    def __str__(self):
        return f"Problème {self.get_type_probleme_display()} - Commande #{self.commande.id}"