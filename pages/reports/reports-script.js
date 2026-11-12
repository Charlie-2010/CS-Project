document.addEventListener("DOMContentLoaded", () => {
  const dateOffset = days => {
    const date = new Date();
    date.setHours(12, 0, 0, 0);
    date.setDate(date.getDate() - days);
    return date;
  };
  let sampleTasks = [];
  const categoryColors = {
    "Engineering": "#3b82f6",
    "UI/UX Design": "#a855f7",
    "Database & DevOps": "#06b6d4",
    "Growth & Launch": "#f97316",
    "Productivity & Habits": "#10b981",
    "Architecture": "#ec4899"
  };
  const priorityColors = { URGENT: "#ef4444", HIGH: "#f97316", MEDIUM: "#eab308", LOW: "#64748b" };
  const priorityNames = { URGENT: "Urgent", HIGH: "High", MEDIUM: "Medium", LOW: "Low" };

  function calculateReportMetrics(tasks, days) {
    const cutoff = new Date();
    cutoff.setHours(0, 0, 0, 0);
    cutoff.setDate(cutoff.getDate() - days + 1);
    const periodTasks = tasks.filter(task => task.date >= cutoff);
    const completed = periodTasks.filter(task => task.status === "done");
    const hours = completed.reduce((total, task) => total + task.hours, 0);
    return {
      tasks: periodTasks,
      completed,
      efficiency: periodTasks.length ? Math.round(completed.length / periodTasks.length * 100) : 0,
      velocity: completed.length / days,
      hours
    };
  }

  function calculatePriorityMetrics(tasks) {
    return Object.keys(priorityNames).map(priority => {
      const count = tasks.filter(task => task.priority === priority).length;
      return { name: priorityNames[priority], count, percent: tasks.length ? Math.round(count / tasks.length * 100) : 0, color: priorityColors[priority] };
    }).filter(metric => metric.count);
  }

  function calculateCategoryMetrics(tasks) {
    return [...new Set(tasks.map(task => task.category))].map(name => {
      const matching = tasks.filter(task => task.category === name);
      const completed = matching.filter(task => task.status === "done").length;
      return { name, count: matching.length, completed, percent: matching.length ? Math.round(completed / matching.length * 100) : 0, color: categoryColors[name] || "#64748b" };
    });
  }

  function createMetricRow({ name, detail, percent, color }) {
    const row = document.createElement("div");
    row.className = "metric-row";
    const meta = document.createElement("div");
    meta.className = "metric-meta";
    const labelGroup = document.createElement("div");
    labelGroup.className = "metric-label-group";
    const dot = document.createElement("span");
    dot.className = "dot-indicator";
    dot.style.backgroundColor = color;
    const label = document.createElement("span");
    label.className = "metric-label";
    label.textContent = name;
    labelGroup.append(dot, label);
    const stats = document.createElement("span");
    stats.className = "metric-stats";
    stats.textContent = detail;
    meta.append(labelGroup, stats);
    const track = document.createElement("div");
    track.className = "metric-track";
    const fill = document.createElement("div");
    fill.className = "metric-bar";
    fill.style.width = `${percent}%`;
    fill.style.backgroundColor = color;
    track.appendChild(fill);
    row.append(meta, track);
    return row;
  }

  function createChartPoints(tasks, days) {
    const points = [];
    for (let index = 0; index < 8; index++) {
      const periodDay = Math.round(index * (days - 1) / 7);
      const day = new Date();
      day.setHours(0, 0, 0, 0);
      day.setDate(day.getDate() - (days - 1 - periodDay));
      const nextDay = new Date(day);
      nextDay.setDate(nextDay.getDate() + 1);
      const count = tasks.filter(task => task.status === "done" && task.date >= day && task.date < nextDay).length;
      points.push({ x: 40 + index * 90, count });
    }
    const maxCount = Math.max(1, ...points.map(point => point.count));
    return points.map(point => ({ x: point.x, y: 200 - point.count / maxCount * 150 }));
  }

  function generateCurve(points) {
    if (!points.length) return "";
    return points.slice(1).reduce((path, point, index) => {
      const previous = points[index];
      const middleX = (previous.x + point.x) / 2;
      return `${path} C ${middleX} ${previous.y}, ${middleX} ${point.y}, ${point.x} ${point.y}`;
    }, `M ${points[0].x} ${points[0].y}`);
  }

  function render(days) {
    const metrics = calculateReportMetrics(sampleTasks, days);
    document.getElementById("kpi-efficiency").textContent = `${metrics.efficiency}%`;
    document.getElementById("kpi-velocity").textContent = `${metrics.velocity.toFixed(1)} / day`;
    document.getElementById("kpi-hours").textContent = `${metrics.hours.toFixed(1)} hrs`;

    const categories = calculateCategoryMetrics(metrics.tasks);
    const getCategoryProgress = name => categories.find(category => category.name === name)?.percent || 0;
    document.getElementById("progress-domain-a").style.width = `${getCategoryProgress("Engineering")}%`;
    document.getElementById("progress-domain-b").style.width = `${getCategoryProgress("UI/UX Design")}%`;
    document.getElementById("progress-architecture").style.width = `${getCategoryProgress("Architecture")}%`;

    const points = createChartPoints(metrics.tasks, days);
    const curve = generateCurve(points);
    document.getElementById("chart-line").setAttribute("d", curve);
    document.getElementById("chart-area").setAttribute("d", `${curve} L 670 210 L 40 210 Z`);
    const nodes = document.getElementById("chart-nodes");
    nodes.replaceChildren();
    points.forEach(point => {
      const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      circle.setAttribute("cx", String(point.x));
      circle.setAttribute("cy", String(point.y));
      circle.setAttribute("r", "4.5");
      circle.setAttribute("class", "chart-node-point");
      nodes.appendChild(circle);
    });

    const priorityList = document.getElementById("priority-list");
    priorityList.replaceChildren(...calculatePriorityMetrics(metrics.tasks).map(metric => createMetricRow({
      name: metric.name,
      detail: `${metric.count} tasks (${metric.percent}%)`,
      percent: metric.percent,
      color: metric.color
    })));
    const categoryList = document.getElementById("category-list");
    categoryList.replaceChildren(...categories.map(metric => createMetricRow({
      name: metric.name,
      detail: `${metric.completed}/${metric.count} completed`,
      percent: metric.percent,
      color: metric.color
    })));
  }

  document.querySelectorAll(".filter-opt[data-days]").forEach(button => {
    button.setAttribute("aria-pressed", String(button.classList.contains("active")));
    button.addEventListener("click", () => {
      const days = Number(button.dataset.days);
      document.querySelectorAll(".filter-opt[data-days]").forEach(item => {
        item.classList.toggle("active", item === button);
        item.setAttribute("aria-pressed", String(item === button));
      });
      render(days);
    });
  });
  window.CogniPlanAPI.get("/api/tasks").then(result => {
    sampleTasks = (result.tasks || []).map(task => {
      const dateValue = task.completed_at || task.created_at || new Date().toISOString();
      return { title: task.title, date: new Date(String(dateValue).replace(" ", "T")),
        status: task.status === "Done" ? "done" : "in-progress", priority: task.priority,
        category: task.category || "Uncategorized", hours: Number(task.actual_minutes || 0) / 60 };
    });
    render(Number(document.querySelector(".filter-opt[data-days].active")?.dataset.days || 7));
  }).catch(error => console.warn("Report tasks could not be loaded:", error.message));
  render(7);
});
