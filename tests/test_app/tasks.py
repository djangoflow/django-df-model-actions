from celery.app import shared_task
from django.apps import apps

from tests.test_app.models import BroadcastNotification, M


def create_or_update_notification(instance: M, context: dict) -> None:
    notification = BroadcastNotification.objects.create(post=instance.id)
    notification.title = (
        f"Post: {instance.title} is created"
        if context.get("created")
        else f"Post {instance.title} is updated"
    )
    notification.save()


def delete_notifications(instance: M, context: dict) -> None:
    BroadcastNotification.objects.filter(post=instance.id).delete()


@shared_task
def create_or_update_notification_task(
    instance_id: int, app_label: str, model_name: str, context: dict
) -> None:
    model = apps.get_model(app_label, model_name)
    instance = model.objects.get(pk=instance_id)
    notification = BroadcastNotification.objects.create(post=instance.id)
    notification.title = (
        f"Post: {instance.title} is created"
        if context.get("created")
        else f"Post {instance.title} is updated"
    )
    notification.save()


@shared_task
def delete_notifications_task(
    instance_id: int, app_label: str, model_name: str, context: dict
) -> None:
    model = apps.get_model(app_label, model_name)
    instance = model.objects.get(pk=instance_id)
    BroadcastNotification.objects.filter(post=instance.id).delete()
