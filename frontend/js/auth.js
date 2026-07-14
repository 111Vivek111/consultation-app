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