# api/models.py

from django.db import models

class Student(models.Model):
    name = models.CharField(max_length=100)
    roll = models.IntegerField(unique=True)
    city = models.CharField(max_length=100)

    def __str__(self):
        return self.name