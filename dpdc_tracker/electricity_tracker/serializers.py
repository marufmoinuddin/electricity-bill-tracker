from rest_framework import serializers
from .models import BalanceEntry

class BalanceEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = BalanceEntry
        fields = ['id', 'timestamp', 'balance', 'hourly_usage', 'customer_name', 'account_id', 'status']

class DailyUsageSerializer(serializers.Serializer):
    date = serializers.DateField()
    total_usage = serializers.FloatField()
    avg_balance = serializers.FloatField()
    entry_count = serializers.IntegerField()

class MonthlyUsageSerializer(serializers.Serializer):
    year = serializers.IntegerField()
    month = serializers.IntegerField()
    total_usage = serializers.FloatField()
    avg_daily_usage = serializers.FloatField()
    days_with_data = serializers.IntegerField()