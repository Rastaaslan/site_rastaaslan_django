from django.apps import AppConfig


class RastaaslanAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rastaaslan_app'
    verbose_name = "Application Rastaaslan"
    
    def ready(self):
        """
        Configuration qui s'exécute au démarrage de l'application.
        Idéal pour enregistrer des signaux ou effectuer d'autres initialisations.
        """
        # Importer les signaux si nécessaire
        import rastaaslan_app.signals  # À créer si vous avez des signaux
        
        # Vous pouvez configurer d'autres éléments ici
        # Par exemple, initialisation de tâches périodiques, etc.
        pass