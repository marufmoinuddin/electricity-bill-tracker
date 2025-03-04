# DPDC Electricity Tracker - Django Backend Implementation Guide

This comprehensive guide outlines the implementation of a Django-based backend service for tracking electricity bill consumption from DPDC (Dhaka Power Distribution Company). The service fetches balance data hourly, calculates usage metrics, and provides REST API endpoints for consumption analytics.

## Table of Contents
1. [Project Overview](#project-overview)
2. [Prerequisites](#prerequisites)
3. [Project Setup](#project-setup)
4. [Project Configuration](#project-configuration)
5. [Database Schema](#database-schema)
6. [API Implementation](#api-implementation)
7. [DPDC Integration](#dpdc-integration)
8. [Scheduled Tasks](#scheduled-tasks)
9. [Testing](#testing)
10. [Deployment](#deployment)
11. [Advanced Features](#advanced-features)
12. [Troubleshooting](#troubleshooting)
13. [Security Considerations](#security-considerations)

## Project Overview

This project creates a Django-based backend service that:
- Periodically fetches electricity balance from DPDC API
- Calculates hourly consumption by tracking balance changes
- Stores data in a PostgreSQL database
- Provides REST API endpoints for:
  - Daily usage statistics
  - Last 30 days usage
  - Monthly usage reporting
  - Historical trends

## Prerequisites

- Python 3.8+ installed
- PostgreSQL database server installed and running
- Basic knowledge of Django and REST APIs
- DPDC customer account details

## Project Setup

### Step 1: Environment Setup

First, create a virtual environment and install required packages:

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required packages
pip install django djangorestframework psycopg2-binary python-dotenv playwright requests
```

### Step 2: Install Playwright browsers

```bash
playwright install chromium
```

### Step 3: Create Django Project

```bash
# Create Django project
django-admin startproject dpdc_tracker
cd dpdc_tracker

# Create Django app
python manage.py startapp electricity_tracker
```

### Step 4: Setup Directory Structure

Ensure your project follows this structure:
```
dpdc_tracker/
├── dpdc_tracker/         # Project directory
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py       # Project settings
│   ├── urls.py           # Project URLs
│   └── wsgi.py
├── electricity_tracker/  # App directory
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── management/       # Management commands
│   │   ├── __init__.py
│   │   └── commands/
│   │       ├── __init__.py
│   │       └── fetch_balance.py
│   ├── migrations/
│   ├── models.py         # Database models
│   ├── serializers.py    # API serializers
│   ├── tests.py
│   ├── urls.py           # App URLs
│   └── views.py          # API views
├── dpdc.py               # DPDC integration code
├── .env                  # Environment variables
└── manage.py
```

## Project Configuration

### Step 1: Configure Environment Variables

Create `.env` file in the project root:

```
DPDC_CUSTOMER_NUMBER=6119123614
DB_NAME=dpdc_tracker
DB_USER=dpdc_user
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=your-django-secret-key
DEBUG=True
```

### Step 2: Update `settings.py`

Update `dpdc_tracker/settings.py` with the following configurations:

```python
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-default-key-for-development')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'electricity_tracker',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'dpdc_tracker.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'dpdc_tracker.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'dpdc_tracker'),
        'USER': os.getenv('DB_USER', 'dpdc_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'yourpassword'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Dhaka'  # Set timezone for Bangladesh
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ]
}
```

### Step 3: Configure Project URLs

Update `dpdc_tracker/urls.py`:

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/usage/', include('electricity_tracker.urls')),
]
```

## Database Schema

### Step 1: Define Models

Create the database models in `electricity_tracker/models.py`:

```python
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
            
        # Calculate hourly usage based on previous entry
        prev_entry = BalanceEntry.objects.order_by('-timestamp').first()
        if prev_entry:
            time_diff = self.timestamp - prev_entry.timestamp
            # Only calculate if previous entry is within reasonable time (less than 3 hours)
            if time_diff.total_seconds() < 10800:  # 3 hours = 10800 seconds
                self.hourly_usage = max(0, prev_entry.balance - self.balance)
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
```

### Step 2: Create Admin Interface

Update `electricity_tracker/admin.py`:

```python
from django.contrib import admin
from .models import BalanceEntry

@admin.register(BalanceEntry)
class BalanceEntryAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'balance', 'hourly_usage', 'customer_name', 'status')
    list_filter = ('status', 'timestamp')
    search_fields = ('customer_name', 'account_id')
    date_hierarchy = 'timestamp'
    readonly_fields = ('hourly_usage', 'original_balance')
```

### Step 3: Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

## API Implementation

### Step 1: Create Serializers

Create `electricity_tracker/serializers.py`:

```python
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
```

### Step 2: Create Views

Create `electricity_tracker/views.py`:

```python
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
            'daily_breakdown': daily_breakdown
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
    def get(self, request, year=None):
        if year is None:
            # Default to current year
            year = timezone.now().year
        
        try:
            year = int(year)
            
            # Calculate date range for the year
            start_date = datetime(year, 1, 1, tzinfo=timezone.get_current_timezone())
            end_date = datetime(year + 1, 1, 1, tzinfo=timezone.get_current_timezone())
            
            # Get monthly breakdown
            monthly_data = BalanceEntry.objects.filter(
                timestamp__gte=start_date,
                timestamp__lt=end_date
            ).annotate(
                month=TruncMonth('timestamp')
            ).values('month').annotate(
                total_usage=Sum('hourly_usage')
            ).order_by('month')
            
            # Calculate total for the year
            total = sum(item['total_usage'] for item in monthly_data)
            
            result = {
                'year': year,
                'total_usage': total,
                'monthly_breakdown': list(monthly_data)
            }
            
            return Response(result)
        except ValueError:
            return Response(
                {"error": "Invalid year parameter"},
                status=status.HTTP_400_BAD_REQUEST
            )
```

### Step 3: Configure App URLs

Create `electricity_tracker/urls.py`:

```python
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
```

## DPDC Integration

### Step 1: Place `dpdc.py` in Project Root

Ensure the `dpdc.py` file is placed in the project root directory as provided in the source code.

### Step 2: Create Management Command

Create the necessary directory structure and files:

```bash
mkdir -p electricity_tracker/management/commands
touch electricity_tracker/management/__init__.py
touch electricity_tracker/management/commands/__init__.py
```

Create `electricity_tracker/management/commands/fetch_balance.py`:

```python
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
                # Create entry in database
                entry = BalanceEntry.objects.create(
                    balance=balance_info['balance'],
                    account_id=balance_info['account_id'],
                    customer_name=balance_info['customer_name'],
                    status=balance_info['status'],
                    timestamp=timezone.now()
                )
                
                self.stdout.write(self.style.SUCCESS(f'Balance saved successfully: {balance_info["balance"]} Tk'))
                self.stdout.write(f'Calculated hourly usage: {entry.hourly_usage} Tk')
                return True
            else:
                self.stderr.write(self.style.ERROR('Failed to fetch balance - no data returned'))
                return False
                
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error fetching balance: {str(e)}'))
            logger.error(f"Error: {str(e)}", exc_info=True)
            return False
```

## Scheduled Tasks

### Step 1: Create System-Level Cron Job

To run the management command hourly, set up a cron job:

```bash
crontab -e
```

Add the following line to run the command every hour:

```
0 * * * * cd /path/to/dpdc_tracker && /path/to/python /path/to/dpdc_tracker/manage.py fetch_balance >> /path/to/logs/fetch_balance.log 2>&1
```

### Step 2: Alternative: Using Django Celery (Optional)

For more flexibility, you can use Celery for task scheduling:

1. Install Celery and Redis:
```bash
pip install celery redis django-celery-beat
```

2. Update `settings.py`:
```python
# Add to INSTALLED_APPS
INSTALLED_APPS += [
    'django_celery_beat',
]

# Celery settings
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Dhaka'
```

3. Create `dpdc_tracker/celery.py`:
```python
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dpdc_tracker.settings')

app = Celery('dpdc_tracker')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

4. Create `electricity_tracker/tasks.py`:
```python
from celery import shared_task
import subprocess
import os

@shared_task
def fetch_balance_task():
    """Celery task to fetch balance"""
    django_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    manage_py = os.path.join(django_path, 'manage.py')
    
    # Execute management command as a subprocess
    result = subprocess.run(
        ['python', manage_py, 'fetch_balance'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        return f"Success: {result.stdout}"
    else:
        return f"Error: {result.stderr}"
```

5. Configure periodic tasks in the Django admin after running migrations.

## Testing

### Step 1: Create Test Cases

Create `electricity_tracker/tests.py`:

```python
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from .models import BalanceEntry
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
import json

class BalanceEntryModelTest(TestCase):
    """Tests for the BalanceEntry model"""
    
    def test_hourly_usage_calculation(self):
        """Test that hourly usage is calculated correctly"""
        # Create first entry
        first_entry = BalanceEntry.objects.create(
            balance=1000.0,
            account_id="12345",
            customer_name="Test Customer",
            status="Active"
        )
        
        # Create second entry one hour later
        second_entry_time = first_entry.timestamp + timedelta(hours=1)
        second_entry = BalanceEntry.objects.create(
            balance=950.0,
            account_id="12345",
            customer_name="Test Customer",
            status="Active",
            timestamp=second_entry_time
        )
        
        # Usage should be 50.0
        self.assertEqual(second_entry.hourly_usage, 50.0)

class ApiEndpointTest(TestCase):
    """Tests for API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create some test data spanning multiple days
        now = timezone.now()
        
        # Create entries for today
        BalanceEntry.objects.create(balance=1000.0, timestamp=now - timedelta(hours=3))
        BalanceEntry.objects.create(balance=950.0, timestamp=now - timedelta(hours=2))
        BalanceEntry.objects.create(balance=900.0, timestamp=now - timedelta(hours=1))
        
        # Create entries for yesterday
        yesterday = now - timedelta(days=1)
        BalanceEntry.objects.create(balance=1200.0, timestamp=yesterday - timedelta(hours=3))
        BalanceEntry.objects.create(balance=1150.0, timestamp=yesterday - timedelta(hours=2))
        BalanceEntry.objects.create(balance=1100.0, timestamp=yesterday - timedelta(hours=1))
    
    def test_latest_balance_api(self):
        """Test the latest balance API endpoint"""
        url = reverse('latest_balance')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Latest entry should have balance of 900.0
        self.assertEqual(response.data['balance'], 900.0)
    
    def test_daily_usage_api(self):
        """Test the daily usage API endpoint"""
        url = reverse('daily_usage')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return data for at least 2 days
        self.assertTrue(len(response.data) >= 2)

def test_command():
    """Test the fetch_balance management command"""
    from django.core.management import call_command
    from io import StringIO
    
    # Redirect stdout to capture output
    output = StringIO()
    call_command('fetch_balance', stdout=output)
    
    # Check if command execution was successful
    result = output.getvalue()
    return "successfully" in result.lower()
```

### Step 2: Run Tests

```bash
python manage.py test
```

### Step 3: Manual Testing

1. Start the development server:
```bash
python manage.py runserver
```

2. Test API endpoints with curl or a browser:
```bash
# Get latest balance
curl http://localhost:8000/api/usage/latest/

# Get daily usage for last 7 days
curl http://localhost:8000/api/usage/daily/?days=7

# Get last 30 days usage
curl http://localhost:8000/api/usage/last30days/

# Get usage for current month
curl http://localhost:8000/api/usage/month/

# Get usage for specific month
curl http://localhost:8000/api/usage/month/2024/3/
```

## Deployment

### Step 1: Prepare for Production

1. Update `settings.py` for production:
```python
DEBUG = False
ALLOWED_HOSTS = ['your-domain.com', 'www.your-domain.com']

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

2. Collect static files:
```bash
python manage.py collectstatic
```

### Step 2: Deploy with Gunicorn and Nginx

1. Install Gunicorn (if not already installed):
   ```bash
   pip install gunicorn
   ```

2. Create a Systemd Service File:
   Create a systemd service file to manage the Gunicorn process. Create a file at `/etc/systemd/system/dpdc_tracker.service`:

   ```ini
   [Unit]
   Description=DPDC Tracker Django Application
   After=network.target

   [Service]
   User=your_username
   Group=your_groupname
   WorkingDirectory=/path/to/dpdc_tracker
   ExecStart=/path/to/venv/bin/gunicorn --workers 3 --bind unix:/path/to/dpdc_tracker/dpdc_tracker.sock dpdc_tracker.wsgi:application
   Restart=always
   RestartSec=5
   Environment="DJANGO_SETTINGS_MODULE=dpdc_tracker.settings"
   Environment="PATH=/path/to/venv/bin"

   [Install]
   WantedBy=multi-user.target
   ```

   Replace the following placeholders:
   - `your_username`: The user running the service.
   - `your_groupname`: The group of the user.
   - `/path/to/dpdc_tracker`: The absolute path to your Django project.
   - `/path/to/venv`: The absolute path to your virtual environment.

3. Enable and Start the Service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl start dpdc_tracker
   sudo systemctl enable dpdc_tracker
   ```

4. Check the Status:
   Ensure the service is running without errors:
   ```bash
   sudo systemctl status dpdc_tracker
   ```

5. Configure Nginx:
   Install Nginx if not already installed:
   ```bash
   sudo apt install nginx
   ```

   Create an Nginx configuration file for your project at `/etc/nginx/sites-available/dpdc_tracker`:

   ```nginx
   server {
       listen 80;
       server_name your-domain.com www.your-domain.com;

       location / {
           proxy_pass http://unix:/path/to/dpdc_tracker/dpdc_tracker.sock;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }

       location /static/ {
           alias /path/to/dpdc_tracker/staticfiles/;
       }

       location /media/ {
           alias /path/to/dpdc_tracker/media/;
       }

       error_page 500 502 503 504 /50x.html;
       location = /50x.html {
           root /usr/share/nginx/html;
       }
   }
   ```

   Replace the following placeholders:
   - `your-domain.com`: Your domain name.
   - `/path/to/dpdc_tracker`: The absolute path to your Django project.

6. Enable the Nginx Configuration:
   Create a symbolic link to enable the configuration:
   ```bash
   sudo ln -s /etc/nginx/sites-available/dpdc_tracker /etc/nginx/sites-enabled/
   ```

7. Test and Restart Nginx:
   Test the Nginx configuration for syntax errors:
   ```bash
   sudo nginx -t
   ```

   If the test is successful, restart Nginx:
   ```bash
   sudo systemctl restart nginx
   ```

8. Set Up SSL with Certbot:
   Install Certbot and obtain an SSL certificate:
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com -d www.your-domain.com
   ```

   Certbot will automatically configure Nginx to use HTTPS.

9. Verify Deployment:
   Visit your domain in a browser (e.g., `https://your-domain.com`) to ensure the application is running correctly.

---

## Advanced Features

### 1. User Authentication
- Add user authentication using Django REST Framework's token authentication or JWT.
- Create user roles (e.g., admin, viewer) to restrict access to certain endpoints.

### 2. Notifications
- Integrate email or SMS notifications for:
  - Low balance alerts.
  - Unusual usage patterns.
  - Monthly usage summaries.

### 3. Data Export
- Add endpoints to export usage data in CSV or Excel format.
- Implement a reporting feature for generating PDF reports.

### 4. Usage Predictions
- Use machine learning (e.g., scikit-learn) to predict future usage based on historical data.
- Add an endpoint to retrieve predicted usage for the next month.

### 5. API Rate Limiting
- Use Django REST Framework's throttling to limit API requests:
  ```python
  REST_FRAMEWORK = {
      'DEFAULT_THROTTLE_CLASSES': [
          'rest_framework.throttling.AnonRateThrottle',
          'rest_framework.throttling.UserRateThrottle'
      ],
      'DEFAULT_THROTTLE_RATES': {
          'anon': '100/day',
          'user': '1000/day'
      }
  }
  ```

---

## Troubleshooting

### 1. DPDC API Issues
- If the DPDC API fails to return data:
  - Check the `auth_token.txt` file for a valid token.
  - Verify that the customer number is correct.
  - Ensure Playwright is properly installed and configured.

### 2. Database Errors
- If PostgreSQL connection fails:
  - Verify the database credentials in `.env`.
  - Ensure PostgreSQL is running and accessible.
  - Check Django's `settings.py` for correct database configuration.

### 3. Celery Issues
- If scheduled tasks fail:
  - Ensure Redis is running.
  - Check Celery logs for errors:
    ```bash
    sudo journalctl -u celery
    ```

### 4. Nginx Errors
- If the site is inaccessible:
  - Check Nginx error logs:
    ```bash
    sudo tail -f /var/log/nginx/error.log
    ```
  - Verify the Gunicorn socket file exists and has the correct permissions.

---

## Security Considerations

### 1. Environment Variables
- Never commit `.env` files to version control.
- Use a secrets manager (e.g., AWS Secrets Manager) for production environments.

### 2. Database Security
- Use strong passwords for PostgreSQL.
- Restrict database access to specific IP addresses.

### 3. API Security
- Use HTTPS for all API requests.
- Implement authentication and authorization for sensitive endpoints.

### 4. Regular Updates
- Keep Django, PostgreSQL, and other dependencies up to date.
- Monitor for security vulnerabilities using tools like `django-security-check`.

---

This guide provides a comprehensive roadmap for implementing and deploying the DPDC Electricity Tracker backend. Let me know if you need further assistance!