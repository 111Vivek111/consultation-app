// ===================== Theme =====================

(function initTheme() {
    const saved = localStorage.getItem("theme");
    if (saved) {
        document.documentElement.setAttribute("data-theme", saved);
    }
})();

document.getElementById("theme-toggle").addEventListener("click", () => {
    const current = document.documentElement.getAttribute("data-theme") || "dark";
    const next = current === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("theme", next);
});

// ===================== Account (best-effort display only) =====================

(function showAccountEmail() {
    const token = localStorage.getItem("token");
    const emailEl = document.getElementById("account-email");
    if (!token) return;

    try {
        const payload = JSON.parse(atob(token.split(".")[1]));
        if (payload.email) {
            emailEl.textContent = payload.email;
        }
    } catch (e) {
        // leave default "Signed in" label if token can't be decoded
    }
})();

// ===================== Welcome screen helper =====================

function setWelcomeVisible(visible) {
    const chatBox = document.getElementById("chat-box");
    if (visible) {
        chatBox.innerHTML = `
            <div id="welcome-screen" class="welcome">
                <span class="welcome__eyebrow">KnowledgeFlow AI</span>
                <h1 class="welcome__title">Ask anything about your documents.</h1>
                <p class="welcome__sub">
                    Upload files to the knowledge base on the left, then ask a question —
                    answers are grounded in your documents with sources cited below each reply.
                </p>
            </div>
        `;
    }
}

function setStreaming(active) {
    const flowBar = document.getElementById("flow-bar");
    if (!flowBar) return;
    flowBar.classList.toggle("is-active", active);
}

// ===================== Chat =====================

async function sendMessage(){

    let input =
        document.getElementById("question");

    let query =
        input.value;

    if(!query)
        return;

    if (!currentConversationId) {

        alert(
            "Please create or select a conversation first."
        );

        return;
    }
    let chatBox =
        document.getElementById("chat-box");

    const welcomeScreen = document.getElementById("welcome-screen");
    if (welcomeScreen) welcomeScreen.remove();

    chatBox.innerHTML +=
        `<div class="user">
            <b>You:</b> ${query}
        </div>`;

    input.value = "";

    const token =
    localStorage.getItem(
        "token"
    );

    setStreaming(true);

    const response =
        await fetch(
            "http://127.0.0.1:8000/chat-stream",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json",

                    "Authorization":
                        `Bearer ${token}`
                },

                body: JSON.stringify({
                    conversation_id:
                        currentConversationId,

                    query: query
                })
            }
        );
    let botDiv =
    document.createElement("div");
    
    botDiv.className = "bot";
    
    botDiv.innerHTML =
        "<b>Assistant:</b><br>";
    
    chatBox.appendChild(botDiv);    

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    let answer = "";
    let buffer = "";

    while (true) {

        const { done, value } =
            await reader.read();

        if (done)
            break;

        buffer += decoder.decode(
            value,
            { stream: true }
        );

        const lines =
            buffer.split("\n\n");

        buffer = lines.pop();

        for (const line of lines) {

            if (
                !line.startsWith("data:")
            )
                continue;

            try {

                const jsonData =
                    JSON.parse(
                        line.replace(
                            "data:",
                            ""
                        ).trim()
                    );

                // TOKEN EVENT
                if (
                    jsonData.type ===
                    "token"
                ) {

                    answer +=
                        jsonData.content;

                    botDiv.innerHTML =
                        `<b>Assistant:</b><br>
                        ${marked.parse(answer)}`;

                    chatBox.scrollTop = chatBox.scrollHeight;

                }

                // SOURCES EVENT
                else if (
                    jsonData.type ===
                    "sources"
                ) {

                    let sourceHtml =
                        `
                        <hr>
                        <b>Sources</b>
                        <ul>
                        `;

                    jsonData.content.forEach(src => {

                        // document without pages
                        if (src.pages.length === 0) {

                            sourceHtml += `
                                <li>
                                    ${src.source}
                                </li>
                            `;

                        }

                        // single page
                        else if (src.pages.length === 1) {

                            sourceHtml += `
                                <li>
                                    ${src.source}
                                    (Page ${src.pages[0]})
                                </li>
                            `;

                        }

                        // multiple pages
                        else {

                            sourceHtml += `
                                <li>
                                    ${src.source}
                                    (Pages ${src.pages.join(", ")})
                                </li>
                            `;

                        }

                    });

                    sourceHtml +=
                        "</ul>";

                    botDiv.innerHTML =
                        `
                        <b>Assistant:</b><br>
                        ${marked.parse(answer)}
                        ${sourceHtml}
                        `;

                    setStreaming(false);

                    // Only refresh the sidebar conversation titles —
                    // do NOT reload the chat body, or citations get wiped
                    const conversations = await getConversations();
                    conversationList.innerHTML = "";
                    conversations.forEach(renderConversation);
                }

            } catch (err) {

                console.error(
                    "JSON Parse Error",
                    err
                );
            }
        }

        chatBox.scrollTop =
            chatBox.scrollHeight;
    }

    setStreaming(false);
}
let currentConversationId = null;

const conversationList =
    document.getElementById(
        "conversation-list"
    );

const newChatBtn =
    document.getElementById(
        "new-chat-btn"
    );

const documentList =
    document.getElementById(
        "document-list"
    );

const uploadBtn =
    document.getElementById(
        "upload-btn"
    );

const uploadInput =
    document.getElementById(
        "document-upload"
    );

function renderConversation(
    conversation
) {

    const div =
        document.createElement(
            "div"
        );

    div.className =
        "conversation-item";

    div.dataset.id =
        conversation.id;

    div.innerHTML =
        `
        <span>
            ${conversation.title}
        </span>

        <button
            class="delete-btn"
        >
            🗑
        </button>
        `;
    const deleteBtn =
        div.querySelector(
            ".delete-btn"
        );

    deleteBtn.addEventListener(
        "click",
        async (e) => {

            e.stopPropagation();

            const confirmed =
                confirm(
                    "Delete this conversation?"
                );

            if(!confirmed)
                return;

            await deleteConversation(
                conversation.id
            );

            await loadConversations();

            document
                .getElementById(
                    "chat-box"
                )
                .innerHTML = "";

            currentConversationId =
                null;

            setWelcomeVisible(true);
        }
    );

    div.onclick =
        () => {

            document
                .querySelectorAll(
                    ".conversation-item"
                )
                .forEach(
                    item =>
                        item.classList.remove(
                            "active"
                        )
                );

            div.classList.add(
                "active"
            );

            loadConversation(
                conversation.id
            );
        };

    conversationList.appendChild(
        div
    );
}

async function loadConversation(
    conversationId
) {
    document
        .querySelectorAll(
            ".conversation-item"
        )
        .forEach(
            item =>
                item.classList.remove(
                    "active"
                )
        );

    const activeItem =
        document.querySelector(
            `[data-id="${conversationId}"]`
        );

    if(activeItem){

        activeItem.classList.add(
            "active"
        );
    }

    currentConversationId =
        conversationId;

    const messages =
        await getConversation(
            conversationId
        );

    const chatBox =
        document.getElementById(
            "chat-box"
        );

    chatBox.innerHTML = "";

    if (messages.length === 0) {
        setWelcomeVisible(true);
    } else {

        messages.forEach(
            message => {

                if (
                    message.role === "user"
                ) {

                    chatBox.innerHTML += `
                        <div class="user">
                            <b>You:</b>
                            ${message.content}
                        </div>
                    `;
                }

                else {

                    chatBox.innerHTML += `
                        <div class="bot">
                            <b>Assistant:</b><br>
                            ${marked.parse(
                                message.content
                            )}
                        </div>
                    `;
                }

            }
        );
    }

    chatBox.scrollTop =
        chatBox.scrollHeight;
}

async function newChat() {

    const conversation =
        await createConversation();

    currentConversationId =
        conversation.id;

    renderConversation(
        conversation
    );

    await loadConversation(
        conversation.id
    );
}

async function loadConversations() {

    const conversations =
        await getConversations();

    conversationList.innerHTML =
        "";

    conversations.forEach(
        conversation => {

            renderConversation(
                conversation
            );

        }
    );

    if (
        conversations.length > 0
    ) {

        loadConversation(
            conversations[0].id
        );
    } else {
        setWelcomeVisible(true);
    }
}

newChatBtn.addEventListener(
    "click",
    newChat
);

async function getDocuments() {

    const response =
        await apiRequest(
            "/documents"
        );

    return await response.json();
}

async function deleteDocument(
    documentId
) {

    await apiRequest(
        `/documents/${documentId}`,
        "DELETE"
    );
}

async function uploadDocument(
    file
) {

    const token =
        localStorage.getItem(
            "token"
        );

    const formData =
        new FormData();

    formData.append(
        "file",
        file
    );

    const response =
        await fetch(
            `${API_BASE}/documents/upload`,
            {
                method: "POST",

                headers: {
                    Authorization:
                        `Bearer ${token}`
                },

                body: formData
            }
        );

    return response;
}

function renderDocument(doc) {

    const div =
        document.createElement(
            "div"
        );

    div.className =
        "document-item";

    div.innerHTML =
        `
        <span>
            📄 ${doc.filename}
        </span>

        <button
            class="delete-doc-btn"
        >
            🗑
        </button>
        `;

    div.querySelector(
        ".delete-doc-btn"
    ).onclick =
        async (e) => {

            e.stopPropagation();

            const confirmed =
                confirm(
                    "Delete this document?"
                );

            if(!confirmed)
                return;

            await deleteDocument(
                doc.id
            );

            await loadDocuments();
        };

    documentList.appendChild(
        div
    );
}
async function loadDocuments() {

    const documents =
        await getDocuments();

    documentList.innerHTML =
        "";

    documents.forEach(
        document => {

            renderDocument(
                document
            );
        }
    );
}

// ===================== Upload: staged progress, drag & drop, errors =====================

const ALLOWED_EXTENSIONS = ["pdf", "docx", "txt"];

const UPLOAD_STAGES = [
    "Uploading document",
    "Reading document",
    "Creating chunks",
    "Generating embeddings",
    "Indexing document"
];

const dropzone = document.getElementById("upload-btn");
const progressPanel = document.getElementById("upload-progress");
const progressStageEl = document.getElementById("upload-progress__stage");
const progressFillEl = document.getElementById("upload-progress__fill");
const uploadErrorEl = document.getElementById("upload-error");

let stageTimer = null;

function showUploadError(message) {
    uploadErrorEl.textContent = message;
    uploadErrorEl.hidden = false;
}

function clearUploadError() {
    uploadErrorEl.hidden = true;
    uploadErrorEl.textContent = "";
}

function setUploadInProgress(active) {
    dropzone.classList.toggle("is-disabled", active);
    uploadInput.disabled = active;
}

function startStagedProgress() {
    let stageIndex = 0;

    progressPanel.hidden = false;
    progressStageEl.classList.remove("is-done");
    progressStageEl.textContent = UPLOAD_STAGES[0];
    progressFillEl.style.width = "8%";

    stageTimer = setInterval(() => {
        // Hold on the last stage until the real request actually finishes
        if (stageIndex < UPLOAD_STAGES.length - 1) {
            stageIndex += 1;
            progressStageEl.textContent = UPLOAD_STAGES[stageIndex];
            const pct = Math.round(((stageIndex + 1) / UPLOAD_STAGES.length) * 90);
            progressFillEl.style.width = `${pct}%`;
        }
    }, 900);
}

function finishStagedProgress(success) {
    clearInterval(stageTimer);

    if (success) {
        progressStageEl.textContent = "Completed successfully";
        progressStageEl.classList.add("is-done");
        progressFillEl.style.width = "100%";
    }

    setTimeout(() => {
        progressPanel.hidden = true;
        progressFillEl.style.width = "8%";
    }, success ? 900 : 0);
}

function validateFile(file) {
    const extension = file.name.split(".").pop().toLowerCase();

    if (!ALLOWED_EXTENSIONS.includes(extension)) {
        return `Unsupported file type ".${extension}" — use PDF, DOCX, or TXT.`;
    }

    return null;
}

async function handleFileUpload(file) {

    clearUploadError();

    const validationError = validateFile(file);
    if (validationError) {
        showUploadError(validationError);
        return;
    }

    setUploadInProgress(true);
    startStagedProgress();

    try {
        const response = await uploadDocument(file);

        if (!response.ok) {
            let detail = "Upload failed. Please try again.";
            try {
                const body = await response.json();
                if (body.detail) detail = body.detail;
            } catch (e) {
                // response wasn't JSON — keep default message
            }
            finishStagedProgress(false);
            showUploadError(detail);
            return;
        }

        await loadDocuments();
        finishStagedProgress(true);

    } catch (err) {
        finishStagedProgress(false);
        showUploadError("Couldn't reach the server. Check your connection and try again.");
    } finally {
        setUploadInProgress(false);
    }
}

uploadInput.addEventListener(
    "change",
    async (e) => {

        const file =
            e.target.files[0];

        if(!file)
            return;

        await handleFileUpload(file);

        uploadInput.value = "";
    }
);

// Drag and drop onto the dropzone label

["dragenter", "dragover"].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.add("is-dragover");
    });
});

["dragleave", "drop"].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.remove("is-dragover");
    });
});

dropzone.addEventListener("drop", async (e) => {
    const file = e.dataTransfer.files[0];
    if (!file) return;

    await handleFileUpload(file);
});

(async () => {

    await loadConversations();

    await loadDocuments();

})();