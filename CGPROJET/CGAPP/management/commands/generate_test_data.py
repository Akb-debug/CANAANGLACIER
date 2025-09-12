import os
import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.core.files import File
from django.contrib.auth import get_user_model
from django.db import transaction
from faker import Faker
from faker.providers import lorem

from CGAPP.models import (
    Categorie, Produit, AvisProduit, Utilisateur, Gerant
)

class Command(BaseCommand):
    help = 'Génère des données de test (catégories, produits, avis)'

    def handle(self, *args, **options):
        fake = Faker('fr_FR')
        fake.add_provider(lorem)
        
        # Créer des catégories
        categories_data = [
            {'nom': 'Glaces', 'description': 'Délicieuses glaces artisanales'},
            {'nom': 'Boissons', 'description': 'Rafraîchissements variés'},
            {'nom': 'Pâtisseries', 'description': 'Viennoiseries et pâtisseries maison'},
            {'nom': 'Snacks', 'description': 'En-cas salés et sucrés'},
            {'nom': 'Desserts', 'description': 'Desserts gourmands'}
        ]
        
        categories = []
        for cat_data in categories_data:
            cat, created = Categorie.objects.get_or_create(
                nom=cat_data['nom'],
                defaults={'description': cat_data['description']}
            )
            categories.append(cat)
            self.stdout.write(self.style.SUCCESS(f'Catégorie créée : {cat.nom}'))
        
        # Créer un utilisateur avec le rôle gérant s'il n'existe pas
        try:
            utilisateur_gerant = Utilisateur.objects.get(username='gerant')
            gerant, created = Gerant.objects.get_or_create(utilisateur=utilisateur_gerant)
        except Utilisateur.DoesNotExist:
            # Créer d'abord l'utilisateur avec uniquement les champs valides
            utilisateur_gerant = Utilisateur.objects.create_user(
                username='gerant',
                email='gerant@example.com',
                password='passer123',
                first_name='Jean',
                last_name='Dupont',
                role='gerant',
                telephone='+221781234567'
            )
            # Puis créer l'instance Gerant liée
            gerant = Gerant.objects.create(utilisateur=utilisateur_gerant)
            self.stdout.write(self.style.SUCCESS('Gérant créé avec succès'))
        
        # Liste d'images de démonstration (à placer dans le dossier media/produits/)
        images_dir = os.path.join('media', 'produits')
        os.makedirs(images_dir, exist_ok=True)
        
        # Produits à créer avec des images par défaut
        produits_data = [
            # Glaces
            {
                'nom': 'Glace Chocolat',
                'description': 'Glace onctueuse au chocolat belge',
                'prix': 2000,
                'categorie': 'Glaces',
                'image': 'default-product.png',
                'quantite_stock': 100,
                'est_disponible': True
            },
            {
                'nom': 'Glace Vanille',
                'description': 'Glace crémeuse à la vanille de Madagascar',
                'prix': 1800,
                'categorie': 'Glaces',
                'image': 'default-product.png',
                'quantite_stock': 150,
                'est_disponible': True
            },
            # Ajoutez d'autres produits ici...
            {
                'nom': 'Jus d\'Orange Frais',
                'description': 'Jus d\'orange pressé 100% naturel',
                'prix': 1500,
                'categorie': 'Boissons',
                'image': 'default-product.png',
                'quantite_stock': 80,
                'est_disponible': True
            },
            {
                'nom': 'Jus de Mangue',
                'description': 'Jus de mangue frais et sucré',
                'prix': 1800,
                'categorie': 'Boissons',
                'image': 'default-product.png',
                'quantite_stock': 90,
                'est_disponible': True
            },
            {
                'nom': 'Croissant',
                'description': 'Croissant pur beurre frais du jour',
                'prix': 1000,
                'categorie': 'Pâtisseries',
                'image': 'default-product.png',
                'quantite_stock': 60,
                'est_disponible': True
            },
            {
                'nom': 'Pain au Chocolat',
                'description': 'Pain au chocolat moelleux et croustillant',
                'prix': 1200,
                'categorie': 'Pâtisseries',
                'image': 'default-product.png',
                'quantite_stock': 50,
                'est_disponible': True
            },
            {
                'nom': 'Cookie Chocolat',
                'description': 'Cookie moelleux aux pépites de chocolat',
                'prix': 800,
                'categorie': 'Snacks',
                'image': 'default-product.png',
                'quantite_stock': 120,
                'est_disponible': True
            },
            {
                'nom': 'Tarte aux Pommes',
                'description': 'Tarte fine aux pommes caramélisées',
                'prix': 2500,
                'categorie': 'Desserts',
                'image': 'default-product.png',
                'quantite_stock': 30,
                'est_disponible': True
            },
        ]
        
        # Créer un fichier image par défaut s'il n'existe pas
        default_image_path = os.path.join('media', 'default-product.png')
        if not os.path.exists(default_image_path):
            from PIL import Image, ImageDraw
            img = Image.new('RGB', (400, 300), color=(220, 220, 220))
            d = ImageDraw.Draw(img)
            d.text((100, 140), "Image du produit", fill=(100, 100, 100))
            img.save(default_image_path)
        
        # Créer les produits
        for prod_data in produits_data:
            try:
                with transaction.atomic():
                    # Créer le produit
                    categorie = Categorie.objects.get(nom=prod_data['categorie'])
                    
                    # Utiliser l'image par défaut
                    image_path = os.path.join('media', prod_data['image'])
                    if not os.path.exists(image_path):
                        # Copier l'image par défaut si elle n'existe pas
                        import shutil
                        shutil.copy2(default_image_path, image_path)
                    
                    # Créer l'instance du produit
                    produit = Produit.objects.create(
                        nom=prod_data['nom'],
                        description=prod_data['description'],
                        description_longue=prod_data.get('description_longue', prod_data['description']),
                        prix=prod_data['prix'],
                        categorie=categorie,
                        gerant=gerant,
                        quantite_disponible=prod_data.get('quantite_stock', 10),
                        promotion=prod_data.get('promotion', 0)
                    )
                    
                    # Associer l'image
                    with open(image_path, 'rb') as f:
                        produit.image.save(prod_data['image'], File(f), save=True)
                    
                    self.stdout.write(self.style.SUCCESS(f'Produit créé : {produit.nom}'))
                    
                    # Créer des avis pour ce produit
                    for _ in range(random.randint(3, 10)):
                        # Créer un utilisateur fictif pour l'avis
                        username = fake.user_name()
                        while Utilisateur.objects.filter(username=username).exists():
                            username = fake.user_name()
                            
                        user = Utilisateur.objects.create_user(
                            username=username,
                            email=fake.unique.email(),
                            password='passer123',
                            first_name=fake.first_name(),
                            last_name=fake.last_name(),
                            telephone=f'+22177{random.randint(1000000, 9999999)}',
                            role='client'
                        )
                        
                        AvisProduit.objects.create(
                            utilisateur=user,
                            produit=produit,
                            note=random.randint(3, 5),
                            titre=fake.sentence(nb_words=4),
                            commentaire=fake.paragraph(nb_sentences=3),
                            date_creation=fake.date_time_between(start_date='-1y', end_date='now')
                        )
                        
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Erreur lors de la création du produit {prod_data["nom"]}: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS('Données de test générées avec succès!'))
