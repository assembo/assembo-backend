from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    # Any extra fields would go here
    def __str__(self):
        return self.email

