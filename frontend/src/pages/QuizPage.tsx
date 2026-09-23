import { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { api } from "../api/client";
import "./NewQuizPage.css";
import "./QuizPage.css";

interface QuestionOption {
  id: string;
  text: string;
}

interface Question {
  question_id: string;
  body: string;
  options: QuestionOption[];
}

interface SessionResponse {
  session_id: string;
  topic: string;
  difficulty: number;
  questions: Question[];
}

interface LocationState {
  questions?: Question[];
}

interface AnswerFeedback {
  is_correct: boolean;
  correct_answer: string;
  explanation: string | null;
}

export function QuizPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const location = useLocation();
  const navigate = useNavigate();
  const hasFetched = useRef(false);

  const state = location.state as LocationState | null;
  const [questions, setQuestions] = useState<Question[] | null>(
    state?.questions ?? null,
  );
  const [loadError, setLoadError] = useState("");

  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedOptionId, setSelectedOptionId] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<AnswerFeedback | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    // questions already came in via navigation state — nothing to fetch
    if (questions !== null) return;
    // guard against double-fetching (e.g. React StrictMode's dev double-invoke)
    if (hasFetched.current) return;
    hasFetched.current = true;

    api
      .get<SessionResponse>(`/quiz/sessions/${sessionId}`)
      .then((data) => setQuestions(data.questions))
      .catch((err) =>
        setLoadError(err instanceof Error ? err.message : "Failed to load quiz"),
      );
  }, [questions, sessionId]);

  if (questions === null) {
    if (loadError) {
      return (
        <div className="quiz-page">
          <div className="quiz-card">
            <h1>Couldn't load this quiz</h1>
            <p className="quiz-error" role="alert">
              {loadError}
            </p>
            <button className="quiz-next" onClick={() => navigate("/new-quiz")}>
              New Quiz
            </button>
          </div>
        </div>
      );
    }
    return (
      <div className="quiz-page">
        <div className="quiz-card">
          <p>Loading quiz...</p>
        </div>
      </div>
    );
  }

  if (questions.length === 0) {
    return (
      <div className="quiz-page">
        <div className="quiz-card">
          <h1>No questions found</h1>
          <p>This quiz has no questions. Try creating a new one.</p>
          <button className="quiz-next" onClick={() => navigate("/new-quiz")}>
            New Quiz
          </button>
        </div>
      </div>
    );
  }

  const currentQuestion = questions[currentIndex];
  const isLastQuestion = currentIndex === questions.length - 1;

  const handleSubmitAnswer = async () => {
    if (selectedOptionId === null) return;
    setSubmitting(true);
    setError("");

    try {
      const data = await api.post<AnswerFeedback>(
        `/quiz/sessions/${sessionId}/answers`,
        {
          question_id: currentQuestion.question_id,
          given_answer: selectedOptionId,
        },
      );
      setFeedback(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit answer");
    } finally {
      setSubmitting(false);
    }
  };

  const handleNext = () => {
    setSelectedOptionId(null);
    setFeedback(null);
    setError("");
    if (isLastQuestion) {
      navigate(`/results/${sessionId}`);
    } else {
      setCurrentIndex((i) => i + 1);
    }
  };

  return (
    <div className="quiz-page">
      <div className="quiz-card">
        <p className="quiz-progress">
          Question {currentIndex + 1} of {questions.length}
        </p>
        <h1>{currentQuestion.body}</h1>

        <div className="quiz-options">
          {currentQuestion.options.map((option) => (
            <button
              key={option.id}
              type="button"
              className={`quiz-option${
                selectedOptionId === option.id ? " selected" : ""
              }`}
              onClick={() => setSelectedOptionId(option.id)}
              disabled={feedback !== null}
            >
              {option.text}
            </button>
          ))}
        </div>

        {error && (
          <p className="quiz-error" role="alert">
            {error}
          </p>
        )}

        {feedback && (
          <p
            className={`quiz-feedback ${
              feedback.is_correct ? "correct" : "incorrect"
            }`}
          >
            {feedback.is_correct
              ? "Correct!"
              : `Incorrect — the correct answer was "${feedback.correct_answer}".`}
            {feedback.explanation ? ` ${feedback.explanation}` : ""}
          </p>
        )}

        {feedback === null ? (
          <button
            type="button"
            className="quiz-next"
            onClick={handleSubmitAnswer}
            disabled={selectedOptionId === null || submitting}
          >
            {submitting ? "Submitting..." : "Submit Answer"}
          </button>
        ) : (
          <button type="button" className="quiz-next" onClick={handleNext}>
            {isLastQuestion ? "Finish" : "Next"}
          </button>
        )}
      </div>
    </div>
  );
}

export default QuizPage;
