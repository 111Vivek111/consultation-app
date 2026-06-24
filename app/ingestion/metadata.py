# app/ingestion/metadata.py

def detect_section(text):

    lines = text.split("\n")

    for line in lines[:5]:

        line = line.strip()

        if (
            len(line) < 80
            and len(line.split()) < 10
        ):
            return line

    return "Unknown Section"


def add_metadata(docs):

    for doc in docs:

        section = detect_section(
            doc.page_content
        )

        doc.metadata["section"] = section

        # TXT files won't have page numbers
        if "page" not in doc.metadata:

            doc.metadata["page"] = "N/A"

    return docs