/* Matilda Bay Ops - Interactive Dashboard & Data Visualization Engine */
document.addEventListener("DOMContentLoaded", function() {
  let fullData = null;
  let chartStock = null;
  let chartDisruption = null;
  let chartCouncil = null;
  let chartCalibration = null;

  // Tab Switching Logic
  const tabBtns = document.querySelectorAll(".nav-tab-btn");
  const tabPanes = document.querySelectorAll(".tab-pane");

  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetTab = btn.getAttribute("data-tab");
      
      tabBtns.forEach(b => b.classList.remove("active"));
      tabPanes.forEach(p => p.classList.remove("active"));

      btn.classList.add("active");
      document.getElementById("tab-" + targetTab).classList.add("active");

      // Re-render/update chart sizes when switching to data viz tab
      if (targetTab === "visualization" || targetTab === "council") {
        setTimeout(() => {
          if (chartStock) chartStock.resize();
          if (chartDisruption) chartDisruption.resize();
          if (chartCouncil) chartCouncil.resize();
          if (chartCalibration) chartCalibration.resize();
        }, 100);
      }
    });
  });

  // Fetch Data from Django API
  fetch("/api/data/")
    .then(response => response.json())
    .then(data => {
      if (data.status === "success") {
        fullData = data;
        initDashboard(data);
      }
    })
    .catch(err => console.error("Error loading Matilda Bay datasets:", err));

  function initDashboard(data) {
    setupFilters();
    renderCharts();
  }

  function setupFilters() {
    const podSelect = document.getElementById("podFilter");
    const resourceSelect = document.getElementById("resourceFilter");
    const calibrationToggle = document.getElementById("calibrationToggle");

    if (podSelect) podSelect.addEventListener("change", renderCharts);
    if (resourceSelect) resourceSelect.addEventListener("change", renderCharts);
    if (calibrationToggle) calibrationToggle.addEventListener("change", renderCharts);
  }

  function renderCharts() {
    if (!fullData) return;

    const selectedPod = document.getElementById("podFilter") ? document.getElementById("podFilter").value : "all";
    const selectedResource = document.getElementById("resourceFilter") ? document.getElementById("resourceFilter").value : "all";
    const isCalibrated = document.getElementById("calibrationToggle") ? document.getElementById("calibrationToggle").checked : true;

    let supplyRecords = fullData.supply_records;
    let councilRecords = fullData.council_records;

    // Filter by pod if selected
    if (selectedPod !== "all") {
      supplyRecords = supplyRecords.filter(r => r.pod_id === selectedPod);
      councilRecords = councilRecords.filter(r => r.pod_id === selectedPod);
    }

    renderStockChart(supplyRecords, selectedResource, isCalibrated);
    renderDisruptionChart(supplyRecords);
    renderCouncilChart(councilRecords);
    renderCalibrationChart(fullData.supply_records);
  }

  // 1. Stock & Runway Time-Series Chart
  function renderStockChart(records, resourceFilter, isCalibrated) {
    const ctx = document.getElementById("chartStockCanvas");
    if (!ctx) return;

    // Group records by date
    const dates = [...new Set(records.map(r => r.report_date))].sort();

    // Group by Pods
    const pods = [...new Set(records.map(r => r.pod_name))];

    const colors = {
      "Orca Pod 1": "#06b6d4",
      "Orca Pod 2": "#3b82f6",
      "Orca Pod 3": "#10b981",
      "Orca Pod 4": "#f43f5e",
    };

    const datasets = [];

    pods.forEach(podName => {
      const podRecords = records.filter(r => r.pod_name === podName);
      
      const runwayData = dates.map(d => {
        const rec = podRecords.find(r => r.report_date === d);
        if (!rec) return null;

        if (resourceFilter === "water") return rec.water_runway_days;
        if (resourceFilter === "food") return rec.food_runway_days;
        if (resourceFilter === "medicine") return rec.medicine_runway_days;
        
        // Default: overall minimum runway
        return Math.min(rec.water_runway_days, rec.food_runway_days, rec.medicine_runway_days);
      });

      datasets.push({
        label: `${podName} Runway (Days)`,
        data: runwayData,
        borderColor: colors[podName] || "#8b5cf6",
        backgroundColor: colors[podName] + "22",
        borderWidth: 2.5,
        tension: 0.3,
        fill: false,
        pointRadius: 3,
        pointHoverRadius: 6,
      });
    });

    if (chartStock) chartStock.destroy();

    chartStock = new Chart(ctx, {
      type: "line",
      data: {
        labels: dates,
        datasets: datasets
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: "#94a3b8", font: { family: "Inter" } } },
          tooltip: {
            mode: "index",
            intersect: false,
            backgroundColor: "#141b2d",
            titleColor: "#f8fafc",
            bodyColor: "#94a3b8",
            borderColor: "rgba(255,255,255,0.1)",
            borderWidth: 1,
          }
        },
        scales: {
          x: {
            ticks: { color: "#64748b" },
            grid: { color: "rgba(255,255,255,0.05)" }
          },
          y: {
            title: { display: true, text: "Supply Runway (Days)", color: "#94a3b8" },
            ticks: { color: "#64748b" },
            grid: { color: "rgba(255,255,255,0.05)" },
            min: 0
          }
        }
      }
    });
  }

  // 2. Consumption vs Peacock Disruption Correlation
  function renderDisruptionChart(records) {
    const ctx = document.getElementById("chartDisruptionCanvas");
    if (!ctx) return;

    // Group by date: sum consumption & peak disruption
    const dateMap = {};
    records.forEach(r => {
      if (!dateMap[r.report_date]) {
        dateMap[r.report_date] = {
          water: 0,
          food: 0,
          disruption: "none"
        };
      }
      dateMap[r.report_date].water += r.water_consumption_lpd;
      dateMap[r.report_date].food += r.food_consumption_kgpd;
      if (r.peacock_disruption === "major") dateMap[r.report_date].disruption = "major";
      else if (r.peacock_disruption === "minor" && dateMap[r.report_date].disruption !== "major") {
        dateMap[r.report_date].disruption = "minor";
      }
    });

    const dates = Object.keys(dateMap).sort();
    const waterData = dates.map(d => Math.round(dateMap[d].water));
    const disruptionColors = dates.map(d => {
      const dis = dateMap[d].disruption;
      if (dis === "major") return "#f43f5e";
      if (dis === "minor") return "#f59e0b";
      return "#10b981";
    });

    if (chartDisruption) chartDisruption.destroy();

    chartDisruption = new Chart(ctx, {
      type: "bar",
      data: {
        labels: dates,
        datasets: [{
          label: "Total Daily Water Burn Rate (Litres)",
          data: waterData,
          backgroundColor: disruptionColors,
          borderRadius: 4,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              afterLabel: function(context) {
                const d = dates[context.dataIndex];
                return `Peacock Disruption: ${dateMap[d].disruption.toUpperCase()}`;
              }
            }
          }
        },
        scales: {
          x: { ticks: { color: "#64748b" }, grid: { display: false } },
          y: { ticks: { color: "#64748b" }, grid: { color: "rgba(255,255,255,0.05)" } }
        }
      }
    });
  }

  // 3. Council Allocation Fairness (Naive vs Fair Priority)
  function renderCouncilChart(records) {
    const ctx = document.getElementById("chartCouncilCanvas");
    if (!ctx) return;

    const events = [...new Set(records.map(r => `Event #${r.event_id} (${r.event_date})`))];

    // Compare Pod 4 (Reed's End) Naive Rank vs Fair Rank
    const pod4Records = records.filter(r => r.pod_id === "Pod 4");
    const naiveRanks = pod4Records.map(r => r.naive_priority_rank);
    const fairRanks = pod4Records.map(r => r.fair_priority_rank);
    const unmetAmounts = pod4Records.map(r => r.unmet_amount);

    if (chartCouncil) chartCouncil.destroy();

    chartCouncil = new Chart(ctx, {
      type: "bar",
      data: {
        labels: pod4Records.map(r => `Meeting #${r.event_id} (${r.event_date})`),
        datasets: [
          {
            label: "Reed's End (Pod 4) Fair Need Rank (1=Highest)",
            data: fairRanks,
            backgroundColor: "#10b981",
            borderRadius: 4,
          },
          {
            label: "Reed's End (Pod 4) Naive Rank (Distance-based)",
            data: naiveRanks,
            backgroundColor: "#f43f5e",
            borderRadius: 4,
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: "#94a3b8" } },
        },
        scales: {
          x: { ticks: { color: "#64748b" }, grid: { display: false } },
          y: {
            title: { display: true, text: "Priority Rank (1 = Top Priority)", color: "#94a3b8" },
            reverse: true,
            ticks: { color: "#64748b", stepSize: 1 },
            min: 1,
            max: 4,
            grid: { color: "rgba(255,255,255,0.05)" }
          }
        }
      }
    });
  }

  // 4. Drone Calibration Offset Analyzer
  function renderCalibrationChart(records) {
    const ctx = document.getElementById("chartCalibrationCanvas");
    if (!ctx) return;

    // Filter Pod 1 records to compare elder reports vs drone scans
    const pod1Records = records.filter(r => r.pod_id === "Pod 1").slice(0, 15);
    const dates = pod1Records.map(r => r.report_date);
    
    const waterRaw = pod1Records.map(r => r.water_stock_l);
    const waterCalibrated = pod1Records.map(r => {
      if (r.report_source === "scout_drone_scan") {
        return r.water_stock_l + 1250.0; // Correcting drone offset
      }
      return r.water_stock_l;
    });

    if (chartCalibration) chartCalibration.destroy();

    chartCalibration = new Chart(ctx, {
      type: "line",
      data: {
        labels: dates,
        datasets: [
          {
            label: "Raw Reported Water Stock (L)",
            data: waterRaw,
            borderColor: "#64748b",
            borderDash: [5, 5],
            borderWidth: 2,
            fill: false,
          },
          {
            label: "Drone Scan Calibrated Water Stock (L)",
            data: waterCalibrated,
            borderColor: "#06b6d4",
            borderWidth: 2.5,
            fill: false,
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: "#94a3b8" } }
        },
        scales: {
          x: { ticks: { color: "#64748b" }, grid: { display: false } },
          y: { ticks: { color: "#64748b" }, grid: { color: "rgba(255,255,255,0.05)" } }
        }
      }
    });
  }
});
