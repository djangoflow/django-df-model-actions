from typing import Any

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver


class ServerAction(models.Model):
    class Type(models.TextChoices):
        python_code = "python_code"

    name = models.CharField(max_length=255)
    python_code = models.TextField(help_text="Python code. Allowed variables: instance")

    def __str__(self) -> str:
        return self.name


class ModelAction(models.Model):
    class TriggerCondition(models.TextChoices):
        on_creation = "on_creation"
        on_update = "on_update"
        on_deletion = "on_deletion"

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    trigger = models.CharField(
        max_length=32, choices=TriggerCondition.choices, editable=False
    )
    action = models.ForeignKey(
        ServerAction, on_delete=models.CASCADE, related_name="model_actions"
    )
    model = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name="model_actions"
    )
    condition = models.TextField(
        null=True,
        blank=True,
        help_text="Python code. If it returns False, the action is not executed."
        "Allowed variable: instance",
    )
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name

    def execute_server_action(self, sender: Any, instance: Any, **kwargs: Any) -> None:
        if (
            self.trigger == self.TriggerCondition.on_creation
            and not kwargs.get("created")
            or self.trigger == self.TriggerCondition.on_update
            and kwargs.get("created")
        ):
            return

        if not self.is_active:
            return

        if self.condition:
            condition_result = eval(self.condition, {"instance": instance})  # noqa S307
        else:
            condition_result = True

        if condition_result:
            exec(self.action.python_code, {"instance": instance})  # noqa S102

    def register_model_signal(self) -> None:
        model_class = self.model.model_class()
        if self.trigger in [
            self.TriggerCondition.on_creation,
            self.TriggerCondition.on_update,
        ]:
            post_save.connect(
                self.execute_server_action,
                sender=model_class,
                dispatch_uid=self.signal_uid(),
            )
        elif self.trigger == self.TriggerCondition.on_deletion:
            post_delete.connect(
                self.execute_server_action,
                sender=model_class,
                dispatch_uid=self.signal_uid(),
            )

    def update_model_signal(self) -> None:
        self.register_model_signal()

    def remove_model_signal(self) -> None:
        # Getting the model class
        model_class = self.model.model_class()

        # Disconnecting the signal
        post_save.disconnect(sender=model_class, dispatch_uid=self.signal_uid())
        post_delete.disconnect(sender=model_class, dispatch_uid=self.signal_uid())

    def signal_uid(self) -> str:
        return f"ModelAction_{self.id}"


@receiver(post_save, sender=ModelAction)
def model_action_created_or_updated(
    sender: Any, instance: Any, created: bool, **kwargs: Any
) -> None:
    # Register the new signal / Update the signal
    instance.update_model_signal()


@receiver(post_delete, sender=ModelAction)
def model_action_deleted(sender: Any, instance: Any, **kwargs: Any) -> None:
    # Remove the signal
    instance.remove_model_signal()
