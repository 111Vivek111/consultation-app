def build_prompt(
    query,
    docs,
    history
):

    context = "\n\n".join(
        doc.page_content
        for doc in docs
    )

    history_text = ""

    for msg in history[-3:]:

        history_text += (
            f"{msg['role']}: "
            f"{msg['content']}\n"
        )

    return f"""
Answer ONLY using the given context.

Rules:
- No outside knowledge
- No guessing
- If missing say:
  "I could not find this information in the documents."
- Use headings and bullet points.
- Avoid markdown tables.

History:
{history_text}

Context:
{context}

Question:
{query}

Answer:
"""