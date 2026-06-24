async function sendMessage(){

    let input =
        document.getElementById("question");

    let query =
        input.value;

    if(!query)
        return;

    let chatBox =
        document.getElementById("chat-box");

    chatBox.innerHTML +=
        `<div class="user">
            <b>You:</b> ${query}
        </div>`;

    input.value = "";

    const response =
        await fetch(
            "http://127.0.0.1:8000/chat-stream",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
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