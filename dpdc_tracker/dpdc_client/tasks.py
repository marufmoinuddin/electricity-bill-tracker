import asyncio
import logging
from celery import shared_task
from django.utils import timezone
from django.conf import settings
from .dpdc import get_balance_info
from api.models import BalanceRecord

logger = logging.getLogger('dpdc_tasks')

@shared_task
def collect_balance_data(customer_number=None):
    """
    Collect balance data and store in database
    """
    if not customer_number:
        customer_number = getattr(settings, "DPDC_CUSTOMER_NUMBER", "35067784")
    
    logger.info(f"Collecting balance data for customer {customer_number}")
    
    try:
        # Use asyncio to run async function synchronously
        balance_info = asyncio.run(get_balance_info(customer_number))
        
        if balance_info:
            # Save balance record to database
            BalanceRecord.objects.create(
                customer_number=customer_number,
                customer_name=balance_info.get('customerName', ''),
                account_id=balance_info.get('accountId', ''),
                balance=float(balance_info.get('balanceRemaining', 0)),
                connection_status=balance_info.get('connectionStatus', ''),
                customer_class=balance_info.get('customerClass', ''),
                mobile_number=balance_info.get('mobileNumber', ''),
                account_type=balance_info.get('accountType', ''),
                timestamp=timezone.now()
            )
            
            logger.info(f"Successfully saved balance record: {balance_info.get('balanceRemaining')} Tk")
            return True
        else:
            logger.error("Failed to get balance info")
            return False
    except Exception as e:
        logger.error(f"Error collecting balance data: {e}")
        return False

@shared_task
def collect_hourly_data():
    """
    Task to be run hourly to collect balance data
    """
    customer_number = getattr(settings, "DPDC_CUSTOMER_NUMBER", "35067784")
    return collect_balance_data(customer_number)