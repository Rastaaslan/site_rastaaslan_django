#!/usr/bin/env python
"""
Script d'initialisation pour la boutique Oscar.
Ce script doit être exécuté après avoir appliqué les migrations.
"""
import os
import django

# Configurer l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rastaaslan_website.settings')
django.setup()

from django.core.management import call_command
from django.contrib.auth.models import User
from oscar.apps.catalogue.categories import create_from_breadcrumbs
from oscar.apps.partner.models import Partner, StockRecord
from oscar.apps.catalogue.models import ProductClass, Product

def create_superuser():
    """Crée un superutilisateur s'il n'en existe pas déjà"""
    if not User.objects.filter(is_superuser=True).exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin'
        )
        print("Superutilisateur créé avec succès.")
    else:
        print("Un superutilisateur existe déjà.")

def create_product_class():
    """Crée la classe de produit par défaut si elle n'existe pas"""
    if not ProductClass.objects.exists():
        ProductClass.objects.create(
            name='Marchandise',
            requires_shipping=True,
            track_stock=True
        )
        print("Classe de produit 'Marchandise' créée avec succès.")
    else:
        print("Des classes de produit existent déjà.")

def create_partner():
    """Crée un partenaire par défaut si aucun n'existe"""
    if not Partner.objects.exists():
        Partner.objects.create(
            name='RastaAslan Store',
            code='rastaaslan'
        )
        print("Partenaire 'RastaAslan Store' créé avec succès.")
    else:
        print("Des partenaires existent déjà.")

def create_categories():
    """Crée les catégories de produits"""
    categories = [
        'Vêtements > T-shirts',
        'Vêtements > Sweats',
        'Accessoires > Mugs',
        'Accessoires > Stickers',
        'Exclusivités Streamers'
    ]
    
    for breadcrumbs in categories:
        create_from_breadcrumbs(breadcrumbs)
    
    print("Catégories créées avec succès.")

def create_stock_records():
    """Crée des enregistrements de stock pour les produits"""
    partner = Partner.objects.first()
    if not partner:
        print("Aucun partenaire trouvé. Création de stock ignorée.")
        return
        
    for product in Product.objects.filter(structure=Product.STANDALONE):
        if not StockRecord.objects.filter(product=product).exists():
            price = 19.99
            if 'Mug' in product.title:
                price = 12.99
            elif 'Hoodie' in product.title or 'Sweat' in product.title:
                price = 49.99
                
            StockRecord.objects.create(
                product=product,
                partner=partner,
                partner_sku=f'SKU-{product.id}',
                price_excl_tax=price,
                price_retail=price,
                cost_price=price * 0.6,
                num_in_stock=100
            )
    
    print("Enregistrements de stock créés avec succès.")

def main():
    """Fonction principale qui exécute toutes les étapes d'initialisation"""
    print("Début de l'initialisation de la boutique Oscar...")
    
    # Charger les données par défaut
    call_command('loaddata', 'countries.json')
    print("Pays chargés avec succès.")
    
    # Créer les éléments de base
    create_superuser()
    create_product_class()
    create_partner()
    create_categories()
    
    # Charger les produits initiaux
    try:
        call_command('loaddata', 'initial_products.json')
        print("Produits initiaux chargés avec succès.")
    except Exception as e:
        print(f"Erreur lors du chargement des produits: {e}")
    
    # Créer les enregistrements de stock
    create_stock_records()
    
    print("Initialisation de la boutique Oscar terminée avec succès.")

if __name__ == "__main__":
    main()