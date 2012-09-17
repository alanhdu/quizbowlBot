from django.db import models

class Question(models.Model):
    body = models.TextField()
    category = models.TextField()
    label = models.ForeignKey("Label", related_name="questions")
class Label(models.Model):
    body = models.TextField()
