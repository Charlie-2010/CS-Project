document.addEventListener("DOMContentLoaded", () => {
  // --- DOM Element Hooks ---
  const columns = document.querySelectorAll(".kanban-column");
  const cardsListContainers = document.querySelectorAll(".cards-list-container");
  // Progress Tracking Elements
  const domainABar = document.getElementById("domain-a-bar");
  const domainAPct = document.getElementById("domain-a-pct");
  const domainBBar = document.getElementById("domain-b-bar");
  const domainBPct = document.getElementById("domain-b-pct");
  // Active dragging states references
  let draggedCard = null;
  // ==========================================
  // 1. Initialize Cards & Event Bindings
  // ==========================================
  function initializeCards() {
    const cards = document.querySelectorAll(".kanban-card");
    cards.forEach(card => {
      card.setAttribute("draggable", "true");
      card.removeEventListener("dragstart", handleDragStart);
      card.removeEventListener("dragend", handleDragEnd);
      card.addEventListener("dragstart", handleDragStart);
      card.addEventListener("dragend", handleDragEnd);
      // Bind options click configuration listeners
      setupCardOptions(card);
    });
  }
  function handleDragStart(e) {
    draggedCard = this;
    setTimeout(() => { this.style.opacity = "0.4"; }, 0);
    e.dataTransfer.effectAllowed = "move";
  }
  function handleDragEnd() {
    draggedCard = null;
    this.style.opacity = "1";
    columns.forEach(col => {
      col.style.backgroundColor = "";
      col.style.borderColor = "";
    });
  }
  // ==========================================
  // 2. Interactive Editing Menu Action Loop
  // ==========================================
  function setupCardOptions(card) {
    const dotsBtn = card.querySelector(".card-dots");
    if (!dotsBtn || dotsBtn.dataset.bound === "true") return;
    dotsBtn.dataset.bound = "true"; // Guard against redundant listener accumulation
    dotsBtn.addEventListener("click", function (e) {
      e.stopPropagation(); // Avoid event context bubbles bleeding
      // Remove existing dropdown panels if any are active elsewhere
      document.querySelectorAll(".card-edit-dropdown").forEach(d => d.remove());
      // Create new dropdown structural context list menu node
      const dropdown = document.createElement("div");
      dropdown.className = "card-edit-dropdown";
      dropdown.innerHTML = `<div><button class="dropdown-item btn-edit-title">✏️ Rename Title</button> <button class="dropdown-item btn-toggle-priority">⚡ Swap Priority</button> <button class="dropdown-item btn-swap-tag">🏷️ Toggle Tag</button> <button class="dropdown-item dropdown-item--delete btn-delete-card">🗑️ Delete Task</button></div>`;
      // Event listeners for internal actions mapping
      dropdown.querySelector(".btn-edit-title").addEventListener("click", () => {
        const titleNode = card.querySelector(".card-heading");
        const currentText = titleNode.textContent;
        const updatedText = prompt("Update task headline string:", currentText);
        if (updatedText && updatedText.trim() !== "") {
          titleNode.textContent = updatedText.trim();
        }
        dropdown.remove();
      });
      dropdown.querySelector(".btn-toggle-priority").addEventListener("click", () => {
        const indicator = card.querySelector(".priority-indicator");
        if (indicator) {
          if (indicator.classList.contains("priority-indicator--high")) {
            indicator.className = "priority-indicator priority-indicator--mid";
            indicator.textContent = "⚡ mid";
          } else {
            indicator.className = "priority-indicator priority-indicator--high";
            indicator.textContent = "⚡ high";
          }
        }
        dropdown.remove();
      });
      dropdown.querySelector(".btn-swap-tag").addEventListener("click", () => {
        const tag = card.querySelector(".tag-pill");
        if (tag) {
          const currentTagText = tag.textContent.trim();
          if (currentTagText === "PCM Backend") {
            tag.className = "tag-pill tag-pill--orange";
            tag.textContent = "SQL Arch";
          } else if (currentTagText === "SQL Arch") {
            tag.className = "tag-pill tag-pill--blue";
            tag.textContent = "Node Engine";
          } else {
            tag.className = "tag-pill tag-pill--cyan";
            tag.textContent = "PCM Backend";
          }
          calculateDomainMetrics(); // Update domain bar graphs instantly
        }
        dropdown.remove();
      });
      dropdown.querySelector(".btn-delete-card").addEventListener("click", () => {
        if (confirm("Are you sure you want to delete this task card option parameter?")) {
          card.remove();
          calculateDomainMetrics(); // Wipes counting configurations instantly
        }
        dropdown.remove();
      });
      dotsBtn.parentElement.appendChild(dropdown);
    });
  }
  // Global overlay window hook listener to close dropdown panels on blank space hits
  document.addEventListener("click", () => {
    document.querySelectorAll(".card-edit-dropdown").forEach(d => d.remove());
  });
  // ==========================================
  // 3. Drop Zone Target Implementation Flow
  // ==========================================
  cardsListContainers.forEach(container => {
    const columnParent = container.closest(".kanban-column");
    container.addEventListener("dragover", (e) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = "move";
      if (columnParent) {
        columnParent.style.backgroundColor = "rgba(0, 180, 216, 0.03)";
        columnParent.style.borderColor = "rgba(0, 180, 216, 0.2)";
      }
    });
    container.addEventListener("dragleave", () => {
      if (columnParent) {
        columnParent.style.backgroundColor = "";
        columnParent.style.borderColor = "";
      }
    });
    container.addEventListener("drop", function (e) {
      e.preventDefault();
      const activeCard = draggedCard || window.activeDynamicInstance;
      if (activeCard) {
        this.appendChild(activeCard);
        const columnTitle = columnParent.querySelector(".column-title").textContent.trim().toLowerCase();
        if (columnTitle.startsWith("done")) {
          activeCard.classList.add("kanban-card--done-highlight");
        } else {
          activeCard.classList.remove("kanban-card--done-highlight");
        }
        calculateDomainMetrics();
      }
    });
  });
  // ==========================================
  // 4. Metric Distribution Recalculator Layer
  // ==========================================
  function calculateDomainMetrics() {
    let domainA = { total: 0, done: 0 };
    let domainB = { total: 0, done: 0 };
    columns.forEach(column => {
      const colTitle = column.querySelector(".column-title").textContent.trim().toLowerCase();
      const countBadge = column.querySelector(".column-count");
      const cards = column.querySelectorAll(".kanban-card");
      // Sync header list text badges immediately
      if (countBadge) countBadge.textContent = `${cards.length}`;
    cards.forEach(card => {
      const tagText = card.querySelector(".tag-pill") ? card.querySelector(".tag-pill").textContent.trim() : "";
      if (tagText === "PCM Backend") {
        domainA.total++;
        if (colTitle.startsWith("done")) domainA.done++;
      } else {
        domainB.total++;
        if (colTitle.startsWith("done")) domainB.done++;
      }
    });
  });
const pctA = domainA.total > 0 ? Math.round((domainA.done / domainA.total) * 100) : 0;
const pctB = domainB.total > 0 ? Math.round((domainB.done / domainB.total) * 100) : 0;
if (domainABar && domainAPct) {
  domainABar.style.width = `${pctA}%`;
  domainAPct.textContent = `${pctA}% Complete`;
}
if (domainBBar && domainBPct) {
  domainBBar.style.width = `${pctB}%`;
  domainBPct.textContent = `${pctB}% Complete`;
}
}
// ==========================================
// 5. Dynamic Task Card Adder Hook Handlers
// ==========================================
const addTaskButtons = document.querySelectorAll(".btn-add-task");
addTaskButtons.forEach(btn => {
  btn.addEventListener("click", function () {
    const columnParent = this.closest(".kanban-column");
    const listContainer = columnParent.querySelector(".cards-list-container");
    if (!listContainer) return;
    const taskTitleInput = prompt("Enter a text description name title payload for this card item:");
    if (!taskTitleInput || taskTitleInput.trim() === "") return;
    const newCard = document.createElement("div");
    newCard.className = "kanban-card";
    newCard.setAttribute("draggable", "true");
    const colTitleText = columnParent.querySelector(".column-title").textContent.trim().toLowerCase();
    const isDone = colTitleText.startsWith("done");
    if (isDone) newCard.classList.add("kanban-card--done-highlight");
    newCard.innerHTML = `<div class="card-top-meta">
      <span class="card-category">Developer</span>
      <span class="card-dots">•••</span>
    </div>
    <h3 class="card-heading">${escapeHTML(taskTitleInput.trim())}</h3>
    <div class="card-tags-row"><span class="tag-pill tag-pill--cyan">PCM Backend</span></div>
    ${isDone
      ? '<div class="card-metrics">Velocity: 0.0 / day<br>Score: 0 %</div>'
      : '<span class="priority-indicator priority-indicator--mid">⚡ mid</span>'}`;
    newCard.addEventListener("dragstart", function (e) {
      window.activeDynamicInstance = this;
      setTimeout(() => { this.style.opacity = "0.4"; }, 0);
      e.dataTransfer.effectAllowed = "move";
    });
    newCard.addEventListener("dragend", function () {
      window.activeDynamicInstance = null;
      this.style.opacity = "1";
      columns.forEach(col => { col.style.backgroundColor = ""; col.style.borderColor = ""; });
    });
    listContainer.appendChild(newCard);
    setupCardOptions(newCard); // Hook option click settings on the fly onto new card parameters
    calculateDomainMetrics();
  });
});
function escapeHTML(str) {
  return str.replace(/[&<>'"]/g, tag => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
  }[tag] || tag));
}
// Initial runtime script triggers execution loops
initializeCards();
  calculateDomainMetrics();
});