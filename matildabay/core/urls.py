from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('forecasting/', views.ml_forecast_view, name='forecasting'),
    path('api/data/', views.api_data_view, name='api_data'),
    path('api/bottleneck-rankings/', views.api_bottleneck_rankings_view, name='api_bottleneck_rankings'),
    path('api/simulate-allocation/', views.api_simulate_allocation_view, name='api_simulate_allocation'),
    path('api/forecast/', views.api_forecast_view, name='api_forecast'),
    path('api/marketplace/', views.api_marketplace_view, name='api_marketplace'),
    path('api/trade/create/', views.api_trade_create_view, name='api_trade_create'),
    path('api/trade/execute/', views.api_trade_execute_view, name='api_trade_execute'),
    path('api/grant-subsidy/', views.api_grant_subsidy_view, name='api_grant_subsidy'),
]
