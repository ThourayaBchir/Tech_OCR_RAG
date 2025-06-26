from openai import OpenAI

from utils.config import settings


def ask_llm_lambda_stream(prompt, model=settings.LAMBDA_API_MODEL):
    api_key = settings.LAMBDA_API_KEY
    api_base = settings.LAMBDA_API_BASE
    client = OpenAI(api_key=api_key, base_url=api_base)

    stream = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a technical assistant. Use ONLY the provided context to answer the user's question and cite sources.",
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=512,
        temperature=0.2,
        stream=True,  # Enable streaming
    )
    for chunk in stream:
        content = chunk.choices[0].delta.content
        if content:
            yield content
