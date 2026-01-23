"""
AI Utilities for document summarization
"""
import os
from openai import OpenAI


def generate_summary(text: str, max_length: int = 500) -> dict:
    """Generate summary using GPT-4 (non-streaming)."""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Truncate if too long (GPT-4 context limit)
    if len(text) > 100000:
        text = text[:100000] + "..."

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Summarize this document concisely. Include key points."},
            {"role": "user", "content": text}
        ],
        max_tokens=max_length
    )

    return {
        "summary": response.choices[0].message.content,
        "model": "gpt-4"
    }


def generate_summary_stream(text: str, max_length: int = 500):
    """Generate summary using GPT-4 with streaming. Yields chunks of text."""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Truncate if too long (GPT-4 context limit)
    if len(text) > 100000:
        text = text[:100000] + "..."

    stream = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Summarize this document concisely. Include key points."},
            {"role": "user", "content": text}
        ],
        max_tokens=max_length,
        stream=True
    )

    for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


def chat_with_document(document_text: str, chat_history: list, user_message: str):
    """
    Chat with a document using GPT-4 with streaming.

    Args:
        document_text: The extracted text from the PDF document
        chat_history: List of previous messages [{"role": "user/assistant", "content": "..."}]
        user_message: The current user question

    Yields:
        Chunks of the assistant's response for streaming
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Truncate document if too long (leave room for chat history)
    if len(document_text) > 80000:
        document_text = document_text[:80000] + "\n\n[Document truncated due to length...]"

    # Build messages list
    system_prompt = f"""You are a helpful AI assistant that answers questions about a document.
You have access to the full document content below. Answer questions accurately based on the document.
If the answer is not in the document, say so clearly. Be concise but thorough.

DOCUMENT CONTENT:
---
{document_text}
---

Instructions:
- Answer questions based on the document above
- Quote relevant sections when helpful
- If asked about something not in the document, clearly state it's not covered
- Be conversational and helpful"""

    messages = [{"role": "system", "content": system_prompt}]

    # Add chat history (limit to last 10 exchanges to manage context)
    for msg in chat_history[-20:]:
        messages.append({"role": msg["role"], "content": msg["content"]})

    # Add current user message
    messages.append({"role": "user", "content": user_message})

    stream = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        max_tokens=1000,
        stream=True
    )

    for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
