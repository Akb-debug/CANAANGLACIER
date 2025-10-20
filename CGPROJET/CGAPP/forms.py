from django import forms
from django.core.validators import RegexValidator,validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import *

from django.contrib.auth import get_user_model

User = get_user_model()

# ==================== FORMULAIRES ADMIN ====================

class CategorieForm(forms.ModelForm):
    class Meta:
        model = Categorie
        fields = ['nom', 'description', 'image', 'ordre_affichage']
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de la catégorie'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description de la catégorie'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'ordre_affichage': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': 'Ordre d\'affichage'
            })
        }

class CouponModelForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = ['code', 'type_reduction', 'valeur', 'date_debut', 'date_fin', 'usage_max', 'actif']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Code du coupon (ex: NOEL2024)'
            }),
            'type_reduction': forms.Select(attrs={
                'class': 'form-select'
            }),
            'valeur': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'date_debut': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'date_fin': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'usage_max': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Nombre maximum d\'utilisations'
            }),
            'actif': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

class ParametreSystemeForm(forms.ModelForm):
    class Meta:
        model = ParametreSysteme
        fields = ['cle', 'valeur', 'description']
        widgets = {
            'cle': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Clé du paramètre'
            }),
            'valeur': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Valeur du paramètre'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description du paramètre'
            })
        }

class ProfilForm(forms.ModelForm):
    telephone = forms.CharField(max_length=20, required=False, label='Téléphone')

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'telephone']


class InscriptionForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ajout des classes CSS aux champs
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Nom d\'utilisateur'
        })
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'email@exemple.com'
        })
        self.fields['telephone'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': '90 12 34 56'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': '••••••••'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': '••••••••'
        })
    
    telephone = forms.CharField(
        max_length=15,
        required=True,
        help_text='Format: 90 12 34 56',
        validators=[RegexValidator(
            regex=r'^(90|91|92|93|96|97|98|99)[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$',
            message='Numéro togolais invalide'
        )],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '90 12 34 56'
        })
    )
    
    class Meta:
        model = Utilisateur
        fields = ('username', 'email', 'telephone', 'password1', 'password2')

class ConnexionForm(forms.Form):
    username = forms.CharField(
        label="Nom d'utilisateur ou Email",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom d\'utilisateur ou email'
        })
    )
    password = forms.CharField(
        label="Mot de passe", 
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••'
        })
    )

class CommandeForm(forms.Form):
    # Section informations personnelles
    nom = forms.CharField(
        label="Nom",
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'autocomplete': 'family-name'
        }),
        validators=[
            RegexValidator(
                regex=r'^[a-zA-ZÀ-ÿ\s\-]{2,100}$',
                message='Le nom ne doit contenir que des lettres et espaces (2-100 caractères)'
            )
        ]
    )
    
    prenom = forms.CharField(
        label="Prénom",
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'autocomplete': 'given-name'
        }),
        validators=[
            RegexValidator(
                regex=r'^[a-zA-ZÀ-ÿ\s\-]{2,100}$',
                message='Le prénom ne doit contenir que des lettres et espaces (2-100 caractères)'
            )
        ]
    )
    
    telephone = forms.CharField(
        label="Téléphone",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '90 12 34 56',
            'autocomplete': 'tel'
        }),
        validators=[
            RegexValidator(
                regex=r'^(90|91|92|93|96|97|98|99)[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$',
                message='Numéro togolais invalide (format: 90 12 34 56)'
            )
        ]
    )
    
    # Section adresse
    adresse = forms.CharField(
        label="Adresse complète",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'autocomplete': 'street-address',
            'placeholder': 'Rue, Quartier, Ville'
        }),
        max_length=200
    )
    
    ville = forms.CharField(
        label="Ville",
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'autocomplete': 'address-level2',
            'placeholder': 'Lomé'
        }),
        initial='Lomé'
    )
    
    # Section livraison
    MODE_LIVRAISON_CHOICES = [
        ('domicile', 'Livraison à domicile (+3 000 FCFA)'),
        ('relais', 'Point relais (gratuit)'),
        ('emporter', 'Retrait en boutique (gratuit)')
    ]
    
    mode_livraison = forms.ChoiceField(
        label="Mode de livraison",
        choices=MODE_LIVRAISON_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        }),
        initial='relais'
    )
    
    # Section paiement
    MODE_PAIEMENT_CHOICES = [
        ('tmoney', 'T-Money'),
        ('flooz', 'Flooz'),
        ('carte', 'Carte bancaire'),
        ('livraison', 'Paiement à la livraison')
    ]
    
    mode_paiement = forms.ChoiceField(
        label="Moyen de paiement",
        choices=MODE_PAIEMENT_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        }),
        initial='tmoney'
    )
    
    informations_complementaires = forms.CharField(
        label="Informations complémentaires (optionnel)",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Instructions spéciales pour la livraison...'
        }),
        max_length=500
    )
    
    conditions_acceptees = forms.BooleanField(
        label="J'accepte les conditions générales de vente",
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        error_messages={
            'required': 'Vous devez accepter les conditions générales'
        }
    )
    
    def clean(self):
        cleaned_data = super().clean()
        mode_livraison = cleaned_data.get('mode_livraison')
        mode_paiement = cleaned_data.get('mode_paiement')
        
        # Validation: Paiement à la livraison seulement pour retrait en boutique
        if mode_paiement == 'livraison' and mode_livraison != 'emporter':
            raise forms.ValidationError(
                "Le paiement à la livraison n'est disponible que pour le retrait en boutique."
            )
            
        # Normalisation du numéro de téléphone
        if 'telephone' in cleaned_data:
            tel = cleaned_data['telephone']
            tel = tel.replace(' ', '').replace('-', '')
            if len(tel) == 8:  # Format 90123456
                tel = f"{tel[:2]} {tel[2:4]} {tel[4:6]} {tel[6:8]}"
            cleaned_data['telephone'] = tel
            
        return cleaned_data
    


class NewsletterForm(forms.ModelForm):
    email = forms.EmailField(
        label="",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Entrez votre email pour nos offres exclusives',
            'aria-label': 'Adresse email pour newsletter'
        }),
        error_messages={
            'required': 'Veuillez entrer une adresse email valide',
            'invalid': 'Format d\'email invalide'
        }
    )
    
    class Meta:
        model = AbonnementNewsletter
        fields = ['email']
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        
        # Validation standard de l'email
        try:
            validate_email(email)
        except ValidationError:
            raise forms.ValidationError("Veuillez entrer une adresse email valide.")
        
        # Vérification si l'email est déjà inscrit et actif
        if AbonnementNewsletter.objects.filter(email=email, actif=True).exists():
            raise forms.ValidationError("Cet email est déjà inscrit à notre newsletter.")
            
        return email.lower()  # Normalisation en minuscules


# ==================== FORMULAIRES ADMIN ====================

class CreerGerantForm(UserCreationForm):
    """
    Formulaire pour que l'admin puisse créer un gérant
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ajout des classes CSS aux champs
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
        
        self.fields['username'].widget.attrs.update({
            'placeholder': 'Nom d\'utilisateur du gérant'
        })
        self.fields['email'].widget.attrs.update({
            'placeholder': 'email@exemple.com'
        })
        self.fields['first_name'].widget.attrs.update({
            'placeholder': 'Prénom'
        })
        self.fields['last_name'].widget.attrs.update({
            'placeholder': 'Nom de famille'
        })
        self.fields['telephone'].widget.attrs.update({
            'placeholder': '90 12 34 56'
        })
    
    first_name = forms.CharField(
        label="Prénom",
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Prénom'
        })
    )
    
    last_name = forms.CharField(
        label="Nom",
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom de famille'
        })
    )
    
    telephone = forms.CharField(
        label="Téléphone",
        max_length=15,
        required=True,
        help_text='Format: 90 12 34 56',
        validators=[RegexValidator(
            regex=r'^(90|91|92|93|96|97|98|99)[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$',
            message='Numéro togolais invalide'
        )],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '90 12 34 56'
        })
    )
    
    class Meta:
        model = Utilisateur
        fields = ('username', 'first_name', 'last_name', 'email', 'telephone', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'gerant'  # Définir le rôle comme gérant
        if commit:
            user.save()
            # # Créer l'instance Gerant associée
            # Gerant.objects.create(utilisateur=user)
        return user


class CreerServeurForm(UserCreationForm):
    """
    Formulaire pour que l'admin puisse créer un serveur
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ajout des classes CSS aux champs
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
        
        self.fields['username'].widget.attrs.update({
            'placeholder': 'Nom d\'utilisateur du serveur'
        })
        self.fields['email'].widget.attrs.update({
            'placeholder': 'email@exemple.com'
        })
        self.fields['first_name'].widget.attrs.update({
            'placeholder': 'Prénom'
        })
        self.fields['last_name'].widget.attrs.update({
            'placeholder': 'Nom de famille'
        })
        self.fields['telephone'].widget.attrs.update({
            'placeholder': '90 12 34 56'
        })
    
    first_name = forms.CharField(
        label="Prénom",
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Prénom'
        })
    )
    
    last_name = forms.CharField(
        label="Nom",
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom de famille'
        })
    )
    
    telephone = forms.CharField(
        label="Téléphone",
        max_length=15,
        required=True,
        help_text='Format: 90 12 34 56',
        validators=[RegexValidator(
            regex=r'^(90|91|92|93|96|97|98|99)[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$',
            message='Numéro togolais invalide'
        )],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '90 12 34 56'
        })
    )
    
    class Meta:
        model = Utilisateur
        fields = ('username', 'first_name', 'last_name', 'email', 'telephone', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'serveur'  # Définir le rôle comme serveur
        if commit:
            user.save()
            # Créer l'instance Serveur associée
            # Serveur.objects.create(utilisateur=user)
        return user


# ==================== FORMULAIRES GÉRANT ====================


class ProduitForm(forms.ModelForm):
    """
    Formulaire pour ajouter/modifier des produits - accessible aux admins et gérants
    """
    
    class Meta:
        model = Produit
        fields = [
            'nom', 'description', 'description_longue', 'prix', 'promotion',
            'quantite_disponible', 'categorie', 'image',
            'ingredients', 'allergenes', 'poids_net', 'conseil_conservation',
            'est_populaire'
        ]
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du produit'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description courte du produit'
            }),
            'description_longue': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Description détaillée du produit'
            }),
            'prix': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Prix'
            }),
            'promotion': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'placeholder': '0'
            }),
            'quantite_disponible': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '0'
            }),
            'categorie': forms.Select(attrs={
                'class': 'form-select'
            }),
           
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'ingredients': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Liste des ingrédients, séparés par des virgules'
            }),
            'allergenes': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Lait, œufs, fruits à coque...'
            }),
            'poids_net': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 500g, 1kg, 250ml...'
            }),
            'conseil_conservation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: À conserver à -18°C'
            }),
            'est_populaire': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'nom': 'Nom du produit',
            'description': 'Description courte',
            'description_longue': 'Description détaillée',
            'prix': 'Prix (FCFA)',
            'promotion': 'Pourcentage de réduction (%)',
            'quantite_disponible': 'Quantité en stock',
            'categorie': 'Catégorie',
            'image': 'Image principale',
            'ingredients': 'Liste des ingrédients',
            'allergenes': 'Allergènes',
            'poids_net': 'Poids net',
            'conseil_conservation': 'Conseil de conservation',
            'est_populaire': 'Produit populaire'
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Rendre certains champs facultatifs
        for field in ['description', 'description_longue', 'allergenes', 'poids_net', 
                     'ingredients', 'conseil_conservation', 'promotion', 'categorie']:
            self.fields[field].required = False
    
    def clean_prix(self):
        prix = self.cleaned_data.get('prix')
        if prix is not None and prix <= 0:
            raise forms.ValidationError("Le prix doit être supérieur à 0.")
        return prix
    
    def clean_promotion(self):
        promotion = self.cleaned_data.get('promotion') or 0
        if promotion < 0:
            raise forms.ValidationError("La promotion ne peut pas être négative.")
        if promotion > 100:
            raise forms.ValidationError("La promotion ne peut pas dépasser 100%.")
        return promotion
    
    def clean_quantite_disponible(self):
        quantite = self.cleaned_data.get('quantite_disponible')
        if quantite is not None and quantite < 0:
            raise forms.ValidationError("La quantité ne peut pas être négative.")
        return quantite
    
    def clean_gerant(self):
        gerant = self.cleaned_data.get('gerant')
        if self.user and hasattr(self.user, 'gerant'):
            # Pour les gérants, utiliser leur propre compte
            return self.user.gerant
        return gerant
    
#==================================Adresse==================================

class CoordonneesClientForm(forms.Form):
    nom = forms.CharField(
        max_length=100,
        label="Nom",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre nom'
        })
    )
    prenom = forms.CharField(
        max_length=100,
        label="Prénom",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre prénom'
        })
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@exemple.com'
        })
    )
    telephone = forms.CharField(
        max_length=20,
        label="Téléphone",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'XX XXX XXXX'
        })
    )

class LivraisonForm(forms.Form):
    MODE_LIVRAISON_CHOICES = [
        ('livraison', 'Livraison à domicile'),
        ('magasin', 'Retrait en magasin'),
    ]
    
    mode_livraison = forms.ChoiceField(
        choices=MODE_LIVRAISON_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'livraison-option'
        }),
        initial='livraison'
    )

class AdresseLivraisonForm(forms.ModelForm):
    class Meta:
        model = AdresseLivraison
        fields = ['rue', 'ville', 'code_postal', 'pays']
        widgets = {
            'rue': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de la rue, numéro'
            }),
            'ville': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ville'
            }),
            'code_postal': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Code postal'
            }),
            'pays': forms.TextInput(attrs={
                'class': 'form-control',
                'value': 'Côte d\'Ivoire',
                'readonly': 'readonly'
            })
        }
        labels = {
            'rue': 'Adresse complète',
            'ville': 'Ville',
            'code_postal': 'Code postal',
            'pays': 'Pays'
        }

class PaiementForm(forms.Form):
    METHODE_PAIEMENT_CHOICES = [
        ('mobile_money', 'Mobile Money'),
        ('carte', 'Carte Bancaire'),
        ('sur_place', 'Paiement en magasin'),
        ('a_la_livraison', 'Paiement à la livraison'),
    ]
    
    methode_paiement = forms.ChoiceField(
        choices=METHODE_PAIEMENT_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'paiement-method'
        }),
        initial='mobile_money'
    )

class MobileMoneyForm(forms.Form):
    OPERATEUR_CHOICES = [
        ('mtn', 'MTN'),
        ('orange', 'Orange'),
        ('moov', 'Moov'),
    ]
    
    numero = forms.CharField(
        max_length=20,
        label="Numéro Mobile Money",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'XX XXX XXXX'
        })
    )
    operateur = forms.ChoiceField(
        choices=OPERATEUR_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label="Opérateur"
    )

class CarteBancaireForm(forms.Form):
    numero_carte = forms.CharField(
        max_length=16,
        min_length=16,
        label="Numéro de carte",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '1234 5678 9012 3456'
        })
    )
    date_expiration = forms.CharField(
        max_length=5,
        label="Date d'expiration (MM/AA)",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'MM/AA'
        })
    )
    cvv = forms.CharField(
        max_length=3,
        min_length=3,
        label="Code de sécurité",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '123'
        })
    )

class CouponForm(forms.Form):
    code = forms.CharField(
        max_length=20,
        label="Code promo",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Entrez votre code promo'
        })
    )

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if code:
            try:
                coupon = Coupon.objects.get(code=code)
                if not coupon.is_valide():
                    raise forms.ValidationError("Ce coupon a expiré")
            except Coupon.DoesNotExist:
                raise forms.ValidationError("Code promo invalide")
        return code
    



#Serveur

class ClientForm(forms.Form):
    nom_complet = forms.CharField(max_length=100, label="Nom complet", widget=forms.TextInput(attrs={'placeholder': 'Prénom Nom', 'class': 'form-control'}))
    telephone = forms.CharField(max_length=15, label="Téléphone", widget=forms.TextInput(attrs={'placeholder': '+228 XX XX XX XX', 'class': 'form-control'}))
    email = forms.EmailField(required=False, label="Email", widget=forms.EmailInput(attrs={'placeholder': 'email@exemple.com', 'class': 'form-control'}))

class ProduitPanierForm(forms.Form):
    produit = forms.ModelChoiceField(
        queryset=Produit.objects.filter(quantite_disponible__gt=0),
        label="Produit",
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Sélectionnez un produit"
    )
    quantite = forms.IntegerField(
        min_value=1,
        initial=1,
        label="Quantité",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ajouter le stock dans le label des options
        self.fields['produit'].label_from_instance = lambda obj: f"{obj.nom} - {obj.prix} FCFA (Stock: {obj.quantite_disponible})"

class PaiementServeurForm(forms.Form):
    METHODES_PAIEMENT = [
        ('espèces', 'Espèces'),
        ('carte_bancaire', 'Carte Bancaire'),
        ('mobile_money', 'Mobile Money'),
    ]
    
    methode_paiement = forms.ChoiceField(
        choices=METHODES_PAIEMENT,
        label="Méthode de paiement",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    montant_paye = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        label="Montant payé",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    #---------------------Avis des clients------------------------------
  


class PreferenceAlimentaireForm(forms.ModelForm):
    class Meta:
        model = PreferenceAlimentaire
        fields = ['type', 'description', 'severite', 'est_actif']
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Décrivez votre allergie, intolérance ou préférence alimentaire...'
            }),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'severite': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'est_actif': 'Cette préférence est active',
        }
class AvisProduitForm(forms.ModelForm):
    image = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput, 
        label='Ajouter une photo'
    )
    
    class Meta:
        model = AvisProduit
        fields = ['note', 'titre', 'commentaire', 'remarques', 'image']
        widgets = {
            'commentaire': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Partagez votre expérience avec ce produit...'
            }),
            'remarques': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Remarques supplémentaires, suggestions...'
            }),
            'note': forms.RadioSelect(choices=AvisProduit.NOTE_CHOICES),
        }
class NotationCommandeForm(forms.ModelForm):
    image = forms.ImageField(
        required=False,
        widget=forms.FileInput(),  # simple FileInput pour une seule image
        label='Ajouter une photo de la commande'
    )
    
    class Meta:
        model = NotationCommande
        fields = ['note_globale', 'note_livraison', 'note_emballage', 'commentaire', 'remarques', 'image']
        widgets = {
            'commentaire': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Comment était votre expérience globale avec cette commande ?'
            }),
            'remarques': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Remarques supplémentaires, suggestions...'
            }),
            'note_globale': forms.RadioSelect(),
            'note_livraison': forms.RadioSelect(),
            'note_emballage': forms.RadioSelect(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['note_globale'].widget.attrs.update({'class': 'form-check-input'})
        self.fields['note_livraison'].widget.attrs.update({'class': 'form-check-input'})
        self.fields['note_emballage'].widget.attrs.update({'class': 'form-check-input'})
class ProblemeCommandeForm(forms.ModelForm):
    image = forms.ImageField(
        required=False,
        widget=forms.FileInput(),  # simple FileInput pour une seule image
        label='Ajouter une photo du problème'
    )
    
    class Meta:
        model = ProblemeCommande
        fields = ['type_probleme', 'produit_concerne', 'description', 'image']  # ajout de 'image'
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Décrivez précisément le problème rencontré...'
            }),
            'type_probleme': forms.Select(attrs={'class': 'form-select'}),
            'produit_concerne': forms.Select(attrs={'class': 'form-select'}),
        }



#++++++++++++++++++++++++ Gestion livreur par admin +++++++++++++++++++++++++

class LivreurForm(UserCreationForm):
    email = forms.EmailField(required=True)
    telephone = forms.CharField(max_length=15, required=True)
    first_name = forms.CharField(max_length=30, required=True, label='Prénom')
    last_name = forms.CharField(max_length=30, required=True, label='Nom')

    class Meta:
        model = Utilisateur
        fields = ['username', 'email', 'first_name', 'last_name', 'telephone', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'livreur'
        user.email = self.cleaned_data['email']
        user.telephone = self.cleaned_data['telephone']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
        return user
    
class LivreurUpdateForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@exemple.com'})
    )
    telephone = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '90 12 34 56'})
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        label='Prénom',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        label='Nom',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom de famille'})
    )
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Nom d'utilisateur"})
    )

    class Meta:
        model = Utilisateur
        fields = ['username', 'email', 'first_name', 'last_name', 'telephone']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        # Vérifie qu'aucun autre utilisateur n'a ce username
        if Utilisateur.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Ce nom d'utilisateur est déjà utilisé par un autre compte.")
        return username


class ModifierGerantForm(UserChangeForm):
   
    password = None  # Suppression du champ mot de passe par défaut

    username = forms.CharField(
        label="Nom d'utilisateur",
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': "Nom d'utilisateur du gérant"
        })
    )

    email = forms.EmailField(
        label="Email",
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@exemple.com'
        })
    )

    first_name = forms.CharField(
        label="Prénom",
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom'})
    )

    last_name = forms.CharField(
        label="Nom",
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom de famille'})
    )

    telephone = forms.CharField(
        label="Téléphone",
        max_length=15,
        required=True,
        help_text='Format: 90 12 34 56',
        validators=[RegexValidator(
            regex=r'^(90|91|92|93|96|97|98|99)[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$',
            message='Numéro togolais invalide'
        )],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '90 12 34 56'})
    )

    class Meta:
        model = Utilisateur
        fields = ['username', 'first_name', 'last_name', 'email', 'telephone']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        # Vérifie qu'aucun autre utilisateur n'a ce username
        if Utilisateur.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Ce nom d'utilisateur est déjà utilisé par un autre compte.")
        return username
    
    password = None  # Suppression du champ mot de passe par défaut

    first_name = forms.CharField(
        label="Prénom",
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom'})
    )

    last_name = forms.CharField(
        label="Nom",
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom de famille'})
    )

    telephone = forms.CharField(
        label="Téléphone",
        max_length=15,
        required=True,
        help_text='Format: 90 12 34 56',
        validators=[RegexValidator(
            regex=r'^(90|91|92|93|96|97|98|99)[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$',
            message='Numéro togolais invalide'
        )],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '90 12 34 56'})
    )

    class Meta:
        model = Utilisateur
        fields = ['username', 'first_name', 'last_name', 'email', 'telephone']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        # Vérifie qu'aucun autre utilisateur n'a ce username
        if Utilisateur.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Ce nom d'utilisateur est déjà utilisé par un autre compte.")
        return username
    
class ModifierServeurForm(UserChangeForm):
   
    password = None 

    username = forms.CharField(
        label="Nom d'utilisateur",
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': "Nom d'utilisateur du serveur"
        })
    )

    email = forms.EmailField(
        label="Email",
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@exemple.com'
        })
    )

    first_name = forms.CharField(
        label="Prénom",
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom'})
    )

    last_name = forms.CharField(
        label="Nom",
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom de famille'})
    )

    telephone = forms.CharField(
        label="Téléphone",
        max_length=15,
        required=True,
        help_text='Format: 90 12 34 56',
        validators=[RegexValidator(
            regex=r'^(90|91|92|93|96|97|98|99)[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$',
            message='Numéro togolais invalide'
        )],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '90 12 34 56'})
    )

    class Meta:
        model = Utilisateur
        fields = ['username', 'first_name', 'last_name', 'email', 'telephone']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        # Vérifie qu'aucun autre utilisateur n'a ce username
        if Utilisateur.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Ce nom d'utilisateur est déjà utilisé par un autre compte.")
        return username
    
    from django import forms


Utilisateur = get_user_model()

class ModifierClientForm(UserChangeForm):
    password = None  # On supprime le champ mot de passe du formulaire

    username = forms.CharField(
        label="Nom d'utilisateur",
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': "Nom d'utilisateur du client"
        })
    )

    email = forms.EmailField(
        label="Email",
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@exemple.com'
        })
    )

    first_name = forms.CharField(
        label="Prénom",
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Prénom'
        })
    )

    last_name = forms.CharField(
        label="Nom",
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom de famille'
        })
    )

    telephone = forms.CharField(
        label="Téléphone",
        max_length=15,
        required=True,
        help_text='Format: 90 12 34 56',
        validators=[RegexValidator(
            regex=r'^(90|91|92|93|96|97|98|99)[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$',
            message='Numéro togolais invalide'
        )],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '90 12 34 56'
        })
    )

    class Meta:
        model = Utilisateur
        fields = ['username', 'first_name', 'last_name', 'email', 'telephone']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        # Vérifie qu'aucun autre utilisateur n’a ce nom d’utilisateur
        if Utilisateur.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Ce nom d'utilisateur est déjà utilisé par un autre compte.")
        return username