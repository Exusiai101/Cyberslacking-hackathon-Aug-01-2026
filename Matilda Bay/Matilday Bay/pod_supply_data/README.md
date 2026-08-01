# Matilda Bay Pod Supply Dataset

## Overview
--------
This dataset contains daily supply reports from four orca pods sheltering around Matilda Bay after
the Giant Peacock's feathers wrecked the western side of campus. It can be used to build a forecasting tool to predict which pod will run critically short of water, food, or medicine *before* it happens, rather than reacting once a pod is already in crisis.

The four pods:
- **Pod 1 — Kestrel**: controls the last working water purification system, but its food stores
  are nearly gone.
- **Pod 2 — Marrow**: holds a huge recovered medicine stockpile, but its boats and carts were
  wrecked, so almost nothing can be moved — including the water and food it needs for itself.
- **Pod 3 — Tallowfen**: has been overproducing food and is comfortably stocked on everything, but
  stopped sharing after a convoy was intercepted, and hoards out of fear rather than need.
- **Pod 4 — Reed's End**: the hardest pod to reach. Genuinely running low across the board, but the
  elders stopped asking for help after repeated requests were delayed or abandoned.

All reports are daily, covering **1–30 July 2026**. Reports come from two sources — direct elder
reports and salvaged scout drone scans — and reporting reliability differs by pod, especially for
Reed's End.

There is also a courier scout's field notes file (`pip_scout_logs.md`) with cryptic hints useful
for spotting patterns in the data.

## Column Descriptions
-------------------

**report_date**
Unit: Date (YYYY-MM-DD)
The day the report was recorded.

**pod_id / pod_name**
Unit: Categorical
Identifies which of the four pods (Pod 1–4 / Kestrel, Marrow, Tallowfen, Reed's End) the row
describes.

**population**
Unit: number of orcas
Pod headcount. Drives baseline daily consumption of every resource.

**distance_from_hub_km**
Unit: kilometres
Approximate distance from the central courier hub. Larger distances mean slower, riskier, and
less frequent deliveries.

**peacock_disruption**
Unit: Categorical (`none`, `minor`, `major`)
Whether smaller peacocks disrupted the pod's routes/cargo that day. Disruption raises consumption
(spoilage, rationing inefficiency, injuries) and increases the chance a scheduled delivery is
blocked entirely.

**water_stock_l / food_stock_kg / medicine_stock_units**
Unit: litres / kilograms / units
Reported remaining stockpile of each resource at the end of the day. These are *reported* values —
see `report_source` below, since scout drone readings carry a small calibration offset (find what this is
and remove it!).

**water_consumption_lpd / food_consumption_kgpd / medicine_consumption_upd**
Unit: per day
That day's actual consumption of each resource (litres/day, kg/day, units/day).

**delivery_resource / delivery_amount**
Unit: Categorical / matching unit
Whether a courier delivery reached the pod that day, which resource it carried (`water`, `food`,
`medicine`, or `none`), and how much. Because the courier network is uncoordinated, a delivery does
not necessarily carry the resource the pod is shortest on.

**water_runway_days / food_runway_days / medicine_runway_days**
Unit: days
Current stock divided by the pod's trailing 7-day average consumption for that resource — i.e. "at
this rate, how many days until this resource runs out."

**water_status / food_status / medicine_status**
Unit: Categorical (`stable`, `warning`, `critical`, `failed`)
Derived from runway:
- `stable`: 10+ days of runway
- `warning`: 5–10 days
- `critical`: 1–5 days
- `failed`: under 1 day / effectively depleted

**overall_status**
Unit: Categorical
The worst of the three resource statuses for that pod that day.

**requested_assistance**
Unit: Boolean
Whether the pod actively asked for help that day. Note: Reed's End stops requesting help after day
7 regardless of how bad things get.

**report_source**
Unit: Categorical (`elder_report`, `scout_drone_scan`)
Who filed the report. Scout drone scans carry a small consistent calibration offset.

## Known data quality issues
-------------------------
Some rows have missing values in the stock/consumption/runway columns — 
mirrors real reporting gaps, especially for Reed's End, whose reports are the least reliable
because of how hard the pod is to reach.
