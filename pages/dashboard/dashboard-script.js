document.addEventListener("DOMContentLoaded", () => {
  const columns = [...document.querySelectorAll(".kanban-col")];
  const taskData = window.CogniPlanTasks;
  let draggedCard = null;
  let draggedFromStatus = null;

  function getStatus(column) {
    return column.dataset.status;
  }

  function updateEmptyStates() {
    columns.forEach(column => {
      const container = column.querySelector(".kanban-col__cards");
      const cards = container.querySelectorAll(".task-card");
      let empty = container.querySelector(".kanban-empty-state");
      if (!cards.length && !empty) {
        empty = document.createElement("p");
        empty.className = "kanban-empty-state";
        empty.textContent = "Nothing here yet. Drag a task into this column.";
        container.appendChild(empty);
      } else if (cards.length) {
        empty?.remove();
      }
    });
  }

  function updateCardForStatus(card, status) {
    card.dataset.status = status;
    card.querySelector(".task-card__status").textContent = status;
    card.classList.toggle("task-card--done", status === "Done");
    const progress = card.querySelector(".progress-block");
    if (status === "In Progress" && !progress) {
      const block = document.createElement("div");
      block.className = "progress-block";
      block.innerHTML = '<div class="progress-block__label"><span>Progress</span><span>50%</span></div><div class="progress-block__track"><div class="progress-block__fill" style="width:50%"></div></div>';
      card.appendChild(block);
    } else if (status !== "In Progress") {
      progress?.remove();
    }

    card.querySelectorAll(".task-pill").forEach(pill => {
      const checked = status === "Done";
      pill.classList.toggle("task-pill--checked", checked);
      pill.querySelector(".task-pill__text")?.classList.toggle("line-through", checked);
      let check = pill.querySelector(".checked-mark");
      if (checked && !check) {
        check = document.createElement("span");
        check.className = "checked-mark";
        check.textContent = "✓";
        pill.appendChild(check);
      } else if (!checked) {
        check?.remove();
      }
    });
    updateEmptyStates();
  }

  function makeTaskCard(task) {
    const card = document.createElement("div");
    card.className = "task-card";
    card.dataset.id = task.id;
    const meta = document.createElement("div");
    meta.className = "task-card__meta";
    const heading = document.createElement("h3");
    heading.className = "task-card__heading";
    heading.textContent = task.title;
    const menu = document.createElement("span");
    menu.className = "task-card__menu";
    menu.textContent = "⋮";
    meta.append(heading, menu);

    const status = document.createElement("span");
    status.className = "task-card__status";
    status.textContent = task.status;

    const pill = document.createElement("div");
    const badgeText = task.category === "PCM Backend" ? "A" : task.category === "SQL Arch" ? "B" : "C";
    const pillColor = task.category === "PCM Backend" ? "blue" : task.category === "SQL Arch" ? "orange" : "purple";
    pill.className = `task-pill task-pill--${pillColor}`;
    const badge = document.createElement("span");
    badge.className = "task-pill__badge";
    badge.textContent = badgeText;
    const pillText = document.createElement("p");
    pillText.className = "task-pill__text";
    pillText.textContent = task.category;
    pill.append(badge, pillText);

    const footer = document.createElement("div");
    footer.className = "task-card__footer";
    const priority = document.createElement("span");
    priority.className = `task-card__priority task-card__priority--${task.priority.toLowerCase()}`;
    priority.textContent = task.priority;
    const favorite = document.createElement("button");
    favorite.type = "button";
    favorite.className = `star-toggle${task.favorite ? " star-toggle--active" : ""}`;
    favorite.setAttribute("aria-label", "Toggle task favorite");
    favorite.setAttribute("aria-pressed", String(task.favorite));
    favorite.textContent = task.favorite ? "★" : "☆";
    footer.append(priority, favorite);

    card.append(meta, status, pill, footer);
    updateCardForStatus(card, task.status);
    bindCard(card);
    return card;
  }

  function renderBoard() {
    columns.forEach(column => column.querySelector(".kanban-col__cards").replaceChildren());
    taskData.getAll().forEach(task => {
      const column = columns.find(item => getStatus(item) === task.status);
      if (!column) throw new Error(`No dashboard column exists for status: ${task.status}`);
      column.querySelector(".kanban-col__cards").appendChild(makeTaskCard(task));
    });
    updateEmptyStates();
  }

  function moveCard(card, destination) {
    const target = columns[destination];
    if (!target || target === card.closest(".kanban-col")) return;
    target.querySelector(".kanban-col__cards").appendChild(card);
    const status = getStatus(target);
    taskData.update(card.dataset.id, { status });
    updateCardForStatus(card, status);
    window.AppUI.toast(`Task moved to ${status}.`, "success");
  }

  function bindCard(card) {
    card.setAttribute("draggable", "true");
    card.setAttribute("tabindex", "0");
    card.setAttribute("role", "listitem");
    card.addEventListener("dragstart", event => {
      draggedCard = card;
      draggedFromStatus = getStatus(card.closest(".kanban-col"));
      card.classList.add("is-dragging");
      event.dataTransfer.effectAllowed = "move";
      event.dataTransfer.setData("text/plain", card.dataset.id);
    });
    card.addEventListener("dragend", () => {
      card.classList.remove("is-dragging");
      draggedCard = null;
      draggedFromStatus = null;
      columns.forEach(column => column.classList.remove("is-drop-target"));
    });
    card.addEventListener("keydown", event => {
      if (!event.altKey || !["ArrowLeft", "ArrowRight"].includes(event.key)) return;
      event.preventDefault();
      const currentIndex = columns.indexOf(card.closest(".kanban-col"));
      moveCard(card, currentIndex + (event.key === "ArrowRight" ? 1 : -1));
      card.focus();
    });
    card.querySelector(".star-toggle").addEventListener("click", event => {
      event.stopPropagation();
      const favorite = !card.querySelector(".star-toggle").classList.contains("star-toggle--active");
      taskData.update(card.dataset.id, { favorite });
      const star = card.querySelector(".star-toggle");
      star.classList.toggle("star-toggle--active", favorite);
      star.textContent = favorite ? "★" : "☆";
      star.setAttribute("aria-pressed", String(favorite));
    });
  }

  columns.forEach(column => {
    const container = column.querySelector(".kanban-col__cards");
    column.setAttribute("role", "region");
    column.setAttribute("aria-label", `${column.querySelector(".kanban-col__title")?.textContent.trim() || "Tasks"} tasks`);
    container.addEventListener("dragover", event => {
      event.preventDefault();
      event.dataTransfer.dropEffect = "move";
      column.classList.add("is-drop-target");
      const afterCard = [...container.querySelectorAll(".task-card:not(.is-dragging)")].find(card => {
        return event.clientY <= card.getBoundingClientRect().top + card.offsetHeight / 2;
      });
      if (draggedCard) container.insertBefore(draggedCard, afterCard || null);
    });
    container.addEventListener("dragleave", event => {
      if (!container.contains(event.relatedTarget)) column.classList.remove("is-drop-target");
    });
    container.addEventListener("drop", event => {
      event.preventDefault();
      column.classList.remove("is-drop-target");
      if (!draggedCard) return;
      const status = getStatus(column);
      if (draggedFromStatus !== status) {
        taskData.update(draggedCard.dataset.id, { status });
        updateCardForStatus(draggedCard, status);
        window.AppUI.toast(`Task moved to ${status}.`, "success");
      }
    });
  });

  renderBoard();
  window.addEventListener("storage", event => {
    if (event.key === taskData.storageKey) renderBoard();
  });
});
