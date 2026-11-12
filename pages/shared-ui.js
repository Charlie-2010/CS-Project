(() => {
  window.CogniPlanAPI = {
    async request(url, options = {}) {
      const response = await fetch(url, { credentials: "same-origin", headers: { "Content-Type": "application/json", ...(options.headers || {}) }, ...options });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.error || `Request failed (${response.status})`);
      return payload;
    },
    get(url) { return this.request(url); },
    post(url, data) { return this.request(url, { method: "POST", body: JSON.stringify(data) }); },
    put(url, data) { return this.request(url, { method: "PUT", body: JSON.stringify(data) }); },
    delete(url) { return this.request(url, { method: "DELETE" }); }
  };
  const toastRegion = document.createElement("div");
  toastRegion.className = "app-toast-region";
  toastRegion.setAttribute("aria-live", "polite");
  toastRegion.setAttribute("aria-atomic", "false");
  document.addEventListener("DOMContentLoaded", () => document.body.appendChild(toastRegion));

  window.AppUI = {
    toast(message, type = "info") {
      const toast = document.createElement("div");
      toast.className = `app-toast${type === "error" ? " app-toast--error" : type === "success" ? " app-toast--success" : ""}`;
      toast.setAttribute("role", type === "error" ? "alert" : "status");
      toast.textContent = message;
      toastRegion.appendChild(toast);
      window.setTimeout(() => toast.remove(), 4200);
    }
  };

  document.addEventListener("DOMContentLoaded", () => {
    const path = window.location.pathname;
    const isPublicPage = path.includes("/pages/landing-page/") || path.includes("/pages/auth/");
    if (!isPublicPage) {
      window.CogniPlanAPI.get("/api/auth/me").then(result => {
        if (!result.authenticated) window.location.replace("../auth/auth.html");
      }).catch(() => window.location.replace("../auth/auth.html"));
    }
    let themePreference = "dark";
    try {
      const preferences = JSON.parse(localStorage.getItem("cogniplan.preferences") || "{}");
      themePreference = preferences.theme || "dark";
      document.body.dataset.theme = themePreference === "system"
        ? (window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark")
        : themePreference;
      if (preferences.compactMode) document.body.classList.add("compact-mode");
      if (preferences.accent) document.documentElement.dataset.accent = preferences.accent;
      if (preferences.fontSize) document.body.dataset.fontSize = preferences.fontSize.toLowerCase();
    } catch (error) {
      console.error("Could not load saved preferences.", error);
      window.AppUI.toast("Saved preferences could not be loaded.", "error");
    }
    window.matchMedia("(prefers-color-scheme: light)").addEventListener?.("change", event => {
      if (themePreference === "system") document.body.dataset.theme = event.matches ? "light" : "dark";
    });
    try {
      const profile = JSON.parse(localStorage.getItem("cogniplan.profile") || "{}");
      if (typeof profile.username === "string" && profile.username.trim()) {
        document.querySelectorAll(".profile-pill__name, .user-name").forEach(name => {
          name.textContent = profile.username;
        });
      }
      if (typeof profile.email === "string" && profile.email.trim()) {
        document.querySelectorAll(".user-email").forEach(email => {
          email.textContent = profile.email;
        });
      }
    } catch (error) {
      console.error("Could not load profile details.", error);
      window.AppUI.toast("Saved profile details could not be loaded.", "error");
    }

    const sidebar = document.getElementById("sidebar");
    const toggle = document.getElementById("sidebar-toggle");
    if (sidebar && toggle) {
      toggle.setAttribute("role", "button");
      toggle.setAttribute("tabindex", "0");
      toggle.setAttribute("aria-label", "Toggle navigation");
      toggle.setAttribute("aria-expanded", String(sidebar.classList.contains("expanded")));
      const toggleMenu = () => {
        sidebar.classList.toggle("expanded");
        toggle.setAttribute("aria-expanded", String(sidebar.classList.contains("expanded")));
      };
      toggle.addEventListener("click", event => {
        event.stopPropagation();
        toggleMenu();
      });
      toggle.addEventListener("keydown", event => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          toggleMenu();
        }
      });
      document.addEventListener("click", event => {
        if (!sidebar.contains(event.target) && sidebar.classList.contains("expanded")) {
          sidebar.classList.remove("expanded");
          toggle.setAttribute("aria-expanded", "false");
        }
      });
      document.addEventListener("keydown", event => {
        if (event.key === "Escape" && sidebar.classList.contains("expanded")) {
          sidebar.classList.remove("expanded");
          toggle.setAttribute("aria-expanded", "false");
          toggle.focus();
        }
      });
    }

    document.querySelectorAll(".menu-cluster__link").forEach(link => {
      if (new URL(link.href, window.location.href).pathname === window.location.pathname) {
        link.classList.add("active");
        link.setAttribute("aria-current", "page");
      }
    });

    document.querySelectorAll(".action-trigger--bell, .notification-btn").forEach(button => {
      button.setAttribute("aria-label", "View notifications");
      button.addEventListener("click", () => window.AppUI.toast("You’re all caught up.", "info"));
    });

    const profileButton = document.getElementById("profile-pill");
    if (profileButton) {
      const menuHost = profileButton.parentElement;
      const accountMenu = document.createElement("div");
      accountMenu.className = "app-account-menu";
      accountMenu.setAttribute("role", "menu");
      accountMenu.hidden = true;

      const profileAction = document.createElement("button");
      profileAction.className = "app-account-menu__item";
      profileAction.type = "button";
      profileAction.setAttribute("role", "menuitem");
      profileAction.textContent = "View profile";
      profileAction.addEventListener("click", () => {
        window.location.href = "../profile/profile.html";
      });

      const logoutAction = document.createElement("button");
      logoutAction.className = "app-account-menu__item app-account-menu__item--logout";
      logoutAction.type = "button";
      logoutAction.setAttribute("role", "menuitem");
      logoutAction.textContent = "Log out";
      logoutAction.addEventListener("click", async () => {
        try { await window.CogniPlanAPI.post("/api/auth/logout", {}); }
        catch (error) { console.error("Logout failed", error); }
        window.location.href = "../auth/auth.html";
      });

      accountMenu.append(profileAction, logoutAction);
      menuHost.appendChild(accountMenu);
      menuHost.classList.add("app-account-menu-host");
      profileButton.setAttribute("aria-haspopup", "menu");
      profileButton.setAttribute("aria-expanded", "false");

      const closeMenu = () => {
        accountMenu.hidden = true;
        profileButton.setAttribute("aria-expanded", "false");
      };
      profileButton.addEventListener("click", event => {
        event.stopPropagation();
        const isOpen = !accountMenu.hidden;
        accountMenu.hidden = isOpen;
        profileButton.setAttribute("aria-expanded", String(!isOpen));
      });
      document.addEventListener("click", event => {
        if (!menuHost.contains(event.target)) closeMenu();
      });
      document.addEventListener("keydown", event => {
        if (event.key === "Escape" && !accountMenu.hidden) {
          closeMenu();
          profileButton.focus();
        }
      });
    }
  });
})();
