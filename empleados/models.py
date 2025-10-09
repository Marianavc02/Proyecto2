from django.contrib.auth.models import User
from django.db import models


class Empleado(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    id = models.AutoField(primary_key=True)
    preferred_name = models.CharField(max_length=100)
    sbd_email = models.EmailField(unique=True)

    def __str__(self):
        return self.preferred_name
