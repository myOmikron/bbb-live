from django.db import models
from django.db.models import BooleanField


class Streaming(models.Model):
    running = BooleanField(default=False)
