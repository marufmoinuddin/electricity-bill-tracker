from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from django.db.models import Sum, Avg, Count
from django.db.models.functions import TruncDate, TruncMonth, TruncYear
from django.utils import timezone
from datetime import datetime, timedelta
from .models import BalanceEntry
from .serializers import BalanceEntrySerializer, DailyUsageSerializer, MonthlyUsageSerializer

class LatestBalanceAPI(APIView):
    """API endpoint to get the latest balance entry"""
    def get(self, request):
        latest_entry = BalanceEntry.objects.order_by('-timestamp').first()
        if latest_entry:
            serializer = BalanceEntrySerializer(latest_entry)
            return Response(serializer.data)
        return Response({"error": "No balance data available"}, status=status.HTTP_404_NOT_FOUND)

class BalanceHistoryAPI(generics.ListAPIView):
    """API endpoint to get balance history with pagination"""
    serializer_class = BalanceEntrySerializer
    
    def get_queryset(self):
        days = self.request.query_params.get('days', 1)
        try:
            days = int(days)
            if days < 1:
                days = 1
            start_date = timezone.now() - timedelta(days=days)
            return BalanceEntry.objects.filter(timestamp__gte=start_date)
        except ValueError:
            return BalanceEntry.objects.all()[:100]  # Default limit

class DailyUsageAPI(APIView):
    """API endpoint to get daily usage summary"""
    def get(self, request):
        days = self.request.query_params.get('days', 30)
        try:
            days = int(days)
            if days < 1:
                days = 30
            
            start_date = timezone.now() - timedelta(days=days)
            
            daily_data = BalanceEntry.objects.filter(
                timestamp__gte=start_date
            ).annotate(
                date=TruncDate('timestamp')
            ).values('date').annotate(
                total_usage=Sum('hourly_usage'),
                avg_balance=Avg('balance'),
                entry_count=Count('id')
            ).order_by('-date')
            
            serializer = DailyUsageSerializer(daily_data, many=True)
            return Response(serializer.data)
        except ValueError:
            return Response(
                {"error": "Invalid days parameter"},
                status=status.HTTP_400_BAD_REQUEST
            )

class Last30DaysUsageAPI(APIView):
    """API endpoint to get the last 30 days usage summary"""
    def get(self, request):
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        
        # Get total usage for last 30 days
        total = BalanceEntry.objects.filter(
            timestamp__gte=thirty_days_ago
        ).aggregate(
            total=Sum('hourly_usage'),
            avg_daily=Avg('hourly_usage') * 24  # Estimate daily average
        )
        
        # Get daily breakdown
        daily_breakdown = BalanceEntry.objects.filter(
            timestamp__gte=thirty_days_ago
        ).annotate(
            date=TruncDate('timestamp')
        ).values('date').annotate(
            total_usage=Sum('hourly_usage')
        ).order_by('-date')[:30]
        
        result = {
            'total_usage': total['total'] or 0.0,
            'avg_daily_usage': total['avg_daily'] or 0.0,
            'daily_breakdown': list(daily_breakdown)
        }
        
        return Response(result)

class MonthlyUsageAPI(APIView):
    """API endpoint to get monthly usage for a specific year/month"""
    def get(self, request, year=None, month=None):
        if year is None or month is None:
            # Default to current year/month
            today = timezone.now()
            year = today.year
            month = today.month
        
        try:
            year = int(year)
            month = int(month)
            
            # Validate month
            if month < 1 or month > 12:
                return Response(
                    {"error": "Month must be between 1 and 12"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Calculate date range for the month
            start_date = datetime(year, month, 1, tzinfo=timezone.get_current_timezone())
            if month == 12:
                end_date = datetime(year + 1, 1, 1, tzinfo=timezone.get_current_timezone())
            else:
                end_date = datetime(year, month + 1, 1, tzinfo=timezone.get_current_timezone())
            
            # Get total usage for the month
            total = BalanceEntry.objects.filter(
                timestamp__gte=start_date,
                timestamp__lt=end_date
            ).aggregate(
                total=Sum('hourly_usage')
            )['total'] or 0.0
            
            # Get daily breakdown
            daily_data = BalanceEntry.objects.filter(
                timestamp__gte=start_date,
                timestamp__lt=end_date
            ).annotate(
                date=TruncDate('timestamp')
            ).values('date').annotate(
                daily_usage=Sum('hourly_usage')
            ).order_by('date')
            
            # Calculate number of days with data
            days_with_data = daily_data.count()
            
            # Calculate average daily usage
            avg_daily_usage = total / days_with_data if days_with_data > 0 else 0
            
            result = {
                'year': year,
                'month': month,
                'total_usage': total,
                'avg_daily_usage': avg_daily_usage,
                'days_with_data': days_with_data,
                'daily_breakdown': list(daily_data)
            }
            
            return Response(result)
        except ValueError:
            return Response(
                {"error": "Invalid year or month parameters"},
                status=status.HTTP_400_BAD_REQUEST
            )

class YearlyUsageAPI(APIView):
    """API endpoint to get yearly usage summary"""