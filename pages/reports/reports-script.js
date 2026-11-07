document.addEventListener("DOMContentLoaded", () => {
  // --- DOM Core Layout Hook Elements ---
  const filterOptions = document.querySelectorAll(".filter-opt");
  const kpiEfficiency = document.getElementById("kpi-efficiency");
  const kpiVelocity = document.getElementById("kpi-velocity");
  const kpiHours = document.getElementById("kpi-hours");

  const chartLine = document.getElementById("chart-line");
  const chartArea = document.getElementById("chart-area");
  const chartNodesGroup = document.getElementById("chart-nodes");

  const progressBarA = document.getElementById("progress-domain-a");
  const progressBarB = document.getElementById("progress-domain-b");
  const progressArchitecture = document.getElementById("progress-architecture");

  const priorityList = document.getElementById("priority-list");
  const categoryList = document.getElementById("category-list");

  const sidebar = document.getElementById('sidebar');
  const sidebarToggle = document.getElementById('sidebar-toggle');

  // ==========================================
  // 1. Sidebar Navigation Expansion Interaction Module 
  // ==========================================
  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', (e) => {
      e.stopPropagation();
      sidebar.classList.toggle('expanded');
    });

    document.addEventListener('click', (event) => {
      const isClickInsideSidebar = sidebar.contains(event.target);
      if (!isClickInsideSidebar && sidebar.classList.contains('expanded')) {
        sidebar.classList.remove('expanded');
      }
    });
  }

  // ==========================================
  // 2. Data Store Matrices (7 Days vs 30 Days)
  // ==========================================
  const reportDatasets = {
    "7": {
      kpis: { efficiency: "85%", velocity: "4.8 / day", hours: "38.4 hrs" },
      progress: { domainA: "82%", domainB: "76%", architecture: "62%" },
      chartPoints: [
        { x: 40, y: 210 },
        { x: 130, y: 150 },
        { x: 220, y: 170 },
        { x: 310, y: 110 },
        { x: 400, y: 160 },
        { x: 490, y: 90 },
        { x: 580, y: 140 },
        { x: 670, y: 95 }
      ],
      priorityData: [
        { name: "Urgent", count: 2, pct: "29%", color: "#ef4444" },
        { name: "High", count: 2, pct: "29%", color: "#f97316" },
        { name: "Medium", count: 2, pct: "29%", color: "#eab308" },
        { name: "Low", count: 1, pct: "14%", color: "#64748b" }
      ],
      categoryData: [
        { name: "Engineering", comp: "0/2", pct: "35%", color: "#3b82f6" },
        { name: "UI/UX Design", comp: "1/1", pct: "100%", color: "#a855f7" },
        { name: "Database & DevOps", comp: "0/2", pct: "40%", color: "#06b6d4" },
        { name: "Growth & Launch", comp: "0/1", pct: "15%", color: "#f97316" },
        { name: "Productivity & Habits", comp: "1/1", pct: "100%", color: "#10b981" }
      ]
    },
    "30": {
      kpis: { efficiency: "91%", velocity: "5.2 / day", hours: "164.8 hrs" },
      progress: { domainA: "94%", domainB: "81%", architecture: "78%" },
      chartPoints: [
        { x: 40, y: 190 },
        { x: 130, y: 110 },
        { x: 220, y: 140 },
        { x: 310, y: 80 },
        { x: 400, y: 120 },
        { x: 490, y: 65 },
        { x: 580, y: 110 },
        { x: 670, y: 70 }
      ],
      priorityData: [
        { name: "Urgent", count: 5, pct: "38%", color: "#ef4444" },
        { name: "High", count: 4, pct: "31%", color: "#f97316" },
        { name: "Medium", count: 3, pct: "23%", color: "#eab308" },
        { name: "Low", count: 1, pct: "8%", color: "#64748b" }
      ],
      categoryData: [
        { name: "Engineering", comp: "3/4", pct: "75%", color: "#3b82f6" },
        { name: "UI/UX Design", comp: "2/2", pct: "100%", color: "#a855f7" },
        { name: "Database & DevOps", comp: "1/3", pct: "33%", color: "#06b6d4" },
        { name: "Growth & Launch", comp: "1/2", pct: "50%", color: "#f97316" },
        { name: "Productivity & Habits", comp: "2/2", pct: "100%", color: "#10b981" }
      ]
    }
  };

  // ==========================================
  // 3. Smooth Cubic Bezier Vector Generator
  // ==========================================
  function generateBezierCurve(points) {
    if (points.length === 0) return "";
    let d = `M ${points[0].x} ${points[0].y}`;

    for (let i = 0; i < points.length - 1; i++) {
      const p0 = points[i];
      const p1 = points[i + 1];

      const cpX1 = p0.x + (p1.x - p0.x) / 2;
      const cpY1 = p0.y;
      const cpX2 = p0.x + (p1.x - p0.x) / 2;
      const cpY2 = p1.y;

      d += ` C ${cpX1} ${cpY1}, ${cpX2} ${cpY2}, ${p1.x} ${p1.y}`;
    }
    return d;
  }

  // ==========================================
  // 4. Dynamic UI Render Controller
  // ==========================================
  function updateDashboardView(daysKey) {
    const dataset = reportDatasets[daysKey];

    // A. Load Metrics Texts
    if (kpiEfficiency) kpiEfficiency.textContent = dataset.kpis.efficiency;
    if (kpiVelocity) kpiVelocity.textContent = dataset.kpis.velocity;
    if (kpiHours) kpiHours.textContent = dataset.kpis.hours;

    // B. Trigger Smooth Horizontal Slider Fills
    if (progressBarA) progressBarA.style.width = dataset.progress.domainA;
    if (progressBarB) progressBarB.style.width = dataset.progress.domainB;
    if (progressArchitecture) progressArchitecture.style.width = dataset.progress.architecture;

    // C. Re-draw Graphical Waveforms Splines
    if (chartLine && chartArea) {
      const curveLinePath = generateBezierCurve(dataset.chartPoints);
      chartLine.setAttribute("d", curveLinePath);

      const closedAreaPath = `${curveLinePath} L 670 210 L 40 210 Z`;
      chartArea.setAttribute("d", closedAreaPath);
    }

    // D. Drop Interactive Circle Data Nodes
    if (chartNodesGroup) {
      chartNodesGroup.innerHTML = "";
      dataset.chartPoints.forEach((pt, index) => {
        const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        circle.setAttribute("cx", pt.x);
        circle.setAttribute("cy", pt.y);

        if (index === 5) {
          circle.setAttribute("r", "6");
          circle.setAttribute("class", "chart-node-point active-peak");
          circle.style.fill = "#ffffff";
          circle.style.stroke = "#00b4d8";
          circle.style.strokeWidth = "3px";
        } else {
          circle.setAttribute("r", "4.5");
          circle.setAttribute("class", "chart-node-point");
        }
        chartNodesGroup.appendChild(circle);
      });
    }

    // E. Render Workload Priorities Metric List
    if (priorityList) {
      priorityList.innerHTML = dataset.priorityData.map(item => `
        <div class="metric-row" style="display: flex; flex-direction: column; gap: 8px; margin-bottom: 12px;">
          <div class="metric-meta" style="display: flex; justify-content: space-between; font-size: 13px;">
            <div class="metric-label-group" style="display: flex; align-items: center; gap: 8px;">
              <span class="dot-indicator" style="background-color: ${item.color}; display: inline-block; width: 6px; height: 6px; border-radius: 50%;"></span>
              <span class="metric-label" style="color: #e2e8f0; font-weight: 500;">${item.name}</span>
            </div>
            <span class="metric-stats" style="color: #718096; font-size: 13px;">${item.count} tasks (${item.pct})</span>
          </div>
          <div class="metric-track" style="width: 100%; height: 6px; background-color: #1c2630; border-radius: 3px; overflow: hidden;">
            <div class="metric-bar" style="background-color: ${item.color}; width: ${item.pct} !important; height: 100%; border-radius: 3px;"></div>
          </div>
        </div>
      `).join('');
    }

    // F. Render Tasks Categories Metric List
    if (categoryList) {
      categoryList.innerHTML = dataset.categoryData.map(item => `
        <div class="metric-row" style="display: flex; flex-direction: column; gap: 8px; margin-bottom: 12px;">
          <div class="metric-meta" style="display: flex; justify-content: space-between; font-size: 13px;">
            <div class="metric-label-group" style="display: flex; align-items: center; gap: 8px;">
              <span class="dot-indicator" style="background-color: ${item.color}; display: inline-block; width: 6px; height: 6px; border-radius: 50%;"></span>
              <span class="metric-label" style="color: #e2e8f0; font-weight: 500;">${item.name}</span>
            </div>
            <span class="metric-stats" style="color: #718096; font-size: 13px;">${item.comp} completed (${item.pct})</span>
          </div>
          <div class="metric-track" style="width: 100%; height: 6px; background-color: #1c2630; border-radius: 3px; overflow: hidden;">
            <div class="metric-bar" style="background-color: ${item.color}; width: ${item.pct} !important; height: 100%; border-radius: 3px;"></div>
          </div>
        </div>
      `).join('');
    }
  }

  // ==========================================
  // 5. Click Listener Interactions Bindings
  // ==========================================
  filterOptions.forEach(opt => {
    opt.addEventListener("click", () => {
      filterOptions.forEach(el => el.classList.remove("active"));
      opt.classList.add("active");

      const selectedDays = opt.getAttribute("data-days");
      updateDashboardView(selectedDays);
    });
  });

  // Default Entry View Setup Initialization (7 Days Mode default)
  updateDashboardView("7");
});
