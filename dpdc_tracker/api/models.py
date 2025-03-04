from django.db import models
from django.utils import timezone

class BalanceRecord(models.Model):
    """Model to store DPDC balance records"""
    customer_number = models.CharField(max_length=50)
    customer_name = models.CharField(max_length=255)
    account_id = models.CharField(max_length=100)
    balance = models.FloatField()
    connection_status = models.CharField(max_length=50)
    customer_class = models.CharField(max_length=100, blank=True, null=True)
    mobile_number = models.CharField(max_length=20, blank=True, null=True)
    account_type = models.CharField(max_length=50, blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['customer_number', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.customer_name} - {self.balance} Tk - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

class DailyUsage(models.Model):
    """Model to store calculated daily usage"""
    customer_number = models.CharField(max_length=50)
    date = models.DateField()
    usage = models.FloatField(help_text="Usage in Tk for the day")
    
    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['customer_number', 'date']),
            models.Index(fields=['date']),
        ]
        unique_together = ('customer_number', 'date')
    
    def __str__(self):
        return f"{self.customer_number} - {self.date} - {self.usage} Tk"

class MonthlyUsage(models.Model):
    """Model to store calculated monthly usage"""
    customer_number = models.CharField(max_length=50)
    year = models.IntegerField()
    month = models.IntegerField()  # 1-12
    usage = models.FloatField(help_text="Total usage in Tk for the month")
    
    class Meta:
        ordering = ['-year', '-month']
        indexes = [
            models.Index(fields=['customer_number', 'year', 'month']),
        ]
        unique_together = ('customer_number', 'year', 'month')
    
    def __str__(self):
        return f"{self.customer_number} - {self.year}-{self.month} - {self.usage} Tk"