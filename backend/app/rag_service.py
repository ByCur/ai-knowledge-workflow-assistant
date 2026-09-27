from .llm_service import generate_chat

from .config import settings


def generate_answer(
    question: str,
    sources: list[dict],
) -> str:

    context_parts = []

    for index, source in enumerate(
        sources,
        start=1,
    ):
        context_parts.append(
            (
                f"[Source {index}]\n"
                f"Document: "
                f"{source['document_name']}\n"
                f"Content:\n"
                f"{source['content']}"
            )
        )

    context = "\n\n---\n\n".join(
        context_parts
    )

    system_prompt = """
You are a retrieval-augmented knowledge assistant.

IMPORTANT:
You already have direct access to the extracted
content of the user's uploaded documents in the
CONTEXT section below.

Do NOT say that you cannot access the document.
Do NOT invent information that is not present
in the context.

Answer using ONLY the supplied context.

If the context contains the answer, answer
directly and cite the source using [Source 1],
[Source 2], etc.

If the answer is genuinely not present in the
context, say:

"No tengo suficiente información en los
documentos proporcionados para responder."

Answer in the same language as the user's
question.

For very short documents, simply report what
the document says without adding assumptions.
""".strip()

    user_prompt = f"""
CONTEXT FROM THE UPLOADED DOCUMENTS:

{context}

USER QUESTION:

{question}

Answer only from the context above.
""".strip()

    return generate_chat(
    messages=[
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": user_prompt,
        },
    ]
)