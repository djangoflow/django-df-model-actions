from django.db import models


class Post(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField()
    is_published = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.title
