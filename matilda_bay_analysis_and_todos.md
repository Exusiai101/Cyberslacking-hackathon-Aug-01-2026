# Matilda Bay Hackathon Analysis & Implementation TODO List

## 📌 Executive Summary
This document provides a complete breakdown of the **Matilda Bay Orca Pod Crisis Forecasting and Fair Resource Allocation** hackathon challenge, detailing the dataset structure, core problems identified, analytical questions, and a step-by-step TODO list for the Django application located at [`matildabay`](file:///home/scout/Desktop/Cyberslacking-hackathon-Aug-01-2026/matildabay).

---

## 📊 1. Dataset Breakdown & Context

The dataset covers **July 1–30, 2026**, following a major environmental disruption in Matilda Bay. It tracks four Orca Pods across daily supply telemetry and bi-weekly council allocation meetings.

### Data Sources
1. **Daily Pod Supply Telemetry** ([`matilda_bay_pod_supply_data.csv`](file:///home/scout/Desktop/Cyberslacking-hackathon-Aug-01-2026/Matilda%20Bay/Matilday%20Bay/pod_supply_data/matilda_bay_pod_supply_data.csv))
   - **Metrics**: Stock levels (`water_stock_l`, `food_stock_kg`, `medicine_stock_units`), daily consumption rates, runway days, status (`stable`, `warning`, `critical`, `failed`), courier deliveries, and reporting source (`elder_report` vs `scout_drone_scan`).
2. **Council Allocation Meetings** ([`matilda_bay_council_meetings_data.csv`](file:///home/scout/Desktop/Cyberslacking-hackathon-Aug-01-2026/Matilda%20Bay/Matilday%20Bay/pod_council_meetings/matilda_bay_council_meetings_data.csv))
   - **Metrics**: Allocation decisions every 5 days for scarce resource pools. Compares **Naive Priority** (distance-based) vs. **Fair Priority** (need, vulnerability, neglect, silent need).
3. **Field Scout Logs** ([`pip_scout_logs.md`](file:///home/scout/Desktop/Cyberslacking-hackathon-Aug-01-2026/Matilda%20Bay/Matilday%20Bay/pod_supply_data/pip_scout_logs.md))
   - Qualitative courier observations providing crucial domain hints (e.g., drone sensor offsets, uncoordinated delivery mismatches, silent pod behavior).

### Pod Profiles Matrix

| Pod ID & Name | Distance (km) | Constrained Resource | Vulnerability | Key Paradox / Behavior |
| :--- | :--- | :--- | :--- | :--- |
| **Pod 1 — Kestrel** | 3.2 km (Closest) | **Food** | 18 / 120 (15.0%) | Operates water purification system (water is safe), but food reserves are sliding rapidly. Over-favored by naive distance metrics. |
| **Pod 2 — Marrow** | 5.8 km (Medium) | **Water** | 14 / 90 (15.6%) | Holds massive medicine reserves, but wrecked boats prevent fetching water/food for themselves. |
| **Pod 3 — Tallowfen** | Variable | None (Hoarding) | Low | Overproducing food; hoards supplies out of fear. Excluded from shortage council requests. |
| **Pod 4 — Reed's End** | 11.5 km (Furthest) | **Water / All** | 14 / 55 (25.5%) | **Highest vulnerability percentage**. Stopped submitting requests after Day 7 due to systemic neglect ("Silent Pod"). |

---

## ❓ 2. Key Problems & Critical Analytical Questions

Based on exploratory analysis and courier field notes, the solution framework must address these core questions:

### Question 1: How do we identify and support "Silent Pods"?
- **Problem**: Pod 4 (Reed's End) stopped filing formal requests (`request_submitted = False`, `amount_requested = 0`) after Day 7 due to repeated delivery failures.
- **Challenge**: Standard allocation algorithms rank pods by formal requests or proximity, leaving silent pods with zero allocation.
- **Solution Required**: Calculate priority using `estimated_true_need` and apply a **Silent Need Bonus** for unsubmitted critical needs.

### Question 2: How do we correct for sensor measurement bias?
- **Problem**: Scout drone readings (`scout_drone_scan`) consistently report lower stockpile numbers than direct elder reports (`elder_report`).
- **Challenge**: Raw drone data causes false alarms or inaccurate runway predictions if uncalibrated.
- **Solution Required**: Estimate empirical deltas between drone scans and elder reports on adjacent days, applying an automated calibration correction factor.

### Question 3: How do we prevent single-resource masking in prioritization?
- **Problem**: In naive aggregation (e.g. summing total stock or net balances), a huge surplus in water or medicine masks a lethal food shortage.
- **Challenge**: As seen in [`pod_fixed.py`](file:///home/scout/Desktop/Cyberslacking-hackathon-Aug-01-2026/Matilda%20Bay/Matilday%20Bay/pod_fixed.py#L81-L114), pods must be prioritized by their **worst-case bottleneck resource** ($\min(\text{netWater}, \text{netFood}, \text{netMedicine})$).

### Question 4: How do we fix courier delivery mismatches?
- **Problem**: Deliveries are currently uncoordinated — couriers frequently drop off resources a pod doesn't urgently need (e.g. food to a pod suffering from a water emergency).
- **Solution Required**: Provide courier routing recommendations aligned with the pod's bottleneck resource status.

---

## 📝 3. Master TODO List for Django Platform (`matildabay`)

```
┌───────────────────────────┐    ┌───────────────────────────┐    ┌───────────────────────────┐
│ Phase 1: Data Pipeline &  │    │ Phase 2: Core Algorithmic │    │ Phase 3: Dynamic UI &     │
│ Drone Calibration         │───►│ Engine & API Services     │───►│ Allocation Simulator      │
└───────────────────────────┘    └───────────────────────────┘    └───────────────────────────┘
```

### Phase 1: Data Pipeline & Preprocessing
- [ ] **Empirical Drone Sensor Calibration**:
  - Update [`calculate_drone_offset()`](file:///home/scout/Desktop/Cyberslacking-hackathon-Aug-01-2026/matildabay/core/data_service.py#L108-L124) in [`core/data_service.py`](file:///home/scout/Desktop/Cyberslacking-hackathon-Aug-01-2026/matildabay/core/data_service.py) to dynamically calculate offset per resource (`water`, `food`, `medicine`) between adjacent drone vs. elder reports.
  - Automatically apply calibration adjustments to stock levels when `report_source == 'scout_drone_scan'`.
- [ ] **Data Imputation & Telemetry Smoothing**:
  - Handle missing data entries (`NaN`) for distant pods using 7-day rolling window averages instead of zero-filling.
- [ ] **Structured Scout Log Tagging**:
  - Parse log entries in [`load_scout_logs()`](file:///home/scout/Desktop/Cyberslacking-hackathon-Aug-01-2026/matildabay/core/data_service.py#L86-L106) with metadata tags (`#SilentPod`, `#DroneBias`, `#Bottleneck`) for UI banner highlights.

---

### Phase 2: Core Algorithmic Engine & API Services
- [ ] **Min-Heap Bottleneck Priority Service**:
  - Port priority algorithms from [`pod_fixed.py`](file:///home/scout/Desktop/Cyberslacking-hackathon-Aug-01-2026/Matilda%20Bay/Matilday%20Bay/pod_fixed.py#L81-L114) into a Django service function `get_pod_rankings()`.
  - Rank pods based on worst-case single resource shortfall ($\min(\text{netWater}, \text{netFood}, \text{netMedicine})$).
- [ ] **Fair Allocation Simulator Endpoint**:
  - Create a new API route `/api/simulate-allocation/` in [`core/views.py`](file:///home/scout/Desktop/Cyberslacking-hackathon-Aug-01-2026/matildabay/core/views.py) accepting available resource pool inputs and returning comparative allocation outputs (Naive vs. Fair Priority).
- [ ] **Predictive Crisis Forecaster**:
  - Implement runway forecasting considering peacock disruption levels (`none`, `minor`, `major`) and flag pods hitting $< 3$ days runway.

---

### Phase 3: Frontend Visualization & Interactive Simulator
- [ ] **Interactive Allocation Simulator Widget**:
  - Build an interactive control panel in [`templates/dashboard.html`](file:///home/scout/Desktop/Cyberslacking-hackathon-Aug-01-2026/matildabay/templates/dashboard.html) allowing users to adjust resource pools and compare Naive vs. Fair allocations side-by-side.
- [ ] **Silent Need Alert Banner**:
  - Add a persistent alert component in the dashboard surfacing silent pods (e.g. Reed's End) that require proactive intervention.
- [ ] **Enhanced Chart.js Visualizations**:
  - Expand [`static/js/dashboard.js`](file:///home/scout/Desktop/Cyberslacking-hackathon-Aug-01-2026/matildabay/static/js/dashboard.js) to include:
    1. Historical Stock Depletion & Projected Runway line chart.
    2. Council Meeting Unmet Needs breakdown bar chart.
    3. Delivery Efficiency & Resource Mismatch radar chart.
- [ ] **Courier Dispatch Export**:
  - Add a button on the dashboard to export optimized delivery recommendations as CSV/PDF.

---

### Phase 4: Authentication, Verification & Testing
- [ ] **Verification & Test Suite**:
  - Add unit tests in [`core/tests.py`](file:///home/scout/Desktop/Cyberslacking-hackathon-Aug-01-2026/matildabay/core/tests.py) testing calibration math, missing value imputation, and min-heap ordering.
  - Verify auth flows (`demo_user` / `password123`) and API response schemas.
- [ ] **UI Polish & Dark-Mode Theme**:
  - Ensure status badges (`critical`, `warning`, `stable`) conform to accessible, high-contrast dark mode styling in [`static/css/styles.css`](file:///home/scout/Desktop/Cyberslacking-hackathon-Aug-01-2026/matildabay/static/css/styles.css).

---

## 🎯 Summary of Next Steps
1. Execute **Phase 1** calibration & data service updates in [`core/data_service.py`](file:///home/scout/Desktop/Cyberslacking-hackathon-Aug-01-2026/matildabay/core/data_service.py).
2. Implement **Phase 2** simulation & bottleneck priority algorithms in [`core/views.py`](file:///home/scout/Desktop/Cyberslacking-hackathon-Aug-01-2026/matildabay/core/views.py).
3. Connect **Phase 3** interactive charts & simulator widgets in [`templates/dashboard.html`](file:///home/scout/Desktop/Cyberslacking-hackathon-Aug-01-2026/matildabay/templates/dashboard.html) and [`static/js/dashboard.js`](file:///home/scout/Desktop/Cyberslacking-hackathon-Aug-01-2026/matildabay/static/js/dashboard.js).
