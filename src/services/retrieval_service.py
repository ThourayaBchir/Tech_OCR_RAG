from cloud_io.gcs import generate_gcs_signed_url


def build_rag_prompt(user_query, retrieved_chunks, url_expiry_sec=600):
    """
    Build LLM prompt and references, attaching presigned URLs to sources.
    """
    chunk_texts = []
    references = []
    for i, chunk in enumerate(retrieved_chunks):
        label = f"[Source {i+1}]"
        source_path = chunk.get("source", "unknown")
        file_name = source_path.split("/")[-1] if "/" in source_path else source_path
        page = chunk.get("page", "?")
        try:
            url = generate_gcs_signed_url(
                source_path, expiration_seconds=url_expiry_sec
            )
        except Exception:
            url = None
        if url:
            ref = (
                f'{label}: <a href="{url}" target="_blank">{file_name}</a>, page {page}'
            )
        else:
            ref = f"{label}: {file_name}, page {page}"
        references.append(ref)
        chunk_texts.append(f"{label}\n{chunk['text']}")
    context = "\n\n".join(chunk_texts)
    prompt = (
        f"You are a technical assistant. "
        f"Use ONLY the provided context below to answer the question as accurately as possible. "
        f"Cite your sources using the labels like [Source 1], [Source 2], etc. "
        f"Do not invent citations or add any sources not in the context.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {user_query}\n"
        f"Answer (with sources cited as [Source N]):"
    )
    return prompt, references
