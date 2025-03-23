from oscar.apps.dashboard.app import DashboardApplication as CoreDashboardApplication

class DashboardApplication(CoreDashboardApplication):
    """
    Extension du tableau de bord d'Oscar
    """
    def get_urls(self):
        urls = super().get_urls()
        # Ici vous pouvez ajouter des URLs personnalisées pour le tableau de bord
        return urls