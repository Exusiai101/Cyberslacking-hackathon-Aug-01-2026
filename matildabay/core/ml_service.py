import numpy as np
from sklearn.ensemble import RandomForestRegressor
from core.data_service import load_supply_data

# In-memory model cache: { "Pod 1": {"water": model, "food": model, "medicine": model}, ... }
_models = {}

def _prepare_training_data(pod_id, resource, records):
    """
    Prepare X and y for training.
    We predict the runway 'horizon' days into the future.
    To do this, we pair today's features with the actual runway 'horizon' days later in the dataset.
    Since dataset might be small, we'll augment it or just use a simpler direct mapping.
    Features: [population, stock, consumption, distance]
    Target: runway
    """
    X = []
    y = []
    
    # Sort by date
    pod_records = sorted([r for r in records if r["pod_id"] == pod_id], key=lambda x: x["report_date"])
    
    for r in pod_records:
        stock = r[f"{resource}_stock"] if f"{resource}_stock" in r else r.get(f"{resource}_stock_l", r.get(f"{resource}_stock_kg", r.get(f"{resource}_stock_units", 0)))
        cons = r[f"{resource}_consumption"] if f"{resource}_consumption" in r else r.get(f"{resource}_consumption_lpd", r.get(f"{resource}_consumption_kgpd", r.get(f"{resource}_consumption_upd", 1)))
        
        features = [
            r["population"],
            stock,
            cons,
            r["distance_from_hub_km"]
        ]
        
        # In a real scenario we'd use future actuals. Here we use current runway as target proxy for training
        # combined with a small synthetic decay to teach the model how stock depletion affects runway.
        runway = r.get(f"{resource}_runway_days", 0)
        
        X.append(features)
        y.append(runway)
        
        # Synthetic data to teach the model about consumption
        X.append([r["population"], max(0, stock - cons*7), cons, r["distance_from_hub_km"]])
        y.append(max(0, runway - 7))
        
    return np.array(X), np.array(y)

def train_pod_models():
    """Train Random Forest models for each pod and resource."""
    global _models
    records = load_supply_data(apply_calibration=True, impute_missing=True)
    pods = ["Pod 1", "Pod 2", "Pod 3", "Pod 4"]
    resources = ["water", "food", "medicine"]
    
    for pod in pods:
        _models[pod] = {}
        for res in resources:
            X, y = _prepare_training_data(pod, res, records)
            if len(X) > 0:
                model = RandomForestRegressor(n_estimators=50, random_state=42)
                model.fit(X, y)
                _models[pod][res] = model

def predict_runway(pod_id, resource, current_stock, consumption, population, distance, days_ahead):
    """Predict the runway for a specific pod 'days_ahead' into the future."""
    if not _models:
        train_pod_models()
        
    if pod_id not in _models or resource not in _models[pod_id]:
        return 0.0
        
    model = _models[pod_id][resource]
    # Predict the future stock
    future_stock = max(0, current_stock - (consumption * days_ahead))
    
    # Use ML model to predict runway based on future features
    features = np.array([[population, future_stock, consumption, distance]])
    predicted_runway = model.predict(features)[0]
    
    return round(float(predicted_runway), 1)

def get_ml_forecasts():
    """Get predictions for next day, next week, and next month for all pods."""
    records = load_supply_data(apply_calibration=True, impute_missing=True)
    
    # Get latest record per pod
    latest_per_pod = {}
    for r in records:
        pod_id = r["pod_id"]
        if pod_id not in latest_per_pod or r["report_date"] > latest_per_pod[pod_id]["report_date"]:
            latest_per_pod[pod_id] = r
            
    forecasts = []
    for pod_id in sorted(latest_per_pod.keys()):
        r = latest_per_pod[pod_id]
        
        pod_forecast = {
            "pod_id": pod_id,
            "pod_name": r["pod_name"],
            "population": r["population"],
            "predictions": {}
        }
        
        for res, res_name in [("water", "Water"), ("food", "Food"), ("medicine", "Medicine")]:
            stock = r.get(f"{res}_stock_l", r.get(f"{res}_stock_kg", r.get(f"{res}_stock_units", 0)))
            cons = r.get(f"{res}_consumption_lpd", r.get(f"{res}_consumption_kgpd", r.get(f"{res}_consumption_upd", 1)))
            dist = r["distance_from_hub_km"]
            pop = r["population"]
            
            pod_forecast["predictions"][res] = {
                "next_day": predict_runway(pod_id, res, stock, cons, pop, dist, 1),
                "next_week": predict_runway(pod_id, res, stock, cons, pop, dist, 7),
                "next_month": predict_runway(pod_id, res, stock, cons, pop, dist, 30),
            }
            
        forecasts.append(pod_forecast)
        
    return forecasts
