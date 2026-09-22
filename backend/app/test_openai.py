import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_questions(topic: str, difficulty: int, count: int) -> list[dict]:
    prompt = f"""
    Generate {count} multiple choice questions about "{topic}"
    at difficulty level {difficulty} (1 = easy, 5 = hard).

    Each question must have exactly 4 answer choices.

    Return ONLY a JSON array in this format:

    [
        {{
            "body": "What is ...?",
            "options": [
                {{"id": "a", "text": "..."}},
                {{"id": "b", "text": "..."}},
                {{"id": "c", "text": "..."}},
                {{"id": "d", "text": "..."}}
            ],
            "correct_answer": "a",
            "explanation": "Because ..."
        }}
    ]
    """

    response = client.responses.create(
        model="gpt-5.6-luna",
        input=prompt
    )

    return json.loads(response.output_text)