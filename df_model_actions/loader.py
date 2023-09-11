from django.db import connection

from df_model_actions.models import ModelAction


def signal_loader() -> None:
    if ModelAction._meta.db_table in connection.introspection.table_names():
        for model_action in ModelAction.objects.all():
            model_action.register_model_signal()
