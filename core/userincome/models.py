from django.db import models
from django.utils.timezone import now
from django.contrib.auth.models import User

class UserIncome(models.Model):
    amount = models.FloatField()
    date = models.DateField(default=now)
    description = models.TextField()
    owner = models.ForeignKey(to=User, on_delete=models.CASCADE)
    source = models.CharField(max_length=266)


    def __str__(self) -> str:
        return self.source
    
    class Meta:
        ordering = ['-date']
        verbose_name_plural = 'Income'

class Source(models.Model):
    name=models.CharField(max_length=255)
    
    def __str__(self) -> str:
        return self.name