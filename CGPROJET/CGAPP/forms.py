from django import forms
from django.core.validators import RegexValidator,validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm
from .models import Utilisateur,Contact,AbonnementNewsletter


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
            regex='^(90|91|92|93|96|97|98|99)[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$',
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
                regex='^[a-zA-ZÀ-ÿ\s\-]{2,100}$',
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
                regex='^[a-zA-ZÀ-ÿ\s\-]{2,100}$',
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
                regex='^(90|91|92|93|96|97|98|99)[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$',
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
    

class ContactForm(forms.ModelForm):
    # Champ nom avec validation personnalisée
    nom = forms.CharField(
        label="Votre nom complet",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre nom complet'
        }),
        validators=[
            RegexValidator(
                regex='^[a-zA-ZÀ-ÿ\s\-]{2,100}$',
                message='Le nom ne doit contenir que des lettres et espaces (2-100 caractères)'
            )
        ]
    )
    
    # Champ email avec validation renforcée
    email = forms.EmailField(
        label="Votre email",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'votre@email.com'
        })
    )
    
    # Champ sujet avec choix prédéfinis
    SUJET_CHOICES = [
        ('', 'Sélectionnez un sujet...'),
        ('commande', 'Question sur une commande'),
        ('produit', 'Question sur un produit'),
        ('livraison', 'Problème de livraison'),
        ('autre', 'Autre demande')
    ]
    
    sujet = forms.ChoiceField(
        label="Sujet de votre message",
        choices=SUJET_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    # Champ message avec configuration spécifique
    message = forms.CharField(
        label="Votre message",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Décrivez votre demande en détail...'
        }),
        min_length=10,
        max_length=1000
    )
    
    class Meta:
        model = Contact
        fields = ['nom', 'email', 'sujet', 'message']
    
    def clean_sujet(self):
        sujet = self.cleaned_data.get('sujet')
        if not sujet:
            raise forms.ValidationError("Veuillez sélectionner un sujet.")
        return sujet


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