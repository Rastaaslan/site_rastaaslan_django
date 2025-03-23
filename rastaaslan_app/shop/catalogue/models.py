from django.db import models
from oscar.apps.catalogue.abstract_models import AbstractProduct

class Product(AbstractProduct):
    """
    Extension du modèle de produit Oscar avec des champs personnalisés
    """
    is_streamer_exclusive = models.BooleanField(
        default=False, 
        verbose_name="Article exclusif aux streamers",
        help_text="Cochez cette case pour les produits réservés aux streamers"
    )
    
    related_vod = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        verbose_name="VOD associée",
        help_text="ID de la VOD Twitch associée à ce produit (si applicable)"
    )

# L'import suivant doit être à la fin du fichier pour éviter les problèmes d'imports circulaires
from oscar.apps.catalogue.models import *  # noqa isort:skip