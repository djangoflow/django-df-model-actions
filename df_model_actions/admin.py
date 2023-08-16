from django.contrib import admin


class ServerActionAdmin(admin.ModelAdmin):
    list_display = ("id", "name")


class ModelActionAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "server_action")
