from tests.test_app.models import BroadcastNotification, M


def create_notification(instance: M, context: dict) -> None:
    if instance.is_published:
        BroadcastNotification.objects.create(title=f"Post: {instance.title} is created")


# @task
# def create_notification_task(instance, context):
#     # Creates a BroadcastNotification on post save
#     BroadcastNotification.objects.create(title="Post: ")
#
