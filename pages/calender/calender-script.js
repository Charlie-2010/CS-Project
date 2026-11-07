document.addEventListener('DOMContentLoaded', () => {
    // === Core Components Selectors Matrix ===
    const calendarGridMatrix = document.getElementById('calendar-grid-matrix');
    const currentMonthDisplay = document.getElementById('current-month-display');
    const timelineDateTitle = document.getElementById('timeline-date-title');
    const timelineEventsWrapper = document.getElementById('timeline-events-wrapper');

    const prevMonthBtn = document.getElementById('prev-month-btn');
    const nextMonthBtn = document.getElementById('next-month-btn');
    const filterButtons = document.querySelectorAll('.filter-btn');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    const profilePill = document.getElementById('profile-pill');

    const eventModal = document.getElementById('event-modal');
    const openModalTrigger = document.getElementById('add-event-quick-trigger');
    const closeModalBtn = document.getElementById('modal-close-btn');
    const eventCreationForm = document.getElementById('event-creation-form');

    // === System State Database Structure ===
    const state = {
        currentDate: new Date(2024, 9, 1), // Oct 2024 per UI mockup baseline
        selectedDay: 24, // Active highlighted day anchor
        activeFilter: 'Weekly',
        eventsDatabase: {
            "2024-09-01": [{ title: "SQL Arch Review", start: "10:00AM", end: "11:30AM", priority: "mid", theme: "cyan" }],
            "2024-09-03": [{ title: "Node Route Dev (PCM Mock)", start: "01:30PM", end: "03:00PM", priority: "high", theme: "blue" }],
            "2024-09-06": [{ title: "SQL Arch Review", start: "09:00AM", end: "10:30AM", priority: "mid", theme: "cyan" }],
            "2024-09-07": [{ title: "SQL Arch Review", start: "04:00PM", end: "05:30PM", priority: "mid", theme: "cyan" }],
            "2024-09-10": [{ title: "Node Route Dev (PCM Mock)", start: "01:30PM", end: "03:00PM", priority: "high", theme: "blue" }],
            "2024-09-13": [{ title: "Node Route Dev (PCM Mock)", start: "11:00AM", end: "12:30PM", priority: "high", theme: "blue" }],
            "2024-09-15": [{ title: "SQL Arch Dev", start: "02:00PM", end: "03:30PM", priority: "mid", theme: "blue" }],
            "2024-09-20": [{ title: "Node Route Express Auth", start: "03:00PM", end: "04:30PM", priority: "high", theme: "purple" }],
            "2024-09-24": [
                { title: "Backend PCM Mock Route Handlers (high)", start: "10:00AM", end: "11:30AM", priority: "high", theme: "cyan" },
                { title: "SQL Schema Migration Script (mid)", start: "01:30PM", end: "03:00PM", priority: "mid", theme: "blue" },
                { title: "Express Auth Middleware Refactor", start: "04:30PM", end: "06:00PM", priority: "high", theme: "purple" }
            ],
            "2024-09-25": [{ title: "Refactor Express Auth", start: "09:30AM", end: "11:00AM", priority: "high", theme: "purple" }],
            "2024-09-28": [{ title: "Node Route Dev (PCM Mock)", start: "01:30PM", end: "03:00PM", priority: "high", theme: "purple" }]
        }
    };

    const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
    const monthShort = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

    function init() {
        renderCalendarGrid();
        renderTimelinePanel();
        setupEventListeners();
    }

    // === Calendar Days Layout Rendering Loop ===
    function renderCalendarGrid() {
        if (!calendarGridMatrix) return;
        calendarGridMatrix.innerHTML = '';

        const year = state.currentDate.getFullYear();
        const month = state.currentDate.getMonth();

        currentMonthDisplay.textContent = `${monthNames[month]} ${year}`;

        const firstDayIndex = new Date(year, month, 1).getDay();
        const totalDaysInMonth = new Date(year, month + 1, 0).getDate();
        const totalDaysInPrevMonth = new Date(year, month, 0).getDate();

        // Previous month filler nodes
        for (let i = firstDayIndex - 1; i >= 0; i--) {
            const dayNum = totalDaysInPrevMonth - i;
            createDayCell(dayNum, true, false);
        }

        // Active month cell nodes
        for (let day = 1; day <= totalDaysInMonth; day++) {
            const isSelected = (day === state.selectedDay);
            createDayCell(day, false, isSelected);
        }

        // Next month filler nodes to satisfy grid rows
        const renderedCellsCount = firstDayIndex + totalDaysInMonth;
        const totalCellsNeeded = 42;
        for (let nextDay = 1; nextDay <= (totalCellsNeeded - renderedCellsCount); nextDay++) {
            createDayCell(nextDay, true, false);
        }
    }

    function createDayCell(dayNumber, isMuted, isSelected) {
        const cell = document.createElement('div');
        cell.classList.add('grid-day');
        if (isMuted) cell.classList.add('dynamic-muted-day');
        if (isSelected && !isMuted) cell.classList.add('active-selected-day');

        cell.innerHTML = `<span class="day-number">${dayNumber}</span>`;

        const tagListWrapper = document.createElement('div');
        tagListWrapper.classList.add('event-tag-list');

        if (!isMuted) {
            const lookupString = getDateLookupString(dayNumber);
            const explicitDayEvents = state.eventsDatabase[lookupString] || [];
            explicitDayEvents.forEach(evt => {
                const tag = document.createElement('div');
                tag.classList.add('event-tag', `tag-${evt.theme}`);
                tag.textContent = evt.title;
                tagListWrapper.appendChild(tag);
            });

            cell.addEventListener('click', () => {
                document.querySelectorAll('.active-selected-day').forEach(c => c.classList.remove('active-selected-day'));
                cell.classList.add('active-selected-day');
                state.selectedDay = dayNumber;
                renderTimelinePanel();
            });
        }

        cell.appendChild(tagListWrapper);
        calendarGridMatrix.appendChild(cell);
    }

    // === Timeline Side Panel Synchronization ===
    function renderTimelinePanel() {
        if (!timelineDateTitle || !timelineEventsWrapper) return;

        const monthStr = monthShort[state.currentDate.getMonth()];
        timelineDateTitle.textContent = `${monthStr} ${state.selectedDay}${getOrdinalSuffix(state.selectedDay)}`;

        timelineEventsWrapper.innerHTML = '';
        const dateKey = getDateLookupString(state.selectedDay);
        const dailyEvents = state.eventsDatabase[dateKey] || [];

        if (dailyEvents.length === 0) {
            timelineEventsWrapper.innerHTML = `<p class="time-range" style="padding:20px; text-align:center;">No task entries scheduled.</p>`;
            return;
        }

        dailyEvents.forEach(event => {
            const card = document.createElement('div');
            card.classList.add('timeline-card', `border-${event.theme}`);
            card.innerHTML = `
                <div class="timeline-card__header">
                    <span class="time-range">${event.start} - ${event.end}</span>
                    <button class="card-options-btn">•••</button>
                </div>
                <h3 class="timeline-card__title">${event.title}</h3>
                <div class="timeline-card__footer">
                    <span class="priority-badge status-${event.priority}">${event.priority}</span>
                    <span class="status-icon success">✓</span>
                </div>
            `;
            timelineEventsWrapper.appendChild(card);
        });
    }

    // === Core UI Event Interceptors ===
    function setupEventListeners() {
        if (prevMonthBtn) {
            prevMonthBtn.addEventListener('click', () => shiftMonthOffset(-1));
        }
        if (nextMonthBtn) {
            nextMonthBtn.addEventListener('click', () => shiftMonthOffset(1));
        }

        filterButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                filterButtons.forEach(b => b.classList.remove('active'));
                e.currentTarget.classList.add('active');
                state.activeFilter = e.currentTarget.getAttribute('data-filter');
            });
        });

        if (sidebarToggle && sidebar) {
            sidebarToggle.addEventListener('click', (e) => {
                e.stopPropagation();
                sidebar.classList.toggle('expanded');
            });

            document.addEventListener('click', (event) => {
                if (!sidebar.contains(event.target) && sidebar.classList.contains('expanded')) {
                    sidebar.classList.remove('expanded');
                }
            });
        }

        if (profilePill) {
            profilePill.addEventListener('click', () => {
                window.location.href = '../profile/profile.html';
            });
        }

        if (openModalTrigger) openModalTrigger.addEventListener('click', () => eventModal.classList.add('active'));
        if (closeModalBtn) closeModalBtn.addEventListener('click', () => eventModal.classList.remove('active'));

        if (eventCreationForm) {
            eventCreationForm.addEventListener('submit', (e) => {
                e.preventDefault();

                const title = document.getElementById('event-title').value;
                const startRaw = document.getElementById('event-start').value;
                const endRaw = document.getElementById('event-end').value;
                const priority = document.getElementById('event-priority').value;
                const theme = document.getElementById('event-theme').value;

                const dateKey = getDateLookupString(state.selectedDay);
                if (!state.eventsDatabase[dateKey]) state.eventsDatabase[dateKey] = [];

                state.eventsDatabase[dateKey].push({
                    title,
                    start: formatTime12H(startRaw),
                    end: formatTime12H(endRaw),
                    priority,
                    theme
                });

                eventCreationForm.reset();
                eventModal.classList.remove('active');

                renderCalendarGrid();
                renderTimelinePanel();
            });
        }
    }

    // === State Handlers & Mathematics Normalizers ===
    function shiftMonthOffset(offset) {
        state.currentDate.setMonth(state.currentDate.getMonth() + offset);
        state.selectedDay = 1;
        renderCalendarGrid();
        renderTimelinePanel();
    }

    function getDateLookupString(day) {
        const year = state.currentDate.getFullYear();
        const month = String(state.currentDate.getMonth()).padStart(2, '0');
        const dayStr = String(day).padStart(2, '0');
        return `${year}-${month}-${dayStr}`;
    }

    function getOrdinalSuffix(val) {
        if (val > 3 && val < 21) return 'th';
        switch (val % 10) {
            case 1: return "st";
            case 2: return "nd";
            case 3: return "rd";
            default: return "th";
        }
    }

    function formatTime12H(time24) {
        const [hrs, mins] = time24.split(':');
        let hours = parseInt(hrs, 10);
        const ampm = hours >= 12 ? 'PM' : 'AM';
        hours = hours % 12;
        hours = hours ? hours : 12;
        return `${hours}:${mins}${ampm}`;
    }

    init();
});