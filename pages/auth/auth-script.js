const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

function toggleAuthView(targetCardId) {
    document.querySelectorAll(".auth-card").forEach(card => card.classList.toggle("hidden", card.id !== targetCardId));
    document.getElementById(targetCardId)?.querySelector("input")?.focus();
}
function showFormMessage(form, message, isError = false) {
    const feedback = form.querySelector(".form-feedback");
    if (!feedback) return;
    feedback.textContent = message;
    feedback.classList.toggle("form-feedback--error", isError);
    feedback.classList.toggle("form-feedback--success", !isError);
}
function setFormBusy(form, busy, label) {
    const button = form.querySelector('button[type="submit"]');
    if (!button) return;
    if (!button.dataset.defaultLabel) button.dataset.defaultLabel = button.textContent.trim();
    button.disabled = busy; button.setAttribute("aria-busy", String(busy));
    button.textContent = busy ? label : button.dataset.defaultLabel;
}
async function executeSignIn(event) {
    event.preventDefault(); const form=event.currentTarget;
    const identity=document.getElementById("login-user"); const password=document.getElementById("login-pass");
    if (!identity.value.trim() || !password.value) return showFormMessage(form,"Enter your username/email and password.",true);
    setFormBusy(form,true,"Signing in…");
    try {
        await window.CogniPlanAPI.post("/api/auth/login",{identity:identity.value.trim(),password:password.value});
        showFormMessage(form,"Signed in. Opening your workspace…");
        window.location.href="../dashboard/dashboard.html";
    } catch(error) { showFormMessage(form,error.message,true); setFormBusy(form,false); }
}
async function executeSignUp(event) {
    event.preventDefault(); const form=event.currentTarget;
    const name=document.getElementById("reg-name"); const email=document.getElementById("reg-user");
    const password=document.getElementById("reg-pass"); const confirmation=document.getElementById("reg-confirm");
    if (!name.value.trim()) return showFormMessage(form,"Enter your name.",true);
    if (!emailPattern.test(email.value.trim())) return showFormMessage(form,"Enter a valid email address.",true);
    if (password.value.length<8) return showFormMessage(form,"Use a password with at least 8 characters.",true);
    if (password.value!==confirmation.value) return showFormMessage(form,"Passwords do not match.",true);
    setFormBusy(form,true,"Creating account…");
    try {
        await window.CogniPlanAPI.post("/api/auth/register",{username:name.value.trim(),email:email.value.trim(),password:password.value});
        showFormMessage(form,"Account created. Opening your workspace…");
        window.location.href="../dashboard/dashboard.html";
    } catch(error) { showFormMessage(form,error.message,true); setFormBusy(form,false); }
}
function executeReset(event) {
    event.preventDefault(); const form=event.currentTarget;
    const email=document.getElementById("reset-mail");
    if (!emailPattern.test(email.value.trim())) return showFormMessage(form,"Enter a valid email address.",true);
    showFormMessage(form,"Password recovery has not been configured yet. Contact your administrator.",true);
}
document.addEventListener("DOMContentLoaded",()=>{
    document.querySelectorAll(".auth-form").forEach(form=>form.addEventListener("input",event=>{
        form.querySelector(".form-feedback").textContent=""; event.target.removeAttribute("aria-invalid");
    }));
});
