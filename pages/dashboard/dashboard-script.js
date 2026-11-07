document.addEventListener('DOMContentLoaded', () => {
    // === Sidebar Navigation Expansion Interaction Module ===
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebar-toggle');

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

    // === Profile Page button Functionality ===
    const profilebutton=document.querySelector('#profile-pill');
    if (profilebutton) {
        profilebutton.addEventListener('click', () =>{
            window.location.href = '../profile/profile.html';
        });
    }

    // === Kanban Board Drag and Drop Engine ===
    const cards = document.querySelectorAll('.task-card');
    const columns = document.querySelectorAll('.kanban-col');

    let draggedCard = null;

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

        const star = card.querySelector('.star-toggle');
        if (star) {
            star.addEventListener('click', function(e) {
                e.stopPropagation();
                this.classList.toggle('star-toggle--active');
                this.textContent = this.classList.contains('star-toggle--active') ? '★' : '☆';
            });
        }
    });

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

    function adaptCardToColumnStatus(card, status) {
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