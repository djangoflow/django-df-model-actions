from typing import Any, TypeVar

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils.module_loading import import_string

from df_model_actions.settings import module_settings

M = TypeVar("M", bound=models.Model)


class ServerAction(models.Model):
    class Type(models.TextChoices):
        python_code = "python_code"
        python_function = "python_function"
        celery_task = "celery_task"

    name = models.CharField(max_length=255)
    executable_action = models.TextField(
        help_text="It can be python code, python function or celery task", default=""
    )
    type = models.CharField(
        max_length=32, choices=Type.choices, default=Type.python_code
    )
    context = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:
        return self.name

    def execute_celery_task(self, instance: M, **kwargs: Any) -> None:
        task_path = self.executable_action
        try:
            task = import_string(task_path)
            kwargs.pop("signal")
            parameters = {
                "instance_id": instance.id,
                "app_label": instance._meta.app_label,
                "model_name": instance._meta.model_name,
                "context": {**self.context, **kwargs},
            }
            try:
                if module_settings.CELERY_USE_ASYNC:
                    task.apply_async(kwargs=parameters)
                else:
                    task.apply(kwargs=parameters)
            except Exception as e:
                print(f"{type(e)}: {str(e)}")
                raise type(e)(  # noqa B904
                    f"ServerAction: Failed to execute the celery task:{task_path} "
                )
        except ModuleNotFoundError:
            raise ModuleNotFoundError(  # noqa B904
                f"ServerAction: Celery task {task_path} could not be found in current scope"
            )

    def execute_python_code(self, instance: M, **kwargs: Any) -> None:
        exec(self.executable_action, {"instance": instance})  # noqa S102

    def execute_python_function(self, instance: M, **kwargs: Any) -> None:
        function_path = self.executable_action
        try:
            function = import_string(function_path)
            try:
                function(instance=instance, context={**self.context, **kwargs})
            except Exception as e:
                print(f"{type(e)}: {str(e)}")
                raise type(e)(  # noqa B904
                    f"ServerAction: Failed to execute the function:{function_path} "
                )
        except Exception:
            raise ModuleNotFoundError(  # noqa B904
                f"ServerAction: function {function_path} could not be found in current scope"
            )


class ModelAction(models.Model):
    class TriggerCondition(models.TextChoices):
        on_creation = "on_creation"
        on_update = "on_update"
        on_deletion = "on_deletion"

    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    trigger = models.CharField(max_length=32, choices=TriggerCondition.choices)
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
            if self.action.type == ServerAction.Type.python_code:
                self.action.execute_python_code(instance, **kwargs)
            elif self.action.type == ServerAction.Type.python_function:
                self.action.execute_python_function(instance, **kwargs)
            else:
                self.action.execute_celery_task(instance, **kwargs)

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
