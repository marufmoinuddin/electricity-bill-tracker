from django.db import models
from django.utils import timezone
import uuid

class BalanceEntry(models.Model):
    """
    Model to store electricity balance entries from DPDC
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(default=timezone.now)
    balance = models.FloatField(help_text="Current balance from DPDC in Taka")
    hourly_usage = models.FloatField(default=0, help_text="Calculated usage based on balance difference")
    original_balance = models.FloatField(null=True, blank=True, help_text="Original balance before calculations")
    
    # Optional fields for more detailed tracking
    account_id = models.CharField(max_length=20, blank=True, null=True)
    customer_name = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, blank=True, null=True)
    
    def save(self, *args, **kwargs):
        # Store original balance before calculations
        if self.original_balance is None:
            self.original_balance = self.balance
            
        # Ensure balance is a float
        try:
            self.balance = float(self.balance)
        except (ValueError, TypeError):
            self.balance = 0.0
            
        # Calculate hourly usage based on previous entry
        prev_entry = BalanceEntry.objects.order_by('-timestamp').first()
        if prev_entry:
            time_diff = self.timestamp - prev_entry.timestamp
            # Only calculate if previous entry is within reasonable time (less than 3 hours)
            if time_diff.total_seconds() < 10800:  # 3 hours = 10800 seconds
                try:
                    prev_balance = float(prev_entry.balance)
                    current_balance = float(self.balance)
                    self.hourly_usage = max(0, prev_balance - current_balance)
                except (ValueError, TypeError):
                    self.hourly_usage = 0
            else:
                self.hourly_usage = 0
        else:
            self.hourly_usage = 0
        
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Balance Entry"
        verbose_name_plural = "Balance Entries"
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['balance'])
        ]
    
    def __str__(self):
        return f"{self.timestamp.strftime('%Y-%m-%d %H:%M')}: {self.balance} Tk"