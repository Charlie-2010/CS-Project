document.addEventListener("DOMContentLoaded", () => {
  const list = document.querySelector(".contacts-container");
  const messagesContainer = document.querySelector(".chat-messages-container");
  const input = document.querySelector(".chat-input-field");
  const sendButton = document.querySelector(".btn-send");
  const search = document.querySelector(".search-bar__input");
  const headerName = document.querySelector(".chat-header-name");
  const newChatButton = document.querySelector(".new-chat-btn");
  let conversations = [];
  let active = null;
  let searchResults = false;

  const timeLabel = value => value ? new Date(String(value).replace(" ", "T")).toLocaleTimeString([], {hour:"numeric",minute:"2-digit"}) : "";
  function renderMessages(messages) {
    messagesContainer.replaceChildren();
    if (!messages.length) {
      const empty = document.createElement("p"); empty.className="chat-empty-state";
      empty.textContent="No messages yet. Start the conversation below."; messagesContainer.appendChild(empty); return;
    }
    messages.forEach(message => {
      const bubble=document.createElement("div");
      bubble.className=`message-bubble message-bubble--${Number(message.sender_id) === Number(window.CogniPlanUserId) ? "sent" : "received"}`;
      if (bubble.classList.contains("message-bubble--received")) { const avatar=document.createElement("div"); avatar.className="message-avatar"; bubble.appendChild(avatar); }
      const wrap=document.createElement("div"); wrap.className="message-content-wrapper";
      const text=document.createElement("div"); text.className="message-text"; text.textContent=message.message_text;
      const time=document.createElement("time"); time.className="message-timestamp"; time.textContent=timeLabel(message.sent_at);
      wrap.append(text,time); bubble.appendChild(wrap); messagesContainer.appendChild(bubble);
    });
    messagesContainer.scrollTop=messagesContainer.scrollHeight;
  }

  async function openConversation(conversation) {
    active=conversation; headerName.textContent=conversation.other_username;
    [...list.querySelectorAll(".contact-item")].forEach(item=>item.classList.toggle("active",Number(item.dataset.conversationId)===Number(conversation.conversation_id)));
    try {
      const result=await window.CogniPlanAPI.get(`/api/conversations/${conversation.conversation_id}/messages`);
      renderMessages(result.messages || []);
    } catch(error) { renderMessages([]); window.AppUI.toast(error.message,"error"); }
  }

  function renderConversations() {
    list.replaceChildren();
    if (!conversations.length) {
      const empty=document.createElement("p"); empty.className="contacts-empty-state";
      empty.textContent="No conversations yet. Use New Chat to find another user."; list.appendChild(empty); return;
    }
    conversations.forEach(conversation=>{
      const item=document.createElement("button"); item.type="button"; item.className="contact-item";
      item.dataset.conversationId=conversation.conversation_id;
      const avatar=document.createElement("span"); avatar.className="avatar";
      const info=document.createElement("span"); info.className="contact-info";
      const heading=document.createElement("span"); heading.className="contact-header";
      const name=document.createElement("span"); name.className="contact-name"; name.textContent=conversation.other_username;
      const preview=document.createElement("span"); preview.className="contact-preview"; preview.textContent="Open conversation";
      heading.append(name); info.append(heading,preview); item.append(avatar,info);
      item.addEventListener("click",()=>openConversation(conversation)); list.appendChild(item);
    });
    if (!active && conversations.length) openConversation(conversations[0]);
  }

  async function refreshConversations() {
    const result=await window.CogniPlanAPI.get("/api/conversations");
    conversations=result.conversations || []; renderConversations();
  }

  async function searchUsers(term) {
    if (term.length<2) { searchResults=false; renderConversations(); return; }
    const result=await window.CogniPlanAPI.get(`/api/users/search?q=${encodeURIComponent(term)}`);
    searchResults=true; list.replaceChildren();
    (result.users || []).forEach(user=>{
      const item=document.createElement("button"); item.type="button"; item.className="contact-item";
      const avatar=document.createElement("span"); avatar.className="avatar";
      const info=document.createElement("span"); info.className="contact-info";
      const name=document.createElement("span"); name.className="contact-name"; name.textContent=user.username;
      const email=document.createElement("span"); email.className="contact-preview"; email.textContent=user.email;
      info.append(name,email); item.append(avatar,info);
      item.addEventListener("click",async()=>{
        try {
          const created=await window.CogniPlanAPI.post("/api/conversations",{user_id:user.user_id});
          await refreshConversations();
          const found=conversations.find(c=>Number(c.conversation_id)===Number(created.conversation_id));
          if(found) await openConversation(found);
          search.value=""; searchResults=false;
        } catch(error) { window.AppUI.toast(error.message,"error"); }
      });
      list.appendChild(item);
    });
    if (!(result.users || []).length) { const empty=document.createElement("p"); empty.className="contacts-empty-state"; empty.textContent="No matching users found."; list.appendChild(empty); }
  }

  async function sendMessage() {
    const message_text=input.value.trim(); if(!message_text)return input.focus();
    if(!active) return window.AppUI.toast("Open a conversation or start a new chat first.","info");
    sendButton.disabled=true;
    try {
      await window.CogniPlanAPI.post(`/api/conversations/${active.conversation_id}/messages`,{message_text});
      input.value="";
      const result=await window.CogniPlanAPI.get(`/api/conversations/${active.conversation_id}/messages`);
      renderMessages(result.messages || []);
    } catch(error) { window.AppUI.toast(error.message,"error"); }
    finally { sendButton.disabled=false; input.focus(); }
  }

  search.addEventListener("input",()=>{
    const term=search.value.trim();
    if(term.length>=2) searchUsers(term).catch(error=>window.AppUI.toast(error.message,"error"));
    else if(searchResults) { searchResults=false; renderConversations(); }
    else [...list.querySelectorAll(".contact-item")].forEach(item=>item.hidden=!item.textContent.toLowerCase().includes(term.toLowerCase()));
  });
  newChatButton.addEventListener("click",()=>{search.focus();search.placeholder="Search users by name or email...";window.AppUI.toast("Search for a registered CogniPlan user to start a chat.","info");});
  sendButton.addEventListener("click",sendMessage);
  input.addEventListener("keydown",event=>{if(event.key==="Enter"&&!event.shiftKey){event.preventDefault();sendMessage();}});
  document.querySelector(".btn-mic")?.addEventListener("click",()=>window.AppUI.toast("Voice messages are not supported yet.","info"));
  document.querySelector(".btn-attach")?.addEventListener("click",()=>window.AppUI.toast("File attachments are not supported yet.","info"));

  window.CogniPlanAPI.get("/api/auth/me").then(result=>{window.CogniPlanUserId=result.user?.user_id;return refreshConversations();})
    .catch(error=>window.AppUI.toast("Could not load conversations: "+error.message,"error"));
});
