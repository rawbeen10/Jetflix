from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class Payment(models.Model):
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=500.00)
    transaction_id = models.CharField(max_length=100, unique=True)
    esewa_ref_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=30)
        super().save(*args, **kwargs)
    
    @property
    def is_active(self):
        return self.status == 'completed' and self.expires_at > timezone.now()
    
    def __str__(self):
        return f"{self.user.username} - Rs.{self.amount} ({self.status})"

# Create your models here.
