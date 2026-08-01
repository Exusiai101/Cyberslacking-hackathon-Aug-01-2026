import os
import csv
import re
from heapq import heapify, heappush, heappop
from pathlib import Path

# Paths to dataset files
BASE_DATA_DIR = Path("/home/scout/Desktop/Cyberslacking-hackathon-Aug-01-2026/Matilda Bay/Matilday Bay")
SUPPLY_CSV_PATH = BASE_DATA_DIR / "pod_supply_data" / "matilda_bay_pod_supply_data.csv"
COUNCIL_CSV_PATH = BASE_DATA_DIR / "pod_council_meetings" / "matilda_bay_council_meetings_data.csv"
SCOUT_LOGS_PATH = BASE_DATA_DIR / "pod_supply_data" / "pip_scout_logs.md"

def calculate_drone_offset(raw_records=None):
    """
    Calculate empirical drone under-reporting calibration offsets for water, food, and medicine.
    Compares stock readings between elder reports and drone scans on adjacent dates.
    """
    if raw_records is None:
        raw_records = _load_raw_supply_records()

    w_offsets, f_offsets, m_offsets = [], [], []

    # Group by pod_id ordered by report_date
    by_pod = {}
    for r in raw_records:
        by_pod.setdefault(r["pod_id"], []).append(r)

    for pod_id, pod_rows in by_pod.items():
        pod_rows.sort(key=lambda x: x["report_date"])
        for i in range(len(pod_rows) - 1):
            r1, r2 = pod_rows[i], pod_rows[i + 1]
            if r1["report_source"] == "elder_report" and r2["report_source"] == "scout_drone_scan":
                if r1["water_stock_l"] > 0 and r2["water_stock_l"] > 0:
                    cons = r1["water_consumption_lpd"]
                    deliv = r1["delivery_amount"] if r1["delivery_resource"] == "water" else 0.0
                    expected = max(0.0, r1["water_stock_l"] - cons + deliv)
                    diff = expected - r2["water_stock_l"]
                    if diff > 0:
                        w_offsets.append(diff)

                if r1["food_stock_kg"] > 0 and r2["food_stock_kg"] > 0:
                    cons = r1["food_consumption_kgpd"]
                    deliv = r1["delivery_amount"] if r1["delivery_resource"] == "food" else 0.0
                    expected = max(0.0, r1["food_stock_kg"] - cons + deliv)
                    diff = expected - r2["food_stock_kg"]
                    if diff > 0:
                        f_offsets.append(diff)

                if r1["medicine_stock_units"] > 0 and r2["medicine_stock_units"] > 0:
                    cons = r1["medicine_consumption_upd"]
                    deliv = r1["delivery_amount"] if r1["delivery_resource"] == "medicine" else 0.0
                    expected = max(0.0, r1["medicine_stock_units"] - cons + deliv)
                    diff = expected - r2["medicine_stock_units"]
                    if diff > 0:
                        m_offsets.append(diff)

    avg_water = round(sum(w_offsets) / len(w_offsets), 1) if w_offsets else 1467.1
    avg_food = round(sum(f_offsets) / len(f_offsets), 1) if f_offsets else 1101.8
    avg_med = round(sum(m_offsets) / len(m_offsets), 1) if m_offsets else 77.9

    drone_count = sum(1 for r in raw_records if r["report_source"] == "scout_drone_scan")
    elder_count = sum(1 for r in raw_records if r["report_source"] == "elder_report")

    return {
        "estimated_water_offset": avg_water,
        "estimated_food_offset": avg_food,
        "estimated_medicine_offset": avg_med,
        "drone_count": drone_count,
        "elder_count": elder_count,
        "sample_size": len(w_offsets),
    }

def _load_raw_supply_records():
    """Helper to parse raw CSV rows before imputation or calibration."""
    if not SUPPLY_CSV_PATH.exists():
        return []

    records = []
    with open(SUPPLY_CSV_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            parsed = {
                "report_date": row["report_date"],
                "pod_id": row["pod_id"],
                "pod_name": row["pod_name"],
                "population": int(row["population"]) if row["population"] else 0,
                "distance_from_hub_km": float(row["distance_from_hub_km"]) if row["distance_from_hub_km"] else 0.0,
                "peacock_disruption": row["peacock_disruption"],
                "water_stock_l": float(row["water_stock_l"]) if row["water_stock_l"] else 0.0,
                "food_stock_kg": float(row["food_stock_kg"]) if row["food_stock_kg"] else 0.0,
                "medicine_stock_units": float(row["medicine_stock_units"]) if row["medicine_stock_units"] else 0.0,
                "water_consumption_lpd": float(row["water_consumption_lpd"]) if row["water_consumption_lpd"] else 0.0,
                "food_consumption_kgpd": float(row["food_consumption_kgpd"]) if row["food_consumption_kgpd"] else 0.0,
                "medicine_consumption_upd": float(row["medicine_consumption_upd"]) if row["medicine_consumption_upd"] else 0.0,
                "delivery_resource": row["delivery_resource"],
                "delivery_amount": float(row["delivery_amount"]) if row["delivery_amount"] else 0.0,
                "water_runway_days": float(row["water_runway_days"]) if row["water_runway_days"] else 0.0,
                "food_runway_days": float(row["food_runway_days"]) if row["food_runway_days"] else 0.0,
                "medicine_runway_days": float(row["medicine_runway_days"]) if row["medicine_runway_days"] else 0.0,
                "water_status": row["water_status"],
                "food_status": row["food_status"],
                "medicine_status": row["medicine_status"],
                "overall_status": row["overall_status"],
                "requested_assistance": row["requested_assistance"].lower() == "true",
                "report_source": row["report_source"],
                "is_missing": not row["water_stock_l"] or not row["food_stock_kg"],
                "is_imputed": False,
                "is_calibrated": False,
            }
            records.append(parsed)
    return records

def _derive_status(runway_days):
    """Derive resource status based on runway days."""
    if runway_days >= 10.0:
        return "stable"
    elif runway_days >= 5.0:
        return "warning"
    elif runway_days >= 1.0:
        return "critical"
    else:
        return "failed"

def _derive_overall_status(w_status, f_status, m_status):
    """Overall status is the worst of the three resource statuses."""
    order = {"failed": 0, "critical": 1, "warning": 2, "stable": 3}
    statuses = [w_status, f_status, m_status]
    worst = min(statuses, key=lambda s: order.get(s, 3))
    return worst

def load_supply_data(apply_calibration=False, impute_missing=True):
    """
    Load, impute missing values, and optionally calibrate drone readings for pod supply reports.
    """
    raw_records = _load_raw_supply_records()
    if not raw_records:
        return []

    offsets = calculate_drone_offset(raw_records) if apply_calibration else None

    # Group by pod for sequential imputation & calibration
    by_pod = {}
    for r in raw_records:
        by_pod.setdefault(r["pod_id"], []).append(r)

    processed_records = []

    for pod_id in sorted(by_pod.keys()):
        pod_rows = sorted(by_pod[pod_id], key=lambda x: x["report_date"])

        recent_w_cons = []
        recent_f_cons = []
        recent_m_cons = []

        for i, row in enumerate(pod_rows):
            if impute_missing and row["is_missing"]:
                row["is_imputed"] = True
                if i > 0:
                    prev = pod_rows[i - 1]
                    w_cons = sum(recent_w_cons) / len(recent_w_cons) if recent_w_cons else prev["water_consumption_lpd"]
                    f_cons = sum(recent_f_cons) / len(recent_f_cons) if recent_f_cons else prev["food_consumption_kgpd"]
                    m_cons = sum(recent_m_cons) / len(recent_m_cons) if recent_m_cons else prev["medicine_consumption_upd"]

                    w_deliv = row["delivery_amount"] if row["delivery_resource"] == "water" else 0.0
                    f_deliv = row["delivery_amount"] if row["delivery_resource"] == "food" else 0.0
                    m_deliv = row["delivery_amount"] if row["delivery_resource"] == "medicine" else 0.0

                    row["water_consumption_lpd"] = w_cons
                    row["food_consumption_kgpd"] = f_cons
                    row["medicine_consumption_upd"] = m_cons

                    row["water_stock_l"] = max(0.0, prev["water_stock_l"] - w_cons + w_deliv)
                    row["food_stock_kg"] = max(0.0, prev["food_stock_kg"] - f_cons + f_deliv)
                    row["medicine_stock_units"] = max(0.0, prev["medicine_stock_units"] - m_cons + m_deliv)
            else:
                if row["water_consumption_lpd"] > 0:
                    recent_w_cons.append(row["water_consumption_lpd"])
                    if len(recent_w_cons) > 7:
                        recent_w_cons.pop(0)
                if row["food_consumption_kgpd"] > 0:
                    recent_f_cons.append(row["food_consumption_kgpd"])
                    if len(recent_f_cons) > 7:
                        recent_f_cons.pop(0)
                if row["medicine_consumption_upd"] > 0:
                    recent_m_cons.append(row["medicine_consumption_upd"])
                    if len(recent_m_cons) > 7:
                        recent_m_cons.pop(0)

            if apply_calibration and row["report_source"] == "scout_drone_scan" and offsets:
                row["water_stock_l"] += offsets["estimated_water_offset"]
                row["food_stock_kg"] += offsets["estimated_food_offset"]
                row["medicine_stock_units"] += offsets["estimated_medicine_offset"]
                row["is_calibrated"] = True

            w_cons = row["water_consumption_lpd"] if row["water_consumption_lpd"] > 0 else 1.0
            f_cons = row["food_consumption_kgpd"] if row["food_consumption_kgpd"] > 0 else 1.0
            m_cons = row["medicine_consumption_upd"] if row["medicine_consumption_upd"] > 0 else 1.0

            row["water_runway_days"] = round(row["water_stock_l"] / w_cons, 1)
            row["food_runway_days"] = round(row["food_stock_kg"] / f_cons, 1)
            row["medicine_runway_days"] = round(row["medicine_stock_units"] / m_cons, 1)

            row["water_status"] = _derive_status(row["water_runway_days"])
            row["food_status"] = _derive_status(row["food_runway_days"])
            row["medicine_status"] = _derive_status(row["medicine_runway_days"])
            row["overall_status"] = _derive_overall_status(row["water_status"], row["food_status"], row["medicine_status"])

            processed_records.append(row)

    processed_records.sort(key=lambda x: (x["report_date"], x["pod_id"]))
    return processed_records

def load_council_data():
    """Load and process council meeting allocation records."""
    if not COUNCIL_CSV_PATH.exists():
        return []

    records = []
    with open(COUNCIL_CSV_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            parsed = {
                "event_id": int(row["event_id"]),
                "event_date": row["event_date"],
                "pod_id": row["pod_id"],
                "pod_name": row["pod_name"],
                "population": int(row["population"]) if row["population"] else 0,
                "vulnerable_count": int(row["vulnerable_count"]) if row["vulnerable_count"] else 0,
                "vulnerable_pct": float(row["vulnerable_pct"]) if row["vulnerable_pct"] else 0.0,
                "resource_type": row["resource_type"],
                "need_status": row["need_status"],
                "request_submitted": row["request_submitted"].lower() == "true",
                "amount_requested": float(row["amount_requested"]) if row["amount_requested"] else 0.0,
                "estimated_true_need": float(row["estimated_true_need"]) if row["estimated_true_need"] else 0.0,
                "distance_from_hub_km": float(row["distance_from_hub_km"]) if row["distance_from_hub_km"] else 0.0,
                "delivery_difficulty": row["delivery_difficulty"],
                "days_since_last_successful_delivery": int(row["days_since_last_successful_delivery"]) if row["days_since_last_successful_delivery"] else 0,
                "prior_unfulfilled_requests": int(row["prior_unfulfilled_requests"]) if row["prior_unfulfilled_requests"] else 0,
                "pool_available_that_resource": float(row["pool_available_that_resource"]) if row["pool_available_that_resource"] else 0.0,
                "naive_priority_score": float(row["naive_priority_score"]) if row["naive_priority_score"] else 0.0,
                "naive_priority_rank": int(row["naive_priority_rank"]) if row["naive_priority_rank"] else 0,
                "fair_priority_score": float(row["fair_priority_score"]) if row["fair_priority_score"] else 0.0,
                "fair_priority_rank": int(row["fair_priority_rank"]) if row["fair_priority_rank"] else 0,
                "amount_allocated": float(row["amount_allocated"]) if row["amount_allocated"] else 0.0,
                "unmet_amount": float(row["unmet_amount"]) if row["unmet_amount"] else 0.0,
            }
            records.append(parsed)
    return records

def load_scout_logs():
    """Load field notes from Pip's Scout Logs with structured tags and categories."""
    if not SCOUT_LOGS_PATH.exists():
        return []

    content = SCOUT_LOGS_PATH.read_text(encoding="utf-8")
    entries = []
    raw_entries = re.split(r'##\s+', content)

    tag_mapping = {
        "stockpile is not the story": {
            "category": "Runway Dynamics",
            "tags": ["#StockpileVsConsumption", "#BurnRate", "#PredictiveForecasting"],
            "pod_association": "All Pods",
        },
        "kestrel": {
            "category": "Pod Analysis",
            "tags": ["#Pod1Kestrel", "#FoodDeficit", "#WaterPurificationSurplus"],
            "pod_association": "Pod 1 — Kestrel",
        },
        "marrow": {
            "category": "Pod Analysis",
            "tags": ["#Pod2Marrow", "#WaterDeficit", "#MedicineSurplus", "#WreckedBoats"],
            "pod_association": "Pod 2 — Marrow",
        },
        "tallowfen": {
            "category": "Pod Analysis",
            "tags": ["#Pod3Tallowfen", "#HoardingFear", "#SurplusFood", "#DeHoardingIncentive"],
            "pod_association": "Pod 3 — Tallowfen",
        },
        "reeds end": {
            "category": "Pod Analysis",
            "tags": ["#Pod4ReedsEnd", "#SilentNeed", "#UnreportedShortage", "#DistancePenalty"],
            "pod_association": "Pod 4 — Reed's End",
        },
        "missing days": {
            "category": "Data Pipeline",
            "tags": ["#MissingTelemetry", "#DataImputation", "#RemotePodGaps"],
            "pod_association": "Pod 4 — Reed's End",
        },
        "delivery is not always": {
            "category": "Courier Operations",
            "tags": ["#UncoordinatedCouriers", "#ResourceMismatch", "#BottleneckRouting"],
            "pod_association": "Courier Network",
        },
        "drone reads a little low": {
            "category": "Sensor Calibration",
            "tags": ["#DroneSensorBias", "#CalibrationOffset", "#ElderVsDrone"],
            "pod_association": "Scout Drones",
        },
    }

    for raw in raw_entries:
        if not raw.strip() or raw.startswith("# "):
            continue
        lines = raw.strip().split("\n")
        title = lines[0].strip()
        body_lines = [l for l in lines[1:] if not l.startswith("---")]
        body = "\n".join(body_lines).strip()

        matched_meta = {
            "category": "General Scout Note",
            "tags": ["#FieldScout"],
            "pod_association": "Matilda Bay",
        }
        lower_title = title.lower()
        for key, meta in tag_mapping.items():
            if key in lower_title:
                matched_meta = meta
                break

        entries.append({
            "title": title,
            "content": body,
            "category": matched_meta["category"],
            "tags": matched_meta["tags"],
            "pod_association": matched_meta["pod_association"],
        })
    return entries

def get_pod_bottleneck_rankings(apply_calibration=True):
    """
    Ranks pods by their single worst resource shortfall (min of netWater, netFood, netMedicine)
    using a tie-break safe min-heap, directly implementing the logic from pod_fixed.py.
    """
    supply_records = load_supply_data(apply_calibration=apply_calibration, impute_missing=True)
    
    latest_per_pod = {}
    for r in supply_records:
        pod_id = r["pod_id"]
        if pod_id not in latest_per_pod or r["report_date"] > latest_per_pod[pod_id]["report_date"]:
            latest_per_pod[pod_id] = r

    priority_heap = []
    heapify(priority_heap)

    counter = 0
    for pod_id, pod in sorted(latest_per_pod.items()):
        net_water = pod["water_stock_l"] - (7 * pod["water_consumption_lpd"])
        net_food = pod["food_stock_kg"] - (7 * pod["food_consumption_kgpd"])
        net_med = pod["medicine_stock_units"] - (7 * pod["medicine_consumption_upd"])

        worst_net = min(net_water, net_food, net_med)
        
        if worst_net == net_water:
            bottleneck_resource = "water"
            runway = pod["water_runway_days"]
        elif worst_net == net_food:
            bottleneck_resource = "food"
            runway = pod["food_runway_days"]
        else:
            bottleneck_resource = "medicine"
            runway = pod["medicine_runway_days"]

        item = {
            "pod_id": pod["pod_id"],
            "pod_name": pod["pod_name"],
            "population": pod["population"],
            "distance_km": pod["distance_from_hub_km"],
            "worst_net_shortfall": round(worst_net, 1),
            "bottleneck_resource": bottleneck_resource,
            "bottleneck_runway_days": runway,
            "net_water": round(net_water, 1),
            "net_food": round(net_food, 1),
            "net_medicine": round(net_med, 1),
            "overall_status": pod["overall_status"],
        }
        heappush(priority_heap, (worst_net, counter, item))
        counter += 1

    rankings = []
    rank = 1
    while priority_heap:
        _, _, item = heappop(priority_heap)
        item["bottleneck_priority_rank"] = rank
        rankings.append(item)
        rank += 1

    return rankings

def simulate_fair_vs_naive_allocation(pools=None):
    """
    Simulates resource allocation under Naive Priority (distance-based) vs.
    Fair Priority (vulnerability, urgency, neglect history, and silent need bonus).
    """
    if pools is None:
        pools = {"water": 6000.0, "food": 1000.0, "medicine": 500.0}

    council_records = load_council_data()
    if not council_records:
        return {}

    latest_date = max(c["event_date"] for c in council_records)
    meeting_records = [c for c in council_records if c["event_date"] == latest_date]

    results = {}
    for resource, available_amount in pools.items():
        res_records = [c for c in meeting_records if c["resource_type"] == resource]
        if not res_records:
            res_records = [c for c in council_records if c["resource_type"] == resource]
            if res_records:
                latest_date_res = max(c["event_date"] for c in res_records)
                res_records = [c for c in res_records if c["event_date"] == latest_date_res]

        # 1. Naive Priority Allocation (Closest distance first, only considers requested_amount)
        naive_sorted = sorted(res_records, key=lambda x: x["distance_from_hub_km"])
        pool_left = float(available_amount)
        naive_allocations = {}
        for r in naive_sorted:
            pod_id = r["pod_id"]
            req = r["amount_requested"] if r["request_submitted"] else 0.0
            allocated = min(pool_left, req)
            pool_left -= allocated
            naive_allocations[pod_id] = {
                "rank": naive_sorted.index(r) + 1,
                "amount_allocated": round(allocated, 1),
                "unmet_amount": round(max(0.0, r["estimated_true_need"] - allocated), 1),
            }

        # 2. Fair Priority Allocation (Weighted by true need, vulnerability, neglect, silent need)
        fair_scored = []
        for r in res_records:
            # Use the canonical fair priority score from the council records dataset
            fair_score = r["fair_priority_score"]
            fair_scored.append((fair_score, r))

        fair_sorted = [item[1] for item in sorted(fair_scored, key=lambda x: x[0], reverse=True)]
        
        pool_left = float(available_amount)
        fair_allocations = {}
        for r in fair_sorted:
            pod_id = r["pod_id"]
            need = r["estimated_true_need"]
            allocated = min(pool_left, need)
            pool_left -= allocated
            fair_allocations[pod_id] = {
                "rank": fair_sorted.index(r) + 1,
                "amount_allocated": round(allocated, 1),
                "unmet_amount": round(max(0.0, need - allocated), 1),
            }

        pod_comparisons = []
        for r in res_records:
            pod_id = r["pod_id"]
            n_alloc = naive_allocations.get(pod_id, {"rank": 99, "amount_allocated": 0, "unmet_amount": r["estimated_true_need"]})
            f_alloc = fair_allocations.get(pod_id, {"rank": 99, "amount_allocated": 0, "unmet_amount": r["estimated_true_need"]})
            
            pod_comparisons.append({
                "pod_id": r["pod_id"],
                "pod_name": r["pod_name"],
                "request_submitted": r["request_submitted"],
                "estimated_true_need": r["estimated_true_need"],
                "naive_rank": n_alloc["rank"],
                "naive_allocated": n_alloc["amount_allocated"],
                "naive_unmet": n_alloc["unmet_amount"],
                "fair_rank": f_alloc["rank"],
                "fair_allocated": f_alloc["amount_allocated"],
                "fair_unmet": f_alloc["unmet_amount"],
                "fair_benefit_delta": round(f_alloc["amount_allocated"] - n_alloc["amount_allocated"], 1),
            })

        results[resource] = {
            "available_pool": available_amount,
            "total_need": sum(r["estimated_true_need"] for r in res_records),
            "pods": pod_comparisons,
        }

    return results

def forecast_pod_crisis(disruption_level="none", forecast_days=7):
    """
    Projects daily stock depletion and runway under different peacock disruption levels.
    """
    supply_records = load_supply_data(apply_calibration=True, impute_missing=True)
    
    latest_per_pod = {}
    for r in supply_records:
        pod_id = r["pod_id"]
        if pod_id not in latest_per_pod or r["report_date"] > latest_per_pod[pod_id]["report_date"]:
            latest_per_pod[pod_id] = r

    disruption_multipliers = {
        "none": 1.0,
        "minor": 1.25,
        "major": 1.60,
    }
    multiplier = disruption_multipliers.get(disruption_level.lower(), 1.0)

    forecasts = []
    for pod_id in sorted(latest_per_pod.keys()):
        pod = latest_per_pod[pod_id]

        w_cons = pod["water_consumption_lpd"] * multiplier
        f_cons = pod["food_consumption_kgpd"] * multiplier
        m_cons = pod["medicine_consumption_upd"] * multiplier

        w_runway = round(pod["water_stock_l"] / w_cons, 1) if w_cons > 0 else 999.0
        f_runway = round(pod["food_stock_kg"] / f_cons, 1) if f_cons > 0 else 999.0
        m_runway = round(pod["medicine_stock_units"] / m_cons, 1) if m_cons > 0 else 999.0

        worst_runway = min(w_runway, f_runway, m_runway)

        if worst_runway < 3.0:
            alert_tier = "CRITICAL_ALERT"
        elif worst_runway < 5.0:
            alert_tier = "WARNING_ALERT"
        else:
            alert_tier = "STABLE"

        trajectory = []
        curr_w = pod["water_stock_l"]
        curr_f = pod["food_stock_kg"]
        curr_m = pod["medicine_stock_units"]

        for day in range(1, forecast_days + 1):
            curr_w = max(0.0, curr_w - w_cons)
            curr_f = max(0.0, curr_f - f_cons)
            curr_m = max(0.0, curr_m - m_cons)
            trajectory.append({
                "day": day,
                "water_stock": round(curr_w, 1),
                "food_stock": round(curr_f, 1),
                "medicine_stock": round(curr_m, 1),
            })

        forecasts.append({
            "pod_id": pod["pod_id"],
            "pod_name": pod["pod_name"],
            "disruption_level": disruption_level,
            "consumption_multiplier": multiplier,
            "projected_water_runway": w_runway,
            "projected_food_runway": f_runway,
            "projected_medicine_runway": m_runway,
            "bottleneck_runway": worst_runway,
            "alert_tier": alert_tier,
            "daily_trajectory": trajectory,
        })

    return forecasts

def get_dashboard_summary(apply_calibration=True):
    """Build aggregated metrics for the overview dashboard."""
    supply_records = load_supply_data(apply_calibration=apply_calibration, impute_missing=True)
    council_records = load_council_data()
    scout_logs = load_scout_logs()

    latest_per_pod = {}
    for r in supply_records:
        pod_id = r["pod_id"]
        if pod_id not in latest_per_pod or r["report_date"] > latest_per_pod[pod_id]["report_date"]:
            latest_per_pod[pod_id] = r

    pods_overview = []
    total_pop = 0
    critical_count = 0
    imputed_count = sum(1 for r in supply_records if r.get("is_imputed"))

    for pod_id in sorted(latest_per_pod.keys()):
        r = latest_per_pod[pod_id]
        total_pop += r["population"]
        if r["overall_status"] in ["critical", "failed"]:
            critical_count += 1

        pods_overview.append({
            "pod_id": r["pod_id"],
            "pod_name": r["pod_name"],
            "population": r["population"],
            "distance_km": r["distance_from_hub_km"],
            "overall_status": r["overall_status"],
            "water_status": r["water_status"],
            "food_status": r["food_status"],
            "medicine_status": r["medicine_status"],
            "water_runway_days": r["water_runway_days"],
            "food_runway_days": r["food_runway_days"],
            "medicine_runway_days": r["medicine_runway_days"],
            "water_stock_l": r["water_stock_l"],
            "food_stock_kg": r["food_stock_kg"],
            "medicine_stock_units": r["medicine_stock_units"],
            "requested_assistance": r["requested_assistance"],
            "report_date": r["report_date"],
            "report_source": r["report_source"],
            "is_imputed": r.get("is_imputed", False),
            "is_calibrated": r.get("is_calibrated", False),
        })

    total_unmet = sum(c["unmet_amount"] for c in council_records)
    silent_need_pods = list(set(c["pod_name"] for c in council_records if not c["request_submitted"] and c["need_status"] in ["critical", "failed"]))

    raw_records = _load_raw_supply_records()
    calibration_details = calculate_drone_offset(raw_records)
    bottleneck_rankings = get_pod_bottleneck_rankings(apply_calibration=apply_calibration)
    marketplace = get_marketplace_data()

    return {
        "total_population": total_pop,
        "total_pods": len(pods_overview),
        "critical_pods_count": critical_count,
        "imputed_records_count": imputed_count,
        "total_unmet_council_need": round(total_unmet, 1),
        "silent_need_pods": silent_need_pods,
        "pods": pods_overview,
        "bottleneck_rankings": bottleneck_rankings,
        "drone_calibration": calibration_details,
        "marketplace": marketplace,
    }

def ensure_pod_wallets():
    """Seed initial pod trading wallets and order book offers if not present."""
    from core.models import PodWallet, TradeOffer, TradeTransaction

    default_wallets = [
        {"pod_id": "Pod 1", "pod_name": "Orca Pod 1 (Kestrel)", "credit_balance": 1500.0},
        {"pod_id": "Pod 2", "pod_name": "Orca Pod 2 (Marrow)", "credit_balance": 1200.0},
        {"pod_id": "Pod 3", "pod_name": "Orca Pod 3 (Tallowfen)", "credit_balance": 3000.0},
        {"pod_id": "Pod 4", "pod_name": "Orca Pod 4 (Reed's End)", "credit_balance": 800.0},
    ]

    wallets = {}
    for w in default_wallets:
        wallet, created = PodWallet.objects.get_or_create(
            pod_id=w["pod_id"],
            defaults={"pod_name": w["pod_name"], "credit_balance": w["credit_balance"]}
        )
        wallets[w["pod_id"]] = wallet

    if TradeOffer.objects.count() == 0:
        TradeOffer.objects.create(
            seller_pod=wallets["Pod 1"],
            resource_offered="water",
            amount_offered=1000.0,
            price_in_credits=250.0,
            wanted_resource="food",
            wanted_amount=200.0,
            status="open"
        )
        TradeOffer.objects.create(
            seller_pod=wallets["Pod 2"],
            resource_offered="medicine",
            amount_offered=150.0,
            price_in_credits=350.0,
            wanted_resource="water",
            wanted_amount=800.0,
            status="open"
        )
        TradeOffer.objects.create(
            seller_pod=wallets["Pod 3"],
            resource_offered="food",
            amount_offered=600.0,
            price_in_credits=450.0,
            wanted_resource="water",
            wanted_amount=1000.0,
            status="open"
        )

def get_marketplace_data():
    """Return transparent wallet balances, open trade offers, and completed transactions."""
    from core.models import PodWallet, TradeOffer, TradeTransaction

    ensure_pod_wallets()

    wallets = list(PodWallet.objects.all().values("id", "pod_id", "pod_name", "credit_balance", "escrow_balance"))
    offers = list(TradeOffer.objects.filter(status="open").values(
        "id", "seller_pod__pod_id", "seller_pod__pod_name", "resource_offered",
        "amount_offered", "price_in_credits", "wanted_resource", "wanted_amount", "created_at"
    ))
    transactions = list(TradeTransaction.objects.all().order_by("-transaction_date").values(
        "id", "buyer_pod__pod_id", "seller_pod__pod_id", "resource_type", "amount", "price_paid", "transaction_date"
    ))

    return {
        "wallets": wallets,
        "open_offers": offers,
        "recent_transactions": transactions,
    }

def create_trade_offer(seller_pod_id, resource_offered, amount_offered, price_in_credits, wanted_resource=None, wanted_amount=0.0):
    from core.models import PodWallet, TradeOffer
    ensure_pod_wallets()
    wallet = PodWallet.objects.get(pod_id=seller_pod_id)
    offer = TradeOffer.objects.create(
        seller_pod=wallet,
        resource_offered=resource_offered,
        amount_offered=float(amount_offered),
        price_in_credits=float(price_in_credits),
        wanted_resource=wanted_resource,
        wanted_amount=float(wanted_amount),
        status="open"
    )
    return offer

def execute_trade_offer(buyer_pod_id, offer_id):
    from core.models import PodWallet, TradeOffer, TradeTransaction
    ensure_pod_wallets()
    offer = TradeOffer.objects.get(id=offer_id, status="open")
    buyer_wallet = PodWallet.objects.get(pod_id=buyer_pod_id)
    seller_wallet = offer.seller_pod

    if buyer_wallet.pod_id == seller_wallet.pod_id:
        raise ValueError("A pod cannot execute its own trade offer.")

    if buyer_wallet.credit_balance < offer.price_in_credits:
        raise ValueError(f"Insufficient credits. {buyer_wallet.pod_name} has {buyer_wallet.credit_balance} BC, needs {offer.price_in_credits} BC.")

    buyer_wallet.credit_balance -= offer.price_in_credits
    seller_wallet.credit_balance += offer.price_in_credits

    buyer_wallet.save()
    seller_wallet.save()

    offer.status = "completed"
    offer.save()

    tx = TradeTransaction.objects.create(
        offer=offer,
        buyer_pod=buyer_wallet,
        seller_pod=seller_wallet,
        resource_type=offer.resource_offered,
        amount=offer.amount_offered,
        price_paid=offer.price_in_credits
    )
    return tx

def grant_council_subsidy(pod_id, subsidy_amount):
    from core.models import PodWallet
    ensure_pod_wallets()
    wallet = PodWallet.objects.get(pod_id=pod_id)
    wallet.credit_balance += float(subsidy_amount)
    wallet.save()
    return wallet

