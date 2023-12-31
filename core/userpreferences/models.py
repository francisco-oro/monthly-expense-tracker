from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class UserPreferences(models.Model):
    user = models.OneToOneField(to=User, on_delete=models.CASCADE)
    currency = models.CharField(max_length=255, blank=True)


    def __str__(self) -> str:
        return str(self.user)+'s'+'preferences'
    
    class Meta:
        verbose_name_plural = "User preferences"