document.addEventListener("DOMContentLoaded", () => {
  // --- DOM Query Core Component Selectors ---
  const filterOptions = document.querySelectorAll(".filter-opt");
  const milestonesPct = document.getElementById("milestones-pct");
  const milestonesBar = document.getElementById("milestones-bar");
  const semesterAvgVal = document.getElementById("semester-avg-val");
  
  const usernameInput = document.getElementById("username-field");
  const emailInput = document.getElementById("email-field");
  const timezoneSelect = document.getElementById("timezone-select");
  const btnSaveProfile = document.getElementById("btn-save-profile");

  // ==========================================
  // 1. Data Store Matrices for Time Series Profiles
  // ==========================================
  const academicDatasets = {
    "weekly": { milestones: "72%", avg: "88%" },
    "monthly": { milestones: "65%", avg: "84%" },
    "overall": { milestones: "89%", avg: "91%" }
  };

  // ==========================================
  // 2. Filter Interactive Metrics Engine
  // ==========================================
  filterOptions.forEach(opt => {
    opt.addEventListener("click", () => {
      // Toggle layout visual classes cleanly
      filterOptions.forEach(el => el.classList.remove("active"));
      opt.classList.add("active");

      // Extract parameter state tokens
      const selectedFilter = opt.getAttribute("data-filter");
      const dataset = academicDatasets[selectedFilter];

      if (dataset) {
        // Apply smooth timeline state modifications
        milestonesPct.textContent = dataset.milestones;
        milestonesBar.style.width = dataset.milestones;
        semesterAvgVal.textContent = dataset.avg;
      }
    });
  });

  // ==========================================
  // 3. Email Formatting Input Validation Regex
  // ==========================================
  function validateEmail(email) {
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return emailRegex.test(String(email).toLowerCase());
  }

  // Live input change error color tracking indicators
  emailInput.addEventListener("input", () => {
    const value = emailInput.value.trim();
    if (value === "" || validateEmail(value)) {
      emailInput.style.borderColor = "";
      emailInput.style.boxShadow = "";
    } else {
      emailInput.style.borderColor = "#ef4444";
      emailInput.style.boxShadow = "0 0 8px rgba(239, 68, 68, 0.2)";
    }
  });

  // ==========================================
  // 4. Form Action Submission Handler
  // ==========================================
  btnSaveProfile.addEventListener("click", () => {
    const userVal = usernameInput.value.trim();
    const emailVal = emailInput.value.trim();
    const tzVal = timezoneSelect.value;

    // A. Handle validation failures
    if (!userVal) {
      alert("Validation Error: Username parameter cannot remain empty.");
      usernameInput.focus();
      return;
    }

    if (!validateEmail(emailVal)) {
      alert("Validation Error: Please provide a compliant, well-formed email mapping address.");
      emailInput.focus();
      return;
    }

    // B. Simulate save event configuration lifecycle
    btnSaveProfile.textContent = "Saving Configuration...";
    btnSaveProfile.disabled = true;

    setTimeout(() => {
      // Print target parameter configurations data matrix payload to local debugging environment
      console.log("Ecosystem profile metrics synchronized successfully:", {
        username: userVal,
        email: emailVal,
        timezone: tzVal,
        timestamp: new Date().toISOString()
      });

      alert("Success: Full-stack configuration ecosystem parameters updated successfully.");
      
      btnSaveProfile.textContent = "Update Profile";
      btnSaveProfile.disabled = false;
    }, 1000);
  });
});
