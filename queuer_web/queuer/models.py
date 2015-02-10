from django.db import models

class QueuedPlayer(models.Model):
    name = models.CharField(max_length=200, unique=True)

class Game(models.Model):
    p1 = models.CharField(max_length=200)
    p2 = models.CharField(max_length=200)
    active = models.BooleanField(default=True)
