document.addEventListener("DOMContentLoaded", () => {
    // --- DOM Elements ---
    const contactItems = document.querySelectorAll(".contact-item");
    const messagesContainer = document.querySelector(".chat-messages-container");
    const inputField = document.querySelector(".chat-input-field");
    const micButton = document.querySelector(".btn-mic");
    const attachButton = document.querySelector(".btn-attach");
    const chatHeaderName = document.querySelector(".chat-header-name");
    
    // Add this helper near the top of your chat.js file under DOM Elements section
    const sidebarLinks = document.querySelectorAll(".menu-cluster__link");
    sidebarLinks.forEach(link => {
        if (link.getAttribute("href") === "messages.html") {
            sidebarLinks.forEach(l => l.classList.remove("active"));
            link.classList.add("active");
        }
    });

    // === Profile Page button Functionality ===
    const profilebutton=document.querySelector('#profile-pill');
    if (profilebutton) {
        profilebutton.addEventListener('click', () =>{
            window.location.href = '../profile/profile.html';
        });
    }
    
    // Sidebar Toggle
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

    // Initialize viewport scroll position to the bottom of the feed
    scrollToBottom();

    // ==========================================
    // 1. Thread Switching Functionality
    // ==========================================
    contactItems.forEach(item => {
        item.addEventListener("click", () => {
            // Remove 'active' state highlighting from the previous selection
            contactItems.forEach(el => el.classList.remove("active"));

            // Assign active highlighting to the selected contact card
            item.classList.add("active");

            // Update target chat room details inside the right workspace window
            const selectedName = item.querySelector(".contact-name").textContent;
            chatHeaderName.textContent = `${selectedName} - Operator`;

            // Clear layout chat screen to simulate entering a clean workspace thread
            messagesContainer.innerHTML = `
        <div class="message-bubble message-bubble--received">
          <div class="message-avatar"></div>
          <div class="message-content-wrapper">
            <div class="message-text">Welcome to the secure encrypted session room for <strong>${selectedName}</strong>. How can I help you today?</div>
          </div>
        </div>
      `;
            scrollToBottom();
        });
    });

    // ==========================================
    // 2. Message Dispatching System
    // ==========================================
    function handleSendMessage() {
        const textContent = inputField.value.trim();
        if (!textContent) return; // Disallow executing on empty entries

        // Capture standard timestamp
        const now = new Date();
        const timeString = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        // Generate output HTML payload structure for Sent message bubbles
        const sentBubble = document.createElement("div");
        sentBubble.className = "message-bubble message-bubble--sent";
        sentBubble.innerHTML = `
      <div class="message-content-wrapper">
        <div class="message-text">${escapeHTML(textContent)}</div>
        <div class="message-timestamp">${timeString}</div>
      </div>
    `;

        // Append to viewport list panel
        messagesContainer.appendChild(sentBubble);
        inputField.value = ""; // Reset entry box layout tracking cleanly
        scrollToBottom();

        // Trigger an automated responsive feedback response to keep interface engaging
        simulateOperatorResponse();
    }

    // Bind Enter keypress configuration to the primary layout text field
    inputField.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            handleSendMessage();
        }
    });

    // ==========================================
    // 3. UI Utility Hook Methods
    // ==========================================
    function scrollToBottom() {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    // Prevent Cross-Site Scripting injections via user chat strings
    function escapeHTML(str) {
        return str.replace(/[&<>'"]/g,
            tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
        );
    }

    // ==========================================
    // 4. Simulated Automated Responses
    // ==========================================
    function simulateOperatorResponse() {
        setTimeout(() => {
            const receivedBubble = document.createElement("div");
            receivedBubble.className = "message-bubble message-bubble--received";
            receivedBubble.innerHTML = `
        <div class="message-avatar"></div>
        <div class="message-content-wrapper">
          <div class="message-text">Acknowledged. The system has updated the request parameters for this task thread.</div>
        </div>
      `;
            messagesContainer.appendChild(receivedBubble);
            scrollToBottom();
        }, 1200); // 1.2 second response delay
    }

    // Optional Button Interactive Micro-feedback Triggers
    micButton.addEventListener("click", () => alert("Microphone capture session starting..."));
    attachButton.addEventListener("click", () => alert("File attachment upload prompt loading..."));
});
