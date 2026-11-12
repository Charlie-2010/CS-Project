document.addEventListener("DOMContentLoaded", () => {
  const storageKey = "cogniplan.preferences";
  const themeButtons = [...document.querySelectorAll(".segment-btn")];
  const colorButtons = [...document.querySelectorAll(".color-dot")];
  const statusText = document.getElementById("status-text");
  const statusDot = document.querySelector(".status-dot");
  const controls = [...document.querySelectorAll(".dropdown-control, .switch input")];
  const defaults = {
    theme: "dark",
    accent: "cyan",
    language: "English",
    fontSize: "Medium",
    taskReminders: true,
    weeklySummary: true,
    achievementAlerts: false,
    compactMode: false,
    requirePassword: false,
    biometricLogin: true
  };
  let preferences = { ...defaults };
  let savedSnapshot = "";

  function collectPreferences() {
    return {
      theme: document.querySelector(".segment-btn.active")?.dataset.theme || "dark",
      accent: document.querySelector(".color-dot.active")?.dataset.color || "cyan",
      language: document.getElementById("language-preference").value,
      fontSize: document.getElementById("font-size-preference").value,
      taskReminders: document.getElementById("task-reminders").checked,
      weeklySummary: document.getElementById("weekly-summary").checked,
      achievementAlerts: document.getElementById("achievement-alerts").checked,
      compactMode: document.getElementById("compact-mode").checked,
      requirePassword: document.getElementById("require-password").checked,
      biometricLogin: document.getElementById("biometric-login").checked
    };
  }

  function renderPreferences(values) {
    themeButtons.forEach(button => button.classList.toggle("active", button.dataset.theme === values.theme));
    colorButtons.forEach(button => button.classList.toggle("active", button.dataset.color === values.accent));
    document.getElementById("language-preference").value = values.language;
    document.getElementById("font-size-preference").value = values.fontSize;
    document.getElementById("task-reminders").checked = values.taskReminders;
    document.getElementById("weekly-summary").checked = values.weeklySummary;
    document.getElementById("achievement-alerts").checked = values.achievementAlerts;
    document.getElementById("compact-mode").checked = values.compactMode;
    document.getElementById("require-password").checked = values.requirePassword;
    document.getElementById("biometric-login").checked = values.biometricLogin;
    applyPreferences(values);
  }

  function applyPreferences(values) {
    const theme = values.theme === "system"
      ? (window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark")
      : values.theme;
    document.body.dataset.theme = theme;
    document.body.classList.toggle("compact-mode", values.compactMode);
    document.body.dataset.fontSize = values.fontSize.toLowerCase();
    document.documentElement.dataset.accent = values.accent;
    const colors = { cyan: "#00bcd4", purple: "#9c27b0", pink: "#ec4899", orange: "#f97316", green: "#10b981" };
    document.documentElement.style.setProperty("--app-accent", colors[values.accent] || colors.cyan);
  }

  function setStatus(message, kind = "saved") {
    statusText.textContent = message;
    statusDot.style.backgroundColor = kind === "error" ? "#ef4444" : kind === "dirty" ? "#f59e0b" : "#10b981";
    statusDot.style.boxShadow = `0 0 8px ${kind === "error" ? "#ef4444" : kind === "dirty" ? "#f59e0b" : "#10b981"}`;
  }

  function markDirty() {
    const unchanged = JSON.stringify(collectPreferences()) === savedSnapshot;
    setStatus(unchanged ? "All changes saved" : "Unsaved changes", unchanged ? "saved" : "dirty");
  }

  async function savePreferences() {
    preferences = collectPreferences();
    try {
      await window.CogniPlanAPI.put("/api/preferences", {
        theme_mode: preferences.theme, daily_task_goal: 0, widget_layout: preferences
      });
      localStorage.setItem(storageKey, JSON.stringify(preferences));
      savedSnapshot = JSON.stringify(preferences); applyPreferences(preferences);
      setStatus("All changes saved"); window.AppUI.toast("Preferences saved to your account.", "success");
    } catch (error) {
      console.error("Could not save preferences.", error); setStatus("Could not save preferences", "error");
      window.AppUI.toast("Preferences could not be saved: " + error.message, "error");
    }
  }

  try {
    const stored = localStorage.getItem(storageKey);
    if (stored) {
      const parsed = JSON.parse(stored);
      preferences = { ...defaults, ...parsed };
    }
  } catch (error) {
    console.error("Could not read saved preferences.", error);
    setStatus("Saved preferences could not be loaded", "error");
    window.AppUI.toast("Saved preferences could not be loaded.", "error");
  }
  renderPreferences(preferences);
  savedSnapshot = JSON.stringify(collectPreferences());
  window.CogniPlanAPI.get("/api/preferences").then(result => {
    const remote = result.preferences?.widget_layout;
    if (remote && typeof remote === "object") {
      preferences = { ...defaults, ...remote }; renderPreferences(preferences);
      savedSnapshot = JSON.stringify(collectPreferences());
    }
  }).catch(error => console.warn("Preferences could not be loaded from server:", error.message));

  themeButtons.forEach(button => button.addEventListener("click", () => {
    themeButtons.forEach(item => item.classList.toggle("active", item === button));
    applyPreferences(collectPreferences());
    markDirty();
  }));
  colorButtons.forEach(button => button.addEventListener("click", () => {
    colorButtons.forEach(item => item.classList.toggle("active", item === button));
    applyPreferences(collectPreferences());
    markDirty();
  }));
  controls.forEach(control => control.addEventListener("change", () => {
    applyPreferences(collectPreferences());
    markDirty();
  }));
  document.getElementById("save-btn").addEventListener("click", savePreferences);
  document.getElementById("reset-btn").addEventListener("click", () => {
    preferences = { ...defaults };
    renderPreferences(preferences);
    savePreferences();
  });
  window.addEventListener("beforeunload", event => {
    if (JSON.stringify(collectPreferences()) !== savedSnapshot) {
      event.preventDefault();
      event.returnValue = "";
    }
  });

  const systemTheme = window.matchMedia("(prefers-color-scheme: light)");
  systemTheme.addEventListener?.("change", () => {
    if (collectPreferences().theme === "system") applyPreferences(collectPreferences());
  });
});
