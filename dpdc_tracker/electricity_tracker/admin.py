from django.contrib import admin
from .models import BalanceEntry

@admin.register(BalanceEntry)
class BalanceEntryAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'balance', 'hourly_usage', 'customer_name', 'status')
    list_filter = ('status', 'timestamp')
    search_fields = ('customer_name', 'account_id')
    date_hierarchy = 'timestamp'
    readonly_fields = ('hourly_usage', 'original_balance')