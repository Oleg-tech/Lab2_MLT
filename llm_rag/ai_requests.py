import requests

from .config import AI_TOKEN, AI_API_URL


request_headers = {
    "Authorization": f"Bearer {AI_TOKEN}",
    "Content-Type": "application/json"
}


def get_response(text, question):
    prompt = get_prompt(text, question)

    request_payload = {
        "model": "mistral-tiny",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.55
    }

    response = requests.post(url=AI_API_URL, json=request_payload, headers=request_headers)
    response.raise_for_status()

    return response.json()["choices"][0]["message"]["content"]


def get_prompt(text, question):
    return f"""You are a knowledgeable assistant tasked with answering questions based on the provided information.
        Context: {text}
        Question: {question}
        Please provide a clear and accurate response using only the information above. 
        If the context doesn't contain the answer, simply say "I don't know".
    """
