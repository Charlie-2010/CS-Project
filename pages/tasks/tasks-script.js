document.addEventListener("DOMContentLoaded", () => {
  const columns = [...document.querySelectorAll(".kanban-column")];
  const modal = document.getElementById("task-modal");
  const form = document.getElementById("task-form");
  const titleInput = document.getElementById("task-title-input");
  const descriptionInput = document.getElementById("task-description-input");
  const priorityInput = document.getElementById("task-priority-input");
  const categoryInput = document.getElementById("task-category-input");
  const titleError = document.getElementById("task-title-error");
  const taskData = window.CogniPlanTasks;
  let draggedCard = null;
  let draggedFromStatus = null;
  let editingCard = null;
  let newTaskStatus = "Draft";
  let modalOpener = null;

  function getStatus(column) {
    return column.querySelector(".column-title").childNodes[0].textContent.trim();
  }

  function updateBoard() {
    columns.forEach(column => {
      const container = column.querySelector(".cards-list-container");
      const cards = [...container.querySelectorAll(".kanban-card")];
      const count = column.querySelector(".column-count");
      if (count) count.textContent = `(${cards.length})`;
      let empty = container.querySelector(".board-empty-state");
      if (cards.length === 0 && !empty) {
        empty = document.createElement("p");
        empty.className = "board-empty-state";
        empty.textContent = "No tasks here yet. Add one or drag a task into this column.";
        container.appendChild(empty);
      } else if (cards.length > 0) {
        empty?.remove();
      }
    });

    const domains = {
      a: { total: 0, done: 0 },
      b: { total: 0, done: 0 }
    };
    columns.forEach(column => {
      const isDone = getStatus(column).toLowerCase().startsWith("done");
      column.querySelectorAll(".kanban-card").forEach(card => {
        const domain = card.querySelector(".tag-pill")?.textContent.trim() === "PCM Backend" ? domains.a : domains.b;
        domain.total++;
        if (isDone) domain.done++;
      });
    });
    const percentA = domains.a.total ? Math.round(domains.a.done / domains.a.total * 100) : 0;
    const percentB = domains.b.total ? Math.round(domains.b.done / domains.b.total * 100) : 0;
    const progressA = document.getElementById("domain-a-bar");
    const progressB = document.getElementById("domain-b-bar");
    const progressPctA = document.getElementById("domain-a-pct");
    const progressPctB = document.getElementById("domain-b-pct");
    if (progressA) progressA.style.width = `${percentA}%`;
    if (progressB) progressB.style.width = `${percentB}%`;
    if (progressPctA) progressPctA.textContent = `${percentA}% Complete`;
    if (progressPctB) progressPctB.textContent = `${percentB}% Complete`;
  }

  function setCardPriority(card, priority) {
    const normalized = taskData.normalizePriority(priority);
    const priorityEl = card.querySelector(".priority-indicator");
    priorityEl.className = `priority-indicator priority-indicator--${normalized.toLowerCase()}`;
    priorityEl.textContent = `⚡ ${normalized.toLowerCase()}`;
    return normalized;
  }

  function createCard(task) {
    const card = document.createElement("article");
    card.className = "kanban-card";
    card.draggable = true;
    card.dataset.id = task.id;
    card.innerHTML = `
      <div class="card-top-meta"><span class="card-category"></span><button type="button" class="card-dots" aria-label="Task options">•••</button></div>
      <h3 class="card-heading"></h3>
      ${task.description ? '<p class="card-description"></p>' : ""}
      <div class="card-tags-row"><span class="tag-pill"></span></div>
      <div class="card-footer-row"><span class="priority-indicator"></span></div>`;
    card.querySelector(".card-category").textContent = task.status;
    card.querySelector(".card-heading").textContent = task.title;
    card.querySelector(".card-description")?.replaceChildren(document.createTextNode(task.description));
    const tag = card.querySelector(".tag-pill");
    tag.textContent = task.category;
    tag.classList.add(task.category === "SQL Arch" ? "tag-pill--orange" : task.category === "Node Engine" ? "tag-pill--blue" : "tag-pill--cyan");
    setCardPriority(card, task.priority);
    bindCard(card);
    return card;
  }

  function renderBoard() {
    columns.forEach(column => column.querySelector(".cards-list-container").replaceChildren());
    taskData.getAll().forEach(task => {
      const column = columns.find(item => getStatus(item) === task.status);
      if (!column) throw new Error(`No task column exists for status: ${task.status}`);
      column.querySelector(".cards-list-container").appendChild(createCard(task));
    });
    updateBoard();
  }

  function bindCard(card) {
    card.setAttribute("draggable", "true");
    card.addEventListener("dragstart", event => {
      draggedCard = card;
      draggedFromStatus = getStatus(card.closest(".kanban-column"));
      card.classList.add("is-dragging");
      event.dataTransfer.effectAllowed = "move";
      event.dataTransfer.setData("text/plain", card.querySelector(".card-heading").textContent);
    });
    card.addEventListener("dragend", () => {
      card.classList.remove("is-dragging");
      draggedCard = null;
      draggedFromStatus = null;
      columns.forEach(column => column.classList.remove("is-drop-target"));
    });

    const optionButton = card.querySelector(".card-dots");
    if (optionButton && optionButton.tagName !== "BUTTON") {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "card-dots";
      button.setAttribute("aria-label", "Task options");
      button.textContent = optionButton.textContent;
      optionButton.replaceWith(button);
      bindOptions(card, button);
    } else if (optionButton && !optionButton.dataset.bound) {
      bindOptions(card, optionButton);
    }
  }

  function bindOptions(card, button) {
    button.dataset.bound = "true";
    button.addEventListener("click", event => {
      event.stopPropagation();
      document.querySelectorAll(".card-edit-dropdown").forEach(menu => menu.remove());
      const menu = document.createElement("div");
      menu.className = "card-edit-dropdown";
      menu.innerHTML = '<button type="button" class="dropdown-item edit-task">Edit task</button><button type="button" class="dropdown-item toggle-priority">Toggle priority</button><button type="button" class="dropdown-item dropdown-item--delete delete-task">Delete task</button>';
      button.closest(".card-top-meta").appendChild(menu);
      menu.querySelector(".edit-task").addEventListener("click", () => {
        const category = card.querySelector(".tag-pill").textContent;
        const priority = [...card.querySelector(".priority-indicator").classList]
          .find(name => name.startsWith("priority-indicator--"))?.replace("priority-indicator--", "") || "MEDIUM";
        openModal({
          title: card.querySelector(".card-heading").textContent,
          description: card.querySelector(".card-description")?.textContent || "",
          category,
          priority
        }, card);
        menu.remove();
      });
      menu.querySelector(".toggle-priority").addEventListener("click", () => {
        const current = taskData.normalizePriority(
          [...card.querySelector(".priority-indicator").classList]
            .find(name => name.startsWith("priority-indicator--"))
            ?.replace("priority-indicator--", "")
        );
        const nextIndex = (taskData.priorities.indexOf(current) + 1) % taskData.priorities.length;
        taskData.update(card.dataset.id, { priority: taskData.priorities[nextIndex] });
        setCardPriority(card, taskData.priorities[nextIndex]);
        menu.remove();
      });
      menu.querySelector(".delete-task").addEventListener("click", () => {
        if (window.confirm("Delete this task? This action cannot be undone.")) {
          taskData.remove(card.dataset.id);
          renderBoard();
          window.AppUI.toast("Task deleted.", "success");
        }
        menu.remove();
      });
    });
  }

  function openModal(values, card = null, status = "Draft") {
    modalOpener = card?.querySelector(".card-dots") || document.activeElement;
    editingCard = card;
    newTaskStatus = status;
    document.getElementById("task-modal-title").textContent = card ? "Edit task" : "Add task";
    document.getElementById("task-save").textContent = card ? "Save changes" : "Add task";
    titleInput.value = values?.title || "";
    descriptionInput.value = values?.description || "";
    priorityInput.value = taskData.normalizePriority(values?.priority || "MEDIUM");
    categoryInput.value = values?.category || "PCM Backend";
    titleError.textContent = "";
    modal.classList.add("is-open");
    modal.setAttribute("aria-hidden", "false");
    titleInput.focus();
  }

  function closeModal() {
    modal.classList.remove("is-open");
    editingCard = null;
    form.reset();
    modalOpener?.focus();
    modalOpener = null;
    modal.setAttribute("aria-hidden", "true");
  }

  document.querySelectorAll(".btn-add-task").forEach(button => {
    button.addEventListener("click", () => openModal(null, null, getStatus(button.closest(".kanban-column"))));
  });
  document.getElementById("task-modal-close").addEventListener("click", closeModal);
  document.getElementById("task-cancel").addEventListener("click", closeModal);
  modal.addEventListener("click", event => {
    if (event.target === modal) closeModal();
  });
  document.addEventListener("keydown", event => {
    if (event.key === "Escape" && modal.classList.contains("is-open")) closeModal();
  });

  form.addEventListener("submit", event => {
    event.preventDefault();
    const title = titleInput.value.trim();
    if (!title) {
      titleError.textContent = "Enter a task title.";
      titleInput.setAttribute("aria-invalid", "true");
      titleInput.focus();
      return;
    }
    titleInput.removeAttribute("aria-invalid");
    const values = {
      title,
      description: descriptionInput.value.trim(),
      priority: priorityInput.value,
      category: categoryInput.value
    };
    const wasEditing = Boolean(editingCard);
    if (editingCard) {
      taskData.update(editingCard.dataset.id, values);
    } else {
      taskData.add({ ...values, status: newTaskStatus });
    }
    closeModal();
    renderBoard();
    window.AppUI.toast(wasEditing ? "Task updated." : "Task added.", "success");
  });
  titleInput.addEventListener("input", () => {
    titleError.textContent = "";
    titleInput.removeAttribute("aria-invalid");
  });

  columns.forEach(column => {
    const container = column.querySelector(".cards-list-container");
    container.addEventListener("dragover", event => {
      event.preventDefault();
      event.dataTransfer.dropEffect = "move";
      column.classList.add("is-drop-target");
      const after = [...container.querySelectorAll(".kanban-card:not(.is-dragging)")].find(card => {
        return event.clientY <= card.getBoundingClientRect().top + card.offsetHeight / 2;
      });
      if (draggedCard) container.insertBefore(draggedCard, after || null);
    });
    container.addEventListener("dragleave", event => {
      if (!container.contains(event.relatedTarget)) column.classList.remove("is-drop-target");
    });
    container.addEventListener("drop", event => {
      event.preventDefault();
      column.classList.remove("is-drop-target");
      if (draggedCard) {
        const status = getStatus(column);
        if (draggedFromStatus !== status) {
          taskData.update(draggedCard.dataset.id, { status });
        }
        draggedCard.querySelector(".card-category").textContent = status;
        draggedCard = null;
        draggedFromStatus = null;
      }
      updateBoard();
    });
  });

  document.addEventListener("click", event => {
    if (!event.target.closest(".card-top-meta")) {
      document.querySelectorAll(".card-edit-dropdown").forEach(menu => menu.remove());
    }
  });
  renderBoard();
  window.addEventListener("storage", event => {
    if (event.key === taskData.storageKey) renderBoard();
  });
});
