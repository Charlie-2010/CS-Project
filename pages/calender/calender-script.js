document.addEventListener("DOMContentLoaded", () => {
  const grid = document.getElementById("calendar-grid-matrix");
  const monthLabel = document.getElementById("current-month-display");
  const timelineTitle = document.getElementById("timeline-date-title");
  const timeline = document.getElementById("timeline-events-wrapper");
  const modal = document.getElementById("event-modal");
  const form = document.getElementById("event-creation-form");
  const formError = document.getElementById("event-form-error");
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const addDays = (date, offset) => {
    const result = new Date(date);
    result.setDate(result.getDate() + offset);
    return result;
  };
  const dateKey = date => `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
  const formatTime = time => {
    const [hourText, minute] = time.split(":");
    const hour = Number(hourText);
    return `${hour % 12 || 12}:${minute} ${hour >= 12 ? "PM" : "AM"}`;
  };
  const dayName = new Intl.DateTimeFormat(undefined, { weekday: "long" });
  const fullDate = new Intl.DateTimeFormat(undefined, { month: "long", day: "numeric", year: "numeric" });

  const events = [
    { date: addDays(today, 0), title: "Review project milestones", start: "09:30", end: "10:30", priority: "HIGH", theme: "cyan" },
    { date: addDays(today, 1), title: "Update database schema", start: "13:00", end: "14:00", priority: "MEDIUM", theme: "blue" },
    { date: addDays(today, 3), title: "Prepare sprint notes", start: "11:00", end: "11:45", priority: "LOW", theme: "purple" },
    { date: addDays(today, 8), title: "Review API integration", start: "15:00", end: "16:00", priority: "HIGH", theme: "cyan" },
    { date: addDays(today, -3), title: "Plan weekly priorities", start: "10:00", end: "10:30", priority: "MEDIUM", theme: "blue" }
  ];
  let currentMonth = new Date(today.getFullYear(), today.getMonth(), 1);
  let selectedDate = new Date(today);
  let activeFilter = "Weekly";

  function matchesFilter(date) {
    if (activeFilter === "Overall") return true;
    if (activeFilter === "Monthly") {
      return date.getFullYear() === currentMonth.getFullYear() && date.getMonth() === currentMonth.getMonth();
    }
    const weekStart = new Date(selectedDate);
    weekStart.setDate(selectedDate.getDate() - selectedDate.getDay());
    const weekEnd = addDays(weekStart, 7);
    return date >= weekStart && date < weekEnd;
  }

  function renderCalendar() {
    const year = currentMonth.getFullYear();
    const month = currentMonth.getMonth();
    monthLabel.textContent = new Intl.DateTimeFormat(undefined, { month: "long", year: "numeric" }).format(currentMonth);
    grid.replaceChildren();

    const firstWeekday = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const daysInPreviousMonth = new Date(year, month, 0).getDate();
    const cellCount = Math.ceil((firstWeekday + daysInMonth) / 7) * 7;
    grid.style.gridTemplateRows = `repeat(${cellCount / 7}, minmax(0, 1fr))`;

    for (let index = 0; index < cellCount; index++) {
      const dayNumber = index - firstWeekday + 1;
      let date;
      let muted = false;
      if (dayNumber < 1) {
        date = new Date(year, month - 1, daysInPreviousMonth + dayNumber);
        muted = true;
      } else if (dayNumber > daysInMonth) {
        date = new Date(year, month + 1, dayNumber - daysInMonth);
        muted = true;
      } else {
        date = new Date(year, month, dayNumber);
      }
      const cell = document.createElement("button");
      cell.type = "button";
      cell.className = `grid-day${muted ? " dynamic-muted-day" : ""}`;
      if (dateKey(date) === dateKey(selectedDate)) cell.classList.add("active-selected-day");
      cell.setAttribute("aria-pressed", String(dateKey(date) === dateKey(selectedDate)));
      cell.setAttribute("aria-label", fullDate.format(date));
      const number = document.createElement("span");
      number.className = "day-number";
      number.textContent = String(date.getDate());
      cell.appendChild(number);

      const tagList = document.createElement("span");
      tagList.className = "event-tag-list";
      events.filter(event => dateKey(event.date) === dateKey(date) && matchesFilter(event.date)).forEach(event => {
        const tag = document.createElement("span");
        tag.className = `event-tag tag-${event.theme}`;
        tag.textContent = event.title;
        tagList.appendChild(tag);
      });
      cell.appendChild(tagList);
      cell.addEventListener("click", () => {
        selectedDate = new Date(date);
        if (muted) currentMonth = new Date(date.getFullYear(), date.getMonth(), 1);
        renderCalendar();
        renderTimeline();
      });
      grid.appendChild(cell);
    }
  }

  function filteredEvents() {
    return events.filter(event => matchesFilter(event.date))
      .sort((a, b) => a.date - b.date || a.start.localeCompare(b.start));
  }

  function renderTimeline() {
    const title = activeFilter === "Weekly"
      ? `${dayName.format(selectedDate)} · week view`
      : activeFilter === "Monthly"
        ? new Intl.DateTimeFormat(undefined, { month: "long", year: "numeric" }).format(currentMonth)
        : "All scheduled tasks";
    timelineTitle.textContent = title;
    timeline.replaceChildren();
    const visibleEvents = filteredEvents();
    if (!visibleEvents.length) {
      const empty = document.createElement("p");
      empty.className = "calendar-empty-state";
      empty.textContent = "No tasks match this date range. Add an event to get started.";
      timeline.appendChild(empty);
      return;
    }

    visibleEvents.forEach(event => {
      const card = document.createElement("article");
      card.className = `timeline-card border-${event.theme}`;
      const header = document.createElement("div");
      header.className = "timeline-card__header";
      const dateLabel = document.createElement("span");
      dateLabel.className = "time-range";
      dateLabel.textContent = `${fullDate.format(event.date)} · ${formatTime(event.start)} - ${formatTime(event.end)}`;
      header.appendChild(dateLabel);
      const title = document.createElement("h3");
      title.className = "timeline-card__title";
      title.textContent = event.title;
      const footer = document.createElement("div");
      footer.className = "timeline-card__footer";
      const priority = document.createElement("span");
      priority.className = `priority-badge status-${event.priority.toLowerCase()}`;
      priority.textContent = ({ LOW: "Low", MEDIUM: "Medium", HIGH: "High", URGENT: "Urgent" })[event.priority];
      footer.appendChild(priority);
      card.append(header, title, footer);
      timeline.appendChild(card);
    });
  }

  document.getElementById("prev-month-btn").addEventListener("click", () => {
    currentMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1, 1);
    selectedDate = new Date(currentMonth);
    renderCalendar();
    renderTimeline();
  });
  document.getElementById("next-month-btn").addEventListener("click", () => {
    currentMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 1);
    selectedDate = new Date(currentMonth);
    renderCalendar();
    renderTimeline();
  });

  document.querySelectorAll(".filter-btn").forEach(button => {
    button.setAttribute("aria-pressed", String(button.dataset.filter === activeFilter));
    button.addEventListener("click", () => {
      activeFilter = button.dataset.filter;
      document.querySelectorAll(".filter-btn").forEach(item => {
        item.classList.toggle("active", item === button);
        item.setAttribute("aria-pressed", String(item === button));
      });
      renderCalendar();
      renderTimeline();
    });
  });

  const openButton = document.getElementById("add-event-quick-trigger");
  const closeButton = document.getElementById("modal-close-btn");
  let modalOpener = null;
  function closeModal() {
    modal.classList.remove("active");
    formError.textContent = "";
    modalOpener?.focus();
    modalOpener = null;
    modal.setAttribute("aria-hidden", "true");
  }
  openButton.addEventListener("click", () => {
    modalOpener = document.activeElement;
    modal.classList.add("active");
    modal.setAttribute("aria-hidden", "false");
    document.getElementById("event-title").focus();
  });
  closeButton.addEventListener("click", closeModal);
  modal.addEventListener("click", event => {
    if (event.target === modal) closeModal();
  });
  document.addEventListener("keydown", event => {
    if (event.key === "Escape" && modal.classList.contains("active")) closeModal();
  });

  form.addEventListener("submit", event => {
    event.preventDefault();
    const title = document.getElementById("event-title").value.trim();
    const start = document.getElementById("event-start").value;
    const end = document.getElementById("event-end").value;
    if (!title) {
      formError.textContent = "Enter a task title.";
      document.getElementById("event-title").focus();
      return;
    }
    if (end <= start) {
      formError.textContent = "End time must be later than start time.";
      document.getElementById("event-end").focus();
      return;
    }
    events.push({
      date: new Date(selectedDate),
      title,
      start,
      end,
      priority: document.getElementById("event-priority").value,
      theme: document.getElementById("event-theme").value
    });
    form.reset();
    closeModal();
    renderCalendar();
    renderTimeline();
    window.AppUI.toast("Event added to your temporary calendar.", "success");
  });

  renderCalendar();
  renderTimeline();
});
