import json
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt

from .data_service import (
    load_supply_data,
    load_council_data,
    load_scout_logs,
    get_dashboard_summary,
    get_pod_bottleneck_rankings,
    simulate_fair_vs_naive_allocation,
    forecast_pod_crisis
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
def ml_forecast_view(request):
    """View rendering the ML predictions page."""
    from .ml_service import get_ml_forecasts
    forecasts = get_ml_forecasts()
    
    context = {
        "forecasts": forecasts,
        "username": request.user.username,
    }
    return render(request, "forecasting.html", context)


@login_required
def api_data_view(request):
    """JSON API providing structured datasets for dynamic frontend charts."""
    calibrate_param = request.GET.get("calibrate", "true").lower() == "true"
    impute_param = request.GET.get("impute", "true").lower() == "true"

    supply_records = load_supply_data(apply_calibration=calibrate_param, impute_missing=impute_param)
    council_records = load_council_data()
    scout_logs = load_scout_logs()
    summary = get_dashboard_summary(apply_calibration=calibrate_param)
    rankings = get_pod_bottleneck_rankings(apply_calibration=calibrate_param)

    return JsonResponse({
        "status": "success",
        "calibration_active": calibrate_param,
        "imputation_active": impute_param,
        "summary": summary,
        "bottleneck_rankings": rankings,
        "supply_records": supply_records,
        "council_records": council_records,
        "scout_logs": scout_logs,
    })

@login_required
def api_bottleneck_rankings_view(request):
    """API returning min-heap bottleneck priority rankings based on worst-case resource shortfall."""
    calibrate_param = request.GET.get("calibrate", "true").lower() == "true"
    rankings = get_pod_bottleneck_rankings(apply_calibration=calibrate_param)
    return JsonResponse({
        "status": "success",
        "rankings": rankings
    })

@csrf_exempt
@login_required
def api_simulate_allocation_view(request):
    """API simulating resource allocation under Naive vs Fair priority for custom available pool sizes."""
    pools = {"water": 6000.0, "food": 1000.0, "medicine": 500.0}

    if request.method == "POST":
        try:
            body = json.loads(request.body)
            if "water" in body:
                pools["water"] = float(body["water"])
            if "food" in body:
                pools["food"] = float(body["food"])
            if "medicine" in body:
                pools["medicine"] = float(body["medicine"])
        except Exception:
            pass
    elif request.method == "GET":
        if "water" in request.GET:
            pools["water"] = float(request.GET["water"])
        if "food" in request.GET:
            pools["food"] = float(request.GET["food"])
        if "medicine" in request.GET:
            pools["medicine"] = float(request.GET["medicine"])

    simulation = simulate_fair_vs_naive_allocation(pools)
    return JsonResponse({
        "status": "success",
        "simulation": simulation
    })

@login_required
def api_forecast_view(request):
    """API predicting daily stock depletion and runway under different peacock disruption levels."""
    disruption = request.GET.get("disruption", "none")
    try:
        days = int(request.GET.get("days", "7"))
    except ValueError:
        days = 7

    forecasts = forecast_pod_crisis(disruption_level=disruption, forecast_days=days)
    return JsonResponse({
        "status": "success",
        "disruption_level": disruption,
        "forecast_days": days,
        "forecasts": forecasts
    })

@login_required
def api_marketplace_view(request):
    """API returning transparent trading accounts, open order book offers, and recent transactions."""
    from .data_service import get_marketplace_data
    data = get_marketplace_data()
    return JsonResponse({
        "status": "success",
        "marketplace": data
    })

@csrf_exempt
@login_required
def api_trade_create_view(request):
    """API creating a new trade offer in the inter-pod order book."""
    from .data_service import create_trade_offer, get_marketplace_data
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST method required"}, status=405)

    try:
        body = json.loads(request.body)
        offer = create_trade_offer(
            seller_pod_id=body["seller_pod_id"],
            resource_offered=body["resource_offered"],
            amount_offered=body["amount_offered"],
            price_in_credits=body["price_in_credits"],
            wanted_resource=body.get("wanted_resource"),
            wanted_amount=body.get("wanted_amount", 0.0)
        )
        return JsonResponse({
            "status": "success",
            "message": f"Trade offer #{offer.id} created successfully for {offer.seller_pod.pod_name}",
            "marketplace": get_marketplace_data()
        })
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)

@csrf_exempt
@login_required
def api_trade_execute_view(request):
    """API executing a trade offer between a buyer pod and seller pod."""
    from .data_service import execute_trade_offer, get_marketplace_data
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST method required"}, status=405)

    try:
        body = json.loads(request.body)
        tx = execute_trade_offer(
            buyer_pod_id=body["buyer_pod_id"],
            offer_id=body["offer_id"]
        )
        return JsonResponse({
            "status": "success",
            "message": f"Trade transaction #{tx.id} executed successfully! {tx.buyer_pod.pod_name} bought {tx.amount} {tx.resource_type} for {tx.price_paid} BC.",
            "marketplace": get_marketplace_data()
        })
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)

@csrf_exempt
@login_required
def api_grant_subsidy_view(request):
    """API injecting Central Council subsidy credits into vulnerable pod wallets."""
    from .data_service import grant_council_subsidy, get_marketplace_data
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST method required"}, status=405)

    try:
        body = json.loads(request.body)
        wallet = grant_council_subsidy(
            pod_id=body["pod_id"],
            subsidy_amount=body["subsidy_amount"]
        )
        return JsonResponse({
            "status": "success",
            "message": f"Granted {body['subsidy_amount']} BC subsidy to {wallet.pod_name}. New Balance: {wallet.credit_balance} BC.",
            "marketplace": get_marketplace_data()
        })
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)

