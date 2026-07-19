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

    chatBox.innerHTML +=
        `<div class="user">
            <b>You:</b> ${query}
        </div>`;

    input.value = "";

    const token =
    localStorage.getItem(
        "token"
    );

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

                    jsonData.content.forEach(
                        src => {

                            sourceHtml += `
                            <li>
                                ${src.source}
                                (Page ${src.page})
                            </li>
                            `;
                        }
                    );

                    sourceHtml +=
                        "</ul>";

                    botDiv.innerHTML =
                        `
                        <b>Assistant:</b><br>
                        ${marked.parse(answer)}
                        ${sourceHtml}
                        `;
                    await loadConversations();
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

function renderConversation(
    conversation
) {

    const div =
        document.createElement(
            "div"
        );

    div.className =
        "conversation-item";

    div.innerText =
        conversation.title;

    div.onclick =
        () => loadConversation(
            conversation.id
        );

    conversationList.appendChild(
        div
    );
}

async function loadConversation(
    conversationId
) {

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
    }
}

newChatBtn.addEventListener(
    "click",
    newChat
);

loadConversations();