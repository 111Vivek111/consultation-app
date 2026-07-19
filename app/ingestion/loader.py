from langchain_community.document_loaders import (
    PDFPlumberLoader,
    TextLoader,
    Docx2txtLoader
)

import os

from pathlib import Path

def load_single_document(
    file_path: str
):

    extension = (
        Path(file_path)
        .suffix
        .lower()
    )

    if extension == ".pdf":

        loader = PDFPlumberLoader(
            file_path
        )

    elif extension == ".txt":

        loader = TextLoader(
            file_path,
            encoding="utf-8"
        )

    elif extension == ".docx":

        loader = Docx2txtLoader(
            file_path
        )

    else:

        raise ValueError(
            f"Unsupported file type: {extension}"
        )

    return loader.load()


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