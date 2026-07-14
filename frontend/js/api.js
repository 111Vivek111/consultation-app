const API_BASE = "http://127.0.0.1:8000";

async function apiRequest(endpoint, method = "GET", body = null) {

    const token = localStorage.getItem("token");

    const headers = {
        "Content-Type": "application/json"
    };

    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(
        `${API_BASE}${endpoint}`,
        {
            method,
            headers,
            body: body ? JSON.stringify(body) : null
        }
    );

    return response;
}