/* Matilda Bay Ops — Clean Flat Design Chart Engine */
document.addEventListener("DOMContentLoaded", function() {
  let fullData = null;
  let chartStock = null;
  let chartDisruption = null;
  let chartCouncil = null;
  let chartCalibration = null;

  // Chart.js Global Flat Design Configuration
  Chart.defaults.font.family = "'Plus Jakarta Sans', system-ui, sans-serif";
  Chart.defaults.color = "#94a3b8";

  // Tab Switching Logic
  const tabBtns = document.querySelectorAll(".nav-tab-btn");
  const tabPanes = document.querySelectorAll(".tab-pane");

  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetTab = btn.getAttribute("data-tab");
      if (!targetTab) return; // Allow normal link navigation
      
      tabBtns.forEach(b => b.classList.remove("active"));
      tabPanes.forEach(p => p.classList.remove("active"));

      btn.classList.add("active");
      const targetPane = document.getElementById("tab-" + targetTab);
      if (targetPane) targetPane.classList.add("active");

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

  // Handle cross-page tab routing via URL parameter
  const urlParams = new URLSearchParams(window.location.search);
  const requestedTab = urlParams.get('tab');
  if (requestedTab) {
    const targetBtn = document.querySelector(`.nav-tab-btn[data-tab="${requestedTab}"]`);
    if (targetBtn) {
      targetBtn.click();
      // Remove param from URL cleanly
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }

  // Initial Fetch & Setup
  fetch("/api/data/?calibrate=true")
    .then(response => response.json())
    .then(data => {
      if (data.status === "success") {
        fullData = data;
        setupFilters();
        renderCharts();
      }
    })
    .catch(err => console.error("Error loading Matilda Bay datasets:", err));

  function fetchDashboardData() {
    const isCalibrated = document.getElementById("calibrationToggle") ? document.getElementById("calibrationToggle").checked : true;
    fetch(`/api/data/?calibrate=${isCalibrated}`)
      .then(response => response.json())
      .then(data => {
        if (data.status === "success") {
          fullData = data;
          renderCharts();
        }
      })
      .catch(err => console.error("Error reloading data:", err));
  }

  function setupFilters() {
    const podSelect = document.getElementById("podFilter");
    const resourceSelect = document.getElementById("resourceFilter");
    const calibrationToggle = document.getElementById("calibrationToggle");
    const disruptionSelect = document.getElementById("disruptionFilter");

    if (podSelect) podSelect.addEventListener("change", renderCharts);
    if (resourceSelect) resourceSelect.addEventListener("change", renderCharts);
    if (calibrationToggle) calibrationToggle.addEventListener("change", fetchDashboardData);
    if (disruptionSelect) disruptionSelect.addEventListener("change", renderCharts);
  }

  function renderCharts() {
    if (!fullData) return;

    const selectedPod = document.getElementById("podFilter") ? document.getElementById("podFilter").value : "all";
    const selectedResource = document.getElementById("resourceFilter") ? document.getElementById("resourceFilter").value : "all";
    const isCalibrated = document.getElementById("calibrationToggle") ? document.getElementById("calibrationToggle").checked : true;

    let supplyRecords = fullData.supply_records;
    let councilRecords = fullData.council_records;

    if (selectedPod !== "all") {
      supplyRecords = supplyRecords.filter(r => r.pod_id === selectedPod);
      councilRecords = councilRecords.filter(r => r.pod_id === selectedPod);
    }

    const selectedDisruption = document.getElementById("disruptionFilter") ? document.getElementById("disruptionFilter").value : "major";

    renderStockChart(supplyRecords, selectedResource, isCalibrated);
    renderDisruptionChart(supplyRecords);
    renderCouncilChart(fullData.council_records, selectedPod);
    renderCalibrationChart(fullData.supply_records);
    renderOverview(selectedPod, selectedResource, selectedDisruption);
  }

  function renderOverview(selectedPod, selectedResource, selectedDisruption) {
    // 1. Pod & Resource HTML DOM filtering
    document.querySelectorAll('.pods-grid .pod-card').forEach(card => {
      if (selectedPod === "all" || card.getAttribute("data-pod-id") === selectedPod) {
        card.style.display = "block";
      } else {
        card.style.display = "none";
      }
    });

    document.querySelectorAll('.runway-row').forEach(row => {
      if (selectedResource === "all" || row.getAttribute("data-resource") === selectedResource) {
        row.style.display = "flex";
      } else {
        row.style.display = "none";
      }
    });

    // 2. Peacock Disruption Fetching & DOM Updating
    fetch(`/api/forecast/?disruption=${selectedDisruption}&days=7`)
      .then(r => r.json())
      .then(d => {
        if (d.status === "success" && d.forecasts) {
          d.forecasts.forEach(f => {
            const safePodId = f.pod_id.replace(/\s+/g, '-').toLowerCase();
            const wDays = f.projected_water_runway;
            const fDays = f.projected_food_runway;
            const mDays = f.projected_medicine_runway;

            // Water
            const wText = document.querySelector(`.runway-text-water-${safePodId}`);
            const wBar = document.querySelector(`.runway-bar-water-${safePodId}`);
            if (wText) wText.innerHTML = `${wDays.toFixed(1)} days`;
            if (wBar) {
              wBar.style.width = `${Math.min(wDays, 100)}%`;
              wBar.className = `progress-bar-fill runway-bar-water-${safePodId} ` + (wDays > 10 ? 'fill-emerald' : wDays > 5 ? 'fill-amber' : 'fill-rose');
            }

            // Food
            const fText = document.querySelector(`.runway-text-food-${safePodId}`);
            const fBar = document.querySelector(`.runway-bar-food-${safePodId}`);
            if (fText) fText.innerHTML = `${fDays.toFixed(1)} days`;
            if (fBar) {
              fBar.style.width = `${Math.min(fDays, 100)}%`;
              fBar.className = `progress-bar-fill runway-bar-food-${safePodId} ` + (fDays > 10 ? 'fill-emerald' : fDays > 5 ? 'fill-amber' : 'fill-rose');
            }

            // Medicine
            const mText = document.querySelector(`.runway-text-medicine-${safePodId}`);
            const mBar = document.querySelector(`.runway-bar-medicine-${safePodId}`);
            if (mText) mText.innerHTML = `${mDays.toFixed(1)} days`;
            if (mBar) {
              mBar.style.width = `${Math.min(mDays, 100)}%`;
              mBar.className = `progress-bar-fill runway-bar-medicine-${safePodId} ` + (mDays > 10 ? 'fill-emerald' : mDays > 5 ? 'fill-amber' : 'fill-rose');
            }
          });
        }
      });
  }

  // 1. Stock & Runway Time-Series Chart
  function renderStockChart(records, resourceFilter, isCalibrated) {
    const ctx = document.getElementById("chartStockCanvas");
    if (!ctx) return;

    const dates = [...new Set(records.map(r => r.report_date))].sort();
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
        
        return Math.min(rec.water_runway_days, rec.food_runway_days, rec.medicine_runway_days);
      });

      datasets.push({
        label: `${podName} Runway (Days)`,
        data: runwayData,
        borderColor: colors[podName] || "#8b5cf6",
        backgroundColor: colors[podName],
        borderWidth: 2,
        tension: 0,
        fill: false,
        pointRadius: 4,
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
          legend: { labels: { color: "#94a3b8", font: { family: "Plus Jakarta Sans", weight: "600" } } },
          tooltip: {
            mode: "index",
            intersect: false,
            backgroundColor: "#131926",
            titleColor: "#f8fafc",
            bodyColor: "#94a3b8",
            borderColor: "#263147",
            borderWidth: 1,
            padding: 10,
            cornerRadius: 4,
          }
        },
        scales: {
          x: {
            ticks: { color: "#64748b" },
            grid: { color: "#182030" }
          },
          y: {
            title: { display: true, text: "Supply Runway (Days)", color: "#94a3b8" },
            ticks: { color: "#64748b" },
            grid: { color: "#182030" },
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

    const dateMap = {};
    records.forEach(r => {
      if (!dateMap[r.report_date]) {
        dateMap[r.report_date] = { water: 0, food: 0, disruption: "none" };
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
          borderRadius: 2,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: "#131926",
            borderColor: "#263147",
            borderWidth: 1,
            cornerRadius: 4,
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
          y: { ticks: { color: "#64748b" }, grid: { color: "#182030" } }
        }
      }
    });
  }

  // 3. Council Allocation Fairness (Naive vs Fair Priority)
  function renderCouncilChart(records, selectedPod) {
    const ctx = document.getElementById("chartCouncilCanvas");
    if (!ctx) return;

    let targetPod = selectedPod === "all" ? "Pod 4" : selectedPod;
    const podRecords = records.filter(r => r.pod_id === targetPod);
    
    // If we filtered out the target pod (e.g. they selected a pod but the records don't match, though they should)
    if (podRecords.length === 0) {
       if (chartCouncil) chartCouncil.destroy();
       return;
    }

    const naiveRanks = podRecords.map(r => r.naive_priority_rank);
    const fairRanks = podRecords.map(r => r.fair_priority_rank);

    if (chartCouncil) chartCouncil.destroy();

    chartCouncil = new Chart(ctx, {
      type: "line",
      data: {
        labels: podRecords.map(r => `Meeting #${r.event_id} (${r.event_date})`),
        datasets: [
          {
            label: `${targetPod} Fair Need Rank`,
            data: fairRanks,
            borderColor: "#10b981",
            backgroundColor: "#10b981",
            borderWidth: 3,
            tension: 0.1,
            pointRadius: 5
          },
          {
            label: `${targetPod} Naive Rank`,
            data: naiveRanks,
            borderColor: "#f43f5e",
            backgroundColor: "#f43f5e",
            borderWidth: 3,
            tension: 0.1,
            pointRadius: 5
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: "#94a3b8", font: { family: "Plus Jakarta Sans", weight: "600" } } },
          tooltip: { backgroundColor: "#131926", borderColor: "#263147", borderWidth: 1, cornerRadius: 4 }
        },
        scales: {
          x: { ticks: { color: "#64748b" }, grid: { display: false } },
          y: {
            title: { display: true, text: "Priority Rank (1 = Top Priority)", color: "#94a3b8" },
            reverse: true,
            ticks: { color: "#64748b", stepSize: 1 },
            min: 0.5,
            max: 4.5,
            grid: { color: "#182030" }
          }
        }
      }
    });
  }

  // 4. Drone Calibration Offset Analyzer
  function renderCalibrationChart(records) {
    const ctx = document.getElementById("chartCalibrationCanvas");
    if (!ctx) return;

    const pod1Records = records.filter(r => r.pod_id === "Pod 1").slice(0, 15);
    const dates = pod1Records.map(r => r.report_date);
    
    const waterRaw = pod1Records.map(r => r.water_stock_l);
    const waterCalibrated = pod1Records.map(r => {
      if (r.report_source === "scout_drone_scan") {
        return r.water_stock_l + 1250.0;
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
            borderDash: [4, 4],
            borderWidth: 2,
            fill: false,
          },
          {
            label: "Drone Scan Calibrated Water Stock (L)",
            data: waterCalibrated,
            borderColor: "#06b6d4",
            borderWidth: 2,
            fill: false,
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: "#94a3b8", font: { family: "Plus Jakarta Sans", weight: "600" } } },
          tooltip: { backgroundColor: "#131926", borderColor: "#263147", borderWidth: 1, cornerRadius: 4 }
        },
        scales: {
          x: { ticks: { color: "#64748b" }, grid: { display: false } },
          y: { ticks: { color: "#64748b" }, grid: { color: "#182030" } }
        }
      }
    });
  }

  // 5. Interactive Allocation Simulator Event Handler
  const btnRunSim = document.getElementById("btnRunSimulation");
  if (btnRunSim) {
    btnRunSim.addEventListener("click", runAllocationSimulation);
  }

  function runAllocationSimulation() {
    const water = parseFloat(document.getElementById("simWater").value) || 6500;
    const food = parseFloat(document.getElementById("simFood").value) || 1000;
    const med = parseFloat(document.getElementById("simMedicine").value) || 500;

    fetch("/api/simulate-allocation/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ water: water, food: food, medicine: med })
    })
      .then(res => res.json())
      .then(data => {
        if (data.status === "success") {
          renderSimulationResults(data.simulation);
        }
      })
      .catch(err => console.error("Simulation error:", err));
  }

  function renderSimulationResults(simData) {
    const output = document.getElementById("simResultsOutput");
    if (!output) return;

    output.style.display = "block";
    let html = `<h4 style="margin-top: 0; color: var(--accent-cyan); font-size: 0.95rem;">Simulation Results (Naive vs. Fair Allocation)</h4>`;
    
    Object.keys(simData).forEach(resource => {
      const resData = simData[resource];
      html += `
        <div style="margin-bottom: 1rem;">
          <div style="font-weight: 700; font-size: 0.85rem; color: var(--text-primary); text-transform: uppercase; margin-bottom: 4px;">
            Resource: ${resource} (Available Pool: ${resData.available_pool} | Total Need: ${resData.total_need})
          </div>
          <table class="custom-table" style="font-size: 0.8rem; margin-top: 4px;">
            <thead>
              <tr>
                <th>Pod</th>
                <th>Request Status</th>
                <th>Estimated Need</th>
                <th>Naive Rank (Allocated)</th>
                <th>Fair Rank (Allocated)</th>
                <th>Benefit Delta</th>
              </tr>
            </thead>
            <tbody>
              ${resData.pods.map(p => `
                <tr>
                  <td><strong>${p.pod_name}</strong></td>
                  <td>${p.request_submitted ? '<span style="color:var(--accent-emerald);">Submitted</span>' : '<span style="color:var(--accent-rose); font-weight:700;">Silent (No Request)</span>'}</td>
                  <td class="mono">${p.estimated_true_need}</td>
                  <td class="mono">#${p.naive_rank} (${p.naive_allocated})</td>
                  <td class="mono" style="color:var(--accent-emerald); font-weight:700;">#${p.fair_rank} (${p.fair_allocated})</td>
                  <td class="mono" style="color:${p.fair_benefit_delta > 0 ? 'var(--accent-emerald)' : 'var(--text-muted)'}; font-weight:700;">
                    ${p.fair_benefit_delta > 0 ? '+' + p.fair_benefit_delta : p.fair_benefit_delta}
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `;
    });

    output.innerHTML = html;
  }

  // (Disruption event listener was moved to setupFilters and renderOverview)

  // 7. Export Courier Dispatch CSV Handler
  const btnExportCsv = document.getElementById("btnExportCsv");
  if (btnExportCsv) {
    btnExportCsv.addEventListener("click", exportCourierDispatchCsv);
  }

  function exportCourierDispatchCsv() {
    if (!fullData || !fullData.summary || !fullData.summary.pods) return;

    let csvContent = "data:text/csv;charset=utf-8,";
    csvContent += "Pod ID,Pod Name,Population,Distance (km),Overall Status,Bottleneck Resource,Water Runway (Days),Food Runway (Days),Medicine Runway (Days),Recommended Action\n";

    fullData.summary.pods.forEach(pod => {
      let recAction = "Standard Delivery";
      if (pod.overall_status === "critical" || pod.overall_status === "failed") {
        recAction = "PRIORITY EMERGENCY DISPATCH";
      } else if (pod.requested_assistance === false && pod.distance_km > 10) {
        recAction = "PROACTIVE SILENT NEED DISPATCH";
      }

      csvContent += `"${pod.pod_id}","${pod.pod_name}",${pod.population},${pod.distance_km},"${pod.overall_status}","Water",${pod.water_runway_days},${pod.food_runway_days},${pod.medicine_runway_days},"${recAction}"\n`;
    });

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "matilda_bay_courier_dispatch.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  // 8. Inter-Pod Marketplace Handlers
  const btnCreateOffer = document.getElementById("btnCreateOffer");
  if (btnCreateOffer) {
    btnCreateOffer.addEventListener("click", function() {
      const seller = document.getElementById("tradeSellerPod").value;
      const resource = document.getElementById("tradeResource").value;
      const amount = parseFloat(document.getElementById("tradeAmount").value) || 100;
      const price = parseFloat(document.getElementById("tradePrice").value) || 50;

      fetch("/api/trade/create/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          seller_pod_id: seller,
          resource_offered: resource,
          amount_offered: amount,
          price_in_credits: price
        })
      })
        .then(r => r.json())
        .then(d => {
          if (d.status === "success") {
            alert(d.message);
            window.location.replace("?tab=marketplace");
          } else {
            alert("Error: " + d.message);
          }
        });
    });
  }

  const btnGrantSubsidy = document.getElementById("btnGrantSubsidy");
  if (btnGrantSubsidy) {
    btnGrantSubsidy.addEventListener("click", function() {
      const podId = document.getElementById("subsidyPod").value;
      const amount = parseFloat(document.getElementById("subsidyAmount").value) || 500;

      fetch("/api/grant-subsidy/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pod_id: podId, subsidy_amount: amount })
      })
        .then(r => r.json())
        .then(d => {
          if (d.status === "success") {
            alert(d.message);
            window.location.replace("?tab=marketplace");
          } else {
            alert("Error: " + d.message);
          }
        });
    });
  }

  document.addEventListener("click", function(e) {
    if (e.target && e.target.classList.contains("btn-execute-trade")) {
      const offerId = e.target.getAttribute("data-offer-id");
      const buyerSelect = e.target.previousElementSibling;
      const buyerPod = buyerSelect ? buyerSelect.value : null;
      if (!buyerPod) return;

      fetch("/api/trade/execute/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ buyer_pod_id: buyerPod, offer_id: offerId })
      })
        .then(r => r.json())
        .then(d => {
          if (d.status === "success") {
            alert(d.message);
            window.location.replace("?tab=marketplace");
          } else {
            alert("Error: " + d.message);
          }
        });
    }
  });
});


