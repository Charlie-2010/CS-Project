document.addEventListener("DOMContentLoaded", () => {
  const contacts = [...document.querySelectorAll(".contact-item")];
  const messagesContainer = document.querySelector(".chat-messages-container");
  const input = document.querySelector(".chat-input-field");
  const sendButton = document.querySelector(".btn-send");
  const search = document.querySelector(".search-bar__input");
  const headerName = document.querySelector(".chat-header-name");
  const initialData = [
    [{ text: "Hello, let me know if you are available today.", sent: false, time: "09:15" }, { text: "I can review the sprint plan this afternoon.", sent: true, time: "09:22" }],
    [{ text: "Please check the document I sent you earlier.", sent: false, time: "10:05" }],
    [{ text: "We need to schedule a meeting for tomorrow.", sent: false, time: "10:55" }],
    []
  ];
  const threads = new Map();
  contacts.forEach((contact, index) => {
    const key = `contact-${index}`;
    contact.dataset.contact = key;
    threads.set(key, initialData[index] || []);
    contact.setAttribute("role", "button");
    contact.setAttribute("tabindex", "0");
    contact.setAttribute("aria-label", `Open conversation with ${contact.querySelector(".contact-name").textContent.trim()}`);
  });
  let activeContact = contacts.find(contact => contact.classList.contains("active")) || contacts[0];

  function timeNow() {
    return new Date().toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
  }

  function renderThread() {
    if (!activeContact) return;
    const name = activeContact.querySelector(".contact-name").textContent.trim();
    headerName.textContent = `${name} - Operator`;
    const thread = threads.get(activeContact.dataset.contact) || [];
    messagesContainer.replaceChildren();
    if (!thread.length) {
      const empty = document.createElement("p");
      empty.className = "chat-empty-state";
      empty.textContent = `No messages with ${name} yet. Start the conversation below.`;
      messagesContainer.appendChild(empty);
      return;
    }

    thread.forEach(message => {
      const bubble = document.createElement("div");
      bubble.className = `message-bubble message-bubble--${message.sent ? "sent" : "received"}`;
      if (!message.sent) {
        const avatar = document.createElement("div");
        avatar.className = "message-avatar";
        bubble.appendChild(avatar);
      }
      const wrapper = document.createElement("div");
      wrapper.className = "message-content-wrapper";
      const text = document.createElement("div");
      text.className = "message-text";
      text.textContent = message.text;
      const timestamp = document.createElement("time");
      timestamp.className = "message-timestamp";
      timestamp.textContent = message.time;
      wrapper.append(text, timestamp);
      bubble.appendChild(wrapper);
      messagesContainer.appendChild(bubble);
    });
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  function updateContactPreview(contact, message) {
    if (!contact) return;
    const preview = contact.querySelector(".contact-preview, .contact-preview-active");
    if (preview) preview.textContent = message;
    const time = contact.querySelector(".contact-time, .contact-time-active");
    if (time) time.textContent = timeNow();
  }

  function selectContact(contact) {
    activeContact = contact;
    contacts.forEach(item => {
      item.classList.toggle("active", item === contact);
      item.setAttribute("aria-pressed", String(item === contact));
    });
    renderThread();
  }

  contacts.forEach(contact => {
    contact.addEventListener("click", () => selectContact(contact));
    contact.addEventListener("keydown", event => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        selectContact(contact);
      }
    });
  });

  function sendMessage() {
    const text = input.value.trim();
    if (!text || !activeContact) {
      if (!text) input.focus();
      return;
    }
    const key = activeContact.dataset.contact;
    const thread = threads.get(key);
    const message = { text, sent: true, time: timeNow() };
    thread.push(message);
    updateContactPreview(activeContact, text);
    input.value = "";
    renderThread();
    window.setTimeout(() => {
      const response = { text: "Thanks for the update. I’ll take a look and follow up here.", sent: false, time: timeNow() };
      thread.push(response);
      if (activeContact?.dataset.contact === key) renderThread();
      const contact = contacts.find(item => item.dataset.contact === key);
      updateContactPreview(contact, response.text);
    }, 850);
  }

  input.addEventListener("keydown", event => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  });
  sendButton.addEventListener("click", sendMessage);
  search.addEventListener("input", () => {
    const query = search.value.trim().toLocaleLowerCase();
    contacts.forEach(contact => {
      const name = contact.querySelector(".contact-name").textContent.toLocaleLowerCase();
      const preview = contact.querySelector(".contact-preview, .contact-preview-active")?.textContent.toLocaleLowerCase() || "";
      contact.hidden = !name.includes(query) && !preview.includes(query);
    });
    const noMatches = contacts.every(contact => contact.hidden);
    let empty = document.querySelector(".contacts-empty-state");
    if (noMatches && !empty) {
      empty = document.createElement("p");
      empty.className = "contacts-empty-state";
      empty.textContent = "No conversations match your search.";
      document.querySelector(".contacts-container").appendChild(empty);
    } else if (!noMatches) {
      empty?.remove();
    }
  });

  document.querySelector(".btn-mic").addEventListener("click", () => {
    window.AppUI.toast("Voice messages are not available in this demo.", "info");
  });
  document.querySelector(".btn-attach").addEventListener("click", () => {
    const picker = document.createElement("input");
    picker.type = "file";
    picker.addEventListener("change", () => {
      if (picker.files?.[0]) window.AppUI.toast(`${picker.files[0].name} selected. Upload is not connected.`, "info");
    });
    picker.click();
  });

  selectContact(activeContact);
});
