from django.contrib import admin

from tests.test_app.models import BroadcastNotification, Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    pass


@admin.register(BroadcastNotification)
class BroadcastNotificationAdmin(admin.ModelAdmin):
    pass
