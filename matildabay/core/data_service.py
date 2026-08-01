import os
import csv
import re
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

        # Track rolling averages for consumption
        recent_w_cons = []
        recent_f_cons = []
        recent_m_cons = []

        for i, row in enumerate(pod_rows):
            # Imputation logic for missing reports
            if impute_missing and row["is_missing"]:
                row["is_imputed"] = True
                if i > 0:
                    prev = pod_rows[i - 1]
                    # Estimate consumption from recent window or previous row
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

            # Drone Calibration logic
            if apply_calibration and row["report_source"] == "scout_drone_scan" and offsets:
                row["water_stock_l"] += offsets["estimated_water_offset"]
                row["food_stock_kg"] += offsets["estimated_food_offset"]
                row["medicine_stock_units"] += offsets["estimated_medicine_offset"]
                row["is_calibrated"] = True

            # Recalculate Runway Days & Statuses
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

    # Sort back by report_date
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

    # Category and tag mapping per entry title / keyword
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

        # Find matching tags
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

def get_dashboard_summary(apply_calibration=True):
    """Build aggregated metrics for the overview dashboard."""
    supply_records = load_supply_data(apply_calibration=apply_calibration, impute_missing=True)
    council_records = load_council_data()
    scout_logs = load_scout_logs()

    # Get latest report per pod
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

    # Council meeting metrics
    total_unmet = sum(c["unmet_amount"] for c in council_records)
    silent_need_pods = list(set(c["pod_name"] for c in council_records if not c["request_submitted"] and c["need_status"] in ["critical", "failed"]))

    raw_records = _load_raw_supply_records()
    calibration_details = calculate_drone_offset(raw_records)

    return {
        "total_population": total_pop,
        "total_pods": len(pods_overview),
        "critical_pods_count": critical_count,
        "imputed_records_count": imputed_count,
        "total_unmet_council_need": round(total_unmet, 1),
        "silent_need_pods": silent_need_pods,
        "pods": pods_overview,
        "drone_calibration": calibration_details,
    }
