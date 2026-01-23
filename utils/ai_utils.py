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
