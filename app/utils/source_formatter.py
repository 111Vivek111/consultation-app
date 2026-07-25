from pathlib import Path


def format_sources(docs):

    grouped_sources = {}

    for doc in docs:

        filename = Path(
            doc.metadata.get(
                "source",
                ""
            )
        ).name

        page = doc.metadata.get(
            "page"
        )

        # convert to 1 based indexing
        if page is not None:
            page += 1

        # create document entry
        if filename not in grouped_sources:

            grouped_sources[filename] = set()

        # avoid adding None values
        if page is not None:
            grouped_sources[filename].add(page)

    sources = []

    for filename, pages in grouped_sources.items():

        sources.append(

            {
                "source": filename,

                "pages": sorted(
                    list(pages)
                )
            }

        )

    return sources