import re


def clean_document_text(text: str) -> str:
    if not isinstance(text, str):
        raise TypeError("Document text must be a string.")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n{4,}", "\n\n\n", text).strip()
