from langchain_community.document_loaders import (
    PDFPlumberLoader,
    TextLoader
)

import os


def load_documents(data_folder="knowledge"):

    knowledge = []

    for file in os.listdir(data_folder):

        path = os.path.join(
            data_folder,
            file
        )

        # PDF
        if file.lower().endswith(".pdf"):

            loader = PDFPlumberLoader(
                path
            )

            docs = loader.load()

            knowledge.extend(
                docs
            )

        # TXT
        elif file.lower().endswith(".txt"):

            loader = TextLoader(
                path,
                encoding="utf-8"
            )

            docs = loader.load()

            knowledge.extend(
                docs
            )

    print(
        f"Loaded {len(knowledge)} documents"
    )

    return knowledge