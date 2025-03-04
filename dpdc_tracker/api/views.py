import asyncio
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import F, Max
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import BalanceRecord, DailyUsage, MonthlyUsage
from .serializers import BalanceRecordSerializer, DailyUsageSerializer, MonthlyUsageSerializer, CurrentBalanceSerializer
from dpdc_client.dpdc import get_balance_info
from dpdc_client.tasks import collect_balance_data

class BalanceRecordViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing balance records
    """
    queryset = BalanceRecord.objects.all()
    serializer_class = BalanceRecordSerializer
    
    def get_queryset(self):
        queryset = BalanceRecord.objects.all()
        customer = self.request.query_params.get('customer')
        days = self.request.query_params.get('days')
        
        if customer:
            queryset = queryset.filter(customer_number=customer)
        
        if days:
            try:
                days_ago = timezone.now() - timedelta(days=int(days))
                queryset = queryset.filter(timestamp__gte=days_ago)
            except ValueError:
                pass
        
        return queryset

class DailyUsageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing daily usage
    """
    queryset = DailyUsage.objects.all()
    serializer_class = DailyUsageSerializer
    
    def get_queryset(self):
        queryset = DailyUsage.objects.all()
        customer = self.request.query_params.get('customer')
        days = self.request.query_params.get('days')
        
        if customer:
            queryset = queryset.filter(customer_number=customer)
        
        if days:
            try:
                days_ago = timezone.now().date() - timedelta(days=int(days))
                queryset = queryset.filter(date__gte=days_ago)
            except ValueError:
                pass
        
        return queryset

class MonthlyUsageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing monthly usage
    """
    queryset = MonthlyUsage.objects.all()
    serializer_class = MonthlyUsageSerializer
    
    def get_queryset(self):
        queryset = MonthlyUsage.objects.all()
        customer = self.request.query_params.get('customer')
        year = self.request.query_params.get('year')
        
        if customer:
            queryset = queryset.filter(customer_number=customer)
        
        if year:
            try:
                queryset = queryset.filter(year=int(year))
            except ValueError:
                pass
        
        return queryset

class CurrentBalanceView(APIView):
    """
    Get current balance for a customer
    """
    def get(self, request, format=None):
        customer = request.query_params.get('customer', None)
        force_refresh = request.query_params.get('refresh', 'false').lower() == 'true'
        
        if not customer:
            return Response(
                {"error": "Customer number is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Check if we need fresh data
        if force_refresh:
            # Collect new data synchronously
            collect_balance_data.delay(customer)
            
        # Get the latest record
        latest_record = BalanceRecord.objects.filter(
            customer_number=customer
        ).order_by('-timestamp').first()
        
        if not latest_record:
            return Response(
                {"error": "No data available for this customer"}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        data = {
            "customer_number": latest_record.customer_number,
            "customer_name": latest_record.customer_name,
            "account_id": latest_record.account_id,
            "balance": latest_record.balance,
            "connection_status": latest_record.connection_status,
            "last_updated": latest_record.timestamp
        }
        
        serializer = CurrentBalanceSerializer(data)
        return Response(serializer.data)

@api_view(['POST'])
def force_data_collection(request):
    """
    Force an immediate data collection
    """
    customer = request.data.get('customer', None)
    
    if not customer:
        return Response(
            {"error": "Customer number is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
        
    # Schedule the task to run immediately
    task = collect_balance_data.delay(customer)
    
    return Response({
        "status": "Data collection scheduled",
        "task_id": task.id
    })

@api_view(['POST'])
def calculate_daily_usage(request):
    """
    Calculate and store daily usage from balance records
    """
    customer = request.data.get('customer', None)
    
    if not customer:
        return Response(
            {"error": "Customer number is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get all records for this customer
    records = BalanceRecord.objects.filter(
        customer_number=customer
    ).order_by('timestamp')
    
    if not records:
        return Response(
            {"error": "No data available for this customer"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Dictionary to store the last balance for each day
    daily_balances = {}
    
    # Group records by day and keep the last one for each day
    for record in records:
        day = record.timestamp.date()
        daily_balances[day] = record.balance
    
    # Convert to list of tuples (date, balance) and sort by date
    daily_data = sorted(daily_balances.items())
    
    # Calculate daily usage (difference between consecutive days)
    created_count = 0
    for i in range(1, len(daily_data)):
        prev_date, prev_balance = daily_data[i-1]
        curr_date, curr_balance = daily_data[i]
        
        # Calculate usage (negative values mean consumption)
        usage = prev_balance - curr_balance
        
        # Create or update daily usage record
        daily_usage, created = DailyUsage.objects.update_or_create(
            customer_number=customer,
            date=curr_date,
            defaults={'usage': usage}
        )
        
        if created:
            created_count += 1
    
    # Also calculate and update monthly records
    update_monthly_usage(customer)
    
    return Response({
        "status": "Daily usage calculated",
        "new_records": created_count,
        "total_days": len(daily_data) - 1
    })

def update_monthly_usage(customer):
    """Calculate monthly usage from daily records"""
    # Get all daily usage records for the customer
    daily_records = DailyUsage.objects.filter(customer_number=customer)
    
    # Group records by year and month
    monthly_usage = {}
    for record in daily_records:
        key = (record.date.year, record.date.month)
        if key not in monthly_usage:
            monthly_usage[key] = 0
        monthly_usage[key] += record.usage
    
    # Create or update monthly usage records
    for (year, month), usage in monthly_usage.items():
        MonthlyUsage.objects.update_or_create(
            customer_number=customer,
            year=year,
            month=month,
            defaults={'usage': usage}
        )