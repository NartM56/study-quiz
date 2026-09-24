import json

from openai import OpenAI
from pydantic import BaseModel, ValidationError

from app.core.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

MAX_ATTEMPTS = 2

# Options are modeled as four named fields (not an array) so "exactly 4
# options" is a plain object-shape guarantee, which strict mode reliably
# enforces. minItems/maxItems on the questions array is unconfirmed in docs,
# but tested live and matched exactly across multiple trials — kept as a
# genuine constraint here, with the count check below as a safety net either way.
def _build_schema(count: int) -> dict:
    return {
        "type": "object",
        "properties": {
            "questions": {
                "type": "array",
                "minItems": count,
                "maxItems": count,
                "items": {
                    "type": "object",
                    "properties": {
                        "body": {"type": "string"},
                        "option_a": {"type": "string"},
                        "option_b": {"type": "string"},
                        "option_c": {"type": "string"},
                        "option_d": {"type": "string"},
                        "correct_answer": {"type": "string", "enum": ["a", "b", "c", "d"]},
                        "explanation": {"type": "string"},
                    },
                    "required": [
                        "body",
                        "option_a",
                        "option_b",
                        "option_c",
                        "option_d",
                        "correct_answer",
                        "explanation",
                    ],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["questions"],
        "additionalProperties": False,
    }


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


def _build_prompt(topic: str, difficulty: int, count: int) -> str:
    return f"""
    Generate multiple choice questions about "{topic}"
    at difficulty level {difficulty} (1 = easy, 5 = hard).

    IMPORTANT: Return EXACTLY {count} questions in the "questions" array —
    not {count - 1}, not {count + 1}. Count them before responding.
    """


def _generate_once(topic: str, difficulty: int, count: int) -> list[GeneratedQuestion]:
    prompt = _build_prompt(topic, difficulty, count)

    # ~300 tokens/question covers body + 4 options + explanation + JSON overhead;
    # without an explicit cap, larger requests are more exposed to whatever
    # default limit the API applies and can get cut off mid-generation.
    max_output_tokens = max(1024, count * 300)

    try:
        response = client.responses.create(
            model=settings.OPENAI_MODEL,
            input=prompt,
            max_output_tokens=max_output_tokens,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "quiz_questions",
                    "schema": _build_schema(count),
                    "strict": True,
                }
            },
        )
    except Exception as e:
        raise QuestionGenerationError(f"OpenAI request failed: {e}") from e

    output_text = response.output_text
    print(output_text)
    if not output_text:
        status = getattr(response, "status", "unknown")
        incomplete_reason = getattr(
            getattr(response, "incomplete_details", None), "reason", None
        )
        raise QuestionGenerationError(
            f"OpenAI returned an empty response (status={status}, "
            f"incomplete_reason={incomplete_reason})"
        )

    try:
        raw = json.loads(output_text)
    except json.JSONDecodeError as e:
        raise QuestionGenerationError(
            f"Model returned invalid JSON: {e} — raw response started with {output_text[:200]!r}"
        ) from e

    raw_questions = raw.get("questions") if isinstance(raw, dict) else None
    if not isinstance(raw_questions, list):
        raise QuestionGenerationError("Model response did not contain a 'questions' array")

    questions: list[GeneratedQuestion] = []
    for item in raw_questions:
        try:
            question = GeneratedQuestion(
                body=item["body"],
                options=[
                    GeneratedOption(id="a", text=item["option_a"]),
                    GeneratedOption(id="b", text=item["option_b"]),
                    GeneratedOption(id="c", text=item["option_c"]),
                    GeneratedOption(id="d", text=item["option_d"]),
                ],
                correct_answer=item["correct_answer"],
                explanation=item["explanation"],
            )
        except (KeyError, ValidationError) as e:
            raise QuestionGenerationError(f"Malformed question object: {e}") from e

        questions.append(question)

    if len(questions) != count:
        raise QuestionGenerationError(f"Expected {count} questions, got {len(questions)}")

    return questions


def generate_questions(topic: str, difficulty: int, count: int) -> list[GeneratedQuestion]:
    """Ask OpenAI for `count` questions, retrying once on any failure —
    empty output or a wrong question count are typically one-off model
    imprecision rather than a deterministic bug."""
    last_error: QuestionGenerationError | None = None

    for _ in range(MAX_ATTEMPTS):
        try:
            return _generate_once(topic, difficulty, count)
        except QuestionGenerationError as e:
            last_error = e

    assert last_error is not None
    raise last_error
