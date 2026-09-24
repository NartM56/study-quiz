from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies import get_current_user
from app.models.study_models import (
    Attempt,
    User,
    Question,
    QuestionTopic,
    Session as QuizSession,
    Topic,
)
from app.schemas.quiz import (
    CreateSessionRequest,
    QuizHistoryItem,
    SessionCreateResponse,
    SessionResultResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
    UserStatsResponse,
)
from app.services.question_generator import generate_questions, QuestionGenerationError
from app.services.topics import get_or_create_topic

router = APIRouter()


@router.post("/sessions", response_model=SessionCreateResponse, status_code=201)
def create_quiz(
    request: CreateSessionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    print("got here")
    topic = get_or_create_topic(db, request.topic)

    try:
        print(f"Trying to generate questions for topic '{request.topic}' with difficulty {request.difficulty} and count {request.question_count}")
        generated_questions = generate_questions(
            request.topic, request.difficulty, request.question_count
        )
    except QuestionGenerationError as e:
        raise HTTPException(status_code=502, detail=str(e))

    session = QuizSession(
        user_id=current_user.id,
        mode="practice",
        topic_ids=[topic.id],
        target_count=request.question_count,
    )
    db.add(session)
    db.flush()  # assigns session.id without committing yet
    
    print(f"Created session with ID {session.id}")

    questions = []
    for q in generated_questions:
        question = Question(
            session_id=session.id,
            body=q.body,
            question_type="mcq",
            options=[o.model_dump() for o in q.options],
            correct_answer=q.correct_answer,
            explanation=q.explanation,
            difficulty=request.difficulty,
            created_by=current_user.id,
        )
        db.add(question)
        db.flush()
        db.add(QuestionTopic(question_id=question.id, topic_id=topic.id))
        questions.append(question)

    db.commit()

    return SessionCreateResponse(
        session_id=session.id,
        topic=topic.name,
        difficulty=request.difficulty,
        questions=[
            {"question_id": q.id, "body": q.body, "options": q.options}
            for q in questions
        ],
    )


@router.get("/sessions/{session_id}", response_model=SessionCreateResponse)
def get_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = db.get(QuizSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your session")

    questions = db.scalars(
        select(Question)
        .where(Question.session_id == session.id)
        .order_by(Question.created_at)
    ).all()
    if not questions:
        raise HTTPException(status_code=404, detail="No questions found for this session")

    topic_id = session.topic_ids[0] if session.topic_ids else None
    topic = db.get(Topic, topic_id) if topic_id is not None else None

    return SessionCreateResponse(
        session_id=session.id,
        topic=topic.name if topic else "",
        difficulty=questions[0].difficulty,
        questions=[
            {"question_id": q.id, "body": q.body, "options": q.options}
            for q in questions
        ],
    )


@router.post("/sessions/{session_id}/answers", response_model=SubmitAnswerResponse)
def submit_answer(
    session_id: UUID,
    request: SubmitAnswerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = db.get(QuizSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your session")

    question = db.get(Question, request.question_id)
    if question is None or question.session_id != session.id:
        raise HTTPException(status_code=404, detail="Question not found in this session")

    existing_attempt = db.scalar(
        select(Attempt).where(
            Attempt.session_id == session.id,
            Attempt.question_id == question.id,
        )
    )
    if existing_attempt is not None:
        raise HTTPException(status_code=409, detail="Question already answered")

    is_correct = request.given_answer == question.correct_answer

    attempt = Attempt(
        session_id=session.id,
        user_id=current_user.id,
        question_id=question.id,
        given_answer=request.given_answer,
        is_correct=is_correct,
        time_taken_ms=request.time_taken_ms,
        difficulty_at_attempt=question.difficulty,
    )
    db.add(attempt)
    db.commit()

    return SubmitAnswerResponse(
        is_correct=is_correct,
        correct_answer=question.correct_answer,
        explanation=question.explanation,
    )


@router.post("/sessions/{session_id}/finish", response_model=SessionResultResponse)
def finish_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = db.get(QuizSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your session")
    if session.ended_at is not None:
        raise HTTPException(status_code=409, detail="Session already finished")

    session.ended_at = datetime.now(timezone.utc)

    total_questions = db.scalar(
        select(func.count()).select_from(Question).where(Question.session_id == session.id)
    ) or 0

    answered = db.scalar(
        select(func.count()).select_from(Attempt).where(Attempt.session_id == session.id)
    ) or 0

    correct = db.scalar(
        select(func.count())
        .select_from(Attempt)
        .where(Attempt.session_id == session.id, Attempt.is_correct.is_(True))
    ) or 0

    score_percent = round((correct / answered) * 100, 2) if answered > 0 else 0.0

    db.commit()

    return SessionResultResponse(
        session_id=session.id,
        total_questions=total_questions,
        answered=answered,
        correct=correct,
        score_percent=score_percent,
        ended_at=session.ended_at,
    )


@router.get("/stats", response_model=UserStatsResponse)
def get_user_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total_answered = db.scalar(
        select(func.count()).select_from(Attempt).where(Attempt.user_id == current_user.id)
    ) or 0
    total_correct = db.scalar(
        select(func.count())
        .select_from(Attempt)
        .where(Attempt.user_id == current_user.id, Attempt.is_correct.is_(True))
    ) or 0
    overall_score_percent = (
        round((total_correct / total_answered) * 100, 2) if total_answered > 0 else 0.0
    )

    finished_sessions = db.scalars(
        select(QuizSession)
        .where(QuizSession.user_id == current_user.id, QuizSession.ended_at.is_not(None))
        .order_by(QuizSession.started_at.desc())
    ).all()

    quizzes = []
    for session in finished_sessions:
        questions = db.scalars(
            select(Question)
            .where(Question.session_id == session.id)
            .order_by(Question.created_at)
        ).all()

        session_answered = db.scalar(
            select(func.count()).select_from(Attempt).where(Attempt.session_id == session.id)
        ) or 0
        session_correct = db.scalar(
            select(func.count())
            .select_from(Attempt)
            .where(Attempt.session_id == session.id, Attempt.is_correct.is_(True))
        ) or 0
        session_score = (
            round((session_correct / session_answered) * 100, 2) if session_answered > 0 else 0.0
        )

        topic_id = session.topic_ids[0] if session.topic_ids else None
        topic = db.get(Topic, topic_id) if topic_id is not None else None

        quizzes.append(
            QuizHistoryItem(
                session_id=session.id,
                topic=topic.name if topic else "",
                difficulty=questions[0].difficulty if questions else 0,
                total_questions=len(questions),
                answered=session_answered,
                correct=session_correct,
                score_percent=session_score,
                started_at=session.started_at,
                ended_at=session.ended_at,
            )
        )

    return UserStatsResponse(
        total_quizzes=len(finished_sessions),
        total_questions_answered=total_answered,
        total_correct=total_correct,
        overall_score_percent=overall_score_percent,
        quizzes=quizzes,
    )
