"""generated with djinit"""

from django.db import models


class AbstractBaseModel(models.Model):
    """Abstract base model with common fields."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
