# Matilda Bay Council Meetings Dataset

## Overview
--------
This dataset reflects the dynamics of interactions between the orca pods. 

It covers six bay-wide allocation council meetings (every 5 days, 5–30 July 2026) where pods with
a genuine shortage compete for a limited shared pool of water, food, or medicine. Each row is one
pod's situation and outcome at one meeting.

The dataset deliberately contrasts two approaches:
- **naive_priority**: ranks purely by how easy a pod is to reach (closest/easiest first) — this is
  what happens by default when nobody corrects for it.
- **fair_priority**: ranks by actual need — urgency, population vulnerability, and a history of
  being overlooked — and crucially, still surfaces a pod's need even if it stopped submitting
  requests.

## Column Descriptions
-------------------

**event_id / event_date**
Unit: integer / date
Identifies each of the six council meetings.

**pod_id / pod_name**
Unit: Categorical
Kestrel (Pod 1), Marrow (Pod 2), Tallowfen (Pod 3), Reed's End (Pod 4). Tallowfen never appears in
this dataset as it has hoarded all the supplies it needs.

**population**
Unit: number of orcas
Pod headcount.

**vulnerable_count / vulnerable_pct**
Unit: count / proportion
Number and share of the pod who are elderly, very young, or injured — those most at risk if
resources run out.

**resource_type**
Unit: Categorical (`water`, `food`, `medicine`)
Which resource this row's request/allocation concerns — each pod's known constrained resource
(Kestrel: food, Marrow: water, Reed's End: water).

**need_status**
Unit: Categorical (`stable`, `warning`, `critical`, `failed`)
How severe the pod's shortage of that resource is at this meeting.

**request_submitted**
Unit: Boolean
Whether the pod actually submitted a request at this meeting. Reed's End stops submitting requests
after day 7.

**amount_requested**
Unit: matches resource (litres/kg/units)
What the pod formally asked for. Zero when no request was submitted.

**estimated_true_need**
Unit: matches resource
An estimate of what the pod actually needs (enough to cover roughly the next week), independent of
whether they asked for it. Fair allocation is calculated against this, not against
`amount_requested`.

**distance_from_hub_km**
Unit: kilometres
Distance from the central courier hub.

**delivery_difficulty**
Unit: Categorical (`low`, `medium`, `high`)
Overall difficulty/risk of delivering to this pod (driven by distance and peacock disruption
frequency).

**days_since_last_successful_delivery**
Unit: days
How long it's been since this pod last received a successful delivery of this resource.

**prior_unfulfilled_requests**
Unit: integer count
Running count of previous meetings where this pod's need for this resource wasn't met — a pod's
neglect history.

**pool_available_that_resource**
Unit: matches resource
Total amount of this resource available to distribute across all pods at this meeting — always
less than total need.

**naive_priority_score / naive_priority_rank**
Unit: score / rank (1 = highest priority)
Priority if you rank purely by ease of delivery (closer = higher priority).

**fair_priority_score / fair_priority_rank**
Unit: score / rank (1 = highest priority)
Priority under a fairness-weighted scheme: urgency, vulnerability, neglect history, and a bonus
for pods with a genuine critical/failed need who submitted no request (silent need).

**amount_allocated / unmet_amount**
Unit: matches resource
What was actually given out (allocated in fair-priority order against the scarce pool) and what
remained unmet.
