import json

from openai import OpenAI
from pydantic import BaseModel, ValidationError

from app.core.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)


class GeneratedOption(BaseModel):
    id: str
    text: str


class GeneratedQuestion(BaseModel):
    body: str
    options: list[GeneratedOption]
    correct_answer: str
    explanation: str


class QuestionGenerationError(Exception):
    """Raised when OpenAI fails, or returns something we can't safely use."""


def generate_questions(topic: str, difficulty: int, count: int) -> list[GeneratedQuestion]:
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

    try:
        response = client.responses.create(model=settings.OPENAI_MODEL, input=prompt)
    except Exception as e:
        raise QuestionGenerationError(f"OpenAI request failed: {e}") from e

    try:
        raw = json.loads(response.output_text)
    except json.JSONDecodeError as e:
        raise QuestionGenerationError(f"Model returned invalid JSON: {e}") from e

    if not isinstance(raw, list):
        raise QuestionGenerationError("Model response was not a JSON array")

    questions: list[GeneratedQuestion] = []
    for item in raw:
        try:
            question = GeneratedQuestion.model_validate(item)
        except ValidationError as e:
            raise QuestionGenerationError(f"Malformed question object: {e}") from e

        if len(question.options) != 4:
            raise QuestionGenerationError("Question did not have exactly 4 options")
        if question.correct_answer not in {opt.id for opt in question.options}:
            raise QuestionGenerationError("correct_answer does not match any option id")

        questions.append(question)

    if len(questions) != count:
        raise QuestionGenerationError(f"Expected {count} questions, got {len(questions)}")

    return questions
