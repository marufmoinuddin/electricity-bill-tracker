from django.core.management.base import BaseCommand
from django.utils import timezone
from electricity_tracker.models import BalanceEntry
import os
import sys
import logging
import asyncio

# Add project root to path to import dpdc.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Import the DPDC function
try:
    from dpdc import check_balance_for_customer
except ImportError:
    logging.error("Failed to import dpdc.py. Make sure it exists in the project root directory.")
    check_balance_for_customer = None

class Command(BaseCommand):
    help = 'Fetches current balance from DPDC and saves to database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--customer',
            type=str,
            help='DPDC customer number to use (overrides env variable)',
        )

    def handle(self, *args, **options):
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        logger = logging.getLogger('fetch_balance')
        
        # Ensure DPDC function is available
        if check_balance_for_customer is None:
            self.stderr.write(self.style.ERROR('DPDC integration not available. Aborting.'))
            return
        
        # Get customer number from options or environment
        customer_number = options.get('customer') or os.getenv("DPDC_CUSTOMER_NUMBER")
        
        if not customer_number:
            self.stderr.write(self.style.ERROR('No customer number provided. Set DPDC_CUSTOMER_NUMBER environment variable or use --customer option.'))
            return
        
        self.stdout.write(f"Fetching balance for customer {customer_number}...")
        
        try:
            # Get balance information
            balance_info = check_balance_for_customer(customer_number)
            
            if balance_info:
                # Check if there's already a balance entry with this value
                current_balance = float(balance_info['balance'])
                
                # Get the latest entry to compare
                latest_entry = BalanceEntry.objects.order_by('-timestamp').first()
                
                if latest_entry and latest_entry.balance == current_balance:
                    self.stdout.write(self.style.SUCCESS(f'No change in balance detected (still {current_balance} Tk). Skipping database entry.'))
                    return None
                
                # Create entry in database only if balance has changed or this is the first entry
                entry = BalanceEntry.objects.create(
                    balance=current_balance,
                    account_id=balance_info['account_id'],
                    customer_name=balance_info['customer_name'],
                    status=balance_info['status'],
                    timestamp=timezone.now()
                )

                self.stdout.write(self.style.SUCCESS(f'Balance changed - new value saved: {current_balance} Tk'))
                self.stdout.write(f'Calculated hourly usage: {entry.hourly_usage} Tk')
                return None
            else:
                self.stderr.write(self.style.ERROR('Failed to fetch balance - no data returned'))
                return None
                
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error fetching balance: {str(e)}'))
            logger.error(f"Error: {str(e)}", exc_info=True)
            return None