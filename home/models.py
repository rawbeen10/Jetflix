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
    
    id = models.AutoField(primary_key=True)
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

class SuccessfulPayment(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='successful_payments')
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='success_record')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=100, unique=True)
    esewa_ref_id = models.CharField(max_length=100)
    payment_date = models.DateTimeField(auto_now_add=True)
    subscription_start = models.DateTimeField()
    subscription_end = models.DateTimeField()
    
    class Meta:
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"{self.user.username} - Rs.{self.amount} - {self.payment_date.strftime('%Y-%m-%d')}"
