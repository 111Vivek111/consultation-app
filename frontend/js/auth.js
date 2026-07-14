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

async function login() {

    const email =
        document.getElementById("email").value;

    const password =
        document.getElementById("password").value;

    if (!email || !password) {

        alert("Please fill all fields.");

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

        alert(data.detail);

        return;
    }

    saveToken(
        data.access_token
    );

    window.location.href =
        "index.html";
}