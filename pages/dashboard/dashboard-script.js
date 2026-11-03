document.addEventListener('DOMContentLoaded', () => {
    const cards = document.querySelectorAll('.task-card');
    const columns = document.querySelectorAll('.kanban-col');

    let draggedCard = null;

    // Initialize HTML5 Drag and Drop events for items
    cards.forEach(card => {
        card.addEventListener('dragstart', function(e) {
            draggedCard = this;
            setTimeout(() => {
                this.style.display = 'none';
            }, 0);
        });

        card.addEventListener('dragend', function() {
            setTimeout(() => {
                this.style.display = 'block';
                draggedCard = null;
            }, 0);
        });

        // Initialize priority star button interaction limits
        const star = card.querySelector('.star-toggle');
        if (star) {
            star.addEventListener('click', function(e) {
                e.stopPropagation(); // Avoid picking up parent task card element triggers
                this.classList.toggle('star-toggle--active');
                this.textContent = this.classList.contains('star-toggle--active') ? '★' : '☆';
            });
        }
    });

    // Initialize Column Drop zones
    columns.forEach(column => {
        const cardsContainer = column.querySelector('.kanban-col__cards');

        column.addEventListener('dragover', function(e) {
            e.preventDefault();
        });

        column.addEventListener('dragenter', function(e) {
            e.preventDefault();
            this.style.backgroundColor = 'rgba(255, 255, 255, 0.02)';
        });

        column.addEventListener('dragleave', function() {
            this.style.backgroundColor = 'transparent';
        });

        column.addEventListener('drop', function(e) {
            this.style.backgroundColor = 'transparent';
            if (draggedCard && cardsContainer) {
                cardsContainer.appendChild(draggedCard);
                adaptCardToColumnStatus(draggedCard, this.getAttribute('data-status'));
            }
        });
    });

    // Contextual workflow renderer helper adjusting inner node states dynamically
    function adaptCardToColumnStatus(card, status) {
        // Strip any context progress or complete tags cleanly first
        const existingProgress = card.querySelector('.progress-block');
        if (existingProgress) existingProgress.remove();

        const checkedPills = card.querySelectorAll('.task-pill--checked');
        checkedPills.forEach(pill => {
            pill.classList.remove('task-pill--checked');
            const txt = pill.querySelector('.task-pill__text');
            if (txt) txt.classList.remove('line-through');
            const check = pill.querySelector('.checked-mark');
            if (check) check.remove();
        });

        // Map behavior context allocations matches
        if (status === 'In Progress') {
            const progressHtml = `
                <div class="progress-block">
                    <div class="progress-block__label"><span>Progress</span><span>50%</span></div>
                    <div class="progress-block__track"><div class="progress-block__fill" style="width: 50%"></div></div>
                </div>
            `;
            card.insertAdjacentHTML('beforeend', progressHtml);
        } else if (status === 'Done') {
            const pills = card.querySelectorAll('.task-pill');
            pills.forEach(pill => {
                pill.classList.add('task-pill--checked');
                const txt = pill.querySelector('.task-pill__text');
                if (txt) txt.classList.add('line-through');
                
                if (!pill.querySelector('.checked-mark')) {
                    const checkMark = document.createElement('span');
                    checkMark.className = 'checked-mark';
                    checkMark.textContent = '✓';
                    pill.appendChild(checkMark);
                }
            });
        }
    }
});