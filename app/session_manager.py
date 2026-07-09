from collections import defaultdict

MAX_HISTORY = 20

# session_id -> chat history
chat_sessions = defaultdict(list)


def get_history(session_id: str):
    return chat_sessions[session_id]


def add_message(session_id: str, role: str, content: str):

    history = chat_sessions[session_id]

    history.append({
        "role": role,
        "content": content
    })

    # Keep only latest messages
    if len(history) > MAX_HISTORY:
        chat_sessions[session_id] = history[-MAX_HISTORY:]