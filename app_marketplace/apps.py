from django.apps import AppConfig


class AppMarketplaceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app_marketplace'
    
    def ready(self):
        """Registra signals quando o app estiver pronto"""
        import app_marketplace.signals_whatsapp  # noqa