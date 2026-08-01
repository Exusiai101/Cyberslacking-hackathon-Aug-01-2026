import json
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.contrib import messages

from .data_service import (
    load_supply_data,
    load_council_data,
    load_scout_logs,
    get_dashboard_summary
)

def ensure_demo_user():
    """Ensure a default user exists for easy testing."""
    if not User.objects.filter(username="demo_user").exists():
        User.objects.create_user(username="demo_user", password="password123", email="demo@matildabay.org")

def login_view(request):
    ensure_demo_user()
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect("home")
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = AuthenticationForm()

    return render(request, "auth/login.html", {"form": form})

def register_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully! Welcome to Matilda Bay Ops.")
            return redirect("home")
        else:
            messages.error(request, "Registration error. Please check the requirements below.")
    else:
        form = UserCreationForm()

    return render(request, "auth/register.html", {"form": form})

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("login")

@login_required
def home_view(request):
    summary = get_dashboard_summary(apply_calibration=True)
    scout_logs = load_scout_logs()
    
    context = {
        "summary": summary,
        "scout_logs": scout_logs,
        "username": request.user.username,
    }
    return render(request, "dashboard.html", context)

@login_required
def api_data_view(request):
    """JSON API providing structured datasets for dynamic frontend charts."""
    calibrate_param = request.GET.get("calibrate", "true").lower() == "true"
    impute_param = request.GET.get("impute", "true").lower() == "true"

    supply_records = load_supply_data(apply_calibration=calibrate_param, impute_missing=impute_param)
    council_records = load_council_data()
    scout_logs = load_scout_logs()
    summary = get_dashboard_summary(apply_calibration=calibrate_param)

    return JsonResponse({
        "status": "success",
        "calibration_active": calibrate_param,
        "imputation_active": impute_param,
        "summary": summary,
        "supply_records": supply_records,
        "council_records": council_records,
        "scout_logs": scout_logs,
    })
