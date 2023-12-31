from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DFApiConfig(AppConfig):
    name = "df_model_actions"
    verbose_name = _("DjangoFlow API DRF")
