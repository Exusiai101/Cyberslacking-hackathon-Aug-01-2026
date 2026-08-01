import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

from core.models import PodWallet, TradeOffer, TradeTransaction
from core.data_service import (
    load_supply_data,
    load_council_data,
    load_scout_logs,
    calculate_drone_offset,
    get_pod_bottleneck_rankings,
    simulate_fair_vs_naive_allocation,
    forecast_pod_crisis,
    get_dashboard_summary,
    ensure_pod_wallets,
    get_marketplace_data,
    create_trade_offer,
    execute_trade_offer,
    grant_council_subsidy
)

class MatildaBayDataPipelineTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password123")

    def test_load_supply_data_imputation(self):
        """Test missing report imputation logic."""
        raw = load_supply_data(apply_calibration=False, impute_missing=False)
        imputed = load_supply_data(apply_calibration=False, impute_missing=True)

        raw_missing = sum(1 for r in raw if r.get("is_missing"))
        imputed_count = sum(1 for r in imputed if r.get("is_imputed"))

        self.assertEqual(raw_missing, 14)
        self.assertEqual(imputed_count, 14)

    def test_drone_calibration_offsets(self):
        """Test empirical drone under-reporting calibration calculation."""
        offsets = calculate_drone_offset()
        self.assertGreater(offsets["estimated_water_offset"], 1000.0)
        self.assertGreater(offsets["estimated_food_offset"], 500.0)
        self.assertGreater(offsets["estimated_medicine_offset"], 10.0)
        self.assertEqual(offsets["drone_count"], 31)
        self.assertEqual(offsets["elder_count"], 89)

    def test_scout_logs_parsing_and_tagging(self):
        """Test Pip's scout logs metadata tagging."""
        logs = load_scout_logs()
        self.assertGreaterEqual(len(logs), 8)
        
        first = logs[0]
        self.assertIn("category", first)
        self.assertIn("tags", first)
        self.assertIn("pod_association", first)

class MatildaBayAlgorithmTests(TestCase):
    def test_min_heap_bottleneck_rankings(self):
        """Test worst-case bottleneck shortfall min-heap rankings."""
        rankings = get_pod_bottleneck_rankings(apply_calibration=True)
        self.assertEqual(len(rankings), 4)

        for i in range(len(rankings) - 1):
            self.assertLessEqual(
                rankings[i]["worst_net_shortfall"],
                rankings[i + 1]["worst_net_shortfall"]
            )

        pod2_rank = next(r for r in rankings if r["pod_id"] == "Pod 2")
        self.assertEqual(pod2_rank["bottleneck_resource"], "water")

    def test_simulate_fair_vs_naive_allocation(self):
        """Test allocation simulation outputs."""
        pools = {"water": 6000.0, "food": 1000.0, "medicine": 500.0}
        sim = simulate_fair_vs_naive_allocation(pools)

        self.assertIn("water", sim)
        self.assertIn("food", sim)
        self.assertIn("medicine", sim)

        water_pods = sim["water"]["pods"]
        self.assertEqual(len(water_pods), 2)

    def test_forecast_pod_crisis(self):
        """Test crisis forecasting trajectories under disruption."""
        forecasts = forecast_pod_crisis(disruption_level="major", forecast_days=7)
        self.assertEqual(len(forecasts), 4)

        critical_pods = [f for f in forecasts if f["alert_tier"] == "CRITICAL_ALERT"]
        self.assertGreaterEqual(len(critical_pods), 2)

class MatildaBayMarketplaceTests(TestCase):
    def setUp(self):
        ensure_pod_wallets()

    def test_pod_wallets_seeding(self):
        wallets = PodWallet.objects.all()
        self.assertEqual(wallets.count(), 4)
        pod4 = PodWallet.objects.get(pod_id="Pod 4")
        self.assertEqual(pod4.credit_balance, 800.0)

    def test_create_and_execute_trade_offer(self):
        offer = create_trade_offer("Pod 3", "food", 500.0, 200.0)
        self.assertEqual(offer.status, "open")

        tx = execute_trade_offer("Pod 1", offer.id)
        self.assertEqual(tx.price_paid, 200.0)

        pod1_wallet = PodWallet.objects.get(pod_id="Pod 1")
        pod3_wallet = PodWallet.objects.get(pod_id="Pod 3")

        self.assertEqual(pod1_wallet.credit_balance, 1300.0)  # 1500 - 200
        self.assertEqual(pod3_wallet.credit_balance, 3200.0)  # 3000 + 200

    def test_grant_council_subsidy(self):
        wallet = grant_council_subsidy("Pod 4", 500.0)
        self.assertEqual(wallet.credit_balance, 1300.0)  # 800 + 500

class MatildaBayApiViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="demouser", password="password123")
        self.client.login(username="demouser", password="password123")

    def test_api_data_endpoint(self):
        response = self.client.get(reverse("api_data"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("summary", data)
        self.assertIn("marketplace", data["summary"])

    def test_api_bottleneck_rankings_endpoint(self):
        response = self.client.get(reverse("api_bottleneck_rankings"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(len(data["rankings"]), 4)

    def test_api_simulate_allocation_endpoint(self):
        response = self.client.post(
            reverse("api_simulate_allocation"),
            data=json.dumps({"water": 7000.0, "food": 1200.0, "medicine": 600.0}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")

    def test_api_marketplace_endpoints(self):
        # 1. Get marketplace data
        res1 = self.client.get(reverse("api_marketplace"))
        self.assertEqual(res1.status_code, 200)

        # 2. Create trade offer via API
        res2 = self.client.post(
            reverse("api_trade_create"),
            data=json.dumps({
                "seller_pod_id": "Pod 1",
                "resource_offered": "water",
                "amount_offered": 300.0,
                "price_in_credits": 100.0
            }),
            content_type="application/json"
        )
        self.assertEqual(res2.status_code, 200)

        # 3. Grant subsidy via API
        res3 = self.client.post(
            reverse("api_grant_subsidy"),
            data=json.dumps({"pod_id": "Pod 4", "subsidy_amount": 250.0}),
            content_type="application/json"
        )
        self.assertEqual(res3.status_code, 200)
