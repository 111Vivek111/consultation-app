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

async function createConversation() {

    const response =
        await apiRequest(
            "/conversation",
            "POST"
        );

    return await response.json();
}

async function getConversations() {

    const response =
        await apiRequest(
            "/conversations"
        );

    return await response.json();
}

async function getConversation(
    conversationId
) {

    const response =
        await apiRequest(
            `/conversation/${conversationId}`
        );

    return await response.json();
}

async function deleteConversation(
    conversationId
){

    const response =
        await apiRequest(
            `/conversation/${conversationId}`,
            "DELETE"
        );

    return await response.json();
}