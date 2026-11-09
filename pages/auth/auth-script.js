const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

function toggleAuthView(targetCardId) {
    document.querySelectorAll(".auth-card").forEach(card => {
        card.classList.toggle("hidden", card.id !== targetCardId);
    });
    const target = document.getElementById(targetCardId);
    target?.querySelector("input")?.focus();
}

function showFormMessage(form, message, isError = false) {
    const feedback = form.querySelector(".form-feedback");
    feedback.textContent = message;
    feedback.classList.toggle("form-feedback--error", isError);
    feedback.classList.toggle("form-feedback--success", !isError);
}

function setFormBusy(form, busy, label) {
    const button = form.querySelector('button[type="submit"]');
    if (!button.dataset.defaultLabel) button.dataset.defaultLabel = button.textContent.trim();
    button.disabled = busy;
    button.setAttribute("aria-busy", String(busy));
    button.textContent = busy ? label : button.dataset.defaultLabel;
}

function executeSignIn(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const username = document.getElementById("login-user");
    const password = document.getElementById("login-pass");
    if (!username.value.trim()) {
        username.setAttribute("aria-invalid", "true");
        username.focus();
        return showFormMessage(form, "Enter your username or email address.", true);
    }
    if (!password.value) {
        password.setAttribute("aria-invalid", "true");
        password.focus();
        return showFormMessage(form, "Enter your password.", true);
    }

    showFormMessage(form, "Demo sign-in validated. Opening your workspace…");
    setFormBusy(form, true, "Opening workspace…");
    window.setTimeout(() => {
        window.location.href = "../dashboard/dashboard.html";
    }, 350);
}

function executeSignUp(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const name = document.getElementById("reg-name");
    const email = document.getElementById("reg-user");
    const password = document.getElementById("reg-pass");
    const confirmation = document.getElementById("reg-confirm");

    if (!name.value.trim()) {
        name.setAttribute("aria-invalid", "true");
        name.focus();
        return showFormMessage(form, "Enter your name.", true);
    }
    if (!emailPattern.test(email.value.trim())) {
        email.setAttribute("aria-invalid", "true");
        email.focus();
        return showFormMessage(form, "Enter a valid email address.", true);
    }
    if (password.value.length < 8) {
        password.setAttribute("aria-invalid", "true");
        password.focus();
        return showFormMessage(form, "Use a password with at least 8 characters.", true);
    }
    if (password.value !== confirmation.value) {
        confirmation.setAttribute("aria-invalid", "true");
        confirmation.focus();
        return showFormMessage(form, "Passwords do not match.", true);
    }

    showFormMessage(form, "This frontend demo does not create accounts. You can continue to sign in.");
    setFormBusy(form, true, "Checking…");
    window.setTimeout(() => {
        document.getElementById("login-user").value = email.value.trim();
        setFormBusy(form, false);
        toggleAuthView("card-signin");
    }, 700);
}

function executeReset(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const email = document.getElementById("reset-mail");
    if (!emailPattern.test(email.value.trim())) {
        email.setAttribute("aria-invalid", "true");
        email.focus();
        return showFormMessage(form, "Enter a valid email address.", true);
    }
    showFormMessage(form, "Password recovery is not connected in this demo.", true);
}

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".auth-form").forEach(form => {
        form.addEventListener("input", event => {
            form.querySelector(".form-feedback").textContent = "";
            event.target.removeAttribute("aria-invalid");
        });
    });
});
