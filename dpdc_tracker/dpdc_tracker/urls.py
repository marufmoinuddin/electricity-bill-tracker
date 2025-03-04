"""
URL configuration for dpdc_tracker project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'balance-records', views.BalanceRecordViewSet)
router.register(r'daily-usage', views.DailyUsageViewSet)
router.register(r'monthly-usage', views.MonthlyUsageViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('current-balance/', views.CurrentBalanceView.as_view(), name='current-balance'),
    path('force-data-collection/', views.force_data_collection, name='force-data-collection'),
    path('calculate-daily-usage/', views.calculate_daily_usage, name='calculate-daily-usage'),
]