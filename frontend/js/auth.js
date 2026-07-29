function saveToken(token) {

    localStorage.setItem(
        "token",
        token
    );
}

function getToken() {

    return localStorage.getItem(
        "token"
    );
}

function logout() {

    localStorage.removeItem(
        "token"
    );

    window.location.href =
        "login.html";
}

function requireLogin() {

    if (!getToken()) {

        window.location.href =
            "login.html";
    }
}

function showAuthError(message) {

    const el = document.getElementById("auth-error");

    if (el) {
        el.textContent = message;
        el.hidden = false;
    } else {
        alert(message);
    }
}

function clearAuthError() {

    const el = document.getElementById("auth-error");

    if (el) {
        el.hidden = true;
        el.textContent = "";
    }
}

async function login() {

    clearAuthError();

    const email =
        document.getElementById("email").value;

    const password =
        document.getElementById("password").value;

    if (!email || !password) {

        showAuthError("Please fill all fields.");

        return;
    }

    const response =
        await apiRequest(
            "/login",
            "POST",
            {
                email,
                password
            }
        );

    const data =
        await response.json();

    if (!response.ok) {

        showAuthError(data.detail || "Login failed. Please try again.");

        return;
    }

    saveToken(
        data.access_token
    );

    window.location.href =
        "index.html";
}

async function register() {

    clearAuthError();

    const full_name =
        document.getElementById("full_name").value;

    const email =
        document.getElementById("email").value;

    const password =
        document.getElementById("password").value;

    if (
        !full_name ||
        !email ||
        !password
    ) {

        showAuthError(
            "Please fill all fields."
        );

        return;
    }

    const response =
        await apiRequest(
            "/signup",
            "POST",
            {
                full_name,
                email,
                password
            }
        );

    const data =
        await response.json();

    if (!response.ok) {

        showAuthError(
            data.detail || "Registration failed. Please try again."
        );

        return;
    }

    saveToken(
        data.access_token
    );

    window.location.href =
        "index.html";
}