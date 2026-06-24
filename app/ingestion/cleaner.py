# app/ingestion/cleaner.py

import re


IGNORE_TERMS = [

    "table of contents",

    "copyright",

    "all rights reserved",

    "confidential"
]


def clean_text(text):

    text = re.sub(
        r"\n+",
        "\n",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    text = re.sub(
        r"Page\s+\d+",
        "",
        text,
        flags=re.IGNORECASE
    )

    return text.strip()


def clean_documents(documents):

    clean_docs = []

    for doc in documents:

        content = clean_text(
            doc.page_content
        )

        lower_content = content.lower()

        if any(
            term in lower_content
            for term in IGNORE_TERMS
        ):
            continue

        doc.page_content = content

        clean_docs.append(doc)

    print(
        f"Useful Pages: {len(clean_docs)}"
    )

    return clean_docs