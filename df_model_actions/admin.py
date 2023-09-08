from django.contrib import admin

from df_model_actions.models import ModelAction, ServerAction


@admin.register(ServerAction)
class ServerActionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "type",
    )


@admin.register(ModelAction)
class ModelActionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "action",
    )
