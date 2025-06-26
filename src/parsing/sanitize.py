import re


def sanitize_prompt(text: str, allow_newline: bool = True) -> str:
    # Remove all control chars except optional newline
    if allow_newline:
        text = re.sub(r"[^\x20-\x7E\n]", "", text)
    else:
        text = re.sub(r"[^\x20-\x7E]", "", text)
    # Optionally, remove/replace other special chars (e.g., only allow [a-zA-Z0-9.,;:?! ])
    text = re.sub(r"[^a-zA-Z0-9.,;:?! \n]", "", text)
    return text
