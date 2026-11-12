document.addEventListener("DOMContentLoaded", () => {
  const username = document.getElementById("username-field");
  const email = document.getElementById("email-field");
  const timezone = document.getElementById("timezone-select");
  const editButton = document.getElementById("btn-edit-profile");
  const cancelButton = document.getElementById("btn-cancel-profile");
  const saveButton = document.getElementById("btn-save-profile");
  const errorMessage = document.getElementById("profile-form-error");
  const inputs = [username, email, timezone];
  const storageKey = "cogniplan.profile";
  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
  const metricData = {
    weekly: { milestones: 72, average: 88 },
    monthly: { milestones: 65, average: 84 },
    overall: { milestones: 89, average: 91 }
  };
  let savedValues = {};

  function getValues() {
    return { username: username.value.trim(), email: email.value.trim(), timezone: timezone.value };
  }

  function setEditMode(enabled) {
    inputs.forEach(input => { input.disabled = !enabled; });
    editButton.hidden = enabled;
    cancelButton.hidden = !enabled;
    saveButton.hidden = !enabled;
    (enabled ? username : editButton).focus();
  }

  function renderSavedValues(values) {
    username.value = values.username;
    email.value = values.email;
    timezone.value = values.timezone;
    inputs.forEach(input => input.removeAttribute("aria-invalid"));
    const timezoneLabel = timezone.options[timezone.selectedIndex]?.textContent || "Choose a time zone";
    document.querySelectorAll(".metadata-block .meta-val").forEach((value, index) => {
      value.textContent = [values.username, values.email, timezoneLabel][index] || "";
    });
    document.querySelector(".avatar-initials").textContent = values.username.slice(0, 2).toUpperCase();
  }

  try {
    const stored = localStorage.getItem(storageKey);
    if (stored) {
      const values = JSON.parse(stored);
      if (values.username && values.email && values.timezone) renderSavedValues(values);
    }
  } catch (error) {
    console.error("Could not load profile.", error);
    window.AppUI.toast("Saved profile details could not be loaded.", "error");
  }
  savedValues = getValues();
  window.CogniPlanAPI.get("/api/profile").then(result => {
    const remote = result.profile || {};
    const values = { username: remote.username || username.value, email: remote.email || email.value, timezone: timezone.value };
    renderSavedValues(values); savedValues = getValues();
  }).catch(error => console.warn("Profile could not be loaded from server:", error.message));

  editButton.addEventListener("click", () => {
    savedValues = getValues();
    errorMessage.textContent = "";
    setEditMode(true);
  });
  cancelButton.addEventListener("click", () => {
    renderSavedValues(savedValues);
    errorMessage.textContent = "";
    setEditMode(false);
  });
  inputs.forEach(input => input.addEventListener("input", () => {
    errorMessage.textContent = "";
    input.removeAttribute("aria-invalid");
  }));
  saveButton.addEventListener("click", async () => {
    const values = getValues();
    if (!values.username) {
      errorMessage.textContent = "Enter a username.";
      username.setAttribute("aria-invalid", "true");
      username.focus();
      return;
    }
    if (!emailPattern.test(values.email)) {
      errorMessage.textContent = "Enter a valid email address.";
      email.setAttribute("aria-invalid", "true");
      email.focus();
      return;
    }

    saveButton.disabled = true;
    saveButton.textContent = "Saving…";
    try {
      await window.CogniPlanAPI.put("/api/profile", { username: values.username, email: values.email });
      localStorage.setItem(storageKey, JSON.stringify(values));
      savedValues = values; renderSavedValues(values); setEditMode(false);
      window.AppUI.toast("Profile saved to your account.", "success");
    } catch (error) {
      console.error("Could not save profile.", error);
      errorMessage.textContent = error.message || "Profile could not be saved.";
      window.AppUI.toast("Profile could not be saved.", "error");
    } finally {
      saveButton.disabled = false;
      saveButton.textContent = "Save Changes";
    }
  });

  document.querySelectorAll(".filter-opt").forEach(button => {
    button.setAttribute("aria-pressed", String(button.classList.contains("active")));
    button.addEventListener("click", () => {
      document.querySelectorAll(".filter-opt").forEach(item => {
        item.classList.toggle("active", item === button);
        item.setAttribute("aria-pressed", String(item === button));
      });
      const values = metricData[button.dataset.filter];
      document.getElementById("milestones-pct").textContent = `${values.milestones}%`;
      document.getElementById("milestones-bar").style.width = `${values.milestones}%`;
      document.getElementById("semester-avg-val").textContent = `${values.average}%`;
    });
  });
});
