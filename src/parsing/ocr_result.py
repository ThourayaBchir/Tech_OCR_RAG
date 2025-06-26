import uuid


def extract_text_and_tables(document_proto, min_paragraph_len=50):
    chunks = []
    full_text = document_proto.get("text", "")

    for page in document_proto.get("pages", []):
        page_number = page.get("pageNumber")

        para_buffer = ""
        for paragraph in page.get("paragraphs", []):
            para_text = extract_text_from_anchor(
                full_text, paragraph.get("layout", {}).get("textAnchor", {})
            )
            if not para_text.strip():
                continue
            if len(para_text) < min_paragraph_len:
                para_buffer += " " + para_text.strip()
            else:
                if para_buffer:
                    chunks.append(
                        {
                            "id": str(uuid.uuid4()),
                            "type": "paragraph",
                            "text": para_buffer.strip(),
                            "page": page_number,
                        }
                    )
                    para_buffer = ""
                chunks.append(
                    {
                        "id": str(uuid.uuid4()),
                        "type": "paragraph",
                        "text": para_text.strip(),
                        "page": page_number,
                    }
                )
        if para_buffer:
            chunks.append(
                {
                    "id": str(uuid.uuid4()),
                    "type": "paragraph",
                    "text": para_buffer.strip(),
                    "page": page_number,
                }
            )
        # --- Extract tables as Markdown ---
        for table in page.get("tables", []):
            table_text = extract_table_as_markdown(full_text, table)
            row_count = len(table.get("bodyRows", [])) + len(
                table.get("headerRows", [])
            )
            if table_text.strip():
                chunks.append(
                    {
                        "id": str(uuid.uuid4()),
                        "type": "table",
                        "text": table_text.strip(),
                        "page": page_number,
                        "rows": row_count,
                    }
                )
    return chunks


def extract_text_from_anchor(full_text, anchor):
    """
    Given a text anchor (Document AI format), extract actual text.
    """
    if not anchor or "textSegments" not in anchor:
        return ""
    result = ""
    for segment in anchor["textSegments"]:
        start = int(segment.get("startIndex", 0))
        end = int(segment.get("endIndex", 0))
        result += full_text[start:end]
    return result


def extract_table_as_markdown(full_text, table):
    """
    Extract a table as Markdown (or CSV-like text) for easy embedding.
    """
    if "headerRows" in table:
        header_rows = table["headerRows"]
    else:
        header_rows = []
    body_rows = table.get("bodyRows", [])

    rows = []

    # Extract header
    for row in header_rows:
        row_text = [
            extract_text_from_anchor(
                full_text, cell.get("layout", {}).get("textAnchor", {})
            )
            for cell in row.get("cells", [])
        ]
        rows.append(" | ".join(cell.strip() for cell in row_text))

    # Extract body
    for row in body_rows:
        row_text = [
            extract_text_from_anchor(
                full_text, cell.get("layout", {}).get("textAnchor", {})
            )
            for cell in row.get("cells", [])
        ]
        rows.append(" | ".join(cell.strip() for cell in row_text))

    return "\n".join(rows)
