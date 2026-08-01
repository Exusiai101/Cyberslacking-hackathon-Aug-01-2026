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

| Pod ID & Name          | Distance (km)      | Constrained Resource | Vulnerability                                                                                  | Key Paradox / Behavior                                                                                                                                                                                        |
| :--------------------- | :----------------- | :------------------- | :--------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Pod 1 — Kestrel**    | 3.2 km (Closest)   | **Food**             | 18 / 120 (15.0%)                                                                               | Operates water purification system (water is safe), but food reserves are sliding rapidly. Over-favored by naive distance metrics.                                                                            |
| **Pod 2 — Marrow**     | 5.8 km (Medium)    | **Water**            | 14 / 90 (15.6%)                                                                                | Holds massive medicine reserves, but wrecked boats prevent fetching water/food for themselves.                                                                                                                |
| **Pod 3 — Tallowfen**  | 4.0 km (fixed)     | None (Hoarding)      | Not tracked — no`vulnerable_count`/`vulnerable_pct` data exists for this pod in either dataset | Overproducing food; hoards supplies out of fear. Excluded from shortage council requests (zero rows in the meetings data).                                                                                    |
| **Pod 4 — Reed's End** | 11.5 km (Furthest) | **Water / All**      | 14 / 55 (25.5%)                                                                                | **Highest vulnerability percentage**. Stopped submitting requests starting the July 10 council meeting (`request_submitted` was still `True` on July 5) — a shift between two meetings, not a "Day 7" cutoff. |

> **Correction note:** Pod 3's distance is fixed (4.0 km, same pattern as every pod — not "Variable"). Pod 3 has no vulnerability figures anywhere in the data, so "Low" was an inference, not a sourced number. There is no Day 7 meeting — meetings fall only on days 5, 10, 15, 20, 25, 30 — and Pod 4's `request_submitted` flips from `True` to `False` between the day-5 and day-10 meetings.

---

## ❓ 2. Key Problems & Critical Analytical Questions

### Question 1: How do we identify and support "Silent Pods"?

- **Problem**: Pod 4 (Reed's End) stopped filing formal requests (`request_submitted = False`, `amount_requested = 0`) starting the July 10 meeting, after repeated delivery failures.
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

### Question 5: How do we surface unmet need when the total pool is insufficient?

- **Problem**: Even the fair-priority allocation logic cannot fully resolve some meetings — e.g. Pod 2's water pool is consistently ~6,500 L against ~11,000 L of estimated need. No ranking method manufactures supply that doesn't exist, and no marketplace trade manufactures it either if no pod holds a matching surplus.
- **Challenge**: A dashboard that only displays "who got what" from a pool, or "who traded what" in the marketplace, risks looking like the crisis is under control even when a large fraction of total need goes unfilled every cycle.
- **Solution Required**: Track and display **total unmet need per resource per meeting** — computed as `total_estimated_need − (council allocation + marketplace-settled trades)` — as a standalone metric, not folded into either the naive/fair comparison or the trade ledger.

---

## 📝 3. Master TODO List for Django Platform (`matildabay`)

```
┌───────────────────────────┐    ┌───────────────────────────┐    ┌───────────────────────────┐
│ Phase 1: Data Pipeline &  │    │ Phase 2: Core Algorithmic │    │ Phase 3: Dynamic UI &     │
│ Drone Calibration         │───►│ Engine & API Services     │───►│ Allocation Simulator      │
└───────────────────────────┘    └───────────────────────────┘    └───────────────────────────┘
```

### Phase 1: Data Pipeline & Preprocessing

- [x] **Empirical Drone Sensor Calibration**:
    - Update `calculate_drone_offset()` in `core/data_service.py` to dynamically calculate offset per resource (`water`, `food`, `medicine`) between adjacent drone vs. elder reports.
    - Automatically apply calibration adjustments to stock levels when `report_source == 'scout_drone_scan'`.
- [x] **Data Imputation & Telemetry Smoothing**:
    - Handle missing data entries (`NaN`) for distant pods using 7-day rolling window averages instead of zero-filling.
    - Emit a confidence flag when a gap exceeds 2 consecutive missing days (Pod 4's water telemetry is missing roughly a third of the time — a rolling average across a gap that large shouldn't be presented with the same confidence as a fully-measured value).
- [x] **Structured Scout Log Tagging**:
    - Parse log entries in `load_scout_logs()` with metadata tags (`#SilentPod`, `#DroneBias`, `#Bottleneck`) for UI banner highlights.

---

### Phase 2: Core Algorithmic Engine & API Services

- [ ] **Min-Heap Bottleneck Priority Service**:
    - Port priority algorithms from [`pod_fixed.py`](file:///home/scout/Desktop/Cyberslacking-hackathon-Aug-01-2026/Matilda%20Bay/Matilday%20Bay/pod_fixed.py#L81-L114) into a Django service function `get_pod_rankings()`.
    - Rank pods based on worst-case single resource shortfall ($\min(\text{netWater}, \text{netFood}, \text{netMedicine})$).
- [ ] **Fair Allocation Simulator Endpoint**:
- [ ]   - Create a new API route `/api/simulate-allocation/` in `core/views.py` accepting available resource pool inputs and returning comparative allocation outputs (Naive vs. Fair Priority).
    - Return the fair-priority formula's components explicitly (severity weight, silent-need bonus, neglect term, remoteness/vulnerability base) rather than a single opaque score — the remoteness/vulnerability component can't be fully decomposed with only three distinct pod profiles in the source data, and that limitation should stay visible in the output.
- [ ] **Total Pool & Unmet Need Tracker**:
    - For every simulated or historical meeting, compute and expose as first-class API fields: `pool_available`, `total_estimated_need`, `total_allocated`, and `total_unmet_need` per resource.
    - This must be computed and returned independently of whether the marketplace (Phase 5) resolves any of the gap through trade — unmet need is a pre-trade fact, and should stay reported even after trades reduce it, so the size of the original shortfall is never lost from the record.
- [ ] **Predictive Crisis Forecaster**:
    - Implement runway forecasting considering peacock disruption levels (`none`, `minor`, `major`) and flag pods hitting $< 3$ days runway.

---

### Phase 3: Frontend Visualization & Interactive Simulator

- [ ] **Interactive Allocation Simulator Widget**:
    - Build an interactive control panel in `templates/dashboard.html` allowing users to adjust resource pools and compare Naive vs. Fair allocations side-by-side.
- [ ] **Silent Need Alert Banner**:
    - Add a persistent alert component in the dashboard surfacing silent pods (e.g. Reed's End) that require proactive intervention.
- [ ] **Unmet Need Banner**:
    - Alongside the Silent Need banner, surface `total_unmet_need` per resource for the current cycle at the top level of the dashboard — not buried in a chart — so scarcity that no allocation or trade fully resolves stays visible by default.
- [ ] **Enhanced Chart.js Visualizations**:
    - Expand `static/js/dashboard.js` to include:
        1. Historical Stock Depletion & Projected Runway line chart.
        2. Council Meeting Unmet Needs breakdown bar chart (sourced from the Phase 2 Unmet Need Tracker).
        3. Delivery Efficiency & Resource Mismatch radar chart — requires defining a mismatch metric from `delivery_resource`/`delivery_amount` against same-day bottleneck status, since no such metric currently exists pre-computed in either CSV.
- [ ] **Courier Dispatch Export**:
    - Add a button on the dashboard to export optimized delivery recommendations as CSV/PDF.

---

### Phase 4: Authentication, Verification & Testing

- [ ] **Verification & Test Suite**:
    - Add unit tests in `core/tests.py` testing calibration math, missing value imputation, min-heap ordering, and unmet-need arithmetic (`total_estimated_need − total_allocated == total_unmet_need`, always).
    - Verify auth flows and API response schemas.
- [ ] Replace demo credentials before any real deployment.
- [ ] **UI Polish & Dark-Mode Theme**:
    - Ensure status badges (`critical`, `warning`, `stable`) conform to accessible, high-contrast dark mode styling in `static/css/styles.css`.

---

## 🪙 4. Inter-Pod Resource Marketplace & Currency System ("Bay Credits")

### The Economic Concept & Hackathon Value

Instead of relying solely on top-down council allocations, pods can engage in **peer-to-peer resource trading** backed by a local economy using **Bay Credits (🦪 BC)** or direct resource barter.

### Why This Perfectly Solves the Problem:

1. **Unlocks Complementary Surpluses**:
    - **Pod 1 (Kestrel)** has surplus **Water** (purification plant) $\leftrightarrow$ needs **Food**.
    - **Pod 2 (Marrow)** has surplus **Medicine** $\leftrightarrow$ needs **Water** and **Food**.
    - **Pod 3 (Tallowfen)** has surplus **Food** $\leftrightarrow$ needs economic incentive / security guarantees to stop hoarding.
2. **De-hoarding Incentive for Pod 3**:
    - Pod 3 hoards food out of fear. A currency/credit system allows Pod 3 to sell excess food for **Bay Credits** (or future delivery guarantees), transforming hoarded food into active liquid capital without risking their own safety.
3. **Equitable Subsidies for Pod 4 (Reed's End)**:
    - To prevent distant or isolated pods from being priced out, the Central Council can issue **Universal Need Subsidies / Stimulus Credits** directly to vulnerable pods like Reed's End, giving them purchasing power to buy water/food from Pod 1 & Pod 3.
    - **Open question, not yet resolved by this design**: subsidy credits are only real if backed by a reserved resource allocation. If the council issues vouchers without ring-fencing supply for them to redeem against, this recreates the original allocation shortfall with a currency layer on top rather than solving it. Any subsidy implementation needs to reserve actual resource units at issuance time, not just mint spendable credits.

### Fair-Priority-Gated Trade Execution _(new)_

An open marketplace during active scarcity risks reproducing the naive, leverage-based prioritization the fair-priority system exists to correct — Pod 1's food-for-water toll, charged from a position of transport advantage, is exactly this pattern already happening informally. To prevent the marketplace from formalizing that instead of fixing it:

- [ ] **Trade matching must consult `get_pod_rankings()` before execution, not just price/quantity.** When multiple pods bid for the same scarce surplus (e.g. both Pod 2 and Pod 4 want Pod 1's water), the trade engine should offer first refusal to whichever bidder has the higher fair-priority score for that resource, not simply the first or highest offer.
- [ ] **Cap exchange rates for resources currently at `critical` or `failed` status for the requesting pod.** A pod in acute crisis shouldn't be able to be priced out of a trade it fair-priority-qualifies for. Price caps apply specifically when the buying pod's own status for that resource is critical/failed — normal-status trades remain open market.
- [ ] **Subsidy grants to Pod 4 should scale with its fair-priority score, not a flat stipend.** Ties the marketplace's equity mechanism to the same need calculation already validated against the data, instead of introducing a second, separate notion of "how much help this pod deserves."

### Proposed Trade Matrix & Exchange Rates

| Pod                    | Offering (Surplus)  | Seeking (Deficit)         | Synergistic Trade Partner                                                           |
| :--------------------- | :------------------ | :------------------------ | :---------------------------------------------------------------------------------- |
| **Pod 1 (Kestrel)**    | 🚰 Water (Purified) | 🌾 Food                   | **Pod 3** (Food $\leftrightarrow$ Water) or **Pod 2** (Med $\leftrightarrow$ Water) |
| **Pod 2 (Marrow)**     | 💊 Medicine         | 🚰 Water & 🌾 Food        | **Pod 1** (Water $\leftrightarrow$ Med) & **Pod 3** (Food $\leftrightarrow$ Med)    |
| **Pod 3 (Tallowfen)**  | 🌾 Food             | 🦪 Bay Credits / Security | **Pod 1** & **Pod 2** (Buys surplus with Credits)                                   |
| **Pod 4 (Reed's End)** | 🎟️ Council Vouchers | 🚰 Water & 🌾 Food        | **Council-Subsidized Trades**                                                       |

---

### Phase 5: Inter-Pod Trading & Currency Implementation (Django)

- [ ] **Django Database Models (`core/models.py`)**:
    - `PodWallet`: Tracks `pod_id`, `credit_balance` (🦪 BC), and `escrow_balance`.
    - `TradeOffer`: Tracks `offering_pod`, `resource_offered` (`water`, `food`, `medicine`), `amount_offered`, `price_in_credits` or `wanted_resource`, `wanted_amount`, and `status` (`open`, `completed`, `cancelled`).
    - `TradeTransaction`: Records completed trades, timestamps, and delivery dispatch triggers.
    - `ResourceReservation`: Backs subsidy vouchers with an actual reserved quantity from the issuing pod's pool, so a voucher can't be issued without supply behind it.

- [ ] **Marketplace & Trading API (`core/views.py` & `core/urls.py`)**:
    - `GET /api/marketplace/`: List active trade offers and current exchange rates based on supply/demand.
    - `POST /api/trade/create/`: Allow pods to list surplus resources for sale/barter.
    - `POST /api/trade/execute/`: Execute a transaction, transferring credits and triggering courier delivery tasking. Must call `get_pod_rankings()` as part of match resolution when a trade offer has multiple competing bidders.

- [ ] **Marketplace UI & Trading Terminal (`dashboard.html` & `dashboard.js`)**:
    - Add a **"Matilda Bay Marketplace"** tab to the dashboard displaying:
        1. **Pod Credit Balances & Treasury**.
        2. **Active Order Book / Trade Offers**.
        3. **"Quick Trade / Swap" Modal** allowing users to simulate trades between pods.
        4. **Council Subsidy Grant Tool** to inject credits into Pod 4 (Reed's End), scaled to its fair-priority score.

---

## 👁️ 5. Transparent System Architecture & Public Pod Dashboard

### Core Principle: The Open Public Ledger

To build trust across isolated pods after a disaster, **every resource metric, council allocation, and marketplace trade must operate on a transparent system**.

The **Matilda Bay Live Dashboard** serves as a single source of truth accessible to all pod elders, couriers, and council members.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MATILDA BAY PUBLIC TRANSPARENCY SYSTEM                  │
├──────────────────────────────────────┬──────────────────────────────────────┤
│ 🌊 REAL-TIME POD TELEMETRY           │ ⚖️ PUBLIC GOVERNANCE & TRADING       │
│ • Live Stock (Water, Food, Meds)     │ • Naive vs. Fair Priority Comparison │
│ • Trailing 7-Day Consumption Rates   │ • Public Order Book (Inter-Pod Trades│
│ • Calibrated Drone vs Elder Reports  │ • Council Subsidy & Grant Ledger     │
│ • Silent Need Warning System         │ • Transparent Transaction History    │
│ • Total Pool & Unmet Need Metrics    │                                      │
└──────────────────────────────────────┴──────────────────────────────────────┘
```

### Key Transparency Modules:

1. **Public Pod Telemetry & Runway Meters**:
    - Every pod's exact stockpiles, population, vulnerability headcount (where tracked), and runway days are displayed publicly.
    - **Surfaces Silent Need**: Pod 4 (Reed's End)'s zero-request state does not hide their critical status — the dashboard transparently surfaces their true estimated need.
    - **On exposing Pod 3's hoarding publicly**: consider carefully before broadcasting this by default. Pod 3's holdout stems from a trust rupture after an intercepted convoy, not indifference — public exposure risks reading as shaming and hardening the position rather than inviting trade. A quieter, escrowed first exchange with Pod 3 is lower-risk than a public callout; the transparency principle can still apply to aggregate totals without singling out one pod's stockpile as a headline.

2. **Sensor Calibration Transparency**:
    - A global toggle allows users to view **Raw Drone Data** vs **Calibrated Drone Offset Data**, proving how sensor noise affected previous reporting.

3. **Total Pool & Unmet Need Ledger**:
    - Publicly displays, per resource per meeting: total pool available, total need, total allocated via council, total settled via marketplace trades, and the remainder still unmet. This is the number that keeps the system honest about what it can't yet solve.

4. **Public Trade Ledger & Order Book**:
    - All trade offers (`TradeOffer`) and credit balances (`PodWallet`) are open to the entire bay, preventing price gouging or secret backroom deals — enforced in part by the fair-priority trade caps in Phase 5.

5. **Allocation Audit Trail**:
    - Side-by-side comparison of **Naive Distance-based Rank** vs **Fair Need-based Rank** for every council meeting, exposing historical distance penalties on distant pods.

---

## 🎯 Summary of Next Steps

1. Execute **Phase 1** calibration & data service updates in `core/data_service.py`.
2. Implement **Phase 2** simulation, bottleneck priority, and total-pool/unmet-need tracking in `core/views.py`.
3. Connect **Phase 3** interactive charts, simulator widgets, and the unmet-need banner in `templates/dashboard.html` and `static/js/dashboard.js`.
4. Build **Phase 5** Trading Marketplace & Currency System (`PodWallet`, `TradeOffer`, `ResourceReservation`) with fair-priority-gated trade matching.
5. Enforce **Transparency Principles** across all API responses, dashboards, and transaction ledgers — including the total pool / unmet need ledger.
