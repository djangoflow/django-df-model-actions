from typing import Any
from unittest.mock import patch

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from df_model_action.models import ModelAction, ServerAction

from .models import Post


class CustomSignalTestCase(TestCase):
    def setUp(self) -> None:
        self.post = Post.objects.create(title="Test", body="This is a test post")
        self.content_type = ContentType.objects.get_for_model(Post)
        self.server_action = ServerAction.objects.create(
            name="Test Action", python_code='instance.title = "Changed by signal"'
        )

    def test_signal_on_creation(self) -> None:
        _ = ModelAction.objects.create(
            name="On Creation Test",
            trigger=ModelAction.TriggerCondition.on_creation,
            action=self.server_action,
            model=self.content_type,
        )

        new_post = Post.objects.create(title="Another test", body="Test post body")

        self.assertEqual(new_post.title, "Changed by signal")

    def test_signal_on_update(self) -> None:
        _ = ModelAction.objects.create(
            name="On Update Test",
            trigger=ModelAction.TriggerCondition.on_update,
            action=self.server_action,
            model=self.content_type,
        )

        self.post.body = "Updated body"
        self.post.save()

        self.assertEqual(self.post.title, "Changed by signal")

    @patch("builtins.print")
    def test_signal_on_deletion(self, mock_print: Any) -> None:
        delete_action = ServerAction.objects.create(
            name="Test Delete", python_code='print("Post Deleted")'
        )
        _ = ModelAction.objects.create(
            name="On Deletion Test",
            trigger=ModelAction.TriggerCondition.on_deletion,
            action=delete_action,
            model=self.content_type,
        )

        self.post.delete()

        # Check if the print function was called with the expected argument
        mock_print.assert_called_once_with("Post Deleted")

    def test_inactive_signal_does_not_execute(self) -> None:
        _ = ModelAction.objects.create(
            name="Inactive Signal Test",
            trigger=ModelAction.TriggerCondition.on_creation,
            action=self.server_action,
            model=self.content_type,
            is_active=False,
        )

        new_post = Post.objects.create(title="Another test", body="Test post body")
        self.assertNotEqual(new_post.title, "Changed by signal")

    def test_condition_blocks_execution(self) -> None:
        _ = ModelAction.objects.create(
            name="Condition Block Test",
            trigger=ModelAction.TriggerCondition.on_creation,
            action=self.server_action,
            model=self.content_type,
            condition="instance.title != 'Block this'",
        )

        new_post = Post.objects.create(title="Block this", body="Test post body")
        self.assertNotEqual(new_post.title, "Changed by signal")

    def test_condition_allows_execution(self) -> None:
        _ = ModelAction.objects.create(
            name="Condition Allow Test",
            trigger=ModelAction.TriggerCondition.on_creation,
            action=self.server_action,
            model=self.content_type,
            condition="instance.title != 'Block this'",
        )

        new_post = Post.objects.create(title="Do not block", body="Test post body")
        self.assertEqual(new_post.title, "Changed by signal")

    def test_signal_update(self) -> None:
        _ = ModelAction.objects.create(
            name="Signal Update Test",
            trigger=ModelAction.TriggerCondition.on_update,
            action=self.server_action,
            model=self.content_type,
        )

        self.post.body = "Updated body"
        self.post.save()

        self.assertEqual(self.post.title, "Changed by signal")

        self.server_action.python_code = 'instance.body = "Body changed by signal"'
        self.server_action.save()

        self.post.body = "Updated body again"
        self.post.save()
        self.assertEqual(self.post.body, "Body changed by signal")

    def test_signal_removal_after_model_action_deleted(self) -> None:
        action = ModelAction.objects.create(
            name="Signal Removal Test",
            trigger=ModelAction.TriggerCondition.on_creation,
            action=self.server_action,
            model=self.content_type,
        )
        action.delete()

        new_post = Post.objects.create(title="After Removal", body="Original body")
        self.assertNotEqual(new_post.title, "Changed by signal")
