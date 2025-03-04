from rest_framework import serializers
from .models import BalanceRecord, DailyUsage, MonthlyUsage

class BalanceRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = BalanceRecord
        fields = '__all__'

class DailyUsageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyUsage
        fields = '__all__'

class MonthlyUsageSerializer(serializers.ModelSerializer):
    month_name = serializers.SerializerMethodField()
    
    class Meta:
        model = MonthlyUsage
        fields = ['id', 'customer_number', 'year', 'month', 'month_name', 'usage']
    
    def get_month_name(self, obj):
        months = [
            'January', 'February', 'March', 'April',
            'May', 'June', 'July', 'August',
            'September', 'October', 'November', 'December'
        ]
        return months[obj.month - 1]

class CurrentBalanceSerializer(serializers.Serializer):
    customer_number = serializers.CharField()
    customer_name = serializers.CharField()
    account_id = serializers.CharField()
    balance = serializers.FloatField()
    connection_status = serializers.CharField()
    last_updated = serializers.DateTimeField()