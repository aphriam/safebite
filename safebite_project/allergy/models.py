from django.db import models
from django.contrib.auth.models import User


class UserAllergy(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    allergy_name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.user.username} - {self.allergy_name}"