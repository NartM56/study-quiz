from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CreateSessionRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=100)
    difficulty: int = Field(ge=1, le=5)
    question_count: int = Field(ge=1, le=20)


class QuestionOption(BaseModel):
    id: str
    text: str


class QuestionOut(BaseModel):
    question_id: UUID
    body: str
    options: list[QuestionOption]


class SessionCreateResponse(BaseModel):
    session_id: UUID
    topic: str
    difficulty: int
    questions: list[QuestionOut]


class SubmitAnswerRequest(BaseModel):
    question_id: UUID
    given_answer: str = Field(min_length=1)
    time_taken_ms: Optional[int] = Field(default=None, ge=0)


class SubmitAnswerResponse(BaseModel):
    is_correct: bool
    correct_answer: str
    explanation: Optional[str] = None


class SessionResultResponse(BaseModel):
    session_id: UUID
    total_questions: int
    answered: int
    correct: int
    score_percent: float
    ended_at: datetime


class QuizHistoryItem(BaseModel):
    session_id: UUID
    topic: str
    difficulty: int
    total_questions: int
    answered: int
    correct: int
    score_percent: float
    started_at: datetime
    ended_at: datetime


class UserStatsResponse(BaseModel):
    total_quizzes: int
    total_questions_answered: int
    total_correct: int
    overall_score_percent: float
    quizzes: list[QuizHistoryItem]
