from typing import TypeVar

from django.db import models

M = TypeVar("M", bound=models.Model)


class Post(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField()
    is_published = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.title


class BroadcastNotification(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField()
    post = models.IntegerField()

    def __str__(self) -> str:
        return self.title
