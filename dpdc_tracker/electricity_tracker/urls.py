from django.urls import path
from .views import (
    LatestBalanceAPI,
    BalanceHistoryAPI,
    DailyUsageAPI,
    Last30DaysUsageAPI,
    MonthlyUsageAPI,
    YearlyUsageAPI
)

urlpatterns = [
    path('latest/', LatestBalanceAPI.as_view(), name='latest_balance'),
    path('history/', BalanceHistoryAPI.as_view(), name='balance_history'),
    path('daily/', DailyUsageAPI.as_view(), name='daily_usage'),
    path('last30days/', Last30DaysUsageAPI.as_view(), name='last_30_days_usage'),
    path('month/<int:year>/<int:month>/', MonthlyUsageAPI.as_view(), name='monthly_usage'),
    path('month/', MonthlyUsageAPI.as_view(), name='current_month_usage'),
    path('year/<int:year>/', YearlyUsageAPI.as_view(), name='yearly_usage'),
    path('year/', YearlyUsageAPI.as_view(), name='current_year_usage'),
]